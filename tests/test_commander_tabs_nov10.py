#!/usr/bin/env python3
"""Nov 10: Park Commander's cards sit behind ONE tab bar (1 SEARCH | 2 NEARBY | 3 MY TRIP | 4 TRAILS | 5 ABOUT); the map stays outside the tabs.
Layout only: every earlier id and feature stays."""
import pathlib, re, subprocess, sys, collections
ROOT = pathlib.Path(__file__).resolve().parents[1]; bad = 0
def check(ok, msg):
    global bad; bad += not ok; print(('PASS ' if ok else 'FAIL ') + msg)
h = (ROOT / 'finder.html').read_text(encoding='utf-8'); js = (ROOT / 'finder.js').read_text(encoding='utf-8'); css = (ROOT / 'finder.css').read_text(encoding='utf-8')
ids = re.findall(r'\sid="([^"]+)"', h)
check(not [k for k, v in collections.Counter(ids).items() if v > 1], 'no duplicate ids')
i0 = h.find('id="fp-tabwrap"'); i1 = h.find('id="map"')
check(0 < i0 < i1, 'tab bar comes before the map')
check('role="tablist"' in h[i0:i0 + 300] and h[i0:i1].count('role="tab"') == 5, 'tablist with 5 role=tab buttons')
for k in ('where', 'near', 'trip', 'trails', 'about'):
    check(f'id="ftab-{k}"' in h and f'aria-controls="fpanel-{k}"' in h and f'id="fpanel-{k}"' in h and f'data-fpanel="{k}"' in h and f'aria-labelledby="ftab-{k}"' in h, f'tab {k}: tab, panel, aria links')
check('id="ftab-near-n"' in h and 'id="ftab-trip-n"' in h, 'live counts on NEARBY and MY TRIP')
panel_of = lambda sid: next((m.group(1) for m in re.finditer(r'data-fpanel="(\w+)"', h) if h.find(sid) > m.start() and not any(h.find(sid) > x.start() for x in re.finditer(r'data-fpanel="(\w+)"', h) if x.start() > m.start())), None)
check(all(panel_of(s) == p for s, p in (('id="finder-search"', 'where'), ('id="finder-results"', 'near'), ('id="finder-planner"', 'trip'), ('id="finder-tools"', 'trip'), ('id="trailfinder"', 'trails'), ('id="finder-about"', 'about'))), 'each card is in its tab')
check('</div></div><div class="mapgrid"><section class="panel mapwrap" id="finder-map"' in h and h.find('id="map"') > h.find('id="fpanel-about"'), 'map is outside every tab panel (after the closed panels)')
check(all(f'id="{i}"' in h for i in ('place', 'town', 'gps', 'sota', 'pota', 'wwff', 'radius', 'status', 'items', 'count', 'favorites', 'tripstops', 'tripcount', 'clearplan', 'exportresults', 'exporttrip', 'sharesearch', 'gis-inside-btn')), 'main control ids kept')
check(all(x in js for x in ('function setTab', 'kpcCmdTab', 'function goNear', 'flashTab', 'invalidateSize', 'ArrowRight', 'hashchange', 'aria-selected')), 'tab logic: remember, hash, arrows, map resize')
check(js.count('wantNear=true') >= 5, 'every kind of search (town, reference, GPS, Kentucky jump, shared link) opens NEARBY')
check(re.search(r'finder\.js\?v=[A-Za-z0-9]+', h) and re.search(r'finder\.css\?v=[A-Za-z0-9]+', h), 'script and style have a version stamp')
r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_feature_inventory.py'), '--check'], capture_output=True, text=True)
check(r.returncode == 0, 'every feature-inventory item is still present: ' + r.stdout.strip()[-120:])
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
