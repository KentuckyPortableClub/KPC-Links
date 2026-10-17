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
        'type': pick('TYPE_E', 'TYPE_EN', 'TYPE'),
        'owner': pick('OWNER_E', 'OWNER_EN', 'OWNER'),
        'mgr': pick('MGMT_E', 'MGMT_EN', 'MANAGEMENT_E', 'MGMT'),
        'loc': pick('LOC_E', 'LOC', 'JURISDICTION'),
    }
    return lid, info, fields, F


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
        if not RECHECK and m and (dt.date.today() - dt.date.fromisoformat(m)).days < 30:
            continue
        todo.append(r)
    if LIMIT:
        todo = todo[:LIMIT]
    note('Canada boundaries', f'{len(parks)} Canadian POTA parks; {len(idx["found"])} already saved; checking {len(todo)} now')
    outf = ','.join(x for x in [F['oid'], F['name'], F['type'], F['owner'], F['mgr'], F['loc']] if x)

    def one(r):
        if time.time() > DEADLINE:
            return r[1], None, 'time'
        ref, nm, la, lo = r[1], r[2], float(r[3]), float(r[4])
        d = 0.03
        q = {'f': 'json', 'geometry': f'{lo - d},{la - d},{lo + d},{la + d}', 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326,
             'spatialRel': 'esriSpatialRelIntersects', 'outFields': outf, 'returnGeometry': 'false'}
        cands = []
        for d in (0.03, 0.12):   # widen to about 13 km when nothing is near the pin
            q['geometry'] = f'{lo - d},{la - d},{lo + d},{la + d}'
            try:
                j = get(url, q)
            except Exception as e:
                return ref, None, 'err ' + str(e)[:80]
            cands = [f['attributes'] for f in j.get('features') or []]
            if any(sim(nm, a.get(F['name'])) >= 0.5 for a in cands):
                break
        if not cands:
            return ref, None, 'none'
        # does the pin sit inside? (one extra point query, only when there is a choice)
        inside = set()
        if len(cands) > 1:
            try:
                jp = get(url, {'f': 'json', 'geometry': f'{lo},{la}', 'geometryType': 'esriGeometryPoint', 'inSR': 4326,
                               'spatialRel': 'esriSpatialRelIntersects', 'outFields': F['oid'], 'returnGeometry': 'false'})
                inside = {f['attributes'][F['oid']] for f in jp.get('features') or []}
            except Exception:
                pass
        scored = sorted(cands, key=lambda a: (sim(nm, a.get(F['name'])), a.get(F['oid']) in inside), reverse=True)
        best = scored[0]
        s = sim(nm, best.get(F['name']))
        if s < 0.5 and not (best.get(F['oid']) in inside and len(words(nm)) == 0):
            return ref, None, f'no name match (closest: {best.get(F["name"])})'
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
                idx['found'][ref] = [feat['properties']['cpcad'], round(len(txt) / 1024)]
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
