#!/usr/bin/env python3
"""23 Nov 2026, owner: 12:51 AM 'Yes' (use the county), 4:28 AM 'yes for both' (W-G8: the check list), 5:24 AM "I dont want key
bots to do internet stuff". When the park's OWN page on an official site names its county, a joined record whose box lies
well outside every named county goes to the check list, the row saying why. A record in or by the county stays; an id or the
agency's own size speaking for the joined records stops the check; a list page or an unofficial site gives nothing; the
county never confirms. The county's middle point and size come with the park facts (made on the PC): this file opens no
connection. Invented parks and records."""
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


SQ = lambda x0, y0: {'type': 'Polygon', 'coordinates': [[[x0, y0], [x0 + .05, y0], [x0 + .05, y0 + .05], [x0, y0 + .05], [x0, y0]]]}
TABLE = {'sgzza': {'agency': 'state wildlife', 'kind': 'wildlife area'}}
LINK = {'site': 'agency (known)', 'agency': 'ZZ DNR', 'page_kind': 'own page', 'usable': True, 'id_shared_by': 1, 'shared_by': 1,
        'web_name': 'unit 4471', 'name_match': 'none'}
rec = lambda oid, name, x0, y0: {'OBJECTID': oid, 'Unit_Nm': name, 'Mang_Type': 'STAT', 'Mang_Name': 'SFW', 'GIS_Acres': 500, '_g': SQ(x0, y0),
                                 '_bb': [x0, y0, x0 + .05, y0 + .05]}
OTTER = {'name': 'Otter', 'lat': 44.5, 'lon': -88.5, 'radius_km': 22.3}        # a county about 22 km in radius


def run(recs, rows, county_areas=(OTTER,), own='own', unofficial=False, sizes=()):
    parks = {'US-9001': {'n': 'Mud Lake State Wildlife Area', 't': 'State Wildlife Area', 'g': 'official', 'c': [], 'm': [list(r) for r in rows]}}
    f = {'US-9001': {'area': 'US-ZZ', 'name': 'Mud Lake State Wildlife Area', 'type': 'State Wildlife Area', 'pin': [44.5, -88.5], 'link': dict(LINK),
                     'page': {'kind': 'html', 'own_page': own, 'unofficial': unofficial, 'host': 'dnr.zz.example.gov', 'name_vs_pota': 'differs', 'name_on_page': '',
                              'sizes': list(sizes), 'coords': [], 'parts': [], 'inside_of': [], 'county_areas': list(county_areas)}}}
    out = MC.pass_state(parks, recs, f, lambda ref, ids: False, st='ZZ', holds_fn=lambda ref, i: False, layer_table=TABLE,
                      auto_confirm_stops={'US-9001'})   # 24 Nov (#371): this rule alone; the held name and pin would auto-confirm
    p = parks['US-9001']
    return [q[0] for q in p.get('m') or []], [(x[0], x[3]) for x in p.get('c') or []], (p.get('match') or {}).get('status'), out


NEAR = rec('sgzza1', 'Mud Lake Wildlife Area', -88.52, 44.48)          # inside the county
FAR = rec('sgzza2', 'Mud Lake Wildlife Area', -87.20, 45.10)           # about 120 km away: another county's Mud Lake
EDGE = rec('sgzza3', 'Mud Lake Wildlife Area', -88.10, 44.60)          # about 33 km from the middle: by the county, not clearly outside
ROW = lambda r: [r['OBJECTID'], r['Unit_Nm'], 500, 'same name']
check('has the county check', hasattr(MC, 'outside_counties') and hasattr(MC, 'county_areas_of'))
m, c, st, out = run({'sgzza2': FAR}, [ROW(FAR)])
check("a joined record far outside the county the page names goes to the check list, and the row says why",
      m == [] and len(c) == 1 and c[0][0] == 'sgzza2' and c[0][1].startswith("check (county: the park's own page names Otter County"))
check('counted', out.get('county_moved') == 1)
m, c, st, _ = run({'sgzza1': NEAR, 'sgzza2': FAR}, [ROW(NEAR), ROW(FAR)])
check('with one record in the county and one far outside: only the far one moves', m == ['sgzza1'] and [x[0] for x in c] == ['sgzza2'])
m, c, st, _ = run({'sgzza1': NEAR}, [ROW(NEAR)])
check('a record inside the county stays, and the county alone never confirms', m == ['sgzza1'] and c == [] and st == 'outlined')
m, c, st, _ = run({'sgzza3': EDGE}, [ROW(EDGE)])
check('a record just over the county line is not called outside (a county is no circle)', m == ['sgzza3'] and c == [])
m, c, st, _ = run({'sgzza2': FAR}, [ROW(FAR)], county_areas=())
check('the page names no county: nothing moves', m == ['sgzza2'] and c == [])
m, c, st, _ = run({'sgzza2': FAR}, [ROW(FAR)], county_areas=(OTTER, {'name': 'Door', 'lat': 45.12, 'lon': -87.18, 'radius_km': 30.0}))
check('the page names two counties and the record is in the second: nothing moves', m == ['sgzza2'] and c == [])
m, c, st, _ = run({'sgzza2': FAR}, [ROW(FAR)], own='list')
check('a list page: nothing moves', m == ['sgzza2'] and c == [])
m, c, st, _ = run({'sgzza2': FAR}, [ROW(FAR)], unofficial=True)
check('an unofficial site: nothing moves', m == ['sgzza2'] and c == [])
nobox = dict(FAR); nobox.pop('_bb')
m, c, st, _ = run({'sgzza2': nobox}, [ROW(FAR)])
check('a record with no box is never called outside', m == ['sgzza2'] and c == [])
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
