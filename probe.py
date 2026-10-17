import urllib.request, json, urllib.parse, re, unicodedata, random, collections
random.seed(7); out=[]
B='https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/'
N2K=B+'Natura2000Sites/MapServer/2/query'; NAT=B+'CDDA_Dyna_WM/MapServer/4/query'
def g(u):
    try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent':'KPC probe'}), timeout=60).read())
    except Exception as e: return None
GEN=r'\b(national|nationalpark|nature|natural|naturale|natura|naturpark|naturschutzgebiet|landschaftsschutzgebiet|nsg|lsg|ffh|spa|sac|sci|park|parks|parc|parco|parque|krajobrazowy|rezerwat|obszar|chronionego|krajobrazu|regional|regionale|nazionale|nacional|reserve|riserva|reserva|naturreservat|area|site|zone|zona|sito|the|of|and|de|del|della|di|du|des|la|le|les|der|die|das|von|im|am|en|et|y|e|i|och|og)\b'
def deacc(s): return ''.join(c for c in unicodedata.normalize('NFD', str(s or '')) if unicodedata.category(c)!='Mn').lower()
def words(s):
    s=re.sub(r'[^a-z0-9 ]',' ',re.sub(r'["\'„“”«»]',' ',deacc(s))); s=re.sub(GEN,' ',s); return [w for w in s.split() if len(w)>2]
def sim(a,b):
    A=words(a); Bs=set(words(b))
    if not A or not Bs: return 0
    hit=sum(1 for w in A if w in Bs or any(len(x)>4 and len(w)>4 and (x.startswith(w[:5]) or w.startswith(x[:5])) for x in Bs))
    return hit/max(len(A),len(Bs))
def at(url,la,lo,d,fields):
    q={'geometry':f'{lo-d},{la-d},{lo+d},{la+d}','geometryType':'esriGeometryEnvelope'} if d else {'geometry':f'{lo},{la}','geometryType':'esriGeometryPoint'}
    q.update({'inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':fields,'returnGeometry':'false','f':'json'})
    j=g(url+'?'+urllib.parse.urlencode(q)); return [f['attributes'] for f in (j or {}).get('features',[])]
L=g('https://api.pota.app/locations') or []
res=collections.Counter(); bytype=collections.defaultdict(lambda:[0,0]); fails=[]
for cc in ['DE','FR','IT','ES','PL','SE','NL','CZ','AT','PT','FI','GB']:
    descs=[l['locationDesc'] for l in L if l['locationDesc'].split('-')[0]==cc]
    parks=[]
    for d in random.sample(descs, min(4,len(descs))):
        parks += (g('https://api.pota.app/location/parks/'+d) or [])
    sample=random.sample(parks, min(20,len(parks)))
    for p in sample:
        la,lo=float(p['latitude']),float(p['longitude']); name=p['name']
        det=g('https://api.pota.app/park/'+p['reference']) or {}; typ=det.get('parktypeDesc','')
        best=0; bn=''
        for d in [0,0.01]:
            C=[x['SITENAME'] for x in at(N2K,la,lo,d,'SITENAME')]+[x['siteName'] for x in at(NAT,la,lo,d,'siteName')]
            for c in C:
                s=sim(name,c)
                if s>best: best,bn=s,c
            if best>=.5: break
        ok=best>=.5; res[(cc,ok)]+=1; bytype[typ][0]+=ok; bytype[typ][1]+=1
        if not ok and len(fails)<40: fails.append(f'{p["reference"]} {name} [{typ}] best={bn!r} {best:.2f}')
out.append('by country (matched, total): '+json.dumps({cc:[res[(cc,True)],res[(cc,True)]+res[(cc,False)]] for cc in ['DE','FR','IT','ES','PL','SE','NL','CZ','AT','PT','FI','GB']}))
out.append('by type: '+json.dumps({k:v for k,v in sorted(bytype.items(), key=lambda x:-x[1][1])}, ensure_ascii=False))
out+=fails
open('out.txt','w').write('\n'.join(out))
