#!/usr/bin/env python3
"""kpc_us_key_v2: the clean v2 US key matcher (26 Nov 2026).

Ties each park to the records of TODAY's layer files that are that park, and nothing else.
Rule sheet: .claude/notes/rule-sheet-us-key-v2-nov26.md. Rule table: .github/us-key-v2-rules.json (every rule row names the
function that carries it and the test that notices when it is gone).
Steps, each for all parks before the next: load -> 2 agency id -> 3 name with pin, size or two sources -> 4 pin only -> 5 gate.
Step 1: check the locks (a witness; it never decides). It compares the lock file with today's step 2 and reports held / broken.
Plain Python 3.12, no packages, no legacy modules.

  python kpc_us_key_v2.py --states MN NY --store <folder> --facts <park-facts.json.gz> --out <folder>
                          [--locks <run folder>] [--write-locks] [--repo <KPC-Links root>] [--selftest]
Exit codes: 0 built; 2 bad arguments / missing input / rule table refused; 3 a typed state not built (layer not complete);
4 gate failed.
"""
import argparse, array, csv, gzip, hashlib, io, json, math, os, re, sys, time, unicodedata

TOOL = 'kpc_us_key_v2 1 (2026-11-26)'
HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------------------------------------------- tables
S, L, D, RX = 'str', 'list of str', 'dict of str', 'regex'
TABLE_SHAPES = {
    'drop_layers': D, 'record_id_fields': D, 'class_fields': D, 'short_forms': D, 'des_kinds': D,
    'fixed_names': D, 'pin_only_reasons': D, 'neighbours': D, 'ca_neighbours': D, 'no_wait_layers': D, 'no_wait_status': D,
    'kind_words': L, 'place_words': L, 'compound_kinds': L, 'core_drop': L, 'water_last_words': L, 'acre_fields': L,
    'size_witness_tags': L, 'placeholders': L, 'drop_words': L, 'ca_kind_words': L,
    'easement_rx': RX, 'type_field_rx': RX, 'lease_name_rx': RX, 'water_park_kind_rx': RX, 'office_rx': RX,
    'trail_kind_rx': RX, 'line_park_kind_rx': RX, 'home_page_rx': RX, 'acre_field_rx': RX, 'roman_rx': RX,
    'other_spellings': {'*': [{'name': S, 'why': S, 'date': S}]},
    'name_fields': {'*': [S]}, 'unit_fields': {'*': [S]}, 'bilingual_fields': {'*': [[S, S]]}, 'size_fields': {'*': [S, S]},
    'size_text_units': [[RX, S]], 'apostrophes': L, 'lang_kinds': [{'kind': S, 'en': [S], 'fr': [S], 'proof': S}], 'lang_small_words': L, 'full_name_fields': {'*': [[S]]}, 'layer_kinds': {'*': [S]},
    'piece_suffixes': [RX], 'kind_patterns': [[S, RX]], 'name_equivalences': [[RX, S]],
    'id_ties': [{'kind': S, 'layer': S, 'field': S, '?rx': RX, '?where': D, '?measured': S, '?glue': S}],
    'kind_swaps': [{'park_kind': S, 'record_kinds': [S], '?layer': S}],
    'unit_pieces': {'*': {'project_field': S, 'name_field': S}},
    'interest_fields': {'*': {'field': S, 'fee': [S]}},
    'wetland_district': {'park_rx': RX, 'layer': S, 'field': S, 'fee': S, 'type_field': S, 'type': S},
    'page_name': {'page_kind': S, 'sites': [S], 'other_state': S, 'level': S},
    'own_page': {'own': S, 'sites': [S], 'source_rx': RX, 'witness': S, 'hand_copy': S},
}
LINK_TIE_SHAPE = [{'kind': S, 'layer': S, 'field': S, 'rx': RX, '?glue': S}]
VALUE_KEYS = ('size_tol', 'two_sources_tol', 'pin_m', 'near_km', 'lock_acres_tol', 'thin_m', 'long_ratio', 'acre_box_factor',
              'same_ground_share', 'same_ground_tol', 'place_word_len', 'line_pin_m', 'ha_acres', 'km2_acres', 'mi2_acres')
RULE_ROW = {'id': S, 'step': S, 'what': S, 'why': S, 'test': S, 'fn': S, 'stub': S}
STEPS = {'load', '1', '2', '3', '4', 'gate', 'write'}
STUBS = {'true', 'false', 'empty', 'identity', 'none'}


class RulesError(ValueError):
    pass


def check_shape(v, shape, where):
    """A table value must have exactly the shape the code reads; else RulesError naming the place."""
    def bad(msg): raise RulesError(f'{where}: {msg}')
    if shape in (S, RX):
        if not isinstance(v, str): bad('not a text')
        if shape == RX:
            try: re.compile(v)
            except re.error as e: bad(f'broken pattern ({e})')
    elif shape == L:
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v): bad('not a list of texts')
    elif shape == D:
        if not isinstance(v, dict) or not all(isinstance(x, str) for x in v.values()): bad('not a map of texts')
    elif isinstance(shape, list):
        if not isinstance(v, list): bad('not a list')
        if len(shape) == 1:
            for n, x in enumerate(v): check_shape(x, shape[0], f'{where}[{n}]')
        else:
            if len(v) != len(shape): bad(f'needs {len(shape)} items')
            for n, (x, s) in enumerate(zip(v, shape)): check_shape(x, s, f'{where}[{n}]')
    elif isinstance(shape, dict):
        if not isinstance(v, dict): bad('not a map')
        if '*' in shape:
            for k, x in v.items(): check_shape(x, shape['*'], f'{where}.{k}')
            return
        need = {k for k in shape if not k.startswith('?')}
        known = {k.lstrip('?') for k in shape}
        if need - set(v): bad(f'missing {", ".join(sorted(need - set(v)))}')
        if set(v) - known: bad(f'unknown {", ".join(sorted(set(v) - known))}')
        for k, s in shape.items():
            if k.lstrip('?') in v: check_shape(v[k.lstrip('?')], s, f'{where}.{k.lstrip("?")}')


def check_rules(d):
    """Rule rule_table_checked: the table must be exactly what the code knows: no unknown key, every why, test, function and
    stub, every value of the right type, every row inside every table of the right shape."""
    def bad(msg): raise RulesError(msg)
    top = {'about': str, 'version': int, 'rules': list, 'values': dict, 'tables': dict, 'notes': dict}
    if not isinstance(d, dict): bad('the rule table is not a JSON object')
    for k in d:
        if k not in top: bad(f'unknown key {k!r}')
    for k, t in top.items():
        if not isinstance(d.get(k), t): bad(f'{k!r} missing or not a {t.__name__}')
    for row in d['rules']:
        if not isinstance(row, dict) or set(row) != set(RULE_ROW) or not all(isinstance(row[k], str) for k in row):
            bad(f'rule row {row.get("id") if isinstance(row, dict) else row!r} needs exactly {", ".join(RULE_ROW)}')
        if not all(row[k] for k in ('id', 'what', 'why', 'test')) or row['step'] not in STEPS or row['stub'] not in STUBS:
            bad(f'rule row {row["id"]!r}: empty text, unknown step or unknown stub')
        if row['stub'] != 'none' and not row['fn']: bad(f'rule row {row["id"]!r} names no function')
    for part, want in (('values', {k: None for k in VALUE_KEYS}), ('tables', TABLE_SHAPES)):
        for k in d[part]:
            if k not in want: bad(f'unknown {part[:-1]} {k!r}')
        for k in want:
            row = d[part].get(k)
            if not isinstance(row, dict) or set(row) != {'value', 'why', 'test'}: bad(f'{part[:-1]} {k!r} needs exactly value, why, test')
            if not (isinstance(row['why'], str) and row['why'] and isinstance(row['test'], str) and row['test']): bad(f'{k!r} needs a why and a test')
            if part == 'values':
                if isinstance(row['value'], bool) or not isinstance(row['value'], (int, float)): bad(f'{k!r} has a value of the wrong type')
            else:
                check_shape(row['value'], TABLE_SHAPES[k], k)
    for k, v in d['notes'].items():
        if not isinstance(v, (str, dict)) or (isinstance(v, dict) and not all(isinstance(x, str) for x in v.values())):
            bad(f'note {k!r} is not text')


def rules_path(repo, path=None):
    """The rule table: --rules, else the copy beside this script (the PC kit folder), else <repo>/.github/."""
    beside = os.path.join(HERE, 'us-key-v2-rules.json')
    return path or (beside if os.path.isfile(beside) else os.path.join(repo, '.github', 'us-key-v2-rules.json'))


def load_rules(repo, path=None):
    """The rule table (.github/us-key-v2-rules.json, or a trial table given with --rules), checked, patterns compiled once."""
    try:
        with open(rules_path(repo, path), encoding='utf-8') as f: d = json.load(f)
        with open(os.path.join(repo, '.github', 'link-id-ties.json'), encoding='utf-8') as f: web = json.load(f).get('ties')
    except ValueError as e:
        raise RulesError(f'not JSON ({e})')
    check_rules(d)
    check_shape(web, LINK_TIE_SHAPE, 'link-id-ties.json ties')
    r = {k: v['value'] for k, v in d['tables'].items()}
    r['numbers'] = {k: float(v['value']) for k, v in d['values'].items()}
    r['rules'] = d['rules']
    for k in [k for k, s in TABLE_SHAPES.items() if s == RX]: r['_' + k] = re.compile(r[k], re.I)
    r['_wmd'] = re.compile(r['wetland_district']['park_rx'], re.I)
    r['_kinds'] = [(k, re.compile(x)) for k, x in r['kind_patterns']]
    r['_equiv'] = [(re.compile(a), b) for a, b in r['name_equivalences']]
    r['_suffix'] = re.compile(r'\s(?:' + '|'.join(r['piece_suffixes'] or ['(?!)']) + r')$')
    r['_kind_words'], r['_place_words'] = set(r['kind_words']), set(r['place_words'])
    r['_ties'] = {}
    for t in r['id_ties'] + web:
        r['_ties'].setdefault(t['layer'], []).append(dict(t, _rx=re.compile(t['rx'], re.I) if t.get('rx') else None))
    r['_size_units'] = [(re.compile(x, re.I), u) for x, u in r['size_text_units']]
    r['_keep'] = keep_fields(r)
    return r


def keep_fields(r):
    """Rule memory: the attribute names any step reads (lower case); the loader keeps only these (plus acre / type fields)."""
    k = {'des_tp'} | {f for f in r['acre_fields']} | set(r['record_id_fields'].values()) | set(r['class_fields'].values())
    for ts in r['_ties'].values():
        for t in ts: k |= {t['field']} | set(t.get('where') or {})
    for fs in r['name_fields'].values(): k |= set(fs)
    for fss in r['full_name_fields'].values(): k |= {f for fs in fss for f in fs}
    for fs in r['unit_fields'].values(): k |= set(fs)
    for u in r['unit_pieces'].values(): k |= {u['project_field'], u['name_field']}
    for f in r['interest_fields'].values(): k.add(f['field'])
    k |= {r['wetland_district']['field'], r['wetland_district']['type_field']} | {f for f, _ in r['size_fields'].values()}
    return {x.lower() for x in k}


# ---------------------------------------------------------------------------------------------------------------- names
def wildlife_and_fish(s, rules):
    """Rule name_wildlife_and_fish (name_equivalences): 'Wildlife and Fish Refuge' = 'Wildlife Refuge'."""
    for rx, to in rules['_equiv']: s = rx.sub(to, s)
    return s


def same_apostrophe(t, rules):
    """Rule same_apostrophe: a curly apostrophe (or a look-alike, table apostrophes) is the straight one."""
    for c in rules['apostrophes']: t = t.replace(c, "'")
    return t


def full(name, rules):
    """Rule name_exact: lower case, accents and brackets out, '&' = and, the name equivalences, punctuation out, drop_words
    ('the') out, short forms written out."""
    memo = rules.setdefault('_full', {})
    key = (str(name or ''), wildlife_and_fish)
    if key not in memo:
        t = unicodedata.normalize('NFKD', same_apostrophe(key[0], rules)).encode('ascii', 'ignore').decode().lower()
        t = wildlife_and_fish(re.sub(r'\(.*?\)', ' ', t).replace('&', ' and '), rules)
        t = re.sub(r'[^a-z0-9 ]+', ' ', t)
        memo[key] = ' '.join(rules['short_forms'].get(w, w) for w in t.split() if w not in rules['drop_words'])
    return memo[key]


def full_ps(name, rules):
    """Rule name_possessive: full() with a possessive written as one word (Knox's = Knoxs). The second try."""
    return full(re.sub(r"(?i)(?<=[a-z])['’`]s\b", 's', str(name or '')), rules)


def nk(t):
    """The PC test's name key: lower-case letters and digits only (POTA's names, brackets too)."""
    return re.sub(r'[^a-z0-9]', '', str(t or '').lower())


def generic(name, rules):
    """A name that tells no place from another ('Unit 1', 'Wildlife Management Area', ''): never a name to join by."""
    words = re.findall(r'[a-z0-9]+', str(name or '').lower())
    return not words or all(w in rules['_kind_words'] or w.isdigit() or rules['_roman_rx'].fullmatch(w) for w in words)


def real_words(text, rules):
    """The real place words of a name: place_word_len letters or more, not a kind word or a place word."""
    return {w for w in full(text, rules).split()
            if len(w) >= rules['numbers']['place_word_len'] and w not in rules['_kind_words'] and w not in rules['_place_words']}


def kind_swap_keys(k, layer, rules):
    """Rules name_ny_dec_class / name_kind_swaps (v1 KIND_SWAPS): 'X Marine Park' also reads 'X State Park', 'X Trail' reads
    'X State Trail', NY DEC 'X Wild Forest' reads 'X State Forest'; only with a real place word in X."""
    out = set()
    for sw in rules['kind_swaps']:
        if sw.get('layer') and sw['layer'] != layer: continue
        for rk in sw['record_kinds']:
            if k.endswith(' ' + rk):
                core = k[:-len(rk) - 1].strip()
                if real_words(core, rules): out.add(f"{core} {sw['park_kind']}")
    return out


def compound_keys(k, rules):
    """Rule name_compound: 'X Heritage Preserve and Wildlife Management Area' also reads 'X Heritage Preserve' and
    'X Wildlife Management Area' (both kinds from compound_kinds, a real place word in X)."""
    for a in rules['compound_kinds']:
        for b in rules['compound_kinds']:
            tail = f' {a} and {b}'
            if a != b and k.endswith(tail) and real_words(k[:-len(tail)], rules):
                return {f'{k[:-len(tail)].strip()} {a}', f'{k[:-len(tail)].strip()} {b}'}
    return set()


def single_letters_out(k, rules):
    """Rule name_single_letters (v1 R4, 25 Nov): 'knox s headquarters' = 'knox headquarters'; only when 2 or more real words
    (not kind words) are left. '' otherwise."""
    w = [x for x in k.split() if len(x) > 1]
    return ' '.join(w) if len([x for x in w if x not in rules['_kind_words']]) >= 2 else ''


def run_together(k, rules):
    """Rule name_words_run_together: the place words written as one ('roeliff jansen kill' = 'roeliff jansenkill');
    kind words stay words."""
    out = []
    for w in k.split():
        if out and not out[-1][1] and w not in rules['_kind_words']: out[-1][0] += w
        else: out.append([w, w in rules['_kind_words']])
    return ' '.join(x[0] for x in out)


def name_forms(n, rules):
    """The forms one name is known by: plain, single letters out, the possessive as one word, place words run together."""
    out = set()
    for k in (full(n, rules), full_ps(n, rules)):
        if k: out |= {k, single_letters_out(k, rules)} - {''}
    return out | {run_together(k, rules) for k in out}


def record_name_keys(names, layer, rules):
    """The name keys a record is found by."""
    out = set()
    for n in names:
        if generic(n, rules): continue
        for k in name_forms(n, rules):
            out.add(k)
            for alt in kind_swap_keys(k, layer, rules) | compound_keys(k, rules):
                out |= {alt, single_letters_out(alt, rules)} - {''}
    return out


def park_name_keys(name, kind, rules):
    """Rule name_exact: the park's own name, and its name without its kind word ('Crow Wing' for Crow Wing State Park)."""
    out = set()
    for f in (full, full_ps):
        a, t = f(name, rules), f(kind, rules)
        if not a: continue
        out.add(a)
        if t and a.endswith(' ' + t) and not generic(a[:-len(t) - 1], rules): out.add(a[:-len(t) - 1].strip())
    out |= {single_letters_out(k, rules) for k in out} - {''}
    return out | {run_together(k, rules) for k in out}


def other_spelling_keys(ref, rules):
    """Rule name_other_spelling (27 Nov 2026): a park may have a few more exact spellings of its name in the table
    other_spellings (US-0474, US-2147, US-4239). Each is one exact string, read like any exact name (full, then the possessive
    second try): no kind word taken off, no single letters set aside, no run-together words, nothing fuzzy. It is only a way
    to write the name: the pin or the size must still prove the land. -> a set of name keys (empty for any other park)."""
    out = set()
    for row in rules['other_spellings'].get(ref, []): out |= {full(row['name'], rules), full_ps(row['name'], rules)}
    return out - {''}


def page_name(p, rules):
    """The place name inside the park's own official page address, when the link bot rated it 'strong'; '' otherwise."""
    lk, pn = p.get('link') or {}, rules['page_name']
    if lk.get('page_kind') != pn['page_kind'] or lk.get('site') not in pn['sites']: return ''
    if str(lk.get('state_check') or '').startswith(pn['other_state']) or lk.get('name_match') != pn['level']: return ''
    return str(lk.get('web_name') or '')


def page_name_keys(p, rules):
    """Rule page_name (v1 link_name_agree, 'strong' only): the keys of the page name; empty when there is none."""
    w = page_name(p, rules)
    return set() if generic(w, rules) else name_forms(w, rules)


# ---------------------------------------------------------------------------------------------------------------- shapes
def decode_rings(raw, q, min_pts=3):
    """The layer file's delta-encoded integer rings (or a line's paths, min_pts 2) -> [[(lon, lat), ...], ...] (first point,
    then steps)."""
    if isinstance(raw, str):
        try: raw = json.loads(raw)
        except ValueError: return []
    try: s = 10 ** int(q or 6)
    except (TypeError, ValueError): s = 10 ** 6
    out = []
    for ring in raw or []:
        if not isinstance(ring, (list, array.array)) or len(ring) < 2: continue
        x, y = ring[0], ring[1]; pts = [(x / s, y / s)]
        for i in range(2, len(ring) - 1, 2):
            x += ring[i]; y += ring[i + 1]; pts.append((x / s, y / s))
        if len(pts) >= min_pts: out.append(pts)
    return out


def inside(lon, lat, rings):
    """Pin inside the shape (even-odd, so holes are out)."""
    c = False
    for ring in rings:
        j = len(ring) - 1
        for i in range(len(ring)):
            xi, yi = ring[i]; xj, yj = ring[j]
            if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi: c = not c
            j = i
    return c


def edge_m(lon, lat, rings):
    """The pin's distance in metres to the nearest edge of the shape."""
    kx, ky, best = 111320.0 * math.cos(math.radians(lat)), 110574.0, float('inf')
    for r in rings:
        for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]):
            ax, ay, bx, by = (x1 - lon) * kx, (y1 - lat) * ky, (x2 - lon) * kx, (y2 - lat) * ky
            dx, dy = bx - ax, by - ay
            t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
            best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best


def line_m(lon, lat, paths):
    """The pin's distance in metres to the nearest segment of a line (open paths, never closed)."""
    kx, ky, best = 111320.0 * math.cos(math.radians(lat)), 110574.0, float('inf')
    for r in paths:
        for (x1, y1), (x2, y2) in zip(r, r[1:]):
            ax, ay, bx, by = (x1 - lon) * kx, (y1 - lat) * ky, (x2 - lon) * kx, (y2 - lat) * ky
            dx, dy = bx - ax, by - ay
            t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
            best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best


def box_of(rings):
    xs = [p[0] for r in rings for p in r]; ys = [p[1] for r in rings for p in r]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def km_to_box(lat, lon, b):
    """Distance in km from the pin to a box (0 inside it; no box = endless)."""
    if not b: return float('inf')
    dx = max(b[0] - lon, 0.0, lon - b[2]) * 111.32 * math.cos(math.radians(lat))
    dy = max(b[1] - lat, 0.0, lat - b[3]) * 110.57
    return math.hypot(dx, dy)


def box_gap_km(a, b):
    """The gap in km between two boxes (0 when they touch or overlap)."""
    if not a or not b: return float('inf')
    dx = max(a[0] - b[2], b[0] - a[2], 0.0) * 111.32 * math.cos(math.radians((a[1] + b[3]) / 2))
    return math.hypot(dx, max(a[1] - b[3], b[1] - a[3], 0.0) * 110.57)


def _ring_m2(ring):
    k = math.cos(math.radians(sum(p[1] for p in ring) / len(ring)))
    return sum((x1 * 111320.0 * k) * (y2 * 110574.0) - (x2 * 111320.0 * k) * (y1 * 110574.0)
               for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1])) / 2.0


def acres_of(rings):
    """Measured acres of a shape (outer rings minus holes, by their turning)."""
    return abs(sum(_ring_m2(r) for r in rings)) / 4046.86


def _perimeter_m(rings):
    return sum(math.hypot((x2 - x1) * 111320.0 * math.cos(math.radians((y1 + y2) / 2)), (y2 - y1) * 110574.0)
               for r in rings for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]))


def mean_width_m(rings):
    per = _perimeter_m(rings)
    return 2 * acres_of(rings) * 4046.86 / per if per > 0 else 0.0


def too_thin(rings, rules):
    """Rule thin_must_be_long: a thin strip = narrower than thin_m on average AND long (its biggest piece: half its outline
    at least long_ratio times its width). A small square is not a strip."""
    n = rules['numbers']
    mw = mean_width_m(rings)
    if not 0 < mw < n['thin_m']: return False
    big = max(rings, key=lambda r: acres_of([r]))
    w = mean_width_m([big])
    return w > 0 and _perimeter_m([big]) / 2 >= n['long_ratio'] * w


# ---------------------------------------------------------------------------------------------------------------- records
def attr(a, field):
    """A record field by name, any letter case."""
    if field in a: return a[field]
    lo = field.lower()
    return next((a[k] for k in a if str(k).lower() == lo), None)


def norm_val(v):
    """An id value as text: '89125' from 89125.0, 'SRA00304' from 'SRA00304  '; '' when empty."""
    if v is None or isinstance(v, bool): return ''
    if isinstance(v, float):
        if v != v: return ''
        if v.is_integer(): v = int(v)
    return str(v).strip().upper().replace('\u2019', "'").replace('\u2018', "'")


def is_placeholder(v, rules):
    """Rule placeholder_not_unit: 'N/A', 'none', 'unknown', empty, a bare home-page address: never an id or a group."""
    t = str(v or '').strip()
    return t.lower() in rules['placeholders'] or bool(rules['_home_page_rx'].fullmatch(t))


def tie_value(rec, tie, rules):
    """Rule id_tie: the agency unit id a record carries for one tie of the table ('' = none)."""
    a = rec['a']
    for f, want in (tie.get('where') or {}).items():
        if norm_val(attr(a, f)) != norm_val(want): return ''
    v = attr(a, tie['field'])
    if tie.get('_rx'):
        m = tie['_rx'].search(str(v or ''))
        v = (tie.get('glue') or '').join(g or '' for g in m.groups()) if m else None
    return '' if is_placeholder(v, rules) else norm_val(v)


def shape(rec):
    """A record's area rings ([] for a line: a line has no area; its paths are in rec['_p'])."""
    if '_g' not in rec:
        if rec.get('line'):
            rec['_g'], rec['_p'] = [], decode_rings(rec['paths'], rec['q'], min_pts=2)
            rec['_b'] = box_of(rec['_p'])
        else:
            rec['_g'] = decode_rings(rec['raw'], rec['q'])
            rec['_b'] = box_of(rec['_g'])
    return rec['_g']


def line_has_no_size(rec):
    """Rule line_no_acres: a line never has acres (never in ac, the size proof, two sources or same ground)."""
    return bool(rec.get('line'))


def rec_box(rec):
    shape(rec)
    return rec['_b']


def agency_acres(rec, rules):
    """The agency's own acres field (acre_fields, else the first field matching acre_field_rx), checked against the record's
    box (acre_box_factor): square feet / square metres converted; None = none on file."""
    if '_aa' in rec: return rec['_aa']
    if line_has_no_size(rec):
        rec['_aa'] = None; return None
    a, v = rec['a'], None
    for k in rules['acre_fields']:
        try:
            x = float(a.get(k))
            if x > 0: v = x; break
        except (TypeError, ValueError):
            pass
    if v is None and rec['layer'] in rules['size_fields']:
        v = size_field_acres(a, rec['layer'], rules)
    if v is None:
        k = next((k for k in a if rules['_acre_field_rx'].search(str(k))), None)
        try: v = float(a[k]) if k is not None and float(a[k]) > 0 else None
        except (TypeError, ValueError): v = None
    g = shape(rec)
    if v and g:
        b = rec['_b']
        cap = max((b[2] - b[0]) * 111.32 * math.cos(math.radians((b[1] + b[3]) / 2)), .01) * max((b[3] - b[1]) * 110.57, .01) \
            * 247.105 * rules['numbers']['acre_box_factor']
        if v > cap: v = next((round(v / d, 1) for d in (43560.0, 4046.86) if v / d <= cap), None)
    rec['_aa'] = float(v) if v else None
    return rec['_aa']


def size_field_acres(a, layer, rules):
    """Rule size_in_hectares: the layer's own size field in the unit measured for it (ha or km2, size_fields), as acres."""
    fld, unit = rules['size_fields'][layer]
    try: x = float(attr(a, fld))
    except (TypeError, ValueError): return None
    return x * rules['numbers'][f'{unit}_acres'] if x > 0 else None


def size_from_text(text, rules):
    """Rule page_size_unit: a page size from its text as written ('568.71 hectares', '1,245 km2', '12,388 acres'): the number
    times its unit (size_text_units). None when the unit cannot be told or the text holds two numbers ('606 + 360 acres')."""
    t = str(text or '').lower().replace('\u00a0', ' ')
    nums = re.findall(r'\d[\d,]*(?:\.\d+)?', re.sub(r'(km|mi)\s*[2\u00b2]', r'\1', t))
    if len(nums) != 1: return None
    x = float(nums[0].replace(',', '')) * (1e6 if re.search(r'\bmillion\b', t) else 1.0)
    for rx, unit in rules['_size_units']:
        if rx.search(t): return x * (1.0 if unit == 'acres' else rules['numbers'][f'{unit}_acres'])
    return None


def rec_acres(rec, rules):
    """A record's size: the agency's own acres, else its outline measured."""
    if '_ac' not in rec:
        rec['_ac'] = 0.0 if line_has_no_size(rec) else agency_acres(rec, rules) or round(acres_of(shape(rec)), 1)
    return rec['_ac']


def box_share(a, b):
    """How much of the smaller box lies on the bigger one (0..1)."""
    if not a or not b: return 0.0
    w, h = min(a[2], b[2]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[1], b[1])
    if w <= 0 or h <= 0: return 0.0
    small = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
    return min(1.0, w * h / small) if small > 0 else 1.0


def class_of(rec, rules):
    """Rule acres_no_double_count: the class a record of a layer in class_fields is totalled in (PAD-US FeatClass)."""
    cf = rules['class_fields'].get(rec['layer'])
    return norm_val(attr(rec['a'], cf)) if cf else ''


GRID = 6   # the sample points per side of the smaller record's box (a measuring detail, not a rule)


def same_ground(v, a, kv, k, rules):
    """Rule acres_same_ground_once: two same-name records are the same ground when the sample points inside the smaller
    record's SHAPE lie at least same_ground_share inside the other's shape (boxes first), and the sizes agree."""
    n = rules['numbers']
    if not box_share(rec_box(a), rec_box(k)) or abs(v - kv) > n['same_ground_tol'] * max(v, kv): return False
    for r in (a, k):
        if '_m' not in r: r['_m'] = acres_of(shape(r))
    small, big = (a, k) if a['_m'] <= k['_m'] else (k, a)
    b = small['_b']
    pts = [(b[0] + (b[2] - b[0]) * (i + .5) / GRID, b[1] + (b[3] - b[1]) * (j + .5) / GRID) for i in range(GRID) for j in range(GRID)]
    pts += [(sum(x for x, _ in r) / len(r), sum(y for _, y in r) / len(r)) for r in small['_g']]   # each piece's middle too
    pts = [q for q in pts if inside(q[0], q[1], small['_g'])]
    return bool(pts) and sum(1 for q in pts if inside(q[0], q[1], shape(big))) >= n['same_ground_share'] * len(pts)


def land_acres(recs, rules, agency_only=False):
    """{layer: acres}: per class, the largest class; same ground counted once. agency_only: the agency's acres only."""
    groups = {}
    for rec in recs:
        if not line_has_no_size(rec): groups.setdefault(rec['layer'], {}).setdefault(class_of(rec, rules), []).append(rec)
    out = {rec['layer']: 0.0 for rec in recs if line_has_no_size(rec)}
    for layer, classes in groups.items():
        best = 0.0
        for rs in classes.values():
            vals = [((agency_acres(r, rules) or 0.0) if agency_only else rec_acres(r, rules), r['id'], nk(r['name']), r) for r in rs]
            kept, total = {}, 0.0
            for v, _, name, r in sorted(vals, key=lambda x: (-x[0], x[1])):
                if any(same_ground(v, r, kv, k, rules) for kv, k in kept.get(name, ())): continue
                kept.setdefault(name, []).append((v, r)); total += v
            best = max(best, total)
        out[layer] = best
    return out


def piece_key(rec, up):
    """Rule wma_project_pieces: (layer, project, unit name) of a record of a layer in unit_pieces."""
    return (rec['layer'], norm_val(attr(rec['a'], up['project_field'])), nk(attr(rec['a'], up['name_field'])))


def piece_base(k, rules):
    """Rule piece_suffix: a name without its trailing piece word ('... state forest west' -> '... state forest')."""
    return rules['_suffix'].sub('', k)


def spell_layer(recs, layer, rules):
    """Rule spell_agency_id: {file key: '<layer>0<agency digits>'} for one layer of one file when its agency id field is
    filled, unique and of one letter prefix on every record; {} when the layer keeps the file's own keys."""
    fld = rules['record_id_fields'].get(layer)
    if not fld or not recs: return {}
    got, letters = {}, set()
    for r in recs:
        m = re.fullmatch(r'([A-Za-z]*)0*(\d+)', norm_val(attr(r.get('attributes') or {}, fld)))
        if not m or int(m.group(2)) == 0: return {}
        letters.add(m.group(1)); got[r['key']] = m.group(2)
    if len(letters) != 1 or len(set(got.values())) != len(got): return {}
    return {k: f'{layer}0{d}' for k, d in got.items()}


# ---------------------------------------------------------------------------------------------------------------- load
def layer_gaps(doc, rules=None):
    """Rule load_complete: layers of a file that are not complete, or that have records but no manifest row.
    Rule load_no_wait (owner 27 Nov 2026): a layer that is not land (points only) is nothing to wait for, so it is no gap."""
    man = doc.get('manifest') or {}
    skip = set(no_wait(doc, rules))
    return sorted(({l for l, m in man.items() if not (m or {}).get('complete')}
                   | {str(r.get('layer') or '') for r in doc.get('records') or []} - set(man)) - skip)


def no_wait(doc, rules):
    """Rule load_no_wait: {layer: why} for the layers of a file that are not complete and are NOT waited for: the layer is
    named in the table no_wait_layers, or the store room gave it a status in the table no_wait_status (its word for a layer
    that holds only points). Such a layer never holds an outline, so a build without it is not a gap build."""
    if not rules: return {}
    names, words = rules.get('no_wait_layers') or {}, rules.get('no_wait_status') or {}
    out = {}
    for l, m in (doc.get('manifest') or {}).items():
        if (m or {}).get('complete'): continue
        if l in names: out[l] = names[l]
        elif str((m or {}).get('status') or '') in words: out[l] = words[str(m.get('status'))]
    return out


def dropped_layer(layer, rules):
    """Rule load_drop_layers."""
    return layer in rules['drop_layers']


def is_line(r):
    """Rule line_record: a record with paths, shape 'line' and no rings is a LINE (a trail), not a record without a shape."""
    return not r.get('rings') and bool(r.get('paths')) and r.get('shape') == 'line'


def has_shape(r):
    """Rule load_no_shape."""
    return bool(r.get('rings')) or is_line(r)


def repeated_key(count, spelled):
    """Rule load_key_not_unique: a file key that repeats in its file names no single record (unless the agency id does)."""
    return count > 1 and not spelled


def service_of(url):
    """Rule two_sources_independent: the map service a layer comes from (its address up to MapServer / FeatureServer)."""
    return re.sub(r'/(?:MapServer|FeatureServer)(?:/.*)?$', '', str(url or ''), flags=re.I).lower()


def other_services(a, b):
    """Rule two_sources_independent: two layers of one map service are one source (Québec's protected-areas register and
    its recognised-reserves layer carry the same records and sizes)."""
    return not (a.get('svc') and a.get('svc') == b.get('svc'))


def layer_copies(manifest):
    """Rule layer_copy: a layer whose source (url and where) is another layer's of the same file is a second copy of it; the
    first label (sorted) is kept, the copies are dropped ('Québec prote' and 'Qu_bec prote' hold the same 5,611 records)."""
    seen, out = {}, set()
    for lay in sorted(manifest):
        m = manifest[lay] or {}
        if not m.get('url'): continue
        k = (m.get('url'), m.get('where'))
        if k in seen: out.add(lay)
        else: seen[k] = lay
    return out


def already_loaded(by_ident, ident):
    """Rule load_same_record_twice: the record is already in from the state's own file (or an earlier neighbour)."""
    return ident in by_ident


class Pool:
    """Today's records of the typed state's file and its neighbours' files, with their indexes."""

    def __init__(self, rules):
        self.rules, self.recs, self.dropped, self.by_ident = rules, [], {}, {}
        self.raw_ids, self.tie_ix, self.name_ix, self.piece_ix, self.core_ix, self.base_ix = {}, {}, {}, {}, {}, {}
        self.layer_name_ix, self.lines, self.kp_ix, self.services = {}, {}, {}, {}

    def rec_kinds(self, rec):
        """v1 record kinds: the kinds its names carry, its PAD-US designation type, its layer's kind (layer_kinds)."""
        r = self.rules
        k = set().union(*[kinds_of(n, r) for n in rec['names']])
        k |= {r['des_kinds'][d] for d in [attr(rec['a'], 'Des_Tp')] if d in r['des_kinds']}
        return k | set(r['layer_kinds'].get(rec['layer'], []))

    def drop(self, why, n=1):
        self.dropped[why] = self.dropped.get(why, 0) + n

    def add_file(self, area, doc):
        """Load one layer file. Every raw record's written id is kept first (the gate's check), then the drops."""
        rules, by_layer = self.rules, {}
        for r in doc.get('records') or []: by_layer.setdefault(str(r.get('layer') or ''), []).append(r)
        copies = layer_copies(doc.get('manifest') or {})
        for lay, m in (doc.get('manifest') or {}).items():
            if (m or {}).get('url'): self.services.setdefault(lay, service_of(m['url']))
        for layer in sorted(by_layer):
            if layer in copies:
                self.drop(f'layer_copy {layer}', len(by_layer[layer])); continue
            rs = by_layer[layer]
            spelled = spell_layer(rs, layer, rules)
            for r in rs:
                key = str(r.get('key') or '').replace('@', '')
                self.raw_ids.setdefault((area, layer, spelled.get(r.get('key')) or key), []).append(key)
            if dropped_layer(layer, rules):
                self.drop(f'drop_layer {layer}', len(rs)); continue
            seen = {}
            for r in rs: seen[r.get('key')] = seen.get(r.get('key'), 0) + 1
            for r in sorted(rs, key=lambda x: str(x.get('key'))):
                key = str(r.get('key') or '').replace('@', '')
                if not has_shape(r): self.drop('no_shape'); continue
                if repeated_key(seen[r.get('key')], bool(spelled)): self.drop(f'key_not_unique {layer}'); continue
                rid = spelled.get(r.get('key')) or key
                if already_loaded(self.by_ident, (layer, rid)):
                    old = self.by_ident[(layer, rid)]
                    self.drop('same_record_in_two_files' if nk(old['name']) == nk(r.get('record_name')) else 'other_record_same_id')
                    continue
                self.add_record(area, layer, key, rid, bool(spelled), r)

    def add_record(self, area, layer, key, rid, agency, r):
        rules, a = self.rules, r.get('attributes') or {}
        names = [str(r.get('record_name') or rules['fixed_names'].get(layer, ''))] + \
            [str(attr(a, f)) for f in rules['name_fields'].get(layer, []) if attr(a, f)]
        fulls = [' '.join(str(attr(a, f) or '').strip() for f in fs) for fs in rules['full_name_fields'].get(layer, [])]
        rec = {'i': len(self.recs), 'area': area, 'layer': layer, 'key': key, 'id': rid, 'agency': agency,
               'name': next((n for n in names if n.strip()), ''),
               'names': [n for n in dict.fromkeys(names) if n.strip()], 'full_names': [n for n in fulls if n.strip()],
               'a': a, 'q': r.get('q'), 'raw': r.get('rings')}
        rec.update(pub=r.get('publishable'), lic=r.get('licence_class'), pub_why=r.get('publish_why'), svc=self.services.get(layer))
        if is_line(r):
            rec.update(line=True, paths=r.get('paths'))
            self.lines[layer] = self.lines.get(layer, 0) + 1
        self.recs.append(rec); self.by_ident[(layer, rid)] = rec
        i = rec['i']
        for t in rules['_ties'].get(layer, []):
            v = tie_value(rec, t, rules)
            if v: self.tie_ix.setdefault((t['kind'], v), []).append(i)
        for k in record_name_keys(rec['names'], layer, rules): self.name_ix.setdefault(k, []).append(i)
        for n in rec['names']:
            kp = kind_place(n, rules)
            if kp: self.kp_ix.setdefault(kp, set()).add(i)
            for w in set(name_core(n, '', rules)): self.core_ix.setdefault(w, []).append(i)
            fn = full(n, rules)
            self.layer_name_ix.setdefault((layer, fn), set()).add(i)
            if piece_base(fn, rules) != fn: self.base_ix.setdefault((layer, piece_base(fn, rules)), set()).add(i)
        up = rules['unit_pieces'].get(layer)
        if up and not is_placeholder(attr(a, up['project_field']), rules): self.piece_ix.setdefault(piece_key(rec, up), []).append(i)


# ---------------------------------------------------------------------------------------------------------------- parks
def pin_of(p):
    """The park's pin (lat, lon), or None: missing, 0,0, or a place that cannot be (rule bad_pin)."""
    pin = p.get('pin') or []
    try:
        la, lo = float(pin[0]), float(pin[1])
    except (TypeError, ValueError, IndexError):
        return None
    return (la, lo) if pin_ok(la, lo) else None


def pin_ok(la, lo):
    """Rule bad_pin: a pin that cannot be a place (latitude outside -90..90, longitude outside -180..180, 0,0) is no pin
    (FACTS-AUDIT F2: CA-2456 Maple Lake WMA [100.856, -49.514])."""
    return -90 <= la <= 90 and -180 <= lo <= 180 and not (la == 0 and lo == 0)


def wmd_ok(p, rec, rules):
    """Rule wetland_district_fee: a wetland district takes only its fws fee-owned Waterfowl Production Areas."""
    if not rules['_wmd'].search(f"{p.get('name') or ''} {p.get('type') or ''}"): return True
    w = rules['wetland_district']
    return (rec['layer'] == w['layer'] and norm_val(attr(rec['a'], w['field'])) == w['fee']
            and norm_val(attr(rec['a'], w['type_field'])) == w['type'])


def other_park_name(p, rec, names_by_full, rules):
    """Rule other_park_name: True when the record's name is the full name of another park with a different name."""
    mine = full(p.get('name'), rules)
    return any(k and k != mine and k in names_by_full for k in (full(n, rules) for n in rec['names'] + rec['full_names']))


def pin_near(rec, pin, rules):
    """Rules name_needs_proof / name_pin_near_edge / thin_must_be_long: the pin is inside the record or within pin_m of its
    edge (a thin long strip: within its own mean width, at most pin_m)."""
    n, g = rules['numbers'], shape(rec)
    if rec.get('line'): return line_pin_near(rec, pin, rules)
    if pin is None or km_to_box(pin[0], pin[1], rec['_b']) * 1000 > n['pin_m']: return False
    if inside(pin[1], pin[0], g): return True
    return edge_m(pin[1], pin[0], g) <= (min(n['pin_m'], mean_width_m(g)) if too_thin(g, rules) else n['pin_m'])


def line_pin_near(rec, pin, rules):
    """Rule line_pin_m: the pin within line_pin_m (100 ft) of the line's nearest segment."""
    shape(rec)
    lim = rules['numbers']['line_pin_m']
    return pin is not None and km_to_box(pin[0], pin[1], rec['_b']) * 1000 <= lim and line_m(pin[1], pin[0], rec['_p']) <= lim


def pin_evidence(rec, pin):
    g = shape(rec)
    if rec.get('line'): return {'pin_near': rec['id'], 'pin_m': round(line_m(pin[1], pin[0], rec['_p']), 1)}
    return {'pin_in': rec['id']} if inside(pin[1], pin[0], g) else {'pin_near': rec['id'], 'pin_m': round(edge_m(pin[1], pin[0], g))}


def shape_km(rec, pin):
    """The pin's distance in km to the record's shape (0 inside)."""
    g = shape(rec)
    if rec.get('line'): return line_m(pin[1], pin[0], rec['_p']) / 1000.0
    return 0.0 if inside(pin[1], pin[0], g) else edge_m(pin[1], pin[0], g) / 1000.0


def holds_other_pin(ref, rec, same_name, parks, rules):
    """Rule other_park_pin: the record holds the pin of another park whose name, brackets aside, is this park's."""
    return any(pin_near(rec, pin_of(parks[o]), rules) for o in same_name if o != ref)


def name_shared_in_state(p, shared_names, rules):
    """Rule size_shared_name: two parks of the state share this name, so no size can pick between them."""
    return full(p.get('name'), rules) in shared_names


def size_witnesses(p, shared_names, rules):
    """Rule name_and_size: official sizes that may prove a name (tagged agency document, or a hand copy that names its page;
    an own-page clean total). None when two parks of the state share the name."""
    if name_shared_in_state(p, shared_names, rules): return []
    out, tags, op = [], set(rules['size_witness_tags']), rules['own_page']
    rows = [p.get('size')]
    pg, lk = p.get('page') or {}, p.get('link') or {}
    own = pg.get('own_page') == op['own'] and not pg.get('unofficial') and (not lk or str(lk.get('site') or '') in op['sites'])
    for s in pg.get('sizes') or []:
        if isinstance(s, dict) and not s.get('witness') and own and s.get('total') and s.get('clean'):
            rows.append(dict(s, witness=op['witness']))
    for s in rows:
        if not isinstance(s, dict) or s.get('witness') not in tags or s.get('witness_counts') is False: continue
        if s.get('witness') == op['hand_copy'] and not re.match(op['source_rx'], str(s.get('source_url') or '')): continue
        if s.get('as') is not None and s.get('witness') == op['witness']:
            ac = size_from_text(s['as'], rules)
            if ac is None: continue
        else:
            try: ac = float(s.get('acres'))
            except (TypeError, ValueError): continue
        if ac > 0: out.append(ac)
    return sorted(out)


def size_agrees(ac, witnesses, rules):
    """Rule name_and_size: the agency's acres within size_tol of an official size."""
    return bool(ac) and any(abs(ac - w) <= rules['numbers']['size_tol'] * w for w in witnesses)


def resolve_claims(claims, parks, rules):
    """Rule same_step_two_names: {record i: [refs]} -> the records claimed in one step by parks of two different names."""
    return {i for i, refs in claims.items() if len({nk(parks[r].get('name')) for r in refs}) > 1}


# ---------------------------------------------------------------------------------------------------------------- step 2
def id_records(pool, p, kind, value, rules, names_by_full, layer=None):
    """All of today's records that carry the park's id (one layer when given), with their project pieces, after the
    wetland district and other-name rules."""
    got = set(pool.tie_ix.get((kind, value), []))
    for i in list(got):
        up = rules['unit_pieces'].get(pool.recs[i]['layer'])
        if up: got.update(pool.piece_ix.get(piece_key(pool.recs[i], up), []))
    return [i for i in sorted(got) if (not layer or pool.recs[i]['layer'] == layer)
            and wmd_ok(p, pool.recs[i], rules) and not other_park_name(p, pool.recs[i], names_by_full, rules)]


def shared_ids(refs, parks, rules):
    """Rule id_shared: the ids two parks of the list claim (or that the link bot saw on two parks)."""
    count = {}
    for ref in refs:
        lk = parks[ref].get('link') or {}
        if lk.get('usable') and lk.get('id_value'):
            k = (lk.get('id_kind'), norm_val(lk['id_value']))
            count[k] = count.get(k, 0) + (2 if int(lk.get('id_shared_by') or 1) > 1 else 1)
    return {k for k, c in count.items() if c > 1}


def id_guard(p, rs, pool, rules):
    """Rule id_guard: an id join stands only when one of its records holds the pin or shares a real place word with the
    park's name (or its strong page name), and the nearest of its land is within near_km of the pin."""
    pin = pin_of(p)
    if pin is None: return False
    words = real_words(p.get('name'), rules) | real_words(page_name(p, rules), rules)
    recs = [pool.recs[i] for i in rs]
    ok = any(pin_near(r, pin, rules) for r in recs) or any(words & real_words(n, rules) for r in recs for n in r['names'])
    for r in sorted(recs, key=lambda r: km_to_box(pin[0], pin[1], rec_box(r))):
        if km_to_box(pin[0], pin[1], r['_b']) > rules['numbers']['near_km']: break
        if shape_km(r, pin) <= rules['numbers']['near_km']: return ok
    return False


def far_pin_waiver(p, rs, pool, rules, ref=''):
    """Rule id_far_pin_listed_states: the id guard's pin and near_km are waived when POTA lists the park in more than one state
    and one of the id's records (found through a real tie) carries the park's full name under the exact-name rules."""
    if len(p.get('listed_in') or []) < 2: return False
    return full_name_record(p, rs, pool, rules, ref)


def full_name_record(p, rs, pool, rules, ref=''):
    """Rules id_far_pin_listed_states / no_pin_proofs: one of the id's records carries the park's full name (exact rules,
    and its other spellings from the table other_spellings, rule name_other_spelling)."""
    keys = park_name_keys(p.get('name'), p.get('type'), rules) | other_spelling_keys(ref, rules)
    return any(keys & record_name_keys(pool.recs[i]['names'], pool.recs[i]['layer'], rules) for i in rs)


def piece_id_empty(rec, rules):
    """Rule id_unit_pieces: the record carries no real id under any tie of its layer, AND it meets every tie's where-filter
    (a PAD-US record not managed by NPS is not part of an NPS unit, even under the same name)."""
    for t in rules['_ties'].get(rec['layer'], []):
        if any(norm_val(attr(rec['a'], f)) != norm_val(w) for f, w in (t.get('where') or {}).items()): return False
        if tie_value(rec, t, rules): return False
    return True


def id_unit_pieces(p, ref, rs, ctx):
    """Rule id_unit_pieces: after an id proves the park, a record of the SAME layer under the same name as an id record, whose
    own id field is empty or a placeholder (never another real id), within near_km of the pin or of a joined piece, every
    refusal applied, joins as a piece of the unit. -> the extra records."""
    pool, rules, pin = ctx['pool'], ctx['rules'], pin_of(p)
    cands = set()
    for i in rs:
        rec = pool.recs[i]
        for n in rec['names']: cands |= pool.layer_name_ix.get((rec['layer'], full(n, rules)), set())
    cands = sorted(i for i in cands - set(rs)
                   if piece_id_empty(pool.recs[i], rules)
                   and not refusal(p, ref, pool.recs[i], i, dict(ctx, taken=set())))
    return [i for i in chain_pieces(cands, pin, pool, rules, seeds=list(rs)) if i not in rs] if cands and pin else []


def step_id(refs, ctx):
    """Step 2, rules id_tie / id_shared / id_guard / id_unit_pieces: -> ({ref: [record i]}, {ref: evidence}, {ref: note},
    {record i: True} for the pieces)."""
    parks, pool, rules, names_by_full = ctx['parks'], ctx['pool'], ctx['rules'], ctx['names_by_full']
    kinds = {t['kind'] for ts in rules['_ties'].values() for t in ts}
    shared = shared_ids(refs, parks, rules)
    want, ev, note, pieces = {}, {}, {}, set()
    for ref in refs:
        p = parks[ref]; lk = p.get('link') or {}
        if not (lk.get('id_kind') in kinds and lk.get('usable') and lk.get('id_value')): continue
        k = (lk['id_kind'], norm_val(lk['id_value']))
        if k in shared: note[ref] = 'id shared by two parks'; continue
        rs = id_records(pool, p, k[0], k[1], rules, names_by_full)
        if not rs: note[ref] = 'id not in the layer files'; continue
        far = False
        nopin = False
        if not id_guard(p, rs, pool, rules):
            if pin_of(p) is None and full_name_record(p, rs, pool, rules, ref): nopin = True
            elif not far_pin_waiver(p, rs, pool, rules, ref): note[ref] = 'id records carry neither the park\'s name nor its pin'; continue
            else: far = True
        extra = id_unit_pieces(p, ref, rs, ctx)
        pieces.update(extra)
        want[ref], ev[ref] = sorted(set(rs) | set(extra)), {'id_kind': k[0], 'id_value': k[1]}
        if far: ev[ref].update(far_pin=True, listed_in=list(p.get('listed_in') or []))
        if nopin: ev[ref]['no_pin'] = True
    claims = {}
    for ref, rs in want.items():
        for i in rs: claims.setdefault(i, []).append(ref)
    bad = resolve_claims(claims, parks, rules)
    out = {}
    for ref in sorted(want):
        rs = [i for i in want[ref] if i not in bad]
        if len(rs) < len(want[ref]): note[ref] = 'a record of this id is claimed by another park'
        if rs: out[ref] = rs
    return out, {r: ev[r] for r in out}, note, pieces


# ---------------------------------------------------------------------------------------------------------------- step 1
def lock_rows(pool, rs, value, rules):
    """The lock rows of one id-proven park: per layer, the record count, sorted names and acres (measured when no field)."""
    by = {}
    for i in rs: by.setdefault(pool.recs[i]['layer'], []).append(pool.recs[i])
    return [{'layer': lay, 'agency_id': value, 'count': len(recs), 'names': sorted({r['name'] for r in recs}),
             'acres': round(land_acres(recs, rules).get(lay, 0.0), 1)} for lay, recs in sorted(by.items())]


def acres_unchanged(old, new, tol):
    """Rule lock_zero_acres: no size both times = unchanged; a size on one side only = changed; both = within tol."""
    old, new = float(old or 0), float(new or 0)
    if old <= 0 and new <= 0: return True
    return old > 0 and new > 0 and abs(new - old) <= tol * old


def lock_reason(row, ref, ctx):
    """Rules lock_holds / lock_broken: '' when the lock row agrees with today's step 2; else ONE reason."""
    parks, refs, rules, pool = ctx['parks'], ctx['refs'], ctx['rules'], ctx['pool']
    if ref not in refs: return 'the park is no longer in the list'
    lk = parks[ref].get('link') or {}
    aid = norm_val(row.get('agency_id'))
    if not lk.get('id_value') or norm_val(lk.get('id_value')) != aid: return "the park's page id changed or is missing"
    if (lk.get('id_kind'), aid) in ctx['shared']: return 'id now claimed by a second park'
    if not any(pool.recs[i]['layer'] == row.get('layer') for i in pool.tie_ix.get((lk.get('id_kind'), aid), [])):
        return "id not in today's file"
    if ref not in ctx['today']: return 'step 2 no longer proves it: ' + ctx['notes'].get(ref, 'no record of the id is left')
    now = next((x for x in ctx['today'][ref] if x['layer'] == row.get('layer')), None)
    if now is None or now['count'] != row.get('count'): return 'record count changed'
    if now['names'] != sorted(row.get('names') or []): return 'record renamed'
    if not acres_unchanged(row.get('acres'), now['acres'], rules['numbers']['lock_acres_tol']): return 'size changed'
    return ''


def compare_locks(locks, ctx):
    """Step 1 (the witness): -> ({ref: 'held' | 'broken'}, [locked_broken rows]). Never changes a join."""
    status, broken = {}, []
    for ref in sorted(locks):
        for row in sorted(locks[ref] or [{}], key=lambda r: str(r.get('layer'))):
            why = lock_reason(row, ref, ctx)
            if why:
                broken.append({'ref': ref, 'layer': row.get('layer'), 'agency_id': row.get('agency_id'), 'why': str(why)})
        status[ref] = 'broken' if any(b['ref'] == ref for b in broken) else 'held'
    return status, broken


# ---------------------------------------------------------------------------------------------------------------- step 3
def is_office(rec, rules):
    """Rule office."""
    return any(rules['_office_rx'].search(n) for n in rec['names'])


def is_water(p, rec, rules):
    """Rule water_only: a lake or pond record, unless the park is a lake or river park or the agency files the record under
    the park's own kind."""
    kind = full(p.get('type'), rules)
    last = (full(rec['name'], rules).split() or [''])[-1]
    same_kind = bool(kind) and any(full(n, rules).endswith(' ' + kind) for n in rec['full_names'])
    return last in rules['water_last_words'] and not rules['_water_park_kind_rx'].search(str(p.get('type') or '')) and not same_kind


def is_easement(rec, rules):
    """Rule easement_by_name: a record whose type field says easement, or whose name says lease or agreement."""
    return any(rules['_easement_rx'].search(str(v)) for k, v in rec['a'].items() if rules['_type_field_rx'].match(str(k)) and v not in (None, '')) \
        or any(rules['_lease_name_rx'].search(n) for n in rec['names'])


def not_fee_interest(rec, rules):
    """Rule fws_interest_by_name: a Fish and Wildlife record whose interest type is not fee-owned (E easement, R, A ...)."""
    f = rules['interest_fields'].get(rec['layer'])
    return bool(f) and norm_val(attr(rec['a'], f['field'])) not in f['fee']


def held_by_stronger(i, taken):
    """Rule stronger_step_wins: the record is held by an id."""
    return i in taken


def line_kind_ok(p, rules):
    """Rule line_by_name_kind: only a trail / river / route park may take a line by NAME (any park may by id)."""
    return bool(rules['_line_park_kind_rx'].search(str(p.get('type') or '')))


def refusal(p, ref, rec, i, ctx):
    """Why a named record may not join this park by a NAME rule ('' = it may)."""
    rules = ctx['rules']
    if rec.get('line') and not line_kind_ok(p, rules): return 'line_kind'
    if not wmd_ok(p, rec, rules): return 'not_fee'
    if is_office(rec, rules): return 'office'
    if is_water(p, rec, rules): return 'water'
    if is_easement(rec, rules) or not_fee_interest(rec, rules): return 'easement'
    if other_park_name(p, rec, ctx['names_by_full'], rules): return 'other_name'
    if holds_other_pin(ref, rec, ctx['same_name'].get(full(p.get('name'), rules), ()), ctx['parks'], rules): return 'other_pin'
    return 'held' if held_by_stronger(i, ctx['taken']) else ''


def chain_pieces(cands, pin, pool, rules, seeds=()):
    """Rule far_pieces (records grouped by NAME alone; a unit group is whole, rule unit_at_any_distance): of same-name records, only those within near_km of the pin (to the shape) or of a piece already
    taken (box to box, a chain) are pieces of one group."""
    near = rules['numbers']['near_km']
    got = [i for i in seeds] + [i for i in cands if i not in seeds and km_to_box(pin[0], pin[1], rec_box(pool.recs[i])) <= near
                                and shape_km(pool.recs[i], pin) <= near]
    left = [i for i in cands if i not in got]
    k = 0
    while k < len(got):
        b = rec_box(pool.recs[got[k]])
        near_ones = [i for i in left if box_gap_km(b, rec_box(pool.recs[i])) <= near]
        got += near_ones
        left = [i for i in left if i not in near_ones]
        k += 1
    return sorted(set(got))


def unit_value(rec, rules):
    """Rule unit_at_any_distance: the record's unit (the first of the layer's unit_fields that is not a placeholder), '' if none."""
    for f in rules['unit_fields'].get(rec['layer'], []):
        v = attr(rec['a'], f)
        if not is_placeholder(v, rules): return norm_val(v)
    return ''


def bilingual_aliases(keys, pool, rules):
    """Rule bilingual_name: a record that carries BOTH an English and a French name in its own fields (bilingual_fields),
    one of them the park's name under the exact rules, makes the other one a name of the park too. No translation tables."""
    out = set()
    for i in {i for k in keys for i in pool.name_ix.get(k, [])}:
        rec = pool.recs[i]
        for e, f in rules['bilingual_fields'].get(rec['layer'], []):
            ve, vf = attr(rec['a'], e), attr(rec['a'], f)
            if is_placeholder(ve, rules) or is_placeholder(vf, rules): continue
            fe, ff = name_forms(str(ve), rules), name_forms(str(vf), rules)
            if fe & keys and not generic(str(vf), rules): out |= ff
            if ff & keys and not generic(str(ve), rules): out |= fe
    return out - keys


def no_pin_group(rs):
    """Rule no_pin_proofs: a park with no pin keeps its whole named group; only a size or two sources can prove it."""
    return list(rs)


def name_groups(p, ref, ctx):
    """Step 3 search for one park: -> (groups {gkey: [record i]}, notes set)."""
    pool, rules, pin, notes = ctx['pool'], ctx['rules'], pin_of(p), set()
    keys = park_name_keys(p.get('name'), p.get('type'), rules) | other_spelling_keys(ref, rules)   # 27 Nov 2026: other spellings
    keys |= bilingual_aliases(keys, pool, rules)
    own = {i for k in keys for i in pool.name_ix.get(k, [])}
    page = {i for k in page_name_keys(p, rules) for i in pool.name_ix.get(k, [])} - own
    lang = {i for kp in {kind_place(n, rules) for n in (p.get('name'),)} - {None} for i in pool.kp_ix.get(kp, ())} - own - page
    groups = {}
    for i in sorted(own | page | lang):
        rec = pool.recs[i]
        no = refusal(p, ref, rec, i, ctx)
        if no: notes.add(no); continue
        uv = unit_value(rec, rules)
        src = 'page' if i in page else 'lang' if i in lang else 'name'
        groups.setdefault((rec['layer'], 'unit', uv, src) if uv else (rec['layer'], 'name', full(rec['name'], rules), src), []).append(i)
    out = {}
    for g, rs in groups.items():
        got = (rs if g[1] == 'unit' else chain_pieces(rs, pin, pool, rules)) if pin else no_pin_group(rs)
        if len(got) < len(rs): notes.add('far')
        if got: out[g] = got
    return out, notes


def group_acres(rs, pool, rules):
    """Rule acres_any_layer: the group's own layer total of agency acres (after the no-double-count rules); 0 when any piece
    has no agency acres."""
    if not all(agency_acres(pool.recs[i], rules) for i in rs): return 0.0
    return max(land_acres([pool.recs[i] for i in rs], rules, agency_only=True).values())


def prove_group(p, rs, pool, rules, witnesses):
    """-> ('name+pin', evidence) or ('name+size', evidence) or None."""
    pin = pin_of(p)
    for i in rs:
        if pin_near(pool.recs[i], pin, rules): return 'name+pin', pin_evidence(pool.recs[i], pin)
    if pin is not None and min(shape_km(pool.recs[i], pin) for i in rs) > rules['numbers']['near_km']: return None
    ac = group_acres(rs, pool, rules)
    return ('name+size', {'agency_acres': round(ac, 1), 'official_acres': witnesses}) if size_agrees(ac, witnesses, rules) else None


def two_sources_ok(a, b, rules):
    """Rule name_two_sources: two named records of different layers, boxes overlapping, agency sizes within two_sources_tol."""
    sa, sb = agency_acres(a, rules) or 0, agency_acres(b, rules) or 0
    return a['layer'] != b['layer'] and other_services(a, b) and box_share(a['_b'], b['_b']) > 0 and sa > 0 and sb > 0 \
        and abs(sa - sb) <= rules['numbers']['two_sources_tol'] * max(sa, sb)


def two_sources(p, groups, pool, rules):
    """{group: ('name+two_sources', evidence)} for the named pairs that agree, near the pin."""
    pin, out = pin_of(p), {}
    named = [(g, pool.recs[i]) for g in sorted(groups) for i in groups[g]
             if pin is None or km_to_box(pin[0], pin[1], rec_box(pool.recs[i])) <= rules['numbers']['near_km']]
    for x, (ga, a) in enumerate(named):
        for gb, b in named[x + 1:]:
            if two_sources_ok(a, b, rules):
                e = {'source_a': a['id'], 'acres_a': agency_acres(a, rules), 'source_b': b['id'], 'acres_b': agency_acres(b, rules)}
                out.setdefault(ga, ('name+two_sources', e)); out.setdefault(gb, ('name+two_sources', e))
    return out


def ambiguous_sizes(sized):
    """Rule two_records_fit: groups of one layer that prove only by size or two sources, two or more of them."""
    layers = [g[0] for g in sized]
    return {g for g in sized if layers.count(g[0]) > 1}


def name_core(t, typ, rules):
    """v1 name_core (PR #390 rule 5): the possessive-as-one-word name, the park's kind taken off the end, an 'and ...' tail
    set aside (after 2+ words), kind words out. () when no real place word is left."""
    s = full_ps(t, rules)
    ty = full(typ, rules) if typ else ''
    if ty and s.endswith(' ' + ty): s = s[:-len(ty) - 1]
    w = s.split()
    if 'and' in w and w.index('and') >= 2: w = w[:w.index('and')]
    w = [x for x in w if x not in rules['_kind_words'] and x not in rules['core_drop']]
    return tuple(w) if any(len(x) >= rules['numbers']['place_word_len'] and x not in rules['_place_words'] for x in w) else ()


def kinds_of(text, rules):
    """v1 kinds: the kind codes a name carries ('sp', 'wma', 'snp', ...)."""
    t = str(text or '').lower()
    return {k for k, rx in rules['_kinds'] if rx.search(t)}


def core_records(p, ref, ctx):
    """Rule name_longer_or_shorter (v1, PR #390 rule 5), tried only when the exact names proved nothing: a record holding the
    pin whose core name is the park's (kinds compatible), or begins with the park's core of 2+ words, or holds 75% of a core of
    3+ words (one word longer at most); the last two need a kind in common; the record's extra words may not be a water word.
    -> ({group: (by, evidence)}, {group: [record i]})."""
    pool, rules = ctx['pool'], ctx['rules']
    pin, pc = pin_of(p), name_core(p.get('name'), p.get('type'), rules)
    if pin is None or not pc: return {}, {}
    pk = kinds_of(p.get('name'), rules) | kinds_of(p.get('type'), rules)
    miss = len(pc) - math.ceil(0.75 * len(pc)) if len(pc) >= 3 else 0
    found = set()
    for w in sorted(set(pc), key=lambda w: (len(pool.core_ix.get(w, ())), w))[:miss + 1]: found |= set(pool.core_ix.get(w, ()))
    proofs, groups = {}, {}
    for i in sorted(found):
        rec = pool.recs[i]
        if rec.get('line') or not pin_near(rec, pin, rules) or refusal(p, ref, rec, i, ctx): continue
        rk, ok = pool.rec_kinds(rec), False
        for n in rec['names']:
            rc = name_core(n, '', rules)
            if not rc or any(x in rules['water_last_words'] for x in rc if x not in pc): continue
            ok = ok or (rc == pc and (not (rk and pk) or bool(rk & pk))) \
                or (len(pc) >= 2 and rc[:len(pc)] == pc and bool(rk & pk)) \
                or (len(pc) >= 3 and bool(rk & pk) and sum(1 for x in pc if x in rc) >= 0.75 * len(pc) and len(rc) <= len(pc) + 1)
        if ok:
            g = (rec['layer'], 'core', rec['id'], 'name')
            proofs[g], groups[g] = ('longer or shorter name+pin', pin_evidence(rec, pin)), [i]
    return proofs, groups


def suffix_pieces(p, ref, rs, ctx):
    """Rule piece_suffix: records of the same layer whose name is a joined record's name but for a trailing piece word (East,
    Unit 2, a number ...), within near_km of the pin or of a joined piece, every refusal applied. Never across layers."""
    pool, rules, pin = ctx['pool'], ctx['rules'], pin_of(p)
    cands = set()
    for i in rs:
        rec = pool.recs[i]
        for n in rec['names']:
            base = piece_base(full(n, rules), rules)
            if not generic(base, rules): cands |= pool.base_ix.get((rec['layer'], base), set())
    cands = sorted(i for i in cands - set(rs) if not refusal(p, ref, pool.recs[i], i, ctx))
    return chain_pieces(cands, pin, pool, rules, seeds=list(rs)) if cands and pin else list(rs)


def is_trail(p, rules):
    """Rule trail_layer_not_in_store: a trail park."""
    return bool(rules['_trail_kind_rx'].search(f"{p.get('type') or ''} {p.get('name') or ''}"))


def reason_for(p, groups, notes, twice, rules):
    """Step 4: the one pin-only reason code for a park step 3 could not prove (fixed list)."""
    if twice: return 'two_records_fit'
    if groups and pin_of(p) is None: return 'park_has_no_pin'
    if groups: return 'name_but_no_pin_or_size_proof'
    if notes & {'held', 'other_name', 'other_pin'}: return 'record_shared_with_another_park'
    if 'water' in notes: return 'water_only'
    if 'office' in notes: return 'office_only'
    if notes & {'far', 'not_fee', 'easement'}: return 'name_but_no_pin_or_size_proof'
    return 'record_layer_not_in_store' if is_trail(p, rules) else 'no_record_with_this_name'


BY_ORDER = ('name+pin', 'name+size', 'name+two_sources', 'page name+pin', 'page name+size', 'page name+two_sources',
            'two-language name+pin', 'two-language name+size', 'two-language name+two_sources', 'longer or shorter name+pin')


def step_name(refs, ctx):
    """Step 3 for all parks: -> ({ref: [record i]}, {ref: (by, evidence)}, {ref: reason code})."""
    parks, pool, rules = ctx['parks'], ctx['pool'], ctx['rules']
    want, ev, why = {}, {}, {}
    for ref in refs:
        p = parks[ref]
        groups, notes = name_groups(p, ref, ctx)
        wit = size_witnesses(p, ctx['shared_names'], rules)
        pinned, sized = {}, {}
        for g in sorted(groups):
            r = prove_group(p, groups[g], pool, rules, wit)
            if r: (pinned if r[0] == 'name+pin' else sized)[g] = r
        sized.update(two_sources(p, {g: rs for g, rs in groups.items() if g not in pinned and g not in sized}, pool, rules))
        page = lambda d: {g: ({'page': 'page ', 'lang': 'two-language '}.get(g[3], '') + v[0], v[1]) for g, v in d.items()}
        pinned, sized = page(pinned), page(sized)
        twice = ambiguous_sizes(sized)
        proven = {**pinned, **{g: v for g, v in sized.items() if g not in twice}}
        if not proven:
            proven, more = core_records(p, ref, ctx)
            groups = {**groups, **more}
        if proven:
            want[ref] = {g: suffix_pieces(p, ref, groups[g], ctx) for g in proven}
            ev[ref] = proven
        else:
            why[ref] = reason_for(p, groups, notes, twice, rules)
    claims = {}
    for ref, gs in want.items():
        for i in {i for rs in gs.values() for i in rs}: claims.setdefault(i, []).append(ref)
    bad = resolve_claims(claims, parks, rules)
    out, by = {}, {}
    for ref in sorted(want):
        gs = {g: rs for g, rs in want[ref].items() if not bad & set(rs)}
        if not gs:
            why[ref] = 'record_shared_with_another_park'; continue
        out[ref] = sorted({i for rs in gs.values() for i in rs})
        best = next(k for k in BY_ORDER if k in {ev[ref][g][0] for g in gs})
        by[ref] = (best, {'proofs': [dict(ev[ref][g][1], by=ev[ref][g][0], layer=g[0]) for g in sorted(gs)]})
    return out, by, why


def match_state(refs, parks, pool, rules, locks=None):
    """Steps 2-4 for one state, then the lock witness. -> {'joins', 'how', 'why', 'id_notes', 'locks_out', 'lock_status',
    'locked_broken'}."""
    names_by_full, cnt = {}, {}
    for ref, p in parks.items(): names_by_full.setdefault(full(p.get('name'), rules), set()).add(ref)
    for ref in refs: cnt[full(parks[ref].get('name'), rules)] = cnt.get(full(parks[ref].get('name'), rules), 0) + 1
    same_name = {k: sorted(v) for k, v in names_by_full.items() if len(v) > 1}
    ctx = {'parks': parks, 'refs': set(refs), 'pool': pool, 'rules': rules, 'names_by_full': names_by_full,
           'same_name': same_name, 'shared_names': {k for k, c in cnt.items() if c > 1}}
    ctx['taken'] = set()
    got, ev, notes, pieces = step_id(refs, ctx)
    joins = dict(got)
    how = {ref: (2, 'id', ev[ref]) for ref in got}
    ctx['taken'] = {i for rs in got.values() for i in rs}
    got3, by, why = step_name([r for r in refs if r not in joins], ctx)
    for ref, rs in got3.items(): joins[ref], how[ref] = rs, (3, by[ref][0], by[ref][1])
    today = {ref: lock_rows(pool, joins[ref], how[ref][2]['id_value'], rules) for ref in sorted(joins) if how[ref][0] == 2}
    ctx.update(today=today, notes=notes, shared=shared_ids(refs, parks, rules))
    status, broken = compare_locks(locks or {}, ctx)
    return {'joins': joins, 'how': how, 'why': {r: c for r, c in why.items() if r not in joins}, 'locks_out': today, 'pieces': pieces,
            'lock_status': status, 'locked_broken': broken}


# ---------------------------------------------------------------------------------------------------------------- gate
def gate_old_ids(doc_parks):
    """Rule gate_old: no record id ends in ~old."""
    return [('old_ids', ref, str(x[0])) for ref, p in sorted(doc_parks.items()) for x in (p.get('m') or []) + (p.get('c') or [])
            if str(x[0]).endswith('~old')]


def gate_two_names(doc_parks):
    """Rule gate_two_name: no record id on two parks under two names (record names, and POTA's park names with brackets)."""
    by_id = {}
    for ref, p in sorted(doc_parks.items()):
        for x in p.get('m') or []:
            if nk(x[1]):
                v = by_id.setdefault(str(x[0]), (set(), set())); v[0].add(nk(x[1])); v[1].add(nk(p.get('n')))
    return [('two_name', i, ' / '.join(sorted(v[1]))) for i, v in sorted(by_id.items()) if len(v[0]) > 1 or len(v[1]) > 1]


def gate_unresolved(res, pool):
    """Rule gate_not_in_file: every id written in a key row resolves to exactly one raw record of today's file."""
    bad = []
    for ref, rs in sorted(res['joins'].items()):
        for i in rs:
            rec = pool.recs[i] if isinstance(i, int) and 0 <= i < len(pool.recs) else None
            raw = pool.raw_ids.get((rec['area'], rec['layer'], rec['id'])) if rec else None
            if not raw or len(raw) != 1 or raw[0] != rec['key']: bad.append(('not_in_file', ref, str(rec['id'] if rec else i)))
    return bad


def gate_id_mismatch(res, pool, rules):
    """Rule gate_id_mismatch: every id-proven park's records carry that id (or are project pieces of one that does)."""
    bad = []
    for ref, rs in sorted(res['joins'].items()):
        step, by, e = res['how'][ref]
        if by != 'id': continue
        ties = [t for ts in rules['_ties'].values() for t in ts if t['kind'] == e.get('id_kind')]
        carry = [pool.recs[i] for i in rs if any(t['layer'] == pool.recs[i]['layer'] and tie_value(pool.recs[i], t, rules) == e.get('id_value')
                                                for t in ties)]
        pieces = {piece_key(r, rules['unit_pieces'][r['layer']]) for r in carry if r['layer'] in rules['unit_pieces']}
        for i in rs:
            rec = pool.recs[i]
            up = rules['unit_pieces'].get(rec['layer'])
            named = {(r['layer'], full(r['name'], rules)) for r in carry}
            loose = i in res.get('pieces', ()) and (rec['layer'], full(rec['name'], rules)) in named and \
                not any(tie_value(rec, t, rules) for t in rules['_ties'].get(rec['layer'], []))
            if rec not in carry and not (up and piece_key(rec, up) in pieces) and not loose: bad.append(('id_mismatch', ref, rec['id']))
    return bad


def gate_other_pin(res, parks, pool, rules):
    """Rule gate_other_park_pin: no record of a name-proven park holds the pin of another park whose name, brackets aside,
    is the same (checked here on its own, so the gate catches a step rule that regresses)."""
    by_name = {}
    for ref, p in parks.items(): by_name.setdefault(full(p.get('name'), rules), []).append(ref)
    bad = []
    for ref, rs in sorted(res['joins'].items()):
        if res['how'][ref][0] != 3: continue
        others = [o for o in by_name.get(full(parks[ref].get('name'), rules), []) if o != ref and pin_of(parks[o])]
        for i in rs:
            for o in others:
                g, pin, r = shape(pool.recs[i]), pin_of(parks[o]), pool.recs[i]
                if (r.get('line') and line_m(pin[1], pin[0], r['_p']) <= rules['numbers']['line_pin_m']) or \
                        (not r.get('line') and km_to_box(pin[0], pin[1], r['_b']) * 1000 <= rules['numbers']['pin_m'] and
                         (inside(pin[1], pin[0], g) or edge_m(pin[1], pin[0], g) <= rules['numbers']['pin_m'])):
                    bad.append(('other_park_pin', ref, f"{pool.recs[i]['id']} holds {o}'s pin"))
    return bad


def gate_licence(res, pool):
    """Rule licence_kept: every joined record carries a publishable value read from today's file, and every private one its
    licence class (a record may prove a match privately; it may never lose its terms)."""
    bad = []
    for ref, rs in sorted(res['joins'].items()):
        for i in rs:
            if not 0 <= i < len(pool.recs): continue   # not_in_file reports it
            r = pool.recs[i]
            if not isinstance(r.get('pub'), bool): bad.append(('licence_kept', ref, f"{r['id']} has no publishable value"))
            elif not r['pub'] and not r.get('lic'): bad.append(('licence_kept', ref, f"{r['id']} is private with no licence class"))
    return bad


def gate(doc_parks, res, pool, rules, parks=None):
    """Step 5: the hard stop. -> {'ok', 'old_ids', 'two_name', 'not_in_file', 'id_mismatch', 'other_park_pin', 'bad'}."""
    bad = gate_old_ids(doc_parks) + gate_two_names(doc_parks) + gate_unresolved(res, pool) + gate_id_mismatch(res, pool, rules) \
        + (gate_other_pin(res, parks, pool, rules) if parks else []) + gate_licence(res, pool)
    out = {k: sum(1 for b in bad if b[0] == k) for k in ('old_ids', 'two_name', 'not_in_file', 'id_mismatch', 'other_park_pin', 'licence_kept')}
    out['ok'], out['bad'] = not bad, [list(b) for b in bad]
    return out


# ---------------------------------------------------------------------------------------------------------------- outputs
def may_show(rec):
    """Rule licence_kept: a record may be shown only when today's file says publishable true (no value = not: fail closed)."""
    return rec.get('pub') is True


def share_of(recs):
    """Rule licence_kept: 'all' (every joined record may be shown), 'none' (proven only on private records), else 'part'."""
    n = sum(1 for r in recs if may_show(r))
    return 'all' if n == len(recs) else 'none' if n == 0 else 'part'


def all_lines(recs):
    """Rule key_line_flag: every joined record is a line, so the map draws a line."""
    return bool(recs) and all(r.get('line') for r in recs)


def shape_word(rec):
    """Rule proof_shape_column: 'line' or 'area' for the proof file."""
    return 'line' if rec.get('line') else 'area'


def state_doc(st, refs, parks, res, pool, rules, layer_files, area=None, gaps=()):
    """The key, in the shape the PC diff tool reads. Never shows the lock (rule lock_is_witness)."""
    out = {}
    for ref in refs:
        p = parks[ref]
        if ref in res['joins']:
            step, by, e = res['how'][ref]
            tag = f"id {e.get('id_kind')} {e.get('id_value')}" if by == 'id' else by
            rows = sorted(([pool.recs[i]['id'], pool.recs[i]['name'], round(rec_acres(pool.recs[i], rules)),
                            'piece of id unit' if i in res.get('pieces', ()) else tag]
                           for i in res['joins'][ref]), key=lambda x: (-x[2], str(x[0])))
            per = land_acres([pool.recs[i] for i in res['joins'][ref]], rules)
            e = dict(e, ac_how='largest layer total', acres_by_layer={k: round(v) for k, v in sorted(per.items())})
            out[ref] = {'n': p.get('name'), 't': p.get('type'), 'm': rows, 'c': [],
                        'match': {'status': 'confirmed', 'by': by, 'step': step, 'evidence': e, 'why': None},
                        'ac': round(max(per.values())), 'src': sorted(per)}
            if all_lines([pool.recs[i] for i in res['joins'][ref]]): out[ref]['line'] = True
            recs = [pool.recs[i] for i in res['joins'][ref]]
            out[ref]['share'] = share_of(recs)
            out[ref]['private'] = sorted({r['id'] for r in recs if not may_show(r)})
        else:
            out[ref] = {'n': p.get('name'), 't': p.get('type'), 'm': [], 'c': [], 'ac': None, 'src': [],
                        'match': {'status': 'pin', 'by': None, 'step': 4, 'evidence': {}, 'why': res['why'].get(ref, 'no_record_with_this_name')}}
    steps = {'id': sum(1 for h in res['how'].values() if h[0] == 2), 'name': sum(1 for h in res['how'].values() if h[0] == 3)}
    n = len(res['joins'])
    doc = {'v2': 1, 'st': st, 'made': layer_files[area or f'US-{st}']['made'], 'tool': rules.get('_tool', TOOL) + gap_note(gaps),
           'layer_files': layer_files,
           'counts': {'parks': len(refs), 'outlined': n, 'confirmed': n, 'pin_only': len(refs) - n, 'by_step': steps}, 'parks': out}
    if gaps: doc['gaps'] = list(gaps)
    return doc


def gap_note(gaps):
    """Rule load_complete: a key built with a store-room gap says so on its tool line."""
    return ' (store gap)' if gaps else ''


def key_text(obj):
    """The key's JSON text: sorted keys, no spaces, UTF-8."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def key_text_sha256(obj):
    """Rule key_text_sha256: the sha256 of the key's uncompressed text, so two machines (two zlib builds) compare by content."""
    return hashlib.sha256(key_text(obj)).hexdigest()


def gz_bytes(obj):
    """JSON with sorted keys in a gzip with a fixed time, so the same inputs give the same bytes (rule same_in_same_out)."""
    raw = key_text(obj)
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb', mtime=0, filename='') as g: g.write(raw)
    return buf.getvalue()


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def proof_rows(st, res, pool, rules):
    out = []
    for ref in sorted(res['joins']):
        step, by, e = res['how'][ref]
        lock = res['lock_status'].get(ref, 'new') if step == 2 else ''
        for i in res['joins'][ref]:
            rec = pool.recs[i]
            out.append([ref, st, rec['key'], rec['id'] if rec['agency'] else '', rec['layer'], rec['name'], round(rec_acres(rec, rules), 1),
                        step, by, ' '.join(f'{k}={e[k]}' for k in sorted(e)), rec['area'], lock, shape_word(rec),
                        '' if rec.get('pub') is None else str(rec['pub']).lower(), rec.get('lic') or ''])
    return out


def id_other_names(st, res, parks, pool, rules):
    """Rule id_other_names_report: id-joined records that share no real place word with the park's name (changes no join)."""
    out = []
    for ref in sorted(res['joins']):
        if res['how'][ref][0] != 2: continue
        p, pin = parks[ref], pin_of(parks[ref])
        words = real_words(p.get('name'), rules)
        for i in res['joins'][ref]:
            rec = pool.recs[i]
            if not any(words & real_words(n, rules) for n in rec['names']):
                out.append([ref, st, p.get('name'), rec['id'], rec['name'], rec['layer'], round(shape_km(rec, pin), 2) if pin else ''])
    return out


def write_csv(path, head, rows):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, lineterminator='\n'); w.writerow(head); w.writerows(rows)


def clear_old_outputs(out, area):
    """Rule stale_outputs_removed: an area's old key and lock file leave --out before it is built."""
    for p in (os.path.join(out, f'{area}.json.gz'), os.path.join(out, 'locks', f'{area}.json')):
        if os.path.exists(p): os.remove(p)
    return True


# ---------------------------------------------------------------------------------------------------------------- run
def slim_record(r, rules):
    """Rule memory: one layer record as the steps use it: key, layer, name, q, the shape as compact integer arrays, and only
    the attributes some step reads (never the whole attributes dict)."""
    memo = rules.setdefault('_keep_memo', {})
    a = r.get('attributes') or {}
    out = {k: r[k] for k in ('key', 'layer', 'record_name', 'q', 'shape', 'publishable', 'licence_class', 'publish_why') if k in r}
    keep = {}
    for k, v in a.items():
        ok = memo.get(k)
        if ok is None:
            t = str(k)
            ok = memo[k] = t.lower() in rules['_keep'] or bool(rules['_acre_field_rx'].search(t) or rules['_type_field_rx'].match(t))
        if ok: keep[k] = v
    out['attributes'] = keep
    for g in ('rings', 'paths'):
        v = r.get(g)
        if isinstance(v, str):
            try: v = json.loads(v)
            except ValueError: v = None
        if v: out[g] = [compact(x) for x in v]
    return out


def compact(ring):
    """A ring's integers as an array (4 bytes each when they fit, else 8) instead of a list of Python ints."""
    if type(ring) is not list: return ring
    try: return array.array('i', ring)
    except OverflowError: return array.array('q', ring)
    except TypeError: return ring


def read_layer_file(path, rules):
    """Rule memory: read a layer file as a stream, record by record (the records list comes last in the file), keeping each
    record slim. -> {'made', 'manifest', ..., 'records': [slim records]}."""
    dec, tag, recs = json.JSONDecoder(), '"records":[', []
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        buf, eof = '', False
        while tag not in buf and not eof:
            c = f.read(1 << 20); buf += c; eof = not c
        if tag not in buf:
            d = json.loads(buf)
            d['records'] = [slim_record(r, rules) for r in d.get('records') or []]
            return d
        i = buf.index(tag)
        head = json.loads(buf[:i] + '"records":[]}')
        pos = i + len(tag)
        while True:
            while pos < len(buf) and buf[pos] in ' \t\r\n,': pos += 1
            if pos < len(buf) and buf[pos] == ']': pos += 1; break
            try:
                if pos >= len(buf): raise ValueError('need more')
                obj, pos = dec.raw_decode(buf, pos)
                recs.append(slim_record(obj, rules))
                if pos > 1 << 20: buf, pos = buf[pos:], 0
            except ValueError:
                if eof: raise
                c = f.read(1 << 20); eof = not c; buf = buf[pos:] + c; pos = 0
        tail = (buf[pos:] + f.read()).strip()
    if tail.startswith(','): head.update(json.loads('{' + tail[1:]))
    head['records'] = recs
    return head


def read_gz_json(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f: return json.load(f)


def area_of(token):
    """Rule areas: 'MN' -> 'US-MN'; 'US-MN' and 'CA-ON' stay as they are."""
    t = str(token or '').strip().upper()
    return t if re.fullmatch(r'[A-Z]{2}-[A-Z]{2}', t) else f'US-{t}'


def area_label(area):
    """The short name an area goes by in the key and the csv files: 'MN' for US-MN (as before), 'CA-ON' for Canada."""
    return area[3:] if area.startswith('US-') else area


def area_neighbours(area, rules):
    """Rule areas: the neighbour areas whose layer files are read too (US states: neighbours; provinces: ca_neighbours)."""
    cc, code = area[:2], area[3:]
    table = rules['neighbours'] if cc == 'US' else rules['ca_neighbours'] if cc == 'CA' else {}
    return [f'{cc}-{x}' for x in sorted(table.get(code, '').split())]


def park_list(repo, area):
    """The area's park list: POTA's own saved list (data/pota/saved/parks/<AREA>.json.gz), the same one the legacy key reads."""
    d = read_gz_json(os.path.join(repo, 'data', 'pota', 'saved', 'parks', f'{area_of(area)}.json.gz'))
    return sorted({str(x.get('reference')) for x in d.get('data') or [] if x.get('reference')})


def park_states(repo, area):
    """Rule id_far_pin_listed_states: {ref: [states]} from POTA's own list (each row's locationDesc, e.g. 'US-CT,US-GA,...')."""
    d = read_gz_json(os.path.join(repo, 'data', 'pota', 'saved', 'parks', f'{area_of(area)}.json.gz'))
    return {str(x['reference']): sorted({t.strip() for t in str(x.get('locationDesc') or '').split(',') if t.strip()})
            for x in d.get('data') or [] if x.get('reference')}


def rules_for_area(rules, area):
    """Rules ca_kind_words / two_language_kind: a Canadian area also counts the Canadian / French kind words (Provincial, Parc,
    Réserve ...) and reads names through the two-language kind table."""
    if not area.startswith('CA-'): return rules
    r = dict(rules, _kind_words=rules['_kind_words'] | {full(w, rules) for w in rules['ca_kind_words']})
    small = {full(w, rules) for w in r['lang_small_words']} - {''}
    words = lambda ph: tuple(x for x in full(ph.replace('\u2019', "'"), r).split() if x not in small)
    kinds = [(k['kind'], 'fr', words(ph)) for k in r['lang_kinds'] for ph in k['fr']] + \
            [(k['kind'], 'en', words(ph)) for k in r['lang_kinds'] for ph in k['en']]
    r['_lang'] = {'small': small, 'kinds': sorted(kinds, key=lambda x: -len(x[2]))}
    return r


def kind_place(name, rules):
    """Rule two_language_kind: (kind, place words) of a name: a French kind at its start and / or an English kind at its end
    (from lang_kinds; both must be the same kind), the rest its place words, accents and the small joining words of both
    languages (lang_small_words) set aside. Place words are never translated. None without a kind or a real place word."""
    lg = rules.get('_lang')
    if not lg: return None
    w = tuple(x for x in full(str(name or '').replace('\u2019', "'").replace('\u2018', "'"), rules).split() if x not in lg['small'])
    ks = next((k for k, side, ph in lg['kinds'] if side == 'fr' and len(w) > len(ph) and w[:len(ph)] == ph), None)
    if ks: w = w[len(next(ph for k, side, ph in lg['kinds'] if k == ks and side == 'fr' and w[:len(ph)] == ph)):]
    ke = next((k for k, side, ph in lg['kinds'] if side == 'en' and len(w) > len(ph) and w[-len(ph):] == ph), None)
    if ke: w = w[:-len(next(ph for k, side, ph in lg['kinds'] if k == ke and side == 'en' and w[-len(ph):] == ph))]
    if (ks and ke and ks != ke) or not (ks or ke) or not w or generic(' '.join(w), rules): return None
    return (ks or ke, w)




def build_state(area, a, rules, facts, layer_file, info):
    """One area: load, match, gate, write. -> (exit code, proof rows, pin rows, other-name rows)."""
    t0, st = time.time(), area_label(area)
    rules = rules_for_area(rules, area)
    clear_old_outputs(a.out, area)
    own = layer_file(area)
    try: refs = park_list(a.repo, area)
    except (OSError, ValueError):
        print(f'{st}: park list not found.'); info['not_built'] = 'no park list'; return 2, [], [], []
    if own is None:
        print(f'{st}: layer file not found.'); info['not_built'] = 'no layer file'; return 2, [], [], []
    gaps = layer_gaps(own[0], rules)
    info['gaps'] = gaps
    info['not_waited_for'] = no_wait(own[0], rules)
    pool = Pool(rules)
    pool.add_file(area, own[0])
    layer_files = {area: {'file': own[2], 'made': own[0].get('made'), 'sha256': own[1]}}
    nbs = area_neighbours(area, rules)
    for nb in nbs:
        f = layer_file(nb)
        if f is None: info['neighbour_gaps'].append(f'{nb}: no file'); continue
        info['neighbour_gaps'] += [f'{nb} {l}' for l in layer_gaps(f[0], rules)]
        pool.add_file(nb, f[0])
        layer_files[nb] = {'file': f[2], 'made': f[0].get('made'), 'sha256': f[1]}
    listed = park_states(a.repo, area)
    parks = {r: dict(facts.get(r) or {'name': '', 'type': ''}, listed_in=listed.get(r) or []) for r in refs}
    for r, p in facts.items():
        if r not in parks and str(p.get('area') or '') in [area] + nbs: parks[r] = p
    locks = {}
    if a.locks and os.path.isfile(os.path.join(a.locks, 'locks', f'{area}.json')):
        with open(os.path.join(a.locks, 'locks', f'{area}.json'), encoding='utf-8') as f: locks = json.load(f).get('locks') or {}
    res = match_state(refs, parks, pool, rules, locks)
    doc = state_doc(st, refs, parks, res, pool, rules, layer_files, area, gaps)
    g = gate(doc['parks'], res, pool, rules, parks)
    id_parks = [r for r in res['joins'] if res['how'][r][0] == 2]
    info.update({'records_loaded': len(pool.recs), 'records_dropped': dict(sorted(pool.dropped.items())), 'gate': g,
                 'by_step': doc['counts']['by_step'], 'counts': doc['counts'], 'layer_files': layer_files,
                 'locks': {'held': sum(1 for r in id_parks if res['lock_status'].get(r) == 'held'),
                           'broken': len({b['ref'] for b in res['locked_broken']}),
                           'new': sum(1 for r in id_parks if r not in res['lock_status'])},
                 'locked_broken': res['locked_broken'], 'seconds': round(time.time() - t0, 1)})
    info['lines'] = dict(sorted(pool.lines.items()))
    shares = [p.get('share') for p in doc['parks'].values() if p.get('m')]
    info['share'] = {'all': shares.count('all'), 'part': shares.count('part'), 'none': shares.count('none')}
    lic = {}
    for rs in res['joins'].values():
        for i in rs: lic[str(pool.recs[i].get('lic') or 'NO CLASS')] = lic.get(str(pool.recs[i].get('lic') or 'NO CLASS'), 0) + 1
    info['joined_by_licence'] = dict(sorted(lic.items()))
    if g['ok']: info['key_text_sha256'] = key_text_sha256(doc)
    if not g['ok']:
        print(f'{st}: GATE FAILED, key not written. {len(g["bad"])} broken row(s), listed in v2-run.json.'); return 4, [], [], []
    with open(os.path.join(a.out, f'{area}.json.gz'), 'wb') as f: f.write(gz_bytes(doc))
    if a.write_locks:
        os.makedirs(os.path.join(a.out, 'locks'), exist_ok=True)
        with open(os.path.join(a.out, 'locks', f'{area}.json'), 'w', encoding='utf-8') as f:
            json.dump({'locks': res['locks_out']}, f, sort_keys=True, indent=1)
    pins = [[r, st, parks[r].get('name'), parks[r].get('type'), doc['parks'][r]['match']['why'],
             rules['pin_only_reasons'][doc['parks'][r]['match']['why']]] for r in refs if r not in res['joins']]
    c, lk = doc['counts'], info['locks']
    gap_text = f" Built with a store-room gap: {', '.join(gaps)}." if gaps else ''
    print(f"{st}: {c['outlined']} of {c['parks']} parks outlined (id {c['by_step']['id']}, name {c['by_step']['name']}), "
          f"{c['pin_only']} pin only. Locks held {lk['held']}, broken {lk['broken']}, new {lk['new']}. Gate OK.{gap_text} "
          f"{time.time() - t0:.0f} s.")
    info['seconds'] = round(time.time() - t0, 1)
    return (3 if gaps else 0), proof_rows(st, res, pool, rules), pins, id_other_names(st, res, parks, pool, rules)


def tool_line(trial):
    """Rule trial_rules: the key's tool line says when it was made with a trial rule table."""
    return TOOL + (' (trial rules)' if trial else '')


def run(argv=None):
    ap = argparse.ArgumentParser(description='Clean v2 US key matcher.')
    ap.add_argument('--states', nargs='+', default=[])
    ap.add_argument('--areas', nargs='+', default=[], help='areas such as US-MN CA-ON')
    ap.add_argument('--store'); ap.add_argument('--facts'); ap.add_argument('--out')
    ap.add_argument('--locks'); ap.add_argument('--write-locks', action='store_true')
    ap.add_argument('--repo', default=os.path.dirname(os.path.dirname(HERE)))
    ap.add_argument('--rules', help='a trial rule table (the key says "trial rules")')
    ap.add_argument('--selftest', action='store_true')
    try: a = ap.parse_args(argv)
    except SystemExit: return 2
    if a.selftest: return selftest()
    areas = list(dict.fromkeys(area_of(x) for x in a.states + a.areas))
    if not (areas and a.store and a.facts and a.out) or not os.path.isfile(a.facts) or not os.path.isdir(a.store):
        print('Missing input: give --states or --areas, --store (a folder), --facts (a file) and --out.'); return 2
    t_all = time.time()
    try: rules = load_rules(a.repo, a.rules)
    except (OSError, RulesError) as e:
        print(f'Rule table refused: {e}. Nothing was built.'); return 2
    facts = read_gz_json(a.facts).get('parks') or {}
    os.makedirs(a.out, exist_ok=True)
    cache, run_info, code = {}, {'states': {}, 'areas': {}, 'inputs': {}}, 0
    run_info['inputs']['facts'] = {'file': os.path.basename(a.facts), 'sha256': sha256(a.facts)}
    run_info['inputs']['rules'] = {'file': a.rules or '.github/us-key-v2-rules.json', 'sha256': sha256(rules_path(a.repo, a.rules)),
                                   'trial': bool(a.rules)}
    rules['_tool'] = tool_line(bool(a.rules))
    proof_all, pin_all, other_all = [], [], []

    def layer_file(area):
        if area not in cache:
            p = os.path.join(a.store, f'{area}.layer-records.json.gz')
            cache[area] = (read_layer_file(p, rules), sha256(p), os.path.basename(p)) if os.path.isfile(p) else None
            if cache[area]: run_info['inputs'][area] = {'file': cache[area][2], 'sha256': cache[area][1]}
        return cache[area]

    for n, area in enumerate(areas):
        info = {'seconds': 0, 'records_loaded': 0, 'records_dropped': {}, 'by_step': {}, 'gate': None, 'locks': None,
                'locked_broken': [], 'not_built': None, 'neighbour_gaps': [], 'gaps': []}
        run_info['states'][area_label(area)] = info
        run_info['areas'][area] = info
        c, pr, pn, on = build_state(area, a, rules, facts, layer_file, info)
        code = 4 if 4 in (code, c) else max(code, c)
        proof_all += pr; pin_all += pn; other_all += on
        later = {x for b in areas[n + 1:] for x in [b] + area_neighbours(b, rules)}
        for k in [k for k in cache if k not in later]: del cache[k]   # rule memory: keep only files a later area reads
    write_csv(os.path.join(a.out, 'v2-proof.csv'), ['ref', 'st', 'file_key', 'agency_id', 'layer', 'record_name', 'acres', 'step', 'by',
                                                    'evidence', 'file_area', 'lock', 'shape', 'publishable', 'licence_class'], proof_all)
    write_csv(os.path.join(a.out, 'v2-pin-only.csv'), ['ref', 'st', 'name', 'kind', 'reason_code', 'reason'], pin_all)
    write_csv(os.path.join(a.out, 'v2-id-other-names.csv'), ['ref', 'st', 'park_name', 'record_key', 'record_name', 'layer',
                                                             'km_from_pin'], other_all)
    run_info['inputs'] = dict(sorted(run_info['inputs'].items()))
    run_info['seconds_total'] = round(time.time() - t_all, 1)
    with open(os.path.join(a.out, 'v2-run.json'), 'w', encoding='utf-8') as f: json.dump(run_info, f, sort_keys=True, indent=1)
    return code


def selftest():
    """A fast check of the pure rules (the full tests live in tests/test_us_key_v2_nov26.py)."""
    rules = load_rules(os.path.dirname(os.path.dirname(HERE)))
    ok = [full("DEVIL'S TRACK", rules) != full('Devils Track', rules),
          full_ps("DEVIL'S TRACK", rules) == full('Devils Track', rules),
          full_ps("Knox's", rules) != full('Knox', rules),
          full('Upper Mississippi River National Wildlife and Fish Refuge', rules) == full('Upper Mississippi River National Wildlife Refuge', rules),
          kind_swap_keys(full('Crystal Lake Wild Forest', rules), 'sgnya', rules) == {'crystal lake state forest'},
          'crow wing' in park_name_keys('Crow Wing State Park', 'State Park', rules),
          decode_rings([[0, 0, 10, 0, 0, 10, -10, 0]], 1) == [[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]],
          inside(0.5, 0.5, [[(0, 0), (1, 0), (1, 1), (0, 1)]])]
    print('selftest: ' + ('OK' if all(ok) else 'FAILED ' + str([i for i, x in enumerate(ok) if not x])))
    return 0 if all(ok) else 1


if __name__ == '__main__':
    sys.exit(run())
