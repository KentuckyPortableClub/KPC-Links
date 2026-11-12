"""Nov 11 (site review S): the service worker, the offline packers and the logger in headless Chromium against a LOCAL server.
Not in kpc_full_suite.py (needs Chromium + playwright). Run: python3 tests/sw_offline_nov11_browser.py
Every non-localhost request is sent to a dead local port (nothing leaves the machine); a fresh browser context is used for every
check and nothing is written outside the temp profile. Prints PASS / FAIL lines."""
import http.server, socketserver, threading, os, sys, time, json
from playwright.sync_api import sync_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PORT = int(os.environ.get('KPC_TEST_PORT', '8795'))
BASE = f'http://127.0.0.1:{PORT}/'
CDN = [('https://unpkg.com/leaflet@1.9.4/dist/', '/__cdn/unpkg/'), ('https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/', '/__cdn/cdnjs/')]
STUB = "(function(){var f=function(){return P};var P=new Proxy(f,{get:function(t,k){if(k==='then')return undefined;if(k===Symbol.toPrimitive)return function(){return ''};return P},apply:function(){return P},construct:function(){return P}});window.L=P;})();"
OVER = {}; HITS = []
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def log_message(s, *a): pass
    def do_POST(s): HITS.append(('POST', s.path)); s.send_response(200); s.send_header('Content-Length', '2'); s.end_headers(); s.wfile.write(b'ok')
    def do_GET(s):
        p = s.path.split('?')[0]; HITS.append(('GET', s.path))
        if p.startswith('/__cdn/'):
            b = b'' if p.endswith('.css') else STUB.encode()
            s.send_response(200); s.send_header('Content-Type', 'text/css' if p.endswith('.css') else 'application/javascript'); s.send_header('Content-Length', str(len(b))); s.end_headers(); s.wfile.write(b); return
        o = OVER.get(p, {})
        if o.get('delay'): time.sleep(o['delay'])
        if o.get('status'): s.send_response(o['status']); s.send_header('Content-Length', '4'); s.end_headers(); s.wfile.write(b'down'); return
        fp = os.path.join(ROOT, p.lstrip('/'))
        if not os.path.isfile(fp): s.send_error(404); return
        d = open(fp, 'rb').read()
        if fp.endswith('.html'):
            t = d.decode('utf8', 'replace')
            for a, b in CDN: t = t.replace(a, b)
            d = t.encode()
        d += o.get('append', '').encode()
        s.send_response(200); s.send_header('Content-Type', s.guess_type(fp)); s.send_header('Content-Length', str(len(d))); s.send_header('Cache-Control', 'no-cache'); s.end_headers(); s.wfile.write(d)
class TS(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True
    def handle_error(self, *a): pass
fails = 0
def ok(c, m):
    global fails
    print(('PASS ' if c else 'FAIL ') + m, flush=True)
    if not c: fails += 1
def ctx(b, w=1280, h=900):
    c = b.new_context(viewport={'width': w, 'height': h}); c.add_init_script("window.__kpc_ext=[]"); return c
def load(c, page_url, wait=1500):
    p = c.new_page(); p.on('dialog', lambda d: d.dismiss()); p.goto(BASE + page_url, wait_until='load', timeout=20000); p.wait_for_timeout(wait); return p
def sw_ready(p): p.evaluate("navigator.serviceWorker.ready.then(()=>1)"); p.wait_for_timeout(300)
def cache_keys(p, name): return p.evaluate("n=>caches.open(n).then(c=>c.keys()).then(k=>k.map(r=>r.url))", name)
def main():
    srv = TS(('127.0.0.1', PORT), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    with sync_playwright() as pw:
        b = pw.chromium.launch(proxy={'server': 'http://127.0.0.1:9', 'bypass': '127.0.0.1,localhost'})
        # --- 1. registrations: same script, same scope, one registration, from every page that registers ---
        c = ctx(b)
        for pg in ['finder.html', 'kpc-kit.html', 'kpc-planner-us.html', 'kpc-planner.html', 'kpc-logger.html?old=1']:
            p = load(c, pg); sw_ready(p); p.close()
        p = c.new_page(); p.goto(BASE + '404.html'); regs = p.evaluate("navigator.serviceWorker.getRegistrations().then(r=>r.map(x=>[x.scope,x.active&&x.active.scriptURL]))")
        ok(len(regs) == 1 and regs[0][0] == BASE and regs[0][1] == BASE + 'kpc-finder-sw.js', f'finder, kit, both planners and the old logger register ONE worker, same address, same scope: {regs}')
        names = sorted(p.evaluate("caches.keys()")); ok(set(names) <= {'kpc-finder-v1', 'kpc-tiles-v1'}, f'only the two named caches exist after using every page: {names}'); c.close()
        # --- 2. the two caches survive activation of a new worker ---
        c = ctx(b); p = c.new_page(); p.goto(BASE + '404.html')
        p.evaluate("caches.open('kpc-finder-v1').then(c=>c.put('/saved-map-marker', new Response('KEEP')))"); p.evaluate("caches.open('kpc-tiles-v1').then(c=>c.put('/tile-marker', new Response('KEEP')))")
        p.evaluate("caches.open('kpc-zz-old').then(c=>c.put('/x', new Response('x')))")
        p = load(c, 'finder.html'); sw_ready(p); p.reload(); p.wait_for_timeout(800)
        ok(p.evaluate("caches.open('kpc-finder-v1').then(c=>c.match('/saved-map-marker')).then(r=>!!r)") and p.evaluate("caches.open('kpc-tiles-v1').then(c=>c.match('/tile-marker')).then(r=>!!r)"), 'phones that already hold maps in kpc-finder-v1 / kpc-tiles-v1 keep them when the worker activates')
        c.close()
        # --- 3. changed code: online update, then offline fallback ---
        c = ctx(b); p = load(c, 'finder.html'); sw_ready(p); p.reload(); p.wait_for_timeout(1200)
        ok(p.evaluate("!!navigator.serviceWorker.controller"), 'worker controls the page on the second load')
        OVER['/finder.js'] = {'append': '\nwindow.__mark="V2";'}
        p.reload(); p.wait_for_timeout(1500)
        ok(p.evaluate("window.__mark") == 'V2', 'finder.js changed between loads: the second page load RUNS the new code (not the saved copy)')
        c.set_offline(True); p.reload(wait_until='load'); p.wait_for_timeout(1200)
        ok(p.evaluate("window.__mark") == 'V2' and 'No signal' in p.inner_text('body'), 'offline: Park Commander opens and runs the NEWEST saved finder.js, with the offline banner')
        OVER['/finder.js'] = {'append': '\nwindow.__mark="V3";'}; c.set_offline(False); p.reload(); p.wait_for_timeout(1500)
        ok(p.evaluate("window.__mark") == 'V3', 'signal back: the next load runs the newer code again')
        OVER['/finder.js'] = {'status': 503}; p.reload(); p.wait_for_timeout(1500)
        ok(p.evaluate("window.__mark") == 'V3', 'the site answers 503 for finder.js: the page still runs the saved copy (was: a broken page)')
        OVER.pop('/finder.js'); c.close()
        # --- 4. slow connection: the saved copy after ~8 s, and the cache catches up ---
        c = ctx(b); p = load(c, 'finder.html'); sw_ready(p); p.reload(); p.wait_for_timeout(1000)
        OVER['/finder.js'] = {'append': '\nwindow.__slow="NEW";', 'delay': 9.5}
        t0 = time.time(); txt = p.evaluate("fetch('finder.js').then(r=>r.text())"); dt = time.time() - t0
        ok('__slow' not in txt and 7 < dt < 9.4, f'a very slow answer: the saved copy is used after the 8 s limit ({dt:.1f} s)')
        p.wait_for_timeout(3000)
        ok('__slow' in p.evaluate("caches.open('kpc-finder-v1').then(c=>c.match(location.origin+'/finder.js')).then(r=>r.text())"), 'and the slow answer is saved for next time')
        OVER.pop('/finder.js'); c.close()
        # --- 5. a page that was never saved, no signal ---
        c = ctx(b); p = load(c, 'finder.html'); sw_ready(p); p.reload(); p.wait_for_timeout(800); c.set_offline(True)
        p2 = c.new_page(); p2.goto(BASE + 'kpc-planner-us.html'); txt = p2.inner_text('body')
        ok('No signal' in txt and 'Save my trip' in txt, 'offline, a planner never saved: an honest "No signal" page that names the planner\'s own save button'); c.close()
        # --- 6. what is never saved ---
        c = ctx(b); p = load(c, 'finder.html'); sw_ready(p); p.reload(); p.wait_for_timeout(800)
        n0 = len(HITS); p.evaluate("fetch('kpc-ky-data.json',{method:'POST',body:'x'}).catch(()=>0)"); p.evaluate("fetch('https://api.pota.app/spot/activator').catch(()=>0)"); p.wait_for_timeout(800)
        ks = cache_keys(p, 'kpc-finder-v1'); ok(not any('api.pota.app' in k for k in ks) and any(h[0] == 'POST' for h in HITS[n0:]), 'a POST reaches the server and api.pota.app live data is not saved'); c.close()
        # --- 7. released map files are kept under their own ?v= (real kpc-trip-offline.js) ---
        c = ctx(b); p = load(c, 'kpc-planner-us.html'); sw_ready(p); p.reload(); p.wait_for_timeout(800)
        p.evaluate("KPCTripOffline.save({stops:[], files:['data/released/RELEASED.json','data/released/us-key/US-WI.json?v=aaa'], msg:document.body.appendChild(document.createElement('p')), key:'t'})"); p.wait_for_timeout(4000)
        ks = cache_keys(p, 'kpc-finder-v1')
        ok(any(k.endswith('/data/released/us-key/US-WI.json?v=aaa') for k in ks) and not any(k.endswith('/data/released/us-key/US-WI.json') for k in ks), 'the trip planner saves a released file under its own ?v=')
        c.set_offline(True)
        a = p.evaluate("fetch('data/released/us-key/US-WI.json?v=aaa').then(r=>r.status).catch(()=>'err')"); bb = p.evaluate("fetch('data/released/us-key/US-WI.json?v=bbb').then(r=>r.status).catch(()=>'err')")
        ok(a == 200 and bb == 'err', f'offline: ?v=aaa is found, a newer index asking ?v=bbb is NOT answered with the older copy ({a}, {bb})'); c.close()
        # --- 8. the logger: a log that cannot be read is kept aside; imported text cannot run ---
        c = ctx(b); c.add_init_script("if(!localStorage.getItem('__seeded')){localStorage.setItem('__seeded','1');localStorage.setItem('kpcLogger','{\"v\":1,\"q\":[{\"call\":\"W4KPC\",BROKEN');}")
        p = load(c, 'kpc-logger.html?old=1', 2500)
        raw = p.evaluate("Object.keys(localStorage).filter(k=>k.indexOf('kpcLoggerBad-')===0).map(k=>localStorage.getItem(k))")
        ok(len(raw) == 1 and 'BROKEN' in raw[0], 'a saved log that fails to read is copied aside (kpcLoggerBad-...) before anything can overwrite it'); c.close()
        c = ctx(b); p = load(c, 'kpc-logger.html?old=1', 2500); p.evaluate("window.__pwn=0")
        enc = lambda s: ''.join(f'&#{ord(ch)};' if ch.isalpha() or ch == '_' else ch for ch in s)
        pay_call = '<IMG SRC=X ONERROR=' + enc('window.__pwn=1') + '>'
        pay = '<img src=x onerror=window.__pwn=2>'
        def f(k, v): return f'<{k}:{len(v)}>{v}'
        adi = 'x<EOH>\n' + f('CALL', pay_call) + f('QSO_DATE', '20261111') + f('TIME_ON', '1200') + f('BAND', '20m') + f('FREQ', '14.074') + f('MODE', 'SSB') + f('NAME', pay) + f('QTH', pay) + f('NOTES', pay) + f('STATE', pay) + f('RST_SENT', pay) + f('COMMENT', pay) + f('GRIDSQUARE', 'EM77') + '<EOR>\n'
        open('/tmp/_kpc_xss_test.adi', 'w').write(adi)
        p.set_input_files('#xLoad', '/tmp/_kpc_xss_test.adi'); p.wait_for_timeout(800)
        p.evaluate("window.KPCQrz && (KPCQrz.get=()=>({key:'k'}), KPCQrz.showAnswer=()=>{})"); p.evaluate("(document.getElementById('xQzSee')||{click(){}}).click()"); p.wait_for_timeout(500)
        inj = p.evaluate("document.querySelectorAll('img[src=x],img[src=X]').length"); pwn = p.evaluate("window.__pwn")
        ok(inj == 0 and pwn == 0, f'an imported ADIF with HTML in CALL / NAME / QTH / NOTES / STATE / RST / COMMENT injects nothing (injected images {inj}, ran {pwn})'); c.close()
        os.remove('/tmp/_kpc_xss_test.adi')
        b.close()
    print('ALL PASSED' if not fails else f'{fails} FAILED'); sys.exit(1 if fails else 0)
main()
