#!/usr/bin/env python3
"""KPC owner, 2026-11-12: Quality's must-fix on #154 and the n-fer time follow-up. Offline (the real kpc_fers.py runs in a
subprocess whose map reads and network all fail at once).
1 the live US-AK candidate US-4448+US-4538@area@54.725,-130.791 (Tongass National Forest x Misty Fjords National Monument,
  center 55.177 N 130.301 W) lies east of the pin-only Alaska box (east edge 130.649 W = Misty Fjords' pin + 0.2). A spot whose
  parks with their own outline are all filed under the area's states is still the area's row; a spot with a park of another
  area (British Columbia) outside the boxes is still left for its own area
2 an n-fer (3-fer and up) stage cut for time marks the pass stopped for time and its parks unfinished (pass 1 keeps the previous
  file / saves it marked incomplete; pass 2 and 3 leave the n-fer row waiting, never 'dropped')"""
import contextlib, gzip, io, json, math, os, pathlib, subprocess, sys, tempfile, types
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
ROW = {'id': 'US-4448+US-4538@area@54.725,-130.791', 'refs': ['US-4448', 'US-4538'], 'center': [55.177264, -130.301469]}
TONGASS = ('US-4448', 'US-AK', 'Tongass National Forest', 58.4167, -134.547)   # POTA pins (KPC-Data data/parkinfo/US-AK.json)
MISTY = ('US-4538', 'US-AK', 'Misty Fjords National Monument', 54.767, -130.849)

# ---------------------------------------------------------------- 1a the box: pins only, so the live row is outside it
K.REGION = 'na'
ak = {'US-AK': [('Alaska Maritime National Wildlife Refuge', 51.9674, 177.533), (TONGASS[2], TONGASS[3], TONGASS[4]), (MISTY[2], MISTY[3], MISTY[4])]}
bx = K.area_boxes(ak)
east = max(b[2] for b in bx)
check(abs(east - (-130.649)) < 1e-9, f"the Alaska box's east edge is Misty Fjords' pin + 0.2 = 130.649 W ({east:.3f})")
check(not K.in_area(ROW['center'][1], ROW['center'][0], bx), f"{ROW['id']} (center 55.177 N 130.301 W) is outside the pin-only box")
check(K.in_area(177.6, 52.0, bx) and K.in_area(-176.6, 51.9, bx), 'the date line is still handled (western Aleutians and Adak inside)')
check("def _ours(s):" in src and "in_area(s['center'][1], s['center'][0]) or _ours(s)" in src,
      'the spot filter keeps a spot whose own-outline parks are all filed under the area (the same test as the filing below it)')


# ---------------------------------------------------------------- 1b the real script, offline: the row is written to US-AK.json
def ring(cx, cy, rx, ry, n):
    r = [[round(cx + rx * math.cos(2 * math.pi * i / n), 6), round(cy + ry * math.sin(2 * math.pi * i / n), 6)] for i in range(n)]
    return r + [r[0]]


# the fixtures of test_fers_area_boxes_time_nov11.py (POTA pins, the key, saved outlines; the offline wrapper)
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


with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    cx, cy = ROW['center'][1], ROW['center'][0]
    parks = [TONGASS + ([ring(cx - .05, cy, .12, .08, 120)],), MISTY + ([ring(cx + .05, cy, .12, .08, 120)],)]
    # a British Columbia park whose pin sits inside the Alaska box, overlapping Tongass only east of it: Canada's area run owns it
    ca = [('CA-9901', 'BC', 'British Columbia test park', 55.6, -130.7, [ring(-130.35, 55.6, .4, .06, 120)]),]
    parks[0] = parks[0][:5] + ([ring(cx - .05, cy, .12, .08, 120), ring(-130.35, 55.6, .1, .05, 120)],)
    write_area(t, parks, ca, old={'US-AK': {'st': 'US-AK', 'pass1': '2026-10-29', 'spots': [], 'marker': 'previous file'}})
    env = {'PASS': '1', 'MINUTES': '5', 'STATES': 'US-AK', 'REGION': 'na', 'RUN_TAG': 'testak', 'KPC_FERS_LIVE_DIR': str(t / 'cache/fers')}
    rc, out = run(t, S, env)
    f = t / 'data/fers/US-AK.json'
    d = json.load(open(f)) if f.exists() else {}
    sp = d.get('spots') or []
    tm = [s for s in sp if sorted(s.get('refs') or []) == ROW['refs']]
    check(rc == 0 and 'marker' not in d, f'the Alaska run finishes and writes US-AK.json (exit {rc})')
    check(tm and all(not K.in_area(s['center'][1], s['center'][0], bx) for s in tm),
          f"the Tongass x Misty Fjords row is kept although its center is east of the box ({[s.get('id') for s in tm]})")
    bc = [s for s in sp if 'CA-9901' in (s.get('refs') or [])]
    check(not bc and 'spots outside this area left for their own area' in out + json.dumps(json.load(open(t / 'data/fers/report-testak.json'))),
          'the Tongass x British Columbia spot east of the box is still left for its own area')
    check('Traceback' not in out, 'no crash')

# ---------------------------------------------------------------- 2 the n-fer stage cut for time
sq = lambda x0, y0, d: [[[[x0, y0], [x0 + d, y0], [x0 + d, y0 + d], [x0, y0 + d], [x0, y0]]]]
G = {'US-1': sq(-121.0, 47.0, .1), 'US-2': sq(-120.95, 47.0, .1), 'US-3': sq(-120.97, 47.0, .1)}
K.PINS.update({'US-1': ('one', 47.05, -120.95, '', '', 'WA'), 'US-2': ('two', 47.05, -120.9, '', '', 'WA'), 'US-3': ('three', 47.05, -120.92, '', '', 'WA')})
cwd = os.getcwd()
ss0, late0 = K.stage_start, K.late
with tempfile.TemporaryDirectory() as t:
    os.chdir(t); pathlib.Path('data/fers').mkdir(parents=True, exist_ok=True)
    try:
        K.OUT = pathlib.Path('data/fers'); K.TIMED_OUT.clear(); K.TIMED_PAIRS.clear(); K.TESTED.clear(); K.NFER_CUT.clear(); K.LOG.clear()
        flag = {'nfer': False}
        K.stage_start = lambda what: flag.update(nfer=flag['nfer'] or 'n-fers' in what)
        K.late = lambda screen=False, frac=None: flag['nfer']   # time runs out as the n-fer stage starts
        cnt = {'pairs tested': 0}
        with contextlib.redirect_stdout(io.StringIO()): spots = K.find_spots(G, {}, {('US-1', 'US-2'), ('US-1', 'US-3'), ('US-2', 'US-3')}, cnt)
        check(cnt['pairs tested'] == 3 and any(s['kind'] == 'area' for s in spots), f"the pairs are tested and give area spots ({cnt['pairs tested']}, {len(spots)} spots)")
        check(flag['nfer'] and cnt.get('stopped for time') is True, 'an n-fer stage cut for time marks the pass stopped for time')
        check({'US-1', 'US-2', 'US-3'} <= K.NFER_CUT and any('fers cut short for time' in x for x in K.LOG), f'its parks are listed as unfinished ({sorted(K.NFER_CUT)})')
        # not cut: nothing marked
        K.TESTED.clear(); K.NFER_CUT.clear(); K.late = lambda screen=False, frac=None: False
        cnt = {'pairs tested': 0}
        with contextlib.redirect_stdout(io.StringIO()): spots = K.find_spots(G, {}, {('US-1', 'US-2'), ('US-1', 'US-3'), ('US-2', 'US-3')}, cnt)
        check(not cnt.get('stopped for time') and not K.NFER_CUT and any(len(s['refs']) == 3 for s in spots), 'a finished n-fer stage marks nothing and finds the 3-fer')
    finally:
        K.stage_start, K.late = ss0, late0
        import kpc_save; kpc_save.flush_status()
        os.chdir(cwd)
check('undone |= {st_of(r) for r in NFER_CUT}' in src, 'pass 1: the areas of a cut n-fer stage keep their previous file (or are saved marked incomplete)')
check("elif NFER_CUT and len(s['refs']) > 2 and set(s['refs']) & NFER_CUT:" in src and "s['status'] = f'waiting for pass {PASS}'; continue" in src,
      "pass 2 and 3: an n-fer row whose test was cut waits for the next run, never 'dropped'")
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
