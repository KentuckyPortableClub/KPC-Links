import json,urllib.request
P={'cf':'football/college-football','mb':'basketball/mens-college-basketball','wb':'basketball/womens-college-basketball','bb':'baseball/college-baseball'}
IDS={'cf':[96,97,98,2198,93,2413],'mb':[96,97,98,2198,93,2413,94,91],'wb':[96,97,98,2198,93,2413,94,91],'bb':[82,83,84,348,394,391,410,1143]}
out={}
for sp,ids in IDS.items():
    for i in ids:
        u=f'https://site.api.espn.com/apis/site/v2/sports/{P[sp]}/teams/{i}/schedule'
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0','Origin':'https://kentuckyportableclub.github.io'}),timeout=40)
            out[sp+':'+str(i)]={'acao':r.headers.get('Access-Control-Allow-Origin'),'j':json.load(r)}
        except Exception as e: out[sp+':'+str(i)]={'err':str(e)}
json.dump(out,open('espn2.json','w'))
