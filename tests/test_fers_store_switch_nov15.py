#!/usr/bin/env python3
"""KPC owner, 2026-11-15: the 2-fer switch-over to the outline store (kpc_fers.main() hook, kpc_fers_store.py in the 2-fer rules).
Offline: proxy variables dropped; the real kpc_fers.py runs in subprocesses on made-up fixtures (tests/fixtures/fers-store-v4: an
area, a line, a pin and one water tile; made-up squares and made-up park refs US-99001..US-99006 filed under US-RI).
1 switch OFF: kpc_fers.py's files are byte for byte main's on the fixture (passes 1-3; the report's own fers_rules hash aside), pair
  fingerprints included (the declared scope is none); the next ordinary run reuses every pair main tested; the first STORE run of an
  area tests its pairs again (its parks carry the 2026-11-15-store-switch stamp)
2 switch ON (passes 1-3): zero sockets (a Python audit hook sees every connect / name lookup / urllib request at C level, whatever
  is patched), the store's area, line and water tile are used, the pin is never a boundary
3 keep the old row: a live candidate that the store run leaves NOT SURE only because closed areas were not checked keeps its old
  row, tagged 'kept: not checked in a store run', only when it is the same spot (place, size within 25 %); a moved or resized spot is
  never kept, nor re-kept by a later run; a pair the store run decides (water only from the store's water tile) is never kept; the
  good copies wait between passes in a side file outside data/ (no store_prev in any data file, also when a run stops after pass 1);
  the write guard refuses a withheld park's NAME in any text and any store_prev in a row
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

# ---------------------------------------------------------------- unit: keep the old row (same spot only: grade of #201, defect 1)
def sp(i, refs, status, kind='area', c=(41.6, -71.6), acres=50.0, d=0.004, **kw):
    r = {'id': i, 'refs': refs, 'kind': kind, 'status': status, 'center': [c[0], c[1]], 'box': [c[1] - d, c[0] - d, c[1] + d, c[0] + d], **kw}
    if kind == 'area': r['acres'] = acres
    else: r['len_m'] = acres
    return r
old = {'spots': [sp('A@1', ['US-1', 'US-2'], 'candidate', passes=[1, 1, 1], checked='2026-11-01'),
                 sp('B@1', ['US-3', 'US-4'], 'candidate'), sp('C@1', ['US-5', 'US-6'], 'not sure: low-confidence outline'),
                 sp('D@1', ['US-7', 'US-8'], 'candidate'), sp('D@2', ['US-7', 'US-8'], 'candidate'),
                 sp('E@1', ['US-9', 'US-10'], 'very tight: could be map error: check both official maps on the ground', kind='trail', acres=300),
                 sp('F@1', ['US-11', 'US-12'], 'candidate'),
                 sp('M@1', ['US-13', 'US-14'], 'candidate', c=(41.9, -71.1), acres=900),          # the grader's case: 20 km away, 900 acres
                 sp('R@1', ['US-15', 'US-16'], 'candidate', acres=200),                            # same place, four times the size
                 sp('N@1', ['US-17', 'US-18'], 'candidate', acres=40),                            # same place, size within 25 %
                 sp('H@1', ['US-19', 'US-20'], 'candidate', acres=50, d=0.25),                    # same acres, but a box 60 times wider
                 sp('S@1', ['US-21', 'US-22'], 'candidate', acres=100), sp('T@1', ['US-23', 'US-24'], 'candidate', acres=100)]}
cl = 'not sure: closed areas not checked (x): the store must carry them first'
mk = lambda i, refs, st=cl, **kw: sp(i, refs, st, store_not_checked='closed areas', **kw)
new = {'spots': [mk('A@2', ['US-2', 'US-1'], c=(41.601, -71.601), acres=52),      # pair match, same spot
                 sp('B@1', ['US-3', 'US-4'], 'water only: boat or kayak'),        # decided: not kept
                 mk('C@1', ['US-5', 'US-6']),                                     # old not a candidate
                 mk('D@9', ['US-7', 'US-8']),                                     # two old rows: no guess
                 sp('E@1', ['US-9', 'US-10'], 'not sure: the agency ownership map did not answer', kind='trail', acres=290),
                 sp('F@1', ['US-11', 'US-12'], 'not sure: closed areas not checked (x; the water was not checked either)'),
                 mk('M@2', ['US-13', 'US-14'], c=(41.628, -71.572), acres=58),
                 mk('R@1', ['US-15', 'US-16'], acres=50), mk('N@1', ['US-17', 'US-18'], acres=48), mk('H@1', ['US-19', 'US-20'], acres=50),
                 mk('S@1', ['US-21', 'US-22'], acres=126), mk('T@1', ['US-23', 'US-24'], acres=80)]}
ST.owner_status(new)
n = ST.keep_old_rows(new, old, '2026-11-15')
by = {x['id']: x for x in new['spots']}
check(n == 4 and by['A@1']['status'] == 'candidate' and by['A@1']['kept'] == 'kept: not checked in a store run' and 'closed areas' in by['A@1']['kept_why']
      and by['A@1']['checked'] == '2026-11-01' and by['A@1']['passes'] == [1, 1, 1],
      f'keep: the SAME spot (place inside, size within 25 %) left NOT SURE only because closed areas were not checked keeps its old row, tagged ({n})')
check(by['N@1']['status'] == 'candidate' and by['N@1'].get('kept'), 'keep: same spot, 48 vs 40 acres (within 25 %): kept')
check(by['E@1']['status'].startswith('very tight') and by['E@1']['kept'] == ST.KEPT_TAG and 'ownership' in by['E@1']['kept_why'],
      'keep: the same when only the ownership map could not be read (a line row: compared by its length)')
check(by['M@2']['status'] == cl and 'moved' in by['M@2'].get('not_kept', '') and 'M@1' not in by,
      "keep: a MOVED spot (the old row 20 km away, 900 acres; this run's spot 58 acres) is NOT kept: this run's NOT SURE row stands")
check(by['R@1']['status'] == cl and 'size' in by['R@1'].get('not_kept', ''), 'keep: a RESIZED spot (200 -> 50 acres, same place) is NOT kept')
check(by['H@1']['status'] == cl and 'shape' in by['H@1'].get('not_kept', ''), 'keep: an old row whose box is far larger than the new spot\'s is NOT kept, even with the same acres')
check(by['S@1']['status'] == cl and 'size' in by['S@1'].get('not_kept', '') and by['T@1']['status'] == 'candidate' and by['T@1'].get('kept'),
      'keep: the size test is symmetric: 100 -> 126 acres (26 % up) not kept; 100 -> 80 (the larger 1.25 times the smaller) kept')
check(by['B@1']['status'] == 'water only: boat or kayak' and by['C@1']['status'] == cl and by['D@9']['status'] == cl and by['F@1']['status'].startswith('not sure: closed')
      and not any('kept' in by[k] for k in ('B@1', 'C@1', 'D@9', 'F@1', 'M@2', 'R@1')),
      'keep: never a row the run decided (water only), never an old row that was not a candidate, never a guess between two old rows, never when the water was not checked either')
again = json.loads(json.dumps(new)); again['spots'] = [dict(x, store_not_checked=x.get('store_not_checked') or 'closed areas') if x['id'] in ('M@2', 'R@1') else x for x in again['spots']]
n2 = ST.keep_old_rows(again, new, '2026-11-16')
check(n2 >= 0 and {x['id']: x for x in again['spots']}['M@2']['status'] == cl and {x['id']: x for x in again['spots']}['R@1']['status'] == cl,
      'keep: a second store run does not re-keep a row that was not kept (its last row is NOT SURE, not a candidate)')
check(not any('store_prev' in x for x in new['spots']), 'keep: no carried copy is ever put in a row')
carry = {}
d1 = {'spots': [sp('A@2', ['US-1', 'US-2'], 'pass 1', passes=[1, 0, 0])]}
ST.keep_old_rows(d1, old, '2026-11-15', final=False, carry=carry)
d3 = {'spots': [mk('A@2', ['US-1', 'US-2'])]}
c3 = dict(carry)
ST.keep_old_rows(d3, {'spots': [dict(d1['spots'][0], status='pass 2')]}, '2026-11-15', final=True, carry=c3)
check(carry.get('A@2', {}).get('status') == 'candidate' and 'store_prev' not in d1['spots'][0] and d3['spots'][0]['status'] == 'candidate' and d3['spots'][0]['kept'] == ST.KEPT_TAG and c3 == {},
      'keep: passes 1-2 rewrite every row, so the good copy waits in the side file (never in the row) until pass 3 decides it; the final pass empties it')
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
        elif ref == 'US-99006':   # the saved key copy has a record for it (the old path reads it; no slow second try); the store has only a pin
            key[ref] = {'g': 'official', 'm': [[99060, nm, 1, 'name']]}
            recs.append({'OBJECTID': 99060, 'Unit_Nm': nm, 'Category': 'Fee', 'Pub_Access': 'OA', 'Own_Type': 'STAT', '_r': [[[lo - .001, la - .001], [lo + .001, la - .001], [lo + .001, la + .001], [lo - .001, la + .001], [lo - .001, la - .001]]]})
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
    {'id': 'old-a', 'refs': ['US-99001', 'US-99002'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1], 'checked': '2026-11-01', 'center': [41.6275, -71.5725],
     'box': [-71.575, 41.625, -71.57, 41.63], 'acres': 57.0, 'wide_m': 400},
    {'id': 'old-b', 'refs': ['US-99003', 'US-99004'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1], 'checked': '2026-11-01', 'center': [41.6675, -71.5325],
     'box': [-71.535, 41.665, -71.53, 41.67], 'acres': 57.0, 'wide_m': 400}]}

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
            # KPC owner, 2026-11-16 (item 1): this code also writes its run receipt (receipt-<tag>.json, new); main has none
            a = {k: v for k, v in a.items() if not k.startswith('receipt-')}; b = {k: v for k, v in b.items() if not k.startswith('receipt-')}
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
        check(dd == [] and fm['US-RI.json'] == fb['US-RI.json'],
              f'switch off, as merged: every file byte for byte main\'s, reuse fingerprints included (the declared scope is none: no pair is re-stamped) ({dd})')
        # the next ordinary run after this change: main's saved pair answers are reused, none is tested again
        ro = run(tm, SCR, {}, WRAP_OFF, passes=(1,))
        rp = json.loads((tm / 'data/fers/report-testri.json').read_text()).get('pass1') or {}
        check(ro[0][1] == 0 and rp.get('pairs tested', 0) > 0 and rp.get('pairs reused (nothing changed)') == rp.get('pairs tested'),
              f"switch off after main: every pair main tested is reused, none tested again ({rp.get('pairs reused (nothing changed)')} of {rp.get('pairs tested')})")
        ra = run(tm, SCR, {'KPC_FERS_FROM_STORE': 'on', 'KPC_FERS_STORE_DIR': str(tm / 'store-copy' / 'store'), 'KPC_FERS_STORE_MAX_DAYS': '100000',
                           'TRIES_OUT': str(TMP / 'tries-stamp.json')}, WRAP_ON, passes=(1,))
        rs = json.loads((tm / 'data/fers/report-testri.json').read_text()).get('pass1') or {}
        check(ra[0][1] == 0 and rs.get('pairs tested', 0) > 0 and not rs.get('pairs reused (nothing changed)'),
              f"the first STORE run of the area tests its pairs again (its parks carry the 2026-11-15-store-switch stamp) ({rs.get('pairs reused (nothing changed)')} of {rs.get('pairs tested')})")

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

    # ------------------------------------------------------------ keep: a moved spot is not kept; store_prev never in a data file
    tv = TMP / 'moved'; tv.mkdir()
    moved = json.loads(json.dumps(OLD_RI)); moved['spots'][0].update(center=[41.9, -71.1], box=[-71.15, 41.85, -71.05, 41.95], acres=900.0)
    layout(tv, {'US-RI': moved})
    ov = run(tv, SCR, dict(env_on, KPC_FERS_STORE_DIR=str(tv / 'store-copy' / 'store'), TRIES_OUT=str(TMP / 'tries-mv.json')), WRAP_ON, passes=(1,))
    r1 = json.loads((tv / 'data/fers/US-RI.json').read_text())
    side = tv / 'cache/fers/store-prev/US-RI.json'
    check(ov[0][1] == 0 and 'store_prev' not in json.dumps(r1) and side.is_file() and not list((tv / 'data').rglob('*store-prev*')),
          'a run that stops after pass 1: no store_prev in any data file; the good copies wait in cache/fers/store-prev (outside data/)')
    ov = run(tv, SCR, dict(env_on, KPC_FERS_STORE_DIR=str(tv / 'store-copy' / 'store'), TRIES_OUT=str(TMP / 'tries-mv.json')), WRAP_ON, passes=(2, 3))
    rv = {tuple(sorted(x['refs'])) + (x['kind'],): x for x in json.loads((tv / 'data/fers/US-RI.json').read_text()).get('spots') or []}
    av = rv.get(('US-99001', 'US-99002', 'area')) or {}
    check([rc for _, rc, _ in ov] == [0, 0] and str(av.get('status')).startswith('not sure: closed areas') and not av.get('kept') and 'moved' in str(av.get('not_kept'))
          and av.get('center') != [41.9, -71.1] and not side.exists(),
          f"keep (end to end): an old candidate 20 km away at 900 acres is NOT kept; this run's own spot stands as NOT SURE; the side file is gone after pass 3 ({av.get('status', '')[:40]}, {av.get('not_kept', '')[:50]})")

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
    # a made-up world area W-ZQ: one ordinary record and one WDPA-derived record. Record keys as the world store files them
    # ('<area>:<layer>:<id>', KPC owner 2026-11-16: a world park is looked up that way)
    wst = TMP / 'wstore'; wst.mkdir()
    def _enc(r):
        o, px, py = [], 0, 0
        for i, (x, y) in enumerate(r):
            X, Y = int(round(x * 1e6)), int(round(y * 1e6)); o += [X, Y] if i == 0 else [X - px, Y - py]; px, py = X, Y
        return o
    def _rec(key, ring, **kw):
        e = [_enc(ring)]
        return {'key': key, 'layer': key.rsplit(':', 1)[0], 'record_id': key.rsplit(':', 1)[-1], 'record_name': key, 'licence_class': 'OPEN', 'publishable': True, 'publish_basis': 'verified-row',
                'wdpa_derived': False, 'private_reason': '', 'source': 'live', 'use': True, 'q': 6, 'geometry_kind': 'area', 'rings': e,
                'points': sum(len(x) // 2 for x in e), 'sha256': ST.geometry_sha256(e), **kw}
    sq = lambda x0, y0, d: [[x0, y0], [x0 + d, y0], [x0 + d, y0 + d], [x0, y0 + d], [x0, y0]]
    import hashlib
    WP = [{'ref': 'ZQ-0001', 'name': 'Test World Park', 'records': [_rec('W-ZQ:w-test:w1', sq(10.0, 50.0, 0.01))]},
          {'ref': 'ZQ-0002', 'name': 'Test Wdpa Park', 'records': [_rec('W-ZQ:w-test:w2', sq(10.1, 50.0, 0.01), wdpa_derived=True)]}]
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

# ---------------------------------------------------------------- the write guard: a withheld park's NAME, and store_prev
import types  # noqa: E402
_po, _kf = ST.PRIVATE_OUT, ST.KF_REF['kf']; ST.PRIVATE_OUT = None
ST.KF_REF['kf'] = types.SimpleNamespace(PINS={'US-77001': ('Hidden Test Marsh', 0, 0), 'US-77002': ('Pine Ridge', 0, 0), 'US-77003': ('Pine Ridge', 0, 0),
                                              'US-77004': ('Hidden Test Marsh Forest', 0, 0), 'US-77005': ('Lake Park', 0, 0), 'US-77006': ('Test Lake Park', 0, 0),
                                              'US-1': ('Open Park', 0, 0), 'US-2': ('Other Park', 0, 0)})
ST.HELD_PRIVATE.update({'US-77001', 'US-77002', 'US-77005'})
def refused(doc):
    try: ST.guard_write('data/fers/US-RI.json', doc); return None
    except ST.LeakRefused as e: return e.code
row = {'refs': ['US-1', 'US-2'], 'kind': 'area', 'status': 'candidate', 'names': {'US-1': 'Open Park', 'US-2': 'Other Park'}}
check(refused({'spots': [row]}) is None, 'write guard: a clean public row is written')
check(refused({'spots': [dict(row, note='shares a fence with hidden test marsh')]}) == 89 and refused({'spots': [dict(row, info={'names': ['Hidden Test Marsh']})]}) == 89,
      "write guard: a withheld park's NAME in any text of a row (a carried note, a list of names), any case, stops the run (exit 89)")
check(all(refused({'spots': [dict(row, note=v)]}) == 89 for v in ('near Hidden-Test-Marsh.', 'HIDDEN  TEST   MARSH', 'Hídden Tést Marsh', 'hidden_test_marsh')),
      'write guard: spacing, hyphen, case and accent variants of the name are caught')
check(refused({'spots': [dict(row, refs=['US-1', 'US-77002'])]}) == 89 and refused({'spots': [dict(row, note='see US-77005')]}) == 89,
      "write guard: the withheld park's REF still stops the run (the main protection), also when its name is not looked for")
check(refused({'spots': [dict(row, refs=['US-1', 'US-77003'], status='not sure: the official outline of Pine Ridge, Open Park could not be read in pass 2', note='approximate line: Pine Ridge')]}) is None,
      'write guard: a PUBLIC namesake (US-77003 "Pine Ridge", the same name as a withheld park) in a status line and a note does not stop the run')
check(refused({'spots': [dict(row, status='not sure: the official outline of Hidden Test Marsh Forest could not be read')]}) is None,
      'write guard: a public park whose name contains the withheld name ("Hidden Test Marsh Forest") does not stop the run')
check(refused({'spots': [dict(row, status='not sure: the official outline of Test Lake Park, State Park and Lake Park could not be read')]}) is None,
      'write guard: a withheld name made only of common words ("Lake Park") is not looked for (it would block every run)')
check(refused({'spots': [dict(row, note='Hidden Test Marshland trail')]}) is None and refused({'spots': [dict(row, names={'US-1': 'Hidden Test Marsh', 'US-2': 'x'})]}) is None,
      "write guard: a longer word is not the name, and a public park's own ref-keyed name map is checked by ref")
check(refused({'spots': [dict(row, store_prev={'status': 'candidate'})]}) == 89, 'write guard: a row carrying a store_prev copy is refused (exit 89)')
ST.HELD_PRIVATE.difference_update({'US-77001', 'US-77002', 'US-77005'}); ST.PRIVATE_OUT, ST.KF_REF['kf'] = _po, _kf; ST._NAME_CACHE.clear()

# ---------------------------------------------------------------- 7 the hook and the hashes
src = (SCR / 'kpc_fers.py').read_text(encoding='utf-8')
mn = src[src.index('def main():'):]
hook = mn.index('kpc_fers_store.install(sys.modules[__name__])')
check(mn.index('if HARD_END: _arm()') < hook < mn.index("WATER_PREFETCH"), 'the hook sits at the top of kpc_fers.main(), right after the hard-end clock (so HardStop and the crash handling still apply)')
check("in ('1', 'on', 'yes', 'true')" in mn[:hook] and mn[:hook].count('import kpc_fers_store') == 1, 'the hook imports the store module only when the switch is on')
import kpc_key_freeze as KFZ  # noqa: E402
import kpc_preflight as PF  # noqa: E402
got = {k: KFZ.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key')}
check(got == {'us-key': 'd4ebfafce438', 'ca-key': 'ba480fa34fb6', 'world-key': '24cd942eca01'}, f'US, CA and world rules hashes do not move ({got})')
log = (ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
# KPC owner, 2026-11-15 (store run fixes, the next declared move 2fe19a32e5eb -> ...): this change's own line, wherever it now sits;
# the newest line on top is checked by test_fers_store_fixes_nov15.py
ln = next((x for x in log.splitlines() if 'fers rules d0064c860cba -> 2fe19a32e5eb' in x), '')
o, nw, _ = PF.changelog_hashes(ln, 'fers')
check(o == 'd0064c860cba' and nw == '2fe19a32e5eb' and 'APPROVED, decided_by KPC owner, 2026-11-15' in ln and (nw == KFZ.rules_hash('fers') or f'fers rules {nw} -> ' in log),
      f'the switch-over moved the 2-fer hash by its own declared line (d0064c860cba -> 2fe19a32e5eb); any later move starts from it ({KFZ.rules_hash("fers")})')
sc = next(c for c in json.loads((ROOT / '.github/fers-rule-scope.json').read_text())['changes'] if c.get('id') == '2026-11-15-store-switch')
check(sc['id'] == '2026-11-15-store-switch' == ST.STORE_STAMP and sc['from'] == 'd0064c860cba' and sc['scope'] == 'none' and sc.get('approved') == 'APPROVED, decided_by KPC owner, 2026-11-15',
      "scope entry 2026-11-15-store-switch: scope none (an ordinary run re-tests nothing); a store run stamps its own areas' parks with the same id")
print('ALL PASS' if not FAILS else 'SOME FAILED')
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAILS else 0)
