"""Nov 11 (page-size PR): the big map files are read on first need, once, from one address, and the results do not change.
Headless Chromium against a LOCAL server; every non-localhost request is aborted (and listed); Leaflet is the working
stand-in tests/leaflet_standin_nov11.js (the CDN is not reachable here). Not in kpc_full_suite.py (needs Chromium +
playwright), like the other *_browser tests. Run: python3 tests/pagesize_nov11_browser.py   Prints PASS / FAIL lines."""
import http.server, socketserver, threading, os, sys, time, json, re
from playwright.sync_api import sync_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PORT = int(os.environ.get('KPC_TEST_PORT', '8796'))
BASE = f'http://127.0.0.1:{PORT}/'
STAND = open(os.path.join(ROOT, 'tests', 'leaflet_standin_nov11.js'), 'rb').read()
CDN = re.compile(r'https://(unpkg\.com/leaflet@1\.9\.4/dist/|cdnjs\.cloudflare\.com/ajax/libs/leaflet/1\.9\.4/)')
KYF = ['ky-state-parks', 'ky-hunting-areas', 'ky-nature-preserves', 'ky-natural-areas', 'ky-dbnf-owned', 'ky-dbnf', 'ky-nps', 'ky-wild-rivers',
       'ky-wilderness', 'ky-fws', 'ky-usace', 'ky-padus-parks', 'ky-kpc-drawn']
BIG_US = ['/locations.json', '/data/canada.json', '/data/northam.json']
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def log_message(s, *a): pass
    def do_GET(s):
        p = s.path.split('?')[0]
        if p.startswith('/__cdn/'):
            b = b'' if p.endswith('.css') else STAND
            s.send_response(200); s.send_header('Content-Type', 'text/css' if p.endswith('.css') else 'application/javascript'); s.send_header('Content-Length', str(len(b))); s.end_headers(); s.wfile.write(b); return
        fp = os.path.join(ROOT, p.lstrip('/'))
        if not os.path.isfile(fp): s.send_error(404); return
        d = open(fp, 'rb').read()
        if fp.endswith('.html'):
            t = d.decode('utf8', 'replace'); t = CDN.sub('/__cdn/', t); t = re.sub(r'\sintegrity="[^"]*"', '', t); d = t.encode()
        st = os.stat(fp); tag = '"%x-%x"' % (int(st.st_mtime), len(d))
        if s.headers.get('If-None-Match') == tag: s.send_response(304); s.send_header('ETag', tag); s.end_headers(); return
        HITS.append(s.path)   # a real download (200), not a cache hit or a 304
        # the same caching headers GitHub Pages sends (10 minutes, with a validator), so 'downloaded once' is tested as members get it
        s.send_response(200); s.send_header('Content-Type', s.guess_type(fp)); s.send_header('Content-Length', str(len(d))); s.send_header('Cache-Control', 'max-age=600'); s.send_header('ETag', tag)
        s.send_header('Last-Modified', time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(st.st_mtime))); s.end_headers(); s.wfile.write(d)
HITS = []
class TS(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True
    def handle_error(self, *a): pass
fails = 0; OUTSIDE = set()
def ok(c, m):
    global fails
    print(('PASS ' if c else 'FAIL ') + m, flush=True)
    if not c: fails += 1
# Nov 11 (job 3 loaders, on top of this PR): the public pages read the RELEASED copy of each Kentucky file (data/released/ky/<name>,
# part 1 keeps the name; its ?v= is the file's own version from RELEASED.json, the same on every page). A check below that asks for
# '/ky-x.geojson' counts its released address; 'the shared address' is that released address.
_RI = json.load(open(os.path.join(ROOT, 'data/released/RELEASED.json'), encoding='utf-8'))
def REL(path):
    m = re.match(r'^/(ky-[a-z0-9-]+\.geojson)$', path)
    return '/data/released/ky/' + m.group(1) if m and ('ky/' + m.group(1)) in _RI.get('files', {}) else path
def ADDR(f): n = f + '.geojson'; return '/data/released/ky/' + n + '?v=' + _RI['files']['ky/' + n][0][1]
class Page:
    """one page in its own context: every same-origin request with its time (ms since navigation), and the load event time"""
    def __init__(s, b, url, w=1280, h=900, store=None, geo=None, wait=True):
        s.c = b.new_context(viewport={'width': w, 'height': h}, service_workers='block', **({'geolocation': geo, 'permissions': ['geolocation']} if geo else {}))
        if store: s.c.add_init_script('(' + json.dumps(store) + ').forEach(([k,v])=>{try{localStorage.setItem(k,v)}catch(e){}})')
        s.req = []; s.t0 = time.time(); s.h0 = len(HITS)
        # no page.route here: routing turns the browser's HTTP cache off, and 'downloaded once' must be tested with it on.
        # Every non-localhost request goes to the dead proxy (127.0.0.1:9, see launch) and fails; each one is listed.
        s.p = s.c.new_page(); s.p.on('request', lambda rq: OUTSIDE.add(re.sub(r'\?.*', '?...', rq.url)) if not rq.url.startswith(BASE) and not rq.url.startswith('data:') and not rq.url.startswith('blob:') else None); s.p.on('dialog', lambda d: d.dismiss()); s.errs = []; s.p.on('pageerror', lambda e: s.errs.append(str(e)[:160]))
        s.p.on('request', lambda rq: s.req.append(((time.time() - s.t0) * 1000, rq.url[len(BASE) - 1:])) if rq.url.startswith(BASE) else None)
        s.t0 = time.time(); s.p.goto(BASE + url, wait_until='load', timeout=30000); s.load = (time.time() - s.t0) * 1000
        if wait: s.settle()
    def settle(s, quiet=2500, cap=30):
        t = time.time(); n = len(s.req); lt = time.time()
        while time.time() - t < cap:
            s.p.wait_for_timeout(200)
            if len(s.req) != n: n = len(s.req); lt = time.time()
            elif time.time() - lt > quiet / 1000: break
    def urls(s, path): path = REL(path); return [u for _, u in s.req if u.split('?')[0] == path]
    def dl(s, path): path = REL(path); return sum(1 for h in HITS[s.h0:] if h.split('?')[0] == path)   # times the file was really downloaded
    def first(s, path): path = REL(path); t = [ms for ms, u in s.req if u.split('?')[0] == path]; return min(t) if t else None
    def close(s): s.c.close()
def inside_point(fc_path):
    """a point inside the first polygon of the file (fixture computed here, not by the page): returns (lat, lon, name)"""
    def in_ring(x, y, r):
        s = False; j = len(r) - 1
        for i in range(len(r)):
            xi, yi = r[i][0], r[i][1]; xj, yj = r[j][0], r[j][1]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi: s = not s
            j = i
        return s
    d = json.load(open(os.path.join(ROOT, fc_path)))
    for f in d['features']:
        g = f.get('geometry') or {}; polys = [g['coordinates']] if g.get('type') == 'Polygon' else g.get('coordinates', []) if g.get('type') == 'MultiPolygon' else []
        for p in polys:
            r = p[0]; xs = [q[0] for q in r]; ys = [q[1] for q in r]
            for fx in (0.5, 0.4, 0.6, 0.3, 0.7):
                for fy in (0.5, 0.4, 0.6, 0.3, 0.7):
                    x = min(xs) + (max(xs) - min(xs)) * fx; y = min(ys) + (max(ys) - min(ys)) * fy
                    if in_ring(x, y, r) and not any(in_ring(x, y, h) for h in p[1:]): return y, x, f['properties'].get('NAME')
    return None
def near_count(la, lo, mi):
    """how many POTA / SOTA / WWFF spots the US planner lists within mi miles: the same rows, order and de-duplication as its
    loadAll, computed here from the files (the fixture for 'results are the same')"""
    import math
    L = json.load(open(os.path.join(ROOT, 'locations.json'))); CA = json.load(open(os.path.join(ROOT, 'data/canada.json'))); NA = json.load(open(os.path.join(ROOT, 'data/northam.json')))
    rows = L + CA.get('rows', []) + NA.get('rows', []); seen = {}; nL = len(L)
    for i, r in enumerate(rows):
        if r[0] not in ('POTA', 'SOTA', 'WWFF'): continue
        if r[0] == 'POTA' and i < nL and not re.match(r'^(US|CA)-', str(r[1])): continue
        k = str(r[1]).upper()
        if k in seen: continue
        seen[k] = r
    def miles(a, b, c, d):
        R = 3958.8; t = math.pi / 180
        return 2 * R * math.asin(math.sqrt(math.sin((c - a) * t / 2) ** 2 + math.cos(a * t) * math.cos(c * t) * math.sin((d - b) * t / 2) ** 2))
    return sum(1 for r in seen.values() if isinstance(r[3], (int, float)) and isinstance(r[4], (int, float)) and miles(la, lo, r[3], r[4]) <= mi)
def main():
    srv = TS(('127.0.0.1', PORT), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    with sync_playwright() as pw:
        b = pw.chromium.launch(proxy={'server': 'http://127.0.0.1:9', 'bypass': '127.0.0.1,localhost'})
        # ---------- US Trip Planner, first visit (nothing to show yet) ----------
        P = Page(b, 'kpc-planner-us.html')
        ok(all(not P.urls(f) for f in BIG_US), 'US planner, first visit: locations.json, data/canada.json and data/northam.json are NOT read at page load ' + str([f for f in BIG_US if P.urls(f)]))
        ok('Search a town' in P.p.inner_text('#us-status'), 'US planner, first visit: the status line says what to do (no count yet): ' + P.p.inner_text('#us-status')[:80])
        ok(not P.errs, 'US planner, first visit: no page errors ' + str(P.errs[:2]))
        P.p.click('#usq'); P.p.wait_for_timeout(200)
        ok('Loading the park list' in P.p.inner_text('#us-status') or 'ready' in P.p.inner_text('#us-status'), 'US planner: tapping the search box shows "Loading the park list…" (then the count)')
        P.settle()
        ok(all(P.dl(f) == 1 for f in BIG_US), 'US planner: after the first tap each of the three park files was read exactly ONCE ' + str({f: P.dl(f) for f in BIG_US}))
        ok(re.search(r'[\d,]+ POTA parks, SOTA summits and WWFF references ready', P.p.inner_text('#us-status')) is not None, 'US planner: then the usual "N POTA parks… ready" line')
        want = near_count(37.57, -84.29, 25)
        P.p.fill('#usq', '37.57, -84.29'); P.p.press('#usq', 'Enter'); P.settle(1500)
        m = re.search(r'([\d,]+)\s*spots within 25 miles', P.p.inner_text('#us-status'))
        got_lazy = int(m.group(1).replace(',', '')) if m else None
        ok(got_lazy == want, f'US planner: a search after the list loads finds the same spots as the files say ({got_lazy} = {want} within 25 miles of 37.57, -84.29)')
        ok(all(P.dl(f) == 1 for f in BIG_US), 'US planner: the search did not read the park files again')
        P.close()
        # ---------- US Trip Planner, typing a search straight away (no tap first): the search waits for the list ----------
        P = Page(b, 'kpc-planner-us.html')
        P.p.evaluate("()=>{const f=document.getElementById('usf');document.getElementById('usq').value='37.57, -84.29';f.requestSubmit?f.requestSubmit():f.dispatchEvent(new Event('submit',{cancelable:true}))}")
        P.settle(1500); m = re.search(r'([\d,]+)\s*spots within 25 miles', P.p.inner_text('#us-status'))
        ok(m and int(m.group(1).replace(',', '')) == want and all(P.dl(f) == 1 for f in BIG_US), 'US planner: a search sent before the list was read waits for it and gives the same answer, files read once')
        P.close()
        # ---------- US Trip Planner, returning member (last search in Colorado): list at once, Kentucky outlines only when the map shows Kentucky ----------
        last = json.dumps({'la': 39.74, 'lo': -104.99, 'label': 'Denver', 'r': 25})
        P = Page(b, 'kpc-planner-us.html', store=[['kpcUsLast', last]])
        ok(all(P.dl(f) == 1 for f in BIG_US), 'US planner, last search on file: the park list is read at once, as before (each file once)')
        ok(len(set(P.urls('/data/canada.json'))) == 1, 'US planner: data/canada.json is asked for at ONE address (park list and official outlines share it; was two downloads): ' + str(sorted(set(P.urls('/data/canada.json')))))
        m = re.search(r'([\d,]+)\s*spots within 25 miles', P.p.inner_text('#us-status'))
        ok(m and int(m.group(1).replace(',', '')) == near_count(39.74, -104.99, 25), 'US planner, last search: the same spot count as the files say')
        ok(all(not P.urls('/' + f + '.geojson') for f in KYF), 'US planner, map on Colorado: none of the 13 Kentucky outline files is read ' + str([f for f in KYF if P.urls('/' + f + '.geojson')]))
        P.p.evaluate("()=>window.__usMap.setView([37.6,-84.3],9)"); P.settle()
        got = {f: P.urls('/' + f + '.geojson') for f in KYF}
        ok(all(P.dl('/' + k + '.geojson') == 1 for k in got), 'US planner: the map moved to Kentucky: each of the 13 Kentucky files read exactly once ' + str({k: P.dl('/' + k + '.geojson') for k in got if P.dl('/' + k + '.geojson') != 1}))
        ok(all(v and v[0] == ADDR(f) for f, v in got.items()), 'US planner: Kentucky files read at the shared address (the released copy, its own ?v=)')
        drawn = P.p.evaluate("()=>window.__usMap._layers.filter(l=>l.feature&&l.feature._lk).length")
        ok(drawn and drawn > 100, f'US planner: the Kentucky outlines are drawn after that ({drawn} outline shapes on the map)')
        P.p.evaluate("()=>window.__usMap.setView([38.2,-85.7],10)"); P.settle(1200)
        ok(all(P.dl('/' + f + '.geojson') == 1 for f in KYF), 'US planner: moving around Kentucky again does not read them again')
        P.close()
        # ---------- US Trip Planner: SAVE MY TRIP FOR NO SIGNAL before the list was read: it reads it first ----------
        trip = json.dumps([{'p': 'POTA', 'c': 'US-1271', 'n': 'Test park', 'la': 37.57, 'lo': -84.29, 'url': ''}])
        P = Page(b, 'kpc-planner-us.html', store=[['kpcUsTrip', trip]])
        ok(all(not P.urls(f) for f in BIG_US) and 'Test park' in P.p.inner_text('#trip-list'), 'US planner: a saved trip is listed at load, without reading the park list')
        P.p.evaluate("()=>document.getElementById('t-off').click()"); P.settle(2500)
        keys = P.p.evaluate("()=>caches.open('kpc-finder-v1').then(c=>c.keys()).then(k=>k.map(r=>new URL(r.url).pathname))")
        ok(all(f in keys for f in BIG_US), 'US planner: SAVE FOR NO SIGNAL first reads the park list, so the saved copy has locations.json, data/canada.json and data/northam.json: ' + str([f for f in BIG_US if f not in keys]))
        P.close()
        # ---------- Kentucky Trip Planner ----------
        P = Page(b, 'kpc-planner.html')
        fb = [P.first('/' + f + '.geojson') for f in KYF]
        ok(all(x is not None for x in fb), 'KY planner: all 13 boundary files still load without any tap (layers on by default, same end state)')
        ok(all(x is not None and x >= P.load - 50 for x in fb), f'KY planner: none of them is asked for before the page has loaded (load {P.load:.0f} ms, first boundary ask {min(x for x in fb if x is not None):.0f} ms)')
        ok(all(P.dl('/' + f + '.geojson') == 1 for f in KYF), 'KY planner: each boundary file read once')
        pt = inside_point('ky-state-parks.geojson')
        w = P.p.evaluate("([a,b])=>{const w=kpcPlanner.where(a,b);return {ready:kpcPlanner.ready(),hits:w.hits.map(h=>h.name)}}", [pt[0], pt[1]])
        ok(w['ready'] and pt[2] in w['hits'], f'KY planner: "where is this spot" finds {pt[2]} for a point inside it (fixture from the file): {w["hits"][:3]}')
        P.close()
        P = Page(b, 'kpc-planner.html', wait=False)
        P.p.evaluate("()=>{const b=document.getElementById('addSpot');if(b)b.click()}"); P.settle()
        ok(all(P.dl('/' + f + '.geojson') == 1 for f in KYF), 'KY planner: ADD A SPOT right away starts the boundary files at once (each read once)')
        P.close()
        # ---------- Park Commander ----------
        pt = inside_point('ky-state-parks.geojson')
        P = Page(b, 'finder.html', geo={'latitude': pt[0], 'longitude': pt[1]})
        on = ['bstate', 'bwma', 'bsnp', 'bsna', 'bdbnf', 'bnps', 'bwild', 'bwilder', 'bfws', 'busace', 'bpad', 'bkpc']
        ok(P.p.evaluate("k=>k.every(x=>document.getElementById('gis-'+x).checked)", on), 'Park Commander: the boundary layers are still ticked by default')
        st = P.p.inner_text('[data-gis=bstatus]') if P.p.query_selector('[data-gis=bstatus]') else P.p.inner_text('#gis-bstatus')
        def polys(fn): return sum(1 for f in json.load(open(os.path.join(ROOT, fn)))['features'] if (f.get('geometry') or {}).get('type') in ('Polygon', 'MultiPolygon') and f['geometry'].get('coordinates'))
        want_st = {'State Parks': polys('ky-state-parks.geojson'), 'WMAs & Public Hunting Areas': polys('ky-hunting-areas.geojson'), 'Army Corps of Engineers land': polys('ky-usace.geojson')}
        ok(all(f'{k}: {n} (KPC copy)' in st for k, n in want_st.items()), f'Park Commander: after idle the same layers are drawn, every outline in the files ({want_st})')
        fb = [P.first('/' + f + '.geojson') for f in ['ky-hunting-areas', 'ky-usace', 'ky-dbnf']]
        ok(all(x is not None and x >= P.load - 50 for x in fb), f'Park Commander: hunting areas, Corps land and forest load after the page has loaded (load {P.load:.0f} ms, first ask {min(x for x in fb if x is not None) if all(fb) else None})')
        ok(all(P.dl('/' + f + '.geojson') == 1 for f in ['ky-hunting-areas', 'ky-usace', 'ky-dbnf', 'ky-state-parks']), 'Park Commander: each boundary file read once')
        ok(all(u == ADDR(f) for f in ['ky-hunting-areas', 'ky-usace', 'ky-state-parks'] for u in P.urls('/' + f + '.geojson')), 'Park Commander: same address as the trip planners (the released copy, its own ?v=)')
        P.p.click('#gis-inside-btn'); P.p.wait_for_timeout(2500)
        txt = P.p.inner_text('#gis-inside')
        ok('INSIDE' in txt and pt[2] in txt and 'NOT INSIDE' not in txt, f'Park Commander: "Am I inside a park?" says INSIDE {pt[2]} for a point inside it: {txt[:90]!r}')
        ok(all(P.dl('/' + f + '.geojson') == 1 for f in ['ky-hunting-areas', 'ky-usace', 'ky-state-parks', 'ky-nature-preserves']), 'Park Commander: the inside check did not download any boundary file a second time')
        P.close()
        P = Page(b, 'finder.html', geo={'latitude': pt[0], 'longitude': pt[1]}, wait=False)
        P.p.click('#gis-inside-btn'); P.settle(); txt = P.p.inner_text('#gis-inside')
        ok('INSIDE' in txt and pt[2] in txt and all(P.dl('/' + f + '.geojson') == 1 for f in ['ky-hunting-areas', 'ky-state-parks', 'ky-nature-preserves']), 'Park Commander: the inside check right at load waits for the files, same answer, each file once')
        P.close()
        # ---------- one address for every page: Park Commander, both planners, the Kentucky Park Map ----------
        addr = set()
        for pg in ['finder.html', 'kpc-planner.html', 'kpc-park-control.html']:
            P = Page(b, pg); addr |= set(P.urls('/ky-usace.geojson')); P.close()
        ok(addr == {ADDR('ky-usace')}, f'ky-usace.geojson (2.2 MB) has ONE address on Park Commander, the KY planner and the Kentucky Park Map: {sorted(addr)}')
        # ---------- About / Events: photos far down the page wait until scrolled to ----------
        for pg, img in [('about.html', '/KPC_Founders_Group.jpg'), ('events.html', '/KPC26-Group-Photo.jpg')]:
            for w_, h_ in [(1280, 900), (390, 844)]:
                P = Page(b, pg, w_, h_)
                ok(not P.urls(img), f'{pg} {w_}px: {img[1:]} is not downloaded at page load')
                for y in range(0, 25000, 700): P.p.evaluate(f'scrollTo(0,{y})'); P.p.wait_for_timeout(60)
                P.settle(1200)
                ok(len(P.urls(img)) == 1 and P.p.evaluate(f"()=>[...document.images].some(i=>i.getAttribute('src')==='{img[1:]}'&&i.complete&&i.naturalWidth>0)"), f'{pg} {w_}px: it is downloaded (once) and shown when scrolled to')
                P.close()
        b.close()
    srv.shutdown()
    print('outside addresses the pages tried (all failed at the dead proxy, nothing left the machine):', sorted(OUTSIDE))
    print(('ALL PASSED' if not fails else f'SOME FAILED ({fails})'))
    sys.exit(1 if fails else 0)
main()
