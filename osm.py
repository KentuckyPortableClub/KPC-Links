import json,urllib.request,urllib.parse,time
P={'US-3802':(38.1355,-84.8549,'Buckley'),'US-10173':(38.1498,-84.5199,'Horse Park'),'US-1264':(37.0838,-84.0549,'Levi Jackson'),'US-10172':(38.1777,-84.9231,'Salato|Game Farm|Fish and Wildlife'),'US-3787':(37.8332,-84.3527,'White Hall'),'US-10099':(36.8727,-85.1456,'Hatchery|Wolf Creek')}
EP=['https://overpass-api.de/api/interpreter','https://overpass.private.coffee/api/interpreter','https://maps.mail.ru/osm/tools/overpass/api/interpreter','https://overpass.kumi.systems/api/interpreter']
out={}
for r,(la,lo,nm) in P.items():
    q=f'[out:json][timeout:90];(way(around:4000,{la},{lo})["name"~"{nm}",i];relation(around:4000,{la},{lo})["name"~"{nm}",i];way(around:1500,{la},{lo})[~"^(leisure|boundary|landuse)$"~"."];);out geom;'
    j=None
    for k in range(8):
        ep=EP[k%len(EP)]
        try:
            j=json.load(urllib.request.urlopen(urllib.request.Request(ep,data=urllib.parse.urlencode({'data':q}).encode(),headers={'User-Agent':'KPC-Links boundary check'}),timeout=120)); print(r,'ok',ep,len(j.get('elements',[]))); break
        except Exception as e: print(r,ep,e); time.sleep(10)
    out[r]=j; time.sleep(5)
json.dump(out,open('osm.json','w'))
