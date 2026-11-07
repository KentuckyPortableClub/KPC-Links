#!/usr/bin/env python3
"""Nov 7 Quality fix 2: in own_park mode a 2-fer combo touching a guessed tract (approx_split, or box-only tracts sharing one
box with an even acre share) is NOT counted; it is listed in 'tract_flagged' as 'guessed tract'. one_park output is unchanged."""
import os, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_fers_count as FC
fails = 0
def check(ok, msg):
    global fails; fails += not ok; print(('PASS ' if ok else 'FAIL ') + msg)
B1, B2 = [0, 0, 1, 1], [2, 2, 3, 3]
IDX = lambda: {
    'P-1': {'tracts': [{'rid': 'a', 'name': 'North', 'ac': 100, 'box': B1}, {'rid': 'b', 'name': 'South', 'ac': 50, 'box': B2}]},
    'P-2': {'tracts': [{'rid': 'c', 'name': 'Split', 'ac': 100, 'box': [0, 0, 3, 3], 'pieces': 2}]},
    'P-3': {'tracts': [{'rid': 'd', 'name': 'One', 'ac': 10, 'box': [0, 0, 3, 3]}]},
}
def doc():
    return {'st': 'XX', 'spots': [
        {'id': 's1', 'status': 'candidate', 'refs': ['P-1', 'P-3'], 'center': [0.5, 0.5]},
        {'id': 's2', 'status': 'candidate', 'refs': ['P-1', 'P-3'], 'center': [2.5, 2.5]},
        {'id': 's3', 'status': 'candidate', 'refs': ['P-2', 'P-3'], 'center': [0.5, 0.5]}]}
os.environ['KPC_TRACT_MODE'] = 'own_park'
d = FC.apply('XX.json', doc(), 'tracts', IDX())
check(d['count_tracts'] == 2 and d['count'] == 2, 'own_park counts only the 2 real-tract combos (got %s)' % d.get('count_tracts'))
fl = d.get('tract_flagged') or []
check(len(fl) == 1 and fl[0]['flag'] == 'guessed tract' and any(t.startswith('P-2#') for t in fl[0]['tracts']), 'the approx_split combo is flagged guessed tract')
IDX2 = IDX(); IDX2['P-1']['tracts'][1]['box'] = B1; IDX2['P-1']['tracts'][1]['ac'] = 100
d = FC.apply('XX.json', doc(), 'tracts', IDX2)
check(len(d.get('tract_flagged') or []) >= 2 and d['count_tracts'] == 1, 'box-only tracts sharing one box are flagged, not counted')
lab = d['spots'][0].get('tract_labels') or {}
check(any(k.startswith('P-1#') for k in lab) and all(v.endswith(' tract') and ', ' in v for v in lab.values()), "tracts get '<Park name>, <X> tract' labels; ids stay <ref>#<n>: %s" % lab)
os.environ['KPC_TRACT_MODE'] = 'one_park'
d = FC.apply('XX.json', doc(), 'tracts', IDX())
check('tract_flagged' not in d and d['count_tracts'] == 3, 'one_park output unchanged (no flag field, count_tracts as before)')
print('ALL PASS' if not fails else 'SOME FAILED'); sys.exit(1 if fails else 0)
