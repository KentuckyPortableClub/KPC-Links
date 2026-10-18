import json, re, urllib.request, urllib.parse
UA = {'User-Agent': 'KPC (kentuckyportableclub.github.io)'}
out = []
def get(u, n=400000):
    try:
        return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90).read(n).decode('utf-8', 'replace')
    except Exception as e:
        return 'ERR ' + str(e)[:120]
def say(*a): out.append(' '.join(str(x) for x in a))
# 1 BLM lands folder + WSA services
t = get('https://gis.blm.gov/arcgis/rest/services/lands?f=json')
say('BLM lands folder:', t[:1500])
for s in ('BLM_Natl_NLCS_WLD_WSA', 'BLM_Natl_NLCS_WSA_poly', 'BLM_Natl_NLCS_Wilderness_WSA'):
    say(s, get('https://gis.blm.gov/arcgis/rest/services/lands/%s/MapServer?f=json' % s)[:800])
# 2 Oklahoma WMAs on ArcGIS Online
for q in ('Oklahoma wildlife management areas ODWC', 'ODWC WMA boundaries', 'Oklahoma Department of Wildlife Conservation'):
    t = get('https://www.arcgis.com/sharing/rest/search?' + urllib.parse.urlencode({'q': q, 'f': 'json', 'num': 15}))
    try:
        for r in json.loads(t).get('results', []):
            say('AGOL', q, '|', r.get('title'), '|', r.get('type'), '|', r.get('owner'), '|', r.get('url'))
    except Exception: say('AGOL ERR', t[:200])
# 3 Wales (DataMapWales) WFS layers
t = get('https://datamap.gov.wales/geoserver/ows?service=WFS&version=2.0.0&request=GetCapabilities', 6000000)
names = re.findall(r'<(?:wfs:)?Name>([^<]+)</', t)
say('DataMapWales layers', len(names), t[:150] if not names else '')
for n in names:
    if re.search(r'nrw|sssi|nature|reserve|country.?park|national.?park|aonb|landscape|protected', n, re.I): say('  WALES', n)
# 4 NatureScot WFS layers
t = get('https://ogc.nature.scot/geoserver/protectedareas/wfs?service=WFS&version=2.0.0&request=GetCapabilities', 3000000)
for n in re.findall(r'<(?:wfs:)?Name>([^<]+)</', t): say('  SCOT', n)
open('.claude/build/ap/probe2.txt', 'w').write('\n'.join(out))
print('::notice title=probe2::%d lines' % len(out))
