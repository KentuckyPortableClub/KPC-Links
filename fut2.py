import json,urllib.request,urllib.parse,re,html
out={}
def get(u,t=120,raw=False):
    r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 KPC-Links park research'}),timeout=t).read()
    return r.decode('utf8','replace') if raw else json.loads(r)
NAMES=['Cascade','Clear Creek','Bullock','Guist','Linville','Wilgreen','Wood Creek','Beaver','Kingfisher','Carpenter','Boltz']
rx=re.compile('|'.join(NAMES),re.I)
KY='https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/'
for svc in ['Ky_Fish_Wildlife_WGS84WM','Ky_KNP_State_Nature_Preserves_WGS84WM','Ky_Water_WGS84WM']:
    try:
        m=get(KY+svc+'/MapServer?f=json'); print(svc,[(l['id'],l['name']) for l in m.get('layers',[])])
        for l in m.get('layers',[]):
            if l.get('subLayerIds'): continue
            try:
                j=get(KY+svc+'/MapServer/%d/query?where=1%%3D1&outFields=*&returnGeometry=false&resultRecordCount=4000&f=json'%l['id'])
                fs=j.get('features',[]); hits=[f['attributes'] for f in fs if rx.search(json.dumps(f['attributes']))]
                print(' layer',l['id'],l['name'],len(fs),'hits',len(hits)); [print('   ',{k:v for k,v in h.items() if v not in (None,'') and not k.startswith(('Shape','Global','created','last'))}) for h in hits[:25]]
                if hits and len(hits)<60:
                    ids=','.join(str(h.get('OBJECTID')) for h in hits if h.get('OBJECTID') is not None)
                    if ids:
                        g=get(KY+svc+'/MapServer/%d/query?'%l['id']+urllib.parse.urlencode({'objectIds':ids,'outFields':'*','outSR':4326,'geometryPrecision':5,'f':'geojson'}),180)
                        out[svc+'_%d'%l['id']]=g
            except Exception as e: print(' layer',l['id'],e)
    except Exception as e: print(svc,e)
# KDFWR waterbody pages
W={'Bullock Pen':51,'Wilgreen':121,'Wood Creek':102,'Beaver':49,'Kingfisher':40,'Carpenter':39}
try:
    idx=get('https://app.fw.ky.gov/fisheries/waterbody.aspx',raw=True)
    for m in re.finditer(r'waterbodydetail\.aspx\?wid=(\d+)[^>]*>([^<]+)<',idx,re.I):
        if rx.search(m.group(2)): print('wb idx',m.group(1),html.unescape(m.group(2)))
        for n in ['Guist','Linville','Boltz']:
            if n.lower() in m.group(2).lower(): W[n]=int(m.group(1))
except Exception as e: print('idx',e)
print(W)
for n,w in W.items():
    try:
        t=get('https://app.fw.ky.gov/fisheries/waterbodydetail.aspx?wid=%d'%w,raw=True)
        txt=re.sub(r'\s+',' ',html.unescape(re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S)))
        txt=re.sub(r'<[^>]+>',' | ',txt); txt=re.sub(r'(\s*\|\s*)+',' | ',txt)
        i=txt.lower().find('county'); out['wb_'+n]=txt[:20000]; print('WB',n,w,txt[max(0,i-400):i+1600]); 
    except Exception as e: print('wb',n,e)
json.dump(out,open('fut2.json','w'))
