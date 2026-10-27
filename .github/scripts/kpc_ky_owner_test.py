#!/usr/bin/env python3
"""TEMP (chat 2, Oct 27 2026; HQ + chat 8 verdict file KPC_KY2fer_VERDICT_desk.md section 6). Kentucky 2-fer owner tests,
hidden, one run:
  AREA: park x Daniel Boone = a patch at least 50 yards across that is Forest Service-OWNED (Basic Ownership layer) and
        inside the park's official outline.
  LINE: river / trail park x other park = a station spot (5 m inside the other park's public land) within 100 ft of the
        river edge (USGS NHD: large-scale flowline + river-area edges, clipped to the wild river corridor) or the
        Forest Service trail line.
Writes .claude/build/research/ky-owner-test.json. Changes no data. Deleted after the run. Never fails."""
import json, re, sys, time, urllib.parse, urllib.request
from shapely.geometry import shape, Polygon, MultiPolygon, LineString, MultiLineString, box
from shapely.ops import unary_union, transform
from pyproj import Transformer

UA = {'User-Agent': 'KPC Kentucky 2-fer owner test (kentuckyportableclub.github.io)'}
KYBOX = (-85.4, 36.5, -82.9, 38.5)     # the Daniel Boone side of Kentucky
FWD = Transformer.from_crs(4326, '+proj=aeqd +lat_0=37.3 +lon_0=-84.2 +units=m', always_xy=True).transform
SHRINK, ZONE, IN = 22.86, 30.48 - 5.0, 5.0
OUT = {'made': time.strftime('%Y-%m-%d %H:%M'), 'tests': {}, 'notes': []}


def note(t, m): print('::notice title=%s::%s' % (t, str(m).replace('\n', ' ')[:900]), flush=True)


def get(url, p, timeout=180):
    req = urllib.request.Request(url + '?' + urllib.parse.urlencode(p), headers=UA)
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read().decode('utf-8', 'replace'))
        except Exception as e:  # noqa: BLE001
            if i == 3: raise
            time.sleep(5 * (i + 1))


def esri(g):
    if not g: return None
    if g.get('rings'):
        polys = []
        for r in g['rings']:
            if len(r) < 4: continue
            p = Polygon(r)
            if not p.is_valid: p = p.buffer(0)
            polys.append(p)
        if not polys: return None
        # even-odd: rings inside others are holes
        out = None
        for p in sorted(polys, key=lambda q: -q.area):
            out = p if out is None else out.symmetric_difference(p)
        return out
    if g.get('paths'): return MultiLineString([pp for pp in g['paths'] if len(pp) > 1])
    return None


def pull(url, where, fields='*', env=KYBOX, off_m=0.00005):
    feats, off = [], 0
    while True:
        j = get(url + '/query', {'where': where, 'outFields': fields, 'returnGeometry': 'true', 'outSR': 4326, 'geometry': ','.join(map(str, env)),
                                 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
                                 'maxAllowableOffset': off_m, 'geometryPrecision': 6, 'resultOffset': off, 'resultRecordCount': 1000, 'f': 'json'})
        if j.get('error'): raise RuntimeError(str(j['error'])[:200])
        fs = j.get('features') or []
        feats += fs; off += len(fs)
        if not fs or not j.get('exceededTransferLimit'): break
        time.sleep(.3)
    return feats


def fields(url):
    j = get(url, {'f': 'json'})
    return [f['name'] for f in j.get('fields') or []]


def m(g): return transform(FWD, g)


def ky(file, name):
    fs = [f for f in json.load(open(file))['features'] if str((f.get('properties') or {}).get('NAME') or '') == name]
    gs = []
    for f in fs:
        g = shape(f['geometry'])
        gs.append(g if g.is_valid else g.buffer(0))
    return unary_union(gs) if gs else None


KYF = {'bstate': 'ky-state-parks.geojson', 'bwma': 'ky-hunting-areas.geojson', 'bsnp': 'ky-nature-preserves.geojson', 'bsna': 'ky-natural-areas.geojson',
       'bnps': 'ky-nps.geojson', 'bwild': 'ky-wild-rivers.geojson'}
KEY = json.load(open('data/ky-answer-key.json'))['parks']


def park(ref):
    gs = [ky(KYF[t[0]], t[1]) for t in KEY[ref].get('tracts') or [] if t[0] in KYF]
    gs = [g for g in gs if g is not None and not g.is_empty]
    return m(unary_union(gs)) if gs else None


def acres(g): return round(g.area / 4046.86, 1)


# ---- Forest Service OWNED land, Daniel Boone
BO = 'https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_BasicOwnership_02/MapServer/0'
fl = fields(BO)
oc = next((f for f in fl if f.lower() == 'ownerclassification'), None)
fn = next((f for f in fl if f.lower() == 'forestname'), None)
OUT['notes'].append(f'Basic Ownership fields: {fl[:20]}')
where = f"{oc} = 'USDA FOREST SERVICE'" if oc else '1=1'
if fn: where += f" AND {fn} LIKE 'Daniel Boone%'"
bo = pull(BO, where, ','.join(x for x in (oc, fn) if x) or '*')
FS = unary_union([g for g in (esri(f.get('geometry')) for f in bo) if g is not None and not g.is_empty])
FSm = m(FS)
OUT['notes'].append(f'Forest Service-owned Daniel Boone parcels: {len(bo)} features, {acres(FSm)} acres')
note('KY owner test', OUT['notes'][-1])


def area_test(ref, label):
    P = park(ref)
    if P is None: return {'park': label, 'result': 'no outline'}
    inter = P.intersection(FSm)
    core = inter.buffer(-SHRINK)
    return {'park': label, 'ref': ref, 'park_acres': acres(P), 'fs_owned_inside_acres': acres(inter) if not inter.is_empty else 0,
            'result': 'KEEP: a 50-yard Forest Service-owned patch is inside the park' if not core.is_empty else
                      ('DROP: Forest Service-owned land inside the park, but no patch 50 yards across' if not inter.is_empty else 'DROP: no Forest Service-owned land inside the park')}


for ref, nm in (('US-10168', 'Sunny Brook WMA'), ('US-10138', 'Hoskins WMA'), ('US-10160', 'Rockcastle River WMA'), ('US-7970', 'Sinking Creek SNA'),
                ('US-1277', 'Cumberland Falls State Park'), ('US-0686', 'Big South Fork NRA'),
                ('US-10159', 'Redbird WMA'), ('US-3794', 'Beaver Creek WMA'), ('US-10121', 'Cane Creek WMA'), ('US-10146', 'Mill Creek WMA'),
                ('US-10158', 'Pioneer Weapons WMA'), ('US-10170', 'Twin Knobs Campground'), ('US-10171', 'Zilpo Campground'),
                ('US-7964', 'W.H. Martin SNA'), ('US-1286', 'Natural Bridge State Park')):
    try: OUT['tests'][f'{nm} x Daniel Boone (owned)'] = area_test(ref, nm)
    except Exception as e: OUT['tests'][f'{nm} x Daniel Boone (owned)'] = {'error': str(e)[:200]}  # noqa: BLE001
    note('KY owner test', f"{nm}: {OUT['tests'][f'{nm} x Daniel Boone (owned)']}")

# ---- river edges (USGS NHD large scale) and the Sheltowee line (Forest Service trails)
NHD = 'https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer'
lays = get(NHD, {'f': 'json'}).get('layers') or []
flid = next((l['id'] for l in lays if re.search(r'flowline.*large', l['name'], re.I)), None)
arid = next((l['id'] for l in lays if re.search(r'^area.*large', l['name'], re.I)), None)
OUT['notes'].append(f'NHD layers: flowline {flid}, area {arid}')


def river(gnis, corridor_ll):
    b = corridor_ll.bounds
    env = (b[0] - .01, b[1] - .01, b[2] + .01, b[3] + .01)
    ff = fields(f'{NHD}/{flid}')
    gf = next(f for f in ff if f.lower() == 'gnis_name')
    fs = pull(f'{NHD}/{flid}', f"{gf} = '{gnis}'", gf, env, 0.00001)
    lines = unary_union([esri(f.get('geometry')) for f in fs if f.get('geometry')])
    edge = lines
    try:
        ar = pull(f'{NHD}/{arid}', '1=1', '*', env, 0.00001)
        polys = [esri(f.get('geometry')) for f in ar if f.get('geometry')]
        polys = [p for p in polys if p is not None and p.intersects(lines.buffer(.0005))]
        if polys: edge = unary_union([lines] + [p.boundary for p in polys])
    except Exception as e: OUT['notes'].append(f'NHD area {gnis}: {str(e)[:80]}')  # noqa: BLE001
    return m(edge), len(fs)


def line_test(label, L, land, corridor=None):
    if corridor is not None: L = L.intersection(corridor.buffer(60))
    if L.is_empty: return {'test': label, 'result': 'the river / trail line does not cross the designated stretch'}
    spots = L.buffer(ZONE).intersection(land.buffer(-IN))
    along = L.intersection(land.buffer(ZONE + IN)).length if not spots.is_empty else 0
    return {'test': label, 'spot_acres': acres(spots) if not spots.is_empty else 0, 'line_km_with_spots': round(along / 1000, 2),
            'result': 'KEEP: public land of the other park lies within 100 ft of the line (station 5 m inside)' if not spots.is_empty else 'DROP: no qualifying land within 100 ft'}


WR = {'US-10104': ('Red River', 'Red River Wild River'), 'US-10106': ('Rockcastle River', 'Rockcastle River Wild River'),
      'US-10111': ('Rock Creek', 'Rock Creek Wild River'), 'US-10103': ('Cumberland River', 'Cumberland River Wild River'),
      'US-10107': ('Big South Fork Cumberland River', 'Big South Fork Wild River')}
RIV = {}
for ref, (gnis, cname) in WR.items():
    try:
        cor_ll = ky(KYF['bwild'], cname)
        E, n = river(gnis, cor_ll)
        RIV[ref] = (E, m(cor_ll))
        OUT['tests'][f'{cname} x Daniel Boone (owned within 100 ft)'] = dict(line_test(cname, E, FSm, m(cor_ll)), nhd_pieces=n)
    except Exception as e: OUT['tests'][f'{cname} x Daniel Boone (owned within 100 ft)'] = {'error': str(e)[:200]}  # noqa: BLE001
    note('KY owner test', f"{cname}: {OUT['tests'][f'{cname} x Daniel Boone (owned within 100 ft)']}")
for lab, rref, pref in (('Cumberland River wild river x Cumberland Falls State Park', 'US-10103', 'US-1277'),
                        ('Rockcastle wild river x W.H. Martin SNA', 'US-10106', 'US-7964')):
    try:
        E, C = RIV[rref]; OUT['tests'][lab] = line_test(lab, E, park(pref), C)
    except Exception as e: OUT['tests'][lab] = {'error': str(e)[:200]}  # noqa: BLE001
    note('KY owner test', f"{lab}: {OUT['tests'][lab]}")

TR = 'https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_TrailNFSPublish_01/MapServer/0'
try:
    tf = fields(TR); tn = next(f for f in tf if f.lower() == 'trail_name')
    st = pull(TR, f"UPPER({tn}) LIKE '%SHELTOWEE%'", tn, KYBOX, 0.00001)
    SH = m(unary_union([esri(f.get('geometry')) for f in st if f.get('geometry')]))
    OUT['notes'].append(f'Sheltowee Trace (Forest Service trail layer): {len(st)} pieces, {round(SH.length / 1000)} km')
    PW = park('US-10158')
    OUT['tests']['Pioneer Weapons WMA x Sheltowee Trace'] = line_test('Pioneer Weapons x Sheltowee', SH, PW.intersection(FSm))
    E, C = RIV['US-10107']
    near_both = SH.buffer(ZONE).intersection(E.intersection(C.buffer(60)).buffer(ZONE))
    pub = unary_union([FSm, park('US-0686')])
    sp = near_both.intersection(pub.buffer(-IN))
    OUT['tests']['Big South Fork wild river x Sheltowee Trace'] = {'spot_acres': acres(sp) if not sp.is_empty else 0,
        'result': 'KEEP: public land within 100 ft of BOTH the river edge and the trail' if not sp.is_empty else 'DROP: no public spot within 100 ft of both'}
except Exception as e: OUT['tests']['Sheltowee'] = {'error': str(e)[:200]}  # noqa: BLE001
for k in ('Pioneer Weapons WMA x Sheltowee Trace', 'Big South Fork wild river x Sheltowee Trace', 'Sheltowee'):
    if k in OUT['tests']: note('KY owner test', f"{k}: {OUT['tests'][k]}")

json.dump(OUT, open('.claude/build/research/ky-owner-test.json', 'w'), indent=1)
note('KY owner test', 'done: ' + '; '.join(f"{k.split(' x ')[0]}: {str(v.get('result', v.get('error')))[:10]}" for k, v in OUT['tests'].items()))
