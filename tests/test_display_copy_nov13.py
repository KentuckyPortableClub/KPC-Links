#!/usr/bin/env python3
"""Display copy from the outline store (KPC owner, 2026-11-13; levels, pieces, one layer per park, parks across state lines
2026-11-14): tools/kpc_display_copy.py and kpc-outline-display.js.

Everything here is SYNTHETIC: small fake stores are written into a temporary folder by this test (made-up parks near 0 N 0 E,
tests/display_copy_fixture.py), in the store's format 1. No real outline, no network (sockets are blocked), no repo file
written. The 500,000-point multi-state park is in tests/test_display_copy_huge_nov14.py.
Prints PASS / FAIL lines and ends ALL PASS or SOME FAILED."""
import gzip, hashlib, json, math, os, pathlib, shutil, socket, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))


def _no_net(*a, **k): raise OSError('network blocked in this test')


socket.socket.connect = _no_net
socket.create_connection = _no_net
import kpc_display_copy as K  # noqa: E402
from display_copy_fixture import circle, record, park, write_store, V2_OPEN  # noqa: E402

FAILS = []


def check(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok: FAILS.append(name)


def feats_of(out, area):
    idx = json.loads((out / area / 'INDEX.json').read_text())
    fs = []
    for name, *_ in idx['parts']: fs += json.loads(gzip.decompress((out / area / name).read_bytes()))['features']
    return idx, fs


def by_ref(fs):
    d = {}
    for f in fs: d.setdefault(f['properties']['ref'], []).append(f)
    return d


def drawn_lines(fs):
    """every drawn line (polygon rings or line strings; 'hit' features are never drawn)"""
    out = []
    for f in fs:
        if f['properties'].get('role') == 'hit': continue
        g = f['geometry']
        out += g['coordinates'] if g['type'] == 'MultiLineString' else [r for p in g['coordinates'] for r in p]
    return out


def square(x0, y0, x1, y1, n_side=20):
    """a clockwise square ring with n_side points per side"""
    pts = [(x0 + (x1 - x0) * i / n_side, y1) for i in range(n_side)] + [(x1, y1 - (y1 - y0) * i / n_side) for i in range(n_side)]
    pts += [(x1 - (x1 - x0) * i / n_side, y0) for i in range(n_side)] + [(x0, y0 + (y1 - y0) * i / n_side) for i in range(n_side)]
    pts = [(round(x, 6), round(y, 6)) for x, y in pts]
    return pts + [pts[0]]


tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-display-test-'))
try:
    store = tmp / 'store'
    big = [circle(0.5 + 0.02 * k, 0.5, 0.008, 900, wobble=0.05, phase=k) for k in range(6)]
    pad_dup = circle(0.15, 0.6, 0.01, 150)
    pad_shift = [(round(x + 0.0001, 6), y) for x, y in pad_dup]                                    # same land ~11 m east
    parks = [
        park('US-0001', [record('a1', 'lay1', [circle(0.1, 0.1, 0.01, 200, wobble=0.03)])]),
        park('US-0002', [record('b1', 'lay1', [circle(0.2, 0.1, 0.01, 120)]), record('b2', 'lay2', [circle(0.2, 0.1, 0.01, 120)]),
                         record('b3', 'lay1', [circle(0.2, 0.1, 0.0100001, 97)])]),
        park('US-0003', [record('c1', 'lay1', [circle(0.3, 0.1, 0.01, 80)]), record('c2', 'lay2', [circle(0.31, 0.1, 0.004, 60)], licence='')]),
        park('US-0004', [record('d1', 'lay1', [circle(0.4, 0.1, 0.01, 60)]), record('d2', 'lay1', [circle(0.9, 0.1, 0.01, 60)])]),
        park('US-0005', [record('e%d' % k, 'lay1', [r]) for k, r in enumerate(big)]),
        park('US-0006', [record('f1', 'wdpa', [circle(0.6, 0.2, 0.01, 50)], licence='OPEN; credit: Protected Planet WDPA',
                                url='https://data-gis.unep-wcmc.org/server/rest/services/ProtectedSites/The_World_Database_of_Protected_Areas/MapServer/1')]),
        park('US-0007', [record('g1', 'lay1', [circle(0.7, 0.2, 0.02, 100), circle(0.7, 0.2, 0.005, 40, clockwise=False)])]),
        park('US-0008', [record('h1', 'lay4', [circle(0.8, 0.2, 0.01, 50)], licence='RESTRICTED; credit: X')]),
        park('US-0009', [record('i1', 'lay1', [circle(0.1, 0.3, 0.01, 50)])]),
        park('US-0010', [record('j1', 'lay5', [circle(0.2, 0.3, 0.01, 50)], licence='NON-COMMERCIAL; credit: County Parks')]),
        park('US-0011', [record('k%d' % k, 'lay1', [circle(0.3 + 0.005 * (k % 26), 0.4 + 0.005 * (k // 26), 0.002, 8, phase=k)])
                         for k in range(650)]),
        park('US-0012', [record('m1', 'stl', [pad_dup]), record('m2', 'PAD-US', [pad_shift], licence='OPEN; credit: USGS PAD-US')]),   # same land
        park('US-0013', [record('n1', 'stl', [circle(0.35, 0.6, 0.01, 150)]),
                         record('n2', 'PAD-US', [circle(0.365, 0.6, 0.01, 150)], licence='OPEN; credit: USGS PAD-US')]),             # half overlaps
    ]
    write_store(store, 'US-ZZ', parks)
    dcsv = tmp / 'doubtful.csv'
    dcsv.write_text('state,park,name,matcher_doubt_code,key_records_joined,matcher_records,matcher_review_state\n'
                    'ZZ,US-0009,Test,pin-far,i1,,KEEP-FLAGGED\nAA,US-0001,Other state,pin-far,a1,,KEEP-FLAGGED\n')
    out = tmp / 'out'
    logs = []
    rep = K.build(store, 'US-ZZ', out, doubtful=K.read_doubtful(dcsv, 'US-ZZ'), log=logs.append)
    idx, fs = feats_of(out, 'US-ZZ')
    feats = by_ref(fs)
    one = {r: v[0] for r, v in feats.items()}
    fb = idx['fallback']
    rows = {r['ref']: r for r in rep['rows']}

    check('the check of what was written finds no problem', K.check(out, 'US-ZZ') == [])
    check('a one-tract park with an OPEN licence is drawn with every point (no simplifying under the cap)',
          'US-0001' in feats and rows['US-0001']['detail_m'] == 0 and rows['US-0001']['points'] == 201)
    check('identical geometry in two layers is drawn once; a near-identical tract of the same layer is drawn once too',
          rows['US-0002']['drawn_records'] == 1 and rows['US-0002']['drawn_once'] == 1)
    check("a park with ONE unlicensed tract is left out whole and keeps today's outline (never half a park)",
          'US-0003' not in feats and 'licence gate' in fb.get('US-0003', '') and 'c2' in fb.get('US-0003', ''))
    check("tracts 10 km or more apart = check join: today's outline, flagged", 'US-0004' not in feats and fb.get('US-0004', '').startswith('check join'))
    check('a park over the cap is simplified to the cap with the smallest ladder step, written on it',
          rows['US-0005']['store_points'] == 5406 and rows['US-0005']['points'] <= 3000 and one['US-0005']['properties']['detail_m'] == rows['US-0005']['detail_m'])
    check('the error at the cap is measured and never more than the tolerance plus rounding (0.6 m at 5 decimals)',
          rows['US-0005']['worst_m'] <= rows['US-0005']['detail_m'] + 0.7)
    prev = ([0.0] + [s for s in K.LADDER if s < rows['US-0005']['detail_m']])[-1]
    rr = [K.Rec('US-ZZ', 'x%d' % i, 'l', [[(x, y) for x, y in r]], '') for i, r in enumerate(big)]; K.clusters(rr)
    check('the step before the one used would have gone over the cap (simplified only as far as needed)',
          K.level(rr, 0, fixed=prev)['points'] > 3000)
    check('a park of 650 small tracts fits the overview cap (rings smaller than the tolerance wait for a finer level)',
          rows['US-0011']['points'] <= 3000 and rows['US-0011']['detail_m'] > 0)
    check('WDPA never goes in, whatever its licence text says', 'US-0006' not in feats and 'WDPA' in fb.get('US-0006', ''))
    check('a hole stays a hole: one polygon with an outer ring and an inner ring',
          len(one['US-0007']['geometry']['coordinates']) == 1 and len(one['US-0007']['geometry']['coordinates'][0]) == 2)
    check('a RESTRICTED licence class is refused', 'US-0008' not in feats and 'RESTRICTED' in fb.get('US-0008', ''))
    check("a park in the doubtful-joins list keeps today's outline (another state's row is ignored)",
          'US-0009' not in feats and fb.get('US-0009', '').startswith('doubtful join') and 'US-0001' in feats)
    check('NON-COMMERCIAL counts as publishable and its credit line is kept per layer',
          'US-0010' in feats and idx['credits'].get('lay5') == 'County Parks' and one['US-0010']['properties']['cr'] == ['lay5'])
    check('every park of the store is either drawn or in the fallback list, never both',
          set(feats) | set(fb) == {p['ref'] for p in parks} and not (set(feats) & set(fb)))
    # one layer per park
    check('ONE LAYER PER PARK: the same land in PAD-US 11 m off the state layer is not drawn; the state layer won',
          rows['US-0012']['won'] == 'stl' and rows['US-0012']['dropped'] == {'PAD-US': 1} and one['US-0012']['properties']['records'] == ['m1']
          and idx['won']['US-0012']['won'] == 'stl')
    n13 = feats['US-0013']; line13 = [f for f in n13 if f['properties'].get('role') == 'line']
    pad_inside = [p for ln in drawn_lines(n13) for p in ln if math.hypot(p[0] - 0.35, p[1] - 0.6) < 0.0095]   # a stretch may end one segment in, where the lines meet
    check("...a PAD-US tract that adds land is kept, but only its line OUTSIDE the state layer's land is drawn (never mixed)",
          rows['US-0013']['extra'] == {'PAD-US': 1} and len(line13) == 1 and any(f['properties'].get('role') == 'hit' for f in n13)
          and not pad_inside and sorted(one['US-0013']['properties']['records']) == ['n1', 'n2'])
    tbl = json.loads((ROOT / 'tools' / 'kpc_display_precedence.json').read_text())
    check('the precedence table is the small file tools/kpc_display_precedence.json, PAD-US last by default',
          K.DEFAULT_PRECEDENCE == tbl and tbl['default'][-1] == 'PAD-US' and tbl['US-NH'][-1] == 'PAD-US')
    rp = K.build(store, 'US-ZZ', tmp / 'out-prec', precedence_table={'US-ZZ': ['PAD-US', '*']}, log=logs.append)
    check('the precedence table is editable: listing PAD-US first makes PAD-US win', {r['ref']: r for r in rp['rows']}['US-0012']['won'] == 'PAD-US')
    # levels
    many = rows['US-0011']
    check('a park whose overview is more than 25 m off gets a MIDDLE file (under 1 MB) that is finer',
          (many['worst_m'] <= K.MID_OVER_M and 'US-0011' not in idx['mid']) or
          ('US-0011' in idx['mid'] and idx['mid']['US-0011'][3] < 1_000_000 and many['mid_worst_m'] < many['worst_m']))
    coarse = many['mid_worst_m'] if many['mid_worst_m'] is not None else many['worst_m']
    check('a FINE level is written only when the coarser levels are more than 5 m off', ('US-0011' in idx['fine']) == (coarse > K.FINE_OVER_M))
    # fine pieces: a long rough line, a tiny piece cap to force small tiles
    rough = [(round(0.1 + i * 0.00002, 6), round(0.8 + 0.0003 * math.sin(i / 7) + 0.00001 * math.sin(i * 1.7), 6)) for i in range(6000)]
    ring = list(reversed(rough + [(round(0.1 + 5999 * 0.00002, 6), 0.81), (0.1, 0.81)] + [rough[0]]))
    write_store(tmp / 'store-f', 'US-ZZ', [park('US-0020', [record('p1', 'lay1', [ring])])])
    rf = K.build(tmp / 'store-f', 'US-ZZ', tmp / 'out-f', cap=200, piece_cap=1000, mid_cap=500, log=logs.append)
    i_f = json.loads((tmp / 'out-f' / 'US-ZZ' / 'INDEX.json').read_text())
    fe = i_f['fine'].get('US-0020') or {}
    sizes = [t[1] for t in (fe.get('tiles') or {}).values()]
    check(f'FINE pieces: every piece is under the hard cap ({len(sizes)} pieces, largest {max(sizes or [0])} B, cap 1000) and the tile shrank to fit',
          bool(sizes) and max(sizes) <= 1000 and fe['t'] < K.TILE_START and K.check(tmp / 'out-f', 'US-ZZ', piece_cap=1000) == [])
    pieces = {}
    for t in fe.get('tiles') or {}:
        pieces[t] = json.loads(gzip.decompress((tmp / 'out-f' / 'US-ZZ' / 'fine' / 'US-0020' / f'{t}.geojson.gz').read_bytes()))['features'][0]['geometry']['coordinates']
    ends = {}
    for ls in pieces.values():
        for l in ls:
            for p in (tuple(l[0]), tuple(l[-1])): ends[p] = ends.get(p, 0) + 1
    check('...the pieces join exactly: every cut point is shared by two pieces (no gap, no overlap)', bool(ends) and not [p for p, n in ends.items() if n % 2])
    check('...the FINE level is within 5 m of the store', rf['rows'][0]['fine_worst_m'] is not None and rf['rows'][0]['fine_worst_m'] <= 5.0)
    T = fe.get('t') or 1
    inside = all(int(t.split('_')[0]) * T - 1e-9 <= x <= (int(t.split('_')[0]) + 1) * T + 1e-9 and int(t.split('_')[1]) * T - 1e-9 <= y <= (int(t.split('_')[1]) + 1) * T + 1e-9
                 for t, ls in pieces.items() for l in ls for x, y in l)
    check('...each piece lies inside its own tile', inside)
    # parts, rebuilds, store untouched
    out2 = tmp / 'out2'
    K.build(store, 'US-ZZ', out2, doubtful=K.read_doubtful(dcsv, 'US-ZZ'), max_part=20000, log=logs.append)
    idx2 = json.loads((out2 / 'US-ZZ' / 'INDEX.json').read_text())
    sz = [(out2 / 'US-ZZ' / n).stat().st_size for n, *_ in idx2['parts']]
    check(f'a small part size splits the area into whole-park parts, each under the limit ({len(sz)} parts)',
          len(sz) >= 2 and all(s <= 20000 for s in sz) and K.check(out2, 'US-ZZ') == [])
    out3 = tmp / 'out3'
    K.build(store, 'US-ZZ', out3, doubtful=K.read_doubtful(dcsv, 'US-ZZ'), log=logs.append)
    check('the same store gives byte-identical display files',
          all((out / 'US-ZZ' / n).read_bytes() == (out3 / 'US-ZZ' / n).read_bytes() for n, *_ in idx['parts']))
    before = {p.name: p.read_bytes() for p in store.iterdir()}
    K.build(store, 'US-ZZ', tmp / 'out4', log=logs.append)
    check('the store files are never changed', before == {p.name: p.read_bytes() for p in store.iterdir()})
    # licence: store tool full 2 index fields; older index without them
    v2p = [park('US-0030', [record('q1', 'lay1', [circle(0.1, 0.9, 0.01, 40)], v2=V2_OPEN)]),
           park('US-0031', [record('q2', 'lay1', [circle(0.2, 0.9, 0.01, 40)], v2={'licence_class': 'PRIVATE UNTIL LICENCE READ', 'publishable': False})]),
           park('US-0032', [record('q3', 'lay1', [circle(0.3, 0.9, 0.01, 40)], v2={'licence_class': 'LOOKS RESTRICTED', 'publishable': True})]),
           park('US-0033', [record('q4', 'PAD-US', [circle(0.4, 0.9, 0.01, 40)], v2={'licence_class': 'US FEDERAL (public domain)', 'credit': 'USGS PAD-US', 'publishable': True})])]
    write_store(tmp / 'store-v2', 'US-ZZ', v2p, index_licence=False, v2=True)
    K.build(tmp / 'store-v2', 'US-ZZ', tmp / 'out-v2', log=logs.append)
    i2 = json.loads((tmp / 'out-v2' / 'US-ZZ' / 'INDEX.json').read_text())
    check("store index full 2: 'publishable' true passes and its credit line is used",
          'US-0030' not in i2['fallback'] and i2['credits'].get('lay1') == 'Synthetic State Lands' and i2['credits'].get('PAD-US') == 'USGS PAD-US')
    check("...'publishable' false keeps the park on today's outline", 'not publishable' in i2['fallback'].get('US-0031', ''))
    check('...a restricting class is refused even if marked publishable (belt and braces)', 'restricts' in i2['fallback'].get('US-0032', ''))
    p6 = [park('US-0001', [dict(record('a1', 'lay1', [circle(0.1, 0.1, 0.01, 50)]), licence='')])]
    write_store(tmp / 'store6', 'US-ZZ', p6, index_licence=False)
    r6 = K.build(tmp / 'store6', 'US-ZZ', tmp / 'out6', log=logs.append)
    check("an older index with no licence recorded anywhere = not public (0 parks drawn, kept on today's outline)", r6['parks_drawn'] == 0 and r6['fallback'] == 1)
    # private preview
    r7 = K.build(store, 'US-ZZ', tmp / 'prev', preview=True, log=logs.append)
    i7 = json.loads((tmp / 'prev' / 'US-ZZ' / 'INDEX.json').read_text())
    check('a private preview skips the licence gate but is stamped PRIVATE PREVIEW in the index and every file',
          i7.get('stamp') == K.PREVIEW_STAMP and 'US-0003' not in i7['fallback'] and r7['parks_drawn'] > rep['parks_drawn'] and K.check(tmp / 'prev', 'US-ZZ') == [])
    check('a private preview still never draws WDPA', 'US-0006' in i7['fallback'])
    try:
        K.build(store, 'US-ZZ', tmp / 'site' / 'data' / 'display', preview=True, log=logs.append); refused = False
    except K.DisplayError: refused = True
    check('a private preview is refused in a folder named like the public one (data/display)', refused)
    check('check --public refuses a private preview; the gated copy passes it',
          any('PRIVATE PREVIEW' in x for x in K.check(tmp / 'prev', 'US-ZZ', public=True)) and K.check(out, 'US-ZZ', public=True) == [])
    (out / 'US-ZZ' / 'stray.json').write_text('{}')
    check('check --public refuses a file the INDEX does not list', any('not listed' in x for x in K.check(out, 'US-ZZ', public=True)))
    (out / 'US-ZZ' / 'stray.json').unlink()
    # a moved coordinate in the store
    st8 = tmp / 'store8'; shutil.copytree(store, st8)
    b = bytearray((st8 / 'US-ZZ.kpcstore.json.gz').read_bytes())
    ix = json.loads((st8 / 'index-US-ZZ.json').read_text()); e = ix['parks']['US-0001']
    m = json.loads(gzip.decompress(bytes(b[e['o']:e['o'] + e['n']])).decode().lstrip(',\n'))
    m['records'][0]['rings'][0][3] += 1
    nm = gzip.compress(json.dumps(m, separators=(',', ':')).encode(), 9, mtime=0)
    shift = len(nm) - e['n']
    for v in ix['parks'].values():
        if v['o'] > e['o']: v['o'] += shift
    ix['parks']['US-0001']['n'] = len(nm); ix['files'] = {}
    (st8 / 'index-US-ZZ.json').write_text(json.dumps(ix))
    (st8 / 'US-ZZ.kpcstore.json.gz').write_bytes(bytes(b[:e['o']]) + nm + bytes(b[e['o'] + e['n']:]))
    try:
        K.build(st8, 'US-ZZ', tmp / 'out8', log=logs.append); caught = False
    except K.DisplayError as ex: caught = 'checksum' in str(ex)
    check('a moved coordinate in the store stops the build (checksum)', caught)
    # Douglas-Peucker and projection
    xs = [i * 10.0 for i in range(50)] + [0.0]; ys = [math.sin(i / 3) * 40 for i in range(50)] + [0.0]
    imp = K.dp_importance(xs, ys); ok1 = ok2 = True
    for t in (1, 5, 20, 100, 1000, 5000):
        k = K.kept_at(imp, t)
        ok1 &= K.ring_error(xs, ys, k) <= t + 1e-9 or len(k) == 4
        ok2 &= len(k) >= 4
    check('Douglas-Peucker (computed once, filtered per level) never leaves a point farther than the tolerance; a ring keeps 4 points', ok1 and ok2)
    check('the local projection is metres on the ellipsoid (1 degree of latitude at 45 N = 111.13 km, of longitude 78.85 km)',
          abs(K.local_scale(45)[1] - 111132) < 15 and abs(K.local_scale(45)[0] - 78847) < 15)
    pr = K.Proj([(179.9, 52.0), (-179.9, 52.1)])
    xs_, _ = pr.xy([(179.9, 52.0), (-179.9, 52.0)])
    check('a park across 180 degrees is measured on one plane (0.2 degree apart is ~14 km, not ~24,000 km)', 10_000 < abs(xs_[1] - xs_[0]) < 20_000)

    # ---- two areas: one park across a state line ---------------------------------------------------------------------------
    sa = tmp / 'store-2'
    west, east = square(0.1, 0.1, 0.2, 0.2, 30), square(0.2, 0.1, 0.3, 0.2, 30)      # they meet along x = 0.2 (the state line)
    copy_a = square(0.12, 0.25, 0.18, 0.3, 30)                                          # the same land in both states' stores...
    copy_b = [(round(x + 0.000005, 6), y) for x, y in copy_a]                             # ...0.5 m apart: both tracts on the SAME side
    shared = record('sh1', 'stl', [square(0.2, 0.32, 0.24, 0.36, 10)])
    write_store(sa, 'US-ZA', [park('US-0040', [record('w1', 'stl', [west]), record('cp1', 'stl', [copy_a]), shared]),
                              park('US-0041', [record('o1', 'stl', [circle(0.15, 0.5, 0.01, 40)])])])
    write_store(sa, 'US-ZB', [park('US-0040', [record('e1', 'stl', [east]), record('cp2', 'stl', [copy_b]), dict(shared)])])
    K.build(sa, ['US-ZA', 'US-ZB'], tmp / 'out-2', log=logs.append)
    ia, fa = feats_of(tmp / 'out-2', 'US-ZA'); ib, fb2 = feats_of(tmp / 'out-2', 'US-ZB')
    la = drawn_lines([f for f in fa if f['properties']['ref'] == 'US-0040']); lb = drawn_lines([f for f in fb2 if f['properties']['ref'] == 'US-0040'])
    on_line = [(a, b2) for l in la + lb for a, b2 in zip(l, l[1:]) if a[0] == 0.2 and b2[0] == 0.2 and 0.1 < a[1] < 0.2 and 0.1 < b2[1] < 0.2]
    check('A PARK ACROSS TWO STATES draws no line where its own tracts meet at the state line (no seam, no double line)', not on_line)
    check("...the tracts' outer edges are still drawn on both sides",
          any(abs(p[1] - 0.2) < 1e-9 and 0.1 < p[0] < 0.2 for l in la for p in l) and any(abs(p[1] - 0.2) < 1e-9 and 0.2 < p[0] < 0.3 for l in lb for p in l))
    check("...a record held in both states' stores is drawn from one state only",
          sum(1 for f in fa + fb2 if 'sh1' in (f['properties'].get('records') or []) and f['properties'].get('role') != 'hit') == 1)
    cp_drawn = [p for l in la + lb for p in l if 0.25 - 1e-9 <= p[1] <= 0.3 + 1e-9 and 0.12 <= p[0] <= 0.18001]
    check('...two copies of the same boundary with both tracts on the same side are NOT taken for a seam: the line stays', len(cp_drawn) > 20)
    pa = [f for f in fa if f['properties']['ref'] == 'US-0040']
    check("...the park carries both areas and the run's build id, as a line feature plus a click-only area",
          all(f['properties'].get('areas') == ['US-ZA', 'US-ZB'] and f['properties'].get('gen') == ia['gen'] == ib['gen'] for f in pa)
          and sorted(f['properties']['role'] for f in pa) == ['hit', 'line'])
    K.build(sa, 'US-ZA', tmp / 'out-2b', park_areas={'US-0040': ['US-ZA', 'US-ZB']}, log=logs.append)
    ib2 = json.loads((tmp / 'out-2b' / 'US-ZA' / 'INDEX.json').read_text())
    check("...built WITHOUT its other state (the key says it is in both): today's outline, flagged",
          'not in this run' in ib2['fallback'].get('US-0040', '') and 'US-0041' not in ib2['fallback'])

    # ---- the browser loader (node, if this machine has it) -----------------------------------------------------------------
    node = shutil.which('node')
    if not node:
        print('SKIP browser loader checks: node is not installed here')
    else:
        site = tmp / 'site2'; (site / 'data' / 'display').mkdir(parents=True)
        shutil.copytree(out / 'US-ZZ', site / 'data' / 'display' / 'US-ZZ')
        shutil.copytree(tmp / 'prev' / 'US-ZZ', site / 'data' / 'display' / 'US-ZY')
        shutil.copytree(tmp / 'out-2' / 'US-ZA', site / 'data' / 'display' / 'US-ZA')
        shutil.copytree(tmp / 'out-2' / 'US-ZB', site / 'data' / 'display' / 'US-ZB')
        K.build(tmp / 'store-f', 'US-ZZ', tmp / 'out-f2', cap=200, piece_cap=1000, mid_cap=500, log=logs.append)
        shutil.copytree(tmp / 'out-f2' / 'US-ZZ', site / 'data' / 'display' / 'US-ZF')
        zf = site / 'data' / 'display' / 'US-ZF'   # rename that area US-ZZ -> US-ZF (index and part) so both can be loaded
        ixf = json.loads((zf / 'INDEX.json').read_text()); ixf['area'] = 'US-ZF'
        for prt in ixf['parts']:
            pth = zf / prt[0]; d = json.loads(gzip.decompress(pth.read_bytes())); d['kpc']['area'] = 'US-ZF'
            nb = gzip.compress(json.dumps(d).encode(), mtime=0); (zf / 'US-ZF.geojson.gz').write_bytes(nb); pth.unlink()
            prt[0], prt[1] = 'US-ZF.geojson.gz', hashlib.sha256(nb).hexdigest()[:12]
        (zf / 'INDEX.json').write_text(json.dumps(ixf))
        js = (ROOT / 'kpc-outline-display.js').resolve()
        old = {'features': [{'type': 'Feature', 'properties': {'ref': r, 'g': 'official', 'old': True}, 'geometry': None}
                            for r in ('US-0001', 'US-0003', 'US-0099', 'US-0040')] + [{'type': 'Feature', 'properties': {'ref': 'US-0098', 'g': 'pin'}, 'geometry': None}]}
        fine_box = [0.1, 0.79, 0.104, 0.81]
        script = r'''
const fs=require('fs'),path=require('path'),zlib=require('zlib');const SITE=process.argv[2],JS=process.argv[3],OLD=JSON.parse(process.argv[4]),BOX=JSON.parse(process.argv[5]);
function setup(search,store){const ls={};global.localStorage={getItem:k=>k in ls?ls[k]:null,setItem:(k,v)=>{ls[k]=String(v)},removeItem:k=>{delete ls[k]}};if(store)ls.kpcOutlineStore='1';
 global.location={search};global.window=global;delete global.kpcDisplayOutlines;global.fetched=[];
 global.fetch=(u,o)=>{global.fetched.push(u);const p=path.join(SITE,u.replace(/\?.*$/,''));if(!fs.existsSync(p))return Promise.resolve({ok:false,status:404});const b=fs.readFileSync(p);
  return Promise.resolve({ok:true,status:200,arrayBuffer:()=>Promise.resolve(b.buffer.slice(b.byteOffset,b.byteOffset+b.length))});};
 global.DecompressionStream=function(){};global.Blob=function(parts){this.b=Buffer.from(parts[0])};
 global.Blob.prototype.stream=function(){const b=this.b;return{pipeThrough:()=>zlib.gunzipSync(b)}};global.Response=function(x){this.x=x};global.Response.prototype.text=function(){return Promise.resolve(this.x.toString())};
 delete require.cache[require.resolve(JS)];return require(JS);}
(async()=>{const r={};
 let A=setup('',false);r.offNull=(await A.load('US-ZZ',OLD))===null;r.offFetched=global.fetched.length;
 A=setup('?outlines=store',false);let pk=await A.load('US-ZZ',OLD);r.on=pk&&pk.source;r.refs=pk?[...new Set(pk.features.map(f=>f.properties.ref))]:[];
 r.oldKept=pk?pk.features.filter(f=>f.properties.old).map(f=>f.properties.ref):[];r.remember=global.localStorage.getItem('kpcOutlineStore');
 r.versioned=global.fetched.filter(u=>/geojson\.gz\?v=[0-9a-f]{12}$/.test(u)).length;r.credit=pk?A.creditLine(pk,pk.by['US-0010']):'';
 A=setup('?outlines=store',false);const pf=await A.load('US-ZF',{features:[]});const f20=pf&&pf.by['US-0020'];
 r.lvLow=f20?A.level(pf,f20,5,0.8):null;r.lvMid=f20?A.level(pf,f20,12,0.8):null;r.lvHigh=f20?A.level(pf,f20,18,0.8):null;
 r.mid=f20&&f20.properties.mid?!!(await A.mid('US-ZF','US-0020')):'nomid';
 const n0=global.fetched.length;const pieces=await A.fine('US-ZF','US-0020',BOX);r.fineN=pieces.length;r.fineFetched=global.fetched.slice(n0).filter(u=>/\/fine\//.test(u)).length;
 r.fineAll=Object.keys(JSON.parse(fs.readFileSync(path.join(SITE,'data/display/US-ZF/INDEX.json'))).fine['US-0020'].tiles).length;
 A=setup('?outlines=store',false);let pa=await A.load('US-ZA',OLD);r.multiOn=pa?pa.features.filter(f=>f.properties.ref==='US-0040'&&!f.properties.old).length:-1;
 A=setup('?outlines=store',false);const ip=path.join(SITE,'data/display/US-ZB/INDEX.json'),keep=fs.readFileSync(ip);const ix=JSON.parse(keep);ix.gen='000000000000';fs.writeFileSync(ip,JSON.stringify(ix));
 pa=await A.load('US-ZA',OLD);r.multiGen=pa?pa.features.filter(f=>f.properties.ref==='US-0040').map(f=>!!f.properties.old):null;fs.writeFileSync(ip,keep);
 A=setup('?outlines=old',true);r.oldParam=(await A.load('US-ZZ',OLD))===null;r.forgot=global.localStorage.getItem('kpcOutlineStore');
 A=setup('',true);r.preview=(await A.load('US-ZY',OLD))===null;
 A=setup('',true);r.missing=(await A.load('US-QQ',OLD))===null;
 const p2=path.join(SITE,'data/display/US-ZZ/US-ZZ.geojson.gz'),k2=fs.readFileSync(p2);fs.writeFileSync(p2,zlib.gzipSync(Buffer.from('{"kpc":{"format":"kpc-display-2","area":"US-ZZ","part":[1,2]},"features":[]}')));
 A=setup('',true);r.badPart=(await A.load('US-ZZ',OLD))===null;fs.writeFileSync(p2,k2);
 r.badArea=setup('?outlines=store',false).wanted('../x')===false;
 console.log(JSON.stringify(r));})().catch(e=>{console.log(JSON.stringify({error:String(e&&e.stack||e)}));});
'''
        sp = tmp / 'loader_test.js'; sp.write_text(script)
        env = {k: v for k, v in os.environ.items() if 'proxy' not in k.lower()}
        res = subprocess.run([node, str(sp), str(site), str(js), json.dumps(old), json.dumps(fine_box)], capture_output=True, text=True, timeout=120, env=env)
        try: r = json.loads(res.stdout.strip().splitlines()[-1])
        except Exception: r = {'error': res.stdout + res.stderr}
        if r.get('error'): print('   ', r['error'][:600])
        check('loader: switch off (no ?outlines, no toggle, empty go-live list) = null and NOTHING is fetched', r.get('offNull') is True and r.get('offFetched') == 0)
        check('loader: ?outlines=store draws the display copy and is remembered in this browser', r.get('on') == 'store' and r.get('remember') == '1')
        check("loader: today's outline is kept for every park the display copy leaves out; pin rows stay out",
              sorted(r.get('oldKept') or []) == ['US-0003', 'US-0040', 'US-0099'] and 'US-0098' not in (r.get('refs') or []) and 'US-0001' in (r.get('refs') or []))
        check('loader: every part is asked for with its own ?v=<sha12> (cache-friendly)', (r.get('versioned') or 0) >= 1)
        check('loader: the popup credit line names the agency from the index and says to check the official map',
              'County Parks' in (r.get('credit') or '') and 'official map' in (r.get('credit') or ''))
        check(f"loader: levels by zoom: overview zoomed out, middle up to zoom 13, fine pieces from zoom 14 ({r.get('lvLow')}/{r.get('lvMid')}/{r.get('lvHigh')})",
              r.get('lvLow') == 'overview' and r.get('lvMid') == 'mid' and r.get('lvHigh') == 'fine')
        check('loader: the middle file loads', r.get('mid') is True)
        check(f"loader: FINE pieces: only the pieces the screen touches are fetched ({r.get('fineN')} of {r.get('fineAll')})",
              (r.get('fineN') or 0) >= 1 and r.get('fineFetched') == r.get('fineN') and r.get('fineN') < (r.get('fineAll') or 0))
        check('loader: a park across two states is drawn new when both states are on and from the same build', (r.get('multiOn') or 0) >= 1)
        check("loader: ...and stays on today's outline when the other state's index is from another build", r.get('multiGen') == [True])
        check('loader: ?outlines=old switches it off again and forgets the toggle', r.get('oldParam') is True and r.get('forgot') is None)
        check('loader: a PRIVATE PREVIEW copy is never drawn', r.get('preview') is True)
        check("loader: no display copy for an area = null (today's outline)", r.get('missing') is True)
        check('loader: a part of another build = null for the whole area (never half an area)', r.get('badPart') is True)
        check('loader: an area name that is not an area is refused', r.get('badArea') is True)
        src = js.read_text(encoding='utf-8')
        check('loader: the go-live list ships empty (LIVE_AREAS = [])', 'var LIVE_AREAS = [];' in src)
        pages = [p.name for p in ROOT.glob('*.html') if 'kpc-outline-display.js' in p.read_text(encoding='utf-8', errors='replace')]
        check('loader: no page includes kpc-outline-display.js yet (nothing changes for the public)', pages == [])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})')
sys.exit(1 if FAILS else 0)
