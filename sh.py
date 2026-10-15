import urllib.request,re,html
def get(u,t=40): return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 KPC'}),timeout=t).read().decode('utf8','replace')
for w in [51,50,56,312,102,49,40,39]:
  try:
    t=get('https://app.fw.ky.gov/fisheries/waterbodydetail.aspx?wid=%d'%w)
    us=sorted(set(u for u in re.findall(r'https?://[^\s"\'<>]+',t)+re.findall(r'(?:href|src)="([^"]+)"',t) if re.search(r'\.pdf|[Mm]ap|\.jpg|\.png',u) and 'Forecast' not in u and 'PublishingImages' not in u))
    print('WB',w,len(t),us[:10],flush=True)
  except Exception as e: print('WB',w,'ERR',e,flush=True)
t=get('https://app.fw.ky.gov/fisheries/waterbodydetail.aspx?wid=51')
i=t.lower().find('map');print(re.sub(r'\s+',' ',t[i-300:i+800]))
