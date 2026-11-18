#!/usr/bin/env python3
"""KPC_AGENCY_TIE (matching plan section 2, HQ 2026-11-17): in the contest, a record that would go to a person goes to the one park
whose POTA website's agency keeps its land in that record's manager (learned table)."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_key_rules as KR
T = {'fws.gov': {'_parks': 72, 'FWS': 28, 'SGVAE': 10}, 'agfc.com': {'_parks': 13, 'SFW': 8, 'SGARA': 3},
     'cpw.state.co.us': {'_parks': 49, 'SGCOB': 37, 'FWS': 1}, 'nps.gov': {'_parks': 70, 'NPS': 36}}
bad = 0
def ck(c, m):
    global bad; bad += not c; print(('PASS ' if c else 'FAIL ') + m)
ck(KR.web_host('https://www.fws.gov/refuge/big-lake') == 'fws.gov' and KR.web_host('') == '', 'web_host drops www. and the path')
ck(KR.agency_pick('FWS', {'A': 'fws.gov', 'B': 'agfc.com'}, T) == 'A', "Big Lake: an FWS record goes to the fws.gov park, not the Game and Fish one")
ck(KR.agency_pick('SFW', {'A': 'fws.gov', 'B': 'agfc.com'}, T) == 'B', 'a state wildlife record goes to the agfc.com park')
ck(KR.agency_pick('FWS', {'A': 'fws.gov', 'B': 'cpw.state.co.us'}, T) is None, "Browns Park: the other host also has FWS (1 park): no win, a person")
ck(KR.agency_pick('FWS', {'A': 'fws.gov', 'B': 'unknown.org'}, T) is None, 'an unknown website = no evidence = a person')
ck(KR.agency_pick('FWS', {'A': 'fws.gov', 'B': 'fws.gov'}, T) is None, 'two parks of one agency: the website cannot decide')
ck(KR.agency_pick('', {'A': 'fws.gov', 'B': 'agfc.com'}, T) is None, 'a record with no manager decides nothing')
ck(KR.agency_pick('SGVAE', {'A': 'fws.gov', 'B': 'nps.gov'}, T) == 'A', 'a learned state-copy manager counts like any other (SGVAE: 10 fws.gov parks, 0 nps.gov)')
ag = lambda refs: KR.agency_pick('FWS', {r: {'US-1': 'fws.gov', 'US-2': 'agfc.com'}[r] for r in refs}, T)
ck(KR.contest('Big Lake', {'US-1': ('Big Lake National Wildlife Refuge', 'NWR'), 'US-2': ('Big Lake Wildlife Management Area', 'WMA')}, None, (), ag) == ('win', 'US-1'),
   'contest: a bare-name record goes to the park of its manager\'s agency')
ck(KR.contest('Big Lake', {'US-1': ('Big Lake National Wildlife Refuge', 'NWR'), 'US-2': ('Big Lake Wildlife Management Area', 'WMA')})[0] == 'person',
   'contest without the agency leg: a person, as before')
ck(KR.contest('Big Lake NWR', {'US-1': ('Big Lake National Wildlife Refuge', 'NWR'), 'US-2': ('Big Lake Wildlife Management Area', 'WMA')}, None, (), lambda r: 'US-2') == ('win', 'US-1'),
   "the record's own type word still comes first; the agency leg only breaks a tie")
t = json.load(open(ROOT / '.github' / 'key-agency-table.json'))
ck(t.get('learned') and isinstance(t.get('hosts'), dict) and all(v.get('_parks', 0) >= 2 for v in t['hosts'].values()), 'the table file is learned (date) and every host counts 2+ parks')
ck(KR.DEFAULTS.get('KPC_AGENCY_TIE') == '0' and 'KPC_AGENCY_TIE' in json.load(open(ROOT / '.github' / 'key-switches.json'))['switches'], 'KPC_AGENCY_TIE is OFF and listed')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
