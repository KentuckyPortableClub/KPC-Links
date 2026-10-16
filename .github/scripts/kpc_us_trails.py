"""KPC national trails for the US Trip Planner (Brandon Oct 16: 'national trails us planner').
Downloads the official route line of every National Scenic / Historic Trail that is a POTA park, simplifies it for the
web map and writes data/trails/<REF>.json (GeoJSON, lines) + data/trails/index.json [{ref,name,kind,bbox,src,info}].
Sources: the National Park Service's own ArcGIS services (services1.arcgis.com/fBc8EJBxQRMcHlei) and, for trails the
NPS doesn't run, the Forest Service / trail partners. MODE=info only prints what each service has."""
import json, os, sys, time, urllib.request, urllib.parse
NPS = 'https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/'
T = json.load(open(os.path.join(os.path.dirname(__file__), 'kpc_us_trails.json')))
UA = {'User-Agent': 'KPC trails (kentuckyportableclub.github.io)'}
def get(u, t=90):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t) as f: return json.loads(f.read().decode('utf-8', 'replace'))
        except Exception as e: err = e; time.sleep(3)
    raise err
def note(t, m):
    line = f'{t} => ' + str(m).replace('\n', ' ')[:3000]; print(line)
    if os.environ.get('OUT'): open(os.environ['OUT'], 'a').write(line + '\n')
def svc(x): return x['url'] if x['url'].startswith('http') else NPS + x['url']
MODE = os.environ.get('MODE', 'build')
if MODE == 'info':
    for x in T:
        try:
            u = svc(x); j = get(u + '?f=json')
            lay = [(l['id'], l['name'], l.get('geometryType')) for l in j.get('layers', [])]
            c = {}
            for l in j.get('layers', [])[:3]:
                try: c[l['id']] = get(f"{u}/{l['id']}/query?where=1%3D1&returnCountOnly=true&f=json").get('count')
                except Exception as e: c[l['id']] = str(e)[:40]
            note(x['ref'], f"{x['name']} | {lay} | counts {c}")
        except Exception as e: note(x['ref'], f"{x['name']} FAILED {e}")
    for q in os.environ.get('SEARCH', '').split('|'):
        if not q: continue
        j = get('https://www.arcgis.com/sharing/rest/search?f=json&num=12&sortField=numviews&sortOrder=desc&q=' + urllib.parse.quote(q + ' type:"Feature Service"'))
        note('search ' + q, ' || '.join(f"{r['owner']} :: {r['title']} :: {r.get('url')}" for r in j.get('results', [])))
    for q in os.environ.get('POTA', '').split('|'):
        if not q: continue
        j = get('https://api.pota.app/lookup?search=' + urllib.parse.quote(q) + '&size=40')
        note('pota ' + q, ' || '.join(x['display'] for x in j if x['value'].startswith('US-')))
    sys.exit(0)

# ------------------------------------------------------------------ build
OUTDIR = 'data/trails'; os.makedirs(OUTDIR, exist_ok=True)
TOL = float(os.environ.get('TOL', '0.0008'))          # about 80 m: plenty for a trip-planning map
def pick_layer(u, want=None):
    j = get(u + '?f=json'); L = j.get('layers', [])
    if want is not None: return want
    lines = [l for l in L if l.get('geometryType') == 'esriGeometryPolyline']
    pref = [l for l in lines if any(w in l['name'].lower() for w in ('trail', 'centerline', 'route', 'nst', 'nht', 'segment', 'line'))]
    pick = (pref or lines or [l for l in L if l.get('geometryType') == 'esriGeometryPolygon'] or L)[0]
    return pick['id']
def fetch(u, lid):
    feats, off = [], 0
    while True:
        q = urllib.parse.urlencode({'where': '1=1', 'outFields': 'OBJECTID', 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': TOL,
                                    'geometryPrecision': 5, 'resultOffset': off, 'resultRecordCount': 1000, 'f': 'geojson'})
        j = get(f'{u}/{lid}/query?{q}', 180); fs = j.get('features') or []
        feats += fs
        if len(fs) < 1000 and not j.get('exceededTransferLimit') and not (j.get('properties') or {}).get('exceededTransferLimit'): break
        off += len(fs)
        if not fs or off > 60000: break
    return feats
def fetch_esri(u, lid):
    """the same query in Esri's own format (paths / rings), for services whose GeoJSON comes back empty"""
    out, off = [], 0
    for tol in (TOL, 0):
        out, off = [], 0
        while True:
            q = urllib.parse.urlencode({'where': '1=1', 'outFields': 'OBJECTID', 'returnGeometry': 'true', 'returnZ': 'false', 'returnM': 'false', 'outSR': 4326,
                                        'maxAllowableOffset': tol, 'resultOffset': off, 'resultRecordCount': 500, 'f': 'json'})
            j = get(f'{u}/{lid}/query?{q}', 180)
            if j.get('error'): note('esri error', f"{u} {j['error']}"); break
            fs = j.get('features') or []
            for f in fs:
                g = f.get('geometry') or {}
                if g.get('paths'): out.append({'type': 'MultiLineString', 'coordinates': g['paths']})
                elif g.get('rings'): out.append({'type': 'MultiLineString', 'coordinates': g['rings']})
            if not j.get('exceededTransferLimit') or not fs or off > 60000: break
            off += len(fs)
        if out: break
    return out
def lines_of(g):
    if not g: return []
    t, c = g.get('type'), g.get('coordinates')
    if t == 'LineString': return [c]
    if t == 'MultiLineString': return c
    if t == 'Polygon': return c
    if t == 'MultiPolygon': return [r for p in c for r in p]
    return []
index, done, failed = [], 0, []
old = {}
try: old = {x['ref']: x for x in json.load(open(OUTDIR + '/index.json'))}
except Exception: pass
for x in T:
    try:
        u = svc(x); lid = pick_layer(u, x.get('layer'))
        L = []
        geoms = [f.get('geometry') for f in fetch(u, lid)]
        if not any(lines_of(g) for g in geoms): geoms = fetch_esri(u, lid)     # some services won't hand out GeoJSON
        for g in geoms:
            for ln in lines_of(g):
                pts = [[round(p[0], 5), round(p[1], 5)] for p in ln if p and len(p) >= 2]
                pts = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
                if len(pts) > 1: L.append(pts)
        if not L: raise RuntimeError('no lines came back')
        xs = [p[0] for l in L for p in l]; ys = [p[1] for l in L for p in l]
        bb = [round(min(xs), 4), round(min(ys), 4), round(max(xs), 4), round(max(ys), 4)]
        geo = {'type': 'Feature', 'properties': {'ref': x['ref'], 'name': x['name']}, 'geometry': {'type': 'MultiLineString', 'coordinates': L}}
        json.dump(geo, open(f"{OUTDIR}/{x['ref']}.json", 'w'), separators=(',', ':'))
        npts = len(xs); kb = os.path.getsize(f"{OUTDIR}/{x['ref']}.json") // 1024
        index.append({'ref': x['ref'], 'name': x['name'], 'kind': 'NST' if 'Scenic' in x['name'] else 'NHT', 'bbox': bb, 'by': x['by'], 'kb': kb})
        note(x['ref'], f"{x['name']}: layer {lid}, {len(L)} lines, {npts} points, {kb} KB"); done += 1
    except Exception as e:
        failed.append(x['ref']); note(x['ref'] + ' FAILED', f"{x['name']}: {e}")
        if x['ref'] in old and os.path.exists(f"{OUTDIR}/{x['ref']}.json"): index.append(old[x['ref']])   # keep last month's copy
index.sort(key=lambda r: r['name'])
json.dump(index, open(OUTDIR + '/index.json', 'w'), indent=0)
note('Trails done', f'{done} built, {len(failed)} failed {failed}')
