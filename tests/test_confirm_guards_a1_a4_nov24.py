#!/usr/bin/env python3
"""24 Nov 2026 (owner t2067u 8:32 PM CT 'I agree work on it'): the four guards from the check of 787 loose-name confirms.
A1 confirm only on a record still in the park's outline; A2 no auto-confirm when two parks share the record; A3 a park named
with words in brackets (NY state forests) needs them in the record name or a one-place record, and each twin keeps only its
own piece of a shared record; A4 the agency / level-of-government check. Status only for A1/A2/A4.
Invented parks only. No network. Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import copy, pathlib, socket, sys

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


def sq(lo, la, d=0.05):
    return [[lo, la], [lo + d, la], [lo + d, la + d], [lo, la + d], [lo, la]]


def poly(lo, la, d=0.05):
    return {'type': 'Polygon', 'coordinates': [sq(lo, la, d)]}


EMPTY = set()
TABLE = {'sgzza': {'agency': 'state wildlife', 'kind': 'wildlife area'}, 'sfzzb': {'agency': 'state forests', 'kind': 'state forest'}}
LINK = {'site': 'agency (known)', 'agency': 'ZZ DNR', 'page_kind': 'own page', 'usable': True, 'id_shared_by': 1,
        'shared_by': 1, 'web_name': 'unit 4471', 'name_match': 'none'}
PAGE = {'kind': 'html', 'own_page': 'own', 'unofficial': False, 'host': 'dnr.zz.example.gov', 'name_vs_pota': 'differs',
        'name_on_page': '', 'sizes': [], 'coords': [], 'parts': [], 'inside_of': [], 'county_areas': []}


def fact(name, typ, pin):
    return {'area': 'US-ZZ', 'name': name, 'type': typ, 'pin': pin, 'link': dict(LINK), 'page': dict(PAGE)}


def run(parks, recs, facts, holds=None):
    MC.pass_state(parks, recs, facts, lambda ref, ids: holds, st='ZZ', holds_fn=lambda ref, i: holds, layer_table=TABLE,
                  auto_confirm_stops=set(), spelling_table={})
    return parks


def status(p):
    return (p.get('match') or {}).get('status')


def acr(*a, **k):
    try:
        return MC.auto_confirm_ok(*a, **k)
    except TypeError:          # main has no shared_by / st arguments: counts as the old answer below
        k.pop('shared_by', None); k.pop('st', None)
        return MC.auto_confirm_ok(*a, **k)


# ---------------------------------------------------------------- control: a plain one-park, one-record match still confirms
WNAME = 'Invented Marsh State Wildlife Area'
W = {'OBJECTID': 'sgzza1', 'Unit_Nm': WNAME, 'GIS_Acres': 500, '_g': poly(-88.50, 44.50)}
p = run({'US-9001': {'n': WNAME, 't': 'State Wildlife Area', 'm': [['sgzza1', WNAME, 500, 'same name']], 'g': 'official'}},
        {'sgzza1': W}, {'US-9001': fact(WNAME, 'State Wildlife Area', [44.525, -88.475])})['US-9001']
check('control: one park, its own one-place state record, pin inside: still confirmed', status(p) == 'confirmed')

# ---------------------------------------------------------------- A1
W9 = dict(W, OBJECTID='sgzza9', _g=poly(-88.50, 44.50))
p1 = {'n': WNAME, 't': 'State Wildlife Area', 'm': [['sgzza1', WNAME, 500, 'same name']],
      'c': [['sgzza9', WNAME, 500, 'check (moved)']], 'held': {'ids': ['sgzza9']}, 'g': 'official'}
f1 = {'US-9001': fact(WNAME, 'State Wildlife Area', [44.525, -88.475])}
check('A1: a held record that is no longer in the outline (moved to the check list) does not confirm',
      not acr('US-9001', p1, {'sgzza1': W, 'sgzza9': W9}, f1, holds_fn=lambda r, i: True, stop_parks=EMPTY, layer_table=TABLE))
p1b = dict(p1, held={'ids': ['sgzza1']}, c=[])
check('A1: the same park held on its outline record still confirms',
      acr('US-9001', p1b, {'sgzza1': W, 'sgzza9': W9}, f1, holds_fn=lambda r, i: True, stop_parks=EMPTY, layer_table=TABLE))

# ---------------------------------------------------------------- A2
pA = {'n': WNAME, 't': 'State Wildlife Area', 'm': [['sgzza1', WNAME, 500, 'same name']], 'g': 'official'}
check('A2: no auto-confirm when another park holds the same record',
      not acr('US-9001', copy.deepcopy(pA), {'sgzza1': W}, f1, holds_fn=lambda r, i: True, stop_parks=EMPTY,
              layer_table=TABLE, shared_by={'sgzza1': {'US-9001', 'US-9002'}}))
check('A2: a record held by this park alone still confirms',
      acr('US-9001', copy.deepcopy(pA), {'sgzza1': W}, f1, holds_fn=lambda r, i: True, stop_parks=EMPTY,
          layer_table=TABLE, shared_by={'sgzza1': {'US-9001'}}))
ONAME = WNAME   # a second park of the same name on the same record (equal fit: both keep it)
pp = run({'US-9001': {'n': WNAME, 't': 'State Wildlife Area', 'm': [['sgzza1', WNAME, 500, 'same name']], 'g': 'official'},
          'US-9002': {'n': ONAME, 't': 'State Wildlife Area', 'm': [['sgzza1', WNAME, 500, 'same name']], 'g': 'official'}},
         {'sgzza1': W}, {'US-9001': fact(WNAME, 'State Wildlife Area', [44.525, -88.475]),
                         'US-9002': fact(ONAME, 'State Wildlife Area', [44.52, -88.47])})
check('A2 in pass_state: two parks on one record: neither is auto-confirmed',
      all(status(pp[r]) != 'confirmed' for r in pp) and all((pp[r].get('match') or {}).get('by') not in
                                                           ('held name and pin', 'page names the land') for r in pp))

# ---------------------------------------------------------------- A3 matching: bracket words
TWO = {'OBJECTID': 'sfzzb1', 'Unit_Nm': 'Lost Pond State Forest', 'GIS_Acres': 11200,
       '_g': {'type': 'MultiPolygon', 'coordinates': [[sq(-75.50, 42.50)], [sq(-74.00, 44.00)]]}}   # two tracts ~200 km apart
ONE = dict(TWO, OBJECTID='sfzzb2', _g=poly(-75.50, 42.50))
AN = 'Lost Pond (Alpha County) State Forest'
check('A3: bracket words missing from the record and the record is two far-apart places: no match',
      not MC.bracket_place_ok(AN, TWO) if hasattr(MC, 'bracket_place_ok') else False)
check('A3: a one-place record, or one that carries the bracket words, still matches',
      hasattr(MC, 'bracket_place_ok') and MC.bracket_place_ok(AN, ONE)
      and MC.bracket_place_ok(AN, dict(TWO, Unit_Nm='Lost Pond State Forest Alpha County')))
pB = {'n': AN, 't': 'State Forest', 'm': [['sfzzb1', 'Lost Pond State Forest', 11200, 'same name']], 'g': 'official'}
fB = {'US-9101': fact(AN, 'State Forest', [42.525, -75.475])}
check('A3: a bracket-named forest on a two-place record without its county is not auto-confirmed',
      not acr('US-9101', pB, {'sfzzb1': TWO}, fB, holds_fn=lambda r, i: True, stop_parks=EMPTY, layer_table=TABLE))

# ---------------------------------------------------------------- A3 split: each NY twin keeps only its own piece
BN = 'Lost Pond (Beta County) State Forest'
tw = run({'US-9101': {'n': AN, 't': 'State Forest', 'm': [['sfzzb1', 'Lost Pond State Forest', 11200, 'same name']], 'g': 'official', 'ac': 11200},
          'US-9102': {'n': BN, 't': 'State Forest', 'm': [['sfzzb1', 'Lost Pond State Forest', 11200, 'same name']], 'g': 'official', 'ac': 11200}},
         {'sfzzb1': TWO}, {'US-9101': fact(AN, 'State Forest', [42.525, -75.475]),
                           'US-9102': fact(BN, 'State Forest', [44.025, -73.975])})
pa, pb = tw['US-9101'], tw['US-9102']
bxa = ((pa.get('parts') or {}).get('sfzzb1') or [])
bxb = ((pb.get('parts') or {}).get('sfzzb1') or [])
check('A3: each twin gets a parts entry for the shared record (one tract each)', len(bxa) == 1 and len(bxb) == 1)
check('A3: each twin\'s piece is the tract around its own pin',
      bool(bxa) and bxa[0][0] <= -75.475 <= bxa[0][2] and bxa[0][1] <= 42.525 <= bxa[0][3]
      and bool(bxb) and bxb[0][0] <= -73.975 <= bxb[0][2] and bxb[0][1] <= 44.025 <= bxb[0][3])
check('A3: the twins\' acres (park and row) drop to their own piece, about half of the shared record',
      all(4000 < (x.get('ac') or 0) < 7000 and 4000 < x['m'][0][2] < 7000 for x in (pa, pb)))
check('A3/A2: neither twin is auto-confirmed on the shared record', status(pa) != 'confirmed' and status(pb) != 'confirmed')
check('A3: the bracket county is kept: POTA name still holds the brackets', pa['n'] == AN and pb['n'] == BN)

# ---------------------------------------------------------------- A4: agency / level of government
LOCR = {'OBJECTID': '7001', 'Unit_Nm': 'Lost Pond State Forest', 'GIS_Acres': 400, 'Mang_Type': 'LOC', 'Mang_Name': 'CNTY',
        '_g': poly(-75.50, 42.50)}
STR = dict(LOCR, OBJECTID='7002', Mang_Type='STAT', Mang_Name='SFW')
SN = 'Lost Pond State Forest'
pC = {'n': SN, 't': 'State Forest', 'm': [['7001', SN, 400, 'same name']], 'g': 'official'}
fC = {'US-9201': fact(SN, 'State Forest', [42.525, -75.475])}
check('A4: a state forest on a county-run record of the same name is not auto-confirmed',
      not acr('US-9201', pC, {'7001': LOCR}, fC, holds_fn=lambda r, i: True, stop_parks=EMPTY, layer_table=TABLE, st='ZZ'))
pD = dict(pC, m=[['7002', SN, 400, 'same name']])
check('A4: the same park on a state-run record still confirms',
      acr('US-9201', pD, {'7002': STR}, fC, holds_fn=lambda r, i: True, stop_parks=EMPTY, layer_table=TABLE, st='ZZ'))
check('A4: park type levels read right', getattr(MC, 'park_gov_level', lambda t: None)('State Forest') == 'STATE'
      and MC.park_gov_level('County Park') == 'LOC' and MC.park_gov_level('National Forest') == 'FED')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
