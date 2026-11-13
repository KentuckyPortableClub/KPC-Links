#!/usr/bin/env python3
"""Offline: owner hand files for W-CZ, W-DE and W-MT (KPC owner, 2026-11-12) are wired,
under 1 MB, keep their counts, merge keep-bigger into a saved copy, do not pre-dedupe
Malta site_codes, and store empty rings for the collapsed CZ EVL geometry."""
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
INBOX = [
    ('CZ-Natura2000-layer0-PO.geojson', 'hand-W-CZ.h212.geojson.gz', 'W-CZ', 'h212', 42, 'NAZEV', 'Ptačí oblast (PO)'),
    ('CZ-Natura2000-layer1-EVL.geojson', 'hand-W-CZ.h213.geojson.gz', 'W-CZ', 'h213', 1111, 'NAZEV', 'Evropsky významná lokalita (EVL)'),
    ('DE-HB-Naturschutzgebiete-layer2.geojson', 'hand-W-DE.h214.geojson.gz', 'W-DE', 'h214', 20, 'Gebietsname', 'Naturschutzgebiete'),
    ('MT-N2K-SAC-layer36.geojson', 'hand-W-MT.h215.geojson.gz', 'W-MT', 'h215', 30, 'site_name', 'Malta: Ambjent Malta (government agency; Natura 2000 data from ERA)'),
    ('MT-N2K-SPA-layer37.geojson', 'hand-W-MT.h216.geojson.gz', 'W-MT', 'h216', 14, 'site_name', 'N2K Special Protected Areas'),
]

check('all five Nov 12 inbox layers have a wired hand file in data/outlines/hand/',
      all((HAND / dest).is_file() for _, dest, *_ in INBOX))

for src, dest, area, layer, n, nf, label in INBOX:
    p = HAND / dest
    check(f'{dest} is under 1 MB ({p.stat().st_size} bytes)', p.stat().st_size < 1024 * 1024)
    check(f'{dest} name parses to {area}|{layer}', M.parse_hand_name(p.name) == (area, layer))
    why = M.hand_file_problem(p, area, layer)
    check(f'{dest} passes hand_file_problem', why == '')
    meta, feats = M.read_layer_file(p)
    check(f'{dest} holds {n} features (got {len(feats)}) with source=hand, name_field={nf}',
          len(feats) == n and meta.get('area') == area and meta.get('layer') == layer
          and meta.get('source') == 'hand' and meta.get('name_field') == nf
          and meta.get('label') == label and int(meta.get('count_expected') or 0) == n)

# names + rings
_, po = WH.recs_from_hand(HAND / 'hand-W-CZ.h212.geojson.gz')
check('CZ PO: 42 named records with usable rings', len(po) == 42 and all(r.get('n') and r.get('_r') for r in po))
_, evl = WH.recs_from_hand(HAND / 'hand-W-CZ.h213.geojson.gz')
check('CZ EVL: 1,111 named records, all rings empty (collapsed WGS84 offset=5 read)',
      len(evl) == 1111 and all(r.get('n') for r in evl) and all(not r.get('_r') and r.get('_bb') is None for r in evl))
_, de = WH.recs_from_hand(HAND / 'hand-W-DE.h214.geojson.gz')
check('DE Bremen: 20 named records with usable rings', len(de) == 20 and all(r.get('n') and r.get('_r') for r in de))
_, sac = WH.recs_from_hand(HAND / 'hand-W-MT.h215.geojson.gz')
_, spa = WH.recs_from_hand(HAND / 'hand-W-MT.h216.geojson.gz')
sac_c, spa_c = {r.get('code') for r in sac}, {r.get('code') for r in spa}
check('MT: 30 + 14 recs, 7 shared site_codes, union 37 (the saved copy is not pre-deduped)',
      len(sac) == 30 and len(spa) == 14 and len(sac_c & spa_c) == 7 and len(sac_c | spa_c) == 37
      and all(r.get('n') and r.get('_r') and r.get('code') for r in sac + spa))

# merge into tiny copies: CZ 0+42+1111, DE 0+20, MT 0+30+14=44, keep-bigger, smaller refused
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    def empty(cc):
        M.save_saved(td / f'W-{cc}.json.gz', {'cc': cc, 'saved': '2026-11-10', 'detail': 0.002, 'thin': 250, 'recs': []})
    empty('CZ'); empty('DE'); empty('MT')
    ok1, _ = WH.apply_world_hand_file(HAND / 'hand-W-CZ.h212.geojson.gz', td)
    ok2, _ = WH.apply_world_hand_file(HAND / 'hand-W-CZ.h213.geojson.gz', td)
    cz = M.load_saved(td / 'W-CZ.json.gz')['recs']
    check('fill-merge W-CZ: 42 + 1,111 = 1,153 records', ok1 and ok2 and len(cz) == 1153)
    okd, _ = WH.apply_world_hand_file(HAND / 'hand-W-DE.h214.geojson.gz', td)
    check('fill-merge W-DE: 20 Bremen records', okd and len(M.load_saved(td / 'W-DE.json.gz')['recs']) == 20)
    okm1, _ = WH.apply_world_hand_file(HAND / 'hand-W-MT.h215.geojson.gz', td)
    okm2, _ = WH.apply_world_hand_file(HAND / 'hand-W-MT.h216.geojson.gz', td)
    mt = M.load_saved(td / 'W-MT.json.gz')['recs']
    check('fill-merge W-MT: 30 + 14 = 44 (baseline), 7 site_codes in both layers',
          okm1 and okm2 and len(mt) == 44 and sum(1 for c in {r.get('code') for r in mt} if sum(1 for r in mt if r.get('code') == c) == 2) == 7)
    # keep-bigger: a 1-record re-read does not replace the SPA layer
    one = WH.recs_from_hand(HAND / 'hand-W-MT.h216.geojson.gz')[1][:1]
    blob, what = WH.merge_world_saved_layer(M.load_saved(td / 'W-MT.json.gz'), one)
    check('keep-bigger: a smaller SPA re-read is refused, 44 records stay',
          'kept the saved' in what and len(blob['recs']) == 44 and blob is not False)

# catalogs
lay = json.loads((ROOT / 'data/outlines/layers.json').read_text())['layers']
src = json.loads((ROOT / 'data/outlines/download-sources.json').read_text())['sources']
for _, dest, area, layer, n, nf, label in INBOX:
    key = f'{area}.{layer}'
    check(f'layers.json has {key} expected_count={n}', (lay.get(key) or {}).get('expected_count') == n)
    check(f'download-sources.json has {layer}', (src.get(layer) or {}).get('stated_count') == n and area in ((src.get(layer) or {}).get('areas') or []))

# world-cache applies repo hand files after T0
wf = (ROOT / '.github/workflows/kpc-world-cache.yml').read_text()
check('world-cache merges data/outlines/hand/hand-W-$CC.*.geojson.gz after T0 via fill',
      'hand-W-$CC' in wf and 'kpc_master_cli.py fill' in wf and 'touch .against/T0' in wf
      and wf.index('touch .against/T0') < wf.index('kpc_master_cli.py fill'))

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
