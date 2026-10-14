"""Writes ky-trail-parks.json (the trail lists under the KY Park Commander map) from fers.json.
usage (repo root): python3 .claude/build/fers/trailparks.py"""
import json,os,re
HERE=os.path.dirname(os.path.abspath(__file__));R=os.path.abspath(os.path.join(HERE,'..','..','..'))+'/'
SP=json.load(open(HERE+'/fers.json'))['spots']
T={'sheltowee':('Sheltowee Trace National Recreation Trail','US-11181'),'pine-mountain':('Pine Mountain State Trail','US-10102'),'dawkins':('Dawkins Line Rail Trail State Park','US-1253'),
   'tears':('Trail of Tears National Historic Trail','US-3791'),'lewis':('Lewis and Clark National Historic Trail','US-4572')}
def how(d):
  h=d['how']
  if 'Water Route bank' in h: return 'shore of the '+('Tennessee River (Kentucky Lake)' if 'Kentucky Lake' in h else 'Mississippi River')+', within 100 ft of the water'
  if 'riverbank' in h.lower() or 'on the Ohio' in h: return 'Ohio River bank, within 100 ft of the water'
  if 'auto tour route' in h: return 'signed auto tour route along the park'
  if 'Historic Trail site' in h: return d.get('site',{}).get('why','NPS-listed site').split(' and the NPS')[0].replace('The National Park Service lists','NPS lists').rstrip('.')
  if 'through the park' in h: return (d.get('size') or '').replace(' inside','')+' of trail inside' if d.get('size') and 'trail' not in d['size'] else (d.get('size') or 'trail through the park')
  return h
out={}
for k,(name,ref) in T.items():
  items=[]
  for d in SP:
    if ref not in d['refs']: continue
    if k=='tears' and 'US-4572' in d['refs'] and len(d['refs'])==3: pass
    o=[(r,n) for r,n in zip(d['refs'],d['names']) if r!=ref]
    m=re.search(r'([\d.]+) mi',d.get('size') or '');miles=float(m.group(1)) if m else 0
    items.append({'refs':[r for r,_ in o],'names':[n for _,n in o],'type':d['type'],'miles':miles,'how':how(d),'auto':any('auto tour' in q['what'] for q in d['points'])})
  items.sort(key=lambda x:(x['type']!='3-fer',-x['miles']))
  out[k]={'name':name,'ref':ref,'parks':items}
open(R+'ky-trail-parks.json','w').write(json.dumps(out,ensure_ascii=False,separators=(',',':')))
for k,v in out.items(): print(k,len(v['parks']),[ '+'.join(p['refs'])+' '+p['type'] for p in v['parks']][:20])
