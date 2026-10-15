import urllib.request,json,time
def get(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'KPC','Origin':'https://kentuckyportableclub.github.io'}),timeout=30);return r.status,r.headers.get('Access-Control-Allow-Origin'),r.read()[:900]
    except Exception as e: return 'ERR',None,str(e).encode()
for u in ['https://api-db2.sotl.as/summits/near?lat=34.874&lon=-83.81&limit=5&maxDistance=20000',
 'https://api-db2.sotl.as/summits/W4G/NG-001',
 'https://api2.sota.org.uk/api/summits/W4G/NG-001',
 'https://api.open-meteo.com/v1/elevation?latitude=34.874&longitude=-83.81',
 'https://epqs.nationalmap.gov/v1/json?x=-83.81&y=34.874&units=Feet&wkid=4326']:
    s,c,b=get(u);print(u,s,c,b,'\n')
