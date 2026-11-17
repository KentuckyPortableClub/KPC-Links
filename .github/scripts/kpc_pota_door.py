#!/usr/bin/env python3
"""THE POTA DOOR (KPC owner, 2026-11-16, handoff 'proof of work', item 7: be polite to POTA). Every club script that wants
something from POTA (api.pota.app) asks here; no other script opens api.pota.app (tests/test_pota_door_nov16.py fails on a new
direct call). The door reads the STORED COPY first and asks POTA only when the copy is older than its allowed age:

  spots            relay       the club spot relay (its address in kpc-spots.json, the one setting; it asks POTA at most every
                               2 minutes); POTA directly only when the relay does not answer or its copy is over 30 minutes old
  all-parks export 1 day       all_parks_ext.csv, read once a day by the park-list job (kpc_pota_parklists.py) and compared with
                               yesterday's copy: only the changed locations' saved lists are rewritten (from the export)
  location list    only for a location the export shows CHANGED, and only when a job needs a field the export lacks
                               (/location/parks/<loc>; the park-list job decides; world ones weekly at most)
  park details     30 days     /park/<ref>
  activations      30 days     /park/activations/<ref>?count=all   (also /park/leaderboard/<ref>, /lookup)
/locations is not used. When the export is gone or too thin, the park-list job falls back to a 7-day re-pull of the US and CA
lists and says so.

Readers of park lists (world_pota, canada, northam, new_refs, pota_activity, state_links, top25, refcheck, new_lands) call
saved_park_list() / saved_locations(): the saved copy ONLY, never POTA.

Every request is paced through kpc_host_pace (one per 2 s per host) and counted against a per-run budget (KPC_POTA_BUDGET,
default 300; a run that reaches it gets the stored copy, or a DoorClosed error when it has none). The club User-Agent with a
contact is sent on every request (KPC_POTA_CONTACT replaces the contact). One report line per run (at exit):
  POTA door <script>: N asked POTA (budget B), M from the stored copy, K refused

Stored copies live in data/pota/saved/ of this repo (KPC_POTA_DIR moves them): export-index.json (yesterday's export: per location
its park count and checksum), locations.json, parks/<loc>.json.gz, <kind>/<shard>.json, receipts/<job>.json (the real numbers). Offline (KPC_POTA_OFFLINE=1): stored copies only.
  python3 kpc_pota_door.py --selftest
"""
import atexit, gzip, hashlib, json, os, pathlib, re, sys, threading, time, urllib.error, urllib.parse, urllib.request
import kpc_net_guard; kpc_net_guard.install()   # never-contact hosts refused before any request

API = 'https://api.pota.app'
MAX_FILE = 1_000_000   # house rule: 1 MB per file
HOST = 'api.pota.app'
CONTACT = os.environ.get('KPC_POTA_CONTACT') or 'https://github.com/KentuckyPortableClub/KPC-Links/issues'
UA = f'KPC-Links/1.0 (Kentucky Portable Club; +https://kentuckyportableclub.github.io/KPC-Links/; contact: {CONTACT})'
DAY = 86400
AGES = {'export': DAY - 3600, 'details': 30 * DAY, 'activations': 30 * DAY, 'leaderboard': 30 * DAY, 'lookup': 30 * DAY}
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
    STAT_KIND[kind] = STAT_KIND.get(kind, 0) + 1
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


# ---------------------------------------------------------------- the all-parks export and the park lists (the park-list job asks; readers read)
# KPC owner, 2026-11-16 (v4 answer 2): POTA's ONE all-parks export (all_parks_ext.csv: reference, name, active, entityId, locationDesc,
# latitude, longitude, grid) is read once a day and compared with yesterday's saved copy (export-index.json: per location its park
# count and a checksum). The difference names the states, provinces and countries that changed; only those saved lists are rewritten,
# from the export itself (no POTA call). /locations is not used. /location/parks/<loc> is asked only for a CHANGED location and only
# when a job needs a field the export lacks (activations, attempts, qsos, parktypeDesc: kpc_pota_parklists.py decides).
EXPORT_URL = os.environ.get('KPC_POTA_EXPORT_URL') or 'https://pota.app/all_parks_ext.csv'
EXPORT_FIELDS = ('reference', 'name', 'active', 'entityId', 'locationDesc', 'latitude', 'longitude', 'grid')
EXPORT_NEEDS = ('reference', 'name', 'locationDesc', 'latitude', 'longitude')   # less than this = too thin: the 7-day fallback
EXTRA_FIELDS = ('activations', 'attempts', 'qsos', 'parktypeDesc', 'parktypeId', 'accessibility', 'sensitivity', 'firstActivator', 'firstActivationDate')


class ExportGone(DoorClosed):
    """The export is not published any more (404 / 410) or lacks the fields the readers need."""


def _ask_export(etag='', modified=''):
    """One paced, budgeted GET of the export, conditional on yesterday's ETag / Last-Modified. (status, text, etag, modified)."""
    if offline(): STAT['refused'] += 1; raise DoorClosed('offline: all_parks_ext.csv')
    if STAT['asked'] >= BUDGET: STAT['refused'] += 1; raise DoorClosed(f'per-run budget of {BUDGET} POTA requests spent: all_parks_ext.csv')
    import kpc_host_pace
    kpc_host_pace.install()
    STAT['asked'] += 1; STAT_KIND['export'] = STAT_KIND.get('export', 0) + 1
    h = {'User-Agent': UA, 'Accept': 'text/csv'}
    if etag: h['If-None-Match'] = etag
    if modified: h['If-Modified-Since'] = modified
    err = None
    for i in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(EXPORT_URL, headers=h), timeout=180) as f:
                return 200, f.read().decode('utf-8-sig', 'replace'), f.headers.get('ETag') or '', f.headers.get('Last-Modified') or ''
        except urllib.error.HTTPError as e:
            if e.code == 304: return 304, '', etag, modified
            if e.code in (403, 404, 410): STAT['failed'] += 1; raise ExportGone(f'all_parks_ext.csv answered HTTP {e.code}')
            err = e
        except Exception as e:  # noqa: BLE001
            err = e
        if i == 0: time.sleep(5)
    STAT['failed'] += 1
    raise DoorClosed(f'all_parks_ext.csv not read: {err}')


def export_by_location(text, inactive=None):
    """{location: [park rows]} from the export text: ACTIVE parks only (as /location/parks lists them); a park in several locations
    ('US-KY,US-TN,US-VA') is in each. inactive (a set) collects the references the `active` column flags as retired. Raises
    ExportGone when the header lacks a field the readers need."""
    import csv, io
    rd = csv.DictReader(io.StringIO(text))
    miss = [f for f in EXPORT_NEEDS if f not in (rd.fieldnames or [])]
    if miss: raise ExportGone(f'all_parks_ext.csv lacks {", ".join(miss)}')
    out = {}
    for r in rd:
        if str(r.get('active', '1')).strip() not in ('1', 'true', 'True'):
            if inactive is not None and r.get('reference'): inactive.add(str(r['reference']).strip())
            continue
        row = {k: r.get(k) for k in EXPORT_FIELDS if k in r}
        for k in ('latitude', 'longitude'):
            try: row[k] = float(row[k])
            except (TypeError, ValueError): row[k] = None
        for k in ('active', 'entityId'):
            try: row[k] = int(row[k])
            except (TypeError, ValueError): pass
        for loc in [x.strip() for x in str(r.get('locationDesc') or '').split(',') if x.strip()]: out.setdefault(loc, []).append(row)
    return out


def _sha(rows):
    return hashlib.sha1(json.dumps(sorted((json.dumps(r, sort_keys=True) for r in rows)), separators=(',', ':')).encode()).hexdigest()[:16]


def export_index():
    return _read(root() / 'export-index.json') or {}


def sync_export():
    """For the park-list job only. Reads the export at most once a day; rewrites the saved list of every location whose rows changed
    since yesterday's copy (the count fields a location's last /location/parks read had are kept per park). Returns a summary dict:
    asked (bool), not_modified, parks, locations, changed [locs], removed [locs]."""
    idx = export_index(); now = int(_now())
    if idx and now - idx.get('saved', 0) < AGES['export']:
        STAT['stored'] += 1
        return {'asked': False, 'not_modified': False, 'parks': idx.get('parks', 0), 'locations': len(idx.get('locations') or {}), 'changed': [], 'removed': []}
    status, text, etag, modified = _ask_export(idx.get('etag', ''), idx.get('modified', ''))
    if status == 304:
        idx['saved'] = now; _write(root() / 'export-index.json', idx)
        return {'asked': True, 'not_modified': True, 'parks': idx.get('parks', 0), 'locations': len(idx.get('locations') or {}), 'changed': [], 'removed': []}
    inactive = set(); by = export_by_location(text, inactive)
    if len(by) < 100: raise ExportGone(f'all_parks_ext.csv holds only {len(by)} locations (too thin)')
    old = idx.get('locations') or {}
    new = {loc: [len(rows), _sha(rows)] for loc, rows in by.items()}
    changed = sorted(loc for loc in new if (old.get(loc) or [None, None])[1] != new[loc][1] or not (root() / 'parks' / f'{loc}.json.gz').exists())
    removed = sorted(set(old) - set(new))
    # v5 (owner, Nov 16): act only on the ROWS that changed against yesterday's copy. Per changed location the rows are compared
    # with the saved list: added (new park), retired (the `active` column now flags it), changed (name / pin / grid / entity /
    # locations), gone (no longer in this location, not retired). A first copy names none.
    new_parks, rows = {}, {'added': [], 'retired': [], 'changed': [], 'gone': []}
    for loc in changed + removed:
        was = _read(root() / 'parks' / f'{loc}.json.gz')
        if was is None: continue
        old_rows = {str(r.get('reference')): r for r in (was.get('data') or []) if isinstance(r, dict)}
        now_rows = {str(r['reference']): r for r in by.get(loc, [])}
        fresh = sorted(set(now_rows) - set(old_rows))
        if fresh: new_parks[loc] = fresh; rows['added'] += [[loc, x] for x in fresh]
        for ref in sorted(set(old_rows) - set(now_rows)): rows['retired' if ref in inactive else 'gone'].append([loc, ref])
        for ref in sorted(set(old_rows) & set(now_rows)):
            diff = sorted(k for k in EXPORT_FIELDS if k in old_rows[ref] and old_rows[ref].get(k) != now_rows[ref].get(k))
            if diff: rows['changed'].append([loc, ref, diff])
    for loc in changed: _write_list(loc, by[loc], 'export')
    for loc in removed: _write_list(loc, [], 'export')
    names = {str(l.get('locationDesc')): l for l in ((_read(root() / 'locations.json') or {}).get('data') or []) if isinstance(l, dict)}
    _write(root() / 'locations.json', {'saved': now, 'source': 'all_parks_ext.csv', 'data': [
        {**{k: v for k, v in (names.get(loc) or {}).items() if k not in ('parks',)}, 'locationDesc': loc, 'parks': new[loc][0]} for loc in sorted(new)]})
    parks = len({r['reference'] for rows in by.values() for r in rows})
    first = not old   # the first export copy: nothing to compare with, so no location counts as changed for the list calls
    _write(root() / 'export-index.json', {'saved': now, 'etag': etag, 'modified': modified, 'parks': parks, 'locations': new,
                                          'extra_due': sorted(set(idx.get('extra_due') or []) | (set() if first else set(new_parks)))})
    # the count fields (activations, attempts, qsos) exist only per list call: only a location with NEW parks needs one (a retired,
    # renamed or moved row keeps its counts), so only those are queued
    _write(root() / 'export-changes.json', {'saved': now, 'first_copy': first, 'retired_in_export': len(inactive),
                                            **{k: v[:2000] for k, v in rows.items()}, 'counts': {k: len(v) for k, v in rows.items()}})
    return {'asked': True, 'not_modified': False, 'parks': parks, 'locations': len(new), 'changed': [] if first else changed,
            'written': len(changed), 'removed': removed, 'first_copy': first, 'new_parks': new_parks,
            'rows': {k: len(v) for k, v in rows.items()}, 'list_due': [] if first else sorted(new_parks)}


def _write_list(loc, rows, source):
    """Save one location's list; per park, the extra fields of the last /location/parks read are kept (the export lacks them)."""
    p = root() / 'parks' / f'{loc}.json.gz'; old = _read(p) or {}
    keep = {str(r.get('reference')): {k: r[k] for k in EXTRA_FIELDS if k in r} for r in (old.get('data') or []) if isinstance(r, dict)}
    if source == 'export': rows = [{**keep.get(str(r.get('reference')), {}), **r} for r in rows]
    doc = {'saved': int(_now()), 'source': source, 'loc': loc, 'count': len(rows), 'data': rows,
           'extra_saved': int(_now()) if source == 'api' else old.get('extra_saved')}
    _write(p, doc)


def saved_locations():
    d = _read(root() / 'locations.json')
    if not d: raise DoorClosed('no saved locations list (the park-list job kpc_pota_parklists.py makes it from all_parks_ext.csv)')
    STAT['stored'] += 1
    return d['data']


def saved_park_list(loc):
    """The saved park list of one location ('US-KY', 'CA-ON', 'DE-BW' ...): the saved copy only, never POTA. A location the export
    lists no active park for is an empty list."""
    d = _read(root() / 'parks' / f'{loc}.json.gz')
    if d is None:
        if export_index().get('locations') is not None and loc not in export_index()['locations']: STAT['stored'] += 1; return []
        raise DoorClosed(f'no saved park list for {loc} (the park-list job kpc_pota_parklists.py makes it)')
    STAT['stored'] += 1
    return d['data']


def saved_list_info(loc):
    """(saved unix time, park count, source, extra_saved) of a saved park list; Nones when there is none."""
    d = _read(root() / 'parks' / f'{loc}.json.gz')
    return (d.get('saved'), d.get('count'), d.get('source'), d.get('extra_saved')) if d else (None, None, None, None)


def fetch_park_list(loc):
    """For the park-list job only: /location/parks/<loc> for a location it chose (changed in the export and a job needs a field
    the export lacks; or the 7-day fallback when the export is gone). Saves it; returns the rows."""
    data = _ask('/location/parks/' + urllib.parse.quote(str(loc)))
    STAT_KIND['list'] = STAT_KIND.get('list', 0) + 1
    _write_list(loc, data if isinstance(data, list) else [], 'api')
    return data


# ---------------------------------------------------------------- spots
# KPC owner, 2026-11-16 (item 7, the spot relay): live spots come from the club spot relay, which reads POTA's spot list at most
# once every 2 minutes and serves the saved copy with the header x-kpc-spot-age (seconds since POTA was last asked). Its address is
# in ONE setting, kpc-spots.json at the top of this repo (the pages read the same file). A reader goes to POTA directly only when
# the relay does not answer or its copy is over stale_seconds (30 minutes) old.
SPOT_CONFIG = pathlib.Path(__file__).resolve().parents[2] / 'kpc-spots.json'
SPOT_STALE = 1800   # 30 minutes (kpc-spots.json stale_seconds wins)


def spot_setting():
    """kpc-spots.json: {'relay': url, 'age_header': name, 'stale_seconds': n}. KPC_SPOT_CONFIG = another copy (tests)."""
    try: d = json.loads(pathlib.Path(os.environ.get('KPC_SPOT_CONFIG') or SPOT_CONFIG).read_text(encoding='utf-8'))
    except Exception: d = {}  # noqa: BLE001
    return {'relay': str(d.get('relay') or ''), 'age_header': str(d.get('age_header') or 'x-kpc-spot-age'),
            'stale_seconds': int(d.get('stale_seconds') or SPOT_STALE)}


def relay_spots(cfg=None):
    """One read of the relay -> (spots, age_s) or (None, why). Never POTA."""
    cfg = cfg or spot_setting()
    if not cfg['relay'].startswith('https://'): return None, 'no relay address in kpc-spots.json'
    try:
        with urllib.request.urlopen(urllib.request.Request(cfg['relay'], headers={'User-Agent': UA}), timeout=20) as f:
            age = f.headers.get(cfg['age_header']); data = json.loads(f.read().decode('utf-8'))
    except Exception as e:  # noqa: BLE001
        return None, f'the relay did not answer ({type(e).__name__})'
    if isinstance(data, dict): data = data.get('spots')
    if not isinstance(data, list): return None, 'the relay answered without a spot list'
    try: age = max(0, int(float(age)))
    except (TypeError, ValueError): age = None
    return data, age


def club_spots(max_age=None):
    """Everyone's spots: the club spot relay (kpc-spots.json). When it does not answer, or its copy is over max_age (stale_seconds,
    30 minutes) old, POTA's spot list is read directly through the door (paced and counted). KPC_POTA_SPOT_FILE = a local
    {saved, spots} copy instead of the relay (tests only). Returns (spots, age_s)."""
    cfg = spot_setting(); max_age = cfg['stale_seconds'] if max_age is None else max_age
    loc = os.environ.get('KPC_POTA_SPOT_FILE')
    if loc:
        d = _read(loc); sp, age = (d.get('spots') or [], int(_now() - d.get('saved', 0))) if d else (None, 'the local copy is missing')
    else: sp, age = relay_spots(cfg)
    if sp is not None and (age is None or age <= max_age): STAT['stored'] += 1; STAT_KIND['spots_relay'] = STAT_KIND.get('spots_relay', 0) + 1; return sp, age
    why = age if isinstance(age, str) else f'the relay copy is {age} s old (over {max_age} s)'
    print(f"::notice title=POTA door::{why}: POTA's spot list read directly", flush=True)
    data = _ask('/spot/activator'); STAT_KIND['spots_fallback'] = STAT_KIND.get('spots_fallback', 0) + 1
    return data or [], 0


# ---------------------------------------------------------------- the report line and the receipt
STAT_KIND = {}


def receipt(extra=None):
    """The real numbers of this run (v4 answer 3): requests by kind, stored-copy reads, refusals."""
    return {'script': pathlib.Path(sys.argv[0] or 'python').name, 'when': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(_now())),
            'pota_requests': STAT['asked'], 'asked_pota': STAT['asked'], 'by_kind': dict(sorted(STAT_KIND.items())), 'from_stored_copy': STAT['stored'],
            'refused_by_budget_or_offline': STAT['refused'], 'unanswered': STAT['failed'], 'budget': BUDGET, **(extra or {})}


def write_receipt(extra=None, name=None):
    """Save the receipt in data/pota/saved/receipts/<script>.json (saved by the jobs that save data/pota/saved)."""
    doc = receipt(extra)
    _write(root() / 'receipts' / ((name or doc['script'].rsplit('.', 1)[0]) + '.json'), doc)
    return doc


def report_line(who=None):
    who = who or pathlib.Path(sys.argv[0] or 'python').name
    kinds = ', '.join(f'{k} {v}' for k, v in sorted(STAT_KIND.items()))
    return (f"POTA door {who}: {STAT['asked']} asked POTA (budget {BUDGET}){f' ({kinds})' if kinds else ''}, {STAT['stored']} from the stored copy, "
            f"{STAT['refused']} refused" + (f", {STAT['failed']} unanswered" if STAT['failed'] else ''))


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
    global _ask, _ask_export, _now, BUDGET
    real = (_ask, _ask_export, _now, BUDGET)
    calls, clock = [], [1_800_000_000.0]
    head = 'reference,name,active,entityId,locationDesc,latitude,longitude,grid\n'
    def csv_of(extra=''):
        rows = [f'XX-{i:04d},Park {i},1,1,XX-{i % 120:03d},1.0,2.0,AA00' for i in range(240)]
        return head + '\n'.join(rows + ['US-9901,Test One,1,291,US-ZZ,37.1,-85.1,EM77', 'US-9902,Test Two,1,291,"US-ZZ,US-YY",37.2,-85.2,EM77',
                                        'US-9903,Gone Park,0,291,US-ZZ,37.3,-85.3,EM77']) + extra + '\n'
    export = {'text': csv_of(), 'etag': 'e1'}
    answers = {'/location/parks/US-ZZ': [{'reference': 'US-9901', 'name': 'Test One', 'activations': 7, 'attempts': 8, 'locationDesc': 'US-ZZ'},
                                         {'reference': 'US-9902', 'name': 'Test Two', 'activations': 1, 'attempts': 1, 'locationDesc': 'US-ZZ,US-YY'}],
               '/park/US-9901': {'reference': 'US-9901', 'name': 'Test'}, '/park/activations/US-9901?count=all': [{'activeCallsign': 'N0CALL'}],
               '/spot/activator': [{'reference': 'US-9901'}]}
    def fake_ask(path):
        if STAT['asked'] >= BUDGET: STAT['refused'] += 1; raise DoorClosed('budget')
        STAT['asked'] += 1; calls.append(path); return answers[path]
    def fake_export(etag='', modified=''):
        if STAT['asked'] >= BUDGET: STAT['refused'] += 1; raise DoorClosed('budget')
        STAT['asked'] += 1; calls.append('export'); STAT_KIND['export'] = STAT_KIND.get('export', 0) + 1
        if export.get('gone'): raise ExportGone('HTTP 404')
        if etag and etag == export['etag']: return 304, '', etag, ''
        return 200, export['text'], export['etag'], ''
    with tempfile.TemporaryDirectory() as t:
        os.environ['KPC_POTA_DIR'] = t; os.environ['KPC_POTA_SPOT_FILE'] = os.path.join(t, 'spots.json')
        _ask, _ask_export, _now = fake_ask, fake_export, (lambda: clock[0])
        try:
            r = sync_export()
            check('export: one request, every location written from it (no list call); a first copy marks nothing changed', (r['asked'], calls, r['written'], r['changed'], r['first_copy']), (True, ['export'], 122, [], True))
            check('export: active parks only; a park in two locations is in both', ([x['reference'] for x in saved_park_list('US-ZZ')], [x['reference'] for x in saved_park_list('US-YY')]), (['US-9901', 'US-9902'], ['US-9902']))
            check('export: locations list made from the export (no /locations)', {l['locationDesc']: l['parks'] for l in saved_locations()}.get('US-ZZ'), 2)
            check('export: the same day -> the stored copy, no request', (sync_export()['asked'], len(calls)), (False, 1))
            clock[0] += DAY; r = sync_export()
            check('export: next day, unchanged (304) -> nothing changed', (r['not_modified'], r['changed']), (True, []))
            clock[0] += DAY; export.update(text=csv_of('\nUS-9904,New Park,1,291,US-ZZ,37.4,-85.4,EM77'), etag='e2'); r = sync_export()
            check('export: a new park -> only its location changed, the new park named', (r['changed'], r['new_parks'], export_index()['extra_due']), (['US-ZZ'], {'US-ZZ': ['US-9904']}, ['US-ZZ']))
            check('export: the changed list has the new park', len(saved_park_list('US-ZZ')), 3)
            answers['/location/parks/US-ZZ'].append({'reference': 'US-9904', 'name': 'New Park', 'activations': 0, 'attempts': 0, 'locationDesc': 'US-ZZ'})
            rows = fetch_park_list('US-ZZ')
            check('a list call for a changed location keeps the extra fields', saved_park_list('US-ZZ')[0].get('activations'), 7)
            clock[0] += DAY; export.update(text=csv_of('\nUS-9904,New Park Renamed,1,291,US-ZZ,37.4,-85.4,EM77'), etag='e3'); r = sync_export()
            check('rows: a renamed park is one changed row (name), no list call due', (r['rows'], r['list_due'], _read(root() / 'export-changes.json')['changed']),
                  ({'added': 0, 'retired': 0, 'changed': 1, 'gone': 0}, [], [['US-ZZ', 'US-9904', ['name']]]))
            check('export rewrite of a location keeps each park\'s extra fields from its last list call', (saved_park_list('US-ZZ')[0].get('activations'), saved_list_info('US-ZZ')[2]), (7, 'export'))
            clock[0] += DAY; export.update(text=csv_of('\nUS-9904,New Park Renamed,0,291,US-ZZ,37.4,-85.4,EM77'), etag='e4'); r = sync_export()
            check('rows: the active column retiring a park -> one retired row, it leaves the list, no list call due',
                  (r['rows']['retired'], _read(root() / 'export-changes.json')['retired'], [x['reference'] for x in saved_park_list('US-ZZ')], r['list_due']),
                  (1, [['US-ZZ', 'US-9904']], ['US-9901', 'US-9902'], []))
            check('receipt: the POTA request count is always shown', receipt()['pota_requests'], len(calls))
            try: saved_park_list('FR-ZZ'); got = 'no error'
            except DoorClosed: got = 'DoorClosed'
            check('a location with no active park in the export is an empty list', got, 'no error')
            check('too thin: a header without latitude is refused', _raises(lambda: export_by_location('reference,name,locationDesc\nA,B,C\n'), ExportGone), True)
            clock[0] += DAY; export['gone'] = True
            check('export gone -> ExportGone (the job falls back to the 7-day re-pull)', _raises(sync_export, ExportGone), True)
            n0 = len(calls); park('US-9901'); park('US-9901'); check('details: one ask, then the stored copy', len(calls) - n0, 1)
            clock[0] += 29 * DAY; park('US-9901'); check('details: 29 days later still stored', len(calls) - n0, 1)
            clock[0] += 2 * DAY; park('US-9901'); check('details: after 30 days asked again', len(calls) - n0, 2)
            n0 = len(calls); activations('US-9901'); activations('US-9901'); check('activations: one ask in 30 days', len(calls) - n0, 1)
            check('readers with ask_pota=False get the stored copy', park('US-9901', ask_pota=False)['name'], 'Test')
            _write(os.environ['KPC_POTA_SPOT_FILE'], {'saved': int(clock[0]), 'spots': [{'reference': 'US-9901'}]})
            n0 = len(calls); check('club_spots with a local copy: no POTA request', (len(club_spots()[0]), len(calls) - n0), (1, 0))
            clock[0] += 16 * 60; n0 = len(calls); check('a copy 16 minutes old is still used (no request)', (len(club_spots()[0]), len(calls) - n0), (1, 0))
            clock[0] += 15 * 60; n0 = len(calls)
            with __import__('contextlib').redirect_stdout(__import__('io').StringIO()): got = club_spots()
            check('a copy over 30 minutes old -> POTA read directly (one request)', (len(got[0]), len(calls) - n0), (1, 1))
            # the relay (kpc-spots.json, the one setting): its x-kpc-spot-age is the age; POTA only when it does not answer / is stale
            os.environ.pop('KPC_POTA_SPOT_FILE', None)
            cfgf = os.path.join(t, 'kpc-spots.json'); os.environ['KPC_SPOT_CONFIG'] = cfgf
            _write(cfgf, {'relay': 'https://relay.test/spots', 'age_header': 'x-kpc-spot-age', 'stale_seconds': 1800})
            relay = {'age': '30', 'fail': False, 'asked': 0}
            class _Resp:
                def __init__(s): s.headers = {'x-kpc-spot-age': relay['age']}
                def read(s): return json.dumps([{'reference': 'US-9901'}, {'reference': 'US-9902'}]).encode()
                def __enter__(s): return s
                def __exit__(s, *a): return False
            def _open(req, timeout=None):
                relay['asked'] += 1
                assert req.full_url == 'https://relay.test/spots', req.full_url
                if relay['fail']: raise urllib.error.URLError('down')
                return _Resp()
            _uo = urllib.request.urlopen; urllib.request.urlopen = _open
            try:
                n0 = len(calls); got = club_spots()
                check('relay answers: its spots and its x-kpc-spot-age, no POTA request', (len(got[0]), got[1], len(calls) - n0), (2, 30, 0))
                relay['age'] = '4000'; n0 = len(calls)
                with __import__('contextlib').redirect_stdout(__import__('io').StringIO()): got = club_spots()
                check('relay copy over 30 minutes old -> POTA read directly (one request)', len(calls) - n0, 1)
                relay['fail'] = True; n0 = len(calls)
                with __import__('contextlib').redirect_stdout(__import__('io').StringIO()): got = club_spots()
                check('relay does not answer -> POTA read directly (one request)', len(calls) - n0, 1)
                check('the relay address comes from the one setting', relay['asked'], 3)
            finally:
                urllib.request.urlopen = _uo; os.environ.pop('KPC_SPOT_CONFIG', None)
            rc = receipt({'x': 1})
            check('receipt: the real numbers by kind', (rc['asked_pota'] == len(calls), rc['by_kind'].get('export'), rc['by_kind'].get('details'), rc['x']), (True, 6, 2, 1))
            BUDGET = len(calls); clock[0] += 31 * DAY
            stale = park('US-9901')
            check('budget spent: the stored copy, the refusal counted', (stale['name'], STAT['refused'] >= 1), ('Test', True))
            check('budget spent and nothing stored: DoorClosed', _raises(lambda: lookup('nothing stored'), DoorClosed), True)
            check('report line', report_line('t').startswith(f'POTA door t: {len(calls)} asked POTA (budget {BUDGET}) ('), True)
            check('club User-Agent with a contact', 'Kentucky Portable Club' in UA and 'contact:' in UA, True)
            src = pathlib.Path(__file__).read_text()
            check('paced through kpc_host_pace; /locations is never asked', ('kpc_host_pace.install()' in src, "_ask('/loc" + "ations')" in src), (True, False))
        finally:
            _ask, _ask_export, _now, BUDGET = real
            os.environ.pop('KPC_POTA_DIR', None); os.environ.pop('KPC_POTA_SPOT_FILE', None)
            for k in STAT: STAT[k] = 0
            STAT_KIND.clear(); _REPORTED[0] = True
    print(f"SELFTEST {'PASS' if ok_all else 'FAIL'}: {n} cases")
    return 0 if ok_all else 1


def _raises(fn, exc):
    try: fn()
    except exc: return True
    except Exception: return False  # noqa: BLE001
    return False


if __name__ == '__main__':
    if '--selftest' in sys.argv[1:]: sys.exit(selftest())
    print(__doc__)
