import urllib.request,urllib.parse
H={'User-Agent':'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/129 Mobile Safari/537.36','Origin':'https://kentuckyportableclub.github.io','Accept':'*/*'}
def get(u,data=None):
  try: return urllib.request.urlopen(urllib.request.Request(u,data=data,headers=dict(H,**({'Content-Type':'application/x-www-form-urlencoded'} if data else {}))),timeout=40).read().decode('utf8','replace')
  except Exception as e: return 'ERR '+str(e)
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
def n(r): return r if r.startswith('ERR') else str(r.count('"Unit_Nm"')-1)+' hits '+r.split('"features"')[-1][:120]
tests=["State_Nm='KY' AND Mang_Type IN ('FED','STAT') AND Category<>'Easement'","State_Nm='KY' AND Category<>'Easement'","State_Nm='KY' AND Mang_Type<>'LOC'","Mang_Type='STAT' AND State_Nm='KY'",
"State_Nm='KY' AND Mang_Name='SFW' AND Unit_Nm LIKE '%Kingfisher%'","State_Nm='KY' AND Unit_Nm LIKE '%Kingfisher%' AND Mang_Name='SFW'","State_Nm='KY' AND (Mang_Name='SFW' OR Mang_Name='SDNR')",
"State_Nm='KY' AND Mang_Name='SFW' OR Mang_Name='SDNR'","State_Nm='KY' AND Unit_Nm LIKE '%McNeely%Lake%'","State_Nm='KY' AND Loc_Nm LIKE '%KINGFISHER%LAKE%'","State_Nm='KY' AND Unit_Nm LIKE '%Barren River%Lake%'",
"State_Nm='KY' AND Unit_Nm LIKE '%Lake Linville%'","State_Nm='KY' AND Unit_Nm LIKE '%O''Brien%'","State_Nm='KY' AND Unit_Nm LIKE 'Kingfisher%'"]
for w in tests:
  q=urllib.parse.urlencode(dict(where=w,outFields='Unit_Nm,State_Nm',returnGeometry='false',f='json'))
  print('GET ',w,'=>',n(get(P+'?'+q)))
