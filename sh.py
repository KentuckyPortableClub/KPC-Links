import urllib.request,json
H={'User-Agent':'Mozilla/5.0'}
for u in ['https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0?f=json','https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer?f=json','https://edits.nationalmap.gov/arcgis/rest/services/PAD-US?f=json']:
  try:
    j=json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=40).read())
    print(u); print({k:j.get(k) for k in ['name','type','minScale','maxScale','geometryType','capabilities','supportsDynamicLayers','maxRecordCount','supportedQueryFormats','singleFusedMapCache']})
    print(' layers',[ (l.get('id'),l.get('name'),l.get('minScale')) for l in j.get('layers',[])][:12]); print(' services',j.get('services'))
  except Exception as e: print(u,'ERR',e)
