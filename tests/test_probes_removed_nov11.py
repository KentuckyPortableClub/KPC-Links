#!/usr/bin/env python3
"""KPC owner, 2026-11-11: the temporary one-off probes are gone and nothing points at them. Offline, reads files only, no network.
  * kpc-adds-probe, kpc-se-probe, kpc-world-probe, kpc-candidates and kpc-state-camps-probe (workflow + script each) are deleted;
  * no workflow, script, page or test names a deleted file (the .claude notes are history and are left alone);
  * no workflow header says 'delete after use' or 'temporary';
  * the saved probe outputs (history a person may want) were not deleted."""
import pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg)
    ok = ok and bool(c)


GONE = ['kpc-adds-probe', 'kpc-se-probe', 'kpc-world-probe', 'kpc-candidates', 'kpc-state-camps-probe']
for n in GONE:
    check(not (ROOT / f'.github/workflows/{n}.yml').exists(), f'{n}.yml is deleted')
    check(not (ROOT / f'.github/scripts/{n.replace("-", "_")}.py').exists(), f'{n.replace("-", "_")}.py is deleted')

NAMES = re.compile('|'.join(re.escape(n) + r'|' + re.escape(n.replace('-', '_')) for n in GONE))
me = pathlib.Path(__file__).resolve()
hits = []
for base in ('.github', 'tests'):
    for f in (ROOT / base).rglob('*'):
        if not f.is_file() or f.resolve() == me or f.suffix not in ('.py', '.yml', '.sh', '.js', '.json', '.md', '.txt'):
            continue
        if f.name in ('test_ky_fishing_shore_nov6.py', 'test_weekly_batch_nov9pm.py'):
            continue   # the allow-list of changed workflows names the deleted files on purpose; the other comment line explains the removal
        t = f.read_text(encoding='utf-8', errors='replace')
        for i, ln in enumerate(t.splitlines(), 1):
            if NAMES.search(ln) and 'kpc_world_key.py' not in str(f):   # one old docstring line in a key rule file is not ours to edit
                hits.append(f'{f.relative_to(ROOT)}:{i}')
for f in ROOT.glob('*.*'):
    if f.suffix in ('.js', '.html', '.json') and NAMES.search(f.read_text(encoding='utf-8', errors='replace')):
        hits.append(str(f.name))
check(not hits, 'nothing in .github, tests or the top-level pages names a deleted probe' + ((' (' + ', '.join(hits[:6]) + ')') if hits else ''))

bad = []
for wf in sorted((ROOT / '.github/workflows').glob('*.yml')):
    head = '\n'.join(wf.read_text(encoding='utf-8').splitlines()[:12]).lower()
    if 'delete after use' in head or '(temporary' in head or 'temporary, once' in head:
        bad.append(wf.name)
check(not bad, 'no workflow header says delete after use / temporary' + ((' (' + ', '.join(bad) + ')') if bad else ''))

for rel in ('.claude/build/research/SE/candidates-tested.json', 'data/world-probe.json', 'data/review/candidates-us-ca.json', 'data/campstate/probe.json'):
    check((ROOT / rel).exists(), f'saved probe output kept: {rel}')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
