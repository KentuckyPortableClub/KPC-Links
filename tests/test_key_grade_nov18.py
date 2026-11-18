#!/usr/bin/env python3
"""The grade (Fable, 2026-11-18; .claude/notes/key-quality.md): blind line-ups, the scorer and the gold set, on a small
made-up area. What must hold: the packet never says what the key joined; no source = UNSURE; a joined NO is wrong land, a
joined BIGGER is too big, a not-joined YES is a missing piece; a grader who fails the known answers is not counted; two
graders who differ make a dispute, not a rate; ranges are honest; sealed gold misses cannot be peeked at for free."""
import csv, gzip, json, pathlib, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_key_factcheck as FC
import kpc_key_grade as G

bad = 0
def ck(c, m):
    global bad; bad += not c; print(('PASS ' if c else 'FAIL ') + m)

def sq(lon, lat, side_km):
    d = side_km / 111.0
    return [[[lon, lat], [lon + d, lat], [lon + d, lat + d], [lon, lat + d], [lon, lat]]]
def rec(i, name, lon, lat, side, acres, des='', mang='STAT'):
    return {'OBJECTID': i, 'Unit_Nm': name, 'Loc_Nm': '', 'Mang_Name': mang, 'Loc_Mang': 'State lands', 'Des_Tp': des, 'GIS_Acres': acres, '_r': sq(lon, lat, side)}
def pi(name, lat, lon, act=10): return [name, 'https://parks.example.gov/x', 'State Park', '', '', lat, lon, act, 0, 0]

RECS = [rec(1, 'Elk Hollow State Park', -90.00, 40.00, 2.0, 988, 'SP'), rec('sgxxa7', 'Elk Hollow', -90.00, 40.00, 2.0, 990),
        rec(2, 'Elk Hollow State Forest', -89.95, 40.00, 6.0, 8900),            # a look-alike next door
        rec(3, 'Stony Run Wildlife Area', -90.03, 40.01, 1.0, 247),             # a neighbour
        rec(4, 'Salt Fork Lake', -91.00, 41.00, 6.6, 10768),                    # the whole lake property
        rec(5, 'Marsh Unit', -91.01, 41.01, 0.5, 60),
        rec(6, 'Quarry Ridge State Park', -92.00, 42.00, 2.0, 988, 'SP'), rec(7, 'Quarry Ridge State Park', -92.03, 42.00, 1.0, 247, 'SP'),   # a second piece, not joined
        rec(8, 'Tall Pines National Monument', -93.00, 43.00, 3.0, 2224, 'NM', 'NPS')]
KEY = {'parks': {
    'US-0001': {'n': 'Elk Hollow State Park', 'g': 'official', 'ac': 988, 'm': [[1, 'Elk Hollow State Park', 988, 'name'], ['sgxxa7', 'Elk Hollow', 990, 'name']]},
    'US-0002': {'n': 'Cove Point on Salt Fork Lake State Recreation Area', 'g': 'approximate', 'm': [[4, 'Salt Fork Lake', 10768, 'reviewed-approx']]},
    'US-0003': {'n': 'Quarry Ridge State Park', 'g': 'official', 'm': [[6, 'Quarry Ridge State Park', 988, 'name']]},
    'US-0004': {'n': 'Tall Pines National Monument', 'g': 'official', 'ac': 2224, 'm': [[8, 'Tall Pines National Monument', 2224, 'NPS unit code']]},
    'US-0005': {'n': 'Stony Run State Wildlife Area', 'g': 'pin', 'm': []}}}
PINFO = {'parks': {'US-0001': pi('Elk Hollow State Park', 40.005, -89.995), 'US-0002': pi('Cove Point on Salt Fork Lake State Recreation Area', 41.02, -90.98),
                   'US-0003': pi('Quarry Ridge State Park', 42.005, -91.995), 'US-0004': pi('Tall Pines National Monument', 43.01, -92.99), 'US-0005': pi('Stony Run State Wildlife Area', 40.012, -90.027)}}
PLANTS = {'plants': {'US-0002': {'area': 'US-XX', 'why': 'the whole lake property for one small area', 'expect': [{'id': 4, 'name': 'Salt Fork Lake', 'acres': 10768, 'verdict': ['BIGGER', 'NO']}]}}}

t = pathlib.Path(tempfile.mkdtemp())
for d in ('keys', 'cache', 'pinfo', 'fact'): (t / d).mkdir()
(t / 'keys' / 'US-XX.json').write_text(json.dumps(KEY)); (t / 'pinfo' / 'US-XX.json').write_text(json.dumps(PINFO))
json.dump({'recs': RECS}, gzip.open(t / 'cache' / 'US-XX.json.gz', 'wt'))
(t / 'plants.json').write_text(json.dumps(PLANTS))
doc = FC.check_area('US-XX', KEY, FC.load_cache(t / 'cache', 'US-XX'), PINFO['parks'], {}, {}, today='2026-11-18')
(t / 'fact' / 'factcheck-US-XX.json').write_text(json.dumps(doc))

# ---- sample: seeded, repeatable
fact = G.load_fact(str(t / 'fact'))
s1, s2 = G.sample(fact, 'random', 'seed-a', n=5), G.sample(fact, 'random', 'seed-a', n=5)
ck(s1['parks'] == s2['parks'] and {p['ref'] for p in s1['parks']} == {'US-0001', 'US-0002', 'US-0003', 'US-0004'}, 'sample: the same seed draws the same parks; only parks with an outline')
ck([p['ref'] for p in G.sample(fact, 'pin', 'seed-a')['parks']] == ['US-0005'], 'sample pin: the pin-only parks (did the key miss an outline that exists?)')
pick = {'parks': [{'ref': r, 'area': 'US-XX', 'stratum': 'method:name'} for r in ('US-0001', 'US-0003', 'US-0005')]}
made = G.packet([pick], str(t / 'keys'), str(t / 'cache'), str(t / 'pinfo'), fact, None, str(t / 'pk'), 'test', 'seed-a', size=60, plants=PLANTS['plants'], plant_share=0.7)
md = (t / 'pk' / 'packet-test-01.md').read_text()
key = json.loads((t / 'pk-keys' / 'packet-test-01.key.json').read_text())['parks']
ck(not list((t / 'pk').glob('*.key.json')) and (t / 'pk' / 'GRADER-PROMPT.md').is_file(), 'packet: the answer key is NOT in the folder the grader gets')
ck(not any(w in md for w in ('reviewed', 'joined', 'method', 'verified', 'flagged', 'unit code')), 'packet: BLIND, no method, flag, class or which records the key joined')
c1 = key['US-0001']['cands']
ck(sum(c['joined'] for c in c1.values()) == 2 and any(c['name'] == 'Elk Hollow State Forest' and not c['joined'] for c in c1.values())
   and any(c['name'] == 'Stony Run Wildlife Area' and c['role'] == 'near' for c in c1.values()), f'line-up: the joined records mixed with a look-alike and a neighbour ({[(c["name"], c["role"]) for c in c1.values()]})')
ck(any(c['role'] == 'sibling' and not c['joined'] for c in key['US-0003']['cands'].values()), 'line-up: a second record of the same name that the key did not join is offered (a missing piece can be found)')
ck(key['US-0002']['plant'] and any(c['expect'] == ['BIGGER', 'NO'] for c in key['US-0002']['cands'].values()), 'plant: the hard case carries its known answer in the key only')
ck(key['US-0004']['plant'] and any(c['expect'] == ['YES'] and c['joined'] for c in key['US-0004']['cands'].values()), 'plant: a unit-code join with the pin on it is a known YES')
ck(key['US-0005']['cands'] and not any(c['joined'] for c in key['US-0005']['cands'].values()), 'a pin-only park gets a line-up too')

# ---- answers: grader A does it right, grader B rubber-stamps by name, grader C differs on one park
L = lambda ref, pred: next(k for k, c in key[ref]['cands'].items() if pred(c))
def answers(name, verdict_of):
    f = t / f'{name}.packet-test-01.answers.csv'
    with open(f, 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['ref', 'candidate', 'verdict', 'source', 'note'])
        for ref, p in key.items():
            for k, c in p['cands'].items():
                v, src = verdict_of(ref, c); w.writerow([ref, k, v, src, ''])
    return str(f)
def right(ref, c):
    if ref == 'US-0002': return ('BIGGER', 'https://agency.example.gov/lake') if c['name'] == 'Salt Fork Lake' else ('NO', 'packet: 1 km off, another name')
    if ref == 'US-0003': return ('YES', 'https://agency.example.gov/quarry') if c['name'] == 'Quarry Ridge State Park' else ('NO', 'packet: other place')
    if ref == 'US-0005': return ('YES', 'https://agency.example.gov/stony') if c['name'] == 'Stony Run Wildlife Area' else ('NO', 'packet: other place')
    return ('YES', 'https://agency.example.gov/unit') if c['joined'] else ('NO', 'packet: a state forest, another designation, 8,900 acres against 988')
def stamper(ref, c): return ('YES', 'packet: the name matches') if FC.name_fit(key[ref]['name'], [c['name']]) else ('NO', 'packet: other name')
def differs(ref, c):
    v, s_ = right(ref, c)
    return ('NO', 'https://agency.example.gov/no') if (ref == 'US-0001' and c['joined'] and c['family'] == 'sgxxa') else (v, s_)
def lazy(ref, c): v, _s = right(ref, c); return (v, '')

fa, fb, fc_, fl = answers('graderA', right), answers('graderB', stamper), answers('graderC', differs), answers('graderL', lazy)
kf = [str(t / 'pk-keys' / 'packet-test-01.key.json')]
rep, parks, ans = G.score(kf, [fa])
P = rep['parks']
ck(rep['graders']['graderA']['counts'] and rep['graders']['graderA']['plants'] == rep['graders']['graderA']['plants_right'] >= 2, 'grader A gets the known answers right and counts')
ck(P['US-0001']['outcome'] == 'RIGHT' and P['US-0003']['outcome'] == 'MISSING PIECES' and P['US-0005']['outcome'] == 'MISSING PIECES' and P['US-0002']['outcome'] == 'TOO BIG',
   f"outcomes: right / a not-joined YES = missing pieces (also on a pin-only park) / a joined BIGGER = too big ({ {r: p['outcome'] for r, p in P.items()} })")
ck('US-0002' not in [r for r, p in P.items() if not p['plant']] and rep['rates']['ALL']['parks'] == 3, 'plants are left out of every rate')
rep_b, _p, _a = G.score(kf, [fb])
ck(not rep_b['graders']['graderB']['counts'] and not rep_b['parks'], f"a grader who says YES by name fails the known answers and is NOT counted ({rep_b['graders']['graderB']['missed']})")
rep_l, _p, ans_l = G.score(kf, [fl])
ck(all(v[0] == 'UNSURE' for v in ans_l['graderL'].values()) and not rep_l['graders']['graderL']['counts'], 'a verdict with no source is scored UNSURE (no evidence = no verdict)')
rep2, parks2, ans2 = G.score(kf, [fa, fc_])
ck(rep2['parks']['US-0001']['outcome'] == 'DISPUTED' and len(rep2['disputes']) == 1 and rep2['disputes'][0]['kind'] == 'conflict' and rep2['rates']['ALL']['disputed'] == 1 and rep2['parks']['US-0003']['graded'] == 'double',
   'two graders who differ on a candidate = DISPUTED, kept out of the rates; where they agree the park is double-graded')
ck(G.merge('NO', 'BIGGER', False) == ('BIGGER', None) and G.merge('NO', 'UNSURE', False) == ('NO', None) and G.merge('YES', 'UNSURE', False) == ('UNSURE', 'one unsure')
   and G.merge('YES', 'NO', True) == (None, 'conflict') and G.merge('BIGGER', 'UNSURE', True) == ('UNSURE', 'one unsure'),
   'merge: NO and BIGGER agree; on a record the key did not join only a YES matters; YES against NO is a conflict; one unsure grader leaves it UNSURE')
adj = t / 'adj.csv'
d = rep2['disputes'][0]
adj.write_text(f"ref,candidate,verdict,source,by\n{d['ref']},{d['candidate']},YES,https://agency.example.gov/map,Fable\n")
rep3, parks3, ans3 = G.score(kf, [fa, fc_], str(adj))
ck(rep3['parks']['US-0001']['outcome'] == 'RIGHT' and rep3['parks']['US-0001']['graded'] == 'adjudicated', 'the adjudicated verdict settles the dispute')
# ---- ranges
lo, hi, most = G.interval(0, 300); lo1, hi1, _m = G.interval(1, 120)
ck(lo == 0 and abs(most - 0.00994) < 0.0005 and 0.0120 < hi < 0.0125, f'300 parks, none wrong: at most {100 * most:.2f}% (the rule of three), two-sided up to {100 * hi:.2f}%')
ck(abs(hi1 - 0.0456) < 0.002 and lo1 < 0.001, f'1 wrong in 120 is NOT "about 0.8%": the range is {100 * lo1:.2f}% to {100 * hi1:.2f}%')
# ---- gold: settled parks go in; sealed misses are not shown; looking moves them to TUNE
gold = t / 'gold.json'
G.write_score(rep3, parks3, ans3, str(t / 'score'), str(gold))
g = json.loads(gold.read_text())
ck(set(g['parks']) >= {'US-0001', 'US-0003'} and g['parks']['US-0001']['half'] == 'TUNE' and g['parks']['US-0002']['half'] == 'TUNE',
   'gold: settled parks are added; an adjudicated park and a plant are TUNE (people looked at them)')
ck(g['parks']['US-0003']['half'] == G.half_of('US-0003') and {G.half_of(f'US-{i:04d}') for i in range(40)} == {'TUNE', 'SEALED'}, 'gold: the half comes from a hash of the park number (nobody chooses)')
for r in ('US-0001', 'US-0003', 'US-0005'): g['parks'][r]['half'] = 'SEALED'
gold.write_text(json.dumps(g))
lines = G.gold_score(str(gold), str(t / 'keys'), str(t / 'cache'), str(t / 'pinfo'))
ck(any(x.startswith('SEALED: 3 gold parks') and 'missing pieces 2 of 3' in x for x in lines) and not any('US-0003' in x or 'US-0005' in x for x in lines),
   f'gold score: the SEALED half gives numbers only, no park is named ({[x[:90] for x in lines]})')
lines = G.gold_score(str(gold), str(t / 'keys'), str(t / 'cache'), str(t / 'pinfo'), show_sealed=True)
g2 = json.loads(gold.read_text())
ck(any('US-0003' in x for x in lines) and g2['parks']['US-0003']['half'] == 'TUNE' and g2['parks']['US-0001']['half'] == 'SEALED' and 'moved to TUNE' in g2['log'][-1],
   'looking at sealed misses moves them to TUNE for good (and says so in the log); sealed parks that pass stay sealed')
fnd = list(csv.DictReader(open(t / 'score' / 'findings.csv')))
want = {r for r in ('US-0003', 'US-0005') if G.half_of(r) == 'TUNE'}
ck({x['ref'] for x in fnd} == want and (not fnd or 'cause (A-F)' in fnd[0]) and 'SEALED half and are not listed' in (t / 'score' / 'score.txt').read_text(),
   f'findings.csv with a gold set: only the TUNE half is listed, with an empty cause column; sealed findings are counted, not named ({sorted(want)})')
G.write_score(rep3, parks3, ans3, str(t / 'score2'))
ck({x['ref'] for x in csv.DictReader(open(t / 'score2' / 'findings.csv'))} == {'US-0003', 'US-0005'}, 'without a gold set every non-right park is listed')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
