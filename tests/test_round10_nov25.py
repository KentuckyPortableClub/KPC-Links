#!/usr/bin/env python3
"""25 Nov 2026, #380 round 10 (grade after the owner's 9:11 AM MN test; the owner's 9:50 AM pick 'Two sources agree').
R1 agency record ids, R2 rough outlines measured by grid points, R3 'two fits' broken by shared ground, R4 + two sources at
park level, R5 wetland district tracts from the layer file, R6 the per-row proof trace. Invented records only.
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


def sq(x, y, d, n=4):
    """A square ring; n = points per side (n=1: 5 points, the rough 0.001-degree saved copy look)."""
    pts = []
    for (ax, ay), (bx, by) in (((x, y), (x + d, y)), ((x + d, y), (x + d, y + d)), ((x + d, y + d), (x, y + d)), ((x, y + d), (x, y))):
        for k in range(n): pts.append([ax + (bx - ax) * k / n, ay + (by - ay) * k / n])
    return [pts + [pts[0]]]


# ---- R1: agency record id ----------------------------------------------------------------------------------------------
spec = SL.id_spec('sgmne')
check("R1: sgmne su_id and sgmna uniqueid are agency record ids (kind 'arec'); sgmna keeps lam_program_project_code",
      spec.get('su_id', ('',))[0] == 'arec' and SL.id_spec('sgmna').get('uniqueid', ('',))[0] == 'arec'
      and SL.id_spec('sgmna').get('lam_program_project_code', ('',))[0] == 'unit')
old = {'Unit_Nm': 'PATTERSON LAKE', 'GIS_Acres': 40, '_g': sq(-93.70, 44.80, 0.006, 1), 'SA': {'su_id': 332589}}
fr_same = {'_nm': 'PATTERSON LAKE', '_ac': 41, '_g': sq(-93.70, 44.80, 0.006), 'su_id': '332589'}
fr_far = {'_nm': 'PATTERSON LAKE', '_ac': 40, '_g': sq(-92.00, 46.00, 0.006), 'su_id': '332589'}
fr_other = {'_nm': 'OTHER PLACE', '_ac': 90, '_g': sq(-93.70, 44.80, 0.006), 'su_id': '332589'}
fr_diff = {'_nm': 'PATTERSON LAKE', '_ac': 40, '_g': sq(-93.70, 44.80, 0.006), 'su_id': '999999'}
lv, note = SL.prove(old, fr_same, spec)
check(f'R1: same su_id, boxes overlap, same name: proven at id ({lv}: {note})', lv == 'id' and 'agency record id' in note)
check('R1: same su_id far away: not proven (the place must agree)', SL.prove(old, fr_far, spec)[0] is None)
check('R1: same su_id on the ground but another name AND size off by more than 10%: not proven by the id',
      SL.prove(old, fr_other, spec)[0] != 'id')
lv2, note2 = SL.prove(old, fr_diff, spec)
check(f'R1: a DIFFERENT su_id never refuses (name + size or ground still decide: {lv2}, {note2})',
      lv2 is not None and 'different agency id' not in note2)

# ---- R2: rough outline, grid points against the fresh outline ------------------------------------------------------------
rough = {'Unit_Nm': 'ALPHA', 'GIS_Acres': 400, '_g': sq(-93.0, 45.0, 0.01, 1)}   # measured ~ 270 ac vs 400 stated: rough
check('R2: the old outline is rough (measured area 20%+ off its acres)', SL.view(rough)['coarse'])
fine = {'_nm': 'ALPHA', '_ac': 400, '_g': sq(-93.0, 45.0005, 0.01, 8)}   # the same land, half an edge allowance off
lv, note = SL.prove(rough, fine)
check(f'R2: rough vs fresh on the same ground: overlap by grid points ({lv}: {note})', lv == 'overlap' and 'grid points' in note)
big = {'_nm': 'ALPHA', '_ac': 4000, '_g': sq(-93.01, 44.99, 0.04, 8)}
lv, note = SL.prove(rough, big)
check(f'R2: rough record inside a larger fresh one with a shared name: piece ({lv})', lv == 'piece')
big_other = dict(big, _nm='GAMMA')
check('R2: the same, no name in common: never a piece', SL.prove(rough, big_other)[0] != 'piece')
check('R2: the edge allowance counts a point just outside the fresh edge (0.0005 degree), not one 0.002 off',
      SL._near_edge(-93.0005, 45.005, SL.rings_of(fine['_g']), SL.EDGE) and not SL._near_edge(-93.002, 45.005, SL.rings_of(fine['_g']), SL.EDGE))

# ---- R3: two fits by name + size, broken by shared ground ------------------------------------------------------------------
c_on = {'_nm': 'ALPHA', '_ac': 400, '_g': sq(-93.0, 45.004, 0.01, 8)}      # 60% of the old ground
c_next = {'_nm': 'ALPHA', '_ac': 400, '_g': sq(-93.0, 44.99, 0.01, 8)}     # the square below: only the edge allowance
tr = {}
k, lv, note = SL.pick(rough, {'sgzza300': c_on, 'sgzza301': c_next}, trace=tr)
check(f'R3: name + size two fits: the one holding half the old ground or more wins ({k}, {lv}, {note})',
      k == 'sgzza300' and lv == 'name_size' and 'shared ground breaks the tie' in note)
k2, lv2, why2 = SL.pick(rough, {'sgzza1': c_next, 'sgzza2': dict(c_next)}, own='sgzza1')
check(f'R3: two fits that neither holds: still not proven; the row number never decides ({why2})', k2 is None and 'two fits' in why2)
check("R6: pick's trace names the rough outline, the winner and its level", tr.get('rough') is True and tr.get('best') == 'sgzza300' and tr.get('level') == 'name_size')
tr = {}
SL.pick(rough, {'sgzza9': dict(c_next, _nm='BETA', _ac=50)}, trace=tr)
check(f"R6: an unproven old record's trace names the best candidate and why ({tr.get('why')})", tr.get('best') == 'sgzza9' and tr.get('level') is None and tr.get('why'))

# ---- R4 + two sources (the key's helper part, real code) -------------------------------------------------------------------
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
start = src.index('RA_USED = {}'); end = src.index('\ndef _maiden6')
ns = {'os': os, 're': re, 'json': json, 'gzip': gzip, 'math': __import__('math'), 'KR': KR, 'MC': MC, 'notice': lambda *a: None}
exec(src[start:end], ns)
rn = ns['real_name']
check("R4: real name: 'George H. Crosby-Manitou' + 'State Park' = 'George Crosby Manitou State Park' (initials aside)",
      rn('George Crosby Manitou State Park', 'George H. Crosby-Manitou', 'State Park') and rn('George Crosby Manitou State Park', 'George H. Crosby Manitou State Park'))
check("R4: real name: 'Area C' never equals 'Area D'; another park's name never; a generic name never",
      not rn('Area C', 'Area D') and not rn('Franz Jevne State Park', 'George H. Crosby-Manitou', 'State Park') and not rn('Scenic State Park', 'Unit 4'))
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    ns['OUT'] = td
    bx = lambda x, y, d: [x, y, x + d, y + d]
    # the website key: the park's old joined land, 6,408 acres, in its boxes
    (td / 'US-ZZ.json').write_text(json.dumps({'parks': {
        'US-9100': {'n': 'Alpha Beta State Park', 't': 'State Park', 'ac': 6408, 'm': [['sgzzd10', 'Alpha Beta', 6161, 'name'], ['209818', 'Alpha Beta State Park', 6143, 'name']]},
        'US-9101': {'n': 'Gamma Falls Unique Area', 't': 'Unique Area', 'ac': 358, 'm': [['sgzzd42', 'Gamma Falls', 91, 'name']]}}}))
    byid = {'sgzzd10': {'Unit_Nm': 'Alpha H. Beta', 'GIS_Acres': 6161, '_bb': bx(-91.3, 47.4, 0.1), '_fresh': True},
            '209818': {'Unit_Nm': 'Alpha H. Beta State Park', 'GIS_Acres': 6143, '_bb': bx(-91.3, 47.4, 0.1), '_fresh': True},
            'sgzze7': {'Unit_Nm': 'DELTA LAKE', 'GIS_Acres': 40, '_bb': bx(-91.28, 47.41, 0.01), '_fresh': True},
            'sgzzd42': {'Unit_Nm': 'Gamma Falls', 'GIS_Acres': 91, '_bb': bx(-91.0, 47.0, 0.01), '_fresh': True},
            'sgzzf9': {'Unit_Nm': 'Gamma Falls', 'GIS_Acres': 88, '_bb': bx(-91.0, 47.0, 0.01), '_fresh': True},
            'sgzzf10': {'Unit_Nm': 'Gamma Falls', 'GIS_Acres': 300, '_bb': bx(-91.0, 47.0, 0.01), '_fresh': True}}
    p1 = {'n': 'Alpha Beta State Park', 't': 'State Park', 'm': [['sgzzd10', 'Alpha H. Beta', 6161, 'name'], ['209818', 'Alpha H. Beta State Park', 6143, 'name']]}
    r, st_ = ns['park_name_and_size']('US-9100', p1, byid, {}, 'ZZ')
    check(f'R4: no official size: the named fresh records match the old joined land within 10%: proven ({r})', st_ == 'ok' and r.startswith('name and old joined size'))
    p1h = dict(p1, m=[['sgzzd10', 'x', 6161, 'name'], ['209818', 'x', 6143, 'name']])
    byh = dict(byid); byh['sgzzd10'] = dict(byid['sgzzd10'], _fresh=False, _hint=True); byh['209818'] = dict(byid['209818'], _fresh=False, _hint=True)
    check('R4: old-copy hints never prove (fresh records only)', ns['park_name_and_size']('US-9100', p1h, byh, {}, 'ZZ')[1] != 'ok')
    p2 = {'n': 'Gamma Falls Unique Area', 't': 'Unique Area', 'm': [['sgzzd42', 'Gamma Falls', 91, 'name'], ['sgzzf9', 'Gamma Falls', 88, 'name']]}
    r, st_ = ns['park_name_and_size']('US-9101', p2, byid, {}, 'ZZ')
    check(f"owner's pick: two official sources (layers d and f) carry the name and agree within 10%: proven ({r})", st_ == 'ok' and r.startswith('name in two official sources'))
    p3 = {'n': 'Gamma Falls Unique Area', 't': 'Unique Area', 'm': [['sgzzd42', 'Gamma Falls', 91, 'name'], ['sgzzf10', 'Gamma Falls', 300, 'name']]}
    check('two sources whose sizes differ by more than 10% (and the old land 358 ac): not proven', ns['park_name_and_size']('US-9101', p3, byid, {}, 'ZZ')[1] != 'ok')
    p4 = {'n': 'Gamma Falls Unique Area', 't': 'Unique Area', 'm': [['sgzzd42', 'Gamma Falls', 91, 'name'], ['sgzzd43', 'Gamma Falls', 90, 'name']]}
    byid['sgzzd43'] = dict(byid['sgzzd42'], GIS_Acres=90)
    check('two records of the SAME layer are one source: not proven by two sources', ns['park_name_and_size']('US-9101', p4, byid, {}, 'ZZ')[1] != 'ok')
    # the gate: a park proven by its named records keeps them; a row carrying ANOTHER real name leaves the map
    ns['_kr'] = lambda n: n == 'KPC_STORE_FRESH'
    ns['OVR'] = {}
    parks = {'US-9100': {'n': 'Alpha Beta State Park', 't': 'State Park', 'm': p1['m'] + [['sgzze7', 'DELTA LAKE', 40, 'name']]}}
    res = ns['proven_only_gate']('ZZ', parks, byid, set(), {})
    kept = [str(q[0]) for q in parks['US-9100']['m']]
    check(f"the gate: proven by its named records, the park keeps them; a piece carrying another name leaves (kept {kept})",
          kept == ['sgzzd10', '209818'] and res['name_size'].get('name and old joined size') == 1)
    check('R6: the gate lists the old rows of a park that lost rows (old id, layer, why)',
          any(x[1] == 'US-9100' and x[2] == 'sgzzd10' for x in ns['PROOF_ROWS']))

# ---- R5: wetland district tracts from the layer file (source check: the filter on the fws records' realty fields) ----------
check("R5: the district rule reads the layer file's fws records (CMPXNAME, RSL_TYPE 'WPA', INTTYPE1 'O') before any live read",
      "_lay_fws = [a for a in recs if a.get('_fresh') and _sl_layer(_oid(a)) == 'fws' and (a.get('SA') or {}).get('CMPXNAME')]" in src
      and src.index('_lay_fws = [') < src.index('try: j, _pg = fetch_geo(FWS'))
import kpc_store_attrs as SA  # noqa: E402
w = SA.wanted_fields()
check('R1 + R5: store id fields keep su_id, uniqueid and the six FWS realty fields',
      {'su_id', 'uniqueid', 'cmpxname', 'rsl_type', 'inttype1', 'orgname', 'unitname', 'sum_gisacres'} <= w)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
