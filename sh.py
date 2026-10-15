import urllib.request,urllib.parse,json,re,html,time
C=json.load(open('corps.json'))
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
def get(u,t=40,ua='KPC'): return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':ua}),timeout=t).read().decode('utf8','replace')
for n,i in C['ids'].items():
  owners={}
  for la,lo in C['pts'][n]:
    q={'geometry':'%s,%s'%(lo,la),'geometryType':'esriGeometryPoint','inSR':4326,'spatialRel':'esriSpatialRelIntersects','where':'1=1','outFields':'Unit_Nm,Loc_Own,Own_Name,Loc_Mang,Category','returnGeometry':'false','f':'json'}
    try:
      j=json.loads(get(P+'?'+urllib.parse.urlencode(q)))
      for f in j.get('features',[]):
        a=f['attributes']
        if a.get('Category')=='Fee': owners[(a['Unit_Nm'],a['Loc_Own'] or a['Own_Name'],a['Loc_Mang'])]=owners.get((a['Unit_Nm'],a['Loc_Own'] or a['Own_Name'],a['Loc_Mang']),0)+1
    except Exception as e: owners['ERR '+str(e)[:40]]=1
    time.sleep(0.5)
  quote=''
  try:
    T=re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',re.sub(r'(?s)<script.*?</script>|<style.*?</style>','',get('https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=%s'%i,ua='Mozilla/5.0')))))
    m=[T[max(0,k.start()-160):k.end()+160] for k in re.finditer(r'Corps|USACE|Army',T)]
    quote=' || '.join(m[:2])
  except Exception as e: quote='ERR '+str(e)
  print('##',n,i,'| PAD:',owners,'| KDFWR:',quote,flush=True)
