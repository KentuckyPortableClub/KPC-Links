import urllib.request,urllib.parse,json
def get(u): 
  try: return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 KPC'}),timeout=40).read().decode('utf8','replace')
  except Exception as e: return 'ERR '+str(e)
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query?'
for x0,y0,x1,y1 in [(-86.995,37.835,-86.96,37.855)]:
  q=dict(geometry=f'{x0},{y0},{x1},{y1}',geometryType='esriGeometryEnvelope',inSR=4326,spatialRel='esriSpatialRelIntersects',outFields='OBJECTID,Unit_Nm,Loc_Nm,Own_Name,Own_Type,Mang_Name,Pub_Access,Des_Tp,GIS_Acres,State_Nm',returnGeometry='false',f='json')
  print('PAD box:',get(P+urllib.parse.urlencode(q))[:3000])
for w in ["UPPER(Unit_Nm) LIKE '%KINGFISHER%'","UPPER(Loc_Nm) LIKE '%KINGFISHER%'","Unit_Nm LIKE '%Kingfisher%'"]:
  print('PAD where',w,':',get(P+urllib.parse.urlencode(dict(where=w,outFields='Unit_Nm,Loc_Nm,State_Nm,Mang_Name',returnGeometry='false',f='json')))[:800])
