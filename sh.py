import urllib.request,json,time,collections,concurrent.futures as cf
P=json.load(open('kyp.json'))
def one(p):
  try: j=json.loads(urllib.request.urlopen(urllib.request.Request('https://api.pota.app/park/'+p[0],headers={'User-Agent':'KPC'}),timeout=30).read()); return p,j
  except Exception as e: return p,{'err':str(e)}
with cf.ThreadPoolExecutor(6) as ex: R=list(ex.map(one,P))
print(json.dumps(R[0][1])[:1500])
c=collections.defaultdict(list)
for p,j in R:
  k=j.get('parktypeDesc') or j.get('parkTypeDesc') or j.get('err','?')
  c[k].append(p[1])
for k,v in sorted(c.items(),key=lambda x:-len(x[1])): print(len(v),'|',k,'|',' ; '.join(v[:4]))
