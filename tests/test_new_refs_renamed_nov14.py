#!/usr/bin/env python3
"""Nov 14 (KPC owner, 2026-11-14): kpc_new_refs.py catches renamed refs and writes data/new-refs/keeper-list.csv.
Offline: every download is stubbed (POTA from a fixture; WWFF + SOTA fail = skipped, as on a bad day). Checks:
old seen.json (no names) learns names and reports no renames; a rename is never posted / never in 'NEW THIS WEEK'; a new
Kentucky park is still posted exactly as before; a garbled list ('everything renamed') records nothing; DRY=1 writes nothing."""
import csv, json, os, pathlib, subprocess, sys, tempfile

R = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = R / '.github' / 'scripts' / 'kpc_new_refs.py'
fails = []


def check(ok, msg):
    print(('PASS ' if ok else 'FAIL ') + msg)
    if not ok: fails.append(msg)


WRAP = r'''
import io, json, os, runpy, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(sys.argv[1]))
FIX = json.load(open('fixture.json'))
class Resp(io.BytesIO):
    status = 200
    def __enter__(self): return self
    def __exit__(self, *a): return False
def urlopen(req, timeout=None):
    url = req.full_url if hasattr(req, 'full_url') else str(req)
    if url == 'https://api.pota.app/locations': return Resp(json.dumps([{'locationDesc': 'US-KY'}, {'locationDesc': 'US-TN'}]).encode())
    for d in ('US-KY', 'US-TN'):
        if url.endswith('/location/parks/' + d): return Resp(json.dumps(FIX[d]).encode())
    raise OSError('offline test: no network for ' + url.split('/')[2])
urllib.request.urlopen = urlopen
time.sleep = lambda s: None
sys.argv = [sys.argv[1]]
runpy.run_path(sys.argv[0], run_name='__main__')
'''


def parks(tn_names=None, extra_ky=()):
    ky = [{'reference': r, 'name': n, 'latitude': 37.5, 'longitude': -85.0} for r, n in
          [('US-1264', 'Big Bone Lick State Historic Site'), ('US-8144', 'Pine Mountain Trail State Park'), ('US-4484', 'Mammoth Cave National Park')]]
    ky += [{'reference': r, 'name': n, 'latitude': 37.1, 'longitude': -84.2} for r, n in extra_ky]
    tn = [{'reference': f'US-{9000 + i:05d}', 'name': (tn_names or {}).get(i, f'Test Park Number {i}'), 'latitude': 36.0, 'longitude': -86.0}
          for i in range(10050)]
    return {'US-KY': ky, 'US-TN': tn}


def run(d, fix, dry=False):
    (d / 'fixture.json').write_text(json.dumps(fix))
    (d / 'wrap.py').write_text(WRAP)
    env = {k: v for k, v in os.environ.items() if k not in ('GITHUB_ACTIONS', 'KPC_PARKS_WEBHOOK', 'DISCORD_WEBHOOK_URL', 'KPC_DISCORD_WEBHOOK',
                                                           'FB_PAGE_ID', 'FB_PAGE_TOKEN', 'DRY', 'GITHUB_RUN_ID')}
    env['GITHUB_RUN_ID'] = '777'
    if dry: env['DRY'] = '1'
    p = subprocess.run([sys.executable, 'wrap.py', str(SCRIPT)], cwd=d, env=env, capture_output=True, text=True)
    if p.returncode != 0: print(p.stdout[-3000:], p.stderr[-3000:])
    return p


def snap(d):
    return {str(f.relative_to(d)): f.read_bytes() for f in d.rglob('*') if f.is_file() and f.name not in ('fixture.json', 'wrap.py')}


with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t)
    (d / 'data' / 'new-refs').mkdir(parents=True)
    (d / 'locations.json').write_text('[]')
    (d / 'kpc-ky-data.json').write_text(json.dumps({'parks': [{'c': 'US-1264', 'n': 'x', 'la': 37.5, 'lo': -85}, {'c': 'US-8144', 'n': 'x', 'la': 37.5, 'lo': -85},
                                                              {'c': 'US-4484', 'n': 'x', 'la': 37.5, 'lo': -85}, {'c': 'US-9999', 'n': 'New KY', 'la': 37.1, 'lo': -84.2}]}))
    # day 0: an OLD seen.json (no names) that already knows every ref
    f0 = parks()
    old = {'pota': sorted(p['reference'] for L in f0.values() for p in L), 'posted': [], 'to_post': {}}
    (d / 'data/new-refs/seen.json').write_text(json.dumps(old))
    p = run(d, parks(tn_names={5: 'Renamed Before Names Existed'}))
    check(p.returncode == 0, 'old-format seen.json run finishes')
    s = json.loads((d / 'data/new-refs/seen.json').read_text())
    check(len(s.get('names', {}).get('pota', {})) == len(old['pota']), 'names learned for every ref')
    rows = list(csv.DictReader(open(d / 'data/new-refs/keeper-list.csv')))
    check(rows == [], 'first run with names: no renames reported (old format never reads as everything renamed)')
    check('names learned' in p.stdout, 'first run says names were learned')
    # day 1: one rename (TN), one case/punctuation-only change, 'State Park' spelled differently, one new KY park
    fix = parks(tn_names={5: 'Renamed Before Names Existed', 7: 'Brand New Name Lake', 8: 'TEST PARK, NUMBER 8'},
                extra_ky=[('US-9999', 'New KY Park')])
    fix['US-KY'][1]['name'] = 'Pine Mountain Trail State Park.'
    before = snap(d)
    p = run(d, fix, dry=True)
    check(p.returncode == 0 and snap(d) == before, 'DRY=1 writes nothing (seen.json, feed, keeper list untouched)')
    p = run(d, fix)
    check(p.returncode == 0, 'day-1 run finishes')
    feed = json.loads((d / 'kpc-new-refs.json').read_text())
    refs = [i['ref'] for i in feed['items']]
    check(refs == ['US-9999'], f'only the new park is in NEW THIS WEEK (got {refs})')
    ann = json.loads((d / 'kpc-announcements.json').read_text())
    txt = ann['items'][0]['text'] if ann.get('items') else ''
    check('US-9999' in txt and 'US-09007' not in txt, 'the new Kentucky park is posted; the renamed park is not')
    rows = {r['ref']: r for r in csv.DictReader(open(d / 'data/new-refs/keeper-list.csv'))}
    check(list(csv.reader(open(d / 'data/new-refs/keeper-list.csv')))[0] ==
          ['ref', 'name', 'pin_lat', 'pin_lon', 'type', 'change', 'old_name', 'date', 'run_id', 'source'], 'keeper-list.csv columns')
    check(set(rows) == {'US-9999', 'US-09007'}, f'keeper list = the new park + the real rename only (got {sorted(rows)})')
    r = rows.get('US-09007', {})
    check(r.get('change') == 'renamed' and r.get('old_name') == 'Test Park Number 7' and r.get('name') == 'Brand New Name Lake'
          and r.get('type') == 'POTA' and r.get('run_id') == '777' and r.get('source') == 'kpc_new_refs' and r.get('pin_lat') == '36.0', 'rename row filled')
    n = rows.get('US-9999', {})
    check(n.get('change') == 'new' and n.get('old_name') == '' and n.get('pin_lon') == '-84.2', 'new row filled')
    # day 2: a garbled download (every TN name different) records no renames and keeps the names; keeper rows persist
    p = run(d, parks(tn_names={i: f'Garbled {i} Xyz' for i in range(10050)}, extra_ky=[('US-9999', 'New KY Park')]))
    rows2 = {r['ref']: r for r in csv.DictReader(open(d / 'data/new-refs/keeper-list.csv'))}
    check(set(rows2) == set(rows), 'garbled list: no renames recorded; last run\'s rows kept (7-day window)')
    s = json.loads((d / 'data/new-refs/seen.json').read_text())
    check(s['names']['pota']['US-09007'] == 'Brand New Name Lake', 'garbled list: names not overwritten')
    check('looks like a bad download' in p.stdout, 'garbled list: one notice')

print('ALL PASS' if not fails else f'{len(fails)} FAILED')
sys.exit(1 if fails else 0)
