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


# ROUND 2
G = 'https://gis-erd-der.gnb.ca/server/rest/services/OpenData/'
for s in ('WMZ', 'Parks', 'Unique_Areas', 'Candidate_Conserved_Areas'):
    step('nb ' + s, layers, G + s + '/MapServer')
    for l in (OUT['nb ' + s] if isinstance(OUT['nb ' + s], list) else [])[:3]:
        step(f'nb {s} {l["id"]} rows', sample, G + s + '/MapServer/' + str(l['id']), 60 if s == 'WMZ' else 8)
        if s != 'WMZ': step(f'nb {s} {l["id"]} test', test, G + s + '/MapServer/' + str(l['id']), ['CA-NB'])


def names(url, flds, where='1=1'):
    out, off = [], 0
    while off < 40000:
        j = get(url + '/query', {'where': where, 'outFields': ','.join(flds), 'returnGeometry': 'false', 'resultOffset': off, 'resultRecordCount': 2000, 'f': 'json'})
        fs = j.get('features') or []
        out += [f.get('attributes') for f in fs]; off += len(fs)
        if not fs or not j.get('exceededTransferLimit'): break
    return out


def trca():
    rows = names('https://services1.arcgis.com/d0ZCwU7eGKVeNiEE/arcgis/rest/services/Property_TRCA/FeatureServer/250', ['PROP_NAME', 'OWNER', 'MNGD_BY', 'L_MUNPALTY'])
    nm = sorted({str(r.get('PROP_NAME')) for r in rows if r.get('PROP_NAME')})
    return {'rows': len(rows), 'distinct names': len(nm), 'hits': [n for n in nm if re.search(r'bond|glassco|duffin|headwater|bathurst|golf', n, re.I)], 'all': nm[:400]}
step('trca names', trca)
step('npca names', lambda: sorted({str(list(r.values())) for r in names('https://services1.arcgis.com/d0ZCwU7eGKVeNiEE/arcgis/rest/services/Conservation_Areas/FeatureServer/2', ['*'])})[:200])
step('crd hits', lambda: names('https://services2.arcgis.com/qRqOFxxnwUHOSocZ/ArcGIS/rest/services/CRD_Parks/FeatureServer/3', ['Name', 'Jurisdic', 'Type', 'RegionalParkStatus', 'AdministrativeArea'],
                               "Name in ('Mount Tolmie Park','Mount Douglas Park','Hatley Park National Historic Site','Uplands Park','Beacon Hill Park')"))


def maris():
    out = {}
    for u in ('https://maris.mississippi.edu/HTML/Maps/RestMapServices.html', 'https://www.maris.state.ms.us/', 'https://maris.mississippi.edu/'):
        try:
            req = urllib.request.Request(u, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r: t = r.read(400000).decode('utf-8', 'replace')
            out[u] = sorted(set(re.findall(r'https?://[^"\' <>]+/rest/services[^"\' <>]*', t)))[:80]
        except Exception as e: out[u] = str(e)[:120]  # noqa: BLE001
    hosts = sorted({re.match(r'https?://[^/]+/[^/]+/rest/services|https?://[^/]+/rest/services', x).group(0) for v in out.values() if isinstance(v, list) for x in v if re.match(r'https?://[^/]+/([^/]+/)?rest/services', x)})
    for h in hosts[:4]:
        out['dir ' + h] = safe(lambda: [x['name'] for x in get(h, {'f': 'json'}).get('folders', [])] + [x['name'] for x in get(h, {'f': 'json'}).get('services', [])])
    return out
step('maris', maris)
mr = OUT.get('maris') if isinstance(OUT.get('maris'), dict) else {}
cand = sorted({x for v in mr.values() if isinstance(v, list) for x in v if isinstance(x, str) and re.search(r'wild|park', x, re.I) and re.search(r'(Map|Feature)Server', x)})
for u in cand[:6]:
    u = re.sub(r'(Server)/.*$', r'\1', u)
    step('ms ' + u, layers, u)
    for l in (OUT['ms ' + u] if isinstance(OUT['ms ' + u], list) else [])[:3]:
        step(f'ms {u} {l["id"]} sample', sample, u + '/' + str(l['id']), 10)
        step(f'ms {u} {l["id"]} test', test, u + '/' + str(l['id']), ['MS'])

os.makedirs('.claude/build/research', exist_ok=True)
json.dump(OUT, open('.claude/build/research/gap-probe.json', 'w'), indent=1, default=str)
gains = {k: v.get('gives') for k, v in OUT.items() if isinstance(v, dict) and 'gives' in v}
print('::notice title=probe gains::' + json.dumps(gains)[:900], flush=True)
