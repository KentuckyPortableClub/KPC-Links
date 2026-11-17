#!/usr/bin/env python3
"""Handoff 8 fix 1 (switch KPC_NPS_UNIT_CODE): Park Service unit codes before names. The records below are the real PAD-US
records (id, name, unit code in Loc_Nm, acres) from the saved copies of Mississippi and Colorado; the parks are as the name rules
leave them today (offline run, Nov 17). The test calls the very function run() calls.
Run:  python3 tests/test_h8_nps_codes_nov17.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import copy, os, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tests')); sys.path.insert(0, str(ROOT / '.github/scripts'))
os.chdir(ROOT)
import run_match_tests as RMT  # noqa: E402
US = RMT._load('kpc_us_key.py', '\nidx = {}\n')
KR = US.KR
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

sq = lambda x, y, s=0.05: {'rings': [[[x, y], [x + s, y], [x + s, y + s], [x, y + s], [x, y]]]}
def rec(oid, nm, code, ac, x, y):
    g = sq(x, y); return {'OBJECTID': oid, 'Unit_Nm': nm, 'Loc_Nm': code, 'Mang_Name': 'NPS', 'GIS_Acres': ac, '_g': g, '_bb': US.bbox(g), '_k': US.kinds(nm)}

# the website reader
check(KR.nps_code_from_site('https://www.nps.gov/guis/index.htm') == 'GUIS', 'nps.gov/guis/index.htm = unit GUIS')
check(KR.nps_code_from_site('https://www.nps.gov/grsa') == 'GRSA', 'nps.gov/grsa = unit GRSA')
check(all(KR.nps_code_from_site(u) is None for u in ('https://www.nps.gov/articles/000/white-clay-creek-wild-and-scenic-river.htm',
      'https://www.nps.gov/places/foca.htm', 'https://npgallery.nps.gov/AssetDetail/NRIS/78001020', 'https://nps.gov', 'https://www.nps.gov/nr/travel/x.html', '')),
      'articles / places / NR pages / the bare site name no unit')
check(KR.nps_record_code({'Mang_Name': 'NPS', 'Loc_Nm': 'GUIS'}) == 'GUIS' and KR.nps_record_code({'Mang_Name': 'FWS', 'Loc_Nm': 'ABCD'}) is None
      and KR.nps_record_code({'SA': {'UNIT_CODE': 'cure'}}) == 'CURE', 'the record code: PAD-US NPS Loc_Nm, or the NPS layer UNIT_CODE; never another agency')
check(not KR.on('KPC_NPS_UNIT_CODE', {}), 'the switch is OFF unless set')

# MUST: US-0661 Gulf Islands National Seashore (pin in Florida) joins the Mississippi half of its unit (today: check, 'far from the pin')
ms_recs = [rec(3331, 'Gulf Islands National Seashore', 'GUIS', 57793, -88.9, 30.2), rec(3400, 'Vicksburg National Military Park', 'VICK', 1800, -90.85, 32.35)]
ms_P = {'US-0661': ['Gulf Islands National Seashore', 'https://www.nps.gov/guis/index.htm', 'National Seashore', 0, 0, 30.3641, -87.1301],
        'US-0702': ['Vicksburg National Military Park', '', 'National Military Park', 0, 0, 32.34, -90.85]}
ms0 = {'US-0661': {'n': 'Gulf Islands National Seashore', 'm': [], 'c': [[3331, 'Gulf Islands National Seashore', 57793, 'same name far from the pin, no join at the pin (Nov 1: check, never an outline)']]},
       'US-0702': {'n': 'Vicksburg National Military Park', 'm': [[3400, 'Vicksburg National Military Park', 1800, 'name']], 'c': []}}
off = copy.deepcopy(ms0); US.nps_code_joins('MS', off, ms_recs, ms_P, {}, on=False)
check(off == ms0, 'switch OFF: nothing changes (Gulf Islands stays a pin in Mississippi)')
on = copy.deepcopy(ms0); US.nps_code_joins('MS', on, ms_recs, ms_P, {}, on=True)
check([str(x[0]) for x in on['US-0661']['m']] == ['3331'] and on['US-0661']['m'][0][3].startswith('NPS unit code GUIS') and not on['US-0661']['c'],
      'switch ON: US-0661 Gulf Islands NS joins record 3331 by its code GUIS, at any distance, and leaves the check list')
check(on['US-0702'] == ms0['US-0702'], 'a park with no nps.gov code (Vicksburg here) is not touched')
no = copy.deepcopy(ms0); US.nps_code_joins('MS', no, ms_recs, ms_P, {'US-0661': {'no': ['3331']}}, on=True)
check(not no['US-0661']['m'], "a person's NO on the record still wins over the code")

# MUST NOT cross: US-0033 Great Sand Dunes NP and US-8295 the Preserve share unit GRSA; today each takes BOTH records by name
co_recs = [rec(3446, 'Great Sand Dunes National Park', 'GRSA', 104902, -105.6, 37.75), rec(3303, 'Great Sand Dunes National Preserve', 'GRSA', 41702, -105.5, 37.8)]
co_P = {'US-0033': ['Great Sand Dunes National Park', 'https://www.nps.gov/grsa/index.htm', 'National Park', 0, 0, 37.7942, -105.581],
        'US-8295': ['Great Sand Dunes National Preserve', '', 'National Preserve', 0, 0, 37.7335, -105.512]}
both = lambda: [[3446, 'Great Sand Dunes National Park', 104902, 'name'], [3303, 'Great Sand Dunes National Preserve', 41702, 'name']]
co0 = {'US-0033': {'n': 'Great Sand Dunes National Park', 'm': both(), 'c': []}, 'US-8295': {'n': 'Great Sand Dunes National Preserve', 'm': both(), 'c': []}}
on = copy.deepcopy(co0); US.nps_code_joins('CO', on, co_recs, co_P, {}, on=True)
check([str(x[0]) for x in on['US-0033']['m']] == ['3446'] and [str(x[0]) for x in on['US-8295']['m']] == ['3303'],
      'shared unit GRSA: the name decides inside it - US-0033 keeps only the Park record, US-8295 only the Preserve record')
check(any('GRSA' in x[3] for x in on['US-0033']['c']) and any('GRSA' in x[3] for x in on['US-8295']['c']), 'the record each gave back goes to check with the reason')
rv = copy.deepcopy(co0); rv['US-0033']['m'][1][3] = 'reviewed'; US.nps_code_joins('CO', rv, co_recs, co_P, {}, on=True)
check(any(str(x[0]) == '3303' for x in rv['US-0033']['m']), "a person's join (reviewed) is never given back")
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
