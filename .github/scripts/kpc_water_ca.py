#!/usr/bin/env python3
"""CANADA'S WATER for the 2-fer line (chat 2, Oct 28 2026; Brandon 11:19 PM: 'download water tiles for Canada').
The same job as kpc_water_bulk.py (USGS) for Canadian rows: the saved water tiles (0.1 degree, WATER_STORE) under every Canadian
area row, water-route row and 'water not checked' row, cut from Natural Resources Canada's NATIONAL HYDRO NETWORK (NHN, GeoBase,
Open Government Licence - Canada) GeoPackages, one per work unit: https://ftp.maps.canada.ca/pub/nrcan_rncan/vector/geobase_nhn_rhn/
(index NHN_INDEX_WORKUNIT_LIMIT_2.zip; files gpkg_en/CA/). Only the water-body POLYGONS are kept (lakes, rivers drawn as areas,
reservoirs = NHN_HD_WATERBODY), as layer 'wb'. A tile is saved only when every work unit over it was read; a tile is never saved
over an existing one. The line reads these tiles exactly like the US ones (never the live USGS map for a Canadian row).
Env: STATES (CA-ON CA-QC ...; US states are skipped), WATER_STORE, DATA. REPORT=1 = the per-province count only. Never fails."""
import gzip, io, json, os, pathlib, re, shutil, sys, tempfile, time, urllib.error, urllib.request, zipfile
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import kpc_water_bulk as WB   # noqa: E402  (tiles_needed / report / the GeoPackage reader)

BASE = 'https://ftp.maps.canada.ca/pub/nrcan_rncan/vector/geobase_nhn_rhn/'
INDEX = BASE + 'index/NHN_INDEX_WORKUNIT_LIMIT_2.zip'
UA = WB.UA
MAX_WU = int(os.environ.get('MAX_WU') or 120)


def notice(m): print('::notice title=Canada water (NHN)::' + str(m)[:900], flush=True)


def fetch(url, timeout=600):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r: return r.read()


def work_units():
    """{work unit id: (minx, miny, maxx, maxy)}: from NRCan's KMZ index first (small), else the shapefile index (big: ~250 MB)."""
    out = {}
    try:
        z = zipfile.ZipFile(io.BytesIO(fetch(BASE + 'index/nhn_index_geobase.kmz', 900)))
        kml = z.read(next(n for n in z.namelist() if n.lower().endswith('.kml'))).decode('utf-8', 'replace')
        for pm in re.findall(r'<Placemark.*?</Placemark>', kml, re.S):
            m = re.search(r'\b(\d{2}[A-Za-z]{2}\d{3})\b', pm)
            cs = [tuple(map(float, c.split(',')[:2])) for blk in re.findall(r'<coordinates>(.*?)</coordinates>', pm, re.S) for c in blk.split() if c.count(',') >= 1]
            if m and cs:
                xs = [c[0] for c in cs]; ys = [c[1] for c in cs]; w = m.group(1).upper()
                b = out.get(w)
                out[w] = (min(xs), min(ys), max(xs), max(ys)) if not b else (min(b[0], min(xs)), min(b[1], min(ys)), max(b[2], max(xs)), max(b[3], max(ys)))
        print(f'NHN index (KMZ): {len(out)} work units', flush=True)
        if out: return out
    except Exception as e: print(f'NHN KMZ index: {str(e)[:100]}', flush=True)  # noqa: BLE001
    import shapefile   # pyshp
    data = None
    for k in range(3):   # the shapefile index is ~250 MB: stream it to disk, retry a cut download
        try:
            p = os.path.join(tempfile.gettempdir(), 'nhn_index.zip')
            with urllib.request.urlopen(urllib.request.Request(INDEX, headers=UA), timeout=1800) as r, open(p, 'wb') as f: shutil.copyfileobj(r, f, 1 << 22)
            data = zipfile.ZipFile(p); break
        except Exception as e: print(f'NHN index try {k + 1}: {str(e)[:100]}', flush=True); time.sleep(20)  # noqa: BLE001
    z = data
    shp = next(n for n in z.namelist() if n.lower().endswith('.shp'))
    stem = shp[:-4]
    r = shapefile.Reader(shp=io.BytesIO(z.read(shp)), dbf=io.BytesIO(z.read(stem + '.dbf')),
                         shx=io.BytesIO(z.read(stem + '.shx')) if stem + '.shx' in z.namelist() else None)
    names = [f[0] for f in r.fields[1:]]
    for sr in r.iterShapeRecords():
        rec = dict(zip(names, sr.record))
        wid = next((str(v).strip() for v in rec.values() if re.fullmatch(r'\d{2}[A-Z]{2}\d{3}', str(v).strip().upper())), None)
        if not wid: continue
        bx = sr.shape.bbox
        if bx and abs(bx[0]) > 180: continue
        out[wid.upper()] = tuple(bx)
    print(f'NHN index (shapefile): {len(out)} work units (fields: {", ".join(names[:8])})', flush=True)
    return out


def listing(need=()):
    """{work unit id: GeoPackage URL}: NRCan files sit in gpkg_en/<first 2 digits>/nhn_rhn_<id>_gpkg_en.zip (the CA folder = whole-country
    files); each needed unit's folder is listed once; when a listing fails, the usual name is tried as is."""
    files = {}
    for d2 in sorted({w[:2] for w in need}):
        sub = f'gpkg_en/{d2}/'
        try:
            html = fetch(BASE + sub, 120).decode('utf-8', 'replace')
            for href in re.findall(r'href="([^"]+\.zip)"', html, re.I):
                m = re.search(r'(\d{2}[a-z]{2}\d{3})', href, re.I)
                if m: files.setdefault(m.group(1).upper(), href if href.startswith('http') else BASE + sub + href.split('/')[-1])
            if not files: notice(f'listing {sub}: no work-unit zip found; first links: ' + ', '.join(re.findall(r'href="([^"]+)"', html)[:8]))
        except Exception as e: notice(f'listing {sub}: {str(e)[:80]}')  # noqa: BLE001
    for w in need: files.setdefault(w, f'{BASE}gpkg_en/{w[:2]}/nhn_rhn_{w.lower()}_gpkg_en.zip')
    if files: print(f'NHN files: {len(files)}, e.g. {next(iter(files.values()))}', flush=True)
    return files


def read_wu(zpath, tiles, out, tmp):
    """Water-body polygons over the needed tiles from one NHN work-unit GeoPackage (SQLite + R-tree, no GDAL)."""
    import sqlite3
    with zipfile.ZipFile(zpath) as z:
        inner = [n for n in z.namelist() if n.lower().endswith('.gpkg')]
        if not inner: return 0
        gp = os.path.join(tmp, 'wu.gpkg')
        with z.open(inner[0]) as src, open(gp, 'wb') as f: shutil.copyfileobj(src, f, 1 << 22)
    os.remove(zpath)
    db = sqlite3.connect(gp); n = 0
    try:
        gc = [(r[0], r[1]) for r in db.execute('SELECT table_name, column_name FROM gpkg_geometry_columns')]
        wb = [(t, c) for t, c in gc if re.search(r'waterbody', t, re.I)]
        if not wb: print(f'  no waterbody layer; layers: {[t for t, _ in gc][:12]}', flush=True)
        for tbl, col in wb:
            rt = f'rtree_{tbl}_{col}'
            has_rt = bool(db.execute("SELECT name FROM sqlite_master WHERE name = ?", (rt,)).fetchone())
            for (i, j) in tiles:
                tb = (i * .1 - .02, j * .1 - .02, (i + 1) * .1 + .02, (j + 1) * .1 + .02)
                if has_rt:
                    q = (f'SELECT t."{col}" FROM "{tbl}" t JOIN "{rt}" r ON t.rowid = r.id WHERE r.maxx >= ? AND r.minx <= ? AND r.maxy >= ? AND r.miny <= ?')
                    rows = db.execute(q, (tb[0], tb[2], tb[1], tb[3]))
                else: rows = db.execute(f'SELECT "{col}" FROM "{tbl}"')
                for (blob,) in rows:
                    if blob is None: continue
                    try: rings = [r for r in WB._gpkg_rings(blob) if len(r) > 2]
                    except Exception: continue  # noqa: BLE001
                    if not has_rt:
                        xs = [p[0] for r in rings for p in r]; ys = [p[1] for r in rings for p in r]
                        if not xs or max(xs) < tb[0] or min(xs) > tb[2] or max(ys) < tb[1] or min(ys) > tb[3]: continue
                    if rings: out.setdefault((i, j), []).append(['wb', rings]); n += 1
    finally:
        db.close()
        try: os.remove(gp)
        except Exception: pass  # noqa: BLE001
    return n


WU_OK = []


def read_wu_shp(zpath, tiles, out):
    """The same water-body polygons from a work unit's SHAPEFILE package (pyshp; NHN shapefiles are in degrees, NAD83)."""
    import shapefile
    n = 0
    with zipfile.ZipFile(zpath) as z:
        shp = [q for q in z.namelist() if q.lower().endswith('.shp') and 'waterbody' in q.lower()]
        for sp in shp:
            b = sp[:-4]
            rd = shapefile.Reader(shp=io.BytesIO(z.read(sp)), dbf=io.BytesIO(z.read(b + '.dbf')), shx=io.BytesIO(z.read(b + '.shx')))
            for i in range(len(rd)):
                try: shp_ = rd.shape(i)
                except Exception: continue  # noqa: BLE001
                if not shp_.points: continue
                bx = shp_.bbox
                parts = list(shp_.parts) + [len(shp_.points)]
                rings = [[[round(p[0], 6), round(p[1], 6)] for p in shp_.points[parts[k]:parts[k + 1]]] for k in range(len(parts) - 1)]
                rings = [r for r in rings if len(r) > 2]
                for (i2, j2) in tiles:
                    tb = (i2 * .1 - .02, j2 * .1 - .02, (i2 + 1) * .1 + .02, (j2 + 1) * .1 + .02)
                    if bx[2] < tb[0] or bx[0] > tb[2] or bx[3] < tb[1] or bx[1] > tb[3]: continue
                    out.setdefault((i2, j2), []).append(['wb', rings]); n += 1
    try: os.remove(zpath)
    except Exception: pass  # noqa: BLE001
    return n


def main():
    WB.STATES[:] = [s for s in WB.STATES if s.startswith('CA-')]
    if not WB.STATES: print('no Canadian provinces in STATES', flush=True); return
    if os.environ.get('REPORT'): WB.report(); return
    store = WB.STORE; store.mkdir(parents=True, exist_ok=True)
    per = {}; need = WB.tiles_needed(per)
    have = {tuple(int(v) for v in p.name.split('.')[0].split('_')) for p in store.glob('*_*.json.gz')}
    miss = sorted(need - have)
    notice(f"{' '.join(WB.STATES)}: {len(need)} water tiles under the rows, {len(have & need)} already saved, {len(miss)} to fill from the NHN files"
           + (' (' + '; '.join(f'{st} {len(t)}/{len(t & have)}' for st, t in per.items() if t) + ' needed/saved)' if per else ''))
    if not miss: return
    try: wus = work_units()
    except Exception as e: notice(f'the NHN index did not answer ({str(e)[:100]}): nothing filled'); return  # noqa: BLE001
    cover = {}
    for t in miss:
        tb = (t[0] * .1, t[1] * .1, (t[0] + 1) * .1, (t[1] + 1) * .1)
        cover[t] = {w for w, b in wus.items() if not (b[2] < tb[0] or b[0] > tb[2] or b[3] < tb[1] or b[1] > tb[3])}
    todo = sorted({w for s in cover.values() for w in s})
    files = listing(todo)
    nofile = [w for w in todo if w not in files]
    if len(todo) > MAX_WU: notice(f'{len(todo)} work units needed, only the first {MAX_WU} read this run'); todo = todo[:MAX_WU]
    out, used, failed, tmp = {}, set(), {}, tempfile.mkdtemp()
    for w in todo:
        if w not in files: continue
        zp = os.path.join(tmp, f'{w}.zip')
        try:
            t0 = time.time()
            # Oct 29: the GeoPackage name is a guess when a folder will not list: try the usual names, then the shapefile package
            tries = [files[w], f'{BASE}gpkg_en/{w[:2]}/nhn_rhn_{w.lower()}_gpkg_en.zip', f'{BASE}gpkg_en/{w[:2]}/NHN_RHN_{w}_GPKG_EN.zip',
                     f'{BASE}shp_en/{w[:2]}/nhn_rhn_{w.lower()}_shp_en.zip', f'{BASE}shp_en/{w[:2]}/NHN_RHN_{w}_SHP_EN.zip']
            got, last = None, None
            for u in dict.fromkeys(tries):
                try:
                    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=1800) as r, open(zp, 'wb') as f: shutil.copyfileobj(r, f, 1 << 22)
                    got = u; break
                except Exception as e2: last = e2  # noqa: BLE001
            if not got: raise last
            if not WU_OK: notice(f'NHN files found at {got}'); WU_OK.append(got)
            mb = os.path.getsize(zp) / 1048576
            ts = [t for t in miss if w in cover[t]]
            n = read_wu(zp, ts, out, tmp) if not got.lower().endswith('_shp_en.zip') else read_wu_shp(zp, ts, out); used.add(w)
            print(f'NHN {w} ({mb:.0f} MB): {n} water pieces for {len(ts)} tiles in {time.time() - t0:.0f} s', flush=True)
        except Exception as e: failed[w] = str(e)[:100]; print(f'NHN {w}: not read ({str(e)[:100]})', flush=True)  # noqa: BLE001
        finally:
            try: os.remove(zp)
            except Exception: pass  # noqa: BLE001
    shutil.rmtree(tmp, ignore_errors=True)
    if not used: notice('no NHN file could be read: nothing filled' + (f" ({'; '.join(f'{k}: {v}' for k, v in list(failed.items())[:4])})" if failed else '')); return
    date = time.strftime('%Y-%m-%d'); n = skipped = 0
    for t in miss:
        if not cover.get(t) or not cover[t] <= used: skipped += 1; continue   # every work unit over the tile must have been read
        p = store / f'{t[0]}_{t[1]}.json.gz'
        if p.exists(): continue
        p.write_bytes(gzip.compress(json.dumps({'d': f'NRCan NHN file {date}', 'f': out.get(t, [])}, separators=(',', ':')).encode(), 6)); n += 1
    if skipped:
        notice(f"{skipped} tiles not filled: {sum(1 for t in miss if not cover.get(t))} have no NHN work unit over them (outside Canada's network); "
               f"work units not read: {', '.join(sorted({w for t in miss for w in cover.get(t, ()) if w not in used})[:20]) or 'none'}"
               + (f"; no file listed for {', '.join(nofile[:10])}" if nofile else ''))
    notice(f'{n} water tiles filled from {len(used)} NHN work units')


if __name__ == '__main__':
    try: main()
    except Exception as e: notice(f'stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
