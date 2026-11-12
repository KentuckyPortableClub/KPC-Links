#!/usr/bin/env python3
"""Planner outline files from what is already published: the US key (data/us-key/US-XX.json, which record ids each park joins)
and the saved copy of that state (US-XX.json.gz on the boundary-cache release, read offline). No map server is contacted.

For each park with joined records (`m`) and no outline yet in data/outlines/US-XX.geojson.gz, the joined records' shapes are
put together (shapely union), trimmed with the master's own trim (5 decimals, 0.0001 deg) and written as a master record
(g = the key's g, layer_url = file:US-XX.json.gz, via = key). An outline already in the file is never replaced.
A park whose records are not all in the saved copy is skipped and listed (fail closed: no partial outline).
Nov 11 (job 2): the area is saved by kpc_master.save_area, so a state whose outlines pass 1 MB is written in parts
(US-AK.geojson.gz + US-AK.p2.geojson.gz ..., the release's part scheme) at full default precision: no extra simplification.
--dry-run builds everything in memory, prints per park what would be written, and the part files the save would make (with sizes)
from a scratch copy; nothing in the repo is written. --verify compares the area with the copy at --ref (default HEAD): every
outline that was there is unchanged (a park the key grades pin may be gone), every file is under 1 MB, and the counts.

  python3 .github/scripts/kpc_outlines_from_key.py --cache DIR --states "CT DC ..." [--only-refs US-4512 ...] [--dry-run]
  python3 .github/scripts/kpc_outlines_from_key.py --verify --states AK [--ref HEAD]
KPC owner, 2026-11-11 (planner: shape files for the states with none)."""
import argparse, datetime, gzip, json, os, pathlib, shutil, subprocess, sys, tempfile
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


def union_geometry(rs):
    """The joined records' shapes put together: a GeoJSON Polygon / MultiPolygon, or (None, why) when there is none. shapely only here."""
    from shapely.geometry import MultiPolygon, mapping
    from shapely.ops import unary_union
    shapes = [s for s in (rec_shape(r) for r in rs) if s is not None]
    if not shapes: return None, 'no shape'
    u = polys_only(unary_union(shapes))
    if not u: return None, 'no polygon'
    return (mapping(MultiPolygon(u)) if len(u) > 1 else mapping(u[0])), ''


def npts(g): return sum(len(r) for p in M.polys_of(g) for r in p)


def build_state(st, cache, only=None, dry=False, root=None, key_dir=None, say=print):
    root = pathlib.Path(root or M.OUTLINES); area = f'US-{st}'
    key_dir = pathlib.Path(key_dir or (ROOT / 'data' / 'us-key'))
    key = json.loads((key_dir / f'US-{st}.json').read_text())
    with gzip.open(pathlib.Path(cache) / f'US-{st}.json.gz', 'rt', encoding='utf-8') as f: blob = json.load(f)
    recs = {str(r.get('OBJECTID')): r for r in blob.get('recs') or []}
    counts = M.saved_counts(pathlib.Path(cache) / f'US-{st}.json.gz')
    have = M.load_area(area, root)
    # Nov 12 (KPC owner, 2026-11-12; D6): an outline's date_read comes from the INPUT, not the clock: the park's 'read' date in the key
    # (the oldest day its joined records were read), else the saved copy's 'saved' stamp, else the run's one date (KPC_BUILD_DATE),
    # else today. So the same key + copy give the same outline file bytes on any day.
    today = str(blob.get('saved') or '').strip() or (os.environ.get('KPC_BUILD_DATE') or '').strip() or datetime.date.today().isoformat()
    added, skipped = [], []
    for ref, q in sorted((key.get('parks') or {}).items()):
        if only and ref not in only: continue
        if ref in have: continue
        ids = [str(x[0]) for x in q.get('m') or [] if isinstance(x, list) and x]
        ids = [i for i in ids if M.prefix_of(i) != 'trl']   # a trail line is drawn by the trails layer, not as an outline
        if not ids: continue
        if q.get('g') == 'pin': continue   # KPC owner, 2026-11-11: a park the key grades pin never gets an outline
        miss = [i for i in ids if i not in recs]
        if miss: skipped.append((ref, f'{len(miss)} of {len(ids)} joined records not in the saved copy ({" ".join(miss[:4])})')); continue
        g, why = union_geometry([recs[i] for i in ids])
        if g is None: skipped.append((ref, why)); continue
        g = M.trim_geometry(g)
        g = json.loads(json.dumps(g))   # tuples -> lists
        lay = sorted({M.prefix_of(i) or 'padus' for i in ids})
        agency = '; '.join(sorted({str(recs[i].get('Loc_Mang') or recs[i].get('Mang_Name') or '') for i in ids} - {''}))[:300]
        gk = q.get('g') if q.get('g') in M.RANK else 'official'
        r = M.make_record(ref, q.get('n') or ref, gk, g, agency, f'file:US-{st}.json.gz', ids,
                          sum(counts.get(M.prefix_of(i), 0) for i in set(map(M.prefix_of, ids))), str(q.get('read') or today), '', 'key', layers=lay)
        M.assert_public_safe(r); added.append(r)
        say(f'  {"would write" if dry else "write"} {ref} {gk:<11} {len(ids)} record(s) {npts(g):>8,} points  {(q.get("n") or "")[:60]}')
    if added:
        out = dict(have); out.update({r['ref']: r for r in added})
        if dry:   # the same save into a scratch copy: which files it would make, and how big
            with tempfile.TemporaryDirectory() as t:
                tr = pathlib.Path(t) / 'outlines'; tr.mkdir()
                for f in M.area_files(area, root): shutil.copy(f, tr / f.name)
                M.save_area(area, out, tr, key_dir=key_dir)
                for f in M.area_files(area, tr): say(f'  would save {f.name}: {f.stat().st_size:,} bytes')
        else:
            M.save_area(area, out, root, key_dir=key_dir)
            for f in M.area_files(area, root): say(f'  saved {f.name}: {f.stat().st_size:,} bytes')
    return added, skipped


def verify(st, ref='HEAD', root=None, repo=None):
    """(ok, lines): every outline at `ref` is unchanged (or gone because the key grades it pin), every file under 1 MB, the counts."""
    root = pathlib.Path(root or M.OUTLINES).resolve(); area = f'US-{st}'
    if repo is None:
        top = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=root, capture_output=True, text=True)
        repo = top.stdout.strip() if top.returncode == 0 else ROOT
    repo = pathlib.Path(repo)
    rel = root.resolve().relative_to(repo.resolve()).as_posix()

    def at_ref(n):
        r = subprocess.run(['git', 'show', f'{ref}:{rel}/{n}'], cwd=repo, capture_output=True)
        return r.stdout if r.returncode == 0 else None
    before = M.recs_of_doc(M.load_doc_parts(f'{area}.geojson.gz', at_ref)); now = M.load_area(area, root)
    pins = M.pin_drops(area, before, root.parent / 'us-key')
    changed = sorted(r for r in before if r in now and now[r].get('hash') != before[r].get('hash'))
    lost = sorted(set(before) - set(now) - pins)
    files = M.area_files(area, root); big = [f.name for f in files if f.stat().st_size > M.PART_CAP]
    bad_hash = sorted(r for r, v in now.items() if M.content_hash(v) != v.get('hash'))
    lines = [f'{area}: {len(before)} outline(s) at {ref}, {len(now)} now ({len(set(now) - set(before))} new, {len(set(before) & pins)} dropped as pin)',
             *(f'  {f.name}: {f.stat().st_size:,} bytes' for f in files),
             f'  changed: {" ".join(changed) or "none"}; lost: {" ".join(lost) or "none"}; over 1 MB: {" ".join(big) or "none"}; bad hash: {" ".join(bad_hash) or "none"}']
    return not (changed or lost or big or bad_hash), lines


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument('--cache'); ap.add_argument('--states', required=True)
    ap.add_argument('--only-refs', nargs='*'); ap.add_argument('--dry-run', action='store_true'); ap.add_argument('--root')
    ap.add_argument('--key', help='the us-key folder (default data/us-key)'); ap.add_argument('--verify', action='store_true'); ap.add_argument('--ref', default='HEAD')
    a = ap.parse_args(argv)
    if a.verify:
        ok = True
        for st in a.states.replace(',', ' ').split():
            good, lines = verify(st, a.ref, a.root); ok = ok and good; print('\n'.join(lines)); print(f'US-{st}: ' + ('OK' if good else 'PROBLEM'))
        return 0 if ok else 1
    if not a.cache: ap.error('--cache is needed (the folder that holds US-XX.json.gz)')
    for st in a.states.replace(',', ' ').split():
        added, skipped = build_state(st, a.cache, set(a.only_refs or []) or None, a.dry_run, a.root, a.key)
        print(f'US-{st}: {len(added)} outline(s) {"would be " if a.dry_run else ""}added; {len(skipped)} skipped'
              + ''.join(f'\n  skipped {r}: {w}' for r, w in skipped))
    return 0


if __name__ == '__main__': sys.exit(main())
