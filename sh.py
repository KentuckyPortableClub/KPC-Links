import urllib.request,urllib.parse,json
K='https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_State_Parks_Features_WGS84WM/MapServer/8/query?'
j=json.loads(urllib.request.urlopen(K+urllib.parse.urlencode({'where':'1=1','outFields':'PUBLIC_NAM,PARK_NAME','returnGeometry':'false','f':'json','resultRecordCount':8}),timeout=40).read())
print([f['attributes'] for f in j['features']])
j=json.loads(urllib.request.urlopen(K+urllib.parse.urlencode({'where':"UPPER(PUBLIC_NAM) LIKE '%BARREN%'",'outFields':'PUBLIC_NAM','returnGeometry':'false','f':'json'}),timeout=40).read())
print(j.get('features'),j.get('error'))
