#!/usr/bin/env python3
"""Offline test, Nov 4 PM fix bundle items 1-2 (Brandon's yes relayed via Super Head Bot, 4:53 PM CST Nov 4):
 1. a partial rebuild (the boundary check) keeps the committed rules hash; the boundary check starts from the newest main;
    the freeze / order checks can read the newest main's stamp (KPC_INDEX_REF).
 2. a chained (workflow_run) key start skips when a build on the same rules from the same inputs exists (also a failed one).
Replays the real Nov 4 stamps (US-41846994942 / US-41860712149 / US-41876470145, CA-41889018960, W-41895532587). No network."""
import importlib.util, json, os, pathlib, subprocess, sys, tempfile
import yaml

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
import kpc_key_freeze as KF
spec = importlib.util.spec_from_file_location('kpc_key_order', HERE / '.github/scripts/kpc_key_order.py'); KO = importlib.util.module_from_spec(spec); spec.loader.exec_module(KO)
ok = True
R = {k: KF.rules_hash(k) for k in KF.RULE_FILES}


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


def git(*a, cwd): return subprocess.run(['git', *a], cwd=cwd, capture_output=True, text=True)


def repo(t, files):
    git('init', '-q', cwd=t); git('config', 'user.email', 't@t', cwd=t); git('config', 'user.name', 't', cwd=t)
    for p, d in files.items():
        os.makedirs(os.path.dirname(os.path.join(t, p)), exist_ok=True); json.dump(d, open(os.path.join(t, p), 'w'))
    git('add', '-A', cwd=t); git('commit', '-qm', 'base', cwd=t)


# --- item 1: the stamp keeps the committed rules hash after a builder rewrote index.json without it
US_FULL = {'build': 'US-41846994942', 'built': '2026-11-04 15:44 UTC', 'rules': R['us-key'], 'rules_files': sorted(KF.RULE_FILES['us-key']) + [KF.VERSION_FILE], 'states': {'GA': {'parks': 1}}}
with tempfile.TemporaryDirectory() as t:
    repo(t, {'data/us-key/index.json': US_FULL})
    cwd = os.getcwd(); os.chdir(t)
    try:
        # what kpc_us_key.py's _with_old_stamp writes after a 3-state rebuild (the real 9:48 AM CST Nov 4 shape)
        json.dump({'previous_build': 'US-41846994942', 'previous_built': '2026-11-04 15:44 UTC', 'states': {'GA': {'parks': 2}}}, open('data/us-key/index.json', 'w'))
        for k in ('KPC_FULL_BUILD', 'KPC_BUILD_FAILED_FILE', 'KPC_INDEX_REF', 'GITHUB_ENV'): os.environ.pop(k, None)
        os.environ['GITHUB_RUN_ID'] = '41860712149'
        KF.stamp('us-key')
        d = json.load(open('data/us-key/index.json'))
        check(d.get('build') == 'US-41860712149' and d.get('rules') == R['us-key'], f"partial rebuild: new build id, the committed rules hash {R['us-key']} is KEPT (before: 'rules none' -> full US/CA/world rebuilds)")
        check(d.get('rules_of_run') == R['us-key'] and d.get('previous_build') == 'US-41846994942', 'rules_of_run and previous_build are written')
        env = pathlib.Path(t) / 'env'; env.write_text(''); os.environ['GITHUB_ENV'] = str(env)
        KF.gh_json = lambda p: None
        fz, bid, why = KF.check('us-key')
        check('RULES_CHANGED=1' not in env.read_text() and fz and bid == 'US-41860712149', 'the next nightly sees the current rules: FROZEN on the ungraded build, NO whole-key rebuild')
        # a partial build on NEW rules keeps the OLD hash: the next run still rebuilds the whole key (links-04 unchanged)
        old = dict(US_FULL, rules='0123456789ab'); json.dump(old, open('data/us-key/index.json', 'w')); git('commit', '-qam', 'old rules', cwd=t)
        json.dump({'previous_build': 'US-1', 'states': {}}, open('data/us-key/index.json', 'w')); KF.stamp('us-key')
        check(json.load(open('data/us-key/index.json')).get('rules') == '0123456789ab', 'a partial build on new rules keeps the old hash (states on old rules are never hidden)')
        # a full build still writes the current hash
        os.environ['KPC_FULL_BUILD'] = '1'; KF.stamp('us-key'); os.environ.pop('KPC_FULL_BUILD')
        check(json.load(open('data/us-key/index.json')).get('rules') == R['us-key'], 'a full build writes the current hash (unchanged)')
        # KPC_INDEX_REF: the freeze reads the committed (newest) copy, not a stale working file
        json.dump({'build': 'US-41695918852'}, open('data/us-key/index.json', 'w'))
        git('checkout', '-q', '-b', 'tmp', cwd=t)
        check(KF.load_index('us-key', ref='HEAD').get('rules') == '0123456789ab' and not KF.load_index('us-key', ref='').get('rules'), 'load_index: KPC_INDEX_REF reads the ref (newest main); unset = the checkout copy (as before)')
        check(KF.load_index('us-key', ref='nosuchref').get('build') == 'US-41695918852', 'load_index: an unreadable ref falls back to the checkout copy')
    finally:
        os.chdir(cwd); os.environ.pop('GITHUB_ENV', None); os.environ.pop('GITHUB_RUN_ID', None)

# --- item 1: wiring
W = HERE / '.github/workflows'
bc = yaml.safe_load(open(W / 'kpc-boundary-check.yml'))
names = [s.get('name', s.get('uses', '')) for s in bc['jobs']['check']['steps']]
i_sync = next((i for i, n in enumerate(names) if n.startswith('Start from the NEWEST main')), -1)
i_ov = next(i for i, n in enumerate(names) if n.startswith('Read the moved data'))
i_st = next(i for i, n in enumerate(names) if n.startswith('Stamp the rebuilt key'))
check(0 < i_sync < i_ov < i_st, 'boundary check: starts from the newest main right after checkout, before the overlay, the rebuild and the stamp')
check('git reset -q --hard FETCH_HEAD' in bc['jobs']['check']['steps'][i_sync]['run'], 'boundary check: the sync is a fetch + reset to the fetched main')
for f, n in (('kpc-us-key.yml', 1), ('kpc-ca-key.yml', 2), ('kpc-world-key.yml', 2), ('kpc-boundary-check.yml', 1)):
    y = yaml.safe_load(open(W / f)); c = sum(1 for j in y['jobs'].values() for s in j.get('steps', []) if (s.get('env') or {}).get('KPC_INDEX_REF') == 'origin/main')
    check(c == n, f'{f}: {n} decision step(s) read the newest main (KPC_INDEX_REF=origin/main)')

# --- item 2: duplicate chained starts
def order(kind, idx, event):
    with tempfile.TemporaryDirectory() as t:
        cwd = os.getcwd(); os.chdir(t)
        try:
            for k, st in idx.items():
                os.makedirs(f'data/{k}', exist_ok=True); json.dump(st, open(f'data/{k}/index.json', 'w'))
            env = pathlib.Path(t) / 'env'; env.write_text(''); os.environ['GITHUB_ENV'] = str(env)
            return KO.check(kind, {'GITHUB_EVENT_NAME': event}), env.read_text()
        finally: os.chdir(cwd); os.environ.pop('GITHUB_ENV', None)


US = {'build': 'US-41876470145', 'rules': R['us-key'], 'rules_of_run': R['us-key']}
CA = {'build': 'CA-41889018960', 'rules': R['ca-key'], 'rules_of_run': R['ca-key'], 'inputs': {'us-key': 'US-41876470145'}}
WD = {'build': 'W-41895532587', 'rules_of_run': R['world-key'], 'failed': ['AU'], 'complete': False, 'inputs': {'us-key': 'US-41876470145', 'ca-key': 'CA-41889018960'}}
res, env = order('world-key', {'us-key': US, 'ca-key': CA, 'world-key': WD}, 'workflow_run')
check(res == 'skip' and 'DUPLICATE=1' in env, 'world: the 2nd chained start after the duplicate Canada (41901828387 on Nov 4) skips: same rules, same US + CA inputs (even though AU failed)')
res, env = order('world-key', {'us-key': US, 'ca-key': dict(CA, build='CA-2'), 'world-key': WD}, 'workflow_run')
check(res == 'go' and 'DUPLICATE' not in env, 'world: a NEW Canada build is a new input: the chained start builds')
res, env = order('world-key', {'us-key': US, 'ca-key': CA, 'world-key': WD}, 'workflow_dispatch')
check(res == 'go' and 'DUPLICATE' not in env, 'world: a by-hand start is never a duplicate (it retries the failed part)')
res, env = order('ca-key', {'us-key': US, 'ca-key': CA}, 'workflow_run')
check(res == 'skip' and 'DUPLICATE=1' in env, 'Canada: the chained start after a duplicate (FROZEN) US run skips (Nov 4: 41891453412)')
res, env = order('ca-key', {'us-key': US, 'ca-key': dict(CA, rules_of_run='0123456789ab', rules='0123456789ab')}, 'workflow_run')
check(res == 'go', 'Canada: a build on OTHER rules is not a duplicate: the chained new-rules build goes on')
res, env = order('ca-key', {'us-key': US, 'ca-key': {'build': 'CA-41739774609'}}, 'workflow_run')
check(res == 'go' and 'DUPLICATE' not in env, 'Canada: an old stamp with no rules_of_run (all of main today) is never a duplicate')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
