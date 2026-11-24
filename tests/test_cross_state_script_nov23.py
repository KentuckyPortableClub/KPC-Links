#!/usr/bin/env python3
"""The PC's cross-state script (tools/pc-keys/kpc_get_cross_state.py, owner 23 Nov 2026 5:26 PM; one-time exception 6:20 PM):
robots.txt is read first (a rule that says no = not asked; 5xx = not asked), only the listed ids are asked, a list is kept
only when every asked record comes back, a busy server (429 / 5xx) is not asked again, and the undo copy is made before the
reader runs. Offline: a stand-in replaces every web request; nothing is merged here.
Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import io, json, pathlib, socket, sys, urllib.error, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
socket.socket.connect = lambda *a, **k: (_ for _ in ()).throw(OSError('test: no network'))
sys.path.insert(0, str(ROOT / 'tools/pc-keys'))
import kpc_get_cross_state as G  # noqa: E402

G.PAUSE = 0
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


CALLS = []
MODE = {}


def fake(url, timeout=120):
    CALLS.append(url)
    host = urllib.parse.urlsplit(url).netloc
    if url.endswith('/robots.txt'):
        m = MODE.get(host, 'none')
        if m == 'none': raise urllib.error.HTTPError(url, 404, 'no', {}, io.BytesIO(b''))
        if m == 'no': return 200, b'User-agent: *\nDisallow: /\n'
        if m == 'down': raise urllib.error.HTTPError(url, 503, 'down', {}, io.BytesIO(b''))
    if MODE.get(host + ':query') == 'busy': raise urllib.error.HTTPError(url, 503, 'busy', {}, io.BytesIO(b''))
    q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
    ids = [int(x) for x in q['where'][q['where'].index('(') + 1:-1].split(',')]
    if MODE.get(host + ':query') == 'short': ids = ids[:-1]
    sq = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
    feats = [{'type': 'Feature', 'properties': {'OBJECTID': i, 'NAME': 'Invented'}, 'geometry': {'type': 'Polygon', 'coordinates': [sq]}} for i in ids]
    return 200, json.dumps({'type': 'FeatureCollection', 'features': feats}).encode()


G.get = fake
E = lambda host, ids: {'st': 'ZZ', 'pre': 'sgzzz', 'url': f'https://{host}/arcgis/rest/services/X/FeatureServer/0', 'nf': 'NAME', 'ids': ids, 'label': '', 'oidf': 'OBJECTID'}

check('ids are read from the W11 list', G.ids_of('OBJECTID IN (1, 22,333)') == [1, 22, 333] and G.ids_of('1=1') == [])
MODE['a.invented.example'] = 'none'
okr, why = G.robots_ok(E('a.invented.example', [1])['url'])
check('no robots.txt (404): no rules, asked', okr)
MODE['b.invented.example'] = 'no'
check('robots.txt says no: not asked', not G.robots_ok(E('b.invented.example', [1])['url'])[0])
MODE['c.invented.example'] = 'down'
check('robots.txt 503: not asked (fail closed)', not G.robots_ok(E('c.invented.example', [1])['url'])[0])
CALLS.clear()
feats, body, url, err = G.fetch(E('a.invented.example', [5, 6]))
check('only the listed ids are asked', len(CALLS) == 1 and 'OBJECTID+IN+%285%2C6%29' in CALLS[0] and len(feats) == 2)
MODE['a.invented.example:query'] = 'short'
feats, body, url, err = G.fetch(E('a.invented.example', [5, 6]))
back = {str(G.oid_of(f['properties'])) for f in feats}
check('a short answer is seen (the caller keeps nothing: all or nothing)', back == {'5'})
MODE['d.invented.example'] = 'none'; MODE['d.invented.example:query'] = 'busy'
G.robots_ok(E('d.invented.example', [1])['url'])
CALLS.clear()
feats, body, url, err = G.fetch(E('d.invented.example', [7]))
check('a busy server (503) is asked once, then rests', feats is None and len(CALLS) == 1 and G.ROBOTS['d.invented.example'][0] is None)
src = (ROOT / 'tools/pc-keys/kpc_get_cross_state.py').read_text(encoding='utf-8')
check('the undo copy is made before the reader runs', src.index('shutil.copy(cp, BEFORE / cp.name)') < src.index("'.github/scripts/kpc_us_key.py'], cwd=LINKS"))
check("the owner's one-time exception is written in the script", "6:20 PM, 'Yes, allow it once'" in src)
check('the reader runs with the network blocked', "KPC_KEY_OFFLINE='1'" in src)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
