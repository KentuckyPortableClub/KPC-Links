#!/usr/bin/env python3
"""Nov 10 2026 (quiet runs): fewer Actions runs and commits, fewer failure emails, no bot turned off. Offline.
Checks: every workflow file parses; NO new schedule entry versus main (a cron may only get LESS frequent, never a new one);
the pages deploy has concurrency + a stale-only red end; kpc-us-key.yml has no push / pull_request trigger; the guide PDF job
retries and can end green; the quiet-save gate (bookkeeping-only + saved recently = skip; material / alarm = save) works on a
real local git repo, and the copy inlined in kpc_push_data.sh / kpc_save_overwrite.sh equals kpc_quiet_gate.py; a stamp-only
save through kpc_push_data.sh commits nothing; fail-safe is narrowed for the retry / scoreboard / storage / measure jobs."""
import json, os, pathlib, re, subprocess, sys, tempfile, time
import yaml

HERE = pathlib.Path(__file__).resolve().parent.parent
WF = sorted((HERE / '.github/workflows').glob('*.yml'))
ok = True


def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)


def on_of(d):
    on = d.get(True, d.get('on')) or {}
    if isinstance(on, str): on = {on: None}
    if isinstance(on, list): on = {k: None for k in on}
    return on


def crons(d):
    return [x.get('cron') for x in (on_of(d).get('schedule') or [])]


def per_day(cron):
    """How many times a day a 5-field cron fires (minute x hour; day fields scale it: day-of-month / weekday lists are counted as a fraction)."""
    m, h, dom, mon, dow = cron.split()
    def n(field, size):
        out = 0
        for part in field.split(','):
            if part == '*': out += size
            elif part.startswith('*/'): out += len(range(0, size, int(part[2:])))
            elif '-' in part: a, b = part.split('-')[:2]; out += int(b) - int(a) + 1
            else: out += 1
        return out
    f = n(m, 60) * n(h, 24)
    if dom != '*': f *= n(dom, 31) / 30.4
    if dow != '*': f *= n(dow, 7) / 7
    if mon != '*': f *= n(mon, 12) / 12
    return f


def git(*a, cwd=HERE):
    return subprocess.run(['git', *a], capture_output=True, text=True, cwd=cwd)


# 1. every workflow parses
bad = []
docs = {}
for f in WF:
    try:
        d = yaml.safe_load(f.read_text(encoding='utf-8'))
        assert isinstance(d, dict) and d.get('jobs') and on_of(d), 'no jobs / triggers'
        docs[f.name] = d
    except Exception as e:  # noqa: BLE001
        bad.append(f'{f.name}: {e}')
check(not bad, f'all {len(WF)} workflow files parse and have triggers and jobs {bad[:3]}')

# 2. no new schedule versus main; a changed cron is never more frequent
base = os.environ.get('KPC_BASE_REF', 'origin/main')
if git('rev-parse', '--verify', '-q', base + '^{commit}').returncode != 0:
    print(f'NOTE no {base} in this checkout: the schedule comparison is skipped here (run it where main is fetched)')
else:
    new_files, more, grew = [], [], []
    for name, d in docs.items():
        r = git('show', f'{base}:.github/workflows/{name}')
        mine = crons(d)
        if r.returncode != 0:
            if mine: new_files.append(name)
            continue
        try: theirs = crons(yaml.safe_load(r.stdout) or {})
        except Exception: theirs = []  # noqa: BLE001
        if len(mine) > len(theirs): grew.append(f'{name}: {len(theirs)} -> {len(mine)} crons')
        if mine and not theirs: new_files.append(name)
        added = [c for c in mine if c not in theirs]
        if added and sum(per_day(c) for c in mine) > sum(per_day(c) for c in theirs) + 1e-9:
            more.append(f'{name}: {theirs} -> {mine}')
    check(not new_files and not grew, f'no new schedule entry versus {base} {new_files + grew}')
    check(not more, f'a changed cron fires no more often than before {more}')

# 3. pages deploy: concurrency, stale-only red
pd = docs['pages-deploy.yml']
check((pd.get('concurrency') or {}).get('group') == 'pages' and (pd.get('concurrency') or {}).get('cancel-in-progress') is False,
      'pages-deploy.yml: concurrency group pages, cancel-in-progress false')
steps = pd['jobs']['deploy']['steps']
dep = [s for s in steps if s.get('id') == 'deployment'][0]
settle = [s for s in steps if 'Settle' in (s.get('name') or '')]
check(dep.get('continue-on-error') is True and len(settle) == 1, 'pages deploy: a failed deploy is judged by the next step, not red on its own')
sr = settle[0]['run'] if settle else ''
check('in progress' in sr and 'newer than this run' in sr and 'is already live' in sr and 'exit 1' in sr and 'stale' in sr,
      'pages deploy: green when already live / in progress / newer, red only when the site would stay stale')
check('GITHUB_STEP_SUMMARY' in sr, 'pages deploy: says what it found in the job summary')
check(len(crons(pd)) == 1 and per_day(crons(pd)[0]) <= 12, 'pages-deploy timer: one cron, at most every 2 hours')
check('event=push' not in json.dumps(pd) and 'go=no' in json.dumps(pd), 'pages-deploy timer: still publishes bot saves (no push-day skip); nothing new = no build')

# 4. us-key never on a push
uk = on_of(docs['kpc-us-key.yml'])
check('push' not in uk and 'pull_request' not in uk and 'pull_request_target' not in uk, 'kpc-us-key.yml: no push / pull_request trigger (feature-branch pushes start nothing)')
check({'schedule', 'workflow_dispatch'} <= set(uk), 'kpc-us-key.yml: schedule + by hand kept')

# 5. guide PDFs: retry, summary, green when nothing changed
gp = docs['kpc-guide-pdf.yml']['jobs']['pdf']['steps']
inst = [s for s in gp if s.get('id') == 'printer'][0]
check('for i in 1 2 3' in inst['run'] and 'GITHUB_STEP_SUMMARY' in inst['run'] and inst.get('continue-on-error') is True, 'guide PDFs: the install is tried 3 times and the error goes to the job summary')
dec = [s for s in gp if 'may this run still end green' in (s.get('name') or '')][0]
check('exit 1' in dec['run'] and 'no PDF needs reprinting' in dec['run'], 'guide PDFs: green when no guide input changed, red when a PDF could ship out of date')
check(all("steps.printer.outcome == 'success'" in str(s.get('if')) for s in gp if s.get('name') in ('Print the guides', 'Keep only PDFs that changed', 'Save')), 'guide PDFs: printing and saving only run when the printer is there')

# 6. fail-safe narrowed
for n in ('kpc-key-measure.yml',):
    t = (HERE / '.github/workflows' / n).read_text()
    check("KPC_FAIL_SAFE: ${{ vars.KPC_HIDDEN_RED == 'all' && '1' || '0' }}" in t and "!= 'off'" not in t.split('KPC_FAIL_SAFE')[1].split('\n')[0], f'{n}: red on a caught error only when KPC_HIDDEN_RED=all')
t = (HERE / '.github/workflows/kpc-watchdog.yml').read_text()
check('this run still ends green' in t, 'kpc-watchdog.yml: a lost notes-save does not turn a watchdog run red')

# 7. the quiet-save gate on real local git repos
GATE = HERE / '.github/scripts/kpc_quiet_gate.py'
gate_src = GATE.read_text()
for sh in ('kpc_push_data.sh', 'kpc_save_overwrite.sh'):
    s = (HERE / '.github/scripts' / sh).read_text()
    m = re.search(r"python3 - <<'KPC_QUIET_PY'\n(.*?)KPC_QUIET_PY\n", s, re.S)
    check(bool(m) and m.group(1) == gate_src, f'{sh}: the inlined quiet gate equals kpc_quiet_gate.py')
    r = subprocess.run(['bash', '-n', str(HERE / '.github/scripts' / sh)], capture_output=True, text=True)
    check(r.returncode == 0, f'{sh}: bash syntax ok {r.stderr[:80]}')

ENV = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null', GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t', GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')


def sh(cmd, cwd, env=None):
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, env=dict(ENV, **(env or {})))


def board(result):
    return json.dumps({'bots': {'park truth checker': {'result': result, 'made': 'x'}}}, indent=1)


with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    origin = t / 'origin.git'; sh(f'git init -q --bare -b main {origin}', t)
    work = t / 'work'; sh(f'git clone -q file://{origin} {work}', t)
    (work / 'data/status/bots').mkdir(parents=True); (work / 'data/truth').mkdir(parents=True); (work / 'data/waiting').mkdir(parents=True)
    (work / 'data/status/board.json').write_text(board('green'))
    (work / 'data/status/bots/park-truth-checker.json').write_text(json.dumps({'last_run': '2026-11-10', 'run': 'https://github.com/x/y/actions/runs/1', 'areas': 'left: 5'}))
    (work / 'data/truth/state.json').write_text('{"done": ["US-IL"]}')
    (work / 'data/waiting/verdicts.json').write_text(json.dumps({'checked': '2026-11-10T01:00Z', 'results': [{'path': 'a.json', 'verdict': 'PASS', 'why': ['4 of 20 links dead']}]}))
    sh('git add -A && git commit -qm "start" && git push -q origin HEAD:main', work)
    PUSH = str(HERE / '.github/scripts/kpc_push_data.sh')

    def save(msg, env=None):
        before = sh('git rev-parse origin/main 2>/dev/null; git ls-remote origin main', work).stdout
        r = sh(f'bash {PUSH} . "{msg}" data', work, dict({'KPC_QUIET_HOURS': '3'}, **(env or {})))
        after = sh('git ls-remote origin main', work).stdout
        return r, before.split() [-2] if before.split() else '', after.split()[0] if after.split() else ''

    def old_head():
        return sh('git ls-remote origin main', work).stdout.split()[0]

    # a) stamp-only save through kpc_push_data.sh commits nothing (the run link and a same-day stamp moved)
    h0 = old_head()
    (work / 'data/status/bots/park-truth-checker.json').write_text(json.dumps({'last_run': '2026-11-10', 'run': 'https://github.com/x/y/actions/runs/2', 'areas': 'left: 5'}))
    r = sh(f'bash {PUSH} . "park truth checker: US-IL (done)" data', work)
    check(old_head() == h0 and 'stamp' in r.stdout + r.stderr or 'nothing' in r.stdout, 'a stamp-only save (new run link, same day) commits nothing')
    sh('git checkout -q -- . ', work)

    # b) a material save (truth data) goes through at once
    (work / 'data/truth/state.json').write_text('{"done": ["US-IL", "US-IN"]}')
    (work / 'data/status/bots/park-truth-checker.json').write_text(json.dumps({'last_run': '2026-11-10', 'run': 'x/actions/runs/3', 'areas': 'left: 4'}))
    sh(f'bash {PUSH} . "park truth checker: US-IN (done)" data', work, {'KPC_QUIET_HOURS': '3'})
    h1 = old_head()
    check(h1 != h0, 'a save with real data in it (data/truth) is committed at once')

    # c) the follow-up refresh, bookkeeping only (areas counter, same verdicts), within 3 h of that save -> not saved
    (work / 'data/status/bots/park-truth-checker.json').write_text(json.dumps({'last_run': '2026-11-10', 'run': 'x/actions/runs/4', 'areas': 'left: 3'}))
    (work / 'data/waiting/verdicts.json').write_text(json.dumps({'checked': '2026-11-10T01:30Z', 'results': [{'path': 'a.json', 'verdict': 'PASS', 'why': ['7 of 20 links dead']}]}))
    r = sh(f'bash {PUSH} . "park truth checker: US-IN (done)" data', work, {'KPC_QUIET_HOURS': '3'})
    check(old_head() == h1 and 'Quiet save' in r.stdout + r.stderr, f'bookkeeping only, same bot saved minutes ago: nothing committed {r.stdout[-160:]}{r.stderr[-160:]}')
    sh('git checkout -q -- . ', work)

    # d) same refresh from ANOTHER bot is not held back by this bot's save
    (work / 'data/status/bots/park-truth-checker.json').write_text(json.dumps({'last_run': '2026-11-10', 'run': 'x/actions/runs/5', 'areas': 'left: 2'}))
    sh(f'bash {PUSH} . "campground info bot: US-TX (done)" data', work, {'KPC_QUIET_HOURS': '3'})
    h2 = old_head()
    check(h2 != h1, "another bot's bookkeeping save is not held back by this bot's earlier save")

    # e) an alarm (a board line turning red) saves at once even for the same bot
    (work / 'data/status/board.json').write_text(board('red'))
    sh(f'bash {PUSH} . "campground info bot: US-TX (done)" data', work, {'KPC_QUIET_HOURS': '3'})
    check(old_head() != h2, 'a board line turning red is saved at once')

    # e2) a bot whose name is inside another bot's name ('board' vs 'campground info bot' / 'flow board') is not held back by it
    h_e = old_head()
    (work / 'data/status/bots/park-truth-checker.json').write_text(json.dumps({'last_run': '2026-11-10', 'run': 'x/actions/runs/9', 'areas': 'left: 7'}))
    sh(f'bash {PUSH} . "flow board" data', work, {'KPC_QUIET_HOURS': '3'})
    h_f = old_head()
    (work / 'data/status/bots/park-truth-checker.json').write_text(json.dumps({'last_run': '2026-11-10', 'run': 'x/actions/runs/10', 'areas': 'left: 8'}))
    sh(f'bash {PUSH} . "board: engine" data', work, {'KPC_QUIET_HOURS': '3'})
    check(h_f != h_e and old_head() != h_f, "'board: engine' is not held back by a 'flow board' save (the bot name must start the subject)")

    # g) Nov 13: last-<key>.json and the <key>-<build> report always save through
    # kpc_save_overwrite.sh (the postcheck call). A same-prefix bookkeeping save
    # within 3 hours must not skip them. Other key-check files stay bookkeeping.
    SAVE = str(HERE / '.github/scripts/kpc_save_overwrite.sh')
    kc = work / 'data/status/key-check'
    kc.mkdir(parents=True, exist_ok=True)
    (kc / 'pin-cover-us.json').write_text(json.dumps({'key': 'us', 'checked': '2026-11-13T01:00Z'}))
    r = sh(f"bash {SAVE} --copy 'Key check after the key build' - -- data/status/key-check", work, {'KPC_QUIET_HOURS': '3'})
    h_kc = old_head()
    check(h_kc != h2 and 'saved' in r.stdout + r.stderr,
          f"first key-check pin-cover save lands {r.stdout[-200:]}{r.stderr[-200:]}")

    (kc / 'pin-cover-us.json').write_text(json.dumps({'key': 'us', 'checked': '2026-11-13T01:10Z', 'n': 1}))
    r = sh(f"bash {SAVE} --copy 'Key check after the key build' - -- data/status/key-check", work, {'KPC_QUIET_HOURS': '3'})
    check(old_head() == h_kc and 'Quiet save' in r.stdout + r.stderr,
          f'key-check pin-cover only, same prefix within 3h: skipped {r.stdout[-200:]}{r.stderr[-200:]}')
    sh('git checkout -q -- .', work)

    (kc / 'last-us.json').write_text(json.dumps({'key': 'us', 'build': 'US-43293787778', 'report': 'us-US-43293787778.json', 'checked': '2026-11-13T04:00Z'}))
    (kc / 'us-US-43293787778.json').write_text(json.dumps({'key': 'us', 'build': 'US-43293787778', 'checked': '2026-11-13T04:00Z'}))
    (kc / 'us-US-43293787778.md').write_text('# US key check US-43293787778\n')
    r = sh(f"bash {SAVE} --copy 'Key check after the key build' - -- data/status/key-check", work, {'KPC_QUIET_HOURS': '3'})
    names = sh('git ls-tree -r --name-only origin/main data/status/key-check', work).stdout
    check(old_head() != h_kc and 'last-us.json' in names and 'us-US-43293787778.json' in names and 'us-US-43293787778.md' in names,
          f'last-us.json and the us-<build> report still save after a same-prefix 3h bookkeeping save {r.stdout[-200:]}{r.stderr[-200:]}')

    # f) KPC_QUIET_HOURS=0 switches the gate off
    h3 = old_head()
    (work / 'data/status/bots/park-truth-checker.json').write_text(json.dumps({'last_run': '2026-11-10', 'run': 'x/actions/runs/6', 'areas': 'left: 1'}))
    sh(f'bash {PUSH} . "campground info bot: US-TX (done)" data', work, {'KPC_QUIET_HOURS': '0'})
    check(old_head() != h3, 'KPC_QUIET_HOURS=0 = the old behaviour (every bookkeeping save lands)')

# 8. the lighter bots keep their stamp filter
for n in ('kpc-park-alerts.yml', 'kpc-discord-relay.yml'):
    check('kpc_save_filter.py' in (HERE / '.github/workflows' / n).read_text() and 'kpc_save_overwrite.sh' in (HERE / '.github/workflows' / n).read_text(), f'{n}: stamp filter + shared save kept')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
