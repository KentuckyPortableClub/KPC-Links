"""US boundary ANSWER KEY, every state but Kentucky (Brandon Oct 17 2026: 'quick and best method… why not start them tonight').
For each state: every federal / state FEE record in USGS PAD-US (names, type, manager, acres, a coarse outline for 'where it is'),
matched to that state's POTA parks (data/parkinfo/US-XX.json) with the same strict rule the Kentucky tools use:
SAME NAME (generic words dropped) AND SAME KIND of place (WMA to WMA, state park to state park…), near the park's pin.
Anything unsure is NOT joined: it goes on the park's 'check' list with the reason. Writes:
  data/us-key/US-XX.json  {updated, st, parks:{ref:{n, t, m:[[objectid, name, acres, how]], c:[[objectid, name, acres, why]]}},
                           nonum:[[objectid, name, designation, manager, acres]] (biggest 300 fed/state places no POTA park matched), counts}
  data/us-key/index.json  {updated, states:{XX:{parks, matched, check, none, nonum}}}
STATES='TN IN' picks states (default: every state + DC except KY). PAD-US's firewall refuses long WHERE clauses, so we list each state with
State_Nm='XX' only and filter here."""
import json, math, os, re, sys, time, urllib.parse, urllib.request, pathlib

Q = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
ALL = 'AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split()
STATES = (os.environ.get('STATES') or '').upper().replace(',', ' ').split() or ALL
if os.environ.get('FINISH_ONLY'): STATES = []   # Oct 28 (key speed-up): the join job after the split jobs: only the all-state steps at the end
OUT = pathlib.Path('data/us-key'); OUT.mkdir(parents=True, exist_ok=True)
T0 = time.time(); LIMIT = float(os.environ.get('MINUTES') or 300) * 60
import gzip
# SHAPE DETAIL + SAVED COPY (Oct 22, Fable's review: 'nearly all the time is re-downloading the same geometry').
# Every live run has fetched outlines simplified to 0.01 degrees (~1.1 km) because they were fetched fresh each
# time and finer ones are slow. That is coarser than many of the parks: a 40-acre wildlife area is narrower than
# a kilometre, and a pin within a kilometre of the real line can fall outside the smoothed one. A SAVED copy is
# fetched once, so it can afford ~110 m. GEO_CACHE_MODE:
#   off      (default) exactly as before: fetch live, save nothing
#   use      load the saved copy if there is one, else fetch and save it
#   refresh  always fetch, and save
#   only     never touch the network: saved copies only, states without one are skipped (the fast rule test)
DETAIL = float(os.environ.get('GEO_DETAIL') or 0.01)
PREC = 3 if DETAIL >= 0.01 else 5
PAGE = int(os.environ.get('GEO_PAGE') or 500)
CACHE = pathlib.Path(os.environ.get('GEO_CACHE') or 'cache/us')
CMODE = (os.environ.get('GEO_CACHE_MODE') or 'off').strip().lower()
CACHE_USED, CACHE_SAVED = [], []
SHADOW = os.environ.get('SHADOW') == '1'
NAME_JOIN = (os.environ.get('NAME_JOIN') or '1') != '0'   # Oct 24: the world key's kind-label rule, US version (needs the pin inside)


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', '%0A')), flush=True)


def get(params, tries=5):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(Q + '?' + urllib.parse.urlencode(params), headers={'User-Agent': 'KPC (kentuckyportableclub.github.io)'})
            with urllib.request.urlopen(req, timeout=180) as r:
                j = json.loads(r.read().decode('utf-8', 'replace'))
            if j.get('error'): raise RuntimeError(str(j['error'])[:200])
            return j
        except Exception as e:  # noqa: BLE001
            last = e; time.sleep(8 * (i + 1))
    raise last


# ---------------- names + kinds (same idea as kpc-bounds.js, with other states' words) ----------------
GEN = (r"state habitat area|habitat area|mitigation park wildlife and environmental area|wildlife and environmental area|state scientific and natural area|scientific and natural area|scenic reserve|state natural reserve|natural reserve|coastal reserve|conservation reserve|unique area|state wayside|national memorial|natural environment area|nrma|nea|blm national conservation area|national conservation area|wildlife management area (and|&) public fishing area|public fishing area|fishing area|national wild and scenic river|wild and scenic river|national recreational river|state vehicle recreation area|vehicle recreation area|state reservation|reservation|state reserve|national reserve|national fish hatchery|state fish hatchery|fish hatchery|hatchery|fh|fishery area|state fishery area|blm herd management area|herd management area|herd area|blm special recreation management area|special recreation management area|extensive recreation management area|blm recreation management area|recreation management area|wilderness study area|wsa|hma|srma|erma|blm|fishing access site|access site|state game lands? number|designated state natural area|designated|public hunting area|hunting area|state fishing lake|fishing lake|state wilderness area|wilderness area|wilderness|resort|natural state conservation area|waterfowl refuge|wildlife refuge|refuge|state natural area|natural area preserve|state nature preserve|nature preserve|natural area|fish and wildlife area|state wildlife area|"
       r"wildlife management area|wildlife area|state game lands?|game lands?|game areas?|game management area|conservation area|state conservation area|"
       r"state resort park|state historic site|state historical park|state historic park|historic site|state recreation area|recreation area|"
       r"state beach|state seashore|national wildlife refuge|national recreation area|national historical park|national historic site|"
       r"national park|national forest|national grassland|national monument|national seashore|national lakeshore|national battlefield|"
       r"national military park|national preserve|national river|state park|state forest|management area|wma|nwr|nra|nca|na|wa|sp|sf|sgl|state|number|no|the|of|and")
ABBR = {'sulphur': 'sulfur', 'sulpher': 'sulfur', 'vehicular': 'vehicle', 'recreational': 'recreation', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine', '10': 'ten', '11': 'eleven', '12': 'twelve', 'col': 'colonel', 'sgt': 'sergeant', 'mt': 'mount', 'ft': 'fort', 'st': 'saint', 'pt': 'point', 'lk': 'lake', 'cr': 'creek', 'mtn': 'mountain',
        # Oct 22: agency short forms, expanded so the generic-word strip removes them. Colorado Parks & Wildlife writes
        # 'Flagler Reservoir SWA' for PAD-US's 'Flagler Reservoir State Wildlife Area'; unexpanded, the two read as two places
        'swa': 'state wildlife area', 'sra': 'state recreation area', 'nca': 'national conservation area',
        'nwr': 'national wildlife refuge', 'srma': 'special recreation management area', 'sna': 'state natural area',
        'sfu': 'state fish hatchery', 'historical': 'historic',
        'dnp': 'state nature preserve', 'snp': 'state nature preserve', 'shs': 'state historic site'}   # Oct 25: Ohio ODNR 'Acadia Cliffs DNP' (dedicated nature preserve)   # Colorado Parks & Wildlife 'Rifle Falls SFU' = Rifle Falls State Fish Hatchery
# Oct 24: the Oct 22 'keep a leading type word' rule must not keep a leading article or filler - 'The 400 State Trail'
# came out as 'the 400 trail' and no longer met '400 State Trail' (found measuring the WI key)
NOTNAME = {'the', 'of', 'and', 'state', 'national', 'no', 'number', 'blm', 'designated', 'a', 'an'}
def norm(s, drop1=False):
    s = str(s or '')
    # Oct 26 (gap hunt): Michigan DNR names its State Game Lands 'Bill Rollo Memorial Grouse Enhanced Mgmt.Sys.(GEMS)(SWMA)';
    # POTA says 'Bill Rollo Memorial State Game Land'. The GEMS words (and anything after, '... of Plum Creek') are not the name
    s = re.sub(r'\s*\bgrouse\s+enh.*$', ' ', s, flags=re.I)
    # Oct 22: a named piece of one area is still that area - 'Cherokee SWA - Lone Pine Unit', 'Roaring Fork SWA -
    # Wheeler Parcel', 'Dolores River Canyon, Zone 3'. Drop the piece's own name after the dash or comma. Done FIRST,
    # while the dash is still a dash (it becomes a space a few lines down).
    s = re.sub(r'\s+[-–,]\s+[\w .\']*?\b(unit|parcel|tract|zone|addition|annex)\b.*$', ' ', s, flags=re.I)
    s = re.sub(r'^([A-Za-z-]+) \(([^)]+)\)', r'\2 \1', s)   # 'Busch (August A.) Memorial' = 'August A. Busch Memorial'
    s = re.sub(r'&', ' and ', s.lower()).replace('-', ' ')
    s = re.sub(r'\(.*?\)', ' ', s)                       # '(2021 Addition)'
    s = re.sub(r"[’'`ʻʼ‘]", '', s)                         # Chimney's = Chimneys; Hawaiian ʻokina (Kuliʻouʻou = Kuliouou)
    s = re.sub(r'\.', ' ', s)
    s = re.sub(r'\b([a-z])\b(?:\s+(?=[a-z]\b))', r'\1', s)  # initials: 'm t s u' = 'mtsu', 'c r' = 'cr'
    s = re.sub(r'^[a-z]{2} (\d)', r'\1', s)                # 'PA 332 State Game Land' = 'State Game Land 332'
    s = re.sub(r'\b0+(\d)', r'\1', s)                     # 'Game Land 013' = 'Game Lands 13'
    s = re.sub(r'\b(unit|tract|parcel|zone)\s+[0-9ivx]+\b', ' ', s)
    s = ' '.join(ABBR.get(w, w) for w in s.split())
    _first = s.split()[0] if s.split() else ''
    s = re.sub(r'\b(' + GEN + r')\b', ' ', s)
    if _first and _first not in NOTNAME and not s.startswith(_first) and len(s.split()) <= 3:
        s = _first + ' ' + s          # keep a leading type word: it is doing the naming here
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    s = ' '.join(ABBR.get(w, w) if w.isdigit() else w for w in s.split())   # '#4' = 'Pool 4' = 'Pool Four'
    if drop1: s = re.sub(r'(?<=[a-z0-9] )[a-z](?= [a-z0-9])', ' ', s)   # only a MIDDLE initial (World War I keeps its I)              # also try without a lone middle initial ('George H. Crosby')
    return re.sub(r'\s+', ' ', s).strip()


KINDS = [('wma', r'wildlife management area|\bwma\b|\bswa\b|wildlife area|game lands?|game areas?|game management area|hunting area|fish and wildlife area|public hunting|fishery area|fishing access|habitat area|wildlife and environmental area|(?<!recreation )(?<!herd )(?<!conservation )management area'),
         ('wsr', r'wild (and|&) scenic river|recreational river'),
         ('ca', r'conservation area|conservation reserve|\baccess$'),          # Missouri: 'Kings Prairie Access' = Kings Prairie Access State Conservation Area
         ('snp', r'nature preserve|natural area|\bsnp\b|\bsna\b|natural heritage|\bpreserve\b|natural state conservation|natural reserve|scientific and natural|natural environment area|\bnea\b|\bnrma\b'),
         ('hist', r'historic(al)? (site|park|area)|\bshs\b'),
         ('sp', r'state (resort )?park|historic(al)? park|\bsrp\b|recreation(al)? area|state beach|state seashore'),
         ('nf', r'national forest|national grassland'), ('sf', r'state forest'),
         ('nwr', r'wildlife refuge|\bnwr\b'), ('nfh', r'hatchery|\bnfh\b|\bfh\b'),
         ('nps', r'national (park|monument|preserve|seashore|lakeshore|battlefield|military park|river|scenic river|parkway)'),
         ('wild', r'wilderness(?! study)'), ('wsa', r'wilderness study area|\bwsa\b'),
         ('hma', r'herd (management )?area|\bhma\b'),
         ('rma', r'recreation management area|\bs?rma\b|\berma\b|campground|recreation site|day use area')]
def kinds(s):
    s = str(s or '').lower(); return {k for k, r in KINDS if re.search(r, s)}
DES = {'SP': 'sp', 'SREC': 'sp', 'SHCA': 'hist', 'NWR': 'nwr', 'NF': 'nf', 'NG': 'nf', 'NP': 'nps', 'NM': 'nps', 'NRA': 'nps', 'NHS': 'hist', 'WA': 'wild'}


def variants(s):
    # other ways of writing the same name: no middle initial, bracket words left out ('Reifsnider (Frank)'), no leading 'Mount'
    v = {norm(s), norm(s, True), norm(re.sub(r'\(.*?\)', ' ', str(s or '')))}
    v |= {re.sub(r'^mount ', '', x) for x in v}
    v |= {re.sub(r' (park|forest|pond|ponds|lake|reservoir|complex|memorial|reserve)$', '', x) for x in v}         # 'Fort Revere Park' = Fort Revere, 'Coulee Experimental Forest'
    return {x for x in v if x}


def _nosp(a, b):
    # Oct 26 (gap hunt): one name written as one word, the other as two: 'Hard Trigger' = BLM 'Hardtrigger', 'Blackridge' =
    # 'Black Ridge'. EQUAL only once the spaces are gone (no typo allowance here: 'World War I' / 'World War II' stay apart)
    va = {x.replace(' ', '') for x in variants(a)}; vb = {x.replace(' ', '') for x in variants(b)}
    return any(len(x) >= 8 for x in va & vb)


def same_name(a, b):
    if str(a or '').strip().lower() == str(b or '').strip().lower(): return True
    if _nosp(a, b): return True
    a1, b1 = norm(a), norm(b)
    if _same(a1, b1) or any(_same(x, y) for x in variants(a) for y in variants(b)): return True
    sa, sb = _sing(a1), _sing(b1)                          # McCloskey's = McCloskey, Glades = Glade
    if _same(sa, sb): return True
    return len(sa) >= 8 and len(sb) >= 8 and not re.search(r'\d', sa + sb) and _ed1(sa, sb)   # one-letter typos in PAD-US ('Horshoe', 'Morraine')


SOFT = {'preserve', 'reserve', 'beach', 'complex', 'game', 'mua', 'fwma', 'ca', 'pas', 'tract', 'tracts', 'addition', 'unit', 'area', 'lake', 'lakes', 'pond', 'ponds', 'reservoir',
        'park', 'forest', 'center', 'centre', 'site', 'lands', 'land'}
def _soft(x): return ' '.join(w for w in x.split() if w not in SOFT and not re.fullmatch(r'(19|20)\d\d', w))


SIDES = ('upper', 'lower', 'north', 'south', 'east', 'west', 'middle')


def _side(x):
    return {w for w in str(x or '').lower().replace('-', ' ').split() if w in SIDES}


def exact_name(a, b):
    if _side(a) != _side(b): return False        # Upper White Oak Lake is not White Oak Lake
    # no 'starts with' allowance: used when only one of the two names says what kind of place it is.
    # Only 'soft' words may differ (Torrey Pines Reserve = Torrey Pines State Reserve, Big Bend = Big Bend - 2015)
    if str(a or '').strip().lower() == str(b or '').strip().lower(): return True
    if _nosp(a, b): return True
    va, vb = variants(a), variants(b)
    va |= {_soft(x) for x in va if _soft(x)}; vb |= {_soft(x) for x in vb if _soft(x)}
    if va & vb or {_sing(x) for x in va} & {_sing(x) for x in vb}: return True
    return any(len(x) >= 8 and len(y) >= 8 and not re.search(r'\d', x + y) and _ed1(x, y) for x in va for y in vb)   # one-letter typo ('Pishkin' / 'Pishkun')


def name_ok(a, b, ka, kb):
    if not same_kind(ka, kb): return False
    if ('nfh' in ka) != ('nfh' in kb): return False                      # a hatchery only joins a hatchery (Dworshak Reservoir is not the hatchery)
    if bool(re.search(r'\btrail\b', str(a), re.I)) != bool(re.search(r'\btrail\b', str(b), re.I)): return False   # a trail only joins a trail
    return exact_name(a, b) if (bool(ka) != bool(kb)) else same_name(a, b)


def _sing(s): return ' '.join(w[:-1] if len(w) > 3 and w.endswith('s') else w for w in s.split())


def _ed1(a, b):
    if a == b: return True
    wa, wb = a.split(), b.split()   # one typo inside one long word only ('Horshoe'), never a short word ('I' / 'II')
    if len(wa) != len(wb): return False
    diff = [(x, y) for x, y in zip(wa, wb) if x != y]
    if len(diff) != 1 or min(len(diff[0][0]), len(diff[0][1])) < 5: return False
    a, b = diff[0]
    if abs(len(a) - len(b)) > 1: return False
    if len(a) == len(b): return sum(x != y for x, y in zip(a, b)) == 1
    if len(a) > len(b): a, b = b, a
    return any(a == b[:i] + b[i + 1:] for i in range(len(b)))


def wset(s):
    # every word, keeping words in brackets ('Cash (Ben) Memorial' = Ben Cash Memorial)
    return set(w for w in _sing(norm(str(s or '').replace('(', ' ').replace(')', ' '))).split() if len(w) > 1)


def same_words(a, b, ka, kb):
    # all words of the shorter name are in the longer one, at most 2 extra words, and BOTH names say the same kind of place
    if not (ka and kb and ka & kb): return False
    # Oct 22: THIS is where Upper and Lower White Oak Lake both joined White Oak Lake State Park - 'white oak lake' sits
    # inside 'upper white oak lake' with one word to spare. A side word in one name and not the other is a different place.
    if _side(a) != _side(b): return False
    if ('nfh' in ka) != ('nfh' in kb) or bool(re.search(r'\btrail\b', str(a), re.I)) != bool(re.search(r'\btrail\b', str(b), re.I)): return False
    w1, w2 = wset(a), wset(b)
    s, l = (w1, w2) if len(w1) <= len(w2) else (w2, w1)
    big = [w for w in s if len(w) > 2]
    if len(big) == 1:   # one long word, same kind ('Keyhole' = 'Keyhole Reservoir'); wrong ones go in overrides.json 'no'
        return len(big[0]) >= 6 and ka == kb and s <= l and len(l - s) <= 2
    return len(big) >= 2 and s <= l and len(l - s) <= 2


def _same(a, b):
    if not a or not b: return False
    if a == b: return True
    s, l = (a, b) if len(a) < len(b) else (b, a)
    return len(s) > 5 and l.startswith(s) and l[len(s):len(s) + 1] == ' ' and len(s) / len(l) >= 0.6   # whole words only (World War I is not World War II)


US_COMPAT = [{'wild', 'wsa'}, {'ca', 'snp'}]   # POTA lists many BLM study areas as 'BLM Wilderness Area'
def same_kind(ka, kb): return not ka or not kb or bool(ka & kb) or any(ka & c and kb & c and (ka | kb) & c == c for c in US_COMPAT)


def words(s): return set(w for w in norm(s).split() if len(w) > 2)


def join_how(name, kp, a, close):
    """How - if at all - the POTA park called `name` (kinds `kp`) joins official record `a`. `close` = within
    about 0.1 degree of the park's pin. This is the ONLY place the decision is made: run() calls it and so do the
    golden tests, so a test can never again check a different path from the one the matcher really takes (Oct 22:
    the first Upper/Lower fix went into exact_name, which was never the path White Oak Lake actually joined by)."""
    nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
    loc = a.get('Loc_Nm')
    if name_ok(name, nm, kp, a['_k']) or (loc and name_ok(name, loc, kp, a['_k'])):
        return 'name'
    if isinstance(a.get('OBJECTID'), int) and not kinds(nm) and exact_name(name, nm) and name_ok(name, nm, kp, set()):
        # Oct 18 review: a bare PAD-US name ('Fort Fetterman', 'Trail End') whose only 'kind' came from its designation code,
        # and the whole name matches: the designation code is often off, so the name decides
        return 'name (designation code ignored)'
    if close and (same_words(name, nm, kp, a['_k']) or (loc and same_words(name, loc, kp, a['_k']))):
        return 'words'
    return None


# ---------------- geometry helpers (coarse) ----------------
def rings(g): return g.get('rings') or [] if g else []
def bbox(g):
    xs = [p[0] for r in rings(g) for p in r]; ys = [p[1] for r in rings(g) for p in r]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None
def in_ring(x, y, r):
    ins = False; j = len(r) - 1
    for i in range(len(r)):
        xi, yi, xj, yj = r[i][0], r[i][1], r[j][0], r[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi: ins = not ins
        j = i
    return ins
def inside(la, lo, g): return sum(1 for r in rings(g) if in_ring(lo, la, r)) % 2 == 1
def near(la, lo, b, pad): return b and b[0] - pad <= lo <= b[2] + pad and b[1] - pad <= la <= b[3] + pad


FIELDS = None
def fields():
    global FIELDS
    if FIELDS is None:
        try:
            req = urllib.request.Request(Q.rsplit('/', 1)[0] + '?f=json', headers={'User-Agent': 'KPC (kentuckyportableclub.github.io)'})
            info = json.loads(urllib.request.urlopen(req, timeout=120).read())
            have = {f['name'] for f in info.get('fields', [])}
            # Oct 27 (boundary review #2 / rule B7): the PAD-US version every PAD-US outline comes from
            m = re.search(r'PAD-US\s*(?:version\s*)?(\d+(?:\.\d+)*)', ' '.join(str(info.get(k) or '') for k in ('description', 'copyrightText', 'name')), re.I)
            PADVER[0] = 'PAD-US ' + m.group(1) if m else 'PAD-US'
        except Exception: have = set()  # noqa: BLE001
        want = 'OBJECTID,Unit_Nm,Loc_Nm,Own_Type,Mang_Type,Mang_Name,Loc_Mang,Des_Tp,d_Des_Tp,Pub_Access,GIS_Acres,Category'.split(',')
        FIELDS = ','.join(w for w in want if not have or w in have)
        notice('PAD-US fields', FIELDS + (' (field list not read)' if not have else ''))
    return FIELDS


PADVER = ['PAD-US']
GEO = ([{'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': DETAIL, 'geometryPrecision': PREC}] if DETAIL < 0.01 else []) + \
      [{'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': 0.01, 'geometryPrecision': 3},
       {'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': 0.01}, {'returnGeometry': 'true', 'outSR': 4326}]
GI = [0]
def page(st, off):
    while True:
        q = {'where': "State_Nm='%s'" % st, 'outFields': fields(), 'f': 'json', 'resultOffset': off, 'resultRecordCount': PAGE, 'orderByFields': 'OBJECTID'}
        q.update(GEO[GI[0]])
        try: return get(q, tries=3)
        except Exception as e:  # noqa: BLE001
            if GI[0] + 1 >= len(GEO): raise
            notice('PAD-US', f'query shape {GI[0]} refused ({e}); trying a simpler one'); GI[0] += 1


def pad_state(st):
    recs, off = [], 0
    while True:
        j = page(st, off)
        fs = j.get('features', [])
        for f in fs:
            a = f.get('attributes') or {}
            if (a.get('Category') or '') not in ('Fee', 'Designation'): continue   # Designation = wilderness, NCA… overlays (BLM wilderness has no fee record of its own)
            # Oct 18: + DIST (regional special districts: Florida's water management districts own the 'State Conservation Areas' POTA lists)
            if (a.get('Own_Type') or '') not in ('FED', 'STAT', 'DIST') and (a.get('Mang_Type') or '') not in ('FED', 'STAT', 'DIST'): continue
            g = f.get('geometry') or {}
            a['_bb'] = bbox(g); a['_g'] = g
            a['_k'] = kinds(a.get('Unit_Nm')) | kinds(a.get('Loc_Nm')) | ({DES[a['Des_Tp']]} if a.get('Des_Tp') in DES else set())
            recs.append(a)
        if not fs or (not j.get('exceededTransferLimit') and len(fs) < PAGE): break
        off += len(fs); time.sleep(.6)
    return recs, off + len(fs)


def fetch_geo(url, q, timeout=180):
    """Ask for the finer outline first when one was asked for; if the server refuses or times out, fall back to
    the 0.01-degree outline every run has always used, rather than losing the layer for that state."""
    tries = ([(DETAIL, PREC)] if DETAIL < 0.01 else []) + [(0.01, 3)]
    last = None
    for det, pr in tries:
        q = dict(q, maxAllowableOffset=det, geometryPrecision=pr, resultRecordCount=PAGE if det < 0.01 else 500)
        try:
            req = urllib.request.Request(url + '?' + urllib.parse.urlencode(q), headers={'User-Agent': 'KPC (kentuckyportableclub.github.io)'})
            j = json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', 'replace'))
            if j.get('error'): raise RuntimeError(str(j['error'])[:150])
            return j, q['resultRecordCount']
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


FWS = 'https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSInterest_Simplified_Authoritative/FeatureServer/0/query'
STB = None
def st_box(st):
    global STB
    if STB is None:
        try: STB = json.load(open('kpc-us-states.json'))
        except Exception: STB = []  # noqa: BLE001
    x = next((b for b in STB if b.get('a') == st), None)
    if not x: return None
    xs = [q[0] for pl in x['p'] for q in pl[0]]; ys = [q[1] for pl in x['p'] for q in pl[0]]
    return [min(xs), min(ys), max(xs), max(ys)]


def fws_state(st, have):
    # USFWS's own land layer: PAD-US misses some refuges (Oklahoma: Sequoyah, Optima, Tishomingo NWR are not in it)
    box = st_box(st)
    if not box: return []
    out, off = [], 0
    while True:
        q = {'where': "INTTYPE1<>'E'", 'geometry': ','.join(map(str, box)), 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
             'outFields': 'OBJECTID,ORGNAME,RSL_TYPE,SUM_GISACRES', 'returnGeometry': 'true', 'outSR': 4326, 'f': 'json', 'resultOffset': off}
        try:
            j, pg = fetch_geo(FWS, q)
        except Exception as e:  # noqa: BLE001
            notice(f'US key {st}', f'USFWS land not read ({e})'); FAILED_READ.add(st); return out
        fs = j.get('features', [])
        for f in fs:
            a = f.get('attributes') or {}; nm = (a.get('ORGNAME') or '').title()
            if not nm or norm(nm) in have: continue
            g = f.get('geometry') or {}
            out.append({'OBJECTID': 'fws' + str(a.get('OBJECTID')), 'Unit_Nm': nm, 'Loc_Nm': '', 'Own_Type': 'FED', 'Mang_Type': 'FED', 'Mang_Name': 'FWS',
                        'Loc_Mang': 'U.S. Fish & Wildlife Service (own map)', 'Des_Tp': '', 'GIS_Acres': a.get('SUM_GISACRES') or 0, 'Category': 'Fee',
                        '_bb': bbox(g), '_g': g, '_k': kinds(nm) | kinds(a.get('RSL_TYPE')) | {'nwr'}})
        if not fs or (not j.get('exceededTransferLimit') and len(fs) < pg): break
        off += len(fs); time.sleep(.5)
    return out


# Official maps of the agencies themselves (Oct 18, Brandon: 'anything you can be working on in the US trip planner'): PAD-US stores wilderness,
# BLM herd areas and BLM recreation areas only as the forest / BLM office around them, so those parks never matched by name.
XS = [  # prefix, query url, name field, acres field, kinds
    ('wld', 'https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_Wilderness_02/MapServer/0/query', 'wildernessname', 'gis_acres', {'wild'}, 'National Wilderness Preservation System (Forest Service map)'),
    ('hma', 'https://gis.blm.gov/arcgis/rest/services/range/BLM_Natl_WHB/MapServer/0/query', 'HMA_NAME', 'BLM_ACRES', {'hma'}, 'BLM herd management areas'),
    # Oct 26 (gap hunt, HQ): the same BLM service's layer 1 = HERD AREAS (327; where horses were found in 1971). POTA lists some
    # of them as 'BLM Herd Management Area' (Bonanza, Robbers Roost, Big Creek, Triangle, Salt Wells Creek, Blawn Wash...).
    # A herd area with the same name as an HMA is left out (not_in): the HMA is the managed area and wins
    ('hab', 'https://gis.blm.gov/arcgis/rest/services/range/BLM_Natl_WHB/MapServer/1/query', 'HA_NAME', 'BLM_ACRES', {'hma'}, 'BLM herd areas', 'FED', None, {'not_in': 'hma'}),
    ('rma', 'https://gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recreation/MapServer/9/query', 'FET_NAME', 'GIS_ACRES', {'rma'}, 'BLM recreation areas'),
    # Oct 26 (round 11, HQ): this IS the national BLM Recreation Management Area layer (SRMA 1,108 + ERMA 1,782 + campgrounds,
    # day use, OHV areas); read since Oct 18. Relabelled. A probe of all 3,478 names found only 10 of the 427 BLM 'Recreation
    # Management Area' POTA parks with no outline in it: POTA's are mostly sites INSIDE an RMA (dams, canyons, trailheads).
    ('rst', 'https://gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recs_poly/MapServer/0/query', 'FET_NAME', 'GIS_ACRES', {'rma'}, 'BLM recreation management areas · official (BLM planning area)'),
    # Oct 26 (round 11): NPS official Wild and Scenic River CORRIDOR boundaries (33 rivers, legal corridors; the USFS centre lines
    # stay the trails bot's for the other rivers) + the Ala Kahakai NHT official corridor (one polygon, Hawaii)
    ('wsrc', 'https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/WildScenicRiverBoundaries/FeatureServer/0/query', 'WSR_GNIS_NAME', 'GIS_ACRES', {'wsr'}, 'NPS Wild and Scenic River corridor (official boundary)'),
    # Oct 27 chat 9 (HQ, desk BigHoles Round 3): Forest Service wild-and-scenic river CORRIDORS (area parks, rule 5) and the Forest
    # Service's other national designated areas (monuments, NRAs, scenic areas); 'fullname' carries the type word. US federal data.
    ('fwsr', 'https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_WildScenicRiver_01/MapServer/0/query', 'designatedname', 'gis_acres', {'wsr'}, 'Forest Service Wild and Scenic River corridor (official boundary)'),
    ('fsod', 'https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_OtherNationalDesignatedArea_01/MapServer/0/query', 'fullname', 'gis_acres', set(), 'Forest Service national designated areas (monuments, NRAs, scenic areas)'),
    ('akht', 'https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/Ala_Kahakai_National_Historic_Trail_Official_Corridor/FeatureServer/0/query', 'TrailName', '', set(), 'NPS Ala Kahakai National Historic Trail corridor (official)', 'FED', {'HI'}),
    ('nca', 'https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_NM_NCA_poly/MapServer/0/query', 'NCA_NAME', '', set(), 'BLM national monuments / conservation areas'),
    # Oct 18: layer id + name field looked up at run time ('?' = find it); found by probe 2
    ('wsa', 'svc:https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_WLD_WSA/MapServer|study', '?', '?', {'wsa'}, 'BLM wilderness study areas'),
    ('wbl', 'svc:https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_WLD_WSA/MapServer|^(?!.*study).*wilderness', '?', '?', {'wild'}, 'BLM wilderness'),
    ('odw', 'svc:https://services1.arcgis.com/jRf8jjFwxedITdFe/arcgis/rest/services/Public_WMA_Boundaries/FeatureServer|.', '?', '?', {'wma'}, 'Oklahoma Dept. of Wildlife Conservation WMA map', 'STAT', {'OK'}),
    # Oct 18 (Brandon: 'go ahead'): state agencies' own land maps (found on ArcGIS Online, owner = the agency) for states with many unmatched parks
    ('ncg', 'svc:https://services1.arcgis.com/YfqBAUM5nWR3yhGP/arcgis/rest/services/gamelands_general/FeatureServer|.', '?', '?', {'wma'}, 'NC Wildlife Resources Commission game lands', 'STAT', {'NC'}),
    ('wdw', 'svc:https://geodataservices.wdfw.wa.gov/arcgis/rest/services/MapServices/WildlifeAreas/MapServer|wildlife', '?', '?', {'wma'}, 'WDFW wildlife areas', 'STAT', {'WA'}),
    ('idw', 'svc:https://services.arcgis.com/FjJI5xHF2dUPVrgK/arcgis/rest/services/WildlifeManagementAreas/FeatureServer|.', '?', '?', {'wma'}, 'Idaho Fish and Game WMAs', 'STAT', {'ID'}),
    ('law', 'svc:https://services1.arcgis.com/6euNCaGPCgCzgAVF/arcgis/rest/services/LDWF_WMA_Refuge/FeatureServer|.', '?', '?', set(), 'Louisiana Dept. of Wildlife and Fisheries WMAs and refuges', 'STAT', {'LA'}),   # Oct 18: LDWF_WMA moved (empty); probe 2 found these on LDWF's own account
    ('lar', 'svc:https://services1.arcgis.com/6euNCaGPCgCzgAVF/arcgis/rest/services/LDWF_WildlifeRefuge/FeatureServer|.', '?', '?', set(), 'Louisiana Dept. of Wildlife and Fisheries wildlife refuges', 'STAT', {'LA'}),
    ('maw', 'svc:https://services1.arcgis.com/7iJyYTjCtKsZS1LR/arcgis/rest/services/MassWildlifeLands/FeatureServer|.', '?', '?', {'wma'}, 'MassWildlife lands', 'STAT', {'MA'}),
    ('utw', 'svc:https://services.arcgis.com/ZzrwjTRez6FJiOq4/arcgis/rest/services/ULTRA_Properties_2_view/FeatureServer|.', '?', '?', {'wma'}, 'Utah DWR public access properties', 'STAT', {'UT'}),
    ('ctd', 'svc:https://services1.arcgis.com/FjPcSmEFuDYlIdKC/arcgis/rest/services/Connecticut_DEEP_Property/FeatureServer|.', '?', '?', set(), 'Connecticut DEEP property', 'STAT', {'CT'}),
    ('ind', 'svc:https://gisdata.in.gov/server/rest/services/Hosted/ManagedLands_DNR_Open/FeatureServer|.', '?', '?', set(), 'Indiana DNR properties', 'STAT', {'IN'}),
    ('wid', 'svc:https://dnrmaps.wi.gov/arcgis/rest/services/LF_DML/LF_AGOL_STAGING_WTM_Ext/MapServer|propert', '?', '?', set(), 'Wisconsin DNR managed properties', 'STAT', {'WI'}),
    ('tnd', 'svc:https://services5.arcgis.com/bPacKTm9cauMXVfn/arcgis/rest/services/TDEC_Public_Access_Lands/FeatureServer|.', '?', '?', set(), 'TDEC public access lands', 'STAT', {'TN'}),
    ('osp', 'svc:https://maps.prd.state.or.us/arcgis/rest/services/Land_ownership/Oregon_State_Parks/FeatureServer|.', '?', '?', set(), 'Oregon State Parks', 'STAT', {'OR'}),
    # Oct 20 (Brandon: 'keep working on the boundaries'): probe round 2, owner = the agency itself
    ('fnl', 'svc:https://services.arcgis.com/9Jk4Zl9KofTtvg3x/arcgis/rest/services/FL_Conservation_Lands_web/FeatureServer|.', '?', '?', set(), 'Florida Natural Areas Inventory conservation lands', 'STAT', {'FL'}),
    ('cow', 'svc:https://services5.arcgis.com/ttNGmDvKQA7oeDQ3/arcgis/rest/services/CPWAdminData/FeatureServer|managed propert', '?', '?', set(), 'Colorado Parks and Wildlife properties', 'STAT', {'CO'}),
    ('nep', 'svc:https://services5.arcgis.com/IOshH1zLrIieqrNk/arcgis/rest/services/Park_Areas/FeatureServer|.', '?', '?', set(), 'Nebraska Game and Parks areas', 'STAT', {'NE'}),
    # Oct 20 probe round 4 (owner = the state agency / state GIS office)
    ('arw', 'svc:https://gisec2.agfc.com/arcgis/rest/services/APP_AGFC/MapServer|wma boundar', '?', '?', {'wma'}, 'Arkansas Game and Fish Commission WMAs', 'STAT', {'AR'}),
    ('nhc', 'svc:https://nhgeodata.unh.edu/hosting/rest/services/Hosted/EC_Conservation/FeatureServer|conservation|public', '?', '?', set(), 'NH GRANIT conservation and public lands', 'STAT', {'NH'}),
    ('mid', 'svc:https://services3.arcgis.com/Jdnp1TjADvSDxMAX/arcgis/rest/services/DNRLOTSParcelsOPENDATA/FeatureServer|project boundar', '?', '?', set(), 'Michigan DNR project boundaries', 'STAT', {'MI'}),
    ('ndw', 'svc:https://services1.arcgis.com/GOcSXpzwBHyk2nog/arcgis/rest/services/NDGISHUB_Wildlife_Management_Areas/FeatureServer|.', '?', '?', {'wma'}, 'North Dakota Game and Fish WMAs', 'STAT', {'ND'}),
    ('vta', 'svc:https://anrmaps.vermont.gov/arcgis/rest/services/Open_Data/OPENDATA_ANR_CADASTRAL_SP_NOCACHE_v2/MapServer|unit', '?', '?', set(), 'Vermont ANR lands', 'STAT', {'VT'}),
    ('mol', 'svc:https://services2.arcgis.com/kNS2ppBA4rwAQQZy/arcgis/rest/services/MO_Missouri_Department_of_Conservation_Lands/FeatureServer|.', '?', '?', set(), 'Missouri Dept. of Conservation lands (MSDIS)', 'STAT', {'MO'}),
    ('mdd', 'svc:https://mdgeodata.md.gov/imap/rest/services/Environment/MD_ProtectedLands/FeatureServer|dnr owned', '?', '?', set(), 'Maryland DNR lands', 'STAT', {'MD'}),
    ('vta', 'svc:https://anrmaps.vermont.gov/arcgis/rest/services/Open_Data/OPENDATA_ANR_CADASTRAL_SP_NOCACHE_v2/MapServer|unit', '?', '?', set(), 'Vermont ANR lands', 'STAT', {'VT'}),
]
# Oct 24 (Brandon: 'they a new state level gis fable set up you can use as needed'): the Map Rep Tool Box's table of
# each state's OWN park / wildlife / forest / preserve layers (data/state-gis.json, 60 layers in 37 states, kept by
# kpc-state-gis.yml) feeds the key too. Layers already in XS by address are skipped; a layer that does not answer is
# skipped like any other. Entries marked 'auto:' were found by the bot and not yet checked by a person, and are used
# all the same: the key's name + kind rules decide, and the website labels the result like any other join.
SGK = {'park': {'sp'}, 'wild': {'wma'}, 'forest': {'sf'}, 'preserve': {'snp'}, 'land': set()}
try:
    _sg = json.load(open('data/state-gis.json')).get('states') or {}
    _have = {x[1].split('/query')[0].rstrip('/') for x in XS}
    # Oct 25: a layer keeps the prefix it was first given (read back from data/us-key/layers.json), so a layer added in
    # the MIDDLE of a state's list can never shift the others and make saved ids point at the wrong map
    try: _LJ = json.load(open(OUT / 'layers.json'))
    except Exception: _LJ = {}  # noqa: BLE001
    _byurl = {v[0].split('/query')[0].rstrip('/'): k for k, v in _LJ.items() if k.startswith('sg') and isinstance(v, list) and v}
    _taken = set(_LJ)
    def _pre(st, u):
        if u in _byurl: return _byurl[u]
        n = 0
        while True:
            k = f'sg{st.lower()}' + (chr(97 + n) if n < 26 else chr(97 + n // 26 - 1) + chr(97 + n % 26))
            if k not in _taken: _taken.add(k); _byurl[u] = k; return k
            n += 1
    for _st, _lays in sorted(_sg.items()):
        if _st not in ALL: continue          # Oct 25: province codes (ON, QC…) are the Canada key's
        for _i, _l in enumerate(_lays):
            _u = str(_l.get('url') or '').rstrip('/')
            if not _u or not _l.get('nm') or _u in _have or not re.search(r'/\d+$', _u): continue
            # prefix = letters only ('sgfla'): the website splits an id into prefix + number with /^[a-z]+/
            XS.append((_pre(_st, _u), _u + '/query', _l['nm'], '', SGK.get(_l.get('kind'), set()), f"{_l.get('ag') or _st + ' state GIS'} ({_l.get('kind')}, state GIS table)", 'STAT', {_st},
                       {'water': bool(_l.get('water')), 'where': _l.get('where') or '1=1', 'nm2': _l.get('nm2') or ''}))
except Exception as _e: print(f'state-gis.json not read: {_e}', flush=True)  # noqa: BLE001
RESOLVED = {}
def resolve(pre, url, nf, af):
    # 'svc:<service>|<layer name regex>' → (query url, name field, acres field, object id field)
    rq = lambda u: json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'KPC (kentuckyportableclub.github.io)'}), timeout=120).read().decode('utf-8', 'replace'))
    if not url.startswith('svc:'):
        if not pre.startswith('sg'): return url, nf, af, ('objectid' if pre in ('wld', 'fwsr', 'fsod') else 'OBJECTID')
        if pre in RESOLVED: return RESOLVED[pre]
        L = rq(url.rsplit('/query', 1)[0] + '?f=json'); flds = L.get('fields') or []     # a state GIS layer: ask it for its own id + acres fields
        if 'Polygon' not in str(L.get('geometryType', '')): raise RuntimeError('not a polygon layer')
        oid = L.get('objectIdField') or next((f['name'] for f in flds if f.get('type') == 'esriFieldTypeOID'), 'OBJECTID')
        acres = next((f['name'] for f in flds if re.search(r'acre', f['name'], re.I)), '')
        RESOLVED[pre] = (url, nf, acres, oid)
        return RESOLVED[pre]
    if pre in RESOLVED: return RESOLVED[pre]
    svc, rx = url[4:].split('|', 1)
    lays = rq(svc + '?f=json').get('layers') or []
    pick = [l for l in lays if re.search(rx, l.get('name', ''), re.I) and not l.get('subLayerIds')] or [l for l in lays if not l.get('subLayerIds')]
    lid = pick[0]['id']
    L = rq(f'{svc}/{lid}?f=json'); flds = L.get('fields') or []
    strs = [f['name'] for f in flds if f.get('type') == 'esriFieldTypeString']
    name = next((f for f in strs if re.search(r'(^|_)(NAME|NM)(_|$)|NAME', f, re.I) and not re.search(r'admin|state|county|office|agency|own|mgr|manag|type|desig|file', f, re.I)), strs[0] if strs else '')
    acres = next((f['name'] for f in flds if re.search(r'acre', f['name'], re.I)), '')
    oid = L.get('objectIdField') or next((f['name'] for f in flds if f.get('type') == 'esriFieldTypeOID'), 'OBJECTID')
    RESOLVED[pre] = (f'{svc}/{lid}/query', name, acres, oid)
    notice('US key layer found', f'{pre}: {svc}/{lid} [{pick[0].get("name")}] name={name} acres={acres} oid={oid}')
    return RESOLVED[pre]
XCOUNT = {}
# Oct 22 (Brandon: 'keep the last good outlines'): a state whose maps did not all answer this run (a time-out, a server
# down for the night) must not lose the parks that map would have given it. Such a state uses its saved copy instead,
# and the half-read copy is never saved over the good one.
FAILED_READ = set()


def _num(v):   # Oct 25: an acres field can be text (NPS legal boundary layer): never let it stop a state
    try: return float(v or 0)
    except (TypeError, ValueError): return 0


# Oct 28 (HQ, chat 9 hand-off): layers that exist only as ZIPPED SHAPEFILES (Mississippi's MARIS has no live layers).
# Same reader as the Canada key's sz_pull(): the projection comes from the zip's own .prj. 'tk' = TYPE value -> kind
# (a TYPE not listed is left out). Credit 'MARIS / Mississippi Dept. of Wildlife, Fisheries & Parks' (disclaimer only, no use limits).
MS_TK = {'wma': 'wma', 'wma zone2': 'wma', 'sp': 'sp', 'refuge': 'wma', 'waterfowl': 'wma'}   # runner probe Oct 28: TYPE values; 'WMAcossar1..7' = WMA pieces
# left out on purpose: PRIVATE (198 inholdings), '16 section lease 2015' (a private lease, Q12), 'WMA tobe' (not yet a WMA), USFS (the
# Forest Service's own land), and the hunting zones INSIDE a WMA (Dog / Still Hunting Area, NO Hunting, Handicap, Greentree, Restricted,
# SANDBAR, IMPOUNDMENT, Lake): they are rules on a WMA's land, not more land
SZ_US = [('mszw', 'https://maris.mississippi.edu/MARISdata/Boundaries/MS_WildlifeManagementAreas_2026.zip', ('Name',), ('ACREAGE',),
          'MARIS / Mississippi Dept. of Wildlife, Fisheries & Parks (WMAs 2026, zip)', 'STAT', {'MS'}, {'type': 'TYPE', 'tk': MS_TK, 'tk_re': r'^wmacossar\d+$'}),
         # parks: NAME = a tract ('JP COLEMAN TRACT 5'), LABEL = the park ('JP COLEMAN SP'). MARIS: 'not a legal description, the general area'
         ('mszp', 'https://maris.mississippi.edu/MARISdata/Cultural/MS_StateParks_2026.zip', ('LABEL',), ('ACRES',),
          'MARIS / Mississippi Dept. of Wildlife, Fisheries & Parks (state parks 2026, zip; general area, not a legal description)', 'STAT', {'MS'},
          {'kind': 'sp', 'sub': [(r'\bSP$', 'State Park')]})]
ZIPC = {}


def _dup(have, key, bb):
    """Oct 29 (chat 2 trace): a state record is a COPY of a PAD-US record only when the same name + kind sits on the SAME
    ground (boxes overlap). Before, a same-name record ANYWHERE in the state hid it (WA Rock Creek / Telford Recreation Area,
    Hanford McGee Ranch, NC Nags Head Woods never reached the matcher)."""
    if not isinstance(have, dict): return key in have
    return key in have and (bb is None or any(b is None or not (bb[2] < b[0] or bb[0] > b[2] or bb[3] < b[1] or bb[1] > b[3]) for b in have[key]))


def _have(recs):
    d = {}
    for a in recs: d.setdefault((norm(a.get('Unit_Nm') or ''), frozenset(a['_k'])), []).append(a.get('_bb'))
    return d


def _fine(r):
    """R-G6 (Brandon Oct 29 12:36 PM): a saved ring simplified by at most ~3 m (0.00003 deg), never 'every Nth point'."""
    try:
        from shapely.geometry import LinearRing
        s = LinearRing(r).simplify(0.00003, preserve_topology=False)
        c = [[round(x, 6), round(y, 6)] for x, y in s.coords]
        return c if len(c) > 3 else r
    except Exception: return r  # noqa: BLE001


def zip_state(st, have):
    """Records from the zipped-shapefile layers for this state ([] when none, or when pyshp / pyproj are missing)."""
    out = []
    for pre, url, nfs, afs, label, own, sts, opt in SZ_US:
        if st not in sts: continue
        try:
            import io, zipfile, shapefile
            from pyproj import CRS, Transformer
            if url not in ZIPC:
                with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'KPC (kentuckyportableclub.github.io)'}), timeout=240) as r: ZIPC[url] = zipfile.ZipFile(io.BytesIO(r.read()))
            z = ZIPC[url]; n = 0; bad_shp = 0
            for sp in [q for q in z.namelist() if q.lower().endswith('.shp')]:
                b = sp[:-4]
                prj = next((q for q in z.namelist() if q.lower() == (b + '.prj').lower()), None)
                tr = Transformer.from_crs(CRS.from_wkt(z.read(prj).decode('utf8', 'ignore')) if prj else CRS.from_epsg(4326), 4326, always_xy=True)
                rd = shapefile.Reader(shp=io.BytesIO(z.read(sp)), dbf=io.BytesIO(z.read(b + '.dbf')), shx=io.BytesIO(z.read(b + '.shx')))
                fn = [f[0] for f in rd.fields[1:]]
                nf = next((f for f in fn if f in nfs or f.lower() in {x.lower() for x in nfs}), None)
                af = next((f for f in fn if f in afs or f.lower() in {x.lower() for x in afs}), None)
                tf = next((f for f in fn if f.lower() == str(opt.get('type', '')).lower()), None)
                if not nf: notice(f'US key {st}', f'{label}: no name field in {fn}'); continue
                bad_shp = 0
                def _each():   # Oct 29: one empty shape ('Polygon requires non-empty points', Mississippi WMAs) used to drop the WHOLE layer
                    nonlocal bad_shp
                    for i2 in range(len(rd)):
                        try: yield i2, rd.shape(i2), rd.record(i2)
                        except Exception: bad_shp += 1  # noqa: BLE001
                for i, shp, rec in _each():
                    a = dict(zip(fn, list(rec))); nm = str(a.get(nf) or '').strip()
                    if not nm or not shp.points: continue
                    for pat, rp in opt.get('sub') or []: nm = re.sub(pat, rp, nm, flags=re.I)
                    if tf:
                        tv = str(a.get(tf) or '').strip().lower()
                        kd = opt['tk'].get(tv) or ('wma' if opt.get('tk_re') and re.match(opt['tk_re'], tv) else None)
                        if not kd: continue
                        kk = {kd}
                    else: kk = {opt.get('kind')} - {None}
                    pts, parts = shp.points, list(shp.parts) + [len(shp.points)]
                    rs = []
                    for k2 in range(len(parts) - 1):
                        ring = pts[parts[k2]:parts[k2 + 1]]
                        xs, ys = tr.transform([q[0] for q in ring], [q[1] for q in ring])
                        rs.append([[round(x, 6), round(y, 6)] for x, y in zip(xs, ys)])
                    g = {'rings': rs}; k = kinds(nm) | kk
                    if _dup(have, (norm(nm), frozenset(k)), bbox(g)): continue
                    ZIPGEO.setdefault(pre, {})[f'{pre}{i}'] = [nm, [_fine(r2) for r2 in rs if len(r2) > 3]]   # R-G6 fine lines: 3 m, not 'every Nth point'
                    out.append({'OBJECTID': f'{pre}{i}', 'Unit_Nm': nm, 'Loc_Nm': '', 'Own_Type': own, 'Mang_Type': own, 'Mang_Name': pre.upper(), 'Loc_Mang': label,
                                'Des_Tp': '', 'GIS_Acres': _num(a.get(af) if af else 0), 'Category': 'Fee', '_bb': bbox(g), '_g': g, '_k': k})
                    n += 1
            if bad_shp: notice(f'US key {st}', f'{label}: {bad_shp} empty / broken shapes skipped (the rest read)')
            XCOUNT[pre] = XCOUNT.get(pre, 0) + n
            LAYERS_ZIP[pre] = [url, nf, label]
        except Exception as e: notice(f'US key {st}', f'{label} not read ({str(e)[:120]})')  # noqa: BLE001
    return out


LAYERS_ZIP = {}
ZIPGEO = {}   # prefix -> {id: [name, rings]}: saved as data/us-key/zip-<prefix>.json, because a zip has no live map to draw from


def extra_state(st, have, only=None):
    box = st_box(st)
    if not box: return []
    out = [] if only is not None else zip_state(st, have)
    for x in XS:
        pre, url, nf, af, kk, label = x[:6]
        if only is not None and pre not in only: continue
        own = x[6] if len(x) > 6 else 'FED'
        if len(x) > 7 and x[7] is not None and st not in x[7]: continue
        opt = x[8] if len(x) > 8 else {}      # Oct 25: state-GIS options: 'where' = the layer's own filter, 'water' = lake surfaces, not property lines
        try: url, nf, af, oidf = resolve(pre, url, nf, af)
        except Exception as e:  # noqa: BLE001
            notice(f'US key {st}', f'{label} layer not found ({e})'); continue
        off, n = 0, 0
        while True:
            q = {'where': opt.get('where') or '1=1', 'geometry': ','.join(map(str, box)), 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
                 'outFields': ','.join(q for q in (oidf, nf, af, opt.get('nm2')) if q), 'returnGeometry': 'true', 'outSR': 4326, 'f': 'json', 'resultOffset': off}
            try:
                j, pg = fetch_geo(url, q)
            except Exception as e:  # noqa: BLE001
                notice(f'US key {st}', f'{label} not read ({e})'); FAILED_READ.add(st); break
            fs = j.get('features', [])
            for f in fs:
                a = {k.lower(): v for k, v in (f.get('attributes') or {}).items()}
                nm = (a.get(nf.lower()) or '').strip()
                if not nm: continue
                # Oct 20: an 'easement' record is private land with public access, never joined by name alone. Oct 29 (Brandon 2:22 PM:
                # 'we are not here to correct POTA's mistakes, we show the boundaries of where they are'): when POTA numbered the
                # easement itself and a person named that record in overrides.json, it IS the park's outline (Buena Vista SWA)
                if re.search(r'easement', nm, re.I) and _nf(nm) not in {_nf(w) for o in OVR.values() for w in (o.get('join') or []) + (o.get('alias') or [])}: continue
                k = kinds(nm) | kk
                if opt.get('not_in') and norm(nm) in {norm(o['Unit_Nm']) for o in out if str(o['OBJECTID']).startswith(opt['not_in'])}: continue
                if not opt.get('where') and _dup(have, (norm(nm), frozenset(k)), bbox(f.get('geometry') or {})): continue   # Oct 25: a hand-filtered layer (NPS legal boundary) is kept even when PAD-US has the same name
                g = f.get('geometry') or {}
                nm2 = (a.get(opt['nm2'].lower()) or '').strip() if opt.get('nm2') else ''   # Oct 25: Ohio's readable names are a second field (ALT_NAME); the key reads Loc_Nm as a second name
                out.append({'OBJECTID': pre + str(a.get(oidf.lower())), 'Unit_Nm': nm, 'Loc_Nm': nm2 if nm2 != nm else '', 'Own_Type': own, 'Mang_Type': own, 'Mang_Name': pre.upper(),
                            'Loc_Mang': label, 'Des_Tp': '', 'GIS_Acres': _num(a.get(af.lower()) if af else 0), 'Category': 'Fee', '_bb': bbox(g), '_g': g, '_k': k,
                            **({'Water': 1} if opt.get('water') else {})})
                n += 1
            if not fs or (not j.get('exceededTransferLimit') and len(fs) < pg): break
            off += len(fs); time.sleep(.5)
        XCOUNT[pre] = XCOUNT.get(pre, 0) + n
    return out


# ------------------------------------------------------------------------------------------------ the shared scoring
# Oct 22 (Fable's review): one weighing of the evidence for every country, in kpc_match.py. This is the US side of it:
# it READS the names the US way and hands kpc_match plain facts. It runs in SHADOW next to the matcher above - its
# verdict is recorded wherever it disagrees, nothing it says changes a join - until the disagreements have been read.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kpc_match as KM  # noqa: E402
from kpc_save import save_json, save_text  # noqa: E402  (Oct 25 storage plan: write only when the content changed)


def name_clusters(recs):
    for a in recs: a['_nn'] = norm(a.get('Unit_Nm') or a.get('Loc_Nm') or '')
    return KM.name_clusters([(a['_nn'], a['_bb']) for a in recs])


# Oct 22 review (162 of 202 'check' cases were the SAME land the key already used): words that change between two
# agencies' names for one place - 'Christmas Rocks State / DEDICATED Nature Preserve', 'Chandler Wayside State Park' /
# 'Chandler State Wayside', 'Big Muddy National (Fish and) Wildlife Refuge', Madira Bickel Mound State HISTORIC /
# ARCHAEOLOGICAL Site, BLM 'Baldy Mountain' / 'Baldy Mountain Facility Area'. Shadow only, measured before it counts.
FILL = re.compile(r"\b(blm|special recreation management area|extensive recreation management area|recreation management area|dedicated|heritage|historic|historical|archaeological|archeological|fish and|state|national|"
                  r"facility area|recreation site|campground|campsites?( \d+)?|trailhead|wayside|park|parks|site|"
                  r"educational|wildlife refuge|nature preserve|natural area|recreation area|wildlife area|"
                  r"wildlife management area|wma|sra|shp|sp)\b")
def _fill(x):
    t = re.sub(r"[’'`ʻʼ‘]", '', str(x or '').lower().replace('&', ' and '))
    t = ' '.join(ABBR.get(w, w) for w in re.sub(r'[^a-z0-9 ]', ' ', t).split())
    t = re.sub(r'\s+', ' ', FILL.sub(' ', t)).strip()
    return t if len(t) >= 4 else ''
TAGS = [('memorial', r'national memorial'), ('refuge', r'wildlife refuge|\bnwr\b'), ('wilderness', r'wilderness(?! study)'),
        ('water', r'reservoir|fishing lake'), ('beach', r'\bbeach\b'), ('access', r'fishing access|access site'),
        ('wildforest', r'wild forest'), ('stateforest', r'state forest'), ('hatchery', r'hatchery')]
def _tags(x):
    x = str(x or '').lower(); return {k for k, r in TAGS if re.search(r, x)}


def score_park(name, typ, la, lo, recs, clusters):
    """The shared module's verdict for one park: ('join'|'check'|'none', best_group, runner_group)."""
    kp = kinds(name) | kinds(typ)
    cands = []
    for a in recs:
        if la is not None and not near(la, lo, a['_bb'], .6): continue
        nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
        if KM.is_admin(nm) or KM.is_admin(a.get('Loc_Nm')): continue          # an office boundary is never a park
        ak = a['_k'] if kinds(nm) else set()         # a kind that came only from a designation code says nothing
        kind_ok = same_kind(kp, ak) and ('nfh' in kp) == ('nfh' in ak) and \
            bool(re.search(r'\btrail\b', name, re.I)) == bool(re.search(r'\btrail\b', nm, re.I))
        # the SAME name reads identically; one that only STARTS the same way is similar words ('Colorado River' /
        # 'Colorado River Island', 'Dallas County' / 'Dallas County Public Fishing Lake')
        def same(x): return bool(x) and (norm(name) == norm(x) or exact_name(name, x) or (_fill(name) and _fill(name) == _fill(x)))
        ex = same(nm) or same(a.get('Loc_Nm'))
        # Oct 22 review: two names that each say a DIFFERENT kind of place (Pearl Harbor National Memorial / Pearl Harbor
        # National Wildlife Refuge, Hells Canyon Reservoir / Hells Canyon Wilderness, Crystal Lake State Forest / Crystal
        # Lake WILD Forest) are not joined by name: refused outright when the pin is not inside, a person's look when it is
        tp, ta = _tags(name), _tags(nm)
        clash = bool(tp and ta and not (tp & ta))
        if clash and not (la is not None and near(la, lo, a['_bb'], 0) and KM.inside(la, lo, a['_g'])):
            kind_ok = False
        wd = (not ex) and bool(same_words(name, nm, kp, ak) or same_name(name, nm)
                               or (a.get('Loc_Nm') and same_name(name, a['Loc_Nm'])))
        holds = la is not None and near(la, lo, a['_bb'], 0) and KM.inside(la, lo, a['_g'])
        if not (ex or wd or holds): continue
        cands.append({'a': a, 'nn': a.get('_nn'), 'bb': a['_bb'], 'kind_ok': kind_ok, 'kind_clash': clash, 'side_ok': _side(name) == _side(nm), 'name_exact': ex,
                      'name_unique': clusters.get(a.get('_nn'), 1) == 1, 'name_words': wd,
                      'pin': (la, lo) if la is not None else None, 'g': a['_g'], 'acres': a.get('GIS_Acres') or 0})
        # PIN_JOIN stays off in the US: the names CAN be read here, and a pin alone mostly finds the forest around
        # the park (Brainard Lake Recreation Area -> all of Roosevelt National Forest, Oct 22)
    return KM.choose(cands)


RD = {}
_TR = []
def transfers():
    """data/park-transfers.json: parks handed to another agency that keep their POTA number (Oct 28)."""
    if not _TR:
        try: _TR.append(json.load(open('data/park-transfers.json')).get('parks') or {})
        except Exception: _TR.append({})  # noqa: BLE001
    return _TR[0]


def outline_dates(p, recs):
    """Rule B7 (boundary review #2): 'read' = the oldest day this park's joined land was read from its agency; 'src' = what it
    came from (PAD-US version, or the agency layer). Only changes when a saved copy is re-read, so the key does not churn."""
    if not p.get('m'): return
    if not RD:
        if CMODE != 'only' and FIELDS is None: fields()   # reads the PAD-US version once
        RD.update({_oid(a): a.get('rd') or time.strftime('%Y-%m-%d') for a in recs}); RD['_'] = ''
    ds = [RD.get(str(x[0])) for x in p['m'] if RD.get(str(x[0]))]
    if ds: p['read'] = min(ds)
    p['src'] = sorted({PADVER[0] if isinstance(x[0], int) else (re.match(r'[a-z]+', str(x[0])) or [''])[0] for x in p['m']})


def split_places(m, recs, la, lo, ref, P):
    """(joined records to keep, records moved to 'check', far places kept [names]): see run(). Places = records whose boxes
    touch (0.02 degree)."""
    gs = {_oid(a): a for a in recs}
    items = [(x, (gs.get(str(x[0])) or {}).get('_bb')) for x in m]
    if any(b is None for _, b in items): return m, [], []
    par = list(range(len(items)))
    def f(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if not KM._apart(items[i][1], items[j][1], .02): par[f(i)] = f(j)
    groups = {}
    for i, (x, b) in enumerate(items): groups.setdefault(f(i), []).append((x, b))
    if len(groups) < 2: return m, [], []
    def box(g): return [min(b[0] for _, b in g), min(b[1] for _, b in g), max(b[2] for _, b in g), max(b[3] for _, b in g)]
    def size(bb): return max(bb[2] - bb[0], bb[3] - bb[1])
    def gap(b1, b2): return max(b1[0] - b2[2], b2[0] - b1[2], b1[1] - b2[3], b2[1] - b1[3], 0)
    def pin_d(bb): return max(bb[0] - lo, lo - bb[2], bb[1] - la, la - bb[3], 0)
    G = [(g, box(g)) for g in groups.values()]
    holds = [k for k, (g, bb) in enumerate(G) if any(inside(la, lo, (gs.get(str(x[0])) or {}).get('_g')) for x, _ in g)]
    home = holds[0] if holds else min(range(len(G)), key=lambda k: pin_d(G[k][1]))
    keep, moved, far = [], [], []
    for k, (g, bb) in enumerate(G):
        d = gap(bb, G[home][1])
        if k == home or d <= max(.1, 2 * max(size(bb), size(G[home][1]))): keep += [x for x, _ in g]; continue
        other = next((r2 for r2, v in P.items() if r2 != ref and len(v) > 6 and v[5] is not None and any(same_name(v[0], x[1]) for x, _ in g)
                      and any(inside(v[5], v[6], (gs.get(str(x[0])) or {}).get('_g')) for x, _ in g)), None)
        if other: moved += [[x[0], x[1], x[2], f'same name, another place ~{round(d * 100)} km away that holds the pin of {other}: not joined (a person checks)'] for x, _ in g]
        else: keep += [x for x, _ in g]; far.append(f'{g[0][0][1]} (~{round(d * 100)} km from the rest)')
    return keep, moved, far


def cache_file(st): return CACHE / f'US-{st}.json.gz'


def save_cache(st, recs, seen):
    """Everything the matcher needs, so a rule can be tested without the network. Outlines to ~1 m."""
    CACHE.mkdir(parents=True, exist_ok=True)
    rows = []
    for a in recs:
        r = {k: v for k, v in a.items() if not k.startswith('_')}
        r['_r'] = [[[round(pt[0], 5), round(pt[1], 5)] for pt in ring if len(pt) >= 2] for ring in rings(a.get('_g'))]
        r['_k'] = sorted(a.get('_k') or [])
        r['rd'] = a.get('rd') or time.strftime('%Y-%m-%d')   # the day this record was read from its agency (rule B7)
        rows.append(r)
    blob = {'st': st, 'saved': time.strftime('%Y-%m-%d'), 'detail': DETAIL, 'seen': seen, 'recs': rows}
    with gzip.open(cache_file(st), 'wt', encoding='utf-8') as f:
        json.dump(blob, f, separators=(',', ':'))
    CACHE_SAVED.append(st)


def load_cache(st):
    p = cache_file(st)
    if not p.exists(): return None
    try:
        with gzip.open(p, 'rt', encoding='utf-8') as f: blob = json.load(f)
    except Exception as e:  # noqa: BLE001
        notice(f'US key {st}', f'saved shapes unreadable ({e}); fetching'); return None
    recs = []
    for r in blob.get('recs') or []:
        a = {k: v for k, v in r.items() if k not in ('_r', '_k')}
        a['_g'] = {'rings': r.get('_r') or []}
        a['_bb'] = bbox(a['_g'])
        a['_k'] = set(r.get('_k') or [])
        a['rd'] = r.get('rd') or blob.get('saved') or ''
        recs.append(a)
    return recs, blob.get('seen', len(recs)), blob.get('detail')


def out_date(): return time.strftime('%Y-%m-%d')


# Sites (Oct 18 review): an airstrip, trailhead, hatchery, byway, BLM recreation site… has no outline of its own in any official map;
# when the only official land found is the bigger place AROUND its pin, it is not a 'check' case: we keep that land as 'a' (sits on), never joined.
SITE = re.compile(r'airstrip|interpretive site|historic preservation site|trail ?head|day use|recreation site|\bohv\b|off.highway|byway|backway|historic(al)? trail|'
                  r'historical monument|multiple use area|hatchery|historic area|designated routes?|desigated|desingated|staging area|camping area|campground|boat (ramp|launch)|'
                  r'rock ?hounding|petroglyph|kilns|^blm |\bblm\b.*recreation management area|scenic drive|overlook|wayside|picnic', re.I)

# Reviewed by hand (Oct 18 on): data/us-key/overrides.json {ref: {join: [objectid or exact name], no: [objectid or exact name], why: '...'}}.
# 'join' adds that official land (it must be within ~0.6° of the pin), 'no' keeps a piece out; the bot follows it on every rerun.
def _nf(t):   # hand decisions match names whatever way the accents are stored (Oct 18: SG̲áan K̲ínghlas-Bowie never matched)
    import unicodedata; return unicodedata.normalize('NFC', str(t or '')).strip().casefold()
try: OVR = json.load(open(OUT / 'overrides.json')).get('parks', {})
except Exception: OVR = {}  # noqa: BLE001
def _oid(a): return str(a['OBJECTID'])


DBG = set((os.environ.get('DEBUG_REFS') or '').split())   # Oct 29 (chat 2): trace these parks through every step (a debug run saves nothing)
def dbg(ref, stage, x):
    if ref in DBG: print(f"::notice title=TRACE {ref} {stage}::{str(x)[:900]}", flush=True)


PIN = {}
def pins():
    # 20 state park files have no lat/lon (older format): fall back to the site index, then locations.json
    if PIN: return PIN
    try:
        for r in json.load(open('data/parkinfo/index.json')).get('rows', []):
            if len(r) > 4 and r[3] is not None: PIN[r[0]] = (r[3], r[4])
    except Exception: pass  # noqa: BLE001
    try:
        for r in json.load(open('locations.json')):
            if r[0] == 'POTA' and r[1] not in PIN: PIN[r[1]] = (r[3], r[4])
    except Exception: pass  # noqa: BLE001
    return PIN


def run(st):
    try: P = json.load(open(f'data/parkinfo/US-{st}.json'))['parks']
    except Exception: notice(f'US key {st}', 'no park file, skipped'); return None  # noqa: BLE001
    try: P = {k: v for k, v in P.items() if k not in set(json.load(open('data/retired-refs.json')).get('refs') or {})}   # Oct 29: retired numbers leave the key (issue #17)
    except Exception: pass  # noqa: BLE001
    got = load_cache(st) if CMODE in ('use', 'only') else None
    if got is None and CMODE == 'only':
        notice(f'US key {st}', 'no saved shapes yet; skipped (saved-copy-only run)'); return None
    if got is not None:
        recs, seen, used_detail = got; CACHE_USED.append(st)
        # Oct 25: a saved copy made before a layer was added (data/state-gis.json grows) never had that layer's land, so the
        # nightly rebuild could not join it. Top the copy up: read live only the layers it has no records from, add, re-save.
        if CMODE == 'use':
            present = {re.match(r'[a-z]*', str(a.get('OBJECTID'))).group(0) for a in recs}
            missing = {x[0] for x in XS if (len(x) <= 7 or x[7] is None or st in x[7]) and x[0] not in present}
            if missing:
                add = extra_state(st, _have(recs), only=missing)
                if add:
                    recs += add
                    notice(f'US key {st}', f'saved copy topped up with {len(add)} areas from {len({str(a["OBJECTID"]).rstrip("0123456789") for a in add})} newer layer(s)')
                    if st not in FAILED_READ: save_cache(st, recs, seen)
    else:
        recs, seen = pad_state(st)
        recs += fws_state(st, {norm(a.get('Unit_Nm') or '') for a in recs if a.get('Mang_Name') == 'FWS'})
        recs += extra_state(st, _have(recs))
        used_detail = DETAIL
        old = load_cache(st) if st in FAILED_READ else None
        # only when this read actually came back SHORT (a source that fails every time is already missing from the
        # saved copy too, and must not freeze the state on an old copy forever)
        if old is not None and len(recs) < .97 * len(old[0]):
            notice(f'US key {st}', f'a map did not answer ({len(recs)} areas read, {len(old[0])} saved), so the saved copy was used (nothing dropped)')
            recs, seen, used_detail = old; CACHE_USED.append(st)
        elif CMODE in ('use', 'refresh') and not (st in FAILED_READ and old is None and cache_file(st).exists()): save_cache(st, recs, seen)
    parks, used = {}, set()
    RD.clear()
    clusters = name_clusters(recs)
    for ref, r in sorted(P.items()):
        name, typ, la, lo = r[0], r[2] if len(r) > 2 else '', r[5] if len(r) > 5 else None, r[6] if len(r) > 6 else None
        if la is None and ref in pins(): la, lo = pins()[ref]
        kp = kinds(name) | kinds(typ)
        m, c = [], []
        for a in recs:
            nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
            close = la is None or near(la, lo, a['_bb'], .6)
            if not close: continue
            if bool(kp) != bool(a['_k']) and la is not None and not near(la, lo, a['_bb'], .1): close = False   # one name has no kind word: must be close by
            if not close: continue
            if a.get('Water') and (la is None or not near(la, lo, a['_bb'], .02)): continue   # Oct 25: lake names repeat (Washington has dozens of Lost Lakes): a lake surface joins only right at the pin
            how = join_how(name, kp, a, near(la, lo, a['_bb'], .1) if la is not None else False)
            if how and a.get('Water'): how += ' · water outline only'
            if how:
                m.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), how])
        ov = OVR.get(ref) or {}
        if ov:
            no = {str(x) for x in ov.get('no', [])}
            m = [x for x in m if str(x[0]) not in no and _nf(x[1]) not in {_nf(y) for y in no}]
            for want in ov.get('join', []):
                # Oct 27 (boundary review #3): PAD-US gives its records NEW ids in each version. A hand join by id whose id is gone
                # is found again by its fingerprint (name + acres within 10%, near the pin), saved with it in overrides.json 'fp'
                if not any(_oid(a) == str(want) for a in recs) and str(want) in (ov.get('fp') or {}):
                    fn, fa = ov['fp'][str(want)][:2]
                    want = next((_oid(a) for a in recs if _nf(a.get('Unit_Nm') or a.get('Loc_Nm') or '') == _nf(fn) and (la is None or near(la, lo, a['_bb'], .6))
                                 and abs((a.get('GIS_Acres') or 0) - (fa or 0)) <= max(20, .1 * (fa or 0))), want)
                for a in recs:
                    nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
                    if (_oid(a) == str(want) or _nf(nm) == _nf(want)) and _oid(a) not in no and (la is None or near(la, lo, a['_bb'], .6)) and not any(str(x[0]) == _oid(a) for x in m):   # Oct 25: an id in 'no' is never re-added by a same-name join
                        m.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), 'reviewed-approx' if ov.get('approx') else 'reviewed'])   # Oct 22: 'approx' = a person picked the closest official land, but it is bigger or shaped differently: the tools label it Approximate
        # Oct 29 (chat 8's name-mismatch list, Brandon 'help the boundaries'): 'alias' = another name the official layer uses for this
        # park. An alias joins ONLY with the sure-match test: same name as the alias AND the POTA pin inside that record's outline
        # 'alias_all' = a name PREFIX for a park the layer splits into units (Whitewater WMA: Main Branch Unit, …): when one of
        # them holds the pin or lies within ~3 km of it, every unit with that prefix within ~30 km joins (chat 2 + chat 8, Oct 29)
        if not m and la is not None and ov.get('alias_all'):
            for pre in ov['alias_all']:
                units = [a for a in recs if _nf(a.get('Unit_Nm') or a.get('Loc_Nm') or '').startswith(_nf(pre)) and near(la, lo, a['_bb'], .3)]
                if any(inside(la, lo, a['_g']) or near(la, lo, a['_bb'], .03) for a in units):
                    for a in units: m.append([a['OBJECTID'], a.get('Unit_Nm') or a.get('Loc_Nm') or '', round(a.get('GIS_Acres') or 0), f'alias units: {pre}'])
        if not m and la is not None and ov.get('alias'):
            for al in ov['alias']:
                for a in recs:
                    nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
                    if _nf(nm) == _nf(al) and _oid(a) not in {str(x) for x in ov.get('no', [])} and near(la, lo, a['_bb'], .05) and inside(la, lo, a['_g']):
                        m.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), f'alias name (pin inside): {al}'])
        if ref in DBG:
            wants = list(ov.get('join', [])) + list(ov.get('alias', []))
            seen_ = [[_oid(a), a.get('Unit_Nm') or a.get('Loc_Nm'), round(a.get('GIS_Acres') or 0), near(la, lo, a['_bb'], .6) if la is not None else None,
                      inside(la, lo, a['_g']) if la is not None and a.get('_g') else None] for a in recs
                     if _oid(a) in [str(w) for w in wants] or _nf(a.get('Unit_Nm') or a.get('Loc_Nm') or '') in {_nf(w) for w in wants}]
            dbg(ref, 'A after joins+overrides', {'pin': [la, lo], 'm': [x[:4] for x in m], 'wants': wants, 'records with that id/name [id,name,ac,within0.6,pin inside]': seen_[:8], 'n_recs': len(recs)})
        site = []
        if not m and la is not None:
            # unsure: not joined, only listed so a person can look
            for a in recs:
                nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
                if not near(la, lo, a['_bb'], .02): continue
                w1, w2 = words(name), words(nm)
                share = len(w1 & w2) / max(1, min(len(w1), len(w2))) if w1 and w2 else 0
                if same_name(name, nm): why = 'same name, different kind of place'
                elif share >= .6: why = 'similar name'
                elif inside(la, lo, a['_g']): why = 'the POTA pin is inside it (different name)'
                else: continue
                c.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), why])
            c.sort(key=lambda x: (x[3] != 'similar name', x[3] != 'same name, different kind of place', -x[2])); c = c[:6]
            # Oct 22 review: when the ONLY land found is a differently named place around the pin (a Wild and Scenic river inside a
            # national preserve, a trail in a forest), the park has no outline of its own on file. That is an answer, not a
            # question: it is kept as 'sits on' (shown in the tools) and leaves the waiting list. 550 of 918 were this.
            if c and all(x[3].startswith('the POTA pin is inside') for x in c):
                site = sorted(c, key=lambda x: x[2])[:2]; c = []
            if ov.get('site'): site, c = sorted(c, key=lambda x: x[2])[:2] or site, []
            if ov.get('none'): c = []   # a person looked: no official outline for this park in any map we read
            # NAME_JOIN, the US way (Oct 24, step 2 of the Oct 22 plan: 'cross-port the rules each script is missing').
            # The world key joins a 'same name, different kind of place' candidate when every such candidate is one
            # and the same official area. Here the kind words are English on both sides and usually mean it: a lake
            # WMA and the state park on the same lake really are two places (Yatesville, Oct 17). So the US takes the
            # join only when the one same-named area also HOLDS the park's pin (or the pin sits at its edge): an
            # Oregon 'State Recreation Site' filed by PAD-US as a state park, a SC heritage preserve that is the WMA.
            if not m and c and NAME_JOIN and not ov.get('none') and not ov.get('site'):
                sn = [x for x in c if x[3] == 'same name, different kind of place' and str(x[0]) not in {str(y) for y in ov.get('no', [])}]   # Oct 25: a person's 'no' wins here too
                if sn and len({_nf(x[1]) for x in sn}) == 1:
                    gs = {_oid(a): a for a in recs}
                    hold = [x for x in sn if str(x[0]) in gs and rings(gs[str(x[0])].get('_g'))
                            and (inside(la, lo, gs[str(x[0])]['_g']) or near(la, lo, gs[str(x[0])]['_bb'], .005))]
                    if hold and not any(_tags(name) and _tags(x[1]) and not (_tags(name) & _tags(x[1])) for x in hold):   # a memorial is never the refuge
                        m = [[x[0], x[1], x[2], 'same name (POTA writes the kind into the name) + pin inside'] for x in hold]
                        c = [x for x in c if x not in hold]; site = []
        # Oct 27 (Fable's boundary review #4, HQ GO): two different places with the same name and kind within reach of the pin
        # must not become ONE park. Joined records are grouped into places (pieces that link up are one place). A far place
        # (further than twice its own size and over ~10 km) that holds ANOTHER POTA park's pin with the same name belongs to
        # that park: it goes to 'check'. Any other far place stays joined (a park's sections can lie 40 km apart: James M.
        # Robb - Colorado River SP) but is listed for a person ('far_place', observations log). A person's join is never split.
        far_place = []
        if len(m) > 1 and la is not None and not any(str(x[3]).startswith('reviewed') for x in m):
            m, far_places, far_place = split_places(m, recs, la, lo, ref, P)
            c += far_places
        for x in m: used.add(x[0])
        # SHADOW: what the shared scoring says, recorded only where it disagrees with the join above
        shadow = None
        # Oct 27 (boundary review #10, HQ GO): the shared scoring ran in shadow since Oct 22 and never decided a join; it is OFF
        # (SHADOW=1 turns it back on for a measuring run). The decision path is join_how() + the golden cases.
        if SHADOW and not (ov.get('join') or any(str(x[3]).startswith('reviewed') for x in m)):        # a person's decision is never second-guessed
            try:
                v, best, runner = score_park(name, typ, la, lo, recs, clusters)
                ids_now = {str(x[0]) for x in m}
                ids_new = {_oid(c['a']) for c in best[2]} if (best and v == 'join') else set()
                if bool(ids_now) != (v == 'join') or (ids_now and ids_new and not ids_now & ids_new):
                    shadow = {'v': v, 'pts': best[0] if best else None, 'why': best[1] if best else [],
                              'to': (best[2][0]['a'].get('Unit_Nm') or best[2][0]['a'].get('Loc_Nm')) if best else None,
                              'vs': ((runner[2][0]['a'].get('Unit_Nm') or '') + f' ({runner[0]})') if runner else None}
            except Exception as e:  # noqa: BLE001
                shadow = {'v': 'error', 'why': [str(e)[:120]]}
        # IS THE BOUNDARY WHERE IT SHOULD BE? (Brandon Oct 21: 'check see if the boundaries are where they
        # supposed to be'.) A name can match confidently and still be the wrong place, and until now nothing
        # tested that - a joined park was simply counted as a success. So: does the park's own pin actually
        # fall inside the land we joined it to? 'far' = it does not, and that join wants looking at.
        if m and la is not None:
            gs = {_oid(a): a for a in recs}
            mine = [gs[str(x[0])] for x in m if str(x[0]) in gs]
            # Does the joined land have a shape at all? Some services hand back records with no rings, and
            # then 'the pin is outside' means nothing - it is the CHECK that is blind, not the match.
            shaped = [a for a in mine if rings(a.get('_g'))]
            hit = any(inside(la, lo, a['_g']) for a in shaped)
            if not hit:
                why = ('no shape to check against' if not shaped else
                       'edge' if any(near(la, lo, a['_bb'], .02) for a in shaped) else 'well outside')
                parks[ref] = {'n': name, 't': typ, 'm': sorted(m, key=lambda x: -x[2]), 'c': c, 'far': why}
                if shadow: parks[ref]['shadow'] = shadow
                # THE ONE THAT CAN BE FIXED AUTOMATICALLY: is there another area with the SAME NAME that
                # does contain the pin? Then we joined the wrong one of two places sharing a name, and the
                # right one is right here. Recorded, not acted on, until a person has looked at a few.
                if shaped:
                    jn = {_nf(x[1]) for x in m}
                    # Oct 25 review of the first 9 'swaps': 5 were the SAME land in two maps (PAD-US + the state's own copy),
                    # 2 a different KIND of place with the same name (herd area vs recreation area / study area), 1 an office
                    # name shared by two areas. A swap must now be a different place: land apart from the joined land, a
                    # kind that fits the park, and not an office boundary.
                    def apart(b): return bool(b) and all(b[2] < q['_bb'][0] or b[0] > q['_bb'][2] or b[3] < q['_bb'][1] or b[1] > q['_bb'][3] for q in shaped if q['_bb'])
                    swap = [a for a in recs if _nf(a.get('Unit_Nm') or a.get('Loc_Nm') or '') in jn
                            and _oid(a) not in {str(x[0]) for x in m}
                            and not KM.is_admin(a.get('Unit_Nm') or a.get('Loc_Nm') or '')
                            and same_kind(kp, a['_k']) and apart(a['_bb'])
                            and rings(a.get('_g')) and inside(la, lo, a['_g'])]
                    if swap:
                        parks[ref]['swap'] = [[a['OBJECTID'], a.get('Unit_Nm') or a.get('Loc_Nm') or '',
                                               round(a.get('GIS_Acres') or 0)] for a in swap[:2]]
                if site: parks[ref]['a'] = site
                if far_place: parks[ref]['far_place'] = far_place
                outline_dates(parks[ref], recs)
                continue
        parks[ref] = {'n': name, 't': typ, 'm': sorted(m, key=lambda x: -x[2]), 'c': c}
        if far_place: parks[ref]['far_place'] = far_place
        outline_dates(parks[ref], recs)
        if shadow: parks[ref]['shadow'] = shadow
        if site: parks[ref]['a'] = site
    # Oct 29 (chat 8, 'wrong joins solved'): a record joined to two or more parks by NAME alone (Robert Moses Long Island +
    # Thousand Islands, NY county forests) stays only with the parks it is NEAR: a claim from a park whose pin is more than
    # 15 km from the record is dropped when another park's pin sits within 2 km of it. Hand joins ('reviewed') are never dropped.
    for r_ in DBG & set(parks): dbg(r_, 'B after the park loop', {k: parks[r_].get(k) for k in ('m', 'c', 'far', 'a')})
    rb = {_oid(a): a['_bb'] for a in recs if a.get('_bb')}
    # Fable Oct 29: a MULTIPART record (Lost Nation = St. Lawrence + Allegany forests in one record) has a bbox that spans the
    # state, so every pin looks 'near' it: measure to the nearest PART (ring) instead
    rparts = {}
    for a in recs:
        rr = [r for r in rings(a.get('_g')) if len(r) > 2]
        if len(rr) > 1: rparts[_oid(a)] = [[min(p[0] for p in r), min(p[1] for p in r), max(p[0] for p in r), max(p[1] for p in r)] for r in rr]
    pinx = {}
    for ref in parks:
        r = P.get(ref) or []
        la_, lo_ = (r[5], r[6]) if len(r) > 6 else (None, None)
        if la_ is None and ref in pins(): la_, lo_ = pins()[ref]
        if la_ is not None: pinx[ref] = (la_, lo_)
    def _dk1(ref, b):
        la_, lo_ = pinx[ref]
        return math.hypot(max(0, b[0] - lo_, lo_ - b[2]) * 111.32 * math.cos(math.radians(la_)), max(0, b[1] - la_, la_ - b[3]) * 110.57)
    _cur = [None]
    def _dkm(ref, b):   # b = the record's bbox; the distance is to its nearest part when the record has several
        ps = rparts.get(_cur[0])
        return min(_dk1(ref, q) for q in ps) if ps else _dk1(ref, b)
    claim = {}
    for ref, p in parks.items():
        for x in p.get('m') or []: claim.setdefault(str(x[0]), set()).add(ref)
    pruned = []
    for rid, refs in claim.items():
        if len(refs) < 2 or rid not in rb: continue
        _cur[0] = rid
        close = {r for r in refs if r in pinx and _dkm(r, rb[rid]) <= 2}
        if not close: continue
        for r in refs - close:
            if r not in pinx or _dkm(r, rb[rid]) <= 15: continue
            if any(str(x[0]) == rid and str(x[3]).startswith('reviewed') for x in parks[r]['m']): continue
            parks[r]['m'] = [x for x in parks[r]['m'] if str(x[0]) != rid]
            parks[r].setdefault('not_mine', []).append([rid, sorted(close)[0], round(_dkm(r, rb[rid]))]); pruned.append(f'{r} ({round(_dkm(r, rb[rid]))} km)')
    if pruned: notice(f'US key {st}', f"{len(pruned)} name-only joins dropped (the record belongs to a park next to it): {', '.join(pruned[:12])}")
    for r_ in DBG & set(parks): dbg(r_, 'C after the name-only prune', {k: parks[r_].get(k) for k in ('m', 'not_mine')})
    # Fable + chat 8 Oct 29 (rule B12, part-level clipping): a multipart record still claimed by two or more parks whose pins sit
    # near DIFFERENT parts (Robert Moses Long Island vs Thousand Islands): each park keeps only the parts within 2 km of its pin,
    # written as part boxes in 'parts' {record id: [[w, s, e, n], ...]}; the 2-fer line reads only those parts
    claim = {}
    for ref, p in parks.items():
        for x in p.get('m') or []: claim.setdefault(str(x[0]), set()).add(ref)
    clipped = []
    for rid, refs in claim.items():
        ps = rparts.get(rid)
        # only small multipart records (<= 6 parts: NY county-bracket forests, Robert Moses, Truman Home + Farm, San Juan Island
        # camps); a 500-part national forest is not cut to the bit near a pin. Parts near the pins must not overlap, and the
        # pins must be more than 15 km apart (the same distance as the prune above)
        if len(refs) < 2 or not ps or len(ps) > 6 or any(r not in pinx for r in refs): continue
        nearp = {r: [i for i, q in enumerate(ps) if _dk1(r, q) <= 2] for r in refs}
        if any(not v for v in nearp.values()): continue
        rl = sorted(refs)
        if any(set(nearp[a_]) & set(nearp[b_]) or _dk1(a_, [pinx[b_][1], pinx[b_][0], pinx[b_][1], pinx[b_][0]]) <= 15
               for k_, a_ in enumerate(rl) for b_ in rl[k_ + 1:]): continue
        for r, v in nearp.items():
            if len(v) == len(ps) or any(str(x[0]) == rid and str(x[3]).startswith('reviewed') for x in parks[r]['m']): continue
            parks[r].setdefault('parts', {})[rid] = [[round(c, 4) for c in ps[i]] for i in v]
            clipped.append(f'{r} ({len(v)} of {len(ps)} parts)')
    if clipped: notice(f'US key {st}', f"{len(clipped)} parks given only their own parts of a shared multipart record: {', '.join(clipped[:12])}")
    # Oct 29 10:40 AM: the 'agency layer has nothing there' cut (plan 2.7) was TAKEN OUT the same morning: it cut REAL tracts of
    # spread-out parks (Florida Keys WA 20 of 235 pieces, Tanana Valley SF 63 of 92, US-0150 242 of 249) because a state layer
    # can be partial. Brandon: 'if it is a tract that belongs to the park NEVER delete it'. Far pieces are now only HELD + checked
    # in the 2-fer line (kpc_fers_far_hold.py / kpc_fers_far_check.py), never cut from an outline by distance.
    # Oct 29 (HQ 10:40 AM, Brandon 10:39 AM GO: 'wetland districts = owned tracts only'): a Wetland Management District (and any
    # scattered-tract FWS park the same way) = ALL the tracts the Fish and Wildlife Service OWNS in fee in that district, from its
    # own realty layer (INTTYPE1 = 'F'), one multi-part outline; EASEMENT tracts (private farmland) are never part of it
    wmd = [ref for ref, p in parks.items() if re.search(r'wetland management district', p.get('n') or '', re.I) and not p.get('m')]
    nwmd = 0
    for ref in wmd:
        core = re.sub(r'\s*(wpa\s+)?wetland management district.*$', '', parks[ref]['n'], flags=re.I).strip().upper().replace("'", "''")
        if not core: continue
        # Oct 29 noon probe of the FWS realty layer: the district is the tract's COMPLEX (CMPXNAME 'KULM WETLAND MANAGEMENT
        # DISTRICT'), each tract is a county Waterfowl Production Area (RSL_TYPE 'WPA'), and OWNED tracts are INTTYPE1 'O'
        # ('E' = easement on private land: never part of the outline). There is no 'F' code (the first try joined 0 of 5).
        q = {'where': f"UPPER(CMPXNAME) LIKE '%{core}%WETLAND MANAGEMENT DISTRICT%' AND RSL_TYPE = 'WPA' AND INTTYPE1 = 'O'",
             'outFields': 'OBJECTID,ORGNAME,UNITNAME,CMPXNAME,INTTYPE1,SUM_GISACRES', 'returnGeometry': 'true', 'outSR': 4326, 'f': 'json'}
        fs, off_, bad_ = [], 0, False
        while True:
            try: j, _pg = fetch_geo(FWS, dict(q, resultOffset=off_))
            except Exception as e: notice(f'US key {st}', f'{ref} wetland district tracts not read ({str(e)[:60]})'); bad_ = True; break  # noqa: BLE001
            got_ = (j or {}).get('features') or []
            fs += [f for f in got_ if (f.get('geometry') or {}).get('rings')]
            if not got_ or (not (j or {}).get('exceededTransferLimit') and len(got_) < _pg): break
            off_ += len(got_); time.sleep(.5)
        if bad_: continue
        if not fs: continue
        m = []
        for f in fs:
            a = f.get('attributes') or {}; g = f.get('geometry') or {}
            rec = {'OBJECTID': 'fws' + str(a.get('OBJECTID')), 'Unit_Nm': ((a.get('UNITNAME') + ' WPA, ') if a.get('UNITNAME') else '') + (a.get('ORGNAME') or '').title(), 'Loc_Nm': '', 'Own_Type': 'FED', 'Mang_Type': 'FED',
                   'Mang_Name': 'FWS', 'Loc_Mang': 'U.S. Fish & Wildlife Service (own realty map, fee tracts)', 'Des_Tp': '', 'GIS_Acres': a.get('SUM_GISACRES') or 0,
                   'Category': 'Fee', '_bb': bbox(g), '_g': g, '_k': {'nwr'}}
            recs.append(rec)
            m.append([rec['OBJECTID'], rec['Unit_Nm'], round(rec['GIS_Acres'] or 0), 'reviewed: the district = FWS fee (owned) tracts only, easements left out (Brandon Oct 29)'])
        parks[ref]['m'] = sorted(m, key=lambda x: -x[2]); parks[ref].pop('c', None); nwmd += 1
    if wmd: notice(f'US key {st}', f'{nwmd} of {len(wmd)} wetland districts joined to their FWS-owned (fee) tracts')
    for r_ in DBG & set(parks): dbg(r_, 'D before rule G', {k: parks[r_].get(k) for k in ('m', 'parts')})
    # RULE SHEET G (one boundary pipeline; Brandon Oct 29 12:09 PM 'implement this now', rulings 12:14 + 12:18; notes/mapping.md):
    # G-1 the AGENCY'S OWN RECORD that names the park is the proof and joins at ANY distance (pins can be wrong). A piece matched
    # only by SIMILAR words ('words', 'name (designation code ignored)') must prove its place: the POTA pin inside it or within
    # 100 m, or the piece within 2 km of a piece that already passed; otherwise it is HELD (moved to 'c', never drawn).
    # A pin well outside its official outline never blocks the outline: the park goes on the 'POTA pin may be wrong' list.
    # Every park gets ONE grade 'g': official / approximate / pin (G-2: a piece-only outline drawn as the agency has it = official).
    WEAK = ('words', 'name (designation code ignored)')
    try:
        from shapely.geometry import Polygon as _GP, Point as _GPt
        _shp = True
    except Exception: _shp = False  # noqa: BLE001
    gs_ = {_oid(a): a for a in recs}
    def _scaled(a, lat0):
        k = math.cos(math.radians(lat0))
        out_ = []
        for r in rings(a.get('_g')):
            if len(r) > 3:
                try: out_.append(_GP([(x * 111.32 * k, y * 110.57) for x, y in r]).buffer(0))
                except Exception: pass  # noqa: BLE001
        return out_
    def _gap_km(a, b, lat0):
        ba, bb_ = a.get('_bb'), b.get('_bb')
        if not ba or not bb_: return 1e9
        k = math.cos(math.radians(lat0))
        bx = max(0, ba[0] - bb_[2], bb_[0] - ba[2]) * 111.32 * k; by = max(0, ba[1] - bb_[3], bb_[1] - ba[3]) * 110.57
        d0 = math.hypot(bx, by)
        if d0 > 2 or not _shp: return d0
        pa, pb = _scaled(a, lat0), _scaled(b, lat0)
        return min((x.distance(y) for x in pa for y in pb), default=d0)
    def _pin_km(a, la_, lo_):
        if inside(la_, lo_, a.get('_g')): return 0
        b = a.get('_bb')
        if not b: return 1e9
        k = math.cos(math.radians(la_))
        d0 = math.hypot(max(0, b[0] - lo_, lo_ - b[2]) * 111.32 * k, max(0, b[1] - la_, la_ - b[3]) * 110.57)
        if d0 > .1 or not _shp: return d0
        pt = _GPt(lo_ * 111.32 * k, la_ * 110.57)
        return min((x.exterior.distance(pt) if hasattr(x, 'exterior') else x.distance(pt) for x in _scaled(a, la_)), default=d0)
    # the key matches on a COARSE working copy (GEO_DETAIL, 0.01 deg ~ 1 km by default; the saved outlines are fine, rule R-G6):
    # its edges can sit up to that far off, so the tests allow that much more before holding a piece
    _slack = DETAIL * 111.0
    held_g, pin_wrong = [], []
    g8 = []
    def _g8tok(s):
        s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
        s = re.sub(r'\bft\b', 'fort', re.sub(r'\bmt\b', 'mount', re.sub(r'\bst\b', 'saint', s)))
        return {w for w in re.findall(r'[a-z0-9]+', s) if len(w) > 2 and w not in G8_TYPE}
    G8_DES = ('national park', 'state park', 'national monument', 'monument', 'national forest', 'state forest', 'forest', 'refuge', 'recreation area', 'wildlife area',
              'wildlife management area', 'wma', 'game land', 'preserve', 'seashore', 'lakeshore', 'grassland', 'historic site', 'battlefield', 'office', 'park')
    def _g8des(s):
        s = ' ' + re.sub(r'[^a-z ]', ' ', str(s or '').lower()) + ' '
        # only the STRONG designations can disagree (Park / Monument / Forest / Refuge / Office…); area, WMA, game land, site are
        # the same family of state lands and never count as 'another kind' by themselves
        return {x.split()[-1] for x in G8_DES if f' {x} ' in s} & {'park', 'monument', 'forest', 'refuge', 'office', 'seashore', 'lakeshore', 'battlefield', 'preserve', 'grassland'}
    G8_TYPE = {'park', 'parks', 'forest', 'forests', 'monument', 'refuge', 'recreation', 'area', 'areas', 'lake', 'lakes', 'creek', 'bay', 'state', 'national', 'wildlife',
               'management', 'office', 'field', 'district', 'unit', 'units', 'site', 'sites', 'river', 'trail', 'wilderness', 'preserve', 'reserve', 'natural', 'scenic',
               'historic', 'historical', 'memorial', 'fish', 'game', 'conservation', 'county', 'city', 'public', 'land', 'lands', 'blm', 'nwr', 'wma', 'the', 'and'}
    for ref, p in parks.items():
        m = p.get('m') or []
        r = P.get(ref) or []
        la_, lo_ = (r[5], r[6]) if len(r) > 6 else (None, None)
        if la_ is None and ref in pins(): la_, lo_ = pins()[ref]
        # the record NAMES the park when every word of POTA's name is in it ('White Horse Hill Game Preserve' in 'White Horse
        # Hill National Game Preserve' = the agency's own record, G-1: any distance); only the rest must prove their place
        _pw = words(p.get('n') or (r[0] if r else ''))
        weak = [x for x in m if str(x[3]).split(' · ')[0] in WEAK and not (_pw and _pw == words(x[1]))]   # R-G8 fix: 'Kodiak' is in 'Kodiak Office' but that record does not NAME the park
        # R-G8 (HQ ruling Oct 29 2:45 PM, Brandon 2:40 PM): a shared-words piece joins only if (1) it shares a PLACE word (type
        # words do not count), (2) the kind of place agrees (an office is never park land), (3) it is not bigger than the park's
        # own name-matched record; else CHECK (the waiting room), never joined, never silently dropped
        if weak:
            _kp = kinds(p.get('n') or '') | kinds(p.get('t') or '')
            _strong = [x for x in m if x not in weak]
            _nm = [x[2] or 0 for x in _strong if str(x[3]).split(' · ')[0] == 'name']
            _cap = 1.1 * sum(_nm) + 5 if _nm and all(_nm) else None   # the park's own name-matched land (all its records), 10% slack; a record with no acres on file = no size test
            _bad = []
            for x in weak:
                a = gs_.get(str(x[0])) or {}
                ta, tb = _g8tok(p.get('n') or ''), _g8tok(x[1])
                pw_ = (ta & tb) or {w for w in ta | tb if any(w == u + v for u in ta | tb for v in ta | tb if u != v)}
                da, db = _g8des(p.get('n') or ''), _g8des(x[1])
                why8 = ('no shared place word' if not pw_ else
                        'another kind of place' if (KM.is_admin(x[1]) or 'office' in db or (da and db and not da & db) or not same_kind(_kp, a.get('_k') or kinds(x[1]))) else
                        'bigger than the park\'s own record' if (_cap is not None and (x[2] or 0) > _cap) else '')
                if why8: _bad.append((x, why8))
            if _bad:
                m = [x for x in m if x not in [b[0] for b in _bad]]; p['m'] = sorted(m, key=lambda x: -x[2])
                p['c'] = (p.get('c') or []) + [[b[0][0], b[0][1], b[0][2], f'check (rule R-G8): {b[1]}'] for b in _bad]
                g8.append(f"{ref} ({', '.join(b[0][1][:24] for b in _bad[:2])})")
                weak = [x for x in weak if x not in [b[0] for b in _bad]]
        if weak and la_ is not None:
            ok = [x for x in m if x not in weak]
            left = list(weak)
            for x in list(left):   # the pin proves it
                a = gs_.get(str(x[0]))
                if a is not None and _pin_km(a, la_, lo_) <= .1 + _slack: ok.append(x); left.remove(x)
            grew = True
            while left and grew:   # the chain: touches / within 2 km of a piece that passed
                grew = False
                for x in list(left):
                    a = gs_.get(str(x[0]))
                    if a is None: continue
                    if any(gs_.get(str(y[0])) is not None and _gap_km(a, gs_[str(y[0])], la_) <= 2 + 2 * _slack for y in ok):
                        ok.append(x); left.remove(x); grew = True
            if left:
                p['m'] = sorted(ok, key=lambda x: -x[2])
                p['c'] = (p.get('c') or []) + [[x[0], x[1], x[2], 'held (rule G-1): a similar-name piece more than 2 km from the pin and from every passed piece'] for x in left]
                held_g.append(f'{ref} ({len(left)})')
        m = p.get('m') or []
        if m and p.get('far') == 'well outside' and any(str(x[3]).split(' · ')[0] not in WEAK for x in m):
            pin_wrong.append(ref); p['pin_may_be_wrong'] = 1
        p['g'] = ('pin' if not m else 'approximate' if any(str(x[3]).startswith('reviewed-approx') for x in m) or all(str(x[3]).split(' · ')[0] in WEAK and not (_pw and _pw == words(x[1])) for x in m) else 'official')
    if g8: notice(f'US key {st}', f"rule R-G8: {len(g8)} parks had shared-words pieces moved to CHECK (waiting room): {', '.join(g8[:10])}")
    if held_g: notice(f'US key {st}', f"rule G-1: {len(held_g)} parks had similar-name pieces held (not drawn): {', '.join(held_g[:12])}")
    if pin_wrong: notice(f'US key {st}', f"{len(pin_wrong)} parks: the POTA pin sits well outside the official outline (POTA pin may be wrong; the outline stays): {', '.join(pin_wrong[:12])}")
    # Oct 29 (chat 10: Virginia's Dragon Run = PAD-US 9,563 + the state layer 9,562 + more copies of the SAME tracts; anything that
    # SUMS the records doubles the land): one acreage per park = the area of the UNION of its records ('ac'), the number every
    # reader should use. Needs shapely (installed by the workflow); without it nothing is written.
    try:
        from shapely.geometry import Polygon as _Poly
        from shapely.ops import unary_union as _union
        byid = {_oid(a): a for a in recs if a.get('_g')}
        nac, t_ac, skipped = 0, time.time(), 0
        for ref, p in parks.items():
            ids = [str(x[0]) for x in p.get('m') or []]
            if len(ids) < 2 or not all(i in byid for i in ids): continue
            if time.time() - t_ac > 90: skipped += 1; continue   # Oct 29: a time budget per state (the first run sat 2 h on Alaska)
            pts = [q for i in ids for r in rings(byid[i]['_g']) for q in r]
            nr = sum(len(rings(byid[i]['_g'])) for i in ids)
            if not pts or len(pts) > 60000 or nr > 400: skipped += 1; continue   # huge refuges / forests: too heavy, left without 'ac'
            la0 = sum(q[1] for q in pts) / len(pts); kx, ky = 111320 * math.cos(math.radians(la0)), 110574
            geoms = []
            for i in ids:
                rr = [r for r in rings(byid[i]['_g']) if len(r) > 3]
                boxes = (p.get('parts') or {}).get(i)
                if boxes: rr = [r for r in rr if any(b[0] - .01 <= (min(q[0] for q in r) + max(q[0] for q in r)) / 2 <= b[2] + .01 and b[1] - .01 <= (min(q[1] for q in r) + max(q[1] for q in r)) / 2 <= b[3] + .01 for b in boxes)]
                g = None
                if len(rr) > 40:   # many rings: union them all (holes are rare in big multi-part records)
                    g = _union([_Poly([(q[0] * kx, q[1] * ky) for q in r]).buffer(0) for r in rr])
                else:
                    for r in rr:
                        pg = _Poly([(q[0] * kx, q[1] * ky) for q in r]).buffer(0)
                        g = pg if g is None else g.symmetric_difference(pg)
                if g is not None: geoms.append(g)
            if geoms:
                p['ac'] = round(_union(geoms).area / 4046.86); nac += 1
        notice(f'US key {st}', f'{nac} parks with several records got one union acreage (ac)' + (f'; {skipped} too big or out of time (no ac)' if skipped else '')) if nac or skipped else None
    except ImportError: pass
    except Exception as e: notice(f'US key {st}', f'union acreage skipped: {str(e)[:120]}')  # noqa: BLE001
    # Oct 25 (round 5 leftovers, HQ): a hand note shown on the park cards (e.g. private land inside a legal boundary)
    for ref in parks:
        if (OVR.get(ref) or {}).get('note'): parks[ref]['note'] = OVR[ref]['note']
    # Oct 22 guard (a rebuild from the saved outlines dropped 315 joins: the land was simply not in the saved copy): a park
    # that HAD an outline keeps it when NONE of its old land is in what this run read. A join the new rules turned down
    # (its land is here, just not matched) is not kept; a person's 'no' always wins.
    try:
        old = json.load(open(OUT / f'US-{st}.json')).get('parks', {})
        ids_here = {_oid(a) for a in recs}; kept = 0
        TR = transfers()
        for ref, op in old.items():
            np_ = parks.get(ref)
            if not np_ or np_.get('m') or not op.get('m'): continue
            no = {str(x) for x in (OVR.get(ref) or {}).get('no', [])}
            om = [x for x in op['m'] if str(x[0]) not in no and str(x[1]) not in no]
            if om and ref in TR and any(str(x[0]) in ids_here for x in om):
                # Oct 28 (HQ, Brandon): a TRANSFERRED park (handed to a county / city, POTA number kept) never loses its outline:
                # its land is still in the read but no longer under the old name: keep the last good join, say why
                np_['m'] = [x for x in om if str(x[0]) in ids_here]; np_['c'] = []
                np_['kept'] = f"transferred to {TR[ref].get('by')}: the last official outline is kept"; kept += 1; continue
            if om and not any(str(x[0]) in ids_here for x in om):
                # boundary review #3: the same land under a new PAD-US id (a new PAD-US version) = found by name + acres
                fp = []
                for x in om:
                    if not isinstance(x[0], int): continue
                    hit = next((a for a in recs if isinstance(a.get('OBJECTID'), int) and _nf(a.get('Unit_Nm') or a.get('Loc_Nm') or '') == _nf(x[1])
                                and abs((a.get('GIS_Acres') or 0) - (x[2] or 0)) <= max(20, .1 * (x[2] or 0))), None)
                    if hit: fp.append([hit['OBJECTID'], x[1], round(hit.get('GIS_Acres') or 0), (str(x[3]) if str(x[3]).startswith('reviewed') else 'same land, new PAD-US id (name + acres)')])
                if fp and len(fp) == sum(1 for x in om if isinstance(x[0], int)):
                    np_['m'] = fp + [x for x in om if not isinstance(x[0], int) and str(x[0]) in ids_here]; np_['c'] = []; np_['refound'] = PADVER[0]; kept += 1
                    continue
                np_['m'] = om; np_['c'] = []; np_['kept'] = 'its land was not in this run\'s map read; the last good join is kept'
                for k in ('read', 'src'):
                    if op.get(k): np_[k] = op[k]   # rule B7: a kept outline keeps the day it was last read (the clock keeps running)
                if op.get('far'): np_['far'] = op['far']
                kept += 1
        if kept: notice(f'US key {st}', f'{kept} park(s) kept their last good outline (their land was missing from this read)')
    except FileNotFoundError: pass
    except Exception as e: notice(f'US key {st}', f'keep-last-good check skipped: {e}')  # noqa: BLE001
    try:
        for ref, t in transfers().items():
            if ref in parks: parks[ref]['run_by'] = t.get('by', '') + (f" since {t['since']}" if t.get('since') else '')
            if ref in parks and t.get('outline_note'): parks[ref]['outline_note'] = t['outline_note']
    except FileNotFoundError: pass
    except Exception as e: notice(f'US key {st}', f'transfer tags skipped: {e}')  # noqa: BLE001
    nonum = sorted(([a['OBJECTID'], a.get('Unit_Nm') or a.get('Loc_Nm') or '', a.get('d_Des_Tp') or a.get('Des_Tp') or '', a.get('Loc_Mang') or a.get('Mang_Name') or '',
                     round(a.get('GIS_Acres') or 0)] for a in recs if a['OBJECTID'] not in used), key=lambda x: -x[4])
    counts = {'parks': len(parks), 'matched': sum(1 for p in parks.values() if p['m']), 'check': sum(1 for p in parks.values() if not p['m'] and p['c']),
              'none': sum(1 for p in parks.values() if not p['m'] and not p['c'] and not p.get('a')), 'site': sum(1 for p in parks.values() if p.get('a')), 'nonum': len(nonum), 'padus': len(recs), 'read': seen,
              'pin_outside': sum(1 for p in parks.values() if p.get('far')),
              'pin_well_outside': sum(1 for p in parks.values() if p.get('far') == 'well outside'),
              'detail': used_detail,
              'pin_no_shape': sum(1 for p in parks.values() if p.get('far') == 'no shape to check against'),
              'pin_swap': sum(1 for p in parks.values() if p.get('swap')),
              # the shared scoring, in shadow: how often it would have decided differently
              'shadow_demote': sum(1 for p in parks.values() if p.get('m') and (p.get('shadow') or {}).get('v') in ('check', 'none')),
              'shadow_add': sum(1 for p in parks.values() if not p.get('m') and (p.get('shadow') or {}).get('v') == 'join'),
              'shadow_other_place': sum(1 for p in parks.values() if p.get('m') and (p.get('shadow') or {}).get('v') == 'join')}
    out = {'updated': time.strftime('%Y-%m-%d'), 'st': st, 'note': 'Built by .github/scripts/kpc_us_key.py from USGS PAD-US (fed + state fee land) and POTA. m = joined (same name + same kind), c = check by hand (NOT joined).',
           'counts': counts, 'parks': parks, 'nonum': nonum[:300]}
    # plain-words review page for this state (GitHub shows .md files nicely)
    R = OUT / 'review'; R.mkdir(exist_ok=True)
    L = [f'# {st}: POTA parks vs official land (USGS PAD-US)', '', f"Built by `.github/scripts/kpc_us_key.py` (date: data/status/kpc_us_key.json). **{counts['matched']} of {counts['parks']}** parks joined to official land "
         f"(same name + same kind of place). **{counts['check']}** to check by hand, **{counts['none']}** with nothing found. Nothing below is joined until a person checks it.", '']
    chk = [(r, p) for r, p in parks.items() if not p['m'] and p['c']]
    L += ['## To check (not joined)', ''] + [f"- **{r}** {p['n']} ({p['t']}) → " + '; '.join(f"{x[1]} (~{x[2]:,} ac, {x[3]})" for x in p['c']) for r, p in chk] + ['']
    L += ['## Sites on bigger public land (no outline of their own; the land around the pin)', ''] + [f"- {r} {p['n']} ({p['t']}) → on " + '; '.join(f"{x[1]} (~{x[2]:,} ac)" for x in p['a']) for r, p in parks.items() if p.get('a')] + ['']
    L += ['## Nothing found in PAD-US', ''] + [f"- {r} {p['n']} ({p['t']})" for r, p in parks.items() if not p['m'] and not p['c'] and not p.get('a')] + ['']
    L += ['## Biggest federal / state places with no POTA park joined (first 60)', ''] + [f"- {x[1]} · {x[2]} · {x[3]} · ~{x[4]:,} ac" for x in nonum[:60]]
    save_text(R / f'US-{st}.md', '\n'.join(L) + '\n')
    for r_ in DBG & set(parks): dbg(r_, 'E saved', {k: parks[r_].get(k) for k in ('m', 'c', 'g', 'kept', 'far')})
    save_json(OUT / f'US-{st}.json', out)
    return counts


idx = {}
try: idx = json.load(open(OUT / 'index.json')).get('states', {})
except Exception: pass  # noqa: BLE001
# GOLDEN CASES FIRST (Oct 22). If any known case comes out wrong, a matching rule is broken: write NO keys rather
# than spread the mistake across fifty states. Says which case and why, and exits cleanly (a failed run emails Brandon).
try:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent / 'tests'))
    import run_match_tests
    _bad = run_match_tests.failures(groups=('us_names',))
except Exception as _e:  # noqa: BLE001
    _bad = []; notice('US key', f'golden cases could not be run ({_e}); carrying on')
if _bad:
    notice('US key STOPPED', f'{len(_bad)} golden case(s) wrong, so NO keys were written: ' + ' | '.join(_bad)[:700])
    sys.exit(0)
done = []
STATE_S = {}
for st in STATES:
    if st == 'KY': continue
    if time.time() - T0 > LIMIT: notice('US key', f'stopped for time before {st}; run again for the rest'); break
    _t0 = time.time()
    try:
        c = run(st)
    except Exception as e:  # noqa: BLE001
        notice(f'US key {st}', f'FAILED: {e}'); continue
    STATE_S[st] = round(time.time() - _t0)   # Oct 28 (HQ: key rebuild speed-up): where the minutes go, state by state
    if c:
        idx[st] = c; done.append(st); c['seconds'] = STATE_S[st]
        print(f"{st}: {c['parks']} parks, {c['matched']} joined, {c['check']} to check, {c['none']} nothing found, {c['nonum']} places with no POTA park, {STATE_S[st]} s", flush=True)
    save_json(OUT / 'index.json', {'states': idx})
    # the map pages draw joined pieces live: tell them each layer's query url + name field (layers found at run time too)
    try: LJ = json.load(open(OUT / 'layers.json'))
    except Exception: LJ = {}  # noqa: BLE001
    for x in XS:
        if x[0] in RESOLVED: LJ[x[0]] = [RESOLVED[x[0]][0], RESOLVED[x[0]][1], x[5]]
        elif not x[1].startswith('svc:'): LJ[x[0]] = [x[1], x[2], x[5]]
    # Oct 28: zipped-shapefile layers: the map pages and the 2-fer bot read the outlines from our own simplified copy
    for pre, recs_ in ZIPGEO.items():
        fc = {'type': 'FeatureCollection', 'about': f'{LAYERS_ZIP[pre][2]}; from {LAYERS_ZIP[pre][0]}; read {time.strftime("%Y-%m-%d")}',
              'features': [{'type': 'Feature', 'properties': {'OBJECTID': i, 'Unit_Nm': v[0]}, 'geometry': {'type': 'Polygon' if len(v[1]) == 1 else 'MultiPolygon',
                            'coordinates': [v[1][0]] if len(v[1]) == 1 else [[r] for r in v[1]]}} for i, v in sorted(recs_.items()) if v[1]]}
        save_json(OUT / f'zip-{pre}.json', fc)
        LJ[pre] = [f'file:data/us-key/zip-{pre}.json', 'Unit_Nm', LAYERS_ZIP[pre][2]]
    save_json(OUT / 'layers.json', LJ)
# Oct 28 (HQ item C): a park POTA files under several states (132 do: the Appalachian Trail under 14) is not 'nothing found' in
# one state when another state's key joined it. Such parks are marked 'joined_in' and counted apart ('joined_in_another_state').
try:
    import glob as _g0
    _all = {pathlib.Path(_f).stem: json.load(open(_f)) for _f in _g0.glob(str(OUT / 'US-??.json'))}
    _joined = {}
    for _st, _d in _all.items():
        for _r, _p in (_d.get('parks') or {}).items():
            if _p.get('m'): _joined.setdefault(_r, []).append(_st)
    # Oct 29 (HQ 2:08 PM, Brandon 2:07 PM 'yea 1 pin for several states'): a park across a state line has ONE POTA pin, in one
    # state; in the other states' files the pin is 'outside' by definition. The pin is judged against the WHOLE park: when it
    # sits inside the park's land in ANY state, the far / pin_may_be_wrong flags come off in the others (the pin is never moved).
    _pin_in = {}
    for _st, _d in _all.items():
        for _r, _p in (_d.get('parks') or {}).items():
            if _p.get('m') and not _p.get('far'): _pin_in.setdefault(_r, _st)
    for _st, _d in _all.items():
        _n = 0; _was = json.dumps(_d, sort_keys=True)
        for _r, _p in (_d.get('parks') or {}).items():
            if _p.get('far') and _r in _pin_in and _pin_in[_r] != _st:
                _p.pop('far', None); _p.pop('pin_may_be_wrong', None); _p['pin_in_state'] = _pin_in[_r][3:]
        _d.setdefault('counts', {})['pin_outside'] = sum(1 for _p in (_d.get('parks') or {}).values() if _p.get('far'))
        _d['counts']['pin_well_outside'] = sum(1 for _p in (_d.get('parks') or {}).values() if _p.get('far') == 'well outside')
        for _r, _p in (_d.get('parks') or {}).items():
            _else = [x for x in _joined.get(_r, []) if x != _st]
            if not _p.get('m') and _else:
                _p['joined_in'] = _else; _n += 1
            elif _p.get('joined_in') and not _else: _p.pop('joined_in')
        _c = _d.get('counts') or {}
        _c['joined_in_another_state'] = _n; _d['counts'] = _c
        if json.dumps(_d, sort_keys=True) != _was: save_json(OUT / f'{_st}.json', _d)
        if _st[3:] in idx: idx[_st[3:]]['joined_in_another_state'] = _n
except Exception as _e: print(f'cross-state count skipped: {_e}', flush=True)  # noqa: BLE001
if STATE_S: notice('US key time', f"{sum(STATE_S.values())} s over {len(STATE_S)} states; slowest: " + ', '.join(f'{k} {v} s' for k, v in sorted(STATE_S.items(), key=lambda kv: -kv[1])[:10]))
tot = {k: sum(v.get(k, 0) for v in idx.values()) for k in ('parks', 'matched', 'check', 'none', 'site')}
notice('US key extra maps', ', '.join(f'{k}: {v}' for k, v in XCOUNT.items()))
if CMODE != 'off':
    notice('US key saved shapes', f"mode {CMODE}, detail {DETAIL}: loaded {len(CACHE_USED)} ({' '.join(CACHE_USED)}), "
                                  f"saved {len(CACHE_SAVED)} ({' '.join(CACHE_SAVED)})")
notice('US answer key', f"{len(done)} states this run ({' '.join(done)}). All states so far: {tot['parks']} parks, {tot['matched']} joined, {tot['check']} to check, {tot['site']} sites on bigger land, {tot['none']} nothing found (of them {sum(v.get('joined_in_another_state', 0) for v in idx.values())} are joined in another state they cross: not missing)")
# How many joins put the park's pin outside the land it was joined to? A big number here means the match
# count has been flattering us. Printed per run so it can be watched rather than discovered later.
try:
    import glob as _g
    bad = tot_j = 0
    worst = []
    for _f in _g.glob(str(OUT / '*.json')):
        if _f.endswith('index.json'): continue
        _d = json.loads(pathlib.Path(_f).read_text(encoding='utf-8'))
        _c = _d.get('counts') or {}
        b, j = _c.get('pin_outside', 0) or 0, _c.get('matched', 0) or 0
        bad += b; tot_j += j
        if b: worst.append((b, _d.get('st'), j))
    if tot_j:
        notice('Boundary check', f'{bad} of {tot_j} joined parks have their pin OUTSIDE the land they were '
                                 f'joined to ({100 * bad / tot_j:.1f}%). Worst: '
                                 + ', '.join(f'{st} {b}/{j}' for b, st, j in sorted(worst, reverse=True)[:8]))
except Exception as _e:
    notice('Boundary check', f'could not total it up: {_e}')
