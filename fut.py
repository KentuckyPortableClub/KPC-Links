import json,urllib.request,urllib.parse,time,re
out={}
def get(u,data=None,t=120,raw=False):
    r=urllib.request.urlopen(urllib.request.Request(u,data=data,headers={'User-Agent':'KPC-Links park research'}),timeout=t).read()
    return r if raw else json.loads(r)
NAMES=['Cascade Cave','Clear Creek','Bullock Pen','Guist Creek','Linville','Wilgreen','Wood Creek','Beaver Lake','Kingfisher','Carpenter','Boltz']
rx=re.compile('|'.join(NAMES),re.I)
# 1 POTA
try:
    p=get('https://api.pota.app/location/parks/US-KY'); out['pota_all']=p
    print('pota',len(p)); [print(' ',x.get('reference'),x.get('name'),x.get('latitude'),x.get('longitude'),x.get('activations')) for x in p if rx.search(x.get('name',''))]
    print('pota max', sorted(p,key=lambda x:int(x['reference'][3:]))[-15:])
except Exception as e: print('pota',e)
for r in ['US-12970','US-12973','US-12975','US-12976','US-12977','US-12978','US-12979','US-12980','US-12981','US-12982','US-12983','US-12984','US-12985']:
    try: j=get('https://api.pota.app/park/'+r); print(r,j and (j.get('name'),j.get('locationDesc'),j.get('latitude'),j.get('longitude'),j.get('website'))); out['park_'+r]=j
    except Exception as e: print(r,e)
# 2 KY GIS services catalog
KY='https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/'
try:
    c=get(KY+'?f=json'); out['kycat']=c; print('ky services',[s['name'] for s in c.get('services',[]) if re.search('fish|hunt|lake|wild|park|recre|water|nature',s['name'],re.I)])
except Exception as e: print('kycat',e)
for svc in ['Ky_Public_Hunting_Areas_WGS84WM']:
    try:
        m=get(KY+svc+'/MapServer?f=json'); print(svc,[(l['id'],l['name']) for l in m.get('layers',[])])
        for l in m.get('layers',[]):
            try:
                j=get(KY+svc+'/MapServer/%d/query?where=1%%3D1&outFields=*&returnGeometry=false&f=json'%l['id'])
                fs=j.get('features',[]); hits=[f['attributes'] for f in fs if rx.search(json.dumps(f['attributes']))]
                print(' layer',l['id'],len(fs),'hits',hits[:20])
                if hits:
                    q=urllib.parse.urlencode({'where':'1=1','outFields':'*','outSR':4326,'geometryPrecision':5,'f':'geojson'})
                    g=get(KY+svc+'/MapServer/%d/query?'%l['id']+q,None,180)
                    out['kyhunt_%d'%l['id']]={'type':'FeatureCollection','features':[f for f in g['features'] if rx.search(json.dumps(f['properties']))]}
            except Exception as e: print(' layer',l['id'],e)
    except Exception as e: print(svc,e)
# 3 PAD-US by name in KY
base='https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Protected_Areas_Fee_Manager/FeatureServer/0/query'
for n in NAMES:
    w="State_Nm='KY' AND Unit_Nm LIKE '%"+n.replace("'","''")+"%'"
    try:
        j=get(base+'?'+urllib.parse.urlencode({'where':w,'outFields':'Unit_Nm,Mang_Name,Loc_Mang,Loc_Own,GIS_Acres,Des_Tp,Pub_Access','outSR':4326,'geometryPrecision':5,'f':'geojson'}),None,120)
        out['padus_'+n]=j; print('padus',n,[(f['properties']['Unit_Nm'],f['properties'].get('Loc_Mang'),f['properties'].get('GIS_Acres')) for f in j.get('features',[])])
    except Exception as e: print('padus',n,e)
# 4 OSM: named features in KY
EP=['https://overpass-api.de/api/interpreter','https://overpass.private.coffee/api/interpreter','https://maps.mail.ru/osm/tools/overpass/api/interpreter']
q='[out:json][timeout:240];area["ISO3166-2"="US-KY"]->.k;(nwr["name"~"'+'|'.join(NAMES)+'",i](area.k)[~"^(natural|water|leisure|boundary|landuse|tourism|protected_area)$"~"."];);out geom;'
for k in range(6):
    try: o=get(EP[k%3],urllib.parse.urlencode({'data':q}).encode(),300); out['osm']=o; print('osm',len(o['elements'])); [print('  ',e['type'],e['id'],e.get('tags',{}).get('name'),{a:b for a,b in e.get('tags',{}).items() if a in('natural','water','leisure','boundary','landuse','operator','owner','protect_class','website')}, e.get('bounds')) for e in o['elements']]; break
    except Exception as e: print('osm',e); time.sleep(20)
json.dump(out,open('fut.json','w'))
