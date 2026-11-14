#!/usr/bin/env python3
"""Nov 11 2026 (KPC owner): the hand map placer page in a REAL headless Chrome (playwright), offline. Run by hand (needs Chrome and
playwright; not part of the suite):  DATA=<KPC-Data checkout> python3 tests/map_placer_nov11_browser.py [--keep DIR]

What is real: kpc-map-placer.html, kpc-map-placer.js, kpc-map-placer-math.js, kpc-gate.js, the page's KPC.dataUrl snippet, the DOM,
crypto.subtle (the picture's sha256), Blob download. What is NOT real: Leaflet. Its CDN is unreachable here, so a small stand-in `L`
(below) records the layers the page draws and lets the test fire map clicks with chosen coordinates; tiles are never drawn, so no
map is seen. Every request the page makes is answered locally or refused, and the test fails on any request to another host.
The flow: pick a state and a park (saved-picture index + POTA park list, both stand-ins), the picture loads, 5 point pairs are
clicked, one pair is moved and one deleted, a click on the OpenStreetMap layer is refused, the boundary is traced on the picture,
SAVE downloads the click set; then KPC-Data's kpc_picture_prep.py builds the tracer's input folder from the same stand-ins and
kpc_hand_place.py must accept the click set (DRAWN) and re-check its trace (--check)."""
import hashlib, json, math, os, pathlib, shutil, subprocess, sys, tempfile, threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = pathlib.Path(os.environ.get('DATA') or ROOT.parent / 'data')
CHECKER = DATA / '.github/scripts/draft/kpc_hand_place.py'
ok = True


def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m)
    ok = ok and bool(c)


# ---------------------------------------------------------------- the synthetic park (same numbers as the shared fixture)
FIX = json.loads((ROOT / 'tests/fixtures/hand-place-cases.json').read_text())
PIN, REF, ST = FIX['pin'], 'US-99001', 'GA'
W, H = 1200, 900
RING = FIX['cases']['exact']['input']['shape']['px']
PAIRS = [(q['px'], q['ll']) for q in FIX['cases']['exact']['input']['pairs']]
MAPFILE = f'maps/{REF}_test-park.jpg'
SRC = 'https://parks.example.gov/maps/test-lake.pdf'

L_STUB = r"""
(function(){
  var maps=[], made=[];
  function ev(o){o._h={};o.on=function(n,f){(o._h[n]=o._h[n]||[]).push(f);return o;};o.fire=function(n,e){(o._h[n]||[]).forEach(function(f){f(e||{});});return o;};return o;}
  function layer(kind,a,o){var l=ev({kind:kind,a:a,o:o||{},_map:null});made.push(l);
    l.addTo=function(t){if(t.addLayer)t.addLayer(l);return l;};l.bindTooltip=function(t){l.tip=t;return l;};
    l.getLatLng=function(){return {lat:l.a[0],lng:l.a[1]};};l.setLatLng=function(x){l.a=[x.lat,x.lng];return l;};return l;}
  function group(){var g=layer('group');g.items=[];g.addLayer=function(l){g.items.push(l);l._map=g;return g;};g.clearLayers=function(){g.items=[];return g;};return g;}
  function map(id,o){var el=document.getElementById(id),pane=document.createElement('div');el.appendChild(pane);
    var m=ev({id:id,o:o||{},layers:[],z:0,c:[0,0]});maps.push(m);
    m.setView=function(c,z){m.c=c;m.z=z;return m;};m.fitBounds=function(b){m.b=b;return m;};m.getZoom=function(){return m.z;};
    m.addLayer=function(l){if(m.layers.indexOf(l)<0)m.layers.push(l);return m;};m.removeLayer=function(l){m.layers=m.layers.filter(function(x){return x!==l;});return m;};
    m.hasLayer=function(l){return m.layers.indexOf(l)>=0;};m.getPanes=function(){return {overlayPane:pane};};
    m.latLngToLayerPoint=function(ll){var k=Math.pow(2,m.z)*256/360;return {x:(ll.lng-m.c[1])*k,y:-(ll.lat-m.c[0])*k*1.27};};
    return m;}
  window.L={map:map,CRS:{Simple:{}},imageOverlay:function(u,b){return layer('image',b,{url:u});},tileLayer:function(u,o){return layer('tile',null,Object.assign({url:u},o));},
    layerGroup:group,marker:function(a,o){return layer('marker',a,o);},circleMarker:function(a,o){return layer('circle',a,o);},
    polygon:function(a,o){return layer('polygon',a,o);},polyline:function(a,o){return layer('polyline',a,o);},
    divIcon:function(o){return o;},latLng:function(a,b){return {lat:a,lng:b};}};
  window.__L={maps:maps,made:made};
})();
"""


def make_picture(path):
    import cv2, numpy as np
    img = np.full((H, W, 3), 235, np.uint8)
    for a, b in ([(0, 200), (1200, 260)], [(300, 0), (360, 900)], [(800, 0), (900, 900)], [(0, 700), (1200, 650)]):
        cv2.line(img, a, b, (90, 90, 90), 6)
    cv2.polylines(img, [np.array(RING, np.int32)], True, (40, 160, 40), 4)
    cv2.imwrite(str(path), img, [cv2.IMWRITE_JPEG_QUALITY, 80])


def main():
    from playwright.sync_api import sync_playwright
    keep = sys.argv[sys.argv.index('--keep') + 1] if '--keep' in sys.argv else None
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-placer-'))
    pic = tmp / 'pic.jpg'
    make_picture(pic)
    pic_bytes = pic.read_bytes()
    index = {'maps': [{'ref': REF, 'name': 'Test Lake State Park', 'agency': 'Test State Parks', 'source_url': SRC, 'page': [1], 'files': [MAPFILE]},
                      {'ref': 'US-99009', 'name': 'Not in this state', 'source_url': SRC, 'page': [1], 'files': ['maps/US-99009_x.jpg']}]}
    parkinfo = {'parks': {REF: ['Test Lake State Park', 'https://parks.example.gov', 'State Park', '', '', PIN[0], PIN[1], 0, 0, 0, ST]}}
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    origin = f'http://127.0.0.1:{srv.server_address[1]}'
    asked, foreign = [], []

    def route(r):
        u = r.request.url
        asked.append(u)
        if u.startswith(origin):
            return r.continue_()
        if u == 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js':
            return r.fulfill(status=200, content_type='application/javascript', body=L_STUB)
        if u == 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css':
            return r.fulfill(status=200, content_type='text/css', body='')
        if u.startswith('https://raw.githubusercontent.com/KentuckyPortableClub/KPC-Data/picture-maps/index.json'):
            return r.fulfill(status=200, content_type='application/json', body=json.dumps(index))
        if u == 'https://raw.githubusercontent.com/KentuckyPortableClub/KPC-Data/picture-maps/' + MAPFILE:
            return r.fulfill(status=200, content_type='image/jpeg', body=pic_bytes)
        if u == f'https://kentuckyportableclub.github.io/KPC-Data/data/parkinfo/US-{ST}.json':
            return r.fulfill(status=200, content_type='application/json', body=json.dumps(parkinfo))
        foreign.append(u)
        return r.abort()

    dl = tmp / 'dl'
    dl.mkdir()
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        ctx = b.new_context(accept_downloads=True)
        page = ctx.new_page()
        errs = []
        page.on('pageerror', lambda e: errs.append(str(e)))
        page.route('**/*', route)
        page.goto(origin + '/kpc-map-placer.html', wait_until='load')
        check(page.evaluate('!!window.KPCPlacer && !!window.KPCPlaceMath && window.__L.maps.length === 2'), 'the page starts: math module, page script, two maps (picture + real)')
        check(page.evaluate("KPCGate.member()") and not page.evaluate("document.documentElement.classList.contains('kpc-door')"),
              'members gate: an automated browser passes the gate (as the PDF printer does); the page is not in kpc-gate.js PUBLIC')
        page.select_option('#mpSt', ST)
        page.wait_for_function("document.querySelectorAll('#mpPark option').length >= 2")
        opts = page.eval_on_selector_all('#mpPark option', 'o => o.map(x => x.value)')
        check(REF in opts and 'US-99009' not in opts, f'the park list = parks of the state that have a saved picture: {opts}')
        page.select_option('#mpPark', REF)
        page.wait_for_function('KPCPlacer.state().pic && KPCPlacer.state().pic.sha256')
        st = page.evaluate('KPCPlacer.state().pic')
        check(st['sha256'] == hashlib.sha256(pic_bytes).hexdigest() and st['width'] == W and st['height'] == H,
              'the saved picture loads from the picture-maps branch address; sha256 and pixel size measured in the browser')
        tiles = page.evaluate("__L.maps[1].layers.filter(l => l.kind === 'tile').map(l => l.o.url)")
        check(len(tiles) == 1 and tiles[0].startswith('https://basemap.nationalmap.gov/'), f'the real map starts on the USGS Topo layer: {tiles}')

        def pic_click(x, y):
            page.evaluate(f'__L.maps[0].fire("click", {{latlng: {{lat: {-y}, lng: {x}}}}})')

        def map_click(la, lo):
            page.evaluate(f'__L.maps[1].fire("click", {{latlng: {{lat: {la}, lng: {lo}}}}})')
        map_click(PIN[0], PIN[1])
        check('PICTURE first' in page.inner_text('#mpSay') and page.evaluate('KPCPlacer.state().pairs.length') == 0, 'a map click before a picture click is refused with a message')
        for (px, ll) in PAIRS:
            pic_click(*px)
            map_click(*ll)
        s = page.evaluate('KPCPlacer.state()')
        check(len(s['pairs']) == 5 and s['fit'] is not None, '5 pairs placed by clicks; the fit is live')
        nums = page.evaluate("__L.maps.map(m => m.layers.filter(l => l.kind === 'group')[0].items.filter(l => l.kind === 'marker' && l.o.icon && /<span>\\d+<\\/span>/.test(l.o.icon.html)).length)")
        check(nums == [5, 5], f'each pair is numbered on both sides (numbered markers: picture {nums[0]}, map {nums[1]})')
        fit_txt = page.inner_text('#mpFit')
        check('leave-one-out' in fit_txt and 'm per picture pixel' in fit_txt, f'fit error, leave-one-out, scale and turn shown: {fit_txt}')
        rows = page.eval_on_selector_all('#mpPairs tr', 'r => r.length')
        check(rows == 6, f'the pairs table lists 5 pairs with their error in metres ({rows - 1} rows)')
        gates = page.eval_on_selector_all('#mpGates li', 'l => l.map(x => x.className + ":" + x.textContent)')
        check(any(g.startswith('ok:') and 'fit error' in g for g in gates) and any('CHECKED LATER' in g for g in gates),
              f'gates shown in plain words, pass / fail, plus what the checker does later ({len(gates)} lines)')
        check(page.evaluate("__L.made.some(l => l.kind === 'circle' && l._map && l.tip === 'POTA pin (never moved)' && !l.o.draggable)"), 'the POTA pin is on the real map, not draggable')
        check(page.evaluate("document.querySelector('img.mp-ghost') && /matrix\\(/.test(document.querySelector('img.mp-ghost').style.transform) && document.querySelector('img.mp-ghost').style.opacity === '0.5'"),
              'the ghosted picture sits on the real map with a fitted transform at the slider opacity (50%)')
        page.evaluate("document.getElementById('mpOp').value = '20'")
        page.dispatch_event('#mpOp', 'input')
        check(page.evaluate("document.querySelector('img.mp-ghost').style.opacity") == '0.2', 'the opacity slider changes the ghosted picture')
        # move pair 2 on the picture by dragging (marker dragend) to a wrong spot, see the error grow, move it back
        before = page.evaluate('KPCPlacer.state().fit.rms')
        page.evaluate("(function(){var m=__L.maps[0].layers.find(l=>l.kind==='group').items.filter(l=>l.kind==='marker')[1];m.setLatLng({lat:-160-80,lng:1050+80});m.fire('dragend');})()")
        moved = page.evaluate('KPCPlacer.state().pairs[1].px')
        after = page.evaluate('KPCPlacer.state().fit.rms')
        check(moved == [1130, 240] and after > before + 20, f'a pair can be moved (picture side): error {before:.2f} -> {after:.1f} m')
        page.evaluate("(function(){var m=__L.maps[0].layers.find(l=>l.kind==='group').items.filter(l=>l.kind==='marker')[1];m.setLatLng({lat:-160,lng:1050});m.fire('dragend');})()")
        check(abs(page.evaluate('KPCPlacer.state().fit.rms') - before) < 1e-9, 'moved back: the error is as before')
        # a bad extra pair, deleted with its button
        pic_click(600, 450)
        map_click(PIN[0] + 0.01, PIN[1])
        check(page.evaluate('KPCPlacer.state().pairs.length') == 6, 'a 6th (wrong) pair added')
        page.click('#mpPairs button[data-del="5"]')
        check(page.evaluate('KPCPlacer.state().pairs.length') == 5 and abs(page.evaluate('KPCPlacer.state().fit.rms') - before) < 1e-9, 'a pair is deleted with its ✕ button')
        # OpenStreetMap is look-only
        page.select_option('#mpBase', 'osm')
        pic_click(600, 450)
        map_click(PIN[0], PIN[1])
        check(page.evaluate('KPCPlacer.state().pairs.length') == 5 and 'USGS' in page.inner_text('#mpSay'), 'on the OpenStreetMap layer no point can be placed')
        page.select_option('#mpBase', 'usgs-topo')
        page.click('#mpModeShape')
        for x, y in RING:
            pic_click(x, y)
        s = page.evaluate('KPCPlacer.state()')
        check(len(s['shape']['px']) == len(RING) and s['mode'] == 'shape', 'the boundary is traced on the picture, corner by corner')
        check(page.evaluate("__L.maps[1].layers.find(l=>l.kind==='group').items.some(l => l.kind === 'polygon' && l.tip === 'Approximate: not the official boundary')"),
              'the traced boundary is drawn on the real map with the not-official note')
        bad = page.eval_on_selector_all('#mpGates li.no', 'l => l.map(x => x.textContent)')
        check(not bad, f'every page gate passes on this placement {bad}')
        check('acres' in page.inner_text('#mpAcres'), 'the traced size is shown: ' + page.inner_text('#mpAcres'))
        page.fill('#mpBy', 'tester')
        with page.expect_download() as d:
            page.click('#mpSave')
        f = d.value
        out = dl / f.suggested_filename
        f.save_as(str(out))
        check(f.suggested_filename == f'{REF}.clicks.json', f'SAVE downloads {f.suggested_filename}')
        cs = json.loads(out.read_text())
        check(cs['format'] == 'kpc-click-set 1' and cs['picture']['sha256'] == hashlib.sha256(pic_bytes).hexdigest() and cs['by'] == 'tester'
              and len(cs['pairs']) == 5 and cs['shape']['kind'] == 'area' and cs['fit']['model'] == 'similarity' and cs['park']['pin'] == PIN,
              'the click set holds the picture identity, the pairs, the traced shape, the fit, the gates, the handle and the pin')
        check(not errs, f'no page errors {errs[:3]}')
        b.close()
    srv.shutdown()
    check(not foreign, f'no request to any other host (refused: {foreign[:4]})')

    # ---- the KPC-Data checker accepts the browser's click set (the tracer's own prep builds its input folder)
    if not CHECKER.exists():
        print(f'SKIP checker hand-off: no KPC-Data checkout at {DATA} (set DATA=...)')
    else:
        fake = tmp / 'kpcdata-cwd'
        (fake / 'data/parkinfo').mkdir(parents=True)
        (fake / 'data/parkinfo' / f'US-{ST}.json').write_text(json.dumps(parkinfo))
        base = tmp / 'base'
        (base / 'maps').mkdir(parents=True)
        shutil.copy(pic, base / MAPFILE)
        (base / 'index.json').write_text(json.dumps(index))
        r = subprocess.run([sys.executable, '-B', str(DATA / '.github/scripts/kpc_picture_prep.py'), str(base), str(ROOT)], cwd=fake, capture_output=True, text=True, timeout=120)
        check(r.returncode == 0 and REF in json.loads((base / 'index.json').read_text()), 'kpc_picture_prep.py builds the tracer input folder for the park')
        res = tmp / 'traced-hand'
        r = subprocess.run([sys.executable, '-B', str(CHECKER), str(out), '--base', str(base), '--out', str(res)], capture_output=True, text=True, timeout=300)
        check(r.returncode == 0 and 'DRAWN' in r.stdout, 'KPC-Data kpc_hand_place.py accepts the click set the page saved: ' + r.stdout.strip()[:160])
        tr = res / f'{REF}.json'
        r2 = subprocess.run([sys.executable, '-B', str(CHECKER), '--check', str(tr), '--base', str(base)], capture_output=True, text=True, timeout=300)
        check(r2.returncode == 0 and '1 of 1' in r2.stdout, 'and its trace re-checks identical (--check)')
        if keep and tr.exists():
            k = pathlib.Path(keep); k.mkdir(parents=True, exist_ok=True)
            shutil.copy(out, k / f'{REF}.clicks.json'); shutil.copy(tr, k / f'{REF}.trace.json')
            print(f'kept the click set and its trace in {k}')
    shutil.rmtree(tmp, ignore_errors=True)
    print('ALL PASS' if ok else 'SOME FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
