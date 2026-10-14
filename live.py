import json,urllib.request,urllib.parse
KY='https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/'
SV={'US-7968':'Ky_KNP_State_Nature_Preserves_WGS84WM/MapServer/0','KFF-6879':'Ky_KNP_State_Nature_Preserves_WGS84WM/MapServer/0','US-1263':'Ky_State_Parks_Features_WGS84WM/MapServer/8','KFF-1263':'Ky_State_Parks_Features_WGS84WM/MapServer/8','US-1255':'Ky_Public_Hunting_Areas_WGS84WM/MapServer/1','KFF-1255':'Ky_Public_Hunting_Areas_WGS84WM/MapServer/1','US-4526':'Ky_Public_Hunting_Areas_WGS84WM/MapServer/1','KFF-6295':'Ky_Public_Hunting_Areas_WGS84WM/MapServer/1'}
P=json.load(open('newpins.json'));out=[]
for ref,(la,lo) in P.items():
    q=urllib.parse.urlencode({'geometry':f'{lo},{la}','geometryType':'esriGeometryPoint','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'*','returnGeometry':'false','f':'json'})
    try:
        j=json.load(urllib.request.urlopen(KY+SV[ref]+'/query?'+q,timeout=60))
        names=[ ' / '.join(str(v) for k,v in f['attributes'].items() if isinstance(v,str) and len(v)>3)[:120] for f in j.get('features',[])]
        out.append(f'{ref} {la},{lo}: {len(names)} hit(s): {names}  err={j.get("error")}')
    except Exception as e: out.append(f'{ref}: {e}')
open('live.txt','w').write('\n'.join(out));print('\n'.join(out))
