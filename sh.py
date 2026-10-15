import urllib.request,urllib.parse
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
for w,extra in [("State_Nm='KY' AND Pub_Access='OA'",{}),("State_Nm='KY' AND Mang_Type IN ('FED','STAT')",{}),("State_Nm='KY' AND (Mang_Type='FED' OR Mang_Type='STAT')",{}),("State_Nm='KY'",{'orderByFields':'OBJECTID'}),("State_Nm='KY'",{'resultOffset':0,'resultRecordCount':1000})]:
  q=dict({'where':w,'outFields':'Unit_Nm','returnGeometry':'false','f':'json'},**extra)
  try: r=urllib.request.urlopen(urllib.request.Request(P+'?'+urllib.parse.urlencode(q),headers={'User-Agent':'KPC'}),timeout=40); print(w,extra,r.status,len(r.read()))
  except Exception as e: print(w,extra,'ERR',e)
