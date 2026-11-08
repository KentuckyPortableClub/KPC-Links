"""Mapping Rep Tool Box (Brandon Nov 8 1:55 PM CST, t749u): the map is not pinned (it scrolls with the page, drags and zooms),
Leaflet is told when its box changes size, and FULL RULES CHECK brings the result into view."""
import re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
bad = 0
def check(ok, what):
    global bad
    print(('PASS ' if ok else 'FAIL ') + what); bad += (not ok)
js = (ROOT / 'kpc-maprep-research.js').read_text(encoding='utf-8')
for f in ('kpc-maprep.html', 'kpc-maprep-reps.html', '.claude/build/maprep/main.html'):
    h = (ROOT / f).read_text(encoding='utf-8')
    css = ''.join(re.findall(r'\.mr-one[^{]*\{[^}]*\}', h))
    check('sticky' not in css and 'position:fixed' not in css, f'{f}: the one map is not sticky or fixed')
    check('.mr-one-mapcol{position:relative}' in h, f'{f}: map column scrolls with the page')
    check('id="mrDrop"' in h and h.count('role="application"') == 1, f'{f}: still one map')
check('new ResizeObserver(() => rmap.invalidateSize())' in js, 'Leaflet invalidateSize when the map box changes size')
check('function showSpot()' in js and "showSpot();" in js[js.find('data-rscheck'):], 'FULL RULES CHECK brings the rules check into view')
check("inPanel(el, 'start', true)" in js and 'if (force) try { el.scrollIntoView' in js, 'the page moves only when asked (force)')
check("inPanel(el, 'start'); }" in js, 'opening a result still does not jump the page')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
