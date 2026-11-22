#!/usr/bin/env python3
"""F16 A and B (22 Nov 2026). Invented parks only. Offline.
A: a 25-yard-or-wider sliver next to federal land is counted only when it is a
real gap, not a drawing error (length/width at or over KPC_FERS_SLIVER_ASPECT, default 8).
B: a trail or river 100-foot zone gets the same one-grid-cell not-sure band as the area size lines.
Run: python3 -B tests/test_fers_sliver_and_zone_nov22.py
"""
import os, pathlib, sys, tempfile
sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
os.environ['PASS'] = '3'
os.environ['REGION'] = 'na'
os.environ['HTTP_CACHE'] = ''
for k in list(os.environ):
    if k.startswith('KPC_FERS_') or 'proxy' in k.lower():
        os.environ.pop(k)
TD = pathlib.Path(tempfile.mkdtemp(prefix='kpc-f16-'))
os.chdir(TD)
import kpc_fers as K  # noqa: E402

FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok:
        FAILS.append(what)


# --- F16 B: 100-foot trail/river zone band (one cell, same pattern as the area lines) ---
# at pass 3, CELL is 5 m; ZONE is 30.48 m
check(K.ZONE == 30.48 and K.CELL == 5.0, 'the 100-foot zone is 30.48 m and pass 3 uses a 5 m cell')
check(K.near_line({'kind': 'trail', 'zone_wide_m': 30.48}).startswith('near a size line')
      and '100-foot zone' in K.near_line({'kind': 'trail', 'zone_wide_m': 30.48}),
      'F16 B a trail zone width on the 100-foot line is NOT SURE')
check(K.near_line({'kind': 'river', 'strip_wide_m': 30.48}).startswith('near a size line')
      and '100-foot zone' in K.near_line({'kind': 'river', 'strip_wide_m': 30.48}),
      'F16 B a river strip width on the 100-foot line (strip_wide_m) is NOT SURE')
check(K.near_line({'kind': 'trail', 'zone_wide_m': 34.0}).startswith('near a size line'),
      'F16 B a trail zone within one cell of the 100-foot line is still in the band')
check(K.near_line({'kind': 'trail', 'zone_wide_m': 30.48 + 6.0}) == ''
      and K.near_line({'kind': 'river', 'zone_wide_m': 20.0}) == '',
      'F16 B a trail or river zone well off the 100-foot line is not NOT SURE')
check(K.near_line({'kind': 'river', 'wide_m': 22.86}) == ''
      and K.near_line({'kind': 'trail', 'wide_m': 30.48}) == '',
      'F16 B a trail or river row is judged by zone_wide_m / strip_wide_m, not wide_m')
check(K.near_line({'kind': 'area', 'wide_m': 22.86}).startswith('near a size line')
      and K.near_line({'kind': 'area', 'wide_m': 200}) == '',
      'area rows still use the 25-yard and 50-yard lines')
os.environ['KPC_FERS_NEAR_LINE'] = '0'
check(K.near_line({'kind': 'trail', 'zone_wide_m': 30.48}) == ''
      and K.near_line({'kind': 'area', 'wide_m': 22.86}) == '',
      'F16 B with the near-line rule off, a width on the line is not NOT SURE')
os.environ.pop('KPC_FERS_NEAR_LINE')

# --- F16 A: fed-neighbour detection (invented names only) ---
PIN = {
    'US-9901': ['Sample National Park'],
    'US-9902': ['Sample National Forest'],
    'US-9903': ['Sample National Wildlife Refuge'],
    'US-9904': ['Sample National Grassland'],
    'US-9905': ['Sample State Park'],
    'US-9906': ['Sample Wilderness'],
    'US-9907': ['Sample National Recreation Area'],
}
parks = {r: {} for r in PIN}
check(K.fed_neighbours(['US-9901', 'US-9902'], parks, PIN) == 'Sample National Park x Sample National Forest',
      'F16 A a national park next to a national forest is a fed-neighbour pair')
check(K.fed_neighbours(['US-9903', 'US-9904'], parks, PIN) == 'Sample National Wildlife Refuge x Sample National Grassland',
      'F16 A a refuge next to a grassland is a fed-neighbour pair')
check(K.fed_neighbours(['US-9905', 'US-9902'], parks, PIN) == '',
      'F16 A a state park next to a national forest is not a fed-neighbour pair')
check(K.fed_neighbours(['US-9901', 'US-9905'], parks, PIN) == '',
      'F16 A two parks with no forest/grassland are not a fed-neighbour pair')
check(K.fed_neighbours(['US-9906', 'US-9902'], parks, PIN) == ''
      and K.fed_neighbours(['US-9907', 'US-9902'], parks, PIN) == '',
      'F16 A a wilderness or recreation area designation is not a fed-neighbour pair')

# --- F16 A: drawing-error vs real-gap (aspect 8 in the switch file) ---
check(K.sliver_aspect_min() == 8.0, 'F16 A the switch file sets the drawing-error aspect at 8')
ribbon = {'kind': 'area', 'wide_m': 25.0, 'len_m': 200.0}          # 25 x 200 m, aspect 8.0
longer = {'kind': 'area', 'wide_m': 25.0, 'len_m': 250.0}          # aspect 10
compact = {'kind': 'area', 'wide_m': 30.0, 'len_m': 80.0}           # aspect ~2.67, a real gap
thin_short = {'kind': 'area', 'wide_m': 20.0, 'len_m': 400.0}       # under 25 yards, not this rule
unknown = {'kind': 'area', 'wide_m': 30.0}                         # length unknown: do not guess
# acres path: 25 m * 200 m / 4046.86 ≈ 1.235 acres
from_acres = {'kind': 'area', 'wide_m': 25.0, 'acres': 25.0 * 200.0 / 4046.86}
check(K.drawing_error_sliver(ribbon) and K.drawing_error_sliver(longer),
      'F16 A a 25-yard-wide sliver at or over aspect 8 is a drawing error')
check(not K.drawing_error_sliver(compact),
      'F16 A a more compact 25-yard-or-wider overlap is a real gap, not a drawing error')
check(not K.drawing_error_sliver(thin_short),
      'F16 A a sliver under 25 yards is not judged by this rule')
check(not K.drawing_error_sliver(unknown),
      'F16 A a sliver whose length is not known is not guessed to be a drawing error')
check(K.drawing_error_sliver(from_acres) and abs(K.sliver_len_m(from_acres) - 200.0) < 0.01,
      'F16 A length comes from acres / width when len_m is missing')
just_under = {'kind': 'area', 'wide_m': 25.0, 'len_m': 199.0}       # aspect 7.96
check(not K.drawing_error_sliver(just_under),
      'F16 A an aspect just under 8 is counted as a real gap')
wide_ribbon = {'kind': 'area', 'wide_m': 45.72, 'len_m': 45.72 * 10}   # 50 yards wide, aspect 10
check(not K.drawing_error_sliver(wide_ribbon),
      'F16 A an overlap 50 yards or wider is counted even when it is long and thin')

# --- F16 A: the filter only drops a drawing-error sliver next to federal land ---
ribbon['kind'] = 'area'
compact['kind'] = 'area'
why = K.fed_sliver_filter(ribbon, ['US-9901', 'US-9902'], parks, PIN)
check(why and 'aspect' in why and 'KPC_FERS_SLIVER_ASPECT' in why,
      'F16 A a drawing-error sliver next to federal land is not counted')
check(K.fed_sliver_filter(compact, ['US-9901', 'US-9902'], parks, PIN) == '',
      'F16 A a real compact gap next to federal land is counted')
check(K.fed_sliver_filter(unknown, ['US-9901', 'US-9902'], parks, PIN) == '',
      'F16 A a fed-neighbour sliver with unknown length is counted (not guessed)')
check(K.fed_sliver_filter(ribbon, ['US-9905', 'US-9902'], parks, PIN) == '',
      'F16 A a drawing-error shape that is not a fed-neighbour pair is left alone')
# a large compact park-in-forest overlap (200 m wide, 400 m long) is not held
big = {'kind': 'area', 'wide_m': 200.0, 'len_m': 400.0}
check(K.fed_sliver_filter(big, ['US-9901', 'US-9902'], parks, PIN) == ''
      and not K.drawing_error_sliver(big),
      'F16 A a large compact park-in-forest overlap is not held as a drawing error')
os.environ['KPC_FERS_FED_NEIGHBOUR'] = '0'
check(K.fed_sliver_filter(ribbon, ['US-9901', 'US-9902'], parks, PIN) == '',
      'F16 A with the fed-neighbour switch off, a sliver is not filtered')
os.environ.pop('KPC_FERS_FED_NEIGHBOUR')

# bookkeeping drop, not a "these two are not a 2-fer" denial
st = 'dropped: shared-boundary drawing error: length 200 m / width 25 m = aspect 8.0, at or over the drawing-error line 8'
check(K.denial(st) is False and not K._shown({'status': st}),
      'F16 A a drawing-error sliver is not shown and is not recorded as "not a 2-fer"')

print(f'{len(FAILS)} failed' if FAILS else 'ALL PASS')
sys.exit(1 if FAILS else 0)
