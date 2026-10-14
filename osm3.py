import json,urllib.request,urllib.parse,time
Q={'US-10098':'[out:json][timeout:120];(way(around:9000,37.8999,-87.5281)["name"~"Green River",i]["boundary"];relation(around:9000,37.8999,-87.5281)["name"~"Green River",i];way(around:9000,37.8999,-87.5281)["name"~"Green River National",i];);out geom;',
   'US-3789':'[out:json][timeout:120];(way(around:3000,37.4681,-84.5493)["name"~"Whitley",i];relation(around:3000,37.4681,-84.5493)["name"~"Whitley",i];way(around:800,37.4681,-84.5493)[~"^(leisure|boundary|historic|tourism)$"~"."];);out geom;'}
EP=['https://overpass-api.de/api/interpreter','https://overpass.private.coffee/api/interpreter','https://maps.mail.ru/osm/tools/overpass/api/interpreter']
out={}
for r,q in Q.items():
    for k in range(9):
        try: out[r]=json.load(urllib.request.urlopen(urllib.request.Request(EP[k%3],data=urllib.parse.urlencode({'data':q}).encode(),headers={'User-Agent':'KPC-Links'}),timeout=150));print(r,'ok',len(out[r]['elements']));break
        except Exception as e: print(r,e);time.sleep(10)
json.dump(out,open('osm3.json','w'))
