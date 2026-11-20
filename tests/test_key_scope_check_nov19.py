#!/usr/bin/env python3
"""S2 (keys-first rev 3.1, F7; Opus 19 Nov 2026): a US key rule-file edit with no scope entry is refused. Offline.
Prints PASS / FAIL lines and ends ALL PASS or SOME FAILED."""
import json, pathlib, shutil, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_freeze as F  # noqa: E402
import kpc_key_scope_check as C  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


def tree():
    t = pathlib.Path(tempfile.mkdtemp())
    for rel in list(F.RULE_FILES['us-key']) + [F.VERSION_FILE, 'data/us-key/index.json']:
        src = ROOT / rel
        if src.is_file():
            (t / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, t / rel)
    return t


def set_built(t, h):
    p = t / 'data/us-key/index.json'
    i = json.loads(p.read_text(encoding='utf-8'))
    i['rules'] = h
    p.write_text(json.dumps(i), encoding='utf-8')


def flip_switch(t):
    p = t / '.github/key-switches.json'
    s = json.loads(p.read_text(encoding='utf-8'))
    s['KPC_TEST_ONLY_SWITCH'] = 'off'
    p.write_text(json.dumps(s, indent=1), encoding='utf-8')


def add_entry(t, **kw):
    p = t / F.SCOPE_FILES['us-key']
    s = json.loads(p.read_text(encoding='utf-8'))
    e = {'id': '2026-11-19-test', 'when': '2026-11-19', 'why': 'test', 'scope': 'none'}
    e.update(kw)
    s['changes'].append(e)
    p.write_text(json.dumps(s, indent=1), encoding='utf-8')


base = tree()
built = F.rules_hash('us-key', base)
set_built(base, built)

check('the real repo against itself: fine', C.check(ROOT, ROOT) == [])

h = tree(); set_built(h, built)
check('no rule file changed: fine', C.check(base, h) == [])

h = tree(); set_built(h, built); flip_switch(h)
w = C.check(base, h)
check('a switch edit with no scope entry is REFUSED', len(w) == 1 and 'has no new entry' in w[0])

h = tree(); set_built(h, built); flip_switch(h); add_entry(h, **{'from': built})
check('the same edit with a new entry from the last build, scope none: fine', C.check(base, h) == [])

h = tree(); set_built(h, built); flip_switch(h); add_entry(h, **{'from': 'abc123abc123'})
w = C.check(base, h)
check('a lone new entry from the wrong hash is REFUSED (the run would rebuild all 50)', len(w) == 1 and 'UNDECLARED' in w[0])

# Fable's review of #294 (2, probe_scope.py): a STACKED draft. Main holds a merged-OFF draft whose entry is from the last build;
# the next draft's entry is from the hash the first one moved to. The run (pending_scope) reads the chain as declared.
b2 = tree(); set_built(b2, built); flip_switch(b2); add_entry(b2, **{'id': 'draft-1', 'from': built})
h2 = tree(); set_built(h2, built); flip_switch(h2); add_entry(h2, **{'id': 'draft-1', 'from': built})
p_ = h2 / '.github/key-switches.json'; d_ = json.loads(p_.read_text()); d_['KPC_TEST_ONLY_SWITCH_2'] = 'off'; p_.write_text(json.dumps(d_, indent=1))
add_entry(h2, **{'id': 'draft-2', 'from': F.rules_hash('us-key', b2)})
check('the run itself reads the stacked draft as declared', F.pending_scope('us-key', built, h2)[0] is not None)
check('a stacked draft (its entry from the hash the draft before it moved to) is FINE', C.check(b2, h2) == [])
h3 = tree(); set_built(h3, built); flip_switch(h3); add_entry(h3, **{'id': 'draft-1', 'from': built})
p_ = h3 / '.github/key-switches.json'; d_ = json.loads(p_.read_text()); d_['KPC_TEST_ONLY_SWITCH_2'] = 'off'; p_.write_text(json.dumps(d_, indent=1))
check('a stacked draft that adds NO entry of its own is REFUSED', any('has no new entry' in x for x in C.check(b2, h3)))

h = tree(); set_built(h, built); flip_switch(h); add_entry(h, **{'from': built, 'scope': 'some'})
w = C.check(base, h)
check("a new entry with a scope that is not 'none', 'all' or a dict is REFUSED", len(w) == 1 and "scope 'some'" in w[0])

h = tree(); set_built(h, built); flip_switch(h); add_entry(h, **{'from': built, 'why': ''})
check('a new entry with no why is REFUSED', any('needs an id, a when and a why' in x for x in C.check(base, h)))

check('the command ends 1 when refused, 0 when fine',
      C.main(['--base', str(base), '--head', str(tree())]) == 0 and
      (lambda t: (set_built(t, built), flip_switch(t), C.main(['--base', str(base), '--head', str(t)]))[2])(tree()) == 1)

src = (ROOT / '.github/scripts/kpc_key_scope_check.py').as_posix()
check('the check is not a rule file (it moves no hash)', not any(src.endswith(r) for r in F.RULE_FILES['us-key']))

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
