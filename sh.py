import urllib.request,urllib.parse,json
def get(u):
  try: return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'KPC'}),timeout=40).read().decode('utf8','replace')
  except Exception as e: return 'ERR '+str(e)
K='https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/'
for lay in ['Ky_KNP_State_Nature_Preserves_WGS84WM/MapServer/0','Ky_KNP_Natural_Areas_WGS84WM/MapServer/0','Ky_State_Parks_Features_WGS84WM/MapServer/8','Ky_Public_Hunting_Areas_WGS84WM/MapServer/1']:
  j=json.loads(get(K+lay+'?f=json')); print('==',lay,[f['name'] for f in j.get('fields',[])], j.get('supportsAdvancedQueries'))
  for w in ["NAME LIKE '%Apple%'","NAME LIKE '%APPLE%'","1=1"]:
    print(w, get(K+lay+'/query?'+urllib.parse.urlencode({'where':w,'outFields':'*','returnGeometry':'false','resultRecordCount':2,'f':'json'}))[:400])
