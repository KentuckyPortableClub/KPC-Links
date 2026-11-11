#!/usr/bin/env python3
"""Offline static test (owner rule, 2026-11-10) over every workflow in KPC-Links and KPC-Data (DATA=../kpc-data by default):
no expression uses an `inputs.X` that the workflow does not declare (workflow_dispatch / workflow_call inputs), no choice input has
an empty option, the post-key check queues per key, and nothing refers to the deleted one-time kpc-chain.yml."""
import os, pathlib, re, sys
import yaml

HERE = pathlib.Path(__file__).resolve().parent.parent
DATA = pathlib.Path(os.environ.get('DATA') or HERE.parent / 'kpc-data')
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


def exprs(node, key=None):
    """Every expression text: ${{ ... }} anywhere, plus a bare `if:` value."""
    if isinstance(node, dict):
        for k, v in node.items(): yield from exprs(v, k)
    elif isinstance(node, list):
        for v in node: yield from exprs(v, key)
    elif isinstance(node, str):
        yield from re.findall(r'\$\{\{(.*?)\}\}', node, re.S)
        if key == 'if' and '${{' not in node: yield node


wfs = sorted((HERE / '.github/workflows').glob('*.yml')) + (sorted((DATA / '.github/workflows').glob('*.yml')) if DATA.is_dir() else [])
check(len(wfs) > 20, f'{len(wfs)} workflow files read')
for f in wfs:
    try: y = yaml.safe_load(f.read_text())
    except Exception as e: check(False, f'{f.name}: YAML does not parse ({e})'); continue  # noqa: BLE001
    on = y.get('on', y.get(True)) or {}
    on = on if isinstance(on, dict) else {}
    declared = set()
    for ev in ('workflow_dispatch', 'workflow_call'):
        declared |= set(((on.get(ev) or {}).get('inputs') or {}) if isinstance(on.get(ev), dict) else {})
    used = {m for e in exprs(y.get('jobs') or {}) for m in re.findall(r'\binputs\.([A-Za-z_][A-Za-z0-9_-]*)', e)}
    used |= {m for e in exprs(y.get('concurrency') or {}) for m in re.findall(r'\binputs\.([A-Za-z_][A-Za-z0-9_-]*)', e)}
    und = sorted(used - declared)
    check(not und, f'{f.parent.parent.parent.name}/{f.name}: every inputs.X it uses is declared ({und or "ok"})')
    for ev in ('workflow_dispatch', 'workflow_call'):
        for n, d in (((on.get(ev) or {}).get('inputs') or {}) if isinstance(on.get(ev), dict) else {}).items():
            if isinstance(d, dict) and d.get('type') == 'choice':
                check('' not in [str(o) for o in d.get('options') or []] and str(d.get('default')) in [str(o) for o in d.get('options') or []],
                      f'{f.name}: choice input {n} has no empty option and its default is one of the options')
    if f.parent.parent.parent == HERE:
        check('kpc-chain.yml' not in f.read_text() and 'KPC bot chain' not in f.read_text(), f'{f.name}: no reference to the deleted kpc-chain.yml')

check(not (HERE / '.github/workflows/kpc-chain.yml').exists(), 'the one-time kpc-chain.yml is gone (date-gated, dead)')
pc = yaml.safe_load((HERE / '.github/workflows/kpc-key-postcheck.yml').read_text())
g = str(pc['concurrency']['group'])
check('inputs.key' in g and 'workflow_run' not in g, f'kpc-key-postcheck.yml: one queue per key ({g})')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
