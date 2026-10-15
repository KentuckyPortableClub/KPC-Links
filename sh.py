import urllib.request
for u in ['https://geo.fcc.gov/api/census/area?lat=38.55&lon=-84.8&censusYear=2020&format=json','https://nominatim.openstreetmap.org/search?q=Elmer+Davis+Lake,+KY,+USA&format=jsonv2&countrycodes=us&extratags=1&limit=3']:
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'KPC test','Origin':'https://kentuckyportableclub.github.io','Referer':'https://kentuckyportableclub.github.io/'}),timeout=30)
        print(u,r.status,r.headers.get('Access-Control-Allow-Origin'),r.read()[:500])
    except Exception as e: print(u,'ERR',e)
