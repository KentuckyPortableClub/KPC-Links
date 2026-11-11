#!/usr/bin/env python3
"""kpc_us_key.py reads and joins (owner rule, 2026-11-10):
1. a state layer is read whole or not at all (kpc_master.read_complete): a real page cap below the reported maxRecordCount,
   a box-after-window server, a count off by one (fails closed, quickly), never a partial layer;
2. PAD-US: a short page without exceededTransferLimit is not the end; a server that ignores resultOffset fails the state;
3. the Vermont ANR layer is listed once; the layer file counts DISTINCT object ids;
4. a park left with no joined record by the one-record-two-parks pass is a pin, not 'official';
5. overrides.json 'none' only clears the to-check list (a later official join stays; see test_us_key_corridor_pins_nov10r.py);
6. one set of host rules: KPC_SAVED_ONLY_HOSTS only ADDS hosts (it used to replace the list in this script).
Offline: the reads go to a stand-in server object; nothing leaves the process."""
import json, os, pathlib, re, subprocess, sys, textwrap, types, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


def chunk(a, b): return SRC[SRC.index(a):SRC.index(b)]


class Server:
    """rows [(oid, in_box)]; cap = the page the server really sends (it reports maxrec); window = cut rows first, box after."""
    def __init__(self, rows, cap=1000, window=False, ids=True, count_delta=0):
        self.rows, self.cap, self.window, self.ids, self.count_delta, self.calls = rows, cap, window, ids, count_delta, []

    def answer(self, url):
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query)); self.calls.append(q)
        box = 'geometry' in q
        inb = [r for r in self.rows if r[1] or not box]
        if q.get('returnCountOnly') == 'true': return {'count': len(inb) + self.count_delta}
        if q.get('returnIdsOnly') == 'true':
            return {'objectIdFieldName': 'OBJECTID', 'objectIds': [r[0] for r in inb]} if self.ids else {'error': {'code': 400, 'message': 'no'}}
        if 'objectIds' in q:
            want = {int(x) for x in q['objectIds'].split(',')}; page = [r for r in self.rows if r[0] in want][:self.cap]
        else:
            off, n = int(q.get('resultOffset', 0)), min(int(q.get('resultRecordCount') or self.cap), self.cap)
            page = [r for r in self.rows[off:off + n] if r[1] or not box] if self.window else inb[off:off + n]
        return {'features': [{'attributes': {'OBJECTID': r[0], 'NAME': f'Tract {r[0]}'}, 'geometry': {'rings': [[[0, 0], [0, 1], [1, 1], [0, 0]]]}} for r in page]}


class Resp:
    def __init__(self, b): self.b = b
    def read(self): return self.b
    def __enter__(self): return self
    def __exit__(self, *a): return False


def make_ns(server, xs, maxrec=1000):
    opener = types.SimpleNamespace(open=lambda u, timeout=0: Resp(json.dumps(server.answer(u)).encode()))
    kmaster = types.SimpleNamespace(checked_opener=lambda check, handlers=(): opener, live_ok=lambda u: (True, ''),
                                    LiveNotAllowed=type('LiveNotAllowed', (Exception,), {}), HUB_RE=re.compile(r'^$'), HUB_DELAY=60.0)
    ns = {'urllib': types.SimpleNamespace(request=types.SimpleNamespace(Request=lambda u, headers=None, data=None: u + '?' + data.decode() if data else u), parse=urllib.parse),
          'json': json, 're': re, 'time': types.SimpleNamespace(sleep=lambda s: None, strftime=lambda f: '2026-11-10', monotonic=lambda: 0.0),
          'kpc_host_pace': types.SimpleNamespace(host_of=lambda u: urllib.parse.urlsplit(str(u)).netloc.lower(), wait=lambda h: None),
          'saved_only': lambda u: False, 'DETAIL': 0.001, 'PREC': 5, 'PAGE': 200, 'st_box': lambda st: [-80.0, 40.0, -70.0, 45.0],
          'XS': xs, 'KMASTER': kmaster, 'HOP_HANDLERS': (), 'resolve': lambda pre, url, nf, af: (url, nf, af, 'OBJECTID'),
          'LAYER_MAXREC': {x[0]: maxrec for x in xs}, 'SF': types.SimpleNamespace(mapping=lambda *a: {}, extra_fields=lambda m: []),
          'SFIELDS': {}, 'SFMAP': {}, 'RAWF': {}, 'XCOUNT': {}, 'LAYER_OUT': pathlib.Path('/nonexistent'), '_layer_in': lambda st, pre: None,
          'notes': [], 'FAILED_READ': set(), 'OVR': {}, 'kinds': lambda nm: set(), 'norm': lambda s: s.lower(), '_dup': lambda *a: False,
          '_nf': lambda s: s, '_sane_ac': lambda a, b: a, '_num': lambda v: v or 0, 'bbox': lambda g: [0, 0, 1, 1], 'zip_state': lambda st, have: []}
    ns['notice'] = lambda t, m: ns['notes'].append(m)
    exec(compile(chunk('def layer_page_size', 'FWS = ') + chunk('def extra_state', 'def _in_box'), 'kpc_us_key.py', 'exec'), ns)
    return ns


LAY = ('sgvtz', 'https://gis.example.gov/arcgis/rest/services/x/MapServer/0/query', 'NAME', '', set(), 'Example lands (land, state GIS table)', 'STAT', {'VT'}, {})
rows = [(i, i % 16 != 0) for i in range(1, 3001)]
inbox = {r[0] for r in rows if r[1]}


def read(server, maxrec=1000):
    ns = make_ns(server, [LAY], maxrec)
    out = ns['extra_state']('VT', {}, only={'sgvtz'})
    return ns, out, {f['attributes']['OBJECTID'] for f in ns['RAWF'].get('sgvtz', [])}


# 1. state layers
for win in (False, True):
    for ids in (True, False):
        ns, out, got = read(Server(rows, cap=500, window=win, ids=ids))
        check(f'real page cap 500 under a reported 1000 (box after window={win}, ids-only={ids}): every record ({len(got)} of {len(inbox)})',
              got == inbox and len(out) == len(inbox) and 'VT' not in ns['FAILED_READ'])
old = Server(rows, cap=500, window=True, ids=False)   # what the #117 window loop did: windows of the reported maxRecordCount
seen, off = set(), 0
while off < len(rows):
    seen |= {f['attributes']['OBJECTID'] for f in old.answer(LAY[1] + '?' + urllib.parse.urlencode({'geometry': '1', 'resultOffset': off, 'resultRecordCount': 1000}))['features']}
    off += 1000
check(f'... the old window step (the reported 1000) skipped rows: {len(seen)} of {len(inbox)}', len(seen) < len(inbox))
sv = Server(rows, count_delta=1)
ns, out, got = read(sv)
check(f'count one too high: the layer is NOT used (no partial layer: {len(out)} records), the state is marked failed', not out and not got and 'VT' in ns['FAILED_READ'])
check(f'count one too high: failed after {len(sv.calls)} requests (no walk through empty windows)', len(sv.calls) <= 3000 // 500 + 4)
ns, out, got = read(Server(rows))
check('a normal layer: no "window by window" notice', got == inbox and not any('window by window' in m for m in ns['notes']))

# 2. PAD-US: pages of 150 although PAGE=500 asks for more, no exceededTransferLimit
pns = {'time': types.SimpleNamespace(sleep=lambda s: None, monotonic=lambda: 0.0), 'KMASTER': types.SimpleNamespace(LAYER_MINUTES=60.0), 'NAME_KEEP': False, '_passes_load': lambda a: True, '_shape': lambda a, f: a,
       'keep_names': lambda P, st: ({}, {}), 'notice': lambda t, m: None, 'NAME_KEEP_HIT': [], 'Q': 'https://padus.example.gov/query', 'COUNT': [1200]}
pns['count_query'] = lambda url, q, box=True: pns['COUNT'][0] if q.get('where') == "State_Nm='VT'" and not box else None
exec(compile(chunk('def pad_state(st, P=None):', 'SAVED_HIT = []'), 'kpc_us_key.py', 'exec'), pns)
PAD = [{'attributes': {'OBJECTID': i, 'Unit_Nm': f'Area {i}'}} for i in range(1, 1201)]
pns['page'] = lambda st, off: {'features': PAD[off:off + 150]}
recs, n = pns['pad_state']('VT')
check(f'PAD-US: a 150-record page is not the last page (read {n} of {len(PAD)}; the old loop stopped at 150)', n == len(PAD) and len(recs) == len(PAD))
pns['page'] = lambda st, off: {'features': PAD[:150]}
try: pns['pad_state']('VT'); err = None
except RuntimeError as e: err = e
check(f'PAD-US: a server that ignores resultOffset fails the state ({err})', err is not None and 'again' in str(err))
pns['page'] = lambda st, off: {'features': (PAD[off:off + 150] + PAD[off:off + 2]) if off < len(PAD) else []}
recs, n = pns['pad_state']('VT')
check(f'PAD-US: a row sent twice is one record ({n})', n == len(PAD) and len({a["OBJECTID"] for a in recs}) == len(recs) == len(PAD))
for cnt, what in ((1201, 'one more than read'), (None, 'no count')):
    pns['COUNT'][0] = cnt; pns['page'] = lambda st, off: {'features': PAD[off:off + 150]}
    try: pns['pad_state']('VT'); err = None
    except RuntimeError as e: err = e
    check(f'PAD-US: the layer count ({what}) is not met: the state fails closed ({err})', err is not None and 'SHORT' in str(err))
pns['COUNT'][0] = 1200

# 3. Vermont ANR listed once; distinct ids in the layer file
xs = chunk('XS = [', '# Oct 24 (Brandon')
check('XS lists the Vermont ANR lands layer (vta) once', xs.count("('vta', ") == 1)
check('XS has no prefix twice', len(re.findall(r"^\s*\('([a-z]+)',", xs, re.M)) == len(set(re.findall(r"^\s*\('([a-z]+)',", xs, re.M))))
written = []
wns = {'XS': [LAY], 'RAWF': {'sgvtz': [{'attributes': {'OBJECTID': i}, 'geometry': None} for i in (1, 2, 3)] * 2}, 'RESOLVED': {}, 'time': types.SimpleNamespace(strftime=lambda f: '2026-11-10'),
       '_layer_in': lambda st, pre: None, '_save_row': lambda a: a, 'layer_live_count': lambda *a: 3, 'notice': lambda t, m: None, 'LAYER_OUT': '/x', 'st_box': lambda st: None,
       'KMASTER': types.SimpleNamespace(prefix_of=lambda o: re.match(r'[a-z]*', str(o)).group(0), esri_to_geojson=lambda g: None, layer_file_path=lambda *a: a,
                                        write_layer_file=lambda p, meta, feats: written.append((meta, feats)))}
exec(compile(chunk('def _write_layer_files', 'def save_cache'), 'kpc_us_key.py', 'exec'), wns)
wns['_write_layer_files']('VT', {'sgvtz'}, [])
check(f"layer file: the same 3 records read twice count 3 (count_raw {written[-1][0]['count_raw']})", written[-1][0]['count_raw'] == 3 and len(written[-1][1]) == 3)

# 4. one-record-two-parks: no joined record left = pin
blk = SRC[SRC.index('    try:\n        _by = {}\n'):SRC.index("    except Exception as _e: notice(f'US key {st}', f'one-record-two-parks pass skipped")]
blk = textwrap.dedent(blk).replace('try:\n', 'if True:\n', 1)
KIND = {'Woodson State Wildlife Area': {'wma'}, 'Woodson State Fishing Lake': {'lake'}}
parks = {'US-1': {'n': 'Woodson State Wildlife Area', 'm': [['sgks5', 'Woodson State Wildlife Area', 10, 'name']], 'g': 'official'},
         'US-2': {'n': 'Woodson State Fishing Lake', 'm': [['sgks5', 'Woodson State Wildlife Area', 10, 'name']], 'g': 'official'}}
exec(compile(blk, 'kpc_us_key.py', 'exec'), {'parks': parks, 'kinds': lambda s: KIND.get(s, set()), 're': re, 'notice': lambda t, m: None, 'st': 'KS'})
check(f"one-record-two-parks: the park that gave its only record back is a pin ({parks['US-2']['g']}), the other keeps it",
      parks['US-2']['m'] == [] and parks['US-2']['g'] == 'pin' and parks['US-1']['g'] == 'official' and parks['US-2']['c'])

# 5. 'none' only clears the to-check list (no blanket pass over the joins: a later official join stays)
check("'none' is applied only to the to-check list, never as a last pass over the joins",
      SRC.count("ov.get('none')") >= 1 and "if ov.get('none'): c = []" in SRC and "(overrides.json none)" not in SRC and "_p['m'], _p['c'], _p['g'] = [], [], 'pin'" not in SRC)

# 6. host rules: KPC_SAVED_ONLY_HOSTS adds, never replaces (the old copy here replaced the default list)
code = textwrap.dedent('''
    import os, re, sys, urllib.parse
    s = open(sys.argv[1], encoding='utf-8').read()
    ns = {'os': os, 're': re, 'urllib': __import__('urllib.parse')}
    exec(compile(s[s.index('SAVED_ONLY_HOSTS = '):s.index('def notice(')], 'k', 'exec'), ns)
    so = ns['saved_only']
    print(so('https://apps.fs.usda.gov/arcx/rest/services/x/MapServer/0'), so('https://gis.example.net/x'), so('https://services7.arcgis.com/x'), so('https://gis.blm.gov/x'))''')
r = subprocess.run([sys.executable, '-c', code, str(ROOT / '.github/scripts/kpc_us_key.py')], capture_output=True, text=True, cwd=ROOT,
                   env=dict(os.environ, KPC_SAVED_ONLY_HOSTS='gis.example.net'))
check(f'KPC_SAVED_ONLY_HOSTS=gis.example.net: apps.fs.usda.gov stays saved-copy only, the extra host is added ({r.stdout.strip() or r.stderr[-200:]})',
      r.stdout.split() == ['True', 'True', 'True', 'False'])
check('no copy of the host rules is left in the key (no services regex, no never-contact list)',
      'arcgis\\.com$' not in SRC and "NEVER_HOSTS = {" not in SRC and "_ARCGIS_SERVICES" not in SRC)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
