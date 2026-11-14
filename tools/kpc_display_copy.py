#!/usr/bin/env python3
"""kpc_display_copy.py: make the public map's DISPLAY COPY of park outlines from the accurate OUTLINE STORE (KPC owner, 2026-11-13;
huge parks, one layer per park and parks across state lines 2026-11-14; grade fixes 2026-11-14).

Plain words
-----------
The outline store keeps every tract of every park at full detail (about 2 m). It is never thinned and never published as is.
This tool reads store areas (US-NH, US-ME ...) and writes a copy for DRAWING ONLY, in three levels:
  OVERVIEW  one file set per area, every park at most CAP points (3,000);
  MIDDLE    for a park whose overview is more than 25 m off: one file per park and area, at most 30,000 points;
  FINE      for a park whose coarser levels are more than 5 m off: lines at 1 m, cut into square PIECES (tiles), each under a
            hard byte cap, so the map loads only the pieces on screen.
A level drops rings smaller than its tolerance only when that tolerance is over 5 m (so the finest level of every park is
complete). The store files are only read, never changed.

What is drawn (in this order, per park; all of a park's areas together):
  1. LICENCE GATE (strict; see gate()): a store in index format kpc-outline-store-index/3 or later, read from its PER-AREA
     index, every file's sha256 checked. A record is drawn only if the index's record_meta AND the record itself say publishable,
     with the same licence class (one the store's licence-classes.json allows; SHARE-ALIKE stays off; an unknown class stops
     the build), a basis of a verified row or the owner's confirmation, and the same plain credit line. wdpa_derived true, or
     WDPA / Protected Planet / SPREP / UNEP-WCMC in any value = never. One record that fails keeps the WHOLE park on today's
     outline.
  2. Doubtful joins (lists, the store's check-join flag, or tracts 10 km apart): today's outline.
  3. Records with the same geometry are drawn once: the copy from the highest-ranked layer.
  4. ONE LAYER PER PARK. tools/kpc_display_precedence.json ranks the layers per area. The WINNING layer (the best present) is
     always drawn in full. A lower layer is judged per SEGMENT, by points every 5 m: a segment whose points all lie inside land a
     higher layer draws, or within 30 m of its line, is covered and not drawn (holes are not land). Every uncovered stretch is
     drawn (stretches under 10 m between covered ones are noise). A ring that is covered all round is still drawn in full if
     hiding it would lose land (its inside reaches more than 30 m beyond the higher layers' land).
  5. DRAW ONCE: a segment whose points all lie within 3 m of a segment ALREADY DRAWN is not drawn again.
  6. A PARK ACROSS AREAS: a segment where the park's own tracts from two areas meet, on opposite sides, is not drawn (no seam).
  7. INVARIANTS, checked for every park on its finest level; a park that fails keeps today's outline (and is listed privately):
       I1 every metre of boundary that must be drawn (the winning layer's, and the uncovered stretches of lower layers; not the
          seam) lies within 5 m of a drawn line;
       I2 no land is lost: every point of the park's publishable land in the store is inside a tract that is shown (not covered
          all round by a higher layer), or within 30 m of a drawn line (the 30 m strip is the "layers disagree" allowance; its area
          is reported).
What is written is public: no record keys, licence words, reasons or store names go into it. The detailed reasons, per park,
go only into the private report (--report FILE, which must be outside the output folder).

Files (folder OUT/<AREA>/), every file gzip level 9 with mtime 0 (same store = byte-identical files):
  INDEX.json                      format, area, gen, built_with, caps, parts, mid, fine, fallback {ref: "kept today's outline"}
  <AREA>.geojson.gz (+ .pN)       OVERVIEW: one feature per park (MultiPolygon). A park with stretches not drawn has two
                                  features: role 'line' (MultiLineString, drawn) and role 'hit' (its drawn tracts, clicks only).
                                  Properties: ref, name, g, detail_m, worst_m, points, layers, won, cr (credit lines), mid,
                                  fine, and for a park across areas 'areas' and 'gen'.
  mid/<REF>.geojson.gz            MIDDLE: one MultiLineString feature (this area's part of the park).
  fine/<REF>/<ix>_<iy>.geojson.gz FINE pieces: MultiLineString inside tile ix,iy (T x T degrees, T in INDEX fine[ref].t).
Standard library only, Python 3.9+. No network.

  python3 kpc_display_copy.py build --store DIR --area US-NH [--area US-ME ...] --out DIR [--doubtful CSV ...]
                                    [--precedence JSON] [--key-dir data/us-key] [--report private.json] [--private-preview]
  python3 kpc_display_copy.py check --out DIR --area US-NH [--public]
Exit 0 = done; 1 = stopped or a check failed; 2 = usage error.
"""
import argparse, csv, gzip, hashlib, json, math, pathlib, re, sys, time, urllib.parse

FORMAT = 'kpc-display-3'
CAP = 3000                      # OVERVIEW points per park (owner decision 2)
MID_CAP = 30000                 # MIDDLE points per park
MID_OVER_M = 25.0               # a MIDDLE level when the overview is more than this off
FINE_OVER_M = 5.0               # a FINE level when the coarser levels are more than this off; also the street-level promise
FINE_TOL_M = 1.0                # FINE simplification (the store is ~2 m already)
MAX_PART = 950_000              # overview parts and middle files: under the 1 MB rule with a margin
PIECE_CAP = 128_000             # hard cap per FINE piece (bytes, gzip)
TILE_START = 0.05               # FINE piece size to start with (degrees); halved until every piece is under PIECE_CAP
TILE_MIN = 0.05 / 64
DECIMALS = 5                    # at most 0.6 m of rounding (as today's master files)
MERGE_M = 3.0                   # draw-once distance
SEAM_M = 3.0                    # tracts of one park in two areas closer than this at the border, on opposite sides: no line
COVER_M = 30.0                  # a lower layer's point within this of a higher layer's line (or inside its land) is covered
STEP_M = 5.0                    # boundary sample spacing for the judgements and the invariants
MIN_STRETCH_M = 10.0            # an uncovered lower-layer stretch shorter than this between covered ones is noise
LOST_TOL_CELLS = 4              # invariant I2: more than this many lost cells (each at most 50 x 50 m) in one ring = land lost (fail)
I2_CELLS = 250_000              # the park's store land (reported): about this many cells per cluster
LADDER = [0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 80, 100, 120, 150, 200, 250, 300, 400, 500,
          750, 1000, 1500, 2000, 3000, 5000, 7500, 10000, 20000]
# Licence classes: the store tool's own list (licence-classes.json of store tool full 3, copied word for word to
# tools/kpc_display_licence_classes.json). A class may be drawn only if that list says can_be_publishable: true AND it is not
# held back here (SHARE-ALIKE stays off until the owner decides; it is can_be_publishable false in full 3 anyway). A store that
# names a class this list does not know stops the build (the list must be updated first, by a person).
HELD_CLASSES = {'SHARE-ALIKE'}
BASIS_OK = {'verified-row', 'owner-confirmed'}
STORE_FORMAT_MIN = 3            # store index 'kpc-outline-store-index/3' or later
STORE_FORMAT_RX = re.compile(r'kpc-outline-store-index/(\d+)')
META_KEYS = ('publishable', 'licence_class', 'publish_basis', 'publish_basis_detail', 'credit_line', 'source_layer', 'source_url',
             'terms_text_sha256', 'terms_text_file', 'wdpa_derived', 'private_reason')
# WDPA words, searched in VALUES only (never in field names: every v3 record has a field NAMED wdpa_derived)
WDPA = re.compile(r'wdpa|protected ?planet|\bsprep\b|unep[- ]?wcmc|world database on protected areas', re.I)
WDPA_SKIP_ATTRS = {'wdpa_cd'}   # PAD-US's own code field (a number or a code, never a WDPA source)
LICENCE_CLASSES_FILE = pathlib.Path(__file__).resolve().parent / 'kpc_display_licence_classes.json'


def load_licence_classes(path=None):
    """{class name: can be drawn (bool)} from the store tool's licence-classes.json semantics."""
    d = json.loads(pathlib.Path(path or LICENCE_CLASSES_FILE).read_text(encoding='utf-8'))
    cl = d.get('classes')
    if not isinstance(cl, dict) or not cl: raise DisplayError('licence class list has no classes')
    out = {}
    for name, v in cl.items():
        if not isinstance(v, dict) or not isinstance(v.get('can_be_publishable'), bool):
            raise DisplayError(f'licence class {name!r}: can_be_publishable must be true or false')
        out[str(name).strip().upper()] = v['can_be_publishable'] and str(name).strip().upper() not in HELD_CLASSES
    return out


LICENCE_CLASSES = load_licence_classes()
ALLOW_CLASSES = frozenset(k for k, v in LICENCE_CLASSES.items() if v)
PREVIEW_STAMP = 'PRIVATE PREVIEW - licence gate skipped - never publish'
FALLBACK_CODE = "kept today's outline"
JOIN_LINK_KM, JOIN_FLAG_KM = 5.0, 10.0
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


def read_index(store_dir, area, preview=False):
    """The PER-AREA index index-<AREA>.json. The combined index.json (store tool full 3) merges the entries of parks that span
    areas into one, so it is read only for a private preview of an older store that has no per-area index."""
    d = pathlib.Path(store_dir)
    p = d / f'index-{area}.json'
    if p.is_file(): return json.loads(p.read_text(encoding='utf-8')), p
    p = d / 'index.json'
    if preview and p.is_file():
        idx = json.loads(p.read_text(encoding='utf-8'))
        if idx.get('area') == area: return idx, p
        parks = {k: v for k, v in (idx.get('parks') or {}).items() if str(v.get('file', '')).startswith(area + '.')}
        if parks: return dict(idx, parks=parks, area=area), p
    raise DisplayError(f'no per-area index index-{area}.json in {d}' + ('' if preview else ' (a public build never reads the combined index.json)'))


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


# ---- licence gate ---------------------------------------------------------------------------------------------------------
def store_format(idx):
    """'kpc-outline-store-index/3' -> 3; anything else -> 0."""
    m = STORE_FORMAT_RX.fullmatch(str(idx.get('store_format_version') or '').strip())
    return int(m.group(1)) if m else 0


def check_classes(names, where, known=None):
    known = LICENCE_CLASSES if known is None else known
    bad = sorted({str(n) for n in names if str(n or '').strip().upper() not in known})
    if bad: raise DisplayError(f'{where}: the store names licence class(es) this builder does not know: {bad} '
                               f'(update tools/kpc_display_licence_classes.json from the store tool first)')


def require_public_index(idx, area, known=None):
    """A public build needs a PER-AREA index in store format 3 or later, with file checksums and, per record, the record_meta block."""
    v = store_format(idx)
    if v < STORE_FORMAT_MIN:
        raise DisplayError(f'{area}: store_format_version is {idx.get("store_format_version")!r}; a public build needs '
                           f'kpc-outline-store-index/{STORE_FORMAT_MIN} or later')
    if idx.get('area') != area:
        raise DisplayError(f'{area}: a public build reads the per-area index index-{area}.json (the combined index.json merges parks '
                           f'that span areas)')
    files = idx.get('files') or {}
    if not files or not all(re.fullmatch(r'[0-9a-f]{64}', str((m or {}).get('sha256') or '')) for m in files.values()):
        raise DisplayError(f'{area}: the store index has no file checksums')
    check_classes(idx.get('licence_classes') or [], f'{area} index', known)
    for ref, e in (idx.get('parks') or {}).items():
        if e.get('file') not in files: raise DisplayError(f'{area}: park {ref} is in {e.get("file")!r}, which the index does not list')
        rm = e.get('record_meta')
        if not isinstance(rm, dict) or not rm: raise DisplayError(f'{area}: park {ref} has no record_meta in the store index')
        check_classes([m.get('licence_class') for m in rm.values() if isinstance(m, dict)], f'{area} park {ref}', known)


def clean_credit(t):
    """The credit line as the map prints it: e-mail addresses, web addresses and account notes ('owner ...', parentheses holding
    one of those) are removed; '' when nothing plain is left (then the record does not pass)."""
    t = str(t or '')
    t = re.sub(r'\([^()]*(?:@|https?:|www\.|\bowner\b)[^()]*\)', ' ', t, flags=re.I)
    t = re.sub(r'[\w.+-]+@[\w-]+(\.[\w-]+)+', ' ', t)
    t = re.sub(r'(https?://|www\.)\S+', ' ', t, flags=re.I)
    t = re.sub(r'\bowner\b[^,;]*', ' ', t, flags=re.I)
    t = re.sub(r'\s+', ' ', t).strip(' ,;:-')
    if len(t) > 160 or re.search(r'password|token|private|internal|@', t, re.I): return ''
    return t


def norm_layer_url(u):
    """The store tool's layer-table key (its norm_layer): host lower case (with a port other than 443), path unquoted and lower
    case, no /query, no trailing slash, no scheme, no query string. A key already in that form maps to itself."""
    u = str(u or '').strip()
    if not re.match(r'[a-z][a-z0-9+.-]*://', u, re.I): u = 'https://' + u
    sp = urllib.parse.urlsplit(u)
    path = re.sub(r'/query/?$', '', urllib.parse.unquote(sp.path or ''), flags=re.I).rstrip('/')
    host = (sp.hostname or '').lower().rstrip('.')
    try: port = sp.port
    except ValueError: port = -1
    if port not in (None, 443): host = f'{host}:{port}'
    return f'{host}{path.lower()}'


def _values(x, skip_keys=()):
    """Every string / number VALUE inside x (dicts and lists walked); keys are never returned; skip_keys (lower case) are skipped."""
    if isinstance(x, dict):
        for k, v in x.items():
            if str(k).lower() in skip_keys: continue
            yield from _values(v, skip_keys)
    elif isinstance(x, (list, tuple)):
        for v in x: yield from _values(v, skip_keys)
    elif isinstance(x, str): yield x


def wdpa_hit(rec, meta, layer_row):
    """True = a WDPA / Protected Planet / SPREP / UNEP-WCMC record. First the store's own boolean wdpa_derived (index record_meta
    and record: anything but False on either is a hit), then the words, in VALUES only (record without rings, its record_meta,
    its layer row), skipping PAD-US's WDPA_Cd field. An attribute named WDPAID / WDPA_PID is a WDPA feature id."""
    for d in (rec, meta):
        if d is not None and 'wdpa_derived' in d and d['wdpa_derived'] is not False: return True
    for k in (rec.get('attributes') or {}):
        if re.fullmatch(r'wdpa_?(pid|id)|wdpaid', str(k), re.I): return True
    body = {k: v for k, v in rec.items() if k not in ('rings', 'sha256')}
    for part in (body, meta or {}, layer_row or {}):
        for v in _values(part, WDPA_SKIP_ATTRS):
            if WDPA.search(v): return True
    return False


def gate(rec, e, layers_tbl):
    """(passes, private reason, credit) for one record. The stricter answer wins: the index's record_meta AND the record itself
    must say publishable (boolean true) with the same allowed class, the same verified-row / owner-confirmed basis and the same
    plain credit line; the layer row (if the index has one) must agree; the park must be publishable as a whole. WDPA never."""
    key = rec.get('key')
    meta = ((e.get('record_meta') or {}).get(key)) if isinstance(e.get('record_meta'), dict) else None
    if not isinstance(meta, dict): return False, 'no record_meta for it in the index', ''
    tbl = {norm_layer_url(k): v for k, v in layers_tbl.items()} if isinstance(layers_tbl, dict) else {}
    row = tbl.get(norm_layer_url(rec.get('source_url') or rec.get('layer_url'))) if tbl else None
    if wdpa_hit(rec, meta, row) or meta.get('wdpa_derived') is not False or rec.get('wdpa_derived') is not False:
        return False, 'WDPA / Protected Planet / SPREP / UNEP-WCMC source (or wdpa_derived is not false)', ''
    for k in META_KEYS:
        if k in rec and rec.get(k) != meta.get(k): return False, f'index and record differ on {k}', ''
    if meta.get('publishable') is not True: return False, f"index publishable is {meta.get('publishable')!r}", ''
    if rec.get('publishable') is not True: return False, f"record publishable is {rec.get('publishable')!r}", ''
    if e.get('park_publishable') is not True: return False, 'park_publishable is not true', ''
    if meta.get('private_reason'): return False, 'the store gives a private reason', ''
    cls_i = str(meta.get('licence_class') or '').strip().upper()
    cls_r = str(rec.get('licence_class') or '').strip().upper()
    if cls_i != cls_r: return False, f'licence class differs: index {cls_i!r}, record {cls_r!r}', ''
    if cls_i not in LICENCE_CLASSES: raise DisplayError(f'{key}: licence class {cls_i!r} is not one this builder knows')
    if cls_i not in ALLOW_CLASSES: return False, f'licence class {cls_i!r} may not be drawn', ''
    basis = str(meta.get('publish_basis') or '')
    if basis not in BASIS_OK or str(rec.get('publish_basis') or '') != basis:
        return False, f'publish basis {basis!r} is not a verified row or the owner\'s confirmation (in both)', ''
    if row is not None and (row.get('publishable') is not True or str(row.get('class') or '').strip().upper() != cls_i):
        return False, 'the index layer table disagrees', ''
    credit = clean_credit(meta.get('credit_line'))
    if not credit or credit != clean_credit(rec.get('credit_line')): return False, 'no plain credit line (or index and record differ)', ''
    return True, '', credit


# ---- land and rasters -----------------------------------------------------------------------------------------------------
class Land:
    """Polygons of several records (each record even-odd over its own rings, so holes are not land), for point-in-land tests.
    Each ring's edges are bucketed by y (BUCKET m) so a test looks only at the edges at the point's height."""
    BUCKET = 100.0

    def __init__(self):
        self.recs = []    # [(bbox, [(ring bbox, {bucket: [edges]})])]

    def add(self, xy):
        rings, rb = [], [math.inf, math.inf, -math.inf, -math.inf]
        for xs, ys in xy:
            if len(xs) < 4: continue
            bb = (min(xs), min(ys), max(xs), max(ys))
            rb = [min(rb[0], bb[0]), min(rb[1], bb[1]), max(rb[2], bb[2]), max(rb[3], bb[3])]
            buckets = {}
            for i in range(len(xs) - 1):
                x1, y1, x2, y2 = xs[i], ys[i], xs[i + 1], ys[i + 1]
                if y1 == y2: continue
                for b in range(int(math.floor(min(y1, y2) / self.BUCKET)), int(math.floor(max(y1, y2) / self.BUCKET)) + 1):
                    buckets.setdefault(b, []).append((x1, y1, x2, y2))
            rings.append((bb, buckets))
        if rings: self.recs.append((tuple(rb), rings))

    def inside(self, x, y):
        b = int(math.floor(y / self.BUCKET))
        for rb, rings in self.recs:
            if not (rb[0] <= x <= rb[2] and rb[1] <= y <= rb[3]): continue
            odd = False
            for bb, buckets in rings:
                if not (bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3]): continue
                for x1, y1, x2, y2 in buckets.get(b, ()):
                    if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): odd = not odd
            if odd: return True
        return False


def raster(xys, x0, y0, cell, nx, ny):
    """Cells (nx x ny, centres x0 + (i + 0.5) * cell ...) inside any of the given records (each record even-odd over its rings):
    a bytearray. Scan lines: every edge adds its crossing to the rows it spans."""
    mask = bytearray(nx * ny)
    for xy in xys:
        rows = {}
        for xs, ys in xy:
            for i in range(len(xs) - 1):
                x1, y1, x2, y2 = xs[i], ys[i], xs[i + 1], ys[i + 1]
                if y1 == y2: continue
                lo, hi = (y1, y2) if y1 < y2 else (y2, y1)
                j0 = max(0, math.ceil((lo - y0) / cell - 0.5)); j1 = min(ny - 1, math.ceil((hi - y0) / cell - 0.5) - 1)
                for j in range(j0, j1 + 1):
                    yc = y0 + (j + 0.5) * cell
                    rows.setdefault(j, []).append(x1 + (yc - y1) * (x2 - x1) / (y2 - y1))
        for j, xsr in rows.items():
            xsr.sort()
            for a, b in zip(xsr[0::2], xsr[1::2]):
                i0 = max(0, math.ceil((a - x0) / cell - 0.5)); i1 = min(nx - 1, math.ceil((b - x0) / cell - 0.5) - 1)
                base = j * nx
                for i in range(i0, i1 + 1): mask[base + i] = 1
    return mask


def bbox_xy(xy):
    xs = [x for a, _ in xy for x in a]; ys = [y for _, b in xy for y in b]
    return min(xs), min(ys), max(xs), max(ys)


# ---- one park -------------------------------------------------------------------------------------------------------------
DRAWN, COVERED, ONCE, SEAM = 0, 1, 2, 3   # segment states


class Rec:
    __slots__ = ('area', 'key', 'layer', 'rank', 'rings', 'sha', 'cluster', 'xy', 'imp', 'seg')

    def __init__(self, area, key, layer, rings, sha, rank=0):
        self.area, self.key, self.layer, self.rings, self.sha, self.rank = area, key, layer, rings, sha, rank
        self.cluster = None; self.xy = None; self.imp = None
        self.seg = None   # seg[ring][i] = state of segment i -> i+1

    def drawn_any(self):
        return any(s == DRAWN for ring in self.seg for s in ring)

    def kept(self):
        """not covered all round by a higher layer: its land is shown (its line may be drawn by another record: draw once, seam)"""
        return any(s != COVERED for ring in self.seg for s in ring)


def clusters(recs):
    """Records whose boxes are within JOIN_LINK_KM are one cluster, measured on its own plane (longitudes unwrapped across 180
    degrees). -> (number of clusters, smallest gap between two clusters in km)."""
    lons = [x for r in recs for ring in r.rings for x, _ in ring]
    wrap = bool(lons) and (max(lons) - min(lons)) > 180
    W = (lambda x: x + 360 if wrap and x < 0 else x)
    boxes = []
    for r in recs:
        xs = [W(x) for ring in r.rings for x, _ in ring]; ys = [y for ring in r.rings for _, y in ring]
        boxes.append((min(xs), min(ys), max(xs), max(ys)))
    n = len(recs); parent = list(range(n))

    def find(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i

    def kx_of(b): return 111.32 * max(0.05, math.cos(math.radians(min(85.0, max(abs(b[1]), abs(b[3]))))))

    def gap(a, b):
        kx = 111.32 * max(0.05, math.cos(math.radians((a[1] + a[3] + b[1] + b[3]) / 4)))
        return math.hypot(max(0.0, max(a[0], b[0]) - min(a[2], b[2])) * kx, max(0.0, max(a[1], b[1]) - min(a[3], b[3])) * 110.574)

    def sweep(bx, link, act):
        order = sorted(range(len(bx)), key=lambda i: bx[i][0])
        for p in range(len(order)):
            i = order[p]; kx = kx_of(bx[i])
            for q in range(p + 1, len(order)):
                j = order[q]
                if (bx[j][0] - bx[i][2]) * kx > link: break
                act(i, j)
    sweep(boxes, JOIN_LINK_KM, lambda i, j: parent.__setitem__(find(i), find(j)) if gap(boxes[i], boxes[j]) < JOIN_LINK_KM else None)
    groups = {}
    for i in range(n): groups.setdefault(find(i), []).append(i)
    gl = list(groups.values())
    for g in gl:
        pts = [(boxes[i][0], boxes[i][1]) for i in g] + [(boxes[i][2], boxes[i][3]) for i in g]
        pr = Proj([((x - 360) if x > 180 else x, y) for x, y in pts])
        for i in g:
            recs[i].cluster = pr
            recs[i].xy = [pr.xy(ring) for ring in recs[i].rings]
    if len(gl) < 2: return 1, 0.0
    gb = [(min(boxes[i][0] for i in g), min(boxes[i][1] for i in g), max(boxes[i][2] for i in g), max(boxes[i][3] for i in g)) for g in gl]
    best = [math.inf]
    sweep(gb, JOIN_FLAG_KM * 4, lambda i, j: best.__setitem__(0, min(best[0], gap(gb[i], gb[j]))))
    if best[0] == math.inf: best[0] = JOIN_FLAG_KM * 4   # nothing within 40 km of anything else: far apart
    return len(gl), best[0]


def rank_of(prec, area, layer):
    order = prec.get(area) or prec.get('default') or ['*']
    if layer in order: return order.index(layer)
    return order.index('*') if '*' in order else len(order)


def seg_samples(xs, ys, i, step=STEP_M):
    """points every `step` m along segment i (both ends included)"""
    dx, dy = xs[i + 1] - xs[i], ys[i + 1] - ys[i]
    n = int(math.hypot(dx, dy) // step) + 1
    return [(xs[i] + dx * k / n, ys[i] + dy * k / n) for k in range(n + 1)]


def seg_len(xs, ys, i): return math.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i])


class ClusterRef:
    """What is already drawn in one cluster: DRAWN segments (draw once), and the higher layers' land and lines (cover)."""
    def __init__(self):
        self.drawn = SegGrid(); self.lines = SegGrid(); self.land = Land(); self.n_lines = 0


def lost_cells(xs_ring, ys_ring, ref, cell_target=20000):
    """For a ring that is covered all round: raster cells inside it that are neither inside the higher layers' land nor within
    COVER_M of their lines (land that hiding the ring would lose). -> (lost cells, band cells, cell size m)."""
    x0, y0, x1, y1 = min(xs_ring), min(ys_ring), max(xs_ring), max(ys_ring)
    cell = max(2.0, min(50.0, math.sqrt(max(1.0, (x1 - x0) * (y1 - y0)) / cell_target)))
    nx, ny = max(1, int(math.ceil((x1 - x0) / cell))), max(1, int(math.ceil((y1 - y0) / cell)))
    inner = raster([[(xs_ring, ys_ring)]], x0, y0, cell, nx, ny)
    lost = band = 0
    for j in range(ny):
        yc = y0 + (j + 0.5) * cell
        run_state = None
        for i in range(nx):
            if not inner[j * nx + i]: run_state = None; continue
            xc = x0 + (i + 0.5) * cell
            if ref.lines.dist(xc, yc, COVER_M * 1.2) <= COVER_M:
                run_state = None
                if not ref.land.inside(xc, yc): band += 1
                continue
            if run_state is None: run_state = ref.land.inside(xc, yc)   # a run of cells far from every line: one test
            if not run_state: lost += 1
    return lost, band, cell


def process_park(recs, prec, merge_m=MERGE_M, multi=False):
    """Decide what is drawn for one park (recs already clustered). Sets r.seg. Order: one layer per park (4), the border seam (6),
    then draw once (5) against segments really drawn. -> stats dict (private)."""
    st = {'covered_records': 0, 'kept_whole_for_land': 0, 'band_m2': 0.0, 'lost_m2_hidden': 0.0, 'seam_m': 0.0, 'once_m': 0.0}
    top = min(r.rank for r in recs)
    refs = {}
    order = sorted(recs, key=lambda r: (r.rank, -sum(len(x) for x in r.rings), r.area, r.key))
    groups = []
    for r in order:
        if groups and groups[-1][0] == r.rank: groups[-1][1].append(r)
        else: groups.append((r.rank, [r]))
    for rank, grp in groups:                                             # 4. one layer per park
        for r in grp:
            ref = refs.setdefault(id(r.cluster), ClusterRef())
            r.seg = []
            for xs, ys in r.xy:
                states = bytearray(max(0, len(xs) - 1))
                if rank != top and ref.n_lines:
                    for i in range(len(states)):
                        cov = True
                        for x, y in seg_samples(xs, ys, i):
                            if ref.lines.dist(x, y, COVER_M * 1.2) <= COVER_M: continue
                            if not ref.land.inside(x, y): cov = False; break
                        if cov: states[i] = COVERED
                    i = 0                                                # uncovered stretches under MIN_STRETCH_M between covered: noise
                    while i < len(states):
                        if states[i] == COVERED: i += 1; continue
                        j = i; L = 0.0
                        while j < len(states) and states[j] != COVERED: L += seg_len(xs, ys, j); j += 1
                        if L < MIN_STRETCH_M and i > 0 and j < len(states):
                            for k in range(i, j): states[k] = COVERED
                        i = j
                    if states and all(s == COVERED for s in states) and signed_area(list(zip(xs, ys))) <= 0:
                        lost, band, cell = lost_cells(xs, ys, ref)       # an outer ring covered all round: would land be lost?
                        if lost >= 1:                                    # even one cell of land would be lost: keep the ring whole
                            states = bytearray(len(states)); st['kept_whole_for_land'] += 1
                        else:
                            st['band_m2'] += band * cell * cell; st['lost_m2_hidden'] += lost * cell * cell
                r.seg.append(states)
            if rank != top and not r.drawn_any(): st['covered_records'] += 1
        for r in grp:                                                    # this layer is now a higher layer for the ones below
            if not r.drawn_any(): continue
            ref = refs[id(r.cluster)]
            for xs, ys in r.xy: ref.lines.add_ring(xs, ys)
            ref.land.add(r.xy); ref.n_lines += 1
    if multi: st['seam_m'] = mark_seams(recs)                            # 6. the border seam, both sides
    drawn_grids = {}
    for r in order:                                                      # 5. draw once: only against segments really drawn
        g = drawn_grids.setdefault(id(r.cluster), SegGrid())
        for (xs, ys), states in zip(r.xy, r.seg):
            for i in range(len(states)):
                if states[i] != DRAWN: continue
                if all(g.dist(x, y, merge_m * 2) <= merge_m for x, y in seg_samples(xs, ys, i)):
                    states[i] = ONCE; st['once_m'] += seg_len(xs, ys, i)
            for i in range(len(states)):
                if states[i] == DRAWN: g.add_ring(xs[i:i + 2], ys[i:i + 2])
    return st


def mark_seams(recs, seam_m=SEAM_M):
    """6. A park in two or more areas: a DRAWN segment within seam_m of a drawn line of the park's records from ANOTHER area,
    where the two tracts lie on opposite sides (a point 5 m inside this tract beside the segment is not inside the other area's
    tract), is the border seam: not drawn. Two copies of one boundary with both tracts on the same side keep their line."""
    areas = {r.area for r in recs}
    if len(areas) < 2: return 0.0
    total = 0.0
    marks = []
    for a in areas:
        grids, lands = {}, {}
        for o in recs:
            if o.area == a or not o.drawn_any(): continue
            g = grids.setdefault(id(o.cluster), SegGrid())
            for (xs, ys), states in zip(o.xy, o.seg):
                for i, s in enumerate(states):
                    if s == DRAWN: g.add_ring(xs[i:i + 2], ys[i:i + 2])
            lands.setdefault(id(o.cluster), Land()).add(o.xy)
        for r in recs:
            if r.area != a: continue
            g, land = grids.get(id(r.cluster)), lands.get(id(r.cluster))
            if g is None: continue
            for ri, ((xs, ys), states) in enumerate(zip(r.xy, r.seg)):
                ring = list(zip(xs, ys))
                for i, s in enumerate(states):
                    if s != DRAWN: continue
                    if not all(g.dist(x, y, seam_m * 2) <= seam_m for x, y in seg_samples(xs, ys, i)): continue
                    dx, dy = xs[i + 1] - xs[i], ys[i + 1] - ys[i]; L = math.hypot(dx, dy)
                    if L == 0: continue
                    mx, my = xs[i] + dx / 2, ys[i] + dy / 2
                    q = [c for c in ((mx - dy / L * 5, my + dx / L * 5), (mx + dy / L * 5, my - dx / L * 5)) if in_ring(c[0], c[1], ring)][:1]
                    if q and not land.inside(q[0][0], q[0][1]): marks.append((r, ri, i)); total += L
    for r, ri, i in marks: r.seg[ri][i] = SEAM
    return total


def level(recs, cap, decimals=DECIMALS, ladder=LADDER, fixed=None):
    """Simplify every record with a drawn segment for one level: the smallest ladder step that brings the park to cap points or
    fewer, or the fixed tolerance. A ring smaller than the tolerance (box diagonal) is dropped at this level only when the
    tolerance is over FINE_OVER_M. -> dict(tol, points, worst (m, measured after rounding, over drawn stretches), hidden rings,
    rings=[(rec, ring index, kept, rounded ring)])."""
    recs = [r for r in recs if r.drawn_any()]
    for r in recs:
        if r.imp is None: r.imp = [dp_importance(xs, ys) for xs, ys in r.xy]
    diag = [(r, i, math.hypot(max(xs) - min(xs), max(ys) - min(ys))) for r in recs for i, (xs, ys) in enumerate(r.xy)
            if any(s == DRAWN for s in r.seg[i])]

    def count(t):
        n = 0
        for r, i, dg in diag:
            if t > FINE_OVER_M and dg < t: continue
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
        if t > FINE_OVER_M and dg < t: hidden += 1; worst = max(worst, dg); continue
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


def lines_of(lv, area=None):
    """The lines drawn at a level (one area, or all): a chord is left out when every segment it stands for is not drawn."""
    out = []
    for r, i, k, qr in lv['rings']:
        if area is not None and r.area != area: continue
        states = r.seg[i]
        if all(s == DRAWN for s in states):
            out.append(qr); continue
        cur = []
        for jj in range(len(k) - 1):
            a, b = k[jj], k[jj + 1]
            if all(s != DRAWN for s in states[a:b]):
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


def invariants(recs, finest):
    """I1 and I2 on the finest level written for the park. -> dict with must_draw_m, missing_m, max_gap_m, lost_m2, band_m2."""
    out = {'must_draw_m': 0.0, 'missing_m': 0.0, 'max_gap_m': 0.0, 'winner_must_m': 0.0, 'winner_missing_m': 0.0,
           'lost_m2': 0.0, 'band_m2': 0.0, 'store_land_m2': 0.0, 'lost_fail': False}
    top = min(r.rank for r in recs)
    by_cluster = {}
    for r in recs: by_cluster.setdefault(id(r.cluster), []).append(r)
    for cid, rs in by_cluster.items():
        pr = rs[0].cluster
        g = SegGrid()
        for ln in finest:   # every drawn line of the finest level, on this cluster's plane
            xs, ys = pr.xy(ln)
            g.add_ring(xs, ys)
        # I1: every segment that must be drawn (not covered by a higher layer, not the seam) is within FINE_OVER_M of a drawn line
        for r in rs:
            for (xs, ys), states in zip(r.xy, r.seg):
                for i, s in enumerate(states):
                    if s in (COVERED, SEAM): continue
                    pts = seg_samples(xs, ys, i); L = seg_len(xs, ys, i)
                    out['must_draw_m'] += L
                    far = 0
                    for x, y in pts:
                        d = g.dist(x, y, FINE_OVER_M * 4)
                        if d > FINE_OVER_M: far += 1; out['max_gap_m'] = max(out['max_gap_m'], d)
                    out['missing_m'] += L * far / len(pts)
                    if r.rank == top: out['winner_must_m'] += L; out['winner_missing_m'] += L * far / len(pts)
        # I2: lost land can only be land of a record covered all round (every other record's land is shown). Each such outer ring,
        # on its own grid (cells of 50 m or less): a point inside it must be inside a shown tract or within COVER_M of a drawn line.
        shown = Land()
        for r in rs:
            if r.kept(): shown.add(r.xy)
        for r in rs:
            if r.kept(): continue
            for xs, ys in r.xy:
                if len(xs) < 4 or signed_area(list(zip(xs, ys))) > 0: continue    # a hole is not land
                x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
                cell = max(2.0, min(50.0, math.sqrt(max(1.0, (x1 - x0) * (y1 - y0)) / 20000)))
                nx, ny = max(1, int(math.ceil((x1 - x0) / cell))), max(1, int(math.ceil((y1 - y0) / cell)))
                inner = raster([[(xs, ys)]], x0, y0, cell, nx, ny)
                lost = band = 0
                for jy in range(ny):
                    yc = y0 + (jy + 0.5) * cell
                    for ix in range(nx):
                        if not inner[jy * nx + ix]: continue
                        xc = x0 + (ix + 0.5) * cell
                        if shown.inside(xc, yc): continue
                        if g.dist(xc, yc, COVER_M * 1.2) <= COVER_M: band += 1
                        else: lost += 1
                out['lost_m2'] += lost * cell * cell; out['band_m2'] += band * cell * cell
                if lost > LOST_TOL_CELLS: out['lost_fail'] = True
        # the park's land in the store (reported only): a coarse grid over the cluster
        bbs = [bbox_xy(r.xy) for r in rs]
        x0, y0 = min(b[0] for b in bbs), min(b[1] for b in bbs)
        x1, y1 = max(b[2] for b in bbs), max(b[3] for b in bbs)
        cell = max(5.0, math.sqrt(max(1.0, (x1 - x0) * (y1 - y0)) / I2_CELLS))
        nx, ny = max(1, int(math.ceil((x1 - x0) / cell))), max(1, int(math.ceil((y1 - y0) / cell)))
        out['store_land_m2'] += sum(raster([r.xy for r in rs], x0, y0, cell, nx, ny)) * cell * cell
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




def read_doubtful(paths, areas):
    """CSV lists of doubtful joins: a 'park' or 'ref' column, optionally 'state' (XX) or 'area' (US-XX). -> {ref: reason}.
    A list that does not exist stops the build (a missing list must never mean 'nothing is doubtful')."""
    out = {}
    if not paths: return out
    paths = [paths] if isinstance(paths, (str, pathlib.Path)) else list(paths)
    areas = [areas] if isinstance(areas, str) else list(areas)
    sts = {a.split('-', 1)[1] for a in areas if '-' in a}
    for path in paths:
        if not pathlib.Path(path).is_file(): raise DisplayError(f'the doubtful-joins list {path} does not exist')
        with open(path, encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                ref = (row.get('park') or row.get('ref') or '').strip()
                if not ref: continue
                st = (row.get('state') or '').strip() or (row.get('area') or '').strip().split('-')[-1]
                if sts and st and st not in sts: continue
                why = ' '.join(x for x in (row.get('matcher_review_state'), row.get('matcher_doubt_code'), row.get('reason')) if x)
                out[ref] = 'doubtful join' + (f' ({why})' if why else '')
    return out


def key_areas(key_dir):
    """ref -> [areas] from the key files (data/us-key/US-XX.json and parts). A folder that does not exist stops the build."""
    out = {}
    if not key_dir: return out
    d = pathlib.Path(key_dir)
    if not d.is_dir(): raise DisplayError(f'--key-dir {key_dir} is not a folder')
    files = sorted(d.glob('US-*.json'))
    if not files: raise DisplayError(f'--key-dir {key_dir} holds no US-XX.json key files')
    for p in files:
        m = re.match(r'US-([A-Z]{2})(\.p\d+)?\.json$', p.name)
        if not m: continue
        try: dd = json.loads(p.read_text(encoding='utf-8'))
        except Exception as e: raise DisplayError(f'{p}: unreadable key file ({e})')
        parks = dd.get('parks') or {}
        for ref in (parks.keys() if isinstance(parks, dict) else [x.get('ref') for x in parks if isinstance(x, dict)]):
            a = 'US-' + m.group(1)
            if a not in out.setdefault(ref, []): out[ref].append(a)
    return out


def build(store_dir, areas, out_dir, cap=CAP, doubtful=None, preview=False, decimals=DECIMALS, merge_m=MERGE_M,
          precedence_table=None, park_areas=None, max_part=MAX_PART, piece_cap=PIECE_CAP, mid_cap=MID_CAP, log=print):
    """Build the display copy of one or more areas in one run (a park in two areas needs both in the same run).
    -> the PRIVATE report (reasons, numbers per park). What is written under out_dir is public."""
    t0 = time.time()
    areas = [areas] if isinstance(areas, str) else sorted(set(areas))
    for a in areas:
        if not re.fullmatch(r'(US|CA)-[A-Z]{2,3}|W-[A-Z]{2}', a): raise DisplayError(f'bad area {a!r}')
    if preview and re.search(r'(^|/)(data/display|data/released|_site)(/|$)', str(pathlib.Path(out_dir).resolve()).replace('\\', '/')):
        raise DisplayError('a PRIVATE PREVIEW is never written into a public folder')
    prec = dict(DEFAULT_PRECEDENCE, **(precedence_table or {}))
    idx, sha = {}, {}
    for a in areas:
        ix, p = read_index(store_dir, a, preview)
        if not preview: require_public_index(ix, a)
        idx[a] = (ix, p)
        for f in sorted({e['file'] for e in ix['parks'].values()} | (set() if preview else set(ix.get('files') or {}))):
            if not re.fullmatch(r'[A-Za-z0-9_.-]+\.kpcstore\.json\.gz', str(f)): raise DisplayError(f'{a}: odd store file name {f!r}')
            if not (pathlib.Path(store_dir) / f).is_file(): raise DisplayError(f'{a}: the index lists {f}, which is not in the store folder')
            sha[f] = file_sha256(pathlib.Path(store_dir) / f)
            meta = (ix.get('files') or {}).get(f) or {}
            if not preview and not meta.get('sha256'): raise DisplayError(f'{f}: the index has no checksum for it')
            if meta.get('sha256') and meta['sha256'] != sha[f]:
                raise DisplayError(f'{f}: sha256 differs from the index (store and index are not from the same build)')
    gen = hashlib.sha256(json.dumps(sorted(sha.items())).encode()).hexdigest()[:12]
    doubt = dict(doubtful or {})
    in_areas = {}
    for a in areas:
        for ref in idx[a][0]['parks']: in_areas.setdefault(ref, []).append(a)
    handles = {}
    res = {a: {'feats': [], 'mid': {}, 'fine': {}, 'fallback': {}} for a in areas}
    rows, why_private = [], {}
    try:
        for ref in sorted(in_areas):
            mine = in_areas[ref]
            others = [a for a in (park_areas or {}).get(ref, []) if a not in mine]

            def fall(why):
                why_private[ref] = why
                for a in mine: res[a]['fallback'][ref] = FALLBACK_CODE
            if others:
                fall(f"also in {', '.join(others)}, which is not in this run (a park's areas are built together)"); continue
            parks, why_not, credit_of, name = {}, [], {}, ref
            for a in mine:
                e = idx[a][0]['parks'][ref]
                p = read_park(store_dir, ref, e, handles); parks[a] = (e, p); name = p.get('name') or name
                if p.get('circle') or p.get('grade') != 'official':
                    why_not.append(f'{a}: not an official outline in the store'); continue
                if e.get('check_join'):
                    cj = e['check_join']; doubt.setdefault(ref, f"check join (tracts in {cj.get('groups')} groups {cj.get('gap_km')} km apart)")
                lt = idx[a][0].get('layers')
                for r in p.get('records') or []:
                    if preview:
                        ok, why, cr = True, '', clean_credit(r.get('credit') or r.get('agency_label')) or str(r.get('layer') or '')
                        if wdpa_hit(r, None, None): ok, why = False, 'WDPA / Protected Planet / SPREP / UNEP-WCMC source'
                    else:
                        ok, why, cr = gate(r, e, lt)
                    if not ok: why_not.append(f"{r.get('key')}: {why}"); continue
                    credit_of[(a, r.get('key'))] = cr
            if why_not:
                fall('licence gate: ' + '; '.join(why_not[:3]) + (f' (+{len(why_not) - 3} more)' if len(why_not) > 3 else '')); continue
            # 3. the same geometry once: the copy from the highest-ranked layer (then area, key)
            cand = []
            for a in mine:
                e, p = parks[a]
                for r in p.get('records') or []:
                    cand.append((rank_of(prec, a, r.get('layer') or ''), a, r.get('key'), r, p))
            seen, recs = set(), []
            for rk, a, key, r, p in sorted(cand, key=lambda c: (c[0], c[1], str(c[2]))):
                if key in seen or r.get('sha256') in seen: continue
                seen.update((key, r.get('sha256')))
                rings = [[(x / SCALE, y / SCALE) for x, y in ring_ints(er)] for er in enc_rings(r, p)]
                rings = [rg for rg in rings if len(rg) >= 2]
                if rings: recs.append(Rec(a, key, r.get('layer') or '', rings, r.get('sha256'), rk))
            n_records = sum(len(parks[a][1].get('records') or []) for a in mine)
            if not recs: fall('no drawable rings in the store'); continue
            ng, sep = clusters(recs)
            if ng > 1 and sep >= JOIN_FLAG_KM: doubt.setdefault(ref, f'check join (tracts in {ng} groups {sep:.1f} km apart)')
            if ref in doubt: fall(doubt[ref]); continue
            store_pts = sum(len(x) for r in recs for x in r.rings)
            multi = len(mine) > 1
            stp = process_park(recs, prec, merge_m, multi)
            drawn = [r for r in recs if r.drawn_any()]
            won = min((r.rank, r.layer) for r in recs)[1]
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
            finest = fine or mid or ov
            inv = invariants(recs, lines_of(finest))
            row = {'ref': ref, 'name': name, 'areas': mine, 'records': n_records, 'distinct_records': len(recs),
                   'drawn_records': len(drawn), 'won': won, 'store_points': store_pts, **stp,
                   'points': ov['points'], 'detail_m': ov['tol'], 'worst_m': round(ov['worst'], 2), 'hidden_rings': ov['hidden'],
                   'mid_points': mid['points'] if mid else None, 'mid_detail_m': mid['tol'] if mid else None,
                   'mid_worst_m': round(mid['worst'], 2) if mid else None,
                   'fine_points': fine['points'] if fine else None, 'fine_worst_m': round(fine['worst'], 2) if fine else None,
                   'street_worst_m': round(finest['worst'], 2), **{k: (round(v, 1) if isinstance(v, float) else v) for k, v in inv.items()}}
            rows.append(row)
            if inv['missing_m'] > 0 or inv['lost_fail']:
                fall(f"invariant failed: {inv['missing_m']:.0f} m of boundary to draw not drawn (max gap {inv['max_gap_m']:.0f} m), "
                     f"{inv['lost_m2']:.0f} m2 of land lost")
                row['failed'] = True
                continue
            merged_add = merge_m if stp['once_m'] else 0.0
            as_lines = multi or any(s != DRAWN for r in drawn for ring in r.seg for s in ring)
            for a in mine:
                lay = sorted({r.layer for r in drawn if r.area == a})
                cr = sorted({credit_of.get((r.area, r.key), '') for r in drawn if r.area == a} - {''})
                base = {'ref': ref, 'name': name, 'g': 'official', 'detail_m': ov['tol'], 'worst_m': round(ov['worst'] + merged_add, 1),
                        'points': sum(len(k) for r, i, k, q in ov['rings'] if r.area == a), 'layers': lay, 'won': won, 'cr': cr,
                        'mid': bool(mid), 'fine': bool(fine)}
                if multi: base.update({'areas': mine, 'gen': gen})
                if as_lines:
                    res[a]['feats'].append({'type': 'Feature', 'properties': dict(base, role='line'),
                                            'geometry': {'type': 'MultiLineString', 'coordinates': rnd(lines_of(ov, a), decimals)}})
                    res[a]['feats'].append({'type': 'Feature', 'properties': dict(base, role='hit'),
                                            'geometry': {'type': 'MultiPolygon', 'coordinates': polys_of(ov, a)}})
                else:
                    res[a]['feats'].append({'type': 'Feature', 'properties': base, 'geometry': {'type': 'MultiPolygon', 'coordinates': polys_of(ov, a)}})
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
            row.update({'mid_bytes': sum(len(gz(res[a]['mid'][ref][1])) for a in mine) if mid else None,
                        'fine_t': {a: res[a]['fine'][ref][1] for a in mine} if fine else None,
                        'fine_pieces': len(fb) if fine else None, 'fine_bytes': sum(fb) if fine else None,
                        'fine_piece_max': max(fb, default=0) if fine else None})
    finally:
        for f in handles.values(): f.close()
    reps = {}
    for a in areas:
        reps[a] = write_area(out_dir, a, res[a], gen, areas, cap, decimals, merge_m, preview, max_part)
        log(f"{a}: {reps[a]['parks']} parks drawn, {reps[a]['fallback']} kept on today's outline, {reps[a]['mid']} middle, "
            f"{reps[a]['fine']} fine ({reps[a]['pieces']} pieces); {reps[a]['bytes_parts']:,} B overview, {reps[a]['bytes_mid']:,} B middle, "
            f"{reps[a]['bytes_fine']:,} B fine")
    rep = {'PRIVATE': 'build report: reasons and numbers per park. Never publish this file.', 'areas': areas, 'gen': gen,
           'made': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'store': sha, 'seconds': round(time.time() - t0, 2),
           'per_area': reps, 'rows': rows, 'fallback_reasons': why_private,
           'invariant_failures': [r['ref'] for r in rows if r.get('failed')]}
    for k in ('fallback', 'bytes_parts', 'bytes_mid', 'bytes_fine', 'pieces'): rep[k] = sum(r[k] for r in reps.values())
    rep['parks_drawn'] = len([r for r in rows if not r.get('failed')])
    return rep


def write_area(out_dir, area, R, gen, built_with, cap, decimals, merge_m, preview, max_part):
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
            if preview:
                d = json.loads(gzip.decompress(b)); d['kpc']['stamp'] = PREVIEW_STAMP; b = gz(d)
            (out / 'fine' / ref / f'{ix}_{iy}.geojson.gz').write_bytes(b)
            tl[f'{ix}_{iy}'] = [hashlib.sha256(b).hexdigest()[:12], len(b)]
        flist[ref] = {'detail_m': tol, 't': T, 'tiles': tl}
    index = {'format': FORMAT, 'area': area, 'gen': gen, 'built_with': built_with,
             'cap': cap, 'mid_cap': MID_CAP, 'mid_over_m': MID_OVER_M, 'fine_over_m': FINE_OVER_M, 'fine_tol_m': FINE_TOL_M,
             'piece_cap': PIECE_CAP, 'decimals': decimals,
             'parks': len({f['properties']['ref'] for f in R['feats']}), 'parts': plist, 'mid': mlist, 'fine': flist,
             'fallback': dict(sorted(R['fallback'].items())),
             'about': 'Display copy for drawing only (overview / middle / fine pieces). A park listed under fallback, or not '
                      'listed, keeps its old outline on the map. Never used for "am I in the park" or 2-fers.'}
    if preview: index['stamp'] = PREVIEW_STAMP
    (out / 'INDEX.json').write_text(json.dumps(index, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return {'parks': index['parks'], 'fallback': len(R['fallback']), 'mid': len(mlist), 'fine': len(flist),
            'pieces': sum(len(v['tiles']) for v in flist.values()), 'bytes_parts': sum(x[3] for x in plist),
            'bytes_mid': sum(v[3] for v in mlist.values()), 'bytes_fine': sum(t[1] for v in flist.values() for t in v['tiles'].values())}


NAME_RX = re.compile(r'(mid/[A-Z0-9-]+|fine/[A-Z0-9-]+/-?\d+_-?\d+|[A-Z0-9-]+(\.p\d+)?)\.geojson\.gz')
PRIVATE_RX = re.compile(r'wdpa|protected ?planet|sprep|unep|licen[cs]e|restrict|private|held\b|publishable|@|https?:|'
                        r'kpcstore|not on the allow|class\b|basis', re.I)


def check(out_dir, area, max_part=1_000_000, public=False, piece_cap=PIECE_CAP):
    """Re-read a written display copy: every file under its cap, sha12 as listed, parts join, every park once, the preview
    stamp consistent (refused with public=True), nothing unlisted, no private words in INDEX.json or the overview (public=True).
    -> problems (empty = good)."""
    out = pathlib.Path(out_dir) / area
    probs = []
    try: raw = (out / 'INDEX.json').read_text(encoding='utf-8'); idx = json.loads(raw)
    except Exception as e: return [f'INDEX.json unreadable: {e}']
    if idx.get('format') != FORMAT: probs.append('wrong format')
    if public and idx.get('stamp'): probs.append('a PRIVATE PREVIEW: never published')
    if idx.get('area') != area: probs.append(f"INDEX is for {idx.get('area')!r}, not {area}")
    if public:
        if any(v != FALLBACK_CODE for v in (idx.get('fallback') or {}).values()): probs.append('INDEX fallback carries a reason (private)')
        if PRIVATE_RX.search(json.dumps({k: v for k, v in idx.items() if k != 'about'})): probs.append('INDEX carries a private word')
    names = [x[0] for x in idx.get('parts') or []] + [v[0] for v in (idx.get('mid') or {}).values()]
    names += [f'fine/{ref}/{t}.geojson.gz' for ref, v in (idx.get('fine') or {}).items() for t in (v.get('tiles') or {})]
    if any('..' in n or n.startswith('/') or not NAME_RX.fullmatch(n) for n in names):
        probs.append('a file name in INDEX is not a display file name'); return probs
    listed = {'INDEX.json'} | set(names)
    present = {str(q.relative_to(out)).replace('\\', '/') for q in out.rglob('*') if q.is_file()}
    if public and present - listed: probs.append(f'files not listed in INDEX: {sorted(present - listed)[:5]}')
    if listed - present: probs.append(f'INDEX lists files that are not there: {sorted(listed - present)[:5]}')
    seen = set()
    for name, sha12, n, size in idx.get('parts') or []:
        p = out / name
        b = p.read_bytes() if p.is_file() else b''
        if not b: continue
        if len(b) > max_part: probs.append(f'{name} is {len(b)} bytes (over {max_part})')
        if hashlib.sha256(b).hexdigest()[:12] != sha12: probs.append(f'{name} sha differs from INDEX')
        d = json.loads(gzip.decompress(b))
        if (d.get('kpc') or {}).get('stamp') != idx.get('stamp'): probs.append(f'{name}: preview stamp differs from INDEX')
        if (d.get('kpc') or {}).get('gen') != idx.get('gen'): probs.append(f'{name}: from another build')
        if len(d.get('features') or []) != n: probs.append(f'{name}: feature count differs from INDEX')
        for f in d.get('features') or []:
            pr = f['properties']; r = pr['ref']; role = pr.get('role', 'park')
            if (r, role) in seen: probs.append(f'{r} {role} twice')
            seen.add((r, role))
            if r in (idx.get('fallback') or {}): probs.append(f'{r} both drawn and fallback')
            if public and any(PRIVATE_RX.search(c) for c in pr.get('cr') or []): probs.append(f'{r}: a credit line carries a private word')
            if pr.get('mid') and r not in (idx.get('mid') or {}): probs.append(f'{r}: middle level missing')
            if pr.get('fine') and r not in (idx.get('fine') or {}): probs.append(f'{r}: fine level missing')
            if pr.get('areas') and (pr.get('gen') != idx.get('gen') or area not in pr['areas']): probs.append(f'{r}: areas / gen inconsistent')
    if len({r for r, _ in seen}) != idx.get('parks'): probs.append(f"{len({r for r, _ in seen})} parks in parts, INDEX says {idx.get('parks')}")
    for ref, (name, sha12, _t, size) in (idx.get('mid') or {}).items():
        b = (out / name).read_bytes() if (out / name).is_file() else b''
        if b and hashlib.sha256(b).hexdigest()[:12] != sha12: probs.append(f'mid {ref}: sha differs')
        elif len(b) > max_part: probs.append(f'mid {ref}: over {max_part} bytes')
    for ref, v in (idx.get('fine') or {}).items():
        for t, (sha12, size) in (v.get('tiles') or {}).items():
            q = out / 'fine' / ref / f'{t}.geojson.gz'
            b = q.read_bytes() if q.is_file() else b''
            if not b: continue
            if hashlib.sha256(b).hexdigest()[:12] != sha12: probs.append(f'fine {ref} {t}: sha differs')
            elif len(b) > piece_cap: probs.append(f'fine {ref} {t}: {len(b)} bytes, over the piece cap {piece_cap}')
            elif (json.loads(gzip.decompress(b)).get('kpc') or {}).get('stamp') != idx.get('stamp'): probs.append(f'fine {ref} {t}: preview stamp differs')
    return probs


def main(argv=None):
    ap = argparse.ArgumentParser(description='Make the map display copy from the outline store (drawing only).')
    sub = ap.add_subparsers(dest='cmd')
    b = sub.add_parser('build')
    b.add_argument('--store', required=True); b.add_argument('--area', required=True, action='append')
    b.add_argument('--out', required=True); b.add_argument('--cap', type=int, default=CAP)
    b.add_argument('--doubtful', action='append', default=[], help='a CSV list of doubtful joins (may be given more than once)')
    b.add_argument('--precedence', help='JSON {area: [layer, ..., "*", ...], "default": [...]} (best first)')
    b.add_argument('--key-dir', help="data/us-key: a park that is also in an area not in this run keeps today's outline")
    b.add_argument('--decimals', type=int, default=DECIMALS); b.add_argument('--merge-m', type=float, default=MERGE_M)
    b.add_argument('--private-preview', action='store_true')
    b.add_argument('--report', '--json', dest='report', help='the PRIVATE build report (reasons per park); must be outside --out')
    c = sub.add_parser('check'); c.add_argument('--out', required=True); c.add_argument('--area', required=True)
    c.add_argument('--public', action='store_true', help='also refuse a PRIVATE PREVIEW, unlisted files and private words')
    a = ap.parse_args(argv)
    try:
        if a.cmd == 'build':
            if a.report and pathlib.Path(out_root := a.out).resolve() in pathlib.Path(a.report).resolve().parents:
                raise DisplayError('the private report must not be written inside the public output folder')
            pt = json.loads(pathlib.Path(a.precedence).read_text(encoding='utf-8')) if a.precedence else None
            rep = build(a.store, a.area, a.out, cap=a.cap, doubtful=read_doubtful(a.doubtful, a.area), preview=a.private_preview,
                        decimals=a.decimals, merge_m=a.merge_m, precedence_table=pt, park_areas=key_areas(a.key_dir))
            if a.report: pathlib.Path(a.report).write_text(json.dumps(rep, indent=1), encoding='utf-8')
            probs = [f'{ar}: {p}' for ar in rep['areas'] for p in check(a.out, ar, public=not a.private_preview)]
            for p in probs: print('PROBLEM', p)
            if rep['invariant_failures']: print(f"{len(rep['invariant_failures'])} park(s) failed an invariant and keep today's outline (see the private report)")
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
