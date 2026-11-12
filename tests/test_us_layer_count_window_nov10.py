#!/usr/bin/env python3
"""Nov 10 (fresh-start run 42891101784: FL, UT and DE held by the master gate).

1. The live count sent page and outline parameters (resultRecordCount, maxAllowableOffset) with returnCountOnly: the FL DEP
   STATE_OWNED_LANDS server then counts one page window (188 of 77,144), the NRHP server caps the count at the page (200), and
   the DE state lands server refuses the count. The count is now a plain returnCountOnly query.
2. The layer file for a state took the FIRST XS entry of a prefix, so a per-state 'where' (the NRHP layer, sgaki, lists only the
   hand-joined OBJECTIDs in each state) was counted with another state's options (UT: read 1 of 161).
3. A server that cuts a window of rows first and applies the state box after it returns short pages without
   exceededTransferLimit; the read stopped after the first page (189). It now steps window by window when the plain count says
   records in the box are missing.

Runs offline: execs the helpers from kpc_us_key.py (importing it would run the builder) against a stand-in ArcGIS server.
"""
import json, pathlib, re, sys, types, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


def chunk(a, b): return src[src.index(a):src.index(b)]


class Server:
    """rows: [(oid, in_box)]. window=True: cut the row window first, then apply the box (FL DEP); else box first (normal).
    count_mode: 'window' (counts one window when resultRecordCount is sent), 'cap' (caps at it), 'refuse' (error with it)."""
    def __init__(self, rows, window=True, count_mode='window', maxrec=1000):
        self.rows, self.window, self.count_mode, self.maxrec, self.calls = rows, window, count_mode, maxrec, []

    def answer(self, url):
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query)); self.calls.append(q)
        box = 'geometry' in q
        where = q.get('where', '1=1'); ids = None
        m = re.match(r'OBJECTID IN \(([\d,]+)\)', where)
        if m: ids = {int(x) for x in m.group(1).split(',')}
        rows = [r for r in self.rows if ids is None or r[0] in ids]
        rrc = int(q['resultRecordCount']) if 'resultRecordCount' in q else None
        if q.get('returnCountOnly') == 'true':
            if rrc and self.count_mode == 'refuse': return {'error': {'code': 400, 'message': 'Unable to complete operation.'}}
            inb = [r for r in rows if r[1] or not box]
            if rrc and self.count_mode == 'window': return {'count': sum(1 for r in rows[:rrc] if r[1] or not box)}
            if rrc and self.count_mode == 'cap': return {'count': min(len(inb), rrc)}
            return {'count': len(inb)}
        off, n = int(q.get('resultOffset', 0)), min(rrc or self.maxrec, self.maxrec)
        if self.window: page = [r for r in rows[off:off + n] if r[1] or not box]; more = None
        else:
            inb = [r for r in rows if r[1] or not box]; page = inb[off:off + n]; more = off + n < len(inb)
        out = {'features': [{'attributes': {'OBJECTID': r[0], 'NAME': f'Tract {r[0]}'}, 'geometry': {'rings': [[[0, 0], [0, 1], [1, 1], [0, 0]]]}} for r in page]}
        if more: out['exceededTransferLimit'] = True
        return out


class Resp:
    def __init__(self, b): self.b = b
    def read(self): return self.b
    def __enter__(self): return self
    def __exit__(self, *a): return False


def make_ns(server, xs, maxrec=1000, layer_out=True):
    fake_req = types.SimpleNamespace(Request=lambda u, headers=None: u, urlopen=lambda u, timeout=0: Resp(json.dumps(server.answer(u)).encode()))
    urllib_ns = types.SimpleNamespace(request=fake_req, parse=urllib.parse)
    # every read and count goes through checked_open (the master's checked-redirect opener); here a direct stand-in transport
    kmaster = types.SimpleNamespace(checked_opener=lambda check, handlers=(): types.SimpleNamespace(open=lambda u, timeout=0: Resp(json.dumps(server.answer(u)).encode())),
                                    live_ok=lambda u: (True, ''), LiveNotAllowed=type('LiveNotAllowed', (Exception,), {}), HUB_RE=re.compile(r'(^|\.)hub\.arcgis\.com$'), HUB_DELAY=60.0)
    ns = {'urllib': urllib_ns, 'json': json, 're': re, 'time': types.SimpleNamespace(sleep=lambda s: None, strftime=lambda f: '2026-11-10', monotonic=lambda: 0.0),
          'BUILD_DATE': '2026-11-10',   # Nov 12 (KPC owner, 2026-11-12; D6) CHANGED: the builder's one run date replaces its clock calls
          'kpc_host_pace': types.SimpleNamespace(host_of=lambda u: urllib.parse.urlsplit(str(u)).netloc.lower(), wait=lambda h: None),
          'saved_only': lambda u: False, 'DETAIL': 0.001, 'PREC': 5, 'PAGE': 200, 'st_box': lambda st: [-87.6, 25.1, -80.0, 31.0],
          'XS': xs, 'KMASTER': kmaster, 'HOP_HANDLERS': (), 'resolve': lambda pre, url, nf, af: (url, nf, af, 'OBJECTID'), 'LAYER_MAXREC': {x[0]: maxrec for x in xs},
          'SF': types.SimpleNamespace(mapping=lambda *a: {}, extra_fields=lambda m: []), 'SFIELDS': {}, 'SFMAP': {}, 'RAWF': {}, 'XCOUNT': {},
          'LAYER_OUT': pathlib.Path('/nonexistent') if layer_out else None, '_layer_in': lambda st, pre: None, 'notes': [],
          'FAILED_READ': set(), 'OVR': {}, 'kinds': lambda nm: set(), 'norm': lambda s: s.lower(), '_dup': lambda *a: False, '_nf': lambda s: s,
          '_sane_ac': lambda a, b: a, '_num': lambda v: v or 0, 'bbox': lambda g: [0, 0, 1, 1], 'zip_state': lambda st, have: []}
    ns['notice'] = lambda t, m: ns['notes'].append(m)
    code = chunk('def layer_page_size', 'FWS = ') + chunk('def extra_state', 'def _in_box') + chunk('def layer_live_count', '# ------------------------------------------------------------------------------------------------ the shared scoring')
    exec(compile(code, 'kpc_us_key.py', 'exec'), ns)
    return ns


FL = ('sgflf', 'https://ca.dep.state.fl.us/arcgis/rest/services/OpenData/STATE_OWNED_LANDS/MapServer/0/query', 'NAME', '', set(), 'FL DEP (land, state GIS table)', 'STAT', {'FL'}, {})
# 3,000 rows; about 1 in 16 is outside the state box (like 77,144 of 79,689)
rows = [(i, i % 16 != 0) for i in range(1, 3001)]
inbox = sum(1 for r in rows if r[1])

# 1) the count: plain returnCountOnly, no page or outline parameters
sv = Server(rows, window=True, count_mode='window')
ns = make_ns(sv, [FL])
c = ns['layer_live_count']('FL', 'sgflf', FL[1], 'NAME', '', {})
check(f'count: the windowing server gives the true count in the box ({c} of {inbox}), not one window', c == inbox)
check('count: no resultRecordCount / maxAllowableOffset / geometryPrecision on the count query',
      all(not ({'resultRecordCount', 'maxAllowableOffset', 'geometryPrecision'} & set(q)) for q in sv.calls))
old = Server(rows, window=True, count_mode='window').answer(FL[1] + '?' + urllib.parse.urlencode({'where': '1=1', 'geometry': '1,2,3,4', 'returnCountOnly': 'true', 'resultRecordCount': 200, 'maxAllowableOffset': 0.001}))
check(f'count: the old query (page parameters) counted one window ({old["count"]}), the run\'s 188', old['count'] < 200)
sv = Server(rows, window=False, count_mode='refuse')
ns = make_ns(sv, [FL])
check('count: a server that refuses a count with page parameters (DE state lands) now answers', ns['layer_live_count']('DE', 'sgflf', FL[1], 'NAME', '', {}) == inbox)
sv = Server(rows, window=False, count_mode='cap')
ns = make_ns(sv, [FL])
check('count: a server that caps the count at the page (NRHP, 200) now gives the whole count', ns['layer_live_count']('NE', 'sgflf', FL[1], 'NAME', '', {}) == inbox)

# 2) window paging: short pages without exceededTransferLimit are not the end when the plain count says more are in the box
sv = Server(rows, window=True, count_mode='window')
ns = make_ns(sv, [FL])
out = ns['extra_state']('FL', {}, only={'sgflf'})
got = {f['attributes']['OBJECTID'] for f in ns['RAWF'].get('sgflf', [])}
check(f'window paging: every record in the box is read ({len(got)} of {inbox}; the old read stopped at the first page)', len(got) == inbox and len(out) == inbox)
check('window paging: the read says so in a notice', any('window by window' in m for m in ns['notes']))
reads = [q for q in sv.calls if q.get('returnCountOnly') != 'true']
check(f'window paging: windows of the server cap after the first page ({len(reads)} reads for 3,000 rows)', len(reads) <= 1 + 3000 // 1000 + 1)
check('window paging: no record read twice', len(ns['RAWF']['sgflf']) == len(got))

# a normal server (box first, exceededTransferLimit set): unchanged, one extra count at the short last page at most
sv = Server(rows, window=False, count_mode='cap')
ns = make_ns(sv, [FL])
ns['extra_state']('FL', {}, only={'sgflf'})
got = {f['attributes']['OBJECTID'] for f in ns['RAWF'].get('sgflf', [])}
counts = [q for q in sv.calls if q.get('returnCountOnly') == 'true']
check('normal server: every record read, at most one count query, no window paging', len(got) == inbox and len(counts) <= 1 and not any('window by window' in m for m in ns['notes']))

# a server that ignores resultOffset: stops, no endless loop
class Same(Server):
    def answer(self, url):
        a = super().answer(url)
        if 'features' in a: a = super().answer(re.sub(r'resultOffset=\d+', 'resultOffset=0', url))
        return a
sv = Same(rows, window=True, count_mode='window')
ns = make_ns(sv, [FL])
ns['extra_state']('FL', {}, only={'sgflf'})
check('a server that ignores resultOffset: the read stops (no endless loop); the count check then fails it closed', len(sv.calls) < 10 and len(ns['RAWF']['sgflf']) < inbox)

# 3) the layer file counts this state's own entry (its where), not the first entry of the prefix
AK = ('sgaki', 'https://mapservices.nps.gov/arcgis/rest/services/cultural_resources/nrhp_locations/MapServer/1/query', 'RESNAME', '', set(), 'NRHP (land, state GIS table)', 'STAT', {'AK'}, {})
UT = ('sgaki', AK[1], 'RESNAME', '', set(), 'NRHP (land, state GIS table)', 'STAT', {'UT'}, {'where': 'OBJECTID IN (401149)'})
nrhp = Server([(i, True) for i in range(401000, 401300)], window=False, count_mode='cap')
ns = make_ns(nrhp, [AK, UT])
written = []
ns.update({'RESOLVED': {}, '_save_row': lambda a: a, 'KMASTER': types.SimpleNamespace(**vars(ns['KMASTER']), prefix_of=lambda o: re.match(r'[a-z]*', str(o)).group(0),
           esri_to_geojson=lambda g: g, layer_file_path=lambda *a: a, write_layer_file=lambda p, meta, feats: written.append((meta, feats)))})
exec(compile(chunk('def _write_layer_files', 'def save_cache'), 'kpc_us_key.py', 'exec'), ns)
add = ns['extra_state']('UT', {}, only={'sgaki'})
ns['_write_layer_files']('UT', {'sgaki'}, add)
meta, feats = written[-1]
check(f"layer file: UT's NRHP count uses UT's own where ({meta['count_raw']} read of {meta['count_live']} counted; the run had 1 of 161)",
      meta['count_raw'] == 1 and meta['count_live'] == 1)

if __name__ == '__main__':
    sys.exit(0 if ok else 1)
