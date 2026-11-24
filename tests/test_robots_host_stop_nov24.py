#!/usr/bin/env python3
"""24 Nov 2026 (club rule R-NET1; review of #368): a data request that answers 401 / 403 / 429 stops that host for the run,
in kpc_master.http_fetcher and kpc_leadtest.polite_open. A robots.txt that cannot be parsed = not this run.
Invented hosts only. Nothing here contacts a server. Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import io, pathlib, socket, sys, urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
socket.socket.connect = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('no network in tests'))
import kpc_master as M  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


class _Pace:
    def wait(self, host): pass


calls = []


class _Resp(io.BytesIO):
    status = 200
    def __enter__(self): return self
    def __exit__(self, *a): return False


class _Opener:
    def open(self, req, timeout=60):
        u = req.full_url
        calls.append(u)
        if u.endswith('/robots.txt'): return _Resp(b'User-agent: *\nAllow: /\n')
        raise urllib.error.HTTPError(u, 403, 'Forbidden', {}, None)


M.live_ok = lambda url: (True, '')
M.checked_opener = lambda check, handlers=(): _Opener()
M.host_checked_opener = lambda handlers=(): _Opener()
M.time.sleep = lambda s: None
fetch = M.http_fetcher(pacer=_Pace(), max_tries=3)
try:
    fetch('https://gis.invented.gov/arcgis/rest/services/A/MapServer/0/query'); first = 'no error'
except M.LiveNotAllowed as e:
    first = str(e)
n1 = len([c for c in calls if 'query' in c])
try:
    fetch('https://gis.invented.gov/arcgis/rest/services/B/MapServer/0/query'); second = 'no error'
except M.LiveNotAllowed as e:
    second = str(e)
n2 = len([c for c in calls if 'query' in c])
check('a data request answering 403 is not retried (asked once)', n1 == 1 and 'stopped for this run' in first)
check('the next request to that host is not sent at all', n2 == 1 and 'stopped for this run' in second)

class _Bad:
    def __str__(self): raise UnicodeError('cannot read')   # a body that cannot be read as rules


check('a robots.txt that cannot be parsed = not this run', M.robots_allows('https://x.invented.gov/a', lambda u: (200, _Bad()), {}) is False)
check('a robots.txt 403 = no rules = allowed', M.robots_allows('https://y.invented.gov/a', lambda u: (403, ''), {}) is True)

src = (ROOT / '.github/scripts/kpc_master.py').read_text(encoding='utf-8')
check("no line says a robots 403 is a no", 'a 403 = no)' not in src and 'says no / 403' not in src and '403 counts as no' not in src)

import kpc_leadtest as L  # noqa: E402
L.kpc_net_guard.host_ok = lambda url: (True, '')
L.robots_ok = lambda url: True
L._pace = lambda host: None
sent = []
def _uo(req, timeout=20):
    sent.append(req.full_url)
    raise urllib.error.HTTPError(req.full_url, 429, 'Too Many', {}, None)
L.urllib.request.urlopen = _uo
for u in ('https://hub.invented.gov/a', 'https://hub.invented.gov/b'):
    try: L.polite_open(L.urllib.request.Request(u))
    except Exception as e: last = e  # noqa: BLE001
check('leadtest: after a 429 the host is left for the run', len(sent) == 1 and isinstance(last, L.NotAsked))
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
