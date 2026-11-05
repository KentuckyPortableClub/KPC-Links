#!/usr/bin/env python3
"""Next round C4 (Nov 5; item 7 next part, Brandon's yes relayed via Super): hidden failures in the KPC-Links workflows.
 * every '|| echo "::error/::warning ..."' site in a workflow with a G8 step also records the line (kpc-hidden.txt; errors also in
   kpc-hidden-errors.txt), with the real exit code;
 * the G8 step lists them, leaves one 'Hidden failures' line, and goes red on a caught ERROR only where it is safe (KPC_FAIL_SAFE=1:
   no workflow follows it, no job needs it, it starts no workflow, not a matrix that fails fast, not a reporter, not paused);
 * the check-up (kpc_bot_health.py) keeps them in data/status/hidden-failures.json (notes only: it emails nobody);
 * the '|| true' forms left are each marked '# ok: <why>' or now record the failure.
No network, no run. Run: python3 -B tests/test_nextround_hidden_failures_nov5.py"""
import os, pathlib, re, subprocess, sys, tempfile, importlib.util
import yaml
HERE = pathlib.Path(__file__).resolve().parent.parent
WF = HERE / '.github/workflows'
ok = True
def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)
G8 = 'Report hidden failures'
docs = {f.name: (f.read_text(), yaml.safe_load(f.read_text())) for f in sorted(WF.glob('*.yml'))}
listened = set()
for n, (t, d) in docs.items():
    on = d.get(True) or {}
    if isinstance(on, dict) and isinstance(on.get('workflow_run'), dict): listened |= set(on['workflow_run'].get('workflows') or [])
plain = re.compile(r'\|\| echo "::(error|warning) title=')
g8files = [n for n, (t, d) in docs.items() if G8 in t]
left = [n for n in g8files if plain.search(docs[n][0])]
check(not left, f'no bare "|| echo ::error/::warning" site left in the {len(g8files)} workflows with a G8 step ({left[:5]})')
n_rec = sum(t.count('>> "$RUNNER_TEMP/kpc-hidden.txt"') for n, (t, d) in docs.items())
n_err = sum(t.count('| tee -a "$RUNNER_TEMP/kpc-hidden-errors.txt" >> "$RUNNER_TEMP/kpc-hidden.txt"') for n, (t, d) in docs.items())
check(n_rec >= 113 and n_err >= 60, f'{n_rec} sites record the line ({n_err} of them errors, also in kpc-hidden-errors.txt)')
bad_rc = [n for n, (t, d) in docs.items() for m in re.finditer(r'\|\| \{ kpc_rc=\$\?; echo "::[^"]*"; echo "[^"]*"', t) if '$?' in m.group(0)[18:]]
check(not bad_rc, f'the recorded line carries the real exit code ($kpc_rc, not a later $?) ({bad_rc[:3]})')
# bash syntax of every run block + G8 behaviour
syn, beh, safe, notsafe = [], [], [], []
for n, (t, d) in docs.items():
    jobs = d.get('jobs') or {}
    needed = {x for j in jobs.values() for x in ([j.get('needs')] if isinstance(j.get('needs'), str) else (j.get('needs') or []))}
    for jn, j in jobs.items():
        for st in j.get('steps') or []:
            r = st.get('run')
            if not r: continue
            if subprocess.run(['bash', '-n'], input=re.sub(r'\$\{\{.*?\}\}', 'X', r), capture_output=True, text=True).returncode: syn.append(f'{n}:{jn}')
            if not (st.get('name') or '').startswith(G8): continue
            fs = 'KPC_FAIL_SAFE' in (st.get('env') or {})
            (safe if fs else notsafe).append(f'{n}:{jn}')
            if fs:
                stg = j.get('strategy') or {}
                why = [w for w, c in (('followed', (d.get('name') or n) in listened), ('needed', jn in needed), ('dispatches', bool(re.search(r'gh workflow run|/dispatches', t))),
                       ('matrix', bool(stg.get('matrix')) and stg.get('fail-fast', True) is not False), ('reporter', n in ('kpc-watchdog.yml', 'kpc-bot-health.yml')),
                       ('not last', not (j['steps'][-1].get('name') or '').startswith(G8))) if c]
                if why: beh.append(f'{n}:{jn} marked safe but {why}')
                check(st['env']['KPC_FAIL_SAFE'] == "${{ vars.KPC_HIDDEN_RED != 'off' && '1' || '0' }}", f'{n}:{jn}: KPC_FAIL_SAFE can be turned off by the repo variable KPC_HIDDEN_RED=off') if len(safe) == 1 else None
            py = r.split("<<'PY'\n", 1)[1].rsplit('PY', 1)[0]
            with tempfile.TemporaryDirectory() as tmp:
                for case in ('none', 'warn', 'err'):
                    for x in ('kpc-hidden.txt', 'kpc-hidden-errors.txt'):
                        if os.path.exists(os.path.join(tmp, x)): os.remove(os.path.join(tmp, x))
                    if case != 'none': open(os.path.join(tmp, 'kpc-hidden.txt'), 'w').write('t - m\n')
                    if case == 'err': open(os.path.join(tmp, 'kpc-hidden-errors.txt'), 'w').write('t - m\n')
                    e = dict(os.environ, RUNNER_TEMP=tmp, KPC_STEPS='{}', KPC_FAIL_SAFE='1' if fs else '', GITHUB_STEP_SUMMARY=os.path.join(tmp, 's'), GITHUB_JOB=jn)
                    p = subprocess.run([sys.executable, '-B', '-'], input=py, env=e, capture_output=True, text=True)
                    want = 1 if (case == 'err' and fs) else 0
                    line = ('::warning title=Hidden failures::' in p.stdout) == (case != 'none')
                    if p.returncode != want or not line: beh.append(f'{n}:{jn} {case}: exit {p.returncode} (want {want}), Hidden failures line {line}')
            # a person can turn it off
check(not syn, f'every run block is valid bash ({syn[:3]})')
check(not beh, f'every G8 step: red on a caught error only when safe, a Hidden failures line when anything was caught ({beh[:3]})')
check(len(safe) >= 20 and 'kpc-us-key.yml:join' in notsafe and 'kpc-world-key.yml:join' in notsafe and not any(s.startswith(('kpc-us-key', 'kpc-ca-key', 'kpc-world-key', 'kpc-watchdog', 'kpc-bot-health', 'kpc-chain')) for s in safe),
      f'{len(safe)} jobs safe to fail, {len(notsafe)} not (the keys, the chain, the watchdog and the check-up never go red from this)')
# || true forms
bare = [f'{n}:{i}' for n, (t, d) in docs.items() for i, l in enumerate(t.splitlines(), 1)
        if re.search(r'\|\| true\b', l) and not l.lstrip().startswith('#') and "no more '|| true'" not in l and "# ok" not in l and 'rebase --abort' not in l and "'|| true'" not in l]
check(not bare, f"every '|| true' left is marked '# ok: <why>' (or is a rebase --abort in a retry loop) ({bare[:5]})")
check("python3 - <<'PY' || { kpc_rc=$?; echo \"::warning title=Rebuild list::" in docs['kpc-us-key.yml'][0], "US key: the 'rebuild tonight' list step no longer hides a failure")
check('--restore data/status/watchdog.json || { kpc_rc=$?; echo "::warning title=Watchdog notes::' in docs['kpc-watchdog.yml'][0], 'watchdog: a failed restore of its notes is recorded')
# no cron changed, nothing un-paused
base = next((r for r in ('nr-links-main', 'origin/main', 'main') if subprocess.run(['git', 'rev-parse', '-q', '--verify', r], cwd=HERE, capture_output=True).returncode == 0), None)
if base:
    cr = lambda txt: sorted(re.findall(r"^\s*-\s*cron:\s*'([^']+)'", txt, re.M))
    moved = []
    for n, (t, d) in docs.items():
        p = subprocess.run(['git', 'show', f'{base}:.github/workflows/{n}'], cwd=HERE, capture_output=True, text=True)
        if p.returncode == 0 and cr(p.stdout) != cr(t): moved.append(n)
    check(not moved or base != 'nr-links-main', f'no cron line changed vs {base} ({moved[:3]})')
# the check-up
spec = importlib.util.spec_from_file_location('bh', HERE / '.github/scripts/kpc_bot_health.py'); BH = importlib.util.module_from_spec(spec); spec.loader.exec_module(BH)
ANN = {11: [{'title': 'Hidden failures', 'message': '2 error(s) and 1 warning(s) caught inside steps, 0 step(s) failed but kept green (job run)'}, {'title': 'x', 'message': 'y'}], 12: []}
def fake(path, *a):
    if path.endswith('/jobs?per_page=100'): return {'jobs': [{'id': 11}, {'id': 12}]}
    m = re.search(r'check-runs/(\d+)/annotations', path); return ANN.get(int(m.group(1))) if m else None
BH.gh = fake
h = BH.hidden_in('KentuckyPortableClub/KPC-Links', 'kpc-x.yml', {'id': 5})
check(h == [{'job': 'run', 'errors': 2, 'warnings': 1, 'kept_green_steps': 0}], f'the check-up reads the G8 line ({h})')
with tempfile.TemporaryDirectory() as tmp:
    cwd = os.getcwd(); os.chdir(tmp)
    try:
        BH.HIDDEN[:] = [dict(h[0], workflow='kpc-x.yml', run='u', created='c', conclusion='success')]; BH.write_hidden(3, 1)
        import json; j = json.load(open('data/status/hidden-failures.json'))
        check(j['runs_checked'] == 3 and j['runs_unread'] == 1 and j['with_hidden'][0]['errors'] == 2, 'data/status/hidden-failures.json: the runs read and each job with hidden errors')
    finally: os.chdir(cwd)
bt = docs['kpc-bot-health.yml'][1]
check((bt.get('permissions') or {}).get('checks') == 'read', "kpc-bot-health.yml: 'checks: read' (the annotations)")
check('git add data/status/hidden-failures.json' in docs['kpc-bot-health.yml'][0], 'kpc-bot-health.yml saves data/status/hidden-failures.json')
src = (HERE / '.github/scripts/kpc_bot_health.py').read_text()
check("notes.append({'chat': owner(x['workflow'])" in src and 'problems.append((tag + f.name, f"{x' not in src, 'hidden failures are notes in the check-up (never a new problem: no email)')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
