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

EMPTY = set()   # a readable stop list with no IDs (not fail-closed)

check('confirms when the pin is inside the saved outline and the held name matches',
      MC.auto_confirm_ok('US-9001', park(), recs, facts_inside, holds_fn=lambda r, i: True, stop_parks=EMPTY))
check('confirms when the pin is within 100 m of the saved outline, even if the key\'s bk says it is far',
      MC.auto_confirm_ok('US-9001', park(bk_km=99), recs, facts_near, holds_fn=lambda r, i: False, stop_parks=EMPTY)
      and park()['bk'][1] == 99)
check('does not confirm when the pin is more than 100 m from the saved outline',
      not MC.auto_confirm_ok('US-9001', park(), recs, facts_far, holds_fn=lambda r, i: False, stop_parks=EMPTY))
check('does not confirm when the held name does not match',
      not MC.auto_confirm_ok('US-9001', park(name='Invented Pond Wildlife Area'), recs, facts_inside,
                             holds_fn=lambda r, i: True, stop_parks=EMPTY))
check('person-NO is a hard stop',
      not MC.auto_confirm_ok('US-9001', park(), recs, facts_inside, holds_fn=lambda r, i: True,
                             is_no=lambda ref, rid, a: True, stop_parks=EMPTY))
check('a blocked held id is a hard stop',
      not MC.auto_confirm_ok('US-9001', park(), recs, facts_inside, holds_fn=lambda r, i: True,
                             blocked={'US-9001': {'sgzza1'}}, stop_parks=EMPTY))
check('a park on the calls / land-wrong / pin-wrong stop list is a hard stop',
      not MC.auto_confirm_ok('US-9001', park(), recs, facts_inside, holds_fn=lambda r, i: True,
                             stop_parks={'US-9001'}))

# 24 Nov repair: missing / unreadable stop list = confirm nothing (fail closed)
check('no stop list passed (None) confirms nothing',
      not MC.auto_confirm_ok('US-9001', park(), recs, facts_inside, holds_fn=lambda r, i: True))

# pass_state: status only, land unchanged
TABLE = {'sgzza': {'agency': 'state wildlife', 'kind': 'wildlife area'}}
LINK = {'site': 'agency (known)', 'agency': 'ZZ DNR', 'page_kind': 'own page', 'usable': True, 'id_shared_by': 1,
        'shared_by': 1, 'web_name': 'unit 4471', 'name_match': 'none'}


def fresh_park(name='Invented Marsh State Wildlife Area', hid='sgzza1', rows=None):
    """A pass_state park: no held, no bk (a fresh US build does not copy them onto the park dict)."""
    return {'n': name, 't': 'State Wildlife Area',
            'm': rows if rows is not None else [[hid, name, 500, 'same name']],
            'g': 'official'}


def run(holds, pin, stops=(), spelling=None, name='Invented Marsh State Wildlife Area', park_fn=fresh_park, **pkw):
    parks = {'US-9001': park_fn(name=name, **pkw)}
    before_m = [list(x) for x in parks['US-9001']['m']]
    f = {'US-9001': {'area': 'US-ZZ', 'name': name, 'type': 'State Wildlife Area', 'pin': pin,
                     'link': dict(LINK),
                     'page': {'kind': 'html', 'own_page': 'own', 'unofficial': False, 'host': 'dnr.zz.example.gov',
                              'name_vs_pota': 'differs', 'name_on_page': '', 'sizes': [], 'coords': [], 'parts': [],
                              'inside_of': [], 'county_areas': []}}}
    MC.pass_state(parks, recs, f, lambda ref, ids: holds, st='ZZ',
                  holds_fn=lambda ref, i: holds, layer_table=TABLE,
                  auto_confirm_stops=set(stops) if stops is not None else None, spelling_table=spelling or {})
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

# ---- 24 Nov repair: held id at pass_state, stop list loaded, no nearest fallback ----
p, before = run(True, PIN_INSIDE)   # fresh_park has no bk / held
check('held id is found at pass_state with no bk and no held (builder holds, pin inside)',
      (p.get('match') or {}).get('status') == 'confirmed'
      and (p.get('match') or {}).get('by') == 'held name and pin'
      and 'bk' not in p and 'held' not in p
      and p.get('m') == before)

p, _ = run(None, PIN_INSIDE)   # builder has no answer; saved outline contains the pin
check('no builder answer, pin inside the saved outline: confirms (0 m, not the edge distance)',
      (p.get('match') or {}).get('status') == 'confirmed'
      and (p.get('match') or {}).get('by') == 'held name and pin')

p, _ = run(False, PIN_NEAR)   # builder says not inside; unique outline within 100 m
check('builder does not hold, pin within 100 m of the only saved outline: confirms',
      (p.get('match') or {}).get('status') == 'confirmed'
      and (p.get('match') or {}).get('by') == 'held name and pin')

p, _ = run(False, PIN_FAR)
check('neither the builder nor a saved outline within 100 m: no confirm',
      (p.get('match') or {}).get('status') == 'outlined')

# Two joined outlines, pin inside neither, both within 100 m: do not pick the nearer sliver
SQ2 = {'type': 'Polygon', 'coordinates': [[[-88.4488, 44.524], [-88.4483, 44.524], [-88.4483, 44.526], [-88.4488, 44.526], [-88.4488, 44.524]]]}  # ~30–70 m east of PIN_NEAR, not containing it
recs_two = dict(recs, sgzza2={'OBJECTID': 'sgzza2', 'Unit_Nm': 'Invented Marsh State Wildlife Area', 'GIS_Acres': 2, '_g': SQ2})
# PIN_NEAR is ~63 m east of the big square's east edge -88.45; the sliver sits around -88.4492, also near that pin.

def run_two(pin, holds=False):
    name = 'Invented Marsh State Wildlife Area'
    parks = {'US-9001': fresh_park(name=name, rows=[['sgzza1', name, 500, 'same name'], ['sgzza2', name, 2, 'same name']])}
    before_m = [list(x) for x in parks['US-9001']['m']]
    f = {'US-9001': {'area': 'US-ZZ', 'name': name, 'type': 'State Wildlife Area', 'pin': pin,
                     'link': dict(LINK),
                     'page': {'kind': 'html', 'own_page': 'own', 'unofficial': False, 'host': 'dnr.zz.example.gov',
                              'name_vs_pota': 'differs', 'name_on_page': '', 'sizes': [], 'coords': [], 'parts': [],
                              'inside_of': [], 'county_areas': []}}}
    MC.pass_state(parks, recs_two, f, lambda ref, ids: holds, st='ZZ',
                  holds_fn=lambda ref, i: holds, layer_table=TABLE,
                  auto_confirm_stops=EMPTY, spelling_table={})
    return parks['US-9001'], before_m

p, before = run_two(PIN_NEAR)
check('two saved outlines within 100 m and the pin inside neither: no confirm (no nearest-record fallback)',
      (p.get('match') or {}).get('status') == 'outlined' and p.get('m') == before)

# default loader: the shipped file is IDs only and is read
stops, found = MC.load_auto_confirm_stops()
check('the shipped stop list is loaded (IDs only, 1,278 parks)',
      found is not None and isinstance(stops, set) and len(stops) == 1278
      and all(isinstance(x, str) and (x.startswith('US-') or x.startswith('CA-')) for x in stops))
check('a missing stop list is fail-closed (None, not an empty set)',
      MC.load_auto_confirm_stops(paths=['/tmp/kpc-invented-no-such-stops.json'], root='/tmp') == (None, None))
# unreadable file
bad = pathlib.Path(tempfile.mkdtemp()) / 'auto-confirm-stops.json'
bad.write_text('{not json', encoding='utf-8')
check('an unreadable stop list is fail-closed',
      MC.load_auto_confirm_stops(paths=[str(bad)], root='/tmp') == (None, None))

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
