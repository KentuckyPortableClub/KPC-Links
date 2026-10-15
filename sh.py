import urllib.request,urllib.parse
P='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
u=P+'?'+urllib.parse.urlencode({'objectIds':'202789','outFields':'Unit_Nm,Loc_Own,Loc_Mang,Pub_Access,GIS_Acres','returnGeometry':'false','f':'html'})
r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'KPC'}),timeout=30);b=r.read().decode('utf8','replace')
import re;print(r.status,len(b),re.sub(r'<[^>]+>',' ',b)[-900:])
