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


def index(dirs=('data/us-key/tracts', 'data/ca-key/tracts', 'data/world-key/tracts', 'data/tracts')):
    """{ref: {'tracts': [...], 'parent': ref or None, 'children': [refs]}} over every side file found (the 2-fer switch reads this)."""
    out = {}
    for d in dirs:
        for f in sorted(pathlib.Path(d).glob('*.json')) if pathlib.Path(d).exists() else []:
            j = load(f) or {}
            for r, ts in (j.get('parks') or {}).items(): out.setdefault(r, {'tracts': [], 'parent': None, 'children': []})['tracts'] = ts
            for x in j.get('nested') or []:
                out.setdefault(x['child'], {'tracts': [], 'parent': None, 'children': []})['parent'] = x['parent']
                out.setdefault(x['parent'], {'tracts': [], 'parent': None, 'children': []})['children'].append(x['child'])
    return out
