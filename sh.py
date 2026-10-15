import urllib.request,urllib.parse
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
for w in ["UPPER(Unit_Nm) LIKE '%APPLE%' AND UPPER(Unit_Nm) LIKE '%VALLEY%' AND State_Nm='KY'","Unit_Nm LIKE '%apple%' AND Unit_Nm LIKE '%valley%' AND State_Nm='KY'"]:
  u=P+'?'+urllib.parse.urlencode({'where':w,'outFields':'Unit_Nm','returnGeometry':'false','f':'json'})
  try: print(w,'->',urllib.request.urlopen(u,timeout=40).read().decode()[-300:])
  except Exception as e: print(w,'ERR',e)
