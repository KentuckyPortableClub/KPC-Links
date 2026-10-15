import urllib.request,urllib.parse,json
H={'User-Agent':'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/129 Mobile Safari/537.36','Origin':'https://kentuckyportableclub.github.io','Accept':'*/*'}
def get(u):
  try: return urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60).read().decode('utf8','replace')
  except Exception as e: return 'ERR '+str(e)
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query?'
st=json.dumps([{'statisticType':'count','onStatisticField':'OBJECTID','outStatisticFieldName':'n'}])
st2=json.dumps([{'statisticType':'count','onStatisticField':'OBJECTID','outStatisticFieldName':'n'}],separators=(',',':'))
for name,d in [('stat KY only',dict(where="State_Nm='KY'",groupByFieldsForStatistics='Mang_Type,Mang_Name,Loc_Mang,Category',outStatistics=st,f='json')),
 ('stat compact',dict(where="State_Nm='KY'",groupByFieldsForStatistics='Mang_Type,Mang_Name,Loc_Mang,Category',outStatistics=st2,f='json')),
 ('stat 1=1 geom-less', dict(where="State_Nm='KY'",groupByFieldsForStatistics='Mang_Type',outStatistics=st2,f='json')),
 ('distinct',dict(where="State_Nm='KY'",outFields='Mang_Type,Mang_Name,Loc_Mang,Category',returnDistinctValues='true',returnGeometry='false',f='json')),
 ('distinct CA',dict(where="State_Nm='CA'",outFields='Mang_Type,Mang_Name,Loc_Mang,Category',returnDistinctValues='true',returnGeometry='false',f='json'))]:
  r=get(P+urllib.parse.urlencode(d)); print(name, r[:120], r.count('"attributes"'), r.count('exceededTransferLimit'))
