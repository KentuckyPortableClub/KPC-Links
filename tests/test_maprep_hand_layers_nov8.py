#!/usr/bin/env python3
"""Nov 8: hand-downloaded GA / TX / PA / MB layers are Tool Box search sources (local site files; no live robots-blocked hosts)."""
import json, pathlib, sys, re
ROOT = pathlib.Path(__file__).resolve().parents[1]; ok = True
def check(c, m):
    global ok; print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
reg = json.loads((ROOT / 'data/maprep-state-layers.json').read_text(encoding='utf-8'))
need = {'GA': {'gas','gaw'}, 'TX': {'txs','txw'}, 'PA': {'pas'}, 'MB': {'mbp'}}
for st, ks in need.items():
    got = {x['k'] for x in reg['areas'].get(st, []) if x.get('local') == 'hand' and x.get('ok')}
    check(ks <= got, f'{st} hand layers present ({got})')
    for x in reg['areas'][st]:
        if x.get('local') != 'hand': continue
        check((ROOT / x['url']).is_file() and not x['url'].startswith('http'), x['url'] + ' is a site file')
        check(len(json.load(open(ROOT / x['url']))['features']) == x['count'], x['url'] + ' count')
js = (ROOT / 'kpc-maprep-research.js').read_text(encoding='utf-8')
check('o.L.local ? await slLocal' in js, 'local layers are read by slLocal')
check(not any(x['ok'] and 'services1.arcgis.com/1mtXwieMId59thmg' in x.get('url','') for a in reg['areas'].values() for x in a), 'no live TPWD services1.arcgis.com layer is used')
for f in ('kpc-maprep.html', 'kpc-maprep-reps.html', '.claude/build/maprep/main.html'):
    h = (ROOT / f).read_text(encoding='utf-8')
    check(re.search(r'kpc-maprep-research\.js\?v=(\w+)', h).group(1) >= '20261108y', f + ': script version')
sys.exit(0 if ok else 1)
