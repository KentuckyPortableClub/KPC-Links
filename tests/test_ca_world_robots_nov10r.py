#!/usr/bin/env python3
"""kpc_ca_key.py and kpc_world_key.py follow the US key's live-read rule (owner rule, 2026-11-10): every live read goes through
checked_open: host rules first (a saved-only / never-contact host gets NO request, robots.txt included), then robots.txt
(kpc_master.robots_allows: 401 / 403 / 5xx = no; 404 / 410 = no file, allowed) for the first address AND every redirect hop,
paced per host. Offline: an in-process stand-in server (an https handler); sockets are switched off."""
import io, json, os, pathlib, socket, sys, types, urllib.error, urllib.parse, urllib.request, urllib.response
import email.message

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / '.github/scripts'))


def _off(*a, **k): raise OSError('network disabled in this test')


socket.socket.connect = _off; socket.create_connection = _off
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


LOG, PACED, SLEPT = [], [], []
ROBOTS = {}      # host -> robots.txt status (200 text 'User-agent: *\nAllow: /' when 200)
MOVE = {}        # host -> host a data request is redirected to


class Stand(urllib.request.HTTPSHandler):
    def https_open(self, req):
        p = urllib.parse.urlsplit(req.full_url); LOG.append((p.netloc, p.path))
        h = email.message.Message()
        if p.path == '/robots.txt':
            st = ROBOTS.get(p.netloc, 404); body = b'User-agent: *\nAllow: /\n' if st == 200 else b''
        elif p.netloc in MOVE:
            st, body = 302, b''; h['Location'] = req.full_url.replace(p.netloc, MOVE[p.netloc], 1)
        else:
            st, body = 200, json.dumps({'features': [], 'count': 0}).encode()
        r = urllib.response.addinfourl(io.BytesIO(body), h, req.full_url, st); r.msg = 'stand-in'
        return r


def setup(ns):
    ns['HOP_HANDLERS'] = (Stand(),)
    ns['kpc_host_pace'] = types.SimpleNamespace(host_of=lambda u: urllib.parse.urlsplit(str(u)).netloc.lower(), wait=lambda h: PACED.append(h))
    ns['time'] = types.SimpleNamespace(sleep=lambda s: SLEPT.append(s), monotonic=lambda: 0.0, time=lambda: 0.0, strftime=lambda *a: '2026-11-10')
    ns['ROBOTS'].clear()


CA_SRC = (ROOT / '.github/scripts/kpc_ca_key.py').read_text(encoding='utf-8')
WK_SRC = (ROOT / '.github/scripts/kpc_world_key.py').read_text(encoding='utf-8')
ca = types.ModuleType('ca'); ca.__dict__['__file__'] = str(ROOT / '.github/scripts/kpc_ca_key.py')
exec(compile(CA_SRC.split('\nrecs = cload()')[0], 'kpc_ca_key.py', 'exec'), ca.__dict__)
wk = {'__name__': 'kpc_world_key_test', '__file__': str(ROOT / '.github/scripts/kpc_world_key.py')}
exec(compile(WK_SRC.split('\nfor cc in COUNTRIES:')[0], 'kpc_world_key.py', 'exec'), wk)
sys.excepthook = sys.__excepthook__
CA_GET = lambda u: ca.get(u, {'where': '1=1', 'f': 'json'}, tries=3)
W_GET = lambda u: wk['fetch'](u + '?where=1%3D1&f=json', tries=3)

for name, ns, read in (('Canada', ca.__dict__, CA_GET), ('world', wk, W_GET)):
    for st, allowed in ((403, False), (401, False), (503, False), (404, True), (410, True), (200, True)):
        setup(ns); LOG.clear(); PACED.clear(); ROBOTS.clear(); MOVE.clear(); SLEPT.clear()
        host = f'gis{st}.example.gc.ca'; ROBOTS[host] = st
        try: read(f'https://{host}/arcgis/rest/services/x/MapServer/0/query'); err = None
        except Exception as e: err = e  # noqa: BLE001
        data = [x for x in LOG if x[1] != '/robots.txt']
        if allowed:
            check(f'{name}: robots.txt {st} = allowed: the layer is read after robots.txt ({LOG}), paced ({PACED})',
                  err is None and LOG[0] == (host, '/robots.txt') and len(data) == 1 and PACED.count(host) == 2)
        else:
            check(f'{name}: robots.txt {st} = NOT allowed: the layer is blocked, no data request ({err})',
                  err is not None and 'robots.txt' in str(err) and LOG == [(host, '/robots.txt')] and not SLEPT)   # no retry waits either
    # saved-only / never-contact hosts: no request at all, robots.txt included
    for u in ('https://apps.fs.usda.gov/arcx/rest/services/x/MapServer/0/query', 'https://services7.arcgis.com/abc/arcgis/rest/services/x/FeatureServer/0/query'):
        setup(ns); LOG.clear(); PACED.clear()
        try: ns['checked_open'](urllib.request.Request(u), 30); err = None
        except Exception as e: err = e  # noqa: BLE001
        try: read(u); err2 = None
        except Exception as e: err2 = e  # noqa: BLE001
        check(f'{name}: {urllib.parse.urlsplit(u).netloc} (saved copy only): refused with no request, robots.txt included ({err})',
              err is not None and err2 is not None and LOG == [] and PACED == [])
    # a redirect hop: its own robots.txt is asked before it is followed
    setup(ns); LOG.clear(); PACED.clear(); MOVE.clear(); ROBOTS.clear()
    MOVE['first.example.gc.ca'] = 'second.example.gc.ca'; ROBOTS['second.example.gc.ca'] = 403
    try: read('https://first.example.gc.ca/arcgis/rest/services/x/MapServer/0/query'); err = None
    except Exception as e: err = e  # noqa: BLE001
    check(f"{name}: a redirect hop's robots.txt is asked; 403 = the hop is not followed ({LOG})",
          err is not None and ('second.example.gc.ca', '/robots.txt') in LOG and not any(x[0] == 'second.example.gc.ca' and x[1] != '/robots.txt' for x in LOG))
    setup(ns); LOG.clear(); PACED.clear(); ROBOTS.clear()
    ROBOTS['second.example.gc.ca'] = 404
    try: read('https://first.example.gc.ca/arcgis/rest/services/x/MapServer/0/query'); err = None
    except Exception as e: err = e  # noqa: BLE001
    check(f"{name}: a hop whose robots.txt allows is followed and paced ({LOG}; {PACED})",
          err is None and ('second.example.gc.ca', '/robots.txt') in LOG and ('second.example.gc.ca', '/arcgis/rest/services/x/MapServer/0/query') in LOG
          and PACED.count('second.example.gc.ca') == 2)
    setup(ns); LOG.clear(); MOVE.clear(); MOVE['first.example.gc.ca'] = 'services2.arcgis.com'
    try: read('https://first.example.gc.ca/arcgis/rest/services/x/MapServer/0/query'); err = None
    except Exception as e: err = e  # noqa: BLE001
    check(f'{name}: a hop onto a never-contact host is refused without any request to it ({err})',
          err is not None and not any(x[0] == 'services2.arcgis.com' for x in LOG))

for fn, src in (('kpc_ca_key.py', CA_SRC), ('kpc_world_key.py', WK_SRC)):
    check(f'{fn}: no plain urlopen left (every live read is checked_open)', 'urllib.request.urlopen(' not in src and 'def checked_open(req, timeout):' in src)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
