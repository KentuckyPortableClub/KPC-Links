#!/usr/bin/env python3
"""Hand-off 06 part 2: a change to the measuring math cannot hide behind scope none.

The fingerprint is the source of the functions that move or size a spot, from find_spots() down, plus the size
constants that are not already inside pair_fp. It is saved in tests/fixtures/fers-math-guard.json with the id of
the scope entry that covers it. A different fingerprint fails until that fixture is updated in the same pull
request and the scope entry it names is not none.
"""
import hashlib, inspect, json, os, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
os.environ.setdefault('PASS', '3')
import kpc_fers as K

FUNCS = ('find_spots', 'area_spots', 'water_route_spots', 'line_spots', 'pmask', 'Frame', 'inter', 'tiles', 'dt',
         'bbox_groups', 'bbox_lines')
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
    """True only when the fixture matches and its scope entry exists and is not none."""
    if fp != fixture.get('fingerprint'):
        return False
    entry = next((c for c in changes if c.get('id') == fixture.get('scope_id')), None)
    return bool(entry) and entry.get('scope') != 'none'


fp = fingerprint()
fix = json.loads(FIX.read_text(encoding='utf-8'))
changes = json.loads((HERE / '.github/fers-rule-scope.json').read_text(encoding='utf-8'))['changes']
check(fp == fix['fingerprint'],
      'the measuring math matches the fixture (a change fails until this file is updated in the same pull request)')
check(covered(fp, fix, changes),
      f"the scope entry {fix.get('scope_id')} exists and is not none")
check(not covered(fp + 'x', fix, changes), 'KA-25 a different fingerprint fails')
none_fix = dict(fix, scope_id='2026-11-17-thin-shelf')
check(not covered(fp, none_fix, changes), 'KA-25 a scope entry of none does not cover a math change')
check('FERS_ALGO' not in (HERE / '.github/scripts/kpc_fers.py').read_text(encoding='utf-8')
      and 'REUSE_KEY' not in (HERE / '.github/scripts/kpc_fers.py').read_text(encoding='utf-8')
      and 'KPC_FERS_REUSE_KEY' not in (HERE / '.github/scripts/kpc_fers.py').read_text(encoding='utf-8'),
      'the dead math-version lines are gone')
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
