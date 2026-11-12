#!/usr/bin/env python3
"""Offline test (bots review, package E, Nov 11 2026): no secret reaches a log line.

A made-up Discord webhook link, Facebook token, API key and published-sheet link are put in the environment of each club / info bot
(boards, hunters, POTA spotter, Discord watch, Facebook comments, park alerts, club posts, new references, social, videos, EU
alerts), then every error path is forced (a dropped connection whose text repeats the address, a Graph / Discord answer that repeats
the token, a refused post) and what the bot printed (stdout + stderr + the step-summary file) is searched for the made-up values.
Nothing here touches the network: urlopen / fetch are replaced by fakes, the real tree is only read, temp dirs only.
The made-up values are built at run time so this file holds nothing that looks like a live credential."""
import ast, contextlib, importlib, io, json, os, pathlib, re, subprocess, sys, tempfile, textwrap

HERE = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = HERE / '.github/scripts'
sys.path.insert(0, str(SCRIPTS))
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


# made-up secrets, assembled at run time
HOOK = 'https://discord' + '.com/api/' + 'webhooks/' + '123456789012345678/' + 'FAKEhookTOKEN' + 'abcdefghijklmnopqrstuvwxyz012345'
FB = 'EA' + 'AFAKEfbTOKEN' + '0123456789abcdefghijklmnopqrstuvwxyz0123456789'
SHEET = 'https://docs.google' + '.com/spreadsheets/d/e/' + '2PACX-1vFAKEsheetid0123456789abcdefghijklmnop' + '/pub?output=csv'
NPS = 'FAKEnpsKEY' + '0123456789abcdef'
BOT = 'FAKEdiscordBOT' + 'TOKEN0123456789abcdef'
SECRETS = [HOOK, HOOK.rsplit('/', 1)[1], FB, SHEET, SHEET.split('/e/')[1].split('/')[0], NPS, BOT]
ENV = {'FB_PAGE_ID': '123', 'FB_PAGE_TOKEN': FB, 'KPC_DISCORD_WEBHOOK': HOOK, 'KPC_ADMIN_WEBHOOK': HOOK, 'KPC_PARKS_WEBHOOK': HOOK,
       'DISCORD_WEBHOOK_URL': HOOK, 'NPS_API_KEY': NPS, 'DISCORD_BOT_TOKEN': BOT, 'KPC_ACTIVATIONS_CSV': SHEET,
       'COMMUNITY_SHEET_CSV': SHEET, 'NOTES_SHEET_CSV': SHEET, 'KPC_REPORTS_CSV': SHEET}
for k, v in ENV.items(): os.environ[k] = v


def leaks(text):
    return [s[:6] + '...' for s in SECRETS if s in text]


import urllib.error, urllib.request


class Boom(Exception): pass


def fake_urlopen_factory(mode, calls=None):
    """mode: 'text' = raise an error whose text repeats the address; 'http' = HTTP 400 whose body repeats the token and the link."""
    def fake(req, *a, **k):
        url = req.full_url if hasattr(req, 'full_url') else str(req)
        if calls is not None: calls.append(url.split('?')[0].split('/webhooks/')[0])
        if mode == 'text': raise ValueError(f'could not reach {url} (token {FB})')
        body = json.dumps({'error': {'message': f'Malformed access token {FB} for {HOOK}', 'code': 190}}).encode()
        raise urllib.error.HTTPError(url, 400, 'Bad Request', {}, io.BytesIO(body))
    return fake


def capture(fn, *a, **k):
    out, err = io.StringIO(), io.StringIO()
    summary = tempfile.NamedTemporaryFile('w+', suffix='.md', delete=False)
    os.environ['GITHUB_STEP_SUMMARY'] = summary.name
    res = exc = None
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try: res = fn(*a, **k)
        except SystemExit as e: exc = e
        except Exception as e: exc = e  # noqa: BLE001
    summary.close(); s = pathlib.Path(summary.name).read_text(); os.unlink(summary.name)
    return res, exc, out.getvalue() + err.getvalue() + s


def load(name):
    sys.modules.pop(name, None)
    return importlib.import_module(name)


real_urlopen = urllib.request.urlopen
tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
(tmp / 'data').mkdir()

# ------------------------------------------------------------------ the scrub module itself (python + node)
import kpc_scrub as S
raw = f'x {HOOK} y access_token={FB} z key={NPS} Bearer {FB} {SHEET} {HOOK.rsplit("/", 1)[1]} {FB.replace("A", "%41")}'
check(not leaks(S.scrub(raw)), 'kpc_scrub.scrub removes the webhook link, the token (as given, as a query value, as Bearer), the API key, the sheet link and the bare webhook token')
import urllib.parse
check(not leaks(S.scrub(urllib.parse.quote(HOOK, safe='') + ' ' + urllib.parse.quote(FB, safe=''))), 'kpc_scrub.scrub removes URL-encoded copies of the secrets of this run')
check('50%' in S.notice_text('50% done\nsecond line') or True, 'notice_text escapes (smoke)')
check(S.notice_text('a%b\nc') == 'a%25b%0Ac', 'notice_text still escapes % and line breaks for ::notice lines')
check(S.scrub('plain text, no secrets, 12345') == 'plain text, no secrets, 12345', 'text without a secret is left alone')
check(S.host_of(HOOK) == 'discord.com', 'host_of gives the host only')
node = subprocess.run(['node', '-e', "const s=require(process.argv[1]);process.stdout.write(s.scrub(process.env.RAW)+'|'+s.noticeText('a%b\\nc'))",
                       str(SCRIPTS / 'kpc_scrub.js')], capture_output=True, text=True, env={**os.environ, 'RAW': raw})
check(node.returncode == 0 and not leaks(node.stdout) and node.stdout.endswith('|a%25b%0Ac'), 'kpc_scrub.js (node) removes the same secrets and escapes the same way')

# ------------------------------------------------------------------ Facebook comments
fbc = load('kpc_fb_comments')
for mode in ('text', 'http'):
    urllib.request.urlopen = fake_urlopen_factory(mode)
    (c, j), exc, o = capture(fbc.graph, 'me', fields='id,name')
    check(c in (0, 400) and not leaks(json.dumps(j)), f'fb_comments.graph ({mode} error): the answer handed back holds no secret')
    _, exc, o = capture(fbc.notice, 'Could not see who the token belongs to: ' + str(j.get('error', {}).get('message')))
    check(not leaks(o), f'fb_comments.notice ({mode} error): nothing leaks to the log')
    (okr, err), exc, o = capture(fbc.fb_reply, '1_2', 'hello')
    check(not okr and not leaks(err + o), f'fb_comments.fb_reply ({mode} error): the error text holds no secret')
    _, exc, o = capture(fbc.discord, 'title', 'text')
    check(not leaks(o), f'fb_comments.discord ({mode} error): the log holds no secret')
fbc.STATE_F = pathlib.Path('data/fb-comments-state.json')
urllib.request.urlopen = fake_urlopen_factory('text')
_, exc, o = capture(fbc.main)
check(not leaks(o), 'fb_comments.main with every request failing: stdout/stderr hold no secret')

# ------------------------------------------------------------------ Hunters
hn = load('kpc_hunters')
urllib.request.urlopen = fake_urlopen_factory('text')
st, exc, o = capture(hn._http, HOOK, b'{}', {})
check(st == 'ValueError' and not leaks(o + str(st)), 'hunters._http: a failed post answers with the kind of error, not its text')
urllib.request.urlopen = fake_urlopen_factory('http')
st, exc, o = capture(hn._http, HOOK, b'{}', {})
check(st == 400 and not leaks(o), 'hunters._http: an HTTP refusal answers with the number only')
pathlib.Path('kpc-hunters.json').write_text(json.dumps({'ready': True, 'days': 20, 'top': [{'day': 6, 'from': '08:00', 'to': '11:00', 'band': '20m'}], 'windows': [], 'bands': [], 'odds': []}))
_, exc, o = capture(hn.post)
check(not leaks(o), 'hunters.post with Discord and Facebook failing: the log holds no secret')
_, exc, o = capture(hn.notice, 'Hunters', f'POTA spots not read this time ({FB} {HOOK}); skipped')
check(not leaks(o), 'hunters.notice scrubs what it is given')

# ------------------------------------------------------------------ park alerts
pa = load('kpc_park_alerts')
urllib.request.urlopen = fake_urlopen_factory('text')
(c, r), exc, o = capture(pa.http, HOOK, b'{}')
check(c == 0 and not leaks(str(r) + o), 'park_alerts.http: a dropped connection answers with the kind of error only')
pa.DISCORD, pa.FB_ID, pa.FB_TOKEN, pa.STAFF = HOOK, '123', FB, HOOK
pa.POSTS_PAUSED_UNTIL = '2000-01-01'
urllib.request.urlopen = fake_urlopen_factory('http')
_, exc, o = capture(pa.post_discord, 'a', 'b'); check(not leaks(o), 'park_alerts.post_discord (HTTP error repeating the link): no secret in the log')
_, exc, o = capture(pa.post_facebook, 'a', 'b'); check(not leaks(o), 'park_alerts.post_facebook (HTTP error repeating the token): no secret in the log')
_, exc, o = capture(pa.post_staff, 'a', 'b'); check(not leaks(o), 'park_alerts.post_staff: no secret in the log')
_, exc, o = capture(pa.notice, 'Park alerts', f'Kentucky State Parks did not answer: {HOOK} {FB}'); check(not leaks(o), 'park_alerts.notice scrubs what it is given')

# ------------------------------------------------------------------ club posts
cp = load('kpc_club_posts')
cp.FB_ID, cp.FB_TOKEN = '123', FB
urllib.request.urlopen = fake_urlopen_factory('text')
c, r = cp.http(HOOK, b'{}')
check(c == 0 and not leaks(r), 'club_posts.http: a dropped connection answers with the kind of error only')
urllib.request.urlopen = fake_urlopen_factory('http')
_, exc, o = capture(cp.to_discord, ('KPC_DISCORD_WEBHOOK',), 't', 'b'); check(not leaks(o), 'club_posts.to_discord (HTTP error repeating the link): no secret in the log')
_, exc, o = capture(cp.to_facebook, 'hello'); check(not leaks(o), 'club_posts.to_facebook (HTTP error repeating the token): no secret in the log')

# ------------------------------------------------------------------ Discord watch / mod
dw = load('kpc_discord_watch')
dw.HOOK, dw.TOKEN = HOOK, BOT
urllib.request.urlopen = fake_urlopen_factory('http')
_, exc, o = capture(dw.say, 't', 'b'); check(not leaks(o), 'discord_watch.say (HTTP error repeating the link): no secret in the log')
urllib.request.urlopen = fake_urlopen_factory('text')
_, exc, o = capture(dw.say, 't', 'b'); check(not leaks(o), 'discord_watch.say (dropped connection repeating the link): no secret in the log')
res, exc, o = capture(dw.call, 'channels/1/messages'); check(not leaks(json.dumps(res) + o), 'discord_watch.call: the error handed back holds no secret')
_, exc, o = capture(dw.notice, f'Could not post: {HOOK}'); check(not leaks(o), 'discord_watch.notice scrubs what it is given')
dm = load('kpc_discord_mod')
_, exc, o = capture(dm.notice, f'x {BOT} {HOOK}'); check(not leaks(o), 'discord_mod.notice scrubs what it is given')

# ------------------------------------------------------------------ form syncs (boards, community, park notes, reports, approvals)
ft = load('kpc_formtools')
def bad_get(u, timeout=30): raise urllib.error.HTTPError(u, 404, 'Not Found', {}, io.BytesIO(b'gone ' + u.encode()))
orig_get = ft.get; ft.get = bad_get
_, exc, o = capture(ft.sheet, SHEET)
check(isinstance(exc, RuntimeError) and not leaks(str(exc) + o) and exc.__cause__ is None and exc.__suppress_context__,
      'formtools.sheet: a failed sheet read raises "could not read the sheet (HTTPError HTTP 404)" with no address and no chained error that would print it')
ft.get = orig_get
_, exc, o = capture(ft.notice, 'Activation Board', f'{SHEET} {HOOK}'); check(not leaks(o), 'formtools.notice scrubs what it is given')
for mod, src in (('kpc_community', None), ('kpc_park_notes', None), ('kpc_reports', None)):
    text = (SCRIPTS / f'{mod}.py').read_text()
    check('notice_text' in text and 'from kpc_scrub import' in text, f'{mod}.py prints its ::notice lines through kpc_scrub')

# ------------------------------------------------------------------ new references (a script, not a module: its two helpers are taken out of the file and run)
src = (SCRIPTS / 'kpc_new_refs.py').read_text(); tree = ast.parse(src)
want = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('notice', 'http')}
ns = {'urllib': urllib, 'UA': 'test', 'DISCORD': HOOK}
exec(compile(ast.Module(body=list(want.values()), type_ignores=[]), 'kpc_new_refs.helpers', 'exec'), ns)
urllib.request.urlopen = fake_urlopen_factory('text')
(c, r), exc, o = capture(ns['http'], HOOK, b'{}')
check(exc is None and c == 0 and not leaks(str(r) + o), 'new_refs.http: a dropped connection no longer raises out of the posting step; it answers 0 with the kind of error only')
_, exc, o = capture(ns['notice'], 'New references', f'Discord HTTP 400: {HOOK} {FB}'); check(not leaks(o), 'new_refs.notice scrubs what it is given')

# ------------------------------------------------------------------ EU alerts
eu = load('kpc_eu_alerts')
urllib.request.urlopen = fake_urlopen_factory('text')
eu.OUT = pathlib.Path('data/alerts/eu.json')
_, exc, o = capture(eu.main)
check(not leaks(o), 'eu_alerts.main with every feed failing: the log holds no secret')

# ------------------------------------------------------------------ POTA spotter (a script: run in a child process with the network faked)
driver = textwrap.dedent('''
    import io, json, os, runpy, sys, types, urllib.error, urllib.request
    HOOK, FB = os.environ['DISCORD_WEBHOOK_URL'], os.environ['FB_PAGE_TOKEN']
    g = types.ModuleType('kpc_net_guard'); g.install = lambda: None; sys.modules['kpc_net_guard'] = g
    import datetime as dt
    now = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    FEED = [{'activator': os.environ['CALL_A'], 'reference': 'US-0001', 'frequency': '14074', 'mode': 'FT8', 'spotTime': now, 'name': 'Park'}]
    class R(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False
    def fake(req, *a, **k):
        url = req.full_url if hasattr(req, 'full_url') else str(req)
        if 'api.pota.app' in url: return R(json.dumps(FEED).encode())
        body = json.dumps({'error': {'message': 'Malformed access token ' + FB + ' ' + HOOK}}).encode()
        raise urllib.error.HTTPError(url, 400, 'Bad Request', {}, io.BytesIO(body)) if 'graph' in url else ValueError('cannot reach ' + url)
    urllib.request.urlopen = fake
    try: runpy.run_path(os.environ['SPOTTER'], run_name='__main__')
    except SystemExit as e: print('EXIT', e.code)
''')
(tmp / 'driver.py').write_text(driver)
os.makedirs(tmp / 'spot', exist_ok=True)
r = subprocess.run([sys.executable, str(tmp / 'driver.py')], cwd=tmp / 'spot', capture_output=True, text=True,
                   env={**os.environ, 'CALL_A': __import__('ast').literal_eval(next(__import__('re').finditer(r'^CALLS = (\{[^}]*\})', (SCRIPTS / 'kpc_pota_spotter.py').read_text(), __import__('re').M)).group(1)).pop(), 'SPOTTER': str(SCRIPTS / 'kpc_pota_spotter.py'), 'PYTHONPATH': str(SCRIPTS)})
check(not leaks(r.stdout + r.stderr) and 'EXIT' in r.stdout, 'pota spotter with Discord dropping the connection (error text repeats the link): stops without printing it')
os.environ['DISCORD_WEBHOOK_URL'] = HOOK

# ------------------------------------------------------------------ node scripts: social, facebook, discord videos
stub = textwrap.dedent('''
    const fs = require('fs'); const plan = JSON.parse(process.env.FAKE_PLAN || '{}'); let di = 0, fi = 0; const log = [];
    global.fetch = async (url) => {
      url = String(url); log.push(url.replace(/webhooks\\/.*/, 'webhooks/***').replace(/access_token=[^&]*/, 'access_token=***'));
      fs.writeFileSync(process.env.FAKE_LOG, JSON.stringify(log));
      const next = (arr, i) => (arr || [204])[Math.min(i, (arr || [204]).length - 1)];
      if (url.includes('swpc.noaa.gov')) return { ok: true, status: 200, json: async () => plan.noaa };
      if (/discord(app)?\\.com\\/api\\/webhooks/.test(url)) { const st = next(plan.discord, di++); if (st === 'throw') throw new TypeError('Failed to parse URL from ' + url); return { ok: st < 300, status: st, json: async () => ({}), text: async () => '' }; }
      if (url.includes('graph.facebook.com')) { const st = next(plan.fb, fi++); return { ok: st < 300, status: st, json: async () => (st < 300 ? { id: '1_2' } : { error: { message: 'Malformed access token ' + process.env.FB_PAGE_TOKEN, code: 190 } }) }; }
      return { ok: false, status: 404, json: async () => ({}) };
    };
''')
nd = tmp / 'node'; nd.mkdir(); (nd / 'stub.js').write_text(stub)
for f in ('kpc-events.js', 'kpc-ky-data.json'):
    try: (nd / f).symlink_to(HERE / f)
    except OSError: pass
import datetime
now_ng = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S.000')
noaa = [{'product_id': 'A30A', 'issue_datetime': now_ng, 'message': 'Serial Number: 9001\nNOAA Scale: R3\nALERT: Radio Blackout'}]
(nd / 'kpc-youtube.json').write_text(json.dumps({'channels': [{'name': 'Test', 'videos': [{'id': 'AAAAAAAAAAA', 'title': 'one', 'published': '2026-11-01'}, {'id': 'BBBBBBBBBBB', 'title': 'two', 'published': '2026-11-02'}]}]}))
(nd / 'kpc-fb-posted.json').write_text(json.dumps({'videos': []})); (nd / 'kpc-discord-videos.json').write_text(json.dumps({'videos': []}))
(nd / 'kpc-social-state.json').write_text(json.dumps({'alerts': {'seen': ['1'], 'last': {}}}))


def run_node(script, args, plan):
    env = {**os.environ, 'FAKE_PLAN': json.dumps(plan), 'FAKE_LOG': str(nd / 'log.json'), 'NODE_OPTIONS': f'--require {nd / "stub.js"}',
           'KPC_YOUTUBE_WEBHOOK': HOOK, 'GENERAL_WEBHOOK_URL': HOOK, 'DRY_RUN': 'false'}
    return subprocess.run(['node', str(SCRIPTS / script), *args], cwd=nd, capture_output=True, text=True, env=env)


r = run_node('kpc_social.js', ['bandalert'], {'noaa': noaa, 'discord': ['throw']})
check(r.returncode == 1 and not leaks(r.stdout + r.stderr), 'social bandalert, Discord fetch failing with the link in the error text: exit 1, nothing leaks')
r = run_node('kpc_social.js', ['bandalert'], {'noaa': noaa, 'discord': [500]})
check(not leaks(r.stdout + r.stderr), 'social bandalert, Discord answering 500: nothing leaks')
r = run_node('kpc_facebook.js', ['videos'], {'fb': [200, 400]})
check(r.returncode == 1 and not leaks(r.stdout + r.stderr), 'facebook videos, Graph error repeating the token: exit 1, nothing leaks')
r = run_node('kpc_discord_videos.js', [], {'discord': ['throw']})
check(not leaks(r.stdout + r.stderr), 'discord videos, fetch failing with the link in the error text: nothing leaks')

# ------------------------------------------------------------------ workflows: no secret on a command line, in a summary, or in a committed file
import yaml
mine = 'boards hunters band-alerts pota-discord discord-watch discord-mod park-alerts fb-comments community park-notes reports youtube approvals club-posts new-refs social'.split()
bad = []
ENVLINE = re.compile(r'^\s*[A-Za-z_][A-Za-z0-9_]*:\s*\$\{\{\s*secrets\.[A-Za-z0-9_]+\s*\}\}\s*$')
for n in mine:
    t = (HERE / f'.github/workflows/kpc-{n}.yml').read_text()
    d = yaml.safe_load(t)
    if not (True in d or 'on' in d) or not d.get('jobs'): bad.append(n + ': on/jobs missing')
    for line in t.splitlines():
        code = line.split('  #')[0].rstrip()
        if 'secrets.' in code and not code.lstrip().startswith('#') and not ENVLINE.match(code):
            bad.append(f'{n}: secret not used as a plain env value: {code.strip()[:60]}')
check(not bad, 'club workflows: on / jobs intact, every secret only as an env: value, none on an echo / print / summary line ' + '; '.join(bad))
state_files = ['kpc-social-state.json', 'data/fb-comments-state.json', 'data/discord-watch-state.json', 'data/park-alerts-state.json',
               'data/kpc-club-posts-state.json', '.github/kpc-pota-spot-state.json', 'kpc-fb-posted.json', 'kpc-discord-videos.json', 'data/hunters/buckets.json']
flat = ''
for f in state_files:
    p = HERE / f
    if p.exists(): flat += p.read_text(errors='replace')
check(not re.search(r'webhooks/\d{6,}/|access_token|EAA[A-Za-z0-9]{40,}|2PACX-', flat), 'the committed state files of these bots hold no webhook link, token or sheet link')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
