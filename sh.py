import urllib.request,urllib.parse,json
H={'User-Agent':'Mozilla/5.0 (Linux; Android 14) Chrome/129 Mobile','Origin':'https://kentuckyportableclub.github.io'}
def get(u,data=None):
  try: return json.loads(urllib.request.urlopen(urllib.request.Request(u,data=data,headers=H),timeout=90).read())
  except Exception as e: return {'ERR':str(e)}
j=get('https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0?f=json'); print('PAD fields',[f['name'] for f in j.get('fields',[])])
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query?'
for w in ["State_Nm='KY' AND Unit_Nm LIKE '%Wood Creek%'","State_Nm='KY' AND Loc_Nm LIKE '%WOOD CREEK%'"]:
  j=get(P+urllib.parse.urlencode(dict(where=w,outFields='Unit_Nm,Loc_Nm,Own_Type,Loc_Mang,GIS_Acres',returnGeometry='false',f='json'))); print(w, j.get('ERR') or [f['attributes'] for f in j.get('features',[])])
la,lo=37.214088,-84.197804
q=f'[out:json][timeout:30];(is_in({la},{lo});)->.a;(area.a[name];)->.b;.b out tags;(nwr(around:1200,{la},{lo})[name][~"^(natural|water|leisure|boundary|landuse)$"~"^(water|reservoir|lake|park|nature_reserve|protected_area|national_park|recreation_ground)$"];);out tags center 30;'
j=get('https://overpass-api.de/api/interpreter',('data='+urllib.parse.quote(q)).encode()); print('OSM', j.get('ERR') or [(e.get('type'),e['tags'].get('name'),{k:v for k,v in e['tags'].items() if k in('natural','water','leisure','boundary','landuse','operator','owner','website','protect_class')}) for e in j.get('elements',[])][:25])
for u in ['https://www.fws.gov/refuge/clarks-river','https://www.fws.gov/refuge/clarks-river/map','https://www.fws.gov/refuge/clarks-river/visit-us']:
  try: r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) Chrome/129'}),timeout=30); print(u,r.status)
  except Exception as e: print(u,e)
