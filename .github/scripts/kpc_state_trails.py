"""KPC state + recreation trails that are POTA parks (Brandon Oct 16: 'give me 12 states trails ... where they need to be').
For each state in STATES, every POTA park in data/parkinfo/US-XX.json whose POTA type is a trail (State Trail,
National Recreation Trail ...) or a State Park whose name says Trail (rail-trail parks like Katy Trail). National
Scenic / Historic Trails are left out (kpc_us_trails.py draws those from the NPS).
Line sources, best first:
  1. US Forest Service trails (EDW TrailNFS_Publish) by trail name, for National Recreation Trails on forest land
  2. OpenStreetMap route relations (Overpass) with the trail's name inside the state; labelled NOT OFFICIAL
Each line must pass near the POTA pin (CHECK_KM) or it is not used: wrong-place matches are worse than none.
Writes data/trails/<REF>.json (same format as the national trails) + data/trails/index-state.json
[{ref,name,kind ST|NRT|TP,bbox,by,official,km}] and data/trails/state-report.json (found / missing, for KPC)."""
import json, os, re, time, math, urllib.request, urllib.parse, datetime
STATES = (os.environ.get('STATES') or 'TN IN OH WV VA MO IL NC GA AL MI PA').split()
OUT = 'data/trails'; os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'KPC trails (kentuckyportableclub.github.io)'}
CHECK_KM = 8.0   # the drawn line must come this close to the POTA pin
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
def core(n): return re.sub(r'\s+', ' ', re.sub(GEN, ' ', n.lower())).strip()
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
# ---------------------------------------------------------------- 2. OpenStreetMap
OVP = 'https://overpass-api.de/api/interpreter'
def words(name):  # Oct 17: letters/numbers only, so "Alene's", "Ka‘ena" and "Estacada- Boring" still match OpenStreetMap
    return [x for x in re.split(r'[^0-9a-z]+', core(name)) if len(x) > 2]
def osm(name, iso, la, lo):
    """Oct 17 (Brandon: 'readdress the missing trails'): route relations of any kind (foot, bike, horse, canoe for water
    trails, road for scenic byways) AND plain named paths/cycleways/tracks (many rail-trails are just ways); every match
    within MATCH_KM of the POTA pin is kept (trails come in sections), not just the longest one anywhere in the state."""
    w = words(name)
    if not w: return None, ''
    rx = '.*'.join(re.escape(x) for x in w)
    road = re.search(r'byway|highway|scenic drive', name, re.I)
    water = re.search(r'water|river|canoe|paddl', name, re.I)
    rt = 'hiking|foot|bicycle|mtb|horse|inline_skates|running|canoe|boat' + ('|road' if road else '')
    hw = '' if road else f'way["highway"~"path|cycleway|footway|track|bridleway"]["name"~"{rx}",i](area.a);'
    wt = f'way["waterway"~"river|stream|canal"]["name"~"{rx}",i](area.a);' if water else ''
    q = (f'[out:json][timeout:150];area["ISO3166-2"="{iso}"]->.a;'
         f'(relation["route"~"{rt}"]["name"~"{rx}",i](area.a);{hw}{wt});out geom;')
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
        lines, by, off = None, '', False
        if 'National Recreation' in typ:
            lines = forest(name, la, lo); by, off = ('US Forest Service', True) if lines else ('', False)
        if not lines:
            lines, on = osm(name, iso, la, lo); by = 'OpenStreetMap (not official)' if lines else ''
        if not lines: report['missing'].append([ref, name, stc, 'no line found']); continue
        near = min(km(la, lo, p[1], p[0]) for l in lines for p in l)
        if near > CHECK_KM: report['missing'].append([ref, name, stc, f'line found {near:.0f} km from the POTA pin: not used']); continue
        lines = [dp(l, 0.0003) for l in lines]
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
json.dump(report, open(f'{OUT}/state-report.json', 'w'), indent=1)
note('State trails done', f"{len(report['found'])} drawn, {len(report['missing'])} not drawn (see data/trails/state-report.json)")
