#!/usr/bin/env python3
"""Offline test (R-LR2 ruled 'full', KPC owner, 2026-11-17): a layer that looks like it is going away gets ONE full-detail save before
it dies. Before this, a dying-layer request with KPC_LR_DYING=full was only held and listed, never saved.

Checked on made-up copies in temp folders, a fake `gh` (a fake release folder) and a fake key script that writes what the real one
would (no network):
  1. the planner sends a dying area to the full-detail save (full=[...]) and NOT to the normal ~110 m re-read; once the release
     has full-<area>.json.gz, or when the asset list was not read, it is held (one save only);
  2. kpc_layer_full_save.sh runs the old key script at full detail into its own folder and uploads full-<area>.json.gz, with the
     ~110 m copy untouched; a second run uploads nothing; a full read with fewer records is refused by save-check (nothing uploaded);
  3. both cache workflows carry the full_save job: only when the planner names an area, by hand only, from_requests off by default,
     the knob default 'full', no --clobber on the full upload."""
import gzip, json, os, pathlib, shutil, stat, subprocess, sys, tempfile
import yaml

HERE = pathlib.Path(__file__).resolve().parent.parent
PLAN = HERE / '.github/scripts/kpc_layer_refresh.py'
SAVE = HERE / '.github/scripts/kpc_layer_full_save.sh'
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


sys.path.insert(0, str(PLAN.parent))
import kpc_layer_refresh as LR  # noqa: E402

ALL_US = 'AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split()
RULED = {'KPC_LR_STALE_DAYS': '180', 'KPC_LR_DYING': 'full', 'KPC_LR_CHANGED_READ': 'whole', 'KPC_LR_WHO': 'keeper+hand'}
DYING = {'format': 1, 'requests': [{'layer': 'sha256:00aa11bb22cc33dd', 'area': 'US-TN', 'moved': ['retiring'], 'date': '2026-11-17', 'by': 'keeper'},
                                   {'layer': 'sha256:00aa11bb22cc33ee', 'area': 'US-OH', 'moved': ['etag'], 'date': '2026-11-17', 'by': 'keeper'},
                                   {'layer': 'sha256:00aa11bb22cc33ff', 'area': 'W-JP', 'moved': ['gone'], 'date': '2026-11-17', 'by': 'chat'},
                                   {'layer': 'sha256:00aa11bb22cc3300', 'area': 'CA-BC', 'moved': ['etag'], 'date': '2026-11-17', 'by': 'keeper', 'dying': True}]}
NOW = {'US-TN.json.gz': '2026-11-10', 'US-OH.json.gz': '2026-11-10', 'W-JP.json.gz': '2026-11-10', 'CA-ALL.json.gz': '2026-11-10'}

# --- 1. the planner
rc = LR.plan(DYING, 'found', 'us', known=ALL_US, asset_dates=NOW, env=RULED)
check(rc.get('full_save') == ['TN'], f"R-LR2 full: the dying US area goes to the full-detail save ({rc.get('full_save')})")
check(rc['fetch'] == ['OH'], f"and not to the normal re-read; the changed area still is ({rc['fetch']})")
rw = LR.plan(DYING, 'found', 'world', asset_dates=NOW, env=RULED)
check(rw.get('full_save') == ['CA', 'JP'], f"world: a dying country and a dying Canada row go to the full-detail save ({rw.get('full_save')})")
done = LR.plan(DYING, 'found', 'us', known=ALL_US, asset_dates=dict(NOW, **{'full-US-TN.json.gz': '2026-11-16'}), env=RULED)
check(done.get('full_save') == [] and any('already on the release' in k for k in done['held']), 'one save only: an area that already has full-<area>.json.gz is held')
blind = LR.plan(DYING, 'found', 'us', known=ALL_US, asset_dates=None, env=RULED)
check(blind.get('full_save') == [] and any('asset list was not read' in k for k in blind['held']), 'the asset list was not read: held (fail closed)')
check(LR.plan(DYING, 'found', 'us', known=ALL_US, asset_dates=NOW, env=dict(RULED, KPC_LR_DYING=''))['full_save'] == [], 'R-LR2 empty: no full-detail save')
check('R-LR2 one full-detail save' in LR.summary_md(rc) and 'US-TN' in LR.summary_md(rc), 'the receipt names the full-detail save')
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); (t / 'req.json').write_text(json.dumps(DYING)); (t / 'dates.json').write_text(json.dumps([{'name': k, 'updatedAt': v} for k, v in NOW.items()]))
    env = dict(os.environ, **RULED)
    r = subprocess.run([sys.executable, str(PLAN), 'plan', '--job', 'us', '--requests', str(t / 'req.json'), '--known', ' '.join(ALL_US), '--asset-dates', str(t / 'dates.json')], capture_output=True, text=True, env=env)
    out = dict(x.split('=', 1) for x in r.stdout.splitlines() if '=' in x)
    check(json.loads(out.get('full', 'null') or 'null') == ['TN'] and json.loads(out.get('groups', 'null')) == ['OH'], f'the planner prints full=[...] for $GITHUB_OUTPUT ({r.stdout.strip()})')

# --- 2. the full-detail save itself
FAKE_GH = r'''#!/usr/bin/env python3
import os, shutil, sys
a = sys.argv[1:]; rel = os.environ['FAKE_REL']; open(os.environ['FAKE_LOG'], 'a').write(' '.join(a) + '\n')
if a[:2] == ['release', 'view']:
    print('\n'.join(sorted(os.listdir(rel)))); sys.exit(0)
if a[:2] == ['release', 'download']:
    p = a[a.index('-p') + 1]; d = a[a.index('-D') + 1]
    if not os.path.exists(os.path.join(rel, p)): sys.exit(1)
    shutil.copy(os.path.join(rel, p), os.path.join(d, p)); sys.exit(0)
if a[:2] == ['release', 'upload']:
    f = a[3]; n = os.path.basename(f)
    if os.path.exists(os.path.join(rel, n)) and '--clobber' not in a: sys.exit(1)
    shutil.copy(f, os.path.join(rel, n)); sys.exit(0)
sys.exit(1)
'''
# the old key script's part this test needs: a refresh read writes GEO_CACHE/US-<st>.json.gz at GEO_DETAIL (FAKE_N records per layer)
FAKE_KEY = r'''import gzip, json, os
st = os.environ['STATES']; n = int(os.environ.get('FAKE_N', '12'))
assert os.environ.get('GEO_CACHE_MODE') == 'refresh'
recs = [{'OBJECTID': f'{i}'} for i in range(n)] + [{'OBJECTID': f'tnw{i}'} for i in range(5)]
os.makedirs(os.environ['GEO_CACHE'], exist_ok=True)
with gzip.open(os.path.join(os.environ['GEO_CACHE'], f'US-{st}.json.gz'), 'wt', encoding='utf-8') as f:
    json.dump({'st': st, 'detail': float(os.environ['GEO_DETAIL']), 'recs': recs}, f)
'''


def blob(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f: return json.load(f)


with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); repo = t / 'repo'; rel = t / 'release'; rel.mkdir()
    shutil.copytree(HERE / '.github/scripts', repo / '.github/scripts', ignore=shutil.ignore_patterns('__pycache__'))
    (repo / '.github/scripts/kpc_us_key.py').write_text(FAKE_KEY)
    (repo / 'data/outlines').mkdir(parents=True)
    (repo / 'data/outlines/layers.json').write_text(json.dumps({'format': 1, 'layers': {}, 'caches': {'US-TN': {'expected_count': 10}}}))
    with gzip.open(rel / 'US-TN.json.gz', 'wt', encoding='utf-8') as f:
        json.dump({'st': 'TN', 'detail': 0.001, 'recs': [{'OBJECTID': f'{i}'} for i in range(10)] + [{'OBJECTID': f'tnw{i}'} for i in range(5)]}, f)
    before = (rel / 'US-TN.json.gz').read_bytes()
    (t / 'bin').mkdir(); g = t / 'bin/gh'; g.write_text(FAKE_GH); g.chmod(g.stat().st_mode | stat.S_IEXEC)
    py = t / 'bin/python3'; py.symlink_to(sys.executable)
    (t / 'bin/pip').write_text('#!/bin/sh\nexit 0\n'); (t / 'bin/pip').chmod(0o755)
    rt = t / 'rt'; rt.mkdir()
    env = {'PATH': f"{t / 'bin'}:{os.environ.get('PATH', '')}", 'HOME': str(t), 'RUNNER_TEMP': str(rt), 'GITHUB_REPOSITORY': 'KentuckyPortableClub/KPC-Links',
           'FAKE_REL': str(rel), 'FAKE_LOG': str(t / 'gh.log'), 'GEO_CACHE': 'cache/full', 'GEO_DETAIL': '0.00001', 'GH_TOKEN': 'not-a-token', 'PYTHONDONTWRITEBYTECODE': '1'}
    script = repo / '.github/scripts/kpc_layer_full_save.sh'

    def run(**more):
        return subprocess.run(['bash', str(script), 'us', 'TN'], cwd=repo, env=dict(env, **more), capture_output=True, text=True, timeout=120)

    if not script.is_file():
        check(False, 'the full-detail save .github/scripts/kpc_layer_full_save.sh exists')
    else:
        r = run(FAKE_N='12')
        full = rel / 'full-US-TN.json.gz'
        check(r.returncode == 0 and full.is_file(), f'a dying area gets its full-detail save uploaded as full-US-TN.json.gz ({r.stdout[-300:]} {r.stderr[-300:]})')
        check(full.is_file() and blob(full).get('detail') == 0.00001 and len(blob(full)['recs']) == 17, 'the saved copy is the full-detail read (GEO_DETAIL 0.00001), every record')
        check((rel / 'US-TN.json.gz').read_bytes() == before, 'the ~110 m copy US-TN.json.gz is left exactly as it was')
        log = (t / 'gh.log').read_text()
        check('--clobber' not in ''.join(x for x in log.splitlines() if x.startswith('release upload')), 'the full upload never uses --clobber')
        first = full.read_bytes(); (t / 'gh.log').write_text('')
        r = run(FAKE_N='20')
        check(full.read_bytes() == first and 'release upload' not in (t / 'gh.log').read_text() and 'already on the release' in r.stdout, 'one save only: a second run uploads nothing and replaces nothing')
        full.unlink(); shutil.rmtree(repo / 'cache', ignore_errors=True); (t / 'gh.log').write_text('')
        r = run(FAKE_N='9')
        check(not full.is_file() and 'release upload' not in (t / 'gh.log').read_text() and 'save-check refused' in r.stdout, 'a full read with fewer records than the ~110 m copy is refused by save-check: nothing uploaded')
        check((rel / 'US-TN.json.gz').read_bytes() == before, 'and the ~110 m copy is still untouched')
        (rel / 'US-TN.json.gz').rename(t / 'aside.gz'); r = run(FAKE_N='12')
        check(not full.is_file() and 'nothing to compare' in r.stdout, 'no ~110 m copy on the release to compare against: no full save')
        (t / 'aside.gz').rename(rel / 'US-TN.json.gz')
        r = subprocess.run(['bash', str(script), 'us', 'tn;x'], cwd=repo, env=env, capture_output=True, text=True)
        check(r.returncode == 0 and 'not a state code' in r.stdout, 'a bad area code stops it, kept green')

# --- 3. the workflows
for wf, mx, job in (('kpc-geo-cache.yml', 'st', 'us'), ('kpc-world-cache.yml', 'cc', 'world')):
    y = yaml.safe_load((HERE / '.github/workflows' / wf).read_text(encoding='utf-8'))
    on = y.get('on', y.get(True))
    check(set(on) == {'workflow_dispatch'} and on['workflow_dispatch']['inputs']['from_requests'].get('default') is False, f'{wf}: still by hand only, from_requests off by default')
    j = y['jobs'].get('full_save') or {}
    check('full' in (y['jobs']['prepare'].get('outputs') or {}), f'{wf}: prepare passes the planner\'s full list on')
    check("needs.prepare.outputs.full != '[]'" in str(j.get('if', '')) and j.get('needs') == 'prepare', f'{wf}: full_save runs only when the planner names an area')
    runs = ' '.join(str(s.get('run') or '') for s in j.get('steps') or [])
    envs = [s.get('env') or {} for s in j.get('steps') or []]
    check(f'kpc_layer_full_save.sh {job} "$UNIT"' in runs and any(e.get('GEO_DETAIL') == '0.00001' and e.get('GEO_CACHE') == 'cache/full' for e in envs),
          f'{wf}: full_save runs the full-detail save at full detail into its own folder')
    txt = (HERE / '.github/workflows' / wf).read_text(encoding='utf-8')
    check("${{ vars.KPC_LR_DYING || 'full' }}" in txt, f"{wf}: the R-LR2 knob still defaults to the ruling 'full'")
    check('save-check' in SAVE.read_text() and SAVE.read_text().index('save-check') < SAVE.read_text().index('gh release upload') if SAVE.is_file() else False,
          f'{wf}: save-check runs before the full upload')

print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
