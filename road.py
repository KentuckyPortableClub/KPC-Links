import json,urllib.request,urllib.parse,time
q='[out:json][timeout:90];way(around:1500,36.9632,-83.1092)[highway];out geom;'
EP=['https://overpass-api.de/api/interpreter','https://overpass.private.coffee/api/interpreter','https://maps.mail.ru/osm/tools/overpass/api/interpreter']
for k in range(9):
    try:
        j=json.load(urllib.request.urlopen(urllib.request.Request(EP[k%3],data=urllib.parse.urlencode({'data':q}).encode(),headers={'User-Agent':'KPC'}),timeout=120));break
    except Exception as e: print(e);time.sleep(10);j=None
json.dump(j,open('road.json','w'))
