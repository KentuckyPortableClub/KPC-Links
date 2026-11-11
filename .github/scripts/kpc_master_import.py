#!/usr/bin/env python3
"""kpc_master_import.py (Nov 10): `kpc_master_cli.py import-existing` - take in the downloads a person already made, BEFORE anyone is
asked for anything. Run on the box (the files never go in a repo).

  1. The inventory: the hand map (layer address -> file), the downloads table (DOWNLOADS.md), the Drive index (INDEX.md) and the
     research inbox. Every file that a needs row (or a hand-map layer) points at gets a raw-add row in data/outlines/raw-manifest.json:
     name, size, sha256, date, source address and record count. Facts only: no licence or terms text.
  2. The needs list is rebuilt: the hand-filled source list (seed, checked against the saved copies US-XX / CA-ALL / W-XX by layer
     id and source label), plus the master step's rows; a row whose layer an existing download covers is DONE (source 'existing
     download'). A done row is never asked again until the change check sees its source change.
  3. Checked hand files for the rows whose records are only in a box file (--box-only, a box-side list): US rows through the PC
     helper's check_and_pack (state box, fail closed, trim dry run); Canada rows as hand-CA.<name>.geojson.gz (the Canada key merges
     them, KPC_CA_HAND); world rows as hand-W-XX.<layer>.geojson.gz. Uploading them is a separate, explicit step (--upload).
Nothing here makes a network request except --upload (gh release upload to the boundary-cache release).
"""
import datetime, gzip, json, os, pathlib, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpc_master as M  # noqa: E402

GIS_EXT = ('.geojson', '.json', '.zip', '.shp', '.gpkg', '.kml', '.kmz', '.gdb')
WHY_EXISTING = 'an existing download covers this layer (raw facts in data/outlines/raw-manifest.json); a change at the source reopens it'


def norm_url(u): return re.sub(r'/query/?$', '', str(u or '').replace('svc:', '', 1).split('|')[0].split('?')[0]).rstrip('/').lower()


def real_path(p):
    """'/vsizip//a/b.zip/inner' -> /a/b.zip (the file on disk)."""
    s = str(p or '')
    if s.startswith('/vsizip/'):
        s = s[len('/vsizip/'):].lstrip('/'); s = '/' + s
        m = re.match(r'(.*?\.zip)(/.*)?$', s)
        if m: s = m.group(1)
    return pathlib.Path(s)


def md_table_files(md_path, base):
    """The file column of every markdown table row in md_path -> [(path, label text of the row)], only files that exist."""
    out = []
    try: txt = pathlib.Path(md_path).read_text(encoding='utf-8')
    except Exception: return out  # noqa: BLE001
    for line in txt.splitlines():
        if not line.startswith('|') or set(line.replace('|', '').strip()) <= set('-: '): continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        for c in cells:
            for f in re.findall(r'`([^`]+)`', c) or ([c] if c.lower().endswith(GIS_EXT) else []):
                p = pathlib.Path(f) if f.startswith('/') else pathlib.Path(base) / f
                if (p.is_file() and p.suffix.lower() in GIS_EXT + ('',)) or (p.is_dir() and p.suffix.lower() == '.gdb'):
                    out.append((p, ' '.join(cells)))
    return out


def count_features(p):
    """Record count of a GIS file, when cheap to read (GeoJSON / Esri JSON; shapefile / gdb zips with pyogrio if installed)."""
    p = pathlib.Path(p)
    try:
        if p.suffix.lower() in ('.geojson', '.json') or not p.suffix:
            d = json.loads(p.read_text(encoding='utf-8-sig'))
            fs = d.get('features') if isinstance(d, dict) else d
            return len(fs) if isinstance(fs, list) else None
        import pyogrio  # noqa: F401  (box only)
        src = f'/vsizip/{p}' if p.suffix.lower() == '.zip' else str(p)
        return sum(int(pyogrio.read_info(src, layer=str(l[0]))['features']) for l in pyogrio.list_layers(src))
    except Exception: return None  # noqa: BLE001


def facts(p, source, count=None):
    p = pathlib.Path(p)
    if p.is_dir():
        files = sorted(x for x in p.rglob('*') if x.is_file()); size = sum(x.stat().st_size for x in files)
        sha = M.hashlib.sha256(''.join(M.sha256_file(x) for x in files).encode()).hexdigest(); mt = max((x.stat().st_mtime for x in files), default=0)
    else: size, sha, mt = p.stat().st_size, M.sha256_file(p), p.stat().st_mtime
    return {'name': p.name, 'size': size, 'sha256': sha, 'source': source, 'date': datetime.date.fromtimestamp(mt).isoformat(),
            'count': count if count is not None else count_features(p)}


def inventory(hand_map=None, downloads_md=None, drive_index=None, research=None):
    """-> {'by_url': {layer address: [file]}, 'files': [(file, label text)]} of the downloads already on the box."""
    by_url, files = {}, []
    if hand_map and pathlib.Path(hand_map).exists():
        for u, v in (json.load(open(hand_map, encoding='utf-8')) or {}).items():
            raw = v if isinstance(v, str) else (v or {}).get('path') or (v or {}).get('original')
            if not raw or str(raw).startswith('http'): continue   # a pointer to another layer, not a file
            rp = real_path(raw)
            if rp.exists(): by_url.setdefault(norm_url(u), []).append(rp); files.append((rp, ' '.join(str(x) for x in ((v if isinstance(v, dict) else {}).get('label') or '', u))))
    for md in (downloads_md, drive_index):
        if md: files += md_table_files(md, pathlib.Path(md).parent)
    if research and pathlib.Path(research).is_dir():
        files += [(p, p.stem.replace('_', ' ')) for p in sorted(pathlib.Path(research).iterdir()) if p.suffix.lower() in ('.geojson', '.json', '.zip')]
    return {'by_url': by_url, 'files': files}


def match_rows(rows, inv, sources=None):
    """{row id: [files]}: a row's layer address in the hand map, or its source's FULL layer name (25+ letters, so a generic name
    like 'Protected Areas' never matches) in a downloads-table row. A bot's row with an official direct file is left to the bot:
    a box file that happens to share its address may cover other areas (e.g. a few refuges, none in this area)."""
    src = (sources or {}).get('sources') or {}
    out = {}
    for r in rows:
        if r.get('who') == 'bot' and M.direct_file_of(r): continue
        got = list(inv['by_url'].get(norm_url(r.get('url')), []))
        nm = (src.get(r.get('src') or '') or {}).get('name') or ''
        if len(nm) >= 25:
            key = re.sub(r'\W+', ' ', nm.lower()).strip()
            got += [p for p, lab in inv['files'] if key and key in re.sub(r'\W+', ' ', lab.lower())]
        if got: out[r['id']] = sorted(set(got), key=str)
    return out


# ---- reading box files (GeoJSON directly; Shapefile / FGDB through pyogrio, box only) ------------------------------------------
def read_any(path, layer=None, where=None):
    """-> [GeoJSON Feature] in lon/lat. where = {field: [values]} keeps only those records."""
    s = str(path)
    if not s.startswith('/vsizip/') and pathlib.Path(s).suffix.lower() in ('.geojson', '.json', ''):
        d = json.loads(pathlib.Path(s).read_text(encoding='utf-8-sig')); fs = d.get('features') or []
    else:
        import pyogrio, shapely  # noqa: E401  (box only)
        df = pyogrio.read_dataframe(s, layer=layer)
        if df.crs is not None and df.crs.to_epsg() != 4326: df = df.to_crs(4326)
        df['geometry'] = shapely.force_2d(df.geometry.values)
        for c in df.columns:
            if c != 'geometry' and str(df[c].dtype).startswith(('datetime', 'object')): df[c] = df[c].map(lambda v: v if v is None or isinstance(v, (str, int, float, bool)) else str(v))
        fs = json.loads(df.to_json(drop_id=True)).get('features') or []
    if where:
        fs = [f for f in fs if all(str((f.get('properties') or {}).get(k)) in {str(x) for x in v} for k, v in where.items())]
    return fs


def write_feats_json(feats, path):
    pathlib.Path(path).write_text(json.dumps({'type': 'FeatureCollection', 'features': feats}, ensure_ascii=False), encoding='utf-8'); return path


def pack_ca(spec, row, out_dir, today):
    feats = read_any(spec['file'], spec.get('ogr_layer'), spec.get('where'))
    nf = spec['name_field']; idf = spec.get('id_field') or 'OBJECTID'
    out_f = []
    for f in feats:
        a = f.get('properties') or {}
        if not a.get(nf): continue
        g = M.trim_geometry(f.get('geometry'))
        out_f.append({'type': 'Feature', 'geometry': g, 'properties': {'_ca': {'id': a.get(idf), 'n': a.get(nf), 'nf': a.get(spec.get('namef_field') or '') or '',
                                                                                'ty': a.get(spec.get('type_field') or '') or spec['label'], 'ow': spec.get('owner') or '',
                                                                                'mg': spec.get('manager') or '', 'ha': 0}}})
    if not out_f: return False, 'no named records in the file', None
    rp = real_path(spec['file'])
    meta = {'area': 'CA', 'layer': spec['layer'], 'label': spec['label'], 'url': row.get('url') or '', 'count_expected': len(out_f), 'count_raw': len(feats),
            'raw': facts(rp, row.get('page') or row.get('url') or '', len(feats)), 'page': row.get('page') or '', 'read': today, 'source': 'hand', 'by': 'KPC owner (import-existing)'}
    slug = re.sub(r'[^A-Za-z0-9]+', '', spec['layer'])
    p = M.write_layer_file(pathlib.Path(out_dir) / f'hand-CA.{slug}.geojson.gz', meta, out_f)
    return True, f'OK: {len(out_f)} records ({spec["label"]}); checked file {p.name}', p


def pack_world(spec, row, out_dir, today):
    feats = read_any(spec['file'], spec.get('ogr_layer'), spec.get('where'))
    if spec.get('expected') and len(feats) < int(spec['expected']): return False, f'SHORT: {len(feats)} of {spec["expected"]} records (fail closed)', None
    if not feats: return False, 'no records for this area in the file', None
    for f in feats: f['geometry'] = M.trim_geometry(f.get('geometry'))
    rp = real_path(spec['file'])
    meta = {'area': row['area'], 'layer': row['layer'], 'label': spec.get('label') or '', 'url': row.get('url') or '', 'name_field': spec.get('name_field') or '',
            'count_expected': len(feats), 'raw': facts(rp, row.get('page') or row.get('url') or ''), 'page': row.get('page') or '', 'read': today, 'source': 'hand',
            'by': 'KPC owner (import-existing)'}
    p = M.write_layer_file(pathlib.Path(out_dir) / f'hand-{row["area"]}.{row["layer"]}.geojson.gz', meta, feats)
    return True, f'OK: {len(feats)} records in {row["area"]}; checked file {p.name}', p


def pack_us(spec, row, out_dir, parks, layers_table, today, work):
    import importlib.util
    hp = pathlib.Path(__file__).resolve().parents[2] / 'tools' / 'kpc_pc_helper.py'
    sp = importlib.util.spec_from_file_location('kpc_pc_helper', hp); H = importlib.util.module_from_spec(sp); sp.loader.exec_module(H)
    feats = read_any(spec['file'], spec.get('ogr_layer'), spec.get('where'))
    tmp = write_feats_json(feats, pathlib.Path(work) / (re.sub(r'[^A-Za-z0-9._-]+', '_', real_path(spec['file']).name) + '.json'))
    r2 = dict(row, layer=spec.get('layer') or row['layer'])
    lt = dict(layers_table)
    if spec.get('name_field') and r2['layer'] not in lt: lt[r2['layer']] = [row.get('url') or '', spec['name_field'], spec.get('label') or '']
    ok, msg, p = H.check_and_pack(r2, [tmp], parks, out_dir, lt, today=today)
    if ok:   # the raw facts are the person's ORIGINAL file, not the converted copy
        meta, fs = M.read_layer_file(p); meta['raw'] = facts(real_path(spec['file']), row.get('page') or row.get('url') or '', len(feats))
        meta['count_expected'] = max(int(meta.get('count_expected') or 0), len(fs))   # the whole checked file is expected, not only the old baseline
        M.write_layer_file(p, meta, fs)
    return ok, msg, p


def build_needs(seed_rows, extra_rows, matched, all_facts):
    """One fresh list: seed rows + the master step's rows, then 'existing download' marks."""
    doc = {'format': M.NEEDS_FORMAT, 'rows': []}
    doc, _, _ = M.merge_needs(doc, seed_rows)
    doc, _, _ = M.merge_needs(doc, extra_rows)
    for r in doc['rows']:
        fs = matched.get(r['id'])
        if not fs or r.get('who') == 'never': continue
        names = ', '.join(sorted({all_facts[str(f)]['name'] + (f" ({all_facts[str(f)]['count']} records)" if all_facts[str(f)].get('count') else '') for f in fs if str(f) in all_facts}))
        if r.get('status') != 'done':
            r['status'] = 'done'; r['source'] = 'existing download'; r['why'] = WHY_EXISTING
        r['note'] = ((r.get('note') or '') + ' existing download: ' + names).strip()[:600]
    return doc


def main(a):
    today = datetime.date.today().isoformat(); root = pathlib.Path(a.root or M.OUTLINES)
    import kpc_master_watch as W
    same_as = json.load(open(a.same_as, encoding='utf-8')) if a.same_as else None
    _, seed_rows = W.seed(a.csv, root / 'download-sources.json', copies=a.copies, same_as=same_as, us_layers=a.us_layers) if a.csv else (None, [])
    extra = []
    for f in a.add or []: extra += (M.load_json(f, {}) or {}).get('rows') or []
    W.link_rows(root / 'download-sources.json', extra)
    inv = inventory(a.hand_map, a.downloads_md, a.drive_index, a.research)
    rows_all = seed_rows + extra
    matched = match_rows(rows_all, inv, M.load_json(root / 'download-sources.json', {}))
    spec = json.load(open(a.box_only, encoding='utf-8')) if a.box_only else []
    keep = set()   # spec rows with mark_done false: raw facts + a hand file, the row keeps its status (e.g. a bot's official file)
    for s in spec:
        for rid in [s['row']] + list(s.get('also') or []):
            matched.setdefault(rid, []).append(real_path(s['file']))
            if s.get('mark_done') is False: keep.add(rid)
    all_facts = {}
    # a US hand file's original is recorded by the master step when it merges the file (the same sha256 is how it knows a file was
    # already applied), so it is not raw-added here
    later = {str(real_path(s['file'])) for s in spec if (s.get('kind') or ('us' if s['row'].startswith('US-') else '')) == 'us'}
    for rid, fs in sorted(matched.items()):
        r = next((x for x in rows_all if x['id'] == rid), {})
        for f in fs:
            if str(f) in all_facts or not pathlib.Path(f).exists(): continue
            all_facts[str(f)] = facts(f, r.get('page') or r.get('url') or '')
            if str(f) not in later: M.raw_add_facts(all_facts[str(f)], root=root)
    doc = build_needs(seed_rows, extra, {k: v for k, v in matched.items() if k not in keep}, all_facts)
    made, report = [], []
    if spec:
        out = pathlib.Path(a.hand_out); out.mkdir(parents=True, exist_ok=True); work = out / '.work'; work.mkdir(exist_ok=True)
        lt = M.load_json(a.us_layers, {}) or {}
        for s in spec:
            r = next((x for x in doc['rows'] if x['id'] == s['row']), None)
            if r is None: report.append((s['row'], False, 'no such needs row')); continue
            kind = s.get('kind') or ('us' if r['area'].startswith('US-') else 'ca' if r['area'].startswith('CA') else 'world')
            blk = M.share_block(r, root)
            if blk: report.append((s['row'], False, blk)); continue   # WDPA / redistribute=no: never packed or uploaded
            try:
                ok, msg, p = (pack_us(s, r, out, a.parks, lt, today, work) if kind == 'us' else pack_ca(s, r, out, today) if kind == 'ca' else pack_world(s, r, out, today))
            except Exception as e: ok, msg, p = False, f'could not pack it ({e})', None  # noqa: BLE001
            report.append((s['row'], ok, msg))
            if ok:
                made.append(p)
                fa = (M.parse_hand_name(p.name) or (r['area'],))[0]   # a checked file is noted only on rows of the area in its name
                for r2 in [x for x in doc['rows'] if x['id'] in [s['row']] + list(s.get('also') or []) and (x['area'] == fa or not p.name.startswith(('hand-US-', 'hand-W-')))]:
                    r2['note'] = ((r2.get('note') or '') + f' checked hand file: {p.name}').strip()[:600]
                    if s.get('status'): r2['status'] = s['status']; r2['why'] = s.get('why') or r2['why']
    M.save_needs(doc, a.needs_out)
    for rid, ok, msg in report: print(('OK   ' if ok else 'FAIL ') + rid + ': ' + msg, flush=True)
    print(json.dumps({'raw_files': len(all_facts), 'rows': len(doc['rows']), 'hand_files': [str(p) for p in made], **M.needs_summary(doc)}, indent=1, default=str), flush=True)
    if a.upload and made:
        rc = subprocess.run(['gh', 'release', 'upload', 'boundary-cache', *map(str, made), '-R', a.repo, '--clobber']).returncode
        print(f'uploaded {len(made)} file(s) to boundary-cache: exit {rc}', flush=True)
        return rc
    return 0
