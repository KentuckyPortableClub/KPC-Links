#!/usr/bin/env python3
"""Keys in store mode (KPC owner, 2026-11-15): with the repo variable KPC_KEY_SOURCE=store a key run only keeps joins, offline.

1. The three key workflows: every step that reads a live map, builds or uploads outlines, copies to KPC-Archive or starts another
   workflow carries `vars.KPC_KEY_SOURCE != 'store'`; nothing that can run in store mode does any of those; the drop guard, the join
   check, the review files and the save still run; every step that runs a key script sets KPC_KEY_OFFLINE=1 (kpc_key_offline.py,
   installed by kpc_host_pace) and GEO_CACHE_MODE=only in store mode; the US plan leaves out a state with no saved copy. With the variable unset the workflows are what they were (checked against 838fee6 while this change is the
   only edit since; later edits make that part a plain note).
2. kpc_us_key.py on a small made-up state, store mode (KPC_KEY_OFFLINE=1 + GEO_CACHE_MODE=only, as the workflow runs it): no connection refused (zero tried),
   joins identical to a normal offline run (GEO_CACHE_MODE=use, KPC_MASTER_OWNS=1, sockets off) on the same saved copy; a new park
   with no record stays pin only; a state with no saved copy is skipped with a plain line and its key file is left byte for byte.
3. Never worse: the drop guard as the store-mode step calls it (KPC_DROP_PCT=0, KPC_DROP_MIN=0) keeps a state that lost ONE official
   park from main; the default limit (3%) lets that through.
4. The to-do lists: a far join in a store-mode key is held by the join check and written to held-parks-todo.csv; the new-park list
   data/new-refs/keeper-list.csv is the new-refs bot's (kpc_new_refs.py), not written by a key run.
Offline, temp folders only."""
import gzip, json, os, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
WF = ROOT / '.github/workflows'
SC = ROOT / '.github/scripts'
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


try:
    import yaml
except ImportError:
    print('SKIP pyyaml is not installed'); sys.exit(0)

STORE_ONLY = "vars.KPC_KEY_SOURCE == 'store'"
NOT_STORE = "vars.KPC_KEY_SOURCE != 'store'"
# what a store-mode run must never do (a step / job that does it must carry NOT_STORE)
FORBIDDEN = {'starts a workflow': re.compile(r'gh workflow run'), 'uploads a release asset': re.compile(r'gh release upload'),
             'copies to KPC-Archive': re.compile(r'kpc_archive\.sh'), 'builds outlines from the key': re.compile(r'kpc_outlines_from_key\.py'),
             'master fill / collect / watch': re.compile(r'kpc_master_cli\.py (fill|collect|watch)\b'),
             'outline fill (Canada)': re.compile(r'kpc_ca_fill_bounds\.py'), 'pushes the world-bounds branch': re.compile(r'git push[^\n]*world-bounds')}
KEYS = {'kpc-us-key.yml': 'kpc_us_key.py', 'kpc-ca-key.yml': 'kpc_ca_key.py', 'kpc-world-key.yml': 'kpc_world_key.py'}
MUST_SKIP = {'kpc-us-key.yml': ['id:master_fill', "name:Save this job's new live reads", 'id:kept_green_master_collect', 'name:Outlines from the key',
                                'job:postcheck', 'job:chain'],
             'kpc-ca-key.yml': ['name:Keep the saved copy current', 'name:Save outline files for joined parks', 'job:chain', 'job:postcheck'],
             'kpc-world-key.yml': ['name:Saved outlines to the branch world-bounds', 'job:postcheck']}
MUST_RUN = {'kpc-us-key.yml': ['name:Drop guard', 'name:Join check', 'id:keep_rows', 'eq:Save', 'name:BUILD STAMP', 'name:Build the answer key'],
            'kpc-ca-key.yml': ['name:Join check', 'id:keep_rows', 'eq:Save', 'name:Build the Canada answer key'],
            'kpc-world-key.yml': ['name:Join check', 'id:keep_rows', 'eq:Save', 'name:Build (this job']}


def cond_of(x): return str(x.get('if', '')) if isinstance(x, dict) else ''


def text_of(step):
    return '\n'.join(str(v) for k, v in step.items() if k in ('run', 'with')) if isinstance(step, dict) else ''


def find(doc, sel):
    kind, val = sel.split(':', 1)
    if kind == 'job': return [(val, doc['jobs'].get(val))] if val in doc['jobs'] else []
    out = []
    for jn, job in doc['jobs'].items():
        for st in job.get('steps') or []:
            if (kind == 'id' and st.get('id') == val) or (kind == 'name' and str(st.get('name', '')).startswith(val)) or (kind == 'eq' and st.get('name') == val): out.append((f'{jn}/{st.get("name") or st.get("id")}', st))
    return out


def unset(s):
    """The text as GitHub runs it with KPC_KEY_SOURCE unset (the store-mode additions read out)."""
    s = re.sub(r"\$\{\{ steps\.store_plan\.outputs\.(\w+) \|\| (steps\.p\.outputs\.\1) \}\}", r'${{ \2 }}', s)   # groups (US, world), full (world)
    def one(m):
        v = m.group(1)
        return '${{ ' + (v[1:-1] if v.startswith('(') and v.endswith(')') else v) + ' }}'
    s = re.sub(r"\$\{\{ vars\.KPC_KEY_SOURCE == 'store' && '[^']*' \|\| (.*?) \}\}", one, s)
    s = re.sub(r"\$\{\{ \((.*)\) && vars\.KPC_KEY_SOURCE != 'store' \}\}", r'${{ \1 }}', s)
    s = s.replace(' || [ "$GEO_CACHE_MODE" = only ]', '')
    return s


def strip_added(doc):
    """Drop the store-only steps, the store-only env keys and the marked store-only lines; then compare with the old file."""
    for job in doc['jobs'].values():
        for x in [job] + list(job.get('steps') or []):
            if str(x.get('if', '')).strip() == "${{ vars.KPC_KEY_SOURCE != 'store' }}": x.pop('if')
        job['steps'] = [st for st in job.get('steps') or [] if STORE_ONLY not in cond_of(st) or NOT_STORE in cond_of(st)]
        for st in job['steps']:
            env = st.get('env') or {}
            for k in [k for k, v in env.items() if re.fullmatch(r"\$\{\{ (\(?)'?'?\)?\s*\}\}", str(v)) or str(v) == "${{ '' }}"]: env.pop(k)
            if 'env' in st and not st['env']: st.pop('env')
            if isinstance(st.get('run'), str) and '# KPC_KEY_SOURCE=store only' in st['run']:
                st['run'] = '\n'.join(l for l in st['run'].split('\n') if not l.rstrip().endswith('# KPC_KEY_SOURCE=store only'))
    return doc


def norm_if(doc):
    for job in doc['jobs'].values():
        for x in [job] + list(job.get('steps') or []):
            if 'if' in x:
                v = str(x['if']).strip()
                v = v[3:-2].strip() if v.startswith('${{') and v.endswith('}}') else v
                x['if'] = v
    return doc


for wf, script in KEYS.items():
    raw = (WF / wf).read_text()
    doc = yaml.safe_load(raw)
    # (a) every KPC_KEY_SOURCE use is one of the three shapes
    for m in re.finditer(r'.*KPC_KEY_SOURCE.*', raw):
        line = m.group(0)
        good = (re.search(r"if: \$\{\{ \(.*\) && vars\.KPC_KEY_SOURCE != 'store' \}\}", line) or re.search(r"if: \$\{\{ vars\.KPC_KEY_SOURCE != 'store' \}\}", line)
                or re.search(r"if: \$\{\{ .*vars\.KPC_KEY_SOURCE == 'store'.*\}\}", line) or re.search(r": \$\{\{ vars\.KPC_KEY_SOURCE == 'store' && '[^']*' \|\| ", line)
                or line.lstrip().startswith('#') or 'KPC_KEY_SOURCE=store' in line)
        if not good: check(f'{wf}: KPC_KEY_SOURCE used in an unknown way: {line.strip()[:120]}', False)
    # (b) the steps / jobs that must be skipped carry the condition
    for sel in MUST_SKIP[wf]:
        hits = find(doc, sel)
        check(f"{wf}: {sel} is skipped in store mode ({len(hits)} found)", hits and all(NOT_STORE in cond_of(x) for _, x in hits))
    for sel in MUST_RUN[wf]:
        hits = find(doc, sel)
        check(f"{wf}: {sel} still runs in store mode", hits and all(NOT_STORE not in cond_of(x) for _, x in hits))
    # (c) nothing a store-mode run reaches does a forbidden thing
    bad = []
    for jn, job in doc['jobs'].items():
        if NOT_STORE in cond_of(job): continue
        for st in job.get('steps') or []:
            if NOT_STORE in cond_of(st): continue
            for what, rx in FORBIDDEN.items():
                if rx.search(text_of(st)): bad.append(f'{jn}/{st.get("name", st.get("id"))[:60]}: {what}')
    check(f'{wf}: no step that runs in store mode starts a workflow, uploads, archives, fills / collects / watches or builds outlines {bad[:3]}', not bad)
    # (d) every call of the key script goes through the no-network runner; store mode = GEO_CACHE_MODE only
    steps_calling = [st for job in doc['jobs'].values() for st in job.get('steps') or [] if script in str(st.get('run', ''))]
    check(f'{wf}: each step that calls {script} sets KPC_KEY_OFFLINE=1 in store mode ({len(steps_calling)} steps; the key imports kpc_host_pace, which installs the guard)',
          steps_calling and all(str((st.get('env') or {}).get('KPC_KEY_OFFLINE')) == "${{ vars.KPC_KEY_SOURCE == 'store' && '1' || '' }}" for st in steps_calling))
    geo = [str((st.get('env') or {}).get('GEO_CACHE_MODE')) for st in steps_calling if (st.get('env') or {}).get('GEO_CACHE_MODE')]
    check(f'{wf}: the build step sets GEO_CACHE_MODE=only in store mode', geo and all(g.startswith("${{ vars.KPC_KEY_SOURCE == 'store' && 'only' ||") for g in geo))
    # (e) unset = as today (838fee6), while this change is the only edit to the file since
    r = subprocess.run(['git', 'log', '--format=%s', '838fee6..HEAD', '--', f'.github/workflows/{wf}'], cwd=ROOT, capture_output=True, text=True)
    old = subprocess.run(['git', 'show', f'838fee6:.github/workflows/{wf}'], cwd=ROOT, capture_output=True, text=True)
    edits = sum(1 for x in r.stdout.splitlines() if 'store mode' not in x.lower()) + 1   # edits since 838fee6 that are not this change (+1 = this change)
    if r.returncode != 0 or old.returncode != 0:
        print(f'note {wf}: 838fee6 is not in this clone; the unset-equals-before check is left out')
    elif edits > 1:
        print(f'note {wf}: edited by {edits - 1} other change(s) since 838fee6; the unset-equals-before check was made at the store-mode change')
    else:
        a = norm_if(yaml.safe_load(old.stdout)); b = norm_if(strip_added(yaml.safe_load(unset(raw))))
        same = a == b
        if not same:
            for jn in a['jobs']:
                sa, sb = a['jobs'][jn].get('steps') or [], (b['jobs'].get(jn) or {}).get('steps') or []
                for i, (x, y) in enumerate(zip(sa, sb)):
                    if x != y: print(f'  first difference: {wf} {jn} step {i} {x.get("name", "")[:60]}: {sorted(k for k in set(x) | set(y) if x.get(k) != y.get(k))}'); break
                if len(sa) != len(sb): print(f'  {wf} {jn}: {len(sa)} steps before, {len(sb)} now')
                if {k: v for k, v in a['jobs'][jn].items() if k != 'steps'} != {k: v for k, v in (b['jobs'].get(jn) or {}).items() if k != 'steps'}: print(f'  {wf} job {jn} differs')
        check(f'{wf}: with KPC_KEY_SOURCE unset the workflow is exactly the 838fee6 workflow (only guarded additions)', same)

# the US plan's store-mode step, run for real: a state with no saved copy leaves the plan with a plain line; an emptied group goes
uswf0 = yaml.safe_load((WF / 'kpc-us-key.yml').read_text())
sp = [st for st in uswf0['jobs']['plan']['steps'] if st.get('id') == 'store_plan'][0]
code = re.search(r"python3 - <<'PY'\n(.*?)\n\s*PY", sp['run'], re.S).group(1)
import textwrap
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); (t / 'store-assets.txt').write_text('US-RI.json.gz\nUS-DE.json.gz\nhand-US-RI.geojson.gz\n'); (t / 'out').write_text('')
    groups = [{'i': 0, 'states': 'DE RI VT'}, {'i': 1, 'states': 'WY'}]
    r = subprocess.run([sys.executable, '-c', textwrap.dedent(code)], capture_output=True, text=True,
                       env=dict(os.environ, RUNNER_TEMP=str(t), GITHUB_OUTPUT=str(t / 'out'), GROUPS=json.dumps(groups)))
    out = (t / 'out').read_text()
    check(f"US plan, store mode: only states with a saved copy stay planned ({out.strip()})", r.returncode == 0 and out.strip() == 'groups=' + json.dumps([{'i': 0, 'states': 'DE RI'}]))
    check('US plan, store mode: each left-out state gets one plain line (no ::error)', 'US key VT: no saved copy' in r.stderr and 'US key WY: no saved copy' in r.stderr and '::error' not in r.stderr)
check("the plan's groups output is the store-mode list when there is one, else the normal one", uswf0['jobs']['plan']['outputs']['groups'] == '${{ steps.store_plan.outputs.groups || steps.p.outputs.groups }}')

# ---------------------------------------------------------------- 2. the US key on a made-up state
KEY = SC / 'kpc_us_key.py'
CHILD = r'''
import runpy, socket, sys
def _off(*a, **k): raise OSError('network disabled in this test')
socket.socket.connect = _off; socket.create_connection = _off; socket.getaddrinfo = _off
key = sys.argv[1]; sys.argv = [key]
runpy.run_path(key, run_name='__main__')
'''


def sq(la, lo, d): return [[[lo - d, la - d], [lo + d, la - d], [lo + d, la + d], [lo - d, la + d], [lo - d, la - d]]]


def rec(oid, name, ac, la, lo, d, own, label, k):
    return {'OBJECTID': oid, 'Unit_Nm': name, 'Loc_Nm': '', 'Own_Type': own, 'Mang_Type': own, 'Mang_Name': 'STAT', 'Loc_Mang': label,
            'Des_Tp': '', 'GIS_Acres': ac, 'Category': 'Fee', '_r': sq(la, lo, d), '_k': k}


P = {'US-99101': ['Example Pond State Park', '', 'State Park', '', '', 41.60, -71.50, 0, 0, 0],
     'US-99102': ['Sample Ridge State Forest', '', 'State Forest', '', '', 41.75, -71.65, 0, 0, 0],
     'US-99103': ['Brand New Meadow State Park', '', 'State Park', '', '', 41.45, -71.40, 0, 0, 0],      # a new park: no record anywhere
     'US-99104': ['Faraway Marsh Wildlife Management Area', '', 'Wildlife Management Area', '', '', 41.90, -71.30, 0, 0, 0]}
RECS = [rec('sgrix1', 'Example Pond State Park', 300, 41.60, -71.50, .01, 'STAT', 'Example state parks (state GIS table)', ['sp']),
        rec('sgrix2', 'Sample Ridge State Forest', 2500, 41.75, -71.65, .03, 'STAT', 'Example state forests (state GIS table)', ['sf']),
        rec('sgrix3', 'Faraway Marsh Wildlife Management Area', 800, 41.62, -71.30, .01, 'STAT', 'Example wildlife areas', ['wma'])]   # ~31 km from its pin


def build(store, with_copy=True, keep_file=None):
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        for d in ('data/parkinfo', 'data/us-key', 'cache/us'): (t / d).mkdir(parents=True)
        (t / 'data/us-key/overrides.json').write_text(json.dumps({'parks': {}}))
        (t / 'data/parkinfo/US-RI.json').write_text(json.dumps({'parks': P, 'state': 'RI'}))
        if keep_file is not None: (t / 'data/us-key/US-RI.json').write_bytes(keep_file)
        if with_copy:
            with gzip.open(t / 'cache/us/US-RI.json.gz', 'wt', encoding='utf-8') as f: json.dump({'recs': RECS, 'seen': len(RECS), 'detail': 0.001}, f)
        env = {k: v for k, v in os.environ.items() if not k.startswith(('KPC_', 'GEO_', 'STATES'))}
        env.update(STATES='RI', GEO_DETAIL='0.001', no_proxy='*', HTTPS_PROXY='', HTTP_PROXY='', https_proxy='', http_proxy='', KPC_MASTER_OWNS='1',
                   KPC_OFFLINE_LOG=str(t / 'refused.txt'))
        if store: cmd, env['GEO_CACHE_MODE'], env['KPC_KEY_OFFLINE'] = [sys.executable, str(KEY)], 'only', '1'
        else: cmd, env['GEO_CACHE_MODE'] = [sys.executable, '-c', CHILD, str(KEY)], 'use'
        r = subprocess.run(cmd, cwd=t, capture_output=True, text=True, timeout=600, env=env)
        f = t / 'data/us-key/US-RI.json'
        doc = json.loads(f.read_text()) if f.exists() else None
        raw = f.read_bytes() if f.exists() else None
        refused = (t / 'refused.txt').read_text().splitlines() if (t / 'refused.txt').exists() else []
        held = None
        if doc is not None and store:   # 4. the join check on the store-mode key: the far join is held and goes on the keeper's to-do
            sys.path.insert(0, str(SC))
            jr = subprocess.run([sys.executable, str(SC / 'kpc_join_check.py')], cwd=t, capture_output=True, text=True, timeout=300,
                                env=dict(env, KEY='us', ANSWER_SHEET=str(t / 'no-answer-sheet')))
            todo = t / 'data/us-key/review/held-parks-todo.csv'
            held = (jr.returncode, todo.read_text() if todo.exists() else '')
        return r, doc, raw, refused, held


def joins(doc): return {k: sorted(str(x[0]) for x in p.get('m') or []) for k, p in ((doc or {}).get('parks') or {}).items()}


r_s, doc_s, raw_s, refused, held = build(True)
r_n, doc_n, _, _, _ = build(False)
if doc_s is None or doc_n is None: print(r_s.stdout[-2000:], r_s.stderr[-2000:], r_n.stdout[-1500:], r_n.stderr[-1500:])
check(f'store mode: the key ran (exit {r_s.returncode}) and wrote US-RI.json', r_s.returncode == 0 and doc_s is not None)
check(f'store mode: zero connections tried (refused log: {refused[:3]})', refused == [] and 'refused' not in r_s.stderr)
check('store mode: the saved copy was read (mode only, loaded 1 (RI), saved 0)', 'mode only' in r_s.stdout and 'loaded 1 (RI)' in r_s.stdout and 'saved 0 ()' in r_s.stdout)
check(f'joins identical to the normal offline run on the same saved copy ({joins(doc_s)})', doc_n is not None and joins(doc_s) == joins(doc_n) and joins(doc_s))
check('grades identical to the normal offline run', {k: p.get('g') for k, p in doc_s['parks'].items()} == {k: p.get('g') for k, p in doc_n['parks'].items()})
check("the two joined parks are joined to their own record", joins(doc_s).get('US-99101') == ['sgrix1'] and joins(doc_s).get('US-99102') == ['sgrix2'])
np_ = doc_s['parks'].get('US-99103') or {}
check(f"a new park with no record stays pin only (g={np_.get('g')}, m={np_.get('m')})", np_ and np_.get('g') == 'pin' and not np_.get('m'))
rc, todo = held
check(f'the join check on the store-mode key holds the far join and writes it to held-parks-todo.csv (exit {rc})', rc == 0 and 'US-99104' in todo and 'join_held' in todo)
check('the new park is not a held join (nothing to hold; it waits on the new-park list)', 'US-99103' not in todo)
OLD_KEY = json.dumps({'parks': {'US-99101': {'n': 'Example Pond State Park', 'g': 'official', 'm': [['sgrix1', 'x', 300, 'name']]}}}).encode()
r_x, doc_x, raw_x, refused_x, _ = build(True, with_copy=False, keep_file=OLD_KEY)
check(f'no saved copy: skipped with a plain line (exit {r_x.returncode})', r_x.returncode == 0 and 'no saved shapes yet; skipped' in r_x.stdout and refused_x == [])
check('no saved copy: the parks and joins of the key file are left as they are (never emptied; only the all-state totals are refreshed, as in every run)',
      doc_x is not None and doc_x.get('parks') == json.loads(OLD_KEY)['parks'])
import importlib.util
spec = importlib.util.spec_from_file_location('nr_src', SC / 'kpc_new_refs.py')
src = (SC / 'kpc_new_refs.py').read_text()
check("the new-park list is the new-refs bot's: kpc_new_refs.py writes data/new-refs/keeper-list.csv", "KEEPER = pathlib.Path('data/new-refs/keeper-list.csv')" in src)
check('a key script never writes the keeper list', all('keeper-list' not in (SC / s).read_text() for s in KEYS.values()))

# ---------------------------------------------------------------- 3. never worse: the drop guard in store mode
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    g = lambda *x: subprocess.run(['git', *x], cwd=t, capture_output=True, text=True, check=True)
    g('init', '-q'); g('config', 'user.email', 't@example.invalid'); g('config', 'user.name', 't')
    (t / 'data/us-key').mkdir(parents=True)
    parks = {f'US-9{i:04d}': {'g': 'official', 'm': [[i, 'x', 1, 'name']]} for i in range(50)}
    (t / 'data/us-key/US-ZZ.json').write_text(json.dumps({'parks': parks}))
    (t / 'data/us-key/index.json').write_text(json.dumps({'states': {'ZZ': {'parks': 50}}}))
    g('add', '-A'); g('commit', '-qm', 'main')
    worse = dict(parks); worse['US-90007'] = {'g': 'pin', 'm': []}
    new = json.dumps({'parks': worse}); (t / 'data/us-key/US-ZZ.json').write_text(new)
    env = {k: v for k, v in os.environ.items() if not k.startswith('KPC_DROP')}

    def guard(**e):
        fo = t / 'failed.txt'; fo.unlink(missing_ok=True)
        r = subprocess.run([sys.executable, str(SC / 'kpc_key_drop_guard.py'), '--repo', str(t), '--ref', 'HEAD', '--restore', '--failed-out', str(fo)],
                           capture_output=True, text=True, env=dict(env, **e), timeout=120, cwd=t)   # cwd = the temp repo: its status file lands there
        return r, (fo.read_text().split() if fo.exists() else [])
    r, failed = guard(KPC_DROP_PCT='', KPC_DROP_MIN='')   # the variable unset: the step passes '' = today's 3% / 1 park
    check(f'default drop guard: 1 of 50 official parks lost (2%) is let through (failed {failed})', r.returncode == 0 and failed == [] and (t / 'data/us-key/US-ZZ.json').read_text() == new)
    r, failed = guard(KPC_DROP_PCT='0', KPC_DROP_MIN='0')   # store mode
    check(f'store-mode drop guard: the same ONE lost park keeps the state from main (failed {failed})', r.returncode == 0 and failed == ['ZZ'])
    check('store-mode drop guard: the key file is main\'s again byte for byte', (t / 'data/us-key/US-ZZ.json').read_text() == json.dumps({'parks': parks}))
    (t / 'data/us-key/US-ZZ.json').write_text(json.dumps({'parks': parks}))
    r, failed = guard(KPC_DROP_PCT='0', KPC_DROP_MIN='0')
    check('store-mode drop guard: an unchanged state passes', r.returncode == 0 and failed == [])
uswf = yaml.safe_load((WF / 'kpc-us-key.yml').read_text())
dg = find(uswf, 'name:Drop guard')[0][1]
check("the US drop guard step passes KPC_DROP_PCT=0 and KPC_DROP_MIN=0 in store mode ('' otherwise)",
      all(str(dg['env'].get(k)) == "${{ vars.KPC_KEY_SOURCE == 'store' && '0' || '' }}" for k in ('KPC_DROP_PCT', 'KPC_DROP_MIN')))

# the two new scripts are not rule files (no key hash moves) and are in NOT_RULES
sys.path.insert(0, str(SC)); import kpc_key_freeze as KZ  # noqa: E402
check('kpc_key_offline.py and kpc_key_never_worse.py are in NOT_RULES and in no RULE_FILES',
      {'kpc_key_offline.py', 'kpc_key_never_worse.py'} <= KZ.NOT_RULES and not any(os.path.basename(f) in ('kpc_key_offline.py', 'kpc_key_never_worse.py') for fs in KZ.RULE_FILES.values() for f in fs))

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
