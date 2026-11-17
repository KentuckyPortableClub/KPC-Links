#!/usr/bin/env python3
"""Handoff 8 fix 4 (switch KPC_MEASURED_ACRES): a park whose records have no acres on file gets 'ac' measured from the saved shape.
The made-up park below is drawn only from two 0-acre study-area pieces (one with a hole) in Utah; its 'ac' must be within 5% of the
shape's true area (measured here a second, independent way: the area on the sphere).
Run:  python3 tests/test_h8_measured_acres_nov17.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import math, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

def sphere_acres(rings):   # independent check: the polygon area on a sphere of the earth's mean radius (holes wind the other way)
    R = 6371008.8; tot = 0.0
    for r in rings:
        s = 0.0
        for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]):
            s += math.radians(x2 - x1) * (2 + math.sin(math.radians(y1)) + math.sin(math.radians(y2)))
        tot += s * R * R / 2
    return abs(tot) / 4046.8564224
box = lambda x, y, w, h: [[x, y], [x, y + h], [x + w, y + h], [x + w, y], [x, y]]             # clockwise (an outer ring, ESRI order)
hole = lambda x, y, w, h: [[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]]            # the other way round (a hole)
pieces = {'wsa101': [box(-113.20, 38.90, 0.10, 0.06), hole(-113.17, 38.92, 0.02, 0.02)],     # study-area piece with a hole
          'wsa102': [box(-113.05, 38.95, 0.04, 0.03)]}
rows = [['wsa101', 'Notch Peak Wilderness Study Area', 0, 'name'], ['wsa102', 'Notch Peak Wilderness Study Area', 0, 'name']]
truth = sum(sphere_acres(r) for r in pieces.values())
got = KR.measured_ac(rows, lambda i: pieces.get(i))
check(got is not None and got[1] == 2, 'both 0-acre pieces are measured')
check(got and abs(got[0] - truth) <= 0.05 * truth, f"a park drawn only from 0-acre study-area pieces gets 'ac' {got and got[0]} within 5% of its shape ({truth:.0f} acres)")
check(abs(KR.ring_acres(pieces['wsa101']) - sphere_acres(pieces['wsa101'])) <= 0.02 * sphere_acres(pieces['wsa101']), 'the hole is taken out')
check(KR.measured_ac([['a', 'X', 120, 'name'], ['wsa102', 'Y', 0, 'name']], lambda i: pieces.get(i))[0] == round(120 + KR.ring_acres(pieces['wsa102'])),
      'a record with acres on file counts its own acres; only the 0-acre one is measured')
check(KR.measured_ac([['a', 'X', 120, 'name']], lambda i: pieces.get(i)) is None, 'no 0-acre record: nothing to measure (the park keeps what it has)')
check(KR.measured_ac([['trl1', 'A State Trail', 0, 'official trail line']], lambda i: None) is None, 'a trail line (no shape) gets no acres')
part = KR.measured_ac([['wsa101', 'X', 0, 'name']], lambda i: pieces.get(i) + [box(-100.0, 38.0, 0.05, 0.05)], {'wsa101': [[-113.21, 38.89, -113.09, 38.97]]})
check(part and abs(part[0] - KR.ring_acres(pieces['wsa101'])) <= 1, "a park given only its own parts of a record (rule B12 'parts') measures only those parts")
check(not KR.on('KPC_MEASURED_ACRES', {}), 'the switch is OFF unless set')
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
check("p['ac'], p['ac_how'] = got[0], 'measured'" in src and "if _kr('KPC_MEASURED_ACRES'):" in src, "the US key marks a measured 'ac' (ac_how = measured), behind its switch")
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
