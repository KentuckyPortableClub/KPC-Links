#!/usr/bin/env python3
"""KY fishing-lake shore outlines stay report-only.

Kingfisher (US-13599) and Carpenter (US-13600) each get their own outline:
PAD-US water unioned with the Daviess parcel pieces that touch that water.
Guist Creek's bank parcel is not fetched (services2 robots 403). Beaver,
Bullock Pen and Boltz stay water-only. The KY key outlines and the rules
hashes are not changed. KPC_RESEARCH_SOURCES defaults to off.
"""
import json, os, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
os.environ.pop('KPC_RESEARCH_SOURCES', None)

import kpc_key_freeze as KF
import kpc_pin_edge as PE
import kpc_research_sources as RS

ok = True
LABEL = 'county tax parcel, KDFWR owner, not a survey'
SHORE = ROOT / 'data' / 'research-sources' / 'ky-fishing-shore.json'


def check(cond, msg):
    global ok
    ok = ok and bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


def samples(geom, n=9):
    rings = PE.geojson_rings(geom)
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    if not xs:
        return []
    found = []
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    for i in range(1, n):
        for j in range(1, n):
            lon = x0 + (x1 - x0) * i / n
            lat = y0 + (y1 - y0) * j / n
            if PE.inside(lat, lon, rings):
                found.append((lat, lon))
    return found


check(KF.rules_hash('us-key') == 'a066624520b4', 'US rules hash stays a066624520b4')
check(KF.rules_hash('ca-key') == '8feccbb7d9ee', 'Canada rules hash stays 8feccbb7d9ee')
# Nov 7 world rebuild (B1 B2 B3 B4 B6, world-failed-diagnosis.md section 7; Brandon OK'd the world hash move): kpc_world_key.py
# changed on purpose, so the world rules hash moved 1b50faf1dfe8 -> 6a5969a25d2c. US and CA stay; this check still pins all three.
check(KF.rules_hash('world-key') == '6a5969a25d2c', 'world rules hash stays 6a5969a25d2c')
check('kpc_research_sources.py' in KF.NOT_RULES, 'the shore reader is not a rule file')

kept = [
    'data/ky-answer-key.json', 'ky-padus-parks.geojson', 'ky-kpc-drawn.geojson',
    '.github/scripts/kpc_us_key.py', '.github/scripts/kpc_key_rules.py',
    '.github/scripts/kpc_match.py', '.github/scripts/kpc_key_facts.py',
    '.github/key-rules-version.json',
]
diff = subprocess.run(['git', 'diff', '--name-only', 'origin/main', '--', *kept],
                      cwd=ROOT, capture_output=True, text=True, timeout=30)
changed = [ln for ln in diff.stdout.splitlines() if ln.strip()]
check(diff.returncode == 0 and not changed, 'KY key outlines and rule files are unchanged'
      + ((' (' + ', '.join(changed) + ')') if changed else ''))
# Links #53: the Canada and US key workflows checkout .gz and materialize hardlook.json. Those two files may differ from main.
allowed_wf = {'.github/workflows/kpc-ca-key.yml', '.github/workflows/kpc-us-key.yml'}
wf = subprocess.run(['git', 'diff', '--name-only', 'origin/main', '--', '.github/workflows'],
                    cwd=ROOT, capture_output=True, text=True, timeout=30)
changed_wf = [ln.strip() for ln in wf.stdout.splitlines() if ln.strip()]
# Nov 7 world fix part A (hash-neutral; Brandon kept every approved layer): the held retry + layer checkpoints in the world key
# workflow and the fuller saved-shapes list may differ from main too. Neither touches the KY key; the rules hashes are checked above.
world_wf = {'.github/workflows/kpc-world-key.yml', '.github/workflows/kpc-world-cache.yml'}
# Nov 7 round 4: the by-hand app-packs and KML/GPX workflows and the optional 2-fer publish trigger. None of them is a key workflow.
round4_wf = {'.github/workflows/kpc-app-packs.yml', '.github/workflows/kpc-ky-mapfiles.yml', '.github/workflows/kpc-fers-publish.yml', '.github/workflows/kpc-new-refs.yml'}
# Nov 8 (Quality, US-42446831487): the key-check workflow reads the RELEASED keys (read-only); not a key workflow, no rule file.
nov8_wf = {'.github/workflows/kpc-key-postcheck.yml'}
extra_wf = [ln for ln in changed_wf if ln not in allowed_wf | world_wf | round4_wf | nov8_wf]
check(wf.returncode == 0 and not extra_wf, 'workflows other than the Canada and US key gzip checkouts are unchanged'
      + ((' (' + ', '.join(extra_wf) + ')') if extra_wf else ''))
if set(changed_wf) & allowed_wf:
    body = subprocess.run(['git', 'diff', 'origin/main', '--', *sorted(allowed_wf)],
                          cwd=ROOT, capture_output=True, text=True, timeout=30).stdout
    # Nov 7: Links #53 is on main, so a later US key workflow change (the problem solver step) no longer carries the hard-look
    # lines; the check applies only to a diff that touches the hard-look checkout.
    check(('hardlook' not in body) or ('hardlook.json.gz' in body and '--materialize' in body and 'external-results.json.gz' in body),
          'the Canada and US workflow diff is the gzip checkout and the hard-look materialize')

check(RS.mode() == 'off', 'KPC_RESEARCH_SOURCES still defaults to off')
check(RS.fishing_shore_overlays() == [], 'flag off: shore overlays are not offered')
check(RS.fishing_shore_report() is None, 'flag off: the shore report is not offered')
check(RS.layers() == [], 'flag off: research layers stay empty')

doc = json.loads(SHORE.read_text(encoding='utf-8'))
raw = SHORE.read_text(encoding='utf-8')
check(doc.get('source_label') == LABEL, 'source label is the county tax parcel line')
check(doc.get('report_only') is True and doc.get('applied_to_key') is False, 'the file says it is report only')
check(doc.get('shared_outline') is False and doc.get('piece_assigned_twice') is False, 'the file says the parks are separate')
check('33TOOklri9xpic7U' not in raw, 'the banned Grant County server is not in the shore file')
check(doc.get('robots', {}).get('status') == 404, 'Owensboro robots.txt was a 404 (no disallow)')
check(all(x.get('host') == 'services2.arcgis.com' and x.get('parcel') == '070-00-002B' for x in doc.get('not_fetched') or []),
      'the Shelby parcel is listed as not fetched')
check('services2.arcgis.com' not in (doc.get('service') or ''), 'the live service is Owensboro, not Shelby')

by_ref = {row['ref']: row for row in doc['lakes']}
check(by_ref['US-13598']['status'] == 'needs person' and by_ref['US-13598']['outline'] == 'water only', 'Beaver stays water-only')
check(by_ref['US-13606']['status'] == 'needs person' and by_ref['US-13607']['status'] == 'needs person', 'Bullock Pen and Boltz need a person')
guist = by_ref['US-13601']
check(guist['status'] == 'needs person' and guist['outline'] == 'water only' and guist['access_parcel'] == '070-00-002B',
      'Guist keeps the water outline and the bank parcel needs a person')
check('do not use the Guist PAD-US' in guist['padus_caution'], 'the Guist PAD-US caution stays')

pieces = [f for f in doc['overlays'] if f['properties']['role'] == 'parcel-piece']
outlines = [f for f in doc['overlays'] if f['properties']['role'] == 'shore-outline']
check(len(pieces) == 3 and len(outlines) == 2, 'three pieces and two outlines')
assigned = {}
for f in pieces:
    pr = f['properties']
    check(pr['source'] == LABEL and pr['parcel_id'] == '097-A0-00-060-00-000', f"piece {pr['fid']} keeps the source line and parcel id")
    check(pr['assigned_to'] == [pr['ref']] and pr['also_assigned'] is False, f"piece {pr['fid']} has one assignment")
    assigned.setdefault(pr['fid'], set()).add(pr['ref'])
check(all(len(v) == 1 for v in assigned.values()), 'no piece is assigned to both lakes')
by_fid = {f['properties']['fid']: f for f in pieces}
check(by_fid[31356]['properties']['ref'] == 'US-13599' and abs(by_fid[31356]['properties']['county_acres'] - 22.79) < 0.01, '22.79 ac piece is Kingfisher')
check(by_fid[31376]['properties']['ref'] == 'US-13599' and abs(by_fid[31376]['properties']['county_acres'] - 17.30) < 0.011, '17.30 ac piece is Kingfisher')
check(by_fid[31486]['properties']['ref'] == 'US-13600' and abs(by_fid[31486]['properties']['county_acres'] - 76.11) < 0.01, '76.11 ac piece is Carpenter')
check(by_fid[31376]['properties']['pin_inside']['US-13599'] is True and by_fid[31376]['properties']['pin_inside']['US-13600'] is False,
      'the Kingfisher pin is inside the 17.30 piece only')
check(by_fid[31486]['properties']['pin_inside']['US-13600'] is True and by_fid[31486]['properties']['pin_inside']['US-13599'] is False,
      'the Carpenter pin is inside the 76.11 piece only')
check(by_fid[31356]['properties']['gap_m']['US-13600'] > 5 and by_fid[31376]['properties']['gap_m']['US-13600'] > 5,
      'the Kingfisher pieces do not touch Carpenter')
check(by_fid[31486]['properties']['gap_m']['US-13599'] > 5 and by_fid[31486]['properties']['gap_m']['US-13600'] == 0,
      'the Carpenter piece does not touch Kingfisher water')

out_by = {f['properties']['ref']: f for f in outlines}
kf, cp = out_by['US-13599'], out_by['US-13600']
check(abs(PE.acres_geojson(kf['geometry']) - 41.67) < 0.05, f"Kingfisher outline measures about 41.67 ac ({PE.acres_geojson(kf['geometry']):.2f})")
check(abs(PE.acres_geojson(cp['geometry']) - 79.99) < 0.05, f"Carpenter outline measures about 79.99 ac ({PE.acres_geojson(cp['geometry']):.2f})")
check(kf['properties']['water_inside_outline_pct'] == 100.0 and cp['properties']['water_inside_outline_pct'] == 100.0,
      'each water body is entirely inside its own outline')
check(abs(kf['properties']['water_inside_parcel_pct'] - 95.5) < 0.2, 'about 95.5% of Kingfisher water is inside its pieces')
check(abs(cp['properties']['water_inside_parcel_pct'] - 94.4) < 0.2, 'about 94.4% of Carpenter water is inside its piece')
check(kf['properties']['pieces'] == [31356, 31376] and cp['properties']['pieces'] == [31486], 'outline piece lists do not overlap')
check('US-13600' in kf['properties']['separate_from'] and 'US-13599' in cp['properties']['separate_from'], 'each outline names the other park as separate')

pad = json.loads((ROOT / 'ky-padus-parks.geojson').read_text(encoding='utf-8'))
water = {f['properties']['ref']: f['geometry'] for f in pad['features'] if f['properties'].get('ref') in ('US-13599', 'US-13600')}
kf_rings = PE.geojson_rings(kf['geometry'])
cp_rings = PE.geojson_rings(cp['geometry'])
piece_rings = {fid: PE.geojson_rings(feat['geometry']) for fid, feat in by_fid.items()}

def share(pts, rings):
    if not pts:
        return 0.0
    return sum(1 for la, lo in pts if PE.inside(la, lo, rings)) / len(pts)

kf_pts = samples(water['US-13599'])
cp_pts = samples(water['US-13600'])
check(len(kf_pts) >= 8 and len(cp_pts) >= 8, f'water samples ({len(kf_pts)}, {len(cp_pts)})')
check(share(kf_pts, kf_rings) == 1 and share(cp_pts, cp_rings) == 1, 'sampled water points sit inside their own outline')
check(share(kf_pts, cp_rings) == 0 and share(cp_pts, kf_rings) == 0, 'sampled water does not fall in the other outline')
kf_piece = piece_rings[31356] + piece_rings[31376]
check(share(kf_pts, kf_piece) >= 0.90, f'most Kingfisher water samples are inside its pieces ({share(kf_pts, kf_piece):.2f})')
check(share(cp_pts, piece_rings[31486]) >= 0.90, f'most Carpenter water samples are inside its piece ({share(cp_pts, piece_rings[31486]):.2f})')
check(share(kf_pts, piece_rings[31486]) == 0 and share(cp_pts, kf_piece) == 0, 'no water sample falls in the other lake\'s pieces')

# pins from the park file
pins = {'US-13599': (37.8469, -86.9736), 'US-13600': (37.8452, -86.9784)}
check(PE.inside(*pins['US-13599'], piece_rings[31376]) and not PE.inside(*pins['US-13599'], piece_rings[31356])
      and not PE.inside(*pins['US-13599'], piece_rings[31486]), 'Kingfisher pin is inside only the 17.30 piece')
check(PE.inside(*pins['US-13600'], piece_rings[31486]) and not PE.inside(*pins['US-13600'], piece_rings[31356])
      and not PE.inside(*pins['US-13600'], piece_rings[31376]), 'Carpenter pin is inside only the 76.11 piece')
check(not any(f['properties']['ref'] == 'US-13601' for f in doc['overlays']), 'Guist has no overlay geometry')

os.environ['KPC_RESEARCH_SOURCES'] = 'report'
got = RS.fishing_shore_overlays()
check(len(got) == len(doc['overlays']) and {f['properties']['ref'] for f in got if f['properties']['role'] == 'shore-outline'} == {'US-13599', 'US-13600'},
      'report mode returns the two shore outlines')
rep = RS.fishing_shore_report()
check(rep and rep.get('applied_to_key') is False and 'overlays' not in rep, 'report mode returns the acre report without rewriting a key')
check(RS.leave_key_unchanged({'parks': {}}) == {'parks': {}}, 'report mode still does not edit a key document')
os.environ.pop('KPC_RESEARCH_SOURCES', None)
check(RS.fishing_shore_overlays() == [], 'the flag is off again after the report read')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
