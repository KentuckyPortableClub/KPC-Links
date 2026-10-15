import urllib.request,re
H={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) Chrome/129 Safari/537.36'}
for u in ['https://forms.gle/cv2fygMCDReVpjWk9','https://docs.google.com/forms/d/e/1FAIpQLSfW0ExC6PYtznIS4fll4AUx5Cp83zOBBT2_882thoQj8fi36w/viewform']:
  try:
    r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=30); t=r.read().decode('utf8','replace')
    ti=re.search(r'<title>(.*?)</title>',t,re.S); print(u,'->',r.geturl()[:140],'|',ti.group(1) if ti else '')
    print('  questions:', re.findall(r'\[\d+,"([^"]{2,80})",null,\d',t)[:12])
  except Exception as e: print(u,'ERR',e)
