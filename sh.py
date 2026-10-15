import urllib.request,urllib.parse
H={'User-Agent':'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/129 Mobile Safari/537.36','Origin':'https://kentuckyportableclub.github.io','Referer':'https://kentuckyportableclub.github.io/','Accept':'*/*'}
def get(u):
  try: return urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=40).read().decode('utf8','replace')[:300]
  except Exception as e: return 'ERR '+str(e)
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query?'
for w in ["UPPER(Unit_Nm) LIKE '%KINGFISHER%'","UPPER(Unit_Nm) LIKE '%KINGFISHER%' AND State_Nm='KY'","Unit_Nm LIKE '%Kingfisher%' AND State_Nm='KY'","Unit_Nm LIKE '%KINGFISHER%' AND State_Nm='KY'","Loc_Nm LIKE '%KINGFISHER%' AND State_Nm='KY'","State_Nm='KY' AND Unit_Nm LIKE '%Barren%'","UPPER(Unit_Nm) LIKE '%BARREN%' AND State_Nm='KY'","LOWER(Unit_Nm) LIKE '%kingfisher%'"]:
  print(w,'=>',get(P+urllib.parse.urlencode(dict(where=w,outFields='Unit_Nm,State_Nm',returnGeometry='false',f='json'))).split('"features"')[-1][:200])
