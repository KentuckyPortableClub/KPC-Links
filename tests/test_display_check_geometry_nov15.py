#!/usr/bin/env python3
"""check --public refuses a display copy with bad geometry (KPC owner, 2026-11-15, grade fix): a feature with geometry null, a
null or text coordinate (lines too), a wrong geometry type, an empty geometry, truncated JSON in a part, a broken middle file or
fine piece. So such a file cannot reach the site (the publish script and the Pages step both run check --public).
SYNTHETIC only: a made-up store near 0 N 0 E in a temporary folder. No network. Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import contextlib, gzip, hashlib, io, json, math, pathlib, shutil, socket, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))


def _no_net(*a, **k): raise OSError('network blocked in this test')


socket.socket.connect = _no_net
socket.create_connection = _no_net
import kpc_display_copy as K  # noqa: E402
from display_copy_fixture import circle, record, park, write_store, line_record, wiggle_line  # noqa: E402

FAILS = []


def check(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok: FAILS.append(name)


A = 'US-ZZ'
tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-geocheck-'))
try:
    rough = [(round(0.1 + i * 0.00002, 6), round(0.8 + 0.0003 * math.sin(i / 7) + 0.00001 * math.sin(i * 1.7), 6)) for i in range(6000)]
    ring = list(reversed(rough + [(round(0.1 + 5999 * 0.00002, 6), 0.81), (0.1, 0.81)] + [rough[0]]))
    st = tmp / 'store'
    write_store(st, A, [park('US-0501', [record('a1', 'lay1', [circle(0.1, 0.1, 0.01, 200)])]),
                        park('US-0502', [line_record('t1', 'lay1', [wiggle_line(0.2, 0.1, 0.23, 80)])]),
                        park('US-0503', [record('r1', 'lay1', [ring])])])
    empty = tmp / 'rel'; (empty / 'outlines').mkdir(parents=True)
    good = tmp / 'good'
    K.build(st, [A], good, log=lambda *a: None, released=empty, cap=200, mid_cap=500, piece_cap=4000)
    check('the made-up display copy passes check --public as built', K.check(good, A, public=True) == [])
    idx0 = json.loads((good / A / 'INDEX.json').read_text(encoding='utf-8'))
    check('...and it has a middle file and fine pieces to break', bool(idx0['mid']) and bool(idx0['fine']))

    def variant(name, edit_part=None, raw_part=None, edit_file=None):
        """a copy of the good output with one change; INDEX sha12 / sizes put right so only the geometry is wrong"""
        d = tmp / name; shutil.copytree(good, d)
        ix = json.loads((d / A / 'INDEX.json').read_text(encoding='utf-8'))
        if edit_part or raw_part is not None:
            pn = ix['parts'][0][0]; doc = json.loads(gzip.decompress((d / A / pn).read_bytes()))
            if edit_part: edit_part(doc)
            b = gzip.compress(raw_part(doc) if raw_part else json.dumps(doc).encode(), 9, mtime=0)
            (d / A / pn).write_bytes(b); ix['parts'][0][1] = hashlib.sha256(b).hexdigest()[:12]; ix['parts'][0][3] = len(b)
        if edit_file:
            rel, fn = edit_file; q = d / A / rel
            b = fn(q.read_bytes()); q.write_bytes(b)
            sha = hashlib.sha256(b).hexdigest()[:12]
            if rel.startswith('mid/'):
                ref = rel[4:-11]; ix['mid'][ref][1] = sha; ix['mid'][ref][3] = len(b)
            else:
                _, ref, t = rel.split('/'); ix['fine'][ref]['tiles'][t[:-11]] = [sha, len(b)]
        (d / A / 'INDEX.json').write_text(json.dumps(ix, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        return d

    def of(doc, ref, role=None):
        return next(f for f in doc['features'] if f['properties']['ref'] == ref and (role is None or f['properties'].get('role') == role))

    def null_geo(doc): of(doc, 'US-0501')['geometry'] = None
    def null_xy(doc): of(doc, 'US-0502', 'line')['geometry']['coordinates'][0][3] = [None, 0.1]
    def text_xy(doc): of(doc, 'US-0501')['geometry']['coordinates'][0][0][2] = ['0.1', '0.1']
    def nan_xy(doc): of(doc, 'US-0501')['geometry']['coordinates'][0][0][2] = [float('nan'), 0.1]
    def wrong_type(doc): of(doc, 'US-0501')['geometry'] = {'type': 'Point', 'coordinates': [0.1, 0.1]}
    def line_as_poly(doc): of(doc, 'US-0502', 'line')['geometry']['type'] = 'MultiPolygon'
    def empty_geo(doc): of(doc, 'US-0501')['geometry']['coordinates'] = []
    def out_of_range(doc): of(doc, 'US-0501')['geometry']['coordinates'][0][0][2] = [0.1, 95.0]
    def no_props(doc): doc['features'][0]['properties'] = None
    cases = {'geometry null': null_geo, 'a null coordinate in a line': null_xy, 'a coordinate given as text': text_xy,
             'a NaN coordinate': nan_xy, 'a wrong geometry type (Point)': wrong_type, 'a line given as a polygon type': line_as_poly,
             'an empty geometry': empty_geo, 'a latitude over 90': out_of_range, 'a feature with no properties': no_props}
    for name, fn in cases.items():
        d = variant('v-' + fn.__name__, edit_part=fn)
        pr = K.check(d, A, public=True)
        check(f'check --public refuses {name} ({pr[:1]})', bool(pr))
    d = variant('v-trunc', raw_part=lambda doc: json.dumps(doc).encode()[:5000])
    pr = K.check(d, A, public=True)
    check(f'check --public refuses truncated JSON in a part, as a problem, not a crash ({pr[:1]})', any('unreadable' in p for p in pr))
    mid_rel = idx0['mid']['US-0503'][0]
    d = variant('v-mid', edit_file=(mid_rel, lambda b: gzip.compress(json.dumps(dict(json.loads(gzip.decompress(b)), features=[
        {'type': 'Feature', 'properties': {'ref': 'US-0503'}, 'geometry': {'type': 'MultiLineString', 'coordinates': [[[0.1, None], [0.2, 0.8]]]}}])).encode(), 9, mtime=0)))
    check('check --public refuses a middle file with a null coordinate', any(p.startswith('mid US-0503') for p in K.check(d, A, public=True)))
    t0 = sorted(idx0['fine']['US-0503']['tiles'])[0]
    d = variant('v-fine', edit_file=(f'fine/US-0503/{t0}.geojson.gz', lambda b: b[:len(b) // 2]))
    check('check --public refuses a broken fine piece', any(p.startswith('fine US-0503') for p in K.check(d, A, public=True)))
    with contextlib.redirect_stdout(io.StringIO()) as out:
        rc = K.main(['check', '--out', str(tmp / 'v-null_geo'), '--area', A, '--public'])
    check('the command line check exits 1 on bad geometry', rc == 1 and 'FAIL' in out.getvalue())
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})')
sys.exit(1 if FAILS else 0)
