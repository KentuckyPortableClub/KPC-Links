"""Next round v3 C10 (Quality's grade of next round v2, Part 3 NO, Nov 5 2026): a number in ONE name only is a different piece
(rule 18 -> PIN), now in its own module .github/scripts/kpc_number_rules.py, used by kpc_precheck._rule18_core and
kpc_world_key.same_name. kpc_key_rules.piece_ok is untouched and the new module is not a US-key rule file, so the US rules hash
does not move (the relayed sign-off of US-42016221491 holds). Also the v2 false refusals Quality found: the same number bracketed on
one side only (FR-5626, FR-5526), 'No2' written glued (NZ-0408), the number only in the official name while the park is the record's
bracket name (SE-0054, SE-0123), the WA '5 Reserve' short form of CAPAD's '5(1)(h) Reserve' (AU-3037, AU-6700; checked against
CAPAD on Nov 5), and Roman numerals. Brandon's ruling (relayed via Super, 10:08 AM CST Nov 5): "Yeah just put them in the review
pile": a number only in POTA's name, and a whole park joined to one numbered piece, are PINs on the review pile (default 'strict').
Fails on the old code (no kpc_number_rules; AU-7265 not refused)."""
import pathlib, sys, types
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_precheck as PC  # noqa: E402
import kpc_key_freeze as KF  # noqa: E402


def _kn():
    import kpc_number_rules as KN
    return KN


def _world():
    src = (ROOT / '.github' / 'scripts' / 'kpc_world_key.py').read_text(encoding='utf-8')
    m = types.ModuleType('kpc_world_key'); m.__dict__['__file__'] = str(ROOT / '.github' / 'scripts' / 'kpc_world_key.py')
    exec(compile(src.split('\nfor cc in COUNTRIES:')[0], 'kpc_world_key.py', 'exec'), m.__dict__)
    return m


# (park, record, country)
REFUSE = [('Mount Stanley State Forest', 'Mount Stanley State Forest 1', 'AU'),   # AU-7265 vs DESI (C7)
          ('Mount Stanley State Forest', 'Mount Stanley 1', 'AU'),                # AU-7265 vs CAPAD (main)
          ('Fish Lake 2', 'Fish Lake', 'FI'), ('Danbulla South', 'Danbulla South 2', 'AU'),
          ('Ecrevisse a Pattes Blanches Et Faune Patrimoniale Associee - 39 Biological Reserve',
           'Ecrevisse À Pattes Blanches Et Faune Patrimoniale Associée (25)', 'FR'),             # FR-5157: 39 vs 25, a real catch
          ('Bagno Wizna II Nature Reserve', 'Bagno Wizna', 'PL'),                               # a Roman numeral on one side
          ('Trehörningen 2 Nature Reserve', '2000542 Risveden etapp 1 (Trehörningen)', 'SE')]  # the bracket name, another number
KEEP = [('Ecrevisse A Pattes Blanches Et Faune Patrimoniale Associee 25 Conservation Area',
         'Ecrevisse À Pattes Blanches Et Faune Patrimoniale Associée (25)', 'FR'),               # FR-5626: the same number, bracketed
        ('Terril Fontenelle a Fouquereuil n° 28 Biological Reserve', 'Terril Fontenelle à Fouquereuil (n° 28)', 'FR'),   # FR-5526
        ('Terril de la cite n9 d’Annequin Biological Reserve', 'Terril de la cité n°9 d’Annequin', 'FR'),   # FR-5508: 'n9' = 'n°9'
        ('Rangataua No2 Conservation Area', 'Rangataua No.2 Conservation Area', 'NZ'),           # NZ-0408: 'No2' glued
        ('Trehörningen Nature Reserve', '2000542 Risveden etapp 1 (Trehörningen)', 'SE'),        # SE-0054: the park is the bracket name
        ('Kroksjön Nature Reserve', '2000558 Risveden etapp 2 (Kroksjön)', 'SE'),                # SE-0123
        ('Wellington Discovery Forest 5 Reserve', 'Wellington Discovery Forest', 'AU'),          # AU-3037: CAPAD TYPE '5(1)(h) Reserve' (Quality v3: strip AU-only; pass cc)
        ('Buntine 5 Reserve', 'Buntine', 'AU'),                                                  # AU-6700: CAPAD TYPE '5(1)(h) Reserve'
        ('Bagno Wizna II Nature Reserve', 'Bagno Wizna 2', 'PL'), ('Tenayuca III', 'Tenayuca 3', 'MX'),   # Roman = arabic
        ('Bagno Wizna I Nature Reserve', 'Bagno Wizna 1', 'PL'),
        ('King George V Fields Recreation Park', 'King George Fields Recreation Park', 'GB'),     # a king, not a piece
        ('Ciudad Deportiva Francisco I. Madero State Park', 'Ciudad Deportiva Francisco Madero', 'MX'),   # an initial
        ('Ribniki V Dolini Drage Pri Igu', 'Ribniki Dolini Drage Pri Igu', 'SI'),               # Slovene 'v' = 'in'
        ("Kt'ii/Racey Conservation Area", "KT'II/RACEY CONSERVANCY", 'CA'),                       # CA-4007: a Dene word, not II
        ('Oak Creek 2014 Wildlife Area', 'Oak Creek 2014 - 2588.27 Acre Parcel', 'US'),             # a decimal is a measure
        ('9 Mile Canyon', 'Nine Mile Canyon', 'US'), ('Kilcolman Bog Natura 2000', 'Kilcolman Bog', 'IE'),
        ('Abisko National Park', '2001225 Abisko', 'SE'), ('Nullan I106', 'Nullan', 'AU'),
        ('Stockyard Gully 5(1)(g) Reserve', 'Stockyard Gully Reserve', 'AU'),
        ('Gerang Gerung North', 'Gerang Gerung North (0130)', 'AU'),                              # bracket text alone never refuses
        ('Mount Stanley State Forest', 'Mount Stanley State Forest', 'AU')]


def test_the_module_refuses_and_keeps():
    KN = _kn()
    assert KN.ONE_SIDE_NUMBER == 'strict', 'the default is the letter of rule 18'
    for a, b, _ in REFUSE: assert KN.one_side(a, b), (a, b)
    for a, b, cc in KEEP: assert KN.one_side(a, b, cc=cc) == [], (a, b, cc, KN.one_side(a, b, cc=cc))
    assert KN.one_side('Mount Stanley State Forest', 'Mount Stanley 1') == ['1']
    assert KN.one_side('Foo Reserve', 'Foo 2 (Reserve)') == ['2'], 'a bracket of kind words is not the park name'
    assert KN.why('Fish Lake', 'Fish Lake 2').endswith('(rule 18)') and 'in one name only' in KN.why('Fish Lake', 'Fish Lake 2')


def test_precheck_flags_au7265_and_not_the_false_refusals():
    for a, b, _ in REFUSE[:2]:
        w = PC.rule18_differs(a, b)
        assert w and 'number 1' in w and w.endswith('(rule 18)'), (a, b, w)
    for a, b, cc in KEEP: assert PC.rule18_differs(a, b, cc=cc) == '', (a, b, cc, PC.rule18_differs(a, b, cc=cc))
    assert PC.rule18_differs('Ławski Las 2 Nature Reserve', 'Ławski Las II') == '', "'2' vs 'II' is one piece (the both-sides test)"
    assert 'different pieces' in PC.rule18_differs('Ławski Las 2 Nature Reserve', 'Ławski Las III')


def test_world_same_name():
    WK = _world()
    for a, b, cc in REFUSE: assert not WK.same_name(cc, a, b), (cc, a, b)
    names = ('Rangataua No2 Conservation Area', 'Wellington Discovery Forest 5 Reserve', 'Buntine 5 Reserve')   # (same_name compares the text: 'II' vs '2' was never a world join)
    for a, b, cc in [k for k in KEEP if k[0] in names] + [('Mount Stanley State Forest', 'Mount Stanley State Forest', 'AU')]:
        assert WK.same_name(cc, a, b), (cc, a, b)
    assert WK.same_name('JP', 'Nikko 1', 'Nikko'), 'Japan: no number test (norm joins the words there)'


def test_the_switch():
    KN = _kn()
    A = ('Glenbar 1 State Forest', 'Glenbar')                   # pattern A: a POTA counter
    B = ('Mount Stanley State Forest', 'Mount Stanley 1')       # pattern B: a numbered piece
    C = REFUSE[4][:2]                                            # FR-5157: 39 vs (25), a clash
    want = {'strict': (1, 1, 1), 'counter-ok': (0, 1, 1), 'piece-ok': (1, 0, 1), 'both-ok': (0, 0, 1), 'off': (0, 0, 0)}
    assert set(want) == set(KN.MODES)
    for m, w in want.items():
        assert tuple(int(bool(KN.one_side(*x, mode=m))) for x in (A, B, C)) == w, m
    try: KN.one_side('a', 'b', mode='loose'); raise AssertionError('an unknown mode must stop')
    except ValueError: pass


def test_us_fingerprint_unchanged_and_world_lists_the_module():
    us = KF.RULE_FILES['us-key']
    assert '.github/scripts/kpc_number_rules.py' not in us, 'not a US-key rule file: the US rules hash does not move'
    assert sorted(us) == sorted(['.github/scripts/kpc_us_key.py', '.github/scripts/kpc_key_rules.py', '.github/scripts/kpc_match.py',
                                 '.github/scripts/kpc_key_facts.py'])
    assert '.github/scripts/kpc_number_rules.py' in KF.RULE_FILES['world-key'], 'kpc_world_key imports it: a world rule file'
    import kpc_key_rules as KR
    assert not hasattr(KR, 'one_side_number') and not hasattr(KR, 'bare_numbers'), 'kpc_key_rules.py (piece_ok) is untouched'


# Brandon's ruling (relayed via Super, 10:08 AM CST Nov 5 2026): "Yeah just put them in the review pile"
PILE_A = [('Glenbar 1 State Forest', 'Glenbar State Forest', 'AU'), ('Fish Lake 2', 'Fish Lake', 'FI'),
          ('Deep Lead No.2 Reserve', 'Deep Lead Reserve', 'AU')]                 # a number only in POTA's name
PILE_B = [('Mount Stanley State Forest', 'Mount Stanley 1', 'AU'),             # AU-7265: the whole park joined to one numbered piece
          ('Danbulla South', 'Danbulla South 2', 'AU')]


def test_brandon_pile_case_a_number_only_in_the_pota_name():
    KN = _kn(); WK = _world()
    assert KN.ONE_SIDE_NUMBER == 'strict'
    for a, b, cc in PILE_A:
        assert not WK.same_name(cc, a, b), ('the world key does not join it: the park stays a PIN', a, b)
        w = PC.rule18_differs(a, b)
        assert w and w.endswith('(rule 18)'), ('the pre-check puts it on the review pile', a, b, w)


def test_brandon_pile_case_b_whole_park_joined_to_one_numbered_piece():
    WK = _world()
    for a, b, cc in PILE_B:
        assert not WK.same_name(cc, a, b), ('the world key does not join it: the park stays a PIN', a, b)
        w = PC.rule18_differs(a, b)
        assert w and 'in one name only' in w and w.endswith('(rule 18)'), ('the pre-check puts it on the review pile', a, b, w)


def test_the_ruling_is_recorded_and_the_default_is_strict():
    src = (ROOT / '.github' / 'scripts' / 'kpc_number_rules.py').read_text(encoding='utf-8')
    assert 'Yeah just put them in the' in src and '10:08 AM CST Nov 5' in src and "\nONE_SIDE_NUMBER = 'strict'\n" in src
