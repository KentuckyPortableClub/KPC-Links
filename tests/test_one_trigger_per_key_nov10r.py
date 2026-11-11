"""Owner rule, 2026-11-10: each key is started ONCE per run of the key before it, by dispatch only. A key workflow never has both a
workflow_run trigger and an upstream dispatch for the same edge (that started CA and world 2-4 times). No network."""
import pathlib, re, sys
import yaml

W = pathlib.Path(__file__).resolve().parent.parent / '.github' / 'workflows'
ok = True


def check(c, m):
    global ok
    print(('ok   ' if c else 'FAIL ') + m)
    ok = ok and bool(c)


def load(f):
    y = yaml.safe_load((W / f).read_text(encoding='utf-8'))
    return y, (y.get('on') or y.get(True) or {})


KEYS = {'us': 'kpc-us-key.yml', 'ca': 'kpc-ca-key.yml', 'world': 'kpc-world-key.yml', 'postcheck': 'kpc-key-postcheck.yml'}
names = {k: load(f)[0]['name'] for k, f in KEYS.items()}
dispatched_by = {}   # target workflow file -> list of (workflow, job) that dispatch it
for k, f in KEYS.items():
    y, _ = load(f)
    for jn, j in y['jobs'].items():
        for s in j.get('steps', []):
            for t in re.findall(r'gh workflow run "?(kpc-[a-z-]+\.yml)', str(s.get('run', ''))):
                dispatched_by.setdefault(t, []).append((f, jn))
for k, f in KEYS.items():
    y, on = load(f)
    wr = on.get('workflow_run') or {}
    for up in wr.get('workflows') or []:
        up_file = next((KEYS[x] for x in KEYS if names[x] == up), None)
        dup = [d for d in dispatched_by.get(f, []) if d[0] == up_file]
        check(not dup, f'{f}: workflow_run on {up!r} AND a dispatch from it (same edge twice)')
    check(not wr, f'{f}: no workflow_run trigger')
for target, edges in dispatched_by.items():
    ups = [e[0] for e in edges]
    check(len(ups) == len(set(ups)), f'{target}: dispatched from each upstream workflow by exactly one job ({edges})')
check(dispatched_by.get('kpc-ca-key.yml') == [('kpc-us-key.yml', 'chain')], 'US run -> exactly one Canada start')
check(dispatched_by.get('kpc-world-key.yml') == [('kpc-ca-key.yml', 'chain')], 'Canada run -> exactly one world start (the US key does not start it)')
pcs = sorted(dispatched_by.get('kpc-key-postcheck.yml', []))
check(pcs == [('kpc-ca-key.yml', 'postcheck'), ('kpc-us-key.yml', 'postcheck'), ('kpc-world-key.yml', 'postcheck')], 'each key dispatches its own postcheck once')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
