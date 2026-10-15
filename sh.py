import urllib.request,re
H={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) Chrome/129 Safari/537.36'}
def get(u): return urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=40).read().decode('utf8','replace')
for u in ['https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=9719','https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=224','https://parks.ky.gov/lucas/parks/resort/barren-river-lake-state-resort-park','https://eec.ky.gov/Nature-Preserves/Locations/Pages/Bad-Branch.aspx']:
  t=get(u); print('##',u)
  for m in re.finditer(r'(?i)[^<>"\']{0,80}(map|\.pdf)[^<>]{0,160}',t):
    s=m.group(0)
    if re.search(r'(?i)map_images|\.pdf|detailed map|mapping|park map|trail map|boundary|arcgis|webmap|kml',s) and not re.search('sitemap|Forecast|Title%20VI',s): print('  ',s.strip()[:240])
