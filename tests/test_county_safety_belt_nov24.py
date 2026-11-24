#!/usr/bin/env python3
"""24 Nov 2026 (owner approved E, 5:39 AM CT): the county rule does not remove land that holds POTA's pin.
The distance test is not loosened. Invented parks and records only. No network."""
import pathlib, socket, sys

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


SQ = lambda x0, y0: {'type': 'Polygon', 'coordinates': [[[x0, y0], [x0 + .05, y0], [x0 + .05, y0 + .05], [x0, y0 + .05], [x0, y0]]]}
TABLE = {'sgzza': {'agency': 'state wildlife', 'kind': 'wildlife area'}}
LINK = {'site': 'agency (known)', 'agency': 'ZZ DNR', 'page_kind': 'own page', 'usable': True, 'id_shared_by': 1, 'shared_by': 1,
        'web_name': 'unit 4471', 'name_match': 'none'}
rec = lambda oid, name, x0, y0: {'OBJECTID': oid, 'Unit_Nm': name, 'Mang_Type': 'STAT', 'Mang_Name': 'SFW', 'GIS_Acres': 500,
                                 '_g': SQ(x0, y0), '_bb': [x0, y0, x0 + .05, y0 + .05]}
OTTER = {'name': 'Otter', 'lat': 44.5, 'lon': -88.5, 'radius_km': 22.3}
FAR = rec('sgzza2', 'Invented Marsh Wildlife Area', -87.20, 45.10)   # well outside Otter County
ROW = [FAR['OBJECTID'], FAR['Unit_Nm'], 500, 'same name']


def run(holds):
    parks = {'US-9001': {'n': 'Invented Marsh State Wildlife Area', 't': 'State Wildlife Area', 'g': 'official', 'c': [],
                         'm': [list(ROW)]}}
    f = {'US-9001': {'area': 'US-ZZ', 'name': 'Invented Marsh State Wildlife Area', 'type': 'State Wildlife Area',
                     'pin': [44.5, -88.5], 'link': dict(LINK),
                     'page': {'kind': 'html', 'own_page': 'own', 'unofficial': False, 'host': 'dnr.zz.example.gov',
                              'name_vs_pota': 'differs', 'name_on_page': '', 'sizes': [], 'coords': [], 'parts': [],
                              'inside_of': [], 'county_areas': [OTTER]}}}
    out = MC.pass_state(parks, {'sgzza2': FAR}, f, lambda ref, ids: False, st='ZZ',
                        holds_fn=lambda ref, i: holds, layer_table=TABLE)
    p = parks['US-9001']
    return [q[0] for q in p.get('m') or []], [(x[0], x[3]) for x in p.get('c') or []], out


m, c, out = run(holds=False)
check('land that does not hold the pin and lies far outside the county still goes to the check list (the rule is not loosened)',
      m == [] and len(c) == 1 and c[0][0] == 'sgzza2' and out.get('county_moved') == 1)
m, c, out = run(holds=True)
check("land that holds POTA's pin is not removed by the county rule, even when its box is far from the named county",
      m == ['sgzza2'] and c == [] and not out.get('county_moved'))

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
