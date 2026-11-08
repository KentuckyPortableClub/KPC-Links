#!/usr/bin/env python3
"""Nov 8 (Brandon 8:26 / 8:27 AM CST): Tool Box leftovers. 1 huge multi-part shapes are clipped to the parts near the view (whole
shape kept); 2 Club layers for this state from the existing indexes; 3 Research on this place (no mention of bots in the page);
4 the stale 'off by default' comment is fixed."""
import json, pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
js = r"""
global.fetch = p => Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(require('fs').readFileSync(p, 'utf8'))) });
global.KPCMapLogic = require('./kpc-maprep-logic.js');
const X = require('./kpc-maprep-extras.js');
const sq = (x, y) => [[[x, y], [x + .01, y], [x + .01, y + .01], [x, y]]];
const parts = []; for (let i = 0; i < 40; i++) parts.push(sq(-85 + i * 0.5, 37));
const fc = { type: 'FeatureCollection', features: [{ type: 'Feature', properties: {}, geometry: { type: 'MultiPolygon', coordinates: parts } }, { type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: sq(-85, 37) } }] };
const c = X.clipFC(fc, 37, -85);
const small = X.clipFC({ type: 'FeatureCollection', features: [{ type: 'Feature', properties: {}, geometry: { type: 'MultiPolygon', coordinates: parts.slice(0, 3) } }] }, 37, -85);
(async () => {
  const va = await X.clubLayers('VA'), co = await X.clubLayers('CO');
  const rs = await X.research('US-0150');
  console.log(JSON.stringify({ clipped: c.clipped, kept: c.fc.features[0].geometry.coordinates.length, whole: fc.features[0].geometry.coordinates.length, poly: c.fc.features[1].geometry.type,
    small: small.clipped, va: va.layers.map(l => l.id), co: co.layers.map(l => l.id), coCamps: (co.layers.find(l => l.id === 'camps') || {}).pts ? 1 : 0, rs: rs.map(x => x[0]) }));
})();
"""
r = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, timeout=60)
check(r.returncode == 0, 'node ran ' + r.stderr[:300])
o = json.loads(r.stdout or '{}')
check(o.get('clipped') and 0 < o.get('kept', 0) < 10 and o.get('whole') == 40, f"40-part shape drawn as {o.get('kept')} parts near the pin; the caller keeps the whole shape")
check(o.get('poly') == 'Polygon' and o.get('small') is False, 'small shapes and single polygons are untouched')
check('key' in o.get('co', []) and any(x.startswith('sg') for x in o.get('co', [])) and o.get('coCamps') == 1, 'Colorado: answer-key outlines, state key layers and campgrounds listed (camp points can be shown)')
check('vabird' in o.get('va', []), 'Virginia lists the birding trail sites')
check('Recommended next step' in o.get('rs', []) and 'Signed decision' in o.get('rs', []), 'Research on US-0150: recommendation and signed decision')
src = (ROOT / 'kpc-maprep-extras.js').read_text(encoding='utf-8')
ui = ' '.join(re.findall(r"'([^'\\]*(?:\\.[^'\\]*)*)'", src))
check(not re.search(r'\b(bots?|automat\w*|robot)\b', ui, re.I), 'no bot or automation wording in the page text')
check('Research on this place' in src and 'CLUB LAYERS FOR' in src, 'section titles')
chk = (ROOT / 'kpc-maprep-check.js').read_text(encoding='utf-8')
check('(off by default)' not in chk and 'ON by default since Nov 7' in chk, "the stale 'off by default' comment is fixed")
check('KPCMapExtras.clipFC(fc, la, lo)' in chk and 'SHOW THE WHOLE SHAPE' in chk and "map.getZoom() <= 8" in chk, 'outline drawing clips, with a whole-shape button and zoom-out restore')
for f in ('kpc-maprep.html', 'kpc-maprep-reps.html', '.claude/build/maprep/main.html'):
    check('kpc-maprep-extras.js?v=' in (ROOT / f).read_text(encoding='utf-8'), f + ' loads the extras')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
