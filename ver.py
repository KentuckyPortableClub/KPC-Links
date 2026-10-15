import urllib.request,re,html
UA='Mozilla/5.0 (KPC-Links events finder)'
def txt(u):
    s=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=30).read().decode('utf8','replace')
    s=re.sub(r'(?is)<(script|style)\b.*?</\1>',' ',s);s=re.sub(r'<[^>]+>',' ',s);return re.sub(r'\s+',' ',html.unescape(s))
for u,kw in [('https://www.13colonies.net/','July|UTC|Z '),('https://www.nj2bb.org/museum/','June|weekend'),('https://illw.net/','August|weekend'),('https://en.wikipedia.org/wiki/Jamboree_on_the_Air','October|weekend'),('https://www.arrl.org/straight-key-night','January|UTC'),('https://www.arrl.org/Events/view/159881','Route|Sep|66')]:
    try:
        t=txt(u); hits=[t[max(0,m.start()-160):m.end()+160] for m in re.finditer(kw,t)][:5]
        print('=====',u); [print(' *',h) for h in hits]
    except Exception as e: print('=====',u,e)
