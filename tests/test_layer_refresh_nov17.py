#!/usr/bin/env python3
"""Offline test (Handoff 3, third job; KPC owner, 2026-11-17): the keeper asks, the old saved-shapes bots fetch.

kpc_layer_refresh.py reads the keeper's request file and names the areas kpc-geo-cache.yml / kpc-world-cache.yml re-read with their own
fetch, pacing, save-check and upload. Checked here, on made-up request files in temp folders and a fake `gh` (no network):
  1. request-only fetch: only the requested areas are planned, in both workflows' real prepare step;
  2. a layer nobody has walked is UNKNOWN, never 'unchanged';
  3. the save-check guard still refuses a copy with fewer records, and still runs before every upload;
  4. no request file (or an unreadable one) = nothing is fetched (empty list, and the fetch job is skipped);
  5. the receipt shows the request count;
  6. the four rulings R-LR1..R-LR4 are knobs that are unset in the repo: unset = nothing extra (every changed row held);
  7. no schedule block, by-hand button only; the planner has no network code; a layer address never reaches a log; WDPA refused."""
import ast, gzip, json, os, pathlib, stat, subprocess, sys, tempfile
import yaml

HERE = pathlib.Path(__file__).resolve().parent.parent
PLAN = HERE / '.github/scripts/kpc_layer_refresh.py'
CLI = HERE / '.github/scripts/kpc_master_cli.py'
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


if not PLAN.is_file():
    check(False, 'the request planner .github/scripts/kpc_layer_refresh.py exists'); print('SOME FAILED'); sys.exit(1)
sys.path.insert(0, str(PLAN.parent))
import kpc_layer_refresh as LR  # noqa: E402

SECRET = 'https://example.invalid/private-layer-address/FeatureServer/7'
ALL_US = 'AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split()
RULED = {'KPC_LR_CHANGED_READ': 'whole'}   # a test-only ruling; the repo leaves every knob unset
REQ = {'format': 1, 'written': '2026-11-17 07:41 UTC',
       'requests': [{'layer': SECRET, 'area': 'US-TN', 'moved': ['etag'], 'date': '2026-11-17', 'by': 'keeper'},
                    {'layer': SECRET + 'b', 'area': 'US-TN', 'moved': ['etag', 'lastEditDate'], 'date': '2026-11-17', 'by': 'keeper'},
                    {'layer': SECRET + 'c', 'area': 'W-JP', 'moved': ['lastEditDate'], 'date': '2026-11-16', 'by': 'keeper'},
                    {'layer': SECRET + 'd', 'area': 'CA-ON', 'moved': ['etag'], 'date': '2026-11-16', 'by': 'keeper'}],
       'walked': [{'layer': SECRET, 'area': 'US-TN'}, {'layer': SECRET + 'b', 'area': 'US-TN'}, {'layer': SECRET + 'e', 'area': 'US-MO'},
                  {'layer': SECRET + 'f', 'area': 'US-OH'}],
       'unwalked': [{'layer': SECRET + 'g', 'area': 'US-OH'}, {'layer': SECRET + 'h', 'area': 'US-IN'}]}

# --- 1. request-only fetch (pure plan)
rc = LR.plan(REQ, 'found', 'us', known=ALL_US, env=RULED)
check(rc['fetch'] == ['TN'], f"US: only the requested state is re-read ({rc['fetch']})")
ky = dict(REQ, requests=[dict(REQ['requests'][0], area='US-KY')])
rk = LR.plan(ky, 'found', 'us', known=ALL_US, env=RULED)
check(rk['fetch'] == [] and rk['for_this_job'] == 1 and any('no saved copy' in k for k in rk['held']), 'a US area the job does not save (KY: its own key) is held and said, not dropped silently')
rw = LR.plan(REQ, 'found', 'world', env=RULED)
check(rw['fetch'] == ['CA', 'JP'] and rw['served'] == 2, f"world: only the requested country and Canada are re-read ({rw['fetch']})")
rc2 = LR.plan(REQ, 'found', 'us', want=['OH'], known=ALL_US, env=RULED)
check(rc2['fetch'] == [] and rc2['held'], 'the states box narrows the requests (TN not asked this run: held, nothing fetched)')

# --- 2. unknown is not unchanged
check(rc['unknown_layers'] == {'US-IN': 1, 'US-OH': 1}, f"a layer with no first reading is counted as unknown ({rc['unknown_layers']})")
check('US-OH' not in rc['unchanged_areas'] and 'US-IN' not in rc['unchanged_areas'], 'an area with an unwalked layer is never called unchanged')
check(rc['unchanged_areas'] == ['US-MO'], f"only a fully walked area with no request is unchanged ({rc['unchanged_areas']})")
check('US-WY' in rc['unknown_areas'] and 'US-TN' not in rc['unknown_areas'], "an area the keeper's file does not cover is unknown")
r0 = LR.plan(None, 'none', 'us', known=ALL_US, env=RULED)
check(len(r0['unknown_areas']) == len(ALL_US) and r0['unchanged_areas'] == [], 'no request file: every area is unknown, none unchanged')

# --- 6. the knobs: unset = nothing extra
ru = LR.plan(REQ, 'found', 'us', known=ALL_US, env={})
check(ru['fetch'] == [] and sum(ru['held'].values()) == 2 and all(v == 'unset' for v in ru['knobs'].values()),
      'every knob unset: the changed rows are held (R-LR3 not ruled), nothing is fetched')
rr = LR.plan(REQ, 'found', 'us', known=ALL_US, env={'KPC_LR_CHANGED_READ': 'records'})
check(rr['fetch'] == [] and any('R-LR3' in k for k in rr['held']), "R-LR3 'records': held (the records-only read is not built)")
rbad = LR.plan(REQ, 'found', 'us', known=ALL_US, env={'KPC_LR_CHANGED_READ': 'yes please'})
check(rbad['fetch'] == [] and rbad['knobs']['R-LR3'] == 'unset' and rbad['notes'], 'a knob with an unknown value counts as unset, with a note')
hand = dict(REQ, requests=[dict(REQ['requests'][0], by='chat')])
check(LR.plan(hand, 'found', 'us', known=ALL_US, env=RULED)['fetch'] == [], 'R-LR4 unset: a row added by hand is held')
check(LR.plan(hand, 'found', 'us', known=ALL_US, env=dict(RULED, KPC_LR_WHO='keeper'))['fetch'] == [], "R-LR4 'keeper': a hand row is held")
check(LR.plan(hand, 'found', 'us', known=ALL_US, env=dict(RULED, KPC_LR_WHO='keeper+hand'))['fetch'] == ['TN'], "R-LR4 'keeper+hand': a hand row is served")
dying = dict(REQ, requests=[dict(REQ['requests'][0], moved=['gone'])])
check(LR.plan(dying, 'found', 'us', known=ALL_US, env=RULED)['fetch'] == [], 'R-LR2 unset: a dying layer is held (our last copy left as it is)')
check(LR.plan(dying, 'found', 'us', known=ALL_US, env=dict(RULED, KPC_LR_DYING='full'))['fetch'] == [], "R-LR2 'full': held for a full-detail save")
check(LR.plan(dying, 'found', 'us', known=ALL_US, env=dict(RULED, KPC_LR_DYING='saved'))['fetch'] == ['TN'], "R-LR2 'saved': served like any row")
import datetime  # noqa: E402
dates = {'US-MO.json.gz': '2026-01-01T00:00:00Z', 'US-OH.json.gz': '2026-11-15T00:00:00Z', 'W-JP.json.gz': '2026-01-01T00:00:00Z'}
today = datetime.date(2026, 11, 17)
check(LR.plan(None, 'none', 'us', known=ALL_US, env={}, asset_dates=dates, today=today)['fetch'] == [], 'R-LR1 unset: no staleness re-read')
check(LR.plan(None, 'none', 'us', known=ALL_US, env={'KPC_LR_STALE_DAYS': 'never'}, asset_dates=dates, today=today)['fetch'] == [], "R-LR1 'never': no staleness re-read")
st = LR.plan(None, 'none', 'us', known=ALL_US, env={'KPC_LR_STALE_DAYS': '180'}, asset_dates=dates, today=today)
check(st['fetch'] == ['MO'] and st['stale'] == ['US-MO'], f"R-LR1 180 days: only the copy older than that is re-read ({st['fetch']})")

# --- 7. WDPA, bad rows, privacy, no network code
wd = dict(REQ, requests=[dict(REQ['requests'][0], layer='https://data-gis.unep-wcmc.org/server/rest/services/ProtectedSites/The_World_Database_of_Protected_Areas/FeatureServer/1')])
rwd = LR.plan(wd, 'found', 'us', known=ALL_US, env=RULED)
check(rwd['fetch'] == [] and any('WDPA' in k for k in rwd['refused']), 'a WDPA / Protected Planet row is refused (never a source)')
bad = dict(REQ, requests=[{'area': 'US-TN', 'moved': ['etag'], 'date': 'soon', 'by': 'keeper', 'layer': 'x'}, {'area': 'KY', 'moved': ['etag'], 'date': '2026-11-17', 'by': 'keeper', 'layer': 'x'}])
check(LR.plan(bad, 'found', 'us', known=ALL_US, env=RULED)['fetch'] == [], 'a row not in the request format is refused')
tree = ast.parse(PLAN.read_text(encoding='utf-8'))
mods = {n.name.split('.')[0] for x in ast.walk(tree) if isinstance(x, ast.Import) for n in x.names} | {x.module.split('.')[0] for x in ast.walk(tree) if isinstance(x, ast.ImportFrom) and x.module}
check(not mods & {'urllib', 'http', 'socket', 'requests', 'ssl', 'subprocess', 'kpc_net_guard', 'kpc_host_pace'}, f'the planner has no network or fetch code (imports: {sorted(mods)})')

# --- 1/4/5 through the real prepare steps, with a fake gh
FAKE_GH = r'''#!/usr/bin/env python3
import json, os, shutil, sys
a = sys.argv[1:]; open(os.environ['FAKE_LOG'], 'a').write(' '.join(a) + '\n')
if a[:2] == ['release', 'view'] and '--json' in a:
    print(json.dumps([{'name': n, 'updatedAt': '2026-11-10T00:00:00Z'} for n in os.environ.get('FAKE_ASSETS', '').split()])); sys.exit(0)
if a[:2] == ['release', 'view']: sys.exit(0)
if a[:2] == ['release', 'download'] and a[a.index('-p') + 1] == 'layer-requests.json' and os.environ.get('FAKE_REQ'):
    shutil.copy(os.environ['FAKE_REQ'], os.path.join(a[a.index('-D') + 1], 'layer-requests.json')); sys.exit(0)
sys.exit(1)
'''


def prepare_step(wf, sid):
    y = yaml.safe_load((HERE / '.github/workflows' / wf).read_text(encoding='utf-8'))
    return y, next(s for s in y['jobs']['prepare']['steps'] if s.get('id') == sid)


def run_step(step, t, from_req, assets, req_text, env_more=None, want=''):
    (t / 'bin').mkdir(exist_ok=True); g = t / 'bin/gh'; g.write_text(FAKE_GH); g.chmod(g.stat().st_mode | stat.S_IEXEC)
    import shutil; rt = t / 'rt'; shutil.rmtree(rt, ignore_errors=True); rt.mkdir(); out = t / 'out.txt'; summ = t / 'summary.md'; log = t / 'gh.log'
    for f in (out, summ, log): f.write_text('')
    req = None
    if req_text is not None: req = t / 'req.json'; req.write_text(req_text)
    env = {'PATH': f"{t / 'bin'}:{os.environ.get('PATH', '')}", 'HOME': str(t), 'RUNNER_TEMP': str(rt), 'GITHUB_OUTPUT': str(out),
           'GITHUB_STEP_SUMMARY': str(summ), 'GITHUB_REPOSITORY': 'KentuckyPortableClub/KPC-Links', 'FAKE_LOG': str(log),
           'FAKE_ASSETS': ' '.join(assets), 'FAKE_REQ': str(req or ''), 'WANT': want, 'FROM_REQUESTS': 'true' if from_req else 'false',
           'GH_TOKEN': 'not-a-token', **(env_more or {})}
    for k in ('KPC_LR_STALE_DAYS', 'KPC_LR_DYING', 'KPC_LR_CHANGED_READ', 'KPC_LR_WHO'): env.setdefault(k, '')
    py = pathlib.Path(sys.executable).parent; env['PATH'] = f"{t / 'bin'}:{py}:{os.environ.get('PATH', '')}"
    r = subprocess.run(['bash', '-e', '-c', step['run']], cwd=HERE, env=env, capture_output=True, text=True, timeout=120)
    lines = [x for x in out.read_text().splitlines() if '=' in x]
    return r, dict(x.split('=', 1) for x in lines), summ.read_text(), log.read_text()


for wf, sid, key, want_fetch in (('kpc-geo-cache.yml', 'g', 'groups', ['TN']), ('kpc-world-cache.yml', 'l', 'list', ['JP', 'CA'])):
    y, step = prepare_step(wf, sid)
    with tempfile.TemporaryDirectory() as td:
        t = pathlib.Path(td)
        r, o, summ, log = run_step(step, t, True, ['US-TN.json.gz', 'layer-requests.json'], json.dumps(REQ), RULED)
        check(r.returncode == 0 and json.loads(o.get(key, 'null')) == want_fetch, f'{wf}: from_requests plans only the requested areas ({o.get(key)}; rc {r.returncode} {r.stderr[-300:]})')
        check('rows read: **4**' in summ and 'served: **' in summ, f'{wf}: the receipt in the step summary shows the request count')
        check(SECRET not in summ + r.stdout + r.stderr + json.dumps(o), f'{wf}: no layer address reaches the log, the summary or the output')
        check('upload' not in log and 'create' not in log, f'{wf}: the prepare step only reads the release (gh calls: {log.split()[:2]})')
        r, o, summ, log = run_step(step, t, True, ['US-TN.json.gz'], None, RULED)
        check(r.returncode == 0 and json.loads(o.get(key, 'null')) == [] and 'request file: **none**' in summ, f'{wf}: no request file on the release = nothing planned')
        r, o, summ, log = run_step(step, t, True, ['layer-requests.json'], '{not json', RULED)
        check(r.returncode == 0 and json.loads(o.get(key, 'null')) == [] and 'unreadable' in summ, f'{wf}: an unreadable request file = nothing planned')
        r, o, summ, log = run_step(step, t, True, ['layer-requests.json'], json.dumps(REQ), {})
        check(r.returncode == 0 and json.loads(o.get(key, 'null')) == [], f'{wf}: knobs unset = the changed rows are held, nothing planned')
        r, o, summ, log = run_step(step, t, False, [], None, RULED, want='TN' if 'geo' in wf else 'JP')
        check(r.returncode == 0 and json.loads(o.get(key, 'null')) == (['TN'] if 'geo' in wf else ['JP']) and 'Layer requests' not in summ,
              f'{wf}: without from_requests the list is made exactly as before')
    fj = y['jobs']['fetch']
    check(f"needs.prepare.outputs.{key} != '[]'" in str(fj.get('if', '')), f'{wf}: the fetch job is skipped when the list is empty (no request = nothing fetched)')
    on = y.get('on', y.get(True))
    check(set(on) == {'workflow_dispatch'} and 'from_requests' in on['workflow_dispatch']['inputs'] and on['workflow_dispatch']['inputs']['from_requests'].get('default') is False,
          f'{wf}: by-hand button only (no schedule block); from_requests is off unless pressed')
    txt = (HERE / '.github/workflows' / wf).read_text(encoding='utf-8')
    # KPC owner, 2026-11-17: R-LR1..R-LR4 RULED (180 days for a dateless layer, full save before a layer dies, whole re-read,
    # keeper or a chat may ask). The workflow carries the rulings as defaults; a repo variable still overrides.
    RULED_DEFAULTS = {'KPC_LR_STALE_DAYS': '180', 'KPC_LR_DYING': 'full', 'KPC_LR_CHANGED_READ': 'whole', 'KPC_LR_WHO': 'keeper+hand'}
    check(all(f"${{{{ vars.{k} || '{v}' }}}}" in txt for k, v in RULED_DEFAULTS.items()) and set(RULED_DEFAULTS) == set(LR.KNOBS.values()),
          f'{wf}: the four knobs default to the owner\'s rulings, and a repo variable overrides')
    steps = fj['steps']; runs = [str(s.get('run') or '') for s in steps]
    fetch_i = next(i for i, x in enumerate(runs) if ('kpc_us_key.py' if 'geo' in wf else 'kpc_world_key.py') in x)
    up_i = next(i for i, x in enumerate(runs) if 'gh release upload boundary-cache' in x)
    check((steps[fetch_i].get('env') or {}).get('GEO_CACHE_MODE') == 'refresh' and 'save-check' in runs[up_i][:runs[up_i].index('gh release upload')],
          f'{wf}: the same old fetch step (GEO_CACHE_MODE refresh) and save-check before the upload serve the requests')
    check('kpc_layer_refresh' not in ''.join(runs), f'{wf}: the fetch job is unchanged (no new fetcher)')

# --- 3. the save-check guard still refuses a smaller copy
def copy(path, layers):
    recs = [{'OBJECTID': f'{lay}{i}'} for lay, n in layers.items() for i in range(n)]
    with gzip.open(path, 'wt', encoding='utf-8') as f: json.dump({'recs': recs}, f)


with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); root = t / 'outlines'; root.mkdir(); ag = t / 'against'; ag.mkdir(); new = t / 'new'; new.mkdir()
    (root / 'layers.json').write_text(json.dumps({'format': 1, 'layers': {}, 'caches': {'US-KY': {'expected_count': 10}}}))
    copy(ag / 'US-KY.json.gz', {'': 10, 'kyw': 6})
    copy(new / 'US-KY.json.gz', {'': 12, 'kyw': 5})
    r = subprocess.run([sys.executable, str(CLI), 'save-check', '--root', str(root), '--against', str(ag), '--ok-list', str(t / 'ok.txt'), str(new / 'US-KY.json.gz')], capture_output=True, text=True)
    check(r.returncode != 0 and 'kyw' in r.stdout and (t / 'ok.txt').read_text().strip() == '', 'save-check refuses a requested re-read that came back with fewer records for a layer')
    copy(new / 'US-KY.json.gz', {'': 10, 'kyw': 7})
    r = subprocess.run([sys.executable, str(CLI), 'save-check', '--root', str(root), '--against', str(ag), str(new / 'US-KY.json.gz')], capture_output=True, text=True)
    check(r.returncode == 0, 'and allows one that holds at least as many')

print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
