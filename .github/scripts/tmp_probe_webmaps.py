import json,urllib.request
def gj(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'KPC-probe'}),timeout=40) as r: return json.load(r)
    except Exception as e: return {'error':str(e)[:100]}
out={}
for nm,app in (('AB','e5651574de1342d7ae8277ef415864be'),('BC','4e9f5f3a722b45c8a86696f6c91d09c6')):
    e={'app':app}
    item=gj(f'https://www.arcgis.com/sharing/rest/content/items/{app}?f=json');e['title']=item.get('title');e['owner']=item.get('owner');e['org']=item.get('orgId')
    d=gj(f'https://www.arcgis.com/sharing/rest/content/items/{app}/data?f=json');e['err']=d.get('error')
    wm=(d.get('map') or {}).get('itemId');e['webmap']=wm
    layers=[]
    if wm:
        w=gj(f'https://www.arcgis.com/sharing/rest/content/items/{wm}/data?f=json')
        def walk(L):
            for l in L or []:
                layers.append({'title':l.get('title'),'url':l.get('url'),'type':l.get('layerType')})
                walk(l.get('layers'))
        walk(w.get('operationalLayers'))
    e['layers']=layers
    out[nm]=e
json.dump(out,open('data/webmap-probe-oct25.json','w'),indent=1);print('done')
