import json,re,urllib.request,urllib.parse,html
d=json.load(open('kpc-ky-data.json'));out={}
UA={'User-Agent':'Mozilla/5.0 (KPC map link check)'}
def get(u):
  try:
    r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30);return r.geturl(),r.read().decode('utf-8','replace')
  except Exception as e: return u,'ERR '+str(e)
for p in d['parks']:
  if p.get('off') or not p.get('web'):continue
  fu,t=get(p['web']);links=[]
  for m in re.finditer(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>',t,re.S|re.I):
    h,tx=m.group(1),re.sub('<[^>]+>',' ',m.group(2));tx=html.unescape(' '.join(tx.split()))[:80]
    if re.search(r'map|brochure|\.pdf|guide',h+' '+tx,re.I): links.append([tx,urllib.parse.urljoin(fu,html.unescape(h))])
  out[p['c']]={'n':p['n'],'url':fu,'err':t[:80] if t.startswith('ERR') else '','links':links[:40]}
  print(p['c'],len(links),out[p['c']]['err'])
json.dump(out,open('.claude/build/ap/maplinks.json','w'),indent=1)
