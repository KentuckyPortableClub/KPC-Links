#!/usr/bin/env python3
"""Offline test, key hotfix patch 2 (Nov 5; Brandon's approval relayed via Super Head Bot, 4:21 AM CST):
 a. when the rules changed (RULES_CHANGED=1 from the freeze check), the US key plan builds EVERY state whatever the states input
    says, and says so (replays 41984527710: STATES=CT ID ME ND OH TN WV, RULES CHANGED 6bb847b4f6cd -> 3dc53f70256a, built 7 states
    with full=0). Runs the plan step's own Python from kpc-us-key.yml. Fails on the old plan.
 b. a run started by github-actions[bot] (no workflow_run event) starts the post-key check itself (workflow_dispatch). No network."""
import json, os, pathlib, re, subprocess, sys, tempfile
import yaml

HERE = pathlib.Path(__file__).resolve().parent.parent
W = HERE / '.github/workflows'
ok = True
ALL = set('AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split())


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


y = yaml.safe_load(open(W / 'kpc-us-key.yml', encoding='utf-8'))
p = next(s for s in y['jobs']['plan']['steps'] if s.get('id') == 'p')
code = re.search(r"<<'PY' >> \"\$GITHUB_OUTPUT\"\n(.*?)\nPY", p['run'], re.S).group(1)


def plan(**env):
    with tempfile.TemporaryDirectory() as t:
        e = {k: v for k, v in os.environ.items() if k not in ('RULES_CHANGED', 'STATES', 'SCHED', 'FROZEN')}; e.update(env)
        r = subprocess.run([sys.executable, '-B', '-c', code], cwd=t, env=e, capture_output=True, text=True)
    out = dict(l.split('=', 1) for l in r.stdout.splitlines() if '=' in l and not l.startswith('::'))
    st = {s for g in json.loads(out.get('groups') or '[]') for s in g['states'].split()}
    return out.get('full'), st, r.stdout + r.stderr   # hotfix 3: the plan's log lines go to stderr (stdout is GITHUB_OUTPUT)


Q = 'CT ID ME ND OH TN WV'
full, st, log = plan(RULES_CHANGED='1', STATES=Q, NJOBS='3', SCHED='')
check(full == '1' and st == ALL, f"rules changed + states '{Q}' (41984527710): ALL {len(ALL)} states, full=1 (got full={full}, {len(st)} states)")
check("is OVERRIDDEN" in log and Q in log, 'the plan says the states input was overridden, and names it')
full, st, _ = plan(RULES_CHANGED='1', STATES='', NJOBS='3', SCHED='17 9 * * *')
check(full == '1' and st == ALL, 'rules changed, no states (the nightly): all states, as before')
full, st, _ = plan(STATES=Q, NJOBS='3', SCHED='')
check(full == '0' and st == set(Q.split()), 'rules NOT changed + states given: only those states (by-hand runs unchanged)')
full, st, _ = plan(FROZEN='1', RULES_CHANGED='1', STATES=Q, NJOBS='3', SCHED='')
check(st == set(), 'frozen still builds nothing (the freeze wins over the rules change, as before)')
j = y['jobs']['join']; stamp = next(s for s in j['steps'] if 'kpc_key_freeze.py stamp us-key' in str(s.get('run', '')))
check("needs.plan.outputs.full == '1'" in stamp['env']['KPC_FULL_BUILD'], 'the join stamps the rules hash from the plan\'s full=1 (KPC_FULL_BUILD)')

pc = y['jobs'].get('postcheck') or {}
check(set(pc.get('needs') or []) >= {'join'} and 'triggering_actor' not in str(pc.get('if')) and "needs.join.result != 'cancelled'" in str(pc.get('if')),
      'every US key run (not cancelled, join not skipped) dispatches the post-key check')
check((pc.get('permissions') or {}).get('actions') == 'write' and any('gh workflow run kpc-key-postcheck.yml' in str(s.get('run')) and '-f key=us' in str(s.get('run')) for s in pc.get('steps', [])),
      'it dispatches kpc-key-postcheck.yml with key=us (actions: write only in that job)')
k = yaml.safe_load(open(W / 'kpc-key-postcheck.yml', encoding='utf-8')); on = k.get('on') or k.get(True)
check('key' in (on['workflow_dispatch'].get('inputs') or {}) and 'workflow_run' not in on, 'the post-key check takes key=us and has no workflow_run trigger')
check(not any('schedule' in (yaml.safe_load(open(f)).get(True) or yaml.safe_load(open(f)).get('on') or {}) for f in [W / 'kpc-key-postcheck.yml']), 'no cron added to the post-key check')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
