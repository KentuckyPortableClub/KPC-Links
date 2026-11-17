#!/usr/bin/env python3
"""Owner rulings 2026-11-17 11:14 AM on the 2-fer review. Q1: a pair whose every land half is only a designation / planning line
is shown in the approximate tier with the 'may contain private land' note. Q3: a row this run's rules drop is not put back
(never worse is for missing inputs only; KPC_FERS_KEEP_DROPPED=1 brings the old rule back).
Run: python3 tests/test_fers_q1_q3_nov17.py   (from the repo root)"""
import sys as _sys; _sys.dont_write_bytecode = True
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import os; os.chdir(ROOT)
import kpc_fers as KF  # noqa: E402
R = []
def check(ok, what): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + what)
KF.PADMANG.update({101: ('BLM', 'Designation'), 102: ('USFS', 'Fee'), 103: ('NPS', 'Proclamation'), '_': ('', '')})
parks = {'US-1': {'ids': ['wsa900', 'wsa901']}, 'US-2': {'ids': ['nca21338']}, 'US-3': {'ids': [102]}, 'US-4': {'ids': [101, 'fwsr5']},
         'US-5': {'ids': ['sgcab12']}, 'US-6': {'ids': []}, 'US-7': {'ids': [103]}, 'US-8': {'ids': ['wsa1', 102]}}
check(KF.designation_only('US-1', parks) and KF.designation_only('US-2', parks), 'study area / monument lines are designation-only')
check(not KF.designation_only('US-3', parks), 'PAD-US Fee land (the agency owns it) is not')
check(KF.designation_only('US-4', parks) and KF.designation_only('US-7', parks), 'PAD-US Designation / Proclamation records are')
check(not KF.designation_only('US-5', parks), 'a state park boundary layer is not')
check(not KF.designation_only('US-6', parks), 'a line park (trail / river, no records) keeps its own rules')
check(not KF.designation_only('US-8', parks), 'a park with owned land of its own is not, even with a designation piece too')
check(KF.PRIVATE_NOTE.startswith('May contain private land.') and 'public land before you set up' in KF.PRIVATE_NOTE and 'law' not in KF.PRIVATE_NOTE,
      'the note in plain words (owner 11:22 AM): may contain private land, check the official map, be on public land')
src = (ROOT / '.github/scripts/kpc_fers.py').read_text(encoding='utf-8')
blk = src[src.index("_land = [r for r in refs if not (r in LN and r not in G)]"):][:600]
check("all(designation_only(r, parks) for r in _land)" in blk and "s['approx'] = True" in blk and 'PRIVATE_NOTE' in blk,
      'decide(): every land half designation-only = approximate tier with the note (one owned half = public ground, as before)')
check(KF.KEEP_DROPPED_ROWS is False, 'Q3: dropped rows are not put back unless KPC_FERS_KEEP_DROPPED=1')
# Q4 (owner 11:22 AM: 'if it is a pota park we treat it as one ... and overlap boundaries matter'): leased / agreement land is
# that park's land; the pair is decided like any other, with an access note
KF.REGION = 'na'
_po = KF.park_owner
own = {'US-10': 'PRIVATE', 'US-11': 'STATE', 'US-12': 'PRIVATE', 'US-13': '?'}
KF.park_owner = lambda r, parks: own[r]
s1 = {'refs': ['US-10', 'US-11'], 'notes': ['x']}
v, why = KF.ownership_step(s1, {}, {})
check(v == 'ok' and KF.LEASE_NOTE in s1['notes'] and 'leased / agreement land' in why, f'Q4: leased land + a state park = public ground, with the access note ({v}: {why})')
s2 = {'refs': ['US-10', 'US-12']}
check(KF.ownership_step(s2, {}, {})[0] == 'ok', 'Q4: two leased parks: their overlap counts like any other')
s3 = {'refs': ['US-10', 'US-13']}
check(KF.ownership_step(s3, {}, {})[0] == 'not sure', 'Q4: an unknown owner is still not sure (nothing else changed)')
KF.park_owner = _po
check(KF.owner_word('LEASE') == 'leased / agreement land', 'the owner in plain words')
print('ALL PASS' if all(R) else f'{R.count(False)} FAILED'); sys.exit(0 if all(R) else 1)
