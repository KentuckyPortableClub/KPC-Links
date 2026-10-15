import urllib.request,re,html
H={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) Chrome/129 Safari/537.36'}
def get(u): return urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=40).read().decode('utf8','replace')
for u in ['https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=9719','https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=224',
 'https://parks.ky.gov/lucas/parks/resort/barren-river-lake-state-resort-park','https://eec.ky.gov/Nature-Preserves/Locations/Pages/Bad-Branch.aspx','https://eec.ky.gov/Nature-Preserves/Locations/Pages/Dr.-William-H.-Martin-WWCA.aspx','https://www.nps.gov/maca/planyourvisit/maps.htm','https://www.fws.gov/refuge/clarks-river']:
  try: t=get(u)
  except Exception as e: print('##',u,'ERR',e); continue
  print('##',u,len(t))
  for m in re.finditer(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>',t,re.S|re.I):
    h,x=m.group(1),re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',m.group(2)))).strip()
    if re.search(r'map|\.pdf|boundar',h+' '+x,re.I) and not re.search(r'sitemap|google\.com/maps\?q|mapquest',h,re.I): print('  ',x[:60],'|',h[:160])
