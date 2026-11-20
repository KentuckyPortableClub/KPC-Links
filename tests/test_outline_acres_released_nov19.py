#!/usr/bin/env python3
"""Outline acres on the RELEASED Maryland outlines (2026-11-19; outside review F9, the reviewer's first slice, step S4). The key's
'ac' of US-1588 Patapsco Valley State Park reads 523 on main and 14,225 in the 11 Nov release; its outline measures about 12,920
acres. kpc_outline_acres.py measures the three parks of the finding from data/released/outlines/US-MD.geojson.gz (stable since
11 Nov) within 3%. Pins a released file: in the 'data' group (tests/data-check.txt).
Run:  python3 tests/test_outline_acres_released_nov19.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_outline_acres as OA  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

F = ROOT / 'data/released/outlines/US-MD.geojson.gz'
if not F.is_file(): print('SKIP: no data/released/outlines/US-MD.geojson.gz'); sys.exit(0)
got = OA.state_acres(F.parent, 'US-MD')
for ref, name, want in (('US-1588', 'Patapsco Valley State Park', 12920), ('US-1573', 'Gambrill State Park', 1207), ('US-1589', 'Patuxent River State Park', 5255)):
    a = got.get(ref, 0)
    check(abs(a - want) <= 0.03 * want, f'{ref} {name}: measured {a:,.0f} acres, about {want:,} (within 3%)')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
