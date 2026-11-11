#!/usr/bin/env python3
"""kpc_net_guard.py: one process-wide, fail-closed check before ANY bot request (data, robots.txt, HEAD, every redirect hop).

Never contacted, by any bot process: services.arcgis.com / servicesN.arcgis.com / services-<region>.arcgis.com (the Grant County
org lives there too), apps.fs.usda.gov and ncnhde.natureserve.org (saved copies only). KPC_SAVED_ONLY_HOSTS adds hosts to this
list; it can never remove one. Only plain http(s) addresses are allowed; a redirect from https to anything else is refused.

install() (idempotent) wraps urllib.request.OpenerDirector.open (urlopen, build_opener openers and every redirect hop go through
it), HTTPRedirectHandler.redirect_request (scheme downgrade) and http.client.HTTPConnection.connect (the host the socket really
opens, before any DNS lookup). kpc_host_pace, kpc_http_cache and kpc_master call install() when they are imported.
Not a rule file: it never decides a join. Standard library only.
"""
import http.client, json, os, re, sys, urllib.error, urllib.parse, urllib.request

SERVICES_RE = re.compile(r'^services(?:\d+|-[a-z0-9]+)?\.arcgis\.com$')
NEVER = frozenset({'apps.fs.usda.gov', 'ncnhde.natureserve.org'})   # plus SERVICES_RE (hard-coded: an env list cannot drop them)
_STATE = {'installed': False}
# data/outlines/layers.json rows with "never_contact": true: no request of any kind to that layer's service (its host + the path
# up to /MapServer or /FeatureServer). KPC_LAYERS_JSON points at another copy (tests). Missing file = no flags; an unreadable or
# malformed file refuses every request (fail closed).
LAYERS_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'outlines', 'layers.json')
_FLAGS = {}


class NetGuardRefused(urllib.error.URLError):
    """A request the host rules forbid. A URLError (an OSError), so a caller's ordinary 'read failed' handling applies."""


def _norm_host(h):
    h = urllib.parse.unquote(str(h or '')).strip().lower()
    try: h = h.encode('idna').decode('ascii').lower()   # a full-width dot is a dot to the resolver
    except Exception: pass  # noqa: BLE001
    return h.strip('[]').rstrip('.')


def _addr(url):
    u = str(getattr(url, 'full_url', url) or '').strip()
    return (u[4:] if u.startswith('svc:') else u).split('|')[0]   # kpc_master's 'svc:<url>|<layer>' form


def host_of(url):
    """The host a request to url really reaches, lowercased, no port / user / trailing dot. '' when there is none."""
    u = _addr(url)
    try: return _norm_host(urllib.parse.urlsplit(u).hostname)
    except ValueError: return ''


def extra_hosts():
    return {_norm_host(h) for h in str(os.environ.get('KPC_SAVED_ONLY_HOSTS') or '').split(',') if h.strip()}


def _service_path(url):
    p = urllib.parse.unquote(urllib.parse.urlsplit(url).path or '/').lower().rstrip('/')
    m = re.search(r'/(mapserver|featureserver|imageserver)(/|$)', p)
    return p[:m.start()] if m else p


def never_contact_flags(path=None):
    """{(host, service path)} for layers.json rows with never_contact true. Raises ValueError when the file cannot be read."""
    path = path or os.environ.get('KPC_LAYERS_JSON') or LAYERS_JSON
    try: st = os.stat(path)
    except FileNotFoundError: return frozenset()
    except OSError as e: raise ValueError(f'{path}: {e}')
    key = (path, st.st_mtime_ns, st.st_size)
    if key not in _FLAGS:
        try:
            d = json.load(open(path, encoding='utf-8'))
            rows = (d.get('layers') or {}).values()
            _FLAGS.clear()
            _FLAGS[key] = frozenset((host_of(r['url']), _service_path(_addr(r['url'])))
                                    for r in rows if isinstance(r, dict) and r.get('never_contact') is True and r.get('url'))
        except Exception as e:  # noqa: BLE001
            raise ValueError(f'{path}: cannot read the never_contact flags ({e})')
    return _FLAGS[key]


def flag_rule(url):
    """'' unless url reaches a layer flagged never_contact in layers.json (or the flags cannot be read)."""
    try: flags = never_contact_flags()
    except ValueError as e: return f'{e}: refused (fail closed)'
    u = _addr(url); host, path = host_of(u), urllib.parse.unquote(urllib.parse.urlsplit(u).path or '/').lower()
    for h, p in flags:
        if host == h and (path.rstrip('/') == p or path.startswith(p.rstrip('/') + '/')):
            return f'{h}{p}: never_contact in data/outlines/layers.json, no request of any kind to that service'
    return ''


def host_rule(host):
    """'' when host may be contacted, else why not."""
    host = _norm_host(host)
    if not host: return 'no host in the address: refused'
    if SERVICES_RE.match(host): return f'{host}: services*.arcgis.com is never contacted, robots.txt included'
    if host in NEVER or host in extra_hosts(): return f'{host}: saved copies only, never contacted by a bot'
    return ''


def host_ok(url):
    """(True, '') or (False, why). Fail closed: not plain http(s), no host, or a forbidden host = refused."""
    u = _addr(url)
    try: scheme = urllib.parse.urlsplit(u).scheme.lower()
    except ValueError: scheme = ''
    if scheme not in ('http', 'https'): return False, f'{u[:80]}: only http(s) addresses are allowed'
    why = host_rule(host_of(u)) or flag_rule(u)
    return (False, why) if why else (True, '')


def check(url, hop_from=None):
    """Raise NetGuardRefused unless url may be requested. hop_from = the address that redirected here (https -> http refused)."""
    ok, why = host_ok(url)
    if not ok: raise NetGuardRefused(why)
    if hop_from is not None and urllib.parse.urlsplit(str(getattr(hop_from, 'full_url', hop_from))).scheme.lower() == 'https' \
            and urllib.parse.urlsplit(str(getattr(url, 'full_url', url))).scheme.lower() != 'https':
        raise NetGuardRefused(f'{str(url)[:80]}: redirect from https to a plain address refused')
    return True


def _check_req(req):
    check(req)
    if isinstance(req, urllib.request.Request):   # the host urllib itself will dial (it unquotes; it keeps user@ and :port)
        why = host_rule(re.sub(r':\d*$', '', str(req.host or '').rsplit('@', 1)[-1]))
        if why: raise NetGuardRefused(why)


def install():
    """Wrap the urllib opener, the redirect handler and http.client once per process."""
    if _STATE['installed']: return
    o_open = urllib.request.OpenerDirector.open
    o_redir = urllib.request.HTTPRedirectHandler.redirect_request
    o_conn = http.client.HTTPConnection.connect

    def open_(self, fullurl, *a, **k):
        _check_req(fullurl)
        return o_open(self, fullurl, *a, **k)

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        newurl = urllib.parse.urljoin(req.full_url, newurl)
        check(newurl, hop_from=req.full_url)
        return o_redir(self, req, fp, code, msg, headers, newurl)

    def connect(self):
        why = host_rule(getattr(self, '_tunnel_host', None) or self.host)
        if why: raise NetGuardRefused(why)
        return o_conn(self)
    open_.__wrapped__, redirect_request.__wrapped__, connect.__wrapped__ = o_open, o_redir, o_conn
    urllib.request.OpenerDirector.open = open_
    urllib.request.HTTPRedirectHandler.redirect_request = redirect_request
    http.client.HTTPConnection.connect = connect
    _STATE['installed'] = True


def installed(): return _STATE['installed']


def _selftest():
    bad = ['https://services1.arcgis.com:443/x', 'https://u@services1.arcgis.com/x', 'https://services1.arcgis.com./x',
           'https://apps.fs.usda.gov:443/x', 'https://SERVICES9.arcgis.com/robots.txt', 'https://services-eu1.arcgis.com/x',
           'https://services.arcgis.com/33TOOklri9xpic7U/x', 'http://ncnhde.natureserve.org/', 'svc:https://services2.arcgis.com/a|b',
           'https://services1%2earcgis.com/x', '//services1.arcgis.com/x', 'services1.arcgis.com/x', '', 'ftp://example.org/x',
           'file:///etc/passwd', 'data:,x', 'https:///x']
    good = ['https://api.pota.app/park/US-0001', 'https://raw.githubusercontent.com/a/b', 'https://www.sciencebase.gov/x',
            'https://kygisserver.ky.gov/arcgis/rest/services/x', 'https://hub.arcgis.com/x', 'http://127.0.0.1:8000/x']
    fails = [u for u in bad if host_ok(u)[0]] + [u for u in good if not host_ok(u)[0]]
    try: check('http://example.org/x', hop_from='https://example.org/'); fails.append('downgrade allowed')
    except NetGuardRefused: pass
    old = os.environ.get('KPC_SAVED_ONLY_HOSTS')
    os.environ['KPC_SAVED_ONLY_HOSTS'] = 'example.net'
    if host_ok('https://apps.fs.usda.gov/x')[0] or host_ok('https://example.net/x')[0]: fails.append('env list not additive')
    if old is None: os.environ.pop('KPC_SAVED_ONLY_HOSTS', None)
    else: os.environ['KPC_SAVED_ONLY_HOSTS'] = old
    install(); install()
    try: urllib.request.build_opener().open('https://services3.arcgis.com/robots.txt', timeout=1); fails.append('opener not guarded')
    except NetGuardRefused: pass
    try: http.client.HTTPSConnection('apps.fs.usda.gov', 443, timeout=1).connect(); fails.append('http.client not guarded')
    except NetGuardRefused: pass
    for f in fails: print('SELFTEST FAIL', f)
    print('kpc_net_guard selftest:', 'FAIL' if fails else 'ok', f'({len(bad) + len(good) + 4} cases)')
    return 1 if fails else 0


if __name__ == '__main__':
    if '--selftest' in sys.argv: sys.exit(_selftest())
    for a in sys.argv[1:]: print(a, host_ok(a))
