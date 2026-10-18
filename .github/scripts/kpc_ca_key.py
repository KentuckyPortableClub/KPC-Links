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


GEN = (r"national historic site of canada|national historic site|lieu historique national du canada|lieu historique national|historic site|lieu historique|"
       r"national wildlife area|reserve nationale de faune|migratory bird sanctuary|refuge d oiseaux migrateurs|bird sanctuary|wildlife management area|"
       r"wildlife refuge|wildlife area|reserve faunique|refuge faunique|national park reserve|national park of canada|parc national du canada|national park|parc national|"
       r"national marine conservation area|marine park|provincial park|parc provincial|territorial park|parc territorial|regional park|parc regional|"
       r"provincial recreation area|recreation area|recreation site|recreation park|conservation reserve|conservation area|aire de conservation|"
       r"ecological reserve|reserve ecologique|nature reserve|reserve naturelle|natural area|protected natural area|protected area|aire protegee|"
       r"wilderness area|wilderness park|heritage rivers?|heritage area|heritage site|biosphere reserve|reserve de la biosphere|provincial forest|"
       r"provincial|national|park|parc|reserve|area|site|de la|des|du|de|la|le|les|the|of|and|et")
ABBR = {'st': 'saint', 'ste': 'sainte', 'mt': 'mount', 'pt': 'point', 'lk': 'lake', 'cr': 'creek', 'is': 'island', 'isl': 'island'}


def norm(s):
    s = flat(s).replace('&', ' and ')
    s = re.sub(r'\(.*?\)', ' ', s)
    s = re.sub(r"[’'`.]", '', s)
    s = re.sub(r'[-/]', ' ', s)
    s = ' '.join(ABBR.get(w, w) for w in re.sub(r'[^a-z0-9 ]', ' ', s).split())
    s = re.sub(r'\b(' + GEN + r')\b', ' ', s)
    s = re.sub(r'\b(d|l)\b', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


KINDS = [('pp', r'provincial park|parc provincial|territorial park|parc territorial|parc national(?! du canada)'),
         ('np', r'national park|parc national du canada|national park reserve|parc national(?! [a-z])'),
         ('hist', r'historic|historique|heritage site'),
         ('wma', r'wildlife|faune|faunique|bird sanctuary|oiseaux migrateurs|game'),
         ('ca', r'conservation (area|reserve)|aire de conservation'),
         ('eco', r'ecological reserve|reserve ecologique|nature reserve|reserve naturelle|natural area|protected natural area|nature preserve'),
         ('rec', r'recreation|loisirs'), ('rp', r'regional park|parc regional'), ('mp', r'marine park|marine conservation'),
         ('wild', r'wilderness'), ('pf', r'provincial forest|foret')]
def kinds(s):
    s = flat(s); return {k for k, r in KINDS if re.search(r, s)}


def same_name(a, b):
    a, b = norm(a), norm(b)
    if not a or not b: return False
    if a == b: return True
    sh, lo = (a, b) if len(a) < len(b) else (b, a)
    return len(sh) > 5 and lo.startswith(sh) and len(sh) / len(lo) >= 0.6


def same_kind(ka, kb): return not ka or not kb or bool(ka & kb)
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


def acres(r): return round((r['ha'] or 0) * 2.47105)


P = json.load(open('data/parkinfo/CA.json'))['parks']
by = {}
for ref, x in P.items(): by.setdefault((x[10] if len(x) > 10 else '') or 'XX', {})[ref] = x
idx = {}
for pv, parks_in in sorted(by.items()):
    parks, used = {}, set()
    for ref, x in sorted(parks_in.items()):
        name, typ, la, lo = x[0], x[2], x[5], x[6]
        kp = kinds(name) | kinds(typ)
        m, c = [], []
        for r in recs:
            if la is not None and not near(la, lo, r['_bb'], .6): continue
            if (same_name(name, r['n']) or (r['nf'] and same_name(name, r['nf']))) and same_kind(kp, r['_k']):
                m.append([r['oid'], r['n'] or r['nf'], acres(r), 'name'])
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
        used.update(q[0] for q in m)
        parks[ref] = {'n': name, 't': typ, 'm': sorted(m, key=lambda q: -q[2]), 'c': c}
    cnt = {'parks': len(parks), 'matched': sum(1 for p in parks.values() if p['m']), 'check': sum(1 for p in parks.values() if not p['m'] and p['c']),
           'none': sum(1 for p in parks.values() if not p['m'] and not p['c'])}
    out = {'updated': time.strftime('%Y-%m-%d'), 'prov': pv, 'source': 'CPCAD (Environment and Climate Change Canada), Open Government Licence - Canada',
           'note': 'm = joined (same name + same kind), c = check by hand (NOT joined).', 'counts': cnt, 'parks': parks}
    (OUT / f'CA-{pv}.json').write_text(json.dumps(out, separators=(',', ':'), ensure_ascii=False), encoding='utf-8')
    R = OUT / 'review'; R.mkdir(exist_ok=True)
    L = [f'# Canada {pv}: POTA parks vs official land (CPCAD)', '', f"Built {time.strftime('%Y-%m-%d')} by `.github/scripts/kpc_ca_key.py`. **{cnt['matched']} of {cnt['parks']}** joined (same name + same kind). "
         f"**{cnt['check']}** to check, **{cnt['none']}** nothing found in CPCAD (provincial maps come next). Nothing below is joined.", '', '## To check (not joined)', '']
    L += [f"- **{r}** {p['n']} ({p['t']}) → " + '; '.join(f"{q[1]} (~{q[2]:,} ac, {q[3]})" for q in p['c']) for r, p in parks.items() if not p['m'] and p['c']]
    L += ['', '## Nothing found in CPCAD', ''] + [f"- {r} {p['n']} ({p['t']})" for r, p in parks.items() if not p['m'] and not p['c']]
    (R / f'CA-{pv}.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    idx[pv] = cnt
    print(f"{pv}: {cnt['parks']} parks, {cnt['matched']} joined, {cnt['check']} check, {cnt['none']} none", flush=True)
json.dump({'updated': time.strftime('%Y-%m-%d'), 'provinces': idx}, open(OUT / 'index.json', 'w'), separators=(',', ':'))
t = {k: sum(v[k] for v in idx.values()) for k in ('parks', 'matched', 'check', 'none')}
notice('Canada answer key', f"{t['parks']} parks: {t['matched']} joined, {t['check']} to check, {t['none']} nothing found · " + ' '.join(f"{k} {v['matched']}/{v['parks']}" for k, v in sorted(idx.items())))
