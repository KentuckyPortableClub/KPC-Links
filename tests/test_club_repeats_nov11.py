#!/usr/bin/env python3
"""Offline test (bots review, package E, Nov 11 2026): a club / info post cannot go out twice, and a feed that did not answer is
not published as "no alerts".

Fake posters (Discord / Facebook / NOAA / POTA / park-alert feeds are replaced by fakes: zero connections) and fake failing saves:
  - POTA spotter: a Discord refusal half way through a check leaves the posts already sent recorded; the next check sends only the rest
  - Facebook comments: the memory is written BEFORE a reply on Facebook (one reply per comment, ever), a crash half way loses nothing
    and repeats nothing, a comment cut off by the per-run cap is not marked as sent
  - Hunters: the Friday post is sent once per ISO week per channel; a refused post is tried again; a by-hand run can force it
  - Club posts: a crash after Park of the Week has gone out still writes the state file
  - Band alerts (node): the alerts already posted stay recorded when a later post fails; weak alerts are not written down; a quiet check
    leaves the state file alone; the first run posts nothing
  - Facebook / Discord videos (node): the videos already shared stay recorded when the next one is refused
  - Park alerts: a source that did not answer never makes its alerts "gone" (the red warnings stay), a source that answered with
    nothing still does
  - EU alerts: a country whose feed stays down is marked stale and then left out; a run-out warning is taken off
  - The shared save (kpc_save_overwrite.sh) lands a state file after a lost push race, and ends loud (no failure email) when it never lands
Temp dirs only."""
import contextlib, datetime, importlib, io, json, os, pathlib, shutil, subprocess, sys, tempfile, textwrap, urllib.error, urllib.request

HERE = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = HERE / '.github/scripts'
sys.path.insert(0, str(SCRIPTS))
ok = True


def _club_calls():
    import ast
    tree = ast.parse((SCRIPTS / 'kpc_pota_spotter.py').read_text())
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(getattr(t, 'id', '') == 'CALLS' for t in n.targets):
            return sorted(ast.literal_eval(n.value))
    raise SystemExit('CALLS not found')


CALL1, CALL2 = _club_calls()[:2]      # two of the calls the spotter already watches (read from the script, not written here)


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


HOOK = 'https://discord' + '.com/api/' + 'webhooks/' + '123456789012345678/' + 'FAKEhookTOKEN' + 'abcdefghijklmnopqrstuvwxyz012345'
FB = 'EA' + 'AFAKEfbTOKEN' + '0123456789abcdefghijklmnopqrstuvwxyz0123456789'
for k, v in {'FB_PAGE_ID': '123', 'FB_PAGE_TOKEN': FB, 'KPC_DISCORD_WEBHOOK': HOOK, 'KPC_ADMIN_WEBHOOK': HOOK, 'KPC_PARKS_WEBHOOK': HOOK,
             'DISCORD_WEBHOOK_URL': HOOK}.items(): os.environ[k] = v
tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
NOW = datetime.datetime.now(datetime.timezone.utc)


def capture(fn, *a, **k):
    out = io.StringIO(); res = exc = None
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        try: res = fn(*a, **k)
        except SystemExit as e: exc = e
        except Exception as e: exc = e  # noqa: BLE001
    return res, exc, out.getvalue()


def load(name):
    sys.modules.pop(name, None)
    return importlib.import_module(name)


def run_py(script, cwd, env, driver_extra=''):
    return subprocess.run([sys.executable, str(cwd / 'driver.py')], cwd=cwd, capture_output=True, text=True,
                          env={**os.environ, 'C1': CALL1, 'C2': CALL2, 'SCRIPT': str(script), 'PYTHONPATH': str(SCRIPTS), **env})


# ------------------------------------------------------------------ POTA spotter
sp = tmp / 'spot'; sp.mkdir()
(sp / 'driver.py').write_text(textwrap.dedent('''
    import io, json, os, runpy, sys, types, urllib.error, urllib.request, datetime as dt
    g = types.ModuleType('kpc_net_guard'); g.install = lambda: None; sys.modules['kpc_net_guard'] = g
    now = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    FEED = [{'activator': os.environ['C1'], 'reference': 'US-0001', 'frequency': '14074', 'mode': 'FT8', 'spotTime': now, 'name': 'Park A'},
            {'activator': os.environ['C2'], 'reference': 'US-0002', 'frequency': '7074', 'mode': 'FT8', 'spotTime': now, 'name': 'Park B'}]
    plan = os.environ['PLAN'].split(','); calls = []
    class R(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False
    def fake(req, *a, **k):
        url = req.full_url if hasattr(req, 'full_url') else str(req)
        if 'api.pota.app' in url: return R(json.dumps(FEED).encode())
        if 'graph.facebook' in url: return R(b'{}')
        step = plan[min(len(calls), len(plan) - 1)]; calls.append(json.loads(req.data)['embeds'][0]['description'][:30])
        open('calls.json', 'w').write(json.dumps(calls))
        if step == 'ok': return R(b'')
        raise urllib.error.HTTPError(url, int(step), 'x', {}, io.BytesIO(b'{}'))
    urllib.request.urlopen = fake
    try: runpy.run_path(os.environ['SCRIPT'], run_name='__main__')
    except SystemExit as e: print('EXIT', e.code)
'''))
r1 = run_py(SCRIPTS / 'kpc_pota_spotter.py', sp, {'PLAN': 'ok,500'})
st = json.loads((sp / '.github/kpc-pota-spot-state.json').read_text())
acts = sorted(k for k in st if k.startswith('act|'))
check(len(acts) == 1 and 'EXIT' in r1.stdout, 'pota spotter: Discord refuses the 2nd alert of a check: the 1st is already recorded on disk (state written after every post), the 2nd is not')
r2 = run_py(SCRIPTS / 'kpc_pota_spotter.py', sp, {'PLAN': 'ok'})
calls = json.loads((sp / 'calls.json').read_text())
st2 = json.loads((sp / '.github/kpc-pota-spot-state.json').read_text())
check(len(calls) == 1 and len([k for k in st2 if k.startswith('act|')]) == 2, 'pota spotter: the next check sends only the alert that was not sent (1 post, not 2); both are recorded')
(sp / 'calls.json').unlink()
r3 = run_py(SCRIPTS / 'kpc_pota_spotter.py', sp, {'PLAN': 'ok'})
check(not (sp / 'calls.json').exists(), 'pota spotter: a quiet check (nothing new) posts nothing')
before = (sp / '.github/kpc-pota-spot-state.json').read_text()
run_py(SCRIPTS / 'kpc_pota_spotter.py', sp, {'PLAN': 'ok'})
check((sp / '.github/kpc-pota-spot-state.json').read_text() == before, 'pota spotter: a quiet check leaves the state file byte for byte as it was (nothing to commit)')

# ------------------------------------------------------------------ Facebook comments
fbc = load('kpc_fb_comments')
(tmp / 'data').mkdir(exist_ok=True)
fbc.STATE_F = pathlib.Path('data/fb-comments-state.json'); fbc.AUTO_F = pathlib.Path('data/fb-comments-auto.json')
fbc.AUTO_F.write_text('{"auto": true}')
fbc.STATE_F.write_text(json.dumps({'updated': '2026-11-01 00:00', 'sent': []}))
ts = (NOW - datetime.timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%S+0000')


def comments(n):
    return [{'id': f'c{i}', 'created_time': ts[:-7] + f'{i:02d}+0000', 'from': {'name': 'Commenter'}, 'message': 'When is the campout?',
             'permalink_url': 'https://example.invalid/x'} for i in range(n)]


def fake_graph(n):
    def graph(path, **q):
        if path == 'debug_token': return 200, {'data': {'scopes': ['pages_read_user_content', 'pages_manage_posts', 'pages_read_engagement', 'pages_manage_engagement']}}
        if path == 'me': return 200, {'id': '123', 'name': 'Kentucky Portable Club'}
        if path.endswith('/posts'): return 200, {'data': [{'id': 'p1', 'permalink_url': 'u'}]}
        if path.endswith('/comments'): return 200, {'data': comments(n)}
        return 404, {}
    return graph


seen_at_reply, sent = [], []
def reply_crash(cid, text):
    seen_at_reply.append((cid, fbc.fingerprint(cid) in json.loads(fbc.STATE_F.read_text()).get('sent', [])))
    if len(seen_at_reply) == 2: raise KeyError('simulated crash while answering')
    return True, ''
fbc.graph = fake_graph(3); fbc.fb_reply = reply_crash; fbc.discord = lambda t, b: sent.append(t)
_, exc, o = capture(fbc.main)
check(isinstance(exc, KeyError) and seen_at_reply and all(flag for _, flag in seen_at_reply), 'fb_comments: each comment is written to the memory BEFORE the reply on Facebook is tried (a crash or a lost run cannot answer it twice)')
st = json.loads(fbc.STATE_F.read_text())
fps = {c: fbc.fingerprint(c) for c in ('c0', 'c1', 'c2')}
check(fps['c0'] in st['sent'] and fps['c1'] in st['sent'] and fps['c2'] not in st['sent'], 'fb_comments: after the crash the memory holds the comments already handled and NOT the one never reached (it is sent next run)')
seen_at_reply.clear(); sent.clear()
fbc.fb_reply = lambda cid, text: (True, '')
_, exc, o = capture(fbc.main)
check(exc is None and len(sent) == 1, 'fb_comments: the next run sends only the comment that was never reached (1 Discord post, not 3)')
# the per-run cap
fbc.STATE_F.write_text(json.dumps({'updated': '2026-11-01 00:00', 'sent': []}))
fbc.graph = fake_graph(12); sent.clear()
_, exc, o = capture(fbc.main)
st = json.loads(fbc.STATE_F.read_text())
check(len(sent) == fbc.MAX_PER_RUN and len(st['sent']) == fbc.MAX_PER_RUN, 'fb_comments: 12 new comments, cap 10: 10 are sent and remembered; the 2 over the cap are NOT remembered (they used to be, and never came)')
sent.clear(); _, exc, o = capture(fbc.main)
check(len(sent) == 2, 'fb_comments: the next run sends the 2 that waited')
# quiet run
sent.clear(); before = fbc.STATE_F.read_text(); _, exc, o = capture(fbc.main)
after = json.loads(fbc.STATE_F.read_text())
check(not sent and json.loads(before)['sent'] == after['sent'], 'fb_comments: a run with no new comment sends nothing and changes no id in the memory')

# ------------------------------------------------------------------ Hunters weekly post
hn = load('kpc_hunters')
pathlib.Path('kpc-hunters.json').write_text(json.dumps({'ready': True, 'days': 20, 'top': [{'day': 6, 'from': '08:00', 'to': '11:00', 'band': '20m'}], 'windows': [], 'bands': [], 'odds': []}))
hn.W = pathlib.Path('data/hunters/work.json'); hn.W.parent.mkdir(parents=True, exist_ok=True)
hn.W.write_text(json.dumps({'open': {}, 'ids': [], 'cnt': {}}))
calls = []; answers = [204, 200]
hn._http = lambda url, data, headers=None: (calls.append(url.split('/')[2]), answers[0] if 'discord' in url else answers[1])[1]
os.environ.pop('KPC_HUNTERS_FORCE', None)
capture(hn.post); n1 = len(calls)
capture(hn.post); n2 = len(calls)
check(n1 == 2 and n2 == 2, 'hunters: the Friday post goes to Discord and Facebook once; a second Friday run the same week sends nothing')
os.environ['KPC_HUNTERS_FORCE'] = '1'; capture(hn.post)
check(len(calls) == 4, 'hunters: a by-hand run with "post" ticked (KPC_HUNTERS_FORCE=1) posts again on purpose')
os.environ.pop('KPC_HUNTERS_FORCE')
hn.W.write_text(json.dumps({'open': {}, 'ids': [], 'cnt': {}, 'posted': {'discord': '2020-W01', 'facebook': '2020-W01'}}))
capture(hn.post)
check(len(calls) == 6, 'hunters: a mark from an earlier week does not stop this week\'s post')
hn.W.write_text(json.dumps({'open': {}, 'ids': [], 'cnt': {}})); answers[:] = [500, 500]; capture(hn.post); k = len(calls)
answers[:] = [204, 200]; capture(hn.post)
check(len(calls) - k == 2, 'hunters: a refused post (HTTP 500) is not remembered as sent; the next run tries it again')
hn.W.unlink(); k = len(calls); capture(hn.post); capture(hn.post)
check(len(calls) - k == 4 and not hn.W.exists(), 'hunters: with no work file (a cold cache) the post is not blocked and no work file is invented (the next count would think it had seen nothing)')

# ------------------------------------------------------------------ Club posts: state written even when a later step crashes
cp = load('kpc_club_posts')
cp.STATE_F = pathlib.Path('data/kpc-club-posts-state.json')
if cp.STATE_F.exists(): cp.STATE_F.unlink()
cp.park_of_the_week = lambda state: (state.setdefault('featured', []).append('US-0001') or True)
cp.lonely_parks = lambda state: False
cp.busy_bands = lambda state, today, force=False: []
def boom(state, today, force=False): raise RuntimeError('simulated crash after the park post')
cp.holiday_post = boom
os.environ['HOLIDAY_DATE'] = '2026-11-12'      # a Thursday
cp.ONLY = ''
_, exc, o = capture(cp.main)
st = json.loads(cp.STATE_F.read_text()) if cp.STATE_F.exists() else {}
check(isinstance(exc, RuntimeError) and st.get('park_on') == '2026-11-12' and st.get('featured') == ['US-0001'],
      'club posts: a crash after Park of the Week had gone out still writes the state file (a second run the same day does not post it again)')
cp.holiday_post = lambda *a, **k: False; cp.event_weather = lambda *a, **k: None
posted = []; cp.park_of_the_week = lambda state: (posted.append(1) or True)
capture(cp.main)
check(not posted, 'club posts: the run after that does not post Park of the Week again')

# ------------------------------------------------------------------ Park alerts: a source that did not answer is not "gone"
pa = load('kpc_park_alerts')
pa.STATE_F = pathlib.Path('data/park-alerts-state.json'); pa.COND_F = pathlib.Path('kpc-conditions.json'); pa.KY_F = pathlib.Path('kpc-ky-data.json')
pathlib.Path('kpc-ky-data.json').write_text(json.dumps({'parks': [{'c': 'US-1', 'n': 'Test State Park'}]}))
posts = []
pa.post_staff = lambda t, x: posts.append(('staff', t)); pa.post_discord = lambda t, x: posts.append(('discord', t)); pa.post_facebook = lambda t, x: posts.append(('fb', t))


def rec(title):
    return {'who': 'x', 'title': title, 'text': 't', 'link': '', 'first': '2026-10-01', 'runs': 2, 'missing': 0, 'announced': True,
            'routine': False, 'refs': ['US-1']}


def start():
    pa.STATE_F.write_text(json.dumps({'updated': '2026-11-01 00:00', 'pending': [], 'sources': ['fs', 'ky'], 'burn_queue': [],
                                      'seen': {'fs-a': rec('Forest road closed'), 'ky-b': rec('Park gate closed')}}))
    pathlib.Path('kpc-conditions.json').write_text(json.dumps({'updated': '2026-11-01', 'items': [
        {'id': 'pa-fs-a-US-1', 'ref': 'US-1', 'kind': 'Park alert', 'details': 'Forest road closed', 'seen': '2026-10-01', 'call': 'KPC BOT', 'expires': '2026-12-01'}]}))
    posts.clear()


up = {'ky-b': {'who': 'x', 'title': 'Park gate closed', 'text': 't', 'link': ''}}
pa.ky_state_parks = lambda: dict(up); pa.nps_alerts = lambda: {}; pa.lbl_alerts = lambda: {}; pa.kdfwr_alerts = lambda: {}
start(); pa.forest_alerts = lambda: None
outs = ''
for _ in range(3):
    _, exc, o = capture(pa.main); outs += o
st = json.loads(pa.STATE_F.read_text()); cond = json.loads(pathlib.Path('kpc-conditions.json').read_text())
check('fs-a' in st['seen'] and st['seen']['fs-a']['missing'] == 0, 'park alerts: the forest feed fails 3 checks in a row: its alert is kept exactly as it was (missing stays 0; it used to count up and be cleared)')
check(any(c['id'].startswith('pa-fs-a') for c in cond['items']) and not posts, 'park alerts: ...the red warning stays on the park page and nothing is announced (no "looks open again")')
check('::warning title=Park alerts::fs did not answer' in outs, 'park alerts: ...and the run says out loud that the forest feed did not answer (a ::warning), not "nothing changed"')
start(); pa.forest_alerts = lambda: {}
for _ in range(2): capture(pa.main)
st = json.loads(pa.STATE_F.read_text())
check('fs-a' not in st['seen'], 'park alerts: the forest feed ANSWERS with no alerts twice in a row: the alert is gone (a real reopening is still noticed)')
cond = json.loads(pathlib.Path('kpc-conditions.json').read_text())
check(not any(c['id'].startswith('pa-fs-a') for c in cond['items']), 'park alerts: ...and the red warning is taken off the park page')
start(); pa.forest_alerts = lambda: None; pa.ky_state_parks = lambda: {}
pa.nps_alerts = lambda: {'nps-z': {**rec('Some other alert'), 'refs': []}}      # something answered, so the run goes on
for _ in range(3): capture(pa.main)
st = json.loads(pa.STATE_F.read_text())
check('ky-b' not in st['seen'], 'park alerts: a source that answered with nothing still counts its alerts as gone, while the failed one is left alone')
check('fs-a' in st['seen'] and st['seen']['fs-a']['missing'] == 0, 'park alerts: ...in the same run the failed source\'s alert is still kept')

# ------------------------------------------------------------------ EU alerts: stale is visible
eu = load('kpc_eu_alerts')
eu.OUT = pathlib.Path('data/alerts/eu.json'); eu.OUT.parent.mkdir(parents=True, exist_ok=True)
fut = (NOW + datetime.timedelta(hours=5)).isoformat(); past = (NOW - datetime.timedelta(hours=1)).isoformat()
eu.OUT.write_text(json.dumps({'updated': NOW.isoformat(), 'countries': {
    'AT': {'name': 'Austria', 'link': 'x', 'items': [{'area': 'a', 'event': 'Wind', 'level': 'orange', 'sev': 'Severe', 'onset': '', 'expires': fut},
                                                    {'area': 'b', 'event': 'Rain', 'level': 'yellow', 'sev': 'Minor', 'onset': '', 'expires': past}]}}}))
EMPTY = b'<feed xmlns="http://www.w3.org/2005/Atom"></feed>'
def fake_get(u):
    if u.endswith('-austria'): raise OSError('down')
    return EMPTY
eu.get = fake_get
outs = ''
for run in range(1, 5):
    _, exc, o = capture(eu.main); outs += o
    d = json.loads(eu.OUT.read_text())
    if run == 1:
        at = d['countries']['AT']
        check(at.get('stale') is True and at.get('failed_runs') == 1 and len(at['items']) == 1 and at['items'][0]['event'] == 'Wind',
              'eu alerts: Austria\'s feed fails: its last list is kept but marked stale, and the warning that has run out is taken off')
    if run == 3:
        check(d['countries']['AT'].get('failed_runs') == 3, 'eu alerts: still shown (stale) after 3 failed runs in a row')
check('AT' not in json.loads(eu.OUT.read_text())['countries'], 'eu alerts: after the 4th failed run the country is left out, so the page says "our copy did not load" instead of an old list')
check('::warning title=EU weather warnings::' in outs and 'AT' in outs, 'eu alerts: each such run says out loud which feeds did not answer (a ::warning)')
before = eu.OUT.read_text(); capture(eu.main)
check(eu.OUT.read_text() == before, 'eu alerts: a run where nothing changed leaves the file as it is (no commit)')

# ------------------------------------------------------------------ the node bots
stub = textwrap.dedent('''
    const fs = require('fs'); const plan = JSON.parse(process.env.FAKE_PLAN || '{}'); let di = 0, fi = 0; const log = [];
    global.fetch = async (url) => {
      url = String(url); log.push(url.replace(/webhooks\\/.*/, 'webhooks/***').replace(/access_token=[^&]*/, 'access_token=***'));
      fs.writeFileSync(process.env.FAKE_LOG, JSON.stringify(log));
      const next = (arr, i) => (arr || [204])[Math.min(i, (arr || [204]).length - 1)];
      if (url.includes('swpc.noaa.gov')) return { ok: true, status: 200, json: async () => plan.noaa };
      if (/discord(app)?\\.com\\/api\\/webhooks/.test(url)) { const st = next(plan.discord, di++); if (st === 'throw') throw new TypeError('fetch failed'); return { ok: st < 300, status: st, json: async () => ({}), text: async () => '' }; }
      if (url.includes('graph.facebook.com')) { const st = next(plan.fb, fi++); return { ok: st < 300, status: st, json: async () => (st < 300 ? { id: '1_2' } : { error: { message: 'refused', code: 100 } }) }; }
      return { ok: false, status: 404, json: async () => ({}) };
    };
''')


def node_dir(name):
    d = tmp / name; d.mkdir(); (d / 'stub.js').write_text(stub)
    for f in ('kpc-events.js', 'kpc-ky-data.json'): (d / f).symlink_to(HERE / f)
    return d


def run_node(d, script, args, plan):
    env = {**os.environ, 'FAKE_PLAN': json.dumps(plan), 'FAKE_LOG': str(d / 'log.json'), 'NODE_OPTIONS': f'--require {d / "stub.js"}',
           'KPC_YOUTUBE_WEBHOOK': HOOK, 'GENERAL_WEBHOOK_URL': HOOK, 'DRY_RUN': 'false'}
    r = subprocess.run(['node', str(SCRIPTS / script), *args], cwd=d, capture_output=True, text=True, env=env)
    log = json.loads((d / 'log.json').read_text()) if (d / 'log.json').exists() else []
    (d / 'log.json').unlink(missing_ok=True)
    return r, log


stamp = lambda: datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S.000')
al = lambda serial, scale, kind='ALERT': {'product_id': 'A30A', 'issue_datetime': stamp(), 'message': f'Serial Number: {serial}\nNOAA Scale: {scale}\n{kind}: Event {serial}'}
bd = node_dir('band')
feed = [al(9001, 'R3'), al(9002, 'G3'), al(9003, 'R1')]
(bd / 'kpc-social-state.json').write_text(json.dumps({'alerts': {'seen': ['1'], 'last': {}}}))
r, log = run_node(bd, 'kpc_social.js', ['bandalert'], {'noaa': feed, 'discord': [204, 500]})
st = json.loads((bd / 'kpc-social-state.json').read_text())
check(r.returncode == 1 and '9001' in st['alerts']['seen'] and '9002' not in st['alerts']['seen'] and 'R' in st['alerts']['last'],
      'band alerts: the 2nd post is refused: the 1st alert is recorded, the 2nd is not (it is tried again at the next check)')
check('9003' not in st['alerts']['seen'], 'band alerts: a weak alert (R1) is not written to the state file (that was a commit for every flare notice)')
r, log = run_node(bd, 'kpc_social.js', ['bandalert'], {'noaa': feed, 'discord': [204]})
st = json.loads((bd / 'kpc-social-state.json').read_text())
check(r.returncode == 0 and len([u for u in log if 'webhooks' in u]) == 1 and '9002' in st['alerts']['seen'], 'band alerts: the next check posts only the alert that was not sent (1 Discord post, not 2)')
before = (bd / 'kpc-social-state.json').read_text()
r, log = run_node(bd, 'kpc_social.js', ['bandalert'], {'noaa': feed, 'discord': [204]})
check(r.returncode == 0 and not [u for u in log if 'webhooks' in u] and (bd / 'kpc-social-state.json').read_text() == before, 'band alerts: a quiet check posts nothing and leaves the state file byte for byte as it was')
fresh_dir = node_dir('band_first')
r, log = run_node(fresh_dir, 'kpc_social.js', ['bandalert'], {'noaa': feed, 'discord': [204]})
st = json.loads((fresh_dir / 'kpc-social-state.json').read_text())
check(r.returncode == 0 and not [u for u in log if 'webhooks' in u] and set(st['alerts']['seen']) == {'9001', '9002', '9003'} and st['alerts'].get('init') is True,
      'band alerts: the very first run remembers what is already up and posts nothing')

vd = node_dir('videos')
vids = {'channels': [{'name': 'Test', 'videos': [{'id': 'AAAAAAAAAAA', 'title': 'one', 'published': '2026-11-01'}, {'id': 'BBBBBBBBBBB', 'title': 'two', 'published': '2026-11-02'}]}]}
(vd / 'kpc-youtube.json').write_text(json.dumps(vids)); (vd / 'kpc-fb-posted.json').write_text('{"videos": []}'); (vd / 'kpc-discord-videos.json').write_text('{"videos": []}')
r, log = run_node(vd, 'kpc_facebook.js', ['videos'], {'fb': [200, 400]})
st = json.loads((vd / 'kpc-fb-posted.json').read_text())
check(r.returncode == 1 and st['videos'] == ['AAAAAAAAAAA'], 'facebook videos: the 2nd video is refused: the 1st is recorded as shared (it used to be lost with the exit), the run still ends red')
r, log = run_node(vd, 'kpc_facebook.js', ['videos'], {'fb': [200]})
st = json.loads((vd / 'kpc-fb-posted.json').read_text())
check(r.returncode == 0 and len([u for u in log if 'graph' in u]) == 1 and sorted(st['videos']) == ['AAAAAAAAAAA', 'BBBBBBBBBBB'], 'facebook videos: the next run shares only the 2nd (1 post, not 2)')
r, log = run_node(vd, 'kpc_discord_videos.js', [], {'discord': [204, 'throw']})
st = json.loads((vd / 'kpc-discord-videos.json').read_text())
check(st['videos'] == ['AAAAAAAAAAA'], 'discord videos: the connection drops on the 2nd video: the 1st is recorded as shared (the program no longer ends before writing the list)')
r, log = run_node(vd, 'kpc_discord_videos.js', [], {'discord': [204]})
st = json.loads((vd / 'kpc-discord-videos.json').read_text())
check(len([u for u in log if 'webhooks' in u]) == 1 and sorted(st['videos']) == ['AAAAAAAAAAA', 'BBBBBBBBBBB'], 'discord videos: the next run shares only the 2nd')

# ------------------------------------------------------------------ the shared save: lost push race, never lands
def sh(cmd, cwd, **k):
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, **k)


def make_repo(reject_first):
    base = pathlib.Path(tempfile.mkdtemp(dir=tmp)); bare = base / 'origin.git'; work = base / 'work'
    sh(f'git init -q --bare -b main {bare}', base)
    hook = bare / 'hooks/pre-receive'
    sh(f'git clone -q {bare} {work}', base)
    (work / '.github/scripts').mkdir(parents=True)
    for f in ('kpc_save_overwrite.sh', 'kpc_save_merge.py'): shutil.copy(SCRIPTS / f, work / '.github/scripts' / f)
    (work / '.github/kpc-pota-spot-state.json').write_text('{}\n')
    sh('git config user.name t; git config user.email t@example.invalid; git checkout -q -b main; git add -A; git commit -qm init', work)
    sh('git push -q origin HEAD:main', work)       # the first push (init) is allowed; the refusing hook is installed after it
    hook.write_text('#!/bin/sh\nf="$0.count"; n=$(cat "$f" 2>/dev/null || echo 0); n=$((n+1)); echo $n > "$f"\n'
                    f'[ "$n" -le {reject_first} ] && {{ echo "rejected (simulated lost race)" >&2; exit 1; }}\nexit 0\n')
    hook.chmod(0o755)
    return bare, work


for label, reject, expect_landed in (('one lost push race', 1, True), ('the push never lands', 99, False)):
    bare, work = make_repo(reject)
    (work / '.github/kpc-pota-spot-state.json').write_text('{"act|' + CALL1 + '|US-0001|2026-11-11": "t"}\n')
    sh('git add .github/kpc-pota-spot-state.json', work)
    r = sh('KPC_SAVE_TRIES=2 KPC_SAVE_MODE=overwrite KPC_SAVE_RED=no bash .github/scripts/kpc_save_overwrite.sh --copy "Update KPC POTA spot notification state" - -- .github/kpc-pota-spot-state.json', work)
    shown = sh(f'git --git-dir={bare} show main:.github/kpc-pota-spot-state.json', tmp).stdout
    landed = CALL1 in shown
    if expect_landed:
        check(landed and r.returncode == 0, 'save helper: the push is refused once (a lost race): the state file still lands on try 2, on top of the newest main')
    else:
        check(not landed and r.returncode == 0 and '::error title=Save' in r.stdout, 'save helper: the push never lands: ends with a loud ::error and exit 0 (KPC_SAVE_RED=no: no failure email), nothing half-saved on main')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
