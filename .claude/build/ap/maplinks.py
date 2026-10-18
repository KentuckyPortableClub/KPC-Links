import json,re,urllib.request,html,urllib.parse
UA={'User-Agent':'Mozilla/5.0 (KPC map link check)'};out={}
def get(u):
  try: r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40);return r.geturl(),r.read().decode('utf-8','replace')
  except Exception as e: return u,'ERR '+str(e)
urls=set()
for sm in ['https://parks.ky.gov/sitemap.xml','https://parks.ky.gov/sitemap_index.xml']:
  u,t=get(sm);out[sm]=t[:200] if t.startswith('ERR') else 'ok'
  for x in re.findall(r'<loc>([^<]+)</loc>',t):
    if x.endswith('.xml'):
      u2,t2=get(x);urls.update(re.findall(r'<loc>([^<]+)</loc>',t2))
    else: urls.add(x)
hits=[u for u in urls if re.search(r'sawyer|white-hall|whitley',u,re.I)]
out['hits']=hits;out['count']=len(urls)
for h in hits[:8]:
  fu,t=get(h);out[h]=[[html.unescape(' '.join(re.sub('<[^>]+>',' ',tx).split()))[:60],urllib.parse.urljoin(fu,html.unescape(hr))] for hr,tx in re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',t,re.S|re.I) if re.search(r'map|\.pdf',hr+tx,re.I)][:20]
json.dump(out,open('.claude/build/ap/maplinks2.json','w'),indent=1)
