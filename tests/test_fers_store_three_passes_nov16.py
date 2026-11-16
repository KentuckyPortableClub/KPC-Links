#!/usr/bin/env python3
"""KPC owner, 2026-11-16: a store run does three passes of work, not four. The outline store gives every pass the SAME outline
(about 2 m), so pass 2 (the 10 m grid) could only repeat pass 3's test on a coarser grid. In a store run PASS=2 does nothing
(exit 0, its receipt section says why, no 2-fer file changes) and pass 3 takes every pass-1 row on the 5 m grid. A run that
downloads from the agencies is unchanged. Offline, on the made-up store fixture of tests/test_fers_proof_of_work_nov16.py."""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
src = (HERE / 'test_fers_proof_of_work_nov16.py').read_text()
exec(compile(src.split('\nif not HAVE:')[0], 'proof-of-work helpers', 'exec'))   # layout, go, store_env, fers_files, receipt, check
FAILS.clear()

bot = (SCR / 'kpc_fers.py').read_text()
check('if PASS == 2 and store_one_detail():' in bot and 'return _store_mod() is not None' in bot,
      'pass 2 is skipped only in a store run (a run that downloads from the agencies is unchanged)')
check("_from1 = PASS == 3 and store_one_detail()" in bot, 'only a store run lets pass 3 take the pass-1 rows')

if not HAVE:
    print('SKIP the end-to-end part: numpy / cv2 not installed')
else:
    t = TMP / 'three'; t.mkdir(); layout(t)
    rc1, _ = go(t, store_env(t, PASS='1'))
    before = fers_files(t)
    rows1 = json.loads((t / 'data/fers/US-RI.json').read_text())['spots']
    rc2, out2 = go(t, store_env(t, PASS='2'))
    r2 = (receipt(t) or {}).get('passes', {}).get('2') or {}
    check(rc1 == 0 and rc2 == 0, f'passes 1 and 2 exit 0 ({rc1}, {rc2})')
    after = fers_files(t); diff = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    check(not [k for k in diff if k.startswith('US-')], f'pass 2 changes no area 2-fer file in a store run (changed: {diff})')
    check('pass 2 not run' in str(r2.get('note')) and r2.get('areas') == {'US-RI': 'measured'} and r2.get('pairs tested') == 0,
          f"pass 2's receipt section says it was not run and why ({str(r2.get('note'))[:50]})")
    rc3, _ = go(t, store_env(t, PASS='3'))
    d = json.loads((t / 'data/fers/US-RI.json').read_text())
    done = [s for s in d['spots'] if s['passes'][2] == 1]
    check(rc3 == 0 and rows1 and all(s['passes'] == [1, 0, 0] for s in rows1) and done, f'pass 3 takes the pass-1 rows itself ({len(done)} of {len(rows1)} agreed)')
    check(all(s['passes'] == [1, 1, 1] for s in done), 'a row pass 3 agrees with counts for pass 2 as well (same outlines, finer grid)')
    check(d.get('pass2') and d.get('pass3'), 'the file carries the pass 2 and pass 3 dates (the waiting room asks for both)')
    rc5, _ = go(t, store_env(t, PASS='5'))
    check(rc5 == 0 and R.check(receipt(t), [1, 2, 3, 5]) == [], 'the receipt of passes 1, 2, 3, 5 is done (the pass loop is unchanged)')

print('ALL PASS' if not FAILS else f'{len(FAILS)} FAILED: ' + '; '.join(FAILS))
sys.exit(1 if FAILS else 0)
