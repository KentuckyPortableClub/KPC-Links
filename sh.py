import json,urllib.request,collections,re
j=json.load(urllib.request.urlopen(urllib.request.Request('https://spothole.app/api/v1/spots?limit=5000&max_age=10800',headers={'User-Agent':'KPC'}),timeout=60))
a=j if isinstance(j,list) else j.get('spots',[])
print('n',len(a))
print('sig',collections.Counter(str(x.get('sig')) for x in a).most_common(40))
print('source',collections.Counter(str(x.get('source')) for x in a).most_common(20))
kw=collections.Counter()
for x in a:
  c=str(x.get('comment') or '').upper()
  for k in ['IOTA','COTA','WCA','CASTLE','LIGHTHOUSE','ARLHS','ILLW','BOTA','BUNKER','GMA','HEMA','SIOTA','WAB','ZLOTA','LLOTA','MOTA','TOTA','IOCA','JOTA','SES','SPECIAL EVENT','QSO PARTY','QP','CONTEST','NPOTA','WWBOTA','SUMMIT','TROOP']:
    if re.search(r'\b'+k+r'\b',c): kw[k]+=1
print('comment kw',kw.most_common())
ex=[(x.get('sig'),x.get('dx_call'),x.get('comment'),[r for r in (x.get('sig_refs') or [])][:1]) for x in a if x.get('sig') not in (None,'POTA','SOTA','WWFF')][:25]
for e in ex: print(e)
