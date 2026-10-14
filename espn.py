import json,urllib.request
def get(u):
    r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0','Origin':'https://kentuckyportableclub.github.io'}),timeout=60)
    return r.headers.get('Access-Control-Allow-Origin'),json.load(r)
out={}
KEY=['Kentucky','Louisville','Western Kentucky','Eastern Kentucky','Murray','Morehead','Northern Kentucky','Bellarmine','Kentucky State']
for sp,lg in [('football','college-football'),('basketball','mens-college-basketball'),('basketball','womens-college-basketball'),('baseball','college-baseball')]:
    try:
        cors,j=get(f'https://site.api.espn.com/apis/site/v2/sports/{sp}/{lg}/teams?limit=2000')
        teams=[t['team'] for t in j['sports'][0]['leagues'][0]['teams']]
        out[lg]={'cors':cors,'n':len(teams),'ky':[{k:t.get(k) for k in('id','location','displayName','abbreviation','color','alternateColor')}|{'logo':(t.get('logos') or [{}])[0].get('href')} for t in teams if any(x in t.get('displayName','') for x in KEY)]}
    except Exception as e: out[lg]={'err':str(e)}
try:
    cors,j=get('https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/96/schedule')
    out['sample']={'cors':cors,'ev':j.get('events',[])[:2]}
except Exception as e: out['sample']={'err':str(e)}
json.dump(out,open('espn.json','w'),indent=1)
