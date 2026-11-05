#!/usr/bin/env python3
"""Offline test, key hotfix patch 1 (Nov 5; Brandon's approval relayed via Super Head Bot, 4:21 AM CST):
the boundary check never writes or stamps the US key index or its build id; only the US answer key workflow stamps.
Replays run 41995722306 (2:36 AM CST Nov 5: IA + ID rebuilt, the live index stamped US-41995722306). Fails on the old workflow
(its 'Stamp the rebuilt key' step) and on the old kpc_key_freeze.py (no stamper check). No network."""
import json, os, pathlib, subprocess, sys, tempfile
import yaml

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
import kpc_key_freeze as KF
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


def git(*a, cwd): return subprocess.run(['git', *a], cwd=cwd, capture_output=True, text=True)


wf = yaml.safe_load(open(HERE / '.github/workflows/kpc-boundary-check.yml', encoding='utf-8'))
steps = wf['jobs']['check']['steps']
names = [s.get('name', '') for s in steps]
runs = [str(s.get('run', '')) for s in steps]
check(not any('kpc_key_freeze.py stamp' in r for r in runs), 'no boundary-check step runs kpc_key_freeze.py stamp (the old step stamped US-41995722306)')
save = next(s for s in steps if s.get('name') == 'Save')
check('data/us-key/index.json' in save['run'].split('KPC_SAVE_SKIP="')[1].split('"')[0].split(), "the save never copies data/us-key/index.json back (KPC_SAVE_SKIP)")
ri = next((i for i, n in enumerate(names) if n.startswith('Never write or stamp the US key index')), None)
bi = next(i for i, n in enumerate(names) if n.startswith('Rebuild those keys'))
check(ri is not None and bi < ri < names.index('Save') and steps[ri].get('if') == 'always()', 'the index is put back after the rebuild and before the save, always')
check("env.RULES_CHANGED != '1'" in steps[bi]['if'], 'no partial rebuild here while the rules changed (the US key builds every state then)')

with tempfile.TemporaryDirectory() as t:
    # the live index as committed before 41995722306, then kpc_us_key.py's own write (IA + ID rebuilt) on top
    old = {'build': 'US-41984527710', 'built': '2026-11-05 07:13 UTC', 'rules': '6bb847b4f6cd', 'rules_of_run': '3dc53f70256a', 'states': {'IA': {'parks': 1}}}
    os.makedirs(f'{t}/data/us-key'); json.dump(old, open(f'{t}/data/us-key/index.json', 'w'))
    git('init', '-q', cwd=t); git('config', 'user.email', 't@t', cwd=t); git('config', 'user.name', 't', cwd=t); git('add', '-A', cwd=t); git('commit', '-qm', 'base', cwd=t)
    json.dump({'previous_build': 'US-41984527710', 'states': {'IA': {'parks': 2}}}, open(f'{t}/data/us-key/index.json', 'w'))
    subprocess.run(['bash', '-c', steps[ri]['run'] if ri is not None else 'true'], cwd=t, capture_output=True, text=True)
    check(json.load(open(f'{t}/data/us-key/index.json')) == old, 'the restore step puts the committed index back (build US-41984527710 kept)')
    # a stamp asked for from the boundary check is refused and writes nothing
    cwd = os.getcwd(); os.chdir(t)
    try:
        before = open('data/us-key/index.json', 'rb').read()
        os.environ['GITHUB_WORKFLOW_REF'] = 'KentuckyPortableClub/KPC-Links/.github/workflows/kpc-boundary-check.yml@refs/heads/main'
        os.environ['GITHUB_RUN_ID'] = '41995722306'
        try: KF.stamp('us-key')
        except Exception as e: print('stamp raised', type(e).__name__)  # the old stamp needs the rule files: it tried to write
        check(open('data/us-key/index.json', 'rb').read() == before, 'kpc_key_freeze.py stamp us-key from the boundary check is refused (no US-41995722306)')
    finally:
        os.chdir(cwd); os.environ.pop('GITHUB_WORKFLOW_REF', None); os.environ.pop('GITHUB_RUN_ID', None)
check(KF.may_stamp('us-key', 'KentuckyPortableClub/KPC-Links/.github/workflows/kpc-us-key.yml@refs/heads/main'), 'the US answer key workflow may stamp')
check(not KF.may_stamp('us-key', 'o/r/.github/workflows/kpc-boundary-check.yml@refs/heads/main'), 'the boundary check may not')
check(not KF.may_stamp('us-key', 'o/r/.github/workflows/kpc-world-key.yml@refs/heads/main'), "another key's workflow may not stamp the US key")
check(KF.may_stamp('us-key', ''), 'a local run (no GITHUB_WORKFLOW_REF) may stamp, as before')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
