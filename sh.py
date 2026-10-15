import urllib.request,urllib.parse
UA='Mozilla/5.0 (KPC-Links contest calendar)'
for m in ['September 2026','October 2026','November 2026','December 2026','January 2027']:
    u='https://www.arrl.org/files/file/Contest%20Corral/'+m.split()[1]+'/'+urllib.parse.quote(m+' Corral.pdf')
    try:
        d=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=40).read()
        open(m.replace(' ','_')+'.pdf','wb').write(d); print(m,'OK',len(d))
    except Exception as e: print(m,e)
