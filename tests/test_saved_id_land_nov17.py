#!/usr/bin/env python3
"""D1 (KPC owner, 2026-11-17): a saved record id is the LAND, not the number (KPC_SAVED_ID_LAND, kpc_key_rules.saved_row_ok).
A saved join row [id, record name, acres, how] still describes a record only while the record carries the same name and acres
within 10% (20 acres at least). Run:  python3 tests/test_saved_id_land_nov17.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import gzip, json, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402

RESULTS = []


def check(ok, what):
    RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)


def main():
    row = ['sgflf2743', 'Big Shoals', 1, 'name']
    check(KR.saved_row_ok(row, {'Unit_Nm': 'Big Shoals', 'GIS_Acres': 1.2}), 'same name, about the same acres: still the same land')
    check(not KR.saved_row_ok(row, {'Unit_Nm': 'Save Our Everglades', 'GIS_Acres': 1.59}), 'another name under the same id: not the same land (Big Shoals 17 Nov)')
    check(KR.saved_row_ok(['x1', 'Pine Lake WMA', 1000, 'name'], {'Unit_Nm': 'PINE LAKE WMA', 'GIS_Acres': 1080}), 'case aside, acres 8% off: same land')
    check(not KR.saved_row_ok(['x1', 'Pine Lake WMA', 1000, 'name'], {'Unit_Nm': 'Pine Lake WMA', 'GIS_Acres': 1500}), 'same name, acres 50% off: not the same land')
    check(KR.saved_row_ok(['x1', 'Tiny Park', 5, 'name'], {'Unit_Nm': 'Tiny Park', 'GIS_Acres': 20}), 'a small park gets 20 acres of slack')
    check(KR.saved_row_ok(['x1', 'Zero Acres', 0, 'name'], {'Unit_Nm': 'Zero Acres', 'GIS_Acres': 900}), 'a saved 0 skips the acres test (name decides)')
    check(KR.saved_row_ok(['x1', 'Steese', 9, 'name'], {'Unit_Nm': '', 'Loc_Nm': 'Steese', 'GIS_Acres': 9}), 'a record named only in Loc_Nm is read too')
    check(KR.setting('KPC_SAVED_ID_LAND', {}) == '0' and not KR.on('KPC_SAVED_ID_LAND', {}), 'the switch is OFF unless set (it changes outlines)')
    # the real Florida saved copy, when it is on hand (cache/us/US-FL.json.gz): Big Shoals' renumbered rows are caught
    f = ROOT / 'cache/us/US-FL.json.gz'
    if f.is_file():
        recs = {str(a.get('OBJECTID')): a for a in json.load(gzip.open(f, 'rt'))['recs']}
        bs = json.load(open(ROOT / 'data/us-key/US-FL.json'))['parks']['US-1838']
        bad = [x for x in bs['m'] if str(x[0]) in recs and not KR.saved_row_ok(x, recs[str(x[0])])]
        check(len(bad) >= 10 and all('big shoals' in str(x[1]).lower() for x in bad), f'Florida saved copy: {len(bad)} of Big Shoals\' saved rows now hold other land')
    else: print('SKIP: no cache/us/US-FL.json.gz, the real-data check is not run')
    n = sum(1 for ok, _ in RESULTS if ok)
    print(f'\n{n}/{len(RESULTS)} checks passed')
    return 0 if n == len(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())
