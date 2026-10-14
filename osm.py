import json,urllib.request,urllib.parse,time
P={'US-3802':(38.1355,-84.8549),'US-10173':(38.1498,-84.5199),'US-1264':(37.0838,-84.0549),'US-10172':(38.1777,-84.9231),'US-3787':(37.8332,-84.3527),'US-10099':(36.8727,-85.1456)}
out={}
for r,(la,lo) in P.items():
    q=f'[out:json][timeout:60];(way(around:2500,{la},{lo})[~"^(leisure|boundary|landuse|tourism|historic|protect_class|amenity|man_made)$"~"."][name];relation(around:2500,{la},{lo})[~"^(leisure|boundary|landuse|tourism|historic)$"~"."][name];);out geom;'
    for ep in ['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter']:
        try:
            j=json.load(urllib.request.urlopen(urllib.request.Request(ep,data=urllib.parse.urlencode({'data':q}).encode(),headers={'User-Agent':'KPC'}),timeout=90));break
        except Exception as e: print(r,ep,e); j=None
    out[r]=j; print(r,len((j or {}).get('elements',[])) ); time.sleep(3)
json.dump(out,open('osm.json','w'))
