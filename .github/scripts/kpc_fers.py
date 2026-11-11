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
- Official and approximate outlines from the answer keys (data/us-key, data/ca-key). Approximate and point-circle
  pairs are an approximate 2-fer, never shown as official. WDPA / Protected Planet is never a public 2-fer source.
  A lake surface is not a land outline. Never a park whose pin is well outside its land. POTA parks only.
- A spot counts only when the overlap holds a spot AT LEAST 50 YARDS ACROSS (Oct 26 2:11 PM; was 100): shrink the overlap 25 yards inward
  and something must remain (no slivers, no parks that only touch). Holes (inholdings) in an outline stay holes.
- TRAILS + RIVERS (official lines, data/trails): POTA's rule = the station entirely within 100 ft of the trail (KPC applies
  the same to rivers). So a stretch AT LEAST 25 METRES LONG (STRETCH; KPC owner, 2026-11-11) where a station spot inside the
  other park (5 m in) is within 100 ft of the line; two lines: their 100-ft zones meet along 25 metres. A line whose whole
  saved copy is shorter than 25 metres is a broken copy, not the trail: its pairs are NOT SURE (fix the line), never dropped.
- n-fers: a 3-fer is three parks whose boundaries may overlap at the SAME place (never a chain); same up to 9 (Oct 27).
- Two park numbers joined to the SAME outline record (Oct 27 10:35 AM, HQ: the 'never a 2-fer' rule is retired): SHOWN as
  'Same land, two park numbers' everywhere (US, Canada, Kentucky); also listed in data/fers/same-outline.json.
- Oct 27 (Fable's design review, HQ GO): passes 1-2 only SCREEN (any overlap pixel goes on), pass 3 decides the 25/50/100-yard
  tiers; ownership sampled at up to 5 points of the patch; no public fee owner at the spot = NOT SURE; an owned-land mask that
  empties the overlap = a NOT SURE row (never silence); tile caches kept small; Canada: water + roads not checked yet = NOT SURE.
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
import kpc_http_cache as HC
import numpy as np
import cv2
sys.path.insert(0, os.path.dirname(__file__))
from kpc_save import save_json
import kpc_fers_count as FCOUNT  # noqa: E402  Nov 6: 2-fer count switch, KPC_FERS_COUNT_MODE (default whole_park = today, untouched)
_save_json_raw = save_json


def save_json(p, d, *a, **k):  # noqa: F811
    return _save_json_raw(p, FCOUNT.apply(p, d), *a, **k)
import kpc_owned as KO
import kpc_fers_guard as FG   # Nov 4 (Mapping 2-fer review): bad POTA pins, one-record same land, overrides 'no'
import kpc_fers_key_status as FKS  # Nov 6 (Quality 2-fer grade): area/same-land follow key PIN/approximate
from kpc_fers_key_status import key_line_match, load_key_status, KEY_STATUS  # noqa: E402
import kpc_fers_ready as FREADY  # Nov 8: declared ready-areas gate (ownership+management)
try:
    import kpc_key_freeze as KFREEZE  # Nov 8: declared 2-fer rules hash (kind 'fers')
except Exception:  # noqa: BLE001
    KFREEZE = None


T0 = time.time(); LIMIT = float(os.environ.get('MINUTES') or 300) * 60
PASS = int(os.environ.get('PASS') or 1)
ONLY = set((os.environ.get('STATES') or '').upper().replace(',', ' ').split())
# Oct 28 (HQ 2:58 PM, Brandon): SMALL BATCHES. PARKS='US-1234 US-5678' = only the pairs touching those parks are looked at again
# (a park with a new or changed outline, from data/fers/pending.json); every other row of the file is carried over as it was.
PARKS = set((os.environ.get('PARKS') or '').upper().replace(',', ' ').split())
RUN_TAG = re.sub(r'[^a-z0-9-]', '', (os.environ.get('RUN_TAG') or '').lower())  # Oct 27 (HQ 5:11 PM): parallel region jobs keep their shared files apart
REGION = (os.environ.get('REGION') or 'na').strip().lower()      # 'na' = US + Canada, 'world' = the other countries (Brandon Oct 26: 'do the world')
CELL = {1: 20.0, 2: 10.0, 3: 5.0, 4: 5.0, 5: 5.0, 6: 5.0}[PASS]   # 4 = access pins only, for candidates that have none; 5 = re-check water + tidy the rows
DET = {1: 0.0005, 2: 0.0002, 3: 0.00002, 4: 0.00002, 5: 0.00002, 6: 0.00002}[PASS]
PREC = {1: 5, 2: 5, 3: 6, 4: 6, 5: 6, 6: 6}[PASS]
# Oct 26 2:11 PM (Brandon, RULE CHANGES): the overlap must hold a spot at least 50 YARDS across (POTA only says the
# overlap must ENTIRELY contain the activator + station; 50 yd still clears map error); 50-100 yd = 'small overlap'.
SHRINK = 22.86            # 25 yards in from every edge = a spot 50 yards across
SMALL_M = 91.44           # under 100 yards across = 'small overlap: tight fit, check carefully'
# Oct 27 4:59 AM (Brandon, rule 4 tiers): 25-50 yards across = a separate VERY TIGHT list (members only, 'could be map error: check
# both official maps on the ground'); under 25 yards = not shown. 'Across' = a circle that size fits: shrink by half from every edge.
TIGHT_M = 45.72           # 50 yards: below this = very tight
TIGHT_SHRINK = 11.43      # 12.5 yards in from every edge = a spot 25 yards across (the smallest kept)
VERY_TIGHT = 'very tight: could be map error: check both official maps on the ground'
# KPC owner, 2026-11-11: a trail / river stretch counts only when it runs at least 25 METRES (about 27 yards) along the line
# inside the other park: room to set up, longer than the usual 10-20 m map slop. Measured on the joined stretch (pieces of one
# line that touch count together); passes 1-2 only screen (every stretch goes on), pass 3 applies it.
STRETCH = 25.0
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
# Nov 9 PM (run 42649544758; Brandon t905u/t906u: one good, complete US + Canada result): ONE park can never freeze a pass, and a
# pass never runs past its step. KPC_FERS_PARK_S (default 600) = the most one park / pair / map request may take; past it, that
# park is skipped and listed (TIMED_OUT, in the report). KPC_HARD_END (epoch seconds, set by the workflow) = the step's own end:
# the bot stops there with exit 3, so the run shows red instead of a green check after a 335-minute time-out.
import signal


class ParkTimeout(BaseException):
    """One park / pair / request ran past KPC_FERS_PARK_S. BaseException, so the many 'except Exception' blocks never eat it."""


class HardStop(BaseException):
    """The step's own end (KPC_HARD_END) arrived: stop now (exit 3, red run); the areas not saved keep their previous files."""


PARK_S = float(os.environ.get('KPC_FERS_PARK_S') or 600)
HARD_END = float(os.environ.get('KPC_HARD_END') or 0)
TIMED_OUT = {}      # {what ran too long: where} -> the report's 'timed out (skipped, listed for a person)'
TIMED_PAIRS = set()  # pairs skipped for time in find_spots (pass 1 carries their old rows over; passes 2-3 leave them waiting)
_CLOCKS = []


def _ring(signum, frame):
    now = time.time()
    if HARD_END and now >= HARD_END - .5: raise HardStop()
    if _CLOCKS and now >= min(_CLOCKS) - .5: raise ParkTimeout()
    _arm()


def _arm():
    if not hasattr(signal, 'setitimer'): return
    if signal.getsignal(signal.SIGALRM) is not _ring: signal.signal(signal.SIGALRM, _ring)
    ends = list(_CLOCKS) + ([HARD_END] if HARD_END else [])
    signal.setitimer(signal.ITIMER_REAL, max(.05, min(ends) - time.time()) if ends else 0)


class park_clock:
    """with park_clock('US-1+US-2', 'pass 1 pair') as c: ...   c.hit is True when the limit cut it short (skipped + listed)."""
    def __init__(self, label, where, seconds=None): self.label, self.where, self.s, self.hit = str(label), where, (PARK_S if seconds is None else seconds), False
    def __enter__(self):
        _CLOCKS.append(time.time() + self.s); _arm(); return self
    def __exit__(self, et, ev, tb):
        _CLOCKS.pop(); _arm()
        if et is ParkTimeout:
            self.hit = True
            TIMED_OUT[self.label] = f'{self.where}: over {self.s:.0f} s, skipped (listed for a person)'
            LOG.append(f'{self.label}: over the {self.s:.0f}-second limit ({self.where}): skipped, listed')
            return True
        return False


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', ' ')[:900]), flush=True)
def late(screen=False, frac=None):
    """Out of time? Pass 3 stops LOOKING at 70% of its time, so deciding the spots it found (ownership, water, pins) fits.
    Nov 9 PM: frac = a share of the pass (pass 1 downloads stop at half, so the pairs always get tested); 2 minutes before the
    step's hard end (KPC_HARD_END) is always late."""
    if HARD_END and time.time() > HARD_END - 120: return True
    return time.time() - T0 > LIMIT * (frac if frac is not None else .7 if screen else 1)
def low(x): return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', str(x or '').lower()).split())


GET_ONLY = set()
def get(url, params, tries=3, timeout=120):
    return HC.cached(url, params, lambda: _get(url, params, tries, timeout))   # assembly-line bundle cache (kpc_http_cache.py)


def _get(url, params, tries=3, timeout=120):
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
BAD_PIN = {}   # Nov 4 (Mapping 2-fer review #1): {ref: (name, why, area)} POTA pins at 0,0 / impossible: listed, never moved, never used


NOPIN_BY_ID = set()   # Nov 9 PM (Brandon t902u): bad POTA pin, but saved official record ids in the key: tested by those outlines


def _pin(P, r, v):
    why = FG.pin_problem(v[1], v[2])
    if why:
        BAD_PIN[r] = (v[0], why, v[5])
        # Nov 9 PM (Brandon t901u/t902u: 'are we not going to matched id numbers also?'): a 0,0 / impossible pin is never used and
        # never moved. US + Canada parks keep their NAME with no coordinates (None, None), so a park whose key has saved official
        # record ids is tested by those outlines; nothing is ever looked up around a bad pin. (CA-2062: pin 0,0, saved id 22162.)
        if str(v[5]).startswith('W-'): P.pop(r, None)
        else: P[r] = (v[0], None, None) + tuple(v[3:])
        return
    P[r] = v


def pins():
    P = {}
    for f in pathlib.Path('data/parkinfo').glob('US-*.json'):
        for r, v in json.load(open(f))['parks'].items():
            if v[5] is not None: _pin(P, r, (v[0], v[5], v[6], v[1], v[2], f.stem[3:]))
    try:
        for r, v in json.load(open('data/parkinfo/CA.json'))['parks'].items():
            if v[5] is not None and len(v) > 10:
                # Nov 4 (Mapping 2-fer review #1; rule: never move POTA pins): the Oct 31 swap guess for an impossible Canadian pin
                # (Churchill WMA) is gone. An impossible or 0,0 pin is listed in BAD_PIN and the park waits for POTA to fix it.
                _pin(P, r, (v[0], v[5], v[6], v[1], v[2], 'CA-' + v[10]))
    except Exception: pass  # noqa: BLE001
    try:   # Kentucky's parks live in kpc-ky-data.json (data/parkinfo/KY.json is the Cayman Islands)
        for x in json.load(open('kpc-ky-data.json')).get('parks') or []:
            if x.get('la') is not None: _pin(P, x['c'], (x.get('n', ''), x['la'], x['lo'], x.get('web', ''), x.get('t', ''), 'KY'))
    except Exception: pass  # noqa: BLE001
    for f in pathlib.Path('data/parkinfo').glob('[A-Z][A-Z].json'):
        if f.stem in ('CA', 'US'): continue

        try:
            for r, v in json.load(open(f))['parks'].items():
                if len(v) > 6 and v[5] is not None and v[6] is not None: _pin(P, r, (v[0], v[5], v[6], v[1], v[2], 'W-' + f.stem))
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


PADMANG = {}


def agency_kind(m):
    """Which owned-land mask a park's joined records need (pre-flight fixes 2-4): BLM planning areas, Forest Service NRAs /
    monuments, Park Service units (PF-1: owned land only), Corps projects, FWS approved boundaries, Michigan project lines."""
    pres = {re.match(r'[a-z]+', str(x[0])).group() for x in m if isinstance(x[0], str) and re.match(r'[a-z]+', str(x[0]))}
    if pres & {'rst', 'hma', 'hab', 'rma', 'nca'}: return 'blm'
    if pres & {'mid'}: return 'state'
    if pres & {'sgmac'}: return 'nps'
    if pres & {'sgazd'}: return 'fws'
    if not PADMANG:
        for f in CACHE_US.glob('US-*.json.gz'):
            try:
                with gzip.open(f, 'rt', encoding='utf-8') as fh:
                    for r in json.load(fh).get('recs') or []:
                        if isinstance(r.get('OBJECTID'), int): PADMANG[r['OBJECTID']] = (r.get('Mang_Name') or '', r.get('Category') or '')
            except Exception: pass  # noqa: BLE001
        PADMANG['_'] = ('', '')
    mg = {PADMANG.get(x[0], ('', ''))[0] for x in m if isinstance(x[0], int)} - {''}
    if len(mg) == 1:
        return {'USFS': 'usfs', 'NPS': 'nps', 'USACE': 'usace', 'BLM': 'blm'}.get(next(iter(mg)))
    return None


def blocked_ids(root='.'):
    """Nov 9 evening (Brandon t919u, 4:48 PM CST): {ref: {id}} from the keys' 'blocked_ids' lists (US + Canada overrides.json); an entry
    counts only with decided_by. A blocked id is never used for that park here either (the key drops it at its next build)."""
    out = {}
    for f in ('data/us-key/overrides.json', 'data/ca-key/overrides.json'):
        try:
            for b in json.load(open(pathlib.Path(root) / f)).get('blocked_ids') or []:
                if b.get('ref') and b.get('id') not in (None, '') and str(b.get('decided_by') or '').strip(): out.setdefault(b['ref'], set()).add(str(b['id']))
        except Exception: pass  # noqa: BLE001
    return out


def drop_blocked(parks, B=None):
    B = blocked_ids() if B is None else B
    for ref, ids in B.items():
        p = parks.get(ref)
        if not p: continue
        keep = [i for i in p['ids'] if str(i) not in ids]
        if len(keep) != len(p['ids']):
            LOG.append(f"{ref}: blocked id(s) {', '.join(sorted(ids))} not used (blocked_ids)")
            if keep: p['ids'] = keep
            else: parks.pop(ref)
    return parks


def official_parks(PIN):
    """{ref: {'st', 'ids': [record ids], 'names': {id: name}}} + why parks were left out."""
    water_prefixes()
    parks, skip = {}, {'approximate': 0, 'pin well outside': 0, 'no outline': 0, 'no pin': 0, 'Kentucky (own list)': 0,
                       'bad POTA pin (0,0 / impossible, listed)': 0, 'every joined piece is in the overrides no list (key not rebuilt yet)': 0}
    # Nov 4 (Mapping 2-fer review #4): a piece a person (or a ruling) said is NOT this park ('no' in overrides.json) is never
    # tested, even when the answer key file was built before that 'no' was written (the keys wait for a rebuild)
    NO = {k: FG.override_no(f'data/{k}-key/overrides.json') for k in ('us', 'ca', 'world')}

    def _bad(ref, m=None, p=None):
        # Nov 9 PM (Brandon t902u): the key's own 'pin00' mark (bk[4]) counts as a bad pin even if POTA's file changed since
        if p is not None and len(p.get('bk') or []) > 4 and p['bk'][4] == 'pin00' and ref not in BAD_PIN and ref in PIN:
            BAD_PIN[ref] = (PIN[ref][0], "the key marks this POTA pin 'pin00'", PIN[ref][5]); PIN[ref] = (PIN[ref][0], None, None) + tuple(PIN[ref][3:])
        if ref not in BAD_PIN: return False
        if REGION == 'na' and m and all(x[0] is not None for x in m):
            NOPIN_BY_ID.add(ref); return False   # saved official record ids: tested by the outline, the pin is not needed
        skip['bad POTA pin (0,0 / impossible, listed)'] += 1; SKIPWHY[ref] = f'{BAD_PIN[ref][1]}: POTA\'s pin, never moved; not tested until POTA fixes it'
        return True

    def _no(ref, m, k):
        m2 = FG.drop_no(m, NO[k].get(ref))
        if m and not m2:
            skip['every joined piece is in the overrides no list (key not rebuilt yet)'] += 1
            SKIPWHY[ref] = 'every joined piece is in the overrides no list (a person said: not this park); waits for the key rebuild'
        elif len(m2) < len(m): LOG.append(f'{ref}: {len(m) - len(m2)} joined piece(s) in the overrides no list left out (key not rebuilt yet)')
        return m2
    if REGION == 'ky':   # Oct 26 (Brandon: 'run just KY and see if it matches the guide'): Kentucky's own answer key + official files
        k = json.load(open('data/ky-answer-key.json'))['parks']
        for ref, p in k.items():
            tr = [t for t in p.get('tracts') or [] if t[0] not in ('bdbnf', 'bkpc', 'btrail', 'trl')]   # the forest's proclamation line and KPC-drawn outlines are not proof; Oct 31 (Fable #15): a trail's own line tract = a LINE park (tested by its line below), never an area
            if not tr: skip['no outline'] += 1; SKIPWHY[ref] = 'no official boundary'; continue
            if ref in KY_NOT_SURE: skip['no outline'] += 1; SKIPWHY[ref] = KY_NOT_SURE[ref]; continue   # ruling Oct 27: a line park, not its land tracts
            if _bad(ref): continue
            if ref not in PIN: skip['no pin'] += 1; continue
            parks[ref] = {'st': 'US-KY', 'ids': [f'{t[0]}|{t[1]}' for t in tr], 'names': {f'{t[0]}|{t[1]}': t[1] for t in tr}}
            if all(t[0] != 'bpad' for t in tr): AGENCY.add(ref)   # Kentucky's agency files (state parks, KDFWR, nature preserves, NPS, FWS)
        # Daniel Boone NF: its KY file is the PROCLAMATION line (private land and towns inside). The Forest Service's own FEE
        # land comes from PAD-US instead (downloaded each run), so only real forest land counts.
        if 'US-4484' in PIN:
            # Oct 27: the outer line (ky-dbnf.geojson) masked by Forest Service Basic Ownership = owned land INSIDE the forest (rule 1b);
            # PAD-US's fee records missed whole districts (Redbird WMA, 24,000 acres of Forest Service land, never paired)
            parks['US-4484'] = {'st': 'US-KY', 'ids': ['bdbnf|Daniel Boone National Forest'], 'names': {'bdbnf|Daniel Boone National Forest': 'Daniel Boone National Forest'}}
            skip['no outline'] -= 1
            OWNED['US-4484'] = 'usfs'   # ruling Oct 27: Daniel Boone = Forest Service-OWNED land only (Basic Ownership)
        # Oct 28 (HQ): Mammoth Cave = Park Service-owned land (PAD-US fee, 50,624 ac; the unit line includes private inholdings);
        # Land Between the Lakes = Forest Service-owned land (Basic Ownership holds 'Land Between the Lakes NRA', runner probe Oct 28)
        for r, kind in (('US-0050', 'nps'), ('US-3792', 'usfs')):
            if r in parks: OWNED[r] = kind
        skip.pop('Kentucky (own list)', None)
        add_approx_outlines(parks, PIN, skip, 'ky')
        return parks, skip
    if REGION == 'world':
        for f in sorted(pathlib.Path('data/world-key').glob('[A-Z][A-Z].json')):
            for ref, p in json.load(open(f))['parks'].items():
                m = p.get('m') or []
                m0, m = m, _no(ref, m, 'world')
                if m0 and not m: continue
                if not m or p.get('g') == 'pin': skip['no outline'] += 1; SKIPWHY[ref] = 'no official boundary'; continue
                if is_wdpa_outline(p):
                    WDPA_SKIP.append({'ref': ref, 'why': 'WDPA / Protected Planet is never a public 2-fer source'}); continue
                apx = p.get('g') == 'approximate' or any('approx' in str(x[3]) for x in m if len(x) > 3) or p.get('approx')
                if _bad(ref): continue
                if ref not in PIN: skip['no pin'] += 1; continue
                if outline_unlabelled(p, 'W'): WDPA_SKIP.append({'ref': ref, 'why': 'outline source not labelled: not official'}); SKIPWHY[ref] = 'outline source not labelled (fail closed)'; continue
                parks[ref] = {'st': 'W-' + f.stem, 'ids': [x[0] for x in m], 'names': {str(i): x[1] for i, x in enumerate(m)}, 'm': m, 'approx': apx}
                if apx: APX_PARKS.add(ref)
        skip.pop('Kentucky (own list)', None)
        add_approx_outlines(parks, PIN, skip, 'world')
        return parks, skip
    for f in sorted(pathlib.Path('data/us-key').glob('US-*.json')):
        st = f.stem
        if st == 'US-KY': continue
        for ref, p in json.load(open(f))['parks'].items():
            m = p.get('m') or []
            m0, m = m, _no(ref, m, 'us')
            if m0 and not m: continue
            if (not m or p.get('g') == 'pin') and ref in PC and ref in PIN:   # point-circle tier only
                parks[ref] = pc_park(ref, st); skip['point circle (100 ft, not a boundary)'] = skip.get('point circle (100 ft, not a boundary)', 0) + 1; continue
            if not m or p.get('g') == 'pin': skip['no outline'] += 1; SKIPWHY[ref] = 'no official boundary'; continue
            # Approximate outlines (picture traces, key g=approximate) are an approximate 2-fer, not a drop.
            # Lake-surface-only layers stay out (they are not a land outline). WDPA is never a public 2-fer.
            water_only = any(isinstance(x[0], str) and re.match(r'[a-z]+', str(x[0])).group() in WATER for x in m)
            apx = p.get('g') == 'approximate' or any('approx' in str(x[3]) for x in m if len(x) > 3) or p.get('approx')
            if water_only and not apx:
                skip['approximate'] += 1; SKIPWHY[ref] = 'lake surface only (not a land outline)'; continue
            if is_wdpa_outline(p):
                WDPA_SKIP.append({'ref': ref, 'why': 'WDPA / Protected Planet is never a public 2-fer source'}); continue
            if _bad(ref, m, p): continue
            if ref not in PIN: skip['no pin'] += 1; continue
            if outline_unlabelled(p, 'US'): WDPA_SKIP.append({'ref': ref, 'why': 'outline source not labelled: not official'}); SKIPWHY[ref] = 'outline source not labelled (fail closed)'; continue
            parks[ref] = {'st': st, 'ids': [x[0] for x in m], 'names': {str(x[0]): x[1] for x in m}, 'approx': apx}
            if apx: APX_PARKS.add(ref)
            if p.get('parts'): CLIP[ref] = p['parts']   # Oct 29 rule B12: only this park's own parts of a shared multipart record
            if AGENCY_LAND.search(PIN[ref][0]) and not re.search(r'wilderness|wild and scenic', PIN[ref][0], re.I): OWNED[ref] = 'usfs'   # rule 1b
            else:
                k = agency_kind(m)
                if k: OWNED[ref] = k
            # rule (c): the agency's OWN layer (state parks / WMA / NPS / FWS / river corridor maps), joined by name -> its
            # outline outranks POTA's pin. PAD-US joins (a national compilation) and BLM planning areas keep the pin test.
            if all(isinstance(x[0], str) and re.match(r'[a-z]+', x[0]).group() not in ('rst', 'hma', 'rma') and str(x[3]).startswith(('name', 'reviewed')) for x in m if len(x) > 3):
                AGENCY.add(ref)
    for f in sorted(pathlib.Path('data/ca-key').glob('CA-*.json')):
        if not re.fullmatch(r'CA-[A-Z]{2}', f.stem): continue
        for ref, p in json.load(open(f))['parks'].items():
            m = p.get('m') or []
            m0, m = m, _no(ref, m, 'ca')
            if m0 and not m: continue
            if (not m or p.get('g') == 'pin') and ref in PC and ref in PIN:   # point-circle tier only
                parks[ref] = pc_park(ref, f.stem); skip['point circle (100 ft, not a boundary)'] = skip.get('point circle (100 ft, not a boundary)', 0) + 1; continue
            if not m or p.get('g') == 'pin': skip['no outline'] += 1; SKIPWHY[ref] = 'no official boundary'; continue
            apx = p.get('g') == 'approximate' or any('approx' in str(x[3]) for x in m if len(x) > 3) or p.get('approx')
            if is_wdpa_outline(p):
                WDPA_SKIP.append({'ref': ref, 'why': 'WDPA / Protected Planet is never a public 2-fer source'}); continue
            if _bad(ref, m, p): continue
            if ref not in PIN: skip['no pin'] += 1; continue
            if outline_unlabelled(p, 'CA'): WDPA_SKIP.append({'ref': ref, 'why': 'outline source not labelled: not official'}); SKIPWHY[ref] = 'outline source not labelled (fail closed)'; continue
            parks[ref] = {'st': f.stem, 'ids': [x[0] for x in m], 'names': {str(x[0]): x[1] for x in m}, 'approx': apx}
            if apx: APX_PARKS.add(ref)
            if all(isinstance(x[0], str) and str(x[3]).startswith(('name', 'reviewed')) for x in m if len(x) > 3): AGENCY.add(ref)   # provincial / Parks Canada layer, not CPCAD
    if NOPIN_BY_ID: skip['bad POTA pin, tested by its saved record ids (pin not used)'] = len(NOPIN_BY_ID)
    try: skip['Kentucky (own list)'] = len(json.load(open('data/parkinfo/US-KY.json'))['parks'])
    except Exception: skip['Kentucky (own list)'] = 'all (ky-overlaps.geojson)'  # noqa: BLE001
    add_approx_outlines(parks, PIN, skip, 'na')
    return parks, skip


AREA_BOX = []   # Oct 30: the run's area (box of its own park pins, padded ~20 km); a spot outside it is another area's


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
        try: _j = json.load(open(f)); g = _j.get('geometry') or {}; _wp = set((_j.get('properties') or {}).get('water_parts') or [])
        except Exception: continue  # noqa: BLE001
        c = g.get('coordinates') or []
        ls = c if g.get('type') == 'MultiLineString' else ([c] if g.get('type') == 'LineString' else [])
        _keep = [i for i, l in enumerate(ls) if len(l) > 1]
        _wp = {_keep.index(i) for i in _wp if i in _keep}
        ls = [ls[i] for i in _keep]
        if ls: out[x['ref']] = {**({'water_parts': sorted(_wp)} if _wp else {}), 'lines': ls, 'kind': 'river' if x.get('kind') == 'WSR' or re.search(r'river', str(x.get('type')), re.I) else 'trail',
                                'by': x.get('by') or '', 'type': x.get('kind') or x.get('type') or ''}
    return out


# Oct 27 (chat 8's KPC_TrailLines_desk.md + HQ): two official lines read LIVE from the agencies, replacing the saved copies.
# Pine Mountain State Scenic Trail = Kentucky's trails service layer 1 'Pine Mountain Trail (Open)' (the open 44 miles, Breaks to
# US 119; pairs on the planned stretch stay NOT SURE); Sheltowee Trace = the Forest Service's own trail line (TRAIL_NAME Sheltowee
# Trace), used only where the forest's districts say 'centerline data available'.
LIVE_LINES = {
    'US-10102': ('https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Recreational_Trails_WGS84WM/MapServer/1/query', '1=1',
                 "Kentucky State Parks / KY Division of Geographic Information: Ky_Recreational_Trails layer 1 'Pine Mountain Trail (Open)' (open section only, Breaks to US 119)"),
    'US-11181': ('https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_TrailNFSPublishWithDataStatus_01/MapServer/0/query', "UPPER(TRAIL_NAME) LIKE '%SHELTOWEE%'",
                 'U.S. Forest Service: EDW_TrailNFSPublishWithDataStatus_01 layer 0 (National Forest System Trails, TRAIL_NAME Sheltowee Trace)')}
FS_STATUS = 'https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_TrailNFSPublishWithDataStatus_01/MapServer'


WSR_HELD = {}   # W&S river ref -> why its pairs are held (no saved corridor copy)
WSRW = re.compile(r'\b(national )?(wild (and|&) scenic|wild|scenic|recreational) river\b', re.I)


def wsr_corridors(parks, PIN, LN):
    """Pre-flight fix 5 (rule 5): a wild & scenic river WITH an official corridor polygon is an AREA park. The answer key joined
    the NPS corridor layer to only 17 rivers; here every national W&S river park with no area outline is joined to its corridor
    by name (kind words dropped) when the corridor lies within ~1 degree of the pin; the others stay line parks."""
    core = lambda x: ' '.join(re.sub(r'[^a-z0-9 ]', ' ', WSRW.sub(' ', str(x or '').lower())).replace(' river', ' ').split())
    # owner rule, 2026-11-10: the corridors come from the key's saved copy (the corridor map is a saved-copy-only host), never live
    saved_us({})
    cors = [(int(k[4:]), SAVED_NAME.get(k) or '', core(SAVED_NAME.get(k)), bbox_groups([g])) for k, g in sorted(SAVED_STR.items())
            if re.fullmatch(r'wsrc\d+', k) and g]
    WSR_HELD.clear()
    n = 0
    for ref, v in PIN.items():
        if v[5].startswith(('W-', 'CA-')) or v[5] == 'KY' or not WSRW.search(v[0]) or v[1] is None: continue   # Nov 9 PM: never search around a bad pin
        if ref in parks and parks[ref]['ids'] and not any(str(i).startswith('wsrc') for i in parks[ref]['ids']) and ref not in LN: continue   # has its own area outline
        if not cors:   # no saved corridor copy at all: the river's pairs are held, never quietly tested as a line park
            WSR_HELD[ref] = 'saved copy missing for wsrc (W&S river corridors): needs download'; continue
        c = core(v[0])
        hit = [x for x in cors if c and x[2] == c and x[3] and x[3][0] - 1 <= v[2] <= x[3][2] + 1 and x[3][1] - 1 <= v[1] <= x[3][3] + 1]
        if not hit: continue
        parks[ref] = {'st': 'US-' + v[5], 'ids': [f'wsrc{x[0]}' for x in hit], 'names': {f'wsrc{x[0]}': x[1] for x in hit}}
        AGENCY.add(ref); LN.pop(ref, None); n += 1
    LOG.append(f'W&S river corridors joined as area parks: {n} (saved copy: {len(cors)} corridors)' + (f'; {len(WSR_HELD)} rivers held: no saved corridor copy' if WSR_HELD else ''))
    return n


def live_lines(LN):
    today = time.strftime('%Y-%m-%d')
    for ref, (url, where, by) in LIVE_LINES.items():
        if saved_only_host([url]): LOG.append(f'{ref} live line: saved-copy-only map, saved copy kept'); continue   # owner rule, 2026-11-10
        try:
            ls = []
            for fs in read_pages(lambda off: get(url, {'where': where, 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': DET / 4,
                                                       'geometryPrecision': 6, 'resultOffset': off, 'resultRecordCount': 1000, 'f': 'json'}, timeout=180)):
                for ft in fs:
                    for pth in (ft.get('geometry') or {}).get('paths') or []:
                        if len(pth) > 1: ls.append([[p[0], p[1]] for p in pth])
            if not ls: LOG.append(f'{ref} live line: nothing read, saved copy kept'); continue
            note = ''
            if ref == 'US-11181':   # the districts' 'centerline data available' layers
                try:
                    lays = [l for l in get(FS_STATUS, {'f': 'json'}).get('layers') or [] if re.search(r'centerline', l.get('name', ''), re.I)]
                    stat = []
                    for l in lays[:3]:
                        r = get(f"{FS_STATUS}/{l['id']}/query", {'where': "UPPER(FORESTNAME) LIKE '%DANIEL BOONE%'", 'outFields': '*', 'returnGeometry': 'false', 'f': 'json'})
                        for ft in r.get('features') or []:
                            a = ft.get('attributes') or {}
                            stat.append(' '.join(str(v) for k, v in a.items() if re.search(r'district|forest|status|avail', k, re.I) and v))
                    note = '; '.join(sorted(set(stat)))[:300] or 'district centerline status not listed'
                except Exception as e: note = f'district status not read ({str(e)[:40]})'  # noqa: BLE001
            LN[ref] = {'lines': ls, 'kind': 'trail', 'by': by, 'date': f'read live {today}', 'type': 'trail', **({'districts': note} if note else {})}
            KY_NOT_SURE.pop(ref, None)
        except Exception as e: LOG.append(f'{ref} live line: {str(e)[:60]}')  # noqa: BLE001


def read_pages(ask, most=500):
    """Every page of one paged query (ask(offset) -> answer), or an error: never a partial answer. The same first record twice
    (a server that ignores resultOffset) or more than `most` pages is an error."""
    pages, off, firsts = [], 0, set()
    for _ in range(most):
        j = ask(off); fs = j.get('features') or []
        if not fs: return pages
        f0 = json.dumps(fs[0].get('attributes') or fs[0].get('geometry'), sort_keys=True, default=str)
        if f0 in firsts: raise RuntimeError('the map ignored resultOffset (the same page twice)')
        firsts.add(f0); pages.append(fs)
        if not j.get('exceededTransferLimit'): return pages
        off += len(fs)
    raise RuntimeError(f'more than {most} pages')


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
    # Oct 31 (Fable review #3): US records are checked by NAME too (chk=True): a server that re-numbered its records can hand back
    # ANOTHER park's polygon under the same id (Florida far-check rows); the record must carry the park's record name
    if isinstance(rid, int): return [PADUS], rid, True
    m = re.fullmatch(r'([a-z]+)(\d+)', str(rid))
    if not m: return [], None, False
    pre, n = m.group(1), int(m.group(2))
    if pre == 'fws': return [FWS], n, True
    if pre in ('trl',): return [], None, False
    if pre in LAYERS_US: return [LAYERS_US[pre][0]], n, True
    return [], None, False


def name_ok(want, attrs):
    w = low(want)
    if not w: return True
    # Oct 29 (chat 8 NOT SURE group 1: NB 264 rows 'outline could not be read'): the key NAMES New Brunswick's management zones
    # 'New Brunswick #24 Wildlife Management Area' from the layer's zone NUMBER (field WMZ); the layer itself holds only the number
    m = re.match(r'new brunswick (\d+) wildlife management area$', w)
    if m and any(str(v).split('.')[0] == m.group(1) for k, v in attrs.items() if str(k).upper() == 'WMZ'): return True
    for v in attrs.values():
        if isinstance(v, str):
            v = low(v)
            if v and (v == w or (len(v) > 3 and (v in w or w in v))): return True
    return False


CLIP = {}   # {ref: {record id: [[w, s, e, n] part boxes]}} from the key (rule B12)


def clip(ref, rid, rs):
    """Rule B12 (Oct 29): keep only the rings whose middle sits in one of this park's own part boxes (a multipart record shared
    by two far-apart parks). Holes ride along with their part. No clip on the record = every ring."""
    boxes = (CLIP.get(ref) or {}).get(str(rid))
    if not boxes or not rs: return rs
    def mid(r): return ((min(p[0] for p in r) + max(p[0] for p in r)) / 2, (min(p[1] for p in r) + max(p[1] for p in r)) / 2)
    out = [r for r in rs if len(r) > 2 and any(b[0] - .01 <= mid(r)[0] <= b[2] + .01 and b[1] - .01 <= mid(r)[1] <= b[3] + .01 for b in boxes)]
    return out or rs


SLOW_MAP = {}   # Nov 9 PM: map url -> requests that ran past the limit this run (2 = the map is skipped for the rest of the run)
DL_CUT = set()  # Nov 9 PM: parks not downloaded for time


# Nov 9 (Brandon t949u + t950u, 6:50-6:51 PM CST: "If we have a point shouldn't we confirm 100' circle around pin at least?"): a park
# with NO boundary whose official POINT record matches its name near the POTA pin (POINT-CONFIRMED, data/point-circles.json) gets a
# 100 ft (30.48 m) circle around the OFFICIAL point (the POTA pin is never moved) as a stand-in. Its 2-fers are a separate, labelled
# 'point-circle' tier (never an official boundary; Quality filters on tier == 'point-circle'). A park with a real outline never uses
# it (the circle is dropped as soon as the key has a boundary). KPC_FERS_POINT_CIRCLE=0 turns the tier off.
PC_ON = (os.environ.get('KPC_FERS_POINT_CIRCLE') or '1') != '0'
PC_KIND = 'point-circle-100ft'
PC_LIST = '📍 Point circle: 100 ft around the official point (NOT an official boundary)'
PCT = set()   # the parks in this run that use a point circle
def pc_load():
    try: d = json.load(open('data/point-circles.json', encoding='utf-8')).get('parks') or {}
    except Exception: return {}  # noqa: BLE001
    return {r: v for r, v in d.items() if v.get('kind') == PC_KIND and v.get('pt') and len(v['pt']) == 2}
PC = pc_load() if PC_ON else {}
def pc_ring(lon, lat, r_m=30.48, n=24):
    k = math.cos(math.radians(lat))
    ring = [[round(lon + r_m * math.cos(2 * math.pi * i / n) / (111320.0 * k), 7), round(lat + r_m * math.sin(2 * math.pi * i / n) / 110574.0, 7)] for i in range(n)]
    return ring + [ring[0]]
def pc_park(ref, st):
    """the 2-fer park entry for a POINT-CONFIRMED park without a boundary (None when it has no circle)"""
    v = PC.get(ref)
    if not v: return None
    PCT.add(ref); i = f'pc|{ref}'
    return {'st': st, 'ids': [i], 'names': {i: f"{v.get('record_name') or ref} (100 ft point circle, {v.get('layer_name') or 'official point'})"}, 'pc': True}
def pc_note(ref):
    """the plain note every card shows for a point-circle park (Brandon t954u; neutral words, t952u). Same text as kpc-bounds.js pcNote."""
    v = PC.get(ref) or {}
    u = v.get('layer_url') or ''
    m = re.search(r'services/(.+?)/(?:MapServer|FeatureServer)/(\d+)', u, re.I)
    lay = (m.group(1).split('/')[-1].replace('_', ' ') + ' layer ' + m.group(2)) if m else ('official layer' if u else '')
    rid = v.get('record_id')
    src = ', '.join(x for x in [v.get('record_name') or '', lay, f'record {rid}' if rid not in (None, '') else ''] if x)
    return ("No official boundary on file. Using a 100 ft circle around the agency\u2019s official point" + (f' ({src})' if src else '')
            + '. The real boundary may be larger, so check before you activate.')
def pc_tag(d):
    """Tag approximate 2-fers (picture traces and point-circles) and keep point-circle details.
    The public tier is approximate. Quality can also read the point_circle list."""
    note = 'Not the official boundary. We believe this is a 2-fer, but it needs more research.'
    lst = 'Approximate 2-fer: not the official boundary; needs more research'
    for x in (d.get('spots') or []) if isinstance(d, dict) else []:
        refs = list(x.get('refs') or [])
        pr = sorted(set(refs) & PCT)
        ar = sorted(set(refs) & set(APX_PARKS) | set(x.get('approx_refs') or []))
        if pr:
            x['point_circle'] = pr
            x['pc_note'] = {r: pc_note(r) for r in pr}
        if pr or ar or x.get('approx'):
            x['tier'] = 'approximate'
            x['list'] = lst
            x['official_boundary'] = False
            x['approx_note'] = x.get('approx_note') or note
            if ar:
                x['approx_refs'] = ar
    return d


# Approximate 2-fer outlines (picture traces). Not official key outlines.
# WDPA / Protected Planet is never a public 2-fer source.
APX_NOTE = 'Not the official boundary. We believe this is a 2-fer, but it needs more research.'
APX_LIST = 'Approximate 2-fer: not the official boundary; needs more research'
WDPA_RX = re.compile(r'wdpa|protectedplanet|protected.?planet|unep-?wcmc|world_database_of_protected', re.I)
WDPA_SKIP = []   # refs whose outline is WDPA / Protected Planet (internal file only)
APX_PARKS = set()
APX_OUT = {}


def is_wdpa_outline(p=None, text=''):
    """True when the outline source is WDPA / Protected Planet (never a public 2-fer)."""
    bits = [text]
    if isinstance(p, dict):
        for k, v in p.items():
            if k in ('m', 'tracts', 'rings', 'geom', 'poly', 'coords'):
                for x in (v or [] if k in ('m', 'tracts') else []):
                    if isinstance(x, (list, tuple)):
                        bits.append(' '.join(str(i) for i in x[:6]))
                    elif isinstance(x, dict):
                        bits.append(' '.join(f'{kk}={vv}' for kk, vv in x.items() if kk not in ('rings', 'coords', 'geom')))
            elif k not in ('rings', 'geom', 'poly', 'coords'):
                bits.append(f'{k}={v}')
    return bool(WDPA_RX.search(' '.join(str(b) for b in bits)))


def outline_unlabelled(p, area):
    """True when a joined record of this key park has no source we can name (fail closed: an unlabelled outline is not official).
    US: a PAD-US number, a layers.json prefix, FWS or a trail line, or the park's own 'src'; Canada: a CPCAD number or the layer
    label the id carries ('<label>:<id>'); world: every joined row names its source."""
    for x in (p or {}).get('m') or []:
        if not isinstance(x, (list, tuple)) or not x: return True
        i = x[0]
        if area == 'W':
            if len(x) < 3 or not str(x[2] or '').strip(): return True
            continue
        if isinstance(i, int): continue
        if area == 'CA' and ':' in str(i):
            if not str(i).partition(':')[0].strip(): return True
            continue
        mm = re.fullmatch(r'([a-z]+)\d+', str(i))
        if mm and (mm.group(1) in ('fws', 'trl') or (area == 'US' and mm.group(1) in LAYERS_US)): continue
        if area == 'US' and any(str(v).strip() for v in (p.get('src') or [])): continue
        return True
    return False


def load_apx_outlines(root='.'):
    """Picture-trace outlines entered as approximate 2-fers (data/fers-approx-outlines.json)."""
    global APX_OUT
    if APX_OUT: return APX_OUT
    try:
        d = json.load(open(pathlib.Path(root) / 'data/fers-approx-outlines.json', encoding='utf-8'))
        APX_OUT = d.get('parks') or {}
    except Exception:
        APX_OUT = {}  # noqa: BLE001
    return APX_OUT


def has_official_outline(ref, parks=None, root=None):
    """True when this park already has an official (not approximate, not point-circle) outline.
    The official outline always wins; a picture trace must not replace it."""
    cur = (parks or {}).get(ref) or {}
    ids = [i for i in (cur.get('ids') or []) if i not in (None, '') and not str(i).startswith(('apx|', 'pc|'))]
    if ids and not cur.get('approx') and not cur.get('pc'):
        return True
    try:
        from kpc_fers_key_status import status_for, load_key_status
        load_key_status(root or '.')
        if status_for(ref) == 'official':
            return True
    except Exception:
        pass  # noqa: BLE001
    return False


def add_approx_outlines(parks, PIN, skip, region=None, root=None):
    """Enter passed picture traces only for parks that have no official outline.
    An official outline already in parks or in the key always wins (it is never overwritten).
    WDPA / Protected Planet outlines are skipped for the public list."""
    region = region if region is not None else REGION
    for ref, v in (load_apx_outlines(root or '.') or {}).items():
        if is_wdpa_outline(v) or not str(v.get('src') or '').strip():   # fail closed: an unlabelled trace is not used
            WDPA_SKIP.append({'ref': ref, 'why': 'WDPA / Protected Planet is never a public 2-fer source' if is_wdpa_outline(v) else 'outline source not labelled: not used'})
            continue
        if ref not in PIN: continue
        if has_official_outline(ref, parks, root=root):
            continue  # official wins (e.g. Salato US-10172, KDFWR HQ)
        st = v.get('st') or ('CA-' + PIN[ref][5] if str(ref).startswith('CA-') else 'US-' + PIN[ref][5])
        if not str(st).startswith(('US-', 'CA-', 'W-')):
            st = ('CA-' + st) if str(ref).startswith('CA-') else ('W-' + st if region == 'world' else 'US-' + st)
        if region == 'world':
            continue  # these traces are US / Canada parks
        if region == 'ky' and st not in ('US-KY', 'KY') and PIN[ref][5] not in ('KY', 'US-KY'):
            continue
        rings = v.get('rings') or []
        if not rings: continue
        i = f'apx|{ref}'
        parks[ref] = {'st': 'US-KY' if st in ('KY', 'US-KY') else st, 'ids': [i], 'names': {i: v.get('name') or ref},
                      'approx': True, 'rings': rings, 'approx_src': v.get('src') or 'picture trace of an official map'}
        APX_PARKS.add(ref)
        skip['approximate (picture trace)'] = skip.get('approximate (picture trace)', 0) + 1
    return parks


def inject_apx_geom(G, parks, refs=None):
    """Use picture-trace rings only when this park has no official outline."""
    for r, p in (parks or {}).items():
        if refs is not None and r not in refs: continue
        if p.get('rings') and p.get('approx') and not has_official_outline(r, parks):
            G[r] = [p['rings']]
            MAPDATE[r] = p.get('approx_src') or 'approximate picture trace'
            APX_PARKS.add(r)
    return G


SAVED_USE = set()     # parks whose outline (or part of it) came from a saved copy in download (never re-saved as a live read)
MISSING_SAVED = {}    # ref -> layer whose host is saved-copy only and whose record is in no saved copy


def saved_only_host(urls):
    """True when every map address of a record is on a saved-copy-only host (kpc_net_guard refuses it)."""
    us = [u for u in urls or [] if str(u).startswith(('http://', 'https://'))]
    return bool(us) and not any(HC.kpc_net_guard.host_ok(u)[0] for u in us)


def saved_missing_why(ref):
    return f"saved copy missing for {MISSING_SAVED[ref]}: needs download" if ref in MISSING_SAVED else ''


def _layer_name(rid, src=None, ca=False):
    if src: return str(src)
    if ':' in str(rid): return str(rid).partition(':')[0]
    m = re.fullmatch(r'([a-z]+)\d+', str(rid))
    return m.group(1) if m else 'CPCAD' if ca else 'PAD-US'


def download(parks, refs, det, prec):
    """{ref: [group of rings per record]} downloaded from the agencies by object id. A park with a record that could not
    be read is left out (dead certain: half a park is not the park). A record on a saved-copy-only host is taken from the
    same saved copy the key was built from (owner rule, 2026-11-10); none there = the park is held 'saved copy missing'."""
    _pc = {r: [[pc_ring(*PC[r]['pt'])]] for r in refs if r in PCT}   # Brandon t950u: the circle, never a download
    _apx = {r: [parks[r]['rings']] for r in refs if (parks.get(r) or {}).get('rings') and (parks.get(r) or {}).get('approx') and not has_official_outline(r, parks)}
    refs = [r for r in refs if r not in PCT and r not in _apx]
    want, saved, whole = {}, {}, set()
    if REGION == 'na' and refs: saved_us({})
    for ref in refs:
        ca = parks[ref]['st'].startswith('CA-')
        for i, rid in enumerate(parks[ref]['ids']):
            if 'm' in parks[ref]:
                urls, oid, chk = source_of(rid, False, parks[ref]['m'][i][2]); key = str(i)
            else:
                urls, oid, chk = source_of(rid, ca); key = str(rid)
            if saved_only_host(urls):
                if not ca and 'm' not in parks[ref] and str(rid) in SAVED_STR:
                    saved.setdefault(ref, []).append(clip(ref, rid, SAVED_STR[str(rid)])); continue
                if not ca and 'm' not in parks[ref] and str(rid) in SAVED_LEFT:
                    LEFT.setdefault(ref, []).append(f"{parks[ref]['names'].get(str(rid)) or rid}: {SAVED_LEFT[str(rid)]}"); saved.setdefault(ref, []); continue
                if ca or 'm' in parks[ref]: whole.add(ref)   # Canada / world: the park's own saved copy (below)
                MISSING_SAVED.setdefault(ref, _layer_name(rid, parks[ref]['m'][i][2] if 'm' in parks[ref] else None, ca))
            if not urls: want.setdefault(('none',), []).append((ref, key, None, chk)); continue
            want.setdefault(tuple(urls), []).append((ref, key, oid, chk))
    got, bad = {}, set()
    cut = set()   # Nov 9 PM: parks not reached for time (never half-read: 'half a park is not the park')
    for urls, items in want.items():
        if urls == ('none',):
            for ref, *_ in items: bad.add(ref)
            continue
        # Nov 9 PM (run 42649544758: pass 1 spent its whole 132 minutes downloading, 'pairs tested': 0): pass 1 stops downloading
        # at half its time, so the pairs it did read are always tested; the rest are listed and their areas keep their files
        if late(frac=.5 if PASS == 1 else None): cut |= {i[0] for i in items}; continue
        oids = sorted({i[2] for i in items})
        found = {}
        for u in urls:
            if u.startswith('file:'):   # Oct 28: a zipped-shapefile layer = the key's own simplified copy (no live map)
                try:
                    for ft in json.load(open(u[5:])).get('features') or []:
                        pr = ft.get('properties') or {}; mm = re.fullmatch(r'[a-z]+(\d+)', str(pr.get('OBJECTID')))
                        gm = ft.get('geometry') or {}
                        rs = gm.get('coordinates') or []
                        rs = rs if gm.get('type') == 'Polygon' else [r for poly in rs for r in poly]
                        if mm and int(mm.group(1)) in oids: found.setdefault(int(mm.group(1)), []).append((pr, rs))
                except Exception as e: LOG.append(f'{u}: not read ({str(e)[:60]})')  # noqa: BLE001
                continue
            for k in range(0, len(oids), 100):
                ids = [o for o in oids[k:k + 100] if o not in found]
                if not ids: continue
                if SLOW_MAP.get(u, 0) >= 2: LOG.append(f'{u.split("/rest/services/")[-1][:60]}: skipped (2 requests over the time limit this run)'); break
                j = None
                with park_clock(f'{u.split("/rest/services/")[-1][:50]} ids {ids[0]}..{ids[-1]}', 'outline download') as _c:
                    try:
                        j = get(u, {'objectIds': ','.join(map(str, ids)), 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326,
                                    'maxAllowableOffset': det, 'geometryPrecision': prec, 'f': 'json'})
                    except Exception as e:  # noqa: BLE001
                        LOG.append(f'{u.split("/rest/services/")[-1][:60]}: not read ({str(e)[:60]})')
                if _c.hit: SLOW_MAP[u] = SLOW_MAP.get(u, 0) + 1
                if j is None: continue
                oidf = j.get('objectIdFieldName') or 'OBJECTID'
                _d = HC.LAST or time.time()   # B2 (Oct 30): the date this answer was really read from the agency (a bundle answer is older)
                for f in j.get('features') or []:
                    a = f.get('attributes') or {}
                    o = a.get(oidf)
                    if o is None: o = next((v for k2, v in a.items() if k2.lower() in ('objectid', 'fid', 'oid', 'object id')), None)
                    if o is not None: found.setdefault(int(o), []).append((a, esri_rings(f.get('geometry')))); WHEN[(u, int(o))] = _d
                time.sleep(.3)
        # Oct 30 (chat 2, Iowa came out EMPTY twice: 173 of 182 outlines 'not read' with only 12 requests asked): some state servers
        # re-number their records when they re-publish (Iowa DNR's ids changed between the key build and the line), so a record
        # asked for by its id is simply not there. Then ask for it by its NAME in the same layer (the key's name field) and use
        # the record(s) of that name nearest the park's pin.
        _pre = lambda rid_: (re.fullmatch(r'([a-z]+)\d+', str(rid_)) or [None, None])[1]
        for ref, rid, oid, chk in items:
            if 'm' in parks[ref] or late(): continue
            if ref in NOPIN_BY_ID: continue   # Nov 9 PM: a bad pin = by saved id only, never 'the same name near the pin'
            if found.get(oid) and (not chk or any(name_ok(parks[ref]['names'].get(rid), a_) for a_, _ in found[oid])): continue   # Oct 31: an id that now names ANOTHER place is looked up by name too
            pre_ = _pre(parks[ref]['ids'][int(rid)] if str(rid).isdigit() and 'm' in parks[ref] else rid)
            lay = LAYERS_US.get(pre_) if pre_ else None
            nm_ = parks[ref]['names'].get(rid) or ''
            if not lay or len(lay) < 2 or not lay[1] or not nm_: continue
            if SLOW_MAP.get(lay[0], 0) >= 2: continue
            try:
                with park_clock(f'{ref} by name', 'outline download by name') as _c:
                    j = get(lay[0], {'where': f"{lay[1]} = '{nm_.replace(chr(39), chr(39) * 2)}'", 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326,
                                     'maxAllowableOffset': det, 'geometryPrecision': prec, 'f': 'json'})
                if _c.hit: SLOW_MAP[lay[0]] = SLOW_MAP.get(lay[0], 0) + 1; continue
                global _PINS
                if _PINS is None: _PINS = pins()
                pin = _PINS.get(ref)
                fs = [(f.get('attributes') or {}, esri_rings(f.get('geometry'))) for f in j.get('features') or []]
                fs = [x for x in fs if x[1]]
                if pin and pin[1] is not None and len(fs) > 1:   # Oct 31 (Fable #3): keep EVERY same-name record near the pin (a park of several
                    # tracts of one name keeps them all), only far namesakes (another place of the same name) are left out
                    dist = lambda x: min(abs(q[1] - pin[1]) + abs(q[0] - pin[2]) for rr in x[1] for q in (rr[::20] or rr))
                    d0 = min(dist(x) for x in fs)
                    fs = [x for x in fs if dist(x) <= d0 + .15]
                if fs: found[oid] = fs; FOUNDBYNAME.add(ref)
            except Exception as e: LOG.append(f'{lay[0].split("/rest/services/")[-1][:50]}: by-name not read ({str(e)[:40]})')  # noqa: BLE001
            time.sleep(.3)
        for ref, rid, oid, chk in items:
            cand = [(a, r) for a, r in (found.get(oid) or []) if r and (not chk or name_ok(parks[ref]['names'].get(rid), a))]
            if not cand: bad.add(ref); continue
            a, r = cand[0]
            use, why = fws_use(a) if FWS in urls else pad_use(a, ref) if PADUS in urls else (True, None)
            if use:
                got.setdefault(ref, []).append(clip(ref, parks[ref]['ids'][int(rid)] if 'm' in parks[ref] else rid, r))
                _w = [WHEN[(u, oid)] for u in urls if (u, oid) in WHEN]
                if _w: READ[ref] = min([READ.get(ref, 9e12)] + _w)
            else: LEFT.setdefault(ref, []).append(f'{parks[ref]["names"].get(rid) or rid}: {why}')   # rule 2: left out, not 'unreadable'
    for ref, gs in saved.items():   # records from the saved copy (saved-copy-only host): never asked, never cut for time
        if ref in bad or ref in cut: continue
        if gs: got.setdefault(ref, []).extend(gs)
        SAVED_USE.add(ref)
    for ref in bad | cut: got.pop(ref, None)
    cut -= bad
    DL_CUT.update(cut)
    if cut: LOG.append(f'{len(cut)} parks not downloaded: out of time (listed; their areas keep their previous files)')
    for ref in ({i[0] for v in want.values() for i in v} | set(saved)) - bad - set(got) - cut:
        if ref in LEFT: bad.add(ref)   # every record of this park was left out (all easement / closed): no public land to test
    _miss = sorted(r for r in bad if r in MISSING_SAVED)
    if _miss:   # a saved-copy-only record the key copy does not hold: the park's other saved copies, else held with the reason
        if LIVE_FILE is None and REGION == 'na': live_load(area_name())
        _ca = saved_ca({r: parks[r] for r in _miss if r in whole and parks[r]['st'].startswith('CA-')})
        _w = saved_world({r: parks[r] for r in _miss if r in whole and parks[r]['st'].startswith('W-')}) if any(parks[r]['st'].startswith('W-') for r in _miss) else {}
        for r in _miss:
            g = _ca.get(r) or _w.get(r) or (LIVE[r]['g'] if r in LIVE and [str(i) for i in parks[r]['ids']] == LIVE[r].get('ids') else None)
            if g: got[r] = g; bad.discard(r); SAVED_USE.add(r); MAPDATE[r] = 'saved copy (saved-copy-only map)'
    for r in [r for r in MISSING_SAVED if r in got]: MISSING_SAVED.pop(r)
    if MISSING_SAVED: LOG.append(f"{len(MISSING_SAVED)} parks held: saved copy missing (saved-copy-only maps): " + ', '.join(sorted(MISSING_SAVED)[:10]))
    today = time.strftime('%Y-%m-%d')
    for ref in got:   # B2 (Oct 30): the real read date (a reused bundle answer can be up to weeks old), never 'today' for an old answer
        if ref in SAVED_USE and ref not in READ:
            MAPDATE[ref] = MAPDATE.get(ref) if str(MAPDATE.get(ref) or '').startswith('saved copy') else 'saved copy (answer key)'; continue
        MAPDATE[ref] =f"read from the agency {time.strftime('%Y-%m-%d', time.gmtime(READ[ref]))}" if ref in READ else f'downloaded {today}'
    got.update(_pc)
    got.update(_apx)
    inject_apx_geom(got, parks)
    return got, bad


SAVED_LEFT = {}


SAVED_STR = {}   # Nov 9 evening: str(record id) -> rings for every saved record (state layers, FWS, ... not only PAD-US)
SAVED_DATE = {}
SAVED_NAME = {}   # str(record id) -> the record's name (the W&S corridors are joined by name from the saved copy)
_SAVED_BY = []


def area_name():
    return 'ky' if REGION == 'ky' else RUN_TAG or ('-'.join(sorted(ONLY)) if ONLY else REGION)


def saved_us(parks):
    """PAD-US records from the boundary cache (the answer key's own saved copy). Nov 9 evening (Brandon t909u 'saved outlines
    first'): the state-layer / FWS / line records in the same copy are kept too (SAVED_STR), so a park is downloaded live only
    when one of its record ids is not in any saved copy. Read once per run."""
    if _SAVED_BY: return _SAVED_BY[0]
    by = {}
    _SAVED_BY.append(by)
    for f in CACHE_US.glob('US-*.json.gz'):
        if f.name.startswith('prev-'): continue
        try:
            with gzip.open(f, 'rt', encoding='utf-8') as fh:
                blob = json.load(fh)
                for r in blob.get('recs') or []:
                    if not r.get('_r'): continue
                    oid = r.get('OBJECTID')
                    use, why = pad_use(r) if isinstance(oid, int) else fws_use(r) if str(oid).startswith('fws') else (True, None)
                    if use:
                        by[oid] = r['_r']; SAVED_STR[str(oid)] = r['_r']; SAVED_DATE[str(oid)] = r.get('rd') or blob.get('saved') or ''
                        SAVED_NAME[str(oid)] = r.get('Unit_Nm') or ''
                    else: SAVED_LEFT[oid] = why; SAVED_LEFT[str(oid)] = why
        except Exception: pass  # noqa: BLE001
    return by


# Nov 9 evening (Brandon t909u: 'every live download gets saved, so the next run has it'): the 2-fer bot's OWN saved copy of the
# outlines it had to read live (parks whose records are in no key copy). One file per area, kept on KPC-Data's fers-cache release
# (the workflow downloads it before the run and uploads it after a good save). {ref: {ids, g (rings per record), rd (read date)}}.
# Rolling refresh (t909u, 'once a month'): an entry older than KPC_FERS_REFRESH_DAYS (30) is read live again, at most
# KPC_FERS_REFRESH_SHARE (a quarter) of the entries per run, oldest first, so no server is asked for everything in one run.
LIVE_FILE = None
LIVE = {}
REFRESH_DAYS = int(os.environ.get('KPC_FERS_REFRESH_DAYS') or 30)
REFRESH_SHARE = float(os.environ.get('KPC_FERS_REFRESH_SHARE') or .25)


def live_load(area):
    global LIVE_FILE, LIVE
    LIVE_FILE = pathlib.Path(os.environ.get('KPC_FERS_LIVE_DIR') or OUT) / f'saved-live-{area}.json.gz'
    LIVE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with gzip.open(LIVE_FILE, 'rt', encoding='utf-8') as fh: LIVE = json.load(fh).get('parks') or {}
    except Exception: LIVE = {}  # noqa: BLE001
    return LIVE


def live_due(today):
    """The saved-live entries due for their monthly re-read this run (oldest first, at most a share of them)."""
    import datetime as _dt
    t = _dt.date.fromisoformat(today)
    old = sorted((v.get('rd') or '', r) for r, v in LIVE.items() if (v.get('rd') or '') and (t - _dt.date.fromisoformat(v['rd'][:10])).days >= REFRESH_DAYS)
    return {r for _, r in old[:max(1, int(len(LIVE) * REFRESH_SHARE))]} if old else set()


def live_save(today):
    if LIVE_FILE is None: return
    with gzip.open(LIVE_FILE, 'wt', encoding='utf-8') as fh:
        json.dump({'about': "2-fer bot's own saved outlines (read live once, then reused; re-read about once a month in slices)", 'date': today, 'parks': LIVE}, fh, separators=(',', ':'))


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


KYF = {'bdbnf': 'ky-dbnf.geojson', 'bstate': 'ky-state-parks.geojson', 'bwma': 'ky-hunting-areas.geojson', 'bsnp': 'ky-nature-preserves.geojson', 'bsna': 'ky-natural-areas.geojson',
       'bnps': 'ky-nps.geojson', 'bwild': 'ky-wild-rivers.geojson', 'bwilder': 'ky-wilderness.geojson', 'bfws': 'ky-fws.geojson', 'bpad': 'ky-padus-parks.geojson'}
KYIDX = {}
# Oct 27 8:10 AM (HQ, chat 8 re-check fix 5): passes 2-3 read Kentucky's outlines FRESH from the agencies' live layers (the same
# ones Map Rep reads), so a row is no longer 'saved outline only'. A tract whose live read fails keeps the file copy (flagged).
KYGIS = 'https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/'
KYLIVE = {'bwma': (KYGIS + 'Ky_Public_Hunting_Areas_WGS84WM/MapServer/1/query', 'AREANAME'),
          'bstate': (KYGIS + 'Ky_State_Parks_Features_WGS84WM/MapServer/8/query', 'PUBLIC_NAM'),
          'bsnp': (KYGIS + 'Ky_KNP_State_Nature_Preserves_WGS84WM/MapServer/0/query', 'MANAME'),
          'bsna': (KYGIS + 'Ky_KNP_Natural_Areas_WGS84WM/MapServer/0/query', 'MANAME'),
          'bnps': ('https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/2/query', 'UNIT_NAME'),
          'bfws': (FWS, 'ORGNAME'),
          'bwilder': ('https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_Wilderness_02/MapServer/0/query', 'WILDERNESSNAME'),
          # Oct 27 (Brandon found it): Kentucky's open-data 'Kentucky Wild Rivers (Corridors)' (boundaries as described in KRS 146.2XX),
          # opengisdata.ky.gov item efefe7342aa4460aaf8697e17deb4146: the service address and name field are looked up at run time
          'bwild': ('item:efefe7342aa4460aaf8697e17deb4146', '?')}
KYKIND = re.compile(r'\b(state resort park|state park|state historic site|state nature preserve|state natural area|wildlife management area|wma|'
                    r'national wild and scenic river|wild river|scenic river|wild and scenic river|national recreation area|wilderness)\b', re.I)


def _kcore(x): return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', KYKIND.sub(' ', str(x or '').lower().replace('-', ' '))).split())


RESOLVED_KY = {}


def ky_resolve(src):
    """An ArcGIS Online / Hub item id -> its layer query url + name field (asked once per run)."""
    url, fld = KYLIVE[src]
    if not url.startswith('item:'): return url, fld
    if src in RESOLVED_KY: return RESOLVED_KY[src]
    it = url[5:]
    j = get(f'https://www.arcgis.com/sharing/rest/content/items/{it}', {'f': 'json'})
    u = str(j.get('url') or '').rstrip('/')
    if not re.search(r'/\d+$', u): u += '/0'
    lj = get(u, {'f': 'json'})
    names = [x['name'] for x in lj.get('fields') or [] if x.get('type') == 'esriFieldTypeString']
    nf = next((n for n in names if re.fullmatch(r'(river_?)?name|name_?1?|wr_?name|label', n, re.I)), None) or next((n for n in names if re.search(r'name', n, re.I)), names[0] if names else 'NAME')
    RESOLVED_KY[src] = (u + '/query', nf)
    KYSRC[src] = f'{u} (item {it}, read {time.strftime("%Y-%m-%d")})'
    return RESOLVED_KY[src]


KYSRC = {}
FRESHKY = {}   # ref -> {'live', 'file'}: where its tracts came from this run
KYFRESH = {}   # (src, name) -> groups read live this run (or [] when the live read failed)


def ky_live(src, nm):
    k = (src, nm)
    if k in KYFRESH: return KYFRESH[k]
    gs = []
    try:
        if saved_only_host([KYLIVE[src][0]]): KYFRESH[k] = []; return []   # owner rule, 2026-11-10: the Kentucky file copy is used
        url, fld = ky_resolve(src)
        if saved_only_host([url]): KYFRESH[k] = []; return []
        q = lambda w: get(url, {'where': w, 'outFields': fld, 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': DET, 'geometryPrecision': PREC, 'f': 'json'})
        esc = lambda x: x.upper().replace(chr(39), chr(39) * 2)
        fs = q(f"UPPER({fld}) = '{esc(nm)}'").get('features') or []
        if not fs and _kcore(nm):
            # Oct 27: the live layers often name the place without its kind ('Carter Caves', 'Columbus-Belmont', 'Bat Cave'):
            # same name once the kind words are dropped
            w = max(_kcore(nm).split(), key=len)
            fs = [ft for ft in q(f"UPPER({fld}) LIKE '%{esc(w)}%'").get('features') or [] if _kcore((ft.get('attributes') or {}).get(fld)) == _kcore(nm)]
        for ft in fs:
            g = esri_rings(ft.get('geometry'))
            if g: gs.append(g)
    except Exception as e: LOG.append(f'Kentucky live {src} {nm[:30]}: {str(e)[:50]}')  # noqa: BLE001
    KYFRESH[k] = gs
    return gs


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
                    polys = []
                    try:
                        for fs in read_pages(lambda off: get(PADUS, {'where': f"State_Nm='KY' AND Category='Fee' AND Unit_Nm LIKE '{nm}%'", 'outFields': 'OBJECTID',
                                                                     'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': DET, 'geometryPrecision': PREC,
                                                                     'resultOffset': off, 'resultRecordCount': 500, 'f': 'json'})):
                            polys += [esri_rings(f.get('geometry')) for f in fs if esri_rings(f.get('geometry'))]
                    except Exception as e:  # noqa: BLE001
                        polys = []; LOG.append(f'PAD-US {nm}: {str(e)[:60]} (not read: half a park is not the park)')   # never a partial read
                    KYIDX[('padus', nm)] = polys
                if KYIDX[('padus', nm)]: gs += KYIDX[('padus', nm)]
                else: bad.add(ref)
                continue
            if PASS >= 2 and src in KYLIVE:
                live = ky_live(src, nm)
                if live:
                    gs += live; FRESHKY.setdefault(ref, set()).add('live'); continue
                FRESHKY.setdefault(ref, set()).add('file')
            elif src != 'bdbnf': FRESHKY.setdefault(ref, set()).add('file')
            else: FRESHKY.setdefault(ref, set()).add('live')   # its land = the live Forest Service ownership map
            near = (lambda pp: True) if src == 'bdbnf' else (lambda pp: any(abs(q[0] - lo) < .6 and abs(q[1] - la) < .6 for q in pp[0][::max(1, len(pp[0]) // 20)]))   # the forest spans 3 degrees
            polys = [pp for pp in KYIDX.get((src, nm), []) if pp and pp[0] and near(pp)]
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
LOWCONF = set()
try: LOWCONF = {x[0] for x in json.load(open('data/boundary-score.json')).get('low_busiest_first') or []}
except Exception: pass  # noqa: BLE001
RIVER_PAD = 150.0          # pass 1 screen for line-only rivers (no water areas yet): a river up to 300 m wide
CURG = {}                  # the outlines in use (find_spots sets it)
OWNED = {}                 # ref -> 'usfs' = agency-land park: only Forest Service-owned land counts
AGENCY_LAND = re.compile(r'national forests?\b|national grasslands?\b', re.I)
FSBO = KO.FSBO
ACC = {}                   # ref -> notes ('restricted access (PAD-US)')
LEFT = {}                  # ref -> records left out and why (easement, closed, proclamation…)
MAPDATE = {}               # ref -> where / when its outline came from
_PINS = None
FOUNDBYNAME = set()        # Oct 30: parks whose record was found again by NAME (the server re-numbered its ids)
WHEN, READ = {}, {}        # B2 (Oct 30): (layer url, object id) -> when read; ref -> the oldest read among its records


# Oct 27 (Fable's boundary review #1): the ownership maps are read in ONE place, kpc_owned.py, shared with the website's
# owned-land files (chat 8's pre-flight fixes 2-4 + PF-1/2/3: Forest Service = Basic Ownership; BLM planning areas = BLM surface
# management; Park Service, Corps, FWS approved boundaries = PAD-US Fee records of that agency; Michigan project lines = state fee)
OWNER_KEY, OWNMAP = KO.OWNER_KEY, KO.OWNMAP
# Nov 9 (Brandon 9:37 AM CST, KISS: "ownership if it say national forest it is owned by federal government etc.. kiss method ...lets
# not over think this.."): an agency park's owner is the agency from its own record; no owned-land masks, no live ownership calls.
# (The live BLM SMA query that failed with HTTP 400 in run 42594981324 is no longer made by the 2-fer run.)
def fs_owned(box): return None
def owned_land(kind, box): return None


def pmask(F, r, G):
    """The park's land in raster F: its official outline (Nov 9, Brandon 9:37 AM CST: no owned-land mask; the owner is the agency)."""
    return F.area(G[r])


SOFT = {'nps', 'usace', 'fws', 'state'}
# Brandon Oct 28 8:35 PM: pairs he activates in person = PERMANENT KNOWN ANSWERS (the whole overlap of the two official
# boundaries, river included; no mask, no ownership argument)
KNOWN_LIVE = {('US-0050', 'US-10105'): 'Mammoth Cave x Green River Wild River: Brandon activates it in person (ruling Oct 28 8:35 PM)'}


OWNED_FAIL = set()
CA_WATER = None     # Fable #9: an official Canadian water service (NRCan National Hydro Network) once the probe finds one
CACHE_TILES = 600   # Oct 27 (Fable #8): tiles kept in memory before the far ones are dropped
# Nov 4 PM fix bundle item 4 (Brandon's yes relayed via Super Head Bot 4:53 PM CST; the Southeast worker was shut down near
# 12.5 GB in pass 5's water re-check of 365 spots): pass 5 never dropped a cached tile, so every saved water tile of the area
# (3 m detail) stayed in memory. Pass 5 now streams the spots tile by tile (sorted by place) and drops the far tiles before each
# spot like pass 3 does; the caches are ALSO dropped when the process passes KPC_FERS_MEM_MB (default 5000 MB; a GitHub runner
# has 16 GB). Only memory changes: the same tiles are read again from the saved copy (bundle/water) when needed, so the answers
# do not change.
MEM_MB = float(os.environ.get('KPC_FERS_MEM_MB') or 5000)


def rss_mb():
    """This process's memory now (Linux /proc), in MB; 0 when it cannot be read."""
    try: return int(open('/proc/self/statm').read().split()[1]) * os.sysconf('SC_PAGE_SIZE') / 1048576.0
    except Exception: return 0.0  # noqa: BLE001


def evict(box):
    """Keep the cached ownership / water tiles near box (1 degree around); drop the rest when the caches grow big, or when
    the process passes MEM_MB (then only the tiles of box itself are kept)."""
    if not box: return
    n = KO.tiles_cached() + len(NHDC)
    big = MEM_MB > 0 and rss_mb() > MEM_MB
    if n <= CACHE_TILES and not big: return
    m = 0.0 if big else 1.0
    near = lambda x0, y0, sz: inter(box, [x0 * sz, y0 * sz, (x0 + 1) * sz, (y0 + 1) * sz], m) is not None
    KO.evict(near)
    for k in [k for k in NHDC if not near(k[0], k[1], .1)]: del NHDC[k]   # keys (i, j) and (i, j, 'd')
    if big:
        import gc; gc.collect(); EVICT_N['memory'] += 1


EVICT_N = {'memory': 0}


NHD = 'https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer'
NHDL = {}
NHDC = {}


NHD_DOWN = {'until': 0.0, 'fails': 0, 'pauses': 0}
# Oct 28 (HQ 12:21 AM): the water check must not depend on USGS being up that night. Every 0.1-degree water tile read live is
# also kept in WATER_STORE (bundle/water: travels fetcher -> worker in the bundle and is kept between nights as the release
# asset water-<tag>.tar.gz). When the live map does not answer, the last good copy is used and the row says so with its date
# (rule 13: map_dates 'USGS water'). Live map AND saved copy both missing = None = NOT SURE, as before.
WATER_STORE = os.environ.get('WATER_STORE') or ''
WATER_MARK = []                     # dates of saved copies used since the caller last cleared it
WATER_N = {'live': 0, 'saved': 0, 'missing': 0}
WATER_RETRY = {'budget': float(os.environ.get('WATER_RETRY_S') or 1500), 'spent': 0.0, 'tries': 0, 'won': 0}


def _wpath(i, jt): return pathlib.Path(WATER_STORE) / f'{i}_{jt}.json.gz'


def _wsave(i, jt, feats):
    if not WATER_STORE: return
    try:
        p = _wpath(i, jt); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(gzip.compress(json.dumps({'d': time.strftime('%Y-%m-%d', time.gmtime()), 'f': feats}, separators=(',', ':')).encode(), 6))
    except Exception: pass  # noqa: BLE001


def _wload(i, jt):
    if not WATER_STORE: return None
    try: return json.loads(gzip.decompress(_wpath(i, jt).read_bytes()))
    except Exception: return None  # noqa: BLE001


def _wlive(i, jt):
    """One tile from the live USGS map: [[layer, rings], ...] (both layers, so a later rivers-only ask can use it too)."""
    if not NHDL:
        for L in get(NHD, {'f': 'json'}, tries=1, timeout=30).get('layers') or []:
            nm = L.get('name', '').lower()
            if nm == 'nhdarea': NHDL['area'] = L['id']
            if nm == 'nhdwaterbody': NHDL['wb'] = L['id']
    tb = [i * .1, jt * .1, (i + 1) * .1, (jt + 1) * .1]
    got = []
    for lay, where in (('area', 'FType = 460'), ('wb', 'FType IN (390, 436, 493)')):
        if lay not in NHDL: continue
        j = get(f'{NHD}/{NHDL[lay]}/query', {'where': where, 'geometry': ','.join(map(str, tb)), 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326,
                                             'spatialRel': 'esriSpatialRelIntersects', 'outFields': 'FType', 'returnGeometry': 'true', 'outSR': 4326,
                                             'maxAllowableOffset': min(DET, 0.00003), 'geometryPrecision': max(PREC, 6), 'f': 'json'}, tries=1, timeout=30)   # Oct 31 (Fable #21): a SAVED water tile is reused by pass 3's 100-ft-from-bank test: always ~3 m
        got += [[lay, esri_rings(f.get('geometry'))] for f in j.get('features') or [] if esri_rings(f.get('geometry'))]
    if len(NHDL) < 2: raise RuntimeError('USGS water layers not listed')
    return got


NHD2 = 'https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer'   # chat 8 KPC_RiverBackup_desk.md: 'a second USGS door'
NHD2L = {}


def _wlive2(i, jt):
    """Oct 28 (chat 8's backup list, Brandon 1:30 PM): the SAME NHD high-resolution water (StreamRiver areas + lakes / reservoirs /
    estuaries, the same feature codes) from USGS's older NHD map service, when the NHDPlus HR service does not answer. NOT used:
    EPA NHDPlus V2.1 (its polygon layer has lakes but no river areas: a river would read as land) and the Corps IENC charts
    (navigable rivers only): both would let a wrong 'land' answer through, so a row with neither USGS door answering stays NOT SURE."""
    if not NHD2L:
        for L in get(NHD2, {'f': 'json'}, tries=2, timeout=60).get('layers') or []:
            nm = L.get('name', '').lower()
            if 'area' in nm and 'large' in nm: NHD2L['area'] = L['id']
            if 'waterbod' in nm and 'large' in nm: NHD2L['wb'] = L['id']
    if len(NHD2L) < 2: raise RuntimeError('second USGS water door: layers not listed')
    tb = [i * .1, jt * .1, (i + 1) * .1, (jt + 1) * .1]
    got = []
    for lay, where in (('area', 'FType = 460'), ('wb', 'FType IN (390, 436, 493)')):
        j = get(f'{NHD2}/{NHD2L[lay]}/query', {'where': where, 'geometry': ','.join(map(str, tb)), 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326,
                                               'spatialRel': 'esriSpatialRelIntersects', 'outFields': 'FType', 'returnGeometry': 'true', 'outSR': 4326,
                                               'maxAllowableOffset': DET, 'geometryPrecision': PREC, 'f': 'json'}, tries=2, timeout=90)
        if 'error' in j: raise RuntimeError(str(j['error'])[:80])
        got += [[lay, esri_rings(f.get('geometry'))] for f in j.get('features') or [] if esri_rings(f.get('geometry'))]
    return got


def nhd_water(box, rivers_only=False, live=True):
    """USGS NHD High Resolution water areas in box (rivers = NHDArea StreamRiver; + lakes, reservoirs, estuaries).
    Oct 28 6:57 PM (HQ, Brandon: 'if we have the offline files WHY are we still trying to pull the water live, it keeps breaking
    the line'): (1) the SAVED tile (a live read saved earlier, or the USGS bulk files cut by kpc_water_bulk.py, fetched up front),
    (2) ONLY for a tile neither has: ONE short live try (30 s, no retry loop, no waiting; after 3 failures the live map is not
    asked again this run), (3) else None = NOT SURE (a map that did not answer is never 'no water')."""
    out = []
    for i in range(int(math.floor(box[0] / .1)), int(math.floor(box[2] / .1)) + 1):
        for jt in range(int(math.floor(box[1] / .1)), int(math.floor(box[3] / .1)) + 1):
            k = (i, jt)
            if k not in NHDC:
                sv = _wload(i, jt)
                if sv is not None:
                    NHDC[k] = sv['f']; NHDC[k + ('d',)] = sv.get('d') or ''
                    WATER_N['bulk file' if str(sv.get('d', '')).startswith('USGS NHDPlus HR file') else 'saved'] = WATER_N.get('bulk file' if str(sv.get('d', '')).startswith('USGS NHDPlus HR file') else 'saved', 0) + 1
                else:
                    feats = None
                    if live and NHD_DOWN['fails'] < 3:   # Canada (live=False): only the saved NHN tiles, never the USGS map
                        try: feats = _wlive(i, jt); WATER_N['live'] += 1; _wsave(i, jt, feats)
                        except Exception as e:  # noqa: BLE001
                            NHD_DOWN['fails'] += 1; LOG.append(f'NHD water (one try): {str(e)[:70]}')
                    if feats is None:
                        WATER_N['missing'] += 1
                        return None
                    NHDC[k] = feats
            if NHDC.get(k + ('d',)): WATER_MARK.append(NHDC[k + ('d',)])
            out += [g for lay, g in NHDC[k] if not (rivers_only and lay == 'wb')]
    return out


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


def pad_closed(box):
    j = get(PADUS, {'where': "Pub_Access = 'XA' AND Category IN ('Fee','Designation')", 'geometry': ','.join(map(str, box)), 'geometryType': 'esriGeometryEnvelope',
                    'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects', 'outFields': 'Unit_Nm', 'returnGeometry': 'true', 'outSR': 4326,
                    'maxAllowableOffset': DET, 'geometryPrecision': PREC, 'f': 'json'})
    return [esri_rings(f.get('geometry')) for f in j.get('features') or [] if esri_rings(f.get('geometry'))]


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
        try:   # Oct 28: hand finds where KDFWR's page names no owner (Boatwright: the Office of Nature Preserves page says KDFWR)
            for n, v in json.load(open('data/ky-wma-owners-hand.json'))['wmas'].items():
                if not KYOWN.get(low(n)): KYOWN[low(n)] = {'State': 'STATE', 'Local': 'STATE', 'Corps': 'FED:USACE', 'Federal': 'FED', 'Private': 'PRIVATE', 'University': 'UNIVERSITY'}.get(v.get('type'), '')
        except Exception: pass  # noqa: BLE001
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


# Nov 9 (Brandon 9:37 AM CST, KISS): the owner straight from the park's own name / agency when its record does not say
NAME_OWNER = [(r'parks canada|national park of canada|national historic site of canada|national marine conservation area', 'FED:CANADA'), (r'national (forest|grassland)s?\b', 'FED:USFS'), (r'\bblm\b|bureau of land management|national conservation area', 'FED:BLM'),
              (r'national (park|seashore|lakeshore|battlefield|historic(al)? (site|park)|preserve|memorial|military park|river and recreation area)\b', 'FED:NPS'),
              (r'national wildlife refuge|\bnwr\b|national fish hatchery|waterfowl production area', 'FED:FWS'), (r'corps of engineers|\busace\b', 'FED:USACE'),
              (r'\btva\b|tennessee valley authority', 'FED:TVA'),
              (r'state (park|forest|recreation area|natural area|nature preserve|historic site|wildlife area|game land|beach|seashore)|wildlife management area|\bwma\b|'
               r'state fish and wildlife|provincial (park|forest|recreation area)|ecological reserve|conservation reserve|wildlife (refuge|area) \(state\)', 'STATE'),
              (r'\b(county|city|municipal|metro|town|township|village|borough) (park|forest|preserve|recreation area)\b|regional park|conservation authority', 'LOCAL')]


def owner_from_name(*names):
    t = ' '.join(str(x or '') for x in names)
    for rx, k in NAME_OWNER:
        if re.search(rx, t, re.I): return k
    return owner_of_text(t)


def park_owner(ref, parks):
    """'' = a designation / management record (layers on someone else's land); '?' = not known; else the owner key."""
    if not (parks.get(ref) or {}).get('ids'): return ''   # a line park (trail / water trail): a designation along the line
    if REGION == 'ky': return ky_owner(ref, parks)
    if ref in OWNED: return OWNER_KEY.get(OWNED[ref], 'FED:USFS')
    p = parks.get(ref) or {}
    if p.get('st', '').startswith('CA-'):
        o = OWN_CA.get(ref, '?')
    else:
        fee, des = OWN.get(ref, (set(), False))
        o = (sorted(fee)[0] if len(fee) == 1 else '?') if fee else ('' if des else '?')
    if o == 'UNK': o = '?'   # PAD-US 'unknown' owner = not known
    if o in ('', '?'):   # Nov 9 (KISS): the park's own name / its records' names say the agency
        o = owner_from_name((PINS.get(ref) or [''])[0], *((p.get('names') or {}).values())) or o
    return o


OWN_CA = {}


def ownership_step(s, parks, PIN):
    """Brandon Oct 28 8:35 PM, THE SIMPLE TEST (step 2 of 'the job in two steps', mapping.md): the patch already sits inside two
    OFFICIAL boundaries (step 1, the keys, settled each park's boundary), so the line only asks: is the ground PUBLIC?
    Every owner public (federal, state, county, city, TVA, Corps...) = 'ok', the whole patch, however many owners. PRIVATE
    pieces are named ('private land', cut out, count only for their own park); a piece with no owner on any map = only that
    piece is not sure, the public rest counts. Owners are INFO ('ground'), never the verdict. ('ok' | 'drop' | 'not sure', why)."""
    refs = s['refs']
    owners = {r: park_owner(r, parks) for r in refs}
    # Brandon Oct 27 5:21 AM (rule 14 + boundary B-G2): a park on private land (lease / agreement) counts only for its own number
    priv = [r for r, o in owners.items() if o == 'PRIVATE']
    if priv: return 'drop', 'private land (leased / open by agreement) counts only for its own park number: ' + ', '.join(PIN.get(r, [r])[0] for r in priv)
    real = {r: o for r, o in owners.items() if o not in ('', '?')}
    if REGION == 'world':
        if real and len(set(real.values())) <= 1 and '?' not in owners.values(): return 'ok', 'one owner (or designations on it): layered'
        return 'not sure', ('owners differ' if real else 'no park here owns land (designations only)') + '; no land register read for this country yet'
    PUB = ('FED', 'STATE', 'STAT', 'LOCAL', 'LOC', 'DIST', 'TVA', 'JNT')
    # Nov 9 (Brandon 9:37 AM CST, KISS): owners come from the parks' own records / agency names only: no ownership map, no live call
    if real and '?' not in owners.values() and all(str(o).split(':')[0] in PUB for o in real.values()):
        # every park here is held by a known PUBLIC owner (one or several; a trail / designation layers on it): public ground
        s['ground'] = sorted({owner_word(o) for o in real.values()})
        if len(set(real.values())) > 1: s['mixed_owners'] = sorted(set(real.values()))
        s['owner_src'] = "the parks' own records / agency names (Brandon Nov 9, 9:37 AM CST)"
        return 'ok', 'public land (' + ' + '.join(s['ground']) + ')'
    # Official agency outlines already show government or public land, so a blank owner field
    # is not a hold when every half comes from such a layer. Point-circle and approximate
    # pairs stay flagged. A blank owner whose outline is not from an official agency layer
    # still cannot be a candidate.
    if official_agency_outlines(refs):
        known = sorted({owner_word(o) for o in real.values()}) if real else []
        s['ground'] = known or ['government or public land']
        s['owner_src'] = 'official agency outline (government / public land)'
        if len(set(real.values())) > 1: s['mixed_owners'] = sorted(set(real.values()))
        return 'ok', 'public land (' + ' + '.join(s['ground']) + ')'
    blank = [PIN.get(r, [r])[0] for r, o in owners.items() if o == '?']
    if blank: return 'not sure', 'no owner on the park record or in its name for ' + ', '.join(blank) + ' (a person adds it)'
    if not real: return 'not sure', 'no park here owns land (designations only): no owner on the records'
    return 'not sure', 'an owner here is not a public owner (' + ', '.join(sorted({owner_word(o) for o in real.values()})) + ')'


OWNWORD = {'STAT': 'state', 'STATE': 'state', 'LOC': 'local', 'LOCAL': 'local', 'PVT': 'private', 'PRIVATE': 'private', 'TRIB': 'tribal',
           'TRIBAL': 'tribal', 'USFS': 'Forest Service', 'NPS': 'Park Service', 'FWS': 'Fish and Wildlife Service', 'USACE': 'Corps of Engineers',
           'BLM': 'BLM', 'TVA': 'TVA', 'DOD': 'military', 'FED': 'federal', 'DIST': 'special district', 'UNIVERSITY': 'university'}


def owner_word(k):
    """Oct 27 (chat 8 Ohio note 2: 'stat land'): an owner key in plain words."""
    k = str(k or '').split(':')[-1].upper()
    return OWNWORD.get(k, k.lower())


def patch_points(s):
    """[(lon, lat)] where the owner is read: the spot's middle + the farthest point inside its shape in each quarter (NE, NW,
    SE, SW), at least 12.5 yards in from its edge; line spots and tiny patches = the middle only."""
    la, lo = s['center']
    out = [(lo, la)]
    shape = s.get('shape')
    if s.get('kind') != 'area' or not shape or len(shape) < 3: return out
    try:
        b = bbox_lines([shape]); cell = 5.0
        F = Frame(b, cell, 20)
        while F.W * F.H > 4_000_000: cell *= 1.5; F = Frame(b, cell, 20)
        m = F.area([[shape]])
        dd = dt(m) * cell
        rows, cols = np.nonzero(dd >= TIGHT_SHRINK + cell * .5)
        if not len(rows): rows, cols = np.nonzero(dd >= cell * 1.5)
        if not len(rows): return out
        c0, r0 = F.px([[lo, la]])[0]
        dx, dy = cols - c0, r0 - rows
        for qx, qy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            sel = (dx * qx > 0) & (dy * qy > 0)
            if not sel.any(): continue
            i = np.argmax(np.where(sel, dx * dx + dy * dy, -1))
            out.append(tuple(F.ll(int(cols[i]), int(rows[i]))))
    except Exception as e: LOG.append(f'patch points: {str(e)[:60]}')  # noqa: BLE001
    return out[:5]


# Kentucky rulings (Brandon + HQ Oct 27; chat 8's KPC_KY2fer_VERDICT_desk.md): decided pairs, applied after the tests
KY_DROP = {('US-1277', 'US-4484'): 'Cumberland Falls is state land beside Forest Service land (ruling Oct 27)',
           ('US-1286', 'US-4484'): 'Natural Bridge is state land beside Forest Service land (ruling Oct 27)',
           ('US-0686', 'US-4484'): 'Big South Fork is Park Service land beside Forest Service land (ruling Oct 27)',
           ('US-3799', 'US-4484'): 'Burchell-Beech is KDFWR-owned (ruling Oct 27)',
           ('US-4484', 'US-7964'): 'W.H. Martin is state nature preserve land (ruling Oct 27)',
           ('US-12083', 'US-4484'): 'University of the Cumberlands WMA is private (ruling Oct 27)'}
PARTIAL = {'US-10102': 'official line = the open 44 miles only (Breaks to US 119): pairs on the planned stretch stay NOT SURE'}
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


def same_part(gs, a, b):
    """Fable Oct 29: ONE polygon part (one outer ring) holds both pins (lon, lat). PAD-US stores same-named far-apart places as one
    multipart record (Lost Nation, Robert Moses), and each record is one group here, so a test per group or per record passes for
    two different places; a test per RING does not."""
    def _in(ring, lon, lat): return len(ring) > 2 and cv2.pointPolygonTest(np.asarray(ring, np.float32)[:, :2].reshape(-1, 1, 2), (float(lon), float(lat)), False) >= 0
    return any(_in(r, *a) and _in(r, *b) for g in gs for r in g)


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
        if not want(v[5]) or ref in RET or (ref in G) or (ref in LN and ref not in PARTIAL): continue
        nm, la, lo = v[0], v[1], v[2]
        if la is None or lo is None: continue   # Nov 9 PM: a bad POTA pin (0,0) is never placed anywhere
        ins = [r for r in grid.get((int(lo // .5), int(la // .5)), []) if r != ref and boxes[r][0] <= lo <= boxes[r][2] and boxes[r][1] <= la <= boxes[r][3] and pip_groups(G[r], lo, la)]
        if ins or ref in KY_NOT_SURE or ref in PARTIAL:
            why = PARTIAL.get(ref) if ref in LN else KY_NOT_SURE.get(ref) or ('line park: no official trail / river line yet' if re.search(r'\btrail\b|\briver\b|parkway', nm, re.I) and ref not in SKIPWHY else skip_why.get(ref, 'no official boundary'))
            out.append({'ref': ref, 'name': nm, 'st': v[5], 'why': why,
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
        t = np.zeros_like(m)
        W16, H16 = self.W * 16, self.H * 16
        for g in gs:
            gm = None
            for ring in g:
                if not len(ring): continue
                r = np.round(self.px(ring) * 16).astype(np.int32)
                # Oct 28 (speed A3): a ring wholly outside the raster paints nothing: skipped; one scratch buffer instead of a new
                # one per ring (cleared before each use): the same fillPoly, the same XOR, pixel for pixel
                if r[:, 0].max() < -48 or r[:, 0].min() > W16 + 48 or r[:, 1].max() < -48 or r[:, 1].min() > H16 + 48: continue
                t.fill(0)
                cv2.fillPoly(t, [r], 1, lineType=cv2.LINE_8, shift=4)
                if gm is None: gm = t.copy()
                else: gm ^= t
            if gm is not None: m |= gm
        return m

    def _ring_boxes(self, gs):
        """Per record, its rings as 1/16-pixel points with each ring's pixel box on this frame (clipped to the frame)."""
        out = []
        for g in gs:
            rs = []
            for ring in g:
                if not len(ring): continue
                r = np.round(self.px(ring) * 16).astype(np.int32)
                if r[:, 0].max() < -48 or r[:, 0].min() > self.W * 16 + 48 or r[:, 1].max() < -48 or r[:, 1].min() > self.H * 16 + 48: rs.append((r, None)); continue
                x0 = max(0, (int(r[:, 0].min()) >> 4) - 2); x1 = min(self.W, (int(r[:, 0].max()) >> 4) + 3)
                y0 = max(0, (int(r[:, 1].min()) >> 4) - 2); y1 = min(self.H, (int(r[:, 1].max()) >> 4) + 3)
                rs.append((r, (x0, y0, x1, y1) if x0 < x1 and y0 < y1 else None))
            out.append(rs)
        return out

    def area_in(self, gs, w):
        """Frame.area(gs) cut to window w, without drawing the whole frame: each ring filled in its own box (fillPoly gives the
        same pixels for a polygon moved by whole pixels; the picture's real edges stay where they are), XOR per record as in area()."""
        m = np.zeros((w.H, w.W), np.uint8)
        for rs in self._ring_boxes(gs):
            gm = None; any_ring = False
            for r, bx in rs:
                any_ring = True
                if bx is None: continue
                x0, y0, x1, y1 = bx
                a0, b0, a1, b1 = max(x0, w.c0), max(y0, w.r0), min(x1, w.c0 + w.W), min(y1, w.r0 + w.H)
                if a0 >= a1 or b0 >= b1: continue   # this ring paints nothing in the window (XOR with zeros there)
                t = np.zeros((y1 - y0, x1 - x0), np.uint8)
                cv2.fillPoly(t, [r], 1, lineType=cv2.LINE_8, shift=4, offset=(-x0 * 16, -y0 * 16))
                if gm is None: gm = np.zeros_like(m)
                gm[b0 - w.r0:b1 - w.r0, a0 - w.c0:a1 - w.c0] ^= t[b0 - y0:b1 - y0, a0 - x0:a1 - x0]
            if gm is not None: m |= gm
        return m

    def any_in(self, gs):
        """Would area(gs) paint any pixel? (the same rings, the same test: True as soon as one record paints one)"""
        for rs in self._ring_boxes(gs):
            boxes = [(r, bx) for r, bx in rs if bx is not None]
            if not boxes: continue
            x0 = min(b[0] for _, b in boxes); y0 = min(b[1] for _, b in boxes); x1 = max(b[2] for _, b in boxes); y1 = max(b[3] for _, b in boxes)
            if (x1 - x0) * (y1 - y0) > 50_000_000: return True   # a frame-sized record: it paints (only the ownership-map call depends on this)
            gm = np.zeros((y1 - y0, x1 - x0), np.uint8)
            for r, (a0, b0, a1, b1) in boxes:
                t = np.zeros((b1 - b0, a1 - a0), np.uint8)
                cv2.fillPoly(t, [r], 1, lineType=cv2.LINE_8, shift=4, offset=(-a0 * 16, -b0 * 16))
                gm[b0 - y0:b1 - y0, a0 - x0:a1 - x0] ^= t
            if gm.any(): return True
        return False

    def window(self, P, pad):
        """A sub-raster of THIS frame's pixel grid around pixel points P (+ pad pixels), clipped to the frame."""
        c0 = max(0, int(math.floor(P[:, 0].min())) - pad); r0 = max(0, int(math.floor(P[:, 1].min())) - pad)
        c1 = min(self.W, int(math.ceil(P[:, 0].max())) + pad + 1); r1 = min(self.H, int(math.ceil(P[:, 1].max())) + pad + 1)
        return Win(self, c0, r0, max(1, c1 - c0), max(1, r1 - r0))

    def lines(self, ls, width_m):
        m = np.zeros((self.H, self.W), np.uint8)
        th = max(1, int(round(2 * width_m / self.cell)))
        ls = [l for l in ls if len(l)]
        if not ls: return m
        # Oct 28 (speed A2): every segment through ONE px() call, then one polylines call (the same arithmetic on the same points,
        # drawn the same way: identical to the one-segment-at-a-time loop); segments far outside the raster are left out
        # (a line more than the pen's width outside the picture paints nothing)
        n = np.fromiter((len(l) for l in ls), dtype=np.int64, count=len(ls))
        P = np.round(self.px(np.concatenate([np.asarray(l, dtype=np.float64)[:, :2] for l in ls])) * 16).astype(np.int32)
        parts = np.split(P, np.cumsum(n)[:-1])
        pad = (th + 3) * 16
        keep = [p for p in parts if p[:, 0].max() >= -pad and p[:, 0].min() <= self.W * 16 + pad and p[:, 1].max() >= -pad and p[:, 1].min() <= self.H * 16 + pad]
        if keep: cv2.polylines(m, keep, False, 1, thickness=th, lineType=cv2.LINE_8, shift=4)
        return m


class Win(Frame):
    """A window of a Frame: the parent's pixel grid shifted by whole pixels (px = parent px minus the offset, exact in floats),
    so fillPoly / polylines paint exactly the parent's pixels there."""
    def __init__(self, F, c0, r0, W, H):
        self.P, self.c0, self.r0, self.W, self.H, self.cell = F, c0, r0, W, H, F.cell
        self.lat0, self.lon0, self.kx, self.ky, self.x0, self.y1 = F.lat0, F.lon0, F.kx, F.ky, F.x0, F.y1

    def px(self, pts):
        return Frame.px(self.P, pts) - np.array([self.c0, self.r0], dtype=np.float64)

    def ll(self, c, r): return self.P.ll(c + self.c0, r + self.r0)

    def bounds(self): raise RuntimeError('Win.bounds: use the parent frame')


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
    owned = any(r in OWNED for r in refs) and tuple(sorted(refs)) not in KNOWN_LIVE
    for r in refs:
        # Oct 27 (Fable #4): the coarse look uses the WHOLE outlines, so a pair whose agency-owned land does not overlap still
        # reaches the fine look and becomes a NOT SURE row (never a silent drop)
        m = cv2.dilate(f.area(G[r]), k)
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
            m = F.area(G[r]); ovf = m if ovf is None else ovf & m
            if not ovf.any(): break
        if ovf is None or not ovf.any(): continue
        masked_out = False
        if owned:
            raw = ovf.copy()
            for r in refs:
                if r in OWNED: ovf &= pmask(F, r, G)
            if not (dt(ovf) * CELL >= TIGHT_SHRINK + CELL * .5 if PASS == 3 else ovf > 0).any():
                ovf, masked_out = raw, True   # the outlines overlap, the agency's ownership map shows none of it as its land
        dist = dt(ovf) * CELL
        # Oct 27 (Fable #5): passes 1-2 only SCREEN (any overlap pixel: a 25-yard patch can be one 20-m cell wide there);
        # pass 3 (5-m cells, finest lines) decides: a 25-yard circle must fit (rule 4 floor; the distance map runs to the
        # middle of the next cell, so half a cell more), wide_m sets the tier
        core = (dist >= TIGHT_SHRINK + CELL * .5).astype(np.uint8) if PASS == 3 else (dist > 0).astype(np.uint8)
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
            w = round(max(0.0, float(d.max()) - CELL * .5) * 2)   # the distance map counts to the next cell's middle: half a cell less = the real width
            out.append({'refs': sorted(refs), 'kind': 'area', 'center': F.ll(int(c0), int(r0))[::-1],
                        'acres': round(int(comp.sum()) * CELL * CELL / 4046.86, 1), 'wide_m': w, 'shape': shape,
                        **({'masked_out': sorted({OWNED[r] for r in refs if r in OWNED})} if masked_out else {})})
    return merge(out)


def merge(spots):
    """A spot cut by a tile edge comes back as two: one spot when their shapes touch."""
    out = []
    for s in spots:
        b = bbox_lines([s['shape']])
        t = next((o for o in out if o['refs'] == s['refs'] and o['kind'] == s['kind'] and inter(o['_b'], b, 0.0005)), None)
        if t:
            if not s.get('masked_out'): t.pop('masked_out', None)   # one piece on agency-owned land = a real spot
            if 'acres' in t or 'acres' in s: t['acres'] = round(t.get('acres', 0) + s.get('acres', 0), 1)   # line spots have none
            if s.get('wide_m', 0) > t.get('wide_m', 0): t['center'], t['wide_m'] = s['center'], s['wide_m']
            if s.get('len_m'): t['len_m'] = round(t.get('len_m', 0) + s['len_m'])
            t['_b'] = [min(t['_b'][0], b[0]), min(t['_b'][1], b[1]), max(t['_b'][2], b[2]), max(t['_b'][3], b[3])]
            t['shape'] = t['shape'] if len(t['shape']) >= len(s['shape']) else s['shape']
            for _r, _z in (s.get('route_zone') or {}).items():   # Nov 1: the water route's own zone rings add up over the tiles
                _have = t.setdefault('route_zone', {}).setdefault(_r, [])
                _have += [z for z in _z if z not in _have]
        else:
            s['_b'] = b; out.append(s)
    for o in out: o['box'] = [round(v, 5) for v in o.pop('_b')]   # the box of ALL its pieces (the shape is the biggest piece only)
    return out


SAMPLED = {}


def sample(l, step):
    """Points every `step` metres along line l. Oct 28 (speed A2): per segment the count n is found exactly as before (math), the n
    points come from numpy with the same expression in the same order ((b-a)*i/n), so every coordinate is bit for bit the same;
    the result is kept per line + step (the same trail line used to be re-sampled for every pair it is in)."""
    k = (id(l), step)
    hit = SAMPLED.get(k)
    if hit is not None and hit[0] is l: return hit[1]
    out = []
    for a, b in zip(l, l[1:]):
        kx = 111320 * math.cos(math.radians(a[1])); d = math.hypot((b[0] - a[0]) * kx, (b[1] - a[1]) * 110574)
        n = max(1, int(d // step))
        if n == 1: out.append((a[0], a[1])); continue
        i = np.arange(n, dtype=np.float64)
        xs = a[0] + (b[0] - a[0]) * i / n; ys = a[1] + (b[1] - a[1]) * i / n
        out.extend(zip(xs.tolist(), ys.tolist()))
    out.append(tuple(l[-1][:2]))
    SAMPLED[k] = (l, out)
    return out


# Oct 27 (chat 8's KPC_KY_RiverTrails_desk.md, HQ 3:21 PM; rule 5 applied right): a WATER-ROUTE national historic trail (Lewis and
# Clark; the Trail of Tears water routes on the Ohio / Mississippi / Tennessee / Cumberland; Captain John Smith Chesapeake;
# Star-Spangled Banner) follows a RIVER. Its Park Service line is ~1:100,000 and runs 0.2-3 km from the real river, so it only
# tells WHICH water the route is: the 100 ft is measured from that water's BANK (USGS NHD High Resolution) onto the other park's
# own public land. Overland stretches stay ordinary trail lines.
WATER_NHT = re.compile(r'lewis (and|&) clark|trail of tears|captain john smith|star.spangled banner', re.I)
ROUTE_KM = 3.0          # water within this distance of the route line is the route's water
BANK = 30.48            # 100 ft from the bank
WATER_FAIL = []
WATER_NO_SPLIT = set()   # Nov 4: water routes with no water/land split (centre-line test skipped)
WATER_UNCHECKED = set()   # Oct 31 (Fable #22): (river, park) pairs measured from the line because the water map did not answer
ROUTE_PTS = {}


def water_route(ref, LN, PIN):
    return ref in LN and LN[ref].get('type') in ('NHT', 'National Historic Trail') and bool(WATER_NHT.search((PIN.get(ref) or [''])[0] + ' ' + str(LN[ref].get('by'))))


def water_route_spots(lref, ls, oref, obox):
    """Stretches of park oref's own land (5 m in from its line) within 100 ft of the bank of the water the route lref follows."""
    out = []
    lbox = bbox_lines(ls)
    box = inter(lbox, [obox[0] - .003, obox[1] - .003, obox[2] + .003, obox[3] + .003], ROUTE_KM / 90)
    if not box: return out
    if lref not in ROUTE_PTS:
        ROUTE_PTS[lref] = np.asarray([p for l in ls for p in sample(l, 50)])
    A = ROUTE_PTS[lref]
    P = A[(A[:, 0] >= box[0] - .05) & (A[:, 0] <= box[2] + .05) & (A[:, 1] >= box[1] - .05) & (A[:, 1] <= box[3] + .05)]
    if not len(P): return out
    for b in tiles(box, CELL, 0):
        F = Frame(b, CELL, 60)
        bb = F.bounds()
        near = P[(P[:, 0] >= bb[0] - ROUTE_KM / 80) & (P[:, 0] <= bb[2] + ROUTE_KM / 80) & (P[:, 1] >= bb[1] - ROUTE_KM / 110) & (P[:, 1] <= bb[3] + ROUTE_KM / 110)]
        if len(near) < 4: continue                                    # the route does not pass near this tile
        land = pmask(F, oref, CURG)
        if not land.any(): continue
        # Oct 31 (Fable review #14 + HQ 4:15 PM): the route's water = the ONE big water body the route follows in this tile (the river or its
        # reservoir), not every lake / oxbow / slough beside it: only the LARGEST edge-touching blob near the route is kept (below)
        wg = nhd_water(bb, live=not str(oref).startswith('CA-'))   # rivers AND reservoirs: the Trail of Tears follows Kentucky Lake / Lake Barkley (NHD reservoirs)
        if wg is None:   # never silent: the pair becomes a NOT SURE row
            WATER_FAIL.append((lref, oref))
            c = F.ll(F.W // 2, F.H // 2)
            out.append({'refs': sorted([lref, oref]), 'kind': 'river', 'center': [c[1], c[0]], 'len_m': 0, 'shape': [[bb[0], bb[1]], [bb[2], bb[3]]],
                        'water_route': True, 'water_unchecked': True}); continue
        water = F.area(wg)
        if not water.any(): continue
        # Oct 28 (speed A1): every blob's box + size from one connectedComponentsWithStats call (the same labels as
        # connectedComponents: left = cc.min(), left + width - 1 = cc.max(), top = rr.min(), top + height - 1 = rr.max(),
        # area = len(rr)), and the route mask from one isin over the accepted labels: the same pixels as the per-blob loop
        n, lab, stats, _ = cv2.connectedComponentsWithStats(water, connectivity=8)
        kx, ky = F.kx, F.ky
        accepted = []
        for L in range(1, n):
            left, top, w, h, k = (int(v) for v in stats[L])
            if k < 4: continue
            lo0, la1 = F.ll(left, top); lo1, la0 = F.ll(left + w - 1, top + h - 1)
            dx = np.maximum(0, np.maximum(lo0 - near[:, 0], near[:, 0] - lo1)) * kx
            dy = np.maximum(0, np.maximum(la0 - near[:, 1], near[:, 1] - la1)) * ky
            d = np.hypot(dx, dy)
            # Oct 31 (Brandon on the live Finder, Ballard WMA x Trail of Tears x Lewis and Clark: '25.6 mi' and shading far from the
            # Ohio): the route's water = the RIVER the route follows, not every lake / slough inside the park within 1-3 km of the
            # coarse NPS line. A river runs THROUGH the tile (the blob touches the tile's edge); a lake / pond inside the land does not.
            edge = left == 0 or top == 0 or left + w >= F.W or top + h >= F.H
            if edge and (d <= ROUTE_KM * 1000).sum() >= 4 and d.min() <= 1000: accepted.append(L)   # the route runs along it
        if not accepted: continue
        accepted = [max(accepted, key=lambda L_: int(stats[L_][4]))]   # the main river / reservoir only
        route = np.isin(lab, accepted).astype(np.uint8)
        # Nov 1 (Brandon on the live Finder, Ballard WMA x Trail of Tears x Lewis and Clark: the strip ran up a creek through the fields;
        # rule R5a: a cove / side arm of the river or lake counts, a separate creek does not): narrow channels joined to the main water
        # are cut off. Width test = an opening as wide as 1/6 of the main water's width (15-100 m); the main bank keeps its exact line
        # (only the pixels the opening removed AND that lie outside its grown copy go), so wide coves / embayments stay.
        _mw = 2 * float(dt(route).max()) * CELL
        _k = int(round(min(100.0, max(15.0, _mw / 6)) / CELL))
        if _k >= 2:
            _ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (_k | 1, _k | 1))
            _op = cv2.morphologyEx(route, cv2.MORPH_OPEN, _ker)
            if _op.any():
                _keep = cv2.dilate(_op, _ker) & route
                _n2, _l2, _st2, _ = cv2.connectedComponentsWithStats(_keep, connectivity=8)
                if _n2 > 1: route = (_l2 == 1 + int(np.argmax(_st2[1:, 4]))).astype(np.uint8)
        wd = dt(1 - route, outside=1) * CELL
        # Nov 1 (Brandon: 'shows the border for the WMA but never shows the river trail boundaries'): the water route's OWN zone in this
        # tile = the land within 100 ft of the main water's edge (both banks), saved as rings beside the strip so the Finder can draw it
        _bz = ((wd <= BANK) & (route == 0)).astype(np.uint8)
        _bzr = []
        if _bz.any():
            for _c in cv2.findContours(_bz, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
                if cv2.contourArea(_c) < 4: continue
                _a = cv2.approxPolyDP(_c, 1.5, True).reshape(-1, 2)
                if len(_a) > 2: _bzr.append([F.ll(int(x), int(y)) for x, y in _a])
        ok = ((dt(land) * CELL >= STATION_IN) & (wd <= BANK + (CELL * .5 if PASS == 3 else CELL)) & (route == 0)).astype(np.uint8)
        if not ok.any(): continue
        m2, lab2 = cv2.connectedComponents(ok, connectivity=8)
        for L in range(1, m2):
            comp = lab2 == L
            k = int(comp.sum())
            if k < (2 if PASS == 3 else 1): continue
            rr, cc = np.nonzero(comp); i = len(rr) // 2
            c = F.ll(int(cc[i]), int(rr[i]))
            cs, _ = cv2.findContours(comp.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            ap = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 1.5, True).reshape(-1, 2)
            # Oct 31 (Fable review #13: the Metropolis shading): this shape is the OUTLINE of the bank strip (a polygon), not a line: no
            # 'every Nth point' (it cut straight across land), kept closed at 1.5 m (sharp_shape caps the points), marked shape_kind polygon
            # length = half the strip's outline (both long sides of a thin strip), not area / width (Fable #14: 25.6 mi for Ballard)
            per = cv2.arcLength(ap.reshape(-1, 1, 2).astype(np.float32), True) * CELL / 2   # the smoothed outline: a pixel staircase would add up to 40%
            out.append({'refs': sorted([lref, oref]), 'kind': 'river', 'center': [c[1], c[0]], 'len_m': round(per),
                        'shape': [F.ll(int(x), int(y)) for x, y in ap], 'water_route': True, 'shape_kind': 'polygon',
                        'route_zone': {lref: _bzr}})
    return merge(out)


def line_spots(lref, ls, oref, other, other_is_line, box, kind):
    """Stretches of park lref's line(s) at least STRETCH (25 metres) long where a station can stand within 100 ft of the line AND
    inside park oref (5 m in from its line); for two lines: within 100 ft of both (the two 100-ft zones meet).
    Nov 11 (KPC owner): a stretch is measured to the line's real end (sample() leaves the last vertex out) and pieces of the line
    that touch are joined before the 25 m test (a trail saved as many short pieces is one stretch). Passes 1-2 only screen (saved
    copies, coarse cells): every stretch goes on, as before; pass 3 applies the 25 m. A line whose WHOLE saved copy is
    shorter than 25 m is a broken copy, not the trail: anything it touches is kept and marked 'line_short' (decide() = not sure)."""
    out, runs, step = [], [], CELL / 2
    whole = sum(line_m(l) for l in ls)          # the whole saved line (every piece), metres
    for l in ls:
        smp = sample(l, step)
        if len(l) > 1 and (not smp or (smp[-1][0], smp[-1][1]) != (l[-1][0], l[-1][1])): smp = smp + [(l[-1][0], l[-1][1])]   # the line's real end
        pts = [p for p in smp if box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]]
        if len(pts) < 2 and not (pts and whole < STRETCH): continue
        ins = np.zeros(len(pts), bool)
        for b in tiles(bbox_lines([pts]), CELL, 0):
            idx = [i for i, p in enumerate(pts) if b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3]]
            if not idx: continue
            F = Frame(b, CELL, 120 + (RIVER_PAD if kind == 'river' else 0))
            # Oct 27 rule 5: a LINE-ONLY river counts from the river's EDGE (USGS NHD High Resolution water areas), a trail
            # from its line. Pass 1 has no water areas: a river gets RIVER_PAD extra as a screen; passes 2-3 measure exactly.
            wd = None
            if kind == 'river' and PASS >= 2 and str(lref).startswith('US-'):
                _wg = nhd_water(F.bounds(), rivers_only=True)
                if _wg is None: WATER_UNCHECKED.add((lref, oref))   # Oct 31 (Fable #22): no water map here = measured from the line: NOT SURE, never silent
                wm = F.area(_wg or [])
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
        run = []
        for i, p in enumerate(pts + [None]):
            if p is not None and ins[i]: run.append(p); continue
            if run: runs.append((run, line_m(run)))
            run = []
    # Nov 11 (KPC owner, 25 m rule): runs whose ends touch (pieces of one line, joined end to end) are ONE stretch for the test
    grp = list(range(len(runs)))
    def root(i):
        while grp[i] != i: grp[i] = grp[grp[i]]; i = grp[i]
        return i
    for i in range(len(runs)):
        for j in range(i + 1, len(runs)):
            if any(close_m(a, b) <= step for a in (runs[i][0][0], runs[i][0][-1]) for b in (runs[j][0][0], runs[j][0][-1])): grp[root(i)] = root(j)
    tot = {}
    for i, (_r, L) in enumerate(runs): tot[root(i)] = tot.get(root(i), 0.0) + L
    for i, (run, L) in enumerate(runs):
        short = whole < STRETCH                 # a broken saved line: kept, marked, decided as NOT SURE (never dropped)
        if not (short or PASS < 3 or tot[root(i)] >= STRETCH): continue   # passes 1-2 only screen (saved copies, coarse cells): pass 3 decides
        st = run[::max(1, len(run) // 200)]
        if len(st) == 1: st = st * 2
        out.append({'refs': sorted([lref, oref]), 'kind': kind, 'center': [round(run[len(run) // 2][1], 6), round(run[len(run) // 2][0], 6)],
                    'len_m': round(L), 'shape': [[round(q[0], 6), round(q[1], 6)] for q in st], **({'line_short': {lref: round(whole)}} if short else {})})
    return merge(out)


def line_m(pts):
    """Length of a line (list of [lon, lat]) in metres, flat earth per segment (the same sum line_spots always used)."""
    return sum(math.hypot((b[0] - a[0]) * 111320 * math.cos(math.radians(a[1])), (b[1] - a[1]) * 110574) for a, b in zip(pts, pts[1:]))


def close_m(a, b):
    return math.hypot((b[0] - a[0]) * 111320 * math.cos(math.radians(a[1])), (b[1] - a[1]) * 110574)


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


# ------------------------------------------------------------------ Oct 28 (speed step 2): reuse a pair's spots when NOTHING it depends on changed
# A pair's spots in a pass are a pure function of: this code, the pass's constants, both parks' outlines / lines / pins / owner kind,
# and every server answer the computation read (traced through the bundle cache, with a digest of each answer). The fingerprint of
# all that is kept with the spots in data/fers/reuse-p<pass>-<tag>.json; next run, the pair is computed again only if any of it
# differs (a changed answer, outline, line, pin, code or constant). Identical by construction: the same inputs, the same function.
import copy, hashlib
REUSE, REUSE_NEW, REUSE_FILE = {}, {}, None
CODE_HASH = hashlib.sha1(b''.join(open(pathlib.Path(__file__).parent / n, 'rb').read() for n in ('kpc_fers.py', 'kpc_owned.py', 'kpc_http_cache.py'))).hexdigest()
# Nov 2 review (speed): CODE_HASH changes on ANY edit to these files (a comment, a log line), and then every pair is computed
# again (~all night). FERS_ALGO is a version name for the 2-fer MATH: bump it by hand whenever a change can move a spot.
# Switch KPC_FERS_REUSE_KEY: 'code' (default, today: the file hash) | 'algo' (FERS_ALGO, so edits that cannot move a spot keep
# the saved spots). The pass constants (PASS, CELL, DET, PREC, REGION) stay in the fingerprint either way.
FERS_ALGO = 'fers-2026-11-02.1'
REUSE_KEY = FERS_ALGO if os.environ.get('KPC_FERS_REUSE_KEY', 'code').strip().lower() == 'algo' else CODE_HASH
# Nov 9 evening (Brandon t914u-t917u, 4:37-4:42 PM CST: 'only redo the parts that changed'; KISS): a pair is tested again only when
# one of its two parks changed (outline, record ids, POTA pin/name, line) or a DECLARED rule change names it. The code hash is no
# longer in the fingerprint: every rule change declares its scope in .github/fers-rule-scope.json (states, park kinds, flags such
# as 'bad-pin' / 'no-id' / 'line', or 'all'), and only the parks in that scope get a new stamp (so only their pairs are redone).
# KPC_FERS_FULL=1 = redo every pair (emergency switch; the areas workflow also uses it for its one round-robin full area per run).
FULL = str(os.environ.get('KPC_FERS_FULL') or '').strip().lower() in ('1', 'yes', 'true', 'y')
RECHECK_ANSWERS = os.environ.get('KPC_FERS_RECHECK_ANSWERS') == '1'   # the old 'read every server answer again' check (off)
try: SCOPE = json.load(open(pathlib.Path(__file__).resolve().parents[1] / 'fers-rule-scope.json')).get('changes') or []
except Exception: SCOPE = []  # noqa: BLE001
_STAMP = {}


def rule_stamp(r):
    """The ids of the declared rule changes whose scope covers park r (the park itself, its area, POTA kind, or a flag)."""
    if r in _STAMP: return _STAMP[r]
    p = PINS.get(r) or ()
    area = str(p[5]) if len(p) > 5 else ''
    area = area if area.startswith(('CA-', 'W-', 'US-')) else ('US-' + area if area else '')
    kind = str(p[4] or '').lower() if len(p) > 4 else ''
    flags = set()
    if r in NOPIN_BY_ID or (p and p[1] is None): flags.add('bad-pin')
    if r in CURLN: flags.add('line')
    out = []
    for c in SCOPE:
        sc = c.get('scope')
        if sc == 'none': continue
        # Nov 9 evening (KZ4CP 5:41 PM CST): 'parks' = park refs; a scope that lists nothing means ALL. A named park's pairs are all
        # tested again (pair_fp carries both parks' stamps), so the parks touching it are rechecked with it.
        if not isinstance(sc, dict) or sc.get('all') or not any(sc.get(k) for k in ('states', 'kinds', 'flags', 'parks')) \
           or r in {str(x) for x in sc.get('parks') or []} or area in (sc.get('states') or []) or area[3:] in (sc.get('states') or []) \
           or any(k.lower() in kind for k in (sc.get('kinds') or [])) or flags & set(sc.get('flags') or []):
            out.append(c.get('id'))
    _STAMP[r] = out
    return out


def _h(x): return hashlib.sha1(json.dumps(x, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()


def pair_fp(a, b, G, LN):
    ln = lambda r: {k: v for k, v in (LN.get(r) or {}).items() if k != 'date'} if r in LN else None   # the read date is not an input
    return _h([PASS, CELL, DET, PREC, REGION, a, b, G.get(a), G.get(b), ln(a), ln(b), PINS.get(a), PINS.get(b), OWNED.get(a), OWNED.get(b),
               a in KY_FS_MANAGED, b in KY_FS_MANAGED, rule_stamp(a), rule_stamp(b)])


def answers_unchanged(keys):
    """Every server answer the pair read last time, read again (from the bundle when it is there): the same digest?"""
    for url, params, digest in keys:
        HC.TRACE = []
        try: get(url, params)
        except Exception: HC.TRACE = None; return False  # noqa: BLE001
        same = bool(HC.TRACE) and HC.TRACE[-1][2] == digest
        HC.TRACE = None
        if not same: return False
    return True


def reuse_load():
    global REUSE, REUSE_FILE
    REUSE_FILE = OUT / f'reuse-p{PASS}-{RUN_TAG or REGION}.json'
    REUSE_NEW.clear()
    try: REUSE = json.load(open(REUSE_FILE)).get('pairs') or {}
    except Exception: REUSE = {}  # noqa: BLE001
    if FULL: REUSE = {}; LOG.append('full rebuild (KPC_FERS_FULL): every pair is tested again')


def reuse_keep_finished():
    """Nov 9 evening (Brandon t926u, 5:03 PM CST: 'save what was good before a run broke'): on a crash or time-out, the pair answers
    this pass FINISHED are saved to the saved-answers cache (with the older ones it did not reach), so the next run skips them.
    A pair that timed out was already taken out of REUSE_NEW. The live 2-fer files are NOT written here."""
    if REUSE_FILE is None or not REUSE_NEW: return 0
    merged = dict(REUSE); merged.update(REUSE_NEW)
    save_json(REUSE_FILE, {'about': 'saved pair answers (fingerprint + spots); written at a crash / time-out with the pairs that finished', 'pass': PASS,
                           'date': time.strftime('%Y-%m-%d'), 'partial': True, 'pairs': merged}, indent=None)
    return len(REUSE_NEW)


def reuse_save():
    if REUSE_FILE is None: return
    save_json(REUSE_FILE, {'about': 'Speed step 2 (Oct 28): per pair the fingerprint of everything its spots depend on + the server answers it read + the spots; a pair is computed again only when something changed.', 'pass': PASS, 'date': time.strftime('%Y-%m-%d'), 'pairs': REUSE_NEW}, indent=None)


TESTED = set()
CURLN = {}


def find_spots(G, LN, pairs, counts):
    CURG.clear(); CURG.update(G); CURLN.clear(); CURLN.update(LN); _STAMP.clear()
    spots = []
    reuse_load()
    # Oct 27 (Fable #8): pairs in map order (1-degree cells), so the ownership / water tiles in memory are the ones in use
    def cell_of(p):
        bx = [bbox_groups(G[r]) if r in G else bbox_lines(LN[r]['lines']) for r in p if r in G or r in LN]
        bx = [x for x in bx if x]
        return (math.floor(bx[0][0]), math.floor(bx[0][1]), p) if bx else (999, 999, p)
    for a, b in sorted(pairs, key=cell_of):
        if late(screen=PASS == 3): counts['stopped for time'] = True; break
        counts['pairs tested'] += 1
        TESTED.add((a, b))
        ba = bbox_groups(G[a]) if a in G else bbox_lines(LN[a]['lines'])
        bb = bbox_groups(G[b]) if b in G else bbox_lines(LN[b]['lines'])
        box = inter(ba, bb, ROUTE_KM / 90 if (water_route(a, LN, PINS) or water_route(b, LN, PINS)) else 0.0008)
        if not box or not all(math.isfinite(v) for v in box): continue
        if box[2] - box[0] > 40 or box[3] - box[1] > 40: LOG.append(f'{a} + {b}: shared box too big (an outline crossing the date line?)'); continue
        pk = f'{a}+{b}'; fp = pair_fp(a, b, G, LN); old = REUSE.get(pk)
        if old and old.get('fp') == fp and (not RECHECK_ANSWERS or answers_unchanged(old.get('keys') or [])):
            spots += copy.deepcopy(old['spots']); REUSE_NEW[pk] = old; counts['pairs reused (nothing changed)'] = counts.get('pairs reused (nothing changed)', 0) + 1
            fx = old.get('fx') or {}   # the pair's side notes are replayed too (a map that did not answer, a water route left unchecked, log lines)
            OWNED_FAIL.update(fx.get('owned_fail') or []); WATER_FAIL.extend(tuple(x) for x in fx.get('water_fail') or []); LOG.extend(fx.get('log') or [])
            evict(box); continue
        n_log, of0, wf0 = len(LOG), set(OWNED_FAIL), len(WATER_FAIL)
        HC.TRACE = []
        _pc = park_clock(f'{a}+{b}', f'pass {PASS} pair test')
        try:
          with _pc:
            if a in G and b in G: got = area_spots(G, [a, b], box)
            else:
                got = []
                for l_ref, o_ref in ((a, b), (b, a)):
                    _ls = LN[l_ref]['lines'] if l_ref in LN else []
                    _wp = set(LN[l_ref].get('water_parts') or []) if l_ref in LN else set()
                    _wet = [l for i, l in enumerate(_ls) if i in _wp] if _wp else _ls          # Oct 31 (Fable #12): the WATER parts (from the
                    _dry = [l for i, l in enumerate(_ls) if i not in _wp] if _wp else _ls      # agency's route field) use the bank, the land parts the line
                    if not _wp and l_ref in LN and water_route(l_ref, LN, PINS):
                        # Nov 4 (Mapping 2-fer review #2): a WATER route with no water/land split (no route field) was tested by its bank
                        # AND its drawn centre line; the drawn line of a water trail is not land. Bank only; listed as not sure.
                        _dry = []
                        if l_ref not in WATER_NO_SPLIT: WATER_NO_SPLIT.add(l_ref); LOG.append(f'{l_ref}: water route with no water/land split: bank test only, centre-line test skipped (not sure)')
                    if l_ref in LN and l_ref not in G and o_ref in G and water_route(l_ref, LN, PINS) and _wet:
                        got += water_route_spots(l_ref, _wet, o_ref, bbox_groups(G[o_ref]))   # the river bank, not the drawn line
                    if l_ref in LN and l_ref not in G:
                        if o_ref in G and _dry: got += line_spots(l_ref, _dry, o_ref, G[o_ref], False, box, LN[l_ref]['kind'])
                        elif o_ref in LN: got += line_spots(l_ref, LN[l_ref]['lines'], o_ref, LN[o_ref]['lines'], True, box, LN[l_ref]['kind']); break
            spots += got
            seen_k = {}
            for u, p, dg in HC.TRACE: seen_k[(u, json.dumps(p, sort_keys=True, default=str))] = [u, p, dg]
            REUSE_NEW[pk] = {'fp': fp, 'keys': list(seen_k.values()), 'spots': copy.deepcopy(got),
                             'fx': {'owned_fail': sorted(OWNED_FAIL - of0), 'water_fail': [list(x) for x in WATER_FAIL[wf0:]], 'log': LOG[n_log:]}}
        except Exception as e:  # noqa: BLE001
            LOG.append(f'{a} + {b}: {str(e)[:80]}')
        if _pc.hit:   # Nov 9 PM: skipped for time and listed; pass 1 carries its old rows over, passes 2-3 leave it waiting
            TIMED_PAIRS.add((a, b)); REUSE_NEW.pop(f'{a}+{b}', None)
            if PASS != 1: TESTED.discard((a, b))
        HC.TRACE = None
        evict(box)
    # Oct 27 (chat 8): two water routes on the same bank of one park (Lewis and Clark + Trail of Tears at Ballard WMA) = a 3-fer
    wr = [x for x in spots if x.get('water_route') and not x.get('water_unchecked')]
    for i, x in enumerate(wr):
        for y in wr[i + 1:]:
            if x is y: continue
            lx = [r for r in x['refs'] if r in LN and r not in G]; ly = [r for r in y['refs'] if r in LN and r not in G]
            ox = [r for r in x['refs'] if r in G]; oy = [r for r in y['refs'] if r in G]
            if ox != oy or not lx or not ly or lx == ly or not inter(sbox(x), sbox(y), 0.0003): continue
            refs3 = sorted(set(x['refs']) | set(y['refs']))
            if any(z['refs'] == refs3 and inter(sbox(z), sbox(x), 0.0003) for z in spots): continue
            spots.append({'refs': refs3, 'kind': 'river', 'center': x['center'], 'len_m': min(x.get('len_m') or 0, y.get('len_m') or 0),
                          'shape': x['shape'], 'box': sbox(x), 'water_route': True})
    # n-fers: a third park whose boundary may overlap the SAME place as an area spot (50 yards across, all three)
    nb = {}
    for a, b in pairs: nb.setdefault(a, set()).add(b); nb.setdefault(b, set()).add(a)
    level = [s for s in spots if s['kind'] == 'area' and not s.get('masked_out')]
    for n in range(3, 10):   # Oct 27 (Fable #6, rule 11): up to 9-fers; a level that adds nothing ends it
        if not level: break
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
        spots += nxt; level = [x for x in nxt if not x.get('masked_out')]
    reuse_save()
    return spots


def near_pairs(G, pairs, spots, gap_m=100.0):
    """MISSING CHECK (HQ Oct 27 3:23 PM): area pairs with no spot whose outlines still come within gap_m of each other: an
    outside reason to expect a 2-fer, so the expected list says why there is none. [[a, b, metres]]"""
    have = {tuple(x['refs'][:2]) for x in spots}
    out = []
    for a, b in sorted(pairs):
        if time.time() - T0 > LIMIT * 1.1: LOG.append('near-pairs list cut short for time'); break   # Nov 9: never runs long past the budget
        if (a, b) in have or a not in G or b not in G: continue
        box = inter(bbox_groups(G[a]), bbox_groups(G[b]), gap_m / 90000 * 2)
        if not box: continue
        try:
            f = Frame(box, max(10.0, math.sqrt(max(1.0, (box[2] - box[0]) * 111320 * math.cos(math.radians(box[1])) * (box[3] - box[1]) * 110574) / 4e6)), gap_m)
            if f.cell > gap_m / 2: continue
            da = dt(1 - f.area(G[a]), outside=1) * f.cell
            mb = f.area(G[b])
            if mb.any():
                d = float(da[mb > 0].min())
                if d <= gap_m: out.append([a, b, round(d)])
        except Exception as e: LOG.append(f'near {a}+{b}: {str(e)[:50]}')  # noqa: BLE001
    return out


# Oct 28 (Brandon 6:18 AM): Fort Heiman (US-3790) = its own outline now (the Fort Heiman tract only, split out of Fort Donelson's
# 8-piece record), but the pair STAYS a 'same land, two park numbers' row: both numbers apply to that one tract.
SAME_FAR = []   # same-land pairs left out: pins far apart, not both inside the shared outline (Oct 29)
SAME_LAND_PAIRS = [(('US-0703', 'US-3790'), 'Fort Heiman tract', 'Fort Heiman (Fort Donelson National Battlefield tract)')]


def same_outline(parks):
    seen, out = {}, []
    for refs, rec, nm in SAME_LAND_PAIRS:
        if all(r in parks for r in refs): out.append({'refs': sorted(refs), 'record': rec, 'name': nm})
    for ref, p in parks.items():
        for i, rid in enumerate(p['ids']):
            if rid is None: continue
            k = (p['m'][i][2], str(rid)) if 'm' in p else (p['st'][:2], str(rid))
            # Oct 29 (chat 8: NS 161 'same land' rows): Canada ids are '<first 12 letters of the layer label>:<oid>', and two Nova
            # Scotia layers both start 'Nova Scotia ', so ':731' is Boot Island in one layer and Seal Cove in the other: the record
            # NAME must match too (saved_ca already reads geometry by id + name)
            if p['st'].startswith('CA-') and 'm' not in p: k = k + (low(p['names'].get(str(rid))),)
            if k in seen and seen[k] != ref: out.append({'refs': sorted([seen[k], ref]), 'record': str(rid), 'name': p['names'].get(str(i) if 'm' in p else str(rid))})
            else: seen[k] = ref
    return out


AGENCY = set()
WILDRIVER = re.compile(r'wild (and|&) scenic|wild river|scenic river|recreational river', re.I)


def pin_inside(ref, PIN, G, LN):
    nm, la, lo = PIN[ref][0], PIN[ref][1], PIN[ref][2]
    if la is None or lo is None: return None   # Nov 9 PM: a bad POTA pin is never used (pins never count anyway, rule 6)
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
            if s.get('water_route') and water_route(r, LN, PINS):   # within 100 ft of the water's bank, not of the drawn route line
                wg = nhd_water(F.bounds())
                if not wg: continue
                w = F.area(wg)
                z = ((dt(1 - w, outside=1) * cell <= BANK) & (w == 0)).astype(np.uint8)
            else:
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
    # Oct 31 (Brandon, Ballard WMA: the 'P' was a road in Metropolis, Illinois, across the Ohio): only a road / lot / path ON or AT the
    # edge of the parks' own land (within ~60 m) can be the access; one across a river or in another state is never picked
    if areas:
        own = None
        for r in areas:
            m_ = pmask(F, r, G)
            own = m_ if own is None else (own | m_)
        if own is not None and own.any():
            near_own = (dt(1 - own, outside=1) * cell <= 60).astype(np.uint8)
            for k_ in feats: feats[k_] = feats[k_] & near_own
    best = None
    for kind, fm in feats.items():
        if not fm.any(): continue
        d = dt(1 - fm, outside=1) * cell
        d = np.where(ok > 0, d, np.inf)
        i = np.unravel_index(np.argmin(d), d.shape)
        if np.isfinite(d[i]) and (best is None or d[i] < best[0]): best = (float(d[i]), kind, i)
    if not best:
        if not s['refs'][0].startswith('US-'):
            return {'at': s['center'], 'from': 'none (no road source yet)', 'note': 'no road map read for this country yet: the pin is the middle of the spot'}
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
FEDDES = {'wsrc', 'akht', 'wld', 'wsa', 'wbl', 'nca', 'hma', 'rst', 'rma', 'fwsr', 'fsod'}   # Oct 28 (chat 9): + FS wild-river corridors, FS other designated areas   # federal DESIGNATIONS / planning areas, not ownership


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



LINE_PAD_M = 150.0
def clip_ring(ring, b):
    """The parts of one ring inside box b, as polylines (one point past each end kept, so a line reaches the box edge)."""
    out, cur = [], []
    inside = [b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3] for p in ring]
    for i, p in enumerate(ring):
        if inside[i]:
            if not cur and i > 0: cur.append(ring[i - 1])
            cur.append(p)
        elif cur:
            cur.append(p); out.append(cur); cur = []
    if cur: out.append(cur)
    return [[[round(q[0], 6), round(q[1], 6)] for q in l] for l in out if len(l) > 1]


def spot_lines(x, G):
    """Oct 27 (chat 3 -> HQ 5:36 PM): each park's boundary edges from the SAME read the patch was cut from (pass 3+ detail,
    Kentucky = the live layers, agency-land parks = the owned land the patch used), clipped to the spot's box + 150 m.
    The Overlap Finder draws these bold, so the patch and the lines agree."""
    b = x.get('box') or sbox(x)
    if not b: return None
    la = (b[1] + b[3]) / 2
    dx, dy = LINE_PAD_M / (111320 * math.cos(math.radians(la))), LINE_PAD_M / 110574
    bb = [b[0] - dx, b[1] - dy, b[2] + dx, b[3] + dy]
    out = {}
    for r in x.get('refs') or []:
        gs = G.get(r)
        if not gs: continue
        if r in OWNED and OWNED[r] not in SOFT:   # Oct 28 (simple test): Park Service / Corps / FWS / state projects draw their OFFICIAL boundary
            own = owned_land(OWNED[r], bb)
            if own: gs = own
        ls, n = [], 0
        for g in gs:
            for ring in g:
                if not inter(bbox_lines([ring]), bb): continue
                for l in clip_ring(ring, bb):
                    l = dp_line(l, LINE_DP_M)   # Nov 2 (HQ, the 103 MB Alaska file): drawing lines thinned 3 m (R-G6), 5 decimals
                    if len(l) < 2: continue
                    if n + len(l) > LINE_CAP: break
                    ls.append(l); n += len(l)
                if n >= LINE_CAP: break
            if n >= LINE_CAP: break   # the cap was per ring group only, so a big park (Tongass, Wrangell) filled 240 KB per spot
        if ls: out[r] = ls
    return out or None


LINE_DP_M, LINE_CAP = 3.0, 6000


def dp_line(l, tol_m=3.0):
    """Douglas-Peucker in metres (flat earth near the line), both ends kept, rounded to 5 decimals (~1 m)."""
    if len(l) < 3: return [[round(q[0], 5), round(q[1], 5)] for q in l]
    la = math.radians(sum(q[1] for q in l) / len(l)); kx, ky = 111320 * math.cos(la), 110574
    P = [(q[0] * kx, q[1] * ky) for q in l]; keep = [False] * len(P); keep[0] = keep[-1] = True; st = [(0, len(P) - 1)]
    while st:
        a, b = st.pop(); ax, ay = P[a]; dx, dy = P[b][0] - ax, P[b][1] - ay; L = dx * dx + dy * dy; best, bi = -1.0, -1
        for i in range(a + 1, b):
            px, py = P[i][0] - ax, P[i][1] - ay
            t = 0.0 if L == 0 else max(0.0, min(1.0, (px * dx + py * dy) / L))
            d = math.hypot(px - t * dx, py - t * dy)
            if d > best: best, bi = d, i
        if best > tol_m: keep[bi] = True; st += [(a, bi), (bi, b)]
    return [[round(l[i][0], 5), round(l[i][1], 5)] for i in range(len(l)) if keep[i]]


def add_lines(files, G, today):
    n = 0
    for d in files.values():
        for x in d.get('spots', []):
            if x.get('kind') != 'area' or str(x.get('status', '')).startswith('dropped') or late(): continue
            if any(r not in G for r in x.get('refs', [])): continue
            try:
                L = spot_lines(x, G)
                if L: x['lines'] = L; x['lines_read'] = today; n += 1
            except Exception as e: LOG.append(f"lines {x.get('id')}: {str(e)[:60]}")  # noqa: BLE001
    return n


def _seg_dist(pts, rings, kx, ky):
    """Metres from each point to the nearest edge of rings (numpy, flat-earth near the park)."""
    segs = [np.asarray(r, dtype=np.float64)[:, :2] for r in rings if len(r) > 1]
    if not segs or not len(pts): return np.array([])
    A = np.concatenate([g[:-1] for g in segs]); B = np.concatenate([g[1:] for g in segs])
    A = A * [kx, ky]; B = B * [kx, ky]; P = np.asarray(pts, dtype=np.float64)[:, :2] * [kx, ky]
    out = np.empty(len(P))
    AB = B - A; L2 = np.maximum((AB ** 2).sum(1), 1e-9)
    for i in range(0, len(P), 64):
        q = P[i:i + 64, None, :]
        t = np.clip(((q - A) * AB).sum(2) / L2, 0, 1)
        d = np.sqrt((((A + t[..., None] * AB) - q) ** 2).sum(2))
        out[i:i + 64] = d.min(1)
    return out


def ky_drift(parks, spots_boxes):
    """Oct 27 (HQ 5:36 PM, item 3; measure only, nothing refreshed): how far the SAVED Kentucky outlines (ky-*.geojson, used by
    Am I in the Park and the maps) sit from the LIVE agency layer, park by park: points every ~sample along the saved edge ->
    distance to the live edge. Daniel Boone: the saved owned-land file vs the live Forest Service ownership map in the spot boxes."""
    rows = []
    ky_geom(parks, [])   # fills KYIDX
    for ref in sorted(parks):
        for rid in parks[ref].get('ids') or []:
            src, nm = str(rid).split('|', 1) if '|' in str(rid) else ('', '')
            if src not in KYLIVE: continue
            saved = [ring for pp in KYIDX.get((src, nm), []) for ring in pp]
            live = [ring for g in ky_live(src, nm) for ring in g]
            if not saved or not live: rows.append({'ref': ref, 'layer': src, 'name': nm, 'note': 'no live copy' if saved else 'no saved copy'}); continue
            pts = [p for r in saved for p in r]
            pts = pts[::max(1, len(pts) // 600)]
            la = pts[0][1]; kx, ky = 111320 * math.cos(math.radians(la)), 110574
            d = _seg_dist(pts, live, kx, ky)
            if not len(d): continue
            rows.append({'ref': ref, 'layer': src, 'name': nm, 'median_m': round(float(np.median(d)), 1), 'p95_m': round(float(np.percentile(d, 95)), 1),
                         'max_m': round(float(d.max()), 1), 'points': int(len(d))})
    try:
        fs = json.load(open('ky-dbnf-owned.geojson')).get('features') or []
        own_saved = []
        for f in fs:
            g = f.get('geometry') or {}; c = g.get('coordinates') or []
            for pp in (c if g.get('type') == 'MultiPolygon' else [c]): own_saved += pp
        for sid, b in spots_boxes:
            live = owned_land('usfs', b)
            if not live: continue
            lr = [ring for g in live for ring in g]
            pts = [p for r in own_saved for p in r if b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3]]
            if not pts: continue
            kx, ky = 111320 * math.cos(math.radians(pts[0][1])), 110574
            d = _seg_dist(pts[::max(1, len(pts) // 600)], lr, kx, ky)
            if len(d): rows.append({'ref': 'US-4484', 'layer': 'owned land (ky-dbnf-owned.geojson)', 'name': f'around spot {sid}',
                                    'median_m': round(float(np.median(d)), 1), 'p95_m': round(float(np.percentile(d, 95)), 1), 'max_m': round(float(d.max()), 1), 'points': int(len(d))})
    except Exception as e: LOG.append(f'drift dbnf: {str(e)[:60]}')  # noqa: BLE001
    off = [r for r in rows if (r.get('p95_m') or 0) > 9.144]
    save_json(OUT / 'ky-outline-drift.json', {'about': 'Saved Kentucky outlines vs the live agency layers (measured only, nothing refreshed; HQ + Brandon decide). '
              'p95 = 95 of 100 points on the saved edge are within this distance of the live edge. Off = p95 over 10 yards (9.1 m).',
              'date': time.strftime('%Y-%m-%d'), 'off_over_10_yards': len(off), 'parks': sorted(rows, key=lambda r: -(r.get('p95_m') or 0))}, indent=1)
    notice('2-fer bot', f'Kentucky outline drift: {len(rows)} outlines measured, {len(off)} off by more than 10 yards (p95)')


def dedupe_line_rows(spots):
    """Oct 27 (chat 3, Pine Mountain State Trail x Jefferson NF WMA): the same stretch can come back twice (two tiles / two passes,
    centres a few metres apart, the SAME shape). The second copy is marked 'dropped: the same stretch twice' and every main row's
    'stretches' + 'len_m' are counted again without it."""
    seen, n = {}, 0
    for x in spots:
        if x.get('kind') not in ('trail', 'river') or not x.get('shape'): continue   # Oct 28: only line stretches (Ohio lost 35 'same land' rows to this)
        k = (tuple(x['refs']), x['kind'], tuple(tuple(q) for q in x['shape'][::max(1, len(x['shape']) // 20)]), x.get('len_m'))
        if k in seen and not str(x.get('status', '')).startswith('dropped'):
            x['status'] = 'dropped: the same stretch twice (copy of ' + seen[k] + ')'; n += 1
        else: seen.setdefault(k, x['id'])
    for m in spots:
        if m.get('kind') not in ('trail', 'river') or not m.get('stretches'): continue
        mem = [x for x in spots if str(x.get('status', '')) == 'merged into one row: ' + m['id']]
        own = (m.get('len_main') or m.get('len_m') or 0) if not mem else None
        m['stretches'] = 1 + len(mem)
        if 'len_main' not in m:   # a row merged before Nov 11 has no own length: its total less ITS members and the copies OF them
            ids = {m['id']} | {x.get('id') for x in mem}   # (was: every copy of the pair, even of other rows = 0 m for real trails)
            m['len_main'] = max(0, (m.get('len_m') or 0) - sum(x.get('len_m') or 0 for x in spots if tuple(x['refs']) == tuple(m['refs']) and (
                str(x.get('status', '')) == 'merged into one row: ' + m['id'] or any(str(x.get('status', '')).startswith('dropped: the same stretch twice (copy of ' + str(i) + ')') for i in ids))))
        m['len_m'] = m['len_main'] + sum(x.get('len_m') or 0 for x in mem)
    return n


LINE_WORD = re.compile(r'\btrail\b|\btrace\b|scenic byway', re.I)
def line_zone(x, G, PIN):
    """Oct 27 (chat 3): the TRUE 2-fer ground of a trail stretch = the 100-ft band around the trail that is also inside the other
    park (5 m in from its line, its owned land for an agency-land park) = 'zone' rings, + its acres and how wide it gets at most."""
    if x.get('kind') != 'trail' or not x.get('shape'): return None
    lref = next((r for r in x['refs'] if LINE_WORD.search((PIN.get(r) or [''])[0])), None)
    oref = next((r for r in x['refs'] if r != lref and r in G), None)
    if not lref or not oref: return None
    b = x.get('box') or bbox_lines([x['shape']])
    F = Frame(b, CELL, 60)
    # Oct 28 (pass-5 speed-up): the zone lies within 100 ft of THIS stretch's own line, but a main row's box covers every stretch
    # folded into it (Sheltowee x Daniel Boone: a 961-million-pixel frame, 4 GB). So the same global pixel grid is used, but only a
    # window around the stretch's line (+ a margin far wider than the pen and the 5-m distance test) is drawn: the same pixels.
    w = F.window(F.px(x['shape']), int(math.ceil((ZONE + STATION_IN) / CELL)) + 24)
    # land: each ring is filled in its own box on the WHOLE frame's grid and edges (fillPoly gives other pixels when the picture
    # edge cuts a polygon somewhere else: tested), then only the window is kept
    m = F.area_in(G[oref], w)
    if oref in OWNED and F.any_in(G[oref]):
        o = owned_land(OWNED[oref], F.bounds())   # the global frame's bounds: the same ownership-map answer as before
        if o is None: pass   # Nov 9 (Brandon 9:37 AM CST): no owned-land mask; the official outline is the park
        else:
            keep = F.area_in(o, w)
            if OWNED[oref] in SOFT:   # Oct 28 (simple test): only private land is cut out of the official boundary
                pub = owned_land('public', F.bounds())
                if pub: keep |= F.area_in(pub, w)
            m &= keep
    own = (dt(m) * CELL >= STATION_IN).astype(np.uint8)
    z = (w.lines([x['shape']], ZONE + STATION_IN) & own).astype(np.uint8)
    if os.environ.get('ZONE_CHECK') and F.W * F.H < 200e6:   # proof hook: the old whole-frame zone, pixel by pixel
        own0 = (dt(pmask(F, oref, G)) * CELL >= STATION_IN).astype(np.uint8)
        z0 = (F.lines([x['shape']], ZONE + STATION_IN) & own0).astype(np.uint8)
        zz = np.zeros_like(z0); zz[w.r0:w.r0 + w.H, w.c0:w.c0 + w.W] = z
        d = np.argwhere(zz != z0)
        print(f"ZONECHECK {x.get('id')} frame {F.W}x{F.H} win {w.c0},{w.r0},{w.W}x{w.H} old {int(z0.sum())} new {int(z.sum())} diff {len(d)} at {d[:5].tolist()}", flush=True)
        if len(d):
            l0 = F.lines([x['shape']], ZONE + STATION_IN); m0 = pmask(F, oref, G)
            lw = np.zeros_like(l0); lw[w.r0:w.r0 + w.H, w.c0:w.c0 + w.W] = w.lines([x['shape']], ZONE + STATION_IN)
            mw = np.zeros_like(m0); mw[w.r0:w.r0 + w.H, w.c0:w.c0 + w.W] = m
            print(f"ZONECHECK   lines differ {int((lw != l0).sum())}, land differ (inside window) {int((mw != m0)[w.r0:w.r0 + w.H, w.c0:w.c0 + w.W].sum())}", flush=True)
    if not z.any(): return {'zone': [], 'zone_acres': 0, 'zone_wide_m': 0}
    cs, _ = cv2.findContours(z, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE, offset=(w.c0, w.r0))
    rings = []
    for c in sorted(cs, key=cv2.contourArea, reverse=True)[:12]:
        c = cv2.approxPolyDP(c, 1.0, True).reshape(-1, 2)
        if len(c) >= 3: rings.append([F.ll(int(p[0]), int(p[1])) for p in c[:300]])
    return {'zone': rings, 'zone_acres': round(float(z.sum()) * CELL * CELL / 4046.86, 2),
            'zone_wide_m': round(float(dt(z).max()) * CELL * 2, 1)}


STRIP_MIN_M = 9.144   # RULE 15 (Brandon Oct 27 6:30 PM, option A): a trail strip at least 10 yards (30 ft) wide somewhere along it
def add_zones(files, G, PIN, today):
    n = 0
    for d in files.values():
        dedupe_line_rows(d.get('spots', []))
        for x in d.get('spots', []):
            if x.get('kind') != 'trail' or str(x.get('status', '')).startswith('dropped') or late(): continue
            try:
                zz = line_zone(x, G, PIN)
                if zz is not None: x.update(zz); x['zone_read'] = today; n += 1
            except Exception as e: LOG.append(f"zone {x.get('id')}: {str(e)[:60]}")  # noqa: BLE001
        rule15(d.get('spots', []))
    return n


def rule15(spots):
    """RULE 15: a trail row (with the stretches folded into it) whose strip is under 10 yards wide EVERYWHERE = 'very tight
    (members only)', the same tier as a 25-50 yard overlap. A row whose strip was not measured is left as it is."""
    for m in spots:
        if m.get('kind') != 'trail' or not str(m.get('status', '')).startswith(('candidate', VERY_TIGHT)): continue
        mem = [x for x in spots if str(x.get('status', '')) == 'merged into one row: ' + m['id']]
        ws = [x['zone_wide_m'] for x in [m] + mem if x.get('zone_wide_m') is not None]
        if not ws: continue
        m['strip_wide_m'] = max(ws)
        if max(ws) < STRIP_MIN_M:
            m['status'] = VERY_TIGHT; m['tier'] = VERY_TIGHT; m['list'] = 'Very tight (members only)'
            m['rule15'] = f'strip at most {round(max(ws) / 0.9144, 1)} yards wide (under 10 yards everywhere: rule 15)'
        elif m.pop('rule15', None):
            m['status'] = 'candidate'; m.pop('tier', None); m.pop('list', None)

def file_of(st): return OUT / f'{st}.json'


def sbox(s): return s.get('box') or bbox_lines([s['shape']])



PATCH_PTS, PATCH_EPS_M = 400, 1.5
def sharp_shape(pts, closed=True):
    """Oct 27 (HQ 6:46 PM, chat 3's Finder: an 80-point patch cut corners by 10-20 m on big Daniel Boone patches): keep the patch
    within 1.5 m of its 5 m-grid edge (Douglas-Peucker in metres), at most 400 points (the 20 MB file rule: small patches stay small)."""
    if len(pts) <= 3: return pts
    la = sum(p[1] for p in pts) / len(pts); kx, ky = 111320 * math.cos(math.radians(la)), 110574
    P = np.asarray(pts, dtype=np.float64)[:, :2] * [kx, ky]
    eps = PATCH_EPS_M
    c = cv2.approxPolyDP(P.astype(np.float32).reshape(-1, 1, 2), eps, closed).reshape(-1, 2)   # B5 (Oct 30): a trail / river stretch is an open line
    # Oct 28 (Mammoth Cave x Green River: a 25-mile patch drawn with lines jumping across the land): too many points = a LARGER
    # tolerance (the outline stays on its real edge, within eps metres), never 'every n-th point'; up to 4x the points for long patches
    cap = PATCH_PTS * 4 if len(P) > PATCH_PTS * 8 else PATCH_PTS
    while len(c) > cap and eps < 200:
        eps *= 1.6; c = cv2.approxPolyDP(P.astype(np.float32).reshape(-1, 1, 2), eps, closed).reshape(-1, 2)
    return [[round(float(x) / kx, 6), round(float(y) / ky, 6)] for x, y in c]

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
            elif len(s['shape']) > 80: s['shape'] = sharp_shape(s['shape'], closed=bool(s.get('water_route')) or s.get('kind') not in ('trail', 'river'))   # a water-route row's shape is a polygon
    return spots


def key_of(s): return '+'.join(s['refs']) + '@' + s['kind']


# Nov 2 5:45 PM (HQ, chat 8's KY hold check: 4 pairs looked 'missing' after the river fix, only their centre had moved a little): a
# spot keeps its id from run to run. ID memory per state file ('ids': {pair@kind: [[lat, lon, id], ...]}); a new spot of the same
# pair + kind within STABLE_M of a remembered spot takes that id (nearest first, each id once per run); else a new id is made.
STABLE_M = 600


def stable_ids(spots, mem):
    used = set()
    def dm(a, b): return math.hypot((a[0] - b[0]) * 110570, (a[1] - b[1]) * 111320 * math.cos(math.radians(a[0])))
    for s in sorted(spots, key=lambda x: (key_of(x), x['center'][0], x['center'][1])):
        k = key_of(s); c = s['center']
        near = sorted((dm(c, (m[0], m[1])), m[2]) for m in mem.get(k, []) if m[2] not in used)
        if near and near[0][0] <= STABLE_M: s['id'] = near[0][1]
        else:
            i = k + '@%.3f,%.3f' % tuple(c); n = 2
            while i in used: i = k + '@%.3f,%.3f' % tuple(c) + f'#{n}'; n += 1
            s['id'] = i; mem.setdefault(k, []).append([round(c[0], 5), round(c[1], 5), i])
        used.add(s['id'])
    return mem


def id_memory(d):
    """the state file's id memory, seeded from its spots when it has none yet (files made before Nov 2 5:45 PM)"""
    mem = {k: [list(m) for m in v] for k, v in ((d or {}).get('ids') or {}).items()}
    for x in (d or {}).get('spots') or []:
        if x.get('id') and x.get('center') and x.get('refs') and x.get('kind'):
            k = key_of(x)
            if not any(m[2] == x['id'] for m in mem.get(k, [])): mem.setdefault(k, []).append([round(x['center'][0], 5), round(x['center'][1], 5), x['id']])
    return mem


def channel_rows(files, G, today):
    """Brandon Oct 28 6:55 PM (mapping.md): a river channel counts as park land only where the agency's OWN record includes it;
    else the channel inside BOTH parks' outlines is a WATER ONLY row (boat spot), never dropped. For each live area pair with an
    agency-land park: (both outlines) minus (the agency's own land) = the slot; its USGS water part holding a 50-yard spot = the row."""
    n = 0
    for d in files.values():
        have = {x.get('id') for x in d.get('spots', [])}
        for x in list(d.get('spots', [])):
            if x.get('kind') != 'area' or len(x.get('refs') or []) != 2 or not str(x.get('status', '')).startswith(('candidate', 'very tight')): continue
            if not any(r in OWNED for r in x['refs']) or any(r not in G for r in x['refs']) or late(): continue
            try:
                sb = sbox(x); pad = .002; box = [sb[0] - pad, sb[1] - pad, sb[2] + pad, sb[3] + pad]
                cell = CELL; F = Frame(box, cell, SHRINK * 2)
                while F.W * F.H > MAXPX: cell *= 1.5; F = Frame(box, cell, SHRINK * 2)
                outl = None; own = None
                for r in x['refs']:
                    m = F.area(G[r]); outl = m if outl is None else outl & m
                    # the agency's OWN land only (as before tonight: the simple test's public-land + water keep is not used here)
                    if r in OWNED:
                        ol = owned_land(OWNED[r], F.bounds()); pm = m & F.area(ol) if ol else m
                    else: pm = m
                    own = pm if own is None else own & pm
                slot = outl & (1 - own)
                if not slot.any(): continue
                wg = nhd_water(F.bounds())
                if wg is None: continue   # no water map: nothing said (the land row stands)
                ch = (slot & F.area(wg)).astype(np.uint8)
                dd = dt(ch) * cell
                if not (dd >= TIGHT_SHRINK + cell).any(): continue
                r0, c0 = np.unravel_index(np.argmax(dd), dd.shape); ctr = F.ll(int(c0), int(r0))
                rid = '+'.join(x['refs']) + '@area@channel@%.3f,%.3f' % (ctr[1], ctr[0])
                if rid in have: continue
                cs, _ = cv2.findContours(ch, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                big = max(cs, key=cv2.contourArea); ap = cv2.approxPolyDP(big, 1.5, True).reshape(-1, 2)
                agency = ', '.join(OWNMAP.get(OWNED[r], OWNED[r]) for r in x['refs'] if r in OWNED)
                row = {'refs': x['refs'], 'kind': 'area', 'id': rid, 'center': [ctr[1], ctr[0]], 'box': x.get('box'), 'shape': sharp_shape([F.ll(int(c), int(r)) for c, r in ap]),
                       'acres': round(int(ch.sum()) * cell * cell / 4046.86, 1), 'wide_m': round(float(dd.max()) * 2, 1), 'passes': [1, 1, 1],
                       'status': 'water only: boat or kayak', 'list': '🚤 Water only: boat or kayak', 'found': today, 'checked': today,
                       'note': f"the river channel between the banks: inside both parks' outlines, but not on {agency} (ruling Oct 28: a boat spot, never dropped)",
                       'names': x.get('names'), 'maps': x.get('maps'), 'channel_of': x.get('id')}
                water_date(row); d['spots'].append(row); have.add(rid); n += 1
            except Exception as e: LOG.append(f"channel {x.get('id')}: {str(e)[:60]}")  # noqa: BLE001
    return n


def land_check(s, G, live=True):
    """Rules 9 + 10 on a US area spot: 'ok', 'water' (the 50-yard patch exists only on a lake / river surface), 'closed'
    (it exists only inside a PAD-US closed area)."""
    sb = sbox(s); pad = .002
    box = [sb[0] - pad, sb[1] - pad, sb[2] + pad, sb[3] + pad]
    cell = CELL
    F = Frame(box, cell, SHRINK * 2)
    while F.W * F.H > MAXPX: cell *= 1.5; F = Frame(box, cell, SHRINK * 2)
    ov, raw = None, None
    for r in s['refs']:
        if r not in G: continue
        m = pmask(F, r, G); ov = m if ov is None else ov & m
        a = F.area(G[r]); raw = a if raw is None else raw & a
    if ov is None or not ov.any(): return 'ok'
    # Oct 28 (HQ 8:40 PM, Brandon: 'might come in handy as a tool'): INFO only, never the verdict: how much of the patch is water,
    # and how much of the two official boundaries' overlap was cut out as not public ground
    ac = cell * cell / 4046.86
    if raw is not None and (raw & (1 - ov)).any(): s.setdefault('info', {})['cut_ac'] = round(float((raw & (1 - ov)).sum()) * ac, 1)
    need = TIGHT_SHRINK + cell
    try: closed = F.area(pad_closed(F.bounds()))
    except Exception as e: LOG.append(f'closed areas: {str(e)[:60]}'); closed = np.zeros_like(ov)  # noqa: BLE001
    open_ = ov & (1 - closed)
    if not (dt(open_) * cell >= need).any(): return 'closed' if closed.any() else 'ok'
    wg = nhd_water(box, live=live)   # Oct 28 11 PM: the row's own box (the tiles the water job saves), not the frame's wider margin (a missing margin tile = 'not checked' with every needed tile saved)
    if wg is None: return 'not checked'
    water = F.area(wg)
    s.setdefault('info', {})['water_pct'] = round(100.0 * float((ov & water).sum()) / max(1.0, float(ov.sum())))
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


def water_date(s):
    """Rule 13: a spot whose water came from the saved copy says so, with that copy's date."""
    if WATER_MARK:
        m = min(WATER_MARK)
        if m.startswith('NRCan NHN file'):   # Canada (kpc_water_ca.py)
            s.setdefault('map_dates', {})['water'] = m + " (Natural Resources Canada's National Hydro Network, Open Government Licence - Canada)"; WATER_MARK.clear(); return
        s.setdefault('map_dates', {})['USGS water'] = ((m.replace('USGS NHD (second service) ', 'USGS NHD second service, read ') + ' (the main USGS water map did not answer)') if m.startswith('USGS NHD (second')
                                                       else (m + ' (the same NHDPlus HR water, from USGS\'s download files)') if m.startswith('USGS NHDPlus HR file')
                                                       else ('saved copy of the USGS map, read ' + m))
        WATER_MARK.clear()
    elif isinstance(s.get('map_dates'), dict): s['map_dates'].pop('USGS water', None)   # read live this time



def _fers_links_root():
    return pathlib.Path(__file__).resolve().parent.parent.parent


def official_agency_outlines(refs, root=None):
    """True when every park already has an official government or agency outline in the key.
    The key source layer (PAD-US, CPCAD, provincial / Parks Canada maps, state agency layers)
    is government or public land, so no separate ownership source is required. Point-circle
    and approximate parks are not official agency outlines; they become an approximate 2-fer,
    not a drop."""
    refs = list(refs or [])
    if not refs: return False
    root = str(root or _fers_links_root())
    try:
        from kpc_fers_key_status import status_for, load_key_status
        load_key_status(root)
    except Exception:
        return False  # noqa: BLE001
    pc = PC
    if not pc:
        try:
            p = pathlib.Path(root) / 'data/point-circles.json'
            pc = {r: v for r, v in (json.load(open(p, encoding='utf-8')).get('parks') or {}).items()
                  if v.get('kind') == PC_KIND and v.get('pt') and len(v['pt']) == 2}
        except Exception:
            pc = {}  # noqa: BLE001
    for r in refs:
        if r in pc: return False
        if status_for(r) != 'official': return False
    return True


def no_owner_source(x, root=None):
    """A live candidate with no ownership answer recorded. An official agency outline already
    shows government or public land, so that pair is not held. Point-circle and approximate
    pairs become an approximate 2-fer (not held here). A blank owner whose outline is not
    from an official agency layer and is not an approximate or point-circle outline still
    cannot be a candidate."""
    st = str(x.get('status', ''))
    if not (st.startswith('candidate') or st.startswith('very tight')): return False
    refs = list(x.get('refs') or [])
    if (str(x.get('tier') or '') in ('point-circle', 'approximate') or x.get('approx')
            or any(r in PCT or r in APX_PARKS for r in refs)):
        return False
    if x.get('kind') == 'same land':
        o = str(x.get('owner_here') or '').lower()
        missing = not o or o.startswith(('owner not published', 'unk ', '? '))
    else:
        missing = not x.get('ownership') and not x.get('known')
    if not missing: return False
    if official_agency_outlines(x.get('refs') or [], root=root):
        x['ownership'] = x.get('ownership') or 'public land (official agency outline)'
        x['owner_src'] = x.get('owner_src') or 'official agency outline (government / public land)'
        if x.get('kind') == 'same land' and not str(x.get('owner_here') or '').strip():
            x['owner_here'] = 'government or public land (official agency outline)'
        return False
    return True


def hold_no_owner(spots, root=None):
    n = 0
    for x in spots:
        if no_owner_source(x, root=root):
            x['status'] = 'not sure: no ownership source for this row (an inside or overlapping pair needs one: Brandon Nov 8): a person or the next run checks it'
            x.pop('list', None); n += 1
    return n



SAME_RECORDS_HOLD = ('not sure: both parks join the same official records '
                     '(one place, two park numbers): a person looks')


def join_record_ids(park):
    """Official record ids for one park as (area, source, id) (picture-trace and point-circle ids left out). The area and the
    world source keep two layers' equal numbers apart (PAD-US 3425 is not the CPCAD or a world layer's 3425)."""
    ids = []
    p = park or {}
    raw = p.get('ids') or []
    rows = p.get('m') or p.get('tracts') or []
    if not raw and rows:
        raw = [x[0] for x in rows if isinstance(x, (list, tuple)) and x]
    area = str(p.get('st') or '').split('-')[0]
    for n, i in enumerate(raw):
        if i in (None, '') or str(i).startswith(('apx|', 'pc|')):
            continue
        src = str(rows[n][2]) if area == 'W' and n < len(rows) and isinstance(rows[n], (list, tuple)) and len(rows[n]) > 2 else ''
        ids.append((area, src, str(i)))
    return frozenset(ids)


def identical_record_refs(parks, refs):
    """Groups of parks in this pair that join the exact same non-empty set of official records."""
    by = {}
    for r in refs or []:
        ids = join_record_ids((parks or {}).get(r))
        if not ids:
            continue
        by.setdefault(ids, []).append(r)
    return [v for v in by.values() if len(v) >= 2]


def identical_records_hold(parks, refs):
    """Status string when two parks in the pair join the same official records; else ''."""
    return SAME_RECORDS_HOLD if identical_record_refs(parks, refs) else ''


# Owner rule, 2026-11-10: two parks on the same official records are an APPROXIMATE 2-fer only when both POTA pins are inside
# the shared outline (one place, two park numbers). A pin outside it, or one that cannot be tested, means a likely wrong join: held.
SAME_RECORDS_APX_NOTE = ('Both park numbers join the same official outline and both POTA pins are inside it. Each park\u2019s own boundary is not '
                         'confirmed. Not the official boundary of either park alone: we believe this is a 2-fer, but it needs more research.')
SAME_RECORDS_JOIN_HOLD = ('not sure: both parks join the same official records but a POTA pin is outside the shared outline '
                          '(or cannot be tested): likely a join to fix')


def pin_in_outline(ref, PIN, G):
    """Strict point test (no river / agency exceptions): True or False for a usable pin and an outline, None when it cannot be tested."""
    v = PIN.get(ref)
    if not v or v[1] is None or v[2] is None or ref not in G: return None
    la, lo, d = v[1], v[2], .004
    F = Frame([lo - d, la - d, lo + d, la + d], CELL, 0)
    c, r = F.px([[lo, la]])[0].astype(int)
    return bool(pmask(F, ref, G)[min(max(r, 0), F.H - 1), min(max(c, 0), F.W - 1)])


# KPC owner, 2026-11-10: "both pins inside" alone also passes SEPARATE units of one big record (the Patoka Lake and Salamonie Lake
# recreation-area units, a park and its "Unit"): those parks do not overlap, so they are not 2-fers. A same-record pair is approximate
# only when, on top of both pins inside the shared outline:
#   * the pins are close: at most SAME_RECORDS_NEAR_KM apart. 1 km sits in the gap of the Nov 10 list: the two real pairs are 0.04 km
#     (Chalk Bluff) and 0.48 km (Red Cliffs) apart, the nearest separate units 1.72 km (Salamonie). SAME_FAR's 8 km is far too loose;
#   * and the shared record names both parks with no kind that differs (kpc_fers_guard.same_land_doubt, the same-land test), unless
#     the two pins are on the same spot (SAME_RECORDS_SPOT_KM, about the precision of a POTA pin), where only the kind words differ.
# Otherwise the pair is held as a likely join to fix, with the reason, the parks and the pin distance on the row.
SAME_RECORDS_NEAR_KM = 1.0
SAME_RECORDS_SPOT_KM = 0.1
SAME_RECORDS_UNITS_HOLD = ('not sure: both parks join the same official records and both POTA pins are inside it, but the pins are '
                           'more than 1 km apart (separate units of one big record): likely a join to fix')


def pin_km(a, b, PIN):
    """Great-circle km between two POTA pins; None when either pin is missing."""
    va, vb = PIN.get(a), PIN.get(b)
    if not va or not vb or None in (va[1], va[2], vb[1], vb[2]): return None
    la1, lo1, la2, lo2 = map(math.radians, (float(va[1]), float(va[2]), float(vb[1]), float(vb[2])))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(min(1.0, math.sqrt(h)))


def shared_record_names(parks, grp):
    """Names of the official records the parks in grp share (from their key 'm' rows)."""
    ids = None
    for r in grp:
        s = {i[2] for i in join_record_ids((parks or {}).get(r))}
        ids = s if ids is None else ids & s
    out = []
    for r in grp:
        for q in ((parks or {}).get(r) or {}).get('m') or []:
            if isinstance(q, (list, tuple)) and len(q) > 1 and str(q[0]) in (ids or set()) and q[1] and q[1] not in out: out.append(q[1])
    return out


def same_records_doubt(a, b, parks, PIN):
    """'' when the pair may be an approximate 2-fer; else the reason it is held (pins far apart, or the record does not name both)."""
    d = pin_km(a, b, PIN)
    if d is None or d > SAME_RECORDS_NEAR_KM:
        return SAME_RECORDS_UNITS_HOLD + (f' ({a} and {b}: pins {d:.2f} km apart)' if d is not None else f' ({a} and {b}: a pin cannot be measured)')
    if d <= SAME_RECORDS_SPOT_KM: return ''
    na, nb = (PIN.get(a) or [a])[0], (PIN.get(b) or [b])[0]
    recs = shared_record_names(parks, [a, b]) or ['']
    whys = [FG.same_land_doubt(na, nb, rec) for rec in recs]
    return '' if '' in whys else whys[0]


def same_records_verdict(parks, refs, PIN, G):
    """() when no two parks of the pair join identical records; ('approx', []) when every such park's pin is inside the shared
    outline and every two of them pass same_records_doubt; ('held', [refs whose pin is outside or untestable]) when a pin is not
    inside; ('held', [refs], 'units', why) when the pins are inside but the parks look like separate places. Every call site
    (decide, same-land pass 1 and pass 5) goes through here."""
    grp = sorted({r for g in identical_record_refs(parks, refs) for r in g})
    if not grp: return ()
    out = [r for r in grp if pin_in_outline(r, PIN, G) is not True]
    if out: return ('held', out)
    far, whys = [], []
    for i, a in enumerate(grp):
        for b in grp[i + 1:]:
            why = same_records_doubt(a, b, parks, PIN)
            if why: far += [a, b]; whys.append(why)
    return ('held', sorted(set(far)), 'units', whys[0]) if far else ('approx', [])


def same_records_mark(x, v, parks, PIN):
    """Write the verdict on a row. True = held (the caller stops)."""
    refs = list(x.get('refs') or [])
    x['shared_records'] = sorted({i[2] for r in refs for i in join_record_ids((parks or {}).get(r))})
    if v[0] == 'held':
        x['person_review'] = True; x['join_check'] = True; x['names'] = {r: (PIN[r][0] if r in PIN else r) for r in refs}
        if len(v) > 2 and v[2] == 'units':   # pins inside but far apart under different names: separate units of one record
            x['status'] = v[3] if len(v) > 3 and v[3] else SAME_RECORDS_UNITS_HOLD; x['separate_units'] = v[1]
            x['pin_km'] = {f'{a}+{b}': (round(d, 2) if d is not None else None) for i, a in enumerate(v[1]) for b in v[1][i + 1:] for d in [pin_km(a, b, PIN)]}
            x.pop('pin_outside', None)
        else:
            x['status'] = SAME_RECORDS_JOIN_HOLD; x['pin_outside'] = v[1]
        return True
    x['approx'] = True; x['same_records'] = True; x['approx_note'] = SAME_RECORDS_APX_NOTE
    for k in ('person_review', 'join_check', 'pin_outside', 'separate_units', 'pin_km'): x.pop(k, None)
    return False


def decide(s, parks, G, LN, PIN, today, saved_only, st_of):
    """Pass 3: the rules decide what a spot that passed all three geometry passes is."""
    refs = s['refs']
    s['checked'] = today
    s['map_dates'] = {r: MAPDATE.get(r) or ('saved copy' if r in saved_only else 'official line (trails bot)' if r in LN else 'Kentucky official file' if REGION == 'ky' else 'saved copy') for r in refs}
    # Nov 6 / Part A v2: area/same-land follow key PIN/approximate PER STATE (weakest if area unknown)
    _areas = {r: (st_of(r) if callable(st_of) else '') for r in refs}
    # A point-circle or approximate half is an approximate 2-fer (pc_tag), not a drop.
    # Two point-circles can still be an approximate 2-fer. A key PIN with no circle is still dropped.
    _kr = [r for r in refs if r not in PCT and r not in APX_PARKS]
    _lines = [r for r in refs if r in LN and r not in G]   # trail / river rows: the park(s) tested by their line (the rest are area halves)
    _klm = key_line_match(_kr, s.get('kind'), areas=_areas, lines=_lines) if _kr else ''
    if _klm:
        s['status'] = _klm; return
    if s.get('line_short'):   # Nov 11 (KPC owner): the saved line is shorter than 25 m in all = a broken copy, not the trail
        s['status'] = ('not sure: our saved copy of the official line for ' + ', '.join(f'{r} is only {m} m long in all' for r, m in sorted(s['line_short'].items()))
                       + ' (a broken copy, not the trail): fix the line, then run again')
        s['names'] = {r: (PIN[r][0] if r in PIN else r) for r in refs}; return
    _sv = same_records_verdict(parks, refs, PIN, G)
    if _sv and same_records_mark(s, _sv, parks, PIN): return
    _held = [WSR_HELD.get(r) or saved_missing_why(r) for r in refs if WSR_HELD.get(r) or saved_missing_why(r)]
    if _held:   # owner rule, 2026-11-10: no saved copy for a saved-copy-only map = held, never tested without it
        s['status'] = 'not sure: ' + '; '.join(sorted(set(_held))); s['names'] = {r: (PIN[r][0] if r in PIN else r) for r in refs}; return
    # Approximate or point-circle halves stay in the approximate 2-fer tier (they are not held).
    # pc_tag writes the public note and thinner-card fields.
    load_key_status()
    from kpc_fers_key_status import status_for as _status_for
    _apx = [r for r in refs if _status_for(r, _areas.get(r)) == 'approximate' or r in APX_PARKS or r in PCT]
    if _apx:
        s['approx'] = True
        s['approx_refs'] = _apx
        s['approx_note'] = APX_NOTE
    if _sv: s['approx'] = True; s['approx_note'] = SAME_RECORDS_APX_NOTE   # both pins inside the shared outline: approximate tier
    s['pins_inside'] = {r: pin_inside(r, PIN, G, LN) for r in refs}   # information only: pins never count (rule 6)
    if any(r in saved_only for r in refs):
        s['fresh'] = 'saved copy only for ' + ', '.join(r for r in refs if r in saved_only)
        s['members_line'] = 'saved outline, not read live today'   # chat 8 KY note 4
    notes = sorted({n for r in refs for n in ACC.get(r, ())} | {"check the agency's closures and seasons before you go"})   # pre-flight fix 14
    s['notes'] = notes
    for k in ('list', 'ownership', 'ground', 'private_part', 'unknown_part', 'corps_land', 'owner_src', 'info', 'known', 'mixed_owners'): s.pop(k, None)
    pk = tuple(sorted(refs))
    if pk in KNOWN_LIVE:   # Brandon Oct 28 8:35 PM: a permanent known answer (he activates it in person): the whole overlap, live
        s['known'] = KNOWN_LIVE[pk]; s['ownership'] = 'known answer: ' + KNOWN_LIVE[pk]
        s['status'] = 'candidate' if not s.get('fresh') else 'candidate (saved outline only)'
        s['access'] = nearest_access(s, st_of)
        try: s['access_pin'] = access_pin(s, G, LN, st_of)
        except Exception as e: LOG.append(f"pin {s['id']}: {str(e)[:60]}")  # noqa: BLE001
        s['maps'] = [[r, map_link(r, PIN)] for r in refs]; s['names'] = {r: PIN[r][0] for r in refs}
        line_rows(s, LN); how_checked(s, parks, PIN); return
    if REGION == 'ky':
        for a in range(len(refs)):
            for b in range(a + 1, len(refs)):
                if (refs[a], refs[b]) in KY_DROP: s['status'] = 'dropped: ' + KY_DROP[(refs[a], refs[b])]; return
    if any(r in OWNED_FAIL for r in refs): s['status'] = 'not sure: the agency ownership map did not answer'; return
    if s.get('kind') == 'river' and not s.get('water_route') and any((x, y) in WATER_UNCHECKED for x in refs for y in refs if x != y): s['water_unchecked'] = True   # Oct 31 (Fable #22)
    if s.get('water_unchecked'):
        s['status'] = 'not sure: water not checked (the USGS water map did not answer for this river bank): run again'; s['names'] = {r: PIN[r][0] for r in refs}; return
    if s['kind'] != 'area' and all(water_route(r, LN, PIN) for r in refs):   # Oct 28 (chat 8 KY 4, rule 9): two water routes alone share only the water
        s['status'] = 'water only: boat or kayak'; s['list'] = '🚤 Water only: boat or kayak'; s['names'] = {r: PIN[r][0] for r in refs}; s['maps'] = [[r, map_link(r, PIN)] for r in refs]; return
    if s.get('masked_out') and len(refs) > 2:   # Oct 28 (HQ 9:20 AM, chat 8: Rockcastle River WMA 3-fer, 28 ac): the agency's own map says the
        # three-way patch is not its land = no 3-fer THERE (rule 14b); each pair's own overlap is its own row and stands
        s['status'] = ('dropped: the ' + ' / '.join(OWNMAP.get(k, k) for k in s['masked_out']) + ' shows no agency land on the patch all '
                       + str(len(refs)) + ' share (rule 14b): the pairs stand as their own rows'); return
    if s.get('masked_out'):   # Oct 27 (Fable #4) was NOT SURE; Brandon Oct 29 8:07 AM ruled: 'if state owned inside a federal park no
        # overlap, not a 2fer ... if federal claims all the land (a national park + a state park on it) 2fer'. The patch sits inside
        # the federal line but the agency's own land map shows none of it as theirs = someone else's land inside the line = DROP
        s['status'] = ('dropped: inside the federal boundary, but the ' + ' / '.join(OWNMAP.get(k, k) for k in s['masked_out'])
                       + " shows this patch is not the agency's own land (state or other land inside a federal boundary is not an overlap; Brandon Oct 29)")
        s['map_note'] = "the agency land map may be out of date: if the agency does own this patch, it is a 2-fer"
        s['names'] = {r: PIN[r][0] for r in refs}; s['maps'] = [[r, map_link(r, PIN)] for r in refs]; return
    if REGION != 'ky' and any(r in LOWCONF for r in refs):   # pre-flight fix 9 (Oct 28: not in Kentucky: its outlines come from Kentucky's own files, not the US key join the score is about)
        s['status'] = 'not sure: low-confidence outline for ' + ', '.join(PIN[r][0] for r in refs if r in LOWCONF) + ' (check the join)'; return
    if s['kind'] == 'area' and refs[0].startswith('US-'):
        try: lc = land_check(s, G)
        except Exception as e: lc = 'ok'; LOG.append(f"land check {s['id']}: {str(e)[:60]}")  # noqa: BLE001
        if lc == 'water': s['status'] = 'water only: boat or kayak'; s['list'] = '🚤 Water only: boat or kayak'; return
        if lc == 'closed': s['status'] = 'dropped: only inside an area closed to the public (no entry)'; return
        if lc == 'not checked': s['status'] = 'not sure: water not checked (the USGS water map did not answer): run pass 5'; s['names'] = {r: PIN[r][0] for r in refs}; return
    if s['kind'] == 'area' and refs[0].startswith('CA-'):
        # Oct 28 11:19 PM (Brandon: Canada's water): the saved NRCan NHN tiles (kpc_water_ca.py); none saved = never guess it is land
        try: lc = land_check(s, G, live=False)
        except Exception as e: lc = 'not checked'; LOG.append(f"land check {s['id']}: {str(e)[:60]}")  # noqa: BLE001
        if lc == 'water': s['status'] = 'water only: boat or kayak'; s['list'] = '🚤 Water only: boat or kayak'; return
        if lc == 'closed': s['status'] = 'dropped: only inside an area closed to the public (no entry)'; return
        if lc == 'not checked': s['status'] = 'not sure: water not checked (no saved Canadian water tile here yet: run the Canada water job)'; s['names'] = {r: PIN[r][0] for r in refs}; return
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
    s['maps'] = [[r, map_link(r, PIN)] for r in refs]
    s['names'] = {r: PIN[r][0] for r in refs}
    line_rows(s, LN)
    how_checked(s, parks, PIN)


MAPFIX = {'US-0703': 'https://www.nps.gov/fodo/planyourvisit/maps.htm'}   # Oct 27 (chat 8 re-check): the file had a POTA page
WEB = {}
KYOFF = {}


def map_link(r, PIN):
    """The official map / page for a park: a fixed one, then parkinfo-web.json's checked map, then the park's own page;
    never a POTA page (not an agency map)."""
    if r in MAPFIX: return MAPFIX[r]
    if not KYOFF:
        try: KYOFF.update({x['c']: x.get('off') for x in json.load(open('kpc-ky-data.json'))['parks'] if x.get('off')})
        except Exception: pass  # noqa: BLE001
        KYOFF['_'] = ''
    if KYOFF.get(r) and str(KYOFF[r]).startswith('http') and 'pota.app' not in KYOFF[r]: return KYOFF[r]   # Kentucky's hand-checked official map
    if not WEB:
        try: WEB.update(json.load(open('data/parkinfo-web.json'))['parks'])
        except Exception: WEB['_'] = {}  # noqa: BLE001
    w = WEB.get(r) or {}
    ok = lambda u: u and str(u).startswith('http') and 'pota.app' not in str(u)
    if ok(w.get('map')) and (w.get('map_check') or {}).get('map', 'ok') == 'ok' and not w.get('map_hold'): return w['map']
    if ok((PIN.get(r) or ('', None, None, ''))[3]): return PIN[r][3]   # Nov 9 PM: KeyError 'CA-2062' stopped pass 3 (run 42649544758)
    if ok(w.get('web')): return w['web']
    return ''


LDATE = {}


def line_rows(s, LN):
    """Chat 8 fix 3: every line row says which line was used and its date; national historic trail lines are approximate."""
    if s['kind'] == 'area': return
    if not LDATE:
        for f in pathlib.Path('data/status').glob('*.json'):
            try: LDATE.update({k: v for k, v in (json.load(open(f)).get('changed') or {}).items() if k.startswith('data/trails/')})
            except Exception: pass  # noqa: BLE001
        LDATE['_'] = ''
    src = {}
    for r in s['refs']:
        if r in LN:
            nht = LN[r].get('type') in ('NHT',) or re.search(r'historic trail', str(LN[r].get('by')) + ' ' + str(s.get('names', {}).get(r, '')), re.I)
            live = str(LN[r].get('date', '')).startswith('read live')
            src[r] = {'line': 'live agency layer' if live else f"data/trails/{r}.json", 'by': LN[r].get('by') or 'official layer (trails bot)',
                      'date': LN[r].get('date') or LDATE.get(f'data/trails/{r}.json') or 'not recorded', **({'districts': LN[r]['districts']} if LN[r].get('districts') else {}),
                      **({'note': 'approximate line (national historic trail, about 1:100,000)'} if nht else {})}
    s['line_source'] = src
    ap = [r for r, v in src.items() if 'note' in v]
    if len(src) > 1 and len(ap) == len(src): s['note'] = 'approximate line: both trail lines are approximate'
    elif ap: s['note'] = 'approximate line: ' + ', '.join(str(s.get('names', {}).get(r) or r) for r in ap)   # HQ Oct 28: cards say so


def how_checked(s, parks, PIN):
    """Chat 8 fix 4 + KR-4: the owner shown is the owner of the land AT THE SPOT (inside the WMA), never the land around it."""
    refs = s['refs']
    if REGION != 'ky' or 'US-4484' not in refs: return
    bits = []
    for r in refs:
        if r == 'US-4484': continue
        o = park_owner(r, parks)
        if r in KY_FS_MANAGED: bits.append(f"{PIN[r][0]}: owned by the U.S. Forest Service, managed by KDFWR (KDFWR's own page)")
        elif o == '' and any(str(i).startswith('bwma|') for i in parks[r]['ids']): bits.append(f"{PIN[r][0]}: owner not published by KDFWR")
    s['owner_here'] = 'U.S. Forest Service (Forest Service ownership map, Basic Ownership, 2015)'
    s['how_checked'] = '; '.join(bits + ['the spot itself is Forest Service-owned land']) if bits else 'the spot is Forest Service-owned land'


MARK_T = [time.time()]
def mark(what):
    """Oct 28 (pass-5 speed-up): one log line per stage: seconds since the last mark + the process's peak memory so far."""
    try:
        import resource
        mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024
    except Exception: mb = -1  # noqa: BLE001
    now = time.time(); print(f'stage: {what}: {now - MARK_T[-1]:.0f} s, peak {mb} MB', flush=True); MARK_T.append(now)


def tidy_rows(spots, PIN, today):
    """Chat 8's Kentucky final look (Oct 27 ~2 PM): (1) one AREA pair with several separate patches (a wild river corridor x
    Daniel Boone: 6 rows) = ONE row with up to 3 pins, like the trail rows (KR-1); (5) a 3-fer (or more) and the pair rows that
    lie on its patch = ONE patch: the pairs fold into the n-fer row; (2) 'same land' rows carry the checked date and both map
    links like every other row."""
    live = lambda x: str(x.get('status', '')).startswith(('candidate', 'very tight'))
    # (0) Oct 30 (chat 8's PRIORITY BUG: 'merged into one row: <its own id>', 643 extra rows in 32 states, MA one pair 113x): a rerun
    #     added the same row (same id) again, and the merge below then stubbed the copies into themselves, more every run. ONE row
    #     per id: a live row first, then not sure / water only, then anything else; self-stubs and copies are removed.
    _rank = lambda x: (0 if live(x) else 1 if str(x.get('status', '')).startswith(('not sure', 'water only')) else
                       3 if str(x.get('status', '')) .startswith('merged into one row: ' + str(x.get('id'))) else 2)
    _best = {}
    for x in spots:
        k = x.get('id')
        if k is None: continue
        if k not in _best or _rank(x) < _rank(_best[k]): _best[k] = x
    spots[:] = [x for x in spots if x.get('id') is None or _best.get(x.get('id')) is x]
    # (5) n-fers first. RULE 11 (HQ + chat 8, Oct 28 7:55 AM): the n-fer patch is the ground ALL the parks share, listed once;
    # every PAIR's own overlap OUTSIDE it stays its own 2-fer row (never absorbed: Clifty x Daniel Boone, 12,364 ac, was hidden
    # inside a 592-ac 3-fer row). A pair row folds into the n-fer only when its patch IS the shared patch (same place, not bigger).
    size = lambda x: (x.get('acres') or 0) if x.get('kind') == 'area' else (x.get('len_m') or 0)
    for x in spots:   # a second pass 5 on the same file (a worker rerun) must not list the same pairs twice
        for k in ('pairs_here', 'pairs_around', 'nfer_here'): x.pop(k, None)
    nf = [x for x in spots if live(x) and len(x['refs']) > 2 and x.get('kind') in ('area', 'river', 'trail')]
    for n in nf:
        for x in spots:
            if x is n or not live(x) or len(x['refs']) != 2 or x.get('kind') != n.get('kind') or not set(x['refs']) <= set(n['refs']): continue
            if not inter(sbox(x), sbox(n), 0.0005): continue
            if size(x) <= size(n) * 1.05 + 0.05:
                x['status'] = 'merged into one row: ' + n['id'] + ' (the same patch as the ' + str(len(n['refs'])) + '-fer)'
                n.setdefault('pairs_here', []).append('+'.join(x['refs']))
            else:
                x.setdefault('nfer_here', []).append(n['id']); n.setdefault('pairs_around', []).append('+'.join(x['refs']))   # its own bigger overlap stays a row
    # (1) one row per pair (any size of refs) and kind, for every LIVE row (Oct 28 chat 8: de-dupe by sorted refs + kind)
    by = {}
    for x in spots:
        if live(x) or str(x.get('status', '')).startswith('water only'): by.setdefault((tuple(sorted(x['refs'])), x.get('kind'), 'water' if str(x.get('status', '')).startswith('water only') else 'land'), []).append(x)
    for (pair, kind, _w), ss in by.items():   # a water-only row (a river channel) never folds into the land row of the same pair
        if len(ss) < 2: continue
        if kind == 'area': ss.sort(key=lambda x: (-(x.get('wide_m') or 0), -(x.get('acres') or 0)))
        else: ss.sort(key=lambda x: -(x.get('len_m') or 0))
        main = ss[0]
        pins = [x.get('access_pin') for x in ss if x.get('access_pin') and str(x['access_pin'].get('from', '')).split(' ')[0] != 'none']
        pins.sort(key=lambda q: (q.get('from') != 'road', q.get('walk_m') or 1e9))
        main['pins'] = pins[:3]
        if kind == 'area': main['patches'] = len(ss); main['acres_all'] = round(sum(x.get('acres') or 0 for x in ss), 1)
        else: main.setdefault('len_main', main.get('len_m') or 0); main['stretches'] = len(ss); main['len_m'] = main['len_main'] + sum(x.get('len_m') or 0 for x in ss[1:])
        xs = [b for x in ss for b in (x.get('box') or [])]
        if xs: main['box'] = [min(xs[0::4]), min(xs[1::4]), max(xs[2::4]), max(xs[3::4])]
        for x in ss[1:]: x['status'] = 'merged into one row: ' + main['id']
    # (3) Oct 28 (chat 8 KY 5 / OH): the same pair NOT SURE in several places (Kentenia x Daniel Boone 5 slivers, Burr Oak x
    #     Wayne 5 rows) = ONE not-sure row with the count; the others say which row carries it
    byn = {}
    for x in spots:
        if str(x.get('status', '')).startswith('not sure'): byn.setdefault((tuple(sorted(x['refs'])), x.get('kind'), str(x.get('status'))[:60]), []).append(x)
    for k, ss in byn.items():
        if len(ss) < 2: continue
        ss.sort(key=lambda x: -((x.get('acres') or 0) + (x.get('len_m') or 0)))
        main = ss[0]; main['places'] = len(ss)
        xs = [b for x in ss for b in (x.get('box') or [])]
        if xs: main['box'] = [min(xs[0::4]), min(xs[1::4]), max(xs[2::4]), max(xs[3::4])]
        for x in ss[1:]: x['status'] = 'merged into one row: ' + main['id'] + ' (the same not-sure pair, shown once)'
    # (2) same land rows
    for x in spots:
        if x.get('kind') == 'same land':
            x.setdefault('checked', today)
            x['maps'] = [[r, map_link(r, PIN)] for r in x['refs']]


def one_row_per_line_pair(spots, st_of, G, LN):
    """KR-1 (Brandon Oct 27 8:10 AM): a trail or river line with a park = ONE row per pair, up to 3 pins nearest a road first;
    the other stretches are folded into it (status 'merged into …', never shown on their own)."""
    by = {}
    for s in spots:
        if s['kind'] != 'area' and str(s.get('status', '')).startswith('candidate'): by.setdefault(tuple(s['refs']), []).append(s)
    for pair, ss in by.items():
        if len(ss) < 2: continue
        ss.sort(key=lambda x: -(x.get('len_m') or 0))
        main = ss[0]
        pins = [x.get('access_pin') for x in ss if x.get('access_pin') and x['access_pin'].get('from') != 'none']
        pins.sort(key=lambda p: (p.get('from') != 'road', p.get('walk_m') or 1e9))
        main['pins'] = pins[:3]
        main.setdefault('len_main', main.get('len_m') or 0)   # Nov 11: the row's OWN stretch, kept apart before the others are added
        main['stretches'] = len(ss); main['len_m'] = main['len_main'] + sum(x.get('len_m') or 0 for x in ss[1:])
        xs = [b for x in ss for b in (x.get('box') or [])]
        if xs: main['box'] = [min(xs[0::4]), min(xs[1::4]), max(xs[2::4]), max(xs[3::4])]
        for x in ss[1:]: x['status'] = 'merged into one row: ' + main['id']


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
        # Nov 9 (Quality: blank CPCAD owners): 37,961 of 60,426 saved Canadian records have no 'ow' text (the provincial layers);
        # their manager / source name says who holds them ('Alberta Parks (Government of Alberta)')
        os_ = {(lambda r: owner_of_text(r.get('ow')) or owner_of_text(r.get('mg')) or owner_of_text(r.get('src') or r.get('ty')))(by.get(str(i), {})) for i in p['ids']} - {''}
        OWN_CA[ref] = next(iter(os_)) if len(os_) == 1 else '?'




PINS = {}


def known_ok():
    """HQ Oct 27 3:21 PM: no all-US / Canada run until Kentucky's known river + trail pairs come out (kpc_fers_known.py)."""
    try: k = json.load(open(OUT / 'known-answers.json'))
    except Exception: return False, 'no known-answers check yet (run Kentucky first)'  # noqa: BLE001
    fresh = k.get('date', '') >= time.strftime('%Y-%m-%d', time.localtime(time.time() - 7 * 86400))
    return bool(k.get('pass')) and fresh, f"known answers {'PASS' if k.get('pass') else 'FAIL'} on {k.get('date')}: {k.get('found')} of {k.get('required')}"


def water_prefetch():
    """Oct 28 (HQ): fetcher stage, after passes 1 + 2: read (and keep in WATER_STORE) the USGS water tiles around every
    spot this area has, so the worker's water check works from the saved copy if USGS is down later that night."""
    import glob
    boxes = []
    for fn in sorted(glob.glob('data/fers/US-*.json')):
        st = pathlib.Path(fn).stem
        if ONLY and st not in ONLY and st[3:] not in ONLY: continue
        try: d = json.load(open(fn))
        except Exception: continue  # noqa: BLE001
        for x in d.get('spots') or []:
            b = x.get('box')
            if not b and x.get('shape'):
                xs = [p[0] for p in x['shape']]; ys = [p[1] for p in x['shape']]; b = [min(xs), min(ys), max(xs), max(ys)]
            if b: boxes.append([b[0] - .01, b[1] - .01, b[2] + .01, b[3] + .01])
    tiles = sorted({(i, j) for b in boxes for i in range(int(math.floor(b[0] / .1)), int(math.floor(b[2] / .1)) + 1)
                    for j in range(int(math.floor(b[1] / .1)), int(math.floor(b[3] / .1)) + 1)})
    for i, j in tiles:
        if late(): break
        nhd_water([i * .1 + .01, j * .1 + .01, i * .1 + .09, j * .1 + .09])
    n = len(list(pathlib.Path(WATER_STORE).glob('*.json.gz'))) if WATER_STORE else 0
    notice('2-fer water copy', f"{len(tiles)} water tiles near {len(boxes)} spots: {WATER_N['live']} read live, {WATER_N['saved']} from the saved copy, "
                               f"{WATER_N['missing']} missing (live down and no saved copy); {n} tiles kept")


def main():
    if HARD_END: _arm()   # Nov 9 PM: the step's hard end is armed from the start (exit 3 = red, never a silent time-out)
    if os.environ.get('WATER_PREFETCH') == '1': return water_prefetch()
    # Nov 8 (Brandon t808u): only areas declared ready (ownership + management). Skip others with a clear log; no silent world run.
    global ONLY
    _run_areas = sorted(ONLY) if ONLY else (
        ['W-*'] if REGION == 'world' else (['US-KY'] if REGION == 'ky' else [])
    )
    if REGION == 'world' and not ONLY:
        msg = ('2-fer ready-areas: SKIP world run — no STATES set, and W-* is not on '
               '.github/fers-ready-areas.json (needs ownership + management).')
        print(f'::notice title=2-fer ready-areas::{msg}', flush=True)
        notice('2-fer bot', msg); return
    if _run_areas:
        # Expand a bare W-* refuse; concrete W-AU etc. go through filter_areas
        if _run_areas == ['W-*']:
            msg = ('2-fer ready-areas: SKIP W-* — world countries are not declared ready '
                   '(ownership + management required; Brandon Nov 8 / t808u).')
            print(f'::notice title=2-fer ready-areas::{msg}', flush=True)
            notice('2-fer bot', msg); return
        _allow, _skip = FREADY.filter_areas(_run_areas, log=lambda m: print(f'::notice title=2-fer ready-areas::{m}', flush=True))
        if _skip:
            print(f'::notice title=2-fer ready-areas::{FREADY.skip_message(_skip)}', flush=True)
            notice('2-fer bot', FREADY.skip_message(_skip))
        if not _allow:
            notice('2-fer bot', 'STOPPED: no ready areas left in this run (see 2-fer ready-areas notices).'); return
        if ONLY:
            ONLY = set(_allow)
    # Oct 27 (Fable's assembly-line review A5): the park list + trail lines live in KPC-Data (Step B); without them a pass would
    # run and quietly drop every trail pair. Stop instead, loudly.
    if REGION != 'world':
        for need in ('data/parkinfo', 'data/trails'):
            if not pathlib.Path(need).is_dir() or not any(pathlib.Path(need).iterdir()):
                notice('2-fer bot', f'STOPPED: {need} is missing (KPC-Data overlay not laid in: run kpc_overlay.sh first)'); return
    PIN = pins()
    PINS.update(PIN)
    if REGION == 'na' and not ONLY and PASS == 1:
        ok, why = known_ok()
        if not ok: notice('2-fer bot', f'STOPPED before the all-US / Canada run: {why}. Fix and rerun Kentucky first.'); return
    parks, skip = official_parks(PIN)
    drop_blocked(parks)
    PINS.update(PIN)   # Nov 9 PM: official_parks blanks the key's 'pin00' pins (no coordinates)
    RET = retired()   # rule 13: retired POTA numbers drop out
    parks = {r: p for r, p in parks.items() if r not in RET}
    LN = {r: v for r, v in trail_lines().items() if r not in RET}
    if REGION in ('ky', 'na'): live_lines(LN)
    if REGION == 'na': wsr_corridors(parks, PIN, LN)
    # Oct 29 (FINAL rules R5 + example 'Channahon SP x I&M Canal State Trail = test with the 100-ft trail rule, not as two areas'):
    # a TRAIL park (not a wild river: R6 keeps the corridor) that has an official trail LINE is tested by its line (public land
    # within 100 ft of the trail), even when the key also joined a corridor polygon for it
    if REGION != 'ky':
        TRAIL_BY_LINE = sorted(r for r in parks if r in LN and LN[r].get('kind') == 'trail' and r in PIN
                               and re.search(r'\btrail\b', f'{PIN[r][0]} {PIN[r][4]}', re.I) and not re.search(r'wild and scenic|river', str(PIN[r][4]), re.I))
        for r in TRAIL_BY_LINE: parks.pop(r, None); OWNED.pop(r, None)
        if TRAIL_BY_LINE: LOG.append(f'{len(TRAIL_BY_LINE)} trail parks tested by their official line (R5), not their polygon: ' + ', '.join(TRAIL_BY_LINE[:10]))
    owners(parks); ca_owners(parks)
    for ref in LN:
        # Oct 27: a trail that CROSSES Kentucky counts in the Kentucky run even when POTA files it under another state
        # (Trail of Tears, Lewis and Clark NHT): the Kentucky region takes any line whose box touches the state
        kyl = REGION == 'ky' and ref in PIN and not PIN[ref][5].startswith(('W-', 'CA-')) and (lambda b: b[0] < -81.96 and b[2] > -89.6 and b[1] < 39.15 and b[3] > 36.49)(bbox_lines(LN[ref]['lines']))
        if ref not in parks and ref in PIN and (REGION == 'world') == PIN[ref][5].startswith('W-') and (kyl or (REGION == 'ky') == (PIN[ref][5] == 'KY')):
            st = 'KY' if kyl else PIN[ref][5]
            parks[ref] = {'st': st if st.startswith('CA-') else 'US-' + st, 'ids': [], 'names': {}}
    st_of = lambda r: parks[r]['st'] if r in parks else ''
    if ONLY:
        # Oct 30 (chat 2, from the wave-2 recheck: IA lost both Mormon Pioneer NHT pairs, NM every Old Spanish NHT pair): a LINE park
        # (a national trail crossing many states) is filed under ONE state by POTA, so a one-state area dropped it whenever that
        # state was not the area. Since the areas were cut to 1/3 size this hit IA / NM / ME / MN. A line park now stays when its
        # line passes through the area (the box of the area's own park pins, padded ~20 km); its rows are filed under the area's state.
        # only parks with their OWN outline set the box: a line park's POTA pin can sit far away (the Appalachian Trail is filed under
        # Maine with its pin in Georgia, which once stretched Maine's box to Georgia)
        _in = [PIN[r] for r, p in parks.items() if (p['st'] in ONLY or p['st'][3:] in ONLY) and p.get('ids') and r not in LN and r in PIN and PIN[r][1] is not None]
        _ab = [min(v[2] for v in _in) - .2, min(v[1] for v in _in) - .2, max(v[2] for v in _in) + .2, max(v[1] for v in _in) + .2] if _in else None
        AREA_BOX[:] = _ab or []
        def _crosses(r):
            if not _ab or r not in LN or (parks.get(r) or {}).get('ids'): return False
            return any(_ab[0] <= q[0] <= _ab[2] and _ab[1] <= q[1] <= _ab[3] for l in LN[r]['lines'] for q in l[::5] + l[-1:])
        # Oct 31 (chat 2, Delaware lost a cross-border area pair): a one-state area also needs its NEIGHBOURS' parks that sit at its edge,
        # or a pair across a state line (a Delaware park x a Pennsylvania park) is found by neither state's run. A park filed under
        # another state comes in when its POTA pin lies inside this area's box (its own state's run still owns its other rows).
        def _near(r):
            v = PIN.get(r)
            if not (_ab and (parks.get(r) or {}).get('ids')): return False
            if v and v[1] is not None and _ab[0] <= v[2] <= _ab[2] and _ab[1] <= v[1] <= _ab[3]: return True
            # Oct 31 (Fable #20): or one of its OWN record part boxes (rule B12, from the key) reaches into this area (a national forest
            # whose pin is a state away)
            return any(not (b_[2] < _ab[0] or b_[0] > _ab[2] or b_[3] < _ab[1] or b_[1] > _ab[3]) for bs in (CLIP.get(r) or {}).values() for b_ in bs if len(b_) == 4)
        _x = [r for r, p in parks.items() if not (p['st'] in ONLY or p['st'][3:] in ONLY) and (_crosses(r) or _near(r))]
        parks = {r: p for r, p in parks.items() if p['st'] in ONLY or p['st'][3:] in ONLY or r in _x}
        if _x: LOG.append(f'{len(_x)} parks filed under another state but crossing / at the edge of this area kept: ' + ', '.join(_x[:8]))
    counts = {'pass': PASS, 'cell_m': CELL, 'official parks': len(parks), 'left out': skip, 'pairs tested': 0, 'with official lines': sum(1 for r in LN if r in parks)}
    today = time.strftime('%Y-%m-%d')
    old = {}
    for f in OUT.glob('*-*.json'):
        if re.fullmatch(FILES, f.stem):
            try: old[f.stem] = json.load(open(f))
            except Exception: pass  # noqa: BLE001

    if PASS == 6:   # Oct 27 (HQ 5:36 PM): ONLY the live boundary lines around each area spot (Kentucky after its run; later runs do it in pass 5)
        files = {st: d for st, d in old.items() if (not ONLY or st in ONLY or st[3:] in ONLY)}
        lw = [x for d in files.values() for x in d.get('spots', []) if x.get('kind') in ('area', 'trail') and not str(x.get('status', '')).startswith('dropped')]
        refs = sorted({r for x in lw for r in x['refs'] if r in parks and parks[r]['ids']})
        G, bad = ky_geom(parks, refs) if REGION == 'ky' else download(parks, refs, DET, PREC)
        inject_apx_geom(G, parks, refs)
        counts['spots given their boundary lines'] = add_lines(files, G, today)
        counts['trail stretches given their true zone'] = add_zones(files, G, PIN, today)
        if REGION == 'ky':
            try: ky_drift(parks, [(x.get('id'), x.get('box')) for x in lw if 'US-4484' in x['refs'] and x.get('box')])
            except Exception as e: LOG.append(f'drift: {str(e)[:80]}')  # noqa: BLE001
        for st, d in files.items():
            d['spots'] = slim(d.get('spots', []))
            save_json(file_of(st), pc_tag(d), indent=None)  # Nov 2: spot files compact everywhere (indent made Alaska 824 MB)
    elif PASS == 5:   # Oct 27 (chat 8 KY note 3): re-check water for the decided area spots + tidy the rows; no new geometry passes
        files = {st: d for st, d in old.items() if (not ONLY or st in ONLY or st[3:] in ONLY)}
        mark('pass 5 start')
        want = lambda x: x.get('kind') == 'area' and str(x.get('refs', [''])[0]).startswith(('US-', 'CA-')) and str(x.get('status', '')).startswith(('candidate', 'very tight', 'not sure: water not checked'))
        cand = [x for d in files.values() for x in d.get('spots', []) if want(x)]
        same = [x for d in files.values() for x in d.get('spots', []) if x.get('kind') == 'same land' and str(x.get('status', '')).startswith('candidate')]
        refs = sorted({r for x in cand + same for r in x['refs'] if r in parks and parks[r]['ids']})
        if REGION == 'ky': G, bad = ky_geom(parks, refs)
        else: G, bad = download(parks, refs, DET, PREC)
        inject_apx_geom(G, parks, refs)
        mark(f'geometry of {len(refs)} parks read')
        n = {'checked': 0, 'water only': 0, 'still not checked': 0}
        # Oct 28 (Southeast: only 17 of ~400 rows checked before pass 5's time ran out, the rest waiting on the USGS map that was down):
        # rows whose water tiles are ALL saved go first (seconds each); rows that would have to ask the live map go last
        def _saved_all(x):
            b = sbox(x); pad = .002
            if not b or not WATER_STORE: return False
            return all(_wpath(i, j).exists() for i in range(int(math.floor((b[0] - pad) / .1)), int(math.floor((b[2] + pad) / .1)) + 1)
                       for j in range(int(math.floor((b[1] - pad) / .1)), int(math.floor((b[3] + pad) / .1)) + 1))
        # Nov 4 PM fix bundle item 4: saved-first as before, then by place (0.5-degree cells, west to east), so the water tiles are
        # read once per place and the far ones are dropped before each spot (evict), not all kept to the end
        _cell = lambda x: (lambda b: (int(math.floor(b[1] / .5)), int(math.floor(b[0] / .5))) if b else (0, 0))(sbox(x))
        cand.sort(key=lambda x: (0 if _saved_all(x) else 1,) + _cell(x))
        for x in cand:
            if late(): break
            if any(r not in G for r in x['refs']): continue
            evict(sbox(x))
            WATER_MARK.clear()
            lc = 'not checked'
            with park_clock(x.get('id'), 'pass 5 water check'):
                try: lc = land_check(x, G, live=not str(x['refs'][0]).startswith('CA-'))
                except Exception as e: lc = 'not checked'; LOG.append(f"water {x['id']}: {str(e)[:60]}")  # noqa: BLE001
            water_date(x)
            n['checked'] += 1
            if lc == 'water': x['status'] = 'water only: boat or kayak'; x['list'] = '🚤 Water only: boat or kayak'; n['water only'] += 1
            elif lc == 'not checked': x['status'] = 'not sure: water not checked (the USGS water map did not answer): run pass 5'; n['still not checked'] += 1
            elif str(x['status']).startswith('not sure: water not checked'):
                x['status'] = 'candidate' if not x.get('fresh') else 'candidate (saved outline only)'
                if (x.get('wide_m') or 0) < TIGHT_M: x['status'] = VERY_TIGHT; x['list'] = 'Very tight (members only)'
            x['water_checked'] = today
        for x in same:   # chat 8 Ohio note 3 / KY note 2: 'same land' rows get the checked date, an owner line and a pin like the others
            if late(): break
            x['checked'] = today
            # Oct 29 (chat 8's wrong joins): rows made before the pass-1 distance test are checked here too (a worker rerun fixes them)
            a, b = (x.get('refs') or [None, None])[:2]
            # Oct 29 (Nebraska: Platte River SP x Platte River Landing SP stayed live after the key took the Landing's wrong join
            # away): a park that no longer has an outline in the key cannot share one: the old row drops
            if REGION != 'ky' and tuple(sorted((a, b))) not in {tuple(sorted(p[0])) for p in SAME_LAND_PAIRS} and any(r not in parks or not parks[r].get('ids') for r in (a, b) if r):
                x['status'] = 'dropped: one of the two park numbers is no longer joined to this outline in the answer key (the old join was wrong)'
                n['same land dropped: join gone from the key'] = n.get('same land dropped: join gone from the key', 0) + 1; continue
            _sv = () if tuple(sorted((a, b))) in {tuple(sorted(p[0])) for p in SAME_LAND_PAIRS} else same_records_verdict(parks, (a, b), PIN, G)
            if _sv and same_records_mark(x, _sv, parks, PIN):
                n['same land held: same records, a pin outside the outline'] = n.get('same land held: same records, a pin outside the outline', 0) + 1; continue
            if a in PIN and b in PIN and (PIN[a][1] is None or PIN[b][1] is None):   # Nov 9 PM: a bad pin = a person checks the join
                x['status'] = 'not sure: one of the two parks has no usable POTA pin (0,0), so the far-pin check cannot run: a person checks the join'; continue
            if a in PIN and b in PIN and b in G and tuple(sorted((a, b))) not in {tuple(sorted(p[0])) for p in SAME_LAND_PAIRS}:
                dkm = math.hypot((PIN[a][2] - PIN[b][2]) * 111.32 * math.cos(math.radians(PIN[a][1])), (PIN[a][1] - PIN[b][1]) * 110.57)
                if dkm > 8 and not same_part(G[b], (PIN[a][2], PIN[a][1]), (PIN[b][2], PIN[b][1])):
                    x['status'] = f'dropped: two park numbers joined to one record by name, pins {dkm:.0f} km apart and not both inside the same part of it (a wrong join in the key)'
                    n['same land dropped: wrong join'] = n.get('same land dropped: wrong join', 0) + 1; continue
            if REGION != 'ky' and a in PIN and b in PIN and tuple(sorted((a, b))) not in {tuple(sorted(p[0])) for p in SAME_LAND_PAIRS}:
                _rm = re.search(r'same official outline \((.*)\); POTA', str(x.get('note') or ''))
                _doubt = FG.same_land_doubt(PIN[a][0], PIN[b][0], _rm.group(1)) if _rm else ''
                if _doubt:   # Nov 4 (Mapping 2-fer review #3): an older row from one record that does not clearly name both parks
                    x['status'] = _doubt; n['same land not sure: one record covers two parks'] = n.get('same land not sure: one record covers two parks', 0) + 1; continue
            ow = {owner_word(park_owner(r, parks)) for r in x['refs']} - {'', '?'}
            x['owner_here'] = (' / '.join(sorted(ow)) + ' land (from the outline both numbers are joined to)') if ow else 'owner not published'
            if all(r in G for r in x['refs']) and not x.get('access_pin'):
                evict(sbox(x))
                with park_clock(x.get('id'), 'pass 5 same-land access pin'):
                    try: x['access'] = nearest_access(x, st_of); x['access_pin'] = access_pin(x, G, LN, st_of)
                    except Exception as e: LOG.append(f"pin {x['id']}: {str(e)[:60]}")  # noqa: BLE001
        # Oct 28 (HQ 12:28 PM): rows the water map did not answer for are re-checked once more at the end, after a pause
        again = [x for x in cand if str(x.get('status', '')).startswith('not sure: water not checked')]
        if again and not late():
            pass   # Oct 28 6:57 PM: no waiting on a down server (the saved / bulk tiles are read first; a missing one stays NOT SURE)
            for x in again:
                if late(): break
                evict(sbox(x))
                WATER_MARK.clear()
                lc = 'not checked'
                with park_clock(x.get('id'), 'pass 5 water re-check'):
                    try: lc = land_check(x, G, live=not str(x['refs'][0]).startswith('CA-'))
                    except Exception as e: lc = 'not checked'; LOG.append(f"water again {x['id']}: {str(e)[:60]}")  # noqa: BLE001
                water_date(x)
                if lc == 'water': x['status'] = 'water only: boat or kayak'; x['list'] = '🚤 Water only: boat or kayak'; n['water only'] += 1; n['still not checked'] -= 1
                elif lc != 'not checked':
                    x['status'] = 'candidate' if not x.get('fresh') else 'candidate (saved outline only)'
                    if (x.get('wide_m') or 0) < TIGHT_M: x['status'] = VERY_TIGHT; x['list'] = 'Very tight (members only)'
                    n['still not checked'] -= 1
            n['re-checked at the end'] = len(again)
        n['water retries (won / tries)'] = f"{WATER_RETRY['won']} / {WATER_RETRY['tries']}"
        n['memory (MB now / cap; caches dropped for memory)'] = f"{rss_mb():.0f} / {MEM_MB:.0f}; {EVICT_N['memory']}"
        mark(f'water re-check of {len(cand)} spots + {len(same)} same-land rows')
        # Oct 28 11 PM (Fable's 'store not read' check found DE 43, VA 13, PA 1 rows): a water-route row made while the water was missing
        # is a PLACEHOLDER (water_unchecked) that no later pass made again; once its tiles are saved it is made again HERE and decided
        ph = [(st, x) for st, d in files.items() for x in d.get('spots', []) if x.get('water_unchecked')]
        if ph and not late():
            need = sorted({r for _, x in ph for r in x['refs'] if r in parks and parks[r]['ids'] and r not in G})
            if need:
                g4, _ = ky_geom(parks, need) if REGION == 'ky' else download(parks, need, DET, PREC)
                G.update(g4)
            CURG.clear(); CURG.update(G)
            done, remade, still = set(), 0, 0
            for st, x in ph:
                if late(): break
                pr = tuple(x['refs']); d = files[st]
                if pr in done:
                    if x in d['spots']: d['spots'].remove(x)
                    continue
                lref = next((r for r in x['refs'] if r in LN and r not in G), None); oref = next((r for r in x['refs'] if r in G), None)
                if not lref or not oref: continue
                try: got = water_route_spots(lref, [l for i, l in enumerate(LN[lref]['lines']) if not LN[lref].get('water_parts') or i in set(LN[lref]['water_parts'])], oref, bbox_groups(G[oref]))
                except Exception as e: LOG.append(f"water route again {x.get('id')}: {str(e)[:60]}"); continue  # noqa: BLE001
                if any(g.get('water_unchecked') for g in got): still += 1; continue
                done.add(pr)
                if x in d['spots']: d['spots'].remove(x)
                have = {q.get('id') for q in d['spots']}
                for g in got:
                    g['id'] = key_of(g) + '@%.3f,%.3f' % tuple(g['center']); g.update({'passes': [1, 1, 1], 'found': today})
                    mem = files[st].setdefault('ids', id_memory(files[st]))
                    near = [m[2] for m in mem.get(key_of(g), []) if m[2] not in have and math.hypot((m[0] - g['center'][0]) * 110570, (m[1] - g['center'][1]) * 111320 * math.cos(math.radians(m[0]))) <= STABLE_M]
                    if near: g['id'] = near[0]   # Nov 2 5:45 PM: a remade row keeps its old id
                    else: mem.setdefault(key_of(g), []).append([round(g['center'][0], 5), round(g['center'][1], 5), g['id']])
                    if g['id'] in have: continue
                    decide(g, parks, G, LN, PIN, today, set(), st_of); d['spots'].append(g); have.add(g['id']); remade += 1
            n['water-route rows made again from the saved water'] = remade
            n['water-route pairs still without water'] = still
        # Oct 29 (chat 8 NOT SURE groups 2 + 6): rows left from older runs with an owner wording the simple test no longer makes
        # ('more than one owner across the spot': all-public mixes are 'ok' now) or an ownership map that did not answer (BLM
        # time-outs, fixed in kpc_owned.py) are decided AGAIN here; pass 3 never re-reads a 'not sure' row
        STALE = re.compile(r'^not sure: (the ownership map shows more than one owner|the agency ownership map did not answer|ownership map did not answer|the outlines overlap, but the )')
        stale = [x for d in files.values() for x in d.get('spots', []) if STALE.search(str(x.get('status', ''))) or (no_owner_source(x) and x.get('kind') != 'same land')]
        if stale and not late():
            need = sorted({r for x in stale for r in x['refs'] if r in parks and parks[r]['ids'] and r not in G})
            if need:
                g5, _ = ky_geom(parks, need) if REGION == 'ky' else download(parks, need, DET, PREC)
                G.update(g5)
            CURG.clear(); CURG.update(G)
            redo = 0
            for x in stale:
                if late(): break
                if any(r not in G and r not in LN for r in x['refs']): continue
                before = dict(x)
                with park_clock(x.get('id'), 'pass 5 re-decide') as _c:
                    try: decide(x, parks, G, LN, PIN, today, set(), st_of); redo += 1
                    except Exception as e: x.clear(); x.update(before); LOG.append(f"re-decide {x.get('id')}: {str(e)[:60]}")  # noqa: BLE001
                if _c.hit: x.clear(); x.update(before)
            n['old not-sure owner rows decided again'] = f'{redo} of {len(stale)}'
        lw = [x for d in files.values() for x in d.get('spots', []) if x.get('kind') == 'area' and not str(x.get('status', '')).startswith('dropped')]
        more = sorted({r for x in lw for r in x['refs'] if r in parks and parks[r]['ids'] and r not in G})
        if late(): more = []; lw = []; LOG.append('pass 5: boundary lines + trail zones left for the next run (out of time)')   # Nov 9 PM
        if more:
            g2, _ = ky_geom(parks, more) if REGION == 'ky' else download(parks, more, DET, PREC)
            G.update(g2)
        mark(f'geometry of {len(more)} more parks')
        n['spots given their boundary lines'] = add_lines(files, G, today) if not late() else 0
        # Brandon Oct 28 9:17 PM (overrides HQ's 8:17 PM removal): the boat / water-only rows STAY ('we run them like they are, we're
        # making a list to review later'); they go on the review list, nothing is deleted
        n['river channels listed as water only (boat spots)'] = channel_rows(files, G, today)
        mark(f"boundary lines for {n['spots given their boundary lines']} spots")
        tw = [] if late() else sorted({r for d in files.values() for x in d.get('spots', []) if x.get('kind') == 'trail' for r in x['refs'] if r in parks and parks[r]['ids'] and r not in G})
        if tw:
            g3, _ = ky_geom(parks, tw) if REGION == 'ky' else download(parks, tw, DET, PREC)
            G.update(g3)
        mark(f'geometry of {len(tw)} trail-pair parks')
        n['trail stretches given their true zone'] = add_zones(files, G, PIN, today) if not late() else 0
        mark(f"zones for {n['trail stretches given their true zone']} trail stretches")
        # Oct 29 (chat 10 + Brandon 7:23 AM 'some live 2fers were wrong'): a live spot more than 100 km from a STATE-LEVEL park's
        # pin = that park's outline holds a far piece / a wrong join: held as NOT SURE (kpc_fers_far_hold.py; rule B13 pending)
        if REGION not in ('ky', 'world'):
            try:
                import kpc_fers_far_hold as FH
                FP = {r: (v[1], v[2], str(v[0]), str(v[4])) for r, v in PIN.items() if v[1] is not None and v[2] is not None and (v[1] or v[2])}
                n['live rows held: spot far from a state park pin (rule B13)'] = sum(FH.hold_spots(d.get('spots', []), FP) for d in files.values())
            except Exception as e: LOG.append(f'far-spot hold: {str(e)[:80]}')  # noqa: BLE001
        n['candidates held: no ownership source'] = sum(hold_no_owner(d.get('spots', [])) for d in files.values())
        for st, d in files.items():
            tidy_rows(d.get('spots', []), PIN, today)
            d['pass5'] = today; d['about'] = ABOUT
            d['spots'] = slim(d.get('spots', []))
            save_json(file_of(st), pc_tag(d), indent=None)  # Nov 2: spot files compact everywhere (indent made Alaska 824 MB)
        counts.update(n)
    elif PASS == 4:   # access pins for candidates that have none yet (Oct 26: added after pass 3 had run)
        files = {st: d for st, d in old.items() if (not ONLY or st in ONLY or st[3:] in ONLY)}
        cand = [s for d in files.values() for s in d.get('spots', []) if str(s.get('status', '')).startswith('candidate') and not s.get('access_pin')]
        refs = sorted({r for s in cand for r in s['refs'] if r in parks and parks[r]['ids']})
        if REGION == 'ky': G, bad = ky_geom(parks, refs)
        else: G, bad = download(parks, refs, DET, PREC)
        inject_apx_geom(G, parks, refs)
        n = 0
        for s in cand:
            if late(): break
            if any(r not in G and r not in LN for r in s['refs']): continue
            if not s.get('access'): s['access'] = nearest_access(s, st_of)
            try: s['access_pin'] = access_pin(s, G, LN, st_of); n += 1
            except Exception as e: LOG.append(f"pin {s['id']}: {str(e)[:60]}")  # noqa: BLE001
        for st, d in files.items():
            d['about'] = ABOUT
            save_json(file_of(st), pc_tag(d), indent=None)  # Nov 2: spot files compact everywhere (indent made Alaska 824 MB)
        counts.update({'candidates without a pin': len(cand), 'pins placed': n})
    elif PASS == 1:
        same = same_outline(parks)
        save_json(OUT / (f'same-outline-{RUN_TAG}.json' if RUN_TAG else {'world': 'same-outline-world.json', 'ky': 'same-outline-ky.json'}.get(REGION, 'same-outline.json')), {'about': "Two park numbers joined to the SAME outline record. Shown in the spot files as 'Same land, two park numbers' (HQ Oct 27 10:35 AM: the old 'never a 2-fer' rule is retired); a wrong join is still worth fixing in the answer key.", 'pairs': same}, indent=1)
        skip_pairs = {tuple(x['refs']) for x in same}
        # saved outlines: PAD-US from the cache, Canada from the saved files; the rest from the state layers at the key's detail
        pad = saved_us(parks) if REGION == 'na' else {}
        _area = 'ky' if REGION == 'ky' else RUN_TAG or ('-'.join(sorted(ONLY)) if ONLY else REGION)
        live_load(_area); _due = live_due(today) if REGION == 'na' else set()
        G, need = {}, []
        _sv = lambda i: (isinstance(i, int) and i in pad) or str(i) in SAVED_STR
        _lf = lambda i: i in SAVED_LEFT or str(i) in SAVED_LEFT
        n_key = n_live = 0
        for ref, p in parks.items():
            if p['st'].startswith(('CA-', 'W-')) or not p['ids'] or REGION == 'ky': continue
            if all(_sv(i) or _lf(i) for i in p['ids']):
                for i in p['ids']:
                    if _lf(i) and not _sv(i): LEFT.setdefault(ref, []).append(f"{p['names'].get(str(i)) or i}: {SAVED_LEFT.get(i) or SAVED_LEFT.get(str(i))}")
                gs = [clip(ref, i, pad[i] if isinstance(i, int) and i in pad else SAVED_STR[str(i)]) for i in p['ids'] if _sv(i)]
                if gs: G[ref] = gs; MAPDATE[ref] = 'saved copy (answer key)'; n_key += 1
            elif ref in LIVE and [str(i) for i in p['ids']] == LIVE[ref].get('ids') and ref not in _due:
                G[ref] = LIVE[ref]['g']; MAPDATE[ref] = f"saved copy (read live {LIVE[ref].get('rd')})"; n_live += 1
            else: need.append(ref)
        counts['parks from saved outlines (answer key copy)'] = n_key
        counts["parks from saved outlines (2-fer bot's own copy)"] = n_live
        counts['saved outlines due for their monthly re-read'] = len(_due & set(need))
        if REGION == 'ky':
            kg, kb = ky_geom(parks, [r for r in parks if parks[r]['ids']]); G.update(kg); need = []
        else: G.update(saved_world(parks) if REGION == 'world' else saved_ca(parks))
        notice('2-fer bot', f"pass 1: {len(G)} parks from saved outlines, {len(need)} to download, {len(LN)} official lines")
        mark('pass 1 saved outlines')
        got, bad = download(parks, need, DET, PREC)
        G.update(got)
        if bad and not late(frac=.5):   # Oct 30 (chat 2, Iowa came out EMPTY: 180 of 491 outlines not read, Iowa DNR did not answer): one slow second try
            time.sleep(60); got2, bad = download(parks, sorted(bad), DET, PREC); G.update(got2); got.update(got2)
        # Nov 9 evening: every live read is saved for the next run; a due re-read that failed keeps its saved copy (nothing lost)
        for ref in set(need) & set(G):
            if ref in got and ref not in SAVED_USE: LIVE[ref] = {'ids': [str(i) for i in parks[ref]['ids']], 'g': G[ref], 'rd': today}
        for ref in list(bad | DL_CUT):
            if ref in LIVE and [str(i) for i in parks[ref]['ids']] == LIVE[ref].get('ids'):
                G[ref] = LIVE[ref]['g']; MAPDATE[ref] = f"saved copy (read live {LIVE[ref].get('rd')}; today's re-read did not answer)"
                bad.discard(ref); DL_CUT.discard(ref)
        counts['parks read live (saved for next time)'] = len(set(need) & set(got))
        live_save(today)
        mark(f'pass 1 downloads ({len(need)} parks; {len(DL_CUT)} not reached for time)')
        if DL_CUT:   # Nov 9 PM: parks not downloaded for time = an unfinished pass; their areas keep their previous files
            counts['stopped for time'] = True; counts['parks not downloaded: out of time'] = len(DL_CUT)
        counts['parks whose outline could not be read'] = len(bad)
        _held = {r for r in bad if r in MISSING_SAVED}   # a known reason (saved copy missing): listed, not an agency map down
        if _held: counts['parks held: saved copy missing (needs download)'] = {r: saved_missing_why(r) for r in sorted(_held)}
        _withids = sum(1 for r in parks if parks[r].get('ids'))
        if len(bad - _held) > 20 and len(bad - _held) > .2 * max(1, _withids):   # half a state missing is not a 2-fer answer: stop loudly (a real issue)
            hosts = sorted({str(next(iter(parks[r]['ids']), ''))[:6] for r in list(bad)[:200]})
            print(f"::error title=2-fer line: outlines not read::{len(bad)} of {_withids} parks' outlines could not be read (id prefixes {' '.join(hosts[:8])}): "
                  "an agency map did not answer. The area stops here, nothing is saved; try it again later.", flush=True)
            sys.exit(1)
        boxes = {r: bbox_groups(g) for r, g in G.items() if bbox_groups(g)}
        for r in LN:
            if r in parks and r not in boxes:
                b = bbox_lines(LN[r]['lines']); boxes[r] = [b[0] - .0005, b[1] - .0005, b[2] + .0005, b[3] + .0005]   # the 100-ft zone
        pairs = grid_pairs(boxes) - skip_pairs
        if PARKS:   # the pairs touching PARKS + the pairs among their neighbours (so a 3-fer that includes a PARKS park is still found)
            nbr = {r for p in pairs if PARKS & set(p) for r in p}
            pairs = {p for p in pairs if PARKS & set(p) or set(p) <= nbr}
            notice('2-fer bot', f"pass 1: small batch for {len(PARKS)} park(s) ({' '.join(sorted(PARKS))[:200]}): {len(pairs)} pairs touch them; every other row is carried over")
        touched = {r for p in pairs for r in p}
        counts['parks done by the box test'] = len(boxes) - len(touched)
        counts['pairs whose boxes touch'] = len(pairs)
        spots = find_spots(G, LN, pairs, counts)
        mark(f"pass 1 pair tests ({counts['pairs tested']} of {len(pairs)})")
        # MISSING CHECK (HQ Oct 27 3:23 PM): what pass 1 looked at, which parks it could not look at and why, and the pairs whose
        # outlines nearly touch, so kpc_fers_expected.py can say FOUND / DROPPED / NEVER LOOKED AT for every expected pair
        try:
            area = 'ky' if REGION == 'ky' else RUN_TAG or ('-'.join(sorted(ONLY)) if ONLY else REGION)
            if PARKS: raise RuntimeError('small batch: the whole-area look-list is kept as it was')
            save_json(OUT / f'looked-{area}.json', {'about': 'What the 2-fer bot looked at in pass 1 (for the missing check).', 'date': today,
                                                    'tested': sorted(['+'.join(p) for p in TESTED]), 'no_outline': {r: w for r, w in SKIPWHY.items() if r in PIN and r not in LN and (PIN[r][5] == 'KY' if REGION == 'ky' else (not ONLY or PIN[r][5] in ONLY or 'US-' + str(PIN[r][5]) in ONLY))},
                                                    # Oct 29 (chat 8, missing pairs): a trail / river park is tested by its official LINE (LN), so it is
                                                    # neither 'no official boundary' nor 'not in this run' (a multi-state trail's pin may sit elsewhere)
                                                    'near100': near_pairs(G, {p for p in pairs if p in TESTED}, spots), 'parks': sorted(set(parks) | set(LN)),
                                                    # Nov 4 (Mapping 2-fer review #1): POTA pins at 0,0 / impossible (never moved; not tested)
                                                    'bad_pota_pins': {r: v[1] for r, v in sorted(BAD_PIN.items()) if not ONLY or v[2] in ONLY or 'US-' + str(v[2]) in ONLY or str(v[2])[3:] in ONLY},
                                                    'water_no_split': sorted(WATER_NO_SPLIT),
                                                    # Oct 29 (chat 8: Colton Point / Leonard Harrison x Tioga SF said 'boxes do not touch'):
                                                    # parks whose official outline could not be READ in pass 1 (one record of theirs did not answer)
                                                    'unread': sorted(r for r in parks if r not in G and r not in LN and r not in SKIPWHY and r not in LEFT),
                                                    'held_saved_missing': {r: saved_missing_why(r) for r in sorted(MISSING_SAVED) if r not in G},
                                                    # Oct 27 (HQ: the missing check's 1 km filter measures OUTLINE to OUTLINE): each park's box, so the
                                                    # check can measure every park, not only the ones in the PAD-US cache
                                                    'boxes': {r: [round(v, 4) for v in bbox_groups(G[r])] for r in G if G.get(r)}}, indent=None)
        except Exception as e: LOG.append(f'looked file: {str(e)[:80]}')  # noqa: BLE001
        try:   # rule 12: parks with no official boundary whose pin sits inside another park = 'Missing boundary' list
            if PARKS: raise RuntimeError('small batch: the missing-boundary list is kept as it was')
            miss = missing_list(PIN, parks, SKIPWHY, G, LN, today)
            save_json(OUT / f'missing-{RUN_TAG or REGION}.json', {'about': "Missing boundary: check the official map. A park with no official boundary (or only an approximate one) whose POTA pin sits inside another park's official outline. Never in the main list; members first.", 'parks': miss}, indent=1)
            if WDPA_SKIP:
                save_json(OUT / f'wdpa-internal-{RUN_TAG or REGION}.json',
                          {'about': 'Internal only. WDPA / Protected Planet outlines are never a public 2-fer source.',
                           'public': False, 'parks': WDPA_SKIP}, indent=1)
            counts['missing boundary'] = len(miss)
        except Exception as e: LOG.append(f'missing list: {str(e)[:80]}')  # noqa: BLE001
        if REGION == 'ky':   # Oct 27: a trail that crosses Kentucky brings pairs in other states; keep only spots IN Kentucky
            try:
                KYC = [c['r'] for c in json.load(open('kpc-ky-counties.json'))]
                # Oct 28 10:45 PM: the CENTER alone dropped the Kentucky Lake shore rows at Fort Heiman (center 30 m south of the coarse
                # state line in kpc-ky-counties.json): a spot is kept when its center OR any point of its shape is in Kentucky
                spots = [s for s in spots if pip_groups(KYC, s['center'][1], s['center'][0])
                         or any(pip_groups(KYC, p[0], p[1]) for p in (s.get('shape') or [])[::max(1, len(s.get('shape') or []) // 40)])]
            except Exception as e: LOG.append(f'Kentucky outline: {str(e)[:60]}')  # noqa: BLE001
        by = {}
        if AREA_BOX:   # Oct 30 (chat 2): two LINE parks meet anywhere along their whole length (the Appalachian Trail x Virginia trails
            n0 = len(spots)   # landed in US-ME.json): only spots inside this run's own area are this run's rows
            spots = [s for s in spots if AREA_BOX[1] <= s['center'][0] <= AREA_BOX[3] and AREA_BOX[0] <= s['center'][1] <= AREA_BOX[2]]
            if n0 != len(spots): LOG.append(f'{n0 - len(spots)} spots outside this area left for their own area')
        for s in spots:
            s.update({'id': key_of(s) + '@%.3f,%.3f' % tuple(s['center']), 'passes': [1, 0, 0], 'status': 'pass 1', 'found': today})
            # Oct 29 (chat 8, nec: 22 Massachusetts Appalachian Trail rows sat in US-ME.json): a row is filed under the state of a
            # park with its own outline (where the spot is), not the line's state, when that state is in this run
            # Oct 31 (chat 11, Delaware: Captain John Smith x MARYLAND WMAs sat in US-DE.json): when the row has parks with their own
            # outline, it belongs to THEIR state; a line park filed under this state (a national trail) never pulls it into this file
            own = [st_of(r) for r in s['refs'] if r in G]
            sts = own if own else [st_of(r) for r in s['refs']]
            by.setdefault(next((x for x in sts if x and (not ONLY or x in ONLY or x[3:] in ONLY)), sts[0] if sts else st_of(s['refs'][0])), []).append(s)
        if REGION != 'world':
            # Brandon Oct 26 2:03 PM ('Fort Heiman and Donelson, it is what it is: both'): two park numbers on ONE official outline
            # (the NPS folded Fort Heiman into Fort Donelson National Battlefield) are both valid there: a 'same land' spot on
            # the piece nearest the second park's pin. Oct 27 10:35 AM (HQ, Fable #7): the same for US + Canada.
            for x in same:
                a, b = x['refs']
                if a not in G or b not in G or a not in PIN or b not in PIN: continue
                _nopin = PIN[a][1] is None or PIN[b][1] is None   # Nov 9 PM: a bad pin (0,0): no far-pin test, a person checks the join
                # Oct 29 (chat 8's wrong-joins puzzle: Robert Moses Long Island + Thousand Islands, 503 km apart, 'same land'): two park
                # numbers joined to one record by NAME alone. Pins more than 8 km apart = only when BOTH pins sit inside the shared outline
                dkm = 0 if _nopin else math.hypot((PIN[a][2] - PIN[b][2]) * 111.32 * math.cos(math.radians(PIN[a][1])), (PIN[a][1] - PIN[b][1]) * 110.57)
                if dkm > 8 and tuple(sorted((a, b))) not in {tuple(sorted(p[0])) for p in SAME_LAND_PAIRS} and not same_part(G[b], (PIN[a][2], PIN[a][1]), (PIN[b][2], PIN[b][1])):
                    SAME_FAR.append([a, b, round(dkm, 1), x.get('record')]); continue
                # Nov 4 (Mapping 2-fer review #3): one record joined to two parks is only a candidate when it names BOTH parks and
                # no kind differs (Fundy Biosphere Reserve on the Fundy National Park record = a person decides, rule 18)
                _doubt = '' if tuple(sorted((a, b))) in {tuple(sorted(p[0])) for p in SAME_LAND_PAIRS} else FG.same_land_doubt(PIN[a][0], PIN[b][0], x.get('name') or x.get('record'))
                la, lo = PIN[b][1], PIN[b][2]
                best = G[b][0] if _nopin else min(G[b], key=lambda poly: min(math.hypot(q[0] - lo, q[1] - la) for q in poly[0]) if poly and poly[0] else 1e9)
                ring = best[0]; xs = [q[0] for q in ring]; ys = [q[1] for q in ring]
                sp = {'refs': sorted([a, b]), 'kind': 'same land', 'center': [round(sum(ys) / len(ys), 6), round(sum(xs) / len(xs), 6)],
                      'box': [round(min(xs), 5), round(min(ys), 5), round(max(xs), 5), round(max(ys), 5)],
                      'shape': [[round(q[0], 6), round(q[1], 6)] for q in sharp_shape(ring)],
                      'passes': [1, 1, 1], 'status': 'candidate', 'label': 'Same land, two park numbers', 'found': today,   # ruling Oct 27 8:10 AM: shown, labelled plainly
                      'note': f"both park numbers are joined to the same official outline ({x['name']}); POTA lists them separately: check POTA's current list",
                      'maps': [[r, map_link(r, PIN)] for r in (a, b)], 'names': {r: PIN[r][0] for r in (a, b)}}
                sp['id'] = key_of(sp) + '@%.3f,%.3f' % tuple(sp['center'])
                _sv = () if tuple(sorted((a, b))) in {tuple(sorted(p[0])) for p in SAME_LAND_PAIRS} else same_records_verdict(parks, (a, b), PIN, G)
                if _sv and same_records_mark(sp, _sv, parks, PIN): counts['same land held: same records, a pin outside the outline'] = counts.get('same land held: same records, a pin outside the outline', 0) + 1
                elif any(r in LOWCONF for r in (a, b)): sp['status'] = 'not sure: low-confidence outline (check the join)'
                elif _nopin: sp['status'] = 'not sure: one of the two parks has no usable POTA pin (0,0), so the far-pin check cannot run: a person checks the join'
                elif _doubt: sp['status'] = _doubt; counts['same land not sure: one record covers two parks'] = counts.get('same land not sure: one record covers two parks', 0) + 1
                by.setdefault(st_of(a), []).append(sp)
            if SAME_FAR:
                counts['same land left out: pins far apart, not both inside the outline'] = len(SAME_FAR)
                LOG.append('same land left out (pins far apart): ' + '; '.join(f'{p[0]}+{p[1]} {p[2]} km' for p in SAME_FAR[:8]))
        # Nov 9 (Quality must-fix 1, run 42594981324: US-CO 40 -> 4 candidates, CA-NB 747 -> 7 spots): a pass that stopped for time
        # never rewrites an area it did not finish. An area with any untested pair keeps its previous file; a new area is saved
        # marked incomplete. Only areas whose every pair was tested are written.
        undone = set()
        if counts.get('stopped for time'):
            for p_ in pairs:
                if p_ not in TESTED: undone |= {st_of(r) for r in p_}
            undone |= {st_of(r) for r in DL_CUT}   # Nov 9 PM: a park never downloaded makes no pair, but its area is not finished
            undone.discard('')
            kept = sorted(st for st in undone if st in old)
            if kept: counts['areas kept as before (pass 1 out of time)'] = kept; LOG.append(f'{len(kept)} areas kept their previous file (pass 1 out of time): ' + ' '.join(kept[:20]))
        for st in sorted(set(by) | {p['st'] for p in parks.values()}):
            if counts.get('stopped for time') and st in old and (st in undone or st not in by): continue
            sp = by.get(st, [])
            if PARKS:   # small batch: the new rows for the pairs touching PARKS + every other old row unchanged
                sp = [x for x in sp if PARKS & set(x['refs'])]
                kinds = {(tuple(sorted(x['refs'])), x['kind']) for x in sp}
                # Oct 28 9:15 PM (KY known answer 18/19: the Kentucky Lake shore rows vanished): an old row of a PARKS pair is carried
                # over when the batch made no row of that pair + kind (line / river / water-route rows are not all remade by a batch)
                sp += [x for x in (old.get(st) or {}).get('spots', []) if not PARKS & set(x.get('refs') or []) or (tuple(sorted(x.get('refs') or [])), x.get('kind')) not in kinds]
                if not sp and st not in old: continue
            if TIMED_PAIRS:   # Nov 9 PM: a pair skipped for time keeps its old rows (listed in the report for a person)
                _tp = {tuple(sorted(p_)) for p_ in TIMED_PAIRS}
                sp = sp + [x for x in (old.get(st) or {}).get('spots', []) if tuple(sorted((x.get('refs') or [])[:2])) in _tp and len(x.get('refs') or []) == 2]
            mem = stable_ids([x for x in sp if x.get('center') and x.get('refs') and x.get('kind') and '@channel@' not in str(x.get('id'))], id_memory(old.get(st)))
            save_json(file_of(st), pc_tag({'st': st, 'about': ABOUT, 'pass1': today, 'ids': mem, 'spots': slim(sorted(sp, key=lambda s: s['id'])),
                                    **({'incomplete': 'pass 1 stopped for time before every pair here was tested: run again'} if st in undone else {})}), indent=None)  # Nov 2: spot files compact everywhere (indent made Alaska 824 MB)
    else:
        files = {st: d for st, d in old.items() if (not ONLY or st in ONLY or st[3:] in ONLY)}
        # resume: a spot this pass already decided (agreed, or dropped) is not done again
        todo = lambda s: s['passes'][PASS - 2] == 1 and not s['passes'][PASS - 1] and not str(s.get('status', '')).startswith(f'dropped in pass {PASS}') and not (PASS == 3 and str(s.get('status', '')).startswith(('candidate', 'dropped: ', 'not sure', 'water only', 'check: two owners', 'very tight', 'merged into')))
        prev = [s for d in files.values() for s in d.get('spots', []) if todo(s)]
        refs = sorted({r for s in prev for r in s['refs'] if r in parks})
        notice('2-fer bot', f'pass {PASS}: {len(prev)} spots from pass {PASS - 1}, {len(refs)} parks to download fresh')
        if REGION == 'ky':   # Kentucky's official files are the only copy (no agency download by id): saved copy, flagged
            G, bad = ky_geom(parks, [r for r in refs if parks[r]['ids']])
            inject_apx_geom(G, parks, refs)
            # fresh = every tract read live (Daniel Boone = its outer line masked by the live Forest Service ownership map)
            saved_only = {r for r in G if 'file' in FRESHKY.get(r, {'file'})}
            for r in G:
                MAPDATE[r] = ('read live from the agency ' + today + ''.join(f' · {v}' for k, v in KYSRC.items() if any(str(i).startswith(k + '|') for i in parks[r]['ids']))) if r not in saved_only else 'Kentucky file copy (live layer did not answer or has no live source)'
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
                ub = [r for r in s['refs'] if r in bad]
                if ub:   # Oct 29 (Mississippi: 24 rows waited for pass 2 run after run, their WMA layer will not read): a row whose
                    # outline cannot be read is NOT SURE with the reason (review list), never 'waiting' forever
                    _sm = [saved_missing_why(r) for r in ub if r in MISSING_SAVED]
                    s['status'] = (f"not sure: {'; '.join(_sm)} ({', '.join(PIN.get(r, [r])[0] for r in ub if r in MISSING_SAVED)})" if _sm else
                                   f"not sure: the official outline of {', '.join(PIN.get(r, [r])[0] for r in ub)} could not be read in pass {PASS} (the next run tries again)"); continue
                if pk not in TESTED and len(s['refs']) == 2:   # out of time before this pair: the next run carries on
                    s['status'] = f'waiting for pass {PASS}'; continue
                sb = sbox(s)
                m = next((n for n in newk.get(key_of(s), []) if inter(sb, sbox(n), 0.0005)), None)
                if m:
                    s['passes'][PASS - 1] = 1; agree += 1
                    for k in ('center', 'shape', 'box', 'acres', 'wide_m', 'len_m'):
                        if k in m: s[k] = m[k]
                    if m.get('masked_out'): s['masked_out'] = m['masked_out']
                    else: s.pop('masked_out', None)
                    m['_used'] = 1
                    s['status'] = f'pass {PASS}'
                else:
                    s['passes'][PASS - 1] = 0
                    s['status'] = f'dropped in pass {PASS}' + (' (an outline could not be downloaded)' if any(r in bad for r in s['refs']) else
                                                               ': the finer official outlines show no shared patch here (the first, coarse look overlapped by drawing error only)')
                if REGION == 'ky' and 'US-4484' in s['refs'] and set(s['refs']) & KY_FS_MANAGED:
                    s['label'] = 'Forest Service land managed by KDFWR'   # Oct 27 (HQ ruling 2): one agency owns, another manages = a real 2-fer
                if PASS == 3 and m:
                    if late():   # Fable #1: out of time = carried on by the next run, never a half-decided row
                        s['passes'][2] = 0; s['status'] = 'waiting for pass 3'; continue
                    evict(sbox(s))
                    WATER_MARK.clear()
                    _before = dict(s)
                    with park_clock(s.get('id') or '+'.join(s['refs']), f'pass {PASS} decide') as _c:
                        decide(s, parks, G, LN, PIN, today, saved_only, st_of)
                        water_date(s)
                    if _c.hit: s.clear(); s.update(_before); s['passes'][2] = 0; s['status'] = 'waiting for pass 3'   # listed; the next run carries on
            if PASS == 3: one_row_per_line_pair(d.get('spots', []), st_of, G, LN); tidy_rows(d.get('spots', []), PIN, today); counts['candidates held: no ownership source'] = counts.get('candidates held: no ownership source', 0) + hold_no_owner(d.get('spots', []))
            d[f'pass{PASS}'] = today
            d['about'] = ABOUT   # Oct 26 6:41 PM (HQ): the house-rule wording travels with every save
            d['spots'] = slim(d.get('spots', []))
            save_json(file_of(st), pc_tag(d), indent=None)  # Nov 2: spot files compact everywhere (indent made Alaska 824 MB)
        new_only = sum(1 for v in newk.values() for n in v if not n.get('_used'))
        counts.update({'agree with the pass before': agree, 'new here only (not counted)': new_only})
    # report
    rep = {}
    RF = OUT / (f'report-{RUN_TAG}.json' if RUN_TAG else {'world': 'report-world.json', 'ky': 'report-ky.json'}.get(REGION, 'report.json'))
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
    try:
        rep['fers_rules'] = KFREEZE.rules_hash('fers') if KFREEZE else None
    except Exception:  # noqa: BLE001
        rep['fers_rules'] = None

    if TIMED_OUT: counts['timed out (skipped, listed for a person)'] = dict(sorted(TIMED_OUT.items())[:200])
    if NOPIN_BY_ID: counts['bad POTA pin: tested by saved record ids'] = sorted(NOPIN_BY_ID)[:400]
    if counts.get('stopped for time'):   # Nov 9 PM: a pass cut short says so as a warning (the run summary shows it)
        print(f"::warning title=2-fer bot::pass {PASS} stopped for time ({counts.get('pairs tested', 0)} pairs tested, {counts.get('parks not downloaded: out of time', 0)} parks not downloaded); unfinished areas keep their previous files", flush=True)
    rep[f'pass{PASS}'] = dict(counts, date=today, problems=LOG[:40])
    rep['per state'] = per
    save_json(RF, rep, indent=1)
    if HC.report(): notice('2-fer bot', f'pass {PASS}: ' + HC.report())
    notice('2-fer bot', json.dumps({k: v for k, v in counts.items() if k != 'left out'})[:800])
    if LOG: notice('2-fer bot problems', f'pass {PASS}: {len(LOG)} · ' + ' | '.join(dict.fromkeys(l[:90] for l in LOG))[:700])   # ONE line: GitHub keeps only 10 notes a step


ABOUT = ("Spots where the boundaries of two or more POTA parks may overlap, by the 2-FER RULES FOR THE WHOLE WORLD (Brandon Oct 27, "
         "notes/mapping.md): the park = where its designation legally applies (national forests + grasslands = Forest Service-OWNED land only, "
         "never proclamation lines); public land open to the public; layered = real, side by side = not (ownership step: PAD-US / CPCAD at the "
         "spot, read at up to 5 points of the patch; no public owner there = not sure); a patch 50 yards across in every park ('small' = 50-100 yards; 25-50 yards = the separate 'very tight' list, members only; under 25 = not kept); line-only trails / rivers by POTA's 100-ft rule from the line "
         "or the river EDGE (USGS NHD), along at least 25 metres of the line inside the other park; pins never count. Status: 'candidate' = all checks passed; 'not sure: …' and 'water only: boat or "
         "kayak' are separate lists, never the main one; n-fers up to 9; 'Same land, two park numbers' (two numbers on one official outline) is shown with that label; 'dropped: …' says why. Every decided spot shows 'checked' + 'map_dates'. Parks with "
         "no official boundary: missing-<region>.json. HIDDEN, not reviewed: passes [saved, fresh, finest] must all be 1 "
         "and status 'candidate' before a person looks. Wording when shown (house rule, Oct 27): '⚠️ Parks' boundaries may overlap here, but we can't confirm it. "
         "Check both official boundary maps and make your "
         "own call before you count it.' Tool pages carry the FULL notice from .claude/notes/notices.md.")

if __name__ == '__main__':
    # Nov 9 PM (run 42649544758 showed a green check after pass 3 stopped on KeyError 'CA-2062' and the step timed out): a crash
    # exits 1 and the step's hard end exits 3, so the workflow records an error and the run is red. Areas not saved keep their files.
    try: main()
    except HardStop:
        try: print(f'::notice title=2-fer bot::{reuse_keep_finished()} finished pair answers kept for the next run', flush=True)
        except Exception: pass  # noqa: BLE001
        print(f'::error title=2-fer bot::pass {PASS} reached the step\'s time limit and stopped; nothing more was saved by this pass (unfinished areas keep their previous files)', flush=True)
        sys.exit(3)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc()
        notice('2-fer bot', f'stopped: {e}')
        try: notice('2-fer bot', f'{reuse_keep_finished()} finished pair answers kept for the next run')
        except Exception: pass  # noqa: BLE001
        sys.exit(1)
    sys.exit(0)
