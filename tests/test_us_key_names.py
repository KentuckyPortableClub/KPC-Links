"""Nov 2: a local variable named '_kr' inside run() hid the module-level switch test _kr(), so every US state build stopped
with "cannot access local variable '_kr'". This test fails if any function in kpc_us_key.py assigns to the name of a
module-level function it also calls (the same mistake, any name). Run: python3 tests/test_us_key_names.py (no network)."""
import ast, pathlib, sys

SRC = pathlib.Path(__file__).resolve().parent.parent / '.github/scripts/kpc_us_key.py'
tree = ast.parse(SRC.read_text(encoding='utf-8'))
top = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
bad = []
for fn in ast.walk(tree):
    if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)): continue
    glob = {g for n in ast.walk(fn) if isinstance(n, (ast.Global, ast.Nonlocal)) for g in n.names}
    stored = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)} - glob
    called = {n.func.id for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    for name in sorted(stored & called & top):
        bad.append(f'{fn.name}() line {fn.lineno}: assigns to {name!r}, which hides the function {name}()')
print('\n'.join(('FAIL ' + b) for b in bad) or 'ok   no function hides a module-level function it calls')
sys.exit(1 if bad else 0)
