#!/usr/bin/env python3
"""Nov 19 (job C, N2, finding F3; KPC owner, 2026-11-19): tools/kpc_map_lag.py, "the public map is this far behind the key".
On the 19 Nov files (main 521ed9826d9b, read with git show) it must give Montana 50 and Delaware 29 parks that differ between the
released key and today's key. Plus made-up keys for what counts as a difference, row-only outlines, Central dates, the --out guard
(never inside the repo: the lines belong on the KPC-Data tools-out branch), read-only, and no timer (no workflow runs it).
Offline. The 19 Nov part SKIPs when that commit is not in this clone (a shallow clone)."""
import json, pathlib, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import kpc_map_lag as L

ok = True
def check(name, cond, extra=''):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name + (f'  [{str(extra)[:400]}]' if extra and not cond else ''))
    ok = ok and bool(cond)

# what counts as a difference: a park in one key only, or a different grade or joined record ids; not names, acres or candidates
old = {'US-99901': {'g': 'official', 'm': [[1, 'A', 5, 'name']], 'ac': 5, 'c': []},
       'US-99902': {'g': 'official', 'm': [[2, 'B', 5, 'name']]},
       'US-99903': {'g': 'official', 'm': [[3, 'C', 5, 'name']]},
       'US-99904': {'g': 'official', 'm': [[4, 'D', 5, 'name']]}}
new = {'US-99901': {'g': 'official', 'm': [[1, 'A renamed', 9, 'reviewed']], 'ac': 9, 'c': [[7, 'X', 1, 'check']]},
       'US-99902': {'g': 'approximate', 'm': [[2, 'B', 5, 'name']]},
       'US-99903': {'g': 'official', 'm': [['3b', 'C', 5, 'name']]},
       'US-99905': {'g': 'pin', 'm': []}}
check('differ: grade change + id change + one gone + one new = 4; a renamed / re-sized record with the same id is not a difference',
      L.parks_differ(old, new) == 4, L.parks_differ(old, new))
check('differ: the same key = 0', L.parks_differ(old, old) == 0)
doc = {'features': [{'properties': {'ref': 'US-99901', 'record_ids': ['row219']}},
                    {'properties': {'ref': 'US-99902', 'record_ids': ['row1', 'row2']}},
                    {'properties': {'ref': 'US-99903', 'record_ids': ['row3', 'sgx9']}},
                    {'properties': {'ref': 'US-99904', 'record_ids': ['trl99904']}},
                    {'properties': {'ref': 'US-99905', 'record_ids': ['55']}}]}
check('row_only: only outlines with row numbers and no real record id are counted (2 of 5)', L.row_only(doc) == 2, L.row_only(doc))
check('dates are Central: 22:10 UTC on Nov 11 is Nov 11; 03:40 UTC on Nov 12 is Nov 11',
      (L.central('2026-11-11T22:10:22Z'), L.central('2026-11-12T03:40:54Z'), L.central('2026-11-19 21:52 UTC')) == ('2026-11-11', '2026-11-11', '2026-11-19'))

# the 19 Nov files: Montana 50, Delaware 29
REV = '521ed9826d9b9c008267f0e214f9a043f875b81f'
have = subprocess.run(['git', 'cat-file', '-e', f'{REV}^{{commit}}'], cwd=ROOT, capture_output=True).returncode == 0
before = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, text=True).stdout
if have:
    rows = {r['state']: r for r in L.lag(ROOT, rev=REV, states=['US-MT', 'US-DE'])}
    check('19 Nov files: Montana 50 parks differ between the released key and today\'s key', rows['US-MT']['differ'] == 50, rows['US-MT'])
    check('19 Nov files: Delaware 29 parks differ', rows['US-DE']['differ'] == 29, rows['US-DE'])
    check('19 Nov files: released 2026-11-11, key 2026-11-19, 8 days behind (both states)',
          all((r['released'], r['key'], r['days']) == ('2026-11-11', '2026-11-19', 8) for r in rows.values()), rows)
    check('19 Nov files: row-only released outlines Montana 179, Delaware 56', (rows['US-MT']['row_only'], rows['US-DE']['row_only']) == (179, 56), rows)
    cli = subprocess.run([sys.executable, str(ROOT / 'tools/kpc_map_lag.py'), '--repo', str(ROOT), '--rev', REV, '--states', 'US-MT'],
                         capture_output=True, text=True)
    check('CLI: one plain line per state', cli.stdout.strip() == 'US-MT  released 2026-11-11  key 2026-11-19  8 day(s) behind  50 park(s) differ  179 row-only outline(s)', cli.stdout + cli.stderr)
with tempfile.TemporaryDirectory() as t:
    bad = subprocess.run([sys.executable, str(ROOT / 'tools/kpc_map_lag.py'), '--repo', str(ROOT), '--states', 'US-MT', '--out', str(ROOT / 'data/lag.txt')],
                         capture_output=True, text=True)
    check('--out inside the repo is refused (exit 2) and writes nothing', bad.returncode == 2 and not (ROOT / 'data/lag.txt').exists(), bad.stderr)
    if have:
        o = pathlib.Path(t) / 'lag.txt'
        good = subprocess.run([sys.executable, str(ROOT / 'tools/kpc_map_lag.py'), '--repo', str(ROOT), '--rev', REV, '--states', 'US-DE', '--out', str(o)],
                              capture_output=True, text=True)
        check('--out outside the repo writes the lines there', good.returncode == 0 and '29 park(s) differ' in o.read_text(), good.stderr)
check('read-only: the repo is unchanged', subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, text=True).stdout == before)
wf = ''.join(p.read_text(encoding='utf-8', errors='replace') for p in (ROOT / '.github/workflows').glob('*.y*ml'))
check('no timer: no workflow runs kpc_map_lag.py (by hand only)', 'kpc_map_lag' not in wf)

print('ALL PASS' if ok else 'SOME FAILED')
if ok and not have: print('SKIP: the 19 Nov commit is not in this clone (shallow); the Montana 50 / Delaware 29 check did not run')
sys.exit(0 if ok else 1)
