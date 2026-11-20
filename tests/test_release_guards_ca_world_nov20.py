#!/usr/bin/env python3
"""Nov 20: Canada and world release guards (N1 + N3) apply when an area outline exists, same as the US.
MUST_FIX_FIRST stays US-only. Tests use made-up CA-ZZ / GB parks only."""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_release as R  # noqa: E402

FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok:
        FAILS.append(what)


# Direct N1/N3 on made-up parks. No real park names.
ca_key = {
    'CA-99901': {'n': 'Sample North Park', 'g': 'official', 'm': [[11, 'Sample North Park', 10, 'name']]},
    'CA-99902': {'n': 'Sample Pin Park', 'g': 'pin', 'm': []},
}
ca_recs_bad = {
    'CA-99901': {'record_ids': ['row12'], 'via': 'shape'},  # only row numbers
    'CA-99903': {'record_ids': ['11'], 'via': 'shape'},     # not in the key
}
import json, tempfile
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    (td / 'CA-ZZ.json').write_text(json.dumps({'parks': ca_key}), encoding='utf-8')
    (td / 'GB.json').write_text(json.dumps({'parks': {
        'GB-99901': {'n': 'Sample Heath', 'g': 'official', 'm': [[21, 'Sample Heath', 10, 'name'], [22, 'Sample Heath North', 4, 'name']]},
    }}), encoding='utf-8')
    p1 = R.us_release_guard_problems('CA-ZZ', ca_recs_bad, str(td), approved={})
    check(any('CA-99901' in x and 'row numbers' in x for x in p1),
          'CA-ZZ: N1 case 1, only row numbers, is refused')
    check(any('CA-99903' in x and 'does not list it' in x for x in p1),
          'CA-ZZ: N3 item 1, a park the key does not list, is refused')
    clean = {'CA-99901': {'record_ids': ['11'], 'via': 'shape', 'g': 'official'}}
    p2 = R.us_release_guard_problems('CA-ZZ', clean, str(td), approved={})
    check(p2 == [], 'CA-ZZ: a matching outline and key pass the guards')

    miss = {'GB-99901': {'record_ids': ['21'], 'via': 'shape'}}  # missing 22 with a different name
    p3 = R.us_release_guard_problems('GB', miss, str(td), approved={})
    check(any('GB-99901' in x and '22' in x for x in p3),
          'GB: N1 case 3, a missing record with another name, is refused')
    # name+pin not approved
    np = {'GB-99901': {'record_ids': ['21', '22'], 'via': 'name+pin'}}
    p4 = R.us_release_guard_problems('GB', np, str(td), approved={})
    check(any('name+pin' in x and 'GB-99901' in x for x in p4),
          'GB: N3 item 2, name+pin not on the approved list, is refused')
    # MUST_FIX_FIRST does not invent a world/CA row (US-only)
    check('US-2635' in R.MUST_FIX_FIRST and R.MUST_FIX_FIRST['US-2635'][0] == 'US-NV',
          'MUST_FIX_FIRST stays US-only')
    p5 = R.us_release_guard_problems('CA-ZZ', clean, str(td), approved={})
    check(not any('US-2635' in x or 'must be fixed' in x for x in p5),
          'a CA area is not refused by a US MUST_FIX_FIRST row')

print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
