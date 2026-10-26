#!/usr/bin/env python3
"""ALL-STATES 2-FER BOT (chat 2, Oct 26 2026; Brandon via HQ: 'dead certain before anything is shown').

Finds spots where two (or more) POTA parks share the same ground, in the US (all states but Kentucky, which has its own
hand-checked list in ky-overlaps.geojson) and Canada. HIDDEN: it writes data files only (data/fers/), nothing links to them.

Rules (Brandon, Oct 26):
- OFFICIAL outlines only: the answer keys' joins (data/us-key, data/ca-key), never a park the key marks approximate
  ('reviewed-approx', a lake surface), never a park whose pin is 'well outside' its land. POTA parks only.
- A spot counts only when the shared ground holds a spot AT LEAST 100 YARDS ACROSS: shrink the overlap 50 yards inward
  and something must remain (no slivers, no parks that only touch). Holes (inholdings) in an outline stay holes.
- TRAILS + RIVERS (official lines, data/trails): POTA's rule = the station entirely within 100 ft of the trail (KPC applies
  the same to rivers). So a stretch AT LEAST 100 YARDS LONG where a station spot inside the other park (5 m in) is within
  100 ft of the line; two lines: their 100-ft zones meet along 100 yards.
- n-fers: a 3-fer is three parks sharing the SAME ground (never a chain); same for 4.
- Two park numbers joined to the SAME outline record = an answer-key mistake: listed in data/fers/same-outline.json,
  never a spot.
- Both pins inside their own outlines (checked on the finest shapes, pass 3).

Three passes, each a different way; a spot is a CANDIDATE only when all three agree:
  PASS=1  the saved outlines (PAD-US copy in the boundary cache, saved Canadian outlines, saved trail lines) + the state
          layers at the key's own detail; every park: box test on a grid first (most parks stop there), then a coarse
          overlap, then the 100-yard test at 20 m cells. Writes data/fers/<US-XX|CA-XX>.json.
  PASS=2  only the parks in pass-1 spots, outlines downloaded FRESH from the agencies (PAD-US, the state / provincial
          layers, CPCAD) at ~20 m detail, 10 m cells.
  PASS=3  the same parks, the FINEST shapes the agencies give (~2 m), 5 m cells, + the pin test.
Geometry is done on rasters (numpy + OpenCV): outlines are filled with the even-odd rule, the overlap is measured with a
distance transform (= the 50-yard shrink), spots are its connected pieces.

Never fails (exit 0). MINUTES = time limit; what is done is saved.
"""
import gzip, json, math, os, pathlib, re, sys, time, urllib.parse, urllib.request
import numpy as np
import cv2
sys.path.insert(0, os.path.dirname(__file__))
from kpc_save import save_json

T0 = time.time(); LIMIT = float(os.environ.get('MINUTES') or 300) * 60
PASS = int(os.environ.get('PASS') or 1)
ONLY = set((os.environ.get('STATES') or '').upper().replace(',', ' ').split())
REGION = (os.environ.get('REGION') or 'na').strip().lower()      # 'na' = US + Canada, 'world' = the other countries (Brandon Oct 26: 'do the world')
CELL = {1: 20.0, 2: 10.0, 3: 5.0}[PASS]
DET = {1: 0.0005, 2: 0.0002, 3: 0.00002}[PASS]
PREC = {1: 5, 2: 5, 3: 6}[PASS]
SHRINK = 45.72            # 50 yards: what must remain after shrinking the overlap this far = a spot 100 yards across
STRETCH = 91.44           # 100 yards of a trail / river inside the other park
# POTA's trail rule (Activator Guide, docs.pota.app): 'Your station must be located entirely within 100 feet (30.5m) of the
# trail'; KPC's guide applies the same to river parks (within 100 ft of the water). So a trail / river counts with another
# park where a station spot sits INSIDE that park (5 m in) and within 100 ft of the line (5 m to spare): 25 m.
ZONE = 30.48 - 5.0
STATION_IN = 5.0
MAXPX = 9_000_000         # pixels per raster tile
OUT = pathlib.Path('data/fers'); OUT.mkdir(parents=True, exist_ok=True)
CACHE_US = pathlib.Path(os.environ.get('GEO_CACHE') or 'cache/us')
CACHE_CA = pathlib.Path(os.environ.get('GEO_CACHE_CA') or 'cache/ca')
CACHE_W = pathlib.Path(os.environ.get('GEO_CACHE_W') or 'cache/world')
UA = {'User-Agent': 'KPC 2-fer bot (kentuckyportableclub.github.io)'}
PADUS = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
FWS = 'https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSInterest_Simplified_Authoritative/FeatureServer/0/query'
CPCAD = 'https://maps-cartes.ec.gc.ca/arcgis/rest/services/CWS_SCF/CPCAD/MapServer/0/query'
LOG = []


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', ' ')[:900]), flush=True)
def late(): return time.time() - T0 > LIMIT
def low(x): return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', str(x or '').lower()).split())


def get(url, params, tries=3, timeout=120):
    body = urllib.parse.urlencode(params).encode()
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=body, headers=dict(UA, **{'Content-Type': 'application/x-www-form-urlencoded'}))
            j = json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', 'replace'))
            if isinstance(j, dict) and j.get('error'): raise RuntimeError(str(j['error'])[:150])
            return j
        except Exception as e:  # noqa: BLE001
            last = e; time.sleep(2 + 3 * i)
    raise last


# ------------------------------------------------------------------ parks (official only)
def pins():
    P = {}
    for f in pathlib.Path('data/parkinfo').glob('US-*.json'):
        for r, v in json.load(open(f))['parks'].items():
            if v[5] is not None: P[r] = (v[0], v[5], v[6], v[1], v[2], f.stem[3:])
    try:
        for r, v in json.load(open('data/parkinfo/CA.json'))['parks'].items():
            if v[5] is not None and len(v) > 10: P[r] = (v[0], v[5], v[6], v[1], v[2], 'CA-' + v[10])
    except Exception: pass  # noqa: BLE001
    for f in pathlib.Path('data/parkinfo').glob('[A-Z][A-Z].json'):
        if f.stem in ('CA', 'US'): continue
        try:
            for r, v in json.load(open(f))['parks'].items():
                if len(v) > 6 and v[5] is not None and v[6] is not None: P[r] = (v[0], v[5], v[6], v[1], v[2], 'W-' + f.stem)
        except Exception: pass  # noqa: BLE001
    return P


WATER = set()
def water_prefixes():
    """state-gis layers that are lake SURFACES (water: 1) give only an approximate park."""
    try:
        sg = json.load(open('data/state-gis.json'))['states']
        L = json.load(open('data/us-key/layers.json'))
        for st, lays in sg.items():
            for l in lays:
                if l.get('water'):
                    u = str(l.get('url') or '').rstrip('/') + '/query'
                    for pre, v in L.items():
                        if v[0] == u: WATER.add(pre)
    except Exception: pass  # noqa: BLE001


def official_parks(PIN):
    """{ref: {'st', 'ids': [record ids], 'names': {id: name}}} + why parks were left out."""
    water_prefixes()
    parks, skip = {}, {'approximate': 0, 'pin well outside': 0, 'no outline': 0, 'no pin': 0, 'Kentucky (own list)': 0}
    if REGION == 'world':
        for f in sorted(pathlib.Path('data/world-key').glob('[A-Z][A-Z].json')):
            for ref, p in json.load(open(f))['parks'].items():
                m = p.get('m') or []
                if not m: skip['no outline'] += 1; continue
                if p.get('far') == 'well outside': skip['pin well outside'] += 1; continue
                if any('approx' in str(x[3]) for x in m if len(x) > 3): skip['approximate'] += 1; continue
                if ref not in PIN: skip['no pin'] += 1; continue
                parks[ref] = {'st': 'W-' + f.stem, 'ids': [x[0] for x in m], 'names': {str(i): x[1] for i, x in enumerate(m)}, 'm': m}
        skip.pop('Kentucky (own list)', None)
        return parks, skip
    for f in sorted(pathlib.Path('data/us-key').glob('US-*.json')):
        st = f.stem
        if st == 'US-KY': continue
        for ref, p in json.load(open(f))['parks'].items():
            m = p.get('m') or []
            if not m: skip['no outline'] += 1; continue
            if p.get('far') == 'well outside': skip['pin well outside'] += 1; continue
            if any('approx' in str(x[3]) for x in m if len(x) > 3) or any(isinstance(x[0], str) and re.match(r'[a-z]+', x[0]).group() in WATER for x in m):
                skip['approximate'] += 1; continue
            if ref not in PIN: skip['no pin'] += 1; continue
            parks[ref] = {'st': st, 'ids': [x[0] for x in m], 'names': {str(x[0]): x[1] for x in m}}
    for f in sorted(pathlib.Path('data/ca-key').glob('CA-*.json')):
        if not re.fullmatch(r'CA-[A-Z]{2}', f.stem): continue
        for ref, p in json.load(open(f))['parks'].items():
            m = p.get('m') or []
            if not m: skip['no outline'] += 1; continue
            if p.get('far') == 'well outside': skip['pin well outside'] += 1; continue
            if any('approx' in str(x[3]) for x in m if len(x) > 3): skip['approximate'] += 1; continue
            if ref not in PIN: skip['no pin'] += 1; continue
            parks[ref] = {'st': f.stem, 'ids': [x[0] for x in m], 'names': {str(x[0]): x[1] for x in m}}
    try: skip['Kentucky (own list)'] = len(json.load(open('data/parkinfo/US-KY.json'))['parks'])
    except Exception: skip['Kentucky (own list)'] = 'all (ky-overlaps.geojson)'  # noqa: BLE001
    return parks, skip


def trail_lines():
    """{ref: [[[lon, lat], ...], ...]} official trail / river lines saved by the trails bot."""
    out = {}
    try: idx = json.load(open('data/trails/index-state.json'))
    except Exception: return out  # noqa: BLE001
    for x in idx:
        if not x.get('official'): continue
        f = pathlib.Path(f"data/trails/{x['ref']}.json")
        if not f.exists(): continue
        try: g = json.load(open(f)).get('geometry') or {}
        except Exception: continue  # noqa: BLE001
        c = g.get('coordinates') or []
        ls = c if g.get('type') == 'MultiLineString' else ([c] if g.get('type') == 'LineString' else [])
        ls = [l for l in ls if len(l) > 1]
        if ls: out[x['ref']] = {'lines': ls, 'kind': 'river' if x.get('kind') == 'WSR' or re.search(r'river', str(x.get('type')), re.I) else 'trail'}
    return out


# ------------------------------------------------------------------ outlines
def esri_rings(g):
    if not g: return []
    if g.get('rings'): return [[[p[0], p[1]] for p in r] for r in g['rings'] if len(r) > 2]
    return []


LAYERS_US = json.load(open('data/us-key/layers.json')) if os.path.exists('data/us-key/layers.json') else {}
LAYERS_CA = json.load(open('data/ca-key/layers.json')) if os.path.exists('data/ca-key/layers.json') else {}


LAYERS_W = json.load(open('data/world-key/layers.json')) if os.path.exists('data/world-key/layers.json') else {}


def source_of(rid, canada, src=None):
    """(query url, objectid, name check?) for a key record id."""
    if src is not None:   # the world: only ArcGIS maps can be asked for one record by id
        u = LAYERS_W.get(src)
        if isinstance(rid, int) and u and re.search(r'/\d+$', u.rstrip('/')): return [u.rstrip('/') + '/query'], rid, True
        return [], None, True
    if canada:
        if isinstance(rid, int): return [CPCAD], rid, True
        lab, _, n = str(rid).partition(':')
        if not n.isdigit(): return [], None, True
        urls = [u.rstrip('/') + '/query' for u in LAYERS_CA.get(lab) or [] if re.search(r'/\d+$', u.rstrip('/'))]
        return urls, int(n), True
    if isinstance(rid, int): return [PADUS], rid, False
    m = re.fullmatch(r'([a-z]+)(\d+)', str(rid))
    if not m: return [], None, False
    pre, n = m.group(1), int(m.group(2))
    if pre == 'fws': return [FWS], n, False
    if pre in LAYERS_US: return [LAYERS_US[pre][0]], n, False
    return [], None, False


def name_ok(want, attrs):
    w = low(want)
    if not w: return True
    for v in attrs.values():
        if isinstance(v, str):
            v = low(v)
            if v and (v == w or (len(v) > 3 and (v in w or w in v))): return True
    return False


def download(parks, refs, det, prec):
    """{ref: [group of rings per record]} downloaded from the agencies by object id. A park with a record that could not
    be read is left out (dead certain: half a park is not the park)."""
    want = {}
    for ref in refs:
        ca = parks[ref]['st'].startswith('CA-')
        for i, rid in enumerate(parks[ref]['ids']):
            if 'm' in parks[ref]:
                urls, oid, chk = source_of(rid, False, parks[ref]['m'][i][2]); key = str(i)
            else:
                urls, oid, chk = source_of(rid, ca); key = str(rid)
            if not urls: want.setdefault(('none',), []).append((ref, key, None, chk)); continue
            want.setdefault(tuple(urls), []).append((ref, key, oid, chk))
    got, bad = {}, set()
    for urls, items in want.items():
        if urls == ('none',):
            for ref, *_ in items: bad.add(ref)
            continue
        if late(): break
        oids = sorted({i[2] for i in items})
        found = {}
        for u in urls:
            for k in range(0, len(oids), 100):
                ids = [o for o in oids[k:k + 100] if o not in found]
                if not ids: continue
                try:
                    j = get(u, {'objectIds': ','.join(map(str, ids)), 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326,
                                'maxAllowableOffset': det, 'geometryPrecision': prec, 'f': 'json'})
                except Exception as e:  # noqa: BLE001
                    LOG.append(f'{u.split("/rest/services/")[-1][:60]}: not read ({str(e)[:60]})'); continue
                oidf = j.get('objectIdFieldName') or 'OBJECTID'
                for f in j.get('features') or []:
                    a = f.get('attributes') or {}
                    o = a.get(oidf)
                    if o is None: o = next((v for k2, v in a.items() if k2.lower() in ('objectid', 'fid', 'oid', 'object id')), None)
                    if o is not None: found.setdefault(int(o), []).append((a, esri_rings(f.get('geometry'))))
                time.sleep(.3)
        for ref, rid, oid, chk in items:
            cand = found.get(oid) or []
            hit = next((r for a, r in cand if r and (not chk or name_ok(parks[ref]['names'].get(rid), a))), None)
            if hit: got.setdefault(ref, []).append(hit)
            else: bad.add(ref)
    for ref in bad: got.pop(ref, None)
    return got, bad


def saved_us(parks):
    """PAD-US records from the boundary cache (the answer key's own saved copy)."""
    by = {}
    for f in CACHE_US.glob('US-*.json.gz'):
        try:
            with gzip.open(f, 'rt', encoding='utf-8') as fh:
                for r in json.load(fh).get('recs') or []:
                    if r.get('_r'): by[r.get('OBJECTID')] = r['_r']
        except Exception: pass  # noqa: BLE001
    return by


def saved_ca(parks):
    """{ref: [groups]} from data/canada-bounds (one group per polygon) or the CA-ALL cache (one per record, id + name)."""
    by = {}
    f = CACHE_CA / 'CA-ALL.json.gz'
    if f.exists():
        try:
            with gzip.open(f, 'rt', encoding='utf-8') as fh:
                for r in json.load(fh).get('recs') or []: by.setdefault(str(r.get('oid')), []).append(r)
        except Exception: pass  # noqa: BLE001
    out = {}
    for ref, p in parks.items():
        if not p['st'].startswith('CA-'): continue
        gs = []
        bf = pathlib.Path(f'data/canada-bounds/{ref}.json')
        if bf.exists():
            try:
                g = json.load(open(bf)).get('geometry') or {}
                c = g.get('coordinates') or []
                gs = [poly for poly in c if poly] if g.get('type') == 'MultiPolygon' else ([c] if c else [])
            except Exception: gs = []  # noqa: BLE001
        if not gs:
            ok = True
            for rid in p['ids']:
                r = next((q for q in by.get(str(rid), []) if low(p['names'].get(str(rid))) in (low(q.get('n')), low(q.get('nf')))), None)
                if r and r.get('_r'): gs.append(r['_r'])
                else: ok = False
            if not ok: gs = []
        if gs: out[ref] = gs
    return out


def saved_world(parks):
    """{ref: [groups]} from the world key's saved copy (cache/world/W-CC.json.gz): every joined record must be found
    (same source + id + name, or same source + name near the pin when the record had no id)."""
    out, PINS = {}, pins()
    by_cc = {}
    for ref, p in parks.items(): by_cc.setdefault(p['st'][2:], []).append(ref)
    for cc, refs in by_cc.items():
        f = CACHE_W / f'W-{cc}.json.gz'
        if not f.exists(): continue
        try:
            with gzip.open(f, 'rt', encoding='utf-8') as fh: recs = json.load(fh).get('recs') or []
        except Exception: continue  # noqa: BLE001
        idx = {}
        for r in recs: idx.setdefault((r.get('src'), low(r.get('n'))), []).append(r)
        for ref in refs:
            la, lo = PINS[ref][1], PINS[ref][2]
            gs, ok = [], True
            for x in parks[ref]['m']:
                cand = idx.get((x[2], low(x[1])), [])
                r = next((c for c in cand if x[0] is not None and c.get('id') == x[0]), None) or \
                    next((c for c in cand if x[0] is None and c.get('_bb') and c['_bb'][0] - .6 <= lo <= c['_bb'][2] + .6 and c['_bb'][1] - .6 <= la <= c['_bb'][3] + .6), None)
                if r and r.get('_r'): gs.append(r['_r'])
                else: ok = False
            if ok and gs: out[ref] = gs
    return out


# ------------------------------------------------------------------ rasters
def bbox_groups(gs):
    xs = [p[0] for g in gs for r in g for p in r]; ys = [p[1] for g in gs for r in g for p in r]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


def bbox_lines(ls):
    xs = [p[0] for l in ls for p in l]; ys = [p[1] for l in ls for p in l]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


class Frame:
    """A raster window: x = east metres, y = north metres around (lon0, lat0)."""
    def __init__(self, box, cell, pad):
        self.lat0 = (box[1] + box[3]) / 2; self.lon0 = (box[0] + box[2]) / 2
        self.kx = 111320 * math.cos(math.radians(self.lat0)); self.ky = 110574
        x0, y0 = (box[0] - self.lon0) * self.kx - pad, (box[1] - self.lat0) * self.ky - pad
        x1, y1 = (box[2] - self.lon0) * self.kx + pad, (box[3] - self.lat0) * self.ky + pad
        self.cell = cell; self.x0, self.y1 = x0, y1
        self.W, self.H = max(1, int(math.ceil((x1 - x0) / cell))), max(1, int(math.ceil((y1 - y0) / cell)))

    def px(self, pts):
        a = np.asarray(pts, dtype=np.float64)[:, :2]
        c = ((a[:, 0] - self.lon0) * self.kx - self.x0) / self.cell
        r = (self.y1 - (a[:, 1] - self.lat0) * self.ky) / self.cell
        return np.stack([c, r], axis=1)

    def ll(self, c, r):
        x = self.x0 + (c + .5) * self.cell; y = self.y1 - (r + .5) * self.cell
        return [round(self.lon0 + x / self.kx, 6), round(self.lat0 + y / self.ky, 6)]

    def area(self, gs):
        """inside ANY record; inside one record by the even-odd rule (holes stay holes)."""
        m = np.zeros((self.H, self.W), np.uint8)
        for g in gs:
            gm = np.zeros_like(m)
            for ring in g:
                t = np.zeros_like(m)
                cv2.fillPoly(t, [np.round(self.px(ring) * 16).astype(np.int32)], 1, lineType=cv2.LINE_8, shift=4)
                gm ^= t
            m |= gm
        return m

    def lines(self, ls, width_m):
        m = np.zeros((self.H, self.W), np.uint8)
        th = max(1, int(round(2 * width_m / self.cell)))
        for l in ls:
            cv2.polylines(m, [np.round(self.px(l) * 16).astype(np.int32)], False, 1, thickness=th, lineType=cv2.LINE_8, shift=4)
        return m


def inter(b1, b2, pad=0.0):
    b = [max(b1[0], b2[0]) - pad, max(b1[1], b2[1]) - pad, min(b1[2], b2[2]) + pad, min(b1[3], b2[3]) + pad]
    return b if b[0] <= b[2] and b[1] <= b[3] else None


def tiles(box, cell, pad):
    """Split a box into raster tiles of at most MAXPX pixels at this cell size."""
    f = Frame(box, cell, pad)
    if f.W * f.H <= MAXPX: return [box]
    side = math.sqrt(MAXPX) * cell
    nx = max(1, int(math.ceil(f.W * cell / side))); ny = max(1, int(math.ceil(f.H * cell / side)))
    dx, dy = (box[2] - box[0]) / nx, (box[3] - box[1]) / ny
    return [[box[0] + i * dx, box[1] + j * dy, box[0] + (i + 1) * dx, box[1] + (j + 1) * dy] for i in range(nx) for j in range(ny)]


def area_spots(G, refs, box):
    """Spots where every park in refs shares ground holding a 100-yard spot. G[ref] = groups. Coarse look first."""
    # coarse: at most ~1 M pixels over the shared box; parks grown by one pixel so thin-but-real overlaps are not lost
    f = Frame(box, max(CELL, math.sqrt(max(1.0, (box[2] - box[0]) * 111320 * math.cos(math.radians(box[1])) * (box[3] - box[1]) * 110574) / 1e6)), 0)
    k = np.ones((3, 3), np.uint8)
    ov = None
    for r in refs:
        m = cv2.dilate(f.area(G[r]), k)
        ov = m if ov is None else ov & m
        if not ov.any(): return []
    rows, cols = np.nonzero(ov)
    if f.cell > CELL:   # fine tiles only where the coarse look saw shared ground
        lon = f.lon0 + (f.x0 + (cols + .5) * f.cell) / f.kx
        lat = f.lat0 + (f.y1 - (rows + .5) * f.cell) / f.ky
        fine_box = [lon.min() - f.cell / f.kx, lat.min() - f.cell / f.ky, lon.max() + f.cell / f.kx, lat.max() + f.cell / f.ky]
        mx, my = f.cell / f.kx, f.cell / f.ky
        boxes = [b for b in tiles(fine_box, CELL, 0)
                 if np.any((lon >= b[0] - mx) & (lon <= b[2] + mx) & (lat >= b[1] - my) & (lat <= b[3] + my))] or [fine_box]
    else:
        boxes = [box]
    out = []
    for b in boxes:
        if late(): break
        F = Frame(b, CELL, SHRINK * 3)
        ovf = None
        for r in refs:
            m = F.area(G[r]); ovf = m if ovf is None else ovf & m
            if not ovf.any(): break
        if ovf is None or not ovf.any(): continue
        dist = cv2.distanceTransform(ovf, cv2.DIST_L2, 5) * CELL
        core = (dist >= SHRINK + CELL * (1.0 if PASS == 3 else .5)).astype(np.uint8)   # pass 3 strict, 1-2 a little lenient (screens)
        if not core.any(): continue
        n, lab = cv2.connectedComponents(ovf, connectivity=8)
        for L in sorted(set(lab[core > 0].tolist())):
            comp = (lab == L)
            d = np.where(comp, dist, 0); r0, c0 = np.unravel_index(np.argmax(d), d.shape)
            cs, _ = cv2.findContours(comp.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            big = max(cs, key=cv2.contourArea)
            ap = cv2.approxPolyDP(big, 1.5, True).reshape(-1, 2)
            if len(ap) > 300: ap = ap[::int(math.ceil(len(ap) / 300))]
            shape = [F.ll(int(c), int(r)) for c, r in ap]
            out.append({'refs': sorted(refs), 'kind': 'area', 'center': F.ll(int(c0), int(r0))[::-1],
                        'acres': round(int(comp.sum()) * CELL * CELL / 4046.86, 1), 'wide_m': round(float(d.max()) * 2), 'shape': shape})
    return merge(out)


def merge(spots):
    """A spot cut by a tile edge comes back as two: one spot when their shapes touch."""
    out = []
    for s in spots:
        b = bbox_lines([s['shape']])
        t = next((o for o in out if o['refs'] == s['refs'] and o['kind'] == s['kind'] and inter(o['_b'], b, 0.0005)), None)
        if t:
            t['acres'] = round(t['acres'] + s.get('acres', 0), 1)
            if s.get('wide_m', 0) > t.get('wide_m', 0): t['center'], t['wide_m'] = s['center'], s['wide_m']
            if s.get('len_m'): t['len_m'] = round(t.get('len_m', 0) + s['len_m'])
            t['_b'] = [min(t['_b'][0], b[0]), min(t['_b'][1], b[1]), max(t['_b'][2], b[2]), max(t['_b'][3], b[3])]
            t['shape'] = t['shape'] if len(t['shape']) >= len(s['shape']) else s['shape']
        else:
            s['_b'] = b; out.append(s)
    for o in out: o.pop('_b', None)
    return out


def sample(l, step):
    out = []
    for a, b in zip(l, l[1:]):
        kx = 111320 * math.cos(math.radians(a[1])); d = math.hypot((b[0] - a[0]) * kx, (b[1] - a[1]) * 110574)
        n = max(1, int(d // step))
        for i in range(n): out.append((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n))
    out.append(tuple(l[-1][:2])); return out


def line_spots(lref, ls, oref, other, other_is_line, box, kind):
    """Stretches of park lref's line(s) at least 100 yards long where a station can stand within 100 ft of the line AND
    inside park oref (5 m in from its line); for two lines: within 100 ft of both (the two 100-ft zones meet)."""
    out = []
    for l in ls:
        pts = [p for p in sample(l, CELL / 2) if box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]]
        if len(pts) < 2: continue
        ins = np.zeros(len(pts), bool)
        for b in tiles(bbox_lines([pts]), CELL, 0):
            idx = [i for i, p in enumerate(pts) if b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3]]
            if not idx: continue
            F = Frame(b, CELL, 120)
            if other_is_line: ok = F.lines(other, 2 * ZONE)
            else:
                spot_ok = (cv2.distanceTransform(F.area(other), cv2.DIST_L2, 5) * CELL >= STATION_IN).astype(np.uint8)
                ok = (cv2.distanceTransform(1 - spot_ok, cv2.DIST_L2, 5) * CELL <= ZONE).astype(np.uint8)
            P = F.px([pts[i] for i in idx]).astype(int)
            P[:, 0] = P[:, 0].clip(0, F.W - 1); P[:, 1] = P[:, 1].clip(0, F.H - 1)
            ins[idx] = ok[P[:, 1], P[:, 0]] > 0
        run, best = [], []
        for i, p in enumerate(pts + [None]):
            if p is not None and ins[i]: run.append(p); continue
            if len(run) > 1:
                L = sum(math.hypot((b2[0] - a2[0]) * 111320 * math.cos(math.radians(a2[1])), (b2[1] - a2[1]) * 110574) for a2, b2 in zip(run, run[1:]))
                if L >= STRETCH:
                    st = run[::max(1, len(run) // 200)]
                    out.append({'refs': sorted([lref, oref]), 'kind': kind, 'center': [round(run[len(run) // 2][1], 6), round(run[len(run) // 2][0], 6)],
                                'len_m': round(L), 'shape': [[round(q[0], 6), round(q[1], 6)] for q in st]})
            run = []
    return merge(out)


# ------------------------------------------------------------------ the passes
def grid_pairs(boxes):
    """Pairs whose boxes touch, found on a 0.5-degree grid (never every pair)."""
    cells = {}
    for ref, b in boxes.items():
        for i in range(int(math.floor(b[0] / .5)), int(math.floor(b[2] / .5)) + 1):
            for j in range(int(math.floor(b[1] / .5)), int(math.floor(b[3] / .5)) + 1):
                cells.setdefault((i, j), []).append(ref)
    pairs = set()
    for refs in cells.values():
        if len(refs) > 1:
            for a in range(len(refs)):
                ba = boxes[refs[a]]
                for c in range(a + 1, len(refs)):
                    if inter(ba, boxes[refs[c]]): pairs.add(tuple(sorted((refs[a], refs[c]))))
    return pairs


def find_spots(G, LN, pairs, counts):
    spots = []
    for a, b in sorted(pairs):
        if late(): counts['stopped for time'] = True; break
        counts['pairs tested'] += 1
        ba = bbox_groups(G[a]) if a in G else bbox_lines(LN[a]['lines'])
        bb = bbox_groups(G[b]) if b in G else bbox_lines(LN[b]['lines'])
        box = inter(ba, bb, 0.0008)
        if not box: continue
        try:
            if a in G and b in G: got = area_spots(G, [a, b], box)
            else:
                got = []
                for l_ref, o_ref in ((a, b), (b, a)):
                    if l_ref in LN and l_ref not in G:
                        if o_ref in G: got += line_spots(l_ref, LN[l_ref]['lines'], o_ref, G[o_ref], False, box, LN[l_ref]['kind'])
                        elif o_ref in LN: got += line_spots(l_ref, LN[l_ref]['lines'], o_ref, LN[o_ref]['lines'], True, box, LN[l_ref]['kind']); break
            spots += got
        except Exception as e:  # noqa: BLE001
            LOG.append(f'{a} + {b}: {str(e)[:80]}')
    # n-fers: a third park sharing the SAME ground as an area spot (100 yards across, all three)
    nb = {}
    for a, b in pairs: nb.setdefault(a, set()).add(b); nb.setdefault(b, set()).add(a)
    level = [s for s in spots if s['kind'] == 'area']
    for n in (3, 4):
        nxt = []
        for s in level:
            if late(): break
            others = set.intersection(*[nb.get(r, set()) for r in s['refs']]) - set(s['refs'])
            sb = bbox_lines([s['shape']])
            for c in sorted(others):
                if c not in G or any(x['refs'] == sorted(s['refs'] + [c]) for x in nxt): continue
                box = inter(sb, bbox_groups(G[c]), 0.0008)
                if not box: continue
                try: nxt += area_spots(G, s['refs'] + [c], [box[0] - .001, box[1] - .001, box[2] + .001, box[3] + .001])
                except Exception as e: LOG.append(f"{'+'.join(s['refs'])} + {c}: {str(e)[:60]}")  # noqa: BLE001
        spots += nxt; level = nxt
    return spots


def same_outline(parks):
    seen, out = {}, []
    for ref, p in parks.items():
        for i, rid in enumerate(p['ids']):
            if rid is None: continue
            k = (p['m'][i][2], str(rid)) if 'm' in p else (p['st'][:2], str(rid))
            if k in seen and seen[k] != ref: out.append({'refs': sorted([seen[k], ref]), 'record': str(rid), 'name': p['names'].get(str(i) if 'm' in p else str(rid))})
            else: seen[k] = ref
    return out


def pin_inside(ref, PIN, G, LN):
    nm, la, lo = PIN[ref][0], PIN[ref][1], PIN[ref][2]
    d = .004
    b = [lo - d, la - d, lo + d, la + d]
    F = Frame(b, CELL, 0)
    c, r = F.px([[lo, la]])[0].astype(int)
    if ref in G:
        m = F.area(G[ref])
        return bool(m[min(max(r, 0), F.H - 1), min(max(c, 0), F.W - 1)])
    if ref in LN:
        m = F.lines(LN[ref]['lines'], 300)
        return bool(m[min(max(r, 0), F.H - 1), min(max(c, 0), F.W - 1)])
    return False


def nearest_access(spot, st_of):
    best = None
    la, lo = spot['center']
    for ref in spot['refs']:
        st = st_of(ref)
        f = pathlib.Path(f'data/access/{st}.json')
        try: pts = json.load(open(f))['parks'].get(ref) or []
        except Exception: continue  # noqa: BLE001
        for q in pts:
            d = math.hypot((q[1] - lo) * 111320 * math.cos(math.radians(la)), (q[0] - la) * 110574)
            if best is None or d < best[4]: best = [q[0], q[1], q[2], ref, round(d)]
    return best


FILES = r'W-[A-Z]{2}' if REGION == 'world' else r'(US|CA)-[A-Z]{2}'
def file_of(st): return OUT / f'{st}.json'


def key_of(s): return '+'.join(s['refs']) + '@' + s['kind']


def main():
    PIN = pins()
    parks, skip = official_parks(PIN)
    LN = trail_lines()
    for ref in LN:
        if ref not in parks and ref in PIN and (REGION == 'world') == PIN[ref][5].startswith('W-'):
            st = PIN[ref][5]
            parks[ref] = {'st': st if st.startswith('CA-') else 'US-' + st, 'ids': [], 'names': {}}
    st_of = lambda r: parks[r]['st'] if r in parks else ''
    if ONLY: parks = {r: p for r, p in parks.items() if p['st'] in ONLY or p['st'][3:] in ONLY}
    counts = {'pass': PASS, 'cell_m': CELL, 'official parks': len(parks), 'left out': skip, 'pairs tested': 0, 'with official lines': sum(1 for r in LN if r in parks)}
    today = time.strftime('%Y-%m-%d')
    old = {}
    for f in OUT.glob('*-*.json'):
        if re.fullmatch(FILES, f.stem):
            try: old[f.stem] = json.load(open(f))
            except Exception: pass  # noqa: BLE001

    if PASS == 1:
        same = same_outline(parks)
        save_json(OUT / ('same-outline.json' if REGION != 'world' else 'same-outline-world.json'), {'about': 'Two park numbers joined to the SAME outline record: an answer-key mistake to fix, never a 2-fer.', 'pairs': same}, indent=1)
        skip_pairs = {tuple(x['refs']) for x in same}
        # saved outlines: PAD-US from the cache, Canada from the saved files; the rest from the state layers at the key's detail
        pad = saved_us(parks) if REGION != 'world' else {}
        G, need = {}, []
        for ref, p in parks.items():
            if p['st'].startswith(('CA-', 'W-')) or not p['ids']: continue
            if all(isinstance(i, int) and i in pad for i in p['ids']): G[ref] = [pad[i] for i in p['ids']]
            else: need.append(ref)
        G.update(saved_world(parks) if REGION == 'world' else saved_ca(parks))
        notice('2-fer bot', f"pass 1: {len(G)} parks from saved outlines, {len(need)} to download, {len(LN)} official lines")
        got, bad = download(parks, need, DET, PREC)
        G.update(got)
        counts['parks whose outline could not be read'] = len(bad)
        boxes = {r: bbox_groups(g) for r, g in G.items() if bbox_groups(g)}
        for r in LN:
            if r in parks and r not in boxes:
                b = bbox_lines(LN[r]['lines']); boxes[r] = [b[0] - .0005, b[1] - .0005, b[2] + .0005, b[3] + .0005]   # the 100-ft zone
        pairs = grid_pairs(boxes) - skip_pairs
        touched = {r for p in pairs for r in p}
        counts['parks done by the box test'] = len(boxes) - len(touched)
        counts['pairs whose boxes touch'] = len(pairs)
        spots = find_spots(G, LN, pairs, counts)
        by = {}
        for s in spots:
            s.update({'id': key_of(s) + '@%.3f,%.3f' % tuple(s['center']), 'passes': [1, 0, 0], 'status': 'pass 1', 'found': today})
            by.setdefault(st_of(s['refs'][0]), []).append(s)
        for st in sorted(set(by) | {p['st'] for p in parks.values()}):
            if counts.get('stopped for time') and st not in by and st in old: continue
            save_json(file_of(st), {'st': st, 'about': ABOUT, 'pass1': today, 'spots': sorted(by.get(st, []), key=lambda s: s['id'])}, indent=1)
    else:
        files = {st: d for st, d in old.items() if (not ONLY or st in ONLY or st[3:] in ONLY)}
        prev = [s for d in files.values() for s in d.get('spots', []) if s['passes'][PASS - 2] == 1]
        refs = sorted({r for s in prev for r in s['refs'] if r in parks})
        notice('2-fer bot', f'pass {PASS}: {len(prev)} spots from pass {PASS - 1}, {len(refs)} parks to download fresh')
        G, bad = download(parks, [r for r in refs if parks[r]['ids']], DET, PREC)
        saved_only = set()
        if REGION == 'world' and bad:   # not an ArcGIS map (France's IGN, Germany's BfN, Japan's A10…): only the saved copy exists
            sw = saved_world({r: parks[r] for r in bad})
            for r, g in sw.items(): G[r] = g; saved_only.add(r)
            bad -= saved_only
        counts['parks whose outline could not be read'] = len(bad)
        counts['parks with a saved copy only (no fresh download possible)'] = len(saved_only)
        pairs = {tuple(sorted(s['refs'][:2])) for s in prev}
        for s in prev:
            if len(s['refs']) > 2:
                rs = s['refs']; pairs |= {tuple(sorted((rs[i], rs[j]))) for i in range(len(rs)) for j in range(i + 1, len(rs))}
        pairs = {p for p in pairs if all((r in G) or (r in LN) for r in p)}
        spots = find_spots(G, LN, pairs, counts)
        newk = {}
        for s in spots: newk.setdefault(key_of(s), []).append(s)
        agree = new_only = 0
        for st, d in files.items():
            for s in d.get('spots', []):
                if s['passes'][PASS - 2] != 1: continue
                sb = bbox_lines([s['shape']])
                m = next((n for n in newk.get(key_of(s), []) if inter(sb, bbox_lines([n['shape']]), 0.0005)), None)
                if m:
                    s['passes'][PASS - 1] = 1; agree += 1
                    for k in ('center', 'shape', 'acres', 'wide_m', 'len_m'):
                        if k in m: s[k] = m[k]
                    m['_used'] = 1
                    s['status'] = f'pass {PASS}'
                else:
                    s['passes'][PASS - 1] = 0
                    s['status'] = f'dropped in pass {PASS}' + (' (an outline could not be downloaded)' if any(r in bad for r in s['refs']) else '')
                if PASS == 3 and m:
                    pin_ok = {r: pin_inside(r, PIN, G, LN) for r in s['refs']}
                    s['pins_inside'] = pin_ok
                    if any(r in saved_only for r in s['refs']): s['fresh'] = 'saved copy only for ' + ', '.join(r for r in s['refs'] if r in saved_only)
                    if all(pin_ok.values()):
                        s['status'] = 'candidate' if not s.get('fresh') else 'candidate (saved outline only)'
                        s['access'] = nearest_access(s, st_of)
                        s['maps'] = [[r, PIN[r][3]] for r in s['refs']]
                        s['names'] = {r: PIN[r][0] for r in s['refs']}
                    else: s['status'] = 'dropped: a pin is outside its own outline'
            d[f'pass{PASS}'] = today
            save_json(file_of(st), d, indent=1)
        new_only = sum(1 for v in newk.values() for n in v if not n.get('_used'))
        counts.update({'agree with the pass before': agree, 'new here only (not counted)': new_only})
    # report
    rep = {}
    RF = OUT / ('report.json' if REGION != 'world' else 'report-world.json')
    try: rep = json.load(open(RF))
    except Exception: pass  # noqa: BLE001
    per = {}
    for f in sorted(OUT.glob('*-*.json')):
        if not re.fullmatch(FILES, f.stem): continue
        sp = json.load(open(f)).get('spots', [])
        if sp: per[f.stem] = {'spots': len(sp), 'pass1': len(sp), 'pass2': sum(1 for s in sp if s['passes'][1]), 'candidates': sum(1 for s in sp if s['status'] == 'candidate'), 'candidates (saved outline only)': sum(1 for s in sp if s['status'] == 'candidate (saved outline only)'),
                              'n-fers': sum(1 for s in sp if len(s['refs']) > 2), 'lines': sum(1 for s in sp if s['kind'] != 'area')}
    rep['about'] = 'Counts from the 2-fer bot (kpc_fers.py). Hidden: data only.'
    rep[f'pass{PASS}'] = dict(counts, date=today, problems=LOG[:40])
    rep['per state'] = per
    save_json(RF, rep, indent=1)
    notice('2-fer bot', json.dumps({k: v for k, v in counts.items() if k != 'left out'})[:800])
    for l in LOG[:8]: notice('2-fer bot problem', l)


ABOUT = ("Spots where two or more POTA parks may share the same ground (official outlines only, 100 yards across; trails "
         "and rivers 100 yards long). HIDDEN, not reviewed: passes [saved, fresh, finest] must all be 1 and status "
         "'candidate' before a person looks. Wording when shown: 'We think these parks overlap. Check both boundaries "
         "yourself before you count it.'")

if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc()
        notice('2-fer bot', f'stopped: {e}')
    sys.exit(0)
