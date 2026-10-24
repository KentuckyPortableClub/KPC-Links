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
# the state agencies (same table as SA in kpc-maprep.js): name, website
AGENCIES = {
 'AL': [('Alabama State Parks', 'alapark.com'), ('Alabama Wildlife and Freshwater Fisheries', 'outdooralabama.com'), ('Alabama Department of Conservation and Natural Resources', 'outdooralabama.com')],
 'AK': [('Alaska State Parks', 'dnr.alaska.gov'), ('Alaska Department of Fish and Game', 'adfg.alaska.gov')],
 'AZ': [('Arizona State Parks', 'azstateparks.com'), ('Arizona Game and Fish Department', 'azgfd.com'), ('Arizona State Land Department', 'land.az.gov')],
 'AR': [('Arkansas State Parks', 'arkansasstateparks.com'), ('Arkansas Game and Fish Commission', 'agfc.com'), ('Arkansas Natural Heritage Commission', 'naturalheritage.com')],
 'CA': [('California State Parks', 'parks.ca.gov'), ('California Department of Fish and Wildlife', 'wildlife.ca.gov')],
 'CO': [('Colorado Parks and Wildlife', 'cpw.state.co.us')], 'CT': [('Connecticut DEEP', 'portal.ct.gov'), ('Connecticut Department of Energy and Environmental Protection', 'portal.ct.gov')],
 'DE': [('Delaware State Parks', 'destateparks.com'), ('Delaware DNREC', 'dnrec.delaware.gov')],
 'FL': [('Florida State Parks', 'floridastateparks.org'), ('Florida Fish and Wildlife Conservation Commission', 'myfwc.com'), ('Florida Forest Service', 'fdacs.gov'), ('Florida Department of Environmental Protection', 'floridadep.gov')],
 'GA': [('Georgia State Parks', 'gastateparks.org'), ('Georgia Department of Natural Resources', 'georgiawildlife.com')],
 'HI': [('Hawaii DLNR', 'dlnr.hawaii.gov')], 'ID': [('Idaho Parks and Recreation', 'parksandrecreation.idaho.gov'), ('Idaho Fish and Game', 'idfg.idaho.gov'), ('Idaho Department of Lands', 'idl.idaho.gov')],
 'IL': [('Illinois Department of Natural Resources', 'dnr.illinois.gov'), ('Illinois Nature Preserves Commission', 'dnr.illinois.gov')], 'IN': [('Indiana Department of Natural Resources', 'in.gov')],
 'IA': [('Iowa Department of Natural Resources', 'iowadnr.gov')], 'KS': [('Kansas Department of Wildlife and Parks', 'ksoutdoors.gov')],
 'KY': [('Kentucky State Parks', 'parks.ky.gov'), ('Kentucky Department of Fish and Wildlife Resources', 'fw.ky.gov')],
 'LA': [('Louisiana State Parks', 'lastateparks.com'), ('Louisiana Department of Wildlife and Fisheries', 'wlf.louisiana.gov')],
 'ME': [('Maine Bureau of Parks and Lands', 'maine.gov'), ('Maine Department of Inland Fisheries and Wildlife', 'maine.gov')],
 'MD': [('Maryland Department of Natural Resources', 'dnr.maryland.gov'), ('Maryland Park Service', 'dnr.maryland.gov')],
 'MA': [('Massachusetts Department of Conservation and Recreation', 'mass.gov'), ('MassWildlife', 'mass.gov')],
 'MI': [('Michigan Department of Natural Resources', 'michigan.gov')], 'MN': [('Minnesota Department of Natural Resources', 'dnr.state.mn.us')],
 'MS': [('Mississippi Department of Wildlife, Fisheries, and Parks', 'mdwfp.com')], 'MO': [('Missouri State Parks', 'mostateparks.com'), ('Missouri Department of Conservation', 'mdc.mo.gov')],
 'MT': [('Montana Fish, Wildlife and Parks', 'fwp.mt.gov')], 'NE': [('Nebraska Game and Parks Commission', 'outdoornebraska.gov')],
 'NV': [('Nevada State Parks', 'parks.nv.gov'), ('Nevada Department of Wildlife', 'ndow.org')], 'NH': [('New Hampshire State Parks', 'nhstateparks.org'), ('New Hampshire Fish and Game', 'wildlife.nh.gov')],
 'NJ': [('New Jersey Department of Environmental Protection', 'dep.nj.gov'), ('New Jersey Fish and Wildlife', 'dep.nj.gov')],
 'NM': [('New Mexico State Parks', 'emnrd.nm.gov'), ('New Mexico Department of Game and Fish', 'wildlife.dgf.nm.gov')],
 'NY': [('New York State Parks', 'parks.ny.gov'), ('New York State Department of Environmental Conservation', 'dec.ny.gov')],
 'NC': [('North Carolina State Parks', 'ncparks.gov'), ('North Carolina Wildlife Resources Commission', 'ncwildlife.gov')],
 'ND': [('North Dakota Parks and Recreation', 'parks.nd.gov'), ('North Dakota Game and Fish', 'gf.nd.gov')],
 'OH': [('Ohio Department of Natural Resources', 'ohiodnr.gov'), ('Ohio State Parks', 'ohiodnr.gov'), ('Ohio Division of Wildlife', 'ohiodnr.gov')],
 'OK': [('Oklahoma Tourism and Recreation Department', 'travelok.com'), ('Oklahoma Department of Wildlife Conservation', 'wildlifedepartment.com')],
 'OR': [('Oregon Parks and Recreation Department', 'stateparks.oregon.gov'), ('Oregon Department of Fish and Wildlife', 'myodfw.com')],
 'PA': [('Pennsylvania DCNR', 'dcnr.pa.gov'), ('Pennsylvania Game Commission', 'pgc.pa.gov'), ('Pennsylvania Department of Conservation and Natural Resources', 'dcnr.pa.gov')],
 'RI': [('Rhode Island Department of Environmental Management', 'dem.ri.gov')],
 'SC': [('South Carolina State Parks', 'southcarolinaparks.com'), ('South Carolina Department of Natural Resources', 'dnr.sc.gov'), ('South Carolina Department of Parks, Recreation and Tourism', 'scprt.com')],
 'SD': [('South Dakota Game, Fish and Parks', 'gfp.sd.gov')], 'TN': [('Tennessee State Parks', 'tnstateparks.com'), ('Tennessee Wildlife Resources Agency', 'tn.gov'), ('Tennessee Department of Environment and Conservation', 'tn.gov')],
 'TX': [('Texas Parks and Wildlife Department', 'tpwd.texas.gov')], 'UT': [('Utah State Parks', 'stateparks.utah.gov'), ('Utah Division of Wildlife Resources', 'wildlife.utah.gov')],
 'VT': [('Vermont Department of Forests, Parks and Recreation', 'fpr.vermont.gov'), ('Vermont Fish and Wildlife', 'vtfishandwildlife.com'), ('Vermont Agency of Natural Resources', 'anr.vermont.gov')],
 'VA': [('Virginia Department of Conservation and Recreation', 'dcr.virginia.gov'), ('Virginia Department of Wildlife Resources', 'dwr.virginia.gov')],
 'WA': [('Washington State Parks', 'parks.wa.gov'), ('Washington Department of Fish and Wildlife', 'wdfw.wa.gov'), ('Washington Department of Natural Resources', 'dnr.wa.gov')],
 'WV': [('West Virginia Division of Natural Resources', 'wvdnr.gov'), ('West Virginia State Parks', 'wvstateparks.com')],
 'WI': [('Wisconsin Department of Natural Resources', 'dnr.wisconsin.gov')], 'WY': [('Wyoming State Parks', 'wyoparks.wyo.gov'), ('Wyoming Game and Fish Department', 'wgfd.wyo.gov')],
}
# statewide GIS clearinghouses: many agencies publish through these instead of their own server (name for the org hunt, roots to crawl)
CLEARING = {
 'IL': [('Illinois Geospatial Data Clearinghouse', ['https://clearinghouse.isgs.illinois.edu/arcgis/rest/services', 'https://maps.isgs.illinois.edu/arcgis/rest/services']), ('Illinois Department of Natural Resources', ['https://gis.dnr.illinois.gov/server/rest/services', 'https://gis1.dnr.illinois.gov/arcgis/rest/services'])],
 'MO': [('Missouri Spatial Data Information Service', ['https://gis.msdis.missouri.edu/arcgis/rest/services', 'https://msdis.missouri.edu/arcgis/rest/services']), ('Missouri Department of Conservation', ['https://gis.mdc.mo.gov/server/rest/services', 'https://services1.arcgis.com/HlnbiNA7Hc9zHnbe/arcgis/rest/services']), ('Missouri State Parks', ['https://gis.mostateparks.com/server/rest/services'])],
 'NC': [('NC OneMap', ['https://services.nconemap.gov/secure/rest/services', 'https://services.nconemap.gov/arcgis/rest/services']), ('North Carolina Wildlife Resources Commission', ['https://gis.ncwildlife.org/arcgis/rest/services', 'https://services1.arcgis.com/BfvuK1CEtgNkDUnZ/arcgis/rest/services']), ('North Carolina Division of Parks and Recreation', ['https://gis.ncparks.gov/arcgis/rest/services'])],
 'AL': [('Alabama GIS', ['https://gis.alabama.gov/arcgis/rest/services', 'https://algis.alabama.gov/arcgis/rest/services']), ('Alabama Department of Conservation and Natural Resources', ['https://gis.outdooralabama.com/arcgis/rest/services', 'https://maps.outdooralabama.com/arcgis/rest/services'])],
 'MS': [('Mississippi Automated Resource Information System', ['https://gis.maris.state.ms.us/arcgis/rest/services', 'https://maris.mississippi.edu/arcgis/rest/services']), ('Mississippi Department of Wildlife, Fisheries, and Parks', ['https://gis.mdwfp.com/server/rest/services'])],
 'NE': [('NebraskaMAP', ['https://maps.nebraska.gov/arcgis/rest/services', 'https://gis.ne.gov/portal/rest/services']), ('Nebraska Game and Parks Commission', ['https://maps.outdoornebraska.gov/server/rest/services', 'https://gis.outdoornebraska.gov/arcgis/rest/services'])],
 'NH': [('NH GRANIT', ['https://nhgeodata.unh.edu/nhgeodata/rest/services', 'https://granit.unh.edu/arcgis/rest/services']), ('New Hampshire Fish and Game', ['https://gis.wildlife.nh.gov/arcgis/rest/services'])],
 'MA': [('MassGIS', ['https://arcgisserver.digital.mass.gov/arcgisserver/rest/services', 'https://gis-prod.digital.mass.gov/arcgis/rest/services', 'https://gisprpxy.itd.state.ma.us/arcgisserver/rest/services'])],
 'CT': [('CT ECO', ['https://cteco.uconn.edu/ctmaps/rest/services', 'https://cteco.uconn.edu/arcgis/rest/services']), ('Connecticut DEEP', ['https://gis.ct.gov/arcgis/rest/services', 'https://ctmaps.ct.gov/arcgis/rest/services'])],
 'MD': [('Maryland iMAP', ['https://mdgeodata.md.gov/imap/rest/services', 'https://geodata.md.gov/imap/rest/services']), ('Maryland Department of Natural Resources', ['https://gis.dnr.maryland.gov/arcgis/rest/services', 'https://geodata.md.gov/imap/rest/services/Biota'])],
 'SD': [('South Dakota GIS', ['https://arcgis.sd.gov/arcgis/rest/services', 'https://arcgis.sd.gov/server/rest/services']), ('South Dakota Game, Fish and Parks', ['https://gis.gfp.sd.gov/arcgis/rest/services', 'https://services.arcgis.com/jWPBXspaQsJStWX8/arcgis/rest/services'])],
 'AZ': [('AZGeo', ['https://azgeo.az.gov/arcgis/rest/services', 'https://services.azgeo.az.gov/arcgis/rest/services']), ('Arizona Game and Fish Department', ['https://gis.azgfd.gov/arcgis/rest/services', 'https://gis.azgfd.com/arcgis/rest/services']), ('Arizona State Parks and Trails', ['https://gis.azstateparks.com/arcgis/rest/services'])],
 'PA': [('Pennsylvania Game Commission', ['https://pgcgis.pa.gov/arcgis/rest/services', 'https://www.pgcapps.pa.gov/arcgis/rest/services'])],
 'MN': [('Minnesota Department of Natural Resources', ['https://enterprise.gisdata.mn.gov/aghost/rest/services/us_mn_state_dnr'])],
}
# ArcGIS Hub open-data sites per state (Brandon Oct 24, from his spreadsheet) + extra service roots he found
HUBS = {
 'MO': ['https://data-msdis.opendata.arcgis.com'], 'AL': ['https://data-algeohub.opendata.arcgis.com'], 'MS': ['https://opendata.gis.ms.gov'], 'SC': ['https://gis.sc.gov', 'https://public-lands-scdnr.hub.arcgis.com'],
 'AZ': ['https://azgeo-open-data-agic.hub.arcgis.com'], 'MN': ['https://gis.data.mn.gov'], 'MD': ['https://imap.maryland.gov', 'https://data.imap.maryland.gov'], 'SD': ['https://gis.sd.gov', 'https://opendata-sdgis.hub.arcgis.com'],
 'NH': ['https://www.nhgeodata.unh.edu', 'https://nhgeodata.unh.edu'], 'NC': ['https://www.nconemap.gov'], 'NE': ['https://www.nebraskamap.gov'], 'CT': ['https://geodata.ct.gov'], 'MA': ['https://gis.data.mass.gov'],
 'IL': ['https://clearinghouse.isgs.illinois.edu'], 'PA': ['https://www.pasda.psu.edu'], 'ME': ['https://maine.hub.arcgis.com'], 'OH': ['https://gis-ohiodnr.opendata.arcgis.com', 'https://ohiodnr.hub.arcgis.com'],
}
EXTRA_ROOTS = {'OH': ['https://gis2.ohiodnr.gov/arcgis/rest/services', 'https://gis2.ohiodnr.gov/arcgis/rest/services/OIT_Services']}
KIND = [('wild', re.compile(r'wildlife|\bwma\b|game land|game area|hunting|fish(ing)? (area|lake)|conservation area|waterfowl|public hunting|\bwmas?\b', re.I)),
        ('park', re.compile(r'state park|parks?\b|historic site|recreation area', re.I)),
        ('forest', re.compile(r'state forest|forest(ry)?\b', re.I)),
        ('preserve', re.compile(r'nature preserve|natural area|preserve|scientific|natural heritage|nrca', re.I)),
        ('land', re.compile(r'trust land|state land|school land|public land|managed (land|area)|state owned|ownership|dnr land|dnr managed|conservation land|protected|open space', re.I))]
NAMEF = re.compile(r'^(dnr_?name|lands_?name|prop_?name|sitename|site_?name|park_?name|parkname|area_?name|areaname|unit_?name|unitname|site_?name|sitename|prop(erty)?_?name|propname|wma_?name|wmaname|name|full_?name|label|land_?name|tract_?name|official_?name|facility|title|gl_?name|managed_?area|ma_?name|sp_?name|desc(ription)?)$', re.I)
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

def state_host(st, url):
    """True when the server is this state's own: <st>.gov / state.<st>.us / an agency, clearinghouse or hub site of this state."""
    try:
        h = urllib.parse.urlparse(url).hostname or ''
    except Exception:
        return False
    h = h.lower(); a = st.lower()
    if re.search(r'(^|\.)' + a + r'\.gov$|\.state\.' + a + r'\.us$|(^|\.)' + a + r'\.us$', h):
        return True
    sites = [site for _, site in AGENCIES.get(st, [])] + [urllib.parse.urlparse(r).hostname for _, rs in CLEARING.get(st, []) for r in rs] + [urllib.parse.urlparse(x).hostname for x in HUBS.get(st, [])] + [urllib.parse.urlparse(x).hostname for x in ROOTS.get(st, [])] + [urllib.parse.urlparse(x).hostname for x in EXTRA_ROOTS.get(st, [])]
    if re.search(r'(^|\.)arcgis\.com$', h):
        return False   # ArcGIS Online hosting belongs to no state: only the publishing org (state_match) can vouch for it
    for site in sites:
        if not site or re.search(r'arcgis\.com$', site):
            continue
        base = re.sub(r'^(www\.|data-|data\.|gis\.|maps\.|portal\.)', '', site.lower())
        if base and (h == base or h.endswith('.' + base)):
            return True
    return False

def state_match(st, text):
    """The state's name, or an agency of this state, named in the org / owner / title text."""
    t = (text or '').lower()
    if STATES[st].lower() in t:
        return True
    for name, _ in AGENCIES.get(st, []) + [(n, '') for n, _ in CLEARING.get(st, [])]:
        words = [w.lower() for w in re.findall(r'[A-Za-z]{5,}', name) if w.lower() not in ('department', 'division', 'state', 'parks', 'natural', 'resources', 'wildlife', 'conservation', 'recreation', 'commission', 'agency', 'fisheries', 'forestry', 'environmental', 'protection', 'energy', 'bureau', 'lands', 'office')]
        if words and all(w in t for w in words):
            return True
    return False

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

def org_hunt(st, seen, out):
    """ArcGIS Online: find the agency's own organization (by the agency's name in the org title), then every public
    polygon service that org publishes. The owner/org is what tells an official layer from a hobbyist copy."""
    orgs = {}
    for name, site in AGENCIES.get(st, []) + [(n, '') for n, _ in CLEARING.get(st, [])]:
        q = f'"{name}" type:("Feature Service" OR "Map Service") access:public'
        j = jget('https://www.arcgis.com/sharing/rest/search?f=json&num=50&q=' + urllib.parse.quote(q))
        for it in (j or {}).get('results', []) or []:
            oid = it.get('orgId')
            if oid and oid not in orgs:
                orgs[oid] = None
    words = {w.lower() for name, _ in AGENCIES.get(st, []) + [(n, '') for n, _ in CLEARING.get(st, [])] for w in re.findall(r'[A-Za-z]{4,}', name)} | {STATES[st].lower()}
    good = []
    for oid in list(orgs)[:25]:
        pj = jget(f'https://www.arcgis.com/sharing/rest/portals/{oid}?f=json')
        if not pj or pj.get('error'):
            continue
        oname = (pj.get('name') or '') + ' ' + (pj.get('urlKey') or '')
        ow = {w.lower() for w in re.findall(r'[A-Za-z]{4,}', oname)}
        hit = len(ow & words)
        if STATES[st].lower() in oname.lower() and re.search(r'natural resources|wildlife|parks|conservation|fish|game|forest|environment|dnr|dcnr|state of|gis|geographic|onemap|geospatial|map', oname, re.I) or hit >= 3:
            good.append((oid, pj.get('name'), pj.get('urlKey')))
    for oid, oname, key in good[:4]:
        for start in range(1, 400, 100):
            j = jget('https://www.arcgis.com/sharing/rest/search?f=json&num=100&start=%d&q=' % start + urllib.parse.quote(f'orgid:{oid} type:("Feature Service" OR "Map Service") access:public'))
            res = (j or {}).get('results', []) or []
            for it in res:
                u = it.get('url') or ''
                if not u or u in seen or not re.match(r'https?://', u):
                    continue
                if not re.search(r'park|wildlife|wma|game|hunt|forest|preserve|natural|land|conserv|recreat|manage|boundar|propert', (it.get('title') or '') + ' ' + u, re.I):
                    continue
                seen.add(u)
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
                    r.update({'agolTitle': it.get('title'), 'owner': it.get('owner'), 'orgId': oid, 'orgName': oname, 'agolId': it.get('id'), 'via': 'org'})
            if len(res) < 100:
                break

def host_hunt(st, seen, out):
    """Guess the agency's own ArcGIS server from its website (gis.<site>/arcgis/rest/services and friends) and read the
    agency's GIS / maps / data pages for links to REST services or ArcGIS Online items."""
    roots = []
    for name, site in AGENCIES.get(st, []):
        base = re.sub(r'^(www\.|portal\.|parks\.|fw\.|dnr\.|dec\.|dcr\.|dwr\.|dep\.)', '', site)
        for h in {site, base, 'gis.' + base, 'maps.' + base, 'gis.' + site, 'maps.' + site, 'geo.' + base, 'data.' + base, 'arcgis.' + base}:
            for path in ('/arcgis/rest/services', '/server/rest/services', '/gis/rest/services', '/hosting/rest/services', '/public/rest/services'):
                roots.append('https://' + h + path)
        for page in (f'https://{site}/', f'https://{site}/gis', f'https://{site}/maps', f'https://{site}/data', f'https://www.{base}/gis'):
            try:
                t = get(page, 15)
            except Exception:
                continue
            for u in set(re.findall(r'https?://[^\s"\'<>]+?/(?:arcgis|server|hosting|gis)/rest/services[^\s"\'<>]*', t)):
                roots.append(re.sub(r'(/rest/services).*', r'\1', u))
            for oid in set(re.findall(r'https?://([a-z0-9-]+)\.maps\.arcgis\.com', t)):
                pj = jget(f'https://{oid}.maps.arcgis.com/sharing/rest/portals/self?f=json')
                if pj and pj.get('id') and not pj.get('error'):
                    for start in range(1, 300, 100):
                        j = jget('https://www.arcgis.com/sharing/rest/search?f=json&num=100&start=%d&q=' % start + urllib.parse.quote(f'orgid:{pj["id"]} type:("Feature Service" OR "Map Service") access:public'))
                        res = (j or {}).get('results', []) or []
                        for it in res:
                            u = it.get('url') or ''
                            if not u or u in seen or not re.match(r'https?://', u) or not re.search(r'park|wildlife|wma|game|hunt|forest|preserve|natural|land|conserv|recreat|manage|boundar|propert', (it.get('title') or '') + ' ' + u, re.I):
                                continue
                            seen.add(u)
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
                                r.update({'agolTitle': it.get('title'), 'owner': it.get('owner'), 'orgId': pj['id'], 'orgName': pj.get('name'), 'via': 'site→org'})
                        if len(res) < 100:
                            break
    for _, rs in CLEARING.get(st, []):
        roots.extend(rs)
    done = set()
    for root in roots:
        if root in done:
            continue
        done.add(root)
        try:
            n0 = len(out)
            crawl_root(root, st, seen, out)
            for r in out[n0:]:
                r.setdefault('via', 'host')
        except Exception as e:
            pass

def hub_hunt(st, seen, out):
    """ArcGIS Hub sites: /api/v3/datasets?q=… lists datasets with their service url + owner/org; /api/search/v1 on newer sites."""
    for hub in HUBS.get(st, []):
        hub = hub.rstrip('/')
        items = []
        for q in ('state park', 'wildlife management area', 'state forest', 'nature preserve', 'conservation lands', 'public hunting', 'protected lands', 'managed lands'):
            j = jget(f'{hub}/api/v3/datasets?q={urllib.parse.quote(q)}&page[size]=50&fields[datasets]=name,url,owner,orgName,type,recordCount')
            for it in (j or {}).get('data', []) or []:
                a = it.get('attributes') or {}
                if a.get('url'):
                    items.append((a.get('name'), a['url'], a.get('owner'), a.get('orgName')))
            j2 = jget(f'{hub}/api/search/v1?q={urllib.parse.quote(q)}&num=50')
            for it in (j2 or {}).get('results', []) or []:
                u = it.get('url') or (it.get('item') or {}).get('url')
                if u:
                    items.append((it.get('title') or it.get('name'), u, it.get('owner'), it.get('orgName') or it.get('source')))
        for name, u, owner, org in items:
            if not re.match(r'https?://', u or '') or u in seen:
                continue
            if not (state_host(st, u) or state_match(st, (org or '') + ' ' + (owner or '') + ' ' + (name or ''))):
                continue
            if not re.search(r'park|wildlife|wma|game|hunt|forest|preserve|natural|land|conserv|recreat|manage|boundar|propert', (name or '') + ' ' + u, re.I):
                continue
            seen.add(u)
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
                r.update({'agolTitle': name, 'owner': owner, 'orgName': org, 'via': 'hub', 'hub': hub})

def do_state(st):
    out, seen = [], set()
    try:
        agol_search(st, seen, out)
    except Exception as e:
        print('agol', st, e)
    try:
        org_hunt(st, seen, out)
    except Exception as e:
        print('org', st, e)
    try:
        host_hunt(st, seen, out)
    except Exception as e:
        print('host', st, e)
    try:
        hub_hunt(st, seen, out)
    except Exception as e:
        print('hub', st, e)
    for root in EXTRA_ROOTS.get(st, []):
        try:
            n0 = len(out); crawl_root(root, st, seen, out)
            for r in out[n0:]:
                r.setdefault('via', 'host')
        except Exception as e:
            print('extra', st, root, e)
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
    # proposals: layers that look official (state server, or the agency's own ArcGIS Online org) for states the tool does not have yet
    try:
        have = json.load(open('data/state-gis.json')).get('states', {})
    except Exception:
        have = {}
    prop = []
    for r in found:
        if r['st'] in have or not r['nameFields'] or not r['kind'] or r['count'] < 5:
            continue
        u = r['url'].lower()
        official = state_host(r['st'], r['url']) or (r.get('via') in ('org', 'site→org', 'hub') and state_match(r['st'], str(r.get('orgName') or '') + ' ' + str(r.get('owner') or ''))) or bool(re.search(r'dnr|dcnr|parks|wildlife|fwc|tpwd|twra|odnr|mdc|agfc|dec_|dep|forest|_gis$|gis_', str(r.get('owner') or ''), re.I))
        if not official or re.search(r'buffer|intersect|proposed|easement|habitat|wetland|karst|county|city|parcel|zoning|soil|flood', r['layer'] + ' ' + str(r.get('agolTitle') or ''), re.I):
            continue
        prop.append(r)
    json.dump({'when': time.strftime('%Y-%m-%d'), 'n': len(prop), 'layers': prop}, open('data/state-gis-proposed.json', 'w'), indent=0)
    # AUTO-ADD (Brandon Oct 24: 'keep looking and add as found'): only the strong ones — a state .gov/.us server or the agency's own ArcGIS Online
    # organization, a clear park/wildlife/forest/preserve layer name, a name field, 5-5000 records, and no such kind for that state yet.
    # Marked auto:true so the Tool Box labels them 'found by the bot, not yet checked'. Everything else stays in the proposal file for a person.
    try:
        gis = json.load(open('data/state-gis.json'))
    except Exception:
        gis = {'states': {}, 'portals': {}}
    states = gis.setdefault('states', {})
    STRONG = re.compile(r'state park|parks? (boundar|unit|propert)|wildlife (management )?area|\bwma|game land|state forest|nature preserve|natural area|public (hunting|land)|managed land|conservation area|dnr (land|managed)', re.I)
    added = []
    for r in prop:
        title = r['layer'] + ' ' + str(r.get('agolTitle') or '')
        if not STRONG.search(title) or not (5 <= r['count'] <= 5000):
            continue
        u = r['url'].lower()
        oname = str(r.get('orgName') or '')
        agency_words = {w.lower() for name, _ in AGENCIES.get(r['st'], []) for w in re.findall(r'[A-Za-z]{5,}', name)}
        org_ok = r.get('via') in ('org', 'site→org', 'hub') and state_match(r['st'], oname + ' ' + str(r.get('owner') or '')) and (STATES[r['st']].lower() in oname.lower() or len({w.lower() for w in re.findall(r'[A-Za-z]{5,}', oname)} & agency_words) >= 2)
        gov_ok = state_host(r['st'], r['url'])
        if not (org_ok or gov_ok):
            continue
        have = states.get(r['st'], [])
        if any(h.get('url') == r['url'] for h in have) or any(h.get('kind') == r['kind'] for h in have):
            continue
        if not oname and not gov_ok:
            continue
        e = {'kind': r['kind'], 'ag': (oname or 'State of ' + STATES[r['st']] + ' (' + (urllib.parse.urlparse(r['url']).hostname or '') + ')'), 'nm': r['nameFields'][0], 'url': r['url'], 'host': 'agency' if gov_ok else 'agol', 'auto': time.strftime('%Y-%m-%d'), 'layer': r['layer'], 'count': r['count']}
        if r.get('webFields'):
            e['web'] = r['webFields'][0]
        states.setdefault(r['st'], []).append(e)
        added.append(f"{r['st']} {r['kind']} {r['layer'][:40]}")
    if added:
        gis['when'] = time.strftime('%Y-%m-%d')
        json.dump(gis, open('data/state-gis.json', 'w'), indent=1)
        print('::notice title=State GIS layers auto-added::' + '; '.join(added)[:900])
    if only:
        try:
            old = json.load(open(OUT)).get('layers', [])
            found = [r for r in old if r['st'] not in sts] + found
        except Exception:
            pass
    json.dump({'when': time.strftime('%Y-%m-%d'), 'n': len(found), 'layers': found}, open(OUT, 'w'), indent=0)
    by = {}
    for r in found:
        by[r['st']] = by.get(r['st'], 0) + 1
    print('::notice title=State GIS layers found::' + ', '.join(f'{k} {v}' for k, v in sorted(by.items())) + f' (total {len(found)}; {len(prop)} proposed for states not covered yet)')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('::notice title=State GIS scan problem::' + str(e)[:300])
