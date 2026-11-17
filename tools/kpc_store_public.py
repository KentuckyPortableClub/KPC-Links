#!/usr/bin/env python3
"""kpc_store_public.py: the PUBLIC SHELF of the outline store (KPC owner, 2026-11-16; Fable's brief of the same night).

Plain words
-----------
The outline store (KPC-Store, branch store-data, private) holds every record of every park at full detail, held ones too.
This tool copies the CLEAN part of it out: for each area it writes a new index-<AREA>.json + <AREA>.kpcstore.json.gz in the
SAME store format, holding only what a PUBLIC run of the 2-fer bot is allowed to read. The private store is never changed;
the public shelf is rebuilt from it, so a layer whose terms are confirmed later simply appears on the next build, and a
layer that turns out restricted simply drops off. Nothing is moved between the two.

ONE GATE. Every record is judged by kpc_display_copy.gate() and kpc_display_copy.view_of() - the same gate the public map's
display copy already uses. There is no second set of licence rules here.

A PARK PASSES WHOLE OR NOT AT ALL. A park is put on the shelf with EXACTLY the records a public run of the full store would
read (all of them for a park_publishable park; the records of its public view for a held park with a valid full or partial
view) and only when every one of those records passes the gate. Anything else - a record the gate refuses, a view that names
a record the park does not have, a checksum that does not match, a park with no public view - and the park is left off the
shelf entirely. It is never trimmed into a shape the reader did not expect, because the reader's "no record X for REF"
answer would then name it.

A PARK THAT IS NOT ON THE SHELF IS NEVER NAMED. The shelf index carries "shelf": "public". The 2-fer bot's store reader
(kpc_fers_store.py) treats a park it cannot find on a public shelf as held privately ("needs the private store"), exactly as
it treats a held park when it reads the full store: its rows of the previous public file are carried unchanged and nothing
names it. So the shelf never lists the parks it leaves out, and neither does the bot.

LEAST SURFACE. A record keeps only the fields the reader and the gate read (REC_KEEP); a park only PARK_KEEP; an index entry
only ENTRY_KEEP, with its per-record dicts cut down to the records kept; the index layer table only the layers of kept
records and only LAYER_KEEP. Source attributes, owner names, the request URL, private reasons and the terms-text file are
never copied.

Partial parks (owner decision 2026-11-15 23:08: a partial 2-fer is better than none, marked partial boundary) keep their
view fields exactly, so the reader still marks every row that uses them partial boundary.

  build --store DIR --area US-RI [--area ...] --out DIR [--report FILE]
  check --out DIR --area US-RI [...]       re-reads the shelf and refuses it if any record on it is not public
"""
import argparse, collections, gzip, hashlib, json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kpc_display_copy as DC  # noqa: E402  (the one licence gate)

SHELF = 'public'
SHELF_FORMAT = 'kpc-store-public-shelf/1'

# What the 2-fer bot's reader (kpc_fers_store.py) and the gate actually read. Nothing else is copied.
REC_KEEP = ('key', 'rings', 'sha256', 'points', 'geometry_kind', 'boundary_kind', 'lines', 'line_sha256', 'line_points',
            'line_extent', 'publishable', 'licence_class', 'publish_basis', 'credit_line', 'wdpa_derived',
            'use', 'use_why', 'record_name', 'source_layer', 'source_url', 'layer_url', 'boundary_rule', 'corridor_ft',
            'corridor_from', 'bank_status', 'bank_ok', 'bank_missing', 'river_class', 'len_m', 'km', 'read', 'q', 'source')
PARK_KEEP = ('ref', 'name', 'grade', 'grade_today', 'circle', 'geometry_kind', 'pin', 'publish_view', 'publish_view_records',
             'publish_view_basis', 'publish_view_ratio')
ENTRY_KEEP = ('file', 'grade', 'circle', 'date', 'geometry_kind', 'park_public', 'park_publishable', 'publish_view',
              'publish_view_records', 'publish_view_basis', 'publish_view_ratio')
ENTRY_PER_RECORD = ('licence', 'licence_class', 'credit', 'publishable')
META_KEEP = ('geometry_kind', 'boundary_kind', 'publishable', 'licence_class', 'publish_basis', 'credit_line', 'source_layer',
             'source_url', 'wdpa_derived')
LAYER_KEEP = ('layer', 'address', 'publishable', 'class', 'credit')
# Never on the shelf, whatever else changes (the push check's private fields and the store's own private notes).
NEVER = frozenset({'private_reason', 'terms_text_file', 'terms_text_sha256', 'attributes', 'attrs', 'owner', 'request',
                   'source_detail', 'credit_detail', 'licence_from', 'publish_why', 'note', 'join', 'record_id',
                   'record_name_in_source', 'tract_name', 'agency_label', 'finer_than_6_decimals', 'same_geometry_as',
                   'publish_basis_detail'})


# A record's 'source' is kept because the reader reads it ('nhd-by-name' = a river line found by name: the park may be only a stretch
# of it, so its line is skipped), but only as one plain lower-case word: the store's values are 'live', 'have-line', 'nhd-by-name'.
SOURCE_RX = re.compile(r'[a-z][a-z0-9-]{0,30}')


class ShelfError(Exception):
    pass


def _gz_member(text):
    return gzip.compress(text.encode('utf-8'), 9, mtime=0)


def _keep(d, keys):
    out = {k: d[k] for k in keys if k in d}
    assert not (set(out) & NEVER), sorted(set(out) & NEVER)
    return out


def readable_keys(e, park):
    """The record keys a PUBLIC run of the full store would read for this park, or None when it would read none."""
    if e.get('park_publishable') is True: return [r['key'] for r in park.get('records') or []]
    if 'park_public' not in e: return None            # a store before core 3.6.3: never on a public shelf (fail closed)
    if DC.view_of(e, park): return list(e.get('publish_view_records') or [])
    return None


def public_park(ref, e, park, bad, n_bad, layers):
    """-> (public park, public entry fields) or (None, why). Whole park or nothing."""
    if bad or n_bad: return None, 'a record failed its checksum'
    want = readable_keys(e, park)
    if not want: return None, 'no public view'
    by = {r['key']: r for r in park.get('records') or []}
    if any(k not in by for k in want): return None, 'its view names a record the park does not have'
    kept = []
    for k in want:
        r = dict(by[k])
        ok, why, _ = DC.gate(r, e, layers)
        if not ok: return None, 'a record it needs did not pass the gate'
        if r.get('rings') is None and r.get('same_geometry_as'):   # the same rings as another record: copy them in
            src = by.get(r['same_geometry_as'])
            if not src or src.get('rings') is None: return None, 'a record shares the rings of a record the park does not have'
            if DC.geometry_sha256(src['rings']) != r.get('sha256'): return None, 'a shared ring set does not match its checksum'
            r['rings'] = src['rings']
        pr = _keep(r, REC_KEEP)
        if not (isinstance(pr.get('source'), str) and SOURCE_RX.fullmatch(pr['source'])): pr.pop('source', None)   # plain words only
        kept.append(pr)
    pk = _keep(park, PARK_KEEP); pk['records'] = kept
    meta = e.get('record_meta') or {}
    ent = _keep(e, ENTRY_KEEP)
    ent['records'] = [r['key'] for r in kept]
    ent['points'] = sum(int(r.get('points') or 0) for r in kept)
    ent['fp'] = hashlib.sha256('|'.join(str(r.get('sha256')) for r in kept).encode()).hexdigest()
    ent['record_meta'] = {r['key']: _keep(meta[r['key']], META_KEEP) for r in kept}
    for f in ENTRY_PER_RECORD:
        if isinstance(e.get(f), dict): ent[f] = {r['key']: e[f][r['key']] for r in kept if r['key'] in e[f]}
    return (pk, ent), ''


def build_area(store_dir, area, out_dir):
    idx, _ = DC.read_index(store_dir, area)
    DC.require_public_index(idx, area)
    layers = idx.get('layers') if isinstance(idx.get('layers'), dict) else {}
    handles, rows, why = {}, [], collections.Counter()
    try:
        for ref, e in sorted((idx.get('parks') or {}).items(), key=lambda kv: (str(kv[1].get('file')), int(kv[1].get('o') or 0))):
            try: park, bad, n_bad = DC.read_park(store_dir, ref, e, handles)
            except DC.DisplayError: why['the park failed its check'] += 1; continue
            got, w = public_park(ref, e, park, bad, n_bad, layers)
            if got is None: why[w] += 1; continue
            rows.append((ref, got[0], got[1]))
    finally:
        for f in handles.values(): f.close()
    store_name = f'{area}.kpcstore.json.gz'
    head = {'kpcstore': 1, 'area': area, 'shelf': SHELF, 'shelf_format': SHELF_FORMAT, 'made': idx.get('made'),
            'tool': idx.get('tool'), 'about': 'KPC outline store, PUBLIC SHELF: only records that passed the licence gate '
            '(tools/kpc_display_copy.py gate). Same format as the private store; parks not on it are never named.'}
    blob = bytearray(_gz_member(json.dumps(head, separators=(',', ':'))[:-1] + ',"parks":[\n'))
    entries = {}
    for i, (ref, pk, ent) in enumerate(rows):
        m = _gz_member(('' if i == 0 else ',\n') + json.dumps(pk, separators=(',', ':')))
        ent = dict(ent, file=store_name, o=len(blob), n=len(m)); entries[ref] = ent; blob += m
    blob += _gz_member('\n]}\n')
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / store_name).write_bytes(bytes(blob))
    used = {DC.norm_layer_url(r.get('source_url') or r.get('layer_url')) for _, pk, _ in rows for r in pk['records']}
    lay = {k: _keep(v, LAYER_KEEP) for k, v in layers.items() if DC.norm_layer_url(k) in used and isinstance(v, dict)}
    n_rec = sum(len(pk['records']) for _, pk, _ in rows)
    pidx = {k: idx[k] for k in ('format', 'store_format_version', 'geometry_kinds', 'licence_classes', 'made', 'tool') if k in idx}
    pidx.update({'area': area, 'shelf': SHELF, 'shelf_format': SHELF_FORMAT,
                 'about': 'PUBLIC SHELF of the KPC outline store (tools/kpc_store_public.py): only parks whose every needed record '
                          'passed the licence gate. A park not listed here is held privately and is never named.',
                 'files': {store_name: {'bytes': len(blob), 'sha256': hashlib.sha256(bytes(blob)).hexdigest(),
                                        'parks': len(rows), 'records': n_rec,
                                        'points': sum(e['points'] for e in entries.values()), 'circles': 0,
                                        'date': (idx.get('files') or {}).get(store_name, {}).get('date')}},
                 'parks': entries, 'layers': lay,
                 # KPC owner, 2026-11-17: how much of the area the shelf holds. The 2-fer bot reads this and leaves a THIN area on the
                 # old path by itself (kpc_fers_store.THIN_SHELF), so no hand-kept list has to be edited as licences are confirmed.
                 'coverage': {'parks_in_store': len(idx.get('parks') or {}), 'parks_on_shelf': len(rows),
                              'share': round(len(rows) / max(1, len(idx.get('parks') or {})), 4)},
                 'publishable_rule': 'every record here passed tools/kpc_display_copy.py gate(); a park is here whole or not at all'})
    (out / f'index-{area}.json').write_text(json.dumps(pidx, separators=(',', ':'), sort_keys=True), encoding='utf-8')
    # The report counts only: it never names a park that was left off.
    return {'area': area, 'parks_in': len(idx.get('parks') or {}), 'parks_on_shelf': len(rows), 'records_on_shelf': n_rec,
            'left_off': dict(why)}


def check_area(out_dir, area):
    """Refuses the shelf for one area if anything on it is not public. Raises ShelfError."""
    out = pathlib.Path(out_dir)
    idx = json.loads((out / f'index-{area}.json').read_text(encoding='utf-8'))
    if idx.get('shelf') != SHELF: raise ShelfError(f'{area}: the index does not say it is the public shelf')
    DC.require_public_index(idx, area)
    for name, m in (idx.get('files') or {}).items():
        if DC.file_sha256(out / name) != m.get('sha256'): raise ShelfError(f'{area}: {name} does not match its checksum')
    layers = idx.get('layers') or {}
    handles, n = {}, 0
    try:
        for ref, e in (idx.get('parks') or {}).items():
            park, bad, n_bad = DC.read_park(out, ref, e, handles)
            if bad or n_bad: raise ShelfError(f'{area}: a park on the shelf fails its checksum')
            if [r['key'] for r in park['records']] != list(e.get('records') or []): raise ShelfError(f'{area}: index and park disagree')
            for blob in [park, e] + [m for m in (e.get('record_meta') or {}).values() if isinstance(m, dict)]:
                hit = NEVER & set(blob)
                if hit: raise ShelfError(f'{area}: a private field is on the shelf: {sorted(hit)}')
            for r in park['records']:
                hit = NEVER & set(r)
                if hit: raise ShelfError(f'{area}: a private field is on the shelf: {sorted(hit)}')
                ok, why, _ = DC.gate(r, e, layers)
                if not ok: raise ShelfError(f'{area}: a record on the shelf does not pass the gate ({why})')
                n += 1
            if e.get('park_publishable') is not True and not DC.view_of(e, park):
                raise ShelfError(f'{area}: a held park on the shelf has no valid public view')
    finally:
        for f in handles.values(): f.close()
    return n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build'); b.add_argument('--store', required=True); b.add_argument('--area', action='append', required=True)
    b.add_argument('--out', required=True); b.add_argument('--report')
    c = sub.add_parser('check'); c.add_argument('--out', required=True); c.add_argument('--area', action='append', required=True)
    a = ap.parse_args(argv)
    if a.cmd == 'build':
        rep = []
        for ar in a.area:
            rep.append(build_area(a.store, ar, a.out)); check_area(a.out, ar)
            r = rep[-1]; print(f"{ar}: {r['parks_on_shelf']} of {r['parks_in']} parks on the public shelf ({r['records_on_shelf']} records); "
                               f"left off: {sum(r['left_off'].values())}", flush=True)
        if a.report: pathlib.Path(a.report).write_text(json.dumps(rep, indent=1), encoding='utf-8')
        return 0
    for ar in a.area:
        print(f'{ar}: {check_area(a.out, ar)} records, every one passes the gate')
    return 0


if __name__ == '__main__':
    try: sys.exit(main())
    except (ShelfError, DC.DisplayError) as e:
        print(f'STOP: {e}: nothing published', file=sys.stderr); sys.exit(1)
