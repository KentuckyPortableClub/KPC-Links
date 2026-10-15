import urllib.request,re,html,concurrent.futures as cf
def get(u,t=30): return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 KPC'}),timeout=t).read().decode('utf8','replace')
def ok(u):
  try:
    r=urllib.request.urlopen(urllib.request.Request(u,method='HEAD',headers={'User-Agent':'Mozilla/5.0 KPC'}),timeout=20);return r.status
  except Exception as e: return str(e)[:30]
for n,i in [('Boone Forestlands',9003),('Elk Forest',9124),('Martins Fork',9118),('Fortner-Davis',9204),('Blackford Oaks',9719),('Robinson Forest',9120)]:
  t=get('https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=%d'%i)
  us=sorted(set(u for u in re.findall(r'https?://[^\s"\'<>]+',t) if re.search(r'Documents/.*\.pdf|Map_Images',u) and 'FishingForecast' not in u))
  print('WMA',n,i,[(u,ok(u)) for u in us],flush=True)
try:
  t=get('https://eec.ky.gov/Nature-Preserves/Locations/Pages/Martins-Fork.aspx')
  print('EEC',sorted(set(u for u in re.findall(r'(?:href|src)="([^"]+)"',t) if re.search(r'\.pdf|map|Map|\.jpg|\.png',u) and 'Title' not in u))[:15],flush=True)
except Exception as e: print('EEC ERR',e)
want=['corinth','elmer davis','mcneely','shanty hollow','spurlington','washburn','beshear','guist','boltz','linville','bullock','wood creek','beaver lake','kingfisher','carpenter']
def scan(w):
  try:
    t=get('https://app.fw.ky.gov/fisheries/waterbodydetail.aspx?wid=%d'%w,20)
    m=re.search(r'<title>([^<]*)</title>',t,re.I);h=re.search(r'<h[12][^>]*>([^<]+)</h',t)
    name=html.unescape((h.group(1) if h else (m.group(1) if m else ''))).strip()
    if any(x in t.lower()[:20000] and x in name.lower() for x in want):
      maps=sorted(set(u for u in re.findall(r'https?://[^\s"\'<>]+',t) if re.search(r'\.pdf|Map',u) and 'FishingForecast' not in u))
      sites=sorted(set(re.findall(r'accesssitedetail\.aspx\?asid=(\d+)',t)))
      return (w,name,maps[:6],sites[:8])
  except Exception as e: return None
with cf.ThreadPoolExecutor(8) as ex:
  for r in ex.map(scan,range(1,460)):
    if r: print('WB',r,flush=True)
