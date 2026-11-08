#!/usr/bin/env python3
"""Nov 8 (follow-up to #94): FULL RULES CHECK uses the place's state-layer facts (owner, manager, designation, website) with
'sources differ'; Kentucky's own official layers are search sources too (they were missing: no US-KY key, so no 'sgky' rows)."""
import json, re, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
rj = (ROOT / 'kpc-maprep-research.js').read_text(encoding='utf-8'); cj = (ROOT / 'kpc-maprep-check.js').read_text(encoding='utf-8')
reg = json.loads((ROOT / 'data/maprep-state-layers.json').read_text(encoding='utf-8'))
KY = reg['areas'].get('KY') or []
ks = {x['k'] for x in KY}
check(ks == {'bstate', 'bwma', 'bsnp', 'bsna', 'bwild', 'bdbnfo', 'bnps', 'bwilder', 'bfws'}, 'Kentucky official layers are search sources (%d)' % len(KY))
check(not ks & {'bpad', 'bkpc', 'bdbnf'}, 'PAD-US copy, OpenStreetMap drawings and the forest boundary line are left out')
check(all(x['ok'] and x['local'] == 'ky' and (ROOT / x['url']).exists() and not x['url'].startswith('http') for x in KY), 'KY layers are our own site files (no outside server, no robots question)')
for x in KY:
    n = len(json.loads((ROOT / x['url']).read_text(encoding='utf-8'))['features']); check(n == x['count'], x['url'] + ' count %d' % n)
check(next(x for x in KY if x['k'] == 'bwma').get('owners') == 'data/ky-wma-owners.json', 'WMA owners come from the KDFWR owners file')
check('ky_note' in reg and 'US-KY' in reg['ky_note'], 'the registry says why Kentucky was missing')
check('o.L.local ? await slLocal(o.L, kind, arg)' in rj and "/^[\\w.-]+\\.geojson$/.test(L.url)" in rj, 'local layers read only same-site .geojson files')
check("kpc_maprep_state_layers" and "out['KY'] = kyr" in (ROOT / '.github/scripts/kpc_maprep_state_layers.py').read_text(encoding='utf-8'), 'a rebuild keeps the Kentucky rows')
check('W.KPCMapCheck.setPlaceFacts(placeFacts(p))' in rj and 'function placeFacts(p)' in rj, 'FULL RULES CHECK hands over the place facts')
check('function setPlaceFacts(h)' in cj and 'ctx.stateFacts = H.facts' in cj and "H && H.html ? H.html : ''" in cj, 'the full check uses them and shows the facts block (sources differ)')
check("sDes ? 'designation field on ' + SF.designation.src" in cj, 'designation rule can use the state-layer designation')
check('120000' in cj and 'h.box' in cj, 'facts only for that place, 2 minutes')
for f in ('kpc-maprep.html', 'kpc-maprep-reps.html', '.claude/build/maprep/main.html'):
    h = (ROOT / f).read_text(encoding='utf-8')
    check('kpc-maprep-research.js?v=20261108v' in h and 'kpc-maprep-check.js?v=20261108v' in h, f + ': new script versions')
sys.exit(0 if ok else 1)
