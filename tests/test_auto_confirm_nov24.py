#!/usr/bin/env python3
"""24 Nov 2026 (owner 7:06 AM CT approved the auto-confirm rule, with both review additions):
status only, never changes land. The held record's name must match (spelling table or the shared
name key) and the pin must sit inside that record or within 100 m on the SAVED outline, not the
key's working copy. Invented parks only. No network. Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import pathlib, socket, sys, json, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))


def _no_net(*a, **k):
    raise RuntimeError('no network in tests')


socket.socket.connect = _no_net
import kpc_match_checks as MC  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


check('Camel\'s Hump and Camels Hump share a name key',
      MC.name_key("Camel's Hump") == MC.name_key('Camels Hump') == 'camelshump')
table = {'swa': 'statewildlifearea'}
# Apply table: park "Invented Marsh SWA" vs record "Invented Marsh State Wildlife Area"
check('the spelling table makes SWA match State Wildlife Area; without it they do not',
      MC.names_match('Invented Marsh SWA', 'Invented Marsh State Wildlife Area', table)
      and not MC.names_match('Invented Marsh SWA', 'Invented Marsh State Wildlife Area', None))

# A 0.05° square. Pin at the centre is inside; a pin 0.0005° (~55 m) east of the east edge is within 100 m;
# a pin 0.002° (~220 m) east is not.
# Square from lon -88.50 to -88.45, lat 44.50 to 44.55. East edge lon=-88.45.
SQ = {'type': 'Polygon', 'coordinates': [[[-88.50, 44.50], [-88.45, 44.50], [-88.45, 44.55], [-88.50, 44.55], [-88.50, 44.50]]]}
REC = {'OBJECTID': 'sgzza1', 'Unit_Nm': 'Invented Marsh State Wildlife Area', 'GIS_Acres': 500, '_g': SQ}
PIN_INSIDE = [44.525, -88.475]
# 100 m ≈ 0.0009° lon at this lat (k = cos(lat)*111.32 ≈ 79.4 km/deg; 0.1/79.4≈0.00126°)
# Place pin 0.0008° east of edge: ~63 m
PIN_NEAR = [44.525, -88.45 + 0.0008]
PIN_FAR = [44.525, -88.45 + 0.005]  # ~400 m

def park(pin_unused=None, name='Invented Marsh State Wildlife Area', hid='sgzza1', bk_km=99):
    # bk_km is a huge working-copy distance that must be IGNORED
    return {'n': name, 't': 'State Wildlife Area',
            'm': [[hid, name, 500, 'same name']],
            'bk': [hid, bk_km], 'g': 'official'}

recs = {'sgzza1': REC}
facts_inside = {'US-9001': {'name': 'Invented Marsh State Wildlife Area', 'pin': PIN_INSIDE}}
facts_near = {'US-9001': {'name': 'Invented Marsh State Wildlife Area', 'pin': PIN_NEAR}}
facts_far = {'US-9001': {'name': 'Invented Marsh State Wildlife Area', 'pin': PIN_FAR}}

check('confirms when the pin is inside the saved outline and the held name matches',
      MC.auto_confirm_ok('US-9001', park(), recs, facts_inside, holds_fn=lambda r, i: True))
check('confirms when the pin is within 100 m of the saved outline, even if the key\'s bk says it is far',
      MC.auto_confirm_ok('US-9001', park(bk_km=99), recs, facts_near, holds_fn=lambda r, i: False)
      and park()['bk'][1] == 99)
check('does not confirm when the pin is more than 100 m from the saved outline',
      not MC.auto_confirm_ok('US-9001', park(), recs, facts_far, holds_fn=lambda r, i: False))
check('does not confirm when the held name does not match',
      not MC.auto_confirm_ok('US-9001', park(name='Invented Pond Wildlife Area'), recs, facts_inside,
                             holds_fn=lambda r, i: True))
check('person-NO is a hard stop',
      not MC.auto_confirm_ok('US-9001', park(), recs, facts_inside, holds_fn=lambda r, i: True,
                             is_no=lambda ref, rid, a: True))
check('a blocked held id is a hard stop',
      not MC.auto_confirm_ok('US-9001', park(), recs, facts_inside, holds_fn=lambda r, i: True,
                             blocked={'US-9001': {'sgzza1'}}))
check('a park on the calls / land-wrong / pin-wrong stop list is a hard stop',
      not MC.auto_confirm_ok('US-9001', park(), recs, facts_inside, holds_fn=lambda r, i: True,
                             stop_parks={'US-9001'}))

# pass_state: status only, land unchanged
TABLE = {'sgzza': {'agency': 'state wildlife', 'kind': 'wildlife area'}}
LINK = {'site': 'agency (known)', 'agency': 'ZZ DNR', 'page_kind': 'own page', 'usable': True, 'id_shared_by': 1,
        'shared_by': 1, 'web_name': 'unit 4471', 'name_match': 'none'}

def run(holds, pin, stops=(), spelling=None, name='Invented Marsh State Wildlife Area'):
    parks = {'US-9001': park(name=name)}
    before_m = [list(x) for x in parks['US-9001']['m']]
    f = {'US-9001': {'area': 'US-ZZ', 'name': name, 'type': 'State Wildlife Area', 'pin': pin,
                     'link': dict(LINK),
                     'page': {'kind': 'html', 'own_page': 'own', 'unofficial': False, 'host': 'dnr.zz.example.gov',
                              'name_vs_pota': 'differs', 'name_on_page': '', 'sizes': [], 'coords': [], 'parts': [],
                              'inside_of': [], 'county_areas': []}}}
    MC.pass_state(parks, recs, f, lambda ref, ids: holds, st='ZZ',
                  holds_fn=lambda ref, i: holds, layer_table=TABLE,
                  auto_confirm_stops=set(stops), spelling_table=spelling or {})
    return parks['US-9001'], before_m

p, before = run(True, PIN_INSIDE)
check('pass_state confirms by held name and pin when the park would otherwise stay outlined',
      (p.get('match') or {}).get('status') == 'confirmed'
      and (p.get('match') or {}).get('by') == 'held name and pin')
check('the joined land is not changed', p.get('m') == before)
p, _ = run(False, PIN_FAR)
check('pass_state does not confirm when the pin is far from the saved outline',
      (p.get('match') or {}).get('status') == 'outlined')
p, before = run(True, PIN_INSIDE, stops={'US-9001'})
check('pass_state does not confirm a park on the stop list, and still does not change land',
      (p.get('match') or {}).get('status') == 'outlined' and p.get('m') == before)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
