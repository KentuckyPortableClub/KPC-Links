"""Monthly check: are the site's Kentucky reference lists still current?

Compares kpc-ky-data.json (what the maps, planners and checkers use) with the official lists:
  - POTA parks in US-KY        (api.pota.app)
  - SOTA summits in W4K        (api2.sota.org.uk)
  - WWFF/KFF areas in Kentucky (wwff.co directory)
Nothing is changed automatically. New, retired or renamed references are listed in one GitHub issue
labelled "ref-check", which closes itself when the lists match.
"""
import csv
import datetime as dt
import io
import json
import os
import pathlib
import re
import sys
import time
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from kpc_issue import report  # noqa: E402

UA = 'Mozilla/5.0 (compatible; KPC-reference-check; +https://kentuckyportableclub.github.io/KPC-Links/)'
DATA = json.load(open('kpc-ky-data.json', encoding='utf-8'))
EXTRA = {}  # extra details for new references (location), shown in the report
# References the club has decided to leave off for now. Listed in the report, but not counted as problems.
ON_HOLD = {'US-0608': 'Ohio River Islands NWR, on hold (Oct 2026)'}


def get(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json,text/csv,*/*'})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(5 * (i + 1))
    raise last


def notice(title, msg):
    print('::notice title=%s::%s' % (title, str(msg).replace('%', '%25').replace('\n', '%0A')), flush=True)


def ours(key, code='c', name='n'):
    return {x[code]: x.get(name, '') for x in DATA.get(key, []) if x.get(code)}


def pota():
    rows = json.loads(get('https://api.pota.app/location/parks/US-KY'))
    return {r['reference']: r.get('name', '') for r in rows if r.get('reference', '').startswith('US-') and r.get('active', 1) in (1, True, '1')}


def sota():
    today = dt.date.today().isoformat()
    assoc = json.loads(get('https://api2.sota.org.uk/api/associations/W4K'))
    regions = [r['regionCode'] for r in assoc.get('regions', []) if r.get('regionCode')]
    out = {}
    for rc in regions:
        for s in json.loads(get('https://api2.sota.org.uk/api/regions/W4K/' + rc)).get('summits', []):
            vt = str(s.get('validTo', '9999'))[:10]
            vf = str(s.get('validFrom', '0000'))[:10]
            if vf <= today <= vt:
                out[s['summitCode']] = s.get('name', '')
    return out


def wwff():
    text = get('https://wwff.co/wwff-data/wwff_directory.csv')
    rdr = csv.DictReader(io.StringIO(text))
    cols = rdr.fieldnames or []
    notice('WWFF columns', ', '.join(cols))
    out = {}
    for r in rdr:
        ref = (r.get('reference') or '').strip()
        if not ref.startswith('KFF-'):
            continue
        if (r.get('status') or 'active').strip().lower() not in ('active', ''):
            continue
        vals = ' '.join(str(v) for k, v in r.items() if k and k.lower() in ('state', 'region', 'county', 'iota', 'notes', 'name'))
        if re.search(r'\b(US-)?KY\b|Kentucky', vals):
            out[ref] = r.get('name', '')
            EXTRA[ref] = '(%s, %s · %s)' % (r.get('latitude', ''), r.get('longitude', ''), r.get('county', '') or r.get('region', ''))
    return out


checks = [('POTA parks', 'parks', pota), ('SOTA summits (W4K)', 'summits', sota), ('WWFF / KFF areas', 'kff', wwff)]
sections, problems, status = [], 0, {}
for label, key, fn in checks:
    mine = ours(key)
    try:
        official = fn()
    except Exception as e:  # noqa: BLE001
        status[label] = 'could not check: %s' % e
        sections.append('## %s\nCould not reach the official list this time (%s). Will try again next month.\n' % (label, e))
        continue
    if not official:
        status[label] = 'official list came back empty; skipped'
        sections.append('## %s\nThe official list came back empty, so nothing was compared.\n' % label)
        continue
    held = sorted(c for c in set(official) - set(mine) if c in ON_HOLD)
    new = sorted(set(official) - set(mine) - set(ON_HOLD))
    gone = sorted(set(mine) - set(official))
    def nm(x):
        return re.sub(r'\W', '', re.sub(r'(?i)unnamed\s+summit', '', x).lower())
    renamed = sorted(c for c in set(mine) & set(official) if official[c] and mine[c] and nm(official[c]) != nm(mine[c]))
    status[label] = 'site %d / official %d / new %d / gone %d / renamed %d' % (len(mine), len(official), len(new), len(gone), len(renamed))
    notice(label, status[label])
    n = len(new) + len(gone)
    problems += n
    lines = ['## %s' % label, 'Site: %d · Official: %d' % (len(mine), len(official)), '']
    if new:
        lines += ['**New on the official list, missing from the site (%d):**' % len(new)] + ['- %s %s %s' % (c, official[c], EXTRA.get(c, '')) for c in new[:80]] + ['']
    if gone:
        lines += ['**On the site but not on the official active list (%d):** retired, or not in Kentucky per the official list.' % len(gone)] + ['- %s %s' % (c, mine[c]) for c in gone[:80]] + ['']
    if renamed:
        lines += ['<details><summary>Name differences (%d), usually just wording</summary>' % len(renamed), ''] + \
                 ['- %s: site "%s" · official "%s"' % (c, mine[c], official[c]) for c in renamed[:80]] + ['', '</details>', '']
    if held:
        lines += ['_On hold (not counted): ' + ', '.join('%s (%s)' % (c, ON_HOLD[c]) for c in held) + '_', '']
    if not (new or gone or renamed):
        lines += ['✅ Matches.', '']
    sections.append('\n'.join(lines))

when = dt.date.today().strftime('%b %d, %Y')
body = '_Checked %s against the official POTA, SOTA and WWFF lists. Site data last updated: %s._\n\n' % (when, DATA.get('updated', '?')) + \
       '\n'.join(sections) + \
       '\nThe site data lives in `kpc-ky-data.json`. Ask Claude (or edit it) to add new references with their county, location and links.\n' + \
       'This issue updates on the 1st of each month and closes itself when the lists match. Run it any time: Actions → KPC Reference Check → Run workflow.'
print(body)
notice('Reference check', json.dumps(status))
if os.getenv('GITHUB_ACTIONS'):
    report('ref-check', '📍 Kentucky reference lists: %d change%s to review (%s)' % (problems, '' if problems == 1 else 's', when), body, problems)
