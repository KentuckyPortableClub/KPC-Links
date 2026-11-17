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
# D4 rewritten (KPC owner, 2026-11-17 9:17 AM): who owns the water decides; inside the park's own land = keep, else a person
LI = KR.lake_inside_land
check(not LI([-111.5, 41.8, -111.2, 42.2], 69474, [[-111.30, 41.95, -111.25, 42.00]], 966)[0], 'Bear Lake SP: a 69,474-acre lake beside a 966-acre park is not joined')
check('3 times' in LI([-111.5, 41.8, -111.2, 42.2], 69474, [[-111.30, 41.95, -111.25, 42.00]], 966)[1], 'Bear Lake SP: the reason says over 3 times the land')
check(not LI([-120.7, 47.8, -120.0, 48.5], 0, [[-120.9, 48.3, -120.6, 48.6]], 62000)[0], 'Lake Chelan NRA: the lake runs far past the NRA land: a person decides')
check(LI([-116.645, 47.835, -116.630, 47.845], 0, [[-116.66, 47.82, -116.61, 47.86]], 142)[0], 'Round Lake SP: a small lake the park surrounds is kept')
check(LI([-90.10, 35.88, -90.05, 35.95], 0, [[-90.12, 35.86, -90.03, 35.97]], 10911)[0], 'Big Lake NWR: the lake inside the refuge land is kept')
check(not LI([0, 0, 1, 1], 500, [[0, 0, 1, 1]], 100)[0], 'a lake bigger than the park land is never joined by name')
check(LI([0.001, 0, 1.005, 1], 0, [[0, 0, 1, 1]], 100, pad=0.01)[0], 'the working copy slack is allowed at the edge')
check(not LI([0, 0, 1, 1], 0, [None], 100)[0], 'no land outline: never joined here')
_blk = src[src.index('# D4 (KPC owner, 2026-11-17 9:17 AM'):src.index("weak = [x for x in m if str(x[3]).split(' · ')[0] in WEAK")]
check('KR.lake_inside_land' in _blk and "if _wt and not LAKE_TYPE_RX.search(str(p.get('t') or '')) and not re.search(r'\\breservoir\\b', str(p.get('n') or ''), re.I)" in _blk and "_kr('KPC_LAKE_ONLY_IF_LAKE')" in _blk,
      'a lake-type park (fishing lake, reservoir) keeps its lake; other parks: lake inside their land, else CHECK; behind the switch')
check("'water outline only' not in str(x[3])]" in _blk, 'land = every joined row that is not a lake surface')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
