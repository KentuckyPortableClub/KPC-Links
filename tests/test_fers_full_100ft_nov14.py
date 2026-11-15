#!/usr/bin/env python3
"""Nov 14 2026 (KPC owner, rule R5): the 2-fer builder measures the FULL 100 ft (30.48 m) for a line-only park: from a trail's centre
line (ZONE) and from a river's bank (BANK); no margin is taken off (was ZONE = 30.48 - 5.0). The station spot must still be
STATION_IN (5 m) inside the other park: unchanged, not part of the ruling.
line_spots (the real code) on a synthetic 1 km square park, a 400 m line running beside its east edge:
- at a 1 m raster (the rule without raster slop): a trail 25 m from the park pairs, 35 m does not; a river whose near bank is 25 m
  from the park pairs (the water map is a stub: no network), 35 m does not;
- at the real pass-3 raster (5 m): the same trail answers (25 m pairs, 35 m does not).
Offline, no run started."""
import math, os, pathlib, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
os.environ['PASS'] = '3'
_cwd = os.getcwd(); os.chdir(tempfile.mkdtemp())   # kpc_fers makes data/fers in the working folder: keep it out of the repo
import kpc_fers as K
os.chdir(_cwd)
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


check(K.ZONE == 30.48, f'ZONE is the full 100 ft, 30.48 m (got {K.ZONE})')
check(K.BANK == 30.48, f'BANK is the full 100 ft from the bank, 30.48 m (got {K.BANK})')
check(K.STATION_IN == 5.0, f'STATION_IN (the station spot 5 m inside the other park) is unchanged (got {K.STATION_IN})')
src = (HERE / '.github/scripts/kpc_fers.py').read_text(encoding='utf-8')
check('30.48 - 5.0' not in src and '5 m to spare' not in src, 'no 5 m margin is taken off the 100 ft any more')
check('<= BANK + wd[' in src and '<= ZONE + wd[' not in src, 'the river test is the full 100 ft from the bank (BANK + wd), not ZONE + wd')
check("w.lines([x['shape']], ZONE + STATION_IN)" not in src and "w.lines([x['shape']], ZONE)" in src,
      'the drawn trail zone is the 100-ft band (ZONE), with no extra 5 m on top of the full ZONE')
check('(or only an approximate one)' not in src and 'members first' not in src, "the missing-boundary list's about text is no longer stale")
for f in ('.claude/notes/mapping.md', '.claude/RULES-NOW.md'):
    t = (HERE / f).read_text(encoding='utf-8')
    check('full 100 ft (30.48 m) from the trail' in t and 'STATION_IN' in t, f'{f}: R5 says how the 100 ft is measured')

lat0, lon0 = 45.0, -90.0
kx, ky = 111320 * math.cos(math.radians(lat0)), 110574


def P(x, y): return [lon0 + x / kx, lat0 + y / ky]


SQ = [[P(-500, -500), P(500, -500), P(500, 500), P(-500, 500), P(-500, -500)]]   # the park's east edge is x = 500
BOX = [lon0 - 0.02, lat0 - 0.02, lon0 + 0.03, lat0 + 0.02]


def trail(d): return K.line_spots('US-LINE', [[P(500 + d, -200), P(500 + d, 200)]], 'US-AREA', [SQ], False, BOX, 'trail')


def river(b):   # a 60 m wide river whose near bank is b metres from the park; the river park's line is its centre line
    W = [[[P(500 + b, -800), P(560 + b, -800), P(560 + b, 800), P(500 + b, 800), P(500 + b, -800)]]]
    K.nhd_water = lambda bounds, rivers_only=False: W
    return K.line_spots('US-RIV', [[P(530 + b, -200), P(530 + b, 200)]], 'US-AREA', [SQ], False, BOX, 'river')


_cell, _nhd = K.CELL, K.nhd_water
try:
    K.CELL = 1.0
    check([x['len_m'] for x in trail(25)] == [400], 'a park 25 m from a trail now pairs (the whole 400 m stretch)')
    check(trail(35) == [], 'a park 35 m from a trail does not pair')
    check([x['len_m'] for x in river(25)] == [400], "a park 25 m from a river's bank pairs")
    check(river(35) == [], "a park 35 m from a river's bank does not pair")
    K.CELL = 5.0   # the real pass-3 raster
    check([x['len_m'] for x in trail(25)] == [400] and trail(35) == [], 'at the pass-3 raster (5 m): 25 m from a trail pairs, 35 m does not')
finally:
    K.CELL, K.nhd_water = _cell, _nhd

print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
