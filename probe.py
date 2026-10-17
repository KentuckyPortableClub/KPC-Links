import urllib.request, json, urllib.parse
out=[]
B='https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/'
def g(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent':'KPC probe','Origin':'https://kentuckyportableclub.github.io'}), timeout=60)
        return r.status, r.headers.get('Access-Control-Allow-Origin'), r.read()
    except Exception as e: return 'ERR', None, str(e).encode()
for svc in ['CDDA_Dyna_WM','NatDAv22_Dyna_WM','Natura2000Sites']:
    s,c,b=g(B+svc+'/MapServer?f=json')
    try: j=json.loads(b); out.append(f'{svc} layers: '+json.dumps([(l['id'],l['name']) for l in j.get('layers',[])]))
    except Exception: out.append(svc+' '+str(s)+' '+b[:200].decode('utf-8','replace'))
for svc,lay in [('CDDA_Dyna_WM',0),('NatDAv22_Dyna_WM',0),('Natura2000Sites',2),('Natura2000Sites',0)]:
    s,c,b=g(B+f'{svc}/MapServer/{lay}?f=json')
    try: j=json.loads(b); out.append(f'{svc}/{lay} {j.get("name")} fields: '+', '.join(f["name"] for f in j.get('fields',[])) + f' maxRecord {j.get("maxRecordCount")}')
    except Exception: out.append(f'{svc}/{lay} '+str(s)+' '+b[:200].decode('utf-8','replace'))
# point queries: Bayerischer Wald NP (48.95,13.42), Doñana (37.0,-6.45), Hoge Veluwe (52.07,5.82)
for la,lo in [(48.95,13.42),(37.0,-6.45),(52.07,5.82),(54.45,-3.08)]:
    for svc,lay in [('CDDA_Dyna_WM',0),('NatDAv22_Dyna_WM',0),('Natura2000Sites',2),('Natura2000Sites',0),('Natura2000Sites',1)]:
        q=urllib.parse.urlencode({'geometry':f'{lo},{la}','geometryType':'esriGeometryPoint','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'*','returnGeometry':'false','f':'json'})
        s,c,b=g(B+f'{svc}/MapServer/{lay}/query?'+q)
        try: j=json.loads(b); out.append(f'PT {la},{lo} {svc}/{lay}: {s} cors={c} '+json.dumps([f['attributes'] for f in j.get('features',[])][:3], ensure_ascii=False)[:700] + (' ERR '+json.dumps(j.get('error')) if j.get('error') else ''))
        except Exception: out.append(f'PT {svc}/{lay} {s} '+b[:300].decode('utf-8','replace'))
open('out.txt','w').write('\n'.join(out))
