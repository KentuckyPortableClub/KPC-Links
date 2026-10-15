import urllib.request,urllib.parse,json
def get(u):
  try: return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'KPC'}),timeout=40).read().decode('utf8','replace')
  except Exception as e: return 'ERR '+str(e)
K='https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/'
for lay,nm in [('Ky_KNP_State_Nature_Preserves_WGS84WM/MapServer/0','MANAME'),('Ky_KNP_Natural_Areas_WGS84WM/MapServer/0','MANAME'),('Ky_State_Parks_Features_WGS84WM/MapServer/8','PARK_NAME'),('Ky_Public_Hunting_Areas_WGS84WM/MapServer/1','AREANAME')]:
  for w in [f"UPPER({nm}) LIKE '%APPLE%'",f"UPPER({nm}) LIKE '%AXE%'",f"UPPER({nm}) LIKE '%BLACKFORD%'",f"UPPER({nm}) LIKE '%CARTER CAVES%'"]:
    print(lay[:20],w, get(K+lay+'/query?'+urllib.parse.urlencode({'where':w,'outFields':'*','returnGeometry':'false','resultRecordCount':2,'f':'json'}))[-700:].replace('\n',' '))
print(get(K+'Ky_KNP_State_Nature_Preserves_WGS84WM/MapServer/0/query?'+urllib.parse.urlencode({'where':'1=1','outFields':'PUB_ACCESS,MA_OWNER,MNG_INST','returnDistinctValues':'true','returnGeometry':'false','f':'json'}))[-1500:])
