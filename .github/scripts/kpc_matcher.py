#!/usr/bin/env python3
"""THE shared park-to-outline matcher (KPC owner, 2026-11-13; stage 1: added alongside, NOT used by any key or bot yet).

One question, asked the same way everywhere: is this layer record a POTA park's outline? Three answers only:
  MATCH    the record(s) are the park's outline. Every record that belongs is returned (all tracts), with its id.
  UNCLEAR  a person decides. `likely` says 'yes' or 'no', `reason` says why in plain English.
  NO       not this park's outline.

Standard library only. No network, no files, no environment switches, nothing happens on import: a Windows PC, the trim
tool and every bot can `import kpc_matcher` and call the same small pure functions.

Where the rules come from (copied, not imported, so this file stands alone on a PC; each copy keeps its source):
  * names and kinds: the US key's reading, kpc_us_key.py norm / kinds / variants / same_name / exact_name / name_ok /
    same_words / same_kind (lines 115-279 of KPC-Links main at the time of copying), its golden-tested core.
  * pieces: kpc_key_rules.py piece_words / piece_ok (rule 18, lines 237-303). Here it is ON by default (gap 3).
  * pin and weighing: kpc_match.py inside / km_to / size_km / W / JOIN_AT / MARGIN / score / decide (lines 30-179).
  * second opinion on acres: kpc_problem_solver.py ACRE_TOL = 0.15 (line 734), and the join check's acres band
    kpc_join_check.py RATIO = (0.5, 2.0) and FAR_KM = 15 (lines 39-41).
  * a park inside a park: kpc_tracts.py NEST_SHARE = 0.9 and _sample (lines 28, 243-248).

What is new (the gaps of out/nov13-matchers/MATCHERS.md, each with tests in tests/test_kpc_matcher_nov13.py):
  1. More kind words: refuge, wildlife area, wa, sp, np, nf, sf, sra, sb, nm, nhs, nhp, nra, sgl, shp, and POTA's own common park
     types the US table missed (State Fishing Lake, trails, State Historical Monument, State / Ecological Reserve, National
     Memorial, Wetland Management District, Waterfowl Production Area). MATCH needs a recognised kind on BOTH sides and the
     kinds must agree; no kind word or an unknown one on either side = UNCLEAR.
  2. A bare name ('Cedar') never MATCHes by name alone. Its kind can come from the PAD-US designation (PAD-US layers only), from
     the record's own class field, or from the layer's declared kind (layer_info['kind']); else UNCLEAR.
  3. The piece / unit rule is on: a park named 'Unit 2' never takes Unit 1.
  4. A small park inside a bigger park (POTA allows it now) matches only its OWN outline. A record whose name is the park's name
     minus words ('Big Woods SP' for 'Big Woods Beach SP') is the bigger place around it: never joined, never auto-confirmed.
     A same-name record lying >= 90% inside the park's own outline with extra words of its own is another park inside it.
  5. The pin counts: inside, or outside by at most max(0.25 km, half the land's width) (kpc_match.py W['pin_edge'], line 94)
     and never over 15 km (kpc_join_check.FAR_KM). Farther = UNCLEAR, very far (over 10 widths and over 20 km, kpc_match.py
     'pin_very_far') = NO. A pin is never moved.
  6. OWNER DECISION 2026-11-13: same name, DIFFERENT kind, pin inside = UNCLEAR with likely=yes; a person confirms (or the
     auto-confirm second opinion below). It never joins on its own. This replaces the Nov 4 pile-solver 'two-agency rule'
     (join with a flag) for any caller of this module.
  7. A park in several tracts gets every record that belongs; none is dropped silently (a record left out is listed with why).
  8. Two same-named places far apart: the park keeps the one at its pin; the far one is listed ('far_same_name'), never both.
  Also: names differing only by Upper / Lower / North / South / East / West / Middle = UNCLEAR likely no (kpc_match: 'may be the
  whole or a part'); a same-name record with no outline and no box is listed as 'cannot be placed', never treated as far away.
  For the bigger-place test the US key's SOFT words are split: park, area, unit, tract, site, land(s), complex ... are ignored,
  lake, pond, reservoir, beach, forest, preserve, reserve count as name words ('Big Woods Beach' is not 'Big Woods').

Owner additions, 2026-11-13 evening:
  * decide_with_key(): a park the key already joined in THIS source is cut by the key's record ids first, then only
    sanity-checked; name + kind + pin matching is the fallback (no ids, or a file from another source).
  * auto-confirm second opinion: an UNCLEAR-likely-yes is promoted to MATCH ('auto-confirmed', reasons kept) only when
    independent evidence agrees: official acres within 15% of the outline, pin inside, the only place of that name within the
    distance rule, and agency / official-page kind not contradicting where both sides state one. A small park can NEVER be
    auto-confirmed onto the bigger outline around it. Extra evidence comes in on the park dict: official_acres, agency,
    web (the official page address), page_kind (the kind of place that page states), wdpa_id (POTA's WDPA site id). Nothing is
    looked up here.
  * WDPA site id: strong evidence only on the PRIVATE WDPA layer (layer_info['wdpa']); on a public layer a cross-check only, when
    the public record carries the id itself. A result that used the WDPA layer is private=True: nothing WDPA-derived may go public.
  * review_state(): an existing key join that the new rules call doubtful is KEEP-FLAGGED (keep the outline, mark it), never
    removed.
"""
import math
import re
import unicodedata

MATCH, UNCLEAR, NO = 'MATCH', 'UNCLEAR', 'NO'

# ======================================================================================================== names (US key copy)
# Copied from kpc_us_key.py lines 115-157 (GEN, ABBR, NOTNAME, norm). Unchanged except the ABBR additions right below it.
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

# Gap 1 (2026-11-13): the common short kind forms. ABBR is used by norm() (so 'Cedar SP' reads 'cedar', as before: 'sp' was
# already a generic word) and by kinds() below (so 'Cedar SP' is now a State Park, not a place of no kind).
SHORT_KINDS = {'sp': 'state park', 'np': 'national park', 'nf': 'national forest', 'sf': 'state forest', 'wa': 'wildlife area',
               'sra': 'state recreation area', 'swa': 'state wildlife area', 'nwr': 'national wildlife refuge',
               'nm': 'national monument', 'nhs': 'national historic site', 'nhp': 'national historical park',
               'nra': 'national recreation area', 'sgl': 'state game lands', 'shp': 'state historic park',
               'shs': 'state historic site', 'sna': 'state natural area', 'wma': 'wildlife management area',
               'fwa': 'fish and wildlife area', 'sha': 'state habitat area', 'nca': 'national conservation area',
               'spk': 'state park', 'stpk': 'state park', 'natl': 'national', 'sb': 'state beach'}


# Copied from kpc_us_key.py lines 160-176 (KINDS, kinds, DES).
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

# Gap 1: 'refuge' alone is a refuge (not as the FIRST word: 'Refuge Cove State Recreation Site' is a cove, golden case Oct 22).
KINDS_MORE = [('nwr', r'.\brefuge\b|wetland management district|waterfowl production area'),
              # POTA's own common park types that the US key's table did not name (KPC owner run, 2026-11-13: 299 'State Fishing
              # Lake', 350 trails, 69 'State Historical Monument', 43 'State Reserve', 36 'National Memorial' parks had no kind)
              ('fl', r'fishing lake'), ('trl', r'\btrail\b'), ('hist', r'historic(al)? monument'),
              ('snp', r'state reserve|ecological reserve'), ('nps', r'national memorial')]
# Words that say 'a kind of place' on their own. A name that has one of these but no recognised kind ('Cedar Wildlife',
# 'Lake Z National', 'Cedar Management Area' with nothing else) carries an UNKNOWN kind word: UNCLEAR, never MATCH.
# (The trim tool grade 13d list: sp np nf refuge area wildlife management state national, plus the plain kind nouns.)
KINDISH = {'state', 'national', 'wildlife', 'management', 'area', 'refuge', 'park', 'forest', 'preserve', 'reserve', 'sanctuary',
           'monument', 'recreation', 'conservation', 'wilderness', 'seashore', 'lakeshore', 'grassland', 'grasslands', 'historic',
           'historical', 'game', 'habitat', 'natural', 'nature', 'memorial', 'battlefield', 'parkway', 'hatchery'}
# Words that are not part of the place's name (golden case: 'Gunnison Gorge BLM National Conservation Area' = '... NCA').
NOISE = {'blm', 'usfws', 'fws', 'usfs', 'nps', 'usace', 'the', 'of', 'and', 'a', 'an', 'at', 'designated'}


def expand(s):
    """The name with short kind forms written out ('Cedar SP' -> 'cedar state park'), lower case."""
    t = re.sub(r"[’'`ʻʼ‘]", '', str(s or '').lower().replace('&', ' and '))
    t = re.sub(r'[().,;:/\\\-–]', ' ', t)
    return ' '.join(SHORT_KINDS.get(w, w) for w in t.split())


def kinds_of(s):
    """(kinds, odd): the recognised kinds of place a name states, and whether it ALSO carries a kind-ish word that no
    recognised kind explains (only reported when no kind was recognised). Gap 1."""
    t = expand(s)
    k = kinds(t) | {c for c, r in KINDS_MORE if re.search(r, t)}
    if k:
        return k, False
    words = [w for w in re.findall(r'[a-z]+', t)]
    return set(), any(w in KINDISH for w in words[1:])   # a first word is a name word ('Forest Hills', 'Park City')


def park_kinds(park):
    """The park's kinds from its name AND its POTA type (as kpc_us_key.py line 1855: kinds(name) | kinds(typ))."""
    k1, o1 = kinds_of(park.get('name'))
    k2, o2 = kinds_of(park.get('type') or park.get('t') or '')
    k = k1 | k2
    return k, (o1 or o2) and not k


# Copied from kpc_us_key.py lines 179-279 (variants ... same_kind), unchanged.
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


# Gap 4 needs to see a word like 'Beach' or 'Lake' that may name a smaller place inside a bigger one, so the US key's SOFT
# list is split in two here: NEUTRAL words never name a separate place and are ignored; the rest of SOFT (lake, pond,
# reservoir, beach, forest, preserve, reserve ...) count as name words.
NEUTRAL = {'park', 'area', 'unit', 'tract', 'tracts', 'addition', 'complex', 'site', 'lands', 'land', 'center', 'centre', 'game',
           'mua', 'fwma', 'ca', 'pas'}


def plain_words(s, v=None):
    """The name's own words: norm() (or the given variant), singular, no neutral words, no noise words ('blm'), no years."""
    base = v if v is not None else norm(str(s or '').replace('(', ' ').replace(')', ' '))
    return {w for w in _sing(base).split() if w not in NOISE and w not in NEUTRAL and not re.fullmatch(r'(19|20)\d\d', w)}


_SHORT_RE = re.compile(r'(?<=\S)(\s+)(' + '|'.join(sorted(SHORT_KINDS, key=len, reverse=True)) + r')\b\.?', re.I)


def long_kinds(s):
    """The name with short kind forms written out, keeping everything else ('Cedar NF' -> 'Cedar national forest'), so the
    name reading drops them as the generic words they are. Never the first word ('SP Ranch' stays a name)."""
    return _SHORT_RE.sub(lambda m: m.group(1) + SHORT_KINDS[m.group(2).lower()], str(s or ''))


def name_relation(park_name, rec_name):
    """How two names relate, read the US key's way:
         'exact'          the same name (generic words dropped; spelling variants of kpc_us_key.variants; one word written
                          as two, _nosp; a one-letter typo inside one long word, _ed1)
         'record_longer'  the record has up to 2 more words ('Keyhole' / 'Keyhole Reservoir') - kpc_us_key.same_words
         'park_longer'    the RECORD is the park's name minus up to 2 words ('Big Woods' for 'Big Woods Beach'): it may be
                          the bigger place around the park (gap 4)
         None             not the same name.
       Side words (Upper / Lower / North ...) must be on both or neither (kpc_us_key._side)."""
    if not str(park_name or '').strip() or not str(rec_name or '').strip():
        return None
    park_name, rec_name = long_kinds(park_name), long_kinds(rec_name)
    if park_name.strip().lower() == rec_name.strip().lower():
        return 'exact'
    if _side(park_name) != _side(rec_name):
        # kpc_match.score: 'Yates Lake' vs 'Yates Lake WEST' may be the whole or a part: never joined, a person looks
        drop = lambda s: ' '.join(w for w in re.split(r'[\s\-]+', s) if w.lower() not in SIDES)
        return 'side_differs' if name_relation(drop(park_name), drop(rec_name)) else None
    vp = [plain_words(park_name, x) for x in variants(park_name)]
    vr = [plain_words(rec_name, x) for x in variants(rec_name)]
    if any(a and a == b for a in vp for b in vr) or _nosp(park_name, rec_name):
        return 'exact'
    wp, wr = plain_words(park_name), plain_words(rec_name)
    if wp and wr and wr < wp and len(wp - wr) <= 2:
        return 'park_longer'
    if wp and wr and wp < wr and len(wr - wp) <= 2:
        big = [w for w in wp if len(w) > 2]
        if len(big) >= 2 or (len(big) == 1 and len(big[0]) >= 6):   # kpc_us_key.same_words: one long word, or two words
            return 'record_longer'
        return None
    sa, sb = _sing(norm(park_name)), _sing(norm(rec_name))
    if len(sa) >= 8 and len(sb) >= 8 and not re.search(r'\d', sa + sb) and _ed1(sa, sb):   # kpc_us_key.same_name: a one-letter
        return 'exact'                                                                  # typo in one long word ('Morraine')
    return None


def kinds_agree(ka, kb):
    """'agree' | 'clash' | 'unknown'. Gap 1: 'agree' needs a recognised kind on BOTH sides that agree (kpc_us_key.same_kind with
    its US_COMPAT pairs); one side without a kind = 'unknown', never 'agree'."""
    if not ka or not kb:
        return 'unknown'
    return 'agree' if same_kind(ka, kb) else 'clash'


# ======================================================================================================== pieces (rule 18)
# Copied from kpc_key_rules.py lines 237-303 (piece_words / piece_ok), its _ed1 renamed _ed1_piece (it differs from the
# US key's _ed1). Gap 3: here it is ON unless the caller turns it off (layer_info['piece_rule'] = False).
_PIECE = r'(?:sub ?unit|unit|tract|parcel|zone|division)'
_PIECE_SKIP = {'the', 'of', 'a', 'an', 'sub', 'state', 'national', 'wildlife', 'management', 'area', 'park', 'forest', 'refuge',
               'blm', 'recreation', 'special', 'wma',
               'forever', 'wild',
               'use'}   # Nov 3 step 3: 'Public Land USE Zone' (Alberta PLUZ, CA-6125) is a kind of place, not a piece called 'use'   # batch 1b (Quality): Alabama's 'Forever Wild Tract' is a program name, not a piece (US-12740, US-13081)
_COMPASS = {'n': 'north', 's': 'south', 'e': 'east', 'w': 'west', 'ne': 'northeast', 'nw': 'northwest', 'se': 'southeast', 'sw': 'southwest'}
_PIECE_WORD = re.compile(_PIECE)


def _compass(w):
    """batch 1b (Quality: US-13221 'Gordon W. Yeager-S.E. Unit' vs MN DNR 'Gordon W. Yeager WMA: South East Unit'): compass
    words written short or in two words become one word. 'ne' / 'nw' / 'se' / 'sw' always; a single n / s / e / w only right
    before a piece word ('E Unit'), so a middle initial ('Gordon W. Yeager') stays a name."""
    out = []
    for i, x in enumerate(w):
        nxt = w[i + 1] if i + 1 < len(w) else ''
        if len(x) == 2 and x in _COMPASS: x = _COMPASS[x]
        elif len(x) == 1 and x in _COMPASS and _PIECE_WORD.fullmatch(nxt): x = _COMPASS[x]
        if out and out[-1] in ('north', 'south') and x in ('east', 'west'): out[-1] += x; continue   # 'south east' = 'southeast'
        out.append(x)
    return out


def _plain_words(t):
    t = unicodedata.normalize('NFKD', str(t or '')).encode('ascii', 'ignore').decode().lower()
    t = re.sub(r"[\u2019'`.]", '', t).replace('-', ' ')
    return _compass(re.findall(r'[a-z0-9]+', t))


def piece_words(park_name, layer=''):
    """The words that name a piece in a POTA name: 'Abo' in 'Salinas Pueblo Missions, Abo Unit National Monument', 'Hilliard'
    in '... Hilliard Tract WMA', '2' in '... Unit 2'. Empty when the name names no piece.
    Nov 3 step 3 (Quality, CA-6125 Porcupine Hills PLUZ / NV herd areas): `layer` = the record layer's own label ('Public Land
    Use Zones', 'Wildlife Management Units'). A piece word that is part of the layer's own type ('zone' on a land-use-ZONE layer)
    says what KIND of place every record there is, not which piece: it is skipped."""
    w = _plain_words(park_name)
    lw = {x.rstrip('s') for x in _plain_words(layer)} if layer else set()
    out = set()
    for i, x in enumerate(w):
        if not re.fullmatch(_PIECE, x) and not (x == 'sub' and i + 1 < len(w) and w[i + 1] == 'unit'): continue
        if x in lw and i >= 1 and w[i - 1].rstrip('s') in lw: continue   # the layer's own type PHRASE ('land use zone'), not a piece; 'Anacua Unit' on a 'Management Units' layer is still a piece
        if x == 'sub': continue
        j = i - 1
        if j >= 0 and w[j] == 'sub': j -= 1
        if j >= 0 and w[j] not in _PIECE_SKIP: out.add(w[j])
        if i + 1 < len(w) and re.fullmatch(r'\d+|[ivx]+', w[i + 1]): out.add(w[i + 1])
        elif i + 2 < len(w) and w[i + 1] == 'no' and re.fullmatch(r'\d+|[ivx]+', w[i + 2]): out.add(w[i + 2])
    return out


def _ed1_piece(a, b):
    if a == b: return True
    if abs(len(a) - len(b)) > 1 or min(len(a), len(b)) < 5: return False
    if len(a) == len(b): return sum(x != y for x, y in zip(a, b)) == 1
    if len(a) > len(b): a, b = b, a
    return any(a == b[:i] + b[i + 1:] for i in range(len(b)))


def piece_ok(park_name, rec_name, rec_name2=None, layer=''):
    """(ok, why). ok unless the park names a piece and the record carries none of that piece's own words (a one-letter
    spelling difference in a long word counts: 'Dimmitt' / 'Dimmit'). `layer`: see piece_words."""
    pw = piece_words(park_name, layer)
    if not pw: return True, ''
    have = set(_plain_words(rec_name)) | set(_plain_words(rec_name2))
    miss = [p for p in sorted(pw) if p not in have and not (not p.isdigit() and any(_ed1_piece(p, h) for h in have))]
    if not miss: return True, ''
    return False, f"the park is the piece '{' '.join(miss)}' of a bigger area; '{rec_name}' does not name that piece (rule 18)"


# ======================================================================================================== pin and weighing
# Copied from kpc_match.py lines 30-179 (ADMIN, is_admin, geometry, W, JOIN_AT, MARGIN, score, decide, _apart).
import re as _re
ACRE_KM2 = 0.00404686   # kpc_match.py line 24
ADMIN = _re.compile(r'\b(field office|district office|ranger district|resource area|administrative unit|'
                    r'supervisor.?s office|management unit office)\b', _re.I)


def is_admin(name):
    return bool(ADMIN.search(str(name or '')))


def rings_of(g):
    # the US and Canada keep an ArcGIS geometry ({'rings': [...]}); the world keeps the bare list of rings
    if isinstance(g, list): return g
    return (g or {}).get('rings') or []


def inside(la, lo, g):
    """Is the point inside the outline (even-odd across every ring, so holes and islands count right)?"""
    hits = 0
    for r in rings_of(g):
        j = len(r) - 1
        ins = False
        for i in range(len(r)):
            xi, yi, xj, yj = r[i][0], r[i][1], r[j][0], r[j][1]
            if (yi > la) != (yj > la) and lo < (xj - xi) * (la - yi) / ((yj - yi) or 1e-15) + xi:
                ins = not ins
            j = i
        hits += ins
    return hits % 2 == 1


def km_to(la, lo, g):
    """Distance in km from the point to the outline's nearest edge; 0 when inside. None when there is no outline."""
    rs = rings_of(g)
    if not rs:
        return None
    if inside(la, lo, g):
        return 0.0
    kx, ky = 111.32 * math.cos(math.radians(la)), 110.57
    best = None
    for ring in rs:
        for i in range(len(ring) - 1):
            x1, y1 = (ring[i][0] - lo) * kx, (ring[i][1] - la) * ky
            x2, y2 = (ring[i + 1][0] - lo) * kx, (ring[i + 1][1] - la) * ky
            dx, dy = x2 - x1, y2 - y1
            L = dx * dx + dy * dy
            t = 0 if L == 0 else max(0.0, min(1.0, -(x1 * dx + y1 * dy) / L))
            d = math.hypot(x1 + t * dx, y1 + t * dy)
            if best is None or d < best:
                best = d
    return best


def size_km(acres):
    """A rough 'width' of the area in km, the square root of its area, never below ~0.2 km."""
    return math.sqrt(max((acres or 0) * ACRE_KM2, 0.05))

# ------------------------------------------------------------------------------------------------ the weighing
# Points. Tuned against measurement, never by feel: change a number, run the golden cases and the shadow
# comparison, and look at what moved before keeping it.
W = {
    'name_exact': 2,        # the names agree once read (generic words gone, accents gone, abbreviations expanded)
    'name_unique': 2,       # ...and no other area within ~10 km carries that name
    'name_words': 1,        # the shorter name's words all appear in the longer one
    'pin_inside': 3,        # POTA's pin falls inside the outline
    'pin_edge': 2,          # outside, but within 250 m or half the area's width: a car park, a gate
                            # (CO, Oct 22: 41 of 123 'outside' pins were within 100 m of the right park)
    'pin_far': 0,           # more than 3 widths away - reported, but NOT held against a match: POTA pins can be
                            # kilometres off (Vega State Park 7.9 km, Pike National Forest 18.8 km, both right)
    'pin_very_far': -3,     # more than 10 widths AND more than 20 km away
    'only_fit_holding_pin': 1,   # the smallest area of a fitting kind that the pin is inside (PIN_JOIN, generalised)
    'kind_clash': -1,       # both names say what kind of place they are, and the kinds differ ('Bayerischer Wald'
                            # National Park against the Bayerischer Wald Nature Park): a person should look
}
JOIN_AT = 4      # enough evidence to join without a person
MARGIN = 2       # and clearly better than the next-best place, or a person decides


def score(f):
    """f = facts about ONE park and ONE candidate area:
         kind_ok      the kinds of place are compatible (or one name gives no kind)       REQUIRED - else rejected
         side_ok      neither says Upper/Lower/North/South/East/West/Middle without the other  REQUIRED
         name_exact, name_unique, name_words      from the caller's own reading of the names
         pin          (lat, lon) of the park, or None
         g, acres     the candidate's outline and size
         smallest_fit True when this is the smallest area of a fitting kind that holds the pin
       Returns (points, reasons)."""
    if not f.get('kind_ok', True):
        return -99, ['a different kind of place']
    if not f.get('side_ok', True):
        # Upper/Lower White Oak Lake are two places; Yates Lake vs Yates Lake WEST may be the whole or a part. Never
        # joined either way - but worth a person's look when the names otherwise agree
        named = f.get('name_exact') or f.get('name_words')
        return (1 if named else -99), ['one name says Upper/Lower/North/South/East/West and the other does not']
    pts, why = 0, []
    if f.get('kind_clash'):
        pts += W['kind_clash']; why.append('the names say different kinds of place')
    if f.get('name_exact'):
        pts += W['name_exact']; why.append('same name')
        if f.get('name_unique'):
            pts += W['name_unique']; why.append('no other place nearby has that name')
    elif f.get('name_words'):
        pts += W['name_words']; why.append('same words')
    pin = f.get('pin')
    if pin and pin[0] is not None:
        d = km_to(pin[0], pin[1], f.get('g'))
        f['km'] = d
        if d is None:
            why.append('no outline to check the pin against')
        elif d == 0:
            pts += W['pin_inside']; why.append('pin inside')
            if f.get('smallest_fit'):
                pts += W['only_fit_holding_pin']; why.append('smallest fitting area holding the pin')
        else:
            rel = d / size_km(f.get('acres'))
            if d <= 0.25 or rel <= 0.5:
                pts += W['pin_edge']; why.append(f'pin {d:.2f} km outside (at the edge)')
            elif rel > 10 and d > 20:
                pts += W['pin_very_far']; why.append(f'pin {d:.0f} km away')
            elif rel > 3:
                pts += W['pin_far']; why.append(f'pin {d:.1f} km off')
            else:
                why.append(f'pin {d:.1f} km outside')
    return pts, why


def decide_groups(groups):   # kpc_match.decide, renamed here: decide() below is the matcher's entry
    """groups = [(points, reasons, members)] - one entry per distinct PLACE (all the parcels of one area together).
    Returns ('join' | 'check' | 'none', best_group, runner_up_group)."""
    live = sorted([g for g in groups if g[0] > -50], key=lambda g: -g[0])
    if not live:
        return 'none', None, None
    best = live[0]
    # A place that matches the park's NAME is not seriously rivalled by one that merely holds the pin: in the US
    # the pin sits inside reservoirs, trust land and forests around half the wildlife areas (Fort Lyon SWA lost to
    # John Martin Reservoir that way on Oct 22). Where nothing matches by name (unreadable names abroad), every
    # candidate is a rival as before.
    def named(g): return any(w in ('same name', 'same words') for w in g[1])
    rivals = [g for g in live[1:] if named(g)] if named(best) else live[1:]
    runner = rivals[0] if rivals else None
    if best[0] >= JOIN_AT and (runner is None or best[0] - runner[0] >= MARGIN):
        return 'join', best, runner
    if best[0] >= 1:
        return 'check', best, runner
    return 'none', best, runner

def _apart(b1, b2, pad=0.1):
    return b1[2] + pad < b2[0] or b2[2] + pad < b1[0] or b1[3] + pad < b2[1] or b2[3] + pad < b1[1]

# The pin rule (gap 5), from existing numbers only:
EDGE_KM = 0.25          # kpc_match.py score(): 'd <= 0.25 or rel <= 0.5' = at the edge (a gate, a car park)
EDGE_WIDTHS = 0.5
NEAR_WIDTHS = 3.0       # kpc_match.py: more than 3 widths = 'pin far'
VERY_FAR_WIDTHS = 10.0  # kpc_match.py: more than 10 widths AND more than 20 km = 'pin very far'
VERY_FAR_KM = 20.0
FAR_KM = 15.0           # kpc_join_check.py FAR_KM: a join with the pin farther than this is held for a person
# The acres rules:
ACRE_TOL = 0.15         # kpc_problem_solver.py ACRE_TOL (line 734): the auto-confirm acres test
ACRE_RATIO = (0.5, 2.0) # kpc_join_check.py RATIO (line 41): outside this a MATCH goes back to a person
# A park inside a park:
NEST_SHARE = 0.9        # kpc_tracts.py NEST_SHARE (line 28): 90% of the smaller outline inside the bigger one
EDGE_M = 30             # kpc_tracts.nested_geometry: points within 30 m of the edge count as inside
APART_DEG = 0.1         # kpc_match._apart default pad: same-name pieces further apart than this are separate places


def pin_tolerance_km(acres):
    """How far outside its outline a pin may be and still MATCH: max(0.25 km, half the land's width), never over 15 km.
    Width = kpc_match.size_km(acres) (square root of the area). 40 acres -> 0.25 km; 1,000 ac -> 0.5 km; 100,000 ac -> 6.4 km."""
    return min(max(EDGE_KM, EDGE_WIDTHS * size_km(acres)), FAR_KM)


def pin_class(km, acres):
    """'inside' | 'edge' | 'near' | 'far' | 'very_far' | 'unknown' for a pin `km` from an outline of `acres`."""
    if km is None:
        return 'unknown'
    if km == 0:
        return 'inside'
    rel = km / size_km(acres)
    if km <= pin_tolerance_km(acres):
        return 'edge'
    if rel > VERY_FAR_WIDTHS and km > VERY_FAR_KM:
        return 'very_far'
    if rel > NEAR_WIDTHS or km > FAR_KM:
        return 'far'
    return 'near'


# Copied from kpc_tracts.py lines 243-248.
def _sample(rings, n=40):
    pts = [p for r in rings for p in r[:-1]] if rings else []
    if len(pts) <= n: return pts
    step = len(pts) / n
    return [pts[int(i * step)] for i in range(n)]


def to_rings(g):
    """Rings [[lon, lat], ...] from an ArcGIS geometry ({'rings': ...}), a GeoJSON Polygon / MultiPolygon, or a bare ring list."""
    if not g:
        return []
    if isinstance(g, list):
        if g and g[0] and isinstance(g[0][0], (int, float)):
            return [g]
        if g and g[0] and g[0][0] and isinstance(g[0][0][0], (list, tuple)):   # list of polygons
            return [r for poly in g for r in poly]
        return g
    if 'rings' in g:
        return g.get('rings') or []
    t, c = g.get('type'), g.get('coordinates') or []
    if t == 'Polygon':
        return list(c)
    if t == 'MultiPolygon':
        return [r for poly in c for r in poly]
    if t == 'GeometryCollection':
        return [r for x in g.get('geometries') or [] for r in to_rings(x)]
    return []


def bbox_of(rings):
    xs = [p[0] for r in rings for p in r]; ys = [p[1] for r in rings for p in r]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


def _ring_km2(r, la0):
    kx, ky = 111.32 * math.cos(math.radians(la0)), 110.57
    s = 0.0
    for i in range(len(r) - 1):
        s += (r[i][0] * kx) * (r[i + 1][1] * ky) - (r[i + 1][0] * kx) * (r[i][1] * ky)
    return abs(s) / 2


def acres_of(rings):
    """Rough acres of an outline (flat-earth, holes taken out by the even-odd rule). Used only when a record states none."""
    rs = [r for r in rings or [] if r and len(r) >= 4]
    if not rs:
        return 0.0
    la0 = sum(p[1] for r in rs for p in r) / sum(len(r) for r in rs)
    tot = 0.0
    for i, r in enumerate(rs):
        a = _ring_km2(r, la0)
        p = r[0]
        depth = sum(1 for j, o in enumerate(rs) if j != i and inside(p[1], p[0], [o]))
        tot += -a if depth % 2 else a
    return max(tot, 0.0) / ACRE_KM2


def nested_share(inner, outer):
    """Share (0..1) of the inner outline's sampled points that lie inside the outer outline or within 30 m of its edge
    (kpc_tracts.nested_geometry's test, stdlib geometry from kpc_match)."""
    pts = _sample([r for r in inner if r and len(r) >= 3])
    if not pts or not outer:
        return 0.0
    n = 0
    for x, y in pts:
        d = km_to(y, x, {'rings': outer})
        if d is not None and d * 1000 <= EDGE_M:
            n += 1
    return n / len(pts)


# ======================================================================================================== one record
def _office_name(c):
    nm, n2 = str(c.get('name') or ''), c.get('name2')
    if (is_admin(nm) or re.search(r'field office|district office|ranger district', nm, re.I)) and n2 and not is_admin(n2):
        return n2, None   # kpc_us_key.join_how: an office's own name is not the place; its second name is tested instead
    return nm, n2


def record_kinds(c, layer_info=None):
    """(kinds, where_from, odd) for one record. Gap 2: from its name; a bare name takes its kind from the record's own class
    field (c['kind']), the PAD-US designation (PAD-US layers only: c['des'] code via the US key's DES table, or c['des_name']
    text), or the layer's declared kind (layer_info['kind']), in that order."""
    li = layer_info or {}
    nm, n2 = _office_name(c)
    k, odd = kinds_of(nm)
    if k:
        return k, 'name', False
    if n2:
        k2, odd2 = kinds_of(n2)
        if k2:
            return k2, 'second name', False
        odd = odd or odd2
    if c.get('kind'):
        kc, _ = kinds_of(c['kind'])
        if kc:
            return kc, "the record's own class field", odd
    if c.get('layer_kinds'):   # records from several layers in one call: each record's own layer's declared kind codes
        kl = {str(x) for x in c['layer_kinds'] if x}
        if kl:
            return kl, "its layer's declared kind", odd
    if c.get('layer_kind'):
        kl, _ = kinds_of(c['layer_kind'])
        if kl:
            return kl, "its layer's declared kind", odd
    if li.get('padus'):
        d = str(c.get('des') or '').strip().upper()
        if d in DES:
            return {DES[d]}, f'PAD-US designation {d}', odd
        if c.get('des_name'):
            kd, _ = kinds_of(c['des_name'])
            if kd:
                return kd, 'PAD-US designation', odd
    if li.get('kind'):
        kl, _ = kinds_of(li['kind'])
        if kl:
            return kl, "the layer's declared kind", odd
    return set(), '', odd


def _hatchery_trail_ok(pn, rn, kp, kr):
    """kpc_us_key.name_ok: a hatchery only joins a hatchery, a trail only joins a trail."""
    if ('nfh' in kp) != ('nfh' in kr):
        return False
    return bool(re.search(r'\btrail\b', str(pn), re.I)) == bool(re.search(r'\btrail\b', str(rn), re.I))


def assess(park, c, layer_info=None):
    """Plain facts about ONE park and ONE record (no decision). Pure."""
    li = layer_info or {}
    pn = park.get('name') or ''
    nm, n2 = _office_name(c)
    f = {'id': c.get('id'), 'name': c.get('name') or '', 'office': False, 'rel': None, 'why_out': ''}
    if is_admin(nm) or re.search(r'field office|district office|ranger district', str(nm), re.I):
        f['office'] = True; f['why_out'] = f"'{nm}' is an office or district, not a park"
    rels = [name_relation(pn, x) for x in (nm, n2) if x]
    order = ['exact', 'record_longer', 'park_longer', 'side_differs']
    f['rel'] = next((r for r in order if r in rels), None)
    kp, podd = park_kinds(park)
    kr, ksrc, rodd = record_kinds(c, li)
    f.update(kp=kp, park_odd=podd, kr=kr, kind_from=ksrc, rec_odd=rodd, kind=kinds_agree(kp, kr))
    if f['rel'] and not _hatchery_trail_ok(pn, nm, kp, kr):
        f['rel'] = None; f['why_out'] = 'a hatchery only joins a hatchery and a trail only a trail'
    if f['rel'] and li.get('piece_rule', True):
        ok, why = piece_ok(pn, nm, n2, li.get('label') or '')
        if not ok:
            f['rel'] = None; f['why_out'] = why
    rings = to_rings(c.get('rings') or c.get('geometry'))
    f['rings'] = rings
    f['bb'] = c.get('bbox') or bbox_of(rings)
    ac = c.get('acres')
    f['acres'] = float(ac) if isinstance(ac, (int, float)) and ac > 0 else (acres_of(rings) if rings else 0.0)
    la, lo = park.get('lat'), park.get('lon')
    f['km'] = km_to(la, lo, {'rings': rings}) if (la is not None and lo is not None and rings) else None
    f['pin'] = pin_class(f['km'], f['acres'])
    f['agency'] = c.get('agency')
    f['wdpa'] = rec_wdpa_ids(c)
    return f


# ======================================================================================================== places
def _places(fs):
    """Group the name-matching records into PLACES: the same name read and linked (boxes within 0.1 degree), or overlapping
    (kpc_match.choose). Two Beaver Creeks a county apart are two places."""
    par = list(range(len(fs)))
    def g(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for i in range(len(fs)):
        for j in range(i + 1, len(fs)):
            a, b = fs[i], fs[j]
            if not a['bb'] or not b['bb']:
                if not a['bb'] and not b['bb']:
                    par[g(i)] = g(j)   # no outline on either: one place as far as anyone can tell
                continue
            if not _apart(a['bb'], b['bb'], APART_DEG):
                par[g(i)] = g(j)
    out = {}
    for i, f in enumerate(fs):
        out.setdefault(g(i), []).append(f)
    return list(out.values())


def _place_km(p):
    ks = [f['km'] for f in p if f['km'] is not None]
    return min(ks) if ks else None


def _place_pin(p):
    """The pin class of a place: measured against the nearest record, sized by the whole place's acres."""
    km = _place_km(p)
    return pin_class(km, sum(f['acres'] for f in p)), km


def _ids(fs): return [f['id'] for f in fs]


def _res(outcome, likely, reason, **kw):
    r = {'outcome': outcome, 'likely': likely if outcome == UNCLEAR else None, 'reason': reason, 'records': [], 'tracts': [],
         'not_joined': [], 'far_same_name': [], 'maybe': [], 'flags': [], 'auto_confirmed': False, 'points': None,
         'pin_km': None, 'pin': 'unknown', 'checks': {}, 'private': False}
    r.update(kw)
    return r


def _pin_words(pc, km, acres):
    tol = pin_tolerance_km(acres)
    if pc == 'inside': return 'the pin is inside the outline'
    if pc == 'edge': return f'the pin is {km:.2f} km outside the outline, within the {tol:.2f} km allowed for land this size (gate or car park)'
    if pc == 'near': return f'the pin is {km:.1f} km outside the outline (more than the {tol:.2f} km allowed for land this size)'
    if pc == 'far': return f'the pin is {km:.1f} km from the outline (far for land this size, or over {FAR_KM:.0f} km)'
    if pc == 'very_far': return f'the pin is {km:.0f} km away (over {VERY_FAR_WIDTHS:.0f} widths of the land and over {VERY_FAR_KM:.0f} km)'
    return 'there is no outline or no pin to test the pin against'


KIND_NAMES = {'wma': 'a wildlife area', 'wsr': 'a wild and scenic river', 'ca': 'a conservation area', 'snp': 'a nature preserve',
              'hist': 'a historic site', 'sp': 'a state park or recreation area', 'nf': 'a national forest', 'sf': 'a state forest',
              'nwr': 'a wildlife refuge', 'nfh': 'a fish hatchery', 'nps': 'a national park unit', 'wild': 'a wilderness',
              'wsa': 'a wilderness study area', 'hma': 'a herd area', 'rma': 'a recreation site', 'air': 'an airstrip',
              'trh': 'a trailhead'}
PERSON_TXT = ' A person confirms (owner rule 2026-11-13: never joined automatically on name alone).'


def _kind_words(k):
    return ' / '.join(KIND_NAMES.get(x, x) for x in sorted(k)) if k else 'no kind stated'


def _decide_names(park, candidates, layer_info=None, other_parks=None):
    """The name + kind + pin decision (decide() adds the WDPA id step around it) for one park against one layer's records.
       park        {ref, name, type (POTA type), lat, lon} + optional evidence: official_acres, agency, web, page_kind
       candidates  [{id, name, name2?, kind?, des?, des_name?, acres?, rings | geometry?, bbox?, agency?}]
       layer_info  {source, padus (bool), kind (the layer's declared kind, e.g. 'State Forest'), label, piece_rule (default True)}
       other_parks optional [{ref, name, lat, lon}]: other POTA parks, so a far same-name place can be named as theirs
       Returns {outcome MATCH | UNCLEAR | NO, likely 'yes'|'no' (UNCLEAR only), reason (plain English), records [ids],
                tracts [{id, name, km}], not_joined [{id, name, why}], far_same_name [...], maybe [...], flags [...],
                auto_confirmed, points, pin, pin_km, checks}."""
    li = layer_info or {}
    fs = [assess(park, c, li) for c in candidates or []]
    named = [f for f in fs if f['rel'] and not f['office']]
    not_joined = [{'id': f['id'], 'name': f['name'], 'why': f['why_out']} for f in fs if f['why_out'] and f not in named]
    sided = [f for f in fs if f['rel'] == 'side_differs' and not f['office']]
    named = [f for f in named if f['rel'] != 'side_differs']
    if not named and sided:
        f0 = min(sided, key=lambda f: (f['km'] is None, f['km'] or 0))
        return _res(UNCLEAR, 'no', f"'{f0['name']}' has the park's name but one of the two says Upper / Lower / North / South / "
                    "East / West / Middle and the other does not: it may be a part of the park or another place",
                    not_joined=not_joined, flags=['side_differs'], maybe=_ids(sided), pin=f0['pin'], pin_km=f0['km'])
    if not named:
        why = 'no record in this layer has the park\'s name'
        if not_joined:
            why += '; ' + '; '.join(f"{x['name']}: {x['why']}" for x in not_joined[:3])
        return _res(NO, None, why, not_joined=not_joined)

    own = [f for f in named if f['rel'] in ('exact', 'record_longer')]
    bigger = [f for f in named if f['rel'] == 'park_longer']
    flags = []
    # Gap 4: a record whose name is the park's name minus words is the bigger place around it. Never joined.
    if own:
        for f in bigger:
            not_joined.append({'id': f['id'], 'name': f['name'], 'why': 'its name is shorter than the park\'s: the bigger place around this park, not the park'})
    else:
        f0 = min(bigger, key=lambda f: (f['km'] is None, f['km'] or 0))
        return _res(UNCLEAR, 'no', f"only '{f0['name']}' has the park's name, minus words: it is probably the bigger place around this "
                    "park. The park's own outline is not in this layer. A person decides; it is never joined automatically.",
                    not_joined=not_joined, flags=['bigger_place'], maybe=_ids(bigger), pin=f0['pin'], pin_km=f0['km'])

    # Gap 4, the other way: a record with extra words of its own lying >= 90% inside an exact-name record is another park inside
    exact = [f for f in own if f['rel'] == 'exact']
    keep = []
    for f in own:
        if f['rel'] == 'record_longer' and f['rings'] and any(e['rings'] and e['acres'] > f['acres'] * 1.05 and
                                                             nested_share(f['rings'], e['rings']) >= NEST_SHARE for e in exact):
            not_joined.append({'id': f['id'], 'name': f['name'], 'why': 'a smaller place with its own name lying inside the park (90% or more): its own park, not a tract of this one'})
            flags.append('sub_park_left_out')
        else:
            keep.append(f)
    own = keep

    # a record with neither an outline nor a box cannot be placed: listed (never dropped silently), never a 'far' place
    unplaced = [f for f in own if not f['bb'] and not f['rings']]
    if unplaced and len(unplaced) < len(own):
        own = [f for f in own if f not in unplaced]
        flags.append('unplaced_records')
    else:
        unplaced = []
    places = _places(own)
    for p in places:
        p.sort(key=lambda f: (f['km'] is None, f['km'] or 0))
    scored = []
    for p in places:
        pc, km = _place_pin(p)
        scored.append((pc, km, p))
    rank = {'inside': 0, 'edge': 1, 'near': 2, 'far': 3, 'very_far': 4, 'unknown': 5}
    scored.sort(key=lambda x: (rank[x[0]], x[1] if x[1] is not None else 1e9))
    pc, km, best = scored[0]
    others = scored[1:]
    # Gap 8: other same-name places are listed, never joined to this park.
    far_same = []
    for opc, okm, p in others:
        owner = None
        for op in other_parks or []:
            if op.get('ref') == park.get('ref') or op.get('lat') is None:
                continue
            if name_relation(park.get('name'), op.get('name')) == 'exact':
                dk = min((km_to(op['lat'], op['lon'], {'rings': f['rings']}) for f in p if f['rings']), default=None)
                if dk is not None and dk <= pin_tolerance_km(sum(f['acres'] for f in p)):
                    owner = op.get('ref')
        far_same.append({'ids': _ids(p), 'names': sorted({f['name'] for f in p}), 'km': okm, 'pin': opc, 'belongs_to': owner})
    # Gap 7 + the tie rule: two separate places that both fit the pin = a person decides
    rivals = [x for x in others if x[0] in ('inside', 'edge')]
    acres = sum(f['acres'] for f in best)

    agree = [f for f in best if f['kind'] == 'agree']
    clash = [f for f in best if f['kind'] == 'clash']
    unknown = [f for f in best if f['kind'] == 'unknown']
    for f in unplaced:
        not_joined.append({'id': f['id'], 'name': f['name'], 'why': 'same name, but it has no outline or box to place it: a person checks'})
    base = dict(not_joined=not_joined, far_same_name=far_same, flags=flags, pin=pc, pin_km=km)
    pinw = _pin_words(pc, km, acres)

    if pc == 'very_far':
        return _res(NO, None, f'same name, but {pinw}', **base)
    if rivals:
        return _res(UNCLEAR, 'yes', f"{len(rivals) + 1} separate places with this name fit the pin; a person picks one",
                    maybe=_ids(best) + [i for x in rivals for i in _ids(x[2])], **base)

    if agree:
        sel = agree
        sel_pc, sel_km = _place_pin(sel)
        sel_ac = sum(f['acres'] for f in sel)
        pinw = _pin_words(sel_pc, sel_km, sel_ac)
        for f in clash:
            not_joined.append({'id': f['id'], 'name': f['name'], 'why': f"same name but another kind of place ({_kind_words(f['kr'])} vs the park's {_kind_words(f['kp'])})"})
        maybe = _ids(unknown)   # same name, no kind stated: never passed, never dropped silently (listed + named in the reason)
        tail = ''
        if unknown:
            flags.append('tract_kind_unknown')
            tail = ('; not included: ' + ', '.join(f"'{f['name']}'" for f in unknown[:3]) +
                    ' (same name, but no kind of place stated: a person checks whether it is a tract of this park)')
        rel = 'exact' if any(f['rel'] == 'exact' for f in sel) else 'record_longer'
        facts = {'kind_ok': True, 'side_ok': True, 'name_exact': rel == 'exact', 'name_words': rel == 'record_longer',
                 'name_unique': not far_same, 'pin': None}
        pts, _w = score(facts)
        pts += {'inside': W['pin_inside'], 'edge': W['pin_edge']}.get(sel_pc, 0)
        kindw = f"same name and the same kind of place ({_kind_words(sel[0]['kr'] & sel[0]['kp']) or _kind_words(sel[0]['kr'])})"
        if rel == 'record_longer':
            kindw = f"the record's name has the park's words plus up to two more, same kind of place ({_kind_words(sel[0]['kr'])})"
        extra = dict(base, pin=sel_pc, pin_km=sel_km, points=pts)
        if sel_pc in ('inside', 'edge') and pts >= JOIN_AT:
            out = _res(MATCH, None, f'{kindw}; {pinw}' + (f'; {len(sel)} tracts' if len(sel) > 1 else '') + tail, records=_ids(sel),
                       tracts=[{'id': f['id'], 'name': f['name'], 'km': f['km']} for f in sel], maybe=maybe, **extra)
            off = park.get('official_acres')
            if isinstance(off, (int, float)) and off > 0 and sel_ac > 0 and not (ACRE_RATIO[0] <= sel_ac / off <= ACRE_RATIO[1]):
                out.update(outcome=UNCLEAR, likely='yes', records=[], flags=flags + ['acres_disagree'],
                           reason=f"{kindw}; {pinw}; but the outline is {sel_ac:,.0f} acres against the official {off:,.0f} "
                                  f"(outside {ACRE_RATIO[0]}x-{ACRE_RATIO[1]}x): a person checks", maybe=_ids(sel) + maybe)
            return out
        if sel_pc in ('inside', 'edge'):   # 'record_longer' at the edge: 1 + 2 points, under JOIN_AT
            return second_opinion(park, _res(UNCLEAR, 'yes', f'{kindw}; {pinw}; not enough to join on its own', maybe=_ids(sel) + maybe, **extra), sel, far_same)
        if sel_pc == 'unknown':
            return _res(UNCLEAR, 'yes', f'{kindw}; {pinw}', maybe=_ids(sel) + maybe, **extra)
        if sel_pc == 'near':
            return second_opinion(park, _res(UNCLEAR, 'yes', f'{kindw}; {pinw}', maybe=_ids(sel) + maybe, **extra), sel, far_same)
        return _res(UNCLEAR, 'no', f'{kindw}; but {pinw}', maybe=_ids(sel) + maybe, **extra)

    if clash:   # owner decision 2026-11-13 (gap 6): same name, different kind
        sel_pc, sel_km = _place_pin(clash)
        sel_ac = sum(f['acres'] for f in clash)
        pinw = _pin_words(sel_pc, sel_km, sel_ac)
        f0 = clash[0]
        w = (f"same name but a different kind of place: the park is {_kind_words(f0['kp'])}, '{f0['name']}' is "
             f"{_kind_words(f0['kr'])} (from {f0['kind_from']})")
        extra = dict(base, pin=sel_pc, pin_km=sel_km, flags=flags + ['kind_differs'], maybe=_ids(clash))
        if sel_pc in ('inside', 'edge'):
            return second_opinion(park, _res(UNCLEAR, 'yes', f'{w}; {pinw}.' + PERSON_TXT, **extra), clash, far_same)
        if sel_pc in ('near', 'unknown'):
            return _res(UNCLEAR, 'no', f'{w}; {pinw}', **extra)
        return _res(NO, None, f'{w}; and {pinw}', **dict(extra, maybe=[]))

    # only records whose kind is not known on one side (gap 1 / gap 2)
    sel_pc, sel_km = _place_pin(unknown)
    sel_ac = sum(f['acres'] for f in unknown)
    pinw = _pin_words(sel_pc, sel_km, sel_ac)
    f0 = unknown[0]
    if not f0['kp']:
        side = "the park's name and POTA type state no kind of place" + (' (or an unknown one)' if f0['park_odd'] else '')
    elif f0['rec_odd']:
        side = f"'{f0['name']}' carries a kind word that is not a recognised kind"
    else:
        side = f"'{f0['name']}' is a bare name: it states no kind of place, and neither does the layer"
    w = f'same name, but {side}'
    extra = dict(base, pin=sel_pc, pin_km=sel_km, flags=flags + ['kind_unknown'], maybe=_ids(unknown))
    if sel_pc in ('inside', 'edge'):
        return second_opinion(park, _res(UNCLEAR, 'yes', f'{w}; {pinw}', **extra), unknown, far_same)
    if sel_pc == 'near':
        return second_opinion(park, _res(UNCLEAR, 'yes', f'{w}; {pinw}', **extra), unknown, far_same)
    if sel_pc == 'unknown':
        return _res(UNCLEAR, 'yes', f'{w}; {pinw}', **extra)
    return _res(UNCLEAR, 'no', f'{w}; and {pinw}', **extra)


# ======================================================================================================== the WDPA site id (owner, 2026-11-13)
# POTA stores some parks' WDPA site id, mostly as a Protected Planet address on the park website (2,491 of 81,438 parks in KPC-Data
# data/parkinfo on 2026-11-13; 0 US parks). Copied from kpc_problem_solver.py lines 58-104 (WDPA_URL_RE, pota_wdpa_id, rec_wdpa_ids).
# WDPA stays PRIVATE: a result that used a WDPA layer is marked private=True; its names, shapes and record ids must never be
# written to a public file. The park's own id comes from POTA, not from WDPA.
WDPA_URL_RE = re.compile(r'protectedplanet\.net/(?:en/)?(?:sites/)?([0-9]+)|dopa-explorer\.jrc\.ec\.europa\.eu/wdpa/([0-9]+)', re.I)


def park_wdpa_id(park):
    """The WDPA site id POTA stores for the park (park['wdpa_id'], or the number in a Protected Planet address in park['web']), or None."""
    park = park or {}
    for k in ('wdpa_id', 'wdpaid', 'pota_wdpa_id'):
        v = park.get(k)
        if v not in (None, '', 0, '0'):
            try:
                return int(str(v).strip())
            except ValueError:
                pass
    m = WDPA_URL_RE.search(str(park.get('web') or park.get('website') or ''))
    if m:
        return int(m.group(1) or m.group(2))
    return None


def rec_wdpa_ids(c):
    """WDPA site ids a record carries in its OWN fields (WDPAID / WDPA_PID / SITE_ID ...), top level or in c['attrs']."""
    ids = set()
    for blob in (c, c.get('attrs') if isinstance(c, dict) else None):
        if not isinstance(blob, dict):
            continue
        for k, v in blob.items():
            if k == 'id' or v in (None, ''):
                continue
            kl = re.sub(r'[^a-z0-9]', '', str(k).lower())
            if kl in ('wdpaid', 'wdpapid', 'siteid', 'sitepid', 'wdpaids') or kl.endswith('wdpaid'):
                for x in (v if isinstance(v, (list, tuple, set)) else [v]):
                    try:
                        ids.add(int(str(x).split('_')[0].strip()))
                    except ValueError:
                        pass
    ids.discard(0)
    return ids


def decide(park, candidates, layer_info=None, other_parks=None):
    """THE decision for one park against one layer's records.
       park        {ref, name, type (POTA type), lat, lon} + optional evidence: official_acres, agency, web, page_kind, wdpa_id
       candidates  [{id, name, name2?, kind?, layer_kinds?, layer_kind?, des?, des_name?, acres?, rings | geometry?, bbox?, agency?,
                     attrs?}] (a WDPAID / WDPA_PID field, top level or in attrs, is read as the record's own WDPA id)
       layer_info  {source, padus (bool), wdpa (bool: the PRIVATE WDPA layer), kind (the layer's declared kind), label,
                    piece_rule (default True)}
       other_parks optional [{ref, name, lat, lon}]: other POTA parks, so a far same-name place can be named as theirs
       Returns {outcome MATCH | UNCLEAR | NO, likely 'yes'|'no' (UNCLEAR only), reason (plain English), records [ids],
                tracts [{id, name, km}], not_joined [{id, name, why}], far_same_name [...], maybe [...], flags [...],
                auto_confirmed, points, pin, pin_km, checks, private}.
       WDPA id (owner, 2026-11-13): on the PRIVATE WDPA layer an exact id equality with POTA's id is strong evidence (MATCH when
       the pin is not far). On a public layer it is only a cross-check, and only when the public record itself carries the id
       field: a different id sends a MATCH back to a person; the same id never joins anything by itself."""
    li = layer_info or {}
    pw = park_wdpa_id(park)
    private = bool(li.get('wdpa'))
    if private and pw is not None:
        fs = [assess(park, c, li) for c in candidates or []]
        hit = [f for f in fs if pw in f['wdpa']]
        if hit:
            pc, km = _place_pin(hit)
            ac = sum(f['acres'] for f in hit)
            if pc in ('inside', 'edge', 'near', 'unknown'):
                r = _res(MATCH, None, f'the record carries the same WDPA site id as POTA ({pw}); {_pin_words(pc, km, ac)}',
                         records=_ids(hit), tracts=[{'id': f['id'], 'name': f['name'], 'km': f['km']} for f in hit],
                         flags=['wdpa_id'], pin=pc, pin_km=km)
            else:
                r = _res(UNCLEAR, 'no', f'the record carries the same WDPA site id as POTA ({pw}), but {_pin_words(pc, km, ac)}',
                         flags=['wdpa_id'], maybe=_ids(hit), pin=pc, pin_km=km)
            r['private'] = True
            r['checks']['wdpa'] = True
            return r
    r = _decide_names(park, candidates, li, other_parks)
    r['private'] = private
    if pw is not None and not private and r['records']:
        byid = {str(c.get('id')): rec_wdpa_ids(c) for c in candidates or []}
        carried = [byid.get(str(i)) for i in r['records'] if byid.get(str(i))]
        if carried:
            same = all(pw in s for s in carried)
            r['checks']['wdpa'] = same
            if not same:
                r.update(outcome=UNCLEAR, likely='yes', records=[], auto_confirmed=False, flags=r['flags'] + ['wdpa_differs'],
                         maybe=[str(i) for i in byid if byid[i]] if not r.get('maybe') else r['maybe'],
                         reason=r['reason'].rstrip(' .') + f". But the record's own WDPA id differs from POTA's ({pw}): a person checks")
    return r


# ======================================================================================================== second opinion
FED_HOSTS = {'nps.gov': 'NPS', 'fws.gov': 'FWS', 'fs.usda.gov': 'USFS', 'fs.fed.us': 'USFS', 'blm.gov': 'BLM',
             'usace.army.mil': 'USACE', 'recreation.gov': None}
AGENCY_LEVEL = {'NPS': 'FED', 'FWS': 'FED', 'USFS': 'FED', 'BLM': 'FED', 'USACE': 'FED', 'FED': 'FED', 'STAT': 'STAT', 'STATE': 'STAT'}


def host_of(url):
    m = re.match(r'^[a-z]+://([^/:?#]+)', str(url or '').strip().lower())
    return m.group(1) if m else ''


def agency_from_web(url):
    """The agency an official page address shows, only for the federal land agencies' own hosts (nps.gov, fws.gov,
    fs.usda.gov, blm.gov, usace.army.mil); None for anything else (no guessing state hosts)."""
    h = host_of(url)
    for k, v in FED_HOSTS.items():
        if h == k or h.endswith('.' + k):
            return v
    return None


def agencies_agree(a, b):
    """True / False when both sides state an agency, None when either is missing. Compared at the level the data allows
    (an agency name, or FED / STAT as PAD-US Own_Type / Mang_Type give it)."""
    if not a or not b:
        return None
    a, b = str(a).upper().strip(), str(b).upper().strip()
    if a == b:
        return True
    la, lb = AGENCY_LEVEL.get(a), AGENCY_LEVEL.get(b)
    if la and lb and (a in ('FED', 'STAT', 'STATE') or b in ('FED', 'STAT', 'STATE')):
        return la == lb
    return False


def second_opinion(park, res, sel, far_same=None):
    """Auto-confirm (owner, 2026-11-13): an UNCLEAR-likely-yes becomes MATCH, recorded as auto-confirmed with its reasons, only
    when ALL of these hold; otherwise it stays UNCLEAR and res['checks'] says which test was missing or failed:
      acres   the park's official acres (park['official_acres'], gathered elsewhere) within 15% of the outline's acres
              (kpc_problem_solver.ACRE_TOL)
      pin     the pin inside the outline (not merely near it)
      only    the only place of this name within the distance rule (no other same-name place inside the pin tolerance)
      agency  where both sides state one, the managing agency agrees (park['agency'] or the official page's host vs the
              record's agency); not stated on a side = not counted against
      page    where the park's official page states a kind of place (park['page_kind']), it agrees with the record's kind
    Never for the bigger place around a small park (flag 'bigger_place'), never on a tie between places."""
    if res.get('outcome') != UNCLEAR or res.get('likely') != 'yes' or 'bigger_place' in res.get('flags', []):
        return res
    chk = {}
    off = park.get('official_acres')
    ac = sum(f['acres'] for f in sel)
    if isinstance(off, (int, float)) and off > 0 and ac > 0:
        chk['acres'] = abs(ac - off) / off <= ACRE_TOL
    else:
        chk['acres'] = None
    chk['pin'] = res.get('pin') == 'inside'
    tol = pin_tolerance_km(ac)
    chk['only'] = not any(x.get('km') is not None and x['km'] <= max(tol, FAR_KM) for x in (far_same or []))
    pa = park.get('agency') or agency_from_web(park.get('web'))
    ra = next((f.get('agency') for f in sel if f.get('agency')), None)
    chk['agency'] = agencies_agree(pa, ra)
    pk = park.get('page_kind')
    if pk:
        k, _ = kinds_of(pk)
        chk['page'] = kinds_agree(k, set().union(*[f['kr'] for f in sel])) != 'clash' if k else None
    else:
        chk['page'] = None
    res['checks'] = chk
    ok = chk['acres'] is True and chk['pin'] and chk['only'] and chk['agency'] is not False and chk['page'] is not False
    if ok:
        res['reason'] = res['reason'].replace(PERSON_TXT.strip(), '').rstrip(' .')
        res.update(outcome=MATCH, likely=None, auto_confirmed=True, records=[f['id'] for f in sel],
                   tracts=[{'id': f['id'], 'name': f['name'], 'km': f['km']} for f in sel], maybe=[],
                   reason=f"auto-confirmed (second opinion): {res['reason']}; official acres {off:,.0f} agree with the outline's "
                          f"{ac:,.0f} (within {ACRE_TOL:.0%}), the pin is inside, no other place of this name nearby"
                          + ('' if chk['agency'] is None else ', the agency agrees') + ('' if chk['page'] is None else ", the official page's kind agrees"))
    else:
        miss = [k for k in ('acres', 'pin', 'only', 'agency', 'page') if chk[k] is False or (k == 'acres' and chk[k] is None)]
        res['reason'] = res['reason'].rstrip(' .') + '. Not auto-confirmed: ' + ', '.join({'acres': 'no official acres to compare' if chk['acres'] is None else 'official acres differ by more than 15%',
                                                               'pin': 'the pin is not inside', 'only': 'another place of this name is nearby',
                                                               'agency': 'the agency differs', 'page': "the official page names another kind"}[k] for k in miss)
    return res


# ======================================================================================================== the key's record ids first
def decide_with_key(park, key_join, candidates, layer_info=None, other_parks=None):
    r = _decide_with_key(park, key_join, candidates, layer_info, other_parks)
    r['private'] = bool(r.get('private') or (layer_info or {}).get('wdpa'))
    return r


def _decide_with_key(park, key_join, candidates, layer_info=None, other_parks=None):
    """Standard order for every caller (owner, 2026-11-13):
      1. the key already lists record ids for this park from THIS source (key_join['source'] == layer_info['source']):
         select those records by id and only sanity-check them (all present, name and kind not contradictory, pin not far).
         A contradiction = UNCLEAR with the reason, never a silent accept.
      2. no ids, or the file is from another source than the key read: decide() by name + kind + pin.
       key_join = {source, ids [...], names {id: name}? (the names the key saved), by_person (a person approved the join)}"""
    li = layer_info or {}
    kj = key_join or {}
    ids = [str(x) for x in kj.get('ids') or []]
    src_key, src_file = str(kj.get('source') or '').strip().lower(), str(li.get('source') or '').strip().lower()
    if not ids:
        r = decide(park, candidates, li, other_parks); r['path'] = 'name (the key has no record ids for this park)'; return r
    if not src_key or not src_file or src_key != src_file:
        r = decide(park, candidates, li, other_parks)
        r['path'] = f"name (the key's ids are from '{src_key or '?'}', this file is '{src_file or '?'}': ids not trusted across sources)"
        r['reason'] = "the key's record ids are from another source, so they are not used; " + r['reason']
        return r
    byid = {str(c.get('id')): c for c in candidates or []}
    have = [byid[i] for i in ids if i in byid]
    miss = [i for i in ids if i not in byid]
    fb = decide(park, candidates, li, other_parks)
    if not have:
        return _res(UNCLEAR, 'no', f"none of the key's record ids ({', '.join(ids[:5])}) is in this file: the file may be cut "
                    f"differently or out of date. (By name alone this file would say: {fb['outcome']}.)", path='key ids',
                    flags=['key_ids_missing'], name_fallback=fb)
    if miss:
        return _res(UNCLEAR, 'yes', f"only {len(have)} of the key's {len(ids)} records are in this file (missing: "
                    f"{', '.join(miss[:5])}); half a park is not the park", path='key ids', flags=['key_ids_partial'],
                    maybe=[str(c.get('id')) for c in have], name_fallback=fb)
    names = {str(k): v for k, v in (kj.get('names') or {}).items()}
    problems, kinds_bad = [], []
    for c in have:
        f = assess(park, c, li)
        saved = names.get(str(c.get('id')))
        name_fits = f['rel'] in ('exact', 'record_longer') or (saved and name_relation(saved, c.get('name')) == 'exact')
        if saved and name_relation(saved, c.get('name')) != 'exact' and not f['rel']:
            problems.append(f"record {c.get('id')} is now called '{c.get('name')}', the key saved '{saved}'")
        elif not name_fits and not kj.get('by_person'):
            problems.append(f"record {c.get('id')} '{c.get('name')}' does not carry the park's name")
        if f['kind'] == 'clash' and not kj.get('by_person'):
            kinds_bad.append(f"record {c.get('id')} '{c.get('name')}' is {_kind_words(f['kr'])}, the park is {_kind_words(f['kp'])}")
    fs = [assess(park, c, li) for c in have]
    pc, km = _place_pin(fs)
    if pc in ('far', 'very_far'):
        problems.append(_pin_words(pc, km, sum(f['acres'] for f in fs)))
    if problems or kinds_bad:
        return _res(UNCLEAR, 'yes' if not problems else 'no', "the key's records were found by id, but: " + '; '.join(problems + kinds_bad),
                    path='key ids', flags=['key_ids_contradict'] + (['kind_differs'] if kinds_bad else []),
                    maybe=[str(c.get('id')) for c in have], pin=pc, pin_km=km, name_fallback=fb)
    return _res(MATCH, None, f"the key's {len(have)} record id(s) are all in this file and agree"
                + (' (a person approved this join)' if kj.get('by_person') else '') + f'; {_pin_words(pc, km, sum(f["acres"] for f in fs))}',
                records=[str(c.get('id')) for c in have], tracts=[{'id': f['id'], 'name': f['name'], 'km': f['km']} for f in fs],
                path='key ids', pin=pc, pin_km=km)


# ======================================================================================================== old vs new
def review_state(old_ids, res):
    """What happens to a park when the new rules meet the key's current join (owner, 2026-11-13: a doubtful existing join must
    not drop off the map):
      UNCHANGED        joined before and MATCH now on the same records (or not joined and still NO)
      AUTO-CONFIRMED   MATCH now through the second opinion
      DIFFERENT-RECORD joined before, MATCH now on other records: keep the old outline, flag it
      KEEP-FLAGGED     joined before, UNCLEAR / NO now: keep the old outline, mark it for review
      NEW-MATCH        not joined before, MATCH now
      PERSON           not joined, UNCLEAR now
      NO               not joined, NO now"""
    old = {str(x) for x in old_ids or []}
    new = {str(x) for x in res.get('records') or []}
    if res.get('outcome') == MATCH:
        if res.get('auto_confirmed'):
            return 'AUTO-CONFIRMED'
        if not old:
            return 'NEW-MATCH'
        return 'UNCHANGED' if old == new else 'DIFFERENT-RECORD'
    if old:
        return 'KEEP-FLAGGED'
    return 'PERSON' if res.get('outcome') == UNCLEAR else 'NO'
