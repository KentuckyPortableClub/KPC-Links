"""Park Commander map, Nov 10: on a phone the opened Boundaries legend stays inside
the map (header and close control visible), and Full screen fills the viewport so
leftover under-map chrome (2-fer lists, notes) cannot shrink the map."""
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ok = True
def check(name, cond, detail=''):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name + ((' — ' + detail) if detail and not cond else ''))
    ok = ok and bool(cond)

g = (ROOT / 'gis-overlays.js').read_text(encoding='utf-8')
x = (ROOT / 'kpc-map-extras.js').read_text(encoding='utf-8')
css = (ROOT / 'finder.css').read_text(encoding='utf-8')
html = (ROOT / 'finder.html').read_text(encoding='utf-8')
js = (ROOT / 'finder.js').read_text(encoding='utf-8')

check('legend has a sticky header row and an X close button',
      'class="kbl-h"' in g and 'class="kbl-x"' in g and 'aria-label="Close legend"' in g)
check('X close button closes the legend', 'x.onclick' in g and "classList.add('closed')" in g)
check('legend body scrolls when it is taller than the map',
      'overflow-y:auto' in html and '.kbl-b{' in html and 'position:sticky' in html and 'top:0' in html)
check('open legend max-height is the map height minus the credits lift and a margin',
      'leg.style.maxHeight=max+\'px\'' in x and 'mr.height-liftPx-margin' in x and 'KPCX.fitLegend' in x)
check('full screen is fixed, 100dvh, and above the site header',
      'position:fixed!important' in css and 'height:100dvh!important' in css and 'z-index:2147483000!important' in css)
check('full screen hides leftover under-map chrome (2-fer lists, notes) so the map can fill',
      '.mapwrap.kpc-mapfull > :not(.mapbar):not(#map):not(.kx-tbar){display:none!important}' in css)
check('full screen map flexes to fill the remaining wrap',
      'flex:1 1 auto!important' in css and 'min-height:0!important' in css)
check('full screen reparents the map wrap to the page body so a parent cannot clip it',
      "document.body.appendChild(wrap)" in js and "createComment('kpc-mapfull')" in js)

pages = list(ROOT.glob('*.html')) + list(ROOT.glob('.claude/build/**/*.html'))
want = {'gis-overlays.js': '?v=20261111zr', 'kpc-answer-key.js': '?v=20261111zr', 'kpc-map-extras.js': '?v=20261111zr', 'finder.js': '?v=20261111p', 'finder.css': '?v=20261110fit'}
for name, stamp in want.items():
    vs = {}
    attr = 'href="' if name.endswith('.css') else 'src="'
    for p in pages:
        for m in re.finditer(re.escape(attr + name) + r'(\?v=[^"]*)?"', p.read_text(encoding='utf-8', errors='replace')):
            vs.setdefault(m.group(1), []).append(p.name)
    check(f'{name} has one bumped ?v= everywhere: {sorted(vs)}', list(vs) == [stamp])

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
