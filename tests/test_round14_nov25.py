#!/usr/bin/env python3
"""25 Nov 2026, #380 round 14 (the owner's NY 1:32 PM test, kit 25t: 18 parks pin only). Invented records only.
  A  Adirondack Park: a record with no id of its own ('sgnycNone') or a line / point is never a record; a layer with no
     name field names its one record from the table's fixed 'name'.
  B  exact-name state parks: the agency's second name (NY State Parks Label, PAD-US Loc_Nm), park-family type swaps
     ('X Marine Park' = POTA's 'X State Park', 'X Trail' = 'X State Trail'), a shared record measured only on the parts the
     park holds (Robert Moses (Long Island) / (Thousand Islands)), and one source's several records added up against the
     other's. Never across families, never on other ground, never more than 10% off; the round 10 test runs first.
Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import gzip, json, os, pathlib, re, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_same_land as SL  # noqa: E402
import kpc_key_rules as KR  # noqa: E402
import kpc_match_checks as MC  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')

# ---- A: no id, lines, fixed name -------------------------------------------------------------------------------------------
na = {'re': re}
exec(src[src.index('def no_id(i):'):src.index('\ntry:', src.index('def not_area(g):'))], na)
no_id, not_area = na['no_id'], na['not_area']
check("A: 'sgnycNone', 'sgnyc', '' and None have no id; 'sgnyb330', 237576 and 'sgmne10198' do",
      all(no_id(x) for x in ('sgnycNone', 'sgnyc', '', None, 'sgnycnull')) and not any(no_id(x) for x in ('sgnyb330', 237576, 'sgmne10198')))
check('A: a line (paths / LineString) or a point is not land; a polygon is',
      not_area({'paths': [[[0, 0], [1, 1]]]}) and not_area({'type': 'LineString', 'coordinates': [[0, 0], [1, 1]]}) and not_area({'x': 1, 'y': 2})
      and not not_area({'rings': [[[0, 0], [1, 0], [1, 1], [0, 0]]]}) and not not_area({'type': 'Polygon', 'coordinates': []}))
es = src[src.index('def extra_state('):src.index('\nREAD_ONCE = {}')]
check('A: the layer reader leaves out a record with no id or no area BEFORE it can be named, saved or joined, and says so',
      es.index('if no_id(a.get(oidf.lower()))') < es.index("out.append({'OBJECTID': pre + str(") and
      es.index('if not_area(f.get(') < es.index('RAWF.setdefault(pre, []).append(f)') and 'records left out, never joined' in es)
check("A: a layer with no name field takes the table's fixed 'name' (XS accepts 'name' without 'nm')",
      "FIXED_NAME.get(pre, '')" in es and "not (_l.get('nm') or _l.get('name'))" in src and "FIXED_NAME[_pre(_st, _u)]" in src)
lc = src[src.index('def load_cache(st):'):src.index('def out_date()')]
check("A: an old saved copy's no-id record ('sgnycNone') is left out on load, so the key can never join it again",
      "if no_id(r.get('OBJECTID'))" in lc)
fr = src[src.index('def fresh_records('):src.index('def ', src.index('def fresh_records(') + 20)]
check("A: a fresh layer-file record with no name takes the table's fixed name; store keys stay letters + digits only",
      "(globals().get('FIXED_NAME') or {}).get(lay)" in fr and r"re.fullmatch(r'[a-z]*\d+', k)" in fr)

# ---- B: the key's helper part (real code) ------------------------------------------------------------------------------------
ns = {'os': os, 're': re, 'json': json, 'gzip': gzip, 'math': __import__('math'), 'KR': KR, 'MC': MC, 'notice': lambda *a: None}
exec(src[src.index('RA_USED = {}'):src.index('\ndef _maiden6')], ns)
rn = ns['real_name']
check("B: 'Canandaigua Lake Marine Park' / 'Canandaigua Lake State Marine Park' are POTA's 'Canandaigua Lake State Park'",
      rn('Canandaigua Lake State Park', 'Canandaigua Lake Marine Park', 'State Park') and rn('Canandaigua Lake State Park', 'Canandaigua Lake State Marine Park'))
check("B: 'Black Diamond Trail' is 'Black Diamond State Trail'",
      rn('Black Diamond State Trail', 'Black Diamond Trail', 'State Trail'))
check("B: never across families or other words: a forest, another lake, a trail for a park, a bare type",
      not rn('Canandaigua Lake State Park', 'Canandaigua Lake State Forest') and not rn('Honeoye Lake State Park', 'Hemlock Lake Marine Park')
      and not rn('Black Diamond State Park', 'Black Diamond Trail') and not rn('Lake State Park', 'Lake Marine Park')
      and not rn('Artpark State Park', 'Earl W. Brydges Artpark', 'State Park') and not rn('Schunnemunk Mountain State Park', 'Schunnemunk', 'State Park'))
check("B: the record's second name counts (NY State Parks Name 'Honeoye Marine Park', Label 'Honeoye Lake Marine Park')",
      ns['real_name_rec']('Honeoye Lake State Park', {'Unit_Nm': 'Honeoye Marine Park', 'Loc_Nm': 'Honeoye Lake Marine Park'}, 'State Park')
      and not ns['real_name']('Honeoye Lake State Park', 'Honeoye Marine Park', 'State Park'))


def sqr(x, y, d):
    return [[x, y], [x + d, y], [x + d, y + d], [x, y + d], [x, y]]


def box(rs):
    return [min(p[0] for r in rs for p in r), min(p[1] for r in rs for p in r), max(p[0] for r in rs for p in r), max(p[1] for r in rs for p in r)]


def rec(nm, rs, ac=None, loc=''):
    return {'Unit_Nm': nm, 'Loc_Nm': loc, '_g': {'rings': rs}, '_bb': box(rs), '_fresh': True,
            'GIS_Acres': ac if ac is not None else MC._ring_acres(rs)}


with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td); ns['OUT'] = td
    li, ti = sqr(-73.30, 40.62, 0.02), sqr(-74.86, 44.98, 0.04)   # two tracts 150 km apart: LI ~ 370 ac, TI ~ 1,300 ac
    li_ac, ti_ac = MC._ring_acres([li]), MC._ring_acres([ti])
    ti3 = [sqr(-74.86, 44.98, 0.02), sqr(-74.84, 44.98, 0.02), [[-74.86, 45.00], [-74.82, 45.00], [-74.82, 45.02], [-74.86, 45.02], [-74.86, 45.00]]]   # the same tract in 3 records
    byid = {'9576': rec('Robert Moses State Park', [li, ti]),
            'sgzzb585': rec('Robert Moses', [sqr(-73.30, 40.62, 0.0199)], loc='Robert Moses State Park'),
            'sgzzb178': rec('Robert Moses', [ti3[0]]), 'sgzzb179': rec('Robert Moses', [ti3[1]]), 'sgzzb180': rec('Robert Moses', [ti3[2]]),
            'sgzzb330': rec('Canandaigua Lake Marine Park', [sqr(-77.27, 42.87, 0.003)], 13),
            '9623': rec('Canandaigua Lake Marine Park', [sqr(-77.27, 42.87, 0.003)], 13),
            '9137': rec('Canandaigua Lake Access', [sqr(-77.20, 42.80, 0.002)], 7),
            'sgzzb361': rec('Honeoye Marine Park', [sqr(-77.50, 42.72, 0.002)], 9, loc='Honeoye Lake Marine Park'),
            '9629': rec('Honeoye Lake Marine Park', [sqr(-77.50, 42.72, 0.002)], 9)}
    for k, v in byid.items(): ns['OLD_BOX'][k] = v['_bb']
    web = {'US-9128': {'n': 'Robert Moses (Long Island) State Park', 'ac': round(li_ac), 'm': [['9576', 'x', 3655, 'name'], ['sgzzb585', 'x', 943, 'name']]},
           'US-9374': {'n': 'Robert Moses (Thousand Islands) State Park', 'ac': 99999, 'm': [['9576', 'x', 3655, 'name']]},
           'US-9026': {'n': 'Canandaigua Lake State Park', 'ac': 17, 'm': []}, 'US-9077': {'n': 'Honeoye Lake State Park', 'ac': 5, 'm': []}}
    (td / 'US-ZZ.json').write_text(json.dumps({'parks': web}))
    pli = {'n': 'Robert Moses (Long Island) State Park', 't': 'State Park', 'parts': {'9576': [box([li])]},
           'm': [['9576', 'Robert Moses State Park', 3655, 'name'], ['sgzzb585', 'Robert Moses', 943, 'name']]}
    r, s_ = ns['park_name_and_size']('US-9128', pli, byid, {}, 'ZZ')
    check(f"B: Robert Moses (Long Island): the shared PAD-US record counts only on the part the park holds: proven ({r})", s_ == 'ok')
    pli_whole = dict(pli); pli_whole.pop('parts')
    check('B: the same park without its parts (the whole shared record, both places): not proven',
          ns['park_name_and_size']('US-9128', pli_whole, byid, {}, 'ZZ')[1] != 'ok')
    pti = {'n': 'Robert Moses (Thousand Islands) State Park', 't': 'State Park', 'parts': {'9576': [box([ti])]},
           'm': [['9576', 'Robert Moses State Park', 3655, 'name'], ['sgzzb178', 'Robert Moses', 1, 'name'], ['sgzzb179', 'Robert Moses', 1, 'name'],
                 ['sgzzb180', 'Robert Moses', 1, 'name']]}
    r, s_ = ns['park_name_and_size']('US-9374', pti, byid, {}, 'ZZ')
    check(f"B: Robert Moses (Thousand Islands): one PAD-US part against three NY State Parks records added up: proven ({r})",
          s_ == 'ok' and '3 record(s)' in r)
    byid_big = dict(byid, sgzzb179=rec('Robert Moses', [sqr(-74.84, 44.98, 0.03)]))
    check('B: the same, when the three records add up to more than 10% over the part: not proven',
          ns['park_name_and_size']('US-9374', pti, byid_big, {}, 'ZZ')[1] != 'ok')
    byid_far = dict(byid, sgzzb178=rec('Robert Moses', [sqr(-75.50, 44.50, 0.02)]), sgzzb179=rec('Robert Moses', [sqr(-75.50, 44.60, 0.02)]),
                    sgzzb180=rec('Robert Moses', [sqr(-75.50, 44.70, 0.02)]))
    check("B: the other source's records on other ground are not counted: not proven",
          ns['park_name_and_size']('US-9374', pti, byid_far, {}, 'ZZ')[1] != 'ok')
    pc = {'n': 'Canandaigua Lake State Park', 't': 'State Park',
          'm': [['9623', 'Canandaigua Lake Marine Park', 13, 'name'], ['sgzzb330', 'Canandaigua Lake Marine Park', 13, 'name'], ['9137', 'Canandaigua Lake Access', 7, 'name']]}
    r, s_ = ns['park_name_and_size']('US-9026', pc, byid, {}, 'ZZ')
    check(f"B: Canandaigua Lake State Park: 'Marine Park' in PAD-US and NY State Parks, same ground, same size: proven ({r})", s_ == 'ok')
    ph = {'n': 'Honeoye Lake State Park', 't': 'State Park', 'm': [['9629', 'x', 9, 'name'], ['sgzzb361', 'x', 9, 'name']]}
    r, s_ = ns['park_name_and_size']('US-9077', ph, byid, {}, 'ZZ')
    check(f"B: Honeoye Lake State Park: PAD-US name + NY State Parks Label: proven ({r})", s_ == 'ok')
    byid_off = dict(byid, sgzzb361=rec('Honeoye Marine Park', [sqr(-77.50, 42.72, 0.002)], 20, loc='Honeoye Lake Marine Park'))
    check('B: the same with sizes 9 and 20 acres: not proven', ns['park_name_and_size']('US-9077', ph, byid_off, {}, 'ZZ')[1] != 'ok')
    # the gate: the proven park keeps its named rows; the access site with another name leaves
    ns['_kr'] = lambda n: n == 'KPC_STORE_FRESH'
    ns['OVR'] = {}
    parks = {'US-9026': dict(pc, m=[list(q) for q in pc['m']])}
    ns['proven_only_gate']('ZZ', parks, byid, set(), {})
    check(f"B: the gate: Canandaigua keeps its two Marine Park rows, the 'Canandaigua Lake Access' row leaves ({[q[0] for q in parks['US-9026']['m']]})",
          [q[0] for q in parks['US-9026']['m']] == ['9623', 'sgzzb330'])
nw = src[src.index('def park_name_no_witness('):src.index('def _name_proofs(')]
check('B: the round 10 test runs first and stands: the wide test only adds proofs', "wide=False" in nw and "if r_[1] == 'ok' else" in nw)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
