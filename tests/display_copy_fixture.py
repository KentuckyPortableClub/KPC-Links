"""Synthetic outline stores for the display-copy tests (KPC owner, 2026-11-14). Made-up shapes near 0 N 0 E, store format 1, index
in the shape store tool full 3 (final) writes: store_format_version kpc-outline-store-index/3, licence_classes, file checksums,
per park record_meta {key: the 11 licence fields} mirrored in each record, park_publishable.
Not a test itself (the suite runs tests/test_*.py only)."""
import gzip, hashlib, io, json, math, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import kpc_display_copy as K  # noqa: E402

VERIFIED_WHY = 'verified-layers.csv (read 2026-11-14: https://example.invalid/terms)'


def enc(ring):
    out, px, py = [], 0, 0
    for i, (x, y) in enumerate(ring):
        xi, yi = int(round(x * 1e6)), int(round(y * 1e6))
        out += [xi, yi] if i == 0 else [xi - px, yi - py]
        px, py = xi, yi
    return out


def jit(i, seed, amp):
    """deterministic jitter in [-amp, amp] (no random module: the same shapes on every machine)"""
    v = math.sin(i * 12.9898 + seed * 78.233) * 43758.5453
    return (v - math.floor(v) - 0.5) * 2 * amp


def circle(cx, cy, r_deg, n, wobble=0.0, clockwise=True, phase=0.0, jitter=0.0):
    """a closed wiggly ring; jitter (degrees) makes it rough like a real 2 m line"""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n * (-1 if clockwise else 1)
        rr = r_deg * (1 + wobble * math.sin(7 * a + phase) + wobble * 0.5 * math.sin(23 * a)) + (jit(i, phase, jitter) if jitter else 0.0)
        pts.append((round(cx + rr * math.cos(a), 6), round(cy + rr * math.sin(a), 6)))
    pts.append(pts[0])
    return pts


def square(x0, y0, x1, y1, n_side=20, clockwise=True):
    """a square ring with n_side points per side (clockwise = an outer ring in the store's convention)"""
    pts = [(x0 + (x1 - x0) * i / n_side, y1) for i in range(n_side)] + [(x1, y1 - (y1 - y0) * i / n_side) for i in range(n_side)]
    pts += [(x1 - (x1 - x0) * i / n_side, y0) for i in range(n_side)] + [(x0, y0 + (y1 - y0) * i / n_side) for i in range(n_side)]
    pts = [(round(x, 6), round(y, 6)) for x, y in pts]
    if not clockwise: pts = pts[::-1]
    return pts + [pts[0]]


def record(key, layer, rings, cls='OPEN', credit=None, publishable=True, why=VERIFIED_WHY, basis='verified-row',
           url='https://example.invalid/arcgis/rest/services/x/MapServer/0', **extra):
    er = [enc(r) for r in rings]
    cr = credit if credit is not None else 'Test Agency ' + layer
    rec = {'key': key, 'layer': layer, 'record_id': key, 'layer_url': url + '/query', 'agency_label': 'Test Agency ' + layer,
           'record_name': key, 'source': 'live', 'rings': er, 'points': sum(len(r) for r in rings),
           'sha256': K.geometry_sha256(er), 'q': 6, 'use': True,
           'publishable': publishable, 'licence_class': cls, 'credit': cr, 'publish_why': why,
           'publish_basis': basis if publishable is True else 'none',
           'publish_basis_detail': {'evidence_url': 'https://example.invalid/terms', 'date_read': '2026-11-14'} if publishable is True else {},
           'credit_line': cr, 'source_layer': layer, 'source_url': url, 'terms_text_sha256': '', 'terms_text_file': '',
           'wdpa_derived': False, 'private_reason': '' if publishable is True else 'no licence recorded by a person yet'}
    rec.update(extra)
    return rec


def park(ref, recs, name=None):
    return {'ref': ref, 'name': name or ('Test Park ' + ref), 'grade': 'official', 'circle': False, 'pin': None, 'records': recs}


def _merge(e, over):
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(e.get(k), dict):
            for k2, v2 in v.items():
                if isinstance(v2, dict) and isinstance(e[k].get(k2), dict): e[k][k2] = dict(e[k][k2], **v2)
                else: e[k][k2] = v2
        else: e[k] = v


def write_store(d, area, parks, fmt='kpc-outline-store-index/3', index_override=None, layers=None, maps=True, classes=None, top=None):
    """One area store + index-<AREA>.json. index_override: {ref: {field: value}} merged over the index entry (two levels deep, so
    {'record_meta': {'r1': {'publishable': False}}} changes one field) to make the index disagree with the store. maps=False: an
    index with no record_meta (an older tool). top: fields written over the top of the index."""
    d = pathlib.Path(d); d.mkdir(parents=True, exist_ok=True)
    fname = f'{area}.kpcstore.json.gz'
    buf, idx = io.BytesIO(), {}
    buf.write(gzip.compress(json.dumps({'kpcstore': 1, 'area': area})[:-1].encode() + b',"parks":[\n', 9, mtime=0))
    for i, p in enumerate(parks):
        m = gzip.compress(((',\n' if i else '') + json.dumps(p, separators=(',', ':'))).encode(), 9, mtime=0)
        e = {'file': fname, 'o': buf.tell(), 'n': len(m), 'grade': p['grade'], 'circle': False, 'records': [r['key'] for r in p['records']],
             'points': sum(r['points'] for r in p['records']), 'fp': hashlib.sha256('|'.join(r['sha256'] for r in p['records']).encode()).hexdigest()}
        if maps:
            e['record_meta'] = {r['key']: {k: r.get(k) for k in K.META_KEYS} for r in p['records']}
            e['park_publishable'] = all(r.get('publishable') is True for r in p['records'])
        _merge(e, (index_override or {}).get(p['ref']) or {})
        idx[p['ref']] = e
        buf.write(m)
    buf.write(gzip.compress(b']}\n', 9, mtime=0))
    (d / fname).write_bytes(buf.getvalue())
    doc = {'format': 1, 'store_format_version': fmt, 'licence_classes': sorted(classes if classes is not None else K.LICENCE_CLASSES),
           'area': area, 'tool': 'kpc-outline-store full 3 (test)',
           'files': {fname: {'sha256': hashlib.sha256(buf.getvalue()).hexdigest(), 'bytes': len(buf.getvalue())}}, 'parks': idx}
    if fmt is None: del doc['store_format_version']
    if layers is not None: doc['layers'] = layers
    doc.update(top or {})
    (d / f'index-{area}.json').write_text(json.dumps(doc))
    return d / fname


def corridor(x0, x1, ymid, half_w, step_deg, split_x):
    """A wiggly corridor from x0 to x1, cut at split_x into two clockwise rings that share the cut edge exactly (same points)."""
    xs = [x0 + i * step_deg for i in range(int((x1 - x0) / step_deg) + 1)]
    J = 0.0000135   # about 1.5 m of roughness, like a real 2 m line
    top = [(round(x, 6), round(ymid + half_w + 0.0006 * math.sin(x * 900) + 0.0002 * math.sin(x * 7000) + jit(i, 1, J), 6)) for i, x in enumerate(xs)]
    bot = [(round(x, 6), round(ymid - half_w + 0.0006 * math.sin(x * 800 + 1) + 0.0002 * math.sin(x * 6100) + jit(i, 2, J), 6)) for i, x in enumerate(xs)]
    cut_top = (split_x, round(ymid + half_w + 0.0006 * math.sin(split_x * 900) + 0.0002 * math.sin(split_x * 7000), 6))
    cut_bot = (split_x, round(ymid - half_w + 0.0006 * math.sin(split_x * 800 + 1) + 0.0002 * math.sin(split_x * 6100), 6))
    cut = [(split_x, round(cut_bot[1] + (cut_top[1] - cut_bot[1]) * k / 40, 6)) for k in range(41)]   # bottom -> top
    lt = [p for p in top if p[0] < split_x] + [cut_top]; lb = [p for p in bot if p[0] < split_x] + [cut_bot]
    rt = [cut_top] + [p for p in top if p[0] > split_x]; rb = [cut_bot] + [p for p in bot if p[0] > split_x]
    left = lt + list(reversed(cut))[1:-1] + list(reversed(lb)); left.append(left[0])
    right_ring = rt + list(reversed(rb)) + cut[1:-1]; right_ring.append(right_ring[0])
    return left, right_ring


def huge_two_area_stores(d, n_tracts=330, tract_pts=1000):
    """US-ZA (x < 1.0) and US-ZB (x > 1.0): one park SYN-HUGE with a 180 km corridor cut at the state line, n_tracts rough
    tracts and one record stored in both areas. About 504,000 points."""
    left, right = corridor(0.2, 1.8, 0.3, 0.002, 0.0000185, 1.0)
    za, zb = [record('cor-w', 'synst', [left], credit='Synthetic State Lands')], [record('cor-e', 'synst', [right], credit='Synthetic State Lands')]
    for k in range(n_tracts):
        cx = 0.21 + 1.58 * (k + 0.5) / n_tracts
        cy = 0.3 + (0.012 if k % 2 else -0.012)
        r = record(f't{k}', 'synst', [circle(round(cx, 6), cy, 0.0033, tract_pts, wobble=0.04, phase=k, jitter=0.0000135)], credit='Synthetic State Lands')
        (za if cx < 1.0 else zb).append(r)
    both = record('both1', 'synst', [circle(1.0, 0.34, 0.002, 400, wobble=0.05)], credit='Synthetic State Lands')
    za.append(both); zb.append(dict(both))
    write_store(d, 'US-ZA', [park('SYN-HUGE', za, 'Synthetic Long Corridor Forest')])
    write_store(d, 'US-ZB', [park('SYN-HUGE', zb, 'Synthetic Long Corridor Forest')])
    return sum(r['points'] for r in za) + sum(r['points'] for r in zb) - both['points']
