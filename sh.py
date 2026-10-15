import urllib.request,urllib.parse,json,time
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
def q(params):
    base={'where':'1=1','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'OBJECTID,Unit_Nm,Loc_Nm,Mang_Name,Loc_Mang,Des_Tp,Pub_Access,GIS_Acres,Category','outSR':4326,'f':'geojson'};base.update(params)
    t=time.time();b=urllib.request.urlopen(urllib.request.Request(P+'?'+urllib.parse.urlencode(base),headers={'User-Agent':'KPC'}),timeout=60).read();return json.loads(b),len(b),round(time.time()-t,1)
for nm,la,lo in [('Vogel GA',34.766,-83.925),('DBNF RedRiver',37.82,-83.62),('Smokies',35.61,-83.49)]:
    d=0.03;env=f'{lo-d},{la-d},{lo+d},{la+d}'
    m,n,t=q({'geometry':env,'geometryType':'esriGeometryEnvelope','returnGeometry':'false'})
    fs=[f['properties'] for f in m['features']]
    print(nm,'meta',len(fs),n,t,[(p['Unit_Nm'],p['Category'],p['Pub_Access'],int(p['GIS_Acres'] or 0)) for p in fs][:10])
    small=[str(p['OBJECTID']) for p in fs if (p['GIS_Acres'] or 0)<20000 and p['Category']!='Proclamation'];big=[str(p['OBJECTID']) for p in fs if (p['GIS_Acres'] or 0)>=20000 and p['Category']!='Proclamation']
    if small: g,n,t=q({'objectIds':','.join(small),'returnGeometry':'true','geometryPrecision':5,'maxAllowableOffset':0.00004});print('  small',len(g['features']),n,'bytes',t)
    if big: g,n,t=q({'objectIds':','.join(big),'geometry':env,'geometryType':'esriGeometryEnvelope','returnGeometry':'true','geometryPrecision':5,'maxAllowableOffset':0.00015});print('  big',len(g['features']),n,'bytes',t)
