#!/usr/bin/env python3
"""Round-3 research return. Confirmed and sourced rows only. Report mode does not change a key.

KPC_RESEARCH_SOURCES stays off by default. Rules hashes stay put. Offline.
"""
import csv, json, os, pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
os.environ.pop('KPC_RESEARCH_SOURCES', None)

import kpc_key_freeze as KF
import kpc_research_sources as RS
import kpc_source_fields as SF
import kpc_tracts as TR

ok = True


def check(cond, msg):
    global ok
    if not cond:
        ok = False
        print('FAIL', msg)
    else:
        print('PASS', msg)


check(KF.rules_hash('us-key') == 'a066624520b4', 'US rules hash stays a066624520b4')
check(KF.rules_hash('ca-key') == '8feccbb7d9ee', 'Canada rules hash stays 8feccbb7d9ee')
# Nov 7 world rebuild (B1 B2 B3 B4 B6, world-failed-diagnosis.md section 7; Brandon OK'd the world hash move): kpc_world_key.py
# changed on purpose, so the world rules hash moved 1b50faf1dfe8 -> 6a5969a25d2c. US and CA stay; this check still pins all three.
check(KF.rules_hash('world-key') == '6a5969a25d2c', 'world rules hash stays 6a5969a25d2c')
# Nov 7 world rebuild: docs/key-rules-change.txt now declares that approved world-key change (the repo's way to declare an on-purpose
# rules change, see test_maprep_toolbox.py). This file still must not change rules itself: the declaration may only be that one.
_decl = (ROOT / 'docs/key-rules-change.txt')
check(not _decl.exists() or (__import__('re').search(r'KPC-Links #\d+', _decl.read_text(encoding='utf-8')) is not None), 'docs/key-rules-change.txt only carries PR-numbered declarations (rules hashes pinned above)')
check(RS.mode() == 'off', 'flag defaults to off')
check(RS.layers() == [], 'flag off: no research layers are offered to a builder')
check(RS.official_suggestions() == [], 'flag off: official pages are not suggested')
check(RS.link_postcheck([{'ref': 'US-3475', 'area': 'US-CA', 'name': 'Montara', 'kind': 'State Beach', 'web': ''}]) == [],
      'flag off: the link post-check returns nothing')

ag = RS.load_agencies()
check(RS.AGENCIES_FILE == ROOT / 'data' / 'maprep' / 'agencies.json', 'the Tool Box and the post-check read one agency file')
check('33TOOklri9xpic7U' not in json.dumps(ag), 'Grant County NM server is not in the agency file')
ak = next(a for a in ag['places']['AK']['agencies'] if 'State Parks' in a['name'])
check(ak['home']['url'] == 'https://dnr.alaska.gov/parks/' and ak['home']['verified'] is True,
      'Alaska State Parks home is the confirmed round-3 URL')
az = next(a for a in ag['places']['AZ']['agencies'] if 'Game' in a['name'])
check(az['home']['url'] == 'https://azgfd.com/' and az['home']['verified'] is False,
      'Arizona Game and Fish stays the old unverified URL (the new one was blocked)')
fl = next(a for a in ag['places']['FL']['agencies'] if a['name'].startswith('Florida State Parks'))
check(fl['gis']['url'] == 'https://geodata.dep.state.fl.us/',
      'Florida State Parks GIS was not replaced from a blocked row')
gaps = (ROOT / 'docs/maprep-agency-gaps.txt').read_text(encoding='utf-8')
check('AK | Alaska State Parks (DNR) | home |' not in gaps, 'a confirmed Alaska home URL is no longer a gap')
check('AZ | Arizona Game & Fish Department | home | unverified | https://azgfd.com/' in gaps,
      'the blocked Arizona home stays on the gap list')

ab = (ROOT / 'data/research-sources/abbreviations.csv').read_text(encoding='utf-8')
check('US-LA,SHS,State Historic Site' in ab, 'sourced LA SHS was added')
check('round-3 blocked' not in ab, 'the blocked LA State Park abbreviation was not added')
check('State Commemorative Area' not in ab and 'round-3 from_memory' not in ab,
      'from-memory abbreviations were not added')
check(RS.canon_name('a SPA', report=True) == 'a special protection area',
      'a later SPA row does not replace Special Protection Area')
check(RS.name_score('Foo SPA', 'Foo Special Protection Area', report=True) == 96,
      'Foo SPA vs Foo Special Protection Area still scores 96')
check(RS.name_score('Foo SPA', 'Foo State Preservation Area', report=True) == 96,
      'Louisiana SPA is a second expansion and still matches its own words')
check(RS.canon_name('Los Adaes SHS', report=True) == 'los adaes state historic site', 'SHS expands in report mode')
game = RS.workbench_canon('Allegan State Game Area', report=True)[1]
wild = RS.workbench_canon('Allegan State Wildlife Area', report=True)[1]
check('game' in game and game != wild, f'game stays a distinguishing word ({game} vs {wild})')

os.environ['KPC_RESEARCH_SOURCES'] = 'report'
pages = RS.official_suggestions()
check(len(pages) == 22 and all(p['suggestion'] == 'suggestion, never auto-replace' for p in pages),
      f'confirmed official pages are suggestions ({len(pages)})')
check(sum(1 for p in pages if p.get('two_name') == 'separate units, report only') == 4,
      'the separate-unit pairs are marked on the page list')
row = RS.link_postcheck([{'ref': 'US-3475', 'area': 'US-CA', 'name': 'Montara Beach and McNee Ranch State Beach',
                          'kind': 'State Beach', 'web': '', 'map_check': {}}], ag)[0]
check(row['suggest_url'].startswith('https://parks.ca.gov/') and row['suggestion'] == 'suggestion, never auto-replace'
      and row.get('two_name') != 'separate units, report only',
      'Montara suggests the confirmed page and is not flagged as separate units')
before = {'ref': 'US-3475', 'web': ''}
RS.link_postcheck([dict(before)], ag)
check(before == {'ref': 'US-3475', 'web': ''}, 'the suggestion is not written back onto the park')
import kpc_two_name_check as TN
sep = {x['ref'] for x in RS.separate_units('us')}
check(sep == {'US-3692', 'US-4373', 'US-4224', 'US-12143'},
      'the two-name report lists the separate pairs, including Devil\'s Playground / Redwash')
check('US-3475' not in sep and 'US-3891' not in sep, 'Montara and Campbells are not asserted as separate units')
review = {x['ref']: x['why'] for x in RS.review_list('us')}
check(review == {'US-3475': 'round 4 UNCLEAR, needs official confirmation',
                 'US-3891': 'round 4 UNCLEAR, needs official confirmation'},
      'Montara and Campbells are on the review list')
check(RS.separate_units('ca') == [], 'Canada has none of those pairs')
stamped_sep, stamped = TN.stamp_separate('us', [{'park': ref} for ref in sorted(sep)] + [{'park': 'US-0001'}])
flagged = {r['park'] for r in stamped if r.get('looks_like_separate_units')}
check(flagged == sep and all(x.get('joins_changed') is False for x in stamped_sep),
      'the two-name report code flags those separate pairs and does not change joins')
raw_report = (ROOT / 'data/status/key-check/two-name-us.json').read_text(encoding='utf-8')
check('<<<<<<' not in raw_report, 'the generated two-name report is main\'s file, not a hand edit')

cat = RS.catalog()
pei = [r for r in cat if 'GeoLinc_Wildlife_Management_Area' in (r.get('url') or '')]
check(len(pei) == 1 and pei[0]['use'] == 'report' and pei[0]['republish'] is False and pei[0]['builder'] == 'ca',
      'PEI WMA is a Canada research source, report only')
check(all('gisportaldev.dot.ny.gov' not in (r.get('url') or '') for r in cat), 'NY OPRHP dev portal is not in the catalog')
check(all(r.get('use') == 'matching_only' and r.get('republish') is False for r in cat if 'MAREA' in (r.get('title') or '') or r.get('area') == 'AU-WA'),
      'NCNHP and AU-WA stay matching-only and are not republished')
check(SF.find(pei[0]['url']) is None and SF.research_find(pei[0]['url'])['key'] == 'pe_wma',
      'the PEI field row is research-only and is not a builder source')
dni = (ROOT / 'data/research-sources/do_not_ingest.csv').read_text(encoding='utf-8')
check('gisportaldev.dot.ny.gov' in dni, 'NY OPRHP stays on do_not_ingest')
box = json.loads((ROOT / 'data/maprep/catalog.json').read_text(encoding='utf-8'))
live = next(s for s in box['sources'] if s.get('id') == 'ca-pe-geolinc-wildlife-management-area')
check(live.get('live') is True and live.get('place') == 'PE' and 'services' not in live.get('rest', '').split('/')[2],
      'PEI GeoLinc is a Tool Box live layer and is not services*.arcgis.com')
check(all('33TOOklri9xpic7U' not in ((s.get('rest') or '') + (s.get('download') or '')) for s in box['sources']),
      'the Tool Box catalog still omits Grant County NM')

fix = json.loads((ROOT / 'tests/fixtures/round3_joint_nested.json').read_text(encoding='utf-8'))
check(len(fix['joint']) == 6 and len(fix['nested']) == 9, 'sourced joint and nested examples are the fixture')
check(all('services.arcgis.com' not in (r.get('source_url') or '') for r in fix['joint'] + fix['nested']),
      'no services*.arcgis.com URL is in the fixtures')
check(all(r['spot_status'] == 'confirmed' for r in fix['joint'] + fix['nested']), 'every fixture row was spot-confirmed')
mp = {'how': 'explicit', 'key': 'round3_fixture', 'id': 'SID', 'parent': 'PARENT', 'owner': 'OWN', 'acres': 'AC', 'unit': 1.0}
sample = {'schema': 1, 'parks': {'US-1': {'n': 'Big Rivers'}}}
raw = json.dumps(sample, sort_keys=True)
for ex in fix['joint']:
    tract = TR.tract('1', ex['park_or_area'], 'round3 fixture', {'OWN': ex['owners'], 'SID': ex['jurisdiction']}, mp)
    check(tract.get('own') == ex['owners'] and tract['src'] == 'round3_fixture',
          'joint owners are stored on the tract (' + ex['park_or_area'][:40] + ')')
check(json.dumps(sample, sort_keys=True) == raw, 'building a tract did not change the key row')


def sq(x0, y0, x1, y1):
    return [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]


nest = TR.nested_geometry({'US-mill': sq(-84.6, 37.4, -84.4, 37.6), 'US-dbnf': sq(-85, 37, -84, 38)})
check(nest == [{'child': 'US-mill', 'parent': 'US-dbnf', 'share': 1.0, 'how': 'geometry'}],
      f'Mill Creek inside Daniel Boone links as a nested park ({nest})')
apart = TR.nested_geometry({'pp': sq(-66, 43.5, -65.9, 43.6), 'nr': sq(-65.2, 43.8, -65.1, 43.9)})
check(apart == [], 'Port L\'Hebert park and nature reserve are not nested')
cc = TR.tract('cc', 'Campbells Crossroads', 'round3 fixture', {'SID': 'CC', 'PARENT': 'PROP1', 'OWN': 'SCDNR'}, mp)
ang = TR.tract('ang', 'Angelus', 'round3 fixture', {'SID': 'ANG', 'PARENT': 'PROP1', 'OWN': 'SCDNR'}, mp)
same = TR.same_area({'US-3891a': [cc], 'US-3891b': [ang]})
check(len(same) == 1 and {same[0]['park'], same[0]['other']} == {'US-3891a', 'US-3891b'},
      'Campbells and Angelus share a parent id and are separate tracts')
check(TR.nested_geometry({'US-big': sq(-88.2, 37.2, -88.0, 37.4)}) == [],
      'one joint tract is not a park inside itself')
left = (ROOT / 'docs/round3-left-out.md').read_text(encoding='utf-8')
check('Cane Creek' in left and 'from_memory' in left, 'left-out list names Cane Creek and the memory rows')
check('OPRHP' in left and 'ScienceBase PAD-US' in left and 'DBCA-011' in left,
      'left-out list keeps NY OPRHP out and names the human downloads')

os.environ.pop('KPC_RESEARCH_SOURCES', None)
import kpc_save as KS
with tempfile.TemporaryDirectory() as td:
    KS.STATUS = pathlib.Path(td) / 'status.json'
    path = pathlib.Path(td) / 'US-KY.json'
    doc = TR.doc('US-KY', {'US-1': [cc]}, [])
    TR.save(path, doc)
    saved = path.read_bytes()
    check(not path.with_name('US-KY.research.json').exists(), 'flag off: tract save writes no research sidecar')
    os.environ['KPC_RESEARCH_SOURCES'] = 'report'
    side = RS.note_saved(path, doc)
    check(path.read_bytes() == saved, 'report mode does not rewrite the tract file')
    check(side and side.is_file() and side.name.endswith('.research.json'), 'report mode writes a side file only')
os.environ.pop('KPC_RESEARCH_SOURCES', None)
check(json.dumps(sample, sort_keys=True) == raw, 'the key row bytes are still unchanged')
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
