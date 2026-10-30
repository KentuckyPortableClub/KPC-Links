"""CANADA boundary ANSWER KEY (Brandon Oct 18 2026: 'set one up to start pulling the Canada data'). Same method as kpc_us_key.py:
pull every area in CPCAD (Canadian Protected and Conserved Areas Database, Environment and Climate Change Canada, Open Government
Licence - Canada) with a coarse outline, then join to the CA- POTA parks (data/parkinfo/CA.json) ONLY when the name matches (English
or French, generic words and accents dropped) AND it is the same kind of place, near the park's pin. EVERY piece with that name joins.
Unsure = 'c' check list with the reason, never joined. Provincial layers (Québec, Ontario…) come in a later step.
Writes data/ca-key/CA-XX.json per province/territory, data/ca-key/index.json, review pages data/ca-key/review/CA-XX.md."""
import json, os, re, sys, time, unicodedata, urllib.parse, urllib.request, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from kpc_save import save_json, save_text  # noqa: E402  (Oct 25 storage plan: write only when the content changed)

SVC = 'https://maps-cartes.ec.gc.ca/arcgis/rest/services/CWS_SCF/CPCAD/MapServer'
OUT = pathlib.Path('data/ca-key'); OUT.mkdir(parents=True, exist_ok=True)
UA = 'KPC (kentuckyportableclub.github.io)'
import gzip
# SHAPE DETAIL + SAVED COPY (Oct 22, Fable's review; same scheme as kpc_us_key.py). Every live run has fetched CPCAD and
# the provincial layers at 0.02 degrees (~2.2 km) - coarser than many parks. GEO_CACHE_MODE: off (default, exactly as
# before) | use | refresh | only (no network). All of Canada is read at once, so it is saved as ONE file.
DETAIL = float(os.environ.get('GEO_DETAIL') or 0.02)
PREC = 3 if DETAIL >= 0.01 else 5
CCACHE = pathlib.Path(os.environ.get('GEO_CACHE') or 'cache/ca')
CMODE = (os.environ.get('GEO_CACHE_MODE') or 'off').strip().lower()
USED_DETAIL = DETAIL


def ccache_file(): return CCACHE / 'CA-ALL.json.gz'


def csave(recs):
    CCACHE.mkdir(parents=True, exist_ok=True)
    rows = []
    for r in recs:
        o = {k: v for k, v in r.items() if k not in ('_g', '_k')}
        o['_r'] = [[[round(pt[0], 5), round(pt[1], 5)] for pt in ring if len(pt) >= 2] for ring in ((r.get('_g') or {}).get('rings') or [])]
        o['_k'] = sorted(r.get('_k') or [])
        rows.append(o)
    with gzip.open(ccache_file(), 'wt', encoding='utf-8') as f:
        json.dump({'saved': time.strftime('%Y-%m-%d'), 'detail': DETAIL, 'recs': rows}, f, separators=(',', ':'),
                  default=lambda o: sorted(o) if isinstance(o, (set, frozenset)) else str(o))


def cload():
    f = ccache_file()
    if not f.exists(): return None
    try:
        with gzip.open(f, 'rt', encoding='utf-8') as fh: blob = json.load(fh)
    except Exception as e:  # noqa: BLE001
        print(f'saved outlines unreadable ({e}); fetching', flush=True); return None
    out = []
    for o in blob.get('recs') or []:
        r = {k: v for k, v in o.items() if k not in ('_r', '_k')}
        r['_g'] = {'rings': o.get('_r') or []}
        r['_bb'] = bbox(r['_g'])
        r['_k'] = set(o.get('_k') or [])
        out.append(r)
    notice('Canada saved outlines', f"loaded {len(out)} areas saved {blob.get('saved')} at detail {blob.get('detail')}")
    global USED_DETAIL; USED_DETAIL = blob.get('detail') or DETAIL
    return out


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', '%0A')), flush=True)


def get(url, params, tries=5):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url + '?' + urllib.parse.urlencode(params), headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=180) as r: j = json.loads(r.read().decode('utf-8', 'replace'))
            if isinstance(j, dict) and j.get('error'): raise RuntimeError(str(j['error'])[:200])
            return j
        except Exception as e:  # noqa: BLE001
            last = e; time.sleep(8 * (i + 1))
    raise last


def flat(s): return ''.join(c for c in unicodedata.normalize('NFKD', str(s or '')) if not unicodedata.combining(c)).lower()


GEN = (r"habitat protection area|habitat protection|special management area|game preserve|area of outstanding natural beauty|conservation park|and district|district|natural area under private stewardship|under private stewardship|parc nature|campground|national historic site of canada|national historic site|lieu historique national du canada|lieu historique national|historic site|lieu historique|"
       r"national marine park of canada|national marine park|national wildlife area|reserve nationale de faune|migratory bird sanctuary|refuge d oiseaux migrateurs|bird sanctuary|wildlife management area|"
       r"wildlife refuge|wildlife area|reserve faunique|refuge faunique|national park reserve|national park of canada|parc national du canada|national park|parc national|"
       r"national marine conservation area|marine park|provincial park|parc provincial|territorial park|parc territorial|regional park|parc regional|"
       r"provincial recreation area|recreation area|recreation site|recreation park|conservation reserve|conservation area|aire de conservation|"
       r"ecological reserve|reserve ecologique|nature reserve|nature preserve|conservancy|reserve naturelle|natural area|protected natural area|protected area|aire protegee|"
       r"wilderness area|wilderness park|heritage rivers?|heritage area|heritage site|biosphere reserve|reserve de la biosphere|provincial forest|"
       r"provincial|national|park|parc|reserve|area|site|de la|des|du|de|la|le|les|the|of|and|et")
ABBR = {'st': 'saint', 'ste': 'sainte', 'mt': 'mount', 'pt': 'point', 'lk': 'lake', 'cr': 'creek', 'is': 'island', 'isl': 'island'}


@__import__('functools').lru_cache(maxsize=None)
def norm(s):
    s = flat(s).replace('&', ' and ')
    s = re.sub(r'\(.*?\)|\[.*?\]', ' ', s)
    s = re.sub(r'\b0+(\d)', r'\1', s)
    s = re.sub(r"\b([dlj]|qu)[’'`]", r'\1 ', s)   # French d'/l' must not glue onto the next word (d'Anticosti → d anticosti)
    s = re.sub(r"[’'`.]", '', s)
    s = re.sub(r'[-/]', ' ', s)
    s = ' '.join(ABBR.get(w, w) for w in re.sub(r'[^a-z0-9 ]', ' ', s).split())
    s = re.sub(r'\b(' + GEN + r')\b', ' ', s)
    s = re.sub(r'\b(d|l|j|qu|en|au|aux|a)\b', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


KINDS = [('pp', r'provincial park|parc provincial|territorial park|parc territorial|parc national(?! du canada)'),
         ('np', r'national park|national marine park|parc national du canada|national park reserve|parc national(?! [a-z])'),
         ('hist', r'historic|historique|heritage site'),
         ('wma', r'wildlife|faune|faunique|bird sanctuary|oiseaux migrateurs|game'),
         ('ca', r'conservation (area|reserve)|aire de conservation|conservancy'),
         ('eco', r'ecological reserve|reserve ecologique|nature reserve|reserve naturelle|natural area|protected natural area|nature preserve'),
         ('rec', r'recreation|loisirs'), ('rp', r'regional park|parc regional'), ('mp', r'marine (provincial )?park|marine conservation'),
         ('wild', r'wilderness'), ('pf', r'provincial forest|foret')]
def kinds(s):
    s = flat(s); return {k for k, r in KINDS if re.search(r, s)}


def _sing(s): return ' '.join(w[:-1] if len(w) > 3 and w.endswith('s') else w for w in s.split())


@__import__('functools').lru_cache(maxsize=None)   # Oct 28: the same names are compared millions of times (speed only)
def variants(s):
    # Oct 18 review: plurals ('Munroes' = 'Munroe'), 'and' between two names, a leading Ile/Isle ('Ile d'Anticosti' = 'Anticosti')
    v = {norm(s)} | {norm(x) for x in re.split(r'\s*/\s*', str(s or '')) if len(x.strip()) > 3}   # 'Indigenous name / English name'
    v |= {_sing(x) for x in v} | {re.sub(r'\b(and|et)\b', ' ', x) for x in v}
    v |= {re.sub(r'^(iles?|isles?|islands?) ', '', x) for x in v}
    return frozenset(re.sub(r'\s+', ' ', x).strip() for x in v if x.strip())


def _pre(a, b):
    if a == b: return True
    sh, lo = (a, b) if len(a) < len(b) else (b, a)
    return len(sh) > 5 and lo.startswith(sh) and lo[len(sh):len(sh) + 1] == ' ' and len(sh) / len(lo) >= 0.6


# Oct 24: Upper / Lower / North / South / East / West tell two halves of one place apart (the US key's Oct 22 rule), in
# English and French. 'sur' is left out: in a French name it is 'on' (Saint-Jean-sur-Richelieu), not a side.
SIDEW = {'n': 'north northern nord', 's': 'south southern sud', 'e': 'east eastern est', 'w': 'west western ouest',
         'u': 'upper haut haute', 'l': 'lower bas basse', 'm': 'middle'}
SIDE = {w: k for k, ws in SIDEW.items() for w in ws.split()}


@__import__('functools').lru_cache(maxsize=None)
def _side(s): return {SIDE[w] for w in re.split(r'[\s/\-–,]+', re.sub(r'\(.*?\)', ' ', flat(s))) if w in SIDE}   # 'Dzawadi/Upper' splits; bracket text ('secteur Haut Richelieu') is not a side


def same_name(a, b, exact=False):
    if _side(a) != _side(b): return False      # Upper White Oak Lake is not White Oak Lake
    va, vb = variants(a), variants(b)
    if not va or not vb: return False
    if va & vb: return True
    return not exact and any(_pre(x, y) for x in va for y in vb)


COMPAT = [{'rec', 'pp'}, {'mp', 'pp'}, {'rp', 'rec'}]   # Manitoba recreation parks became provincial parks; BC marine parks are provincial parks
def same_kind(ka, kb): return not ka or not kb or bool(ka & kb) or any(ka & c and kb & c and (ka | kb) & c == c for c in COMPAT)
def words(s): return set(w for w in norm(s).split() if len(w) > 2)
def rings(g): return (g or {}).get('rings') or []
def bbox(g):
    xs = [p[0] for r in rings(g) for p in r]; ys = [p[1] for r in rings(g) for p in r]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None
def in_ring(x, y, r):
    ins = False; j = len(r) - 1
    for i in range(len(r)):
        xi, yi, xj, yj = r[i][0], r[i][1], r[j][0], r[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi: ins = not ins
        j = i
    return ins
def inside(la, lo, g): return sum(1 for r in rings(g) if in_ring(lo, la, r)) % 2 == 1
LOCALSRC = re.compile(r'local and regional|greenspace|municipal parks', re.I)
def near(la, lo, b, pad): return b and b[0] - pad <= lo <= b[2] + pad and b[1] - pad <= la <= b[3] + pad


recs = cload() if CMODE in ('use', 'only') else None
if recs is None and CMODE == 'only':
    notice('Canada key', 'no saved outlines yet; nothing done (saved-copy-only run)'); raise SystemExit(0)
if recs is None:
    # ---------------- pull CPCAD ----------------
    root = get(SVC, {'f': 'json'})
    lid, info = None, None
    for l in root.get('layers') or []:
        i = get(f"{SVC}/{l['id']}", {'f': 'json'})
        if 'Polygon' in str(i.get('geometryType', '')): lid, info = l['id'], i; break
    if lid is None: raise SystemExit('No CPCAD polygon layer')
    names = [f['name'] for f in info.get('fields', [])]
    pick = lambda *ns: next((f for n in ns for f in names if f.lower() == n.lower()), None)
    F = {'oid': info.get('objectIdField') or pick('OBJECTID', 'FID'), 'name': pick('NAME_E', 'NAME_EN', 'NAME'), 'namef': pick('NAME_F', 'NAME_FR'),
         'type': pick('TYPE_E', 'TYPE_EN', 'TYPE'), 'owner': pick('OWNER_E', 'OWNER_EN', 'OWNER'), 'mgr': pick('MGMT_E', 'MGMT_EN', 'MGMT'),
         'area': pick('O_AREA_HA', 'O_AREA', 'AREA_HA', 'SHAPE_Area')}
    notice('CPCAD layer', f'layer {lid}, fields {F}')
    mx = int(info.get('maxRecordCount') or 1000)
    mx = min(mx, 1000 if DETAIL >= 0.02 else 250)     # finer outlines = heavier pages: ask for fewer at a time
    recs, off = [], 0
    while True:
        j = get(f'{SVC}/{lid}/query', {'where': '1=1', 'outFields': ','.join(v for v in F.values() if v), 'returnGeometry': 'true', 'outSR': 4326,
                                       'maxAllowableOffset': DETAIL, 'geometryPrecision': PREC, 'f': 'json', 'resultOffset': off, 'resultRecordCount': min(mx, 1000),
                                       'orderByFields': F['oid']})
        fs = j.get('features', [])
        for f in fs:
            a = f.get('attributes') or {}; g = f.get('geometry') or {}
            r = {'oid': a.get(F['oid']), 'n': a.get(F['name']) or '', 'nf': a.get(F['namef']) or '', 'ty': a.get(F['type']) or '', 'ow': a.get(F['owner']) or '',
                 'mg': a.get(F['mgr']) or '', 'ha': a.get(F['area']) or 0, '_g': g, '_bb': bbox(g)}
            r['_k'] = kinds(r['n']) | kinds(r['nf']) | kinds(r['ty'])
            recs.append(r)
        if not fs or (not j.get('exceededTransferLimit') and len(fs) < min(mx, 1000)): break
        off += len(fs); time.sleep(.5)
    notice('CPCAD read', f'{len(recs)} areas')
    if len(recs) < 3000: raise SystemExit('Too few CPCAD areas read; keeping the old files.')


    # ---------------- provincial + Parks Canada layers (the same official list kpc_canada_bounds.py uses), pulled whole ----------------
    _src = open('.github/scripts/kpc_canada_bounds.py', encoding='utf-8').read()
    _ns = {'re': re}; exec(_src[_src.index('CA = ('):_src.index('BCWFS =')], _ns)
    NAMEY = re.compile(r'(name|nom|toponym|title)', re.I)
    HINT = [('regional parks', {'rp'}), ('recreation sites', {'rec'}), ('nature reserves', {'eco'}), ('Ontario Parks', {'pp'}), ('conservation reserves', {'ca'}), ('ecological reserves', {'eco'}), ('wildlife', {'wma'})]


    _ERR = []
    LAYERS = {'cpcad': [f'{SVC}/{lid}']}   # Oct 24: the website fetches a joined area by id from its own map (data/ca-key/layers.json)
    # Oct 29 (chat 8 'NS wrong joins solved'): an id was '<first 12 letters of the label>:<record number>', and two layers can share
    # those 12 letters (two Nova Scotia sources, one source with 4 sub-layers): record 731 of one layer = record 731 of another.
    # Each LAYER now gets its own prefix: the first keeps the old 12 letters (old ids and hand joins still point at it), the next
    # ones get '~1', '~2' …
    _PID, _BASE, ERRLAB = {}, {}, set()
    def pid_for(label, lu):
        k = (label, lu)
        if k not in _PID:
            b = label[:12]; n = _BASE.get(b, 0); _BASE[b] = n + 1
            _PID[k] = b if n == 0 else f'{b}~{n}'
        return _PID[k]
    def arc_pull(label, url, nf):
        lays = []
        if re.search(r'/(MapServer|FeatureServer)/\d+$', url): lays = [url]
        else:
            info = get(url, {'f': 'json'})
            for l in info.get('layers') or []:
                lays.append(f"{url}/{l['id']}")
        got = []
        for lu in lays:
            try: li = get(lu, {'f': 'json'})
            except Exception as e: print(f'{label} {lu}: {e}', flush=True); _ERR.append(f'{label[:30]} layer: {str(e)[:80]}'); continue  # noqa: BLE001
            if 'Polygon' not in str(li.get('geometryType', '')): continue
            pid = pid_for(label, lu)
            LAYERS.setdefault(pid, []).append(lu)
            fl = [f['name'] for f in li.get('fields', [])]
            names = [n for n in (nf or []) if n in fl] or [f for f in fl if NAMEY.search(f) and not re.search(r'(file|url|link|code|id$)', f, re.I)][:3]
            oidf = li.get('objectIdField') or 'OBJECTID'; mx = int(li.get('maxRecordCount') or 1000); off = 0
            # Oct 25 (round 5 hand checks): Québec's MRNF MapServer answers objectIds queries with the field ALIASES as keys,
            # so a.get('OBJECTID') was None and every ZEC / réserve / parc got the id 'None' (one shared, wrong shape)
            oida = {oidf.lower(), 'objectid', 'fid'} | {str(f.get('alias') or '').lower() for f in li.get('fields', []) if f.get('name') == oidf}
            oidv = lambda a: a.get(oidf) if a.get(oidf) is not None else next((v for k, v in a.items() if k.lower() in oida and v is not None), None)
            ids = None   # Oct 20: Québec's MRNF MapServer answers 400 to paged queries (no pagination): fall back to asking by object ids
            while True:
                try:
                    if ids is None:
                        j = get(f'{lu}/query', {'where': '1=1', 'outFields': ','.join([oidf] + names), 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': DETAIL,
                                                'geometryPrecision': 3, 'f': 'json', 'resultOffset': off, 'resultRecordCount': min(mx, 1000), 'orderByFields': oidf}, tries=3)
                    else:
                        if off >= len(ids): break
                        j = get(f'{lu}/query', {'objectIds': ','.join(str(x) for x in ids[off:off + 100]), 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': DETAIL, 'geometryPrecision': PREC, 'f': 'json'}, tries=3)
                except Exception as e:
                    if ids is None and off == 0:
                        try: ids = sorted(get(f'{lu}/query', {'where': '1=1', 'returnIdsOnly': 'true', 'f': 'json'}, tries=3).get('objectIds') or []); print(f'{label}: paging by {len(ids)} ids', flush=True); continue
                        except Exception as e2: e = e2  # noqa: BLE001
                    print(f'{label}: {e}', flush=True); _ERR.append(f'{label[:30]} query: {str(e)[:80]}'); ERRLAB.add(label); break  # noqa: BLE001
                fs = j.get('features', [])
                if ids is not None and fs and not any((f.get('attributes') or {}).get(n) for f in fs[:5] for n in names):
                    at = fs[0].get('attributes') or {}; names = [k for k in at if NAMEY.search(k) and not re.search(r'(file|url|link|code|id$)', k, re.I)][:3] or names
                for f in fs:
                    a = f.get('attributes') or {}; g = f.get('geometry') or {}
                    nm = next((str(a[n]) for n in names if a.get(n)), '')
                    if not nm: continue
                    r = {'oid': f'{pid}:' + (str(oidv(a)) if oidv(a) is not None else 'n-' + nm[:60]), 'n': nm, 'nf': '', 'ty': label, 'ow': '', 'mg': '', 'ha': 0, '_g': g, '_bb': bbox(g), 'src': label}
                    r['_k'] = kinds(nm) | next((k for h, k in HINT if h.lower() in label.lower()), set())
                    got.append(r)
                if ids is not None: off += 100; time.sleep(.4); continue
                if not fs or (not j.get('exceededTransferLimit') and len(fs) < min(mx, 1000)): break
                off += len(fs); time.sleep(.4)
        return got


    extra = 0
    for e in _ns['EXTRA']:
        if e[1] != 'arcgis': continue
        try: g = arc_pull(e[0], e[2], e[3]); recs += g; extra += len(g); print(f'{e[0]}: {len(g)}', flush=True)
        except Exception as ex: notice('Canada extra', f'{e[0]} FAILED: {ex}')  # noqa: BLE001
    # Oct 18 review: more official layers found by a probe from GitHub (POTA Québec 'Nature Reserve' parks are the province's
    # recognized nature reserves, which CPCAD files as private stewardship; the government register has them by name)
    MORE = [('Québec recognized nature reserves (MELCCFP)', 'https://geo.environnement.gouv.qc.ca/donnees/rest/services/Biodiversite/Aires_protegees/MapServer/12', ['TOPONYME', 'DESIGNOM']),
            ('Saskatchewan regional parks (Government of Saskatchewan)', 'https://gis.saskatchewan.ca/arcgis/rest/services/ParksAsTitled/MapServer/6', None),
            ('Yukon parks and protected areas (Government of Yukon)', 'https://mapservices.gov.yk.ca/arcgis/rest/services/GeoYukon/GY_ParksProtectedAreas/MapServer/3', None),
            ('Yukon campgrounds and parks (Government of Yukon)', 'https://mapservices.gov.yk.ca/arcgis/rest/services/GeoYukon/GY_ParksProtectedAreas/MapServer/0', None),
            ('Ontario federal protected areas (Land Information Ontario)', 'https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open03/MapServer/10', None),
            ('Ontario municipal parks (Land Information Ontario)', 'https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open03/MapServer/3', None),
            ('BC recreation sites (BC Ministry of Forests)', 'https://maps.gov.bc.ca/arcgis/rest/services/whse/bcgw_pub_whse_forest_tenure/MapServer/5', None)]
    # Oct 20 (probe 3): Nova Scotia Parks and Protected Areas System, layer 1 = parks + protected areas (layer 0 = only proposed)
    MORE.append(('Nova Scotia parks and protected areas', 'https://services1.arcgis.com/qpxtVXh93G601MmT/arcgis/rest/services/Nova_Scotia_Parks_and_Protected_Areas_System_V1/FeatureServer/1', None))
    MORE.append(('Manitoba wildlife lands (Government of Manitoba; contains information licensed under the OpenMB Information and Data Use Licence)', 'https://services.arcgis.com/mMUesHYPkXjaFGfS/arcgis/rest/services/Manitoba_Wildlife_Lands/FeatureServer/0', None))
    # Oct 20 (probe 6): Québec MRNF recreation territories (TRQ): ZEC (POTA files many as 'Nature Reserve') + réserves fauniques; outfitters (pourvoiries) are leases, left out
    try:
        # Oct 20: the old mern host closed the connection; the ministry moved it to servicescarto.mrnf.gouv.qc.ca (Données Québec record)
        _ql0 = None
        for _q in ['https://servicescarto.mrnf.gouv.qc.ca/pes/rest/services/Territoire/TRQ_WMS/MapServer',
                   'https://serviceswebcarto.mern.gouv.qc.ca/pes/rest/services/Territoire/TRQ_WMS/MapServer']:
            try: _ql0 = get(_q, {'f': 'json'}).get('layers') or []; break
            except Exception as _e: notice('Canada more layers', f'Québec TRQ host {_q.split("/")[2]} failed: {_e}')  # noqa: BLE001
        if _ql0 is None: raise RuntimeError('no Québec TRQ host answered')
        _ql = [l for l in _ql0 if re.search(r'zec|zone d|faunique|parc', l.get('name', ''), re.I) and not re.search(r'pourvoir', l.get('name', ''), re.I) and not l.get('subLayerIds')]
        notice('Canada more layers', 'Québec TRQ layers: ' + ', '.join(f"{l['id']}:{l['name']}" for l in _ql))
        MORE += [(f"Québec {l['name']} (MRNF)", f"{_q}/{l['id']}", None) for l in _ql]
    except Exception as ex: notice('Canada more layers', f'Québec TRQ list FAILED: {ex}')  # noqa: BLE001
    # Oct 25: the provinces' entries in data/state-gis.json (the outside research bot's tested layers: Ontario conservation
    # authorities, NovaRoc, GeoNB, GeoLinc, Nunavut, Saskatchewan, Québec culture ministry). Each gets a unique short code
    # as its label start, so ids from two layers can never collide ('ON-NPCA Niag:5').
    PROVS = {'AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT'}
    GJ, SZ = [], []
    try:
        _sg = json.load(open('data/state-gis.json')).get('states') or {}
        _have = {e[1].rstrip('/') for e in MORE}
        for _pv, _ls in sorted(_sg.items()):
            if _pv not in PROVS: continue
            for _l in _ls:
                _u = str(_l.get('url') or '').rstrip('/')
                if not _u or _u in _have or not _l.get('nm') or _l.get('water'): continue
                _lab = f"{_l.get('code') or _pv} {_l.get('ag') or ''}"
                if _l.get('fmt') == 'geojson': GJ.append((_lab, _u, _l['nm']))
                elif _l.get('fmt') == 'shpzip': SZ.append((_lab, _u, _l['nm'], _l.get('epsg') or 4326))
                else: MORE.append((_lab, _u, [_l['nm']]))
    except Exception as ex: notice('Canada state-gis layers', f'not read: {ex}')  # noqa: BLE001

    def gj_pull(label, url, nf):
        # a plain GeoJSON download (Québec's culture ministry publishes its heritage-site outlines this way)
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=240) as r: j = json.loads(r.read().decode('utf-8', 'replace'))
        got = []
        for i, f in enumerate(j.get('features') or []):
            P = f.get('properties') or {}; nm = str(P.get(nf) or '').strip(); geo = f.get('geometry') or {}
            if not nm: continue
            t, c = geo.get('type'), geo.get('coordinates') or []
            rs = c if t == 'Polygon' else [q for pp in c for q in pp] if t == 'MultiPolygon' else []
            k = max(1, max((len(q) for q in rs), default=1) // 400)
            g = {'rings': [[[round(pt[0], 5), round(pt[1], 5)] for pt in q[::k]] for q in rs]}
            rr = {'oid': f'{pid_for(label, url)}:{P.get("OBJECTID") or P.get("objectid") or i}', 'n': nm, 'nf': '', 'ty': label, 'ow': '', 'mg': '', 'ha': 0, '_g': g, '_bb': bbox(g), 'src': label}
            rr['_k'] = kinds(nm); got.append(rr)
        return got
    def sz_pull(label, url, nf, epsg):
        # a zipped shapefile in the agency's own projection (Grand River CA: UTM zone 17, no live map service)
        import io, zipfile, shapefile
        from pyproj import Transformer
        tr = Transformer.from_crs(int(epsg), 4326, always_xy=True)
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=240) as r: z = zipfile.ZipFile(io.BytesIO(r.read()))
        got = []
        for sp in [q for q in z.namelist() if q.lower().endswith('.shp')]:
            b = sp[:-4]
            rd = shapefile.Reader(shp=io.BytesIO(z.read(sp)), dbf=io.BytesIO(z.read(b + '.dbf')), shx=io.BytesIO(z.read(b + '.shx')))
            fn = [f[0] for f in rd.fields[1:]]
            for i, (shp, rec) in enumerate(zip(rd.shapes(), rd.records())):
                a = dict(zip(fn, list(rec))); nm = str(a.get(nf) or '').strip()
                if not nm: continue
                pts, parts = shp.points, list(shp.parts) + [len(shp.points)]
                rs = []
                for k in range(len(parts) - 1):
                    ring = pts[parts[k]:parts[k + 1]]; st = max(1, len(ring) // 400)
                    xs, ys = tr.transform([q[0] for q in ring[::st]], [q[1] for q in ring[::st]])
                    rs.append([[round(x, 5), round(y, 5)] for x, y in zip(xs, ys)])
                g = {'rings': rs}
                rr = {'oid': f'{pid_for(label, url)}:{i}', 'n': nm, 'nf': '', 'ty': label, 'ow': '', 'mg': '', 'ha': 0, '_g': g, '_bb': bbox(g), 'src': label}
                rr['_k'] = kinds(nm); got.append(rr)
        return got
    _mores = []   # Oct 20: GitHub shows only 10 notices per step, so all layer counts go in ONE notice
    for e in SZ:
        try: g = sz_pull(*e); recs += g; extra += len(g); _mores.append(f'{e[0]}: {len(g)}')
        except Exception as ex: _mores.append(f'{e[0]} FAILED: {ex}')  # noqa: BLE001
    for e in GJ:
        try: g = gj_pull(*e); recs += g; extra += len(g); _mores.append(f'{e[0]}: {len(g)}')
        except Exception as ex: _mores.append(f'{e[0]} FAILED: {ex}')  # noqa: BLE001
    for e in MORE:
        try: g = arc_pull(e[0], e[1], e[2]); recs += g; extra += len(g); _mores.append(f'{e[0]}: {len(g)}')
        except Exception as ex: _mores.append(f'{e[0]} FAILED: {ex}')  # noqa: BLE001
    notice('Canada more layers (all)', ' | '.join(_mores))
    notice('Canada extra layers', f'{extra} areas from the provincial + Parks Canada maps' + (' · errors: ' + ' | '.join(_ERR[:12]) if _ERR else ''))
    try: save_json(OUT / 'layers.json', LAYERS, indent=1)
    except Exception as ex: notice('Canada key layers', ex)  # noqa: BLE001
    # Oct 22: a provincial map that did not answer must not cost Canada its parks: use the last saved copy instead,
    # and never save a half-read copy over a good one
    old = cload() if (_ERR or any('FAILED' in x for x in _mores)) else None
    if old is not None and len(recs) < .97 * len(old):   # only when the read came back SHORT (Québec fails most runs)
        notice('Canada key', f'a map did not answer ({len(recs)} areas read, {len(old)} saved), so the saved copy was used (nothing dropped)'); recs = old
    else:
        # Oct 29 (15 Québec regional parks lost their outline when 'Parc régional (MRNF)' answered 400): a layer whose query
        # failed this run and brought back NOTHING keeps its records from the saved copy (ids moved to the layer's own prefix)
        topped = 0
        have = {r.get('src') for r in recs}
        _sv = (old if old is not None else cload()) if ERRLAB - have else []
        for lab in sorted(ERRLAB):
            if lab in have: continue
            pids = [v for (l2, _u), v in _PID.items() if l2 == lab]
            if len(pids) != 1: continue
            saved = [dict(r) for r in (_sv or []) if r.get('src') == lab]
            for r in saved:
                r['oid'] = pids[0] + ':' + str(r.get('oid', '')).split(':', 1)[-1]; recs.append(r); topped += 1
        if topped: notice('Canada key', f'{topped} areas of layers that did not answer this run were taken from the saved copy ({", ".join(sorted(ERRLAB))[:200]})')
        if CMODE in ('use', 'refresh') and not topped: csave(recs)
# Oct 26 (gap hunt, HQ): POTA's 'New Brunswick #24 Wildlife Management Area' parks are New Brunswick's numbered WILDLIFE
# MANAGEMENT ZONES (OpenData/WMZ, one number field, 27 zones). A probe found 23 of the 25 pins inside the zone of their own
# number. No zone carries a name, so each gets the POTA-style name from its number and joins by name like any other area.
# Topped up into a saved copy that does not have them yet.
NBWMZ = 'https://gis-erd-der.gnb.ca/server/rest/services/OpenData/WMZ/MapServer/0'
if CMODE != 'only' and not any(str(r.get('oid', '')).startswith('NB WMZ:') for r in recs):
    try:
        j = get(f'{NBWMZ}/query', {'where': '1=1', 'outFields': 'OBJECTID_1,WMZ', 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': DETAIL,
                                   'geometryPrecision': 3, 'f': 'json'})
        _z = 0
        for f in j.get('features') or []:
            a = f.get('attributes') or {}; g = f.get('geometry') or {}
            if a.get('WMZ') is None: continue
            nm = f"New Brunswick #{int(a['WMZ'])} Wildlife Management Area"
            recs.append({'oid': f"NB WMZ:{a.get('OBJECTID_1')}", 'n': nm, 'nf': '', 'ty': 'Wildlife Management Zone (New Brunswick)', 'ow': 'Government of New Brunswick',
                         'mg': 'New Brunswick Department of Natural Resources and Energy Development', 'ha': 0, '_g': g, '_bb': bbox(g), 'src': 'NB WMZ', '_k': {'wma'}})
            _z += 1
        notice('Canada NB zones', f'{_z} New Brunswick wildlife management zones added')
        if _z and CMODE in ('use', 'refresh'): csave(recs)
        try:
            _L = json.load(open(OUT / 'layers.json')); _L['NB WMZ'] = [NBWMZ]; save_json(OUT / 'layers.json', _L, indent=1)
        except Exception as ex: notice('Canada key layers', ex)  # noqa: BLE001
    except Exception as ex: notice('Canada NB zones', f'not read: {ex}')  # noqa: BLE001
PRIV = re.compile(r'private|privately|stewardship|ncc \d|nature conservancy', re.I)


def _shape_acres(g):
    """Oct 30 (HQ morning queue 1, chat 11: every Canada piece showed 0 acres): area from the outline itself when the layer gives none.
    Rings in lon/lat degrees: shoelace on an equal-area local projection (x scaled by cos(latitude)); holes subtract by winding."""
    import math
    tot = 0.0
    for r in rings(g):
        if len(r) < 3: continue
        lat0 = math.radians(sum(p[1] for p in r) / len(r)); kx = 111320.0 * math.cos(lat0); ky = 110540.0
        a = 0.0
        for i in range(len(r)):
            x1, y1 = r[i - 1][0] * kx, r[i - 1][1] * ky; x2, y2 = r[i][0] * kx, r[i][1] * ky
            a += x1 * y2 - x2 * y1
        tot += a / 2.0
    return abs(tot) / 4046.8564224
def acres(r):
    if r.get('ha'): return round(r['ha'] * 2.47105)
    try: return round(_shape_acres(r.get('_g')))
    except Exception: return 0  # noqa: BLE001


# Oct 18 review: sites (lighthouse, bridge, trail, campground…) have no outline of their own; reviewed parks in data/ca-key/overrides.json
SITE = re.compile(r'lighthouse|phare|bridge|pont|trail|sentier|campground|camping|day use|boat launch|wharf|quai|canal|hotel|station|building|house|maison|church|eglise|fort |monument|recreation site', re.I)
def _nf(t):   # hand decisions match names whatever way the accents are stored (Oct 18: SG̲áan K̲ínghlas-Bowie never matched)
    import unicodedata; return unicodedata.normalize('NFC', str(t or '')).strip().casefold()
try: OVR = json.load(open(OUT / 'overrides.json')).get('parks', {})
except Exception: OVR = {}  # noqa: BLE001
P = json.load(open('data/parkinfo/CA.json'))['parks']
# Oct 29 (chat 5 check-up, issue #17): park numbers POTA retired (data/retired-refs.json) leave the answer key
try: P = {k: v for k, v in P.items() if k not in set(json.load(open('data/retired-refs.json')).get('refs') or {})}
except Exception: pass  # noqa: BLE001
RID = {str(r['oid']): r for r in recs}
# Oct 28 (tune + speed-up pass): the join below compared every park with every saved area (5,900 parks x 48,000 areas, ~13 min
# of the run). A 1-degree grid of the areas' boxes (+0.6 degree, the widest search used) hands each park only the areas
# near its pin, in the same order, so every result is the same as before. Parks with no pin still look at all of them.
import math as _m
GRID, BIG = {}, []
for _i, _r in enumerate(recs):
    _b = _r.get('_bb')
    if not _b: continue
    _x0, _x1, _y0, _y1 = _m.floor(_b[0] - .6), _m.floor(_b[2] + .6), _m.floor(_b[1] - .6), _m.floor(_b[3] + .6)
    if (_x1 - _x0 + 1) * (_y1 - _y0 + 1) > 400: BIG.append(_i); continue
    for _gx in range(_x0, _x1 + 1):
        for _gy in range(_y0, _y1 + 1): GRID.setdefault((_gx, _gy), []).append(_i)


def around(la, lo):
    """The areas whose box (+0.6 degree) can hold this pin, in their original order; all of them when there is no pin."""
    if la is None: return recs
    return [recs[i] for i in sorted(GRID.get((_m.floor(lo), _m.floor(la)), []) + BIG)]


# SELF-GRADE GATE (Oct 28, HQ): five well-known parks must keep a joined outline with the pin inside or at the edge.
# A FAIL means the read or the matcher broke: the old province files are kept (nothing saved) and the run says so.
GATE_REFS = {'CA-0005': 'Banff', 'CA-0040': 'Jasper', 'CA-0138': 'Algonquin', 'CA-0030': 'Gros Morne', 'CA-0010': 'Bruce Peninsula'}
PENDING = []
by = {}
for ref, x in P.items(): by.setdefault((x[10] if len(x) > 10 else '') or 'XX', {})[ref] = x
idx = {}
for pv, parks_in in sorted(by.items()):
    parks, used = {}, set()
    _pins = [(x[5], x[6]) for x in parks_in.values() if x[5] or x[6]]
    PVB = [min(q[1] for q in _pins) - 1, min(q[0] for q in _pins) - 1, max(q[1] for q in _pins) + 1, max(q[0] for q in _pins) + 1] if _pins else None
    def in_pv(b): return not PVB or (b and b[0] <= PVB[2] and b[2] >= PVB[0] and b[1] <= PVB[3] and b[3] >= PVB[1])
    for ref, x in sorted(parks_in.items()):
        name, typ, la, lo = x[0], x[2], x[5], x[6]
        if not la and not lo: la = lo = None   # Oct 18: POTA has no pin for ~200 Canadian parks (0,0): match by name in the province only
        elif abs(la) > 90:                      # Oct 25: POTA has a few pins with latitude and longitude swapped (Churchill WMA 92.6, -57.1): Canada is north + west
            la, lo = abs(lo), -abs(la)
        kp = kinds(name) | kinds(typ)
        m, c = [], []
        NEAR = around(la, lo)
        for r in NEAR:
            if la is not None and not near(la, lo, r['_bb'], .6): continue
            if la is None and not in_pv(r['_bb']): continue              # no pin: stay inside this province's area
            if PRIV.search(r['n'] + ' ' + str(r['ow'])): continue      # private stewardship land is never joined (only listed to check)
            ex = bool(kp) != bool(r['_k'])      # only one name says what kind of place it is: the names must match exactly
            if ex and la is not None and not near(la, lo, r['_bb'], .1): continue   # and be close by (many lakes share a name)
            # Oct 30 4:45 AM (chat 11's ca-key sample, R-G3 location): city / regional greenspace layers repeat the same plain names
            # town after town (Memorial Park, Lions Park, Cariboo Park): a piece from such a layer joins only AT the pin (~1 km box)
            if la is not None and LOCALSRC.search(str(r.get('src') or '')) and not near(la, lo, r['_bb'], .01): continue
            if (same_name(name, r['n'], ex) or (r['nf'] and same_name(name, r['nf'], ex))) and same_kind(kp, r['_k']):
                m.append([r['oid'], r['n'] or r['nf'], acres(r), 'name' if not r.get('src') else 'name · ' + r['src']])
        ov = OVR.get(ref) or {}
        if ov:
            no = {str(q) for q in ov.get('no', [])}
            m = [q for q in m if str(q[0]) not in no and _nf(q[1]) not in {_nf(x) for x in no}]
            for want in ov.get('join', []):
                for r in NEAR:
                    # Oct 29 (R-CA1): a hand join written as an OLD id 'Nova Scotia :26' (12-letter prefix, before one prefix per
                    # layer) also matches the same record number in that prefix's other layers ('Nova Scotia ~1:26'), but only
                    # close to the pin (0.1 deg), so the reviewed record is found again and a far namesake number is not
                    oldid = ':' in str(want) and '~' not in str(want) and re.sub(r'~\d+:', ':', str(r['oid'])) == str(want) and str(r['oid']) != str(want)
                    if (str(r['oid']) == str(want) or _nf(r['n']) == _nf(want) or _nf(r['nf']) == _nf(want) or (oldid and la is not None and near(la, lo, r['_bb'], .1))) and (la is None or near(la, lo, r['_bb'], .02 if ov.get('atpin') else .6)) and not any(str(q[0]) == str(r['oid']) for q in m):
                        m.append([r['oid'], r['n'] or r['nf'], acres(r), 'reviewed-approx' if ov.get('approx') else 'reviewed'])   # Oct 22: approx = closest official land, bigger / other shape
        # Oct 29 (chat 2 + chat 8, as in the US key): 'alias' = another name the official layer uses; joins ONLY with the pin inside it
        if not m and la is not None and ov.get('alias'):
            for al in ov['alias']:
                for r in NEAR:
                    if (_nf(r['n']) == _nf(al) or _nf(r['nf']) == _nf(al)) and near(la, lo, r['_bb'], .05) and inside(la, lo, r['_g']):
                        m.append([r['oid'], r['n'] or r['nf'], acres(r), f'alias name (pin inside): {al}'])
        site = []
        if not m and la is not None:
            for r in NEAR:
                if not near(la, lo, r['_bb'], .03): continue
                nm = r['n'] or r['nf']
                w1, w2 = words(name), words(nm) | words(r['nf'])
                share = len(w1 & w2) / max(1, min(len(w1), len(w2))) if w1 and w2 else 0
                if same_name(name, r['n']) or same_name(name, r['nf']): why = 'same name, different kind of place'
                elif share >= .6: why = 'similar name'
                elif inside(la, lo, r['_g']): why = 'the POTA pin is inside it (different name)'
                else: continue
                c.append([r['oid'], nm, acres(r), why])
            c.sort(key=lambda q: (q[3] != 'similar name', q[3] != 'same name, different kind of place', -q[2])); c = c[:6]
            # Oct 22 review (as in the US key): the ONLY land found is a differently named place around the pin = no outline of its own: 'sits on', off the waiting list
            if c and all(q[3].startswith('the POTA pin is inside') for q in c):
                site = sorted((q for q in c if not re.search(r'buffer zone|closure|\bsfa\b|marine refuge|fishing area|fishery', q[1], re.I)), key=lambda q: q[2])[:2]; c = []
        if ov.get('none'): c = []   # a person looked: no official outline for this park
        used.update(q[0] for q in m)
        parks[ref] = {'n': name, 't': typ, 'm': sorted(m, key=lambda q: -q[2]), 'c': c}
        if site: parks[ref]['a'] = site
        # IS THE BOUNDARY WHERE IT SHOULD BE? (Oct 24: the US key's Oct 21-22 check, ported.) Does the park's own pin
        # fall inside the land it was joined to? 'no shape to check against' = the check is blind (not the join);
        # 'edge' = within about a mile; 'well outside'; 'swap' = another area with the SAME NAME holds the pin (a wrong
        # join with the right land already found). Recorded only; kpc_boundary_report.py reads it.
        if m and la is not None:
            mine = [RID[str(q[0])] for q in m if str(q[0]) in RID]
            shaped = [r for r in mine if rings(r.get('_g'))]
            if not any(inside(la, lo, r['_g']) for r in shaped):
                parks[ref]['far'] = ('no shape to check against' if not shaped else
                                     'edge' if any(near(la, lo, r['_bb'], .02) for r in shaped) else 'well outside')
                if shaped:
                    jn = {_nf(q[1]) for q in m}; mids = {str(q[0]) for q in m}
                    def apart(b): return all(b[2] < q['_bb'][0] or b[0] > q['_bb'][2] or b[3] < q['_bb'][1] or b[1] > q['_bb'][3] for q in shaped if q['_bb'])   # a different place, not the same site in two layers
                    swap = [r for r in NEAR if (_nf(r['n']) in jn or _nf(r['nf']) in jn) and str(r['oid']) not in mids
                            and near(la, lo, r['_bb'], 0) and apart(r['_bb']) and rings(r.get('_g')) and inside(la, lo, r['_g'])]
                    if swap: parks[ref]['swap'] = [[r['oid'], r['n'] or r['nf'], acres(r)] for r in swap[:2]]
    cnt = {'parks': len(parks), 'matched': sum(1 for p in parks.values() if p['m']), 'check': sum(1 for p in parks.values() if not p['m'] and p['c']),
           'none': sum(1 for p in parks.values() if not p['m'] and not p['c'] and not p.get('a')), 'site': sum(1 for p in parks.values() if p.get('a')),
           'pin_outside': sum(1 for p in parks.values() if p.get('far')),
           'pin_well_outside': sum(1 for p in parks.values() if p.get('far') == 'well outside'),
           'pin_no_shape': sum(1 for p in parks.values() if p.get('far') == 'no shape to check against'),
           'pin_swap': sum(1 for p in parks.values() if p.get('swap')), 'detail': USED_DETAIL}
    out = {'updated': time.strftime('%Y-%m-%d'), 'prov': pv, 'source': 'CPCAD (Environment and Climate Change Canada) + provincial and Parks Canada maps, Open Government Licence',
           'note': 'm = joined (same name + same kind), c = check by hand (NOT joined).', 'counts': cnt, 'parks': parks}
    PENDING.append((pv, out))
    R = OUT / 'review'
    L = [f'# Canada {pv}: POTA parks vs official land (CPCAD)', '', f"Built by `.github/scripts/kpc_ca_key.py` (date: data/status/kpc_ca_key.json). **{cnt['matched']} of {cnt['parks']}** joined (same name + same kind). "
         f"**{cnt['check']}** to check, **{cnt['none']}** nothing found in CPCAD (provincial maps come next). Nothing below is joined.", '', '## To check (not joined)', '']
    L += [f"- **{r}** {p['n']} ({p['t']}) → " + '; '.join(f"{q[1]} (~{q[2]:,} ac, {q[3]})" for q in p['c']) for r, p in parks.items() if not p['m'] and p['c']]
    L += ['', '## Sites on bigger land (no outline of their own; the land around the pin)', ''] + [f"- {r} {p['n']} ({p['t']}) → on " + '; '.join(f"{q[1]} (~{q[2]:,} ac)" for q in p['a']) for r, p in parks.items() if p.get('a')]
    L += ['', '## Nothing found in CPCAD', ''] + [f"- {r} {p['n']} ({p['t']})" for r, p in parks.items() if not p['m'] and not p['c'] and not p.get('a')]
    PENDING[-1] += (R / f'CA-{pv}.md', '\n'.join(L) + '\n')
    idx[pv] = cnt
    print(f"{pv}: {cnt['parks']} parks, {cnt['matched']} joined, {cnt['check']} check, {cnt['none']} none", flush=True)
_all = {ref: p for _pv, _o, *_ in PENDING for ref, p in _o['parks'].items()}
_bad = []
for _ref, _nm in GATE_REFS.items():
    _p = _all.get(_ref) or {}
    if not _p.get('m'): _bad.append(f'{_nm} {_ref} lost its outline')
    elif _p.get('far') == 'well outside': _bad.append(f'{_nm} {_ref} pin well outside its outline')
GATE = {'result': 'FAIL' if _bad else 'PASS', 'checked': len(GATE_REFS), 'bad': _bad, 'date': time.strftime('%Y-%m-%d')}
_old_ok = any(OUT.glob('CA-*.json'))
if _bad and _old_ok:
    notice('Canada key GATE FAIL', '; '.join(_bad) + ' -- the old province files are kept (nothing saved). grade me: Canada answer key, ' + ', '.join(_bad))
    raise SystemExit(0)
# RULE SHEET G (Brandon Oct 29 12:09 / 12:14 / 12:18): one grade per park; a pin well outside its official outline = 'POTA pin may
# be wrong' (the outline stays). Canada's joins are all the agencies' own named records, so G-1 holds nothing back here.
_pw = []
for _r, _p in _all.items():
    _m = _p.get('m') or []
    _p['g'] = 'pin' if not _m else ('approximate' if any(str(q[3]).startswith('reviewed-approx') for q in _m) else 'official')
    if _m and _p.get('far') == 'well outside': _p['pin_may_be_wrong'] = 1; _pw.append(_r)
if _pw: notice('Canada key', f"{len(_pw)} parks: the POTA pin sits well outside the official outline (POTA pin may be wrong; the outline stays): {', '.join(_pw[:12])}")
for _pv, _o, _rp, _rt in PENDING:
    save_json(OUT / f'CA-{_pv}.json', _o)
    _rp.parent.mkdir(exist_ok=True); save_text(_rp, _rt)
notice('Canada key GATE ' + GATE['result'], f"{len(GATE_REFS) - len(_bad)} of {len(GATE_REFS)} well-known parks keep an outline (" + ', '.join(GATE_REFS.values()) + ')'
       + ('; ' + '; '.join(_bad) if _bad else '') + f" · grade me: Canada answer key {GATE['result']}, {sum(1 for p in _all.values() if p.get('m'))} of {len(_all)} parks joined")
save_json(OUT / 'index.json', {'provinces': idx, 'gate': GATE})
# Oct 24 (Brandon: 'hook the Canada answer key into the planner, Info Finder and the Kit'): the website needs to know which
# province file holds a park (a CA- number says nothing about the province)
save_json(OUT / 'refs.json', {ref: pv for pv, pk in by.items() for ref in pk})
t = {k: sum(v.get(k, 0) for v in idx.values()) for k in ('parks', 'matched', 'check', 'none', 'site')}
notice('Canada answer key', f"{t['parks']} parks: {t['matched']} joined, {t['check']} to check, {t['site']} sites on bigger land, {t['none']} nothing found · " + ' '.join(f"{k} {v['matched']}/{v['parks']}" for k, v in sorted(idx.items())))
