"""US boundary ANSWER KEY, every state but Kentucky (Brandon Oct 17 2026: 'quick and best method… why not start them tonight').
For each state: every federal / state FEE record in USGS PAD-US (names, type, manager, acres, a coarse outline for 'where it is'),
matched to that state's POTA parks (data/parkinfo/US-XX.json) with the same strict rule the Kentucky tools use:
SAME NAME (generic words dropped) AND SAME KIND of place (WMA to WMA, state park to state park…), near the park's pin.
Anything unsure is NOT joined: it goes on the park's 'check' list with the reason. Writes:
  data/us-key/US-XX.json  {updated, st, parks:{ref:{n, t, m:[[objectid, name, acres, how]], c:[[objectid, name, acres, why]]}},
                           nonum:[[objectid, name, designation, manager, acres]] (biggest 300 fed/state places no POTA park matched), counts}
  data/us-key/index.json  {updated, states:{XX:{parks, matched, check, none, nonum}}}
STATES='TN IN' picks states (default: every state + DC except KY). PAD-US's firewall refuses long WHERE clauses, so we list each state with
State_Nm='XX' only and filter here."""
import json, math, os, re, sys, time, urllib.parse, urllib.request, pathlib

Q = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
ALL = 'AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split()
STATES = (os.environ.get('STATES') or '').upper().replace(',', ' ').split() or ALL
OUT = pathlib.Path('data/us-key'); OUT.mkdir(parents=True, exist_ok=True)
T0 = time.time(); LIMIT = float(os.environ.get('MINUTES') or 300) * 60


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', '%0A')), flush=True)


def get(params, tries=5):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(Q + '?' + urllib.parse.urlencode(params), headers={'User-Agent': 'KPC (kentuckyportableclub.github.io)'})
            with urllib.request.urlopen(req, timeout=180) as r:
                j = json.loads(r.read().decode('utf-8', 'replace'))
            if j.get('error'): raise RuntimeError(str(j['error'])[:200])
            return j
        except Exception as e:  # noqa: BLE001
            last = e; time.sleep(8 * (i + 1))
    raise last


# ---------------- names + kinds (same idea as kpc-bounds.js, with other states' words) ----------------
GEN = (r"state habitat area|habitat area|mitigation park wildlife and environmental area|wildlife and environmental area|state scientific and natural area|scientific and natural area|scenic reserve|state natural reserve|natural reserve|coastal reserve|conservation reserve|unique area|state wayside|national memorial|natural environment area|nrma|nea|blm national conservation area|national conservation area|wildlife management area (and|&) public fishing area|public fishing area|fishing area|national wild and scenic river|wild and scenic river|national recreational river|state vehicle recreation area|vehicle recreation area|state reservation|reservation|state reserve|national reserve|national fish hatchery|state fish hatchery|fish hatchery|hatchery|fh|fishery area|state fishery area|blm herd management area|herd management area|herd area|blm special recreation management area|special recreation management area|extensive recreation management area|blm recreation management area|recreation management area|wilderness study area|wsa|hma|srma|erma|blm|fishing access site|access site|state game lands? number|designated state natural area|designated|public hunting area|hunting area|state fishing lake|fishing lake|state wilderness area|wilderness area|wilderness|resort|natural state conservation area|waterfowl refuge|wildlife refuge|refuge|state natural area|natural area preserve|state nature preserve|nature preserve|natural area|fish and wildlife area|state wildlife area|"
       r"wildlife management area|wildlife area|state game lands?|game lands?|game areas?|game management area|conservation area|state conservation area|"
       r"state resort park|state historic site|state historical park|state historic park|historic site|state recreation area|recreation area|"
       r"state beach|state seashore|national wildlife refuge|national recreation area|national historical park|national historic site|"
       r"national park|national forest|national grassland|national monument|national seashore|national lakeshore|national battlefield|"
       r"national military park|national preserve|national river|state park|state forest|management area|wma|nwr|nra|nca|na|wa|sp|sf|sgl|state|number|no|the|of|and")
ABBR = {'sulphur': 'sulfur', 'vehicular': 'vehicle', 'recreational': 'recreation', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine', '10': 'ten', '11': 'eleven', '12': 'twelve', 'col': 'colonel', 'sgt': 'sergeant', 'mt': 'mount', 'ft': 'fort', 'st': 'saint', 'pt': 'point', 'lk': 'lake', 'cr': 'creek', 'mtn': 'mountain'}
def norm(s, drop1=False):
    s = str(s or '')
    s = re.sub(r'^([A-Za-z-]+) \(([^)]+)\)', r'\2 \1', s)   # 'Busch (August A.) Memorial' = 'August A. Busch Memorial'
    s = re.sub(r'&', ' and ', s.lower()).replace('-', ' ')
    s = re.sub(r'\(.*?\)', ' ', s)                       # '(2021 Addition)'
    s = re.sub(r"[’'`ʻʼ‘]", '', s)                         # Chimney's = Chimneys; Hawaiian ʻokina (Kuliʻouʻou = Kuliouou)
    s = re.sub(r'\.', ' ', s)
    s = re.sub(r'\b([a-z])\b(?:\s+(?=[a-z]\b))', r'\1', s)  # initials: 'm t s u' = 'mtsu', 'c r' = 'cr'
    s = re.sub(r'^[a-z]{2} (\d)', r'\1', s)                # 'PA 332 State Game Land' = 'State Game Land 332'
    s = re.sub(r'\b0+(\d)', r'\1', s)                     # 'Game Land 013' = 'Game Lands 13'
    s = re.sub(r'\b(unit|tract|parcel)\s+[0-9ivx]+\b', ' ', s)
    s = ' '.join(ABBR.get(w, w) for w in s.split())
    s = re.sub(r'\b(' + GEN + r')\b', ' ', s)
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    s = ' '.join(ABBR.get(w, w) if w.isdigit() else w for w in s.split())   # '#4' = 'Pool 4' = 'Pool Four'
    if drop1: s = re.sub(r'(?<=[a-z0-9] )[a-z](?= [a-z0-9])', ' ', s)   # only a MIDDLE initial (World War I keeps its I)              # also try without a lone middle initial ('George H. Crosby')
    return re.sub(r'\s+', ' ', s).strip()


KINDS = [('wma', r'wildlife management area|\bwma\b|wildlife area|game lands?|game areas?|game management area|hunting area|fish and wildlife area|public hunting|fishery area|fishing access|habitat area|wildlife and environmental area|(?<!recreation )(?<!herd )(?<!conservation )management area'),
         ('wsr', r'wild (and|&) scenic river|recreational river'),
         ('ca', r'conservation area|conservation reserve|\baccess$'),          # Missouri: 'Kings Prairie Access' = Kings Prairie Access State Conservation Area
         ('snp', r'nature preserve|natural area|\bsnp\b|\bsna\b|natural heritage|\bpreserve\b|natural state conservation|natural reserve|scientific and natural|natural environment area|\bnea\b|\bnrma\b'),
         ('hist', r'historic(al)? (site|park|area)|\bshs\b'),
         ('sp', r'state (resort )?park|historic(al)? park|\bsrp\b|recreation(al)? area|state beach|state seashore'),
         ('nf', r'national forest|national grassland'), ('sf', r'state forest'),
         ('nwr', r'wildlife refuge|\bnwr\b'), ('nfh', r'hatchery|\bnfh\b|\bfh\b'),
         ('nps', r'national (park|monument|preserve|seashore|lakeshore|battlefield|military park|river|scenic river|parkway)'),
         ('wild', r'wilderness(?! study)'), ('wsa', r'wilderness study area|\bwsa\b'),
         ('hma', r'herd (management )?area|\bhma\b'),
         ('rma', r'recreation management area|\bs?rma\b|\berma\b|campground|recreation site|day use area')]
def kinds(s):
    s = str(s or '').lower(); return {k for k, r in KINDS if re.search(r, s)}
DES = {'SP': 'sp', 'SREC': 'sp', 'SHCA': 'hist', 'NWR': 'nwr', 'NF': 'nf', 'NG': 'nf', 'NP': 'nps', 'NM': 'nps', 'NRA': 'nps', 'NHS': 'hist', 'WA': 'wild'}


def variants(s):
    # other ways of writing the same name: no middle initial, bracket words left out ('Reifsnider (Frank)'), no leading 'Mount'
    v = {norm(s), norm(s, True), norm(re.sub(r'\(.*?\)', ' ', str(s or '')))}
    v |= {re.sub(r'^mount ', '', x) for x in v}
    v |= {re.sub(r' (park|forest|pond|ponds|lake|reservoir|complex|memorial|reserve)$', '', x) for x in v}         # 'Fort Revere Park' = Fort Revere, 'Coulee Experimental Forest'
    return {x for x in v if x}


def same_name(a, b):
    if str(a or '').strip().lower() == str(b or '').strip().lower(): return True
    a1, b1 = norm(a), norm(b)
    if _same(a1, b1) or any(_same(x, y) for x in variants(a) for y in variants(b)): return True
    sa, sb = _sing(a1), _sing(b1)                          # McCloskey's = McCloskey, Glades = Glade
    if _same(sa, sb): return True
    return len(sa) >= 8 and len(sb) >= 8 and not re.search(r'\d', sa + sb) and _ed1(sa, sb)   # one-letter typos in PAD-US ('Horshoe', 'Morraine')


SOFT = {'preserve', 'reserve', 'beach', 'complex', 'game', 'mua', 'fwma', 'ca', 'pas', 'tract', 'tracts', 'addition', 'unit', 'area', 'lake', 'pond', 'ponds', 'reservoir',
        'park', 'forest', 'center', 'centre', 'site', 'lands', 'land'}
def _soft(x): return ' '.join(w for w in x.split() if w not in SOFT and not re.fullmatch(r'(19|20)\d\d', w))


def exact_name(a, b):
    # no 'starts with' allowance: used when only one of the two names says what kind of place it is.
    # Only 'soft' words may differ (Torrey Pines Reserve = Torrey Pines State Reserve, Big Bend = Big Bend - 2015)
    if str(a or '').strip().lower() == str(b or '').strip().lower(): return True
    va, vb = variants(a), variants(b)
    va |= {_soft(x) for x in va if _soft(x)}; vb |= {_soft(x) for x in vb if _soft(x)}
    if va & vb or {_sing(x) for x in va} & {_sing(x) for x in vb}: return True
    return any(len(x) >= 8 and len(y) >= 8 and not re.search(r'\d', x + y) and _ed1(x, y) for x in va for y in vb)   # one-letter typo ('Pishkin' / 'Pishkun')


def name_ok(a, b, ka, kb):
    if not same_kind(ka, kb): return False
    if ('nfh' in ka) != ('nfh' in kb): return False                      # a hatchery only joins a hatchery (Dworshak Reservoir is not the hatchery)
    if bool(re.search(r'\btrail\b', str(a), re.I)) != bool(re.search(r'\btrail\b', str(b), re.I)): return False   # a trail only joins a trail
    return exact_name(a, b) if (bool(ka) != bool(kb)) else same_name(a, b)


def _sing(s): return ' '.join(w[:-1] if len(w) > 3 and w.endswith('s') else w for w in s.split())


def _ed1(a, b):
    if a == b: return True
    wa, wb = a.split(), b.split()   # one typo inside one long word only ('Horshoe'), never a short word ('I' / 'II')
    if len(wa) != len(wb): return False
    diff = [(x, y) for x, y in zip(wa, wb) if x != y]
    if len(diff) != 1 or min(len(diff[0][0]), len(diff[0][1])) < 5: return False
    a, b = diff[0]
    if abs(len(a) - len(b)) > 1: return False
    if len(a) == len(b): return sum(x != y for x, y in zip(a, b)) == 1
    if len(a) > len(b): a, b = b, a
    return any(a == b[:i] + b[i + 1:] for i in range(len(b)))


def wset(s):
    # every word, keeping words in brackets ('Cash (Ben) Memorial' = Ben Cash Memorial)
    return set(w for w in _sing(norm(str(s or '').replace('(', ' ').replace(')', ' '))).split() if len(w) > 1)


def same_words(a, b, ka, kb):
    # all words of the shorter name are in the longer one, at most 2 extra words, and BOTH names say the same kind of place
    if not (ka and kb and ka & kb): return False
    if ('nfh' in ka) != ('nfh' in kb) or bool(re.search(r'\btrail\b', str(a), re.I)) != bool(re.search(r'\btrail\b', str(b), re.I)): return False
    w1, w2 = wset(a), wset(b)
    s, l = (w1, w2) if len(w1) <= len(w2) else (w2, w1)
    big = [w for w in s if len(w) > 2]
    if len(big) == 1:   # one long word, same kind ('Keyhole' = 'Keyhole Reservoir'); wrong ones go in overrides.json 'no'
        return len(big[0]) >= 6 and ka == kb and s <= l and len(l - s) <= 2
    return len(big) >= 2 and s <= l and len(l - s) <= 2


def _same(a, b):
    if not a or not b: return False
    if a == b: return True
    s, l = (a, b) if len(a) < len(b) else (b, a)
    return len(s) > 5 and l.startswith(s) and l[len(s):len(s) + 1] == ' ' and len(s) / len(l) >= 0.6   # whole words only (World War I is not World War II)


US_COMPAT = [{'wild', 'wsa'}, {'ca', 'snp'}]   # POTA lists many BLM study areas as 'BLM Wilderness Area'
def same_kind(ka, kb): return not ka or not kb or bool(ka & kb) or any(ka & c and kb & c and (ka | kb) & c == c for c in US_COMPAT)


def words(s): return set(w for w in norm(s).split() if len(w) > 2)


# ---------------- geometry helpers (coarse) ----------------
def rings(g): return g.get('rings') or [] if g else []
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
def near(la, lo, b, pad): return b and b[0] - pad <= lo <= b[2] + pad and b[1] - pad <= la <= b[3] + pad


FIELDS = None
def fields():
    global FIELDS
    if FIELDS is None:
        try:
            req = urllib.request.Request(Q.rsplit('/', 1)[0] + '?f=json', headers={'User-Agent': 'KPC (kentuckyportableclub.github.io)'})
            have = {f['name'] for f in json.loads(urllib.request.urlopen(req, timeout=120).read()).get('fields', [])}
        except Exception: have = set()  # noqa: BLE001
        want = 'OBJECTID,Unit_Nm,Loc_Nm,Own_Type,Mang_Type,Mang_Name,Loc_Mang,Des_Tp,d_Des_Tp,Pub_Access,GIS_Acres,Category'.split(',')
        FIELDS = ','.join(w for w in want if not have or w in have)
        notice('PAD-US fields', FIELDS + (' (field list not read)' if not have else ''))
    return FIELDS


GEO = [{'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': 0.01, 'geometryPrecision': 3},
       {'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': 0.01}, {'returnGeometry': 'true', 'outSR': 4326}]
GI = [0]
def page(st, off):
    while True:
        q = {'where': "State_Nm='%s'" % st, 'outFields': fields(), 'f': 'json', 'resultOffset': off, 'resultRecordCount': 500, 'orderByFields': 'OBJECTID'}
        q.update(GEO[GI[0]])
        try: return get(q, tries=3)
        except Exception as e:  # noqa: BLE001
            if GI[0] + 1 >= len(GEO): raise
            notice('PAD-US', f'query shape {GI[0]} refused ({e}); trying a simpler one'); GI[0] += 1


def pad_state(st):
    recs, off = [], 0
    while True:
        j = page(st, off)
        fs = j.get('features', [])
        for f in fs:
            a = f.get('attributes') or {}
            if (a.get('Category') or '') not in ('Fee', 'Designation'): continue   # Designation = wilderness, NCA… overlays (BLM wilderness has no fee record of its own)
            # Oct 18: + DIST (regional special districts: Florida's water management districts own the 'State Conservation Areas' POTA lists)
            if (a.get('Own_Type') or '') not in ('FED', 'STAT', 'DIST') and (a.get('Mang_Type') or '') not in ('FED', 'STAT', 'DIST'): continue
            g = f.get('geometry') or {}
            a['_bb'] = bbox(g); a['_g'] = g
            a['_k'] = kinds(a.get('Unit_Nm')) | kinds(a.get('Loc_Nm')) | ({DES[a['Des_Tp']]} if a.get('Des_Tp') in DES else set())
            recs.append(a)
        if not fs or (not j.get('exceededTransferLimit') and len(fs) < 500): break
        off += len(fs); time.sleep(.6)
    return recs, off + len(fs)


FWS = 'https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSInterest_Simplified_Authoritative/FeatureServer/0/query'
STB = None
def st_box(st):
    global STB
    if STB is None:
        try: STB = json.load(open('kpc-us-states.json'))
        except Exception: STB = []  # noqa: BLE001
    x = next((b for b in STB if b.get('a') == st), None)
    if not x: return None
    xs = [q[0] for pl in x['p'] for q in pl[0]]; ys = [q[1] for pl in x['p'] for q in pl[0]]
    return [min(xs), min(ys), max(xs), max(ys)]


def fws_state(st, have):
    # USFWS's own land layer: PAD-US misses some refuges (Oklahoma: Sequoyah, Optima, Tishomingo NWR are not in it)
    box = st_box(st)
    if not box: return []
    out, off = [], 0
    while True:
        q = {'where': "INTTYPE1<>'E'", 'geometry': ','.join(map(str, box)), 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
             'outFields': 'OBJECTID,ORGNAME,RSL_TYPE,SUM_GISACRES', 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': 0.01, 'geometryPrecision': 3,
             'f': 'json', 'resultOffset': off, 'resultRecordCount': 500}
        try:
            req = urllib.request.Request(FWS + '?' + urllib.parse.urlencode(q), headers={'User-Agent': 'KPC (kentuckyportableclub.github.io)'})
            j = json.loads(urllib.request.urlopen(req, timeout=180).read().decode('utf-8', 'replace'))
        except Exception as e:  # noqa: BLE001
            notice(f'US key {st}', f'USFWS land not read ({e})'); return out
        fs = j.get('features', [])
        for f in fs:
            a = f.get('attributes') or {}; nm = (a.get('ORGNAME') or '').title()
            if not nm or norm(nm) in have: continue
            g = f.get('geometry') or {}
            out.append({'OBJECTID': 'fws' + str(a.get('OBJECTID')), 'Unit_Nm': nm, 'Loc_Nm': '', 'Own_Type': 'FED', 'Mang_Type': 'FED', 'Mang_Name': 'FWS',
                        'Loc_Mang': 'U.S. Fish & Wildlife Service (own map)', 'Des_Tp': '', 'GIS_Acres': a.get('SUM_GISACRES') or 0, 'Category': 'Fee',
                        '_bb': bbox(g), '_g': g, '_k': kinds(nm) | kinds(a.get('RSL_TYPE')) | {'nwr'}})
        if not fs or (not j.get('exceededTransferLimit') and len(fs) < 500): break
        off += len(fs); time.sleep(.5)
    return out


# Official maps of the agencies themselves (Oct 18, Brandon: 'anything you can be working on in the US trip planner'): PAD-US stores wilderness,
# BLM herd areas and BLM recreation areas only as the forest / BLM office around them, so those parks never matched by name.
XS = [  # prefix, query url, name field, acres field, kinds
    ('wld', 'https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_Wilderness_02/MapServer/0/query', 'wildernessname', 'gis_acres', {'wild'}, 'National Wilderness Preservation System (Forest Service map)'),
    ('hma', 'https://gis.blm.gov/arcgis/rest/services/range/BLM_Natl_WHB/MapServer/0/query', 'HMA_NAME', 'BLM_ACRES', {'hma'}, 'BLM herd management areas'),
    ('rma', 'https://gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recreation/MapServer/9/query', 'FET_NAME', 'GIS_ACRES', {'rma'}, 'BLM recreation areas'),
    ('rst', 'https://gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recs_poly/MapServer/0/query', 'FET_NAME', 'GIS_ACRES', {'rma'}, 'BLM recreation sites'),
    ('nca', 'https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_NM_NCA_poly/MapServer/0/query', 'NCA_NAME', '', set(), 'BLM national monuments / conservation areas'),
    # Oct 18: layer id + name field looked up at run time ('?' = find it); found by probe 2
    ('wsa', 'svc:https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_WLD_WSA/MapServer|study', '?', '?', {'wsa'}, 'BLM wilderness study areas'),
    ('wbl', 'svc:https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_WLD_WSA/MapServer|^(?!.*study).*wilderness', '?', '?', {'wild'}, 'BLM wilderness'),
    ('odw', 'svc:https://services1.arcgis.com/jRf8jjFwxedITdFe/arcgis/rest/services/Public_WMA_Boundaries/FeatureServer|.', '?', '?', {'wma'}, 'Oklahoma Dept. of Wildlife Conservation WMA map', 'STAT', {'OK'}),
]
RESOLVED = {}
def resolve(pre, url, nf, af):
    # 'svc:<service>|<layer name regex>' → (query url, name field, acres field, object id field)
    if not url.startswith('svc:'): return url, nf, af, ('objectid' if pre == 'wld' else 'OBJECTID')
    if pre in RESOLVED: return RESOLVED[pre]
    svc, rx = url[4:].split('|', 1)
    rq = lambda u: json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'KPC (kentuckyportableclub.github.io)'}), timeout=120).read().decode('utf-8', 'replace'))
    lays = rq(svc + '?f=json').get('layers') or []
    pick = [l for l in lays if re.search(rx, l.get('name', ''), re.I) and not l.get('subLayerIds')] or [l for l in lays if not l.get('subLayerIds')]
    lid = pick[0]['id']
    L = rq(f'{svc}/{lid}?f=json'); flds = L.get('fields') or []
    strs = [f['name'] for f in flds if f.get('type') == 'esriFieldTypeString']
    name = next((f for f in strs if re.search(r'(^|_)(NAME|NM)(_|$)|NAME', f, re.I) and not re.search(r'admin|state|county|office|agency|own|mgr|manag|type|desig|file', f, re.I)), strs[0] if strs else '')
    acres = next((f['name'] for f in flds if re.search(r'acre', f['name'], re.I)), '')
    oid = L.get('objectIdField') or next((f['name'] for f in flds if f.get('type') == 'esriFieldTypeOID'), 'OBJECTID')
    RESOLVED[pre] = (f'{svc}/{lid}/query', name, acres, oid)
    notice('US key layer found', f'{pre}: {svc}/{lid} [{pick[0].get("name")}] name={name} acres={acres} oid={oid}')
    return RESOLVED[pre]
XCOUNT = {}
def extra_state(st, have):
    box = st_box(st)
    if not box: return []
    out = []
    for x in XS:
        pre, url, nf, af, kk, label = x[:6]
        own = x[6] if len(x) > 6 else 'FED'
        if len(x) > 7 and st not in x[7]: continue
        try: url, nf, af, oidf = resolve(pre, url, nf, af)
        except Exception as e:  # noqa: BLE001
            notice(f'US key {st}', f'{label} layer not found ({e})'); continue
        off, n = 0, 0
        while True:
            q = {'where': '1=1', 'geometry': ','.join(map(str, box)), 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
                 'outFields': ','.join(q for q in (oidf, nf, af) if q), 'returnGeometry': 'true', 'outSR': 4326,
                 'maxAllowableOffset': 0.01, 'geometryPrecision': 3, 'f': 'json', 'resultOffset': off, 'resultRecordCount': 500}
            try:
                req = urllib.request.Request(url + '?' + urllib.parse.urlencode(q), headers={'User-Agent': 'KPC (kentuckyportableclub.github.io)'})
                j = json.loads(urllib.request.urlopen(req, timeout=180).read().decode('utf-8', 'replace'))
                if j.get('error'): raise RuntimeError(str(j['error'])[:150])
            except Exception as e:  # noqa: BLE001
                notice(f'US key {st}', f'{label} not read ({e})'); break
            fs = j.get('features', [])
            for f in fs:
                a = {k.lower(): v for k, v in (f.get('attributes') or {}).items()}
                nm = (a.get(nf.lower()) or '').strip()
                if not nm: continue
                k = kinds(nm) | kk
                if (norm(nm), frozenset(k)) in have: continue
                g = f.get('geometry') or {}
                out.append({'OBJECTID': pre + str(a.get(oidf.lower())), 'Unit_Nm': nm, 'Loc_Nm': '', 'Own_Type': own, 'Mang_Type': own, 'Mang_Name': pre.upper(),
                            'Loc_Mang': label, 'Des_Tp': '', 'GIS_Acres': (a.get(af.lower()) if af else 0) or 0, 'Category': 'Fee', '_bb': bbox(g), '_g': g, '_k': k})
                n += 1
            if not fs or (not j.get('exceededTransferLimit') and len(fs) < 500): break
            off += len(fs); time.sleep(.5)
        XCOUNT[pre] = XCOUNT.get(pre, 0) + n
    return out


def out_date(): return time.strftime('%Y-%m-%d')


# Sites (Oct 18 review): an airstrip, trailhead, hatchery, byway, BLM recreation site… has no outline of its own in any official map;
# when the only official land found is the bigger place AROUND its pin, it is not a 'check' case: we keep that land as 'a' (sits on), never joined.
SITE = re.compile(r'airstrip|interpretive site|historic preservation site|trail ?head|day use|recreation site|\bohv\b|off.highway|byway|backway|historic(al)? trail|'
                  r'historical monument|multiple use area|hatchery|historic area|designated routes?|desigated|desingated|staging area|camping area|campground|boat (ramp|launch)|'
                  r'rock ?hounding|petroglyph|kilns|^blm |\bblm\b.*recreation management area|scenic drive|overlook|wayside|picnic', re.I)

# Reviewed by hand (Oct 18 on): data/us-key/overrides.json {ref: {join: [objectid or exact name], no: [objectid or exact name], why: '...'}}.
# 'join' adds that official land (it must be within ~0.6° of the pin), 'no' keeps a piece out; the bot follows it on every rerun.
try: OVR = json.load(open(OUT / 'overrides.json')).get('parks', {})
except Exception: OVR = {}  # noqa: BLE001
def _oid(a): return str(a['OBJECTID'])


PIN = {}
def pins():
    # 20 state park files have no lat/lon (older format): fall back to the site index, then locations.json
    if PIN: return PIN
    try:
        for r in json.load(open('data/parkinfo/index.json')).get('rows', []):
            if len(r) > 4 and r[3] is not None: PIN[r[0]] = (r[3], r[4])
    except Exception: pass  # noqa: BLE001
    try:
        for r in json.load(open('locations.json')):
            if r[0] == 'POTA' and r[1] not in PIN: PIN[r[1]] = (r[3], r[4])
    except Exception: pass  # noqa: BLE001
    return PIN


def run(st):
    try: P = json.load(open(f'data/parkinfo/US-{st}.json'))['parks']
    except Exception: notice(f'US key {st}', 'no park file, skipped'); return None  # noqa: BLE001
    recs, seen = pad_state(st)
    recs += fws_state(st, {norm(a.get('Unit_Nm') or '') for a in recs if a.get('Mang_Name') == 'FWS'})
    recs += extra_state(st, {(norm(a.get('Unit_Nm') or ''), frozenset(a['_k'])) for a in recs})
    parks, used = {}, set()
    for ref, r in sorted(P.items()):
        name, typ, la, lo = r[0], r[2] if len(r) > 2 else '', r[5] if len(r) > 5 else None, r[6] if len(r) > 6 else None
        if la is None and ref in pins(): la, lo = pins()[ref]
        kp = kinds(name) | kinds(typ)
        m, c = [], []
        for a in recs:
            nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
            close = la is None or near(la, lo, a['_bb'], .6)
            if not close: continue
            if bool(kp) != bool(a['_k']) and la is not None and not near(la, lo, a['_bb'], .1): close = False   # one name has no kind word: must be close by
            if not close: continue
            if name_ok(name, nm, kp, a['_k']) or (a.get('Loc_Nm') and name_ok(name, a['Loc_Nm'], kp, a['_k'])):
                m.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), 'name'])
            elif isinstance(a['OBJECTID'], int) and not kinds(nm) and exact_name(name, nm) and name_ok(name, nm, kp, set()):
                # Oct 18 review: a bare PAD-US name ('Fort Fetterman', 'Trail End') whose only 'kind' came from its designation code,
                # and the whole name matches: the designation code is often off, so the name decides
                m.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), 'name (designation code ignored)'])
            elif near(la, lo, a['_bb'], .1) if la is not None else False:
                if same_words(name, nm, kp, a['_k']) or (a.get('Loc_Nm') and same_words(name, a['Loc_Nm'], kp, a['_k'])):
                    m.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), 'words'])
        ov = OVR.get(ref) or {}
        if ov:
            no = {str(x) for x in ov.get('no', [])}
            m = [x for x in m if str(x[0]) not in no and x[1] not in no]
            for want in ov.get('join', []):
                for a in recs:
                    nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
                    if (_oid(a) == str(want) or nm == want) and (la is None or near(la, lo, a['_bb'], .6)) and not any(str(x[0]) == _oid(a) for x in m):
                        m.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), 'reviewed'])
        site = []
        if not m and la is not None:
            # unsure: not joined, only listed so a person can look
            for a in recs:
                nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
                if not near(la, lo, a['_bb'], .02): continue
                w1, w2 = words(name), words(nm)
                share = len(w1 & w2) / max(1, min(len(w1), len(w2))) if w1 and w2 else 0
                if same_name(name, nm): why = 'same name, different kind of place'
                elif share >= .6: why = 'similar name'
                elif inside(la, lo, a['_g']): why = 'the POTA pin is inside it (different name)'
                else: continue
                c.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), why])
            c.sort(key=lambda x: (x[3] != 'similar name', x[3] != 'same name, different kind of place', -x[2])); c = c[:6]
            if c and SITE.search(name + ' ' + typ) and all(x[3].startswith('the POTA pin is inside') for x in c):
                site = sorted(c, key=lambda x: x[2])[:2]; c = []
            if ov.get('site'): site, c = sorted(c, key=lambda x: x[2])[:2] or site, []
        for x in m: used.add(x[0])
        parks[ref] = {'n': name, 't': typ, 'm': sorted(m, key=lambda x: -x[2]), 'c': c}
        if site: parks[ref]['a'] = site
    nonum = sorted(([a['OBJECTID'], a.get('Unit_Nm') or a.get('Loc_Nm') or '', a.get('d_Des_Tp') or a.get('Des_Tp') or '', a.get('Loc_Mang') or a.get('Mang_Name') or '',
                     round(a.get('GIS_Acres') or 0)] for a in recs if a['OBJECTID'] not in used), key=lambda x: -x[4])
    counts = {'parks': len(parks), 'matched': sum(1 for p in parks.values() if p['m']), 'check': sum(1 for p in parks.values() if not p['m'] and p['c']),
              'none': sum(1 for p in parks.values() if not p['m'] and not p['c'] and not p.get('a')), 'site': sum(1 for p in parks.values() if p.get('a')), 'nonum': len(nonum), 'padus': len(recs), 'read': seen}
    out = {'updated': time.strftime('%Y-%m-%d'), 'st': st, 'note': 'Built by .github/scripts/kpc_us_key.py from USGS PAD-US (fed + state fee land) and POTA. m = joined (same name + same kind), c = check by hand (NOT joined).',
           'counts': counts, 'parks': parks, 'nonum': nonum[:300]}
    # plain-words review page for this state (GitHub shows .md files nicely)
    R = OUT / 'review'; R.mkdir(exist_ok=True)
    L = [f'# {st}: POTA parks vs official land (USGS PAD-US)', '', f"Built {out_date()} by `.github/scripts/kpc_us_key.py`. **{counts['matched']} of {counts['parks']}** parks joined to official land "
         f"(same name + same kind of place). **{counts['check']}** to check by hand, **{counts['none']}** with nothing found. Nothing below is joined until a person checks it.", '']
    chk = [(r, p) for r, p in parks.items() if not p['m'] and p['c']]
    L += ['## To check (not joined)', ''] + [f"- **{r}** {p['n']} ({p['t']}) → " + '; '.join(f"{x[1]} (~{x[2]:,} ac, {x[3]})" for x in p['c']) for r, p in chk] + ['']
    L += ['## Sites on bigger public land (no outline of their own; the land around the pin)', ''] + [f"- {r} {p['n']} ({p['t']}) → on " + '; '.join(f"{x[1]} (~{x[2]:,} ac)" for x in p['a']) for r, p in parks.items() if p.get('a')] + ['']
    L += ['## Nothing found in PAD-US', ''] + [f"- {r} {p['n']} ({p['t']})" for r, p in parks.items() if not p['m'] and not p['c'] and not p.get('a')] + ['']
    L += ['## Biggest federal / state places with no POTA park joined (first 60)', ''] + [f"- {x[1]} · {x[2]} · {x[3]} · ~{x[4]:,} ac" for x in nonum[:60]]
    (R / f'US-{st}.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    (OUT / f'US-{st}.json').write_text(json.dumps(out, separators=(',', ':'), ensure_ascii=False), encoding='utf-8')
    return counts


idx = {}
try: idx = json.load(open(OUT / 'index.json')).get('states', {})
except Exception: pass  # noqa: BLE001
done = []
for st in STATES:
    if st == 'KY': continue
    if time.time() - T0 > LIMIT: notice('US key', f'stopped for time before {st}; run again for the rest'); break
    try:
        c = run(st)
    except Exception as e:  # noqa: BLE001
        notice(f'US key {st}', f'FAILED: {e}'); continue
    if c:
        idx[st] = c; done.append(st)
        print(f"{st}: {c['parks']} parks, {c['matched']} joined, {c['check']} to check, {c['none']} nothing found, {c['nonum']} places with no POTA park", flush=True)
    json.dump({'updated': time.strftime('%Y-%m-%d'), 'states': idx}, open(OUT / 'index.json', 'w'), separators=(',', ':'))
tot = {k: sum(v.get(k, 0) for v in idx.values()) for k in ('parks', 'matched', 'check', 'none', 'site')}
notice('US key extra maps', ', '.join(f'{k}: {v}' for k, v in XCOUNT.items()))
notice('US answer key', f"{len(done)} states this run ({' '.join(done)}). All states so far: {tot['parks']} parks, {tot['matched']} joined, {tot['check']} to check, {tot['site']} sites on bigger land, {tot['none']} nothing found")
