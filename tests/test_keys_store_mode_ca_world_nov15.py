#!/usr/bin/env python3
"""Canada + world keys in store mode (KPC owner, 2026-11-15; repo variable KPC_KEY_SOURCE=store).

1. Canada: a hard look is a live read (one named record, not in the saved copy). In store mode the build step moves
   data/ca-key/hardlook-joins.json aside before kpc_ca_key.py and puts it back right after (kpc_ca_store_keep.py aside / back) (so the key opens no connection);
   the next step (kpc_ca_store_keep.py keep) gives a park main joined through a hard look its entry back; after the join check
   kpc_ca_store_keep.py todo lists a hard-look park that is still a pin in held-parks-todo.csv (todo_kind store_hard_look).
2. World: the plan leaves out (plain line, not failed, not a full build) a country with no saved copy or whose saved copy lacks a
   source (data/outlines/world-store-gaps.json, kpc_world_store_gaps.py); the build job checks the copies it really downloaded again.
3. data/outlines/world-store-gaps.json is well formed and small; both new scripts are in NOT_RULES and in no RULE_FILES; their self
   tests pass; the gap check opens no connection under KPC_KEY_OFFLINE=1.
Offline, temp folders only."""
import gzip, json, os, pathlib, re, subprocess, sys, tempfile, textwrap

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
sys.path.insert(0, str(SC))
import kpc_key_freeze as KZ  # noqa: E402

# ---------------------------------------------------------------- 3. scripts: NOT_RULES, self tests
NEW = ('kpc_ca_store_keep.py', 'kpc_world_store_gaps.py')
check('kpc_ca_store_keep.py and kpc_world_store_gaps.py are in NOT_RULES and in no RULE_FILES',
      set(NEW) <= KZ.NOT_RULES and not any(os.path.basename(f) in NEW for fs in KZ.RULE_FILES.values() for f in fs))
for s in NEW:
    r = subprocess.run([sys.executable, str(SC / s), '--selftest'], cwd=ROOT, capture_output=True, text=True)
    check(f'{s} --selftest passes', r.returncode == 0 and 'SELFTEST PASS' in r.stdout)

# ---------------------------------------------------------------- 1. the Canada workflow
ca = yaml.safe_load((WF / 'kpc-ca-key.yml').read_text())
steps = ca['jobs']['run']['steps']
names = [str(st.get('name', st.get('id', ''))) for st in steps]
def at(prefix): return next(i for i, n in enumerate(names) if n.startswith(prefix))
b = at('Build the Canada answer key'); run = steps[b]['run']
i_aside, i_key, i_back = run.index('kpc_ca_store_keep.py aside'), run.index('python3 .github/scripts/kpc_ca_key.py >'), run.index('kpc_ca_store_keep.py back')
check('Canada build: the hard-look file goes aside before the key and comes back right after it', i_aside < i_key < i_back)
mine = [l for l in run.split('\n') if 'kpc_ca_store_keep.py' in l]
check('Canada build: aside / back run only in store mode (GEO_CACHE_MODE=only) and the lines are marked store-only',
      len(mine) == 2 and all(l.strip().startswith('if [ "$GEO_CACHE_MODE" = only ]') and l.rstrip().endswith('# KPC_KEY_SOURCE=store only') for l in mine))
check('Canada build: the key line itself is unchanged (no store-mode edit inside it)',
      'python3 .github/scripts/kpc_ca_key.py > ca-key.log 2>&1 || { touch /tmp/ca-key-stopped;' in next(l for l in run.split('\n') if 'kpc_ca_key.py >' in l).strip()[:90])
k, t = at('Store mode (KPC owner, 2026-11-15) - a hard-look join on main is kept'), at("Store mode (KPC owner, 2026-11-15) - a hard-look park that is still a pin")
check('Canada: the keep step is store-only and runs after the build, before the why-not tags and the join check',
      STORE_ONLY in str(steps[k].get('if')) and 'kpc_ca_store_keep.py keep' in steps[k]['run'] and b < k < at('Why-not tags') < at('Join check'))
check('Canada: the to-do step is store-only and runs after the join check and the review rows, before never worse',
      STORE_ONLY in str(steps[t].get('if')) and 'kpc_ca_store_keep.py todo' in steps[t]['run'] and at('Join check') < steps.index(next(s for s in steps if s.get('id') == 'keep_rows')) < t < at('Store mode (KPC owner, 2026-11-15) - never worse'))
check('Canada: a failed keep holds the whole key (the stopped flag), never saves a half-kept key', 'touch /tmp/ca-key-stopped' in steps[k]['run'])

# ---------------------------------------------------------------- 2. the world workflow
wd = yaml.safe_load((WF / 'kpc-world-key.yml').read_text())
plan = wd['jobs']['plan']
sp = [st for st in plan['steps'] if st.get('id') == 'store_plan']
check('world plan: one store-only store_plan step, after the split', len(sp) == 1 and STORE_ONLY in str(sp[0].get('if')) and plan['steps'].index(sp[0]) > [s.get('id') for s in plan['steps']].index('p'))
check("world plan outputs: groups and full come from store_plan when it ran",
      plan['outputs']['groups'] == '${{ steps.store_plan.outputs.groups || steps.p.outputs.groups }}' and plan['outputs']['full'] == '${{ steps.store_plan.outputs.full || steps.p.outputs.full }}')
code = re.search(r"python3 - <<'PY'\n(.*?)\n\s*PY", sp[0]['run'], re.S).group(1)
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td); (td / 'out').write_text('')
    groups = [{'i': 0, 'countries': 'GB FR VI', 'cmin': ''}, {'i': 1, 'countries': 'AU', 'cmin': '300'}]
    r = subprocess.run([sys.executable, '-c', textwrap.dedent(code)], capture_output=True, text=True,
                       env=dict(os.environ, GITHUB_OUTPUT=str(td / 'out'), GROUPS=json.dumps(groups), KEEP='GB VI'))
    out = (td / 'out').read_text().split('\n')
    check(f'world plan, store mode: only the countries kept stay planned, an emptied job goes, full=0 ({out[:2]})',
          r.returncode == 0 and out[0] == 'groups=' + json.dumps([{'i': 0, 'countries': 'GB VI', 'cmin': ''}]) and 'full=0' in out)
    (td / 'assets.txt').write_text('W-GB.json.gz\nW-FR.json.gz\nW-AU.json.gz\n')
    (td / 'gaps.json').write_text(json.dumps({'countries': {'FR': {'missing': [{'label': 'Some layer'}]}, 'GB': {'missing': []}}}))
    r = subprocess.run([sys.executable, str(SC / 'kpc_world_store_gaps.py'), 'plan', '--assets', str(td / 'assets.txt'), '--gaps', str(td / 'gaps.json'), 'GB', 'FR', 'VI', 'AU'],
                       cwd=ROOT, capture_output=True, text=True)
    check(f'gap plan: GB AU built, FR (a gap) and VI (no copy) left out with one plain line each ({r.stdout.strip()})',
          r.stdout.split() == ['GB', 'AU'] and 'World key FR: the saved copy has no record' in r.stderr and 'World key VI: no saved copy' in r.stderr and '::error' not in r.stderr)
    # the build-job check, offline: the key's own sources, a made-up GB copy with one source only
    import kpc_world_store_gaps as G
    gb = G.sources(str(ROOT))['GB']
    (td / 'cw').mkdir()
    with gzip.open(td / 'cw/W-GB.json.gz', 'wt') as f: json.dump({'saved': '2026-11-15', 'recs': [{'sid': G.src_id(gb[0])}]}, f)
    env = dict(os.environ, KPC_KEY_OFFLINE='1', KPC_OFFLINE_LOG=str(td / 'refused.txt'))
    r = subprocess.run([sys.executable, str(SC / 'kpc_world_store_gaps.py'), 'check', '--cache', str(td / 'cw'), '--out', str(td / 'gaps.txt'), 'GB', 'JP'],
                       cwd=ROOT, capture_output=True, text=True, env=env)
    check(f'gap check (KPC_KEY_OFFLINE=1): GB (one source of {len(gb)}) and JP (no copy) are listed, no connection tried (exit {r.returncode})',
          r.returncode == 0 and (td / 'gaps.txt').read_text().split() == ['GB', 'JP'] and not (td / 'refused.txt').exists())
bstep = next(st for st in wd['jobs']['build']['steps'] if str(st.get('name', '')).startswith('Build (this job'))
lines = [l for l in bstep['run'].split('\n') if 'store-gaps' in l]
check('world build: the copy check runs only in store mode, before the country loop, marked store-only, fails closed',
      lines and all(l.rstrip().endswith('# KPC_KEY_SOURCE=store only') for l in lines) and all('"${GEO_CACHE_MODE:-}" = only' in l for l in lines if l.strip().startswith('if '))
      and bstep['run'].index('kpc_world_store_gaps.py check') < bstep['run'].index('for c in $BUILD; do') and "|| printf '%s\\n' $BUILD" in bstep['run'])

# ---------------------------------------------------------------- 3. the keeper's gaps file
p = ROOT / 'data/outlines/world-store-gaps.json'
g = json.loads(p.read_text(encoding='utf-8'))
cs = g.get('countries') or {}
check(f'store-gaps.json: under 1 MB ({p.stat().st_size} bytes), every country has copy / missing fields', p.stat().st_size < 1_000_000 and cs and all({'copy', 'missing'} <= set(v) for v in cs.values()))
check('store-gaps.json: the gaps list = the countries with a missing source', sorted(g.get('gaps') or []) == sorted(c for c, v in cs.items() if v['missing']))
check('store-gaps.json: a country with no saved copy lists every one of its sources as missing', all(v['missing'] or not v['sources'] for v in cs.values() if v['copy'] is None))

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
