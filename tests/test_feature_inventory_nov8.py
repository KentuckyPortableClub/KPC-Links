#!/usr/bin/env python3
"""Nov 8 2026 (Brandon: keep every feature; the last polish lost many). Every item in tests/features-commander-tripplanner.json
(DOM ids, JS functions, URL params, localStorage keys, data-actions, buttons, fields, labels, shortcuts, links, export) must still
be in the Park Commander / Trip Planner files, and the card polish must stay wired on all three pages. Offline."""
import json, pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
FAILS = []


def check(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: FAILS.append(m)


r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_feature_inventory.py'), '--check'], capture_output=True, text=True)
print(r.stdout.strip()[-1500:])
base = json.loads((ROOT / 'tests/features-commander-tripplanner.json').read_text())
check(sum(map(len, base.values())) >= 1000, f'inventory lists the features ({sum(map(len, base.values()))} items)')
check(r.returncode == 0, 'every inventory item is still present')
for page in ('finder.html', 'kpc-planner.html', 'kpc-planner-us.html'):
    s = (ROOT / page).read_text(encoding='utf-8')
    check('kpc-card-polish.css' in s and 'kpc-card-polish.js' in s and s.index('kpc-card-polish.js') > s.lower().index('leaflet'),
          f'{page}: card polish loaded after Leaflet')
css = (ROOT / 'kpc-card-polish.css').read_text()
check(re.search(r'close-button\{width:40px', css) is not None, 'close button is at least 40 px')
check('min-height:40px' in css, 'card buttons are at least 40 px tall')
js = (ROOT / 'kpc-card-polish.js').read_text()
check('addInitHook' in js and 'popupclose' in js and 'kpc-under-card' in js, 'cards step over the map overlays and give them back on close')
check('display:none' not in css and 'remove()' not in js, 'the polish hides or removes no feature')
sys.exit(1 if FAILS else 0)
