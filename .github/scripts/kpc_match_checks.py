#!/usr/bin/env python3
"""kpc_match_checks.py: the name alone never draws an outline (KPC owner, 20 Nov 2026; the outside agent's checks, as the
19 Nov sample scored them).

The key builders find candidate records by name. This module decides whether a name-found record may draw the park's outline.
It is a US rule file (kpc_key_freeze.RULE_FILES['us-key']): a change here moves the US rules hash.

The checks (none of them reads the POTA side from the record being checked):
  id        the id in POTA's link to the park's own agency page against the record's id of the SAME kind (NPS unit code,
            Minnesota DNR unit id on sgmna uniqueid, sgmnb sft and sgmnc pgrm_project); ids of different kinds are never compared;
            a record whose same-kind id differs goes to check
  link      the park's own agency page in the park's state, when the address names the park in full (strong); with pin 3c
            passing and size or place passing, the park is confirmed by link; a part name in the address is a note only
  agency    the agency of POTA's own link (KPC-Data's park facts file) against the agency that owns the record (PAD-US
            Mang_Name / Mang_Type; the club's layer table for the federal layers by prefix); applied only where both are known
  place     'pin 3c': POTA's pin is outside the record, another joined record of the park holds the pin, and no joined
            record with the record's own full name holds it (a park in many pieces is not flagged for its other pieces;
            a pin no record holds flags nothing)
  name      the record's full name (short forms such as WMA spelled out) is another park's own full name in the state
  national  a national-layer record joined by name whose manager level (FED / STAT) differs from the level in the park's
            name, unless it is a copy (size within 10 percent) of land the park already holds at its own level
  size      only a size whose park-facts `witness` tag is agency_document or hand_copy counts (same_record, other_layer,
            unknown and untagged rows never do: fail closed)
  kind      POTA's type against the record's kind: ADVISORY only (the sample: 1 wrong record caught, 71 right ones flagged)

The rule:
  - a record whose same-kind id agrees with POTA's link = confirmed by id (the id stands in for the name);
  - a name-joined park that passes agency (when known), place (3c), name, national and size (when there is a tagged size)
    is confirmed by size when a tagged size agrees, or confirmed by link when POTA's own agency page (in the park's state)
    names the park in full in the address and place (the pin is in or near the outline) also passes; a part name in the
    address is a note only, like kind;
  - another name-joined record keeps drawing the outline only when it passes those checks; kind is written down as a note, never a reason;
  - a failure sends the record to check with its reason; a park with no record left shows its pin;
  - code rows (NPS unit code, official line, link id) and a person's saved join ('reviewed...') are kept as they are;
  - two fits = not sure is the builder's one-record-two-parks pass (it runs before this one); a link id on two parks
    is never a tie.
"""
import json, math, os, re

# The kind table of kpc_us_key.py, copied so the offline counter reads the same codes; the tests check both stay equal.
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
US_COMPAT = [{'wild', 'wsa'}, {'ca', 'snp'}, {'rma', 'trh'}]
DES = {'SP': 'sp', 'SREC': 'sp', 'SHCA': 'hist', 'NWR': 'nwr', 'NF': 'nf', 'NG': 'nf', 'NP': 'nps', 'NM': 'nps', 'NRA': 'nps', 'NHS': 'hist', 'WA': 'wild', 'SW': 'wma', 'SCA': 'ca', 'WSR': 'wsr', 'NCA': 'rma', 'SRMA': 'rma', 'RMA': 'rma'}


def kinds(s):
    s = str(s or '').lower(); return {k for k, r in KINDS if re.search(r, s)}


SIZE_AGREE = (0.8, 1.25)   # within 25% either way: the outline and the agency's own figure tell the same story
SIZE_FAR = 3.0             # 3 times off either way = the wrong land (owner's FI-2 hold mark)
NEAR_KM = 0.5              # a pin within half a kilometre of the line is 'near' (the keys read a ~0.1 km working copy)
CODE_HOW = ('NPS', 'official', 'id')   # 'id': joined here by the park's own link id (plus place or size)
PERSON_HOW = ('reviewed',)
NAME_HOW_NOTE = 'name, words, alias, same name, answer sheet: all name-linked'

# id kinds a joined record can carry. 'rec': how the builder reads it from a record; 'url': the layer address part that
# says the layer carries this kind; 'rx': the value shape (anything else from that layer is not this kind).
ID_KINDS = {
    'NPS unit code': {'rec': 'nps', 'rx': r'[A-Z]{4}'},
    'MN DNR unit id': {'url': 'us_mn_state_dnr/', 'pre': ('sgmna', 'sgmnb', 'sgmnc'),
                      'sa': ('uniqueid', 'sft', 'pgrm_project'), 'rx': r'(WMA|AMA|SNA|SFT|SPK|SRA)\d{5,8}'},
}
# Checked 20-21 Nov: these two kinds are carried by a layer the key reads. Minnesota's same-id fields (crosswalk 20 Nov) are
# sgmna uniqueid, sgmnb sft and sgmnc pgrm_project; they confirm like a Park Service unit code. The other link kinds (NY DEC,
# CA State Parks, OR State Parks, MI DNR, MT FWP, AR, SC, TX, ME, Forest Service, Recreation.gov) are on no saved record today,
# so they give no id vote until the keeper saves the agency's id field (plan O5).

SHORT = {'np': 'national park', 'nwr': 'national wildlife refuge', 'sp': 'state park', 'wma': 'wildlife management area',
         'sf': 'state forest', 'nf': 'national forest', 'nm': 'national monument', 'nra': 'national recreation area',
         'sra': 'state recreation area', 'shs': 'state historic site', 'nhp': 'national historical park',
         'nhs': 'national historic site', 'snp': 'state nature preserve', 'sna': 'state natural area', 'np&pres': 'national park and preserve',
         'npres': 'national preserve', 'nmem': 'national memorial', 'nhl': 'national historic landmark', 'nsr': 'national scenic river',
         'nwsr': 'national wild and scenic river', 'st': 'saint', 'mt': 'mount', 'ft': 'fort', 'co': 'county', 'cnty': 'county'}


def full(name):
    """The exact-name test of the plan: lower case, accents aside, punctuation and 'the' out, short forms written out."""
    import unicodedata
    s = unicodedata.normalize('NFKD', str(name or '')).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'\(.*?\)', ' ', s).replace('&', ' and ')
    s = re.sub(r"[^a-z0-9 ]+", ' ', s)
    w = [SHORT.get(x, x) for x in s.split() if x != 'the']
    return ' '.join(' '.join(w).split())


def exact_name(park_name, list_name, park_kind=''):
    """True when the list's name IS the park's full name, as written or as its bare name plus the park's kind word
    ('X' + 'State Park' = 'X State Park'). 'X' never ties 'X Lake'."""
    a, b = full(park_name), full(list_name)
    if not a or not b: return False
    return a == b or (bool(park_kind) and full(f'{list_name} {park_kind}') == a)


def how_word(row):
    return str(row[3] if len(row) > 3 else '').split(' · ')[0].split(' ')[0].rstrip(':')


def row_class(row):
    w = how_word(row)
    if w in CODE_HOW: return 'code'
    if w in PERSON_HOW or w.startswith('reviewed'): return 'person'   # reviewed-approx, reviewed-sheet: a person's too (builder rule)
    return 'name'


def norm_id(v):
    s = str(v if v is not None else '').strip().upper()
    return s[:-2] if re.fullmatch(r'\d+\.0', s) else s


def load_nps_units(path='data/nps-units.json'):
    try:
        return {u['code'].upper(): {s.strip() for s in str(u.get('states') or '').split(',') if s.strip()}
                for u in json.load(open(path))['units']}
    except (OSError, ValueError, KeyError):
        return {}


def link_tie(fact, nps_units=None):
    """-> (id_kind, id_value, why). id_kind None = no tie. Only the park's own page on the agency's own site, a known id kind,
    the id on no other park, and (NPS) a code the Park Service's unit list has in the park's state."""
    lk = (fact or {}).get('link') or {}
    if not lk.get('id_value'): return None, None, 'no id in the link'
    if lk.get('page_kind') not in (None, 'own page'): return None, None, f"not the park's own page ({lk.get('page_kind')})"
    if not lk.get('usable'): return None, None, 'link id not usable (shared, unknown kind or another state)'
    if int(lk.get('id_shared_by') or 1) > 1 or int(lk.get('shared_by') or 1) > 1: return None, None, 'the id is on more than one park'
    kind, val = lk.get('id_kind'), norm_id(lk.get('id_value'))
    if kind == 'NPS unit code' and nps_units is not None:
        st = str((fact or {}).get('area') or '')[3:]
        if val not in nps_units: return None, None, "the Park Service's unit list has no such code"
        if nps_units[val] and st and st not in nps_units[val]: return None, None, "the code's unit is in another state"
    return kind, val, 'own agency page'


# The address-name test of kpc_link_ids, from POTA's saved park list (no fetch). 'strong' = the address names the park in full.
LINK_GENERIC = {'index', 'home', 'default', 'details', 'detail', 'info', 'information', 'visit', 'about', 'aboutus', 'about-us',
                'pages', 'page', 'park', 'parks', 'maps', 'map', 'planyourvisit', 'basicinfo', 'recreation', 'overview', 'en',
                'fr', 'eng', 'fra', 'detail_report', 'main', 'welcome', 'directions', 'history', 'learn', 'historyculture',
                'files', 'pdf', 'pdfs', 'documents', 'uploads', 'content', 'download', 'location', 'locations', 'property'}
LINK_EXT = re.compile(r'\.(html?|aspx?|php|cfm|shtml|dot|action|pl|jsp|pdf|png|jpe?g|ashx)$', re.I)
LINK_STOP = {'the', 'of', 'and', 'at', 'in', 'a', 'an', 'on', 'for', 'de', 'du', 'la', 'le', 'des', 'st', 'saint', 'mt', 'mount', 'no'}
LINK_KINDWORDS = {'state', 'park', 'parks', 'national', 'provincial', 'wildlife', 'management', 'area', 'areas', 'forest', 'refuge',
                  'historic', 'historical', 'site', 'recreation', 'recreational', 'conservation', 'natural', 'nature', 'preserve',
                  'reserve', 'game', 'land', 'lands', 'wma', 'sp', 'sf', 'nwr', 'sna', 'swa', 'sgl', 'sra', 'shs', 'nhs', 'wsa',
                  'hma', 'memorial', 'monument', 'trail', 'river', 'lake', 'fishing', 'access', 'public', 'unit', 'tract',
                  'wilderness', 'study', 'herd', 'heritage', 'scenic', 'wild', 'ecological', 'county', 'regional', 'municipal',
                  'city', 'beach', 'marine', 'seashore', 'lakeshore', 'battlefield', 'military', 'fish', 'hatchery', 'waterfowl',
                  'production', 'sanctuary', 'habitat', 'protected', 'easement', 'grassland', 'grasslands'}


def _link_words(text):
    import urllib.parse
    t = re.sub(r'([a-z])([A-Z])', r'\1 \2', urllib.parse.unquote(str(text or '')))
    return [w for w in re.split(r'[^a-z0-9]+', t.lower().replace("'", '').replace('\u2019', '')) if w]


def web_name(url_or_segs):
    """The agency's own words for the place, taken from the address: the last part that is not a filler or a number."""
    import urllib.parse
    if isinstance(url_or_segs, (list, tuple)):
        segs = list(url_or_segs)
    else:
        u = str(url_or_segs or '').strip()
        if not u: return ''
        if not re.match(r'[a-z][a-z0-9+.-]*://', u, re.I): u = 'http://' + u
        try: pu = urllib.parse.urlsplit(u)
        except ValueError:
            return ''
        segs = [s for s in pu.path.split('/') if s]
    for s in reversed(segs):
        base = LINK_EXT.sub('', urllib.parse.unquote(s))
        w = _link_words(base)
        if not w or all(x.isdigit() for x in w) or base.lower() in LINK_GENERIC or (len(w) == 1 and w[0] in LINK_GENERIC):
            continue
        return ' '.join(w)
    return ''


def name_match(park_name, wname):
    """strong / part / none / '' (no name in the address). Every significant word of the park's name is in the address (strong);
    at least half (part). Same scoring as kpc_link_ids, from the address text only."""
    if not wname: return ''
    pw = [w for w in _link_words(park_name) if w not in LINK_STOP]
    key = [w for w in pw if w not in LINK_KINDWORDS] or pw
    ww = set(_link_words(wname)); squashed = ''.join(_link_words(wname))
    hit = sum(1 for w in key if w in ww or (len(w) >= 4 and w in squashed))
    if key and hit == len(key): return 'strong'
    return 'part' if key and hit * 2 >= len(key) and hit else 'none'


def link_name_agree(fact):
    """'strong' | 'part' | ''. The park's own agency page, the website not in another state, and the address names the park.
    Reads the link facts already taken from POTA's saved park list (no fetch). 'part' is advisory only."""
    f = fact or {}
    lk = f.get('link') or {}
    page = lk.get('page_kind') or lk.get('page') or ''
    if page != 'own page': return ''
    if lk.get('site') not in ('agency (known)', 'government site'): return ''
    if str(lk.get('state_check') or '').startswith('OTHER'): return ''
    nm = lk.get('name_match') or ''
    if nm not in ('strong', 'part', 'none'):
        wname = lk.get('web_name') or web_name(lk.get('url') or lk.get('link') or '')
        if wname: nm = name_match(f.get('name') or '', wname)
    return nm if nm in ('strong', 'part') else ''


def shared_names(facts):
    """{area: {full name seen on two or more parks}}: an exact name shared inside a state ties neither park."""
    seen, out = {}, {}
    for f in (facts or {}).values():
        if not isinstance(f, dict): continue
        k = (f.get('area'), full(f.get('name')))
        if k[1]: seen[k] = seen.get(k, 0) + 1
    for (a, n), c in seen.items():
        if c > 1: out.setdefault(a, set()).add(n)
    return out




WITNESS_PROOF = ('agency_document', 'hand_copy')   # KPC-Data park facts `size.witness`: the only two tags that count


def tagged_witness(row):
    """True only for a size row whose `witness` tag (KPC-Data park facts) is agency_document or hand_copy and that does not say
    witness_counts false. same_record, other_layer, unknown and an untagged row never count: fail closed.
    Job C (KPC owner, 2026-11-21): a hand_copy counts only when it names its source (a web address in source_url); a hand
    copy with no page ('page not given') is a typed number nobody can check, so it never counts."""
    if not isinstance(row, dict): return False
    if row.get('witness') == 'hand_copy' and not hand_copy_sourced(row): return False
    return row.get('witness') in WITNESS_PROOF and row.get('witness_counts', True) is not False


def hand_copy_sourced(row):
    """True when a hand-copied size names the page it was copied from (source_url is a web address)."""
    return bool(re.match(r'^https?://\S+\.\S+', str((row or {}).get('source_url') or '').strip(), re.I))


def size_witnesses(fact, shared=None):
    """-> [(acres, witness tag, why)]: official sizes that may witness this park's join. Empty = none.
    Only rows carrying an explicit independent-witness tag (tagged_witness); a full name two parks of the state share = none."""
    f = fact or {}
    pname, area = f.get('name') or '', f.get('area')
    if pname and full(pname) in ((shared or {}).get(area) or set()): return []
    out = []
    rows = [f.get('size')] + [page_size_witness(f, s) for s in ((f.get('page') or {}).get('sizes') or [])]
    for s in rows:
        if not tagged_witness(s): continue
        try: ac = float(s.get('acres'))
        except (TypeError, ValueError): continue
        if ac > 0: out.append((ac, s.get('witness'), 'tagged independent witness'))
    return out


# ---------------------------------------------------------------------------------------------------------------------------
# 22 Nov 2026 (owner 3:55 PM "go for all"; notes/mapping.md plan P1-P7 and rule sheet PN): the park's OWN agency page helps the
# match. Nothing from a page that is not the park's own (P6): own_page() is the one gate every page fact passes.
SECOND_NAME_PLACE = re.compile(r'\b(park|forest|refuge|wildlife|area|preserve|reserve|lake|river|trail|monument|site|recreation|'
                               r'sanctuary|wma|conservation|marsh|island|beach|reservoir|creek|natural|historic|seashore|lakeshore|'
                               r'battlefield|grassland|wilderness|hma|viewpoint|wayside|game lands?|fishing|access|unit|tract)\b', re.I)
SECOND_NAME_SPLIT = re.compile(r'\s*(?:\||•|·|–|—|\s-\s|:)\s*')
SITE_HEADING_PARKS = 3     # the same text on this many parks' pages of one host = a site heading, never a park's name
TRACT_KM = 5.0             # P4: a tract's record lies within 5 km of the park's pin
LAYER_KIND_CODES = {'wildlife area': {'wma'}, 'park': {'sp'}, 'preserve': {'snp'}, 'forest': {'nf', 'sf'}, 'recreation area': {'sp', 'rma'},
                    'refuge': {'nwr'}, 'herd area': {'hma'}, 'wilderness': {'wild'}, 'river corridor': {'wsr'}, 'trail': {'trh'}}


def own_page(fact):
    """P6: True only for the park's OWN page on an agency or government site (the reader's own-page test, not an unofficial host).
    A page POTA links that is another park's page, a list or the agency's front page gives this park nothing."""
    f = fact or {}
    pg, lk = f.get('page') or {}, f.get('link') or {}
    if pg.get('own_page') != 'own' or pg.get('unofficial'): return False
    return str(lk.get('site') or '') in ('agency (known)', 'government site') or not lk


def page_size_witness(fact, s):
    """P1: a size the park's own agency page states as the park's clean total counts as an agency document (an untagged page
    size, or one from any other page, never counts)."""
    if not isinstance(s, dict) or s.get('witness'): return s
    if own_page(fact) and s.get('total') and s.get('clean'):
        return dict(s, witness='agency_document', witness_why="the park's own agency page states its total size")
    return s


def second_names(fact, park_name, heading_count=None, names_in_state=None):
    """P2 (rule sheet PN): the place names the park's own page gives it that differ from POTA's, cleaned: the page heading cut at
    | • – — ' - ' ':' and each part that reads as a place name. Never a site heading (the same text on SITE_HEADING_PARKS or
    more parks' pages of that host), never another POTA park's name in the state, never POTA's own name."""
    if not own_page(fact): return []
    pg = (fact or {}).get('page') or {}
    raw = str(pg.get('name_on_page') or '').strip()
    if not raw or '\ufffd' in raw: return []
    if heading_count and heading_count.get((pg.get('host'), full(raw)), 0) >= SITE_HEADING_PARKS: return []
    mine, out = full(park_name), []
    for part in [raw] + SECOND_NAME_SPLIT.split(raw):
        part = part.strip()
        n = full(part)
        if not n or n == mine or len(n.split()) < 2 or not SECOND_NAME_PLACE.search(part): continue
        if heading_count and heading_count.get((pg.get('host'), n), 0) >= SITE_HEADING_PARKS: continue
        if names_in_state and n in names_in_state: continue
        if n not in out: out.append(n)
    return out


def parent_units(fact):
    """P5: the bigger units the park's own page says it lies inside (the reader's sure 'inside_of', never 'maybe inside')."""
    if not own_page(fact): return []
    return [u for u in ((fact or {}).get('page') or {}).get('inside_of') or [] if isinstance(u, dict) and full(u.get('unit'))]


def tract_names(fact):
    """P4: the tract names the park's own page lists."""
    if not own_page(fact): return []
    return [full(t) for t in ((fact or {}).get('page') or {}).get('parts') or [] if full(t) and len(full(t)) > 3]


def rec_name(a):
    return (a or {}).get('Unit_Nm') or (a or {}).get('Loc_Nm') or ''


def layer_kinds(rec, table=None):
    """A record's kinds: its own (record_kinds) plus its layer's kind from the layer table (P7)."""
    k = set(record_kinds(rec))
    t = (table or {}).get(layer_of(rec)) or {}
    return k | LAYER_KIND_CODES.get(str(t.get('kind') or '').lower(), set())


def near_box(lat, lon, bb, km_):
    """True when (lat, lon) lies within km_ of the box [w, s, e, n]."""
    if not bb or lat is None or lon is None: return False
    w, s_, e, n = bb
    dla = km_ / 111.2; dlo = km_ / max(1e-6, 111.2 * math.cos(math.radians(lat)))
    return (s_ - dla) <= lat <= (n + dla) and (w - dlo) <= lon <= (e + dlo)


NEAR_MISS_KM = (('within 100 ft', 0.03048), ('within 0.5 km', 0.5))   # report only (owner 22 Nov 4:41 PM): the pin rule is not changed


def km_to_record(lat, lon, rec):
    """Kilometres from (lat, lon) to the nearest edge of a record's rings (segment distance), None when it has no shape."""
    g = (rec or {}).get('_g') or {}
    rs = g.get('rings') or (g.get('coordinates') if g.get('type') == 'Polygon' else
                           [r for poly in g.get('coordinates') or [] for r in poly] if g.get('type') == 'MultiPolygon' else [])
    if lat is None or lon is None or not rs: return None
    k, best = math.cos(math.radians(lat)) * 111.32, None
    for r in rs:
        for (x1, y1), (x2, y2) in zip(r, r[1:]):
            ax, ay, bx, by = (x1 - lon) * k, (y1 - lat) * 110.57, (x2 - lon) * k, (y2 - lat) * 110.57
            dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
            t_ = 0 if L == 0 else max(0, min(1, -(ax * dx + ay * dy) / L))
            d = math.hypot(ax + t_ * dx, ay + t_ * dy)
            best = d if best is None or d < best else best
    return best


def claim_fit(park, rec, table=None):
    """P7: how well a park fits a record two parks claim: name (2 exact, 1 with 'state' left out, 0 other) plus kind
    (+1 agrees, -1 differs, 0 no data)."""
    rn, pn = full(rec_name(rec)), full(park.get('n') or '')
    loose = lambda t: ' '.join(w for w in t.split() if w != 'state')
    sc = 2 if rn and rn == pn else (1 if rn and loose(rn) == loose(pn) else 0)
    a, b = kinds(park.get('t') or park.get('n') or ''), layer_kinds(rec, table)
    if a and b: sc += 1 if (a & b or any(a & c and b & c for c in US_COMPAT)) else -1
    return sc


def page_pins(fact):
    pg = (fact or {}).get('page') or {}
    if pg.get('own_page') != 'own' or pg.get('unofficial'): return []
    out = []
    for c in pg.get('coords') or []:
        try:
            la, lo = (c.get('lat'), c.get('lon')) if isinstance(c, dict) else (c[0], c[1])
            la, lo = float(la), float(lo)
            if -90 <= la <= 90 and -180 <= lo <= 180 and (la, lo) != (0.0, 0.0): out.append((la, lo))
        except (TypeError, ValueError, IndexError, KeyError):
            pass
    return out


def size_vote(witnesses, outline_acres):
    """-> ('agrees' | 'far off' | 'no vote', ratio)."""
    if not witnesses or not outline_acres or outline_acres <= 0: return 'no vote', None
    best = None
    for ac, _k, _w in witnesses:
        r = outline_acres / ac
        if SIZE_AGREE[0] <= r <= SIZE_AGREE[1]: return 'agrees', round(r, 3)
        best = r if best is None or abs(math.log(r)) < abs(math.log(best)) else best
    if best is not None and (best > SIZE_FAR or best < 1 / SIZE_FAR): return 'far off', round(best, 3)
    return 'no vote', round(best, 3) if best else None


def record_id_of(kind, rec_ids):
    """The value of `kind` a record carries, from {kind: value} (None = the record carries no id of that kind)."""
    return norm_id(rec_ids.get(kind)) if rec_ids and rec_ids.get(kind) else None


def nps_code_of(rec):
    """A record's Park Service unit code: the NPS layer's UNIT_CODE, or a PAD-US Park Service record's 4-letter Loc_Nm
    (the same reading as kpc_key_rules.nps_record_code). Never from the record's name."""
    rec = rec or {}
    sa = rec.get('SA') or {}
    v = sa.get('UNIT_CODE') or sa.get('unit_code') or rec.get('UNIT_CODE')
    if v and re.fullmatch(r'[A-Za-z]{4}', str(v).strip()): return str(v).strip().upper()
    if str(rec.get('Mang_Name') or '') == 'NPS' and re.fullmatch(r'[A-Z]{4}', str(rec.get('Loc_Nm') or '').strip()):
        return str(rec['Loc_Nm']).strip()
    return None


LINK_TIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'link-id-ties.json')
_LINK_TIES = {}


def load_link_ties(path=None):
    """[{kind, layer, field, rx}] of .github/link-id-ties.json: web ids a record carries inside its own web address field
    (KPC owner, 2026-11-21, job A). A missing or unreadable file = no address ties. Never a WDPA layer or field."""
    path = path or LINK_TIES_FILE
    if path not in _LINK_TIES:
        try:
            with open(path, encoding='utf-8') as f:
                rows = json.load(f).get('ties') or []
        except (OSError, ValueError):
            rows = []
        _LINK_TIES[path] = [dict(t, rx_c=re.compile(t['rx'], re.I)) for t in rows
                            if t.get('kind') and t.get('layer') and t.get('field') and t.get('rx')
                            and not re.search(r'wdpa|protectedplanet', t['layer'] + t['field'], re.I)]
    return _LINK_TIES[path]


def layer_of(rec):
    """A record's layer: the letters of its record id (sgnya, sgmtb...), or 'PAD-US' for a PAD-US record (numeric id)."""
    rec = rec or {}
    pre = re.match(r'[a-z]*', str(rec.get('OBJECTID') or '')).group(0)
    if pre: return pre
    return 'PAD-US' if any(k in rec for k in ('Unit_Nm', 'Mang_Name', 'Des_Tp')) else ''


def field_value(rec, field):
    """A field of a record, from its saved extra fields (SA) or its own attributes, any letter case."""
    rec = rec or {}
    for src in (rec.get('SA') or {}, rec):
        for k, v in src.items():
            if str(k).lower() == str(field).lower() and v not in (None, ''): return v
    return None


def addr_key(kind):
    """The ids_from key of an id read from a record's web address (agree-only: it can confirm, never drop)."""
    return 'addr:' + kind


def ids_from(rec, url='', ties=None):
    """{id kind: value} a record carries: its Park Service unit code, and its layer's own id when that layer carries a kind.
    url = the address of the layer the record came from; a known layer prefix on the record id also counts (sgmnb, sgmnc).
    Job A (21 Nov): an id inside the record's own web address field (link-id-ties.json) is added as addr_key(kind): it agrees
    or says nothing (an address can point to a neighbouring page), so a different address id never drops a record."""
    out = {}
    c = nps_code_of(rec)
    if c: out['NPS unit code'] = c
    sa = (rec or {}).get('SA') or {}
    pre = re.match(r'[a-z]*', str((rec or {}).get('OBJECTID') or '')).group(0)
    for k, spec in ID_KINDS.items():
        on_url = bool(spec.get('url') and spec['url'] in str(url or ''))
        on_pre = bool(pre and pre in (spec.get('pre') or ()))
        if not on_url and not on_pre: continue
        for fld in spec.get('sa') or ():
            v = next((sa[x] for x in sa if str(x).lower() == fld.lower()), None)
            if v not in (None, '') and re.fullmatch(spec['rx'], norm_id(v)): out[k] = norm_id(v); break
    lay = layer_of(rec)
    for t in (load_link_ties() if ties is None else ties):
        if t['layer'] != lay or addr_key(t['kind']) in out: continue
        m = t['rx_c'].search(str(field_value(rec, t['field']) or ''))
        if m and m.group(1): out[addr_key(t['kind'])] = norm_id(m.group(1))
    return out


def map_tie_of(fact):
    """The agency list's tie for the park's own link id (KPC-Data park facts link.map_tie, from the keeper's agency-crosswalk
    files): {map_layer, map_field, map_id, agency, source_url} or None. Never WDPA."""
    t = ((fact or {}).get('link') or {}).get('map_tie') or None
    if not isinstance(t, dict) or not (t.get('map_layer') and t.get('map_field') and t.get('map_id')): return None
    if re.search(r'wdpa|protectedplanet', str(t['map_layer']) + str(t['map_field']), re.I): return None
    return t


def map_tie_holds(tie, rec):
    """True when the record is on the agency list's layer and carries the list's map id in its field."""
    return bool(tie and rec is not None and layer_of(rec) == tie['map_layer']
                and norm_id(field_value(rec, tie['map_field'])) == norm_id(tie['map_id']))


def id_agrees(kind, val, rec_ids, rec=None, tie=None):
    """The record carries the park's own link id: as its own id, inside its web address, or through the agency's list."""
    if not kind: return False
    if record_id_of(kind, rec_ids) == val: return True
    if rec_ids and rec_ids.get(addr_key(kind)) and norm_id(rec_ids[addr_key(kind)]) == val: return True
    return map_tie_holds(tie, rec)


STATES = {'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT',
          'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA',
          'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD', 'massachusetts': 'MA', 'michigan': 'MI',
          'minnesota': 'MN', 'mississippi': 'MS', 'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH',
          'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
          'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC', 'south dakota': 'SD', 'tennessee': 'TN',
          'texas': 'TX', 'utah': 'UT', 'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV', 'wisconsin': 'WI',
          'wyoming': 'WY', 'district of columbia': 'DC'}
FED_LINK = {'US National Park Service': 'NPS', 'US Fish and Wildlife Service': 'FWS', 'US Forest Service': 'USFS',
            'US Bureau of Land Management': 'BLM', 'US Army Corps of Engineers': 'USACE', 'US Bureau of Reclamation': 'BOR',
            'National Wild and Scenic Rivers': 'FED', 'Recreation.gov': 'FED'}
FEDERAL = {'NPS', 'FWS', 'USFS', 'BLM', 'USACE', 'BOR', 'FED'}
PAD_MANG = {'NPS': 'NPS', 'FWS': 'FWS', 'USFS': 'USFS', 'BLM': 'BLM', 'USACE': 'USACE', 'USBR': 'BOR', 'BOR': 'BOR'}


def link_agency(fact, st=''):
    """The agency of POTA's own link: 'NPS', 'FWS', 'USFS', 'BLM', 'USACE', 'BOR', 'FED' (a federal site of any agency),
    'STATE' (an agency of the park's own state) or None (no agency site, no link, or an agency the table does not know)."""
    lk = (fact or {}).get('link') or {}
    if lk.get('site') not in ('agency (known)', 'government site'): return None
    ag = str(lk.get('agency') or '').strip()
    if ag in FED_LINK: return FED_LINK[ag]
    m = re.match(r'([A-Z]{2}) ', ag)
    code = m.group(1) if m else STATES.get(next((k for k in sorted(STATES, key=len, reverse=True) if ag.lower().startswith(k)), ''), '')
    if code and (not st or code == st): return 'STATE'
    return None


LAYER_TABLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'layer-agency-kind.json')
FED_AGENCIES = ('NPS', 'FWS', 'USFS', 'BLM', 'USACE', 'BOR')


def load_layer_table(path=None):
    """{layer prefix: {'agency', 'kind', 'why'}} from KPC-Links .github/layer-agency-kind.json (kpc_layer_agency_kind.py).
    Missing or unreadable RAISES: the caller holds the state (the agency check is never run without the club's table)."""
    with open(path or LAYER_TABLE, encoding='utf-8') as fh:
        d = json.load(fh)
    t = d.get('layers')
    if not isinstance(t, dict) or not t: raise ValueError('layer-agency-kind.json has no layers')
    return t


def layer_family(agency):
    """The table's agency words -> 'NPS' / 'FWS' / 'USFS' / 'BLM' / 'USACE' / 'BOR' / 'STATE' / 'DIST' / None (several or
    many owners, unknown: no data)."""
    a = str(agency or '').strip()
    if a in FED_AGENCIES: return a
    if a.startswith('state'):
        if 'many owners' in a: return None
        return 'DIST' if 'water district' in a else 'STATE'
    return None


# A record's OWN manager field (never its name): a field the keeper saves later (plan O5) as 'manager', or a saved source field
# ('SA') with one of these names. Owner fields are not manager fields.
OWN_MANAGER_FIELD = re.compile(r'^(manager|manager_name|managed_by|manage_by|managing_agency|managingagency|mang_name|mgr_name|mgr)$', re.I)
MANAGER_WORDS = [('FWS', r'\bFWS\b|\bUSFWS\b|fish (and|&) wildlife service'), ('NPS', r'\bNPS\b|national park service'),
                 ('USFS', r'\bUSFS\b|(us|u\.s\.|united states|usda) forest service'), ('BLM', r'\bBLM\b|bureau of land management'),
                 ('USACE', r'\bUSACE\b|corps of engineers'), ('BOR', r'\bUSBR\b|bureau of reclamation')]


def layer_is_compilation(pre, table=None):
    """True when the layer table marks the layer a compilation (D11 'what' = compilation: many owners' lands gathered by one
    office; the same layers the D7 'compilation copy' rule reads)."""
    return bool(pre) and ((table or {}).get(pre) or {}).get('what') == 'compilation'


def own_manager(rec):
    """The record's own manager field value, '' when it carries none."""
    rec = rec or {}
    if str(rec.get('manager') or '').strip(): return str(rec['manager']).strip()
    for k, v in (rec.get('SA') or {}).items():
        if OWN_MANAGER_FIELD.match(str(k)) and str(v or '').strip(): return str(v).strip()
    return ''


def manager_family(v):
    """A manager field's words -> 'NPS' / 'FWS' / 'USFS' / 'BLM' / 'USACE' / 'BOR' / 'STATE' / None, read like PAD-US's
    Mang_Name (its codes) and Mang_Type ('STAT')."""
    t = str(v or '').strip()
    if t.upper() in PAD_MANG: return PAD_MANG[t.upper()]
    if t.upper() == 'STAT': return 'STATE'
    for fam, rx in MANAGER_WORDS:
        if re.search(rx, t, re.I): return fam
    if re.search(r'\bstate\b|department|\bdept\b|division|commission|\bdnr\b|\bdcr\b|\bdec\b|\bwdfw\b|\btpwd\b', t, re.I): return 'STATE'
    return None


def record_agency(rec, table=None):
    """Who owns a record, never from its name: PAD-US records by their own Mang_Name / Mang_Type; every other layer by the
    club's layer table (load_layer_table). None = not known (also: no table, or a layer the table does not hold).
    22 Nov 2026 (owner's go): a COMPILATION layer (one office's list of many agencies' land) gives no agency vote: None,
    unless the record carries its own manager field, which is then read like a PAD-US record's."""
    rec = rec or {}
    oid = str(rec.get('OBJECTID'))
    pre = re.match(r'[a-z]*', oid).group(0)
    if pre:
        if layer_is_compilation(pre, table):
            return manager_family(own_manager(rec))
        return layer_family(((table or {}).get(pre) or {}).get('agency'))
    mn, mt = str(rec.get('Mang_Name') or '').upper(), str(rec.get('Mang_Type') or '').upper()
    if mn in PAD_MANG: return PAD_MANG[mn]
    if mt == 'FED': return 'FED:' + (mn or '?')
    if mt == 'STAT': return 'STATE'
    if mt in ('LOC', 'DIST', 'PVT', 'NGO', 'TRIB', 'JNT'): return mt
    return None


def agency_check(fact, rec, st='', table=None):
    """'agrees' | 'differs' | 'no data'."""
    a, b = link_agency(fact, st), record_agency(rec, table)
    if a is None or b is None: return 'no data'
    if a == 'FED': return 'agrees' if (b in FEDERAL or b.startswith('FED:')) else 'differs'
    if a == 'STATE': return 'agrees' if b == 'STATE' else 'differs'
    return 'agrees' if b == a else 'differs'


CLASH_KINDS = {'sp', 'wma', 'nwr', 'sf', 'nf'}   # park, wildlife area, refuge, state / national forest (the F3 land kinds)


def compilation_kind_clash(park_name, rec_name, rec, table=None):
    """22 Nov 2026 (owner): with no agency vote from a compilation layer, a record that names another kind of place than the
    park (a park against a wildlife area, refuge or state forest; a refuge against a wildlife area) still never stays joined.
    Kinds from KINDS on full() names (SP, WMA, NWR written out), only park / wildlife area / refuge / forest; a name with none of
    them says nothing. Only on a compilation layer whose record has no manager field of its own."""
    pre = re.match(r'[a-z]*', str((rec or {}).get('OBJECTID'))).group(0)
    if not layer_is_compilation(pre, table) or record_agency(rec, table) is not None: return False
    a, b = kinds(full(park_name)) & CLASH_KINDS, kinds(full(rec_name)) & CLASH_KINDS
    return bool(a) and bool(b) and not (a & b)


def record_kinds(rec):
    rec = rec or {}
    k = set(rec.get('_k') or [])
    d = DES.get(str(rec.get('Des_Tp') or '').upper())
    if d: k.add(d)
    return k


def kind_check(pota_type, rec):
    """POTA's type against the record's kind: 'agrees' | 'differs' | 'no data'."""
    a, b = kinds(pota_type), record_kinds(rec)
    if not a or not b: return 'no data'
    ok = bool(a & b) or any(a & c and b & c and (a | b) & c == c for c in US_COMPAT)
    return 'agrees' if ok else 'differs'


def other_park_name(rec_name, own_name, names_in_state):
    """Check 4: True when the record's full name is ANOTHER park's own full name in the state (and not this park's own,
    also with 'state' left out)."""
    r, mine = full(rec_name), full(own_name)
    if not r or r == mine: return False
    loose = lambda t: ' '.join(w for w in t.split() if w != 'state')
    if loose(r) == loose(mine): return False
    if r in names_in_state: return True
    # 22 Nov 2026 (owner 3:47 PM; Arkansas: a battlefield park joined to "X Natural Area", the record of "X State Natural Area"):
    # the word "state" is left out on BOTH sides, as it already is for the park's own name
    key = id(names_in_state)
    hit = _LOOSE_NAMES.get(key)
    if hit is None or hit[0] is not names_in_state or hit[1] != len(names_in_state):
        hit = (names_in_state, len(names_in_state), {loose(n) for n in names_in_state})
        _LOOSE_NAMES[key] = hit
    return loose(r) in hit[2]


_LOOSE_NAMES = {}


def reason_of(w):
    """'agency', 'kind', 'place', 'name', 'id', 'size', or 'no data: agency' / 'no data: kind' / 'no data: record' / 'no data: place'."""
    head, _, rest = w.partition(':')
    if head != 'no data': return head
    rest = rest.strip()
    return 'no data: ' + ('record' if rest.startswith('the record') else rest.split(' ')[0])


def outline_size(p, m):
    twins = {str(t) for t in p.get('twin') or []}
    return p.get('ac') or sum(float(q[2] or 0) for q in m if str(q[0]) not in twins)


NATIONAL_PREFIXES = ('wld', 'hma', 'hab', 'rma', 'rst', 'wsrc', 'fwsr', 'fsod', 'nca', 'wsa', 'wbl', 'fws', 'trl', 'nps')


def is_national(rid):
    """PAD-US (a number) or one of the national layers the US key reads."""
    t = str(rid)
    return t.isdigit() or re.match(r'[a-z]*', t).group(0) in NATIONAL_PREFIXES


def park_level(name):
    n = str(name or '').lower()
    if re.search(r'\bstate\b', n): return 'STAT'
    if re.search(r'\bnational\b|\bnwr\b|\bblm\b', n): return 'FED'
    return None


def national_flag(q, rows, recs, park_name):
    """The national-layer rule for one name-joined row q of a park's rows."""
    i = str(q[0])
    if not is_national(i) or row_class(q) != 'name': return False
    plev = park_level(park_name)
    lev = str((recs.get(i) or {}).get('Mang_Type') or '').upper()
    if not plev or lev not in ('FED', 'STAT') or lev == plev: return False
    try: a = float(q[2] or 0)
    except (TypeError, ValueError): return True
    if a < 5.0: return True
    same = [float(x[2] or 0) for x in rows if str(x[0]) != i and str((recs.get(str(x[0])) or {}).get('Mang_Type') or '').upper() == plev]
    return not any(abs(b - a) <= 0.10 * a for b in same)     # a copy of land the park already holds at its own level is not flagged


# 22 Nov 2026 (owner's go, PC test): the type words 3c leaves out are the kinds of KINDS (the builder's own kind table) for the
# kinds of land a park's pieces are named by, after full() has written the short forms out (SHORT). No second word list.
BARE_KINDS = ('sp', 'nps', 'hist', 'wma', 'nwr', 'ca', 'snp', 'nf', 'sf')
_BARE_RX = re.compile('|'.join(f'(?:{r})' for k, r in KINDS if k in BARE_KINDS))
# what may be all that is left between the record and the park: a piece of the same park
PIECE_WORD = re.compile(r'^(additions?|units?|tracts?|parcels?|annex|extension|north|south|east|west|\d+|(?=[ivx])x{0,2}(ix|iv|v?i{0,3}))$')


def bare_name(name):
    """full(name) with the kind words of KINDS left out and then a loose 'state' / 'national' / 'park' at the ends (the
    'state' check 4 leaves out): 'Lake Test State Park' -> 'lake test', 'Ft. Test' -> 'fort test'."""
    t = _BARE_RX.sub(' ', full(name))
    w = t.split()
    while w and w[-1] in ('state', 'national', 'park', 'parks'): w.pop()
    while w and w[0] in ('state', 'national'): w.pop(0)
    return ' '.join(w)


def same_bare(a, b):
    """True when two names are one park's: the same bare name, or the same once piece words are left out (Addition, Unit,
    Tract, Parcel, Annex, Extension, North / South / East / West, a number). 'One name holds the other' is NOT the same,
    and neither are two names of two different kinds (KINDS)."""
    x, y = bare_name(a), bare_name(b)
    if not x or not y: return False
    ka, kb = kinds(full(a)), kinds(full(b))
    if ka and kb and not (ka & kb or any(ka & c and kb & c and (ka | kb) & c == c for c in US_COMPAT)):
        return False                                            # two kinds of place ('X WMA' / 'X State Park'): never one park's
    if x == y: return True
    px = [t for t in x.split() if not PIECE_WORD.match(t)]
    py = [t for t in y.split() if not PIECE_WORD.match(t)]
    return bool(px) and px == py


def pin_3c(q, rows, holds, park_name=''):
    """holds(record id) -> True / False / None (POTA's pin strictly inside the record). True = flag q.
    22 Nov 2026: a record that does not hold the pin stays when its bare name is the bare name of a record that holds it, or
    of the park's own POTA name, or differs from one only by piece words (same_bare)."""
    if holds(str(q[0])) is not False: return False
    held = [x for x in rows if holds(str(x[0])) is True]
    if not held: return False                                   # no record holds the pin: says nothing about this one
    me = full(q[1])
    if any(full(x[1]) == me for x in held): return False
    return not any(same_bare(q[1], n) for n in [x[1] for x in held] + ([park_name] if park_name else []))


def reason_of(w):
    return w.partition(':')[0]


def outline_size(p, m):
    twins = {str(t) for t in p.get('twin') or []}
    return p.get('ac') or sum(float(q[2] or 0) for q in m if str(q[0]) not in twins)


def pass_state(parks, recs, facts, place_fn, url_of=lambda a: '', is_no=lambda ref, rid, a: False, skip=(), st='',
               units=None, hits=None, holds_fn=None, layer_table=None):
    """The whole pass for one state, shared by the US builder and the offline counter (one implementation).
    parks = the key's park rows (changed in place); recs = {record id: record}; place_fn(ref, [record ids]) -> True / False /
    None (pin inside or near; used to join a record by the park's link id); holds_fn(ref, record id) -> True / False / None
    (POTA's pin strictly inside that record; pin 3c); layer_table = load_layer_table() (each layer's owner); is_no(ref, rid, rec) = a person's saved NO; skip = parks never touched
    here (official trail lines). Every joined park gets park['match'] = {'status': 'confirmed' | 'outlined' | 'pin',
    'why': [reasons], 'notes': [advisory], 'by': 'id' | 'size' | 'link'} (pin = no outline; 'by' only when confirmed).
    Returns counts and appends [park, what, record id] to hits."""
    hits = [] if hits is None else hits
    holds_fn = holds_fn or (lambda ref, i: None)
    shared = shared_names(facts)
    rids = {i: ids_from(a, url_of(a)) for i, a in recs.items()}
    index = {}
    for i, d in rids.items():
        for k, v in d.items(): index.setdefault((k, v), []).append(i)
    names = {}
    for ref, p in parks.items(): names.setdefault(full(p.get('n') or ''), set()).add(ref)
    out = {'parks': 0, 'confirmed': 0, 'outlined': 0, 'pin': 0, 'gained': 0, 'moved': 0, 'why': {}, 'notes': {},
           'by_id': 0, 'by_link': 0, 'by_size': 0, 'second_name': 0, 'tract': 0, 'parent': 0, 'shared_record': 0,
           'second_name_near': {w: 0 for w, _k in NEAR_MISS_KM}}

    def to_check(p, rows, why):
        ids_ = {id(q) for q in rows}
        p['m'] = [q for q in p.get('m') or [] if id(q) not in ids_]
        p['c'] = [list(q[:3]) + [f'check ({why})'] for q in rows] + list(p.get('c') or [])

    # 22 Nov 2026 (plan P2/P4/P7): what the park pages of this state say, read once
    all_names = set(names)
    heading_count = {}
    for ref in parks:
        pg = ((facts.get(ref) or {}).get('page') or {})
        h = pg.get('host')
        for t in {full(pg.get('name_on_page'))} | {full(x) for x in SECOND_NAME_SPLIT.split(str(pg.get('name_on_page') or ''))}:
            if h and t: heading_count[(h, t)] = heading_count.get((h, t), 0) + 1
    by_name = {}
    for i, a in recs.items():
        n = full(rec_name(a))
        if n: by_name.setdefault(n, []).append(i)

    def add_row(p, i, how):
        a = recs[i]
        p['m'] = sorted(list(p.get('m') or []) + [[a['OBJECTID'], rec_name(a), round(float(a.get('GIS_Acres') or 0)), how]],
                        key=lambda x: -(x[2] or 0))
        p['c'] = [x for x in p.get('c') or [] if str(x[0]) != i]
        if p.get('g') in (None, 'pin'): p['g'] = 'official'

    # P7: one record that two parks of the state claim by NAME stays with the park whose name and kind fit it best; the others go
    # to check. Equal fits keep it for both (real 'same land, two park numbers').
    claims = {}
    for ref in sorted(parks):
        if ref in skip: continue
        for q in parks[ref].get('m') or []:
            if row_class(q) == 'name': claims.setdefault(str(q[0]), []).append(ref)
    for i, refs_ in sorted(claims.items()):
        if len(refs_) < 2 or i not in recs: continue
        fit = {r: claim_fit(parks[r], recs[i], layer_table) for r in refs_}
        best = max(fit.values())
        winners = [r for r in refs_ if fit[r] == best]
        if len(winners) == len(refs_): continue
        for r in refs_:
            if fit[r] == best: continue
            rows = [q for q in parks[r].get('m') or [] if str(q[0]) == i and row_class(q) == 'name']
            if not rows: continue
            to_check(parks[r], rows, f"another park's record: {rec_name(recs[i])[:60]} fits {', '.join(winners)} better")
            out['moved'] += len(rows); out['shared_record'] += 1; hits.append([r, 'shared record', i])

    for ref in sorted(parks):
        p = parks[ref]
        if ref in skip: continue
        f = facts.get(ref)
        kind, val, _w = link_tie(f, units)
        tie = map_tie_of(f) if kind else None
        typ = p.get('t') or (f or {}).get('type') or ''
        nm = p.get('n') or ''
        others = {n for n, rs in names.items() if len(rs - {ref}) == 1}    # one other park has that name (two: not sure)
        why, notes = [], []
        # the id used as a matcher: the record(s) carrying the park's own link id, missed by the name rules
        if kind:
            have = {str(q[0]) for q in p.get('m') or []}
            pool = list(index.get((kind, val), [])) + [i for i in index.get((addr_key(kind), val), []) if i not in index.get((kind, val), [])]
            if tie: pool += [i for i, a in recs.items() if i not in pool and map_tie_holds(tie, a)]
            cand = [i for i in pool if i not in have and not is_no(ref, i, recs[i])
                    and agency_check(f, recs[i], st, layer_table) != 'differs']
            if cand and place_fn(ref, cand):
                for i in cand:
                    a = recs[i]
                    p['m'] = sorted(list(p.get('m') or []) + [[a['OBJECTID'], a.get('Unit_Nm') or a.get('Loc_Nm') or '',
                                     round(float(a.get('GIS_Acres') or 0)), f"id: {kind} {val} (POTA's own link) + place"]], key=lambda x: -(x[2] or 0))
                    p['c'] = [x for x in p.get('c') or [] if str(x[0]) != i]
                    out['gained'] += 1; hits.append([ref, 'joined (id)', i])
                if p.get('g') in (None, 'pin'): p['g'] = 'official'
        # P2 (rule sheet PN): a second name from the park's own agency page joins a record of exactly that name that holds the pin
        have = {str(q[0]) for q in p.get('m') or []} | {str(q[0]) for q in p.get('c') or []}
        for n2 in second_names(f, nm, heading_count, all_names - {full(nm)}):
            pre = [i for i in by_name.get(n2, []) if i not in have and not is_no(ref, i, recs[i])
                   and agency_check(f, recs[i], st, layer_table) != 'differs']
            cand = [i for i in pre if holds_fn(ref, i) is True]
            if not cand and len(pre) == 1:   # report only: the one record of that name, missed only because the pin is outside it
                pin_ = (f or {}).get('pin') or []
                d = km_to_record(pin_[0], pin_[1], recs[pre[0]]) if len(pin_) == 2 else None
                for w, k_ in NEAR_MISS_KM:
                    if d is not None and d <= k_: out['second_name_near'][w] += 1
            if len(cand) == 1:
                add_row(p, cand[0], f'name: second name "{n2[:60]}" (the park\'s own page) + pin inside')
                out['gained'] += 1; out['second_name'] += 1; hits.append([ref, 'joined (second name)', cand[0]]); have.add(cand[0])
            elif len(cand) > 1:
                p['c'] = [[recs[i]['OBJECTID'], rec_name(recs[i]), round(float(recs[i].get('GIS_Acres') or 0)),
                           f'check (second name "{n2[:60]}": {len(cand)} records carry it)'] for i in cand] + list(p.get('c') or [])
                have |= set(cand)
        # P4: the tracts the park's own page names join their records on a layer the park is already joined to, within 5 km of the pin
        tracts = tract_names(f)
        pin = (f or {}).get('pin') or []
        if tracts and len(pin) == 2 and p.get('m'):
            lays = {layer_of(recs.get(str(q[0]))) for q in p.get('m') or [] if recs.get(str(q[0]))} - {''}
            words = {w for w in full(nm).split() if w not in ('state', 'national', 'park', 'area', 'wildlife', 'management')}
            for i, a in recs.items():
                if i in have or layer_of(a) not in lays: continue
                rn = full(rec_name(a))
                if not rn or not any(rn == t or (rn.endswith(' ' + t) and words & set(rn.split())) for t in tracts): continue
                if is_no(ref, i, a) or not near_box(pin[0], pin[1], a.get('_bb'), TRACT_KM): continue
                if other_park_name(rec_name(a), nm, others): continue
                add_row(p, i, f'name: tract "{rn[:60]}" (the park\'s own page lists it)')
                out['gained'] += 1; out['tract'] += 1; hits.append([ref, 'joined (tract)', i]); have.add(i)
        m = list(p.get('m') or [])
        if not m: continue
        out['parks'] += 1
        held = {}
        holds = lambda i: held.setdefault(i, holds_fn(ref, i))
        drop = []
        for q in m:
            i = str(q[0]); rec = recs.get(i)
            v = record_id_of(kind, rids.get(i) or {}) if kind else None
            if row_class(q) != 'name': continue
            if v is not None and v != val: drop.append((q, f"id: this record's {kind} is not {val}, the id in POTA's own link")); continue
            if id_agrees(kind, val, rids.get(i) or {}, rec, tie): continue           # the id agrees (own id, address or agency list): stands in for the name
            if rec is None: drop.append((q, 'no data: the record was not read this build')); continue
            if other_park_name(q[1], nm, others):
                drop.append((q, "name: this record carries another park's own full name")); continue
            par = [u for u in parent_units(f) if full(u.get('unit')) == full(q[1]) and full(u.get('unit')) != full(nm) and u.get('pota_ref') != ref]
            if par:   # P5: the park's own page says it lies inside this unit: the unit's record is not the park's own outline
                drop.append((q, f"place: the park's own page says it lies inside {str(par[0].get('unit'))[:60]}; that record is the bigger unit"))
                out['parent'] += 1; continue
            if agency_check(f, rec, st, layer_table) == 'differs': drop.append((q, "agency: the record belongs to another agency than POTA's link")); continue
            if compilation_kind_clash(nm, q[1], rec, layer_table):
                drop.append((q, "kind: a compilation layer's record (no agency vote) names another kind of place than the park")); continue
            if national_flag(q, m, recs, nm): drop.append((q, "national: a national-layer record of another level of government than the park's name")); continue
            if pin_3c(q, m, holds, nm): drop.append((q, "place: POTA's pin is in another of the park's records, none of this record's name")); continue
            if kind_check(typ, rec) == 'differs': notes.append('kind')                 # advisory only
        for q, w in drop: to_check(p, [q], w); out['moved'] += 1; hits.append([ref, reason_of(w), str(q[0])]); why.append(reason_of(w))
        left = p.get('m') or []
        name_left = [q for q in left if row_class(q) == 'name' and not id_agrees(kind, val, rids.get(str(q[0])) or {}, recs.get(str(q[0])), tie)]
        sv = size_vote(size_witnesses(f, shared), outline_size(p, left))
        id_ok = bool(kind) and any(id_agrees(kind, val, rids.get(str(q[0])) or {}, recs.get(str(q[0])), tie) for q in left)
        if name_left and sv[0] == 'far off' and not id_ok:
            to_check(p, name_left, f"size: the outline is {sv[1]} times the agency's own figure"); why.append('size')
            hits.extend([ref, 'size', str(q[0])] for q in name_left)
            out['moved'] += len(name_left)
        left = p.get('m') or []
        id_ok = bool(kind) and any(id_agrees(kind, val, rids.get(str(q[0])) or {}, recs.get(str(q[0])), tie) for q in left)
        link_nm = link_name_agree(f)
        if link_nm == 'part': notes.append('link name')
        place_ok = bool(left) and place_fn(ref, [str(q[0]) for q in left]) is True
        how = None
        if not left:
            p['g'] = 'pin'; st_ = 'pin'
        else:
            if id_ok: st_, how = 'confirmed', 'id'
            elif sv[0] == 'agrees': st_, how = 'confirmed', 'size'
            elif link_nm == 'strong' and place_ok: st_, how = 'confirmed', 'link'
            else: st_ = 'outlined'
        p['match'] = {'status': st_, 'why': sorted(set(why))}
        if notes: p['match']['notes'] = sorted(set(notes))
        if how: p['match']['by'] = how
        if id_ok: p['match']['id'] = f'{kind} {val}'
        if link_nm == 'strong': p['match']['link'] = 'strong'
        out[st_] += 1
        if how: out['by_' + how] += 1
        for w in set(why): out['why'][w] = out['why'].get(w, 0) + 1
        for w in set(notes): out['notes'][w] = out['notes'].get(w, 0) + 1
    return out


def facts_stamp(path):
    """'<made date> <first 12 of the file's sha256>' of the park facts file, or '' (plan L6: the input that decided is named)."""
    import gzip, hashlib
    if not path or not os.path.isfile(path): return ''
    h = hashlib.sha256(open(path, 'rb').read()).hexdigest()[:12]
    try:
        op = gzip.open if path.endswith('.gz') else open
        with op(path, 'rt', encoding='utf-8') as fh: made = json.load(fh).get('made') or ''
    except (OSError, ValueError, EOFError):
        made = ''
    return f'{made} {h}'.strip()


def km(la1, lo1, la2, lo2):
    return 111.2 * math.hypot(la1 - la2, (lo1 - lo2) * math.cos(math.radians((la1 + la2) / 2)))


def selftest():
    bad = []
    def ok(what, c):
        print(('  ok   ' if c else '  FAIL ') + what)
        if not c: bad.append(what)
    f = {'area': 'US-ZZ', 'name': 'Invented Lake State Park', 'type': 'State Park',
         'link': {'site': 'agency (known)', 'agency': 'ZZ State Parks', 'id_kind': 'NPS unit code', 'id_value': 'INVP',
                  'usable': True, 'page_kind': 'own page', 'id_shared_by': 1}}
    ok('exact name with kind', exact_name('Invented Lake State Park', 'Invented Lake', 'State Park'))
    ok('X never ties X Lake', not exact_name('Invented State Park', 'Invented Lake', 'State Park'))
    ok('NPS code not in unit list is no tie', link_tie(f, {'ABCD': {'ZZ'}})[0] is None)
    ok('state link vs federal record differs', agency_check(f, {'OBJECTID': 1, 'Mang_Name': 'USFS', 'Mang_Type': 'FED'}, 'ZZ') == 'differs')
    ok('state park vs wildlife area differs', kind_check('State Park', {'_k': ['wma']}) == 'differs')
    ok('address names the park in full', name_match('Invented Creek State Park', web_name('https://parks.example.gov/state-parks/invented-creek')) == 'strong')
    ok('a part name in the address is only part', name_match('Invented Creek State Park', 'creek') == 'part')
    ok('Minnesota forest id on sft is a same-kind id', ids_from({'OBJECTID': 'sgmnb1', 'SA': {'sft': 'SFT0000100'}}) == {'MN DNR unit id': 'SFT0000100'})
    lk = dict(f['link'], name_match='strong', state_check='same state', page_kind='own page', id_value='')
    ok("own page in the park's state with a strong address name agrees", link_name_agree({'name': 'Invented Lake State Park', 'link': lk}) == 'strong')
    return not bad


if __name__ == '__main__':
    import sys
    if '--selftest' in sys.argv:
        good = selftest()
        print('SELF-TEST PASSED' if good else 'SELF-TEST FAILED')
        sys.exit(0 if good else 1)
    print(__doc__)
