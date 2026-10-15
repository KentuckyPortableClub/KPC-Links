import urllib.request,urllib.parse,json,re,html
K='https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Public_Hunting_Areas_WGS84WM/MapServer/1/query?'
names=['Blackford Oaks WMA','Boone Forestlands WMA','Cumberland Forest WMA','Elk Forest WMA','Fortner-Davis WMA','Legacy WMA','Pocahontas WMA','RH Group WMA','Robinson Forest WMA','Asher Hunting Access Area','Martins Fork WMA and State Natural Area','Knobs State Forest and WMA']
for n in names:
  j=json.loads(urllib.request.urlopen(K+urllib.parse.urlencode({'where':f"AREANAME='{n}'",'outFields':'AREANAME,MANAGER,KDFWR_ID,DETAIL,ACRES_CAL,Counties,WMA,AreaOpen','returnGeometry':'false','f':'json'}),timeout=40).read())
  for f in j.get('features',[])[:1]:
    a=f['attributes'];print('##',a['AREANAME'],'|',a['MANAGER'],'|',round(a['ACRES_CAL'] or 0),'ac |',a['Counties'],'| open',a['AreaOpen'])
    try:
      t=urllib.request.urlopen(urllib.request.Request(a['DETAIL'],headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read().decode('utf8','replace')
      t=html.unescape(re.sub(r'<[^>]+>',' ',re.sub(r'(?s)<script.*?</script>|<style.*?</style>','',t)));t=re.sub(r'\s+',' ',t)
      i=t.find('Owner');print('   ',t[max(0,i-200):i+400] if i>=0 else t[:600])
    except Exception as e: print('   detail ERR',e)
