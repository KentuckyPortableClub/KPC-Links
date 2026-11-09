#!/usr/bin/env python3
"""Nov 9 PM 2-fer fixes folded into the weekly batch (Brandon t901u/t902u/t905u/t906u; run 42649544758). Offline: no network.
1 a park with a bad POTA pin (0,0) and saved official record ids is tested by those outlines; the pin is never used or moved
  (CA-2062 Iles de la Paix: pin 0,0, saved id 22162); a bad-pin park with no saved id is still left out and listed
2 a per-park time limit: one slow pair / map request is skipped and listed, never freezes the pass
3 pass 1 downloads stop at half the pass, parks not reached are never half-read and their areas keep their files
4 a crash exits 1 and the step's hard end exits 3 (the run shows red, never a green check after a time-out)"""
import json, os, pathlib, sys, tempfile, time, types
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
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


src = open(S / 'kpc_fers.py', encoding='utf-8').read()
cwd = os.getcwd()
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    for d in ('data/parkinfo', 'data/ca-key', 'data/us-key', 'data/world-key'): (t / d).mkdir(parents=True)
    # POTA's own list: CA-2062 and CA-9999 at 0,0; CA-0001 fine
    (t / 'data/parkinfo/CA.json').write_text(json.dumps({'parks': {
        'CA-2062': ['Iles de la Paix Migratory Bird Sanctuary', '', 'Bird Sanctuary', '', '', 0.0, -0.0, 0, 0, 0, 'QC'],
        'CA-9999': ['Nowhere Bird Sanctuary', '', 'Bird Sanctuary', '', '', 0.0, 0.0, 0, 0, 0, 'QC'],
        'CA-0001': ['Somewhere Provincial Park', 'https://example.ca/map', 'Provincial Park', '', '', 46.1, -73.2, 0, 0, 0, 'QC'],
        'CA-0002': ['Pin Fixed Since Sanctuary', '', 'Bird Sanctuary', '', '', 46.2, -73.3, 0, 0, 0, 'QC']}}))
    (t / 'data/ca-key/CA-QC.json').write_text(json.dumps({'parks': {
        'CA-2062': {'bk': [22162, None, 'MBS', 'des', 'pin00'], 'g': 'official', 'm': [[22162, 'Iles de la Paix Bird Sanctuary', 2371, 'name']]},
        'CA-9999': {'bk': [None, None, None, None, 'pin00'], 'g': 'pin', 'm': []},
        'CA-0001': {'bk': [5, 0.1, 'PP', 'src', ''], 'g': 'official', 'm': [[5, 'Somewhere Provincial Park', 10, 'name']]},
        'CA-0002': {'bk': [7, None, 'MBS', 'des', 'pin00'], 'g': 'official', 'm': [[7, 'Pin Fixed Since Sanctuary', 3, 'name']]}}}))
    os.chdir(t)
    try:
        K.REGION = 'na'
        PIN = K.pins()
        check(PIN.get('CA-2062', [None, 1, 1])[1:3] == (None, None) and 'CA-2062' in K.BAD_PIN, 'CA-2062 (pin 0,0): name kept, no coordinates, listed as a bad pin')
        check(PIN['CA-0001'][1:3] == (46.1, -73.2), 'a good pin is unchanged (never moved)')
        parks, skip = K.official_parks(PIN)
        check('CA-2062' in parks and 22162 in parks['CA-2062']['ids'] and 'CA-2062' in K.NOPIN_BY_ID, 'CA-2062 is tested by its saved record id 22162')
        check('CA-9999' not in parks and skip.get('no outline', 0) >= 1, 'a bad-pin park with no saved id is still left out')
        check('CA-0002' in parks and PIN['CA-0002'][1] is None and 'CA-0002' in K.NOPIN_BY_ID, "the key's 'pin00' mark blanks the pin even when POTA's file looks fine")
        check(K.pin_inside('CA-2062', PIN, {}, {}) is None, 'pin_inside: no usable pin = None (pins never count)')
        try: K.map_link('CA-NOT-THERE', PIN); r = True
        except KeyError: r = False
        check(r, "map_link never raises KeyError (pass 3 stopped on 'CA-2062' in run 42649544758)")
        try: K.missing_list(PIN, parks, {}, {}, {}, '2026-11-09'); r = True
        except TypeError: r = False
        check(r, 'the missing-boundary list skips parks with no usable pin (no crash)')
    finally:
        os.chdir(cwd)

# 2 per-park time limit
with K.park_clock('US-1+US-2', 'test pair', seconds=1) as c:
    try: time.sleep(5)
    except Exception: pass  # noqa: BLE001  (the limit is a BaseException: an 'except Exception' never eats it)
check(c.hit and 'US-1+US-2' in K.TIMED_OUT, 'a pair over its limit is cut, skipped and listed')
with K.park_clock('fast', 'test', seconds=5) as c2: time.sleep(.05)
check(not c2.hit and 'fast' not in K.TIMED_OUT, 'a fast park is untouched')

# a slow map request: skipped, listed, the map dropped after 2 time-outs, the parks counted as not read
calls = []
def slow_get(url, params, tries=3, timeout=120):
    calls.append(url); time.sleep(3); return {'features': []}
g0, ps0 = K.get, K.PARK_S
K.get, K.PARK_S = slow_get, 1
try:
    parks = {f'US-{i}': {'st': 'US-ZZ', 'ids': list(range(i * 100, i * 100 + 100)), 'names': {}} for i in range(1, 4)}
    got, bad = K.download(parks, sorted(parks), .0005, 5)
finally:
    K.get, K.PARK_S = g0, ps0
check(len(calls) == 2 and not got and bad == set(parks), f'a slow map: 2 requests cut, then skipped for the run; its parks listed as not read ({len(calls)} calls)')
# pass 1 downloads stop at half the pass; a park not reached is never half-read
K.SLOW_MAP.clear(); K.DL_CUT.clear()
t0, lim = K.T0, K.LIMIT
K.T0, K.LIMIT = time.time() - 100, 120   # 100 s of a 120 s pass gone = past half
try: got, bad = K.download({'US-7': {'st': 'US-ZZ', 'ids': [1], 'names': {}}}, ['US-7'], .0005, 5)
finally: K.T0, K.LIMIT = t0, lim
check(not got and 'US-7' in K.DL_CUT and 'US-7' not in bad, 'pass 1: past half its time, downloads stop; the park is listed as not reached')
check('undone |= {st_of(r) for r in DL_CUT}' in src and "counts['stopped for time'] = True; counts['parks not downloaded: out of time']" in src,
      'parks not downloaded for time mark the pass as cut short and their areas keep their previous files')
check('if PASS != 1: TESTED.discard((a, b))' in src and 'if TIMED_PAIRS:' in src, 'a pair skipped for time: pass 1 keeps its old rows, passes 2-3 leave it waiting')

# 4 the step's hard end
K.HARD_END = time.time() + 1; K._arm()
try:
    time.sleep(4); r = False
except K.HardStop: r = True
finally:
    K.HARD_END = 0; K._arm()
check(r, "the step's hard end stops the bot (HardStop)")
check('sys.exit(3)' in src and "notice('2-fer bot', f'stopped: {e}')\n        sys.exit(1)" in src, 'a crash exits 1 and the hard end exits 3 (red run, not green)')
check('if late(): more = []; lw = []' in src and "add_lines(files, G, today) if not late() else 0" in src, "pass 5's later stages respect the time")
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
