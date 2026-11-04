#!/usr/bin/env python3
"""Offline test for the Nov 4 'trail_check' rows in .github/scripts/kpc_precheck.py (Brandon, Super Head Bot chat, 4:35 AM CST Nov 4 (relayed via Super Head Bot): 'Agree keep the official line';
Brandon, Mapping chat, 4:36 AM CST Nov 4: 'No keep the full length ones we had' for US-9905 / US-9906). data/review/precheck-notes.json trail_check parks get ONE review-pile row
'TRAIL CHECK' (check the kept line against the agency's trail data), are never held, never added to review-hold.json, and a park in
no key file still gets its row. Also checks the real precheck-notes.json lists US-9905 and US-9906 citing both Brandon lines
(the 4:35 AM CST one relayed via Super Head Bot and the 4:36 AM CST one written directly in the Mapping chat)."""
import csv, json, os, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
TOOL = HERE / '.github/scripts/kpc_precheck.py'
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


def run(root, env=None):
    e = dict(os.environ, OUT=str(root / 'out'), DATA=str(root / 'nodata'), KFF_COUNTY_CSV=str(root / 'cty.csv'), **(env or {}))
    e.pop('KPC_PRECHECK_HOLD', None)
    return subprocess.run([sys.executable, str(TOOL)], cwd=root, env=e, capture_output=True, text=True)


real = json.load(open(HERE / 'data/review/precheck-notes.json'))
tc = real.get('trail_check') or {}
check(set(tc) >= {'US-9905', 'US-9906'} and all("Super Head Bot chat, 4:35 AM CST Nov 4" in tc[r].get('by', '') and "Mapping chat, 4:36 AM CST Nov 4" in tc[r].get('by', '') for r in ('US-9905', 'US-9906')),
      "the real precheck-notes.json lists US-9905 + US-9906 as trail checks, citing both Brandon lines (Super Head Bot chat 4:35 AM, Mapping chat 4:36 AM CST)")
check('6.0 km' in tc['US-9905']['keep'] and '6.4 km' in tc['US-9906']['keep'] and all('Forest Service trail data' in tc[r]['check'] for r in ('US-9905', 'US-9906')),
      'the kept lines are the full-length FS lines (6.0 / 6.4 km), to be checked against FS trail data')

with tempfile.TemporaryDirectory() as t:
    R = pathlib.Path(t)
    (R / 'data/us-key').mkdir(parents=True); (R / 'data/ca-key').mkdir(parents=True); (R / 'data/review').mkdir(parents=True)
    parks = {
        'US-1': {'n': 'Alpha National Recreation Trail', 't': 'National Recreation Trail', 'g': 'official', 'c': [], 'line': 1,
                 'm': [['trl1', 'Alpha National Recreation Trail', 0, "official trail line (US Forest Service): the park is the line + POTA's 100-ft band"]]},
        'US-2': {'n': 'Bravo State Park', 't': 'State Park', 'g': 'official', 'c': [], 'm': [['sgxxa2', 'Bravo State Park', 100, 'name']]},
        'US-3': {'n': 'Charlie Trail', 't': 'National Recreation Trail', 'g': 'official', 'c': [], 'line': 1,
                 'm': [['trl3', 'Charlie Trail', 0, 'official trail line (US Forest Service)']], 'far': 'well outside'},
    }
    json.dump({'parks': parks}, open(R / 'data/us-key/US-XX.json', 'w'))
    json.dump({'parks': {}}, open(R / 'data/us-key/overrides.json', 'w'))
    json.dump([['POTA', r, parks[r]['n'], 38.0, -84.0, ''] for r in parks], open(R / 'locations.json', 'w'))
    open(R / 'cty.csv', 'w').write('park,wwff_counties,county_pin,pin_in_county,km_to_listed,wwff_name_vs_pota_rule18\n')
    entry = lambda n: {'name': n, 'keep': 'the saved official US Forest Service line (6.0 km)', 'check': 'check the kept line against US Forest Service trail data',
                       'rejected': 'the shorter new line (2.9 km)', 'by': "Brandon, Super Head Bot chat, 4:35 AM CST Nov 4 2026 (relayed via Super Head Bot): 'Agree keep the official line'; Brandon, Mapping chat, 4:36 AM CST Nov 4 2026: 'No keep the full length ones we had'"}
    json.dump({'trail_check': {'US-1': entry('Alpha National Recreation Trail'), 'US-9': entry('Nine Trail'), 'US-3': entry('Charlie Trail')}},
              open(R / 'data/review/precheck-notes.json', 'w'))
    p = run(R)
    check(p.returncode == 0, f'pre-check finishes ({p.stdout.strip()[-120:]})')
    pile = {r['park']: r for r in csv.DictReader(open(R / 'out/review-pile.csv'))}
    hold = json.load(open(R / 'out/review-hold.json'))['parks']
    counts = json.load(open(R / 'out/counts.json'))
    check('US-1' in pile and pile['US-1']['action'].startswith('TRAIL CHECK (not held') and 'US Forest Service trail data' in pile['US-1']['action']
          and 'Mapping chat, 4:36 AM CST' in pile['US-1']['action'] and 'TRAIL_CHECK' in pile['US-1']['flags'], 'a trail-check park in the key gets one TRAIL CHECK review-pile row')
    check('US-1' not in hold, 'a trail-check park is never held (the kept line stays)')
    check('US-9' in pile and 'TRAIL CHECK' in pile['US-9']['action'] and pile['US-9']['why'] == 'park in no key file read', 'a trail-check park in no key file still gets its row')
    check('US-2' not in pile, 'a park with no flag and no trail check is not added')
    check('US-3' in pile and pile['US-3']['action'].count('TRAIL CHECK') == 1, 'a trail-check park already on the pile for another reason gets the TRAIL CHECK once, appended')
    check(sorted(counts.get('trail_check') or []) == ['US-1', 'US-3', 'US-9'], 'counts.json lists the trail-check parks')
    os.remove(R / 'data/review/precheck-notes.json'); p = run(R)
    pile = {r['park']: r for r in csv.DictReader(open(R / 'out/review-pile.csv'))}
    check('US-1' not in pile and 'US-9' not in pile, 'no trail_check in the notes: nothing added (behaves as before)')

print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
