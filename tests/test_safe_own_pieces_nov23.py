#!/usr/bin/env python3
"""23 Nov 2026, owner 2:55 PM: 'Go ahead with the safer version' (rule W8b, from the outside agent's accuracy test of W8).
W8 let the place test ('pin 3c') leave a record alone on its NAME only: a water body, a road or a business named like the park,
a same-name area of another county and another owner's piece stayed with the park. W8b keeps a same-name piece only when the
name (the exact name or another spelling / short form, plus at most a unit / county / section ending), the owner (the same
agency or owner type as the park) and the place (it touches or lies within 500 m of the park's other joined land) all agree;
plus one narrow case for a POTA name that covers two units. Invented names only; no connection is opened.
Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import pathlib, socket, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))


def _no_net(*a, **k): raise RuntimeError('no network in tests')
socket.socket.connect = _no_net
import kpc_match_checks as MC  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


YES, NO = (lambda q: True), (lambda q: False)


def flag(rec, park, held=None, owner=YES, near=YES, counties=()):
    """pin 3c on one record: row 1 holds the pin (named held, else the park), row 2 is the record under test."""
    rows = [['1', held or park, 900, 'name'], ['2', rec, 120, 'name']]
    return MC.pin_3c(rows[1], rows, lambda i: i == '1', park, same_owner=owner, near_land=near, counties=counties)


# false keeps of W8 that now go to the check list (W8 kept every one of these on its name)
SENT = [
    ('a water body with the park name', 'Otter Bend State Park - Fresh Pond', 'Otter Bend State Park', {}),
    ('a lake as a piece label', 'Birch Hollow State Forest - Mirror Lake', 'Birch Hollow State Forest', {}),
    ('a road as a piece label', 'Birch Hollow State Forest - Ridge Drive', 'Birch Hollow State Forest', {}),
    ('a resort / business', 'Maple Knob State Park - Lodge Resort', 'Maple Knob State Park', {}),
    ('a house of another owner', 'Maple Knob State Park - Test House', 'Maple Knob State Park', {}),
    ('the same name in another county, far off', 'Heron Run Fishery Area-Polk', 'Heron Run State Fish and Wildlife Area',
     {'near': NO, 'counties': {'polk'}}),
    ('a piece of another owner', 'Pine Hollow State Forest - Lucas Tract', 'Pine Hollow State Forest', {'owner': NO}),
    ('a piece with no owner data', 'Pine Hollow State Forest - Lucas Tract', 'Pine Hollow State Forest', {'owner': lambda q: None}),
    ('a far piece (over 500 m from the other land)', 'Pine Hollow State Forest - Lucas Tract', 'Pine Hollow State Forest', {'near': NO}),
    ('a piece with no shape to measure', 'Pine Hollow State Forest - Lucas Tract', 'Pine Hollow State Forest', {'near': lambda q: None}),
    ('a two-word label that is not a unit or a county', 'Cedar Gap WMA - Fall Creek', 'Cedar Gap Wildlife Management Area', {}),
]
for why, rec, park, kw in SENT:
    check(f'W8 alone kept it: "{rec}" for "{park}"', MC.own_piece(rec, park))
    check(f'W8b sends {why} to the check list: "{rec}"', flag(rec, park, **kw) is True)

# D+: the park's own pieces still stay (name, owner and place agree)
KEPT = [
    ('a tract', 'Pine Hollow State Forest - Lucas Tract', 'Pine Hollow State Forest', {}),
    ('a named section', 'Pine Hollow State Forest - Bower Section', 'Pine Hollow State Forest', {}),
    ('an addition', 'Granite Bluff State Natural Area - Laurel Addition', 'Granite Bluff State Natural Area', {}),
    ('a county ending', 'Heron Run Fishery Area-Polk', 'Heron Run State Fish and Wildlife Area', {'counties': {'polk'}}),
    ('a short form', 'Cedar Gap SHP', 'Cedar Gap State Historical Park', {}),
    ('another spelling', 'Silver Fern Test CA', 'Silver Fern Test State Conservation Area', {}),
    ('a unit with no separator', 'Quail Test WMA Unit 2', 'Quail Test Wildlife Management Area', {}),
]
for why, rec, park, kw in KEPT:
    check(f'W8b keeps {why}: "{rec}" for "{park}"', flag(rec, park, **kw) is False)
check('W8b: another kind of place named for a lake (the short-form path) goes to check',
      flag('Birch Hollow State Recreation Area (Otter Lake)', 'Birch Hollow State Forest') is True)
check('W8b: a lake park keeps its own lake piece', flag('Clear Test Lake State Park - Lucas Tract', 'Clear Test Lake State Park') is False)
check('W8b: a county ending that is not one of the state\'s counties goes to check',
      flag('Heron Run Fishery Area-Smallville', 'Heron Run State Fish and Wildlife Area', counties={'polk'}) is True)

# E: a POTA name that covers two units
for pk in ('Red Fox Hills Blue Heron State Forest', 'Red Fox Hills and Blue Heron State Forest', 'Red Fox Hills & Blue Heron State Forest',
           'Red Fox Hills - Blue Heron State Forest', 'Red Fox Hills/Blue Heron State Forest'):
    check(f'E keeps the one half when the pin record is the other half (far is fine): "{pk}"',
          flag('Red Fox Hills State Forest', pk, held='Blue Heron State Forest', near=NO) is False)
pk = 'Red Fox Hills Blue Heron State Forest'
check('E: another owner goes to check', flag('Red Fox Hills State Forest', pk, held='Blue Heron State Forest', owner=NO, near=NO) is True)
check('E: the pin record does not name the other half: check', flag('Red Fox Hills State Forest', pk, held='Otter Bend State Forest', near=NO) is True)
check('E: another kind of place: check', flag('Red Fox Hills Wildlife Area', pk, held='Blue Heron State Forest', near=NO) is True)
check('E: a longer name that only holds a half: check', flag('Red Fox Hills Lake State Forest', pk, held='Blue Heron State Forest', near=NO) is True)
check('two_unit_half needs the half to be exact', not MC.two_unit_half('Red Fox State Forest', pk, ['Blue Heron State Forest']))

# unchanged: a record holding the pin and a same-bare name stay without any owner or place data
check('the 22 Nov rule still keeps the same bare name with no data', flag('Pine Hollow State Forest Addition', 'Pine Hollow State Forest', owner=None, near=None) is False)
check('a river named like the park still goes to check', flag('Pine Hollow River', 'Pine Hollow State Forest') is True)

# the place test's shape check
A = [[[-80.0, 40.0], [-79.99, 40.0], [-79.99, 40.01], [-80.0, 40.01], [-80.0, 40.0]]]
touch = [[[-79.99, 40.0], [-79.98, 40.0], [-79.98, 40.01], [-79.99, 40.01], [-79.99, 40.0]]]
m300 = [[[-79.9865, 40.0], [-79.98, 40.0], [-79.98, 40.01], [-79.9865, 40.01], [-79.9865, 40.0]]]   # ~300 m east
km2 = [[[-79.966, 40.0], [-79.96, 40.0], [-79.96, 40.01], [-79.966, 40.01], [-79.966, 40.0]]]       # ~2 km east
check('rings_near: touching shapes are near', MC.rings_near(A, touch) is True)
check('rings_near: 300 m apart is near', MC.rings_near(A, m300) is True)
check('rings_near: 2 km apart is not near', MC.rings_near(A, km2) is False)
check('rings_near: no shape is no data', MC.rings_near(A, []) is None)
check('feature_of reads a pond, a drive and a resort, not a creek addition',
      MC.feature_of('X - Fresh Pond') == 'water' and MC.feature_of('X - Ridge Drive') == 'road' and MC.feature_of('X Resort') == 'business'
      and MC.feature_of('X - Hurricane Creek Addition') is None)

# the whole pass: the builder hands near_fn; the owner comes from the park's link
SQ = [[[-80.0, 40.0], [-79.99, 40.0], [-79.99, 40.01], [-80.0, 40.01], [-80.0, 40.0]]]
recs = {'1': {'OBJECTID': '1', 'Unit_Nm': 'Pine Hollow State Forest', 'Mang_Type': 'STAT', 'GIS_Acres': 900, '_r': SQ},
        '2': {'OBJECTID': '2', 'Unit_Nm': 'Pine Hollow State Forest - Lucas Tract', 'Mang_Type': 'STAT', 'GIS_Acres': 100, '_r': touch},
        '3': {'OBJECTID': '3', 'Unit_Nm': 'Pine Hollow State Forest - Bower Tract', 'Mang_Type': 'STAT', 'GIS_Acres': 100, '_r': km2},
        '4': {'OBJECTID': '4', 'Unit_Nm': 'Pine Hollow State Forest - Miller Tract', 'Mang_Type': 'LOC', 'GIS_Acres': 100, '_r': touch}}
rows = [[k, recs[k]['Unit_Nm'], recs[k]['GIS_Acres'], 'name'] for k in '1234']
parks = {'US-9001': {'n': 'Pine Hollow State Forest', 't': 'State Forest', 'm': [list(r) for r in rows], 'c': [], 'g': 'official'}}
facts = {'US-9001': {'area': 'US-ZZ', 'name': 'Pine Hollow State Forest', 'type': 'State Forest', 'pin': [40.005, -79.995],
                     'link': {'site': 'agency (known)', 'agency': 'ZZ Dept of Forests', 'page_kind': 'own page'}}}
near = lambda ref, i, ids: MC.rings_near(recs[i]['_r'], [r for j in ids for r in recs[j]['_r']])
MC.pass_state(parks, recs, facts, lambda ref, ids: True, st='ZZ', units={}, holds_fn=lambda ref, i: i == '1', near_fn=near)
kept = sorted(str(q[0]) for q in parks['US-9001']['m'])
checked = sorted(str(q[0]) for q in parks['US-9001']['c'])
check(f'pass: the touching state piece stays, the far piece and the local piece go to check (kept {kept}, check {checked})',
      '1' in kept and '2' in kept and '3' in checked and '4' in checked)
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
check("the builder hands its shapes to the place test (near_fn)", 'page_holds_fn=_page_holds, near_fn=_near)' in src)
src = (ROOT / '.github/scripts/kpc_match_checks_count.py').read_text(encoding='utf-8')
check("the offline counter hands its shapes to the place test (near_fn)", 'near_fn=near)' in src)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
