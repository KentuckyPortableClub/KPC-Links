#!/usr/bin/env python3
"""KPC owner, 2026-11-11: the Pacific 2-fer run (KPC-Data run 43109640166) printed nothing for 4.5 hours after 'pass 1 downloads'
and saved nothing. Offline: no network (the real kpc_fers.py runs in a subprocess whose map reads all fail at once).
1 the area filter: a longitude east of 180 is past it (Alaska Maritime NWR's pin is at 177.5 E); Alaska, Hawaii and the West Coast
  get one box each; an area of touching states keeps exactly its old single box; far parks are not loaded, border parks are
2 a park whose outline crosses 180 and is in many pairs: pass 1 stops on its own time, prints progress, saves the finished pair
  answers, keeps the unfinished state's previous file and exits 0 (the workflow's 'ran out of time, saved, next run carries on');
  the next run carries on from the saved answers and finishes
3 the per-park limit holds (pair test and pair fingerprint); a pair cut by the pass's own time is left for the next run, never
  listed as too slow
4 the near-pairs list stops 4 minutes before the step's hard end (the pass still saves instead of exit 3)
5 a normal area's files are byte for byte what the code before this change wrote (golden made with main 11f908d9)
6 the memory collect runs at most once a minute (it ran after every pair once the outlines alone were over the cap)"""
import contextlib, gzip, hashlib, io, json, math, os, pathlib, re, subprocess, sys, tempfile, time, types
HERE = pathlib.Path(__file__).resolve().parent.parent
S = HERE / '.github/scripts'
sys.path.insert(0, str(S))
os.environ.setdefault('PASS', '1')
try: import cv2  # noqa: F401
except Exception: sys.modules['cv2'] = types.ModuleType('cv2')  # noqa: BLE001
import kpc_fers as K
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg, flush=True); ok = ok and bool(c)


src = open(S / 'kpc_fers.py', encoding='utf-8').read()

# ---------------------------------------------------------------- 1 the area filter
K.REGION = 'na'
pins = {'US-AK': [('Alaska Maritime NWR', 51.9674, 177.533), ('Unalaska park', 53.5, -167.5), ('Wrangell park', 60.0, -139.0)],
        'US-HI': [('Big Island park', 19.1, -155.6), ('Kauai park', 22.2, -159.6)],
        'US-WA': [('Coast park', 46.0, -124.0), ('Border park', 48.9, -117.0)]}
P = {st: [(n, la, lo) for n, la, lo in v] for st, v in pins.items()}
bx = K.area_boxes(P)
check(len(bx) == 3, f'Alaska, Hawaii and Washington are three boxes, not one ({len(bx)})')
check(K.in_area(177.6, 52.0, bx) and K.in_area(-176.6, 51.9, bx) and K.in_area(-167.5, 53.5, bx),
      'the western Aleutians (177.6 E), Adak (176.6 W) and Unalaska are inside the Alaska box')
check(not K.in_area(-75.0, 43.0, bx) and not K.in_area(-127.0, 52.5, bx), 'New York and central British Columbia are not in the area')
check(K.in_area(-121.0, 49.05, bx) and K.in_area(-139.3, 60.1, bx), "a park just across Washington's border and one beside Alaska's are border neighbours")
_all = [v for vs in P.values() for v in vs]
old = [min(v[2] for v in _all) - .2, min(v[1] for v in _all) - .2, max(v[2] for v in _all) + .2, max(v[1] for v in _all) + .2]
check(old[0] <= -75.0 <= old[2] and not (old[0] <= -176.6 <= old[2]),
      'the old single box held New York but not Adak (the bug this fixes: it ran from 167.7 W to 177.7 E)')
sw = {'US-NV': [('a', 36.0, -119.97), ('b', 41.95, -114.0)], 'US-AZ': [('c', 31.34, -114.6), ('d', 36.9, -109.24)],
      'US-NM': [('e', 31.83, -108.75), ('f', 36.95, -103.04)]}   # the Southwest: NM's box is 0.49 degrees from AZ's
_sw = [v for vs in sw.values() for v in vs]
old_sw = [min(v[2] for v in _sw) - .2, min(v[1] for v in _sw) - .2, max(v[2] for v in _sw) + .2, max(v[1] for v in _sw) + .2]
check(K.area_boxes(sw) == [old_sw], 'an area of states closer than 5 degrees keeps exactly its old single box (bit for bit)')
check(K.box_in_area([-160.0, 58.0, -159.0, 59.0], bx) and not K.box_in_area([172.5, 52.0, 173.5, 53.0], bx),
      'a part box is tested in the same longitudes (Attu, 4.6 degrees west of the westmost Alaska pin, stays outside like any edge)')
check(K.box_in_area([-179.2, 51.2, 179.8, 70.0], bx), 'a box that runs across 0 (an outline crossing 180) touches the area, as before')
K.REGION = 'world'
check(K.wrap_lon(10.0) == 10.0 and K.wrap_box([5, 45, 6, 46]) == [5, 45, 6, 46], 'outside US + Canada nothing is wrapped (Europe stays east)')
K.REGION = 'na'

# ---------------------------------------------------------------- 3 the per-park limit
with K.park_clock('US-1+US-2', 'test', budget_end=time.time() - 58.5) as c:
    try: time.sleep(4)
    except Exception: pass  # noqa: BLE001
check(c.hit and c.out_of_time and 'US-1+US-2' not in K.TIMED_OUT, "a pair cut by the pass's own time is out of time, not listed as too slow")
with K.park_clock('US-3+US-4', 'test', seconds=1) as c:
    time.sleep(3)
check(c.hit and not c.out_of_time and 'US-3+US-4' in K.TIMED_OUT, 'a pair over its own limit is still cut, skipped and listed')
sq = lambda x0, y0, d: [[[[x0, y0], [x0 + d, y0], [x0 + d, y0 + d], [x0, y0 + d], [x0, y0]]]]
G = {'US-1': sq(-121.0, 47.0, .1), 'US-2': sq(-120.95, 47.05, .1)}
K.PINS.update({'US-1': ('one', 47.05, -120.95, '', '', 'WA'), 'US-2': ('two', 47.1, -120.9, '', '', 'WA')})
fp0, ps0, ar0, be0 = K.pair_fp, K.PARK_S, K.area_spots, K.budget_end
cwd = os.getcwd()
with tempfile.TemporaryDirectory() as t:
    os.chdir(t); pathlib.Path('data/fers').mkdir(parents=True, exist_ok=True)
    try:
        K.OUT = pathlib.Path('data/fers'); K.TIMED_OUT.clear(); K.TIMED_PAIRS.clear(); K.TESTED.clear()
        K.pair_fp = lambda *a: time.sleep(4); K.PARK_S = 1
        cnt = {'pairs tested': 0}
        with contextlib.redirect_stdout(io.StringIO()): K.find_spots(G, {}, {('US-1', 'US-2')}, cnt)
        check(('US-1', 'US-2') in K.TIMED_PAIRS and 'pair fingerprint' in K.TIMED_OUT.get('US-1+US-2', ''), 'the pair fingerprint is inside the per-park limit')
        K.pair_fp, K.PARK_S = fp0, ps0; K.TIMED_OUT.clear(); K.TIMED_PAIRS.clear(); K.TESTED.clear()
        K.area_spots = lambda *a: time.sleep(5) or []; K.budget_end = lambda screen=False, frac=None: time.time() - 58.5
        cnt = {'pairs tested': 0}
        with contextlib.redirect_stdout(io.StringIO()): K.find_spots(G, {}, {('US-1', 'US-2')}, cnt)
        check(cnt.get('stopped for time') and cnt['pairs tested'] == 0 and ('US-1', 'US-2') not in K.TESTED and not K.TIMED_OUT,
              "a pair cut by the pass's own time is not tested: the pass stops for time and the next run carries on")
    finally:
        K.pair_fp, K.PARK_S, K.area_spots, K.budget_end = fp0, ps0, ar0, be0
        import kpc_save; kpc_save.flush_status()   # its change-date file goes to the temp folder, never the repo
        os.chdir(cwd)

# ---------------------------------------------------------------- 4 near pairs before the hard end, progress lines, 6 the memory collect
K.LOG.clear(); h0 = K.HARD_END; K.HARD_END = time.time() + 100
try: out = K.near_pairs(G, {('US-1', 'US-2')}, [])
finally: K.HARD_END = h0
check(out == [] and 'near-pairs list cut short for time' in K.LOG, "the near-pairs list stops 4 minutes before the step's hard end")
K.LOG.clear(); dt0, t00, l0 = K.dt, K.T0, K.LIMIT
K.dt = lambda *a, **k: time.sleep(20)   # one near pair that would run 20 s (two many-island parks)
K.T0, K.LIMIT = time.time(), 2 / 1.1    # the list's own end: 2 s from now
t1 = time.time()
try: out = K.near_pairs(G, {('US-1', 'US-2')}, [])
finally: K.dt, K.T0, K.LIMIT = dt0, t00, l0
check(time.time() - t1 < 6 and out == [] and 'near-pairs list cut short for time' in K.LOG, f'one slow near pair is cut when the list\'s time ends ({time.time() - t1:.1f} s, not 20)')
check("'n-fer test', seconds=1e9, budget_end=_be" in src, "each n-fer test is inside the pass's own time (no limit of its own: no result changes)")
n0, s0 = K.PROGRESS_N, K.PROGRESS_S
K.PROGRESS_N, K.PROGRESS_S = 2, 3600
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    pg = K.Progress('pass 1 pair tests', 5)
    for i in range(5): pg.step(f'US-{i}+US-9', reused=i)
K.PROGRESS_N, K.PROGRESS_S = n0, s0
lines = [ln for ln in buf.getvalue().splitlines() if ln.startswith('progress: pass 1 pair tests')]
check(len(lines) == 2 and '2 of 5' in lines[0] and 'peak' in lines[0] and 'now US-1+US-9' in lines[0], f'a progress line every N pairs with counts, minutes, peak MB and the pair in hand ({lines[:1]})')
check(src.count('flush=True); _BEAT') >= 1 and "stage_start(f'pass {PASS} pair tests" in src and "stage_start(f'pass 1 downloads" in src,
      'progress lines are flushed; a stage line at the start of the pair tests and the downloads')
import gc as _gc
rss0, col0, mem0 = K.rss_mb, _gc.collect, K.MEM_MB
calls = []
K.rss_mb = lambda: 99999.0; _gc.collect = lambda *a: calls.append(1) or 0; K._GC_T[0] = 0.0; e0 = K.EVICT_N['memory']
try:
    for _ in range(5): K.evict([-121, 47, -120, 48])
finally: K.rss_mb, _gc.collect = rss0, col0
check(len(calls) == 1 and K.EVICT_N['memory'] - e0 == 5, f'over the memory cap the caches are dropped every time, the collect runs once a minute ({len(calls)} of 5)')


# ---------------------------------------------------------------- fixtures for the real script
def ring(cx, cy, rx, ry, n):
    r = [[round(cx + rx * math.cos(2 * math.pi * i / n), 6), round(cy + ry * math.sin(2 * math.pi * i / n), 6)] for i in range(n)]
    return r + [r[0]]


def write_area(t, parks, ca=(), old=None):
    """parks: [(ref, state, name, lat, lon, rings)]; writes POTA pins, the key and the saved PAD-US / Canadian outlines."""
    for d in ('data/parkinfo', 'data/trails', 'data/us-key', 'data/ca-key', 'data/canada-bounds', 'data/fers', 'cache/us', 'cache/ca', 'cache/fers'):
        (t / d).mkdir(parents=True, exist_ok=True)
    (t / 'data/trails/index.json').write_text('[]')
    pin, key, recs = {}, {}, {}
    for oid, (ref, st, name, la, lo, rings) in enumerate(parks, start=1000):
        pin.setdefault(st, {})[ref] = [name, '', 'National Wildlife Refuge', '', '', la, lo]
        key.setdefault(st, {})[ref] = {'g': 'official', 'm': [[oid, name, 1, 'name']]}
        recs.setdefault(st, []).append({'OBJECTID': oid, 'Unit_Nm': name, 'Category': 'Fee', 'Pub_Access': 'OA', 'Own_Type': 'FED', '_r': rings})
    for st in pin:
        (t / f'data/parkinfo/{st}.json').write_text(json.dumps({'parks': pin[st]}))
        (t / f'data/us-key/{st}.json').write_text(json.dumps({'parks': key[st]}))
        with gzip.open(t / f'cache/us/{st}.json.gz', 'wt') as fh: json.dump({'saved': '2026-11-01', 'recs': recs[st]}, fh)
    cpin, ckey = {}, {}
    for oid, (ref, prov, name, la, lo, rings) in enumerate(ca, start=5000):
        cpin[ref] = [name, '', 'Provincial Park', '', '', la, lo, 0, 0, 0, prov]
        ckey.setdefault(prov, {})[ref] = {'g': 'official', 'm': [[oid, name, 1, 'name']]}
        (t / f'data/canada-bounds/{ref}.json').write_text(json.dumps({'geometry': {'type': 'MultiPolygon', 'coordinates': [[r] for r in rings]}}))
    if cpin:
        (t / 'data/parkinfo/CA.json').write_text(json.dumps({'parks': cpin}))
        for prov, v in ckey.items(): (t / f'data/ca-key/CA-{prov}.json').write_text(json.dumps({'parks': v}))
    for st, d in (old or {}).items(): (t / f'data/fers/{st}.json').write_text(json.dumps(d))


WRAP = """import runpy, sys, urllib.request
S = sys.argv[1]; sys.path.insert(0, S)
import kpc_http_cache as HC
def _off(url, params, fetch): raise RuntimeError('offline test: no map is read (%s)' % str(url)[:60])
HC.cached = _off
def _no(*a, **k): raise RuntimeError('offline test: no network')
urllib.request.urlopen = _no
sys.argv = [S + '/kpc_fers.py']
runpy.run_path(S + '/kpc_fers.py', run_name='__main__')
"""


def run(t, script_dir, env, timeout=150):
    (t / 'wrap_offline.py').write_text(WRAP)
    e = {k: v for k, v in os.environ.items() if not k.startswith(('KPC_', 'PASS', 'MINUTES', 'STATES', 'REGION', 'RUN_TAG', 'PARKS'))}
    e.update(env)
    r = subprocess.run([sys.executable, '-B', str(t / 'wrap_offline.py'), str(script_dir)], cwd=t, env=e, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


# ---------------------------------------------------------------- 2 a park crossing 180 in many pairs: stops on time, saves, carries on
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    giant = [ring(-158.0, 58.3, 3.0, 1.2, 250000)] + [ring(172.8 + .2 * k, 52.6, .05, .03, 400) for k in range(30)] + \
            [ring(-179.5 + .4 * k, 51.8, .05, .03, 400) for k in range(30)] + [ring(-167.5, 53.5, .3, .2, 400)]
    parks = [('US-0143', 'US-AK', 'Alaska Maritime National Wildlife Refuge', 51.9674, 177.533, giant),
             ('US-9100', 'US-AK', 'Unalaska test park', 53.5, -167.5, [ring(-167.45, 53.5, .1, .05, 40)]),
             ('US-9050', 'US-AK', 'Wrangell test park', 60.0, -139.0, [ring(-139.0, 60.0, .2, .1, 40)]),
             ('US-9500', 'US-HI', 'Hawaii test park', 19.1, -155.6, [ring(-155.6, 19.1, .1, .1, 40)]),
             ('US-9600', 'US-WA', 'Washington border test park', 48.9, -121.0, [ring(-121.0, 48.9, .1, .1, 40)]),
             ('US-9700', 'US-NY', 'New York test park', 43.0, -75.0, [ring(-75.0, 43.0, .1, .1, 40)])]
    parks += [(f'US-{9200 + k}', 'US-AK', f'Small test park {k}', 58.3, -160.6 + .045 * k, [ring(-160.6 + .045 * k, 58.3, .015, .01, 40)]) for k in range(120)]
    ca = [('CA-9001', 'BC', 'Border test park', 49.05, -121.0, [ring(-121.0, 49.05, .1, .1, 40)]),
          ('CA-9002', 'BC', 'Central BC test park', 52.5, -127.0, [ring(-127.0, 52.5, .1, .1, 40)]),
          ('CA-9003', 'YT', 'Yukon test park', 60.1, -139.3, [ring(-139.3, 60.1, .1, .05, 40)])]
    write_area(t, parks, ca, old={'US-AK': {'st': 'US-AK', 'pass1': '2026-10-29', 'spots': [], 'marker': 'previous file'}})
    env = {'PASS': '1', 'MINUTES': '0.1', 'STATES': 'US-AK US-HI US-WA', 'REGION': 'na', 'RUN_TAG': 'testpac', 'KPC_FERS_LIVE_DIR': str(t / 'cache/fers'),
           'KPC_FERS_PROGRESS_N': '5', 'KPC_FERS_PROGRESS_S': '2', 'KPC_HARD_END': str(int(time.time()) + 900)}
    t0 = time.time(); rc, out = run(t, S, env); dt1 = time.time() - t0
    rep = json.load(open(t / 'data/fers/report-testpac.json'))['pass1'] if (t / 'data/fers/report-testpac.json').exists() else {}
    looked = json.load(open(t / 'data/fers/looked-testpac.json')) if (t / 'data/fers/looked-testpac.json').exists() else {}
    reuse = json.load(open(t / 'data/fers/reuse-p1-testpac.json')).get('pairs') or {} if (t / 'data/fers/reuse-p1-testpac.json').exists() else {}
    check(rc == 0, f'out of time, pass 1 exits 0 (saved; the next run carries on), not 3 or 1 (exit {rc}, {dt1:.0f} s)')
    check('::warning title=2-fer bot::pass 1 stopped for time' in out and rep.get('stopped for time') is True, 'it says it stopped for time, in the log and the report')
    check(0 < rep.get('pairs tested', 0) < rep.get('pairs whose boxes touch', 0), f"some pairs tested, not all ({rep.get('pairs tested')} of {rep.get('pairs whose boxes touch')})")
    check(len(reuse) == rep.get('pairs tested'), f'the finished pair answers are saved for the next run ({len(reuse)})')
    check(json.load(open(t / 'data/fers/US-AK.json')).get('marker') == 'previous file', "the unfinished state keeps its previous file")
    check('stage start: pass 1 pair tests' in out and len(re.findall(r'^progress: pass 1 pair tests: \d+ of \d+', out, re.M)) >= 2,
          'stage start line and progress lines in the log (every 5 pairs here)')
    lp = set(looked.get('parks') or [])
    check({'CA-9001', 'CA-9003'} <= lp and not lp & {'US-9700', 'CA-9002'}, f'only the area and its border neighbours are loaded (no New York, no central BC park): {sorted(lp & {"CA-9001", "CA-9002", "CA-9003", "US-9700"})}')
    check(rep.get('official parks') == len(parks) - 1 + 2, f"official parks counted for the area: {rep.get('official parks')}")
    check(not re.search(r'Traceback|HardStop|::error', out), 'no crash, no hard stop')
    # the next run carries on from the saved answers and finishes
    env2 = dict(env, MINUTES='5')
    t0 = time.time(); rc2, out2 = run(t, S, env2); dt2 = time.time() - t0
    rep2 = json.load(open(t / 'data/fers/report-testpac.json'))['pass1']
    ak = json.load(open(t / 'data/fers/US-AK.json'))
    check(rc2 == 0 and not rep2.get('stopped for time') and rep2.get('pairs tested') == rep2.get('pairs whose boxes touch'),
          f"the next run finishes: every pair tested (exit {rc2}, {rep2.get('pairs tested')} of {rep2.get('pairs whose boxes touch')}, {dt2:.0f} s)")
    check(rep2.get('pairs reused (nothing changed)') == len(reuse), f"it reuses the saved answers ({rep2.get('pairs reused (nothing changed)')})")
    check('marker' not in ak and any('US-9100' in s.get('refs', []) for s in ak.get('spots', [])),
          "the finished state file is written; the Unalaska spot (west of the old box's edge) is kept")

# ---------------------------------------------------------------- 5 a normal area: byte for byte what main's code wrote
# made by running normal_area() with main 11f908d9's kpc_fers.py (KPC_FERS_TEST_SCRIPTS=<main>/.github/scripts KPC_FERS_PRINT_GOLDEN=1);
# every data/fers file it writes, today's date written as TODAY and the report's fers_rules hash left out
GOLDEN = '17ebca8a53004e16'


def normal_area(script_dir):
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        parks = [('US-9601', 'US-WA', 'Washington test park A', 47.05, -120.95, [ring(-120.95, 47.05, .06, .05, 120)]),
                 ('US-9602', 'US-WA', 'Washington test park B', 47.1, -120.88, [ring(-120.88, 47.09, .06, .05, 120)]),
                 ('US-9603', 'US-WA', 'Washington test park C', 47.6, -122.0, [ring(-122.0, 47.6, .05, .05, 60)]),
                 ('US-9604', 'US-WA', 'Washington border park', 48.98, -121.05, [ring(-121.05, 48.98, .06, .05, 120)]),
                 ('US-9605', 'US-OR', 'Oregon test park', 45.0, -121.0, [ring(-121.0, 45.0, .05, .05, 60)])]
        ca = [('CA-9601', 'BC', 'British Columbia border park', 49.05, -121.0, [ring(-121.0, 49.03, .06, .05, 120)])]
        write_area(t, parks, ca)
        env = {'PASS': '1', 'MINUTES': '5', 'STATES': 'US-WA', 'REGION': 'na', 'RUN_TAG': 'testwa', 'KPC_FERS_LIVE_DIR': str(t / 'cache/fers')}
        rc, out = run(t, script_dir, env)
        today = time.strftime('%Y-%m-%d')
        h = hashlib.sha256()
        names = sorted(p.name for p in (t / 'data/fers').glob('*.json'))
        for n in names:
            d = json.load(open(t / 'data/fers' / n))
            if n.startswith('report-'): d.pop('fers_rules', None)
            h.update(n.encode() + b'\0' + json.dumps(d, sort_keys=True).replace(today, 'TODAY').encode() + b'\0')
        spots = sum(len(json.load(open(t / 'data/fers' / n)).get('spots') or []) for n in names if re.fullmatch(r'(US|CA)-[A-Z]{2}\.json', n))
        return rc, h.hexdigest()[:16], names, spots


rc, hv, names, nsp = normal_area(pathlib.Path(os.environ.get('KPC_FERS_TEST_SCRIPTS') or S))
if os.environ.get('KPC_FERS_PRINT_GOLDEN'): print('GOLDEN=' + hv, names, nsp)
check(rc == 0 and nsp >= 2, f'the normal area runs and finds its spots (exit {rc}, {nsp} rows in {len(names)} files)')
check(hv == GOLDEN, f'its files are byte for byte the ones main (11f908d9) wrote ({hv} == {GOLDEN})')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
