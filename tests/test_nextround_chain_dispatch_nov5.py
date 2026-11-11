#!/usr/bin/env python3
"""Next round C1 (Nov 5; Brandon's yes relayed via Super, 4:32 AM CST Nov 5): a bot-started US key run fires no workflow_run, so it
DISPATCHES the Canada and world keys (chained=us-key); a bot-started Canada run that built dispatches the world key (chained=ca-key).
kpc_key_order.py checks such a dispatch as a chained start. No network, no run. Run: python3 -B tests/test_nextround_chain_dispatch_nov5.py"""
import importlib.util, json, os, pathlib, re, sys, tempfile
import yaml
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
spec = importlib.util.spec_from_file_location('kpc_key_order', HERE / '.github/scripts/kpc_key_order.py'); KO = importlib.util.module_from_spec(spec); spec.loader.exec_module(KO)
import kpc_key_freeze as KF
ok = True
def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)
R = {k: KF.rules_hash(k) for k in KF.RULE_FILES}
CUR = {k: {'build': k[:2].upper() + '-9', 'built': '2026-11-05 12:00 UTC', 'rules': R[k]} for k in R}
OLD = {k: dict(CUR[k], rules='0123456789ab') for k in R}
def run(kind, idx, env):
    with tempfile.TemporaryDirectory() as t:
        cwd = os.getcwd(); os.chdir(t)
        try:
            for k, st in idx.items():
                os.makedirs(f'data/{k}', exist_ok=True); json.dump(st, open(f'data/{k}/index.json', 'w'))
            e = pathlib.Path(t) / 'env'; e.write_text(''); os.environ['GITHUB_ENV'] = str(e)
            return KO.check(kind, env), e.read_text()
        finally: os.chdir(cwd); os.environ.pop('GITHUB_ENV', None)
# --- kpc_key_order: a chained dispatch is a chained start
up = {k: CUR[k] for k in R}
r = run('ca-key', up, {'GITHUB_EVENT_NAME': 'workflow_dispatch', 'KPC_CHAINED': 'us-key'})
check(r[0] == 'skip' and 'SKIP=1' in r[1], f'Canada up to date, dispatched chained=us-key: skips like a workflow_run start ({r[0]})')
r = run('ca-key', up, {'GITHUB_EVENT_NAME': 'workflow_dispatch', 'KPC_CHAINED': ''})
check(r[0] == 'go' and 'SKIP' not in r[1], f'Canada up to date, a by-hand dispatch (chained blank): still builds ({r[0]})')
r = run('world-key', {'us-key': CUR['us-key'], 'ca-key': OLD['ca-key'], 'world-key': OLD['world-key']}, {'GITHUB_EVENT_NAME': 'workflow_dispatch', 'KPC_CHAINED': 'us-key'})
check(r[0] == 'wait' and 'ORDER_WAIT=1' in r[1], f'world on old rules, Canada not done, dispatched by the US key: WAITS ({r[0]})')
r = run('world-key', {'us-key': CUR['us-key'], 'ca-key': CUR['ca-key'], 'world-key': OLD['world-key']}, {'GITHUB_EVENT_NAME': 'workflow_dispatch', 'KPC_CHAINED': 'ca-key'})
check(r[0] == 'go', f'world on old rules, US + Canada done, dispatched by the Canada key: builds ({r[0]})')
r = run('ca-key', up, {'GITHUB_EVENT_NAME': 'workflow_dispatch', 'KPC_CHAINED': 'world-key'})
check(r[0] == 'go', f"a chained value that is not a key before this one ('world-key' for Canada) is ignored: a by-hand run ({r[0]})")
r = run('ca-key', up, {'GITHUB_EVENT_NAME': 'workflow_dispatch', 'KPC_CHAINED': 'us-key', 'FORCE': 'yes'})
check(r[0] == 'go', f'FORCE=yes still wins ({r[0]})')
# --- the workflows
W = {f: yaml.safe_load(open(HERE / f'.github/workflows/kpc-{f}-key.yml')) for f in ('us', 'ca', 'world')}
T = {f: open(HERE / f'.github/workflows/kpc-{f}-key.yml').read() for f in W}
on = lambda f: W[f][True]
for f in ('ca', 'world'):
    check('chained' in on(f)['workflow_dispatch']['inputs'] and on(f)['workflow_dispatch']['inputs']['chained'].get('default') == '', f'{f} key: a chained input, blank by default')
    check(re.search(r"BUILD ORDER[^\n]*\n(?:\s+#[^\n]*\n)?\s+env:\n(?:\s+[A-Z_]+:[^\n]*\n)*\s+KPC_CHAINED: \$\{\{ inputs\.chained \}\}", T[f]) is not None, f'{f} key: the BUILD ORDER step gets KPC_CHAINED from the input')
    check(len(on(f)['workflow_dispatch']['inputs']) <= 10, f'{f} key: at most 10 dispatch inputs')
c = W['us']['jobs']['chain']
check(c['needs'] == ['plan', 'join'] and 'triggering_actor' not in c['if'] and '!cancelled()' in c['if'], 'US chain job: after plan + join, for every actor, never for a cancelled run (dispatch is the only path)')
check(c['permissions'] == {'actions': 'write', 'contents': 'read'}, 'US chain job: actions write, contents read')
run_ = c['steps'][0]['run']
check('gh workflow run kpc-ca-key.yml' in run_ and 'world' not in run_ and '-f chained=us-key' in run_ and '--ref main' in run_, 'US chain job: dispatches ONLY kpc-ca-key.yml with chained=us-key on main')
c = W['ca']['jobs']['chain']
check(c['needs'] == ['run'] and 'triggering_actor' not in c['if'] and 'skip' not in c['if'] and '!cancelled()' in c['if'], 'Canada chain job: after every Canada run that was not cancelled (built or skipped)')
check('gh workflow run kpc-world-key.yml' in c['steps'][0]['run'] and '-f chained=ca-key' in c['steps'][0]['run'], 'Canada chain job: dispatches the world key with chained=ca-key')
check(W['ca']['jobs']['run']['outputs']['skip'] == '${{ steps.skipped.outputs.skip }}' and any(s.get('id') == 'skipped' and s.get('if') == 'always()' for s in W['ca']['jobs']['run']['steps']), 'Canada run job: exposes skip from an always() step')
check('chain' not in W['world']['jobs'], 'the world key dispatches nothing (it is last)')
check([x['cron'] for x in on('us')['schedule']] == ['37 9 1 * *', '17 9 * * *', '46 11 * * *'] and [x['cron'] for x in on('ca')['schedule']] == ['43 10 2 * *', '49 9 * * *'] and [x['cron'] for x in on('world')['schedule']] == ['17 11 3 * *', '7 10 * * *'], 'no new cron in the three keys')
check('workflow_run' not in on('ca') and 'workflow_run' not in on('world'), 'no workflow_run trigger on the Canada or world key (dispatch only)')
check('kpc_key_order.py' in KF.NOT_RULES and all('kpc_key_order.py' not in ' '.join(v) for v in KF.RULE_FILES.values()), 'kpc_key_order.py is not a rule file (no rules hash moves)')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
