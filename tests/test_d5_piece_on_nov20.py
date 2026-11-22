#!/usr/bin/env python3
"""D5 (leased / agreement land never by name, KPC_NO_LEASE_BY_NAME) and the piece rule (rule 18, KPC_PIECE_NAME) are ON in the
switch file for all 50 US key areas (49 states and DC; Kentucky has its own key), the same list as the other US rules that are on. Their two scope entries name states and
counts only, never a park. Fails on a tree where either switch is still off for any state.
Run:  python3 tests/test_d5_piece_on_nov20.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

sw = json.load(open(ROOT / '.github/key-switches.json', encoding='utf-8'))['switches']
ALL = sorted(sw['KPC_SAVED_ID_LAND']['on'])
check(len(ALL) == 50 and 'DC' in ALL and 'KY' not in ALL, f'the reference list is the 50 US key areas: 49 states and DC, Kentucky has its own key ({len(ALL)})')
for name in ('KPC_NO_LEASE_BY_NAME', 'KPC_PIECE_NAME'):
    check(sorted(sw[name]['on']) == ALL, f'{name} is on in the switch file for every state on the reference list')
    off = [a for a in ALL if not KR.on(name, env={}, area=a)]
    check(not off, f'{name}: with an empty environment the builder reads it ON in every state (off in {off[:5]})')
    check(not KR.on(name, env={name: '0'}, area='NC'), f'{name}: a 0 in the environment still turns it off for one run')
sc = {c['id']: c for c in json.load(open(ROOT / '.github/us-key-rule-scope.json', encoding='utf-8'))['changes']}
for cid in ('2026-11-20-d5-lease-by-name-on', '2026-11-20-piece-name-on'):
    c = sc.get(cid) or {}
    s = c.get('scope') if isinstance(c.get('scope'), dict) else {}
    check(bool(s.get('states')) and 'parks' not in s, f'{cid}: scope names states only, no park')
    check('APPROVED, decided_by KPC owner' in str(c.get('approved') or ''), f'{cid}: approved by the owner')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
