"""WORLD boundary ANSWER KEY for the busy POTA programs (Brandon Oct 18 2026: 'have data waiting on you'). Same strict method as
kpc_us_key.py / kpc_ca_key.py: pull the country's OFFICIAL protected-area layers (found by kpc_world_probe.py), join to that program's
POTA parks (data/parkinfo/<CC>.json) ONLY when the name matches (generic words in that language dropped, accents dropped) AND the kind
of place matches, near the pin; every piece with that name joins; anything unsure goes on a check list, never joined.
COUNTRIES='AU DE' picks. Writes data/world-key/<CC>.json, data/world-key/review/<CC>.md, data/world-key/index.json.
Sources (official agencies only):
  AU  CAPAD 2024 terrestrial (DCCEEW, Australian Government)                     ArcGIS
  DE  BfN Schutzgebiete WFS (Bundesamt für Naturschutz)                          WFS: Nationalparke, Naturparke, Naturschutzgebiete, Landschaftsschutzgebiete,
                                                                                  Biosphärenreservate, FFH-Gebiete, Vogelschutzgebiete, Nationale Naturmonumente
  GB  Natural England open data (NNR, LNR, Country Parks, SSSI) ArcGIS + NatureScot WFS (cpk, nnr, lnr, …)
  JP  Ministry of the Environment national park areas via Esri Japan's 国立公園区域等 (nps_all) ArcGIS
  PL  GDOŚ refuses GitHub (403): Poland uses the EEA layers live in the tools; skipped here."""
import json, os, re, time, unicodedata, urllib.parse, urllib.request, pathlib

UA = {'User-Agent': 'KPC (kentuckyportableclub.github.io)'}
OUT = pathlib.Path('data/world-key'); (OUT / 'review').mkdir(parents=True, exist_ok=True)
SRC = {
    'AU': [('CAPAD (DCCEEW)', 'arcgis', 'https://gis.environment.gov.au/gispubmap/rest/services/ogc_services/CAPAD/MapServer/0')],
    'DE': [('BfN ' + t, 'wfs', 'https://geodienste.bfn.de/ogc/wfs/schutzgebiet', 'schutzgebiet:' + t) for t in
           ('Nationalparke', 'Naturparke', 'Naturschutzgebiete', 'Biosphaerenreservate', 'Nationale_Naturmonumente', 'Fauna_Flora_Habitat_Gebiete', 'Vogelschutzgebiete', 'Landschaftsschutzgebiete')],
    'GB': [('Natural England ' + n, 'arcgis', f'https://services.arcgis.com/JJzESW51TqeY9uat/arcgis/rest/services/{s}/FeatureServer/0') for n, s in
           (('NNR', 'National_Nature_Reserves_England'), ('LNR', 'Local_Nature_Reserves_England'), ('Country Parks', 'Country_Parks_England'), ('SSSI', 'SSSI_England'),
            ('National Parks', 'National_Parks_England'), ('National Landscapes', 'Areas_of_Outstanding_Natural_Beauty_England'))]
          + [('NatureScot ' + t, 'wfs', 'https://ogc.nature.scot/geoserver/protectedareas/wfs', 'protectedareas:' + t) for t in ('cpk', 'nnr', 'lnr', 'sssi', 'rp', 'sac', 'spa')]
          + [('NRW Wales ' + n, 'wfs', 'https://datamap.gov.wales/geoserver/ows', t) for n, t in
             (('SSSI', 'inspire-nrw:NRW_SSSI'), ('NNR', 'inspire-nrw:NRW_NNR'), ('LNR', 'inspire-nrw:NRW_LNR'), ('National Parks', 'inspire-nrw:NRW_NATIONAL_PARK'),
              ('National Landscapes', 'inspire-nrw:NRW_AONB'), ('Country Parks', 'geonode:country_parks'), ('SAC', 'inspire-nrw:NRW_SAC'), ('SPA', 'inspire-nrw:NRW_SPA'))],
    'JP': [('Ministry of the Environment national parks (Esri Japan)', 'arcgis', 'https://services.arcgis.com/wlVTGRSYTzAbjjiC/arcgis/rest/services/nps_all/FeatureServer/0')],
}
# Oct 18 (Brandon: 'go ahead'): PL ES FR CH AT from the European Environment Agency (official EU inventory, one place for all five):
# Natura 2000 sites + Nationally designated areas (ex-CDDA; Switzerland reports there too, it has no Natura 2000).
EEA = 'https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/'
EU = ('PL', 'ES', 'FR', 'CH', 'AT')
for _c in EU:
    SRC[_c] = [('EEA Natura 2000', 'arcgis', EEA + 'Natura2000Sites/MapServer/2', [f"MS='{_c}'", f"SITECODE LIKE '{_c}%'"]),
               ('EEA nationally designated areas', 'arcgis', EEA + 'CDDA_Dyna_WM/MapServer/4', [f"countryCode='{_c}'", f"countryCode LIKE '{_c}%'"])]
COUNTRIES = (os.environ.get('COUNTRIES') or 'AU DE GB JP PL ES FR CH AT').upper().split()


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', '%0A')[:3500]), flush=True)


def fetch(u, tries=4, timeout=240):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout) as r: return json.loads(r.read().decode('utf-8', 'replace'))
        except Exception as e:  # noqa: BLE001
            last = e; time.sleep(6 * (i + 1))
    raise last


def flat(s): return ''.join(c for c in unicodedata.normalize('NFKD', str(s or '')) if not unicodedata.combining(c)).lower().replace('ß', 'ss')


GEN = {
    'AU': r"nature conservation reserve|flora and fauna reserve|flora fauna reserve|nature recreation area|state recreation area|marine national park|national park|state park|wilderness park|wildlife reserve|state reserve|regional reserve|nature refuge|nature park|bushland reserve|historic reserve|resources reserve|resources area|coastal reserve|scenic reserve|regional park|conservation park|conservation reserve|state conservation area|conservation area|nature reserve|flora reserve|"
          r"state forest|forest reserve|historic site|historical reserve|game reserve|karst conservation reserve|aboriginal area|recreation park|recreation area|"
          r"indigenous protected area|marine park|reserve|park|area",
    'DE': r"nationalpark|naturpark|naturschutzgebiet|landschaftsschutzgebiet|biospharenreservat|biospharengebiet|nationales naturmonument|ffh gebiet|"
          r"vogelschutzgebiet|europaisches vogelschutzgebiet|fauna flora habitat gebiet|schutzgebiet|gebiet|nsg|lsg|ffh|spa|und|im|am|an|der|die|das|des|von|bei|zum|zur|"
          r"national park|nature park|nature reserve|biosphere reserve|landscape protection area|flora and fauna reserve|flora fauna reserve|recreation park|natura 2000|"
          r"special protection area|bird sanctuary|national natural monument|protected area|reserve|park|area",
    'GB': r"national nature reserve|local nature reserve|site of special scientific interest|site of significant scientific interest|sssi|nnr|lnr|country park|national park|regional park|nature reserve|"
          r"area of outstanding natural beauty|national landscape|aonb|conservation reserve|protected area|natural area|special area of conservation|"
          r"special protection area|sac|spa|ramsar|rspb|inc|reserve|park|area",
    'JP': r"quasi national park|national park|prefectural natural park|natural park|kokuritsu koen|kokutei koen|park",
}
_EN = (r"natura 2000|protected landscape area|nature and landscape complex|landscape park|ecological site|national park|natural monument|wetland reserve|"
       r"nature park|national recreation trail|biosphere reserve|world heritage site|protected landscape|state trail|biological reserve|marine conservation area|"
       r"conservation area|recreation park|conservation park|national nature reserve|regional park|forest reserve|ramsar site|game reserve|mire landscapes?|"
       r"landscape reserve|protected area|national reserve|nature conservation reserve|historic site|bird sanctuary|recreation site|nature reserve|park|reserve|area")
_LOC = {'PL': r"park narodowy|park krajobrazowy|rezerwat przyrody|rezerwat|obszar chronionego krajobrazu|zespol przyrodniczo krajobrazowy|uzytek ekologiczny|"
              r"pomnik przyrody|stanowisko dokumentacyjne|ostoja|obszar|plb\d*|plh\d*|i|w|na|nad|pod|im",
        'ES': r"parque nacional|parque natural|parque regional|parque rural|reserva natural|reserva natural parcial|paraje natural|monumento natural|paisaje protegido|"
              r"espacio natural protegido|espacio natural|zona especial de conservacion|zec|lic|zepa|humedal|de|del|la|las|los|el|y|en",
        'FR': r"parc national|parc naturel regional|parc naturel|reserve naturelle nationale|reserve naturelle regionale|reserve naturelle|reserve biologique integrale|"
              r"reserve biologique dirigee|reserve biologique|site classe|zps|zsc|sic|de|du|des|la|le|les|et|d|l|en|sur|aux|au",
        'CH': r"naturschutzgebiete|naturschutzgebiet|nsg|wasser und zugvogelreservat|zugvogelreservat|jagdbanngebiet|waldreservat|naturpark|regionaler naturpark|nationalpark|naturdenkmal|moorlandschaft|auengebiet|reserve naturelle|parc naturel|parco naturale|"
              r"riserva naturale|parco|monumento naturale|zona|und|im|am|an|der|die|das|des|von|bei|de|du|des|la|le|les|et|d|l|e|di|del|della|dei|e dintorni",
        'AT': r"naturschutzgebiete|landschaftsschutzgebiete|europaschutzgebiete|vogelschutzgebiet|naturschutzgebiet|landschaftsschutzgebiet|europaschutzgebiet|nsg|lsg|esg|naturpark|nationalpark|naturdenkmal|geschutzter landschaftsteil|ramsar|"
              r"und|im|am|an|der|die|das|des|von|bei|zum|zur"}
for _c in EU: GEN[_c] = _LOC[_c] + r'|parc|parco|parque|krajobrazowy|naturalny|nacional|regional|' + _EN   # local (longer) words first
KINDS = {
    'AU': [('np', r'national park'), ('cp', r'conservation park|conservation reserve|conservation area|n\.\s?c\.\s?r|\bc\.\s?a\.'), ('nr', r'nature reserve|flora reserve|game reserve|\bn\.\s?r\.|f\.\s?f\.\s?r'),
           ('sf', r'state forest|forest reserve'), ('rp', r'regional park|recreation'), ('hist', r'historic'), ('mp', r'marine')],
    'DE': [('np', r'nationalpark|national park'), ('nat', r'naturpark|nature park'), ('nsg', r'naturschutzgebiet|\bnsg\b|nature reserve'),
           ('lsg', r'landschaftsschutzgebiet|\blsg\b|landscape protection'), ('br', r'biospharen|biosphere'),
           ('ffh', r'\bffh\b|fauna flora habitat|flora and fauna|natura 2000'), ('spa', r'vogelschutz|special protection area|bird sanctuary|natura 2000'),
           ('nnm', r'naturmonument|natural monument')],
    'GB': [('nnr', r'national nature reserve|\bnnr\b'), ('lnr', r'local nature reserve|\blnr\b'), ('cp', r'country park'), ('sssi', r'scientific interest|\bsssi\b'),
           ('np', r'national park'), ('rp', r'regional park'), ('aonb', r'national landscape|outstanding natural beauty|\baonb\b'), ('sac', r'special area of conservation|\bsac\b'), ('spa', r'special protection area|\bspa\b')],
    'JP': [('np', r'(?<!quasi )national park|国立公園'), ('qnp', r'quasi national park|国定公園'), ('pnp', r'prefectural|県立')],
}
for _c in EU: KINDS[_c] = [('n2k', r'natura 2000|\bzps\b|\bzsc\b|\bzepa\b|\bzec\b')]


ABBR = [(r'\bn\.\s?c\.\s?r\b\.?', ' nature conservation reserve '), (r'\bf\.\s?f\.\s?r\b\.?', ' flora fauna reserve '),
        (r'\bn\.\s?r\b\.?', ' nature reserve '), (r'\bc\.\s?a\b\.', ' conservation area '), (r'\bs\.\s?f\b\.', ' state forest '),
        (r'\bb\.\s?r\b\.', ' bushland reserve '), (r'\bh\.\s?r\b\.', ' historic reserve ')]


def norm(cc, s):
    s = flat(s).replace('&', ' and ')
    if cc == 'AU':
        for a, b in ABBR: s = re.sub(a, b, s)
        s = re.sub(r'\bmt\b\.?', 'mount', s); s = re.sub(r'\bst\b\.?', 'saint', s)
        s = re.sub(r'\b[a-z]\d{1,4}\b', ' ', s)   # map codes like 'H57' (Victoria bushland reserves)
    if cc in ('DE', 'AT', 'CH'):
        for a, b in (('ae', 'a'), ('oe', 'o'), ('ue', 'u')): s = s.replace(a, b)   # Schwaebisch = Schwäbisch
    if cc in EU:
        s = re.sub(r"\b[a-z]{2}\d{6,8}\b", ' ', s)              # Natura codes inside POTA names (FR4100198)
        s = re.sub(r"\b(l|d|s|qu)['’]", ' ', s)                 # l'Etang, d'Arc
        s = re.sub(r'\bste?\b\.?', lambda m: 'sainte' if m.group(0).startswith('ste') else 'saint', s)
        s = s.replace('ł', 'l')
    s = re.sub(r'\(.*?\)', ' ', s); s = re.sub(r"[’'`.]", '', s); s = re.sub(r'[-/,]', ' ', s)
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    s = re.sub(r'\b(' + GEN[cc] + r'|the|of|and)\b', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    if cc == 'JP':
        s = s.replace(' ', '')
        for a, b in (('ou', 'o'), ('oo', 'o'), ('uu', 'u'), ('aa', 'a'), ('ii', 'i'), ('nm', 'mm'), ('nb', 'mb'), ('np', 'mp')): s = s.replace(a, b)
    return s


KKS = None
def romaji(t):
    # Japanese layer names → Hepburn romaji so they can meet POTA's English names (pykakasi, installed in the workflow)
    global KKS
    if not re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', t or ''): return t
    if KKS is None:
        try:
            import pykakasi; KKS = pykakasi.kakasi()
        except Exception: KKS = False  # noqa: BLE001
    if not KKS: return t
    return ' '.join(x['hepburn'] for x in KKS.convert(t))


def kinds(cc, s): s = flat(s) + ' ' + str(s or ''); return {k for k, r in KINDS[cc] if re.search(r, s)}
def codes(s): return set(re.findall(r'\b[a-z]\d{1,4}\b', flat(s)))


def same_name(cc, a, b):
    if cc == 'AU':
        ca, cb = codes(a), codes(b)
        if ca and cb and not (ca & cb): return False      # 'Nullan I106' is not 'Nullan I108' (Oct 18 review)
    a, b = norm(cc, a), norm(cc, b)
    if not a or not b: return False
    if a == b: return True
    sh, lo = (a, b) if len(a) < len(b) else (b, a)
    return len(sh) > 4 and lo.startswith(sh) and len(sh) / len(lo) >= 0.6
def words(cc, s): return set(w for w in norm(cc, s).split() if len(w) > 2)


def rings_of(g):
    if not g: return []
    if 'rings' in g: return g['rings']
    t, c = g.get('type'), g.get('coordinates') or []
    if t == 'Polygon': return c
    if t == 'MultiPolygon': return [r for p in c for r in p]
    return []
def bbox(rs):
    xs = [p[0] for r in rs for p in r]; ys = [p[1] for r in rs for p in r]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None
def thin(rs, n=60): return [r[::max(1, len(r) // n)] for r in rs]   # keep it light: only used for 'pin inside'
def in_ring(x, y, r):
    ins = False; j = len(r) - 1
    for i in range(len(r)):
        xi, yi, xj, yj = r[i][0], r[i][1], r[j][0], r[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi: ins = not ins
        j = i
    return ins
def inside(la, lo, rs): return sum(1 for r in rs if in_ring(lo, la, r)) % 2 == 1
def near(la, lo, b, pad): return b and b[0] - pad <= lo <= b[2] + pad and b[1] - pad <= la <= b[3] + pad


NAMEF = ['NAME', 'Name', 'name', 'NNR_NAME', 'LNR_NAME', 'CP_NAME', 'SSSI_NAME', 'PA_NAME', 'NAME_E', 'NAME_EN', 'SITE_NAME', 'sitename', 'NAMEX', '名称', '公園名']
TYPEF = ['TYPE', 'Type', 'type', 'PA_TYPE', 'DESIGNATION', 'desig', 'GAZ_TYPE', 'KIND', '種別', 'TYPE_E']


def pick(a, names):
    for n in names:
        for k in a:
            if k.lower() == n.lower() and a[k] not in (None, ''): return str(a[k])
    return ''
def pick_name(a):
    # known name fields first; else any English-looking *name* field (Welsh layers: SSSI_Name / Name_Welsh…)
    v = pick(a, NAMEF)
    if v: return v
    for k in a:
        if re.search(r'name|enw', k, re.I) and not re.search(r'welsh|cymraeg|_cy$|^cy_|enw', k, re.I) and a[k] not in (None, ''): return str(a[k])
    return ''


def pull_arcgis(label, url, wheres=None):
    for w in (wheres or ['1=1']):
        got = pull_arcgis1(label, url, w)
        if got: return got
    return []


def pull_arcgis1(label, url, where):
    info = fetch(url + '?f=json'); mx = int(info.get('maxRecordCount') or 1000); oidf = info.get('objectIdField') or 'OBJECTID'
    if not oidf or oidf == 'OBJECTID': oidf = next((f['name'] for f in info.get('fields', []) if f.get('type') == 'esriFieldTypeOID'), oidf)
    fnames = [f['name'] for f in info.get('fields', [])]
    notice(f'{label} fields', ', '.join(fnames)[:900])
    recs, off = [], 0
    while True:
        j = fetch(url + '/query?' + urllib.parse.urlencode({'where': where, 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': 0.01,
                                                             'geometryPrecision': 3, 'f': 'json', 'resultOffset': off, 'resultRecordCount': min(mx, 1000), 'orderByFields': oidf}))
        fs = j.get('features', [])
        for f in fs:
            a = f.get('attributes') or {}; rs = rings_of(f.get('geometry'))
            recs.append({'id': a.get(oidf), 'n': pick_name(a), 'ty': pick(a, TYPEF), 'src': label, '_bb': bbox(rs), '_r': thin(rs), '_a': a,
                         'code': str(a.get('SITECODE') or a.get('nationalId') or ''), 'dc': str(a.get('designationTypeCode') or a.get('SITETYPE') or '')})
        if j.get('error'): notice(f'{label} query error', j.get('error')); break
        if not fs or (not j.get('exceededTransferLimit') and len(fs) < min(mx, 1000)): break
        off += len(fs); time.sleep(.5)
    return recs


FMT, TOLD = {}, set()
def pull_wfs(label, url, typ):
    recs, start, step = [], 0, 1000
    while True:
        q = {'SERVICE': 'WFS', 'VERSION': '2.0.0', 'REQUEST': 'GetFeature', 'TYPENAMES': typ, 'OUTPUTFORMAT': 'application/json', 'SRSNAME': 'EPSG:4326',
             'COUNT': step, 'STARTINDEX': start}
        j = None
        for fmt in ([FMT[url]] if url in FMT else ['application/json', 'application/geo+json', 'json', 'geojson', 'application/json; subtype=geojson']):
            q['OUTPUTFORMAT'] = fmt
            try:
                j = fetch(url + '?' + urllib.parse.urlencode(q), tries=2); FMT[url] = fmt; break
            except Exception as e:  # noqa: BLE001
                try:
                    with urllib.request.urlopen(urllib.request.Request(url + '?' + urllib.parse.urlencode(q), headers=UA), timeout=120) as rr: body = rr.read(400)
                except Exception as e2: body = str(e2).encode()  # noqa: BLE001
                if (url, fmt) not in TOLD: TOLD.add((url, fmt)); notice(f'WFS {fmt}', body.decode('utf-8', 'replace'))
        if j is None: raise RuntimeError('no JSON output format worked')
        fs = j.get('features', [])
        for f in fs:
            p = f.get('properties') or {}; rs = rings_of(f.get('geometry'))
            # EPSG:4326 in WFS 2.0 can come back lat,lon: swap when the 'x' looks like a latitude for this country
            if rs and abs(rs[0][0][0]) > 40 and abs(rs[0][0][1]) < 20: rs = [[[q2[1], q2[0]] for q2 in r] for r in rs]
            recs.append({'id': f.get('id'), 'n': pick_name(p), 'ty': pick(p, TYPEF) or label, 'src': label, '_bb': bbox(rs), '_r': thin(rs), '_a': p})
        if len(fs) < step: break
        start += step; time.sleep(.5)
    if recs and not any(r['n'] for r in recs[:50]): notice(f'{label} name field?', ', '.join(list(recs[0]['_a'].keys())[:40]))
    return recs


idx = {}
try: idx = json.load(open(OUT / 'index.json')).get('countries', {})
except Exception: pass  # noqa: BLE001
for cc in COUNTRIES:
    try: P = json.load(open(f'data/parkinfo/{cc}.json'))['parks']
    except Exception: notice(f'World key {cc}', 'no park list yet (data/parkinfo); skipped'); continue  # noqa: BLE001
    recs = []
    for s in SRC.get(cc, []):
        try:
            got = pull_arcgis(s[0], s[2], s[3] if len(s) > 3 else None) if s[1] == 'arcgis' else pull_wfs(s[0], s[2], s[3])
            recs += got; print(f'{cc} {s[0]}: {len(got)}', flush=True)
        except Exception as e:  # noqa: BLE001
            notice(f'World key {cc}', f'{s[0]} FAILED: {e}')
    if not recs: continue
    if cc == 'JP':
        for r in recs:
            r['_k0'] = kinds(cc, r['n']) | kinds(cc, r['ty'])
            if r['n']: r['nj'], r['n'] = r['n'], romaji(r['n'])
        notice('World key JP sample', '; '.join(f"{r.get('nj')} → {r['n']} [{r['ty']}]" for r in recs[:12]) + ' | fields: ' + ', '.join(list(recs[0]['_a'].keys())[:30]))
    for r in recs: r['_k'] = kinds(cc, r['n']) | kinds(cc, r['ty']) | kinds(cc, r['src']) | r.get('_k0', set())
    # 1-degree grid so big countries (FR: 14k parks x 15k areas) stay quick
    GRID = {}
    for i, r in enumerate(recs):
        b = r['_bb']
        if not b: continue
        for gx in range(int((b[0] - .6) // 1), int((b[2] + .6) // 1) + 1):
            for gy in range(int((b[1] - .6) // 1), int((b[3] + .6) // 1) + 1): GRID.setdefault((gx, gy), []).append(i)
    def nearby(la, lo): return [recs[i] for i in GRID.get((int(lo // 1), int(la // 1)), [])] if la is not None else recs
    BYCODE = {r['code'].upper(): r for r in recs if r['code']}
    parks = {}
    for ref, x in sorted(P.items()):
        name, typ, la, lo = x[0], x[2], x[5], x[6]
        kp = kinds(cc, name) | kinds(cc, typ)
        m, c = [], []
        cand = [name] + ([q for q in re.split(r'\s+-\s+', name) if q.strip()] if cc == 'GB' and ' - ' in name else [])
        mr = []
        if cc in EU:
            for code in re.findall(r'\b[A-Z]{2}[0-9A-Z]\d{4,6}\b', name):           # a Natura code in the POTA name = that exact site
                r = BYCODE.get(code)
                if r: m.append([r['id'], r['n'], r['src'], 'site code ' + code])
        for r in ([] if m else nearby(la, lo)):
            if la is not None and not near(la, lo, r['_bb'], .6): continue
            if cc in EU and (('n2k' in kp) != ('n2k' in r['_k'])): continue          # Natura 2000 parks only join Natura 2000 sites, and the other way round
            if r['n'] and any(same_name(cc, q, r['n']) for q in cand) and (not kp or (kp & r['_k']) or (not r['_k'] and not (cc == 'AU' and r.get('ty')))):
                m.append([r['id'], r['n'], r['src'], 'name']); mr.append(r)
        if cc in EU and len({r2['dc'] for r2 in mr if r2['src'] == 'EEA nationally designated areas'}) > 1:
            c = [[q[0], q[1], q[2], 'same name, more than one kind of area'] for q in m]; m = []   # e.g. a reserve and a landscape park with one name
        if c: parks[ref] = {'n': name, 't': typ, 'm': [], 'c': c[:6]}; continue
        if not m and la is not None:
            for r in nearby(la, lo):
                if not near(la, lo, r['_bb'], .03) or not r['n']: continue
                w1, w2 = words(cc, name), words(cc, r['n'])
                share = len(w1 & w2) / max(1, min(len(w1), len(w2))) if w1 and w2 else 0
                if same_name(cc, name, r['n']): why = 'same name, different kind of place'
                elif share >= .6: why = 'similar name'
                elif inside(la, lo, r['_r']): why = 'the POTA pin is inside it (different name)'
                else: continue
                c.append([r['id'], r['n'], r['src'], why])
            c = sorted(c, key=lambda q: (q[3] != 'similar name', q[3] != 'same name, different kind of place'))[:6]
        parks[ref] = {'n': name, 't': typ, 'm': m, 'c': c}
    cnt = {'parks': len(parks), 'matched': sum(1 for p in parks.values() if p['m']), 'check': sum(1 for p in parks.values() if not p['m'] and p['c']),
           'none': sum(1 for p in parks.values() if not p['m'] and not p['c']), 'areas': len(recs)}
    (OUT / f'{cc}.json').write_text(json.dumps({'updated': time.strftime('%Y-%m-%d'), 'cc': cc, 'sources': [s[0] for s in SRC[cc]], 'counts': cnt, 'parks': parks},
                                               separators=(',', ':'), ensure_ascii=False), encoding='utf-8')
    L = [f'# {cc}: POTA parks vs official land', '', f"Built {time.strftime('%Y-%m-%d')} by `.github/scripts/kpc_world_key.py` from: {', '.join(s[0] for s in SRC[cc])}. "
         f"**{cnt['matched']} of {cnt['parks']}** joined (same name + same kind), **{cnt['check']}** to check, **{cnt['none']}** nothing found. Nothing below is joined.", '', '## To check (not joined)', '']
    L += [f"- **{r}** {p['n']} ({p['t']}) → " + '; '.join(f"{q[1]} ({q[2]}, {q[3]})" for q in p['c']) for r, p in parks.items() if not p['m'] and p['c']]
    L += ['', '## Nothing found', ''] + [f"- {r} {p['n']} ({p['t']})" for r, p in parks.items() if not p['m'] and not p['c']]
    (OUT / 'review' / f'{cc}.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    idx[cc] = cnt
    notice(f'World key {cc}', f"{cnt['matched']} of {cnt['parks']} joined, {cnt['check']} to check, {cnt['none']} nothing found ({cnt['areas']} official areas read)")
    json.dump({'updated': time.strftime('%Y-%m-%d'), 'countries': idx}, open(OUT / 'index.json', 'w'), separators=(',', ':'))
