import urllib.request,urllib.parse,re,html,json,datetime as dt
UA='Mozilla/5.0 (KPC-Links events finder)'
def get(u,data=None):
    b=urllib.parse.urlencode(data).encode() if data is not None else None
    with urllib.request.urlopen(urllib.request.Request(u,data=b,headers={'User-Agent':UA}),timeout=40) as r: return r.read().decode('utf8','replace'),r.geturl()
t=dt.date.today()
for fmt in ('%m/%d/%Y','%Y-%m-%d'):
    f={'_method':'POST','data[Search][call_sign]':'','data[Search][keywords]':'','data[Location][zip]':'','data[Location][area]':'','data[Location][city]':'','data[Location][state]':'','data[Location][division_id]':'','data[Location][section_id]':'','data[Location][country]':'','data[Date][start]':t.strftime(fmt),'data[Date][end]':(t+dt.timedelta(days=45)).strftime(fmt)}
    s,u=get('https://www.arrl.org/special-event-stations',f)
    links=sorted(set(re.findall(r'href="(/special-event[s]?/[^"#?]+)"',s)))
    print(fmt,len(s),u,len(links),links[:10])
    open('ses-res-%s.html'%fmt.replace('/','').replace('%',''),'w').write(s)
    pg=re.findall(r'href="([^"]*page:\d+[^"]*)"',s); print('pages',sorted(set(pg))[:10])
    if links:
        d,_=get('https://www.arrl.org'+[l for l in links if l not in('/special-events-application',)][0]); open('ses-detail.html','w').write(d)
        break
