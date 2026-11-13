#!/usr/bin/env python3
"""Offline (KPC owner, 2026-11-13): a code-only world move uses each country's OWN last rules hash to find the declared
scope, so a stale index top stamp (world 487a51327b86, a Nov 5 complete-build stamp) no longer forces a full 84/84 add.
A country with no row rules hash and no matching scope still fails closed (added)."""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_area_hash as H  # noqa: E402

ok = True

def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


H.only_shared_code_moved = lambda *a, **k: True
H.real_inputs_moved = lambda *a, **k: True
rows = {'FR': {'area_hash': 'old1', 'rules': 'a47e0479ad41', 'area_parts': {'code': 'a'}},
        'BE': {'area_hash': 'old2', 'area_parts': {'code': 'a'}}}
hashes, parts = {'FR': 'new1', 'BE': 'new2'}, {'FR': {'code': 'b'}, 'BE': {'code': 'b'}}
final, table, added, reused = H.decide('world', [], hashes, parts, rows, '158325de87ce', 'add', repo=ROOT, prev_rules='487a51327b86')
act = {r[0]: r[4] for r in table}
check('FR (row rules a47e0479ad41, declared scope none) is not planned despite stale index stamp 487a51327b86',
      'FR' not in added and act['FR'].startswith('not planned'))
check('BE (no row rules, stale stamp has no scope) still fails closed: added', 'BE' in added)
# regrade 3 LA: a row with no rules and no index stamp must not borrow another row's hash (it rebuilds)
final, table, added, reused = H.decide('world', [], hashes, parts, rows, '158325de87ce', 'add', repo=ROOT, prev_rules='')
check('BE (no row rules, no index stamp) does not borrow FR a47e0479ad41: added', 'BE' in added)

# regrade 3 LB: trail rows whose park is in no key file are not a shared part, and its drop is a declared ah3 migration
import importlib
H2 = importlib.reload(H)
src = (ROOT / '.github/scripts/kpc_area_hash.py').read_text(encoding='utf-8')
check("trails no longer writes shared:data/trails#rows-in-no-key", "shared['shared:data/trails#rows-in-no-key']" not in src)
op = {'composition': 'ah2', 'shared:data/trails#rows-in-no-key': 'x', 'data:other': 'same'}
np = {'composition': 'ah3', 'data:other': 'same'}
check('dropping the old stateless-trails shared part at ah3 is not a real move', not H2.real_inputs_moved(op, np, 'ah3'))
check('a real data change still moves', H2.real_inputs_moved(op, dict(np, **{'data:other': 'changed'}), 'ah3'))
sys.exit(0 if ok else 1)
