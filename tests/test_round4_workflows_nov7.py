#!/usr/bin/env python3
"""Round 4 (Nov 7 2026), items 2-3: the by-hand app-packs and Kentucky map-file workflows. Offline; nothing is run on GitHub."""
import json, os, re, subprocess, sys, tempfile, shutil
import yaml
import xml.etree.ElementTree as ET
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bad = 0
def ck(c, m):
    global bad
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: bad += 1
def wf(n):
    d = yaml.safe_load(open(f'{R}/.github/workflows/{n}', encoding='utf-8')); d['on'] = d.pop(True, d.get('on')); return d
for n in ('kpc-app-packs.yml', 'kpc-ky-mapfiles.yml'):
    d = wf(n)
    ck(list(d['on']) == ['workflow_dispatch'], f'{n}: by hand only (no schedule, no workflow_run)')
    ck(d['permissions'] == {'contents': 'write'}, f'{n}: contents write only')
    txt = open(f'{R}/.github/workflows/{n}', encoding='utf-8').read()
    ck(not re.search(r'secrets\.|robots|User-Agent|--user-agent', txt, re.I), f'{n}: no secrets / UA tricks')
    ck('33TOOklri9xpic7U' not in txt and 'natureserve' not in txt.lower(), f'{n}: no banned hosts')
a = open(f'{R}/.github/workflows/kpc-app-packs.yml', encoding='utf-8').read()
ck('kpc_overlay.sh' in a and 'node .github/scripts/build_app_pack.js' in a, 'app packs: runs overlay then builder')
ck("inputs.save == 'release'" in a and 'gh release upload app-packs' in a and '--clobber' in a, 'app packs: release-asset mode')
ck(re.search(r"git add -A app/packs", a) and 'kpc_save_overwrite.sh --copy' in a, 'app packs: commit mode saves app/packs only')
m = open(f'{R}/.github/workflows/kpc-ky-mapfiles.yml', encoding='utf-8').read()
ck('refresh.py' in m and m.count('KPC_Kentucky_') >= 8, 'map files: runs refresh.py, saves only the four KPC_Kentucky files')
# run the real refresh.py in a temp copy: files stay well-formed, every ref kept
with tempfile.TemporaryDirectory() as t:
    for f in ('kpc-ky-data.json', 'ky-overlaps.geojson', 'KPC_Kentucky_POTA_Parks.kml', 'KPC_Kentucky_POTA_Parks.gpx', 'KPC_Kentucky_KFF_References.kml', 'KPC_Kentucky_KFF_References.gpx'):
        shutil.copy(f'{R}/{f}', t)
    os.makedirs(t + '/.claude/build/mapfiles'); shutil.copy(f'{R}/.claude/build/mapfiles/refresh.py', t + '/.claude/build/mapfiles/')
    r = subprocess.run([sys.executable, '.claude/build/mapfiles/refresh.py'], cwd=t, capture_output=True, text=True)
    ck(r.returncode == 0, 'refresh.py runs: ' + r.stdout.strip().replace('\n', ' | ')[:120])
    d = json.load(open(t + '/kpc-ky-data.json'))
    for b, refs in (('KPC_Kentucky_POTA_Parks', {p['c'] for p in d['parks']}), ('KPC_Kentucky_KFF_References', {k['c'] for k in d['kff']})):
        for e in ('kml', 'gpx'):
            ET.parse(f'{t}/{b}.{e}'); s = open(f'{t}/{b}.{e}', encoding='utf-8').read()
            lost = refs - set(re.findall(r'\b(?:US|KFF)-\d{4,5}\b', s))
            ck(not lost, f'{b}.{e}: well-formed, all {len(refs)} refs (incl. 5-digit) present' + (f' MISSING {sorted(lost)[:5]}' if lost else ''))
    ck('\\d{4,5}' in m and 'refs - have' in m, 'map files: the workflow check compares the exact ref set (5-digit refs too)')
    r2 = subprocess.run([sys.executable, '.claude/build/mapfiles/refresh.py'], cwd=t, capture_output=True, text=True)
    ck(r2.stdout == r.stdout, 'refresh.py second run gives the same report (stable)')
# item 6 (OPTIONAL second commit): if the 2-fer publish workflow starts on a push of the reviewed list, it must stay inert and cron-free
fp = wf('kpc-fers-publish.yml')
ft = open(f'{R}/.github/workflows/kpc-fers-publish.yml', encoding='utf-8').read()
ck('schedule' not in fp['on'] and 'workflow_run' not in fp['on'], 'fers publish: no cron')
ck("vars.KPC_FERS_PDF || 'off'" in ft and "vars.KPC_FERS_LAYER || 'off'" in ft and "vars.KPC_FERS_GPX || 'off'" in ft and "vars.KPC_HOURS_PUBLISH || 'off'" in ft, 'fers publish: switches still default off')
if 'push' in fp['on']:
    ck(fp['on']['push'] == {'branches': ['main'], 'paths': ['kpc-fers-reviewed.json']}, 'fers publish: push only for kpc-fers-reviewed.json')
    ck('= push ] && [ "$part" = hours ] && continue' in ft, 'fers publish: hours part never starts from a push')
    c = fp['jobs']['publish'].get('if', '')
    ck("github.event_name != 'push'" in c and all(f"(vars.{v} || 'off') != 'off'" in c for v in ('KPC_FERS_LAYER', 'KPC_FERS_GPX', 'KPC_FERS_PDF')) and 'HOURS' not in c,
       'fers publish: a push run is skipped whole while the three 2-fer switches are off')
# item 5 (OPTIONAL third commit): new-refs may also start on a push of kpc-ky-data.json; still the one cron, nothing else added
nr = wf('kpc-new-refs.yml')
ck(nr['on']['schedule'] == [{'cron': '39 12 * * *'}] and 'workflow_run' not in nr['on'], 'new-refs: still only its one cron')
if 'push' in nr['on']:
    ck(nr['on']['push'] == {'branches': ['main'], 'paths': ['kpc-ky-data.json']}, 'new-refs: push only for kpc-ky-data.json')
    ck('workflow_dispatch' in nr['on'], 'new-refs: still startable by hand')
    src = open(f'{R}/.github/scripts/kpc_new_refs.py', encoding='utf-8').read()
    ck("while aid in ids" in src and "if a.get('id') != aid]" not in src, 'new-refs: a second post the same day gets its own Club News id (never replaces the first)')
print('ALL PASS' if not bad else f'{bad} FAILED'); sys.exit(1 if bad else 0)
