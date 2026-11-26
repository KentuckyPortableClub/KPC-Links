#!/usr/bin/env python3
"""PAD-US state geodatabase -> the store's hand file (25 Nov 2026, owner: Alaska's PAD-US server answers 500, so the store has no
Alaska PAD-US; he downloaded USGS's own Alaska file PADUS4_1_State_AK_GDB_KMZ.zip from ScienceBase).

Reads the Fee and Proclamation layers of the unzipped .gdb (the two PAD-US layers the store keeps, as its PAD-US service gives
them), turns them to longitude/latitude, and writes ONE file the store tool reads by itself:
  ...\\1-STORE-TOOL\\kpc-outline-store-full\\have\\US-AK-PAD-US.geojson.gz  (+ a .kpc-source.json note)
Nothing is downloaded and nothing goes to GitHub. Then run LAYER-RECORDS.bat (it picks the file up), then START-HERE.

  py -3 -m pip install pyogrio        once (reads the geodatabase; shapely and pyproj are already there for the kit)
  py -3 kpc_padus_gdb.py "D:\\DOWNLOADS!\\PADUS4_1_State_AK.gdb" AK
"""
import datetime, gzip, hashlib, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
HAVE = HERE.parent / 'Tools' / 'KPC-TOOLS-NOV14' / '1-STORE-TOOL' / 'kpc-outline-store-full' / 'have'


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    gdb, st = pathlib.Path(argv[0]), argv[1].upper()
    try:
        import numpy as np, pyogrio, pyogrio.raw, shapely, shapely.ops, shapely.geometry, shapely.wkb
        from pyproj import Transformer
    except ImportError as e:
        print(f'STOPPED: {e.name} is missing. Run:  py -3 -m pip install pyogrio'); return 2
    if not gdb.is_dir():
        print(f'STOPPED: {gdb} is not a folder (unzip the download first; the .gdb is a folder).'); return 2
    layers = [str(x[0]) for x in pyogrio.list_layers(gdb)]
    want = [l for l in layers if ('fee' in l.lower() or 'proclamation' in l.lower()) and 'combined' not in l.lower()]
    print('layers in the file:', ', '.join(layers)); print('read:', ', '.join(want))
    if not want:
        print('STOPPED: no Fee or Proclamation layer in this file. Tell Claude the layer names above.'); return 2
    feats, n = [], 0
    for lay in want:
        meta, fids, geom, cols = pyogrio.raw.read(gdb, layer=lay, return_fids=True)
        _t = Transformer.from_crs(meta['crs'], 'EPSG:4326', always_xy=True).transform
        def to_ll(x, y, z=None):   # longitude/latitude, 6 decimals (about 0.1 m)
            a, b = _t(x, y)
            return np.round(np.asarray(a, dtype=float), 6), np.round(np.asarray(b, dtype=float), 6)
        names = list(meta['fields'])
        kind = 'Fee' if 'fee' in lay.lower() else 'Proclamation'
        for i in range(len(fids)):
            if geom[i] is None: continue
            g = shapely.ops.transform(to_ll, shapely.wkb.loads(bytes(geom[i])))
            if g.is_empty: continue
            p = {}
            for k, c in zip(names, cols):
                v = c[i]
                if hasattr(v, 'item'): v = v.item()
                if isinstance(v, float) and v != v: v = None
                if isinstance(v, (datetime.date, datetime.datetime)): v = v.isoformat()
                p[k] = v if isinstance(v, (str, int, float, bool, type(None))) else str(v)
            p.setdefault('FeatClass', kind)
            n += 1; p['OBJECTID'] = n   # the row number (not an id); PAD-US's own id is Source_PAID
            gj = json.loads(json.dumps(shapely.geometry.mapping(g)))
            feats.append({'type': 'Feature', 'properties': p, 'geometry': gj})
        print(f'  {lay}: {len(fids)} records')
    HAVE.mkdir(parents=True, exist_ok=True)
    out = HAVE / f'US-{st}-PAD-US.geojson.gz'
    data = json.dumps({'type': 'FeatureCollection', 'features': feats}, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    raw = gzip.compress(data, 9); out.write_bytes(raw)
    note = {'list_rows': [{'key id': 'US:PAD-US'}], 'id_field': 'OBJECTID',
            'about': f'USGS PAD-US (Fee + Proclamation), {len(feats)} records, from the owner\'s own download of the {st} state geodatabase '
                     f'({gdb.name}) from USGS ScienceBase, because the PAD-US server failed for the tool. OBJECTID is the row number; '
                     'Source_PAID is PAD-US\'s own id.',
            'key_layer_address': 'PAD-US', 'page_address': 'https://www.sciencebase.gov/catalog/item/6759abcfd34edfeb8710a004',
            'licence_line_as_shown': 'U.S. Geological Survey data (public domain)', 'sha256': hashlib.sha256(raw).hexdigest(),
            'crs': {'stated': 'converted to longitude/latitude (EPSG:4326) from the file\'s own projection'},
            'conversion': 'geodatabase Fee + Proclamation layers -> GeoJSON lon/lat (pyogrio, pyproj), 6 decimals; gzipped',
            'filed_on': datetime.date.today().isoformat()}
    (out.with_name(out.name + '.kpc-source.json')).write_text(json.dumps(note, indent=1), encoding='utf-8')
    print(f'Done: {len(feats)} records -> {out} ({len(raw) / 1e6:.1f} MB). Now run LAYER-RECORDS.bat, then START-HERE.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
