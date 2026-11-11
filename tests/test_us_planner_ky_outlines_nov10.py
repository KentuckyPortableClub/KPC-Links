"""US Trip Planner, Nov 10: official boundaries in Kentucky are the same saved
vector GeoJSON files Park Commander uses, drawn as thin SVG. The PAD-US raster
export (thick cyan, tile-edge cuts, missing parks) is skipped over Kentucky.
No new live services*.arcgis.com calls; no key/data file changes."""
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ok = True
def check(name, cond, detail=''):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name + ((' — ' + detail) if detail and not cond else ''))
    ok = ok and bool(cond)

pad = (ROOT / 'kpc-padus-layer.js').read_text(encoding='utf-8')
us = (ROOT / 'kpc-us-planner.js').read_text(encoding='utf-8')
html = (ROOT / 'kpc-planner-us.html').read_text(encoding='utf-8')

check('US planner turns on skipKY and kyOfficial',
      "KPCPad(map,{keyPos:'bottomleft',minz:7,skipKY:true,kyOfficial:true})" in us)
check('kyOfficial implies skipKY so the PAD-US raster is cut out of Kentucky',
      'if (opts.kyOfficial) opts.skipKY = true' in pad)
check('Kentucky official outlines are the saved ky-*.geojson files, drawn as SVG',
      "file:'ky-state-parks.geojson'" in pad and "file:'ky-natural-areas.geojson'" in pad
      and "file:'ky-nature-preserves.geojson'" in pad and "file:'ky-hunting-areas.geojson'" in pad
      and "L.svg({ pane: 'kyoff'" in pad and "pane: 'kyoff'" in pad and "L.canvas" not in pad.split('attachKyOfficial')[1])
check('Kentucky official strokes are thin (weight 2)',
      'const W = 2' in pad and 'kpc-kyoff' in pad)
check('the four reported parks have complete saved official outlines',
      all((ROOT / f).exists() for f in ['ky-state-parks.geojson','ky-natural-areas.geojson','ky-nature-preserves.geojson','ky-hunting-areas.geojson']))

import json
def has_name(fn, name):
    j=json.loads((ROOT/fn).read_text())
    return any((f.get('properties') or {}).get('NAME')==name for f in j.get('features') or [])
check('saved files include Green River SNA, Barren River Lake SRP, Brigadoon SNP, and Marrowbone WMA',
      has_name('ky-natural-areas.geojson','Green River State Natural Area (Davis Bend)')
      and has_name('ky-natural-areas.geojson','Green River State Natural Area (Rush Island Bottoms)')
      and has_name('ky-state-parks.geojson','Barren River Lake State Resort Park')
      and has_name('ky-nature-preserves.geojson','Brigadoon State Nature Preserve')
      and has_name('ky-hunting-areas.geojson','Marrowbone State Forest and WMA'))

# no new services*.arcgis.com
new = set(re.findall(r'https?://services\d*\.arcgis\.com[^\'"\s]*', pad+us))
check('no new services*.arcgis.com calls added',
      all('edits.nationalmap.gov' not in u for u in new) and not any('FeatureServer' in u and 'PAD' in u for u in new))

check('US planner loads the shared answer key and bumped stamps',
      'kpc-answer-key.js?v=20261110key' in html and 'kpc-padus-layer.js?v=20261110ky' in html
      and 'kpc-us-planner.js?v=20261110ky' in html)

pages = list(ROOT.glob('*.html'))
vs = {}
for p in pages:
    for m in re.finditer(r'src="kpc-padus-layer\.js(\?v=[^"]*)?"', p.read_text(encoding='utf-8', errors='replace')):
        vs.setdefault(m.group(1) or '', []).append(p.name)
check(f'kpc-padus-layer.js has one bumped ?v= everywhere: {sorted(vs)}', list(vs) == ['?v=20261110ky'])

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
