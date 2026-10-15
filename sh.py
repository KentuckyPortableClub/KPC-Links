import urllib.parse
import urllib.request,json,collections,concurrent.futures as cf
def g(u): return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'KPC'}),timeout=30).read())
refs=[]
for s in ['fishing lake','state lake','fish and wildlife area','conservation area','wildlife area','game land','state recreation','hatchery','state preserve','state wildlife','public fishing','reservoir']:
  try: L=g('https://api.pota.app/lookup?search='+urllib.parse.quote(s)+'&size=60')
  except Exception as e: print('ERR',s,e); continue
  refs+= [x.get('value') or x.get('reference') for x in L if str(x.get('value','')).startswith('US-')][:25]
import urllib.parse
refs=list(dict.fromkeys(refs))
def one(r):
  try: j=g('https://api.pota.app/park/'+r); return r,j.get('name'),j.get('parktypeDesc')
  except Exception as e: return r,'',str(e)
with cf.ThreadPoolExecutor(6) as ex: R=list(ex.map(one,refs))
c=collections.defaultdict(list)
for r,n,t in R: c[t].append(n)
for k,v in sorted(c.items(),key=lambda x:-len(x[1])): print(len(v),'|',k,'|',' ; '.join(v[:3]))
