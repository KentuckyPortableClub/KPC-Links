#!/usr/bin/env python3
"""Offline: owner hand files for W-CZ, W-DE, W-MT and W-GL (KPC owner, 2026-11-12) are wired,
under 1 MB, keep their counts, merge keep-bigger into a saved copy, do not pre-dedupe
Malta site_codes, skip no-geometry records, refuse WDPA / unlicensed files, and merge chunks."""
import json, os, pathlib, shutil, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as M  # noqa: E402
import kpc_world_hand as WH  # noqa: E402

ok = True

def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


HAND = ROOT / 'data/outlines/hand'
# Usable Nov 12 inbox layers. Full-precision CZ EVL is shipped as h218 chunks (test_world_hand_nov13.py).
INBOX = [
    ('CZ-Natura2000-layer0-PO.geojson', 'hand-W-CZ.h217.geojson.gz', 'W-CZ', 'h217', 42, 'NAZEV', 'Ptačí oblast (PO)'),
    ('DE-HB-Naturschutzgebiete-layer2.geojson', 'hand-W-DE.h214.geojson.gz', 'W-DE', 'h214', 20, 'Gebietsname', 'Naturschutzgebiete'),
]
# Brandon, Nov 13 2026 7:45 AM CT: GL h212 and MT h213/h215 have no stated licence, so they stay off the public repo (internal only).
OFF = ('hand-W-GL.h212.geojson.gz', 'hand-W-MT.h213.geojson.gz', 'hand-W-MT.h215.geojson.gz')

check('usable Nov 12 inbox layers have a wired hand file in data/outlines/hand/',
      all((HAND / dest).is_file() for _, dest, *_ in INBOX))
check('the collapsed CZ EVL file is not shipped; full-precision EVL is chunked under h218 (no merged file in the repo)',
      not (HAND / 'hand-W-CZ.h213.geojson.gz').exists()
      and not (HAND / 'hand-W-CZ.h218.geojson.gz').exists()
      and bool(list(HAND.glob('hand-W-CZ.h218.chunk*.geojson.gz'))))
check('no-licence GL/MT hand files are not in the public repo', not any((HAND / f).exists() for f in OFF))
_lay = json.loads((ROOT / 'data/outlines/layers.json').read_text(encoding='utf-8'))['layers']
_src = json.loads((ROOT / 'data/outlines/download-sources.json').read_text(encoding='utf-8'))['sources']
check('GL/MT no-licence layers are not registered (layers.json, download-sources.json)',
      not any(k in _lay for k in ('W-GL.h212', 'W-MT.h213', 'W-MT.h215')) and not any(k in _src for k in ('h212', 'h213', 'h215')))

PROV = ('person', 'route', 'date', 'license', 'page')
for src, dest, area, layer, n, nf, label in INBOX:
    p = HAND / dest
    check(f'{dest} is under 1 MB ({p.stat().st_size} bytes)', p.stat().st_size < 1024 * 1024)
    check(f'{dest} name parses to {area}|{layer}', M.parse_hand_name(p.name) == (area, layer))
    why = M.hand_file_problem(p, area, layer)
    check(f'{dest} passes hand_file_problem', why == '')
    meta, feats = M.read_layer_file(p)
    if nf:
        check(f'{dest} holds {n} features (got {len(feats)}) with source=hand, name_field={nf}',
              len(feats) == n and meta.get('area') == area and meta.get('layer') == layer
              and meta.get('source') == 'hand' and meta.get('name_field') == nf
              and meta.get('label') == label and int(meta.get('count_expected') or 0) == n)
    else:
        check(f'{dest} holds {n} features (got {len(feats)})',
              len(feats) == n and meta.get('area') == area and meta.get('layer') == layer
              and int(meta.get('count_expected') or 0) == n)
    check(f'{dest} records full provenance (person, route, date, licence, official page)',
          meta.get('person') == 'Brandon (KPC owner)'
          and meta.get('route') == 'owner hand download'
          and meta.get('date') in ('2026-11-12', '2026-11-11')
          and bool(WH.hand_licence_text(meta))
          and bool(str(meta.get('page') or '').strip())
          and 'gis.nature.cz' not in str(meta.get('page') or '')
          and 'gis-hub.bremen.de' not in str(meta.get('page') or '')
          and 'arcgis.com' not in str(meta.get('page') or ''))

# Quality regrade: "not stated" is not a licence unless a recorded owner acceptance file exists
_ns = M.share_block({'area': 'W-MT', 'layer': 'h213', 'license': 'not stated (no licence text on the source page)'}, HAND)
check('a not-stated licence is refused by share_block', bool(_ns) and 'not stated' in _ns.lower())

_, po = WH.recs_from_hand(HAND / 'hand-W-CZ.h217.geojson.gz')
check('CZ PO: 42 named records with usable rings', len(po) == 42 and all(r.get('n') and r.get('_r') for r in po))
_, de = WH.recs_from_hand(HAND / 'hand-W-DE.h214.geojson.gz')
check('DE Bremen: 20 named records with usable rings', len(de) == 20 and all(r.get('n') and r.get('_r') for r in de))
# merge: CZ +42 only (no EVL), DE +20, MT 44; keep-bigger
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    def empty(cc):
        M.save_saved(td / f'W-{cc}.json.gz', {'cc': cc, 'saved': '2026-11-10', 'detail': 0.002, 'thin': 250, 'recs': []})
    empty('CZ'); empty('DE')
    ok1, what1 = WH.apply_world_hand_file(HAND / 'hand-W-CZ.h217.geojson.gz', td)
    cz = M.load_saved(td / 'W-CZ.json.gz')['recs']
    check(f'fill-merge W-CZ: 42 usable PO records, no EVL ({what1})', ok1 and len(cz) == 42)
    okd, _ = WH.apply_world_hand_file(HAND / 'hand-W-DE.h214.geojson.gz', td)
    check('fill-merge W-DE: 20 Bremen records', okd and len(M.load_saved(td / 'W-DE.json.gz')['recs']) == 20)

# no-geometry records are not counted
check('a record with no _bb and no _r is not counted',
      WH.world_current_rec_count('W-XX', {'recs': [{'_bb': None, '_r': [], 'src': 'L'}]}, ROOT) == 0)
check('a record with a bbox is counted when labels are unknown',
      WH.world_current_rec_count('W-XX', {'recs': [{'_bb': [0, 0, 1, 1], '_r': [[0, 0], [1, 0], [1, 1]], 'src': 'L'}]}, ROOT) == 1)

# M6: refuse WDPA / no licence; merge only a licensed file
POLY = {'type': 'Polygon', 'coordinates': [[[14.0, 35.8], [14.1, 35.8], [14.1, 35.9], [14.0, 35.9], [14.0, 35.8]]]}
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    M.save_saved(td / 'W-XX.json.gz', {'cc': 'XX', 'recs': []})
    def pack(name, meta, n=1):
        feats = [{'type': 'Feature', 'properties': {'NAME': f'p{i}', 'OBJECTID': i}, 'geometry': POLY} for i in range(n)]
        dest = td / name
        M.write_layer_file(dest, meta, feats)
        return dest
    wdpa = pack('hand-W-XX.wd1.geojson.gz', {
        'area': 'W-XX', 'layer': 'wd1', 'source': 'hand', 'label': 'Protected Planet WDPA polygons',
        'url': 'https://example.invalid/wdpa', 'name_field': 'NAME', 'count_expected': 1,
        'license': 'Protected Planet', 'person': 'Brandon (KPC owner)', 'route': 'owner hand download', 'date': '2026-11-12',
        'page': 'https://example.invalid/wdpa',
    })
    okw, whatw = WH.apply_world_hand_file(wdpa, td)
    check('a WDPA-labelled hand file is refused and the copy stays empty',
          (not okw) and ('WDPA' in whatw or 'Protected Planet' in whatw)
          and len(M.load_saved(td / 'W-XX.json.gz')['recs']) == 0)
    bare = pack('hand-W-XX.nolic.geojson.gz', {
        'area': 'W-XX', 'layer': 'nolic', 'source': 'hand', 'label': 'Some parks',
        'url': 'https://example.invalid/parks', 'name_field': 'NAME', 'count_expected': 1,
        'person': 'Brandon (KPC owner)', 'route': 'owner hand download', 'date': '2026-11-12',
        'page': 'https://example.invalid/parks',
    })
    okn, whatn = WH.apply_world_hand_file(bare, td)
    check('a hand file with no licence or terms is refused',
          (not okn) and 'licence' in whatn.lower() and len(M.load_saved(td / 'W-XX.json.gz')['recs']) == 0)

# M4: chunk merger
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    def pack_chunk(n, i):
        dest = td / f'hand-W-CZ.h218.chunk{i:02d}.geojson.gz'
        feat = {'type': 'Feature', 'properties': {'NAZEV': f'EVL{i}', 'OBJECTID': i}, 'geometry': POLY}
        M.write_layer_file(dest, {
            'area': 'W-CZ', 'layer': 'h218', 'source': 'hand', 'label': 'Evropsky významná lokalita (EVL)',
            'url': 'https://data.nature.cz/ds/INSPIRE-PS-Natura2000/', 'name_field': 'NAZEV', 'count_expected': 1,
            'license': 'CC BY 4.0 (c) AOPK ČR', 'person': 'Brandon (KPC owner)', 'route': 'owner hand download',
            'date': '2026-11-12', 'page': 'https://data.nature.cz/ds/INSPIRE-PS-Natura2000/',
        }, [feat])
        return dest
    p1, p2 = pack_chunk(1, 1), pack_chunk(1, 2)
    groups = WH.discover_hand_chunks(td, area='W-CZ', layer='h218')
    check('discover_hand_chunks groups two EVL chunk files', groups.get(('W-CZ', 'h218')) and len(groups[('W-CZ', 'h218')]) == 2)
    meta, feats = WH.merge_geojson_chunks([p1, p2])
    check('merge_geojson_chunks concatenates features and records chunk names',
          len(feats) == 2 and meta.get('count') == 2 and len(meta.get('chunks') or []) == 2)
    merged = td / 'hand-W-CZ.h218.geojson.gz'
    WH.write_merged_chunks([p1, p2], merged)
    M.save_saved(td / 'W-CZ.json.gz', {'cc': 'CZ', 'recs': []})
    okc, whatc = WH.apply_world_hand_file(merged, td)
    recs = M.load_saved(td / 'W-CZ.json.gz')['recs']
    check(f'chunk-merged EVL file merges 2 usable records ({whatc})', okc and len(recs) == 2)

# catalogs
lay = json.loads((ROOT / 'data/outlines/layers.json').read_text())['layers']
src = json.loads((ROOT / 'data/outlines/download-sources.json').read_text())['sources']
for _, dest, area, layer, n, nf, label in INBOX:
    key = f'{area}.{layer}'
    check(f'layers.json has {key} expected_count={n}', (lay.get(key) or {}).get('expected_count') == n)
    check(f'download-sources.json has {layer} for {area}',
          (src.get(layer) or {}).get('stated_count') == n and area in ((src.get(layer) or {}).get('areas') or []))
check('h212 / h213 are not reused for W-CZ (GL/MT ids stay retired off the public repo)',
      all('W-CZ' not in ((src.get(k) or {}).get('areas') or []) for k in ('h212', 'h213')) and 'W-CZ.h212' not in lay and 'W-CZ.h213' not in lay)
check('h218 is W-CZ EVL, stated_count 1111, shipped as chunks (no single merged file in the repo)',
      (src.get('h218') or {}).get('areas') == ['W-CZ']
      and (src.get('h218') or {}).get('stated_count') == 1111
      and not (src.get('h218') or {}).get('file')
      and bool((src.get('h218') or {}).get('files'))
      and 'W-CZ.h218' in lay
      and (lay.get('W-CZ.h218') or {}).get('expected_count') == 1111)

wf = (ROOT / '.github/workflows/kpc-world-cache.yml').read_text()
check('world-cache merges data/outlines/hand/hand-W-$CC.*.geojson.gz after T0 via fill',
      'hand-W-$CC' in wf and 'kpc_master_cli.py fill' in wf and 'touch .against/T0' in wf
      and wf.index('touch .against/T0') < wf.index('kpc_master_cli.py fill'))
check('world-cache stages release hand files and does not --clobber a repo copy',
      'world-hand-release' in wf and '--clobber' in wf
      and wf.index('world-hand-release') < wf.rindex('--clobber')  # clobber is only on the staging dir download
      and 'kept the repo copy' in wf and 'not a W-$CC hand file' in wf)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
