#!/usr/bin/env python3
"""25 Nov 2026, #380 speed (KPC owner: MN took 49.7 min and printed nothing). The same-land proof's point-in-outline and
edge-allowance tests now look only at the edges near the point (kpc_same_land._bands / _edge_index). This test runs the
proof twice on invented records, once the new way and once with the old all-edges loops put back, and asks for the SAME
answer every time (pick's key, level, note and trace; every share). Also: the key prints a progress line while it builds.
Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import math, pathlib, random, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_same_land as SL  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


rnd = random.Random(380)


def blob(cx, cy, r, n, jit=0.25):
    """A closed ring around (cx, cy): n points, radius r with some wobble (a real outline's look)."""
    pts = [[cx + r * (1 + rnd.uniform(-jit, jit)) * math.cos(2 * math.pi * k / n), cy + r * (1 + rnd.uniform(-jit, jit)) * math.sin(2 * math.pi * k / n)] for k in range(n)]
    return pts + [pts[0]]


def dens(ring, k=3, j=2e-5):
    o = []
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        for t in range(k): o.append([x1 + (x2 - x1) * t / k + rnd.uniform(-j, j), y1 + (y2 - y1) * t / k + rnd.uniform(-j, j)])
    return o + [o[0]]


def rough(ring):
    """The 0.001-degree saved copy look: rounded points, every other one dropped."""
    o = [[round(x, 3), round(y, 3)] for x, y in ring[::2]]
    return o + [o[0]] if o[0] != o[-1] else o


# invented fixtures: single outlines, holes, many-piece records, rough old copies, near neighbours, ids that agree / differ
olds, fresh = [], {}
for n in range(70):
    cx, cy = -94 + rnd.uniform(0, 2), 45 + rnd.uniform(0, 2)
    r = rnd.choice([0.002, 0.004, 0.01, 0.03])
    rings = [blob(cx, cy, r, rnd.choice([8, 24, 60, 200]))]
    if n % 5 == 0: rings.append(blob(cx, cy, r * 0.3, 12))                         # a hole
    if n % 7 == 0: rings.append(blob(cx + 3 * r, cy, r * 0.6, 30))                 # a second piece
    nm = rnd.choice(['Mud Lake WMA', 'Lost Valley Prairie', 'Big Woods', 'Unit 4', ''])
    ac = round(SL.acres_of(rings), 1)
    sid = rnd.choice([None, 1000 + n, 2000 + n])
    old = {'OBJECTID': f'sgmne{n}', 'Unit_Nm': nm, 'GIS_Acres': ac * rnd.choice([1, 1, 1.05, 1.4]),
           '_g': {'rings': [rough(x) for x in rings] if n % 3 == 0 else rings}, 'SA': {'su_id': sid} if sid else {}}
    olds.append(old)
    fresh[f'sgmne{9000 + n}'] = {'_nm': nm, '_ac': ac, '_g': [dens(x) for x in rings], 'su_id': str(1000 + n)}
    fresh[f'sgmne{9500 + n}'] = {'_nm': rnd.choice([nm, 'Other Place']), '_ac': ac * 0.9,
                                 '_g': [dens(blob(cx + r * rnd.uniform(-1.2, 1.2), cy + r * rnd.uniform(-1.2, 1.2), r * rnd.uniform(0.5, 1.2), 40))],
                                 'su_id': str(5000 + n)}
for e in fresh.values(): e['_bx'] = SL.box_of(SL.rings_of(e['_g']))


def run_all():
    SL._VIEWS.clear(); SL._BIX.clear()
    out, shares = [], []
    for a in olds:
        bb = SL.box_of(SL.rings_of(a['_g']))
        cands = {k: dict(e) for k, e in fresh.items() if SL.boxes_overlap(bb, e['_bx'], 0.001)}
        tr = {}
        out.append((a['OBJECTID'], SL.pick(a, cands, SL.id_spec('sgmne'), cache=False, own=a['OBJECTID'], trace=tr), tr))
        va = SL.view(a)
        for k, c in cands.items():
            vc = SL.view(c)
            shares.append((a['OBJECTID'], k, SL.ground_shares2(va, vc), SL.ground_shares2(va, vc, 16),
                           SL.shares(va['rings'], vc['rings'])))
    return out, shares


new = run_all()

# the old way: every edge of every ring for every grid point (the code before this change)
saved = SL._bands, SL._inside_ix, SL._edge_index, SL._near_edge_ix
SL._bands = lambda rings, rboxes: None
SL._inside_ix = lambda x, y, rings, rboxes, ix: SL._inside(x, y, rings, rboxes)
SL._edge_index = lambda rings: rings
SL._near_edge_ix = lambda x, y, rings, d: SL._near_edge(x, y, rings, d)
old_way = run_all()
SL._bands, SL._inside_ix, SL._edge_index, SL._near_edge_ix = saved

check(f'fixtures reach every proof level and the rough path ({sorted({str(x[1][1]) for x in new[0]})})',
      {'id', 'overlap', 'None'} <= {str(x[1][1]) for x in new[0]} and any(x[2].get('rough') for x in new[0]))
check(f'pick: the same key, level, note and trace for all {len(new[0])} old records', new[0] == old_way[0])
check(f'shares / ground_shares2 (48 and 16 grid): the same numbers for all {len(new[1])} pairs', new[1] == old_way[1])
check('some pairs land on the edge allowance (the indexed edge test is used)',
      any(s[2] and s[2][0] != s[2][1] for s in new[1]))

# point by point: the indexed tests against the all-edges loops, on many points, near edges too
pts_ok = edge_ok = True
for e in list(fresh.values())[:40]:
    rings = SL.rings_of(e['_g']); rb = [SL.box_of([r]) for r in rings]
    bix, eix = SL._band_index(rings, rb), SL._edge_index(rings)
    bx = SL.box_of(rings)
    pts = [(rnd.uniform(bx[0] - 0.002, bx[2] + 0.002), rnd.uniform(bx[1] - 0.002, bx[3] + 0.002)) for _ in range(300)]
    pts += [(x + rnd.uniform(-0.0012, 0.0012), y + rnd.uniform(-0.0012, 0.0012)) for r in rings for x, y in r[::3]]
    pts += [(x, y) for r in rings for x, y in r[::5]]   # exactly on a corner
    for x, y in pts:
        pts_ok &= SL._inside_ix(x, y, rings, rb, bix) == SL._inside(x, y, rings, rb)
        for d in (SL.EDGE, 0.0004, 1e-7):
            edge_ok &= SL._near_edge_ix(x, y, eix, d) == SL._near_edge(x, y, rings, d)
check('point in outline: the banded test = the all-edges test on every point', pts_ok)
check('edge allowance: the indexed test = the all-edges test on every point and distance', edge_ok)
check('selftest of kpc_same_land still passes', SL.selftest() == 0)

# the key says where it is while it builds (MN went 49.7 min with no line)
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text()
check('kpc_us_key: progress() prints flushed lines every PROGRESS_EVERY (500)',
      re.search(r"^PROGRESS_EVERY = 500$", src, re.M) and re.search(r"def progress\(.*?flush=True\)", src, re.S))
for what in ('state build started (', 'same-land proof: old records', 'store fields by proof: records', 'proven-only gate: parks',
             'matching: parks', 'joining the fresh layer files', 'fresh layer files joined', 'match checks done', 'state build done'):
    check(f"kpc_us_key: progress line '{what}'", f"progress(st, '{what}" in src or f"progress(st, f'{what}" in src)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
