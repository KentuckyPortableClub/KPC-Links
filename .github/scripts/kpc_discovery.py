#!/usr/bin/env python3
"""DISCOVERY BOT (chat 2, Oct 27 2026; design: .claude/build/research/KPC_DiscoveryBot_Design_Fable.md; replaces the portal scout).
Asks the CATALOGS where agencies list what they publish, by keyword per gap, tests each NEW lead with the shared lead tests
(kpc_leadtest.py), grades it 0-6 automatically and writes ONE ranked file. It never adds anything to the live data, never emails,
never fails. People (chat 8, Brandon) read the top of data/discovery/leads.md.
RULE SHEET (design §1): a lead = published by the managing agency / the state or province GIS office / a national register, not
read yet, filling one of the gaps (outline, ownership, map page, closures, access, roads/water, trail line, replaces). Not a lead:
non-agency hosts, city/council parks, historic markers, closed licences (WDPA, 'no derivatives'), theme layers that only NAME a park,
over 10 years old. Grey areas (Brandon YES Oct 27 11:51 AM): D-1 county layers = 'second witness' only; D-2 a .gov layer with no
licence = 'licence unknown'; D-3 the Maps tab = allow-listed agency hosts, 1 page per 3 s, 300 pages a run; D-4 no world catalogs.
Steps (STEPS=A,B,C,D; STATES=OH; MIN_A/MIN_B/MIN_C minutes each):
  A catalog search: ArcGIS Online (by the state's agency org ids, then state name + keyword with the publisher test), Socrata
    Discovery (the state's open-data domains), CKAN (data.gov / open.canada.ca and provincial catalogs).
  B test each new lead with a service: answers, layers, geometry, name field, parks with no outline it names (attributes only).
  C the 'Maps' tab: agency park pages (allow list in maps-tab.json) -> map / PDF links for parks with no official map link.
  D write data/discovery/leads.json + leads.md (top 50) + one observation per NEW A lead."""
import json, os, pathlib, re, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import kpc_leadtest as T
from kpc_save import save_json

D = pathlib.Path('data/discovery')
T0 = time.time()
STEPS = set((os.environ.get('STEPS') or 'A,B,D').upper().replace(' ', '').split(','))
STATES = [s.upper() for s in (os.environ.get('STATES') or 'OH').replace(',', ' ').split()]
BUDGET = {'A': float(os.environ.get('MIN_A') or 40), 'B': float(os.environ.get('MIN_B') or 60), 'C': float(os.environ.get('MIN_C') or 45)}
MAPDBG = []
STAT = {'hits': 0, 'new': 0, 'already_read': 0, 'not_agency': 0, 'not_a_lead': 0, 'tested': 0, 'sleeping': 0, 'pages': 0, 'errors': 0}
# Oct 27 (chat 8's Ohio grade, HQ 8:37 PM): a layer is graded by WHAT IT IS (name + geometry + fields), never by the keyword that found it
THEME = re.compile(r'bluff|shoreline|watershed|historic shoreline|\bcounty\b|counties|district|ortho|runoff|parcel|permit|planning|legislative|'
                   r'zoning|census|soil|geolog|flood|aquifer|well\b|wells\b|mine\b|mining|oil|gas\b|elevation|contour|imagery|basemap|boundary markers|'
                   r'mile markers|air quality|monitoring|trout|bass|fish distribution|elk|deer|harvest|hunting units?|survey|address|roads? centerline|'
                   r'commerce|economic|school|voting|precinct|sewer|utility|hydrant|crime|coastal barrier', re.I)
ACCESS_W = re.compile(r'trail ?heads?|parking|\bramps?\b|launch|put-?in|access (?:site|point|area)s?|boat|kiosk|campground|camp ?sites?|'
                      r'day use|picnic|entrance|gate|waypoint|poi\b|point[s]? of interest|facilit', re.I)
TRAIL_W = re.compile(r'\btrails?\b|\btrace\b|towpath|path(?:way)?s?\b|greenway|paddling|water trail', re.I)
PARK_W = re.compile(r'park|preserve|forest|wildlife|wma\b|game land|natural area|recreation|conservation|refuge|wilderness|wild river|scenic river|lands?\b', re.I)
WATER_W = re.compile(r'\blakes?\b|rivers?\b|streams?\b|hydro|water ?bod|shore|wetland', re.I)
ROAD_W = re.compile(r'\broads?\b|street', re.I)
CLOSE_W = re.compile(r'closure|closed|alert|advisor|restriction|status', re.I)
OWN_W = re.compile(r'ownership|owner|surface management|fee title|tenure|crown land|public land', re.I)


BLOCK = re.compile(r'seismic|earthquake|commercial fishing|bathymetr|depth|horsepower|\bhp\b|\bdams?\b|spillway|bluff|watershed|permit|'
                   r'netting|quota|hatcher|stocking|pheasant|release|meteorite|astro', re.I)
PARKWORD = re.compile(r'park|trail|campground|camp|refuge|forest|preserve|wildlife area|state land|public land|recreation|access|boat ramp|launch', re.I)


def classify(name, geom, fields, service='', state=''):
    """-> (gap or None, why). geom = Point / Polyline / Polygon / ''. A theme layer = None."""
    n = re.sub(r'[_\-]+', ' ', name or '')   # Parks_DNAP_Trails -> Parks DNAP Trails (word tests)
    sv = re.sub(r'[_\-/]+', ' ', service or '')   # Oct 27 (chat 8): the SERVICE name counts too ('Watercraft Paddling Query' / 'Stream Access')
    both = (n + ' ' + sv).strip()
    if BLOCK.search(both): return None, 'block list (' + BLOCK.search(both).group(0) + ')'
    if THEME.search(n) and not (ACCESS_W.search(n) or TRAIL_W.search(n)): return None, 'theme layer (' + THEME.search(n).group(0) + ')'
    g = (geom or '').lower()
    canada = str(state).startswith('CA-')
    if ACCESS_W.search(both) and 'point' in g: return 'access', 'points named ' + ACCESS_W.search(both).group(0)
    if re.search(r'\baccess\b', both, re.I) and 'point' in g: return 'access', 'access points'
    if TRAIL_W.search(both) and 'line' in g: return 'trail line', 'lines named ' + TRAIL_W.search(both).group(0)
    if TRAIL_W.search(both) and 'point' in g: return 'access', 'trail points (' + TRAIL_W.search(both).group(0) + ')'
    if OWN_W.search(both) and 'polygon' in g: return 'ownership', 'ownership polygons'
    # Oct 27 (chat 8 fix 3): a 'closed / status' layer counts only with a park word, and never off the block list
    if CLOSE_W.search(both):
        if PARKWORD.search(both): return 'closures', 'closure / status layer for parks'
        return None, 'a "closed" layer with nothing about parks in its name'
    # Oct 27 (chat 8 fix 4, HQ): water + roads are a CANADA gap only (the US takes water from USGS NHD, rule 9)
    if canada and WATER_W.search(n) and ('polygon' in g or 'line' in g) and not PARK_W.search(n): return 'roads/water', 'water ' + ('areas' if 'polygon' in g else 'lines')
    if canada and ROAD_W.search(n) and 'line' in g: return 'roads/water', 'road lines'
    if (WATER_W.search(n) or ROAD_W.search(n)) and not canada and not (ACCESS_W.search(both) or TRAIL_W.search(both)):
        return None, 'water / roads: the US takes those from USGS NHD (rule 9), so not a gap here'
    if PARK_W.search(n) and 'polygon' in g and any(re.search(r'name|nm$|label|title', f, re.I) for f in fields or []): return 'outline', 'park polygons with a name field'
    if ACCESS_W.search(both) or TRAIL_W.search(both): return 'access', 'named like access (' + (ACCESS_W.search(both) or TRAIL_W.search(both)).group(0) + ')'
    return None, 'nothing a gap needs (no access / trail / park / closure / ownership in its name)'


NOT_LEAD = re.compile(r'\bcity\b|council|municipal|historic marker|hunting unit|fire district|census place|zoning|parcel sales|'
                      r'school|voting|precinct|sewer|utility|hydrant|crime|permit applications?|\btest\b|\bcopy\b|sample', re.I)
CLOSED = re.compile(r'no derivatives|internal use|not for redistribution|wdpa|all rights reserved', re.I)
OPEN = re.compile(r'cc[- ]?by|creative commons|public domain|no restrictions|open government licen|odbl|cc0|freely available|unrestricted', re.I)
CA_CKAN = {'CA-ON': 'https://data.ontario.ca', 'CA-BC': 'https://catalogue.data.gov.bc.ca', 'CA-AB': 'https://open.alberta.ca',
           'CA-QC': 'https://www.donneesquebec.ca/recherche'}


def notice(m): print('::notice title=Discovery bot::' + str(m).replace('\n', ' ')[:900], flush=True)
def late(step, t0): return time.time() - t0 > BUDGET[step] * 60
def load(p, d):
    try: return json.load(open(p))
    except Exception: return d  # noqa: BLE001


def key_of(u):
    """Oct 27 (chat 8 fix 2): ONE row per service: gis2.x = gis.x (same agency), no /MapServer|/FeatureServer|/<layer number>."""
    u = (u or '').split('?')[0].rstrip('/').lower()
    u = re.sub(r'/(feature|map)server(/\d+)?$', '', u)
    u = re.sub(r'^(https?://)gis\d+\.', r'\1gis.', u)
    return u


def svc_of(u):
    m = re.match(r'(https?://[^?#]+?/(?:Feature|Map)Server)', u or '', re.I)
    return m.group(1).rstrip('/') if m else (u or '').split('?')[0].rstrip('/')


def already_read():
    """Every service URL the data bots already read (rule 1b), found by scanning their files."""
    seen = set()
    files = ['data/state-gis.json', 'data/us-key/layers.json', 'data/ca-key/layers.json', 'data/access-layers.json',
             'data/campstate-layers.json', 'kpc-ky-data.json'] + [str(p) for p in pathlib.Path('data/trails').glob('index*.json')]
    for f in files:
        try: txt = open(f).read()
        except Exception: continue  # noqa: BLE001
        for u in re.findall(r'https?://[^"\s\\]+', txt): seen.add(key_of(u))
    return seen


def org_ids(st):
    """The state's agency ArcGIS Online org ids, from the hosts we already read (services*.arcgis.com/<org id>/)."""
    g = load('data/state-gis.json', {}).get('states', {}).get(st, [])
    return sorted({m.group(1) for x in g for m in [re.match(r'https?://services\d*\.arcgis\.com/([A-Za-z0-9]+)/', x.get('url', ''))] if m})


ORG = {}
def org_name(oid):
    if oid not in ORG:
        try: ORG[oid] = (T.get(f'https://www.arcgis.com/sharing/rest/portals/{oid}', {'f': 'json'}).get('name') or '')
        except Exception: ORG[oid] = ''  # noqa: BLE001
    return ORG[oid]


def step_a(st, kws, known, leads, kwlog):
    t0 = time.time()
    for root in agency_servers(st): walk_server(st, root, known, leads, t0, kwlog)
    sn = T.STATE_NAMES.get(st, st)
    orgs = org_ids(st)
    for gap, words in kws.items():
        for kw in words:
            if late('A', t0): return
            qs = [f'"{kw}" AND orgid:{o}' for o in orgs[:6]] + [f'"{kw}" AND "{sn}"']
            kl = {'keyword': kw, 'gap': gap, 'hits': 0, 'new': 0, 'already_read': 0, 'not_agency': 0, 'not_this_state': 0, 'theme': 0}; kwlog.append(kl)
            for q in qs:
                try: j = T.get('https://www.arcgis.com/sharing/rest/search', {'f': 'json', 'num': 100, 'q': q + ' AND (type:"Feature Service" OR type:"Map Service")'})
                except Exception: STAT['errors'] += 1; continue  # noqa: BLE001,E702
                for it in j.get('results') or []:
                    STAT['hits'] += 1; kl['hits'] += 1
                    u = svc_of(it.get('url') or '')
                    if not u: continue
                    title = (it.get('title') or '')[:90]
                    if key_of(u) in known: STAT['already_read'] += 1; kl['already_read'] += 1; continue
                    if NOT_LEAD.search(title) or CLOSED.search(it.get('licenseInfo') or ''): STAT['not_a_lead'] += 1; continue
                    if THEME.search(title) and not (ACCESS_W.search(title) or TRAIL_W.search(title)): STAT['not_a_lead'] += 1; kl['theme'] += 1; continue
                    org = org_name(it.get('orgId') or '')
                    county = bool(re.search(r'\bcounty\b', org, re.I))
                    if not T.agency_org(org, st) and not county: STAT['not_agency'] += 1; kl['not_agency'] += 1; continue
                    # Oct 27 (Ohio test: Great Smoky Mountains layers topped the list): a publisher that is NOT the state's own agency
                    # (federal, county) counts only when the item's own title / snippet / tags name the state
                    if not T.official_org(org, st) and not re.search(r'\b' + re.escape(sn) + r'\b', ' '.join([title, it.get('snippet') or '', ' '.join(it.get('tags') or [])]), re.I):
                        STAT['not_this_state'] = STAT.get('not_this_state', 0) + 1; kl['not_this_state'] += 1; continue
                    lic = re.sub(r'<[^>]+>', ' ', it.get('licenseInfo') or '')[:200]
                    mod = time.strftime('%Y-%m-%d', time.gmtime((it.get('modified') or 0) / 1000)) if it.get('modified') else ''
                    if mod and mod < time.strftime('%Y-%m-%d', time.gmtime(time.time() - 10 * 365 * 86400)): STAT['not_a_lead'] += 1; continue
                    if key_of(u) not in leads: kl['new'] += 1
                    x = leads.setdefault(key_of(u), {'url': u, 'st': st, 'title': title, 'publisher': org[:70], 'catalog': 'ArcGIS Online',
                                                    'gaps': [], 'keywords': [], 'licence': lic.strip(), 'modified': mod, 'found': time.strftime('%Y-%m-%d'),
                                                    'kind': 'second witness' if county else 'new'})
                    if gap not in x['gaps']: x['gaps'].append(gap)
                    if kw not in x['keywords']: x['keywords'].append(kw)
            # Socrata (state open-data domains we know of in state-gis portals)
            for dom in socrata_domains(st):
                try: j = T.get('https://api.us.socrata.com/api/catalog/v1', {'domains': dom, 'q': kw, 'only': 'datasets,maps', 'limit': 50})
                except Exception: STAT['errors'] += 1; continue  # noqa: BLE001,E702
                for r in j.get('results') or []:
                    STAT['hits'] += 1
                    res = r.get('resource') or {}
                    u = (r.get('link') or '').rstrip('/')
                    if not u or key_of(u) in known or NOT_LEAD.search(res.get('name') or ''): continue
                    x = leads.setdefault(key_of(u), {'url': u, 'st': st, 'title': (res.get('name') or '')[:90], 'publisher': dom, 'catalog': 'Socrata',
                                                    'gaps': [], 'keywords': [], 'licence': ((r.get('metadata') or {}).get('license') or '')[:120],
                                                    'modified': (res.get('updatedAt') or '')[:10], 'found': time.strftime('%Y-%m-%d'), 'kind': 'table (no map service)'})
                    if gap not in x['gaps']: x['gaps'].append(gap)
                    if kw not in x['keywords']: x['keywords'].append(kw)
            # CKAN (Canada: the federal catalog + provincial ones)
            for base in ckan_bases(st):
                try: j = T.get(base + '/api/3/action/package_search', {'q': kw, 'rows': 50})
                except Exception: STAT['errors'] += 1; continue  # noqa: BLE001,E702
                for p in (j.get('result') or {}).get('results') or []:
                    STAT['hits'] += 1
                    svcs = [svc_of(r.get('url') or '') for r in p.get('resources') or [] if re.search(r'/(Feature|Map)Server', r.get('url') or '', re.I)]
                    u = svcs[0] if svcs else f"{base}/dataset/{p.get('name')}"
                    if key_of(u) in known or NOT_LEAD.search(p.get('title') or ''): continue
                    x = leads.setdefault(key_of(u), {'url': u, 'st': st, 'title': (p.get('title') or '')[:90], 'publisher': ((p.get('organization') or {}).get('title') or '')[:70],
                                                    'catalog': 'CKAN ' + base.split('//')[1].split('/')[0], 'gaps': [], 'keywords': [], 'licence': (p.get('license_title') or '')[:120],
                                                    'modified': (p.get('metadata_modified') or '')[:10], 'found': time.strftime('%Y-%m-%d'),
                                                    'kind': 'new' if svcs else 'download, needs a loader'})
                    if gap not in x['gaps']: x['gaps'].append(gap)
                    if kw not in x['keywords']: x['keywords'].append(kw)


EMPTY = {}
def empty_gaps(st):
    """Oct 27 (chat 8 + HQ): band A = the lead fills a gap that is EMPTY in that state. Ohio: no trail lines at all -> trail line
    is empty (Parks_DNAP_Trails = A); 4 ODNR access layers already read -> more access points = B."""
    if st in EMPTY: return EMPTY[st]
    e, code = set(), st.split('-')[-1]
    try:
        ix = load('data/trails/index-state.json', []) or []
        if not [t for t in ix if str(t.get('st', '')).upper() == code]: e.add('trail line')
    except Exception: e.add('trail line')  # noqa: BLE001
    a = load(f'data/access/{st if st.startswith("CA-") else "US-" + code}.json', {}) or {}
    if len(a.get('parks') or {}) < 20: e.add('access')
    c = load('data/alerts/us-parks.json', {}) or {}
    if not [k for k, v in (c.get('sources') or {}).items() if str(v.get('st', '')).upper() == code]: e.add('closures')
    b = load('data/boundary-score.json', {}) or {}
    if ((b.get('states') or {}).get('US-' + code) or {}).get('no_outline', 0) > 0: e.add('outline')
    if st.startswith('CA-'): e |= {'roads/water', 'ownership'}   # Canada: no national water / road layer and no ownership map yet
    e.add('map page')
    EMPTY[st] = e
    return e


def agency_servers(st):
    """The state's own ArcGIS Server roots we already read something from (data/state-gis.json), e.g. gis.ohiodnr.gov/arcgis/rest/services."""
    g = load('data/state-gis.json', {}).get('states', {}).get(st, [])
    roots = set()
    for x in g:
        m = re.match(r'(https?://[^/]+/[^/]*/rest/services)', x.get('url', ''))
        if m and not re.search(r'arcgis\.com', m.group(1)): roots.add(m.group(1))
    return sorted(roots)


def whys_none(rows):
    r = [x.get('is') for x in rows if x.get('is')]
    return 'no layer a gap needs: ' + '; '.join(dict.fromkeys(r))[:120] if r else 'no layer a gap needs'


def walk_server(st, root, known, leads, t0, kwlog):
    """Every folder → every service → its layers; each layer classified by what it is (Oct 27, chat 8's fix 1)."""
    try: top = T.get(root, {'f': 'json'})
    except Exception as e: STAT['errors'] += 1; kwlog.append({'server': root, 'error': str(e)[:80]}); return  # noqa: BLE001
    folders = [''] + [f for f in top.get('folders') or []]
    for f in list(folders):   # Oct 27 (chat 8): one level deeper, so a service in a sub-folder is seen too
        if not f or late('A', t0): continue
        try: sub = T.get(f'{root}/{f}', {'f': 'json'})
        except Exception: continue  # noqa: BLE001
        folders += [g if g.startswith(f + '/') else f + '/' + g for g in sub.get('folders') or []]
    n_svc = n_lead = 0
    for f in folders:
        if late('A', t0): break
        try: j = top if f == '' else T.get(f'{root}/{f}', {'f': 'json'})
        except Exception: STAT['errors'] += 1; continue  # noqa: BLE001
        for sv in j.get('services') or []:
            if sv.get('type') not in ('MapServer', 'FeatureServer'): continue
            nm = sv.get('name') or ''
            u = f"{root}/{nm}/{sv['type']}"
            n_svc += 1
            if key_of(u) in known or svc_of(u).lower() in known: STAT['already_read'] += 1; continue
            if NOT_LEAD.search(nm.split('/')[-1]): STAT['not_a_lead'] += 1; continue
            try: d = T.get(u, {'f': 'json'})
            except Exception: STAT['errors'] += 1; continue  # noqa: BLE001
            lays = (d.get('layers') or [])[:60]
            gaps, whys, lay_rows = [], [], []
            for L in lays:
                lu = f"{u}/{L.get('id')}"
                try: ld = T.get(lu, {'f': 'json'})
                except Exception: continue  # noqa: BLE001
                gap, why = classify(L.get('name') or ld.get('name') or '', (ld.get('geometryType') or '').replace('esriGeometry', ''), [x['name'] for x in ld.get('fields') or []], nm, st)
                lay_rows.append({'id': L.get('id'), 'name': (L.get('name') or '')[:60], 'geom': (ld.get('geometryType') or '').replace('esriGeometry', ''), 'is': why, 'gap': gap})
                if gap and gap not in gaps: gaps.append(gap); whys.append(f"{L.get('name')}: {why}")
                if len(lay_rows) >= 25: break
            if not gaps:
                STAT['not_a_lead'] += 1
                if len(kwlog) < 400: kwlog.append({'server': root, 'service': nm, 'skipped': whys_none(lay_rows), 'layers': [r['name'] for r in lay_rows][:6]})
                continue
            STAT['hits'] += 1; n_lead += 1
            x = leads.setdefault(key_of(u), {'url': u, 'st': st, 'title': nm.split('/')[-1][:90], 'folder': nm.split('/')[0] if '/' in nm else '',
                                             'publisher': root.split('/')[2], 'catalog': 'agency server walk', 'gaps': [], 'keywords': [], 'licence': (d.get('copyrightText') or '')[:120],
                                             'modified': '', 'found': time.strftime('%Y-%m-%d'), 'kind': 'new', 'is': whys[:4], 'layers_seen': lay_rows[:12]})
            for gp in gaps:
                if gp not in x['gaps']: x['gaps'].append(gp)
            x['is'] = whys[:4]
    kwlog.append({'server': root, 'folders': len(folders), 'services': n_svc, 'leads': n_lead})


def socrata_domains(st):
    P = load(D / 'portals.json', {}).get(st, {})
    return P.get('socrata', [])


def ckan_bases(st):
    P = load(D / 'portals.json', {}).get(st, {})
    b = list(P.get('ckan', []))
    if st.startswith('CA-'): b = ['https://open.canada.ca/data'] + ([CA_CKAN[st]] if st in CA_CKAN else []) + b
    return b


def grade(x):
    """0-6: answers / geometry + name field / agency publisher / open licence / fills a gap by what it IS / parks named (outline) or
    new-to-us with records (access, trail, water, closures, ownership). A theme layer (classify → None) is dropped to C."""
    g = 0
    t = x.get('test') or {}
    if t.get('answers') and t.get('n_layers'): g += 1
    if any(l.get('nameField') and l.get('geom') for l in t.get('layers', [])): g += 1
    # what the layers ARE (from the test's layer rows or the walk's), not the search word
    kinds, whys = [], []
    for l in (t.get('layers') or x.get('layers_seen') or []):
        gap, why = classify(l.get('name') or '', l.get('geom') or '', l.get('fields') or [], x.get('title', ''), x['st'])
        if gap: kinds.append(gap); whys.append(f"{l.get('name')}: {why}")
    if kinds:
        x['gaps'] = sorted(set(kinds)); x['is'] = whys[:4]; g += 1
    elif t.get('layers') or x.get('layers_seen'):
        x['is'] = [l.get('name', '') + ': ' + classify(l.get('name') or '', l.get('geom') or '', [], x.get('title', ''), x['st'])[1] for l in (t.get('layers') or x.get('layers_seen'))[:3]]
        x['grade'] = 0; x['band'] = 'C'; x['parks_named'] = 0; return 0
    if T.agency_org(x.get('publisher', ''), x['st']) or re.search(r'\.gov\b|\.us\b|\.gc\.ca|\.gov\.[a-z]{2}\.ca', x['url']): g += 1
    lic = x.get('licence', '')
    if lic and OPEN.search(lic): g += 1
    elif not lic: x['licence_note'] = 'licence unknown'
    n = max([l.get('names_missing', 0) for l in t.get('layers', [])] or [0])
    recs = max([l.get('records', 0) or 0 for l in t.get('layers', [])] or [0])
    empty = empty_gaps(x['st'])
    fills = sorted(set(kinds) & empty)
    x['fills_empty_gap'] = fills
    if n >= 1: g += 1
    if n >= 5: g += 1
    elif fills and (recs > 0 or x.get('catalog') == 'agency server walk'): g += 1   # Oct 27 (HQ): the gap is EMPTY in this state
    x['parks_named'] = n
    if x.get('kind') == 'replaces' and not x.get('replaces_url'): x['kind'] = 'new'   # 'replaces' only when it really replaces a layer we read
    x['grade'] = g
    # HQ Oct 27: A = it fills a gap that is EMPTY in this state (or it names 5+ parks we lack); everything else tops out at B
    x['band'] = 'A' if g >= 5 and (fills or n >= 5) else 'B' if g >= 3 else 'C'
    if x.get('kind') == 'second witness': x['band'] = 'C'   # D-1: county layers never the outline
    return g


def step_b(leads, miss):
    t0 = time.time()
    for x in sorted(leads.values(), key=lambda v: (bool(v.get('tested')), v['st'])):
        if late('B', t0): break
        if x.get('tested') or not re.search(r'/(Feature|Map)Server$', x['url'], re.I): continue
        if x.get('sleeping_until', '') > time.strftime('%Y-%m-%d'): STAT['sleeping'] += 1; continue
        st2 = x['st'] if x['st'].startswith('CA-') else x['st']
        try:
            x['test'] = T.probe_service(x['url'], miss.get(st2, []) if 'outline' in x['gaps'] else [])
            x['tested'] = time.strftime('%Y-%m-%d'); x.pop('fails', None); STAT['tested'] += 1
        except Exception as e:  # noqa: BLE001
            x['fails'] = x.get('fails', 0) + 1; x['last_error'] = str(e)[:80]
            if x['fails'] >= 2: x['sleeping_until'] = time.strftime('%Y-%m-%d', time.gmtime(time.time() + 60 * 86400))


def pdf_patterns(st, cfg, leads):
    """Oct 27 (chat 8): the agency's own PDF host by known pattern (e.g. dam.assets.ohio.gov/.../wildlife-area-maps/<slug>.pdf):
    one HEAD per park of the matching kind; a hit = a map-page lead."""
    import urllib.request
    have = load('data/parkinfo-web.json', {}).get('parks', {})
    parks = load(f'data/parkinfo/US-{st}.json', {}).get('parks', {})
    n_try = n_hit = 0
    for pat in cfg.get('patterns') or []:
        kind = re.compile(pat.get('kind', '.'), re.I)
        for ref, v in parks.items():
            if n_try >= int(pat.get('max', 150)): break
            if not kind.search(v[0] or '') or (have.get(ref) or {}).get('map') or f'map-page:{ref}' in leads: continue
            slug = re.sub(r'[^a-z0-9]', '', re.sub(pat.get('strip', r'(wildlife|fishing|area|state|park|forest|nature|preserve|lake)\b'), '', (v[0] or '').lower()))
            if not slug: continue
            url = pat['url'].replace('{slug}', slug); n_try += 1
            made, ok = '', False
            try:
                req = urllib.request.Request(url, method='HEAD', headers=T.UA)
                time.sleep(1.0)
                with urllib.request.urlopen(req, timeout=20) as r:
                    ok = r.status == 200 and 'pdf' in (r.headers.get('Content-Type') or '').lower()
                    lm = r.headers.get('Last-Modified') or ''
                if ok:   # Oct 27 (chat 8): keep the map's printed date: PDF metadata is plain bytes at the front of the file
                    rq = urllib.request.Request(url, headers=dict(T.UA, Range='bytes=0-131071'))
                    time.sleep(1.0)
                    with urllib.request.urlopen(rq, timeout=30) as r2: head = r2.read()
                    m = re.search(rb'/(?:Creation|Mod)Date\s*\(D:(\d{4})(\d{2})(\d{2})', head)
                    made = '-'.join(x.decode() for x in m.groups()) if m else ''
                    if not made and lm:
                        try: made = time.strftime('%Y-%m-%d', time.strptime(lm[5:16], '%d %b %Y')) + ' (file date, not the printed date)'
                        except Exception: made = ''  # noqa: BLE001
            except Exception: ok = False  # noqa: BLE001
            if ok:
                n_hit += 1
                yr = int(made[:4]) if made[:4].isdigit() else 0
                note = ('map dated ' + made) if made else 'NO DATE on the file: check the date printed on the map'
                old = (not made) or yr < 2015
                leads[f'map-page:{ref}'] = {'url': url, 'st': st, 'ref': ref, 'title': f'{v[0]}: official map (PDF)', 'publisher': url.split('/')[2], 'catalog': 'agency PDF host',
                                          'gaps': ['map page'], 'keywords': [], 'licence': '', 'found': time.strftime('%Y-%m-%d'), 'kind': 'map page',
                                          'map_date': made, 'old_map': old, 'use': 'official map LINK only: never an outline source' + (' · OLD OR UNDATED: say so where it is shown' if old else ''),
                                          'is': [note], 'grade': 5 if not old else 4, 'band': 'A' if not old else 'B'}
    STAT['pdf_tried'] = STAT.get('pdf_tried', 0) + n_try; STAT['pdf_found'] = STAT.get('pdf_found', 0) + n_hit


def step_c(st, leads):
    """The 'Maps' tab with a real browser: agency park pages on the allow list -> map / PDF links."""
    cfg = load(D / 'maps-tab.json', {}).get(st)
    if not cfg: return
    pdf_patterns(st, cfg, leads)
    try: from playwright.sync_api import sync_playwright
    except Exception: notice('Maps tab: no browser on this runner'); return  # noqa: BLE001,E702
    allow, files = cfg.get('hosts', []), cfg.get('files', [])
    have = load('data/parkinfo-web.json', {}).get('parks', {})
    parks = load(f'data/parkinfo/US-{st}.json', {}).get('parks', {})
    todo = [(r, v[0], v[1]) for r, v in parks.items() if v[1] and any(h in v[1] for h in allow) and not (have.get(r) or {}).get('map')]
    t0, pages, errs = time.time(), 0, {}
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(user_agent=T.UA['User-Agent'])
        for ref, name, url in todo[:int(cfg.get('max', 300))]:
            host = url.split('/')[2]
            if late('C', t0) or pages >= 300 or errs.get(host, 0) >= 5: break
            try:
                pg.goto(url, timeout=30000, wait_until='networkidle'); pages += 1
                links = pg.eval_on_selector_all('a[href]', 'as => as.map(a => [a.href, (a.innerText||"").trim().slice(0,60)])')
            except Exception: errs[host] = errs.get(host, 0) + 1; time.sleep(3); continue  # noqa: BLE001,E702
            hit = [(h, t) for h, t in links if re.search(r'map|\.pdf|geopdf|brochure', h + ' ' + t, re.I)
                   and any(f in h.split('/')[2] for f in files) and not re.search(r'google\.|bing\.|apple\.com/maps|mapquest', h, re.I)]
            if pages <= 3: MAPDBG.append({'ref': ref, 'url': url, 'links': len(links), 'map_like': [h for h, t in links if re.search(r'map|\.pdf', h + ' ' + t, re.I)][:8], 'kept': len(hit)})
            if hit:
                k = f'map-page:{ref}'
                leads[k] = {'url': hit[0][0], 'st': st, 'ref': ref, 'title': f'{name}: {hit[0][1] or "map"}', 'publisher': host, 'catalog': 'Maps tab',
                            'gaps': ['map page'], 'keywords': [], 'licence': '', 'found': time.strftime('%Y-%m-%d'), 'kind': 'map page',
                            'all_links': [h for h, _ in hit][:6], 'grade': 5 if hit[0][0].lower().endswith('.pdf') else 4}
                leads[k]['band'] = 'A' if leads[k]['grade'] >= 5 else 'B'
            time.sleep(3)
        b.close()
    STAT['pages'] += pages
    kept = sum(1 for k, v in leads.items() if k.startswith('map-page:') and v.get('catalog') == 'Maps tab' and v.get('found') == time.strftime('%Y-%m-%d'))
    if pages >= 10 and kept == 0: notice(f'WARNING Maps tab {st}: {pages} agency pages opened, 0 map links kept: the pages hide their map links from the reader (see maps_tab_sample)')


def main():
    kws = load(D / 'keywords.json', {}).get('gaps', {})
    if not kws: notice('no keywords.json: nothing to search'); return
    kwlog = []
    known = already_read()
    old = load(D / 'leads.json', {}).get('leads', {})
    # Oct 27: leads kept from an earlier run must pass today's publisher test too (the Ohio test kept Great Smoky Mountains layers)
    leads = {k: v for k, v in old.items() if v.get('catalog') == 'Maps tab' or T.official_org(v.get('publisher', ''), v['st'])
             or re.search(r'\b' + re.escape(T.STATE_NAMES.get(v['st'], v['st'])) + r'\b', v.get('title', ''), re.I)}
    before = set(leads)
    miss = T.missing() if 'B' in STEPS else {}
    for st in STATES:
        st_key = st if st.startswith('CA-') else st
        if 'A' in STEPS: step_a(st_key, kws, known, leads, kwlog)
        if 'C' in STEPS: step_c(st_key, leads)
        save_json(D / 'leads.json', {'about': 'Discovery bot leads (never used by the live data; chat 8 reads leads.md).', 'date': time.strftime('%Y-%m-%d'), 'leads': leads}, indent=1)
    if 'B' in STEPS: step_b(leads, miss)
    for x in leads.values():
        if x.get('catalog') not in ('Maps tab', 'agency PDF host'): grade(x)
    # chat 8's hand finds (data/discovery/known-good.json): the bot must find them by itself; they are merged in as known-good either way
    kg = load(D / 'known-good.json', {})
    kg_found, kg_missed = [], []
    for st in STATES:
        for k in (kg.get(st) or []):
            key = next((u for u in leads if key_of(u) == key_of(k['url'])), None)
            if key: leads[key]['known_good'] = k.get('note', 'chat 8'); leads[key]['hand_band'] = k.get('band', ''); kg_found.append(k['url'])
            else:
                kg_missed.append(k['url'])
                leads[key_of(k['url'])] = {'url': k['url'], 'st': st, 'title': k.get('title', k['url'].split('/')[-2])[:90], 'publisher': k['url'].split('/')[2], 'catalog': 'hand (chat 8)',
                                           'gaps': k.get('gaps', []), 'keywords': [], 'licence': '', 'found': time.strftime('%Y-%m-%d'), 'kind': 'new', 'known_good': k.get('note', 'chat 8'),
                                           'hand_band': k.get('band', ''), 'missed_by_bot': True}
    STAT['known_good_found'] = len(kg_found); STAT['known_good_missed'] = len(kg_missed)
    new = sorted(set(leads) - before)
    STAT['new'] = len(new)
    # learning loop: which keyword found what this run
    found = {}
    for k in new:
        for kw in leads[k].get('keywords', []): found.setdefault(kw, []).append(leads[k]['url'])
    rank = sorted(leads.values(), key=lambda v: (-v.get('grade', 0), not (T.official_org(v.get('publisher', ''), v['st']) or v.get('catalog') == 'agency server walk'), -v.get('parks_named', 0), v['st']))
    save_json(D / 'leads.json', {'about': 'Discovery bot leads (never used by the live data; chat 8 reads leads.md).', 'date': time.strftime('%Y-%m-%d'),
                                 'stats': STAT, 'what_ran': kwlog, 'known_good_missed': kg_missed, 'maps_tab_sample': MAPDBG, 'found_by_keyword_this_run': found, 'leads': leads}, indent=1)
    md = ['# Discovery bot: top 50 leads', f"Run {time.strftime('%Y-%m-%d')}, states {' '.join(STATES)}. The bot's number is the queue order only; chat 8 gives the real A/B/C.", '',
          f"Known-good hand finds (chat 8): {STAT.get('known_good_found', 0)} found by the bot itself, {STAT.get('known_good_missed', 0)} missed" + (': ' + ', '.join(kg_missed) if kg_missed else '') + '.', '',
          '| Band | Grade | State | Gap | What | What it is | Publisher | Parks named | Kind | Link |', '|---|---|---|---|---|---|---|---|---|---|']
    for x in rank[:50]:
        md.append(f"| {x.get('band', '')}{(' (chat 8: ' + x['hand_band'] + ')') if x.get('hand_band') else ''} | {x.get('grade', 0)} | {x['st']} | {', '.join(x.get('gaps', []))} | {x.get('title', '')[:60].replace('|', '/')} | "
                  f"{'; '.join(x.get('is') or [])[:90].replace('|', '/')} | {x.get('publisher', '')[:40].replace('|', '/')} | {x.get('parks_named', '')} | {x.get('kind', '')}{' · ' + x['licence_note'] if x.get('licence_note') else ''} | {x['url']} |")
    md += ['', '## What ran', '| Source / keyword | Gap | Hits | New | Already read | Not the agency | Not this state | Theme |', '|---|---|---|---|---|---|---|---|']
    for k in kwlog:
        if 'keyword' in k: md.append(f"| {k['keyword']} | {k['gap']} | {k['hits']} | {k['new']} | {k['already_read']} | {k['not_agency']} | {k['not_this_state']} | {k['theme']} |")
        elif 'services' in k: md.append(f"| server walk {k['server']} | all | {k['services']} services in {k['folders']} folders | {k['leads']} | | | | |")
    (D / 'leads.md').write_text('\n'.join(md) + '\n')
    obs = [leads[k] for k in new if leads[k].get('band') == 'A']
    if obs:
        save_json(D / 'new-a-leads.json', {'date': time.strftime('%Y-%m-%d'), 'leads': [{'st': x['st'], 'title': x['title'], 'url': x['url'], 'gaps': x['gaps']} for x in obs]}, indent=1)
    bands = {b: sum(1 for x in leads.values() if x.get('band') == b) for b in 'ABC'}
    notice(f"{' '.join(STATES)}: {STAT} · bands {bands} · {len(obs)} new A · {round((time.time() - T0) / 60)} min")


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        notice(f'stopped: {type(e).__name__}: {e}')
    sys.exit(0)
