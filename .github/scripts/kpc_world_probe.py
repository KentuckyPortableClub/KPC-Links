"""Find the OFFICIAL protected-area map services for the next busy POTA countries (JP, DE, GB, PL, AU) so the answer-key bots
have sources waiting (Brandon Oct 18 2026: 'have data waiting on you instead of waiting on data'). Prints what answers from GitHub's
servers: direct services (status, layers, fields, record count) and ArcGIS Online searches (title, owner, url). Writes
data/world-probe.json for the next step. Safe to rerun."""
import json, re, time, urllib.parse, urllib.request

UA = {'User-Agent': 'KPC (kentuckyportableclub.github.io)'}
OUT = {}


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', '%0A')[:3800]), flush=True)


def fetch(u, raw=False, timeout=60):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout) as r:
            b = r.read(6000000)
            return r.status, (b if raw else b.decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e: return e.code, ''
    except Exception as e: return 0, str(e)[:120]  # noqa: BLE001


DIRECT = {   # Oct 20 round: the biggest missing groups (France's 10k small reserves, Australia's state forests, Canada's provinces)
    'FR': ['https://data.geopf.fr/wfs/ows?SERVICE=WFS&REQUEST=GetCapabilities&VERSION=2.0.0',
           'https://ws.carmencarto.fr/WFS/119/fxx_inpn?SERVICE=WFS&REQUEST=GetCapabilities'],
    'AU': ['https://mapprod3.environment.nsw.gov.au/arcgis/rest/services?f=json',
           'https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Boundaries?f=json',
           'https://services.land.vic.gov.au/catalogue/publicproxy/guest/dv_geoserver/wfs?SERVICE=WFS&REQUEST=GetCapabilities'],
    'CA': ['https://servicesmatriciels.mern.gouv.qc.ca/erdas-iws/ogc/wms?SERVICE=WMS&REQUEST=GetCapabilities'],
}
SEARCH = {
    'FR': ['ZNIEFF type 1', 'Zones naturelles d interet ecologique faunistique et floristique', 'reserves biologiques ONF'],
    'AU': ['NSW State Forests', 'Forestry Corporation NSW state forest', 'Queensland State Forests', 'Victoria state forest', 'Western Australia state forest DBCA', 'DBCA legislated lands and waters'],
    'CA': ['Ontario conservation areas conservation authority', 'Parcs regionaux Quebec', 'Lieux historiques nationaux du Canada', 'Nova Scotia provincial parks', 'New Brunswick provincial parks', 'Quebec reserves naturelles'],
}
for cc in DIRECT:
    rows = []
    for u in DIRECT[cc]:
        st, t = fetch(u)
        info = ''
        if st == 200 and t.lstrip().startswith('{'):
            try:
                j = json.loads(t); info = 'layers: ' + ', '.join(f"{l.get('id')}:{l.get('name')}" for l in (j.get('layers') or [])[:25]) or ('services: ' + ', '.join(s.get('name', '') for s in (j.get('services') or [])[:40]))
            except Exception: info = 'json?'  # noqa: BLE001
        elif st == 200:
            names = re.findall(r'<(?:wfs:)?Name>([^<]{2,80})</(?:wfs:)?Name>', t); names = ([n for n in names if re.search(r'PROTECT|ZNIEFF|znieff|RB|forest|parc', n, re.I)] or names)[:40]
            info = ('types: ' + ', '.join(names)) if names else re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t))[:200]
        rows.append({'url': u, 'status': st, 'info': info})
        time.sleep(1)
    hits = []
    for q in SEARCH[cc]:
        st, t = fetch('https://www.arcgis.com/sharing/rest/search?' + urllib.parse.urlencode({'q': f'{q} type:("Feature Service" OR "Map Service")', 'num': 8, 'f': 'json', 'sortField': 'numviews', 'sortOrder': 'desc'}))
        try:
            for r in json.loads(t).get('results', []):
                hits.append({'q': q, 'title': r.get('title'), 'owner': r.get('owner'), 'url': r.get('url'), 'views': r.get('numViews')})
        except Exception: pass  # noqa: BLE001
        time.sleep(1)
    OUT[cc] = {'direct': rows, 'search': hits}
    notice(f'Probe {cc} direct', '\n'.join(f"{r['status']} {r['url']} · {r['info'][:300]}" for r in rows))
    notice(f'Probe {cc} ArcGIS', '\n'.join(f"[{h['q']}] {h['title']} · {h['owner']} · {h['url']}" for h in hits[:24]))
json.dump(OUT, open('data/world-probe.json', 'w'), indent=1, ensure_ascii=False)
