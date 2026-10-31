#!/usr/bin/env python3
"""REFINE THE SAVED CANADA OUTLINES (chat 2, Oct 29 2026; Brandon 7:07 AM 'yes send it', after the outline accuracy probe:
data/canada-bounds sat 20-50 m off the real edge: 1,900 files thinned at 0.0004-0.006 deg by the old matcher, 940 made from
the Canada key's coarse saved copy (3 decimals, 0.02 deg)). Each saved file is read AGAIN from its own official records at
fine detail (server thinning 0.00005 deg = ~5 m, 6 decimals; bigger only when a park would pass 450 KB) and written back.
Records: the Canada key's joins for that park (CPCAD numbers + provincial '<layer>:<record>' ids via data/ca-key/layers.json,
each checked by name); a park the key does not join (old matcher file) = CPCAD by its saved name near the old outline.
A file is replaced ONLY when every record answered; otherwise the old one stays. Resumable: a done file carries
properties.detail_m. LIMIT=N (test), MINUTES. Writes data/canada-bounds/refine-report.json. Never fails."""
import glob, json, math, os, pathlib, re, sys, time, urllib.parse, urllib.request

UA = {'User-Agent': 'KPC park-map bot (kentuckyportableclub.github.io; ham radio club)'}
OUT = pathlib.Path('data/canada-bounds')
CPCAD = 'https://maps-cartes.ec.gc.ca/arcgis/rest/services/CWS_SCF/CPCAD/MapServer/0'
OFFS = [(0.00003, 3), (0.00005, 5)]   # Oct 31 (Fable review #10, R-G6 'never over 5 m'): a park that cannot be read at 5 m keeps its old file (no 220 m fallback)
LIMIT = int(os.environ.get('LIMIT') or 0)
DEADLINE = time.time() + float(os.environ.get('MINUTES') or 150) * 60
LAST = {}
UCS = [None]
try:   # Oct 29 v3: ALL the park's records, merged into one shape (CPCAD alone can be a 58-acre piece of an 1,900-acre area)
    from shapely.geometry import Polygon as _P, mapping as _map
    from shapely.ops import unary_union as _U
    UNION = True
except Exception: UNION = False  # noqa: BLE001


def notice(m): print('::notice title=Canada outlines refined::' + str(m).replace('\n', ' ')[:900], flush=True)


def get(url, params, timeout=120):
    host = urllib.parse.urlparse(url).netloc
    w = 2 - (time.time() - LAST.get(host, 0))
    if w > 0: time.sleep(w)
    for k in range(3):
        try:
            LAST[host] = time.time()
            data = urllib.parse.urlencode(params).encode()
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=UA), timeout=timeout) as r:   # POST: long ids / where
                j = json.loads(r.read().decode('utf-8', 'replace'))
            if isinstance(j, dict) and 'error' in j: raise RuntimeError(str(j['error'])[:120])
            return j
        except Exception:  # noqa: BLE001
            if k == 2: return None
            time.sleep(6 * (k + 1))


def low(x): return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', str(x or '').lower()).split())


def rings_of(g):
    return [r for r in (g or {}).get('rings') or [] if len(r) >= 4]


def name_ok(want, attrs):
    w = low(want)
    if not w: return True
    m = re.match(r'new brunswick (\d+) wildlife management area$', w)
    if m: return any(str(v).split('.')[0] == m.group(1) for k, v in attrs.items() if str(k).upper() == 'WMZ')
    for v in attrs.values():
        if isinstance(v, str):
            v = low(v)
            if v and (v == w or (len(v) > 3 and (v in w or w in v))): return True
    return False


def read_ids(url, oids, names, off):
    """rings of these object ids at this detail; None when the map did not answer or a record is missing / wrong name."""
    j = get(url.rstrip('/') + '/query', {'objectIds': ','.join(map(str, oids)), 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326,
                                         'maxAllowableOffset': off, 'geometryPrecision': 6, 'f': 'json'})
    if j is None or 'features' not in j: return None
    oidf = j.get('objectIdFieldName') or 'OBJECTID'
    got = {}
    for f in j['features']:
        a = f.get('attributes') or {}
        o = a.get(oidf)
        if o is None: o = next((v for k, v in a.items() if k.lower() in ('objectid', 'fid', 'objectid_1')), None)
        if o is not None: got[str(int(o))] = (a, rings_of(f.get('geometry')))
    out = []
    for o, nm in zip(oids, names):
        x = got.get(str(o))
        if not x or not x[1] or not name_ok(nm, x[0]): return None
        out += x[1]
    return out


def bbox(rings):
    xs = [p[0] for r in rings for p in r]; ys = [p[1] for r in rings for p in r]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


def refine(ref, feat, key, layers, off):
    """all rings for this park at this detail, or (None, why)."""
    m = (key.get(ref) or {}).get('m') or []
    # ONE family per park (test run: CPCAD + 1-3 provincial copies of the same land made files 8x bigger): the CPCAD records
    # when the key has any, else the provincial ones
    if not UNION and any(str(x[0]).isdigit() for x in m): m = [x for x in m if str(x[0]).isdigit()]
    m = [x for x in m if ':n-' not in str(x[0])]   # records saved without a number cannot be asked for by id
    if m:
        groups = {}
        for x in m:
            rid = str(x[0])
            if rid.isdigit(): groups.setdefault(CPCAD, []).append((int(rid), x[1]))
            else:
                pre, _, n = rid.rpartition(':')
                urls = layers.get(pre) or []
                if len(urls) != 1 or not n.isdigit(): return None, f'record {rid}: layer not known exactly'
                groups.setdefault(urls[0], []).append((int(n), x[1]))
        rings = []
        for url, items in groups.items():
            r = read_ids(url, [i for i, _ in items], [n for _, n in items], off)
            if r is None: return None, f'{url.split("/rest/services/")[-1][:50]} did not answer (or a record changed name)'
            rings += r
        return rings, 'key joins'
    # an old matcher file (park the key does not join): CPCAD by its saved name, near the old outline
    nm = (feat.get('properties') or {}).get('cpcad')
    old = [r for poly in (feat.get('geometry') or {}).get('coordinates') or [] for r in (poly if feat['geometry'].get('type') == 'MultiPolygon' else [poly])]
    b = bbox(old) if old and isinstance(old[0][0], list) else None
    if not nm or not b: return None, 'no saved name / shape'
    nmq = str(nm).replace("'", "''")
    j = get(CPCAD + '/query', {'where': f"NAME_E = '{nmq}' OR NAME_F = '{nmq}'", 'geometry': f'{b[0] - .1},{b[1] - .1},{b[2] + .1},{b[3] + .1}', 'geometryType': 'esriGeometryEnvelope',
                               'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects', 'outFields': 'NAME_E', 'returnGeometry': 'true', 'outSR': 4326,
                               'maxAllowableOffset': off, 'geometryPrecision': 6, 'f': 'json'})
    if j is None or 'features' not in j: return None, 'CPCAD did not answer'
    rings = [r for f in j['features'] for r in rings_of(f.get('geometry'))]
    return (rings, 'CPCAD by name') if rings else (None, 'CPCAD has no record with that name here now')


def polys(rings):
    """Esri rings -> GeoJSON MultiPolygon coordinates: clockwise rings are outers, the others are holes of the outer that holds them."""
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
            host = next((o for o in outs if inside(r[0], o[0])), None)
            if host: host.append(r)
            else: outs.append([r])
    return outs


def area_ac(rings):
    if not rings: return 0
    la = sum(p[1] for p in rings[0]) / len(rings[0]); kx, ky = 111320 * math.cos(math.radians(la)), 110574
    return sum(abs(sum((a[0] * kx) * (b_[1] * ky) - (b_[0] * kx) * (a[1] * ky) for a, b_ in zip(r, r[1:] + r[:1]))) / 2 for r in rings) / 4046.86


def main():
    key = {}
    for f in glob.glob('data/ca-key/CA-*.json'):
        try: key.update(json.load(open(f))['parks'])
        except Exception: pass  # noqa: BLE001
    layers = json.load(open('data/ca-key/layers.json')) if os.path.exists('data/ca-key/layers.json') else {}
    files = sorted(OUT.glob('CA-*.json'))
    rep = {'date': time.strftime('%Y-%m-%d'), 'done': 0, 'kept_old': {}, 'bytes_before': 0, 'bytes_after': 0, 'detail_m': {}, 'acres_changed_over_25pct': []}
    n = 0
    for f in files:
        if time.time() > DEADLINE: rep['stopped'] = 'out of time (the next run carries on)'; break
        if LIMIT and n >= LIMIT: break
        try: feat = json.load(open(f))
        except Exception: continue  # noqa: BLE001
        if (feat.get('properties') or {}).get('refine_v') == 3: continue
        n += 1
        ref = f.stem; before = f.stat().st_size
        rings, why, used = None, '', None
        for off, metres in OFFS:
            rings, why = refine(ref, feat, key, layers, off)
            if rings is None: break
            if UNION and rings:
                try:
                    ps = []
                    for poly in polys(rings):
                        g = _P(poly[0], poly[1:]).buffer(0)
                        if not g.is_empty: ps.append(g)
                    u = _U(ps).simplify(off * .6, preserve_topology=True)
                    mm = _map(u)
                    cs = mm['coordinates'] if mm['type'] == 'MultiPolygon' else [mm['coordinates']] if mm['type'] == 'Polygon' else []
                    rings = [[[round(x, 6), round(y, 6)] for x, y in r] for poly in cs for r in poly]
                    rings = [r if k == 0 else r for k, r in enumerate(rings)]
                    UCS[0] = [[[[round(x, 6), round(y, 6)] for x, y in r] for r in poly] for poly in cs]
                except Exception: UCS[0] = None  # noqa: BLE001
            else: UCS[0] = None
            geo = {'type': 'MultiPolygon', 'coordinates': UCS[0] or polys(rings)}
            if len(json.dumps(geo, separators=(',', ':'))) < 120_000: used = metres; break
        if rings is None or used is None:
            rep['kept_old'][ref] = why or 'over 450 KB at every detail'; continue
        old_rings = [r for poly in (feat.get('geometry') or {}).get('coordinates') or [] for r in poly] if (feat.get('geometry') or {}).get('type') == 'MultiPolygon' else (feat.get('geometry') or {}).get('coordinates') or []
        a0, a1 = area_ac(old_rings), area_ac([r for r in rings])
        if a0 and abs(a1 - a0) / a0 > .25: rep['acres_changed_over_25pct'].append([ref, round(a0), round(a1)])
        feat['geometry'] = {'type': 'MultiPolygon', 'coordinates': UCS[0] or polys(rings)}
        feat.setdefault('properties', {})['detail_m'] = used; feat['properties']['refine_v'] = 3
        feat['properties']['refined'] = time.strftime('%Y-%m-%d') + ' (' + why + ')'
        f.write_text(json.dumps(feat, separators=(',', ':')))
        rep['done'] += 1; rep['bytes_before'] += before; rep['bytes_after'] += f.stat().st_size
        rep['detail_m'][str(used)] = rep['detail_m'].get(str(used), 0) + 1
    left = sum(1 for f in files if (json.load(open(f)).get('properties') or {}).get('refine_v') != 3)
    rep['left'] = left
    (OUT / 'refine-report.json').write_text(json.dumps(rep, indent=1))
    grow = rep['bytes_after'] / rep['bytes_before'] if rep['bytes_before'] else 0
    notice(f"{rep['done']} outlines refined (detail metres: {rep['detail_m']}), {len(rep['kept_old'])} kept as they were, {left} left for the next run · "
           f"size {rep['bytes_before'] // 1024} KB -> {rep['bytes_after'] // 1024} KB (x{grow:.1f}) · {len(rep['acres_changed_over_25pct'])} changed area by 25%+: "
           + ', '.join(f'{r} {a}->{b}' for r, a, b in rep['acres_changed_over_25pct'][:8]))
    if rep['kept_old']: notice('kept: ' + '; '.join(f'{k}: {v}' for k, v in list(rep['kept_old'].items())[:10]))


if __name__ == '__main__':
    try: main()
    except Exception as e: notice(f'stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
