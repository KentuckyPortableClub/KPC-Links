#!/usr/bin/env python3
"""Offline: Nov 13 full-precision W-CZ EVL and W-DE state owner hand files (KPC owner, 2026-11-13)
reach the published baselines from usable geometry only: W-CZ = 7,938 (6,785 + 42 PO + 1,111 EVL)
and W-DE = 30,616 (23,904 + 6,692 state + 20 Bremen). Parts stay under 1 MB, ids do not collide,
each file has provenance and a per-agency licence, no POTA pin is moved, and no water-only
outline is shipped or counted."""
import hashlib, json, os, pathlib, sys, tempfile

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
CAP = 1024 * 1024
DATE = '2026-11-13'
BANNED_PAGE = ('gis.nature.cz', 'gis-hub.bremen.de', 'arcgis.com')

# Current-layer saved-copy counts (without the Nov 12/13 owner hand layers).
CZ_CURRENT = 6785
DE_CURRENT = 23904
CZ_PO, CZ_EVL = 42, 1111
DE_BREMEN, DE_STATE = 20, 6692
CZ_BASELINE = CZ_CURRENT + CZ_PO + CZ_EVL  # 7938
DE_BASELINE = DE_CURRENT + DE_STATE + DE_BREMEN  # 30616

NEW = [
    # layer, area, expected usable, name_field, label, n_parts_min
    ('h218', 'W-CZ', 1111, 'NAZEV', 'Evropsky významná lokalita (EVL)'),
    ('h219', 'W-DE', 1062, 'OBJEKT', 'Naturschutzgebiet'),
    ('h220', 'W-DE', 90, 'OBJEKT', 'Vogelschutzgebiet_SPA'),
    ('h221', 'W-DE', 775, 'NAME', 'Naturschutzgebiete'),
    ('h222', 'W-DE', 1, 'NAME', 'Nationalpark'),
    ('h223', 'W-DE', 60, 'NAME', 'Vogelschutzgebiete'),
    ('h224', 'W-DE', 582, 'NAME', 'Fauna-Flora-Habitate'),
    ('h225', 'W-DE', 13, 'NAME', 'Naturparke'),
    ('h226', 'W-DE', 390, 'name', 'Fauna-Flora-Habitat-Gebiete (FFH) in Niedersachsen'),
    ('h227', 'W-DE', 850, 'name', 'Naturschutzgebiet'),
    ('h228', 'W-DE', 2498, 'NAME', 'Flaechennaturdenkmaeler'),
    ('h229', 'W-DE', 2, 'NAME', 'Nationalpark'),
    ('h230', 'W-DE', 3, 'NAME', 'Naturpark'),
    ('h231', 'W-DE', 366, 'NAME', 'Naturschutzgebiete'),
]


def parts_for(area, layer):
    chunks = sorted(HAND.glob(f'hand-{area}.{layer}.chunk*.geojson.gz'))
    single = HAND / f'hand-{area}.{layer}.geojson.gz'
    if chunks:
        return chunks
    if single.is_file():
        return [single]
    return []


def recs_of(area, layer):
    paths = parts_for(area, layer)
    recs = []
    for p in paths:
        if WH.parse_hand_chunk_name(p.name):
            # A chunk is not a complete hand name; read features and convert.
            meta, feats = M.read_layer_file(p)
            label = str(meta.get('label') or '')
            url = str(meta.get('url') or '')
            nf = str(meta.get('name_field') or '')
            for f in feats:
                rec = WH.rec_from_feature(f, label, url, nf)
                if WH.rec_has_geometry(rec):
                    recs.append(rec)
        else:
            _, got = WH.recs_from_hand(p)
            recs.extend(got)
    return recs


# --- M4: part cap, only usable geometry ---
check('no merged hand-W-CZ.h218.geojson.gz is committed (chunks only; fill merges at run time)',
      not (HAND / 'hand-W-CZ.h218.geojson.gz').exists())

all_new_parts = []
for layer, area, n, nf, label in NEW:
    paths = parts_for(area, layer)
    all_new_parts.extend(paths)
    check(f'{area}.{layer} has at least one packed part', bool(paths))
    for p in paths:
        check(f'{p.name} is under 1 MB ({p.stat().st_size} bytes)', p.stat().st_size < CAP)
        if WH.parse_hand_chunk_name(p.name):
            got = WH.parse_hand_chunk_name(p.name)
            check(f'{p.name} chunk name parses to {area}|{layer}', got[:2] == (area, layer))
        else:
            check(f'{p.name} name parses to {area}|{layer}', M.parse_hand_name(p.name) == (area, layer))
            why = M.hand_file_problem(p, area, layer)
            check(f'{p.name} passes hand_file_problem', why == '')
        meta, feats = M.read_layer_file(p)
        check(f'{p.name} is source=hand, label={label}, name_field={nf}',
              meta.get('source') == 'hand' and meta.get('label') == label
              and meta.get('name_field') == nf and meta.get('area') == area
              and meta.get('layer') == layer)
        check(f'{p.name} records provenance (person, route, date {DATE}, licence, official page)',
              meta.get('person') == 'Brandon (KPC owner)'
              and meta.get('route') == 'owner hand download'
              and meta.get('date') == DATE
              and bool(WH.hand_licence_text(meta))
              and bool(str(meta.get('page') or '').strip())
              and not any(h in str(meta.get('page') or '').lower() for h in BANNED_PAGE))

# --- usable counts ---
cz_evl = recs_of('W-CZ', 'h218')
de_state = []
de_by_layer = {}
for layer, area, n, nf, label in NEW:
    recs = recs_of(area, layer)
    de_by_layer[layer] = recs
    named = sum(1 for r in recs if r.get('n'))
    # Sachsen FND OBJECTID 675 has usable geometry but no NAME in the owner download; it still counts.
    allow_unnamed = 1 if layer == 'h228' else 0
    check(f'{area}.{layer}: {n} usable records (got {len(recs)}, named {named})',
          len(recs) == n and all(r.get('_bb') or r.get('_r') for r in recs)
          and named == n - allow_unnamed
          and all(r.get('src') == label for r in recs))
    if area == 'W-DE':
        de_state.extend(recs)

check(f'CZ EVL usable count is 1,111 (got {len(cz_evl)})', len(cz_evl) == CZ_EVL)
check(f'DE state usable count is 6,692 (got {len(de_state)})', len(de_state) == DE_STATE)

_, po = WH.recs_from_hand(HAND / 'hand-W-CZ.h217.geojson.gz')
_, hb = WH.recs_from_hand(HAND / 'hand-W-DE.h214.geojson.gz')
check('CZ PO still 42 usable records', len(po) == CZ_PO)
check('DE Bremen still 20 usable records', len(hb) == DE_BREMEN)
check(f'W-CZ baseline from usable geometry is 7,938 (got {CZ_CURRENT + len(po) + len(cz_evl)})',
      CZ_CURRENT + len(po) + len(cz_evl) == CZ_BASELINE == 7938)
check(f'W-DE baseline from usable geometry is 30,616 (got {DE_CURRENT + len(de_state) + len(hb)})',
      DE_CURRENT + len(de_state) + len(hb) == DE_BASELINE == 30616)

# world_current_rec_count on a saved-copy shaped blob
def stub(n, src):
    return [{'_bb': [0, 0, 1, 1], '_r': [[0, 0], [1, 0], [1, 1], [0, 0]], 'src': src, 'id': i} for i in range(n)]

cz_labels = WH.world_source_labels('CZ', ROOT)
de_labels = WH.world_source_labels('DE', ROOT)
check('CZ current labels include PO and EVL',
      'Ptačí oblast (PO)' in cz_labels and 'Evropsky významná lokalita (EVL)' in cz_labels)
for _, area, n, nf, label in NEW:
    if area == 'W-DE':
        check(f'DE current labels include {label}', label in de_labels)

# 6785 stubs use an already-current CZ label (not PO/EVL)
cz_other = next(s for s in cz_labels if s not in ('Ptačí oblast (PO)', 'Evropsky významná lokalita (EVL)'))
de_other = next(s for s in de_labels if s.startswith('BfN '))
cz_blob = {'recs': stub(CZ_CURRENT, cz_other) + po + cz_evl}
de_blob = {'recs': stub(DE_CURRENT, de_other) + hb + de_state}
got_cz = WH.world_current_rec_count('W-CZ', cz_blob, ROOT)
got_de = WH.world_current_rec_count('W-DE', de_blob, ROOT)
check(f'world_current_rec_count(W-CZ) is 7,938 (got {got_cz})', got_cz == 7938)
check(f'world_current_rec_count(W-DE) is 30,616 (got {got_de})', got_de == 30616)

# fill-merge of chunked EVL + all DE state layers into empty copies, then add current-layer stubs
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    M.save_saved(td / 'W-CZ.json.gz', {'cc': 'CZ', 'recs': stub(CZ_CURRENT, cz_other)})
    M.save_saved(td / 'W-DE.json.gz', {'cc': 'DE', 'recs': stub(DE_CURRENT, de_other)})
    # merge EVL chunks to a temp complete file (runtime only; not committed)
    evl_parts = parts_for('W-CZ', 'h218')
    evl_merged = td / 'hand-W-CZ.h218.geojson.gz'
    WH.write_merged_chunks(evl_parts, evl_merged)
    meta_m, _ = M.read_layer_file(evl_merged)
    check('merged EVL temp file has count_expected=1111',
          meta_m.get('count_expected') == 1111 and evl_merged.stat().st_size >= CAP)
    okc, whatc = WH.apply_world_hand_file(HAND / 'hand-W-CZ.h217.geojson.gz', td)
    oke, whate = WH.apply_world_hand_file(evl_merged, td)
    cz_recs = M.load_saved(td / 'W-CZ.json.gz')['recs']
    check(f'fill-merge W-CZ: 6,785 + 42 + 1,111 = 7,938 ({whatc}; {whate})',
          okc and oke and len(cz_recs) == 7938
          and WH.world_current_rec_count('W-CZ', {'recs': cz_recs}, ROOT) == 7938)

    okb, _ = WH.apply_world_hand_file(HAND / 'hand-W-DE.h214.geojson.gz', td)
    applied = [okb]
    for layer, area, n, nf, label in NEW:
        if area != 'W-DE':
            continue
        paths = parts_for(area, layer)
        if WH.parse_hand_chunk_name(paths[0].name):
            dest = td / f'hand-{area}.{layer}.geojson.gz'
            WH.write_merged_chunks(paths, dest)
            okx, _ = WH.apply_world_hand_file(dest, td)
        else:
            okx, _ = WH.apply_world_hand_file(paths[0], td)
        applied.append(okx)
    de_recs = M.load_saved(td / 'W-DE.json.gz')['recs']
    check(f'fill-merge W-DE: 23,904 + 6,692 + 20 = 30,616 (got {len(de_recs)})',
          all(applied) and len(de_recs) == 30616
          and WH.world_current_rec_count('W-DE', {'recs': de_recs}, ROOT) == 30616)

# --- M7: unique hand-* ids, no collisions ---
src = json.loads((ROOT / 'data/outlines/download-sources.json').read_text())['sources']
lay = json.loads((ROOT / 'data/outlines/layers.json').read_text())['layers']
ids = {}
for p in sorted(HAND.iterdir()):
    if not p.name.endswith('.geojson.gz'):
        continue
    got = M.parse_hand_name(p.name) or (WH.parse_hand_chunk_name(p.name) or (None, None, None))[:2]
    if not got or not got[0]:
        check(f'{p.name} is a parseable hand file', False)
        continue
    area, layer = got[0], got[1]
    ids.setdefault(layer, set()).add(area)
check('every hand-* layer id in data/outlines/hand/ belongs to exactly one area',
      all(len(v) == 1 for v in ids.values()))
# source catalog: one area per h218-h231, no reuse of h212-h217
for layer, area, n, nf, label in NEW:
    check(f'download-sources {layer} is only {area}, stated_count={n}',
          (src.get(layer) or {}).get('areas') == [area]
          and (src.get(layer) or {}).get('stated_count') == n)
    check(f'layers.json {area}.{layer} expected_count={n}',
          (lay.get(f'{area}.{layer}') or {}).get('expected_count') == n)
    check(f'{layer} does not collide with h212-h217 (GL/MT/Bremen/PO)',
          layer not in ('h212', 'h213', 'h214', 'h215', 'h217'))
check('h216 stays unused (no collision with a retired MT id)', 'h216' not in src and 'h216' not in ids)
check('h212 remains W-GL, h213 remains W-MT, h214 remains W-DE Bremen, h217 remains W-CZ PO',
      (src.get('h212') or {}).get('areas') == ['W-GL']
      and (src.get('h213') or {}).get('areas') == ['W-MT']
      and (src.get('h214') or {}).get('areas') == ['W-DE']
      and (src.get('h217') or {}).get('areas') == ['W-CZ'])

# --- M8: catalogue provenance per agency ---
for layer, area, n, nf, label in NEW:
    s = src.get(layer) or {}
    L = lay.get(f'{area}.{layer}') or {}
    check(f'{layer} catalogue records person, route, date, terms, official page',
          s.get('person') == 'Brandon (KPC owner)' and s.get('route') == 'owner hand download'
          and s.get('date') == DATE and bool(s.get('terms') or s.get('license'))
          and bool(s.get('page')) and not any(h in str(s.get('page') or '').lower() for h in BANNED_PAGE)
          and L.get('person') == 'Brandon (KPC owner)' and bool(L.get('license'))
          and bool(L.get('page')) and not any(h in str(L.get('page') or '').lower() for h in BANNED_PAGE))

# --- no POTA pin moved ---
# World POTA pins live in data/pota/t/*.json (index.json is counts only). US pins are in locations.json.
# The key files record the join, not a moved pin (c is empty; bk[1] is km from POTA's pin).
pin_files = [ROOT / 'locations.json', ROOT / 'data/pota-pin-changes.json',
             ROOT / 'data/world-key/CZ.json', ROOT / 'data/world-key/DE.json']
pin_files += sorted((ROOT / 'data/pota/t').glob('*.json'))
pin_files.append(ROOT / 'data/pota/index.json')

def collect_world_pins():
    out = []
    tdir = ROOT / 'data/pota/t'
    for p in sorted(tdir.glob('*.json')):
        rows = json.loads(p.read_text())
        for r in rows if isinstance(rows, list) else []:
            if isinstance(r, list) and len(r) >= 4 and isinstance(r[0], str) and r[0].startswith(('CZ-', 'DE-')):
                out.append((r[0], r[2], r[3]))
    return out

def file_digest(paths):
    h = hashlib.sha256()
    for p in paths:
        h.update(p.as_posix().encode())
        h.update(b'\0')
        h.update(p.read_bytes())
    return h.hexdigest()

before = file_digest(pin_files)
pins = collect_world_pins()
# apply hands in a temp cache; pin files on ROOT must be untouched
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    M.save_saved(td / 'W-CZ.json.gz', {'cc': 'CZ', 'recs': []})
    evl_merged = td / 'hand-W-CZ.h218.geojson.gz'
    WH.write_merged_chunks(parts_for('W-CZ', 'h218'), evl_merged)
    WH.apply_world_hand_file(HAND / 'hand-W-CZ.h217.geojson.gz', td)
    WH.apply_world_hand_file(evl_merged, td)
after = file_digest(pin_files)
pins_after = collect_world_pins()
check('POTA pin stores (data/pota, pota-pin-changes, locations.json, CZ.json, DE.json) are unchanged after applying the hand files',
      before == after)
check(f'every CZ- and DE- POTA pin in data/pota/t is unchanged ({len(pins)} pins)',
      pins == pins_after and len(pins) >= 232 + 1265)

# --- no water-only outlines ---
# All packed features are land-capable polygons with usable rings; no Point/Line water leftovers.
waterish = 0
nopoly = 0
zero = 0
for p in all_new_parts:
    meta, feats = M.read_layer_file(p)
    for f in feats:
        g = (f or {}).get('geometry') or {}
        typ = g.get('type')
        if typ not in ('Polygon', 'MultiPolygon'):
            nopoly += 1
        rec = WH.rec_from_feature(f, meta.get('label') or '', meta.get('url') or '', meta.get('name_field') or '')
        if typ in ('LineString', 'MultiLineString', 'Point', 'MultiPoint'):
            waterish += 1
        if WH.rec_has_geometry(rec):
            rs = rec.get('_r') or []
            if not rs and not rec.get('_bb'):
                zero += 1
        else:
            zero += 1
        props = (f or {}).get('properties') or {}
        typv = str(props.get('SCHUTZSTATUS') or props.get('kategorie') or props.get('KAT') or props.get('TYPE') or '')
        if typv.lower() in ('water', 'gewässer', 'wasserkörper', 'inland water'):
            waterish += 1
check(f'no water-only or non-polygon outlines in the new hand files (nopoly={nopoly}, waterish={waterish}, unusable={zero})',
      nopoly == 0 and waterish == 0 and zero == 0)
check('every usable CZ EVL and DE state record has a bbox or ring (not a water-only leftover)',
      all((r.get('_bb') or r.get('_r')) for r in cz_evl + de_state + po + hb))

# caches still declare the published baselines
caches = json.loads((ROOT / 'data/outlines/layers.json').read_text())['caches']
check('layers.json caches declare W-CZ expected_count=7938 and W-DE=30616',
      (caches.get('W-CZ') or {}).get('expected_count') == 7938
      and (caches.get('W-DE') or {}).get('expected_count') == 30616)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
