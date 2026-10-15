import urllib.request,urllib.parse,json
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0'
def g(u):
    return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'KPC'}),timeout=60).read())
j=g(P+'?f=json');print([f['name'] for f in j['fields']])
for w in ["Unit_Nm LIKE '%Bullock Pen%' AND State_Nm='KY'","Unit_Nm LIKE '%Fort Yargo%'","Unit_Nm LIKE '%Taylorsville%' AND State_Nm='KY'"]:
    q={'where':w,'outFields':'OBJECTID,Unit_Nm,Loc_Nm,Mang_Type,Mang_Name,Loc_Mang,Own_Type,Own_Name,Loc_Own,Des_Tp,Loc_Ds,Pub_Access,GIS_Acres,State_Nm,Category','returnGeometry':'false','f':'json'}
    r=g(P+'/query?'+urllib.parse.urlencode(q));print(w,len(r.get('features',[])));[print('  ',f['attributes']) for f in r.get('features',[])[:6]]
    if 'error' in r: print(r['error'])
