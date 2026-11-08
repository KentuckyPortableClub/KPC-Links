#!/usr/bin/env python3
"""Nov 8 2026 (Brandon: "Yes, layer + list"): optional Virginia Bird & Wildlife Trail (US-9935) site layer, OFF by default, in Park
Commander and the US Trip Planner; offline-cached; report-only list of parks holding a site (never read by the 2-fer line). Offline."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
FAILS = []


def check(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: FAILS.append(m)


rd = lambda p: (ROOT / p).read_text(encoding='utf-8')
d = json.loads(rd('data/va-birding-sites.json'))
check(d['ref'] == 'US-9935' and len(d['pts']) == 640, '640 official site points for US-9935')
check(all(-84 < p[0] < -75 and 36 < p[1] < 40 and p[2] and p[3] for p in d['pts']), 'every point is in Virginia with an id and a name')
check((ROOT / 'data/va-birding-sites.json').stat().st_size < 80000, 'site file stays small')
js = rd('kpc-va-birding-layer.js')
check('window.KPCVaBirding' in js and "g.on('add', load)" in js, 'layer loads only when turned on')
f = rd('finder.html')
check('<input id="gis-vabird" type="checkbox">' in f and "localStorage.getItem('kpcPcVaBird')==='1'" in f and 'kpc-va-birding-layer.js' in f, 'Park Commander: checkbox off by default')
check('kpc-va-birding-layer.js' in rd('kpc-planner-us.html') and "store.get('kpcUsVaBird',false)" in rd('kpc-us-planner.js'), 'Trip Planner: overlay off by default')
sw = rd('kpc-finder-sw.js')
check('kpc-va-birding-layer\\.js' in sw and 'va-birding-sites\\.json' in sw and "const APP = 'kpc-finder-v1'" in sw, 'offline cache list has the files; cache name never renamed')
r = json.loads(rd('data/reports/va-birding-sites-in-parks-nov8.json'))
check(r['about'].startswith('REPORT ONLY') and r['parks_with_sites'] == len(r['parks']) > 0 and 'US-9935' not in {p['ref'] for p in r['parks']}, 'report-only park list')
ids = {p[2] for p in d['pts']}
check(all(set(p['site_ids']) <= ids for p in r['parks']), 'report site ids are real sites')
code = ''.join(p.read_text(encoding='utf-8', errors='ignore') for p in (ROOT / '.github/scripts').glob('*.py'))
check('va-birding' not in code, 'no key / 2-fer script reads the birding files')
sys.exit(1 if FAILS else 0)
