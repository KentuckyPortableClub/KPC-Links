#!/usr/bin/env python3
"""Nov 6: the 4 post-Nov-2 override misses Quality flagged, and multi-state parks_of preference."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_postcheck as KC

ok = True
def check(cond, msg):
    global ok
    if not cond: ok = False; print('FAIL', msg)
    else: print('PASS', msg)

# parks_of prefers outline
tree = {
  'US-AR': {'parks': {'US-0822': {'n': 'Fort Smith', 'g': 'official', 'm': [[3132, 'Fort Smith National Historic Site', 32, 'name']]}}},
  'US-OK': {'parks': {'US-0822': {'n': 'Fort Smith', 'g': 'pin', 'm': [], 'joined_in': ['US-AR']}}},
}
P = KC.parks_of(tree)
check(P['US-0822']['_area'] == 'US-AR' and KC.has_outline(P['US-0822']), f"parks_of prefers AR outline (got {P['US-0822'].get('_area')} g={P['US-0822'].get('g')})")
# reverse order still prefers outline
tree2 = {'US-OK': tree['US-OK'], 'US-AR': tree['US-AR']}
P2 = KC.parks_of(tree2)
check(KC.has_outline(P2['US-0822']), 'parks_of prefers outline regardless of area sort order')

# Live key: the 4 should no longer be real misses under override_check
N = KC.parks_of(KC.load_tree('us', None, str(ROOT)))
misses = KC.override_check(N, 'us', cwd=str(ROOT), built='2026-11-06')
by = {x['park']: x for x in misses}
for r in ('US-0822', 'US-4342', 'US-8209', 'US-8679'):
  check(r not in by, f"{r} is not an override miss (got {by.get(r)})")

# Root-cause notes are recorded on the overrides
ov = json.load(open(ROOT / 'data/us-key/overrides.json'))['parks']
check('wid702688' not in (ov['US-4342'].get('join') or []), 'US-4342 dead wid join cleared')
check('sgwic6887' in (ov['US-8209'].get('join') or []), 'US-8209 join is the live SNA id')
check('190969' in (ov['US-8679'].get('join') or []) and 'sgfld222' in ov['US-8679']['join'], 'US-8679 keeps PAD-US + agency ids')
check(bool((ov['US-8679'].get('fp') or {}).get('190969')), 'US-8679 has fingerprint for 190969')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
