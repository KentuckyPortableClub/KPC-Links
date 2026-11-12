#!/usr/bin/env python3
"""WDPA stays off this public repo (Nov 11 2026, owner: remove the WDPA files, no history purge). Offline: no network.

 1. No tracked file carries WDPA / Protected Planet DATA: WDPA ids with a value, the WDPA service address, protectedplanet.net/<id>
    links, 'UNEP-WCMC WDPA' sources or 'WDPA match' leads. Mentions of the rule ('never use WDPA'), field-name lists of other
    layers (PAD-US WDPA_Cd, CPCAD WDPAID) and the code / tests that recognise WDPA leads are allowed (ALLOW below).
 2. The files the owner had removed stay removed.
 3. The research inbox (kpc_research_inbox.run) skips WDPA rows: nothing from them reaches results/ or needs-another-look.json.
"""
import csv, json, os, pathlib, re, subprocess, sys, tempfile
HERE = pathlib.Path(os.environ.get('LINKS') or pathlib.Path(__file__).resolve().parent.parent)
sys.path.insert(0, str(HERE / '.github/scripts'))
fails = 0


def ok(c, m):
    global fails
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails += 1


DATA = re.compile(r'"wdpa_?id"\s*:\s*"?[0-9]|"(?:wdpaid|wdpa_pid)"\s*:\s*"?[0-9]|unep-wcmc\.org|The_World_Database_of_Protected_Areas|'
                  r'protectedplanet\.net/[0-9]|WDPA match|UNEP-WCMC WDPA|wdpa_poly_latest|WDPA[ _-]?id[ :=#]+[0-9]{3,}', re.I)
# code that recognises WDPA leads (so it can refuse them), its tests' fixtures, and the written rule
ALLOW_DIRS = ('.github/scripts/', 'tests/')
ALLOW = {'docs/QUALITY_AMENDMENT2.md': 'the rule: a WDPA match is a lead only, never SURE'}
try:
    files = subprocess.run(['git', 'ls-files'], cwd=HERE, capture_output=True, text=True, timeout=120).stdout.split('\n')
except Exception:  # noqa: BLE001
    files = []
if not [f for f in files if f]:
    files = [str(p.relative_to(HERE)) for p in HERE.rglob('*') if p.is_file() and '.git' not in p.parts]
bad = []
for f in files:
    if not f or f.startswith(ALLOW_DIRS) or f in ALLOW: continue
    p = HERE / f
    if not p.is_file() or p.stat().st_size > 30_000_000 or p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.pdf', '.gz', '.zip', '.xlsx', '.mp3', '.mp4', '.ico'): continue
    try: t = p.read_text(encoding='utf-8', errors='replace')
    except Exception: continue  # noqa: BLE001
    m = DATA.search(t)
    if m: bad.append('%s (%s)' % (f, m.group(0)[:40]))
ok(not bad, 'no tracked file outside code / tests / the rule text carries WDPA data: ' + ('; '.join(bad[:6]) or 'none'))
for f in ('data/wdpa-approximate-candidates.json', 'data/research-inbox/nov9-brandon-no-id-world-high-med.csv',
          'data/research-inbox/results/nov9-brandon-no-id-world-high-med.json', 'data/research-inbox/results/nov9-brandon-no-id-world-high-med.md'):
    ok(not (HERE / f).exists(), 'removed and not back: ' + f)
nal = json.load(open(HERE / 'data/research-inbox/needs-another-look.json', encoding='utf-8'))
ok(isinstance(nal.get('parks'), dict) and len(nal['parks']) > 0 and not re.search(r'wdpa|protected planet|unep-wcmc', json.dumps(nal), re.I),
   'needs-another-look.json: still a valid retry list (%d parks), no WDPA row left' % len(nal.get('parks') or {}))

import kpc_research_inbox as RI  # noqa: E402
ok(RI.wdpa_row({'layer_url': 'https://data-gis.unep-wcmc.org/server/rest/services/x/FeatureServer/1'}) and RI.wdpa_row({'official_name': 'UNEP-WCMC WDPA (WDPA_poly_latest)'})
   and RI.wdpa_row({'source': 'Protected Planet'}) and not RI.wdpa_row({'layer_url': 'https://gis.example.gov/arcgis/rest/services/p/MapServer/0', 'notes': 'state layer'}),
   'wdpa_row() tells a WDPA lead from an agency lead')
root = pathlib.Path(tempfile.mkdtemp()); inbox = root / 'data/research-inbox'; inbox.mkdir(parents=True)
W = {'pota_ref': 'ZZ-0001', 'park_name': 'Test Reserve', 'layer_url': 'https://data-gis.unep-wcmc.org/server/rest/services/ProtectedSites/The_World_Database_of_Protected_Areas/FeatureServer/1',
     'record_id': '999999901', 'official_name': 'UNEP-WCMC WDPA (WDPA_poly_latest)', 'notes': 'made-up row', 'source': 'test', 'pin_lat': '1', 'pin_lon': '1'}
A = dict(W, pota_ref='ZZ-0002', layer_url='https://gis.example.gov/arcgis/rest/services/p/MapServer/0', record_id='7', official_name='Example Parks', notes='agency row')
for name, rows in (('all-wdpa', [W]), ('mixed', [W, A])):
    with open(inbox / (name + '.csv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=RI.COLS); w.writeheader(); [w.writerow({c: r.get(c, '') for c in RI.COLS}) for r in rows]
json.dump({'about': 'test', 'parks': {'ZZ-0003': {'status': 'needs another look', 'row': dict(W, pota_ref='ZZ-0003')}}}, open(inbox / 'needs-another-look.json', 'w'))
(root / 'kpcdata').mkdir()
try:
    RI.run(sorted(str(p) for p in inbox.glob('*.csv')), root=root, kpcdata=root / 'kpcdata', cache=root / 'cache', offline=True, retry=True)
    err = ''
except Exception as e:  # noqa: BLE001
    err = repr(e)
ok(not err, 'the inbox runs offline on a throwaway repo ' + err)
outs = [p for p in root.rglob('*') if p.is_file() and 'cache' not in p.parts and p.suffix in ('.json', '.md', '.csv') and p.parent != inbox or p.name == 'needs-another-look.json']
leak = [str(p.relative_to(root)) for p in outs if re.search(r'wdpa|unep-wcmc|999999901|ZZ-0001|ZZ-0003', p.read_text(encoding='utf-8'), re.I)]
ok(not leak, 'nothing from a WDPA row is written (results, retry list, lists): ' + (', '.join(leak) or 'clean'))
ok(not (inbox / 'results/all-wdpa.json').exists(), 'a file of only WDPA rows makes no results file')
m = inbox / 'results/mixed.json'
ok(m.exists() and [r['pota_ref'] for r in json.load(open(m))['rows']] == ['ZZ-0002'], 'a mixed file keeps its agency rows')
print('SOME FAILED' if fails else 'ALL PASSED')
sys.exit(1 if fails else 0)
