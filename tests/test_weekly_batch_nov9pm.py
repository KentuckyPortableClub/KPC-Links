#!/usr/bin/env python3
"""Nov 9 PM weekly batch (Brandon t906u 3:58 PM CST): Playwright jobs pinned to ubuntu-24.04 + the hand joins saved with record ids.
Offline. No network."""
import json, pathlib, re, sys
HERE = pathlib.Path(__file__).resolve().parent.parent
ok = True
def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)

# 1) every workflow that installs Playwright runs on ubuntu-24.04 (Playwright has no build for ubuntu 26.04: Guide PDFs run 42637107981)
for wf in sorted((HERE / '.github/workflows').glob('*.yml')):
    t = wf.read_text(encoding='utf-8')
    if not re.search(r'playwright', t, re.I): continue
    bad = [l.strip() for l in t.splitlines() if re.match(r'\s*runs-on:\s*ubuntu-latest', l)]
    check(not bad, f'{wf.name}: no ubuntu-latest runner in a Playwright workflow')
for name in ('kpc-guide-pdf.yml', 'kpc-adds-probe.yml', 'kpc-bot-health.yml'):
    check('runs-on: ubuntu-24.04' in (HERE / '.github/workflows' / name).read_text(encoding='utf-8'), f'{name} pinned to ubuntu-24.04')

# 2) hand joins carry the record id (join + fp) and no 'none' flag
o = json.load(open(HERE / 'data/us-key/overrides.json', encoding='utf-8'))['parks']
WANT = {'US-11316': 'sgakg13903', 'US-12471': 'sgakg13505', 'US-11003': 'sgakg9736',
        'US-12060': 'sgnya64818', 'US-5308': 'sgnya66353', 'US-3140': 'sgvta430', 'US-0754': 'sgakd1159', 'US-11900': 'sgakd1245', 'US-0822': 'sgakd1122'}
for ref, rid in WANT.items():
    v = o.get(ref) or {}
    if rid in ((v.get('join_held') or {}).get('ids') or []):   # Nov 9 6:05 PM CST (Quality regrade v2 must-fix h): held, not joined
        check(rid not in (v.get('join') or []) and rid in (v['join_held'].get('fp') or {}), f'{ref} {rid} is HELD for Brandon (not sure under t927u), not joined'); continue
    check(rid in (v.get('join') or []) and rid in (v.get('fp') or {}) and not v.get('none') and rid not in (v.get('no') or []),
          f'{ref} joins {rid} with its saved record id')
# Nov 9 evening: Brandon t918u ('i agree to new number and if the boundary matches the park yes') decided both: joined, un-pended
for ref, rid in (('US-11308', 'sgakg13878'), ('US-10008', 'sgakg12225')):
    v = o[ref]
    check(rid in (v.get('join') or []) and rid in (v.get('fp') or {}) and rid not in (v.get('no') or []) and not v.get('none') and 'pending' not in v,
          f'{ref}: {rid} joined (no longer pending)')
    check('t918u' in str(v.get('decided_by')) and 'boundary matches the park' in str(v.get('decided_by')), f'{ref}: decided_by Brandon with his words')
    check(v['why'].count("NO 'Blackfoot' (chat 11") <= 1, f'{ref}: no repeated NO lines')
check('sgorf111' in o['US-10008']['no'], "US-10008: the Oregon layer's copy of the same land stays NO (no double count)")
for ref in ('US-12471', 'US-11003', 'US-12060', 'US-5308', 'US-11308', 'US-10008'):
    check(not o[ref]['why'].startswith('a different place, not this park'), f'{ref}: stale "a different place" lead-in cleared')
L = json.load(open(HERE / 'data/us-key/layers.json'))
check(L['sgvta'][0].endswith('/MapServer/38/query') and L['vta'][0].endswith('/MapServer/44/query'), 'sgvta = VT ANR unit POLYGONS (38); vta = points (44)')
print('ALL PASS' if ok else 'FAILED'); sys.exit(0 if ok else 1)
