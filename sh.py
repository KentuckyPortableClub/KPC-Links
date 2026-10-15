import urllib.request
def get(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'KPC','Origin':'https://kentuckyportableclub.github.io'}),timeout=30);return r.status,r.headers.get('Access-Control-Allow-Origin'),r.read()[:700]
    except Exception as e: return 'ERR',None,str(e).encode()
for u in ['https://api.sotl.as/summits/near?lat=34.874&lon=-83.81&limit=5&maxDistance=20000','https://api.sotl.as/summits/W4G/NG-001','https://sotl.as/api/summits/near?lat=34.874&lon=-83.81&limit=5','https://api2.sota.org.uk/api/regions/W4G/NG','https://storage.sota.org.uk/summitslist.csv']:
    s,c,b=get(u);print(u,s,c,b[:500],'\n')
