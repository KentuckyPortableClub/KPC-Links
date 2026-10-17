import urllib.request, urllib.parse
out=[]
def post(ua, origin=True, method='POST', ct='application/x-www-form-urlencoded;charset=UTF-8'):
    body=urllib.parse.urlencode({'KEY':'ABCD-1234-EFGH-5678','ACTION':'STATUS'}).encode()
    h={'User-Agent':ua,'Content-Type':ct}
    if origin: h['Origin']='https://kentuckyportableclub.github.io'
    if method=='OPTIONS': h.update({'Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type'}); body=None
    try:
        r=urllib.request.urlopen(urllib.request.Request('https://logbook.qrz.com/api', data=body, headers=h, method=method), timeout=40)
        return f'{r.status} ACAO={r.headers.get("Access-Control-Allow-Origin")} ACAM={r.headers.get("Access-Control-Allow-Methods")} body={r.read()[:300]!r}'
    except urllib.error.HTTPError as e: return f'HTTP {e.code} ACAO={e.headers.get("Access-Control-Allow-Origin")} body={e.read()[:300]!r}'
    except Exception as e: return 'ERR '+str(e)
CH='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
out.append('chrome UA + origin: '+post(CH))
out.append('chrome UA no origin: '+post(CH, False))
out.append('app UA: '+post('KPCHuntersLounge/1.0 (KZ4CP)'))
out.append('apps script UA: '+post('Mozilla/5.0 (compatible; Google-Apps-Script; beanserver; +https://script.google.com; id: UAEmdDd-x)'))
out.append('OPTIONS: '+post(CH, True, 'OPTIONS'))
out.append('text/plain: '+post(CH, True, 'POST', 'text/plain;charset=UTF-8'))
open('out.txt','w').write('\n'.join(out))
