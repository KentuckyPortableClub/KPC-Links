import json,urllib.request,urllib.parse
UA={'User-Agent':'Mozilla/5.0 KPC'};out={}
def j(u):
  try: return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40).read())
  except Exception as e: return {'ERR':str(e)[:120]}
B='https://gis.blm.gov/arcgis/rest/services/'
for sv in ['range/BLM_Natl_WHB','recreation/BLM_Natl_Recreation','recreation/BLM_Natl_Recs_poly','lands/BLM_Natl_NLCS_WLD_WSA','lands/BLM_Natl_NLCS_NM_NCA_poly']:
  for typ in ['MapServer','FeatureServer']:
    r=j(B+sv+'/'+typ+'?f=json')
    if 'ERR' in r or r.get('error'): out[sv+'/'+typ]=str(r)[:150];continue
    L=[(l['id'],l['name'],l.get('geometryType')) for l in r.get('layers',[])];out[sv+'/'+typ]=L
    for lid,nm,g in L:
      if g and 'olygon' not in g: continue
      x=j(B+sv+'/'+typ+'/'+str(lid)+'?f=json');c=j(B+sv+'/'+typ+'/'+str(lid)+'/query?where=1%3D1&returnCountOnly=true&f=json')
      out[sv+'/'+typ+'/'+str(lid)]={'name':nm,'fields':[f['name'] for f in x.get('fields') or []],'count':c.get('count'),'max':x.get('maxRecordCount'),'geo':x.get('supportedQueryFormats')}
    break
json.dump(out,open('.claude/build/ap/blmprobe.json','w'),indent=1)
