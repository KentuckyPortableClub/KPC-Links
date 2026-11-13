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
    ('MT-N2K-SAC-layer36.geojson', 'hand-W-MT.h215.geojson.gz', 'W-MT', 'h215', 30, 'site_name', 'Malta: Ambjent Malta (government agency; Natura 2000 data from ERA)'),
    ('MT-N2K-SPA-layer37.geojson', 'hand-W-MT.h213.geojson.gz', 'W-MT', 'h213', 14, 'site_name', 'N2K Special Protected Areas'),
]
GL = ('hand-W-GL.h212.geojson.gz', 'W-GL', 'h212', 63)

check('usable Nov 12 inbox layers have a wired hand file in data/outlines/hand/',
      all((HAND / dest).is_file() for _, dest, *_ in INBOX))
check('the collapsed CZ EVL file is not shipped; full-precision EVL is chunked under h218 (no merged file in the repo)',
      not (HAND / 'hand-W-CZ.h213.geojson.gz').exists()
      and not (HAND / 'hand-W-CZ.h218.geojson.gz').exists()
      and bool(list(HAND.glob('hand-W-CZ.h218.chunk*.geojson.gz'))))
check('hand-W-GL.h212 is registered in the repo', (HAND / GL[0]).is_file())

PROV = ('person', 'route', 'date', 'license', 'page')
for src, dest, area, layer, n, nf, label in INBOX + [(None, GL[0], GL[1], GL[2], GL[3], None, None)]:
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

# Quality regrade: "not stated" is not a licence unless a recorded owner acceptance file exists (do not invent one)
with tempfile.TemporaryDirectory() as _td_ns:
    _td_ns = pathlib.Path(_td_ns)
    for dest, area, layer in (('hand-W-GL.h212.geojson.gz', 'W-GL', 'h212'),
                              ('hand-W-MT.h213.geojson.gz', 'W-MT', 'h213'),
                              ('hand-W-MT.h215.geojson.gz', 'W-MT', 'h215')):
        meta, _ = M.read_layer_file(HAND / dest)
        why = M.share_block(meta, HAND)
        check(f'{dest} is refused by share_block (licence is not stated, no owner acceptance)',
              bool(why) and 'not stated' in why.lower())
        M.save_saved(_td_ns / f'{area}.json.gz', {'cc': area.replace('W-', ''), 'recs': []})
        applied, what = WH.apply_world_hand_file(HAND / dest, _td_ns)
        check(f'{dest} is not merged', (not applied) and 'not stated' in what.lower())

_, po = WH.recs_from_hand(HAND / 'hand-W-CZ.h217.geojson.gz')
check('CZ PO: 42 named records with usable rings', len(po) == 42 and all(r.get('n') and r.get('_r') for r in po))
_, de = WH.recs_from_hand(HAND / 'hand-W-DE.h214.geojson.gz')
check('DE Bremen: 20 named records with usable rings', len(de) == 20 and all(r.get('n') and r.get('_r') for r in de))
_, sac = WH.recs_from_hand(HAND / 'hand-W-MT.h215.geojson.gz')
_, spa = WH.recs_from_hand(HAND / 'hand-W-MT.h213.geojson.gz')
sac_c, spa_c = {r.get('code') for r in sac}, {r.get('code') for r in spa}
check('MT: 30 + 14 recs, 7 shared site_codes, union 37 (the saved copy is not pre-deduped)',
      len(sac) == 30 and len(spa) == 14 and len(sac_c & spa_c) == 7 and len(sac_c | spa_c) == 37
      and all(r.get('n') and r.get('_r') and r.get('code') for r in sac + spa))

# merge: CZ +42 only (no EVL), DE +20, MT 44; keep-bigger
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    def empty(cc):
        M.save_saved(td / f'W-{cc}.json.gz', {'cc': cc, 'saved': '2026-11-10', 'detail': 0.002, 'thin': 250, 'recs': []})
    empty('CZ'); empty('DE'); empty('MT')
    ok1, what1 = WH.apply_world_hand_file(HAND / 'hand-W-CZ.h217.geojson.gz', td)
    cz = M.load_saved(td / 'W-CZ.json.gz')['recs']
    check(f'fill-merge W-CZ: 42 usable PO records, no EVL ({what1})', ok1 and len(cz) == 42)
    okd, _ = WH.apply_world_hand_file(HAND / 'hand-W-DE.h214.geojson.gz', td)
    check('fill-merge W-DE: 20 Bremen records', okd and len(M.load_saved(td / 'W-DE.json.gz')['recs']) == 20)
    okm1, whatm1 = WH.apply_world_hand_file(HAND / 'hand-W-MT.h215.geojson.gz', td)
    okm2, whatm2 = WH.apply_world_hand_file(HAND / 'hand-W-MT.h213.geojson.gz', td)
    check('fill-merge W-MT h213/h215 is refused: licence is not stated and no owner acceptance file',
          (not okm1) and (not okm2)
          and 'not stated' in whatm1.lower() and 'not stated' in whatm2.lower()
          and len(M.load_saved(td / 'W-MT.json.gz')['recs']) == 0)
    # counting / keep-bigger still work on records read from the file; the file itself is not packed or merged
    mt = list(sac) + list(spa)
    M.save_saved(td / 'W-MT.json.gz', {'cc': 'MT', 'saved': '2026-11-10', 'detail': 0.002, 'thin': 250, 'recs': mt})
    one = WH.recs_from_hand(HAND / 'hand-W-MT.h213.geojson.gz')[1][:1]
    blob, what = WH.merge_world_saved_layer(M.load_saved(td / 'W-MT.json.gz'), one)
    check('keep-bigger: a smaller SPA re-read is refused, 44 records stay',
          'kept the saved' in what and len(blob['recs']) == 44 and blob is not False)
    # current-layer count honours sheet-countries labels (Quality #179 M5)
    got = WH.world_current_rec_count('W-MT', {'recs': mt}, ROOT)
    check(f'W-MT current-layer count is 44 (got {got}); sheet-countries label is honoured',
          got == 44 and 'Malta: Ambjent Malta (government agency; Natura 2000 data from ERA)' in WH.world_source_labels('MT', ROOT))

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
check('h212 is W-GL (release hand-W-GL.h212), not W-CZ',
      (src.get('h212') or {}).get('areas') == ['W-GL'] and 'W-GL.h212' in lay)
check('h213 is W-MT SPA (release hand-W-MT.h213), not W-CZ',
      (src.get('h213') or {}).get('areas') == ['W-MT'] and 'W-MT.h213' in lay)
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
