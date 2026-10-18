import json,urllib.request
out={}
for u in ['https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_Wilderness_02/MapServer/0/query?objectIds=1&outFields=wildernessname&returnGeometry=true&outSR=4326&maxAllowableOffset=0.01&f=geojson',
 'https://gis.blm.gov/arcgis/rest/services/range/BLM_Natl_WHB/MapServer/0/query?objectIds=1&outFields=HMA_NAME&returnGeometry=true&outSR=4326&maxAllowableOffset=0.01&f=geojson',
 'https://gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recreation/MapServer/9/query?objectIds=1&outFields=FET_NAME&returnGeometry=true&outSR=4326&f=geojson']:
  try:
    r=urllib.request.urlopen(urllib.request.Request(u,headers={'Origin':'https://kentuckyportableclub.github.io','User-Agent':'Mozilla/5.0'}),timeout=40)
    b=r.read();out[u[:70]]={'status':r.status,'acao':r.headers.get('Access-Control-Allow-Origin'),'len':len(b),'start':b[:160].decode('utf-8','replace')}
  except Exception as e: out[u[:70]]=str(e)
json.dump(out,open('.claude/build/ap/blmprobe.json','w'),indent=1)
