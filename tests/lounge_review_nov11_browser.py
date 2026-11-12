#!/usr/bin/env python3
"""Nov 11 review of the Hunters Lounge / VIP Lounge (kpc-hunters.html, kpc-hunt.html): browser check with every outside address stubbed.
Not part of kpc_full_suite.py (needs Chromium + Playwright). Run from the repo root:
    python3 -m http.server 8791 --bind 127.0.0.1 &     BASE=http://127.0.0.1:8791/ python3 tests/lounge_review_nov11_browser.py
Every request that is not to BASE is answered by a stand-in or refused: NO live network. Prints PASS / FAIL lines, exits 1 on a FAIL."""
import datetime, json, os, sys
from playwright.sync_api import sync_playwright

BASE = os.environ.get('BASE', 'http://127.0.0.1:8791/')
VIPH = '2053c7c0ae91be40fd2816d87b55adca15e478c076973648e9e0bb42ffedf8b2'   # the public SHA-256 kpc-vip.js compares with (test unlock only)
LEAFLET = "(function(){var C=function(){return new Proxy(function(){},{get:function(t,k){if(k==='then')return undefined;return function(){return C();};},apply:function(){return C();}});};window.L={map:function(){return C()},tileLayer:function(){return C()},layerGroup:function(){return C()},divIcon:function(){return {}},marker:function(){return C()},circleMarker:function(){return C()},geoJSON:function(){return C()},latLngBounds:function(){return C()}};})();"
ok_all = True
def check(c, m):
    global ok_all
    print(('PASS ' if c else 'FAIL ') + m); ok_all = ok_all and bool(c)
def iso(mins): return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=mins)).strftime('%Y-%m-%dT%H:%M:%S')

POTA = [
 {"activator": "K4ABC", "frequency": "14285", "mode": "SSB", "reference": "US-1234", "name": "<img src=x onerror=window.__x1=1>Test Park", "spotTime": iso(3), "spotter": "W1<b>X</b>", "comments": "<script>window.__x2=1</script> fb signal", "locationDesc": "US-KY", "grid6": "EM77ab"},
 {"activator": "VE3XYZ", "frequency": "7200", "mode": "SSB", "reference": "CA-0001", "name": "Parc national de la Gaspésie", "spotTime": iso(5), "spotter": "N0CALL", "comments": "", "locationDesc": "CA-ON", "latitude": 45, "longitude": -75}]
SOTA = [{"timeStamp": iso(4), "frequency": "14.062", "mode": "CW", "associationCode": "W4K", "summitCode": "EC-001\"><svg onload=window.__x3=1>", "summitDetails": "Summit", "activatorCallsign": "N4SOTA", "callsign": "K1ABC", "comments": "hi"}]
HOLE = [{"sig": "WWFF", "source": "Cluster", "freq": 7144000, "mode": "SSB", "dx_call": "DL1ABC", "sig_refs": [{"id": "KFF-0001\"><img src=x onerror=window.__x4=1>", "name": "Wald"}], "dx_country": "Germany", "time": iso(2), "comment": "x"}]
ALLF = {"v": 3, "p": ["POTA", "WWFF", "SOTA", "DXPED", "EVENT", "DX"], "hide": False, "qrt": False, "modes": [], "bands": [], "where": "all", "view": "cards", "st": "", "q": "", "sort": "new"}

def open_page(b, name, vip=False, w=1280, h=900, pota=None, calls=None, init=''):
    ctx = b.new_context(viewport={'width': w, 'height': h}); pg = ctx.new_page(); calls = calls if calls is not None else {}
    pg.errs = []
    def route(r):
        u = r.request.url
        if u.startswith(BASE): return r.continue_()
        for k, f in (('api.pota.app/spot/activator', lambda: pota() if pota else (200, json.dumps(POTA))), ('api2.sota.org.uk/api/spots', lambda: (200, json.dumps(SOTA))),
                     ('spothole.app/api/v1/spots', lambda: (200, json.dumps(HOLE))), ('api.pota.app/programs', lambda: (200, '[]')), ('api2.sota.org.uk/api/associations', lambda: (200, '[]')),
                     ('api.pota.app/spot/', lambda: (200, '"ok"'))):
            if k in u:
                calls[k] = calls.get(k, 0) + 1
                if k == 'api.pota.app/spot/' and r.request.method == 'POST': calls['POST'] = calls.get('POST', 0) + 1; pg.wait_for_timeout(400)
                st, body = f(); return r.fulfill(status=st, content_type='application/json', body=body)
        if 'leaflet.js' in u: return r.fulfill(status=200, content_type='application/javascript', body=LEAFLET)
        if u.endswith('.css'): return r.fulfill(status=200, content_type='text/css', body='')
        calls['other:' + u.split('/')[2]] = calls.get('other:' + u.split('/')[2], 0) + 1
        return r.abort()
    pg.route('**/*', route)
    pg.on('pageerror', lambda e: pg.errs.append(str(e)[:200]))
    pg.on('dialog', lambda d: d.accept())
    pg.add_init_script("localStorage.setItem('kpcMyCall','\"Q4LNG\"');localStorage.setItem('kpcHuntF'," + json.dumps(json.dumps(ALLF)) + ");" + ("localStorage.setItem('kpcVipOK','%s');" % VIPH if vip else '') + init)
    pg.goto(BASE + name); pg.wait_for_timeout(3500)
    return pg

def poll_scenario(b, fail):
    """five minutes of page time (fake clock): how many times does the page ask api.pota.app for the spots?"""
    n = {'pota': 0}
    ctx = b.new_context(viewport={'width': 1280, 'height': 900}); pg = ctx.new_page()
    def route(r):
        u = r.request.url
        if u.startswith(BASE): return r.continue_()
        if 'api.pota.app/spot/activator' in u: n['pota'] += 1; return r.fulfill(status=500 if fail else 200, content_type='application/json', body='{}' if fail else json.dumps(POTA))
        if 'api2.sota.org.uk/api/spots' in u: return r.fulfill(status=500 if fail else 200, content_type='application/json', body='{}' if fail else json.dumps(SOTA))
        if 'leaflet.js' in u: return r.fulfill(status=200, content_type='application/javascript', body=LEAFLET)
        if u.endswith('.css'): return r.fulfill(status=200, content_type='text/css', body='')
        return r.abort()
    pg.route('**/*', route)
    pg.add_init_script("localStorage.setItem('kpcMyCall','\"Q4LNG\"');")
    pg.clock.install(); pg.goto(BASE + 'kpc-hunters.html'); pg.wait_for_timeout(1500)
    for i in range(300): pg.clock.run_for(1000); pg.wait_for_timeout(25)
    ctx.close(); return n['pota']

with sync_playwright() as p:
    b = p.chromium.launch()
    # 1: text from other people's spots shows as text, in the cards and in the table
    for name, vip in (('kpc-hunters.html', False), ('kpc-hunt.html', True)):
        pg = open_page(b, name, vip)
        r = pg.evaluate("()=>({x:[window.__x1,window.__x2,window.__x3,window.__x4].filter(Boolean).length, imgs:document.querySelectorAll('#hlSpots img[src=x], #hlSpots svg[onload]').length, scripts:document.querySelectorAll('#hlSpots script').length, n:document.querySelectorAll('#hlSpots .hs').length, txt:document.getElementById('hlSpots').textContent, hrefs:[...document.querySelectorAll('#hlSpots a[href]')].map(a=>a.getAttribute('href'))})")
        check(r['n'] >= 3, name + ': spot cards drawn (%d)' % r['n'])
        check(r['x'] == 0 and r['imgs'] == 0 and r['scripts'] == 0, name + ': markup in a park name / spotter / comment / summit code / WWFF ref ran nothing and made no elements')
        check('<img src=x' in r['txt'] and '<script>' in r['txt'], name + ': the markup is shown as plain text')
        check(all(h.startswith(('https://', 'kpc-', '#')) for h in r['hrefs']) and not any('"' in h or 'onload' in h for h in r['hrefs']), name + ': every link made from spot data is https or a page of ours, no attribute break-out')
        pg.evaluate("()=>{const F=JSON.parse(localStorage.kpcHuntF);F.view='table';localStorage.kpcHuntF=JSON.stringify(F);document.querySelector('[data-view=table]').click();}"); pg.wait_for_timeout(300)
        r = pg.evaluate("()=>({x:[window.__x1,window.__x2,window.__x3,window.__x4].filter(Boolean).length, rows:document.querySelectorAll('#hlSpots tr.hr').length, imgs:document.querySelectorAll('#hlSpots img[src=x], #hlSpots svg[onload]').length})")
        check(r['rows'] >= 3 and r['x'] == 0 and r['imgs'] == 0, name + ': table view the same (%d rows)' % r['rows'])
        check(not pg.errs, name + ': no script errors %s' % pg.errs[:2])
        pg.context.close()
    # 2: a double Enter on the log dock logs ONE contact
    pg = open_page(b, 'kpc-hunters.html')
    pg.evaluate("()=>{document.getElementById('dCall').value='K1TST';document.getElementById('dFreq').value='14.285';document.getElementById('dRef').value='US-1234';document.getElementById('dkForm').requestSubmit();document.getElementById('dkForm').requestSubmit();}")
    pg.wait_for_timeout(1500)
    n = pg.evaluate("()=>JSON.parse(localStorage.kpcHuntQSO).q.length")
    check(n == 1, 'dock: two quick submits log one contact (%d)' % n)
    # 3: the quick-log sheet keeps the state typed in it, and the filter's state list is not touched
    pg.evaluate("()=>{document.querySelector('#hlSpots [data-k^=\"POTA|K4ABC\"] [data-lq]').click()}"); pg.wait_for_timeout(400)
    r = pg.evaluate("()=>({ids:document.querySelectorAll('#fSt').length, sheet:!!document.getElementById('lgSt'), tag:document.getElementById('fSt').tagName})")
    check(r['ids'] == 1 and r['sheet'] and r['tag'] == 'SELECT', 'sheet: the state box has its own id, #fSt is only the filter list %s' % r)
    pg.evaluate("()=>{(document.getElementById('lgSt')||document.querySelector('#lgForm input#fSt')).value='tx';document.getElementById('lgForm').requestSubmit();document.getElementById('lgForm').requestSubmit();}"); pg.wait_for_timeout(1200)
    q = pg.evaluate("()=>JSON.parse(localStorage.kpcHuntQSO).q")
    check(len(q) == 2 and q[-1]['st'] == 'TX', 'sheet: the state typed in the sheet is saved (TX) and a double save adds one contact (%d) %s' % (len(q), [x['st'] for x in q]))
    # 4: ADIF with accents reads back whole (lengths are bytes)
    r = pg.evaluate("""()=>{const q={id:'a',call:'K1TST',d:'20261111',tm:'1200',f:'14.285',band:'20m',mode:'SSB',ref:'CA-0001',name:'Parc Gaspésie é Québec',st:'',rs:'59',rr:'59',note:'café ñ ü',my:'Q4LNG',grid:'EM77',x:0};
      const t=KPCHunt.adif([q]), L=KPCHunt.parseAdif(t); const ch=KPCHunt.parseAdif(t.replace(/<(\\w+):\\d+>([^<]*) /g,(m,k,v)=>'<'+k+':'+v.length+'>'+v+' ')); return {n:L.length, note:L[0]&&L[0].note, call:L[0]&&L[0].call, my:L[0]&&L[0].my, n2:ch.length, note2:ch[0]&&ch[0].note}}""")
    check(r['n'] == 1 and r['note'] == 'café ñ ü' and r['call'] == 'K1TST' and r['my'] == 'Q4LNG', 'ADIF: our own export with accents reads back whole %s' % r)
    check(r['n2'] == 1 and r['note2'] == 'café ñ ü', 'ADIF: a file whose lengths count characters (other loggers) still reads right %s' % r)
    pg.context.close()
    # 5: respot: a second tap while the first is on its way posts nothing more (VIP page)
    calls = {}
    pg = open_page(b, 'kpc-hunt.html', True, calls=calls)
    pg.evaluate("()=>{const b=document.querySelector('#hlSpots [data-rsp]');b.click();b.click();b.click();}"); pg.wait_for_timeout(1500)
    check(calls.get('POST', 0) == 1, 'respot: three quick taps send one spot (%s)' % calls.get('POST', 0))
    pg.context.close()
    # 6: polling: one minute apart; after POTA and SOTA both fail it backs off; the park list is not fetched on the Lounge pages
    calls = {}
    pg = open_page(b, 'kpc-hunters.html', calls=calls, pota=lambda: (500, '{}'))
    check(calls.get('api.pota.app/spot/activator', 0) >= 1, 'poll: first check made')
    check(not any(k.startswith('other:api.pota.app') for k in calls), 'the state park list (a big POTA call) is not asked for on the Lounge page')
    pg.context.close()
    h, f = poll_scenario(b, False), poll_scenario(b, True)
    check(4 <= h <= 6, 'poll: about one check a minute while all is well (%d in 5 minutes)' % h)
    check(f <= 3, 'poll: after POTA and SOTA both fail the page backs off (%d in 5 minutes; it was 5)' % f)
    # 7: the tab strip ignores ?from=constructor
    pg = open_page(b, 'kpc-space-weather.html?from=constructor')
    check(not [e for e in pg.errs if 'map' in e or 'S.tabs' in e or 'tabs' in e], 'tab strip: ?from=constructor does not break the page %s' % pg.errs[:2])
    pg.context.close()
    # 8: a browser with no Web Serial / WebUSB: both pages still draw spots, the radio window says so, no script errors
    for name, vip in (('kpc-hunters.html', False), ('kpc-hunt.html', True)):
        pg = open_page(b, name, vip, init="delete Navigator.prototype.serial; delete Navigator.prototype.usb;")
        r = pg.evaluate("()=>({noSerial:!('serial' in navigator)&&!('usb' in navigator), n:document.querySelectorAll('#hlSpots .hs').length})")
        pg.evaluate("()=>document.getElementById('hxGear').click()"); pg.wait_for_timeout(500)
        txt = pg.evaluate("()=>document.getElementById('hxPane').textContent")
        check(r['noSerial'] and r['n'] >= 3 and 'cannot talk to a radio' in txt and not pg.errs, name + ': no Web Serial: spots and log work, the radio window explains, no script errors %s' % pg.errs[:2])
        pg.context.close()
    # 9: a contact logged just after 0000 UTC gets the new UTC day whatever the phone's own time zone is
    for tz in ('America/Chicago', 'Pacific/Auckland'):
        ctx = b.new_context(viewport={'width': 1280, 'height': 900}, timezone_id=tz); pg = ctx.new_page()
        pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(BASE) else (r.fulfill(status=200, content_type='application/json', body=json.dumps(POTA)) if 'spot/activator' in r.request.url else r.abort()))
        pg.add_init_script("localStorage.setItem('kpcMyCall','\"Q4LNG\"');")
        pg.clock.install(time=datetime.datetime(2026, 11, 12, 0, 0, 30, tzinfo=datetime.timezone.utc)); pg.goto(BASE + 'kpc-hunters.html'); pg.wait_for_timeout(2000)
        pg.evaluate("()=>{dCall.value='K1TST';dFreq.value='14.285';dkForm.requestSubmit()}"); pg.wait_for_timeout(1000)
        q = pg.evaluate("()=>JSON.parse(localStorage.kpcHuntQSO).q.map(x=>[x.d,x.tm])")
        check(q == [['20261112', '0000']], 'UTC: logged at 00:00:30 UTC in %s = %s' % (tz, q)); ctx.close()
    b.close()
sys.exit(0 if ok_all else 1)
