import json,urllib.request,urllib.parse
C=['https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSApproved/FeatureServer/0','https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSApproved/FeatureServer/1',
'https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSInterest_Simplified_Authoritative/FeatureServer/0','https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSInterest_Simplified_Authoritative/FeatureServer/1',
'https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/National_Wildlife_Refuge_System_Boundaries/FeatureServer/0','https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSBoundaries/FeatureServer/0']
out={}
for u in C:
    q=urllib.parse.urlencode({'geometry':'-87.70,37.80,-87.35,38.00','geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'*','outSR':4326,'f':'geojson'})
    try:
        j=json.load(urllib.request.urlopen(u+'/query?'+q,timeout=60));out[u]=j;print(u,len(j.get('features',[])),[ {k:v for k,v in f['properties'].items() if isinstance(v,str)} for f in j.get('features',[])][:3], j.get('error'))
    except Exception as e: print(u,e)
try:
    j=json.load(urllib.request.urlopen('https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services?f=json',timeout=60));print([s['name'] for s in j.get('services',[])][:80])
except Exception as e: print('list',e)
json.dump(out,open('fws.json','w'))
