#!/usr/bin/env python3
"""22 Nov 2026 (owner 3:55 PM "go for all"; notes/mapping.md plan P1-P7, rule sheet PN): the park's OWN agency page helps the
match. P1 its clean total acres witness the size; P2 its name joins a record of exactly that name that holds the pin; P4 its
tracts join their records on the park's layer near the pin; P5 the bigger unit it says it lies in is never its outline; P6
nothing from a page that is not the park's own; P7 a record two parks claim stays with the better fit. Invented parks and
records only. No network. Prints PASS / FAIL lines and ends ALL PASS or SOME FAILED."""
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


SQ = [[[-80.0, 40.0], [-79.9, 40.0], [-79.9, 40.1], [-80.0, 40.1], [-80.0, 40.0]]]
LINK = {'site': 'agency (known)', 'agency': 'ZZ State Parks', 'page_kind': 'own page', 'usable': True, 'id_shared_by': 1, 'shared_by': 1}
TABLE = {'sgzza': {'agency': 'state parks', 'kind': 'park'}, 'sgzzw': {'agency': 'state wildlife', 'kind': 'wildlife area'},
         'sgzzn': {'agency': 'state natural areas', 'kind': 'preserve'}}


def page(**kw):
    return dict({'own_page': 'own', 'unofficial': False, 'host': 'parks.zz.example.gov', 'name_on_page': '', 'sizes': [],
                 'coords': [], 'parts': [], 'inside_of': []}, **kw)


def fact(name, kind='State Park', pg=None, link=LINK):
    f = {'area': 'US-ZZ', 'name': name, 'type': kind, 'pin': [40.05, -79.95], 'link': dict(link) if link else None}
    if pg is not None: f['page'] = pg
    return f


def rec(oid, name, acres=2000, **kw):
    return dict({'OBJECTID': oid, 'Unit_Nm': name, 'Mang_Type': 'STAT', 'Mang_Name': 'SPR', 'GIS_Acres': acres,
                 '_g': {'type': 'Polygon', 'coordinates': SQ}, '_bb': [-80.0, 40.0, -79.9, 40.1]}, **kw)


def park(name, rows=None, t='State Park'):
    return {'n': name, 't': t, 'm': rows or [], 'c': [], 'g': 'official' if rows else 'pin'}


def run(parks, recs, facts, holds=True):
    return MC.pass_state(parks, recs, facts, lambda ref, ids: True, st='ZZ', holds_fn=lambda ref, i: holds, layer_table=TABLE)


# ---- P1 acres from the park's own page
s_ok = {'acres': 2000.0, 'total': True, 'clean': True}
check('P1: the own page\'s clean total acres witness the size', MC.size_witnesses(fact('Invented Lake State Park', pg=page(sizes=[s_ok]))) ==
      [(2000.0, 'agency_document', 'tagged independent witness')])
check('P1: a size that is not the clean total does not', MC.size_witnesses(fact('Invented Lake State Park', pg=page(sizes=[dict(s_ok, clean=False)]))) == [])
check('P6: acres from a page that is not the park\'s own do not count',
      MC.size_witnesses(fact('Invented Lake State Park', pg=page(own_page='shared', sizes=[s_ok]))) == [])
check('P6: nor from an unofficial host', MC.size_witnesses(fact('Invented Lake State Park', pg=page(unofficial=True, sizes=[s_ok]))) == [])
p = {'US-9001': park('Invented Lake State Park', [['sgzza1', 'Invented Lake', 2000, 'name']])}
run(p, {'sgzza1': rec('sgzza1', 'Invented Lake')}, {'US-9001': fact('Invented Lake State Park', pg=page(sizes=[s_ok]))})
check('P1: the join is confirmed by the page\'s own size', p['US-9001']['match'].get('by') == 'size')

# ---- P2 second name
f2 = fact('Invented Hollow State Park', pg=page(name_on_page='Hollow Creek Natural Area | ZZ State Parks'))
p = {'US-9002': park('Invented Hollow State Park')}
out = run(p, {'sgzzn7': rec('sgzzn7', 'Hollow Creek Natural Area')}, {'US-9002': f2})
check('P2: the own page\'s name joins the one record of exactly that name that holds the pin',
      [q[0] for q in p['US-9002']['m']] == ['sgzzn7'] and 'second name' in p['US-9002']['m'][0][3] and out['second_name'] == 1)
p = {'US-9002': park('Invented Hollow State Park')}
run(p, {'sgzzn7': rec('sgzzn7', 'Hollow Creek Natural Area')}, {'US-9002': f2}, holds=False)
check('P2: not when the pin is outside the record', not p['US-9002']['m'])
near_rec = rec('sgzzn7', 'Hollow Creek Natural Area', _g={'type': 'Polygon', 'coordinates': [[[-79.9499, 40.0], [-79.9, 40.0], [-79.9, 40.1], [-79.9499, 40.1], [-79.9499, 40.0]]]})
p = {'US-9002': park('Invented Hollow State Park')}
out = run(p, {'sgzzn7': near_rec}, {'US-9002': f2}, holds=False)
check('near misses are counted, report only: a pin about 10 m outside is within 100 ft and within 0.5 km, and is NOT joined',
      not p['US-9002']['m'] and out['second_name_near'] == {'within 100 ft': 1, 'within 0.5 km': 1})
far_rec = rec('sgzzn7', 'Hollow Creek Natural Area', _g={'type': 'Polygon', 'coordinates': [[[-79.946, 40.0], [-79.9, 40.0], [-79.9, 40.1], [-79.946, 40.1], [-79.946, 40.0]]]})
out = run({'US-9002': park('Invented Hollow State Park')}, {'sgzzn7': far_rec}, {'US-9002': f2}, holds=False)
check('a pin about 340 m outside counts within 0.5 km only', out['second_name_near'] == {'within 100 ft': 0, 'within 0.5 km': 1})
p = {'US-9002': park('Invented Hollow State Park')}
run(p, {'sgzzn7': rec('sgzzn7', 'Hollow Creek Natural Area'), 'sgzzn8': rec('sgzzn8', 'Hollow Creek Natural Area')}, {'US-9002': f2})
check('P2: two records with that name go to check, never both joined', not p['US-9002']['m'] and len(p['US-9002']['c']) == 2)
p = {'US-9002': park('Invented Hollow State Park')}
run(p, {'sgzzn7': rec('sgzzn7', 'Hollow Creek Natural Area')}, {'US-9002': fact('Invented Hollow State Park',
    pg=page(own_page='shared', name_on_page='Hollow Creek Natural Area'))})
check('P6: no second name from a page that is not the park\'s own', not p['US-9002']['m'])
heads = {f'US-91{i:02d}': fact(f'Park Number {i} State Park', pg=page(name_on_page='Division of State Parks and Natural Areas')) for i in range(4)}
parks_h = {r: park(f['name']) for r, f in heads.items()}
run(parks_h, {'sgzzn9': rec('sgzzn9', 'Division of State Parks and Natural Areas')}, heads)
check('P2: a heading the site puts on 3+ parks\' pages is never a name', not any(p_['m'] for p_ in parks_h.values()))
both = {'US-9003': fact('Invented Hollow State Park', pg=page(name_on_page='Other Pond State Park')), 'US-9004': fact('Other Pond State Park')}
pb = {'US-9003': park('Invented Hollow State Park'), 'US-9004': park('Other Pond State Park')}
run(pb, {'sgzza4': rec('sgzza4', 'Other Pond State Park')}, both)
check('P2: a page naming ANOTHER POTA park of the state gives no second name', not pb['US-9003']['m'])

# ---- P4 tracts
f4 = fact('Invented River Wildlife Area', 'Wildlife Area', pg=page(parts=['North Unit', 'South Unit']))
p = {'US-9005': park('Invented River Wildlife Area', [['sgzzw1', 'Invented River Wildlife Area', 900, 'name']], t='Wildlife Area')}
far = rec('sgzzw4', 'Invented River North Unit', _bb=[-70.0, 30.0, -69.9, 30.1])
out = run(p, {'sgzzw1': rec('sgzzw1', 'Invented River Wildlife Area', 900), 'sgzzw2': rec('sgzzw2', 'Invented River South Unit', 300),
              'sgzzw3': rec('sgzzn3', 'Invented River North Unit', 200), 'sgzzw4': far}, {'US-9005': f4})
got = sorted(str(q[0]) for q in p['US-9005']['m'])
check('P4: a tract the page names joins on the park\'s own layer near the pin', 'sgzzw2' in got and out['tract'] >= 1)
check('P4: not a tract record on another layer, nor one far from the pin', 'sgzzn3' not in got and 'sgzzw4' not in got)

# ---- P5 parent unit
f5 = fact('Invented Wilderness', 'Wilderness', pg=page(inside_of=[{'unit': 'Invented National Forest', 'kind': 'National Forest'}]))
p = {'US-9006': park('Invented Wilderness', [['sgzza9', 'Invented National Forest', 90000, 'name']], t='Wilderness')}
out = run(p, {'sgzza9': rec('sgzza9', 'Invented National Forest', 90000)}, {'US-9006': f5})
check('P5: the bigger unit the page says the park lies inside never stays as its outline',
      not p['US-9006']['m'] and 'bigger unit' in p['US-9006']['c'][0][3] and out['parent'] == 1)

# ---- P7 one record, two parks
pa = {'US-9007': park('Chalky Bluff State Natural Area', [['sgzzn5', 'Chalky Bluff Natural Area', 400, 'name']], t='State Natural Area'),
      'US-9008': park('Chalky Bluff Battlefield Park', [['sgzzn5', 'Chalky Bluff Natural Area', 400, 'name']], t='Recreation Park')}
out = run(pa, {'sgzzn5': rec('sgzzn5', 'Chalky Bluff Natural Area', 400)}, {'US-9007': fact('Chalky Bluff State Natural Area', 'State Natural Area'),
                                                                          'US-9008': fact('Chalky Bluff Battlefield Park', 'Recreation Park')})
check('P7: the record stays with the park whose name and kind fit it', [q[0] for q in pa['US-9007']['m']] == ['sgzzn5'])
check('P7: the other park goes to check', not pa['US-9008']['m'] and 'another park' in pa['US-9008']['c'][0][3])
pe = {'US-9009': park('Twin Marsh Wildlife Area', [['sgzzw6', 'Twin Marsh', 500, 'name']], t='Wildlife Area'),
      'US-9010': park('Twin Marsh Wildlife Area', [['sgzzw6', 'Twin Marsh', 500, 'name']], t='Wildlife Area')}
run(pe, {'sgzzw6': rec('sgzzw6', 'Twin Marsh', 500)}, {'US-9009': fact('Twin Marsh Wildlife Area', 'Wildlife Area'), 'US-9010': fact('Twin Marsh Wildlife Area', 'Wildlife Area')})
check('P7: two parks that fit equally both keep it (same land, two park numbers)', pe['US-9009']['m'] and pe['US-9010']['m'])

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
