#!/usr/bin/env python3
"""kpc_master.py: trimmed outline MASTER RECORDS (one small trusted outline per POTA park) and the guards around them.

Plain words: a build should read a small file of already-checked park outlines instead of downloading a whole agency layer
every run. This module holds everything that keeps those files trustworthy:

  * the record format and the area files (data/outlines/<area>.geojson.gz),
  * the live-read gate (never-contact hosts, saved-copy-only hosts, robots.txt, per-host pacing),
  * the paged layer read (honors the layer's own maxRecordCount and exceededTransferLimit),
  * the completeness check (a short read FAILS CLOSED and never becomes the new baseline),
  * the refresh policy (read master first; re-read ONE layer only when it is old, edited, or its count is off),
  * the precedence rule (official beats approximate beats circle beats pin; never the other way round),
  * the licence guard (Protected Planet / WDPA geometry is never written to a public file).

Not a rule file: it never decides a park-to-land join, so it is listed in NOT_RULES (kpc_key_freeze.py) and does not move any
rules hash. Standard library only (a Shapefile or GDB input needs pyshp / ogr2ogr on the machine; the tool says so if missing).
"""
import copy, datetime, gzip, hashlib, json, math, os, pathlib, re, time, urllib.error, urllib.parse, urllib.request
from urllib import robotparser

FORMAT = 1
UA = 'KPC (kentuckyportableclub.github.io)'          # the same User-Agent the key builders use; never changed to get around a block
RANK = {'pin': 0, 'point-circle': 1, 'approximate': 2, 'official': 3}   # a higher rank is never replaced by a lower one
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUTLINES = ROOT / 'data' / 'outlines'
DECIMALS = 5                                           # ~1 m
DEFAULT_DETAIL = 0.0001                                # degrees (~11 m) line simplification kept in a master record
SHRINK_LIMIT = 0.90                                    # a layer whose count falls below 90% of its baseline is HELD, not accepted

# ---- hard rules about hosts --------------------------------------------------------------------------------------------
# (host, path prefix). Never contacted at all: not the layer, not even robots.txt.
NEVER_CONTACT = [('services.arcgis.com', '/33TOOklri9xpic7U'), ('ncnhde.natureserve.org', '')]
# services.arcgis.com and services<digits>.arcgis.com: no live read of any kind, robots.txt included.
# This is hard-coded (not only the env list) so a count run cannot reach those hosts.
ARCGIS_SERVICES_HOST_RE = re.compile(r'^services(?:\d+|-[a-z0-9]+)?\.arcgis\.com$')   # Nov 10: services, services2..9 and services-eu1 (any services-<region>) alike
# Saved copies only, no live read (their robots.txt answers 403). Same default list as kpc_us_key.py (KPC_SAVED_ONLY_HOSTS).
# services*.arcgis.com is also blocked in live_ok even if this list is overridden or emptied.
SAVED_ONLY_HOSTS = {h.strip().lower() for h in (os.environ.get('KPC_SAVED_ONLY_HOSTS') or
                                                'services.arcgis.com,services1.arcgis.com,apps.fs.usda.gov').split(',') if h.strip()}
HUB_RE = re.compile(r'(^|\.)(hub\.arcgis\.com|opendata\.arcgis\.com)$')   # hub portals: 60 s between requests
HUB_DELAY, HOST_DELAY = 60.0, 2.0
WDPA_RE = re.compile(r'wdpa|protected\s*-?planet|protectedplanet', re.I)


class MasterError(Exception): pass
class ShortRead(MasterError): pass          # fewer records than the layer itself reports
class ShrinkHeld(MasterError): pass         # the layer reports far fewer than its baseline: a person decides
class LiveNotAllowed(MasterError): pass     # a host or path the rules forbid
class LicenseBlocked(MasterError): pass     # WDPA / Protected Planet geometry
class LayerStall(MasterError): pass         # the server keeps sending the same page


def parts(url):
    u = urllib.parse.urlsplit(str(url).replace('svc:', '', 1).split('|')[0])
    return u.netloc.lower(), u.path


def is_arcgis_services_host(host):
    """True for services.arcgis.com and services<digits>.arcgis.com (services2, services9, ...)."""
    return bool(ARCGIS_SERVICES_HOST_RE.match((host or '').lower()))


def live_ok(url):
    """(True, '') or (False, why). Checked BEFORE every request, robots.txt included."""
    host, path = parts(url)
    for h, p in NEVER_CONTACT:
        if host == h and path.lower().startswith(p.lower()):
            return False, f'never contact {h}{p}: no request of any kind, robots.txt included'
    if is_arcgis_services_host(host):
        return False, f'{host}: services*.arcgis.com is never contacted, robots.txt included'
    if host in SAVED_ONLY_HOSTS:
        return False, f'{host}: saved copies only, no live read'
    return True, ''


def host_delay(host): return HUB_DELAY if HUB_RE.search(host) else HOST_DELAY


def is_wdpa(*texts): return any(WDPA_RE.search(str(t or '')) for t in texts)


# ---- pacing and robots --------------------------------------------------------------------------------------------------
class Pacer:
    """At least host_delay(host) seconds between two requests to the same host (60 s for hub portals). Clock and sleep can be swapped for tests."""
    def __init__(self, clock=time.monotonic, sleep=time.sleep): self.clock, self.sleep, self.last = clock, sleep, {}

    def wait(self, host):
        gap = host_delay(host); w = self.last.get(host, -1e9) + gap - self.clock()
        if w > 0: self.sleep(w)
        self.last[host] = self.clock()


def robots_allows(url, get_robots, cache=None):
    """get_robots(host_url) -> (status, text). 403 / 401 = disallow (a robots 403 is a 'no'). 404/410 = no file = allowed. 5xx / error = disallow."""
    u = urllib.parse.urlsplit(url); base = f'{u.scheme}://{u.netloc}'
    cache = cache if cache is not None else {}
    if base not in cache:
        try: st, txt = get_robots(base + '/robots.txt')
        except Exception: st, txt = 599, ''   # noqa: BLE001
        if st in (404, 410): cache[base] = True
        elif st == 200:
            rp = robotparser.RobotFileParser(); rp.parse(str(txt).splitlines()); cache[base] = rp
        else: cache[base] = False
    v = cache[base]
    return v if isinstance(v, bool) else v.can_fetch(UA, url)


def http_fetcher(pacer=None, max_tries=3):
    """The live fetch(url, params) -> dict used by read_layer. Every call goes through live_ok, robots.txt and the per-host pacer."""
    pacer, robots = pacer or Pacer(), {}

    def raw(url, timeout=60):
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        try:
            with checked_opener(hop).open(req, timeout=timeout) as r: return r.status, r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e: return e.code, ''

    def robots_get(url):
        ok, _ = live_ok(url)
        if not ok: raise LiveNotAllowed(url)
        pacer.wait(parts(url)[0])
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        try:
            with host_checked_opener().open(req, timeout=60) as r: return r.status, r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e: return e.code, ''

    def hop(u):   # Nov 10: a redirect hop gets the same checks as the first request (host rules, robots.txt, pacing)
        ok, why = live_ok(u)
        if not ok: raise LiveNotAllowed(f'redirect refused: {why}')
        if not robots_allows(u, robots_get, robots): raise LiveNotAllowed(f'redirect refused: {parts(u)[0]}: robots.txt does not allow this read')
        pacer.wait(parts(u)[0])

    def fetch(url, params=None):
        ok, why = live_ok(url)
        if not ok: raise LiveNotAllowed(why)
        if not robots_allows(url, robots_get, robots): raise LiveNotAllowed(f'{parts(url)[0]}: robots.txt does not allow this read')
        full = url + ('?' + urllib.parse.urlencode(params) if params else '')
        last = None
        for i in range(max_tries):
            pacer.wait(parts(url)[0])
            try:
                st, txt = raw(full)
                if st == 200: return json.loads(txt)
                last = f'HTTP {st}'
            except (urllib.error.URLError, ValueError, OSError) as e: last = str(e)
            time.sleep(8 * (i + 1))
        raise MasterError(f'{full[:120]}: {last}')
    return fetch


# ---- paged layer read + completeness ------------------------------------------------------------------------------------
def layer_info(url, fetch):
    """What the layer says about itself: page limit, id field, last edit, and its own total (returnCountOnly)."""
    info = fetch(url, {'f': 'json'})
    cnt = fetch(url.rstrip('/') + '/query', {'where': '1=1', 'returnCountOnly': 'true', 'f': 'json'})
    if 'count' not in cnt: raise MasterError(f"{url}: the layer did not report its own count ({str(cnt)[:120]})")
    return {'maxRecordCount': int(info.get('maxRecordCount') or 1000), 'oid_field': info.get('objectIdField') or 'OBJECTID',
            'last_edit': (info.get('editingInfo') or {}).get('lastEditDate'), 'count': int(cnt['count']), 'name': info.get('name')}


def read_layer(url, fetch, want_page=500, out_fields='*', max_pages=5000):
    """Read every feature of an ArcGIS layer. The page size is min(want_page, the layer's own maxRecordCount) - asking for more than the
    layer allows is what truncated the Nov 3 saved copies (page 500 on a layer that sends 200: the first page was taken for the last).
    Continues while the server says exceededTransferLimit, OR while it has sent fewer than its own total. Stops on an empty page.
    Always ends with the completeness check; a short read raises ShortRead and returns nothing."""
    info = layer_info(url, fetch)
    page = max(1, min(int(want_page), info['maxRecordCount']))
    feats, off, seen_first, pages = [], 0, set(), 0
    while True:
        pages += 1
        if pages > max_pages: raise LayerStall(f'{url}: more than {max_pages} pages')
        j = fetch(url.rstrip('/') + '/query', {'where': '1=1', 'outFields': out_fields, 'returnGeometry': 'true', 'outSR': 4326, 'f': 'json',
                                                'resultOffset': off, 'resultRecordCount': page, 'orderByFields': info['oid_field']})
        if 'error' in j: raise MasterError(f"{url}: the layer answered an error ({str(j['error'])[:160]})")
        fs = j.get('features') or []
        if not fs: break
        first = json.dumps((fs[0].get('attributes') or {}).get(info['oid_field']), default=str)
        if off and first in seen_first: raise LayerStall(f'{url}: the server sent the page at offset {off} again (resultOffset ignored?)')
        seen_first.add(first)
        feats += fs; off += len(fs)
        if len(feats) >= info['count']: break
        # exceededTransferLimit, or fewer than a full page while the layer says there is more (the server clamped the page): keep going.
        # Only an empty page, or having every record the layer reports, ends the loop.
    check_complete(info['count'], len(feats), url)
    return feats, info


def check_complete(expected, got, label=''):
    """Fail closed. expected is what the LAYER reports (returnCountOnly / numberMatched), never our own earlier count."""
    if expected is None: raise ShortRead(f'{label}: the layer did not report a total, so the read cannot be checked: refused')
    if got < expected: raise ShortRead(f'{label}: read {got} of {expected} records the layer reports: SHORT, nothing is saved')
    return True


# ---- geometry (GeoJSON, longitude / latitude) -----------------------------------------------------------------------------
def _area(r): return sum((r[i][0] * r[(i + 1) % len(r)][1] - r[(i + 1) % len(r)][0] * r[i][1]) for i in range(len(r))) / 2


def _pip_ring(x, y, r):
    ins = False; j = len(r) - 1
    for i in range(len(r)):
        xi, yi, xj, yj = r[i][0], r[i][1], r[j][0], r[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-18) + xi: ins = not ins
        j = i
    return ins


def polys_of(g):
    """GeoJSON geometry -> list of polygons, each a list of rings."""
    if not g: return []
    t = g.get('type')
    if t == 'Polygon': return [g['coordinates']]
    if t == 'MultiPolygon': return list(g['coordinates'])
    return []


def contains(g, lon, lat):
    for poly in polys_of(g):
        if poly and _pip_ring(lon, lat, poly[0]) and not any(_pip_ring(lon, lat, h) for h in poly[1:]): return True
    return False


def bbox_of(g):
    pts = [p for poly in polys_of(g) for ring in poly for p in ring]
    if not pts and g and g.get('type') == 'Point': pts = [g['coordinates']]
    if not pts: return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def esri_to_geojson(g):
    """Esri JSON geometry {rings:[...]} / {x,y} -> GeoJSON. Coordinates must already be longitude / latitude (outSR 4326): anything else is refused."""
    if not g: return None
    if 'x' in g and 'y' in g:
        if abs(g['x']) > 180 or abs(g['y']) > 90: raise MasterError('geometry is not in longitude / latitude (ask the layer for outSR=4326)')
        return {'type': 'Point', 'coordinates': [g['x'], g['y']]}
    rings = g.get('rings')
    if not rings: return None
    for r in rings:
        for p in r:
            if abs(p[0]) > 180 or abs(p[1]) > 90: raise MasterError('geometry is not in longitude / latitude (ask the layer for outSR=4326)')
    outers, holes = [], []
    for r in rings:
        if len(r) < 4: continue
        (outers if _area(r) < 0 else holes).append(r)   # Esri: clockwise = outer ring (negative signed area in x/y)
    if not outers: outers, holes = holes, []
    polys = [[o] for o in outers]
    for h in holes:
        for poly in polys:
            if _pip_ring(h[0][0], h[0][1], poly[0]): poly.append(h); break
    return {'type': 'Polygon', 'coordinates': polys[0]} if len(polys) == 1 else {'type': 'MultiPolygon', 'coordinates': polys}


def _dp(pts, tol):
    if len(pts) < 3: return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]; dx, dy = x2 - x1, y2 - y1; n = math.hypot(dx, dy)
    best, idx = -1, 0
    for i in range(1, len(pts) - 1):
        d = math.hypot(pts[i][0] - x1, pts[i][1] - y1) if n == 0 else abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / n
        if d > best: best, idx = d, i
    if best <= tol: return [pts[0], pts[-1]]
    return _dp(pts[:idx + 1], tol)[:-1] + _dp(pts[idx:], tol)


def trim_geometry(g, detail=DEFAULT_DETAIL):
    """Round to 5 decimals and simplify each ring to `detail` degrees. A ring that would collapse keeps its original points."""
    if not g or g.get('type') == 'Point':
        return {'type': 'Point', 'coordinates': [round(c, DECIMALS) for c in g['coordinates']]} if g else None
    out = []
    for poly in polys_of(g):
        rs = []
        for ring in poly:
            r = [[round(p[0], DECIMALS), round(p[1], DECIMALS)] for p in ring]
            s = _dp(r[:-1], detail) + [r[0]] if detail else r
            rs.append(s if len(s) >= 4 else r)
        out.append(rs)
    return {'type': 'Polygon', 'coordinates': out[0]} if len(out) == 1 else {'type': 'MultiPolygon', 'coordinates': out}


def circle(lat, lon, meters):
    """A 24-sided circle around a pin (g = 'point-circle'). The pin itself is never moved."""
    dlat = meters / 111320.0; dlon = meters / (111320.0 * max(0.2, math.cos(math.radians(lat))))
    ring = [[round(lon + dlon * math.cos(2 * math.pi * i / 24), DECIMALS), round(lat + dlat * math.sin(2 * math.pi * i / 24), DECIMALS)] for i in range(24)]
    return {'type': 'Polygon', 'coordinates': [ring + [ring[0]]]}


# ---- records ------------------------------------------------------------------------------------------------------------
def content_hash(rec):
    core = {'ref': rec['ref'], 'g': rec['g'], 'geometry': rec['geometry'], 'record_ids': sorted(map(str, rec.get('record_ids') or []))}
    return hashlib.sha256(json.dumps(core, sort_keys=True, separators=(',', ':')).encode()).hexdigest()[:32]


def make_record(ref, name, g, geometry, agency, layer_url, record_ids, source_count, date_read, license_, via, detail=DEFAULT_DETAIL, **extra):
    if g not in RANK: raise MasterError(f'g must be one of {sorted(RANK)}, not {g!r}')
    rec = {'ref': ref, 'name': name, 'g': g, 'geometry': geometry, 'agency': agency, 'layer_url': layer_url,
           'record_ids': [str(x) for x in record_ids], 'source_count': int(source_count), 'date_read': date_read,
           'license': license_, 'via': via, 'detail': detail}
    rec.update(extra); rec['hash'] = content_hash(rec); return rec


def assert_public_safe(rec):
    """A record that came from, or points at, Protected Planet / WDPA never reaches a public file."""
    if is_wdpa(rec.get('agency'), rec.get('layer_url'), rec.get('license'), rec.get('name'), rec.get('via'), rec.get('source'), rec.get('layer_key')):
        raise LicenseBlocked(f"{rec.get('ref')}: Protected Planet / WDPA geometry cannot go into the public repo or pages (licence); use wdpa-lookup for the managing agency only")
    return True


def merge(existing, new):
    """Return (record_to_keep, what). Official always wins over approximate; never overwrite a higher kind with a lower one.
    Same kind from the SAME layer = a refresh (replace). Same kind from ANOTHER layer = keep what is there, report a conflict."""
    if existing is None: return new, 'added'
    re_, rn = RANK[existing['g']], RANK[new['g']]
    if rn < re_: return existing, f"kept {existing['g']} (a {new['g']} never replaces it)"
    if rn > re_: return new, f"replaced {existing['g']} with {new['g']}"
    if existing['layer_url'] == new['layer_url']:
        return (new, 'refreshed') if existing['hash'] != new['hash'] else (existing, 'unchanged')
    return existing, 'conflict: same kind from another layer, kept the saved one (person to decide)'


def area_path(area, root=None): return pathlib.Path(root or OUTLINES) / f'{area}.geojson.gz'


def load_area(area, root=None):
    p = area_path(area, root)
    if not p.exists(): return {}
    with gzip.open(p, 'rt', encoding='utf-8') as f: doc = json.load(f)
    return {ft['properties']['ref']: dict(ft['properties'], geometry=ft['geometry']) for ft in doc.get('features', [])}


def save_area(area, recs, root=None):
    """Deterministic bytes (sorted refs, gzip mtime 0): an unchanged area is a byte-identical file, so git shows no change."""
    for r in recs.values(): assert_public_safe(r)
    feats = [{'type': 'Feature', 'id': ref, 'properties': {k: v for k, v in recs[ref].items() if k != 'geometry'}, 'geometry': recs[ref]['geometry']}
             for ref in sorted(recs)]
    doc = {'type': 'FeatureCollection', 'kpc': {'format': FORMAT, 'area': area}, 'features': feats}
    p = area_path(area, root); p.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(doc, separators=(',', ':'), sort_keys=True).encode()
    with open(p, 'wb') as fh, gzip.GzipFile(fileobj=fh, mode='wb', mtime=0, compresslevel=9) as z: z.write(raw)
    return p


# ---- matching (the trim step) --------------------------------------------------------------------------------------------
REF_RE = re.compile(r'^[A-Z]{1,3}-\d{3,5}$')
_STOP = {'the', 'of', 'and', 'a', 'at', 'state', 'national', 'park', 'wma', 'wildlife', 'management', 'area', 'nwr', 'refuge', 'forest', 'sra', 'sp', 'np', 'nf'}


def norm_name(s):
    import unicodedata
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    return [t for t in re.sub(r'[^a-z0-9 ]+', ' ', s).split() if t not in _STOP]


def names_agree(a, b):
    ta, tb = set(norm_name(a)), set(norm_name(b))
    if not ta or not tb: return False
    if ta == tb: return True
    return min(len(ta), len(tb)) >= 2 and (ta <= tb or tb <= ta)   # a one-word name must match exactly; a longer one may be a part of the other


class Grid:
    """A 0.25 degree grid over feature bounding boxes, so 13,000 pins are not tested against 100,000 outlines one by one."""
    def __init__(self, geoms, cell=0.25):
        self.cell, self.cells, self.bb = cell, {}, []
        for i, g in enumerate(geoms):
            b = bbox_of(g); self.bb.append(b)
            if not b: continue
            for cx in range(int(b[0] // cell), int(b[2] // cell) + 1):
                for cy in range(int(b[1] // cell), int(b[3] // cell) + 1): self.cells.setdefault((cx, cy), []).append(i)

    def near(self, lon, lat, pad=0.0):
        """Features whose bounding box (grown by `pad` degrees) holds the point."""
        c = self.cell; cells = {(cx, cy) for cx in range(int((lon - pad) // c), int((lon + pad) // c) + 1) for cy in range(int((lat - pad) // c), int((lat + pad) // c) + 1)}
        out = sorted({i for k in cells for i in self.cells.get(k, [])})
        return [i for i in out if self.bb[i][0] - pad <= lon <= self.bb[i][2] + pad and self.bb[i][1] - pad <= lat <= self.bb[i][3] + pad]


def trim(parks, feats, cfg, date_read=None, source_count=None):
    """parks: [(ref, name, lat, lon)]. feats: [{'attributes'/'properties': {...}, 'geometry': GeoJSON}]. cfg: layer settings
    (id_fields, name_fields, record_id_field, g, agency, layer_url, license, detail, circle_m).
    Returns (records {ref: record}, queue [rows]). ONLY matched park geometry is kept. The queue holds the parks a person must look at: ambiguous names, a pin inside an outline whose name does not agree, a pin just outside a same-name outline.
    A park this layer simply does not cover is not queued (it is another layer's job).
    Match order: the layer's own id fields first, then name + pin inside. A pin is read, never moved."""
    date_read = date_read or datetime.date.today().isoformat()
    source_count = len(feats) if source_count is None else source_count
    prop = lambda f: f.get('properties') if 'properties' in f else f.get('attributes') or {}
    by_ref = {p[0]: p for p in parks}
    geoms = [f.get('geometry') for f in feats]
    recs, queue, used = {}, [], set()

    def rid(f, i):
        v = prop(f).get(cfg.get('record_id_field') or '')
        return str(v) if v not in (None, '') else f'row{i}'

    def build(ref, idx, via):
        gs = [geoms[i] for i in idx]
        polys = [pl for g in gs for pl in polys_of(g)]
        geom = (None if not polys else {'type': 'Polygon', 'coordinates': polys[0]} if len(polys) == 1 else {'type': 'MultiPolygon', 'coordinates': polys})
        g = cfg.get('g', 'official')
        if geom is None and gs and gs[0] and gs[0].get('type') == 'Point':
            geom = circle(by_ref[ref][2], by_ref[ref][3], cfg['circle_m']) if cfg.get('circle_m') else gs[0]
            g = 'point-circle' if cfg.get('circle_m') else 'pin'
        if geom is None: return None
        return make_record(ref, by_ref[ref][1], g, trim_geometry(geom, cfg.get('detail', DEFAULT_DETAIL)), cfg.get('agency', ''), cfg.get('layer_url', ''),
                           [rid(feats[i], i) for i in idx], source_count, date_read, cfg.get('license', ''), via, cfg.get('detail', DEFAULT_DETAIL))

    # 1) the layer's own id fields
    ids = {}
    for i, f in enumerate(feats):
        for fld in cfg.get('id_fields') or []:
            v = str(prop(f).get(fld) or '').strip().upper().replace(' ', '')
            if REF_RE.match(v) and v in by_ref: ids.setdefault(v, []).append(i)
    for ref, idx in ids.items():
        r = build(ref, idx, 'id');
        if r: recs[ref] = r; used.add(ref)
    # 2) name + pin inside, for the rest
    ext = None
    bbs = [b for b in (bbox_of(g) for g in geoms) if b]
    if bbs: ext = (min(b[0] for b in bbs) - .05, min(b[1] for b in bbs) - .05, max(b[2] for b in bbs) + .05, max(b[3] for b in bbs) + .05)
    grid = Grid(geoms)
    for ref, name, lat, lon in parks:
        if ref in used: continue
        if not ext or not (ext[0] <= lon <= ext[2] and ext[1] <= lat <= ext[3]): continue   # outside this layer's reach: not this layer's miss
        near = [i for i in grid.near(lon, lat) if contains(geoms[i], lon, lat)]
        fields = cfg.get('name_fields') or []
        if not near:
            # Nothing in this layer holds the pin. That is usually just "not in this layer", so it is NOT queued - unless an outline with the park's
            # name lies within ~0.1 degree (a pin that sits just off its own boundary): that one a person should look at.
            close = [i for i in grid.near(lon, lat, 0.1) if any(names_agree(name, prop(feats[i]).get(nf)) for nf in fields)]
            if close: queue.append({'ref': ref, 'name': name, 'lat': lat, 'lon': lon, 'why': 'a same-name outline is nearby but the pin is outside it',
                                    'candidates': '; '.join(sorted({str(prop(feats[i]).get(fields[0])) for i in close})[:6])})
            continue
        hit = [i for i in near if any(names_agree(name, prop(feats[i]).get(nf)) for nf in fields)]
        if not hit:
            cands = '; '.join(sorted({str(prop(feats[i]).get(fields[0]) if fields else rid(feats[i], i)) for i in near})[:6])
            queue.append({'ref': ref, 'name': name, 'lat': lat, 'lon': lon, 'why': 'pin is inside an outline but no name agrees', 'candidates': cands}); continue
        names = {tuple(norm_name(prop(feats[i]).get(fields[0]))) for i in hit} if fields else set()
        if len(names) > 1:
            queue.append({'ref': ref, 'name': name, 'lat': lat, 'lon': lon, 'why': 'ambiguous: more than one outline name fits',
                          'candidates': '; '.join(sorted({str(prop(feats[i]).get(fields[0])) for i in hit})[:6])}); continue
        r = build(ref, hit, 'name+pin')
        if r: recs[ref] = r
    return recs, queue


# ---- the layers manifest (expected counts) and the refresh policy -------------------------------------------------------
def load_json(p, default):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return default   # noqa: BLE001


def layers_path(root=None): return pathlib.Path(root or OUTLINES) / 'layers.json'


def load_layers(root=None): return load_json(layers_path(root), {'format': FORMAT, 'layers': {}})


def save_layers(doc, root=None):
    p = layers_path(root); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, indent=1, sort_keys=True) + '\n', encoding='utf-8')


def accept_baseline(doc, key, entry, count, accept_shrink=False):
    """Record `count` (what the layer itself reported, on a COMPLETE read) as the layer's expected count. A short read never gets here
    (read_layer raised). A layer whose total fell below 90% of the old baseline is held until a person passes accept_shrink."""
    old = (doc['layers'].get(key) or {}).get('expected_count')
    if old and count < SHRINK_LIMIT * old and not accept_shrink:
        raise ShrinkHeld(f'{key}: the layer now reports {count}, baseline was {old} (under {int(SHRINK_LIMIT * 100)}%): held, the baseline is unchanged')
    doc['layers'][key] = dict(doc['layers'].get(key) or {}, **entry, expected_count=int(count))
    return doc


def plan(doc, now, max_days, probe, areas=None):
    """Read master first. For each layer decide: use-master, re-read (with the reason), or saved-only (no live read allowed).
    probe(layer) -> {'count':..., 'last_edit':...} or None (not allowed / no answer). Only the layers that need it are marked: one layer, not a state."""
    out = []
    for key, L in sorted(doc.get('layers', {}).items()):
        if areas and not (set(areas) & set(L.get('areas') or [])): continue
        ok, why = live_ok(L.get('url', ''))
        age = None
        try: age = (now - datetime.datetime.fromisoformat(L['read_date']).replace(tzinfo=datetime.timezone.utc)).total_seconds() / 86400
        except Exception: pass   # noqa: BLE001
        if age is None:
            out.append({'layer': key, 'action': 'saved-only-missing' if not ok else 're-read', 'reason': 'no master yet' + ('' if ok else f' and {why}')}); continue
        if not ok:
            out.append({'layer': key, 'action': 'use-master', 'reason': f'{why}; master is {age:.0f} days old' + (' (OLD: needs a saved copy refresh)' if age > max_days else '')}); continue
        if age > max_days: out.append({'layer': key, 'action': 're-read', 'reason': f'(a) master is {age:.0f} days old (limit {max_days})'}); continue
        live = probe(L)
        if live is None: out.append({'layer': key, 'action': 'use-master', 'reason': 'could not ask the layer; master is within the limit'}); continue
        if live.get('last_edit') and live['last_edit'] != L.get('last_edit'): out.append({'layer': key, 'action': 're-read', 'reason': '(b) lastEditDate changed'}); continue
        if live.get('count') is not None and live['count'] != L.get('expected_count'):
            out.append({'layer': key, 'action': 're-read', 'reason': f"(c) count check: layer reports {live['count']}, manifest has {L.get('expected_count')}"}); continue
        out.append({'layer': key, 'action': 'use-master', 'reason': f'fresh ({age:.0f} days), edit date and count unchanged'})
    return out


# ---- raw files: a manifest, never the files ---------------------------------------------------------------------------------
RAW_EXT = {'.gdb', '.shp', '.dbf', '.shx', '.zip', '.gpkg', '.7z', '.tar', '.tgz'}   # big layer downloads: never tracked
RAW_MAX = 5 * 1024 * 1024


def sha256_file(p, buf=1 << 20):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(buf), b''): h.update(b)
    return h.hexdigest()


def raw_manifest_path(root=None): return pathlib.Path(root or OUTLINES) / 'raw-manifest.json'


def raw_add(path, source, date=None, root=None):
    p = pathlib.Path(path); doc = load_json(raw_manifest_path(root), {'format': FORMAT, 'files': []})
    row = {'name': p.name, 'size': p.stat().st_size, 'sha256': sha256_file(p), 'source': source, 'date': date or datetime.date.today().isoformat()}
    doc['files'] = [r for r in doc['files'] if r['name'] != row['name']] + [row]; doc['files'].sort(key=lambda r: r['name'])
    raw_manifest_path(root).parent.mkdir(parents=True, exist_ok=True)
    raw_manifest_path(root).write_text(json.dumps(doc, indent=1, sort_keys=True) + '\n', encoding='utf-8'); return row


def raw_add_facts(facts, root=None):
    """Nov 10: one raw-manifest row from facts already measured elsewhere (import-existing, an official-file download): name, size,
    sha256, source, date and the record count when known. Facts only: no licence or terms text goes in."""
    row = {k: facts.get(k) for k in ('name', 'size', 'sha256', 'source', 'date', 'count') if facts.get(k) not in (None, '')}
    doc = load_json(raw_manifest_path(root), {'format': FORMAT, 'files': []})
    doc['files'] = [r for r in doc['files'] if r['name'] != row['name']] + [row]; doc['files'].sort(key=lambda r: r['name'])
    raw_manifest_path(root).parent.mkdir(parents=True, exist_ok=True)
    raw_manifest_path(root).write_text(json.dumps(doc, indent=1, sort_keys=True) + '\n', encoding='utf-8'); return row


def raw_in_repo(files):
    """files: [(path, size)] tracked by git. Returns the ones that must not be there: layer downloads by type, a .gdb folder, or any file
    under data/outlines/ over 5 MB (a master area file is small by design)."""
    bad = []
    for f, size in files:
        low = str(f).replace('\\', '/').lower()
        if pathlib.Path(low).suffix in RAW_EXT or '.gdb/' in low or (low.startswith('data/outlines/') and size > RAW_MAX): bad.append(f)
    return bad


# ---- completeness of a SAVED copy (the cache the key builders read) ------------------------------------------------------------
def check_saved_cache(path, expected):
    """A saved copy is short when its actual record list (recs) is shorter than the baseline.
    The baseline is the complete published live-key count (US: counts.padus; world: counts.areas).
    Do not use the cache 'seen' / 'read' field: that is a different counter and can be larger than len(recs)."""
    with gzip.open(path, 'rt', encoding='utf-8') as f: blob = json.load(f)
    recs = blob.get('recs')
    got = len(recs) if isinstance(recs, list) else 0
    check_complete(expected, got, str(path)); return got


# ---- WDPA: managing-agency lookup, never geometry --------------------------------------------------------------------------------
PRIVATE_FORBIDDEN = ('data', 'docs', 'app', 'img', 'photos', 'tests', '.github')


def private_path_ok(path, repo_root=None):
    """The lookup file must live OUTSIDE the repo's published folders (and outside the repo root's files). Returns (ok, why)."""
    rr = pathlib.Path(repo_root or ROOT).resolve(); p = pathlib.Path(path).resolve()
    try: rel = p.relative_to(rr)
    except ValueError: return True, ''
    return False, f'{rel} is inside the repo; the managing-agency lookup is private: write it outside the repo (e.g. ~/kpc-private/)'


def wdpa_agency_lookup(rows):
    """rows: WDPA attribute rows (dicts). Keeps ONLY id, name, managing authority, owner type, designation, and the POTA ref if there is one. No geometry, no coordinates."""
    keep = ('WDPAID', 'WDPA_PID', 'NAME', 'ORIG_NAME', 'DESIG', 'DESIG_ENG', 'MANG_AUTH', 'MANG_PLAN', 'OWN_TYPE', 'GOV_TYPE', 'PARENT_ISO', 'ISO3', 'STATUS')
    return [{k: r.get(k) for k in keep if k in r} for r in rows]


# ==== Nov 10 (the master owns the saved copies): the needs-download list, layer files, the keep-bigger merge ==========
# Plain words. ONE list says which layers somebody must download. It lives in KPC-Data (data/needs-download.json) because the
# hunters and the engine write there. The master step in this repo reads it and adds its own rows through the boundary-cache
# release (asset needs-download.json, same schema), which KPC-Data's hourly copy job merges into the one file.
#   who = 'bot'     the master downloads it itself (allowed host, robots.txt says yes)
#         'person' a person downloads it in a browser (saved-copy-only host, services*.arcgis.com, or robots.txt says no / 403)
#         'never'   nobody contacts it (never-contact host); the saved copy is kept as it is
NEEDS_FORMAT = 1
NEEDS_FIELDS = ('id', 'area', 'layer', 'url', 'page', 'host', 'who', 'why', 'expected', 'have', 'source', 'added', 'status', 'note',
                'src', 'check')   # Nov 10 (change check): src = the download source id in data/outlines/download-sources.json; check = bot | person
NEEDS_STATUS = ('open', 'done', 'held')


def who_for(url, robots_ok=None, file_url=None):
    """('bot' | 'person' | 'never', why). robots_ok(url) -> bool is only asked for a host live_ok allows (never before it).
    Nov 10: when the layer itself may not be read but its OFFICIAL DIRECT FILE (file_url) sits on a host a bot may fetch, the row
    is a bot's: the master step downloads the file through the same pre-request check, robots.txt and pacing (download_official_file)."""
    host, path = parts(url)
    for h, p in NEVER_CONTACT:
        if host == h and path.lower().startswith(p.lower()): return 'never', f'never contact {h}{p}: no request of any kind, by a bot or a person'
    ok, why = live_ok(url)
    if ok and (robots_ok is None or robots_ok(url)): return 'bot', ''
    if not ok: why = why + ': a person downloads it in a browser'
    else: why = f'{host}: robots.txt does not allow a bot to read it (a 403 counts as no): a person downloads it'
    if file_url:
        fok, _ = live_ok(file_url)
        if fok and (robots_ok is None or robots_ok(file_url)):
            return 'bot', f'the official direct file is on {parts(file_url)[0]}, which a bot may fetch: the master step downloads it'
    return 'person', why


def direct_file_of(row):
    """The official direct file a needs row names ('direct file: <url>' in its note), or None."""
    m = re.search(r'direct file:\s*(\S+)', str((row or {}).get('note') or ''))
    return m.group(1) if m else None


class _CheckedRedirect(urllib.request.HTTPRedirectHandler):
    """Nov 10: every redirect hop goes through check(new_url) BEFORE it is followed (the same pre-request host check, and robots.txt
    for the main fetch). A hop onto a host the rules forbid raises LiveNotAllowed: nothing is requested from it."""
    def __init__(self, check):
        super().__init__(); self.check = check

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        newurl = urllib.parse.urljoin(req.full_url, newurl)
        self.check(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _refuse_hop(u):
    ok, why = live_ok(u)
    if not ok: raise LiveNotAllowed(f'redirect refused: {why}')


def host_checked_opener(handlers=()):
    """An opener that refuses any redirect hop onto a host live_ok forbids (robots.txt reads, HEAD checks)."""
    return checked_opener(_refuse_hop, handlers)


def checked_opener(check, handlers=()):
    """A urllib opener whose every redirect hop is checked (see _CheckedRedirect). handlers: stand-ins for tests."""
    return urllib.request.build_opener(_CheckedRedirect(check), *handlers)


def download_official_file(url, dest, robots_get=None, pacer=None, handlers=(), max_bytes=2 << 30):
    """Nov 10: the official-file download path. live_ok first (never a services*.arcgis.com host, never a never-contact host,
    nothing saved-copy-only), then robots.txt (a 403 = no), then the per-host pacer (60 s on hub portals). EVERY redirect hop is
    checked the same way before it is followed (live_ok + robots.txt + pacing; a robots.txt redirect gets live_ok), and the final
    address is checked again. Streams the file to dest and returns its raw facts {name, size, sha256, source, date}. Raises
    LiveNotAllowed before any request it may not make. Only the master step calls it, and only when asked (--official-files,
    the fresh-start run)."""
    ok, why = live_ok(url)
    if not ok: raise LiveNotAllowed(why)
    pacer = pacer or Pacer(); robots_cache = {}

    def host_check(u):
        ok_, why_ = live_ok(u)
        if not ok_: raise LiveNotAllowed(f'redirect refused: {why_}')
    robots_opener = checked_opener(host_check, handlers)
    if robots_get is None:
        def robots_get(u):
            host_check(u); pacer.wait(parts(u)[0])
            try:
                with robots_opener.open(urllib.request.Request(u, headers={'User-Agent': UA}), timeout=30) as r: return r.status, r.read(200000).decode('utf-8', 'replace')
            except urllib.error.HTTPError as e: return e.code, ''

    def hop_check(u):   # a redirect hop of the file itself: the same three checks as the first request
        host_check(u)
        if not robots_allows(u, robots_get, robots_cache): raise LiveNotAllowed(f'redirect refused: {parts(u)[0]}: robots.txt does not allow this download')
        pacer.wait(parts(u)[0])
    if not robots_allows(url, robots_get, robots_cache): raise LiveNotAllowed(f'{parts(url)[0]}: robots.txt does not allow this download')
    pacer.wait(parts(url)[0])
    dest = pathlib.Path(dest); dest.parent.mkdir(parents=True, exist_ok=True); h = hashlib.sha256(); n = 0
    tmp = dest.with_name(dest.name + '.part')
    try:
        with checked_opener(hop_check, handlers).open(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=300) as r:
            final = r.geturl() or url
            if not live_ok(final)[0]: raise LiveNotAllowed(f'final address refused: {live_ok(final)[1]}')
            with open(tmp, 'wb') as f:
                while True:
                    b = r.read(1 << 20)
                    if not b: break
                    n += len(b)
                    if n > max_bytes: raise MasterError(f'{url[:100]}: larger than {max_bytes} bytes; stopped')
                    h.update(b); f.write(b)
    except BaseException:
        tmp.unlink(missing_ok=True); raise
    tmp.replace(dest)
    return {'name': dest.name, 'size': n, 'sha256': h.hexdigest(), 'source': url, 'date': datetime.date.today().isoformat()}


def saved_counts(path):
    """Read only. {layer: records} of one saved copy: US-XX = OBJECTID prefix ('' = PAD-US); CA-ALL = the oid's layer id (the first
    12 letters of the source label, '~N' for the next layers of that label) and the source label itself; W-XX = the source label."""
    out = {}
    try: blob = load_saved(path)
    except Exception: return out  # noqa: BLE001
    name = pathlib.Path(path).name
    for r in blob.get('recs') or []:
        if name.startswith('US-'): ks = [prefix_of(r.get('OBJECTID'))]
        elif name.startswith('CA-'): ks = {str(r.get('oid', '')).split(':', 1)[0] if ':' in str(r.get('oid', '')) else 'cpcad', 'src:' + str(r.get('src') or '')}
        else: ks = ['src:' + str(r.get('src') or '')]
        for k in ks: out[k] = out.get(k, 0) + 1
    return out


def joined_missing(key_path, blob):
    """Nov 10 (actually missing): {prefix: n} of record ids the live key (data/us-key/US-XX.json) joins a park to that the saved copy
    does not hold. Only these make a layer 'needed'; a short copy whose missing records sit in no joined layer asks no one."""
    try: pk = (load_json(key_path, {}) or {}).get('parks') or {}
    except Exception: return {}  # noqa: BLE001
    have = {str(r.get('OBJECTID')) for r in blob.get('recs') or []}
    out = {}
    for q in pk.values():
        ids = [x[0] for x in q.get('m') or [] if isinstance(x, list) and x]
        bk = q.get('bk')
        if isinstance(bk, list) and bk and not isinstance(bk[0], (list, dict)): ids.append(bk[0])
        for i in ids:
            i = str(i)
            if i and i not in have:
                p = prefix_of(i)
                if p in ('trl',): continue   # trail lines live in data/trails, not in the saved copy
                out[p] = out.get(p, 0) + 1
    return out


def needs_key(row): return f"{row.get('area')}|{row.get('layer')}"


def needs_row(area, layer, url, why, source, who=None, expected=None, have=None, page=None, date=None, note='', src='', check=''):
    w, w_why = who_for(url) if who is None else (who, '')
    row = {'id': f'{area}|{layer}', 'area': area, 'layer': layer, 'url': str(url or ''), 'page': page or official_page(url), 'host': parts(url)[0],
           'who': w, 'why': why + (f' ({w_why})' if w_why and w_why not in why else ''), 'expected': expected, 'have': have, 'source': source,
           'added': date or datetime.date.today().isoformat(), 'status': 'open', 'note': note, 'src': src, 'check': check}
    return row


def official_page(url):
    """The page a PERSON opens for a layer: the agency's own open-data search on ArcGIS Hub for a hosted (services*.arcgis.com) layer,
    else the layer's own REST page (most agency servers show an 'Export' / 'Query' link there). Never fetched by a bot here."""
    u = str(url or '').replace('svc:', '', 1).split('|')[0]
    u = re.sub(r'/query/?$', '', u)
    host, path = parts(u)
    if is_arcgis_services_host(host):
        m = re.search(r'/services/([^/]+)/(?:Feature|Map)Server', path)
        if m: return 'https://hub.arcgis.com/search?q=' + urllib.parse.quote(m.group(1).replace('_', ' '))
    return u


def load_needs(path):
    doc = load_json(path, None)
    if not isinstance(doc, dict) or not isinstance(doc.get('rows'), list): doc = {'format': NEEDS_FORMAT, 'about': NEEDS_ABOUT, 'rows': []}
    return doc


NEEDS_ABOUT = ('Layers somebody must download for the saved copies. who=bot: the master step downloads it; who=person: the PC helper '
               '(KPC-Links tools/kpc_pc_helper.py) opens the official page in a browser; who=never: nobody contacts it. Hunters and the '
               'engine only add rows here; only the master step saves layers. One row per area|layer.')


def merge_needs(doc, rows):
    """Add or update rows by area|layer. A row that is already done stays done unless the new row says a NEWER need (a later date);
    a held row stays held unless the change check reopens it.
    Returns (doc, added, updated). Deterministic order (sorted by id)."""
    have = {needs_key(r): r for r in doc.get('rows') or []}
    added = updated = 0
    for r in rows:
        r = {k: r.get(k) for k in NEEDS_FIELDS}
        r['id'] = needs_key(r); k = r['id']; old = have.get(k)
        if old is None: have[k] = r; added += 1; continue
        if old.get('status') == 'done' and r.get('status') != 'done' and str(r.get('added') or '') <= str(old.get('added') or ''): continue
        if old.get('status') == 'held' and r.get('status') == 'open' and r.get('source') != 'change check': continue   # a held row stays held (a person decides); only a changed source reopens it
        new = dict(old)
        for f in NEEDS_FIELDS:
            if f == 'added': continue
            if r.get(f) not in (None, ''): new[f] = r[f]
        if new != old: have[k] = new; updated += 1
    doc['rows'] = [have[k] for k in sorted(have)]
    doc['format'] = NEEDS_FORMAT; doc.setdefault('about', NEEDS_ABOUT)
    return doc, added, updated


def save_needs(doc, path):
    p = pathlib.Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    new = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + '\n'
    if p.exists() and p.read_text(encoding='utf-8') == new: return False   # no change, no save
    p.write_text(new, encoding='utf-8'); return True


def needs_summary(doc):
    c = {}
    for r in doc.get('rows') or []:
        if r.get('status') == 'open': c[r.get('who')] = c.get(r.get('who'), 0) + 1
    return c


# ---- layer files: one layer of one area, every record read, plus what the key keeps -----------------------------------------
# GeoJSON FeatureCollection (gzip). 'kpc' says where it came from and how many records the layer itself reported for this area
# (count_live) or a person counted (count_expected); 'features' are EVERY record read (so the count can be checked), each with
# properties._kpc = the record as the saved copy stores it when the key keeps it (null when it is left out, e.g. a PAD-US copy).
def layer_file_path(root, area, layer): return pathlib.Path(root) / f'{area}.{layer}.geojson.gz'   # one flat folder; the name is unique (raw-add keys on it)


def write_layer_file(path, meta, feats):
    p = pathlib.Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    doc = {'type': 'FeatureCollection', 'kpc': dict(meta, format=FORMAT), 'features': feats}
    raw = json.dumps(doc, separators=(',', ':'), sort_keys=True, ensure_ascii=False).encode()
    tmp = p.with_name(p.name + '.tmp')
    with open(tmp, 'wb') as fh, gzip.GzipFile(fileobj=fh, mode='wb', mtime=0) as z: z.write(raw)
    os.replace(tmp, p)   # never a half-written layer file
    return p


def read_layer_file(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f: doc = json.load(f)
    return doc.get('kpc') or {}, doc.get('features') or []


def layer_file_expected(meta):
    """What the layer file must hold: the layer's own total for the area, else the count a person's download was checked against."""
    for k in ('count_live', 'count_expected'):
        if meta.get(k) not in (None, ''): return int(meta[k])
    return None


def prefix_of(oid): return re.match(r'[a-z]*', str(oid)).group(0)


def merge_saved_layer(blob, layer, new_recs):
    """Keep-bigger merge of ONE layer (OBJECTID prefix) into a saved copy blob {'recs': [...]}. The layer's records are replaced only
    when the new read has at least as many; a smaller re-read never replaces a saved layer. Returns (blob, what)."""
    recs = blob.get('recs') or []
    old = [r for r in recs if prefix_of(r.get('OBJECTID')) == layer]
    new = [r for r in new_recs if prefix_of(r.get('OBJECTID')) == layer]
    if len(new) < len(old): return blob, f'kept the saved {layer} ({len(old)} records; the new read has {len(new)})'
    if sorted(json.dumps(r, sort_keys=True) for r in new) == sorted(json.dumps(r, sort_keys=True) for r in old): return blob, f'{layer} unchanged ({len(old)})'
    blob = dict(blob, recs=[r for r in recs if prefix_of(r.get('OBJECTID')) != layer] + new, saved=datetime.date.today().isoformat())
    return blob, f'{layer}: {len(old)} -> {len(new)} records'


def load_saved(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f: return json.load(f)


def save_saved(path, blob):
    """The same bytes kpc_us_key.save_cache writes (compact JSON, gzip); written to a temp file first, so it is never half-written."""
    p = pathlib.Path(path); tmp = p.with_name(p.name + '.tmp')
    with gzip.open(tmp, 'wt', encoding='utf-8') as f: json.dump(blob, f, separators=(',', ':'))
    os.replace(tmp, p)


def prefix_counts(blob):
    c = {}
    for r in blob.get('recs') or []: c[prefix_of(r.get('OBJECTID'))] = c.get(prefix_of(r.get('OBJECTID')), 0) + 1
    return c


def geojson_to_rings(g):
    """GeoJSON (Multi)Polygon -> the key's Esri-style {'rings': [...]} (every ring, outer and holes, as the key reads them)."""
    return {'rings': [ring for poly in polys_of(g) for ring in poly]}
