#!/usr/bin/env python3
"""Reviewer B #7 (KPC owner, 2026-11-17): the key rule switches live in .github/key-switches.json, are read per state, move only
the hash of the states they are on for, and a broken rules / switch file stops the build instead of turning every rule off.
Run: python3 tests/test_key_switch_file_nov17.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import json, pathlib, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
import kpc_area_hash as AH  # noqa: E402
import kpc_key_freeze as KF  # noqa: E402
R = []
def check(ok, what): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + what)

real = json.load(open(ROOT / '.github/key-switches.json'))
# Owner 17 Nov 7:10 PM: the eleven new rules are ON for the eight tested states only (scope entry 2026-11-17-switch-on-8)
EIGHT = ['AR', 'DE', 'GA', 'MD', 'MI', 'OH', 'RI', 'TN']
import kpc_area_hash as _AH
USALL = sorted(x for x in _AH.US_ALL if x != 'KY')
TEST_ORDER = {'KPC_SAME_LAND': ['MN', 'NY'], 'KPC_PROVEN_ONLY': ['MN', 'NY'], 'KPC_STORE_FRESH': ['MN', 'NY'], 'KPC_SAVED_HINTS_ONLY': ['MN', 'NY']}   # 25 Nov 2026 (KPC owner): MN first, then NY
check(all(v['on'] in ([], EIGHT, USALL) or v['on'] == TEST_ORDER.get(k) for k, v in real['switches'].items()), "the committed file has each switch off, or on for the owner's states (17 Nov: every US state the US key builds; 25 Nov: the better matcher on MN and NY only)")
check(set(real['switches']) == {k for k, v in KR.DEFAULTS.items() if v == '0'}, 'every OFF-by-default switch is in the file (and only those)')
check(KR.on('KPC_NO_ALL_PATHS', env={}, area='OH'), 'the default-ON switch (a NO on every path) stays on')

d = pathlib.Path(tempfile.mkdtemp()); f = d / 'sw.json'
f.write_text(json.dumps({'switches': {'KPC_ONE_RECORD_ONE_PARK': {'on': ['US-NH']}, 'KPC_SAVED_ID_LAND': {'on': ['*']}, 'KPC_NO_LEASE_BY_NAME': {'on': []}}}))
P = str(f)
check(KR.on('KPC_ONE_RECORD_ONE_PARK', env={}, area='NH', path=P) and KR.on('KPC_ONE_RECORD_ONE_PARK', env={}, area='US-NH', path=P), 'on for the state it lists (NH or US-NH)')
check(not KR.on('KPC_ONE_RECORD_ONE_PARK', env={}, area='OH', path=P), '... and off for every other state')
check(KR.on('KPC_SAVED_ID_LAND', env={}, area='OH', path=P), "'*' = on everywhere")
check(not KR.on('KPC_NO_LEASE_BY_NAME', env={}, area='OH', path=P), 'an empty list = off')
check(not KR.on('KPC_ONE_RECORD_ONE_PARK', env={'KPC_ONE_RECORD_ONE_PARK': '0'}, area='NH', path=P) and KR.on('KPC_NO_LEASE_BY_NAME', env={'KPC_NO_LEASE_BY_NAME': '1'}, area='OH', path=P),
      'an environment variable of the same name still wins (offline proofs, the scorecard)')
check(KR.areas_on('NH', path=P) == ['KPC_ONE_RECORD_ONE_PARK', 'KPC_SAVED_ID_LAND'], 'areas_on lists the switches on for a state')
b = d / 'bad.json'; b.write_text('{"switches": {"KPC_SAVED_ID_LAND": {"on": "US-OH"}}}')
try: KR.switch_file(str(b)); ok = False
except KR.SwitchFileError: ok = True
check(ok, "a malformed switch file raises (the build stops; nothing runs with every switch silently off)")
b2 = d / 'bad2.json'; b2.write_text('{not json')
try: KR.switch_file(str(b2)); ok = False
except KR.SwitchFileError: ok = True
check(ok, 'an unreadable switch file raises')

sl = AH.switch_slice(json.load(open(f)), {'NH', 'OH'})
check(sl == {'NH': ['KPC_ONE_RECORD_ONE_PARK', 'KPC_SAVED_ID_LAND'], 'OH': ['KPC_SAVED_ID_LAND']}, f'the area hash slice: each state only its own switches ({sl})')
alloff = {'switches': {k: {'on': []} for k in real['switches']}}
check(AH.switch_slice(alloff, {'NH', 'OH'}) == {} and 'KY' not in AH.switch_slice(real, {'KY', 'OH'}), 'every switch off = no part for any state; a state with none on (KY: its own key) gets no part')
check('.github/key-switches.json' in AH.SLICED_RULE_FILES and '.github/key-switches.json' in KF.RULE_FILES['us-key'],
      'the switch file is a US rule file and is sliced per state (not hashed whole as shared code)')
ah = (ROOT / '.github/scripts/kpc_area_hash.py').read_text(encoding='utf-8')
check("self.slice_file('.github/key-switches.json', parts, sh, lambda v: (switch_slice(v, self.areas_set), {})" in ah, 'the US area hash reads the switch slice')
uk = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
check('except Exception: KR = None' not in uk and 'KR.switch_file()' in uk, 'a rules file that cannot load stops the US key (no silent all-off)')
check("def _kr(name): return KR.on(name, area=CUR_ST['st'])" in uk and "CUR_ST['st'] = st" in uk, 'the US key reads each switch for the state it is building')
print('ALL PASS' if all(R) else f'{R.count(False)} FAILED'); sys.exit(0 if all(R) else 1)
