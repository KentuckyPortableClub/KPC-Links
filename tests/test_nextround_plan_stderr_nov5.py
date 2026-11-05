"""Next round C2 (Nov 5; Brandon's yes relayed via Super): every message of the US and world plan steps goes to the run log (stderr);
stdout (>> $GITHUB_OUTPUT) holds only key=value step outputs. Runs the plan heredocs themselves in a temp folder.
Run: python3 -B tests/test_nextround_plan_stderr_nov5.py"""
import json, os, pathlib, re, shutil, subprocess, sys, tempfile, textwrap
R = pathlib.Path(__file__).resolve().parents[1]
ok = True
def check(what, got, want):
    global ok
    good = got == want; ok &= good
    print(('PASS ' if good else 'FAIL ') + f'{what}: got {got!r}' + ('' if good else f', want {want!r}'))
def heredocs(wf):
    t = open(R / '.github/workflows' / wf).read()
    return [textwrap.dedent(m.group(1)) for m in re.finditer(r"python3 - <<'PY' >> \"\$GITHUB_OUTPUT\"\n(.*?)\n\s*PY\n", t, re.S)]
def run(code, env, cwd):
    p = subprocess.run([sys.executable, '-B', '-c', code], cwd=cwd, env=dict({k: v for k, v in os.environ.items() if k not in ('FROZEN', 'RULES_CHANGED', 'STATES', 'SCHED')}, **env), capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr
def only_outputs(out): return all(re.fullmatch(r'[a-z_]+=.*', l) for l in out.splitlines() if l.strip())
us = heredocs('kpc-us-key.yml'); check('the US plan has one heredoc into $GITHUB_OUTPUT', len(us), 1)
td = tempfile.mkdtemp(prefix='nrc2_')
try:
    os.makedirs(f'{td}/data/us-key')
    import datetime as dt
    now = dt.datetime.now(dt.timezone.utc)
    built = now.strftime('%Y-%m-%d %H:%M UTC') if now.hour * 60 + now.minute >= 9 * 60 + 17 else ''
    json.dump({'built': built, 'states': {'TN': {'seconds': 120}, 'OH': {'seconds': 60}}}, open(f'{td}/data/us-key/index.json', 'w'))
    open(f'{td}/data/us-key/answers-states.txt', 'w').write('TN OH\n')
    cases = [('FROZEN', {'FROZEN': '1', 'FROZEN_BUILD': 'US-1'}, 'FROZEN'),
             ('no new answers', {'STATES': ''}, None),
             ('a states input', {'STATES': 'TN OH'}, 'jobs'),
             ('rules changed', {'RULES_CHANGED': '1', 'STATES': 'TN'}, 'RULES CHANGED')]
    for name, env, word in cases:
        if name == 'no new answers': open(f'{td}/data/us-key/answers-states.txt', 'w').write('')
        rc, out, err = run(us[0], env, td)
        check(f'US plan, {name}: exit 0, stdout only key=value outputs', (rc, only_outputs(out)), (0, True))
        check(f'US plan, {name}: the message is in the run log (stderr)', '::notice' in err or '::warning' in err, True)
        check(f'US plan, {name}: no ::notice/::warning in $GITHUB_OUTPUT', '::' in out, False)
        if word: check(f'US plan, {name}: the message says {word!r}', word in err, True)
        if name == 'no new answers': open(f'{td}/data/us-key/answers-states.txt', 'w').write('TN OH\n')
    if built:
        rc, out, err = run(us[0], {'SCHED': '46 11 * * *', 'STATES': ''}, td)
        check('US plan, already built today: groups=[] on stdout, the notice on stderr', ('groups=[]' in out, 'already finished today' in err, '::' in out), (True, True, False))
    else: print('SKIP already-built-today case (before 09:17 UTC now)')
    w = heredocs('kpc-world-key.yml'); check('the world plan has one heredoc into $GITHUB_OUTPUT', len(w), 1)
    os.makedirs(f'{td}/data/world-key'); json.dump({'countries': {}}, open(f'{td}/data/world-key/index.json', 'w'))
    rc, out, err = run(w[0], {'ALL': 'AU DE GB', 'SLOW': 'AU', 'SLOW_MIN': '300'}, td)
    check('world plan: stdout only key=value outputs, the job split in the run log', (rc, only_outputs(out), 'World key plan' in err), (0, True, True))
finally:
    shutil.rmtree(td, ignore_errors=True)
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
