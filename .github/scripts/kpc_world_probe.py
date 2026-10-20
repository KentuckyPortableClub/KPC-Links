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


DIRECT = {   # Oct 20 round 5: layer lists of agency servers we already trust, to find the missing groups
    'WA': ['https://geodataservices.wdfw.wa.gov/arcgis/rest/services/MapServices?f=json', 'https://geodataservices.wdfw.wa.gov/arcgis/rest/services/MapServices/WildlifeAreas/MapServer?f=json'],
    'ID': ['https://services.arcgis.com/FjJI5xHF2dUPVrgK/arcgis/rest/services?f=json'],
    'MO': ['https://gisblue.mdc.mo.gov/arcgis/rest/services?f=json', 'https://gis.mdc.mo.gov/arcgis/rest/services?f=json'],
    'QC': ['https://geo.environnement.gouv.qc.ca/donnees/rest/services/Biodiversite/Aires_protegees/MapServer?f=json'],
    'ON': ['https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open03/MapServer?f=json', 'https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open01/MapServer?f=json'],
}
SEARCH = {'WA': ['WDFW water access areas'], 'ID': [], 'MO': ['Missouri Department of Conservation areas MDC lands'], 'QC': ['parcs regionaux du Quebec'],
          'ON': ['Ontario conservation authority properties conservation lands'],
          'MS': ['MDWFP wildlife management areas'], 'KS': ['KDWP public lands wildlife areas Kansas']}
for _k in SEARCH: DIRECT.setdefault(_k, [])
for cc in DIRECT:
    rows = []
    for u in DIRECT[cc]:
        st, t = fetch(u)
        info = ''
        if st == 200 and t.lstrip().startswith('{'):
            try:
                j = json.loads(t); info = ('name: ' + str(j.get('name')) + ' fields: ' + ', '.join(f.get('name','') for f in (j.get('fields') or [])[:30]) + ' | ' if j.get('fields') else '') + 'layers: ' + ', '.join(f"{l.get('id')}:{l.get('name')}" for l in (j.get('layers') or [])[:60]) or ('services: ' + ', '.join(s.get('name', '') for s in (j.get('services') or [])[:120]))
            except Exception: info = 'json?'  # noqa: BLE001
        elif st == 200:
            names = re.findall(r'<(?:wfs:)?Name>([^<]{2,80})</(?:wfs:)?Name>', t); names = ([n for n in names if re.search(r'ZNIEFF|PROTECTEDAREAS', n, re.I)] or names)[:60]
            info = ('types: ' + ', '.join(names)) if names else re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t))[:200]
        rows.append({'url': u, 'status': st, 'info': info})
        time.sleep(1)
    hits = []
    for q in SEARCH[cc]:
        st, t = fetch('https://www.arcgis.com/sharing/rest/search?' + urllib.parse.urlencode({'q': f'{q} type:("Feature Service" OR "Map Service")', 'num': 6, 'f': 'json', 'sortField': 'numviews', 'sortOrder': 'desc'}))
        try:
            for r in json.loads(t).get('results', []):
                hits.append({'q': q, 'title': r.get('title'), 'owner': r.get('owner'), 'url': r.get('url'), 'views': r.get('numViews')})
        except Exception: pass  # noqa: BLE001
        time.sleep(1)
    OUT[cc] = {'direct': rows, 'search': hits}
    notice(f'Probe {cc} direct', '\n'.join(f"{r['status']} {r['url']} · {r['info'][:300]}" for r in rows))
    notice(f'Probe {cc} ArcGIS', '\n'.join(f"[{h['q']}] {h['title']} · {h['owner']} · {h['url']}" for h in hits[:24]))
json.dump(OUT, open('data/world-probe.json', 'w'), indent=1, ensure_ascii=False)
