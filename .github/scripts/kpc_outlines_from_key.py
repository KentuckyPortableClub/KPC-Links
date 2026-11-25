#!/usr/bin/env python3
"""Planner outline files from what is already published: the US key (data/us-key/US-XX.json, which record ids each park joins)
and the saved copy of that state (US-XX.json.gz on the boundary-cache release, read offline). No map server is contacted.

For each park with joined records (`m`) and no outline yet in data/outlines/US-XX.geojson.gz, the joined records' shapes are
put together (shapely union), trimmed with the master's own trim (5 decimals, 0.0001 deg) and written as a master record
(g = the key's g, layer_url = file:US-XX.json.gz, via = key). An outline already in the file is kept when it already agrees with the key (grade not PIN, record_ids are the key's m).
A PIN leftover, a ref no key lists, or an outline that holds a record the key did not join is rebuilt from the key (or dropped
on save). A park whose records are not all in the saved copy is skipped and listed (fail closed: no partial outline).
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


def store_records(store, area):
    """25 Nov 2026 (KPC-Links #380, the other builder's next fix): the outline store's own records of one area, by record id as
    the key spells it ('sgmnc210', a PAD-US number), at the store's full detail: {id: {'_r': rings, 'Loc_Mang', 'publishable',
    'read', 'layer_url', 'name'}}. {} when the store folder or the area's file is not there. Reads files only."""
    if not store: return {}
    f = pathlib.Path(store) / f'{area}.kpcstore.json.gz'
    if not f.is_file(): return {}
    import kpc_store_attrs as SA
    with gzip.open(f, 'rt', encoding='utf-8') as fh: d = json.load(fh)
    out = {}
    for p in d.get('parks') or []:
        for r in p.get('records') or []:
            k = SA.record_key(r)
            if not k: continue
            rs = SA.record_rings(r)
            if not rs: continue
            out[k] = {'_r': rs, 'Loc_Mang': r.get('agency_label') or '', 'publishable': r.get('publishable') is True,
                      'read': str(r.get('read') or '')[:10], 'layer_url': r.get('layer_url') or '', 'name': r.get('record_name') or ''}
    return out


def clip_rec(rec, boxes):
    """D9 / rule B12 (KPC owner, 2026-11-17): a record shared by two far-apart parks keeps, for THIS park, only the rings whose middle
    sits in one of the park's own part boxes from the key ('parts' {record id: [[w, s, e, n], ...]}), +-0.01 degree, exactly as
    the 2-fer bot clips (kpc_fers.clip). Holes ride along with their part. No box, or no ring left = the record as it is."""
    rs = rec.get('_r') or []
    if not boxes or not rs: return rec
    def mid(r): return ((min(q[0] for q in r) + max(q[0] for q in r)) / 2, (min(q[1] for q in r) + max(q[1] for q in r)) / 2)
    keep = [r for r in rs if len(r) > 2 and any(b[0] - .01 <= mid(r)[0] <= b[2] + .01 and b[1] - .01 <= mid(r)[1] <= b[3] + .01 for b in boxes)]
    return dict(rec, _r=keep) if keep else rec


def build_state(st, cache, only=None, dry=False, root=None, key_dir=None, say=print, store=None):
    root = pathlib.Path(root or M.OUTLINES); area = f'US-{st}'
    key_dir = pathlib.Path(key_dir or (ROOT / 'data' / 'us-key'))
    key = json.loads((key_dir / f'US-{st}.json').read_text())
    cache_path = pathlib.Path(cache) / f'US-{st}.json.gz' if cache else pathlib.Path()
    blob, recs, counts = {}, {}, {}
    if cache_path.is_file():
        with gzip.open(cache_path, 'rt', encoding='utf-8') as f: blob = json.load(f)
        recs = {str(r.get('OBJECTID')): r for r in blob.get('recs') or []}
        counts = M.saved_counts(cache_path)
    have = M.load_area(area, root)
    # Nov 12 (KPC owner, 2026-11-12; D6): an outline's date_read comes from the INPUT, not the clock: the park's 'read' date in the key
    # (the oldest day its joined records were read), else the saved copy's 'saved' stamp, else the run's one date (KPC_BUILD_DATE),
    # else today. So the same key + copy give the same outline file bytes on any day.
    today = str(blob.get('saved') or '').strip() or (os.environ.get('KPC_BUILD_DATE') or '').strip() or datetime.date.today().isoformat()
    def stale(ref, rec, q):
        """True when the existing outline must be rebuilt or will be dropped: PIN, or record_ids are not the key's m."""
        if q.get('g') == 'pin': return True
        if q.get('parts'): return True   # D9: a park given only its own parts of a shared record is always drawn from those parts
        ids = [str(x[0]) for x in (q.get('m') or []) if isinstance(x, list) and x]
        ids = [i for i in ids if M.prefix_of(i) != 'trl']
        # 25 Nov 2026: a park joined to a fresh store record whose outline was not cut from the store is always rebuilt (the
        # same number in the old saved copy can be other land, so equal record ids prove nothing)
        if any(i in fresh for i in ids) and not str(rec.get('layer_url') or '').startswith('store:'): return True
        have_ids = M.outline_record_ids(rec)
        return sorted(have_ids) != sorted(ids)
    added, skipped, replaced = [], [], []
    # 25 Nov 2026 (KPC-Links #380 grade, must-fix): a key built from the outline store's own records (KPC_STORE_FRESH) lists
    # them in 'fresh_store'. Their shapes are NOT in the saved copy: the same number there can be other land (fresh sgmnc210
    # drew old 210, about 140 miles off). Fail closed: a park with any such record is skipped (kept as it is, listed), never
    # cut from the saved copy. Cutting it from the store is a later step.
    fresh = {str(i) for i in ((key.get('fresh_store') or {}).get('ids') or [])}
    srecs = store_records(store, area) if fresh else {}
    drop_fresh = []
    # M1 (grade of round 4): no store file for this area = this run cannot tell what the fresh records look like. It changes
    # NOTHING here: no save, every old outline kept, the reason listed, and the caller exits 3 (the workflow then says the file
    # is as it was and the sync marks the state HELD). Only with the store file present is an old outline ever dropped.
    if fresh and not (store and (pathlib.Path(store) / f'{area}.kpcstore.json.gz').is_file()):
        return [], [('*', f'{len(fresh)} fresh store record id(s) in the key, but no outline store file for {area} '
                          f'(--store / KPC_STORE_DIR): nothing changed, nothing saved, every old outline kept (HELD)')]
    for ref, q in sorted((key.get('parks') or {}).items()):
        if only and ref not in only: continue
        if ref in have and not stale(ref, have[ref], q): continue
        ids = [str(x[0]) for x in q.get('m') or [] if isinstance(x, list) and x]
        ids = [i for i in ids if M.prefix_of(i) != 'trl']   # a trail line is drawn by the trails layer, not as an outline
        if not ids: continue
        if q.get('g') == 'pin': continue   # KPC owner, 2026-11-11: a park the key grades pin never gets an outline
        _fr = [i for i in ids if i in fresh]
        if _fr:
            # 25 Nov 2026: a park joined to fresh store records is cut from the STORE's own outlines, never the saved copy. Every
            # one of its records must be in the store and publishable; else it is skipped and its old outline is DROPPED (it
            # may hold land the fresh match left out): the park shows its pin. Fail closed.
            why = ''
            if any(i not in srecs for i in ids): why = f'{sum(1 for i in ids if i not in srecs)} of {len(ids)} joined records not in the store ({" ".join([i for i in ids if i not in srecs][:4])})'
            elif any(not srecs[i]['publishable'] for i in ids): why = f'{sum(1 for i in ids if not srecs[i]["publishable"])} of {len(ids)} joined store records not publishable (licence)'
            if why:
                skipped.append((ref, f'fresh store records ({" ".join(_fr[:4])}): {why}; not cut (fail closed)'))
                if ref in have: drop_fresh.append(ref)
                continue
            _parts = q.get('parts') or {}
            g, why = union_geometry([clip_rec(srecs[i], _parts.get(i)) for i in ids])
            if g is None:
                skipped.append((ref, f'fresh store records: {why}'))
                if ref in have: drop_fresh.append(ref)
                continue
            g = json.loads(json.dumps(M.trim_geometry(g)))
            lay = sorted({M.prefix_of(i) or 'padus' for i in ids})
            agency = '; '.join(sorted({srecs[i]['Loc_Mang'] for i in ids} - {''}))[:300]
            gk = q.get('g') if q.get('g') in M.RANK else 'official'
            rd = min((srecs[i]['read'] for i in ids if srecs[i]['read']), default='') or str(q.get('read') or today)
            r = M.make_record(ref, q.get('n') or ref, gk, g, agency, f'store:{area}.kpcstore.json.gz', ids, 0, rd, '', 'key', layers=lay)
            M.assert_public_safe(r); added.append(r)
            if ref in have: replaced.append(ref)
            say(f'  {"would write" if dry else "write"} {ref} {gk:<11} {len(ids)} store record(s) {npts(g):>8,} points  {(q.get("n") or "")[:60]}')
            continue
        if not recs: skipped.append((ref, 'no saved copy (cannot rebuild this outline this run)')); continue
        miss = [i for i in ids if i not in recs]
        if miss: skipped.append((ref, f'{len(miss)} of {len(ids)} joined records not in the saved copy ({" ".join(miss[:4])})')); continue
        _parts = q.get('parts') or {}   # D9 / rule B12: only this park's own parts of a shared multipart record
        g, why = union_geometry([clip_rec(recs[i], _parts.get(i)) for i in ids])
        if g is None: skipped.append((ref, why)); continue
        g = M.trim_geometry(g)
        g = json.loads(json.dumps(g))   # tuples -> lists
        lay = sorted({M.prefix_of(i) or 'padus' for i in ids})
        agency = '; '.join(sorted({str(recs[i].get('Loc_Mang') or recs[i].get('Mang_Name') or '') for i in ids} - {''}))[:300]
        gk = q.get('g') if q.get('g') in M.RANK else 'official'
        r = M.make_record(ref, q.get('n') or ref, gk, g, agency, f'file:US-{st}.json.gz', ids,
                          sum(counts.get(M.prefix_of(i), 0) for i in set(map(M.prefix_of, ids))), str(q.get('read') or today), '', 'key', layers=lay)
        M.assert_public_safe(r); added.append(r)
        if ref in have: replaced.append(ref)
        say(f'  {"would write" if dry else "write"} {ref} {gk:<11} {len(ids)} record(s) {npts(g):>8,} points  {(q.get("n") or "")[:60]}')
    out = {k: v for k, v in have.items() if k not in set(drop_fresh)}; out.update({r['ref']: r for r in added})
    # Always run save_area when there is something to drop (PIN leftovers, refs not in any key) or something to write, even
    # if this pass added no new park: an outline already in the file is otherwise never cleaned.
    drop_pin = M.pin_drops(area, out, key_dir)
    drop_unk = M.not_in_key_drops(area, out, key_dir)
    if added or drop_pin or drop_unk or drop_fresh:
        if dry:   # the same save into a scratch copy: which files it would make, and how big
            with tempfile.TemporaryDirectory() as t:
                tr = pathlib.Path(t) / 'outlines'; tr.mkdir()
                for f in M.area_files(area, root): shutil.copy(f, tr / f.name)
                M.save_area(area, out, tr, key_dir=key_dir)
                for f in M.area_files(area, tr): say(f'  would save {f.name}: {f.stat().st_size:,} bytes')
        else:
            M.save_area(area, out, root, key_dir=key_dir)
            for f in M.area_files(area, root): say(f'  saved {f.name}: {f.stat().st_size:,} bytes')
        if drop_pin: say(f'  dropped {len(drop_pin)} PIN outline(s): {" ".join(sorted(drop_pin)[:8])}')
        if drop_unk: say(f'  dropped {len(drop_unk)} outline(s) not in any key: {" ".join(sorted(drop_unk)[:8])}')
        if drop_fresh: say(f'  dropped {len(drop_fresh)} old outline(s) of parks joined to fresh store records that could not be cut from the store: {" ".join(sorted(drop_fresh)[:8])}')
        if replaced: say(f'  rebuilt {len(replaced)} outline(s) to match the key: {" ".join(replaced[:8])}')
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
    key_dir = root.parent / 'us-key'
    pins = M.pin_drops(area, before, key_dir) | M.not_in_key_drops(area, before, key_dir)
    changed = sorted(r for r in before if r in now and now[r].get('hash') != before[r].get('hash'))
    lost = sorted(set(before) - set(now) - pins)
    files = M.area_files(area, root); big = [f.name for f in files if f.stat().st_size > M.PART_CAP]
    bad_hash = sorted(r for r, v in now.items() if M.content_hash(v) != v.get('hash'))
    lines = [f'{area}: {len(before)} outline(s) at {ref}, {len(now)} now ({len(set(now) - set(before))} new, {len(set(before) & pins)} dropped as pin or not in the key)',
             *(f'  {f.name}: {f.stat().st_size:,} bytes' for f in files),
             f'  changed: {" ".join(changed) or "none"}; lost: {" ".join(lost) or "none"}; over 1 MB: {" ".join(big) or "none"}; bad hash: {" ".join(bad_hash) or "none"}']
    return not (changed or lost or big or bad_hash), lines


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument('--cache'); ap.add_argument('--states', required=True)
    ap.add_argument('--only-refs', nargs='*'); ap.add_argument('--dry-run', action='store_true'); ap.add_argument('--root')
    ap.add_argument('--key', help='the us-key folder (default data/us-key)'); ap.add_argument('--verify', action='store_true'); ap.add_argument('--ref', default='HEAD')
    ap.add_argument('--store', help="the outline store's results\\store folder (US-XX.kpcstore.json.gz): fresh store records are cut from it")
    a = ap.parse_args(argv)
    if a.verify:
        ok = True
        for st in a.states.replace(',', ' ').split():
            good, lines = verify(st, a.ref, a.root); ok = ok and good; print('\n'.join(lines)); print(f'US-{st}: ' + ('OK' if good else 'PROBLEM'))
        return 0 if ok else 1
    if not a.cache: ap.error('--cache is needed (the folder that holds US-XX.json.gz)')
    held = []
    for st in a.states.replace(',', ' ').split():
        added, skipped = build_state(st, a.cache, set(a.only_refs or []) or None, a.dry_run, a.root, a.key, store=a.store or os.environ.get('KPC_STORE_DIR'))
        if any(r == '*' for r, _w in skipped):
            held.append(st); print(f'US-{st}: HELD: ' + next(w for r, w in skipped if r == '*')); continue
        print(f'US-{st}: {len(added)} outline(s) {"would be " if a.dry_run else ""}added; {len(skipped)} skipped'
              + ''.join(f'\n  skipped {r}: {w}' for r, w in skipped))
    if held:   # M1: exit 3 = the outline file of these states is as it was (kpc-us-key.yml says so; the sync marks them HELD)
        print(f'HELD (no outline store file for fresh store records): {" ".join(held)}')
        return 3
    return 0


if __name__ == '__main__': sys.exit(main())
