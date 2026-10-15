import urllib.request,urllib.parse,json,time
def get(u,data=None,h=None):
    t=time.time()
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,data=data,headers=h or {'User-Agent':'KPC test','Origin':'https://kentuckyportableclub.github.io'}),timeout=40)
        b=r.read(); return r.status,b,round(time.time()-t,1),r.headers.get('Access-Control-Allow-Origin')
    except Exception as e: return 'ERR',str(e).encode(),round(time.time()-t,1),None
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
for nm,la,lo in [('FortYargo',33.975,-83.735),('MammothCave',37.19,-86.10),('DBNF',37.8,-83.68),('BarrenRiver',36.86,-86.05),('town',38.2,-84.87)]:
    q={'geometry':f'{lo},{la}','geometryType':'esriGeometryPoint','inSR':4326,'spatialRel':'esriSpatialRelIntersects','where':'1=1','outFields':'Unit_Nm,Loc_Nm,Mang_Name,Loc_Mang,Des_Tp,Pub_Access,GIS_Acres,Category','returnGeometry':'true','outSR':4326,'geometryPrecision':5,'maxAllowableOffset':0.00005,'f':'geojson'}
    s,b,t,c=get(P+'?'+urllib.parse.urlencode(q))
    try:
        j=json.loads(b);print(nm,s,t,'s','cors',c,len(b),'bytes',[(f['properties']['Unit_Nm'],f['properties']['Pub_Access'],f['properties'].get('Category'),f['properties']['Des_Tp']) for f in j.get('features',[])])
    except Exception as e: print(nm,s,t,b[:300])
    q.update({'geometry':f'{lo-.03},{la-.03},{lo+.03},{la+.03}','geometryType':'esriGeometryEnvelope','returnGeometry':'false'})
    s,b,t,c=get(P+'?'+urllib.parse.urlencode(q));
    try: j=json.loads(b);print('  near',t,len(j.get('features',[])),sorted(set(f['properties']['Unit_Nm'] for f in j['features']))[:12])
    except Exception: print('  near',s,b[:200])
for u in ['https://api.pota.app/park/grids/37.1/-86.2/37.3/-86.0/0','https://api.pota.app/lookup?search=Mammoth%20Cave&size=10']:
    s,b,t,c=get(u);print(u,s,t,c,b[:600])
