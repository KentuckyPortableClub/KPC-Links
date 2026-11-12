#!/usr/bin/env python3
"""Nov 12 (KPC owner, 2026-11-11): world key run 43148551915 was CANCELLED (AU's shard red on the master gate, the others cancelled),
and the join still committed a6c493c, which emptied held-joins.* / join-check.* (66 held joins, 35 join-check rows) and re-stamped
index.json. Checked here:
  1) the workflow (parsed YAML + a small evaluator of the `if:` expressions, GitHub's rules: no status function = success() && ...):
     a cancelled run, a failed shard, a cancel mid-join, a red join verdict, a missing part = no join check, no stamp, no Save, no
     world-bounds push, no post-key check; all green = all of them run; the verdict runs before every writing step; the build is not
     started after a red gate; the old workflow is shown saving on tonight's shape (the cause);
  2) the join script: a missing / short part or a country not built = exit 1 and nothing written (tonight's shape: 4 planned groups,
     2 parts); replay of a6c493c on the real tree of its parent: nothing written, every row survives; the old path reproduces the wipe;
  3) expected holds (owner-signed list): kept from main byte for byte (key, index row, review rows), summary row, complete false;
     unsigned / 'KPC owner' / no source / unknown / expired = ignored; sha match = held, sha mismatch = ignored; no previous join = red;
     a real failure in the same shard = red; not on the list + short = red;
  4) a complete green run writes the same bytes as the script on main.
Offline: temp folders only. Run: python3 -B tests/test_world_join_cancel_nov12.py"""
import contextlib, datetime, io, json, os, pathlib, re, shutil, subprocess, sys, tempfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_world_key_join as J  # noqa: E402
SCRIPTS = ROOT / '.github/scripts'
ok = True


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


W = yaml.safe_load((ROOT / '.github/workflows/kpc-world-key.yml').read_text(encoding='utf-8'))
JOIN, POST = W['jobs']['join'], W['jobs']['postcheck']
js = JOIN['steps']
names = [s.get('name', '') for s in js]
WRITERS = {'kept_green_joincheck': 'join check (writes key + review files)', 'keep_rows': 'review rows of expected holds', 'stamp': 'BUILD STAMP (index + status)',
           'save': 'Save (the commit to main)', 'kept_green_1': 'world-bounds push'}


def wkey(s): return 'stamp' if 'stamp world-key' in str(s.get('run', '')) else (s.get('id') or s.get('name'))


GROUPS = json.dumps([{'i': 0, 'countries': 'DE FR', 'cmin': ''}])


def scenario(build, run_cancelled=False, cancel_after=None, outcome=None, built='3', plan_out=None):
    po = {'groups': GROUPS, 'full': '1', 'expected': ''}; po.update(plan_out or {})
    go, ctx = job_runs(JOIN, {'plan': 'success', 'build': build}, {'plan': po}, run_cancelled, {'inputs.outline_test': ''})
    if not go: ran, res = {}, 'skipped'
    else: ran, res = walk(JOIN, ctx, outcome, {'tonight': {'built': built}}, cancel_after, run_cancelled)
    ran2 = {wkey(s): ran.get(s.get('id') or s.get('name') or s.get('uses'), False) for s in js}
    pgo, _ = job_runs(POST, {'plan': 'success', 'join': res}, {'join': {'built': built if go else ''}}, run_cancelled or res == 'cancelled')
    return go, ran2, res, pgo


def nothing_written(r): return not any(r[1].get(k) for k in WRITERS) and not r[3]


r = scenario('success')
check('all green: join, join check, review rows, stamp, Save, world-bounds and the post-key check all run', r[0] and all(r[1].get(k) for k in WRITERS) and r[3])
# Nov 12 (KPC owner, 2026-11-12) CHANGED: each country stands alone (handoff part A): a red shard on a run that was NOT cancelled no longer stops the join
r = scenario('failure')
check('a failed shard (needs.build.result failure, run not cancelled): the join runs and saves the green countries (was: no join)', r[0] and r[1]['save'] and r[1]['stamp'])
check('tonight\'s shape (AU failed, the others cancelled, the run cancelled): no join, nothing written', nothing_written(scenario('failure', run_cancelled=True)))
check('a cancelled build: nothing written', nothing_written(scenario('cancelled', run_cancelled=True)))
check('a cancel that arrives after the builds finished green, before the join: no join', not scenario('success', run_cancelled=True)[0])
for at in ('tonight', 'join_verdict', 'kept_green_joincheck', 'keep_rows'):
    rr = scenario('success', cancel_after=at)
    check(f'a cancel mid-join (after step {at}): no Save, no world-bounds push, no stamp, no post-key check',
          not rr[1]['save'] and not rr[1]['kept_green_1'] and (at in ('kept_green_joincheck', 'keep_rows') or not rr[1]['stamp']) and not rr[3])
rr = scenario('success', outcome={'join_verdict': 'failure'})
# Nov 12 (KPC owner, 2026-11-12) CHANGED: the verdict step is now "May we save the green set?" (a held country no longer makes it red; a kept country that is not main's does)
check('"May we save the green set?" red: no join check, stamp, Save, world-bounds, post-key check', nothing_written(rr))
rr = scenario('success', outcome={'tonight': 'failure'}, built='0')
check('the join stopped (a missing / short part, exit 1, built=0): nothing written', nothing_written(rr))
rr = scenario('success', outcome={'keep_rows': 'failure'})
check('the review rows could not be put back: no Save, no world-bounds push, no post-key check', not rr[1]['save'] and not rr[1]['kept_green_1'] and not rr[3])
vi = names.index(next(n for n in names if n.startswith('May we save the green set?')))   # Nov 12 CHANGED: was 'Master gate verdict of the join'
wi = [i for i, s in enumerate(js) if wkey(s) in WRITERS]
check('the join verdict runs BEFORE every writing step', wi and vi < min(wi) and js[vi].get('id') == 'join_verdict')
# Nov 12 (KPC owner, 2026-11-12) CHANGED: a green build of EVERY shard is no longer required (that was the all-or-nothing join); !cancelled() and the verdict stay
G = ["!cancelled()", "steps.join_verdict.outcome == 'success'"]
check('every writing step needs !cancelled() and the passed verdict (in its own if:), not a green build of every shard', all(all(g in str(js[i].get('if', '')) for g in G)
      and "needs.build.result == 'success'" not in str(js[i].get('if', '')) for i in wi))
check('the join job: !cancelled(), not needs.build.result == \'success\' (Nov 12 CHANGED), the not-skipped and has-groups checks kept, no always()',
      '!cancelled()' in JOIN['if'] and "needs.build.result == 'success'" not in JOIN['if'] and "needs.build.result != 'skipped'" in JOIN['if'] and "needs.plan.outputs.groups != '[]'" in JOIN['if'] and 'always()' not in JOIN['if'])
check('the post-key check (the key-check commit) needs a green join', "needs.join.result == 'success'" in POST['if'] and '!cancelled()' in POST['if'])
WRITE_RE = re.compile(r'git push|git commit|kpc_save_overwrite|kpc_push_data|save_json|stamp world-key|kpc_join_check|keep-rows|gh workflow run')
bare = [(j, s.get('name')) for j, jb in W['jobs'].items() for s in jb.get('steps', []) if 'always()' in str(s.get('if', '')) and WRITE_RE.search(str(s.get('run', '')))]
check('no step that writes or commits is guarded by always() anywhere in kpc-world-key.yml', not bare)
alw = [(j, s.get('name', '')[:60], s.get('if')) for j, jb in W['jobs'].items() for s in jb.get('steps', []) if 'always()' in str(s.get('if', ''))]
alw += [(j, '(job)', jb.get('if')) for j, jb in W['jobs'].items() if 'always()' in str(jb.get('if', ''))]
print('INFO always() left in kpc-world-key.yml:'); [print(f'INFO   {j}: {n} :: {i}') for j, n, i in alw]
check('always() is left only on build-job part / upload / checkpoint / verdict steps and the read-only "Report hidden failures" steps',
      alw and all(j == 'build' or n.startswith('Report hidden failures') for j, n, _ in alw) and not any(n == '(job)' for _, n, _ in alw))
B = W['jobs']['build']['steps']
bstep = next(s for s in B if s.get('id') == 'kept_green_b')
for rc, want in (('0', True), ('7', False), ('', False), ('1', False)):
    check(f'build: the Build step runs only on a green gate (gate rc {rc or "none"} -> {"build" if want else "not started"})',
          evaluate(f"success() && ({bstep['if']})", {'steps.kept_green_master.outputs.rc': rc}, {'always': True, 'success': True, 'failure': False, 'cancelled': False}) == want)
gate = next(s for s in B if s.get('id') == 'kept_green_master')
check('build: the gate step hands its exit code to the Build step (rc output)', 'echo "rc=$mg" >> "$GITHUB_OUTPUT"' in gate['run'])
plan_run = next(s for s in W['jobs']['plan']['steps'] if s.get('id') == 'p')['run']
check('plan: expected holds are decided before the build, from the APPROVED file only, and a hold means not a full build',
      'kpc_world_key_join.py expected --file data/outlines/world-expected-holds.approved.json' in plan_run and '|| exit 1' in plan_run
      and """[ -z "$EXPECTED" ]; then echo 'full=1'""" in plan_run and W['jobs']['plan']['outputs']['expected'] == '${{ steps.p.outputs.expected }}')
check('plan: each hold is checked against the current W-<CC> copy sha (--cache cache/world)',
      '--cache cache/world' in plan_run and 'gh release download boundary-cache' in plan_run and 'W-$c.json.gz' in plan_run)
tn = next(s for s in js if s.get('id') == 'tonight')
check('join: --planned-groups and --expected go to the join', '--planned-groups "$PLAN_GROUPS" --expected "$EXPECTED"' in tn['run'] and tn['env']['EXPECTED'] == '${{ needs.plan.outputs.expected }}')
st = next(s for s in js if 'stamp world-key' in str(s.get('run', '')))
check('join: the stamp is told the expected holds', st['env'].get('KPC_HELD_EXPECTED') == '${{ needs.plan.outputs.expected }}')
check('no new trigger, no cron change', sorted(W[True]) == ['schedule', 'workflow_dispatch'] and [c['cron'] for c in W[True]['schedule']] == ['17 11 3 * *', '7 10 * * *'])

# the same cancel hole in the US and Canada keys: the join / Save never on a cancelled run
US = yaml.safe_load((ROOT / '.github/workflows/kpc-us-key.yml').read_text(encoding='utf-8'))
CA = yaml.safe_load((ROOT / '.github/workflows/kpc-ca-key.yml').read_text(encoding='utf-8'))
usave = next(s for s in US['jobs']['join']['steps'] if s.get('name') == 'Save'); csave = next(s for s in CA['jobs']['run']['steps'] if s.get('name') == 'Save')
check('US key: the join job and its Save need !cancelled() (not always())', '!cancelled()' in US['jobs']['join']['if'] and 'always()' not in US['jobs']['join']['if']
      and usave['if'].startswith('${{ !cancelled()') and 'always()' not in usave['if'])   # Nov 12: + the stamp step must be green and (#161 must-fix) the review-file merge step must not have failed
check('Canada key: its Save needs !cancelled() (not always())', csave['if'].startswith("${{ !cancelled() && env.SKIP != '1'") and 'always()' not in csave['if'])   # Nov 12 (#161 must-fix): + the review-file merge step must not have failed
for nm, wf in (('kpc-us-key.yml', US), ('kpc-ca-key.yml', CA)):
    bad2 = [s.get('name') for jb in wf['jobs'].values() for s in jb.get('steps', []) if 'always()' in str(s.get('if', '')) and WRITE_RE.search(str(s.get('run', '')))]
    check(f'{nm}: no step that saves or commits is guarded by always()', not bad2)

# the cause, on the workflow as it was (main before this change, when git has it)
old_txt = subprocess.run(['git', 'show', 'a6c493c:.github/workflows/kpc-world-key.yml'], cwd=ROOT, capture_output=True, text=True).stdout
if old_txt:
    OW = yaml.safe_load(old_txt); OJ = OW['jobs']['join']
    go, ctx = job_runs(OJ, {'plan': 'success', 'build': 'failure'}, {'plan': {'groups': GROUPS, 'full': '1'}}, True, {'inputs.outline_test': ''})
    ran, _ = walk(OJ, ctx, {}, {'tonight': {'built': '2'}}, None, True) if go else ({}, '')
    check('the cause (the workflow of a6c493c): on a cancelled run with a red shard the old join ran and its Save ran', go and ran.get('Save'))
else:
    print('INFO a6c493c not in this checkout: the old-workflow case is not checked')


# ------------------------------------------------------------------ 2) the join script on fixtures
def run_join(t, parts, *extra):
    """In the fixture's folder: kpc_save's status file (data/status/...) is flushed there, never into this repo."""
    import kpc_save
    buf = io.StringIO(); cwd = os.getcwd(); os.chdir(t)
    try:
        with contextlib.redirect_stdout(buf):
            rc = J.main([*map(str, parts), '--gate', '--held-out', str(t / 'held.txt'), '--out', str(t / 'data/world-key'), '--bounds', str(t / 'data/world-bounds'),
                         '--failed-out', str(t / 'failed.txt'), *extra])
        kpc_save.flush_status()
    finally: os.chdir(cwd)
    return rc, buf.getvalue()


def mkpart(t, i, countries, done=None, rc='0', short='', files=None):
    d = t / 'parts' / f'world-key-part-{i}'; (d / 'world-key' / 'review').mkdir(parents=True, exist_ok=True); (d / 'world-bounds').mkdir(exist_ok=True)
    done = countries if done is None else done
    (d / 'countries.txt').write_text(' '.join(countries) + '\n'); (d / 'failed.txt').write_text(''.join(c + '\n' for c in countries if c not in done))
    (d / 'done.txt').write_text(''.join(c + '\n' for c in done))
    idx = {}
    for c in done:
        body = (files or {}).get(c) or json.dumps({'parks': {f'{c}-0001': {'n': f'{c} park', 'm': [[1, 'x', 'L']], 'g': 'official', 'bk': [1, 0.2]}}})
        (d / 'world-key' / f'{c}.json').write_text(body); (d / 'world-key' / 'review' / f'{c}.md').write_text(f'review {c} new')
        idx[c] = {'parks': 1, 'new': i}
    (d / 'world-key' / 'index.json').write_text(json.dumps({'countries': idx}))
    (t / f'rc{i}').write_text(rc + '\n'); (t / f'short{i}').write_text(short)
    with contextlib.redirect_stdout(io.StringIO()):
        J.main_verdict(['verdict', '--part', str(d), '--countries', ' '.join(countries), '--rc-file', str(t / f'rc{i}'), '--short-file', str(t / f'short{i}')])
    return d


def git(t, *a): return subprocess.run(['git', *a], cwd=t, capture_output=True, text=True)


def snapshot(t):
    return {str(p.relative_to(t)): p.read_bytes() for p in sorted((t / 'data').rglob('*')) if p.is_file()}


REVIEW_MAIN = {}


def mkrepo(t, countries=('AU', 'DE', 'FR')):
    """A tiny world key on 'main' (one commit), with review rows of every country (as an earlier join check wrote them)."""
    wk = t / 'data/world-key'; (wk / 'review').mkdir(parents=True); (wk / 'tracts').mkdir(); (t / 'data/world-bounds').mkdir(parents=True)
    for c in countries:
        (wk / f'{c}.json').write_text(json.dumps({'parks': {f'{c}-0001': {'n': f'{c} park', 'm': [[1, 'x', 'L']], 'g': 'official', 'bk': [1, 0.2]},
                                                            f'{c}-0002': {'n': f'{c} far', 'g': 'pin', 'm': [], 'c': [[2, 'y', 'L', 'held: far']]}}}, separators=(',', ':')))
        (wk / 'tracts' / f'{c}.json').write_text('{"about":"t","area":"%s"}' % c)
    idx = {'countries': {c: {'parks': 2, 'old': True} for c in countries}, 'build': 'W-1', 'built': '2026-11-11 00:00 UTC'}
    (wk / 'index.json').write_text(json.dumps(idx, indent=1))
    held = [{'park': f'{c}-0002', 'area': c, 'name': f'{c} far – é', 'pin_km': 30.0, 'was_g': 'official', 'held_ids': '2', 'held_names': 'y', 'reason': 'far, "quoted"',
             'decided_by': 'rule', 'to_keep_it': 'sign'} for c in countries]
    rows = [{'park': f'{c}-0001', 'area': c, 'name': f'{c}, park', 'outline_ac': '', 'official_ac': '', 'pin_km': 16.0, 'suspect': 'far', 'decided_by': 'rule', 'evidence_only': 'yes'} for c in countries]
    import csv
    (wk / 'review/held-joins.json').write_text(json.dumps({'key': 'world', 'count': len(held), 'parks': held}, indent=1, ensure_ascii=False))
    (wk / 'review/join-check.json').write_text(json.dumps({'key': 'world', 'files_checked': 3, 'suspect': len(rows), 'held': len(held), 'rows': rows}, indent=1, ensure_ascii=False))
    for name, cols, data in (('held-joins.csv', list(held[0]), held), ('join-check.csv', list(rows[0]), rows),
                             ('held-joins-ledger.csv', ['park', 'kind', 'proposal'], [{'park': h['park'], 'kind': 'pile-enter', 'proposal': 'p\nmulti-line'} for h in held])):
        with open(wk / 'review' / name, 'w', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(data)
    git(t, 'init', '-q'); git(t, 'add', '-A'); git(t, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'main')


def rows_of(text, cc, name):
    if name.endswith('.json'):
        d = json.loads(text)   # a row's own bytes in the file: json.dump indent 1, two levels deep
        return ['\n'.join('  ' + ln for ln in json.dumps(r, indent=1, ensure_ascii=False).splitlines()) for r in d.get('parks', d.get('rows', [])) if J._row_cc(r, name) == cc]
    return [raw for raw, r in J._csv_records(text)[1] if J._row_cc(r, name) == cc]


# 2a) tonight's shape: 4 planned groups, 2 parts present and green, 2 absent -> exit 1, nothing written
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); mkrepo(t, ('AU', 'DE', 'FR', 'NO', 'SE', 'MT')); before = snapshot(t)
    groups = json.dumps([{'i': 0, 'countries': 'DE MT', 'cmin': ''}, {'i': 1, 'countries': 'FR', 'cmin': ''}, {'i': 2, 'countries': 'NO SE', 'cmin': ''}, {'i': 3, 'countries': 'AU', 'cmin': '300'}])
    p1, p2 = mkpart(t, 1, ['FR']), mkpart(t, 2, ['NO', 'SE'])
    os.environ['GITHUB_STEP_SUMMARY'] = str(t / 'summary.md'); go = t / 'out'; go.write_text(''); os.environ['GITHUB_OUTPUT'] = str(go)
    try: rc, log = run_join(t, [p1, p2], '--planned-groups', groups, '--record', str(t / 'rec.json'))
    finally: os.environ.pop('GITHUB_STEP_SUMMARY'); os.environ.pop('GITHUB_OUTPUT')
    # Nov 12 (KPC owner, 2026-11-12) CHANGED: (was: exit 1, built=0, nothing written) each country stands alone: FR NO SE saved, the others kept from main and red
    rec = json.loads((t / 'rec.json').read_text()); aft = snapshot(t)
    check('tonight\'s shape (4 groups, 2 parts): FR NO SE joined (built=3), AU DE MT kept from main and red', rc == 0 and 'built=3' in go.read_text()
          and rec['joined'] == ['FR', 'NO', 'SE'] and rec['red'] == ['AU', 'DE', 'MT'])
    check('tonight\'s shape: AU DE MT files byte-identical to main', all(aft[f'data/world-key/{c}.json'] == before[f'data/world-key/{c}.json'] for c in ('AU', 'DE', 'MT')))
    # Nov 12 (KPC owner, 2026-11-12) CHANGED: the one summary table is written after the stamp by kpc_area_join.py summary (tests/test_per_area_join_nov12.py)
    # the same parts through the old path (no --planned-groups) still join FR NO SE: what this patch stops in the workflow
    pass

# 2b) a missing / short part when every build is green; a country not built in its part (a real failure in the same shard)
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); mkrepo(t); before = snapshot(t)
    g2 = json.dumps([{'i': 0, 'countries': 'DE FR', 'cmin': ''}, {'i': 1, 'countries': 'AU', 'cmin': '300'}])
    rc, log = run_join(t, [mkpart(t, 0, ['DE', 'FR'])], '--planned-groups', g2)
# Nov 12 (KPC owner, 2026-11-12) CHANGED: (was: exit 1, nothing written)
    check('a lost part (all builds green, AU\'s artifact missing): DE FR saved, AU kept from main', rc == 0 and snapshot(t)['data/world-key/AU.json'] == before['data/world-key/AU.json']
          and snapshot(t)['data/world-key/DE.json'] != before['data/world-key/DE.json'] and 'RED, kept from main (not saved): AU' in log)
    subprocess.run(['git', 'checkout', '-q', '--', '.'], cwd=t); subprocess.run(['git', 'clean', '-fdq', 'data'], cwd=t)
    shutil.rmtree(t / 'parts')
    rc, log = run_join(t, [mkpart(t, 0, ['DE', 'FR'], done=['DE']), mkpart(t, 1, ['AU'])], '--planned-groups', g2)
# Nov 12 (KPC owner, 2026-11-12) CHANGED: (was: exit 1, nothing written, not even DE)
    check('a real failure in the same shard (FR not built, DE built): DE saved, FR kept from main', rc == 0 and snapshot(t)['data/world-key/FR.json'] == before['data/world-key/FR.json']
          and snapshot(t)['data/world-key/DE.json'] != before['data/world-key/DE.json'])
    subprocess.run(['git', 'checkout', '-q', '--', '.'], cwd=t); subprocess.run(['git', 'clean', '-fdq', 'data'], cwd=t)
    shutil.rmtree(t / 'parts')
    d = mkpart(t, 0, ['DE', 'FR']); (d / 'world-key' / 'FR.json').write_text('{"cut')
    rc, log = run_join(t, [d, mkpart(t, 1, ['AU'])], '--planned-groups', g2, '--held-out', str(t / 'held.txt'))
    check('a part cut short after its verdict (half download): its countries are held (not joined, kept from main)',
          rc == 0 and {'DE', 'FR'} <= set((t / 'held.txt').read_text().split()))

# 2c) the AU shard of tonight: gate exit 7, short W-AU, part built, verdict red
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); mkrepo(t); before = snapshot(t)
    d = mkpart(t, 3, ['AU'], rc='7', short='W-AU\n')
    v = json.loads((d / 'master-gate.json').read_text())
    check('AU-shaped part: the verdict in the part is red and holds AU', v['gate'] == 'red' and v['held'] == ['AU'])
    vstep = next(s for s in B if s.get('name', '').startswith('Master gate verdict'))['run']
    (t / 'master-gate.rc').write_text('7\n'); (t / 'master-short.txt').write_text('W-AU\n')
    r = subprocess.run(['bash', '-e', '-c', vstep], env=dict(os.environ, RUNNER_TEMP=str(t)), capture_output=True, text=True)
    check('AU-shaped shard: the build job\'s verdict step goes red (the shard is red; Nov 12: its countries are kept, the others still save)', r.returncode == 1)
    rc, _ = run_join(t, [d], '--planned-groups', json.dumps([{'i': 3, 'countries': 'AU', 'cmin': '300'}]))
    check('AU not on the list, its copy short: AU is held (not joined, main\'s file kept)',
          rc == 0 and (t / 'held.txt').read_text().startswith('AU ') and (t / 'data/world-key/AU.json').read_bytes() == before['data/world-key/AU.json'])


# 3) expected holds
def holds_file(t, entries, name='world-expected-holds.approved.json'):
    p = t / name; p.write_text(json.dumps({'holds': entries})); return p


AU_COPY_SHA = '8c8b75795c77ee02ceb01360548258ba93f8b47f44a8c26ded55ba3080052598'
MT_COPY_SHA = '9c94cb55777d417b1fcf92aae95308dcd539415d0e833ca1ff8af574908f3b7b'


with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); mkrepo(t)
    today = datetime.date.today().isoformat(); past = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    sig = {'reason': 'short copy', 'approved_by': 'Brandon (KZ4CP)', 'approved_date': today,
           'source': 'test', 'copy_sha256': 'ab' * 32}
    h, n, e = J.load_expected(holds_file(t, {'AU': sig}), 'AU DE FR', t / 'data/world-key')
    check('a signed entry for a country of this run with a previous join: held (expected)', list(h) == ['AU'] and not e)
    cases = {'unsigned': dict(sig, approved_by=''), 'not a person': dict(sig, approved_by='waiting for KPC owner'),
             'kpc owner alias': dict(sig, approved_by='KPC owner'), 'future date': dict(sig, approved_date='2999-01-01'),
             'no reason': dict(sig, reason=''), 'no source': dict(sig, source=''), 'no copy sha': dict(sig, copy_sha256=''),
             'bad copy sha': dict(sig, copy_sha256='FILL IN'), 'expired review_by': dict(sig, review_by=past),
             'bad review_by': dict(sig, review_by='soon')}
    for k, ent in cases.items():
        h, n, e = J.load_expected(holds_file(t, {'AU': ent}), 'AU DE FR', t / 'data/world-key')
        check(f'{k} entry: ignored (AU built as a normal country) and the run says so', h == {} and n and not e)
    h, n, e = J.load_expected(holds_file(t, {'XX': sig, 'au': sig, 'JP': sig}), 'AU DE FR', t / 'data/world-key')
    check('unknown / lower-case / not-in-this-run codes: ignored and said', h == {} and len(n) == 3 and not e)
    h, n, e = J.load_expected(holds_file(t, {'AU': sig}, 'world-expected-holds.proposed.json'), 'AU DE FR', t / 'data/world-key')
    check('a proposed file is never read', h == {} and n)
    (t / 'data/world-key/DE.json').write_text(json.dumps({'parks': {'DE-0001': {'g': 'pin', 'm': []}}}))
    h, n, e = J.load_expected(holds_file(t, {'DE': sig}), 'AU DE FR', t / 'data/world-key')
    check('an expected hold with no joined park on main (nothing to keep): an error', h == {} and e)
    r = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'kpc_world_key_join.py'), 'expected', '--file', str(holds_file(t, {'DE': sig})), '--countries', 'AU DE FR',
                        '--key', str(t / 'data/world-key')], capture_output=True, text=True)
    check('... and the plan step stops red (exit 1) with a clear message', r.returncode == 1 and 'nothing to keep' in r.stderr)
    r = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'kpc_world_key_join.py'), 'expected', '--file', str(holds_file(t, {'AU': sig})), '--countries', 'AU DE FR',
                        '--key', str(t / 'data/world-key')], capture_output=True, text=True)
    check('the plan step prints the list and one notice "AU held (expected): keeping the previous join"', r.returncode == 0 and r.stdout.strip() == 'AU'
          and r.stderr.count('AU held (expected): keeping the previous join') == 1)
    # sha match / mismatch (a hold is for one saved copy)
    cache = t / 'cache'; cache.mkdir()
    (cache / 'W-AU.json.gz').write_bytes(b'W-AU fixture copy')
    match_sha = J._sha(cache / 'W-AU.json.gz')
    h, n, e = J.load_expected(holds_file(t, {'AU': dict(sig, copy_sha256=match_sha)}), 'AU DE FR', t / 'data/world-key', cache_dir=cache)
    check('sha match: the hold applies', list(h) == ['AU'] and not e)
    h, n, e = J.load_expected(holds_file(t, {'AU': dict(sig, copy_sha256='cd' * 32)}), 'AU DE FR', t / 'data/world-key', cache_dir=cache)
    check('sha mismatch: ignored (a changed copy does not inherit the hold) and the run says so',
          h == {} and any('sha mismatch' in x for x in n) and not e)
    r = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'kpc_world_key_join.py'), 'expected', '--file', str(holds_file(t, {'AU': dict(sig, copy_sha256=match_sha)})),
                        '--countries', 'AU DE FR', '--key', str(t / 'data/world-key'), '--cache', str(cache)], capture_output=True, text=True)
    check('plan step with --cache and a matching copy: AU held', r.returncode == 0 and r.stdout.strip() == 'AU')
    r = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'kpc_world_key_join.py'), 'expected', '--file', str(holds_file(t, {'AU': dict(sig, copy_sha256='cd' * 32)})),
                        '--countries', 'AU DE FR', '--key', str(t / 'data/world-key'), '--cache', str(cache)], capture_output=True, text=True)
    check('plan step with --cache and a mismatched copy: nothing held, sha mismatch said', r.returncode == 0 and r.stdout.strip() == '' and 'sha mismatch' in r.stderr)
shipped = json.loads((ROOT / 'data/outlines/world-expected-holds.approved.json').read_text(encoding='utf-8'))
prop = json.loads((ROOT / 'data/outlines/world-expected-holds.proposed.json').read_text(encoding='utf-8'))
h, n, e = J.load_expected(ROOT / 'data/outlines/world-expected-holds.approved.json', 'AU DE GB MT', ROOT / 'data/world-key')
au, mt = shipped['holds']['AU'], shipped['holds']['MT']
check('shipped: AU and MT are active owner-signed holds (both have joined parks on main)',
      sorted(h) == ['AU', 'MT'] and not e
      and au['approved_by'] == 'Brandon (KZ4CP), decided by Quality per his delegation'
      and mt['approved_by'] == 'Brandon (KZ4CP)'
      and au['approved_date'] == mt['approved_date'] == '2026-11-11'
      and au['source'] == 'Quality chat t184u, 11:02 PM CT'
      and mt['source'] == 'Super chat t1419u 10:49 PM CT; Quality chat t181u 10:56 PM CT'
      and au['copy'] == 'W-AU' and mt['copy'] == 'W-MT'
      and au['copy_sha256'] == AU_COPY_SHA and mt['copy_sha256'] == MT_COPY_SHA
      and 'review_by' in au and 'review_by' in mt
      and 't1419u' in mt['reason'] and '14-record baseline is not signed' in mt['reason']
      and 'MT' not in (prop.get('holds') or {})
      and not (ROOT / 'data/world-key/expected-holds.json').exists())

# 3b) expected hold + all else green: run green, saved, AU's files and rows byte-identical to main, summary row, complete false
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); mkrepo(t); before = snapshot(t)
    far = json.dumps({'parks': {'DE-0001': {'n': 'DE park', 'm': [[1, 'x', 'L']], 'g': 'official', 'bk': [1, 0.2]},
                                'DE-0002': {'n': 'DE far', 'm': [[2, 'y', 'L']], 'g': 'official', 'bk': [2, 40.0]}}})
    groups = json.dumps([{'i': 0, 'countries': 'DE FR', 'cmin': ''}])
    os.environ['GITHUB_STEP_SUMMARY'] = str(t / 'summary.md')
    cwd = os.getcwd(); os.chdir(t)
    try:
        rc, log = run_join(t, [mkpart(t, 0, ['DE', 'FR'], files={'DE': far})], '--planned-groups', groups, '--expected', 'AU')
        import kpc_join_check as JC
        with contextlib.redirect_stdout(io.StringIO()): JC.run({'KEY': 'world', 'ANSWER_SHEET': str(t / 'none')}, root=str(t), plain=True)
        wiped = (t / 'data/world-key/review/held-joins.csv').read_text()
        with contextlib.redirect_stdout(io.StringIO()): J.main_keep_rows(['keep-rows', '--countries', 'AU', '--review', str(t / 'data/world-key/review')])
        import kpc_key_freeze as KF
        env0 = dict(os.environ)
        os.environ.update({'KPC_BUILD_FAILED_FILE': str(t / 'failed.txt'), 'KPC_HELD_EXPECTED': 'AU', 'GITHUB_RUN_ID': '99', 'KPC_FULL_BUILD': '0'})
        with contextlib.redirect_stdout(io.StringIO()): KF.stamp('world-key')
        import kpc_save; kpc_save.flush_status()
        os.environ.clear(); os.environ.update(env0)
    finally:
        os.chdir(cwd); os.environ.pop('GITHUB_STEP_SUMMARY', None)
    after = snapshot(t)
    check('expected hold + the rest green: the join saves DE FR (exit 0)', rc == 0 and after['data/world-key/DE.json'] != before['data/world-key/DE.json'])
    check('(the join check alone wiped AU\'s held-joins row: the gap keep-rows closes)', 'AU-0002' not in wiped)
    check('AU\'s key and tracts files are byte-identical to main', all(after[f] == before[f] for f in ('data/world-key/AU.json', 'data/world-key/tracts/AU.json')))
    allsame = True
    for name in J.REVIEW_FILES:
        mt, nt = before[f'data/world-key/review/{name}'].decode(), after[f'data/world-key/review/{name}'].decode()
        same = rows_of(mt, 'AU', name) == rows_of(nt, 'AU', name) and rows_of(mt, 'AU', name) and all(x in nt for x in rows_of(mt, 'AU', name))
        allsame = allsame and bool(same)
        check(f'review/{name}: AU\'s rows byte-identical to main; this run\'s DE / FR rows in', same and (name == 'join-check.csv' or name == 'join-check.json' or rows_of(nt, 'DE', name)))
    hj = json.loads(after['data/world-key/review/held-joins.json'])
    check('held-joins.json: count = the merged rows, kept_from_main names AU', hj['count'] == len(hj['parks']) and hj['kept_from_main'] == ['AU'])
    idx = json.loads(after['data/world-key/index.json']); oidx = json.loads(before['data/world-key/index.json'])
    check('index.json: AU\'s row unchanged, DE FR re-stamped, held_expected [AU], complete false, AU not named failed',
          idx['countries']['AU'] == oidx['countries']['AU'] and idx['countries']['DE'] != oidx['countries']['DE'] and idx.get('held_expected') == ['AU']
          and idx.get('complete') is False and 'AU' not in (idx.get('failed') or []) and idx['build'] == 'W-99' and idx.get('previous_build') == 'W-1')
    # Nov 12 (KPC owner, 2026-11-12) CHANGED: the join no longer writes the summary table itself (one table per run, after the stamp: kpc_area_join.py summary)
    rr = scenario('success', plan_out={'expected': 'AU', 'full': '0'})
    check('workflow: a run with an expected hold and every shard green saves (green)', rr[2] == 'success' and rr[1]['save'] and rr[1]['keep_rows'])

# 3c) keep-rows: a file whose rows cannot be split per country is not written (main's copy kept) and the run says so
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); mkrepo(t)
    f = t / 'data/world-key/review/join-check.csv'; main_bytes = f.read_bytes()
    f.write_text('other,header\n1,2\n')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): J.main_keep_rows(['keep-rows', '--countries', 'AU', '--review', str(t / 'data/world-key/review')])
    check('a review file with another header: main\'s copy kept whole, a warning says it was not written', f.read_bytes() == main_bytes and 'NOT written this run' in buf.getvalue())
    hj = t / 'data/world-key/review/held-joins.json'; hj.write_text(json.dumps({'parks': [{'park': 'DE-1'}]}))
    with contextlib.redirect_stdout(io.StringIO()): J.main_keep_rows(['keep-rows', '--countries', 'AU', '--review', str(t / 'data/world-key/review')])
    check('a row with no country: that file is not written either', hj.read_bytes() == git(t, 'show', 'HEAD:data/world-key/review/held-joins.json').stdout.encode())

# 4) a complete green run: the same bytes as the join script on main (no --planned-groups there), and keep-rows with no countries does nothing
old_join = subprocess.run(['git', 'show', 'a6c493c:.github/scripts/kpc_world_key_join.py'], cwd=ROOT, capture_output=True, text=True).stdout
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td); outs = []
    if old_join: (td / 'old').mkdir(); (td / 'old' / 'kpc_world_key_join.py').write_text(old_join); [shutil.copy(SCRIPTS / x, td / 'old' / x) for x in ('kpc_save.py',)]
    for which in ('new', 'old'):
        if which == 'old' and not old_join: continue
        t = td / which / 'run'; t.mkdir(parents=True); mkrepo(t)
        parts = [mkpart(t, 0, ['DE', 'FR']), mkpart(t, 1, ['AU'])]
        g = json.dumps([{'i': 0, 'countries': 'DE FR', 'cmin': ''}, {'i': 1, 'countries': 'AU', 'cmin': '300'}])
        script = str(SCRIPTS / 'kpc_world_key_join.py') if which == 'new' else str(td / 'old' / 'kpc_world_key_join.py')
        args = [sys.executable, '-B', script, *map(str, parts), '--gate', '--held-out', str(t / 'held.txt'), '--out', 'data/world-key', '--bounds', 'data/world-bounds', '--failed-out', str(t / 'failed.txt')]
        if which == 'new': args += ['--planned-groups', g, '--expected', '']
        r = subprocess.run(args, cwd=t, capture_output=True, text=True, env={k: v for k, v in os.environ.items() if k not in ('GITHUB_OUTPUT', 'GITHUB_STEP_SUMMARY', 'GITHUB_WORKFLOW')})
        if which == 'new':
            subprocess.run([sys.executable, '-B', str(SCRIPTS / 'kpc_world_key_join.py'), 'keep-rows', '--countries', '', '--review', 'data/world-key/review'], cwd=t, capture_output=True)
            (t / 'rec.json').unlink(missing_ok=True)
        outs.append((r.returncode, snapshot(t), (t / 'failed.txt').read_bytes()))
    if len(outs) == 2:
        check('a complete green run: byte-identical tree to the join script of a6c493c (keys, index, review, tracts, status)', outs[0][0] == outs[1][0] == 0 and outs[0][1] == outs[1][1] and outs[0][2] == outs[1][2])
    else:
        print('INFO a6c493c not in this checkout: the byte-identical check against the old script is not run')

# 5) replay of a6c493c on the real tree of its parent (stand-in parts for NO and SE from a6c493c's own files)
have = git(ROOT, 'cat-file', '-e', 'a6c493c^{commit}').returncode == 0 and git(ROOT, 'cat-file', '-e', 'a6c493c^^{commit}').returncode == 0
if have:
    with tempfile.TemporaryDirectory() as td:
        t = pathlib.Path(td)
        a = subprocess.run(f"git archive a6c493c^ data/world-key | tar -x -C '{t}'", shell=True, cwd=ROOT)
        (t / 'data/world-bounds').mkdir(parents=True, exist_ok=True)
        git(t, 'init', '-q'); git(t, 'add', '-A'); git(t, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'parent')
        before = snapshot(t)
        parts = []
        for i, c in ((2, 'NO'), (3, 'SE')):
            files = {c: git(ROOT, 'show', f'a6c493c:data/world-key/{c}.json').stdout}
            d = mkpart(t, i, [c], files=files)
            (d / 'world-key' / 'tracts').mkdir(exist_ok=True); (d / 'world-key' / 'tracts' / f'{c}.json').write_text(git(ROOT, 'show', f'a6c493c:data/world-key/tracts/{c}.json').stdout)
            with contextlib.redirect_stdout(io.StringIO()):
                J.main_verdict(['verdict', '--part', str(d), '--countries', c, '--rc-file', str(t / f'rc{i}'), '--short-file', str(t / f'short{i}')])
            parts.append(d)
        idx = json.loads(before['data/world-key/index.json'])
        planned = sorted(set(idx['countries']))
        rest = [c for c in planned if c not in ('NO', 'SE', 'AU')]
        groups = json.dumps([{'i': 0, 'countries': ' '.join(rest[::2]), 'cmin': ''}, {'i': 1, 'countries': ' '.join(rest[1::2]), 'cmin': ''},
                             {'i': 2, 'countries': 'NO', 'cmin': ''}, {'i': 3, 'countries': 'SE AU', 'cmin': ''}])
        rc, log = run_join(t, parts, '--planned-groups', groups)
        # Nov 12 (KPC owner, 2026-11-12) CHANGED: (was: the join stops and writes nothing) NO SE are joined, every other country is kept from main; the rows oracle with the
        # join check + the per-country review merge is in tests/test_per_area_join_nov12.py (W4)
        aft = snapshot(t)
        check(f'replay a6c493c ({len(planned)} planned countries, parts only for NO SE): only NO SE files change; every other key file is main\'s',
              rc == 0 and all(aft[k] == v for k, v in before.items() if k.startswith('data/world-key/') and k.count('/') == 2 and k.endswith('.json') and k[-7:-5] not in ('NO', 'SE') and not k.endswith('index.json')))
        subprocess.run(['git', 'checkout', '-q', '--', '.'], cwd=t); subprocess.run(['git', 'clean', '-fdq', 'data'], cwd=t)
        diff = git(ROOT, 'diff', 'a6c493c^', 'a6c493c', '--', 'data/world-key/review').stdout
        gone = [ln[1:] for ln in diff.splitlines() if ln.startswith('-') and not ln.startswith('---')]
        hj = before['data/world-key/review/held-joins.csv'].decode()
        allrev = b''.join(v for k, v in before.items() if k.startswith('data/world-key/review/'))
        check(f'replay oracle: all {len(gone)} lines a6c493c deleted from the review files are still there, byte for byte', gone and all(x.encode() in allrev for x in gone))
        check('replay oracle: the 66 held joins and 35 join-check rows of the parent survive', json.loads(before['data/world-key/review/held-joins.json'])['count'] == 66
              and len(J._csv_records(hj)[1]) == 66 and len(J._csv_records(before['data/world-key/review/join-check.csv'].decode())[1]) == 35)
        # the old path on the same tree: the join + the join check reproduce a6c493c's wipe
        rc, _ = run_join(t, parts)
        import kpc_join_check as JC
        cwd = os.getcwd(); os.chdir(t)
        try:
            with contextlib.redirect_stdout(io.StringIO()): JC.run({'KEY': 'world', 'ANSWER_SHEET': str(t / 'none')}, root=str(t), plain=True)
        finally: os.chdir(cwd)
        new_hj = json.loads((t / 'data/world-key/review/held-joins.json').read_text())
        kept = [r for r in J._csv_records((t / 'data/world-key/review/join-check.csv').read_text())[1]]
        check(f'(the cause, replayed: the old path + the join check leave {new_hj["count"]} held joins of 66 and {len(kept)} join-check row(s) of 35, '
              f'like a6c493c: 0 and 1)', new_hj['count'] == 0 and len(kept) <= 2)
else:
    print('INFO a6c493c and its parent are not in this checkout: the replay is not run')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
