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
import json, math, os, re, sys, time, unicodedata, urllib.parse, urllib.request, pathlib

Q = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
ALL = 'AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split()
STATES = (os.environ.get('STATES') or '').upper().replace(',', ' ').split() or ALL
if os.environ.get('FINISH_ONLY'): STATES = []   # Oct 28 (key speed-up): the join job after the split jobs: only the all-state steps at the end
OUT = pathlib.Path('data/us-key'); OUT.mkdir(parents=True, exist_ok=True)
T0 = time.time(); LIMIT = float(os.environ.get('MINUTES') or 300) * 60
import gzip
# Nov 3 (code review vs the proposed rules, rule 29): every request in this script waits for 2 s per host (kpc_host_pace.py)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpc_host_pace  # noqa: E402
import kpc_key_facts as KF  # noqa: E402  (links-10: pin distance + record kind per park, 'bk')
kpc_host_pace.install()
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
# Nov 10 (master gate): KPC_REFILL_ONLY=1 with GEO_CACHE_MODE=use only tops up and re-saves each state's saved copy (saved ids by id,
# newer / short layers); no matching, no key file is written. The master gate then checks the refilled copy again.
REFILL_ONLY = os.environ.get('KPC_REFILL_ONLY') == '1' and CMODE == 'use'
# Nov 10 (owner rule, Nov 10: the master tool is the ONLY owner of the saved copies). The master step (kpc_master_cli.py fill) runs this script in
# refill mode as its READER: KPC_LAYER_OUT=<dir> = each layer it re-reads is written as a layer file (every record read + what the key
# keeps) and NOT merged here; the master checks the count, trims, records it and merges (a smaller read never replaces a saved layer).
# KPC_LAYER_IN=<dir> = a checked download (a person's, from the PC helper) is read from <dir>/US-<st>/<prefix>.geojson.gz instead of
# live. KPC_REFILL_FORCE='all' or prefixes = re-read those layers too (the fresh start). KPC_MASTER_OWNS=1 (the build) = the build only
# READS the saved copy: no top-up, no saved-id top-up, no re-save (the master step did that before the gate).
LAYER_OUT = pathlib.Path(os.environ['KPC_LAYER_OUT']) if REFILL_ONLY and os.environ.get('KPC_LAYER_OUT') else None
LAYER_IN = pathlib.Path(os.environ['KPC_LAYER_IN']) if os.environ.get('KPC_LAYER_IN') else None
REFILL_FORCE = (os.environ.get('KPC_REFILL_FORCE') or '').split() if REFILL_ONLY else []
MASTER_OWNS = os.environ.get('KPC_MASTER_OWNS') == '1' and not REFILL_ONLY
RAWF = {}   # prefix -> every feature read this run (for the layer file)
CACHE_USED, CACHE_SAVED = [], []
SHADOW = os.environ.get('SHADOW') == '1'
NAME_JOIN = (os.environ.get('NAME_JOIN') or '1') != '0'   # Oct 24: the world key's kind-label rule, US version (needs the pin inside)


# Nov 9 (Brandon t939u, 6:20 PM CST, on the hosts whose robots.txt answers 403: "4 saved copies"): no live read from these hosts
# until their robots.txt lets us back in; their layers come from the saved copy (boundary-cache) on every path, refresh included.
# Remove a host (in kpc_master.SAVED_ONLY_HOSTS) only when its robots.txt allows the read again.
# One set of host rules (owner rule, 2026-11-10): kpc_master.live_ok over kpc_net_guard. Its saved-copy list starts as
# services.arcgis.com,services1.arcgis.com,apps.fs.usda.gov; KPC_SAVED_ONLY_HOSTS only adds hosts. No copy of the rules here.
SAVED_ONLY_HOSTS = None   # the list is kpc_master.SAVED_ONLY_HOSTS
SAVED_ONLY_SKIPPED = {}   # state -> layer prefixes taken from the saved copy instead of a live read
NEVER_HOSTS = ()          # the never-contact hosts are kpc_net_guard's (services*.arcgis.com included, robots.txt too)


def _shared(name='kpc_master'):
    """A shared helper module. A test that runs only this part of the file finds it from the repo root."""
    import importlib, os as _os, sys as _sys
    try: return importlib.import_module(name)
    except ImportError:
        _sys.path.insert(0, _os.path.join(_os.getcwd(), '.github', 'scripts')); return importlib.import_module(name)


def saved_only(url):
    """True when the host rules (kpc_master.live_ok) forbid a live read of url: its layers come from the saved copy."""
    return not _shared().live_ok(url)[0]


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', '%0A')), flush=True)


def get(params, tries=5):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(Q + '?' + urllib.parse.urlencode(params), headers={'User-Agent': 'KPC (kentuckyportableclub.github.io)'})
            with checked_open(req, 180) as r:   # Nov 10: checked opener + 2 s per-host pace, first address and every hop
                j = json.loads(r.read().decode('utf-8', 'replace'))
            if j.get('error'): raise RuntimeError(str(j['error'])[:200])
            return j
        except KMASTER.LiveNotAllowed: raise   # a refused host or hop is never retried
        except Exception as e:  # noqa: BLE001
            last = e; time.sleep(8 * (i + 1))
    raise last


# ---------------- names + kinds (same idea as kpc-bounds.js, with other states' words) ----------------
GEN = (r"state habitat area|habitat area|mitigation park wildlife and environmental area|wildlife and environmental area|state scientific and natural area|scientific and natural area|scenic reserve|state natural reserve|natural reserve|coastal reserve|conservation reserve|unique area|state wayside|national memorial|natural environment area|nrma|nea|blm national conservation area|national conservation area|wildlife management area (and|&) public fishing area|public fishing area|fishing area|national wild and scenic river|wild and scenic river|national recreational river|state vehicle recreation area|vehicle recreation area|state reservation|reservation|state reserve|national reserve|national fish hatchery|state fish hatchery|fish hatchery|hatchery|fh|fishery area|state fishery area|blm herd management area|herd management area|herd area|blm special recreation management area|special recreation management area|extensive recreation management area|blm recreation management area|recreation management area|wilderness study area|wsa|hma|srma|erma|blm|fishing access site|access site|state game lands? number|designated state natural area|designated|public hunting area|hunting area|state fishing lake|fishing lake|state wilderness area|wilderness area|wilderness|resort|natural state conservation area|waterfowl refuge|wildlife refuge|refuge|state natural area|natural area preserve|state nature preserve|nature preserve|natural area|fish and wildlife area|state wildlife area|"
       r"wildlife management area|wildlife area|state game lands?|game lands?|game areas?|game management area|conservation area|state conservation area|"
       r"state resort park|state historic site|state historical park|state historic park|historic site|state recreation area|recreation area|"
       r"state beach|state seashore|national wildlife refuge|national recreation area|national historical park|national historic site|"
       r"national park|national forests|national forest|national grasslands|national grassland|national monument|national seashore|national lakeshore|national battlefield|"
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
         ('rma', r'recreation management area|\bs?rma\b|\berma\b|campground|recreation site|day use area'),
         # Oct 29 9:15 PM (HQ recon, R-G8 kind of place): an airstrip is never a trailhead (US-13523 Kingston Airport vs 'Kingston Trailhead')
         ('air', r'airport|airstrip|air ?field|landing strip'), ('trh', r'trail ?head')]
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


US_COMPAT = [{'wild', 'wsa'}, {'ca', 'snp'}, {'rma', 'trh'}]   # POTA lists many BLM study areas as 'BLM Wilderness Area'
def same_kind(ka, kb): return not ka or not kb or bool(ka & kb) or any(ka & c and kb & c and (ka | kb) & c == c for c in US_COMPAT)


def words(s): return set(w for w in norm(s).split() if len(w) > 2)


def piece_why(name, a):
    """Nov 2 (mapping agent, rule 18; switch KPC_PIECE_NAME): why record `a` may not join the park `name` because the park is a
    named PIECE (unit / tract / parcel / zone) and the record does not name that piece; '' when it may. Before: norm()'s
    'starts the same way' allowance joined 'Salinas Pueblo Missions, Abo Unit' to the whole monument, both Chattahoochee Fall
    Line tracts to the whole WMA, 'Las Palomas, Anacua Unit' to every other Las Palomas unit."""
    if not _kr('KPC_PIECE_NAME'): return ''
    nm, loc = a.get('Unit_Nm') or a.get('Loc_Nm') or '', a.get('Loc_Nm')
    if _office(nm) and loc and not _office(loc): nm, loc = loc, None   # batch 1b: an office's Unit_Nm is not the record's place name
    ok, why = KR.piece_ok(name, nm, loc, a.get('Loc_Mang') if str(a.get('Mang_Name') or '').lower() != 'padus' and not isinstance(a.get('OBJECTID'), int) else '')   # Nov 3: a state / BLM layer's own type word is not a piece
    return '' if ok else why


# Nov 6 (big key / 2-fer patch; Quality grade FIX 7:10 AM CST): KPC_US_PUBACCESS = off | report (default). REPORT ONLY: it never
# changes a join and never drops a POTA park. A joined PAD-US piece marked closed to the public (Pub_Access XA), or tribal / military
# land not marked open (the same test as the 2-fer program's pad_use() in kpc_fers.py), is only NOTED: the park is flagged and its
# closed pieces listed in 'pub_access' in data/us-key/tracts/US-XX.json (RI US-6981 / DE US-10670 are mostly UK land with one small XA
# piece). Whether closed pieces should ever leave the outline is Brandon's call (piece-level vs park-level); 'on' is not a mode.
PUBACC = (os.environ.get('KPC_US_PUBACCESS') or 'report').strip().lower()
if PUBACC not in ('off', 'report'):
    print(f'::warning title=US key::KPC_US_PUBACCESS={PUBACC!r} is not a mode (report only, Nov 6 Quality grade): using report', flush=True)
    PUBACC = 'report'
PUBACC_HIT = []
def closed_why(a):
    acc = str(a.get('Pub_Access') or ''); own = str(a.get('Own_Type') or '')
    mang = str(a.get('Mang_Name') or '') + ' ' + str(a.get('Own_Name') or '')
    if acc == 'XA': return 'closed to the public (PAD-US Pub_Access XA)'
    if (own == 'TRIB' or re.search(r'\bDOD\b|\bARMY\b|\bNAVY\b|\bUSAF\b|\bUSMC\b', mang)) and acc and acc != 'OA':
        return f'tribal / military land not open to the public (PAD-US Pub_Access {acc})'
    return None


def _office(t):
    """A name that is an office or district, not a place ('Eastern Interior Field Office', 'Ranger District')."""
    return bool(t) and (KM.is_admin(t) or bool(re.search(r'field office|district office|ranger district', str(t), re.I)))


def join_how(name, kp, a, close, rules=True):
    """How - if at all - the POTA park called `name` (kinds `kp`) joins official record `a`. `close` = within
    about 0.1 degree of the park's pin. This is the ONLY place the decision is made: run() calls it and so do the
    golden tests, so a test can never again check a different path from the one the matcher really takes (Oct 22:
    the first Upper/Lower fix went into exact_name, which was never the path White Oak Lake actually joined by).
    rules=False skips the Nov 2 refusals (only used to tell 'refused by a rule' from 'no match' for the check list)."""
    nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
    loc = a.get('Loc_Nm')
    if rules:
        # Nov 2 (mapping agent; KPC_NO_OFFICE_JOIN): an office is not a park. Batch 1b (Quality): PAD-US 2162 / 2165 carry the
        # office in Unit_Nm ('Eastern Interior Field Office') but the real place in Loc_Nm ('Steese National Conservation Area',
        # 'White Mountains National Recreation Area'): then the place name is tested, never the office's. No place name = no join.
        if _kr('KPC_NO_OFFICE_JOIN') and _office(nm):
            if not loc or _office(loc): return None
            nm, loc = loc, None
        if piece_why(name, a): return None
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
            with checked_open(req, 120) as r: info = json.loads(r.read())   # Nov 10: checked opener + pace
            have = {f['name'] for f in info.get('fields', [])}
            # Oct 27 (boundary review #2 / rule B7): the PAD-US version every PAD-US outline comes from
            m = re.search(r'PAD-US\s*(?:version\s*)?(\d+(?:\.\d+)*)', ' '.join(str(info.get(k) or '') for k in ('description', 'copyrightText', 'name')), re.I)
            PADVER[0] = 'PAD-US ' + m.group(1) if m else 'PAD-US'
            PADMAX[0] = int(info.get('maxRecordCount') or 0) or None
        except Exception: have = set()  # noqa: BLE001
        # Nov 2 (mapping agent): + Agg_Src, the data provider of each record (FWS PAD-US 3.0 / 4.0, a state's list, TNC...): the
        # KPC_PADUS_DEDUPE switch needs it, and a saved copy only carries it once it was read with this list (GEO_CACHE_MODE=refresh)
        # Nov 6 (big key / 2-fer patch): + Source_PAID (the provider's own STABLE id), Own_Name, Loc_Own (the owner) for the tract
        # records (kpc_tracts.py; field names from kpc_source_fields.py). Only fields the layer lists are asked for (below).
        want = 'OBJECTID,Unit_Nm,Loc_Nm,Own_Type,Own_Name,Loc_Own,Mang_Type,Mang_Name,Loc_Mang,Des_Tp,d_Des_Tp,Pub_Access,GIS_Acres,Category,Agg_Src,Source_PAID'.split(',')
        FIELDS = ','.join(w for w in want if not have or w in have)
        notice('PAD-US fields', FIELDS + (' (field list not read)' if not have else ''))
    return FIELDS


PADVER = ['PAD-US']
PADMAX = [None]   # the PAD-US layer's own maxRecordCount (read with its field list)
GEO = ([{'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': DETAIL, 'geometryPrecision': PREC}] if DETAIL < 0.01 else []) + \
      [{'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': 0.01, 'geometryPrecision': 3},
       {'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': 0.01}, {'returnGeometry': 'true', 'outSR': 4326}]
GI = [0]
def page(st, off):
    while True:
        q = {'where': "State_Nm='%s'" % st, 'outFields': fields(), 'f': 'json', 'resultOffset': off, 'resultRecordCount': layer_page_size(PAGE, PADMAX[0]), 'orderByFields': 'OBJECTID'}
        q.update(GEO[GI[0]])
        try: return get(q, tries=3)
        except Exception as e:  # noqa: BLE001
            if GI[0] + 1 >= len(GEO): raise
            notice('PAD-US', f'query shape {GI[0]} refused ({e}); trying a simpler one'); GI[0] += 1


# Nov 9 2026, Brandon 11:24 AM CST ('Yes' to: "keep a record that fails a check whenever its name matches the POTA park, which
# follows your rule to trust the official boundary when the name matches"): a PAD-US record that fails the load filters (Category
# Fee / Designation, owner or manager FED / STAT / DIST, or the State_Nm read) is KEPT when its name matches a POTA park of this state
# under the strict test: exact_name() + name_ok(), BOTH names carry a kind word and share it (a plain 'Riverside Park' never stands
# in for Riverside State Park), a real name (8+ letters after norm(), not an office / admin name). Statewide city-park layers cannot
# flood in: a record enters only for a POTA park's name. Nov 9 11:28 AM (root cause): a SAVED id (overrides.json 'join' / 'fp') is
# ALWAYS loaded, by id if need be (saved_fetch); the name exception is only for parks with no saved id. Nov 9 11:26 AM (Brandon):
# order = PAD-US passes the filters, else the state layer's (state-gis.json) record of that name, else the PAD-US name exception.
# Cross-state: a park whose pin is near its state's edge and that has no strict-name record in the state's read asks PAD-US once
# for records of that name around its pin in a neighbouring state (Silvio O. Conte NWR is filed under NH; POTA lists it in MA).
# KPC_PADUS_NAME_KEEP=0 turns this off. It adds candidates only; the join tests below decide as always.
NAME_KEEP = (os.environ.get('KPC_PADUS_NAME_KEEP') or '1').strip().lower() not in ('0', 'off', 'no', '')
NAME_KEEP_HIT = []   # [st, park, record id, record name, why] for the notice and the key's counts


def _passes_load(a):
    if (a.get('Category') or '') not in ('Fee', 'Designation'): return False   # Designation = wilderness, NCA… overlays
    # Oct 18: + DIST (regional special districts: Florida's water management districts own the 'State Conservation Areas' POTA lists)
    return (a.get('Own_Type') or '') in ('FED', 'STAT', 'DIST') or (a.get('Mang_Type') or '') in ('FED', 'STAT', 'DIST')


def keep_names(P, st=None, every=False):
    """{norm variant: [(park ref, POTA name, kinds)]} for the strict name keep, plus each hand-joined PAD-US id's saved name."""
    idx, hand = {}, saved_ids(P)
    _has = {v[0] for v in hand.values()}
    for ref, r in (P or {}).items():
        if ref in _has and not every: continue   # a park with a saved id uses that id; the name exception is only for parks with none
        name = r[0] if isinstance(r, (list, tuple)) and r else str(r or '')
        if len(norm(name).replace(' ', '')) < 8 or KM.is_admin(name): continue
        kp = kinds(name) | kinds(r[2] if isinstance(r, (list, tuple)) and len(r) > 2 else '')
        for nn in [name] + [x for x in ((OVR.get(ref) or {}).get('alias') or []) if isinstance(x, str)]:   # an alias a person approved is the park's name too
            vs = variants(nn); vs |= {_soft(x) for x in vs if _soft(x)}
            for v in vs: idx.setdefault(v, []).append((ref, nn, kp))
    return idx, hand


def saved_ids(P):
    """Nov 9 ROOT CAUSE (11:28 AM): every PAD-US id a person saved for a park of this state (overrides.json 'join' or 'fp').
    {id: (ref, saved name or '')}. These are ALWAYS loaded, whatever the load filters or the state PAD-US files them under:
    the filters ran before the overrides, so a saved join to a Category 'Other' record (US-2238 Heyburn -> 199938) pointed at nothing."""
    out = {}
    for ref in (P or {}):
        o = OVR.get(ref) or {}
        fp = o.get('fp') or {}
        for i in list(o.get('join') or []) + list(fp):
            if re.fullmatch(r'\d+', str(i).strip()):
                f = fp.get(str(i).strip()) or ['']
                out.setdefault(str(i).strip(), (ref, f[0] if isinstance(f, (list, tuple)) and f else ''))
    return out


def name_keep(a, idx, hand):
    """The POTA park whose name this record carries (strict), or None. Returns (ref, why)."""
    nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
    if not nm or KM.is_admin(nm): return None
    h = hand.get(str(a.get('OBJECTID')))
    if h: return h[0], 'saved id (overrides.json join)'   # a saved id is always loaded (the join tests and fp check still decide)
    ka = kinds(a.get('Unit_Nm')) | kinds(a.get('Loc_Nm')) | ({DES[a['Des_Tp']]} if a.get('Des_Tp') in DES else set())
    vs = variants(nm); vs |= {_soft(x) for x in vs if _soft(x)}
    for v in vs:
        for ref, pname, kp in idx.get(v, []):
            # strict: BOTH names say what kind of place it is, and the same kind ('Riverside Park' / 'Stolley Park' say no kind: never)
            if kp and ka and kp & ka and exact_name(pname, nm) and name_ok(pname, nm, kp, ka): return ref, f"name matches the POTA park ({pname})"
    return None


def _shape(a, f):
    g = f.get('geometry') or {}
    a['_bb'] = bbox(g); a['_g'] = g
    a['_k'] = kinds(a.get('Unit_Nm')) | kinds(a.get('Loc_Nm')) | ({DES[a['Des_Tp']]} if a.get('Des_Tp') in DES else set())
    return a


def pad_state(st, P=None):
    recs, off, seen = [], 0, set()
    idx, hand = keep_names(P, st) if (NAME_KEEP and P) else ({}, {})
    # Owner rule, 2026-11-10: a short page without exceededTransferLimit is not the end (a silent server cap): read on until an
    # empty page, moving by the rows really sent; a page with no new id = resultOffset ignored = the state FAILS (its last key stays).
    lim = float(KMASTER.LAYER_MINUTES); deadline = time.monotonic() + lim * 60   # the same per-layer limit as kpc_master.read_complete
    while True:
        if time.monotonic() > deadline: raise RuntimeError(f'PAD-US {st}: over its {lim:g}-minute layer limit (KPC_LAYER_MINUTES) at offset {off}: not used (the last key stays)')
        fs = page(st, off).get('features', [])
        if not fs: break
        here = {str((f.get('attributes') or {}).get('OBJECTID')) for f in fs}
        if not here - seen: raise RuntimeError(f'PAD-US {st}: the server sent the page at offset {off} again (resultOffset ignored?): not used')
        for f in fs:
            a = f.get('attributes') or {}
            if str(a.get('OBJECTID')) in seen: continue
            seen.add(str(a.get('OBJECTID')))
            if not _passes_load(a):
                k = name_keep(a, idx, hand) if (idx or hand) else None
                if not k: continue
                a['KPC_NameKeep'] = k[1]; NAME_KEEP_HIT.append([st, k[0], a.get('OBJECTID'), a.get('Unit_Nm') or a.get('Loc_Nm'), k[1]])
            recs.append(_shape(a, f))
        off += len(here); time.sleep(.6)
    n = len(seen)
    want = count_query(Q, {'where': "State_Nm='%s'" % st}, box=False)   # the layer's own count, the same where (no page parameters)
    if want is None or n != want: raise RuntimeError(f'PAD-US {st}: read {n} of {want} records the layer reports: SHORT, not used (the last key stays)')
    if NAME_KEEP and P:
        try: recs += pad_cross(st, P, recs, idx, hand)
        except Exception as e: notice(f'US key {st}', f'cross-state name read skipped ({type(e).__name__}: {str(e)[:120]})')  # noqa: BLE001
        _h = [x for x in NAME_KEEP_HIT if x[0] == st]
        if _h: notice(f'US key {st}', f"{len(_h)} PAD-US record(s) kept by name although a load filter dropped them (Brandon Nov 9 11:24 AM): "
                                      + ', '.join(f'{x[1]}={x[2]}' for x in _h[:12]))
    return recs, n


SAVED_HIT = []   # [st, park, id, name, PAD-US state] saved ids loaded by id because the state read did not have them


def saved_fetch(st, P, recs):
    """Nov 9 primary fix: the saved ids (overrides.json) of this state's parks that the read does not have (filtered out, or filed
    under another state in PAD-US: US-0329 -> 5300 is NH) are asked for BY ID, in batches of 100, whatever their Category, owner or state."""
    if not NAME_KEEP: return []
    hand = saved_ids(P)
    seen = {_oid(a) for a in recs}
    miss = sorted({i for i in hand if i not in seen}, key=int)
    out = []
    for b in range(0, len(miss), 100):
        q = {'where': 'OBJECTID IN (%s)' % ','.join(miss[b:b + 100]), 'outFields': fields(), 'f': 'json'}
        q.update(GEO[GI[0]])
        j = get(q, tries=2); time.sleep(.6)
        for f in j.get('features', []):
            a = f.get('attributes') or {}
            i = str(a.get('OBJECTID'))
            if i in seen or i not in hand: continue
            a['KPC_NameKeep'] = 'saved id (overrides.json join)' + (f"; filed under {a.get('State_Nm')} in PAD-US" if a.get('State_Nm') and a.get('State_Nm') != st else '')
            SAVED_HIT.append([st, hand[i][0], a.get('OBJECTID'), a.get('Unit_Nm') or a.get('Loc_Nm'), a.get('State_Nm')])
            seen.add(i); out.append(_shape(a, f))
    if out: notice(f'US key {st}', f'{len(out)} saved PAD-US id(s) loaded by id (the load filters or the state read had left them out)')
    return out


LAYER_HIT = []   # [st, park, state-layer id, name, PAD-US id it stood in for] (Nov 9 11:26 AM order)


def prefer_state_layer(st, recs, P):
    """Nov 9, Brandon 11:26 AM CST: PAD-US passes the load filters -> PAD-US; else the configured state layer (state-gis.json,
    already read; no new host) has an official record of the park's name -> that record; else the PAD-US name exception.
    A PAD-US record kept ONLY by name (not hand-joined) is left out when a state-layer record names the same POTA park.
    A hand-joined id is never dropped here (a person chose it); the overlap is only noted for Quality."""
    kept = [a for a in recs if a.get('KPC_NameKeep') and isinstance(a.get('OBJECTID'), int)]
    if not kept or not P: return recs
    idx, hand = keep_names(P, st, every=True)   # every park: a saved id's overlap with the state layer is noted
    lay = {}
    for a in recs:
        if isinstance(a.get('OBJECTID'), int) or a.get('Water'): continue   # state-layer ids carry their prefix ('ohsp12')
        k = name_keep(a, idx, {})
        if k: lay.setdefault(k[0], []).append(a)
    drop = set()
    for a in kept:
        k = name_keep(a, idx, hand)
        if not k or k[0] not in lay: continue
        for b in lay[k[0]]: LAYER_HIT.append([st, k[0], b['OBJECTID'], b.get('Unit_Nm'), a['OBJECTID']])
        if str(a['OBJECTID']) in hand and hand[str(a['OBJECTID'])][0] == k[0]:
            notice(f'US key {st}', f"{k[0]}: the state layer also names this park ({lay[k[0]][0]['OBJECTID']}); the hand-joined PAD-US {a['OBJECTID']} is kept (Quality to look)")
            continue
        drop.add(_oid(a))
    if drop:
        notice(f'US key {st}', f'{len(drop)} PAD-US record(s) kept only by name were left out: the state layer has the official record of that name (Brandon Nov 9 11:26 AM)')
    return [a for a in recs if _oid(a) not in drop]


CROSS_MAX = int(os.environ.get('KPC_PADUS_CROSS_MAX') or 60)   # at most this many cross-state asks per state (one small box each)


def pad_cross(st, P, recs, idx, hand):
    """Nov 9: a park near its state's edge with no strict-name record in this state's read: PAD-US records of its name in a
    neighbouring state, inside a 0.3 degree box around its pin (one request each, capped). Strict name test as above."""
    box = st_box(st)
    if not box: return []
    have = {}
    for a in recs:
        nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
        for v in variants(nm): have.setdefault(v, True)
    out, asked, seen = [], 0, {_oid(a) for a in recs}
    out += saved_fetch(st, P, recs)
    seen |= {_oid(a) for a in out}
    for ref, r in sorted(P.items()):
        if asked >= CROSS_MAX: notice(f'US key {st}', f'cross-state name read stopped at {CROSS_MAX} asks'); break
        name = r[0] if r else ''
        la, lo = (r[5], r[6]) if len(r) > 6 else (None, None)
        if la is None or len(norm(name).replace(' ', '')) < 8 or KM.is_admin(name): continue
        if any(v in have for v in variants(name)): continue
        if any(i in seen for i, (r2, _n) in hand.items() if r2 == ref): continue   # its hand-joined land is already read
        inside = box[0] <= lo <= box[2] and box[1] <= la <= box[3]
        edge = min(abs(lo - box[0]), abs(lo - box[2]), abs(la - box[1]), abs(la - box[3]))
        if inside and edge > .3: continue   # a pin outside its state's box (US-0329's pin is in NH) always asks
        asked += 1
        q = {'where': "State_Nm<>'%s'" % st, 'geometry': f'{lo - .3},{la - .3},{lo + .3},{la + .3}', 'geometryType': 'esriGeometryEnvelope',
             'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects', 'outFields': fields(), 'f': 'json', 'resultRecordCount': PAGE}
        q.update(GEO[GI[0]])
        j = get(q, tries=2); time.sleep(.6)
        one = {ref: r}
        i1, h1 = keep_names(one)
        for f in j.get('features', []):
            a = f.get('attributes') or {}
            if str(a.get('OBJECTID')) in seen: continue
            k = name_keep(a, i1, h1) or name_keep(a, {}, hand)
            if not k or k[0] != ref: continue
            a['KPC_NameKeep'] = f"{k[1]}; filed under {a.get('State_Nm')} in PAD-US"
            NAME_KEEP_HIT.append([st, ref, a.get('OBJECTID'), a.get('Unit_Nm') or a.get('Loc_Nm'), a['KPC_NameKeep']])
            seen.add(str(a.get('OBJECTID'))); out.append(_shape(a, f))
    return out



def layer_page_size(requested, server_max=None):
    """Ask for no more than the server page cap, so a full page is seen even when exceededTransferLimit is omitted."""
    try:
        req = int(requested)
    except (TypeError, ValueError):
        req = 500
    if req <= 0:
        req = 500
    if server_max in (None, '', 0, '0'):
        return req
    try:
        cap = int(server_max)
    except (TypeError, ValueError):
        return req
    return min(req, cap) if cap > 0 else req


def keep_paging(n_got, page, exceeded, n_new=None):
    """Next offset? Some ArcGIS servers cap a page at maxRecordCount and leave exceededTransferLimit unset.
    n_new is how many new ids this page added; 0 means the server ignored resultOffset (stop)."""
    if not n_got:
        return False
    if n_new == 0:
        return False
    if exceeded:
        return True
    return n_got >= page


CQ_KEEP = ('where', 'geometry', 'geometryType', 'inSR', 'spatialRel')
HOP_HANDLERS = ()   # extra urllib handlers (tests put a stand-in server here)
HOP_ROBOTS = {}     # robots.txt answers per host, for redirect hops


def _pace(u):
    """Nov 10 (Quality on #117, v2): the checked opener does not go through urllib.request.urlopen, so kpc_host_pace's wrap never
    sees it. Every checked request waits here instead: the first address, each redirect hop and each hop's robots.txt, 2 s per host
    (kpc_host_pace.wait); a hub portal (hub / opendata.arcgis.com, kpc_master.HUB_RE) also keeps its 60 s crawl delay."""
    h = kpc_host_pace.host_of(u)
    kpc_host_pace.wait(h)
    if KMASTER.HUB_RE.search(h.split(':')[0]):
        w = _HUB_LAST.get(h, -1e9) + KMASTER.HUB_DELAY - time.monotonic()
        if w > 0: time.sleep(w)
        _HUB_LAST[h] = time.monotonic()


_HUB_LAST = {}


def _hop_ok(u):
    """Nov 10: every redirect hop of a layer read or count gets the same checks as the first request: the saved-copy-only and
    never-contact hosts (saved_only), the master's host rule (live_ok), then that host's robots.txt (a 403 means no)."""
    if saved_only(u): raise KMASTER.LiveNotAllowed(f'redirect refused: saved copy only: {urllib.parse.urlparse(u).netloc}')
    ok, why = KMASTER.live_ok(u)
    if not ok: raise KMASTER.LiveNotAllowed(f'redirect refused: {why}')

    def robots_get(ru):
        req = urllib.request.Request(ru, headers={'User-Agent': 'KPC (kentuckyportableclub.github.io)'})
        _pace(ru)
        try:
            with KMASTER.checked_opener(_hop_host_ok, HOP_HANDLERS).open(req, timeout=60) as r: return r.status, r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e: return e.code, ''
    if not KMASTER.robots_allows(u, robots_get, HOP_ROBOTS):
        raise KMASTER.LiveNotAllowed(f'redirect refused: {urllib.parse.urlparse(u).netloc}: robots.txt does not allow this read')
    _pace(u)   # the hop itself: paced like any other request to that host


def _hop_host_ok(u):   # a robots.txt fetch that redirects: host rules only
    if saved_only(u) or not KMASTER.live_ok(u)[0]: raise KMASTER.LiveNotAllowed(f'redirect refused: {urllib.parse.urlparse(u).netloc}')
    _pace(u)


def checked_open(req, timeout):
    """urlopen through the master's checked-redirect opener (kpc_master.checked_opener): a hop is followed only after _hop_ok.
    Nov 10 (Quality on #117, v2): the ONLY way this script reads the network. The first address gets saved_only + live_ok and the
    2 s per-host pace before it is asked; every hop is checked and paced in _hop_ok."""
    u = getattr(req, 'full_url', None) or str(req)
    if saved_only(u): raise KMASTER.LiveNotAllowed(f'saved copy only: {urllib.parse.urlparse(u).netloc}')
    ok, why = KMASTER.live_ok(u)
    if not ok: raise KMASTER.LiveNotAllowed(why)
    _pace(u)
    return KMASTER.checked_opener(_hop_ok, HOP_HANDLERS).open(req, timeout=timeout)


def count_query(url, q, box=True):
    """Nov 10: a plain returnCountOnly query, built from a read query (its where, and its state box unless box=False), with NO page
    or outline parameters. With resultRecordCount the FL DEP server counts only one page window (188 of 77,144) and the NRHP
    server caps the count at the page (200); with them the DE state lands server refuses the count. None = no count."""
    if saved_only(url): return None
    c = {k: q[k] for k in CQ_KEEP if k in q and (box or k == 'where')}
    c.update({'returnCountOnly': 'true', 'returnGeometry': 'false', 'f': 'json'})
    try:
        req = urllib.request.Request(url + '?' + urllib.parse.urlencode(c), headers={'User-Agent': 'KPC (kentuckyportableclub.github.io)'})
        with checked_open(req, 120) as r: j = json.loads(r.read().decode('utf-8', 'replace'))
        return int(j['count']) if not j.get('error') and j.get('count') is not None else None
    except Exception: return None  # noqa: BLE001


def _req(url, q, post=False):
    """GET, or a POST when the request is long (an objectIds batch)."""
    h = {'User-Agent': 'KPC (kentuckyportableclub.github.io)'}
    if post: return urllib.request.Request(url, data=urllib.parse.urlencode(q).encode(), headers=h)
    return urllib.request.Request(url + '?' + urllib.parse.urlencode(q), headers=h)


def _master():
    """kpc_master (the one complete-read helper). A test that runs only this part of the file finds it from the repo root."""
    import importlib, os as _os, sys as _sys
    try: return importlib.import_module('kpc_master')
    except ImportError:
        _sys.path.insert(0, _os.path.join(_os.getcwd(), '.github', 'scripts')); return importlib.import_module('kpc_master')


READ_PARTS = ('outFields', 'f', 'resultOffset', 'resultRecordCount', 'orderByFields', 'returnCountOnly', 'returnIdsOnly', 'objectIds')


def read_all(url, q, label, max_records=None, order=True, oid_field=None):
    """Owner rule, 2026-11-10: EVERY record of this query (its where + its state box) or an error, never a partial list
    (kpc_master.read_complete: count, ids-only, records by id, else offset paging by the rows really sent). Records through
    fetch_geo (the finer outline first), count and ids through checked_open: the same paced, guarded opener."""
    KM_ = _master()
    box = {k: q[k] for k in CQ_KEEP if k in q and k != 'where'}
    ext = {k: v for k, v in q.items() if k not in CQ_KEEP and k not in READ_PARTS}

    def fj(u, params, post=False):
        if params.get('returnCountOnly') or params.get('returnIdsOnly'):
            with checked_open(_req(u, params, post), 120) as r: return json.loads(r.read().decode('utf-8', 'replace'))
        n = int(params.get('resultRecordCount') or 0) or (str(params.get('objectIds') or '').count(',') + 1)
        return fetch_geo(u, params, max_records=max_records, page=n, post=post)[0]
    mx = int(max_records or 0) or 1000
    return KM_.read_complete(url, q.get('where') or '1=1', box, fj, q.get('outFields') or '*', page_hint=min(mx, 1000), oid_field=oid_field,
                             max_record_count=mx, extra=ext, label=label, order=order)


def fetch_geo(url, q, timeout=180, max_records=None, page=None, post=False):
    """Ask for the finer outline first when one was asked for; if the server refuses or times out, fall back to
    the 0.01-degree outline every run has always used, rather than losing the layer for that state.
    max_records is the layer maxRecordCount from resolve(): request no more than that, so paging can tell a full page
    from the last page when the server omits exceededTransferLimit (FL DEP STATE_OWNED_LANDS, Nov 10)."""
    if saved_only(url): raise RuntimeError(f'saved copy only (Brandon t939u): {urllib.parse.urlparse(url).netloc}')
    tries = ([(DETAIL, PREC)] if DETAIL < 0.01 else []) + [(0.01, 3)]
    last = None
    for det, pr in tries:
        want = page or layer_page_size(PAGE if det < 0.01 else 500, max_records)   # page: a fixed window (window paging below)
        q = dict(q, maxAllowableOffset=det, geometryPrecision=pr, resultRecordCount=want)
        try:
            req = _req(url, q, post)
            with checked_open(req, timeout) as r: j = json.loads(r.read().decode('utf-8', 'replace'))
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
    b = [min(xs), min(ys), max(xs), max(ys)]
    add = BOX_ADD.get(st)   # Nov 11 (KPC owner, 2026-11-11): land the drawn state outline leaves out
    if add: b = [min(b[0], add[0]), min(b[1], add[1]), max(b[2], add[2]), max(b[3], add[3])]
    return b


# Nov 11 (KPC owner, 2026-11-11): kpc-us-states.json draws Florida as one polygon without the Keys (south edge 25.12), so every
# Florida box read missed Monroe County: FL DEP state-owned lands sent 77,144 of its 79,689 records (2,545 Keys parcels: Bahia Honda,
# Long Key, Curry Hammock, Lignumvitae Key, Indian Key, Windley Key, Fort Zachary Taylor, Key Deer lands). The box takes in the Keys
# and the Dry Tortugas. Only Florida's box changes.
BOX_ADD = {'FL': (-83.2, 24.3, -80.0, 25.2)}


def fws_state(st, have):
    # USFWS's own land layer (PAD-US misses some refuges) is on services.arcgis.com: never read live, its records come from the saved copy
    SAVED_ONLY_SKIPPED.setdefault(st, set()).add('fws'); return []


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
SFIELDS = {}   # Nov 6: prefix -> the layer's field list (read by resolve(), which already asks the layer for it)
SFMAP = {}     # Nov 6: prefix -> kpc_source_fields mapping
import kpc_source_fields as SF  # noqa: E402
import kpc_tracts as TR  # noqa: E402
def resolve(pre, url, nf, af):
    # 'svc:<service>|<layer name regex>' → (query url, name field, acres field, object id field)
    def rq(u):
        if saved_only(u): raise RuntimeError(f'saved copy only: {urllib.parse.urlparse(u).netloc}')   # Nov 10: never asked, robots.txt included
        with checked_open(urllib.request.Request(u, headers={'User-Agent': 'KPC (kentuckyportableclub.github.io)'}), 120) as r:   # Nov 10: every hop checked + paced
            return json.loads(r.read().decode('utf-8', 'replace'))
    if not url.startswith('svc:'):
        if not pre.startswith('sg'): return url, nf, af, ('objectid' if pre in ('wld', 'fwsr', 'fsod') else 'OBJECTID')
        if pre in RESOLVED: return RESOLVED[pre]
        L = rq(url.rsplit('/query', 1)[0] + '?f=json'); flds = L.get('fields') or []     # a state GIS layer: ask it for its own id + acres fields
        if 'Polygon' not in str(L.get('geometryType', '')): raise RuntimeError('not a polygon layer')
        oid = L.get('objectIdField') or next((f['name'] for f in flds if f.get('type') == 'esriFieldTypeOID'), 'OBJECTID')
        acres = next((f['name'] for f in flds if re.search(r'acre', f['name'], re.I)), '')
        SFIELDS[pre] = [f['name'] for f in flds if f.get('name')]   # Nov 6: for kpc_source_fields AUTO (no extra request)
        if L.get('maxRecordCount'):
            LAYER_MAXREC[pre] = int(L['maxRecordCount'])
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
    SFIELDS[pre] = [f['name'] for f in flds if f.get('name')]
    if L.get('maxRecordCount'):
        LAYER_MAXREC[pre] = int(L['maxRecordCount'])
    RESOLVED[pre] = (f'{svc}/{lid}/query', name, acres, oid)
    notice('US key layer found', f'{pre}: {svc}/{lid} [{pick[0].get("name")}] name={name} acres={acres} oid={oid}')
    return RESOLVED[pre]
XCOUNT = {}
LAYER_MAXREC = {}   # prefix -> layer maxRecordCount (resolve); used so paging does not stop on a silent server cap
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


def _sane_ac(ac, bb):
    """Oct 29 (chat 11's sweep: Standing Boy Creek SP '68,840,167 acres' = square FEET): a state layer's 'acres' field is checked
    against the record's own box: a number bigger than the box can hold is converted (square feet, square metres, hectares)
    when that makes it fit, else left out (0 = no size on file)."""
    if not ac or not bb: return ac or 0
    k = math.cos(math.radians((bb[1] + bb[3]) / 2))
    box = max((bb[2] - bb[0]) * 111.32 * k, .01) * max((bb[3] - bb[1]) * 110.57, .01) * 247.105 * 1.6   # km2 -> acres, with room for the coarse copy
    if ac <= box: return ac
    for div in (43560.0, 4046.86):        # square feet, square metres
        if ac / div <= box: return round(ac / div, 1)
    return 0


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
            if saved_only(url): SAVED_ONLY_SKIPPED.setdefault(st, set()).add(pre); continue   # Nov 10: services*.arcgis.com and the listed hosts, saved copy only
            if url not in ZIPC:
                with checked_open(urllib.request.Request(url, headers={'User-Agent': 'KPC (kentuckyportableclub.github.io)'}), 240) as r: ZIPC[url] = zipfile.ZipFile(io.BytesIO(r.read()))   # Nov 10: every hop checked + paced
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
        lf = _layer_in(st, pre)   # Nov 10: a checked download the master step put down is read instead of the live layer
        if lf is None and saved_only(url): SAVED_ONLY_SKIPPED.setdefault(st, set()).add(pre); continue   # owner rule, Nov 9: the saved copy has it
        if lf is not None:
            _lm, _lfe = lf
            nf = _lm.get('name_field') or nf; af = _lm.get('acres_field') or af; oidf = _lm.get('oid_field') or 'OBJECTID'
        else:
            try: url, nf, af, oidf = resolve(pre, url, nf, af)
            except Exception as e:  # noqa: BLE001
                notice(f'US key {st}', f'{label} layer not found ({e})'); continue
        n = 0
        # Nov 6 (big key / 2-fer patch): the layer's stable id / official acres / owner / parent fields (kpc_source_fields: the one
        # table, or AUTO from the field list a state layer already gave resolve()). ADDED to this same query; refused = asked without.
        _sfm = SF.mapping(url, x[5], SFIELDS.get(pre))
        _sfx = [f for f in SF.extra_fields(_sfm) if f and f.lower() not in {str(q).lower() for q in (oidf, nf, af, opt.get('nm2')) if q}]
        SFMAP[pre] = _sfm
        order = True   # Oct 29 (chat 2, Nags Head Woods missing): paging WITHOUT a sort order can skip records between pages; sort by the id
        seen_ids = set()
        q = {'where': opt.get('where') or '1=1', 'geometry': ','.join(map(str, box)), 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
             'outFields': ','.join(q for q in (oidf, nf, af, opt.get('nm2'), *_sfx) if q), 'returnGeometry': 'true', 'outSR': 4326, 'f': 'json'}
        if lf is not None:   # the whole layer file, the same state box as the live query
            fs = [{'attributes': {k: v for k, v in (ft.get('properties') or {}).items() if k != '_kpc'}, 'geometry': _G2R(ft.get('geometry'))}
                  for ft in _lfe if _in_box(ft.get('geometry'), box)]
        else:
            # Owner rule, 2026-11-10: the whole layer in the state box or nothing (read_all: count, ids, by id, else offset paging
            # by the rows really sent). A short read is a FAILED read: the state keeps its saved copy, never half a layer.
            fs = None
            while fs is None:
                try:
                    _rk = (url, q['where'], q['geometry'], q['outFields'], order)   # one layer under two prefixes (MD, OR) is read once
                    fs, how = READ_ONCE.get(_rk) or read_all(url, q, f'{label} ({st})', LAYER_MAXREC.get(pre), order=order, oid_field=oidf)
                    READ_ONCE[_rk] = (fs, how)
                except Exception as e:  # noqa: BLE001
                    KM_ = _master()
                    if not isinstance(e, (KM_.ShortRead, KM_.LayerStall, KM_.LiveNotAllowed)):
                        if _sfx:    # Nov 6: an added source field refused: read the layer exactly as before
                            _sfx = []; q['outFields'] = ','.join(x for x in (oidf, nf, af, opt.get('nm2')) if x); continue
                        if order:   # a server that cannot sort: read it without an order
                            order = False; continue
                    notice(f'US key {st}', f'{label} not read ({e})'); FAILED_READ.add(st); break
            if fs is None:
                if LAYER_OUT is not None: RAWF.setdefault(pre, [])
                continue
            if how.get('short_page'):
                notice(f'US key {st}', f"{label}: short pages without exceededTransferLimit: the layer was read window by window to its count ({how['count']})")
        for f in fs:
            a = {k.lower(): v for k, v in (f.get('attributes') or {}).items()}
            if a.get(oidf.lower()) in seen_ids: continue
            seen_ids.add(a.get(oidf.lower()))
            if LAYER_OUT is not None: RAWF.setdefault(pre, []).append(f)
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
                        'Loc_Mang': label, 'Des_Tp': '', 'GIS_Acres': _sane_ac(_num(a.get(af.lower()) if af else 0), bbox(g)), 'Category': 'Fee', '_bb': bbox(g), '_g': g, '_k': k,
                        **({'Water': 1} if opt.get('water') else {}),
                        **({'SA': {f: a.get(f.lower()) for f in _sfx if a.get(f.lower()) not in (None, '', ' ')}} if _sfx and any(a.get(f.lower()) not in (None, '', ' ') for f in _sfx) else {})})
            n += 1
        XCOUNT[pre] = XCOUNT.get(pre, 0) + n
    return out


READ_ONCE = {}   # (query url, where, box, fields, order) -> a complete read of this run


def _in_box(g, box):
    b = bbox(_G2R(g)) if g and 'rings' not in g else bbox(g)
    return bool(b) and not (b[2] < box[0] or b[0] > box[2] or b[3] < box[1] or b[1] > box[3])


def _G2R(g):
    if not g or 'rings' in g: return g or {}
    return KMASTER.geojson_to_rings(g)


def _layer_in(st, pre):
    """(meta, features) of a checked download for this state and layer, or None."""
    if LAYER_IN is None: return None
    p = KMASTER.layer_file_path(LAYER_IN, f'US-{st}', pre)
    if not p.exists(): return None
    try: return KMASTER.read_layer_file(p)
    except Exception as e: notice(f'US key {st}', f'layer file {p.name} unreadable ({e}); not used'); return None  # noqa: BLE001


def layer_live_count(st, pre, url, nf, af, opt):
    """How many features the live layer would return for this state's box (returnCountOnly; no geometry).
    Saved-copy-only hosts are not asked. A failed count is None (the saved copy is left as it is)."""
    if saved_only(url):
        return None
    box = st_box(st)
    if not box:
        return None
    try:
        url, nf, af, oidf = resolve(pre, url, nf, af)
    except Exception:
        return None  # noqa: BLE001
    q = {'where': (opt or {}).get('where') or '1=1', 'geometry': ','.join(map(str, box)), 'geometryType': 'esriGeometryEnvelope',
         'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects'}
    return count_query(url, q)   # Nov 10: no page or outline parameters on a count (they cut or refuse it)


def _one_state_layer(pre, st):
    """Nov 11 r2: True when every XS entry of this prefix (and of its address) belongs to this one state only."""
    ys = [y for y in XS if y[0] == pre]
    if not ys: return False
    u = ys[0][1]
    ys += [y for y in XS if y[1] == u and y[0] != pre]
    return all(len(y) > 7 and y[7] is not None and set(y[7]) == {st} for y in ys)


def layer_total_count(pre, url, nf, af, opt):
    """Nov 11: the layer's own total for its where, with NO state box (returnCountOnly). Saved-copy-only hosts are not asked; None = no count."""
    if saved_only(url): return None
    try: url, nf, af, oidf = resolve(pre, url, nf, af)
    except Exception: return None  # noqa: BLE001
    return count_query(url, {'where': (opt or {}).get('where') or '1=1'}, box=False)


# ------------------------------------------------------------------------------------------------ the shared scoring
# Oct 22 (Fable's review): one weighing of the evidence for every country, in kpc_match.py. This is the US side of it:
# it READS the names the US way and hands kpc_match plain facts. It runs in SHADOW next to the matcher above - its
# verdict is recorded wherever it disagrees, nothing it says changes a join - until the disagreements have been read.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kpc_match as KM  # noqa: E402
import kpc_master as KMASTER  # noqa: E402  (Nov 10: layer files + the never-half-written saves; not a rule file)
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
# Oct 30 (chat 2, HQ Oct 29 8:50 PM 'the Recreation.gov saved copy holds the BLM sites'): the ONE keyed pull (KPC-Data
# data/access-leads/keyed-pull-raw.json.gz: ridb_rec + ridb_fac, id / name / lat-lon). POTA built many BLM / Forest Service sites
# from Recreation.gov, so a same-name Recreation.gov point near the pin is the park's own record: an official polygon that HOLDS that
# point and carries the same name is joined (G-1 location proof). No new calls: the saved copy only, read when present.
# Oct 30 (Brandon 10:43 PM picked A, via chat 3): a NATIONAL TRAIL park (NHT / NST / NRT) whose official line the agency publishes
# (data/trails/<ref>.json, listed in data/trails/index.json by the Park Service / Forest Service / BLM) carries that LINE as its
# record in the key: id 'trl<number>', grade official, line: 1. Every outline tool then follows it; Am I in the Park uses POTA's
# 100-ft band from the line (never an inside test). Only a park with no other official piece gets it.
# Oct 30 11:05 PM: trails whose only official line is a DRIVING route (roads), not the trail: held until Brandon rules
# (US-4582 Washington-Rochambeau = the NPS 'WARO driving route centerline (2016)')
DRIVING_ONLY = set()   # Oct 30 11:05 PM: Brandon's ruling (Lewis and Clark 'needs both') = a trail's official driving route counts too
TRL = {}
try:
    for _x in json.load(open('data/trails/index.json')):
        if str(_x.get('kind') or '') != 'WSR' and re.search(r'service|bureau|agency|department|usfs|nps|blm|fws', str(_x.get('by')), re.I): TRL[_x['ref']] = _x
except Exception as _e: print(f'trail lines index not read: {str(_e)[:80]}', flush=True)  # noqa: BLE001
try:   # Oct 31 (Brandon's missing-boundaries sheet: 68 state / national recreation trails already have an OFFICIAL line saved by the
       # trails bot, data/trails/index-state.json official: true): they carry it too. Wild & scenic rivers keep their own rules (R6).
    for _x in json.load(open('data/trails/index-state.json')):
        if _x.get('official') and str(_x.get('kind') or '') != 'WSR' and _x.get('ref') not in TRL: TRL[_x['ref']] = _x
except Exception as _e: print(f'state trail lines index not read: {str(_e)[:80]}', flush=True)  # noqa: BLE001
RIDB = {}
try:
    import gzip as _gz
    _rj = json.load(_gz.open(os.environ.get('RIDB_FILE') or 'data/access-leads/keyed-pull-raw.json.gz', 'rt', encoding='utf-8'))
    for _k in ('ridb_rec', 'ridb_fac'):
        for _st, _xs in (_rj.get(_k) or {}).items():
            RIDB.setdefault(_st, []).extend(x for x in _xs if x.get('la') and x.get('lo'))
    print(f'Recreation.gov saved copy: {sum(len(v) for v in RIDB.values())} points', flush=True)
except Exception as _e: print(f'Recreation.gov saved copy not read: {str(_e)[:80]}', flush=True)  # noqa: BLE001


def near_ring(la, lo, g, km):
    """Oct 31 (Fable review #18): the key matches on a ROUGH copy (DETAIL ~1 km), so 'pin inside' also passes when the pin is within that
    slack of the rough line (segment distance, km)."""
    k = math.cos(math.radians(la)) * 111.32
    for r in rings(g):
        for (x1, y1), (x2, y2) in zip(r, r[1:]):
            ax, ay, bx, by = (x1 - lo) * k, (y1 - la) * 110.57, (x2 - lo) * k, (y2 - la) * 110.57
            dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
            t_ = 0 if L == 0 else max(0, min(1, -(ax * dx + ay * dy) / L))
            if math.hypot(ax + t_ * dx, ay + t_ * dy) <= km: return True
    return False


def inside_slack(la, lo, g):
    return inside(la, lo, g) or near_ring(la, lo, g, DETAIL * 111.0)


def _km(la1, lo1, la2, lo2):
    return 111.2 * math.hypot(la1 - la2, (lo1 - lo2) * math.cos(math.radians((la1 + la2) / 2)))
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


def _save_row(a):
    r = {k: v for k, v in a.items() if not k.startswith('_')}
    r['_r'] = [[[round(pt[0], 5), round(pt[1], 5)] for pt in ring if len(pt) >= 2] for ring in rings(a.get('_g'))]
    r['_k'] = sorted(a.get('_k') or [])
    r['rd'] = a.get('rd') or time.strftime('%Y-%m-%d')   # the day this record was read from its agency (rule B7)
    return r


def _write_layer_files(st, want, add):
    """Nov 10: one layer file per re-read layer for the master step (it checks, trims, records and merges; nothing merged here)."""
    xs = {}
    for x in XS: xs.setdefault(x[0], x)
    kept = {}
    for a in add: kept.setdefault(KMASTER.prefix_of(a.get('OBJECTID')), {})[str(a['OBJECTID'])] = _save_row(a)
    n = 0
    for pre in sorted(want):
        lf = _layer_in(st, pre)
        if pre not in RAWF and lf is None: continue   # not read: saved-copy-only host, the layer did not answer, or nothing in this state
        x = next((y for y in XS if y[0] == pre and (len(y) <= 7 or y[7] is None or st in y[7])), xs.get(pre)); url = x[1] if x else ''   # Nov 10: this state's entry (its own where), not the first one
        oidf = (RESOLVED.get(pre) or (None, None, None, 'OBJECTID'))[3] if lf is None else (lf[0].get('oid_field') or 'OBJECTID')
        feats, _ids = [], set()
        for f in RAWF.get(pre, []):
            at = f.get('attributes') or {}
            oid = next((v for k, v in at.items() if k.lower() == str(oidf).lower()), None)
            if oid is not None and str(oid) in _ids: continue   # distinct object ids: a record read twice is one record
            _ids.add(str(oid))
            try: geo = KMASTER.esri_to_geojson(f.get('geometry'))
            except Exception: geo = None  # noqa: BLE001
            feats.append({'type': 'Feature', 'properties': dict(at, _kpc=kept.get(pre, {}).get(f'{pre}{oid}')), 'geometry': geo})
        meta = {'area': f'US-{st}', 'layer': pre, 'url': url, 'label': x[5] if x else '', 'oid_field': oidf, 'count_raw': len(feats),
                'name_field': (RESOLVED.get(pre) or (None, x[2] if x else ''))[1] if lf is None else lf[0].get('name_field'),
                'source': 'live' if lf is None else 'hand', 'read': time.strftime('%Y-%m-%d')}
        if lf is None:
            meta['count_live'] = layer_live_count(st, pre, url, x[2], x[3], x[8] if len(x) > 8 else {}) if x else None
            # Nov 11: a layer of this state only (a state-GIS row) is also counted WITHOUT the box: the master step refuses a read
            # whose box left records of the layer's own total out (sgflf: 77,144 in the box of 79,689), unless layers.json allows it
            # (Nov 11 r2, Quality: one-state = EVERY XS entry of the prefix is this state's; NRHP and the USACE layer are listed once per
            # state, and their unboxed total is the whole country). The key is always written for such a layer: None = the count failed,
            # and the master step HOLDS the read (fail closed)
            if x and _one_state_layer(pre, st): meta['count_layer'] = layer_total_count(pre, url, x[2], x[3], x[8] if len(x) > 8 else {})
        else:
            meta.update({k: lf[0].get(k) for k in ('count_expected', 'raw', 'page', 'by') if lf[0].get(k) is not None})
            meta['count_raw'] = sum(1 for ft in lf[1] if _in_box(ft.get('geometry'), st_box(st)))
            meta['url'] = lf[0].get('url') or url
        KMASTER.write_layer_file(KMASTER.layer_file_path(LAYER_OUT, f'US-{st}', pre), meta, feats)
        n += 1
    notice(f'US key {st}', f'refill: {n} layer file(s) written for the master step ({" ".join(sorted(want))})')


def save_cache(st, recs, seen):
    """Everything the matcher needs, so a rule can be tested without the network. Outlines to ~1 m."""
    CACHE.mkdir(parents=True, exist_ok=True)
    rows = [_save_row(a) for a in recs]
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
        # Oct 30 (chat 11: Standing Boy back at 68.8 M acres): a SAVED copy made before the Oct 29 acres check carries the raw number;
        # check it again on load, so the nightly boundary check (GEO_CACHE_MODE) gives the same size as a fresh read
        if str(a.get('OBJECTID', '')).startswith('sg') and a.get('GIS_Acres'): a['GIS_Acres'] = _sane_ac(a['GIS_Acres'], a['_bb'])
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
# Nov 9 evening (Brandon t919u, 4:48 PM CST: pins and names are only sanity checks, the official boundary is right most of the time;
# 'a bad ID block list'): overrides.json 'blocked_ids' = [{ref, id, reason, decided_by}]. A listed id is never used for that park:
# it leaves the park's saved joins (join / fp) and becomes a NO, so the park goes back to normal matching (or to a person).
# An entry without decided_by is ignored (and named in the log), so no block happens without a person.
BLOCKED = {}
try:
    for _b in json.load(open(OUT / 'overrides.json')).get('blocked_ids') or []:
        if not (_b.get('ref') and _b.get('id') not in (None, '')): continue
        if not str(_b.get('decided_by') or '').strip(): print(f"::warning title=Blocked ids::{_b.get('ref')} {_b.get('id')}: no decided_by, ignored", flush=True); continue
        BLOCKED.setdefault(_b['ref'], set()).add(str(_b['id']))
except Exception: pass  # noqa: BLE001
for _r, _ids in BLOCKED.items():
    _o = OVR.setdefault(_r, {})
    _o['join'] = [x for x in _o.get('join') or [] if str(x) not in _ids]
    if _o.get('fp'): _o['fp'] = {k: v for k, v in _o['fp'].items() if str(k) not in _ids}
    _o['no'] = list(_o.get('no') or []) + sorted(_ids - {str(x) for x in _o.get('no') or []})
def _oid(a): return str(a['OBJECTID'])
# Nov 2 review: one set of rules for a person's NO in every join path, a name check on id joins, self-checks and confidence
# (kpc_key_rules.py; every rule has its own switch, see that file). Missing file = today's behaviour.
try:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import kpc_key_rules as KR
except Exception: KR = None  # noqa: BLE001
def _kr(name): return KR is not None and KR.on(name)


def _hand_ids(recs, P):
    """batch 1b (Quality, the Canada lesson): every record id a person joined by hand, AFTER the fingerprint re-find: an
    overrides 'join' id that is gone from this read is found again by its saved name + acres (within 10%) near the pin, the
    same test the join path uses, and the NEW id is kept too. Before, only the old raw ids were kept."""
    out = set()
    for ref, v in OVR.items():
        v = v or {}
        r = P.get(ref) or []   # this state's parks (P from run())
        la, lo = (r[5], r[6]) if len(r) > 6 else (None, None)
        if la is None and ref in pins(): la, lo = pins()[ref]
        for x in v.get('join') or []:
            out.add(str(x))
            fp = (v.get('fp') or {}).get(str(x))
            if not fp or any(_oid(a) == str(x) for a in recs): continue
            fn, fa = fp[:2]
            out |= {_oid(a) for a in recs if _nf(a.get('Unit_Nm') or a.get('Loc_Nm') or '') == _nf(fn) and (la is None or near(la, lo, a.get('_bb'), .6))
                    and abs((a.get('GIS_Acres') or 0) - (fa or 0)) <= max(20, .1 * (fa or 0))}
    return out


def _share_inside(a, b, n=24):
    """batch 1b: the share (0..1) of record a's land that lies inside record b, from their outlines; None if either has none.
    shapely when it is installed, else a 24 x 24 grid of points over a (the Canada fill uses the same grid)."""
    ga, gb = a.get('_g'), b.get('_g')
    if not rings(ga) or not rings(gb): return None
    try:
        from shapely.geometry import Polygon
        def _shp(g):
            u = None
            for r in rings(g):
                if len(r) < 4: continue
                q = Polygon(r).buffer(0)
                u = q if u is None else u.symmetric_difference(q)
            return u
        pa, pb = _shp(ga), _shp(gb)
        if pa is None or pb is None or not pa.area: return None
        return pa.intersection(pb).area / pa.area
    except ImportError: pass
    except Exception: return None  # noqa: BLE001
    w, s_, e, n_ = bbox(ga); hit = tot = 0
    for i in range(n):
        for j in range(n):
            x, y = w + (i + .5) * (e - w) / n, s_ + (j + .5) * (n_ - s_) / n
            if inside(y, x, ga):
                tot += 1; hit += inside(y, x, gb)
    return hit / tot if tot else None
def _no_all(ov, a):   # KPC_NO_ALL_PATHS: True when a person ruled this record out (id, exact name, or with KPC_NO_BY_NAME the saved name)
    return _kr('KPC_NO_ALL_PATHS') and KR.is_no(ov, _oid(a), a.get('Unit_Nm') or a.get('Loc_Nm') or '', a.get('GIS_Acres'))

# Nov 3 (Mapping, answer sheet: inbox 2026-11-03-answer-sheet/DESIGN.md, remade after Quality's grade R1-R4): KPC-Data
# data/answer-sheet/US.csv ties a park to its official record (layer + record id + key id + fp [name, acres] + the agency's unit id).
# READ ONLY: this engine never writes it.  KPC_ANSWER_SHEET = off (default: today's behaviour) | add (YES rows join like hand
# joins) | first (a park with YES rows takes ONLY them + its overrides joins; the builder's own guesses for it go to 'check').
# Precedence: overrides 'no' (id OR name) > overrides 'join' > YES sheet rows > the builder's guessing. Status words are the shared
# list in kpc_answer_words.py (YES / NO / PIN / FIXED / NOT SURE). A row in NOT SURE / PIN / FIXED / any unknown word, a bad cell,
# or a YES row whose record vanished or changed is a NOT SURE question: the park never falls back to a guess. A person answers it
# in an inbox batch (Quality then writes YES or NO on the row); a NO row is enforced like an overrides 'no' for that record id
# (R5, Quality grade Nov 3: before, a typed NO was skipped and the builder's own name match could still join that record).
SHEET_MODE = (os.environ.get('KPC_ANSWER_SHEET') or 'off').strip().lower()
SHEET, SHEET_GREEN, SHEET_STAT, SHEET_NO = {}, False, {}, {}
def _sst(k): SHEET_STAT[k] = SHEET_STAT.get(k, 0) + 1
def _sheet_rows(path, appr, who, chk):
    """One row at a time (R3): a bad row becomes NOT SURE for its park, never switches the whole sheet off."""
    import csv as _csv, kpc_answer_words as AW
    out = {}
    for _r in _csv.DictReader(open(path, encoding='utf-8')):
        ref, kid = (_r.get('ref') or '').strip(), str(_r.get('key_id') or '').strip()
        if not ref or not kid: _sst('no key id (layer not read here)'); continue
        u = AW.use(_r.get('status'))
        if not AW.word(_r.get('status'))[1]: _sst('unknown status word: NOT SURE')
        if u == 'proposed': _sst('proposed (not used)'); continue
        fp = AW.fp_cell(_r.get('fp'))
        if u == 'ignore':   # R5 (Quality, Nov 3 re-cut): a typed NO is ENFORCED as an overrides-style 'no' for that record id (+ its fp)
            SHEET_NO.setdefault(ref, {})[kid] = list(fp) if fp and fp[0] else None; _sst('NO (enforced as a no for that record)'); continue
        st = 'NOT SURE'
        if fp is None: _sst('bad fp cell: NOT SURE'); fp = ('', None)
        elif u == 'join':
            if appr == 'B' and not AW.signed_off(_r.get('approved_by'), _r.get('approved_date'), who):
                _sst('YES without a person sign-off + date (option B): not used'); continue
            st = 'NOT SURE' if (chk.get(f'{ref}|{kid}') or {}).get('state', '') in ('VANISHED', 'CHANGED') else 'OK'
        out.setdefault(ref, []).append({'id': kid, 'fp': [fp[0], fp[1]], 'st': st}); _sst(st.lower())
    return out
def _sheet_no_into(ovr, sno):
    """R5: a sheet NO row becomes a 'no' (+ 'nofp' when its fp cell has a name and acres) for that park, IN MEMORY only (this engine
    never writes overrides.json), so every 'no' path - the m filter, drop_no, alias, kept-outline, the sheet's own R4 - sees it."""
    for _ref, _ids in sno.items():
        _o = dict(ovr.get(_ref) or {}); _have = {str(x) for x in _o.get('no', [])}
        _o['no'] = list(_o.get('no', [])) + [i for i in sorted(_ids) if i not in _have]
        _nf_ = {i: v for i, v in _ids.items() if v and v[1]}
        if _nf_: _o['nofp'] = {**_nf_, **(_o.get('nofp') or {})}
        ovr[_ref] = _o
if SHEET_MODE in ('add', 'first'):
    try:
        import datetime as _dt, kpc_answer_words as _AW
        _appr = (os.environ.get('KPC_SHEET_APPROVAL') or 'B').strip().upper()   # A: Quality's YES alone; B (default): + a person's sign-off
        _who = _AW.persons(os.environ.get('KPC_SHEET_PERSONS'))
        _chk = {}
        try:   # the nightly vanished/changed check (KPC-Data kpc_answer_sheet_check.py): green AND under 36 h old = hand-join protection
            _cj = json.load(open(os.environ.get('ANSWER_SHEET_CHECK') or 'data/answer-sheet/check/US.json', encoding='utf-8'))
            _age = time.time() - _dt.datetime.fromisoformat(str(_cj.get('built')).replace('Z', '+00:00')).timestamp()
            SHEET_GREEN = _cj.get('green') is True and 0 <= _age < 36 * 3600
            _chk = _cj.get('rows') or {}
        except Exception: SHEET_GREEN = False  # noqa: BLE001
        SHEET = _sheet_rows(os.environ.get('ANSWER_SHEET_FILE') or 'data/answer-sheet/US.csv', _appr, _who, _chk)
        _sheet_no_into(OVR, SHEET_NO)
        notice('Answer sheet', f"mode {SHEET_MODE}, approval {_appr}, nightly check {'green' if SHEET_GREEN else 'NOT green: rows join without hand-join protection'}: {SHEET_STAT}")
    except Exception as e:  # noqa: BLE001  (no sheet file / no module: today's behaviour, said once)
        SHEET = {}; notice('Answer sheet', f"not read ({str(e)[:120]}); today's behaviour")
def _sheet_no(ov, a):
    """R4: overrides 'no' always beats the sheet, by id OR by exact name, even with KPC_NO_ALL_PATHS switched off."""
    nos = {str(x) for x in ov.get('no', [])}
    return _oid(a) in nos or _nf(a.get('Unit_Nm') or a.get('Loc_Nm') or '') in {_nf(x) for x in nos} or _no_all(ov, a)


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


ACRES_OFF = None
def _official_acres():
    global ACRES_OFF
    if ACRES_OFF is None:
        ACRES_OFF = {}
        try:
            d = json.load(open('data/acres.json')); d = d.get('parks', d) if isinstance(d, dict) else {}
            for r_, v in d.items():
                try: ACRES_OFF[r_] = float(v.get('acres') if isinstance(v, dict) else v)
                except (TypeError, ValueError): pass
        except Exception: pass  # noqa: BLE001
    return ACRES_OFF


def _selfchk(st, parks, recs):
    """Nov 2 review. KPC_SELF_CHECKS=report notes problems in parks[ref]['self']; =hold also moves the park to check (no outline).
    KPC_CONF_SORT=1 writes review/unsure-US-<st>.json: only the parks a person needs to see, each with a one-line reason."""
    mode = KR.setting('KPC_SELF_CHECKS') if KR is not None else '0'
    if KR is None or (mode in ('0', 'off', '') and not _kr('KPC_CONF_SORT')): return
    bbs = [a['_bb'] for a in recs if a.get('_bb')]
    box_ = (min(b[1] for b in bbs), min(b[0] for b in bbs), max(b[3] for b in bbs), max(b[2] for b in bbs)) if bbs else None
    ko = lambda t, nm: (not _tags(t)) or (not _tags(nm)) or bool(_tags(t) & _tags(nm))
    probs = {}
    for ref, p in parks.items():
        if mode in ('0', 'off', ''): break
        pr = (P_ALL.get(ref) or [])
        q = dict(p, la=pr[5] if len(pr) > 6 else None, lo=pr[6] if len(pr) > 6 else None)
        bad = KR.self_checks(ref, q, box_, _official_acres().get(ref), ko)
        if not bad: continue
        probs[ref] = bad; p['self'] = bad
        if mode == 'hold' and p.get('m'):
            p['c'] = [x[:3] + ['self-check: ' + bad[0]] for x in p['m']] + list(p.get('c') or []); p['m'] = []
    if probs: notice(f'US key {st}', f'self-checks: {len(probs)} park(s) with a problem ({mode})')
    if _kr('KPC_CONF_SORT'):
        for ref, p in parks.items(): p['conf'], p['conf_why'] = KR.confidence(p, probs.get(ref) or ())
        R_ = OUT / 'review'; R_.mkdir(exist_ok=True)
        save_json(R_ / f'unsure-US-{st}.json', {'st': st, 'note': 'Nov 2 review: only the parks a person needs to see, with why', 'parks': KR.unsure_list(parks, probs)})


P_ALL = {}
PAD_MAP = SF.mapping('PAD-US/PAD_US/MapServer')
FWS_MAP = SF.mapping(FWS)
NPS_CODES = None
def _nps_code(name):
    """NPS UNIT_CODE from the Park Service's own unit list (data/nps-units.json, NPS API parkCode = the 4-letter UNIT_CODE), by full name."""
    global NPS_CODES
    if NPS_CODES is None:
        try: NPS_CODES = {_nf(u['name']): u['code'] for u in json.load(open('data/nps-units.json'))['units']}
        except Exception: NPS_CODES = {}  # noqa: BLE001
    return NPS_CODES.get(_nf(name))


def _tract_store(st, parks, recs):
    """Nov 6 (big key / 2-fer patch): the side file data/us-key/tracts/US-<st>.json (kpc_tracts.py): one tract record per official
    record joined to a park (source, stable id, official + measured acres, owner, access, fee / easement / approved boundary), and
    parks inside parks. KPC_TRACT_STORE=0 turns it off. Never changes the key."""
    if not TR.on(): return
    try:
        byid = {_oid(a): a for a in recs}
        PT, shapes = {}, {}
        for ref, p in parks.items():
            ts, rg = [], []
            for q in p.get('m') or []:
                a = byid.get(str(q[0]))
                if a is None:
                    ts.append(TR.tract(q[0], q[1], q[3] if len(q) > 3 else '', src_key='other', ac_key=q[2] if len(q) > 2 else None)); continue
                oid = str(a.get('OBJECTID'))
                if isinstance(a.get('OBJECTID'), int): mp, lay, attrs = PAD_MAP, PADVER[0], a
                elif oid.startswith('fws'): mp, lay, attrs = FWS_MAP, 'U.S. Fish & Wildlife Service (own map)', dict(a.get('SA') or {}, SUM_GISACRES=a.get('GIS_Acres'))
                else:
                    pre = re.match(r'[a-z]*', oid).group(0)
                    _x = next((x for x in XS if x[0] == pre), None)
                    # a saved copy (GEO_CACHE_MODE use / only) did not ask the layer for its fields this run: the fields saved with the
                    # record (SA) are the field list, the table row is found by the layer url
                    mp = SFMAP.get(pre) or SF.mapping(_x[1] if _x else '', _x[5] if _x else '', SFIELDS.get(pre) or list((a.get('SA') or {}).keys()))
                    if not mp.get('key') or mp.get('key') == 'auto': mp = dict(mp, key=pre)   # AUTO / no table row: the layer's own prefix
                    lay, attrs = a.get('Loc_Mang') or pre, dict(a.get('SA') or {})
                t = TR.tract(q[0], q[1], q[3] if len(q) > 3 else '', attrs, mp, rings(a.get('_g')), lay)
                if t.get('ac') is None and a.get('GIS_Acres'): t['ac'] = round(float(a['GIS_Acres']), 1)
                if str(a.get('Mang_Name') or '') == 'NPS' or re.search(r'park service', str(a.get('Loc_Mang') or ''), re.I):
                    _uc = _nps_code(q[1]) or _nps_code(p.get('n'))
                    if _uc: t['unit_code'] = _uc
                ts.append(t); rg += rings(a.get('_g'))
            if ts: PT[ref] = ts
            if rg: shapes[ref] = rg
        nested = TR.nested_geometry(shapes)
        _hits = [x for x in PUBACC_HIT if x['st'] == st]
        _flag = {}
        for x in _hits:
            f = _flag.setdefault(x['park'], {'park': x['park'], 'closed_pieces': [], 'closed_acres': 0})
            f['closed_pieces'].append({'rid': x['rid'], 'name': x['name'], 'acres': x['acres'], 'why': x['why']}); f['closed_acres'] += x['acres'] or 0
        for f in _flag.values():
            f['joined_acres'] = sum(round(t.get('ac') or 0) for t in PT.get(f['park']) or [])
            f['note'] = 'flag only: the park and every join are kept (report only; piece-level vs park-level policy = Brandon)'
        extra = {'pub_access': {'mode': PUBACC + ' (report only: never changes a join, never drops a park)', 'parks_flagged': sorted(_flag.values(), key=lambda f: f['park'])}}
        d = TR.doc(f'US-{st}', PT, nested, 'US: PAD-US, USFWS, the federal layers and the state-agency layers the key reads.')
        d.update(extra); d['ac_measured_detail_deg'] = DETAIL   # measured acres come from the outline the key read (0.01 deg = coarse)
        TR.save(OUT / 'tracts' / f'US-{st}.json', d)
        if any(x['st'] == st for x in PUBACC_HIT):
            notice(f'US key {st}', f"public access ({PUBACC}): {sum(1 for x in PUBACC_HIT if x['st'] == st)} join(s) are to land PAD-US marks closed / not open"
                                   + f" in {len({x['park'] for x in PUBACC_HIT if x['st'] == st})} park(s): flagged only, every join kept")
    except Exception as _e:  # noqa: BLE001
        notice(f'US key {st}', f'tract records skipped: {type(_e).__name__}: {str(_e)[:160]}')


# Nov 6 (big key / 2-fer patch): KPC_US_FS_OWNED = 0 (default: today) | 1: a National Forest / Grassland park gets the same
# 'owned_only' marker the KY answer key gives Daniel Boone, so the website and the 2-fer program both say 'Forest Service-owned land
# only (Basic Ownership map, OWNERCLASSIFICATION = USDA FOREST SERVICE)'. The 2-fer program already masks by it (kpc_owned.py).
FS_OWNED = (os.environ.get('KPC_US_FS_OWNED') or '0').strip().lower() not in ('0', 'off', 'no', '')
def _fs_owned_note(parks):
    if not FS_OWNED: return
    for p in parks.values():
        if p.get('m') and re.search(r'national (forest|grassland)s?\b', str(p.get('n') or ''), re.I):
            p['owned_only'] = 'Forest Service-owned land only (Basic Ownership map: OWNERCLASSIFICATION = USDA FOREST SERVICE)'


def run(st):
    try: P = json.load(open(f'data/parkinfo/US-{st}.json'))['parks']; P_ALL.clear(); P_ALL.update(P)
    except Exception: notice(f'US key {st}', 'no park file, skipped'); return None  # noqa: BLE001
    try: P = {k: v for k, v in P.items() if k not in set(json.load(open('data/retired-refs.json')).get('refs') or {})}   # Oct 29: retired numbers leave the key (issue #17)
    except Exception: pass  # noqa: BLE001
    got = load_cache(st) if CMODE in ('use', 'only') else None
    if got is None and REFILL_ONLY:
        notice(f'US key {st}', 'refill: no saved copy to refill; skipped'); return None
    if got is None and CMODE == 'only':
        notice(f'US key {st}', 'no saved shapes yet; skipped (saved-copy-only run)'); return None
    if got is not None:
        recs, seen, used_detail = got; CACHE_USED.append(st)
        if CMODE == 'use' and not MASTER_OWNS:   # Nov 9 primary fix: a saved copy made before it has no filtered saved ids; ask for them by id
            try:
                _sv = saved_fetch(st, P, recs)
                if _sv: recs += _sv; (save_cache(st, recs, seen) if st not in FAILED_READ else None)
            except Exception as _e: notice(f'US key {st}', f'saved ids not read by id ({type(_e).__name__}: {str(_e)[:120]})')  # noqa: BLE001
        # Oct 25: a saved copy made before a layer was added (data/state-gis.json grows) never had that layer's land, so the
        # nightly rebuild could not join it. Top the copy up: read live only the layers it has no records from, add, re-save.
        if CMODE == 'use' and not MASTER_OWNS:   # Nov 10: with KPC_MASTER_OWNS=1 the master step topped the copy up before the gate
            present = {re.match(r'[a-z]*', str(a.get('OBJECTID'))).group(0) for a in recs}
            missing = {x[0] for x in XS if (len(x) <= 7 or x[7] is None or st in x[7]) and x[0] not in present}
            # Nov 10: a layer already in the saved copy can still be short (one silent server page, e.g. sgflf 199 vs ~17,000).
            # Top-up used to skip any prefix that had at least one record, so the short copy was kept forever.
            short = set()
            for x in XS:
                pre, url = x[0], x[1]
                if pre not in present or pre in missing:
                    continue
                if len(x) > 7 and x[7] is not None and st not in x[7]:
                    continue
                if saved_only(url):
                    continue
                opt = x[8] if len(x) > 8 else {}
                n_have = sum(1 for a in recs if str(a.get('OBJECTID') or '').startswith(pre) and str(a.get('OBJECTID'))[len(pre):].isdigit())
                n_live = layer_live_count(st, pre, url, x[2], x[3], opt)
                if n_live and n_have < 0.97 * n_live:
                    short.add(pre)
                    notice(f'US key {st}', f'saved copy of {pre} is short ({n_have} areas, live layer {n_live}); re-reading that layer')
            if LAYER_OUT is not None:   # Nov 10: the master step's reader: layer files only, the master merges after its checks
                _here = {x[0] for x in XS if len(x) <= 7 or x[7] is None or st in x[7]}
                force = (_here if REFILL_FORCE == ['all'] else set(REFILL_FORCE) & _here)
                lfp = {p.name[len(f'US-{st}.'):-len('.geojson.gz')] for p in LAYER_IN.glob(f'US-{st}.*.geojson.gz')} & _here if LAYER_IN else set()
                want = missing | short | force | lfp
                if want:
                    RAWF.clear()
                    _pf = lambda a: re.match(r'[a-z]*', str(a.get('OBJECTID'))).group(0)
                    base = [a for a in recs if _pf(a) not in want]
                    add = extra_state(st, _have(base), only=want)
                    _write_layer_files(st, want, add)
                missing = short = set()
            if missing or short:
                _pf = lambda a: re.match(r'[a-z]*', str(a.get('OBJECTID'))).group(0)
                kept_old = {}
                if short:
                    kept_old = {pre: [a for a in recs if _pf(a) == pre] for pre in short}
                    recs = [a for a in recs if _pf(a) not in short]
                add = extra_state(st, _have(recs), only=missing | short)
                # Nov 10 (run 42821613637): a re-read that came back SMALLER than the saved copy (mol 16 of 1,000, ind 0 of 457,
                # wid 0 of 1,389) replaced it and the smaller copy was saved. A re-read now replaces a saved layer only when it has
                # at least as many records; otherwise the saved records are kept.
                back = []
                for pre, old_l in sorted(kept_old.items()):
                    n_new = sum(1 for a in add if _pf(a) == pre)
                    if n_new < len(old_l):
                        add = [a for a in add if _pf(a) != pre]; recs += old_l; back.append(f'{pre} {n_new} < {len(old_l)}')
                if back: notice(f'US key {st}', 'a re-read came back smaller than the saved copy, so the saved records were kept: ' + ', '.join(back))
                if add:
                    recs += add
                    notice(f'US key {st}', f'saved copy topped up with {len(add)} areas from {len({str(a["OBJECTID"]).rstrip("0123456789") for a in add})} layer(s)')
                    if st not in FAILED_READ: save_cache(st, recs, seen)
        if REFILL_ONLY:
            notice(f'US key {st}', f'refill: saved copy now {len(recs)} records' + (' (a read failed: not re-saved)' if st in FAILED_READ else ''))
            return None
    else:
        recs, seen = pad_state(st, P)
        recs += fws_state(st, {norm(a.get('Unit_Nm') or '') for a in recs if a.get('Mang_Name') == 'FWS'})
        # Nov 9 (Brandon 11:26 AM CST): the state layer comes BEFORE the PAD-US name exception, so a record kept only by name
        # must not hide the state layer's own record of that name (extra_state leaves out names PAD-US already has)
        recs += extra_state(st, _have([a for a in recs if not a.get('KPC_NameKeep')]))
        used_detail = DETAIL
        if SAVED_ONLY_SKIPPED.get(st):   # Brandon t939u: the layers on saved-copy-only hosts come from the saved copy, never a live read
            _old = load_cache(st)
            _pf = SAVED_ONLY_SKIPPED[st]
            _keep = [a for a in (_old[0] if _old else []) if re.match(r'[a-z]*', str(a.get('OBJECTID'))).group(0) in _pf]
            recs += _keep
            notice(f'US key {st}', f"saved copy used for {len(_pf)} layer(s) on saved-copy-only hosts ({' '.join(sorted(_pf))}): {len(_keep)} areas" + ('' if _old else '; NO saved copy, so those layers are missing this run'))
        old = load_cache(st) if st in FAILED_READ else None
        # only when this read actually came back SHORT (a source that fails every time is already missing from the
        # saved copy too, and must not freeze the state on an old copy forever)
        if old is not None and len(recs) < .97 * len(old[0]):
            notice(f'US key {st}', f'a map did not answer ({len(recs)} areas read, {len(old[0])} saved), so the saved copy was used (nothing dropped)')
            recs, seen, used_detail = old; CACHE_USED.append(st)
        elif CMODE in ('use', 'refresh') and not (st in FAILED_READ and old is None and cache_file(st).exists()): save_cache(st, recs, seen)
    recs = prefer_state_layer(st, recs, P)
    if _kr('KPC_PADUS_DEDUPE'):
        # Nov 2 (mapping agent): PAD-US keeps the older copy of a place from the same provider (FWS_PADUS3_0 + FWS_PADUS4_0 for
        # every refuge); both joined, the park's 'official acres' came out doubled (230 'OFF smaller' map-audit rows) and the two
        # near-identical outlines drew slivers. The older copy is left out; an id a person joined by hand is always kept.
        _old = KR.padus_old_copies(recs, _hand_ids(recs, P), _share_inside)
        if _old:
            recs = [a for a in recs if _oid(a) not in _old]
            notice(f'US key {st}', f'{len(_old)} older PAD-US copies of the same place from the same provider left out (KPC_PADUS_DEDUPE)')
        elif not any(a.get('Agg_Src') for a in recs if isinstance(a.get('OBJECTID'), int)):
            notice(f'US key {st}', 'KPC_PADUS_DEDUPE is on but the saved copy has no Agg_Src: run GEO_CACHE_MODE=refresh once')
    parks, used = {}, set()
    RD.clear()
    clusters = name_clusters(recs)
    for ref, r in sorted(P.items()):
        name, typ, la, lo = r[0], r[2] if len(r) > 2 else '', r[5] if len(r) > 5 else None, r[6] if len(r) > 6 else None
        if la is None and ref in pins(): la, lo = pins()[ref]
        kp = kinds(name) | kinds(typ)
        m, c, farm = [], [], []
        for a in recs:
            nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
            close = la is None or near(la, lo, a['_bb'], .6)
            if not close:
                # Oct 31 (Fable review #2, rule G-1 'a record that NAMES the park joins at any distance'): the 0.6 deg box no longer hides
                # the agency's own record of the SAME full name (Ouachita NF's Oklahoma half, Gulf Islands NS in Mississippi) when that
                # name is unique in the state's records (a namesake elsewhere, like a second Beaver Creek WMA, is never joined this way)
                # Nov 1 (chat 11 KEY NO: Pine Island SP -> 'Pine Island', Long Lake SRA -> 'Long Lake State Habitat Area', Smith River RMA ->
                # the 329,827 ac NRA): norm() drops the kind words, so these were NOT the same full name. Now: the FULL name (kind words
                # kept) must be the same, the kinds must agree, and it only ADDS a far piece to a park already joined at its pin
                # (Ouachita NF's other-state half); with no join at the pin it goes to the check list, never an outline.
                if la is not None and len(norm(name)) > 8 and norm(nm) == norm(name) and clusters.get(a.get('_nn'), 1) == 1 and not a.get('Water') and not KM.is_admin(nm):
                    _full = _nf(nm) == _nf(name) and not (_tags(name) and _tags(nm) and not (_tags(name) & _tags(nm)))
                    farm.append(([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), 'same full name, far from the pin (G-1: the record names the park)'], _full))
                continue
            if bool(kp) != bool(a['_k']) and la is not None and not near(la, lo, a['_bb'], .1): close = False   # one name has no kind word: must be close by
            if not close: continue
            if a.get('Water') and (la is None or not near(la, lo, a['_bb'], .02)): continue   # Oct 25: lake names repeat (Washington has dozens of Lost Lakes): a lake surface joins only right at the pin
            how = join_how(name, kp, a, near(la, lo, a['_bb'], .1) if la is not None else False)
            if how and PUBACC != 'off':   # Nov 6: the 2-fer program's public-access rule (kpc_fers.pad_use), here behind a switch
                _cl = closed_why(a)
                if _cl:
                    PUBACC_HIT.append({'st': st, 'park': ref, 'rid': a['OBJECTID'], 'name': nm, 'why': _cl, 'acres': round(a.get('GIS_Acres') or 0)})   # noted only; the join below is unchanged
            if how and a.get('Water'): how += ' · water outline only'
            if how:
                m.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), how])
            elif piece_why(name, a) and join_how(name, kp, a, near(la, lo, a['_bb'], .1) if la is not None else False, rules=False):
                c.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), piece_why(name, a)])   # Nov 2: a person looks, never an outline
        if re.search(r'wild and scenic|scenic river', name, re.I):   # Nov 2 (chat 11 KEY NO: Fortymile WSR -> SRMA / ACEC): a wild and scenic river is never the
            # management area, monument or office land around it (Delta WSR -> Delta River SRMA, Upper Missouri WSR -> the Breaks monument)
            m = [x for x in m if not re.search(r'ACEC|SRMA|\bRMA\b|recreation management|national monument|conservation area|field office|district', str(x[1]), re.I)]
        if farm:   # Nov 1: far same-name pieces (see above): extra pieces of a park joined at its pin, else only to check
            _pinned = any(la is not None and near(la, lo, a['_bb'], .1) for a in recs if any(str(a['OBJECTID']) == str(x[0]) for x in m))
            for x, _full in farm:
                if _full and _pinned: m.append(x)
                else: c.append(x[:3] + ['same name far from the pin, no join at the pin (Nov 1: check, never an outline)'])
        ov = OVR.get(ref) or {}
        if ov:
            no = {str(x) for x in ov.get('no', [])}
            m = [x for x in m if str(x[0]) not in no and _nf(x[1]) not in {_nf(y) for y in no}]
            if _kr('KPC_NO_BY_NAME'): m = KR.drop_no(m, ov)   # Nov 2: a NO survives a PAD-US renumbering (name + acres saved with it)
            for want in ov.get('join', []):
                _want0 = str(want)
                # Oct 27 (boundary review #3): PAD-US gives its records NEW ids in each version. A hand join by id whose id is gone
                # is found again by its fingerprint (name + acres within 10%, near the pin), saved with it in overrides.json 'fp'
                if not any(_oid(a) == str(want) for a in recs) and str(want) in (ov.get('fp') or {}):
                    fn, fa = ov['fp'][str(want)][:2]
                    # Nov 3 step 3 (Quality drops-27: Elkhorn SP's 'sgmta6613' fp ['Elkhorn', 0] was re-found as BLM's 'wsa205' Elkhorn
                    # WSA, 4.3 km off, and tagged 'reviewed'): the re-found record must come from the SAME layer (id family: PAD-US
                    # numbers, 'sgmta', 'wsa' ...). An id reset happens inside one layer, never across layers.
                    _fam = re.match(r'\D*', _want0).group()
                    want = next((_oid(a) for a in recs if _nf(a.get('Unit_Nm') or a.get('Loc_Nm') or '') == _nf(fn) and (la is None or near(la, lo, a['_bb'], .6))
                                 and re.match(r'\D*', _oid(a)).group() == _fam
                                 and abs((a.get('GIS_Acres') or 0) - (fa or 0)) <= max(20, .1 * (fa or 0))), want)
                for a in recs:
                    nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
                    if (_oid(a) == str(want) or _nf(nm) == _nf(want)) and _oid(a) not in no and (la is None or near(la, lo, a['_bb'], .6)):   # Oct 25: an id in 'no' is never re-added by a same-name join
                        if _no_all(ov, a): continue   # Nov 2: a NO by name wins over a join by id
                        if _kr('KPC_ID_JOIN_NAME') and _oid(a) == str(want) and _nf(nm) != _nf(want):
                            _ok, _why = KR.id_join_name_ok(name, nm, ((ov.get('fp') or {}).get(_want0) or [None])[0])
                            if not _ok:   # Nov 2: the approved id now points at other land: check, never an outline
                                if not any(str(x[0]) == _oid(a) for x in c): c.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), _why])
                                continue
                        _how = 'reviewed-approx' if ov.get('approx') else 'reviewed'
                        _was = next((x for x in m if str(x[0]) == _oid(a)), None)
                        # Oct 29 8:25 PM (release check): a piece the name test had ALREADY joined kept its plain 'name'/'words'
                        # tag, so Rule G (G-1 / R-G8) still held it although a person said YES. A hand join now marks it reviewed.
                        if _was is not None: _was[3] = _how
                        else: m.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), _how])   # Oct 22: 'approx' = a person picked the closest official land, but it is bigger or shaped differently: the tools label it Approximate
        _sct, _sfirst = [], False   # Nov 3 answer sheet (read only; nothing here runs unless KPC_ANSWER_SHEET is add / first)
        if SHEET and SHEET.get(ref) and not ov.get('none'):
            _sno = {str(x) for x in ov.get('no', [])}
            _sby = {_oid(a): a for a in recs}
            _stag = 'reviewed-sheet' if SHEET_GREEN else 'answer sheet (nightly check not green)'
            _spre = {re.match(r'\D*', k).group() for k in _sby}   # the record-id families (PAD-US numbers, 'sgvta'...) this run read
            for _s in SHEET[ref]:
                if _s['id'] in _sno: continue                                  # 1. overrides 'no' always wins
                fn, fa = _s['fp']
                a = _sby.get(_s['id'])
                if a is None and _s['st'] == 'OK' and re.match(r'\D*', _s['id']).group() not in _spre: continue   # a layer this builder does not read: not its question
                if a is None and fn and fa is not None:   # id reset: the SAME fingerprint as overrides.json 'fp' (name + acres within 10%, near the pin)
                    _h = [b for b in recs if _nf(b.get('Unit_Nm') or b.get('Loc_Nm') or '') == _nf(fn) and (la is None or near(la, lo, b['_bb'], .6))
                          and re.match(r'\D*', _oid(b)).group() == re.match(r'\D*', _s['id']).group()   # same layer only (Elkhorn / wsa205; was in step 3)
                          and abs(float(b.get('GIS_Acres') or 0) - fa) <= max(20, .1 * fa)]
                    a = _h[0] if len(_h) == 1 else None
                if a is not None and _sheet_no(ov, a): continue                # 1. a NO by id or name beats the sheet (R4)
                nm = (a.get('Unit_Nm') or a.get('Loc_Nm') or '') if a is not None else ''
                if (_s['st'] != 'OK' or a is None or not fn or _nf(nm) != _nf(fn)
                        or (la is not None and not near(la, lo, a['_bb'], .6))):
                    _sct.append([_s['id'], fn or nm, fa, 'NOT SURE (answer sheet): the record is marked NOT SURE / PIN / FIXED, or it is gone, renamed or moved; a person answers YES or NO in an inbox batch, no guess']); continue
                _was = next((x for x in m if str(x[0]) == _oid(a)), None)
                if _was is not None:
                    if not str(_was[3]).startswith('reviewed'): _was[3] = _stag   # 2. an overrides join keeps its own tag
                else: m.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), _stag])
            _sfirst = SHEET_MODE == 'first' and any(str(x[3]) == _stag for x in m)
        # Oct 29 (chat 8's name-mismatch list, Brandon 'help the boundaries'): 'alias' = another name the official layer uses for this
        # park. An alias joins ONLY with the sure-match test: same name as the alias AND the POTA pin inside that record's outline
        # 'alias_all' = a name PREFIX for a park the layer splits into units (Whitewater WMA: Main Branch Unit, …): when one of
        # them holds the pin or lies within ~3 km of it, every unit with that prefix within ~30 km joins (chat 2 + chat 8, Oct 29)
        if not m and la is not None and ov.get('alias_all') and (ov.get('alias_ok') or any(_nf(x) in {_nf(y) for y in ov.get('alias_ok_names', [])} for x in ov['alias_all'])):
            for pre in ov['alias_all']:
                units = [a for a in recs if _nf(a.get('Unit_Nm') or a.get('Loc_Nm') or '').startswith(_nf(pre)) and near(la, lo, a['_bb'], .3)]
                if any(inside(la, lo, a['_g']) or near(la, lo, a['_bb'], .03) for a in units):
                    for a in units:
                        if _no_all(ov, a): continue   # Nov 2: alias_all had no NO check at all
                        m.append([a['OBJECTID'], a.get('Unit_Nm') or a.get('Loc_Nm') or '', round(a.get('GIS_Acres') or 0), f'alias units: {pre}'])
        if not m and la is not None and RIDB.get(st):   # the Recreation.gov point proves WHERE the site is (see RIDB above)
            for x in RIDB[st]:
                if not (same_name(name, x['n']) or norm(name) == norm(x['n'])) or _km(la, lo, x['la'], x['lo']) > 25: continue
                for a in recs:
                    nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
                    if not (same_name(name, nm) or same_name(x['n'], nm) or (a.get('Loc_Nm') and same_name(name, a['Loc_Nm']))): continue
                    if KM.is_admin(nm) or KM.is_admin(a.get('Loc_Nm')) or re.search(r'field office|district office|ranger district', nm, re.I): continue   # Nov 1 (chat 11: Fortymile WSR -> 'Eastern Interior Field Office'): an office boundary is never a park
                    if _tags(name) and not (_tags(name) & _tags(nm)): continue   # Oct 31 (chat 11: Milford State Fish Hatchery -> 'Milford Wildlife Area'): another kind of place never joins
                    if piece_why(name, a):   # batch 1b (Quality): rule 18 here too; same_name() says yes for Yeager, Abo, Quarai, Rio Bonito
                        if not any(str(q[0]) == _oid(a) for q in c): c.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), piece_why(name, a) + ' (Recreation.gov path)'])
                        continue
                    if _oid(a) in {str(q) for q in ov.get('no', [])} or _no_all(ov, a) or not near(x['la'], x['lo'], a['_bb'], 0) or not inside_slack(x['la'], x['lo'], a['_g']): continue
                    if any(q[0] == a['OBJECTID'] for q in m): continue
                    m.append([a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), f"name + Recreation.gov point inside (G-1, id {x.get('id')})"])
        # Nov 1 (chat 11 KEY NO 2:32 PM: Oxford Slough, Iao Valley, Teanaway joined through name variants nobody approved): a name
        # variant ('alias') joins ONLY when chat 11 said YES to it (kpc_key_answers marks it, or 'alias_ok'); the rest wait as questions
        # Nov 2 (chat 11 KEY NO again: Capitol SP -> 'Capital Park', Rail Trail, Owens Spring): the old 'why' text test let through
        # aliases whose park had ANY chat 11 YES. Now a name variant joins only when chat 11 said YES to THAT name (alias_ok_names,
        # written by kpc_key_answers on an alias YES) or a person set alias_ok for the park.
        _okn = {_nf(x) for x in ov.get('alias_ok_names', [])}
        _alias_ok = [al for al in ov.get('alias', []) if ov.get('alias_ok') or _nf(al) in _okn]
        if not m and la is not None and _alias_ok:
            for al in _alias_ok:
                for a in recs:
                    nm = a.get('Unit_Nm') or a.get('Loc_Nm') or ''
                    if _nf(nm) == _nf(al) and _oid(a) not in {str(x) for x in ov.get('no', [])} and not _no_all(ov, a) and near(la, lo, a['_bb'], .05) and inside_slack(la, lo, a['_g']):
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
                # Nov 3 step 3 (Quality spot-check, NV −26): a record a person answered NO to was listed as 'same name, different
                # kind of place', which read like a kind-check refusal (16 NV herd areas: the real cause was chat 11's map-audit NO,
                # pattern OUTSIDE/FAR, applied Nov 2 in 6662f2d). It is now listed with the true reason, so nobody 'fixes' the kind rule.
                if str(_oid(a)) in {str(y) for y in ov.get('no', [])} or (_kr('KPC_NO_ALL_PATHS') and KR.is_no(ov, a['OBJECTID'], nm, a.get('GIS_Acres'))):
                    why = 'a person said NO to this record (overrides.json no' + (': ' + str(ov.get('why'))[:80] if ov.get('why') else '') + ')'
                elif same_name(name, nm): why = 'same name, different kind of place'
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
                sn = [x for x in c if x[3] == 'same name, different kind of place' and str(x[0]) not in {str(y) for y in ov.get('no', [])}
                      and not (_kr('KPC_NO_ALL_PATHS') and KR.is_no(ov, x[0], x[1], x[2]))]   # Oct 25: a person's 'no' wins here too
                if sn and len({_nf(x[1]) for x in sn}) == 1:
                    gs = {_oid(a): a for a in recs}
                    hold = [x for x in sn if str(x[0]) in gs and rings(gs[str(x[0])].get('_g'))
                            and (inside(la, lo, gs[str(x[0])]['_g']) or near(la, lo, gs[str(x[0])]['_bb'], .005))]
                    # batch 1b (switch KPC_PIECE_NAME): the same piece check as the other name paths. Before, this path joined the
                    # WHOLE area to a park named for one piece of it (US-13221 Gordon W. Yeager-S.E. Unit got the whole WMA; US-11866
                    # Rio Bonito Salazar Tract got Tract 1). A refused record stays on the check list with the reason.
                    _pw = {str(x[0]): piece_why(name, gs[str(x[0])]) for x in hold}
                    if any(_pw.values()):
                        c = [([y[0], y[1], y[2], _pw[str(y[0])] + ' (same name + pin inside path)'] if _pw.get(str(y[0])) else y) for y in c]
                        hold = [x for x in hold if not _pw[str(x[0])]]
                    if hold and not any(_tags(name) and _tags(x[1]) and not (_tags(name) & _tags(x[1])) for x in hold):   # a memorial is never the refuge
                        m = [[x[0], x[1], x[2], 'same name (POTA writes the kind into the name) + pin inside'] for x in hold]
                        c = [x for x in c if x not in hold]; site = []
        if _sct or _sfirst:   # Nov 3 answer sheet: 4. the builder's own guesses never stand in for a sheet row
            _keep = lambda x: str(x[3]).startswith(('reviewed', 'answer sheet'))
            _why = "held: the park's answer-sheet record is NOT SURE" if _sct else 'not on the answer sheet (KPC_ANSWER_SHEET=first): check'
            _sids = {str(y[0]) for y in _sct}
            c = [x for x in c if str(x[0]) not in _sids] + [x[:3] + [_why] for x in m if not _keep(x) and str(x[0]) not in _sids]
            m = [x for x in m if _keep(x)]
            if _sct: c = _sct + c; site = []
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
    # batch 1b, RULE 18 TRACT EXCEPTION (Brandon Nov 2 8:38 PM CST, via Super Head Bot): one official record that is really
    # separate TRACTS, each tract its own POTA park (Salinas Pueblo Missions NM = Abo + Quarai + Gran Quivira in NPS and PAD-US
    # 4.1 Fee): each park gets ONLY its own tract, a person reviewed it (kpc_key_rules.TRACT_SPLITS or an overrides 'tract'
    # entry), and the pin must be inside its tract (30 m on the true line, plus the rough copy's slack). The record is found
    # again by its NAME near the pin every run (PAD-US ids change between versions). If any test fails the park is left as it
    # was and a notice says why; this never joins a record a person did not name. A person's 'no' on the WHOLE record (for
    # example the Nov 2 hand-join drops put 'Salinas Pueblo Missions National Monument' in US-0961's 'no') does not stop the
    # reviewed TRACT: the 'no' is about the whole monument, and the whole is never joined here. To stop a tract, take the park
    # out of TRACT_SPLITS (code review) or remove its overrides 'tract' entry.
    ntr, trw = 0, []
    for ref in sorted(parks):
        t = KR.tract_entry(ref, OVR.get(ref)) if KR is not None and hasattr(KR, 'tract_entry') else None
        if not t or ref not in pinx: continue
        la_, lo_ = pinx[ref]
        rec = next((a for a in recs if _nf(a.get('Unit_Nm') or a.get('Loc_Nm') or '') == _nf(t['record']) and a.get('_bb') and near(la_, lo_, a['_bb'], .6)), None)
        if rec is None: trw.append(f"{ref}: no record named '{t['record']}' near the pin"); continue
        rid = _oid(rec); rr = [r for r in rings(rec.get('_g')) if len(r) > 2]
        bx = [[min(q[0] for q in r), min(q[1] for q in r), max(q[0] for q in r), max(q[1] for q in r)] for r in rr]
        groups = KR.tracts_of(bx)
        if len(groups) < 2: trw.append(f'{ref}: record {rid} is one tract, nothing to split'); continue
        mine = [gp for gp in groups if any(in_ring(lo_, la_, rr[i]) for i in gp) or near_ring(la_, lo_, {'rings': [rr[i] for i in gp]}, 0.03 + DETAIL * 111.0)]
        if len(mine) != 1: trw.append(f'{ref}: the pin is in {len(mine)} tracts of record {rid}, not exactly one'); continue
        gp = mine[0]
        k_ = math.cos(math.radians(la_)) * 111320.0
        def _sq(r): return 0.5 * sum((x1 - lo_) * k_ * (y2 - la_) * 110570.0 - (x2 - lo_) * k_ * (y1 - la_) * 110570.0 for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]))
        acres = round(abs(sum(_sq(rr[i]) for i in gp)) / 4046.86)
        pk = parks[ref]
        pk['m'] = [x for x in (pk.get('m') or []) if str(x[0]) != rid] + [[rec['OBJECTID'], KR.tract_label(t), acres,
                   f"reviewed (official tract: {t['tract']} of {t['record']}; rule 18 tract exception, {t.get('approved_by')} {t.get('approved')})"]]
        pk['c'] = [x for x in (pk.get('c') or []) if str(x[0]) != rid]
        pk.setdefault('parts', {})[rid] = [[round(c, 4) for c in bx[i]] for i in gp]
        pk['tract'] = {'record': t['record'], 'tract': t['tract'], 'label': KR.tract_label(t), 'of': t.get('of'), 'pieces': len(gp), 'acres': acres,
                       'approved_by': t.get('approved_by'), 'approved': t.get('approved'), 'build': t.get('build'), 'source': t.get('source')}
        if len(groups) != (t.get('of') or len(groups)): trw.append(f"{ref}: record {rid} has {len(groups)} tracts, the person-reviewed entry says {t.get('of')}")
        ntr += 1
    if ntr or trw: notice(f'US key {st}', f'{ntr} park(s) given only their own official tract (rule 18 tract exception)' + (f"; not split: {'; '.join(trw[:6])}" if trw else ''))
    # Oct 29 10:40 AM: the 'agency layer has nothing there' cut (plan 2.7) was TAKEN OUT the same morning: it cut REAL tracts of
    # spread-out parks (Florida Keys WA 20 of 235 pieces, Tanana Valley SF 63 of 92, US-0150 242 of 249) because a state layer
    # can be partial. Brandon: 'if it is a tract that belongs to the park NEVER delete it'. Far pieces are now only HELD + checked
    # in the 2-fer line (kpc_fers_far_hold.py / kpc_fers_far_check.py), never cut from an outline by distance.
    # Oct 29 (HQ 10:40 AM, Brandon 10:39 AM GO: 'wetland districts = owned tracts only'): a Wetland Management District (and any
    # scattered-tract FWS park the same way) = ALL the tracts the Fish and Wildlife Service OWNS in fee in that district, from its
    # own realty layer (INTTYPE1 = 'F'), one multi-part outline; EASEMENT tracts (private farmland) are never part of it
    wmd = [ref for ref, p in parks.items() if re.search(r'wetland management district', p.get('n') or '', re.I) and not p.get('m')]
    nwmd = wmd_no = 0
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
            # Nov 3 (rules sort §9 conflict 2; proposed rule 21): a person's 'no' holds on this path too (id, exact name, or with
            # KPC_NO_BY_NAME the saved name + acres). Before, a tract in the district's 'no' came back here on every build.
            if KR.is_no(OVR.get(ref) or {}, rec['OBJECTID'], rec['Unit_Nm'], rec['GIS_Acres']): wmd_no += 1; continue
            recs.append(rec)
            m.append([rec['OBJECTID'], rec['Unit_Nm'], round(rec['GIS_Acres'] or 0), 'reviewed: the district = FWS fee (owned) tracts only, easements left out (Brandon Oct 29)'])
        if not m: continue
        parks[ref]['m'] = sorted(m, key=lambda x: -x[2]); parks[ref].pop('c', None); nwmd += 1
    if wmd: notice(f'US key {st}', f'{nwmd} of {len(wmd)} wetland districts joined to their FWS-owned (fee) tracts' + (f'; {wmd_no} tract(s) left out by a person\'s no' if wmd_no else ''))
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
        # Nov 2 (chat 11 read 'Monroe Lake' and took Indiana's SRA pieces for the whole reservoir): a piece matched on its SECOND name
        # (Indiana's subunit, Ohio's ALT_NAME) shows that name first: 'Allens Creek State Recreation Area (Monroe Lake)'
        for _x in m:
            _a = gs_.get(str(_x[0])) or {}
            _l2 = str(_a.get('Loc_Nm') or '').strip()
            if _l2 and _l2 != _x[1] and _pw and len(_pw & words(_l2)) > len(_pw & words(_x[1])): _x[1] = f'{_l2} ({_x[1]})'
        weak = [x for x in m if str(x[3]).split(' · ')[0] in WEAK and not (_pw and _pw == words(x[1]))]   # R-G8 fix: 'Kodiak' is in 'Kodiak Office' but that record does not NAME the park
        # Nov 2 (map audit, Tennessee: the bare 'Reelfoot' / 'Chickasaw' / 'Pickett' records were drawn into the state park, the WMA AND the
        # refuge at once): when the park already has its own full-name record, a bare-name piece matched with the designation code
        # ignored is NOT added on top (it is often a neighbouring unit); it goes to CHECK
        if weak and any(x not in weak and str(x[3]).split(' · ')[0] not in WEAK for x in m):
            _bare = [x for x in weak if str(x[3]).split(' · ')[0] == 'name (designation code ignored)']
            if _bare:
                p['m'] = m = [x for x in m if x not in _bare]; weak = [x for x in weak if x not in _bare]
                p['c'] = (p.get('c') or []) + [[x[0], x[1], x[2], 'held: a bare-name piece beside the park\'s own full-name record (Nov 2 map audit)'] for x in _bare]
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
        # Oct 30 (chat 2, from the 2-fer recheck: Coronado National Memorial -> the whole Coronado National Forest, Jemez Historic Site ->
        # the whole Jemez NRA): a SMALL site (memorial, historic site, monument, battlefield, museum, lighthouse) never takes a big piece
        # of ANOTHER kind of land (forest, refuge, recreation area, wilderness, grassland, lake) of 5,000+ acres by itself: a person looks
        _sm = re.compile(r'memorial|historic(al)? site|historic park|monument|battlefield|museum|lighthouse|historic district|national historical', re.I)
        _bg = re.compile(r'national forest|wildlife refuge|\bnwr\b|recreation area|wilderness|grassland|state forest|\bblm\b|national park\b|\blake\b', re.I)
        if _sm.search(f"{p.get('n') or ''} {p.get('t') or ''}"):
            _big = [x for x in m if (x[2] or 0) > 5000 and _bg.search(str(x[1])) and not _sm.search(str(x[1]))]
            if _big:
                m = [x for x in m if x not in _big]; p['m'] = sorted(m, key=lambda x: -x[2]); weak = [x for x in weak if x not in _big]
                p['c'] = (p.get('c') or []) + [[x[0], x[1], x[2], 'check: a small site joined to a big piece of another kind of land'] for x in _big]
        # Oct 30 (chat 10 / Brandon's phone, Kings Gap US-4361: TWO dashed edges 20-30 m apart): two joined records that are the SAME
        # land from two layers (sizes within 5%, boxes overlapping 80%+) are drawn once: the state agency's own record is drawn over PAD-US,
        # else the first; the other's id goes in 'twin' = 'do not draw' for the tools (chat 3)
        if len(m) > 1:
            def _ov(b1, b2):
                if not b1 or not b2: return 0
                w = max(0, min(b1[2], b2[2]) - max(b1[0], b2[0])); h = max(0, min(b1[3], b2[3]) - max(b1[1], b2[1]))
                s = min((b1[2] - b1[0]) * (b1[3] - b1[1]), (b2[2] - b2[0]) * (b2[3] - b2[1])) or 1e-12
                return w * h / s
            _drop = []
            for i_, x in enumerate(m):
                for y in m[i_ + 1:]:
                    if x in _drop or y in _drop: continue
                    ax, ay = x[2] or 0, y[2] or 0
                    if not ax or not ay or abs(ax - ay) > .05 * max(ax, ay): continue
                    ra, rb = gs_.get(str(x[0])) or {}, gs_.get(str(y[0])) or {}
                    if _ov(ra.get('_bb'), rb.get('_bb')) < .8: continue
                    _drop.append(x if (isinstance(x[0], int) and not isinstance(y[0], int)) else y)
            if _drop:   # kept in 'm' (the 2-fer line and the ownership tests still see every record); the MAP skips drawing these
                p['twin'] = [str(x[0]) for x in _drop]
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
        if m and all('water outline only' in str(x[3]) for x in m): p['g'] = 'approximate'   # Oct 31 (Fable #25): a lake surface is not the park's land line
        if not m and ref in TRL and ref not in DRIVING_ONLY and pathlib.Path(f'data/trails/{ref}.json').exists():
            p['m'] = [[f"trl{ref.split('-')[1]}", TRL[ref].get('name') or p.get('n'), 0, f"official trail line ({TRL[ref].get('by')}): the park is the line + POTA's 100-ft band"]]
            p['g'] = 'official'; p['line'] = 1
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
        if parks[ref].get('tract'):   # batch 1b: the POTA name stays as POTA lists it; the note says what the outline is
            _tn = KR.tract_note(parks[ref]['tract'])
            parks[ref]['note'] = (parks[ref]['note'] + ' ' + _tn) if parks[ref].get('note') else _tn
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
            if _kr('KPC_NO_ALL_PATHS'): om = KR.drop_no(om, OVR.get(ref) or {})   # Nov 2: a NO by name also wins over the kept outline
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
                    _pr = P.get(ref) or []; _pla, _plo = (_pr[5], _pr[6]) if len(_pr) > 6 else (None, None)
                    if _pla is None and ref in pins(): _pla, _plo = pins()[ref]
                    hit = next((a for a in recs if isinstance(a.get('OBJECTID'), int) and _nf(a.get('Unit_Nm') or a.get('Loc_Nm') or '') == _nf(x[1])
                                and abs((a.get('GIS_Acres') or 0) - (x[2] or 0)) <= max(20, .1 * (x[2] or 0))
                                and not _no_all(OVR.get(ref) or {}, a)   # Nov 2: a NO'd record is never 'found again'
                                and not (_kr('KPC_REFOUND_NEAR') and _pla is not None and not near(_pla, _plo, a['_bb'], .6))), None)
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
    # Nov 9 evening (Brandon t915u, 4:40 PM CST: 'a park with a saved record ID keeps it regardless of rules changes'; KZ4CP 5:12 PM):
    # a park whose last published result is joined to record ids that are all still in this read keeps that result, whatever these
    # rules would match now. A fresh match only when: a person's override names the park (hand decisions are applied as they are), one
    # of its ids is on the bad-ID block list, a record is gone (the keep-last-good guard above handles that), or a declared rule
    # change asks to re-match saved ids (KPC_KEY_REMATCH_IDS=1, from .github/us-key-rule-scope.json 'saved_ids': true).
    if os.environ.get('KPC_KEY_REMATCH_IDS') != '1':
        try:
            old = json.load(open(OUT / f'US-{st}.json')).get('parks', {})
            ids_here = {_oid(a) for a in recs}; carried = 0
            for ref, op in old.items():
                np_ = parks.get(ref)
                if not np_ or not op.get('m') or ref in OVR: continue
                oids = sorted(str(x[0]) for x in op['m'])
                if not all(i in ids_here for i in oids) or set(oids) & BLOCKED.get(ref, set()): continue
                if sorted(str(x[0]) for x in np_.get('m') or []) == oids: continue
                keep = dict(op)
                for k in ('n', 't'):
                    if k in np_: keep[k] = np_[k]   # POTA's current name / type
                keep['kept_ids'] = 'saved record ids kept through a rules change (Brandon t915u)'
                parks[ref] = keep; carried += 1
            if carried: notice(f'US key {st}', f'{carried} park(s) kept their saved record ids (rules changes do not move a park with saved ids; Brandon t915u)')
        except FileNotFoundError: pass
        except Exception as e: notice(f'US key {st}', f'saved-id keep skipped: {e}')  # noqa: BLE001
    # Nov 9 evening (KZ4CP 5:41 PM CST): a park-scoped rule change re-reads this state only for the parks it names; every other park
    # here keeps its last published result (a person's override still applies as it is).
    _only = set((os.environ.get('KPC_KEY_ONLY_PARKS') or '').split())
    if _only and st in (os.environ.get('KPC_KEY_ONLY_STATES') or '').split():
        try:
            _old = json.load(open(OUT / f'US-{st}.json')).get('parks', {}); _kept = 0
            for ref, op in _old.items():
                if ref in parks and ref not in _only and ref not in OVR: parks[ref] = op; _kept += 1
            notice(f'US key {st}', f"park-scoped rule change: only {' '.join(sorted(_only & set(parks)))} re-matched; {_kept} other park(s) kept their result")
        except FileNotFoundError: pass
        except Exception as e: notice(f'US key {st}', f'park-scoped keep skipped: {e}')  # noqa: BLE001
    try:
        for ref, t in transfers().items():
            if ref in parks: parks[ref]['run_by'] = t.get('by', '') + (f" since {t['since']}" if t.get('since') else '')
            if ref in parks and t.get('outline_note'): parks[ref]['outline_note'] = t['outline_note']
    except FileNotFoundError: pass
    except Exception as e: notice(f'US key {st}', f'transfer tags skipped: {e}')  # noqa: BLE001
    # Nov 2 (chat 2, map audit DUPLICATE pattern, chat 11 FIX): one record joined to two parks of DIFFERENT kinds (Woodson State
    # Wildlife Area's record also on Woodson State Fishing Lake; Backbone State Forest's on Backbone State Park; Loess Hills State
    # Forest / Wildlife Area): the record stays with the park whose kind its own name says, the other park gets it as 'check'.
    # Same kind on both (same land, two park numbers) is left alone; hand joins ('reviewed' / chat answers) are never moved.
    try:
        _by = {}
        for _r, _p in parks.items():
            for _q in _p.get('m') or []:
                if str(_q[0]).startswith('trl') or re.search(r'review|chat|hand|answer', str(_q[3] if len(_q) > 3 else ''), re.I): continue
                _by.setdefault(str(_q[0]), []).append(_r)
        _moved = []
        for _id, _rs in _by.items():
            if len(_rs) < 2: continue
            _qn = next(q[1] for q in parks[_rs[0]]['m'] if str(q[0]) == _id)
            _kq = kinds(_qn)   # batch 1b: was '_kr', which made _kr() (the switch test) a local name in run(): every state stopped
            if not _kq: continue
            _fit = [r for r in _rs if kinds(parks[r].get('n')) & _kq]
            if not _fit or len(_fit) == len(_rs): continue
            for _r in _rs:
                if _r in _fit: continue
                _p = parks[_r]; _q = [q for q in _p['m'] if str(q[0]) == _id]
                _p['m'] = [q for q in _p['m'] if str(q[0]) != _id]
                if not _p['m']: _p['g'] = 'pin'   # owner rule, 2026-11-10: no joined record left = a pin, never 'official'
                _p['c'] = [list(q[:3]) + [f'record also joined to {", ".join(_fit)} whose kind it names'] for q in _q] + (_p.get('c') or [])
                _moved.append(_r)
        if _moved: notice(f'US key {st}', f"{len(_moved)} parks gave back a record joined to another park of the kind it names: {', '.join(_moved[:10])}")
    except Exception as _e: notice(f'US key {st}', f'one-record-two-parks pass skipped: {_e}')  # noqa: BLE001
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
    _selfchk(st, parks, recs)   # Nov 2 review: pre-handoff self-checks + confidence (switches KPC_SELF_CHECKS / KPC_CONF_SORT; off = today)
    # Nov 4 PM fix bundle (item 11a, Quality v3 should-fix; Brandon's yes relayed via Super Head Bot, 4:53 PM CST Nov 4): the self-checks
    # run BEFORE 'bk' is written, so a park that KPC_SELF_CHECKS=hold moves from joined to check gets its bk from what is left.
    # Nov 4 (links-10; per Brandon via Super Head Bot (relayed), 7:13 AM CST Nov 4: 'Yes, add distance and kind to the keys in this
    # rebuild'): every park gets 'bk' = [best record id, km from the POTA pin, the record's kind (PAD-US Des_Tp, else its name's
    # kind tags), src] (kpc_key_facts.py). Measures only: no join, no pin is changed.
    try:
        _byid = {_oid(a): a for a in recs}
        def _bkpin(ref):
            r = P.get(ref) or []
            la_, lo_ = (r[5], r[6]) if len(r) > 6 else (None, None)
            if la_ is None and ref in pins(): la_, lo_ = pins()[ref]
            return la_, lo_
        def _bklook(x):
            a = _byid.get(str(x[0]))
            return (rings(a.get('_g')), a.get('Des_Tp') or '') if a else (None, '')
        _bkk, _bkn = KF.stamp(parks, _bkpin, _bklook)
    except Exception as _e:  # noqa: BLE001
        _bkk, _bkn = {}, None; notice(f'US key {st}', f'pin distance / kind (bk) skipped: {type(_e).__name__}: {str(_e)[:120]}')
    out = {'updated': time.strftime('%Y-%m-%d'), 'st': st, 'note': 'Built by .github/scripts/kpc_us_key.py from USGS PAD-US (fed + state fee land) and POTA. m = joined (same name + same kind), c = check by hand (NOT joined).',
           'counts': counts, 'parks': parks, 'nonum': nonum[:300],
           'bk_about': KF.ABOUT, 'bk_kinds': {c: t for c, t in _bkk.items() if c != t}}   # links-10
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
    _fs_owned_note(parks)
    _tract_store(st, parks, recs)
    save_json(OUT / f'US-{st}.json', out)
    return counts


# Nov 2 review (Mapping #7): a rebuild used to write index.json without the build stamp, so the stamp was simply lost.
# The old stamp is now kept as previous_build / previous_built (NOT as 'build': the content changed, so it is not that build any
# more). The workflow that saves the rebuild stamps it again (kpc_key_freeze.py stamp); if one forgets, the copy bot gives the
# new content its own id, which is honest.
def _with_old_stamp(d):
    try: _o = json.load(open(OUT / 'index.json'))
    except Exception: _o = {}  # noqa: BLE001
    _o = _o if isinstance(_o, dict) else {}
    _pb, _pt = _o.get('build') or _o.get('previous_build'), _o.get('built') or _o.get('previous_built')
    if _pb: d['previous_build'] = _pb
    if _pt: d['previous_built'] = _pt
    return d


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
if REFILL_ONLY:
    if LAYER_OUT is not None:   # Nov 10: the key's own layer table (prefix -> url, name field, label, states) for the master step's rows
        LAYER_OUT.mkdir(parents=True, exist_ok=True)
        _xs = {}
        for x in XS: _xs.setdefault(x[0], {'url': x[1], 'name_field': x[2], 'label': x[5], 'states': sorted(x[7]) if len(x) > 7 and x[7] is not None else None})
        for x in SZ_US: _xs.setdefault(x[0], {'url': x[1], 'name_field': x[2][0], 'label': x[4], 'states': sorted(x[6])})
        _xs[''] = {'url': Q, 'name_field': 'Unit_Nm', 'label': 'USGS PAD-US', 'states': None}
        (LAYER_OUT / 'xs.json').write_text(json.dumps(_xs, indent=1, sort_keys=True))
    for st in STATES:
        if st == 'KY': continue
        try: run(st)
        except Exception as e: notice(f'US key {st}', f'refill FAILED: {e}')  # noqa: BLE001
    notice('US key refill', f"saved copies re-saved: {' '.join(CACHE_SAVED) or 'none'}")
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
    save_json(OUT / 'index.json', _with_old_stamp({'states': idx}))
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
    LJ['trl'] = ['file:data/trails/US-{n}.json', 'name', 'official national trail lines (Park Service / Forest Service / BLM): one LINE file per park, trl<n> = US-<n>; draw as a line, POTA 100-ft band']
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
