import json,urllib.request,urllib.parse
UA={'User-Agent':'Mozilla/5.0 KPC'};out={}
def j(u):
  try: return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40).read())
  except Exception as e: return {'ERR':str(e)[:120]}
C=['https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_Wilderness_01/MapServer/0',
 'https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_Wilderness_02/MapServer/0',
 'https://gis.blm.gov/arcgis/rest/services/range/BLM_Natl_WHB_Geocortex/MapServer',
 'https://gis.blm.gov/arcgis/rest/services/range/BLM_Natl_WHB_Geocortex/MapServer/0',
 'https://gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recreation_Geocortex/MapServer',
 'https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_Wilderness_WSA/MapServer',
 'https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_Geocortex/MapServer',
 'https://gis.blm.gov/arcgis/rest/services/range',
 'https://gis.blm.gov/arcgis/rest/services/recreation',
 'https://gis.blm.gov/arcgis/rest/services/lands']
for u in C:
  r=j(u+'?f=json');out[u]={k:r.get(k) for k in ('ERR','name','layers','fields','services','folders','maxRecordCount')}
  if isinstance(out[u].get('layers'),list): out[u]['layers']=[(l['id'],l['name']) for l in out[u]['layers']]
  if isinstance(out[u].get('fields'),list): out[u]['fields']=[f['name'] for f in out[u]['fields']]
  if isinstance(out[u].get('services'),list): out[u]['services']=[s['name'] for s in out[u]['services']]
for q in ['Herd Management Areas BLM','BLM Recreation Management Areas','Special Recreation Management Areas BLM','National Wilderness Preservation System']:
  r=j('https://www.arcgis.com/sharing/rest/search?f=json&num=12&q='+urllib.parse.quote(q+' type:"Feature Service" OR type:"Map Service"'))
  out['search: '+q]=[(x.get('title'),x.get('owner'),x.get('url')) for x in r.get('results',[])]
json.dump(out,open('.claude/build/ap/blmprobe.json','w'),indent=1)
