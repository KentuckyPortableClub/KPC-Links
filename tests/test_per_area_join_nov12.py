#!/usr/bin/env python3
"""Nov 12 (KPC owner, 2026-11-12): each country / state stands alone in a key join (handoff part A). World run 43200398601 went red on
five short saved copies (BE CH CZ DE PT) and #153's all-or-nothing join saved NOTHING, so the French layers never landed; run 43222090832
(countries=BE CH CZ DE PT, every one held) was the second case. Checked here, offline (temp folders, no network):
  W1 workflow (parsed YAML + a small evaluator of GitHub `if:` rules): a cancelled run saves nothing (no join, no Save, no stamp, no
     world-bounds push, no post-key check); a cancel mid-join saves nothing; a RED shard no longer blocks the join: the green countries are
     saved and the verdict job ends the run red; the post-key check still runs for the saved countries; every writer needs !cancelled()
     and "May we save the green set?"; the verdict job writes nothing.
  W2 one or five short countries: the others save; the short ones byte-identical to main (key, review page, tracts, index row, every
     shared review row); the summary lists them red with what to do next; no expected-hold entry needed.
  W3 every requested country held (run 43222090832): nothing saved, nothing rewritten, summary lists all five, run red.
  W4 a6c493c replayed on the real tree of its parent: NONE of its 1,357 deleted lines is deleted.
  W5 AU / MT expected holds: still left out, kept from main, not red; W6 two parts writing one country: exit 1, nothing written.
  W7 honest stamps: only saved countries carry the new code hash; the key-wide hash and the kept rows do not move; a kept country is
     planned again (RULES_SCOPE); an old failure of a country not asked stays failed; KPC_FULL_BUILD only when everything saved.
  U1-U4 US: a failed / short state keeps main's bytes and is listed red; the drop guard keeps the state from main and the rest save;
     review rows merged per state; the US join `if` / Save conditions.  C1 Canada: a stopped build keeps every province, not stamped.
Run: python3 -B tests/test_per_area_join_nov12.py"""
import collections, contextlib, io, json, os, pathlib, re, shutil, subprocess, sys, tempfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / '.github/scripts'
sys.path.insert(0, str(SCRIPTS))
import kpc_world_key_join as J  # noqa: E402
import kpc_area_join as AJ  # noqa: E402
ok = True


def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name, flush=True)
    ok = ok and bool(cond)




def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name, flush=True)
    ok = ok and bool(cond)


# ------------------------------------------------------------------ a small evaluator of GitHub `if:` expressions
TOK = re.compile(r"\s*(?:(\$\{\{)|(\}\})|('(?:[^']|'')*')|(&&|\|\||==|!=|!|\(|\)|,)|([A-Za-z_][\w.\-*]*))")


def tokens(s):
    out, i = [], 0
    s = s.strip()
    while i < len(s):
        m = TOK.match(s, i)
        if not m: raise ValueError(f'cannot read {s[i:i + 30]!r}')
        i = m.end()
        if m.group(1) or m.group(2): continue
        if m.group(3) is not None: out.append(('str', m.group(3)[1:-1].replace("''", "'")))
        elif m.group(4): out.append(('op', m.group(4)))
        elif m.group(5): out.append(('id', m.group(5)))
    return out


STATUS = ('always', 'success', 'failure', 'cancelled')


def has_status(expr): return any(t == ('id', f) for t in tokens(expr) for f in STATUS)


def evaluate(expr, ctx, fn):
    """ctx: dotted name -> value ('' when unknown); fn: status function name -> bool."""
    if isinstance(expr, bool): return expr
    t = tokens(str(expr)); pos = [0]
    def peek(): return t[pos[0]] if pos[0] < len(t) else (None, None)
    def take(): pos[0] += 1; return t[pos[0] - 1]
    def prim():
        k, v = take()
        if (k, v) == ('op', '!'): return not truthy(prim())
        if (k, v) == ('op', '('):
            r = orx(); take(); return r
        if k == 'str': return v
        if peek() == ('op', '('):
            take(); args = []
            while peek() != ('op', ')'):
                args.append(orx())
                if peek() == ('op', ','): take()
            take()
            if v in STATUS: return fn[v]
            if v == 'hashFiles': return ''
            raise ValueError(v)
        if v in ('true', 'false'): return v == 'true'
        return ctx.get(v, '')
    def cmp():
        a = prim()
        while peek() in (('op', '=='), ('op', '!=')):
            op = take()[1]; b = prim()
            a = (str(a) == str(b)) if op == '==' else (str(a) != str(b))
        return a
    def andx():
        a = cmp()
        while peek() == ('op', '&&'): take(); b = cmp(); a = truthy(a) and truthy(b)
        return a
    def orx():
        a = andx()
        while peek() == ('op', '||'): take(); b = andx(); a = truthy(a) or truthy(b)
        return a
    return truthy(orx())


def truthy(v): return v not in ('', False, None, 0, '0') if not isinstance(v, bool) else v


def job_runs(job, needs_results, needs_outputs, run_cancelled, ctx0=None):
    ctx = dict(ctx0 or {})
    for n, r in needs_results.items(): ctx[f'needs.{n}.result'] = r
    for n, o in needs_outputs.items():
        for k, v in o.items(): ctx[f'needs.{n}.outputs.{k}'] = v
    e = job.get('if', 'success()'); e = e if has_status(str(e)) else f'success() && ({e})'
    allok = all(r in ('success', 'skipped') for r in needs_results.values())
    return evaluate(e, ctx, {'always': True, 'cancelled': run_cancelled, 'success': allok and not run_cancelled,
                             'failure': any(r == 'failure' for r in needs_results.values())}), ctx


def walk(job, ctx, outcome=None, outputs=None, cancel_after=None, run_cancelled=False):
    """Run the job's steps through their `if:`. outcome: step id or name -> 'failure' (default success). Returns ({step: ran?}, result).
    A cancel BEFORE the job started does not reach its steps (a6c493c is the proof: the old join, started by always() on the cancelled
    run 43148551915, ran its steps and saved); a cancel DURING the job (cancel_after) makes success() false and cancelled() true."""
    outcome, outputs = outcome or {}, outputs or {}
    ran, failed, cancelled = {}, False, False
    for s in job['steps']:
        key = s.get('id') or s.get('name') or s.get('uses')
        e = s.get('if', 'success()'); e = e if has_status(str(e)) else f'success() && ({e})'
        go = evaluate(e, ctx, {'always': True, 'cancelled': cancelled, 'success': not failed and not cancelled, 'failure': failed})
        ran[key] = go
        if s.get('id'):
            ctx[f"steps.{s['id']}.outcome"] = ('failure' if outcome.get(key) == 'failure' else 'success') if go else 'skipped'
            for k, v in (outputs.get(key) or {}).items():
                if go: ctx[f"steps.{s['id']}.outputs.{k}"] = v
        if go and outcome.get(key) == 'failure' and not s.get('continue-on-error'): failed = True
        if cancel_after and key == cancel_after: cancelled = True
    return ran, ('cancelled' if cancelled else 'failure' if failed else 'success')



# ------------------------------------------------------------------ W1: the workflow
W = yaml.safe_load((ROOT / '.github/workflows/kpc-world-key.yml').read_text(encoding='utf-8'))
JOIN, POST, VER = W['jobs']['join'], W['jobs']['postcheck'], W['jobs']['verdict']
js = JOIN['steps']
WRITERS = ('kept_green_joincheck', 'keep_rows', 'stamp', 'save', 'kept_green_1')
GROUPS = json.dumps([{'i': 0, 'countries': 'DE FR', 'cmin': ''}])


def scenario(build, run_cancelled=False, cancel_after=None, outcome=None, built='3', red='', plan_out=None):
    po = {'groups': GROUPS, 'full': '1', 'expected': ''}; po.update(plan_out or {})
    go, ctx = job_runs(JOIN, {'plan': 'success', 'build': build}, {'plan': po}, run_cancelled, {'inputs.outline_test': ''})
    if not go: ran, res = {}, 'skipped'
    else: ran, res = walk(JOIN, ctx, outcome, {'tonight': {'built': built, 'red': red}}, cancel_after, run_cancelled)
    ran2 = {(s.get('id') or s.get('name')): ran.get(s.get('id') or s.get('name') or s.get('uses'), False) for s in js}
    jo = {'built': built if go else '', 'red': red if go else ''}
    pgo, _ = job_runs(POST, {'plan': 'success', 'join': res}, {'join': jo}, run_cancelled or res == 'cancelled')
    vgo, vctx = job_runs(VER, {'plan': 'success', 'build': build, 'join': res}, {'join': jo, 'plan': po}, run_cancelled or res == 'cancelled')
    return {'join': go, 'ran': ran2, 'res': res, 'post': pgo, 'verdict': vgo, 'vctx': vctx}


def nothing_written(r): return not any(r['ran'].get(k) for k in WRITERS) and not r['post']


def verdict_red(r):
    """Run the verdict job's one bash step with its env (the needs values) and say whether it exits 1."""
    st = VER['steps'][0]
    env = dict(os.environ)
    for k, v in st['env'].items():
        m = re.fullmatch(r'\$\{\{\s*(.*?)\s*\}\}', v); env[k] = str(r['vctx'].get(m.group(1), '')) if m else v
    return subprocess.run(['bash', '-c', st['run']], env=env, capture_output=True, text=True).returncode == 1


r = scenario('success')
check('W1 all green: join, join check, review rows, stamp, Save, world-bounds, post-key check run; verdict green',
      r['join'] and all(r['ran'].get(k) for k in WRITERS) and r['post'] and r['verdict'] and not verdict_red(r))
for b, rc in (('failure', True), ('cancelled', True), ('success', True)):
    check(f'W1 a CANCELLED run (build {b}): no join, nothing written, no post-key check (the #153 rule stays)', nothing_written(scenario(b, run_cancelled=rc)) and not scenario(b, run_cancelled=rc)['join'])
for at in ('tonight', 'join_verdict', 'kept_green_joincheck', 'keep_rows', 'stamp', 'kept_check'):
    rr = scenario('success', cancel_after=at)
    check(f'W1 a cancel mid-join (after step {at}): no Save, no world-bounds push, no post-key check', not rr['ran']['save'] and not rr['ran']['kept_green_1'] and not rr['post'])
rr = scenario('failure', red='BE CH CZ DE PT')
check('W1 a RED shard (five short countries, the run not cancelled): the join runs and SAVES the green set', rr['join'] and rr['ran']['save'] and rr['ran']['stamp'] and rr['ran']['kept_green_1'])
check('W1 ... the post-key check still runs for the saved countries', rr['post'])
check('W1 ... and the verdict job, after the save, ends the run red', rr['verdict'] and verdict_red(rr))
rr = scenario('success', red='BE')
check('W1 every shard green but one country not saved (a missing part): saved, run red', rr['ran']['save'] and verdict_red(rr))
rr = scenario('failure', built='0', red='BE CH CZ DE PT')
check('W1 every planned country held (built=0): no join check, stamp, Save or world-bounds push; no post-key check; run red',
      not any(rr['ran'].get(k) for k in WRITERS) and not rr['post'] and verdict_red(rr))
rr = scenario('success', outcome={'join_verdict': 'failure'})
check('W1 "May we save the green set?" red: nothing written', nothing_written(rr))
rr = scenario('success', outcome={'tonight': 'failure'}, built='0')
check('W1 the join refused (conflict, exit 1, built=0): nothing written, run red', nothing_written(rr) and verdict_red(rr))
for st in ('keep_rows', 'stamp', 'kept_check'):
    rr = scenario('success', outcome={st: 'failure'})
    check(f'W1 {st} failed: no Save, no world-bounds push', not rr['ran']['save'] and not rr['ran']['kept_green_1'])
idx = {(s.get('id') or s.get('name')): i for i, s in enumerate(js)}
check('W1 "May we save the green set?" runs before every writing step; the summary after Save', all(idx['join_verdict'] < idx[k] for k in WRITERS)
      and idx[next(k for k in idx if str(k).startswith('Run summary'))] > idx['save'])
check('W1 every writing step needs !cancelled() and the passed "May we save the green set?"',
      all('!cancelled()' in str(js[idx[k]].get('if')) and "steps.join_verdict.outcome == 'success'" in str(js[idx[k]].get('if')) for k in WRITERS))
check("W1 no writer, no join job and no Save needs needs.build.result == 'success' any more", "needs.build.result == 'success'" not in JOIN['if']
      and not any("needs.build.result == 'success'" in str(js[idx[k]].get('if')) for k in WRITERS))
check('W1 the join job: !cancelled(), not skipped, has groups, no always()', '!cancelled()' in JOIN['if'] and "needs.build.result != 'skipped'" in JOIN['if']
      and "needs.plan.outputs.groups != '[]'" in JOIN['if'] and 'always()' not in JOIN['if'])
check('W1 the verdict job writes nothing and never runs on a cancel', '!cancelled()' in VER['if'] and not re.search(r'git (push|commit|add)|kpc_save|stamp world-key|gh workflow', VER['steps'][0]['run'])
      and not VER.get('permissions'))
check('W1 the plan job still decides expected holds from the APPROVED file (AU / MT)',
      'kpc_world_key_join.py expected --file data/outlines/world-expected-holds.approved.json' in next(s for s in W['jobs']['plan']['steps'] if s.get('id') == 'p')['run'])
check('W1 the signed baselines gate stays (--approved data/outlines/world-baselines.approved.json)',
      '--approved data/outlines/world-baselines.approved.json' in next(s for s in W['jobs']['build']['steps'] if s.get('id') == 'kept_green_master')['run'])
check('W1 no new trigger, no cron change', sorted(W[True]) == ['schedule', 'workflow_dispatch'] and [c['cron'] for c in W[True]['schedule']] == ['17 11 3 * *', '7 10 * * *'])
pl = next(s for s in W['jobs']['plan']['steps'] if s.get('name', '').startswith("Tonight's list"))['run']
check('W1 plan: a rules catch-up builds only the countries not yet on the current code hash (RULES_SCOPE), else every country', 'SCOPE_LIST' in pl and 'RULES_SCOPE' in pl)


# ------------------------------------------------------------------ fixtures
def git(t, *a): return subprocess.run(['git', *a], cwd=t, capture_output=True, text=True)


def snapshot(t, sub='data'):
    return {str(p.relative_to(t)): p.read_bytes() for p in sorted((t / sub).rglob('*')) if p.is_file()}


def mkrepo(t, countries, extra_index=None):
    import csv
    wk = t / 'data/world-key'; (wk / 'review').mkdir(parents=True); (wk / 'tracts').mkdir(); (t / 'data/world-bounds').mkdir(parents=True)
    for c in countries:
        (wk / f'{c}.json').write_text(json.dumps({'parks': {f'{c}-0001': {'n': f'{c} park', 'm': [[1, 'x', 'L']], 'g': 'official', 'bk': [1, 0.2]},
                                                            f'{c}-0002': {'n': f'{c} far', 'g': 'pin', 'm': [], 'c': [[2, 'y', 'L', 'held: far']]}}}, separators=(',', ':')))
        (wk / 'tracts' / f'{c}.json').write_text('{"about":"t","area":"%s"}' % c); (wk / 'review' / f'{c}.md').write_text(f'review {c} main\n')
    idx = {'countries': {c: {'parks': 2, 'old': True} for c in countries}, 'build': 'W-1', 'built': '2026-11-11 00:00 UTC', 'rules': '487a51327b86'}
    idx.update(extra_index or {})
    (wk / 'index.json').write_text(json.dumps(idx, indent=1))
    held = [{'park': f'{c}-0002', 'area': c, 'name': f'{c} far – é', 'pin_km': 30.0, 'reason': 'far, "q"'} for c in countries]
    rows = [{'park': f'{c}-0001', 'area': c, 'name': f'{c}, park', 'pin_km': 16.0, 'suspect': 'far'} for c in countries]
    (wk / 'review/held-joins.json').write_text(json.dumps({'key': 'world', 'count': len(held), 'parks': held}, indent=1, ensure_ascii=False))
    (wk / 'review/join-check.json').write_text(json.dumps({'key': 'world', 'suspect': len(rows), 'held': len(held), 'rows': rows}, indent=1, ensure_ascii=False))
    for name, cols, data in (('held-joins.csv', list(held[0]), held), ('join-check.csv', list(rows[0]), rows),
                             ('held-joins-ledger.csv', ['park', 'kind', 'proposal'], [{'park': h['park'], 'kind': 'pile-enter', 'proposal': 'p\nmulti'} for h in held])):
        with open(wk / 'review' / name, 'w', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(data)
    git(t, 'init', '-q'); git(t, 'add', '-A'); git(t, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'main')


def mkpart(t, i, countries, done=None, rc='0', short='', held=()):
    d = t / 'parts' / f'world-key-part-{i}'; (d / 'world-key' / 'review').mkdir(parents=True, exist_ok=True); (d / 'world-bounds').mkdir(exist_ok=True)
    done = list(countries if done is None else done)
    if short: done = [c for c in done]   # a gate-held country may still be built (the old AU shard) or not
    (d / 'countries.txt').write_text(' '.join(countries) + '\n'); (d / 'failed.txt').write_text(''.join(c + '\n' for c in countries if c not in done))
    (d / 'done.txt').write_text(''.join(c + '\n' for c in done)); (d / 'held.txt').write_text(''.join(c + '\n' for c in held))
    idx = {}
    for c in done:
        (d / 'world-key' / f'{c}.json').write_text(json.dumps({'parks': {f'{c}-0001': {'n': f'{c} park', 'm': [[1, 'x', 'L'], [3, 'z', 'L']], 'g': 'official', 'bk': [1, 0.1]}}}))
        (d / 'world-key' / 'review' / f'{c}.md').write_text(f'review {c} new')
        (d / 'world-bounds' / c).mkdir(); (d / 'world-bounds' / c / 'a.json').write_text('{}')
        idx[c] = {'parks': 1, 'new': i}
    (d / 'world-key' / 'index.json').write_text(json.dumps({'countries': idx}))
    (t / f'rc{i}').write_text(rc + '\n'); (t / f'short{i}').write_text(short)
    with contextlib.redirect_stdout(io.StringIO()):
        J.main_verdict(['verdict', '--part', str(d), '--countries', ' '.join(countries), '--rc-file', str(t / f'rc{i}'), '--short-file', str(t / f'short{i}')])
    return d


def run_join(t, parts, groups, expected=''):
    import kpc_save
    buf = io.StringIO(); cwd = os.getcwd(); os.chdir(t)
    out = t / 'gh-out'; out.write_text('')
    old = os.environ.get('GITHUB_OUTPUT'); os.environ['GITHUB_OUTPUT'] = str(out)
    try:
        with contextlib.redirect_stdout(buf):
            rc = J.main([*map(str, parts), '--gate', '--held-out', str(t / 'held.txt'), '--out', str(t / 'data/world-key'), '--bounds', str(t / 'data/world-bounds'),
                         '--failed-out', str(t / 'failed.txt'), '--planned-groups', groups, '--expected', expected, '--record', str(t / 'rec.json')])
        kpc_save.flush_status()
    finally:
        os.chdir(cwd)
        if old is None: os.environ.pop('GITHUB_OUTPUT', None)
        else: os.environ['GITHUB_OUTPUT'] = old
    return rc, buf.getvalue(), dict(x.split('=', 1) for x in out.read_text().splitlines() if '=' in x)


def after_join(t, expected=''):
    """The join job's later steps on the fixture: the join check, the per-country review merge, the stamp (asked = planned)."""
    import kpc_join_check as JC, kpc_key_freeze as KF, kpc_save
    cwd = os.getcwd(); os.chdir(t); env0 = dict(os.environ)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            JC.run({'KEY': 'world', 'ANSWER_SHEET': str(t / 'none')}, root=str(t), plain=True)
            J.main_keep_rows(['keep-rows', '--countries', expected, '--unchanged', str(t / 'data/world-key'), '--review', str(t / 'data/world-key/review')])
            rec = json.load(open(t / 'rec.json'))
            os.environ.update({'KPC_BUILD_FAILED_FILE': str(t / 'failed.txt'), 'KPC_HELD_EXPECTED': expected, 'GITHUB_RUN_ID': '77', 'KPC_FULL_BUILD': os.environ.get('T_FULL', '0'),
                               'KPC_PLANNED_AREAS': ' '.join(rec['joined']), 'KPC_ASKED_AREAS': ' '.join(rec.get('planned') or [])})
            os.environ.pop('GITHUB_WORKFLOW_REF', None)
            KF.stamp('world-key')
            kpc_save.flush_status()
    finally:
        os.chdir(cwd); os.environ.clear(); os.environ.update(env0)


def rows_of(text, cc, name):
    if name.endswith('.json'):
        d = json.loads(text)
        return [json.dumps(r, sort_keys=True) for r in d.get('parks', d.get('rows', [])) if AJ.row_area(r, name) == cc]
    return [raw for raw, r in AJ.csv_records(text)[1] if AJ.row_area(r, name) == cc]


SHORT5 = ['BE', 'CH', 'CZ', 'DE', 'PT']
ALL = ['AT', 'BE', 'CH', 'CZ', 'DE', 'FR', 'NL', 'PT']
CUR = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'kpc_key_freeze.py'), 'rules', 'world-key'], cwd=ROOT, capture_output=True, text=True).stdout.strip()

# ------------------------------------------------------------------ W2: five short countries (the real case of run 43200398601)
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); mkrepo(t, ALL + ['AU', 'MT']); before = snapshot(t)
    groups = json.dumps([{'i': 0, 'countries': 'DE FR NL', 'cmin': ''}, {'i': 1, 'countries': 'BE CH CZ AT PT', 'cmin': ''}])
    p0 = mkpart(t, 0, ['DE', 'FR', 'NL'], rc='7', short='W-DE\n')            # DE short in a shard with FR (French layers) and NL
    p1 = mkpart(t, 1, ['BE', 'CH', 'CZ', 'AT', 'PT'], rc='7', short='W-BE\nW-CH\nW-CZ\nW-PT\n')
    rc, log, out = run_join(t, [p0, p1], groups, expected='AU MT')
    rec = json.load(open(t / 'rec.json'))
    check('W2 five short countries: the join exits 0 and saves FR NL AT (French layers land)', rc == 0 and rec['joined'] == ['AT', 'FR', 'NL'] and out.get('built') == '3')
    check('W2 the five are red / kept from main, AU MT are expected holds and not red', rec['red'] == SHORT5 and all(rec['areas'][c]['code'] == 'held-gate' for c in SHORT5)
          and all(rec['areas'][c]['code'] == 'held-expected' and rec['areas'][c]['action'] == 'kept' for c in ('AU', 'MT')) and out.get('red') == ' '.join(SHORT5))
    check('W2 no expected-hold entry needed for the keep-old (the five are not on any list)', 'BE' not in (json.loads((ROOT / 'data/outlines/world-expected-holds.approved.json').read_text()).get('holds') or {}))
    r = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'kpc_world_key_join.py'), 'check-saved', '--record', str(t / 'rec.json'), '--key-dir', str(t / 'data/world-key')], capture_output=True, text=True)
    check('W2 "May we save the green set?" passes', r.returncode == 0 and 'saving 3 countries' in r.stdout)
    after_join(t, 'AU MT'); aft = snapshot(t)
    for c in SHORT5 + ['AU', 'MT']:
        same = all(aft.get(f'data/world-key/{x}') == before.get(f'data/world-key/{x}') for x in (f'{c}.json', f'review/{c}.md', f'tracts/{c}.json'))
        check(f'W2 {c}: key, review page and tracts byte-identical to main', same)
    idx, oidx = json.loads(aft['data/world-key/index.json']), json.loads(before['data/world-key/index.json'])
    check('W2 index rows of the kept countries are main\'s; FR NL AT carry the new rows', all(idx['countries'][c] == oidx['countries'][c] for c in SHORT5 + ['AU', 'MT'])
          and all(idx['countries'][c] != oidx['countries'][c] for c in ('FR', 'NL', 'AT')))
    lost = []
    for name in AJ.REVIEW_FILES:
        mt, nt = before[f'data/world-key/review/{name}'].decode(), aft[f'data/world-key/review/{name}'].decode()
        for c in ALL + ['AU', 'MT']:
            if c in ('FR', 'NL', 'AT'): continue
            if rows_of(mt, c, name) != rows_of(nt, c, name): lost.append((name, c))
    check('W2 NO shared review row of any country not saved is lost or changed (5 files x 7 countries)', not lost)
    check('W2 the world-bounds of the five were not touched; FR NL AT were', not any((t / 'data/world-bounds' / c).exists() for c in SHORT5) and all((t / 'data/world-bounds' / c).is_dir() for c in ('FR', 'NL', 'AT')))
    bad = AJ.assert_kept(rec, t / 'data/world-key')
    check('W2 the kept-from-main check before Save passes after the join check, the review merge and the stamp', bad == [])
    # W7 honest stamps on this partial save
    check(f'W7 saved countries carry the current code hash {CUR}; the kept ones do not', all(idx['countries'][c].get('rules') == CUR for c in ('FR', 'NL', 'AT'))
          and not any('rules' in idx['countries'][c] for c in SHORT5 + ['AU', 'MT']))
    check('W7 the key-wide hash did not move (no claim that the world is on the new hash), complete false', idx.get('rules') == '487a51327b86' and idx.get('complete') is False
          and idx.get('rules_of_run') == CUR)
    check('W7 the five are named failed; AU MT are held_expected, not failed', idx.get('failed') == SHORT5 and idx.get('held_expected') == ['AU', 'MT'])
    import kpc_key_freeze as KF
    check('W7 the next plan builds the kept countries again (stale rows: RULES_SCOPE)', sorted(KF.stale_areas('world-key', idx, CUR)) == sorted(f'W-{c}' for c in SHORT5 + ['AU', 'MT']))
    sm = t / 'sum.md'
    AJ.write_summary('World key join', AJ.summary_rows(rec, idx, oidx), dest=str(sm))
    txt = sm.read_text()
    check('W2 ONE summary table: area | built? | verdict | saved or kept from main | hash stamped | why', txt.count('| area | built? | verdict | saved or kept from main | hash stamped | why |') == 1)
    check('W2 summary: FR saved with the new hash; each short country kept from main with held-gate and what to do next',
          f'| FR | yes | green | saved | {CUR} (new) |' in txt and all(re.search(rf'\| {c} \| yes \| held \| kept from main \| kept: none recorded .*held-gate: .*kpc-world-cache.yml, countries={c}\), then rerun the world key for {c}', txt) for c in SHORT5))

# W3: every requested country held (run 43222090832: countries=BE CH CZ DE PT)
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); mkrepo(t, ALL); before = snapshot(t)
    groups = json.dumps([{'i': 0, 'countries': 'BE CH CZ', 'cmin': ''}, {'i': 1, 'countries': 'DE PT', 'cmin': ''}])
    p0 = mkpart(t, 0, ['BE', 'CH', 'CZ'], rc='7', short='W-BE\nW-CH\nW-CZ\n'); p1 = mkpart(t, 1, ['DE', 'PT'], rc='7', short='W-DE\nW-PT\n')
    rc, log, out = run_join(t, [p0, p1], groups)
    rec = json.load(open(t / 'rec.json'))
    check('W3 every requested country held: exit 0, built=0 (nothing to save), all five red', rc == 0 and out.get('built') == '0' and rec['red'] == SHORT5 and rec['joined'] == [])
    check('W3 nothing rewritten: not one file under data/ changed (keys, index, review files, tracts)', snapshot(t) == before)
    sm = t / 'sum.md'; AJ.write_summary('World key join', AJ.summary_rows(rec, json.loads(before['data/world-key/index.json']), json.loads(before['data/world-key/index.json'])), dest=str(sm))
    check('W3 the summary lists all five, kept from main, with the refresh hint', all(re.search(rf'\| {c} \| .* \| kept from main \| .*kpc-world-cache.yml', sm.read_text()) for c in SHORT5))
    rr = scenario('failure', built='0', red=' '.join(SHORT5))
    check('W3 workflow: no join check / review merge / stamp / Save / world-bounds on built=0; the run ends red', not any(rr['ran'].get(k) for k in WRITERS) and verdict_red(rr))

# W2b: a country that failed in its build (exit 3 / time limit) in a green shard, and a lost part
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); mkrepo(t, ALL); before = snapshot(t)
    groups = json.dumps([{'i': 0, 'countries': 'DE FR', 'cmin': ''}, {'i': 1, 'countries': 'AT', 'cmin': ''}])
    rc, log, out = run_join(t, [mkpart(t, 0, ['DE', 'FR'], done=['FR'], held=['DE'])], groups)
    rec = json.load(open(t / 'rec.json'))
    check('W2b DE failed in its build (exit 3) and AT\'s part is missing: FR saved, DE failed, AT not-built, both kept',
          rc == 0 and rec['joined'] == ['FR'] and rec['areas']['DE']['code'] == 'failed' and rec['areas']['AT']['code'] == 'not-built'
          and snapshot(t)['data/world-key/DE.json'] == before['data/world-key/DE.json'] and snapshot(t)['data/world-key/AT.json'] == before['data/world-key/AT.json'])

# W6: two parts writing one country = fail closed
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); mkrepo(t, ALL); before = snapshot(t)
    groups = json.dumps([{'i': 0, 'countries': 'DE FR', 'cmin': ''}, {'i': 1, 'countries': 'FR', 'cmin': ''}])
    rc, log, out = run_join(t, [mkpart(t, 0, ['DE', 'FR']), mkpart(t, 1, ['FR'])], groups)
    check('W6 two parts own FR: exit 1, built=0, nothing written, the record says join-refused', rc == 1 and out.get('built') == '0' and snapshot(t) == before
          and json.load(open(t / 'rec.json'))['red'] == ['join-refused'])
    shutil.rmtree(t / 'parts')
    rc, log, out = run_join(t, [mkpart(t, 0, ['DE', 'FR', 'NL'])], json.dumps([{'i': 0, 'countries': 'DE FR', 'cmin': ''}]))
    check('W6 a part carrying a country the plan did not give it: exit 1, nothing written', rc == 1 and snapshot(t) == before)

# W7b: a full build where every planned country saved stamps the key-wide hash; an old failure not asked stays failed
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); mkrepo(t, ['FR', 'NL', 'GR'], {'failed': ['GR', 'NL'], 'complete': False})
    rc, log, out = run_join(t, [mkpart(t, 0, ['FR', 'NL'])], json.dumps([{'i': 0, 'countries': 'FR NL', 'cmin': ''}]))
    os.environ['T_FULL'] = '1'; after_join(t); os.environ.pop('T_FULL')
    idx = json.loads((t / 'data/world-key/index.json').read_text())
    check('W7 GR failed on main and not asked: still failed; NL saved: off the list; no key-wide stamp while a failure stands',
          idx.get('failed') == ['GR'] and idx.get('rules') == '487a51327b86' and idx['countries']['NL'].get('rules') == CUR and 'rules' not in idx['countries']['GR'])
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); mkrepo(t, ['FR', 'NL'])
    rc, log, out = run_join(t, [mkpart(t, 0, ['FR', 'NL'])], json.dumps([{'i': 0, 'countries': 'FR NL', 'cmin': ''}]))
    os.environ['T_FULL'] = '1'; after_join(t); os.environ.pop('T_FULL')
    idx = json.loads((t / 'data/world-key/index.json').read_text())
    check('W7 a full build where every planned country saved: the key-wide hash moves, every row carries it, complete', idx.get('rules') == CUR and 'failed' not in idx
          and all(r.get('rules') == CUR for r in idx['countries'].values()))

# ------------------------------------------------------------------ W4: replay a6c493c (the Nov 11 wipe) on the real tree of its parent
have = git(ROOT, 'cat-file', '-t', 'a6c493c').stdout.strip() == 'commit'
if not have:
    print('INFO a6c493c is not in this clone (shallow): the replay is skipped')
else:
    with tempfile.TemporaryDirectory() as td:
        t = pathlib.Path(td)
        tar = subprocess.run(['git', 'archive', 'a6c493c^', 'data/world-key'], cwd=ROOT, capture_output=True).stdout
        subprocess.run(['tar', '-x', '-C', str(t)], input=tar, check=True)
        (t / 'data/world-bounds').mkdir(parents=True, exist_ok=True)
        git(t, 'init', '-q'); git(t, 'add', '-A'); git(t, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'a6c493c^')
        allc = sorted(json.loads((t / 'data/world-key/index.json').read_text())['countries'])
        rest = [c for c in allc if c not in ('NO', 'SE', 'AU')]
        groups = json.dumps([{'i': 0, 'countries': ' '.join(rest[::2]), 'cmin': ''}, {'i': 1, 'countries': ' '.join(rest[1::2]), 'cmin': ''},
                             {'i': 2, 'countries': 'NO SE', 'cmin': ''}, {'i': 3, 'countries': 'AU', 'cmin': '300'}])
        d = t / 'parts/world-key-part-2'; (d / 'world-key/review').mkdir(parents=True); (d / 'world-key/tracts').mkdir(); (d / 'world-bounds').mkdir()
        for c in ('NO', 'SE'):
            (d / f'world-key/{c}.json').write_bytes(git(ROOT, 'show', f'a6c493c:data/world-key/{c}.json').stdout.encode())
            (d / f'world-key/tracts/{c}.json').write_bytes(subprocess.run(['git', 'show', f'a6c493c:data/world-key/tracts/{c}.json'], cwd=ROOT, capture_output=True).stdout)
            rv = subprocess.run(['git', 'show', f'a6c493c:data/world-key/review/{c}.md'], cwd=ROOT, capture_output=True)
            if rv.returncode == 0: (d / f'world-key/review/{c}.md').write_bytes(rv.stdout)
        ai = json.loads(git(ROOT, 'show', 'a6c493c:data/world-key/index.json').stdout)
        (d / 'world-key/index.json').write_text(json.dumps({'countries': {c: ai['countries'][c] for c in ('NO', 'SE')}}))
        (d / 'countries.txt').write_text('NO SE\n'); (d / 'done.txt').write_text('NO\nSE\n'); (d / 'failed.txt').write_text('')
        (t / 'rc').write_text('0\n'); (t / 'sh').write_text('')
        with contextlib.redirect_stdout(io.StringIO()):
            J.main_verdict(['verdict', '--part', str(d), '--countries', 'NO SE', '--rc-file', str(t / 'rc'), '--short-file', str(t / 'sh')])
        rc, log, out = run_join(t, [d], groups)
        rec = json.load(open(t / 'rec.json'))
        check(f'W4 replay: the a6c493c shape (4 groups, 1 part) now saves NO SE and keeps the other {len(allc) - 2} countries from main', rc == 0 and rec['joined'] == ['NO', 'SE']
              and len(rec['red']) == len(allc) - 2)
        after_join(t)
        diff = subprocess.run(['git', 'diff', '-U0', 'a6c493c^', 'a6c493c', '--', 'data/world-key/review', 'data/world-key/index.json'], cwd=ROOT, capture_output=True, text=True).stdout
        dels, cur, n = collections.defaultdict(collections.Counter), None, 0
        for ln in diff.splitlines():
            if ln.startswith('--- a/'): cur = ln[6:]
            elif ln.startswith('-') and not ln.startswith('---') and cur: dels[cur][ln[1:]] += 1; n += 1
        missing = {}
        for f, cnt in dels.items():
            if f.endswith('index.json'): continue   # the index is re-stamped (build id, failed list) by design; its country rows are checked below
            if f.endswith('join-check.json'):   # this run's own counters (files_checked, joined_parks, held, files_changed) describe this run's check
                cnt = collections.Counter({k: v for k, v in cnt.items() if not re.fullmatch(r' "(files_checked|joined_parks|held|files_changed)": \d+,', k)})
            have_l = collections.Counter((t / f).read_text(encoding='utf-8').splitlines()) if (t / f).exists() else collections.Counter()
            lost = cnt - have_l
            if lost: missing[f] = sum(lost.values())
        nrev = sum(sum(c.values()) for f, c in dels.items() if not f.endswith('index.json'))
        print('INFO the run counters of join-check.json (files_checked, joined_parks, held, files_changed) are this run\'s by design; every ROW is checked')
        check(f'W4 replay oracle: none of the {nrev} review-file lines a6c493c deleted is deleted now (all 5 review files)', nrev > 1000 and not missing)
        if missing: print('INFO lost lines per file:', missing)
        oidx = json.loads(git(ROOT, 'show', 'a6c493c^:data/world-key/index.json').stdout); nidx = json.loads((t / 'data/world-key/index.json').read_text())
        check('W4 replay: every country row of the index except NO SE is main\'s', all(nidx['countries'].get(c) == oidx['countries'].get(c) for c in allc if c not in ('NO', 'SE')))
        hj = json.loads((t / 'data/world-key/review/held-joins.json').read_text())
        check('W4 replay: held-joins.json still holds its 66 held joins (a6c493c left 0)', hj['count'] == len(hj['parks']) == 66)
        check('W4 replay: the old failed list of countries not asked stays; the key-wide hash does not move', nidx.get('rules') == oidx.get('rules'))

# ------------------------------------------------------------------ US
import kpc_us_key_join as UJ  # noqa: E402
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); k = t / 'data/us-key'; (k / 'tracts').mkdir(parents=True)
    for st in ('AL', 'TN', 'GA'):
        (k / f'US-{st}.json').write_text(json.dumps({'parks': {f'US-{st}{i}': {'g': 'official'} for i in range(3)}, 'counts': {}}, separators=(',', ':')))
        (k / 'tracts' / f'US-{st}.json').write_text('{"t":"main"}')
    (k / 'index.json').write_text(json.dumps({'states': {s: {'seconds': 60, 'rules': 'old000000000'} for s in ('AL', 'TN', 'GA')}, 'rules': 'old000000000', 'build': 'US-1'}, indent=1))
    (k / 'layers.json').write_text('{}')
    git(t, 'init', '-q'); git(t, 'add', '-A'); git(t, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'main'); before = snapshot(t)
    pd = t / 'parts/us-key-part-0'; (pd / 'tracts').mkdir(parents=True)
    for st in ('AL', 'TN'):
        (pd / f'US-{st}.json').write_text(json.dumps({'parks': {f'US-{st}1': {'g': 'official', 'new': 1}}, 'counts': {}}))
        (pd / 'tracts' / f'US-{st}.json').write_text('{"t":"new"}')
    (pd / 'index.json').write_text(json.dumps({'states': {'AL': {'seconds': 9}, 'TN': {'seconds': 8}}})); (pd / 'layers.json').write_text('{}')
    (pd / 'states.txt').write_text('AL TN\n'); (pd / 'failed-states.txt').write_text('AL\n')
    pg = t / 'parts/us-key-part-1'; pg.mkdir(); (pg / 'master-short.txt').write_text('US-GA\n')   # GA held by the gate: no states.txt
    cwd = os.getcwd(); os.chdir(t)
    try:
        with contextlib.redirect_stdout(io.StringIO()): rc = UJ.main([str(pd), str(pg), '--out', str(k)])
        import kpc_save; kpc_save.flush_status()
    finally: os.chdir(cwd)
    aft = snapshot(t); ni = json.loads(aft['data/us-key/index.json'])
    check('U1 US join: AL (named failed by its part) is NOT joined: key and tracts byte-identical to main, index row main\'s',
          rc == 0 and aft['data/us-key/US-AL.json'] == before['data/us-key/US-AL.json'] and aft['data/us-key/tracts/US-AL.json'] == before['data/us-key/tracts/US-AL.json']
          and ni['states']['AL'] == {'seconds': 60, 'rules': 'old000000000'})
    check('U1 US join: TN joined; GA (short, no part states) untouched', aft['data/us-key/US-TN.json'] != before['data/us-key/US-TN.json'] and aft['data/us-key/US-GA.json'] == before['data/us-key/US-GA.json'])
    import kpc_key_freeze as KF
    (t / 'failed.txt').write_text('AL\nGA\n')
    cwd = os.getcwd(); os.chdir(t); env0 = dict(os.environ)
    try:
        os.environ.update({'KPC_BUILD_FAILED_FILE': str(t / 'failed.txt'), 'KPC_PLANNED_AREAS': 'AL GA TN', 'KPC_FULL_BUILD': '0', 'GITHUB_RUN_ID': '5'}); os.environ.pop('GITHUB_WORKFLOW_REF', None)
        with contextlib.redirect_stdout(io.StringIO()): KF.stamp('us-key'); kpc_save.flush_status()
    finally: os.chdir(cwd); os.environ.clear(); os.environ.update(env0)
    ni = json.loads((k / 'index.json').read_text()); cur_us = KF.rules_hash('us-key')
    check('U2 US stamp is honest (confirmed, unchanged code): TN carries the current hash, AL GA keep their old one, the key-wide hash stays',
          ni['states']['TN'].get('rules') == cur_us and ni['states']['AL']['rules'] == 'old000000000' and ni['states']['GA']['rules'] == 'old000000000'
          and ni['rules'] == 'old000000000' and ni['failed'] == ['AL', 'GA'])
    groups = json.dumps([{'i': 0, 'states': 'AL TN'}, {'i': 1, 'states': 'GA'}])
    rec = UJ.record([pd, pg], groups, str(t / 'failed.txt'))
    check('U3 US record: TN saved; AL failed; GA held-gate; all red except TN', rec['red'] == ['AL', 'GA'] and rec['areas']['GA']['code'] == 'held-gate' and rec['areas']['AL']['code'] == 'failed'
          and rec['areas']['TN']['action'] == 'saved')
    # the drop guard keeps a dropped state from main and lets the rest through
    (k / 'US-TN.json').write_text(json.dumps({'parks': {}, 'counts': {}}))   # TN lost its 3 official parks
    r = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'kpc_key_drop_guard.py'), '--repo', str(t), '--ref', 'HEAD', '--mark', str(t / 'bad'), '--restore', '--failed-out', str(t / 'drop.txt')],
                       capture_output=True, text=True, cwd=t)
    check('U4 drop guard --restore: exit 0, TN put back to main byte for byte (key, tracts, index row), TN listed, no "nothing saved" mark',
          r.returncode == 0 and (k / 'US-TN.json').read_bytes() == before['data/us-key/US-TN.json'] and (k / 'tracts/US-TN.json').read_bytes() == before['data/us-key/tracts/US-TN.json']
          and json.loads((k / 'index.json').read_text())['states']['TN'] == {'seconds': 60, 'rules': 'old000000000'} and (t / 'drop.txt').read_text() == 'TN\n' and not (t / 'bad').exists())
    (k / 'US-TN.json').write_text(json.dumps({'parks': {}, 'counts': {}}))
    r = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'kpc_key_drop_guard.py'), '--repo', str(t), '--ref', 'HEAD', '--mark', str(t / 'bad')], capture_output=True, text=True, cwd=t)
    check('U4 drop guard without --restore: the old rule (exit 1, mark)', r.returncode == 1 and (t / 'bad').exists())
US = yaml.safe_load((ROOT / '.github/workflows/kpc-us-key.yml').read_text(encoding='utf-8'))
uj = US['jobs']['join']; us = uj['steps']; uidx = {(s.get('id') or s.get('name', '')[:20]): i for i, s in enumerate(us)}
dg = next(i for i, s in enumerate(us) if s.get('name', '').startswith('Drop guard')); stp = next(i for i, s in enumerate(us) if s.get('id') == 'us_stamp')
sv = next(i for i, s in enumerate(us) if s.get('name') == 'Save'); rv = next(i for i, s in enumerate(us) if s.get('name', '').startswith('Review files'))
jc = next(i for i, s in enumerate(us) if s.get('name', '').startswith('Join check'))
check('U5 US join job: !cancelled(), not skipped; a shard that ended cancelled on its own no longer stops the join', uj['if'] == "${{ !cancelled() && needs.build.result != 'skipped' }}")
check('U5 US: join check -> review rows per state -> drop guard (--restore) -> stamp -> Save; Save needs a green stamp',
      jc < rv < dg < stp < sv and '--restore' in us[dg]['run'] and "steps.us_stamp.outcome == 'success'" in us[sv]['if'] and '!cancelled()' in us[sv]['if']
      and '/tmp/kpc-drop-failed.txt' in us[stp]['run'] and 'exit 1; }' in us[stp]['run'])
check('U5 US: the run summary comes after Save and goes red on a kept state', any(s.get('name', '').startswith('Run summary') and i > sv and 'kpc_area_join.py summary' in s['run'] for i, s in enumerate(us)))
go, ctx = job_runs(uj, {'plan': 'success', 'build': 'failure'}, {'plan': {}}, True)
check('U5 US: a cancelled run starts no join', not go)
go, ctx = job_runs(uj, {'plan': 'success', 'build': 'cancelled'}, {'plan': {}}, False)
check('U5 US: a red / timed-out shard with the run not cancelled: the join runs (per state)', go)
ran, _ = walk(uj, ctx, {'us_stamp': 'failure'})
check('U5 US: a failed stamp = no Save', not ran.get('Save'))
ran, _ = walk(uj, dict(ctx), {}, cancel_after='us_stamp')
check('U5 US: a cancel mid-join (after the stamp) = no Save', not ran.get('Save'))

# ------------------------------------------------------------------ Canada
CA = yaml.safe_load((ROOT / '.github/workflows/kpc-ca-key.yml').read_text(encoding='utf-8'))
cs = CA['jobs']['run']['steps']
kp = next(i for i, s in enumerate(cs) if s.get('name', '').startswith("A Canada build that stopped")); cst = next(i for i, s in enumerate(cs) if 'stamp ca-key' in str(s.get('run', '')))
csv_ = next(i for i, s in enumerate(cs) if s.get('name') == 'Save')
check('C1 Canada: a stopped / held build puts data/ca-key back from main, is not stamped, and keeps tonight\'s list',
      kp < cst < csv_ and 'git checkout -q HEAD -- data/ca-key' in cs[kp]['run'] and "env.CA_KEPT != '1'" in cs[cst]['if'] and 'CA_KEPT' in cs[csv_]['run'])
check('C1 Canada: the review rows are merged per province; one summary table', any('keep-rows --unchanged --key-dir data/ca-key' in str(s.get('run', '')) for s in cs)
      and any(s.get('name', '').startswith('Run summary') for s in cs))
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); (t / 'data/ca-key').mkdir(parents=True)
    (t / 'data/ca-key/index.json').write_text(json.dumps({'provinces': {'ON': {'rules': '4b4176190334'}, 'QC': {}}}))
    git(t, 'init', '-q'); git(t, 'add', '-A'); git(t, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'm')
    AJ.main(['record-whole', '--index', str(t / 'data/ca-key/index.json'), '--rows-key', 'provinces', '--kept', '1', '--why', 'held-gate: short CA-ALL', '--out', str(t / 'r.json')])
    rec = json.load(open(t / 'r.json'))
    check('C1 Canada record: a held build lists every province kept and red', rec['red'] == ['ON', 'QC'] and rec['areas']['ON']['code'] == 'held-gate')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
