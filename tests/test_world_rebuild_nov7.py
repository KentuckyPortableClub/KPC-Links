#!/usr/bin/env python3
"""World key rebuild, part B (Nov 7 2026; Brandon's decisions in world-failed-diagnosis.md section 7: B1 B2 B3 B4 B6 yes, B5 NO).
Run W-42259043963 failed AU (300-min limit: 22 approved AU layers, the GA hydro lines about 3.6M features, read with geometry,
no deadline, no checkpoint), CH and NO (the empty EEA Natura 2000 source held them every build). All in kpc_world_key.py:
  B6  CH and NO read no EEA Natura 2000 source (their EEA nationally designated areas source and CH's BAFU sources stay);
  B1  line and point layers are read without geometry (rings_of() keeps polygons only, so the records are the same);
  B2  one request has a whole-answer time limit and bounded retries with growing, jittered waits (longer for small hosts);
  B3  one layer has a time limit and a stall rule; a stalled layer RAISES into the FAILED path: saved copy or HOLD, as before;
      its partial read is never used (B5 refused);
  B4  a checkpoint after every page (cache/world/parts/<CC>/), keyed by the layer; a stopped read resumes from its last page;
      a FINISHED layer's checkpoint is kept (done) and reused without reading its pages until the country is written, then all of
      that country's checkpoints are deleted; a held country publishes nothing; older than 7 days or another layer key = read fresh.
Offline: stand-in servers, a stand-in clock, temporary folders. Never writes the repo. Plain script (check / ALL PASS)."""
import gzip, json, os, pathlib, re, subprocess, sys, tempfile, textwrap, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.chdir(ROOT)
SCRIPT = ROOT / '.github' / 'scripts' / 'kpc_world_key.py'
TEXT = SCRIPT.read_text(encoding='utf-8')
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


def load(src=TEXT, name='kpc_world_key_test'):
    """Everything before the country loop (definitions only; the golden tests load it the same way)."""
    ns = {'__name__': name, '__file__': str(SCRIPT)}
    exec(compile(src.split('\nfor cc in COUNTRIES:')[0], 'kpc_world_key.py', 'exec'), ns)
    sys.excepthook = sys.__excepthook__   # the script routes tracebacks to its notice(), which the tests replace
    return ns


class Clock:
    """Stand-in for the time module: sleep() moves the clock, nothing waits."""
    def __init__(self):
        import time; self.t, self.sleeps, self.t0 = 1000.0, [], time.time()
    def monotonic(self): return self.t
    def time(self): return self.t0 + self.t - 1000.0   # wall clock = now + the stand-in time passed (file mtimes are real)
    def sleep(self, s): self.sleeps.append(s); self.t += s
    def strftime(self, *a): import time; return time.strftime(*a)


class Resp:
    def __init__(self, body, clock=None, per_chunk=0.0, chunk=1 << 16):
        self.body, self.pos, self.clock, self.per_chunk, self.chunk = body, 0, clock, per_chunk, chunk
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read1(self, n):
        c = self.body[self.pos:self.pos + min(n, self.chunk)]; self.pos += len(c)
        if c and self.clock: self.clock.t += self.per_chunk
        return c


class Kill(BaseException):
    """The runner's time limit (SIGTERM / SIGKILL) arriving in the middle of a read."""


class Layer:
    """A stand-in ArcGIS layer: n features, object ids 1..n, resultOffset or object-id paging."""
    def __init__(self, n, geom='esriGeometryPolygon', oid=True, mx=1000, info_geom=True, order=True, ignore_offset=False,
                 error_on=None, kill_on=None, page_secs=0.0, clock=None, edit=1, refuse_oid=False, spy=None, paging=None):
        self.__dict__.update(locals()); del self.__dict__['self']
        self.urls, self.queries = [], []

    def feat(self, i, want_geom):
        o = i + 1; a = ({'OBJECTID': o} if self.oid else {}) | {'NAME': f'Mount Example {o}', 'TYPE': 'National Park'}
        if not want_geom: return {'attributes': a}
        x, y = 140 + (o % 100) * .01, -30 - (o % 50) * .01
        g = ({'rings': [[[x, y], [x + .1, y], [x + .1, y + .1], [x, y]]]} if self.geom == 'esriGeometryPolygon' else
             {'paths': [[[x, y], [x + .1, y + .1]]]} if self.geom == 'esriGeometryPolyline' else {'x': x, 'y': y})
        return {'attributes': a, 'geometry': g}

    def info(self):
        d = {'maxRecordCount': self.mx, 'fields': ([{'name': 'OBJECTID', 'type': 'esriFieldTypeOID'}] if self.oid else []) +
             [{'name': 'NAME', 'type': 'esriFieldTypeString'}, {'name': 'TYPE', 'type': 'esriFieldTypeString'}],
             'editingInfo': {'lastEditDate': self.edit}, 'advancedQueryCapabilities': {'supportsOrderBy': self.order}}
        if self.paging is not None: d['advancedQueryCapabilities']['supportsPagination'] = self.paging
        if self.oid: d['objectIdField'] = 'OBJECTID'
        if self.info_geom: d['geometryType'] = self.geom
        return d

    def query(self, q):
        self.queries.append(q); k = len(self.queries)
        if self.spy: self.spy(k, q)
        if self.clock: self.clock.t += self.page_secs
        if self.kill_on == k: raise Kill()
        if self.error_on == k or self.error_on == 'all': return {'error': {'code': 500, 'message': 'Error performing query operation'}}
        if self.refuse_oid and 'resultOffset' not in q: return {'error': {'code': 400, 'message': 'Invalid or missing input parameters.'}}
        m = re.search(r'OBJECTID > (\d+)', q.get('where', '')); last = int(m.group(1)) if m else 0
        if 'resultOffset' in q:
            i0 = last + (0 if self.ignore_offset else int(q['resultOffset'])); i1 = min(self.n, i0 + min(int(q['resultRecordCount']), self.mx))
        else:
            i0 = last; i1 = min(self.n, i0 + min(int(q.get('resultRecordCount') or self.mx), self.mx))
        fs = [self.feat(i, q.get('returnGeometry') == 'true') for i in range(i0, i1)]
        return {'features': fs, 'exceededTransferLimit': i1 < self.n, 'geometryType': self.geom}

    def __call__(self, req, timeout=None):
        u = getattr(req, 'full_url', req); self.urls.append(u); p = urllib.parse.urlsplit(u)
        q = dict(urllib.parse.parse_qsl(p.query))
        return Resp(json.dumps(self.query(q) if p.path.endswith('/query') else self.info()).encode())


def new_ns(layer=None, clock=None, parts=None, cc='AU'):
    ns = load(); clock = clock or Clock(); ns['time'] = clock; notes = []
    ns['notice'] = lambda t, m: notes.append(f'{t}: {m}')
    if layer is not None: layer.clock = layer.clock or clock; ns['_open'] = layer
    if parts: ns['WCACHE'] = pathlib.Path(parts)
    ns['PART_CC'] = cc
    return ns, clock, notes


URL = 'https://services.ga.gov.au/gis/rest/services/Example/MapServer/2'
BASE = os.environ.get('KPC_WORLD_BASE', '8620939')  # main before #55 (the world rebuild)
OLD = subprocess.run(['git', 'show', BASE + ':.github/scripts/kpc_world_key.py'], capture_output=True, text=True, cwd=ROOT).stdout


def old_read(layer, where='1=1'):
    """origin/main's pull_arcgis1 on the same stand-in layer (the read before this change)."""
    ns0 = load(OLD, 'old'); ns0['time'] = Clock(); ns0['notice'] = lambda *a: None
    ns0['fetch'] = lambda u, tries=4, timeout=240: json.loads(layer(urllib.request.Request(u)).body)
    return ns0['pull_arcgis1']('Example layer', URL, where)


# ------------------------------------------------------------------ B6: CH and NO read no EEA Natura 2000 source
g = load()
n2k = lambda cc: [s for s in g['SRC'][cc] if 'Natura2000Sites' in str(s[2])]   # noqa: E731
check(not n2k('CH') and not n2k('NO'), 'B6: CH and NO have no EEA Natura 2000 source')
check(all(any(s[0] == 'EEA nationally designated areas' and f"countryCode='{c}'" in s[3] for s in g['SRC'][c]) for c in ('CH', 'NO')),
      'B6: CH and NO keep their EEA nationally designated areas source')
check(sum(1 for s in g['SRC']['CH'] if s[1] == 'chshp') == 10, "B6: CH keeps its 10 BAFU sources")
others = [c for c in g['EU'] if c not in ('CH', 'NO')]
check(len(others) == 22 and all(len(n2k(c)) == 1 and g['SRC'][c][0][0] == 'EEA Natura 2000' and f"MS='{c}'" in g['SRC'][c][0][3] for c in others),
      f'B6: every other EU country ({len(others)}) still reads EEA Natura 2000 first, with its own country filter')
if OLD:
    g0 = load(OLD, 'old_src')
    diff = {c: [s[0] for s in g0['SRC'][c] if s not in g['SRC'].get(c, [])] for c in g0['SRC']}
    diff = {c: v for c, v in diff.items() if v}
    added = {c: [s[0] for s in g['SRC'][c] if s not in g0['SRC'].get(c, [])] for c in g['SRC']}
    check(diff == {'CH': ['EEA Natura 2000'], 'NO': ['EEA Natura 2000']} and not any(added.values()) and set(g0['SRC']) == set(g['SRC']),
          f'B6: vs origin/main only CH and NO lose one source, EEA Natura 2000; nothing else changes ({diff})')
    check(g0['EXTRA_URLS'] == g['EXTRA_URLS'] and g0['LAYER_NAMEF'] == g['LAYER_NAMEF'], 'every approved extra layer is still read (extra-layers.json untouched)')
check(subprocess.run(['git', 'diff', '--quiet', BASE, '--', 'data/world-key/extra-layers.json'], cwd=ROOT).returncode == 0,
      'data/world-key/extra-layers.json is byte-unchanged vs origin/main')
# no data loss: neither key joins or lists a record from the Natura 2000 source
for base in [ROOT] + ([pathlib.Path(os.environ['DATA'])] if os.environ.get('DATA') else []):
    for cc in ('CH', 'NO'):
        f = base / 'data' / 'world-key' / f'{cc}.json'
        if not f.exists(): continue
        d = json.load(open(f, encoding='utf-8'))
        hits = [r for r, p in d['parks'].items() for q in (p.get('m') or []) + (p.get('c') or []) if 'Natura' in str(q[2])]
        check(not hits, f'B6: {f.relative_to(base.parent) if base != ROOT else f.relative_to(ROOT)}: no joined or candidate record from EEA Natura 2000 ({len(d["parks"])} parks)')

# ------------------------------------------------------------------ B1: no geometry for line and point layers
for gt in ('esriGeometryPolyline', 'esriGeometryPoint'):
    lay = Layer(2500, geom=gt); ns, _, _ = new_ns(lay, parts=tempfile.mkdtemp())
    got = ns['pull_arcgis1']('Example layer', URL, '1=1')
    qs = [q for q in lay.queries]
    check(len(qs) == 3 and all(q['returnGeometry'] == 'false' and 'maxAllowableOffset' not in q for q in qs),
          f'B1: {gt} layer: every query asks returnGeometry=false, no generalisation ({len(qs)} pages)')
    ref = old_read(Layer(2500, geom=gt))
    check(got == ref and len(got) == 2500 and all(r['_bb'] is None and r['_r'] == [] for r in got),
          f'B1: {gt} layer: the records equal the old read with geometry, field for field (outline was already discarded)')
lay = Layer(2500); ns, _, _ = new_ns(lay, parts=tempfile.mkdtemp())
got = ns['pull_arcgis1']('Example layer', URL, '1=1')
check(all(q['returnGeometry'] == 'true' and 'maxAllowableOffset' in q for q in lay.queries), 'B1: a polygon layer still asks for geometry on every page')
check(got == old_read(Layer(2500)) and all(r['_bb'] and r['_r'] for r in got), 'B1: polygon records equal the old read (outlines kept)')
lay = Layer(2500, geom='esriGeometryPolyline', info_geom=False); ns, _, _ = new_ns(lay, parts=tempfile.mkdtemp())
got = ns['pull_arcgis1']('Example layer', URL, '1=1')
check([q['returnGeometry'] for q in lay.queries] == ['true', 'false', 'false'] and got == old_read(Layer(2500, geom='esriGeometryPolyline', info_geom=False)),
      'B1: a layer that does not name its geometry: the first answer (polyline) turns geometry off from page 2; same records')
check("in NOGEOM" in TEXT and "info.get('geometryType')" in TEXT and not re.search(r'NOGEOM.*(label|name)', TEXT),
      'B1: geometry type comes from the layer metadata / first answer, never from the layer name')
lay = Layer(2500, oid=False); ns, _, _ = new_ns(lay, parts=tempfile.mkdtemp()); ns['pull_arcgis1']('Example layer', URL, '1=1')
lay0 = Layer(2500, oid=False); old_read(lay0)
check([q for q in lay.queries] == [q for q in lay0.queries], 'fallback: a layer with no object-id field is paged with exactly the old queries (resultOffset)')

# ------------------------------------------------------------------ B2: per-request time limit + bounded retries
ns, clock, _ = new_ns()
calls = []
def flaky(req, timeout):
    calls.append(timeout)
    if len(calls) < 4: raise OSError('503 Service Unavailable')
    return Resp(b'{"ok": 1}')
ns['_open'] = flaky
check(ns['fetch']('https://example.org/x?f=json') == {'ok': 1} and len(calls) == 4, 'B2: three failures then an answer: 4 calls, the answer is returned')
check(len(clock.sleeps) == 3 and all(.5 * min(300, 6 * 3 ** i) <= w <= min(300, 6 * 3 ** i) for i, w in enumerate(clock.sleeps)),
      f'B2: waits grow (6 x 3^try) with jitter x0.5-1.0: {[round(w, 1) for w in clock.sleeps]}')
check(all(t <= ns['SOCK_S'] for t in calls), 'B2: the socket timeout never exceeds SOCK_S')
calls.clear(); clock.sleeps.clear(); ns['_open'] = lambda req, timeout: (calls.append(1), (_ for _ in ()).throw(OSError('reset')))[1]
try: ns['fetch']('https://example.org/x'); raised = None
except OSError as e: raised = e
check(raised is not None and len(calls) == ns['REQ_TRIES'] == 4 and len(clock.sleeps) == 3, 'B2: always failing: stops after REQ_TRIES (4) tries and raises the last error')
calls.clear(); clock.sleeps.clear()
try: ns['fetch']('https://arcgis.mma.gob.cl/server/rest/services/SIMBIO/SIMBIO_AP/FeatureServer/0?f=json')
except OSError: pass
check(len(calls) == 4 and all(.5 * min(300, 30 * 3 ** i) <= w <= min(300, 30 * 3 ** i) for i, w in enumerate(clock.sleeps)),
      f'B2: a small single-server host (CL) waits longer (30 x 3^try, cap 300): {[round(w) for w in clock.sleeps]}')
calls.clear(); clock.sleeps.clear(); t0 = clock.t
try: ns['fetch']('https://example.org/x', deadline=clock.t + 20)
except OSError: pass
check(clock.t <= t0 + 20 and len(calls) < 4, f'B2: waits never sleep past the layer deadline ({len(calls)} tries, {clock.t - t0:.1f} s of 20)')
ns['_open'] = lambda req, timeout: Resp(b'{"features": []}' + b' ' * 400, clock=clock, per_chunk=10.0, chunk=1)
t0 = clock.t
try: ns['fetch']('https://example.org/x', tries=1); raised = None
except TimeoutError as e: raised = e
check(raised is not None and 'trickling' in str(raised) and clock.t - t0 <= ns['REQ_S'] + 10,
      f'B2: a server that trickles bytes is cut at REQ_S ({ns["REQ_S"]:g} s) of whole-answer time: {raised}')
os.environ.update(KPC_WORLD_REQ_TRIES='2', KPC_WORLD_REQ_S='90', KPC_WORLD_SLOW_HOSTS='slow.example.org')
try: e1 = load()
finally:
    for k in ('KPC_WORLD_REQ_TRIES', 'KPC_WORLD_REQ_S', 'KPC_WORLD_SLOW_HOSTS'): os.environ.pop(k, None)
check(e1['REQ_TRIES'] == 2 and e1['REQ_S'] == 90 and 'slow.example.org' in e1['SLOW_HOSTS'] and 'kartor.regeringen.ax' in e1['SLOW_HOSTS'],
      'B2: tries, request limit and slow hosts are environment-tunable')
check(TEXT.count('urllib.request.urlopen(') == 1, 'B2: every request in kpc_world_key.py goes through the one time-limited helper (_open)')

# ------------------------------------------------------------------ B3: per-layer time limit + stall rule
lay = Layer(10 ** 9, page_secs=30.0); ns, clock, _ = new_ns(lay, parts=tempfile.mkdtemp())
try: ns['pull_arcgis1']('Hydro lines', URL, '1=1'); raised = None
except ns['LayerStall'] as e: raised = e
check(raised is not None and 'limit' in str(raised) and 115 <= len(lay.queries) <= 125,
      f'B3: an endless layer (exceededTransferLimit forever) stops at LAYER_MIN=60 min: LayerStall after {len(lay.queries)} pages')
ns['LAYER_MIN_URLS'] = {'example/mapserver/2': 5}; lay = Layer(10 ** 9, page_secs=30.0); ns['_open'] = lay; lay.clock = clock
try: ns['pull_arcgis1']('Hydro lines', URL, '1=1')
except ns['LayerStall']: pass
check(9 <= len(lay.queries) <= 12, f'B3: a per-layer limit (KPC_WORLD_LAYER_MIN_URLS) applies to that address only ({len(lay.queries)} pages in 5 min)')
lay = Layer(5000, order=False, ignore_offset=True); ns, _, _ = new_ns(lay, parts=tempfile.mkdtemp())
try: ns['pull_arcgis1']('Example layer', URL, '1=1'); raised = None
except ns['LayerStall'] as e: raised = e
check(raised is not None and len(lay.queries) == 2 and 'again' in str(raised), f'B3: a server that ignores resultOffset stalls on page 2 ({raised})')
lay = Layer(5000, error_on=3); ns, _, _ = new_ns(lay, parts=tempfile.mkdtemp())
try: ns['pull_arcgis1']('Example layer', URL, '1=1'); raised = None
except ns['LayerStall'] as e: raised = e
check(raised is not None and 'query error after page 2' in str(raised), f'B3: an error answer on page 3 is a stall, not a silent short layer ({raised})')
check(len(old_read(Layer(5000, error_on=3))) == 2000, '... (origin/main returned those 2,000 of 5,000 records as if complete)')
lay = Layer(5000, error_on='all', order=False); ns, _, notes = new_ns(lay, parts=tempfile.mkdtemp())
check(ns['pull_arcgis1']('Example layer', URL, '1=1') == [] and len(lay.queries) == 1 and any('query error' in n for n in notes),
      'B3: an error answer on page 1 (resultOffset paging) is as before: notice, 0 records -> the EMPTY / saved-copy / HOLD path')
lay = Layer(5000, error_on='all'); ns, _, notes = new_ns(lay, parts=tempfile.mkdtemp())
check(ns['pull_arcgis1']('Example layer', URL, '1=1') == [] and len(lay.queries) == 2 and any('object-id paging refused' in n for n in notes),
      'B3: object-id paging: an error on page 1 asks once more the old way (resultOffset), then as before (0 records)')
lay = Layer(5000, error_on=1); ns, _, notes = new_ns(lay, parts=tempfile.mkdtemp())
check(len(ns['pull_arcgis1']('Example layer', URL, '1=1')) == 5000, 'B3: object-id paging: one error on page 1, then the old way answers: the whole layer')

# B3 into HOLD: the real source loop with the real readers
START, END = '    if recs is None:\n        recs, failed = [], False', '\n    if not recs: continue'
_s = TEXT.index(START); BLOCK = textwrap.dedent(TEXT[_s:TEXT.index(END, _s)])
GOOD = ('NSW State Forest', 'arcgis', 'https://services2.arcgis.com/x/arcgis/rest/services/NSW/FeatureServer/0')
HYDRO = ('Surface_HydroLines_National', 'arcgis', 'https://services.ga.gov.au/gis/rest/services/Surface_Hydrology/MapServer/2')


def source_loop(saved, tmpd):
    clock = Clock(); good, hydro = Layer(300, clock=clock), Layer(10 ** 9, geom='esriGeometryPolyline', page_secs=30.0, clock=clock)
    ns, _, notes = new_ns(None, clock, parts=tmpd)
    ns['_open'] = lambda req, timeout: (hydro if 'Surface_Hydrology' in req.full_url else good)(req, timeout)
    held, wsaved = [], []
    ns.update(cc='AU', CMODE='refresh', recs=None, SRC={'AU': [GOOD, HYDRO]}, HELD=held, print=lambda *a, **k: None,
              wload=lambda cc: [dict(r) for r in saved] if saved is not None else None, wsave=lambda cc, r: wsaved.append(r))
    exec(compile('went_on = False\nfor _once in [0]:\n' + textwrap.indent(BLOCK, '    ') + '\n    went_on = True\n', 'source loop', 'exec'), ns)
    return ns, held, wsaved, notes, hydro


tmpd = tempfile.mkdtemp()
ns, held, wsaved, notes, hydro = source_loop(None, tmpd)
check(held == ['AU'] and not ns['went_on'] and wsaved == [], 'B3 -> HOLD: the stalled layer FAILS; no saved copy -> AU is HELD, nothing written, the previous key stays')
check(any('Surface_HydroLines_National FAILED' in n and 'limit' in n for n in notes) and any('HELD' in n for n in notes),
      'B3 -> HOLD: logged as FAILED (over its limit) and HELD')
st = sorted((bool(x.get('done')), x['pages'], x['n']) for x in (json.load(open(f)) for f in pathlib.Path(tmpd, 'parts', 'AU').glob('*.state.json')))
check(st == [(False, len(hydro.queries) - 1, 1000 * (len(hydro.queries) - 1)), (True, 1, 300)],
      f'B3: the stalled layer keeps its in-progress checkpoint, NSW (complete) a finished one; the country is still held ({st})')
sid = ns['src_id'](HYDRO)
saved = [{'src': HYDRO[0], 'id': f'saved-{i}', 'n': f'River {i}', 'sid': sid} for i in range(40)]
ns, held, wsaved, notes, _ = source_loop(saved, tempfile.mkdtemp())
hy = [r for r in ns['recs'] if r['src'] == HYDRO[0]]
check(not held and ns['went_on'] and len(hy) == 40 and all(str(r['id']).startswith('saved-') for r in hy) and wsaved == [],
      'B3: with saved records for the stalled source they are used, exactly as before; not one partial record is kept; nothing saved')

# ------------------------------------------------------------------ B4: checkpoint after every page, resume, clear, signature
def parts_of(d, cc='AU'): return sorted(p.name for p in pathlib.Path(d, 'parts', cc).glob('*')) if pathlib.Path(d, 'parts', cc).exists() else []


def state_of(d, cc='AU'):
    f = list(pathlib.Path(d, 'parts', cc).glob('*.state.json'))
    return json.load(open(f[0])) if f else None


full = None
for mode, kw in (('object-id', {}), ('resultOffset', {'order': False})):
    d = tempfile.mkdtemp(); seen = []
    lay = Layer(4300, **kw); ns, _, _ = new_ns(lay, parts=d)
    lay.spy = lambda k, q: seen.append((state_of(d) or {}).get('pages', 0))
    got = ns['pull_arcgis1']('Example layer', URL, '1=1')
    full = full or got
    check(seen == [0, 1, 2, 3, 4] and got == full and len(got) == 4300, f'B4 ({mode}): a checkpoint is written after every page (pages seen before each request: {seen})')
    check((state_of(d) or {}).get('done') is True and state_of(d)['n'] == 4300, f'B4 ({mode}): the finished layer keeps its checkpoint, marked done (until the country is written)')
    d = tempfile.mkdtemp(); lay = Layer(4300, kill_on=4, **kw); ns, _, notes = new_ns(lay, parts=d)
    try: ns['pull_arcgis1']('Example layer', URL, '1=1')
    except Kill: pass
    s = state_of(d)
    check(s and s['pages'] == 3 and s['n'] == 3000 and s['mode'] == ('oid' if not kw else 'offset'), f'B4 ({mode}): stopped during page 4: the checkpoint holds 3 pages')
    with open(next(pathlib.Path(d, 'parts', 'AU').glob('*.jsonl.gz')), 'ab') as fh: fh.write(gzip.compress(b'{"half":"page"}\n') + b'\x1f\x8b\x08junk')
    lay = Layer(4300, **kw); ns, _, notes = new_ns(lay, parts=d)
    got = ns['pull_arcgis1']('Example layer', URL, '1=1')
    q1 = lay.queries[0]
    right = ("OBJECTID > 3000" in q1['where'] and 'resultOffset' not in q1) if not kw else (q1.get('resultOffset') == '3000' and '>' not in q1['where'])
    check(right and len(lay.queries) == 2, f"B4 ({mode}): the next run resumes at page 4 (first query: {q1.get('where')!r} offset {q1.get('resultOffset')})")
    check(got == full and any('resumed' in n for n in notes), f'B4 ({mode}): resumed read = the uninterrupted read, record for record (a half-written page is dropped)')
    check((state_of(d) or {}).get('done') is True and state_of(d)['n'] == 4300, f'B4 ({mode}): marked done after the resumed layer completes')

# the AU case: the layer limit stops the read, the next run continues it, nothing partial is ever returned
d = tempfile.mkdtemp(); lay = Layer(4300, page_secs=180.0); ns, clock, _ = new_ns(lay, parts=d); ns['LAYER_MIN'] = 10   # 3 pages fit in 10 min
try: got = ns['pull_arcgis1']('Example layer', URL, '1=1'); raised = None
except ns['LayerStall'] as e: raised, got = e, None
check(raised is not None and got is None and state_of(d)['pages'] == 3, 'B4+B3: over the limit after 3 pages: LayerStall (no records returned), checkpoint kept')
lay = Layer(4300); ns, _, _ = new_ns(lay, parts=d)
check(ns['pull_arcgis1']('Example layer', URL, '1=1') == full and len(lay.queries) == 2 and (state_of(d) or {}).get('done') is True and state_of(d)['n'] == 4300,
      'B4+B3: the next run reads only pages 4-5 and returns the whole layer')

# a changed layer never resumes from an old read
for what, kw, where in (('the where clause', {}, "TYPE='National Park'"), ('the layer (last edit date)', {'edit': 2}, '1=1'),
                        ('the geometry type in the metadata', {'info_geom': False}, '1=1')):
    d = tempfile.mkdtemp(); lay = Layer(4300, kill_on=3); ns, _, _ = new_ns(lay, parts=d)
    try: ns['pull_arcgis1']('Example layer', URL, '1=1')
    except Kill: pass
    lay = Layer(4300, **kw); ns, _, _ = new_ns(lay, parts=d)
    got = ns['pull_arcgis1']('Example layer', URL, where)
    check('>' not in lay.queries[0]['where'] and len(got) == 4300, f'B4: a changed {what} starts from page 1 (the old checkpoint is ignored)')
d = tempfile.mkdtemp(); lay = Layer(4300, kill_on=3); ns, _, _ = new_ns(lay, parts=d)
try: ns['pull_arcgis1']('Example layer', URL, '1=1')
except Kill: pass
sf = next(pathlib.Path(d, 'parts', 'AU').glob('*.state.json')); s = json.load(open(sf)); s['sig'][3] = 'other'; json.dump(s, open(sf, 'w'))
lay = Layer(4300); ns, _, notes = new_ns(lay, parts=d); got = ns['pull_arcgis1']('Example layer', URL, '1=1')
check('>' not in lay.queries[0]['where'] and got == full and any('layer key differs' in n for n in notes), 'B4: a state whose stored key differs is ignored and removed')
d = tempfile.mkdtemp(); lay = Layer(4300, kill_on=3); ns, _, _ = new_ns(lay, parts=d)
try: ns['pull_arcgis1']('Example layer', URL, '1=1')
except Kill: pass
lay = Layer(4300); ns, clock, notes = new_ns(lay, parts=d); clock.t += 8 * 86400
got = ns['pull_arcgis1']('Example layer', URL, '1=1')
check('>' not in lay.queries[0]['where'] and got == full, 'B4: an in-progress checkpoint older than KPC_WORLD_PART_DAYS (7) is ignored')
d = tempfile.mkdtemp(); lay = Layer(4300, kill_on=3); ns, _, _ = new_ns(lay, parts=d); ns['PART_CC'] = 'CL'
try: ns['pull_arcgis1']('Example layer', URL, '1=1')
except Kill: pass
check(parts_of(d, 'CL') and not parts_of(d, 'AU'), "B4: checkpoints are kept per country (cache/world/parts/<CC>/), the folder the workflow carries")
d = tempfile.mkdtemp(); lay = Layer(4300); ns, _, _ = new_ns(lay, parts=d); ns['PARTS_ON'] = False
seen = []; lay.spy = lambda k, q: seen.append(parts_of(d))
check(ns['pull_arcgis1']('Example layer', URL, '1=1') == full and not any(seen), 'B4: KPC_WORLD_PARTS=0 writes no checkpoint')
lay = Layer(4300, refuse_oid=True); ns, _, notes = new_ns(lay, parts=tempfile.mkdtemp())
check(ns['pull_arcgis1']('Example layer', URL, '1=1') == full and any('object-id paging refused' in n for n in notes),
      'B4: a server that refuses object-id paging is read with resultOffset paging, as before (same records)')
check(full == old_read(Layer(4300)), 'B4: object-id paging returns exactly the records of the old resultOffset read')
lay = Layer(9000, mx=5000, paging=True); ns, _, _ = new_ns(lay, parts=tempfile.mkdtemp()); got = ns['pull_arcgis1']('Example layer', URL, '1=1')
check(len(got) == 9000 and all(q.get('resultRecordCount') == '1000' and 'resultOffset' not in q for q in lay.queries) and len(lay.queries) == 10,
      'B4: object-id paging still asks 1000 a page when the layer supports it (maxRecordCount 5000 is not one huge page)')
lay = Layer(9000, mx=2000); ns, _, _ = new_ns(lay, parts=tempfile.mkdtemp()); got = ns['pull_arcgis1']('Example layer', URL, '1=1')
check(len(got) == 9000 and len({r['id'] for r in got}) == 9000 and not any('resultRecordCount' in q for q in lay.queries),
      'B4: a layer that does not say it pages: object-id paging at its own maxRecordCount, every record once')
wf = (ROOT / '.github/workflows/kpc-world-key.yml').read_text(encoding='utf-8')
check(wf.count('path: cache/world/parts') == 2 and "WCACHE / 'parts' / (PART_CC" in TEXT and 'PART_CC = cc' in BLOCK,
      'B4: checkpoints go to cache/world/parts/<CC>/, which the workflow restores and saves for the slow-country job')

# ------------------------------------------------------------------ end to end: the real script, a stalled layer, exit 3, previous key kept
RUNNER = r'''
import json, os, re, sys, runpy, urllib.parse, urllib.request
SCRIPT, MODE = sys.argv[1], sys.argv[2]
LOG = open(os.environ['FAKE_LOG'], 'a')
class R:
    def __init__(s, b): s.b, s.p = b, 0
    def __enter__(s): return s
    def __exit__(s, *a): return False
    def read1(s, n): c = s.b[s.p:s.p + n]; s.p += len(c); return c
def fake(req, timeout=None):
    u = getattr(req, 'full_url', req); p = urllib.parse.urlsplit(u); q = dict(urllib.parse.parse_qsl(p.query))
    if 'mma.gob.cl' not in p.netloc: raise OSError('no network in this test: ' + p.netloc)
    LOG.write(json.dumps([p.path, q.get('where')]) + '\n'); LOG.flush()
    if not p.path.endswith('/query'):
        return R(json.dumps({'maxRecordCount': 1000, 'objectIdField': 'OBJECTID', 'geometryType': 'esriGeometryPolygon',
                             'fields': [{'name': 'OBJECTID', 'type': 'esriFieldTypeOID'}, {'name': 'NOMBRE', 'type': 'esriFieldTypeString'}]}).encode())
    m = re.search(r'OBJECTID > (\d+)', q['where']); last = int(m.group(1)) if m else 0
    layer2 = p.path.endswith('FeatureServer/2/query')
    stall = MODE == 'stall' and layer2                  # layer 2 pages forever (over its limit)
    n = last + 1000 if stall else last + 5 if (MODE == 'finish' and layer2) else 1
    fs = [{'attributes': {'OBJECTID': i, 'NOMBRE': 'Parque Nacional Torres del Paine' if i == 1 and not layer2 else f'Rio {i}'},
           'geometry': {'rings': [[[-73.5, -51.5], [-72.5, -51.5], [-72.5, -50.5], [-73.5, -51.5]]]}} for i in range(last + 1, n + 1)]
    return R(json.dumps({'features': fs, 'exceededTransferLimit': stall}).encode())
urllib.request.urlopen = fake
sys.argv = [SCRIPT]
runpy.run_path(SCRIPT, run_name='__main__')
'''
PREV = b'{"cc": "CL", "previous": "key from the last good build"}\n'
IDX = b'{"build": "W-1", "countries": {"CL": {"parks": 1}}}\n'


def e2e_dir():
    t = pathlib.Path(tempfile.mkdtemp()); (t / 'data/parkinfo').mkdir(parents=True); (t / 'data/world-key').mkdir(parents=True)
    json.dump({'parks': {'CL-0001': ['Torres del Paine National Park', '', 'National Park', '', '', -51.0, -73.0]}}, open(t / 'data/parkinfo/CL.json', 'w'))
    json.dump({'countries': {}}, open(t / 'data/world-key/extra-layers.json', 'w'))
    (t / 'data/world-key/CL.json').write_bytes(PREV); (t / 'data/world-key/index.json').write_bytes(IDX)
    (t / 'runner.py').write_text(RUNNER, encoding='utf-8')
    return t


def saved_copy(t):
    """cache/world/W-CL.json.gz with records for layer 2 (by source id), as the boundary-cache release would provide."""
    sid = repr(('arcgis', L2, None)); (t / 'cache/world').mkdir(parents=True, exist_ok=True)
    recs = [{'id': 900 + i, 'n': f'Rio guardado {i}', 'ty': '', 'src': 'Chile SIMBIO protected areas, layer 2 (MMA)', '_bb': [-73.5, -51.5, -72.5, -50.5],
             '_r': [[[-73.5, -51.5], [-72.5, -51.5], [-72.5, -50.5], [-73.5, -51.5]]], '_a': {}, 'code': '', 'dc': '', 'sid': sid} for i in range(3)]
    with gzip.open(t / 'cache/world/W-CL.json.gz', 'wt', encoding='utf-8') as f: json.dump({'cc': 'CL', 'detail': 0.01, 'thin': 60, 'recs': recs}, f)


L2 = 'https://arcgis.mma.gob.cl/server/rest/services/SIMBIO/SIMBIO_AP/FeatureServer/2'


def e2e(mode, t=None):
    t = t or e2e_dir()
    log = t / f'requests-{mode}.jsonl'; log.write_text('')
    env = dict(os.environ, COUNTRIES='CL', PYTHONDONTWRITEBYTECODE='1', KPC_WORLD_LAYER_MIN_URLS='{"featureserver/2": 0.12}', FAKE_LOG=str(log))
    for k in ('GEO_CACHE_MODE', 'GEO_CACHE', 'WB_DIR', 'KPC_WORLD_PARTS', 'KPC_WORLD_PART_DAYS'): env.pop(k, None)
    r = subprocess.run([sys.executable, '-B', str(t / 'runner.py'), str(SCRIPT), mode], cwd=t, env=env, capture_output=True, text=True, timeout=170)
    return t, r, [tuple(json.loads(x)) for x in log.read_text().splitlines()]


def states(t): return [json.load(open(f)) for f in sorted(t.glob('cache/world/parts/CL/*.state.json'))]


def required_test_6_held_country_publishes_nothing_then_reuses_finished_layers():
    # run 1: layer 0 finishes (checkpoint kept, marked done), layer 2 stalls -> CL held, exit 3, nothing published
    t, r, reqs = e2e('stall'); out = r.stdout + r.stderr
    st = states(t)
    check(r.returncode == 3 and 'HELD' in out and 'limit' in out, f'REQUIRED 6a (held with a finished layer saved): a stalled layer HOLDS CL: exit {r.returncode}')
    check((t / 'data/world-key/CL.json').read_bytes() == PREV and (t / 'data/world-key/index.json').read_bytes() == IDX
          and not (t / 'data/world-key/review/CL.md').exists() and not list(t.glob('cache/world/W-*')),
          'REQUIRED 6a: previous CL key and index.json byte-identical, no review page, no saved copy: nothing published')
    check(len(st) == 2 and sorted(bool(s.get('done')) for s in st) == [False, True],
          f"REQUIRED 6a: checkpoints kept: layer 0 finished (done), layer 2 in progress ({[(s['pages'], bool(s.get('done'))) for s in st]})")
    # run 2: layer 2 completes from its checkpoint; layer 0 is reused without reading its pages
    t, r, reqs = e2e('finish', t); out = r.stdout + r.stderr
    key = json.load(open(t / 'data/world-key/CL.json')) if r.returncode == 0 else {}
    l0 = [q for q in reqs if '/FeatureServer/0' in q[0]]; l2q = [q for q in reqs if q[0].endswith('FeatureServer/2/query')]
    check(r.returncode == 0 and key.get('counts', {}).get('matched') == 1 and key.get('counts', {}).get('areas', 0) > 1000,
          f"REQUIRED 6b: the next run writes CL with layer 0's saved records (exit {r.returncode}, {key.get('counts', {}).get('matched')} joined, "
          f"{key.get('counts', {}).get('areas')} areas)" + ('' if r.returncode == 0 else ': ' + out[-500:]))
    check(not [q for q in l0 if q[0].endswith('/query')] and len(l0) == 1,
          f'REQUIRED 6b: no feature request for the finished layer 0 (only its one metadata request, to check the layer key): {l0}')
    check(l2q and all('OBJECTID >' in (q[1] or '') for q in l2q), f'REQUIRED 6b: layer 2 resumed from its checkpoint, never from page 1 ({l2q[:2]})')
    check(not list(t.glob('cache/world/parts/CL/*')), 'REQUIRED 6b: once CL is written, its finished checkpoints (here: all of them) are deleted')


def required_test_7_no_deletion_when_the_key_write_fails():
    t, r, _ = e2e('stall')
    (t / 'data/world-key/CL.json').unlink(); (t / 'data/world-key/CL.json').mkdir()   # the key file cannot be written
    t, r, _ = e2e('finish', t)
    check(r.returncode not in (0, 3) and len(states(t)) == 2,
          f'REQUIRED 7 (delete only after the key is written): the key write fails (exit {r.returncode}): the checkpoints stay')



def required_test_9_written_country_keeps_in_progress_checkpoint():
    # run 1: layer 2 stalls but its saved copy covers it, so CL IS written; only the finished checkpoint (layer 0) is deleted
    t = e2e_dir(); saved_copy(t)
    t, r, _ = e2e('stall', t); out = r.stdout + r.stderr; st = states(t)
    check(r.returncode == 0 and (t / 'data/world-key/CL.json').read_bytes() != PREV and 'came from the saved copy' in out,
          f'REQUIRED 9a (written country keeps in-progress checkpoint): CL is written with layer 2 from its saved copy (exit {r.returncode})'
          + ('' if r.returncode == 0 else ': ' + out[-400:]))
    check(len(st) == 1 and not st[0].get('done') and st[0]['pages'] >= 1,
          f"REQUIRED 9a: after the write the finished checkpoint (layer 0) is gone and layer 2's in-progress one remains ({[(x['pages'], bool(x.get('done'))) for x in st]})")
    n = st[0]['n'] if st else -1
    # run 2: layer 2 resumes from the saved page, finishes, CL is written, and the now-finished checkpoint is deleted
    t, r, reqs = e2e('finish', t)
    l2q = [q for q in reqs if q[0].endswith('FeatureServer/2/query')]
    check(r.returncode == 0 and l2q and l2q[0][1] == f'(1=1) AND OBJECTID > {n}',
          f'REQUIRED 9b: next run resumes layer 2 from the saved page: first feature request {l2q[:1]} (checkpoint held {n} records)')
    check(r.returncode == 0 and not list(t.glob('cache/world/parts/CL/*')), 'REQUIRED 9b: layer 2 finished and CL written: its checkpoint is deleted too')


required_test_6_held_country_publishes_nothing_then_reuses_finished_layers()
required_test_9_written_country_keeps_in_progress_checkpoint()
required_test_7_no_deletion_when_the_key_write_fails()
t, r, _ = e2e('ok')
key = json.load(open(t / 'data/world-key/CL.json')) if r.returncode == 0 else {}
check(r.returncode == 0 and key.get('counts', {}).get('matched') == 1 and not list(t.glob('cache/world/parts/CL/*')),
      f'end to end (control): every layer answering writes CL in one run (exit {r.returncode}), no checkpoint left')

# ------------------------------------------------------------------ rules hashes: only the world key moves (Brandon OK'd)
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_key_freeze as KZ  # noqa: E402
check(KZ.rules_hash('us-key') == 'a066624520b4' and KZ.rules_hash('ca-key') == '8feccbb7d9ee', 'US a066624520b4 and CA 8feccbb7d9ee rules hashes unchanged')
check(KZ.rules_hash('world-key') == '6a5969a25d2c', f"world rules hash moved on purpose once: 1b50faf1dfe8 -> 6a5969a25d2c (now {KZ.rules_hash('world-key')})")
check(json.load(open(ROOT / '.github/key-rules-version.json'))['world-key'] == 'v5b', 'key-rules-version.json not bumped (repo convention: a rule-script change moves the hash by itself; prior world moves did not bump)')
ch = subprocess.run(['git', 'diff', '--name-only', BASE, '--', '.github/scripts/'], cwd=ROOT, capture_output=True, text=True).stdout.split()
# Only RULE files matter here: other patches combined with this one (e.g. Tracts Part 1) may change NOT_RULES scripts.
_rules = set(sum(KZ.RULE_FILES.values(), []))
ch = [c for c in ch if c in _rules]
check(ch == ['.github/scripts/kpc_world_key.py'], f'only kpc_world_key.py changed among the RULE files (kpc_match / kpc_key_facts / kpc_number_rules untouched): {ch}')


# ================================================================== the five tests named in Brandon's Part 2 handoff (Nov 7)
def required_test_1_ch_no_get_no_natura_source():
    w = load()
    eu_n2k = {c: any('Natura2000Sites' in str(s[2]) for s in w['SRC'][c]) for c in w['EU']}
    check(not eu_n2k['CH'] and not eu_n2k['NO'] and all(v for c, v in eu_n2k.items() if c not in ('CH', 'NO')),
          'REQUIRED 1 (CH/NO get no Natura source): CH and NO read no EEA Natura 2000; the 22 other EU countries still do')


def required_test_2_line_point_layers_request_no_geometry():
    res = {}
    for gt in ('esriGeometryPolyline', 'esriGeometryPoint', 'esriGeometryMultipoint', 'esriGeometryPolygon'):
        lay = Layer(1500, geom=gt); w, _, _ = new_ns(lay, parts=tempfile.mkdtemp()); w['pull_arcgis1']('L', URL, '1=1')
        res[gt] = {q['returnGeometry'] for q in lay.queries}
    check(res == {'esriGeometryPolyline': {'false'}, 'esriGeometryPoint': {'false'}, 'esriGeometryMultipoint': {'false'}, 'esriGeometryPolygon': {'true'}},
          f'REQUIRED 2 (line/point layers request no geometry): returnGeometry per layer type {res}')


def required_test_3_checkpoint_resume_on_a_fake_3_page_layer():
    d = tempfile.mkdtemp()
    whole = new_ns(Layer(2500), parts=tempfile.mkdtemp())[0]['pull_arcgis1']('L', URL, '1=1')   # 3 pages: 1000 + 1000 + 500
    lay = Layer(2500, kill_on=3); w, _, _ = new_ns(lay, parts=d)
    try: w['pull_arcgis1']('L', URL, '1=1'); stopped = False
    except Kill: stopped = True
    s = state_of(d)
    lay = Layer(2500); w, _, _ = new_ns(lay, parts=d); got = w['pull_arcgis1']('L', URL, '1=1')
    check(stopped and s and s['pages'] == 2 and len(lay.queries) == 1 and 'OBJECTID > 2000' in lay.queries[0]['where']
          and got == whole and len(got) == 2500 and (state_of(d) or {}).get('done') is True and state_of(d)['n'] == 2500,
          'REQUIRED 3 (checkpoint resume on a fake 3-page layer): stopped in page 3 -> checkpoint of 2 pages -> the next run asks only page 3'
          ' (OBJECTID > 2000), returns all 2,500 records identical to an unbroken read, checkpoint marked done')


def required_test_4_stalled_layer_still_holds():
    ns4, held4, saved4, notes4, _ = source_loop(None, tempfile.mkdtemp())
    check(held4 == ['AU'] and not ns4['went_on'] and saved4 == [] and not any(r['src'] == HYDRO[0] for r in ns4['recs']),
          'REQUIRED 4 (stalled layer still HOLDs): the country is held, no partial record kept, nothing saved, previous key stays (exit 3 end to end above)')


def required_test_5_us_and_ca_hashes_unchanged():
    check((KZ.rules_hash('us-key'), KZ.rules_hash('ca-key')) == ('a066624520b4', '8feccbb7d9ee'),
          'REQUIRED 5 (US and CA hashes unchanged): us a066624520b4, ca 8feccbb7d9ee')


def required_test_8_finished_checkpoint_older_than_7_days_is_read_again():
    res = {}
    for days in (6, 8):
        d = tempfile.mkdtemp(); new_ns(Layer(2500), parts=d)[0]['pull_arcgis1']('L', URL, '1=1')   # finished: done checkpoint
        lay = Layer(2500); w, clock, notes = new_ns(lay, parts=d); clock.t += days * 86400
        got = w['pull_arcgis1']('L', URL, '1=1')
        res[days] = (len([u for u in lay.urls if '/query' in u]), len(got))
    check(res == {6: (0, 2500), 8: (3, 2500)},
          f'REQUIRED 8 (finished checkpoint older than 7 days): 6 days old = reused, no page read; 8 days old = ignored, all 3 pages read again {res}')
    d = tempfile.mkdtemp(); new_ns(Layer(2500), parts=d)[0]['pull_arcgis1']('L', URL, '1=1')
    lay = Layer(2500, edit=2); got = new_ns(lay, parts=d)[0]['pull_arcgis1']('L', URL, '1=1')
    check(len([u for u in lay.urls if '/query' in u]) == 3 and len(got) == 2500,
          'REQUIRED 8: a finished checkpoint of another layer version (last edit date changed) is thrown away and the layer read fresh')
    d = tempfile.mkdtemp(); lay = Layer(0); got = new_ns(lay, parts=d)[0]['pull_arcgis1']('L', URL, '1=1')
    check(got == [] and parts_of(d) == [], 'an empty read leaves no checkpoint (it is asked again next run, and EMPTY still holds the country)')


for _t in (required_test_1_ch_no_get_no_natura_source, required_test_8_finished_checkpoint_older_than_7_days_is_read_again, required_test_2_line_point_layers_request_no_geometry,
           required_test_3_checkpoint_resume_on_a_fake_3_page_layer, required_test_4_stalled_layer_still_holds,
           required_test_5_us_and_ca_hashes_unchanged):
    _t()
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
