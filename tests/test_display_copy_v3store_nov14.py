#!/usr/bin/env python3
"""The display-copy builder on a store made by the REAL outline store tool, full 3 (KPC owner, 2026-11-14). OPT-IN: set
KPC_STORE_TOOL_DIR to an unzipped copy of the store tool (kpc-outline-store-full, unchanged); without it this test only says
SKIP. The store tool builds its store in a temporary folder from its OWN offline test answers (its fake map servers on
127.0.0.1, its tests/fixtures); nothing it makes is kept, and no shape is written into this repository. No network."""
import json, os, pathlib, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import kpc_display_copy as K  # noqa: E402

RESULTS = []


def check(ok, what):
    RESULTS.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + what, flush=True)


# A small helper run in a child process: it imports the store tool's own offline test helpers and builds one store.
HELPER = r'''
import sys, pathlib
tests = pathlib.Path(sys.argv[1]) / 'tests'; sys.path.insert(0, str(tests))
import test_store_full as S
out, mode = pathlib.Path(sys.argv[2]), sys.argv[3]
A, B = S.servers()
try:
    ver = []
    for u in S.FIX['layers']:
        if 'nhgeodata' in u and mode != 'none':
            ver.append([u.replace('https://nhgeodata.unh.edu', f'http://127.0.0.1:{A.port}').replace('/query', ''), 'US:t', 'yes', 'yes',
                        'PUBLIC DOMAIN' if 'CSD_' in u else 'NO TERMS STATED', 't', 'https://example.org/terms', '2026-11-14', 'Test agency'])
        if 'nationalmap' in u and mode == 'all':
            ver.append([u.replace('https://edits.nationalmap.gov', f'http://127.0.0.1:{B.port}').replace('/query', ''), 'US:t', 'yes', 'yes',
                        'PUBLIC DOMAIN', 't', 'https://example.org/terms', '2026-11-14', 'USGS PAD-US'])
    tl = S.tool_copy(out, A, B, verified=ver, extra_ca=True)
    rc1, o1 = S.run(tl, ['fetch', '--go'], {'KPC_TEST_FAST': '1'})
    rc2, o2 = S.run(tl, ['build'])
    print('RC', rc1, rc2)
finally: A.close(); B.close()
'''


def main():
    tool = os.environ.get('KPC_STORE_TOOL_DIR', '')
    if not tool or not (pathlib.Path(tool) / 'kpc_outline_store.py').is_file() or not (pathlib.Path(tool) / 'tests' / 'test_store_full.py').is_file():
        print('SKIP: set KPC_STORE_TOOL_DIR to an unzipped store tool (full 3) to run this test'); print('ALL PASS'); return 0
    tool = pathlib.Path(tool).resolve()
    env = {k: v for k, v in os.environ.items() if k.lower() not in ('http_proxy', 'https_proxy', 'all_proxy', 'ftp_proxy')}
    env['NO_PROXY'] = env['no_proxy'] = '127.0.0.1,localhost'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-v3store-'))
    try:
        lc = json.loads((tool / 'licence-classes.json').read_text(encoding='utf-8'))
        mine = json.loads(K.LICENCE_CLASSES_FILE.read_text(encoding='utf-8'))
        check(lc == mine, "the builder's licence class list is the store tool's licence-classes.json, word for word")
        hp = tmp / 'helper.py'; hp.write_text(HELPER, encoding='utf-8')
        stores = {}
        for mode in ('none', 'state', 'all'):
            p = subprocess.run([sys.executable, '-I', '-B', str(hp), str(tool), str(tmp / mode), mode], env=env, capture_output=True, text=True, timeout=900)
            stores[mode] = tmp / mode / 'tool' / 'results' / 'store'
            check('RC 0 0' in p.stdout and (stores[mode] / 'index-US-NH.json').is_file(), f'the real store tool built a store offline ({mode} layers verified)')
        ix = json.loads((stores['state'] / 'index-US-NH.json').read_text(encoding='utf-8'))
        check(ix.get('store_format_version') == 'kpc-outline-store-index/3' and K.store_format(ix) == 3, 'its per-area index says kpc-outline-store-index/3')
        tbl = {K.norm_layer_url(k) for k in ix.get('layers') or {}}
        miss = []
        for ref, e in ix['parks'].items():
            for key, m in e['record_meta'].items():
                if K.norm_layer_url(m['source_url']) not in tbl: miss.append(key)
        check(not miss and all('://' not in k for k in ix['layers']), f'every record finds its row in the layer table (store keys have no https://; missing: {miss or "none"})')
        rep = {}
        for mode in stores:
            out = tmp / ('out-' + mode)
            rep[mode] = K.build(stores[mode], ['US-NH', 'CA-ZZ'], out, log=lambda *a: None)
            probs = K.check(out, 'US-NH', public=True) + K.check(out, 'CA-ZZ', public=True)
            check(not probs and not rep[mode]['invariant_failures'], f'{mode}: public build passes its own public check, 0 invariant failures ({rep[mode]["parks_drawn"]} parks drawn)')
            wd = [r for r, why in rep[mode]['fallback_reasons'].items() if 'WDPA' in why]
            check(not wd, f'{mode}: no record is taken for WDPA (every v3 record has a field NAMED wdpa_derived; it is false)')
        check(rep['none']['parks_drawn'] == 0, 'nothing verified: nothing drawn, every park keeps today\'s outline')
        ixn = {r: e for r, e in ix['parks'].items() if e.get('park_publishable')}
        check(rep['state']['parks_drawn'] == len(ixn) > 0, f'state layers verified, PAD-US not: exactly the parks the store calls publishable as a whole are drawn ({len(ixn)})')
        pd = [r for r, e in ix['parks'].items() if e.get('park_publishable') and any(m['licence_class'] == 'PUBLIC DOMAIN' for m in e['record_meta'].values())]
        check(pd and not set(pd) & set(rep['state']['fallback_reasons']), f'PUBLIC DOMAIN records are drawn ({len(pd)} park(s))')
        ixa = json.loads((stores['all'] / 'index-US-NH.json').read_text(encoding='utf-8'))
        na = sum(1 for e in ixa['parks'].values() if e.get('park_publishable'))
        check(rep['all']['parks_drawn'] >= na > rep['state']['parks_drawn'], f'PAD-US verified too: more parks drawn ({rep["all"]["parks_drawn"]}, store says {na} in US-NH)')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print('ALL PASS' if all(RESULTS) else f'FAILED {RESULTS.count(False)} of {len(RESULTS)}')
    return 0 if all(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())
