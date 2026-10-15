import urllib.request,urllib.parse,json
for lay in ['Ky_KNP_State_Nature_Preserves_WGS84WM','Ky_KNP_Natural_Areas_WGS84WM']:
  K=f'https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/{lay}/MapServer/0/query?'
  j=json.loads(urllib.request.urlopen(K+urllib.parse.urlencode({'where':'1=1','outFields':'MANAME,MA_OWNER,MNG_INST,ACRES,PUB_ACCESS,Webpage','returnGeometry':'false','f':'json'}),timeout=40).read())
  for f in j['features']:
    a=f['attributes'];print(a['MANAME'],'|',a['MA_OWNER'],'|',a['MNG_INST'],'|',round(a['ACRES'] or 0),'|',a['PUB_ACCESS'])
