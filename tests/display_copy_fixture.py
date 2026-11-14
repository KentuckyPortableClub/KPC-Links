"""Synthetic outline stores for the display-copy tests (KPC owner, 2026-11-14). Made-up shapes near 0 N 0 E, store format 1.
Not a test itself (the suite runs tests/test_*.py only)."""
import gzip, hashlib, io, json, math, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import kpc_display_copy as K  # noqa: E402


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
    """a closed wiggly ring; jitter (degrees) makes it rough like a real 2 m line, so simplifying at 1 m keeps most points"""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n * (-1 if clockwise else 1)
        rr = r_deg * (1 + wobble * math.sin(7 * a + phase) + wobble * 0.5 * math.sin(23 * a)) + (jit(i, phase, jitter) if jitter else 0.0)
        pts.append((round(cx + rr * math.cos(a), 6), round(cy + rr * math.sin(a), 6)))
    pts.append(pts[0])
    return pts


def record(key, layer, rings, licence='OPEN; credit: Test Agency', url='https://example.invalid/arcgis/rest/services/x/MapServer/0',
           v2=None):
    er = [enc(r) for r in rings]
    rec = {'key': key, 'layer': layer, 'record_id': key, 'layer_url': url, 'agency_label': 'Test Agency ' + layer,
           'record_name': key, 'licence': licence, 'source': 'live', 'rings': er, 'points': sum(len(r) for r in rings),
           'sha256': K.geometry_sha256(er), 'q': 6, 'use': True}
    if v2: rec.update(v2)
    return rec


def park(ref, recs, name=None):
    return {'ref': ref, 'name': name or ('Test Park ' + ref), 'grade': 'official', 'circle': False, 'pin': None, 'records': recs}


def write_store(d, area, parks, index_licence=True, v2=False, extra=None):
    """One area store + index-<AREA>.json (v2=True: the full-2 index fields licence_class / credit / publishable per record)."""
    d = pathlib.Path(d); d.mkdir(parents=True, exist_ok=True)
    fname = f'{area}.kpcstore.json.gz'
    buf, idx = io.BytesIO(), {}
    buf.write(gzip.compress(json.dumps({'kpcstore': 1, 'area': area})[:-1].encode() + b',"parks":[\n', 9, mtime=0))
    for i, p in enumerate(parks):
        m = gzip.compress(((',\n' if i else '') + json.dumps(p, separators=(',', ':'))).encode(), 9, mtime=0)
        e = {'file': fname, 'o': buf.tell(), 'n': len(m), 'grade': p['grade'], 'circle': False, 'records': [r['key'] for r in p['records']],
             'points': sum(r['points'] for r in p['records']), 'fp': hashlib.sha256('|'.join(r['sha256'] for r in p['records']).encode()).hexdigest()}
        if index_licence: e['licence'] = {r['key']: (r.get('licence') or 'not recorded') for r in p['records']}
        if v2:
            e['licence_class'] = {r['key']: r.get('licence_class', 'NOT RECORDED') for r in p['records']}
            e['credit'] = {r['key']: r.get('credit', '') for r in p['records']}
            e['publishable'] = {r['key']: bool(r.get('publishable')) for r in p['records']}
        e.update((extra or {}).get(p['ref'], {}))
        idx[p['ref']] = e
        buf.write(m)
    buf.write(gzip.compress(b']}\n', 9, mtime=0))
    (d / fname).write_bytes(buf.getvalue())
    (d / f'index-{area}.json').write_text(json.dumps({'format': 1, 'area': area, 'files': {fname: {'sha256': hashlib.sha256(buf.getvalue()).hexdigest()}},
                                                      'parks': idx}))
    return d / fname


V2_OPEN = {'licence_class': 'OPEN', 'credit': 'Synthetic State Lands', 'publishable': True}


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
    # clockwise rings: along the top west -> east, down the east side, along the bottom east -> west, up the west side
    left = lt + list(reversed(cut))[1:-1] + list(reversed(lb)); left.append(left[0])
    right_ring = rt + list(reversed(rb)) + cut[1:-1]; right_ring.append(right_ring[0])
    return left, right_ring


def huge_two_area_stores(d, n_tracts=330, tract_pts=1000):
    """US-ZA (x < 1.0) and US-ZB (x > 1.0): one park SYN-HUGE with a 180 km corridor cut at the state line, n_tracts wiggly tracts
    and one record stored in both areas. About 510,000 points."""
    left, right = corridor(0.2, 1.8, 0.3, 0.002, 0.0000185, 1.0)
    za, zb = [record('cor-w', 'synst', [left], v2=V2_OPEN)], [record('cor-e', 'synst', [right], v2=V2_OPEN)]
    for k in range(n_tracts):
        cx = 0.21 + 1.58 * (k + 0.5) / n_tracts
        cy = 0.3 + (0.012 if k % 2 else -0.012)
        r = record(f't{k}', 'synst', [circle(round(cx, 6), cy, 0.0033, tract_pts, wobble=0.04, phase=k, jitter=0.0000135)], v2=V2_OPEN)
        (za if cx < 1.0 else zb).append(r)
    both = record('both1', 'synst', [circle(1.0, 0.34, 0.002, 400, wobble=0.05)], v2=V2_OPEN)   # straddles the line, in both stores
    za.append(both); zb.append(dict(both))
    write_store(d, 'US-ZA', [park('SYN-HUGE', za, 'Synthetic Long Corridor Forest')], v2=True)
    write_store(d, 'US-ZB', [park('SYN-HUGE', zb, 'Synthetic Long Corridor Forest')], v2=True)
    return sum(r['points'] for r in za) + sum(r['points'] for r in zb) - both['points']
