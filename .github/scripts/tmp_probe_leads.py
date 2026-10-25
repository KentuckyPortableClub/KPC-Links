import json,re,urllib.request,urllib.parse,time
def gj(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'KPC-probe'}),timeout=25) as r: return json.load(r)
    except Exception as e: return {'error':str(e)[:80]}
leads=json.load(open('data/state-gis-leads-oct24.json'))['states']
out={}
NM=re.compile(r'name|park|unit|prop|site|area|title',re.I)
for st,L in sorted(leads.items()):
    for l in L:
        u=l['link'].split()[0].rstrip('/')
        if 'rest/services' not in u: out.setdefault(st,[]).append({'url':u,'skip':'not a layer link'});continue
        base=re.sub(r'\?.*','',u)
        j=gj(base+'?f=json'); ent={'url':u}
        if 'error' in j: ent['err']=str(j['error'])[:80];out.setdefault(st,[]).append(ent);continue
        lids=[]
        if j.get('layers') is not None and j.get('type') is None or re.search(r'(Feature|Map)Server$',base): lids=[(x['id'],x['name']) for x in j.get('layers',[])][:40]
        else: lids=[(None,j.get('name'))]
        ent['layers']=[]
        for lid,ln in lids:
            lu=base if lid is None else f'{base}/{lid}'
            lj=gj(lu+'?f=json')
            if lj.get('geometryType')!='esriGeometryPolygon': continue
            cnt=gj(lu+'/query?where=1%3D1&returnCountOnly=true&f=json').get('count')
            fl=[f['name'] for f in lj.get('fields',[]) if f.get('type')=='esriFieldTypeString']
            nm=[f for f in fl if NM.search(f)][:6]
            smp=[]
            if nm:
                q=gj(lu+'/query?where=1%3D1&outFields='+urllib.parse.quote(nm[0])+'&returnGeometry=false&resultRecordCount=6&f=json')
                smp=[str((f.get('attributes') or {}).get(nm[0]))[:40] for f in q.get('features',[])]
            ent['layers'].append({'url':lu,'name':ln,'count':cnt,'strfields':nm,'sample':smp,'max':lj.get('maxRecordCount')})
            time.sleep(.2)
        out.setdefault(st,[]).append(ent)
json.dump(out,open('data/state-gis-probe-oct24.json','w'),indent=1)
print('done',sum(len(v) for v in out.values()))
