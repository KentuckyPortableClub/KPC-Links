#!/usr/bin/env python3
"""Outline acres (2026-11-19; outside review F9, the reviewer's first slice, step S4): the fact check may size a park by the acres
MEASURED from its own outline (kpc_outline_acres.py) instead of the key's 'ac', which is not a measurement. Made-up shapes only:
a square of known size, a polygon with a hole, a MultiPolygon, broken shapes (0, no crash), the part files of one area; then the
picking of the size: option off = 'ac' as today, option on = the measured value (line 336 and CHURN).
Run:  python3 tests/test_outline_acres_nov19.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import gzip, json, math, pathlib, shutil, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_outline_acres as OA  # noqa: E402
import kpc_key_factcheck as FC  # noqa: E402
import kpc_key_freeze as KF  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

ACRES_PER_KM2 = 247.105
def ring(lon, lat, side_km):
    """A closed square ring, side_km on a side, south-west corner at lon, lat."""
    dx, dy = side_km / (111.32 * math.cos(math.radians(lat + side_km / 2 / 110.57))), side_km / 110.57
    return [[lon, lat], [lon + dx, lat], [lon + dx, lat + dy], [lon, lat + dy], [lon, lat]]
near = lambda a, b, tol=0.01: b and abs(a - b) <= tol * b

# ---- the measuring routine
sq = {'type': 'Polygon', 'coordinates': [ring(-85.0, 38.0, 2.0)]}
check(near(OA.polygon_acres(sq), 4 * ACRES_PER_KM2), f'a 2 km square at latitude 38 N is {OA.polygon_acres(sq):.1f} acres (988.4 within 1%)')
north = {'type': 'Polygon', 'coordinates': [ring(-150.0, 64.0, 2.0)]}
check(near(OA.polygon_acres(north), 4 * ACRES_PER_KM2), f'the same square at latitude 64 N is {OA.polygon_acres(north):.1f} acres (within 1%)')
cw = {'type': 'Polygon', 'coordinates': [ring(-85.0, 38.0, 2.0)[::-1]]}
check(near(OA.polygon_acres(cw), OA.polygon_acres(sq), 1e-9), 'the way a ring is wound does not change its size')
holed = {'type': 'Polygon', 'coordinates': [ring(-85.0, 38.0, 4.0), ring(-84.99, 38.01, 1.0)]}
check(near(OA.polygon_acres(holed), 15 * ACRES_PER_KM2), f'a 4 km square with a 1 km hole is {OA.polygon_acres(holed):.0f} acres (15 km2 within 1%: the hole comes off)')
holed_same = {'type': 'Polygon', 'coordinates': [ring(-85.0, 38.0, 4.0), ring(-84.99, 38.01, 1.0)[::-1]]}
check(near(OA.polygon_acres(holed_same), OA.polygon_acres(holed), 1e-9), 'a hole wound the same way as its outside still comes off')
multi = {'type': 'MultiPolygon', 'coordinates': [[ring(-85.0, 38.0, 2.0)], [ring(-84.0, 38.0, 4.0), ring(-83.99, 38.01, 1.0)]]}
check(near(OA.polygon_acres(multi), 19 * ACRES_PER_KM2), f'a MultiPolygon (4 km2 + 16 km2 with a 1 km2 hole) is {OA.polygon_acres(multi):.0f} acres (19 km2 within 1%)')
broken = [None, {}, {'type': 'Polygon'}, {'type': 'Polygon', 'coordinates': []}, {'type': 'Polygon', 'coordinates': [[]]},
          {'type': 'Polygon', 'coordinates': [[[1, 2], [3, 4]]]}, {'type': 'Polygon', 'coordinates': [[['a', 'b'], [1], None]]},
          {'type': 'MultiPolygon', 'coordinates': None}, {'type': 'MultiPolygon', 'coordinates': [None, 5]}, {'type': 'Point', 'coordinates': [1, 2]},
          {'type': 'LineString', 'coordinates': [[0, 0], [1, 1]]}, 'not a shape', 7]
vals = []
for g in broken:
    try: vals.append(OA.polygon_acres(g))
    except Exception as ex: vals.append(f'crash {ex!r}')  # noqa: BLE001
check(vals == [0.0] * len(broken), f'{len(broken)} empty or broken shapes measure 0 and nothing crashes: {vals}')

# ---- one area's outline files, part files included
tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-outline-acres-'))
def put(path, feats):
    with gzip.open(path, 'wt', encoding='utf-8') as fh: json.dump({'type': 'FeatureCollection', 'features': feats}, fh)
feat = lambda ref, geom: {'type': 'Feature', 'properties': {'ref': ref}, 'geometry': geom}
SIDE = 5.0   # the park's true outline: a 5 km square = 6,178 acres
(tmp / 'outlines').mkdir()
put(tmp / 'outlines' / 'US-XX.geojson.gz', [feat('US-9001', {'type': 'Polygon', 'coordinates': [ring(-85.0, 38.0, SIDE)]}), feat('US-9002', sq), feat('US-9003', None)])
put(tmp / 'outlines' / 'US-XX.p2.geojson.gz', [feat('US-9002', {'type': 'Polygon', 'coordinates': [ring(-84.0, 38.0, 2.0)]})])
put(tmp / 'outlines' / 'US-XY.geojson.gz', [feat('US-9009', sq)])
got = OA.state_acres(tmp / 'outlines', 'US-XX')
check(sorted(got) == ['US-9001', 'US-9002', 'US-9003'], f'one area = its own file and its part files, not the next area: {sorted(got)}')
check(near(got['US-9002'], 8 * ACRES_PER_KM2), 'a park with features in the main file and a part file gets their sum')
check(got['US-9003'] == 0.0 and OA.state_acres(tmp / 'nowhere', 'US-XX') == {}, 'a feature with no shape = 0; no outline file = {}')

# ---- the picking of the size in the fact check
REAL = 25 * ACRES_PER_KM2
REC = {'OBJECTID': 'mdd179', 'Unit_Nm': 'Made Up Valley State Park', 'Loc_Nm': '', 'Mang_Name': 'STAT', 'Des_Tp': 'SP', 'GIS_Acres': 523,
       '_r': [ring(-85.0, 38.0, SIDE)]}
KEY = {'parks': {'US-9001': {'n': 'Made Up Valley State Park', 'g': 'official', 'ac': 523, 'm': [['mdd179', 'Made Up Valley State Park', 523, 'name']]},
                 'US-9004': {'n': 'Other Made Up State Park', 'g': 'official', 'ac': 700, 'm': [['mdd180', 'Other Made Up State Park', 700, 'name']]}}}
REC2 = dict(REC, OBJECTID='mdd180', Unit_Nm='Other Made Up State Park', GIS_Acres=700, _r=[ring(-83.0, 38.0, 1.0)])
BY = {'mdd179': REC, 'mdd180': REC2}
PIN = {'US-9001': ['Made Up Valley State Park', '', '', '', '', 38.02, -84.98, 5, 0, 0], 'US-9004': ['Other Made Up State Park', '', '', '', '', 38.004, -82.996, 5, 0, 0]}
TRUTH = {'US-9001': {'official': {'acres': 6000.0, 'clean': True, 'sent': 'Made Up Valley State Park covers 6,000 acres.', 'url': 'https://x.gov/a'}}}
PREV = {'US-9001': {'ac': 14225, 'm': [['mdd179', 'Made Up Valley State Park', 523, 'name']]}, 'US-9004': {'ac': 700, 'm': [['mdd180', 'Other Made Up State Park', 700, 'name']]}}
flags = lambda e: {f[0] for f in e.get('flags') or []}
off = FC.check_area('US-XX', KEY, BY, PIN, TRUTH, agency={}, prev=PREV, today='2026-11-19')['parks']
check(off['US-9001']['acres']['outline'] == 523 and off['US-9001']['acres']['from'] == 'key', "option off: the size is the key's 'ac' as today (523)")
check('SIZE_SMALL' in flags(off['US-9001']) and 'size' not in off['US-9001']['witnesses'], "option off: the wrong 'ac' still raises SIZE_SMALL, as today")
check('CHURN' in flags(off['US-9001']), "option off: CHURN compares the two keys' 'ac' as today (14225 -> 523)")
meas = got   # US-9001 measured from its outline; US-9004 has no outline on disk
on = FC.check_area('US-XX', KEY, BY, PIN, TRUTH, agency={}, prev=PREV, today='2026-11-19', measured=meas, prev_measured={'US-9001': REAL * 1.02})['parks']
check(on['US-9001']['acres']['outline'] == round(meas['US-9001']) and near(meas['US-9001'], REAL) and on['US-9001']['acres']['from'] == 'outline',
      f"option on: the size is the measured outline ({on['US-9001']['acres']['outline']:,} acres), marked 'from': 'outline'")
check('size' in on['US-9001']['witnesses'] and not {'SIZE_SMALL', 'SIZE_BIG'} & flags(on['US-9001']), 'option on: the measured size agrees with the official 6,000 acres (size witness, no size flag)')
check('CHURN' not in flags(on['US-9001']), 'option on: CHURN compares measured acres on both sides (2% apart = no CHURN)')
check(on['US-9004']['acres']['outline'] == 700 and on['US-9004']['acres']['from'] == 'key', "option on, but no outline on disk for the park: 'ac' as today")
half = FC.check_area('US-XX', KEY, BY, PIN, TRUTH, agency={}, prev=PREV, today='2026-11-19', measured=meas)['parks']
check('CHURN' in flags(half['US-9001']), "option on with no previous outlines: CHURN keeps comparing 'ac' with 'ac' (never measured with 'ac')")
check(FC.check_area('US-XX', KEY, BY, PIN, TRUTH, agency={}, prev=PREV, today='2026-11-19', measured={})['parks'] == off, 'an empty measured table = option off, the same result')

# ---- the whole run, through the option
for d in ('cache', 'pinfo', 'keys'): (tmp / d).mkdir()
with gzip.open(tmp / 'cache' / 'US-XX.json.gz', 'wt', encoding='utf-8') as fh: json.dump({'recs': [REC, REC2]}, fh)
json.dump({'parks': PIN}, open(tmp / 'pinfo' / 'US-XX.json', 'w')); json.dump(KEY, open(tmp / 'keys' / 'US-XX.json', 'w'))
base = ['run', '--keys', str(tmp / 'keys'), '--cache', str(tmp / 'cache'), '--parkinfo', str(tmp / 'pinfo'), '--date', '2026-11-19']
FC.main(base + ['--out', str(tmp / 'o1')]); FC.main(base + ['--out', str(tmp / 'o2'), '--outline-acres', str(tmp / 'outlines')])
r1 = json.load(open(tmp / 'o1' / 'factcheck-US-XX.json'))['parks']['US-9001']['acres']; r2 = json.load(open(tmp / 'o2' / 'factcheck-US-XX.json'))['parks']['US-9001']['acres']
check(r1['outline'] == 523 and r2['outline'] == round(meas['US-9001']), f"the run: no option = {r1['outline']} (the key), --outline-acres = {r2['outline']:,} (the outline)")

# ---- not a rule file
check('kpc_outline_acres.py' in KF.NOT_RULES and not any('kpc_outline_acres' in f for fs in KF.RULE_FILES.values() for f in fs),
      'kpc_outline_acres.py is in NOT_RULES and in no RULE_FILES (no rules hash moves)')
rule_srcs = {f for fs in KF.RULE_FILES.values() for f in fs if f.endswith('.py')}
check(not [f for f in rule_srcs if (ROOT / f).is_file() and 'kpc_outline_acres' in (ROOT / f).read_text(encoding='utf-8')], 'no rule file imports kpc_outline_acres')
shutil.rmtree(tmp, ignore_errors=True)
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
