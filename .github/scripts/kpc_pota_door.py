#!/usr/bin/env python3
"""THE POTA DOOR (KPC owner, 2026-11-16, handoff 'proof of work', item 7: be polite to POTA). Every club script that wants
something from POTA (api.pota.app) asks here; no other script opens api.pota.app (tests/test_pota_door_nov16.py fails on a new
direct call). The door reads the STORED COPY first and asks POTA only when the copy is older than its allowed age:

  spots            5 minutes   ONLY the club spot reader (kpc_pota_spots.py) asks POTA; everyone else reads the club spot file
  locations        1 day       /locations, read once a day by the park-list job (kpc_pota_parklists.py)
  park list US/CA  until POTA's own park count for that state / province changes (the park-list job decides)
  park list world  1 week      re-pulled by the park-list job on its weekly world day (spill-over the next nights)
  park details     30 days     /park/<ref>
  activations      30 days     /park/activations/<ref>?count=all   (also /park/leaderboard/<ref>, /lookup)

Readers of park lists (world_pota, canada, northam, new_refs, pota_activity, state_links, top25, refcheck, new_lands) call
saved_park_list() / saved_locations(): the saved copy ONLY, never POTA (ask_pota=False).

Every request is paced through kpc_host_pace (one per 2 s per host) and counted against a per-run budget (KPC_POTA_BUDGET,
default 300; a run that reaches it gets the stored copy, or a DoorClosed error when it has none). The club User-Agent with a
contact is sent on every request (KPC_POTA_CONTACT replaces the contact). One report line per run (at exit):
  POTA door <script>: N asked POTA (budget B), M from the stored copy, K refused

Stored copies live in data/pota/saved/ of this repo (KPC_POTA_DIR moves them): locations.json, parks/<loc>.json.gz,
<kind>/<shard>.json. Offline (KPC_POTA_OFFLINE=1): stored copies only.
  python3 kpc_pota_door.py --selftest
"""
import atexit, gzip, hashlib, json, os, pathlib, re, sys, threading, time, urllib.parse, urllib.request
import kpc_net_guard; kpc_net_guard.install()   # never-contact hosts refused before any request

API = 'https://api.pota.app'
MAX_FILE = 1_000_000   # house rule: 1 MB per file
HOST = 'api.pota.app'
CONTACT = os.environ.get('KPC_POTA_CONTACT') or 'https://github.com/KentuckyPortableClub/KPC-Links/issues'
UA = f'KPC-Links/1.0 (Kentucky Portable Club; +https://kentuckyportableclub.github.io/KPC-Links/; contact: {CONTACT})'
DAY = 86400
AGES = {'spots': 300, 'locations': DAY, 'world_list': 7 * DAY, 'details': 30 * DAY, 'activations': 30 * DAY,
        'leaderboard': 30 * DAY, 'lookup': 30 * DAY}
BUDGET = int(os.environ.get('KPC_POTA_BUDGET') or 300)
STAT = {'asked': 0, 'stored': 0, 'refused': 0, 'failed': 0}
_REPORTED = [False]
_LOCK = threading.RLock()   # scripts that read with a few threads share the stored-copy files


class DoorClosed(Exception):
    """No stored copy and the door may not (or could not) ask POTA."""


def root():
    return pathlib.Path(os.environ.get('KPC_POTA_DIR') or 'data/pota/saved')


def offline():
    return os.environ.get('KPC_POTA_OFFLINE') == '1'


def _now():
    return time.time()


# ---------------------------------------------------------------- stored copies
def _read(p):
    p = pathlib.Path(p)
    if not p.exists(): return None
    try:
        with (gzip.open(p, 'rt', encoding='utf-8') if p.name.endswith('.gz') else open(p, encoding='utf-8')) as f: return json.load(f)
    except (OSError, ValueError): return None


def _write(p, doc):
    """Write a stored copy (LF, sorted keys, gzip without a time stamp). A copy over 1 MB is not kept (house rule): False."""
    p = pathlib.Path(p)
    if p.name.endswith('.gz'):
        body = gzip.compress((json.dumps(doc, separators=(',', ':'), sort_keys=True) + '\n').encode('utf-8'), mtime=0)
    else: body = (json.dumps(doc, indent=0, separators=(',', ':'), sort_keys=True) + '\n').encode('utf-8')
    if len(body) > MAX_FILE:
        print(f'::notice title=POTA door::{p.name} not stored: {len(body):,} bytes is over the 1 MB cap (used this run only)', flush=True)
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.tmp'); tmp.write_bytes(body); os.replace(tmp, p)
    return True


def _shard(kind, key):
    """activations: one gzip file per park (a long history is big); details / leaderboard / lookup: 256 small shared files."""
    if kind == 'activations': return root() / kind / (re.sub(r'[^A-Za-z0-9_-]', '_', str(key)) + '.json.gz')
    return root() / kind / (hashlib.sha1(str(key).encode()).hexdigest()[:2] + '.json')


def _shard_get(kind, key):
    with _LOCK: d = _read(_shard(kind, key)) or {}
    return d if kind == 'activations' and 'data' in d else d.get(str(key))


def _shard_put(kind, key, entry):
    p = _shard(kind, key)
    with _LOCK: _write(p, entry if kind == 'activations' else {**(_read(p) or {}), str(key): entry})


# ---------------------------------------------------------------- the one request
def _ask(path):
    """One paced request to POTA, counted against the budget. Raises DoorClosed when the budget is spent or offline."""
    if offline(): STAT['refused'] += 1; raise DoorClosed(f'offline: {path}')
    if STAT['asked'] >= BUDGET: STAT['refused'] += 1; raise DoorClosed(f'per-run budget of {BUDGET} POTA requests spent: {path}')
    import kpc_host_pace
    kpc_host_pace.install()
    STAT['asked'] += 1
    req = urllib.request.Request(API + path, headers={'User-Agent': UA, 'Accept': 'application/json'})
    err = None
    for i in range(2):
        try:
            with urllib.request.urlopen(req, timeout=60) as f: return json.loads(f.read().decode('utf-8', 'replace'))
        except Exception as e:  # noqa: BLE001
            err = e
            if i == 0: time.sleep(5)
    STAT['failed'] += 1
    raise DoorClosed(f'POTA did not answer {path}: {err}')


def _cached(kind, key, path, max_age=None, ask_pota=True):
    e = _shard_get(kind, key)
    age = AGES[kind] if max_age is None else max_age
    if e and _now() - e.get('saved', 0) < age: STAT['stored'] += 1; return e['data']
    if not ask_pota:
        if e: STAT['stored'] += 1; return e['data']
        raise DoorClosed(f'no stored copy of {kind} {key}')
    try: data = _ask(path)
    except DoorClosed:
        if e: STAT['stored'] += 1; return e['data']   # older than its age, but POTA may not be asked: the stored copy
        raise
    _shard_put(kind, key, {'saved': int(_now()), 'data': data})
    return data


def park(ref, ask_pota=True):
    """A park's details (/park/<ref>), 30 days."""
    return _cached('details', str(ref).upper(), '/park/' + urllib.parse.quote(str(ref)), ask_pota=ask_pota)


def activations(ref, ask_pota=True):
    """A park's activation history (/park/activations/<ref>?count=all), 30 days."""
    return _cached('activations', str(ref).upper(), f'/park/activations/{urllib.parse.quote(str(ref))}?count=all', ask_pota=ask_pota)


def leaderboard(ref, count=10, ask_pota=True):
    return _cached('leaderboard', f'{str(ref).upper()}:{count}', f'/park/leaderboard/{urllib.parse.quote(str(ref))}?count={count}', ask_pota=ask_pota)


def lookup(q, size=40, ask_pota=True):
    return _cached('lookup', f'{q}:{size}', '/lookup?search=' + urllib.parse.quote(q) + f'&size={size}', ask_pota=ask_pota)


# ---------------------------------------------------------------- locations and park lists (the park-list job asks; readers read)
def saved_locations():
    d = _read(root() / 'locations.json')
    if not d: raise DoorClosed('no saved /locations copy (the park-list job kpc_pota_parklists.py makes it)')
    STAT['stored'] += 1
    return d['data']


def saved_park_list(loc):
    """The saved park list of one location ('US-KY', 'CA-ON', 'DE-BW' ...): the saved copy only, never POTA."""
    d = _read(root() / 'parks' / f'{loc}.json.gz')
    if d is None: raise DoorClosed(f'no saved park list for {loc} (the park-list job kpc_pota_parklists.py makes it)')
    STAT['stored'] += 1
    return d['data']


def park_count(loc_row):
    for k in ('parks', 'parkCount', 'park_count'):
        if isinstance(loc_row.get(k), (int, float)): return int(loc_row[k])
    return None


def fetch_locations():
    """For the park-list job only: /locations once a day (the stored copy when it is under a day old)."""
    p = root() / 'locations.json'; d = _read(p)
    if d and _now() - d.get('saved', 0) < AGES['locations']: STAT['stored'] += 1; return d['data'], False
    data = _ask('/locations')
    _write(p, {'saved': int(_now()), 'data': data})
    return data, True


def saved_list_info(loc):
    """(saved unix time, saved count) of a saved park list, (None, None) when there is none."""
    d = _read(root() / 'parks' / f'{loc}.json.gz')
    return (d.get('saved'), d.get('count')) if d else (None, None)


def fetch_park_list(loc, count=None, due=False):
    """For the park-list job only (it decides when a list is due: kpc_pota_parklists.py). A list with no saved copy is always
    pulled; otherwise only when due. Returns (rows, pulled)."""
    p = root() / 'parks' / f'{loc}.json.gz'; d = _read(p)
    if d is not None and not due: STAT['stored'] += 1; return d['data'], False
    data = _ask('/location/parks/' + urllib.parse.quote(str(loc)))
    _write(p, {'saved': int(_now()), 'count': count if count is not None else (len(data) if isinstance(data, list) else None), 'loc': loc, 'data': data})
    return data, True


# ---------------------------------------------------------------- spots
SPOT_FILE = 'data/pota/spots.json'


def fetch_spots():
    """For the club spot reader ONLY (kpc_pota_spots.py): /spot/activator, at most once per 5 minutes (stored copy first)."""
    p = pathlib.Path(os.environ.get('KPC_POTA_SPOT_FILE') or SPOT_FILE); d = _read(p)
    if d and _now() - d.get('saved', 0) < AGES['spots']: STAT['stored'] += 1; return d['spots'], False
    return _ask('/spot/activator'), True


def club_spots(max_age=None):
    """Everyone else's spots: the club spot file (written by kpc_pota_spots.py), never POTA. Returns (spots, age_seconds)."""
    src = os.environ.get('KPC_POTA_SPOT_URL') or ''
    d = None
    if src:
        try:
            with urllib.request.urlopen(urllib.request.Request(src, headers={'User-Agent': UA}), timeout=30) as f: d = json.loads(f.read().decode('utf-8'))
        except Exception: d = None  # noqa: BLE001
    if d is None: d = _read(os.environ.get('KPC_POTA_SPOT_FILE') or SPOT_FILE)
    if not d: raise DoorClosed('no club spot file (kpc_pota_spots.py writes data/pota/spots.json)')
    age = _now() - d.get('saved', 0)
    if max_age is not None and age > max_age: raise DoorClosed(f'the club spot file is {int(age)} s old (over {max_age} s)')
    STAT['stored'] += 1
    return d.get('spots') or [], age


# ---------------------------------------------------------------- the report line
def report_line(who=None):
    who = who or pathlib.Path(sys.argv[0] or 'python').name
    return f"POTA door {who}: {STAT['asked']} asked POTA (budget {BUDGET}), {STAT['stored']} from the stored copy, {STAT['refused']} refused" + (f", {STAT['failed']} unanswered" if STAT['failed'] else '')


def _report():
    if _REPORTED[0] or not any(STAT.values()): return
    _REPORTED[0] = True
    print('::notice title=POTA door::' + report_line(), flush=True)


atexit.register(_report)


# ---------------------------------------------------------------- selftest (offline: a fake POTA)
def selftest():
    import tempfile
    ok_all, n = True, 0
    def check(name, got, want):
        nonlocal ok_all, n
        n += 1; good = got == want; ok_all &= good
        print(f"{'PASS' if good else 'SELFTEST FAIL'} {name}" + ('' if good else f' (got {got!r}, want {want!r})'))
    global _ask, _now, BUDGET
    real_ask, real_now, real_budget = _ask, _now, BUDGET
    calls, clock = [], [1_800_000_000.0]
    answers = {'/locations': [{'locationDesc': 'US-ZZ', 'parks': 2}, {'locationDesc': 'DE-ZZ', 'parks': 1}],
               '/location/parks/US-ZZ': [{'reference': 'US-9901'}, {'reference': 'US-9902'}], '/location/parks/DE-ZZ': [{'reference': 'DE-9901'}],
               '/park/US-9901': {'reference': 'US-9901', 'name': 'Test'}, '/park/activations/US-9901?count=all': [{'activeCallsign': 'N0CALL'}],
               '/spot/activator': [{'reference': 'US-9901'}]}
    def fake_ask(path):
        if STAT['asked'] >= BUDGET: STAT['refused'] += 1; raise DoorClosed('budget')
        STAT['asked'] += 1; calls.append(path); return answers[path]
    with tempfile.TemporaryDirectory() as t:
        os.environ['KPC_POTA_DIR'] = t; os.environ['KPC_POTA_SPOT_FILE'] = os.path.join(t, 'spots.json')
        _ask, _now = fake_ask, (lambda: clock[0])
        try:
            locs, pulled = fetch_locations(); check('locations: asked once', (pulled, calls), (True, ['/locations']))
            check('locations: the stored copy the same day', fetch_locations()[1], False)
            rows, pulled = fetch_park_list('US-ZZ', 2); check('US list: first pull (no saved copy)', (pulled, len(rows)), (True, 2))
            check('US list: not due -> the saved copy', fetch_park_list('US-ZZ', 2)[1], False)
            check('US list: due -> pulled', fetch_park_list('US-ZZ', 3, due=True)[1], True)
            check('the saved count goes with the list', saved_list_info('US-ZZ')[1], 3)
            fetch_park_list('DE-ZZ')
            check('world list: no count given -> the number of rows is kept', saved_list_info('DE-ZZ')[1], 1)
            check('readers read the saved list, never POTA', (len(saved_park_list('US-ZZ')), calls.count('/location/parks/US-ZZ')), (2, 2))
            try: saved_park_list('FR-ZZ'); got = 'no error'
            except DoorClosed: got = 'DoorClosed'
            check('a reader with no saved list gets DoorClosed (not a POTA call)', got, 'DoorClosed')
            n0 = len(calls); park('US-9901'); park('US-9901'); check('details: one ask, then the stored copy', len(calls) - n0, 1)
            clock[0] += 29 * DAY; park('US-9901'); check('details: 29 days later still stored', len(calls) - n0, 1)
            clock[0] += 2 * DAY; park('US-9901'); check('details: after 30 days asked again', len(calls) - n0, 2)
            n0 = len(calls); activations('US-9901'); activations('US-9901'); check('activations: one ask in 30 days', len(calls) - n0, 1)
            check('readers with ask_pota=False get the stored copy', park('US-9901', ask_pota=False)['name'], 'Test')
            sp, pulled = fetch_spots(); _write(os.environ['KPC_POTA_SPOT_FILE'], {'saved': int(clock[0]), 'spots': sp})
            check('spots: the reader asks', pulled, True)
            check('spots: under 5 minutes -> the saved file', fetch_spots()[1], False)
            check('club_spots reads the club file', len(club_spots()[0]), 1)
            BUDGET = len(calls) + 1; clock[0] += 31 * DAY
            park('US-9901')
            got = park('US-9901'.replace('1', '1'), ask_pota=True)   # stored again (fresh after the ask above)
            clock[0] += 31 * DAY
            stale = park('US-9901')   # budget spent: the old stored copy, counted as refused
            check('budget spent: the stored copy, the refusal counted', (stale['name'], STAT['refused'] >= 1), ('Test', True))
            try: lookup('nothing stored'); got = 'asked'
            except DoorClosed: got = 'DoorClosed'
            check('budget spent and nothing stored: DoorClosed', got, 'DoorClosed')
            check('report line', report_line('t').startswith(f'POTA door t: {len(calls)} asked POTA (budget {BUDGET}),'), True)
            check('club User-Agent with a contact', 'Kentucky Portable Club' in UA and 'contact:' in UA, True)
            src = pathlib.Path(__file__).read_text()
            check('paced through kpc_host_pace', 'kpc_host_pace.install()' in src, True)
        finally:
            _ask, _now, BUDGET = real_ask, real_now, real_budget
            os.environ.pop('KPC_POTA_DIR', None); os.environ.pop('KPC_POTA_SPOT_FILE', None)
            for k in STAT: STAT[k] = 0
            _REPORTED[0] = True
    print(f"SELFTEST {'PASS' if ok_all else 'FAIL'}: {n} cases")
    return 0 if ok_all else 1


if __name__ == '__main__':
    if '--selftest' in sys.argv[1:]: sys.exit(selftest())
    print(__doc__)
