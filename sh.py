import urllib.request,urllib.parse,json,time
bb=json.load(open('bb.json'))
for n,b in bb.items():
  if 'Ramp' in n: continue
  q='[out:json][timeout:40];(nwr[leisure=slipway](%f,%f,%f,%f);nwr[amenity=parking](%f,%f,%f,%f);nwr[leisure=fishing](%f,%f,%f,%f););out tags center 60;'%(tuple(b)*3)
  for u in ['https://overpass-api.de/api/interpreter','https://overpass.private.coffee/api/interpreter']:
    try:
      j=json.loads(urllib.request.urlopen(urllib.request.Request(u,data=('data='+urllib.parse.quote(q)).encode(),headers={'User-Agent':'KPC'}),timeout=60).read())
      el=j['elements'];T=lambda e:e.get('tags',{})
      c=lambda e:(round(e.get('lat') or e.get('center',{}).get('lat'),5),round(e.get('lon') or e.get('center',{}).get('lon'),5))
      ramps=[(T(e).get('name',''),c(e)) for e in el if T(e).get('leisure')=='slipway']
      park=[e for e in el if T(e).get('amenity')=='parking' and T(e).get('access') not in ('private','no')]
      pier=[e for e in el if T(e).get('leisure')=='fishing']
      print(n,'| ramps',len(ramps),ramps[:3],'| parking',len(park),'| fishing spots',len(pier));break
    except Exception as e: print(n,u,'ERR',e)
  time.sleep(2)
