#!/usr/bin/env python3
"""kpc_display_copy.py: make the public map's DISPLAY COPY of park outlines from the accurate OUTLINE STORE (KPC owner, 2026-11-13).

Plain words
-----------
The outline store keeps every tract of every park at full detail (about 2 m). It is never thinned and never published as is.
This tool reads one store area (for example US-NH) and writes a small copy for DRAWING ONLY:
  * one feature per park, with ALL its tracts (records); tracts that are exactly the same land in two layers are drawn once;
  * simplified only as far as needed: a park keeps every point up to CAP points (default 3,000). A bigger park is simplified
    with the smallest tolerance from a fixed ladder (0.5 m, 1 m, 1.5 m, 2 m, 3 m ...) that brings it under the cap, and the
    tolerance used is written on the park ("detail_m");
  * when the cap costs more than FINE_OVER metres (default 5 m) a second, finer copy of that one park is written (FINE level)
    for the map to load when someone zooms in on that park; it is capped at FINE_CAP points (default 40,000) the same way;
  * only records that pass the LICENCE GATE go in. A park with any record that does not pass, or with a doubtful join,
    is left out of the display copy and listed under "fallback" with the reason: the map keeps today's outline for it.
The store file itself is only read, never changed.

Format written (folder OUT/<AREA>/)
  INDEX.json                       {"format": "kpc-display-1", "area", "made", "store": {file, sha256}, "cap", "fine_over_m",
                                    "parts": [[name, sha12, parks, bytes], ...], "fine": {ref: [name, sha12, detail_m]},
                                    "credits": {layer: text}, "fallback": {ref: reason}, "parks": n, "points": n}
  <AREA>.geojson.gz  (+ .p2 ...)   FeatureCollection, the same shape as data/outlines/US-XX.geojson.gz: feature properties
                                    ref, name, g ("official"), detail_m, points, store_points, records [keys], layers, cr [credit layer
                                    keys], fine (bool); geometry MultiPolygon (outer ring + its holes per polygon). Parts are whole
                                    parks, each part under MAX_PART bytes (1,000,000 minus a margin).
  fine/<REF>.geojson.gz            one park at the fine level (same feature shape).
Every file is gzip level 9 with mtime 0, so the same store gives byte-identical files.

Licence gate (owner decisions 2, 3, 4, 11 of 2026-11-13)
  publishable classes: OPEN, PUBLIC DOMAIN, NO TERMS STATED, DISCLAIMER ONLY, NON-COMMERCIAL (with no "no redistribution" /
  "no derivatives" words). Everything else (empty, "not recorded", restricted, held, private, sign-in, WDPA / Protected Planet /
  SPREP) does not pass. The licence text comes from the store index ("licence": {record key: "CLASS; credit: TEXT"}), else
  from the record in the store. --private-preview skips the gate for a person's own local look; its output is stamped
  PRIVATE PREVIEW and must never be published (the tool refuses to write a preview into a folder named like a public one).

Standard library only, Python 3.9+. No network.

  python3 kpc_display_copy.py build --store DIR --area US-NH --out DIR [--cap 3000] [--fine-over 5] [--doubtful CSV]
                                    [--private-preview] [--json report.json]
  python3 kpc_display_copy.py check --out DIR --area US-NH      re-read what was written and check it (sizes, joins, sha)
Exit 0 = done; 1 = a check failed; 2 = usage error.
"""
import argparse, csv, gzip, hashlib, json, math, os, pathlib, re, sys, time, zlib

FORMAT = 'kpc-display-1'
CAP = 3000
FINE_OVER_M = 5.0
FINE_CAP = 40000
MAX_PART = 950_000                      # the repo / site rule is 1 MB per file; keep a margin
DECIMALS = 5                            # 5 decimals = at most 0.6 m of rounding (as today's master files); 6 costs ~20% more bytes
MERGE_M = 3.0                           # draw-once rule: a tract whose whole line lies within 3 m of a drawn line is not drawn again
LADDER = [0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 80, 100, 120, 150, 200, 250, 300, 400, 500,
          750, 1000, 1500, 2000, 3000, 5000]
PUBLISHABLE = ('OPEN', 'PUBLIC DOMAIN', 'NO TERMS STATED', 'DISCLAIMER ONLY', 'NON-COMMERCIAL')
REFUSE_WORDS = re.compile(r'no[ -]?redistribut|do not redistribut|not for redistribution|no[ -]?derivativ|private|held|restricted|'
                          r'sign[ -]?in|login|token|wdpa|protected ?planet|sprep|not recorded', re.I)
WDPA = re.compile(r'wdpa|protectedplanet|protected planet|sprep', re.I)
JOIN_LINK_KM, JOIN_FLAG_KM = 5.0, 10.0  # the store tool's own "check join" rule (tracts in groups 10 km or more apart)
PREVIEW_STAMP = 'PRIVATE PREVIEW - licence gate skipped - never publish'


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
            if idx.get('area') in (None, area) or name != 'index.json':
                return idx, p
            # a combined index.json (full tool): keep only this area's parks
            parks = {k: v for k, v in (idx.get('parks') or {}).items() if str(v.get('file', '')).startswith(area + '.')}
            if parks: return dict(idx, parks=parks, area=area), p
    raise DisplayError(f'no index for {area} in {d}')


def iter_parks(store_dir, idx):
    """(index entry, park) one park at a time, checksums recomputed (a moved coordinate never passes)."""
    d = pathlib.Path(store_dir)
    handles = {}
    try:
        for ref in sorted(idx.get('parks') or {}):
            e = idx['parks'][ref]
            f = handles.get(e['file']) or handles.setdefault(e['file'], open(d / e['file'], 'rb'))
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
            yield e, p
    finally:
        for f in handles.values(): f.close()


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


# ---- licence gate ---------------------------------------------------------------------------------------------------------
def licence_class(text):
    """'OPEN; credit: X' -> ('OPEN', 'X'). Empty -> ('', '')."""
    t = str(text or '').strip()
    if not t: return '', ''
    cls, _, rest = t.partition(';')
    m = re.search(r'credit:\s*(.+)$', rest.strip(), re.I)
    return cls.strip().upper(), (m.group(1).strip() if m else '')


def gate(rec, lic_text):
    """(passes, why, credit). WDPA never passes, whatever its licence says."""
    if WDPA.search(' '.join(str(rec.get(k) or '') for k in ('layer_url', 'agency_label', 'layer', 'licence', 'licence_from'))
                   + ' ' + json.dumps(rec.get('source_detail') or {})[:2000]):
        return False, 'WDPA / Protected Planet / SPREP source', ''
    cls, credit = licence_class(lic_text)
    if not cls or cls == 'NOT RECORDED': return False, 'no licence class recorded', ''
    if cls not in PUBLISHABLE: return False, f'licence class {cls!r} is not publishable', ''
    if REFUSE_WORDS.search(str(lic_text)): return False, 'licence text restricts sharing', ''
    return True, '', credit or str(rec.get('agency_label') or rec.get('layer') or '')


# ---- geometry -------------------------------------------------------------------------------------------------------------
A_WGS, F_WGS = 6378137.0, 1 / 298.257223563
E2 = F_WGS * (2 - F_WGS)


def local_scale(lat0):
    """metres per degree (x = east, y = north) on the WGS84 ellipsoid at latitude lat0 (a local tangent-plane projection)."""
    s = math.sin(math.radians(lat0))
    w = math.sqrt(1 - E2 * s * s)
    n = A_WGS / w                      # prime vertical radius
    m = A_WGS * (1 - E2) / w ** 3      # meridian radius
    return math.radians(1) * n * math.cos(math.radians(lat0)), math.radians(1) * m


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    if L == 0: return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / L
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def dp_keep(xs, ys, tol):
    """Douglas-Peucker on one ring in metres, SEGMENT distance (not the infinite line). Returns sorted kept indices.
    A closed ring keeps its first and last point and at least 4 points in all (a triangle), so no tract ever disappears."""
    n = len(xs)
    if n <= 4 or tol <= 0: return list(range(n))
    keep = bytearray(n); keep[0] = keep[n - 1] = 1
    closed = xs[0] == xs[-1] and ys[0] == ys[-1]
    if closed:   # split a closed ring at its farthest point from the start, so the two halves are open lines
        far = max(range(1, n - 1), key=lambda i: (xs[i] - xs[0]) ** 2 + (ys[i] - ys[0]) ** 2)
        keep[far] = 1; stack = [(0, far), (far, n - 1)]
    else:
        stack = [(0, n - 1)]

    def far_of(a, b):
        ax, ay, bx, by = xs[a], ys[a], xs[b], ys[b]
        best, bi = -1.0, -1
        for i in range(a + 1, b):
            d = seg_dist(xs[i], ys[i], ax, ay, bx, by)
            if d > best: best, bi = d, i
        return best, bi

    def run(stack):
        while stack:
            a, b = stack.pop()
            if b - a < 2: continue
            best, bi = far_of(a, b)
            if best > tol:
                keep[bi] = 1; stack.append((a, bi)); stack.append((bi, b))
    run(stack)
    idx = [i for i in range(n) if keep[i]]
    while closed and len(idx) < 4:   # a sliver: split the chord with the farthest point anyway, then go on as usual
        cand = [(far_of(a, b), a, b) for a, b in zip(idx, idx[1:]) if b - a >= 2]
        if not cand: break
        (best, bi), a, b = max(cand)
        keep[bi] = 1; run([(a, bi), (bi, b)])
        idx = [i for i in range(n) if keep[i]]
    return idx


def ring_error(xs, ys, kept, qx=None, qy=None):
    """Largest distance (m) from any ORIGINAL vertex to the simplified ring (the kept chord that spans it). The largest
    distance of an original segment to a chord is at one of its ends (distance to a segment is convex along a line), so
    testing vertices is exact. qx/qy: the kept points after rounding (if given, the rounded chord is used)."""
    worst = 0.0
    for a, b in zip(kept, kept[1:]):
        ax, ay = (qx[a], qy[a]) if qx else (xs[a], ys[a])
        bx, by = (qx[b], qy[b]) if qx else (xs[b], ys[b])
        for i in range(a, b + 1):
            d = seg_dist(xs[i], ys[i], ax, ay, bx, by)
            if d > worst: worst = d
    return worst


def signed_area(ring):
    s = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        s += x1 * y2 - x2 * y1
    return s / 2


def in_ring(x, y, r):
    ins = False
    j = len(r) - 1
    for i in range(len(r)):
        xi, yi = r[i]; xj, yj = r[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi: ins = not ins
        j = i
    return ins


def polygons(rings):
    """Esri rings of one record -> GeoJSON polygons [[outer, hole, ...], ...]. Esri: outer rings clockwise, holes
    counter-clockwise (in lon/lat with y up, clockwise = negative signed area). A hole goes to the smallest outer ring that
    holds its first point; a hole no outer holds is drawn as a ring of its own (never lost)."""
    outers, holes = [], []
    for r in rings:
        if len(r) < 4: continue
        (outers if signed_area(r) <= 0 else holes).append(r)
    if not outers and holes: outers, holes = holes, []
    polys = [[o] for o in outers]
    area = [abs(signed_area(o)) for o in outers]
    for h in holes:
        x, y = h[0]
        best = None
        for i, o in enumerate(outers):
            if in_ring(x, y, o) and (best is None or area[i] < area[best]): best = i
        if best is None: polys.append([h])
        else: polys[best].append(h)
    return polys


# ---- one park -------------------------------------------------------------------------------------------------------------
def park_rings(p):
    """[(record key, layer, [ring as [(lon, lat)]...])] with records of identical geometry (same sha256) drawn once."""
    seen, out = set(), []
    for r in p.get('records') or []:
        er = enc_rings(r, p)
        if r.get('sha256') in seen: continue
        seen.add(r.get('sha256'))
        out.append((r.get('key'), r.get('layer'), [[(x / SCALE, y / SCALE) for x, y in ring_ints(e)] for e in er]))
    return out


class SegGrid:
    """Segments in metres, bucketed in CELL m squares, for 'how far is the nearest drawn line' questions."""
    CELL = 25.0

    def __init__(self):
        self.g = {}

    def add_ring(self, xs, ys):
        C = self.CELL
        for i in range(len(xs) - 1):
            ax, ay, bx, by = xs[i], ys[i], xs[i + 1], ys[i + 1]
            s = (ax, ay, bx, by)
            n = int(math.hypot(bx - ax, by - ay) / (C / 2)) + 1   # the cells the segment passes through (walked at half a cell)
            cells = {(int(math.floor((ax + (bx - ax) * k / n) / C)), int(math.floor((ay + (by - ay) * k / n) / C))) for k in range(n + 1)}
            for c in cells:
                for dx in (-1, 0, 1):   # and their neighbours, so a corner cut by the walk is never missed
                    for dy in (-1, 0, 1):
                        self.g.setdefault((c[0] + dx, c[1] + dy), set()).add(s)

    def dist(self, x, y, limit):
        """distance to the nearest segment if it is under limit (looks in the cells within limit), else limit."""
        C, best = self.CELL, limit
        R = int(math.ceil(limit / C))
        cx0, cy0 = int(math.floor(x / C)), int(math.floor(y / C))
        for r in range(0, R + 1):   # rings of cells outward; a segment in ring r is at least (r - 1) * C away
            if (r - 1) * C > best: break
            for cx in range(cx0 - r, cx0 + r + 1):
                for cy in ((cy0 - r, cy0 + r) if abs(cx - cx0) != r else range(cy0 - r, cy0 + r + 1)):
                    for s in self.g.get((cx, cy), ()):
                        d = seg_dist(x, y, *s)
                        if d < best: best = d
        return best


def samples(xs, ys, step=5.0):
    """every vertex, plus a point every `step` m along each edge"""
    for i in range(len(xs)):
        yield xs[i], ys[i]
        if i + 1 < len(xs):
            dx, dy = xs[i + 1] - xs[i], ys[i + 1] - ys[i]
            n = int(math.hypot(dx, dy) // step)
            for k in range(1, n + 1):
                t = k / (n + 1)
                yield xs[i] + t * dx, ys[i] + t * dy


def project(recs):
    pts = [(x, y) for _, _, rs in recs for r in rs for x, y in r]
    lat0 = (min(y for _, y in pts) + max(y for _, y in pts)) / 2
    lon0 = (min(x for x, _ in pts) + max(x for x, _ in pts)) / 2
    kx, ky = local_scale(lat0)
    return lon0, lat0, kx, ky


def merge_near(recs, merge_m):
    """Draw-once rule: a record whose every vertex and every 5 m point along its edges lies within merge_m of a line already
    drawn adds nothing visible, so it is not drawn again (it stays listed). Records are taken largest first.
    -> (drawn records, [(key, layer, into)] merged)."""
    if merge_m <= 0 or len(recs) < 2: return list(recs), []
    lon0, lat0, kx, ky = project(recs)
    order = sorted(range(len(recs)), key=lambda i: (-sum(len(r) for r in recs[i][2]), str(recs[i][0])))
    grid, drawn, merged = SegGrid(), [], []
    for i in order:
        key, layer, rs = recs[i]
        pr = [([(x - lon0) * kx for x, _ in r], [(y - lat0) * ky for _, y in r]) for r in rs]
        if drawn and all(grid.dist(x, y, merge_m * 2) <= merge_m for xs, ys in pr for x, y in samples(xs, ys)):
            merged.append((key, layer)); continue
        drawn.append(i)
        for xs, ys in pr: grid.add_ring(xs, ys)
    return [recs[i] for i in sorted(drawn)], merged


def merged_error(merged_recs, simp, merge_m, cap_m):
    """largest distance (m) from any point of a merged (not drawn) record to the nearest DRAWN, simplified line."""
    if not merged_recs: return 0.0
    allr = list(merged_recs) + list(simp)
    lon0, lat0, kx, ky = project(allr)
    g = SegGrid()
    for _, _, rs in simp:
        for r in rs: g.add_ring([(x - lon0) * kx for x, _ in r], [(y - lat0) * ky for _, y in r])
    worst = 0.0
    for _, _, rs in merged_recs:
        for r in rs:
            for x, y in samples([(x - lon0) * kx for x, _ in r], [(y - lat0) * ky for _, y in r]):
                d = g.dist(x, y, cap_m)
                if d > worst: worst = d
    return worst


def simplify_park(recs, cap, ladder=LADDER, decimals=DECIMALS, min_tol=0.0):
    """-> (tolerance used (m), [(key, layer, [simplified ring lon/lat...])], points, worst error m, median ring error m).
    tolerance 0 = every point kept. The smallest ladder step that brings the park to cap points or fewer is used; if even
    the largest step does not, the largest is used and the park is over the cap (reported)."""
    pts = [(x, y) for _, _, rs in recs for r in rs for x, y in r]
    if not pts: return 0.0, [], 0, 0.0, 0.0
    lat0 = (min(y for _, y in pts) + max(y for _, y in pts)) / 2
    lon0 = (min(x for x, _ in pts) + max(x for x, _ in pts)) / 2
    kx, ky = local_scale(lat0)
    proj = [[([(x - lon0) * kx for x, _ in r], [(y - lat0) * ky for _, y in r]) for r in rs] for _, _, rs in recs]
    total = len(pts)
    steps = ([min_tol] if min_tol > 0 else [0.0]) + [t for t in ladder if t > min_tol]
    chosen, kept_all = None, None
    for t in steps:
        kept_all = [[dp_keep(xs, ys, t) for xs, ys in pr] for pr in proj]
        n = sum(len(k) for kr in kept_all for k in kr)
        chosen = t
        if n <= cap: break
    q = 10 ** decimals
    out, errs, npts = [], [], 0
    for (key, layer, rs), pr, kr in zip(recs, proj, kept_all):
        srs = []
        for r, (xs, ys), k in zip(rs, pr, kr):
            ring = [(round(r[i][0] * q) / q, round(r[i][1] * q) / q) for i in k]
            qx = [(lon - lon0) * kx for lon, _ in ring]; qy = [(lat - lat0) * ky for _, lat in ring]
            qxf, qyf = [0.0] * len(xs), [0.0] * len(xs)
            for j, i in enumerate(k): qxf[i], qyf[i] = qx[j], qy[j]
            errs.append(ring_error(xs, ys, k, qxf, qyf))
            srs.append(ring); npts += len(ring)
        out.append((key, layer, srs))
    errs.sort()
    return chosen, out, npts, (errs[-1] if errs else 0.0), (errs[len(errs) // 2] if errs else 0.0)


def feature(p, simp, tol, npts, store_pts, credits_of, fine=False, merged=()):
    polys = []
    for _, _, rs in simp:
        for poly in polygons(rs):
            polys.append([[[x, y] for x, y in ring] for ring in poly])
    return {'type': 'Feature',
            'properties': {'ref': p['ref'], 'name': p.get('name') or p['ref'], 'g': 'official', 'detail_m': tol, 'points': npts,
                           'store_points': store_pts, 'records': [k for k, _, _ in simp] + [k for k, _ in merged],
                           'drawn_once': len(merged),
                           'layers': sorted({l for _, l, _ in simp if l} | {l for _, l in merged if l}),
                           'cr': sorted({credits_of[k] for k, _, _ in simp if k in credits_of} | {credits_of[k] for k, _ in merged if k in credits_of}),
                           'fine': bool(fine)},
            'geometry': {'type': 'MultiPolygon', 'coordinates': polys}}


def gz(obj):
    return gzip.compress(json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8'), 9, mtime=0)


def tract_spread(recs):
    boxes = []
    for _, _, rs in recs:
        xs = [q[0] for r in rs for q in r]; ys = [q[1] for r in rs for q in r]
        if xs: boxes.append((min(xs), min(ys), max(xs), max(ys)))
    if len(boxes) < 2: return 1, 0.0
    lat0 = sum((b[1] + b[3]) / 2 for b in boxes) / len(boxes)
    kx, ky = 111.32 * math.cos(math.radians(lat0)), 110.574

    def gap(a, b):
        return math.hypot(max(0.0, max(a[0], b[0]) - min(a[2], b[2])) * kx, max(0.0, max(a[1], b[1]) - min(a[3], b[3])) * ky)
    n = len(boxes); parent = list(range(n))

    def find(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if find(i) != find(j) and gap(boxes[i], boxes[j]) < JOIN_LINK_KM: parent[find(i)] = find(j)
    groups = {}
    for i in range(n): groups.setdefault(find(i), []).append(i)
    g = list(groups.values())
    sep = min((gap(boxes[i], boxes[j]) for a in range(len(g)) for b in range(a + 1, len(g)) for i in g[a] for j in g[b]), default=0.0)
    return len(g), sep


def read_doubtful(path, area):
    """A CSV with a 'park' (or 'ref') column, optional 'state' column (KEEP-FLAGGED joins, doubtful joins): ref -> reason."""
    out = {}
    if not path: return out
    st = area.split('-', 1)[1] if area.startswith('US-') else ''
    with open(path, encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            ref = (row.get('park') or row.get('ref') or '').strip()
            if not ref: continue
            if st and row.get('state') and row['state'].strip() != st: continue
            why = ' '.join(x for x in (row.get('matcher_review_state'), row.get('matcher_doubt_code')) if x)
            out[ref] = 'doubtful join' + (f' ({why})' if why else '')
    return out


# ---- build ----------------------------------------------------------------------------------------------------------------
def build(store_dir, area, out_dir, cap=CAP, fine_over=FINE_OVER_M, fine_cap=FINE_CAP, doubtful=None, preview=False,
          decimals=DECIMALS, min_tol=0.0, merge_m=MERGE_M, max_part=MAX_PART, log=print):
    t0 = time.time()
    if not re.fullmatch(r'(US|CA)-[A-Z]{2,3}|W-[A-Z]{2}', area): raise DisplayError(f'bad area {area!r}')
    out = pathlib.Path(out_dir) / area
    if preview and re.search(r'(^|/)(data/display|data/released|_site)(/|$)', str(pathlib.Path(out_dir).resolve()).replace('\\', '/')):
        raise DisplayError('a PRIVATE PREVIEW is never written into a public folder')
    idx, idx_path = read_index(store_dir, area)
    files = sorted({e['file'] for e in idx['parks'].values()})
    store_sha = {f: file_sha256(pathlib.Path(store_dir) / f) for f in files}
    for f, meta in (idx.get('files') or {}).items():
        if f in store_sha and meta.get('sha256') and meta['sha256'] != store_sha[f]:
            raise DisplayError(f'{f}: sha256 differs from the index (store and index are not from the same build)')
    doubt = dict(doubtful or {})
    feats, fines, fallback, credits, rows = [], {}, {}, {}, []
    for e, p in iter_parks(store_dir, idx):
        ref = p['ref']
        lic_map = e.get('licence') or {}
        recs_all = p.get('records') or []
        if p.get('circle') or p.get('grade') != 'official':
            fallback[ref] = 'not an official outline in the store (circle / approximate)'; continue
        why_not, cred = [], {}
        for r in recs_all:
            ok, why, credit = (True, '', str(r.get('agency_label') or r.get('layer') or '')) if preview else gate(r, lic_map.get(r.get('key')) or r.get('licence'))
            if WDPA.search(json.dumps({k: r.get(k) for k in ('layer_url', 'agency_label', 'licence')})):
                ok, why = False, 'WDPA / Protected Planet / SPREP source'   # never, not even in a preview
            if not ok: why_not.append(f"{r.get('key')}: {why}")
            else: cred[r.get('key')] = r.get('layer') or ''; credits.setdefault(r.get('layer') or '', credit)
        if why_not:
            fallback[ref] = 'licence gate: ' + '; '.join(why_not[:3]) + (f' (+{len(why_not) - 3} more)' if len(why_not) > 3 else ''); continue
        recs = park_rings(p)
        ng, sep = tract_spread(recs)
        if e.get('check_join') or (ng > 1 and sep >= JOIN_FLAG_KM):
            cj = e.get('check_join') or {'groups': ng, 'gap_km': round(sep, 1)}
            doubt.setdefault(ref, f"check join (tracts in {cj.get('groups')} groups {cj.get('gap_km')} km apart)")
        if ref in doubt:
            fallback[ref] = doubt[ref]; continue
        store_pts = sum(len(r) for _, _, rs in recs for r in rs)
        drawn, merged = merge_near(recs, merge_m)
        mrecs = [r for r in recs if (r[0], r[1]) in set(merged)]
        tol, simp, npts, worst, med = simplify_park(drawn, cap, decimals=decimals, min_tol=min_tol)
        # a merged tract lies within merge_m of a drawn tract's true line, and that line moved at most `worst`: measured
        # when the drawn line is fine (worst <= 20 m), else the bound merge_m + worst is reported (measuring km-wide gaps is slow)
        mworst = merged_error(mrecs, simp, merge_m, merge_m + worst + 1) if worst <= 20 else merge_m + worst
        fine = None
        if max(worst, mworst) > fine_over:
            ftol, fsimp, fpts, fworst, fmed = simplify_park(drawn, fine_cap, decimals=decimals, min_tol=min_tol)
            fine = (ftol, fsimp, fpts, max(fworst, merged_error(mrecs, fsimp, merge_m, merge_m + fworst + 1) if fworst <= 20 else merge_m + fworst))
        feats.append(feature(p, simp, tol, npts, store_pts, cred, fine=bool(fine), merged=merged))
        if fine:
            fines[ref] = feature(p, fine[1], fine[0], fine[2], store_pts, cred, fine=True, merged=merged)
        rows.append({'ref': ref, 'name': p.get('name'), 'records': len(recs_all), 'distinct_records': len(recs), 'drawn_records': len(drawn),
                     'store_points': store_pts, 'drawn_store_points': sum(len(r) for _, _, rs in drawn for r in rs),
                     'points': npts, 'detail_m': tol, 'worst_m': round(max(worst, mworst), 2), 'worst_drawn_m': round(worst, 2),
                     'worst_merged_m': round(mworst, 2), 'median_ring_m': round(med, 2),
                     'fine_points': fine[2] if fine else None, 'fine_detail_m': fine[0] if fine else None,
                     'fine_worst_m': round(fine[3], 2) if fine else None})
    # parts: whole parks, each part under max_part bytes (gzip), in ref order
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob('*.geojson.gz')) + list((out / 'fine').glob('*.geojson.gz')): old.unlink()
    head = {'area': area, 'format': FORMAT, 'made_from': {f: store_sha[f] for f in files}}
    if preview: head['stamp'] = PREVIEW_STAMP
    parts, cur = [], []

    def flush():
        if cur: parts.append(list(cur)); cur.clear()
    for f in feats:
        cur.append(f)
        if len(gz({'type': 'FeatureCollection', 'kpc': head, 'features': cur})) > max_part:
            last = cur.pop(); flush(); cur.append(last)
            if len(gz({'type': 'FeatureCollection', 'kpc': head, 'features': cur})) > max_part:
                raise DisplayError(f"{last['properties']['ref']}: one park is over {max_part} bytes even alone (lower --cap)")
    flush()
    plist = []
    for i, ps in enumerate(parts, 1):
        name = f'{area}.geojson.gz' if i == 1 else f'{area}.p{i}.geojson.gz'
        b = gz({'type': 'FeatureCollection', 'kpc': dict(head, part=[i, len(parts)]), 'features': ps})
        (out / name).write_bytes(b)
        plist.append([name, hashlib.sha256(b).hexdigest()[:12], len(ps), len(b)])
    flist = {}
    if fines:
        (out / 'fine').mkdir(exist_ok=True)
        for ref, f in sorted(fines.items()):
            b = gz({'type': 'FeatureCollection', 'kpc': dict(head, fine=ref), 'features': [f]})
            if len(b) > max_part: raise DisplayError(f'{ref}: the fine copy is over {max_part} bytes (lower --fine-cap)')
            name = f'fine/{ref}.geojson.gz'
            (out / name).write_bytes(b)
            flist[ref] = [name, hashlib.sha256(b).hexdigest()[:12], f['properties']['detail_m'], len(b)]
    index = {'format': FORMAT, 'area': area, 'made': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
             'store': {f: store_sha[f] for f in files}, 'store_index': idx_path.name, 'cap': cap, 'fine_over_m': fine_over,
             'fine_cap': fine_cap, 'decimals': decimals, 'merge_m': merge_m, 'parks': len(feats), 'points': sum(r['points'] for r in rows),
             'parts': plist, 'fine': flist, 'credits': dict(sorted(credits.items())), 'fallback': dict(sorted(fallback.items())),
             'about': 'Display copy for drawing only. A park not listed here keeps its old outline on the map. Never used for "am I in the park".'}
    if preview: index['stamp'] = PREVIEW_STAMP
    (out / 'INDEX.json').write_text(json.dumps(index, ensure_ascii=False, indent=1, sort_keys=False) + '\n', encoding='utf-8')
    rep = {'area': area, 'seconds': round(time.time() - t0, 2), 'parks_in_store': len(idx['parks']), 'parks_drawn': len(feats),
           'fallback': len(fallback), 'fine_parks': len(fines), 'bytes_parts': sum(x[3] for x in plist),
           'bytes_fine': sum(v[3] for v in flist.values()), 'parts': len(plist), 'rows': rows, 'fallback_reasons': fallback}
    log(f"{area}: {len(feats)} parks drawn, {len(fallback)} kept on today's outline, {len(fines)} with a fine level; "
        f"{rep['bytes_parts']:,} bytes in {len(plist)} part(s) + {rep['bytes_fine']:,} bytes fine; {rep['seconds']} s")
    return rep


def check(out_dir, area, max_part=1_000_000, public=False):
    """Re-read a written display copy: every file under 1 MB, sha12 as listed, parts join, every park once, no preview stamp
    unless the index has one, every credit layer named. -> list of problems (empty = good)."""
    out = pathlib.Path(out_dir) / area
    probs = []
    try: idx = json.loads((out / 'INDEX.json').read_text(encoding='utf-8'))
    except Exception as e: return [f'INDEX.json unreadable: {e}']
    if idx.get('format') != FORMAT: probs.append('wrong format')
    if public and idx.get('stamp'): probs.append('a PRIVATE PREVIEW: never published')
    if idx.get('area') != area: probs.append(f"INDEX is for {idx.get('area')!r}, not {area}")
    names = [x[0] for x in idx.get('parts') or []] + [v[0] for v in (idx.get('fine') or {}).values()]
    if any('..' in n or n.startswith('/') or not re.fullmatch(r'(fine/)?[A-Z0-9-]+(\.p\d+)?\.geojson\.gz', n) for n in names):
        probs.append('a file name in INDEX is not a display file name')
        return probs
    if public:
        listed = {'INDEX.json'} | set(names)
        extra = [str(q.relative_to(out)) for q in out.rglob('*') if q.is_file() and str(q.relative_to(out)).replace('\\', '/') not in listed]
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
        if len(d.get('features') or []) != n: probs.append(f'{name}: {len(d.get("features") or [])} parks, INDEX says {n}')
        for f in d.get('features') or []:
            r = f['properties']['ref']
            if r in seen: probs.append(f'{r} twice')
            seen.add(r)
            if r in (idx.get('fallback') or {}): probs.append(f'{r} both drawn and fallback')
            for c in f['properties'].get('cr') or []:
                if c not in (idx.get('credits') or {}): probs.append(f'{r}: credit {c} not in INDEX credits')
            if f['properties'].get('fine') and r not in (idx.get('fine') or {}): probs.append(f'{r}: fine level missing')
    if len(seen) != idx.get('parks'): probs.append(f"{len(seen)} parks in parts, INDEX says {idx.get('parks')}")
    for ref, (name, sha12, _t, size) in (idx.get('fine') or {}).items():
        b = (out / name).read_bytes() if (out / name).is_file() else b''
        if not b or hashlib.sha256(b).hexdigest()[:12] != sha12: probs.append(f'fine {ref}: missing or sha differs')
        elif len(b) > max_part: probs.append(f'fine {ref}: over {max_part} bytes')
    return probs


def main(argv=None):
    ap = argparse.ArgumentParser(description='Make the map display copy from the outline store (drawing only).')
    sub = ap.add_subparsers(dest='cmd')
    b = sub.add_parser('build')
    b.add_argument('--store', required=True); b.add_argument('--area', required=True); b.add_argument('--out', required=True)
    b.add_argument('--cap', type=int, default=CAP); b.add_argument('--fine-over', type=float, default=FINE_OVER_M)
    b.add_argument('--fine-cap', type=int, default=FINE_CAP); b.add_argument('--doubtful')
    b.add_argument('--decimals', type=int, default=DECIMALS); b.add_argument('--min-tol', type=float, default=0.0)
    b.add_argument('--merge-m', type=float, default=MERGE_M)
    b.add_argument('--private-preview', action='store_true'); b.add_argument('--json')
    c = sub.add_parser('check'); c.add_argument('--out', required=True); c.add_argument('--area', required=True)
    c.add_argument('--public', action='store_true', help='also refuse a PRIVATE PREVIEW and files the INDEX does not list')
    a = ap.parse_args(argv)
    try:
        if a.cmd == 'build':
            rep = build(a.store, a.area, a.out, cap=a.cap, fine_over=a.fine_over, fine_cap=a.fine_cap,
                        doubtful=read_doubtful(a.doubtful, a.area), preview=a.private_preview, decimals=a.decimals, min_tol=a.min_tol, merge_m=a.merge_m)
            if a.json: pathlib.Path(a.json).write_text(json.dumps(rep, indent=1), encoding='utf-8')
            probs = check(a.out, a.area)
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
