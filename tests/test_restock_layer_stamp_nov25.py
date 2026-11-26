#!/usr/bin/env python3
"""25 Nov 2026 (the owner's 11:40 AM MN test): the 'Restock stamps' line showed only the Nov 12 saved copy, so the run looked
stale. It now also names the full layer file the build read (KPC-Store's <area>.layer-records.json.gz): its 'made' stamp and
the file's own date. Invented files only. Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import gzip, json, os, pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_confirm_report as CR  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    cache, store = td / 'cache', td / 'store'
    cache.mkdir(); store.mkdir()
    with gzip.open(cache / 'US-ZZ.json.gz', 'wt', encoding='utf-8') as f: json.dump({'saved': '2026-11-12', 'recs': []}, f)
    with gzip.open(store / 'US-ZZ.layer-records.json.gz', 'wt', encoding='utf-8') as f: json.dump({'area': 'US-ZZ', 'made': '2026-11-25T11:31', 'layers': {}}, f)
    os.utime(store / 'US-ZZ.layer-records.json.gz', (1795620000, 1795620000))
    os.environ.pop('KPC_LAYER_RECORDS_DIR', None)
    s0 = CR.restock_stamp('ZZ', str(cache))
    check(f'no layer files given: the saved-copy stamp as before ({s0})', s0.startswith('saved 2026-11-12 ') and 'layer file' not in s0)
    s1 = CR.restock_stamp('ZZ', str(cache), store_dir=str(store))
    check(f"PC test (store folder): the layer file's made stamp and file date are named ({s1})",
          s1.startswith('saved 2026-11-12 ') and '; layer file made 2026-11-25T11:31 (file date ' in s1)
    s2 = CR.restock_stamp('ZZ', str(cache), layer_files={'US-ZZ': {'file': 'US-ZZ.layer-records.json.gz', 'sha256': 'x', 'made': '2026-11-25T11:31'}})
    check(f"key build (store id fields file): the made stamp from its layer_files ({s2})", s2.endswith('; layer file made 2026-11-25T11:31'))
    s3 = CR.restock_stamp('YY', str(cache), layer_files={})
    check(f'an area with no layer file says so ({s3})', s3 == 'no layer file')
    lines = CR.header_lines(root=ROOT, facts_path='', cache_dir=str(cache), states=['ZZ'], last_rules='x', store_dir=str(store))
    check('the header line carries both dates', any(x.startswith('Restock stamps: ZZ saved 2026-11-12 ') and 'layer file made 2026-11-25T11:31' in x for x in lines))
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
kt = (ROOT / 'tools/pc-keys/kpc_test_keys.py').read_text(encoding='utf-8')
check('the key and the PC test pass the layer files to the stamp',
      'layer_files=_lfs' in src and 'CR.restock_stamp(st, layer_files=' in src and 'store_dir=str(STORE)' in kt)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
