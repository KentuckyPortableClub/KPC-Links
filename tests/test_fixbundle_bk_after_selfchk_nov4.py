#!/usr/bin/env python3
"""Offline test, Nov 4 PM fix bundle item 11a (Quality v3 should-fix; Brandon's yes relayed via Super Head Bot, 4:53 PM CST Nov 4):
kpc_us_key.py runs the self-checks (_selfchk) BEFORE it writes 'bk' (kpc_key_facts.stamp), so a park that KPC_SELF_CHECKS=hold
demotes from joined (m) to check (c) never keeps a bk worked out from its old joins. No network."""
import ast, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
import kpc_key_facts as KF
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


tree = ast.parse(open(HERE / '.github/scripts/kpc_us_key.py', encoding='utf-8').read())
run = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run')
calls = [(n.lineno, ast.unparse(n.func)) for n in ast.walk(run) if isinstance(n, ast.Call)]
sc = [l for l, f in calls if f == '_selfchk']; bk = [l for l, f in calls if f == 'KF.stamp']
check(len(sc) == 1 and len(bk) == 1 and sc[0] < bk[0], f'run(): _selfchk (line {sc}) comes before KF.stamp (line {bk})')

# what hold does to a park (kpc_us_key._selfchk), then bk: two joined pieces, the near one is the one a self-check drops
ring = lambda x, y: [[[x, y], [x + .01, y], [x + .01, y + .01], [x, y + .01], [x, y]]]   # noqa: E731
look = lambda e: ({'near': ring(-85.0, 37.0), 'far': ring(-84.0, 37.0)}[e[0]], 'SP')     # noqa: E731
park = lambda: {'m': [['near', 'Near SP', 10, 'name'], ['far', 'Far SP', 10, 'name']], 'c': []}   # noqa: E731
p_old = park(); KF.stamp({'X': p_old}, lambda r: (37.005, -85.005), look)
p_new = park(); p_new['c'] = [['far', 'Far SP', 10, 'self-check: outline far from the pin']] ; p_new['m'] = []   # hold, the far piece left on check
KF.stamp({'X': p_new}, lambda r: (37.005, -85.005), look)
check(p_old['bk'][0] == 'near' and p_new['bk'][0] == 'far', f"bk follows what is left after the self-check (before: {p_old['bk'][:2]}, after: {p_new['bk'][:2]})")
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
