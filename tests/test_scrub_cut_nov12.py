#!/usr/bin/env python3
"""Offline test (Nov 12 2026, Quality must-fix on package E): a secret cut off in the middle never reaches a log line.

Quality showed that `notice(f'... {str(e)[:160]}')` cut the text BEFORE kpc_scrub saw it, so a secret cut in the middle no longer
matched its whole value and its first part printed (Discord bot token 35 chars, FB_PAGE_TOKEN 28, NPS key 20, YouTube key 19,
GH token 20). Checked here:
  1. kpc_scrub.scrub / kpc_scrub.js hide a leading (and a trailing) piece of 8+ characters of each secret, URL-encoded copies too,
     and a webhook link pasted without its https:// cut in the middle; a link's public start alone is left as it is
  2. clip(text, n) scrubs first, then cuts
  3. no bot script cuts an error / answer text before it is scrubbed (the str(e)[:n] / r[:n] / .decode()[:n] shapes are gone)
  4. the real call sites (park alerts, Discord watch, club posts, new references) with an answer whose secret falls across the cut
  5. FB_PAGE_ID is a secret name, LOOKS catches *_PASS, and the JS NAMES list equals the Python one
Nothing here touches the network (urlopen is a fake); the made-up values are built at run time."""
import ast, contextlib, importlib, io, json, os, pathlib, re, subprocess, sys, tempfile, urllib.error, urllib.parse, urllib.request

HERE = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = HERE / '.github/scripts'
sys.path.insert(0, str(SCRIPTS))
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


# made-up secrets in the real shapes, assembled at run time
BOT = 'M' + 'TAxMjM0NTY3ODkwMTIzNDU2' + '.' + 'GaBcDe' + '.' + 'FAKEbotTOKENabcdefghijklmnop0123456789'
FB = 'EA' + 'AGm0PX4ZCpsBAOZ' + 'FAKEpageTOKEN0123456789abcdefghijklmnopqrstuv'
NPS = 'FAKEnps' + 'KEY0123456789abcdefghijklmnopqrstu'
YT = 'AI' + 'za' + 'SyFAKEyoutubeKEY0123456789abcdefgh'
GH = 'gh' + 'p_' + 'FAKEghTOKEN0123456789abcdefghijklmnop'
HOOK = 'https://discord' + '.com/api/' + 'webhooks/' + '123456789012345678/' + 'FAKEhookTOKEN' + 'abcdefghijklmnopqrstuvwxyz012345'
PAGE_ID = '1029384756' + '102938'
ENV = {'DISCORD_BOT_TOKEN': BOT, 'FB_PAGE_TOKEN': FB, 'NPS_API_KEY': NPS, 'YOUTUBE_API_KEY': YT, 'GH_TOKEN': GH,
       'KPC_DISCORD_WEBHOOK': HOOK, 'KPC_ADMIN_WEBHOOK': HOOK, 'KPC_PARKS_WEBHOOK': HOOK, 'DISCORD_WEBHOOK_URL': HOOK,
       'FB_PAGE_ID': PAGE_ID}
for k, v in ENV.items(): os.environ[k] = v
CUTS = [('Discord bot token', BOT, 35), ('FB_PAGE_TOKEN', FB, 28), ('NPS key', NPS, 20), ('YouTube key', YT, 19), ('GH token', GH, 20)]
TOKENS = [BOT, FB, NPS, YT, GH, HOOK.rsplit('/', 1)[1]]


def leaks(text):
    """any whole secret, or any 8+ character leading / trailing piece of one, in text"""
    return [s[:4] + '...' for s in TOKENS if s[:8] in text or s[-8:] in text]


import kpc_scrub as S

# ------------------------------------------------------------------ 1. the scrubber
for label, sec, n in CUTS:
    piece = sec[:n]
    for shape in (f'bad token {piece}', f'{{"error":{{"message":"(#190) bad token {piece}', f'x {urllib.parse.quote(sec, safe="")[:n]}'):
        out = S.scrub(shape)
        check(not leaks(out) and piece not in out, f'scrub hides a {label} cut at {n} characters ({shape[:20]}...)')
    tail = sec[-12:]
    check(not leaks(S.scrub('ends with ' + tail)), f'scrub hides the last 12 characters of a {label} (a text cut from the front)')
check(S.scrub('id 1234567 ok') == 'id 1234567 ok', 'a piece shorter than 8 characters that only looks like a secret start is left alone')
check(S.scrub('see https://discord.com/api/webhooks/ for help') == 'see https://discord.com/api/webhooks/ for help',
      "a webhook link's public start on its own is left alone (only a piece that reaches the secret part is hidden)")
os.environ['KPC_GENERAL_WEBHOOK'] = HOOK.replace('https://', '')        # Quality's demo: a webhook pasted without https://
try:
    urllib.request.Request(os.environ['KPC_GENERAL_WEBHOOK'])
except Exception as e:  # noqa: BLE001
    out = S.notice_text(f'Could not post: {str(e)[:80]}')
    check('FAKEhook' not in out and '123456789012345678/' not in out, f"Quality's demo: a pasted webhook cut at 80 then scrubbed shows nothing ({out})")
del os.environ['KPC_GENERAL_WEBHOOK']
body = '{"error":{"message":"(#100) bad token ' + FB + '","type":"OAuthException"}}'
check(not leaks(S.scrub(body[:60])), "Quality's demo: a Facebook body cut at 60 then scrubbed shows no piece of FB_PAGE_TOKEN")

# ------------------------------------------------------------------ 2. clip = scrub first, then cut
pad = 'x' * 150
for label, sec, n in CUTS:
    c = S.clip(pad + ' ' + sec + ' tail', 151 + n)
    check(not leaks(c) and len(c) <= 151 + n, f'clip scrubs before it cuts ({label})')
check(S.clip(b'bytes ' + FB.encode(), 40).startswith('bytes ***'), 'clip takes a raw HTTP body (bytes) too')
check(S.clip(ValueError('boom ' + GH), 200) == 'boom ***', 'clip takes an exception (its text)')

# ------------------------------------------------------------------ 5. names
check('FB_PAGE_ID' in S.NAMES, 'FB_PAGE_ID is in kpc_scrub NAMES')
check(bool(S.LOOKS.search('RELAY_SMTP_PASS')) and bool(S.LOOKS.search('SOME_PASSWORD')), 'LOOKS catches *_PASS as well as *PASSWORD')
check(not leaks(S.scrub('page ' + PAGE_ID)) and PAGE_ID not in S.scrub('page ' + PAGE_ID), 'the Facebook page id is hidden')
js = (SCRIPTS / 'kpc_scrub.js').read_text(encoding='utf-8')
js_names = re.findall(r"'([A-Z0-9_]+)'", js[js.index('const NAMES'):js.index('];', js.index('const NAMES'))])
check(js_names == list(S.NAMES), f'the JS NAMES list equals the Python one ({len(js_names)} / {len(S.NAMES)})')
check(S.LOOKS.pattern in js.replace('\\/', '/'), 'the JS LOOKS pattern equals the Python one')

# ------------------------------------------------------------------ 1+2 in node
cases = [sec[:n] for _, sec, n in CUTS] + [sec[-12:] for _, sec, _ in CUTS] + [urllib.parse.quote(FB, safe='')[:30], body[:60]]
node = subprocess.run(['node', '-e', "const s=require(process.argv[1]);const c=JSON.parse(process.env.CASES);"
                       "process.stdout.write(JSON.stringify({o:c.map(x=>s.scrub('a '+x)),k:s.clip('x'.repeat(150)+' '+process.env.FB_PAGE_TOKEN, 170),"
                       "h:s.scrub('see https://discord.com/api/webhooks/ for help')}))", str(SCRIPTS / 'kpc_scrub.js')],
                      capture_output=True, text=True, env={**os.environ, 'CASES': json.dumps(cases)})
try: res = json.loads(node.stdout)
except Exception: res = {'o': ['?'], 'k': '?', 'h': '?'}  # noqa: BLE001
check(node.returncode == 0 and all(not leaks(o) for o in res['o']) and len(res['o']) == len(cases),
      f'kpc_scrub.js hides the same cut-off pieces ({len(cases)} cases) {node.stderr[:200]}')
check(not leaks(res['k']) and res['h'] == 'see https://discord.com/api/webhooks/ for help', 'kpc_scrub.js clip scrubs first; a public link start is left alone')

# ------------------------------------------------------------------ 3. no cut-then-scrub shape left in the bots
BOTS = ['kpc_club_posts.py', 'kpc_discord_mod.py', 'kpc_discord_watch.py', 'kpc_eu_alerts.py', 'kpc_fb_comments.py', 'kpc_new_refs.py',
        'kpc_park_alerts.py', 'kpc_pota_spotter.py', 'kpc_community.py', 'kpc_formtools.py', 'kpc_hunters.py', 'kpc_park_notes.py', 'kpc_reports.py']
bad = []
for f in BOTS:
    for i, ln in enumerate((SCRIPTS / f).read_text(encoding='utf-8').splitlines(), 1):
        if re.search(r'str\(e\)\[:\d+\]|\{r\[:\d+\]\}|\.decode\([^)]*\)\[:\d+\]|\.read\(\)\[:\d+\]|_error\'\)\)\[:\d+\]|message\'\)\)\[:\d+\]', ln):
            bad.append(f'{f}:{i}')
check(not bad, f'no bot cuts an error or answer text before scrubbing it ({bad[:6]})')


# ------------------------------------------------------------------ 4. the real call sites, secret falling across the cut
def capture(fn, *a, **k):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try: res = fn(*a, **k)
        except BaseException as e: res = e  # noqa: BLE001
    return res, out.getvalue() + err.getvalue()


def refuse_with(prefix_len, secret):
    def fake(req, *a, **k):
        url = req.full_url if hasattr(req, 'full_url') else str(req)
        body = ('{"message":"' + 'y' * prefix_len + ' ' + secret + '","code":50035}').encode()
        raise urllib.error.HTTPError(url, 400, 'Bad Request', {}, io.BytesIO(body))
    return fake


def fail_with(text):
    def fake(req, *a, **k): raise ValueError(text)
    return fake


real = urllib.request.urlopen
tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp); (tmp / 'data').mkdir()
try:
    pa = importlib.import_module('kpc_park_alerts')
    pa.DISCORD, pa.FB_ID, pa.FB_TOKEN, pa.STAFF = HOOK, PAGE_ID, FB, HOOK
    pa.POSTS_PAUSED_UNTIL = '2000-01-01'
    # 'Discord HTTP {c}: {r[:200]}' cut the body at 200: put the token across that cut
    urllib.request.urlopen = refuse_with(200 - 12 - 1 - 20, FB)
    _, o = capture(pa.post_discord, 'a', 'b'); check(not leaks(o), 'park_alerts.post_discord: a token across the 200-character cut does not print')
    _, o = capture(pa.post_staff, 'a', 'b'); check(not leaks(o), 'park_alerts.post_staff: same')
    urllib.request.urlopen = refuse_with(200 - 12 - 1 - 25, NPS)
    _, o = capture(pa.post_facebook, 'a', 'b'); check(not leaks(o), 'park_alerts.post_facebook: an API key across the cut does not print')

    dw = importlib.import_module('kpc_discord_watch')
    urllib.request.urlopen = refuse_with(200 - 9 - 12 - 10, BOT)
    r, o = capture(dw.call, 'channels/1/messages')
    check(isinstance(r, dict) and not leaks(json.dumps(r) + o), 'discord_watch.call: a bot token across the 200-character cut of an HTTP error is hidden')
    dw.HOOK = HOOK
    urllib.request.urlopen = fail_with('y' * (200 - 1 - 20) + ' ' + GH)   # str(e)[:200] keeps the first 20 characters
    _, o = capture(dw.say, 't', 'x'); check(not leaks(o), "discord_watch.say: 'Could not post: {str(e)[:200]}' with a GH token across the cut")
    urllib.request.urlopen = refuse_with(160 - 12 - 1 - 35, BOT)
    _, o = capture(dw.say, 't', 'x'); check(not leaks(o), 'discord_watch.say: an HTTP refusal with a bot token across the 160-character cut')

    cp = importlib.import_module('kpc_club_posts')
    cp.FB_ID, cp.FB_TOKEN = PAGE_ID, FB
    urllib.request.urlopen = refuse_with(160 - 12 - 15, YT)
    for name in ('to_discord', 'to_facebook'):
        fn = getattr(cp, name, None)
        if fn is None: continue
        try: _, o = capture(fn, ('KPC_PARKS_WEBHOOK',), 't', 'b') if name == 'to_discord' else capture(fn, 'b')
        except Exception as e: o = str(e)  # noqa: BLE001
        check(not leaks(o), f'club_posts.{name}: a YouTube key across the 160-character cut does not print')

    nr_src = (SCRIPTS / 'kpc_new_refs.py').read_text(encoding='utf-8')
    tree = ast.parse(nr_src)
    uses = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, 'id', '') == 'clip']
    check(len(uses) >= 2 and any(isinstance(n, ast.FunctionDef) and n.name == 'clip' for n in tree.body),
          'new_refs: the Discord / Facebook refusals go through clip (scrub first, then cut)')
finally:
    urllib.request.urlopen = real

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
