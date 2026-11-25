#!/usr/bin/env python3
"""25 Nov 2026 (KPC-Links #380 grade, must-fix): the outline cutter (kpc_outlines_from_key.py) cuts each park's outline by id
from the OLD saved copy. A key built from the outline store's own records (KPC_STORE_FRESH) lists those ids in 'fresh_store':
the same number in the saved copy can be other land (fresh sgmnc210 = Lost Valley Prairie; old 210 = another place, about
140 miles off). A park with a fresh record is skipped (fail closed), never cut from the saved copy. Invented records.
Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import gzip, json, pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_outlines_from_key as O  # noqa: E402

ok = True
# the test is about WHICH records are cut, not the cutting: the shape union is replaced by a plain one (no shapely needed)
O.union_geometry = lambda rs: ({'type': 'Polygon', 'coordinates': [[list(p) for p in (rs[0].get('_r') or [[]])[0]]]}, '')
import kpc_master  # noqa: E402,F401
O.M.trim_geometry = lambda g: g


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


def sq(x, y, d):
    return [[[x, y], [x + d, y], [x + d, y + d], [x, y + d], [x, y]]]


with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    cache, keys, outl = t / 'cache', t / 'keys', t / 'outlines'
    for d in (cache, keys, outl): d.mkdir()
    # the OLD saved copy: its 210 is other land far away; its 55 is Lost Valley Prairie
    old = {'st': 'ZZ', 'saved': '2026-11-12', 'recs': [
        {'OBJECTID': 'sgzzc210', 'Unit_Nm': 'Crystal Spring', 'GIS_Acres': 40, 'Loc_Mang': 'ZZ DNR', '_r': sq(-94.70, 46.70, 0.003)},
        {'OBJECTID': 'sgzzc55', 'Unit_Nm': 'Lost Valley Prairie', 'GIS_Acres': 216, 'Loc_Mang': 'ZZ DNR', '_r': sq(-92.83, 44.80, 0.01)}]}
    with gzip.open(cache / 'US-ZZ.json.gz', 'wt', encoding='utf-8') as f: json.dump(old, f)

    def key(fresh):
        k = {'st': 'ZZ', 'parks': {
            'US-9001': {'n': 'Lost Valley Prairie SNA', 'g': 'official', 'm': [['sgzzc210', 'Lost Valley Prairie', 216, 'name']]},
            'US-9002': {'n': 'Lost Valley Prairie (old ids)', 'g': 'official', 'm': [['sgzzc55', 'Lost Valley Prairie', 216, 'name']]}}}
        if fresh: k['fresh_store'] = {'about': 'test', 'ids': ['sgzzc210']}
        (keys / 'US-ZZ.json').write_text(json.dumps(k))

    key(fresh=False)
    added, skipped = O.build_state('ZZ', cache, dry=True, root=outl, key_dir=keys, say=lambda *a: None)
    check('control: with no fresh list the cutter takes 210 from the saved copy (the wrong land the grade found)',
          'US-9001' in {r['ref'] for r in added})
    key(fresh=True)
    added, skipped = O.build_state('ZZ', cache, dry=True, root=outl, key_dir=keys, say=lambda *a: None)
    sk = dict(skipped)
    check('a park joined to a fresh store record is never cut from the saved copy (no store given: fail closed)',
          'US-9001' not in {r['ref'] for r in added} and 'fresh store records' in sk.get('US-9001', ''))
    check('a park joined only to saved-copy records is still cut as before', 'US-9002' in {r['ref'] for r in added})

def enc(ring, q=6):   # the store's ring spelling: first point, then steps, as q-digit integers
    m = 10 ** q; pts = [(round(x * m), round(y * m)) for x, y in ring]
    out = [pts[0][0], pts[0][1]]
    for (a, b), (c, d) in zip(pts, pts[1:]): out += [c - a, d - b]
    return out


def store_file(folder, publishable=True):
    park = {'ref': 'US-9001', 'records': [
        {'key': 'sgzzc@210', 'layer': 'sgzzc', 'record_id': '210', 'record_name': 'Lost Valley Prairie', 'q': 6, 'agency_label': 'ZZ DNR (store)',
         'read': '2026-11-21T10:00:00-06:00', 'publishable': publishable, 'rings': [enc(sq(-92.83, 44.80, 0.01)[0])]}]}
    with gzip.open(folder / 'US-ZZ.kpcstore.json.gz', 'wt', encoding='utf-8') as f: json.dump({'area': 'US-ZZ', 'parks': [park]}, f)


with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    cache, keys, outl, store = t / 'cache', t / 'keys', t / 'outlines', t / 'store'
    for d in (cache, keys, outl, store): d.mkdir()
    with gzip.open(cache / 'US-ZZ.json.gz', 'wt', encoding='utf-8') as f:
        json.dump({'st': 'ZZ', 'saved': '2026-11-12', 'recs': [
            {'OBJECTID': 'sgzzc210', 'Unit_Nm': 'Crystal Spring', 'GIS_Acres': 40, '_r': sq(-94.70, 46.70, 0.003)}]}, f)
    (keys / 'US-ZZ.json').write_text(json.dumps({'st': 'ZZ', 'fresh_store': {'ids': ['sgzzc210']}, 'parks': {
        'US-9001': {'n': 'Lost Valley Prairie SNA', 'g': 'official', 'm': [['sgzzc210', 'Lost Valley Prairie', 216, 'name']]}}}))
    store_file(store)
    added, skipped = O.build_state('ZZ', cache, dry=True, root=outl, key_dir=keys, say=lambda *a: None, store=store)
    r = {x['ref']: x for x in added}.get('US-9001') or {}
    txt = json.dumps(r)
    check('a fresh park is cut from the STORE outline (the right land, near -92.83), marked store:, read date from the store',
          bool(r) and '-92.83' in txt and '-94.7' not in txt and 'store:US-ZZ.kpcstore.json.gz' in txt and '2026-11-21' in txt)
    store_file(store, publishable=False)
    added, skipped = O.build_state('ZZ', cache, dry=True, root=outl, key_dir=keys, say=lambda *a: None, store=store)
    check('a store record that is not publishable: not cut, listed (fail closed)',
          not added and 'not publishable' in dict(skipped).get('US-9001', ''))
    # an OLD outline already in the file for this park (cut from the old copy, same record number) is dropped, not kept
    M = O.M
    rec_old = M.make_record('US-9001', 'Lost Valley Prairie SNA', 'official', {'type': 'Polygon', 'coordinates': [sq(-94.70, 46.70, 0.003)[0]]},
                            'ZZ DNR', 'file:US-ZZ.json.gz', ['sgzzc210'], 0, '2026-11-12', '', 'key', layers=['sgzzc'])
    saved = {}
    M.load_area = lambda area, root=None: {'US-9001': rec_old}
    M.save_area = lambda area, out, root, key_dir=None: saved.update({'out': dict(out)})
    M.pin_drops = lambda *a, **k: set(); M.not_in_key_drops = lambda *a, **k: set(); M.area_files = lambda *a, **k: []
    added, skipped = O.build_state('ZZ', cache, dry=False, root=outl, key_dir=keys, say=lambda *a: None, store=store)
    check("the old outline of a fresh park that cannot be cut from the store is DROPPED, never kept (it may hold other land)",
          'out' in saved and 'US-9001' not in saved['out'])
    store_file(store, publishable=True)
    added, skipped = O.build_state('ZZ', cache, dry=False, root=outl, key_dir=keys, say=lambda *a: None, store=store)
    check('with the store record publishable the old outline (same record number) is rebuilt from the store',
          'store:' in json.dumps(saved['out'].get('US-9001') or {}) and '-94.7' not in json.dumps(saved['out'].get('US-9001') or {}))

# the report-only tools: kpc_master.joined_missing and kpc_outline_score
import importlib, os, subprocess  # noqa: E402
KM = importlib.import_module('kpc_master')
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    kp = t / 'US-ZZ.json'
    kp.write_text(json.dumps({'fresh_store': {'ids': ['sgzzc210', '207720']}, 'parks': {
        'US-9001': {'m': [['sgzzc210', 'x', 1, 'name'], ['207720', 'y', 1, 'name'], ['sgzzc77', 'z', 1, 'name']]}}}))
    check('joined_missing never counts a fresh store id as missing from the saved copy (only the real gap, sgzzc77)',
          KM.joined_missing(kp, {'recs': [{'OBJECTID': 'sgzzc210'}]}) == {'sgzzc': 1})
    # outline score: a fresh PAD-US id is scored against the STORE record, not the old copy's record of that number
    (t / 'data' / 'us-key').mkdir(parents=True); (t / 'data' / 'parkinfo').mkdir(); (t / 'cache').mkdir(); (t / 'store').mkdir()
    (t / 'data' / 'us-key' / 'US-ZZ.json').write_text(json.dumps({'fresh_store': {'ids': ['207720']}, 'parks': {
        'US-9003': {'n': 'Alpha National Wildlife Refuge', 't': 'National Wildlife Refuge', 'm': [[207720, 'Alpha National Wildlife Refuge', 500, 'name']]}}}))
    with gzip.open(t / 'cache' / 'US-ZZ.json.gz', 'wt') as f:
        json.dump({'recs': [{'OBJECTID': 207720, 'Unit_Nm': 'Somewhere Else Park', 'Mang_Name': 'CITY', 'Mang_Type': 'LOC', '_r': sq(-80, 30, 0.01)}]}, f)
    with gzip.open(t / 'store' / 'US-ZZ.kpcstore.json.gz', 'wt') as f:
        json.dump({'parks': [{'records': [{'key': '207720', 'layer': 'PAD-US', 'record_id': '207720', 'q': 6, 'rings': [enc(sq(-92.8, 44.8, 0.01)[0])],
                                           'attributes': {'Unit_Nm': 'Alpha National Wildlife Refuge', 'Mang_Name': 'FWS', 'Mang_Type': 'FED', 'GIS_Acres': 500}}]}]}, f)
    env = dict(os.environ, GEO_CACHE=str(t / 'cache'), KPC_STORE_DIR=str(t / 'store'))
    subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_outline_score.py')], cwd=t, env=env, capture_output=True, text=True)
    sc = json.loads((t / 'data' / 'boundary-score.json').read_text())['parks'].get('US-9003') or ['', '', '', '']
    check("the outline score reads a fresh id's agency from the store (FWS: agency 1/1), not the old copy's record of that number",
          'agency 1/1' in sc[3])

src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
check("the US key writes the fresh ids into the key file ('fresh_store') when KPC_STORE_FRESH is on",
      "out['fresh_store']" in src and "_kr('KPC_STORE_FRESH')" in src)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
