import json,urllib.request,urllib.parse,time
out={}
def get(u,data=None,t=120):
    return json.load(urllib.request.urlopen(urllib.request.Request(u,data=data,headers={'User-Agent':'KPC-Links boundary check'}),timeout=t))
# White Hall + Salato from OSM (around pins)
Q={'US-3787':'[out:json][timeout:120];(way(around:2500,37.8332,-84.3527)[~"^(leisure|boundary|landuse|historic|tourism)$"~"."];relation(around:2500,37.8332,-84.3527)[~"^(leisure|boundary|historic|tourism)$"~"."];);out geom;',
   'US-10172':'[out:json][timeout:120];(way(around:2500,38.1777,-84.9231)[~"^(leisure|boundary|landuse|historic|tourism)$"~"."];relation(around:2500,38.1777,-84.9231)[~"^(leisure|boundary|landuse)$"~"."];);out geom;'}
EP=['https://overpass-api.de/api/interpreter','https://overpass.private.coffee/api/interpreter','https://maps.mail.ru/osm/tools/overpass/api/interpreter']
for r,q in Q.items():
    for k in range(6):
        try: out[r]=get(EP[k%3],urllib.parse.urlencode({'data':q}).encode(),180); print(r,'osm ok',len(out[r]['elements'])); break
        except Exception as e: print(r,'osm',e); time.sleep(15)
# PAD-US (Esri Living Atlas) around the 6 pins
PINS={'US-3802':(38.1355,-84.8549),'US-10173':(38.1498,-84.5199),'US-1264':(37.0838,-84.0549),'US-10172':(38.1777,-84.9231),'US-3787':(37.8332,-84.3527),'US-10099':(36.8727,-85.1456)}
for svc in ['USA_Protected_Areas_Fee_Manager','USA_Protected_Areas_Manager_Name','USA_Protected_Areas_Fee']:
    base=f'https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/{svc}/FeatureServer/0/query'
    ok=False
    for r,(la,lo) in PINS.items():
        qs=urllib.parse.urlencode({'where':'1=1','geometry':f'{lo-.02},{la-.02},{lo+.02},{la+.02}','geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'*','outSR':4326,'f':'geojson'})
        try: j=get(base+'?'+qs,None,90); out['padus_'+r]=j; ok=True; print(svc,r,len(j.get('features',[])),[ (f['properties'].get('Unit_Nm') or f['properties'].get('UNIT_NM')) for f in j.get('features',[])][:8])
        except Exception as e: print(svc,r,e); break
    if ok: break
json.dump(out,open('more.json','w'))
