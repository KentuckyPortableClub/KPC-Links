import json,urllib.request
UA={'User-Agent':'KPC-Links/1.0'}
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60) as r: return json.loads(r.read())
o=open('out.txt','w')
p=get('https://api.pota.app/programs'); o.write('PROGRAMS '+json.dumps(p)[:6000]+'\n')
for u in ['https://api.pota.app/locations','https://api.pota.app/program/locations/XE','https://api.pota.app/location/parks/XE-BC','https://api.pota.app/locations/XE']:
    try: j=get(u); o.write(u+' :: '+json.dumps(j)[:2500]+'\n')
    except Exception as e: o.write(u+' ERR '+str(e)+'\n')
