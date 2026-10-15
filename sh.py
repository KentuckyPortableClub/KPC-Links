import urllib.request,re
def get(u): return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 KPC'}),timeout=40).read().decode('utf8','replace')
t=get('https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=9003')
for m in sorted(set(re.findall(r'(?:href|src)="([^"]+)"',t))): print('L',m)
for m in sorted(set(re.findall(r'https?://[^\s"\'<>]+',t))): print('U',m)
i=t.lower().find('map');print(t[i-500:i+1500] if i>0 else '')
