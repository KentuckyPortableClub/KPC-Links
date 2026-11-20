#!/usr/bin/env python3
"""kpc_layer_agency_kind.py: each map layer's owning agency and kind, for the key's agency and kind checks.

Reads the club's layer table (data/us-key/layers.json: id -> [address, name field, description]) plus the key's two national
layers, and writes .github/layer-agency-kind.json: {id: {agency, kind, why}}. Each answer comes from the layer's OWN words
(its description and address) by the fixed rules below. When the words don't say, or say two different things, the answer is
'unknown': nothing is guessed. To change an answer, change the rule (or put the layer in HAND with a reason), never the file.

  python3 .github/scripts/kpc_layer_agency_kind.py           write the file
  python3 .github/scripts/kpc_layer_agency_kind.py --check   exit 1 when the file is out of date with layers.json or the rules
  python3 .github/scripts/kpc_layer_agency_kind.py --selftest
"""
import json, os, re, sys

LAYERS = 'data/us-key/layers.json'
OUT = '.github/layer-agency-kind.json'
NATIONAL = {   # the key's national layers (kpc_us_key.py Q and FWS); not in layers.json
    'PAD-US': ['https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query', 'Unit_Nm',
               'PAD-US, the national protected areas database (many owners and kinds)'],
    'fws': ['https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSInterest_Simplified_Authoritative/FeatureServer/0/query',
            'ORGNAME', 'US Fish and Wildlife Service interest lands (refuges, WPAs)'],
}
# A layer only a person can settle: {id: (agency, kind, why)}. Empty: every answer below comes from the rules.
HAND = {}

STATES = (r'Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|'
          r'Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|'
          r'Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|'
          r'Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|'
          r'Wisconsin|Wyoming')

# (agency, pattern) in order: the first that matches wins. Federal first, then state agencies that run two programs, then one.
AGENCY_RULES = [   # case-sensitive: an agency's name is capitalised ("State Parks"), a kind word often is not ("(state parks)")
    ('many owners (PAD-US)', r'\bPAD-US\b'),
    ('many owners (national list)', r'National Register of Historic Places|nrhp_|National Historic Landmarks|National_Heritage_Areas|'
                                    r'National Heritage Areas'),
    ('FWS', r'US Fish and Wildlife Service|U\.S\. Fish (?:and|&) Wildlife Service|\bFWS(?:Boundaries|Approved|Interest)|'
            r'National_Wildlife_Refuge_System'),
    ('NPS', r'\bNPS\b|National Park Service|Park Service'),
    ('BLM', r'\bBLM\b|Bureau of Land Management'),
    ('USACE', r'usace|Army Corps|USACE'),
    ('USFS', r'(?<!Delaware )(?<!Florida )(?<!North Dakota )\bForest Service\b|/EDW/|\bEDW_'),
    ('state parks and wildlife', r'Parks (?:and|&) Wildlife|Wildlife (?:and|&) Parks|Fish, Wildlife (?:and|&) Parks|Game and Parks|'
                                 r'Game, Fish and Parks|Wildlife, Fisheries (?:and|&) Parks|\bKDWPT\b|\bNGPC\b|\bTPWD\b'),
    ('state wildlife', r'Fish (?:and|&) Game|Game (?:and|&) Fish|Fish (?:and|&) Wildlife|Wildlife Resources|Wildlife (?:and|&) Fisheries|'
                       r'Game Commission|Wildlife Conservation|Department of Wildlife|Division of Wildlife|MassWildlife|\bWDFW\b|'
                       r'\bNCWRC\b|\bTWRA\b|\bFWC\b|\bODWC\b|\bLDWF\b|\bAGFC\b|\bNDOW|Dept\.? of Conservation(?! and Natural)|Department of Conservation(?! and Natural)|'
                       r'\bMDC\b|DOFAW|\bIFW\b|\bDWR\b|Wildlife Freshwater|WMA_Boundaries|Game Lands'),
    ('state forestry', r'Division of Forestry|Department of Forestry|(?:' + STATES + r') Forest Service|State Forests?\b'),
    ('state natural heritage', r'Natural Heritage|Nature Preserves? Commission|Natural Areas?\b|Heritage Commission'),
    ('state parks', r'State Parks,? Historic Sites (?:and|&) Trails|State Parks (?:and|&) Trails|State Parks|Parks (?:and|&) Recreation|Division of Parks|Bureau of State Parks|Parks (?:and|&) Trails|'
                    r'Park Boundaries|ParkBoundaries|Bureau of Parks and Lands|Division of State Parks'),
    ('state historic preservation', r'Historic Resources|Historic Preservation'),
    ('state water district', r'Water Management District'),
    ('state (many owners)', r'GRANIT|MassGIS|Adirondack Park Agency|Conservation Lands|conserved lands|Conserved Lands|Protected Lands|'
                            r'Natural Areas Inventory|state owned and managed lands|State Lands|open space|OpenSpace|SCORP'),
    ('state natural resources agency', r'\bDNR\b|\bIDNR\b|Department of Natural Resources|\bDEC\b|\bDEEP\b|\bDEP\b|\bDNREC\b|\bDEM\b|'
                                       r'\bANR\b|Agency of Natural Resources|\bDCR\b|\bDCNR\b|\bTDEC\b|\bEMNRD\b|\bADCNR\b|'
                                       r'Conservation and Natural Resources|Department of Ecology|Natural Resources|Environment and Conservation'),
]
# (kind, pattern): every kind whose words appear is collected; one = that kind, two or more = 'mixed', none = the table tag
KIND_RULES = [
    ('park', r'(?<!non-)\bstate parks?\b|park boundar|ParkBoundar|park areas?|Park_Areas|park polygons|Park_Polygons|\bparks?\b(?! service)|parklands'),
    ('wildlife area', r'\bWMAs?\b|wildlife management areas?|wildlife areas?|game lands?|hunting|wildlife lands|WMA_|WHMA|wildlife properties'),
    ('refuge', r'refuges?\b'),
    ('forest', r'\bforests?\b|State_Forest'),
    ('preserve', r'\bpreserves?\b|natural areas?\b|ecological reserves|scientific and nat'),
    ('trail', r'\btrails?\b(?! system)'),
    ('wilderness', r'Wilderness Preservation System|wilderness areas?|wilderness study|BLM wilderness|\bWLD\b'),
    ('river corridor', r'wild and scenic river|Wild_and_Scenic|WildScenicRiver|\bWSR\b'),
    ('monument or conservation area', r'national monuments?|conservation areas?\b|\bNCAs?\b|\bNRAs?\b|designated areas'),
    ('recreation area', r'recreation (?:area|site|management)|Recreation_Areas|RecAreas|recreation inventory|BLM_\w*Rec'),
    ('herd area', r'\bherd\b|wild horse'),
    ('historic site', r'historic (?:places|sites|landmarks)|Historic Landmarks|Historic Resources'),
    ('fishing access', r'fishing access'),
    ('water', r'\blakes?\b|reservoirs|waterbodies|Fishing Lakes'),
    ('hatchery', r'hatcher'),
    ('special area', r'Critical Environmental Concern|\bACEC\b|Special Interest|Heritage Areas'),
]
TABLE_TAG = {'park': 'park', 'wild': 'wildlife area', 'forest': 'forest', 'preserve': 'preserve'}   # 'land' says nothing
TAG_FITS = {'park': ('park', 'recreation area'), 'wild': ('wildlife area', 'refuge'), 'forest': ('forest',), 'preserve': ('preserve', 'wilderness')}


GENERIC = ('state natural resources agency', 'state (many owners)')


def _agencies(text):
    """[(agency, matched words)] for every rule whose words appear in text, in rule order. A match's words are taken out
    before the next rule looks, so 'US Fish and Wildlife Service' is not also read as a state 'Fish and Wildlife'."""
    out = []
    for a, pat in AGENCY_RULES:
        m = re.search(pat, text)
        if m and a not in [x[0] for x in out]:
            out.append((a, m.group(0)))
            text = re.sub(pat, ' ', text)
    return out


def _kinds(text):
    return [k for k, pat in KIND_RULES if re.search(pat, text, re.I)]


def classify(lid, row):
    """-> {agency, kind, why} from the layer's own words: its description first, its address only when the description says
    nothing. Two different agencies named = 'several agencies'; two kinds named = 'mixed'; nothing named = 'unknown'."""
    if lid in HAND:
        a, k, why = HAND[lid]
        return {'agency': a, 'kind': k, 'why': 'by hand: ' + why}
    url, desc = (row[0] if row else ''), (row[2] if len(row) > 2 else '')
    path = url.split('/rest/services/')[-1] if '/rest/services/' in url else url
    path_words = path.replace('_', ' ') + ' ' + path
    tag = re.search(r'\((park|wild|forest|preserve|land), state GIS table\)', desc)
    plain = re.sub(r'\((?:park|wild|forest|preserve|land), state GIS table\)', ' ', desc)
    # agency
    found, a_from = _agencies(plain), 'its description'
    if not found:
        found, a_from = _agencies(path_words), 'its address'
    specific = [x for x in found if x[0] not in GENERIC]
    if not found:
        agency, a_why = 'unknown', 'no agency named in its description or address'
    elif len({x[0] for x in specific}) > 1 and specific[0][0] != 'many owners (PAD-US)':
        agency, a_why = 'several agencies', f'{a_from} names ' + ' and '.join(f'"{x[1]}"' for x in specific)
    else:
        agency, w = (specific or found)[0]
        a_why = f'{a_from} says "{w}"'
    # kind: the description's own words (the agency's name taken out), then the club's state GIS table tag, then the address
    no_agency = plain
    for _a, w in found:
        no_agency = no_agency.replace(w, ' ')
    kinds, k_from = _kinds(no_agency), 'its description'
    if not kinds:
        p2 = path_words
        for _a, w in _agencies(path_words):
            p2 = p2.replace(w, ' ')
        addr = _kinds(p2)
        t = tag.group(1) if tag and tag.group(1) in TABLE_TAG else None
        if t and addr:
            fits = [k for k in addr if k in TAG_FITS[t]]
            if fits and len(fits) == len(addr):
                kinds, k_from = fits, f'its address (the state GIS table says {t} too)'
            else:
                kinds, k_from = [], None
                kind, k_why = 'unknown', f'the state GIS table says {t}, its address says ' + ', '.join(addr)
        elif t:
            kinds, k_from = [TABLE_TAG[t]], 'the state GIS table'
        else:
            kinds, k_from = addr, 'its address'
    if len(kinds) == 1:
        kind, k_why = kinds[0], f'{k_from} says {kinds[0]}'
    elif kinds:
        kind, k_why = 'mixed', f'{k_from} names ' + ', '.join(kinds)
    elif k_from is not None:
        kind, k_why = 'unknown', 'no kind named'
    if agency == 'many owners (PAD-US)':
        kind, k_why = 'mixed', 'PAD-US holds every kind'
    return {'agency': agency, 'kind': kind, 'why': f'agency: {a_why}; kind: {k_why}'}


def build(layers_path=LAYERS):
    with open(layers_path, encoding='utf-8') as f:
        layers = json.load(f)
    rows = dict(NATIONAL, **{k: v for k, v in layers.items() if isinstance(v, list)})
    out = {lid: classify(lid, rows[lid]) for lid in sorted(rows)}
    n = len(out)
    return {'note': 'Each map layer\'s owning agency and kind, from the layer\'s own words (kpc_layer_agency_kind.py). '
                    '"unknown" = its words don\'t say; nothing is guessed. Change the rules, never this file by hand.',
            'counts': {'layers': n,
                       'agency unknown': sum(1 for v in out.values() if v['agency'] == 'unknown'),
                       'kind unknown': sum(1 for v in out.values() if v['kind'] == 'unknown'),
                       'both known': sum(1 for v in out.values() if v['agency'] != 'unknown' and v['kind'] != 'unknown')},
            'layers': out}


def dumps(doc):
    return json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=False) + '\n'


def selftest():
    bad = []

    def check(what, got, want):
        ok = got == want
        print(f'  {"ok  " if ok else "FAIL"} {what}' + ('' if ok else f': got {got!r}, wanted {want!r}'))
        if not ok:
            bad.append(what)
    C = lambda desc, url='https://x.example/arcgis/rest/services/Invented/FeatureServer/0/query': classify('t', [url, 'NAME', desc])
    check('NPS legal boundary = NPS park', (C('National Park Service (legal boundary) (park, state GIS table)')['agency'],
                                            C('National Park Service (legal boundary) (park, state GIS table)')['kind']), ('NPS', 'park'))
    check('state WMAs = state wildlife, wildlife area', (C('Idaho Fish and Game WMAs')['agency'], C('Idaho Fish and Game WMAs')['kind']),
          ('state wildlife', 'wildlife area'))
    check('a state Forest Service is state forestry, not USFS', C('Delaware Forest Service (forest, state GIS table)')['agency'], 'state forestry')
    check('the national Forest Service map is USFS',
          C('National Wilderness Preservation System (Forest Service map)', 'https://a.example/arcgis/rest/services/EDW/EDW_Wilderness_02/MapServer/0')['agency'],
          'USFS')
    check('BLM herd areas', (C('BLM herd areas')['agency'], C('BLM herd areas')['kind']), ('BLM', 'herd area'))
    check('two programs in one agency', C('Colorado Parks and Wildlife properties')['agency'], 'state parks and wildlife')
    check('WMAs and refuges = mixed, never one picked', C('Louisiana Dept. of Wildlife and Fisheries WMAs and refuges')['kind'], 'mixed')
    check("'land' in the table with no kind word = unknown kind", C('Ohio DNR (land, state GIS table)')['kind'], 'unknown')
    check('no agency words = unknown agency', C('Managed Areas (land, state GIS table)')['agency'], 'unknown')
    check('PAD-US = many owners, mixed', (classify('PAD-US', NATIONAL['PAD-US'])['agency'], classify('PAD-US', NATIONAL['PAD-US'])['kind']),
          ('many owners (PAD-US)', 'mixed'))
    check('the FWS national layer', (classify('fws', NATIONAL['fws'])['agency'], classify('fws', NATIONAL['fws'])['kind']), ('FWS', 'refuge'))
    check("'US Fish and Wildlife Service' is FWS, not also a state agency", C('US Fish and Wildlife Service (approved boundary) (wild, state GIS table)')['agency'], 'FWS')
    check("'State Parks & Trails' is the agency's name, not a trail kind", C('Arizona State Parks & Trails (park, state GIS table)')['kind'], 'park')
    check("a group named 'Chicago Wilderness' is not a wilderness", C('Illinois Nature Preserves Commission (Chicago Wilderness) (preserve, state GIS table)')['kind'], 'preserve')
    check("'Dept of Conservation and Natural Resources' is the whole department, not wildlife",
          C('Alabama Dept of Conservation and Natural Resources (preserve, state GIS table)')['agency'], 'state natural resources agency')
    check('two agencies named = several agencies', C('State of Maine conserved lands (Bureau of Parks and Lands / IFW) (land, state GIS table)')['agency'], 'several agencies')
    check('the table and the address agree: the address word wins', classify('t', ['https://x/arcgis/rest/services/National_Wildlife_Refuge_System_Boundaries/FeatureServer/0', 'N', 'FWSBoundaries (wild, state GIS table)'])['kind'], 'refuge')
    check('the table and the address disagree: unknown', classify('t', ['https://x/arcgis/rest/services/Recreation/Lakes/MapServer/9', 'N', 'Iowa DNR (wild, state GIS table)'])['kind'], 'unknown')
    check('every answer says why', bool(C('Idaho Fish and Game WMAs')['why']), True)
    print('SELF-TEST PASSED' if not bad else f'SELF-TEST FAILED: {len(bad)}: ' + '; '.join(bad))
    return 0 if not bad else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if '--selftest' in argv:
        return selftest()
    doc = dumps(build())
    if '--check' in argv:
        now = open(OUT, encoding='utf-8').read() if os.path.exists(OUT) else ''
        if now != doc:
            print(f'::error title=Layer agency and kind::{OUT} is out of date: run python3 .github/scripts/kpc_layer_agency_kind.py')
            return 1
        print(f'{OUT} is up to date')
        return 0
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(doc)
    c = json.loads(doc)['counts']
    print(f"wrote {OUT}: {c['layers']} layers, agency unknown {c['agency unknown']}, kind unknown {c['kind unknown']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
