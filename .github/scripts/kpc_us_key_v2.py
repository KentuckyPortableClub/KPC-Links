#!/usr/bin/env python3
"""kpc_us_key_v2: the clean v2 US key matcher (26 Nov 2026).

Ties each park to the records of TODAY's layer files that are that park, and nothing else.
Rule sheet: .claude/notes/rule-sheet-us-key-v2-nov26.md. Rule table: .github/us-key-v2-rules.json (every rule row names the
function that carries it and the test that notices when it is gone).
Steps, each for all parks before the next: load -> 2 agency id -> 3 name with pin, size or two sources -> 4 pin only -> 5 gate.
Step 1: check the locks (a witness; it never decides). It compares the lock file with today's step 2 and reports held / broken.
After steps 2 and 3 (27 Nov 2026, owner: "Yes to trails"): each park's own trail-bot file joins it when the pin is within 100 ft
of the line; it is found by the park number only, never by name. A line of any layer joins only on its own proof.
Plain Python 3.12, no packages, no legacy modules.

  python kpc_us_key_v2.py --states MN NY --store <folder> --facts <park-facts.json.gz> --out <folder>
                          [--locks <run folder>] [--write-locks] [--repo <KPC-Links root>] [--selftest]
Exit codes: 0 built; 2 bad arguments / missing input / rule table refused; 3 a typed state not built (layer not complete);
4 gate failed.
"""
import argparse, array, bisect, csv, gzip, hashlib, io, json, math, os, re, sys, time, unicodedata

TOOL = 'kpc_us_key_v2 1 (2026-11-26)'
HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------------------------------------------- tables
S, L, D, RX = 'str', 'list of str', 'dict of str', 'regex'
TABLE_SHAPES = {
    'drop_layers': D, 'record_id_fields': D, 'class_fields': D, 'short_forms': D, 'des_kinds': D,
    'fixed_names': D, 'pin_only_reasons': D, 'neighbours': D, 'ca_neighbours': D, 'no_wait_layers': D, 'no_wait_status': D,
    'single_kind_layers': {'*': [S]}, 'kinds_alike': [[S, S]], 'kind_fields': {'*': [S]},   # 27 Nov 2026, rule name_kind_agrees
    'shared_page_kinds': L, 'kind_words': L, 'place_words': L, 'compound_kinds': L, 'core_drop': L, 'water_last_words': L, 'acre_fields': L,
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
    'trail_bot_layers': {'*': {'ref_field': S, 'key_rx': RX}},
}
LINK_TIE_SHAPE = [{'kind': S, 'layer': S, 'field': S, 'rx': RX, '?glue': S}]
VALUE_KEYS = ('size_tol', 'two_sources_tol', 'pin_m', 'near_km', 'lock_acres_tol', 'thin_m', 'long_ratio', 'acre_box_factor',
              'same_ground_share', 'same_ground_tol', 'place_word_len', 'line_pin_m', 'ha_acres', 'km2_acres', 'mi2_acres',
              'acres_field_tol', 'acres_field_min_n', 'acres_field_sample', 'acres_field_min_acres',   # 27 Nov 2026, rule acres_field_guard
              'shared_record_share',   # 27 Nov 2026, rule shared_record_size
              'two_sources_same_acres',   # 27 Nov 2026, rule two_sources_not_a_copy
              'union_lines', 'union_floor',   # 27 Nov 2026, rule size_union_not_sum
              'two_sources_size_band')   # 27 Nov 2026, rule two_sources_size_agrees
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
    r['_trail_key'] = {l: re.compile(t['key_rx']) for l, t in r['trail_bot_layers'].items()}
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
    k |= {t['ref_field'] for t in r['trail_bot_layers'].values()}
    for fs in r['kind_fields'].values(): k |= set(fs)   # 27 Nov 2026, rule name_kind_agrees
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
    if rec.get('acres_off'): return None   # 27 Nov 2026, rule acres_field_guard: this layer's acres field is not used in this run
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


def acres_field_sample(recs, rules):
    """Rule acres_field_guard (27 Nov 2026): the field / outline ratios of one layer of one area's file. The records with an
    acres field of at least acres_field_min_acres (lines never), in id order, at most acres_field_sample of them, picked
    evenly from first to last, so the same file always gives the same sample. -> [ratio]."""
    n = rules['numbers']
    rs = sorted((r for r in recs if not r.get('line') and (agency_acres(r, rules) or 0) >= n['acres_field_min_acres']), key=lambda r: str(r['id']))
    k = int(n['acres_field_sample'])
    pick = rs if len(rs) <= k else [rs[int(j * len(rs) / k)] for j in range(k)]
    out = []
    for r in pick:
        m = acres_of(shape(r))
        if m > 0: out.append(agency_acres(r, rules) / m)
    return out


def acres_field_ok(ratios, rules):
    """Rule acres_field_guard (27 Nov 2026; measured on Illinois: layer sgild writes its acres from a flat web map, 1.6 to 1.85
    times too big): a layer's acres field is trusted unless at least acres_field_min_n records were measured and their median
    field / outline is more than acres_field_tol ABOVE 1. Too few records to judge = trusted, as before. A field SMALLER than
    its outline is kept: the agency may hold only part of what is drawn (MN sgmne: a 580-acre outline with su_acres 0.02)."""
    n = rules['numbers']
    if len(ratios) < n['acres_field_min_n']: return True
    return median(ratios) <= 1 + n['acres_field_tol']


def median(xs):
    q = sorted(xs)
    return q[len(q) // 2] if len(q) % 2 else (q[len(q) // 2 - 1] + q[len(q) // 2]) / 2


def acres_field_check(pool, rules):
    """Rule acres_field_guard, run once after loading and before step 2: every layer of every area's file is judged on its own
    sample; a layer that fails has its acres field switched off for this run (agency_acres says None, so the outline is
    measured instead, in the size proof, two sources, the lock and the key alike). -> ([switched off], [every layer judged]),
    each row {area, layer, median, measured} for v2-run.json."""
    by = {}
    for r in pool.recs: by.setdefault((r['area'], r['layer']), []).append(r)
    off, seen = [], []
    for (area, layer), recs in sorted(by.items()):
        rat = acres_field_sample(recs, rules)
        if not rat: continue
        row = {'area': area, 'layer': layer, 'measured': len(rat), 'median': round(median(rat), 3)}
        seen.append(row)
        if acres_field_ok(rat, rules): continue
        off.append(row)
        for r in recs:
            r['acres_off'] = True
            r.pop('_aa', None); r.pop('_ac', None)
    return off, seen


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


BAND_MIN = 64   # a ring with more points than this gets bands of latitude (a measuring detail, not a rule)


def ring_bands(ring):
    """27 Nov 2026: for a long ring, which of its sides reach each band of latitude. -> (y0, 1 / band height, bands).
    A side is listed in every band its two ends span, so a point only has to try the sides of its own band: the same sides
    the plain test could ever count (a side counts only when the point's latitude lies between its ends)."""
    y0, y1 = min(y for _, y in ring), max(y for _, y in ring)
    nb = min(2048, max(8, len(ring) // 16))
    inv = nb / (y1 - y0) if y1 > y0 else 0.0
    bands = [array.array('I') for _ in range(nb)]   # the side's first point only (4 bytes): its other end is the point before it
    j = len(ring) - 1
    for i in range(len(ring)):
        ya, yb = ring[i][1], ring[j][1]
        lo, hi = (ya, yb) if ya <= yb else (yb, ya)
        for b in range(min(nb - 1, max(0, int((lo - y0) * inv))), min(nb - 1, max(0, int((hi - y0) * inv))) + 1): bands[b].append(i)
        j = i
    return y0, inv, bands


def inside_boxed(lon, lat, rec):
    """inside(lon, lat, shape(rec)) with the SAME answer (even-odd), measured faster (27 Nov 2026, the owner's Alaska build):
    each ring's box is kept (_rb) and a ring whose box does not hold the point is passed over (such a point crosses the ring an
    even number of times); a long ring is tried only on the sides of the point's own band of latitude (ring_bands, kept in _bd)."""
    g = shape(rec)
    if '_rb' not in rec:
        rec['_rb'] = [(min(x for x, _ in r), min(y for _, y in r), max(x for x, _ in r), max(y for _, y in r)) if r else (0, 0, -1, -1) for r in g]
        rec['_bd'] = {}
        rec['_rk'] = None
        if len(g) > BAND_MIN:   # a record of very many pieces (Yukon Delta: tens of thousands): the pieces by band of latitude too
            ok = [b for b in rec['_rb'] if b[3] >= b[1]]
            ky0, ky1 = min(b[1] for b in ok), max(b[3] for b in ok)
            nb = min(2048, max(8, len(g) // 8)); inv = nb / (ky1 - ky0) if ky1 > ky0 else 0.0
            bands = [[] for _ in range(nb)]
            for n_, b in enumerate(rec['_rb']):
                if b[3] < b[1]: continue
                for q in range(min(nb - 1, max(0, int((b[1] - ky0) * inv))), min(nb - 1, max(0, int((b[3] - ky0) * inv))) + 1): bands[q].append(n_)
            rec['_rk'] = (ky0, ky1, inv, bands)
    c = False
    if rec['_rk'] is None: todo = range(len(g))
    else:
        ky0, ky1, inv, bands = rec['_rk']
        if lat < ky0 or lat > ky1: return False
        todo = bands[min(len(bands) - 1, max(0, int((lat - ky0) * inv)))]
    for n_ in todo:
        ring = g[n_]; x0, y0, x1, y1 = rec['_rb'][n_]
        if lon < x0 or lon > x1 or lat < y0 or lat > y1: continue
        if len(ring) > BAND_MIN:
            bd = rec['_bd'].get(n_)
            if bd is None: bd = rec['_bd'][n_] = ring_bands(ring)
            by0, inv, bands = bd
            sides = bands[min(len(bands) - 1, max(0, int((lat - by0) * inv)))]
        else:
            sides = None
        if sides is None:
            j = len(ring) - 1
            for i in range(len(ring)):
                xi, yi = ring[i]; xj, yj = ring[j]
                if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi: c = not c
                j = i
        else:
            for i in sides:
                xi, yi = ring[i]; xj, yj = ring[i - 1]   # i - 1 = the point before; for i = 0 that is the ring's last point
                if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi: c = not c
    return c


def same_ground(v, a, kv, k, rules):
    """Rule acres_same_ground_once: two same-name records are the same ground when the sample points inside the smaller
    record's SHAPE lie at least same_ground_share inside the other's shape (boxes first), and the sizes agree."""
    n = rules['numbers']
    if not box_share(rec_box(a), rec_box(k)) or abs(v - kv) > n['same_ground_tol'] * max(v, kv): return False
    for r in (a, k):
        if '_m' not in r: r['_m'] = acres_of(shape(r))
    small, big = (a, k) if a['_m'] <= k['_m'] else (k, a)
    # 27 Nov 2026 (the owner's 50-state build sat on Alaska for 14 minutes; it was 11 s the night before, when two Alaska layers
    # were missing): the SAME test, measured faster. A record's own sample points are worked out once and kept (_sp); a point is
    # only tried against the rings whose box holds it (inside_boxed: a point outside a ring's box crosses that ring an even
    # number of times, so the answer cannot change); the count stops as soon as the answer is certain. No join changes.
    if '_sp' not in small:
        b = small['_b']
        pts = [(b[0] + (b[2] - b[0]) * (i + .5) / GRID, b[1] + (b[3] - b[1]) * (j + .5) / GRID) for i in range(GRID) for j in range(GRID)]
        pts += [(sum(x for x, _ in r) / len(r), sum(y for _, y in r) / len(r)) for r in small['_g']]   # each piece's middle too
        small['_sp'] = [q for q in pts if inside_boxed(q[0], q[1], small)]
    pts = small['_sp']
    if not pts: return False
    if not small.get('line') and small.get('raw') is not None and small.get('raw') == big.get('raw') and small.get('q') == big.get('q'):
        return True   # 27 Nov 2026: the very same outline saved twice (Yukon Delta, 16 MB each): every sample point is inside, so no sums are needed
    need, hits = n['same_ground_share'] * len(pts), 0
    for i, q in enumerate(pts):
        if inside_boxed(q[0], q[1], big): hits += 1
        if hits >= need: return True
        if hits + (len(pts) - i - 1) < need: return False
    return hits >= need


def overlap_groups(recs):
    """Rule size_union_not_sum (27 Nov 2026): the records whose boxes touch another record's box, in groups (a box that
    overlaps no other box is no group). Boxes sorted by west edge, so a record is compared only with boxes still open."""
    rs = sorted(recs, key=lambda r: rec_box(r)[0])
    up = list(range(len(rs)))
    def top(i):
        while up[i] != i: up[i] = up[up[i]]; i = up[i]
        return i
    open_ = []
    for i, r in enumerate(rs):
        b = rec_box(r)
        if open_ and min(rec_box(rs[j])[2] for j in open_) < b[0]: open_ = [j for j in open_ if rec_box(rs[j])[2] >= b[0]]
        for j in open_:
            if top(j) == top(i): continue   # already one group: no need to look
            c = rec_box(rs[j])
            if c[1] <= b[3] and b[1] <= c[3]: up[top(i)] = top(j)
        open_.append(i)
    out = {}
    for i, r in enumerate(rs): out.setdefault(top(i), []).append(r)
    return [g for g in out.values() if len(g) > 1]


def union_share(recs, rules):
    """Rule size_union_not_sum (27 Nov 2026): the ground the records' outlines cover together divided by the sum of their own
    outlines (1.0 = no overlap; 0.5 = the same outline twice). Measured on union_lines evenly spaced lines of latitude across
    their joint box: on each line each record's inside stretches (even-odd, so a hole is outside), merged across records;
    each line weighted by the cosine of its latitude. A side is found only on the lines its two ends span (bisect), so the
    work is the records' points plus their crossings, never lines x points. The very same outline saved twice is cut once."""
    n = max(1, int(rules['numbers']['union_lines']))
    bs = [rec_box(r) for r in recs]
    y0, y1 = min(b[1] for b in bs), max(b[3] for b in bs)
    if not y1 > y0: return 1.0
    ys = [y0 + (y1 - y0) * (i + .5) / n for i in range(n)]
    w = [math.cos(math.radians(y)) for y in ys]
    shapes, times, seen = [], [], {}
    for r in recs:
        g = shape(r)
        sig = (r.get('q'), len(g), tuple(g[0][:2]) if g and g[0] else (), sum(len(x) for x in g))   # cheap first look, then the real compare
        k = next((s for s in seen.get(sig, ()) if r.get('raw') is not None and shapes[s][0].get('raw') == r.get('raw')), None)
        if k is None: seen.setdefault(sig, []).append(len(shapes)); shapes.append((r, g)); times.append(1)
        else: times[k] += 1
    lines = [[] for _ in range(n)]   # per line: (start, end) of each inside stretch, every outline together
    total = 0.0
    for s, (r, g) in enumerate(shapes):
        xs = {}
        for ring in g:
            for (xa, ya), (xb, yb) in zip(ring, ring[1:] + ring[:1]):
                if ya == yb: continue
                lo, hi = (ya, yb) if ya < yb else (yb, ya)
                for i in range(bisect.bisect_left(ys, lo), bisect.bisect_left(ys, hi)):   # lo <= y < hi: the same as inside()
                    xs.setdefault(i, []).append(xa + (ys[i] - ya) * (xb - xa) / (yb - ya))
        for i, v in xs.items():
            v.sort()
            for a, b in zip(v[0::2], v[1::2]):
                lines[i].append((a, b)); total += times[s] * (b - a) * w[i]
    if total <= 0: return 1.0
    cover = 0.0
    for i, st in enumerate(lines):
        end = None
        for a, b in sorted(st):
            if end is None or a > end: cover += (b - a) * w[i]; end = b
            elif b > end: cover += (b - end) * w[i]; end = b
    return min(1.0, cover / total)


def union_total(kept, total, rules):
    """Rule size_union_not_sum (27 Nov 2026): a class total measured as ground, not as a sum. kept = the [(acres, record)]
    left after the same-ground skip (so nothing is taken off twice). Each group of overlapping boxes loses its double-counted
    share: its sum x (1 - union_share), but never below its largest record (the ground together is at least the biggest piece,
    even when an acres field holds less than its outline). No group, or every share within union_floor of 1: today's total,
    the very same number."""
    vs = {id(r): v for v, r in kept if v > 0}
    cut = 0.0
    for g in overlap_groups([r for v, r in kept if v > 0]):
        share = union_share(g, rules)
        if share >= 1 - rules['numbers']['union_floor']: continue
        s = sum(vs[id(r)] for r in g)
        cut += s - max(s * share, max(vs[id(r)] for r in g))
    return total - cut if cut > 0 else total


def land_acres(recs, rules, agency_only=False):
    """{layer: acres}: per class, the largest class; same ground counted once; overlapping outlines measured as the ground
    they cover together (rule size_union_not_sum). agency_only: the agency's acres only."""
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
            total = union_total([x for ks in kept.values() for x in ks], total, rules)   # 27 Nov 2026, rule size_union_not_sum
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


def trail_file_ref(rec, rules):
    """Rule trail_bot_file (owner 27 Nov 2026, 5:45 AM: "Yes to trails"): the park number a trail-bot file carries, read from
    BOTH its ref field and its key (trail_bot_layers: 'trl0197' = US-0197). '' when the layer is not a trail-bot layer, or when
    the two disagree (then the file joins nobody). The name inside the file is the club's own label, so it is never a proof."""
    t = rules['trail_bot_layers'].get(rec['layer'])
    if not t: return ''
    ref, m = norm_val(attr(rec['a'], t['ref_field'])), rules['_trail_key'][rec['layer']].fullmatch(str(rec['key']))
    return ref if m and ref and ref.split('-', 1)[-1] == m.group(1) else ''


def name_indexed(rec, rules):
    """Rule trail_bot_name_not_proof (27 Nov 2026): a record is found by its name, unless it is a record of a trail-bot layer
    (its name was typed in the trail bot's list, not read from the agency). Such a record is found by its park number only."""
    return rec['layer'] not in rules['trail_bot_layers']


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
    """Rule two_sources_independent: both records come from a known map service and the two services differ. Two layers of
    one service are one source (Québec's register and its recognised-reserves layer); a blank service is an unknown source and
    proves nothing (hma and sgnvi: one Nevada herd-area record in two layers, grader 27 Nov 2026)."""
    return bool(a.get('svc') and b.get('svc') and a['svc'] != b['svc'])


def record_ids(rec, rules):
    """Rule two_sources_not_a_copy: the ids a record carries: its id and file key, and every agency id of its layer's ties."""
    out = {('id', norm_val(rec.get('id'))), ('id', norm_val(rec.get('key')))}
    out |= {(t['kind'], tie_value(rec, t, rules)) for t in rules['_ties'].get(rec['layer'], [])}
    return {x for x in out if x[1]}


def not_a_copy(a, b, rules):
    """Rule two_sources_not_a_copy: never the same record twice. Refused when the two agency sizes are equal (within
    two_sources_same_acres) or when the two records share any id (record id, file key or agency id of a tie)."""
    sa, sb = agency_acres(a, rules) or 0, agency_acres(b, rules) or 0
    return abs(sa - sb) >= rules['numbers']['two_sources_same_acres'] and not (record_ids(a, rules) & record_ids(b, rules))


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
        self.trail_ix = {}   # rule trail_bot_file: {park number: [record i]} of the trail-bot files

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
        if r.get('source_file'): rec['source_file'] = str(r['source_file'])
        if is_line(r):
            rec.update(line=True, paths=r.get('paths'))
            self.lines[layer] = self.lines.get(layer, 0) + 1
        self.recs.append(rec); self.by_ident[(layer, rid)] = rec
        i = rec['i']
        if not name_indexed(rec, rules):   # 27 Nov 2026: a trail-bot file is found by its park number only, never by name
            ref = trail_file_ref(rec, rules)
            if ref: self.trail_ix.setdefault(ref, []).append(i)
            return
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


def line_by_itself(rec):
    """Rule line_own_proof (27 Nov 2026, review of the trail run): a line is never a piece of a group. It joins only on its
    own proof: it carries the park's agency id itself, or it has the exact name with the pin within line_pin_m of it (or it is
    the park's own trail-bot file, rule trail_bot_file). It never comes along with a park's land, with a same-named group,
    a unit group, a project, a piece word or a piece of an id unit."""
    return bool(rec.get('line'))


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


# 27 Nov 2026, the owner (8:37 AM, passing on the grader's words with his yes): "Both parks may share the record (marked 'same
# land, two park numbers') ONLY when each proves it on its own (own agency ID, or own name + pin inside the record). Unproved
# shared records stay a hard gate fail. Never let a smaller park take a bigger surrounding park's outline."
SAME_LAND = 'same land, two park numbers'


def own_proof(p, ref, rec, step, ctx):
    """Rule shared_record_own_proof: the park's OWN proof on this one record, '' when it has none. Step 2 parks: the record
    itself carries the park's agency id (a piece of the unit that carries no id does not count). Any park: the park's exact name
    is on the record (exact-name rules, full_name_record) and its pin is INSIDE the record (near the edge is not enough; a line
    has no inside). An id two parks claim never gets this far (rule id_shared), so it is never anyone's own."""
    rules, pin = ctx['rules'], pin_of(p)
    lk = p.get('link') or {}
    if step == 2 and lk.get('id_value'):
        kind, value = lk.get('id_kind'), norm_val(lk['id_value'])
        if any(t['kind'] == kind and tie_value(rec, t, rules) == value for t in rules['_ties'].get(rec['layer'], [])):
            return f'own agency id ({kind} {value}) on the record'
    if pin is not None and not rec.get('line') and full_name_record(p, [rec['i']], ctx['pool'], rules, ref) \
            and inside(pin[1], pin[0], shape(rec)):
        return 'own exact name on the record, pin inside it'
    return ''


def size_fits_record(p, rec, ctx):
    """Rule shared_record_size: a park takes a record it shares only when its official size is on file (the size witnesses) and
    even its smallest official size is at least shared_record_share of the record's acres. No official size = unsure = it does
    not take it (pin only, unless it has other land). So Cumberland Falls never takes the Daniel Boone forest around it."""
    wit = size_witnesses(p, ctx['shared_names'], ctx['rules'])
    return bool(wit) and min(wit) >= ctx['rules']['numbers']['shared_record_share'] * rec_acres(rec, ctx['rules'])


def share_claims(bad, claims, step, ctx):
    """Rules shared_record_own_proof / shared_record_size: for each record claimed in one step by parks of two names, the parks
    that keep it: each one with its own proof and a size that fits. Two or more keep it = same land, two park numbers; one =
    that park keeps it alone; none = nobody (as before). -> {record i: {ref: proof words}}."""
    out = {}
    for i in sorted(bad):
        rec = ctx['pool'].recs[i]
        out[i] = {}
        for r in sorted(claims[i]):
            pr = own_proof(ctx['parks'][r], r, rec, step, ctx)
            if pr and size_fits_record(ctx['parks'][r], rec, ctx): out[i][r] = pr
    return out


def note_same_land(keep, ctx):
    """Keeps the records two parks of two names now share (ctx['same_land'] {record i: {ref: proof}}) for the key, the gate and
    the report."""
    for i, refs in keep.items():
        if len({nk(ctx['parks'][r].get('name')) for r in refs}) > 1: ctx['same_land'][i] = dict(refs)


# ---------------------------------------------------------------------------------------------------------------- step 2
def id_records(pool, p, kind, value, rules, names_by_full, layer=None):
    """All of today's records that carry the park's id (one layer when given), with their project pieces, after the
    wetland district and other-name rules."""
    carry = set(pool.tie_ix.get((kind, value), []))
    got = set(carry)
    for i in list(got):
        up = rules['unit_pieces'].get(pool.recs[i]['layer'])
        if up: got.update(pool.piece_ix.get(piece_key(pool.recs[i], up), []))
    got = {i for i in got if i in carry or not line_by_itself(pool.recs[i])}   # 27 Nov 2026: a line must carry the id itself
    return [i for i in sorted(got) if (not layer or pool.recs[i]['layer'] == layer)
            and wmd_ok(p, pool.recs[i], rules) and not other_park_name(p, pool.recs[i], names_by_full, rules)
            and not id_not_fee(pool.recs[i], rules)]


def id_not_fee(rec, rules):
    """Rule easement_not_by_id (27 Nov 2026, grade item 5): a record whose TYPE FIELD says easement is never joined by an id
    either (Virginia's 'NPS Easement' records: MATYPE Conservation Easement). Narrowed the same day: a lease or agreement in
    the NAME, or a Fish and Wildlife interest code, does not refuse an id join (a leased state park is the park: Michigan's
    US-1527 Newaygo State Park, 'leased from Consumer's Energy'; no id-joined Fish and Wildlife record in the country has a
    non-fee code)."""
    return type_says_easement(rec, rules)


def type_says_easement(rec, rules):
    """A record type field (type_field_rx) that says easement (easement_rx)."""
    return any(rules['_easement_rx'].search(str(v)) for k, v in rec['a'].items() if rules['_type_field_rx'].match(str(k)) and v not in (None, ''))


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
                   if not line_by_itself(pool.recs[i]) and piece_id_empty(pool.recs[i], rules)
                   and not refusal(p, ref, pool.recs[i], i, dict(ctx, taken=set())))
    return [i for i in chain_pieces(cands, pin, pool, rules, seeds=list(rs)) if i not in rs] if cands and pin else []


def own_name_record(p, ref, rec, rules):
    """Rule id_shared_page: True when the record carries the park's OWN name: an exact name (the exact-name rules and the
    other_spellings table), or the same place words with only kind words different ('Pigeon Lake Wilderness' for Pigeon Lake
    Wilderness Area), or the part before ' - ' ('High Tor Wma - Clark Gully' is a piece of High Tor Wma). A name with other place
    words ('Twitchell Lake Primitive Area') is another unit's name."""
    keys = park_name_keys(p.get('name'), p.get('type'), rules) | other_spelling_keys(ref, rules)
    if keys & record_name_keys(rec['names'], rec['layer'], rules): return True
    core = name_core(p.get('name'), None, rules)
    return bool(core) and any(name_core(part, None, rules) == core for n in rec['names'] for part in {n, n.split(' - ')[0]})


def shared_page_own(p, ref, kind, rs, pool, rules):
    """Rule id_shared_page: when the records of one id of a page-address kind carry two or more different names, the id proves
    only the records with the park's own name. -> (the records kept, True when the page was shared)."""
    if kind not in rules['shared_page_kinds']: return rs, False
    names = {name_core(pool.recs[i]['name'], None, rules) or (pool.recs[i]['name'],) for i in rs}
    if len(names) < 2: return rs, False
    return [i for i in rs if own_name_record(p, ref, pool.recs[i], rules)], True


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
        rs, _ = shared_page_own(p, ref, k[0], rs, pool, rules)   # 27 Nov 2026, rule id_shared_page
        if not rs: note[ref] = 'id page shared by other units: no record carries the park\'s name'; continue
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
    keep = share_claims(bad, claims, 2, ctx)   # 27 Nov 2026: a park that proves the record on its own keeps it
    note_same_land(keep, ctx)
    out = {}
    for ref in sorted(want):
        rs = [i for i in want[ref] if i not in bad or ref in keep[i]]
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


def other_kind(p, rec, pool, rules, page=None):
    """Rule name_kind_agrees (27 Nov 2026): a record found by the park's name (exact, page or two-language name) is another
    kind of land when the park's name or type says a kind, the record itself says a kind (its own names, or its layer's kind
    from single_kind_layers), and no kind the record is known by (those, its PAD-US designation type, layer_kinds) is the
    park's. 'Ash Meadows' in the BLM herd-area layer is a herd area, not Ash Meadows National Wildlife Refuge. A designation
    type or a park layer's kind alone never refuses (Hawaii's Lava Tree State Monument is Des_Tp SHCA, a park POTA calls a
    State Park; NY sgnyb 'Olana' is a State Historic Site in an 'sp' layer), but it may agree (Oregon's Unity Lake State
    Recreation Site, Des_Tp SREC, is the Unity Lake State Recreation Area). No kind on either side = no opinion (the normal
    case: a bare name in a park layer). Two kinds of one pair of kinds_alike never
    refuse each other (pairs only, never chains): POTA's BLM park types mix up the BLM designations (Utah's US-6073 King Top 'BLM Recreation Management
    Area' is the King Top wilderness study area). page (27 Nov 2026): a record found by the park's page name is judged by the
    PAGE name's kind, the agency's own word for its land (Missouri's US-5697 Atlanta Wildlife Area is MDC's Atlanta
    Conservation Area); a page name with no kind word = no opinion."""
    pk = kinds_of(page, rules) if page is not None else park_kinds(p, rules)
    if not pk: return False
    pk |= {b for a, b in rules['kinds_alike'] if a in pk} | {a for a, b in rules['kinds_alike'] if b in pk}
    own = set(rules['single_kind_layers'].get(rec['layer'], [])) | field_kinds(rec, rules)
    says = set().union(*[kinds_of(n, rules) for n in rec['names']]) | own
    return bool(says and not pk & (pool.rec_kinds(rec) | own))


def size_contradicts(groups, proof, witnesses, pool, rules):
    """Rule two_sources_size_agrees (27 Nov 2026): two sources prove only that two maps agree with EACH OTHER. When the park
    has an official size (the size witnesses) and the land they agree on is more than two_sources_size_band times smaller or
    larger than every official value, they describe a piece of the park or another place: no proof. The land = the larger of
    the two sources' groups (their agency acres) or of the two records. No official size = no opinion (as before).
    Proofs that are not two sources (pin, size) are never touched here."""
    by, e = proof
    if not by.endswith('two_sources') or not witnesses: return False
    gs = [rs for g, rs in groups.items() if {pool.recs[i]['id'] for i in rs} & {e['source_a'], e['source_b']}]
    ac = max([group_acres(rs, pool, rules) for rs in gs] + [e.get('acres_a') or 0, e.get('acres_b') or 0])
    f = rules['numbers']['two_sources_size_band']
    return not any(w / f <= ac <= w * f for w in witnesses)


def far_proof_other_state(p, rs, pool):
    """Rule far_proof_own_state (27 Nov 2026): a proof that is not the pin (size or two sources) uses a group of records only
    when at least one of them comes from the layer file of an area POTA lists the park in (locationDesc). A park listed in
    Alabama only is not proven by two Tennessee layers agreeing with each other (US-10428 Walls of Jericho). A park with no
    listed area = no opinion. The pin's own records are never touched here (a park near a border keeps them)."""
    listed = set(p.get('listed_in') or [])
    return bool(listed) and not any(pool.recs[i]['area'] in listed for i in rs)


def pin_beats_far_proof(proven):
    """Rule pin_beats_far_proof (27 Nov 2026): the exact names proved land only by two sources (no group holds or nears the
    pin, no official size agrees). Then a record of a longer or shorter form of the name that holds the pin is tried too
    (pin_land_wins decides). -> True when every proof is a two-sources one."""
    return bool(proven) and all(v[0].endswith('two_sources') for v in proven.values())


def pin_land_wins(far, near, groups, pool, rules, official=()):
    """Rule pin_beats_far_proof: the pin's land (near: longer or shorter name + pin) replaces the far two-sources land
    (far) when it is at least as big (their agency acres, or measured outlines): two maps agreeing on a piece 1 km away is not
    the park when the park's pin sits in a bigger record of its name (US-3935 Chuck Swan WMA: 755 ac far, 23,925 at the pin;
    US-10428 Walls of Jericho: 759 in Tennessee, 12,330 at the pin). A smaller record at the pin is a part, so the far land
    stays (US-2860 Umpqua Lighthouse State Park: two sources 375 ac, its 25-ac visitor centre at the pin). official (27 Nov
    2026): the park's size on file, any witness (park_size_any); far land within size_tol of it, and pin land not, stays (WA
    US-0340 Spring Creek Hatchery State Park: two sources 10 ac, size on file 9.6; the pin's records 37 ac)."""
    size = lambda gs: max([land_total([pool.recs[i] for i in groups[g]], rules) for g in gs] or [0])
    if not near or size(near) < size(far): return False
    fits = lambda ac: any(abs(ac - w) <= rules['numbers']['size_tol'] * w for w in official)
    return not (fits(size(far)) and not fits(size(near)))   # 27 Nov 2026: far land that has the park's size stays


def park_size_any(p, witnesses):
    """Rule pin_beats_far_proof: every size the park has on file, as information (the witnesses, and the facts' size whatever
    its witness). Used only to keep land as it is, never to prove land."""
    s = (p.get('size') or {}).get('acres')
    try: extra = [float(s)] if s is not None and float(s) > 0 else []
    except (TypeError, ValueError): extra = []
    return list(witnesses) + extra


def land_total(recs, rules):
    """The largest layer total of the records' land (land_acres), 0 for none."""
    return max(land_acres(recs, rules).values() or [0])


def name_reach(p, ref, pool, rules):
    """The records the park's names reach, before any proof or refusal: (own name, page name, two-language name) sets."""
    keys = park_name_keys(p.get('name'), p.get('type'), rules) | other_spelling_keys(ref, rules)   # 27 Nov 2026: other spellings
    keys |= bilingual_aliases(keys, pool, rules)
    own = {i for k in keys for i in pool.name_ix.get(k, [])}
    page = {i for k in page_name_keys(p, rules) for i in pool.name_ix.get(k, [])} - own
    lang = {i for kp in {kind_place(n, rules) for n in (p.get('name'),)} - {None} for i in pool.kp_ix.get(kp, ())} - own - page
    return own, page, lang


def field_kinds(rec, rules):
    """Rule name_kind_agrees (27 Nov 2026): the kinds a record's own type field states (kind_fields: per layer, read through the
    kind words and the des_kinds codes): BLM's nca layer says sma_code BLM_NM (a national monument) on 'Gold Butte'."""
    out = set()
    for fld in rules['kind_fields'].get(rec['layer'], []):
        v = attr(rec['a'], fld)
        if is_placeholder(v, rules): continue
        out |= kinds_of(str(v), rules) | ({rules['des_kinds'][str(v).strip()]} if str(v).strip() in rules['des_kinds'] else set())
    return out


def layer_kinds_of(rec, pool, rules):
    """Rule contested_name: the kinds a record has from its source, not from its words: its layer (single_kind_layers,
    layer_kinds) and its PAD-US designation type (des_kinds)."""
    return set(rules['single_kind_layers'].get(rec['layer'], [])) | set(rules['layer_kinds'].get(rec['layer'], [])) | \
        {rules['des_kinds'][d] for d in [attr(rec['a'], 'Des_Tp')] if d in rules['des_kinds']} | field_kinds(rec, rules)


def park_kinds(p, rules):
    """The kinds the park's name and type say."""
    return kinds_of(p.get('name'), rules) | kinds_of(p.get('type'), rules)


def rival_claims(r, rec, ctx):
    """Rule contested_name: a rival park would prove this record by its own name and its pin (the record holds or nears its
    pin), and the record's own source (its layer or PAD-US designation type: layer_kinds_of) does not say it is another kind
    than the rival. A rival the source rules out is not a claim (NV hma67 'Calico Mountains', a herd-area layer, is no claim of
    US-9242 Calico Mountains Wilderness Area); a rival refused only by a kind word of the record, a copy or a far proof still is."""
    p, rules = ctx['parks'][r], ctx['rules']
    src = layer_kinds_of(rec, ctx['pool'], rules)
    if src and not src & park_kinds(p, rules): return False
    return pin_near(rec, pin_of(p), rules)


def contested_filter(want, ctx):
    """Rule contested_name (27 Nov 2026): a record the names of parks of two or more names reach (before any proof or refusal)
    stays with a park that proved it only when every rival that would claim it (rival_claims) claims it too; then the old rules
    decide between them (same_step_two_names, shared_record_*). A rival that claims it but was refused (another kind word, a
    copy ...) makes it nobody's, as when both claimed it. So a refusal of one park never hands the record to the other: Kansas
    US-2332 Clinton State Park took the Corps' 22,656-ac 'Clinton Recreation Area' (second name 'CLINTON') once the kind rule
    refused Clinton State Wildlife Area. -> {ref: groups}."""
    parks, reach = ctx['parks'], ctx['reach']
    by_rec, wants = {}, {}
    for r, rs in reach.items():
        for i in rs: by_rec.setdefault(i, set()).add(r)
    for r, gs in want.items():
        for rs in gs.values():
            for i in rs: wants.setdefault(i, set()).add(r)
    out = {}
    for ref, gs in want.items():
        new = {}
        for g, rs in gs.items():
            keep = [i for i in rs if not contest_lost(ref, i, by_rec.get(i, ()), wants.get(i, ()), ctx)]
            if keep: new[g] = keep
        out[ref] = new
    return out


def contest_lost(ref, i, reached, wanting, ctx):
    """Rule contested_name: True when park ref must give up record i: a rival of another full name (parks of one full name:
    rules other_pin / same_name decide) would claim it and does not, and the record does not carry ref's own exact FULL name
    (no kind word taken off: SK CA-1149 'Shamrock Regional Park' is that park's, whatever Shamrock Recreation Site's pin), and
    the rival's pin holds the record at least as well as ref's own pin (pin_hold)."""
    parks, rules, rec = ctx['parks'], ctx['rules'], ctx['pool'].recs[i]
    p = parks[ref]
    name = full(p.get('name'), rules)
    if ({name, full_ps(p.get('name'), rules)} - {''}) & record_name_keys(rec['names'], rec['layer'], rules): return False
    own = pin_hold(rec, pin_of(p), rules)
    return any(full(parks[r].get('name'), rules) != name and r not in wanting and pin_of(parks[r]) is not None
               and rival_claims(r, rec, ctx) and pin_hold(rec, pin_of(parks[r]), rules) >= own for r in reached)


def pin_hold(rec, pin, rules):
    """Rule contested_name: 2 = the pin is inside the record, 1 = near it (pin_near), 0 = neither. A rival whose pin is only
    near does not outweigh a park whose pin is inside (TX US-3035 Lyndon B. Johnson State Park keeps its own record; the
    National Historical Park's pin is 41 m outside it)."""
    if pin is None or not pin_near(rec, pin, rules): return 0
    return 1 if rec.get('line') or not inside(pin[1], pin[0], shape(rec)) else 2


def name_groups(p, ref, ctx):
    """Step 3 search for one park: -> (groups {gkey: [record i]}, notes set)."""
    pool, rules, pin, notes = ctx['pool'], ctx['rules'], pin_of(p), set()
    own, page, lang = name_reach(p, ref, pool, rules)
    groups = {}
    for i in sorted(own | page | lang):
        rec = pool.recs[i]
        no = refusal(p, ref, rec, i, ctx)
        if no: notes.add(no); continue
        src = 'page' if i in page else 'lang' if i in lang else 'name'
        if other_kind(p, rec, pool, rules, page_name(p, rules) if src == 'page' else None):   # 27 Nov 2026, rule name_kind_agrees
            notes.add('other_kind'); continue
        uv = unit_value(rec, rules)
        if line_by_itself(rec):   # 27 Nov 2026: a line is a group of its own, so it is proven by its own pin or not at all
            groups[(rec['layer'], 'line', rec['id'], src)] = [i]; continue
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
        and abs(sa - sb) <= rules['numbers']['two_sources_tol'] * max(sa, sb) and not_a_copy(a, b, rules)


def two_sources(p, groups, pool, rules):
    """{group: ('name+two_sources', evidence)} for the named pairs that agree, near the pin."""
    pin, out = pin_of(p), {}
    named = [(g, pool.recs[i]) for g in sorted(groups) for i in groups[g]
             if pin is None or km_to_box(pin[0], pin[1], rec_box(pool.recs[i])) <= rules['numbers']['near_km']]
    for x, (ga, a) in enumerate(named):
        for gb, b in named[x + 1:]:
            if two_sources_ok(a, b, rules):
                e = {'source_a': a['id'], 'acres_a': agency_acres(a, rules), 'service_a': a['svc'],
                     'source_b': b['id'], 'acres_b': agency_acres(b, rules), 'service_b': b['svc']}
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
        if other_kind(p, rec, pool, rules): continue   # 27 Nov 2026, rule name_kind_agrees (a herd area, ACEC ... is no shorter name)
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


def park_is_piece(p, rules):
    """Rule piece_park_no_siblings (27 Nov 2026): the park's own name ends in a piece word (Partridge Valley East Protected
    Area): the park is a piece itself, so the other pieces (Partridge Valley West) are not its land."""
    return any(piece_base(k, rules) != k for k in park_name_keys(p.get('name'), p.get('type'), rules))


def suffix_pieces(p, ref, rs, ctx):
    """Rule piece_suffix: records of the same layer whose name is a joined record's name but for a trailing piece word (East,
    Unit 2, a number ...), within near_km of the pin or of a joined piece, every refusal applied. Never across layers. A park
    that is a piece itself takes no sibling pieces (rule piece_park_no_siblings)."""
    pool, rules, pin = ctx['pool'], ctx['rules'], pin_of(p)
    if park_is_piece(p, rules): return list(rs)
    cands = set()
    for i in rs:
        rec = pool.recs[i]
        for n in rec['names']:
            base = piece_base(full(n, rules), rules)
            if not generic(base, rules): cands |= pool.base_ix.get((rec['layer'], base), set())
    cands = sorted(i for i in cands - set(rs) if not line_by_itself(pool.recs[i]) and not refusal(p, ref, pool.recs[i], i, ctx))
    return chain_pieces(cands, pin, pool, rules, seeds=list(rs)) if cands and pin else list(rs)


def is_trail(p, rules):
    """Rule trail_layer_not_in_store: a trail park."""
    return bool(rules['_trail_kind_rx'].search(f"{p.get('type') or ''} {p.get('name') or ''}"))


def reason_for(p, groups, notes, twice, rules, own_file=False, gap=False):
    """Step 4: the one pin-only reason code for a park step 3 could not prove (fixed list). own_file (27 Nov 2026): the park's
    own trail-bot file is in the store, so record_layer_not_in_store would be untrue; the file carries the park's name and
    number but the pin is too far from its line, which is what name_but_no_pin_or_size_proof says.
    gap (27 Nov 2026, rule reason_store_gap): the park's own area has a layer gap; a park with no record of its name then says
    no_record_store_gap (the record may sit in the missing layer). Every other reason, and a trail park, is unchanged."""
    if twice: return 'two_records_fit'
    if (groups or own_file) and pin_of(p) is None: return 'park_has_no_pin'
    if groups or own_file: return 'name_but_no_pin_or_size_proof'
    if notes & {'held', 'other_name', 'other_pin'}: return 'record_shared_with_another_park'
    if 'water' in notes: return 'water_only'
    if 'office' in notes: return 'office_only'
    if 'other_kind' in notes: return 'name_on_other_kind_of_land'   # 27 Nov 2026, rule name_kind_agrees
    if notes & {'far', 'not_fee', 'easement'}: return 'name_but_no_pin_or_size_proof'
    if is_trail(p, rules): return 'record_layer_not_in_store'
    return 'no_record_store_gap' if gap else 'no_record_with_this_name'


BY_ORDER = ('name+pin', 'name+size', 'name+two_sources', 'page name+pin', 'page name+size', 'page name+two_sources',
            'two-language name+pin', 'two-language name+size', 'two-language name+two_sources', 'longer or shorter name+pin')
TRAIL_BY = 'trail bot file+pin'


def trail_file_pin_ok(rec, pin, rules):
    """Rule trail_bot_pin (owner 27 Nov 2026, 5:45 AM: "Yes to trails"): the park's own trail-bot file joins only when the pin
    is within line_pin_m (100 ft) of its line."""
    return line_pin_near(rec, pin, rules)


def trail_file_ok(ref, p, rec, rules):
    """Rules trail_bot_file / trail_bot_pin: the record is the trail bot's file for THIS park number and the pin is within
    line_pin_m of the line. Used by the step and again by the gate."""
    return trail_file_ref(rec, rules) == norm_val(ref) and trail_file_pin_ok(rec, pin_of(p), rules)


def trail_proof(rec, pin):
    """The plain proof words of a trail-bot join: the file for this park and the pin's distance to the line in feet."""
    m = line_m(pin[1], pin[0], rec['_p'])
    f = rec.get('source_file') or f"{rec['id']}"
    return {'by': TRAIL_BY, 'layer': rec['layer'], 'pin_near': rec['id'], 'pin_m': round(m, 1), 'pin_ft': round(m / 0.3048),
            'proof': f"the trail bot's file for this park ({f}), the pin {round(m / 0.3048)} ft from the line"}


def step_trail_files(refs, ctx):
    """Rule trail_bot_file (27 Nov 2026), after steps 2 and 3, for every park: the park's own trail-bot file (found by its park
    number only, never by name) joins the park when the pin is within line_pin_m of its line. It adds the line to land that
    step 2 or 3 proved, or it is the park's only record. It never joins another park, and its name proves nothing. Refused when
    the line holds the pin of another park with the same name (the gate checks that too). -> {ref: {record i: proof}}."""
    parks, pool, rules, out = ctx['parks'], ctx['pool'], ctx['rules'], {}
    for ref in sorted(refs):
        p = parks[ref]
        for i in pool.trail_ix.get(norm_val(ref), []):
            rec = pool.recs[i]
            if not trail_file_ok(ref, p, rec, rules): continue
            if holds_other_pin(ref, rec, ctx['same_name'].get(full(p.get('name'), rules), ()), parks, rules): continue
            out.setdefault(ref, {})[i] = trail_proof(rec, pin_of(p))
    return out


def step_name(refs, ctx):
    """Step 3 for all parks: -> ({ref: [record i]}, {ref: (by, evidence)}, {ref: reason code})."""
    parks, pool, rules = ctx['parks'], ctx['pool'], ctx['rules']
    want, ev, why = {}, {}, {}
    ctx['reach'] = {r: set().union(*name_reach(parks[r], r, pool, rules)) for r in sorted(ctx['refs'])}   # rule contested_name
    for ref in refs:
        p = parks[ref]
        groups, notes = name_groups(p, ref, ctx)
        wit = size_witnesses(p, ctx['shared_names'], rules)
        pinned, sized = {}, {}
        for g in sorted(groups):
            r = prove_group(p, groups[g], pool, rules, wit)
            if r: (pinned if r[0] == 'name+pin' else sized)[g] = r
        sized.update(two_sources(p, {g: rs for g, rs in groups.items() if g not in pinned and g not in sized}, pool, rules))
        sized = {g: v for g, v in sized.items() if not size_contradicts(groups, v, wit, pool, rules)   # 27 Nov 2026
                 and not far_proof_other_state(p, groups[g], pool)}
        page = lambda d: {g: ({'page': 'page ', 'lang': 'two-language '}.get(g[3], '') + v[0], v[1]) for g, v in d.items()}
        pinned, sized = page(pinned), page(sized)
        twice = ambiguous_sizes(sized)
        proven = {**pinned, **{g: v for g, v in sized.items() if g not in twice}}
        if not proven or pin_beats_far_proof(proven):   # 27 Nov 2026: the pin's own land beats a far two-sources proof
            cp, more = core_records(p, ref, ctx)
            if not proven or pin_land_wins(proven, cp, {**groups, **more}, pool, rules, park_size_any(p, wit)):
                proven, groups = cp, {**groups, **more}
        if proven:
            want[ref] = {g: suffix_pieces(p, ref, groups[g], ctx) for g in proven}
            ev[ref] = proven
        else:
            why[ref] = reason_for(p, groups, notes, twice, rules, own_file=bool(pool.trail_ix.get(ref)), gap=bool(ctx.get('gaps')))
    want = contested_filter(want, ctx)   # 27 Nov 2026, rule contested_name
    claims = {}
    for ref, gs in want.items():
        for i in {i for rs in gs.values() for i in rs}: claims.setdefault(i, []).append(ref)
    bad = resolve_claims(claims, parks, rules)
    keep = share_claims(bad, claims, 3, ctx)   # 27 Nov 2026: a park that proves the record on its own keeps it
    note_same_land(keep, ctx)
    out, by = {}, {}
    for ref in sorted(want):
        gs = {g: rs for g, rs in want[ref].items() if not {i for i in bad if ref not in keep[i]} & set(rs)}
        if not gs:
            why[ref] = 'record_shared_with_another_park'; continue
        out[ref] = sorted({i for rs in gs.values() for i in rs})
        best = next(k for k in BY_ORDER if k in {ev[ref][g][0] for g in gs})
        by[ref] = (best, {'proofs': [dict(ev[ref][g][1], by=ev[ref][g][0], layer=g[0]) for g in sorted(gs)]})
    return out, by, why


def match_state(refs, parks, pool, rules, locks=None, gaps=()):
    """Steps 2-4 for one state, then the lock witness. -> {'joins', 'how', 'why', 'id_notes', 'locks_out', 'lock_status',
    'locked_broken'}."""
    names_by_full, cnt = {}, {}
    for ref, p in parks.items(): names_by_full.setdefault(full(p.get('name'), rules), set()).add(ref)
    for ref in refs: cnt[full(parks[ref].get('name'), rules)] = cnt.get(full(parks[ref].get('name'), rules), 0) + 1
    same_name = {k: sorted(v) for k, v in names_by_full.items() if len(v) > 1}
    ctx = {'parks': parks, 'refs': set(refs), 'pool': pool, 'rules': rules, 'names_by_full': names_by_full,
           'same_name': same_name, 'shared_names': {k for k, c in cnt.items() if c > 1}, 'gaps': list(gaps)}
    ctx['taken'], ctx['same_land'] = set(), {}
    got, ev, notes, pieces = step_id(refs, ctx)
    joins = dict(got)
    how = {ref: (2, 'id', ev[ref]) for ref in got}
    ctx['taken'] = {i for rs in got.values() for i in rs}
    got3, by, why = step_name([r for r in refs if r not in joins], ctx)
    for ref, rs in got3.items(): joins[ref], how[ref] = rs, (3, by[ref][0], by[ref][1])
    today = {ref: lock_rows(pool, got[ref], how[ref][2]['id_value'], rules) for ref in sorted(got)}   # the id's records only
    trail = step_trail_files(refs, ctx)   # 27 Nov 2026, owner: "Yes to trails"
    for ref, got_t in sorted(trail.items()):
        proofs = [got_t[i] for i in sorted(got_t)]
        if ref not in joins:
            joins[ref], how[ref] = sorted(got_t), (3, TRAIL_BY, {'proofs': proofs}); continue
        joins[ref] = sorted(set(joins[ref]) | set(got_t))
        step, b, e = how[ref]
        how[ref] = (step, b, dict(e, proofs=e['proofs'] + proofs) if step == 3 else dict(e, trail_file_proofs=proofs))
    ctx.update(today=today, notes=notes, shared=shared_ids(refs, parks, rules))
    status, broken = compare_locks(locks or {}, ctx)
    return {'joins': joins, 'how': how, 'why': {r: c for r, c in why.items() if r not in joins}, 'locks_out': today, 'pieces': pieces,
            'lock_status': status, 'locked_broken': broken, 'trail': trail,
            'same_land': {i: v for i, v in sorted(ctx['same_land'].items()) if all(i in joins.get(r, ()) for r in v)},
            'share_ctx': {'shared_names': ctx['shared_names']}}


# ---------------------------------------------------------------------------------------------------------------- gate
def gate_old_ids(doc_parks):
    """Rule gate_old: no record id ends in ~old."""
    return [('old_ids', ref, str(x[0])) for ref, p in sorted(doc_parks.items()) for x in (p.get('m') or []) + (p.get('c') or [])
            if str(x[0]).endswith('~old')]


def gate_two_names(doc_parks, allowed=None):
    """Rule gate_two_name: no record id on two parks under two names (record names, and POTA's park names with brackets).
    27 Nov 2026 (rule gate_same_land): one record on parks of two names passes only when shared_allowed, measured again here,
    lets every one of those parks hold it ('same land, two park numbers'). Two record names under one id still fail."""
    by_id, allowed = {}, allowed or {}
    for ref, p in sorted(doc_parks.items()):
        for x in p.get('m') or []:
            if nk(x[1]):
                v = by_id.setdefault(str(x[0]), (set(), set(), set())); v[0].add(nk(x[1])); v[1].add(nk(p.get('n'))); v[2].add(ref)
    return [('two_name', i, ' / '.join(sorted(v[1]))) for i, v in sorted(by_id.items())
            if len(v[0]) > 1 or (len(v[1]) > 1 and not v[2] <= allowed.get(i, set()))]


def shared_allowed(res, pool, rules, parks):
    """Rule gate_same_land (27 Nov 2026): the records the gate lets two parks of two names share, measured again on their own
    terms (each park's own proof and size, the same functions the step used), so a step that regresses is caught.
    -> {record id: {refs}}."""
    ctx = dict(res.get('share_ctx') or {'shared_names': set()}, rules=rules, pool=pool, parks=parks)
    out = {}
    for i, refs in sorted((res.get('same_land') or {}).items()):
        rec = pool.recs[i]
        if all(i in res['joins'].get(r, ()) and own_proof(parks[r], r, rec, res['how'][r][0], ctx) and size_fits_record(parks[r], rec, ctx)
               for r in refs):
            out.setdefault(str(rec['id']), set()).update(refs)
    return out


def gate_unresolved(res, pool):
    """Rule gate_not_in_file: every id written in a key row resolves to exactly one raw record of today's file."""
    bad = []
    for ref, rs in sorted(res['joins'].items()):
        for i in rs:
            rec = pool.recs[i] if isinstance(i, int) and 0 <= i < len(pool.recs) else None
            raw = pool.raw_ids.get((rec['area'], rec['layer'], rec['id'])) if rec else None
            if not raw or len(raw) != 1 or raw[0] != rec['key']: bad.append(('not_in_file', ref, str(rec['id'] if rec else i)))
    return bad


def gate_id_mismatch(res, pool, rules, parks=None):
    """Rule gate_id_mismatch: every id-proven park's records carry that id (or are project pieces of one that does). The
    park's own trail-bot file is checked on its own terms instead (rule trail_bot_file, re-measured here, 27 Nov 2026)."""
    bad = []
    for ref, rs in sorted(res['joins'].items()):
        step, by, e = res['how'][ref]
        if by != 'id': continue
        own = set((res.get('trail') or {}).get(ref, {}))
        if own:
            if parks is None or not all(trail_file_ok(ref, parks[ref], pool.recs[i], rules) for i in own):
                bad += [('id_mismatch', ref, pool.recs[i]['id']) for i in sorted(own)]
            rs = [i for i in rs if i not in own]
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
    allowed = shared_allowed(res, pool, rules, parks) if parks else {}   # 27 Nov 2026: same land, two park numbers
    bad = gate_old_ids(doc_parks) + gate_two_names(doc_parks, allowed) + gate_unresolved(res, pool) + gate_id_mismatch(res, pool, rules, parks) \
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
            own = (res.get('trail') or {}).get(ref, {})
            rows = sorted(([pool.recs[i]['id'], pool.recs[i]['name'], round(rec_acres(pool.recs[i], rules)),
                            'piece of id unit' if i in res.get('pieces', ()) else TRAIL_BY if i in own else tag]
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
            mark = same_land_mark(ref, res, pool, parks)   # 27 Nov 2026: only on a park that shares a record; others unchanged
            if mark: out[ref]['same_land'] = mark
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


def same_land_mark(ref, res, pool, parks):
    """Rule key_same_land (27 Nov 2026): the plain mark on a park that shares a record with a park of another name:
    {'note': 'same land, two park numbers', 'with': [{'ref', 'name', 'record'}]}; None for every other park."""
    rows = [{'ref': o, 'name': parks[o].get('name'), 'record': pool.recs[i]['id']}
            for i, refs in sorted((res.get('same_land') or {}).items()) if ref in refs for o in sorted(refs) if o != ref]
    return {'note': SAME_LAND, 'with': rows} if rows else None


def shared_rows(st, res, pool, rules, parks):
    """Rule shared_records_report (27 Nov 2026, the owner: "Write every allowed shared-record pair to a small report list so reps
    can spot dual-agency 2-fers vs. POTA duplicates"): one row per record and pair of parks for v2-shared-records.csv."""
    out = []
    for i, refs in sorted((res.get('same_land') or {}).items()):
        rec, rs = pool.recs[i], sorted(refs)
        for x, a in enumerate(rs):
            for b in rs[x + 1:]:
                wa = size_witnesses(parks[a], (res.get('share_ctx') or {}).get('shared_names', set()), rules)
                wb = size_witnesses(parks[b], (res.get('share_ctx') or {}).get('shared_names', set()), rules)
                out.append([a, st, parks[a].get('name'), b, parks[b].get('name'), rec['key'], rec['layer'], rec['name'],
                            round(rec_acres(rec, rules), 1), refs[a], refs[b], ' '.join(f'{w:g}' for w in wa), ' '.join(f'{w:g}' for w in wb)])
    return out


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
        own = (res.get('trail') or {}).get(ref, {})
        for i in res['joins'][ref]:
            rec = pool.recs[i]
            rb, re_ = (TRAIL_BY, own[i]) if i in own else (by, e)   # 27 Nov 2026: a trail-bot row shows its own proof words
            out.append([ref, st, rec['key'], rec['id'] if rec['agency'] else '', rec['layer'], rec['name'], round(rec_acres(rec, rules), 1),
                        step, rb, ' '.join(f'{k}={re_[k]}' for k in sorted(re_)), rec['area'], '' if i in own else lock, shape_word(rec),
                        '' if rec.get('pub') is None else str(rec['pub']).lower(), rec.get('lic') or ''])
    return out


def id_other_names(st, res, parks, pool, rules):
    """Rule id_other_names_report: id-joined records that share no real place word with the park's name (changes no join)."""
    out = []
    for ref in sorted(res['joins']):
        if res['how'][ref][0] != 2: continue
        p, pin = parks[ref], pin_of(parks[ref])
        words = real_words(p.get('name'), rules)
        for i in [i for i in res['joins'][ref] if i not in (res.get('trail') or {}).get(ref, {})]:   # trail files: not id records
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
    out = {k: r[k] for k in ('key', 'layer', 'record_name', 'q', 'shape', 'publishable', 'licence_class', 'publish_why',
                             'source_file') if k in r}
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


def pota_fallback(repo, area):
    """Rule facts_fallback_pota_list (27 Nov 2026, grade item 6): {ref: {'name', 'pin'}} from POTA's own list, for a park the
    park facts do not know yet (or know without a name)."""
    d = read_gz_json(os.path.join(repo, 'data', 'pota', 'saved', 'parks', f'{area_of(area)}.json.gz'))
    out = {}
    for x in d.get('data') or []:
        if not x.get('reference'): continue
        row = {'name': str(x.get('name') or '').strip()}
        if x.get('latitude') not in (None, '') and x.get('longitude') not in (None, ''): row['pin'] = [x['latitude'], x['longitude']]
        out[str(x['reference'])] = row
    return out


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
    """One area: load, match, gate, write. -> (exit code, proof rows, pin rows, other-name rows, shared-record rows)."""
    t0, st = time.time(), area_label(area)
    rules = rules_for_area(rules, area)
    clear_old_outputs(a.out, area)
    own = layer_file(area)
    try: refs = park_list(a.repo, area)
    except (OSError, ValueError):
        print(f'{st}: park list not found.'); info['not_built'] = 'no park list'; return 2, [], [], [], []
    if own is None:
        print(f'{st}: layer file not found.'); info['not_built'] = 'no layer file'; return 2, [], [], [], []
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
    # 27 Nov 2026, rule acres_field_guard: a layer whose acres field disagrees with its own outlines is not used for sizes
    info['acres_field_off'], info['acres_field_checked'] = acres_field_check(pool, rules)
    listed = park_states(a.repo, area)
    parks = {r: dict(facts.get(r) or {'name': '', 'type': ''}, listed_in=listed.get(r) or []) for r in refs}
    for r, row in pota_fallback(a.repo, area).items():   # 27 Nov 2026: facts without the park, or without its name: POTA's list
        if r in parks and not str(parks[r].get('name') or '').strip():
            parks[r]['name'] = row['name']
            if not parks[r].get('pin') and row.get('pin'): parks[r]['pin'] = row['pin']
    for r, p in facts.items():
        if r not in parks and str(p.get('area') or '') in [area] + nbs: parks[r] = p
    locks = {}
    if a.locks and os.path.isfile(os.path.join(a.locks, 'locks', f'{area}.json')):
        with open(os.path.join(a.locks, 'locks', f'{area}.json'), encoding='utf-8') as f: locks = json.load(f).get('locks') or {}
    res = match_state(refs, parks, pool, rules, locks, gaps)   # the park's own area's gaps only, never neighbour_gaps
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
        print(f'{st}: GATE FAILED, key not written. {len(g["bad"])} broken row(s), listed in v2-run.json.'); return 4, [], [], [], []
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
    info['same_land_records'] = len(res['same_land'])   # 27 Nov 2026: records two parks of two names share (v2-shared-records.csv)
    return (3 if gaps else 0), proof_rows(st, res, pool, rules), pins, id_other_names(st, res, parks, pool, rules), \
        shared_rows(st, res, pool, rules, parks)


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
    proof_all, pin_all, other_all, shared_all = [], [], [], []

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
        c, pr, pn, on, sh = build_state(area, a, rules, facts, layer_file, info)
        code = 4 if 4 in (code, c) else max(code, c)
        proof_all += pr; pin_all += pn; other_all += on; shared_all += sh
        later = {x for b in areas[n + 1:] for x in [b] + area_neighbours(b, rules)}
        for k in [k for k in cache if k not in later]: del cache[k]   # rule memory: keep only files a later area reads
    write_csv(os.path.join(a.out, 'v2-proof.csv'), ['ref', 'st', 'file_key', 'agency_id', 'layer', 'record_name', 'acres', 'step', 'by',
                                                    'evidence', 'file_area', 'lock', 'shape', 'publishable', 'licence_class'], proof_all)
    write_csv(os.path.join(a.out, 'v2-pin-only.csv'), ['ref', 'st', 'name', 'kind', 'reason_code', 'reason'], pin_all)
    write_csv(os.path.join(a.out, 'v2-id-other-names.csv'), ['ref', 'st', 'park_name', 'record_key', 'record_name', 'layer',
                                                             'km_from_pin'], other_all)
    # 27 Nov 2026: every record two parks of two names share, with each park's own proof and official size (rule shared_records_report)
    write_csv(os.path.join(a.out, 'v2-shared-records.csv'), ['ref', 'st', 'name', 'other_ref', 'other_name', 'record_key', 'layer',
                                                             'record_name', 'record_acres', 'proof', 'other_proof', 'official_acres',
                                                             'other_official_acres'], shared_all)
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
