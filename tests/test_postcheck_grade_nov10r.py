#!/usr/bin/env python3
"""Post-check sees a worse grade replacing a better one (official -> approximate -> point-circle -> pin) and a state whose official
count falls 5% or more; the join check says when its acreage check is off. Two tiny fake builds in memory; offline."""
import json, pathlib, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_postcheck as KP
import kpc_join_check as JC

ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)

def park(g, m=True): return {'n': 'P', 'g': g, 'm': [['a', 'P', 5, 'name']] if m else []}
def tree(**states): return {f'US-{s}': {'parks': ps} for s, ps in states.items()}

old = tree(KY={'US-1': park('official'), 'US-2': park('official'), 'US-3': park('approximate'), 'US-4': park('approx'), 'US-5': park('official'), 'US-6': park('pin', False)},
           TN={f'US-1{i}': park('official') for i in range(20)})
new = tree(KY={'US-1': park('approximate'), 'US-2': park('pin', False), 'US-3': park('point-circle'), 'US-4': park('approx'), 'US-5': park('official'), 'US-6': park('official')},
           TN={**{f'US-1{i}': park('official') for i in range(19)}, 'US-119': park('approximate')})
N, O, R = KP.compare(new, old)
check(R['grade_worse'] == ['US-1', 'US-119', 'US-3'], f"official -> approximate and approximate -> point-circle are listed ({R['grade_worse']})")
check('US-2' in R['outline_to_pin'] and 'US-2' not in R['grade_worse'], 'official -> pin stays in outline_to_pin only')
check('US-4' not in R['grade_worse'] and 'US-6' not in R['grade_worse'], 'approx spelling = approximate (no change); pin -> official is not worse')
check(KP.grade_rank(park('official')) > KP.grade_rank(park('approx')) == KP.grade_rank(park('approximate')) > KP.grade_rank(park('point-circle')) > KP.grade_rank(park('pin')),
      'rank: official > approximate = approx > point-circle > pin')
d = KP.official_drops(N, O)
check([(x['area'], x['before'], x['after']) for x in d] == [('US-KY', 3, 2), ('US-TN', 20, 19)], f'official drops of 5% or more are flagged ({d})')
big_old = tree(TN={f'US-{i}': park('official') for i in range(100)})
small = tree(TN={**{f'US-{i}': park('official') for i in range(96)}, **{f'X-{i}': park('approximate') for i in range(4)}})
almost = tree(TN={**{f'US-{i}': park('official') for i in range(95)}, **{f'X-{i}': park('approximate') for i in range(5)}})
check(KP.official_drops(KP.parks_of(small), KP.parks_of(big_old)) == [] and len(KP.official_drops(KP.parks_of(almost), KP.parks_of(big_old))) == 1, '4% drop is quiet, 5% drop warns')
# join check: no acres file -> the report says so
tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-jc-'))
(tmp / 'data/us-key').mkdir(parents=True)
json.dump({'parks': {'US-1': {'n': 'P', 'g': 'official', 'm': [[1, 'P', 100, 'name']], 'bk': [1, 0.5, '', '-']}}}, open(tmp / 'data/us-key/US-KY.json', 'w'))
rep = JC.run({'KEY': 'us', 'ALL': '1', 'DRY': '1'}, root=str(tmp), plain=True)
check(rep and rep['acres_check'] == 'acres check off: no acres file', f"report says: {rep and rep.get('acres_check')}")
json.dump({'parks': {'US-1': 100}}, open(tmp / 'data/acres.json', 'w'))
check(JC.run({'KEY': 'us', 'ALL': '1', 'DRY': '1'}, root=str(tmp), plain=True)['acres_check'] == 'acres check on', 'with an acres file the check is on')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
