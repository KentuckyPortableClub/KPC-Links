import urllib.request,urllib.parse,json
H={'User-Agent':'Mozilla/5.0 (Linux; Android 14) Chrome/129 Mobile','Origin':'https://kentuckyportableclub.github.io'}
def get(u):
  try: return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60).read())
  except Exception as e: return {'ERR':str(e)}
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query?'
la,lo=37.214088,-84.197804
for d in [0,.004,.02]:
  g=dict(geometry=f'{lo},{la}',geometryType='esriGeometryPoint') if not d else dict(geometry=f'{lo-d},{la-d},{lo+d},{la+d}',geometryType='esriGeometryEnvelope')
  j=get(P+urllib.parse.urlencode(dict(g,inSR=4326,spatialRel='esriSpatialRelIntersects',where="State_Nm='KY'",outFields='Unit_Nm,Own_Type,Mang_Name,Loc_Mang,Category,GIS_Acres',returnGeometry='false',f='json')))
  print(d, j.get('ERR') or [ (f['attributes']['Unit_Nm'],f['attributes']['Own_Type'],f['attributes']['Loc_Mang'],f['attributes']['Category']) for f in j.get('features',[])][:12])
print(get(f'https://geo.fcc.gov/api/census/area?lat={la}&lon={lo}&format=json').get('results',[{}])[0].get('county_name'))
print(json.dumps(get('https://nominatim.openstreetmap.org/reverse?'+urllib.parse.urlencode(dict(lat=la,lon=lo,format='jsonv2',zoom=16))))[:400])
for svc in ['Ky_Public_Hunting_Areas_WGS84WM/MapServer/1','Ky_State_Parks_Features_WGS84WM/MapServer/8','Ky_KNP_State_Nature_Preserves_WGS84WM/MapServer/0']:
  j=get('https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/'+svc+'/query?'+urllib.parse.urlencode(dict(geometry=f'{lo-.01},{la-.01},{lo+.01},{la+.01}',geometryType='esriGeometryEnvelope',inSR=4326,spatialRel='esriSpatialRelIntersects',outFields='*',returnGeometry='false',f='json')))
  print(svc, j.get('ERR') or [ {k:v for k,v in f['attributes'].items() if k in ('AREANAME','PUBLIC_NAM','MANAME','DETAIL')} for f in j.get('features',[])][:5])
