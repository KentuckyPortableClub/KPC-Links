#!/usr/bin/env python3
"""One shared, fail-closed network guard (owner rule, 2026-11-10): no bot process contacts services*.arcgis.com, apps.fs.usda.gov
or ncnhde.natureserve.org: not data, not robots.txt, not HEAD, not a redirect hop. Port / user@ / trailing-dot forms are the same
host; KPC_SAVED_ONLY_HOSTS only ADDS hosts; an https -> http (or ftp:/file:) hop is refused. Offline: a 127.0.0.1 stand-in server."""
import http.client, http.server, os, pathlib, socket, subprocess, sys, tempfile, threading, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
S = ROOT / '.github/scripts'
sys.path.insert(0, str(S))
for k in [k for k in os.environ if k.lower() in ('http_proxy', 'https_proxy', 'all_proxy', 'no_proxy')]: os.environ.pop(k)   # the stand-in is local
os.environ.pop('KPC_SAVED_ONLY_HOSTS', None)
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


def raises(exc, fn, *a, **k):
    try: fn(*a, **k)
    except exc: return True
    except Exception as e: print('   (raised', type(e).__name__, str(e)[:120], ')'); return False  # noqa: BLE001
    return False


# every DNS lookup / socket attempt is recorded; anything not 127.0.0.1 counts as a leak
DIALS = []
_gai, _cc = socket.getaddrinfo, socket.create_connection
def gai(host, *a, **k):
    DIALS.append(('dns', host))
    if host not in ('127.0.0.1', 'localhost'): raise OSError('test: no network')
    return _gai(host, *a, **k)
def cc(addr, *a, **k):
    DIALS.append(('tcp', addr[0]))
    if addr[0] not in ('127.0.0.1', 'localhost'): raise OSError('test: no network')
    return _cc(addr, *a, **k)
socket.getaddrinfo, socket.create_connection = gai, cc
leaks = lambda: [d for d in DIALS if d[1] not in ('127.0.0.1', 'localhost')]

import kpc_net_guard as G   # noqa: E402
import kpc_master as M      # noqa: E402

# --- 1) the bypass forms are refused, by the shared check and by kpc_master.live_ok
BAD = ['https://services1.arcgis.com:443/x', 'https://u@services1.arcgis.com/x', 'https://services1.arcgis.com./x',
       'https://apps.fs.usda.gov:443/x', 'https://u:p@apps.fs.usda.gov./x', 'https://Services7.ArcGIS.com/robots.txt',
       'https://services-eu1.arcgis.com/x', 'https://services.arcgis.com/33TOOklri9xpic7U/arcgis/rest/services/x',
       'https://ncnhde.natureserve.org/', 'svc:https://services3.arcgis.com/a/FeatureServer|layer', 'https://services1%2earcgis.com/x']
for u in BAD:
    check(f'refused by the guard: {u}', not G.host_ok(u)[0])
    check(f'refused by kpc_master.live_ok: {u}', not M.live_ok(u)[0])
for u in ('//services1.arcgis.com/x', 'services1.arcgis.com/x', '', 'https:///x', 'ftp://example.org/x', 'file:///etc/hosts', 'data:,x'):
    check(f'fail closed (no plain http(s) host): {u!r}', not G.host_ok(u)[0] and not M.live_ok(u)[0])
for u in ('https://api.pota.app/park/US-0001', 'https://raw.githubusercontent.com/o/r/main/x.json', 'https://www.sciencebase.gov/catalog/item/x',
          'https://kygisserver.ky.gov/arcgis/rest/services/x/MapServer/0', 'https://hub.arcgis.com/api/x', 'https://www.arcgis.com/sharing/rest/x'):
    check(f'allowed: {u}', G.host_ok(u)[0] and M.live_ok(u)[0])

# --- 2) KPC_SAVED_ONLY_HOSTS adds hosts; it never drops a default one (kpc_master read in a fresh process)
code = ("import sys; sys.path.insert(0, sys.argv[1]); import kpc_master as M, kpc_net_guard as G; "
        "print(M.live_ok('https://apps.fs.usda.gov/x')[0], M.live_ok('https://services1.arcgis.com/x')[0], M.live_ok('https://gis.example.net/x')[0], "
        "G.host_ok('https://apps.fs.usda.gov/x')[0], G.host_ok('https://gis.example.net/x')[0], 'apps.fs.usda.gov' in M.SAVED_ONLY_HOSTS)")
r = subprocess.run([sys.executable, '-B', '-c', code, str(S)], capture_output=True, text=True, env=dict(os.environ, KPC_SAVED_ONLY_HOSTS='gis.example.net'))
check('KPC_SAVED_ONLY_HOSTS=gis.example.net: apps.fs.usda.gov and services1 stay refused, the extra host is refused too',
      r.stdout.split() == ['False', 'False', 'False', 'False', 'False', 'True'])
if r.returncode: print(r.stderr[-500:])

# --- 3) importing kpc_host_pace / kpc_http_cache / kpc_master installs the guard (fresh process each)
for mod in ('kpc_host_pace', 'kpc_http_cache', 'kpc_master'):
    r = subprocess.run([sys.executable, '-B', '-c', f"import sys; sys.path.insert(0, sys.argv[1]); import kpc_net_guard as G; a = G.installed(); import {mod}; print(a, G.installed())", str(S)],
                       capture_output=True, text=True)
    check(f'importing {mod} installs the guard', r.stdout.split() == ['False', 'True'])

# --- 4) a 127.0.0.1 server that redirects to a forbidden host: refused before any DNS lookup or connection
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self): self._go()
    def do_HEAD(self): self._go()
    def _go(self):
        to = {'/to-services': 'https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/x/FeatureServer/0?f=json',
              '/to-port': 'https://services2.arcgis.com:443/x', '/to-dot': 'https://apps.fs.usda.gov./robots.txt',
              '/to-ftp': 'ftp://example.org/x', '/to-rel': '//services9.arcgis.com/robots.txt'}.get(self.path)
        if to: self.send_response(302); self.send_header('Location', to); self.end_headers(); return
        self.send_response(200); self.send_header('Content-Type', 'text/plain'); self.end_headers()
        if self.command == 'GET': self.wfile.write(b'ok')


srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{srv.server_address[1]}'
check('the stand-in answers through urlopen (allowed host still works)', urllib.request.urlopen(base + '/plain', timeout=10).read() == b'ok')
for p in ('/to-services', '/to-port', '/to-dot', '/to-ftp', '/to-rel'):
    n0 = len(leaks())
    check(f'urlopen: redirect {p} refused', raises(G.NetGuardRefused, lambda: urllib.request.urlopen(base + p, timeout=10).read()))
    check(f'build_opener: redirect {p} refused (robots.txt / HEAD path)',
          raises(G.NetGuardRefused, lambda: urllib.request.build_opener().open(urllib.request.Request(base + p, method='HEAD'), timeout=10)))
    check(f'kpc_master checked opener: redirect {p} refused', raises(M.LiveNotAllowed, lambda: M.host_checked_opener().open(base + p, timeout=10)))
    check(f'redirect {p}: no DNS lookup or connection to any host but 127.0.0.1', len(leaks()) == n0)
check('direct urlopen of a forbidden host: refused, nothing dialled',
      raises(G.NetGuardRefused, urllib.request.urlopen, 'https://services5.arcgis.com/robots.txt', timeout=5) and not leaks())
check('http.client to a forbidden host: refused before DNS',
      raises(G.NetGuardRefused, lambda: http.client.HTTPSConnection('services1.arcgis.com.', 443, timeout=5).request('HEAD', '/robots.txt')) and not leaks())
check('a refusal is an ordinary failed read for an `except Exception` / URLError handler', issubclass(G.NetGuardRefused, urllib.error.URLError))
srv.shutdown()

# --- 5) https -> http (or another scheme) hop refused
req = urllib.request.Request('https://gis.example.org/a')
check('stdlib redirect handler: https -> http refused', raises(G.NetGuardRefused, urllib.request.HTTPRedirectHandler().redirect_request, req, None, 302, 'Found', {}, 'http://gis.example.org/b'))
check('kpc_master _CheckedRedirect: https -> http refused', raises(M.LiveNotAllowed, M._CheckedRedirect(lambda u: None).redirect_request, req, None, 302, 'Found', {}, 'http://gis.example.org/b'))
check('kpc_master _CheckedRedirect: https -> ftp refused', raises(M.LiveNotAllowed, M._CheckedRedirect(lambda u: None).redirect_request, req, None, 302, 'Found', {}, 'ftp://gis.example.org/b'))
check('an https -> https hop on an allowed host is still followed', M._CheckedRedirect(lambda u: None).redirect_request(req, None, 302, 'Found', {}, 'https://gis.example.org/b') is not None)

# --- 6) the 2-fer bundle cache: a refused read never starts the fetch (or its retry waits) and is never kept
import kpc_http_cache as HC   # noqa: E402
with tempfile.TemporaryDirectory() as t:
    HC.DIR = t; calls = []
    u = 'https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/W/FeatureServer/0/query'
    check('cache: a refused host raises before fetch() is called', raises(G.NetGuardRefused, HC.cached, u, {'f': 'json'}, lambda: calls.append(1) or {'features': []}) and not calls)
    check('cache: nothing written for a refused read', not any(pathlib.Path(t).rglob('*.gz')))
    p = HC._path(u, {'f': 'json'}); p.parent.mkdir(parents=True, exist_ok=True)
    import gzip, json, time  # noqa: E401,E402
    p.write_bytes(gzip.compress(json.dumps({'features': [1]}).encode())); os.utime(p, (time.time() - 99 * 86400,) * 2)
    n0 = len(leaks()); real = urllib.request.urlopen; opened = []
    urllib.request.urlopen = lambda *a, **k: opened.append(a) or real(*a, **k)
    try: HC.cached(u, {'f': 'json'}, lambda: {'features': []})
    except G.NetGuardRefused: pass
    urllib.request.urlopen = real
    check('cache: the layer edit-date request is never made to a refused host', not opened and len(leaks()) == n0)
    HC.DIR = ''
    check('cache off: a refused host still raises before fetch()', raises(G.NetGuardRefused, HC.cached, u, {}, lambda: calls.append(1)) and not calls)
    check('cache: an allowed host is fetched as before', HC.cached('https://gis.example.org/x/MapServer/0/query', {}, lambda: {'ok': 1}) == {'ok': 1})

# --- 7) the research inbox: every services*.arcgis.com host is saved-copy only (no robots.txt request)
import kpc_research_inbox as RI   # noqa: E402
class _B: offline, rb = False, {}
for u in ('https://services2.arcgis.com/x/FeatureServer/0', 'https://services9.arcgis.com:443/x/FeatureServer/0', 'https://u@services1.arcgis.com./x/FeatureServer/0'):
    okk, why = RI.Reader.allowed(_B(), u)
    check(f'research inbox refuses {u} with no robots.txt request', not okk and 'saved copy only' in why and not _B.rb)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
