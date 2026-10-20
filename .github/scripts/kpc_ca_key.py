"""CANADA boundary ANSWER KEY (Brandon Oct 18 2026: 'set one up to start pulling the Canada data'). Same method as kpc_us_key.py:
pull every area in CPCAD (Canadian Protected and Conserved Areas Database, Environment and Climate Change Canada, Open Government
Licence - Canada) with a coarse outline, then join to the CA- POTA parks (data/parkinfo/CA.json) ONLY when the name matches (English
or French, generic words and accents dropped) AND it is the same kind of place, near the park's pin. EVERY piece with that name joins.
Unsure = 'c' check list with the reason, never joined. Provincial layers (Québec, Ontario…) come in a later step.
Writes data/ca-key/CA-XX.json per province/territory, data/ca-key/index.json, review pages data/ca-key/review/CA-XX.md."""
import json, os, re, time, unicodedata, urllib.parse, urllib.request, pathlib

SVC = 'https://maps-cartes.ec.gc.ca/arcgis/rest/services/CWS_SCF/CPCAD/MapServer'
OUT = pathlib.Path('data/ca-key'); OUT.mkdir(parents=True, exist_ok=True)
UA = 'KPC (kentuckyportableclub.github.io)'


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


def variants(s):
    # Oct 18 review: plurals ('Munroes' = 'Munroe'), 'and' between two names, a leading Ile/Isle ('Ile d'Anticosti' = 'Anticosti')
    v = {norm(s)} | {norm(x) for x in re.split(r'\s*/\s*', str(s or '')) if len(x.strip()) > 3}   # 'Indigenous name / English name'
    v |= {_sing(x) for x in v} | {re.sub(r'\b(and|et)\b', ' ', x) for x in v}
    v |= {re.sub(r'^(iles?|isles?|islands?) ', '', x) for x in v}
    return {re.sub(r'\s+', ' ', x).strip() for x in v if x.strip()}


def _pre(a, b):
    if a == b: return True
    sh, lo = (a, b) if len(a) < len(b) else (b, a)
    return len(sh) > 5 and lo.startswith(sh) and lo[len(sh):len(sh) + 1] == ' ' and len(sh) / len(lo) >= 0.6


def same_name(a, b, exact=False):
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
def near(la, lo, b, pad): return b and b[0] - pad <= lo <= b[2] + pad and b[1] - pad <= la <= b[3] + pad


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
recs, off = [], 0
while True:
    j = get(f'{SVC}/{lid}/query', {'where': '1=1', 'outFields': ','.join(v for v in F.values() if v), 'returnGeometry': 'true', 'outSR': 4326,
                                   'maxAllowableOffset': 0.02, 'geometryPrecision': 3, 'f': 'json', 'resultOffset': off, 'resultRecordCount': min(mx, 1000),
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
        except Exception as e: notice('Canada extra', f'{label} {lu}: {e}'); continue  # noqa: BLE001
        if 'Polygon' not in str(li.get('geometryType', '')): continue
        fl = [f['name'] for f in li.get('fields', [])]
        names = [n for n in (nf or []) if n in fl] or [f for f in fl if NAMEY.search(f) and not re.search(r'(file|url|link|code|id$)', f, re.I)][:3]
        oidf = li.get('objectIdField') or 'OBJECTID'; mx = int(li.get('maxRecordCount') or 1000); off = 0
        while True:
            try:
                j = get(f'{lu}/query', {'where': '1=1', 'outFields': ','.join([oidf] + names), 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': 0.02,
                                        'geometryPrecision': 3, 'f': 'json', 'resultOffset': off, 'resultRecordCount': min(mx, 1000), 'orderByFields': oidf}, tries=3)
            except Exception as e: notice('Canada extra', f'{label}: {e}'); break  # noqa: BLE001
            fs = j.get('features', [])
            for f in fs:
                a = f.get('attributes') or {}; g = f.get('geometry') or {}
                nm = next((str(a[n]) for n in names if a.get(n)), '')
                if not nm: continue
                r = {'oid': f'{label[:12]}:{a.get(oidf)}', 'n': nm, 'nf': '', 'ty': label, 'ow': '', 'mg': '', 'ha': 0, '_g': g, '_bb': bbox(g), 'src': label}
                r['_k'] = kinds(nm) | next((k for h, k in HINT if h.lower() in label.lower()), set())
                got.append(r)
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
# Oct 20: Nova Scotia's own Crown land + provincial parks map (nsgiwa.novascotia.ca): take every layer whose name says park / protected / reserve
try:
    _ns = 'https://nsgiwa.novascotia.ca/arcgis/rest/services/PLAN/PLANCrownLandsWM84V1/MapServer'
    _nl = [l for l in (get(_ns, {'f': 'json'}).get('layers') or []) if re.search(r'park|protected|wilderness|reserve|beach|heritage', l.get('name', ''), re.I) and not l.get('subLayerIds')]
    notice('Canada more layers', 'Nova Scotia layers: ' + ', '.join(f"{l['id']}:{l['name']}" for l in _nl))
    MORE += [(f"Nova Scotia {l['name']} (Province of Nova Scotia)", f"{_ns}/{l['id']}", None) for l in _nl]
except Exception as ex: notice('Canada more layers', f'Nova Scotia list FAILED: {ex}')  # noqa: BLE001
for e in MORE:
    try: g = arc_pull(e[0], e[1], e[2]); recs += g; extra += len(g); notice('Canada more layers', f'{e[0]}: {len(g)}')
    except Exception as ex: notice('Canada more layers', f'{e[0]} FAILED: {ex}')  # noqa: BLE001
notice('Canada extra layers', f'{extra} areas from the provincial + Parks Canada maps')
PRIV = re.compile(r'private|privately|stewardship|ncc \d|nature conservancy', re.I)


def acres(r): return round((r['ha'] or 0) * 2.47105)


# Oct 18 review: sites (lighthouse, bridge, trail, campground…) have no outline of their own; reviewed parks in data/ca-key/overrides.json
SITE = re.compile(r'lighthouse|phare|bridge|pont|trail|sentier|campground|camping|day use|boat launch|wharf|quai|canal|hotel|station|building|house|maison|church|eglise|fort |monument|recreation site', re.I)
def _nf(t):   # hand decisions match names whatever way the accents are stored (Oct 18: SG̲áan K̲ínghlas-Bowie never matched)
    import unicodedata; return unicodedata.normalize('NFC', str(t or '')).strip().casefold()
try: OVR = json.load(open(OUT / 'overrides.json')).get('parks', {})
except Exception: OVR = {}  # noqa: BLE001
P = json.load(open('data/parkinfo/CA.json'))['parks']
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
        kp = kinds(name) | kinds(typ)
        m, c = [], []
        for r in recs:
            if la is not None and not near(la, lo, r['_bb'], .6): continue
            if la is None and not in_pv(r['_bb']): continue              # no pin: stay inside this province's area
            if PRIV.search(r['n'] + ' ' + str(r['ow'])): continue      # private stewardship land is never joined (only listed to check)
            ex = bool(kp) != bool(r['_k'])      # only one name says what kind of place it is: the names must match exactly
            if ex and la is not None and not near(la, lo, r['_bb'], .1): continue   # and be close by (many lakes share a name)
            if (same_name(name, r['n'], ex) or (r['nf'] and same_name(name, r['nf'], ex))) and same_kind(kp, r['_k']):
                m.append([r['oid'], r['n'] or r['nf'], acres(r), 'name' if not r.get('src') else 'name · ' + r['src']])
        ov = OVR.get(ref) or {}
        if ov:
            no = {str(q) for q in ov.get('no', [])}
            m = [q for q in m if str(q[0]) not in no and _nf(q[1]) not in {_nf(x) for x in no}]
            for want in ov.get('join', []):
                for r in recs:
                    if (str(r['oid']) == str(want) or _nf(r['n']) == _nf(want) or _nf(r['nf']) == _nf(want)) and (la is None or near(la, lo, r['_bb'], .6)) and not any(str(q[0]) == str(r['oid']) for q in m):
                        m.append([r['oid'], r['n'] or r['nf'], acres(r), 'reviewed'])
        site = []
        if not m and la is not None:
            for r in recs:
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
            if c and (SITE.search(name + ' ' + typ) or ov.get('site')) and all(q[3].startswith('the POTA pin is inside') for q in c):
                site = sorted((q for q in c if not re.search(r'buffer zone|closure|\bsfa\b|marine refuge|fishing area|fishery', q[1], re.I)), key=lambda q: q[2])[:2]; c = []
        used.update(q[0] for q in m)
        parks[ref] = {'n': name, 't': typ, 'm': sorted(m, key=lambda q: -q[2]), 'c': c}
        if site: parks[ref]['a'] = site
    cnt = {'parks': len(parks), 'matched': sum(1 for p in parks.values() if p['m']), 'check': sum(1 for p in parks.values() if not p['m'] and p['c']),
           'none': sum(1 for p in parks.values() if not p['m'] and not p['c'] and not p.get('a')), 'site': sum(1 for p in parks.values() if p.get('a'))}
    out = {'updated': time.strftime('%Y-%m-%d'), 'prov': pv, 'source': 'CPCAD (Environment and Climate Change Canada) + provincial and Parks Canada maps, Open Government Licence',
           'note': 'm = joined (same name + same kind), c = check by hand (NOT joined).', 'counts': cnt, 'parks': parks}
    (OUT / f'CA-{pv}.json').write_text(json.dumps(out, separators=(',', ':'), ensure_ascii=False), encoding='utf-8')
    R = OUT / 'review'; R.mkdir(exist_ok=True)
    L = [f'# Canada {pv}: POTA parks vs official land (CPCAD)', '', f"Built {time.strftime('%Y-%m-%d')} by `.github/scripts/kpc_ca_key.py`. **{cnt['matched']} of {cnt['parks']}** joined (same name + same kind). "
         f"**{cnt['check']}** to check, **{cnt['none']}** nothing found in CPCAD (provincial maps come next). Nothing below is joined.", '', '## To check (not joined)', '']
    L += [f"- **{r}** {p['n']} ({p['t']}) → " + '; '.join(f"{q[1]} (~{q[2]:,} ac, {q[3]})" for q in p['c']) for r, p in parks.items() if not p['m'] and p['c']]
    L += ['', '## Sites on bigger land (no outline of their own; the land around the pin)', ''] + [f"- {r} {p['n']} ({p['t']}) → on " + '; '.join(f"{q[1]} (~{q[2]:,} ac)" for q in p['a']) for r, p in parks.items() if p.get('a')]
    L += ['', '## Nothing found in CPCAD', ''] + [f"- {r} {p['n']} ({p['t']})" for r, p in parks.items() if not p['m'] and not p['c'] and not p.get('a')]
    (R / f'CA-{pv}.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    idx[pv] = cnt
    print(f"{pv}: {cnt['parks']} parks, {cnt['matched']} joined, {cnt['check']} check, {cnt['none']} none", flush=True)
json.dump({'updated': time.strftime('%Y-%m-%d'), 'provinces': idx}, open(OUT / 'index.json', 'w'), separators=(',', ':'))
t = {k: sum(v.get(k, 0) for v in idx.values()) for k in ('parks', 'matched', 'check', 'none', 'site')}
notice('Canada answer key', f"{t['parks']} parks: {t['matched']} joined, {t['check']} to check, {t['site']} sites on bigger land, {t['none']} nothing found · " + ' '.join(f"{k} {v['matched']}/{v['parks']}" for k, v in sorted(idx.items())))
