#!/usr/bin/env python3
"""Official-links bot, 23 Nov 2026 (owner 6:02 PM 'Yes'; audit 4 items 5.1 and 5.2): every agency page or layer it reads is
checked against that site's robots.txt first (no robots.txt = no rules; an error or no answer = not read), and the page
reader's verified own page is not replaced by another bot's link (it used to flip back and forth). Offline: a stand-in
answers every request. Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import io, pathlib, socket, sys, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
socket.socket.connect = lambda *a, **k: (_ for _ in ()).throw(OSError('test: no network'))
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_link_harvest as H  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


ROBOTS = {'a.invented.gov': b'User-agent: *\nDisallow: /private/\n', 'b.invented.gov': 404, 'c.invented.gov': 503}
ASKED = []


class Resp(io.BytesIO):
    status = 200
    headers = {'Content-Type': 'text/html'}
    def geturl(self): return 'https://a.invented.gov/parks/x'
    def __enter__(self): return self
    def __exit__(self, *a): return False


def fake_open(req, timeout=None):
    url = req.full_url if hasattr(req, 'full_url') else req
    ASKED.append(url)
    host = url.split('/')[2]
    if url.endswith('/robots.txt'):
        v = ROBOTS.get(host)
        if isinstance(v, int): raise urllib.error.HTTPError(url, v, 'x', {}, io.BytesIO(b''))
        return Resp(v)
    return Resp(b'<a href="/maps/x.pdf">Park map</a>')


urllib.request.urlopen = fake_open
check('a path robots.txt allows is read', H.robots_ok('https://a.invented.gov/parks/x'))
check('a path robots.txt forbids is not', not H.robots_ok('https://a.invented.gov/private/x'))
check('no robots.txt (404): no rules', H.robots_ok('https://b.invented.gov/parks/x'))
check('robots.txt 503: not read (fail closed)', not H.robots_ok('https://c.invented.gov/parks/x'))
ASKED.clear()
check('a page robots.txt forbids gives no links and is never asked', H.page_links('https://a.invented.gov/private/park') == [] and ASKED == [])
check('robots.txt is read once per site', sum(1 for u in ASKED if u.endswith('/robots.txt')) == 0)
src = (ROOT / '.github/scripts/kpc_link_harvest.py').read_text(encoding='utf-8')
check("the reader's own page is not replaced by another bot", "str(e.get('web_by') or '').startswith('bot: page reader') and not str(by).startswith('bot: page reader') and ref not in STALE" in src)
check('layers are checked too', "if not robots_ok(url.rstrip('/') + '/query'): continue" in src)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
