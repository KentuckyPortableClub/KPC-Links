import urllib.request,urllib.parse,json,time
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
names=['Beaver Lake','Boltz Lake','Bullock Pen Lake','Carpenter Lake','Corinth Lake','Elmer Davis Lake','Guist Creek Lake','Kingfisher Lakes','McNeely Lake','Shanty Hollow Lake','Spurlington Lake','Washburn Lake',"Murphy's Pond",'Lake Beshear','Cumberland River Mussel Sanctuary','Dr. James C. Salato Wildlife Education Center','Russell County Fish Access - Barnes Property','Redbird Purchase Unit','Clay Hill Memorial Forest','Halls Prairie','Kentucky State University Environmental Education Center','Pullen Farm','Rowan County Sphagnum Swamp','Taylor Fork Ecological Area','The Green at BCTC']
out={}
for n in names:
  for ua in ['KPC','Mozilla/5.0']:
    q={'where':"Unit_Nm='%s'"%n.replace("'","''"),'outFields':'Unit_Nm,Loc_Own,Own_Type,Loc_Mang,Mang_Type,Pub_Access,GIS_Acres,State_Nm','returnGeometry':'true','outSR':4326,'maxAllowableOffset':0.0003,'geometryPrecision':5,'f':'geojson'}
    try:
      j=json.loads(urllib.request.urlopen(urllib.request.Request(P+'?'+urllib.parse.urlencode(q),headers={'User-Agent':ua}),timeout=60).read())
      fs=[f for f in j.get('features',[]) if f['properties'].get('State_Nm')=='KY']
      out[n]=fs;print(n,len(fs),[ (f['properties']['Loc_Own'],f['properties']['Pub_Access']) for f in fs][:3]);break
    except Exception as e: print(n,ua,'ERR',e); time.sleep(2)
  time.sleep(1)
json.dump(out,open('maprep.json','w'))
