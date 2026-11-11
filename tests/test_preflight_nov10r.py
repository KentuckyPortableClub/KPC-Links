#!/usr/bin/env python3
"""Preflight pure functions on fixtures (no git needed): changelog hash lookup, the hash-move rule, workflow checks, added-line scans,
and the full-suite SKIP / stale-baseline rules."""
import pathlib, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_preflight as P
import kpc_full_suite as FS

ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)

A, B, C, D = 'a' * 12, 'b' * 12, 'c' * 12, 'd' * 12
TXT = (f'Newest: US rules {B} -> {C} (FINAL) APPROVED, decided_by KPC owner, 2026-11-10. Re-stamped (US {A} -> {B}). CA {D} unchanged. world rules {A} -> {D}\n'
       f'Why: text\nOlder: US rules {A} -> {B} APPROVED, decided_by KPC owner. fers v1 {A} -> {B}\n')
check(P.changelog_hashes(TXT, 'us-key')[:2] == (B, C), 'us: the newest line wins; new = the last arrow of that line')
check(P.newest_hash('world-key', TXT) == D and P.newest_hash('fers', TXT) == B and P.newest_hash('ca-key', TXT) is None, 'world / fers found, a kind with no arrow is None')
check(P.newest_hash('us-key', '') is None, 'empty changelog -> None')
sc = {'changes': [{'from': B, 'scope': 'all'}]}
check(P.check_hash_pair('us-key', B, C, TXT, sc) == '', 'moved hash with changelog + approval + scope entry passes')
check('does not say' in P.check_hash_pair('us-key', A, C, TXT, sc), 'wrong old hash is refused (text)')
check('APPROVED' in P.check_hash_pair('us-key', B, C, TXT.replace('APPROVED, decided_by KPC owner', 'ok'), sc), 'no approval words is refused (text)')
check('scope entry' in P.check_hash_pair('us-key', B, C, TXT, {'changes': [{'from': A}]}), 'no scope entry from the old hash is refused (text)')
check(P.check_hash_pair('world-key', A, D, TXT, None) == '', 'a kind with no scope file needs no scope entry')
# workflows
WF = {True: {'workflow_dispatch': {'inputs': {'states': {}}}}, 'jobs': {'j': {'steps': [{'env': {'X': '${{ success() }}'}}, {'env': {'Y': '${{ inputs.states }}'}}]}}}
check(P.step_env_problems(WF) == ['j: env X uses a status function'], 'status function in a step env is found')
check(P.undeclared_inputs(WF, 'a ${{ inputs.states }} b ${{ inputs.other }}') == ['other'], 'undeclared inputs.* is found (on parses as True)')
# added-line scans
H = 'https://services' + '2.arcgis' + '.com/x'
f, w = P.scan_added('.github/scripts/kpc_new.py', [f'U = "{H}"'])
check(len(f) == 1, 'forbidden host in an unguarded script is refused')
check(P.scan_added('.github/scripts/kpc_new.py', ['import kpc_net_guard', f'U = "{H}"'])[0] == [], 'the same with kpc_net_guard imported -> allowed')
check(P.scan_added('tests/test_x.py', [f'U = "{H}"'])[0] == [] and P.scan_added('docs/x.md', [H])[0] == [], 'tests and docs may name a host')
check(len(P.scan_added('kpc_x.py', ['u = "https://www.protectedplanet.net/x/wdpa.zip"'])[0]) == 1, 'a WDPA download URL is refused')
check(P.scan_added('x.py', ['# thanks t123u'])[1] != [] and P.scan_added('x.py', ['x = 5'])[1] == [], 'ticket id in a comment -> WARN; plain code is clean')
check(P.added_lines('a\nb', 'a\nc\nb') == ['c'] and P.added_lines(None, 'a\nb') == ['a', 'b'], 'added_lines: new lines only; no base = all lines')
# the suite: SKIP as the last line is skipped, a stale baseline entry fails the gate
d = pathlib.Path(tempfile.mkdtemp(prefix='kpc-pf-'))
(d / 'tests').mkdir()
(d / 'tests/test_s.py').write_text("print('PASS x')\nprint('SKIP: no history')\n")
(d / 'tests/test_p.py').write_text("print('ALL PASS')\n")
(d / 'tests/known-fail-main.txt').write_text('tests/test_p.py\n')
subprocess.run('git init -q && git add -A && git -c user.name=t -c user.email=t@t commit -qm t', shell=True, cwd=d)
res = FS.suite(d, timeout=30, selftests=False)
check(res['skipped'] == ['tests/test_s.py'] and res['pass'] == 1, 'a test ending in SKIP is skipped, not passed')
check(res['fixed'] == ['tests/test_p.py'] and 'stale baseline: remove tests/test_p.py' in FS.report(res) and FS.gate_fails(res), 'a passing baseline entry is stale and fails the gate')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
