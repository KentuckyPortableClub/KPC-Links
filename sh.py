import urllib.request,urllib.parse,json
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
F='OBJECTID,Unit_Nm,Loc_Nm,Mang_Type,Mang_Name,Loc_Mang,Own_Type,Own_Name,Loc_Own,Des_Tp,Loc_Ds,Pub_Access,GIS_Acres,State_Nm,Category,Date_Est,Comments'
def g(u): return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'KPC'}),timeout=60).read()
out={}
for nm in ['Bullock Pen Lake','Taylorsville Lake Wildlife Management Area']:
    w=f"(Unit_Nm LIKE '%{nm.split()[0]}%' OR Loc_Nm LIKE '%{nm.split()[0]}%') AND State_Nm='KY'"
    out['s_'+nm]=json.loads(g(P+'?'+urllib.parse.urlencode({'where':w,'outFields':F,'returnGeometry':'false','f':'json','resultRecordCount':200,'orderByFields':'GIS_Acres DESC'})))
    out['g_'+nm]=json.loads(g(P+'?'+urllib.parse.urlencode({'where':f"Unit_Nm='{nm}' AND State_Nm='KY'",'outFields':F,'returnGeometry':'true','outSR':4326,'geometryPrecision':5,'maxAllowableOffset':0.00005,'f':'geojson'})))
json.dump(out,open('maprep.json','w'))
print({k:len(v.get('features',[])) for k,v in out.items()}, [v.get('error') for v in out.values()])
