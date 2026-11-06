#!/usr/bin/env python3
"""Mapping Rep Tool Box: search, abbreviations, and the rules check.
Also checks this branch did not touch the answer-key scripts or the key files."""
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True

def check(cond, msg):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)

file_check = r'''
const fs = require('fs');
const L = require('./kpc-maprep-logic.js');
const j = JSON.parse(fs.readFileSync('ky-hunting-areas.geojson', 'utf8'));
const names = j.features.map(f => (f.properties || {}).NAME).filter(Boolean);
const hits = L.searchNames('Blackford Oaks W.M.A.', names.map(n => ({name: n})));
if (!hits.some(h => h.name === 'Blackford Oaks WMA' && h.score >= 90)) {
  console.log('SOME FAILED blackford file');
  process.exit(1);
}
const muddy = L.searchNames('Muddygut WMA', L.WATCH);
if (!muddy.some(h => /Muddygut/.test(h.name))) {
  console.log('SOME FAILED muddygut watch');
  process.exit(1);
}
console.log('PASS saved Kentucky names');
'''
f = subprocess.run(['node', '-e', file_check], cwd=ROOT, capture_output=True, text=True, timeout=60)
check(f.returncode == 0 and 'PASS saved Kentucky names' in f.stdout, 'Blackford Oaks W.M.A. is in the Kentucky file and Muddygut WMA is on the watch list: ' + (f.stdout.strip() or f.stderr.strip() or '?'))

r = subprocess.run(['node', str(ROOT / 'kpc-maprep-logic.js')], cwd=ROOT, capture_output=True, text=True, timeout=60)
check(r.returncode == 0 and 'PASS maprep toolbox selftest' in r.stdout and 'SOME FAILED' not in r.stdout,
      'logic selftest: ' + (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or ['?'])[-1])

cat = json.loads((ROOT / 'data/maprep/catalog.json').read_text())
live = [s for s in cat['sources'] if s.get('live')]
check(any(s.get('region') == 'CA' and s.get('live') for s in live), 'a Canada source is live')
check(any(s.get('origin') == 'camp-layers' and s.get('place') == 'IA' for s in live), 'Iowa agency layer is live')
check(any(s.get('origin') == 'camp-layers' and s.get('place') == 'MN' for s in live), 'Minnesota agency layer is live')
check(any(s.get('origin') == 'camp-layers' and s.get('place') == 'WI' for s in live), 'Wisconsin agency layer is live')
check(all('33TOOklri9xpic7U' not in ((s.get('rest') or '') + (s.get('download') or '')) for s in cat['sources']), 'Grant County NM server is absent')
check(all(s.get('place') not in ('CO', 'TN') for s in live), 'Colorado and Tennessee are not queried live')
check(cat['regions']['US']['enabled'] and cat['regions']['CA']['enabled'] and not cat['regions']['AU']['enabled'], 'US and Canada on, other countries off')

have = subprocess.run(['git', 'rev-parse', '--verify', 'origin/main'], cwd=ROOT, capture_output=True, text=True, timeout=20)
if have.returncode != 0:
    fetch = subprocess.run(['git', 'fetch', 'origin', 'main'], cwd=ROOT, capture_output=True, text=True, timeout=60)
    check(fetch.returncode == 0, 'fetched origin/main: ' + ((fetch.stderr or fetch.stdout or 'fetch failed').strip().splitlines() or ['?'])[-1])
diff = subprocess.run(['git', 'diff', '--name-only', 'origin/main...HEAD', '--', '.github/scripts', 'data/us-key', 'data/ca-key', 'data/world-key', 'data/ky-answer-key.json'],
                      cwd=ROOT, capture_output=True, text=True, timeout=30)
names = [ln for ln in diff.stdout.splitlines() if ln.strip()]
# This guard is for a Tool Box-only branch. After #48 merged, this test lives on main and runs on every branch,
# so a key PR (which changes key scripts on purpose and has its own replay tests) must not trip it.
_all = subprocess.run(['git', 'diff', '--name-only', 'origin/main...HEAD'], cwd=ROOT, capture_output=True, text=True, timeout=30)
_toolbox = [ln for ln in _all.stdout.splitlines() if 'maprep' in ln.lower() or 'toolbox' in ln.lower()]
if names and not _toolbox:
    print('SKIP answer-key guard: this branch is not a Tool Box change (' + ', '.join(names[:3]) + ' are covered by that PR\'s own tests)')
else:
    check(diff.returncode == 0 and not names, 'answer-key scripts and key files are unchanged' + ((' ' + ', '.join(names[:8])) if names else ''))

ag = json.loads((ROOT / 'data/maprep/agencies.json').read_text())
NEED = 'AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY AB BC MB NB NL NT NS NU ON PE QC SK YT'.split()
missing_place = [c for c in NEED if not (ag.get('places', {}).get(c) or {}).get('agencies')]
check(not missing_place, 'every state and province has an agency row' + ((' missing ' + ', '.join(missing_place)) if missing_place else ''))
check('33TOOklri9xpic7U' not in json.dumps(ag), 'agency directory does not list the banned server')
gaps = ROOT / 'docs/maprep-agency-gaps.txt'
check(gaps.exists() and gaps.stat().st_size > 40, 'gap list for the outside researcher exists')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
