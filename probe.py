import urllib.request, json, urllib.parse
out=[]
def g(u, hdr=None):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u, headers=dict({'User-Agent':'KPC probe','Origin':'https://kentuckyportableclub.github.io'}, **(hdr or {}))), timeout=40)
        b=r.read(); return r.status, dict(r.headers), b
    except Exception as e:
        return 'ERR', {}, str(e).encode()
for base in ['https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites?f=json',
             'https://bio.discomap.eea.europa.eu/arcgis/rest/services?f=json',
             'https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/Natura2000Sites/MapServer?f=json',
             'https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/CDDA_Dyna_WM/MapServer?f=json']:
    s,h,b=g(base); out.append(f'== {base}\n{s} CORS={h.get("Access-Control-Allow-Origin")} {b[:1500].decode("utf-8","replace")}\n')
# POTA: european programs + how many parks
s,h,b=g('https://api.pota.app/programs')
try:
    P=json.loads(b); out.append('programs '+str(len(P))+' sample '+json.dumps(P[:3]))
except Exception as e: out.append('programs err '+str(e))
s,h,b=g('https://api.pota.app/locations')
try:
    L=json.loads(b); out.append('loc keys '+str(list(L[0].keys()))); 
    tot={}
    for l in L: tot[l.get('entityName','?')+'|'+l['locationDesc'].split('-')[0]]=tot.get(l.get('entityName','?')+'|'+l['locationDesc'].split('-')[0],0)+(l.get('parks') or 0)
    out.append('by entity '+json.dumps(sorted(tot.items(), key=lambda x:-x[1])[:60]))
except Exception as e: out.append('loc err '+str(e))
open('out.txt','w').write('\n'.join(out))
