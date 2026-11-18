#!/usr/bin/env python3
"""The fact check (Fable, 2026-11-18; .claude/notes/key-quality.md): the hard cases of 18 Nov as small made-up squares.
Each case is a real mistake or a real false alarm: Mt Etna on the whole lake property, three Nebraska parks on one county
record, a trail on the state park's record, Badoura (row numbers moved, the key re-found it: must stay clean), the refuge
whose 'official' size belonged to the refuge next door, a pin far away, a clean code join."""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_key_factcheck as FC

bad = 0
def ck(c, m):
    global bad; bad += not c; print(('PASS ' if c else 'FAIL ') + m)

def sq(lon, lat, side_km):
    d = side_km / 111.0
    return [[[lon, lat], [lon + d, lat], [lon + d, lat + d], [lon, lat + d], [lon, lat]]]

def rec(i, name, lon, lat, side, acres, **k):
    r = {'OBJECTID': i, 'Unit_Nm': name, 'Loc_Nm': '', 'Mang_Name': k.get('mang', 'STAT'), 'Des_Tp': k.get('des', ''), 'GIS_Acres': acres, '_r': sq(lon, lat, side)}
    return r

RECS = [
    rec('ind5037', 'Salamonie Lake', -85.70, 40.80, 6.6, 10768),
    rec('fwsc1', 'Clay County Waterfowl Production Area', -98.10, 40.50, 5.3, 7011, mang='FWS'),
    rec(3432, 'First Landing State Park', -76.05, 36.90, 3.4, 2888, des='SP'),
    rec('sgmnb10', 'Badoura', -94.70, 46.90, 7.9, 15429),              # the layer renumbered: Badoura moved from 56 to 10
    rec('sgmnb56', 'Pillsbury', -94.40, 46.40, 8.0, 15800),            # row 56 is another forest now
    rec('sgmnf4080', 'Badoura', -94.70, 46.90, 7.8, 15100),
    rec(51575, 'Upper Mississippi River National Wildlife And Fish Refuge', -91.20, 43.50, 14.4, 51575, mang='FWS', des='NWR'),
    rec(700, 'Lonesome Ridge', -105.00, 40.00, 2.0, 988),
    rec(900, 'Big Cedar National Monument', -110.00, 38.00, 6.4, 10000, mang='NPS', des='NM'),
]
BY = {str(r['OBJECTID']): r for r in RECS}
KEY = {'read': '2026-11-17', 'parks': {
    'US-4179': {'n': 'Mt Etna on Salamonie Lake State Recreation Area', 'g': 'approximate', 'm': [['ind5037', 'Salamonie Lake', 10768, 'reviewed-approx']]},
    'US-4177': {'n': 'Dora-New Holland on Salamonie Lake State Recreation Area', 'g': 'approximate', 'm': [['ind5037', 'Salamonie Lake', 10768, 'reviewed-approx']]},
    'US-3486': {'n': 'Moger National Waterfowl Production Area', 'g': 'approximate', 'm': [['fwsc1', 'Clay County Waterfowl Production Area', 7011, 'reviewed-approx']]},
    'US-3489': {'n': 'Massie National Waterfowl Production Area', 'g': 'approximate', 'm': [['fwsc1', 'Clay County Waterfowl Production Area', 7011, 'reviewed-approx']]},
    'US-1299': {'n': 'First Landing State Park', 'g': 'official', 'ac': 2888, 'm': [[3432, 'First Landing State Park', 2888, 'name']]},
    'US-9907': {'n': 'First Landing National Recreation Trail', 'g': 'approximate', 'm': [[3432, 'First Landing State Park', 2888, 'reviewed-approx']]},
    'US-4780': {'n': 'Badoura State Forest', 'g': 'official', 'm': [['sgmnb56', 'Badoura', 15429, 'reviewed'], ['sgmnf4080', 'Badoura', 15100, 'name']]},
    'US-4236': {'n': 'Upper Mississippi River National Wildlife Refuge', 'g': 'official', 'ac': 51575, 'm': [[51575, 'Upper Mississippi River National Wildlife And Fish Refuge', 51575, 'reviewed']]},
    'US-7000': {'n': 'Lonesome Ridge State Wildlife Area', 'g': 'official', 'm': [[700, 'Lonesome Ridge', 988, 'name']]},
    'US-0900': {'n': 'Big Cedar National Monument', 'g': 'official', 'ac': 10000, 'm': [[900, 'Big Cedar National Monument', 10000, 'NPS unit code']]},
    'US-0001': {'n': 'No Outline State Park', 'g': 'pin', 'm': []},
}}
def pi(name, lat, lon, act=10, web='', typ=''):
    return [name, web, typ, '', '', lat, lon, act, 0, 0]
PINFO = {
    'US-4179': pi('Mt Etna on Salamonie Lake State Recreation Area', 40.83, -85.67), 'US-4177': pi('Dora-New Holland on Salamonie Lake State Recreation Area', 40.82, -85.66),
    'US-3486': pi('Moger National Waterfowl Production Area', 40.52, -98.08), 'US-3489': pi('Massie National Waterfowl Production Area', 40.53, -98.07),
    'US-1299': pi('First Landing State Park', 36.915, -76.035), 'US-9907': pi('First Landing National Recreation Trail', 36.916, -76.036),
    'US-4780': pi('Badoura State Forest', 46.93, -94.67), 'US-4236': pi('Upper Mississippi River National Wildlife Refuge', 43.55, -91.15),
    'US-7000': pi('Lonesome Ridge State Wildlife Area', 40.50, -105.00), 'US-0900': pi('Big Cedar National Monument', 38.02, -109.98),
    'US-0001': pi('No Outline State Park', 40.0, -100.0)}
TRUTH = {
    'US-4236': {'official': {'acres': 1238.0, 'clean': True, 'sent': 'The refuge encompasses 1,238 acres of the Driftless Area in Iowa',
                             'line': 'Trempealeau, WI Driftless Area National Wildlife Refuge The refuge encompasses 1,238 acres of the Driftless Area in Iowa', 'url': 'https://x.gov/a'}},
    'US-1299': {'official': {'acres': 2888.0, 'clean': True, 'sent': 'First Landing State Park covers 2,888 acres.', 'line': '', 'url': 'https://x.gov/b'}},
    'US-9907': {'official': {'acres': 12.0, 'clean': True, 'sent': 'The First Landing trail corridor is 12 acres.', 'line': '', 'url': 'https://x.gov/c'}},
}
doc = FC.check_area('US-XX', KEY, BY, PINFO, TRUTH, agency={}, today='2026-11-18')
P = doc['parks']
fl = lambda r: {f[0] for f in P[r].get('flags') or []}

ck(P['US-4179']['class'] == 'flagged' and 'SHARED' in fl('US-4179') and 'SHARED' in fl('US-4177'), 'Mt Etna: one lake record on two parks that fit it equally = SHARED on both')
ck('SHARED' in fl('US-3486') and 'SHARED' in fl('US-3489'), 'Nebraska: one county record on two parks = SHARED on both')
ck(not fl('US-1299') and P['US-1299']['class'] == 'verified' and set(P['US-1299']['witnesses']) >= {'pin', 'size', 'name', 'designation'},
   f"First Landing State Park: its own record, pin inside, size agrees = verified, and NOT flagged for the trail's mistake ({P['US-1299']})")
ck({'SHARED', 'OTHER_PARK', 'SIZE_BIG', 'BIG_PIECE'} <= fl('US-9907'), f"the trail on the state park's record: SHARED + OTHER_PARK + SIZE_BIG + BIG_PIECE ({fl('US-9907')})")
b = P['US-4780']
ck(not b['flags'] and b['not_in_read'] == 0 and b['m'][0][4].startswith('found again') and 'pin' in b['witnesses'] and 'name' in b['witnesses'],
   f"Badoura: the saved id now sits on Pillsbury; the row is found again by layer + name + acres and the park is CLEAN ({b['m'][0]}, {b['flags']})")
ck('second layer' in b['witnesses'], 'Badoura: two layers show the same land under the same name = the second-layer witness')
u = P['US-4236']
ck(u['acres']['official_is'] == 'weak' and fl('US-4236') == {'SIZE_WEAK'} and u['class'] != 'flagged',
   f"US-4236: the 'official' 1,238 acres sits beside another refuge's name = weak, a soft flag only, never 'flagged' ({u['acres']}, {u['flags']})")
ck('PIN_FAR' in fl('US-7000') and P['US-7000']['class'] == 'flagged', f"a pin 50 km from the only piece = PIN_FAR ({P['US-7000'].get('pin_km')})")
ck(P['US-0900']['class'] == 'verified' and 'code' in P['US-0900']['witnesses'], 'a unit-code join is verified without the name')
ck(P['US-0001']['class'] == 'pin' and not P['US-0001'].get('flags'), 'a park with no outline is pin: honest, no flag')
# shapes
r = FC.rings_of({'_r': sq(0, 0, 1.11)})
ck(FC.inside(0.005, 0.005, r) and not FC.inside(0.5, 0.5, r), 'inside: a point in the square, a point outside it')
ck(abs(FC.edge_km(0.005, 0.02, r) - 1.11) < 0.05, f'edge_km measures to the EDGE between corners, not to the nearest corner ({FC.edge_km(0.005, 0.02, r):.2f} km)')
ck(abs(FC.ring_acres(r) - 1.11 * 1.11 * 247.105) / (1.11 * 1.11 * 247.105) < 0.02, 'ring_acres: a 1.11 km square')
ck(FC.name_fit('Black Canyon State Wildlife Area', ['Black Canyon WMA']) == 'exact' and FC.name_fit('Mt Etna on Salamonie Lake State Recreation Area', ['Salamonie Lake']) == 'part'
   and FC.name_fit('Ramah State Wildlife Area', ['Ralston Creek SWA']) == '', 'name_fit: exact / part / none')
NAMES = [("Creamer's Field Wildlife Refuge", "Creamer's Field", 'exact'), ('Whaleback Shell Midden State Historic Site', 'Whaleback Shell Midden', 'exact'),
         ('PA 144 State Game Land', 'State Game Land 144', 'exact'), ('PA 144 State Game Land', 'State Game Land 145', ''),
         ('Prairie River State Fish and Wildlife Area', 'Prairie River Fishery Area', 'exact'), ('Mount Carmel State Forest', 'Mt. Carmel State Forest', 'exact'),
         ('Patriots Park State Historic Site', 'Patriot Park', 'exact'), ('Cutoff Creek State Natural Area', 'Cut-off Creek', 'exact'),
         ('Halpata Tatanaki Preserve State Conservation Area', 'Halpata Tastanaki Preserve', 'exact'), ('McKee-Breshers Wildlife Management Area', 'Mckee Beshers Wma', 'exact'),
         ('Massie National Waterfowl Production Area', 'Clay County Waterfowl Production Area Of Ne', ''), ('Tuttle Creek Willow State Fishing Lake', 'Tuttle Creek State Parks', 'part'),
         ('De Leon Springs State Park', 'Ponce de Leon Springs State Park', 'part'), ('Prairie Lake State Recreation Area', 'Prairie River', ''),
         ('Rio Grande del Norte National Monument', 'Río Grande del Norte National Monument', 'exact')]
wrong = [(a, b, FC.name_fit(a, [b]), w) for a, b, w in NAMES if FC.name_fit(a, [b]) != w]
ck(not wrong, f'name_fit on 15 real pairs: kind words, short forms, a state code, a plural and a slip of the pen do not matter; another place does ({wrong})')
ck(FC.size_strength('Hobbs State Park', {'acres': 12055, 'clean': True, 'sent': 'The area is 12,055 acres in size.', 'line': ''}) == 'strong'
   and FC.size_strength('X', {'acres': 5, 'clean': False}) == 'unclean' and FC.size_strength('X', None) is None, 'size_strength: strong / unclean / none')
src = (ROOT / '.github' / 'scripts' / 'kpc_key_factcheck.py').read_text(encoding='utf-8')
ck('overrides' not in src.replace('kpc_key_rules', ''), 'the fact check never reads the saved answers (no answer sheet at all)')
import kpc_key_freeze as KF
ck('kpc_key_factcheck.py' in KF.NOT_RULES and not any('kpc_key_factcheck.py' in f for fs in KF.RULE_FILES.values() for f in fs), 'the fact check is not a rule file (it joins nothing)')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
