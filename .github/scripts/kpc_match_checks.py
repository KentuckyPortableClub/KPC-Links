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
    rows = [f.get('size')] + list(((f.get('page') or {}).get('sizes') or []))
    for s in rows:
        if not tagged_witness(s): continue
        try: ac = float(s.get('acres'))
        except (TypeError, ValueError): continue
        if ac > 0: out.append((ac, s.get('witness'), 'tagged independent witness'))
    return out


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


def record_agency(rec, table=None):
    """Who owns a record, never from its name: PAD-US records by their own Mang_Name / Mang_Type; every other layer by the
    club's layer table (load_layer_table). None = not known (also: no table, or a layer the table does not hold)."""
    rec = rec or {}
    oid = str(rec.get('OBJECTID'))
    pre = re.match(r'[a-z]*', oid).group(0)
    if pre:
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


def pin_3c(q, rows, holds):
    """holds(record id) -> True / False / None (POTA's pin strictly inside the record). True = flag q."""
    if holds(str(q[0])) is not False: return False
    held = [x for x in rows if holds(str(x[0])) is True]
    if not held: return False                                   # no record holds the pin: says nothing about this one
    me = full(q[1])
    return not any(full(x[1]) == me for x in held)


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
           'by_id': 0, 'by_link': 0, 'by_size': 0}

    def to_check(p, rows, why):
        ids_ = {id(q) for q in rows}
        p['m'] = [q for q in p.get('m') or [] if id(q) not in ids_]
        p['c'] = [list(q[:3]) + [f'check ({why})'] for q in rows] + list(p.get('c') or [])

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
            if agency_check(f, rec, st, layer_table) == 'differs': drop.append((q, "agency: the record belongs to another agency than POTA's link")); continue
            if national_flag(q, m, recs, nm): drop.append((q, "national: a national-layer record of another level of government than the park's name")); continue
            if pin_3c(q, m, holds): drop.append((q, "place: POTA's pin is in another of the park's records, none of this record's name")); continue
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
