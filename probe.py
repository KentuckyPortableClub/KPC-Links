import json,urllib.request,urllib.parse,re
UA={'User-Agent':'KPC-Links/1.0'}
def get(u,raw=False):
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60) as r:
            b=r.read().decode('utf-8','replace'); return b if raw else json.loads(b)
    except Exception as e: return 'ERR '+str(e)[:150]
def note(t,m): print(f'::notice title={t}::'+str(m).replace('\n',' ')[:1500],flush=True)
def svc(u):
    j=get(u+'?f=json')
    if isinstance(j,str): note('svc '+u[-60:],j); return
    lays=j.get('layers') or []
    note('layers '+u[-70:],'; '.join(f"{l['id']}:{l['name']}" for l in lays)[:1500])
    for l in lays[:25]:
        if l.get('subLayerIds'): continue
        i=get(f"{u}/{l['id']}?f=json")
        if isinstance(i,str) or 'Polygon' not in str(i.get('geometryType')): continue
        note(f"fields {l['id']} {l['name'][:40]}",', '.join(f['name'] for f in i.get('fields',[]))[:600]+' | fmt '+str(i.get('supportedQueryFormats')))
svc('https://geospatial.alberta.ca/titan/rest/services/boundary/parks_protected_areas_alberta/FeatureServer')
svc('https://geo.environnement.gouv.qc.ca/donnees/rest/services/Biodiversite/Aires_protegees/MapServer')
q=get('https://www.publicdocs.mnr.gov.on.ca/mirb/lio-open-qlr-eng/provincial-park-regulated.qlr',True)
note('ON qlr',' '.join(set(re.findall(r'https?://[^"\s<>&]+',q if isinstance(q,str) else ''))))
for m in set(re.findall(r'(https?://[^"\s<>&]*?/MapServer)',q if isinstance(q,str) else '')): svc(m)
# BC WFS
b=get('https://openmaps.gov.bc.ca/geo/pub/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=WHSE_TANTALIS.TA_PARK_ECORES_PA_SVW&count=1&outputFormat=json&srsName=EPSG:4326')
note('BC parks',(json.dumps(b['features'][0]['properties'])[:900]+' geom '+b['features'][0]['geometry']['type']) if isinstance(b,dict) and b.get('features') else b)
b=get('https://openmaps.gov.bc.ca/geo/pub/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=WHSE_FOREST_TENURE.FTEN_RECREATION_POLY_SVW&count=1&outputFormat=json&srsName=EPSG:4326')
note('BC rec',(json.dumps(b['features'][0]['properties'])[:900]) if isinstance(b,dict) and b.get('features') else b)
b=get("https://openmaps.gov.bc.ca/geo/pub/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=WHSE_TANTALIS.TA_PARK_ECORES_PA_SVW&count=3&outputFormat=json&srsName=EPSG:4326&CQL_FILTER="+urllib.parse.quote("INTERSECTS(SHAPE,POINT(49.3 -123.1))"))
note('BC cql',b if isinstance(b,str) else len(b.get('features',[])))
# ArcGIS Online search
for qq in ['National Historic Sites Parks Canada boundaries','Parks Canada administered places boundaries','Saskatchewan provincial parks boundaries','Manitoba provincial parks boundaries','Nova Scotia provincial parks boundaries','New Brunswick provincial parks','Newfoundland provincial parks boundaries','Ontario provincial park regulated']:
    s=get('https://www.arcgis.com/sharing/rest/search?f=json&num=8&q='+urllib.parse.quote(qq+' type:"Feature Service"'))
    if isinstance(s,dict): note('AGOL '+qq[:40],' || '.join(f"{r['title']} [{r.get('owner')}] {r.get('url')}" for r in s.get('results',[]))[:1500])
