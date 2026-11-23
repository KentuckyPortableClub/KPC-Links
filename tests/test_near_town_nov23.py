#!/usr/bin/env python3
"""23 Nov 2026, owner 6:37 AM ('4 I say yes', ruling W-G6): a 'near a town' point the park's OWN official page gives in words
('2 miles east of Shiocton'; made on the PC from the town lists, park facts page.near, with how far off it may be) is a place
witness. Land reaching its circle is in the right place: with a name that agrees it CONFIRMS ('near a town'). When ALL the
joined land lies far from there (the same name somewhere else) it goes to the check list, the row saying why; never a record
holding POTA's pin, never the far pieces of a park that also has land by the town, never when an id or the agency's own size
speaks for it. A list page or an unofficial site gives nothing. Invented parks and records; this file opens no connection."""
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
TOWN = {'lat': 44.50, 'lon': -88.50, 'within_km': 3.0, 'from': '3.2 km E of Otterville (town list)'}


def run(recs, rows, near=(TOWN,), own='own', unofficial=False, sizes=(), name_vs='differs', holds=(), place=False, counties=()):
    parks = {'US-9001': {'n': 'Mud Lake State Wildlife Area', 't': 'State Wildlife Area', 'g': 'official', 'c': [], 'm': [list(r) for r in rows]}}
    f = {'US-9001': {'area': 'US-ZZ', 'name': 'Mud Lake State Wildlife Area', 'type': 'State Wildlife Area', 'pin': [44.9, -89.4], 'link': dict(LINK),
                     'page': {'kind': 'html', 'own_page': own, 'unofficial': unofficial, 'host': 'dnr.zz.example.gov', 'name_vs_pota': name_vs,
                              'name_on_page': '', 'sizes': list(sizes), 'coords': [], 'parts': [], 'inside_of': [], 'near': list(near), 'county_areas': list(counties)}}}
    out = MC.pass_state(parks, recs, f, lambda ref, ids: place, st='ZZ', holds_fn=lambda ref, i: i in holds, layer_table=TABLE)
    p = parks['US-9001']
    return [q[0] for q in p.get('m') or []], [(x[0], x[3]) for x in p.get('c') or []], p.get('match') or {}, out


BY = rec('sgzza1', 'Mud Lake Wildlife Area', -88.52, 44.48)            # the town's point lies inside this land
FAR = rec('sgzza2', 'Mud Lake Wildlife Area', -87.20, 45.10)           # about 120 km away: another Mud Lake
MID = rec('sgzza3', 'Mud Lake Wildlife Area', -88.30, 44.55)           # about 13 km off: neither in the circle nor far
ROW = lambda r: [r['OBJECTID'], r['Unit_Nm'], 500, 'same name']
check('has the town check', hasattr(MC, 'near_points_of') and hasattr(MC, 'near_town_vote'))
m, c, st, out = run({'sgzza2': FAR}, [ROW(FAR)])
check("all the joined land far from the town the page names goes to the check list, and the row says why",
      m == [] and len(c) == 1 and c[0][0] == 'sgzza2' and c[0][1].startswith("check (town: the park's own page puts it 3.2 km E of Otterville"))
check('counted', out.get('town_moved') == 1 and 'town' in st.get('why', []))
m, c, st, _ = run({'sgzza1': BY, 'sgzza2': FAR}, [ROW(BY), ROW(FAR)])
check('a park with land by the town keeps its far pieces too (a park of many pieces)', sorted(m) == ['sgzza1', 'sgzza2'] and c == [])
m, c, st, _ = run({'sgzza2': FAR}, [ROW(FAR)], holds=('sgzza2',))
check("a record holding POTA's pin never moves, however far the town", m == ['sgzza2'] and c == [])
m, c, st, _ = run({'sgzza2': FAR}, [ROW(FAR)], place=True)
check("POTA's pin lies in or by the land (the better witness): a far town line never moves it (Rock Island Trail, 23 Nov 3 PM)", m == ['sgzza2'] and c == [])
m, c, st, _ = run({'sgzza2': FAR}, [ROW(FAR)], counties=({'name': 'Door', 'lat': 45.12, 'lon': -87.18, 'radius_km': 30.0},))
check('the land lies in the county the same page names: a far town line never moves it', m == ['sgzza2'] and c == [])
m, c, st, _ = run({'sgzza2': FAR}, [ROW(FAR)], counties=({'name': 'Otter', 'lat': 44.5, 'lon': -88.5, 'radius_km': 22.3},))
check('town and county both say the land is far: it goes to check', m == [] and len(c) == 1)
m, c, st, _ = run({'sgzza1': BY}, [ROW(BY)], name_vs='same')
check("the page's own name agrees and the land reaches the town's circle: CONFIRMED near a town",
      m == ['sgzza1'] and st.get('status') == 'confirmed' and st.get('by') == 'near a town')
m, c, st, _ = run({'sgzza1': BY}, [ROW(BY)])
check('land by the town but no name that agrees: outlined, not confirmed (the town alone never confirms)', st.get('status') == 'outlined')
m, c, st, _ = run({'sgzza3': MID}, [ROW(MID)], name_vs='same')
check('land 13 km off a 3 km circle: neither confirmed nor moved', m == ['sgzza3'] and c == [] and st.get('status') == 'outlined')
m, c, st, _ = run({'sgzza2': FAR}, [ROW(FAR)], near=())
check('the page names no town: nothing moves', m == ['sgzza2'] and c == [])
m, c, st, _ = run({'sgzza2': FAR}, [ROW(FAR)], own='list')
check('a list page: nothing moves', m == ['sgzza2'] and c == [])
m, c, st, _ = run({'sgzza2': FAR}, [ROW(FAR)], unofficial=True)
check('an unofficial site: nothing moves', m == ['sgzza2'] and c == [])
m, c, st, _ = run({'sgzza2': FAR}, [ROW(FAR)], sizes=({'acres': 500, 'witness': 'agency_document', 'total': True, 'clean': True},))
check("the agency's own size agrees: nothing moves", m == ['sgzza2'] and c == [])
nobox = dict(FAR); nobox.pop('_bb'); nobox.pop('_g')
m, c, st, _ = run({'sgzza2': nobox}, [ROW(FAR)])
check('a record with no shape and no box is never called far', m == ['sgzza2'] and c == [])
check('a circle of 0 km, or a point with no numbers, is no point', hasattr(MC, 'near_points_of') and MC.near_points_of({'link': LINK, 'page': {'own_page': 'own', 'near': [
      {'lat': 44.5, 'lon': -88.5, 'within_km': 0}, {'lat': None, 'lon': -88.5, 'within_km': 3}]}}) == [])
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
