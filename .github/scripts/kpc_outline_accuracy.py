#!/usr/bin/env python3
"""OUTLINE ACCURACY PROBE (chat 2, Oct 29 2026; chat 3 + Brandon 6:05 AM: 'check your stored outlines for the same fault').
For a sample of parks in each STORED outline set, read the same record LIVE at full detail and measure, in metres:
  off  = how far the stored corners sit from the live edge (stored vertex -> live boundary)
  cut  = how far the live corners sit from the stored edge (live vertex -> stored boundary: corners cut off by thinning)
Per set: median / 95% / worst of each park's 95% value. 'edge-keeping' = off ~ 0 (stored corners lie ON the real edge, only
corners are cut); 'drifted' = off > 1 m (the stored corners themselves moved). Read only. Writes
.claude/build/research/outline-accuracy.json + .md and prints notices. Never fails."""
import gzip, json, math, os, pathlib, random, sys, time, urllib.parse, urllib.request

import numpy as np

UA = {'User-Agent': 'KPC park-map bot (kentuckyportableclub.github.io; ham radio club)'}
OUT = pathlib.Path('.claude/build/research')
PADUS = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
CPCAD = 'https://maps-cartes.ec.gc.ca/arcgis/rest/services/CWS_SCF/CPCAD/MapServer/0/query'
KYGIS = 'https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/'
KYSETS = {'ky-hunting-areas.geojson': (KYGIS + 'Ky_Public_Hunting_Areas_WGS84WM/MapServer/1/query', 'AREANAME'),
          'ky-state-parks.geojson': (KYGIS + 'Ky_State_Parks_Features_WGS84WM/MapServer/8/query', 'PUBLIC_NAM'),
          'ky-nature-preserves.geojson': (KYGIS + 'Ky_KNP_State_Nature_Preserves_WGS84WM/MapServer/0/query', 'MANAME'),
          'ky-natural-areas.geojson': (KYGIS + 'Ky_KNP_Natural_Areas_WGS84WM/MapServer/0/query', 'MANAME')}
random.seed(29)
LAST = {}


def get(url, params, timeout=120):
    host = urllib.parse.urlparse(url).netloc
    w = 2 - (time.time() - LAST.get(host, 0))
    if w > 0: time.sleep(w)
    for k in range(3):
        try:
            LAST[host] = time.time()
            with urllib.request.urlopen(urllib.request.Request(url + '?' + urllib.parse.urlencode(params), headers=UA), timeout=timeout) as r:
                return json.loads(r.read().decode('utf-8', 'replace'))
        except Exception:  # noqa: BLE001
            time.sleep(5 * (k + 1))
    return None


def esri_poly(g):
    rings = (g or {}).get('rings') or []
    return rings


def gj_rings(gm):
    t, c = gm.get('type'), gm.get('coordinates') or []
    if t == 'Polygon': return [r for r in c]
    if t == 'MultiPolygon': return [r for poly in c for r in poly]
    return []


def proj(lat0):
    kx, ky = 111320 * math.cos(math.radians(lat0)), 110574
    return lambda lon, lat: (lon * kx, lat * ky)


def seg_dist(pts, rings):
    """distance (m) from each point to the nearest segment of rings (all in metres)."""
    segs = [(r[k], r[k + 1]) for r in rings for k in range(len(r) - 1)]
    if not segs or not len(pts): return np.array([])
    A = np.array([s[0] for s in segs], float); B = np.array([s[1] for s in segs], float); D = B - A
    L2 = (D ** 2).sum(1); L2[L2 == 0] = 1e-9
    out = np.full(len(pts), np.inf)
    P = np.array(pts, float)
    for k in range(0, len(segs), 2000):
        a, d, l2 = A[k:k + 2000], D[k:k + 2000], L2[k:k + 2000]
        for c in range(0, len(P), 500):
            p = P[c:c + 500][:, None, :]
            t = np.clip(((p - a) * d).sum(2) / l2, 0, 1)
            q = a + t[..., None] * d
            out[c:c + 500] = np.minimum(out[c:c + 500], np.sqrt(((p - q) ** 2).sum(2)).min(1))
    return out


def ring_area(r):
    x = np.array([p[0] for p in r]); y = np.array([p[1] for p in r])
    return abs((x * np.roll(y, -1) - np.roll(x, -1) * y).sum()) / 2


def measure(stored_rings, live_rings):
    if not stored_rings or not live_rings: return None
    lat0 = sum(p[1] for r in live_rings for p in r) / max(1, sum(len(r) for r in live_rings))
    P = proj(lat0)
    S = [[P(*p[:2]) for p in r] for r in stored_rings if len(r) > 2]; L = [[P(*p[:2]) for p in r] for r in live_rings if len(r) > 2]
    if not S or not L: return None
    sv = [p for r in S for p in r]; lv = [p for r in L for p in r]
    if len(sv) > 3000: sv = random.sample(sv, 3000)
    if len(lv) > 3000: lv = random.sample(lv, 3000)
    off = np.sort(seg_dist(sv, L)); cut = np.sort(seg_dist(lv, S))
    q = lambda a, f: float(a[min(len(a) - 1, int(f * len(a)))])
    # acres: biggest ring minus the others inside is unknown here: use the outer-ring sum (good enough to spot a wrong record)
    area_s = sum(ring_area(r) for r in S) / 4046.86; area_l = sum(ring_area(r) for r in L) / 4046.86
    return {'off_med': round(q(off, .5), 1), 'off95': round(q(off, .95), 1), 'off_max': round(float(off[-1]), 1),
            'cut_med': round(q(cut, .5), 1), 'cut95': round(q(cut, .95), 1), 'cut_max': round(float(cut[-1]), 1),
            'stored_pts': sum(len(r) for r in stored_rings), 'live_pts': sum(len(r) for r in live_rings),
            'acres_stored': round(area_s), 'acres_live': round(area_l)}


def live_by_oid(url, oid):
    j = get(url, {'objectIds': oid, 'outFields': 'OBJECTID', 'returnGeometry': 'true', 'outSR': 4326, 'geometryPrecision': 7, 'f': 'json'})
    fs = (j or {}).get('features') or []
    return esri_poly(fs[0].get('geometry')) if fs else None


def live_by_name(url, fld, name):
    nm = str(name).replace("'", "''")
    j = get(url, {'where': f"{fld} = '{nm}'", 'outFields': fld, 'returnGeometry': 'true', 'outSR': 4326, 'geometryPrecision': 7, 'f': 'json'})
    return [r for f in (j or {}).get('features') or [] for r in esri_poly(f.get('geometry'))]


def sets():
    res = {}
    # A. Kentucky files (the site + the KY line + the KY app pack read these)
    rows = []
    for fn, (url, fld) in KYSETS.items():
        try: feats = json.load(open(fn))['features']
        except Exception: continue  # noqa: BLE001
        pick = [f for f in feats if f.get('geometry')]
        random.shuffle(pick)
        for f in pick[:6]:
            nm = (f.get('properties') or {}).get('NAME')
            live = live_by_name(url, fld, nm)
            m = measure(gj_rings(f['geometry']), live)
            if m: rows.append(dict(m, park=nm, file=fn))
            if len([r for r in rows if r['file'] == fn]) >= 5: break
    res['Kentucky files (ky-*.geojson)'] = rows
    # B. Kentucky app pack (Douglas-Peucker 3 m from the KY files)
    rows = []
    try:
        pk = json.load(open('app/packs/US-KY.json'))['outlines']
        ky = {x['c']: x.get('n') for x in json.load(open('kpc-ky-data.json'))['parks']}
        refs = [r for r in pk if pk[r] and pk[r][0].get('src') == 'official']
        random.shuffle(refs)
        for r in refs:
            if len(rows) >= 12: break
            o = pk[r][0]; lay = str(o.get('layer') or '')
            fn = next((f for f in KYSETS if f.split('.')[0].split('ky-')[1].split('-')[0] in lay.lower()), None)
            if not fn: continue
            url, fld = KYSETS[fn]
            feats = json.load(open(fn))['features']
            nm = next((f['properties'].get('NAME') for f in feats if (f.get('properties') or {}).get('NAME') and ky.get(r) and str(f['properties']['NAME']).lower() in str(ky[r]).lower()), None)
            if not nm: continue
            m = measure(gj_rings(o['g']), live_by_name(url, fld, nm))
            if m: rows.append(dict(m, park=f'{r} {nm}', file='app/packs/US-KY.json'))
    except Exception as e: print(f'pack: {e}', flush=True)  # noqa: BLE001
    res['Kentucky app pack (3 m)'] = rows
    # C. US key saved outlines (boundary-cache US-XX.json.gz: what pass 1 of the 2-fer line + the saved-copy builds read)
    rows = []
    files = sorted(pathlib.Path('cache/us').glob('US-*.json.gz'))
    random.shuffle(files)
    for f in files[:10]:
        try: recs = [r for r in json.load(gzip.open(f)).get('recs') or [] if isinstance(r.get('OBJECTID'), int) and r.get('_r')]
        except Exception: continue  # noqa: BLE001
        random.shuffle(recs)
        for r in recs[:2]:
            m = measure(r['_r'], live_by_oid(PADUS, r['OBJECTID']))
            if m: rows.append(dict(m, park=f"{f.name[:5]} {r.get('Unit_Nm') or r.get('OBJECTID')}", file=f.name))
    res['US key saved copy (PAD-US, cache/us)'] = rows
    # D. Canada key saved outlines (CA-ALL.json.gz, CPCAD records)
    rows = []
    try:
        recs = [r for r in json.load(gzip.open('cache/ca/CA-ALL.json.gz')).get('recs') or [] if str(r.get('oid', '')).isdigit() and r.get('_r')]
        random.shuffle(recs)
        for r in recs[:20]:
            m = measure(r['_r'], live_by_oid(CPCAD, r['oid']))
            if m: rows.append(dict(m, park=r.get('n'), file='CA-ALL.json.gz'))
    except Exception as e: print(f'canada: {e}', flush=True)  # noqa: BLE001
    res['Canada key saved copy (CPCAD, CA-ALL)'] = rows
    # E. Canada park outlines the site draws (data/canada-bounds, from the checked list) vs CPCAD by name
    rows = []
    fs = sorted(pathlib.Path('data/canada-bounds').glob('CA-*.json'))
    random.shuffle(fs)
    for f in fs:
        if len(rows) >= 12: break
        try: d = json.load(open(f))
        except Exception: continue  # noqa: BLE001
        nm = (d.get('properties') or {}).get('cpcad')
        if not nm or 'CPCAD' not in str((d.get('properties') or {}).get('src')): continue
        m = measure(gj_rings(d.get('geometry') or {}), live_by_name(CPCAD, 'NAME_E', nm))
        if m: rows.append(dict(m, park=f'{f.stem} {nm}', file=str(f)))
    res['Canada outlines the site draws (data/canada-bounds)'] = rows
    return res


def main():
    t0 = time.time()
    res = sets()
    q = lambda a, f: sorted(a)[min(len(a) - 1, int(f * len(a)))] if a else None
    summ = {}
    for k, rows in res.items():
        if not rows: summ[k] = {'parks': 0}; continue
        o95 = [r['off95'] for r in rows]; c95 = [r['cut95'] for r in rows]
        summ[k] = {'parks': len(rows), 'off_median': q(o95, .5), 'off_95': q(o95, .95), 'off_worst': max(r['off_max'] for r in rows),
                   'cut_median': q(c95, .5), 'cut_95': q(c95, .95), 'cut_worst': max(r['cut_max'] for r in rows),
                   'kind': 'edge-keeping (corners on the real edge)' if q(o95, .5) <= 1 else 'drifted (stored corners off the real edge)',
                   'ok_5m': q([max(r['off95'], r['cut95']) for r in rows], .95) <= 5}
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump({'about': __doc__.split('\n')[0], 'date': time.strftime('%Y-%m-%d'), 'summary': summ, 'parks': res}, open(OUT / 'outline-accuracy.json', 'w'), indent=1)
    L = ['# Stored outlines vs a fresh full-detail read (chat 2 probe, %s)' % time.strftime('%Y-%m-%d'), '',
         "Metres, each park's 95% value, then median / 95% / worst over the sample. OFF = stored corners from the live edge; CUT = live corners from the stored edge (thinning cuts them).", '',
         '| Set | parks | OFF median | OFF 95% | OFF worst | CUT median | CUT 95% | CUT worst | kind | within 5 m (95%) |', '|---|---|---|---|---|---|---|---|---|---|']
    for k, s in summ.items():
        if not s.get('parks'): L.append(f'| {k} | 0 (no live answer) | | | | | | | | |'); continue
        L.append(f"| {k} | {s['parks']} | {s['off_median']} | {s['off_95']} | {s['off_worst']} | {s['cut_median']} | {s['cut_95']} | {s['cut_worst']} | {s['kind']} | {'yes' if s['ok_5m'] else 'NO'} |")
    L += ['', '## Parks', '']
    for k, rows in res.items():
        L += [f'### {k}', ''] + [f"- {r['park']}: off {r['off_med']}/{r['off95']}/{r['off_max']} m, cut {r['cut_med']}/{r['cut95']}/{r['cut_max']} m, points {r['stored_pts']} vs {r['live_pts']}, acres {r['acres_stored']} vs {r['acres_live']}" for r in rows] + ['']
    (OUT / 'outline-accuracy.md').write_text('\n'.join(L) + '\n')
    for k, s in summ.items():
        print(f"::notice title=Outline accuracy::{k}: " + (f"{s['parks']} parks · off med/95/worst {s.get('off_median')}/{s.get('off_95')}/{s.get('off_worst')} m · cut {s.get('cut_median')}/{s.get('cut_95')}/{s.get('cut_worst')} m · {s.get('kind')}" if s.get('parks') else 'no live answer'), flush=True)
    print(f'::notice title=Outline accuracy::done in {int(time.time() - t0)} s', flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=Outline accuracy::stopped: {str(e)[:200]}', flush=True)  # noqa: BLE001
    sys.exit(0)
