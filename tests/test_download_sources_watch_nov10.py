#!/usr/bin/env python3
"""Nov 10: the official download sources (data/outlines/download-sources.json), the last-seen fingerprint, the low-cost change
check (allowed requests only), and the PC helper listing only new / never-downloaded / changed rows. No server is contacted:
every request goes to a stand-in, and a forbidden host must be refused before the stand-in is even called."""
import json, pathlib, re, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts')); sys.path.insert(0, str(ROOT / 'tools'))
import kpc_master as M  # noqa: E402
import kpc_master_watch as W  # noqa: E402
import kpc_pc_helper as H  # noqa: E402
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


SRC = ROOT / 'data/outlines/download-sources.json'
doc = json.loads(SRC.read_text(encoding='utf-8'))
S = doc['sources']
check('sources file: one entry per hand-filled row, kinds and checks known', len(S) >= 200 and {e['kind'] for e in S.values()} <= {'first-party', 'fallback', 'none'} and {e['check'] for e in S.values()} <= {'bot', 'person'})
blob = SRC.read_text(encoding='utf-8').lower()
check('sources file: no licence flags and no finder notes in public (terms = see the source page)',
      all(f not in blob for f in ('resale', 'non-commercial', 'noncommercial', 'all rights reserved', 'wdpa', 'protected planet', 'finder_notes', 'license_or_terms'))
      and {e['terms'] for e in S.values()} == {'see the source page'})
check('sources file: small (no layers, no zips)', SRC.stat().st_size < 400_000)
check('sources file: a services*.arcgis.com or never-contact file is never check=bot',
      all(e['check'] == 'person' for e in S.values() if e.get('file') and not M.live_ok(e['file'])[0] and not W.catalog_url(e.get('page'))))
check('sources file: the fingerprint is only what a check read (seeded empty)', all(not (e.get('fp') or {}) or e.get('fp_seen') for e in S.values()))

# change check with stand-ins
calls = []


def head(u):
    calls.append(u)
    return 200, {'content-length': state['size'], 'last-modified': 'Mon, 02 Nov 2026 00:00:00 GMT', 'etag': '"a1"'}


def getj(u):
    calls.append(u)
    return {'provenance': {'lastUpdated': state['ver']}, 'files': [{'size': 10}]}


t = pathlib.Path(tempfile.mkdtemp())
sp, np_ = t / 'sources.json', t / 'needs.json'
test = {'format': 1, 'sources': {
    'h900': {'areas': ['US-ZZ'], 'layer': 'zzx', 'layer_url': 'https://services.arcgis.com/abc/arcgis/rest/services/x/FeatureServer/0', 'page': 'https://gis.example.gov/zz',
             'file': 'https://gis.example.gov/zz/parks.zip', 'kind': 'first-party', 'check': 'bot', 'fp': {}, 'terms': 'see the source page'},
    'h901': {'areas': ['US-ZZ'], 'layer': 'zzp', 'page': 'https://www.sciencebase.gov/catalog/item/6759abcfd34edfeb8710a004', 'file': '', 'kind': 'fallback', 'check': 'bot', 'fp': {}},
    'h902': {'areas': ['US-ZZ'], 'layer': 'zzq', 'page': 'https://services1.arcgis.com/q/arcgis/rest/services/y/FeatureServer/0', 'file': 'https://services-eu1.arcgis.com/q/y.zip', 'kind': 'first-party', 'check': 'bot', 'fp': {}},
    'h903': {'areas': ['US-ZZ'], 'layer': 'zzr', 'page': 'https://p.example.gov', 'file': '', 'kind': 'first-party', 'check': 'person', 'fp': {}}}}
sp.write_text(json.dumps(test))
row = M.needs_row('US-ZZ', 'zzx', test['sources']['h900']['layer_url'], 'test', 'test', who='person', date='2026-11-01', src='h900', check='bot')
M.save_needs({'format': M.NEEDS_FORMAT, 'rows': [dict(row, status='done')]}, np_)
state = {'size': '1000', 'ver': '2026-10-01'}
o1 = W.watch(sp, np_, head=head, getj=getj, date='2026-11-10')
d1 = json.loads(sp.read_text())['sources']
check(f'first check sets the baseline, asks nobody ({o1})', o1['changed'] == [] and d1['h900']['fp']['size'] == '1000' and d1['h900']['fp_seen'] == '2026-11-10')
check('the services-eu1 file is refused before any request (never contacted)', not any('arcgis.com' in c for c in calls) and d1['h902'].get('fp') == {})
check('a check=person source is not requested', not any('p.example.gov' in c for c in calls) and o1['person'] == 1)
check('the catalog metadata (ScienceBase JSON) gives the version', d1['h901']['fp'].get('version') == '2026-10-01' and any('format=json' in c for c in calls))
n0 = len(calls)
o2 = W.watch(sp, np_, head=head, getj=getj, date='2026-11-11')
check('no change: nothing reopened, the needs list not touched', o2['changed'] == [] and json.loads(np_.read_text())['rows'][0]['status'] == 'done')
check('one request per URL per run', len(calls) - n0 == 2)
state['size'] = '2000'
o3 = W.watch(sp, np_, head=head, getj=getj, date='2026-11-12')
r3 = json.loads(np_.read_text())['rows'][0]
check(f'a changed file size reopens the done row (source change check) ({o3["changed"]})', o3['changed'] == ['h900'] and r3['status'] == 'open' and r3['source'] == 'change check' and r3['src'] == 'h900')
state['ver'] = '2026-11-12'
o4 = W.watch(sp, np_, head=head, getj=getj, date='2026-11-13')
check('a changed fallback (PAD-US) version is noted but asks nobody', 'h901' in o4['changed'] and all(r['src'] != 'h901' for r in json.loads(np_.read_text())['rows']))
check('a field that stops being sent is not a change', not W.changed({'etag': '"a"', 'size': '1'}, {'size': '1'}))

# robots: a 403 robots.txt = no request of the file
st, _ = (lambda: (None, None))()
cache = {}
check('robots.txt 403 = disallow', M.robots_allows('https://gis.example.gov/zz/parks.zip', lambda u: (403, ''), cache) is False)

# held stays held unless the change check
nd = {'format': M.NEEDS_FORMAT, 'rows': [dict(row, status='held', id='US-ZZ|zzy', layer='zzy')]}
nd, _, _ = M.merge_needs(nd, [dict(row, id='US-ZZ|zzy', layer='zzy', added='2026-11-12')])
check('a held row stays held for a bot row', nd['rows'][0]['status'] == 'held')
nd, _, _ = M.merge_needs(nd, [dict(row, id='US-ZZ|zzy', layer='zzy', added='2026-11-12', source='change check')])
check('a held row reopens for the change check', nd['rows'][0]['status'] == 'open')

# PC helper: only new / never downloaded / changed rows; groups; reminders
rows = [dict(row, id='US-AA|zzx', area='US-AA', status='open', have=0), dict(row, id='US-BB|zzx', area='US-BB', status='open', have=3, source='change check'),
        dict(row, id='US-CC|zzx', area='US-CC', status='done'), dict(row, id='US|zzx', area='US', status='open'),
        dict(row, id='US-DD|h123', area='US-DD', layer='h123', status='open'), dict(row, id='US-EE|zzr', area='US-EE', status='done', check='person', added='2026-07-01')]
pr = H.rows_for_person({'rows': rows})
check('PC helper lists only open fillable rows (not done, not national leads, not bare source ids)', [r['id'] for r in pr] == ['US-AA|zzx', 'US-BB|zzx'])
check('PC helper tags why', H.why_tag(pr[0]) == 'never downloaded' and H.why_tag(pr[1]) == 'CHANGED at the source')
check('PC helper: one download serves rows of the same source', len(H.groups(pr)) == 1 and len(H.groups(pr)[0]) == 2)
rem = H.reminders({'rows': rows}, today='2026-11-10')
check('PC helper reminders: check=person rows downloaded over 90 days ago only', [r['id'] for r in rem] == ['US-EE|zzr'])

# link_rows gives bot rows the hand-filled source
lr = W.link_rows(sp, [{'area': 'US-ZZ', 'layer': 'zzx'}])
check('link_rows links a row to its source', lr[0].get('src') == 'h900' and lr[0].get('check') == 'bot')

# the workflow runs the watch in the join step, no new cron
wf = (ROOT / '.github/workflows/kpc-us-key.yml').read_text(encoding='utf-8')
check('the change check runs inside the US key join step (no new workflow, no cron)', 'kpc_master_cli.py watch --sources data/outlines/download-sources.json' in wf
      and not (ROOT / '.github/workflows/kpc-download-watch.yml').exists())
w = (ROOT / '.github/scripts/kpc_master_watch.py').read_text(encoding='utf-8')
check('the watch never bypasses robots or changes the User-Agent', 'M.robots_allows' in w and 'M.live_ok' in w and "'User-Agent': M.UA" in w)
shutil.rmtree(t, ignore_errors=True)

if __name__ == '__main__':
    print('ALL PASS' if ok else 'FAILED')
    sys.exit(0 if ok else 1)
