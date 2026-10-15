import urllib.request,urllib.parse
H={'User-Agent':'Mozilla/5.0 (Linux; Android 14) Chrome/129 Mobile','Origin':'https://kentuckyportableclub.github.io','Accept':'*/*'}
def get(u):
  try: r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60); return str(r.status)+' '+r.read().decode('utf8','replace')
  except Exception as e: return 'ERR '+str(e)
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query?'
F='OBJECTID,Unit_Nm,Loc_Nm,Mang_Type,Mang_Name,Loc_Mang,Own_Type,Own_Name,Loc_Own,Des_Tp,Loc_Ds,Pub_Access,GIS_Acres,State_Nm,Category,Date_Est,Comments'
la,lo=37.8452,-86.9755
print('point', get(P+urllib.parse.urlencode(dict(outFields=F,returnGeometry='false',f='json',geometry=f'{lo},{la}',geometryType='esriGeometryPoint',inSR=4326,spatialRel='esriSpatialRelIntersects',where="State_Nm='KY'")))[:60].count('Unit_Nm'), get(P+urllib.parse.urlencode(dict(outFields=F,returnGeometry='false',f='json',geometry=f'{lo},{la}',geometryType='esriGeometryPoint',inSR=4326,spatialRel='esriSpatialRelIntersects',where="State_Nm='KY'")))[-300:])
d=.004
r=get(P+urllib.parse.urlencode(dict(outFields=F,returnGeometry='false',f='json',geometry=f'{lo-d},{la-d},{lo+d},{la+d}',geometryType='esriGeometryEnvelope',inSR=4326,spatialRel='esriSpatialRelIntersects',where="State_Nm='KY'",resultRecordCount=80)))
print('env', r[:4], r.count('"Unit_Nm":'))
print('fcc', get(f'https://geo.fcc.gov/api/census/area?lat={la}&lon={lo}&format=json')[:200])
print('nom', get('https://nominatim.openstreetmap.org/search?'+urllib.parse.urlencode(dict(q='Kingfisher Lakes, Maceo, KY',format='jsonv2',countrycodes='us',addressdetails=1,limit=1)))[:300])
