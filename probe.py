import urllib.request, urllib.parse, json
out=[]
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent':'KPC probe'}), timeout=60) as f: return json.loads(f.read().decode('utf-8','replace'))
    except Exception as e: return {'err': str(e)[:200]}
j=get('https://geo.environnement.gouv.qc.ca/donnees/rest/services/Biodiversite/Aires_protegees/MapServer?f=json')
out.append('QC layers: '+json.dumps([(l.get('id'),l.get('name')) for l in j.get('layers',[])], ensure_ascii=False)[:3000])
for q in ['Nova Scotia provincial parks','Ontario conservation areas','conservation authority lands Ontario','Northwest Territories territorial parks','Manitoba wildlife management areas','New Brunswick wildlife management areas','New Brunswick protected natural areas','Yukon recreation sites','Prince Edward Island provincial parks','Saskatchewan recreation sites','réserves naturelles reconnues','Nunavut territorial parks']:
    s=get('https://www.arcgis.com/sharing/rest/search?f=json&num=8&q='+urllib.parse.quote(q+' type:"Feature Service" OR type:"Map Service"'))
    out.append('\n## '+q)
    for r in s.get('results',[]): out.append(f"- {r.get('title')} | {r.get('owner')} | {r.get('type')} | {r.get('url')}")
open('out.txt','w').write('\n'.join(out))
