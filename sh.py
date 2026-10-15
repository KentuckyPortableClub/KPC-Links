import urllib.request,urllib.parse,json,time,re,html
def get(u,data=None,t=40):
  return urllib.request.urlopen(urllib.request.Request(u,data=data,headers={'User-Agent':'Mozilla/5.0 KPC'}),timeout=t).read().decode('utf8','replace')
def txt(t): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',re.sub(r'(?s)<script.*?</script>|<style.*?</style>','',t))))
# 1 KDFWR WMA pages: entrance GPS + map links
for n,i in [('Boone Forestlands WMA',9003),('Elk Forest WMA',9124),('Martins Fork WMA and State Natural Area',9118),('Fortner-Davis WMA',9204),('Blackford Oaks WMA',9719)]:
  try:
    t=get('https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=%d'%i)
    links=sorted(set(re.findall(r'href="([^"]*(?:\.pdf|map|Map)[^"]*)"',t)))
    T=txt(t);g=re.search(r'Entrance GPS coordinates:([^A-Z]*?Longitude[^A-Z]*?[\d.]+)',T)
    s=T.find('WMA Overview');print('##',n,'|',g.group(1) if g else '', '| links:',links[:8],'|',T[s:s+700],flush=True)
  except Exception as e: print(n,'ERR',e,flush=True)
# 2 Martin's Fork SNA page
try:
  t=get('https://eec.ky.gov/Nature-Preserves/Locations/Pages/Martins-Fork.aspx');T=txt(t)
  print('## EEC Martins Fork |',sorted(set(re.findall(r'href="([^"]*(?:\.pdf|[Mm]ap)[^"]*)"',t)))[:8],'|',T[T.find('Martin'):][:900],flush=True)
except Exception as e: print('EEC ERR',e,flush=True)
# 3 waterbody index -> wid, then each page's access sites
want=['Corinth','Elmer Davis','McNeely','Shanty Hollow','Spurlington','Washburn','Beshear','Guist','Boltz','Linville','Bullock','Wilgreen','Wood Creek','Beaver','Kingfisher','Carpenter']
W={}
try:
  idx=get('https://app.fw.ky.gov/fisheries/waterbody.aspx',t=60)
  for m in re.finditer(r'waterbodydetail\.aspx\?wid=(\d+)[^>]*>([^<]+)<',idx,re.I):
    nm=html.unescape(m.group(2)).strip()
    for w in want:
      if w.lower() in nm.lower() and w not in W: W[w]=(int(m.group(1)),nm)
except Exception as e: print('idx ERR',e,flush=True)
print('W',W,flush=True)
for w,(wid,nm) in W.items():
  try:
    t=get('https://app.fw.ky.gov/fisheries/waterbodydetail.aspx?wid=%d'%wid)
    sites=sorted(set(re.findall(r'accesssitedetail\.aspx\?asid=(\d+)[^>]*>([^<]+)<',t)))
    T=txt(t);c=re.search(r'County:?\s*([A-Za-z ,]+?)\s{1,3}(?:Acres|Size|Surface)',T)
    a=re.search(r'([\d,]+)\s*acres',T,re.I)
    print('## WB',w,wid,nm,'| county',c.group(1) if c else '','| acres',a.group(1) if a else '','| sites',sites[:6],flush=True)
  except Exception as e: print('wb',w,'ERR',e,flush=True)
