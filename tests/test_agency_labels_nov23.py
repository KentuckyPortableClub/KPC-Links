#!/usr/bin/env python3
"""23 Nov 2026, owner 6:42 AM: 'Yes on all but 5' (rulings W-G11 and W-G12, asked in plain words at 6:37 AM).
W-G11: the agency check read one label of a land record, its manager. In Oregon 111 pieces of state park land carry the
manager label CITY while the same record says the STATE owns it; every one went to the check list as 'another agency'. A state
link now agrees with a national-list record the state owns, whatever the manager label says.
W-G12: many state parks sit on lake land the Corps of Engineers, Reclamation or TVA owns. A state link against such a record
gives NO agency vote when the record carries the park's own name; the lake project's own record ('Otter Lake') and any
other name still go to the check list. Invented parks and records; no connection is opened."""
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


TABLE = {'sgzzc': {'agency': 'USACE', 'kind': 'recreation area'}}
LINK = {'site': 'agency (known)', 'agency': 'ZZ State Parks', 'page_kind': 'own page', 'usable': True, 'id_shared_by': 1, 'shared_by': 1,
        'web_name': 'unit 4471', 'name_match': 'none'}
PARK = 'Otter Lake State Park'
fact = lambda agency='ZZ State Parks': {'area': 'US-ZZ', 'name': PARK, 'type': 'State Park', 'pin': [44.5, -88.5], 'link': dict(LINK, agency=agency),
                                         'page': {'kind': 'html', 'own_page': 'own', 'unofficial': False, 'host': 'parks.zz.example.gov', 'name_vs_pota': 'differs',
                                                  'name_on_page': '', 'sizes': [], 'coords': [], 'parts': [], 'inside_of': []}}
rec = lambda oid, name, mn, mt, own='': {'OBJECTID': oid, 'Unit_Nm': name, 'Mang_Name': mn, 'Mang_Type': mt, 'Own_Type': own, 'GIS_Acres': 500,
                                         '_g': {'type': 'Polygon', 'coordinates': [[[-88.52, 44.48], [-88.47, 44.48], [-88.47, 44.53], [-88.52, 44.53], [-88.52, 44.48]]]},
                                         '_bb': [-88.52, 44.48, -88.47, 44.53]}
ac = lambda r, agency='ZZ State Parks': MC.agency_check(fact(agency), r, 'ZZ', TABLE)

# ---- W-G11: the owner label
check('has the two rulings', hasattr(MC, 'owner_family') and hasattr(MC, 'same_park_name'))
check('W-G11: state park land the STATE owns, with the manager label CITY, agrees with the state link', ac(rec(4401, PARK, 'CITY', 'LOC', 'STAT')) == 'agrees')
check('W-G11: state-owned land run by a private operator agrees too', ac(rec(4402, PARK, 'PVT', 'PVT', 'STAT')) == 'agrees')
check('land a city owns still differs from the state link', ac(rec(4403, PARK, 'CITY', 'LOC', 'LOC')) == 'differs')
check('a record with no owner label still differs', ac(rec(4404, PARK, 'CITY', 'LOC')) == 'differs')
check("a layer with its own table row is read by the table, never by the saved copy's STAT tag",
      ac(rec('sgzzc7', 'Otter Lake Dam Site', 'SGZZC', 'STAT', 'STAT')) == 'differs')
check('W-G11 is for state links only: a refuge link against state-owned land still differs',
      ac(rec(4405, PARK, 'SFW', 'STAT', 'STAT'), 'US Fish and Wildlife Service') == 'differs')

# ---- W-G12: a state park on federal lake land
check("W-G12: a Corps record carrying the park's own name gives no agency vote", ac(rec(5501, PARK, 'USACE', 'FED')) == 'no data')
check('W-G12: the same bare name and the same kind of place counts as the same name',
      ac(rec(5502, 'Otter Lake Recreation Area', 'USACE', 'FED')) == 'no data')
check('W-G12: Reclamation and TVA records the same way',
      ac(rec(5503, PARK, 'USBR', 'FED')) == 'no data' and ac(rec(5504, PARK, 'TVA', 'FED')) == 'no data')
check("the lake project's own record ('Otter Lake', no kind of place) still differs", ac(rec(5505, 'Otter Lake', 'USACE', 'FED')) == 'differs')
check('another kind of place with the same bare name still differs', ac(rec(5506, 'Otter Lake Wildlife Management Area', 'USACE', 'FED')) == 'differs')
check('one name holding the other still differs', ac(rec(5507, 'Otter Lake Dam Recreation Area', 'USACE', 'FED')) == 'differs')
check('a Forest Service record with the same name still differs (not lake land)', ac(rec(5508, PARK, 'USFS', 'FED')) == 'differs')
check("the Corps layer of the club's table follows the same rule",
      ac(rec('sgzzc1', PARK, 'SGZZC', 'STAT', 'STAT')) == 'no data' and ac(rec('sgzzc2', 'Otter Lake', 'SGZZC', 'STAT', 'STAT')) == 'differs')


# ---- end to end: what goes to the check list
def run(records):
    recs = {str(r['OBJECTID']): r for r in records}
    parks = {'US-9001': {'n': PARK, 't': 'State Park', 'g': 'official', 'c': [], 'm': [[r['OBJECTID'], r['Unit_Nm'], 500, 'same name'] for r in records]}}
    MC.pass_state(parks, recs, {'US-9001': fact()}, lambda ref, ids: True, st='ZZ', holds_fn=lambda ref, i: True, layer_table=TABLE)
    p = parks['US-9001']
    return [str(q[0]) for q in p.get('m') or []], [(str(x[0]), x[3]) for x in p.get('c') or []]


m, c = run([rec(4401, PARK, 'CITY', 'LOC', 'STAT')])
check('end to end: the state-owned record labelled CITY stays joined', m == ['4401'] and not c)
m, c = run([rec(5501, PARK, 'USACE', 'FED')])
check("end to end: the Corps record with the park's own name stays joined", m == ['5501'] and not c)
m, c = run([rec(4403, PARK, 'CITY', 'LOC', 'LOC')])
check('end to end: city-owned land still goes to the check list, and the row says why',
      m == [] and len(c) == 1 and c[0][1].startswith('check (agency:'))
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
