import urllib.request,urllib.parse,json
H={'User-Agent':'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/129 Mobile Safari/537.36','Origin':'https://kentuckyportableclub.github.io','Accept':'*/*'}
def get(u):
  try: return urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60).read().decode('utf8','replace')
  except Exception as e: return 'ERR '+str(e)
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query?'
st=json.dumps([{'statisticType':'count','onStatisticField':'OBJECTID','outStatisticFieldName':'n'}])
r=get(P+urllib.parse.urlencode(dict(where="State_Nm='KY' AND Mang_Type<>'LOC'",groupByFieldsForStatistics='Mang_Type,Mang_Name,Loc_Mang,Category',outStatistics=st,f='json')))
print('agency', r[:100], r.count('"n"'))
for w in ["Unit_Nm LIKE '%Kingfisher%'","Loc_Nm LIKE '%KINGFISHER%'"]:
  print(w, get(P+urllib.parse.urlencode(dict(where=w,geometry='-87.3,37.5,-86.6,38.2',geometryType='esriGeometryEnvelope',inSR=4326,spatialRel='esriSpatialRelIntersects',outFields='Unit_Nm',returnGeometry='true',outSR=4326,geometryPrecision=5,maxAllowableOffset=0.0001,f='geojson')))[:200])
print('kygis upper', get('https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Hunting_Areas_WGS84WM/MapServer/0/query?'+urllib.parse.urlencode(dict(where="UPPER(AREANAME) LIKE '%BARREN%' AND UPPER(AREANAME) LIKE '%LAKE%'",outFields='AREANAME',returnGeometry='false',f='json')))[:300])
