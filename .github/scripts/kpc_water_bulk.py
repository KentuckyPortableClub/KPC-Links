#!/usr/bin/env python3
"""USGS water from the BULK FILES (chat 2, Oct 28 2026; HQ 4:05 PM = chat 8's first choice in KPC_RiverBackup_desk.md).

The USGS water MAP SERVER (hydro.nationalmap.gov) went down most of Oct 28, and areas that never had a good read had no saved
copy. The same NHDPlus High Resolution data is published as files on USGS's Amazon storage (prd-tnm.s3.amazonaws.com), one
GeoPackage per 4-digit watershed (HU4). This fills the line's saved water tiles (WATER_STORE, the same 0.1-degree tiles
kpc_fers.nhd_water reads) for every tile under this area's spots that has NO saved tile yet:
  1. the tiles = the same boxes pass 5 checks (each area spot's box + 0.002 deg), plus the river-bank rows;
  2. the HU4 files under them = USGS's TNM product list (bbox search), each downloaded once, read with a box filter, deleted;
  3. per tile: NHDArea FType 460 (StreamRiver) + NHDWaterbody FType 390 / 436 / 493 (lake, reservoir, estuary), the same
     features and codes as the live query, whole features touching the tile + 0.02 deg (like the live answer), read with
     Python's own SQLite (a GeoPackage is a SQLite file with an R-tree index: no extra packages);
  4. saved as {'d': 'USGS NHDPlus HR file <date>', 'f': [[layer, rings], ...]}; a tile already saved (a live read) is never
     replaced. Rule 13: the rows show 'USGS water: saved copy of USGS NHDPlus HR file <date>'.
Env: STATES, WATER_STORE, DATA (data/fers), MAX_HU4 (default 40). Never fails the job."""
import glob, gzip, json, math, os, pathlib, re, shutil, sys, tempfile, time, urllib.error, urllib.parse, urllib.request, zipfile

STATES = (os.environ.get('STATES') or '').split()
STORE = pathlib.Path(os.environ.get('WATER_STORE') or 'bundle/water')
DATA = pathlib.Path(os.environ.get('DATA') or 'data/fers')
MAX_HU4 = int(os.environ.get('MAX_HU4') or 150)
DET = 0.00002
UA = {'User-Agent': 'KPC 2-fer bot (kentuckyportableclub.github.io; ham radio club park maps)'}
TNM = 'https://tnmaccess.nationalmap.gov/api/v1/products'
DS = 'National Hydrography Dataset Plus High Resolution (NHDPlus HR)'


def notice(m): print('::notice title=USGS water files::' + str(m)[:900], flush=True)


def sbox(s):
    b = s.get('box')
    if b: return b
    sh = s.get('shape') or []
    if not sh: return None
    return [min(p[0] for p in sh), min(p[1] for p in sh), max(p[0] for p in sh), max(p[1] for p in sh)]


def row_tiles(s):
    b = sbox(s)
    if not b: return set()
    pad = .002 if s.get('kind') == 'area' else .003
    return {(i, j) for i in range(int(math.floor((b[0] - pad) / .1)), int(math.floor((b[2] + pad) / .1)) + 1)
            for j in range(int(math.floor((b[1] - pad) / .1)), int(math.floor((b[3] + pad) / .1)) + 1)}


NOTCHK = re.compile(r'water not checked|water map did not answer')


def load_state(st):
    f = DATA / f'{st}.json'
    try:
        if f.exists(): return json.load(open(f))
        g = pathlib.Path(str(f) + '.gz')
        if g.exists(): return json.loads(gzip.decompress(g.read_bytes()))
    except Exception: pass  # noqa: BLE001
    return None


def tiles_needed(per=None):
    """Tiles under every area spot, water-route row and 'water not checked' row; per = {state: tiles} filled when given."""
    T = set()
    for st in STATES:
        d = load_state(st)
        if not d: continue
        mine = set()
        for s in d.get('spots') or []:
            stt = str(s.get('status', ''))
            if stt.startswith(('dropped', 'merged')): continue
            if s.get('kind') != 'area' and not s.get('water_route') and not NOTCHK.search(stt): continue
            mine |= row_tiles(s)
        T |= mine
        if per is not None: per[st] = mine
    return T


def report():
    """Fable Oct 28 10:34 PM: per state 'tiles needed / saved / rows not checked'; a 'not checked' row whose tiles are ALL saved
    means the line did not read the store = the bug to chase (printed loud)."""
    have = {tuple(int(v) for v in p.name.split('.')[0].split('_')) for p in STORE.glob('*_*.json.gz')}
    per = {}; tiles_needed(per); lines, bugs = [], 0
    for st in STATES:
        d = load_state(st) or {}
        nc = [s for s in d.get('spots') or [] if NOTCHK.search(str(s.get('status', '')))]
        notread = [s for s in nc if row_tiles(s) and row_tiles(s) <= have]
        bugs += len(notread)
        need = per.get(st, set())
        lines.append(f"{st}: tiles needed {len(need)} / saved {len(need & have)} / rows not checked {len(nc)}"
                     + (f" / {len(notread)} with ALL tiles saved = STORE NOT READ ({', '.join(str(s.get('id'))[:40] for s in notread[:3])})" if notread else ''))
        print('water report ' + lines[-1], flush=True)
    notice('water report: ' + ' · '.join(lines)[:850])
    if bugs: print(f'::warning title=2-fer water::{bugs} rows say "water not checked" although every tile they need is saved: the line is not reading the water store', flush=True)


def get_json(url, params, tries=3):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url + '?' + urllib.parse.urlencode(params), headers=UA), timeout=90) as r:
                return json.loads(r.read().decode('utf-8', 'replace'))
        except Exception as e:  # noqa: BLE001
            if k == tries - 1: raise
            time.sleep(10 * (k + 1))


def hu4_products(tiles):
    """HU4 GeoPackages that cover the tiles (TNM product search by box, the tiles grouped into 1-degree boxes)."""
    groups = {}
    for i, j in tiles: groups.setdefault((i // 10, j // 10), []).append((i, j))
    prods, G = {}, {}
    for (gi, gj), ts in groups.items():
        x0 = min(t[0] for t in ts) * .1; y0 = min(t[1] for t in ts) * .1; x1 = (max(t[0] for t in ts) + 1) * .1; y1 = (max(t[1] for t in ts) + 1) * .1
        j = get_json(TNM, {'datasets': DS, 'bbox': f'{x0},{y0},{x1},{y1}', 'prodFormats': 'GeoPackage', 'max': 50, 'outputFormat': 'JSON'})
        for it in j.get('items') or []:
            u = it.get('downloadURL') or ''
            m = re.search(r'NHDPLUS_H_(\d{4})_HU4', u)
            if m and u.lower().endswith('.zip'):
                prods[m.group(1)] = {'url': u, 'date': (it.get('publicationDate') or it.get('dateCreated') or '')[:10]}
                bb = it.get('boundingBox') or {}
                for t in ts:   # Oct 28: a tile needs only the HU4 files whose own box touches it (not every file of its 1-degree group)
                    tb = (t[0] * .1 - .02, t[1] * .1 - .02, (t[0] + 1) * .1 + .02, (t[1] + 1) * .1 + .02)
                    if bb and (bb.get('maxX', 999) < tb[0] or bb.get('minX', -999) > tb[2] or bb.get('maxY', 999) < tb[1] or bb.get('minY', -999) > tb[3]): continue
                    G.setdefault(t, set()).add(m.group(1))
    return prods, G


def s3_find(hu):
    """The current NHDPlus HR GeoPackage for one HU4 straight from USGS's Amazon storage listing (when the product list is stale)."""
    base = 'https://prd-tnm.s3.amazonaws.com/'
    for fmt in ('GPKG', 'GDB'):
        try:
            with urllib.request.urlopen(urllib.request.Request(base + '?' + urllib.parse.urlencode({'prefix': f'StagedProducts/Hydrography/NHDPlusHR/VPU/Current/{fmt}/NHDPLUS_H_{hu}_HU4'}), headers=UA), timeout=60) as r:
                keys = re.findall(r'<Key>([^<]+\.zip)</Key>', r.read().decode('utf-8', 'replace'))
            keys = [k for k in keys if 'GPKG' in k.upper()]
            if keys: return base + sorted(keys)[-1]
        except Exception: pass  # noqa: BLE001
    return None


def _wkb_polys(b, o=0):
    """Polygon / MultiPolygon WKB (2D, Z, M or ZM; ISO or EWKB flags) -> (rings, next offset)."""
    import struct
    bo = '<' if b[o] == 1 else '>'; t = struct.unpack_from(bo + 'I', b, o + 1)[0]; o += 5
    z = bool(t & 0x80000000); m = bool(t & 0x40000000); t &= 0x0FFFFFFF
    if t >= 1000: z = z or (t // 1000) in (1, 3); m = m or (t // 1000) in (2, 3); t %= 1000
    nd = 2 + z + m; rings = []
    if t == 3:
        nr = struct.unpack_from(bo + 'I', b, o)[0]; o += 4
        for _ in range(nr):
            n = struct.unpack_from(bo + 'I', b, o)[0]; o += 4
            v = struct.unpack_from(bo + 'd' * (n * nd), b, o); o += 8 * n * nd
            rings.append([[round(v[k * nd], 6), round(v[k * nd + 1], 6)] for k in range(n)])
    elif t == 6:
        np_ = struct.unpack_from(bo + 'I', b, o)[0]; o += 4
        for _ in range(np_):
            r, o = _wkb_polys(b, o); rings += r
    else: raise ValueError(f'geometry type {t}')
    return rings, o


def _gpkg_rings(blob):
    """GeoPackage geometry blob -> rings (lon, lat)."""
    b = bytes(blob)
    if b[:2] != b'GP': return []
    env = (b[3] >> 1) & 7
    off = 8 + {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}.get(env, 0)
    return _wkb_polys(b, off)[0]


def read_hu4(zpath, tiles, out, tmp):
    """Every needed tile's water from one HU4 GeoPackage (no GDAL: the file is SQLite + its own R-tree index)."""
    import sqlite3
    with zipfile.ZipFile(zpath) as z:
        inner = [n for n in z.namelist() if n.lower().endswith('.gpkg')]
        if not inner: return 0
        gp = os.path.join(tmp, 'hu4.gpkg')
        with z.open(inner[0]) as src, open(gp, 'wb') as f: shutil.copyfileobj(src, f, 1 << 22)
    os.remove(zpath)   # disk: only one copy at a time
    db = sqlite3.connect(gp); n = 0
    try:
        gc = {r[0].lower(): (r[0], r[1]) for r in db.execute('SELECT table_name, column_name FROM gpkg_geometry_columns')}
        xs = [t[0] for t in tiles]; ys = [t[1] for t in tiles]
        for key, lname, codes in (('area', 'nhdarea', (460,)), ('wb', 'nhdwaterbody', (390, 436, 493))):
            if lname not in gc: continue
            tbl, col = gc[lname]
            cols = {r[1].lower(): r[1] for r in db.execute(f'PRAGMA table_info("{tbl}")')}
            ftc = cols.get('ftype')
            rt = f'rtree_{tbl}_{col}'
            for (i, j) in tiles:
                tb = (i * .1 - .02, j * .1 - .02, (i + 1) * .1 + .02, (j + 1) * .1 + .02)
                q = (f'SELECT t."{col}", t."{ftc}" FROM "{tbl}" t JOIN "{rt}" r ON t.rowid = r.id '
                     'WHERE r.maxx >= ? AND r.minx <= ? AND r.maxy >= ? AND r.miny <= ?')
                for blob, ft in db.execute(q, (tb[0], tb[2], tb[1], tb[3])):
                    if blob is None or (ft is not None and int(ft) not in codes): continue
                    try: rings = [r for r in _gpkg_rings(blob) if len(r) > 2]
                    except Exception: continue  # noqa: BLE001
                    if rings: out.setdefault((i, j), []).append([key, rings]); n += 1
    finally:
        db.close()
        try: os.remove(gp)
        except Exception: pass  # noqa: BLE001
    return n


def main():
    STATES[:] = [s for s in STATES if not s.startswith('CA-')]   # Canada's water = kpc_water_ca.py (NRCan NHN), never the USGS files
    if not STATES: return
    STORE.mkdir(parents=True, exist_ok=True)
    per = {}
    need = tiles_needed(per)
    have = {tuple(int(v) for v in p.name.split('.')[0].split('_')) for p in STORE.glob('*_*.json.gz')}
    miss = sorted(need - have)
    notice(f"{' '.join(STATES)}: {len(need)} water tiles under the spots, {len(have & need)} already saved, {len(miss)} to fill from the USGS files"
           + (' (' + '; '.join(f'{st} {len(t)}/{len(t & have)}' for st, t in per.items() if t) + ' needed/saved)' if len(per) > 1 else ''))
    if not miss: return
    try: prods, cover = hu4_products(miss)
    except Exception as e: notice(f'the USGS product list did not answer ({str(e)[:80]}): nothing filled'); return  # noqa: BLE001
    if len(prods) > MAX_HU4: notice(f'{len(prods)} HU4 files needed, only the first {MAX_HU4} read this run'); prods = dict(sorted(prods.items())[:MAX_HU4])
    out, used, tmp, failed = {}, {}, tempfile.mkdtemp(), {}
    for hu, p in sorted(prods.items()):
        zp = os.path.join(tmp, f'{hu}.zip')
        try:
            t0 = time.time()
            try:
                with urllib.request.urlopen(urllib.request.Request(p['url'], headers=UA), timeout=1800) as r, open(zp, 'wb') as f: shutil.copyfileobj(r, f, 1 << 22)
            except urllib.error.HTTPError as e:
                if e.code != 404: raise
                u2 = s3_find(hu)   # Oct 28 (Southeast: 0601-0604 = 404): the product list points at an old file name; ask the storage itself
                if not u2: raise
                print(f'HU4 {hu}: the listed file is gone (404), using {u2}', flush=True)
                with urllib.request.urlopen(urllib.request.Request(u2, headers=UA), timeout=1800) as r, open(zp, 'wb') as f: shutil.copyfileobj(r, f, 1 << 22)
            mb = os.path.getsize(zp) / 1048576
            n = read_hu4(zp, miss, out, tmp); used[hu] = p['date']
            print(f'HU4 {hu} ({mb:.0f} MB, {p["date"]}): {n} water pieces in {time.time() - t0:.0f} s', flush=True)
        except Exception as e: failed[hu] = str(e)[:100]; print(f'HU4 {hu}: not read ({str(e)[:100]})', flush=True)  # noqa: BLE001
        finally:
            try: os.remove(zp)
            except Exception: pass  # noqa: BLE001
    shutil.rmtree(tmp, ignore_errors=True)
    if not used: notice('no USGS file could be read: nothing filled'); return
    date = max(used.values()) or time.strftime('%Y-%m-%d')
    n = 0
    skipped = 0
    for t in miss:   # a tile with no water at all is saved too (empty list = 'no water here', read from the file) ...
        if not cover.get(t) or not cover[t] <= set(used): skipped += 1; continue   # ... but ONLY when every HU4 file over it was read
        p = STORE / f'{t[0]}_{t[1]}.json.gz'
        if p.exists(): continue   # never replace a live read
        p.write_bytes(gzip.compress(json.dumps({'d': f'USGS NHDPlus HR file {date}', 'f': out.get(t, [])}, separators=(',', ':')).encode(), 6)); n += 1
    if skipped:
        need = sorted({h for t in miss for h in (cover.get(t) or set()) if h not in used})
        notice(f"{skipped} tiles not filled: {sum(1 for t in miss if not cover.get(t))} have no USGS file listed over them; files needed but not read: {', '.join(need) or 'none'} ({'; '.join(f'{k}: {v}' for k, v in list(failed.items())[:6])})")
    notice(f"{n} water tiles filled from {len(used)} USGS HU4 files ({', '.join(sorted(used))}), dated {date}")


if __name__ == '__main__':
    try: report() if os.environ.get('REPORT') else main()
    except Exception as e: notice(f'stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
