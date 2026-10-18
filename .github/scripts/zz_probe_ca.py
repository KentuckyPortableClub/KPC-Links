import json, urllib.request, urllib.parse
UA = {'User-Agent': 'KPC (kentuckyportableclub.github.io)'}
def g(u, p=None):
    if p: u += '?' + urllib.parse.urlencode(p)
    try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read().decode('utf-8', 'replace'))
    except Exception as e: return {'ERR': str(e)[:120]}
out = []
def lay(u):
    j = g(u, {'f': 'json'})
    if 'ERR' in j: out.append(f'{u} ERR {j["ERR"]}'); return
    out.append(u + ' :: ' + ' | '.join(f"{l.get('id')}={l.get('name')}" for l in (j.get('layers') or [])[:60]))
for u in ['https://geo.environnement.gouv.qc.ca/donnees/rest/services/Biodiversite/Aires_protegees/MapServer',
          'https://services2.arcgis.com/wCOMu5IS7YdSyPNx/arcgis/rest/services/vw_Places_Public_lieux_public_APCA/FeatureServer',
          'https://maps.gov.bc.ca/arcgis/rest/services/whse/bcgw_pub_whse_tantalis/MapServer',
          'https://maps.gov.bc.ca/arcgis/rest/services/whse/bcgw_pub_whse_forest_tenure/MapServer',
          'https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open03/MapServer',
          'https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open06/MapServer',
          'https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open01/MapServer']:
    lay(u)
for q in ['Conservation Authority Property Ontario', 'Conservation Areas Ontario conservation authority', 'parcs régionaux Québec', 'parc régional limites', 'Prince Edward Island protected areas',
          'PEI provincial parks boundaries', 'National Historic Sites boundaries Parks Canada', 'lieux historiques nationaux limites', 'Saskatchewan regional parks', 'réserves naturelles reconnues',
          'Nova Scotia provincial parks boundaries', 'New Brunswick provincial parks', 'Yukon territorial parks', 'Northwest Territories territorial parks']:
    j = g('https://www.arcgis.com/sharing/rest/search', {'q': q + ' type:"Feature Service" OR type:"Map Service"', 'num': 8, 'f': 'json'})
    out.append('SEARCH ' + q + ' :: ' + ' || '.join(f"{r.get('title')} [{r.get('owner')}] {r.get('url')}" for r in j.get('results', [])))
txt = '\n'.join(out)
open('probe.txt', 'w').write(txt)
for i in range(0, min(len(txt), 36000), 3900):
    print('::notice title=probe %d::%s' % (i // 3900, txt[i:i + 3900].replace('%', '%25').replace('\n', '%0A')))
