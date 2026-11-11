#!/usr/bin/env python3
"""Every bot script that makes web requests gets the shared network guard (owner rule, 2026-11-10): it imports kpc_net_guard,
directly or through a module that installs it when imported (kpc_host_pace, kpc_http_cache, kpc_master). Rule files are never
edited for this: they get it through those modules (checked from the import graph, and by a real import where that is safe).
A NEW fetcher script without the guard fails this test; the scripts listed in NOT_YET are known and reported, not silently allowed."""
import ast, os, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
S = ROOT / '.github/scripts'
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


INSTALLERS = {'kpc_net_guard', 'kpc_host_pace', 'kpc_http_cache', 'kpc_master'}
FETCH = re.compile(r'urlopen\(|build_opener\(|urlretrieve\(|http\.client\.|\brequests\.(get|post|head|Session)\(')
# The standalone fetchers that read map layers / agency pages: each carries the one-line install itself.
DIRECT = ['kpc_state_trails', 'kpc_us_trails', 'kpc_state_gis', 'kpc_checkup', 'kpc_state_camps', 'kpc_state_camps_probe', 'kpc_link_harvest',
          'kpc_parking_explorer', 'kpc_us_access', 'kpc_canada_bounds', 'kpc_research_inbox']
# Rule files (never edited here) that fetch: guarded through an installer module they already import.
RULES = {'kpc_us_key': 'kpc_host_pace', 'kpc_ca_key': 'kpc_host_pace', 'kpc_world_key': 'kpc_host_pace', 'kpc_fers': 'kpc_http_cache', 'kpc_owned': 'kpc_http_cache'}
# Still unguarded and not ours to edit (kpc_fers*.py is another owner's file): reported, not silently allowed.
NOT_YET = {'kpc_fers_layered'}


def top_imports(path):
    """Local modules imported at module level (not inside a function: those run too late to guard the first request)."""
    out = set()
    try: tree = ast.parse(path.read_text(encoding='utf-8', errors='replace'))
    except SyntaxError: return out
    def walk(n):
        for c in ast.iter_child_nodes(n):
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)): continue
            if isinstance(c, ast.Import): out.update(a.name.split('.')[0] for a in c.names)
            elif isinstance(c, ast.ImportFrom) and c.module and not c.level: out.add(c.module.split('.')[0])
            walk(c)
    walk(tree)
    return {m for m in out if (S / f'{m}.py').exists()}


GRAPH = {p.stem: top_imports(p) for p in S.glob('*.py')}


def guarded(names):
    seen, todo = set(), list(names)
    while todo:
        m = todo.pop()
        if m in seen: continue
        seen.add(m)
        if m in INSTALLERS: return True
        todo += GRAPH.get(m, ())
    return False


check('the installer modules call kpc_net_guard.install() at import', all('kpc_net_guard.install()' in (S / f'{m}.py').read_text() for m in INSTALLERS - {'kpc_net_guard'}))
for m in DIRECT:
    src = (S / f'{m}.py').read_text(encoding='utf-8')
    check(f'{m}.py imports and installs the guard at module level', 'kpc_net_guard' in GRAPH[m] and 'kpc_net_guard.install()' in src)
for m, via in RULES.items():
    check(f'rule file {m}.py is guarded through {via} (import graph; the file itself is not edited)', via in GRAPH[m] and guarded([m]))

files = [p for p in sorted(S.glob('*.py')) if p.stem not in ('kpc_net_guard', 'kpc_full_suite')] + sorted((ROOT / 'tools').glob('*.py'))
unguarded = []
for p in files:
    txt = p.read_text(encoding='utf-8', errors='replace')
    if not FETCH.search(txt): continue
    deps = top_imports(p) if p.parent == S else {m for m in re.findall(r'^\s*import (kpc_\w+)', txt, re.M)}
    if not guarded({p.stem} | deps): unguarded.append(p.stem)
new = sorted(set(unguarded) - NOT_YET)
check('every fetcher is guarded or in the reported NOT_YET list' + (f' (new unguarded: {new})' if new else ''), not new)
gone = sorted(NOT_YET - set(unguarded))
if gone: print(f'NOTE: guarded now, drop from NOT_YET: {gone}')

# a real import in a fresh process for the modules that are safe to import (no run at import), with the network stubbed
STUB = ("import socket, sys; sys.path.insert(0, sys.argv[1]); "
        "socket.getaddrinfo = socket.create_connection = lambda *a, **k: (_ for _ in ()).throw(OSError('no network in test')); "
        "import importlib; importlib.import_module(sys.argv[2]); import kpc_net_guard as G; print('INSTALLED', G.installed())")
for m in ('kpc_owned', 'kpc_http_cache', 'kpc_host_pace', 'kpc_master', 'kpc_research_inbox'):
    r = subprocess.run([sys.executable, '-B', '-c', STUB, str(S), m], capture_output=True, text=True, cwd=str(ROOT), timeout=120)
    check(f'importing {m} (network stubbed) installs the guard', 'INSTALLED True' in r.stdout)
    if 'INSTALLED True' not in r.stdout: print(r.stderr[-400:])
r = subprocess.run([sys.executable, '-B', '-c', "import sys; sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2]); "
                    "import socket; socket.getaddrinfo = socket.create_connection = lambda *a, **k: (_ for _ in ()).throw(OSError('no network')); "
                    "import kpc_pc_helper, kpc_net_guard as G; print('INSTALLED', G.installed())", str(S), str(ROOT / 'tools')],
                   capture_output=True, text=True, cwd=str(ROOT), timeout=120)
check('the PC helper (tools/) gets the guard through kpc_master', 'INSTALLED True' in r.stdout)
if 'INSTALLED True' not in r.stdout: print(r.stdout[-300:], r.stderr[-400:])

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
