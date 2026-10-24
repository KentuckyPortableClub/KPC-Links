#!/usr/bin/env python3
"""Find each state's own GIS boundary layers (state parks, wildlife areas, state forests, nature preserves, trust land)
for the Map Rep Tool Box, and check that they answer. Writes data/state-gis-found.json (everything found, for Claude to
curate into data/state-gis.json). One-time / occasional run; never fails the workflow.

How: (1) ArcGIS Online public search for "<State> state parks" etc. (Feature Services + Map Services), (2) the state GIS
server roots listed in ROOTS are crawled (folders → services → layers). Every polygon layer whose name/fields look like a
park or wildlife layer is queried once (count) and its fields are saved."""
import json, re, sys, time, urllib.request, urllib.parse, concurrent.futures as cf

UA = 'KPC-MapRep-state-gis/1.0 (Kentucky Portable Club; brandonwhite42166@gmail.com)'
STATES = {'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'}
# state GIS server roots worth crawling (best guesses; a root that does not answer is just skipped)
ROOTS = {
    'TN': ['https://tnmap.tn.gov/arcgis/rest/services'], 'OH': ['https://gis.ohiodnr.gov/arcgis/rest/services', 'https://gis.ohiodnr.gov/arcgis_odnr/rest/services'],
    'IN': ['https://gisdata.in.gov/server/rest/services'], 'IL': ['https://gis.dnr.illinois.gov/arcgis/rest/services', 'https://maps.isgs.illinois.edu/arcgis/rest/services'],
    'TX': ['https://tpwd.texas.gov/arcgis/rest/services'], 'FL': ['https://ca.dep.state.fl.us/arcgis/rest/services', 'https://atoll.floridamarine.org/arcgis/rest/services', 'https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services'],
    'MI': ['https://gisagocss.state.mi.us/arcgis/rest/services', 'https://services3.arcgis.com/Jdnp1TjADvSDxMAX/arcgis/rest/services'], 'MN': ['https://arcgis.dnr.state.mn.us/host/rest/services', 'https://arcgis.dnr.state.mn.us/arcgis/rest/services'],
    'WI': ['https://dnrmaps.wi.gov/arcgis/rest/services', 'https://dnrmaps.wi.gov/arcgis2/rest/services'], 'PA': ['https://www.gis.dcnr.state.pa.us/arcgis/rest/services', 'https://mapservices.pasda.psu.edu/server/rest/services', 'https://www.pgcapps.pa.gov/arcgis/rest/services'],
    'NY': ['https://gisservices.dec.ny.gov/arcgis/rest/services', 'https://gisservices.its.ny.gov/arcgis/rest/services'], 'VA': ['https://gis.dcr.virginia.gov/arcgis/rest/services', 'https://services1.arcgis.com/PxUNqSbaWFvFgHnJ/arcgis/rest/services'],
    'WV': ['https://services.wvgis.wvu.edu/arcgis/rest/services'], 'MO': ['https://gis.mdc.mo.gov/arcgis/rest/services', 'https://gis.mostateparks.com/arcgis/rest/services'],
    'AR': ['https://gis.arkansas.gov/arcgis/rest/services'], 'GA': ['https://services1.arcgis.com/2iUE8l8JKrP2tygQ/arcgis/rest/services'], 'NC': ['https://services.nconemap.gov/secure/rest/services', 'https://gis.ncdcr.gov/arcgis/rest/services'],
    'SC': ['https://services1.arcgis.com/UoIBCj1QS2fAtQZL/arcgis/rest/services'], 'AL': ['https://services.arcgis.com/B5NlojRPoeyKQ9jr/arcgis/rest/services'], 'MS': ['https://gis.mdwfp.com/arcgis/rest/services'],
    'LA': ['https://gis.wlf.la.gov/arcgis/rest/services'], 'KS': ['https://services.kansasgis.org/arcgis/rest/services', 'https://services1.arcgis.com/A9m4gRZfZDVRvzNI/arcgis/rest/services'], 'IA': ['https://programs.iowadnr.gov/geospatial/rest/services'],
    'NE': ['https://maps.outdoornebraska.gov/arcgis/rest/services'], 'CO': ['https://services5.arcgis.com/ttNCsZgJvG4a0bYE/arcgis/rest/services'], 'UT': ['https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services'],
    'MT': ['https://gisservicemt.gov/arcgis/rest/services', 'https://services.arcgis.com/qnjIrwR8z5Izc0ij/arcgis/rest/services'], 'ID': ['https://gis.idfg.idaho.gov/server/rest/services', 'https://gis1.idl.idaho.gov/arcgis/rest/services'],
    'WA': ['https://gis.dnr.wa.gov/site3/rest/services', 'https://gis.dnr.wa.gov/site2/rest/services', 'https://services.arcgis.com/6lCKYNJLvwTXqrmp/arcgis/rest/services'], 'OR': ['https://maps.prd.state.or.us/arcgis/rest/services', 'https://navigator.state.or.us/arcgis/rest/services'],
    'CA': ['https://services2.arcgis.com/Uq9r85Potqm3MfRV/arcgis/rest/services', 'https://services.gis.ca.gov/arcgis/rest/services'], 'NV': ['https://gis.ndow.org/arcgis/rest/services'], 'AZ': ['https://services1.arcgis.com/mpVYz37anSdrK4d3/arcgis/rest/services'],
    'NM': ['https://mapservice.nmstatelands.org/arcgis/rest/services'], 'OK': ['https://services.arcgis.com/jWQlP64OuwDh6GGX/arcgis/rest/services'], 'ND': ['https://gis.dot.nd.gov/arcgis/rest/services'], 'SD': ['https://arcgis.sd.gov/arcgis/rest/services'],
    'WY': ['https://gis.wyo.gov/arcgis/rest/services', 'https://services1.arcgis.com/ZuA2Ygm6ywzLdPFl/arcgis/rest/services'], 'MD': ['https://geodata.md.gov/imap/rest/services'], 'NJ': ['https://mapsdep.nj.gov/arcgis/rest/services'],
    'MA': ['https://arcgisserver.digital.mass.gov/arcgisserver/rest/services'], 'CT': ['https://cteco.uconn.edu/ctmaps/rest/services'], 'ME': ['https://gis.maine.gov/arcgis/rest/services'],
    'VT': ['https://maps.vcgi.vermont.gov/arcgis/rest/services'], 'NH': ['https://nhgeodata.unh.edu/nhgeodata/rest/services'], 'DE': ['https://enterprise.firstmap.delaware.gov/arcgis/rest/services'], 'RI': ['https://risegis.ri.gov/hosting/rest/services'],
    'AK': ['https://arcgis.dnr.alaska.gov/arcgis/rest/services'], 'HI': ['https://geodata.hawaii.gov/arcgis/rest/services'],
}
KIND = [('wild', re.compile(r'wildlife|\bwma\b|game land|game area|hunting|fish(ing)? (area|lake)|conservation area|waterfowl|public hunting|\bwmas?\b', re.I)),
        ('park', re.compile(r'state park|parks?\b|historic site|recreation area', re.I)),
        ('forest', re.compile(r'state forest|forest(ry)?\b', re.I)),
        ('preserve', re.compile(r'nature preserve|natural area|preserve|scientific|natural heritage|nrca', re.I)),
        ('land', re.compile(r'trust land|state land|school land|public land|managed (land|area)|state owned|ownership|dnr land|dnr managed|conservation land|protected|open space', re.I))]
NAMEF = re.compile(r'^(park_?name|parkname|area_?name|areaname|unit_?name|unitname|site_?name|sitename|prop(erty)?_?name|propname|wma_?name|wmaname|name|full_?name|label|land_?name|tract_?name|official_?name|facility|title|gl_?name|managed_?area|ma_?name|sp_?name|desc(ription)?)$', re.I)
WEBF = re.compile(r'url|link|web|hyperlink|website|homepage|page', re.I)
OUT = 'data/state-gis-found.json'

def get(url, timeout=25):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', 'replace')

def jget(url, timeout=25):
    try:
        t = get(url, timeout)
        return json.loads(t)
    except Exception as e:
        return None

def kind_of(text):
    for k, rx in KIND:
        if rx.search(text or ''):
            return k
    return ''

def layer_info(url, st):
    """url = .../MapServer/3 or .../FeatureServer/0; returns a record or None"""
    j = jget(url + '?f=json')
    if not j or j.get('error') or j.get('geometryType') != 'esriGeometryPolygon':
        return None
    name = j.get('name') or ''
    fields = [f.get('name') for f in j.get('fields', []) if f.get('name')]
    namef = [f for f in fields if NAMEF.match(f)]
    webf = [f for f in fields if WEBF.search(f)]
    k = kind_of(name) or kind_of(j.get('description') or '')
    if not k and not namef:
        return None
    cnt = jget(url + '/query?where=1%3D1&returnCountOnly=true&f=json')
    n = cnt.get('count') if isinstance(cnt, dict) else None
    if not n or n < 3 or n > 60000:
        return None
    rec = {'st': st, 'kind': k, 'url': url, 'layer': name, 'count': n, 'nameFields': namef[:4], 'webFields': webf[:4], 'fields': fields[:40], 'maxRecords': j.get('maxRecordCount')}
    # a sample name, so the curator can see what is in it
    if namef:
        smp = jget(url + '/query?where=1%3D1&outFields=' + urllib.parse.quote(','.join(namef[:2] + webf[:1])) + '&returnGeometry=false&resultRecordCount=3&f=json')
        if isinstance(smp, dict):
            rec['sample'] = [f.get('attributes') for f in smp.get('features', [])][:3]
    return rec

def service_layers(surl, st, seen, out):
    j = jget(surl + '?f=json')
    if not j or j.get('error'):
        return
    for L in (j.get('layers') or []):
        if L.get('subLayerIds'):
            continue
        u = surl + '/' + str(L.get('id'))
        if u in seen:
            continue
        seen.add(u)
        txt = (L.get('name') or '') + ' ' + surl
        if not kind_of(txt) and not re.search(r'parks?|wildlife|wma|forest|preserve|natural|land|conserv|recreat|hunt', txt, re.I):
            continue
        r = layer_info(u, st)
        if r:
            r['service'] = surl
            out.append(r)

def crawl_root(root, st, seen, out, depth=0):
    j = jget(root + '?f=json')
    if not j or j.get('error'):
        return
    for s in (j.get('services') or []):
        name, typ = s.get('name') or '', s.get('type') or ''
        if typ not in ('MapServer', 'FeatureServer'):
            continue
        if not re.search(r'parks?|wildlife|wma|forest|preserve|natural|land|conserv|recreat|hunt|dnr|dcnr|boundar|managed|public|outdoor|state', name, re.I):
            continue
        base = root.split('/rest/services')[0] + '/rest/services/'
        surl = base + name + '/' + typ
        service_layers(surl, st, seen, out)
    if depth < 1:
        for f in (j.get('folders') or []):
            if re.search(r'parks?|wildlife|wma|forest|preserve|natural|land|conserv|recreat|hunt|dnr|dcnr|boundar|managed|public|outdoor|env|resource|open', f, re.I):
                crawl_root(root + '/' + f, st, seen, out, depth + 1)

def agol_search(st, seen, out):
    sn = STATES[st]
    qs = [f'"{sn}" "state parks" type:("Feature Service" OR "Map Service") access:public', f'"{sn}" ("wildlife management area" OR "wildlife management areas" OR "game lands" OR "wildlife areas") type:("Feature Service" OR "Map Service") access:public',
          f'"{sn}" ("state forests" OR "state forest" OR "nature preserves" OR "natural areas") type:("Feature Service" OR "Map Service") access:public']
    for q in qs:
        j = jget('https://www.arcgis.com/sharing/rest/search?f=json&num=25&q=' + urllib.parse.quote(q))
        for it in (j or {}).get('results', []) or []:
            u = it.get('url') or ''
            if not u or u in seen:
                continue
            seen.add(u)
            if not re.match(r'https?://', u):
                continue
            # one layer service (…/FeatureServer/0) or a whole service
            m = re.match(r'(.*/(?:Feature|Map)Server)(?:/(\d+))?$', u)
            if not m:
                continue
            before = len(out)
            if m.group(2):
                r = layer_info(u, st)
                if r:
                    r['service'] = m.group(1); out.append(r)
            else:
                service_layers(m.group(1), st, seen, out)
            for r in out[before:]:
                r.update({'agolTitle': it.get('title'), 'owner': it.get('owner'), 'orgId': it.get('orgId'), 'agolId': it.get('id'), 'modified': it.get('modified')})

def do_state(st):
    out, seen = [], set()
    try:
        agol_search(st, seen, out)
    except Exception as e:
        print('agol', st, e)
    for root in ROOTS.get(st, []):
        try:
            crawl_root(root, st, seen, out)
        except Exception as e:
            print('root', st, root, e)
    print(f'{st}: {len(out)} layers', flush=True)
    return out

def main():
    only = sys.argv[1:]
    sts = [s for s in STATES if not only or s in only]
    found = []
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for res in ex.map(do_state, sts):
            found.extend(res)
    found.sort(key=lambda r: (r['st'], r['kind'], -r['count']))
    json.dump({'when': time.strftime('%Y-%m-%d'), 'n': len(found), 'layers': found}, open(OUT, 'w'), indent=0)
    by = {}
    for r in found:
        by[r['st']] = by.get(r['st'], 0) + 1
    print('::notice title=State GIS layers found::' + ', '.join(f'{k} {v}' for k, v in sorted(by.items())) + f' (total {len(found)})')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('::notice title=State GIS scan problem::' + str(e)[:300])
