import json,urllib.request,urllib.parse,re
def get(u,t=180):
    return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'KPC-Links park research'}),timeout=t).read())
KY='https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_24K_NHD_Waterbodies_WGS84WM/MapServer'
m=get(KY+'?f=json'); print([(l['id'],l['name']) for l in m['layers']])
out={}
PTS={'Bullock Pen Lake':(38.7930,-84.6448),'Boltz Lake':(38.7036,-84.6143),'Guist Creek Lake':(38.2072,-85.1414),'Lake Linville':(37.3886,-84.3456),'Wilgreen Lake':(37.7083,-84.35),'Wood Creek Lake':(37.188,-84.18),'Beaver Lake':(37.9636,-85.0224),'Kingfisher Lakes':(37.8456,-86.9752),'Carpenter Lake':(37.8465,-86.979)}
for l in m['layers']:
    if l.get('subLayerIds'): continue
    lf=get(KY+'/%d?f=json'%l['id']); print(l['id'],[f['name'] for f in lf.get('fields',[])])
    for n,(la,lo) in PTS.items():
        q={'geometry':'%f,%f,%f,%f'%(lo-.03,la-.03,lo+.03,la+.03),'geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'*','outSR':4326,'geometryPrecision':6,'f':'geojson'}
        try:
            g=get(KY+'/%d/query?'%l['id']+urllib.parse.urlencode(q))
            fs=[f for f in g['features'] if re.search(n.split()[0] if n!='Lake Linville' else 'Linville',json.dumps(f['properties']),re.I)]
            print(' ',n,len(g['features']),'named',[{k:v for k,v in f['properties'].items() if k.upper() in('GNIS_NAME','AREASQKM','FTYPE','GNIS_ID','NAME')} for f in fs])
            out.setdefault(n,[]).extend(fs)
        except Exception as e: print(' ',n,e)
# OSM fallback for Boltz + anything missing: water polygons near the point
EP=['https://overpass-api.de/api/interpreter','https://overpass.private.coffee/api/interpreter']
for n,(la,lo) in PTS.items():
    q='[out:json][timeout:90];(way(around:900,%f,%f)[natural=water];relation(around:900,%f,%f)[natural=water];);out geom;'%(la,lo,la,lo)
    for k in range(4):
        try:
            o=json.loads(urllib.request.urlopen(urllib.request.Request(EP[k%2],data=urllib.parse.urlencode({'data':q}).encode(),headers={'User-Agent':'KPC'}),timeout=120).read()); out['osm_'+n]=o; print('osm',n,[(e['type'],e['id'],e.get('tags',{}).get('name')) for e in o['elements']]); break
        except Exception as e: print('osm',n,e)
json.dump(out,open('fut3.json','w'))
