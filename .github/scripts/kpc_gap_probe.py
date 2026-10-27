#!/usr/bin/env python3
"""TEMP PROBE (chat 2, Oct 26 2026, HQ 'gap hunt'): reads the desk's layers (KPC_Gap_Layers_desk.md) and says how many of
our parks with NO outline each would give. Writes .claude/build/research/gap-probe.json. Adds nothing to the data.
Deleted after one run. Never fails."""
import json, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import kpc_outline_lead_test as T

UA = {'User-Agent': 'KPC gap probe (kentuckyportableclub.github.io)'}
OUT = {}
T0 = time.time()


def get(url, p=None, timeout=90):
    u = url + ('?' + urllib.parse.urlencode(p) if p else '')
    req = urllib.request.Request(u, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read().decode('utf-8', 'replace'))


def safe(f, *a, **k):
    try: return f(*a, **k)
    except Exception as e: return {'error': str(e)[:160]}  # noqa: BLE001


def layers(svc):
    j = get(svc, {'f': 'json'})
    out = []
    for l in (j.get('layers') or []) + (j.get('tables') or []):
        lj = safe(get, svc.rstrip('/') + '/' + str(l['id']), {'f': 'json'})
        cnt = safe(get, svc.rstrip('/') + '/' + str(l['id']) + '/query', {'where': '1=1', 'returnCountOnly': 'true', 'f': 'json'})
        out.append({'id': l['id'], 'name': l.get('name'), 'geom': lj.get('geometryType') if isinstance(lj, dict) else None,
                    'count': cnt.get('count') if isinstance(cnt, dict) else None,
                    'fields': [f['name'] for f in (lj.get('fields') or [])][:40] if isinstance(lj, dict) else [], 'err': lj.get('error') if isinstance(lj, dict) else None})
    return out


def sample(url, n=10):
    j = get(url.rstrip('/') + '/query', {'where': '1=1', 'outFields': '*', 'returnGeometry': 'false', 'resultRecordCount': n, 'f': 'json'})
    return [f.get('attributes') for f in j.get('features') or []]


MISS = T.missing()
ALLUS = [s for s in MISS if not s.startswith('CA-')]


def test(url, sts, flds=None):
    """parks with no outline (in states sts) that have a same-name area in this layer near their pin"""
    url = url.rstrip('/')
    lj = get(url, {'f': 'json'})
    if lj.get('geometryType') not in ('esriGeometryPolygon', None): return {'geom': lj.get('geometryType'), 'skipped': 'not areas'}
    if not flds:
        flds = [f['name'] for f in lj.get('fields') or [] if f.get('type') == 'esriFieldTypeString'
                and re.search(r'name|nm$|nm_|title|label|site|park|unit|area|desc', f['name'], re.I)][:5]
    parks = [p + (s,) for s in sts for p in MISS.get(s, [])]
    hits, off, seen = {}, 0, 0
    while seen < 40000:
        j = get(url + '/query', {'where': '1=1', 'outFields': ','.join(flds) or '*', 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': 0.01,
                                 'geometryPrecision': 3, 'resultOffset': off, 'resultRecordCount': 1000, 'f': 'json'}, timeout=180)
        if j.get('error'): return {'error': str(j['error'])[:160], 'fields': flds}
        fs = j.get('features') or []
        for ft in fs:
            pts = [p for r in (ft.get('geometry') or {}).get('rings') or [] for p in r]
            if not pts: continue
            bb = [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]
            attrs = ft.get('attributes') or {}
            names = {T.core(v) for v in attrs.values() if isinstance(v, str) and T.core(v)}
            for ref, c, la, lo, acts, st in parks:
                if c in names and bb[0] - .3 <= lo <= bb[2] + .3 and bb[1] - .3 <= la <= bb[3] + .3:
                    hits[ref] = [st, c, acts, next((v for v in attrs.values() if isinstance(v, str) and T.core(v) == c), '')]
        seen += len(fs); off += len(fs)
        if not fs or not j.get('exceededTransferLimit'): break
        time.sleep(.3)
    return {'fields': flds, 'read': seen, 'gives': len(hits), 'activations': sum(h[2] for h in hits.values()), 'parks': hits}


def hub(base, q):
    j = get(base.rstrip('/') + '/api/search/v1/collections/all/items', {'q': q, 'limit': 40})
    return [{'title': (f.get('properties') or {}).get('title'), 'type': (f.get('properties') or {}).get('type'), 'url': (f.get('properties') or {}).get('url')}
            for f in j.get('features') or []]


def grep_layers(svc, pats, cap=60):
    """every layer of a service, every row (attributes only), rows whose text has one of pats"""
    j = get(svc, {'f': 'json'})
    found = []
    for l in (j.get('layers') or [])[:cap]:
        r = safe(get, svc.rstrip('/') + '/' + str(l['id']) + '/query', {'where': '1=1', 'outFields': '*', 'returnGeometry': 'false', 'resultRecordCount': 2000, 'f': 'json'})
        if not isinstance(r, dict): continue
        for f in r.get('features') or []:
            t = json.dumps(f.get('attributes'))
            if re.search(pats, t, re.I): found.append({'layer': l['id'], 'lname': l.get('name'), 'row': {k: v for k, v in (f.get('attributes') or {}).items() if isinstance(v, str)}})
    return {'layers': [(l['id'], l.get('name')) for l in j.get('layers') or []], 'found': found[:60]}


def step(name, f, *a, **k):
    t = time.time()
    OUT[name] = safe(f, *a, **k)
    print(f'::notice title=probe {name}::{round(time.time() - t)} s {json.dumps(OUT[name])[:300]}', flush=True)


# ROUND 3
import pathlib
def nbzones():
    P = json.load(open('data/parkinfo/CA.json'))['parks']
    j = get('https://gis-erd-der.gnb.ca/server/rest/services/OpenData/WMZ/MapServer/0/query', {'where': '1=1', 'outFields': 'WMZ', 'returnGeometry': 'true', 'outSR': 4326,
             'maxAllowableOffset': 0.002, 'f': 'json'}, timeout=180)
    Z = {int(f['attributes']['WMZ']): (f.get('geometry') or {}).get('rings') or [] for f in j.get('features') or []}
    def inside(lo, la, rings):
        n = 0
        for r in rings:
            for k in range(len(r)):
                (x1, y1), (x2, y2) = r[k - 1], r[k]
                if (y1 > la) != (y2 > la) and lo < (x2 - x1) * (la - y1) / (y2 - y1) + x1: n += 1
        return n % 2 == 1
    out = {}
    for ref, v in P.items():
        m = re.search(r'New Brunswick #(\d+)', v[0])
        if not m or v[5] is None: continue
        n = int(m.group(1))
        inz = [z for z, rr in Z.items() if inside(v[6], v[5], rr)]
        out[ref] = {'name': v[0], 'num': n, 'pin in zone': inz, 'match': n in inz}
    return {'zones': sorted(Z), 'parks': out, 'matched': sum(x['match'] for x in out.values()), 'of': len(out)}
step('nb zones', nbzones)


def agol(q):
    j = get('https://www.arcgis.com/sharing/rest/search', {'q': q + ' type:"Feature Service"', 'num': 25, 'f': 'json'})
    return [{'title': r.get('title'), 'owner': r.get('owner'), 'url': r.get('url')} for r in j.get('results') or []]
found = []
for q in ('Mississippi wildlife management areas', 'MDWFP wildlife management area', 'Mississippi state parks boundaries', 'MDWFP state parks'):
    r = safe(agol, q)
    if isinstance(r, list): found += [x for x in r if x not in found]
OUT['ms agol'] = found
print('::notice title=probe ms agol::' + json.dumps(found)[:900], flush=True)
done = 0
for x in found:
    u = str(x.get('url') or '')
    if done >= 8 or not re.search(r'(Feature|Map)Server', u) or not re.search(r'wma|wildlife|park|mdwfp|manage', str(x.get('title')) + ' ' + str(x.get('owner')), re.I): continue
    ls = safe(layers, re.sub(r'/\d+$', '', u))
    for l in (ls if isinstance(ls, list) else [])[:3]:
        if l.get('geom') != 'esriGeometryPolygon': continue
        step(f'ms test {x.get("title")} / {l.get("name")}', test, re.sub(r'/\d+$', '', u) + '/' + str(l['id']), ['MS']); done += 1

os.makedirs('.claude/build/research', exist_ok=True)
json.dump(OUT, open('.claude/build/research/gap-probe.json', 'w'), indent=1, default=str)
gains = {k: v.get('gives') for k, v in OUT.items() if isinstance(v, dict) and 'gives' in v}
print('::notice title=probe gains::' + json.dumps(gains)[:900], flush=True)
