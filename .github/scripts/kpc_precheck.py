#!/usr/bin/env python3
"""PRE-CHECK STAGE (mapping agent, Nov 3 2026, step 4 of the remake; PROPOSED_RULES 'Pre-check' + Brandon 5:30 PM 'when there is any doubt
about a park's pin or match, drop it from the key and put it in a review pile'). Runs BEFORE a key build is handed on, over EVERY park in
the US, Canada and world keys. No network, decides nothing on its own, never edits a key file, never moves a POTA pin.
  * a park a PERSON approved (every joined row 'reviewed' and not a bot's auto YES) gets the LIGHT check: 0,0 pin, pin way out,
    county contradiction, broken row. Anything found goes to Brandon; the join is NOT dropped (rule 22: a person beats a bot).
  * every other park gets the FULL scorecard: the light check + no official boundary, misnamed (POTA spells it differently = MISNAMED; shares no real word = NAME_MISMATCH,
    a doubt), wrong kind (refuge / wilderness / hatchery ... on the park vs the record), WWFF county vs kff_cty.tsv
    (read from the county check's pota_pins_vs_wwff_counties.csv when given), lost finds (data/us-key/lost-finds.json).
  * a joined park with a DOUBTFUL pin or match that no person approved -> review-pile.csv (action 'hold': drop from the key until a
    person looks; the builders do that only when KPC_PRECHECK_HOLD=1 and they read review-hold.json). Only the pieces no person
    reviewed are ever held: a park that keeps a person-reviewed piece stays outlined and is flagged (rule 22; Quality must-fix 1, Nov 3).
  * a bad POTA pin (0,0, lat/lon swapped, or no pin at all) is POTA's data error, not a doubt about our outline (Brandon's ruling,
    relayed by Super via Quality 6:45 PM CST Nov 3, for Brandon to confirm on the PR): when the POTA name matches the official
    record's name AND the record is in the park's own area (name_area_backs), the pin is taken as the error, the outline stays and
    the park is flagged BAD_POTA_PIN_NAME_MATCH. When the name or the area does not back the match it is BAD_POTA_PIN_UNBACKED,
    a doubt -> the review pile as before.
  * ADDENDUM (Brandon, relayed by Super via Quality 6:54 PM CST Nov 3, for Brandon to confirm on the PR): POTA pins and names are
    not a golden rule. A bad-pin park whose POTA name is very close to the joined record's name keeps its outline PENDING MAPPING'S
    CHECK even when the area test is not backed offline: BAD_POTA_PIN_NAME_ONLY (a flag, not a doubt, never held). Only a bad-pin
    park whose name does NOT match any joined record stays BAD_POTA_PIN_UNBACKED (a doubt -> review pile). A bad-pin park with no
    outline is BAD_POTA_PIN_NO_OUTLINE (flagged, never demoted). Every bad-pin park is written ONCE to BAD_POTA_PIN_FLAGS.csv for
    a person, with the reason, the record id(s), the official name(s) and the POTA name. data/review/precheck-notes.json holds
    Mapping's check of a NAME_ONLY park ('mapping_checked') and parks put to Brandon with a proposal that is NOT applied
    ('ask_brandon': a REVIEW_PILE row 'ASK BRANDON', never held).
Writes OUT (default data/review/precheck): scorecard.csv (one row per park with any flag), the batch CSVs misnamed.csv, pin-way-out.csv,
no-official-boundary.csv, wrong-kind.csv, pota-0-0.csv, county.csv, lost-finds-routed.csv, review-pile.csv, review-hold.json, counts.json,
BAD_POTA_PIN_FLAGS.csv.
  python3 .github/scripts/kpc_precheck.py [--apply-hold]      env DATA (KPC-Data checkout, for the world keys), KFF_COUNTY_CSV, OUT, PRECHECK_ONLY=US-DE,CA-PE
--apply-hold (only with KPC_PRECHECK_HOLD=1; for the workflow, on the freshly BUILT key files before they are saved): each park in
review-hold.json has its joined rows moved to the candidates with 'held for review (pre-check): <why>' and becomes a pin until a
person answers (the same move KPC_SELF_CHECKS=hold makes in kpc_us_key.py). A person-reviewed piece is never moved: a park keeps
those pieces (and its outline) and only its other pieces are held.
Exit 0 on a finished run; on a crash it prints an ::error, writes counts.json with status 'red' and exits 1 (Quality, Nov 3)."""
import collections, csv, glob, gzip, json, os, pathlib, re, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import kpc_key_rules as KR  # noqa: E402

OUT = pathlib.Path(os.environ.get('OUT') or 'data/review/precheck')
DATA = pathlib.Path(os.environ.get('DATA') or 'kpcdata')
ONLY = {x.strip().upper() for x in (os.environ.get('PRECHECK_ONLY') or '').split(',') if x.strip()}
# the same kind tags kpc_us_key.py uses for its self-check (TAGS there); kept in step by tests/test_precheck_nov3.py
TAGS = [('memorial', r'national memorial'), ('refuge', r'wildlife refuge|\bnwr\b'), ('wilderness', r'wilderness(?! study)'),
        ('water', r'reservoir|fishing lake'), ('beach', r'\bbeach\b'), ('access', r'fishing access|access site'),
        ('wildforest', r'wild forest'), ('stateforest', r'state forest'), ('hatchery', r'hatchery')]
WEAK = ('name', 'name-only')
MULTI = re.compile(r'wetland management district|national forest|state forest|trail|river|grassland|complex|national recreation area|'
                   r'national (?:park|preserve|seashore|lakeshore|conservation area|monument)|wilderness|byway|parkway|heritage area|refuge', re.I)   # a join found by name alone (not a person, not the pin)


def tags(x):
    x = str(x or '').lower(); return {k for k, r in TAGS if re.search(r, x)}


SAME_PLACE = [{'access', 'water'}, {'access', 'beach'}]   # DE 'X Pond and Access Site' IS the state fishing lake (small-state test, Nov 3)


def kind_ok(t, nm):
    a, b = tags(t), tags(nm)
    if not a or not b: return None
    return bool(a & b) or any(x in pair and y in pair for pair in SAME_PLACE for x in a for y in b)


def _sq(t):
    return re.sub(r'[^a-z0-9]', '', __import__('unicodedata').normalize('NFKD', KR.nf(t)).encode('ascii', 'ignore').decode())


def _sq2(t):
    return re.sub(r"['’.]", '', __import__('unicodedata').normalize('NFKD', KR.nf(t)).encode('ascii', 'ignore').decode().lower())


# Nov 3 addendum (Quality grade of the recut, should-fix; Super relayed Brandon 7:11-7:12 PM CST, item 3): rule 18 in the name test.
# A word that tells one piece from another is never 'the same place': North / South Fork, Upper / Lower, Unit 2 / Unit 3, and a
# POTA name's own qualifier in brackets ('Riviere Malbaie (CNC/Stallman)') that the record does not carry.
# Quality grade of the addendum (should-fix 1, 7:35 PM CST Nov 3): French compass words too. Accents are stripped and a hyphen splits
# words before this test (KR._plain_words), so 'Nord-Est' = {'nord', 'est'} and 'Rivière Bonaventure Ouest' carries 'ouest'.
_R18_FR = {'nord', 'sud', 'est', 'ouest', 'nordest', 'nordouest', 'sudest', 'sudouest'}
_R18_ONESIDE = _R18_FR | {'north', 'south', 'east', 'west', 'northeast', 'northwest', 'southeast', 'southwest', 'upper', 'lower', 'middle', 'inner', 'outer'}
_R18_CLASSES = ({'north', 'south', 'east', 'west', 'northeast', 'northwest', 'southeast', 'southwest',
                 'nord', 'sud', 'est', 'ouest', 'nordest', 'nordouest', 'sudest', 'sudouest'},
                {'upper', 'lower', 'middle'}, {'big', 'little', 'great', 'lesser'}, {'inner', 'outer'},
                {'first', 'second', 'third', 'fourth', 'fifth'})
_ROMAN = re.compile(r'^(?:ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii)$')


def unbracket(t):
    """links-09 (Nov 4 2026): a name with its bracketed qualifiers taken off ('Dunbar Cave (Lower Tract)' -> 'Dunbar Cave').
    Rule 18 v5 (Brandon, Super Head Bot chat, 7:43 PM CST Nov 3, relayed via Super Head Bot: "Yes"; relayed (paraphrase of the
    question he answered Yes to): bracket qualifiers do not count; one-side compass words in English or French do).
    Same rule as KPC-Links kpc_fers_guard.unbracket (links-02)."""
    return re.sub(r'\s+', ' ', re.sub(r'\([^)]*\)|\[[^\]]*\]', ' ', str(t or ''))).strip()


def rule18_differs(park, rec, brackets=False):
    """'' when nothing tells the two names apart as pieces; else a plain reason. Uses the key's own rule 18 piece test
    (KR.piece_ok: 'Unit 2' vs 'Unit 3', 'Abo Unit') plus clashing piece words. brackets=True (the bad-pin name test only) also
    asks for a bracketed POTA qualifier ('(CNC/Stallman)').
    Used in the bad-pin name test (name_area_backs) and, since Brandon's ruling relayed by Super 7:26 PM CST Nov 3, beside the
    general name test too: there a park whose joined record rule 18 tells apart gets RULE18_PIECE and a review-pile row, never
    a hold. v5 (Brandon, relayed by Super 7:43 PM CST Nov 3): the general test calls it with brackets=False, so a bracketed place
    qualifier ('(Lewis County)', '(Qld)') no longer counts there; the bad-pin test keeps brackets=True.
    links-09 (Nov 4): with brackets=False a difference counts only when it is there BOTH on the full names AND on the names with
    their bracket text taken off, so bracket text can neither make a piece ('(Lower Tract)' read by KR.piece_ok as the piece 'lower',
    a one-side '(South)') nor hide one. links-11: POTA 'Langres Nord' vs record 'Langres (secteur Nord)' (the word only inside the
    other name's bracket) is flagged for the review pile, not passed.
    One exception, kept on purpose: when BOTH names carry bracket text and it clashes ('Horseshoe Canyon (South)' vs
    'Horseshoe Canyon (North)', '(No. 1)' vs '(No. 2)', '(0130)' vs '(0189)'), the two records are different pieces, not a
    qualifier on one side, so the row stays a review-pile flag (flag only, never held). brackets=True (the bad-pin test) is unchanged."""
    if not brackets:
        u = (unbracket(park) or park, unbracket(rec) or rec)
        if u != (park, rec):
            w = _rule18_core(park, rec, False)
            if w and _rule18_core(*u, False): return _rule18_core(*u, False)
            if w and _bracket_text(park) and _bracket_text(rec) and ("' vs '" in w or 'number' in w):
                return w + ' (both names carry a different bracketed piece)'
            # links-11 (Nov 4, Quality's v2 grade, should-fix 3, YES'd by Super's 7:15 AM CST relay): a compass / position word that
            # one name carries OUTSIDE brackets and the other only INSIDE its bracket ('Langres Nord' vs 'Langres (secteur Nord)')
            # may or may not be the same piece: a review-pile flag (never a hold), not a silent pass.
            ua, ub = set(KR._plain_words(u[0])), set(KR._plain_words(u[1]))
            pa, pb = (ua & _R18_ONESIDE) - ub, (ub & _R18_ONESIDE) - ua
            if (pa or pb) and not (pa and pb):
                inb = (pa or pb) & set(KR._plain_words(_bracket_text(rec if pa else park)))
                if inb: return (f"rule 18: '{' '.join(sorted(inb))}' names a piece in one name but sits only inside the other name's bracket "
                                f"({_bracket_text(rec if pa else park)}): check it is the same piece")
            return ''
    return _rule18_core(park, rec, brackets)


def _bracket_text(t): return ' '.join(a or b for a, b in re.findall(r'\(([^)]*)\)|\[([^\]]*)\]', str(t or ''))).strip()


def _rule18_core(park, rec, brackets):
    ok, why = KR.piece_ok(park, rec)
    if not ok: return why
    a, b = set(KR._plain_words(park)), set(KR._plain_words(rec))
    for cl in _R18_CLASSES:
        pa, pb = (a & cl) - b, (b & cl) - a
        if pa and pb: return f"rule 18: '{' '.join(sorted(pa))}' vs '{' '.join(sorted(pb))}' are different pieces"
    # Quality should-fix 1: a compass / position word on ONE side only ('Rivière Bonaventure' vs 'Rivière Bonaventure Ouest') is a piece.
    # v5 (Brandon, relayed by Super 7:43 PM CST Nov 3): English words too (North/South/East/West, Upper/Lower/Middle, Inner/Outer),
    # in both the bad-pin and the general test. Not big/little/great or ordinals (they are ordinary name words, 'Great Swamp').
    if True:
        cw = _R18_ONESIDE; pa, pb = (a & cw) - b, (b & cw) - a
        if (pa or pb) and not (pa and pb): return f"rule 18: '{' '.join(sorted(pa or pb))}' names only one piece"
    nat = lambda x: set(KR._plain_words(re.sub(r'(?i)natura\s*2000', ' ', str(x or ''))))   # 'Natura 2000' is a network, not a piece number
    na = {str(int(w)) if w.isdigit() else w for w in nat(park) if w.isdigit() or _ROMAN.match(w)}; nb = {str(int(w)) if w.isdigit() else w for w in nat(rec) if w.isdigit() or _ROMAN.match(w)}
    if na and nb and not (na & nb): return f"rule 18: number {' '.join(sorted(na))} vs {' '.join(sorted(nb))} are different pieces"
    for q in (re.findall(r'\(([^)]*)\)', str(park or '')) if brackets else []):
        qw = {w for w in KR._plain_words(q) if len(w) >= 3 and w not in KR._STOP}
        if qw and not (qw & b) and not any(KR._ed1(w, h) for w in qw for h in b):
            return f"rule 18: the POTA name's qualifier ({q.strip()}) is not in '{rec}'"
    return ''


# Quality grade of the addendum (should-fix 2): words that do not tell one place from another (English ones are in KR._STOP)
_GENERIC = {'de', 'la', 'le', 'les', 'du', 'des', 'riviere', 'lac', 'reserve', 'reserves', 'naturelle', 'parc', 'ile', 'iles', 'baie',
            'faunique', 'ecologique', 'provincial', 'provinciale', 'national', 'nationale', 'regional', 'regionale', 'marine', 'aquatique',
            'conservation', 'sanctuary', 'bird', 'migratory', 'deer', 'yard', 'white', 'tailed', 'habitat', 'natural', 'wetland',
            'wetlands', 'marsh', 'island', 'islands', 'bay', 'creek', 'beach', 'point', 'mount', 'mountain', 'protected', 'estuaire',
            'estuary', 'zec', 'zone', 'exploitation', 'controlee', 'natura', '2000', 'naturreservat', 'nationalpark'}


def _dw(t): return {w for w in KR._words(re.sub(r"[\u2019'`-]", ' ', str(t or ''))) if w not in _GENERIC and not w.isdigit()}


def one_word_only(park, rec):
    """True when the two names share exactly ONE telling word and both have more than one ('Estuaire de la Riviere Bonaventure
    Nature Reserve' vs 'Rivière Bonaventure Ouest White-Tailed Deer Yard': only 'bonaventure'). Not the same place by name."""
    import difflib
    a, b = _dw(park), _dw(rec)
    near = {x for x in a if any(x == y or difflib.SequenceMatcher(None, x, y).ratio() >= .85 for y in b)}   # 'France' ~ 'Frances'
    return len(near) == 1 and len(a) > 1 and len(b) > 1


def name_how(park, rec, r18=False):
    """'same' | 'spelling' (the same place written differently: Starski / Stariski, Osborndale / Osbornedale, Carter's / CARTERS)
    | 'other' (shares no real word and is not a spelling variant: a doubtful match; or, with r18=True, rule 18 tells them apart)."""
    if r18 and rule18_differs(park, rec, True): return 'other'   # the bad-pin name test only (see rule18_differs)
    import difflib
    if r18 and _sq(park) != _sq(rec) and one_word_only(park, rec) and difflib.SequenceMatcher(None, _sq(park), _sq(rec)).ratio() < .85:
        return 'other'   # Quality should-fix 2: one shared word is not 'same' (bad-pin name test; when in doubt it is a doubt)
    if KR.id_join_name_ok(park, rec)[0] or _sq(park) == _sq(rec): return 'same'
    import difflib
    a, b = [w.rstrip('s') for w in re.findall(r'[a-z0-9]+', _sq2(park)) if w not in KR._STOP], [w.rstrip('s') for w in re.findall(r'[a-z0-9]+', _sq2(rec)) if w not in KR._STOP]
    A, Bq = ''.join(a), ''.join(b)
    if A and Bq and (A in Bq or Bq in A or any(''.join(a[i:i + 2]) in Bq for i in range(len(a) - 1)) or any(''.join(b[i:i + 2]) in A for i in range(len(b) - 1))): return 'spelling'
    if a and b and max(difflib.SequenceMatcher(None, x, y).ratio() for x in a for y in b if len(x) > 3 and len(y) > 3 or x == y) >= .8 if any(len(x) > 3 for x in a) and any(len(y) > 3 for y in b) else False: return 'spelling'
    if difflib.SequenceMatcher(None, _sq(park), _sq(rec)).ratio() >= .85: return 'spelling'
    return 'other'


def name_how_general(park, rec):
    """links-09 (Nov 4): the general name test (MISNAMED / NAME_MISMATCH) with bracket qualifiers off (rule 18 v5, 7:43 PM CST Nov 3):
    the better of name_how on the full names and on the names without their brackets (same > spelling > other). The bad-pin
    name test (name_how(..., r18=True)) is not changed: there a bracketed POTA qualifier still counts."""
    h = name_how(park, rec)
    if h == 'same': return h
    u = name_how(unbracket(park) or park, unbracket(rec) or rec)
    return min(h, u, key=('same', 'spelling', 'other').index)


def load(p, d):
    try:
        if str(p).endswith('.gz'): return json.load(gzip.open(p, 'rt', encoding='utf-8'))
        return json.load(open(p, encoding='utf-8'))
    except Exception: return d  # noqa: BLE001


def pota_pins():
    """{ref: (name, lat, lon)} from the site's own copies of the POTA list: locations.json (US), data/canada.json, data/northam.json
    and the world tiles data/pota/t/*.json. These are POTA's pins exactly as POTA has them (never moved)."""
    pins = {}
    for f in glob.glob('data/pota/t/*.json'):
        for r in load(f, []):
            if isinstance(r, list) and len(r) >= 4: pins[r[0]] = (r[1], r[2], r[3])
    for f in ('locations.json', 'data/canada.json', 'data/northam.json'):
        d = load(f, [])
        for r in (d.get('rows') or []) if isinstance(d, dict) else d:
            if isinstance(r, list) and len(r) >= 5 and r[0] == 'POTA': pins[r[1]] = (r[2], r[3], r[4])
    return pins


def bad_pin(p):
    if p is None: return 'no POTA pin in data/pota'
    try: la, lo = float(p[1]), float(p[2])
    except (TypeError, ValueError): return 'POTA pin is not a number'
    if la == 0 and lo == 0: return '0,0 pin'
    if not (-90 <= la <= 90 and -180 <= lo <= 180): return f'impossible pin {la},{lo}'
    return ''


def keys():
    """(area, key name, ref, park) for every park in every key file."""
    for f in sorted(glob.glob('data/us-key/US-??.json')) + sorted(glob.glob('data/ca-key/CA-??.json')):
        k = pathlib.Path(f).stem
        for r, p in (load(f, {}).get('parks') or {}).items(): yield k, 'us-key' if k.startswith('US') else 'ca-key', r, p
    for f in sorted(glob.glob(str(DATA / 'data/world-key/??.json'))):
        k = pathlib.Path(f).stem
        for r, p in (load(f, {}).get('parks') or {}).items(): yield k, 'world-key', r, p


def overrides():
    ov = {}
    for f in ('data/us-key/overrides.json', 'data/ca-key/overrides.json'):
        ov.update(load(f, {}).get('parks') or {})
    return ov


AUTO = re.compile(r'auto \(T1|auto: ?true|checked_by.?auto|\(auto\b', re.I)
# Nov 3 addendum (Quality grade of the recut, smaller note; Super relayed Brandon 7:11-7:12 PM CST, item 4): Mapping's own notes and
# calls are a bot desk's, never a person's answer. Same words as kpc_key_answers.DESK_RX (kept in step by tests).
DESK = re.compile(r"\(Mapping(?:,|\)|'s\b| addendum\b| desk\b)|\bMapping, (?:Oct|Nov|Dec)\b|\bMapping's (?:own )?call\b|\bMapping addendum\b|^\s*Mapping[:,]|\bMapping desk\b")


def person_said(o):
    """True when the overrides entry holds a person's (chat 11 / hand review) note, not only bot (auto) notes or Mapping's own
    notes and calls. Rule 22."""
    notes = [x for x in str((o or {}).get('why') or '').split(' · ') if x.strip()]
    return any(not AUTO.search(x) and not DESK.search(x) for x in notes) if notes else True


def person_pieces(p, o):
    """The joined pieces a person reviewed: tagged 'reviewed...' by the key, on a park whose overrides entry is not a bot's alone."""
    m = [x for x in (p.get('m') or []) if isinstance(x, list) and len(x) > 3]
    return [x for x in m if str(x[3]).startswith('reviewed')] if person_said(o) else []


def person_approved(p, o):
    m = [x for x in (p.get('m') or []) if isinstance(x, list) and len(x) > 3]
    return bool(m) and len(person_pieces(p, o)) == len(m)   # every piece reviewed by a person (a bot's auto YES is not a person)


NOT_ONE_AREA = re.compile(r'\bEEA\b|natura 2000|wdpa|protected planet|world database', re.I)   # sources that cover many countries


def _bbox(g):
    xs, ys = [], []
    def walk(c):
        if c and isinstance(c[0], (int, float)): xs.append(c[0]); ys.append(c[1])
        else:
            for q in c or []: walk(q)
    walk((g or {}).get('coordinates') or (g or {}).get('rings'))
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


def outline_bbox(ref):
    """bbox of the park's saved official outline (data/canada-bounds/REF.json, or DATA's data/world-bounds/CC/REF.json), or None."""
    for f in [f'data/canada-bounds/{ref}.json'] + glob.glob(str(DATA / f'data/world-bounds/*/{ref}.json')) + [str(DATA / f'data/world-bounds/{ref}.json')]:
        if os.path.exists(f):
            d = load(f, {}); return _bbox(d.get('geometry') or d)
    return None


def name_area_backs(pota_name, m, area, area_box=None, outline_bb=None, sources=()):
    """Brandon's ruling (relayed 6:45 PM CST Nov 3): with a bad POTA pin, the POTA name must match the official record's name AND
    the record must be in the park's own area. Returns (name_ok, area_ok, how).
    NAME: a joined record whose name is the POTA name ('same') or the same place spelled differently ('spelling', name_how).
    AREA (any one, all offline):
      1. the record is on the state's own layer (id 'sg' + the state of the key file the park is in, e.g. sgmtd81 in US-MT);
      2. the park's saved official outline overlaps the area box of the key file (the box around the GOOD POTA pins of the other parks
         POTA puts in the same state / province, 1 degree wider: the same box the Canada builder uses for a park with no pin);
      3. world key: the record comes from a one-country official layer listed in that country's key file (not EEA / WDPA).
    Town / county cannot be tested without a pin, so the area test is the state / province / country one."""
    names = [x for x in m if name_how(pota_name or '', x[1], r18=True) in ('same', 'spelling')]
    r18 = [rule18_differs(pota_name or '', x[1], True) for x in m]
    if not names and any(r18): return False, False, 'POTA name does not match any joined record name: ' + next(r for r in r18 if r)
    if not names: return False, False, 'POTA name does not match any joined record name'
    st = area.split('-', 1)[1].lower() if area.startswith('US-') else ''
    for x in names:
        mm = re.match(r'^sg([a-z]{2})', str(x[0]))
        if st and mm and mm.group(1) == st: return True, True, f"name matches {x[1]!r}; the record is on {area}'s own layer ({x[0]})"
    if outline_bb and area_box and outline_bb[0] <= area_box[2] and outline_bb[2] >= area_box[0] and outline_bb[1] <= area_box[3] and outline_bb[3] >= area_box[1]:
        return True, True, f"name matches {names[0][1]!r}; the saved official outline lies in {area} (box of the other POTA pins there)"
    for x in names:
        src = str(x[2]) if len(x) > 2 and isinstance(x[2], str) else ''
        if src and src in sources and not NOT_ONE_AREA.search(src): return True, True, f"name matches {x[1]!r}; the record is on {area}'s own official layer ({src[:60]})"
    return True, False, f"name matches {names[0][1]!r} but nothing places the record in {area}"


NOTES = os.environ.get('PRECHECK_NOTES') or 'data/review/precheck-notes.json'


def notes():
    """(mapping_checked, ask_brandon) from data/review/precheck-notes.json (a person-readable file; never a key file)."""
    d = load(NOTES, {})
    return d.get('mapping_checked') or {}, d.get('ask_brandon') or {}


def trail_checks():
    """Nov 4 (Brandon, Super Head Bot chat, 4:35 AM CST (relayed via Super Head Bot): 'Agree keep the official line'; Brandon, Mapping chat, 4:36 AM CST: 'No keep the full length ones we had'): data/review/precheck-notes.json 'trail_check' =
    trail parks whose saved official line a person chose to KEEP while it is checked against the official trail data. Each is ONE
    review-pile row 'TRAIL CHECK' (never held, never a doubt: the line stays), whether or not the park is in a key file read."""
    return load(NOTES, {}).get('trail_check') or {}


def trail_act(t):
    return (f"TRAIL CHECK (not held; the line stays): keep {t.get('keep', 'the saved official line')}; {t.get('check', 'check it against the official trail data')}"
            f"{'; rejected: ' + t['rejected'] if t.get('rejected') else ''} ({t.get('by', 'a person')})")


def bad_pin_flag(n_ok, a_ok):
    """6:45 + 6:54 PM CST rulings (relayed): name + area -> NAME_MATCH (keep); name only -> NAME_ONLY (keep, pending Mapping's
    check); no name match -> UNBACKED (a doubt)."""
    return 'BAD_POTA_PIN_NAME_MATCH' if n_ok and a_ok else 'BAD_POTA_PIN_NAME_ONLY' if n_ok else 'BAD_POTA_PIN_UNBACKED'


def county_rows():
    f = os.environ.get('KFF_COUNTY_CSV') or ''
    if not f or not os.path.exists(f): return {}
    op = gzip.open if f.endswith('.gz') else open
    with op(f, 'rt', encoding='utf-8') as fh: return {r['park']: r for r in csv.DictReader(fh)}


def route_lost(lf, ov, layers):
    """lost finds -> PROPOSED (a fix a bot / the key can make, with the record) or NEEDS_RESEARCH (nothing usable to join)."""
    out = []
    for r in lf.get('A') or []:
        ref, st, nm, what, why = (r + [''] * 5)[:5]
        o = ov.get(ref) or {}
        ids = [str(x) for x in (o.get('join') or []) if re.match(r'^[a-z]*\d+$', str(x))]
        fam = sorted({re.match(r'\D*', i).group() for i in ids})
        other = [i for i in ids if re.match(r'^sg([a-z]{2})', i) and re.match(r'^sg([a-z]{2})', i).group(1) != st.lower()]
        unknown = [f for f in fam if f and f not in layers and not f.startswith('sg') and f not in ('hma', 'wsa', 'wid')]
        if other:
            fam0 = re.match(r'\D*', other[0]).group(); lab = str((layers.get(fam0) or ['', '', ''])[-1])[:70]
            rt, why2 = 'PROPOSED', (f"the joined id {other[0]} is on layer {fam0} ({lab}), which was first set up under {fam0[2:4].upper()} in data/state-gis.json "
                                    f"(a layer keeps its first prefix): check that the {st} build reads that layer (its state list) and that the record still exists; "
                                    f"re-run the {st} key with KPC_DEBUG_REFS={ref}")
        elif ids and not unknown: rt, why2 = 'PROPOSED', f"join ids {', '.join(ids[:3])} are on layers the key reads: the record id may have changed (fingerprint re-find) or a 'no' / prune drops it; re-run the key with KPC_DEBUG_REFS={ref}"
        elif ids: rt, why2 = 'PROPOSED', f"layer family {', '.join(unknown)} is not read by the key: add the layer (layers.json / state-gis.json) or join by record on a read layer"
        elif o.get('alias') or o.get('alias_all'): rt, why2 = 'NEEDS_RESEARCH', 'a name alias only (no record id): the alias name is not on any read layer; find the official record id'
        else: rt, why2 = 'NEEDS_RESEARCH', 'nothing to join by (no id, no alias)'
        out.append([ref, st, nm, 'A (a person decided, not in the key)', rt, why2, ', '.join(ids), str(why)[-160:]])
    for grp, label in (('B', 'B (SURE area find, never asked)'), ('C', 'C (SURE trail line, not drawn)')):
        for r in lf.get(grp) or []:
            ref, st, nm, rec, url = (r + [''] * 5)[:5]
            official = bool(re.search(r'\.(gov|us)(/|$)|\.gov\.|arcgis\.com/', str(url)))
            if grp == 'C': rt, why2 = 'PROPOSED', 'kpc_finds_lines.py should carry this line into data/trails (if it stays here a week, that bot or the trail run failed)'
            elif official: rt, why2 = 'PROPOSED', 'ask the park-finder lane (detective) / chat 11 one question: is this record the park? (official layer, SURE)'
            else: rt, why2 = 'NEEDS_RESEARCH', 'the SURE find is not on an agency layer: find the official record'
            out.append([ref, st, nm, label, rt, why2, rec, url])
    return out


def main():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    pins, ov, cty = pota_pins(), overrides(), county_rows()
    layers = load('data/us-key/layers.json', {})
    lf = load('data/us-key/lost-finds.json', {})
    lost_rows = route_lost(lf, ov, layers); lost = {r[0] for r in lost_rows}
    B = collections.defaultdict(list); score, pile, hold = [], {}, {}
    allk = list(keys()); box, srcs = {}, {}
    for area, kname, ref, p in allk:
        pn = pins.get(ref)
        if pn and not bad_pin(pn):
            b = box.setdefault(area, [999, 999, -999, -999]); la, lo = float(pn[1]), float(pn[2])
            box[area] = [min(b[0], lo - 1), min(b[1], la - 1), max(b[2], lo + 1), max(b[3], la + 1)]
    for f in sorted(glob.glob(str(DATA / 'data/world-key/??.json'))): srcs[pathlib.Path(f).stem] = tuple(load(f, {}).get('sources') or ())
    nab = collections.Counter(); nab_rows = []
    checked, asks = notes(); flag_rows = {}   # BAD_POTA_PIN_FLAGS.csv: one row per park
    trails_chk = trail_checks()
    seen, n, cnt = set(), 0, collections.Counter()
    for area, kname, ref, p in allk:
        if ONLY and area not in ONLY: continue
        seen.add(ref); n += 1
        o = ov.get(ref) or {}
        m = [x for x in (p.get('m') or []) if isinstance(x, list)]
        ok_person = person_approved(p, o)
        level = 'light' if ok_person else 'full'
        cnt[level] += 1
        pin = pins.get(ref)
        flags, why = [], []
        bp = bad_pin(pin)
        if bp:
            flags.append('POTA_0_0'); why.append(bp)
            if m:
                n_ok, a_ok, how = name_area_backs((pin or [p.get('n')])[0] or p.get('n'), m, area, box.get(area), outline_bbox(ref), srcs.get(area, ()))
                fl = bad_pin_flag(n_ok, a_ok)
                flags.append(fl); why.append({'BAD_POTA_PIN_NAME_MATCH': 'the pin is POTA\'s error, the outline stays: ',
                                              'BAD_POTA_PIN_NAME_ONLY': 'names very close, the outline stays pending Mapping\'s check: '}.get(fl, 'doubtful: ') + how)
                if not ok_person: nab[fl] += 1; nab_rows.append([ref, area, p.get('n'), (pin or [''])[0], bp, fl, how])
            else:
                fl, how = 'BAD_POTA_PIN_NO_OUTLINE', 'no joined official outline: nothing to keep or drop (flagged, never demoted)'
                flags.append(fl)
            if ref in flag_rows: flag_rows[ref][1] += ' ' + area
            else:
                mc = checked.get(ref) or {}
                flag_rows[ref] = [ref, area, fl, f'{bp}; {how}', ' | '.join(str(x[0]) for x in m[:6]), ' | '.join(str(x[1]) for x in m[:6]),
                                  (pin or [''])[0] or '', p.get('n') or '', '', (mc.get('result') or '') + (f" ({mc.get('by')})" if mc.get('by') else '')]
                if ref in asks:   # Super, 7:24 PM CST Nov 3: a person-list park says so in the flag list too
                    flag_rows[ref][-1] = (flag_rows[ref][-1] + ' | ' if flag_rows[ref][-1] else '') + 'ASK BRANDON: ' + str(asks[ref].get('ask') or '')[:200]
        if ref in asks: flags.append('ASK_BRANDON'); why.append('ask Brandon: ' + str(asks[ref].get('ask') or '')[:200])
        out_why = []
        if p.get('far') == 'well outside' or p.get('pin_may_be_wrong'): out_why.append('the POTA pin is well outside the joined land')
        # 'pin_in_state' is NOT a doubt: the key sets it for a park that spans states (Natchez Trace, Umbagog) instead of 'far'
        c = cty.get(ref) or {}
        try: km = float(c.get('km_to_listed') or 0)
        except ValueError: km = 0
        # the WWFF list often names only the HQ county of a park that spans counties (Morris WMD alone made 185 false hits in the
        # county check), so only a pin more than 15 km from every listed county of a one-county kind of park is a doubt
        if out_why and not bp: flags.append('PIN_WAY_OUT'); why += out_why
        if c.get('county_pin') in ('contradicts', 'near'):
            # a county disagreement alone never holds a park: the NV / MT small-state test (Nov 3) showed the WWFF list itself swapped
            # (Fort Churchill listed in Lincoln County, Kershaw-Ryan in Lyon, Lake Elmo in Lake County) while the POTA pin sat in the park
            far = bool(p.get('far') == 'well outside' or p.get('pin_may_be_wrong'))
            reading = ('pin and outline disagree with the list: check the pin' if far else
                       'the pin sits in the joined land: the WWFF county list is likely wrong' if m else
                       'park is a pin: the county is a lead for the park finder only')
            if c.get('county_pin') == 'contradicts' and km > 15 and not MULTI.search(f"{p.get('n')} {p.get('t')}"): pass
            elif c.get('county_pin') == 'contradicts': reading = 'a park that spans counties or a neighbouring county (within 15 km): weak sign only'
            else: reading = 'near a listed county: weak sign only'
            flags.append('COUNTY'); why.append(f"WWFF county list says {str(c.get('wwff_counties') or '')[:80]}; the pin is in {c.get('pin_in_county', '')} ({km:g} km): {reading}")
            B['county'].append([ref, area, p.get('n'), c.get('county_pin'), c.get('wwff_counties'), c.get('pin_in_county'), c.get('km_to_listed'), reading, level])
        # 0 acres is a self-check 'unsure', not a broken row (Quality, Nov 3): it is shown in 'why' but flags nothing on its own
        broken = [b for b in KR.self_checks(ref, p, None, None, None) if not b.startswith(('missing field c', 'acres: the joined land has 0'))]
        if broken: flags.append('BROKEN_ROW'); why += broken
        if level == 'full':
            if not m or p.get('g') in ('pin', 'approximate'):
                flags.append('NO_OFFICIAL_BOUNDARY')
                B['no-official-boundary'].append([ref, area, p.get('n'), p.get('t'), p.get('g') or 'pin', '; '.join(str(x[1]) + ' (' + str(x[3])[:50] + ')' for x in (p.get('c') or [])[:2] if isinstance(x, list) and len(x) > 3),
                                                  'park-finder lane (detective) / GIS hunter' if kname != 'world-key' else 'world finder'])
            nh = [(x, name_how_general(p.get('n') or '', x[1])) for x in m if not str(x[3]).startswith(('reviewed', 'official trail line'))]
            sp = [x for x, h in nh if h == 'spelling']; oth = [x for x, h in nh if h == 'other']
            if sp: flags.append('MISNAMED'); why.append('POTA spells the name differently from the agency record (same place): ' + '; '.join(f'{x[0]} {x[1]}' for x in sp[:3]))
            if oth: flags.append('NAME_MISMATCH'); why.append('joined record shares no real word with the park name: ' + '; '.join(f'{x[0]} {x[1]}' for x in oth[:3]))
            # Brandon, relayed by Super 7:26 PM CST Nov 3: rule 18 in the general name test too. A record whose name matches but that
            # rule 18 tells apart (North/South Fork, Unit 2/3, Upper/Lower, a bracketed POTA qualifier) is another piece: review pile
            # + flag RULE18_PIECE. Not a doubt, so it is never held (the hold switch stays off by default either way).
            r18p = [(x, why18) for x, h in nh if h != 'other' for why18 in [rule18_differs(p.get('n') or '', x[1], False)] if why18]   # v5 (Brandon, relayed 7:43 PM CST): bracketed place qualifiers ('(Lewis County)') no longer count here
            for _x, _w in r18p[:1]: cnt['rule18_by_' + ('qualifier' if 'qualifier' in _w else 'one-side word' if 'names only one piece' in _w else 'number' if 'number' in _w else 'piece word' if "' vs '" in _w else 'piece test')] += 1
            if r18p: flags.append('RULE18_PIECE'); why.append('rule 18: the joined record may be another piece: ' + '; '.join(f'{x[0]} {x[1]} ({w})' for x, w in r18p[:3]))
            wk = [x for x in m if kind_ok(p.get('t') or p.get('n'), x[1]) is False]
            r18 = str(c.get('wwff_name_vs_pota_rule18') or '')
            if wk or r18.startswith('[KIND]'):
                flags.append('WRONG_KIND'); why.append(('layer kind: ' + '; '.join(f'{x[1]}' for x in wk[:3]) + f" is another kind of place than a {p.get('t') or 'park'}") if wk else 'WWFF: ' + r18[:120])
            if ref in lost: flags.append('LOST_FIND')
        if ref in trails_chk: flags.append('TRAIL_CHECK'); why.append('trail check: a person kept the saved official line; check it against the agency trail data')   # Nov 4: never a doubt
        if not flags: continue
        for f in flags: cnt[f] += 1
        row = [ref, area, p.get('n'), p.get('t'), p.get('g') or ('official' if m else 'pin'), level, ' '.join(flags), ' | '.join(why)[:400],
               ', '.join(str(x[0]) for x in m[:4]), pin[1] if pin else '', pin[2] if pin else '']
        score.append(row)
        if 'MISNAMED' in flags or 'NAME_MISMATCH' in flags: B['misnamed'].append(row)
        if 'PIN_WAY_OUT' in flags: B['pin-way-out'].append(row)
        if 'WRONG_KIND' in flags: B['wrong-kind'].append(row)
        if 'POTA_0_0' in flags: B['pota-0-0'].append([ref, area, p.get('n'), pin[1] if pin else '', pin[2] if pin else '', bp, 'tell POTA (we never move POTA pins)'])
        # a spelling difference alone is not a doubt; a bad POTA pin is a doubt only when the name + area test does not back the match
        doubt = [f for f in flags if f in ('PIN_WAY_OUT', 'NAME_MISMATCH', 'WRONG_KIND', 'BAD_POTA_PIN_UNBACKED')]
        if m and doubt:
            pp = {str(x[0]) for x in person_pieces(p, o)}
            if ok_person:
                act = 'KEEP (a person approved it; rule 22) - tell Brandon what the light check found'
            elif pp:
                act = 'HOLD PIECES: only the pieces no person reviewed leave the key; the person-reviewed pieces and the outline stay (rule 22) - tell Brandon'
            else:
                act = 'HOLD: drop from the key until a person looks (Brandon Nov 3 5:30 PM)'
            if ref in asks: act = ('ASK BRANDON: DROPPED TO PIN by overrides (Brandon 7:33 PM CST Nov 3, relayed: when in doubt drop it, put it on a list); the next key build makes it a pin' if asks[ref].get('dropped_to_pin') else 'ASK BRANDON first: not held while his answer is pending (the outline stays, flagged)')
            if not ok_person and ref not in asks:
                h = hold.setdefault(ref, {'why': ' | '.join(why)[:300], 'flags': doubt, 'ids': [], 'keep_ids': sorted(pp), 'areas': []})
                h['ids'] = sorted(set(h['ids']) | {str(x[0]) for x in m if str(x[0]) not in pp}); h['areas'].append(area)
            if ref in pile: pile[ref][1] += ' ' + area   # one row per park (US-6090 is in US-AZ and US-UT)
            else: pile[ref] = row + [act]
        if ref in asks:   # a question for Brandon with a proposal that is NOT applied: in the pile, never held
            a = asks[ref]; act2 = f"ASK BRANDON ({'DROPPED TO PIN by overrides; ' if a.get('dropped_to_pin') else ''}not held; proposal NOT applied until he answers): {a.get('ask', '')} PROPOSED: {a.get('proposal_text', '')}"
            if ref in pile:
                if 'proposal NOT applied' not in pile[ref][-1]: pile[ref][-1] += ' | ' + act2
            else: pile[ref] = row + [act2]
        if 'RULE18_PIECE' in flags:   # rule 18 (Brandon 7:26 PM CST, relayed): flag + review pile, never held
            act18 = 'RULE 18: check the piece (flag only, not held; Brandon 7:26 PM CST Nov 3, relayed)'
            if ref in pile:
                if 'RULE 18' not in pile[ref][-1]: pile[ref][-1] += ' | ' + act18
            else: pile[ref] = row + [act18]; cnt['rule18_pile_added'] += 1
        if ref in trails_chk:   # Nov 4 (Brandon: Super Head Bot chat 4:35 AM CST + Mapping chat 4:36 AM CST): a kept official trail line to check against the agency's trail data
            actt = trail_act(trails_chk[ref])
            if ref in pile:
                if 'TRAIL CHECK' not in pile[ref][-1]: pile[ref][-1] += ' | ' + actt
            else: pile[ref] = row + [actt]
    # parks with a POTA pin but in no key at all (other programs are in the world key only if DATA was given)
    if not ONLY:
        for ref, pn in pins.items():
            if ref in seen: continue
            bp = bad_pin(pn)
            if bp:
                B['pota-0-0'].append([ref, ref.split('-')[0], pn[0], pn[1], pn[2], bp + ' (park not in any key file read)', 'tell POTA (we never move POTA pins)']); cnt['POTA_0_0_not_in_key'] += 1
                flag_rows[ref] = [ref, ref.split('-')[0], 'BAD_POTA_PIN_NO_OUTLINE', bp + '; the park is in no key file read', '', '', pn[0] or '', '', '', '']
    H = ['park', 'area', 'name', 'type', 'outline', 'check', 'flags', 'why', 'joined ids', 'pota_lat', 'pota_lon']
    if not ONLY:   # a trail-check park in no key file read still gets its row (Nov 4)
        for ref, tc in trails_chk.items():
            if ref not in pile: pile[ref] = [ref, '', tc.get('name', ''), '', 'line (kept)', '', 'TRAIL_CHECK', 'park in no key file read', '', '', '', trail_act(tc)]; cnt['trail_check_not_in_key'] += 1
    tc_in_pile = sorted(r for r in trails_chk if r in pile)
    heads = {'misnamed': H, 'pin-way-out': H, 'wrong-kind': H,
             'no-official-boundary': ['park', 'area', 'name', 'type', 'outline now', 'best candidates the key saw', 'next bot'],
             'pota-0-0': ['park', 'area', 'name', 'pota_lat', 'pota_lon', 'problem', 'action'],
             'county': ['park', 'area', 'name', 'county check', 'WWFF listed counties', 'pin is in', 'km to listed', 'reading', 'check']}
    def w(name, head, rows):
        with open(OUT / name, 'w', newline='', encoding='utf-8') as f: cw = csv.writer(f); cw.writerow(head); cw.writerows(rows)
    for k, rows in B.items(): w(f'{k}.csv', heads[k], rows)
    w('scorecard.csv', H, score)
    pile = [pile[r] for r in sorted(pile, key=lambda r: (not r.startswith('US-'), not r.startswith('CA-'), r))]
    w('review-pile.csv', H + ['action'], pile)
    for r in flag_rows.values(): r[8] = 'HELD (review pile)' if r[0] in hold else 'kept (flag only)' if r[4] else 'no outline (flag only)'
    w('BAD_POTA_PIN_FLAGS.csv', ['park', 'area', 'flag', 'reason (POTA pin problem; name + area test)', 'record id(s)', 'official name(s)', 'POTA name',
                                 'name in key', 'outline now', "Mapping's check"],
      sorted(flag_rows.values(), key=lambda r: (not r[0].startswith('US-'), not r[0].startswith('CA-'), r[0])))
    w('bad-pota-pin-name-area.csv', ['park', 'area', 'name in key', 'POTA name', 'pin problem', 'flag', 'name + area test'], nab_rows)
    w('lost-finds-routed.csv', ['park', 'state', 'name', 'group', 'route', 'why / next step', 'record or ids', 'source or note'], lost_rows)
    json.dump({'made': time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime()), 'note': 'parks the pre-check would hold out of the key (KPC_PRECHECK_HOLD=1); never a person-approved join', 'parks': hold},
              open(OUT / 'review-hold.json', 'w'), indent=1, ensure_ascii=False)
    lr = collections.Counter(r[4] for r in lost_rows)
    us_ca = [r for r in hold if r.startswith(('US-', 'CA-'))]
    counts = {'status': 'green', 'parks': n, **dict(cnt), 'review_pile': len(pile), 'review_pile_keep': sum(1 for r in pile if r[-1].startswith('KEEP')),
              'hold': len(hold), 'hold_us_ca': len(us_ca), 'hold_us_ca_to_pin': sum(1 for r in us_ca if not hold[r]['keep_ids']),
              'hold_us_ca_pieces_only': sum(1 for r in us_ca if hold[r]['keep_ids']), 'hold_world_listed_only': len(hold) - len(us_ca),
              'bad_pin_name_area': dict(nab), 'bad_pin_flags': len(flag_rows), 'bad_pin_flags_by_flag': dict(collections.Counter(r[2] for r in flag_rows.values())),
              'bad_pin_flags_held': sum(1 for r in flag_rows if r in hold), 'ask_brandon': sorted(a for a in asks if a in seen), 'ask_brandon_not_in_key': [] if ONLY else sorted(a for a in asks if a not in seen), 'trail_check': tc_in_pile, 'lost_finds': len(lost_rows), 'lost_find_parks': len(lost), 'lost_routed': dict(lr), 'seconds': round(time.time() - t0, 1)}
    json.dump(counts, open(OUT / 'counts.json', 'w'), indent=1)
    print(f"::notice title=Pre-check::{n} parks: {cnt['light']} light (a person approved), {cnt['full']} full; review pile {len(pile)} "
          f"(hold {len(hold)}); 0,0 pins {len(B['pota-0-0'])}; lost finds {len(lost_rows)} ({dict(lr)}) -> {OUT}")


def apply_hold():
    """Move held parks out of the key files (US + Canada here; the world keys live in KPC-Data and are only listed)."""
    if os.environ.get('KPC_PRECHECK_HOLD', '').strip().lower() not in ('1', 'on', 'yes', 'true'):
        print('::notice title=Pre-check hold::KPC_PRECHECK_HOLD is off: nothing held (the review pile is still written)'); return
    hold, ov = (load(OUT / 'review-hold.json', {}).get('parks') or {}), overrides()
    try:
        import kpc_save; save = lambda f, d: kpc_save.save_json(f, d)  # noqa: E731
    except Exception:  # noqa: BLE001
        save = lambda f, d: open(f, 'w', encoding='utf-8').write(json.dumps(d, separators=(',', ':'), sort_keys=True, ensure_ascii=False))  # noqa: E731
    n = 0
    for f in sorted(glob.glob('data/us-key/US-??.json')) + sorted(glob.glob('data/ca-key/CA-??.json')):
        d = load(f, {}); P = d.get('parks') or {}; ch = 0
        for ref, h in hold.items():
            p = P.get(ref)
            if not p or not p.get('m'): continue
            if person_approved(p, ov.get(ref)): continue   # rule 22, belt and braces (a bot's auto YES is not a person)
            pp = {str(x[0]) for x in person_pieces(p, ov.get(ref))}
            go = [x for x in p['m'] if str(x[0]) not in pp]          # a person-reviewed piece is NEVER moved (Quality must-fix 1, Nov 3)
            if not go: continue
            p['c'] = [list(x[:3]) + ['held for review (pre-check): ' + str(h.get('why') or '')[:140]] for x in go] + list(p.get('c') or [])
            p['m'] = [x for x in p['m'] if str(x[0]) in pp]; p['held'] = h.get('flags') or []; ch += 1
            if not p['m']: p['g'] = 'pin'
            else: p['held_pieces'] = [str(x[0]) for x in go]   # the park keeps its person-reviewed outline; Brandon sees the flag
        if ch: save(f, d); n += ch
    print(f'::notice title=Pre-check hold::{n} parks held out of the US / Canada keys into the review pile ({OUT}/review-pile.csv)')


if __name__ == '__main__':
    try:
        main()
        if '--apply-hold' in sys.argv: apply_hold()
    except Exception as e:  # noqa: BLE001  (Quality, Nov 3: a crash must not look like a clean run)
        print(f'::error title=Pre-check::stopped, the review pile is NOT complete: {type(e).__name__}: {str(e)[:200]}')
        try:
            OUT.mkdir(parents=True, exist_ok=True)
            json.dump({'status': 'red', 'error': f'{type(e).__name__}: {str(e)[:300]}', 'made': time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}, open(OUT / 'counts.json', 'w'), indent=1)
        except Exception: pass  # noqa: BLE001
        sys.exit(1)
    sys.exit(0)
