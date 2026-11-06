#!/usr/bin/env python3
"""FULL SUITE = THE HANDOFF GATE (Nov 6 2026, Mapping; Brandon directly in Mapping's chat, 4:58 PM CST Nov 5: "You write the code
and I think super and quality would agree to it").

Runs EVERY tests/test_*.py file of this repo one by one (python3 -B <file>, its own process; pytest cannot collect these
script-style files because they call sys.exit at module level), then EVERY `.github/scripts/*.py` that handles `--selftest`
(python3 -B <script> --selftest), and compares the failures with the known failures of main (the baseline file,
default tests/known-fail-main.txt). Exit 1 on any NEW failure; exit 0 when every failure is already a known failure of main.

  pass  = exit 0 and none of the fail words below in the output
  fail  = anything else (non-zero exit, timeout, 'SOME FAILED', 'SELFTEST FAIL', '-> FAIL')
  dirty = the run changed the repo's files (git status before / after each file); counted as a failure of THAT file, because a
          test or selftest must never write the repo's own data (Part B 08: the ledger tests did). Nothing is restored or deleted.

Writes a tests.txt-style report (REPORT=<file>, default stdout only). Offline: it runs only local files (each test must be
offline itself). No secrets, no network, never pushes.

  python3 .github/scripts/kpc_full_suite.py [--root DIR] [--baseline FILE] [--report FILE] [--timeout 180] [--no-selftests]
  python3 .github/scripts/kpc_full_suite.py --selftest      (rule-18 style: 10+ frozen cases on a throwaway repo in /tmp)
Env passed through (LINKS / DATA point the tests at the other repo).

Baseline file: one entry per line, '#' comments. An entry is a test path (tests/test_x.py) or 'selftest:<script path>'.
"""
import argparse, os, pathlib, re, subprocess, sys, tempfile, time

FAIL_WORDS = re.compile(r'SOME FAILED|SELFTEST FAIL|-> FAIL\b')
BASELINE = 'tests/known-fail-main.txt'


def git_state(root):
    """Porcelain status (tracked changes + untracked files); None when root is not a git checkout."""
    try:
        r = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=root, capture_output=True, text=True, timeout=60)
        return r.stdout if r.returncode == 0 else None
    except Exception: return None  # noqa: BLE001


def read_baseline(path):
    out = set()
    try:
        for ln in open(path, encoding='utf-8'):
            ln = ln.split('#', 1)[0].strip()
            if ln: out.add(ln)
    except FileNotFoundError: pass
    return out


def selftest_scripts(root):
    out = []
    for f in sorted(pathlib.Path(root, '.github/scripts').glob('*.py')):
        if f.name == 'kpc_full_suite.py': continue   # never itself (its selftest builds its own throwaway repo)
        try: txt = f.read_text(encoding='utf-8', errors='replace')
        except Exception: continue  # noqa: BLE001
        if re.search(r"""['"]--selftest['"]\s+in\s+(sys\.)?argv|==\s*['"]--selftest['"]""", txt): out.append(f)
    return out


def run_one(cmd, root, timeout):
    t = time.time()
    try:
        r = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=timeout, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        out, rc = (r.stdout or '') + (r.stderr or ''), r.returncode
    except subprocess.TimeoutExpired:
        out, rc = f'TIMEOUT after {timeout}s', 124
    ok = rc == 0 and not FAIL_WORDS.search(out)
    why = [ln.strip() for ln in out.splitlines() if re.match(r'\s*(FAIL|SELFTEST FAIL|Traceback|\w*Error)', ln)][:4]
    if not ok and not why: why = [f'exit {rc}'] + [ln.strip() for ln in out.splitlines()[-2:] if ln.strip()]
    return ok, why, round(time.time() - t, 1)


def suite(root='.', baseline=None, timeout=180, selftests=True, label=''):
    root = str(pathlib.Path(root).resolve())
    base = read_baseline(baseline or os.path.join(root, BASELINE))
    items = [(str(f.relative_to(root)), [sys.executable, '-B', str(f.relative_to(root))]) for f in sorted(pathlib.Path(root, 'tests').glob('test_*.py'))]
    if selftests:
        items += [('selftest:' + str(f.relative_to(root)), [sys.executable, '-B', str(f.relative_to(root)), '--selftest']) for f in selftest_scripts(root)]
    rows, before = [], git_state(root)
    for name, cmd in items:
        ok, why, secs = run_one(cmd, root, timeout)
        after = git_state(root)
        if before is not None and after is not None and after != before:
            changed = sorted(set(after.splitlines()) - set(before.splitlines()))
            ok = False; why = ['left the repo changed: ' + '; '.join(c.strip() for c in changed[:4])] + why
            before = after   # attribute only NEW changes to the next file
        known = name in base
        rows.append({'name': name, 'ok': ok, 'known': known, 'why': why, 'secs': secs})
    new = [r for r in rows if not r['ok'] and not r['known']]
    fixed = sorted(b for b in base if any(r['name'] == b and r['ok'] for r in rows))
    gone = sorted(b for b in base if not any(r['name'] == b for r in rows))
    head = ''
    try: head = subprocess.run(['git', 'rev-parse', '--short=12', 'HEAD'], cwd=root, capture_output=True, text=True).stdout.strip()
    except Exception: pass  # noqa: BLE001
    return {'root': root, 'head': head, 'label': label, 'rows': rows, 'new': new, 'fixed': fixed, 'gone': gone,
            'pass': sum(r['ok'] for r in rows), 'total': len(rows),
            'tests_pass': sum(r['ok'] for r in rows if not r['name'].startswith('selftest:')),
            'tests_total': sum(1 for r in rows if not r['name'].startswith('selftest:'))}


def report(res):
    L = [f"## {res['label'] or 'suite'}  root={res['root']}  HEAD={res['head']}",
         f"CMD: python3 .github/scripts/kpc_full_suite.py --root {res['root']}  (every tests/test_*.py one by one + every --selftest)"]
    for r in res['rows']:
        tag = 'PASS' if r['ok'] else ('FAIL (known on main)' if r['known'] else 'FAIL NEW')
        L.append(f"{tag:<21} {r['name']}  ({r['secs']}s)")
        if not r['ok']: L += ['    ' + w[:200] for w in r['why']]
    L.append(f"TOTAL tests: {res['tests_pass']}/{res['tests_total']} pass; with selftests: {res['pass']}/{res['total']} pass; "
             f"NEW failures: {len(res['new'])}" + (' -> GATE FAIL' if res['new'] else ' -> GATE PASS'))
    if res['fixed']: L.append('known failures that now PASS (take them off the baseline): ' + ', '.join(res['fixed']))
    if res['gone']: L.append('baseline entries not found in this repo: ' + ', '.join(res['gone']))
    return '\n'.join(L) + '\n'


def selftest():
    """10+ frozen cases on a throwaway git repo (never this checkout)."""
    ok_all, n = True, 0
    def check(name, got, want):
        nonlocal ok_all, n
        n += 1; good = got == want; ok_all &= good
        print(('PASS ' if good else 'FAIL ') + name + ('' if good else f'  got={got!r} want={want!r}'))
    d = pathlib.Path(tempfile.mkdtemp(prefix='kpc-suite-')); (d / 'tests').mkdir(); (d / '.github/scripts').mkdir(parents=True)
    w = lambda p, s: (d / p).write_text(s, encoding='utf-8')
    w('tests/test_a_pass.py', "print('PASS a')\n")
    w('tests/test_b_known.py', "import sys; print('FAIL b'); sys.exit(1)\n")
    w('tests/test_c_new.py', "import sys; print('FAIL c'); sys.exit(1)\n")
    w('tests/test_d_words.py', "print('SOME FAILED')\n")                         # exit 0 but says it failed
    w('tests/test_e_dirty.py', "open('written.txt','w').write('x')\nprint('PASS e')\n")
    w('tests/test_f_fixed.py', "print('PASS f')\n")
    w('.github/scripts/kpc_s1.py', "import sys\nif '--selftest' in sys.argv: print('SELFTEST PASS')\n")
    w('.github/scripts/kpc_s2.py', "import sys\nif '--selftest' in sys.argv: print('SELFTEST FAIL: 1 of 2')\n")
    w('.github/scripts/kpc_s3.py', "print('no selftest here')\n")
    w('.github/scripts/kpc_s4.py', "import sys\na = sys.argv[1:]\nif a and a[0] == '--selftest': print('SELFTEST PASS')\n")
    w('tests/known-fail-main.txt', "# main\ntests/test_b_known.py\ntests/test_f_fixed.py\nselftest:.github/scripts/kpc_s2.py\ntests/test_gone.py\n")
    subprocess.run('git init -q && git add -A && git -c user.name=t -c user.email=t@t commit -qm t', shell=True, cwd=d)
    res = suite(d, timeout=30, label='selftest')
    by = {r['name']: r for r in res['rows']}
    check('a passing test passes', by['tests/test_a_pass.py']['ok'], True)
    check('a failing test on the baseline is known', (by['tests/test_b_known.py']['ok'], by['tests/test_b_known.py']['known']), (False, True))
    check('a failing test not on the baseline is NEW', (by['tests/test_c_new.py']['ok'], by['tests/test_c_new.py']['known']), (False, False))
    check("exit 0 with 'SOME FAILED' is a failure", by['tests/test_d_words.py']['ok'], False)
    check('a test that writes the repo is a failure (dirty)', (by['tests/test_e_dirty.py']['ok'], 'left the repo changed' in by['tests/test_e_dirty.py']['why'][0]), (False, True))
    check('the next file is not blamed for the earlier write', by['tests/test_f_fixed.py']['ok'], True)
    check('a known failure that now passes is listed as fixed', 'tests/test_f_fixed.py' in res['fixed'], True)
    check('a selftest that passes is run and passes', by.get('selftest:.github/scripts/kpc_s1.py', {}).get('ok'), True)
    check("'SELFTEST FAIL' on the baseline is known", (by['selftest:.github/scripts/kpc_s2.py']['ok'], by['selftest:.github/scripts/kpc_s2.py']['known']), (False, True))
    check('a script without --selftest is not run', 'selftest:.github/scripts/kpc_s3.py' in by, False)
    check("a script testing a[0] == '--selftest' is found too", by.get('selftest:.github/scripts/kpc_s4.py', {}).get('ok'), True)
    check('NEW failures = c, d, e', sorted(r['name'] for r in res['new']), ['tests/test_c_new.py', 'tests/test_d_words.py', 'tests/test_e_dirty.py'])
    check('a baseline entry with no file is reported', res['gone'], ['tests/test_gone.py'])
    check('report says GATE FAIL', 'GATE FAIL' in report(res), True)
    (d / 'tests/test_c_new.py').write_text("print('PASS c')\n"); (d / 'tests/test_d_words.py').write_text("print('PASS d')\n")
    (d / 'tests/test_e_dirty.py').write_text("print('PASS e')\n")
    subprocess.run('git add -A && git -c user.name=t -c user.email=t@t commit -qm t2', shell=True, cwd=d)
    res2 = suite(d, timeout=30, label='selftest-2')
    check('only known failures left -> GATE PASS (exit 0)', (len(res2['new']), 'GATE PASS' in report(res2)), (0, True))
    print(f"SELFTEST {'PASS' if ok_all else 'FAIL'}: {n} cases")
    return ok_all


def main(argv=None):
    if '--selftest' in (argv or sys.argv[1:]): return 0 if selftest() else 1
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.'); ap.add_argument('--baseline'); ap.add_argument('--report', default=os.environ.get('REPORT'))
    ap.add_argument('--timeout', type=int, default=180); ap.add_argument('--no-selftests', action='store_true'); ap.add_argument('--label', default='')
    a = ap.parse_args(argv)
    res = suite(a.root, a.baseline, a.timeout, not a.no_selftests, a.label)
    txt = report(res); sys.stdout.write(txt)
    if a.report:
        with open(a.report, 'a', encoding='utf-8') as f: f.write(txt + '\n')
    return 1 if res['new'] else 0


if __name__ == '__main__':
    sys.exit(main())
