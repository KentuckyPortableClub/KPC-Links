#!/usr/bin/env python3
"""ALL-STATES 2-FER BOT (chat 2, Oct 26 2026; Brandon via HQ: 'dead certain before anything is shown').

Finds spots where our maps suggest the boundaries of two or more POTA parks may overlap, in the US (all states but Kentucky, which has its own
hand-checked list in ky-overlaps.geojson) and Canada. HIDDEN: it writes data files only (data/fers/), nothing links to them.

GOLDEN RULES = POTA's own (Activation Location and Access; Brandon Oct 26 5:55 AM: 'use these as a golden rule'):
- The activator and all equipment must be within the park's boundary and on public property; never private property, even
  private land surrounded by the park (= holes in an outline stay holes; inholdings are out).
- Official boundaries come from the official park websites / agencies; POTA's maps are guidelines only (= official outlines).
- A trail or river designated BY ITSELF (not part of a land park with a defined boundary): the station must be on public
  property within 30.5 m (100 ft) of the edge of the trail or river. (Our lines are centre lines, so measuring from the
  centre is the stricter reading; a trail / river that also has a land outline is tested as that land.)
- Multi-park ('two-fer'…): an overlapped area where ALL the parks' boundaries intersect, and the intersection must ENTIRELY
  contain the activator and the station (= our 100-yard spot: stricter, never a chain).
- The park must be open to the public (closures are not tested here: a reviewer checks them).

KPC's extra rules (Brandon, Oct 26):
- OFFICIAL outlines only: the answer keys' joins (data/us-key, data/ca-key), never a park the key marks approximate
  ('reviewed-approx', a lake surface), never a park whose pin is 'well outside' its land. POTA parks only.
- A spot counts only when the overlap holds a spot AT LEAST 50 YARDS ACROSS (Oct 26 2:11 PM; was 100): shrink the overlap 25 yards inward
  and something must remain (no slivers, no parks that only touch). Holes (inholdings) in an outline stay holes.
- TRAILS + RIVERS (official lines, data/trails): POTA's rule = the station entirely within 100 ft of the trail (KPC applies
  the same to rivers). So a stretch AT LEAST 100 YARDS LONG where a station spot inside the other park (5 m in) is within
  100 ft of the line; two lines: their 100-ft zones meet along 100 yards.
- n-fers: a 3-fer is three parks whose boundaries may overlap at the SAME place (never a chain); same for 4.
- Two park numbers joined to the SAME outline record = an answer-key mistake: listed in data/fers/same-outline.json,
  never a spot.
- Oct 27: THE 2-FER RULES FOR THE WHOLE WORLD (notes/mapping.md) are built in (see the block above 'rasters'): agency-land parks
  = owned land only, public + open, ownership step, river edges, water-only + missing-boundary lists, pins never count.

Three passes, each a different way; a spot is a CANDIDATE only when all three agree:
  PASS=1  the saved outlines (PAD-US copy in the boundary cache, saved Canadian outlines, saved trail lines) + the state
          layers at the key's own detail; every park: box test on a grid first (most parks stop there), then a coarse
          overlap, then the 100-yard test at 20 m cells. Writes data/fers/<US-XX|CA-XX>.json.
  PASS=2  only the parks in pass-1 spots, outlines downloaded FRESH from the agencies (PAD-US, the state / provincial
          layers, CPCAD) at ~20 m detail, 10 m cells.
  PASS=3  the same parks, the FINEST shapes the agencies give (~2 m), 5 m cells, + the pin test.
Geometry is done on rasters (numpy + OpenCV): outlines are filled with the even-odd rule, the overlap is measured with a
distance transform (= the 50-yard shrink), spots are its connected pieces.

Never fails (exit 0). MINUTES = time limit; what is done is saved.
"""
import gzip, json, math, os, pathlib, re, sys, time, urllib.parse, urllib.request
import numpy as np
import cv2
sys.path.insert(0, os.path.dirname(__file__))
from kpc_save import save_json

T0 = time.time(); LIMIT = float(os.environ.get('MINUTES') or 300) * 60
PASS = int(os.environ.get('PASS') or 1)
ONLY = set((os.environ.get('STATES') or '').upper().replace(',', ' ').split())
REGION = (os.environ.get('REGION') or 'na').strip().lower()      # 'na' = US + Canada, 'world' = the other countries (Brandon Oct 26: 'do the world')
CELL = {1: 20.0, 2: 10.0, 3: 5.0, 4: 5.0}[PASS]   # 4 = access pins only, for candidates that have none
DET = {1: 0.0005, 2: 0.0002, 3: 0.00002, 4: 0.00002}[PASS]
PREC = {1: 5, 2: 5, 3: 6, 4: 6}[PASS]
# Oct 26 2:11 PM (Brandon, RULE CHANGES): the overlap must hold a spot at least 50 YARDS across (POTA only says the
# overlap must ENTIRELY contain the activator + station; 50 yd still clears map error); 50-100 yd = 'small overlap'.
SHRINK = 22.86            # 25 yards in from every edge = a spot 50 yards across
SMALL_M = 91.44           # under 100 yards across = 'small overlap: tight fit, check carefully'
# Oct 27 4:59 AM (Brandon, rule 4 tiers): 25-50 yards across = a separate VERY TIGHT list (members only, 'could be map error: check
# both official maps on the ground'); under 25 yards = not shown. 'Across' = a circle that size fits: shrink by half from every edge.
TIGHT_M = 45.72           # 50 yards: below this = very tight
TIGHT_SHRINK = 11.43      # 12.5 yards in from every edge = a spot 25 yards across (the smallest kept)
VERY_TIGHT = 'very tight: could be map error: check both official maps on the ground'
STRETCH = 0.0             # trails + rivers: POTA's 100-ft rule only (no KPC 'length along the line')
# POTA's trail rule (Activator Guide, docs.pota.app): 'Your station must be located entirely within 100 feet (30.5m) of the
# trail'; KPC's guide applies the same to river parks (within 100 ft of the water). So a trail / river counts with another
# park where a station spot sits INSIDE that park (5 m in) and within 100 ft of the line (5 m to spare): 25 m.
ZONE = 30.48 - 5.0
STATION_IN = 5.0
MAXPX = 9_000_000         # pixels per raster tile
OUT = pathlib.Path('data/fers'); OUT.mkdir(parents=True, exist_ok=True)
CACHE_US = pathlib.Path(os.environ.get('GEO_CACHE') or 'cache/us')
CACHE_CA = pathlib.Path(os.environ.get('GEO_CACHE_CA') or 'cache/ca')
CACHE_W = pathlib.Path(os.environ.get('GEO_CACHE_W') or 'cache/world')
UA = {'User-Agent': 'KPC 2-fer bot (kentuckyportableclub.github.io)'}
PADUS = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
FWS = 'https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSInterest_Simplified_Authoritative/FeatureServer/0/query'
CPCAD = 'https://maps-cartes.ec.gc.ca/arcgis/rest/services/CWS_SCF/CPCAD/MapServer/0/query'
LOG = []


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', ' ')[:900]), flush=True)
def late(): return time.time() - T0 > LIMIT
def low(x): return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', str(x or '').lower()).split())


GET_ONLY = set()
def get(url, params, tries=3, timeout=120):
    body = urllib.parse.urlencode(params).encode()
    last = None
    for i in range(tries):
        try:
            if url in GET_ONLY or len(body) < 1500:   # Oct 26: the EEA server answers 405 to POST
                req = urllib.request.Request(url + '?' + body.decode(), headers=UA)
            else:
                req = urllib.request.Request(url, data=body, headers=dict(UA, **{'Content-Type': 'application/x-www-form-urlencoded'}))
            j = json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', 'replace'))
            if isinstance(j, dict) and j.get('error'): raise RuntimeError(str(j['error'])[:150])
            return j
        except Exception as e:  # noqa: BLE001
            last = e
            if '405' in str(e): GET_ONLY.add(url)
            time.sleep(2 + 3 * i)
    raise last


# ------------------------------------------------------------------ parks (official only)
def pins():
    P = {}
    for f in pathlib.Path('data/parkinfo').glob('US-*.json'):
        for r, v in json.load(open(f))['parks'].items():
            if v[5] is not None: P[r] = (v[0], v[5], v[6], v[1], v[2], f.stem[3:])
    try:
        for r, v in json.load(open('data/parkinfo/CA.json'))['parks'].items():
            if v[5] is not None and len(v) > 10: P[r] = (v[0], v[5], v[6], v[1], v[2], 'CA-' + v[10])
    except Exception: pass  # noqa: BLE001
    try:   # Kentucky's parks live in kpc-ky-data.json (data/parkinfo/KY.json is the Cayman Islands)
        for x in json.load(open('kpc-ky-data.json')).get('parks') or []:
            if x.get('la') is not None: P[x['c']] = (x.get('n', ''), x['la'], x['lo'], x.get('web', ''), x.get('t', ''), 'KY')
    except Exception: pass  # noqa: BLE001
    for f in pathlib.Path('data/parkinfo').glob('[A-Z][A-Z].json'):
        if f.stem in ('CA', 'US'): continue

        try:
            for r, v in json.load(open(f))['parks'].items():
                if len(v) > 6 and v[5] is not None and v[6] is not None: P[r] = (v[0], v[5], v[6], v[1], v[2], 'W-' + f.stem)
        except Exception: pass  # noqa: BLE001
    return P


WATER = set()
def water_prefixes():
    """state-gis layers that are lake SURFACES (water: 1) give only an approximate park."""
    try:
        sg = json.load(open('data/state-gis.json'))['states']
        L = json.load(open('data/us-key/layers.json'))
        for st, lays in sg.items():
            for l in lays:
                if l.get('water'):
                    u = str(l.get('url') or '').rstrip('/') + '/query'
                    for pre, v in L.items():
                        if v[0] == u: WATER.add(pre)
    except Exception: pass  # noqa: BLE001


SKIPWHY = {}


def official_parks(PIN):
    """{ref: {'st', 'ids': [record ids], 'names': {id: name}}} + why parks were left out."""
    water_prefixes()
    parks, skip = {}, {'approximate': 0, 'pin well outside': 0, 'no outline': 0, 'no pin': 0, 'Kentucky (own list)': 0}
    if REGION == 'ky':   # Oct 26 (Brandon: 'run just KY and see if it matches the guide'): Kentucky's own answer key + official files
        k = json.load(open('data/ky-answer-key.json'))['parks']
        for ref, p in k.items():
            tr = [t for t in p.get('tracts') or [] if t[0] not in ('bdbnf', 'bkpc')]   # the forest's proclamation line and KPC-drawn outlines are not proof
            if not tr: skip['no outline'] += 1; SKIPWHY[ref] = 'no official boundary'; continue
            if ref in KY_NOT_SURE: skip['no outline'] += 1; SKIPWHY[ref] = KY_NOT_SURE[ref]; continue   # ruling Oct 27: a line park, not its land tracts
            if ref not in PIN: skip['no pin'] += 1; continue
            parks[ref] = {'st': 'US-KY', 'ids': [f'{t[0]}|{t[1]}' for t in tr], 'names': {f'{t[0]}|{t[1]}': t[1] for t in tr}}
            if all(t[0] != 'bpad' for t in tr): AGENCY.add(ref)   # Kentucky's agency files (state parks, KDFWR, nature preserves, NPS, FWS)
        # Daniel Boone NF: its KY file is the PROCLAMATION line (private land and towns inside). The Forest Service's own FEE
        # land comes from PAD-US instead (downloaded each run), so only real forest land counts.
        if 'US-4484' in PIN:
            parks['US-4484'] = {'st': 'US-KY', 'ids': ['padus|Daniel Boone National Forest'], 'names': {'padus|Daniel Boone National Forest': 'Daniel Boone National Forest'}}
            skip['no outline'] -= 1
            OWNED['US-4484'] = 'usfs'   # ruling Oct 27: Daniel Boone = Forest Service-OWNED land only (Basic Ownership)
        skip.pop('Kentucky (own list)', None)
        return parks, skip
    if REGION == 'world':
        for f in sorted(pathlib.Path('data/world-key').glob('[A-Z][A-Z].json')):
            for ref, p in json.load(open(f))['parks'].items():
                m = p.get('m') or []
                if not m: skip['no outline'] += 1; SKIPWHY[ref] = 'no official boundary'; continue
                if any('approx' in str(x[3]) for x in m if len(x) > 3): skip['approximate'] += 1; SKIPWHY[ref] = 'approximate outline only (never confirms)'; continue
                if ref not in PIN: skip['no pin'] += 1; continue
                parks[ref] = {'st': 'W-' + f.stem, 'ids': [x[0] for x in m], 'names': {str(i): x[1] for i, x in enumerate(m)}, 'm': m}
        skip.pop('Kentucky (own list)', None)
        return parks, skip
    for f in sorted(pathlib.Path('data/us-key').glob('US-*.json')):
        st = f.stem
        if st == 'US-KY': continue
        for ref, p in json.load(open(f))['parks'].items():
            m = p.get('m') or []
            if not m: skip['no outline'] += 1; SKIPWHY[ref] = 'no official boundary'; continue
            if any('approx' in str(x[3]) for x in m if len(x) > 3) or any(isinstance(x[0], str) and re.match(r'[a-z]+', x[0]).group() in WATER for x in m):
                skip['approximate'] += 1; SKIPWHY[ref] = 'approximate outline only (never confirms)'; continue
            if ref not in PIN: skip['no pin'] += 1; continue
            parks[ref] = {'st': st, 'ids': [x[0] for x in m], 'names': {str(x[0]): x[1] for x in m}}
            if AGENCY_LAND.search(PIN[ref][0]) and not re.search(r'wilderness|wild and scenic', PIN[ref][0], re.I): OWNED[ref] = 'usfs'   # rule 1b
            # rule (c): the agency's OWN layer (state parks / WMA / NPS / FWS / river corridor maps), joined by name -> its
            # outline outranks POTA's pin. PAD-US joins (a national compilation) and BLM planning areas keep the pin test.
            if all(isinstance(x[0], str) and re.match(r'[a-z]+', x[0]).group() not in ('rst', 'hma', 'rma') and str(x[3]).startswith(('name', 'reviewed')) for x in m if len(x) > 3):
                AGENCY.add(ref)
    for f in sorted(pathlib.Path('data/ca-key').glob('CA-*.json')):
        if not re.fullmatch(r'CA-[A-Z]{2}', f.stem): continue
        for ref, p in json.load(open(f))['parks'].items():
            m = p.get('m') or []
            if not m: skip['no outline'] += 1; SKIPWHY[ref] = 'no official boundary'; continue
            if any('approx' in str(x[3]) for x in m if len(x) > 3): skip['approximate'] += 1; SKIPWHY[ref] = 'approximate outline only (never confirms)'; continue
            if ref not in PIN: skip['no pin'] += 1; continue
            parks[ref] = {'st': f.stem, 'ids': [x[0] for x in m], 'names': {str(x[0]): x[1] for x in m}}
            if all(isinstance(x[0], str) and str(x[3]).startswith(('name', 'reviewed')) for x in m if len(x) > 3): AGENCY.add(ref)   # provincial / Parks Canada layer, not CPCAD
    try: skip['Kentucky (own list)'] = len(json.load(open('data/parkinfo/US-KY.json'))['parks'])
    except Exception: skip['Kentucky (own list)'] = 'all (ky-overlaps.geojson)'  # noqa: BLE001
    return parks, skip


def trail_lines():
    """{ref: [[[lon, lat], ...], ...]} official trail / river lines saved by the trails bot."""
    out = {}
    idx = []
    try: idx += json.load(open('data/trails/index-state.json'))
    except Exception: pass  # noqa: BLE001
    # Oct 27 (Kentucky rerun vs the guide): the NATIONAL trails (index.json: national historic / scenic / recreation trails
    # and wild rivers drawn from the agencies' own layers, e.g. Trail of Tears + Lewis and Clark NHT) were never read, so 39
    # of the guide's Kentucky pairs could not be found. They are official when an agency drew them.
    try: idx += [dict(x, official=bool(re.search(r'service|bureau|agency|department|usfs|nps|blm|fws', str(x.get('by')), re.I)))
                 for x in json.load(open('data/trails/index.json'))]
    except Exception: pass  # noqa: BLE001
    for x in idx:
        if not x.get('official') or x['ref'] in out: continue
        f = pathlib.Path(f"data/trails/{x['ref']}.json")
        if not f.exists(): continue
        try: g = json.load(open(f)).get('geometry') or {}
        except Exception: continue  # noqa: BLE001
        c = g.get('coordinates') or []
        ls = c if g.get('type') == 'MultiLineString' else ([c] if g.get('type') == 'LineString' else [])
        ls = [l for l in ls if len(l) > 1]
        if ls: out[x['ref']] = {'lines': ls, 'kind': 'river' if x.get('kind') == 'WSR' or re.search(r'river', str(x.get('type')), re.I) else 'trail'}
    return out


# ------------------------------------------------------------------ outlines
def esri_rings(g):
    if not g: return []
    if g.get('rings'): return [[[p[0], p[1]] for p in r] for r in g['rings'] if len(r) > 2]
    return []


LAYERS_US = json.load(open('data/us-key/layers.json')) if os.path.exists('data/us-key/layers.json') else {}
LAYERS_CA = json.load(open('data/ca-key/layers.json')) if os.path.exists('data/ca-key/layers.json') else {}


LAYERS_W = json.load(open('data/world-key/layers.json')) if os.path.exists('data/world-key/layers.json') else {}


def source_of(rid, canada, src=None):
    """(query url, objectid, name check?) for a key record id."""
    if src is not None:   # the world: only ArcGIS maps can be asked for one record by id
        u = LAYERS_W.get(src)
        if isinstance(rid, int) and u and re.search(r'/\d+$', u.rstrip('/')): return [u.rstrip('/') + '/query'], rid, True
        return [], None, True
    if canada:
        if isinstance(rid, int): return [CPCAD], rid, True
        lab, _, n = str(rid).partition(':')
        if not n.isdigit(): return [], None, True
        urls = [u.rstrip('/') + '/query' for u in LAYERS_CA.get(lab) or [] if re.search(r'/\d+$', u.rstrip('/'))]
        return urls, int(n), True
    if isinstance(rid, int): return [PADUS], rid, False
    m = re.fullmatch(r'([a-z]+)(\d+)', str(rid))
    if not m: return [], None, False
    pre, n = m.group(1), int(m.group(2))
    if pre == 'fws': return [FWS], n, False
    if pre in LAYERS_US: return [LAYERS_US[pre][0]], n, False
    return [], None, False


def name_ok(want, attrs):
    w = low(want)
    if not w: return True
    for v in attrs.values():
        if isinstance(v, str):
            v = low(v)
            if v and (v == w or (len(v) > 3 and (v in w or w in v))): return True
    return False


def download(parks, refs, det, prec):
    """{ref: [group of rings per record]} downloaded from the agencies by object id. A park with a record that could not
    be read is left out (dead certain: half a park is not the park)."""
    want = {}
    for ref in refs:
        ca = parks[ref]['st'].startswith('CA-')
        for i, rid in enumerate(parks[ref]['ids']):
            if 'm' in parks[ref]:
                urls, oid, chk = source_of(rid, False, parks[ref]['m'][i][2]); key = str(i)
            else:
                urls, oid, chk = source_of(rid, ca); key = str(rid)
            if not urls: want.setdefault(('none',), []).append((ref, key, None, chk)); continue
            want.setdefault(tuple(urls), []).append((ref, key, oid, chk))
    got, bad = {}, set()
    for urls, items in want.items():
        if urls == ('none',):
            for ref, *_ in items: bad.add(ref)
            continue
        if late(): break
        oids = sorted({i[2] for i in items})
        found = {}
        for u in urls:
            for k in range(0, len(oids), 100):
                ids = [o for o in oids[k:k + 100] if o not in found]
                if not ids: continue
                try:
                    j = get(u, {'objectIds': ','.join(map(str, ids)), 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326,
                                'maxAllowableOffset': det, 'geometryPrecision': prec, 'f': 'json'})
                except Exception as e:  # noqa: BLE001
                    LOG.append(f'{u.split("/rest/services/")[-1][:60]}: not read ({str(e)[:60]})'); continue
                oidf = j.get('objectIdFieldName') or 'OBJECTID'
                for f in j.get('features') or []:
                    a = f.get('attributes') or {}
                    o = a.get(oidf)
                    if o is None: o = next((v for k2, v in a.items() if k2.lower() in ('objectid', 'fid', 'oid', 'object id')), None)
                    if o is not None: found.setdefault(int(o), []).append((a, esri_rings(f.get('geometry'))))
                time.sleep(.3)
        for ref, rid, oid, chk in items:
            cand = [(a, r) for a, r in (found.get(oid) or []) if r and (not chk or name_ok(parks[ref]['names'].get(rid), a))]
            if not cand: bad.add(ref); continue
            a, r = cand[0]
            use, why = fws_use(a) if FWS in urls else pad_use(a, ref) if PADUS in urls else (True, None)
            if use: got.setdefault(ref, []).append(r)
            else: LEFT.setdefault(ref, []).append(f'{parks[ref]["names"].get(rid) or rid}: {why}')   # rule 2: left out, not 'unreadable'
    for ref in bad: got.pop(ref, None)
    for ref in {i[0] for v in want.values() for i in v} - bad - set(got):
        if ref in LEFT: bad.add(ref)   # every record of this park was left out (all easement / closed): no public land to test
    today = time.strftime('%Y-%m-%d')
    for ref in got: MAPDATE[ref] = f'downloaded {today}'
    return got, bad


SAVED_LEFT = {}


def saved_us(parks):
    """PAD-US records from the boundary cache (the answer key's own saved copy)."""
    by = {}
    for f in CACHE_US.glob('US-*.json.gz'):
        try:
            with gzip.open(f, 'rt', encoding='utf-8') as fh:
                blob = json.load(fh)
                for r in blob.get('recs') or []:
                    if not r.get('_r'): continue
                    use, why = pad_use(r) if isinstance(r.get('OBJECTID'), int) else (True, None)
                    if use: by[r.get('OBJECTID')] = r['_r']
                    else: SAVED_LEFT[r.get('OBJECTID')] = why
        except Exception: pass  # noqa: BLE001
    return by


def saved_ca(parks):
    """{ref: [groups]} from data/canada-bounds (one group per polygon) or the CA-ALL cache (one per record, id + name)."""
    by = {}
    f = CACHE_CA / 'CA-ALL.json.gz'
    if f.exists():
        try:
            with gzip.open(f, 'rt', encoding='utf-8') as fh:
                for r in json.load(fh).get('recs') or []: by.setdefault(str(r.get('oid')), []).append(r)
        except Exception: pass  # noqa: BLE001
    out = {}
    for ref, p in parks.items():
        if not p['st'].startswith('CA-'): continue
        gs = []
        bf = pathlib.Path(f'data/canada-bounds/{ref}.json')
        if bf.exists():
            try:
                g = json.load(open(bf)).get('geometry') or {}
                c = g.get('coordinates') or []
                gs = [poly for poly in c if poly] if g.get('type') == 'MultiPolygon' else ([c] if c else [])
            except Exception: gs = []  # noqa: BLE001
        if not gs:
            ok = True
            for rid in p['ids']:
                r = next((q for q in by.get(str(rid), []) if low(p['names'].get(str(rid))) in (low(q.get('n')), low(q.get('nf')))), None)
                if r and r.get('_r'): gs.append(r['_r'])
                else: ok = False
            if not ok: gs = []
        if gs: out[ref] = gs
    return out


def saved_world(parks):
    """{ref: [groups]} from the world key's saved copy (cache/world/W-CC.json.gz): every joined record must be found
    (same source + id + name, or same source + name near the pin when the record had no id)."""
    out, PINS = {}, pins()
    by_cc = {}
    for ref, p in parks.items(): by_cc.setdefault(p['st'][2:], []).append(ref)
    for cc, refs in by_cc.items():
        f = CACHE_W / f'W-{cc}.json.gz'
        if not f.exists(): continue
        try:
            with gzip.open(f, 'rt', encoding='utf-8') as fh: recs = json.load(fh).get('recs') or []
        except Exception: continue  # noqa: BLE001
        idx = {}
        for r in recs: idx.setdefault((r.get('src'), low(r.get('n'))), []).append(r)
        for ref in refs:
            la, lo = PINS[ref][1], PINS[ref][2]
            gs, ok = [], True
            for x in parks[ref]['m']:
                cand = idx.get((x[2], low(x[1])), [])
                r = next((c for c in cand if x[0] is not None and c.get('id') == x[0]), None) or \
                    next((c for c in cand if x[0] is None and c.get('_bb') and c['_bb'][0] - .6 <= lo <= c['_bb'][2] + .6 and c['_bb'][1] - .6 <= la <= c['_bb'][3] + .6), None)
                if r and r.get('_r'): gs.append(r['_r'])
                else: ok = False
            if ok and gs: out[ref] = gs
    return out


KYF = {'bstate': 'ky-state-parks.geojson', 'bwma': 'ky-hunting-areas.geojson', 'bsnp': 'ky-nature-preserves.geojson', 'bsna': 'ky-natural-areas.geojson',
       'bnps': 'ky-nps.geojson', 'bwild': 'ky-wild-rivers.geojson', 'bwilder': 'ky-wilderness.geojson', 'bfws': 'ky-fws.geojson', 'bpad': 'ky-padus-parks.geojson'}
KYIDX = {}
def ky_geom(parks, refs):
    """Kentucky: the official files the website draws (ky-*.geojson), each joined tract = every feature of that NAME near the
    pin, one group per polygon (holes stay holes)."""
    if not KYIDX:
        for src, fn in KYF.items():
            try: fs = json.load(open(fn)).get('features') or []
            except Exception: continue  # noqa: BLE001
            for f in fs:
                g = f.get('geometry') or {}; c = g.get('coordinates') or []
                polys = c if g.get('type') == 'MultiPolygon' else [c] if g.get('type') == 'Polygon' else []
                nm = str((f.get('properties') or {}).get('NAME') or '')
                if polys: KYIDX.setdefault((src, nm), []).extend(polys)
    PINS = pins()
    out, bad = {}, set()
    for ref in refs:
        la, lo = PINS[ref][1], PINS[ref][2]
        gs = []
        for rid in parks[ref]['ids']:
            src, nm = rid.split('|', 1)
            if src == 'padus':
                if ('padus', nm) not in KYIDX:
                    polys, off = [], 0
                    try:
                        while True:
                            j = get(PADUS, {'where': f"State_Nm='KY' AND Category='Fee' AND Unit_Nm LIKE '{nm}%'", 'outFields': 'OBJECTID',
                                            'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': DET, 'geometryPrecision': PREC,
                                            'resultOffset': off, 'resultRecordCount': 500, 'f': 'json'})
                            fs = j.get('features') or []
                            polys += [esri_rings(f.get('geometry')) for f in fs if esri_rings(f.get('geometry'))]
                            if not fs or not j.get('exceededTransferLimit'): break
                            off += len(fs)
                    except Exception as e:  # noqa: BLE001
                        LOG.append(f'PAD-US {nm}: {str(e)[:60]}')
                    KYIDX[('padus', nm)] = polys
                if KYIDX[('padus', nm)]: gs += KYIDX[('padus', nm)]
                else: bad.add(ref)
                continue
            polys = [pp for pp in KYIDX.get((src, nm), []) if pp and pp[0] and any(abs(q[0] - lo) < .6 and abs(q[1] - la) < .6 for q in pp[0][::max(1, len(pp[0]) // 20)])]
            if polys: gs += polys
            else: bad.add(ref)
        if gs and ref not in bad: out[ref] = gs
    return out, bad


# ------------------------------------------------------------------ THE 2-FER RULES FOR THE WHOLE WORLD (Brandon + HQ, Oct 27)
# notes/mapping.md '2-FER RULES FOR THE WHOLE WORLD'. (1) the park = where its designation legally applies: 'agency-land'
# parks (US national forests + grasslands) = only the land the agency OWNS (Forest Service Basic Ownership), never the outer
# line; PAD-US Proclamation records are never land. (2) public + open: easements (private land), closed areas, tribal and
# military land not open to the public are left out; 'restricted' access = a note. (3)/(14) layered = real, side by side =
# not: the OWNERSHIP STEP (PAD-US Fee + Designation at the spot; Canada CPCAD) decides LAYERED / LINE MISMATCH / NOT SURE.
# (5) line-only rivers from the river EDGE (USGS NHD High Resolution). (6) pins never count. (7) NOT SURE kept out.
# (9) water only = its own list. (10) a permanent no-entry area cannot be the spot. (12) missing boundary = its own list.
# (13) every decided spot carries the date it was checked + the map dates.
RIVER_PAD = 150.0          # pass 1 screen for line-only rivers (no water areas yet): a river up to 300 m wide
CURG = {}                  # the outlines in use (find_spots sets it)
OWNED = {}                 # ref -> 'usfs' = agency-land park: only Forest Service-owned land counts
AGENCY_LAND = re.compile(r'national forests?\b|national grasslands?\b', re.I)
FSBO = 'https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_BasicOwnership_02/MapServer/0'
FSO = {'feat': {}, 'tile': {}, 'f': None}
ACC = {}                   # ref -> notes ('restricted access (PAD-US)')
LEFT = {}                  # ref -> records left out and why (easement, closed, proclamation…)
MAPDATE = {}               # ref -> where / when its outline came from


def fs_owned(box):
    """Forest Service-OWNED land touching box (USDA Basic Ownership, the agency's own layer): one ring group per parcel.
    Fetched in 0.25-degree tiles, each parcel once (a whole forest can be one big multipart feature)."""
    try:
        if FSO['f'] is None:
            info = get(FSBO, {'f': 'json'})
            fl = [x['name'] for x in info.get('fields') or []]
            FSO['f'] = next((x for x in fl if x.lower() == 'ownerclassification'), 'ownerclassification')
            FSO['oid'] = info.get('objectIdField') or next((x for x in fl if x.lower() == 'objectid'), 'objectid')
        out = []
        for i in range(int(math.floor(box[0] / .25)), int(math.floor(box[2] / .25)) + 1):
            for j in range(int(math.floor(box[1] / .25)), int(math.floor(box[3] / .25)) + 1):
                if (i, j) not in FSO['tile']:
                    tb = [i * .25, j * .25, (i + 1) * .25, (j + 1) * .25]
                    ids = get(FSBO + '/query', {'where': f"{FSO['f']} = 'USDA FOREST SERVICE'", 'geometry': ','.join(map(str, tb)),
                                                'geometryType': 'esriGeometryEnvelope', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
                                                'returnIdsOnly': 'true', 'f': 'json'}).get('objectIds') or []
                    new = [o for o in ids if o not in FSO['feat']]
                    for k in range(0, len(new), 10):
                        j2 = get(FSBO + '/query', {'objectIds': ','.join(map(str, new[k:k + 10])), 'outFields': FSO['oid'], 'returnGeometry': 'true', 'outSR': 4326,
                                                    'maxAllowableOffset': DET, 'geometryPrecision': PREC, 'f': 'json'}, timeout=300)
                        oidf = j2.get('objectIdFieldName') or 'objectid'
                        for f in j2.get('features') or []:
                            a = f.get('attributes') or {}
                            o = a.get(oidf, next((v for kk, v in a.items() if kk.lower() == 'objectid'), None))
                            FSO['feat'][o] = esri_rings(f.get('geometry'))
                    FSO['tile'][(i, j)] = ids
                out += [FSO['feat'][o] for o in FSO['tile'][(i, j)] if FSO['feat'].get(o)]
        return out
    except Exception as e:  # noqa: BLE001
        LOG.append(f'Forest Service ownership: {str(e)[:80]}'); return None


def pmask(F, r, G):
    """The park's land in raster F: its outline, and for an agency-land park only the land the agency owns."""
    m = F.area(G[r])
    if r in OWNED and m.any():
        own = fs_owned(F.bounds())
        if own is None: OWNED_FAIL.add(r); return np.zeros_like(m)   # no ownership map = no spot (NOT SURE, not a guess)
        m &= F.area(own)
    return m


OWNED_FAIL = set()
NHD = 'https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer'
NHDL = {}
NHDC = {}


def nhd_water(box, rivers_only=False):
    """USGS NHD High Resolution water areas in box (rivers = NHDArea StreamRiver; + lakes, reservoirs, estuaries)."""
    try:
        if not NHDL:
            for L in get(NHD, {'f': 'json'}).get('layers') or []:
                nm = L.get('name', '').lower()
                if nm == 'nhdarea': NHDL['area'] = L['id']
                if nm == 'nhdwaterbody': NHDL['wb'] = L['id']
        k = (tuple(round(v, 3) for v in box), rivers_only)
        if k in NHDC: return NHDC[k]
        out = []
        for lay, where in (('area', 'FType = 460'), ('wb', 'FType IN (390, 436, 493)')):
            if lay not in NHDL or (rivers_only and lay == 'wb'): continue
            j = get(f'{NHD}/{NHDL[lay]}/query', {'where': where, 'geometry': ','.join(map(str, box)), 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326,
                                                 'spatialRel': 'esriSpatialRelIntersects', 'outFields': 'FType', 'returnGeometry': 'true', 'outSR': 4326,
                                                 'maxAllowableOffset': DET, 'geometryPrecision': PREC, 'f': 'json'}, timeout=180)
            out += [esri_rings(f.get('geometry')) for f in j.get('features') or [] if esri_rings(f.get('geometry'))]
        NHDC[k] = out
        return out
    except Exception as e:  # noqa: BLE001
        LOG.append(f'NHD water: {str(e)[:80]}'); return []


def pad_use(a, ref=None):
    """Rule 2 + 6 on a PAD-US record: (use it?, why not). Proclamation lines and easements are not public land; a closed
    record cannot be the spot; tribal or military land only when PAD-US says open."""
    cat = str(a.get('Category') or '')
    acc = str(a.get('Pub_Access') or '')
    own = str(a.get('Own_Type') or ''); mang = str(a.get('Mang_Name') or '') + ' ' + str(a.get('Own_Name') or '')
    if cat == 'Proclamation': return False, 'proclamation line (not land)'
    if cat == 'Easement': return False, 'easement (private land)'
    if acc == 'XA': return False, 'closed to the public (PAD-US)'
    if (own == 'TRIB' or re.search(r'\bDOD\b|\bARMY\b|\bNAVY\b|\bUSAF\b|\bUSMC\b', mang)) and acc != 'OA': return False, 'tribal / military land not open to the public'
    if acc == 'RA' and ref: ACC.setdefault(ref, set()).add('restricted access (PAD-US): check the agency rules')
    return True, None


FWS_FEE = re.compile(r'^\s*(f|fee)\b', re.I)


def fws_use(a):
    """FWS Interest records: only FEE land (an easement is private land)."""
    for k, v in a.items():
        if re.fullmatch(r'inttype1?|interest_?type', k, re.I) and v not in (None, ''):
            return (True, None) if FWS_FEE.search(str(v)) else (False, f'FWS interest {v} (not fee land)')
    return True, None


def pad_at(lon, lat):
    """PAD-US records (Fee, Designation, Easement, Proclamation) at one point."""
    j = get(PADUS, {'geometry': f'{lon},{lat}', 'geometryType': 'esriGeometryPoint', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
                    'outFields': 'OBJECTID,Unit_Nm,Loc_Nm,Own_Type,Own_Name,Mang_Type,Mang_Name,Category,Des_Tp,Pub_Access', 'returnGeometry': 'false', 'f': 'json'})
    return [f.get('attributes') or {} for f in j.get('features') or []]


def pad_closed(box):
    j = get(PADUS, {'where': "Pub_Access = 'XA' AND Category IN ('Fee','Designation')", 'geometry': ','.join(map(str, box)), 'geometryType': 'esriGeometryEnvelope',
                    'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects', 'outFields': 'Unit_Nm', 'returnGeometry': 'true', 'outSR': 4326,
                    'maxAllowableOffset': DET, 'geometryPrecision': PREC, 'f': 'json'})
    return [esri_rings(f.get('geometry')) for f in j.get('features') or [] if esri_rings(f.get('geometry'))]


def cpcad_at(lon, lat):
    j = get(CPCAD, {'geometry': f'{lon},{lat}', 'geometryType': 'esriGeometryPoint', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
                    'outFields': '*', 'returnGeometry': 'false', 'f': 'json'})
    return [f.get('attributes') or {} for f in j.get('features') or []]


def owner_of_pad(a):
    """An owner key from a PAD-US record: federal land by agency (Forest Service and Park Service land are different owners)."""
    t = str(a.get('Own_Type') or '')
    if t == 'FED': return 'FED:' + (str(a.get('Own_Name') or '') or str(a.get('Mang_Name') or '')).upper()
    return {'STAT': 'STATE', 'LOC': 'LOCAL', 'PVT': 'PRIVATE', 'NGO': 'PRIVATE', 'TRIB': 'TRIBAL', 'JNT': 'JOINT'}.get(t, t or '?')


def owner_of_text(t):
    t = str(t or '')
    if re.search(r'forest service', t, re.I): return 'FED:USFS'
    if re.search(r'corps of engineers', t, re.I): return 'FED:USACE'
    if re.search(r'fish (and|&) wildlife service', t, re.I): return 'FED:FWS'
    if re.search(r'national park service', t, re.I): return 'FED:NPS'
    if re.search(r'tennessee valley', t, re.I): return 'FED:TVA'
    if re.search(r'\barmy\b|military|department of defense', t, re.I): return 'FED:DOD'
    if re.search(r'parks canada|government of canada|environment (and climate change )?canada|federal', t, re.I): return 'FED:CANADA'
    if re.search(r'state|kentucky department|commonwealth|province|provincial|ministry|government of (?!canada)', t, re.I): return 'STATE'
    if re.search(r'county|city|municipal|town|regional district|conservation authority', t, re.I): return 'LOCAL'
    if re.search(r'llc|l\.l\.c|inc\b|lllp|private|company|university of the|land trust|conservancy|group\b', t, re.I): return 'PRIVATE'
    return ''


KYOWN = {}


def ky_owner(ref, parks):
    """Kentucky owner key of a park from its official files: state parks / nature preserves / natural areas = the state;
    NPS / FWS; Daniel Boone = Forest Service-owned; a WMA = the owner on KDFWR's own page (data/ky-wma-owners.json);
    wild river / wilderness corridors = a designation ('' = layered on whoever owns the ground)."""
    if not KYOWN:
        try:
            for n, v in json.load(open('data/ky-wma-owners.json'))['wmas'].items():
                t = v.get('type') or ''
                KYOWN[low(n)] = {'State': 'STATE', 'Local': 'STATE', 'Corps': 'FED:USACE', 'Private': 'PRIVATE', 'University': 'UNIVERSITY'}.get(t) or owner_of_text(v.get('says')) or ''
        except Exception: KYOWN['_'] = ''  # noqa: BLE001
    if ref == 'US-4484': return 'FED:USFS'
    srcs = [str(rid).split('|', 1) for rid in parks[ref]['ids']]
    for src, nm in srcs:
        if src == 'bstate' or src in ('bsnp', 'bsna'): return 'STATE'
        if src == 'bnps': return 'FED:NPS'
        if src == 'bfws': return 'FED:FWS'
        if src == 'bwma':
            if ref in KY_FS_MANAGED: return 'FED:USFS'
            return KYOWN.get(low(nm), '?')
    return ''   # bwild / bwilder: a designation


def park_owner(ref, parks):
    """'' = a designation / management record (layers on someone else's land); '?' = not known; else the owner key."""
    if not (parks.get(ref) or {}).get('ids'): return ''   # a line park (trail / water trail): a designation along the line
    if REGION == 'ky': return ky_owner(ref, parks)
    if ref in OWNED: return 'FED:USFS'
    p = parks.get(ref) or {}
    if p.get('st', '').startswith('CA-'):
        return OWN_CA.get(ref, '?')
    fee, des = OWN.get(ref, (set(), False))
    if fee: return sorted(fee)[0] if len(fee) == 1 else '?'
    return '' if des else '?'


OWN_CA = {}


def ownership_step(s, parks, PIN):
    """Rule 3 + 14: ('ok' | 'drop' | 'not sure', why). LAYERED (one owner under every designation) = real; LINE MISMATCH
    (a park's own land is a different owner than the ground at the spot) = drop; the data cannot tell = NOT SURE."""
    refs = s['refs']
    owners = {r: park_owner(r, parks) for r in refs}
    # Brandon Oct 27 5:21 AM (rule 14 + boundary B-G2): private land by agreement or lease counts only for ITS OWN park number,
    # never toward any park around it: a park on private land never makes a 2-fer
    priv = [r for r, o in owners.items() if o == 'PRIVATE']
    if priv: return 'drop', 'private land (leased / open by agreement) counts only for its own park number: ' + ', '.join(PIN.get(r, [r])[0] for r in priv)
    real = {r: o for r, o in owners.items() if o not in ('', '?')}
    if len(set(real.values())) <= 1 and '?' not in owners.values() and not any(r in OWNED for r in refs):
        return 'ok', 'one owner (or designations on it): layered'
    if REGION == 'world': return 'not sure', 'owners differ; no land register read for this country yet'
    la, lo = s['center']
    try: recs = cpcad_at(lo, la) if refs[0].startswith('CA-') else pad_at(lo, la)
    except Exception as e: return 'not sure', f'ownership map did not answer ({str(e)[:40]})'  # noqa: BLE001
    if refs[0].startswith('CA-'):
        here = {owner_of_text(' '.join(str(v) for k, v in a.items() if re.search(r'owner', k, re.I))) for a in recs} - {''}
    else:
        here = {owner_of_pad(a) for a in recs if a.get('Category') == 'Fee'}
    if len(here) > 1: return 'not sure', 'the ownership map shows two owners at the spot: ' + ', '.join(sorted(here))
    ground = next(iter(here), '')
    if not ground and REGION == 'ky' and 'US-4484' in refs: ground = 'FED:USFS'   # the Daniel Boone mask = Forest Service-owned land
    bad, unk = [], []
    for r in refs:
        o = owners[r]
        if o == '': continue                                             # a designation layers on the ground's owner
        if covered(r, recs, parks, PIN): continue                        # its own record is at the spot (a lease / agreement shows here)
        if o == '?': unk.append(r); continue
        if ground and o != ground: bad.append(f"{PIN.get(r, [r])[0]} is {o.split(':')[-1].lower()} land, the ground here is {ground.split(':')[-1].lower()}")
        if not ground and len(set(real.values())) > 1: bad.append('two owners side by side')
    if bad: return 'drop', 'side by side, not layered: ' + '; '.join(bad[:2])
    if unk: return 'not sure', 'owner not known for ' + ', '.join(PIN.get(r, [r])[0] for r in unk)
    return 'ok', f'layered on {ground.split(":")[-1].lower() or "one owner"} land'


# Kentucky rulings (Brandon + HQ Oct 27; chat 8's KPC_KY2fer_VERDICT_desk.md): decided pairs, applied after the tests
KY_DROP = {('US-1277', 'US-4484'): 'Cumberland Falls is state land beside Forest Service land (ruling Oct 27)',
           ('US-1286', 'US-4484'): 'Natural Bridge is state land beside Forest Service land (ruling Oct 27)',
           ('US-0686', 'US-4484'): 'Big South Fork is Park Service land beside Forest Service land (ruling Oct 27)',
           ('US-3799', 'US-4484'): 'Burchell-Beech is KDFWR-owned (ruling Oct 27)',
           ('US-4484', 'US-7964'): 'W.H. Martin is state nature preserve land (ruling Oct 27)',
           ('US-12083', 'US-4484'): 'University of the Cumberlands WMA is private (ruling Oct 27)'}
KY_NOT_SURE = {'US-10102': 'Pine Mountain State Scenic Trail is a line park: no official trail line yet'}


def retired():
    out = set()
    try: out |= set(json.load(open('data/retired-refs.json')).get('refs', {}))
    except Exception: pass  # noqa: BLE001
    try:
        k = json.load(open('data/ky-retired.json')).get('parks')
        out |= set(k if isinstance(k, list) else (k or {}))
    except Exception: pass  # noqa: BLE001
    return {x if isinstance(x, str) else str(x.get('ref') or x.get('c') or '') for x in out}


def pip_groups(gs, lon, lat):
    for g in gs:
        n = 0
        for ring in g:
            if len(ring) > 2 and cv2.pointPolygonTest(np.asarray(ring, np.float32)[:, :2].reshape(-1, 1, 2), (float(lon), float(lat)), False) >= 0: n += 1
        if n % 2 == 1: return True
    return False


def missing_list(PIN, parks, skip_why, G, LN, today):
    """Rule 12: a park with NO official boundary whose pin sits inside another park's official outline = a possible 2-fer
    we cannot test: 'Missing boundary: check the official map' (its own list, never the main one)."""
    want = (lambda st: st.startswith('W-')) if REGION == 'world' else (lambda st: st == 'KY') if REGION == 'ky' else (lambda st: not st.startswith('W-') and st != 'KY')
    boxes = {r: bbox_groups(g) for r, g in G.items() if bbox_groups(g)}
    grid = {}
    for r, b in boxes.items():
        for i in range(int(b[0] // .5), int(b[2] // .5) + 1):
            for j in range(int(b[1] // .5), int(b[3] // .5) + 1): grid.setdefault((i, j), []).append(r)
    out = []
    RET = retired()
    for ref, v in PIN.items():
        if not want(v[5]) or ref in RET or (ref in G) or (ref in LN): continue
        nm, la, lo = v[0], v[1], v[2]
        ins = [r for r in grid.get((int(lo // .5), int(la // .5)), []) if r != ref and boxes[r][0] <= lo <= boxes[r][2] and boxes[r][1] <= la <= boxes[r][3] and pip_groups(G[r], lo, la)]
        if ins or ref in KY_NOT_SURE:
            out.append({'ref': ref, 'name': nm, 'st': v[5], 'why': KY_NOT_SURE.get(ref) or skip_why.get(ref, 'no official boundary'),
                        'pin inside': [[r, PIN[r][0]] for r in ins], 'note': 'Missing boundary: check the official map', 'checked': today})
    return out


# ------------------------------------------------------------------ rasters
def bbox_groups(gs):
    xs = [p[0] for g in gs for r in g for p in r]; ys = [p[1] for g in gs for r in g for p in r]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


def bbox_lines(ls):
    xs = [p[0] for l in ls for p in l]; ys = [p[1] for l in ls for p in l]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


class Frame:
    """A raster window: x = east metres, y = north metres around (lon0, lat0)."""
    def __init__(self, box, cell, pad):
        self.lat0 = (box[1] + box[3]) / 2; self.lon0 = (box[0] + box[2]) / 2
        self.kx = 111320 * math.cos(math.radians(self.lat0)); self.ky = 110574
        x0, y0 = (box[0] - self.lon0) * self.kx - pad, (box[1] - self.lat0) * self.ky - pad
        x1, y1 = (box[2] - self.lon0) * self.kx + pad, (box[3] - self.lat0) * self.ky + pad
        self.cell = cell; self.x0, self.y1 = x0, y1
        self.W, self.H = max(1, int(math.ceil((x1 - x0) / cell))), max(1, int(math.ceil((y1 - y0) / cell)))

    def px(self, pts):
        a = np.asarray(pts, dtype=np.float64)[:, :2]
        c = ((a[:, 0] - self.lon0) * self.kx - self.x0) / self.cell
        r = (self.y1 - (a[:, 1] - self.lat0) * self.ky) / self.cell
        return np.stack([c, r], axis=1)

    def ll(self, c, r):
        x = self.x0 + (c + .5) * self.cell; y = self.y1 - (r + .5) * self.cell
        return [round(self.lon0 + x / self.kx, 6), round(self.lat0 + y / self.ky, 6)]

    def bounds(self):
        return [self.lon0 + self.x0 / self.kx, self.lat0 + (self.y1 - self.H * self.cell) / self.ky,
                self.lon0 + (self.x0 + self.W * self.cell) / self.kx, self.lat0 + self.y1 / self.ky]

    def area(self, gs):
        """inside ANY record; inside one record by the even-odd rule (holes stay holes)."""
        m = np.zeros((self.H, self.W), np.uint8)
        for g in gs:
            gm = np.zeros_like(m)
            for ring in g:
                t = np.zeros_like(m)
                cv2.fillPoly(t, [np.round(self.px(ring) * 16).astype(np.int32)], 1, lineType=cv2.LINE_8, shift=4)
                gm ^= t
            m |= gm
        return m

    def lines(self, ls, width_m):
        m = np.zeros((self.H, self.W), np.uint8)
        th = max(1, int(round(2 * width_m / self.cell)))
        for l in ls:
            cv2.polylines(m, [np.round(self.px(l) * 16).astype(np.int32)], False, 1, thickness=th, lineType=cv2.LINE_8, shift=4)
        return m


def inter(b1, b2, pad=0.0):
    b = [max(b1[0], b2[0]) - pad, max(b1[1], b2[1]) - pad, min(b1[2], b2[2]) + pad, min(b1[3], b2[3]) + pad]
    return b if b[0] <= b[2] and b[1] <= b[3] else None


def tiles(box, cell, pad):
    """Split a box into raster tiles of at most MAXPX pixels at this cell size."""
    f = Frame(box, cell, pad)
    if f.W * f.H <= MAXPX: return [box]
    side = math.sqrt(MAXPX) * cell
    nx = max(1, int(math.ceil(f.W * cell / side))); ny = max(1, int(math.ceil(f.H * cell / side)))
    dx, dy = (box[2] - box[0]) / nx, (box[3] - box[1]) / ny
    return [[box[0] + i * dx, box[1] + j * dy, box[0] + (i + 1) * dx, box[1] + (j + 1) * dy] for i in range(nx) for j in range(ny)]


def dt(mask, outside=0):
    """Distance to the nearest pixel OUTSIDE (in cells). A one-pixel empty border, so a tile lying wholly inside the overlap
    (a wilderness inside a national forest) measures to the tile edge instead of 'infinity' (Oct 26 pass-2 bug)."""
    m = cv2.copyMakeBorder(mask, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=outside)
    return cv2.distanceTransform(m, cv2.DIST_L2, 5)[1:-1, 1:-1]


def area_spots(G, refs, box):
    """Spots where the boundaries of every park in refs may overlap, holding a 50-yard spot. G[ref] = groups. Coarse look first."""
    # coarse: at most ~1 M pixels over the shared box; parks grown by one pixel so thin-but-real overlaps are not lost
    f = Frame(box, max(CELL, math.sqrt(max(1.0, (box[2] - box[0]) * 111320 * math.cos(math.radians(box[1])) * (box[3] - box[1]) * 110574) / 1e6)), 0)
    k = np.ones((3, 3), np.uint8)
    ov = None
    for r in refs:
        m = cv2.dilate(pmask(f, r, G), k)
        ov = m if ov is None else ov & m
        if not ov.any(): return []
    rows, cols = np.nonzero(ov)
    if f.cell > CELL:   # fine tiles only where the coarse look saw an overlap
        lon = f.lon0 + (f.x0 + (cols + .5) * f.cell) / f.kx
        lat = f.lat0 + (f.y1 - (rows + .5) * f.cell) / f.ky
        fine_box = [lon.min() - f.cell / f.kx, lat.min() - f.cell / f.ky, lon.max() + f.cell / f.kx, lat.max() + f.cell / f.ky]
        mx, my = f.cell / f.kx, f.cell / f.ky
        boxes = [b for b in tiles(fine_box, CELL, 0)
                 if np.any((lon >= b[0] - mx) & (lon <= b[2] + mx) & (lat >= b[1] - my) & (lat <= b[3] + my))] or [fine_box]
    else:
        boxes = [box]
    out = []
    for b in boxes:
        if late(): break
        F = Frame(b, CELL, SHRINK * 3)
        ovf = None
        for r in refs:
            m = pmask(F, r, G); ovf = m if ovf is None else ovf & m
            if not ovf.any(): break
        if ovf is None or not ovf.any(): continue
        dist = dt(ovf) * CELL
        core = (dist >= TIGHT_SHRINK + CELL * (1.0 if PASS == 3 else .5)).astype(np.uint8)   # pass 3 strict, 1-2 a little lenient (screens); 25-yard floor (rule 4)
        if not core.any(): continue
        n, lab = cv2.connectedComponents(ovf, connectivity=8)
        for L in sorted(set(lab[core > 0].tolist())):
            comp = (lab == L)
            d = np.where(comp, dist, 0); r0, c0 = np.unravel_index(np.argmax(d), d.shape)
            cs, _ = cv2.findContours(comp.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            big = max(cs, key=cv2.contourArea)
            ap = cv2.approxPolyDP(big, 1.5, True).reshape(-1, 2)
            if len(ap) > 300: ap = ap[::int(math.ceil(len(ap) / 300))]
            shape = [F.ll(int(c), int(r)) for c, r in ap]
            w = round(float(d.max()) * 2)
            out.append({'refs': sorted(refs), 'kind': 'area', 'center': F.ll(int(c0), int(r0))[::-1],
                        'acres': round(int(comp.sum()) * CELL * CELL / 4046.86, 1), 'wide_m': w, 'shape': shape})
    return merge(out)


def merge(spots):
    """A spot cut by a tile edge comes back as two: one spot when their shapes touch."""
    out = []
    for s in spots:
        b = bbox_lines([s['shape']])
        t = next((o for o in out if o['refs'] == s['refs'] and o['kind'] == s['kind'] and inter(o['_b'], b, 0.0005)), None)
        if t:
            if 'acres' in t or 'acres' in s: t['acres'] = round(t.get('acres', 0) + s.get('acres', 0), 1)   # line spots have none
            if s.get('wide_m', 0) > t.get('wide_m', 0): t['center'], t['wide_m'] = s['center'], s['wide_m']
            if s.get('len_m'): t['len_m'] = round(t.get('len_m', 0) + s['len_m'])
            t['_b'] = [min(t['_b'][0], b[0]), min(t['_b'][1], b[1]), max(t['_b'][2], b[2]), max(t['_b'][3], b[3])]
            t['shape'] = t['shape'] if len(t['shape']) >= len(s['shape']) else s['shape']
        else:
            s['_b'] = b; out.append(s)
    for o in out: o['box'] = [round(v, 5) for v in o.pop('_b')]   # the box of ALL its pieces (the shape is the biggest piece only)
    return out


def sample(l, step):
    out = []
    for a, b in zip(l, l[1:]):
        kx = 111320 * math.cos(math.radians(a[1])); d = math.hypot((b[0] - a[0]) * kx, (b[1] - a[1]) * 110574)
        n = max(1, int(d // step))
        for i in range(n): out.append((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n))
    out.append(tuple(l[-1][:2])); return out


def line_spots(lref, ls, oref, other, other_is_line, box, kind):
    """Stretches of park lref's line(s) at least 100 yards long where a station can stand within 100 ft of the line AND
    inside park oref (5 m in from its line); for two lines: within 100 ft of both (the two 100-ft zones meet)."""
    out = []
    for l in ls:
        pts = [p for p in sample(l, CELL / 2) if box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]]
        if len(pts) < 2: continue
        ins = np.zeros(len(pts), bool)
        for b in tiles(bbox_lines([pts]), CELL, 0):
            idx = [i for i, p in enumerate(pts) if b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3]]
            if not idx: continue
            F = Frame(b, CELL, 120 + (RIVER_PAD if kind == 'river' else 0))
            # Oct 27 rule 5: a LINE-ONLY river counts from the river's EDGE (USGS NHD High Resolution water areas), a trail
            # from its line. Pass 1 has no water areas: a river gets RIVER_PAD extra as a screen; passes 2-3 measure exactly.
            wd = None
            if kind == 'river' and PASS >= 2 and str(lref).startswith('US-'):
                wm = F.area(nhd_water(F.bounds(), rivers_only=True))
                if wm.any(): wd = dt(wm) * CELL      # inside the water: distance to the bank
            if other_is_line: ok = F.lines(other, 2 * ZONE); okd = None
            else:
                spot_ok = (dt(pmask(F, oref, CURG) if oref in CURG else F.area(other)) * CELL >= STATION_IN).astype(np.uint8)
                okd = np.minimum(dt(1 - spot_ok, outside=1), 1e6) * CELL
                ok = (okd <= ZONE + (RIVER_PAD if kind == 'river' and PASS == 1 else 0)).astype(np.uint8)
            P = F.px([pts[i] for i in idx]).astype(int)
            P[:, 0] = P[:, 0].clip(0, F.W - 1); P[:, 1] = P[:, 1].clip(0, F.H - 1)
            if wd is not None and okd is not None:
                ins[idx] = okd[P[:, 1], P[:, 0]] <= ZONE + wd[P[:, 1], P[:, 0]]   # 100 ft from the BANK, the centre line sits wd from it
            else:
                ins[idx] = ok[P[:, 1], P[:, 0]] > 0
        run, best = [], []
        for i, p in enumerate(pts + [None]):
            if p is not None and ins[i]: run.append(p); continue
            if run:
                L = sum(math.hypot((b2[0] - a2[0]) * 111320 * math.cos(math.radians(a2[1])), (b2[1] - a2[1]) * 110574) for a2, b2 in zip(run, run[1:]))
                if L >= STRETCH:
                    st = run[::max(1, len(run) // 200)]
                    out.append({'refs': sorted([lref, oref]), 'kind': kind, 'center': [round(run[len(run) // 2][1], 6), round(run[len(run) // 2][0], 6)],
                                'len_m': round(L), 'shape': [[round(q[0], 6), round(q[1], 6)] for q in st]})
            run = []
    return merge(out)


# ------------------------------------------------------------------ the passes
def grid_pairs(boxes):
    """Pairs whose boxes touch, found on a 0.5-degree grid (never every pair)."""
    cells = {}
    for ref, b in boxes.items():
        for i in range(int(math.floor(b[0] / .5)), int(math.floor(b[2] / .5)) + 1):
            for j in range(int(math.floor(b[1] / .5)), int(math.floor(b[3] / .5)) + 1):
                cells.setdefault((i, j), []).append(ref)
    pairs = set()
    for refs in cells.values():
        if len(refs) > 1:
            for a in range(len(refs)):
                ba = boxes[refs[a]]
                for c in range(a + 1, len(refs)):
                    if inter(ba, boxes[refs[c]]): pairs.add(tuple(sorted((refs[a], refs[c]))))
    return pairs


TESTED = set()
def find_spots(G, LN, pairs, counts):
    CURG.clear(); CURG.update(G)
    spots = []
    for a, b in sorted(pairs):
        if late(): counts['stopped for time'] = True; break
        counts['pairs tested'] += 1
        TESTED.add((a, b))
        ba = bbox_groups(G[a]) if a in G else bbox_lines(LN[a]['lines'])
        bb = bbox_groups(G[b]) if b in G else bbox_lines(LN[b]['lines'])
        box = inter(ba, bb, 0.0008)
        if not box or not all(math.isfinite(v) for v in box): continue
        if box[2] - box[0] > 40 or box[3] - box[1] > 40: LOG.append(f'{a} + {b}: shared box too big (an outline crossing the date line?)'); continue
        try:
            if a in G and b in G: got = area_spots(G, [a, b], box)
            else:
                got = []
                for l_ref, o_ref in ((a, b), (b, a)):
                    if l_ref in LN and l_ref not in G:
                        if o_ref in G: got += line_spots(l_ref, LN[l_ref]['lines'], o_ref, G[o_ref], False, box, LN[l_ref]['kind'])
                        elif o_ref in LN: got += line_spots(l_ref, LN[l_ref]['lines'], o_ref, LN[o_ref]['lines'], True, box, LN[l_ref]['kind']); break
            spots += got
        except Exception as e:  # noqa: BLE001
            LOG.append(f'{a} + {b}: {str(e)[:80]}')
    # n-fers: a third park whose boundary may overlap the SAME place as an area spot (50 yards across, all three)
    nb = {}
    for a, b in pairs: nb.setdefault(a, set()).add(b); nb.setdefault(b, set()).add(a)
    level = [s for s in spots if s['kind'] == 'area']
    for n in (3, 4):
        nxt = []
        for s in level:
            if late(): break
            others = set.intersection(*[nb.get(r, set()) for r in s['refs']]) - set(s['refs'])
            sb = bbox_lines([s['shape']])
            for c in sorted(others):
                if c not in G or any(x['refs'] == sorted(s['refs'] + [c]) for x in nxt): continue
                box = inter(sb, bbox_groups(G[c]), 0.0008)
                if not box: continue
                try: nxt += area_spots(G, s['refs'] + [c], [box[0] - .001, box[1] - .001, box[2] + .001, box[3] + .001])
                except Exception as e: LOG.append(f"{'+'.join(s['refs'])} + {c}: {str(e)[:60]}")  # noqa: BLE001
        spots += nxt; level = nxt
    return spots


def same_outline(parks):
    seen, out = {}, []
    for ref, p in parks.items():
        for i, rid in enumerate(p['ids']):
            if rid is None: continue
            k = (p['m'][i][2], str(rid)) if 'm' in p else (p['st'][:2], str(rid))
            if k in seen and seen[k] != ref: out.append({'refs': sorted([seen[k], ref]), 'record': str(rid), 'name': p['names'].get(str(i) if 'm' in p else str(rid))})
            else: seen[k] = ref
    return out


AGENCY = set()
WILDRIVER = re.compile(r'wild (and|&) scenic|wild river|scenic river|recreational river', re.I)


def pin_inside(ref, PIN, G, LN):
    nm, la, lo = PIN[ref][0], PIN[ref][1], PIN[ref][2]
    # Brandon Oct 26 2 PM: 'the wild rivers, I have to side with the wild river boundaries being correct and POTA wrong':
    # a river corridor's official boundary wins over POTA's pin (pins sit at a road or bridge outside the corridor)
    if WILDRIVER.search(f'{nm} {PIN[ref][4]}'): return True
    if ref in AGENCY: return True   # rule (c) Oct 26 2:11 PM: the agency's own boundary outranks POTA's pin
    d = .004
    b = [lo - d, la - d, lo + d, la + d]
    F = Frame(b, CELL, 0)
    c, r = F.px([[lo, la]])[0].astype(int)
    if ref in G:
        m = pmask(F, ref, G)
        return bool(m[min(max(r, 0), F.H - 1), min(max(c, 0), F.W - 1)])
    if ref in LN: return True   # a trail / river park has no 'inside'; its pin is often at a trailhead or office far away
    return False


TIGER = 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Transportation/MapServer'
TLAY = {}
def tiger_layers():
    if not TLAY:
        try:
            for L in get(TIGER, {'f': 'json'}).get('layers') or []:
                nm = L.get('name', '')
                for k in ('Primary Roads', 'Secondary Roads', 'Local Roads'):
                    if nm.strip() == k and k not in TLAY: TLAY[k] = L['id']
        except Exception as e: LOG.append(f'TIGERweb: {str(e)[:60]}')  # noqa: BLE001
    return TLAY


def roads_near(box):
    """Public roads (Census TIGER: primary, secondary, local streets; never private / 4WD / service roads) and public
    paths (bike paths, bridle paths) in a box: [(kind, name, [[lon, lat]...])]."""
    out = []
    for k, lid in tiger_layers().items():
        where = "MTFCC IN ('S1100','S1200','S1400','S1820','S1830')" if k == 'Local Roads' else '1=1'
        try:
            j = get(f'{TIGER}/{lid}/query', {'where': where, 'geometry': ','.join(map(str, box)), 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326,
                                             'spatialRel': 'esriSpatialRelIntersects', 'outFields': 'NAME,MTFCC', 'returnGeometry': 'true', 'outSR': 4326,
                                             'maxAllowableOffset': 0.00005, 'f': 'json'})
        except Exception as e:  # noqa: BLE001
            LOG.append(f'TIGER {k}: {str(e)[:60]}'); continue
        for f in j.get('features') or []:
            a = f.get('attributes') or {}
            kind = 'trail' if a.get('MTFCC') in ('S1820', 'S1830') else 'road'
            for pth in (f.get('geometry') or {}).get('paths') or []:
                if len(pth) > 1: out.append((kind, a.get('NAME') or ('path' if kind == 'trail' else 'public road'), pth))
    return out


def access_points(refs, st_of):
    pts = []
    for ref in refs:
        st = st_of(ref)
        try: pts += [(q[0], q[1], q[2]) for q in (json.load(open(f'data/access/{st}.json'))['parks'].get(ref) or [])]
        except Exception: pass  # noqa: BLE001
    if st_of(refs[0]) == 'US-KY':
        try:
            for x in json.load(open('kpc-ky-data.json'))['parks']:
                if x['c'] in refs: pts += [(q[0], q[1], q[2]) for q in x.get('ap') or []]
        except Exception: pass  # noqa: BLE001
    return pts


def access_pin(s, G, LN, st_of):
    """Brandon Oct 26: 'drop a pin closest to the easiest public access (a public road, parking, trail)'. The pin is the
    point INSIDE the overlap (5 m in from every line; for a trail / river within 100 ft of it) that is nearest, as the
    crow flies, to a public road, an official parking / access point or a public path."""
    sb = sbox(s)
    pad = .015
    box = [sb[0] - pad, sb[1] - pad, sb[2] + pad, sb[3] + pad]
    cell = 5.0
    F = Frame(box, cell, 0)
    while F.W * F.H > MAXPX: cell *= 1.5; F = Frame(box, cell, 0)
    ok = None
    areas = [r for r in s['refs'] if r in G]
    for r in areas:
        m = (dt(pmask(F, r, G)) * cell >= STATION_IN).astype(np.uint8)
        ok = m if ok is None else ok & m
    for r in s['refs']:
        if r in LN and r not in G:
            z = (dt(1 - F.lines(LN[r]['lines'], 1), outside=1) * cell <= ZONE).astype(np.uint8)
            ok = z if ok is None else ok & z
    if ok is None or not ok.any(): return None
    feats = {'road': np.zeros_like(ok), 'parking / access point': np.zeros_like(ok), 'trail': np.zeros_like(ok)}
    rds = roads_near(box) if s['refs'][0].startswith('US-') else []
    for kind, nm, pth in rds:
        cv2.polylines(feats[kind], [np.round(F.px(pth) * 16).astype(np.int32)], False, 1, thickness=1, lineType=cv2.LINE_8, shift=4)
    aps = access_points(s['refs'], st_of)
    for la, lo, lab in aps:
        c, r = F.px([[lo, la]])[0].astype(int)
        if 0 <= c < F.W and 0 <= r < F.H: cv2.circle(feats['parking / access point'], (int(c), int(r)), 1, 1, -1)
    best = None
    for kind, fm in feats.items():
        if not fm.any(): continue
        d = dt(1 - fm, outside=1) * cell
        d = np.where(ok > 0, d, np.inf)
        i = np.unravel_index(np.argmin(d), d.shape)
        if np.isfinite(d[i]) and (best is None or d[i] < best[0]): best = (float(d[i]), kind, i)
    if not best:
        return {'at': s['center'], 'from': 'none', 'note': 'no public road, parking or path within about 1.5 km: the pin is the middle of the spot'}
    dist, kind, (r, c) = best
    lon, lat = F.ll(int(c), int(r))
    name = ''
    if kind in ('road', 'trail'):
        near = min(((min(math.hypot((q[0] - lon) * F.kx, (q[1] - lat) * F.ky) for q in pth), nm) for k, nm, pth in rds if k == kind), default=(0, ''))
        name = near[1]
    else:
        near = min(((math.hypot((q[1] - lon) * F.kx, (q[0] - lat) * F.ky), q[2]) for q in aps), default=(0, ''))
        name = near[1]
    return {'at': [round(lat, 6), round(lon, 6)], 'from': kind, 'name': str(name)[:80], 'walk_m': round(dist),
            'note': 'closest spot inside every park to that public access, straight line; check the road / lot is open and public'}


def nearest_access(spot, st_of):
    best = None
    la, lo = spot['center']
    for ref in spot['refs']:
        st = st_of(ref)
        f = pathlib.Path(f'data/access/{st}.json')
        try: pts = json.load(open(f))['parks'].get(ref) or []
        except Exception: continue  # noqa: BLE001
        for q in pts:
            d = math.hypot((q[1] - lo) * 111320 * math.cos(math.radians(la)), (q[0] - la) * 110574)
            if best is None or d < best[4]: best = [q[0], q[1], q[2], ref, round(d)]
    return best


FILES = r'W-[A-Z]{2}' if REGION == 'world' else r'US-KY' if REGION == 'ky' else r'(?!US-KY)(US|CA)-[A-Z]{2}'
OWN = {}
FEDDES = {'wsrc', 'akht', 'wld', 'wsa', 'wbl', 'nca', 'hma', 'rst', 'rma'}   # federal DESIGNATIONS / planning areas, not ownership


def owners(parks):
    """Rule (e), Brandon Oct 26 2:11 PM: {ref: (fee owners {'FED','STAT','LOC'…}, has a designation / management record)}.
    PAD-US records say it (Own_Type + Category); a state layer of kind 'park' = state-owned; FWS = federal; federal
    designation layers (wilderness, wild river corridors, NCAs, BLM areas) and WMA / preserve / river layers = designation
    or management (never flagged). Kentucky: state parks = state, NPS / FWS / Daniel Boone fee land = federal."""
    pad = {}
    for f in CACHE_US.glob('US-*.json.gz'):
        try:
            with gzip.open(f, 'rt', encoding='utf-8') as fh:
                for r in json.load(fh).get('recs') or []: pad[r.get('OBJECTID')] = (r.get('Own_Type') or '', r.get('Category') or '')
        except Exception: pass  # noqa: BLE001
    kind = {}
    try:
        for v in json.load(open('data/state-gis.json'))['states'].values():
            for e in v: kind[str(e.get('url') or '').rstrip('/') + '/query'] = e.get('kind')
    except Exception: pass  # noqa: BLE001
    for ref, p in parks.items():
        fee, des = set(), False
        for rid in p.get('ids') or []:
            if REGION == 'ky':
                src = str(rid).split('|')[0]
                # Oct 27: owners by AGENCY (NPS land and Forest Service land cannot be the same ground either: Big South Fork x DBNF)
                if src == 'bstate': fee.add('STAT')
                elif src == 'bnps': fee.add('FED:NPS')
                elif src == 'bfws': fee.add('FED:FWS')
                elif src == 'padus': fee.add('FED:USFS')
                elif ref in KY_FS_MANAGED: fee.add('FED:USFS')   # Oct 27: KDFWR says the Forest Service OWNS these WMAs
                else: des = True
            elif isinstance(rid, int) and not p['st'].startswith(('CA-', 'W-')):
                o, c = pad.get(rid, ('', ''))
                if c == 'Fee' and o: fee.add('STAT' if o in ('STAT', 'SDNR', 'SPR', 'SFW', 'SLB') else 'PRIVATE' if o in ('PVT', 'NGO') else o)
                else: des = True
            else:
                m = re.fullmatch(r'([a-z]+)\d+', str(rid)); pre = m.group(1) if m else ''
                if pre == 'fws': fee.add('FED')
                elif pre in FEDDES or not pre: des = True
                elif kind.get((LAYERS_US.get(pre) or [''])[0]) == 'park' and 'National Park Service' not in str((LAYERS_US.get(pre) or ['', '', ''])[2]): fee.add('STAT')
                else: des = True
        OWN[ref] = (fee, des)


# Oct 27 (HQ ruling 2 + chat 8's verdict file, from KDFWR's own pages / data/ky-wma-owners.json): Forest Service-OWNED WMAs
# managed by KDFWR: Redbird, Beaver Creek, Cane Creek, Mill Creek, Pioneer Weapons, Twin Knobs, Zilpo
KY_FS_MANAGED = {'US-10159', 'US-3794', 'US-10121', 'US-10146', 'US-10158', 'US-10170', 'US-10171'}


def two_owners(refs, parks):
    """Two parks whose land is OWNED by different governments (federal fee land + a state-owned park) cannot really share
    ground: flag 'likely map mistake' unless either one is a designation, lease or management record."""
    if not OWN: owners(parks)
    got = [OWN.get(r) for r in refs]
    # Oct 27: a designation only exempts a park that is NOTHING BUT a designation / management record (a WMA on forest land).
    # A park with fee land of its own keeps its owner even when a nature preserve is dedicated inside it (Cumberland Falls,
    # Natural Bridge: state park + state nature preserve = state land; they were never flagged)
    if any(g is None or not g[0] for g in got): return False
    return any(not (a[0] & b[0]) for i, a in enumerate(got) for b in got[i + 1:])


def file_of(st): return OUT / f'{st}.json'


def sbox(s): return s.get('box') or bbox_lines([s['shape']])


def slim(spots):
    """Storage (Oct 26: France alone gave 68,000 spots = 94 MB): the world keeps each spot's box, not its outline; North
    America keeps an outline of at most 80 points."""
    for s in spots:
        if s.get('kind') == 'area' and s.get('wide_m'):
            s.pop('small', None); s.pop('tier', None)
            if s['wide_m'] < TIGHT_M: s['tier'] = VERY_TIGHT
            elif s['wide_m'] < SMALL_M: s['small'] = 'small overlap: tight fit, check carefully'
        if s.get('shape'):
            if not s.get('box'): s['box'] = [round(v, 5) for v in bbox_lines([s['shape']])]
            if REGION == 'world': s.pop('shape', None)
            elif len(s['shape']) > 80: s['shape'] = s['shape'][::int(math.ceil(len(s['shape']) / 80))]
    return spots


def key_of(s): return '+'.join(s['refs']) + '@' + s['kind']


def land_check(s, G):
    """Rules 9 + 10 on a US area spot: 'ok', 'water' (the 50-yard patch exists only on a lake / river surface), 'closed'
    (it exists only inside a PAD-US closed area)."""
    sb = sbox(s); pad = .002
    box = [sb[0] - pad, sb[1] - pad, sb[2] + pad, sb[3] + pad]
    cell = CELL
    F = Frame(box, cell, SHRINK * 2)
    while F.W * F.H > MAXPX: cell *= 1.5; F = Frame(box, cell, SHRINK * 2)
    ov = None
    for r in s['refs']:
        if r not in G: continue
        m = pmask(F, r, G); ov = m if ov is None else ov & m
    if ov is None or not ov.any(): return 'ok'
    need = TIGHT_SHRINK + cell
    try: closed = F.area(pad_closed(F.bounds()))
    except Exception as e: LOG.append(f'closed areas: {str(e)[:60]}'); closed = np.zeros_like(ov)  # noqa: BLE001
    open_ = ov & (1 - closed)
    if not (dt(open_) * cell >= need).any(): return 'closed' if closed.any() else 'ok'
    water = F.area(nhd_water(F.bounds()))
    if not water.any(): return 'ok'
    return 'ok' if (dt(open_ & (1 - water)) * cell >= need).any() else 'water'


def covered(r, recs, parks, PIN):
    """Does a record at the spot belong to park r (its own joined record, or the same name)?"""
    ids = {str(i) for i in (parks.get(r) or {}).get('ids') or []}
    names = [PIN[r][0]] + list((parks.get(r) or {}).get('names', {}).values())
    for a in recs:
        if str(a.get('OBJECTID')) in ids: return True
        nm = {k: v for k, v in a.items() if re.search(r'nm$|name', k, re.I) and not re.search(r'own|mang', k, re.I)}
        if any(name_ok(n, nm) for n in names if n): return True
    return False


def decide(s, parks, G, LN, PIN, today, saved_only, st_of):
    """Pass 3: the rules decide what a spot that passed all three geometry passes is."""
    refs = s['refs']
    s['checked'] = today
    s['map_dates'] = {r: MAPDATE.get(r) or ('saved copy' if r in saved_only else 'official line (trails bot)' if r in LN else 'Kentucky official file' if REGION == 'ky' else 'saved copy') for r in refs}
    s['pins_inside'] = {r: pin_inside(r, PIN, G, LN) for r in refs}   # information only: pins never count (rule 6)
    if any(r in saved_only for r in refs): s['fresh'] = 'saved copy only for ' + ', '.join(r for r in refs if r in saved_only)
    notes = sorted({n for r in refs for n in ACC.get(r, ())})
    if notes: s['notes'] = notes
    for k in ('list', 'ownership'): s.pop(k, None)
    pk = tuple(sorted(refs))
    if REGION == 'ky':
        for a in range(len(refs)):
            for b in range(a + 1, len(refs)):
                if (refs[a], refs[b]) in KY_DROP: s['status'] = 'dropped: ' + KY_DROP[(refs[a], refs[b])]; return
    if any(r in OWNED_FAIL for r in refs): s['status'] = 'not sure: the Forest Service ownership map did not answer'; return
    if s['kind'] == 'area' and refs[0].startswith('US-'):
        try: lc = land_check(s, G)
        except Exception as e: lc = 'ok'; LOG.append(f"land check {s['id']}: {str(e)[:60]}")  # noqa: BLE001
        if lc == 'water': s['status'] = 'water only: boat or kayak'; s['list'] = '🚤 Water only: boat or kayak'; return
        if lc == 'closed': s['status'] = 'dropped: only inside an area closed to the public (no entry)'; return
    v, why = ownership_step(s, parks, PIN)
    s['ownership'] = why
    if v == 'drop': s['status'] = 'dropped: ' + why; return
    if v == 'not sure': s['status'] = 'not sure: ' + why; return
    s['status'] = 'candidate' if not s.get('fresh') else 'candidate (saved outline only)'
    if s['kind'] == 'area' and (s.get('wide_m') or 0) < TIGHT_M:
        s['status'] = VERY_TIGHT; s['list'] = 'Very tight (members only)'   # rule 4: its own list, never the main one
    s['access'] = nearest_access(s, st_of)
    try: s['access_pin'] = access_pin(s, G, LN, st_of)
    except Exception as e: LOG.append(f"pin {s['id']}: {str(e)[:60]}")  # noqa: BLE001
    s['maps'] = [[r, PIN[r][3]] for r in refs]
    s['names'] = {r: PIN[r][0] for r in refs}


def ca_owners(parks):
    """Canada (rule 14): each park's owner from its saved CPCAD / provincial record (owner text)."""
    f = CACHE_CA / 'CA-ALL.json.gz'
    if not f.exists(): return
    try:
        with gzip.open(f, 'rt', encoding='utf-8') as fh:
            by = {str(r.get('oid')): r for r in json.load(fh).get('recs') or []}
    except Exception: return  # noqa: BLE001
    for ref, p in parks.items():
        if not p['st'].startswith('CA-'): continue
        os_ = {owner_of_text(by.get(str(i), {}).get('ow')) for i in p['ids']} - {''}
        OWN_CA[ref] = next(iter(os_)) if len(os_) == 1 else '?'




def main():
    PIN = pins()
    parks, skip = official_parks(PIN)
    RET = retired()   # rule 13: retired POTA numbers drop out
    parks = {r: p for r, p in parks.items() if r not in RET}
    LN = {r: v for r, v in trail_lines().items() if r not in RET}
    owners(parks); ca_owners(parks)
    for ref in LN:
        # Oct 27: a trail that CROSSES Kentucky counts in the Kentucky run even when POTA files it under another state
        # (Trail of Tears, Lewis and Clark NHT): the Kentucky region takes any line whose box touches the state
        kyl = REGION == 'ky' and ref in PIN and not PIN[ref][5].startswith(('W-', 'CA-')) and (lambda b: b[0] < -81.96 and b[2] > -89.6 and b[1] < 39.15 and b[3] > 36.49)(bbox_lines(LN[ref]['lines']))
        if ref not in parks and ref in PIN and (REGION == 'world') == PIN[ref][5].startswith('W-') and (kyl or (REGION == 'ky') == (PIN[ref][5] == 'KY')):
            st = 'KY' if kyl else PIN[ref][5]
            parks[ref] = {'st': st if st.startswith('CA-') else 'US-' + st, 'ids': [], 'names': {}}
    st_of = lambda r: parks[r]['st'] if r in parks else ''
    if ONLY: parks = {r: p for r, p in parks.items() if p['st'] in ONLY or p['st'][3:] in ONLY}
    counts = {'pass': PASS, 'cell_m': CELL, 'official parks': len(parks), 'left out': skip, 'pairs tested': 0, 'with official lines': sum(1 for r in LN if r in parks)}
    today = time.strftime('%Y-%m-%d')
    old = {}
    for f in OUT.glob('*-*.json'):
        if re.fullmatch(FILES, f.stem):
            try: old[f.stem] = json.load(open(f))
            except Exception: pass  # noqa: BLE001

    if PASS == 4:   # access pins for candidates that have none yet (Oct 26: added after pass 3 had run)
        files = {st: d for st, d in old.items() if (not ONLY or st in ONLY or st[3:] in ONLY)}
        cand = [s for d in files.values() for s in d.get('spots', []) if str(s.get('status', '')).startswith('candidate') and not s.get('access_pin')]
        refs = sorted({r for s in cand for r in s['refs'] if r in parks and parks[r]['ids']})
        if REGION == 'ky': G, bad = ky_geom(parks, refs)
        else: G, bad = download(parks, refs, DET, PREC)
        n = 0
        for s in cand:
            if late(): break
            if any(r not in G and r not in LN for r in s['refs']): continue
            if not s.get('access'): s['access'] = nearest_access(s, st_of)
            try: s['access_pin'] = access_pin(s, G, LN, st_of); n += 1
            except Exception as e: LOG.append(f"pin {s['id']}: {str(e)[:60]}")  # noqa: BLE001
        for st, d in files.items():
            d['about'] = ABOUT
            save_json(file_of(st), d, indent=1 if REGION != 'world' else None)
        counts.update({'candidates without a pin': len(cand), 'pins placed': n})
    elif PASS == 1:
        same = same_outline(parks)
        save_json(OUT / {'world': 'same-outline-world.json', 'ky': 'same-outline-ky.json'}.get(REGION, 'same-outline.json'), {'about': 'Two park numbers joined to the SAME outline record: an answer-key mistake to fix, never a 2-fer.', 'pairs': same}, indent=1)
        skip_pairs = {tuple(x['refs']) for x in same}
        # saved outlines: PAD-US from the cache, Canada from the saved files; the rest from the state layers at the key's detail
        pad = saved_us(parks) if REGION == 'na' else {}
        G, need = {}, []
        for ref, p in parks.items():
            if p['st'].startswith(('CA-', 'W-')) or not p['ids'] or REGION == 'ky': continue
            if all(isinstance(i, int) and (i in pad or i in SAVED_LEFT) for i in p['ids']):
                for i in p['ids']:
                    if i in SAVED_LEFT: LEFT.setdefault(ref, []).append(f"{p['names'].get(str(i)) or i}: {SAVED_LEFT[i]}")
                gs = [pad[i] for i in p['ids'] if i in pad]
                if gs: G[ref] = gs; MAPDATE[ref] = 'saved PAD-US copy'
            else: need.append(ref)
        if REGION == 'ky':
            kg, kb = ky_geom(parks, [r for r in parks if parks[r]['ids']]); G.update(kg); need = []
        else: G.update(saved_world(parks) if REGION == 'world' else saved_ca(parks))
        notice('2-fer bot', f"pass 1: {len(G)} parks from saved outlines, {len(need)} to download, {len(LN)} official lines")
        got, bad = download(parks, need, DET, PREC)
        G.update(got)
        counts['parks whose outline could not be read'] = len(bad)
        boxes = {r: bbox_groups(g) for r, g in G.items() if bbox_groups(g)}
        for r in LN:
            if r in parks and r not in boxes:
                b = bbox_lines(LN[r]['lines']); boxes[r] = [b[0] - .0005, b[1] - .0005, b[2] + .0005, b[3] + .0005]   # the 100-ft zone
        pairs = grid_pairs(boxes) - skip_pairs
        touched = {r for p in pairs for r in p}
        counts['parks done by the box test'] = len(boxes) - len(touched)
        counts['pairs whose boxes touch'] = len(pairs)
        spots = find_spots(G, LN, pairs, counts)
        try:   # rule 12: parks with no official boundary whose pin sits inside another park = 'Missing boundary' list
            miss = missing_list(PIN, parks, SKIPWHY, G, LN, today)
            save_json(OUT / f'missing-{REGION}.json', {'about': "Missing boundary: check the official map. A park with no official boundary (or only an approximate one) whose POTA pin sits inside another park's official outline. Never in the main list; members first.", 'parks': miss}, indent=1)
            counts['missing boundary'] = len(miss)
        except Exception as e: LOG.append(f'missing list: {str(e)[:80]}')  # noqa: BLE001
        if REGION == 'ky':   # Oct 27: a trail that crosses Kentucky brings pairs in other states; keep only spots IN Kentucky
            try:
                KYC = [c['r'] for c in json.load(open('kpc-ky-counties.json'))]
                spots = [s for s in spots if pip_groups(KYC, s['center'][1], s['center'][0])]
            except Exception as e: LOG.append(f'Kentucky outline: {str(e)[:60]}')  # noqa: BLE001
        by = {}
        for s in spots:
            s.update({'id': key_of(s) + '@%.3f,%.3f' % tuple(s['center']), 'passes': [1, 0, 0], 'status': 'pass 1', 'found': today})
            by.setdefault(st_of(s['refs'][0]), []).append(s)
        if REGION == 'ky':
            # Brandon Oct 26 2:03 PM ('Fort Heiman and Donelson, it is what it is: both'): two park numbers on ONE official outline
            # (the NPS folded Fort Heiman into Fort Donelson National Battlefield) are both valid there: a 'same land' spot on
            # the piece nearest the second park's pin. (Outside Kentucky the same-outline list stays an answer-key question.)
            for x in same:
                a, b = x['refs']
                if a not in G or b not in G: continue
                la, lo = PIN[b][1], PIN[b][2]
                best = min(G[b], key=lambda poly: min(math.hypot(q[0] - lo, q[1] - la) for q in poly[0]) if poly and poly[0] else 1e9)
                ring = best[0]; xs = [q[0] for q in ring]; ys = [q[1] for q in ring]
                sp = {'refs': sorted([a, b]), 'kind': 'same land', 'center': [round(sum(ys) / len(ys), 6), round(sum(xs) / len(xs), 6)],
                      'box': [round(min(xs), 5), round(min(ys), 5), round(max(xs), 5), round(max(ys), 5)],
                      'shape': [[round(q[0], 6), round(q[1], 6)] for q in ring[::max(1, len(ring) // 80)]],
                      'passes': [1, 1, 1], 'status': 'candidate (same land, two park numbers)', 'found': today,
                      'note': f"both park numbers are joined to the same official outline ({x['name']}); POTA lists them separately: check POTA's current list",
                      'maps': [[r, PIN[r][3]] for r in (a, b)], 'names': {r: PIN[r][0] for r in (a, b)}}
                sp['id'] = key_of(sp) + '@%.3f,%.3f' % tuple(sp['center'])
                by.setdefault('US-KY', []).append(sp)
        for st in sorted(set(by) | {p['st'] for p in parks.values()}):
            if counts.get('stopped for time') and st not in by and st in old: continue
            save_json(file_of(st), {'st': st, 'about': ABOUT, 'pass1': today, 'spots': slim(sorted(by.get(st, []), key=lambda s: s['id']))}, indent=1 if REGION != 'world' else None)
    else:
        files = {st: d for st, d in old.items() if (not ONLY or st in ONLY or st[3:] in ONLY)}
        # resume: a spot this pass already decided (agreed, or dropped) is not done again
        todo = lambda s: s['passes'][PASS - 2] == 1 and not s['passes'][PASS - 1] and not str(s.get('status', '')).startswith(f'dropped in pass {PASS}') and not (PASS == 3 and str(s.get('status', '')).startswith(('candidate', 'dropped: ', 'not sure', 'water only', 'check: two owners', 'very tight')))
        prev = [s for d in files.values() for s in d.get('spots', []) if todo(s)]
        refs = sorted({r for s in prev for r in s['refs'] if r in parks})
        notice('2-fer bot', f'pass {PASS}: {len(prev)} spots from pass {PASS - 1}, {len(refs)} parks to download fresh')
        if REGION == 'ky':   # Kentucky's official files are the only copy (no agency download by id): saved copy, flagged
            G, bad = ky_geom(parks, [r for r in refs if parks[r]['ids']]); saved_only = set(G)
        else:
            G, bad = download(parks, [r for r in refs if parks[r]['ids']], DET, PREC)
            saved_only = set()
        if REGION == 'world' and bad:   # not an ArcGIS map (France's IGN, Germany's BfN, Japan's A10…): only the saved copy exists
            sw = saved_world({r: parks[r] for r in bad})
            for r, g in sw.items(): G[r] = g; saved_only.add(r)
            bad -= saved_only
        counts['parks whose outline could not be read'] = len(bad)
        counts['parks with a saved copy only (no fresh download possible)'] = len(saved_only)
        pairs = {tuple(sorted(s['refs'][:2])) for s in prev}
        for s in prev:
            if len(s['refs']) > 2:
                rs = s['refs']; pairs |= {tuple(sorted((rs[i], rs[j]))) for i in range(len(rs)) for j in range(i + 1, len(rs))}
        pairs = {p for p in pairs if all((r in G) or (r in LN) for r in p)}
        spots = find_spots(G, LN, pairs, counts)
        newk = {}
        for s in spots: newk.setdefault(key_of(s), []).append(s)
        agree = new_only = 0
        for st, d in files.items():
            for s in d.get('spots', []):
                if not todo(s): continue
                pk = tuple(sorted(s['refs'][:2]))
                if pk not in TESTED and len(s['refs']) == 2:   # out of time before this pair: the next run carries on
                    s['status'] = f'waiting for pass {PASS}'; continue
                sb = sbox(s)
                m = next((n for n in newk.get(key_of(s), []) if inter(sb, sbox(n), 0.0005)), None)
                if m:
                    s['passes'][PASS - 1] = 1; agree += 1
                    for k in ('center', 'shape', 'box', 'acres', 'wide_m', 'len_m'):
                        if k in m: s[k] = m[k]
                    m['_used'] = 1
                    s['status'] = f'pass {PASS}'
                else:
                    s['passes'][PASS - 1] = 0
                    s['status'] = f'dropped in pass {PASS}' + (' (an outline could not be downloaded)' if any(r in bad for r in s['refs']) else '')
                if REGION == 'ky' and 'US-4484' in s['refs'] and set(s['refs']) & KY_FS_MANAGED:
                    s['label'] = 'Forest Service land managed by KDFWR'   # Oct 27 (HQ ruling 2): one agency owns, another manages = a real 2-fer
                if PASS == 3 and m: decide(s, parks, G, LN, PIN, today, saved_only, st_of)
            d[f'pass{PASS}'] = today
            d['about'] = ABOUT   # Oct 26 6:41 PM (HQ): the house-rule wording travels with every save
            d['spots'] = slim(d.get('spots', []))
            save_json(file_of(st), d, indent=1 if REGION != 'world' else None)
        new_only = sum(1 for v in newk.values() for n in v if not n.get('_used'))
        counts.update({'agree with the pass before': agree, 'new here only (not counted)': new_only})
    # report
    rep = {}
    RF = OUT / {'world': 'report-world.json', 'ky': 'report-ky.json'}.get(REGION, 'report.json')
    try: rep = json.load(open(RF))
    except Exception: pass  # noqa: BLE001
    per = {}
    for f in sorted(OUT.glob('*-*.json')):
        if not re.fullmatch(FILES, f.stem): continue
        sp = json.load(open(f)).get('spots', [])
        if sp: per[f.stem] = {'spots': len(sp), 'pass1': len(sp), 'pass2': sum(1 for s in sp if s['passes'][1]), 'candidates': sum(1 for s in sp if s['status'] == 'candidate'), 'candidates (saved outline only)': sum(1 for s in sp if s['status'] == 'candidate (saved outline only)'),
                              'n-fers': sum(1 for s in sp if len(s['refs']) > 2), 'lines': sum(1 for s in sp if s['kind'] != 'area'),
                              'very tight': sum(1 for s in sp if str(s.get('status', '')).startswith('very tight')), 'not sure': sum(1 for s in sp if str(s.get('status', '')).startswith('not sure')),
                              'water only': sum(1 for s in sp if str(s.get('status', '')).startswith('water only'))}
    rep['about'] = 'Counts from the 2-fer bot (kpc_fers.py). Hidden: data only.'
    rep[f'pass{PASS}'] = dict(counts, date=today, problems=LOG[:40])
    rep['per state'] = per
    save_json(RF, rep, indent=1)
    notice('2-fer bot', json.dumps({k: v for k, v in counts.items() if k != 'left out'})[:800])
    for l in LOG[:8]: notice('2-fer bot problem', l)


ABOUT = ("Spots where the boundaries of two or more POTA parks may overlap, by the 2-FER RULES FOR THE WHOLE WORLD (Brandon Oct 27, "
         "notes/mapping.md): the park = where its designation legally applies (national forests + grasslands = Forest Service-OWNED land only, "
         "never proclamation lines); public land open to the public; layered = real, side by side = not (ownership step: PAD-US / CPCAD at the "
         "spot); a patch 50 yards across in every park ('small' = 50-100 yards; 25-50 yards = the separate 'very tight' list, members only; under 25 = not kept); line-only trails / rivers by POTA's 100-ft rule from the line "
         "or the river EDGE (USGS NHD); pins never count. Status: 'candidate' = all checks passed; 'not sure: …' and 'water only: boat or "
         "kayak' are separate lists, never the main one; 'dropped: …' says why. Every decided spot shows 'checked' + 'map_dates'. Parks with "
         "no official boundary: missing-<region>.json. HIDDEN, not reviewed: passes [saved, fresh, finest] must all be 1 "
         "and status 'candidate' before a person looks. Wording when shown (house rule, Oct 26 5:45 PM): '⚠️ Possible POTA overlap only. "
         "We think these POTA parks' boundaries may overlap here, but we can't confirm it. Check both official boundary maps and make your "
         "own call before you count it.' Tool pages carry the FULL notice from CLAUDE.md.")

if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc()
        notice('2-fer bot', f'stopped: {e}')
    sys.exit(0)
