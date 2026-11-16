#!/usr/bin/env python3
"""Nov 14: park alerts read each host only as its robots.txt allows, 2 s apart, and a skipped source keeps its alerts.

1. robots.txt Disallow (fw.ky.gov, by our User-Agent token; www.landbetweenthelakes.us for everyone) -> not read, items kept.
2. robots.txt 5xx (www.fs.usda.gov) and unreachable (landbetweenthelakes.us) -> host not read this run, items kept.
3. robots.txt 404 (parks.ky.gov) -> read.
4. The keyed Park Service API: robots.txt never asked, still paced.
5. At least 2 s between requests to one host (virtual clock); a longer Crawl-delay is obeyed; Crawl-delay over 30 s = not read.
6. Three runs in a row of skipped sources never count their alerts as gone (the two-check rule cannot clear them).
7. The run's notice names the skipped hosts and why.

Offline: urlopen is a fake, time.sleep / time.monotonic are a virtual clock; temp dir only.
"""
import contextlib, io, json, os, pathlib, sys, tempfile, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
ok = True


def check(cond, msg):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


clock = {'t': 5000.0}
time.monotonic = lambda: clock['t']
def fake_sleep(s): clock['t'] += s
time.sleep = fake_sleep

ROBOTS = {
    'parks.ky.gov': 404,
    'www.fs.usda.gov': 503,
    'landbetweenthelakes.us': 'down',
    'www.landbetweenthelakes.us': b'User-agent: *\nDisallow: /\n',
    'fw.ky.gov': b'User-agent: KPC\nDisallow: /Alerts/\n\nUser-agent: *\nAllow: /\n',
    'slow.example.gov': b'User-agent: *\nCrawl-delay: 5\n',
    'crawl.example.gov': b'User-agent: *\nCrawl-delay: 60\n',
}
PAGES = {
    'https://parks.ky.gov/api/default/alerts?$top=100': json.dumps({'value': [{'Id': '1', 'Title': 'Trail closed', 'Text': 'A trail is closed.'}]}).encode(),
    'https://developer.nps.gov/api/v1/alerts?stateCode=KY&limit=200': json.dumps({'data': []}).encode(),
    'https://slow.example.gov/a': b'ok', 'https://slow.example.gov/b': b'ok',
}
calls = []
def fake_urlopen(req, *a, **k):
    u = req.full_url
    calls.append((u, clock['t']))
    clock['t'] += 0.1
    host = urllib.parse.urlsplit(u).netloc
    if u.endswith('/robots.txt'):
        r = ROBOTS.get(host, 404)
        if r == 'down': raise urllib.error.URLError('unreachable')
        if isinstance(r, int): raise urllib.error.HTTPError(u, r, 'x', {}, io.BytesIO(b''))
        return io.BytesIO(r)
    if u in PAGES: return io.BytesIO(PAGES[u])
    raise AssertionError('unexpected request ' + u)
urllib.request.urlopen = fake_urlopen

os.environ['NPS_API_KEY'] = 'test-key'
for k in ('KPC_PARKS_WEBHOOK', 'KPC_ADMIN_WEBHOOK', 'KPC_DISCORD_WEBHOOK', 'FB_PAGE_ID', 'FB_PAGE_TOKEN', 'DRY_RUN'): os.environ.pop(k, None)
tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
import kpc_park_alerts as pa  # noqa: E402


def new_run():
    pa._robots.clear(); pa._no_host.clear(); pa.SKIPPED.clear(); calls.clear()


def rec(t): return {'who': 'x', 'title': t, 'text': t, 'link': 'x', 'first': '2026-11-01', 'runs': 2, 'missing': 0, 'announced': True, 'routine': False, 'refs': []}
OLD = {'ky-1': rec('Trail closed'), 'fs-a': rec('Forest road closed'), 'lbl-b': rec('LBL road closed'), 'kdfwr-c': rec('Ramp closed')}
pa.STATE_F.parent.mkdir(parents=True, exist_ok=True)
pa.STATE_F.write_text(json.dumps({'updated': '2026-11-13 10:00', 'sources': ['fs', 'kdfwr', 'ky', 'lbl', 'nps'], 'seen': OLD}))

outs = ''
for run in range(3):
    new_run()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): pa.main()
    outs += buf.getvalue()
    if run == 0: first = list(calls)
seen = json.loads(pa.STATE_F.read_text())['seen']
urls = [u for u, _ in first]
check('https://parks.ky.gov/robots.txt' in urls and 'https://parks.ky.gov/api/default/alerts?$top=100' in urls, 'robots 404 (parks.ky.gov): read')
check(not any('developer.nps.gov/robots.txt' in u for u in urls) and any('developer.nps.gov/api/' in u for u in urls), 'keyed Park Service API: robots never asked, API read')
check(not any(u.startswith('https://www.fs.usda.gov/') and not u.endswith('/robots.txt') for u in urls), 'robots 5xx (www.fs.usda.gov): host not read')
check(not any(u.startswith('https://fw.ky.gov/Alerts') for u in urls), 'robots Disallow for our token (fw.ky.gov): not read')
check(not any('landbetweenthelakes.us/' in u and not u.endswith('/robots.txt') for u in urls), 'robots Disallow / unreachable (both LBL hosts): not read')
check(sum(u.endswith('/robots.txt') for u in urls) == len(set(u for u in urls if u.endswith('/robots.txt'))), 'robots.txt read once per host per run')
for aid in ('fs-a', 'lbl-b', 'kdfwr-c'):
    check(seen.get(aid) == OLD[aid], f'{aid}: skipped source, item and counters unchanged after 3 runs')
check(seen.get('ky-1', {}).get('missing') == 0, 'ky-1 still seen (its source was read)')
check('Not read this run' in outs and 'www.fs.usda.gov: robots.txt answered 503' in outs and 'fw.ky.gov: robots.txt disallows /Alerts/' in outs
      and 'landbetweenthelakes.us: robots.txt unreadable' in outs, 'the notice names the skipped hosts and why')
check(not any(m in outs for m in ('looks open', 'open again')), 'nothing announced as reopened')

# a source only partly skipped: LBL's Forest Service page skipped (fs.usda.gov 503), its own site answers with nothing
ROBOTS['www.landbetweenthelakes.us'] = 404; ROBOTS['landbetweenthelakes.us'] = 404
PAGES.update({'https://www.landbetweenthelakes.us/alerts/': b'<html></html>', 'https://landbetweenthelakes.us/alerts/': b'<html></html>',
              'https://landbetweenthelakes.us/wp-json/wp/v2/posts?per_page=20&categories_slug=alerts': b'[]',
              'https://landbetweenthelakes.us/wp-json/wp/v2/posts?per_page=20&search=alert': b'[]',
              'https://landbetweenthelakes.us/alerts/feed/': b'<rss></rss>', 'https://landbetweenthelakes.us/feed/': b'<rss></rss>'})
for run in range(3):
    new_run()
    with contextlib.redirect_stdout(io.StringIO()): pa.main()
seen2 = json.loads(pa.STATE_F.read_text())['seen']
check(any(u == 'https://www.landbetweenthelakes.us/alerts/' for u, _ in calls), 'partly skipped LBL: its own site was read')
check(seen2.get('lbl-b') == OLD['lbl-b'], 'partly skipped LBL answering with nothing: lbl-b kept, counters unchanged after 3 runs')

# pacing: every host 2 s apart, a 5 s Crawl-delay obeyed, 60 s Crawl-delay = not read
by = {}
for u, t in first: by.setdefault(urllib.parse.urlsplit(u).netloc, []).append(t)
check(all(b - a >= 2.0 - 1e-9 for ts in by.values() for a, b in zip(ts, ts[1:])) and len(by['parks.ky.gov']) == 2, 'at least 2 s between requests to one host (robots read included)')
new_run()
pa.fetch('https://slow.example.gov/a'); pa.fetch('https://slow.example.gov/b')
ts = [t for u, t in calls if not u.endswith('robots.txt')]
check(ts[1] - ts[0] >= 5.0 - 1e-9, 'Crawl-delay 5 s obeyed (longer than our 2 s)')
try:
    pa.fetch('https://crawl.example.gov/a'); check(False, 'Crawl-delay 60 s: not read')
except pa.Skipped:
    check(not any(u == 'https://crawl.example.gov/a' for u, _ in calls), 'Crawl-delay 60 s: not read this run')
t0 = clock['t']; pa.gate('https://developer.nps.gov/api/v1/x'); pa.gate('https://developer.nps.gov/api/v1/y')
check(clock['t'] - t0 >= 2.0 - 1e-9, 'keyed API still gets the 2 s gap')

# Nov 15: ONE robots.txt rule everywhere = the store engine 3.6.2 rule (401 / 403 = "unavailable" = no rules; a plain web page = no
# rules; a sign-in page, 429 = not read this run)
ROBOTS.update({'a401.example.gov': 401, 'a403.example.gov': 403, 'a429.example.gov': 429, 'a410.example.gov': 410,
               'page.example.gov': b'<!DOCTYPE html><html><body><h1>Welcome</h1></body></html>',
               'signin.example.gov': b'<html><body><form action="/login"><input type="password" name="p"></form></body></html>',
               'inpage.example.gov': b'<html><pre>User-agent: *\nDisallow: /a</pre></html>'})
for h in ('a401', 'a403', 'a429', 'a410', 'page', 'signin', 'inpage'): PAGES[f'https://{h}.example.gov/a'] = b'ok'
for h, want, what in (('a401', True, '401 = no rules (read)'), ('a403', True, '403 = no rules (read)'), ('a410', True, '410 = no file (read)'),
                      ('a429', False, '429 = not read this run'), ('page', True, 'an ordinary web page = no rules (read)'),
                      ('signin', False, 'a sign-in page = not read this run'), ('inpage', False, 'a page holding robots directives: its Disallow is obeyed')):
    new_run()
    try: pa.fetch(f'https://{h}.example.gov/a'); got = True
    except pa.Skipped: got = False
    check(got == want and (got == any(u == f'https://{h}.example.gov/a' for u, _ in calls)), f'robots.txt {what} (store engine 3.6.2 rule)')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
