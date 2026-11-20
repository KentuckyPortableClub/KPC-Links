#!/usr/bin/env python3
"""ONE licence answer per layer (Opus, 20 Nov 2026; REPAIRS R14). kpc_master.share_block reads data/outlines/licence-verdicts.csv first
(the store's researched table, copied): publish=no blocks, publish=yes passes; the layer address decides, a key id only when it names
one row; a placeholder 'see the source page' is not a licence; the Army Corps layers are held by the owner. Invented rows and the real file.
Run:  python3 tests/test_licence_one_answer_nov20.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import pathlib, sys, tempfile, json
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as M  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

with tempfile.TemporaryDirectory() as d:
    d = pathlib.Path(d)
    (d / 'licence-verdicts.csv').write_text(
        '# test\nlayer address,key id,publish,why,evidence URL,date read\n'
        'https://x.example/a/FeatureServer/0,US:sgzza,yes,PUBLIC DOMAIN: yes,https://x.example/terms,2026-11-18\n'
        'https://x.example/b/FeatureServer/0,US:sgzzb,no,OTHER RESTRICTED: no (terms forbid redistribution),https://x.example/t,2026-11-18\n'
        'https://x.example/c/FeatureServer/0,CA:Hard look~1,yes,OPEN: yes,,\n'
        'https://x.example/d/FeatureServer/0,CA:Hard look~2,no,NOT FOUND: no,,\n', encoding='utf-8')
    (d / 'download-sources.json').write_text(json.dumps({'sources': {'h1': {'layer_url': 'https://x.example/e/FeatureServer/0', 'terms': 'see the source page'}}}))
    sb = lambda url, lay: M.share_block({'area': 'US-ZZ', 'layer': lay, 'url': url}, d)
    check(sb('https://x.example/a/FeatureServer/0/query', 'sgzza') == '', 'publish=yes passes (the address, /query ignored)')
    check('licence verdict no' in sb('https://x.example/b/FeatureServer/0', 'sgzzb'), 'publish=no blocks, with its reason')
    check('licence verdict no' in sb('', 'sgzzb'), 'a hand file with no address: its key id decides when it names one row')
    check(sb('https://x.example/c/FeatureServer/0', 'Hard look') == '' and 'verdict no' in sb('https://x.example/d/FeatureServer/0', 'Hard look'),
          'the address decides before a key id that names several rows')
    check('no licence or terms recorded' in sb('', 'Hard look'), 'a key id naming several rows decides nothing (old rule: no licence = blocked)')
    check('no licence or terms recorded' in sb('https://x.example/e/FeatureServer/0', 'sgzze'), "'see the source page' is not a licence")
    check('no licence or terms recorded' in sb('https://x.example/f/FeatureServer/0', 'sgzzf'), 'a layer in neither table stays blocked')

real = M.licence_verdict('', 'sgide', ROOT / 'data/outlines')
check(real is not None and real[0] is False and 'HELD by the KPC owner' in real[1], 'the real file: the Army Corps recreation areas are held by the owner')
real = M.licence_verdict('', 'usaceproj', ROOT / 'data/outlines')
check(real is not None and real[0] is False, 'the real file: the Army Corps projects (Mississippi) are held too')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
