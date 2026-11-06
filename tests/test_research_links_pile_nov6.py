#!/usr/bin/env python3
"""Nov 6, same research flag: official-link post-check and pile-solver outline ranking.

Both are report-only. KPC_RESEARCH_SOURCES defaults to off, and off writes nothing and
does not change a key. The pile solver itself is in KPC-Data; this repo carries the patch
and the ranker. Pile-solver auto stays false. Offline. Does not write the repo.
"""
import json, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
os.environ.pop('KPC_RESEARCH_SOURCES', None)

import kpc_research_sources as RS

ok = True


def check(cond, msg):
    global ok
    if not cond:
        ok = False
        print('FAIL', msg)
    else:
        print('PASS', msg)


ag = RS.load_agencies()
check(ag.get('places', {}).get('KY', {}).get('name') == 'Kentucky', 'vendored agencies.json from the toolbox PR has Kentucky')
check('33TOOklri9xpic7U' not in json.dumps(ag), 'Grant County NM server is not in the agency file')

sample = {'ref': 'US-1274', 'n': 'Blue Licks Battlefield State Park'}
raw = json.dumps(sample, sort_keys=True)
check(RS.mode() == 'off', 'flag defaults to off')
check(RS.link_postcheck([{'ref': 'US-1274', 'area': 'US-KY', 'name': 'Blue Licks', 'kind': 'State Park', 'web': ''}]) == [],
      'flag off: the link post-check returns nothing')
check(RS.rank_outlines('Allegan SGA', [{'id': '1', 'name': 'Allegan State Game Area'}]) == [],
      'flag off: outline ranking returns nothing')
check(json.dumps(sample, sort_keys=True) == raw, 'flag off: the key row bytes are unchanged')

os.environ['KPC_RESEARCH_SOURCES'] = 'report'
ky_park = RS.suggest_agency('US-KY', 'State Park', 'Blue Licks Battlefield State Park', ag)
ky_wma = RS.suggest_agency('US-KY', 'Wildlife Management Area', 'Muddygut WMA', ag)
ky_snp = RS.suggest_agency('US-KY', 'State Nature Preserve', 'Blue Licks State Nature Preserve', ag)
check('parks.ky.gov' in (ky_park.get('url') or ''), f'a KY state park suggests Kentucky State Parks ({ky_park.get("url")})')
check('fw.ky.gov' in (ky_wma.get('url') or ''), f'a KY WMA suggests Fish and Wildlife ({ky_wma.get("url")})')
check('Nature-Preserves' in (ky_snp.get('url') or ''),
      f'a KY nature preserve suggests the preserves office ({ky_snp.get("url")})')

rows = [
    {'ref': 'US-1274', 'area': 'US-KY', 'name': 'Blue Licks Battlefield State Park', 'kind': 'State Park', 'web': '', 'map_check': {}},
    {'ref': 'US-0727', 'area': 'US-WA', 'name': 'Lake Lenore Caves', 'kind': 'State Park', 'web': 'https://parks.wa.gov/missing',
     'map_check': {'map': 'HTTP 404'}},
    {'ref': 'US-0001', 'area': 'US-KY', 'name': 'A park with a page', 'kind': 'State Park', 'web': 'https://parks.ky.gov/example',
     'map_check': {'map': 'ok'}},
    {'ref': 'US-0002', 'area': 'US-KY', 'name': 'Rate limited only', 'kind': 'State Park', 'web': 'https://parks.ky.gov/slow',
     'map_check': {'map': 'HTTP 429'}},
]
flagged = RS.link_postcheck(rows, ag)
by = {r['ref']: r for r in flagged}
check(set(by) == {'US-1274', 'US-0727'}, f'only the missing page and the 404 are flagged ({sorted(by)})')
check(by['US-1274']['problem'] == 'missing' and 'parks.ky.gov' in by['US-1274']['suggest_url'],
      'US-1274 is missing an official page and the suggestion is the state parks finder')
check(by['US-0727']['problem'] == 'broken' and 'HTTP 404' in by['US-0727']['detail'],
      'US-0727 is a broken official link (stored HTTP 404), not a new fetch')
check(all(r.get('suggestion') == 'suggestion, never auto-replace' for r in flagged),
      'every suggestion is labelled suggestion, never auto-replace')
acadia = {'ref': 'US-0047', 'area': 'US-ME', 'name': 'Acadia National Park', 'kind': 'National Park',
          'owner': 'National Park Service', 'web': '', 'map_check': {}}
before = json.dumps(acadia, sort_keys=True)
got = RS.link_postcheck([acadia], ag)[0]
check(got['suggest_agency'] == 'National Park Service' and 'nps.gov' in got['suggest_url'],
      f'Acadia suggests the National Park Service, not a Maine page ({got.get("suggest_agency")} {got.get("suggest_url")})')
check('Maine' not in got['suggest_agency'], 'Acadia is not sent to the Maine state agency')
check(json.dumps(acadia, sort_keys=True) == before and acadia['web'] == '',
      'the suggestion is not written back onto the park link')
check(json.dumps(sample, sort_keys=True) == raw, 'report mode: the key row bytes stay identical')

ranked = RS.rank_outlines('Allegan SGA', [
    {'id': 'creek', 'name': 'Allegan Creek'},
    {'id': 'sga', 'name': 'Allegan State Game Area'},
    {'id': 'other', 'name': 'Something Else Entirely'},
])
check(ranked and ranked[0]['id'] == 'sga' and ranked[0]['score'] >= 84, f'SGA ranks the state game area first ({ranked[:2]})')
zec = RS.rank_outlines('ZEC Pabok Nature Reserve', [
    {'id': 'other', 'name': 'ZEC des Anses'},
    {'id': 'pabok', 'name': 'ZEC Pabok'},
])
check(zec and zec[0]['id'] == 'pabok' and zec[0]['score'] >= 84, f'ZEC suffix still ranks the real ZEC name first ({zec[:1]})')
check(all('verdict' not in r for r in ranked), 'a rank is not a join verdict')

where = RS.pile_solver_where()
check(where['repo'].endswith('KPC-Data') and where['auto'] is False, 'pile solver is in KPC-Data and auto stays false')
patch = (ROOT / where['patch']).read_text(encoding='utf-8')
check('KPC_RESEARCH_SOURCES' in patch and 'rank_outlines' in patch, 'the patch ranks outlines only in report mode')
check("state['auto'] = True" not in patch and 'state["auto"] = True' not in patch, 'the patch does not turn pile-solver auto on')
check("'auto': False" in patch, 'the side rank file records auto false')
note = (ROOT / 'docs' / 'PILE-SOLVER-RESEARCH.txt').read_text(encoding='utf-8')
check('KPC-Data' in note and 'auto' in note.lower(), 'the docs say the solver is in the other repo and auto stays off')

os.environ.pop('KPC_RESEARCH_SOURCES', None)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
