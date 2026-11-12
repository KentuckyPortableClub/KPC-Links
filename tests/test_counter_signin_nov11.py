#!/usr/bin/env python3
"""No visitor counter while a password is typed (Nov 11 2026, owner). The optional MEMBERS sign-in box on a public page: if the
counter script is already on the page, the gate reloads the page as #members (where kpc-count.js never adds it) and opens the box
there. kpc-count.js also skips while the box is open.

Static checks always run. The browser part (headless Chromium with Playwright) runs when Playwright is installed, else it says SKIP:
the pages are served from this checkout under the live address (https://kentuckyportableclub.github.io/KPC-Links/, answered locally
by the test, so the counter's github.io check passes); EVERY other request is blocked and recorded (gc.zgo.at is answered with an
empty body, never fetched). No network."""
import http.server, os, pathlib, re, socketserver, sys, threading
HERE = pathlib.Path(os.environ.get('LINKS') or pathlib.Path(__file__).resolve().parent.parent)
fails = 0
def ok(c, m):
    global fails
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails += 1
g = (HERE / 'kpc-gate.js').read_text(encoding='utf-8'); c = (HERE / 'kpc-count.js').read_text(encoding='utf-8')
ok("if (closable && counterOn()) { toMembers(); return; }" in g, 'kpc-gate.js: the optional box is not drawn while the counter script is on the page')
ok("location.pathname + location.search + '#members'" in g, 'kpc-gate.js: the reload keeps the query string and adds #members')
ok(g.count('door(true)') == 2 and g.count('door(false)') == 1, 'kpc-gate.js: every way into the box goes through door() (menu button, #members, members-only door)')
ok("document.getElementById('kpcDoor')" in c and "classList.contains('kpc-door')" in c, 'kpc-count.js: never added while the sign-in box is open')

try:
    from playwright.sync_api import sync_playwright
except Exception:  # noqa: BLE001
    print('SKIP browser part: Playwright is not installed here'); print('SOME FAILED' if fails else 'ALL PASSED'); sys.exit(1 if fails else 0)

class Q(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=str(HERE), **k)
    def log_message(s, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), Q); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
LIVE = 'https://kentuckyportableclub.github.io/KPC-Links/'

def run():
    with sync_playwright() as p:
        try: b = p.chromium.launch()
        except Exception as e:  # noqa: BLE001
            print('SKIP browser part: Chromium did not start (%s)' % str(e)[:80]); return
        def page():
            ctx = b.new_context(service_workers='block'); seen = []
            def route(r):
                u = r.request.url
                if u.startswith(LIVE):
                    import urllib.request
                    path = u[len(LIVE):].split('#')[0]
                    try:
                        with urllib.request.urlopen('http://127.0.0.1:%d/%s' % (port, path or 'index.html'), timeout=20) as h:
                            return r.fulfill(status=200, body=h.read(), headers={'content-type': h.headers.get('content-type', 'text/html')})
                    except Exception:  # noqa: BLE001
                        return r.fulfill(status=404, body='')
                seen.append(u)
                if 'gc.zgo.at' in u: return r.fulfill(status=200, content_type='application/javascript', body='')
                return r.abort()
            ctx.route('**/*', route)
            ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false})")
            return ctx, ctx.new_page(), seen
        gc = lambda s: [u for u in s if 'gc.zgo.at' in u]
        el = lambda pg: pg.evaluate("()=>document.querySelectorAll('script[src*=\"gc.zgo.at\"]').length")
        door = lambda pg: pg.evaluate("()=>!!document.getElementById('kpcDoor')&&!!document.querySelector('#kpcDoor input[type=password]')")
        # 1. a normal public page view: the counter is requested once
        ctx, pg, seen = page(); pg.goto(LIVE + 'about.html?from=test'); pg.wait_for_timeout(1500)
        ok(len(gc(seen)) == 1 and el(pg) == 1, 'public page: the counter is requested once (%d) and its script is on the page' % len(gc(seen)))
        # 2. the MEMBERS button: the page comes back as #members with the box open and no counter
        n0 = len(seen)
        with pg.expect_navigation(timeout=15000): pg.click('.kpc-mem-btn')
        pg.wait_for_timeout(1500)
        ok(pg.url.endswith('about.html?from=test#members'), 'after MEMBERS: same page, query kept, #members (%s)' % pg.url[len(LIVE):])
        ok(door(pg) and el(pg) == 0 and not gc(seen[n0:]), 'the box is open with its password field, no gc.zgo.at script in the page, no counter request after the reload')
        # 3. the box closed and opened again in that state: no reload loop, still no counter
        pg.click('#kpcDoor .x'); pg.click('.kpc-mem-btn'); pg.wait_for_timeout(800)
        ok(door(pg) and el(pg) == 0 and pg.url.endswith('#members'), 'closing and reopening there opens the box directly (no loop)')
        ctx.close()
        # 4. keyboard: Enter on the MEMBERS button does the same
        ctx, pg, seen = page(); pg.goto(LIVE + 'index.html'); pg.wait_for_timeout(1500)
        pg.focus('.kpc-mem-btn')
        with pg.expect_navigation(timeout=15000): pg.keyboard.press('Enter')
        pg.wait_for_timeout(1500)
        ok(door(pg) and el(pg) == 0 and pg.url.endswith('index.html#members'), 'keyboard Enter on MEMBERS: #members, box open, no counter script')
        ctx.close()
        # 5. a deep link with #members never asks for the counter
        ctx, pg, seen = page(); pg.goto(LIVE + 'campout.html?x=1#members'); pg.wait_for_timeout(2000)
        ok(door(pg) and not gc(seen) and el(pg) == 0, 'opened directly as #members: the box is open and the counter is never requested')
        outside = sorted(set(u.split('/')[2] for u in seen))
        print('INFO outside hosts these pages tried (all blocked or stubbed): ' + ', '.join(outside))
        ctx.close(); b.close()
try: run()
finally: srv.shutdown()
print('SOME FAILED' if fails else 'ALL PASSED')
sys.exit(1 if fails else 0)
