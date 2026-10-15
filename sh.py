import subprocess,sys,urllib.parse,site,importlib
subprocess.run([sys.executable,'-m','pip','install','-q','--user','--break-system-packages','playwright'])
site.addsitedir(site.getusersitepackages()); importlib.invalidate_caches()
subprocess.run([sys.executable,'-m','playwright','install','--with-deps','chromium'],check=False)
from playwright.sync_api import sync_playwright
PAD='https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0'
KY='https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Public_Hunting_Areas_WGS84WM/MapServer/1'
tests={'pad':'https://www.arcgis.com/apps/mapviewer/index.html?'+urllib.parse.urlencode({'url':PAD,'center':'-86.9755,37.8452','level':14}),
 'ky':'https://www.arcgis.com/apps/mapviewer/index.html?'+urllib.parse.urlencode({'url':KY,'center':'-89.03,37.15','level':12})}
with sync_playwright() as p:
  b=p.chromium.launch(); 
  for k,u in tests.items():
    pg=b.new_page(viewport={'width':1000,'height':800}); print(k,u)
    try:
      reqs=[]; pg.on('response',lambda r: reqs.append((r.status,r.url[:150])) if ('nationalmap' in r.url or 'kygisserver' in r.url) else None); pg.goto(u,timeout=60000); pg.wait_for_timeout(45000); print(' reqs',reqs[-8:]); pg.screenshot(path=f'gis-{k}.png'); print(' title',pg.title()); print(' text',pg.inner_text('body')[:400].replace('\n',' | '))
    except Exception as e: print(' ERR',e)
  b.close()
