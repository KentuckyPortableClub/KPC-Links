#!/usr/bin/env python3
"""Review F22 (KPC owner, 22 Nov 2026): the pull-request scope check covers the Canada and world keys too, not only the US key.
An undeclared Canada or world rule edit is refused; the same edit with a new entry chained from the last build is fine; the
workflow runs the check once per kind. Offline."""
import json, pathlib, shutil, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_freeze as F  # noqa: E402
import kpc_key_scope_check as C  # noqa: E402
ok = True
def check(msg, cond):
    global ok
    ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + msg, flush=True)

def tree(kind):
    t = pathlib.Path(tempfile.mkdtemp())
    for rel in list(F.RULE_FILES[kind]) + [F.VERSION_FILE, C.INDEX[kind]]:
        src = ROOT / rel
        if src.is_file():
            (t / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy(src, t / rel)
    return t

def set_built(t, kind, h):
    p = t / C.INDEX[kind]; i = json.loads(p.read_text(encoding='utf-8')); i['rules'] = h; p.write_text(json.dumps(i), encoding='utf-8')

def edit(t, kind):
    f = t / {'ca-key': '.github/scripts/kpc_ca_key.py', 'world-key': '.github/scripts/kpc_world_key.py'}[kind]
    f.write_text(f.read_text(encoding='utf-8') + '\nKPC_TEST_ONLY = 1\n', encoding='utf-8')

def add_entry(t, kind, **kw):
    p = t / F.SCOPE_FILES[kind]; s = json.loads(p.read_text(encoding='utf-8'))
    e = {'id': '2026-11-22-test', 'when': '2026-11-22', 'why': 'test', 'scope': 'none'}; e.update(kw)
    s.setdefault('changes', []).append(e); p.write_text(json.dumps(s, indent=1), encoding='utf-8')

check('the check knows the Canada and world keys', {'us-key', 'ca-key', 'world-key'} <= set(C.INDEX))
for kind in ('ca-key', 'world-key'):
    base = tree(kind); built = F.rules_hash(kind, base); set_built(base, kind, built)
    check(f'{kind}: the real repo against itself is fine', C.check(ROOT, ROOT, kind) == [])
    h = tree(kind); set_built(h, kind, built); edit(h, kind)
    w = C.check(base, h, kind)
    check(f'{kind}: a rule edit with no scope entry is REFUSED', len(w) == 1 and 'has no new entry' in w[0])
    h = tree(kind); set_built(h, kind, built); edit(h, kind); add_entry(h, kind, **{'from': built})
    check(f'{kind}: the same edit with a new entry from the last build is fine', C.check(base, h, kind) == [])
wf = (ROOT / '.github/workflows/kpc-key-scope-check.yml').read_text(encoding='utf-8')
check('the workflow runs the check for each kind and watches the Canada and world rule files',
      'for kind in us-key ca-key world-key' in wf and "'.github/scripts/kpc_ca_key.py'" in wf and "'.github/scripts/kpc_world_key.py'" in wf)
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
