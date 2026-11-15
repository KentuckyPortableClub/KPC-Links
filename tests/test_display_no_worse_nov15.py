#!/usr/bin/env python3
"""No worse than released (KPC owner, 2026-11-15): tools/kpc_display_copy.py keeps TODAY'S outline for a park whose store outline
would lose land against today's released outline (data/released/outlines/<AREA>.geojson.gz), and lists it in the private report.

Everything here is SYNTHETIC: made-up parks near 0 N 0 E in a temporary folder (tests/display_copy_fixture.py), a made-up released
folder beside them. No real outline, no network (sockets are blocked), no repo file written. Prints PASS / FAIL lines and ends
ALL PASS or SOME FAILED."""
import contextlib, gzip, io, json, pathlib, shutil, socket, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))


def _no_net(*a, **k): raise OSError('network blocked in this test')


socket.socket.connect = _no_net
socket.create_connection = _no_net
import kpc_display_copy as K  # noqa: E402
from display_copy_fixture import circle, square, record, park, write_store, line_record, wiggle_line  # noqa: E402

FAILS = []
NOLOG = lambda *a: None


def check(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok: FAILS.append(name)


def feat(ref, polys, g='official', detail=0.0001):
    """a released feature as today's files hold it: a (Multi)Polygon, GeoJSON lon/lat"""
    geo = {'type': 'Polygon', 'coordinates': [[list(p) for p in polys[0]]]} if len(polys) == 1 else \
          {'type': 'MultiPolygon', 'coordinates': [[[list(p) for p in r]] for r in polys]}
    return {'type': 'Feature', 'properties': {'ref': ref, 'name': 'Released ' + ref, 'g': g, 'detail': detail}, 'geometry': geo}


def write_released(d, area, feats, parts=1):
    o = pathlib.Path(d) / 'outlines'; o.mkdir(parents=True, exist_ok=True)
    n = max(1, parts); per = -(-len(feats) // n) if feats else 0
    for i in range(n):
        doc = {'type': 'FeatureCollection', 'kpc': {'area': area, 'format': 1}, 'features': feats[i * per:(i + 1) * per]}
        if n > 1: doc['kpc_part'] = [i + 1, n, 'tag1']
        name = f'{area}.geojson.gz' if i == 0 else f'{area}.p{i + 1}.geojson.gz'
        (o / name).write_bytes(gzip.compress(json.dumps(doc).encode(), 9, mtime=0))


def drawn_refs(out, area):
    idx = json.loads((out / area / 'INDEX.json').read_text(encoding='utf-8'))
    refs = set()
    for name, *_ in idx['parts']:
        for f in json.loads(gzip.decompress((out / area / name).read_bytes()))['features']: refs.add(f['properties']['ref'])
    return refs, idx


def ccw(r): return r[::-1]   # GeoJSON outer rings are counter-clockwise; the store's are clockwise


tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-noworse-test-'))
try:
    A = 'US-ZZ'
    same = circle(0.1, 0.1, 0.01, 240)
    parks = [
        park('US-0101', [record('a1', 'lay1', [same])]),                                    # the same land as released
        park('US-0102', [record('b1', 'lay1', [circle(0.2, 0.1, 0.005, 160)])]),            # half the radius of released: loses land
        park('US-0103', [record('c1', 'lay1', [circle(0.3, 0.1, 0.012, 200)])]),            # more land than released
        park('US-0104', [record('d1', 'lay1', [circle(0.4, 0.1, 0.01, 120)])]),             # not in the released file
        park('US-0105', [record('e1', 'lay1', [circle(0.5, 0.1, 0.004, 120)])]),            # released 'approximate' only
        park('US-0106', [record('f1', 'lay1', [circle(0.6, 0.1, 0.01, 200)])]),             # released shifted 15 m (simplified copy)
        park('US-0107', [record('g1', 'lay1', [circle(0.7, 0.1, 0.008, 160)])]),            # released has a second tract the store lacks
        park('US-0108', [line_record('h1', 'lay1', [wiggle_line(0.8, 0.1, 0.83, 60)])]),   # a line park; released has an area
    ]
    released = [
        feat('US-0101', [ccw(circle(0.1, 0.1, 0.01, 40))]),            # coarser, same land
        feat('US-0102', [ccw(circle(0.2, 0.1, 0.01, 40))]),
        feat('US-0103', [ccw(circle(0.3, 0.1, 0.01, 40))]),
        feat('US-0105', [ccw(circle(0.5, 0.1, 0.01, 40))], g='approximate'),
        feat('US-0106', [ccw([(x + 0.000135, y) for x, y in circle(0.6, 0.1, 0.01, 50)])]),
        feat('US-0107', [ccw(circle(0.7, 0.1, 0.008, 40)), ccw(circle(0.73, 0.1, 0.003, 30))]),
        feat('US-0108', [ccw(circle(0.815, 0.1, 0.003, 30))]),
        feat('US-0109', [ccw(circle(0.9, 0.1, 0.003, 30))]),            # not in the store at all
    ]
    st = tmp / 'store'; write_store(st, A, parks)
    rel = tmp / 'released'; write_released(rel, A, released)
    rep = K.build(st, [A], tmp / 'out', log=NOLOG, released=rel)
    refs, idx = drawn_refs(tmp / 'out', A)
    kept = set(rep['no_worse_kept_today'])
    check('same land as released (coarser released copy): drawn from the store', 'US-0101' in refs and 'US-0101' not in kept)
    check('a store outline with less land than released: keeps today\'s outline, listed in the report (no_worse_kept_today)',
          'US-0102' not in refs and 'US-0102' in kept and idx['fallback'].get('US-0102') == K.FALLBACK_CODE)
    check('its reason is in the private report only', 'no worse than released' in rep['fallback_reasons'].get('US-0102', '')
          and 'no worse' not in json.dumps(idx))
    check('a store outline with more land than released: drawn', 'US-0103' in refs and 'US-0103' not in kept)
    check('a park with no released outline: drawn, not checked', 'US-0104' in refs and
          not any(r['ref'] == 'US-0104' and 'no_worse' in r for r in rep['rows']))
    check('an approximate released outline is not compared', 'US-0105' in refs and 'US-0105' not in kept)
    check('a released copy 15 m off (its simplification): within the allowance, drawn', 'US-0106' in refs and 'US-0106' not in kept)
    check('released has a tract the store lacks: keeps today\'s outline, listed', 'US-0107' in kept and 'US-0107' not in refs)
    check('a line-only store park against a released AREA: keeps today\'s outline (a line has no land), listed', 'US-0108' in kept)
    check('the report counts the parks checked and lists every kept park', rep['no_worse_checked'] == 6 and kept == {'US-0102', 'US-0107', 'US-0108'})
    check('parks_drawn leaves the kept parks out', rep['parks_drawn'] == 5)
    check('the written copy still passes check --public', K.check(tmp / 'out', A, public=True) == [])
    row = [r for r in rep['rows'] if r['ref'] == 'US-0102'][0]
    check('the numbers (private): lost land about 3/4 of the released circle', row['no_worse']['worse'] and 2.2e6 < row['no_worse']['lost_m2'] < 3.2e6)

    # released in two parts: a park in part 2 is read and judged the same
    rel2 = tmp / 'released2'; write_released(rel2, A, released, parts=2)
    rep2 = K.build(st, [A], tmp / 'out2', log=NOLOG, released=rel2)
    check('released file in two parts (kpc_part): the same parks kept', set(rep2['no_worse_kept_today']) == kept)
    (rel2 / 'outlines' / f'{A}.p2.geojson.gz').unlink()
    try: K.build(st, [A], tmp / 'out3', log=NOLOG, released=rel2); check('a missing released part stops the build', False)
    except K.DisplayError as e: check('a missing released part stops the build (the check never passes on half a file)', 'missing' in str(e))
    (rel2 / 'outlines' / f'{A}.geojson.gz').write_bytes(b'\x1f\x8b not gzip')
    try: K.build(st, [A], tmp / 'out3', log=NOLOG, released=rel2); check('a broken released file stops the build', False)
    except K.DisplayError as e: check('a broken released file stops the build', 'unreadable' in str(e))
    try: K.build(st, [A], tmp / 'out4', log=NOLOG, released=tmp / 'no-such-folder'); check('a released folder that is not there stops the build', False)
    except K.DisplayError as e: check('a released folder that is not there stops the build (never "nothing to compare")', 'not a folder' in str(e))
    empty = tmp / 'released-empty'; (empty / 'outlines').mkdir(parents=True)
    rep5 = K.build(st, [A], tmp / 'out5', log=NOLOG, released=empty)
    check('an area with no released file: nothing to compare, every park drawn', rep5['no_worse_kept_today'] == [] and rep5['parks_drawn'] == 8)

    check('an area with no released file is listed in the report (never silent)', rep5['no_worse_areas_not_compared'] == [A]
          and rep['no_worse_areas_not_compared'] == [])

    # relative allowance (grade fix): small parks cannot shrink to nearly nothing inside the 30 m allowance; big parks keep the
    # distance allowance for today's simplified copy
    m = 1 / 111320.0
    sm = [park('US-0401', [record('s1', 'lay1', [circle(0.1, 0.3, 3 * m, 40)])]),       # released 33 m radius, store 3 m
          park('US-0402', [record('s2', 'lay1', [circle(0.2, 0.3, 31 * m, 60)])]),      # released 33 m, store 31 m
          park('US-0403', [record('s3', 'lay1', [circle(0.3, 0.3, 50 * m, 60)])]),      # released 67 m, store 50 m (25 % lost)
          park('US-0404', [record('l1', 'lay1', [square(0.4 + 10 * m, 0.3 + 10 * m, 0.42 - 10 * m, 0.32 - 10 * m, 40)])]),   # 2.2 km, 10 m inset
          park('US-0405', [record('l2', 'lay1', [square(0.5, 0.3, 0.52 - 300 * m, 0.32, 40)])]),                            # 2.2 km, a 300 m strip gone
          park('US-0406', [record('l3', 'lay1', [square(0.6 + 25 * m, 0.3, 0.62 + 25 * m, 0.32, 40)])])]                     # 2.2 km, shifted 25 m
    relsm = [feat('US-0401', [ccw(circle(0.1, 0.3, 33 * m, 40))]), feat('US-0402', [ccw(circle(0.2, 0.3, 33 * m, 40))]),
             feat('US-0403', [ccw(circle(0.3, 0.3, 67 * m, 40))]),
             feat('US-0404', [ccw(square(0.4, 0.3, 0.42, 0.32, 10))]), feat('US-0405', [ccw(square(0.5, 0.3, 0.52, 0.32, 10))]),
             feat('US-0406', [ccw(square(0.6, 0.3, 0.62, 0.32, 10))])]
    st2 = tmp / 'store-sizes'; write_store(st2, A, sm)
    rel3 = tmp / 'released-sizes'; write_released(rel3, A, relsm)
    rs = K.build(st2, [A], tmp / 'out-sizes', log=NOLOG, released=rel3)
    ks = set(rs['no_worse_kept_today'])
    sh = {r['ref']: r['no_worse']['outside_share'] for r in rs['rows'] if 'no_worse' in r}
    check(f'small park: 33 m shrunk to 3 m keeps today\'s outline (share outside {sh.get("US-0401")})', 'US-0401' in ks)
    check(f'small park: 33 m vs 31 m is drawn (share outside {sh.get("US-0402")})', 'US-0402' not in ks)
    check(f'small park: 67 m vs 50 m (over the 20 % share) keeps today\'s outline ({sh.get("US-0403")})', 'US-0403' in ks)
    check(f'large park: a 10 m inset is drawn ({sh.get("US-0404")})', 'US-0404' not in ks)
    check(f'large park: a 300 m strip gone keeps today\'s outline ({sh.get("US-0405")})', 'US-0405' in ks)
    check(f'large park: shifted 25 m (within the allowance, a small share) is drawn ({sh.get("US-0406")})', 'US-0406' not in ks)

    # the default is this repository's data/released; the command line lists the kept parks
    check('build() and the command line default to the repository\'s data/released', K.RELEASED_DEFAULT == ROOT / 'data' / 'released'
          and K.build.__defaults__[-1] == K.RELEASED_DEFAULT)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = K.main(['build', '--store', str(st), '--area', A, '--out', str(tmp / 'out6'), '--released', str(rel)])
    with contextlib.redirect_stdout(io.StringIO()) as b2:
        K.main(['build', '--store', str(st), '--area', A, '--out', str(tmp / 'out6b'), '--released', str(empty)])
    check('command line: an area with no released file is named', 'no-worse check not run) for: US-ZZ' in b2.getvalue())
    check('command line: exit 0 and the kept parks listed', rc == 0 and 'US-0102' in buf.getvalue() and 'released outline' in buf.getvalue())
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = K.main(['build', '--store', str(st), '--area', A, '--out', str(tmp / 'out7'), '--released', str(tmp / 'nope')])
    check('command line: a wrong --released folder stops (exit 1)', rc == 1 and 'STOP' in buf.getvalue())
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})')
sys.exit(1 if FAILS else 0)
