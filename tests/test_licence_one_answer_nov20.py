#!/usr/bin/env python3
"""ONE licence answer per layer. kpc_master.share_block reads data/outlines/licence-verdicts.csv first
(the store's researched table, copied): publish=no blocks, publish=yes passes; the layer address decides, a key id only when it names
one row; a placeholder 'see the source page' is not a licence; the Army Corps layers are allowed, with their credit. Invented rows and the real file.
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
    _c = M.licence_code
    (d / 'licence-verdicts.csv').write_text(
        '# test\nlayer,key id,publish,licence class,credit line,date read\n'
        f"{_c('https://x.example/a/FeatureServer/0')},US:sgzza,yes,PUBLIC DOMAIN,Example agency,2026-11-18\n"
        f"{_c('https://x.example/b/FeatureServer/0')},US:sgzzb,no,OTHER RESTRICTED,,2026-11-18\n"
        f"{_c('https://x.example/c/FeatureServer/0')},CA:Hard look~1,yes,OPEN,,\n"
        f"{_c('https://x.example/d/FeatureServer/0')},CA:Hard look~2,no,NOT FOUND,,\n", encoding='utf-8')
    (d / 'download-sources.json').write_text(json.dumps({'sources': {'h1': {'layer_url': 'https://x.example/e/FeatureServer/0', 'terms': 'see the source page'}}}))
    sb = lambda url, lay: M.share_block({'area': 'US-ZZ', 'layer': lay, 'url': url}, d)
    check(sb('https://x.example/a/FeatureServer/0/query', 'sgzza') == '', 'publish=yes passes (the address, /query ignored)')
    check('licence verdict no' in sb('https://x.example/b/FeatureServer/0', 'sgzzb'), 'publish=no blocks, with its licence class')
    check(M.licence_code('https://X.example/a/FeatureServer/0/query') == M.licence_code('https://x.example/a/featureserver/0/'), 'the code ignores case, /query and a trailing slash, as the keeper does')
    _pub = (ROOT / 'data/outlines/licence-verdicts.csv').read_text(encoding='utf-8').lower()
    check('/rest/services/' not in _pub and 'noreader://' not in _pub and 'featureserver' not in _pub and 'mapserver' not in _pub, 'the public file holds no layer address (only coded ones)')
    check('licence verdict no' in sb('', 'sgzzb'), 'a hand file with no address: its key id decides when it names one row')
    check(sb('https://x.example/c/FeatureServer/0', 'Hard look') == '' and 'verdict no' in sb('https://x.example/d/FeatureServer/0', 'Hard look'),
          'the address decides before a key id that names several rows')
    check('no licence or terms recorded' in sb('', 'Hard look'), 'a key id naming several rows decides nothing (old rule: no licence = blocked)')
    check('no licence or terms recorded' in sb('https://x.example/e/FeatureServer/0', 'sgzze'), "'see the source page' is not a licence")
    check('no licence or terms recorded' in sb('https://x.example/f/FeatureServer/0', 'sgzzf'), 'a layer in neither table stays blocked')

# both Army Corps layers allowed, credit "US Army Corps of Engineers data"
for lay in ('sgide', 'usaceproj'):
    real = M.licence_verdict('', lay, ROOT / 'data/outlines')
    check(real is not None and real[0] is True and 'US Army Corps of Engineers data' in real[1], f'the real file: the Army Corps layer {lay} is allowed, with its credit')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
