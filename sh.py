import urllib.request,urllib.parse,json
def get(u,data=None):
  try:
    r=urllib.request.urlopen(urllib.request.Request(u,data=data,headers={'User-Agent':'KPC-maprep/1.0 (brandon club site)'}),timeout=40);return r.read().decode('utf8','replace')
  except Exception as e: return 'ERR '+str(e)
K='https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/'
for lay in ['Ky_KNP_State_Nature_Preserves_WGS84WM/MapServer/0','Ky_KNP_Natural_Areas_WGS84WM/MapServer/0','Ky_State_Parks_Features_WGS84WM/MapServer/8','Ky_Public_Hunting_Areas_WGS84WM/MapServer/1']:
  print('==',lay); print(get(K+lay+'/query?'+urllib.parse.urlencode({'where':"UPPER(NAME) LIKE '%APPLE%'",'outFields':'*','returnGeometry':'false','f':'json'}))[:1500])
  print(get(K+lay+'?f=json')[:300])
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
print('== PAD');print(get(P+'?'+urllib.parse.urlencode({'where':"State_Nm='KY' AND (UPPER(Unit_Nm) LIKE '%APPLE%' OR UPPER(Loc_Nm) LIKE '%APPLE%')",'outFields':'Unit_Nm,Loc_Nm,Loc_Own,Loc_Mang,Pub_Access,GIS_Acres','returnGeometry':'false','f':'json'}))[:1500])
print('== NOM');print(get('https://nominatim.openstreetmap.org/search?'+urllib.parse.urlencode({'q':'Apple Valley Glades, Kentucky','format':'jsonv2','extratags':1,'limit':5}))[:2000])
print('== WD');print(get('https://www.wikidata.org/w/api.php?action=wbsearchentities&search=Apple%20Valley%20Glades&language=en&format=json')[:800])
print('== AXE');print(get(K+'Ky_KNP_State_Nature_Preserves_WGS84WM/MapServer/0/query?'+urllib.parse.urlencode({'where':"UPPER(NAME) LIKE '%AXE%'",'outFields':'*','returnGeometry':'false','f':'json'}))[:1500])
