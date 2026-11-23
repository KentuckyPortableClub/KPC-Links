#!/usr/bin/env python3
"""23 Nov 2026, owner 5:53 AM: 'Yes' (rule W7, measure the size one layer at a time). The PC test of 22 Nov showed Wisconsin's
check rows jump from 5,903 to 10,658. The cause: a park with no union acreage got a measured 'ac' that added up EVERY joined
row, so a property saved in a managed-lands layer, a parcel layer and the national list was counted three or four times; the
size check then read '4 times the agency's own figure' and sent every row to the check list.
W7: the rows are totalled one layer at a time; the biggest layer counts in full and a smaller layer is added only when it
lies on other ground. A twin row (the builder's own 'same land again') is left out. Invented parks and records; no
connection is opened."""
import pathlib, socket, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))


def _no_net(*a, **k): raise RuntimeError('no network in tests')
socket.socket.connect = _no_net
import kpc_key_rules as KR  # noqa: E402
import kpc_match_checks as MC  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


box = lambda x, y, w, h: [[x, y], [x, y + h], [x + w, y + h], [x + w, y], [x, y]]
near = lambda a, b, pct=5: abs(a - b) <= pct / 100 * b

# ---- one property, saved three times: the agency's managed-lands record, its parcel layer (three parcels, one with no acres on
# file) and the national list. All on the same ground.
WHOLE = box(-89.60, 44.20, 0.040, 0.030)
PARCELS = {'sgzzd1': box(-89.60, 44.20, 0.020, 0.030), 'sgzzd2': box(-89.58, 44.20, 0.012, 0.030), 'sgzzd3': box(-89.568, 44.20, 0.008, 0.030)}
shapes = {'sgzza7': [WHOLE], '5501': [WHOLE], 'zzo7': [WHOLE], **{k: [v] for k, v in PARCELS.items()}}
LAND = KR.ring_acres([WHOLE])
P3 = KR.ring_acres([PARCELS['sgzzd3']])
rows = [['sgzza7', 'Heron Marsh State Wildlife Area', round(LAND), 'same name'],
        ['zzo7', 'Heron Marsh State Wildlife Area', round(LAND), 'same name'],          # the same record under its old id: a twin
        [5501, 'Heron Marsh State Wildlife Area', round(LAND * .98), 'same name'],      # the national list
        ['sgzzd1', 'Heron Marsh Wildlife Area', round(KR.ring_acres([PARCELS['sgzzd1']])), 'same name'],
        ['sgzzd2', 'Heron Marsh Wildlife Area', round(KR.ring_acres([PARCELS['sgzzd2']])), 'same name'],
        ['sgzzd3', 'Heron Marsh Wildlife Area', 0, 'same name']]                        # a parcel with no acres on file
got = KR.measured_ac(rows, lambda i: shapes.get(i), None, ['zzo7'])
everything = sum(r[2] for r in rows) + P3                                               # what the old routine wrote: every row added up
check('a property held in three layers on the same ground is counted once, not once per layer '
      f'({got and got[0]} acres for {LAND:.0f} acres of land; every row added up = {everything:.0f})', got and near(got[0], LAND))
check('the parcel with no acres on file is still measured from its shape', got and got[1] == 1)
check('the old total was about four times the land (the fault)', everything > 3.5 * LAND)

# ---- pieces from two layers SIDE BY SIDE are different ground: both count (Handoff 8 fix 4, a study-area piece beside the park)
side = {'sgzza1': [box(-112.00, 38.00, 0.05, 0.05)], 'wsa9': [box(-111.90, 38.00, 0.04, 0.04)]}
a1, a2 = KR.ring_acres(side['sgzza1']), KR.ring_acres(side['wsa9'])
got2 = KR.measured_ac([['sgzza1', 'Red Notch State Park', round(a1), 'same name'], ['wsa9', 'Red Notch Wilderness Study Area', 0, 'name']], lambda i: side.get(i))
check('two layers side by side are other ground: both are counted', got2 and near(got2[0], a1 + a2, 1))

# ---- a layer with no saved shape cannot be placed: added, as before
got3 = KR.measured_ac([['a', 'X', 120, 'name'], ['wsa9', 'Y', 0, 'name']], lambda i: side.get(i))
check('a layer with no saved shape is added as before', got3 and got3[0] == round(120 + a2))

# ---- no 0-acre row: one layer = nothing to measure (as before); two layers on the same ground = measured now, counted once
check('one layer and no 0-acre row: nothing to measure, as before', KR.measured_ac(rows[3:5], lambda i: shapes.get(i)) is None)
got4 = KR.measured_ac([rows[0], rows[2], rows[3], rows[4]], lambda i: shapes.get(i))
check('two layers on the same ground and no 0-acre row: measured now, and counted once', got4 and near(got4[0], LAND) and got4[1] == 0)
check('a 0-acre row with no shape: no acreage is made up', KR.measured_ac([rows[0], ['sgzzd9', 'Q', 0, 'name']], lambda i: shapes.get(i)) is None)

# ---- the size check, end to end: with the land counted once the agency's own figure agrees; with every row added up it is
# '4 times the figure' and every row goes to the check list.
SQ = lambda r: {'type': 'Polygon', 'coordinates': [r]}
TABLE = {'sgzza': {'agency': 'state wildlife', 'kind': 'wildlife area'}, 'sgzzd': {'agency': 'state wildlife', 'kind': 'wildlife area'},
         'zzo': {'agency': 'state wildlife', 'kind': 'wildlife area'}}
LINK = {'site': 'agency (known)', 'agency': 'ZZ DNR', 'page_kind': 'own page', 'usable': True, 'id_shared_by': 1, 'shared_by': 1,
        'web_name': 'unit 4471', 'name_match': 'none'}


def run(ac):
    recs = {str(r[0]): {'OBJECTID': r[0], 'Unit_Nm': r[1], 'Mang_Type': 'STAT', 'Mang_Name': 'SFW', 'GIS_Acres': r[2], '_g': SQ(shapes[str(r[0])][0]),
                        '_bb': [-89.60, 44.20, -89.56, 44.23]} for r in rows}
    parks = {'US-9001': {'n': 'Heron Marsh State Wildlife Area', 't': 'State Wildlife Area', 'g': 'official', 'c': [], 'm': [list(r) for r in rows],
                         'twin': ['zzo7'], 'ac': ac, 'ac_how': 'measured'}}
    f = {'US-9001': {'area': 'US-ZZ', 'name': 'Heron Marsh State Wildlife Area', 'type': 'State Wildlife Area', 'pin': [44.215, -89.58], 'link': dict(LINK),
                     'size': {'acres': round(LAND * 1.01), 'witness': 'agency_document'},
                     'page': {'kind': 'html', 'own_page': 'own', 'unofficial': False, 'host': 'dnr.zz.example.gov', 'name_vs_pota': 'differs', 'name_on_page': '',
                              'sizes': [], 'coords': [], 'parts': [], 'inside_of': []}}}
    MC.pass_state(parks, recs, f, lambda ref, ids: True, st='ZZ', holds_fn=lambda ref, i: True, layer_table=TABLE)
    p = parks['US-9001']
    return len(p.get('m') or []), [x[3] for x in p.get('c') or []], p.get('match') or {}


n, c, mt = run(got[0])
check('with the land counted once the size agrees: no row goes to the check list', n == len(rows) and not [w for w in c if 'size' in w])
check('and the agency\'s own figure confirms the park', mt.get('status') == 'confirmed' and mt.get('by') == 'size')
n, c, mt = run(round(everything))
check('with every row added up (the old number) the size check sends the rows to the check list', any(w.startswith('check (size:') for w in c))

src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
check("the US key hands the park's twins to the measure", "p.get('parts'), p.get('twin'))" in src)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
