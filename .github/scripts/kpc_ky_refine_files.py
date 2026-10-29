#!/usr/bin/env python3
"""REFINE THE KENTUCKY OUTLINE FILES (chat 2, Oct 29 2026; Brandon 7:07 AM 'yes send it'). The outline accuracy probe found the
ky-*.geojson files keep their corners ON the real edge but cut corners by ~8 m (95%), over the 5 m goal. Each feature of the
four files that come from Kentucky's own state GIS is read again by its name (all live pieces with that name near the old
shape) at ~5 m (server thinning 0.00005 deg, 6 decimals) and written back with the same properties. A feature whose read
fails or whose area moves more than 25% keeps its old shape (listed). Writes ky-refine-report.json. Never fails."""
import json, math, os, re, sys, time, urllib.parse, urllib.request

UA = {'User-Agent': 'KPC park-map bot (kentuckyportableclub.github.io; ham radio club)'}
KYGIS = 'https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/'
FILES = {'ky-hunting-areas.geojson': (KYGIS + 'Ky_Public_Hunting_Areas_WGS84WM/MapServer/1/query', 'AREANAME'),
         'ky-state-parks.geojson': (KYGIS + 'Ky_State_Parks_Features_WGS84WM/MapServer/8/query', 'PUBLIC_NAM'),
         'ky-nature-preserves.geojson': (KYGIS + 'Ky_KNP_State_Nature_Preserves_WGS84WM/MapServer/0/query', 'MANAME'),
         'ky-natural-areas.geojson': (KYGIS + 'Ky_KNP_Natural_Areas_WGS84WM/MapServer/0/query', 'MANAME')}
LAST = [0.0]


def get(url, params):
    for k in range(3):
        w = 1.5 - (time.time() - LAST[0])
        if w > 0: time.sleep(w)
        try:
            LAST[0] = time.time()
            with urllib.request.urlopen(urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(), headers=UA), timeout=120) as r:
                j = json.loads(r.read().decode('utf-8', 'replace'))
            if 'error' in j: raise RuntimeError(str(j['error'])[:100])
            return j
        except Exception:  # noqa: BLE001
            if k == 2: return None
            time.sleep(6 * (k + 1))


def rings_gj(g):
    t, c = (g or {}).get('type'), (g or {}).get('coordinates') or []
    return [r for r in c] if t == 'Polygon' else [r for p in c for r in p] if t == 'MultiPolygon' else []


def area(rings):
    if not rings: return 0
    la = sum(p[1] for p in rings[0]) / len(rings[0]); kx, ky = 111320 * math.cos(math.radians(la)), 110574
    def sa(r): return sum((a[0] * kx) * (b[1] * ky) - (b[0] * kx) * (a[1] * ky) for a, b in zip(r, r[1:] + r[:1])) / 2
    return abs(sum(sa(r) for r in rings)) / 4046.86   # signed sum: holes subtract


def polys(rings):
    def sa(r): return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(r, r[1:] + r[:1])) / 2
    def inside(pt, r):
        x, y = pt; c = False; j = len(r) - 1
        for i in range(len(r)):
            if (r[i][1] > y) != (r[j][1] > y) and x < (r[j][0] - r[i][0]) * (y - r[i][1]) / ((r[j][1] - r[i][1]) or 1e-12) + r[i][0]: c = not c
            j = i
        return c
    outs = [[r] for r in rings if sa(r) < 0]
    if not outs: return [[r] for r in rings]
    for r in rings:
        if sa(r) >= 0:
            h = next((o for o in outs if inside(r[0], o[0])), None)
            (h.append(r) if h else outs.append([r]))
    return outs


def main():
    rep = {'date': time.strftime('%Y-%m-%d'), 'files': {}}
    for fn, (url, fld) in FILES.items():
        if not os.path.exists(fn): continue
        d = json.load(open(fn)); done = kept = 0; why = []
        b0 = os.path.getsize(fn)
        cnt = {}
        for f in d['features']: n_ = (f.get('properties') or {}).get('NAME'); cnt[n_] = cnt.get(n_, 0) + 1
        for f in d['features']:
            nm = (f.get('properties') or {}).get('NAME'); old = rings_gj(f.get('geometry'))
            if not nm or not old: continue
            if cnt.get(nm, 0) > 1: kept += 1; why.append(f'{nm}: {cnt[nm]} features share this name, kept'); continue
            xs = [p[0] for r in old for p in r]; ys = [p[1] for r in old for p in r]
            q = str(nm).replace("'", "''")
            j = get(url, {'where': f"{fld} = '{q}'", 'geometry': f'{min(xs) - .02},{min(ys) - .02},{max(xs) + .02},{max(ys) + .02}', 'geometryType': 'esriGeometryEnvelope',
                          'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects', 'outFields': fld, 'returnGeometry': 'true', 'outSR': 4326,
                          'maxAllowableOffset': 0.00005, 'geometryPrecision': 6, 'f': 'json'})
            rings = [r for ft in (j or {}).get('features') or [] for r in ((ft.get('geometry') or {}).get('rings') or []) if len(r) >= 4]
            if not rings:   # the state layer may spell it differently ('John James Audubon SP'): the name's main words, near the old shape
                core = [w for w in re.sub(r"[^A-Za-z ]", ' ', str(nm)).split() if w.lower() not in ('state', 'park', 'resort', 'historic', 'site', 'the', 'and', 'of', 'nature', 'preserve', 'area')][:3]
                if core:
                    wh = ' AND '.join(f"UPPER({fld}) LIKE '%{w.upper()}%'" for w in core)
                    j = get(url, {'where': wh, 'geometry': f'{min(xs) - .02},{min(ys) - .02},{max(xs) + .02},{max(ys) + .02}', 'geometryType': 'esriGeometryEnvelope',
                                  'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects', 'outFields': fld, 'returnGeometry': 'true', 'outSR': 4326,
                                  'maxAllowableOffset': 0.00005, 'geometryPrecision': 6, 'f': 'json'})
                    names = {(ft.get('attributes') or {}).get(fld) for ft in (j or {}).get('features') or []}
                    if len(names) == 1:
                        rings = [r for ft in (j or {}).get('features') or [] for r in ((ft.get('geometry') or {}).get('rings') or []) if len(r) >= 4]
            if not rings: kept += 1; why.append(f'{nm}: no live answer'); continue
            a0, a1 = area(old), area([[p for p in r] for r in rings])
            if a0 and abs(a1 - a0) / a0 > .25: kept += 1; why.append(f'{nm}: area {round(a0)} -> {round(a1)} ac, kept'); continue
            f['geometry'] = {'type': 'MultiPolygon', 'coordinates': polys(rings)}
            done += 1
        with open(fn, 'w') as fh: json.dump(d, fh, separators=(',', ':'))
        rep['files'][fn] = {'refined': done, 'kept': kept, 'kb_before': b0 // 1024, 'kb_after': os.path.getsize(fn) // 1024, 'kept_why': why[:20]}
        print(f"::notice title=KY files refined::{fn}: {done} refined, {kept} kept · {b0 // 1024} KB -> {os.path.getsize(fn) // 1024} KB · " + '; '.join(why[:4]), flush=True)
    json.dump(rep, open('ky-refine-report.json', 'w'), indent=1)


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=KY files refined::stopped: {str(e)[:200]}', flush=True)  # noqa: BLE001
    sys.exit(0)
