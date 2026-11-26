#!/usr/bin/env python3
"""kpc_get_cross_state.py: the W11 cross-state pieces + (24 Nov) the saved-answer records the last PC test could not find, fetched once on the owner's PC and added to the PC's saved copies
(owner 23 Nov 2026 5:26 PM: "Just make me a script to get them").

What it is for. Rule W11 (23 Nov) lists, in data/state-gis.json, the records a state's saved answers need from a layer that is
saved only under ANOTHER state (a park across a state line): 'where': 'OBJECTID IN (...)'. No saved copy holds them, so the
test keys report those answers 'not found'. This script asks the agency for exactly those records, nothing else, and adds
them to links\\cache\\us\\US-XX.json.gz on this PC so START-HERE can join them.

Owner's one-time exception (23 Nov 2026 6:20 PM, 'Yes, allow it once', after audit 4 found that 22 of the 24 lists sit on
ArcGIS / Forest Service hosts the key's bots treat as saved-copy only): this person-run script may ask those hosts, once, slowly,
for exactly these records. The key builder's never-contact lines stay as they are; the keeper stays the only bot that fetches.

How it behaves (the 15 Nov host ruling: slow, one at a time, robots.txt always obeyed):
  1. lists the W11 entries whose records this PC's saved copy of that state does not already hold;
  2. reads each host's robots.txt once: a rule that says no = that host is skipped; 4xx = no rules (RFC 9309, the keeper's
     reading); 5xx / no answer = skipped (fail closed);
  3. one query per entry (only the listed OBJECTIDs, at the saved copies' detail), 5 seconds apart, and the answer must hold
     EVERY asked record, else nothing is kept for that entry;
  4. writes each answer as a checked hand file (hand-cross\\hand-US-XX.<layer>.geojson.gz, the PC helper's format);
  5. OFFLINE from here (KPC_KEY_OFFLINE=1: any network use stops the run): the key's own reader (kpc_us_key.py refill mode)
     turns each hand file into saved-copy records, and they are ADDED to the state's saved copy (nothing removed or replaced).
     The copies as they were are kept in links\\cache\\us-before-cross\\ (copy them back to undo).
Nothing goes to GitHub, nothing is published, no key is built. Run START-HERE afterwards to see the matches.

  py -3 kpc_get_cross_state.py            all states
  py -3 kpc_get_cross_state.py ID OR      only these
Report: cross-state-report.txt next to this script (counts and layer codes only).
"""
import datetime, gzip, hashlib, json, os, pathlib, re, shutil, subprocess, sys, time
import urllib.error, urllib.parse, urllib.request, urllib.robotparser

HERE = pathlib.Path(__file__).resolve().parent
LINKS = HERE / 'links'
CACHE = LINKS / 'cache' / 'us'
BEFORE = LINKS / 'cache' / 'us-before-cross'
HAND = LINKS / 'cache' / 'hand-cross'
WORK = LINKS / 'cache' / 'cross-work'
UA = 'KPC-PC-helper/1.0 (Kentucky Portable Club, a ham radio club; +https://kentuckyportableclub.github.io/KPC-Links/)'
PAUSE = 5.0
LINES = []


def say(*a):
    s = ' '.join(str(x) for x in a)
    print(s, flush=True); LINES.append(s)


def _u(u):   # the same address key as kpc_master_fill._u
    return re.sub(r'/query/?$', '', str(u or '').replace('svc:', '', 1).split('|')[0]).rstrip('/')


def ids_of(where):
    m = re.fullmatch(r'\s*OBJECTID\s+IN\s*\(([\d,\s]+)\)\s*', str(where or ''), re.I)
    return [int(x) for x in m.group(1).replace(' ', '').split(',') if x] if m else []


_SAVED = {}


def saved_ids(st):
    if st not in _SAVED:
        p = CACHE / f'US-{st}.json.gz'
        if not p.is_file(): _SAVED[st] = None
        else:
            with gzip.open(p, 'rt', encoding='utf-8') as f: _SAVED[st] = {str(r.get('OBJECTID')) for r in json.load(f).get('recs') or []}
    return _SAVED[st]


def work_list(want):
    sg = json.load(open(LINKS / 'data' / 'state-gis.json', encoding='utf-8')).get('states') or {}
    lj = json.load(open(LINKS / 'data' / 'us-key' / 'layers.json', encoding='utf-8'))
    byurl = {_u(v[0]): k for k, v in lj.items() if isinstance(v, list) and v}
    out, notes = [], []
    for st in sorted(sg):
        if want and st not in want: continue
        for l in sg[st] or []:
            ids = ids_of(l.get('where'))
            if not ids: continue
            pre = byurl.get(_u(l.get('url')))
            if not pre: notes.append(f'{st}: a listed layer has no code in layers.json; skipped'); continue
            have = saved_ids(st)
            if have is None: notes.append(f'{st} {pre}: no saved copy of {st} on this PC; skipped'); continue
            need = [i for i in ids if f'{pre}{i}' not in have]
            if not need: notes.append(f'{st} {pre}: already in the saved copy ({len(ids)})'); continue
            out.append({'st': st, 'pre': pre, 'url': _u(l['url']), 'nf': l.get('nm') or '', 'ids': need,
                        'label': (lj.get(pre) or [None, None, ''])[2] if isinstance(lj.get(pre), list) and len(lj[pre]) > 2 else '',
                        'oidf': 'OBJECTID'})
    return out, notes


def saved_answer_list(want):
    """Owner 24 Nov 2026 5:00 AM (S-G4 'what ever easiest and quickest'): the records a person's saved answer names that the
    last PC test could NOT find, not even by the saved name and size ('saved answers: not found' in reports\\test-*\\XX.log).
    One ask per state and layer, only those record ids. A record that does not come back is reported (gone or renumbered)."""
    tests = sorted((HERE / 'reports').glob('test-*'))
    if not tests: return [], ['saved answers: no PC test report yet (run START-HERE.bat first); none asked']
    lj = json.load(open(LINKS / 'data' / 'us-key' / 'layers.json', encoding='utf-8'))
    need, out = {}, []
    for lf in sorted(tests[-1].glob('??.log')):
        st = lf.stem
        if want and st not in want: continue
        for m in re.finditer(r'not found: US-\d+ ([a-z]+)([1-9]\d*) fingerprint', lf.read_text(encoding='utf-8', errors='replace')):
            if isinstance(lj.get(m.group(1)), list) and lj[m.group(1)]: need.setdefault((st, m.group(1)), set()).add(int(m.group(2)))
    for (st, pre), ids in sorted(need.items()):
        have = saved_ids(st) or set()
        ids = sorted(i for i in ids if f'{pre}{i}' not in have)
        if not ids: continue
        l = lj[pre]
        out.append({'st': st, 'pre': pre, 'url': _u(l[0]), 'nf': l[1] if len(l) > 1 else '', 'ids': ids,
                    'label': l[2] if len(l) > 2 else '', 'oidf': 'OBJECTID', 'part_ok': True})
    return out, [f"saved answers not found in {tests[-1].name}: {sum(len(e['ids']) for e in out)} record(s), {len(out)} layer list(s)"]


def join_work(a, b):
    """One ask per state and layer: the cross-state ids and the saved-answer ids together."""
    by = {}
    for e in a + b:
        k = (e['st'], e['pre'])
        if k in by:
            by[k]['ids'] = sorted(set(by[k]['ids']) | set(e['ids'])); by[k]['part_ok'] = by[k].get('part_ok') and e.get('part_ok')
        else: by[k] = dict(e)
    return [by[k] for k in sorted(by)]


def get(url, timeout=120):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, r.read()


ROBOTS = {}


def robots_ok(url):
    sp = urllib.parse.urlsplit(url); host = sp.netloc
    if host not in ROBOTS:
        rp = urllib.robotparser.RobotFileParser(); why = ''
        try:
            st, body = get(f'{sp.scheme}://{host}/robots.txt', 30)
            rp.parse(body.decode('utf-8', 'replace').splitlines()); ok = True; why = 'robots.txt read'
        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500: rp.parse([]); ok = True; why = f'robots.txt answers {e.code}: no rules'
            else: ok = False; why = f'robots.txt answers {e.code}: skipped (fail closed)'
        except Exception as e:  # noqa: BLE001
            ok = False; why = f'robots.txt not reachable ({type(e).__name__}): skipped'
        ROBOTS[host] = (rp if ok else None, why)
        say(f'  {host}: {why}'); time.sleep(PAUSE)
    rp, why = ROBOTS[host]
    if rp is None: return False, why
    path = sp.path.rstrip('/') + '/query'
    return (rp.can_fetch(UA, path) and rp.can_fetch('*', path)), why


def esri_to_geojson(g):
    rings = (g or {}).get('rings') or []
    if not rings: return None
    return {'type': 'MultiPolygon', 'coordinates': [[r] for r in rings]}   # the key reads every ring (kpc_master.geojson_to_rings)


def fetch(e):
    q = {'where': 'OBJECTID IN (%s)' % ','.join(map(str, e['ids'])), 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326,
         'maxAllowableOffset': 0.001, 'geometryPrecision': 5}
    last = ''
    host = urllib.parse.urlsplit(e['url']).netloc
    for fmt in ('geojson', 'json'):
        url = e['url'] + '/query?' + urllib.parse.urlencode(dict(q, f=fmt))
        try: st, body = get(url)
        except urllib.error.HTTPError as x:
            last = f'HTTP {x.code}'; time.sleep(PAUSE)
            if x.code == 429 or x.code >= 500:   # audit 4: a busy or failing server is not asked again this run
                ROBOTS[host] = (None, f'the server answered {last}: resting this run'); break
            continue
        except Exception as x: last = f'{type(x).__name__}: {str(x)[:120]}'; time.sleep(PAUSE); continue  # noqa: BLE001
        time.sleep(PAUSE)
        try: doc = json.loads(body.decode('utf-8'))
        except Exception: last = 'the answer was not JSON'; continue  # noqa: BLE001
        if doc.get('error'): last = f"the server said: {str(doc['error'].get('message'))[:120]}"; continue
        if doc.get('exceededTransferLimit') or (doc.get('properties') or {}).get('exceededTransferLimit'): last = 'the answer was cut short'; continue
        feats = []
        for f in doc.get('features') or []:
            if fmt == 'geojson': props, geo = f.get('properties') or {}, f.get('geometry')
            else: props, geo = f.get('attributes') or {}, esri_to_geojson(f.get('geometry'))
            feats.append({'type': 'Feature', 'properties': props, 'geometry': geo})
        return feats, body, url, ''
    return None, None, None, last


def oid_of(props):
    return next((v for k, v in props.items() if k.lower() == 'objectid'), None)


def write_hand(e, feats, body, url):
    today = datetime.date.today().isoformat()
    meta = {'area': f"US-{e['st']}", 'layer': e['pre'], 'by': 'KPC owner (PC helper, cross-state)', 'count_expected': len(e['ids']),
            'format': 1, 'label': e['label'], 'name_field': e['nf'], 'oid_field': 'OBJECTID', 'page': e['url'], 'url': e['url'],
            'source': 'hand', 'read': today,
            'raw': {'date': today, 'name': f"US-{e['st']}.{e['pre']}.query.json", 'sha256': hashlib.sha256(body).hexdigest(),
                    'size': len(body), 'source': url}}
    HAND.mkdir(parents=True, exist_ok=True)
    p = HAND / f"hand-US-{e['st']}.{e['pre']}.geojson.gz"
    with gzip.open(p, 'wt', encoding='utf-8') as f: json.dump({'type': 'FeatureCollection', 'kpc': meta, 'features': feats}, f)
    return p


def all_hosts():
    hs = set()
    for st, ls in (json.load(open(LINKS / 'data' / 'state-gis.json', encoding='utf-8')).get('states') or {}).items():
        for l in ls or []: hs.add(urllib.parse.urlsplit(str(l.get('url') or '')).netloc)
    for v in json.load(open(LINKS / 'data' / 'us-key' / 'layers.json', encoding='utf-8')).values():
        if isinstance(v, list) and v: hs.add(urllib.parse.urlsplit(str(v[0]).replace('svc:', '', 1)).netloc)
    return ','.join(sorted(h for h in hs if h))


def merge_state(st, files):
    """Offline: the key's own reader makes the records; they are ADDED to the saved copy (by record id, nothing replaced)."""
    lin, lout = WORK / 'in', WORK / 'out'
    for d in (lin, lout): shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True, exist_ok=True)
    for p in files: shutil.copy(p, lin / p.name[len('hand-'):])
    env = dict(os.environ, STATES=st, GEO_CACHE=str(CACHE), GEO_CACHE_MODE='use', KPC_REFILL_ONLY='1', KPC_LAYER_OUT=str(lout),
               KPC_LAYER_IN=str(lin), KPC_KEY_OFFLINE='1', KPC_HOLD_ON_PASS_ERROR='0', GEO_DETAIL='0.001',
               KPC_SAVED_ONLY_HOSTS=all_hosts(), PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    env.pop('KPC_MASTER_OWNS', None)
    cp = CACHE / f'US-{st}.json.gz'
    BEFORE.mkdir(parents=True, exist_ok=True)   # audit 4: the undo copy is made BEFORE anything can touch the saved copy
    if not (BEFORE / cp.name).exists(): shutil.copy(cp, BEFORE / cp.name)
    try:
        r = subprocess.run([sys.executable, '-X', 'utf8', '.github/scripts/kpc_us_key.py'], cwd=LINKS, env=env, capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=3600)
    except subprocess.TimeoutExpired:
        return f'{st}: the reader took over an hour and was stopped; the saved copy was not changed by this script'
    if r.returncode != 0: return f'{st}: the reader stopped (exit {r.returncode}); the saved copy was not changed'
    sys.path.insert(0, str(LINKS / '.github' / 'scripts'))
    import kpc_master as M   # after every fetch: it installs the never-contact guard for this process
    blob = M.load_saved(cp); have = {str(x.get('OBJECTID')) for x in blob.get('recs') or []}
    add, parts = [], []
    for lf in sorted(lout.glob(f'US-{st}.*.geojson.gz')):
        meta, feats = M.read_layer_file(lf)
        made = [(f.get('properties') or {}).get('_kpc') for f in feats]
        new = [x for x in made if x and str(x.get('OBJECTID')) not in have]
        asked = sum(1 for f in (M.read_layer_file(lin / lf.name)[1] if (lin / lf.name).exists() else feats))
        out_box = max(0, asked - len(feats))
        add += new; parts.append(f"{meta.get('layer')} +{len(new)}" + (f', {out_box} outside the state (not used here)' if out_box else ''))
    if not parts: return f'{st}: the reader made no records (see the files in {lin}); the saved copy was not changed'
    if add: M.save_saved(cp, dict(blob, recs=(blob.get('recs') or []) + add))
    return f"{st}: added {len(add)} record(s) to the saved copy ({', '.join(parts)})"


def main(argv):
    want = {a.upper() for a in argv if a.strip()}
    if not (LINKS / '.github' / 'scripts' / 'kpc_us_key.py').is_file():
        say('STOPPED: links\\ is not unpacked yet. Run START-HERE.bat once first.'); return 2
    work, notes = work_list(want)
    sa, sa_notes = saved_answer_list(want)
    work, notes = join_work(work, sa), notes + sa_notes
    say(f'KPC cross-state pieces (W11), {datetime.datetime.now():%Y-%m-%d %H:%M}')
    for n in notes: say('  ' + n)
    say(f'To ask: {len(work)} layer list(s), {sum(len(e["ids"]) for e in work)} record(s)')
    if not work: say('Nothing to fetch.'); return finish(0)
    got = {}
    say('Step 1 of 2: asking the agencies (one at a time, 5 seconds apart)')
    for e in work:
        ok, why = robots_ok(e['url'])
        tag = f"{e['st']} {e['pre']} ({len(e['ids'])})"
        if not ok: say(f'  {tag}: not asked: {why}'); continue
        feats, body, url, err = fetch(e)
        if feats is None: say(f'  {tag}: no answer ({err}); nothing kept'); continue
        back = {str(oid_of(f['properties'])) for f in feats}
        miss = [i for i in e['ids'] if str(i) not in back]
        if e.get('part_ok') and feats:   # saved-answer records stand alone: keep the whole ones, report the rest
            feats = [f for f in feats if f['geometry'] is not None]
            if miss: say(f'  {tag}: {len(miss)} record(s) did not come back (renumbered or gone: the build checks the saved name and size)')
        elif miss or any(f['geometry'] is None for f in feats):
            say(f'  {tag}: {len(feats)} of {len(e["ids"])} came back whole; nothing kept (all or nothing)'); continue
        if not feats: say(f'  {tag}: none came back; nothing kept'); continue
        got.setdefault(e['st'], []).append(write_hand(e, feats, body, url))
        say(f'  {tag}: {len(feats)} received')
    say('Step 2 of 2: adding them to this PC\'s saved copies (offline)')
    for st in sorted(got): say('  ' + merge_state(st, got[st]))
    say('Done. Now run START-HERE.bat (type the states above, or US). To undo: copy links\\cache\\us-before-cross\\* back into links\\cache\\us\\.')
    return finish(0)


def finish(rc):
    (HERE / 'cross-state-report.txt').write_text('\n'.join(LINES) + '\n', encoding='utf-8')
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
