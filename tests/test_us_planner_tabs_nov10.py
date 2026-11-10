#!/usr/bin/env python3
"""Nov 10: the US trip planner's four step cards sit behind ONE tab bar (WHERE | FIND NEW | MY TRIP | NEARBY), the map stays outside
the tabs, card 1 gets NEAR A PLACE | ALONG A ROUTE tabs and one SEARCH button. Layout only: every earlier id and feature stays."""
import json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]; bad = 0
def check(ok, msg):
    global bad; bad += not ok; print(('PASS ' if ok else 'FAIL ') + msg)
h = (ROOT / 'kpc-planner-us.html').read_text(encoding='utf-8'); js = (ROOT / 'kpc-us-planner.js').read_text(encoding='utf-8')
ids = re.findall(r'\sid="([^"]+)"', h)
check(len(ids) == len(set(ids)), 'no duplicate ids')
i0 = h.find('id="usp-tabwrap"'); i1 = h.find('id="usmap"')
check(0 < i0 < i1, 'tab wrapper comes before the map')
check('role="tablist"' in h[i0:i0 + 400] and h[i0:i1].count('role="tab"') >= 4, 'tab bar has role=tablist and the 4 role=tab buttons')
for k, pid in (('where', 'plan'), ('find', 'uppanel-find'), ('trip', 'uppanel-trip'), ('near', 'uppanel-near')):
    check(f'id="uptab-{k}"' in h and f'aria-controls="{pid}"' in h and f'id="{pid}"' in h and f'data-uppanel="{k}"' in h and 'role="tabpanel"' in h, f'tab {k}: tab, panel and aria-controls')
check('id="uptab-trip-n"' in h and 'id="uptab-near-n"' in h, 'live counts on MY TRIP and NEARBY')
wrap_end = h.find('id="usmap"')
panels = h[i0:wrap_end]
check('id="usmap"' not in panels.replace('id="usmap"', '', 1) and h.count('id="usmap"') == 1, 'map is a single element')
# the map must be outside every tabpanel: balance the divs/sections between the wrapper and the map
check('class="usp-panels"' in panels and panels.rfind('</div>') > panels.find('data-uppanel="near"'), 'panels close before the map card')
check(h.find('Where this comes from') > wrap_end, 'About card and disclaimer stay below the map, untabbed')
check('id="us-modes"' in h and 'data-m="place"' in h and 'data-m="route"' in h and h[h.find('id="us-modes"'):].count('role="tab"') >= 2, 'search-type tabs')
check(all(f'id="{i}"' in h for i in ('usf', 'urf-form', 'us-go', 'us-me', 'us-status', 'us-progs', 'us-hits')), 'search ids kept')
check('>SEARCH<' in h and 'FIND SPOTS ALONG THE WAY' in h and 'NEAR ME' in h, 'button labels kept')
check(all(x in js for x in ('function setTab', 'kpcUsPlanTab', 'function goNear', 'function flashTab', 'invalidateSize', 'ArrowRight', 'aria-selected', 'hashchange', 'requestSubmit')), 'tab logic: remember, hash, arrows, map resize, SEARCH')
check("flashTab('trip')" in js and "setTab('trip',{nosave:true})" in js, 'ADD flashes MY TRIP; shared trip opens it')
import subprocess
r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_feature_inventory.py'), '--check'], capture_output=True, text=True)
check(r.returncode == 0, 'every feature-inventory item (ids, functions, params, buttons, labels) is still present: ' + r.stdout.strip()[-200:])
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
