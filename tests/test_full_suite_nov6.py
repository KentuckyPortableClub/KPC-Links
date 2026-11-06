#!/usr/bin/env python3
"""Nov 6 improvements 1: the handoff gate (kpc_full_suite.py). Runs its rule-18 style selftest (14 frozen cases on a throwaway repo
in /tmp, never this checkout) and checks the baseline file names only real test files / selftest scripts of this repo."""
import pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True
def check(cond, msg):
    global ok
    ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + msg)
r = subprocess.run([sys.executable, '-B', str(ROOT / '.github/scripts/kpc_full_suite.py'), '--selftest'], capture_output=True, text=True, timeout=120)
check(r.returncode == 0 and 'SELFTEST PASS' in r.stdout, 'kpc_full_suite.py --selftest passes: ' + (r.stdout.strip().splitlines() or ['?'])[-1])
base = ROOT / 'tests/known-fail-main.txt'
check(base.exists(), 'baseline file tests/known-fail-main.txt exists')
for ln in base.read_text().splitlines() if base.exists() else []:
    e = ln.split('#', 1)[0].strip()
    if not e: continue
    p = e[len('selftest:'):] if e.startswith('selftest:') else e
    check((ROOT / p).exists(), f'baseline entry is a real file: {e}')
    check(e.startswith('selftest:') or re.fullmatch(r'tests/test_\w+\.py', e), f'baseline entry has the right form: {e}')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
