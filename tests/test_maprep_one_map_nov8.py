"""Mapping Rep Tool Box: ONE section and ONE map (Brandon Nov 8, t748u). Every feature kept."""
import re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
bad = 0
def check(ok, what):
    global bad
    print(('PASS ' if ok else 'FAIL ') + what); bad += (not ok)
js = (ROOT / 'kpc-maprep-research.js').read_text(encoding='utf-8')
for f in ('kpc-maprep.html', 'kpc-maprep-reps.html'):
    h = (ROOT / f).read_text(encoding='utf-8'); app = h[h.find('id="mrApp"'):h.find('</main>')]
    check(app.count('<section') == 1, f'{f}: one section')
    check(app.count('role="application"') == 1 and 'id="mrDrop"' in app and 'id="mrRsMap"' not in app, f'{f}: one map')
    check(app.find('id="mrRsForm"') < app.find('id="mrRsStatus"') < app.find('id="mrDrop"') < app.find('id="mrPanel"'), f'{f}: tabs and status are with the map, the panel beside it')
    pan = app[app.find('id="mrPanel"'):app.find('class="mr-one-tools"')]
    check(all(f'id="{i}"' in pan for i in ('mrRsMsg', 'mrSpot', 'mrRsOut', 'mrDeskDir', 'mrDeskOut')), f'{f}: every result area is in the panel next to the map')
    for i in ('mrRsPlace', 'mrRsQ', 'mrRsGo', 'mrRsFind', 'mrRsNear', 'mrRsTest', 'mrCheckForm', 'mrCheckSt', 'mrCheckQ', 'mrCheckGps', 'mrCheckAll', 'mrLayers', 'mrLayerToggles', 'mrCanada', 'mrDeskForm', 'mrDeskPlace', 'mrDeskQ', 'mrDeskPin', 'mrDeskNew', 'mrDeskExport', 'mrDeskFolder', 'mrFClosed', 'mrFPriv', 'mrFSmall', 'mrFLocal', 'mrFNamed', 'mrDeskBounds', 'mrHowTo'):
        check(f'id="{i}"' in h, f'{f}: kept {i}')
    check('CHECK ALL IN THIS PLACE' in h and 'TRY AGAIN' not in h, f'{f}: Check All button kept')
    check(not re.search(r'\b(bot|AI|agent)\b', re.sub(r'<[^>]+>', ' ', app)), f'{f}: no bot wording')
check('C.map ? C.map()' in js and 'shared = !!rmap' in js, 'research results draw on the one shared map')
check('SHOW ON MAP' not in js and "addEventListener('toggle'" in js, 'no map button: opening a result focuses the map')
check('scrollIntoView' not in js.replace("if (!P) try { el.scrollIntoView", ''), 'no page jumps: only the panel scrolls')
check('TRY AGAIN' in js and 'Still waiting on the official server' in js, 'Try again and the slow-server note kept')
check('W.KPCMapCheck.pin()' in js, 'NEAR A SPOT uses the one pin')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
