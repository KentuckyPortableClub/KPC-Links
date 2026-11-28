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

# ---- S1 (grade of round 10): the edge allowance never reaches a neighbour parcel --------------------------------------------
def sqm(x, y, side_m, n=4):
    """A square of side_m metres at about 45 N (1 deg lat = 111 km; 1 deg lon = 78.7 km)."""
    return [[[x, y], [x + side_m / 78700, y], [x + side_m / 78700, y + side_m / 111000], [x, y + side_m / 111000], [x, y]]] if n == 1 else \
        [[[x + side_m / 78700 * t, y] for t in (0, .25, .5, .75)] + [[x + side_m / 78700, y + side_m / 111000 * t] for t in (0, .25, .5, .75)]
         + [[x + side_m / 78700 * (1 - t), y + side_m / 111000] for t in (0, .25, .5, .75)] + [[x, y + side_m / 111000 * (1 - t)] for t in (0, .25, .5, .75)] + [[x, y]]]
tiny_old = {'Unit_Nm': 'PARCEL A', 'GIS_Acres': 0.02, '_g': sqm(-93.5, 45.0, 9, 1)}                 # 0.02 acre, 5 points: rough
for gap_ft in (100, 180):
    nb = {'_nm': 'PARCEL B', '_ac': 0.02, '_g': sqm(-93.5 + (9 + gap_ft * 0.3048) / 78700, 45.0, 9)}
    check(f'S1: a 0.02-acre rough parcel and a differently named 0.02-acre parcel {gap_ft} ft away: not proven ({SL.prove(tiny_old, nb)})',
          SL.prove(tiny_old, nb)[0] is None)
acre_old = {'Unit_Nm': 'PARCEL C', 'GIS_Acres': 1.5, '_g': sqm(-93.4, 45.0, 64, 1)}                 # ~1 acre drawn, 1.5 stated: rough
nb = {'_nm': 'PARCEL D', '_ac': 1.0, '_g': sqm(-93.4 + (64 + 9.1) / 78700, 45.0, 64)}
check(f'S1: a 1-acre rough parcel and a differently named one 30 ft away: not proven ({SL.prove(acre_old, nb)})', SL.prove(acre_old, nb)[0] is None)
same = {'_nm': 'PARCEL Q', '_ac': 1.5, '_g': sqm(-93.4 + 1.5 / 78700, 45.0, 64)}                   # the same parcel, 5 ft off
check(f'S1: the real same parcel (5 ft off, another spelling) still proves ({SL.prove(acre_old, same)})', SL.prove(acre_old, same)[0] == 'overlap')

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
    ns['OLD_BOX'].update({'sgzzd10': bx(-91.3, 47.4, 0.1), '209818': bx(-91.3, 47.4, 0.1), 'sgzzd42': bx(-91.0, 47.0, 0.01)})   # the OLD copy
    p1 = {'n': 'Alpha Beta State Park', 't': 'State Park', 'm': [['sgzzd10', 'Alpha H. Beta', 6161, 'name'], ['209818', 'Alpha H. Beta State Park', 6143, 'name']]}
    r, st_ = ns['park_name_and_size']('US-9100', p1, byid, {}, 'ZZ')
    check(f'R4: no official size: the named fresh records match the old joined land within 10%: proven ({r})', st_ == 'ok' and r.startswith('name and old joined size'))
    p1h = dict(p1, m=[['sgzzd10', 'x', 6161, 'name'], ['209818', 'x', 6143, 'name']])
    byh = dict(byid); byh['sgzzd10'] = dict(byid['sgzzd10'], _fresh=False, _hint=True); byh['209818'] = dict(byid['209818'], _fresh=False, _hint=True)
    check('R4: old-copy hints never prove (fresh records only)', ns['park_name_and_size']('US-9100', p1h, byh, {}, 'ZZ')[1] != 'ok')
    # S2 (grade of round 10): an old row number now carried by a FRESH record of other land (renumbered layer) never stands in
    # for the old land: only the old copy's own box counts. Old 'sgzzd10' is far away in the old copy -> the fresh named records
    # do not lie in the old land's boxes -> not proven by the old size
    _ob = dict(ns['OLD_BOX']); ns['OLD_BOX'].clear(); ns['OLD_BOX'].update({'sgzzd10': bx(-80.0, 30.0, 0.1), '209818': bx(-80.0, 30.0, 0.1)})
    r2, st2 = ns['park_name_and_size']('US-9100', p1, byid, {}, 'ZZ')
    check(f'S2: the old land comes from the old copy only; old boxes elsewhere = not proven by the old size ({r2 or st2})',
          not r2.startswith('name and old joined size'))
    ns['OLD_BOX'].clear(); ns['OLD_BOX'].update(_ob)
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

# ---- owner 25 Nov 12:07 PM ('Delete any holds they maybe wrong idk'): saved answers are hints only (KPC_SAVED_HINTS_ONLY) ----
sw = json.load(open(ROOT / '.github/key-switches.json', encoding='utf-8'))['switches'].get('KPC_SAVED_HINTS_ONLY') or {}
check('the switch KPC_SAVED_HINTS_ONLY is on for MN, NY and the spread-test states', sorted(sw.get('on') or []) == ['CA', 'CO', 'FL', 'GA', 'ME', 'MN', 'NY', 'PA', 'TX', 'WA', 'WI'])
i_ = src.index('def run(st):'); runsrc = src[i_:src.index('\ndef ', i_ + 10)]
check("run() sets the state's saved answers aside (OVR.pop into SAVED_HINTS) right at the start, before any matching; the files are not touched",
      "if _r in OVR: SAVED_HINTS[_r] = OVR.pop(_r)" in runsrc and runsrc.index('SAVED_HINTS[_r]') < runsrc.index('load_cache(st)')
      and "and not _kr('KPC_SAVED_HINTS_ONLY')" in src[src.index('if SHEET and SHEET.get(ref)') - 5: src.index('if SHEET and SHEET.get(ref)') + 200])
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td); ns['OUT'] = td
    (td / 'US-ZZ.json').write_text(json.dumps({'parks': {}}))
    for on in (False, True):
        ns['_kr'] = (lambda n, on=on: n == 'KPC_STORE_FRESH' or (on and n == 'KPC_SAVED_HINTS_ONLY'))
        ns['OVR'] = {} if on else {'US-9200': {'join': ['sgzzh5'], 'fp': {'sgzzh5': ['Hotel Marsh', 70]}}}
        ns['SAVED_HINTS'].clear()
        if on: ns['SAVED_HINTS']['US-9200'] = {'join': ['sgzzh5', 'Hotel Marsh'], 'fp': {'sgzzh5': ['Hotel Marsh', 70]}}
        del ns['PIN_ONLY'][:]; del ns['FP_PROPOSALS'][:]
        byid2 = {'sgzzh5': {'Unit_Nm': 'Hotel Marsh', 'GIS_Acres': 70, '_bb': [-91.0, 46.0, -90.99, 46.01], '_fresh': True}}
        pk = {'US-9200': {'n': 'Hotel Marsh WMA', 't': 'Wildlife Management Area', 'm': [['sgzzh5', 'Hotel Marsh', 70, 'reviewed']],
                          'match': {'status': 'outlined'}, 'g': 'official'}}
        ns['proven_only_gate']('ZZ', pk, byid2, set(), {})
        if not on:
            check("switch OFF: a person's saved join whose fingerprint fits still draws (today's rule elsewhere)", [q[0] for q in pk['US-9200']['m']] == ['sgzzh5'])
        else:
            pr = [x for x in ns['PIN_ONLY'] if x[1] == 'US-9200']
            check('switch ON: the same saved join is a hint only: not proven by fresh data = pin only, its saved id listed to prove later',
                  pk['US-9200']['m'] == [] and pk['US-9200']['g'] == 'pin' and pr and pr[0][5] == 'sgzzh5' and 'not proven' in pr[0][3])
            check('switch ON: no question goes to the owner (nothing in the no-fingerprint list)', ns['FP_PROPOSALS'] == [])

# ---- R5: wetland district tracts from the layer file (source check: the filter on the fws records' realty fields) ----------
check("R5: the district rule reads the layer file's fws records (CMPXNAME, RSL_TYPE 'WPA', INTTYPE1 'O') before any live read",
      "_lay_fws_all = [a for a in recs if a.get('_fresh') and _sl_layer(_oid(a)) == 'fws' and (a.get('SA') or {}).get('CMPXNAME')]" in src
      and src.index('_lay_fws_all = [') < src.index('try: j, _pg = fetch_geo(FWS'))   # 26 Nov: read once for every district
i_ = src.index('_lay_fws_all = ['); blk = src[i_:src.index('try: j, _pg = fetch_geo(FWS', i_)]
check("R5 fix: the district's tract rows are code rows ('official': the agency's own records), never a person's saved answer",
      "'official: the district = FWS fee" in blk and "'reviewed:" not in blk and MC.row_class([1, 'x', 1, 'official: the district']) == 'code')
import kpc_store_attrs as SA  # noqa: E402
w = SA.wanted_fields()
check('R1 + R5: store id fields keep su_id, uniqueid and the six FWS realty fields',
      {'su_id', 'uniqueid', 'cmpxname', 'rsl_type', 'inttype1', 'orgname', 'unitname', 'sum_gisacres'} <= w)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
