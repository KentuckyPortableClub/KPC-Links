import urllib.request,itertools
base='1FAIpQLScWT7T2nNJytN8hDIn2HEI_2GSRLt_txXjdJ_-jmi{a}Tk1QwrQ'
H={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) Chrome/129 Safari/537.36'}
for a in ['0','O']:
  for b in ['I','l']:
    fid=base.format(a=a).replace('DIn2','D'+b+'n2')
    u='https://docs.google.com/forms/d/e/'+fid+'/viewform'
    try:
      r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=30); t=r.read().decode('utf8','replace'); print(r.status,fid,'KPC Email Updates' in t, 'entry.1708769741' in t or '1708769741' in t)
    except Exception as e: print('ERR',fid,e)
