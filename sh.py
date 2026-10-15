import urllib.request,re
H={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/129 Safari/537.36'}
for u in ['https://www.peakbagger.com/search.aspx?ss=Pilot%20Knob','https://www.peakbagger.com/map/BigMap.aspx?cy=37.78&cx=-83.68&z=13','https://www.peakbagger.com/search.aspx?tid=R&lat=37.78&lon=-83.68&rad=5','https://peakbagger.com/RadiusSearch.aspx?lat=37.78&lon=-83.68&rad=5','https://www.peakbagger.com/search.aspx?tid=R&lat=37.78&lon=-83.68',
 'https://listsofjohn.com/search?q=Pilot+Knob','https://listsofjohn.com/mapf?lat=37.78&lon=-83.68&z=12','https://listsofjohn.com/map?lat=37.78&lon=-83.68&zoom=12','https://listsofjohn.com/','https://listsofjohn.com/searchres?s=Pilot+Knob']:
  try:
    r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=30); t=r.read().decode('utf8','replace')
    ti=re.search(r'<title>(.*?)</title>',t,re.S); print(r.status,u,'|',(ti.group(1).strip() if ti else '')[:80],'|',len(t), 'Pilot' in t, 'Radius' in t or 'radius' in t)
  except Exception as e: print('ERR',u,e)
