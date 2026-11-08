"""Tool Box map starts on Satellite + streets (Brandon Nov 8 3:21 PM CST, t757u); the other base layers stay in the picker."""
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
bad = 0
def check(ok, what):
    global bad
    print(('PASS ' if ok else 'FAIL ') + what); bad += (not ok)
c = (ROOT / 'kpc-maprep-check.js').read_text(encoding='utf-8'); r = (ROOT / 'kpc-maprep-research.js').read_text(encoding='utf-8')
t = (ROOT / 'kpc-map-tools.js').read_text(encoding='utf-8')
check("KPCLayers(map, 'Satellite + streets')" in c and "KPCLayers(map, 'Street')" not in c, 'Check a place map defaults to Satellite + streets')
check("W.KPCLayers(rmap, 'Satellite + streets')" in r, 'research fallback map defaults to Satellite + streets')
check("if (first && B[first]) pick = first;" in t, 'the default is applied by the shared layer picker')
check(all(k in t for k in ("Street:", "Satellite:", "'Satellite + streets':", "'Topo (USGS, US only)':", "'Terrain (OpenTopoMap)':")) and 'L.control.layers(B, O' in t, 'every other base layer is still selectable')
for f in ('kpc-maprep.html', 'kpc-maprep-reps.html'):
    h = (ROOT / f).read_text(encoding='utf-8'); check('kpc-maprep-check.js?v=' in h and 'kpc-map-tools.js' in h, f'{f} loads the same map code')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
