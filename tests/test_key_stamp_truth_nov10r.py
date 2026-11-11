#!/usr/bin/env python3
"""Offline test (owner rule, 2026-11-10): the build stamp names every planned-but-not-built area failed, each US state built green
carries its own rules stamp, a pending whole-key change rebuilds only the stale states, Canada / world accept the US key's
rules_of_run, and the freeze check / stamp fail closed. Temp dirs and fake index files only; no hash literals."""
import contextlib, importlib.util, io, json, os, pathlib, subprocess, sys, tempfile
import yaml

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
import kpc_key_freeze as KF
spec = importlib.util.spec_from_file_location('kpc_key_order', HERE / '.github/scripts/kpc_key_order.py'); KO = importlib.util.module_from_spec(spec); spec.loader.exec_module(KO)
FREEZE = str(HERE / '.github/scripts/kpc_key_freeze.py')
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


CUR = KF.rules_hash('us-key'); OLDH = 'f' * 12   # a hash that is never the current one
check(CUR != OLDH, 'the stand-in old hash differs from the current one')

# --- missing(): planned minus built, from groups json and part files
with tempfile.TemporaryDirectory() as t:
    p = pathlib.Path(t); (p / 'a').mkdir(); (p / 'a/states.txt').write_text('TN OH\n')
    groups = json.dumps([{'i': 0, 'states': 'TN OH'}, {'i': 1, 'states': 'WI IA'}])
    out = subprocess.run([sys.executable, FREEZE, 'missing', '--planned-groups', groups, '--built-file', str(p / 'a/states.txt'), str(p / 'b/states.txt')],
                         capture_output=True, text=True)
    check(out.returncode == 0 and out.stdout.split() == ['IA', 'WI'], f'a group whose part never came back is named failed ({out.stdout.split()})')
    out = subprocess.run([sys.executable, FREEZE, 'missing', '--planned-groups', json.dumps([{'i': 0, 'countries': 'AU DE'}]), '--built', 'AU'], capture_output=True, text=True)
    check(out.stdout.split() == ['DE'], 'world: a planned country not in done.txt is named failed')
    check(KF.missing({'A', 'B'}, {'A'}) == ['B'], 'missing() is planned minus built')

# --- mark-rows / take-rows: a row the builder does not rewrite = not built
with tempfile.TemporaryDirectory() as t:
    ip = pathlib.Path(t) / 'index.json'
    ip.write_text(json.dumps({'states': {'TN': {'parks': 5, 'check': 1}, 'OH': {'parks': 7, 'check': 0}}}))
    KF.mark_rows(str(ip), ['TN', 'OH', 'WI'])
    d = json.loads(ip.read_text()); d['states']['OH'] = {'parks': 8, 'check': 0}; ip.write_text(json.dumps(d))   # the builder rewrote OH only
    nb = KF.take_rows(str(ip), ['TN', 'OH', 'WI'])
    d = json.loads(ip.read_text())
    check(nb == ['TN', 'WI'], f'the states the builder never rewrote are not built ({nb})')
    check(KF.NOT_BUILT not in json.dumps(d) and 'WI' not in d['states'] and d['states']['TN'] == {'parks': 5, 'check': 1}, 'the marks are removed and no empty row is left')


def stamp_in(tmp, idx, env):
    cwd = os.getcwd(); os.chdir(tmp); old = dict(os.environ)
    try:
        os.makedirs('data/us-key', exist_ok=True); json.dump(idx, open('data/us-key/index.json', 'w'))
        for k in ('KPC_BUILD_FAILED_FILE', 'KPC_FULL_BUILD', 'KPC_PLANNED_AREAS', 'GITHUB_WORKFLOW_REF'): os.environ.pop(k, None)
        os.environ.update(env); os.environ['GITHUB_RUN_ID'] = '4242'
        with contextlib.redirect_stdout(io.StringIO()): KF.stamp('us-key')
        return json.load(open('data/us-key/index.json'))
    finally:
        os.chdir(cwd); os.environ.clear(); os.environ.update(old)


rows3 = {'TN': {'parks': 1}, 'OH': {'parks': 2}, 'WI': {'parks': 3}}
with tempfile.TemporaryDirectory() as t:
    open(pathlib.Path(t) / 'failed.txt', 'w').write('WI\n')
    d = stamp_in(t, {'rules': OLDH, 'states': json.loads(json.dumps(rows3))}, {'KPC_PLANNED_AREAS': 'TN OH WI', 'KPC_BUILD_FAILED_FILE': str(pathlib.Path(t) / 'failed.txt'), 'KPC_FULL_BUILD': '0'})
    check(d['states']['TN'].get('rules') == CUR and d['states']['OH'].get('rules') == CUR, 'each state built green carries the current rules')
    check('rules' not in d['states']['WI'], 'a failed state carries no new rules stamp')
    check(d.get('rules') == OLDH and d.get('failed') == ['WI'], 'the key-wide rules stay old while one state is short')
with tempfile.TemporaryDirectory() as t:
    rows = json.loads(json.dumps(rows3)); rows['TN']['rules'] = CUR; rows['OH']['rules'] = CUR
    d = stamp_in(t, {'rules': OLDH, 'states': rows}, {'KPC_PLANNED_AREAS': 'WI', 'KPC_FULL_BUILD': '0'})
    check(d.get('rules') == CUR, 'once every state row is on the current rules, the key-wide rules are stamped (no full rebuild needed)')
with tempfile.TemporaryDirectory() as t:
    d = stamp_in(t, {'rules': OLDH, 'states': json.loads(json.dumps(rows3))}, {'KPC_PLANNED_AREAS': 'TN', 'KPC_FULL_BUILD': '1'})
    check(d.get('rules') == CUR and all(r.get('rules') == CUR for r in d['states'].values()), 'a full green build stamps the key and every row')

# --- check(): only the stale states are rebuilt when some rows are already current
check(KF.stale_areas('us-key', {'states': {'TN': {'rules': CUR}, 'OH': {}}}, CUR) == ['US-OH'], 'stale_areas: the rows not on the current rules')
check(KF.stale_areas('us-key', {'states': {'TN': {}, 'OH': {}}}, CUR) == [], 'no row current yet (first run after this change) = the whole key')
check(KF.stale_areas('us-key', {'states': {'TN': {'rules': CUR}}}, CUR) == [], 'every row current = nothing narrowed')
with tempfile.TemporaryDirectory() as t:
    cwd = os.getcwd(); os.chdir(t); old = dict(os.environ)
    try:
        os.makedirs('data/us-key'); json.dump({'build': 'US-1', 'rules': OLDH, 'states': {'TN': {'rules': CUR}, 'OH': {}, 'WI': {'rules': OLDH}}}, open('data/us-key/index.json', 'w'))
        envf = pathlib.Path(t) / 'env'; envf.write_text(''); os.environ['GITHUB_ENV'] = str(envf); os.environ['FORCE'] = 'yes'; os.environ.pop('KPC_INDEX_REF', None)
        with contextlib.redirect_stdout(io.StringIO()): KF.check('us-key')
        e = dict(l.split('=', 1) for l in envf.read_text().split('\n') if '=' in l)
        check(e.get('RULES_CHANGED') == '1' and e.get('RULES_SCOPE', '').split() == ['US-OH', 'US-WI'], f"a pending whole-key change rebuilds only the stale states ({e.get('RULES_SCOPE')})")
    finally:
        os.chdir(cwd); os.environ.clear(); os.environ.update(old)

# --- the plan turns that scope into just those states, and 'full' so the stamp can finish the key
wf = yaml.safe_load(open(HERE / '.github/workflows/kpc-us-key.yml'))
plan_py = next(s['run'] for s in wf['jobs']['plan']['steps'] if s.get('id') == 'p').split("<<'PY' >> \"$GITHUB_OUTPUT\"\n", 1)[1].rsplit('PY', 1)[0]
with tempfile.TemporaryDirectory() as t:
    os.makedirs(f'{t}/data/us-key'); json.dump({'states': {}}, open(f'{t}/data/us-key/index.json', 'w'))
    env = dict(os.environ, RULES_CHANGED='1', RULES_SCOPE='US-OH US-WI', SCHED='46 11 * * *', STATES='', NJOBS='3')
    out = subprocess.run([sys.executable, '-c', plan_py], cwd=t, env=env, capture_output=True, text=True).stdout
    o = dict(l.split('=', 1) for l in out.splitlines() if '=' in l)
    sts = sorted(x for g in json.loads(o.get('groups', '[]')) for x in g['states'].split())
    check(sts == ['OH', 'WI'] and o.get('full') == '1', f'the backup start builds only the stale states, not every state ({sts}, full={o.get("full")})')

# --- order: Canada / world accept the US key's rules_of_run (one short state no longer blocks them)
with tempfile.TemporaryDirectory() as t:
    os.makedirs(f'{t}/data/us-key'); json.dump({'build': 'US-2', 'rules': OLDH, 'rules_of_run': CUR}, open(f'{t}/data/us-key/index.json', 'w'))
    old = os.environ.pop('KPC_INDEX_REF', None); cwd = os.getcwd(); os.chdir(t)
    try: done, _ = KO.upstream_done('us-key')
    finally:
        os.chdir(cwd)
        if old is not None: os.environ['KPC_INDEX_REF'] = old
    check(done, 'a US build on the current rules with a failed state counts as finished for the keys after it')

# --- fail closed: a check error = FROZEN + exit 1; a stamp error = exit 1
with tempfile.TemporaryDirectory() as t:
    envf = pathlib.Path(t) / 'env'; envf.write_text('')
    r = subprocess.run([sys.executable, FREEZE, 'check', 'no-such-key'], cwd=t, env=dict(os.environ, GITHUB_ENV=str(envf)), capture_output=True, text=True)
    check(r.returncode != 0 and 'FROZEN=1' in envf.read_text(), 'a freeze check that stops with an error reports FROZEN and exits non-zero')
    r = subprocess.run([sys.executable, FREEZE, 'stamp', 'no-such-key'], cwd=t, env=dict(os.environ, GITHUB_ENV=str(envf)), capture_output=True, text=True)
    check(r.returncode != 0, 'a stamp that stops with an error exits non-zero')

# --- workflows: the part reaches the join from a red group; the join and the world name never-built areas failed
us = yaml.safe_load(open(HERE / '.github/workflows/kpc-us-key.yml'))
up = [s for s in us['jobs']['build']['steps'] if 'upload-artifact' in str(s.get('uses', ''))]
check(up and all('always()' in str(s.get('if', '')) for s in up), 'kpc-us-key.yml: the build part is uploaded with always()')
st = next(s for s in us['jobs']['join']['steps'] if 'stamp us-key' in str(s.get('run', '')))
check('missing --planned-groups' in st['run'] and 'KPC_PLANNED_AREAS' in st['run'], 'kpc-us-key.yml stamp: planned minus the parts\' states is named failed; the planned list goes to the stamp')
b = next(s for s in us['jobs']['build']['steps'] if 'kpc_us_key.py 2>&1' in str(s.get('run', '')))
check('mark-rows' in b['run'] and 'take-rows' in b['run'] and 'not-built-states' in b['run'], 'kpc-us-key.yml build: a planned state the builder did not write is named failed')
w = yaml.safe_load(open(HERE / '.github/workflows/kpc-world-key.yml'))
part = next(s for s in w['jobs']['build']['steps'] if s.get('name') == "This job's part")['run']
check('done.txt' in part and '[ -f data/world-key/$c.json ] || echo' not in part, 'kpc-world-key.yml: built = done.txt this run, not the old checkout file')
j = next(s for s in w['jobs']['join']['steps'] if s.get('id') == 'tonight')['run']
check('missing --planned-groups' in j and 'done.txt' in j, 'kpc-world-key.yml join: a planned country with no part / not done is named failed')
fs = next(s for s in w['jobs']['join']['steps'] if 'stamp world-key' in str(s.get('run', '')))
check("needs.build.result == 'success'" in fs['env']['KPC_FULL_BUILD'], 'kpc-world-key.yml: the full-build flag needs a green build')
check({'kpc_net_guard.py', 'kpc_preflight.py'} <= KF.NOT_RULES, 'the new network / preflight helpers are listed as not rule files')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
