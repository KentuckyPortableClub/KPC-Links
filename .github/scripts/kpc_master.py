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
import copy, datetime, gzip, hashlib, json, math, os, pathlib, re, time, urllib.error, urllib.parse, urllib.request, zlib
from urllib import robotparser
import kpc_net_guard
kpc_net_guard.install()   # process-wide: never-contact hosts are refused for every request, every redirect hop

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
# KPC_SAVED_ONLY_HOSTS ADDS hosts; it can never drop a default one (owner rule, 2026-11-10).
SAVED_ONLY_HOSTS = {'services.arcgis.com', 'services1.arcgis.com', 'apps.fs.usda.gov'} | kpc_net_guard.extra_hosts()
HUB_RE = re.compile(r'(^|\.)(hub\.arcgis\.com|opendata\.arcgis\.com)$')   # hub portals: 60 s between requests
HUB_DELAY, HOST_DELAY = 60.0, 2.0
WDPA_RE = re.compile(r'wdpa|protected\s*-?planet|protectedplanet|sprep|pacificdata', re.I)


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
    host, path = kpc_net_guard.host_of(url), parts(url)[1]   # the host really dialled: no port, user@ or trailing dot
    for h, p in NEVER_CONTACT:
        if host == h and path.lower().startswith(p.lower()):
            return False, f'never contact {h}{p}: no request of any kind, robots.txt included'
    if is_arcgis_services_host(host):
        return False, f'{host}: services*.arcgis.com is never contacted, robots.txt included'
    if host in SAVED_ONLY_HOSTS:
        return False, f'{host}: saved copies only, no live read'
    return kpc_net_guard.host_ok(url)


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


# ---- one complete read of an ArcGIS layer query (every key uses it; owner rule, 2026-11-10) --------------------------------
LAYER_MINUTES = float(os.environ.get('KPC_LAYER_MINUTES') or 60)   # one slow layer may not eat the whole job
POST_OVER = 1800   # a request longer than this (an objectIds batch) is sent as a POST


def _oid_of(f, field):
    a = f.get('attributes') or f.get('properties') or {}
    if field in a: return a[field]
    lf = str(field).lower()
    return next((v for k, v in a.items() if str(k).lower() == lf), None)


def read_complete(query_url, where='1=1', box_params=None, fetch_json=None, out_fields='*', page_hint=500, oid_field=None,
                  max_record_count=None, extra=None, id_batch=None, minutes=None, label='', order=True, clock=time.monotonic, oid_of=None):
    """Every record of one ArcGIS query (where + the same box), or an error: never a partial list.
    fetch_json(url, params, post=False) -> dict is the key's own paced, guarded opener. Steps:
      1. returnCountOnly with the same where + box (no page or outline parameters): the number the read must reach;
      2. returnIdsOnly with the same where + box; when every id comes back, the records are asked BY ID in batches of
         min(maxRecordCount, 500) (a smaller batch when the server sends fewer), each id exactly once;
      3. else (no ids-only, or ids-only cut to a window) offset paging that moves by the rows the server REALLY sent, and stops
         on an empty page; a page with no new id = the server ignores resultOffset (LayerStall).
    Finishes only when the distinct ids equal the count; else ShortRead. minutes = this layer's time limit (LayerStall).
    oid_of(feature) -> id, for a server that keys attributes by alias (default: the object-id field, any letter case).
    Returns (features in id / read order, how = {'count', 'mode': 'ids' | 'offset', 'short_page', 'requests'})."""
    box, extra = dict(box_params or {}), dict(extra or {})
    lim = LAYER_MINUTES if minutes is None else float(minutes)
    deadline, how = clock() + lim * 60, {'count': None, 'mode': None, 'short_page': False, 'requests': 0}

    def ask(params):
        if clock() > deadline: raise LayerStall(f'{label}: over its {lim:g}-minute limit ({how["requests"]} requests): not used')
        how['requests'] += 1
        try: j = fetch_json(query_url, params, post=len(urllib.parse.urlencode(params)) > POST_OVER)
        except MasterError: raise
        except Exception as e: raise MasterError(f'{label}: {type(e).__name__}: {str(e)[:160]}') from e  # noqa: BLE001  (the step decides)
        if not isinstance(j, dict): raise MasterError(f'{label}: not a JSON answer')
        if j.get('error'): raise MasterError(f"{label}: the layer answered an error ({str(j['error'])[:160]})")
        return j
    base = dict({'where': where or '1=1'}, **box)
    c = ask(dict(base, returnCountOnly='true', returnGeometry='false', f='json'))
    if c.get('count') is None: raise ShortRead(f'{label}: the layer did not report its count, so the read cannot be checked: refused')
    count = how['count'] = int(c['count'])
    if count == 0: how['mode'] = 'ids'; return [], how
    mx = int(max_record_count or 0) or 1000
    ids, of = None, oid_field
    try:
        r = ask(dict(base, returnIdsOnly='true', f='json'))
        if isinstance(r.get('objectIds'), list):
            ids = sorted({x for x in r['objectIds'] if x is not None}, key=lambda x: (str(type(x)), x))
            of = oid_field or r.get('objectIdFieldName') or 'OBJECTID'
    except MasterError: ids = None   # no ids-only on this server: offset paging
    got = {}
    if ids is not None and len(ids) == count:
        how['mode'], pending, b = 'ids', list(ids), max(1, int(id_batch or min(mx, 500)))
        try:
            while pending:
                batch = pending[:b]; want = {str(x) for x in batch}
                j = ask(dict({'objectIds': ','.join(str(x) for x in batch), 'outFields': out_fields}, **extra, f='json'))
                n = 0
                for f in j.get('features') or []:
                    k = str(oid_of(f) if oid_of else _oid_of(f, of))
                    if k in want and k not in got: got[k] = f; n += 1
                if not n: raise LayerStall(f'{label}: a batch of {len(batch)} ids came back with none of them')
                pending = [x for x in pending if str(x) not in got]
                if n < len(batch): b = n   # the server's real cap is smaller than it says
        except MasterError:
            if got: raise
            got, how['mode'] = {}, None   # by-id reads refused on the first batch: offset paging instead
    if how['mode'] != 'ids':
        how['mode'], of = 'offset', of or oid_field or 'OBJECTID'
        page, off = max(1, min(int(page_hint or mx), mx)), 0
        while True:
            q = dict(base, outFields=out_fields, **extra, f='json', resultOffset=off, resultRecordCount=page)
            if order: q['orderByFields'] = of
            j = ask(q)
            fs = j.get('features') or []
            if not fs: break
            n, here = 0, set()
            for f in fs:
                o = oid_of(f) if oid_of else _oid_of(f, of)
                if o is None: raise ShortRead(f'{label}: a record without its id ({of}): the read cannot be checked: refused')
                here.add(str(o))
                if str(o) not in got: got[str(o)] = f; n += 1
            if not n: raise LayerStall(f'{label}: the server sent the page at offset {off} again (resultOffset ignored?)')
            if len(got) > count: raise ShortRead(f'{label}: {len(got)} distinct records, more than the {count} the layer reports: refused')
            more = bool(j.get('exceededTransferLimit'))
            if len(got) == count and not more: break
            if not more and len(fs) < page: how['short_page'] = True   # the old end test would have stopped here
            off += len(here)   # the distinct rows this page really sent (a row sent twice is one row)
    if len(got) != count:
        raise ShortRead(f'{label}: read {len(got)} of {count} records the layer reports ({how["mode"]}): SHORT, nothing is used')
    return list(got.values()), how


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


# Nov 11 (KPC owner, 2026-11-11): an area whose outlines do not fit one file under 1 MB is saved in parts with the release's own part
# scheme (kpc_release.split / join): US-AK.geojson.gz is part 1 and says how many parts there are (kpc_part = [i, N, tag]); the
# others are US-AK.p2.geojson.gz ... A file that fits stays one file, byte for byte as before. load_area reads every part.
PART_CAP = 1_000_000


def area_files(area, root=None):
    """The files that hold an area now: [part 1 (the area file), part 2, ...] as part 1 declares them; [] when there is none."""
    import kpc_release as REL
    p = area_path(area, root)
    got = REL.read_parts(p.name, lambda n: (p.parent / n).read_bytes() if (p.parent / n).is_file() else None)
    return [p.parent / n for n in got[0]] if got else []


def is_part_file(name):
    """US-AK.p2.geojson.gz is part 2 of US-AK, not an area of its own."""
    import kpc_release as REL
    return bool(REL.PART_RE.match(str(name)))


def load_doc_parts(name, read):
    """The whole area document from its part 1 bytes reader (read(name) -> bytes or None); None when there is no file. Parts that
    are missing or belong to another save raise MasterError (fail closed: never half an area)."""
    import kpc_release as REL
    got = REL.read_parts(name, read)
    if got is None: return None
    try: return REL.join([None if b is None else REL.load_doc(name, b) for b in got[1]])
    except REL.ReleaseError as e: raise MasterError(f'{name}: {e}')


def recs_of_doc(doc): return {ft['properties']['ref']: dict(ft['properties'], geometry=ft['geometry']) for ft in (doc or {}).get('features', [])}


def load_area(area, root=None):
    p = area_path(area, root)
    return recs_of_doc(load_doc_parts(p.name, lambda n: (p.parent / n).read_bytes() if (p.parent / n).is_file() else None))


# Nov 11 (KPC owner, 2026-11-11): a park the US key grades pin has no outline. save_area leaves it out of the state's file, so every
# writer (the master step trim / collect / part, kpc_outlines_from_key, kpc_outlines_keep_main) and every reader agree without
# reading the key. The rule: the park is dropped from a state's file when every US key that lists it grades it pin, whichever
# state's file holds the record (a record in a neighbour's file counts the same). Nov 13 (Quality M2, US-43293787778): a park no US
# key lists is dropped too (no licence, no key row). A park that is pin in one state but official in another (US-4514: pin in TX and OK, official in
# NM) keeps its outline wherever it has one: the planner's lookup (KPCB.usKey) takes the best grade over the states it reads, so it
# would still draw that outline. No key file (or one that cannot be read) = nothing is dropped.
# Nov 13 (Quality M1): an outline that still holds a record the key did not join (an id in record_ids that is not in the key's m,
# e.g. held record 2165 in AK US-10281) is a problem: save-time check fails and release refuses that area. It is not silently dropped
# (that would lose the official park); the outline must be rebuilt from the key's m.
_KEYS = {}
_KEY_M = {}


def _key_grades(key_dir):
    """{ref: {state: g}} over every data/us-key/US-XX.json in key_dir (read once per file version)."""
    key_dir = pathlib.Path(key_dir); out = {}
    for f in sorted(key_dir.glob('US-??.json')):
        try: st = f.stat(); sig = (st.st_mtime_ns, st.st_size)
        except OSError: continue
        if _KEYS.get(f) is None or _KEYS[f][0] != sig:
            try: parks = json.loads(f.read_text(encoding='utf-8')).get('parks') or {}
            except (OSError, ValueError, AttributeError): parks = {}
            _KEYS[f] = (sig, {r: p.get('g') for r, p in parks.items() if isinstance(p, dict)})
        for r, g in _KEYS[f][1].items(): out.setdefault(r, {})[f.stem] = g
    return out


def _key_ready(area, key_dir):
    if not re.match(r'^US-[A-Z]{2}$', str(area)): return None
    key_dir = pathlib.Path(key_dir or (OUTLINES.parent / 'us-key'))
    return key_dir if (key_dir / f'{area}.json').is_file() else None


def _key_joined(key_dir):
    """{ref: set of joined record ids} over every data/us-key/US-XX.json in key_dir, from the key's m only (held candidates in c
    are left out). Read once per file version."""
    key_dir = pathlib.Path(key_dir); out = {}
    for f in sorted(key_dir.glob('US-??.json')):
        try: st = f.stat(); sig = (st.st_mtime_ns, st.st_size)
        except OSError: continue
        if _KEY_M.get(f) is None or _KEY_M[f][0] != sig:
            try: parks = json.loads(f.read_text(encoding='utf-8')).get('parks') or {}
            except (OSError, ValueError, AttributeError): parks = {}
            ids = {}
            for r, p in parks.items():
                if not isinstance(p, dict): continue
                ids[r] = {str(x[0]) for x in (p.get('m') or []) if isinstance(x, list) and x}
            _KEY_M[f] = (sig, ids)
        for r, s in _KEY_M[f][1].items():
            out.setdefault(r, set()).update(s)
    return out


def pin_drops(area, refs, key_dir=None):
    """The refs of `refs` that may not have an outline in `area`'s file: every US key that lists the park grades it pin, whichever
    state's file the record sits in (a park in a neighbour's file counts the same).
    US areas only; no key file for the area = nothing (as before)."""
    key_dir = _key_ready(area, key_dir)
    if key_dir is None: return set()
    grades = _key_grades(key_dir)
    return {r for r in refs if grades.get(r) and all(g == 'pin' for g in grades[r].values())}


def not_in_key_drops(area, refs, key_dir=None):
    """The refs of `refs` that no US key lists (Nov 13 Quality M2). They have no licence in the key and must not have an outline.
    US areas only; no key file for the area = nothing (as before). A park listed in a neighbour's key is kept."""
    key_dir = _key_ready(area, key_dir)
    if key_dir is None: return set()
    grades = _key_grades(key_dir)
    return {r for r in refs if r not in grades}


def outline_record_ids(rec):
    """The record ids an outline says it was built from (record_ids), as strings. Trail ids (trl...) and master-trim row
    indexes (row12) are ignored: those are not key/cache OBJECTIDs, so they are not compared to the key's m."""
    ids = rec.get('record_ids') if isinstance(rec, dict) else None
    if not ids: return []
    out = []
    for i in ids:
        s = str(i)
        if prefix_of(s) == 'trl': continue
        if re.fullmatch(r"row[0-9]+", s): continue
        out.append(s)
    return out


def held_record_refs(area, recs, key_dir=None):
    """{ref: [extra ids]} for outlines that still hold a record the key did not join (id not in any listing's m). Parks the key
    does not list are not in this dict (they are not_in_key_drops). US areas only."""
    key_dir = _key_ready(area, key_dir)
    if key_dir is None: return {}
    joined = _key_joined(key_dir); out = {}
    for r, v in recs.items():
        if r not in joined: continue
        allow = {i for i in joined[r] if prefix_of(i) != 'trl'}
        if not allow: continue
        have = outline_record_ids(v)
        # Only when the outline was clearly built from the key's m (it already carries at least one joined id). A master-trim
        # outline (row12) or a synthetic record that never used those ids is not a held-record leak.
        if not (set(have) & allow): continue
        extra = [i for i in have if i not in allow]
        if extra: out[r] = extra
    return out


def outline_key_problems(area, recs, key_dir=None):
    """Plain-word problems when the area's outlines do not agree with the US key: a PIN-graded park, a ref no key lists, or an
    outline that holds a record missing from the key's m. Empty when the area is not US or there is no key file."""
    key_dir = _key_ready(area, key_dir)
    if key_dir is None: return []
    msgs = []
    for r in sorted(pin_drops(area, recs, key_dir)):
        msgs.append(f'{r}: the key grades the park PIN; it must not have an outline')
    for r in sorted(not_in_key_drops(area, recs, key_dir)):
        msgs.append(f'{r}: not in any US key file; the outline must be dropped')
    for r, extra in sorted(held_record_refs(area, recs, key_dir).items()):
        msgs.append(f"{r}: holds record(s) {', '.join(extra)} not in the key's m")
    return msgs


def grade_lowers(area, recs, key_dir=None):
    """Nov 11 (KPC owner, 2026-11-11): the refs whose record says a HIGHER kind than the key gives the park: the record's g is lowered
    to approximate only when approximate is the best grade any US key that lists the park gives it, whichever state's file the record
    sits in (a park official in any state's key is not touched; an unknown grade anywhere = left alone). Never raised. A park no US
    key lists is left alone. US areas only."""
    key_dir = _key_ready(area, key_dir)
    if key_dir is None: return set()
    grades = _key_grades(key_dir); ra = RANK['approximate']
    return {r for r, v in recs.items() if grades.get(r) and RANK.get(v.get('g'), -1) > ra and max(RANK.get(g, 99) for g in grades[r].values()) == ra}


def key_fix(area, recs, key_dir=None):
    """(records as the key allows them, dropped refs, lowered refs): the ONE place the pin / not-in-key / approximate rules are
    applied (save_area, keep_main, from_key). Dropped = pin-graded in every listing, or listed by no US key. Held-record extras
    are not dropped here (rebuild or refuse)."""
    drop = pin_drops(area, recs, key_dir) | not_in_key_drops(area, recs, key_dir)
    low = grade_lowers(area, {r: v for r, v in recs.items() if r not in drop}, key_dir)
    out = {}
    for r, v in recs.items():
        if r in drop: continue
        if r in low:
            v = dict(v, g='approximate'); v['hash'] = content_hash(v)   # only g (and so the hash) changes
        out[r] = v
    return out, drop, low


def same_content(old, new):
    """Two outline files hold the same thing: the same bytes, or the same JSON once unpacked (another zlib build packs the same
    content into other bytes; that is no change)."""
    if old == new: return True
    try:
        a, b = gzip.decompress(old), gzip.decompress(new)
        return a == b or json.loads(a) == json.loads(b)
    except (OSError, EOFError, ValueError, zlib.error): return False


def write_if_changed(path, b):
    """Write `b` to `path` unless the file there already holds the same content (same_content). True = written."""
    path = pathlib.Path(path)
    if path.is_file() and same_content(path.read_bytes(), b): return False
    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b); return True


def _gz_named(raw, name):
    """The same gzip bytes the area file always had (mtime 0, level 9, the file name in the header)."""
    import io
    b = io.BytesIO()
    with gzip.GzipFile(filename=name, fileobj=b, mode='wb', mtime=0, compresslevel=9) as z: z.write(raw)
    return b.getvalue()


def save_area(area, recs, root=None, key_dir=None, cap=None):
    """Deterministic bytes (sorted refs, gzip mtime 0): an unchanged area is a byte-identical file, so git shows no change.
    Nov 11: a park the key grades pin is left out (pin_drops) and a record graded higher than the key allows is saved as approximate
    (grade_lowers); key_dir defaults to the us-key folder next to the outlines folder. An area over 1 MB is written in parts
    (kpc_release.split). A file that already holds the same content (even packed by another zlib build) is left untouched.
    The gzip header is fixed: mtime 0, the file name, XFL 2 (level 9), OS 255 (Python's). Returns the area file (part 1)."""
    import kpc_release as REL
    for r in recs.values(): assert_public_safe(r)
    root = pathlib.Path(root or OUTLINES)
    recs, drop, low = key_fix(area, recs, key_dir or root.parent / 'us-key')
    kd = key_dir or root.parent / 'us-key'
    pin, unk = pin_drops(area, drop, kd), not_in_key_drops(area, drop, kd)
    if pin: print(f"::notice title=Outlines {area}::{len(pin)} outline(s) not saved: the key grades the park pin ({' '.join(sorted(pin)[:8])}{' ...' if len(pin) > 8 else ''})", flush=True)
    if unk: print(f"::notice title=Outlines {area}::{len(unk)} outline(s) not saved: not in any US key ({' '.join(sorted(unk)[:8])}{' ...' if len(unk) > 8 else ''})", flush=True)
    if low: print(f"::notice title=Outlines {area}::{len(low)} outline(s) saved as approximate: the key grades the park approximate ({' '.join(sorted(low)[:8])}{' ...' if len(low) > 8 else ''})", flush=True)
    feats = [{'type': 'Feature', 'id': ref, 'properties': {k: v for k, v in recs[ref].items() if k != 'geometry'}, 'geometry': recs[ref]['geometry']}
             for ref in sorted(recs)]
    doc = {'type': 'FeatureCollection', 'kpc': {'format': FORMAT, 'area': area}, 'features': feats}
    p = area_path(area, root); p.parent.mkdir(parents=True, exist_ok=True)
    pack = lambda name, d: _gz_named(json.dumps(d, separators=(',', ':'), sort_keys=True).encode(), name)   # noqa: E731
    one = pack(p.name, doc); cap = cap or PART_CAP
    parts = [(p.name, one)] if len(one) <= cap else REL.split(p.name, doc, cap, pack)
    for name, b in parts: write_if_changed(p.parent / name, b)   # the same content already there is never rewritten (no change in git)
    for f in p.parent.glob(f'{area}.p*.geojson.gz'):   # parts of an older, longer save (the copy-mode save carries no deletion: part 1 decides)
        m = REL.PART_RE.match(f.name)
        if m and m.group(1) == area and int(m.group(2)) > len(parts): f.unlink()
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
    ids, unknown = {}, {}
    have_pre = {p[0].split('-')[0] for p in parks}   # a ref of another country's list is not this run's miss
    for i, f in enumerate(feats):
        for fld in cfg.get('id_fields') or []:
            v = str(prop(f).get(fld) or '').strip().upper().replace(' ', '')
            if REF_RE.match(v) and v in by_ref: ids.setdefault(v, []).append(i)
            elif REF_RE.match(v) and v.split('-')[0] in have_pre: unknown.setdefault(v, i)
    for ref, idx in ids.items():
        r = build(ref, idx, 'id')
        if r: recs[ref] = r; used.add(ref)
        else: queue.append({'ref': ref, 'name': by_ref[ref][1], 'lat': by_ref[ref][2], 'lon': by_ref[ref][3], 'why': WHY_NO_GEOM,
                            'candidates': '; '.join(rid(feats[i], i) for i in idx[:6])})   # Nov 11: matched by id, then dropped for lack of an outline
    for v, i in sorted(unknown.items()):   # Nov 11: a layer record that names a POTA ref the park list does not hold (retired / mistyped)
        nf = (cfg.get('name_fields') or [None])[0]
        queue.append({'ref': v, 'name': str(prop(feats[i]).get(nf) or '') if nf else '', 'lat': '', 'lon': '', 'why': WHY_UNKNOWN_REF, 'candidates': rid(feats[i], i)})
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
        else: queue.append({'ref': ref, 'name': name, 'lat': lat, 'lon': lon, 'why': WHY_NO_GEOM, 'candidates': '; '.join(rid(feats[i], i) for i in hit[:6])})
    return recs, dedupe_queue([q for q in queue if not (q['why'] == WHY_NO_GEOM and q['ref'] in recs)])   # a park that got an outline another way is not a miss


# ---- the solver queue (Nov 11): one reason per row, one row per (park, reason), written only when it changed -------------
WHY_NO_GEOM = 'matched an outline record, but the record has no usable outline'
WHY_UNKNOWN_REF = 'the layer record names a POTA ref that is not in the park list'
WHY_NO_LAYER = 'no layer joined this park in the key (no outline record to match)'
WHY_NOT_KEPT = 'joined in the key, but no outline for it is in the master records'
QUEUE_FIELDS = ['ref', 'name', 'lat', 'lon', 'why', 'candidates']


def dedupe_queue(rows):
    """One row per (ref, why), first one wins, order kept (so an unchanged queue is the same bytes and makes no commit)."""
    seen, out = set(), []
    for r in rows:
        k = (str(r.get('ref', '')), str(r.get('why', '')))
        if k in seen: continue
        seen.add(k); out.append({f: r.get(f, '') for f in QUEUE_FIELDS})
    return out


def write_queue(path, rows, keep_empty=True):
    """Write a solver-queue CSV (header + deduped rows) ONLY when its bytes would change. Returns True when the file changed.
    keep_empty=False: an empty queue removes the file instead of writing a header-only one."""
    import csv, io
    path = pathlib.Path(path); rows = dedupe_queue(rows)
    if not rows and not keep_empty:
        if path.exists(): path.unlink(); return True
        return False
    buf = io.StringIO(newline='')
    w = csv.DictWriter(buf, QUEUE_FIELDS); w.writeheader(); w.writerows(rows)
    data = buf.getvalue().encode('utf-8')
    if path.is_file() and path.read_bytes() == data: return False
    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
    return True


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


# ---- a saved copy's own manifest, and the owner-approved baselines (KPC owner, 2026-11-11) ----------------------------------------
# A copy trimmed on purpose (a hand bundle that keeps only the features near POTA parks) cannot be checked against the full-layer
# baseline in layers.json (caches): every such copy is "short" by design. The copy carries its own count instead: a manifest written
# INTO the copy (blob['manifest']) when it is made (`kpc_master_cli.py bundle-manifest`), so it travels with the file and cannot be
# separated from it. The gate checks a trimmed copy against its own manifest, exactly; it refuses a trimmed copy whose manifest is
# missing a field or does not match the copy. A full copy keeps the full baseline. The gate never writes a baseline.
# Copies uploaded before manifests existed have none: for them, and for a baseline that was recorded wrong, the owner signs a file
# of baselines (data/outlines/world-baselines.approved.json). Only a file whose name ends .approved.json and whose approved_by /
# approved_date is a real sign-off is read; the .proposed.json file next to it is never read.
MANIFEST_FIELDS = ('format', 'area', 'trimmed', 'made_by', 'made', 'total', 'layers', 'recs_sha256')


def copy_layer_counts(name, blob):
    """{layer: records} of one saved copy, by the same keys as saved_counts (W-XX: 'src:<label>')."""
    out = {}
    for r in (blob or {}).get('recs') or []:
        if name.startswith('US-'): ks = [prefix_of(r.get('OBJECTID'))]
        elif name.startswith('CA-'): ks = {str(r.get('oid', '')).split(':', 1)[0] if ':' in str(r.get('oid', '')) else 'cpcad', 'src:' + str(r.get('src') or '')}
        else: ks = ['src:' + str(r.get('src') or '')]
        for k in ks: out[k] = out.get(k, 0) + 1
    return out


def recs_sha256(recs):
    """sha256 of the copy's record list in one canonical form (sorted keys, compact): the same records give the same hash."""
    return hashlib.sha256(json.dumps(recs if isinstance(recs, list) else [], sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                                     default=lambda o: sorted(o) if isinstance(o, (set, frozenset)) else str(o)).encode('utf-8')).hexdigest()


def make_manifest(name, blob, made_by, made, trimmed=True, source_full=None, note=''):
    """The manifest for one copy, from its own records. trimmed=True: kept only the features near POTA parks, on purpose."""
    stem = name[:-len('.json.gz')] if name.endswith('.json.gz') else name
    recs = (blob or {}).get('recs') or []
    m = {'format': 1, 'area': stem, 'trimmed': bool(trimmed), 'made_by': str(made_by or '').strip(), 'made': str(made or '').strip(),
         'total': len(recs), 'layers': copy_layer_counts(stem, blob), 'recs_sha256': recs_sha256(recs)}
    if trimmed: m['trimmed_to'] = 'the features near POTA parks (park-relevant only); a full-layer count does not apply'
    if source_full: m['source_full'] = {str(k): int(v) for k, v in source_full.items()}   # for the record: each source layer's own full count
    if note: m['note'] = str(note)
    return m


def manifest_problems(name, blob):
    """[] when the copy's manifest is whole and matches the copy; else what is wrong (each one refuses the copy)."""
    stem = name[:-len('.json.gz')] if name.endswith('.json.gz') else name
    m = (blob or {}).get('manifest')
    if not isinstance(m, dict): return ['no manifest']
    bad = [f'manifest has no {k}' for k in MANIFEST_FIELDS if m.get(k) in (None, '')]
    if bad: return bad
    if m.get('format') != 1: bad.append(f"manifest format {m.get('format')!r} is not 1")
    if m.get('area') != stem: bad.append(f"manifest is for {m.get('area')!r}, not {stem}")
    try: datetime.date.fromisoformat(str(m.get('made'))[:10])
    except ValueError: bad.append(f"manifest date {m.get('made')!r} is not a date")
    recs = (blob or {}).get('recs') or []
    if not isinstance(m.get('total'), int) or m['total'] <= 0: bad.append(f"manifest total {m.get('total')!r} is not a positive count")
    if not isinstance(m.get('layers'), dict) or not all(isinstance(v, int) and v >= 0 for v in m['layers'].values()): bad.append('manifest layers is not {layer: count}')
    if bad: return bad
    if sum(m['layers'].values()) != m['total']: bad.append(f"manifest layers add up to {sum(m['layers'].values())}, its total says {m['total']}")
    have = copy_layer_counts(stem, blob)
    if len(recs) > m['total'] or any(have.get(k, 0) > v for k, v in m['layers'].items()) or set(have) - set(m['layers']):
        bad.append(f"the copy holds records its manifest does not list ({len(recs)} records, manifest {m['total']})")
    if not bad and len(recs) == m['total'] and have == m['layers'] and recs_sha256(recs) != m['recs_sha256']:
        bad.append('the records differ from the ones the manifest was written for (recs_sha256)')
    return bad


def check_against_manifest(name, blob):
    """A trimmed copy against its OWN manifest, exactly. Short (fewer records, in total or for one layer) raises ShortRead, as the
    full-baseline check does; any other mismatch raises MasterError (refused). Returns the record count."""
    stem = name[:-len('.json.gz')] if name.endswith('.json.gz') else name
    m = (blob or {}).get('manifest') or {}
    recs = (blob or {}).get('recs') or []
    if isinstance(m.get('total'), int) and len(recs) < m['total']:
        raise ShortRead(f'{name}: SHORT against its own manifest: {len(recs)} records, the manifest says {m["total"]} (made by {m.get("made_by")}, {m.get("made")})')
    if isinstance(m.get('layers'), dict):
        have = copy_layer_counts(stem, blob)
        less = sorted(k for k, v in m['layers'].items() if isinstance(v, int) and have.get(k, 0) < v)
        if less: raise ShortRead(f'{name}: SHORT against its own manifest for ' + ', '.join(f'{k} ({have.get(k, 0)} < {m["layers"][k]})' for k in less[:10]))
    bad = manifest_problems(name, blob)
    if bad: raise MasterError(f'{name}: trimmed copy refused, its manifest does not match the copy: ' + '; '.join(bad[:5]))
    return len(recs)


def is_trimmed(blob):
    m = (blob or {}).get('manifest')
    return isinstance(m, dict) and bool(m.get('trimmed'))


APPROVED_SUFFIX = '.approved.json'


def load_approved_baselines(path, persons=None, today=None):
    """(entries, why_not). entries = {stem: {'expected_count': int, 'kind': 'trimmed'|'full', 'reason': str, 'copy_sha256': hex}}.
    copy_sha256 (the sha256 of the .json.gz file, as the release page shows it) is required: an approval is for one file only.
    Read ONLY from a file whose name ends .approved.json, with a person's sign-off: approved_by names the owner ('KPC owner') or a
    person in KPC_PERSONS, and approved_date is a real date not in the future (kpc_answer_words.signed_off, the rule the answer
    sheet uses). Anything else: no entries and the reason (the gate then uses the layers.json baselines: fail closed)."""
    p = pathlib.Path(path) if path else None
    if p is None or not p.is_file(): return {}, 'no approved baselines file'
    if not p.name.endswith(APPROVED_SUFFIX): return {}, f'{p.name}: only a file named *{APPROVED_SUFFIX} is read (a proposed file is never read)'
    try: doc = json.load(open(p, encoding='utf-8'))
    except Exception as e: return {}, f'{p.name}: unreadable ({e})'  # noqa: BLE001
    if not isinstance(doc, dict): return {}, f'{p.name}: not a JSON object'
    try:
        import sys; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import kpc_answer_words as AW   # noqa: E402
        who = set(persons) if persons is not None else AW.persons(os.environ.get('KPC_PERSONS'))
        who = {w.lower() for w in who} | {'kpc owner'}
        if not AW.signed_off(doc.get('approved_by'), doc.get('approved_date'), who, today=today):
            return {}, f"{p.name}: not signed off (approved_by {doc.get('approved_by')!r}, approved_date {doc.get('approved_date')!r}): not read"
    except ImportError as e: return {}, f'{p.name}: the sign-off check could not run ({e}): not read'
    out, bad = {}, []
    for stem, e in (doc.get('baselines') or {}).items():
        if not AREA_RE.match(str(stem)) or not isinstance(e, dict): bad.append(f'{stem}: not an area entry'); continue
        n = e.get('expected_count')
        if not isinstance(n, int) or isinstance(n, bool) or n <= 0: bad.append(f'{stem}: expected_count {n!r} is not a positive count'); continue
        if e.get('kind') not in ('trimmed', 'full'): bad.append(f"{stem}: kind {e.get('kind')!r} is not trimmed or full"); continue
        if not str(e.get('reason') or '').strip(): bad.append(f'{stem}: no reason'); continue
        sha = str(e.get('copy_sha256') or '').strip().lower()
        if not re.fullmatch(r'[0-9a-f]{64}', sha): bad.append(f'{stem}: copy_sha256 is not the sha256 of the copy (required: the approval is for that one file)'); continue
        out[stem] = {'expected_count': n, 'kind': e['kind'], 'reason': str(e['reason']), 'copy_sha256': sha}
    if bad: return {}, f'{p.name}: ' + '; '.join(bad[:5]) + ' (the whole file is not read)'
    return out, ''


def gate_baseline(name, blob, file_sha, caches, approved, allow_trimmed=False):
    """What one saved copy is checked against: ('manifest', None, why) | ('approved', n, why) | ('full', n, why) | ('refuse', None, why).
    Order: the copy's own manifest when it says trimmed; else an owner-approved baseline; else the full baseline (layers.json caches)."""
    stem = name[:-len('.json.gz')] if name.endswith('.json.gz') else name
    if is_trimmed(blob):
        if not allow_trimmed: return 'refuse', None, f'{name}: a trimmed copy (manifest), and this gate takes no trimmed copies'
        m = blob['manifest']
        return 'manifest', None, f"{name}: trimmed copy, checked against its own manifest ({m.get('total')} records, made by {m.get('made_by')}, {m.get('made')})"
    a = (approved or {}).get(stem)
    if a:
        if a.get('copy_sha256') != file_sha:
            return 'refuse', None, f"{name}: the approved baseline is for another copy (copy_sha256 {str(a.get('copy_sha256'))[:12]}, this copy {file_sha[:12]})"
        return 'approved', a['expected_count'], f"{name}: owner-approved baseline {a['expected_count']} ({a['kind']}: {a['reason'][:120]})"
    exp = (caches.get(stem) or {}).get('expected_count')
    if exp is None: return 'refuse', None, f'{stem}: no baseline in the manifest (caches): held, not used'
    return 'full', exp, ''


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
    host, path = kpc_net_guard.host_of(url), parts(url)[1]
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
        try: kpc_net_guard.check(newurl, hop_from=req.full_url)   # also refuses https -> http / ftp: / file: hops
        except kpc_net_guard.NetGuardRefused as e: raise LiveNotAllowed(f'redirect refused: {e.reason}') from None
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
    try: blob = load_saved(path)
    except Exception: return {}  # noqa: BLE001
    return copy_layer_counts(pathlib.Path(path).name, blob)


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
    doc['rows'] = [honest_who(have[k]) for k in sorted(have)]   # every merge: an old list cannot bring back a wrong who
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


def layer_file_expected(meta, outside_ok=0):
    """What the layer file must hold: the layer's own total for the area, else the count a person's download was checked against.
    Nov 11 (KPC owner, 2026-11-11; Quality): a live read of a one-state layer carries count_layer, the layer's own total with no state
    box. Then the file must hold that total (less the records layers.json says really lie outside the state, outside_ok), not the boxed
    count_live: a box that misses part of the state (Florida's Keys) cannot pass. count_layer present but None (its count failed) = no
    expected count: the read cannot be checked and is held (fail closed)."""
    if 'count_layer' in meta and meta.get('source', 'live') == 'live':
        tot = meta.get('count_layer')
        if tot in (None, ''): return None
        return max(int(tot) - int(outside_ok or 0), int(meta.get('count_live') or 0))
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


# ---- hand files for any area (US-XX, CA-XX / CA-ALL, W-XX): the area and layer come from the name, nothing else ------------------
AREA_RE = re.compile(r'^(US-[A-Z]{2}|CA-[A-Z]{2,3}|W-[A-Z]{2})$', re.ASCII)
HAND_RE = re.compile(r'^hand-(US-[A-Z]{2}|CA-[A-Z]{2,3}|W-[A-Z]{2})\.(\w+)\.geojson\.gz$', re.ASCII)


def parse_hand_name(name):
    """'hand-W-AS.sgakd.geojson.gz' -> ('W-AS', 'sgakd'); anything else -> None (refused)."""
    m = HAND_RE.match(os.path.basename(str(name or '')))
    return (m.group(1), m.group(2)) if m else None


def hand_file_problem(path, area, layer):
    """'' when a hand file may be used for (area, layer) (its name already parsed); else why not. Fail closed: the file's own
    area and layer must be the ones in its name, and it must hold at least the count it was checked against."""
    try: meta, feats = read_layer_file(path)
    except Exception as e: return f'{pathlib.Path(path).name}: unreadable ({e})'  # noqa: BLE001
    if meta.get('area') != area or str(meta.get('layer') or '') != layer:
        return f"{pathlib.Path(path).name}: the file says {meta.get('area')}|{meta.get('layer')}, its name says {area}|{layer}: refused (never applied to another area)"
    exp = layer_file_expected(meta)
    if exp is None: return f'{pathlib.Path(path).name}: no expected count, so the file cannot be checked: refused'
    if len(feats) < exp: return f'{pathlib.Path(path).name}: {len(feats)} of {exp} records: SHORT, refused (fail closed)'
    return ''



def owner_licence_accepted(area, layer, root):
    """True only when data/outlines/hand/owner-licence-acceptance.json records an owner acceptance for this area+layer.
    The file is not created here (do not invent an acceptance)."""
    p = pathlib.Path(root) / 'hand' / 'owner-licence-acceptance.json'
    try:
        doc = json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return False
    rows = doc.get('accepted') if isinstance(doc, dict) else doc
    if not isinstance(rows, list):
        return False
    want = (str(area or ''), str(layer or ''))
    for r in rows:
        if not isinstance(r, dict):
            continue
        if (str(r.get('area') or ''), str(r.get('layer') or '')) != want:
            continue
        if str(r.get('by') or r.get('accepted_by') or '').strip() and str(r.get('words') or r.get('text') or r.get('acceptance') or '').strip():
            return True
    return False


def share_block(row, root=None):
    """'' when a layer's checked file may be packed / uploaded / merged; else why not. Refused: anything that looks like Protected Planet /
    WDPA or SPREP, a layer / download source marked `redistribute: "no"`, or a row with no licence or terms in data/outlines/layers.json or download-sources.json (optional
    field; absent = no known restriction). row: a needs row or a layer file's meta (area, layer, url, page, label, src)."""
    r = row or {}
    raw = r.get('raw') if isinstance(r.get('raw'), dict) else {}
    if is_wdpa(r.get('layer'), r.get('url'), r.get('page'), r.get('label'), r.get('src'), raw.get('name'), raw.get('source')):
        return f"{r.get('area')}|{r.get('layer')}: looks like Protected Planet / WDPA (licence): not packed, uploaded or merged"
    root = pathlib.Path(root or OUTLINES)
    nu = lambda u: re.sub(r'/query/?$', '', str(u or '').replace('svc:', '', 1).split('|')[0].split('?')[0]).rstrip('/').lower()
    u, area, lay = nu(r.get('url')), r.get('area'), str(r.get('layer') or '')
    for k, L in ((load_layers(root) or {}).get('layers') or {}).items():
        if str((L or {}).get('redistribute', '')).lower() == 'no' and (k in (f'{area}.{lay}', lay) or (u and nu(L.get('url')) == u)):
            return f'{area}|{lay}: layer {k} is marked redistribute=no in layers.json: not packed, uploaded or merged'
    for sid, S in ((load_json(root / 'download-sources.json', {}) or {}).get('sources') or {}).items():
        if str((S or {}).get('redistribute', '')).lower() != 'no': continue
        if sid == r.get('src') or (u and nu(S.get('layer_url')) == u) or (S.get('layer') == lay and area in (S.get('areas') or [])):
            return f'{area}|{lay}: download source {sid} is marked redistribute=no in download-sources.json: not packed, uploaded or merged'
    lic = ''
    for k in ('license', 'licence', 'terms'):
        v = str(r.get(k) or raw.get(k) or '').strip()
        if v:
            lic = v
            break
    if not lic:
        # catalogue licence counts (a hand/import row may name the layer only)
        for k, L in ((load_layers(root) or {}).get('layers') or {}).items():
            if k in (f'{area}.{lay}', lay) or (u and nu((L or {}).get('url')) == u):
                for kk in ('license', 'licence', 'terms'):
                    if str((L or {}).get(kk) or '').strip():
                        lic = str(L.get(kk)).strip(); break
            if lic: break
    if not lic:
        for sid, S in ((load_json(root / 'download-sources.json', {}) or {}).get('sources') or {}).items():
            if sid == r.get('src') or (u and nu(S.get('layer_url')) == u) or (S.get('layer') == lay and area in (S.get('areas') or [])):
                for kk in ('license', 'licence', 'terms'):
                    if str((S or {}).get(kk) or '').strip():
                        lic = str(S.get(kk)).strip(); break
            if lic: break
    if not lic:
        return f"{area}|{lay}: no licence or terms recorded: not packed, uploaded or merged"
    if re.match(r'not\s+stated\b', lic, re.I) and not owner_licence_accepted(area, lay, root):
        return f"{area}|{lay}: licence is 'not stated' and no recorded owner acceptance file: not packed, uploaded or merged"
    return ''


def honest_who(row):
    """A row's who as the host rules see it (used by every merge, so an old list cannot bring a wrong row back): a bot row whose
    layer a bot may not read and with no direct file a bot may fetch is a person's; an OPEN bot row on an allowed host with no
    direct file is a layer the bot re-reads itself, not a download: held. Never turns a person's or a never row into a bot's."""
    if row.get('who') != 'bot': return row
    f = direct_file_of(row)
    w, _ = who_for(row.get('url') or '', file_url=f)
    if w != 'bot': return dict(row, who=w)
    if row.get('status') == 'open' and not f:
        return dict(row, status='held', why=(str(row.get('why') or '') + '; the bot re-reads this layer itself (allowed host): nobody downloads it').lstrip('; '))
    return row
