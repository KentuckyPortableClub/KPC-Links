"""Nov 11 (job 3, loader half): five public map pages in headless Chromium against a LOCAL server; every request that is not to
127.0.0.1 is recorded and refused (nothing leaves the machine; Leaflet is a stand-in). Lists the Kentucky / Canada files each page
asked for, and checks that no page asks for a working Canada outline or Kentucky file, or for any of them from another host.
Not in kpc_full_suite.py (needs Chromium + playwright). Run: python3 tests/loaders_released_ca_ky_nov11_browser.py
KPC_BEFORE=<sha> serves the root *.js / *.html of that commit instead (the data files stay this checkout's): the "before" list.
Prints PASS / FAIL lines (none in the before mode) and, with KPC_URLS_OUT=<file>, writes the URL lists as JSON."""
import http.server, socketserver, threading, os, re, sys, json, subprocess
from playwright.sync_api import sync_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PORT = int(os.environ.get('KPC_TEST_PORT', '8797')); BASE = f'http://127.0.0.1:{PORT}/'
BEFORE = os.environ.get('KPC_BEFORE', '')
LEAFLET = ("(function(){var mk=function(){var f=function(){};return new Proxy(f,{get:function(t,k){if(k==='then')return undefined;if(k===Symbol.toPrimitive)return function(){return 0};"
           "if(k===Symbol.iterator)return function*(){};if(k==='length')return 0;if(k==='prototype')return t.prototype;return mk()},apply:function(){return mk()},construct:function(){return mk()},"
           "set:function(){return true}})};window.L=mk();})();")
_old = {}
def before_file(p):
    if p not in _old:
        r = subprocess.run(['git', 'show', f'{BEFORE}:{p}'], cwd=ROOT, capture_output=True); _old[p] = r.stdout if r.returncode == 0 else None
    return _old[p]
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def log_message(s, *a): pass
    def do_GET(s):
        p = s.path.split('?')[0].lstrip('/')
        if p.startswith('__cdn/'):
            b = b'' if p.endswith('.css') else LEAFLET.encode()
            s.send_response(200); s.send_header('Content-Type', 'text/css' if p.endswith('.css') else 'application/javascript'); s.send_header('Content-Length', str(len(b))); s.end_headers(); s.wfile.write(b); return
        d = before_file(p) if BEFORE and '/' not in p and p.endswith(('.js', '.html')) else None
        fp = os.path.join(ROOT, p)
        if d is None:
            if not os.path.isfile(fp): s.send_error(404); return
            d = open(fp, 'rb').read()
        if p.endswith('.html'):
            t = d.decode('utf8', 'replace')
            t = re.sub(r'\s(?:integrity|crossorigin)="[^"]*"', '', t)
            t = re.sub(r'https://(?:unpkg\.com/leaflet@[\d.]+/dist|cdnjs\.cloudflare\.com/ajax/libs/leaflet/[\d.]+)/', '/__cdn/', t)
            d = t.encode()
        s.send_response(200); s.send_header('Content-Type', s.guess_type(fp)); s.send_header('Content-Length', str(len(d))); s.send_header('Cache-Control', 'no-cache'); s.end_headers(); s.wfile.write(d)
class TS(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True
    def handle_error(self, *a): pass
fails = 0
def ok(c, m):
    global fails
    if BEFORE: return
    print(('PASS ' if c else 'FAIL ') + m, flush=True)
    if not c: fails += 1
MH = re.search(r"MH = '([0-9a-f]{64})'", open(os.path.join(ROOT, 'kpc-gate.js'), encoding='utf-8').read())
IDX = json.load(open(os.path.join(ROOT, 'data/released/RELEASED.json')))
SUB = json.load(open(os.path.join(ROOT, 'data/released', IDX['subs']['canada-bounds/']['file'])))
CA = sorted(SUB['files'])[0][len('canada-bounds/'):-5]
# what each page is asked to do after it loads (the same in both modes): the actions a member takes that read these files
ACT = {
 'finder.html': "async()=>{document.querySelectorAll('input[id^=gis-b]').forEach(c=>{c.checked=true;c.dispatchEvent(new Event('change'))});"
                "document.querySelectorAll('input[id^=gis-]').forEach(c=>{if(!/^gis-b/.test(c.id)){c.checked=true;c.dispatchEvent(new Event('change'))}});"
                "const ix=window.KPCX?await KPCX.overlapIndex().catch(()=>null):null;const k=window.kpcAnswerKey?await kpcAnswerKey.loadKey():null;"
                "return {overlaps:ix?ix.size:-1,key:k?k.size:-1}}",
 'kpc-planner.html': "async()=>{const ix=window.KPCX?await KPCX.overlapIndex().catch(()=>null):null;const k=window.kpcAnswerKey?await kpcAnswerKey.loadKey():null;return {overlaps:ix?ix.size:-1,key:k?k.size:-1}}",
 'kpc-planner-us.html': "async()=>{const fs=window.KPCB&&KPCB.canada?await KPCB.canada('" + CA + "'):null;const o=window.kpcKeyOutlines?await kpcKeyOutlines.loadCanada('" + CA + "'):null;"
                        "const n=window.KPCB&&KPCB.canada?await KPCB.canada('CA-0000'):null;return {canada:fs?fs.length:-1,canadaLayer:o?o.features.length:-1,none:n?n.length:-1}}",
 'kpc-in-park.html': "async()=>{for(let i=0;i<40&&!window.KPCB;i++)await new Promise(r=>setTimeout(r,100));const fs=await KPCB.kyFor('US-1274');return {kyFor:fs?fs.length:-1}}",
 'kpc-guide-pota.html': "async()=>{await new Promise(r=>setTimeout(r,1500));const w=document.getElementById('wild');return {wildText:w?w.innerText.length:-1}}",
 'kpc-maprep.html': "async()=>{for(let i=0;i<40&&!window.KPCB;i++)await new Promise(r=>setTimeout(r,100));const fs=await KPCB.kyFor('US-1274');const c=await KPCB.canada('" + CA + "');return {kyFor:fs?fs.length:-1,canada:c?c.length:-1}}",   # Map Rep: working copies on purpose
 'kpc-park-control.html': "async()=>{for(let i=0;i<40&&!window.KPCB;i++)await new Promise(r=>setTimeout(r,100));const fs=await KPCB.kyFor('US-1274');return {kyFor:fs?fs.length:-1}}",
}
KYCA = re.compile(r'(canada-bounds|ky-[a-z0-9-]+(?:\.p\d+)?\.geojson|ky-answer-key\.json|ky-overlaps)')
def main():
    srv = TS(('127.0.0.1', PORT), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    out = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch(proxy={'server': 'http://127.0.0.1:9', 'bypass': '127.0.0.1,localhost'})
        for page, act in ACT.items():
            c = b.new_context(viewport={'width': 1280, 'height': 900}, service_workers='block')
            if MH: c.add_init_script(f"try{{localStorage.setItem('kpcMember','{MH.group(1)}')}}catch(e){{}}")
            seen, ext = [], []
            def route(r):
                u = r.request.url
                if u.startswith(BASE): return r.continue_()
                ext.append(u); return r.abort()
            c.route('**/*', route)
            p = c.new_page(); p.on('dialog', lambda d: d.dismiss()); p.on('request', lambda q: seen.append(q.url))
            errs = []; p.on('pageerror', lambda e: errs.append(str(e)[:160]))
            try:
                p.goto(BASE + page, wait_until='load', timeout=30000); p.wait_for_timeout(2500)
                res = p.evaluate(act); p.wait_for_timeout(1500)
            except Exception as e: res = {'error': str(e)[:200]}
            loc = sorted({u[len(BASE):] for u in seen if u.startswith(BASE) and KYCA.search(u)})
            out[page] = {'local': loc, 'ext_kyca': sorted({u for u in ext if KYCA.search(u)}), 'ext_hosts': sorted({re.sub(r'^(https?://[^/]+).*', r'\1', u) for u in ext}), 'result': res, 'errors': errs[:5]}
            c.close()
        # finder's SAVE FOR OFFLINE: the Kentucky files go into kpc-finder-v1 as their released addresses, each part with its ?v=
        c = b.new_context(viewport={'width': 1280, 'height': 900}); c.route('**/*', lambda r: r.continue_() if r.request.url.startswith(BASE) else r.abort())
        if MH: c.add_init_script(f"try{{localStorage.setItem('kpcMember','{MH.group(1)}')}}catch(e){{}}")
        p = c.new_page(); saved = []
        try:
            p.goto(BASE + 'finder.html', wait_until='load', timeout=30000); p.wait_for_timeout(1500)
            p.evaluate("()=>{const b=document.getElementById('kpcOffSave');if(b)b.click()}")
            for _ in range(60):
                p.wait_for_timeout(500)
                if p.evaluate("()=>{const b=document.getElementById('kpcOffSave');return !!b&&!b.disabled}"): break
            saved = p.evaluate("()=>caches.open('kpc-finder-v1').then(c=>c.keys()).then(k=>k.map(r=>r.url))")
            c.set_offline(True); p.reload(wait_until='load', timeout=30000); p.wait_for_timeout(2000)
            out['__offline'] = p.evaluate(ACT['finder.html'])
        except Exception as e: saved = ['error ' + str(e)[:120]]; out['__offline'] = {'error': str(e)[:120]}
        out['__finder_saved'] = sorted(u[len(BASE):] for u in saved if KYCA.search(u) or 'RELEASED.json' in u)
        c.close()
        b.close()
    srv.shutdown()
    fsaved = out.pop('__finder_saved')
    offr = out.pop('__offline', None)
    print(f"{'BEFORE' if BEFORE else 'AFTER'} finder.html with NO SIGNAL after saving: {offr}")
    # the overlap index needs kpc-map-extras.js running, which needs Leaflet from the CDN: the stand-in here cannot be saved for offline,
    # so with no signal it is missing both before and after this change; the answer key is the released file read with no signal
    ok((offr or {}).get('key') == out['finder.html']['result'].get('key') > 0, f'finder with no signal after SAVE FOR OFFLINE: the answer key loads from the saved released copy ({offr})')
    print(f"{'BEFORE' if BEFORE else 'AFTER'} finder.html SAVE FOR OFFLINE, Kentucky / released files in kpc-finder-v1: " + ', '.join(re.sub(r'\?v=[^&]+', '?v=…', u) for u in fsaved)[:1500])
    want = sorted(f'data/released/{pp}?v={vv}' for n in ['ky-answer-key.json', 'ky-overlaps.geojson', 'ky-state-parks.geojson', 'ky-hunting-areas.geojson', 'ky-nature-preserves.geojson', 'ky-natural-areas.geojson',
                  'ky-dbnf.geojson', 'ky-dbnf-owned.geojson', 'ky-wild-rivers.geojson', 'ky-nps.geojson', 'ky-wilderness.geojson', 'ky-sheltowee.geojson', 'ky-pine-mountain.geojson', 'ky-dawkins.geojson']
                  for pp, vv in IDX['files']['ky/' + n])
    ok(set(want) <= set(fsaved) and 'data/released/RELEASED.json' in fsaved and not [u for u in fsaved if not u.startswith('data/released/')],
       f'finder SAVE FOR OFFLINE: the same 14 Kentucky files as before, as their {len(want)} released parts with ?v= (+ RELEASED.json), no working copy')
    work = re.compile(r'^(data/canada-bounds/|data/ky-answer-key\.json|ky-[a-z0-9-]+\.geojson)')
    rep = out.pop('kpc-maprep.html')
    print(f"{'BEFORE' if BEFORE else 'AFTER'} kpc-maprep.html (Map Rep, KPC_WORKING_COPY): {json.dumps(rep['result'])}; " + ', '.join(re.sub(r'\?v=[^&]+', '?v=…', u) for u in rep['local'])[:600])
    ok(any(work.match(u) for u in rep['local']) and not any(u.startswith(('data/released/ky/', 'data/released/canada-bounds/')) for u in rep['local']), 'Map Rep page: still the working copies (KPC_WORKING_COPY)')
    for page, o in out.items():
        print(f"{'BEFORE' if BEFORE else 'AFTER'} {page}: {json.dumps(o['result'])}; {len(o['local'])} Kentucky / Canada URL(s): "
              + ', '.join(re.sub(r'\?v=[^&]+', '?v=…', u) for u in o['local'])[:1500] + (f"; other hosts asked (refused): {o['ext_hosts']}" if o['ext_hosts'] else ''))
        ok(not [u for u in o['local'] if work.match(u)], f'{page}: no working Canada outline / Kentucky file asked for')
        ok(not o['ext_kyca'], f'{page}: no Canada outline / Kentucky file asked from another host (KPC-Data)')
        ok(all(re.search(r'\?v=[0-9a-f]{12}$', u) for u in o['local'] if u.startswith('data/released/') and not u.endswith('RELEASED.json')), f'{page}: every released file is asked with its own ?v= version')
        ok('error' not in o['result'], f'{page}: the page ran the member actions ({o["result"]})')
    ok(any(u.startswith('data/released/ky/ky-wild-rivers.geojson?v=') for u in out['kpc-guide-pota.html']['local']), 'POTA guide: the wild river corridors come from data/released/ky/')
    ok(any(u.startswith('data/released/ky/ky-usace.p3.geojson') for o in out.values() for u in o['local']), 'the cut Kentucky layer is read in all its parts')
    ok(any(u.startswith('data/released/canada-bounds/INDEX.json?v=') for u in out['kpc-planner-us.html']['local']) and any(u.startswith(f'data/released/canada-bounds/{CA}.json?v=') for u in out['kpc-planner-us.html']['local']),
       'US planner: a Canada outline comes from data/released/canada-bounds/ through its INDEX')
    if os.environ.get('KPC_URLS_OUT'): json.dump(out, open(os.environ['KPC_URLS_OUT'], 'w'), indent=1)
    if not BEFORE: print('ALL PASS' if not fails else 'SOME FAILED')
    return 1 if fails else 0
if __name__ == '__main__': sys.exit(main())
