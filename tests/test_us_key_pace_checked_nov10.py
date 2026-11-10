#!/usr/bin/env python3
"""Nov 10 (Quality on #117, v2): the US key reads the network ONLY through checked_open (the master's checked-redirect opener),
and every checked request is paced by kpc_host_pace: the first address, each redirect hop and each hop's robots.txt wait 2 s per
host. The checked opener does not go through urllib.request.urlopen, so the import-time urlopen wrap alone no longer paced it.

1. No bare urlopen / urllib.request.urlopen call is left in kpc_us_key.py (AST scan), and the PAD-US reads (get, fields), the
   layer resolve and the zipped-layer download (zip_state) all use checked_open.
2. With the real kpc_host_pace on a virtual clock: the first request waits, a redirect hop to the same host waits a full 2 s,
   a hop to a new host is paced after its robots.txt (also paced), and a refused hop (services*.arcgis.com) is never paced or asked.
3. get() (PAD-US) goes through the checked opener and the pacer, and a refused host is not retried.

Offline: execs the helpers from kpc_us_key.py (importing it would run the builder) with a stand-in http(s) handler.
"""
import ast, email, io, json, os, pathlib, re, sys, types, urllib.error, urllib.parse, urllib.request, urllib.response

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as KMASTER  # noqa: E402
import kpc_host_pace  # noqa: E402
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


def chunk(a, b): return src[src.index(a):src.index(b)]


# 1. no bare urlopen left
bare = []
for node in ast.walk(ast.parse(src)):
    if isinstance(node, ast.Call):
        f = node.func
        if (isinstance(f, ast.Name) and f.id == 'urlopen') or (isinstance(f, ast.Attribute) and f.attr == 'urlopen'):
            bare.append(node.lineno)
    if isinstance(node, (ast.ImportFrom,)) and any(a.name == 'urlopen' for a in node.names):
        bare.append(node.lineno)
check(f'kpc_us_key.py: no bare urlopen / urllib.request.urlopen call left (found at lines {bare})', not bare)
check('kpc_us_key.py: no other raw transport (build_opener, requests, http.client) either',
      not re.search(r'\bbuild_opener\s*\(|^\s*import\s+requests|\bhttp\.client\b', src, re.M))
for name, a, b in (('get() (PAD-US)', 'def get(', '# ---------------- names'), ('fields() (PAD-US)', 'def fields(', 'PADVER = '),
                   ('resolve() (layer path)', 'def resolve(', 'def _num('), ('zip_state()', 'def zip_state(', 'def extra_state(')):
    check(f'{name} reads through checked_open', 'checked_open(' in chunk(a, b))
co = chunk('def checked_open', 'def count_query')
check('checked_open: saved_only + live_ok, then _pace, before the opener asks the first address',
      co.index('saved_only(u)') < co.index('KMASTER.live_ok(u)') < co.index('_pace(u)') < co.index('.open(req'))
ho = chunk('def _hop_ok', 'def checked_open')
check('_hop_ok: the hop is paced after its checks and robots.txt; the robots.txt read is paced too',
      ho.index('robots_allows') < ho.rindex('_pace(u)') and '_pace(ru)' in ho)


# 2. pacing on a virtual clock with the REAL kpc_host_pace
class Clock:
    def __init__(self): self.t = 1000.0; self.slept = []
    def monotonic(self): return self.t
    def sleep(self, s): self.slept.append(round(s, 3)); self.t += s
    def strftime(self, f): return '2026-11-10'


clk = Clock()
kpc_host_pace.time = clk   # the real per-host pacer, on the virtual clock
LOG = []


class Stand(urllib.request.BaseHandler):
    """{url: (status, headers, body)}; anything else 404. Logs (time, url) for every address asked."""
    handler_order = 100
    def __init__(self, routes): self.routes = routes
    def https_open(self, req):
        u = req.full_url; LOG.append((clk.t, u))
        st, hd, body = self.routes.get(u, (404, {}, b''))
        r = urllib.response.addinfourl(io.BytesIO(body), email.message_from_string(''.join(f'{k}: {v}\n' for k, v in hd.items())), u, st)
        r.msg = 'stand-in'; return r
    http_open = https_open


ns = {'urllib': urllib, 'json': json, 're': re, 'os': os, 'KMASTER': KMASTER, 'DETAIL': 0.001, 'PREC': 5, 'PAGE': 200,
      'time': clk, 'kpc_host_pace': kpc_host_pace, 'Q': 'https://padus.example.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'}
code = (chunk('SAVED_ONLY_HOSTS = ', 'SAVED_ONLY_SKIPPED') + chunk('NEVER_HOSTS = ', 'def notice(') + chunk('def get(', '# ---------------- names')
        + chunk('def layer_page_size', 'FWS = '))
exec(compile(code, 'kpc_us_key.py', 'exec'), ns)
UA = {'User-Agent': 'KPC (kentuckyportableclub.github.io)'}


def reset(routes):
    LOG.clear(); clk.slept.clear(); kpc_host_pace._last.clear(); ns['HOP_ROBOTS'].clear(); ns['HOP_HANDLERS'] = (Stand(routes),)


A = 'https://gis.example.gov/arcgis/rest/services/x/MapServer/0/query?f=json'
A2 = 'https://gis.example.gov/arcgis/rest/services/x2/MapServer/0/query?f=json'
B = 'https://gis2.example.gov/arcgis/rest/services/y/MapServer/0/query?f=json'

# two plain requests to one host: the second waits the full 2 s
reset({A: (200, {}, b'{"count": 1}')})
for _ in range(2):
    with ns['checked_open'](urllib.request.Request(A, headers=UA), 30) as r: r.read()
check('first request: two checked requests to one host are 2 s apart (the first address is paced)',
      len(LOG) == 2 and LOG[1][0] - LOG[0][0] >= 2.0 and clk.slept == [2.0])

# a redirect hop on the same host waits 2 s after the first request (robots.txt of that host read first, also paced)
reset({A: (302, {'Location': A2}, b''), 'https://gis.example.gov/robots.txt': (404, {}, b''), A2: (200, {}, b'{"count": 2}')})
with ns['checked_open'](urllib.request.Request(A, headers=UA), 30) as r: j = json.loads(r.read())
ts = [t for t, _ in LOG]
check('redirect hop, same host: first, robots.txt, hop each 2 s apart', j == {'count': 2} and [u for _, u in LOG] == [A, 'https://gis.example.gov/robots.txt', A2]
      and all(b - a >= 2.0 for a, b in zip(ts, ts[1:])))

# a hop to a new host: that host's robots.txt and the hop are 2 s apart; the first host's pace is untouched
reset({A: (302, {'Location': B}, b''), 'https://gis2.example.gov/robots.txt': (404, {}, b''), B: (200, {}, b'{"count": 3}')})
with ns['checked_open'](urllib.request.Request(A, headers=UA), 30) as r: j = json.loads(r.read())
d = dict((u, t) for t, u in LOG)
check('redirect hop, new host: its robots.txt then the hop, 2 s apart (the hop is paced)',
      j == {'count': 3} and d[B] - d['https://gis2.example.gov/robots.txt'] >= 2.0 and set(kpc_host_pace._last) == {'gis.example.gov', 'gis2.example.gov'})

# a refused hop: never paced, never asked
BAD = 'https://services7.arcgis.com/AbC/arcgis/rest/services/x/FeatureServer/0/query?f=json'
reset({A: (302, {'Location': BAD}, b'')})
try:
    ns['checked_open'](urllib.request.Request(A, headers=UA), 30); refused = False
except KMASTER.LiveNotAllowed: refused = True
check('a hop to services*.arcgis.com is refused, never paced, never asked (robots.txt included)',
      refused and [u for _, u in LOG] == [A] and 'services7.arcgis.com' not in kpc_host_pace._last)

# a refused FIRST address: never paced, never asked
for bad in (BAD, 'https://services.arcgis.com/33TOOklri9xpic7U/arcgis/rest/services/P/FeatureServer/0/query', 'https://ncnhde.natureserve.org/x?f=json'):
    reset({})
    try:
        ns['checked_open'](urllib.request.Request(bad, headers=UA), 30); refused = False
    except KMASTER.LiveNotAllowed: refused = True
    check(f'first address {urllib.parse.urlsplit(bad).netloc}: refused before any request or pace', refused and not LOG and not kpc_host_pace._last)

# a windowed walk: ten count/page reads to one host are paced 2 s each (the FL DEP case: ~400 reads, now >= 800 s, not 200 s)
reset({A: (200, {}, b'{"count": 1}')})
for _ in range(10):
    with ns['checked_open'](urllib.request.Request(A, headers=UA), 30) as r: r.read()
check('ten reads to one host take at least 18 s (2 s per host, not the old 0.5 s sleep)', LOG[-1][0] - LOG[0][0] >= 18.0)

# 3. get() (PAD-US) goes through the checked opener and the pacer
P1 = ns['Q'] + '?' + urllib.parse.urlencode({'where': '1=1', 'f': 'json'})
reset({P1: (200, {}, b'{"features": []}')})
g1 = ns['get']({'where': '1=1', 'f': 'json'}); g2 = ns['get']({'where': '1=1', 'f': 'json'})
check('get() (PAD-US): through checked_open, two reads paced 2 s apart', g1 == {'features': []} and len(LOG) == 2 and LOG[1][0] - LOG[0][0] >= 2.0)
ns['Q'] = 'https://services3.arcgis.com/AbC/arcgis/rest/services/x/FeatureServer/0/query'
reset({}); n_sleep = len(clk.slept)
try:
    ns['get']({'f': 'json'}); refused = False
except KMASTER.LiveNotAllowed: refused = True
check('get(): a refused host is not retried (no 8 s retry sleeps) and never asked', refused and not LOG and not clk.slept)

if __name__ == '__main__':
    sys.exit(0 if ok else 1)
