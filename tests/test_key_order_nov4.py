#!/usr/bin/env python3
"""Offline test for the Nov 4 key build order (links-06; per Brandon via Super Head Bot (relayed), 5:48 AM CST Nov 4, the key-order part:
"Full world rebuild yes after us and Canada..stand by for more"): .github/scripts/kpc_key_order.py and its wiring in kpc-ca-key.yml / kpc-world-key.yml.
No network. The 'today' stamps are the real ones on main on Nov 4 (none has a rules hash yet)."""
import importlib.util, json, os, pathlib, re, subprocess, sys, tempfile
import yaml

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
spec = importlib.util.spec_from_file_location('kpc_key_order', HERE / '.github/scripts/kpc_key_order.py'); KO = importlib.util.module_from_spec(spec); spec.loader.exec_module(KO)
import kpc_key_freeze as KF
ok = True
BASE = next((r for r in ('origin/main', 'main') if subprocess.run(['git', 'rev-parse', '-q', '--verify', r], cwd=HERE, capture_output=True).returncode == 0), 'main')


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


R = {k: KF.rules_hash(k) for k in KF.RULE_FILES}
TODAY = {'us-key': {'build': 'US-41695918852', 'built': '2026-11-03 19:40 UTC'}, 'ca-key': {'build': 'CA-41739774609', 'built': '2026-11-03 23:49 UTC'}, 'world-key': {}}
NEW = {k: {'build': k[:2].upper() + '-9', 'built': '2026-11-05 12:00 UTC', 'rules': R[k]} for k in R}
OLD = {k: dict(NEW[k], rules='0123456789ab') for k in R}


def run(kind, idx, event='schedule', force=''):
    with tempfile.TemporaryDirectory() as t:
        cwd = os.getcwd(); os.chdir(t)
        try:
            for k, st in idx.items():
                os.makedirs(f'data/{k}', exist_ok=True); json.dump(st, open(f'data/{k}/index.json', 'w'))
            env = pathlib.Path(t) / 'env'; env.write_text('')
            os.environ['GITHUB_ENV'] = str(env)
            res = KO.check(kind, {'GITHUB_EVENT_NAME': event, 'FORCE': force})
            return res, env.read_text()
        finally: os.chdir(cwd); os.environ.pop('GITHUB_ENV', None)


# --- today (real stamps: no key is on the current rules)
r, e = run('world-key', TODAY)
check(r == 'wait' and 'SKIP=1' in e and 'ORDER_WAIT=1' in e, 'today: the world nightly waits (US and Canada have not finished new-rules builds): SKIP=1, nothing built')
r, e = run('ca-key', TODAY)
check(r == 'wait' and 'SKIP=1' in e, 'today: Canada waits for the US new-rules build')
# --- the order, step by step
r, e = run('ca-key', dict(TODAY, **{'us-key': NEW['us-key']}), event='workflow_run')
check(r == 'go' and 'SKIP' not in e, 'US finished (chained start of Canada): Canada builds on the new rules')
r, e = run('world-key', dict(TODAY, **{'us-key': NEW['us-key']}), event='workflow_run')
check(r == 'wait' and 'SKIP=1' in e, 'US finished, Canada not yet: the chained world start waits cleanly')
r, e = run('world-key', dict(TODAY, **{'ca-key': NEW['ca-key']}))
check(r == 'wait', 'Canada on the new rules but the US not: the world still waits')
r, e = run('world-key', dict(TODAY, **{'us-key': NEW['us-key'], 'ca-key': NEW['ca-key']}), event='workflow_run')
check(r == 'go' and 'SKIP' not in e, 'US and Canada both finished: the chained world start builds (the full world rebuild)')
r, e = run('world-key', dict(TODAY, **{'us-key': NEW['us-key'], 'ca-key': OLD['ca-key']}))
check(r == 'wait', 'a Canada build on OLD rules does not count as finished')
r, e = run('world-key', {'us-key': NEW['us-key'], 'ca-key': NEW['ca-key'], 'world-key': NEW['world-key']}, event='workflow_run')
check(r == 'skip' and 'SKIP=1' in e and 'ORDER_WAIT' not in e, 'everything on the current rules: a chained start has nothing to catch up and skips')
r, e = run('world-key', {'us-key': TODAY['us-key'], 'world-key': NEW['world-key']}, event='schedule')
check(r == 'go' and 'SKIP' not in e, 'world already on the current rules: a normal nightly goes on as before (no new wait)')
r, e = run('ca-key', {'ca-key': NEW['ca-key']}, event='workflow_run')
check(r == 'skip', 'Canada on the current rules: the chained start after each US run skips cleanly')
r, e = run('world-key', TODAY, force='yes')
check(r == 'go' and 'SKIP' not in e, 'FORCE=yes (by hand) skips the order check')
r, e = run('us-key', TODAY)
check(r == 'go', 'the US key waits for nothing (first in the order)')
_oc = KO.on_current
KO.on_current = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('boom'))
r, e = run('world-key', TODAY)
KO.on_current = _oc
check(r == 'wait' and 'SKIP=1' in e, 'an error in the check = wait (the safe direction), never a failure')
_rh = KF.rules_hash; del KF.rules_hash
r, e = run('world-key', TODAY)
KF.rules_hash = _rh
check(r == 'go' and 'SKIP' not in e, 'KPC-Links without links-04 (no rules hash): no order, the run goes on as before (never waits forever)')
check('kpc_key_order.py' in KF.NOT_RULES, 'kpc_key_order.py is listed as not a rule file (it never changes the rules hash)')
check(KO.WAIT_FOR == {'ca-key': ('us-key',), 'world-key': ('us-key', 'ca-key')}, 'WAIT_FOR = Canada after US; world after US + Canada (one line per key: easy to extend)')

# --- the workflows
names = {k: yaml.safe_load(open(HERE / f'.github/workflows/kpc-{k}.yml'))['name'] for k in ('us-key', 'ca-key', 'world-key')}
for kind, want in (('ca-key', ['us-key']), ('world-key', ['us-key', 'ca-key'])):
    f = HERE / f'.github/workflows/kpc-{kind}.yml'; txt = f.read_text(); y = yaml.safe_load(txt); on = y.get(True) or y.get('on')
    wr = on.get('workflow_run') or {}
    check(not wr, f'{kind}: no workflow_run trigger (the key before it dispatches it once)')
    main = subprocess.run(['git', 'show', f'{BASE}:.github/workflows/kpc-{kind}.yml'], cwd=HERE, capture_output=True, text=True).stdout
    om = yaml.safe_load(main); om = om.get(True) or om.get('on')
    check(on.get('schedule') == om.get('schedule'), f'{kind}: no new cron (schedule same as main)')
    job = next(iter(y['jobs'].values()))
    steps = [s.get('name', '') for s in job['steps']]
    i_f = next(i for i, s in enumerate(steps) if s.startswith('FREEZE CHECK')); i_o = next(i for i, s in enumerate(steps) if s.startswith('BUILD ORDER'))
    i_t = next(i for i, s in enumerate(steps) if s.startswith("Tonight's list"))
    check(i_f < i_o < i_t, f'{kind}: BUILD ORDER runs after the freeze check and before tonight\'s list (SKIP=1 stops the build)')
    run_txt = job['steps'][i_o]['run']
    check(f'kpc_key_order.py check {kind}' in run_txt and 'SKIP' in run_txt, f'{kind}: the step calls the order check; a stopped check also skips')
    # run the step's shell for real (cwd = a temp repo that shares .github)
    with tempfile.TemporaryDirectory() as t:
        os.symlink(HERE / '.github', pathlib.Path(t) / '.github')
        for k, st in TODAY.items():
            os.makedirs(f'{t}/data/{k}', exist_ok=True); json.dump(st, open(f'{t}/data/{k}/index.json', 'w'))
        envf = pathlib.Path(t) / 'env'; envf.write_text('')
        p = subprocess.run(['bash', '-e', '-c', run_txt], cwd=t, capture_output=True, text=True, env=dict(os.environ, GITHUB_ENV=str(envf), GITHUB_EVENT_NAME='schedule', FORCE=''))
        check(p.returncode == 0 and 'SKIP=1' in envf.read_text() and 'WAITS' in p.stdout, f'{kind}: the real step on today\'s stamps: exit 0, SKIP=1, one WAITS notice')
        envf.write_text('SKIP=1\n')
        p = subprocess.run(['bash', '-e', '-c', run_txt], cwd=t, capture_output=True, text=True, env=dict(os.environ, GITHUB_ENV=str(envf), SKIP='1'))
        check(p.returncode == 0 and 'Key build order' not in p.stdout, f'{kind}: frozen (SKIP=1 already): the order check does not run')
    # a chained start without a rules change: the plan must NOT turn into a by-hand full build
    check("RULES_CHANGED" in txt and "workflow_run" in txt, f'{kind}: a chained start builds only a new-rules catch-up (order check: skip when on current rules)')
us = yaml.safe_load(open(HERE / '.github/workflows/kpc-us-key.yml')); uon = us.get(True) or us.get('on')
check('workflow_run' not in uon, 'kpc-us-key.yml: no workflow_run (US is first)')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
