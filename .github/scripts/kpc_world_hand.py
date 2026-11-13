#!/usr/bin/env python3
"""Owner world hand files -> W-XX saved-copy records. NOT a rule file: it does not decide a join.

A hand-W-XX.<layer>.geojson.gz file is turned into the same record shape the world key saves
(id, n, ty, src, _bb, _r, _a, code, dc, sid) and keep-bigger merged into cache/world/W-XX.json.gz
by source id (kind, address, where), then by a unique source label. The world key itself is not
imported (its module body would run the key). thin / bbox / rings_of match kpc_world_key.py so
pin-inside stays consistent. Degenerate rings (no area, e.g. a WGS84 read with
maxAllowableOffset=5 degrees) are dropped, not stored or counted. A saved record with no
_bb and no _r, or a zero-area ring, does not count toward the copy's baseline (Quality #179 M4). Two layers that share a
site_code (Malta N2K SAC + SPA) are kept as separate sources; the saved copy is not pre-deduped
(the world key's own site_code handling stays in the key).
"""
import json, os, pathlib, re

import kpc_master as M

# Same formulas as kpc_world_key.py (DETAIL / THIN_N / rings_of / bbox / thin). Kept here so this
# module never imports the world key.
DETAIL = float(os.environ.get('GEO_DETAIL') or 0.01)
THIN_N = int(os.environ.get('GEO_THIN') or 60)
NAMEF = ['nom_site', 'leg_name', 'nazwa', 'NAME', 'Name', 'name', 'NNR_NAME', 'LNR_NAME', 'CP_NAME',
         'SSSI_NAME', 'PA_NAME', 'NAME_E', 'NAME_EN', 'SITE_NAME', 'sitename', 'NAMEX', '名称', '公園名',
         'nombre', 'NOMBRE', 'nombre_ap', 'NOMBRE_AP', 'nom_ap', 'NOM_AP', 'CUR_NME', 'cur_nme', 'PA_NAME',
         'NAZEV', 'Gebietsname', 'site_name']
TYPEF = ['TYPE', 'Type', 'type', 'PA_TYPE', 'DESIGNATION', 'desig', 'GAZ_TYPE', 'KIND', '種別', 'TYPE_E',
         'site_type', 'Schutzgebietstyp', 'KAT']


def rings_of(g):
    if not g:
        return []
    if 'rings' in g:
        return g['rings']
    t, c = g.get('type'), g.get('coordinates') or []
    if t == 'Polygon':
        return c
    if t == 'MultiPolygon':
        return [r for p in c for r in p]
    return []


def bbox(rs):
    xs = [p[0] for r in rs for p in r if len(p) >= 2]
    ys = [p[1] for r in rs for p in r if len(p) >= 2]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


def thin(rs, n=None):
    n = n or THIN_N
    return [r[::max(1, len(r) // n)] for r in rs]


def _unique_pts(ring):
    seen, out = set(), []
    for p in ring or []:
        if len(p) < 2:
            continue
        k = (round(float(p[0]), 7), round(float(p[1]), 7))
        if k not in seen:
            seen.add(k)
            out.append(p)
    return out


def degenerate(rs):
    """True when no ring has three distinct points, or every point is an integer-degree
    coordinate (a WGS84 read with maxAllowableOffset=5 collapses to 1-degree boxes that
    would false-match pin-inside)."""
    useful = []
    for r in (rs or []):
        u = _unique_pts(r)
        if len(u) < 3:
            continue
        if all(float(p[0]) == int(p[0]) and float(p[1]) == int(p[1]) for p in u if len(p) >= 2):
            continue
        useful.append(u)
    return not useful


def pick(a, names):
    for n in names:
        for k in a:
            if k.lower() == n.lower() and a[k] not in (None, ''):
                return str(a[k])
    return ''


def pick_name(a, name_field=''):
    if name_field:
        v = pick(a, [name_field])
        if v:
            return v
    v = pick(a, NAMEF)
    if v:
        return v
    for k in a:
        if re.search(r'name|enw|nombre|_nme$', k, re.I) and not re.search(r'welsh|cymraeg|_cy$|^cy_|enw', k, re.I) and a[k] not in (None, ''):
            return str(a[k])
    return ''


def oid_of(a):
    for k in ('OBJECTID', 'objectid', 'FID', 'fid', 'OID', 'oid', 'OBJECTID_1'):
        if a.get(k) not in (None, ''):
            return a[k]
    return None


def src_id(url, where=None):
    """Same id the world key uses: repr((kind, address, layer)). Extra and sheet layers have no where."""
    return repr(('arcgis', str(url or '').rstrip('/'), where))


def rec_from_feature(feat, label, url, name_field=''):
    a = dict(feat.get('properties') or {})
    a.pop('_kpc', None)
    rs = rings_of(feat.get('geometry'))
    if degenerate(rs):
        bb, th = None, []
    else:
        bb, th = bbox(rs), thin(rs)
    return {
        'id': oid_of(a),
        'n': pick_name(a, name_field),
        'ty': pick(a, TYPEF),
        'src': label,
        '_bb': bb,
        '_r': th,
        '_a': a,
        'code': pick(a, ['SITECODE', 'nationalId', 'site_code', 'siteid']),
        'dc': pick(a, ['designationTypeCode', 'SITETYPE', 'site_type', 'KAT']),
        'sid': src_id(url),
    }


HAND_CHUNK_RE = re.compile(
    r'^hand-(US-[A-Z]{2}|CA-[A-Z]{2,3}|W-[A-Z]{2})\.(\w+)\.chunk(\d+)\.geojson(?:\.gz)?$',
    re.ASCII)
# Inbox-style owner downloads (e.g. CZ-Natura2000-layer1-EVL-chunk01.geojson).
INBOX_CHUNK_RE = re.compile(r'(?i)(?:^|/)(?:hand-)?(?:W-)?([A-Z]{2}).*?(?:layer[_-]?(\w+).*?)?chunk[_-]?0*(\d+)\.(?:geojson|json)(?:\.gz)?$')


def rec_has_geometry(r):
    """Usable for a count or a pin-inside: has a bbox or at least one stored ring.
    A stored world record with `_bb` / `_r` keys that are empty is not counted (Quality #179 M4).
    A fixture or older rec that has neither key is counted as before."""
    if not r:
        return False
    if '_bb' not in r and '_r' not in r:
        return True
    if r.get('_bb'):
        return True
    return bool(r.get('_r'))


def recs_from_hand(path):
    """(meta, recs) for a checked hand-W-XX.<layer>.geojson.gz file.
    Features with no usable geometry (no _bb / _r after degenerate()) are omitted."""
    meta, feats = M.read_layer_file(path)
    label = str(meta.get('label') or '')
    url = str(meta.get('url') or '')
    nf = str(meta.get('name_field') or '')
    recs = []
    for f in feats:
        rec = rec_from_feature(f, label, url, nf)
        if rec_has_geometry(rec):
            recs.append(rec)
    return meta, recs


def _read_geojson_any(path):
    path = pathlib.Path(path)
    try:
        return M.read_layer_file(path)
    except Exception:
        pass  # noqa: BLE001
    raw = path.read_bytes()
    if path.name.endswith('.gz') or raw[:2] == b'\x1f\x8b':
        import gzip
        raw = gzip.decompress(raw)
    data = json.loads(raw.decode('utf-8'))
    if isinstance(data, dict) and 'features' in data:
        return dict(data.get('properties') or data.get('meta') or {}), list(data.get('features') or [])
    if isinstance(data, list):
        return {}, data
    return {}, []


def merge_geojson_chunks(paths):
    """Concatenate features from one layer's chunk files. Shared meta is kept; count is the sum."""
    paths = [pathlib.Path(p) for p in paths]
    if not paths:
        return {}, []
    paths = sorted(paths, key=lambda p: p.name)
    meta, feats = {}, []
    for p in paths:
        m, f = _read_geojson_any(p)
        if not meta:
            meta = dict(m or {})
        feats.extend(f or [])
    meta = dict(meta)
    meta['chunks'] = [p.name for p in paths]
    meta['count'] = len(feats)
    meta['count_expected'] = len(feats)
    return meta, feats


def parse_hand_chunk_name(name):
    m = HAND_CHUNK_RE.match(os.path.basename(str(name or '')))
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    return None


def discover_hand_chunks(directory, area=None, layer=None):
    """Group hand-W-XX.<layer>.chunkN.geojson.gz files. Returns {(area, layer): [paths]}."""
    d = pathlib.Path(directory)
    groups = {}
    if not d.is_dir():
        return groups
    for p in sorted(d.iterdir()):
        got = parse_hand_chunk_name(p.name)
        if not got:
            continue
        a, lyr, _n = got
        if area and a != area:
            continue
        if layer and lyr != layer:
            continue
        groups.setdefault((a, lyr), []).append(p)
    return groups


def write_merged_chunks(paths, dest, meta_extra=None):
    """Write a combined hand-W-XX.<layer>.geojson.gz from chunk files. Returns dest."""
    meta, feats = merge_geojson_chunks(paths)
    if meta_extra:
        meta.update(meta_extra)
    meta['count'] = len(feats)
    meta['count_expected'] = len(feats)
    dest = pathlib.Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    M.write_layer_file(dest, meta, feats) if hasattr(M, 'write_layer_file') else _write_hand(dest, meta, feats)
    return dest


def _write_hand(dest, meta, feats):
    import gzip
    body = json.dumps({'type': 'FeatureCollection', 'features': feats, **({'meta': meta} if meta else {})},
                      ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    # Prefer the same on-disk shape as packed hand files when pack helpers exist.
    try:
        M.write_gz_json(dest, {'type': 'FeatureCollection', 'features': feats, 'meta': meta})
        return
    except Exception:
        pass  # noqa: BLE001
    with gzip.open(dest, 'wt', encoding='utf-8') as f:
        # packed files store [meta, features]
        json.dump([meta, feats], f, ensure_ascii=False, separators=(',', ':'))


def hand_licence_text(meta):
    for k in ('license', 'licence', 'terms'):
        v = str((meta or {}).get(k) or '').strip()
        if v:
            return v
    return ''


def hand_merge_blocked(path, meta=None, root=None):
    """Why this hand file must not merge: share_block / WDPA flag, or no licence or terms recorded."""
    path = pathlib.Path(path)
    meta = dict(meta or {})
    root = pathlib.Path(root) if root else None
    why = M.share_block(meta, root)
    if why:
        return why
    if M.hand_file_problem(path, *(M.parse_hand_name(path.name) or ('', ''))) if path.name else None:
        # share/WDPA already covered; keep the message when it is a WDPA / flag problem
        pass
    if not hand_licence_text(meta):
        return f'{path.name}: no licence or terms recorded; not merged'
    return ''


def _old_recs(recs, sid, src):
    """The saved records of this one source: by sid first, else by a unique label when no sid is stored."""
    if sid:
        old = [r for r in recs if r.get('sid') == sid]
        if old:
            return old
        if src and all((r.get('sid') in (None, '') for r in recs if r.get('src') == src)):
            return [r for r in recs if r.get('src') == src]
        return []
    return [r for r in recs if r.get('src') == src]


def merge_world_saved_layer(blob, new_recs):
    """Keep-bigger merge of one world source into a saved copy blob {'recs': [...]}.
    Matching is by sid when the new records have one, else by a unique source label.
    A smaller re-read never replaces a saved layer. Returns (blob, what)."""
    import datetime
    recs = list(blob.get('recs') or [])
    if not new_recs:
        return blob, 'no new records'
    sid = next((r.get('sid') for r in new_recs if r.get('sid')), None)
    src = next((r.get('src') for r in new_recs if r.get('src')), None)
    old = _old_recs(recs, sid, src)
    tag = src or sid or 'layer'
    if len(new_recs) < len(old):
        return blob, f'kept the saved {tag} ({len(old)} records; the new read has {len(new_recs)})'
    if len(new_recs) == len(old) and old == []:
        return blob, f'{tag} unchanged (0)'
    old_ids = {id(r) for r in old}
    blob = dict(blob, recs=[r for r in recs if id(r) not in old_ids] + list(new_recs),
                saved=datetime.date.today().isoformat())
    return blob, f'{tag}: {len(old)} -> {len(new_recs)} records'


def apply_world_hand_file(path, cache, root=None):
    """Merge one owner world hand file into cache/W-XX.json.gz. Returns (ok, what).

    Refuses a file that share_block / WDPA flags, or that has no licence or terms on its
    meta. The caller (fill) must also run check_other first and only call this when that
    check passed. Degenerate / no-geometry records are not merged.
    """
    path = pathlib.Path(path)
    got = M.parse_hand_name(path.name)
    if not got or not got[0].startswith('W-'):
        return False, f'{path.name}: not a world hand file'
    area, layer = got
    why = M.hand_file_problem(path, area, layer)
    if why:
        return False, why
    meta, new = recs_from_hand(path)
    blocked = hand_merge_blocked(path, meta, root)
    if blocked:
        return False, blocked
    cp = pathlib.Path(cache) / f'{area}.json.gz'
    if not cp.exists():
        return False, f'{area}: no saved copy to merge into (the gate holds it)'
    blob = M.load_saved(cp)
    blob2, what = merge_world_saved_layer(blob, new)
    if blob2 is not blob:
        M.save_saved(cp, blob2)
    return True, f'{area} {what}'


def _world_label_sets(cc, root=None):
    """(current labels, dropped labels) the world key records for one country. Does not import kpc_world_key.py."""
    root = pathlib.Path(root or pathlib.Path(__file__).resolve().parent.parent.parent)
    cc = str(cc or '').upper()
    labels, dropped = [], set()
    try:
        at = json.loads((root / 'data/world-key/area-tables.json').read_text(encoding='utf-8'))
        for s in (at.get('SRC') or {}).get(cc) or []:
            if isinstance(s, (list, tuple)) and s:
                labels.append(str(s[0]))
        split = (at.get('SPLIT_LAYERS') or {}).get(cc) or {}
        split_urls = {str(u).rstrip('/').lower() for u in (split.get('layers') or [])}
        rest_where = split.get('rest_where')
    except Exception:
        at, split_urls, rest_where = {}, set(), None  # noqa: BLE001
    try:
        ex = json.loads((root / 'data/world-key/extra-layers.json').read_text(encoding='utf-8'))
        for L in (ex.get('dropped') or {}).get(cc) or []:
            if isinstance(L, dict) and L.get('label'):
                dropped.add(str(L['label']))
        have = set(labels)
        for L in (ex.get('countries') or {}).get(cc) or []:
            if not isinstance(L, dict):
                continue
            lab = str(L.get('label') or '')
            u = str(L.get('url') or '').rstrip('/').lower()
            if lab and u and u in split_urls and not L.get('where') and rest_where:
                labels.append(lab)
            elif lab and lab not in have and u:
                labels.append(lab)
                have.add(lab)
    except Exception:
        pass  # noqa: BLE001
    try:
        sc = json.loads((root / 'data/world-key/sheet-countries.json').read_text(encoding='utf-8'))
        countries = sc.get('countries') if isinstance(sc.get('countries'), dict) else sc
        row = (countries or {}).get(cc) or {}
        have = set(labels)
        for L in row.get('layers') or []:
            if isinstance(L, dict) and L.get('label') and str(L['label']) not in have:
                labels.append(str(L['label']))
                have.add(str(L['label']))
    except Exception:
        pass  # noqa: BLE001
    current = [x for x in labels if x not in dropped]
    return current, dropped


def world_source_labels(cc, root=None):
    """The source labels the world key currently reads for one country: built-in SRC, plus extra-layers.json
    (a split layer also adds its rest_where entry), minus extra-layers.json 'dropped'. Used by the gate and
    save-check so a saved copy is not compared with layers the key no longer reads (W-AU: Surface_HydroLines_National
    and the other #135 drops). Lives here, not in kpc_master.py, because that module is a READER input of every
    area hash: editing it would move every US / CA / world area. Does not import kpc_world_key.py."""
    return _world_label_sets(cc, root)[0]


def world_current_rec_count(name, blob, root=None):
    """Record count a W-XX saved copy is checked against: only records whose src is a layer the world key still reads.
    US / CA copies, and a world copy whose source list cannot be read, use the full recs list.
    A copy whose src labels are not in the current or dropped key lists (test fixtures, unlabeled recs)
    is also counted in full, so the filter only applies to a real world-key saved copy."""
    recs = (blob or {}).get('recs') if isinstance((blob or {}).get('recs'), list) else []
    stem = str(name or '')
    if stem.endswith('.json.gz'):
        stem = stem[:-len('.json.gz')]
    if not stem.startswith('W-') or len(stem) != 4:
        # Nov 13 (KPC owner): a US / CA copy is counted in FULL, as this docstring says and as its baseline was recorded
        # (layers.json caches, e.g. CA-ALL 60,426 on Nov 11 = every record). The no-outline filter below is for world copies
        # only: applied here it dropped CA-ALL's 475 records that are official point sites with no outline (Quebec heritage
        # sites), so a complete copy of 60,479 records counted as 60,004 and the master gate held every Canada build as SHORT.
        return len(recs)
    recs = [r for r in recs if rec_has_geometry(r)]
    current, dropped = _world_label_sets(stem[2:], root)
    if not current:
        return len(recs)
    srcs = {(r.get('src') or '') for r in recs if r.get('src')}
    if not srcs or not (srcs & (set(current) | dropped)):
        return len(recs)
    return sum(1 for r in recs if (r.get('src') or '') in set(current))
