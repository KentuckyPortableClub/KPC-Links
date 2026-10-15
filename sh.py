import urllib.request,json,urllib.parse
H={'User-Agent':'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/129 Mobile Safari/537.36','Origin':'https://kentuckyportableclub.github.io','Accept':'*/*'}
for u in json.load(open('mr-urls.json')):
  if not any(k in u for k in ('arcgis','kygis','nationalmap')): continue
  try: r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60); b=r.read().decode('utf8','replace'); s=r.status
  except Exception as e: s=str(e); b=''
  print(s, b.count('"attributes"')+b.count('"Feature"'), 'err' if '"error"' in b else '', urllib.parse.unquote_plus(u)[:170])
