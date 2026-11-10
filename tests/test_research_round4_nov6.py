#!/usr/bin/env python3
"""Round-4 research return. Confirmed rows only. Report mode does not change a key.

KPC_RESEARCH_SOURCES stays off by default. Rules hashes stay put. Offline.
No request is made to ncnhde.natureserve.org.
"""
import csv, json, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
os.environ.pop('KPC_RESEARCH_SOURCES', None)

import kpc_key_freeze as KF
import kpc_research_sources as RS
import kpc_source_fields as SF

ok = True


def check(cond, msg):
    global ok
    if not cond:
        ok = False
        print('FAIL', msg)
    else:
        print('PASS', msg)


check(KF.rules_hash('us-key') == 'ac708f0afa33', 'US rules hash ac708f0afa33 (approved Nov 10, 2026; declared)')
check(KF.rules_hash('ca-key') == 'd6892ad555d8', 'Canada rules hash d6892ad555d8 (moved Nov 10, declared)')
# Nov 7 world rebuild (B1 B2 B3 B4 B6, world-failed-diagnosis.md section 7; Brandon OK'd the world hash move): kpc_world_key.py
# changed on purpose, so the world rules hash moved 1b50faf1dfe8 -> 6a5969a25d2c. US and CA stay; this check still pins all three.
check(KF.rules_hash('world-key') == '022f06d08d3c', 'world rules hash 022f06d08d3c (moved Nov 10, declared)')
# Nov 7 world rebuild: docs/key-rules-change.txt now declares that approved world-key change (the repo's way to declare an on-purpose
# rules change, see test_maprep_toolbox.py). This file still must not change rules itself: the declaration may only be that one.
_decl = (ROOT / 'docs/key-rules-change.txt')
check(not _decl.exists() or (__import__('re').search(r'KPC-Links #\d+', _decl.read_text(encoding='utf-8')) is not None), 'docs/key-rules-change.txt only carries PR-numbered declarations (rules hashes pinned above)')
check(RS.mode() == 'off', 'flag defaults to off')
check(RS.layers() == [], 'flag off: no research layers')
check(RS.name_aliases() == [], 'flag off: the Georgia alias is not offered')
check(RS.alias_names('Stephen C. Foster State Park') == ['Stephen C. Foster State Park'],
      'flag off: the old Georgia name is not rewritten')

ab = json.loads((ROOT / 'data/maprep/abbreviations.json').read_text(encoding='utf-8'))
added = [r for r in ab['rows'] if r.get('round') == 4]
check(len(added) == 25, f'25 confirmed abbreviations were added ({len(added)})')
check(all(r.get('source_url', '').startswith('http') for r in added), 'each new abbreviation has a source_url')
check(all('State Natural Park' not in (r.get('expansion') or '') for r in ab['rows']),
      'SNP did not gain a State Natural Park meaning')
spas = [r for r in ab['rows'] if r.get('token') == 'spa']
check(len(spas) >= 2 and spas[0]['expansion'] == 'Special Protection Area' and spas[1]['expansion'] == 'State Preservation Area',
      'SPA keeps Special Protection Area first and State Preservation Area beside it')
check(any(r.get('dotted') == 'PFA' and r.get('expansion') == 'Public Fishing Area' for r in added), 'PFA was added')
foster = next(r for r in added if r.get('dotted') == 'Stephen C. Foster')
check(foster.get('expand') is False and 'Okefenokee' in (foster.get('note') or '') and '2026-09-01' in (foster.get('note') or ''),
      'Stephen C. Foster is stored as an alias note and is not an auto-rename expansion')

ag = RS.load_agencies()
marked = [a for p in ag['places'].values() for a in p['agencies'] if a.get('round4', {}).get('confirmed')]
check(len(marked) == 34, f'34 confirmed agency rows were recorded ({len(marked)})')
tn = next(a for a in ag['places']['TN']['agencies'] if a['name'] == 'Tennessee State Parks')
check(tn['gis']['url'] == 'https://tdeconline.tn.gov/arcgis/rest/services/TN_Natural_Areas/MapServer' and tn['gis']['verified'] is True,
      'Tennessee State Parks GIS is the TDEC REST service')
check('cleanairtn.org' not in json.dumps(tn) and 'cleanairtn.org' not in json.dumps(ag),
      'the Tennessee mirror host is not in the agency directory')
nj = next(a for a in ag['places']['NJ']['agencies'] if a['name'] == 'New Jersey State Park Service (DEP)')
check(nj['finder']['url'] == '' and nj['finder']['verified'] is False and 'unverified' in nj['finder']['source'] and 'not used' in nj['finder']['source'],
      'the New Jersey finder is unverified and was not used')
check(nj['gis']['url'].startswith('https://mapsdep.nj.gov/') and 'parks/maps' not in (nj['finder']['url'] or ''),
      'the New Jersey GIS layer was stored and the stale maps finder was not')
check('33TOOklri9xpic7U' not in json.dumps(ag), 'Grant County NM server is not in the agency file')

os.environ['KPC_RESEARCH_SOURCES'] = 'report'
pages = {p['ref']: p for p in RS.official_suggestions()}
need = ['US-3692', 'US-4373', 'US-0990', 'US-4224', 'US-8393', 'US-7656', 'US-12143', 'CA-4000', 'CA-5653', 'CA-5877']
check(all(ref in pages and pages[ref]['suggestion'] == 'suggestion, never auto-replace' for ref in need),
      'the 10 confirmed official pages are suggestions')
check(pages['US-12143'].get('two_name') == 'separate units, report only' and 'possible wrong page' in (pages['US-12143'].get('suggest_note') or ''),
      "Devil's Playground / Redwash is separate units and a possible wrong page")
check(all(pages[ref].get('two_name') == 'one unit, report only' for ref in ('US-0990', 'CA-4000', 'CA-5653', 'CA-5877')),
      'Donnelley/DePue and the three Canada titles are one unit')
one = {x['ref']: x for x in RS.one_units(None)}
sep = {x['ref'] for x in RS.separate_units('us')}
check('US-12143' in sep and one['US-0990']['claim'] == 'ONE_UNIT' and one['CA-4000']['joins_changed'] is False,
      'the two-name report code carries SEPARATE_UNITS and ONE_UNIT')
check(RS.separate_units('ca') == [], 'Canada separate-unit list stays empty')
check('US-3475' not in sep and 'US-3891' not in sep, 'Montara and Campbells are not asserted as separate units')
review = {x['ref']: x['why'] for x in RS.review_list('us')}
check(review == {'US-3475': 'round 4 UNCLEAR, needs official confirmation',
                 'US-3891': 'round 4 UNCLEAR, needs official confirmation'},
      'Montara and Campbells are on the review list')
aliases = RS.name_aliases()
check(len(aliases) == 1 and aliases[0]['old_name'] == 'Stephen C. Foster State Park'
      and aliases[0]['new_name'] == 'Okefenokee State Park' and aliases[0]['effective'] == '2026-09-01'
      and aliases[0]['auto_rename'] is False and aliases[0]['source'].startswith('https://gastateparks.org/'),
      'the Georgia rename is a report-only alias with the DNR source')
check(RS.alias_names('Stephen C. Foster State Park') == ['Stephen C. Foster State Park', 'Okefenokee State Park'],
      'report mode keeps the old name and adds the new name')
sample = {'ref': 'US-2200', 'n': 'Stephen C. Foster State Park'}
raw = json.dumps(sample, sort_keys=True)
check(json.dumps(RS.leave_key_unchanged(sample), sort_keys=True) == raw, 'the alias does not rewrite a key row')

cat = RS.catalog()
round4 = [r for r in cat if r.get('pack') == 'round4']
check(len(round4) == 9 and all(r.get('use') == 'report' and r.get('republish') is False for r in round4),
      f'9 new catalog sources are report only ({len(round4)})')
pei = [r for r in cat if 'GeoLinc_Wildlife_Management_Area' in (r.get('url') or '')]
check(len(pei) == 1 and pei[0].get('use') == 'report' and pei[0].get('round4_confirmed') is True,
      'PEI WildlifeManagementArea2025 was already catalogued and is confirmed again, report only')
check(all('services.arcgis.com' not in (r.get('url') or '') for r in cat), 'no services.arcgis.com URL is in the catalog')
check(all('ncnhde.natureserve.org' not in (r.get('url') or '') for r in cat), 'ncnhde.natureserve.org is not in the catalog')
check(all('gisportaldev.dot.ny.gov' not in (r.get('url') or '') for r in cat), 'the NY OPRHP dev portal is not in the catalog')
check(all('33TOOklri9xpic7U' not in (r.get('url') or '') for r in cat), 'Grant County NM is not in the catalog')
for key, sample_url in (
    ('ga_other_state14', 'https://data.georgiaspatial.org/data/statewide/dnr/fed_lands/other_state14.zip'),
    ('ns_protected', 'https://data.novascotia.ca/api/geospatial/ticv-5du5?method=export&format=GeoJSON'),
    ('mb_refuges', 'https://geoportal.gov.mb.ca/api/download/v1/items/25b9a5e1781c4bd58d5c8dc8bde07401/shapefile?layers=0'),
    ('ie_np_boundary', 'https://www.npws.ie/sites/default/files/general/Killarney-National-Park-Boundary-Map_v103_20220119.zip'),
):
    check(SF.find(sample_url) is None and SF.research_find(sample_url)['key'] == key,
          key + ' is research-only and is not a builder source')

dni = (ROOT / 'data/research-sources/do_not_ingest.csv').read_text(encoding='utf-8')
check('ncnhde.natureserve.org' in dni, 'NC MAREA host is on do_not_ingest')
check('layer 3' in dni and 'layer 4' in dni, 'SC Public Lands layers 3 and 4 are on do_not_ingest')
check('gisportaldev.dot.ny.gov' in dni, 'NY OPRHP dev portal stays on do_not_ingest')
check('Wildlife_Refuges_06_Feb_2019' in dni, 'the Manitoba live REST is on do_not_ingest')

fix = json.loads((ROOT / 'tests/fixtures/round4_joint_nested.json').read_text(encoding='utf-8'))
check(len(fix['joint']) == 3 and len(fix['nested']) == 7, '3 joint and 7 nested fixtures')
check(all(r.get('spot_status') == 'confirmed' for r in fix['joint'] + fix['nested']), 'every fixture row was confirmed')
check(all('services.arcgis.com' not in (r.get('source_url') or '') and 'ncnhde.natureserve.org' not in (r.get('source_url') or '')
           for r in fix['joint'] + fix['nested']),
      'fixture source URLs are not the banned hosts')
check(any('Cane Creek' in r['park_or_area'] for r in fix['joint']), 'Cane Creek is a joint fixture')
check(any('Rouge' in r['park_or_area'] for r in fix['joint']), 'Rouge National Urban Park is a joint fixture')
check(any('A Tracts' in r['child_or_tract_name'] for r in fix['nested']), 'West Kentucky A Tracts is a nested fixture')

left = (ROOT / 'docs/round4-left-out.md').read_text(encoding='utf-8')
for phrase in ('partly_sourced', 'cleanairtn', 'Montara', 'services.arcgis.com', 'ScienceBase PAD-US',
               'ncnhde.natureserve.org', 'KPC_RESEARCH_SOURCES stays off', 'Okefenokee',
               'round 4 UNCLEAR, needs official confirmation'):
    check(phrase in left, 'left-out list mentions ' + phrase)

os.environ.pop('KPC_RESEARCH_SOURCES', None)
check(RS.mode() == 'off' and RS.layers() == [] and RS.name_aliases() == [], 'the flag is off again at the end')
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
