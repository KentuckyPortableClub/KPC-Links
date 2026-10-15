import urllib.request,re,html
UA='Mozilla/5.0 (KPC-Links contest calendar)'
def txt(u):
    s=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=30).read().decode('utf8','replace')
    s=re.sub(r'(?is)<(script|style)\b.*?</\1>',' ',s);s=re.sub(r'<[^>]+>',' ',s);return re.sub(r'\s+',' ',html.unescape(s))
KW=r'(last|first|second|third|fourth|full)\s+(full\s+)?(weekend|saturday|sunday)|\d{4}\s*(UTC|Z)\s+(Saturday|Sunday)|weekend of'
for u in ['https://cqww.com/rules.htm','https://www.cqwpx.com/rules.htm','https://www.cq160.com/rules.htm','https://ncjweb.com/naqp/','https://www.ncjweb.com/naqp-rules/','https://www.ohqp.org/','https://www.hdxcc.org/inqp/','https://www.tnqp.org/','https://www.w0ma.org/mo_qso_party/','https://www.kyqp.org/','https://www.kyqsoparty.org/','https://wvqp.org/','https://www.qsl.net/kd4wsx/','https://www.ilqp.org/','https://www.qsl.net/sterling/','https://www.winterfieldday.org/']:
    try:
        t=txt(u); hits=[t[max(0,m.start()-140):m.end()+140] for m in re.finditer(KW,t,re.I)][:3]
        print('=====',u,len(t)); [print(' *',h) for h in hits]
    except Exception as e: print('=====',u,'ERR',e)
