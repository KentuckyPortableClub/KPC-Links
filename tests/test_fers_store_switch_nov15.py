#!/usr/bin/env python3
"""KPC owner, 2026-11-15: the 2-fer switch-over to the outline store (kpc_fers.main() hook, kpc_fers_store.py in the 2-fer rules).
Offline: proxy variables dropped; the real kpc_fers.py runs in subprocesses on made-up fixtures (tests/fixtures/fers-store-v4: an
area, a line, a pin and one water tile; made-up squares and made-up park refs US-99001..US-99006 filed under US-RI).
1 switch OFF: kpc_fers.py's files are byte for byte main's on the fixture (passes 1-3): with main's scope file, every file (the
  report's own fers_rules hash aside); with this change's declared scope entry, every spot / looked / missing file (only the pair
  fingerprints in the reuse files move: the declared rule change re-stamps US and Canadian pairs)
2 switch ON (passes 1-3): zero sockets (a Python audit hook sees every connect / name lookup / urllib request at C level, whatever
  is patched), the store's area, line and water tile are used, the pin is never a boundary
3 keep the old row: a live candidate that the store run leaves NOT SURE only because closed areas were not checked keeps its old
  row, tagged 'kept: not checked in a store run'; a pair the store run decides (water only from the store's water tile) is never
  kept; unit checks for ownership, ids, ambiguous pairs, non-candidates
4 the leak guard still exits 89 (a never-released build carried from the last file)
5 the area list: all US + Canadian areas, an except list, US-KY never; an area the store does not hold is left out with its reason
  and the run goes on; a broken list or a run naming no area stops (exit 87)
6 Kentucky runs never use the store; world runs never use it while "world" is "off" (exactly main's notice, nothing replaced); with
  it on: a private store run only, a made-up world area is read, a WDPA-derived world record is refused, publish refuses world rows
7 hashes: fers moves only by its newest declared changelog line; US, CA and world unchanged"""
import gzip, json, os, pathlib, re, shutil, subprocess, sys, tempfile

for k in list(os.environ):
    if 'proxy' in k.lower(): os.environ.pop(k)
ROOT = pathlib.Path(__file__).resolve().parent.parent
SCR = ROOT / '.github' / 'scripts'
FIX = ROOT / 'tests' / 'fixtures' / 'fers-store-v4'
sys.path.insert(0, str(SCR))
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok: FAILS.append(what)


import kpc_fers_store as ST  # noqa: E402

try:
    import numpy, cv2  # noqa: F401
    HAVE = True
except Exception: HAVE = False  # noqa: BLE001
TMP = pathlib.Path(tempfile.mkdtemp(prefix='kpc-fers-switch-'))

# ---------------------------------------------------------------- 5 the area list
cfg, why = ST.store_areas()
check(cfg == {'all': True, 'list': set(), 'except': set(), 'world': False} and not why,
      f'the area list: every US and Canadian area the store holds, nothing excepted, world off ({cfg})')
check(ST.area_use('US-RI', cfg) == '' and ST.area_use('US-DE', cfg) == '' and ST.area_use('CA-ON', cfg) == '' and ST.area_use('US-WY', cfg) == '',
      'every US state and Canadian province may use the store (no two-state start)')
check('Kentucky' in ST.area_use('US-KY', cfg) and 'world' in ST.area_use('W-FR', cfg), 'US-KY never; a world area not while the world switch is off')
def cfg_file(doc):
    p = TMP / f'areas-{abs(hash(json.dumps(doc, sort_keys=True)))}.json'; p.write_text(json.dumps(doc) if not isinstance(doc, str) else doc); return p
c2, _ = ST.store_areas(cfg_file({'areas': 'all-us-ca', 'except': ['US-DE'], 'world': 'off'}))
check('except list' in ST.area_use('US-DE', c2) and ST.area_use('US-RI', c2) == '', 'except list: an area on it stays on the old path; the others use the store')
c3, _ = ST.store_areas(cfg_file({'areas': ['US-RI'], 'except': []}))
check(ST.area_use('US-RI', c3) == '' and 'not listed' in ST.area_use('US-DE', c3), 'a plain list of areas works too')
for bad, what in (('{', 'not JSON'), ({'areas': 'everything'}, 'an unknown areas word'), ({'areas': ['W-FR']}, 'a world code in areas'),
                  ({'areas': 'all-us-ca', 'except': 'US-RI'}, 'except not a list'), ({'areas': 'all-us-ca', 'world': 'yes'}, 'world not on / off')):
    cb, wb = ST.store_areas(cfg_file(bad))
    check(cb is None and wb, f'a broken area list fails closed ({what}: {wb[:70]})')

# ---------------------------------------------------------------- unit: keep the old row
old = {'spots': [{'id': 'A@1', 'refs': ['US-1', 'US-2'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1], 'checked': '2026-11-01'},
                 {'id': 'B@1', 'refs': ['US-3', 'US-4'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1]},
                 {'id': 'C@1', 'refs': ['US-5', 'US-6'], 'kind': 'area', 'status': 'not sure: low-confidence outline'},
                 {'id': 'D@1', 'refs': ['US-7', 'US-8'], 'kind': 'area', 'status': 'candidate'}, {'id': 'D@2', 'refs': ['US-7', 'US-8'], 'kind': 'area', 'status': 'candidate'},
                 {'id': 'E@1', 'refs': ['US-9', 'US-10'], 'kind': 'trail', 'status': 'very tight: could be map error: check both official maps on the ground'},
                 {'id': 'F@1', 'refs': ['US-11', 'US-12'], 'kind': 'area', 'status': 'candidate'}]}
cl = 'not sure: closed areas not checked (x): the store must carry them first'
new = {'spots': [{'id': 'A@2', 'refs': ['US-2', 'US-1'], 'kind': 'area', 'status': cl, 'store_not_checked': 'closed areas'},       # pair match
                 {'id': 'B@1', 'refs': ['US-3', 'US-4'], 'kind': 'area', 'status': 'water only: boat or kayak'},                     # decided: not kept
                 {'id': 'C@1', 'refs': ['US-5', 'US-6'], 'kind': 'area', 'status': cl, 'store_not_checked': 'closed areas'},          # old not a candidate
                 {'id': 'D@9', 'refs': ['US-7', 'US-8'], 'kind': 'area', 'status': cl, 'store_not_checked': 'closed areas'},          # two old rows: no guess
                 {'id': 'E@1', 'refs': ['US-9', 'US-10'], 'kind': 'trail', 'status': 'not sure: the agency ownership map did not answer'},
                 {'id': 'F@1', 'refs': ['US-11', 'US-12'], 'kind': 'area', 'status': 'not sure: closed areas not checked (x; the water was not checked either)'}]}
ST.owner_status(new)
n = ST.keep_old_rows(new, old, '2026-11-15')
by = {x['id']: x for x in new['spots']}
check(n == 2 and by['A@1']['status'] == 'candidate' and by['A@1']['kept'] == 'kept: not checked in a store run' and 'closed areas' in by['A@1']['kept_why']
      and by['A@1']['checked'] == '2026-11-01' and by['A@1']['passes'] == [1, 1, 1],
      'keep: a candidate left NOT SURE only because closed areas were not checked keeps its old row (old date and passes), tagged')
check(by['E@1']['status'].startswith('very tight') and by['E@1']['kept'] == ST.KEPT_TAG and 'ownership' in by['E@1']['kept_why'],
      'keep: the same when only the ownership map could not be read')
check(by['B@1']['status'] == 'water only: boat or kayak' and by['C@1']['status'] == cl and by['D@9']['status'] == cl and by['F@1']['status'].startswith('not sure: closed')
      and not any('kept' in by[k] for k in ('B@1', 'C@1', 'D@9', 'F@1')),
      'keep: never a row the run decided (water only), never an old row that was not a candidate, never a guess between two old rows, never when the water was not checked either')
check(not any('store_prev' in x for x in new['spots']), 'keep: the final pass leaves no carried copy in the file')
d1 = {'spots': [{'id': 'A@2', 'refs': ['US-1', 'US-2'], 'kind': 'area', 'status': 'pass 1', 'passes': [1, 0, 0]}]}
ST.keep_old_rows(d1, old, '2026-11-15', final=False)
d3 = {'spots': [{'id': 'A@3', 'refs': ['US-1', 'US-2'], 'kind': 'area', 'status': cl, 'store_not_checked': 'closed areas'}]}
ST.keep_old_rows(d3, {'spots': [dict(d1['spots'][0], status='pass 2')]}, '2026-11-15')
check(d1['spots'][0]['store_prev']['status'] == 'candidate' and d3['spots'][0]['status'] == 'candidate' and d3['spots'][0]['kept'] == ST.KEPT_TAG,
      'keep: passes 1-2 rewrite every row, so the row carries its good copy (store_prev) until pass 3 decides it')
lc = {'refs': ['US-1', 'US-2'], 'kind': 'area', 'status': 'not sure: water not checked (the USGS water map did not answer): run pass 5'}
for wr, want in (('ok', 'closed areas'), ('water', None), ('not checked', None)):
    s = dict(lc, closed_check='not checked: x', closed_check_water=wr); ST.closed_status({'spots': [s]})
    check(s.get('store_not_checked') == want, f"keep: the closed-area mark only when the rest of the land check said ok (water check: {wr})")

# ---------------------------------------------------------------- fixtures for the real script
st_fix = ST.Store(FIX, 100000, today='2026-11-15', kind='public')
REC = {'US-99001': 99010, 'US-99002': 99020, 'US-99003': 99030, 'US-99004': 99040}
PINS = {'US-99001': ('Test Forest', 41.63, -71.57, 'National Forest'), 'US-99002': ('Test Inner Park', 41.6275, -71.5725, 'State Park'),
        'US-99003': ('Test Lake Park', 41.67, -71.53, 'State Park'), 'US-99004': ('Test Lake Area', 41.6675, -71.5325, 'Wildlife Management Area'),
        'US-99005': ('Test Trail', 41.6352, -71.57, 'National Recreation Trail'), 'US-99006': ('Test Pin', 41.69, -71.51, 'State Park')}


def layout(t, old=None, extra_area=None):
    """The KPC-Data shape kpc_fers.py reads (pins, key, the saved key copy for the old path) + the store fixture copied in."""
    for d in ('data/parkinfo', 'data/trails', 'data/us-key', 'data/ca-key', 'data/canada-bounds', 'data/fers', 'cache/us', 'cache/ca', 'cache/fers'):
        (t / d).mkdir(parents=True, exist_ok=True)
    (t / 'data/trails/index.json').write_text('[]'); (t / 'data/trails/index-state.json').write_text('[]')
    pins, key, recs = {}, {}, []
    for ref, (nm, la, lo, kind) in PINS.items():
        pins[ref] = [nm, '', kind, '', '', la, lo]
        if ref in REC:
            key[ref] = {'g': 'official', 'm': [[REC[ref], nm, 1, 'name']]}
            g, _, w = st_fix.groups_for(ref, 'US-RI', [REC[ref]])
            recs.append({'OBJECTID': REC[ref], 'Unit_Nm': nm, 'Category': 'Fee', 'Pub_Access': 'OA', 'Own_Type': 'FED', '_r': g[0]})
        elif ref == 'US-99006': key[ref] = {'g': 'official', 'm': [[99060, nm, 1, 'name']]}
        else: key[ref] = {'g': 'pin', 'm': []}
    (t / 'data/parkinfo/US-RI.json').write_text(json.dumps({'parks': pins}))
    (t / 'data/us-key/US-RI.json').write_text(json.dumps({'parks': key}))
    with gzip.open(t / 'cache/us/US-RI.json.gz', 'wt') as fh: json.dump({'saved': '2026-11-01', 'recs': recs}, fh)
    if extra_area:   # a second area with one park and no store index
        (t / f'data/parkinfo/{extra_area}.json').write_text(json.dumps({'parks': {'US-99101': ['Test Far Park', '', 'State Park', '', '', 39.0, -75.5]}}))
        (t / f'data/us-key/{extra_area}.json').write_text(json.dumps({'parks': {'US-99101': {'g': 'official', 'm': [[99101, 'Test Far Park', 1, 'name']]}}}))
    for st, d in (old or {}).items(): (t / f'data/fers/{st}.json').write_text(json.dumps(d))
    shutil.copytree(FIX, t / 'store-copy' / 'store', ignore=shutil.ignore_patterns('README.md'))


WRAP_OFF = """import runpy, sys, urllib.request
S = sys.argv[1]; sys.path.insert(0, S)
import kpc_http_cache as HC
def _off(url, params, fetch): raise RuntimeError('offline test: no map is read (%s)' % str(url)[:60])
HC.cached = _off
def _no(*a, **k): raise RuntimeError('offline test: no network')
urllib.request.urlopen = _no
sys.argv = [S + '/kpc_fers.py']
runpy.run_path(S + '/kpc_fers.py', run_name='__main__')
"""
# switch on: nothing is patched by the test; an audit hook (C level, cannot be patched away) counts and refuses every attempt
WRAP_ON = """import json, os, runpy, sys
TRIES = []
def _audit(ev, args):
    if ev in ('socket.connect', 'socket.getaddrinfo', 'socket.gethostbyname', 'socket.gethostbyaddr', 'urllib.Request'):
        TRIES.append(ev + ' ' + str(args)[:80])
        with open(os.environ['TRIES_OUT'], 'w') as fh: fh.write(json.dumps(TRIES))
        raise OSError('test: no network (' + ev + ')')
sys.addaudithook(_audit)
open(os.environ['TRIES_OUT'], 'w').write('[]')
S = sys.argv[1]; sys.path.insert(0, S)
sys.argv = [S + '/kpc_fers.py']
runpy.run_path(S + '/kpc_fers.py', run_name='__main__')
"""


def run(t, script_dir, env, wrap, passes=(1, 2, 3)):
    (t / 'wrap.py').write_text(wrap)
    e = {k: v for k, v in os.environ.items() if not k.startswith(('KPC_', 'PASS', 'MINUTES', 'STATES', 'REGION', 'RUN_TAG', 'PARKS', 'GITHUB_', 'WATER_STORE'))}
    e.update({'MINUTES': '5', 'STATES': 'US-RI', 'REGION': 'na', 'RUN_TAG': 'testri', 'KPC_FERS_LIVE_DIR': str(t / 'cache/fers')})
    e.update(env)
    outs = []
    for p in passes:
        r = subprocess.run([sys.executable, '-B', str(t / 'wrap.py'), str(script_dir)], cwd=t, env=dict(e, PASS=str(p)), capture_output=True, text=True, timeout=600)
        outs.append((p, r.returncode, r.stdout + r.stderr))
        for f in (t / 'data/fers').glob('store-missing-*.json'):   # each pass rewrites it: keep each pass's copy outside data/fers
            (t / 'snap').mkdir(exist_ok=True); shutil.copy(f, t / 'snap' / f'p{p}-{f.name}')
        if r.returncode != 0: break
    return outs


def files_of(t):
    return {p.name: p.read_bytes() for p in sorted((t / 'data/fers').glob('*')) if p.is_file()}


def report_wo_hash(b):
    d = json.loads(b); d.pop('fers_rules', None); return json.dumps(d, sort_keys=True)


OLD_RI = {'st': 'US-RI', 'pass3': '2026-11-01', 'spots': [
    {'id': 'old-a', 'refs': ['US-99001', 'US-99002'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1], 'checked': '2026-11-01', 'center': [41.6275, -71.5725], 'wide_m': 400},
    {'id': 'old-b', 'refs': ['US-99003', 'US-99004'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1], 'checked': '2026-11-01', 'center': [41.6675, -71.5325], 'wide_m': 400}]}

if not HAVE:
    print('SKIP the real kpc_fers.py runs (numpy / cv2 not installed here)')
else:
    # ------------------------------------------------------------ 1 switch OFF: byte for byte main
    base = next((b for b in ('origin/main', 'main') if subprocess.run(['git', 'rev-parse', '-q', '--verify', b], cwd=ROOT, capture_output=True).returncode == 0), None)
    tb = TMP / 'off-branch'; tb.mkdir(); layout(tb, {'US-RI': OLD_RI})
    ob = run(tb, SCR, {}, WRAP_OFF)
    check([rc for _, rc, _ in ob] == [0, 0, 0], f'switch off: passes 1-3 run on the fixture ({[(p, rc) for p, rc, _ in ob]})')
    fb = files_of(tb)
    if base is None:
        print('SKIP-NOTE no main ref in this clone: the byte for byte comparison with main was not run')
    else:
        def tree(name, scope_from_main):
            d = TMP / name; d.mkdir()
            a = subprocess.run(['git', 'archive', base, '.github'], cwd=ROOT, capture_output=True, check=True).stdout
            subprocess.run(['tar', '-x', '-C', str(d)], input=a, check=True)
            if not scope_from_main:
                shutil.rmtree(d / '.github'); shutil.copytree(ROOT / '.github', d / '.github')
                (d / '.github/fers-rule-scope.json').write_bytes(subprocess.run(['git', 'show', f'{base}:.github/fers-rule-scope.json'], cwd=ROOT, capture_output=True, check=True).stdout)
            (d / 'data').symlink_to(ROOT / 'data', target_is_directory=True)
            return d / '.github' / 'scripts'
        main_scr, code_scr = tree('main-tree', True), tree('code-tree', False)
        tm = TMP / 'off-main'; tm.mkdir(); layout(tm, {'US-RI': OLD_RI})
        tc = TMP / 'off-code'; tc.mkdir(); layout(tc, {'US-RI': OLD_RI})
        om, oc = run(tm, main_scr, {}, WRAP_OFF), run(tc, code_scr, {}, WRAP_OFF)
        fm, fc = files_of(tm), files_of(tc)
        def differ(a, b):
            out = sorted(set(a) ^ set(b))
            for k in sorted(set(a) & set(b)):
                if a[k] == b[k]: continue
                if k.startswith('report') and report_wo_hash(a[k]) == report_wo_hash(b[k]): continue
                out.append(k)
            return out
        spots = [x for x in json.loads(fm.get('US-RI.json', b'{}')).get('spots') or []]
        check([rc for _, rc, _ in om] == [0, 0, 0] and len(spots) >= 2 and len(fm) >= 4, f'main runs the fixture too ({len(spots)} rows, {sorted(fm)})')
        check([rc for _, rc, _ in oc] == [0, 0, 0] and differ(fm, fc) == [],
              f'switch off, this code with main\'s scope file: every file byte for byte main\'s (the report\'s own fers_rules hash aside) ({differ(fm, fc)})')
        dd = differ(fm, fb)
        check(all(k.startswith('reuse-') for k in dd) and fm['US-RI.json'] == fb['US-RI.json'],
              f'switch off, as merged: the spot, looked and missing files byte for byte main\'s; only the reuse fingerprints move (the declared scope re-stamps US / CA pairs) ({dd})')

    # ------------------------------------------------------------ 2 + 3 switch ON: zero sockets, keep the old row
    tn = TMP / 'on'; tn.mkdir(); layout(tn, {'US-RI': OLD_RI})
    env_on = {'KPC_FERS_FROM_STORE': 'on', 'KPC_FERS_STORE_DIR': str(tn / 'store-copy' / 'store'), 'KPC_FERS_STORE_MAX_DAYS': '100000', 'KPC_FERS_STORE_KIND': 'public',
              'TRIES_OUT': str(TMP / 'tries-on.json')}
    on = run(tn, SCR, env_on, WRAP_ON)
    tries = json.loads((TMP / 'tries-on.json').read_text())
    fo = files_of(tn)
    ri = json.loads(fo.get('US-RI.json', b'{}'))
    rows = {tuple(sorted(x['refs'])) + (x['kind'],): x for x in ri.get('spots') or [] if not str(x.get('status', '')).startswith('merged')}
    rep = json.loads(fo.get('report-testri.json', b'{}'))
    check([rc for _, rc, _ in on] == [0, 0, 0] and tries == [], f'switch on: passes 1-3 run end to end with ZERO socket / name lookup / urllib attempts ({[(p, rc) for p, rc, _ in on]}, {tries[:2]})')
    check('KPC_FERS_FROM_STORE=on' in on[0][2] and 'outline store' in json.dumps(rep.get('outline_store') or {}) or 'outline_store' in rep,
          'switch on: the run says it reads the store, and the report carries the store counts')
    a = rows.get(('US-99001', 'US-99002', 'area')) or {}
    b = rows.get(('US-99003', 'US-99004', 'area')) or {}
    check(a.get('status') == 'candidate' and a.get('kept') == 'kept: not checked in a store run' and a.get('id') == 'old-a' and a.get('checked') == '2026-11-01',
          f"keep (end to end): the land pair the store run could not check for closed areas keeps its old candidate row, tagged ({a.get('status')}, {a.get('kept')})")
    check(b and not b.get('kept') and str(b.get('status')).startswith('not sure') and (b.get('info') or {}).get('water_pct', 0) >= 99,
          f"keep (end to end): the pair the store's water tile shows as water only is decided by this run, never kept ({b.get('status')}, {b.get('info')})")
    trail = [x for k, x in rows.items() if 'US-99005' in k]
    check(trail and all(x['kind'] == 'trail' for x in trail), f"switch on: the store's line record gives the trail its line (a trail row: {[x.get('status') for x in trail]})")
    p1m = json.loads((tn / 'snap' / 'p1-store-missing-testri.json').read_text()) if (tn / 'snap' / 'p1-store-missing-testri.json').is_file() else {}
    check(not any('US-99006' in k for k in rows) and 'pin is never a boundary' in str((p1m.get('parks') or {}).get('US-99006')),
          'switch on: the pin-only park is never a boundary (held with its reason, no row)')
    check(not any('store_prev' in json.dumps(x) for x in ri.get('spots') or []), 'switch on: the final file carries no store_prev copy')
    check('US-RI' in (json.loads(fo.get('store-missing-testri.json', b'{}')).get('areas') or {}), 'switch on: the area row is written')

    # ------------------------------------------------------------ 4 the leak guard still exits 89
    tl = TMP / 'leak'; tl.mkdir()
    layout(tl, {'US-RI': {'st': 'US-RI', 'pass3': '2026-11-01', 'spots': [{'id': 'x', 'refs': ['US-99001', 'US-99006'], 'kind': 'area', 'status': 'candidate', 'note': 'from build US-42797939226'}]}})
    ol = run(tl, SCR, dict(env_on, KPC_FERS_STORE_DIR=str(tl / 'store-copy' / 'store'), TRIES_OUT=str(TMP / 'tries-leak.json')), WRAP_ON, passes=(1,))
    check(ol[0][1] == 89 and 'write refused' in ol[0][2] and '42797939226' not in ol[0][2] and json.loads((tl / 'data/fers/US-RI.json').read_text())['spots'][0]['id'] == 'x',
          f'leak guard: a carried row naming the never-released build stops the run with exit 89, nothing written, the build not printed ({ol[0][1]})')

    # ------------------------------------------------------------ 5 an area the store does not hold; the except list; no area named
    tx = TMP / 'missing-area'; tx.mkdir(); layout(tx, {'US-ZQ': {'st': 'US-ZQ', 'spots': [], 'marker': 'previous file'}}, extra_area='US-ZQ')
    ox = run(tx, SCR, dict(env_on, KPC_FERS_STORE_DIR=str(tx / 'store-copy' / 'store'), STATES='US-RI US-ZQ', TRIES_OUT=str(TMP / 'tries-x.json')), WRAP_ON, passes=(1,))
    smx = json.loads((tx / 'data/fers/store-missing-testri.json').read_text()) if (tx / 'data/fers/store-missing-testri.json').is_file() else {}
    check(ox[0][1] == 0 and (smx.get('areas') or {}).get('US-ZQ', {}).get('verdict') == 'NOT READY' and 'index-US-ZQ.json' in smx['areas']['US-ZQ']['why']
          and json.loads((tx / 'data/fers/US-ZQ.json').read_text()).get('marker') == 'previous file' and (tx / 'data/fers/US-RI.json').is_file()
          and 'US-ZQ: NOT READY' in ox[0][2] and 'Traceback' not in ox[0][2],
          f'an area the store does not hold is left out with a plain reason (it keeps its previous file) and the run goes on for the others ({ox[0][1]})')
    # the except list, through install() in the real module (the file name is the module's own setting)
    prog = TMP / 'exc.py'
    prog.write_text('import json, os, sys\nsys.path.insert(0, %r)\nos.environ["REGION"] = "na"\nimport kpc_fers as KF, kpc_fers_store as S\nS.STORE_AREAS_FILE = sys.argv[1]\n'
                    'KF.ONLY = set(sys.argv[2].split())\ntry: r = S.install(KF, env={"KPC_FERS_FROM_STORE": "on", "KPC_FERS_STORE_DIR": sys.argv[3], "KPC_FERS_STORE_MAX_DAYS": "100000"})\n'
                    'except SystemExit as e: r = "exit %%s" %% e.code\nw = []\n'
                    'if r is True:\n    os.makedirs("data/fers", exist_ok=True)\n    for a in sorted(set(sys.argv[2].split()) | {"CA-ZQ"}):\n'
                    '        KF._save_json_raw(KF.file_of(a), {"st": a, "spots": []})\n        w.append(a + ("=written" if os.path.exists(KF.file_of(a)) else "=kept"))\n'
                    'print("RESULT", r, sorted(KF.ONLY), KF.download.__module__, json.dumps(S.AREA_ROWS, sort_keys=True), " ".join(w))\n' % str(SCR))
    def exc(areas_doc, states, store=FIX):
        d = TMP / f'exc-{len(list(TMP.glob("exc-*")))}'; d.mkdir()
        r = subprocess.run([sys.executable, str(prog), str(cfg_file(areas_doc)), states, str(store)], cwd=d, capture_output=True, text=True)
        m = re.search(r'^RESULT (.*)$', r.stdout, re.M)
        return (m.group(1) if m else r.stdout[-300:] + r.stderr[-300:]), r.stdout
    res, out = exc({'areas': 'all-us-ca', 'except': ['US-RI']}, 'US-RI')
    check(res.startswith('False') and 'kpc_fers' in res and 'except list' in out and 'runs as today' in out,
          f'except list: an area on it runs the old path (install changes nothing) ({res[:60]})')
    res, out = exc({'areas': 'all-us-ca', 'except': ['US-DE']}, 'US-RI US-DE')
    check(res.startswith("True ['US-RI']") and '"US-DE": {"verdict": "NOT USED"' in res and 'kpc_fers_store' in res,
          f'except list in a mixed run: the excepted area is left out with its reason, the others use the store ({res[:90]})')
    check('US-RI=written' in res and 'US-DE=kept' in res and 'CA-ZQ=kept' in res,
          f'a store run never rewrites the spot file of an area that does not use the store (excepted, or a border area the store does not hold) ({res[-60:]})')
    res, out = exc({'areas': 'all-us-ca'}, 'US-ZQ')
    check(res.startswith('exit 87') and 'index-US-ZQ.json' in res, f'an area the store does not hold, alone: exit 87, nothing read or saved ({res[:60]})')
    res, out = exc({'areas': 'all-us-ca'}, '')
    check(res.startswith('exit 87') and 'no area named' in out, 'a store run that names no area (a whole-region run) is refused: exit 87')
    res, out = exc('{"areas": 7}', 'US-RI')
    check(res.startswith('exit 87') and 'cannot be used' in out, 'a broken area list: exit 87, nothing read')

    # ------------------------------------------------------------ 6 Kentucky and world
    kp = TMP / 'ky.py'
    kp.write_text('import os, sys\nos.environ["REGION"] = sys.argv[1]\nsys.path.insert(0, %r)\nimport kpc_fers as KF, kpc_fers_store as S\nif len(sys.argv) > 2: S.STORE_AREAS_FILE = sys.argv[2]\n'
                  'KF.ONLY = {"US-KY"} if sys.argv[1] == "ky" else {"W-ZQ"}\ndl = KF.download\n'
                  'try: r = S.install(KF, env={"KPC_FERS_FROM_STORE": "on", "KPC_FERS_STORE_DIR": %r, "KPC_FERS_STORE_MAX_DAYS": "100000", "KPC_FERS_STORE_KIND": os.environ.get("KIND", "public"), "KPC_FERS_PRIVATE_OUT": os.environ.get("POUT", "")})\n'
                  'except SystemExit as e: r = "exit %%s" %% e.code\nprint("RESULT", r, KF.download is dl)\n' % (str(SCR), str(FIX)))
    def region(reg, areas_doc=None, **env):
        r = subprocess.run([sys.executable, str(kp), reg] + ([str(cfg_file(areas_doc))] if areas_doc else []), cwd=TMP, capture_output=True, text=True, env={**os.environ, **env})
        return (re.search(r'^RESULT (.*)$', r.stdout, re.M) or re.search('(.*)', r.stdout + r.stderr[-200:])).group(1), r.stdout
    MAIN_NOTICE = '::notice title=2-fer outline store::KPC_FERS_FROM_STORE is on, but this is the {} run: the outline store is not used and the bot runs as today'
    res, out = region('ky')
    check(res == 'False True' and out.splitlines()[0] == MAIN_NOTICE.format('ky'), 'Kentucky run, switch on: the store is not used, nothing replaced, main\'s own notice')
    res, out = region('world')
    check(res == 'False True' and out.splitlines()[0] == MAIN_NOTICE.format('world'), 'world run, world switch off: exactly as main (its notice, nothing replaced, nothing read)')
    wdoc = {'areas': 'all-us-ca', 'except': [], 'world': 'on'}
    res, out = region('world', wdoc)
    check(res == 'exit 89 True' and 'club room only' in out, 'world switch on, public store: refused (exit 89): world 2-fers are club room only, so a world store run is a private run')
    # a made-up world area W-ZQ: one ordinary record and one WDPA-derived record
    wst = TMP / 'wstore'; wst.mkdir()
    def _enc(r):
        o, px, py = [], 0, 0
        for i, (x, y) in enumerate(r):
            X, Y = int(round(x * 1e6)), int(round(y * 1e6)); o += [X, Y] if i == 0 else [X - px, Y - py]; px, py = X, Y
        return o
    def _rec(key, ring, **kw):
        e = [_enc(ring)]
        return {'key': key, 'layer': 'w-test', 'record_id': key, 'record_name': key, 'licence_class': 'OPEN', 'publishable': True, 'publish_basis': 'verified-row',
                'wdpa_derived': False, 'private_reason': '', 'source': 'live', 'use': True, 'q': 6, 'geometry_kind': 'area', 'rings': e,
                'points': sum(len(x) // 2 for x in e), 'sha256': ST.geometry_sha256(e), **kw}
    sq = lambda x0, y0, d: [[x0, y0], [x0 + d, y0], [x0 + d, y0 + d], [x0, y0 + d], [x0, y0]]
    import hashlib
    WP = [{'ref': 'ZQ-0001', 'name': 'Test World Park', 'records': [_rec('w1', sq(10.0, 50.0, 0.01))]},
          {'ref': 'ZQ-0002', 'name': 'Test Wdpa Park', 'records': [_rec('w2', sq(10.1, 50.0, 0.01), wdpa_derived=True)]}]
    fn = 'W-ZQ.kpcstore.json.gz'; raw = bytearray(gzip.compress(b'{"kpcstore": 1, "area": "W-ZQ", "parks": [', mtime=0)); idx = {}
    for i, p in enumerate(WP):
        bb = gzip.compress(((',' if i else '') + json.dumps(p)).encode(), mtime=0)
        idx[p['ref']] = {'file': fn, 'o': len(raw), 'n': len(bb), 'records': [r['key'] for r in p['records']], 'points': 5, 'date': '2026-11-15', 'geometry_kind': 'area',
                         'fp': hashlib.sha256('|'.join(r['sha256'] for r in p['records']).encode()).hexdigest()}
        raw += bb
    raw += gzip.compress(b']}', mtime=0); (wst / fn).write_bytes(bytes(raw))
    (wst / 'index-W-ZQ.json').write_text(json.dumps({'format': 1, 'store_format_version': 'kpc-outline-store-index/4', 'area': 'W-ZQ', 'made': '2026-11-15', 'parks': idx,
                                                     'files': {fn: {'bytes': len(raw), 'sha256': hashlib.sha256(bytes(raw)).hexdigest()}}}))
    wp = TMP / 'world.py'
    wp.write_text('import json, os, sys\nos.environ["REGION"] = "world"\nsys.path.insert(0, %r)\nimport kpc_fers as KF, kpc_fers_store as S\nS.STORE_AREAS_FILE = sys.argv[1]\n'
                  'KF.ONLY = set(sys.argv[3].split())\n'
                  'try: r = S.install(KF, env={"KPC_FERS_FROM_STORE": "on", "KPC_FERS_STORE_DIR": sys.argv[2], "KPC_FERS_STORE_MAX_DAYS": "100000", "KPC_FERS_STORE_KIND": "private", "KPC_FERS_PRIVATE_OUT": sys.argv[4]})\n'
                  'except SystemExit as e: r = "exit %%s" %% e.code\nS.unsilence()\nout = {"install": r}\n'
                  'if r is True:\n    parks = {"ZQ-0001": {"st": "W-ZQ", "ids": ["w1"], "names": {}, "m": [["w1", "Test World Park", "w-test"]]}, "ZQ-0002": {"st": "W-ZQ", "ids": ["w2"], "names": {}, "m": [["w2", "Test Wdpa Park", "w-test"]]}}\n'
                  '    G, bad = KF.download(parks, sorted(parks), 0, 0)\n    out.update(read=sorted(G), held=sorted(bad), ring=G["ZQ-0001"][0][0][0] if "ZQ-0001" in G else None, why=S.FLAGS.get("ZQ-0002", ""))\n'
                  'print("RESULT " + json.dumps(out))\n' % str(SCR))
    def world(states, doc=wdoc, store=wst):
        po = TMP / f'wpriv-{len(list(TMP.glob("wpriv-*")))}'
        d = TMP / f'wrun-{len(list(TMP.glob("wrun-*")))}'; d.mkdir()
        r = subprocess.run([sys.executable, str(wp), str(cfg_file(doc)), str(store), states, str(po)], cwd=d, capture_output=True, text=True)
        m = re.search(r'^RESULT (.*)$', r.stdout, re.M)
        return (json.loads(m.group(1)) if m else {'raw': r.stdout[-300:] + r.stderr[-300:]}), po
    wr, po = world('W-ZQ')
    check(wr.get('install') is True and wr.get('read') == ['ZQ-0001'] and wr.get('ring') == [10.0, 50.0], f'world switch on, private store: a made-up world area is read ({wr})')
    check(wr.get('held') == ['ZQ-0002'] and 'WDPA' in wr.get('why', ''), 'world: a WDPA-derived world record is never read as an outline (held)')
    wr2, _ = world('W-ZQ W-ZX')
    check(wr2.get('install') is True and wr2.get('read') == ['ZQ-0001'], f'world: a world area the store does not hold is left out with its reason, the run goes on ({wr2.get("install")})')
    wr3, _ = world('W-ZX')
    check(wr3.get('install') == 'exit 87', 'world: no world area the store holds: exit 87, nothing read')
    import kpc_fers_publish as PUB
    check('outside the US' in PUB.not_public_why({'id': 'w', 'refs': ['ZQ-0001', 'ZQ-0002'], 'kind': 'area', 'status': 'candidate'}),
          'world: kpc_fers_publish.py still refuses world rows for the public site')
    ST.PRIVATE_OUT = None
    try: ST.guard_write('data/fers/W-ZQ.json', {'spots': [{'refs': ['ZQ-0001', 'US-1'], 'kind': 'area', 'status': 'candidate'}]}, set()); g = False
    except ST.LeakRefused as e: g = e.code == 89
    check(g, 'world: the write guard still refuses a world row in a public file (exit 89)')

# ---------------------------------------------------------------- 7 the hook and the hashes
src = (SCR / 'kpc_fers.py').read_text(encoding='utf-8')
mn = src[src.index('def main():'):]
hook = mn.index('kpc_fers_store.install(sys.modules[__name__])')
check(mn.index('if HARD_END: _arm()') < hook < mn.index("WATER_PREFETCH"), 'the hook sits at the top of kpc_fers.main(), right after the hard-end clock (so HardStop and the crash handling still apply)')
check("in ('1', 'on', 'yes', 'true')" in mn[:hook] and mn[:hook].count('import kpc_fers_store') == 1, 'the hook imports the store module only when the switch is on')
import kpc_key_freeze as KFZ  # noqa: E402
import kpc_preflight as PF  # noqa: E402
got = {k: KFZ.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key')}
check(got == {'us-key': 'd4ebfafce438', 'ca-key': 'ba480fa34fb6', 'world-key': '158325de87ce'}, f'US, CA and world rules hashes do not move ({got})')
log = (ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
o, nw, ln = PF.changelog_hashes(log, 'fers')
check(o == 'd0064c860cba' and nw == KFZ.rules_hash('fers') and 'APPROVED, decided_by KPC owner, 2026-11-15' in ln and log.startswith(ln),
      f'the 2-fer hash moves only by the newest changelog line, on top (d0064c860cba -> {KFZ.rules_hash("fers")})')
sc = json.loads((ROOT / '.github/fers-rule-scope.json').read_text())['changes'][-1]
us = {p.stem for p in (ROOT / 'data/us-key').glob('US-*.json') if re.fullmatch(r'US-[A-Z]{2}', p.stem)}
ca = {p.stem for p in (ROOT / 'data/ca-key').glob('CA-*.json') if re.fullmatch(r'CA-[A-Z]{2}', p.stem)}
check(sc['id'] == '2026-11-15-store-switch' and sc['from'] == 'd0064c860cba' and set(sc['scope']['states']) == us | ca and 'US-KY' not in sc['scope']['states']
      and not any(s.startswith('W-') for s in sc['scope']['states']) and sc.get('approved') == 'APPROVED, decided_by KPC owner, 2026-11-15',
      f"scope entry 2026-11-15-store-switch: every US and Canadian area of the keys, Kentucky's own run and the world (switched off) not in it ({len(sc['scope']['states'])} areas)")
print('ALL PASS' if not FAILS else 'SOME FAILED')
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAILS else 0)
