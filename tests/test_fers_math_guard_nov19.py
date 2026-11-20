#!/usr/bin/env python3
"""Hand-off 06 part 2: a change to the measuring math cannot hide behind scope none.

The fingerprint is the source of the functions that move or size a spot, or that can keep yesterday's spots,
from find_spots() down, plus the size constants that are not already inside pair_fp. It is saved in
tests/fixtures/fers-math-guard.json. The scope entry that id names carries the same fingerprint. A different
fingerprint fails until a new scope entry is written for it and the fixture points at that entry.
"""
import hashlib, inspect, json, os, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
os.environ.setdefault('PASS', '3')
import kpc_fers as K

FUNCS = ('find_spots', 'area_spots', 'water_route_spots', 'line_spots', 'pmask', 'Frame', 'inter', 'tiles', 'dt',
         'bbox_groups', 'bbox_lines',
         'merge', 'Win', 'sample', 'line_m', 'close_m', 'water_route', 'nhd_water',
         'pair_fp', 'rule_stamp', 'answers_unchanged')
# The first-round baseline hashed the first 11 names only. That fingerprint stays on that scope entry.
BASE_ID = '2026-11-19-math-guard-baseline'
BASE_FP = '0162b452da97751fcfad7650ae9c4dcf3ea1f30f7676cfc50ba458ff41f738a1'
CONSTS = ('SHRINK', 'SMALL_M', 'TIGHT_M', 'TIGHT_SHRINK', 'STRETCH', 'ZONE', 'STATION_IN', 'ROUTE_KM', 'BANK')
FIX = HERE / 'tests/fixtures/fers-math-guard.json'
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg, flush=True)
    ok = ok and bool(c)


def fingerprint(mod=K):
    parts = []
    for name in FUNCS:
        obj = getattr(mod, name)
        parts.append(name + '\n' + inspect.getsource(obj))
    for name in CONSTS:
        parts.append(f'{name}={getattr(mod, name)!r}')
    return hashlib.sha256(''.join(parts).encode()).hexdigest()


def covered(fp, fixture, changes):
    """True only when the fixture, the code and the scope entry name the same fingerprint, and that entry is not none.
    The baseline entry's fingerprint is the first-round one. A new fingerprint has to name a different entry."""
    if fp != fixture.get('fingerprint'):
        return False
    entry = next((c for c in changes if c.get('id') == fixture.get('scope_id')), None)
    if not entry or entry.get('scope') == 'none':
        return False
    if entry.get('fingerprint') != fp:
        return False
    base = next((c for c in changes if c.get('id') == BASE_ID), None)
    if not base or base.get('fingerprint') != BASE_FP:
        return False
    if fp != BASE_FP and fixture.get('scope_id') == BASE_ID:
        return False
    return True


fp = fingerprint()
fix = json.loads(FIX.read_text(encoding='utf-8'))
changes = json.loads((HERE / '.github/fers-rule-scope.json').read_text(encoding='utf-8'))['changes']
check(fp == fix['fingerprint'],
      'the measuring math matches the fixture (a change fails until this file is updated in the same pull request)')
check(covered(fp, fix, changes),
      f"the scope entry {fix.get('scope_id')} carries this fingerprint and is not none")
stale = []
for c in changes:
    row = dict(c)
    if row.get('id') == fix.get('scope_id'):
        row['fingerprint'] = BASE_FP
    stale.append(row)
check(not covered(fp, fix, stale), 'refreshing the fixture fingerprint alone does not pass (the scope entry still has the old one)')
check(not covered(fp + 'x', fix, changes), 'KA-25 a different fingerprint fails')
none_fix = dict(fix, scope_id='2026-11-17-thin-shelf')
check(not covered(fp, none_fix, changes), 'KA-25 a scope entry of none does not cover a math change')
check('FERS_ALGO' not in (HERE / '.github/scripts/kpc_fers.py').read_text(encoding='utf-8')
      and 'REUSE_KEY' not in (HERE / '.github/scripts/kpc_fers.py').read_text(encoding='utf-8')
      and 'KPC_FERS_REUSE_KEY' not in (HERE / '.github/scripts/kpc_fers.py').read_text(encoding='utf-8'),
      'the dead math-version lines are gone')
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
