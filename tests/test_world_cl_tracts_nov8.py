#!/usr/bin/env python3
"""Nov 8 (Quality NO on W-42480248682: AX, CH, CL, LK failed). CL ran past its 100 min limit inside kpc_tracts (acres and piece
grouping on records with ~20,000 rings). The answer is unchanged; only the time is bounded."""
import json, pathlib, sys, time, os
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_pin_edge as PE, kpc_tracts as TR
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
sq = lambda x, y, s: [[x, y], [x + s, y], [x + s, y + s], [x, y + s], [x, y]]
outer, hole = sq(0, 0, .1), sq(.02, .02, .01)
check(abs(PE.acres_rings([outer, hole]) - (PE.acres_rings([outer]) - PE.acres_rings([hole]))) < 0.01, 'a hole still subtracts')
check(abs(PE.acres_rings([outer, sq(1, 1, .1)]) - PE.acres_rings([outer]) - PE.acres_rings([sq(1, 1, .1)])) < 0.01, 'two pieces still add')
many = [sq(i * 0.02, (i % 50) * 0.02, 0.005) for i in range(6000)]
t = time.monotonic(); a = PE.acres_rings(many); dt = time.monotonic() - t
check(a > 0 and dt < 30, f'6,000 rings measured in {dt:.1f} s')
PE.ACRES_S, old = 0.0, PE.ACRES_S
try:
    PE.acres_rings(many); check(False, 'time limit raises')
except PE.AcresTooSlow: check(True, 'time limit raises AcresTooSlow')
nest = TR.nested_geometry({'BIG': many, 'S': [sq(5, 5, .1)]})
check(isinstance(nest, list), 'nesting skips a park too big to measure instead of failing the whole country')
PE.ACRES_S = old
check(TR.pieces([sq(i, 0, .1) for i in range(TR.PIECES_MAX + 1)]) is None and TR.pieces([sq(0, 0, .1), sq(5, 5, .1)]) == 2, 'pieces left out over PIECES_MAX rings; small records unchanged')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
