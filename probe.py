import urllib.request, json
out=[]
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent':'KPC probe'}), timeout=60) as f: return json.loads(f.read().decode('utf-8','replace'))
    except Exception as e: return {'err': str(e)[:200]}
for u in ['https://geo.environnement.gouv.qc.ca/donnees/rest/services/Biodiversite/Aires_protegees/MapServer/12',
          'https://geo.environnement.gouv.qc.ca/donnees/rest/services/Biodiversite/Aires_protegees/MapServer/10',
          'https://geo.environnement.gouv.qc.ca/donnees/rest/services/Biodiversite/Aires_protegees/MapServer/23',
          'https://nsgiwa.novascotia.ca/arcgis/rest/services/ENV/ENV_NS_Prot_Area_Sys_UT83/MapServer',
          'https://nsgiwa.novascotia.ca/arcgis/rest/services/PLAN/PLANCrownLandsWM84V1/MapServer',
          'https://gis-erd-der.gnb.ca/server/rest/services/OpenData/PNAs/FeatureServer/0',
          'https://gis-erd-der.gnb.ca/server/rest/services/OpenData/Nature_Legacy_Protected_Areas/FeatureServer/0',
          'https://gis-erd-der.gnb.ca/server/rest/services/OpenData/WildlifeRefuge/MapServer',
          'https://services.arcgis.com/mMUesHYPkXjaFGfS/arcgis/rest/services/Manitoba_Wildlife_Lands/FeatureServer',
          'https://services.arcgis.com/mMUesHYPkXjaFGfS/arcgis/rest/services/bdy_wildlife_mgmt_areas_py_shp/FeatureServer/0']:
    j=get(u+'?f=json')
    out.append('\n## '+u)
    if 'layers' in j: out.append('layers: '+json.dumps([(l.get('id'),l.get('name'),l.get('geometryType')) for l in j['layers']], ensure_ascii=False)[:1500])
    if 'fields' in j and j['fields']: out.append('fields: '+', '.join(f['name'] for f in j['fields'])[:900]+' | geom '+str(j.get('geometryType'))+' | geojson? '+str(j.get('supportedQueryFormats')))
    if 'err' in j: out.append('ERR '+j['err'])
# sample names
for u,f in [('https://geo.environnement.gouv.qc.ca/donnees/rest/services/Biodiversite/Aires_protegees/MapServer/12','*'),('https://geo.environnement.gouv.qc.ca/donnees/rest/services/Biodiversite/Aires_protegees/MapServer/23','*')]:
    j=get(u+"/query?where=1%3D1&outFields=*&returnGeometry=false&resultRecordCount=3&f=json&geometry=-72.9,46.2,-72.7,46.4&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects")
    out.append('\nsample '+u[-3:]+': '+json.dumps([x.get('attributes') for x in j.get('features',[])], ensure_ascii=False)[:1500])
open('out.txt','w').write('\n'.join(out))
