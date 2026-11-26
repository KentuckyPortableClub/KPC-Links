#!/usr/bin/env python3
"""Speed (26 Nov 2026; grade 1:09 AM: 'a side-by-side test shows the same answers'). Two changes that do the same tests on the same
points, so every answer is the same:
  1. an outline of many rings files its rings by box on a grid, so a point looks only at the rings whose box can hold it
     (Minnesota PAD-US records have up to 3,975 rings; every point looked at all of them);
  2. an old record's own grid points inside it are worked out once per record, not once per fresh candidate.
On 300 random old MN PAD-US records the same-land step went from 148 s to 9 s with every answer, note and best try the same.
Offline, made-up shapes. Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import pathlib, random, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_same_land as SL  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


def ring(x, y, w, h):
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]]


def slow_inside(x, y, rings):
    """The plain even-odd test over every edge of every ring (no bands, no cells)."""
    c = False
    for r in rings:
        j = len(r) - 1
        for i in range(len(r)):
            (xi, yi), (xj, yj) = r[i], r[j]; j = i
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-300) + xi: c = not c
    return c


random.seed(3)
# an outline of 400 rings (islands, some with lakes inside them), well over RING_CELLS
rings = []
for _ in range(300):
    x, y, w = random.uniform(-94, -93.5), random.uniform(45, 45.5), random.uniform(0.002, 0.03)
    rings.append(ring(x, y, w, w * random.uniform(0.5, 2)))
    if random.random() < 0.3: rings.append(ring(x + w * 0.25, y + w * 0.25, w * 0.4, w * 0.4))   # a hole
check(f'the test outline has more rings than RING_CELLS ({len(rings)} > {SL.RING_CELLS})', len(rings) > SL.RING_CELLS)
rb = [SL.box_of([r]) for r in rings]
ix = SL._band_index(rings, rb)
bad = 0
for _ in range(4000):
    x, y = random.uniform(-94.05, -93.45), random.uniform(44.95, 45.55)
    if SL._inside_ix(x, y, rings, rb, ix) != slow_inside(x, y, rings): bad += 1
# points exactly on ring corners and box lines (the cell edges)
for r in rings[:60]:
    for x, y in r[:4]:
        if SL._inside_ix(x, y, rings, rb, ix) != slow_inside(x, y, rings): bad += 1
check(f'many rings: the cell index gives the plain test\'s answer on 4,240 points ({bad} differ)', bad == 0)
few = rings[:10]; fb = [SL.box_of([r]) for r in few]; fix = SL._band_index(few, fb)
bad = sum(1 for _ in range(2000) for x, y in [(random.uniform(-94.05, -93.45), random.uniform(44.95, 45.55))]
          if SL._inside_ix(x, y, few, fb, fix) != slow_inside(x, y, few))
check(f'few rings: the same answer as the plain test ({bad} differ)', bad == 0)


def rec(rs, name):
    return {'_nm': name, '_nms': [], '_ac': 0, '_g': rs, '_bx': SL.box_of(rs)}


# the old record's grid points are worked out once: same shares against every candidate, cached or not
a = rec([ring(-93.8, 45.1, 0.05, 0.04)], 'Old Tract')
va = SL.view(a)
cands = [rec([ring(-93.8 + random.uniform(-0.04, 0.04), 45.1 + random.uniform(-0.03, 0.03), 0.05, 0.04)], 'Fresh') for _ in range(40)]
first = [SL.ground_shares2(va, SL.view(c)) for c in cands]
check('the grid points are kept in the old record\'s view', isinstance(va.get('_gin'), tuple) and va['_gin'][1] == SL.GRID_FINE)
again = [SL.ground_shares2(SL.view(a), SL.view(c)) for c in cands]   # a fresh view of a: worked out again from nothing
check('the same shares with the kept points and without them (40 candidates)', first == again)
va['_gin'] = (va['rings'], SL.GRID_FINE, va['_gin'][2])
other = SL.view(rec([ring(-93.0, 46.0, 0.01, 0.01)], 'Elsewhere'))
other['_gin'] = va['_gin']   # another record's kept points are never used for this one (the rings must be the same list)
check('kept points belong to their own outline only', SL._grid_in(other, other['rings'], SL.box_of(other['rings']),
      [SL.box_of([r]) for r in other['rings']], SL.GRID_FINE) is not va['_gin'][2])
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
