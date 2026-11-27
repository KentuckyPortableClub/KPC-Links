#!/usr/bin/env python3
"""26 Nov 2026: tests of the v2 scorecard (tools/pc-keys/kpc_v2_scorecard.py) and of the side-by-side runner
(tools/pc-keys/kpc_test_v2.py). Tiny made-up fixtures only; no real data, no real v2 matcher (the runner test uses a tiny fake
kpc_us_key_v2.py). Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import re, contextlib, copy, csv, gzip, io, json, pathlib, shutil, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'pc-keys'))
import kpc_v2_scorecard as SC  # noqa: E402
import kpc_test_v2 as RUN  # noqa: E402
import kpc_test_keys as K  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


def sq(x0, y0, s=10000): return [x0, y0, s, 0, 0, s, -s, 0, 0, -s]   # a 0.01 degree square (about 0.9 km), q = 6


def wjson(p, d):
    p = pathlib.Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(p, 'wb', mtime=0) as g: g.write(json.dumps(d, sort_keys=True).encode())


def wcsv(p, rows, cols):
    with open(p, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)


def rec(key, name, x0, y0, layer='sgzz'):
    return {'key': key, 'layer': layer, 'record_id': key[len(layer):], 'record_name': name, 'attributes': {}, 'q': 6, 'rings': [sq(x0, y0)]}


ALPHA, BETA = rec('sgzz1', 'Alpha', -85000000, 38000000), rec('sgzz2', 'Beta', -85100000, 38100000)
FACTS = {'parks': {'US-0001': {'pin': [38.005, -84.995], 'size': {'acres': 100, 'witness_counts': True}},
                   'US-0002': {'pin': [38.2, -85.0], 'size': {'acres': 500, 'witness_counts': True}},
                   'US-0003': {'pin': [38.5, -85.5]}}}


def v1_key():
    return {'st': 'MN', 'parks': {
        'US-0001': {'n': 'Alpha Park', 't': 'SP', 'm': [['sgzz1', 'Alpha', 100, 'name']], 'c': [['sgzz2', 'Beta', 5, 'check (x)']], 'ac': 100, 'match': {'status': 'confirmed', 'by': 'id'}},
        'US-0002': {'n': 'Beta Park', 't': 'SP', 'm': [['sgzz2', 'Beta', 100, 'name']], 'c': [], 'ac': 100, 'match': {'status': 'outlined', 'by': 'name'}},
        'US-0003': {'n': 'Gamma Park', 't': 'SP', 'm': [], 'c': [], 'match': {'status': 'pin'}}}}


def v2_data():
    parks = {'US-0001': {'n': 'Alpha Park', 't': 'SP', 'm': [['sgzz1', 'Alpha', 100, 'id']], 'c': [], 'ac': 100, 'match': {'status': 'confirmed', 'by': 'id', 'step': 2, 'why': None}},
             'US-0002': {'n': 'Beta Park', 't': 'SP', 'm': [['sgzz2', 'Beta', 100, 'name']], 'c': [], 'ac': 100, 'match': {'status': 'confirmed', 'by': 'name+pin', 'step': 3, 'why': None}},
             'US-0003': {'n': 'Gamma Park', 't': 'SP', 'm': [], 'c': [], 'match': {'status': 'pin', 'by': None, 'step': 4, 'why': 'no_record_with_this_name'}}}
    proof = [{'ref': 'US-0001', 'st': 'MN', 'file_key': 'sgzz1', 'agency_id': '', 'layer': 'sgzz', 'record_name': 'Alpha', 'acres': 100, 'step': 2, 'by': 'id', 'evidence': ''},
             {'ref': 'US-0002', 'st': 'MN', 'file_key': 'sgzz2', 'agency_id': '', 'layer': 'sgzz', 'record_name': 'Beta', 'acres': 100, 'step': 3, 'by': 'name+pin', 'evidence': ''}]
    pino = [{'ref': 'US-0003', 'st': 'MN', 'name': 'Gamma Park', 'kind': 'SP', 'reason_code': 'no_record_with_this_name', 'reason': 'x'}]
    run = {'MN': {'seconds': 5.0, 'gate': {'ok': True, 'old_ids': 0, 'two_name': 0, 'not_in_file': 0, 'id_mismatch': 0}, 'not_built': None}}
    return {'v2': 1, 'st': 'MN', 'made': 'x', 'layer_files': {'US-MN': {}}, 'counts': {}, 'parks': parks}, proof, pino, run


def write_v2(d, key, proof, pino, run):
    wjson(d / 'US-MN.json.gz', key)
    base_cols = ['ref', 'st', 'file_key', 'agency_id', 'layer', 'record_name', 'acres', 'step', 'by', 'evidence']
    wcsv(d / 'v2-proof.csv', proof, base_cols + sorted({k for r in proof for k in r} - set(base_cols)))
    wcsv(d / 'v2-pin-only.csv', pino, ['ref', 'st', 'name', 'kind', 'reason_code', 'reason'])
    (d / 'v2-run.json').write_text(json.dumps({'states': run}), encoding='utf-8')


def write_world(t, base=None, recs=None):
    store = t / 'store'
    wjson(store / 'US-MN.layer-records.json.gz', {'manifest': {}, 'made': 'x', 'records': recs or [ALPHA, BETA]})
    wjson(t / 'facts.json.gz', FACTS)
    wjson(t / 'base' / 'US-MN.json.gz', base or v1_key())
    return store, t / 'facts.json.gz'


def score(mut=None, v1s=None, lock='same', base=None, states=('MN',), recs=None, repo=ROOT, extra=None, facts_=None):
    """Build the tiny world, let `mut(key, proof, pino, run)` break it, return ({gate: ok}, S, notes, rows)."""
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        store, facts = write_world(t, base, recs)
        if facts_: wjson(facts, facts_)
        key, proof, pino, run = v2_data()
        if mut: mut(key, proof, pino, run)
        write_v2(t / 'v2', key, proof, pino, run)
        for nm_, txt_ in (extra or {}).items(): (t / 'v2' / nm_).write_text(txt_, encoding='utf-8')
        if 'SC' in states: wjson(t / 'base' / 'US-SC.json.gz', base or v1_key())
        gates, S, rows, notes = SC.build(t / 'v2', t / 'base', store, facts, list(states), v1s, repo, lock)
        score.last = (gates, SC.render(gates, S, list(states), notes))
        return {g[0]: g[1] for g in gates}, S, notes, rows


good, S, notes, rows = score(v1s={'MN': 100})
# 27 Nov 2026 (rule sheet 17): the gates are v2 by itself: G2 G3 G4 G5 G9 G10 G11. G1 G6 G7 G8 H1 H2 compared with v1: information only
check('good fixture: every gate passes; the gates are the seven on v2 by itself, none of the old v1 comparisons',
      all(good.values()) and sorted(good) == ['G10', 'G11', 'G2', 'G3', 'G4', 'G5', 'G9'])
check('good fixture: the park-by-park list is empty when v2 equals v1', rows == [])
check('outlined means joined records: v1 2 of 3, v2 2 of 3; confirmed v1 1, v2 2',
      (S['MN']['out1'], S['MN']['out2'], S['MN']['conf1'], S['MN']['conf2']) == (2, 2, 1, 2))


def add_old(k, pr, po, r): k['parks']['US-0001']['m'].append(['sgzz1~old', 'Alpha', 1, 'name'])
check('G2: a ~old id in a join fails', not score(add_old)[0]['G2'])
check('G2: a ~old id in a check row fails', not score(lambda k, pr, po, r: k['parks']['US-0003']['c'].append(['x~old', 'n', 1, 'check']))[0]['G2'])


def two_names(k, pr, po, r): k['parks']['US-0003']['m'] = [['sgzz1', 'Gamma Land', 5, 'name']]
g, S2, _, _ = score(two_names)
check('G3: one id on two parks under two names fails', not g['G3'] and S2['MN']['two'] == 1)


def same_name(k, pr, po, r): k['parks']['US-0003']['m'] = [['sgzz1', 'Alpha', 5, 'name']]
g, S2, _, _ = score(same_name)
check('G3: one id on two parks under the SAME record name is only counted (the allowed number); with different park names G3 fails on those', S2['MN']['samename'] == 1 and S2['MN']['two'] == 0 and not g['G3'])


def not_in_file(k, pr, po, r): pr[0]['file_key'] = 'sgzz99'
g, S2, _, _ = score(not_in_file)
check('G4: a joined key not in the layer files fails', not g['G4'] and S2['MN']['missing'] == 1)
check('G4: a joined key found in the layer file passes', good['G4'])


def drop_park(k, pr, po, r): del k['parks']['US-0003']; po.clear()
g, S2, _, _ = score(drop_park)
check('27 Nov: a park v1 has and v2 has not is no longer a gate (G1 dropped); the information block says so', all(g.values())
      and 'MN: parks v1 3, v2 2 (1 not in v2, 0 not in v1).' in score.last[1])


def many_checks(k, pr, po, r): k['parks']['US-0003']['c'] = [['a', 'b', 1, 'check'], ['c', 'd', 1, 'check']]
check('G5: check rows plus reasons above the pin-only parks fails', not score(many_checks)[0]['G5'])
check('G5: no check rows, one reason for one pin-only park passes', good['G5'])


def lose_outline(k, pr, po, r):
    k['parks']['US-0002'].update(m=[], ac=None); k['parks']['US-0002']['match'] = {'status': 'pin', 'by': None, 'step': 4, 'why': 'two_records_fit'}
    del pr[1]
    po.append({'ref': 'US-0002', 'st': 'MN', 'name': 'x', 'kind': 'x', 'reason_code': 'two_records_fit', 'reason': 'x'})
g, S2, _, rows = score(lose_outline)
check('27 Nov: fewer outlined parks than v1 is not a gate (was G6); the information block shows v1 2 -> v2 1', all(g.values()) and S2['MN']['out2'] == 1
      and 'Outlined v1 2 -> v2 1' in score.last[1])
check('park list: a lost outline is one row, with the reason code', len(rows) == 1 and rows[0]['difference'] == 'outline lost' and rows[0]['v2_reason'] == 'two_records_fit')


def less_confirmed(k, pr, po, r): k['parks']['US-0001']['match']['status'] = 'outlined'
base_c = v1_key(); base_c['parks']['US-0002']['match']['status'] = 'confirmed'
check('27 Nov: fewer confirmed parks than v1 is not a gate (was G7); the information block shows it',
      all(score(less_confirmed, base=base_c)[0].values()) and 'confirmed v1 2 -> v2 1' in score.last[1])


def slow(k, pr, po, r): r['MN']['seconds'] = 200.0
check('27 Nov: slower than v1 is not a gate (was G8); both times are in the information block',
      all(score(slow, v1s={'MN': 100})[0].values()) and 'Seconds: v1 100 s, v2 200 s.' in score.last[1])
check('27 Nov: no v1 time given = the information block says so, nothing fails', all(score(None)[0].values()) and '(v1 times not given)' not in score.last[1])


def gate_bad(k, pr, po, r): r['MN']['gate']['ok'] = False
def not_built(k, pr, po, r): r['MN']['not_built'] = 'layer sgzz is not complete'
check("G9: the matcher's own gate not ok fails", not score(gate_bad)[0]['G9'])
check('G9: a state not built fails', not score(not_built)[0]['G9'])
check('G9: a state with no run record fails', not score(lambda k, pr, po, r: r.clear())[0]['G9'])
check('G10: a lock check not run is NOT CHECKED and fails; same passes, differs fails, skipped passes (said so)',
      score(lock='same')[0]['G10'] and not score(lock='differs')[0]['G10'] and not score(lock='skipped')[0]['G10']
      and 'NOT CHECKED' in SC.lock_gate('skipped')[2] and SC.lock_gate('skipped', trial=True)[1] and 'not part of a trial' in SC.lock_gate('skipped', trial=True)[2])
g, S2, _, _ = score(states=('MN', 'NY'))
check('a missing v2 key for a typed state fails (G9 now, was G1) and the text says NO v2 KEY', not g['G9'] and 'NO v2 KEY NY' in score.last[1] and 'NY: NO v2 KEY' in score.last[1])

# the honest numbers
sqr = SC.decode_rings(ALPHA)
box = (-85.0, 38.0, -84.99, 38.01)
geom = [(box, sqr)]
check('rings decode: a 0.01 degree square with a closing point', len(sqr) == 1 and abs(sqr[0][2][0] - (-84.99)) < 1e-9 and abs(sqr[0][2][1] - 38.01) < 1e-9)
check('pin inside the square: yes', SC.pin_on_land(38.005, -84.995, geom))
check('pin 1 km outside: no', not SC.pin_on_land(38.019, -84.995, geom))
check('pin 50 m outside the edge: counts as on the land', SC.pin_on_land(38.01 + 50 / 110540.0, -84.995, geom))
check('pin 200 m outside the edge: no', not SC.pin_on_land(38.01 + 200 / 110540.0, -84.995, geom))
hole = [sqr[0], [(-84.997, 38.003), (-84.993, 38.003), (-84.993, 38.007), (-84.997, 38.007)]]
check('a hole in the shape is not land (even-odd)', not SC._inside(-84.995, 38.005, hole) and SC._inside(-84.9985, 38.005, hole))
check('size agrees: 100 vs 105 yes, 100 vs 150 no, nothing official = no',
      SC.size_agrees(100, [105]) and not SC.size_agrees(100, [150]) and not SC.size_agrees(100, []))
check('official sizes: the agency size and the page sizes marked total; not a size marked not total',
      SC.official_sizes({'size': {'acres': 10}, 'page': {'sizes': [{'acres': 20, 'total': True}, {'acres': 30, 'total': False}]}}) == [10.0, 20.0])
h1, h2 = S['MN']['h1'], S['MN']['h2']
good_h1_size = h1['size_yes']
check('honest numbers on the fixture: pin inside 1 of 2 (Alpha yes, Beta no), size agrees 1 of 2 (100 yes, 500 no), v1 = v2',
      (h1['pin_yes'], h1['pin_n'], h1['size_yes'], h1['size_n']) == (1, 2, 1, 2) and (h2['pin_yes'], h2['pin_n'], h2['size_yes'], h2['size_n']) == (1, 2, 1, 2))


def worse_pin(k, pr, po, r):
    k['parks']['US-0001']['m'] = [['sgzz2', 'Beta', 100, 'name']]; pr[0].update(file_key='sgzz2', record_name='Beta')
g, S2, _, rows = score(worse_pin)
check('27 Nov: v2 pin inside worse than v1 is not a gate (was H1); v2\'s own number is in its quality line with the count',
      'H1' not in g and S2['MN']['h2']['pin_yes'] == 0 and 'pin inside the land 0.0% (0 of 2)' in score.last[1])   # (G3 fails here: one record on two parks)


def worse_size(k, pr, po, r): k['parks']['US-0001']['ac'] = 300
g, S2, _, rows = score(worse_size)
check('27 Nov: one park off the official size passes (no gate); the list still shows the park (acres differ)',
      all(g.values()) and any(x['difference'] == 'acres differ' for x in rows))
two_ok = v1_key(); two_ok['parks']['US-0002']['ac'] = 500        # v1 size agrees for both parks (2 of 2)


def worse_size2(k, pr, po, r): k['parks']['US-0001']['ac'] = 300
g, S2, _, rows = score(worse_size2, base=two_ok)
check('27 Nov: v2 size agrees 0 of 2 against v1 2 of 2 passes (was H2); v2\'s own number is printed, the v1 one only in the information block',
      all(g.values()) and 'size agrees with the official size 0.0% (0 of 2)' in score.last[1].split('Gates (v2 by itself)')[0]
      and 'Size agrees: v1 100.0% (2 of 2), v2 0.0% (0 of 2)' in score.last[1].split('Next to the old key')[1])

# the store room gap
gap_base = v1_key(); gap_base['parks']['US-0003']['m'] = [['sgzz99', 'Gone', 5, 'name'], ['trl7', 'A trail', 0, 'line']]
g, S2, _, rows = score(base=gap_base)
txt = score.last[1]
check('store room gap: a park v1 drew only from records not in today\'s files is set apart; the information block prints both counts',
      all(g.values()) and S2['MN']['out1'] == 3 and S2['MN']['out1f'] == 2 and len(S2['MN']['gap']) == 1
      and 'Outlined v1 3 -> v2 2' in txt and '(1 parks set apart' in txt and 'fair count outlined 2 -> 2' in txt)
gl_ = next(l for l in txt.splitlines() if l.startswith('Store room gap:'))
check('store room gap (a v1 idea): its line is in the information block, how many, by state, and what kind (trail lines / other)',
      txt.index(gl_) > txt.index('Next to the old key') and 'Store room gap: 1 parks (MN 1)' in gl_ and 'trail lines 0, other 1' in gl_ and 'v2-store-gap.csv' in gl_)
check('store room gap: the park list calls it a store room gap, not an outline lost', [r['difference'] for r in rows] == ['store room gap'])
part_base = v1_key(); part_base['parks']['US-0003']['m'] = [['sgzz99', 'Gone', 5, 'name'], ['sgzz2', 'Beta', 5, 'name']]
g, S2, _, rows = score(base=part_base)
check('store room gap: a park where only SOME of v1\'s records are missing is NOT set apart (and nothing fails: not a gate now)',
      all(g.values()) and not S2['MN']['gap'])


def drew_other_way(k, pr, po, r):
    k['parks']['US-0003'].update(m=[['sgzz2', 'Beta', 5, 'name']], ac=5); k['parks']['US-0003']['match'] = {'status': 'confirmed', 'by': 'name+pin', 'step': 3, 'why': None}
    pr.append({'ref': 'US-0003', 'st': 'MN', 'file_key': 'sgzz2', 'agency_id': '', 'layer': 'sgzz', 'record_name': 'Beta', 'acres': 5, 'step': 3, 'by': 'x', 'evidence': ''})
    po.clear()
g, S2, _, _ = score(drew_other_way, base=gap_base)
check('store room gap: when v2 outlined such a park another way it counts as outlined and is not set apart', not S2['MN']['gap'] and S2['MN']['out2'] == 3)
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); store, facts = write_world(t, gap_base)
    key, proof, pino, run = v2_data(); write_v2(t / 'v2', key, proof, pino, run)
    with contextlib.redirect_stdout(io.StringIO()):
        SC.main(['--v2', str(t / 'v2'), '--base', str(t / 'base'), '--store', str(store), '--facts', str(facts), '--states', 'MN', '--repo', str(ROOT)])
    gc = list(csv.DictReader(open(t / 'v2' / 'v2-store-gap.csv', encoding='utf-8')))
    check('store room gap: v2-store-gap.csv has ref, state, name, v1 record ids, layer letters',
          len(gc) == 1 and gc[0]['ref'] == 'US-0003' and gc[0]['v1_record_ids'] == 'sgzz99 trl7' and gc[0]['layer_letters'] == 'sgzz trl' and gc[0]['name'] == 'Gamma Park')

# a state v2 did not build
def sc_nb(k, pr, po, r): r['SC'] = {'seconds': 0, 'gate': {}, 'not_built': 'layer sgzz is not complete'}
g, S2, _, _ = score(sc_nb, states=('MN', 'SC'))
txt = score.last[1]
check('not built: one plain line for the state, G9 fails, the other state is still judged and every other gate passes',
      not g['G9'] and all(v for k, v in g.items() if k != 'G9') and "SC: NOT BUILT, the store room's layer sgzz is not complete" in txt
      and 'MN: 3 parks' in txt and 'NOT BUILT SC' in txt)

# the lock check says which kind of difference it is
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    key, proof, pino, run = v2_data()
    write_v2(t / 'cold', key, proof, pino, run); write_v2(t / 'same', key, proof, pino, run)
    check('lock check: the same bytes = same', SC.lock_detail(t / 'cold', t / 'same', ['MN'])[0] == 'same')
    k2 = copy.deepcopy(key); k2['made'] = 'other label'; write_v2(t / 'label', k2, proof, pino, run)
    c, d, txt_, rws = SC.lock_detail(t / 'cold', t / 'label', ['MN'])
    check('lock check: different bytes, same joins = "only in labels", still differs (G10 fails), no csv rows',
          c == 'differs' and d == ['MN'] and txt_ == 'same joins, the files differ only in labels' and rws == []
          and not SC.lock_gate(c, d, txt_)[1] and 'only in labels' in SC.lock_gate(c, d, txt_)[2])
    k3 = copy.deepcopy(key)
    for n_ in range(7): k3['parks'][f'US-9{n_}'] = {'n': 'x', 'm': [[f'sgzz{n_}', 'x', 1, 'n']], 'match': {'status': 'confirmed'}}
    k3['parks']['US-0002']['m'] = [['sgzz1', 'Beta', 100, 'name']]
    write_v2(t / 'joins', k3, proof, pino, run)
    c, d, txt_, rws = SC.lock_detail(t / 'cold', t / 'joins', ['MN'])
    check('lock check: different joins = "joins differ in 8 parks"; at most 5 refs go to the csv rows',
          c == 'differs' and txt_.startswith('joins differ in 8 parks') and len(rws) == 5)
    with contextlib.redirect_stdout(io.StringIO()):
        store, facts = write_world(t / 'w')
        SC.main(['--v2', str(t / 'joins'), '--cold', str(t / 'cold'), '--base', str(t / 'w' / 'base'), '--store', str(store), '--facts', str(facts), '--states', 'MN', '--repo', str(ROOT)])
    lt = (t / 'joins' / 'V2-SCORECARD.txt').read_text(encoding='utf-8')
    check('lock check: through the command line: G10 FAIL says the joins differ, no refs in the text, v2-lock-diff.csv written',
          'G10 FAIL a lock changed an answer: joins differ in 8 parks' in lt and 'US-9' not in lt and (t / 'joins' / 'v2-lock-diff.csv').is_file())

# round 4: G3 by park name, G11, limits from the table, locks / other-names lines
def pine(k, pr, po, r):
    k['parks']['US-0001']['n'] = 'Alpha State Forest (Delaware County)'
    k['parks']['US-0003'].update(n='Alpha State Forest (Cattaraugus County)', m=[['sgzz1', 'Alpha', 100, 'name']], ac=100)
    k['parks']['US-0003']['match'] = {'status': 'confirmed', 'by': 'id', 'step': 2, 'why': None}; po.clear()
g, S2, _, _ = score(pine)
check('G3: one record on two parks whose park names differ only in the brackets FAILS (the record names are the same, so the old count is 0)',
      not g['G3'] and S2['MN']['two'] == 0 and S2['MN']['pdiff'] == 1 and S2['MN']['psame'] == 0)
check('G3: the text prints all three numbers', 'ids naming two records 0' in score.last[1] and 'different park names 1' in score.last[1] and 'very same park name 0' in score.last[1])


def same_park_name(k, pr, po, r):
    pine(k, pr, po, r); k['parks']['US-0003']['n'] = k['parks']['US-0001']['n']
g, S2, _, _ = score(same_park_name)
check('G3: one record on two parks with the very same park name is shown (1) and allowed', g['G3'] and S2['MN']['psame'] == 1 and S2['MN']['pdiff'] == 0)

TWO_PART = dict(ALPHA, rings=[sq(-85000000, 38000000), sq(-85505000, 38495000)])    # one record, two pieces, 60 km apart


def tracy(k, pr, po, r):
    k['parks']['US-0001'].update(n='Tracy Creek State Forest (Albany County)')
    k['parks']['US-0001']['match'] = {'status': 'confirmed', 'by': 'name+pin', 'step': 3, 'why': None}
    k['parks']['US-0003']['n'] = 'Tracy Creek State Forest (Essex County)'


g, S2, _, _ = score(tracy, recs=[TWO_PART, BETA])
check('G11: a two-piece record holding the pins of both same-named parks while only one park joins it FAILS, naming both parks and the record',
      not g['G11'] and [(x['park'], x['other_park'], x['record_key']) for x in S2['MN']['g11']] == [('US-0001', 'US-0003', 'sgzz1')])
g, S2, _, _ = score(tracy)
check('G11: with the one-piece record the other park\'s pin is not on it: passes', g['G11'])
g, S2, _, _ = score(lambda k, pr, po, r: (tracy(k, pr, po, r), k['parks']['US-0001']['match'].update(by='id')), recs=[TWO_PART, BETA])
check('G11: a park proven by id is not judged by this check', g['G11'])
g, S2, _, _ = score(lambda k, pr, po, r: k['parks']['US-0003'].update(n='Something Else'), recs=[TWO_PART, BETA])
check('G11: parks with different bare names never count', g['G11'])
tb = v1_key(); tb['parks']['US-0001'].update(n='Tracy Creek (Albany County)'); tb['parks']['US-0001']['match'] = {'status': 'confirmed', 'by': 'name'}
tb['parks']['US-0003']['n'] = 'Tracy Creek (Essex County)'
g, S2, _, _ = score(tracy, base=tb, recs=[TWO_PART, BETA])
check('G11: the same check on v1 is counted in the information block only (not a gate, not on the G11 line)', len(S2['MN']['g11_v1']) == 1
      and "v1 parks on a same-named park's land: 1 records" in score.last[1] and 'v1' not in next(l for l in score.last[1].splitlines() if l.startswith('G11 ')))
check('G11: counts only in the text (no park names), refs in the csv', 'Tracy' not in score.last[1])

with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    lim, note = SC.load_limits(ROOT)
    check('limits: pin_m and size_tol are read from the live rule table (dict values), no note', lim == {'pin_m': 100.0, 'size_tol': 0.1} and note == '')
    (t / 'a' / '.github').mkdir(parents=True)
    (t / 'a' / '.github' / 'us-key-v2-rules.json').write_text(json.dumps({'values': {'pin_m': {'value': 500, 'why': 'x'}, 'size_tol': 5}}))
    lim, note = SC.load_limits(t / 'a')
    check('limits: a dict value and a plain number are both read', lim == {'pin_m': 500.0, 'size_tol': 5.0} and note == '')
    lim, note = SC.load_limits(t / 'nowhere')
    check('limits: no table = the defaults and "defaults used" in one plain line', lim == {'pin_m': 100.0, 'size_tol': 0.1} and 'defaults used' in note and '\n' not in note)
    g, S2, notes2, _ = score(repo=t / 'nowhere')
    check('limits: the scorecard text says "defaults used"', any('defaults used' in n for n in notes2) and 'defaults used' in score.last[1])
    g, S2, notes2, _ = score(repo=t / 'a')
    check('limits: the table\'s tolerance is used (size_tol 5: v1 and v2 size agree 2 of 2; with 10% it is 1 of 2)',
          S2['MN']['h1']['size_yes'] == 2 and S2['MN']['h2']['size_yes'] == 2 and good_h1_size == 1)

# locks line and the other-names file; new columns are tolerated
def locks(k, pr, po, r):
    r['MN']['locks'] = {'held': 3, 'broken': 1, 'new': 2}
    for x in pr: x['lock'] = 'held'; x['step'] = 2
g, S2, _, _ = score(locks, extra={'v2-id-other-names.csv': 'st,ref,x\nMN,US-0001,a\nMN,US-0002,b\nNY,US-0009,c\n'})
check('locks: one line per state, "see v2-run.json" when broken > 0, a broken lock is not a gate; new proof columns are tolerated',
      'Locks: held 3, broken 1, new 2 (see v2-run.json)' in score.last[1] and all(g.values()))
check('other names file: its row count for the state is printed with the list name',
      "Id joins that carry another name, for the owner's eyes: 2 rows, list: v2-id-other-names.csv" in score.last[1])
g, S2, _, _ = score()
check('locks and other-names lines are left out when the matcher did not report them', 'Locks: not reported' in score.last[1] and 'carry another name' not in score.last[1])

# the id translation: a v1 id not in the file is counted, never a crash
miss_base = v1_key(); miss_base['parks']['US-0003']['m'] = [['sgzz99', 'Gone', 5, 'name'], ['trl7', 'A trail', 0, 'line']]
g, S2, _, _ = score(base=miss_base)
check('v1 ids that are not in today\'s file are counted (1 record, 1 trail line), no crash', S2['MN']['h1']['ids_missing'] == 2 and S2['MN']['h1']['ids_trail'] == 1)
# v1 ids of any date: three spellings, no legacy module
def recx(key, rid, name, su_id):
    return {'key': key, 'layer': 'sgmne', 'record_id': rid, 'record_name': name, 'attributes': {'objectid': int(rid), 'su_id': su_id}, 'q': 6, 'rings': [sq(-85000000, 38000000)]}


with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    # row 6 has agency id 99; row 7 has agency id 6: 'sgmne6' is row 6 by one spelling and agency 6 by another
    wjson(t / 'store' / 'US-MN.layer-records.json.gz', {'manifest': {}, 'records': [recx('sgmne6', '6', 'Row Six', 99), recx('sgmne7', '7', 'Agency Six', 6.0)]})
    st = SC.Store(t / 'store', {'sgmne': 'su_id'})
    nm = lambda r: None if r is None else 'AMBIG' if r is SC.AMBIGUOUS else r['record_name']
    f = lambda k, name=None: nm(st.find(k, ['US-MN'], name, v1=True))
    check('id spelling (a): the file\'s own key finds its record (sgmne7 = row 7)', f('sgmne7') == 'Agency Six')
    check('id spelling (b): layer + agency number with no zero (sgmne99 = agency 99 = row 6)', f('sgmne99') == 'Row Six')
    check('id spelling (c): layer + 0 + agency number (sgmne06 = agency 6 = row 7; sgmne099 = agency 99)', f('sgmne06') == 'Agency Six' and f('sgmne099') == 'Row Six')
    check('id spelling: sgmne6 fits row 6 AND agency 6: the v1 row name decides, either way, spelling and case aside',
          f('sgmne6', 'AGENCY six!') == 'Agency Six' and f('sgmne6', 'row six') == 'Row Six')
    check('id spelling: when the name does not choose, the id is AMBIGUOUS (counted, not guessed); an id nowhere is None',
          f('sgmne6', 'Something Else') == 'AMBIG' and f('sgmne6') == 'AMBIG' and f('sgmne555') is None)
    check('id spelling: a v2 lookup (file key only) never uses the agency spellings', nm(st.find('sgmne99', ['US-MN'])) is None and nm(st.find('sgmne6', ['US-MN'])) == 'Row Six')
    wjson(t / 'store2' / 'US-MN.layer-records.json.gz', {'manifest': {}, 'records': [recx('sgmne6', '6', 'One', 5), recx('sgmne7', '7', 'Two', 5)]})
    check('id spelling: two records with one agency id: v1 fell back to rows for them, so the agency spelling is not used',
          nm(SC.Store(t / 'store2', {'sgmne': 'su_id'}).find('sgmne5', ['US-MN'], v1=True)) is None)
    fl, note = SC.load_id_fields(ROOT)
    check('the agency id fields come from us-key-v2-rules.json (record_id_fields)', fl.get('sgmne') == 'su_id' and note == '')
    fl, note = SC.load_id_fields(t / 'nowhere')
    check('no rule table = no fields and one plain line, file keys only', fl == {} and 'not found' in note and '\n' not in note
          and nm(SC.Store(t / 'store', fl).find('sgmne99', ['US-MN'], v1=True)) is None)
    check('agency_digits: 89125.0 -> 89125, WMA0038200 -> 38200 (WMA), SFT00006 -> 6, 0 and empty -> none',
          SC.agency_digits({'attributes': {'SU_ID': 89125.0}}, 'su_id') == ('89125', '') and SC.agency_digits({'attributes': {'uniqueid': 'WMA0038200'}}, 'uniqueid') == ('38200', 'WMA')
          and SC.agency_digits({'attributes': {'sft': 'SFT00006'}}, 'sft') == ('6', 'SFT') and SC.agency_digits({'attributes': {'sft': 0}}, 'sft') == ('', '')
          and SC.agency_digits({'attributes': {}}, 'sft') == ('', ''))

# the scorecard never imports kpc_store_attrs: a broken fake first on the path must not matter
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    (t / 'fake').mkdir(); (t / 'fake' / 'kpc_store_attrs.py').write_text('raise RuntimeError("the scorecard must not import me")\n')
    sys.path.insert(0, str(t / 'fake')); sys.modules.pop('kpc_store_attrs', None)
    try:
        g_, S_, n_, r_ = score(v1s={'MN': 100})
        check('no kpc_store_attrs: with a broken fake first on sys.path the scorecard still runs, every gate passes, nothing imported it',
              all(g_.values()) and 'kpc_store_attrs' not in sys.modules)
    finally: sys.path.remove(str(t / 'fake'))
check('no kpc_store_attrs: the scorecard source has no import of it', 'import kpc_store_attrs' not in (ROOT / 'tools/pc-keys/kpc_v2_scorecard.py').read_text(encoding='utf-8'))

# a v1 id that fits two records and the name does not choose: counted, left out of the pin and size numbers
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    wjson(t / 'store' / 'US-MN.layer-records.json.gz', {'manifest': {}, 'records': [recx('sgmne6', '6', 'Row Six', 99), recx('sgmne7', '7', 'Agency Six', 6)]})
    wjson(t / 'facts.json.gz', FACTS)
    b = v1_key(); b['parks'] = {'US-0001': {'n': 'A', 'm': [['sgmne6', 'Other name', 100, 'name']], 'ac': 100, 'match': {'status': 'confirmed'}}}
    wjson(t / 'base' / 'US-MN.json.gz', b)
    kk, pr, po, rn = v2_data(); kk['parks'] = {'US-0001': kk['parks']['US-0001']}; pr[:] = pr[:1]; po.clear()
    write_v2(t / 'v2', kk, pr, po, rn)
    g_, S_, rows_, notes_ = SC.build(t / 'v2', t / 'base', t / 'store', t / 'facts.json.gz', ['MN'], None, ROOT)
    h = S_['MN']['h1']
    check('fit two records: counted (1), not counted as missing, left out of the pin numbers, and the park is not set apart as a store room gap',
          h['ids_fit2'] == 1 and h['ids_missing'] == 0 and h['pin_n'] == 0 and h['pin_cant'] == 1 and not S_['MN']['gap'])

# the two-name count is the PC test's own count
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    parks = {'A': {'m': [['x1', 'Alpha Lake', 1, 'n'], ['x2', 'Same', 1, 'n']]}, 'B': {'m': [['x1', 'Gamma Pond', 1, 'n'], ['x2', 'SAME!', 1, 'n']]}, 'C': {'m': [['x3', 'Solo', 1, 'n']]}}
    kf = t / 'US-MN.json'; kf.write_text(json.dumps({'parks': parks}), encoding='utf-8')
    line = K.wrong_land_lines(kf, t)[0]
    pc = tuple(int(x) for x in __import__('re').search(r'under two names (\d+), under the same name (\d+)', line).groups())
    check(f'the two-name count equals kpc_test_keys.wrong_land_lines ({pc})', SC.two_name_count(parks) == pc == (1, 1))

# the text and the list
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    store, facts = write_world(t)
    key, proof, pino, run = v2_data(); lose_outline(key, proof, pino, run); write_v2(t / 'v2', key, proof, pino, run)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = SC.main(['--v2', str(t / 'v2'), '--base', str(t / 'base'), '--store', str(store), '--facts', str(facts), '--states', 'mn',
                      '--v1-seconds', 'MN=100', '--repo', str(ROOT), '--lock-check', 'differs', '--lock-differs', 'MN'])
    txt = (t / 'v2' / 'V2-SCORECARD.txt').read_text(encoding='utf-8')
    cs = list(csv.DictReader(open(t / 'v2' / 'v2-vs-base.csv', encoding='utf-8')))
    check('exit code 1 and the first line says how many gates fail and which (a lost outline is not one of them now)', rc == 1 and txt.startswith('V2 DOES NOT PASS YET (1 gate: G10)\n'))
    check('the text has no park names and fits one screen', 'Alpha' not in txt and 'Beta' not in txt and len(txt.splitlines()) <= 40)
    check('v2-vs-base.csv has the names and the columns', cs and cs[0]['name'] == 'Beta Park' and list(cs[0]) == SC.CSV_COLS)
    key, proof, pino, run = v2_data(); write_v2(t / 'v2', key, proof, pino, run)
    with contextlib.redirect_stdout(io.StringIO()):
        rc = SC.main(['--v2', str(t / 'v2'), '--base', str(t / 'base'), '--store', str(store), '--facts', str(facts), '--states', 'MN', '--repo', str(ROOT), '--lock-check', 'same'])
    check('a good run: exit 0 and the first line is V2 PASSES', rc == 0 and (t / 'v2' / 'V2-SCORECARD.txt').read_text().startswith('V2 PASSES\n'))

# ---- 27 Nov 2026 (rule sheet 17), the owner: "why judge against crap work.. I need a system that works end to end and gives me
# excellent results": pass / fail is v2 by itself; v1 is for information only
def worse_everywhere(k, pr, po, r):
    lose_outline(k, pr, po, r)                     # fewer outlined and confirmed than v1
    k['parks']['US-0001']['ac'] = 300              # size agrees 0 of 1 against v1's 2 of 2
    k['parks']['US-0001']['m'] = [['sgzz2', 'Beta', 300, 'name']]; pr[0].update(file_key='sgzz2', record_name='Beta')   # pin not on its land
    r['MN']['seconds'] = 900.0                     # far slower than v1
bad_base = v1_key(); bad_base['parks']['US-0002']['ac'] = 500
bad_base['parks']['US-0004'] = {'n': 'Delta Park', 't': 'SP', 'm': [['sgzz1', 'Alpha', 100, 'name']], 'c': [], 'ac': 100, 'match': {'status': 'confirmed', 'by': 'id'}}
g, S2, _, _ = score(worse_everywhere, v1s={'MN': 100}, base=bad_base)
txt = score.last[1]
h1_, h2_ = S2['MN']['h1'], S2['MN']['h2']
check('27 Nov: a key worse than v1 on every old comparison (parks, outlined, confirmed, pin inside, size agrees, speed) PASSES when its own gates pass',
      all(g.values()) and txt.startswith('V2 PASSES\n') and S2['MN']['out2'] < S2['MN']['out1'] and S2['MN']['conf2'] < S2['MN']['conf1']
      and h2_['pin_yes'] * h1_['pin_n'] < h1_['pin_yes'] * h2_['pin_n'] and h2_['size_yes'] * h1_['size_n'] < h1_['size_yes'] * h2_['size_n']
      and S2['MN']['sec2'] > S2['MN']['sec1'] and not S2['MN']['same'][0])
top, rest = txt.split('\nGates (v2 by itself)\n')
gates_block, info = rest.split('\nNext to the old key (v1), for information only. Not part of pass or fail.\n')
check('27 Nov: the pass / fail line, the first lines and the gates block hold no v1 number (no "v1" at all); every v1 number is in the last block',
      'v1' not in top.replace('the old key (v1)', '') and 'v1' not in gates_block and 'Outlined v1 3 -> v2 1' in info and 'Seconds: v1 100 s, v2 900 s' in info
      and 'Pin inside the land: v1 ' in info and 'Size agrees: v1 ' in info and 'parks v1 4, v2 3' in info)
check('27 Nov: the first lines say outlined, pin only, the two quality numbers with counts, and the licence counts, in that order',
      top.splitlines()[3] == 'MN: 3 parks. Outlined 1, pin only 2. Confirmed 1.' and top.splitlines()[4].startswith('  Quality, not pass or fail (no limit is set yet')
      and 'pin inside the land 0.0% (0 of 1); size agrees with the official size 0.0% (0 of 1).' in top.splitlines()[4] and top.splitlines()[5].startswith('  Licence, what the club may show'))
check('27 Nov: no gate line names an old comparison (G1 G6 G7 G8 H1 H2), and the information lines start with no gate id',
      not re.search(r'^(G1|G6|G7|G8|H1|H2) ', txt, re.M) and not re.search(r'^(G|H)\d+ ', info, re.M))
g, S2, _, _ = score(lambda k, pr, po, r: (worse_everywhere(k, pr, po, r), add_old(k, pr, po, r)), v1s={'MN': 100}, base=bad_base)
check('27 Nov: the same key with one of its own gates failing (a ~old id, G2) still FAILS, and the first line names only that gate',
      not g['G2'] and [k_ for k_, v_ in g.items() if not v_] == ['G2'] and score.last[1].startswith('V2 DOES NOT PASS YET (1 gate: G2)\n'))
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    store, facts = write_world(t)
    key, proof, pino, run = v2_data(); write_v2(t / 'v2', key, proof, pino, run)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):    # no --base and no --no-base at all
        rc = SC.main(['--v2', str(t / 'v2'), '--store', str(store), '--facts', str(facts), '--states', 'MN', '--repo', str(ROOT), '--lock-check', 'same', '--v1-seconds', 'MN=1'])
    nt = (t / 'v2' / 'V2-SCORECARD.txt').read_text(encoding='utf-8')
    js = json.load(open(t / 'v2' / 'v2-score.json'))
    check('27 Nov: no v1 key at all (no --base): a full scorecard, exit 0, the seven gates, the quality line, no information block, no "v1" anywhere',
          rc == 0 and nt.startswith('V2 PASSES\n') and len(js['gates']) == 7 and 'pin inside the land 50.0% (1 of 2)' in nt and 'Licence, what the club may show' in nt
          and 'Next to the old key' not in nt and 'v1' not in nt.replace('the old key (v1)', '') and js['areas']['MN']['has_v1'] is False)


# ---------------------------------------------------------------- the side-by-side runner
FAKE = r'''import argparse, gzip, pathlib, shutil, sys
ap = argparse.ArgumentParser()
ap.add_argument('--states', nargs='+'); ap.add_argument('--areas', nargs='+'); ap.add_argument('--store'); ap.add_argument('--facts'); ap.add_argument('--out')
ap.add_argument('--locks'); ap.add_argument('--write-locks', action='store_true'); ap.add_argument('--repo'); ap.add_argument('--rules')
a = ap.parse_args()
import json
if a.rules:
    rl = json.loads(pathlib.Path(a.rules).read_text())
    if rl.get('refuse'): print('rule table refused: row 3 has no why'); sys.exit(2)
fx, out = pathlib.Path(__FIX__), pathlib.Path(a.out)
mode = (pathlib.Path(__file__).with_name('fake_mode.txt').read_text().strip() if pathlib.Path(__file__).with_name('fake_mode.txt').exists() else 'ok')
out.mkdir(parents=True, exist_ok=True)
for f in fx.iterdir(): shutil.copyfile(f, out / f.name)
if a.areas and mode == 'crash_ca': print('boom'); sys.exit(1)
if a.areas:
    ar = a.areas[0]
    shutil.copyfile(out / 'US-MN.json.gz', out / (ar + '.json.gz')); (out / 'US-MN.json.gz').unlink()
    rj = out / 'v2-run.json'; d = json.loads(rj.read_text()); d['states'] = {ar: d['states']['MN']}; d['areas'] = d['states']; rj.write_text(json.dumps(d))
    for fn in ('v2-proof.csv', 'v2-pin-only.csv'): (out / fn).write_text((out / fn).read_text().replace('MN', ar))
if a.write_locks:
    (out / 'locks').mkdir(); (out / 'locks' / 'US-MN.json').write_text('{"locks": {}}')
if a.locks and mode == 'warm_differs':
    with gzip.open(out / 'US-MN.json.gz', 'ab') as g: g.write(b' ')
if a.rules:
    kp = out / 'US-MN.json.gz'
    k = json.load(gzip.open(kp, 'rt'))
    for ref in rl.get('gain', []): k['parks'][ref].update(m=[['sgzz2', 'Beta', 50, 'name']], ac=50); k['parks'][ref]['match'] = {'status': 'confirmed', 'by': 'name+pin', 'step': 3, 'why': None}
    for ref in rl.get('lose', []): k['parks'][ref].update(m=[], ac=None); k['parks'][ref]['match'] = {'status': 'pin', 'by': None, 'step': 4, 'why': 'two_records_fit'}
    for ref in rl.get('land', []): k['parks'][ref]['ac'] = k['parks'][ref]['ac'] * 2
    k['tool'] = 'fake (trial rules)'
    with gzip.GzipFile(kp, 'wb', mtime=0) as g: g.write(json.dumps(k, sort_keys=True).encode())
if mode == 'exit3':
    import json
    rj = out / 'v2-run.json'; d = json.loads(rj.read_text()); d['states']['SC'] = {'seconds': 0, 'gate': {}, 'not_built': 'layer sgzz is not complete'}
    rj.write_text(json.dumps(d)); print('SC: not built'); sys.exit(3)
print('MN: built (fake)')
'''


def make_kit(t, mode='ok', with_v2=True):
    kit = t / 'kit'; (kit / 'reports').mkdir(parents=True)
    shutil.copyfile(ROOT / 'tools' / 'pc-keys' / 'kpc_v2_scorecard.py', kit / 'kpc_v2_scorecard.py')
    wjson(kit / 'park-facts.json.gz', FACTS)
    wjson(t / '3-MAP-STORE-US-CA' / 'results' / 'store' / 'US-MN.layer-records.json.gz', {'manifest': {}, 'made': 'x', 'records': [ALPHA, BETA]})
    fx = t / 'fixture'; fx.mkdir()
    write_v2(fx, *v2_data())
    if with_v2:
        sd = kit / 'links' / '.github' / 'scripts'; sd.mkdir(parents=True)
        (sd / 'kpc_us_key_v2.py').write_text(FAKE.replace('__FIX__', repr(str(fx))), encoding='utf-8')
        (sd / 'fake_mode.txt').write_text(mode)
    for name, mins, keys in (('test-2026-11-26-1000', '4.0', True), ('test-2026-11-26-1100', '2.5', True), ('test-2026-11-26-1200', '9.0', False),
                             ('v2-2026-11-26-1300', '1.0', True)):
        r = kit / 'reports' / name; r.mkdir()
        (r / 'REPORT.txt').write_text(f'KPC test keys.\n\nMN: built in {mins} minutes (exit 0).\n  more\n', encoding='utf-8')
        if keys: wjson(r / 'keys' / 'US-MN.json.gz', v1_key()); wjson(r / 'keys' / 'US-SC.json.gz', v1_key())
    return kit


def snapshot(root):
    return {str(p.relative_to(root)): (p.stat().st_size, p.stat().st_mtime_ns) for p in sorted(root.rglob('*')) if p.is_file()}


def run_runner(kit, argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = RUN.main(argv, here=kit)
    return rc, buf.getvalue()


with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    kit = make_kit(t)
    reps = kit / 'reports'
    check('runner: the newest test that holds keys for every state is the baseline (not a newer one without keys, not a v2- folder)',
          RUN.find_baseline(reps, ['MN']).name == 'test-2026-11-26-1100' and RUN.find_baseline(reps, ['MN'], 'test-2026-11-26-1000').name == 'test-2026-11-26-1000'
          and RUN.find_baseline(reps, ['MN', 'NY']) is None)
    check('runner: v1 minutes are read from REPORT.txt lines ("MN: built in 2.5 minutes") and become seconds',
          RUN.v1_minutes('x\nMN: built in 4.2 minutes (exit 0).\n', 'MN') == 4.2 and RUN.v1_minutes('NY: built in 3.0 minutes', 'MN') is None
          and RUN.v1_seconds(reps / 'test-2026-11-26-1100', ['MN', 'NY']) == {'MN': 150.0})
    before = snapshot(t)
    rc, out = run_runner(kit, ['MN'])
    after = snapshot(t)
    new = [k for k in after if k not in before]
    check('runner: good fake v2 = exit 0, the scorecard says V2 PASSES, the cold and warm runs are the same', rc == 0 and 'V2 PASSES' in out and 'The two runs: same' in out)
    check('runner: it says which v1 test it compared with', 'test-2026-11-26-1100' in out)
    check('runner: it wrote only into its own new reports\\v2-<time> folder (cold, warm, the scorecard, the list)',
          new and all(k.startswith('kit/reports/v2-2') for k in new) and {k for k in before if k in after and before[k] != after[k]} == set()
          and any(k.endswith('V2-SCORECARD.txt') for k in new) and any(k.endswith('v2-vs-base.csv') for k in new) and any('/cold/locks/US-MN.json' in k for k in new))
    check('runner: the scorecard received the v1 seconds (150 s) and the lock result', 'v1 150 s' in out and 'G10 PASS' in out)

with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    kit = make_kit(t, mode='warm_differs')
    rc, out = run_runner(kit, ['MN'])
    check('runner: a warm key that differs from the cold key = G10 FAIL, exit 1, and it names the state',
          rc == 1 and 'The two runs: differs (MN differ)' in out and 'G10 FAIL' in out and 'only in labels' in out and 'V2 DOES NOT PASS YET' in out)
    cmpd = RUN.lock_compare(t / 'a', t / 'b', ['MN'])
    check('runner: no keys to compare = skipped', cmpd == ('skipped', []))

with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    kit = make_kit(t, mode='exit3')
    rc, out = run_runner(kit, ['MN', 'SC'])
    check('runner: the matcher exits 3 for one state: the scorecard still runs for the other, says SC NOT BUILT, G9 fails, exit 1',
          rc == 1 and '(exit 3)' in out and "SC: NOT BUILT, the store room's layer sgzz is not complete" in out and 'MN: 3 parks' in out
          and 'G9 FAIL' in out and 'G2 PASS' in out)

with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    kit = make_kit(t, with_v2=False)
    real_fl = RUN.find_links
    RUN.find_links = lambda here: here / 'links'      # isolated: no matcher anywhere it can be found, whatever folder the repo sits in
    try: rc, out = run_runner(kit, ['MN'])
    finally: RUN.find_links = real_fl
    check('runner: the v2 script missing = one plain line, exit 2, no new folder', rc == 2 and len(out.strip().splitlines()) == 1
          and 'not on this PC' in out and len(list((kit / 'reports').glob('v2-2*'))) == 1)   # only the one the fixture made
    kit2 = make_kit(t / 'again')
    rc, out = run_runner(kit2, ['MN', 'NY'])
    check('runner: no v1 test with keys for every typed state = exit 2, nothing run', rc == 2 and 'No earlier v1 test' in out and len(list((kit2 / 'reports').glob('v2-2*'))) == 1)


# the TRY A RULE workbench
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    kit = make_kit(t)
    (t / 'my-rules.json').write_text(json.dumps({'gain': ['US-0003'], 'lose': ['US-0002'], 'land': ['US-0001']}))
    before = snapshot(t)
    rc, out = run_runner(kit, ['MN', '--try', str(t / 'my-rules.json')])
    after = snapshot(t)
    new = [k for k in after if k not in before]
    rd = [d for d in (kit / 'reports').glob('v2-try-2*')]
    check('try mode: exit 0, one new reports\\v2-try-<time> folder with now, try, TRY-REPORT.txt and try-changes.csv', rc == 0 and len(rd) == 1
          and (rd[0] / 'now' / 'US-MN.json.gz').is_file() and (rd[0] / 'try' / 'US-MN.json.gz').is_file() and (rd[0] / 'TRY-REPORT.txt').is_file() and (rd[0] / 'try-changes.csv').is_file())
    check('try mode: nothing outside its own new folder was created or changed (the rules file, the kit, the store, the real baseline)',
          new and all(k.startswith('kit/reports/v2-try-2') for k in new) and not [k for k in before if k in after and before[k] != after[k]])
    rep_txt = (rd[0] / 'TRY-REPORT.txt').read_text(encoding='utf-8')
    rows_ = list(csv.DictReader(open(rd[0] / 'try-changes.csv', encoding='utf-8')))
    check('try mode: the report counts parks that gain (1), lose (1), and change their land by more than 10% (1), pin-only reasons before and after',
          'MN: gain an outline 1, lose one 1, joined land changes by more than 10%: 1.' in rep_txt and 'Pin-only reasons now: no_record_with_this_name 1.' in rep_txt
          and 'with the trial rules: no_record_with_this_name 1, two_records_fit 1' not in rep_txt and 'two_records_fit 1.' in rep_txt)
    check('try mode: try-changes.csv has one row per changed park with before / after status, by and acres',
          {(r['ref'], r['change']) for r in rows_} == {('US-0003', 'gains an outline'), ('US-0002', 'loses its outline'), ('US-0001', 'joined land changes by more than 10%')}
          and next(r for r in rows_ if r['ref'] == 'US-0001')['before_acres'] == '100.0' and next(r for r in rows_ if r['ref'] == 'US-0001')['after_acres'] == '200.0'
          and next(r for r in rows_ if r['ref'] == 'US-0003')['after_status'] == 'confirmed' and next(r for r in rows_ if r['ref'] == 'US-0002')['before_status'] == 'confirmed')
    check('try mode: the matcher\'s gate and the scorecard verdicts for both runs, the lock check is not part of a trial (no G10 failure)',
          "The matcher's own gate on the trial run: ok." in rep_txt and 'Scorecard, real rules: V2 PASSES' in rep_txt and 'Scorecard, trial rules: V2 PASSES' in rep_txt
          and 'G10' not in rep_txt and 'Lock check not part of a trial' in rep_txt and (rd[0] / 'score-try' / 'V2-SCORECARD.txt').is_file()
          and 'lock check not part of a trial' in (rd[0] / 'score-try' / 'V2-SCORECARD.txt').read_text(encoding='utf-8'))
    check('try mode: the last lines say nothing real changed and how to make it real',
          rep_txt.rstrip().splitlines()[-2] == 'This changed nothing in the real key or the real rule table.'
          and rep_txt.rstrip().splitlines()[-1].startswith('To make it real: put the row in .github/us-key-v2-rules.json with its why and its test, and open a PR'))
    check('try mode: the report fits one screen', len(rep_txt.splitlines()) <= 25)
    (t / 'bad.json').write_text(json.dumps({'refuse': True}))
    rc, out = run_runner(kit, ['MN', '--try', str(t / 'bad.json')])
    check('try mode: a refused table (matcher exit 2) shows the matcher\'s one line and stops, exit 2, no report',
          rc == 2 and 'The matcher refused the trial rules: rule table refused: row 3 has no why' in out
          and not [d for d in (kit / 'reports').glob('v2-try-2*') if (d / 'TRY-REPORT.txt').is_file() and d != rd[0]])
    rc, out = run_runner(kit, ['MN', '--try', str(t / 'nope.json')])
    check('try mode: a rules file that is not there = one plain line, exit 2', rc == 2 and 'Not found: the trial rules file' in out)

src = (ROOT / 'tools' / 'pc-keys' / 'kpc_test_v2.py').read_text(encoding='utf-8')
check('runner: nothing is downloaded or uploaded (no network words in its code)', not any(w in src for w in ('urllib', 'requests', 'http.client', 'socket', 'ftplib')))
bat = (ROOT / 'tools' / 'pc-keys' / 'V2-SIDE-BY-SIDE.bat').read_bytes()
check('the .bat has CRLF line ends, asks for states, tries Python 3.12 first, has no pip step', b'\r\n' in bat and b'\n' not in bat.replace(b'\r\n', b'')
      and b'py -3.12' in bat and b'pip' not in bat and b'set "ST=MN NY"' in bat and b'kpc_test_v2.py' in bat)   # default MN NY: SC waits for its sgnca layer

# ---- H3 (same land as v1): tiny squares, a report only
def _sqg(x0, y0, w):   # a square w degrees wide, as (box, rings)
    ring = [(x0, y0), (x0 + w, y0), (x0 + w, y0 + w), (x0, y0 + w)]
    return ((x0, y0, x0 + w, y0 + w), [ring])
a1, a2, m1, m2 = SC.land_pair([_sqg(-85.0, 38.0, 0.01)], [_sqg(-85.0, 38.0, 0.01)])
check('H3: the same square on both sides is a full cover both ways (nothing missing)', a1 > 100 and abs(a1 - a2) < 1e-6 and m1 == 0 and m2 == 0)
a1, a2, m1, m2 = SC.land_pair([_sqg(-85.0, 38.0, 0.01)], [_sqg(-85.0, 38.0, 0.005)])
check('H3: v2 holds a quarter of v1\'s square: v1 land not in v2 is about 3/4 of v1; v2 land not in v1 is 0', 0.70 < m1 / a1 < 0.80 and m2 == 0)
a1, a2, m1, m2 = SC.land_pair([_sqg(-85.0, 38.0, 0.01)], [_sqg(-85.0, 38.0, 0.01 / 2 ** 0.5)])
check('H3: a half cover (v2 is a half-area square inside v1)', 0.45 < m1 / a1 < 0.55 and m2 == 0)
a1, a2, m1, m2 = SC.land_pair([_sqg(-85.0, 38.0, 0.01)], [_sqg(-84.0, 39.0, 0.01)])
check('H3: two squares far apart share nothing (the boxes say so before any grid)', m1 == a1 and m2 == a2 and a1 > 100)

# ---- round 6: names the v1 test, key text hashes, other-names copy, no-base mode, lines
def cli(t, extra_args, mut=None, run_extra=None, other_names=True, recs=None, facts_=None):
    store, facts = write_world(t, None, recs)
    if facts_: wjson(facts, facts_)
    key, proof, pino, run = v2_data()
    if mut: mut(key, proof, pino, run)
    if run_extra: run['MN'].update(run_extra)
    write_v2(t / 'v2', key, proof, pino, run)
    if other_names: (t / 'v2' / 'v2-id-other-names.csv').write_text('st,ref\nMN,US-0001\n', encoding='utf-8')
    out = t / 'report'
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = SC.main(['--v2', str(t / 'v2'), '--store', str(store), '--facts', str(facts), '--states', 'MN', '--out', str(out), '--no-land'] + extra_args)
    return rc, out, buf.getvalue()


with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    wjson(t / 'test-2026-11-26-2014' / 'keys' / 'US-MN.json.gz', v1_key())
    rc, out, text = cli(t, ['--base', str(t / 'test-2026-11-26-2014' / 'keys')], run_extra={'key_text_sha256': 'ab' * 32})
    lines = (out / 'V2-SCORECARD.txt').read_text(encoding='utf-8').splitlines()
    check('27 Nov: the scorecard names the v1 test in the information block (under its heading), not in the first lines',
          'Compared with: test-2026-11-26-2014' in lines and lines.index('Compared with: test-2026-11-26-2014') == lines.index('Next to the old key (v1), for information only. Not part of pass or fail.') + 1
          and not any('Compared with' in l for l in lines[:5]))
    check('the scorecard prints each area\'s key_text_sha256 from v2-run.json when present', any('MN ' + 'ab' * 32 in l for l in lines[:6]))
    check('the warm run\'s v2-id-other-names.csv is copied into the report folder and the text points to it there', (out / 'v2-id-other-names.csv').is_file()
          and 'list: v2-id-other-names.csv' in '\n'.join(lines))
    check('no key text hash in v2-run.json = no hash line', 'sha256' not in (lambda: (cli(t / 'x', ['--base', str(t / 'test-2026-11-26-2014' / 'keys')])[2]))())

with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    def stray(k, pr, po, r): k['parks']['US-0002']['m'] = []; k['parks']['US-0002']['match'] = {'status': 'pin', 'by': None, 'step': 4, 'why': 'two_records_fit'}; del pr[1]; po.append({'ref': 'US-0002', 'st': 'MN', 'name': 'x', 'kind': 'x', 'reason_code': 'two_records_fit', 'reason': 'x'})
    rc, out, text = cli(t, ['--no-base'], mut=stray)
    gl = {l.split()[0]: l for l in (out / 'V2-SCORECARD.txt').read_text(encoding='utf-8').splitlines() if re.match(r'^(G|H)\d+ ', l)}
    num = json.load(open(out / 'v2-score.json'))['areas']['MN']
    check('no-base mode: the seven gates on v2 by itself run, no G1 / G6 / G7 / G8 / H1 / H2 line, and no information block',
          sorted(gl) == ['G10', 'G11', 'G2', 'G3', 'G4', 'G5', 'G9'] and 'Next to the old key' not in text)
    check('no-base mode: the area is reported on its own by reason and step; no v2-vs-base rows',
          'Pin only, by reason: no_record_with_this_name 1, two_records_fit 1' in text
          and num['nobase'] and num['why'] == {'no_record_with_this_name': 1, 'two_records_fit': 1} and num['step'] == {'step 2': 1} and len(list(csv.DictReader(open(out / 'v2-vs-base.csv')))) == 0)

with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    # a line: paths and no rings. The pin of US-0001 is ~11 m east of the line (0.0001 degree of longitude at 38 N is about 8.8 m)
    line = {'key': 'sgzz1', 'layer': 'sgzz', 'record_id': '1', 'record_name': 'Alpha', 'attributes': {}, 'q': 6, 'shape': 'line', 'paths': [[-85000000, 38000000, 0, 10000]]}
    def near(k, pr, po, r): pass
    f1 = json.loads(json.dumps(FACTS)); f1['parks']['US-0001']['pin'] = [38.005, -84.9999]
    rc, out, text = cli(t, ['--no-base'], recs=[line, BETA], facts_=f1)
    n1 = json.load(open(out / 'v2-score.json'))['areas']['MN']
    f2 = json.loads(json.dumps(FACTS)); f2['parks']['US-0001']['pin'] = [38.005, -84.998]
    rc, out2, text2 = cli(t / 'two', ['--no-base'], recs=[line, BETA], facts_=f2)
    n2 = json.load(open(out2 / 'v2-score.json'))['areas']['MN']
    check('lines: a pin within line_pin_m (30.48 m) of a line (paths, no rings) counts as on it; 170 m away does not', n1['pin_yes'] == 1 and n2['pin_yes'] == 0 and n1['pin_n'] == n2['pin_n'] == 2)
    check('lines: a park whose records are all lines is left out of the size numbers', n1['size_n'] == 1)
    check('lines: decode_paths reads two points as a path; is_line needs paths and no rings', len(SC.decode_paths(line)[0]) == 2 and SC.is_line(line) and not SC.is_line(ALPHA))
    check('lines: line_m is metres to the nearest segment (about 8.8 m for 0.0001 degree at 38 N)', 8 < SC.line_m(-84.9999, 38.005, SC.decode_paths(line)) < 10)

# ---- the BUILD mode of the runner: real keys, one area per child process, a summary, a pin-only chart
def build_world(t, mode='ok'):
    kit = make_kit(t, mode)
    st = t / '3-MAP-STORE-US-CA' / 'results' / 'store'
    shutil.copyfile(st / 'US-MN.layer-records.json.gz', st / 'CA-ON.layer-records.json.gz')
    shutil.copyfile(st / 'US-MN.layer-records.json.gz', st / 'CA-QC.layer-records.json.gz')
    return kit


with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    kit = build_world(t)
    calls = []
    real_sub = RUN.subprocess.run

    def rec_run(cmd, *a, **k):
        calls.append(list(cmd)); return real_sub(cmd, *a, **k)
    before = snapshot(kit / 'reports')
    RUN.subprocess.run = rec_run
    try: rc, out = run_runner(kit, ['build', 'MN', 'CA-ON', 'SC'])
    finally: RUN.subprocess.run = real_sub
    runs = sorted((kit / 'v2-keys').iterdir())
    check('build: one run folder v2-keys\\<date-time> beside the reports folder; the v1 tests in reports are not touched', len(runs) == 1 and snapshot(kit / 'reports') == before)
    run = runs[0]
    sm = (run / 'V2-BUILD-SUMMARY.txt').read_text(encoding='utf-8').splitlines()
    check('build: the summary starts with how many were built; one line per area; a state with no layer file is "not built (no layer file)"',
          sm[0].startswith('v2 built 2 of 3 areas') and any(l.startswith('MN ') and ' built ' in l for l in sm) and any(l.startswith('CA-ON ') for l in sm)
          and any(l.startswith('SC ') and 'not built (no layer file)' in l for l in sm))
    mn = next(l for l in sm if l.startswith('MN '))
    ca = next(l for l in sm if l.startswith('CA-ON '))
    check('build: with a v1 key the line says outlined of parks, pin inside, v1 outlined and the v1 test; without one it says no v1 key to compare with',
          'outlined 2 of 3' in mn and 'pin inside' in mn and 'v1 outlined 2' in mn and 'test-2026-11-26-1100' in mn and 'outlined 2 of 3' in ca and 'no v1 key to compare with' in ca)
    check('build: each area runs in its own child (cold, then warm, then the scorecard); US by --states, Canada by --areas; v1 matched only by the area name',
          sum(1 for c in calls if '--write-locks' in c) == 2 and sum(1 for c in calls if '--locks' in c) == 2 and sum(1 for c in calls if str(c[3]).endswith('kpc_v2_scorecard.py')) == 2
          and any('--states' in c and 'MN' in c for c in calls) and any('--areas' in c and 'CA-ON' in c for c in calls) and not any('--areas' in c and '--states' in c for c in calls)
          and any('--no-base' in c for c in calls) and any('--base' in c and 'test-2026-11-26-1100' in str(c) for c in calls))
    po = list(csv.DictReader(open(run / 'pin-only-all.csv', encoding='utf-8')))
    check('build: pin-only-all.csv lists every pin-only park of the run with its area and reason', {(r['area'], r['ref']) for r in po} == {('US-MN', 'US-0003'), ('CA-ON', 'US-0003')} and po[0]['reason_code'] == 'no_record_with_this_name')
    sc = list(csv.DictReader(open(run / 'summary.csv', encoding='utf-8')))
    check('build: summary.csv has one row per area; the built keys are copied into keys\\; each area has cold, warm and its scorecard',
          [r['area'] for r in sc] == ['US-MN', 'CA-ON', 'US-SC'] and sc[0]['outlined'] == '2' and (run / 'keys' / 'US-MN.json.gz').is_file() and (run / 'keys' / 'CA-ON.json.gz').is_file()
          and all((run / a / x).exists() for a in ('US-MN', 'CA-ON') for x in ('cold', 'warm', 'V2-SCORECARD.txt')))
    check('build: progress lines say "1 of 3  MN  N s  built"', any(re.match(r'^1 of 3  MN  \d+ s  built', l) for l in out.splitlines()) and any(re.match(r'^3 of 3  SC  0 s  not built', l) for l in out.splitlines()))
    check('build: exit 1 when an area could not be built (SC), the others were built', rc == 1)
    # 27 Nov 2026: licence counts on the build summary (the fake matcher's keys carry no licence word, so every outlined park counts as none)
    check('build summary: each built area line carries its licence counts, and one total line follows with the plain-words legend',
          'licence: share all 0, part 0, none 2' in mn and 'licence: share all 0, part 0, none 2' in ca
          and any(l.startswith('Licence, what the club may show, total over 2 areas: share all 0, share part 0, share none 4 (of 4 outlined parks).') and '4 had no licence word' in l for l in sm)
          and any('share all = every record of the park may be shown' in l for l in sm))
    check('build summary: summary.csv has share_all, share_part, share_none per area', sc[0]['share_all'] == '0' and sc[0]['share_none'] == '2' and 'share_part' in sc[0])
    check('27 Nov build summary: a line per area gives outlined, pin only, the two quality numbers with counts, licence, the gates; v1 only after "| for information"',
          'outlined 2 of 3, pin only 1  pin inside 50.0% (1 of 2)  size agrees 50.0% (1 of 2)  licence:' in mn and 'gates: all pass' in mn
          and mn.index('| for information: v1 outlined 2') > mn.index('gates: all pass') and 'v1' not in mn.split('| for information')[0]
          and ca.endswith('| no v1 key to compare with') and any('Pass or fail is judged on v2 by itself' in l for l in sm[:3]))
    check('27 Nov build summary: summary.csv keeps every column, the v1 columns last; gates_failed is empty (only the gates on v2 by itself)',
          list(sc[0])[-2:] == ['v1_test', 'v1_outlined'] and len(sc[0]) == 18 and sc[0]['gates_failed'] == '' and sc[0]['v1_outlined'] == '2' and sc[1]['v1_outlined'] == '')

with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    kit = build_world(t, 'crash_ca')
    rc, out = run_runner(kit, ['build', 'CA-ON', 'MN'])
    run = next((kit / 'v2-keys').iterdir())
    check('build: a crashing area does not stop the run: it gets build-error.txt and one line, the next area is built',
          (run / 'CA-ON' / 'build-error.txt').is_file() and 'stopped with an error, see CA-ON\\build-error.txt' in (run / 'V2-BUILD-SUMMARY.txt').read_text(encoding='utf-8')
          and (run / 'keys' / 'US-MN.json.gz').is_file() and rc == 1)
    t2 = t / 'again'
    rc, out = run_runner(build_world(t2), ['build', 'ALL'])
    run = next((t2 / 'kit' / 'v2-keys').iterdir())
    check('build: ALL = every area with a layer file (US and Canada), US = only the states, CA = only Canada',
          RUN.parse_areas(['ALL'], t2 / '3-MAP-STORE-US-CA' / 'results' / 'store') == ['CA-ON', 'CA-QC', 'US-MN'] and RUN.parse_areas(['us'], t2 / '3-MAP-STORE-US-CA' / 'results' / 'store') == ['US-MN']
          and RUN.parse_areas(['CA'], t2 / '3-MAP-STORE-US-CA' / 'results' / 'store') == ['CA-ON', 'CA-QC'] and (run / 'V2-BUILD-SUMMARY.txt').is_file())
    rc, out = run_runner(build_world(t / 'enter'), ['build'])
    sm2 = (next((t / 'enter' / 'kit' / 'v2-keys').iterdir()) / 'V2-BUILD-SUMMARY.txt').read_text(encoding='utf-8')
    check('build: nothing typed means MN NY (MN built, NY has no layer file here)', any(l.startswith('MN ') and ' built ' in l for l in sm2.splitlines()) and 'NY     not built (no layer file)' in sm2)
bb = (ROOT / 'tools' / 'pc-keys' / 'V2-BUILD.bat').read_bytes()
check('V2-BUILD.bat: CRLF, the prompt, Python 3.12 first, Enter = MN NY, runs build mode, no pip', b'\r\n' in bb and b'\n' not in bb.replace(b'\r\n', b'') and b'Areas (for example MN NY, or CA-ON, or US, CA, ALL): ' in bb
      and b'py -3.12' in bb and b'set "ST=MN NY"' in bb and b'kpc_test_v2.py build %ST%' in bb and b'pip' not in bb)

# ---- Canadian record keys: "<label>:<n>" (a label with spaces) and bare CPCAD numbers
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    r1 = dict(rec('NS HRM Parks:1', 'Point Pleasant', -63600000, 44600000, layer='NS HRM Parks'), record_id='1')
    r2 = dict(rec('88', 'Kejimkujik', -65000000, 44400000, layer='CPCAD'), record_id='88')
    wjson(t / 'store' / 'CA-NS.layer-records.json.gz', {'manifest': {}, 'made': 'x', 'records': [r1, r2]})
    st = SC.Store(t / 'store', {})
    check('Canadian keys: "NS HRM Parks:1" and the bare CPCAD number "88" are found by the file\'s own key in the area\'s file (CA-NS)',
          st.find('NS HRM Parks:1', ['CA-NS']) is not None and st.find('88', ['CA-NS'])['record_name'] == 'Kejimkujik' and st.find('89', ['CA-NS']) is None
          and SC.aname('CA-NS') == 'CA-NS' and SC.aname('MN') == 'US-MN')

# ---- 27 Nov 2026: licence counts (share all / part / none) on the scorecard
def marked(k, pr, po, r):
    k['parks']['US-0001']['share'] = 'all'; k['parks']['US-0002']['share'] = 'part'; k['parks']['US-0003']['share'] = 'all'   # US-0003 is pin only: not counted


score(marked, v1s={'MN': 100})
txt = score.last[1]
check('licence counts: one line per area in plain words, only outlined parks counted (pin only ignored)',
      '  Licence, what the club may show: share all 1, share part 1, share none 0 (of 2 outlined parks).' in txt)
check('licence counts: a total over the built areas and the legend (what all / part / none mean)',
      'Total over 1 built area: Licence, what the club may show: share all 1, share part 1, share none 0 (of 2 outlined parks).' in txt and 'share none = only private records prove it' in txt)
score(lambda k, pr, po, r: k['parks']['US-0001'].update(share='maybe'), v1s={'MN': 100})
check('licence counts: a word that is not all / part / none, or no word, counts as none (fail closed) and the text says so',
      'share all 0, share part 0, share none 2 (of 2 outlined parks); 2 had no licence word and count as none.' in score.last[1])
c = SC.licence_counts({'a': {'m': [1], 'share': 'all'}, 'b': {'m': [1], 'share': 'part'}, 'c': {'m': [1], 'share': 'none'}, 'd': {'m': [1]}, 'e': {'m': [], 'share': 'all'}, 'f': None})
check('licence counts: the function counts 1 all, 1 part, 2 none (one of them unmarked) and skips pin-only parks and empty rows', c == {'all': 1, 'part': 1, 'none': 2, 'unmarked': 1})
check('licence counts: the totals add up (licence_sum)', SC.licence_sum([c, {'all': 2, 'part': 0, 'none': 5, 'unmarked': 0}, None]) == {'all': 3, 'part': 1, 'none': 7, 'unmarked': 1})
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    rc, out, text = cli(t, ['--no-base'], mut=marked)
    check('licence counts: v2-score.json carries them per area for the build summary', json.load(open(out / 'v2-score.json'))['areas']['MN']['lic'] == {'all': 1, 'part': 1, 'none': 0, 'unmarked': 0})

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
