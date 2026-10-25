#!/usr/bin/env python3
"""State park campgrounds, cabins and lodges for every state but Kentucky (Brandon Oct 24 2026: official sources only).

Writes data/campstate/US-XX.json {state, updated, source, camps:[[id, name, lat, lon, kind(c|b|l), potaRef, officialUrl,
reserveUrl]]} for the one-page Campgrounds & Cabins state picker in the Activators Lounge, plus data/campstate/index.json
{updated, states:{XX:{n, source, updated}}, none:[...]} so the page knows which states have a list. Kentucky stays on its
hand-checked kpc-campgrounds.json.

SOURCE 1 (this script): the state's OWN GIS open data. For each state it takes the server roots we already know
(data/state-gis.json = verified park layers, data/state-gis-found.json = the layer scan, ROOTS in kpc_state_gis.py),
walks those servers (folders -> services -> layers) and keeps point/polygon layers that look like campgrounds, cabins,
lodges or park facilities. Generic 'facilities' layers are filtered to the camp/cabin/lodge rows only.
SOURCE 2 (state reservation systems) is NOT built yet: it has to be written against what the first runs show. A state
with no readable official layer is listed in the rolling GitHub issue labelled 'state-camps' (BODY edits only, never a
comment, so it never emails) and its old file, if any, is kept. Nothing is guessed, and no OpenStreetMap / pay sites.

Skips places already in data/campfed (same spot within 300 m, or the same name within 3 miles). Matches each place to a
POTA park in data/parkinfo/US-XX.json: nearest park within 2 miles AND a name match, or the data's own park-name field
matching a park within 15 miles. Every step is safe: a failure keeps last week's files and the job still ends green.
Env: STATES (blank = every state but KY), DRY_RUN=1 (print, write nothing), SPEED (workers, default 6)."""
import ast, datetime, hashlib, json, math, os, pathlib, re, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
import concurrent.futures as cf

ORG_SEARCH = os.environ.get('ORG_SEARCH', '1') != '0'      # pass 2 for states with no list
DIAG = {}                                   # per state: what was crawled and what each layer held (data/campstate/layers.json)
UA = 'KPC-state-camps/1.0 (Kentucky Portable Club; kentuckyportableclub.github.io)'
OUT = pathlib.Path('data/campstate')
DRY = os.environ.get('DRY_RUN') == '1'
ALL = ('AL AK AZ AR CA CO CT DC DE FL GA HI ID IL IN IA KS LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR '
       'PA RI SC SD TN TX UT VT VA WA WV WI WY').split()
STATES = (os.environ.get('STATES') or '').replace(',', ' ').upper().split() or ALL
STATES = [s for s in STATES if s in ALL]
WORKERS = int(os.environ.get('SPEED') or 6)
DEADLINE = time.time() + 40 * 60            # the workflow allows 50 min; stop crawling before that
REPO = os.environ.get('GITHUB_REPOSITORY') or 'KentuckyPortableClub/KPC-Links'
TODAY = datetime.date.today().isoformat()

STRONG = re.compile(r'camp|cabin|lodg|yurt|cottage|\brv\b', re.I)                  # picks LAYERS (names only, loose on purpose)
GENERIC = re.compile(r'facilit|amenit|point[ _]?of[ _]?interest|\bpoi\b|park[ _]?site|asset|overnight|\bsites?\b', re.I)
PARKCTX = re.compile(r'park|recre|\brec[ _]|camp|cabin|outdoor|visitor|tourism', re.I)   # a generic layer must sit in a park/recreation context
SVC_OK = re.compile(STRONG.pattern + '|' + PARKCTX.pattern, re.I)
FOLDER_OK = re.compile(r'park|recre|outdoor|dnr|tourism|public|open|facil|camp|visitor|lodg|asset|boundar|hosted|utility|data', re.I)
SVC_BAD = re.compile(r'campus|universit|college|school|hospital|health|business|census|election|parcel|cadastr', re.I)
LAYER_BAD = re.compile(r'parking|\blots?\b|building|campus|footprint|structure|extension|\bccc\b|trail(?!head)|boundary|boundaries|road|wetland|hunt|fish|stock|sign|photo|contour|parcel|district|'
                       r'region|county|watershed|invasive|timber|burn|fire|flood|soil|geolog|survey|easement|zone', re.I)
# rows: whole words only ('Campbell', 'Camden', 'campus' are not camps); lodges only count in a lodging layer (below)
CAMPWORD = re.compile(r'\b(?:camps?|camping|campgrounds?|campsites?|campers?|cabins?|cottages?|yurts?|rv)\b', re.I)
LODGEWORD = re.compile(r'\b(?:lodge|lodges|lodging)\b', re.I)
CAMP_SUBSTR = ('CAMP', 'CABIN', 'LODG', 'YURT', 'COTTAGE')
# individual sites / units are not places to list: 'Campsites' layers of thousands of points, 'Campsite 33', 'Cabin 30', '004'
SITE_LAYER = re.compile(r'camp[ _]?sites?\b|camping[ _]?sites?|reservable|individual|\bsites?$|\bspaces?\b|\bpads?\b|\bunits?$', re.I)
SITE_END = re.compile(r'\b(?:camp ?sites?|sites?|units?|spaces?|lots?|cabins?|yurts?|pads?)\s*#?\d+[a-z]?$', re.I)    # '... Campsite 4'
SITE_NAME = re.compile(r'^(?:[\W\d_]*|[A-Za-z]{0,3}\W?\d+[A-Za-z]?|(?:camp ?sites?|sites?|cabins?|yurts?|spaces?|units?|lots?|loops?|pads?|rv)\W*[#]?\s*\w{0,3}\d+\w*)$', re.I)
EXCL = re.compile(r'picnic|shelter|boat ramp|launch|trailhead|restroom|day[- ]use|dump station|parking|playground|'
                  r'pavilion|overlook|museum|visitor center|golf|marina|beach', re.I)
HARD_EXCL = re.compile(r'\bstore\b|bath ?house|\bshed\b|\boffice\b|comfort station|restroom|\bshowers?\b|laundry|dump station|amphitheat|concession|'
                       r'maintenance|firewood|parking|\blot\b|trailhead|boat ramp|picnic|entrance station|kiosk|fee station|\bgate\b|water spigot|'
                       r'hotel|motel|\bmarriott|hilton|comfort inn|best western|hampton|holiday inn', re.I)
GENERIC_NAME = re.compile(r'^(?:(?:the|main|upper|lower|east|west|north|south|group|primitive|rustic|rv|tent|horse|equestrian|overflow|'
                          r'walk-?in|cabin|cabins|camp|campground|campgrounds|camping|area|loop|side|and|day|use|\d+)\W*)+$', re.I)
BAD_HOST = re.compile(r'campendium|hipcamp|tripadvisor|yelp|facebook|google\.|bing\.|openstreetmap|allstays|koa\.com|'
                      r'campgroundreviews|thedyrt|recreation\.gov/api', re.I)
NAME_F = ['FACILITY_NAME', 'FACILITYNAME', 'FAC_NAME', 'CAMPGROUND_NAME', 'CAMP_NAME', 'CAMPGROUND', 'SITE_NAME', 'SITENAME',
          'FEATURE_NAME', 'NAME', 'LABEL', 'TITLE', 'FAC_NAME1', 'PLACE_NAME']
PARK_F = ['PARK_NAME', 'PARKNAME', 'PARK', 'PARK_NM', 'UNIT_NAME', 'UNITNAME', 'AREA_NAME', 'MANAGED_AREA', 'PROPERTY_NAME', 'PROPNAME',
          'SITE_NAME', 'SITENAME', 'SITE', 'LOCATION', 'PARKABBR']
URL_F = ['WEBSITE', 'WEB_URL', 'WEBURL', 'URL', 'LINK', 'WEBPAGE', 'WEB_LINK', 'PAGE_URL', 'PARK_URL', 'HYPERLINK', 'WEB', 'WEBSITE_URL']
RES_F = ['RESERVATION_URL', 'RESERVE_URL', 'RESERVATIONURL', 'RESERVATION_LINK', 'BOOKING_URL', 'BOOKING', 'RESERVE', 'RESERVATIONS',
         'RESERVATION', 'RSV_URL', 'ONLINE_RESERVATION']
TYPE_RX = re.compile(r'type|categ|class|facil|amenit|use|activ|desc|feature|subtype|name', re.I)


def note(t, m):
    print(f'::notice title={t}::{str(m).replace(chr(10), " ")[:700]}', flush=True)


def get_json(url, params=None, tries=3):
    q = dict(params or {}); q.setdefault('f', 'json')
    full = url + ('&' if '?' in url else '?') + urllib.parse.urlencode(q)
    err = None
    for i in range(tries):
        if time.time() > DEADLINE:
            return None
        try:
            with urllib.request.urlopen(urllib.request.Request(full, headers={'User-Agent': UA}), timeout=40) as r:
                j = json.loads(r.read().decode('utf-8', 'replace'))
            if isinstance(j, dict) and j.get('error'):
                err = j['error']
                if str((err or {}).get('code')) in ('400', '403', '404', '499', '498'):
                    return {'error': err}
                time.sleep(2 + i * 3); continue
            return j
        except urllib.error.HTTPError as e:
            err = f'HTTP {e.code}'
            if e.code in (400, 401, 403, 404): return {'error': err}
            time.sleep(2 + i * 4)
        except Exception as e:  # noqa: BLE001
            err = str(e)[:100]; time.sleep(2 + i * 4)
    return {'error': err}


def ok(j):
    return isinstance(j, dict) and 'error' not in j


def cfg():
    try: return json.load(open('data/campstate-layers.json'))
    except Exception: return {}  # noqa: E722


def allowed(st):
    """Layers a person found by hand (data/campstate-layers.json "allow": {ST: [service or layer urls]}): read like the crawl's own."""
    return expand(cfg().get('allow', {}).get(st, []))


def expand(urls, per_service=12):
    """Service / layer urls -> readable point or polygon layers."""
    out = []
    for u in urls:
        m = re.match(r'(.*/(?:Feature|Map)Server)(?:/(\d+))?$', (u or '').strip())
        if not m or any(d in u for d in denied()): continue
        svc = m.group(1)
        ids = [int(m.group(2))] if m.group(2) is not None else []
        if not ids:
            sj = get_json(svc)
            ids = [l['id'] for l in (sj.get('layers') or [])][:per_service] if ok(sj) else []
        for lid in ids:
            lu = f'{svc}/{lid}'; lj = get_json(lu)
            if not ok(lj) or (lj.get('geometryType') or '') not in ('esriGeometryPoint', 'esriGeometryPolygon'): continue
            nm = lj.get('name') or ''
            if LAYER_BAD.search(nm) and not STRONG.search(nm): continue
            out.append({'url': lu, 'name': nm, 'fields': [(f.get('name'), f.get('type')) for f in lj.get('fields', [])], 'geo': lj['geometryType'],
                        'strong': bool(STRONG.search(nm + ' ' + svc.rsplit('/', 2)[-2])), 'max': int(lj.get('maxRecordCount') or 1000), 'svc': svc,
                        'lodging': bool(re.search(r'lodg|resort|cabin', nm + ' ' + svc, re.I))})
    return out


NOT_OFFICIAL = re.compile(r'county|city of|town of|village|township|borough|parish|district|universit|college|school|foundation|club|association|\bllc\b|\binc\b|'
                          r'consult|engineering|esri|conservancy|\btrust\b|society|\bcorp\b|united states|u\.s\.|\busfs\b|\busda\b|\busgs\b|noaa|national park service|'
                          r'army corps|bureau of land|\bblm\b|national forest|tribe|nation\b|hospital|church', re.I)
OFFICIAL_ORG = re.compile(r'department|dept|division|\bdnr\b|\bdcr\b|\bdep\b|\bdec\b|state parks?|parks (?:and|&) (?:recreation|wildlife|tourism)|natural resources|'
                          r'conservation|fish|wildlife|\bgame\b|forestry|forest service|environment|commission|office of|geospatial|\bgis\b|state of|commonwealth|'
                          r'bureau|recreation|tourism|\bgeo\b', re.I)
ORGNAME = {}
STATE_NAMES = {'DC': 'District of Columbia'}
try:
    for _k, _v in json.load(open('data/campstate-sources.json'))['states'].items(): STATE_NAMES[_k] = _v['name']
except Exception: pass  # noqa: E722


def official_org(name, st):
    """An ArcGIS Online account whose NAME says it is that state's own agency (state name or abbreviation + a government word, no county/city/university)."""
    n = name or ''
    if not n or NOT_OFFICIAL.search(n): return False
    sn = STATE_NAMES.get(st, st)
    return bool((re.search(re.escape(sn), n, re.I) or re.search(r'\b%s\b' % st, n)) and OFFICIAL_ORG.search(n))


def org_search(st):
    """For a state with no list yet: search ArcGIS Online for camp layers, keep only items owned by an account that looks like the
    state's own agency. The accepted account names are written to layers.json so a person can check them."""
    sn = STATE_NAMES.get(st, st)
    acc, seen_org = [], 0
    q = f'(campground OR campgrounds OR "camping areas" OR campsites OR cabins OR "recreation sites") AND "{sn}" AND (type:"Feature Service" OR type:"Map Service")'
    for start in (1, 101):
        j = get_json('https://www.arcgis.com/sharing/rest/search', {'q': q, 'num': 100, 'start': start, 'sortField': 'numviews', 'sortOrder': 'desc'})
        if not ok(j): break
        for it in j.get('results') or []:
            oid, url = it.get('orgId'), it.get('url') or ''
            if not oid or not re.search(r'/(?:Feature|Map)Server', url): continue
            if oid not in ORGNAME:
                if seen_org >= 25: continue
                seen_org += 1
                pj = get_json(f'https://www.arcgis.com/sharing/rest/portals/{oid}')
                ORGNAME[oid] = (pj.get('name') or '') if ok(pj) else ''
            if official_org(ORGNAME.get(oid), st):
                acc.append({'org': ORGNAME[oid][:70], 'title': (it.get('title') or '')[:60], 'url': url})
        if len(j.get('results') or []) < 100: break
    DIAG.setdefault(st, {})['orgsearch'] = acc[:40]
    return [a['url'] for a in acc][:15]


def file_layers(st):
    """Official open-data FILES ("files": {ST: {"ckan": package_show url}}), e.g. California State Parks' campground dataset."""
    out = []
    c = cfg().get('files', {}).get(st)
    if not c: return out
    j = get_json(c['ckan']) if c.get('ckan') else None
    if not ok(j): return out
    for r in ((j.get('result') or {}).get('resources') or []):
        fmt = (r.get('format') or '').upper()
        if fmt in ('CSV', 'GEOJSON') and r.get('url'):
            out.append({'url': r['url'], 'file': r['url'], 'fmt': fmt, 'name': ((j['result'].get('title') or 'dataset')[:60]), 'fields': [], 'geo': 'esriGeometryPoint',
                        'strong': True, 'lodging': True, 'max': 1000, 'svc': 'file'})
            break
    return out


def file_rows(lay):
    import csv, io
    try:
        with urllib.request.urlopen(urllib.request.Request(lay['file'], headers={'User-Agent': UA}), timeout=120) as r:
            raw = r.read(40_000_000).decode('utf-8-sig', 'replace')
    except Exception: return []  # noqa: E722
    feats = []
    if lay['fmt'] == 'GEOJSON':
        try:
            for f in json.loads(raw).get('features', []):
                g = f.get('geometry') or {}
                if g.get('type') == 'Point': feats.append({'attributes': f.get('properties') or {}, 'geometry': {'x': g['coordinates'][0], 'y': g['coordinates'][1]}})
        except Exception: pass  # noqa: E722
    else:
        rd = csv.DictReader(io.StringIO(raw)); cols = rd.fieldnames or []
        lat = next((c for c in cols if re.fullmatch(r'(?i)y|lat(itude)?|point_y', c.strip())), None) or next((c for c in cols if re.search(r'(?i)lat', c)), None)
        lon = next((c for c in cols if re.fullmatch(r'(?i)x|lon(g|gitude)?|lng|point_x', c.strip())), None) or next((c for c in cols if re.search(r'(?i)lon|lng', c)), None)
        for row in rd:
            try:
                x, y = float(row[lon]), float(row[lat])
                if abs(x) > 180 or abs(y) > 90:                      # metres, not degrees: Web Mercator (EPSG:3857) is the usual case
                    if abs(x) > 2.0038e7 or abs(y) > 2.0038e7: continue
                    x, y = x / 20037508.34 * 180, math.degrees(math.atan(math.sinh(y / 6378137.0)))
                feats.append({'attributes': row, 'geometry': {'x': x, 'y': y}})
            except Exception: continue  # noqa: E722
    if feats: lay['fields'] = [(k, 'esriFieldTypeString') for k in feats[0]['attributes']]
    lay['raw'] = [{k: str(v)[:40] for k, v in list(f['attributes'].items())[:12]} for f in feats[:2]] + [{'geometry': f['geometry']} for f in feats[:1]]
    return feats


def denied():
    """data/campstate-layers.json {"deny": [url fragments]}: layers a person has looked at and ruled out."""
    try: return [d for d in json.load(open('data/campstate-layers.json')).get('deny', []) if d]
    except Exception: return []  # noqa: E722


# ---------------------------------------------------------------- where to look
def roots_for(st):
    """Server roots (…/rest/services) to walk for a state, from everything we already know about its GIS."""
    # OFFICIAL ONLY. data/state-gis.json = the layers Claude verified as the agency's own (its server or its ArcGIS Online
    # account). Everything else (the layer scan, the root guesses) counts only on a government / state-university host:
    # the shared ArcGIS Online cloud holds anyone's data (Oct 24 first run: nursing homes, other states' parks).
    gov = re.compile(r'^https?://[^/]*\.(?:gov|us|edu)(?::\d+)?/', re.I)
    urls = []
    try:
        for l in json.load(open('data/state-gis.json')).get('states', {}).get(st, []): urls.append(l.get('url', ''))
    except Exception: pass  # noqa: E722
    extra = []
    try:
        for l in json.load(open('data/state-gis-found.json')).get('layers', []):
            if l.get('st') == st: extra += [l.get('url', ''), l.get('service', '')]
    except Exception: pass  # noqa: E722
    try:
        src = open('.github/scripts/kpc_state_gis.py', encoding='utf-8').read()
        for n in ast.parse(src).body:
            if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'ROOTS':
                extra += ast.literal_eval(n.value).get(st, [])
    except Exception: pass  # noqa: E722
    host = lambda u: re.sub(r'^https?://([^/:]+).*', r'\1', u or '').lower()
    trusted = {host(u) for u in urls}
    try:
        for n in ast.parse(open('.github/scripts/kpc_state_gis.py', encoding='utf-8').read()).body:
            if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'ROOTS':
                trusted |= {host(u) for u in ast.literal_eval(n.value).get(st, []) if not re.search(r'arcgis\.com', u)}
    except Exception: pass  # noqa: E722
    mine = re.compile(r'(?:^|\.)%s\.(?:gov|us)$|\.state\.%s\.us$' % (st.lower(), st.lower()))
    # the layer scan also holds other states' and counties' servers (Ohio listed Minnesota's): only the state's own hosts
    urls += [u for u in extra if u and gov.match(u) and (host(u) in trusted or mine.search(host(u)))]
    roots, folders = [], {}
    urls = [u for u in urls if u]
    for u in urls:
        m = re.match(r'(https?://[^?#]*?/rest/services)(?:/(.*))?', u or '')
        if not m: continue
        if m.group(1) not in roots: roots.append(m.group(1))
        if m.group(2) and '/' in m.group(2):
            folders.setdefault(m.group(1), set()).add(m.group(2).split('/')[0])
    return roots, folders


def pick(fields, order, rx=None):
    up = {f.upper(): f for f in fields}
    for o in order:
        if o in up: return up[o]
    if rx:
        for f in fields:
            if re.search(rx, f, re.I): return f
    return None


def discover(st):
    """-> list of layer dicts {url, name, fields, geo, strong, max, svc}."""
    roots, known_folders = roots_for(st)
    found, seen = [], set()
    DIAG[st] = {'roots': []}
    for root in roots[:6]:
        if time.time() > DEADLINE: break
        top = get_json(root)
        dg = {'root': root, 'ok': ok(top), 'services': 0, 'candidates': 0, 'layers': 0}
        DIAG[st]['roots'].append(dg)
        if not ok(top):
            dg['err'] = str((top or {}).get('error'))[:80]; continue
        svcs = [(s['name'], s['type']) for s in top.get('services', []) if s.get('type') in ('FeatureServer', 'MapServer')]
        for fo in top.get('folders', [])[:80]:
            if fo in known_folders.get(root, set()) or FOLDER_OK.search(fo) or len(top.get('folders', [])) <= 12:
                fj = get_json(root + '/' + fo)
                if ok(fj): svcs += [(s['name'], s['type']) for s in fj.get('services', []) if s.get('type') in ('FeatureServer', 'MapServer')]
        dg['services'] = len(svcs)
        svcs = [s for s in svcs if SVC_OK.search(s[0]) and not SVC_BAD.search(s[0])][:90]
        dg['candidates'] = len(svcs)
        for name, typ in svcs:
            if time.time() > DEADLINE: break
            su = f'{root}/{name}/{typ}'
            sj = get_json(su)
            if not ok(sj): continue
            cand = []
            for l in (sj.get('layers') or [])[:60]:
                ln = l.get('name') or ''
                if SITE_LAYER.search(ln.strip()) and not re.search(r'campgrounds?\b|cabins\b', ln, re.I): continue
                if re.search(r'lodg|resort', ln, re.I) and not PARKCTX.search(ln + ' ' + name): continue
                if any(d in f'{su}/{l["id"]}' for d in denied()): continue
                st_ = bool(STRONG.search(ln))
                gen = (bool(GENERIC.search(ln)) or bool(GENERIC.search(name) and not LAYER_BAD.search(ln))) and bool(PARKCTX.search(ln + ' ' + name))
                if (st_ or gen) and not (LAYER_BAD.search(ln) and not st_):
                    cand.append((l['id'], ln, st_ or bool(STRONG.search(name))))
            for lid, ln, strong in cand[:12]:
                lu = f'{su}/{lid}'
                if lu in seen: continue
                seen.add(lu)
                lj = get_json(lu)
                if not ok(lj): continue
                geo = lj.get('geometryType') or ''
                if geo not in ('esriGeometryPoint', 'esriGeometryPolygon') or (geo.endswith('Polygon') and not strong): continue
                dg['layers'] += 1
                found.append({'url': lu, 'name': ln, 'fields': [(f.get('name'), f.get('type')) for f in lj.get('fields', [])],
                              'geo': geo, 'strong': strong, 'max': int(lj.get('maxRecordCount') or 1000), 'svc': name,
                              'lodging': bool(re.search(r'lodg|resort', ln + ' ' + name, re.I))})
            time.sleep(.2)
    for lay in allowed(st) + file_layers(st):
        if lay['url'] not in seen and not any(d in lay['url'] for d in denied()):
            seen.add(lay['url']); found.append(lay)
    DIAG[st]['allowed'] = sum(1 for l in found if l.get('svc') not in (None,) and (l['url'] in {x for x in cfg().get('allow', {}).get(st, [])} or l.get('file')))
    return found


# ---------------------------------------------------------------- reading a layer
def fetch_rows(lay):
    if lay.get('file'): return file_rows(lay)
    strs = [n for n, t in lay['fields'] if t == 'esriFieldTypeString']
    where = '1=1'
    if not lay['strong']:
        fs = [n for n in strs if TYPE_RX.search(n)][:6]
        where = ' OR '.join(f"UPPER({f}) LIKE '%{w}%'" for f in fs for w in CAMP_SUBSTR) or '1=1'
    rows, off, page = [], 0, max(100, min(lay['max'], 1000))
    for attempt in (where, '1=1'):
        rows, off = [], 0
        while len(rows) < 6000:
            j = get_json(lay['url'] + '/query', {'where': attempt, 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326,
                                                 'resultOffset': off, 'resultRecordCount': page})
            if not ok(j):
                if attempt != '1=1' and not rows: break          # the LIKE failed: try everything instead
                return rows
            fs = j.get('features') or []
            rows += fs; off += len(fs)
            if not fs or not (j.get('exceededTransferLimit') or len(fs) >= page): break
        if rows or attempt == '1=1': return rows
    return rows


def xy(g, geo):
    if not g: return None
    try:
        if geo.endswith('Point'): lo, la = float(g['x']), float(g['y'])
        else:
            pts = [p for ring in g.get('rings', []) for p in ring]
            lo = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2; la = (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2
    except Exception: return None  # noqa: E722
    if not (15 < la < 72 and -180 < lo < -60 or 15 < la < 72 and 165 < lo < 180): return None
    return round(la, 5), round(lo, 5)


def nice(s):
    s = re.sub(r'\s+', ' ', str(s or '')).strip()
    if s.isupper() or s.islower(): s = re.sub(r"'S\b", "'s", s.title())
    return s


def url_ok(u):
    u = str(u or '').strip(); u = u.split()[0] if u else ''
    if re.match(r'^www\.', u, re.I): u = 'https://' + u
    if not re.match(r'^https?://[^/]+\.[a-z]{2,}', u, re.I) or BAD_HOST.search(u): return ''
    return u[:300]


def norm(s): return re.sub(r'[^a-z0-9]+', ' ', str(s).lower()).strip()


def kind_of(text, layname):
    t = (text + ' ' + layname).lower()
    if re.search(r'cabin|cottage|yurt', t): return 'b'
    if re.search(r'\blodge|\blodging|\binn\b|resort', t) and not re.search(r'campground|camp\b', t): return 'l'
    return 'c'


def rows_to_camps(lay, feats):
    flds = [n for n, _ in lay['fields']]
    nf, pf = pick(flds, NAME_F, r'name'), pick(flds, PARK_F)
    uf, rf = pick(flds, URL_F, r'url|web|link'), pick(flds, RES_F, r'reserv|booking')
    tf = [n for n, t in lay['fields'] if t == 'esriFieldTypeString' and TYPE_RX.search(n)][:8]
    out = []
    for f in feats:
        a, p = f.get('attributes') or {}, xy(f.get('geometry'), lay['geo'])
        if not p:                                           # some layers carry the position only as LAT / LONG fields
            try:
                la_, lo_ = float(a.get('LAT') or a.get('Lat') or a.get('LATITUDE') or a.get('latitude')), float(a.get('LONG_') or a.get('LONG') or a.get('Long') or a.get('LON') or a.get('LONGITUDE') or a.get('longitude'))
                if 15 < la_ < 72 and -180 < lo_ < -60: p = (la_, lo_)
            except (TypeError, ValueError): p = None
        if not p or not nf: continue
        name = nice(a.get(nf))
        if not name or name.lower() in ('none', 'null', 'unnamed', 'other', 'y', 'n', 'yes', 'no') or len(name) < 4 or SITE_NAME.match(name): continue
        park = nice(a.get(pf)) if pf and pf != nf else ''
        if park and (park.isupper() and len(park) <= 5 or len(park) < 4 or park.lower() in ('y', 'n', 'yes', 'no', 'none', 'null')): park = ''
        if GENERIC_NAME.match(name):                      # 'Campground' / 'Group Camp': only useful with its park in front
            if not park: continue
            name = f'{park} {name}'
        if HARD_EXCL.search(name) or SITE_END.search(name): continue
        text = name + ' ' + ' '.join(str(a.get(x) or '') for x in tf)
        camp, lodge = bool(CAMPWORD.search(text)), bool(LODGEWORD.search(text)) and lay['lodging']
        if not (camp or lodge or (lay['strong'] and not EXCL.search(name))): continue
        if EXCL.search(text) and not (camp or lodge): continue
        u, r = url_ok(a.get(uf)) if uf else '', url_ok(a.get(rf)) if rf else ''
        if u and re.search(r'reserv|book|rsv|camis|usedirect|aspira|reserveamerica', u, re.I) and not r: r, u = u, ''
        out.append({'name': name, 'lat': p[0], 'lon': p[1], 'kind': kind_of(text, lay['name']), 'url': u, 'res': r,
                    'park': park})
    return out


def group_by_park(lay, feats):
    """A layer of individual campsites (listed under 'group' in campstate-layers.json): one camp per park, at the middle of its sites."""
    flds = [n for n, _ in lay['fields']]
    pf = pick(flds, PARK_F, r'park') or pick(flds, ['PARKNAME', 'ParkName', 'PARK'], r'park')
    if not pf: return []
    # Oct 25 2026 (chat 2, from chat 5's note 'the WA list has host sites and yurts'): read the site's TYPE too.
    # Camp host / staff sites are not for the public: left out. Cabins, yurts and cottages become their own
    # '<park> Cabins & Yurts' row (kind 'b'), so they no longer pull the campground's middle point or call a
    # yurt-only park a 'Campground'.
    tf = [n for n, t in lay['fields'] if n != pf and t == 'esriFieldTypeString' and TYPE_RX.search(n)][:8]
    by, skipped = {}, 0
    for f in feats:
        p = xy(f.get('geometry'), lay['geo'])
        a = f.get('attributes') or {}
        park = nice(a.get(pf))
        if not p or not park or len(park) < 4: continue
        text = ' '.join(str(a.get(n) or '') for n in tf)
        if HOSTSITE.search(text):
            skipped += 1
            continue
        k = 'b' if re.search(r'cabin|cottage|yurt', text, re.I) else 'c'
        by.setdefault((park, k), []).append(p)
    if skipped: print(f'    {lay["name"]}: {skipped} camp host / staff sites left out')
    out = []
    for (park, k), pts in by.items():
        la, lo = sum(x[0] for x in pts) / len(pts), sum(x[1] for x in pts) / len(pts)
        if k == 'b':
            name = f'{park} Cabins & Yurts'
        else:
            name = park if re.search(r'camp|cabin|yurt|lodge', park, re.I) else f'{park} Campground'
        out.append({'name': name, 'lat': la, 'lon': lo, 'kind': k, 'url': '', 'res': '', 'park': park})
    return out


HOSTSITE = re.compile(r'\bhost|\bstaff|employee|volunteer|ranger|admin|\bresidence|not\s+reserv', re.I)


# ---------------------------------------------------------------- inside the state?
try:
    _SHAPES = {b['a']: [pl[0] for pl in b['p']] for b in json.load(open('kpc-us-states.json'))}
except Exception: _SHAPES = {}  # noqa: E722


def _inside(x, y, ring):
    c = False; j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]; xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi: c = not c
        j = i
    return c


def in_state(st, la, lo):
    rings = _SHAPES.get(st)
    if not rings: return True
    for dx, dy in ((0, 0), (.05, 0), (-.05, 0), (0, .05), (0, -.05)):          # ~3 miles of slack for the border
        if any(_inside(lo + dx, la + dy, r) for r in rings): return True
    return False


MAX_PER_STATE = 1500        # no state has this many camps in its parks: more means the filter caught something it should not


# ---------------------------------------------------------------- matching
def hav(la1, lo1, la2, lo2):
    p = math.pi / 180
    d = math.sin((la2 - la1) * p / 2) ** 2 + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(d))


STOP = set('state park parks recreation area campground campgrounds camp camping cabin cabins lodge lodges national forest the of at and '
           'rv site sites wildlife management wma sra sp nra lake river creek trail nature preserve resort county memorial historic '
           'historical natural primitive group walk in'.split())


def sig(s): return {w for w in norm(s).split() if w not in STOP and len(w) > 2}


def load_parks(st):
    try:
        d = json.load(open(f'data/parkinfo/US-{st}.json'))['parks']
    except Exception: return []  # noqa: E722
    return [(ref, v[0], v[5], v[6], sig(v[0])) for ref, v in d.items() if isinstance(v, list) and len(v) > 6 and v[5] and v[6]]


def match_pota(c, parks):
    best = None
    own = sig(c['park'])
    me = sig(c['name']) | own
    for ref, nm, la, lo, ps in parks:
        d = hav(c['lat'], c['lon'], la, lo)
        if d <= 2 and (me & ps) and (best is None or d < best[0]): best = (d, ref)
        elif d <= 15 and own and (own & ps) and (best is None or d + 100 < best[0]): best = (d + 100, ref)
    return best[1] if best else ''


def dedupe(cands, fed):
    """Drop what the federal list already has, and repeats. A campground and the cabins beside it stay separate."""
    out = []
    pool = [(norm(f[1]), f[2], f[3]) for f in fed]
    for c in cands:
        n = norm(c['name'])
        if any((c['kind'] == 'c' and hav(c['lat'], c['lon'], la, lo) < 0.19) or (fn == n and hav(c['lat'], c['lon'], la, lo) < 3)
               for fn, la, lo in pool):          # already in data/campfed: 300 m (campgrounds), or the same name within 3 miles
            continue
        dup = next((o for o in out if (o['kind'] == c['kind'] and hav(c['lat'], c['lon'], o['lat'], o['lon']) < 0.19) or
                    (norm(o['name']) == n and hav(c['lat'], c['lon'], o['lat'], o['lon']) < 3)), None)
        if dup:
            dup['url'] = dup['url'] or c['url']; dup['res'] = dup['res'] or c['res']; continue
        out.append(c)
    return out


# ---------------------------------------------------------------- one state
def read_layers(st, lays):
    cands, used = [], []
    for lay in lays:
        if time.time() > DEADLINE: break
        feats = fetch_rows(lay)
        grp = any(g and g in lay['url'] for g in (cfg().get('group', {}).get(st) or []))
        got = group_by_park(lay, feats) if grp else rows_to_camps(lay, feats)
        if not got and feats and not lay.get('raw'):
            lay['raw'] = [{k: str(v)[:60] for k, v in (f.get('attributes') or {}).items() if v not in (None, '')} for f in feats[:3]]
        DIAG.setdefault(st, {}).setdefault('layers', []).append(
            {'url': lay['url'], 'name': lay['name'], 'fields': [n for n, _ in lay['fields']][:14], 'read': len(feats), 'kept': len(got),
             'sample': [c['name'] for c in got[:3]], **({'raw': lay['raw']} if lay.get('raw') else {})})
        if got:
            cands += got; used.append(f"{urllib.parse.urlparse(lay['url']).netloc} · {lay['name']} ({len(got)})")
    return cands, used


def do_state(st):
    t0 = time.time()
    res = {'st': st, 'layers': 0, 'raw': 0, 'camps': [], 'source': '', 'why': ''}
    try:
        lays = discover(st)
        res['layers'] = len(lays)
        cands, used = read_layers(st, lays) if lays else ([], [])
        if not cands and ORG_SEARCH:          # pass 2: the state's own accounts on ArcGIS Online, found by search
            more = expand(org_search(st), per_service=6)
            res['layers'] += len(more)
            c2, u2 = read_layers(st, more)
            cands, used = cands + c2, used + u2
            lays = lays + more
        if not lays:
            rts = DIAG.get(st, {}).get('roots', [])
            res['why'] = ('no official state GIS server known yet' if not rts else
                          'the state GIS server did not answer from GitHub (' + '; '.join(r.get('err', '?') for r in rts if not r['ok'])[:90] + ')' if not any(r['ok'] for r in rts) else
                          'the state GIS servers answered but publish no campground / cabin layer we can read')
            if ORG_SEARCH: res['why'] += '; ArcGIS Online had no camp layer from an account named like the state\'s agencies'
            return res
        n0 = len(cands)
        cands = [c for c in cands if in_state(st, c['lat'], c['lon'])]
        if n0 - len(cands): res['why'] = f'{n0 - len(cands)} outside the state dropped'
        res['raw'] = len(cands)
        if not cands:
            res['why'] = f'{len(lays)} layer(s) looked promising but held no camp / cabin / lodge records'; return res
        try: fed = json.load(open(f'data/campfed/US-{st}.json')).get('camps', [])
        except Exception: fed = []  # noqa: E722
        parks = load_parks(st)
        keep = dedupe(cands, fed)
        if len(keep) > MAX_PER_STATE:
            res['why'] = f'{len(keep)} places is too many to be state-park camps: not written (filter needs a look)'; return res
        for c in keep: c['ref'] = match_pota(c, parks)
        res['camps'] = sorted(keep, key=lambda c: (c['name'].lower(), c['lat']))
        res['source'] = '; '.join(used[:3]) + (f' (+{len(used) - 3} more)' if len(used) > 3 else '')
    except Exception as e:  # noqa: BLE001
        res['why'] = f'stopped early: {type(e).__name__}: {str(e)[:120]}'
    res['secs'] = round(time.time() - t0)
    return res


def row_of(st, c):
    cid = st + '-' + hashlib.sha1(f"{norm(c['name'])}|{c['lat']:.4f}|{c['lon']:.4f}".encode()).hexdigest()[:10]
    return [cid, c['name'], c['lat'], c['lon'], c['kind'], c.get('ref', ''), c['url'], c['res']]


# ---------------------------------------------------------------- the rolling issue (body edits only)
def gh(*a):
    try:
        r = subprocess.run(['gh', 'api', *a], capture_output=True, text=True, timeout=60)
        return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None
    except Exception: return None  # noqa: E722


def update_issue(missing, have, empty):
    if not os.environ.get('GITHUB_ACTIONS') or DRY: return
    body = (f'_Updated {TODAY} by the weekly state-camps bot (.github/scripts/kpc_state_camps.py). This list is edited in place; '
            'the bot never comments here._\n\n'
            f'## Lists written ({len(have)})\n' + (', '.join(sorted(have)) or 'none yet') + '\n\n'
            f'## No official source readable yet ({len(missing)})\n'
            + ('\n'.join(f'- **{s}**: {why}' for s, why in sorted(missing.items())) or 'none') + '\n\n'
            'These need a state reservation-system source (source 2) or a layer found by hand. Nothing is guessed.\n')
    iss = gh(f'repos/{REPO}/issues?labels=state-camps&state=all&per_page=1') or []
    title = f'State park camping: {len(missing)} state(s) without an official source yet'
    if iss:
        gh('-X', 'PATCH', f'repos/{REPO}/issues/{iss[0]["number"]}', '-f', f'title={title}', '-f', f'body={body}', '-f', 'state=open')
    elif missing:
        gh('-X', 'POST', f'repos/{REPO}/issues', '-f', f'title={title}', '-f', f'body={body}', '-f', 'labels[]=state-camps')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    note('State camps', f'{len(STATES)} state(s), {WORKERS} at a time')
    results = {}
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        for r in ex.map(do_state, STATES):
            results[r['st']] = r
            print(f"US-{r['st']}: {len(r['camps'])} kept of {r['raw']} found in {r['layers']} layer(s), {r.get('secs', 0)}s" + (f" · {r['why']}" if r['why'] else ''), flush=True)
    try: idx = json.load(open(OUT / 'index.json'))
    except Exception: idx = {}  # noqa: E722
    states = idx.get('states', {})
    missing, wrote = {}, 0
    for st in STATES:
        r = results[st]
        f = OUT / f'US-{st}.json'
        if r['camps']:
            data = {'state': st, 'updated': TODAY, 'source': r['source'], 'camps': [row_of(st, c) for c in r['camps']]}
            if not DRY: f.write_text(json.dumps(data, separators=(',', ':'), ensure_ascii=False) + '\n', encoding='utf-8')
            states[st] = {'n': len(data['camps']), 'source': r['source'], 'updated': TODAY}; wrote += 1
        elif st in states and f.exists():
            missing[st] = (r['why'] or 'nothing this week') + ' (last week\'s list kept)'
        else:
            states.pop(st, None); missing[st] = r['why'] or 'nothing found'
    for st in list(states):
        if st in STATES: continue
    why = idx.get('none_why', {}) if isinstance(idx, dict) else {}
    why.update(missing)
    for s in list(why):
        if s in states: why.pop(s)
    idx = {'updated': TODAY, 'states': dict(sorted(states.items())),
           'none': sorted(s for s in ALL if s not in states), 'none_why': dict(sorted(why.items()))}
    if not DRY:
        (OUT / 'index.json').write_text(json.dumps(idx, indent=1) + '\n', encoding='utf-8')
        try:
            old = json.loads((OUT / 'layers.json').read_text(encoding='utf-8')).get('states', {})
        except Exception: old = {}  # noqa: E722
        old.update({k: v for k, v in DIAG.items() if k in STATES})
        (OUT / 'layers.json').write_text(json.dumps({'updated': TODAY, 'note': 'What the weekly state-camps bot crawled and read, for tuning. Not for the website.',
                                                     'states': dict(sorted(old.items()))}, separators=(',', ':')) + '\n', encoding='utf-8')
    update_issue({s: idx['none_why'].get(s, 'not read yet') for s in idx['none']}, list(states), None)
    note('State camps done', f'{wrote} written, {len(missing)} without a source. Counts: ' + ' '.join(f"{k}={len(v['camps'])}" for k, v in sorted(results.items())))
    note('State camps: why not', ' | '.join(f"{k}: {v['why'][:70]}" for k, v in sorted(results.items()) if not v['camps'] or v['why']))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        note('State camps stopped early', f'{type(e).__name__}: {e}')
    sys.exit(0)
