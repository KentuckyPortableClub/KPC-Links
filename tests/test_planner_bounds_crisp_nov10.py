"""Kentucky Trip Planner, Nov 10: official park outlines are drawn as SVG
from the saved KY GeoJSON files (same files as Park Commander), not on a
Leaflet canvas. A canvas renderer made the lines thick and blocky and cut
shapes off in a hard straight line at the canvas edge."""
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ok = True
def check(name, cond, detail=''):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name + ((' — ' + detail) if detail and not cond else ''))
    ok = ok and bool(cond)

js = (ROOT / 'kpc-planner.js').read_text(encoding='utf-8')
html = (ROOT / 'kpc-planner.html').read_text(encoding='utf-8')
gis = (ROOT / 'gis-overlays.js').read_text(encoding='utf-8')

check('planner does not use a Leaflet canvas renderer for official outlines',
      'L.canvas' not in js and 'renderer:canvasR' not in js and 'bRend' not in js and 'canvasR' not in js)
check('drawB still puts official outlines on the boundary pane',
      "L.geoJSON(bData[k],{pane:'bndp'" in js)
check('comment explains the SVG (not canvas) choice',
      'official outlines as SVG' in js and 'hard straight cut' in js)

# Same saved KY files the finder uses — no live services*.arcgis.com for these layers
files = re.findall(r"file:'(ky-[a-z0-9-]+\.geojson)'", js)
finder_files = re.findall(r"file:'(ky-[a-z0-9-]+\.geojson)'", gis)
# Planner boundary files should exist on disk and overlap the finder's set
missing = [f for f in files if not (ROOT / f).exists()]
check('every planner outline file is a saved local copy', not missing, str(missing))
bound_files = re.findall(r"file:'(ky-[a-z0-9-]+\.geojson)'", js.split('const T = {')[0])
shared = set(bound_files) & set(finder_files)
check('planner official outlines reuse the same saved KY files as the finder',
      len(shared) >= 10, f'shared={sorted(shared)} planner={bound_files}')

# No new live ArcGIS FeatureServer / MapServer image-layer calls for KY outlines
new_arcgis = re.findall(r'https?://services\d*\.arcgis\.com[^\'"\s]*', js)
# Trail of Tears / Lewis & Clark already used services1.arcgis.com for trail lines; no new hosts, and no image/tile overlay for PAD-US
hosts = {re.match(r'https?://([^/]+)', u).group(1) for u in new_arcgis}
check('no new services*.arcgis.com hosts (existing trail queries stay on services1)',
      hosts <= {'services1.arcgis.com'}, str(hosts))
check('planner does not load a PAD-US raster / image overlay script',
      'kpc-padus-layer.js' not in html)

check('kpc-planner.js cache stamp is bumped',
      'kpc-planner.js?v=20261111zr' in html)
# one stamp everywhere this file is included
pages = list(ROOT.glob('*.html'))
vs = {}
for p in pages:
    for m in re.finditer(r'src="kpc-planner\.js(\?v=[^"]*)?"', p.read_text(encoding='utf-8', errors='replace')):
        vs.setdefault(m.group(1) or '', []).append(p.name)
check(f'kpc-planner.js has one bumped ?v= everywhere: {sorted(vs)}', list(vs) == ['?v=20261111zr'])

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
