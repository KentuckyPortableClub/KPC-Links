#!/usr/bin/env python3
"""TRACT RECORDS + PARKS INSIDE PARKS (Nov 6 2026, big key / 2-fer patch; Brandon: 'This would already be handy where we have had to
split up tracts so yes next patch ... lets add that to save from having that trouble later', and the possible POTA rule change about
separate tracts and parks inside parks).

A SIDE FILE next to each answer key. The key files themselves are NOT changed (the website and the 2-fer program read them exactly
as before). For every park with an outline, each official record joined to it is kept as its own TRACT:
  {"src": layer key (kpc_source_fields), "layer": the layer's label, "rid": the record id the key joined (as in m[0]),
   "sid": the source's STABLE id (Source_PAID, UNIT_CODE, ORGCODE, KDFWR_ID, ZONE_ID, SITECODE, cddaId...) or null,
   "name", "ac": the source's own official acres, "ac_measured": acres measured from the shape the key read (kpc_pin_edge),
   "pieces": separate pieces more than 1 km apart (kpc_key_rules.tracts_of), "own", "own_type", "loc_own", "parent", "access",
   "basis": fee / easement / approved boundary ..., "ownership": true (owned land) / false (easement, approved boundary) / null,
   "how": the key's join reason}
and the area file has 'nested': [{"child", "parent", "share", "how"}] = a park whose land lies inside another park's land
(>= 90% of the child's sampled outline points inside the parent, and the child is smaller), and 'same_area': [{"park", "other", "via"}]
= two parks whose records the SOURCE ties to one official area (CPCAD PARENT_ID / WDPA WDPA_PID / NPS UNIT_CODE): separate tracts.
Shape (KY answer key tracts[] = [layer, name, acres, how, pieces]) -> the same five facts are here, plus the source facts.

Files: data/us-key/tracts/US-XX.json, data/ca-key/tracts/CA-XX.json, data/world-key/tracts/CC.json, data/tracts/US-KY.json.
Switch KPC_TRACT_STORE (default 1 = write the side file; 0 = off). It never changes a join, a pin, an outline or a 2-fer.
"""
import json, os, pathlib, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpc_source_fields as SF
import kpc_pin_edge as PE

SCHEMA = 1
NEST_SHARE = 0.9


def on():
    return str(os.environ.get('KPC_TRACT_STORE', '1')).strip().lower() not in ('0', 'off', 'no', 'false')


# ---------------------------------------------------------------------------------------------------------------------------------
# Nov 7 Part 1 (KEY / 2-FER / WORLD handoff, 'tracts + nested parks + 2-fer switch'). Everything below is OFF by default and only
# READS the side files: the side file written above is byte-for-byte what it was unless KPC_TRACT_STORE=shapes (then each tract also
# carries a thinned 'shape' so the 2-fer count switch can test the spot against the tract's SHAPE, not its box).
#
# What a tract is (handoff 'Decision', used everywhere): one separate piece of land. Stored as one side-file entry per official
# record; a multipart record whose pieces are more than 1 km apart ('pieces' > 1) is split into one tract per piece at READ time
# (split() below). Stable id '<ref>#<n>', n ordered by acres, largest first.
#
# The switches (no new one; the file only holds defaults):
#   KPC_TRACT_STORE      1 (default) = write side files as before | 0 = off | shapes = also write each tract's thinned shape
#   KPC_FERS_COUNT_MODE  whole_park (default) | tracts | nested       (kpc_fers_count.py, the ONLY place 2-fer counting changes)
#   KPC_TRACT_MODE       one_park (default, today's rules) | own_park (each tract may be its own possible new park);
#                        env first, then data/tract-switch.json 'tract_mode', then one_park
# data/tract-switch.json = {"on": false, "mode": "whole_park", "tract_mode": "one_park"} (on/mode: the website's display switch,
# read by kpc-bounds.js KPCB.tractsOn(); the 2-fer bot reads only its env, so the file can never change a published spot file).
TRACT_MODES = ('one_park', 'own_park')
COUNT_MODES = ('whole_park', 'tracts', 'nested')
SWITCH_DEFAULT = {'on': False, 'mode': 'whole_park', 'tract_mode': 'one_park'}
GAP_KM = 1.0          # pieces closer than this are one tract (same as kpc_key_rules.tracts_of, which is used, never copied)
SHAPE_MAX = 400       # points per tract shape when KPC_TRACT_STORE=shapes (GUESS: enough for 'is this spot in this tract')
CONTAIN_SHARE = 0.8   # a ring is a hole of another ring when >= 80% of its points lie inside it (thinned rings can cross a little)
_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


def store_shapes():
    return str(os.environ.get('KPC_TRACT_STORE', '1')).strip().lower() == 'shapes'


def switch(paths=None):
    """data/tract-switch.json merged over the defaults (bad or missing values fall back to the default). The working folder's copy
    first (a bot run from a KPC-Data checkout), then the KPC-Links copy next to this script."""
    out = dict(SWITCH_DEFAULT)
    for p in paths or ('data/tract-switch.json', _ROOT / 'data' / 'tract-switch.json'):
        j = load(p)
        if not isinstance(j, dict): continue
        if isinstance(j.get('on'), bool): out['on'] = j['on']
        if j.get('mode') in COUNT_MODES: out['mode'] = j['mode']
        if j.get('tract_mode') in TRACT_MODES: out['tract_mode'] = j['tract_mode']
        break
    return out


def tract_mode(paths=None):
    m = str(os.environ.get('KPC_TRACT_MODE') or '').strip().lower()
    if m in TRACT_MODES: return m
    if m: print(f'::warning title=tract mode::unknown KPC_TRACT_MODE {m!r}; using the switch file / one_park', flush=True)
    return switch(paths)['tract_mode']


def _thin_shape(rings, max_pts=SHAPE_MAX):
    rings = [r for r in rings or [] if r and len(r) >= 3]
    tot = sum(len(r) for r in rings)
    k = max(1, -(-tot // max_pts)) if tot else 1
    out = []
    for r in rings:
        q = r[::k] if len(r[::k]) >= 4 else r[::max(1, len(r) // 4)]
        q = [[round(float(p[0]), 5), round(float(p[1]), 5)] for p in q]
        if q and q[0] != q[-1]: q.append(list(q[0]))
        if len(q) >= 4: out.append(q)
    return out


def _signed(r):
    return sum(r[i][0] * r[(i + 1) % len(r)][1] - r[(i + 1) % len(r)][0] * r[i][1] for i in range(len(r))) / 2.0


def _in_ring(x, y, r):
    ins, j = False, len(r) - 1
    for i in range(len(r)):
        xi, yi, xj, yj = r[i][0], r[i][1], r[j][0], r[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi: ins = not ins
        j = i
    return ins


def ring_roles(rings):
    """[(parent index or None, is_hole)] per ring. A ring's parent = the smallest other ring holding >= CONTAIN_SHARE of its points.
    A ring is a HOLE when its parent is an outer ring wound the other way; an island in a hole, or two outer rings that overlap or
    repeat each other, stay outer rings. So 'inside' = inside any outer ring and outside that ring's holes (overlapping tracts in one
    MultiPolygon stay inside where they overlap; plain even-odd would call the overlap outside)."""
    rs = [r for r in rings]
    bb = [_bbox([r]) for r in rs]
    area = [abs(_signed(r)) for r in rs]
    parent = []
    for i, r in enumerate(rs):
        best = None
        for j, o in enumerate(rs):
            if i == j or not bb[i] or not bb[j] or area[j] <= area[i]: continue
            if bb[i][0] < bb[j][0] - 1e-9 or bb[i][1] < bb[j][1] - 1e-9 or bb[i][2] > bb[j][2] + 1e-9 or bb[i][3] > bb[j][3] + 1e-9: continue
            pts = r[:-1] if len(r) > 1 and r[0] == r[-1] else r
            if pts and sum(1 for p in pts if _in_ring(p[0], p[1], o)) / len(pts) >= CONTAIN_SHARE and (best is None or area[j] < area[best]): best = j
        parent.append(best)
    hole = [False] * len(rs)
    for i in sorted(range(len(rs)), key=lambda i: -area[i]):     # parents (bigger) are decided first
        p = parent[i]
        hole[i] = p is not None and not hole[p] and (_signed(rs[i]) > 0) != (_signed(rs[p]) > 0)
    return list(zip(parent, hole))


def in_shape(rings, la, lo):
    rings = [r for r in rings or [] if r and len(r) >= 3]
    roles = ring_roles(rings)
    for i, r in enumerate(rings):
        if roles[i][1] or not _in_ring(lo, la, r): continue
        if any(roles[j] == (i, True) and _in_ring(lo, la, rings[j]) for j in range(len(rings))): continue
        return True
    return False


def piece_groups(rings, gap_km=GAP_KM):
    """Groups of ring indexes, one group per piece more than gap_km from the others (kpc_key_rules.tracts_of: the same 1 km rule
    the 'pieces' count uses). Holes sit inside their outer ring's box, so they stay with it."""
    rings = [r for r in rings or [] if r and len(r) >= 3]
    if not rings: return []
    try:
        import kpc_key_rules as KR
        return KR.tracts_of([_bbox([r]) for r in rings], gap_km)
    except Exception: return [list(range(len(rings)))]  # noqa: BLE001


def _acres(t):
    v = t.get('ac_measured') if t.get('ac_measured') is not None else t.get('ac')
    try: return float(v) if v is not None else 0.0
    except (TypeError, ValueError): return 0.0


def split(ref, recs, twins=()):
    """READ-TIME tracts of one park, from its side-file records. Returns [{'id': '<ref>#<n>', 'rid', 'sid', 'name', 'src', 'ac', 'box',
    'shape'?, 'part'?, 'of'?, 'approx_split'?}], largest first. A record listed as a key 'twin' (the same land as another joined
    record) is left out, the same way the website leaves it out. A record with pieces > 1 is split by its shape when the side file has
    one (KPC_TRACT_STORE=shapes); without a shape it becomes 'pieces' tracts that share the record's box and an even share of its
    acres, marked approx_split (GUESS: the side file has no per-piece box)."""
    tw = {str(x) for x in twins or ()}
    rows = []
    for k, t in enumerate(recs or []):
        if not isinstance(t, dict) or str(t.get('rid')) in tw: continue
        shp = [r for r in t.get('shape') or [] if r and len(r) >= 3]
        n = t.get('pieces') or 1
        base = {'rid': t.get('rid'), 'sid': t.get('sid'), 'name': t.get('name'), 'src': t.get('src')}
        if n > 1 and shp:
            gs = piece_groups(shp)
            for gi, g in enumerate(gs):
                rg = [shp[i] for i in g]
                rows.append(dict(base, ac=round(PE.acres_rings(rg), 1), box=[round(v, 4) for v in _bbox(rg)], shape=rg, part=gi + 1, of=len(gs), _k=(k, gi)))
        elif n > 1:
            for gi in range(n):
                rows.append(dict(base, ac=round(_acres(t) / n, 1), box=t.get('box'), part=gi + 1, of=n, approx_split=True, _k=(k, gi)))
        else:
            rows.append(dict(base, ac=round(_acres(t), 1), box=t.get('box'), _k=(k, 0), **({'shape': shp} if shp else {})))
    rows.sort(key=lambda x: (-(x['ac'] or 0), str(x['rid']), x['_k']))
    for i, x in enumerate(rows):
        x['id'] = f'{ref}#{i + 1}'; del x['_k']
    return rows


def at(tr, la, lo, pad=1e-4):
    """(inside?, 'shape' | 'box'): the tract's shape when the side file has one, else its box (the old label rule)."""
    if tr.get('shape'): return in_shape(tr['shape'], la, lo), 'shape'
    b = tr.get('box')
    return bool(b and b[0] - pad <= lo <= b[2] + pad and b[1] - pad <= la <= b[3] + pad), 'box'


def _bbox(rings):
    xs = [p[0] for r in rings for p in r]; ys = [p[1] for r in rings for p in r]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


def pieces(rings, gap_km=1.0):
    try:
        import kpc_key_rules as KR
        outer = [r for r in rings if r and len(r) >= 3]
        if not outer: return 0
        return len(KR.tracts_of([_bbox([r]) for r in outer], gap_km))
    except Exception: return None  # noqa: BLE001


def tract(rid, name, how, attrs=None, mp=None, rings=None, layer='', src_key=None, ac_key=None):
    """One tract record. attrs = the record's own fields; mp = kpc_source_fields.mapping(...) for its layer."""
    f = SF.read(mp, attrs or {}) if mp else {}
    key = src_key or (mp or {}).get('key') or 'unknown'
    t = {'src': key, 'layer': layer, 'rid': rid, 'sid': f.get('sid'), 'name': name, 'ac': f.get('ac', ac_key), 'how': how}
    for k in ('own', 'own_type', 'loc_own', 'parent', 'access'):
        if f.get(k) is not None: t[k] = f[k]
    if f.get('basis') is not None:
        t['basis'] = SF.basis_word(key, f['basis']); t['ownership'] = SF.is_ownership(key, f['basis'])
    if rings:
        try: t['ac_measured'] = round(PE.acres_rings(rings), 1)
        except Exception: pass  # noqa: BLE001
        p = pieces(rings)
        if p: t['pieces'] = p
        try:
            b = _bbox([r for r in rings if r and len(r) >= 3])
            if b: t['box'] = [round(float(v), 4) for v in b]   # Nov 6: lets the 2-fer count switch place a spot in a tract
        except Exception: pass  # noqa: BLE001
        if store_shapes():   # Nov 7: only with KPC_TRACT_STORE=shapes (default 1 writes exactly what it wrote before)
            try:
                s = _thin_shape(rings)
                if s: t['shape'] = s
            except Exception: pass  # noqa: BLE001
    return t


def _sample(rings, n=40):
    pts = [p for r in rings for p in r[:-1]] if rings else []
    if len(pts) <= n: return pts
    step = len(pts) / n
    return [pts[int(i * step)] for i in range(n)]


def nested_geometry(shapes, share=NEST_SHARE):
    """shapes = {ref: rings}. A child = a smaller park with >= share of its sampled outline points inside the other park's land
    (points on the shared edge count as inside when within 30 m). Returns [{'child','parent','share','how'}]; the smallest
    holding park is the direct parent (a park inside a park inside a park keeps its chain)."""
    S = {}
    for r, rg in shapes.items():
        rg = [x for x in rg or [] if x and len(x) >= 3]
        if not rg: continue
        S[r] = (rg, _bbox(rg), PE.acres_rings(rg), _sample(rg))
    out = []
    for c, (rc, bc, ac, sc) in S.items():
        holders = []
        for p, (rp, bp, ap, _sp) in S.items():
            if p == c or ap <= ac * 1.05: continue
            if bc[0] < bp[0] - 1e-3 or bc[1] < bp[1] - 1e-3 or bc[2] > bp[2] + 1e-3 or bc[3] > bp[3] + 1e-3: continue
            n_in = 0
            for x, y in sc:
                if PE.inside(y, x, rp): n_in += 1
                else:
                    e = PE.edge_info(y, x, rp)
                    if e['edge_m'] is not None and e['edge_m'] <= 30: n_in += 1
            s = n_in / len(sc) if sc else 0
            if s >= share: holders.append((ap, p, s))
        if holders:
            ap, p, s = min(holders)
            out.append({'child': c, 'parent': p, 'share': round(s, 2), 'how': 'geometry'})
    return sorted(out, key=lambda x: (x['parent'], x['child']))


def same_area(park_tracts):
    """Links the SOURCE states: a tract whose 'parent' id is another park's tract 'sid' (CPCAD PARENT_ID -> ZONE_ID, WDPA WDPA_PID ->
    WDPAID, NPS tract UNIT_CODE -> boundary UNIT_CODE). Read live Nov 6: CPCAD's PARENT_ID mostly ties the ZONES (separate pieces) of ONE
    protected area together, so two POTA parks linked this way are separate tracts of one official area (the tract-split case), not
    a park inside a park; the shape test (nested_geometry) is what says 'inside'. Returns [{'park','other','via'}], each pair once."""
    by_sid = {}
    for ref, ts in park_tracts.items():
        for t in ts:
            if t.get('sid'): by_sid.setdefault(str(t['sid']), set()).add(ref)
    out = set()
    for ref, ts in park_tracts.items():
        for t in ts:
            par = t.get('parent')
            if not par or str(par) == str(t.get('sid')): continue
            for p in by_sid.get(str(par), set()) - {ref}: out.add((min(ref, p), max(ref, p), f"{t['src']} parent id {par}"))
            # two zones that name the same parent are tracts of one area too
            for ref2, ts2 in park_tracts.items():
                if ref2 != ref and any(str(q.get('parent')) == str(par) for q in ts2): out.add((min(ref, ref2), max(ref, ref2), f"{t['src']} parent id {par}"))
    return [{'park': a, 'other': b, 'via': v} for a, b, v in sorted(out)]


def nested_source(park_tracts):   # kept for callers: the source links are 'same_area', never 'inside'
    return []


def merge_nested(*lists):
    seen, out = {}, []
    for L in lists:
        for x in L:
            k = (x['child'], x['parent'])
            if k in seen: seen[k]['how'] = seen[k]['how'] + '+' + x['how'] if x['how'] not in seen[k]['how'] else seen[k]['how']; continue
            seen[k] = dict(x); out.append(seen[k])
    return out


def coverage(park_tracts):
    """{source key: {'records','sid','ac','own','parent'}} counted over the joined records (what the coverage report shows)."""
    cov = {}
    for ts in park_tracts.values():
        for t in ts:
            c = cov.setdefault(t['src'], {'records': 0, 'sid': 0, 'ac': 0, 'own': 0, 'parent': 0})
            c['records'] += 1
            for k in ('sid', 'ac', 'own', 'parent'):
                if t.get(k) not in (None, ''): c[k] += 1
    return cov


def doc(area, park_tracts, nested, note='', same=None):
    return {'schema': SCHEMA, 'area': area, 'built': time.strftime('%Y-%m-%d'), 'same_area': same if same is not None else same_area(park_tracts),
            'about': 'Tract records (one per official record joined to the park) + parks inside parks. Side file: the key file is unchanged. '
                     'See .github/scripts/kpc_tracts.py. ' + note,
            'coverage': coverage(park_tracts), 'nested': nested,
            'parks': {r: ts for r, ts in sorted(park_tracts.items()) if ts}}


def save(path, d):
    path = pathlib.Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from kpc_save import save_json
        save_json(path, d)
    except Exception:  # noqa: BLE001
        path.write_text(json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(',', ':')), encoding='utf-8')
    # Nov 6 research packs. KPC_RESEARCH_SOURCES defaults to off: note_saved returns without reading or writing,
    # and it does not change `d` or this file. Report mode writes a side report only (kpc_research_sources.py,
    # not a rule file). The US / Canada / world rule scripts are not edited, so their rules hashes stay put.
    try:
        import kpc_research_sources as _RS
        _RS.note_saved(path, d)
    except Exception:  # noqa: BLE001
        pass


def load(path):
    try: return json.load(open(path, encoding='utf-8'))
    except Exception: return None  # noqa: BLE001


def index(dirs=('data/us-key/tracts', 'data/ca-key/tracts', 'data/world-key/tracts', 'data/tracts'), twins=False):
    """{ref: {'tracts': [...], 'parent': ref or None, 'children': [refs], 'area'}} over every side file found (the 2-fer switch reads
    this). twins=True (Nov 7) also reads each side file's answer key for its 'twin' record ids ('twin': [...])."""
    out = {}
    for d in dirs:
        for f in sorted(pathlib.Path(d).glob('*.json')) if pathlib.Path(d).exists() else []:
            j = load(f) or {}
            area = j.get('area') or f.stem
            tw = twins_for(f) if twins else {}
            for r, ts in (j.get('parks') or {}).items():
                e = out.setdefault(r, {'tracts': [], 'parent': None, 'children': []}); e['tracts'] = ts; e['area'] = area
                if tw.get(r): e['twin'] = tw[r]
            for x in j.get('nested') or []:
                out.setdefault(x['child'], {'tracts': [], 'parent': None, 'children': []})['parent'] = x['parent']
                out[x['child']]['area'] = out[x['child']].get('area') or area
                out.setdefault(x['parent'], {'tracts': [], 'parent': None, 'children': []})['children'].append(x['child'])
    return out


def twins_for(tract_file):
    """{ref: [twin record ids]} from the answer key next to a side file (data/us-key/tracts/US-AL.json -> data/us-key/US-AL.json).
    The key's 'twin' list = joined records that are the same land as another joined record (the website does not draw them twice)."""
    p = pathlib.Path(tract_file)
    k = load(p.parent.parent / p.name) or {}
    return {r: [str(x) for x in v.get('twin') or []] for r, v in (k.get('parks') or {}).items() if isinstance(v, dict) and v.get('twin')}


def tracts_of_ref(IDX, ref):
    """The read-time tracts of one park from an index() result, cached on the entry (labels only)."""
    e = IDX.get(ref) or {}
    if '_split' not in e and e.get('tracts'): e['_split'] = split(ref, e['tracts'], e.get('twin') or ())
    return e.get('_split') or []
