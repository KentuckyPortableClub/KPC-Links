#!/usr/bin/env python3
"""A HUGE park across two states (KPC owner, 2026-11-14: "what if it is a huge park covering states: is that enough?").

SYNTHETIC: tests/display_copy_fixture.py writes two area stores (US-ZA west of x = 1.0, US-ZB east of it) holding one park of
503,789 points: a 180 km rough corridor cut at the state line into one record per state (the two records share the cut edge
exactly, as state layers do), 330 rough tracts of about 1,000 points, and one tract held in both states' stores.
The builder runs in a child process so its peak memory can be read. Checks: memory, time, every file under its cap, the three
levels and their errors, no line on the state line at any level, the shared tract drawn once, and how much a phone loads for
one street-level screen anywhere on the park. No network (sockets blocked), nothing written outside a temporary folder.
Prints PASS / FAIL lines and ends ALL PASS or SOME FAILED."""
import gzip, json, math, os, pathlib, resource, shutil, socket, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))


def _no_net(*a, **k): raise OSError('network blocked in this test')


socket.socket.connect = _no_net
socket.create_connection = _no_net
import kpc_display_copy as K  # noqa: E402
import display_copy_fixture as F  # noqa: E402

MEM_LIMIT_MB = 450          # measured about 225 MB on Python 3.13 (Linux); the limit leaves room for other Pythons
SCREEN_LIMIT = 512_000      # bytes of FINE pieces one street-level screen may touch
FAILS = []


def check(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok: FAILS.append(name)


tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-display-huge-'))
try:
    n = F.huge_two_area_stores(tmp / 'store')
    check(f'the synthetic park has at least 500,000 points ({n:,})', n >= 500_000)
    code = ('import sys, json; sys.path.insert(0, sys.argv[1]); import kpc_display_copy as K; '
            'r = K.build(sys.argv[2], ["US-ZA", "US-ZB"], sys.argv[3], log=lambda *a: None); '
            'json.dump(r, open(sys.argv[4], "w"))')
    env = {k: v for k, v in os.environ.items() if 'proxy' not in k.lower()}
    t0 = time.time()
    p = subprocess.run([sys.executable, '-c', code, str(ROOT / 'tools'), str(tmp / 'store'), str(tmp / 'out'), str(tmp / 'rep.json')],
                       capture_output=True, text=True, timeout=900, env=env)
    secs = time.time() - t0
    peak_mb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / (1024 if sys.platform != 'darwin' else 1024 * 1024)
    if p.returncode: print(p.stdout[-800:], p.stderr[-1500:])
    check(f'the build finishes ({secs:.1f} s)', p.returncode == 0)
    check(f'peak memory of the build stays small ({peak_mb:.0f} MB, limit {MEM_LIMIT_MB} MB)', peak_mb < MEM_LIMIT_MB)
    rep = json.loads((tmp / 'rep.json').read_text()) if p.returncode == 0 else {'rows': [{}], 'per_area': {}}
    row = rep['rows'][0] if rep['rows'] else {}
    print('   ', {k: row.get(k) for k in ('store_points', 'points', 'detail_m', 'worst_m', 'mid_points', 'mid_detail_m', 'mid_worst_m', 'mid_bytes',
                                       'fine_points', 'fine_worst_m', 'fine_t', 'fine_pieces', 'fine_bytes', 'fine_piece_max', 'seam_vertices')})
    check('both states pass the public check (every file under its cap, sha as listed, nothing unlisted)',
          all(K.check(tmp / 'out', a, public=True) == [] for a in ('US-ZA', 'US-ZB')))
    check(f"OVERVIEW at most 3,000 points ({row.get('points')}) and its error is measured ({row.get('worst_m')} m at a {row.get('detail_m')} m step)",
          (row.get('points') or 1e9) <= K.CAP and row.get('worst_m') is not None)
    check(f"MIDDLE at most 30,000 points ({row.get('mid_points')}), each state's file under 1 MB, finer than the overview",
          (row.get('mid_points') or 1e9) <= K.MID_CAP and all(v[3] < 1_000_000 for a in ('US-ZA', 'US-ZB')
          for v in json.loads((tmp / 'out' / a / 'INDEX.json').read_text())['mid'].values()) and row.get('mid_worst_m', 1e9) < row.get('worst_m', 0))
    check(f"FINE within 5 m of the store ({row.get('fine_worst_m')} m), every piece under {K.PIECE_CAP:,} B (largest {row.get('fine_piece_max')})",
          row.get('fine_worst_m') is not None and row['fine_worst_m'] <= 5.0 and row['fine_piece_max'] <= K.PIECE_CAP)
    # no line on the state line, at any level; the shared tract once
    on_line, segs, shared = 0, 0, 0
    for f in (tmp / 'out').rglob('*.geojson.gz'):
        for ft in json.loads(gzip.decompress(f.read_bytes()))['features']:
            if ft['properties'].get('role') == 'hit': continue
            if 'both1' in (ft['properties'].get('records') or []): shared += 1
            g = ft['geometry']
            for l in (g['coordinates'] if g['type'] == 'MultiLineString' else [r for q in g['coordinates'] for r in q]):
                for a, b in zip(l, l[1:]):
                    segs += 1
                    if a[0] == 1.0 and b[0] == 1.0: on_line += 1
    check(f'no drawn segment lies on the state line at any level ({on_line} of {segs:,})', segs > 0 and on_line == 0)
    check('the tract held in both states is drawn from one state only', shared == 1)
    # what one screen loads: 1280 x 800 px at zoom 14 (where fine pieces start) and 16 (street level), slid over the whole park
    def screen(z):
        lat = 0.3
        mpp = 156543.034 * math.cos(math.radians(lat)) / 2 ** z
        w, h = 1280 * mpp / (111320 * math.cos(math.radians(lat))), 800 * mpp / 110574
        worst, worst_n, typical = 0, 0, []
        for a in ('US-ZA', 'US-ZB'):
            fe = json.loads((tmp / 'out' / a / 'INDEX.json').read_text())['fine']['SYN-HUGE']
            T, tiles = fe['t'], fe['tiles']
            x = 0.2
            while x < 1.8:
                for y in (0.27, 0.285, 0.29, 0.3, 0.31):
                    keys = [f'{ix}_{iy}' for ix in range(math.floor((x - w / 2) / T), math.floor((x + w / 2) / T) + 1)
                            for iy in range(math.floor((y - h / 2) / T), math.floor((y + h / 2) / T) + 1)]
                    b = sum(tiles[k][1] for k in keys if k in tiles)
                    if b: typical.append(b)
                    if b > worst: worst, worst_n = b, sum(1 for k in keys if k in tiles)
                x += T / 4
        typical.sort()
        print(f'    one screen at zoom {z} ({w:.4f} x {h:.4f} degrees): fine pieces worst {worst:,} B in {worst_n} piece(s), '
              f'median {typical[len(typical) // 2] if typical else 0:,} B')
        return worst, worst_n
    w14, n14 = screen(14)
    worst, n16 = screen(16)
    check(f'one street-level screen (zoom 16) anywhere on the park loads at most {SCREEN_LIMIT:,} B of fine pieces ({worst:,} B)', 0 < worst <= SCREEN_LIMIT)
    check(f'one screen at zoom 14, where fine pieces start, touches at most {K.PIECE_CAP and 48} pieces ({n14}) and {w14:,} B', n14 <= 48)
    ov = sum(v[3] for a in ('US-ZA', 'US-ZB') for v in json.loads((tmp / 'out' / a / 'INDEX.json').read_text())['parts'])
    check(f'the overview of both states together is small ({ov:,} B for a 504,000-point park)', ov < 100_000)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})')
sys.exit(1 if FAILS else 0)
