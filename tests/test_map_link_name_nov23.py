#!/usr/bin/env python3
"""23 Nov 2026, owner: 12:51 AM 'Yes' (use the map link on the park's page), 4:28 AM 'yes for both' (W-G7: a pin-only park's
record goes on the check list). When the park's OWN page on an official site links the agency's own map viewer under a name
and exactly ONE record of the state carries that name: a joined park whose joined record it is is confirmed ('map link
name'); a pin-only park gets that record on its check list with the reason written in the row, never drawn. Two records of
one name, a list page, an unofficial site: nothing. Nothing is joined, moved or dropped. Invented parks and records. No network."""
import ast, pathlib, socket, sys

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


SQ = lambda x0, y0: {'type': 'Polygon', 'coordinates': [[[x0, y0], [x0 + .1, y0], [x0 + .1, y0 + .1], [x0, y0 + .1], [x0, y0]]]}
TABLE = {'sgzza': {'agency': 'state wildlife', 'kind': 'wildlife area'}}
LINK = {'site': 'agency (known)', 'agency': 'ZZ DNR', 'page_kind': 'own page', 'usable': True, 'id_shared_by': 1, 'shared_by': 1,
        'web_name': 'unit 4471', 'name_match': 'none'}
rec = lambda oid, name, x0: {'OBJECTID': oid, 'Unit_Nm': name, 'Mang_Type': 'STAT', 'Mang_Name': 'SFW', 'GIS_Acres': 500, '_g': SQ(x0, 40.0),
                             '_bb': [x0, 40.0, x0 + .1, 40.1]}


def fact(map_names, own='own', unofficial=False):
    return {'area': 'US-ZZ', 'name': 'Otter Marsh State Wildlife Area', 'type': 'State Wildlife Area', 'pin': [40.05, -79.95], 'link': dict(LINK),
            'page': {'kind': 'html', 'own_page': own, 'unofficial': unofficial, 'host': 'dnr.zz.example.gov', 'name_vs_pota': 'differs',
                     'name_on_page': '', 'sizes': [], 'coords': [], 'parts': [], 'inside_of': [],
                     'map_names': [{'name': n, 'host': 'dnrmaps.zz.example.gov', 'param': 'id'} for n in map_names]}}


NOTES, ROWS = [], []


def joined(map_names, recs=None, **kw):
    recs = recs or {'sgzza1': rec('sgzza1', 'Otter Marsh Wildlife Area', -80.0)}
    parks = {'US-9001': {'n': 'Otter Marsh State Wildlife Area', 't': 'State Wildlife Area', 'g': 'official', 'c': [],
                         'm': [['sgzza1', 'Otter Marsh Wildlife Area', 500, 'same name']]}}
    MC.pass_state(parks, recs, {'US-9001': fact(map_names, **kw)}, lambda ref, ids: False, st='ZZ', holds_fn=lambda ref, i: False, layer_table=TABLE,
                      auto_confirm_stops={'US-9001'})   # 24 Nov (#371): this rule alone; the held name and pin would auto-confirm
    p = parks['US-9001']
    NOTES[:] = (p.get('match') or {}).get('notes') or []
    ROWS[:] = p.get('c') or []
    return (p.get('match') or {}).get('status'), (p.get('match') or {}).get('by'), [q[0] for q in p.get('m') or []], len(p.get('c') or [])


check('has the map-link names', hasattr(MC, 'map_link_names'))
check("the page's map link names the joined record, the only one of that name: confirmed by map link name",
      joined(['OTTER MARSH WILDLIFE AREA'])[:2] == ('confirmed', 'map link name'))
check('nothing is joined, moved or dropped by it', joined(['OTTER MARSH WILDLIFE AREA'])[2:] == (['sgzza1'], 0))
wi = {'sgzza1': rec('sgzza1', 'Otter Marsh State Wildlife Area', -80.0)}
check("the map says 'OTTER MARSH WILDLIFE AREA', the record 'Otter Marsh State Wildlife Area': the same place",
      joined(['OTTER MARSH WILDLIFE AREA'], recs=wi)[:2] == ('confirmed', 'map link name'))
check('no map-link name: as before (not confirmed)', joined([])[0] == 'outlined')
r = joined(['HERON ROCK WILDLIFE AREA'])
check('the map link gives a name no record of the state carries (a spelling, a cut-off value): a note, nothing moved',
      r[0] == 'outlined' and r[2:] == (['sgzza1'], 0) and NOTES == ["the page's map link names another record"])
# W-G10 (owner 5:01 AM 'yes'): another record of the state carries the map's name
other = {'sgzza1': rec('sgzza1', 'Otter Marsh Wildlife Area', -80.0), 'sgzza7': rec('sgzza7', 'Heron Rock Wildlife Area', -78.0)}
r = joined(['HERON ROCK WILDLIFE AREA'], recs=other)
check("the map link names ANOTHER record of the state: the joined piece goes to the check list, the park is pin only",
      r[0] == 'pin' and r[2] == [] and r[3] == 1)
check('the check row says why', ROWS and ROWS[0][0] == 'sgzza1' and ROWS[0][3].startswith('check (map link:'))
joined(['OTTER MARSH WILDLIFE AREA'])
check('no note when the map link names the joined record', NOTES == [])
two = {'sgzza1': rec('sgzza1', 'Otter Marsh Wildlife Area', -80.0), 'sgzza9': rec('sgzza9', 'Otter Marsh Wildlife Area', -78.0)}
check('two records of the state carry that name: unsure, not confirmed', joined(['OTTER MARSH WILDLIFE AREA'], recs=two)[0] == 'outlined')
check('a list page: nothing', joined(['OTTER MARSH WILDLIFE AREA'], own='list')[0] == 'outlined')
check('an unofficial site: nothing', joined(['OTTER MARSH WILDLIFE AREA'], unofficial=True)[0] == 'outlined')

# the pin-only check row (kpc_us_key._map_name_checks), run on its own: the builder file is not imported (it builds on import)
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
fn = next((n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == '_map_name_checks'), None)
check('the builder has the pin-only check row', fn is not None)
if fn is not None:
    ns = {'MC': MC, 'OVR': {'US-9003': {'no': ['sgzza1']}}}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), 'kpc_us_key.py', 'exec'), ns)
    byid = {'sgzza1': rec('sgzza1', 'Otter Marsh Wildlife Area', -80.0), 'sgzza2': rec('sgzza2', 'Fox Hollow Wildlife Area', -79.0)}
    f = fact(['OTTER MARSH WILDLIFE AREA'])
    parks = {'US-9001': {'n': 'Otter Marsh State Wildlife Area', 'm': [], 'c': []},                       # pin only
             'US-9002': {'n': 'Fox Hollow State Wildlife Area', 'm': [['sgzza2', 'Fox Hollow Wildlife Area', 500, 'same name']], 'c': []},
             'US-9003': {'n': 'Otter Marsh State Wildlife Area', 'm': [], 'c': []},                       # a person already said no
             'US-9004': {'n': 'Otter Marsh State Wildlife Area', 'm': [], 'c': []}}                       # a list page
    facts = {'US-9001': f, 'US-9002': fact(['FOX HOLLOW WILDLIFE AREA']), 'US-9003': f, 'US-9004': fact(['OTTER MARSH WILDLIFE AREA'], own='list')}
    res = {}
    ns['_map_name_checks']('ZZ', parks, byid, facts, res)
    row = (parks['US-9001']['c'] or [[None, '', 0, '']])[0]
    check('a pin-only park gets the record on its check list, never drawn', row[0] == 'sgzza1' and parks['US-9001']['m'] == [])
    check('the row says why, in plain words', row[3].startswith('check (map link:') and 'a person decides' in row[3])
    check('a joined park gets no check row from it', parks['US-9002']['c'] == [])
    check('a record a person already said no to is not put back', parks['US-9003']['c'] == [])
    check('a list page gives no check row', parks['US-9004']['c'] == [])
    check('counted', res.get('map_name_checks') == 1)
    ns['_map_name_checks']('ZZ', parks, byid, facts, res)
    check('a second pass does not add the row twice', len(parks['US-9001']['c']) == 1)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
