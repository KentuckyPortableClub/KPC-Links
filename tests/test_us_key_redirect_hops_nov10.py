#!/usr/bin/env python3
"""Nov 10 (Quality on #117): the US key's layer count (count_query) and layer read (fetch_geo) go through the master's
checked-redirect opener (kpc_master.checked_opener / _CheckedRedirect). Every redirect hop gets saved_only (saved-copy-only and
never-contact hosts), live_ok, and that host's robots.txt before it is requested. A hop to a services*.arcgis.com host, the
Grant County NM org, or ncnhde.natureserve.org is refused and never asked; a hop to an allowed host passes.

Offline: execs the helpers from kpc_us_key.py (importing it would run the builder) with a stand-in http(s) handler.
"""
import email, io, pathlib, re, sys, types, urllib.parse, urllib.request, urllib.response, urllib.error, json, os

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as KMASTER  # noqa: E402
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


class Stand(urllib.request.BaseHandler):
    """{url: (status, headers, body)}; anything else 404. Records every address asked."""
    handler_order = 100
    def __init__(self, routes): self.routes, self.calls = routes, []
    def https_open(self, req):
        u = req.full_url; self.calls.append(u)
        st, hd, body = self.routes.get(u, (404, {}, b''))
        r = urllib.response.addinfourl(io.BytesIO(body), email.message_from_string(''.join(f'{k}: {v}\n' for k, v in hd.items())), u, st)
        r.msg = 'stand-in'; return r
    http_open = https_open


def chunk(a, b): return src[src.index(a):src.index(b)]


ns = {'urllib': urllib, 'json': json, 're': re, 'os': os, 'KMASTER': KMASTER, 'DETAIL': 0.001, 'PREC': 5, 'PAGE': 200}
code = (chunk('SAVED_ONLY_HOSTS = ', 'SAVED_ONLY_SKIPPED') + chunk('NEVER_HOSTS = ', 'def notice(') + chunk('def layer_page_size', 'FWS = '))
exec(compile(code, 'kpc_us_key.py', 'exec'), ns)
check('count_query and fetch_geo use checked_open (no plain urlopen left in them)',
      'urlopen' not in chunk('def count_query', 'def fetch_geo') and 'urlopen' not in chunk('def fetch_geo', 'FWS = ')
      and 'checked_open(req' in chunk('def count_query', 'def fetch_geo') and 'checked_open(req' in chunk('def fetch_geo', 'FWS = ')
      and 'KMASTER.checked_opener(_hop_ok' in chunk('def checked_open', 'def count_query'))

LAY = 'https://gis.example.gov/arcgis/rest/services/x/MapServer/0/query'
BAD = (('services2.arcgis.com', 'https://services2.arcgis.com/AbC/arcgis/rest/services/x/FeatureServer/0/query'),
       ('services-eu1.arcgis.com', 'https://services-eu1.arcgis.com/AbC/arcgis/rest/services/x/FeatureServer/0/query'),
       ('the Grant County NM org', 'https://services.arcgis.com/33TOOklri9xpic7U/arcgis/rest/services/Parcels/FeatureServer/0/query'),
       ('ncnhde.natureserve.org', 'https://ncnhde.natureserve.org/arcgis/rest/services/x/MapServer/0/query'),
       ('apps.fs.usda.gov (saved copy only)', 'https://apps.fs.usda.gov/arcx/rest/services/x/MapServer/0/query'))
CQ = {'where': '1=1', 'geometry': '1,2,3,4', 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects'}
GQ = dict(CQ, outFields='OBJECTID', returnGeometry='true', outSR=4326, f='json', resultOffset=0)


def first_url(q, count):
    c = {k: q[k] for k in ns['CQ_KEEP'] if k in q}
    if count: c.update({'returnCountOnly': 'true', 'returnGeometry': 'false', 'f': 'json'}); return LAY + '?' + urllib.parse.urlencode(c)
    return None


for name, target in BAD:
    host = urllib.parse.urlsplit(target).netloc
    # count_query: the first address is fixed; it answers with a 302 to the forbidden host
    st = Stand({'https://gis.example.gov/robots.txt': (404, {}, b''), first_url(CQ, True): (302, {'Location': target + '?returnCountOnly=true&f=json'}, b'')})
    ns['HOP_HANDLERS'] = (st,); ns['HOP_ROBOTS'].clear()
    c = ns['count_query'](LAY, CQ)
    check(f'count_query: a 302 to {name} is refused (no count) and {host} is never asked, robots.txt included',
          c is None and not any(host in u for u in st.calls) and len(st.calls) == 1)
    # fetch_geo: every page address gets the same 302
    class Redir(Stand):
        def https_open(self, req):
            if req.full_url.startswith(LAY): self.calls.append(req.full_url); return super().https_open(types.SimpleNamespace(full_url='__302__'))
            return super().https_open(req)
    st = Redir({'__302__': (302, {'Location': target + '?f=json'}, b'')})
    ns['HOP_HANDLERS'] = (st,); ns['HOP_ROBOTS'].clear()
    try: ns['fetch_geo'](LAY, GQ); refused = False
    except KMASTER.LiveNotAllowed: refused = True
    except Exception as e: refused = 'redirect refused' in str(e)  # noqa: BLE001
    check(f'fetch_geo: a 302 to {name} is refused (both outline tries) and {host} is never asked, robots.txt included',
          refused and not any(host in u for u in st.calls if not u.startswith(LAY)) and not any(host in u for u in st.calls))

# an allowed host passes: its robots.txt is read first, then the hop is followed
OK2 = 'https://gis2.example.gov/arcgis/rest/services/y/MapServer/0/query?returnCountOnly=true&f=json'
st = Stand({'https://gis.example.gov/robots.txt': (404, {}, b''), first_url(CQ, True): (302, {'Location': OK2}, b''),
            'https://gis2.example.gov/robots.txt': (404, {}, b''), OK2: (200, {}, b'{"count": 42}')})
ns['HOP_HANDLERS'] = (st,); ns['HOP_ROBOTS'].clear()
c = ns['count_query'](LAY, CQ)
check('count_query: a 302 to an allowed host passes after that host\'s robots.txt', c == 42 and st.calls == [first_url(CQ, True), 'https://gis2.example.gov/robots.txt', OK2])
# a hop the landing host's robots.txt disallows is refused
st = Stand({first_url(CQ, True): (302, {'Location': OK2}, b''), 'https://gis2.example.gov/robots.txt': (200, {}, b'User-agent: *\nDisallow: /arcgis/\n')})
ns['HOP_HANDLERS'] = (st,); ns['HOP_ROBOTS'].clear()
check('count_query: a 302 to a path the landing host\'s robots.txt disallows is refused', ns['count_query'](LAY, CQ) is None and OK2 not in st.calls)
st = Stand({first_url(CQ, True): (302, {'Location': OK2}, b''), 'https://gis2.example.gov/robots.txt': (403, {}, b'')})
ns['HOP_HANDLERS'] = (st,); ns['HOP_ROBOTS'].clear()
check('count_query: a robots.txt 403 on the landing host is a no', ns['count_query'](LAY, CQ) is None and OK2 not in st.calls)
# fetch_geo through an allowed hop returns the page
PG = 'https://gis2.example.gov/arcgis/rest/services/y/MapServer/0/query?page=1'
class Hop(Stand):
    def https_open(self, req):
        if req.full_url.startswith(LAY): self.calls.append(req.full_url); return super().https_open(types.SimpleNamespace(full_url='__302__'))
        return super().https_open(req)
st = Hop({'__302__': (302, {'Location': PG}, b''), 'https://gis2.example.gov/robots.txt': (404, {}, b''), PG: (200, {}, b'{"features": [{"attributes": {"OBJECTID": 1}}]}')})
ns['HOP_HANDLERS'] = (st,); ns['HOP_ROBOTS'].clear()
j, pg = ns['fetch_geo'](LAY, GQ)
check('fetch_geo: a 302 to an allowed host passes after that host\'s robots.txt', len(j['features']) == 1 and 'https://gis2.example.gov/robots.txt' in st.calls)
# a robots.txt that itself redirects to a forbidden host is refused, never asked
st = Stand({first_url(CQ, True): (302, {'Location': OK2}, b''), 'https://gis2.example.gov/robots.txt': (302, {'Location': 'https://services9.arcgis.com/robots.txt'}, b'')})
ns['HOP_HANDLERS'] = (st,); ns['HOP_ROBOTS'].clear()
check('robots.txt of a hop that redirects to a services*.arcgis.com host: refused, never asked', ns['count_query'](LAY, CQ) is None and not any('services9' in u for u in st.calls))

if __name__ == '__main__':
    sys.exit(0 if ok else 1)
