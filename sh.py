import urllib.request,urllib.parse,json,time
def g(u,data=None):
    t=time.time()
    r=urllib.request.urlopen(urllib.request.Request(u,data=data,headers={'User-Agent':'KPC','Origin':'https://kentuckyportableclub.github.io'}),timeout=90)
    return json.loads(r.read()),r.headers.get('Access-Control-Allow-Origin'),round(time.time()-t,1)
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
q={'where':"State_Nm='KY' AND Mang_Type IN ('FED','STAT')",'groupByFieldsForStatistics':'Mang_Type,Loc_Mang','outStatistics':json.dumps([{'statisticType':'count','onStatisticField':'OBJECTID','outStatisticFieldName':'n'}]),'f':'json'}
try:
    j,c,t=g(P+'?'+urllib.parse.urlencode(q));print('stats',t,c,len(j.get('features',[])),j.get('error'));[print('  ',f['attributes']) for f in j.get('features',[])[:40]]
except Exception as e: print('stats ERR',e)
N='https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/2/query'
try:
    j,c,t=g(N+'?'+urllib.parse.urlencode({'where':"UNIT_NAME LIKE '%Camp Nelson%'",'outFields':'*','returnGeometry':'false','f':'json'}));print('nps',t,c,[f['attributes'] for f in j.get('features',[])][:2])
except Exception as e: print('nps ERR',e)
W='https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSInterest_Simplified_Authoritative/FeatureServer/0/query'
try:
    j,c,t=g(W+'?'+urllib.parse.urlencode({'where':"ORGNAME LIKE '%GREEN RIVER%'",'outFields':'*','returnGeometry':'false','f':'json','resultRecordCount':3}));print('fws',t,c,[f['attributes'] for f in j.get('features',[])][:2])
except Exception as e: print('fws ERR',e)
oq='[out:json][timeout:40];area["ISO3166-2"="US-KY"]->.s;(nwr["name"~"Bullock Pen",i](area.s);)->.r;(.r[leisure];.r[boundary];.r[landuse];.r[natural];);out tags center 20;'
try:
    j,c,t=g('https://overpass-api.de/api/interpreter',('data='+urllib.parse.quote(oq)).encode());print('osm',t,c,[(e['type'],e['tags'].get('name'),e['tags'].get('leisure') or e['tags'].get('boundary') or e['tags'].get('natural'),e['tags'].get('operator')) for e in j.get('elements',[])][:10])
except Exception as e: print('osm ERR',e)
