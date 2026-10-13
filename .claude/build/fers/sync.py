"""Push fers.json into the website files: the map page DATA, park 2-fer partners (tf) and the overlap map points.
usage (repo root): python3 .claude/build/fers/sync.py"""
import json,re,os
HERE=os.path.dirname(os.path.abspath(__file__));R=os.path.abspath(os.path.join(HERE,'..','..','..'))+'/'
SP=json.load(open(HERE+'/fers.json'))['spots']
p=R+'kpc-multi-park-spots.html';s=open(p).read()
s=re.sub(r'const DATA=\[.*?\];',lambda m:'const DATA='+json.dumps(SP,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';',s,count=1,flags=re.S);open(p,'w').write(s)
dd=json.load(open(R+'kpc-ky-data.json'));pairs={}
for x in SP:
  for a in x['refs']:
    for b in x['refs']:
      if a!=b and {a,b}!={'US-4572','US-3791'}: pairs.setdefault(a,set()).add(b)
for pk in dd['parks']:
  old=pk.get('tf') or [];pk['tf']=[r for r in old if r in pairs.get(pk['c'],set())]+[r for r in sorted(pairs.get(pk['c'],set())) if r not in old]
open(R+'kpc-ky-data.json','w').write(json.dumps(dd,separators=(',',':'),ensure_ascii=False))
g=json.load(open(R+'ky-overlaps.geojson'))
have={frozenset(r for r,_ in f['properties']['pota']) for f in g['features']}
for d in SP:
  if frozenset(d['refs']) in have or any(r in ('US-11181','US-10102') for r in d['refs']): continue
  p0=d['points'][0];pr={'kind':'2fer','areas':d['names'],'types':['Park','National Historic Trail'],'pota':[[r,n] for r,n in zip(d['refs'],d['names'])],'kff':[],'sota':[],'nht':d['note'].split('. ')[0]}
  if 'Water Route bank' in d['how']: pr['river']=d['how'].replace(' bank','');pr['miles']=re.sub(r'[^0-9.]','',d['size'].split(' mi')[0]) or '?'
  g['features'].append({'type':'Feature','geometry':{'type':'Point','coordinates':[p0['lo'],p0['la']]},'properties':pr})
AUTO={'US-3788':'US 60 / US 51','US-3779':'KY 338'}
for f in g['features']:
  pr=f['properties'];refs=[r for r,_ in pr['pota']]
  for k,road in AUTO.items():
    if 'nht' in pr and k in refs and 'auto tour' not in pr['nht']:
      pr['nht']+=f'. The signed Lewis & Clark auto tour route ({road}) runs along the park line, so a spot inside the park within 100 ft of a signed stretch may also work'
open(R+'ky-overlaps.geojson','w').write(json.dumps(g,separators=(',',':'),ensure_ascii=False))
print('spots',len(SP),'features',len(g['features']))
