#!/usr/bin/env python3
"""kpc_master.read_complete: one complete read of an ArcGIS layer query, or an error (never a partial list).

Against a stand-in ArcGIS server on 127.0.0.1: a normal server; a server that cuts the row window first and applies the box
after it; a silent page cap smaller than the reported maxRecordCount; ids-only cut to a window; resultOffset ignored; a count
off by one (fails closed quickly, no walk through empty windows); duplicate rows; no count; the per-layer time limit.
Offline: only 127.0.0.1 is contacted.
"""
import http.server, json, pathlib, socketserver, sys, threading, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as M  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


class Layer:
    """rows: [(oid, in_box)]. window: cut rows[off:off+n] first, then the box (FL DEP). cap: the page the server really sends
    (it reports maxrec). ids: 'full' | 'window' (ids-only cut to the cap) | None (not supported). count_delta: count off by."""
    def __init__(self, rows, window=False, cap=1000, maxrec=1000, ids='full', ignore_offset=False, count_delta=0, dup=False, flag=True):
        self.__dict__.update(locals()); del self.__dict__['self']
        self.calls = []

    def answer(self, q):
        self.calls.append(q)
        box = 'geometry' in q
        rows = [r for r in self.rows if r[1] or not box]
        if q.get('returnCountOnly') == 'true': return {'count': len(rows) + self.count_delta}
        if q.get('returnIdsOnly') == 'true':
            if not self.ids: return {'error': {'code': 400, 'message': 'returnIdsOnly not supported'}}
            ids = [r[0] for r in rows]
            return {'objectIdFieldName': 'OBJECTID', 'objectIds': ids if self.ids == 'full' else ids[:self.cap]}
        if 'objectIds' in q:
            want = [int(x) for x in q['objectIds'].split(',')]
            page = [r for r in self.rows if r[0] in set(want)][:self.cap]
            more = None
        else:
            off = 0 if self.ignore_offset else int(q.get('resultOffset', 0))
            n = min(int(q.get('resultRecordCount') or self.maxrec), self.cap)
            if self.window: page = [r for r in self.rows[off:off + n] if r[1] or not box]; more = None
            else: page = rows[off:off + n]; more = (off + n < len(rows)) if self.flag else None
        if self.dup and page: page = page + page[:3]
        out = {'features': [{'attributes': {'OBJECTID': r[0], 'NAME': f'Tract {r[0]}'}, 'geometry': {'rings': [[[0, 0], [0, 1], [1, 1], [0, 0]]]}} for r in page]}
        if more: out['exceededTransferLimit'] = True
        return out


LAYER = [None]


class H(http.server.BaseHTTPRequestHandler):
    def _go(self, q):
        b = json.dumps(LAYER[0].answer(q)).encode()
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b))); self.end_headers()
        self.wfile.write(b)

    def do_GET(self): self._go(dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.path).query)))

    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0)
        self._go(dict(urllib.parse.parse_qsl(self.rfile.read(n).decode())))

    def log_message(self, *a): pass


srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), H); srv.daemon_threads = True
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/arcgis/rest/services/x/MapServer/0/query'
POSTS = []


def fetch(url, params, post=False):
    body = urllib.parse.urlencode(params)
    if post: POSTS.append(1); req = urllib.request.Request(url, data=body.encode())
    else: req = urllib.request.Request(url + '?' + body)
    with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read())


BOX = {'geometry': '-87.6,25.1,-80.0,31.0', 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects'}
rows = [(i, i % 16 != 0) for i in range(1, 3001)]
inbox = {r[0] for r in rows if r[1]}


def run(layer, maxrec=1000, **kw):
    LAYER[0] = layer
    try:
        fs, how = M.read_complete(URL, '1=1', BOX, fetch, 'OBJECTID,NAME', page_hint=kw.pop('page_hint', 500), oid_field='OBJECTID',
                                  max_record_count=maxrec, extra={'returnGeometry': 'true', 'outSR': 4326}, label='stand-in', **kw)
        return {f['attributes']['OBJECTID'] for f in fs}, len(fs), how, None
    except M.MasterError as e:
        return None, 0, None, e


def reads(layer): return [q for q in layer.calls if q.get('returnCountOnly') != 'true' and q.get('returnIdsOnly') != 'true']


# 1. a normal server (box first, exceededTransferLimit set), ids-only supported
lay = Layer(rows)
got, n, how, err = run(lay)
check(f'normal server: every record in the box, each once ({n} of {len(inbox)}, by {how and how["mode"]})', got == inbox and n == len(inbox) and how['mode'] == 'ids')
check('normal server: the count and the ids-only ask carry the same where + box, and no page or outline parameters',
      all(q.get('where') == '1=1' and q.get('geometry') == BOX['geometry'] and 'resultRecordCount' not in q and 'maxAllowableOffset' not in q
          for q in lay.calls if q.get('returnCountOnly') == 'true' or q.get('returnIdsOnly') == 'true'))
check(f'normal server: ids asked in batches of min(maxRecordCount, 500) ({len(reads(lay))} reads)', len(reads(lay)) == -(-len(inbox) // 500))
lay = Layer(rows, ids=None)
got, n, how, err = run(lay)
check(f'normal server without ids-only: offset paging reads every record ({n})', got == inbox and how['mode'] == 'offset' and not how['short_page'])

# 2. box after window (FL DEP): short pages without exceededTransferLimit are not the end
lay = Layer(rows, window=True)
got, n, how, err = run(lay)
check(f'box-after-window server: every record by id ({n} of {len(inbox)})', got == inbox and how['mode'] == 'ids')
lay = Layer(rows, window=True, ids=None)
got, n, how, err = run(lay, page_hint=1000)
check(f'box-after-window server without ids-only: offset paging by the rows really sent reads all ({n}), notes the short pages',
      got == inbox and n == len(inbox) and how['short_page'])

# 3. a silent page cap smaller than the reported maxRecordCount (reported 1000, real 150)
for ids in ('full', None):
    lay = Layer(rows, cap=150, ids=ids)
    got, n, how, err = run(lay)
    check(f'silent cap 150 (reports 1000), ids={ids}: every record ({n} of {len(inbox)}; {how and how["mode"]})', got == inbox and n == len(inbox))
for win in (False, True):   # the #117 window loop assumed the window = the reported maxRecordCount
    lay = Layer(rows, cap=500, maxrec=1000, window=win, ids='full')
    got, n, how, err = run(lay)
    check(f'real cap 500 under a reported 1000 (window={win}): every record ({n})', got == inbox)

# 4. ids-only itself cut to a window (fewer ids than the count): offset paging instead
lay = Layer(rows, ids='window', cap=1000)
got, n, how, err = run(lay)
check(f'ids-only windowed (1000 of {len(inbox)} ids): offset paging, every record ({n})', got == inbox and how['mode'] == 'offset')

# 5. resultOffset ignored: a stall error, quickly
lay = Layer(rows, ids=None, ignore_offset=True)
got, n, how, err = run(lay)
check(f'resultOffset ignored: LayerStall, no list ({type(err).__name__}: {err})', isinstance(err, M.LayerStall) and got is None)
check(f'resultOffset ignored: stopped after {len(lay.calls)} requests', len(lay.calls) <= 5)

# 6. count off by one: fails closed quickly (no walk through empty windows)
for win in (False, True):
    lay = Layer(rows, ids='full', count_delta=1, window=win)
    got, n, how, err = run(lay)
    check(f'count one too high (window={win}): refused, nothing returned ({type(err).__name__}: {err})', isinstance(err, (M.ShortRead, M.LayerStall)) and got is None)
    check(f'count one too high (window={win}): {len(lay.calls)} requests (the layer has {len(rows)} rows, pages of 500)', len(lay.calls) <= len(rows) // 500 + 4)
lay = Layer(rows, ids='full', count_delta=-1)
got, n, how, err = run(lay)
check(f'count one too low: refused, not a silently short read ({type(err).__name__})', isinstance(err, M.ShortRead) and got is None)

# 7. duplicate rows: each record once
for ids in ('full', None):
    lay = Layer(rows, dup=True, ids=ids)
    got, n, how, err = run(lay)
    check(f'duplicate rows (ids={ids}): every record exactly once ({n} of {len(inbox)})', got == inbox and n == len(inbox))

# 8. no count, an empty layer, a long id batch as a POST, the time limit
class NoCount(Layer):
    def answer(self, q): return {'error': {'code': 400, 'message': 'no count'}} if q.get('returnCountOnly') else super().answer(q)
got, n, how, err = run(NoCount(rows))
check(f'no count from the layer: refused ({type(err).__name__})', isinstance(err, M.MasterError) and got is None)
got, n, how, err = run(Layer([(i, False) for i in range(1, 50)]))
check('nothing in the box: an empty list, checked by the count', got == set() and err is None)
POSTS.clear()
big = [(i, True) for i in range(100000, 100700)]
got, n, how, err = run(Layer(big, cap=1000))
check(f'a long objectIds batch goes as a POST ({len(POSTS)} posts) and every record comes back', got == {r[0] for r in big} and POSTS)
t = [0.0]
def clk(): t[0] += 61.0; return t[0]
got, n, how, err = run(Layer(rows, ids=None, cap=100), clock=clk, minutes=5)
check(f'a layer over its time limit: LayerStall, no list ({err})', isinstance(err, M.LayerStall) and 'limit' in str(err) and got is None)

# 9. the old end test is what failed: a short page without exceededTransferLimit ended the read
lay = Layer(rows, cap=150, ids=None, flag=False)
LAYER[0] = lay
j = fetch(URL, dict(BOX, where='1=1', outFields='*', f='json', resultOffset=0, resultRecordCount=500))
check('old rule: 150 of 500 asked, no exceededTransferLimit = "the last page" (the read would have stopped at 150)',
      len(j['features']) == 150 and not j.get('exceededTransferLimit'))
got, n, how, err = run(lay)
check(f'... read_complete reads on to every record ({n})', got == inbox)

srv.shutdown()
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
