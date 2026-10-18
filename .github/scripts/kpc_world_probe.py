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
            b = r.read(400000)
            return r.status, (b if raw else b.decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e: return e.code, ''
    except Exception as e: return 0, str(e)[:120]  # noqa: BLE001


DIRECT = {
    'AU': ['https://gis.environment.gov.au/gispubmap/rest/services/ogc_services/CAPAD/MapServer?f=json',
           'https://gis.environment.gov.au/gispubmap/rest/services?f=json'],
    'DE': ['https://geodienste.bfn.de/ogc/wfs/schutzgebiet?SERVICE=WFS&REQUEST=GetCapabilities',
           'https://geodienste.bfn.de/ogc/wms/schutzgebiet?SERVICE=WMS&REQUEST=GetCapabilities'],
    'PL': ['https://sdi.gdos.gov.pl/wfs?SERVICE=WFS&REQUEST=GetCapabilities',
           'https://sdi.gdos.gov.pl/wms?SERVICE=WMS&REQUEST=GetCapabilities'],
    'GB': ['https://services.arcgis.com/JJzESW51TqeY9uat/arcgis/rest/services?f=json',
           'https://environment.data.gov.uk/spatialdata/national-nature-reserves-england/wfs?SERVICE=WFS&REQUEST=GetCapabilities',
           'https://ogc.nature.scot/geoserver/protectedareas/wfs?SERVICE=WFS&REQUEST=GetCapabilities'],
    'JP': ['https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A10-v3_1.html',
           'https://www.biodic.go.jp/trialSystem/top.html'],
}
SEARCH = {
    'AU': ['CAPAD terrestrial', 'Collaborative Australian Protected Areas Database'],
    'DE': ['Naturschutzgebiete Deutschland', 'Schutzgebiete BfN', 'Landschaftsschutzgebiete'],
    'PL': ['parki krajobrazowe', 'rezerwaty przyrody GDOS', 'formy ochrony przyrody'],
    'GB': ['National Nature Reserves England', 'Country Parks England', 'Sites of Special Scientific Interest England', 'NatureScot protected areas', 'Natural Resources Wales protected'],
    'JP': ['Japan national parks boundary', '国立公園', '自然公園地域', 'quasi-national park Japan'],
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
            names = re.findall(r'<(?:wfs:)?Name>([^<]{2,80})</(?:wfs:)?Name>', t)[:30]
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
