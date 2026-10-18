"""KPC state + recreation trails that are POTA parks (Brandon Oct 16: 'give me 12 states trails ... where they need to be').
For each state in STATES, every POTA park in data/parkinfo/US-XX.json whose POTA type is a trail (State Trail,
National Recreation Trail ...) or a State Park whose name says Trail (rail-trail parks like Katy Trail). National
Scenic / Historic Trails are left out (kpc_us_trails.py draws those from the NPS).
Line sources, best first:
  1. US Forest Service trails (EDW TrailNFS_Publish) by trail name, for National Recreation Trails on forest land
  1b. (Oct 18) official agency layers: NPS Public Trails, then ArcGIS Online services found by the trail's name / '<State> trails'
      that were published by that STATE's agency or a federal agency (org name checked; county/city/club layers don't count)
  2. OpenStreetMap route relations (Overpass) with the trail's name inside the state; labelled NOT OFFICIAL
Each line must pass near the POTA pin (CHECK_KM) or it is not used: wrong-place matches are worse than none.
Writes data/trails/<REF>.json (same format as the national trails) + data/trails/index-state.json
[{ref,name,kind ST|NRT|TP,bbox,by,official,km}] and data/trails/state-report.json (found / missing, for KPC)."""
import json, os, re, time, math, urllib.request, urllib.parse, datetime
STATES = (os.environ.get('STATES') or 'TN IN OH WV VA MO IL NC GA AL MI PA').split()
OUT = 'data/trails'; os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'KPC trails (kentuckyportableclub.github.io)'}
CHECK_KM = 8.0   # the drawn line must come this close to the POTA pin
CHECK_KM_TRAIL = 35.0  # Oct 18: a real trail (not a park named 'Trail') may have its POTA pin at one end, away from the mapped line
# Oct 18 (finishing the US): other names the maps use for these POTA trail parks
ALIAS = {'US-3627': ['Van Fleet'], 'US-9909': ['Little Stony'], 'US-9922': ["Lion's Tale", 'Lions Tale'], 'US-9923': ['Virginia Creeper'],
         'US-9753': ['Rock Island Spur', 'Rock Island Trail'], 'US-9380': ['Mill Towns'], 'US-9385': ['Gateway'], 'US-9390': ['Willard Munger', 'Munger'],
         'US-11014': ['Taconite'], 'US-13595': ['Northern Rail Trail', 'Northern Rail'], 'US-10506': ['Cazadero'], 'US-2216': ['Makapuu Point Lighthouse', 'Makapuu'],
         'US-10918': ['Waahila Ridge', 'Waahila'], 'US-5788': ['Slickrock'], 'US-5872': ['Burr Trail', 'Burr'], 'US-5809': ['Little Red Mountain'], 'US-11001': ['Gooseberry Mesa'],
         'US-10757': ['Sterling Mine Ditch'], 'US-8618': ['White Ridge'], 'US-13195': ['Jumbo Grade'], 'US-8313': ['Mountains to Sea'], 'US-9933': ['Beaches to Bluegrass']}
# Oct 18: POTA trail parks that are NOT a line to draw (driving routes, areas, water trails, ordinary parks named 'Trail'): listed under 'noline'
NOLINE = re.compile(r'Byway|Scenic Highway|Heritage|Geologic|Bird & Wildlife|Mining|Civil War Trail|Southwest Trail|Butterfield State|Saracen|West-Northwest|True Grit|Camden Expedition|Water State Trail|Water Trail|Coastal State Trail|Na Ala Hele', re.I)
NOLINE_PARK = {'US-1002', 'US-1007', 'US-4098', 'US-3222', 'US-2152'}
MATCH_KM = 60.0  # pieces with the right name are collected from this far around the pin (long trails come in sections)
# parks named 'Trail' that are NOT trails (a line there would mislead): Scioto Trail SP is a forest park
SKIP = {'US-1990'}
def note(t, m): print(f'::notice title={t}::' + str(m).replace('\n', ' ')[:900])
def get(u, data=None, t=120):
    err = None
    for i in range(3):
        try:
            r = urllib.request.Request(u, data=data, headers=UA)
            with urllib.request.urlopen(r, timeout=t) as f: return json.loads(f.read().decode('utf-8', 'replace'))
        except Exception as e: err = e; time.sleep(4 + 6 * i)
    raise err
def km(a, b, c, d):
    r = math.radians; return 6371 * 2 * math.asin(math.sqrt(math.sin(r(c - a) / 2) ** 2 + math.cos(r(a)) * math.cos(r(c)) * math.sin(r(d - b) / 2) ** 2))
def seglen(line): return sum(km(line[i][1], line[i][0], line[i + 1][1], line[i + 1][0]) for i in range(len(line) - 1))
def dp(pts, eps):
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]; dx, dy = b[0] - a[0], b[1] - a[1]; n = (dx * dx + dy * dy) ** .5 or 1e-12
    i, dm = 0, 0
    for k in range(1, len(pts) - 1):
        d = abs(dy * pts[k][0] - dx * pts[k][1] + b[0] * a[1] - b[1] * a[0]) / n
        if d > dm: i, dm = k, d
    if dm > eps: return dp(pts[:i + 1], eps)[:-1] + dp(pts[i:], eps)
    return [a, b]
GEN = r'\b(state|national|recreation|trail|trails|park|scenic|historic|rail|the|and|of)\b'
import unicodedata
def core(n):  # Oct 18: Hawaiian okina / accents dropped ('Makapuʻu' = 'makapuu')
    n = unicodedata.normalize('NFD', str(n)).replace('ʻ', '').replace('‘', '').replace('’', '').replace("'", '')
    n = ''.join(c for c in n if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(GEN, ' ', n.lower())).strip()
def kind(t, n):
    if 'National Recreation Trail' in t: return 'NRT'
    if 'Trail' in t: return 'ST'
    return 'TP'
# ---------------------------------------------------------------- 1. Forest Service
FS = 'https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_TrailNFSPublish_01/MapServer/0'
FSF = None
def forest(name, la, lo):
    global FSF
    try:
        if FSF is None:
            FSF = [f['name'] for f in get(FS + '?f=json').get('fields', [])]
        nf = next((f for f in FSF if f.upper() == 'TRAIL_NAME'), None)
        if not nf: return None
        w = core(name).upper().split()
        if not w: return None
        q = {'where': f"{nf} LIKE '%{'%'.join(w)}%'", 'geometry': f'{lo-.6},{la-.6},{lo+.6},{la+.6}', 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326,
             'spatialRel': 'esriSpatialRelIntersects', 'outFields': nf, 'returnGeometry': 'true', 'outSR': 4326, 'f': 'json'}
        j = get(FS + '/query?' + urllib.parse.urlencode(q))
        lines = [[[round(x, 5), round(y, 5)] for x, y in p] for f in j.get('features', []) for p in (f.get('geometry') or {}).get('paths', [])]
        return lines or None
    except Exception as e:
        note('Forest Service', f'{name}: {str(e)[:120]}'); return None
# ---------------------------------------------------------------- 2. official agency layers (Oct 18, Brandon: 'look state first etc then unofficial last')
STN = {'AL':'Alabama','AR':'Arkansas','AZ':'Arizona','CA':'California','CO':'Colorado','CT':'Connecticut','DE':'Delaware','FL':'Florida','GA':'Georgia','IA':'Iowa','ID':'Idaho','IL':'Illinois',
       'IN':'Indiana','KS':'Kansas','KY':'Kentucky','LA':'Louisiana','MA':'Massachusetts','MD':'Maryland','ME':'Maine','MI':'Michigan','MN':'Minnesota','MO':'Missouri','MS':'Mississippi','MT':'Montana',
       'NC':'North Carolina','ND':'North Dakota','NE':'Nebraska','NH':'New Hampshire','NJ':'New Jersey','NM':'New Mexico','NV':'Nevada','NY':'New York','OH':'Ohio','OK':'Oklahoma','OR':'Oregon',
       'PA':'Pennsylvania','RI':'Rhode Island','SC':'South Carolina','SD':'South Dakota','TN':'Tennessee','TX':'Texas','UT':'Utah','VA':'Virginia','VT':'Vermont','WA':'Washington','WI':'Wisconsin',
       'WV':'West Virginia','WY':'Wyoming','AK':'Alaska','HI':'Hawaii','DC':'District of Columbia'}
FED = r'forest service|usda|national park service|\bnps\b|fish (and|&) wildlife|bureau of land|army corps|federal highway|department of the interior'
AGW = r'department|dept|division|office|commission|conservation|natural resources|\bdnr\b|\bdcr\b|parks|forestry|transportation|\bdot\b|wildlife|environment|gis|geographic|state of|commonwealth'
ORG = {}
STS = {}
NAMES = {}
ALOG = []  # Oct 18: what the agency search looked at (written to state-report.json 'agency')
def org_name(oid):
    if oid not in ORG:
        try: ORG[oid] = (get(f'https://www.arcgis.com/sharing/rest/portals/{oid}?f=json', t=40) or {}).get('name', '') or ''
        except Exception: ORG[oid] = ''
    return ORG[oid]
ABBR = {'MO': r'modnr|\bmdc\b|_mdc_|modot|mostateparks|mo_?dnr', 'TN': r'tdec|tdot|tnstateparks|tn_?state', 'VA': r'vdcr|\bdcr\b|vdot|vdof|vadcr|virginiadcr',
        'WV': r'wvdnr|wvdep|wvgis|wv_?gis|wvstateparks|wvdot', 'IL': r'\bidnr|il_?dnr|ildnr|idot', 'IN': r'indnr|in_?dnr|indot', 'OH': r'odnr|odot|ohiodnr',
        'NC': r'ncdnr|ncdpr|ncparks|ncdot|ncdeq', 'GA': r'gadnr|gdot|ga_?dnr', 'AL': r'aldcnr|adcnr|aldot', 'MI': r'midnr|mi_?dnr|mdot', 'PA': r'padcnr|dcnr|penndot',
        'MS': r'mdwfp|msdot', 'AR': r'arkansasstateparks|ardot|agfc', 'MD': r'mddnr|md_?dnr|mdot', 'WI': r'widnr|wi_?dnr|wisdot', 'MN': r'mndnr|mn_?dnr|mndot', 'IA': r'iadnr|iowadnr|iowadot'}
FEDO = r'\bnps\b|nps_|_nps|usfs|usda_?fs|\bfws\b|usfws|\bblm\b|usace'
def official_org(org, st):
    o = org.lower()
    if re.search(ABBR.get(st, r'^$'), o) or re.search(FEDO, o): return True
    if re.search(FED, o): return True
    sn = STN.get(st, '').lower()
    if re.search(r'\b(county|city|town|village|township|university|college|club|association|alliance|friends|conservancy|council)\b', o): return False
    return bool(sn) and bool(re.search(r'(?<!west )\b' + re.escape(sn) + r'\b', o)) and bool(re.search(AGW, o))
NPS_TRAILS = 'https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Public_Trails/FeatureServer/0'
def lyr_lines(url, where, la, lo, d=1.0, fld=None, want=''):
    out, off = [], 0
    NAMES.clear()
    nowater = not re.search(r'water ?trail|canoe|paddl|blueway', want or '', re.I)  # 'Elk River Trail' is a LAND trail
    for _ in range(6):
        q = {'where': where, 'geometry': f'{lo-d},{la-d},{lo+d},{la+d}', 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
             'outFields': '*' if fld else '', 'returnGeometry': 'true', 'outSR': 4326, 'f': 'json', 'resultOffset': off, 'resultRecordCount': 1000}
        j = get(url + '/query?' + urllib.parse.urlencode(q), t=90)
        if 'error' in j: raise Exception(str(j['error'])[:150])
        fs = j.get('features', [])
        for f in fs:  # Oct 18: 'Greenbrier River Trail' must not pick up the 'Greenbrier River Water Trail' (the river itself)
            A = f.get('attributes') or {}; nm = str(A.get(fld, '') if fld else '')
            # WV-style layers mark the river line with surface = Water (named just like the rail-trail)
            if nowater and any(re.search(r'surf|type|use|class', str(k), re.I) and str(v).strip().lower() in ('water', 'water trail', 'paddle', 'blueway') for k, v in A.items()): continue
            if nowater and re.search(r'water ?trail|blueway|paddl|canoe', nm, re.I) and not re.search(r'water ?trail|blueway', want or '', re.I): continue
            # a land trail's piece must be named like a trail (the river 'Greenbrier River' is not the 'Greenbrier River Trail')
            if nowater and nm and re.search(r'\btrail\b', want or '', re.I) and not re.search(r'trail|path|greenway|rail|bikeway|route|\btr\b', nm, re.I): continue
            ps = [[[round(x, 5), round(y, 5)] for x, y in p[:]] for p in (f.get('geometry') or {}).get('paths', [])]
            out += ps; NAMES.setdefault(nm, [0, '']); NAMES[nm][0] += sum(seglen(p) for p in ps)
            if not NAMES[nm][1]: NAMES[nm][1] = ' '.join(f'{k}={v}' for k, v in (f.get('attributes') or {}).items() if isinstance(v, str) and v and k != fld)[:160]
        if not j.get('exceededTransferLimit') or not fs: break
        off += len(fs)
    return out
def likes(fld, w):
    """PAD-US style firewalls hate long wheres: one LIKE, words joined by %, tried as Title Case and UPPER."""
    return [f"{fld} LIKE '%{'%'.join(x.title() for x in w)}%'", f"{fld} LIKE '%{'%'.join(x.upper() for x in w)}%'"]
def agency(name, st, la, lo, lim=None):
    lim = lim or CHECK_KM
    """ArcGIS Online search for the trail's name; only services published by a STATE agency of that state or a federal
    agency count; then a polyline layer in it with a name field LIKE the trail, near the pin. Returns (lines, by) or (None, '')."""
    w = words(name)
    if not w: return None, ''
    tries = [(NPS_TRAILS, 'National Park Service', ['TRLNAME', 'TRLALTNAME'])]
    try:
        qq = f'"{name}" (type:"Feature Service" OR type:"Map Service")'
        sr = get('https://www.arcgis.com/sharing/rest/search?' + urllib.parse.urlencode({'q': qq, 'f': 'json', 'num': 25}), t=60)
        res = sr.get('results', [])
        if st not in STS:
            STS[st] = get('https://www.arcgis.com/sharing/rest/search?' + urllib.parse.urlencode({'q': f'{STN.get(st, st)} trails (type:"Feature Service" OR type:"Map Service")', 'f': 'json', 'num': 40}), t=60).get('results', [])
        res += STS[st]
        # Oct 18 (Brandon: 'go for it'): scenic byways come from the national / state byway maps, BLM trails from BLM's own maps
        for key, q in (('byway', 'scenic byways'), ('blm', 'BLM trails routes'), ('blm', 'Bureau of Land Management trails')):
            if key in name.lower():
                if q not in STS: STS[q] = get('https://www.arcgis.com/sharing/rest/search?' + urllib.parse.urlencode({'q': q + ' (type:"Feature Service" OR type:"Map Service")', 'f': 'json', 'num': 40}), t=60).get('results', [])
                res += STS[q]
    except Exception as e: note('ArcGIS search', f'{name}: {str(e)[:120]}'); res = []
    seen = set()
    for it in res:
        u = (it.get('url') or '').rstrip('/')
        if not u or u in seen or not re.search(r'/(Feature|Map)Server(/\d+)?$', u): continue
        seen.add(u)
        org = ((org_name(it.get('orgId', '')) if it.get('orgId') else '') + ' | ' + (it.get('accessInformation') or '') + ' | ' + (it.get('owner') or '')).strip(' |')
        if not official_org(org, st): ALOG.append([name, 'skip (not state/federal)', org[:60], it.get('title', '')[:60]]); continue
        tries.append((u, org, None))
    for u, org, flds in tries[:22]:
        try:
            lays = [u] if re.search(r'/\d+$', u) else [f"{u}/{l['id']}" for l in (get(u + '?f=json', t=40).get('layers') or [])[:8]]
            for lu in lays:
                meta = get(lu + '?f=json', t=40)
                if meta.get('geometryType') != 'esriGeometryPolyline': continue
                F = [x['name'] for x in meta.get('fields', []) if x.get('type') == 'esriFieldTypeString' and (flds is None and re.search(r'name|trail|trl|label|title', x['name'], re.I) or flds and x['name'] in flds)]
                for fld in F[:4]:
                    for wh in likes(fld, w):
                        try: L = lyr_lines(lu, wh, la, lo, fld=fld, want=name)
                        except Exception: continue
                        # Oct 18: long trails run past the ±1° search box (Empire State Trail: 750 miles) → ask again with a statewide box
                        if L and any(abs(p[0] - lo) > 0.95 or abs(p[1] - la) > 0.95 for l in L for p in l):
                            try: L = lyr_lines(lu, wh, la, lo, d=7.0, fld=fld, want=name) or L
                            except Exception: pass
                        if L:
                            nk = min(km(la, lo, p[1], p[0]) for l in L for p in l)
                            ALOG.append([name, f'{len(L)} lines {nk:.0f} km from pin', org[:60], lu[-90:] + ' ' + fld, {k: [round(v[0]), v[1]] for k, v in list(NAMES.items())[:8]}])
                            if nk <= lim: return L, org
        except Exception as e:
            ALOG.append([name, 'error ' + str(e)[:80], org[:60], u[-90:]])
    return None, ''
# ---------------------------------------------------------------- 3. OpenStreetMap
OVP = 'https://overpass-api.de/api/interpreter'
def words(name):  # Oct 17: letters/numbers only, so "Alene's", "Ka‘ena" and "Estacada- Boring" still match OpenStreetMap
    # Oct 18: POTA's type words ('BLM', 'Byway', 'Geologic'...) are not in the map names ('Burr Trail BLM Historic Trail' = 'Burr Trail')
    return [x for x in re.split(r'[^0-9a-z]+', core(name)) if len(x) > 2 and x not in ('blm', 'byway', 'byways', 'geologic', 'wayside', 'state', 'water')]
def osm(name, iso, la, lo):
    """Oct 17 (Brandon: 'readdress the missing trails'): route relations of any kind (foot, bike, horse, canoe for water
    trails, road for scenic byways) AND plain named paths/cycleways/tracks (many rail-trails are just ways); every match
    within MATCH_KM of the POTA pin is kept (trails come in sections), not just the longest one anywhere in the state."""
    w = words(name)
    if not w: return None, ''
    rx = '.*'.join(re.escape(x) for x in w)
    road = re.search(r'byway|highway|scenic drive|blm historic', name, re.I)
    water = re.search(r'water|river|canoe|paddl', name, re.I)
    rt = 'hiking|foot|bicycle|mtb|horse|inline_skates|running|canoe|boat' + ('|road' if road else '')
    hw = '' if road else f'way["highway"~"path|cycleway|footway|track|bridleway"]["name"~"{rx}",i](area.a);'
    wt = f'way["waterway"~"river|stream|canal"]["name"~"{rx}",i](area.a);' if water else ''
    q = (f'[out:json][timeout:150];area["ISO3166-2"="{iso}"]->.a;'
         f'(relation["route"~"{rt}"]["name"~"{rx}",i](area.a);{hw}{wt})->.m;(.m;rel(r.m););out geom;')
    try: j = get(OVP, data=urllib.parse.urlencode({'data': q}).encode(), t=200)
    except Exception as e: note('Overpass', f'{name}: {str(e)[:120]}'); return None, ''
    keep, names = [], set()
    for el in j.get('elements', []):
        if el.get('type') == 'relation':
            lines = [[[round(p['lon'], 5), round(p['lat'], 5)] for p in m.get('geometry', [])] for m in el.get('members', []) if m.get('type') == 'way' and m.get('geometry')]
        else:
            lines = [[[round(p['lon'], 5), round(p['lat'], 5)] for p in el.get('geometry', [])]]
        lines = [l for l in lines if len(l) > 1]
        if not lines: continue
        near = min(km(la, lo, p[1], p[0]) for l in lines for p in l)
        if near <= MATCH_KM: keep += lines; names.add(el.get('tags', {}).get('name', ''))
    time.sleep(2)
    return (keep or None), ', '.join(sorted(n for n in names if n))[:120]
# ---------------------------------------------------------------- run
try: IDX = {x['ref']: x for x in json.load(open(f'{OUT}/index-state.json'))}
except Exception: IDX = {}
try: NAT = {x['ref'] for x in json.load(open(f'{OUT}/index.json'))}
except Exception: NAT = set()
LOC = {}
try:
    for r in json.load(open('locations.json')):
        if r[0] == 'POTA': LOC[r[1]] = (r[3], r[4])
except Exception: pass
report = {'updated': datetime.date.today().isoformat(), 'found': [], 'missing': []}
_ran = lambda s: s in STATES or ('CANADA' in [z.upper() for z in STATES] and str(s).startswith('CA-'))
try:  # keep last run's rows for the states not run this time (Oct 17), so the report covers every state
    _old = json.load(open(f'{OUT}/state-report.json'))
    report['found'] = [x for x in _old.get('found', []) if not _ran(x[2])]; report['missing'] = [x for x in _old.get('missing', []) if not _ran(x[2])]
    report['noline'] = [x for x in _old.get('noline', []) if not _ran(x[2])]
except Exception: pass
def jobs():
    """(label, [(ref, row, iso)]) per state; 'CANADA' (Oct 17, Brandon: 'Canada outlines and trail') = every CA- POTA park
    whose type or name says Trail, from data/parkinfo/CA.json (province = field 10), searched in that province."""
    for st in STATES:
        if st.upper() == 'CANADA':
            try: d = json.load(open('data/parkinfo/CA.json'))
            except Exception: note('Canada', 'no park file'); continue
            yield 'CANADA', [(r, v, 'CA-' + (v[10] if len(v) > 10 and v[10] else '')) for r, v in d['parks'].items()
                             if r not in NAT and ('Trail' in (v[2] or '') or re.search(r'\bTrail\b', v[0] or '')) and len(v) > 10 and v[10]]
            continue
        try: d = json.load(open(f'data/parkinfo/US-{st}.json'))
        except Exception: note(f'US-{st}', 'no park file'); continue
        yield st, [(r, v, f'US-{st}') for r, v in d['parks'].items() if r not in NAT and (
            ('Trail' in (v[2] or '') and 'National Scenic' not in (v[2] or '') and 'National Historic' not in (v[2] or ''))
            or ((v[2] or '') == 'State Park' and re.search(r'\bTrail\b', v[0]) and not re.search(r'Trail of Tears', v[0])))]
for st, cand in jobs():
    got = 0
    for ref, v, iso in cand:
        stc = iso[3:] if iso.startswith('US-') else iso
        if ref in SKIP: continue
        name, typ = v[0], v[2] or ''
        la, lo = (v[5], v[6]) if len(v) > 6 and v[5] is not None else LOC.get(ref, (None, None))
        if la is None: report['missing'].append([ref, name, stc, 'no pin']); continue
        lim = CHECK_KM if kind(typ, name) == 'TP' else CHECK_KM_TRAIL
        lines, by, off, near = None, '', False, 1e9
        for nm in [name] + ALIAS.get(ref, []):   # Oct 18: also the other names the maps use
            if 'National Recreation' in typ:
                lines = forest(nm, la, lo); by, off = ('US Forest Service', True) if lines else ('', False)
            if not lines and iso.startswith('US-'):
                lines, org = agency(nm, stc, la, lo, lim)
                if lines: by, off = org, True
                # Oct 17: an agency layer that only has a tiny piece (Empire State Trail 4 km) loses to a much longer OpenStreetMap line
                if lines and sum(seglen(l) for l in lines) < 8:
                    ol, on = osm(nm, iso, la, lo)
                    if ol and sum(seglen(l) for l in ol) > 3 * sum(seglen(l) for l in lines) and min(km(la, lo, p[1], p[0]) for l in ol for p in l) <= lim:
                        lines, by, off = ol, 'OpenStreetMap (not official)', False
            if not lines:
                lines, on = osm(nm, iso, la, lo); by = 'OpenStreetMap (not official)' if lines else ''
            if lines:
                near = min(km(la, lo, p[1], p[0]) for l in lines for p in l)
                if near <= lim: break
                lines = None
        if not lines:
            why = 'line found too far from the POTA pin: not used' if near < 1e9 else 'no line found'
            if ref in NOLINE_PARK: report.setdefault('noline', []).append([ref, name, stc, 'a park with Trail in its name, not a trail'])
            elif NOLINE.search(name): report.setdefault('noline', []).append([ref, name, stc, 'a driving route, area or water trail: no single line to draw'])
            else: report['missing'].append([ref, name, stc, why])
            continue
        # Oct 18: agency layers often hold the same line 2-4 times (one per surface / year / direction): keep one copy
        _u, _seen = [], set()
        for l in lines:
            k = tuple(map(tuple, l)); kr = tuple(reversed(k))
            if k in _seen or kr in _seen: continue
            _seen.add(k); _u.append(l)
        lines = [dp(l, 0.0003) for l in _u]
        total = sum(seglen(l) for l in lines)
        if kind(typ, name) == 'TP' and total < 4: report['missing'].append([ref, name, stc, 'short: probably a park, not a trail']); continue
        xs = [p[0] for l in lines for p in l]; ys = [p[1] for l in lines for p in l]
        f = {'type': 'Feature', 'properties': {'ref': ref, 'name': name}, 'geometry': {'type': 'MultiLineString', 'coordinates': lines}}
        json.dump(f, open(f'{OUT}/{ref}.json', 'w'), separators=(',', ':'))
        IDX[ref] = {'ref': ref, 'name': name, 'kind': kind(typ, name), 'type': typ, 'st': stc, 'bbox': [round(min(xs), 4), round(min(ys), 4), round(max(xs), 4), round(max(ys), 4)],
                    'by': by, 'official': off, 'km': round(total), 'kb': round(os.path.getsize(f'{OUT}/{ref}.json') / 1024)}
        report['found'].append([ref, name, stc, by, round(total), round(near, 1)]); got += 1
    note(st if st == 'CANADA' else f'US-{st}', f'{got} of {len(cand)} trail parks drawn')
json.dump(sorted(IDX.values(), key=lambda x: (x['st'], x['name'])), open(f'{OUT}/index-state.json', 'w'), separators=(',', ':'))
report['agency'] = ALOG[-400:]
json.dump(report, open(f'{OUT}/state-report.json', 'w'), indent=1)
note('State trails done', f"{len(report['found'])} drawn, {len(report['missing'])} not drawn (see data/trails/state-report.json)")
