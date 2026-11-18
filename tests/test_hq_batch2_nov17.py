#!/usr/bin/env python3
"""HQ batch 2 (2026-11-17): world near names (KPC_WORLD_NEAR_NAME), D7 state copies (KPC_STATE_COPY), all OFF."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_key_rules as KR
bad = 0
def ck(c, m):
    global bad; bad += not c; print(('PASS ' if c else 'FAIL ') + m)
for a, b, want in (('yaw al debsa', 'yaw al dibsa', True), ('bialowieza', 'bialowieski', True), ('ndumo', 'ndumu', False),
                   ('oa', 'the oa', False), ('park 1', 'park 2', False), ('lake', 'lake', False), ('aukstaitijos', 'aukstaitija', True),
                   ('mull oa american monument', 'oa', False), ('wolin', 'wolin', False)):
    ck(KR.near_name(a, b) is want, f'near_name({a!r}, {b!r}) is {want}')
sw = json.load(open(ROOT / '.github' / 'key-switches.json'))['switches']
for k in ('KPC_WORLD_NEAR_NAME', 'KPC_STATE_COPY', 'KPC_AGENCY_TIE'):
    ck(KR.DEFAULTS.get(k) == '0' and k in sw and not sw[k]['on'], f'{k} is OFF by default and listed with no area on')
us = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8'); wk = (ROOT / '.github/scripts/kpc_world_key.py').read_text(encoding='utf-8')
ck("_kr('KPC_STATE_COPY')" in us and "'compilation'" in us and "not str(x[3]).startswith('reviewed')" in us, "D7 reads the layer label and never moves a person's join")
ck("_kr('KPC_WORLD_NEAR_NAME')" in wk and "pk['g'] = 'approx'" in wk and 'check (near name)' in wk, 'a near-name join is approximate and asked of a person')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
