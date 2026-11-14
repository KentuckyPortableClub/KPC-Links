#!/usr/bin/env python3
"""kpc_display_copy.py: make the public map's DISPLAY COPY of park outlines from the accurate OUTLINE STORE (KPC owner, 2026-11-13;
huge parks, one layer per park and parks across state lines: 2026-11-14).

Plain words
-----------
The outline store keeps every tract of every park at full detail (about 2 m). It is never thinned and never published as is.
This tool reads store areas (US-NH, US-ME ...) and writes a copy for DRAWING ONLY, in three levels:
  OVERVIEW  one file set per area, every park at most CAP points (3,000); the tolerance used is written on the park;
  MIDDLE    for a park whose overview is more than 25 m off: one file per park and area, at most 30,000 points;
  FINE      for a park whose coarser levels are more than 5 m off: the park's lines at 1 m, cut into square PIECES (tiles) with
            a hard byte cap per piece, so the map loads only the pieces on screen. Whatever is on screen at street level is
            within 5 m of the store (1 m simplification + at most 0.6 m rounding + at most 3 m for a tract drawn once).
A level drops a ring smaller than its own tolerance (it would be under one screen pixel wherever that level is used); the next
level shows it. The FINE level drops nothing.
Rules on the way in (all written into INDEX.json):
  * LICENCE GATE: only records the store index marks publishable (store tool full 2: 'publishable' per record, with its licence
    class and credit line). An older index without that map: the licence text 'CLASS; credit: X' if present, else NOT publishable.
    WDPA / Protected Planet / SPREP never. One record that does not pass keeps the WHOLE park on today's outline (fallback).
  * DOUBTFUL JOINS (a list, or the store's 'check join' flag / tracts 10 km apart): today's outline, flagged.
  * ONE LAYER PER PARK where layers disagree: a small editable table ranks the layers per area (the state / agency's own layer
    over PAD-US). A lower layer's record whose line lies 90% or more inside the land a higher layer draws (or within 30 m of
    its line) is not drawn; any other lower-layer record draws ONLY the stretches of its line outside that land (more than 30 m
    from it), so land only the lower layer has keeps its boundary ('extra') and lines of two layers are never mixed for the
    same land. The layer that won is written per park.
  * DRAW ONCE: a record whose whole line is within 3 m of a line already drawn is not drawn again (it stays listed).
  * A PARK ACROSS AREAS (two states) is built in one run with all its areas: a record in two area stores is drawn from one area
    only, and the lines where the park's own tracts meet at the area border (within 3 m of each other) are not drawn, so the park
    shows as one with no seam or double line at the state line. Such a park carries 'areas' and the run's 'gen'; the map draws it
    new only when every one of its areas is on and from the same run. A park whose other area is not in the run keeps today's
    outline everywhere.
The store files are only read, never changed.

Files (folder OUT/<AREA>/), every file gzip level 9 with mtime 0 (same store = byte-identical files), every file under 1 MB:
  INDEX.json                     format, area, gen, built_with, store sha256s, caps, parts, mid, fine, credits, fallback, won.
  <AREA>.geojson.gz (+ .pN)      OVERVIEW: one feature per park (MultiPolygon). A park with hidden stretches (across areas, or
                                 a lower layer's extra land) has two features instead: role 'line' (MultiLineString, drawn) and
                                 role 'hit' (MultiPolygon of its tracts, for clicks only, never drawn).
  mid/<REF>.geojson.gz           MIDDLE: one MultiLineString feature (this area's part of the park).
  fine/<REF>/<ix>_<iy>.geojson.gz FINE pieces: MultiLineString of the park's lines inside tile ix,iy (tile = T x T degrees,
                                 T in INDEX fine[ref].t; ix = floor(lon / T)). Lines are cut exactly at tile edges, so the
                                 pieces join with no gap and no overlap.
Standard library only, Python 3.9+. No network.

  python3 kpc_display_copy.py build --store DIR --area US-NH [--area US-ME ...] --out DIR [--doubtful CSV] [--precedence JSON]
                                    [--key-dir data/us-key] [--private-preview] [--json report.json]
  python3 kpc_display_copy.py check --out DIR --area US-NH [--public]
Exit 0 = done; 1 = a check failed; 2 = usage error.
"""
import argparse, csv, gzip, hashlib, json, math, pathlib, re, sys, time

FORMAT = 'kpc-display-2'
CAP = 3000                      # OVERVIEW points per park (owner decision 2)
MID_CAP = 30000                 # MIDDLE points per park
MID_OVER_M = 25.0               # a MIDDLE level when the overview is more than this off
FINE_OVER_M = 5.0               # a FINE level when the coarser levels are more than this off
FINE_TOL_M = 1.0                # FINE simplification (the store is ~2 m already)
MAX_PART = 950_000              # overview parts and middle files: under the 1 MB rule with a margin
PIECE_CAP = 128_000             # hard cap per FINE piece (bytes, gzip)
TILE_START = 0.05               # FINE piece size to start with (degrees); halved until every piece is under PIECE_CAP
TILE_MIN = 0.05 / 64
DECIMALS = 5                    # at most 0.6 m of rounding (as today's master files)
MERGE_M = 3.0                   # draw-once distance
SEAM_M = 3.0                    # tracts of one park in two areas closer than this at the border: not drawn there
COVER_M = 30.0                  # precedence: a lower layer's line within this of a higher layer's land is the same land
COVER_DROP = 0.9                # ...for 90% or more of its line = the same land: not drawn at all; less: only its uncovered stretches
LADDER = [0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 80, 100, 120, 150, 200, 250, 300, 400, 500,
          750, 1000, 1500, 2000, 3000, 5000, 7500, 10000, 20000]
LEGACY_PUBLISHABLE = ('OPEN', 'PUBLIC DOMAIN', 'NO TERMS STATED', 'DISCLAIMER ONLY', 'NON-COMMERCIAL', 'US FEDERAL (PUBLIC DOMAIN)')
REFUSE_WORDS = re.compile(r'no[ -]?redistribut|do not redistribut|not for redistribution|no[ -]?derivativ|private|held|restricted|'
                          r'sign[ -]?in|login|token|wdpa|protected ?planet|sprep|not recorded|unclear', re.I)
WDPA = re.compile(r'wdpa|protectedplanet|protected planet|sprep', re.I)
JOIN_LINK_KM, JOIN_FLAG_KM = 5.0, 10.0
PREVIEW_STAMP = 'PRIVATE PREVIEW - licence gate skipped - never publish'
# Owner 2026-11-14: the state / agency's own layer wins over PAD-US. The editable table is kpc_display_precedence.json beside
# this file (best first per area; '*' = every layer not listed); --precedence FILE overrides it. Built-in copy if it is missing.
DEFAULT_PRECEDENCE = {'default': ['*', 'PAD-US'], 'US-NH': ['sgnha', 'sgnhd', 'nhc', 'sgnhc', '*', 'PAD-US']}
try:
    DEFAULT_PRECEDENCE = json.loads((pathlib.Path(__file__).resolve().parent / 'kpc_display_precedence.json').read_text(encoding='utf-8'))
except (OSError, ValueError):
    pass


class DisplayError(Exception):
    pass


# ---- store reading (format 1, kpc_store_read.py) --------------------------------------------------------------------------
SCALE = 10 ** 6


def ring_ints(enc):
    out, x, y = [], 0, 0
    for i in range(0, len(enc) - 1, 2):
        if i == 0: x, y = enc[0], enc[1]
        else: x, y = x + enc[i], y + enc[i + 1]
        out.append((x, y))
    return out


def geometry_sha256(enc_rings):
    canon = json.dumps([[list(p) for p in ring_ints(r)] for r in enc_rings], separators=(',', ':'))
    return hashlib.sha256(canon.encode('ascii')).hexdigest()


def enc_rings(rec, park):
    if rec.get('rings') is None and rec.get('same_geometry_as'):
        for r in park.get('records') or []:
            if r.get('key') == rec['same_geometry_as'] and r.get('rings') is not None: return r['rings']
        raise DisplayError(f"{park.get('ref')}: {rec.get('key')} same_geometry_as {rec['same_geometry_as']} not found")
    return rec.get('rings') or []


def _member_json(raw):
    txt = gzip.decompress(raw).decode('utf-8').strip()
    if txt.startswith(','): txt = txt[1:].strip()
    if txt.endswith(','): txt = txt[:-1].strip()
    return json.loads(txt)


def read_index(store_dir, area):
    d = pathlib.Path(store_dir)
    for name in (f'index-{area}.json', 'index.json'):
        p = d / name
        if p.is_file():
            idx = json.loads(p.read_text(encoding='utf-8'))
            if idx.get('area') == area or name != 'index.json':
                return idx, p
            parks = {k: v for k, v in (idx.get('parks') or {}).items() if str(v.get('file', '')).startswith(area + '.')}
            if parks: return dict(idx, parks=parks, area=area), p
    raise DisplayError(f'no index for {area} in {d}')


def read_park(store_dir, ref, e, handles):
    """One park, its record checksums recomputed (a moved coordinate never passes)."""
    f = handles.get(e['file']) or handles.setdefault(e['file'], open(pathlib.Path(store_dir) / e['file'], 'rb'))
    f.seek(int(e['o'])); raw = f.read(int(e['n']))
    if len(raw) != int(e['n']): raise DisplayError(f'{ref}: store file shorter than the index says')
    p = _member_json(raw)
    if p.get('ref') != ref: raise DisplayError(f'{ref}: index points at {p.get("ref")!r}')
    for r in p.get('records') or []:
        er = enc_rings(r, p)
        if geometry_sha256(er) != r.get('sha256'): raise DisplayError(f'{ref}: record {r.get("key")} checksum does not match')
        if sum(len(x) // 2 for x in er) != r.get('points'): raise DisplayError(f'{ref}: record {r.get("key")} point count')
    fp = hashlib.sha256('|'.join(str(r.get('sha256')) for r in p.get('records') or []).encode()).hexdigest()
    if e.get('fp') and fp != e['fp']: raise DisplayError(f'{ref}: park fingerprint differs from the index')
    return p


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


# ---- licence gate ---------------------------------------------------------------------------------------------------------
def licence_class(text):
    t = str(text or '').strip()
    if not t: return '', ''
    cls, _, rest = t.partition(';')
    m = re.search(r'credit:\s*(.+)$', rest.strip(), re.I)
    return cls.strip().upper(), (m.group(1).strip() if m else '')


def gate(rec, e):
    """(passes, why, class, credit) for one record, from the store index entry e of its park. WDPA never passes."""
    key = rec.get('key')
    blob = ' '.join(str(rec.get(k) or '') for k in ('layer_url', 'agency_label', 'layer', 'licence', 'licence_from', 'licence_class', 'credit'))
    if WDPA.search(blob + ' ' + json.dumps(rec.get('source_detail') or {})[:2000]):
        return False, 'WDPA / Protected Planet / SPREP source', 'WDPA', ''
    pub = e.get('publishable')
    if isinstance(pub, dict):                       # store tool full 2: the index decides, per record
        cls = str((e.get('licence_class') or {}).get(key) or rec.get('licence_class') or 'NOT RECORDED')
        credit = str((e.get('credit') or {}).get(key) or rec.get('credit') or rec.get('agency_label') or rec.get('layer') or '')
        if pub.get(key) is not True: return False, f'not publishable in the store index ({cls})', cls, ''
        if REFUSE_WORDS.search(cls): return False, f'licence class {cls!r} restricts sharing', cls, ''
        return True, '', cls, credit
    text = (e.get('licence') or {}).get(key) or rec.get('licence')   # older index: the licence text, else NOT publishable
    cls, credit = licence_class(text)
    if not cls or cls == 'NOT RECORDED': return False, 'no licence class recorded', cls or 'NOT RECORDED', ''
    if cls not in LEGACY_PUBLISHABLE: return False, f'licence class {cls!r} is not publishable', cls, ''
    if REFUSE_WORDS.search(str(text)): return False, 'licence text restricts sharing', cls, ''
    return True, '', cls, credit or str(rec.get('agency_label') or rec.get('layer') or '')


# ---- geometry -------------------------------------------------------------------------------------------------------------
A_WGS, F_WGS = 6378137.0, 1 / 298.257223563
E2 = F_WGS * (2 - F_WGS)


def local_scale(lat0):
    """metres per degree (east, north) on the WGS84 ellipsoid at latitude lat0 (a local tangent plane)."""
    s = math.sin(math.radians(lat0)); w = math.sqrt(1 - E2 * s * s)
    return math.radians(1) * A_WGS / w * math.cos(math.radians(lat0)), math.radians(1) * A_WGS * (1 - E2) / w ** 3


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    if L == 0: return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / L
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


class Proj:
    """A local tangent plane around (lon0, lat0); longitudes are unwrapped across 180 degrees."""
    def __init__(self, pts):
        lons = [x for x, _ in pts]; lats = [y for _, y in pts]
        self.wrap = (max(lons) - min(lons)) > 180
        lons = [x + 360 if self.wrap and x < 0 else x for x in lons]
        self.lon0 = (min(lons) + max(lons)) / 2; self.lat0 = (min(lats) + max(lats)) / 2
        self.kx, self.ky = local_scale(self.lat0)

    def xy(self, ring):
        w, l0, a0, kx, ky = self.wrap, self.lon0, self.lat0, self.kx, self.ky
        return [((x + 360 if w and x < 0 else x) - l0) * kx for x, _ in ring], [(y - a0) * ky for _, y in ring]


def dp_importance(xs, ys):
    """Douglas-Peucker once, recording for each vertex the tolerance BELOW which it is kept ('effective importance' = its own
    split distance, never more than its parent's). Keeping every vertex with importance > t is exactly Douglas-Peucker at t
    (segment distance, not the infinite line). A closed ring first splits at its farthest point from the start; first, last
    and that point are always kept (importance infinity)."""
    n = len(xs)
    imp = [0.0] * n
    if n == 0: return imp
    imp[0] = imp[n - 1] = math.inf
    if n <= 2: return imp
    closed = xs[0] == xs[-1] and ys[0] == ys[-1]
    if closed:
        far = max(range(1, n - 1), key=lambda i: (xs[i] - xs[0]) ** 2 + (ys[i] - ys[0]) ** 2)
        imp[far] = math.inf
        stack = [(0, far, math.inf), (far, n - 1, math.inf)]
    else:
        stack = [(0, n - 1, math.inf)]
    while stack:
        a, b, cap = stack.pop()
        if b - a < 2: continue
        ax, ay, bx, by = xs[a], ys[a], xs[b], ys[b]
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        best, bi = -1.0, -1
        for i in range(a + 1, b):
            px, py = xs[i] - ax, ys[i] - ay
            if L == 0: d = math.hypot(px, py)
            else:
                t = (px * dx + py * dy) / L
                t = 0.0 if t < 0 else 1.0 if t > 1 else t
                d = math.hypot(px - t * dx, py - t * dy)
            if d > best: best, bi = d, i
        e = min(best, cap)
        imp[bi] = e
        stack.append((a, bi, e)); stack.append((bi, b, e))
    return imp


def kept_at(imp, t):
    """indices kept at tolerance t; a closed ring keeps at least 4 (the most important ones)."""
    k = [i for i, v in enumerate(imp) if v > t]
    if len(imp) >= 4 and len(k) < 4:
        k = sorted(sorted(range(len(imp)), key=lambda i: -imp[i])[:4])
    return k


def dp_keep(xs, ys, tol):
    return kept_at(dp_importance(xs, ys), tol) if tol > 0 else list(range(len(xs)))


def ring_error(xs, ys, kept, qx=None, qy=None):
    """Largest distance (m) from any ORIGINAL vertex to the simplified line (the kept chord that spans it); qx/qy = the kept
    points after rounding. Exact: the largest distance of a segment to a chord is at one of its ends."""
    worst = 0.0
    for a, b in zip(kept, kept[1:]):
        ax, ay = (qx[a], qy[a]) if qx else (xs[a], ys[a])
        bx, by = (qx[b], qy[b]) if qx else (xs[b], ys[b])
        for i in range(a, b + 1):
            d = seg_dist(xs[i], ys[i], ax, ay, bx, by)
            if d > worst: worst = d
    return worst


def signed_area(ring):
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:])) / 2


def in_ring(x, y, r):
    ins = False
    j = len(r) - 1
    for i in range(len(r)):
        xi, yi = r[i]; xj, yj = r[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi: ins = not ins
        j = i
    return ins


def polygons(rings):
    """Esri rings -> GeoJSON polygons [[outer, hole, ...]]: outer rings clockwise (negative signed area), holes counter-
    clockwise; a hole goes to the smallest outer ring holding its first point; a hole no outer holds is drawn on its own."""
    outers, holes = [], []
    for r in rings:
        if len(r) < 4: continue
        (outers if signed_area(r) <= 0 else holes).append(r)
    if not outers and holes: outers, holes = holes, []
    polys = [[o] for o in outers]
    area = [abs(signed_area(o)) for o in outers]
    for h in holes:
        x, y = h[0]; best = None
        for i, o in enumerate(outers):
            if in_ring(x, y, o) and (best is None or area[i] < area[best]): best = i
        if best is None: polys.append([h])
        else: polys[best].append(h)
    return polys


class SegGrid:
    """Segments in metres, in CELL m squares, for 'how far is the nearest line' questions. A segment is stored only in the
    cells it passes through (walked at half a cell); a search looks one ring of cells further than the distance needs, so a
    segment clipping a cell corner between two walk steps is never missed."""
    CELL = 25.0

    def __init__(self):
        self.g = {}

    def add_ring(self, xs, ys):
        C = self.CELL
        for i in range(len(xs) - 1):
            ax, ay, bx, by = xs[i], ys[i], xs[i + 1], ys[i + 1]
            s = (ax, ay, bx, by)
            n = int(math.hypot(bx - ax, by - ay) / (C / 2)) + 1
            cells = {(int(math.floor((ax + (bx - ax) * k / n) / C)), int(math.floor((ay + (by - ay) * k / n) / C))) for k in range(n + 1)}
            for c in cells:
                self.g.setdefault(c, []).append(s)

    def dist(self, x, y, limit):
        C, best = self.CELL, limit
        R = int(math.ceil(limit / C)) + 1
        cx0, cy0 = int(math.floor(x / C)), int(math.floor(y / C))
        for r in range(0, R + 1):
            if (r - 2) * C > best: break   # a cell in ring r is at least (r - 1) * C away; one ring more for clipped corners
            for cx in range(cx0 - r, cx0 + r + 1):
                for cy in ((cy0 - r, cy0 + r) if abs(cx - cx0) != r else range(cy0 - r, cy0 + r + 1)):
                    for s in self.g.get((cx, cy), ()):
                        d = seg_dist(x, y, *s)
                        if d < best: best = d
        return best


def samples(xs, ys, step=5.0):
    for i in range(len(xs)):
        yield xs[i], ys[i]
        if i + 1 < len(xs):
            dx, dy = xs[i + 1] - xs[i], ys[i + 1] - ys[i]
            n = int(math.hypot(dx, dy) // step)
            for k in range(1, n + 1):
                t = k / (n + 1)
                yield xs[i] + t * dx, ys[i] + t * dy


# ---- one park -------------------------------------------------------------------------------------------------------------
class Rec:
    __slots__ = ('area', 'key', 'layer', 'rings', 'sha', 'cluster', 'xy', 'imp', 'hide')

    def __init__(self, area, key, layer, rings, sha):
        self.area, self.key, self.layer, self.rings, self.sha = area, key, layer, rings, sha
        self.cluster = None; self.xy = None; self.imp = None; self.hide = None   # hide[ring][i]: vertex on a seam / covered by a higher layer


def clusters(recs):
    """Records whose boxes are within JOIN_LINK_KM are one cluster, projected on its own plane (a park 800 km wide is never
    measured on one flat plane). -> (number of clusters, smallest gap between clusters in km)."""
    boxes = []
    for r in recs:
        xs = [x for ring in r.rings for x, _ in ring]; ys = [y for ring in r.rings for _, y in ring]
        boxes.append((min(xs), min(ys), max(xs), max(ys)))
    n = len(recs); parent = list(range(n))

    def find(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i

    def gap(a, b):
        lat = (a[1] + a[3]) / 2; kx = 111.32 * max(0.05, math.cos(math.radians(lat)))
        return math.hypot(max(0.0, max(a[0], b[0]) - min(a[2], b[2])) * kx, max(0.0, max(a[1], b[1]) - min(a[3], b[3])) * 110.574)
    order = sorted(range(n), key=lambda i: boxes[i][0])
    for a in range(n):          # sweep on x: only boxes whose x ranges come within the link distance are compared
        i = order[a]; bi = boxes[i]
        kx = 111.32 * max(0.05, math.cos(math.radians(min(85.0, max(abs(bi[1]), abs(bi[3]))))))
        for b in range(a + 1, n):
            j = order[b]; bj = boxes[j]
            if (bj[0] - bi[2]) * kx > JOIN_LINK_KM: break
            if gap(bi, bj) < JOIN_LINK_KM: parent[find(i)] = find(j)
    groups = {}
    for i in range(n): groups.setdefault(find(i), []).append(i)
    gl = list(groups.values())
    for g in gl:
        pts = [(boxes[i][0], boxes[i][1]) for i in g] + [(boxes[i][2], boxes[i][3]) for i in g]
        pr = Proj(pts)
        for i in g:
            recs[i].cluster = pr
            recs[i].xy = [pr.xy(ring) for ring in recs[i].rings]
    if len(gl) < 2: return 1, 0.0
    gb = [(min(boxes[i][0] for i in g), min(boxes[i][1] for i in g), max(boxes[i][2] for i in g), max(boxes[i][3] for i in g)) for g in gl]
    if len(gb) > 400: return len(gl), 0.0     # very many groups: an archipelago, not a doubtful far join
    return len(gl), min(gap(gb[a], gb[b]) for a in range(len(gb)) for b in range(a + 1, len(gb)))


def rank_of(prec, area, layer):
    order = prec.get(area) or prec.get('default') or ['*']
    if layer in order: return order.index(layer)
    return order.index('*') if '*' in order else len(order)


def precedence(recs, prec):
    """One layer per park: layers in rank order. A lower layer's record is measured against the land the higher layers draw
    (inside it, or within COVER_M of its line): 90% or more covered = not drawn; otherwise only its uncovered stretches are drawn
    (r.hide marks the covered vertices). -> (kept, won layer, {layer: not drawn}, {layer: kept for land only it has})."""
    for r in recs: r.hide = None
    if len({r.layer for r in recs}) < 2: return list(recs), (recs[0].layer if recs else ''), {}, {}
    byrank = {}
    for r in recs: byrank.setdefault((rank_of(prec, r.area, r.layer), r.layer), []).append(r)
    top = min(byrank)
    kept, dropped, extra, grids, polys = [], {}, {}, {}, {}

    def covered(r, x, y):
        g = grids.get(id(r.cluster))
        if g is None: return False
        if g.dist(x, y, COVER_M * 1.5) <= COVER_M: return True
        return any(b[0] <= x <= b[2] and b[1] <= y <= b[3] and in_ring(x, y, ring) for b, ring in polys.get(id(r.cluster), ()))
    for key in sorted(byrank):
        rk, layer = key
        add = []
        for r in sorted(byrank[key], key=lambda r: (-sum(len(x) for x in r.rings), r.key)):
            if key != top and id(r.cluster) in grids:
                mask = [[covered(r, x, y) for x, y in zip(xs, ys)] for xs, ys in r.xy]
                n = sum(len(m) for m in mask); c = sum(sum(m) for m in mask)
                if c >= COVER_DROP * n:
                    dropped[layer] = dropped.get(layer, 0) + 1; continue
                if c: r.hide = mask
                extra[layer] = extra.get(layer, 0) + 1
            add.append(r)
        for r in add:
            g = grids.setdefault(id(r.cluster), SegGrid())
            for xs, ys in r.xy:
                g.add_ring(xs, ys)
                if len(xs) >= 4: polys.setdefault(id(r.cluster), []).append(((min(xs), min(ys), max(xs), max(ys)), list(zip(xs, ys))))
        kept += add
    return kept, top[1], dropped, extra


def draw_once(recs, merge_m=MERGE_M):
    """A record whose every vertex and every 5 m point along its edges is within merge_m of a line already drawn is not drawn
    again. Largest first. -> (drawn, merged keys)."""
    if merge_m <= 0 or len(recs) < 2: return list(recs), []
    grids, drawn, merged = {}, [], []
    for r in sorted(recs, key=lambda r: (-sum(len(x) for x in r.rings), r.area, r.key)):
        g = grids.get(id(r.cluster))
        if g is not None and all(g.dist(x, y, merge_m * 2) <= merge_m for xs, ys in r.xy for x, y in samples(xs, ys)):
            merged.append(r.key); continue
        drawn.append(r)
        g = grids.setdefault(id(r.cluster), SegGrid())
        for xs, ys in r.xy: g.add_ring(xs, ys)
    return drawn, merged


def mark_seams(recs, seam_m=SEAM_M):
    """A park in two or more areas: a vertex is on the border SEAM when it lies within seam_m of a line of the park's records
    from ANOTHER area AND the two tracts lie on opposite sides there (a point 5 m inside this tract, beside the vertex, is not
    inside the other area's tract). Two copies of the same boundary with both tracts on the same side are not a seam (the line
    stays). Seam vertices are added to r.hide. -> number of seam vertices."""
    areas = {r.area for r in recs}
    if len(areas) < 2: return 0
    n = 0
    for a in areas:
        grids, polys = {}, {}
        for o in recs:
            if o.area != a:
                g = grids.setdefault(id(o.cluster), SegGrid())
                for xs, ys in o.xy:
                    g.add_ring(xs, ys)
                    if len(xs) >= 4: polys.setdefault(id(o.cluster), []).append(((min(xs), min(ys), max(xs), max(ys)), list(zip(xs, ys))))
        for r in recs:
            if r.area != a: continue
            g = grids.get(id(r.cluster)); ps = polys.get(id(r.cluster), ())
            sm = []
            for xs, ys in r.xy:
                ring = list(zip(xs, ys)); m = []
                for i in range(len(xs)):
                    on = g is not None and g.dist(xs[i], ys[i], seam_m * 2) <= seam_m
                    if on:   # opposite sides? probe 5 m inside this tract beside either neighbouring segment (a corner has two)
                        hits = []
                        for j in (i - 1, i + 1):
                            if not 0 <= j < len(xs): continue
                            dx, dy = xs[j] - xs[i], ys[j] - ys[i]; L = math.hypot(dx, dy)
                            if L == 0: continue
                            if g.dist((xs[i] + xs[j]) / 2, (ys[i] + ys[j]) / 2, seam_m * 2) > seam_m: continue   # that segment is not on the other line
                            mx, my = xs[i] + dx * 0.5, ys[i] + dy * 0.5
                            q = [c for c in ((mx - dy / L * 5, my + dx / L * 5), (mx + dy / L * 5, my - dx / L * 5)) if in_ring(c[0], c[1], ring)][:1]
                            if q: hits.append(not any(b[0] <= q[0][0] <= b[2] and b[1] <= q[0][1] <= b[3] and in_ring(q[0][0], q[0][1], rg) for b, rg in ps))
                        on = any(hits)
                    m.append(on)
                sm.append(m)
            n += sum(sum(m) for m in sm)
            if any(any(m) for m in sm):
                r.hide = [[x or y for x, y in zip(h, m)] for h, m in zip(r.hide, sm)] if r.hide else sm
    return n


def level(recs, cap, decimals=DECIMALS, ladder=LADDER, fixed=None):
    """Simplify every drawn record for one level: the smallest ladder step that brings the park to cap points or fewer, or the
    fixed tolerance. A ring smaller than the tolerance (box diagonal) is dropped at this level, never at 1 m or less.
    -> dict(tol, points, worst (m, measured after rounding), hidden rings, rings=[(rec, ring index, kept, rounded ring)])."""
    for r in recs:
        if r.imp is None: r.imp = [dp_importance(xs, ys) for xs, ys in r.xy]
    diag = [(r, i, math.hypot(max(xs) - min(xs), max(ys) - min(ys))) for r in recs for i, (xs, ys) in enumerate(r.xy)]

    def count(t):
        n = 0
        for r, i, dg in diag:
            if t > 1 and dg < t: continue
            imp = r.imp[i]
            n += len(imp) if t <= 0 else max(sum(1 for v in imp if v > t), min(4, len(imp)))
        return n
    if fixed is not None: t = fixed
    else:
        steps = [0.0] + list(ladder)
        t = steps[-1]
        for s in steps:
            if count(s) <= cap: t = s; break
    q = 10 ** decimals
    out, worst, hidden, pts = [], 0.0, 0, 0
    for r, i, dg in diag:
        if t > 1 and dg < t: hidden += 1; worst = max(worst, dg); continue
        xs, ys = r.xy[i]
        k = list(range(len(xs))) if t <= 0 else kept_at(r.imp[i], t)
        ring = r.rings[i]
        qr = [(round(ring[j][0] * q) / q, round(ring[j][1] * q) / q) for j in k]
        qx, qy = r.cluster.xy(qr)
        fx, fy = [0.0] * len(xs), [0.0] * len(xs)
        for jj, j in enumerate(k): fx[j], fy[j] = qx[jj], qy[jj]
        worst = max(worst, ring_error(xs, ys, k, fx, fy))
        out.append((r, i, k, qr)); pts += len(k)
    return {'tol': t, 'points': pts, 'worst': worst, 'hidden': hidden, 'rings': out}


def lines_of(lv, area):
    """This area's lines at a level, hidden stretches (border seam, land a higher layer draws) left out: [[(lon, lat), ...], ...]."""
    out = []
    for r, i, k, qr in lv['rings']:
        if r.area != area: continue
        seam = r.hide[i] if r.hide else None
        if not seam or not any(seam):
            out.append(qr); continue
        cur = []
        for jj in range(len(k) - 1):
            a, b = k[jj], k[jj + 1]
            if all(seam[a:b + 1]):            # the whole stretch is hidden (border seam / a higher layer's land)
                if len(cur) >= 2: out.append(cur)
                cur = []; continue
            if not cur: cur = [qr[jj]]
            cur.append(qr[jj + 1])
        if len(cur) >= 2: out.append(cur)
    return out


def polys_of(lv, area):
    rings = {}
    for r, i, k, qr in lv['rings']:
        if r.area == area: rings.setdefault(r.key, []).append(qr)
    out = []
    for rs in rings.values():
        for poly in polygons(rs): out.append([[list(p) for p in ring] for ring in poly])
    return out


def cut_tiles(lines, T):
    """Cut lines at every multiple of T degrees (both axes), exactly; each piece goes to the tile holding its middle.
    -> {(ix, iy): [line, ...]}. Neighbouring pieces share their cut point, so they join with no gap and no overlap."""
    out = {}
    for line in lines:
        cur, ck = [], None
        for (x1, y1), (x2, y2) in zip(line, line[1:]):
            ts = {0.0, 1.0}
            for a, b in ((x1, x2), (y1, y2)):
                if a != b:
                    lo, hi = min(a, b), max(a, b)
                    for m in range(math.floor(lo / T) + 1, math.floor(hi / T) + 1):
                        t = (m * T - a) / (b - a)
                        if 0 < t < 1: ts.add(t)
            ts = sorted(ts)
            for t0, t1 in zip(ts, ts[1:]):
                p0 = (x1, y1) if t0 == 0 else (x1 + (x2 - x1) * t0, y1 + (y2 - y1) * t0)
                p1 = (x2, y2) if t1 == 1 else (x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1)
                key = (math.floor((p0[0] + p1[0]) / 2 / T), math.floor((p0[1] + p1[1]) / 2 / T))
                if key != ck:
                    if len(cur) >= 2: out.setdefault(ck, []).append(cur)
                    cur, ck = [p0], key
                cur.append(p1)
        if len(cur) >= 2: out.setdefault(ck, []).append(cur)
    return out


def gz(obj):
    return gzip.compress(json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8'), 9, mtime=0)


def rnd(lines, decimals):
    q = 10 ** decimals
    return [[[round(x * q) / q, round(y * q) / q] for x, y in ln] for ln in lines]


def read_doubtful(path, areas):
    """A CSV with a 'park' (or 'ref') column and an optional 'state' column: ref -> reason."""
    out = {}
    if not path: return out
    sts = {a.split('-', 1)[1] for a in ([areas] if isinstance(areas, str) else areas) if a.startswith('US-')}
    with open(path, encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            ref = (row.get('park') or row.get('ref') or '').strip()
            if not ref: continue
            if sts and row.get('state') and row['state'].strip() not in sts: continue
            why = ' '.join(x for x in (row.get('matcher_review_state'), row.get('matcher_doubt_code')) if x)
            out[ref] = 'doubtful join' + (f' ({why})' if why else '')
    return out


def key_areas(key_dir):
    """ref -> [areas] from the key files (data/us-key/US-XX.json and parts): which areas a park is in."""
    out = {}
    if not key_dir: return out
    for p in sorted(pathlib.Path(key_dir).glob('US-*.json')):
        m = re.match(r'US-([A-Z]{2})(\.p\d+)?\.json$', p.name)
        if not m: continue
        try: d = json.loads(p.read_text(encoding='utf-8'))
        except Exception: continue
        parks = d.get('parks') or {}
        for ref in (parks.keys() if isinstance(parks, dict) else [x.get('ref') for x in parks if isinstance(x, dict)]):
            a = 'US-' + m.group(1)
            if a not in out.setdefault(ref, []): out[ref].append(a)
    return out


# ---- build ----------------------------------------------------------------------------------------------------------------
def build(store_dir, areas, out_dir, cap=CAP, doubtful=None, preview=False, decimals=DECIMALS, merge_m=MERGE_M,
          precedence_table=None, park_areas=None, max_part=MAX_PART, piece_cap=PIECE_CAP, mid_cap=MID_CAP, log=print):
    """Build the display copy of one or more areas in one run (a park in two areas needs both in the same run)."""
    t0 = time.time()
    areas = [areas] if isinstance(areas, str) else sorted(set(areas))
    for a in areas:
        if not re.fullmatch(r'(US|CA)-[A-Z]{2,3}|W-[A-Z]{2}', a): raise DisplayError(f'bad area {a!r}')
    if preview and re.search(r'(^|/)(data/display|data/released|_site)(/|$)', str(pathlib.Path(out_dir).resolve()).replace('\\', '/')):
        raise DisplayError('a PRIVATE PREVIEW is never written into a public folder')
    prec = dict(DEFAULT_PRECEDENCE, **(precedence_table or {}))
    idx, sha = {}, {}
    for a in areas:
        ix, p = read_index(store_dir, a)
        idx[a] = (ix, p)
        for f in sorted({e['file'] for e in ix['parks'].values()}):
            sha[f] = file_sha256(pathlib.Path(store_dir) / f)
            meta = (ix.get('files') or {}).get(f) or {}
            if meta.get('sha256') and meta['sha256'] != sha[f]:
                raise DisplayError(f'{f}: sha256 differs from the index (store and index are not from the same build)')
    gen = hashlib.sha256(json.dumps(sorted(sha.items())).encode()).hexdigest()[:12]
    doubt = dict(doubtful or {})
    in_areas = {}
    for a in areas:
        for ref in idx[a][0]['parks']: in_areas.setdefault(ref, []).append(a)
    handles = {}
    res = {a: {'feats': [], 'mid': {}, 'fine': {}, 'fallback': {}, 'credits': {}, 'won': {}} for a in areas}
    rows, peak_pts = [], 0
    try:
        for ref in sorted(in_areas):
            mine = in_areas[ref]
            others = [a for a in (park_areas or {}).get(ref, []) if a not in mine]

            def fall(why):
                for a in mine: res[a]['fallback'][ref] = why
            if others:
                fall(f"also in {', '.join(others)}, which is not in this run (a park's areas are built together)"); continue
            parks, why_not, credit, recs, name = {}, [], {}, [], ref
            for a in mine:
                e = idx[a][0]['parks'][ref]
                p = read_park(store_dir, ref, e, handles); parks[a] = (e, p); name = p.get('name') or name
                if p.get('circle') or p.get('grade') != 'official':
                    why_not.append(f'{a}: not an official outline in the store'); continue
                if e.get('check_join'):
                    cj = e['check_join']; doubt.setdefault(ref, f"check join (tracts in {cj.get('groups')} groups {cj.get('gap_km')} km apart)")
                for r in p.get('records') or []:
                    if preview:
                        ok, why, cr = True, '', str(r.get('credit') or r.get('agency_label') or r.get('layer') or '')
                        if WDPA.search(json.dumps({k: r.get(k) for k in ('layer_url', 'agency_label', 'licence', 'credit')})):
                            ok, why = False, 'WDPA / Protected Planet / SPREP source'   # never, not even in a preview
                    else:
                        ok, why, cls, cr = gate(r, e)
                    if not ok: why_not.append(f"{r.get('key')}: {why}"); continue
                    credit[r.get('layer') or ''] = cr
            if why_not:
                fall('licence gate: ' + '; '.join(why_not[:3]) + (f' (+{len(why_not) - 3} more)' if len(why_not) > 3 else '')); continue
            seen = set()
            for a in mine:                      # a record in two area stores (same key or same geometry) is drawn from one area
                e, p = parks[a]
                for r in p.get('records') or []:
                    if r.get('key') in seen or r.get('sha256') in seen: continue
                    seen.update((r.get('key'), r.get('sha256')))
                    rings = [[(x / SCALE, y / SCALE) for x, y in ring_ints(er)] for er in enc_rings(r, p)]
                    rings = [rg for rg in rings if len(rg) >= 2]
                    if rings: recs.append(Rec(a, r.get('key'), r.get('layer') or '', rings, r.get('sha256')))
            n_records = sum(len(parks[a][1].get('records') or []) for a in mine)
            if not recs: fall('no drawable rings in the store'); continue
            ng, sep = clusters(recs)
            if ng > 1 and sep >= JOIN_FLAG_KM: doubt.setdefault(ref, f'check join (tracts in {ng} groups {sep:.1f} km apart)')
            if ref in doubt: fall(doubt[ref]); continue
            store_pts = sum(len(x) for r in recs for x in r.rings)
            peak_pts = max(peak_pts, store_pts)
            kept, won, dropped, extra = precedence(recs, prec)
            drawn, merged = draw_once(kept, merge_m)
            multi = len(mine) > 1
            n_seam = mark_seams(drawn) if multi else 0
            as_lines = multi or any(r.hide for r in drawn)   # some stretches hidden: drawn as lines, plus a click-only area
            ov = level(drawn, cap, decimals=decimals)
            mid = fine = None
            if ov['worst'] > MID_OVER_M:
                mid = level(drawn, mid_cap, decimals=decimals)
                for a in mine:   # each area's middle file stays under the part limit: raise the tolerance until it does
                    while len(gz({'type': 'Feature', 'geometry': {'type': 'MultiLineString', 'coordinates': rnd(lines_of(mid, a), decimals)}})) > max_part:
                        nxt = [s for s in LADDER if s > mid['tol']]
                        if not nxt: raise DisplayError(f'{ref}: the middle level is over {max_part} bytes even at the largest step')
                        mid = level(drawn, 0, fixed=nxt[0], decimals=decimals)
            if (mid or ov)['worst'] > FINE_OVER_M:
                fine = level(drawn, 0, fixed=FINE_TOL_M, decimals=decimals)
            merged_add = merge_m if merged else 0.0
            for a in mine:
                lay = sorted({r.layer for r in drawn if r.area == a})
                base = {'ref': ref, 'name': name, 'g': 'official', 'detail_m': ov['tol'], 'worst_m': round(ov['worst'] + merged_add, 1),
                        'points': sum(len(k) for r, i, k, q in ov['rings'] if r.area == a), 'store_points': store_pts,
                        'records': [r.key for r in kept if r.area == a], 'layers': lay, 'won': won, 'cr': lay,
                        'mid': bool(mid), 'fine': bool(fine)}
                if multi: base.update({'areas': mine, 'gen': gen})
                if as_lines:
                    res[a]['feats'].append({'type': 'Feature', 'properties': dict(base, role='line'),
                                            'geometry': {'type': 'MultiLineString', 'coordinates': rnd(lines_of(ov, a), decimals)}})
                    res[a]['feats'].append({'type': 'Feature', 'properties': dict(base, role='hit'),
                                            'geometry': {'type': 'MultiPolygon', 'coordinates': polys_of(ov, a)}})
                else:
                    res[a]['feats'].append({'type': 'Feature', 'properties': base, 'geometry': {'type': 'MultiPolygon', 'coordinates': polys_of(ov, a)}})
                for l in lay: res[a]['credits'][l] = credit.get(l, l)
                res[a]['won'][ref] = {'won': won, 'dropped': dropped, 'extra': extra, 'drawn_once': len(merged)}
                if mid:
                    res[a]['mid'][ref] = (mid['tol'], {'type': 'Feature', 'properties': {'ref': ref, 'level': 'mid', 'detail_m': mid['tol'],
                                                                                         'worst_m': round(mid['worst'] + merged_add, 1)},
                                                       'geometry': {'type': 'MultiLineString', 'coordinates': rnd(lines_of(mid, a), decimals)}})
                if fine:
                    lines = lines_of(fine, a)
                    T = TILE_START
                    while True:
                        tiles = cut_tiles(lines, T)
                        blobs = {k: gz({'type': 'FeatureCollection', 'kpc': {'format': FORMAT, 'area': a, 'gen': gen, 'fine': ref, 't': T, 'tile': list(k)},
                                        'features': [{'type': 'Feature', 'properties': {'ref': ref, 'level': 'fine', 'detail_m': fine['tol']},
                                                      'geometry': {'type': 'MultiLineString', 'coordinates': rnd(v, decimals)}}]}) for k, v in tiles.items()}
                        if not blobs or max(len(b) for b in blobs.values()) <= piece_cap: break
                        if T / 2 < TILE_MIN: raise DisplayError(f'{ref}: a fine piece is over {piece_cap} bytes even at the smallest tile')
                        T /= 2
                    res[a]['fine'][ref] = (fine['tol'], T, blobs)
            fb = [len(b) for a in mine for b in (res[a]['fine'].get(ref, (0, 0, {}))[2].values())]
            rows.append({'ref': ref, 'name': name, 'areas': mine, 'records': n_records, 'distinct_records': len(recs),
                         'kept_after_precedence': len(kept), 'drawn_records': len(drawn), 'won': won, 'dropped': dropped,
                         'extra': extra, 'drawn_once': len(merged), 'seam_vertices': n_seam, 'store_points': store_pts,
                         'points': ov['points'], 'detail_m': ov['tol'], 'worst_m': round(ov['worst'], 2), 'hidden_rings': ov['hidden'],
                         'mid_points': mid['points'] if mid else None, 'mid_detail_m': mid['tol'] if mid else None,
                         'mid_worst_m': round(mid['worst'], 2) if mid else None,
                         'mid_bytes': sum(len(gz(res[a]['mid'][ref][1])) for a in mine) if mid else None,
                         'fine_points': fine['points'] if fine else None, 'fine_worst_m': round(fine['worst'], 2) if fine else None,
                         'fine_t': {a: res[a]['fine'][ref][1] for a in mine} if fine else None,
                         'fine_pieces': len(fb) if fine else None, 'fine_bytes': sum(fb) if fine else None,
                         'fine_piece_max': max(fb, default=0) if fine else None})
    finally:
        for f in handles.values(): f.close()
    reps = {}
    for a in areas:
        reps[a] = write_area(out_dir, a, res[a], gen, areas, {f: sha[f] for f in sha}, cap, decimals, merge_m, preview,
                             max_part, idx[a][1].name, prec)
        log(f"{a}: {reps[a]['parks']} parks drawn, {reps[a]['fallback']} kept on today's outline, {reps[a]['mid']} middle, "
            f"{reps[a]['fine']} fine ({reps[a]['pieces']} pieces); {reps[a]['bytes_parts']:,} B overview, {reps[a]['bytes_mid']:,} B middle, "
            f"{reps[a]['bytes_fine']:,} B fine")
    rep = {'areas': areas, 'gen': gen, 'seconds': round(time.time() - t0, 2), 'largest_park_points': peak_pts, 'per_area': reps, 'rows': rows,
           'fallback_reasons': {a: res[a]['fallback'] for a in areas}}
    for k in ('fallback', 'bytes_parts', 'bytes_mid', 'bytes_fine', 'pieces'): rep[k] = sum(r[k] for r in reps.values())
    rep['parks_drawn'] = len(rows)
    return rep


def write_area(out_dir, area, R, gen, built_with, store_sha, cap, decimals, merge_m, preview, max_part, idx_name, prec):
    out = pathlib.Path(out_dir) / area
    if out.exists():
        for q in sorted(out.rglob('*'), key=lambda q: -len(q.parts)):
            if q.is_file(): q.unlink()
            elif q.is_dir(): q.rmdir()
    out.mkdir(parents=True, exist_ok=True)
    head = {'area': area, 'format': FORMAT, 'gen': gen}
    if preview: head['stamp'] = PREVIEW_STAMP
    parts, cur = [], []
    feats = R['feats']
    i = 0
    while i < len(feats):                      # a park's line and hit features stay together in one part
        grp = [feats[i]]
        if feats[i]['properties'].get('role') == 'line' and i + 1 < len(feats) and feats[i + 1]['properties'].get('role') == 'hit':
            grp.append(feats[i + 1])
        i += len(grp)
        if cur and len(gz({'type': 'FeatureCollection', 'kpc': head, 'features': cur + grp})) > max_part:
            parts.append(cur); cur = []
        cur += grp
        if len(gz({'type': 'FeatureCollection', 'kpc': head, 'features': cur})) > max_part:
            raise DisplayError(f"{grp[0]['properties']['ref']}: one park is over {max_part} bytes even alone (lower --cap)")
    if cur: parts.append(cur)
    plist = []
    for n, ps in enumerate(parts, 1):
        name = f'{area}.geojson.gz' if n == 1 else f'{area}.p{n}.geojson.gz'
        b = gz({'type': 'FeatureCollection', 'kpc': dict(head, part=[n, len(parts)]), 'features': ps})
        (out / name).write_bytes(b)
        plist.append([name, hashlib.sha256(b).hexdigest()[:12], len(ps), len(b)])
    mlist, flist = {}, {}
    for ref, (tol, feat) in sorted(R['mid'].items()):
        b = gz({'type': 'FeatureCollection', 'kpc': dict(head, mid=ref), 'features': [feat]})
        name = f'mid/{ref}.geojson.gz'
        (out / 'mid').mkdir(exist_ok=True); (out / name).write_bytes(b)
        mlist[ref] = [name, hashlib.sha256(b).hexdigest()[:12], tol, len(b)]
    for ref, (tol, T, blobs) in sorted(R['fine'].items()):
        (out / 'fine' / ref).mkdir(parents=True, exist_ok=True)
        tl = {}
        for (ix, iy), b in sorted(blobs.items()):
            if preview:   # the stamp goes into every piece too
                d = json.loads(gzip.decompress(b)); d['kpc']['stamp'] = PREVIEW_STAMP; b = gz(d)
            (out / 'fine' / ref / f'{ix}_{iy}.geojson.gz').write_bytes(b)
            tl[f'{ix}_{iy}'] = [hashlib.sha256(b).hexdigest()[:12], len(b)]
        flist[ref] = {'detail_m': tol, 't': T, 'tiles': tl}
    index = {'format': FORMAT, 'area': area, 'gen': gen, 'built_with': built_with,
             'made': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'store': store_sha, 'store_index': idx_name,
             'cap': cap, 'mid_cap': MID_CAP, 'mid_over_m': MID_OVER_M, 'fine_over_m': FINE_OVER_M, 'fine_tol_m': FINE_TOL_M,
             'piece_cap': PIECE_CAP, 'decimals': decimals, 'merge_m': merge_m, 'seam_m': SEAM_M, 'cover_m': COVER_M,
             'precedence': {k: v for k, v in prec.items() if k in ('default', area)},
             'parks': len({f['properties']['ref'] for f in R['feats']}), 'parts': plist, 'mid': mlist, 'fine': flist,
             'credits': dict(sorted(R['credits'].items())), 'won': dict(sorted(R['won'].items())),
             'fallback': dict(sorted(R['fallback'].items())),
             'about': 'Display copy for drawing only (overview / middle / fine pieces). A park not listed keeps its old outline on the map. '
                      'Never used for "am I in the park" or 2-fers.'}
    if preview: index['stamp'] = PREVIEW_STAMP
    (out / 'INDEX.json').write_text(json.dumps(index, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return {'parks': index['parks'], 'fallback': len(R['fallback']), 'mid': len(mlist), 'fine': len(flist),
            'pieces': sum(len(v['tiles']) for v in flist.values()), 'bytes_parts': sum(x[3] for x in plist),
            'bytes_mid': sum(v[3] for v in mlist.values()), 'bytes_fine': sum(t[1] for v in flist.values() for t in v['tiles'].values())}


NAME_RX = re.compile(r'(mid/[A-Z0-9-]+|fine/[A-Z0-9-]+/-?\d+_-?\d+|[A-Z0-9-]+(\.p\d+)?)\.geojson\.gz')


def check(out_dir, area, max_part=1_000_000, public=False, piece_cap=PIECE_CAP):
    """Re-read a written display copy: every file under its cap, sha12 as listed, parts join, every park once, the preview
    stamp consistent (refused with public=True), nothing unlisted (public=True), credits named. -> problems (empty = good)."""
    out = pathlib.Path(out_dir) / area
    probs = []
    try: idx = json.loads((out / 'INDEX.json').read_text(encoding='utf-8'))
    except Exception as e: return [f'INDEX.json unreadable: {e}']
    if idx.get('format') != FORMAT: probs.append('wrong format')
    if public and idx.get('stamp'): probs.append('a PRIVATE PREVIEW: never published')
    if idx.get('area') != area: probs.append(f"INDEX is for {idx.get('area')!r}, not {area}")
    names = [x[0] for x in idx.get('parts') or []] + [v[0] for v in (idx.get('mid') or {}).values()]
    names += [f'fine/{ref}/{t}.geojson.gz' for ref, v in (idx.get('fine') or {}).items() for t in (v.get('tiles') or {})]
    if any('..' in n or n.startswith('/') or not NAME_RX.fullmatch(n) for n in names):
        probs.append('a file name in INDEX is not a display file name'); return probs
    if public:
        listed = {'INDEX.json'} | set(names)
        extra = [x for x in (str(q.relative_to(out)).replace('\\', '/') for q in out.rglob('*') if q.is_file()) if x not in listed]
        if extra: probs.append(f'files not listed in INDEX: {extra[:5]}')
    seen = set()
    for name, sha12, n, size in idx.get('parts') or []:
        p = out / name
        b = p.read_bytes() if p.is_file() else b''
        if not b: probs.append(f'{name} missing'); continue
        if len(b) > max_part: probs.append(f'{name} is {len(b)} bytes (over {max_part})')
        if hashlib.sha256(b).hexdigest()[:12] != sha12: probs.append(f'{name} sha differs from INDEX')
        d = json.loads(gzip.decompress(b))
        if (d.get('kpc') or {}).get('stamp') != idx.get('stamp'): probs.append(f'{name}: preview stamp differs from INDEX')
        if len(d.get('features') or []) != n: probs.append(f'{name}: feature count differs from INDEX')
        for f in d.get('features') or []:
            pr = f['properties']; r = pr['ref']; role = pr.get('role', 'park')
            if (r, role) in seen: probs.append(f'{r} {role} twice')
            seen.add((r, role))
            if r in (idx.get('fallback') or {}): probs.append(f'{r} both drawn and fallback')
            for c in pr.get('cr') or []:
                if c not in (idx.get('credits') or {}): probs.append(f'{r}: credit {c} not in INDEX credits')
            if pr.get('mid') and r not in (idx.get('mid') or {}): probs.append(f'{r}: middle level missing')
            if pr.get('fine') and r not in (idx.get('fine') or {}): probs.append(f'{r}: fine level missing')
            if pr.get('areas') and (pr.get('gen') != idx.get('gen') or area not in pr['areas']): probs.append(f'{r}: areas / gen inconsistent')
    if len({r for r, _ in seen}) != idx.get('parks'): probs.append(f"{len({r for r, _ in seen})} parks in parts, INDEX says {idx.get('parks')}")
    for ref, (name, sha12, _t, size) in (idx.get('mid') or {}).items():
        b = (out / name).read_bytes() if (out / name).is_file() else b''
        if not b or hashlib.sha256(b).hexdigest()[:12] != sha12: probs.append(f'mid {ref}: missing or sha differs')
        elif len(b) > max_part: probs.append(f'mid {ref}: over {max_part} bytes')
    for ref, v in (idx.get('fine') or {}).items():
        for t, (sha12, size) in (v.get('tiles') or {}).items():
            q = out / 'fine' / ref / f'{t}.geojson.gz'
            b = q.read_bytes() if q.is_file() else b''
            if not b or hashlib.sha256(b).hexdigest()[:12] != sha12: probs.append(f'fine {ref} {t}: missing or sha differs')
            elif len(b) > piece_cap: probs.append(f'fine {ref} {t}: {len(b)} bytes, over the piece cap {piece_cap}')
            elif (json.loads(gzip.decompress(b)).get('kpc') or {}).get('stamp') != idx.get('stamp'): probs.append(f'fine {ref} {t}: preview stamp differs')
    return probs


def main(argv=None):
    ap = argparse.ArgumentParser(description='Make the map display copy from the outline store (drawing only).')
    sub = ap.add_subparsers(dest='cmd')
    b = sub.add_parser('build')
    b.add_argument('--store', required=True); b.add_argument('--area', required=True, action='append')
    b.add_argument('--out', required=True); b.add_argument('--cap', type=int, default=CAP); b.add_argument('--doubtful')
    b.add_argument('--precedence', help='JSON {area: [layer, ..., "*", ...], "default": [...]} (best first)')
    b.add_argument('--key-dir', help="data/us-key: a park that is also in an area not in this run keeps today's outline")
    b.add_argument('--decimals', type=int, default=DECIMALS); b.add_argument('--merge-m', type=float, default=MERGE_M)
    b.add_argument('--private-preview', action='store_true'); b.add_argument('--json')
    c = sub.add_parser('check'); c.add_argument('--out', required=True); c.add_argument('--area', required=True)
    c.add_argument('--public', action='store_true', help='also refuse a PRIVATE PREVIEW and files the INDEX does not list')
    a = ap.parse_args(argv)
    try:
        if a.cmd == 'build':
            pt = json.loads(pathlib.Path(a.precedence).read_text(encoding='utf-8')) if a.precedence else None
            rep = build(a.store, a.area, a.out, cap=a.cap, doubtful=read_doubtful(a.doubtful, a.area), preview=a.private_preview,
                        decimals=a.decimals, merge_m=a.merge_m, precedence_table=pt, park_areas=key_areas(a.key_dir))
            if a.json: pathlib.Path(a.json).write_text(json.dumps(rep, indent=1), encoding='utf-8')
            probs = [f'{ar}: {p}' for ar in rep['areas'] for p in check(a.out, ar)]
            for p in probs: print('PROBLEM', p)
            return 1 if probs else 0
        if a.cmd == 'check':
            probs = check(a.out, a.area, public=a.public)
            for p in probs: print('PROBLEM', p)
            print('check:', 'PASS' if not probs else f'FAIL ({len(probs)})')
            return 1 if probs else 0
        ap.print_help(); return 2
    except DisplayError as e:
        print('STOP:', e); return 1


if __name__ == '__main__':
    sys.exit(main())
