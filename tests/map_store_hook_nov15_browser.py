#!/usr/bin/env python3
"""Map store hook (KPC owner, 2026-11-15): kpc-padus-layer.js + kpc-outline-display.js in headless Chromium, on MADE-UP display data.
A throwaway site in a temporary folder is served on 127.0.0.1 (every other request is refused; Leaflet is the working stand-in
tests/leaflet_standin_nov11.js). Its made-up state US-ZZ (near 0 N 0 E) has today's released outline file with three parks and a
display copy built by tools/kpc_display_copy.py from a made-up store holding two of them (one area park, one official-line park):
  1. OFF by default: today's three outlines exactly, and no request for the loader or for data/display/;
  2. ON with ?outlines=store: the two store parks from the display copy, the third (missing from the display copy) from today's file;
     remembered in this browser, and ?outlines=old turns it off again;
  3. FALLBACK: display data missing, a broken part, or the loader not loading = exactly what today draws, no page error;
  4. CLICK TARGET: the line-only park has an invisible, interactive polyline (weight 12, opacity 0) carrying its popup, and no band.
Run: python3 tests/map_store_hook_nov15_browser.py (tests/test_map_store_hook_nov15.py runs it in the full suite when Chromium and
playwright are there). Prints PASS / FAIL lines and ends ALL PASS or SOME FAILED."""
import gzip, http.server, json, math, os, pathlib, shutil, socketserver, sys, tempfile, threading
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))
import kpc_display_copy as K  # noqa: E402
from display_copy_fixture import circle, record, park, write_store, line_record, wiggle_line  # noqa: E402

PORT = int(os.environ.get('KPC_TEST_PORT', '8815')); BASE = f'http://127.0.0.1:{PORT}/'
FAILS = []


def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m, flush=True)
    if not c: FAILS.append(m)


PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>store hook test</title></head><body>
<div id="m" style="width:800px;height:600px"></div>
<script src="leaflet.js"></script>
<script src="kpc-padus-layer.js?v=test"></script>
<script>
  const map = L.map('m', { center: [0.1, 0.12], zoom: 12 });
  const pad = KPCPad(map, { usOfficial: true, legend: false, minz: 7 });
  pad.layer.addTo(map);
  window.snap = () => {
    const M = window.__lsMaps[0], out = { feats: [], hits: [] };
    M._layers.forEach(l => {
      if (l.feature) { const p = l.feature.properties || {}; out.feats.push({ ref: p.ref, role: p.role || '', type: l.feature.geometry.type, src: p.cr ? 'store' : p.level ? 'level' : 'today', level: p.level || '', style: l._style || null }); }
      else if (l.options && l.options.className === 'kpc-usoff-hit') out.hits.push({ weight: l.options.weight, opacity: l.options.opacity, interactive: l.options.interactive, fill: l.options.fill, popup: !!l._popup, n: (l._lls || []).length, layer: l });
    });
    out.feats.sort((a, b) => (a.ref + a.role).localeCompare(b.ref + b.role));
    return out;
  };
  window.clickHit = () => { const h = window.snap().hits[0]; if (!h) return null; h.layer.openPopup(); const p = window.__lsMaps[0]._popup; const c = p && p.getContent(); return typeof c === 'function' ? c() : c; };
</script></body></html>"""


def gzj(obj): return gzip.compress(json.dumps(obj).encode(), 9, mtime=0)


def ccw(r): return r[::-1]


# a rough made-up strip (the builder gives it a middle level and fine pieces with small caps); not in today's file
_R = [(round(0.1 + i * 0.00002, 6), round(0.8 + 0.0003 * math.sin(i / 7) + 0.00001 * math.sin(i * 1.7), 6)) for i in range(6000)]
ROUGH = list(reversed(_R + [(round(0.1 + 5999 * 0.00002, 6), 0.81), (0.1, 0.81)] + [_R[0]]))


def make_site(d):
    d = pathlib.Path(d)
    for n in ('kpc-padus-layer.js', 'kpc-outline-display.js'): shutil.copy(ROOT / n, d / n)
    shutil.copy(ROOT / 'tests' / 'leaflet_standin_nov11.js', d / 'leaflet.js')
    (d / 'index.html').write_text(PAGE, encoding='utf-8')
    (d / 'data').mkdir(); (d / 'data' / 'canada.json').write_text('{"rows": []}')   # no Canada parks in this made-up site
    (d / 'kpc-us-states.json').write_text(json.dumps([{'a': 'ZZ', 'n': 'Zedland', 'p': [[[[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]]]}]))
    # today's released outline file (made up): two areas and the trail as a line
    rel = d / 'data' / 'released'; (rel / 'outlines').mkdir(parents=True)
    today = {'type': 'FeatureCollection', 'kpc': {'area': 'US-ZZ', 'format': 1}, 'features': [
        {'type': 'Feature', 'properties': {'ref': 'US-0301', 'name': 'Made-up Lake Park', 'g': 'official', 'detail': 0.0001},
         'geometry': {'type': 'Polygon', 'coordinates': [[list(p) for p in ccw(circle(0.1, 0.1, 0.01, 40))]]}},
        {'type': 'Feature', 'properties': {'ref': 'US-0302', 'name': 'Made-up Trail', 'g': 'official'},
         'geometry': {'type': 'LineString', 'coordinates': [list(p) for p in wiggle_line(0.12, 0.1, 0.15, 12)]}},
        {'type': 'Feature', 'properties': {'ref': 'US-0303', 'name': 'Made-up Wildlife Area', 'g': 'official', 'detail': 0.0001},
         'geometry': {'type': 'Polygon', 'coordinates': [[list(p) for p in ccw(circle(0.14, 0.12, 0.006, 30))]]}}]}
    b = gzj(today); (rel / 'outlines' / 'US-ZZ.geojson.gz').write_bytes(b)
    (rel / 'RELEASED.json').write_text(json.dumps({'areas': {'US': {'sha': 'abc', 'time': 't'}},
                                                   'files': {'outlines/US-ZZ.geojson.gz': [['outlines/US-ZZ.geojson.gz', 'aaaaaaaaaaaa']]}}))
    # the display copy, built by the real builder from a made-up store (the no-worse check runs against the file above)
    st = pathlib.Path(tempfile.mkdtemp(prefix='kpc-hook-store-'))
    try:
        write_store(st, 'US-ZZ', [park('US-0301', [record('a1', 'lay1', [circle(0.1, 0.1, 0.01, 400, wobble=0.01)])], name='Made-up Lake Park'),
                                  park('US-0302', [line_record('t1', 'lay1', [wiggle_line(0.12, 0.1, 0.15, 300)])], name='Made-up Trail'),
                                  park('US-0304', [record('r1', 'lay1', [ROUGH])], name='Made-up Rough Strip')])
        rep = K.build(st, ['US-ZZ'], d / 'data' / 'display', log=lambda *a: None, released=rel, cap=200, mid_cap=500, piece_cap=4000)
    finally:
        shutil.rmtree(st, ignore_errors=True)
    return rep


class TS(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True
    def handle_error(self, *a): pass


def main():
    site = pathlib.Path(tempfile.mkdtemp(prefix='kpc-hook-site-'))
    try:
        rep = make_site(site)
        ok(rep['parks_drawn'] == 3 and K.check(site / 'data' / 'display', 'US-ZZ', public=True) == [],
           f"made-up display copy built and passes check --public ({rep['parks_drawn']} parks, kept today: {rep['no_worse_kept_today']})")

        class H(http.server.SimpleHTTPRequestHandler):
            def __init__(s, *a, **k): super().__init__(*a, directory=str(site), **k)
            def log_message(s, *a): pass
            def end_headers(s): s.send_header('Cache-Control', 'no-store'); super().end_headers()
        srv = TS(('127.0.0.1', PORT), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
        with sync_playwright() as pw:
            b = pw.chromium.launch(proxy={'server': 'http://127.0.0.1:9', 'bypass': '127.0.0.1,localhost'})

            def ctx(block=None):
                c = b.new_context(viewport={'width': 1000, 'height': 800}, service_workers='block')
                def route(r):
                    u = r.request.url
                    if not u.startswith(BASE): return r.abort()
                    if block:
                        x = block(u)
                        if x == 'abort': return r.abort()
                        if x is not None: return r.fulfill(status=200, body=x, headers={'Content-Type': 'application/octet-stream'})
                    return r.continue_()
                c.route('**/*', route)
                return c

            def visit(c, q=''):
                p = c.new_page(); seen, errs, cons, miss = [], [], [], []
                p.on('request', lambda r: seen.append(r.url[len(BASE):] if r.url.startswith(BASE) else r.url))
                p.on('pageerror', lambda e: errs.append(str(e)[:200]))
                p.on('console', lambda m: cons.append(m.text[:200]) if m.type == 'error' else None)
                p.on('response', lambda r: miss.append(r.url[len(BASE):]) if r.status == 404 else None)
                p.goto(BASE + 'index.html' + q, wait_until='load', timeout=30000); p.wait_for_timeout(1500)
                s = p.evaluate("() => { const s = window.snap(); s.hits.forEach(h => delete h.layer); return s; }")
                if os.environ.get('KPC_DEBUG'): print('DEBUG 404', q, miss)
                return p, s, seen, errs, cons

            # 1. off by default
            c = ctx(); p, s0, seen, errs, cons = visit(c)
            today = [(f['ref'], f['role'], f['type']) for f in s0['feats']]
            ok(today == [('US-0301', '', 'Polygon'), ('US-0302', '', 'LineString'), ('US-0303', '', 'Polygon')],
               f"OFF by default: today's three outlines, exactly ({today})")
            ok(not any('kpc-outline-display' in u or 'data/display/' in u for u in seen), 'OFF by default: no request for the loader or data/display/')
            ok(not s0['hits'] and not errs and not cons, f'OFF by default: no click-target polyline, no page or console error ({errs + cons})')
            p.close()

            # 2. on with the address flag
            p, s1, seen, errs, cons = visit(c, '?outlines=store')
            got = [(f['ref'], f['role'], f['type'], f['src']) for f in s1['feats']]
            ok(any(u.startswith('kpc-outline-display.js?v=') for u in seen) and any(u.startswith('data/display/US-ZZ/INDEX.json') for u in seen),
               '?outlines=store: the loader and the display copy are read')
            ok(('US-0301', '', 'MultiPolygon', 'store') in got and ('US-0302', 'line', 'MultiLineString', 'store') in got,
               f'?outlines=store: the two store parks are drawn from the display copy ({got})')
            ok(('US-0303', '', 'Polygon', 'today') in got and len([g for g in got if g[0] == 'US-0303']) == 1,
               "?outlines=store: the park the display copy does not hold keeps today's outline")
            ok(not [g for g in got if g[0] in ('US-0301', 'US-0302') and g[3] == 'today'], "?outlines=store: today's copy of a store park is not drawn as well")
            ok(not errs and not cons, f'?outlines=store: no page or console error ({errs + cons})')

            # 4. the line-only park's click target
            hits = s1['hits']
            ok(len(hits) == 1 and hits[0]['weight'] == 12 and hits[0]['opacity'] == 0 and hits[0]['interactive'] is True and hits[0]['fill'] is False
               and hits[0]['popup'] and hits[0]['n'] >= 1, f'line park: ONE invisible interactive polyline (weight 12, opacity 0, no fill) with a popup ({hits})')
            ok(not [g for g in got if g[0] == 'US-0302' and g[1] == 'hit'] and not [g for g in got if g[0] == 'US-0302' and 'Polygon' in g[2]],
               'line park: no band and no polygon drawn')
            html = p.evaluate('() => window.clickHit()') or ''
            ok('Made-up Trail' in html and 'US-0302' in html and 'Outline: ' in html, f'line park: clicking the line opens its popup with the credit line ({html[:160]})')
            ok(not [f for f in s1['feats'] if f['ref'] == 'US-0301' and f['style'] and f['style'].get('opacity') == 0],
               'area park: its outline is drawn (visible) at the overview level')
            p.close()

            # remembered in this browser; ?outlines=old turns it off
            p, s2, seen, errs, cons = visit(c)
            ok([f['src'] for f in s2['feats'] if f['ref'] == 'US-0301'] == ['store'], 'remembered: the next visit without the flag still draws the store copy')
            p.close()
            p, s3, seen, errs, cons = visit(c, '?outlines=old')
            ok([(f['ref'], f['role'], f['type']) for f in s3['feats']] == today and not s3['hits'], "?outlines=old: today's outlines again")
            p.close()
            p, s4, seen, errs, cons = visit(c)
            ok([(f['ref'], f['role'], f['type']) for f in s4['feats']] == today and not any('data/display/' in u for u in seen),
               '...and it stays off on the next visit (no display request)')
            p.close(); c.close()

            # 3. fallbacks: exactly today's drawing, no page error, only the one failed request in the console
            cases = {
                'display data missing (404)': lambda u: 'abort' if '/data/display/' in u else None,
                'a broken overview part': lambda u: b'not gzip at all' if '/data/display/US-ZZ/US-ZZ.geojson.gz' in u else None,
                'an INDEX of another format': lambda u: json.dumps({'format': 'kpc-display-9', 'area': 'US-ZZ'}).encode() if 'INDEX.json' in u else None,
                'the loader does not load': lambda u: 'abort' if 'kpc-outline-display.js' in u else None,
            }
            for name, blk in cases.items():
                c = ctx(blk); p, sf, seen, errs, cons = visit(c, '?outlines=store')
                ok([(f['ref'], f['role'], f['type']) for f in sf['feats']] == today and not sf['hits'] and not errs and len(cons) <= 1,
                   f"fallback, {name}: exactly today's outlines, no page error, at most the one failed request in the console ({len(cons)}: {cons[:2]})")
                p.close(); c.close()

            # a park missing from the display copy is today's outline (also proved in 2); zoomed in, no error
            c = ctx(); p, s5, seen, errs, cons = visit(c, '?outlines=store')
            ok([f['ref'] for f in s5['feats'] if f['ref'] == 'US-0304'] == ['US-0304'], 'a store park not in today\'s file is drawn from the display copy')
            n0 = len(seen)
            p.evaluate('() => window.__lsMaps[0].setView([0.805, 0.15], 16)'); p.wait_for_timeout(1500)
            z16 = p.evaluate("() => { const s = window.snap(); s.hits.forEach(h => delete h.layer); return s; }")
            lv = [f for f in z16['feats'] if f['level']]
            ov = [f for f in z16['feats'] if f['ref'] == 'US-0304' and not f['level']]
            ok(any('/fine/US-0304/' in u or '/mid/US-0304' in u for u in seen[n0:]) and lv and ov and all((f['style'] or {}).get('opacity') == 0 for f in ov),
               f"zoomed in to 16: the park's finer level is read and drawn, its overview line hidden (levels {sorted({f['level'] for f in lv})})")
            p.evaluate('() => window.__lsMaps[0].setView([0.805, 0.15], 9)'); p.wait_for_timeout(1500)
            z9 = p.evaluate("() => { const s = window.snap(); s.hits.forEach(h => delete h.layer); return s; }")
            ok(not [f for f in z9['feats'] if f['level']] and all((f['style'] or {}).get('opacity') != 0 for f in z9['feats'] if f['ref'] == 'US-0304'),
               'zoomed out again: back to the overview line')
            ok(not errs and not cons, f'zooming with the store copy: no page or console error ({errs + cons})')
            p.close(); c.close()
            b.close()
        srv.shutdown()
    finally:
        shutil.rmtree(site, ignore_errors=True)
    print('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})')
    return 1 if FAILS else 0


if __name__ == '__main__': sys.exit(main())
