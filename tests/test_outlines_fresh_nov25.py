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
    check('a park joined to a fresh store record is never cut from the saved copy (fail closed)',
          'US-9001' not in {r['ref'] for r in added} and 'fresh store records' in sk.get('US-9001', ''))
    check('a park joined only to saved-copy records is still cut as before', 'US-9002' in {r['ref'] for r in added})

src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
check("the US key writes the fresh ids into the key file ('fresh_store') when KPC_STORE_FRESH is on",
      "out['fresh_store']" in src and "_kr('KPC_STORE_FRESH')" in src)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
