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

diff = subprocess.run(['git', 'diff', '--name-only', 'main', '--', '.github/scripts', 'data/us-key', 'data/ca-key', 'data/world-key', 'data/ky-answer-key.json'],
                      cwd=ROOT, capture_output=True, text=True, timeout=30)
names = [ln for ln in diff.stdout.splitlines() if ln.strip()]
check(diff.returncode == 0 and not names, 'answer-key scripts and key files are unchanged' + ((' ' + ', '.join(names[:8])) if names else ''))

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
