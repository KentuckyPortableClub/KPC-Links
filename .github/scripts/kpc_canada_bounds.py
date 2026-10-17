#!/usr/bin/env python3
"""KPC Canada park boundaries (Brandon Oct 17 2026: 'what is the next step for boundaries in Canada, another GitHub bot?').

For every Canadian POTA park (CA- refs in data/canada.json) find its outline in the Government of Canada's
Canadian Protected and Conserved Areas Database (CPCAD, Environment and Climate Change Canada, Open Government
Licence - Canada) and save a small GeoJSON file per park:
  data/canada-bounds/<REF>.json  = {type:Feature, properties:{ref, name, cpcad, type, owner, manager, src}, geometry}
  data/canada-bounds/index.json  = {updated, src, found:{ref:[cpcad name, kb]}, miss:{ref:'yyyy-mm-dd'}}
The KPC US Trip Planner's SHOW THIS PARK'S OUTLINE draws these for CA- parks (labelled official, CPCAD).

How a park is matched: CPCAD areas within about 3 km of the POTA pin (the pin is often at the entrance, outside
the line), best name match after dropping generic words, ties to the area that holds the pin.
If CPCAD has no match, the provincial maps (Ontario, Alberta, Quebec, Saskatchewan, Manitoba, BC parks + recreation sites) and
Parks Canada's own places layer are tried (EXTRA list; properties.srcShort names the source).
Resumable: parks already saved are skipped unless RECHECK=1; misses are retried after 30 days.
MODE=info prints the service's layers and fields only (use it first if the service changes).
"""
import json, os, re, sys, time, unicodedata, urllib.parse, urllib.request, concurrent.futures as cf, datetime as dt

SVC = os.environ.get('CPCAD_URL', 'https://maps-cartes.ec.gc.ca/arcgis/rest/services/CWS_SCF/CPCAD/MapServer')
OUT = 'data/canada-bounds'
UA = {'User-Agent': 'KPC-Links/1.0 (Kentucky Portable Club ham radio site; github.com/KentuckyPortableClub/KPC-Links)'}
TODAY = dt.date.today().isoformat()
LIMIT = int(os.environ.get('LIMIT', '0') or 0)          # 0 = every park
RECHECK = os.environ.get('RECHECK') == '1'
MISSES = os.environ.get('MISSES') == '1'   # look again only at the parks that were not matched
DEADLINE = time.time() + float(os.environ.get('MINUTES', '150')) * 60   # stop cleanly before the job's time limit
GENERIC = set('park parks provincial national territorial area areas reserve reserves conservation protected ecological wildlife wilderness heritage historic site sites marine natural regional recreation recreational the of de du des la le les et and parc reserve-naturelle'.split())


def note(t, m):
    print(f'::notice title={t}::{m}', flush=True)


def get(url, params=None, tries=3, timeout=60):
    if params:
        url += ('&' if '?' in url else '?') + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return json.loads(r.read().decode('utf-8', 'replace'))
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(2 + i * 3)


def words(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode()   # Île -> Ile, é -> e
    s = re.sub(r'[^a-z0-9 ]+', ' ', s.lower().replace('’', "'").replace("'", ''))
    return [w for w in s.split() if w and w not in GENERIC]


def simb(nm, a, F):
    return max(sim(nm, a.get(F['name'])), sim(nm, a.get(F.get('namef')) if F.get('namef') else ''))


def sim(a, b):
    A, B = set(words(a)), set(words(b))
    if not A or not B:
        return 0.0
    return len(A & B) / max(len(A), len(B))


def layer_info():
    root = get(SVC, {'f': 'json'})
    lays = root.get('layers') or []
    best = None
    for l in lays:
        info = get(f"{SVC}/{l['id']}", {'f': 'json'})
        if 'Polygon' in str(info.get('geometryType', '')):
            best = (l['id'], info)
            break
    if not best:
        raise SystemExit('No polygon layer found in ' + SVC)
    lid, info = best
    fields = [f['name'] for f in info.get('fields', [])]
    pick = lambda *names: next((f for n in names for f in fields if f.lower() == n.lower()), None)
    F = {
        'oid': info.get('objectIdField') or pick('OBJECTID', 'FID'),
        'name': pick('NAME_E', 'NAME_EN', 'NAME', 'ENG_NAME', 'PA_NAME'),
        'namef': pick('NAME_F', 'NAME_FR'),
        'type': pick('TYPE_E', 'TYPE_EN', 'TYPE'),
        'owner': pick('OWNER_E', 'OWNER_EN', 'OWNER'),
        'mgr': pick('MGMT_E', 'MGMT_EN', 'MANAGEMENT_E', 'MGMT'),
        'loc': pick('LOC_E', 'LOC', 'JURISDICTION'),
    }
    return lid, info, fields, F


# ---------------------------------------------------------------- provincial + Parks Canada maps (Brandon Oct 17: 'yes')
# Used only when CPCAD has no name match near the pin. Each source: label, kind, url, name fields (None = guess), bbox (lon/lat).
CA = (-141.1, 41.6, -52.5, 83.2)
EXTRA = [
    ('Parks Canada', 'arcgis', 'https://services2.arcgis.com/wCOMu5IS7YdSyPNx/arcgis/rest/services/vw_Places_Public_lieux_public_APCA/FeatureServer', None, CA),
    ('Ontario Parks (Land Information Ontario)', 'arcgis', 'https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open03/MapServer/4', ['PROTECTED_AREA_NAME_ENG', 'PROTECTED_AREA_NAME_FR', 'COMMON_SHORT_NAME'], (-95.2, 41.6, -74.3, 56.9)),
    ('Ontario conservation reserves (Land Information Ontario)', 'arcgis', 'https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open03/MapServer/2', ['PROTECTED_AREA_NAME_ENG', 'PROTECTED_AREA_NAME_FR', 'COMMON_SHORT_NAME'], (-95.2, 41.6, -74.3, 56.9)),
    ('Alberta Parks (Government of Alberta)', 'arcgis', 'https://geospatial.alberta.ca/titan/rest/services/boundary/parks_protected_areas_alberta/FeatureServer/0', ['NAME', 'OC_NAME'], (-120.1, 48.9, -109.9, 60.1)),
    ('Québec protected areas register (MELCCFP)', 'arcgis', 'https://geo.environnement.gouv.qc.ca/donnees/rest/services/Biodiversite/Aires_protegees/MapServer/23', ['TOPONYME', 'DESIGNOM'], (-79.8, 44.9, -57.0, 62.7)),
    ('Saskatchewan Parks (Government of Saskatchewan)', 'arcgis', 'https://gis.saskatchewan.ca/arcgis/rest/services/ParksAsLegislated/FeatureServer', None, (-110.1, 48.9, -101.3, 60.1)),
    ('Manitoba Parks (Government of Manitoba)', 'arcgis', 'https://services.arcgis.com/mMUesHYPkXjaFGfS/arcgis/rest/services/Manitoba_Parks/FeatureServer', None, (-102.2, 48.9, -88.9, 60.1)),
    ('BC Parks (BC Geographic Warehouse)', 'wfs', 'WHSE_TANTALIS.TA_PARK_ECORES_PA_SVW', ['PROTECTED_LANDS_NAME'], (-139.2, 48.2, -114.0, 60.1)),
    ('BC recreation sites (BC Geographic Warehouse)', 'wfs', 'WHSE_FOREST_TENURE.FTEN_RECREATION_POLY_SVW', ['PROJECT_NAME', 'SITE_NAME'], (-139.2, 48.2, -114.0, 60.1)),
]
BCWFS = 'https://openmaps.gov.bc.ca/geo/pub/wfs'
NAMEY = re.compile(r'(name|nom|toponym|title|site)', re.I)
_layers = {}


def arc_layers(url):
    """Polygon layers of a service (or the one layer given), with their name fields."""
    if url in _layers:
        return _layers[url]
    out = []
    try:
        if re.search(r'/(MapServer|FeatureServer)/\d+$', url):
            ids = [url]
        else:
            root = get(url, {'f': 'json'})
            ids = [f"{url}/{l['id']}" for l in root.get('layers') or [] if not l.get('subLayerIds')]
        for lu in ids[:12]:
            i = get(lu, {'f': 'json'})
            if 'Polygon' not in str(i.get('geometryType', '')):
                continue
            fl = [f['name'] for f in i.get('fields', []) if 'String' in f.get('type', '')]
            out.append((lu, i.get('objectIdField') or 'OBJECTID', [f for f in fl if NAMEY.search(f) and not re.search(r'url|link|code|id$', f, re.I)][:4],
                        'geoJSON' in str(i.get('supportedQueryFormats', ''))))
    except Exception as e:
        note('Extra source failed', f'{url}: {str(e)[:120]}')
    _layers[url] = out
    return out


def rings2geo(g):
    rings = (g or {}).get('rings') or []
    return {'type': 'MultiPolygon', 'coordinates': [[r] for r in rings]} if rings else None


def xsim(nm, other):
    # stricter than CPCAD: every key word of the POTA name must be in the map's name, or 2 of 3 words shared
    A, B = set(words(nm)), set(words(other))
    if not A or not B:
        return 0.0
    return 1.0 if A <= B else (sim(nm, other) if sim(nm, other) >= 0.67 else 0.0)


def best_of(nm, cands):
    sc = [(max(xsim(nm, a.get(f) or '') for f in fl) if fl else 0, a, fl) for a, fl in cands]
    sc.sort(key=lambda x: -x[0])
    return sc[0] if sc else (0, None, None)


def extra_one(ref, nm, la, lo):
    for label, kind, url, nf, bb in EXTRA:
        if not (bb[0] <= lo <= bb[2] and bb[1] <= la <= bb[3]):
            continue
        for d in (0.03, 0.12, 0.3):
            try:
                if kind == 'wfs':
                    j = get(BCWFS, {'service': 'WFS', 'version': '2.0.0', 'request': 'GetFeature', 'typeName': url, 'outputFormat': 'json', 'srsName': 'EPSG:4326',
                                    'count': 60, 'bbox': f'{la - d},{lo - d},{la + d},{lo + d},urn:ogc:def:crs:EPSG::4326'})
                    feats = j.get('features') or []
                    cands = [(f.get('properties') or {}, nf) for f in feats]
                    s_, best, fl = best_of(nm, cands)
                    if best is not None and s_ >= 0.5:
                        f = feats[[c[0] for c in cands].index(best)]
                        name = next((best.get(k) for k in nf if best.get(k)), nm)
                        return {'geometry': f['geometry'], 'cpcad': str(name).title() if str(name).isupper() else name, 'src': label}
                else:
                    for lu, oid, fl0, gj in arc_layers(url):
                        fl = nf or fl0
                        if not fl:
                            continue
                        j = get(lu + '/query', {'f': 'json', 'geometry': f'{lo - d},{la - d},{lo + d},{la + d}', 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326,
                                                'spatialRel': 'esriSpatialRelIntersects', 'outFields': ','.join([oid] + fl), 'returnGeometry': 'false'})
                        cands = [(f['attributes'], fl) for f in j.get('features') or []]
                        s_, best, _ = best_of(nm, cands)
                        if best is None or s_ < 0.5:
                            continue
                        geo = None
                        for off in (0.0004, 0.002, 0.006):
                            q = {'objectIds': best[oid], 'outSR': 4326, 'returnGeometry': 'true', 'maxAllowableOffset': off, 'geometryPrecision': 5, 'outFields': oid}
                            if gj:
                                g = get(lu + '/query', dict(q, f='geojson'))
                                fs = g.get('features') or []
                                geo = fs[0].get('geometry') if fs else None
                            else:
                                g = get(lu + '/query', dict(q, f='json'))
                                fs = g.get('features') or []
                                geo = rings2geo(fs[0].get('geometry')) if fs else None
                            if not geo or len(json.dumps(geo)) < 450_000:
                                break
                        if geo:
                            name = next((best.get(k) for k in fl if best.get(k)), nm)
                            return {'geometry': geo, 'cpcad': str(name).title() if str(name).isupper() else name, 'src': label}
            except Exception as e:
                break
    return None


def main():
    lid, info, fields, F = layer_info()
    if os.environ.get('MODE') == 'info':
        note('CPCAD layer', f"{SVC}/{lid} {info.get('name')} · {info.get('geometryType')} · maxRecordCount {info.get('maxRecordCount')} · formats {info.get('supportedQueryFormats')}")
        note('CPCAD fields', ', '.join(fields)[:900])
        note('CPCAD picked', json.dumps(F))
        return
    if not F['name'] or not F['oid']:
        raise SystemExit('Name or id field not found: ' + json.dumps(F))
    url = f'{SVC}/{lid}/query'
    can = json.load(open('data/canada.json'))
    parks = [r for r in can['rows'] if r[0] == 'POTA' and str(r[1]).startswith('CA-')]
    os.makedirs(OUT, exist_ok=True)
    ip = os.path.join(OUT, 'index.json')
    idx = json.load(open(ip)) if os.path.exists(ip) else {'found': {}, 'miss': {}}
    idx.setdefault('found', {}); idx.setdefault('miss', {})
    todo = []
    for r in parks:
        ref = r[1]
        if not RECHECK and ref in idx['found'] and os.path.exists(os.path.join(OUT, ref + '.json')):
            continue
        m = idx['miss'].get(ref)
        if not RECHECK and not MISSES and m and (dt.date.today() - dt.date.fromisoformat(m)).days < 30:
            continue
        if MISSES and not m:
            continue
        todo.append(r)
    if LIMIT:
        todo = todo[:LIMIT]
    note('Canada boundaries', f'{len(parks)} Canadian POTA parks; {len(idx["found"])} already saved; checking {len(todo)} now')
    outf = ','.join(x for x in [F['oid'], F['name'], F.get('namef'), F['type'], F['owner'], F['mgr'], F['loc']] if x)

    def extra_try(ref, nm, la, lo, why):
        if os.environ.get('NO_EXTRA') == '1':
            return ref, None, why
        x = extra_one(ref, nm, la, lo)
        if not x:
            return ref, None, why
        feat = {'type': 'Feature', 'properties': {'ref': ref, 'name': nm, 'cpcad': x['cpcad'], 'type': None, 'owner': None, 'manager': None,
                'src': x['src'], 'srcShort': x['src']}, 'geometry': x['geometry']}
        return ref, feat, 'ok'

    def one(r):
        if time.time() > DEADLINE:
            return r[1], None, 'time'
        ref, nm, la, lo = r[1], r[2], float(r[3]), float(r[4])
        d = 0.03
        q = {'f': 'json', 'geometry': f'{lo - d},{la - d},{lo + d},{la + d}', 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326,
             'spatialRel': 'esriSpatialRelIntersects', 'outFields': outf, 'returnGeometry': 'false'}
        cands = []
        for d in (0.03, 0.12, 0.3):   # widen to about 13 km when nothing is near the pin
            q['geometry'] = f'{lo - d},{la - d},{lo + d},{la + d}'
            try:
                j = get(url, q)
            except Exception as e:
                return ref, None, 'err ' + str(e)[:80]
            cands = [f['attributes'] for f in j.get('features') or []]
            if any(simb(nm, a, F) >= 0.5 for a in cands):
                break
        if not cands:
            return extra_try(ref, nm, la, lo, 'none')
        # does the pin sit inside? (one extra point query, only when there is a choice)
        inside = set()
        if len(cands) > 1:
            try:
                jp = get(url, {'f': 'json', 'geometry': f'{lo},{la}', 'geometryType': 'esriGeometryPoint', 'inSR': 4326,
                               'spatialRel': 'esriSpatialRelIntersects', 'outFields': F['oid'], 'returnGeometry': 'false'})
                inside = {f['attributes'][F['oid']] for f in jp.get('features') or []}
            except Exception:
                pass
        scored = sorted(cands, key=lambda a: (simb(nm, a, F), a.get(F['oid']) in inside), reverse=True)
        best = scored[0]
        s = simb(nm, best, F)
        if s < 0.5 and not (best.get(F['oid']) in inside and len(words(nm)) == 0):
            return extra_try(ref, nm, la, lo, f'no name match (closest: {best.get(F["name"])})')
        oid = best[F['oid']]
        geo = None
        for off in (0.0004, 0.002, 0.006):
            try:
                g = get(url, {'f': 'geojson', 'objectIds': oid, 'outSR': 4326, 'returnGeometry': 'true', 'maxAllowableOffset': off,
                              'geometryPrecision': 5, 'outFields': F['oid']})
                fs = g.get('features') or []
                if not fs or not fs[0].get('geometry'):
                    break
                geo = fs[0]['geometry']
                if len(json.dumps(geo)) < 450_000:
                    break
            except Exception:
                geo = None
                break
        if not geo:
            return ref, None, 'no geometry'
        feat = {'type': 'Feature', 'properties': {'ref': ref, 'name': nm, 'cpcad': best.get(F['name']), 'type': best.get(F['type']) if F['type'] else None,
                'owner': best.get(F['owner']) if F['owner'] else None, 'manager': best.get(F['mgr']) if F['mgr'] else None,
                'src': 'Canadian Protected and Conserved Areas Database (Environment and Climate Change Canada), Open Government Licence - Canada'},
                'geometry': geo}
        return ref, feat, 'ok'

    done = miss = err = 0
    with cf.ThreadPoolExecutor(max_workers=int(os.environ.get('THREADS', '6'))) as ex:
        for ref, feat, why in ex.map(one, todo):
            if why == 'time':
                continue
            if feat:
                txt = json.dumps(feat, separators=(',', ':'))
                open(os.path.join(OUT, ref + '.json'), 'w').write(txt)
                idx['found'][ref] = [feat['properties']['cpcad'], round(len(txt) / 1024)] + ([feat['properties']['srcShort']] if feat['properties'].get('srcShort') else [])
                idx['miss'].pop(ref, None); done += 1
            elif why.startswith('err'):
                err += 1
            else:
                idx['miss'][ref] = TODAY; miss += 1
    idx['updated'] = TODAY
    idx['src'] = 'CPCAD, Environment and Climate Change Canada (Open Government Licence - Canada)'
    json.dump(idx, open(ip, 'w'), separators=(',', ':'), sort_keys=True)
    note('Canada boundaries saved', f'{done} new outlines, {miss} not matched, {err} errors this run; {len(idx["found"])} of {len(parks)} parks have an outline now')


if __name__ == '__main__':
    main()
