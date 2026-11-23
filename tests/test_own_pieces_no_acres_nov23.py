#!/usr/bin/env python3
"""23 Nov 2026, owner 8:45 AM: 'Go' (rules W8 and W9, from the outside agent's counts, jobs 4 and 6).
W8: the place test ('pin 3c') sent the park's OWN pieces to the check list when a piece is named the park's name plus a short
label ('Bullard Creek WMA - Montgomery Tract', 'Sand Creek Fishery Area-Polk', 'Cooper Lake State Park - Johns Creek Unit'),
or carries one part of a two-part park name ('Northern Highland State Forest' for the Northern Highland American Legion State
Forest). Those stay now; a river, lake or road named like the park, another kind of place and a longer name that holds the
park's still go to the check list.
W9: after the union the builder caps a park's acreage at its records' own acres added up; a record with no acres on file
(0 or blank) added 0, so 10 Maryland parks shrank to a few small pieces and fell to a pin. It now adds its own measured area.
Invented names in the shapes of the real ones; no connection is opened. Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import pathlib, socket, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))


def _no_net(*a, **k): raise RuntimeError('no network in tests')
socket.socket.connect = _no_net
import kpc_match_checks as MC  # noqa: E402
import kpc_key_rules as KR  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


KEEP = [('Heron Bend WMA - Montgomery Tract', 'Heron Bend Wildlife Management Area'),
        ('Otter Run Fishery Area-Polk', 'Otter Run State Fish and Wildlife Area'),
        ('Cedar Knob Lake State Park - Johns Creek Unit', 'Cedar Knob Lake State Park'),
        ("Quail Hollow WMA-UNIT 1- Dyer's Creek", 'Quail Hollow Wildlife Management Area'),
        ('Pine Barrens Test State Forest - Toppings Path', 'Pine Barrens Test State Forest'),
        ('Red Fox Hills State Forest', 'Red Fox Hills Blue Heron State Forest'),
        ('Elk Meadow State Park', 'Elk Meadow Coral Reef State Park'),
        ('Stone Hollow State Wildlife Area', 'Mill Creek and Stone Hollow State Wildlife Area')]
SEND = [('Crow Wing River', 'Crow Wing State Park'), ('Somerville Lake', 'Lake Somerville State Park'),
        ('Winberry - Fall Creek', 'Fall Creek State Recreation Area'), ('Big Creek Lake', 'Big Creek State Park'),
        ('Frances Test State Recreation Area (Lake X)', 'Frances Test State Forest'), ('Fort Test Parade Grounds', 'Fort Test State Park'),
        ('Savanna Portage', 'Savanna State Forest'), ('Yachats Ocean Road', 'Yachats State Recreation Area'),
        ('Miami Test State Fishing Lake And Wildlife Area', 'Miami Test State Fishing Lake'),
        ('Heron Bend WMA - Moose Lake State Park Overflow Lot Road Access', 'Moose Lake State Park'),
        ('Ash Grove State Forest', 'Ash Grove Wildlife Management Area')]
for rec, park in KEEP:
    check(f'W8 keeps the park\'s own piece: "{rec}" for "{park}"', MC.own_piece(rec, park))
for rec, park in SEND:
    check(f'W8 still sends another place to the check list: "{rec}" for "{park}"', not MC.own_piece(rec, park))

# pin 3c itself: the pin is in the park's main record; the piece with a piece's label stays, the river goes to the check list
rows = [['1', 'Heron Bend Wildlife Management Area', 900, 'name'], ['2', 'Heron Bend WMA - Montgomery Tract', 120, 'name'],
        ['3', 'Heron Bend River', 40, 'name']]
holds = lambda i: i == '1'
check('pin 3c keeps the tract of the park', MC.pin_3c(rows[1], rows, holds, 'Heron Bend Wildlife Management Area') is False)
check('pin 3c still flags a river named like the park', MC.pin_3c(rows[2], rows, holds, 'Heron Bend Wildlife Management Area') is True)

# W9: what one record adds to the cap after the union
check('W9: a record with acres on file adds its acres', KR.cap_acres(120, 999) == 120)
check('W9: a record with 0 acres on file adds its own measured area, not 0', KR.cap_acres(0, 850.5) == 850.5)
check('W9: a blank or broken acres field is measured too', KR.cap_acres(None, 40) == 40 and KR.cap_acres('n/a', 40) == 40)
check('W9: no acres and no shape adds 0', KR.cap_acres(0, None) == 0)
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
check("W9: the builder's cap after the union counts each record through cap_acres with its measured area",
      'KR.cap_acres(x[2], area_of.get(str(x[0])))' in src and 'area_of[i] = g.area / 4046.86' in src)
check('W9: the old cap (a 0-acre record adds 0) is gone', "_sum = sum(float(x[2] or 0) for x in p['m'] if str(x[0]) in ids or x[0] in ids)" not in src)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
