import subprocess,sys,urllib.parse
subprocess.run([sys.executable,'-m','pip','install','-q','playwright'],check=True)
subprocess.run([sys.executable,'-m','playwright','install','--with-deps','chromium'],check=True,capture_output=True)
from playwright.sync_api import sync_playwright
PAD='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0'
KY='https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Public_Hunting_Areas_WGS84WM/MapServer/1'
tests={'pad':'https://www.arcgis.com/apps/mapviewer/index.html?'+urllib.parse.urlencode({'url':PAD,'center':'-86.9755,37.8452','level':15}),
 'ky':'https://www.arcgis.com/apps/mapviewer/index.html?'+urllib.parse.urlencode({'url':KY,'center':'-87.09,37.40','level':13}),
 'padmapserver':'https://www.arcgis.com/apps/mapviewer/index.html?'+urllib.parse.urlencode({'url':PAD.rsplit('/',1)[0],'center':'-86.9755,37.8452','level':15})}
with sync_playwright() as p:
  b=p.chromium.launch(); 
  for k,u in tests.items():
    pg=b.new_page(viewport={'width':1000,'height':800}); print(k,u)
    try:
      pg.goto(u,timeout=60000); pg.wait_for_timeout(25000); pg.screenshot(path=f'gis-{k}.png'); print(' title',pg.title()); print(' text',pg.inner_text('body')[:400].replace('\n',' | '))
    except Exception as e: print(' ERR',e)
  b.close()
