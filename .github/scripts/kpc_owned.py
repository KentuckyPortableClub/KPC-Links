#!/usr/bin/env python3
"""OWNED LAND, ONE PLACE (Oct 27 2026; Fable's boundary review #1, HQ 11:00 AM GO; MAP DATA RULE SHEET B1 + B-G1).
For AGENCY-LAND parks (national forests + grasslands, BLM planning areas, Park Service units, Corps projects, FWS
approved boundaries, Michigan project lines) the park is the land the agency OWNS or ADMINISTERS, never the outer
(proclamation / acquisition / project) line. This module is the ONLY code that reads those ownership maps; the 2-fer
bot (kpc_fers.py) and the owned-land files the website tools draw both use it.

  usfs   Forest Service Basic Ownership (the agency's own layer; content dated 2015: land not shown = NOT SURE, never 'no')
  blm    BLM Surface Management Agency (BLM-administered land)
  nps / usace / fws / state   PAD-US Fee records of that agency (state = state-owned fee land)

Run as a script (kpc-owned.yml, by hand + monthly) it writes the files the tools read:
  ky     ky-dbnf-owned.geojson = Forest Service-owned land inside Daniel Boone National Forest's outer line (Kentucky first)
Never fails: a map that does not answer leaves the last file in place."""
import json, math, os, re, sys, time, urllib.parse, urllib.request

UA = {'User-Agent': 'KPC (kentuckyportableclub.github.io)'}
PADUS = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
FSBO = 'https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_BasicOwnership_02/MapServer/0'
BLMSMA = 'https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_SMA_LimitedScale/MapServer'
OWNER_KEY = {'usfs': 'FED:USFS', 'blm': 'FED:BLM', 'nps': 'FED:NPS', 'usace': 'FED:USACE', 'fws': 'FED:FWS', 'state': 'STATE'}
PADQ = {'nps': "Category = 'Fee' AND Mang_Name = 'NPS'", 'usace': "Category = 'Fee' AND Mang_Name = 'USACE'",
        'fws': "Category = 'Fee' AND Mang_Name = 'FWS'", 'state': "Category = 'Fee' AND Own_Type = 'STAT'"}
OWNMAP = {'usfs': 'Forest Service ownership map (Basic Ownership, 2015 data)', 'blm': 'BLM surface management map',
          'nps': 'PAD-US Park Service fee records', 'usace': 'PAD-US Corps of Engineers fee records', 'fws': 'PAD-US Fish and Wildlife fee records',
          'state': 'PAD-US state fee records'}
AGENCY_LAND = re.compile(r'national forests?\b|national grasslands?\b', re.I)
LOG = []
FSO = {'feat': {}, 'tile': {}, 'f': None}
OWN_T = {}     # (kind, i, j) -> ring groups; 'blm' -> (query url, where)
GET_ONLY = set()


def get(url, params, tries=3, timeout=120):
    body = urllib.parse.urlencode(params).encode()
    last = None
    for i in range(tries):
        try:
            if url in GET_ONLY or len(body) < 1500:
                req = urllib.request.Request(url + '?' + body.decode(), headers=UA)
            else:
                req = urllib.request.Request(url, data=body, headers=dict(UA, **{'Content-Type': 'application/x-www-form-urlencoded'}))
            j = json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', 'replace'))
            if isinstance(j, dict) and j.get('error'): raise RuntimeError(str(j['error'])[:150])
            return j
        except Exception as e:  # noqa: BLE001
            last = e
            if '405' in str(e): GET_ONLY.add(url)
            time.sleep(2 + 3 * i)
    raise last


def esri_rings(g):
    if not g: return []
    if g.get('rings'): return [[[p[0], p[1]] for p in r] for r in g['rings'] if len(r) > 2]
    return []


def _tiles(box, size):
    for i in range(int(math.floor(box[0] / size)), int(math.floor(box[2] / size)) + 1):
        for j in range(int(math.floor(box[1] / size)), int(math.floor(box[3] / size)) + 1):
            yield i, j


def fs_owned(box, det, prec):
    """Forest Service-OWNED land touching box (USDA Basic Ownership): one ring group per parcel, in 0.25-degree tiles,
    each parcel fetched once (a whole forest can be one big multipart feature). None = the map did not answer."""
    try:
        if FSO['f'] is None:
            info = get(FSBO, {'f': 'json'})
            fl = [x['name'] for x in info.get('fields') or []]
            FSO['f'] = next((x for x in fl if x.lower() == 'ownerclassification'), 'ownerclassification')
            FSO['oid'] = info.get('objectIdField') or next((x for x in fl if x.lower() == 'objectid'), 'objectid')
        out = []
        for i, j in _tiles(box, .25):
            if (i, j) not in FSO['tile']:
                tb = [i * .25, j * .25, (i + 1) * .25, (j + 1) * .25]
                ids = get(FSBO + '/query', {'where': f"{FSO['f']} = 'USDA FOREST SERVICE'", 'geometry': ','.join(map(str, tb)),
                                            'geometryType': 'esriGeometryEnvelope', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
                                            'returnIdsOnly': 'true', 'f': 'json'}).get('objectIds') or []
                new = [o for o in ids if o not in FSO['feat']]
                for k in range(0, len(new), 10):
                    j2 = get(FSBO + '/query', {'objectIds': ','.join(map(str, new[k:k + 10])), 'outFields': FSO['oid'], 'returnGeometry': 'true', 'outSR': 4326,
                                                'maxAllowableOffset': det, 'geometryPrecision': prec, 'f': 'json'}, timeout=300)
                    oidf = j2.get('objectIdFieldName') or 'objectid'
                    for f in j2.get('features') or []:
                        a = f.get('attributes') or {}
                        o = a.get(oidf, next((v for kk, v in a.items() if kk.lower() == 'objectid'), None))
                        FSO['feat'][o] = esri_rings(f.get('geometry'))
                FSO['tile'][(i, j)] = ids
            out += [FSO['feat'][o] for o in FSO['tile'][(i, j)] if FSO['feat'].get(o)]
        return out
    except Exception as e:  # noqa: BLE001
        LOG.append(f'Forest Service ownership: {str(e)[:80]}'); return None


def owned_land(kind, box, det, prec):
    """Land the agency owns / administers touching box, by 0.25-degree tile (cached). None = the map did not answer."""
    if kind == 'usfs': return fs_owned(box, det, prec)
    try:
        out = []
        for i, j in _tiles(box, .25):
            k = (kind, i, j)
            if k not in OWN_T:
                tb = [i * .25, j * .25, (i + 1) * .25, (j + 1) * .25]
                if kind == 'blm':
                    if 'blm' not in OWN_T:
                        lays = get(BLMSMA, {'f': 'json'}).get('layers') or []
                        lid = next((l['id'] for l in lays if re.search(r'bureau of land management|\bblm\b', l.get('name', ''), re.I)), lays[0]['id'] if lays else 0)
                        fl = [x['name'] for x in get(f'{BLMSMA}/{lid}', {'f': 'json'}).get('fields') or []]
                        af = next((x for x in fl if re.search(r'admin.*agency|agency.*code|^sma_?id|admin_agency', x, re.I)), None)
                        OWN_T['blm'] = (f'{BLMSMA}/{lid}/query', f"{af} = 'BLM'" if af else '1=1')
                    url, where = OWN_T['blm']
                else: url, where = PADUS, PADQ[kind]
                gs, off = [], 0
                while True:
                    jj = get(url, {'where': where, 'geometry': ','.join(map(str, tb)), 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326,
                                   'spatialRel': 'esriSpatialRelIntersects', 'outFields': '', 'returnGeometry': 'true', 'outSR': 4326,
                                   'maxAllowableOffset': det, 'geometryPrecision': prec, 'resultOffset': off, 'resultRecordCount': 500, 'f': 'json'}, timeout=240)
                    fs = jj.get('features') or []
                    gs += [esri_rings(x.get('geometry')) for x in fs if esri_rings(x.get('geometry'))]
                    if not fs or not jj.get('exceededTransferLimit'): break
                    off += len(fs)
                OWN_T[k] = gs
            out += OWN_T[k]
        return out
    except Exception as e:  # noqa: BLE001
        LOG.append(f'{kind} owned land: {str(e)[:80]}'); return None


def tiles_cached(): return len(FSO['tile']) + sum(1 for k in OWN_T if isinstance(k, tuple))


def evict(near):
    """Drop cached tiles for which near(i, j, size) is False (the caller decides what is near)."""
    for k in [k for k in FSO['tile'] if not near(k[0], k[1], .25)]: del FSO['tile'][k]
    keep = {o for ids in FSO['tile'].values() for o in ids}
    for o in [o for o in FSO['feat'] if o not in keep]: del FSO['feat'][o]
    for k in [k for k in OWN_T if isinstance(k, tuple) and not near(k[1], k[2], .25)]: del OWN_T[k]


# ------------------------------------------------------------------ files for the website tools
def _area(r): return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(r, r[1:] + r[:1])) / 2


def _in_ring(x, y, r):
    c = False
    for i in range(len(r)):
        (x1, y1), (x2, y2) = r[i][:2], r[i - 1][:2]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-15) + x1: c = not c
    return c


def to_multipolygon(rings):
    """Esri rings (outer clockwise, holes counter-clockwise) -> GeoJSON MultiPolygon coordinates (outer first, holes after)."""
    outers = [[r] for r in rings if _area(r) <= 0] or [[r] for r in rings]
    for h in rings:
        if _area(h) <= 0 or any(h is p[0] for p in outers): continue
        x, y = h[0][:2]
        host = next((p for p in outers if _in_ring(x, y, p[0])), None)
        if host: host.append(h)
    return [[[[round(p[0], 5), round(p[1], 5)] for p in r] for r in poly] for poly in outers]


def inside_groups(groups, x, y):
    """Inside any polygon of a GeoJSON MultiPolygon list (holes respected)."""
    for poly in groups:
        if poly and _in_ring(x, y, poly[0]) and not any(_in_ring(x, y, h) for h in poly[1:]): return True
    return False


def ky_dbnf(out='ky-dbnf-owned.geojson'):
    """Kentucky first (HQ Oct 27 11:00 AM): Forest Service-owned land inside Daniel Boone NF's outer line."""
    g = json.load(open('ky-dbnf.geojson'))
    outer = []
    for f in g.get('features') or []:
        geo = f.get('geometry') or {}
        outer += [geo['coordinates']] if geo.get('type') == 'Polygon' else geo.get('coordinates') or [] if geo.get('type') == 'MultiPolygon' else []
    xs = [p[0] for poly in outer for r in poly for p in r]; ys = [p[1] for poly in outer for r in poly for p in r]
    box = [min(xs), min(ys), max(xs), max(ys)]
    parcels = fs_owned(box, 0.00012, 5)
    if parcels is None or not parcels:
        print(f'::notice title=Owned land::Kentucky: the Forest Service ownership map did not answer ({"; ".join(LOG[:2])}); the last file stays', flush=True)
        return False
    feats, acres, seen = [], 0.0, set()
    for rings in parcels:
        if id(rings) in seen: continue   # a big multipart parcel is listed once per tile it touches
        seen.add(id(rings))
        mp = to_multipolygon(rings)
        keep = []
        for poly in mp:
            ring = poly[0]
            cx = sum(p[0] for p in ring) / len(ring); cy = sum(p[1] for p in ring) / len(ring)
            # a piece belongs to Daniel Boone when it lies inside the forest's outer line (centre, or any corner)
            if inside_groups(outer, cx, cy) or sum(1 for p in ring[::max(1, len(ring) // 8)] if inside_groups(outer, p[0], p[1])) >= 2: keep.append(poly)
        if not keep: continue
        kx = 111320 * math.cos(math.radians(37.5)) * 110574
        acres += sum(abs(_area(poly[0])) - sum(abs(_area(h)) for h in poly[1:]) for poly in keep) * kx / 4046.86
        feats.append({'type': 'Feature', 'properties': {'NAME': 'Daniel Boone National Forest', 'ref': 'US-4484', 'owner': 'USDA Forest Service',
                                                        'src': 'Forest Service Basic Ownership (content 2015)'},
                      'geometry': {'type': 'MultiPolygon', 'coordinates': keep}})
    if acres < 200000:   # Daniel Boone owns about 700,000 acres; a short read never replaces the file
        print(f'::notice title=Owned land::Kentucky: only {len(feats)} parcels, about {round(acres):,} acres read (expected ~700,000); the last file stays', flush=True)
        return False
    doc = {'type': 'FeatureCollection', 'name': 'Daniel Boone National Forest: Forest Service-owned land',
           'about': ("Forest Service-OWNED land inside Daniel Boone National Forest's outer line, from the Forest Service's own ownership map "
                     "(EDW Basic Ownership; its content is dated 2015, so land bought since may be missing: not shown here = check the official map). "
                     "Built by .github/scripts/kpc_owned.py. The outer (proclamation) line ky-dbnf.geojson is drawn only as a faint dashed line: "
                     "'Forest boundary line: not all land inside is public' (ruling Oct 27)."),
           'read': time.strftime('%Y-%m-%d'), 'source_date': '2015', 'features': feats}
    txt = json.dumps(doc, separators=(',', ':'))
    try: old = open(out).read()
    except Exception: old = ''  # noqa: BLE001
    if json.loads(old or '{}').get('features') != feats:
        open(out, 'w').write(txt)
    print(f'::notice title=Owned land::Kentucky: {len(feats)} Forest Service parcels, about {round(acres):,} acres, {len(txt) // 1024:,} KB', flush=True)
    return True


if __name__ == '__main__':
    try:
        what = (sys.argv[1:] or ['ky'])[0]
        if what == 'ky': ky_dbnf()
    except Exception as e:  # noqa: BLE001
        print(f'::notice title=Owned land::stopped: {e}', flush=True)
    sys.exit(0)
