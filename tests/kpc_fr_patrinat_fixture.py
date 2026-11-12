"""Shared offline harness for the job 6 tests (KPC owner, 2026-11-11): the world key's French PatriNat layers on SYNTHETIC fixtures.

Not a test file (the full suite runs tests/test_*.py only). Every socket is refused before anything runs (zero network).
  load_prefix()      the builder's own code up to the country loop (SRC, pull_wfs, arcgis_rec, wsave ...), nothing run
  records(g, ...)    the fixture pages read through the builder's own pull_wfs / arcgis_rec (a stand-in fetch answers from the files)
  build(g, recs, ov) the real kpc_world_key.py, COUNTRIES=FR, GEO_CACHE_MODE=only, on a saved copy of `recs`, in a temp folder;
                     returns the FR key file it wrote (data/world-key/FR.json) and the saved outline shards
The fixtures (tests/fixtures/world_fr_patrinat_nov11/) are SYNTHETIC: real ids and names, made-up rectangles. See their README."""
import json, os, pathlib, re, shutil, socket, subprocess, sys, tempfile, urllib.parse


def _no_net(*a, **k): raise RuntimeError('network refused in this test')


socket.socket.connect = _no_net; socket.create_connection = _no_net; socket.getaddrinfo = _no_net

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.github/scripts/kpc_world_key.py'
FX = ROOT / 'tests/fixtures/world_fr_patrinat_nov11'
WFS = 'https://data.geopf.fr/wfs/ows'
EEA = 'https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/'
# the three layers job 6 adds (label, WFS type name) and the record each of the three parks needs
NEW = [('IGN Géoplateforme ZNIEFF type II sea', 'patrinat_znieff2_mer:znieff2_mer'),
       ('IGN Géoplateforme Conservatoire du littoral', 'patrinat_cdl:cdl'),
       ('IGN Géoplateforme RNN protection perimeters', 'patrinat_pprnn:pprnn')]
OLD_IGN = [('IGN Géoplateforme ZNIEFF type I', 'patrinat_znieff1:znieff1'), ('IGN Géoplateforme ZNIEFF type II', 'patrinat_znieff2:znieff2'),
           ('IGN Géoplateforme ZNIEFF type I sea', 'patrinat_znieff1_mer:znieff1_mer')]
PARKS3 = {'FR-10548': 'znieff2_mer.7', 'FR-10432': 'cdl.502', 'FR-11106': 'pprnn.1'}
DATA = next((pathlib.Path(d) for d in (os.environ.get('KPC_DATA'), os.environ.get('DATA'), ROOT.parent / 'kpc-data', ROOT.parent / 'kpcdata')
             if d and (pathlib.Path(d) / 'data/parkinfo/FR.json').is_file()), None)
# the website's world grade (kpc-bounds.js worldKey): official only when one join's how-text starts with one of these
JS_OFFICIAL = re.compile(r'^(name|same name|exact name)')


def fx(name): return json.load(open(FX / name, encoding='utf-8'))


def load_prefix():
    """kpc_world_key.py up to (not including) the country loop: the source table and the readers, exactly as the builder has them."""
    src = SCRIPT.read_text(encoding='utf-8')
    g = {'__name__': 'kpc_world_key_prefix', '__file__': str(SCRIPT)}
    cwd = os.getcwd(); os.chdir(ROOT)   # it reads data/world-key/*.json relative to the checkout (read only; nothing is written)
    try: exec(compile(src[:src.index('\nfor cc in COUNTRIES:')], str(SCRIPT), 'exec'), g)
    finally: os.chdir(cwd)
    return g


def pages():
    """WFS type name -> the synthetic GeoServer page for it."""
    out = {}
    for f in sorted(FX.glob('wfs-*.json')):
        d = json.load(open(f, encoding='utf-8')); out[d['_layer']] = d
    return out


def read_wfs(g, label, typ, pg=None, asked=None):
    """One layer through the builder's own pull_wfs; a stand-in fetch answers from the fixture page (no request goes out)."""
    pg = pg if pg is not None else pages()
    def fetch(u, tries=None, timeout=None, deadline=None):
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(u).query))
        if asked is not None: asked.append(q)
        return json.loads(json.dumps(pg.get(q.get('TYPENAMES'), {'type': 'FeatureCollection', 'features': []})))
    old = g['fetch']; g['fetch'] = fetch
    try: return g['pull_wfs'](label, WFS, typ)
    finally: g['fetch'] = old


def read_eea(g, label, url, name):
    return [g['arcgis_rec'](label, url, 'OBJECTID', f) for f in fx(name)['features']]


def src_of(g, label):
    return next(s for s in g['SRC']['FR'] if s[0] == label)


def records(g, new=True, pg=None):
    """The fixture set: stand-ins for what the key reads today near the three pins (+ the three new layers when new=True)."""
    pg = pg if pg is not None else pages()
    out = []
    def add(rs, s):
        for r in rs: r['sid'] = g['src_id'](s)
        out.extend(rs)
    add(read_wfs(g, OLD_IGN[0][0], OLD_IGN[0][1], pg), src_of(g, OLD_IGN[0][0]))
    add(read_eea(g, 'EEA nationally designated areas', EEA + 'CDDA_Dyna_WM/MapServer/4', 'eea-cdda.json'), src_of(g, 'EEA nationally designated areas'))
    add(read_eea(g, 'EEA Natura 2000', EEA + 'Natura2000Sites/MapServer/2', 'eea-n2k.json'), src_of(g, 'EEA Natura 2000'))
    if new:
        for label, typ in NEW: add(read_wfs(g, label, typ, pg), src_of(g, label))
    return out


def parks():
    """FR park list: KPC-Data's whole data/parkinfo/FR.json when that checkout is here, else the fixture's small list."""
    if DATA: return json.load(open(DATA / 'data/parkinfo/FR.json', encoding='utf-8')), 'KPC-Data data/parkinfo/FR.json'
    return fx('parks-fr-subset.json'), 'fixture parks-fr-subset.json (no KPC-Data checkout)'


RUNNER = ("import socket, runpy, sys\n"
          "def _n(*a, **k): raise RuntimeError('network refused in this test')\n"
          "socket.socket.connect = _n; socket.create_connection = _n; socket.getaddrinfo = _n\n"
          "sys.argv = [sys.argv[1]]; runpy.run_path(sys.argv[0], run_name='__main__')\n")


def build(g, recs, overrides, park_doc):
    """Run the real builder for FR on a saved copy holding exactly `recs` (GEO_CACHE_MODE=only: no source is read)."""
    t = pathlib.Path(tempfile.mkdtemp(prefix='kpc-job6-'))
    try:
        (t / 'data/world-key').mkdir(parents=True); (t / 'data/parkinfo').mkdir(parents=True)
        json.dump(park_doc, open(t / 'data/parkinfo/FR.json', 'w', encoding='utf-8'), ensure_ascii=False)
        json.dump(overrides, open(t / 'data/world-key/overrides.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        for rel in ('data/retired-refs.json', 'data/world-key/extra-layers.json', 'data/world-key/sheet-countries.json', 'data/world-key/eea-designations.json'):
            if (ROOT / rel).is_file(): shutil.copy(ROOT / rel, t / rel)
        g['WCACHE'] = t / 'cache'; g['wsave']('FR', [dict(r) for r in recs])
        dead = 'http://127.0.0.1:9'
        env = dict(os.environ, COUNTRIES='FR', GEO_CACHE_MODE='only', GEO_CACHE=str(t / 'cache'), KPC_TRACT_STORE='0', PYTHONDONTWRITEBYTECODE='1',
                   HTTP_PROXY=dead, HTTPS_PROXY=dead, http_proxy=dead, https_proxy=dead, ALL_PROXY=dead, NO_PROXY='', no_proxy='')
        r = subprocess.run([sys.executable, '-B', '-c', RUNNER, str(SCRIPT)], cwd=t, env=env, capture_output=True, text=True, timeout=900)
        if r.returncode != 0: raise RuntimeError(f'builder exit {r.returncode}: {(r.stdout + r.stderr)[-1500:]}')
        key = json.load(open(t / 'data/world-key/FR.json', encoding='utf-8'))
        shards = {}
        for f in (t / 'data/world-bounds/FR').glob('*.json'): shards.update(json.load(open(f, encoding='utf-8')))
        return key, shards, r.stdout
    finally:
        shutil.rmtree(t, ignore_errors=True)


def web_official(p):
    """The website's grade of a world park (kpc-bounds.js worldKey): True = Official outline, False = Approximate, None = no join."""
    m = p.get('m') or []
    if not m: return None
    return any(JS_OFFICIAL.search(str(x[3] if len(x) > 3 else '')) for x in m)
