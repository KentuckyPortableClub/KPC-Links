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
