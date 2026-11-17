#!/usr/bin/env python3
"""D4 (lakes) and D5 (leased / agreement land), KPC owner 2026-11-17, both behind switches that are OFF.
Run:  python3 tests/test_d4_d5_nov17.py   (reads kpc_us_key.py as text: importing it would start a build)"""
import sys as _sys; _sys.dont_write_bytecode = True
import ast, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
ns = {'re': re}
for node in ast.parse(src).body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ('LEASE_RX', 'LAKE_TYPE_RX') for t in node.targets):
        exec(compile(ast.Module([node], []), 'x', 'exec'), ns)
L, W = ns['LEASE_RX'], ns['LAKE_TYPE_RX']
for s in ('Yadkin River Game Land (Leased)', 'Newaygo State Park (leased from Consumer\'s Energy)', 'Oxbow Lake Wildlife Area Agreement Area',
          'Mansfield Hollow Lake State- Leased WMA', 'Smith Cooperative Wildlife Area'):
    check(bool(L.search(s)), f'D5 lease / agreement record: {s}')
for s in ('Pleasant Valley State Park', 'Release Creek WMA', 'Leasburg Dam State Park', 'Greenleaf State Park'):
    check(not L.search(s), f'D5 not a lease record (whole word only): {s}')
for s in ('State Fishing Lake', 'Reservoir', 'State Lake', 'Fishing Pond'):
    check(bool(W.search(s)), f'D4 a park type that IS the lake: {s}')
for s in ('State Park', 'National Wildlife Refuge', 'State Recreation Area', 'Wildlife Management Area'):
    check(not W.search(s), f'D4 a park type that is not the lake: {s}')
check(not KR.on('KPC_NO_LEASE_BY_NAME', {}) and not KR.on('KPC_LAKE_ONLY_IF_LAKE', {}), 'both switches are OFF unless set')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
