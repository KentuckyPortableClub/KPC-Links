"""Rule 18, a number in ONE name only (next round v3 C10, Nov 5 2026).

Quality's grade of next round v2 (Part 3 NO): the v2 number test sat in kpc_key_rules.py, a US-key rule file, so it moved the US
rules hash (3dc53f70256a -> b2e696114b5c) although the US key never runs it (kpc_us_key.py calls piece_ok only when KPC_PIECE_NAME
is on, default off). It lives here now, in a module of its own that is NOT a US-key rule file (kpc_key_freeze.RULE_FILES['us-key']
is kpc_us_key.py, kpc_key_rules.py, kpc_match.py, kpc_key_facts.py), so the US hash stays 3dc53f70256a and the relayed sign-off of
US-42016221491 still holds. Callers: kpc_precheck._rule18_core (the review pile) and kpc_world_key.same_name (the world key; this file
is therefore a WORLD-key rule file, listed in kpc_key_freeze.RULE_FILES['world-key']).

What counts as a number in a name:
  - a plain number of 1-4 digits ('Mount Stanley 1', 'Fish Lake 02' = 2). 5+ digits are register ids ('2000542 Risveden'), and
    digits glued to letters are codes ('I106', 'H57', 'FR4201797'), not pieces;
  - 'No2', 'No.2', 'No 2', 'n° 28', 'Nº 3', '#2' = 2, and a lower-case 'n9' (POTA's 'n°9' without the °, FR-5508) = 9;
  - upper-case Roman numerals I..XX = their arabic form ('Bagno Wizna II' = 'Bagno Wizna 2'). A ONE-letter one (I, V, X) only ever
    MATCHES a number on the other side and never refuses on its own: it is too often an initial ('Francisco I. Madero',
    'L.I.V.I.A.'), a word (Slovene / Czech 'V' = 'in') or a king ('King George V'). Lower-case 'ii' / 'vi' are words, not numbers,
    and so is a word with an apostrophe in it (CA-4007 'Kt'ii/Racey' = 'KT'II/RACEY CONSERVANCY');
  - NOT a number: 'Natura 2000'; a decimal ('2588.27 Acre Parcel' is a measure); the WA CALM Act section of a reserve, written '5(1)(h) Reserve' in CAPAD and shortened by POTA to
    '5 Reserve' at the end of a name (AU-3037, AU-6700). Quality v3 should-fix: that strip runs ONLY when cc starts with AU.
A number counts as 'on both sides' when the other name carries it anywhere: as a plain number, inside brackets ('... 25' vs CAPAD-like
'... (25)', FR-5626; 'n° 28' vs '(n° 28)', FR-5526), as a one-letter Roman numeral, or written out in English ('9 Mile' / 'Nine Mile').
A number that only sits inside brackets never refuses on its own (rule 18 v5: bracket text does not count).
When one name's bracket text names the other park ('2000542 Risveden etapp 1 (Trehörningen)' for 'Trehörningen Nature Reserve',
SE-0054; '... etapp 2 (Kroksjön)', SE-0123), the park is that bracket name, and the numbers are compared with the bracket name only.

BRANDON'S RULING (relayed via Super, 10:08 AM CST Nov 5 2026; not his own sign-off on this bundle): "Yeah just put them in the
review pile". A number only in POTA's name (pattern A) and a whole park joined to one numbered piece (pattern B) follow rule 18:
the world key does not join them (the park stays a PIN) and the pre-check puts them on the review pile. So the default stays
'strict'; the switch stays for a later ruling, but its default does not change.
THE SWITCH:
  ONE_SIDE_NUMBER = 'strict'      a number in one name only refuses the join, either way (default; the letter of rule 18)
                  = 'counter-ok'  a number only in the POTA name passes when the record carries no number at all (Quality's
                                  pattern A: POTA's own counters, ~104 FR rows); a clash with another number still refuses
                  = 'piece-ok'    a number only in the record passes when the POTA name carries no number at all (pattern B:
                                  numbered pieces of a multi-piece park, AU-7265 'Mount Stanley' vs 'Mount Stanley 1')
                  = 'both-ok'     counter-ok and piece-ok together
                  = 'off'         no one-side number test at all (the behaviour before C10)
It is a constant on purpose, not an environment variable: this file is a world-key rule file, so changing the switch changes the
world rules hash and needs a world rebuild + grade, like any rule change. (kpc_precheck reads the same constant.)"""
import re
import unicodedata

ONE_SIDE_NUMBER = 'strict'
MODES = ('strict', 'counter-ok', 'piece-ok', 'both-ok', 'off')

_ROMAN = {r: i for i, r in enumerate('I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX'.split(), 1)}
WORDS = {str(i): w for i, w in enumerate('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen '
                                         'fifteen sixteen seventeen eighteen nineteen twenty'.split())}
_BRK = re.compile(r'\(([^)]*)\)|\[([^\]]*)\]')


def fold(t):
    """lower case, accents off ('Trehörningen' -> 'trehorningen')"""
    return unicodedata.normalize('NFKD', str(t or '')).encode('ascii', 'ignore').decode().lower()


def roman(w):
    """the value of an upper-case Roman numeral I..XX, else None ('II' -> 2, 'ii' -> None, 'MIX' -> None)"""
    return _ROMAN.get(w) if w and w == w.upper() else None


def _clean(t, cc=None):
    """Strip network / measure / AU-WA CALM '5 Reserve' noise before scanning numbers.
    Quality v3 should-fix: the '5 Reserve' / '5(1)(h)' strip applies only to AU (WA CALM Act), not every country."""
    t = str(t or '')
    t = re.sub(r'(?i)natura\s*2000', ' ', t)                                # a network, not a number
    t = re.sub(r'\d+[.,]\d+', ' ', t)                                       # a measure, not a piece ('2588.27 Acre Parcel', US-12306)
    au = (cc or '').upper().startswith('AU')
    if au:
        t = re.sub(r'\b\d+\s*\(\s*\d+\s*\)\s*\(\s*[a-zA-Z]\s*\)', ' ', t)  # WA CALM Act section '5(1)(h)'
        t = re.sub(r'(?i)\b5\s+reserve\s*$', ' Reserve', t)                 # POTA short form '... 5 Reserve' (AU-3037, AU-6700)
    t = re.sub(r'(?i)(?:\bno|\bn[º°]|#)\s*\.?\s*(?=\d)', ' ', t)          # 'No2', 'No.2', 'n° 28', '#2' -> ' 2'
    t = re.sub(r'\bn(?=\d{1,3}\b)', ' ', t)                                  # POTA's 'n9' = 'n°9' with the ° lost (FR-5508); lower-case only
    return t


def _scan(t):
    """(strong, weak): strong = plain numbers and multi-letter Roman numerals; weak = one-letter Roman numerals"""
    strong, weak = set(), set()
    for w in re.findall(r"[^\W_]+(?:['’][^\W_]+)*", t):   # a word with an apostrophe is one word: Dene "KT'II" is not Roman II (CA-4007)
        if w.isdigit():
            if len(w) <= 4: strong.add(str(int(w)))
        elif w.isalpha():
            v = roman(w)
            if v: (strong if len(w) > 1 else weak).add(str(v))
    return strong, weak


def numbers(t, cc=None):
    """{'bare': numbers outside brackets, 'weak': one-letter Roman numerals outside brackets, 'brk': every number inside brackets,
    'words': the folded words (for numbers written out)}"""
    c = _clean(t, cc=cc)
    inner = ' '.join(a or b for a, b in _BRK.findall(c))
    bare, weak = _scan(_BRK.sub(' ', c))
    bs, bw = _scan(inner)
    return {'bare': bare, 'weak': weak, 'brk': bs | bw, 'words': set(re.findall(r'[a-z]+', fold(c)))}


def _has(n, side):
    return n in side['bare'] or n in side['weak'] or n in side['brk'] or WORDS.get(n) in side['words']


# kind words, which name no place ('Trehörningen Nature Reserve' is the place 'Trehörningen')
_KIND = set('reserve reserves nature natural park parks national state forest forests area areas conservation protected monument '
            'regional recreation wildlife management sanctuary site historic the and of de la le les du des naturreservat '
            'nationalpark naturpark reservat naturschutzgebiet'.split())


def _place(t): return {w for w in re.findall(r'[a-z]+', fold(_BRK.sub(' ', str(t or '')))) if len(w) >= 3} - _KIND


def _alt(a, b):
    """the bracket text of b that IS park a's name (the same place words, kind words aside), else None. A bracket of kind words
    only ('(Reserve)') or a qualifier ('(Lower Tract)') is never the park's name."""
    wa = _place(a)
    for x, y in _BRK.findall(str(b or '')):
        w = _place(x or y)
        if w and w == wa: return x or y
    return None


def one_side(a, b, mode=None, cc=None):
    """the numbers (sorted, as text) that only ONE of the two names carries and that refuse the join; [] = no refusal.
    a = the POTA name, b = the official record's name. mode: see ONE_SIDE_NUMBER (default: the constant)."""
    mode = mode or ONE_SIDE_NUMBER
    if mode not in MODES: raise ValueError(f'kpc_number_rules: unknown mode {mode!r} (one of {", ".join(MODES)})')
    if mode == 'off': return []
    alt = _alt(a, b)
    if alt is not None: b = alt                     # SE-0054: the record's bracket name is the park
    else:
        alt = _alt(b, a)
        if alt is not None: a = alt
    A, B = numbers(a, cc=cc), numbers(b, cc=cc)
    a_only = {n for n in A['bare'] if not _has(n, B)}
    b_only = {n for n in B['bare'] if not _has(n, A)}
    if mode in ('counter-ok', 'both-ok') and not (B['bare'] or B['weak'] or B['brk']): a_only = set()
    if mode in ('piece-ok', 'both-ok') and not (A['bare'] or A['weak'] or A['brk']): b_only = set()
    return sorted(a_only | b_only, key=int)


def why(a, b, mode=None, cc=None):
    """'' = no refusal; else the plain reason (the wording ends in '(rule 18)')."""
    one = one_side(a, b, mode, cc=cc)
    return f"number {' '.join(one)} is in one name only ('{a}' vs '{b}'): a different piece (rule 18)" if one else ''
