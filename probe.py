import urllib.request, json, urllib.parse
out=[]
B='https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/'
def g(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent':'KPC probe','Origin':'https://kentuckyportableclub.github.io'}), timeout=60)
        return r.status, r.headers.get('Access-Control-Allow-Origin'), r.read()
    except Exception as e: return 'ERR', None, str(e).encode()
for lay in [3,4]:
    s,c,b=g(B+f'CDDA_Dyna_WM/MapServer/{lay}?f=json')
    try: j=json.loads(b); out.append(f'CDDA/{lay} {j.get("name")} geom {j.get("geometryType")} minScale {j.get("minScale")} fields: '+', '.join(f["name"] for f in j.get('fields',[]))[:600])
    except Exception: out.append(f'CDDA/{lay} {s} '+b[:200].decode())
for la,lo in [(48.95,13.42),(37.0,-6.45),(52.07,5.82),(50.73,7.2),(45.2,6.9)]:
    for lay in [3,4]:
        q=urllib.parse.urlencode({'geometry':f'{lo},{la}','geometryType':'esriGeometryPoint','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'siteName,designationTypeCode,iucnCategory,siteArea,countryCode,OBJECTID,nationalId','returnGeometry':'false','f':'json'})
        s,c,b=g(B+f'CDDA_Dyna_WM/MapServer/{lay}/query?'+q)
        try: j=json.loads(b); out.append(f'PT {la},{lo} CDDA/{lay}: '+json.dumps([f['attributes'] for f in j.get('features',[])], ensure_ascii=False)[:500]+(' ERR '+json.dumps(j.get('error')) if j.get('error') else ''))
        except Exception: out.append(f'PT CDDA/{lay} {s} '+b[:300].decode('utf-8','replace'))
# name LIKE query + geojson geometry
for svc,lay,fld,nm in [('Natura2000Sites',2,'SITENAME','Bayerischer Wald'),('CDDA_Dyna_WM',4,'siteName','Bayerischer Wald')]:
    q=urllib.parse.urlencode({'where':f"{fld} LIKE '%{nm}%'",'outFields':fld,'returnGeometry':'true','outSR':4326,'maxAllowableOffset':0.0005,'f':'geojson','resultRecordCount':3})
    s,c,b=g(B+f'{svc}/MapServer/{lay}/query?'+q)
    try: j=json.loads(b); f=j.get('features',[]); out.append(f'LIKE {svc}/{lay}: {s} cors={c} n={len(f)} bytes={len(b)} first={json.dumps(f[0]["properties"],ensure_ascii=False) if f else ""} geom={f[0]["geometry"]["type"] if f and f[0].get("geometry") else None} pts={len(json.dumps(f[0]["geometry"])) if f else 0}'+(' ERR '+json.dumps(j.get('error')) if isinstance(j,dict) and j.get('error') else ''))
    except Exception as e: out.append(f'LIKE {svc} {s} {e} '+b[:300].decode('utf-8','replace'))
# POTA: a German + Spanish park pin and name, to compare
for ref in ['DE-0001','DE-0577','ES-0010','IT-0001','FR-0001','PL-0001','GB-0001','SE-0001']:
    s,c,b=g('https://api.pota.app/park/'+ref)
    try: j=json.loads(b); out.append(f'{ref}: {j.get("name")} | {j.get("parktypeDesc")} | {j.get("latitude")},{j.get("longitude")} | web {j.get("website")}')
    except Exception: out.append(ref+' '+str(s))
open('out.txt','w').write('\n'.join(out))
