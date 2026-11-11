#!/usr/bin/env python3
"""Planner outline files from what is already published: the US key (data/us-key/US-XX.json, which record ids each park joins)
and the saved copy of that state (US-XX.json.gz on the boundary-cache release, read offline). No map server is contacted.

For each park with joined records (`m`) and no outline yet in data/outlines/US-XX.geojson.gz, the joined records' shapes are
put together (shapely union), trimmed with the master's own trim (5 decimals, 0.0001 deg) and written as a master record
(g = the key's g, layer_url = file:US-XX.json.gz, via = key). An outline already in the file is never replaced.
A park whose records are not all in the saved copy is skipped and listed (fail closed: no partial outline).

  python3 .github/scripts/kpc_outlines_from_key.py --cache DIR --states "CT DC ..." [--only-refs US-4512 ...] [--dry-run]
KPC owner, 2026-11-11 (planner: shape files for the states with none)."""
import argparse, datetime, gzip, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kpc_master as M  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]


def rec_shape(r):
    from shapely.geometry import shape
    from shapely.validation import make_valid
    g = M.esri_to_geojson({'rings': r.get('_r') or []})
    if not g: return None
    s = make_valid(shape(g))
    return s if not s.is_empty else None


def polys_only(s):
    from shapely.geometry import MultiPolygon, Polygon
    if isinstance(s, Polygon): return [s]
    if isinstance(s, MultiPolygon): return list(s.geoms)
    return [p for x in getattr(s, 'geoms', []) for p in polys_only(x)]


def build_state(st, cache, only=None, dry=False, root=None):
    from shapely.geometry import MultiPolygon, mapping
    from shapely.ops import unary_union
    root = pathlib.Path(root or M.OUTLINES); area = f'US-{st}'
    key = json.loads((ROOT / 'data' / 'us-key' / f'US-{st}.json').read_text())
    with gzip.open(pathlib.Path(cache) / f'US-{st}.json.gz', 'rt', encoding='utf-8') as f: blob = json.load(f)
    recs = {str(r.get('OBJECTID')): r for r in blob.get('recs') or []}
    counts = M.saved_counts(pathlib.Path(cache) / f'US-{st}.json.gz')
    have = M.load_area(area, root); today = datetime.date.today().isoformat()
    added, skipped = [], []
    for ref, q in sorted((key.get('parks') or {}).items()):
        if only and ref not in only: continue
        if ref in have: continue
        ids = [str(x[0]) for x in q.get('m') or [] if isinstance(x, list) and x]
        ids = [i for i in ids if M.prefix_of(i) != 'trl']   # a trail line is drawn by the trails layer, not as an outline
        if not ids: continue
        if q.get('g') == 'pin': continue   # KPC owner, 2026-11-11: a park the key grades pin never gets an outline
        miss = [i for i in ids if i not in recs]
        if miss: skipped.append((ref, f'{len(miss)} of {len(ids)} joined records not in the saved copy')); continue
        shapes = [s for s in (rec_shape(recs[i]) for i in ids) if s is not None]
        if not shapes: skipped.append((ref, 'no shape')); continue
        u = polys_only(unary_union(shapes))
        if not u: skipped.append((ref, 'no polygon')); continue
        g = M.trim_geometry(mapping(MultiPolygon(u)) if len(u) > 1 else mapping(u[0]))
        g = json.loads(json.dumps(g))   # tuples -> lists
        lay = sorted({M.prefix_of(i) or 'padus' for i in ids})
        agency = '; '.join(sorted({str(recs[i].get('Loc_Mang') or recs[i].get('Mang_Name') or '') for i in ids} - {''}))[:300]
        gk = q.get('g') if q.get('g') in M.RANK else 'official'
        added.append(M.make_record(ref, q.get('n') or ref, gk, g, agency, f'file:US-{st}.json.gz', ids,
                                   sum(counts.get(M.prefix_of(i), 0) for i in set(map(M.prefix_of, ids))), today, '', 'key', layers=lay))
    if added and not dry:
        for r in added: M.assert_public_safe(r); have[r['ref']] = r
        M.save_area(area, have, root)
    return added, skipped


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--cache', required=True); ap.add_argument('--states', required=True)
    ap.add_argument('--only-refs', nargs='*'); ap.add_argument('--dry-run', action='store_true'); ap.add_argument('--root')
    a = ap.parse_args()
    for st in a.states.replace(',', ' ').split():
        added, skipped = build_state(st, a.cache, set(a.only_refs or []) or None, a.dry_run, a.root)
        print(f'US-{st}: {len(added)} outline(s) added; {len(skipped)} skipped' + ''.join(f'\n  skipped {r}: {w}' for r, w in skipped[:20]))
    return 0


if __name__ == '__main__': sys.exit(main())
