#!/usr/bin/env python3
"""kpc_ca_key.py and kpc_world_key.py reads (owner rule, 2026-11-10):
Canada: CPCAD, every provincial layer and the live top-up are read whole or not at all (kpc_master.read_complete, through the
key's own get()); a layer that fails keeps nothing from this read, its source falls back to the saved copy as a whole, and no
saved copy is written in a run where a source failed (the world key's rule).
World: a short page without exceededTransferLimit is not the end; the layer's own count decides (short = a FAILED layer, never
a partial one); a layer with no count is not used; a 'Pagination is not supported' layer is read whole by id, not cut at one page.
Both: one set of host rules (kpc_master.live_ok); KPC_SAVED_ONLY_HOSTS only adds hosts.
Offline: stand-in servers inside the process."""
import json, os, pathlib, re, subprocess, sys, textwrap, types, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / '.github/scripts'))
CA = (ROOT / '.github/scripts/kpc_ca_key.py').read_text(encoding='utf-8')
WK = (ROOT / '.github/scripts/kpc_world_key.py').read_text(encoding='utf-8')
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


class Layer:
    """n records; cap = the page really sent (maxRecordCount says 1000); paging=False answers 'Pagination is not supported';
    alias=True keys attributes by alias (Quebec's MRNF); count: True | None (no count) | an int offset."""
    def __init__(self, n, cap=1000, paging=True, ids=True, alias=False, count=True, flag=False):
        self.__dict__.update(locals()); del self.__dict__['self']
        self.queries = []

    def info(self):
        return {'maxRecordCount': 1000, 'objectIdField': 'OBJECTID', 'geometryType': 'esriGeometryPolygon',
                'fields': [{'name': 'OBJECTID', 'alias': 'Identifiant', 'type': 'esriFieldTypeOID'}, {'name': 'NAME', 'alias': 'Nom', 'type': 'esriFieldTypeString'}],
                **({} if self.paging else {'advancedQueryCapabilities': {'supportsOrderBy': False}})}   # no object-id paging either

    def feat(self, o):
        a = {'Identifiant': o, 'Nom': f'Parc {o}'} if self.alias else {'OBJECTID': o, 'NAME': f'Parc {o}'}
        return {'attributes': a, 'geometry': {'rings': [[[-70, 46], [-69.9, 46], [-69.9, 46.1], [-70, 46]]]}}

    def query(self, q):
        self.queries.append(q)
        if q.get('returnCountOnly') == 'true':
            return {'error': {'code': 400, 'message': 'no count'}} if self.count is None else {'count': self.n + (0 if self.count is True else self.count)}
        if q.get('returnIdsOnly') == 'true':
            return {'objectIdFieldName': 'OBJECTID', 'objectIds': list(range(1, self.n + 1))} if self.ids else {'error': {'code': 400, 'message': 'no'}}
        if 'objectIds' in q:
            return {'features': [self.feat(int(x)) for x in q['objectIds'].split(',')][:self.cap]}
        if 'resultOffset' in q and not self.paging: return {'error': {'code': 400, 'message': 'Pagination is not supported.'}}
        m = re.search(r'OBJECTID > (\d+)', q.get('where', '')); last = int(m.group(1)) if m else 0
        i0 = last + int(q.get('resultOffset') or 0)
        i1 = min(self.n, i0 + min(int(q.get('resultRecordCount') or 1000), self.cap))
        out = {'features': [self.feat(o) for o in range(i0 + 1, i1 + 1)]}
        if self.flag and i1 < self.n: out['exceededTransferLimit'] = True
        return out


# ------------------------------------------------------------------ Canada
ca = types.ModuleType('ca'); ca.__dict__['__file__'] = str(ROOT / '.github/scripts/kpc_ca_key.py')
exec(compile(CA.split('\nrecs = cload()')[0], 'kpc_ca_key.py', 'exec'), ca.__dict__)
LU = 'https://geo.example.gouv.qc.ca/arcgis/rest/services/x/MapServer/3'


def ca_read(lay):
    ca.get = lambda url, params, tries=5, post=False: lay.query(params) if url.endswith('/query') else lay.info()
    try: return ca.arc_read(LU, lay.info(), 'Québec test', '*', extra={'returnGeometry': 'true'}), None
    except Exception as e: return None, e  # noqa: BLE001


fs, err = ca_read(Layer(2500, cap=300, ids=False))
check(f'Canada: a real page cap of 300 under a reported 1000 (no ids-only): every record ({len(fs or [])} of 2500; the old loop stopped at 300)', fs and len(fs) == 2500)
fs, err = ca_read(Layer(1200, paging=False, alias=True))
check(f'Canada: a layer that will not page and answers with aliases: read whole by id ({len(fs or [])} of 1200), ids from the alias field',
      fs and len(fs) == 1200 and len({f['attributes']['Identifiant'] for f in fs}) == 1200)
fs, err = ca_read(Layer(1200, count=1))
check(f'Canada: a layer whose count is not reached is refused, nothing returned ({type(err).__name__})', fs is None and err is not None)
fs, err = ca_read(Layer(1200, count=None))
check('Canada: a layer that gives no count is refused', fs is None and err is not None)
body = CA[CA.index('    def arc_pull(label, url, nf):'):CA.index('        return got\n\n\n    extra = 0')]
check('Canada arc_pull: a layer that fails adds nothing (its records join only after the whole layer is read) and marks its source failed',
      'got += part' in body and body.index('arc_read(lu, li') < body.index('got += part') and 'ERRLAB.add(label); continue' in body and 'off += len(fs)' not in body)
top = CA[CA.index("if recs is not None and CMODE == 'use':"):CA.index('if recs is None:\n    # ---------------- pull CPCAD')]
check('Canada live top-up: a layer joins the saved copy only when read whole (no [:6000] id cut)', '[:6000]' not in top and 'recs += _new' in top and 'arc_read(_u, _li' in top)
check('Canada CPCAD: read whole by read_complete, else the old files are kept', "fs = arc_read(f'{SVC}/{lid}'" in CA and "CPCAD not read whole" in CA)
after = CA[CA.index('if recs is None:\n    # ---------------- pull CPCAD'):CA.index('PRIV = re.compile(')]
saves = [l for l in after.splitlines() if 'csave(recs)' in l]
check(f'Canada: no saved copy is written in a run where a source failed ({len(saves)} saves after the live read, each gated)',
      saves and all('not CA_READ_FAILED' in l for l in saves) and 'CA_READ_FAILED = bool(_ERR or' in after)
fb = after[after.index('        topped = 0\n'):after.index('        if topped:')]
check('Canada: a failed source takes ALL its records from the saved copy (live records of that source are dropped first)',
      "recs = [r for r in recs if r.get('src') != lab]" in fb and 'if lab in have: continue' not in fb)

# ------------------------------------------------------------------ world
def wload():
    ns = {'__name__': 'kpc_world_key_test', '__file__': str(ROOT / '.github/scripts/kpc_world_key.py')}
    exec(compile(WK.split('\nfor cc in COUNTRIES:')[0], 'kpc_world_key.py', 'exec'), ns)
    sys.excepthook = sys.__excepthook__
    return ns


class Resp:
    def __init__(self, b): self.b, self.p = b, 0
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read1(self, n): c = self.b[self.p:self.p + n]; self.p += len(c); return c


g = wload()
URL = 'https://gis.example.gov.au/arcgis/rest/services/x/MapServer/0'


def wread(lay):
    ns = g; ns['notice'] = lambda t, m: None; ns['PARTS_ON'] = False   # the loaded functions read these globals
    ns['time'] = types.SimpleNamespace(monotonic=lambda: 0.0, sleep=lambda s: None, time=lambda: 0.0, strftime=lambda *a: '2026-11-10')
    def op(req, timeout=None):
        p = urllib.parse.urlsplit(req.full_url)
        return Resp(json.dumps(lay.query(dict(urllib.parse.parse_qsl(p.query))) if p.path.endswith('/query') else lay.info()).encode())
    ns['_open'] = op
    try: return ns['pull_arcgis1']('Example layer', URL, '1=1'), None, ns
    except Exception as e: return None, e, ns  # noqa: BLE001


got, err, ns = wread(Layer(2500, cap=300))
check(f'world: a real page cap of 300 under a reported 1000: every record ({len(got or [])} of 2500; the old end test stopped at 300)', got and len(got) == 2500)
got, err, ns = wread(Layer(2500, cap=300, count=5))
check(f'world: the count is not reached: a FAILED layer, no partial list ({type(err).__name__})', got is None and isinstance(err, ns['LayerStall']))
got, err, ns = wread(Layer(2500, count=None))
check(f'world: a layer that gives no count is not used ({err})', got is None and isinstance(err, ns['LayerStall']) and 'count' in str(err))
lay = Layer(2500, paging=False)
got, err, ns = wread(lay)
check(f'world: "Pagination is not supported": read whole by id ({len(got or [])} of 2500; the old branch kept one page of 1000)',
      got and len(got) == 2500 and len({r["id"] for r in got}) == 2500 and any('objectIds' in q for q in lay.queries))
got, err, ns = wread(Layer(2500, paging=False, ids=False))
check('world: no paging and no ids-only: a FAILED layer (never one silent page)', got is None and err is not None)
got, err, ns = wread(Layer(2500, flag=True))
check('world: a normal layer is read whole, every record once', got and len(got) == 2500 and len({r['id'] for r in got}) == 2500)

# ------------------------------------------------------------------ one set of host rules
for fn, a, b in (('kpc_ca_key.py', 'SAVED_ONLY_HOSTS = ', 'def get('), ('kpc_world_key.py', 'SAVED_ONLY_HOSTS = ', 'def fetch_bytes(')):
    code = textwrap.dedent('''
        import os, re, sys
        s = open(sys.argv[1], encoding='utf-8').read()
        ns = {'os': os, 're': re, 'urllib': __import__('urllib.parse')}
        exec(compile(s[s.index(sys.argv[2]):s.index(sys.argv[3])], 'k', 'exec'), ns)
        so = ns['saved_only']
        print(so('https://apps.fs.usda.gov/x'), so('https://gis.example.net/x'), so('https://services-eu1.arcgis.com/x'), so('https://maps.gov.bc.ca/x'))''')
    r = subprocess.run([sys.executable, '-c', code, str(ROOT / '.github/scripts' / fn), a, b], capture_output=True, text=True, cwd=ROOT,
                       env=dict(os.environ, KPC_SAVED_ONLY_HOSTS='gis.example.net'))
    src = CA if fn == 'kpc_ca_key.py' else WK
    check(f'{fn}: KPC_SAVED_ONLY_HOSTS adds a host, never drops apps.fs.usda.gov; no copy of the rules is left ({r.stdout.strip() or r.stderr[-200:]})',
          r.stdout.split() == ['True', 'True', 'True', 'False'] and '_ARCGIS_SERVICES' not in src and 'NEVER_HOSTS = {' not in src)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
