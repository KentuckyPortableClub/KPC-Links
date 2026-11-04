#!/usr/bin/env python3
"""Offline test for .github/scripts/kpc_finds_lines.py (Nov 4; Quality's finding, Brandon 4:35 AM CST, relayed via Super Head Bot): the found-trail-
lines STATUS report (no geometry) is written to data/status/finds-lines-report.json and NEVER under data/trails/ (where the waiting
room would judge it as a trail line). The hand-off list goes to argv[1]. A saved line is never replaced by a found one."""
import json, os, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
TOOL = HERE / '.github/scripts/kpc_finds_lines.py'
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


src = TOOL.read_text()
check("open('data/trails/finds-lines-report.json'" not in src and "open('data/status/finds-lines-report.json'" in src, 'the script names data/status/ for the report, not data/trails/')

with tempfile.TemporaryDirectory() as t:
    R = pathlib.Path(t)
    for d in ('data/parkinfo', 'data/us-key', 'data/trails', 'kpcdata/data/intake', 'kpcdata/data/waiting/questions'): (R / d).mkdir(parents=True)
    json.dump({'parks': {'US-1': ['Alpha National Recreation Trail', '', 'National Recreation Trail', '', '', '38.0', '-84.0'],
                         'US-2': ['Bravo Trail', '', 'National Recreation Trail', '', '', '37.0', '-80.0']}}, open(R / 'data/parkinfo/US-XX.json', 'w'))
    json.dump({'parks': {'US-1': {'n': 'Alpha National Recreation Trail', 'm': []}, 'US-2': {'n': 'Bravo Trail', 'm': []}}}, open(R / 'data/us-key/US-XX.json', 'w'))
    json.dump({'ref': 'US-2', 'geometry': {'type': 'LineString', 'coordinates': [[-80, 37], [-80.01, 37.01]]}}, open(R / 'data/trails/US-2.json', 'w'))
    url = 'https://apps.example.fs.usda.gov/arcx/rest/services/EDW/EDW_TrailNFSPublish_01/MapServer/0'
    json.dump({'pairs': {f'US-1|{url}': {'result': 'SURE', 'record_name': 'Alpha National Recreation Trail'},
                         f'US-2|{url}': {'result': 'SURE', 'record_name': 'Bravo Trail'}},
               'layers': {url: {'geometry': 'esriGeometryPolyline', 'name_field': 'TRAIL_NAME', 'title': 'NFS trails', 'host': 'fs.usda.gov'}}},
              open(R / 'kpcdata/data/intake/external-results.json', 'w'))
    before = sorted(p.name for p in (R / 'data/trails').iterdir())
    out = R / 'finds.json'
    p = subprocess.run([sys.executable, str(TOOL), str(out)], cwd=R, env=dict(os.environ, DATA='kpcdata'), capture_output=True, text=True)
    rep = R / 'data/status/finds-lines-report.json'
    check(p.returncode == 0 and rep.exists(), f'the report is written to data/status/finds-lines-report.json ({p.stdout.strip()[:120]})')
    check(sorted(q.name for q in (R / 'data/trails').iterdir()) == before, 'nothing new under data/trails/ (no report there, no line written by this script)')
    r = json.load(open(rep)); rows = json.load(open(out))
    check(set(r) == {'about', 'count', 'rows'} and 'geometry' not in json.dumps(r), 'the report is a status report: about / count / rows, no geometry')
    check([x['ref'] for x in rows] == ['US-1'] and r['count'] == 1, 'the hand-off list has US-1 only: US-2 already has a saved line, never replaced by a found one')

print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
