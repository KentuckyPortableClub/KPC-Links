import json,urllib.request,urllib.parse
u='https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSInterest_Simplified_Authoritative/FeatureServer/0/query?'
q=urllib.parse.urlencode({'geometry':'-89.6,36.45,-81.95,39.15','geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'ORGNAME,DIVNAME,CMPXNAME,RSL_TYPE,INTTYPE1,INTTYPE2,LIT','outSR':4326,'geometryPrecision':5,'f':'geojson'})
j=json.load(urllib.request.urlopen(u+q,timeout=120))
print(len(j['features']),sorted({(f['properties']['ORGNAME'],f['properties']['INTTYPE1']) for f in j['features']}))
json.dump(j,open('fws.json','w'))
