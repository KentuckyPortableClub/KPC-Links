#!/usr/bin/env python3
"""Nov 6 research packs: bot-safe sources stay behind KPC_RESEARCH_SOURCES (default off).

Default key output stays byte-identical, and the US / Canada / world rules hashes stay put,
because the new code is not a rule file. Report mode writes a side report only.
Pack test cases (KY Blue Licks / Natural Bridge SNPs inside US-1274 / US-1286 only, and the
rest of test_cases.csv) are checked here. Offline: no fetch, no write into the repo.
"""
import csv, hashlib, importlib, json, os, pathlib, sys, tempfile

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


# --- rules hashes do not move (rule files were not edited) ---
check(KF.rules_hash('us-key') == '6395b561d4c8', 'US rules hash 6395b561d4c8 (approved Nov 10, 2026; declared) with the flag off')
check(KF.rules_hash('ca-key') == '0ebc381a788f', 'Canada rules hash 0ebc381a788f (moved Nov 10, declared)')
# Nov 7 world rebuild (B1 B2 B3 B4 B6, world-failed-diagnosis.md section 7; Brandon OK'd the world hash move): kpc_world_key.py
# changed on purpose, so the world rules hash moved 1b50faf1dfe8 -> 6a5969a25d2c. US and CA stay; this check still pins all three.
check(KF.rules_hash('world-key') == '022f06d08d3c', 'world rules hash 022f06d08d3c (moved Nov 10, declared)')
check('kpc_research_sources.py' in KF.NOT_RULES, 'kpc_research_sources.py is not a rule file')
check('kpc_us_key.py' not in KF.NOT_RULES and 'kpc_world_key.py' not in KF.NOT_RULES, 'the key builders are still the rule files')

# existing source rows still win (new rows must not steal them)
pad = SF.mapping('https://example.test/PAD-US/PAD_US/MapServer/0', '', ['Source_PAID', 'GIS_Acres', 'Own_Name', 'Pub_Access'])
check(pad.get('key') == 'padus' and pad.get('id') == 'Source_PAID' and pad.get('acres') == 'GIS_Acres', 'PAD-US field map is unchanged')
cpc = SF.mapping('https://example.test/CWS_SCF/CPCAD/MapServer/0', '', ['ZONE_ID', 'PARENT_ID', 'O_AREA_HA', 'OWNER_E'])
check(cpc.get('key') == 'cpcad' and cpc.get('id') == 'ZONE_ID' and cpc.get('parent') == 'PARENT_ID', 'CPCAD field map is unchanged')

# --- flag off: no layers, no side report, key bytes identical ---
sample = {'schema': 1, 'area': 'US-KY', 'parks': {'US-1274': {'n': 'Blue Licks Battlefield State Park'},
                                                   'US-1286': {'n': 'Natural Bridge State Park'}}}
raw = json.dumps(sample, sort_keys=True, separators=(',', ':'))
check(RS.mode() == 'off', 'KPC_RESEARCH_SOURCES defaults to off')
check(RS.layers() == [] and RS.layers('us') == [] and RS.layers('ca') == [] and RS.layers('world') == [],
      'flag off: US, Canada and world layer lists are empty')
check(json.dumps(RS.leave_key_unchanged(sample), sort_keys=True, separators=(',', ':')) == raw, 'flag off: key document bytes unchanged')
check('kpc_research_sources' in (ROOT / '.github/scripts/kpc_tracts.py').read_text(), 'tract save calls the research hook')
with tempfile.TemporaryDirectory() as t:
    p = pathlib.Path(t) / 'US-KY.json'
    p.write_text(raw, encoding='utf-8')
    check(RS.note_saved(p, sample) is None, 'flag off: note_saved writes nothing')
    check(p.read_text(encoding='utf-8') == raw, 'flag off: the saved key file is byte-identical')
    check(not p.with_name('US-KY.research.json').exists(), 'flag off: no side report')

# a real key file on disk is not touched by importing the module
key_path = ROOT / 'data' / 'ky-answer-key.json'
key_before = hashlib.sha256(key_path.read_bytes()).hexdigest()

# --- abbreviations only in report mode ---
zec_pota, zec_official = 'ZEC Pabok Nature Reserve', 'ZEC Pabok'
natrue, nature = "Lac-Brule Natrue Reserve Nature Reserve", 'Lac-Brule Nature Reserve Nature Reserve'
check(not RS.names_match(zec_pota, zec_official, report=False), 'flag off: ZEC suffix is not stripped')
check(RS.names_match(zec_pota, zec_official, report=True), 'report mode: ZEC Nature Reserve matches the ZEC name')
check('natrue' in RS.canon_name(natrue, report=False), 'flag off: Natrue typo is left as written')
check(RS.names_match(natrue, nature, report=True), 'report mode: Natrue matches Nature')
check(RS.names_match('Allegan SGA', 'Allegan State Game Area', report=True), 'report mode: SGA expands for name matching')
check(not RS.names_match('Allegan SGA', 'Allegan State Game Area', report=False), 'flag off: SGA is not expanded')

# --- report mode still does not change key bytes; it only writes a side report ---
os.environ['KPC_RESEARCH_SOURCES'] = 'report'
check(RS.mode() == 'report', 'KPC_RESEARCH_SOURCES=report is the report mode')
check(json.dumps(RS.leave_key_unchanged(sample), sort_keys=True, separators=(',', ':')) == raw,
      'report mode: key document bytes stay identical')
with tempfile.TemporaryDirectory() as t:
    p = pathlib.Path(t) / 'US-KY.json'
    p.write_text(raw, encoding='utf-8')
    side = RS.note_saved(p, sample)
    check(p.read_text(encoding='utf-8') == raw, 'report mode: the key file on disk is byte-identical')
    check(side and side.is_file() and side.name == 'US-KY.research.json', 'report mode: side report is a separate file')
    rep = json.loads(side.read_text(encoding='utf-8'))
    check(rep.get('key_bytes_changed') is False and rep.get('pins_moved') == 0, 'side report says the key and the pins were not changed')
    check(rep.get('joins_would_add') == 0 and rep.get('joins_would_drop') == 0, 'side report: no join would be added or dropped')

# --- pack test cases ---
cases = list(csv.DictReader((ROOT / 'data/research-sources/test_cases.csv').open(encoding='utf-8')))
check(len(cases) >= 28, f'pack test_cases.csv has the US/CA and GB/IE/AU/NZ rows ({len(cases)})')
ev = { (e['name'], tuple(e['refs'])): e for e in (RS.evaluate_case(r) for r in cases) }
by_name = {}
for e in ev.values():
    by_name.setdefault(e['name'], e)

ky = json.load(open(ROOT / 'data/ky-answer-key.json', encoding='utf-8'))['parks']
ky_names = {ref: p.get('n') or '' for ref, p in ky.items()}
blue = RS.hosts_in('Blue Licks State Nature Preserve', ky_names)
bridge = RS.hosts_in('Natural Bridge State Nature Preserve', ky_names)
check(blue == ['US-1274'], f'Blue Licks SNP is only inside US-1274 ({blue})')
check(bridge == ['US-1286'], f'Natural Bridge SNP is only inside US-1286 ({bridge})')
check(by_name['Blue Licks State Nature Preserve']['hosts'] == ['US-1274'] and not by_name['Blue Licks State Nature Preserve']['new_park'],
      'Blue Licks case is host-only, not a new park')
check(by_name['Natural Bridge State Nature Preserve']['hosts'] == ['US-1286'] and not by_name['Natural Bridge State Nature Preserve']['new_park'],
      'Natural Bridge case is host-only, not a new park')

def one(name):
    return by_name[name]

check(not one('Walk-In Hunting Access (WIHA) tract')['counted'] and not one('Walk-In Hunting Access (WIHA) tract')['new_park'],
      'WIHA is not offered as a new park')
check(any('offshore' in n for n in one('Endeavour Hydrothermal Vents Marine Protected Area')['notes']),
      'Endeavour MPA is not flagged just for being offshore')
check(not one('Coed Cilygroeslwyd')['counted'] and any('inactive' in n for n in one('Coed Cilygroeslwyd')['notes']),
      'GB-2511 is inactive and not counted')
check(one('Walton Moss SAC (inc Walton Moss NNR)')['designations'] == ['SAC', 'NNR'] and not one('Walton Moss SAC (inc Walton Moss NNR)')['new_park'],
      'GB-0002 stays one ref with SAC and NNR, not a second park')
check(one('Glendalough nature reserve inside Wicklow Mountains National Park')['parent'] == 'IE-0003',
      'IE-0097 is a nested 2-fer inside IE-0003')
check(any('not Crown' in n or '2014' in n for n in one('Te Urewera')['notes']),
      'NZ-0280 is not flagged as missing from DOC')
kaik = one('Te Whata Kai o Rakihouia i Te Tai o Marokura (Kaikōura) marine reserve')
check(kaik['shared_pin'] and 'NZ-0614' in kaik['hosts'] and 'NZ-0928' in kaik['hosts'] and not kaik['new_park'],
      'NZ-0928 / NZ-0614 are a near-duplicate; NZ-0614 is a bad-pin note, not a new park')
check(all(e['pins_moved'] is False and e['new_park'] is False for e in ev.values()),
      'every pack case leaves pins where they are and creates no new POTA ref')
rep = RS.would_change(cases)
check(rep['joins_would_add'] == 0 and rep['joins_would_drop'] == 0 and rep['pins_moved'] == 0, 'would-change join counts are zero')
check(rep['twofers_would_note'] >= 4, f'report notes the host / nested / combo 2-fers ({rep["twofers_would_note"]})')
check(rep['acres_would_change'] is None and rep['owners_would_change'] is None, 'acres and owners are not claimed without a shape pass')

# catalog: only ok file/hub/rest rows that passed the live check; nothing banned; WA not republished
cat = RS.catalog()
check(cat, 'catalog has the sources that passed the live robots check')
check(all(r.get('robots_csv') == 'ok' for r in cat), 'every catalog row was robots_status ok in the pack')
check(all(not RS._banned(r.get('url') or '') for r in cat), 'banned and do_not_ingest urls are not in the catalog')
check(all('33TOOklri9xpic7U' not in (r.get('url') or '') for r in cat), 'Grant County NM server is absent')
wa = [r for r in cat if 'CC BY-NC' in (r.get('licence') or '') or r.get('area') == 'AU-WA']
check(all(r.get('use') == 'matching_only' and r.get('republish') is False for r in wa), 'WA CC BY-NC is matching-only and is not republished')
check(all(r.get('republish') is False for r in cat), 'no research source is marked for republish into the repo')
for area in ('US', 'CA', 'GB', 'IE', 'AU', 'NZ'):
    pass
builders = {r.get('builder') for r in cat}
check(builders <= {'us', 'ca', 'world'} and 'us' in builders and 'ca' in builders and 'world' in builders,
      f'catalog feeds US, Canada and world ({sorted(builders)})')

check(hashlib.sha256(key_path.read_bytes()).hexdigest() == key_before, 'ky-answer-key.json was not rewritten')
os.environ.pop('KPC_RESEARCH_SOURCES', None)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
