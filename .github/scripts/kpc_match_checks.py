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
import pathlib

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
    s = re.sub(r"['\u2019`]s\b", 's', s)   # 26 Nov (Fable's review, US-12389): a possessive is one word: DEVIL'S = DEVILS, not 'devil s'
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
    if pg.get('kind') != 'html': return []   # PN-G4: an html page's heading only, never a PDF's title or first line
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



# 24 Nov 2026 (owner 7:06 AM CT approved the auto-confirm rule, with both review additions):
# status only, never changes land. The held record's own name must match (Opus spelling table when
# the file is present, otherwise the shared letters-and-digits name key). The pin must sit inside
# the held record or within 100 m, measured on the SAVED outline, not the key's working copy (`bk`).
AUTO_CONFIRM_KM = 0.1
# Path agreed with Opus for the spelling table. The file is not in the tree yet; we fall back to the name key.
SPELLING_TABLE_PATHS = (
    '.github/name-spelling-table.json',
    'data/names/spelling-table.json',  # KPC-Data
)
STOPS_PATHS = (
    '.github/auto-confirm-stops.json',  # 24 Nov repair: IDs only, in this repo (hashed with the US rules)
)


def name_key(s):
    """Letters and digits only, lower-case (same rule as kpc_store_attrs.name_key)."""
    return re.sub(r'[^a-z0-9]', '', str(s or '').lower())


def load_spelling_table(paths=None, root=None):
    """Read Opus's spelling table if the file is there. map of name_key -> name_key, or a list of pairs.
    Missing file: empty table (the name key is used alone)."""
    root = pathlib.Path(root) if root else pathlib.Path(__file__).resolve().parents[2]
    wanted = list(paths or [])
    env = os.environ.get('KPC_SPELLING_TABLE') or ''
    if env:
        wanted = [env] + wanted
    wanted.extend(SPELLING_TABLE_PATHS)
    for rel in wanted:
        f = pathlib.Path(rel)
        if not f.is_file():
            f = root / rel
        if not f.is_file():
            continue
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        table = {}
        raw = data.get('map') if isinstance(data, dict) else data
        if isinstance(raw, dict):
            for a, b in raw.items():
                table[name_key(a)] = name_key(b)
        elif isinstance(raw, list):
            for pair in raw:
                if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                    table[name_key(pair[0])] = name_key(pair[1])
                    table[name_key(pair[1])] = name_key(pair[0])
        pairs = (data.get('pairs') or []) if isinstance(data, dict) else []
        for pair in pairs:
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                table[name_key(pair[0])] = name_key(pair[1])
                table[name_key(pair[1])] = name_key(pair[0])
        return table, str(f)
    return {}, None


def load_auto_confirm_stops(paths=None, root=None):
    """IDs-only stop list (calls, land-wrong, pin-wrong). Missing or unreadable: (None, None) = fail closed
    (auto-confirm confirms nothing until the list can be read)."""
    root = pathlib.Path(root) if root else pathlib.Path(__file__).resolve().parents[2]
    wanted = list(paths) if paths is not None else list(STOPS_PATHS)
    env = os.environ.get('KPC_AUTO_CONFIRM_STOPS') or ''
    if env:
        wanted = [env] + wanted
    for rel in wanted:
        f = pathlib.Path(rel)
        if not f.is_file():
            f = root / rel
        if not f.is_file():
            continue
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return None, None   # present but unreadable: confirm nothing
        rows = data.get('parks') if isinstance(data, dict) else data
        if not isinstance(rows, list):
            return None, None
        stops = {x for x in rows if isinstance(x, str) and x}
        return stops, str(f)
    return None, None   # no file: confirm nothing


def spelled_key(s, table=None):
    """name_key after each word is rewritten by the spelling table (SWA -> statewildlifearea)."""
    words = re.findall(r'[a-z0-9]+', str(s or '').lower())
    if not words:
        return ''
    if not table:
        return ''.join(words)
    return ''.join(table.get(w, w) for w in words)


def names_match(park_name, rec_name, table=None):
    """Held-name test: same name_key, or the same after the spelling table is applied to either side."""
    a, b = name_key(park_name), name_key(rec_name)
    if not a or not b:
        return False
    if a == b:
        return True
    if not table:
        return False
    a2, b2 = spelled_key(park_name, table), spelled_key(rec_name, table)
    if a2 and a2 == b2:
        return True
    return table.get(a, a) == table.get(b, b) and bool(table.get(a, a))


def held_id_of(p):
    held = p.get('held') or {}
    if isinstance(held, dict) and (held.get('ids') or []):
        return str(held['ids'][0])
    bk = p.get('bk') or [None]
    if bk and bk[0] is not None:
        return str(bk[0])
    return ''


def evidence_id_of(p):
    """26 Nov 2026 (Fable's review finding 6): the record the evidence block reads. A held id counts only while it is still one of
    the park's joined records (a website-key id read on another day can name other land: Northwest Angle's held 'sgmnb14' is
    Crow Wing's forest in the fresh file); else this run's best try ('bk'), if joined; else the first joined record."""
    in_m = [str(q[0]) for q in p.get('m') or [] if isinstance(q, (list, tuple)) and q]
    held = p.get('held') or {}
    for i in (held.get('ids') or []) if isinstance(held, dict) else []:
        if str(i) in in_m: return str(i)
    bk = p.get('bk') or [None]
    if bk and bk[0] is not None and str(bk[0]) in in_m: return str(bk[0])
    return in_m[0] if in_m else ''



def kinds_clash(p, rec, table=None):
    """True when the park's kind and the record's layer kind are both known and do not agree (the same test as claim_fit)."""
    a, b = kinds(p.get('t') or p.get('n') or ''), layer_kinds(rec, table)
    return bool(a and b and not (a & b or any(a & c and b & c for c in US_COMPAT)))


def _saved_shape(rec):
    """A record dict the distance helpers can read: prefer `_g`, else wrap a saved `_r` rings list.
    Never changes the caller's record."""
    rec = rec or {}
    if rec.get('_g'):
        return rec
    if rec.get('_r'):
        return dict(rec, _g={'rings': rec['_r']})
    return rec


def _pin_inside_saved(lat, lon, rec):
    """True when the pin sits inside the saved outline (0 m, not the distance to the edge)."""
    return _in_rings(lat, lon, _saved_shape(rec))


def _km_to_saved(lat, lon, rec):
    """Kilometres to the saved outline: 0 when the pin is inside, else edge distance."""
    rec = _saved_shape(rec)
    if _in_rings(lat, lon, rec):
        return 0.0
    return km_to_record(lat, lon, rec)


def held_id_for_pass(ref, p, recs, pin, holds_fn=None):
    """The held record during the match pass, when `held` / `bk` are not on the park yet.

    1. The record the builder holds (holds_fn is True). That pick wins; no later fallback.
    2. Else the first joined record (m order, usually largest first) whose SAVED outline
       contains the pin.
    3. Else, if the pin is within AUTO_CONFIRM_KM (100 m) of exactly one joined saved
       outline, that record. Two or more within 100 m and none containing the pin: no
       record (no nearest-of-many fallback).
    '' when none of those apply, or when there is no usable pin for steps 2–3.
    A person's NO is applied later in auto_confirm_ok, not here.
    """
    rows = []
    for q in p.get('m') or []:
        i = str(q[0])
        rec = (recs or {}).get(i) or (recs or {}).get(q[0])
        if rec is not None:
            rows.append((i, rec))
    if not rows:
        return ''
    if holds_fn:
        for i, rec in rows:
            if holds_fn(ref, i) is True:
                return i
    try:
        lat, lon = float(pin[0]), float(pin[1])
    except (TypeError, ValueError, IndexError):
        return ''
    inside = [i for i, rec in rows if _pin_inside_saved(lat, lon, rec)]
    if inside:
        return inside[0]
    near = []
    for i, rec in rows:
        d = _km_to_saved(lat, lon, rec)
        if d is not None and d <= AUTO_CONFIRM_KM + 1e-12:
            near.append(i)
    if len(near) == 1:
        return near[0]
    return ''


# 24 Nov 2026 (owner t2067u 8:32 PM CT 'I agree work on it', after the 787 loose-name confirm check: 730 right, 18 wrong, 39
# unsure). Four auto-confirm guards. Status only, except A3, which gives each same-name park only its own piece of a shared
# record. A1: confirm only on a record still in the park's outline (its 'm' rows). A2: no auto-confirm when another park of the
# state holds the same record. A4: the park's level of government (from POTA's type) must not clash with the record's.
# A3: parks whose POTA names differ only by the words in brackets ('X (A County) State Forest', 'X (B County) State Forest') and
# share one multi-part record each keep only the record's tracts nearest their own pin ('parts', the same field rule B12 writes).
BRACKET_RX = re.compile(r'\(([^()]*)\)')
A3_TRACT_GAP_KM = 1.0      # pieces closer than this are one tract (kpc_key_rules.tracts_of)
A3_PINS_APART_KM = 15.0    # the pins of two bracket twins must be this far apart (the B12 / name-only prune distance)
ONE_PLACE_KM = 15.0        # a record whose pieces all chain within this is one place (bracket words need not be in its name)


def bracket_words(name):
    """The words in brackets in a POTA name, as full() writes them: 'Lost Lake (Alpha County) State Forest' -> ('alpha county',).
    full() itself drops bracket text, which is how two same-name forests looked like one park to the looser name rule."""
    return tuple(t for t in (full(x) for x in BRACKET_RX.findall(str(name or ''))) if t)


def rec_rings(rec):
    """A record's rings ([lon, lat] lists of 3+ points) from `_g` ({'rings'} / Polygon / MultiPolygon) or a saved `_r` list."""
    rec = rec or {}
    g = rec.get('_g') or {}
    if isinstance(g, dict) and g:
        rs = g.get('rings') or (g.get('coordinates') if g.get('type') == 'Polygon' else
                               [r for poly in g.get('coordinates') or [] for r in poly] if g.get('type') == 'MultiPolygon' else [])
    else:
        rs = rec.get('_r') or []
    return [r for r in rs or [] if r and len(r) > 2]


def ring_box(r):
    return [min(q[0] for q in r), min(q[1] for q in r), max(q[0] for q in r), max(q[1] for q in r)]


def box_gap_km(a, b):
    la = (a[1] + a[3] + b[1] + b[3]) / 4
    dx = max(0, b[0] - a[2], a[0] - b[2]) * 111.32 * math.cos(math.radians(la)); dy = max(0, b[1] - a[3], a[1] - b[3]) * 110.57
    return math.hypot(dx, dy)


def tracts_of(boxes, gap_km=A3_TRACT_GAP_KM):
    """Group pieces ([w, s, e, n] boxes) into tracts: pieces closer than gap_km are one tract (same as kpc_key_rules.tracts_of)."""
    n = len(boxes); grp = list(range(n))
    def find(i):
        while grp[i] != i: grp[i] = grp[grp[i]]; i = grp[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if box_gap_km(boxes[i], boxes[j]) <= gap_km: grp[find(i)] = find(j)
    out = {}
    for i in range(n): out.setdefault(find(i), []).append(i)
    return sorted(out.values(), key=lambda v: v[0])


def one_place(rec):
    """True when every piece of the record chains within ONE_PLACE_KM (one place); a record with no shape counts as one place."""
    rs = rec_rings(rec)
    return len(rs) < 2 or len(tracts_of([ring_box(r) for r in rs], ONE_PLACE_KM)) == 1


def bracket_place_ok(park_name, rec):
    """A3 (matching): POTA's bracket words are not thrown away. A park named with words in brackets matches a record by name only
    when the record's own name carries those words, or the record is one place (not two same-name places far apart)."""
    bw = bracket_words(park_name)
    if not bw: return True
    rn = ' ' + re.sub(r'[^a-z0-9 ]+', ' ', str(rec_name(rec) or '').lower()) + ' '
    rn = ' ' + ' '.join(rn.split()) + ' '
    if all(' ' + w + ' ' in rn for w in bw): return True
    return one_place(rec)


def _ring_km(lat, lon, r):
    """Kilometres from a pin to one ring: 0 inside, else the edge distance."""
    ins, j = False, len(r) - 1
    for i in range(len(r)):
        xi, yi, xj, yj = r[i][0], r[i][1], r[j][0], r[j][1]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi: ins = not ins
        j = i
    if ins: return 0.0
    d = km_to_record(lat, lon, {'_g': {'rings': [r]}})
    return 1e9 if d is None else d


def _ring_acres(rr):
    """Acres of a group of rings (signed shoelace added up, so holes written the other way round come off)."""
    if not rr: return 0.0
    la0 = sum(q[1] for r in rr for q in r) / sum(len(r) for r in rr)
    kx, ky = 111320.0 * math.cos(math.radians(la0)), 110574.0
    tot = 0.0
    for r in rr:
        tot += 0.5 * sum(x1 * kx * y2 * ky - x2 * kx * y1 * ky for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]))
    return abs(tot) / 4046.86


def _pin_of(ref, facts):
    pin = ((facts or {}).get(ref) or {}).get('pin')
    try:
        return float(pin[0]), float(pin[1])
    except (TypeError, ValueError, IndexError):
        return None


def split_bracket_twins(parks, recs, facts, skip=(), held_by=None):
    """A3: a multi-part record held by two or more parks whose POTA names are the same once the bracket words are left out, and
    whose bracket words differ, is cut by tract: each tract goes to the park whose pin is nearest, and each park keeps only its
    own tracts as 'parts' {record id: [[w, s, e, n], ...]} (what kpc_outlines_from_key and the 2-fer line already read).
    Not done (left as it is) when: a park already has parts for the record (rule B12 did it), a park has no pin, two pins are
    within A3_PINS_APART_KM, a park would get no tract, or the record is one tract. A person's ('reviewed') row is never cut.
    The park's 'ac' and the row's acres drop by the land it no longer holds. Returns [(park, record id, kept, of)]."""
    if held_by is None:
        held_by = {}
        for r_, p_ in parks.items():
            if r_ in skip: continue
            for q in p_.get('m') or []: held_by.setdefault(str(q[0]), set()).add(r_)
    done = []
    for rid, refs_ in sorted(held_by.items()):
        refs = sorted(r for r in refs_ if r in parks and r not in skip)
        rec = (recs or {}).get(rid)
        if len(refs) < 2 or rec is None: continue
        names = [parks[r].get('n') or ((facts or {}).get(r) or {}).get('name') or '' for r in refs]
        if len({full(n) for n in names}) != 1 or not full(names[0]): continue
        bws = [bracket_words(n) for n in names]
        if len(set(bws)) != len(bws) or sum(1 for b in bws if not b) > 1: continue
        if any(rid in (parks[r].get('parts') or {}) for r in refs): continue
        pins = {r: _pin_of(r, facts) for r in refs}
        if any(v is None for v in pins.values()): continue
        if any(km(pins[a][0], pins[a][1], pins[b][0], pins[b][1]) <= A3_PINS_APART_KM for i, a in enumerate(refs) for b in refs[i + 1:]): continue
        rs = rec_rings(rec)
        if len(rs) < 2: continue
        boxes = [ring_box(r) for r in rs]
        tracts = tracts_of(boxes)
        if len(tracts) < 2: continue
        mine = {r: [] for r in refs}
        for t in tracts:
            d = {r: min(_ring_km(pins[r][0], pins[r][1], rs[i]) for i in t) for r in refs}
            best = min(d.values())
            for r in refs:
                if d[r] is not None and d[r] <= best + 1e-9: mine[r].extend(t)
        if any(not v for v in mine.values()): continue
        whole = _ring_acres(rs)
        for r in refs:
            p = parks[r]
            if len(mine[r]) == len(rs): continue
            if any(str(q[0]) == rid and str(q[3] if len(q) > 3 else '').startswith('reviewed') for q in p.get('m') or []): continue
            keep = sorted(mine[r])
            p.setdefault('parts', {})[rid] = [[round(c, 4) for c in boxes[i]] for i in keep]
            own = _ring_acres([rs[i] for i in keep])
            for q in p.get('m') or []:
                if str(q[0]) == rid and len(q) > 2: q[2] = round(own)
            if p.get('ac') not in (None, ''):
                try: p['ac'] = max(round(own), round(float(p['ac']) - max(0.0, whole - own)))
                except (TypeError, ValueError): pass
            done.append((r, rid, len(keep), len(rs)))
    return done


def park_gov_level(typ):
    """POTA's park type -> 'STATE' / 'FED' / 'LOC' / None (the type says nothing about who runs it)."""
    t = ' '.join(str(typ or '').lower().split())
    if re.match(r'(state|commonwealth)\b', t): return 'STATE'
    if re.match(r'(national|blm|federal|us|u\.s\.)\b', t) or t == 'wetland management district': return 'FED'
    if re.match(r'(county|city|municipal|metro|metropolitan|regional|town|township|village|borough|parish)\b', t): return 'LOC'
    return None


def record_gov_level(rec, table=None):
    """The record's level of government from its own agency (record_agency, never its name), or the state owner label (W-G11)."""
    a = record_agency(rec, table)
    if a is None: return 'STATE' if owner_family(rec) == 'STATE' else None
    if a in FEDERAL or str(a).startswith('FED'): return 'FED'
    if a in ('STATE', 'LOC', 'DIST', 'PVT', 'NGO', 'TRIB'): return a
    return None


def auto_confirm_agency_ok(fact, p, rec, st='', table=None):
    """A4: False when POTA's link names another agency (agency_check 'differs'), or POTA's park type and the record's own agency
    are of different levels of government (a state forest on county land, a county park on state land). No data either way =
    no vote. The W-G11 (state-owned) and W-G12 (state park on federal lake land under its own name) exceptions still hold."""
    if agency_check(fact, rec, st, table) == 'differs': return False
    pl = park_gov_level(p.get('t') or (fact or {}).get('type'))
    rl = record_gov_level(rec, table)
    if pl is None or rl is None or pl == rl: return True
    if pl == 'STATE' and owner_family(rec) == 'STATE': return True
    if pl == 'STATE' and record_agency(rec, table) in RESERVOIR_OWNERS and \
            same_park_name(p.get('n') or (fact or {}).get('name'), rec_name(rec)): return True
    return False


def auto_confirm_ok(ref, p, recs, facts=None, holds_fn=None, is_no=None, blocked=None,
                    stop_parks=None, spelling=None, pin=None, name_test=None, layer_table=None,
                    shared_by=None, st=''):
    """True when this joined park may be status-confirmed. Never changes land.

    The held record's own name must match the park, and the pin must sit inside that
    record or within AUTO_CONFIRM_KM (100 m), measured on the saved outline in `recs`
    (inside = 0 m; not the key's `bk` working-copy distance).
    The held record is held_id_of (when `held` / `bk` are already set), else
    held_id_for_pass (the builder's hold, else the saved outline that contains the
    pin, else the only outline within 100 m). If neither a held record nor a unique
    close outline is found, this does not confirm.
    Stops: person-NO, a blocked id, or a park on the stop list (calls, land-wrong, pin-wrong).
    name_test(park name, held record name) replaces the name test (24 Nov: 'page names the land' uses the same
    record, the same stops and the same 100 m; only the name witness differs).
    stop_parks is None (missing / unreadable list) = confirm nothing (fail closed).
    24 Nov 2026 (owner t2067u): A1 the held record must still be one of the park's joined ('m') records (a record already moved to
    the check list is not the outline); A2 shared_by {record id: {parks}}: no confirm when another park holds the same record;
    A3 a park named with words in brackets needs them in the record's name, or a record that is one place (bracket_place_ok);
    A4 the agency / level-of-government check (auto_confirm_agency_ok).
    """
    if stop_parks is None:
        return False
    if ref in stop_parks:
        return False
    if not (p.get('m') or []):
        return False
    if pin is None:
        pin = ((facts or {}).get(ref) or {}).get('pin')
    hid = held_id_of(p)
    if not hid:
        hid = held_id_for_pass(ref, p, recs, pin, holds_fn)
    if not hid:
        return False
    if str(hid) not in {str(q[0]) for q in p.get('m') or []}:   # A1: only a record still in the outline
        return False
    rec = (recs or {}).get(hid) or (recs or {}).get(str(hid))
    if rec is None:
        return False
    if set((shared_by or {}).get(str(hid)) or ()) - {ref}:   # A2: another park holds the same record
        return False
    if is_no and is_no(ref, hid, rec):
        return False
    bl = blocked or {}
    if hid in (bl.get(ref) or bl.get(str(ref)) or set()):
        return False
    facts = facts or {}
    pn = p.get('n') or (facts.get(ref) or {}).get('name') or ''
    rn = rec_name(rec)
    if name_test is not None:
        if not name_test(pn, rn):
            return False
    elif not (names_match(pn, rn, spelling) or same_place_name(pn, rn)):   # 24 Nov: Opus's spelling table (same_place_name) too
        return False
    if kinds_clash(p, rec, layer_table):   # 24 Nov review: a bare record name ('Kiger') takes its kind from its layer
        return False
    if not bracket_place_ok(pn, rec):   # A3: POTA's bracket words are not thrown away
        return False
    if not auto_confirm_agency_ok(facts.get(ref) or {}, p, rec, st, layer_table):   # A4
        return False
    if not pin or len(pin) < 2 or pin[0] in (None, '') or pin[1] in (None, ''):
        return False
    try:
        lat, lon = float(pin[0]), float(pin[1])
    except (TypeError, ValueError):
        return False
    d = _km_to_saved(lat, lon, rec)
    return d is not None and d <= AUTO_CONFIRM_KM + 1e-12



FT_PER_KM = 3280.84   # 24 Nov report: pin distance is shown in feet


def held_name_how(park_name, rec_name, table=None):
    """Which held-name rule agreed: 'exact', 'spelling table', 'looser name', or ''."""
    if names_match(park_name, rec_name, None):
        return 'exact'
    if table and names_match(park_name, rec_name, table):
        return 'spelling table'
    if same_place_name(park_name, rec_name):
        return 'looser name'
    return ''


def official_acres_of(fact):
    """Official acres from KPC-Data park facts (the size row), or None."""
    s = (fact or {}).get('size') if isinstance(fact, dict) else None
    if not isinstance(s, dict):
        return None
    try:
        a = s.get('acres')
        if a not in (None, '', 'n/a'):
            return float(a)
    except (TypeError, ValueError):
        return None
    return None


def outline_acres_of(p):
    """The park's outline acres: the measured 'ac' when present, else the joined row acres added up."""
    if p.get('ac') not in (None, ''):
        try:
            return float(p['ac'])
        except (TypeError, ValueError):
            pass
    tot = 0.0
    for q in p.get('m') or []:
        if len(q) > 2 and q[2] not in (None, ''):
            try:
                tot += float(q[2])
            except (TypeError, ValueError):
                pass
    return tot


def size_far_off(outline, official, far=None):
    """True when the outline is SIZE_FAR times off the official acres (either way)."""
    far = SIZE_FAR if far is None else far
    if official is None or official <= 0 or outline is None:
        return False, None
    ratio = outline / official
    if ratio > far or ratio < 1 / far:
        return True, round(ratio, 3)
    return False, round(ratio, 3)


def agency_id_of(rec, fact=None):
    """A stable agency id on the record (store fields) or the park facts link id, else ''."""
    sa = (rec or {}).get('SA') or {}
    if not isinstance(sa, dict):
        sa = {}
    for k in ('Unit_ID', 'UniqueID', 'UNIQUEID', 'uniqueid', 'LinkID', 'LINKID', 'sft',
              'pgrm_project', 'UNITCODE', 'UnitCode', 'ParkID', 'UNIT_ID'):
        v = sa.get(k)
        if v not in (None, ''):
            return str(v)
    link = (fact or {}).get('link') or {}
    if link.get('id_value') not in (None, ''):
        kind = link.get('id_kind') or 'id'
        return f"{kind} {link.get('id_value')}"
    return ''


def page_link_of(fact):
    pg = (fact or {}).get('page') or {}
    return str(pg.get('url') or '')


def confirm_evidence(ref, p, recs, facts, hid, pin=None):
    """Evidence for one confirm: agency id, sizes, pin distance in feet, page link. IDs only."""
    fact = (facts or {}).get(ref) or {}
    rec = (recs or {}).get(hid) or (recs or {}).get(str(hid or '')) or {}
    if pin is None:
        pin = fact.get('pin')
    pin_ft = None
    if pin and rec:
        try:
            d = _km_to_saved(float(pin[0]), float(pin[1]), rec)
            if d is not None:
                pin_ft = int(round(d * FT_PER_KM))
        except (TypeError, ValueError, IndexError):
            pin_ft = None
    official = official_acres_of(fact)
    outline = outline_acres_of(p)
    far, ratio = size_far_off(outline, official)
    ev = {
        'held_id': str(hid or ''),
        'agency_id': agency_id_of(rec, fact),
        'outline_acres': None if outline is None else round(outline, 1),
        'official_acres': None if official is None else round(official, 1),
        'pin_ft': pin_ft,
        'page_link': page_link_of(fact),
    }
    if far:
        ev['size_flag'] = 'far off'
        ev['size_ratio'] = ratio
    return ev


def on_edge(pin, rec):
    """PN-G2: True when the pin lies ON the record's edge (within 1 mm): on the line is not strictly inside."""
    d = km_to_record(pin[0], pin[1], rec) if pin and len(pin) == 2 else None
    return d is not None and d < 1e-6


def claim_fit(park, rec, table=None):
    """P7: how well a park fits a record two parks claim: name (2 exact, 1 with 'state' left out, 0 other) plus kind
    (+1 agrees, -1 differs, 0 no data)."""
    rn, pn = full(rec_name(rec)), full(park.get('n') or '')
    loose = lambda t: ' '.join(w for w in t.split() if w != 'state')
    sc = 2 if rn and rn == pn else (1 if rn and loose(rn) == loose(pn) else 0)
    a, b = kinds(park.get('t') or park.get('n') or ''), layer_kinds(rec, table)
    if a and b: sc += 1 if (a & b or any(a & c and b & c for c in US_COMPAT)) else -1
    return sc


# 24 Nov 2026 (owner 6:41 AM "1 name i been screaming this!", 6:57 AM "Page reader whole reason is to read names!!"): the
# SPELLING TABLE and the PAGE-NAMES-THE-LAND witness. The same name written another way: the short forms agencies use spelled out
# (a code at the END of a name only for CA / WA / GA, never a state code in the middle), one spelling of sulfur, a plural trail,
# then the kind words set aside. Two names agree when what is left is the same and the kinds of land do not clash.
SPELL = {'swa': 'state wildlife area', 'sna': 'state natural area', 'fwa': 'fish and wildlife area', 'wpa': 'waterfowl production area',
         'svra': 'state vehicular recreation area', 'srma': 'special recreation management area', 'erma': 'extensive recreation management area',
         'wsa': 'wilderness study area', 'hp': 'heritage preserve', 'fwma': 'fish and wildlife management area', 'mua': 'multiple use area',
         'hma': 'herd management area', 'col': 'colonel', 'sulphur': 'sulfur', 'trails': 'trail', 'mgmt': 'management', 'natl': 'national'}
SPELL_LAST = {'ca': 'conservation area', 'wa': 'wildlife area', 'ga': 'game area'}
KIND_WORDS = set('state national park parks wildlife area areas management conservation natural nature preserve reserve reservation '
                 'recreation fishing fish and game land lands refuge forest forests habitat special extensive blm unit site historic '
                 'historical memorial monument scenic trail public access waterfowl fishery comprehensive no of the at sanctuary study '
                 'herd production multiple use vehicular heritage'.split())
KIND_FAMILY = {'park': {'park', 'parks'}, 'forest': {'forest', 'forests'}, 'wildlife': {'wildlife', 'game', 'waterfowl', 'fish', 'fishery', 'habitat'},
               'wilderness': {'wilderness'}, 'preserve': {'preserve', 'reserve', 'natural', 'nature'},
               # 24 Nov review: every word that names a kind of place has a family, so 'X Trail' never equals 'X State Park'
               'trail': {'trail'}, 'access': {'access', 'fishing'}, 'memorial': {'memorial'}, 'monument': {'monument'},
               'historic': {'historic', 'historical', 'heritage'}, 'refuge': {'refuge', 'sanctuary'}, 'recreation': {'recreation'},
               'conservation': {'conservation'}, 'reservation': {'reservation'}, 'herd': {'herd'}, 'vehicular': {'vehicular'},
               'multiple use': {'multiple'}}


def spelled(name):
    """full(name) with the agencies' short forms written out (SPELL_LAST only as the last word of a longer name)."""
    w = full(name).split()
    out = []
    for i, x in enumerate(w):
        out += (SPELL_LAST[x] if i == len(w) - 1 and len(w) > 1 and x in SPELL_LAST else SPELL.get(x, x)).split()
    return out


def name_core(name):
    return ''.join(x for x in spelled(name) if x not in KIND_WORDS)


def kind_families(name):
    w = set(spelled(name))
    return {k for k, v in KIND_FAMILY.items() if w & v}


def same_place_name(a, b):
    """True when two names are the same place name written another way: the same core (4+ letters) once the short forms are
    spelled out and the kind words set aside, and no clash of kinds (a forest is not a park; Wilderness is not a Wilderness
    Study Area). 'Ogden Treat SWA' = 'Ogden-Treat State Wildlife Area'; 'Hot Sulphur Springs' = 'Hot Sulfur Springs'."""
    ca, cb = name_core(a), name_core(b)
    if len(ca) < 4 or ca != cb: return False
    fa, fb = kind_families(a), kind_families(b)
    if fa and fb and not (fa & fb): return False
    sa, sb = ' '.join(spelled(a)), ' '.join(spelled(b))
    return ('wilderness study' in sa) == ('wilderness study' in sb)


def page_names_land(fact, park_name, land_name, heading_count=None, names_in_state=None):
    """The park's OWN official html page calls the park by the land's own name (the page heading or one part of it): the page and
    the agency's map record name the same place. Never a site heading, never another POTA park's name in the state."""
    if not own_page(fact) or not land_name: return False
    pg = (fact or {}).get('page') or {}
    if pg.get('kind') != 'html': return False
    raw = str(pg.get('name_on_page') or '').strip()
    if not raw or '\ufffd' in raw: return False
    for part in [raw] + SECOND_NAME_SPLIT.split(raw):
        part = part.strip()
        n = full(part)
        if not n: continue
        if heading_count and heading_count.get((pg.get('host'), n), 0) >= SITE_HEADING_PARKS: continue
        if names_in_state and n in names_in_state and n != full(park_name): continue
        if n == full(land_name) or same_place_name(part, land_name): return True
    return False


PAGE_NAME_OK = ('same', 'same-core', 'same-words')   # W4 / W-G5 (owner 23 Nov 2026 12:51 AM)


def page_name_agrees(fact):
    """W4 (owner's rulings W-G4 "Yes I think so", W-G5 "Yes", 23 Nov 2026 12:51 AM): the park's OWN page on an official site
    carries the park's own name. The page reader's name check decides it (KPC-Data park facts, page.name_vs_pota): the same
    name, the same core, or the same words calling the place another kind ('Anthony Branch Fishery Area' for 'Anthony Branch
    State Fish and Wildlife Area'). A list, a shared page, an unofficial site or a page that names another place gives nothing."""
    return own_page(fact) and str((((fact or {}).get('page') or {}).get('name_vs_pota')) or '') in PAGE_NAME_OK


def map_link_names(fact):
    """W5 MAP-LINK NAME (owner 23 Nov 2026: 12:51 AM 'Yes', 4:28 AM 'yes for both'): the names the park's OWN page on an official
    site hands to the agency's own map viewer in its map link (KPC-Data park facts page.map_names; Wisconsin DNR:
    ...Public_Access_Lands&ID=MACK WILDLIFE AREA), as bare names (bare_name: the kind words and a loose 'state' left out, so the
    map's 'MACK WILDLIFE AREA' is the record's 'Mack State Wildlife Area'). A list, a shared page or an unofficial site gives none."""
    if not own_page(fact): return []
    out = []
    for m in ((fact or {}).get('page') or {}).get('map_names') or []:
        n = bare_name((m or {}).get('name')) if isinstance(m, dict) else ''
        if n and len(n) > 3 and n not in out: out.append(n)
    return out[:3]


COUNTY_FAR_X = 2.0     # W6: how many county radii from the county's middle a record may lie and still count as in or by it
COUNTY_FAR_KM = 25.0   # ... and never nearer than this


def county_areas_of(fact):
    """W6 COUNTY (owner 23 Nov 2026: 12:51 AM 'Yes', 4:28 AM 'yes for both', ruling W-G8 the check list; 5:24 AM "I dont want key
    bots to do internet stuff"): the counties the park's OWN page on an official site names, each with its middle point and the
    radius of a circle of its size. The PC's converter looked them up; park facts carries them (page.county_areas); nothing
    is fetched here. A list, a shared page or an unofficial site gives none."""
    if not own_page(fact): return []
    out = []
    for c in ((fact or {}).get('page') or {}).get('county_areas') or []:
        try: out.append((str(c.get('name') or ''), float(c['lat']), float(c['lon']), float(c['radius_km'])))
        except (TypeError, ValueError, KeyError): continue
    return [c for c in out if c[0] and c[3] > 0][:4]


def outside_counties(rec, areas):
    """True when the record's box lies well outside EVERY county the page names: its nearest corner or edge is farther from the
    county's middle than COUNTY_FAR_X radii (and COUNTY_FAR_KM). A county is no circle, so this only catches land that is
    clearly somewhere else (the same name in another part of the state); a record with no box is never called outside."""
    bb = (rec or {}).get('_bb')
    if not areas or not bb or len(bb) != 4: return False
    for _n, la, lo, r in areas:
        x, y = min(max(lo, bb[0]), bb[2]), min(max(la, bb[1]), bb[3])
        dy = (y - la) * 110.574
        dx = (x - lo) * 111.320 * math.cos(math.radians(la))
        if math.hypot(dx, dy) <= max(COUNTY_FAR_KM, COUNTY_FAR_X * r): return False
    return True


NEAR_TOWN_FAR_X = 3.0     # W-G6: land farther than this many times the point's own 'within' distance from a 'near a town' point ...
NEAR_TOWN_FAR_KM = 25.0   # ... and farther than this, lies far from where the park's own page puts the park


def near_points_of(fact):
    """W-G6 NEAR A TOWN (owner 23 Nov 2026 6:37 AM, '4 I say yes'): the approximate points the park's OWN page on an official
    site gives in words ('2 miles east of Shiocton'), each with how far off it may be. The PC's reader made them from the
    Census / Natural Resources Canada town lists (park facts page.near); nothing is fetched here. A list, a shared page or an
    unofficial site gives none."""
    if not own_page(fact): return []
    out = []
    for n in ((fact or {}).get('page') or {}).get('near') or []:
        try:
            la, lo, w = float(n['lat']), float(n['lon']), float(n.get('within_km') or 0)
        except (TypeError, ValueError, KeyError):
            continue
        if -90 <= la <= 90 and -180 <= lo <= 180 and w > 0: out.append((la, lo, w, str(n.get('from') or '')))
    return out[:3]


def _in_rings(lat, lon, rec):
    g = (rec or {}).get('_g') or {}
    rs = g.get('rings') or (g.get('coordinates') if g.get('type') == 'Polygon' else
                           [r for poly in g.get('coordinates') or [] for r in poly] if g.get('type') == 'MultiPolygon' else [])
    ins = False
    for r in rs:
        j = len(r) - 1
        for i in range(len(r)):
            xi, yi, xj, yj = r[i][0], r[i][1], r[j][0], r[j][1]
            if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi: ins = not ins
            j = i
    return ins


def _km_to_box(lat, lon, bb):
    if not bb or len(bb) != 4: return None
    x, y = min(max(lon, bb[0]), bb[2]), min(max(lat, bb[1]), bb[3])
    return math.hypot((x - lon) * 111.320 * math.cos(math.radians(lat)), (y - lat) * 110.574)


def near_town_vote(rec, pts):
    """W-G6: 'inside' when the record's land reaches into a point's circle (the point inside the land, or its edge within the
    point's 'within' distance; the record's box when it has no shape); 'far' when its box lies farther than NEAR_TOWN_FAR_X
    times 'within' (and NEAR_TOWN_FAR_KM) from EVERY point; else None (no vote). A record with no box is never far."""
    if not pts or not rec: return None
    bb = rec.get('_bb')
    far_all = bool(bb and len(bb) == 4)
    for la, lo, w, _f in pts:
        d = km_to_record(la, lo, rec)
        if d is None:
            d = _km_to_box(la, lo, bb)
        elif _in_rings(la, lo, rec):
            d = 0.0
        if d is not None and d <= w: return 'inside'
        db = _km_to_box(la, lo, bb)
        if db is None or db <= max(NEAR_TOWN_FAR_KM, NEAR_TOWN_FAR_X * w): far_all = False
    return 'far' if far_all else None


def page_pins(fact):
    pg = (fact or {}).get('page') or {}
    if pg.get('own_page') != 'own' or pg.get('unofficial'): return []
    out = []
    for c in pg.get('coords') or []:
        if isinstance(c, dict) and str(c.get('role') or '') in ('office', 'mailing'): continue   # 22 Nov: an office is not the park
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
        if m and m.group(1):   # 'glue' (24 Nov): the field drops the link's ':' (MI DNR LinkID SPRK433 = link SPRK:433)
            v = t['glue'].join(g for g in m.groups() if g) if t.get('glue') else m.group(1)
            out[addr_key(t['kind'])] = norm_id(v)
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


RESERVOIR_OWNERS = ('USACE', 'BOR', 'FED:TVA')   # W-G12: the federal agencies that own the land under many state-run lake parks


def owner_family(rec):
    """W-G11 (owner 23 Nov 2026, 6:42 AM 'Yes'): the OWNER label of a national-list record: 'STATE' when its Own_Type is STAT.
    None for anything else, and for every record of a layer with its own table row: there Own_Type is the saved copy's tag
    for the table it came from, not an owner."""
    rec = rec or {}
    if re.match(r'[a-z]*', str(rec.get('OBJECTID'))).group(0): return None
    return 'STATE' if str(rec.get('Own_Type') or '').strip().upper() == 'STAT' else None


def same_park_name(park_name, rec_name):
    """W-G12: the record carries the park's own name: the same full name, or the same bare name with the same kind of place
    ('Otter Lake State Park' and 'Otter Lake Recreation Area'). A record that names no kind ('Otter Lake': the whole lake
    project) or another kind, and 'one name holds the other', are NOT the same."""
    a, b = full(park_name or ''), full(rec_name or '')
    if not a or not b: return False
    if a == b: return True
    return bool(bare_name(park_name)) and bare_name(park_name) == bare_name(rec_name) and bool(kinds(a) & kinds(b))


# W-G13 (grade of #380 batch 16, 25 Nov 2026, US-4518 Finger Lakes National Forest: POTA's link is a NY DEC page, so the link
# said STATE and the Forest Service's own record of the forest was sent to check): a park whose OWN name says it is a national
# unit (the official sources settle the agency: a national forest is the Forest Service's land) is the federal land, whatever the
# link names; the link is only a link. Only when the link names a NON-federal agency (a federal link is still compared agency
# by agency), and only for a FEDERAL record carrying the park's own name (same_park_name).
FED_UNIT = re.compile(r'\bnational (forest|grassland|wildlife refuge|park|monument|recreation area|seashore|lakeshore|preserve|'
                      r'historical park|historic site|battlefield|military park|memorial|wild and scenic river|scenic riverway)s?\s*$', re.I)   # the park's KIND (its name ends with it)


def agency_check(fact, rec, st='', table=None):
    """'agrees' | 'differs' | 'no data'.
    W-G11: a state link agrees with a national-list record the STATE OWNS, whatever its manager label says (Oregon: state park
    land labelled 'CITY'; a state reservation run by a private operator). W-G12: a state link against a record of the Corps of
    Engineers, Reclamation or TVA gives NO agency vote when the record carries the park's own name (the state runs the park on
    the federal agency's lake land); any other name still differs."""
    a, b = link_agency(fact, st), record_agency(rec, table)
    if a is None or b is None: return 'no data'
    pn = (fact or {}).get('name') or ''
    if a not in FEDERAL and not str(a).startswith('FED:') and (b in FEDERAL or str(b).startswith('FED:')) and FED_UNIT.search(pn) and same_park_name(pn, (rec or {}).get('Unit_Nm')):
        return 'agrees'   # W-G13: the park's own name says it is a national unit; the record is that federal land
    if a == 'FED': return 'agrees' if (b in FEDERAL or b.startswith('FED:')) else 'differs'
    if a == 'STATE':
        if b == 'STATE' or owner_family(rec) == 'STATE': return 'agrees'
        if b in RESERVOIR_OWNERS and same_park_name((fact or {}).get('name'), (rec or {}).get('Unit_Nm')): return 'no data'
        return 'differs'
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
        _LOOSE_NAMES.clear(); _LOOSE_NAMES[key] = hit   # keep only the newest set (pass_state builds a new one per park)
    return loose(r) in hit[2]


_LOOSE_NAMES = {}


def reason_of(w):
    """'agency', 'kind', 'place', 'name', 'id', 'size', or 'no data: agency' / 'no data: kind' / 'no data: record' / 'no data: place'."""
    head, _, rest = w.partition(':')
    if head != 'no data': return head
    rest = rest.strip()
    return 'no data: ' + ('record' if rest.startswith('the record') else rest.split(' ')[0])


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
    if plev == 'STAT' and record_agency(recs.get(i)) in RESERVOIR_OWNERS and same_park_name(park_name, q[1]): return False   # W-G12: the state's park on federal lake land
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


# 23 Nov 2026 (owner 8:45 AM "Go", rule W8; outside agent's job 4: 1,798 place rows, most of them the park's own pieces): a record
# named "<the park's own name> - <a short label of one piece>" ('Bullard Creek WMA - Montgomery Tract', 'Sand Creek Fishery
# Area-Polk', 'Cooper Lake State Park - Johns Creek Unit') is the park's own piece; so is a record carrying ONE PART of a
# two-part park name of the same kind ('Northern Highland State Forest' for the Northern Highland American Legion State Forest).
PIECE_SEP = re.compile(r'\s+[-\u2013\u2014]+\s*|(?<=[A-Za-z.)])[-\u2013\u2014](?=\s*[A-Za-z0-9])|\s*,\s+|\s*\(')
PIECE_TAIL = re.compile(r'\b(units?|tracts?|additions?|annex|phase|sections?|parcels?|count(?:y|ies)|parish)\b', re.I)
PART_SPLIT = re.compile(r'\s+(?:and|&)\s+|\s*/\s*')


def own_piece(rec_name, name):
    """W8: True when the record is one piece of the park NAME (the park's POTA name, or a record that holds the pin).
    (a) the record's name, cut at its first separator ( - , ( ), starts with a name that is the same park's (same_bare: the
        same bare name and a kind that fits) and the rest is a short label: at most two words, or any words that hold a piece
        word (Unit, Tract, Addition, Annex, Phase, Section, Parcel, County, Parish);
    (b) the record's bare name is one part of the park's own two-part bare name: split at 'and' / '&' / '/', or the first or
        last words of it, at least two words and 8 letters, the two names of the SAME kind (both named, both alike).
    Never: a record that only shares a word, a longer name that holds the park's ('Crow Wing River' for Crow Wing State
    Park), another kind of place ('X State Recreation Area' for X State Forest)."""
    rec, name = str(rec_name or ''), str(name or '')
    if not rec or not name: return False
    bits = PIECE_SEP.split(rec, maxsplit=1)
    if len(bits) == 2:
        lead, tail = bits[0].strip(), bits[1].strip(' )')
        words = re.findall(r"[A-Za-z0-9'.]+", tail)
        if lead and words and (len(words) <= 2 or PIECE_TAIL.search(tail)) and same_bare(lead, name):
            return True
    kr, kn = kinds(full(rec)), kinds(full(name))
    if not kr or kr != kn: return False
    rb, nb = bare_name(rec).split(), bare_name(name).split()
    if not rb or len(rb) >= len(nb): return False
    joined = ' '.join(rb)
    parts = [x.strip() for x in PART_SPLIT.split(bare_name(name)) if x.strip()]
    if len(parts) > 1 and joined in parts and len(joined) >= 4: return True
    return len(rb) >= 2 and len(joined) >= 8 and (nb[:len(rb)] == rb or nb[-len(rb):] == rb)


def all_parcels_ok(park_name, names):
    """23 Nov 2026 (owner 9:20 AM, job 7: 'All parcels inside the park'; switch KPC_SAVED_ALL_PARCELS): a saved answer whose
    fingerprint fits SEVERAL records (look-alike 40-acre survey parcels) joins them all, but only when every one of them carries
    the park's own name (same_bare with POTA's name, or W8's own_piece: 'X Wildlife Area-Columbia'): then each is a parcel of this park's land. Fewer than two, or any other
    name: as before (the first one joins and it is said)."""
    names = [n for n in names or [] if n]
    return len(names) >= 2 and bool(park_name) and all(same_bare(n, park_name) or own_piece(n, park_name) for n in names)


# 23 Nov 2026 (owner 2:55 PM "Go ahead with the safer version", rule W8b; the outside agent's accuracy test of W8 on the 1,798
# job-4 rows: W8 cleared 756 rows, 19 of them another place). W8's name test alone kept water bodies, roads and businesses named
# like the park, and a same-name area of another county. A same-name record is the park's own piece only with ALL three:
# (1) the park's exact name or another spelling / short form, plus at most a unit / county / section ending; (2) the same agency
# or owner type as the park; (3) it touches or lies within NEAR_KM of the park's other joined land. One narrow case besides:
# a POTA name made of two units ('A B C D State Forest', 'A B and C D State Forest'): a record named exactly the one half, of the
# same kind and agency, while a record holding the pin is named the other half.
W8B_KIND_WORDS = {'state', 'park', 'area', 'recreation', 'forest', 'wildlife', 'management', 'wma', 'swa', 'sna', 'nap', 'ca', 'shp',
                  'sra', 'sp', 'sf', 'natural', 'conservation', 'fish', 'fishery', 'and', 'preserve', 'reserve', 'nature', 'historic',
                  'historical', 'site', 'reservation', 'game', 'lands', 'land', 'public', 'access', 'stl', 'refuge', 'national'}
W8B_TAIL = re.compile(r'^(?:(?:north|south|east|west|ne|nw|se|sw|upper|lower|[0-9ivx]+)\s+)*(?:units?|tracts?|additions?|annex|'
                      r'sections?|parcels?|phase|count(?:y|ies)|parish)?(?:\s+[0-9ivx]+)?$')
W8B_TAIL_END = re.compile(r'(.*?)\s+((?:north|south|east|west)\s+)?(units?|tracts?|additions?|annex|sections?|parcels?)(\s+[0-9ivx]+)?$', re.I)
W8B_PIECE_WORD = re.compile(r'\b(unit|tract|addition|annex|section|parcel|county|parish)\b')
W8B_FEATURES = (('road', r'\b(road|rd|drive|dr|highway|hwy|parkway|pkwy|street|st|avenue|ave|lane|boulevard|blvd|right of way|row|trail corridor|rail)\b'),
                ('water', r'\b(river|stream|creek|brook|run|branch|canal|ditch|pond|lake|reservoir|lagoon|bay|harbor|marina|dam|spillway|boat ramp|landing)\b'),
                ('business', r'\b(resort|inc|llc|company|co|corp|club|golf|country club|campground|marina|motel|hotel|lodge|store|ranch|farm)\b'),
                ('hoa', r'\b(hoa|homeowners?|association|estates|subdivision|condo|condominium|village green)\b'),
                ('cemetery', r'\b(cemetery|cemeteries|burial|memorial gardens)\b'),
                ('school', r'\b(school|elementary|college|university|academy|campus)\b'),
                ('utility', r'\b(substation|utility|sewer|water works|treatment plant|easement|transmission)\b'))
W8B_LAND_END = re.compile(r'\b(units?|tracts?|additions?|annex|sections?|parcels?|area|wma|swa|sna|park|forest|preserve|refuge|reserve|access|zone)\b(\s+[0-9ivx]+)?$')


def feature_of(name, park_name=''):
    """W8b: the kind of non-park feature a name says it is ('road', 'water', 'business', 'hoa', 'cemetery', 'school', 'utility'),
    or None. A word the park's own name carries says nothing; a road or water word followed by a land word ('Hurricane Creek
    Addition', 'Cobb Lake Unit') is a piece of land named after it."""
    r, p = full(re.sub(r'[()]', ' ', str(name or ''))), full(park_name)   # words in brackets count here ('X Area (Y Lake)')
    for k, rx in W8B_FEATURES:
        for m_ in re.finditer(rx, r):
            w = m_.group(0)
            if re.search(r'\b' + re.escape(w) + r'\b', p): continue
            rest = r[m_.end():]
            if k in ('road', 'water') and rest.strip() and W8B_LAND_END.search(rest): continue
            return k
    return None


def _core_words(name): return [w for w in full(re.sub(r'[()]', ' ', str(name or ''))).split() if w not in W8B_KIND_WORDS]



def same_name_piece(rec_name, name, counties=()):
    """W8b (1): the record carries the park NAME (the park's POTA name or a pin record's): the same full name or bare name (a
    kind that fits) followed only by a unit / tract / addition / section / parcel / county ending or the name of one of the
    state's counties (counties = full() county names, 'county' left out); or the same name in another spelling or short form
    (the same words once kind words and short forms are left out, words in brackets kept: 'X SHP' for X State Historical
    Park, 'X Access' for X State Recreation Area; never 'X State Recreation Area (Y Lake)' for X State Forest)."""
    rec, name = str(rec_name or ''), str(name or '')
    if not rec or not name: return False
    cr = _core_words(rec)
    if cr and cr == _core_words(name): return True
    bits = PIECE_SEP.split(rec, maxsplit=1)
    if len(bits) == 2: lead, tail = bits[0].strip(), bits[1].strip(' )')
    else:
        m_ = W8B_TAIL_END.match(rec)
        if not m_: return False
        lead, tail = m_.group(1), rec[len(m_.group(1)):].strip()
    t = full(tail)
    t2 = re.sub(r'\b(county|counties|parish|unit|units)\b', '', t).strip()
    cs = set(counties or ())
    ok = (bool(W8B_TAIL.match(t)) and t != '') or t2 in cs or (t2 != '' and all(w in cs or w == 'and' for w in t2.split()))
    if not ok and W8B_PIECE_WORD.search(t): ok = len(t.split()) <= 4 and not feature_of(tail)
    if not ok: return False
    if full(lead) == full(name): return True
    bl, kl = bare_name(lead), kinds(full(lead))
    return bool(bl) and bl == bare_name(name) and (not kl or bool(kl & kinds(full(name))))


TWO_UNIT_SPLIT = re.compile(r'\s+(?:and|&)\s+|\s*[-\u2013\u2014/]\s*')


def two_unit_half(rec_name, park_name, held_names):
    """W8b (E): the POTA name covers two units ('A B C D State Forest'; also joined by 'and' / '&' / '-'): True when the record
    is named exactly the one half (same kind of place as the park) and a record that holds the pin is named the other half."""
    rec, park = str(rec_name or ''), str(park_name or '')
    if not rec or not park or kinds(full(rec)) != kinds(full(park)) or not kinds(full(park)): return False
    rb = bare_name(rec)
    pb = ' '.join(x for x in TWO_UNIT_SPLIT.split(bare_name(park)) if x)
    if not rb or rb == pb: return False
    if pb.startswith(rb + ' '): rest = pb[len(rb):].strip()
    elif pb.endswith(' ' + rb): rest = pb[:-len(rb)].strip()
    else: return False
    rest = ' '.join(x for x in TWO_UNIT_SPLIT.split(rest) if x and x not in ('and', '&'))
    return bool(rest) and any(bare_name(h) == rest for h in held_names or [])


def pin_3c(q, rows, holds, park_name='', held=None, same_owner=None, near_land=None, counties=()):
    """holds(record id) -> True / False / None (POTA's pin strictly inside the record). True = flag q.
    22 Nov 2026: a record that does not hold the pin stays when its bare name is the bare name of a record that holds it, or
    of the park's own POTA name, or differs from one only by piece words (same_bare). held = the rows that hold the pin, when
    the caller already has them (22 Nov 2026, speed: worked out once per park, not once per row).
    W8b (23 Nov 2026, replaces W8's name-only own_piece here): a same-name piece (same_name_piece) that names no road, water
    body, business, HOA, cemetery, school or utility the park's own name does not carry (feature_of) stays only when
    same_owner(q) is True AND near_land(q) is True; a two-unit half (two_unit_half) stays when same_owner(q) is True.
    same_owner / near_land missing or not True (no data) = the check list, as before W8."""
    if holds(str(q[0])) is not False: return False
    held = [x for x in rows if holds(str(x[0])) is True] if held is None else held
    if not held: return False                                   # no record holds the pin: says nothing about this one
    me = full(q[1])
    if any(full(x[1]) == me for x in held): return False
    names = [x[1] for x in held] + ([park_name] if park_name else [])
    if any(same_bare(q[1], n) for n in names): return False
    owner_ok = bool(same_owner) and same_owner(q) is True
    if owner_ok and park_name and two_unit_half(q[1], park_name, [x[1] for x in held]): return False
    if owner_ok and not feature_of(q[1], park_name) and any(same_name_piece(q[1], n, counties) for n in names) \
            and bool(near_land) and near_land(q) is True:
        return False                                            # W8b: the park's own piece (name, owner and place agree)
    return True


def rings_near(ra, rb, km=None):
    """W8b (3): True when two shapes (lists of [lon, lat] rings) touch, overlap or come within km (NEAR_KM) of each other;
    None when either has no shape. Up to ~120 points of each ring are tested (the keys read a rough working copy)."""
    km = NEAR_KM if km is None else km
    ra = [r for r in ra or [] if len(r) >= 3]; rb = [r for r in rb or [] if len(r) >= 3]
    if not ra or not rb: return None
    def box_(rr):
        xs = [p[0] for r in rr for p in r]; ys = [p[1] for r in rr for p in r]
        return min(xs), min(ys), max(xs), max(ys)
    A, B = box_(ra), box_(rb)
    pad = km / 80.0
    if A[0] > B[2] + pad or B[0] > A[2] + pad or A[1] > B[3] + pad or B[1] > A[3] + pad: return False
    def in_r(x, y, r):
        ins, j = False, len(r) - 1
        for i in range(len(r)):
            xi, yi, xj, yj = r[i][0], r[i][1], r[j][0], r[j][1]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi: ins = not ins
            j = i
        return ins
    def near_r(la, lo, rr):
        k = math.cos(math.radians(la)) * 111.32
        for r in rr:
            for (x1, y1), (x2, y2) in zip(r, r[1:]):
                ax, ay, bx, by = (x1 - lo) * k, (y1 - la) * 110.57, (x2 - lo) * k, (y2 - la) * 110.57
                dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
                t = 0 if L == 0 else max(0, min(1, -(ax * dx + ay * dy) / L))
                if math.hypot(ax + t * dx, ay + t * dy) <= km: return True
        return False
    for x in ra:
        for (lo, la) in x[::max(1, len(x) // 120)]:
            if any(in_r(lo, la, y) for y in rb) or near_r(la, lo, rb): return True
    for y in rb:
        for (lo, la) in y[::max(1, len(y) // 120)]:
            if any(in_r(lo, la, x) for x in ra): return True
    return False


def _fam_same(p, r):
    """W8b (2): the park's agency family p against a record's r: True / False / None (no data)."""
    if p is None or r is None: return None
    if p == r: return True
    fed = lambda z: 'FED' if z.startswith('FED') or z in FED_AGENCIES else z
    if p == 'FED' or r == 'FED': return fed(p) == fed(r)
    return False


def reason_of(w):
    return w.partition(':')[0]


def outline_size(p, m):
    """The joined outline's size for the size vote. 23 Nov (owner 'Yes', audit 3 S5): the key's measured 'ac' (the union of
    the records), or the one row's own acres; several rows with no measured 'ac' give NO vote (None), because adding them up
    counts land two layers both hold twice."""
    if p.get('ac'): return p['ac']
    twins = {str(t) for t in p.get('twin') or []}
    rows = [q for q in m if str(q[0]) not in twins]
    return float(rows[0][2] or 0) if len(rows) == 1 else None


def pass_state(parks, recs, facts, place_fn, url_of=lambda a: '', is_no=lambda ref, rid, a: False, skip=(), st='',
               units=None, hits=None, holds_fn=None, layer_table=None, page_holds_fn=None, near_fn=None,
               blocked_ids=None, auto_confirm_stops=None, spelling_table=None, size_hold=False):
    """The whole pass for one state, shared by the US builder and the offline counter (one implementation).
    parks = the key's park rows (changed in place); recs = {record id: record}; place_fn(ref, [record ids]) -> True / False /
    None (pin inside or near; used to join a record by the park's link id); holds_fn(ref, record id) -> True / False / None
    (POTA's pin strictly inside that record; pin 3c); layer_table = load_layer_table() (each layer's owner); is_no(ref, rid, rec) = a person's saved NO; skip = parks never touched
    here (official trail lines). Every joined park gets park['match'] = {'status': 'confirmed' | 'outlined' | 'pin',
    'why': [reasons], 'notes': [advisory], 'by': 'id' | 'size' | 'link'} (pin = no outline; 'by' only when confirmed).
    near_fn(ref, record id, [record ids]) -> True / False / None: the record touches or lies within NEAR_KM of those records
    (W8b; missing = no data, the same-name piece stays on the check list).
    size_hold (24 Nov, switch KPC_CONFIRM_SIZE_HOLD, default off): if True, an auto-confirm whose outline acres are far off the official acres is left outlined and flagged. Off = still confirmed, still flagged in the report.\n    Returns counts and appends [park, what, record id] to hits."""
    hits = [] if hits is None else hits
    near_fn = near_fn or (lambda ref, i, ids: None)
    counties = set()    # W8b: the state's county names, from the park pages
    for _v in facts.values():
        _pg = (_v or {}).get('page') or {}
        if st and str((_v or {}).get('area', ''))[-2:] != st: continue
        for _c in list(_pg.get('counties') or []) + [(_x or {}).get('name', '') for _x in _pg.get('county_areas') or []]:
            _t = full(_c).replace(' county', '').strip()
            if _t: counties.add(_t)
    holds_fn = holds_fn or (lambda ref, i: None)
    if spelling_table is None:
        spelling_table, _ = load_spelling_table()
    if auto_confirm_stops is None:
        auto_confirm_stops, _ = load_auto_confirm_stops()
    blocked_ids = blocked_ids or {}
    shared = shared_names(facts)
    names_n = None       # W5: how many records of the state carry each name (made when the first map-link name comes up)
    rids = {i: ids_from(a, url_of(a)) for i, a in recs.items()}
    index = {}
    for i, d in rids.items():
        for k, v in d.items(): index.setdefault((k, v), []).append(i)
    names = {}
    for ref, p in parks.items(): names.setdefault(full(p.get('n') or ''), set()).add(ref)
    out = {'parks': 0, 'confirmed': 0, 'outlined': 0, 'pin': 0, 'gained': 0, 'moved': 0, 'why': {}, 'notes': {},
           'by_id': 0, 'by_link': 0, 'by_size': 0, 'second_name': 0, 'tract': 0, 'parent': 0, 'shared_record': 0,
           'second_name_near': {w: 0 for w, _k in NEAR_MISS_KM}}

    ref_of = {id(p_): r_ for r_, p_ in parks.items()}

    def to_check(p, rows, why):
        ids_ = {id(q) for q in rows}
        p['m'] = [q for q in p.get('m') or [] if id(q) not in ids_]
        r_ = ref_of.get(id(p))
        if r_:   # A2: a park whose row went to the check list no longer holds that record
            still = {str(q[0]) for q in p['m']}
            for q in rows:
                if str(q[0]) not in still and str(q[0]) in held_by: held_by[str(q[0])].discard(r_)
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

    def add_row(p, i, how, ref_=None):
        a = recs[i]
        p['m'] = sorted(list(p.get('m') or []) + [[a['OBJECTID'], rec_name(a), round(float(a.get('GIS_Acres') or 0)), how]],
                        key=lambda x: -(x[2] or 0))
        p['c'] = [x for x in p.get('c') or [] if str(x[0]) != i]
        if p.get('g') in (None, 'pin'): p['g'] = 'official'
        if ref_: held_by.setdefault(str(i), set()).add(ref_)   # A2: the gained record is held by this park too

    held_by = {}
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

    # 24 Nov 2026 (owner t2067u): who holds each record (A2), and A3 bracket twins cut to their own tracts
    for r_, p_ in parks.items():
        if r_ in skip: continue
        for q in p_.get('m') or []: held_by.setdefault(str(q[0]), set()).add(r_)
    for r_, i_, k_, n_ in split_bracket_twins(parks, recs, facts, skip, held_by):
        out['bracket_split'] = out.get('bracket_split', 0) + 1; hits.append([r_, 'own tracts (A3)', i_])

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
                    held_by.setdefault(str(i), set()).add(ref)
                    out['gained'] += 1; hits.append([ref, 'joined (id)', i])
                if p.get('g') in (None, 'pin'): p['g'] = 'official'
        # P2 (rule sheet PN): a second name from the park's own agency page joins a record of exactly that name that holds the pin
        have = {str(q[0]) for q in p.get('m') or []} | {str(q[0]) for q in p.get('c') or []}
        for n2 in second_names(f, nm, heading_count, all_names - {full(nm)}):
            pre = [i for i in by_name.get(n2, []) if i not in have and not is_no(ref, i, recs[i])
                   and agency_check(f, recs[i], st, layer_table) != 'differs']
            pin_ = (f or {}).get('pin') or []
            cand = [i for i in pre if holds_fn(ref, i) is True and not on_edge(pin_, recs[i])]   # PN-G2: strictly inside
            if not cand and len(pre) == 1:   # report only: the one record of that name, missed only because the pin is outside it
                d = km_to_record(pin_[0], pin_[1], recs[pre[0]]) if len(pin_) == 2 else None
                for w, k_ in NEAR_MISS_KM:
                    if d is not None and d <= k_: out['second_name_near'][w] += 1
            if len(cand) == 1:
                add_row(p, cand[0], f'name: second name "{n2[:60]}" (the park\'s own page) + pin inside', ref)
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
                add_row(p, i, f'name: tract "{rn[:60]}" (the park\'s own page lists it)', ref)
                out['gained'] += 1; out['tract'] += 1; hits.append([ref, 'joined (tract)', i]); have.add(i)
        m = list(p.get('m') or [])
        if not m: continue
        out['parks'] += 1
        held = {}
        # 22 Nov 2026 (speed, same answers): really remembered now (setdefault worked holds_fn out on every call)
        holds = lambda i: held[i] if i in held else held.setdefault(i, holds_fn(ref, i))
        held_rows = []
        anchor = []          # W8b: the rows the place test leaves alone on name (22 Nov rule): the park's other joined land
        fam_ = []

        def park_fam():
            if not fam_:
                a_ = link_agency(f, st)
                if a_ is None:
                    fs_ = [record_agency(recs.get(str(x[0])), layer_table) or owner_family(recs.get(str(x[0]))) for x in (anchor[0] if anchor else [])]
                    fs_ = [z for z in fs_ if z]
                    a_ = max(sorted(set(fs_)), key=fs_.count) if fs_ else None
                fam_.append(a_)
            return fam_[0]
        # 22 Nov 2026 (owner: "more options to match other than name"): a point on the park's own official page inside a record
        page_in = {}
        on_page = lambda i: page_in[i] if i in page_in else page_in.setdefault(i, (page_holds_fn(ref, i) is True) if page_holds_fn else False)
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
            if not held_rows: held_rows.append([x for x in m if holds(str(x[0])) is True])
            if not anchor: anchor.append([x for x in m if not pin_3c(x, m, holds, nm, held_rows[0])])   # W8b: the park's other land
            if pin_3c(q, m, holds, nm, held_rows[0], same_owner=lambda x: _fam_same(park_fam(), record_agency(recs.get(str(x[0])), layer_table) or owner_family(recs.get(str(x[0])))),
                      near_land=lambda x: near_fn(ref, str(x[0]), [str(y[0]) for y in anchor[0] if y is not x]), counties=counties):
                if on_page(i): out['kept_by_page_point'] = out.get('kept_by_page_point', 0) + 1; continue   # the park's own page puts it here
                drop.append((q, "place: POTA's pin is in another of the park's records, none of this record's name")); continue
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
        mnames = map_link_names(f)
        # audit 1 MUST 2 (owner 23 Nov 2026 5:43 PM 'Yes'): the map link, county and town rules move only plain name joins that
        # no id backs up; a row a person joined or checked, or one an official id ties, is never sent to the check list here
        movable = lambda q: row_class(q) == 'name' and not id_agrees(kind, val, rids.get(str(q[0])) or {}, recs.get(str(q[0])), tie)
        if mnames and names_n is None:
            names_n = {}
            for a_ in recs.values(): names_n[bare_name(rec_name(a_))] = names_n.get(bare_name(rec_name(a_)), 0) + 1
        if mnames and left and not any(bare_name(q[1]) in mnames for q in left):
            if not id_ok and sv[0] != 'agrees' and any(names_n.get(n) for n in mnames) and any(movable(q) for q in left):
                # W-G10 (owner 23 Nov 2026 5:01 AM, 'yes'): the park's own page links the agency's map under ANOTHER record's
                # name (a record of the state carries the map's name; none of the park's joined records does) and neither an
                # id nor the agency's size speaks for the joined records: they go to the check list, as when an id disagrees
                # (a same-name unit of another county: the map says 'Mud Lake Wildlife Area-Columbia', the key joined '-Door')
                rows_ = [q for q in left if movable(q)]
                to_check(p, rows_, "map link: the park's own page links the agency's map under another record's name")
                why.append('map link'); hits.extend([ref, 'map link', str(q[0])] for q in rows_)
                out['moved'] += len(rows_); out['map_link_moved'] = out.get('map_link_moved', 0) + 1
                left = p.get('m') or []
            else:
                # no record of the state carries the map's name (a spelling, a cut-off value), or an id or the size speaks
                # for the joined record: a note for a person, nothing moves
                notes.append("the page's map link names another record")
                out['map_link_other'] = out.get('map_link_other', 0) + 1
        careas = county_areas_of(f)
        if careas and left and not id_ok and sv[0] != 'agrees':
            # W6 / W-G8 (owner 23 Nov 2026, 'yes'): the park's own page names its county, and a joined record lies well
            # outside it (the same name in another part of the state): that record goes to the check list. Not when an id
            # or the agency's own size speaks for the joined records.
            # 24 Nov 2026 (owner approved E, 5:39 AM CT): the county rule does not remove land that holds POTA's pin.
            # The distance test itself is unchanged (max(25 km, 2 x county radius)).
            far_all = [q for q in left if movable(q) and outside_counties(recs.get(str(q[0])), careas)]
            belt = [q for q in far_all if holds(str(q[0])) is True]
            if belt:
                out['county_belt'] = out.get('county_belt', 0) + len(belt)
            far_ = [q for q in far_all if holds(str(q[0])) is not True]
            if far_:
                cn_ = ' / '.join(c[0] for c in careas)[:60]
                to_check(p, far_, f"county: the park's own page names {cn_} County; this land lies outside it")
                why.append('county'); hits.extend([ref, 'county', str(q[0])] for q in far_)
                out['moved'] += len(far_); out['county_moved'] = out.get('county_moved', 0) + len(far_)
                left = p.get('m') or []
        npts = near_points_of(f)
        if npts and left and not id_ok and sv[0] != 'agrees':
            # W-G6 (owner 23 Nov 2026 6:37 AM, 'yes'): the park's own page puts the park near a town ('2 miles east of X'), and
            # ALL its joined land lies far from there (the same name somewhere else): those records go to the check list. Not
            # when an id or the agency's own size speaks for the joined records; never a record holding POTA's pin; and not
            # when any joined record reaches the town's circle (a park of many pieces: the far ones are its own pieces, W8).
            votes_ = {str(q[0]): near_town_vote(recs.get(str(q[0])), npts) for q in left}
            right_ = any(v == 'inside' for v in votes_.values()) or any(holds(str(q[0])) is True for q in left)
            # 23 Nov 3 PM (the owner's 'did you make it worse' check: one park, confirmed by its link, lost its land to a town
            # line 36 km off): a town point is approximate. It never moves land POTA's pin lies in or by, nor land inside a
            # county the same page names; those are the better witnesses.
            if not right_ and place_fn(ref, [str(q[0]) for q in left]) is True:
                right_ = True
            if not right_ and careas and not any(outside_counties(recs.get(str(q[0])), careas) for q in left):
                right_ = True
            far_ = [] if right_ else [q for q in left if movable(q) and votes_[str(q[0])] == 'far']
            if far_:
                fr_ = npts[0][3][:60]
                to_check(p, far_, f"town: the park's own page puts it {fr_}; this land lies far from there")
                why.append('town'); hits.extend([ref, 'town', str(q[0])] for q in far_)
                out['moved'] += len(far_); out['town_moved'] = out.get('town_moved', 0) + len(far_)
                left = p.get('m') or []
        if link_nm == 'part': notes.append('link name')
        place_ok = bool(left) and place_fn(ref, [str(q[0]) for q in left]) is True
        how = None
        if not left:
            p['g'] = 'pin'; st_ = 'pin'
        else:
            if id_ok: st_, how = 'confirmed', 'id'
            elif sv[0] == 'agrees': st_, how = 'confirmed', 'size'
            elif link_nm == 'strong' and place_ok: st_, how = 'confirmed', 'link'
            elif link_nm in ('strong', 'part') and any(on_page(str(q[0])) for q in left): st_, how = 'confirmed', 'page point'
            # W4 (23 Nov 2026): the park's own official page carries its name, and POTA's pin lies in the joined record (or,
            # W-G1 with the page's name as the name that agrees, the page's own point does). Confirms only: nothing is moved.
            elif page_name_agrees(f) and place_ok: st_, how = 'confirmed', 'page name'
            elif page_name_agrees(f) and any(on_page(str(q[0])) for q in left): st_, how = 'confirmed', 'page name and point'
            # W5 (23 Nov 2026): the park's own page links the agency's own map under this record's name, and exactly ONE
            # record of the state carries that bare name (two records of one name: unsure, nothing). Confirms only.
            elif mnames and any(bare_name(q[1]) in mnames and names_n.get(bare_name(q[1])) == 1 for q in left): st_, how = 'confirmed', 'map link name'
            # W-G6 (23 Nov 2026): a name that agrees (the link's or the park's own page's) and the joined land reaches into the
            # circle of the 'near a town' point the park's own page gives. Confirms only: nothing is moved.
            elif (link_nm in ('strong', 'part') or page_name_agrees(f)) and npts and any(
                    near_town_vote(recs.get(str(q[0])), npts) == 'inside' for q in left): st_, how = 'confirmed', 'near a town'
            else: st_ = 'outlined'
            # 24 Nov 2026 7:06 AM CT: status-only auto-confirm (never changes land).
            if st_ == 'outlined' and auto_confirm_ok(
                    ref, p, recs, facts, holds_fn=lambda _r, i: holds(i), is_no=is_no,
                    blocked=blocked_ids, stop_parks=auto_confirm_stops,
                    spelling=spelling_table, pin=(facts.get(ref) or {}).get('pin'), layer_table=layer_table,
                    shared_by=held_by, st=st):
                st_, how = 'confirmed', 'held name and pin'
            # 24 Nov 2026 (owner: "Page reader whole reason is to read names!!"; review: the same gate as auto-confirm): the park's
            # own official page calls it by the HELD record's own name, with the same stops and the same 100 m on the saved outline.
            elif st_ == 'outlined' and auto_confirm_ok(
                    ref, p, recs, facts, holds_fn=lambda _r, i: holds(i), is_no=is_no,
                    blocked=blocked_ids, stop_parks=auto_confirm_stops, pin=(facts.get(ref) or {}).get('pin'), layer_table=layer_table,
                    shared_by=held_by, st=st, name_test=lambda pn, rn: page_names_land(f, pn, rn, heading_count, all_names - {full(pn)})):
                st_, how = 'confirmed', 'page names the land'
        ev, name_how = None, ''
        if st_ == 'confirmed' and how:
            pin_ = (facts.get(ref) or {}).get('pin')
            hid = evidence_id_of(p) or held_id_for_pass(ref, p, recs, pin_, lambda _r, i: holds(i))   # 26 Nov: finding 6
            ev = confirm_evidence(ref, p, recs, facts, hid, pin=pin_)
            if how == 'held name and pin':
                rec_ = recs.get(hid) or recs.get(str(hid or '')) or {}
                pn_ = p.get('n') or (facts.get(ref) or {}).get('name') or ''
                name_how = held_name_how(pn_, rec_name(rec_), spelling_table)
            if ev.get('size_flag'):
                out['size_far_confirms'] = out.get('size_far_confirms', 0) + 1
                out.setdefault('size_far_ids', []).append(ref)
                if size_hold and how in ('held name and pin', 'page names the land'):
                    st_, how = 'outlined', None
                    out['size_hold'] = out.get('size_hold', 0) + 1
        p['match'] = {'status': st_, 'why': sorted(set(why))}
        if notes: p['match']['notes'] = sorted(set(notes))
        if how: p['match']['by'] = how
        if ev: p['match']['evidence'] = ev
        if name_how: p['match']['name_how'] = name_how
        if ev and ev.get('size_flag') and size_hold and st_ == 'outlined':
            p['match']['size_hold'] = True
        if id_ok: p['match']['id'] = f'{kind} {val}'
        if link_nm == 'strong': p['match']['link'] = 'strong'
        out[st_] += 1
        if how:
            out['by_' + how] = out.get('by_' + how, 0) + 1
            if name_how:
                out['by_name_' + name_how] = out.get('by_name_' + name_how, 0) + 1
        for w in set(why): out['why'][w] = out['why'].get(w, 0) + 1
        for w in set(notes): out['notes'][w] = out['notes'].get(w, 0) + 1
    return out



def size_once(p, m, box_of, layer_of=lambda rid: None, same=0.8):
    """The joined outline's size with the same land counted once (23 Nov review of #363: Canada often holds one piece in
    2 or 3 layers, CPCAD plus the province's own). Largest row first; a row whose box lies 80%+ inside a counted row's box of
    ANOTHER layer is the same ground and is not added (the US W7 twin test). The key's measured 'ac' wins when it has one."""
    if p.get('ac'): return p['ac']
    twins = {str(t) for t in p.get('twin') or []}
    kept, tot = [], 0.0
    for q in sorted(m, key=lambda q: -float(q[2] or 0)):
        if str(q[0]) in twins: continue
        bb, ly = box_of(str(q[0])), layer_of(str(q[0]))
        if bb:
            def share(a, b):
                w = max(0.0, min(a[2], b[2]) - max(a[0], b[0])); h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
                return w * h / (min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1])) or 1e-12)
            if any(ly != l2 and share(bb, b2) >= same for l2, b2 in kept): continue
            kept.append((ly, bb))
        tot += float(q[2] or 0)
    return tot


def canada_pass(parks, recs, facts, place_fn, page_holds_fn=None, size_of=None):
    """Job 8 (owner 23 Nov 2026 2:12 PM, approving the outside agent's count; 4:43 PM 'Do it'): the US proofs on the Canada key.
    Canada joins by name alone; these proofs confirm a joined park, the same way and with the same words as the US pass:
    the agency's own size (size), POTA's link naming the park with the pin in or by the land (link), the link naming it and a
    point on the park's own page inside the land (page point), the park's own page carrying its name with the pin in or by the
    land (page name), or with a page point inside it (page name and point). The size check is the one that MOVES: name-joined
    rows whose outline is 3 times off the agency's own figure go to the check list (the US rule). Nothing else changes: no
    agency, place, national or other-name check runs here (not counted, not approved for Canada).
    parks = one province's key rows (changed in place); recs = {record id: record with Unit_Nm, GIS_Acres, _g}."""
    shared = shared_names(facts)
    out = {'confirmed': 0, 'outlined': 0, 'pin': 0, 'moved': 0, 'why': {}}
    for ref, p in parks.items():
        m = p.get('m') or []
        if not m:
            continue
        f = facts.get(ref) or {}
        why = []
        name_left = [q for q in m if row_class(q) == 'name']
        sv = size_vote(size_witnesses(f, shared), (size_of or outline_size)(p, m))
        if name_left and sv[0] == 'far off':
            ids_ = {id(q) for q in name_left}
            p['m'] = [q for q in m if id(q) not in ids_]
            p['c'] = [list(q[:3]) + [f"check (size: the outline is {sv[1]} times the agency's own figure)"] for q in name_left] + list(p.get('c') or [])
            why.append('size'); out['moved'] += len(name_left)
        left = p.get('m') or []
        if not left:
            st_, how = 'pin', None
        else:
            place_ok = place_fn(ref, [str(q[0]) for q in left]) is True
            on_page = lambda i: bool(page_holds_fn and page_holds_fn(ref, i) is True)
            link_nm = link_name_agree(f)
            how = None
            if sv[0] == 'agrees': how = 'size'
            elif link_nm == 'strong' and place_ok: how = 'link'
            elif link_nm in ('strong', 'part') and any(on_page(str(q[0])) for q in left): how = 'page point'
            elif page_name_agrees(f) and place_ok: how = 'page name'
            elif page_name_agrees(f) and any(on_page(str(q[0])) for q in left): how = 'page name and point'
            st_ = 'confirmed' if how else 'outlined'
        p['match'] = {'status': st_, 'why': sorted(set(why))}
        if how: p['match']['by'] = how
        out[st_] += 1
        if how: out['by_' + how] = out.get('by_' + how, 0) + 1
        for w in why: out['why'][w] = out['why'].get(w, 0) + 1
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
