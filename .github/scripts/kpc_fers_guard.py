"""Small, pure guards for the 2-fer finder (Mapping, Nov 4, read-only review of the 2-fer code on main).

  pin_problem(la, lo)     -> '' or why a POTA pin cannot be used (0,0 / impossible / not a number). The pin is NEVER moved
                             (no swap guess): a park with a bad POTA pin is listed, not tested, until POTA fixes the pin.
  same_land_doubt(a, b, record)
                          -> '' when one official record really names BOTH parks (same name, same kind), else a plain
                             'not sure: ...' reason. A same-land row is only a candidate when the record is clearly both parks
                             (Fundy Biosphere Reserve on the Fundy National Park record, Logoly State Natural Area on the Logoly
                             State Park record = a person decides).
  override_no(path)       -> {ref: (set of ids, set of lower-case names)} from an answer key's overrides.json 'no' lists.
  drop_no(m, no)          -> m without the pieces a person (or a ruling) said are NOT this park, for runs made before the key
                             was rebuilt.
No network, no writes."""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def pin_problem(la, lo):
    try: la, lo = float(la), float(lo)
    except (TypeError, ValueError): return 'POTA pin is not a number'
    if la != la or lo != lo: return 'POTA pin is not a number'
    if la == 0 and lo == 0: return '0,0 POTA pin'
    if not (-90 <= la <= 90 and -180 <= lo <= 180): return f'impossible POTA pin {la},{lo}'
    return ''


_KIND = [('biosphere', r'biosphere'), ('natural area', r'natural area|nature preserve|state nature'), ('wma', r'wildlife management|\bwma\b|game land|wildlife area'),
         ('refuge', r'wildlife refuge|\bnwr\b|national wildlife area'), ('state park', r'state park|provincial park|\bparc provincial'),
         ('national park', r'national park|parc national'), ('forest', r'national forest|state forest|provincial forest'),
         ('wilderness', r'wilderness(?! study)'), ('recreation', r'recreation area|\bsra\b'), ('historic', r'historic site|historical park|battlefield|monument|memorial'),
         ('trail', r'\btrail\b'), ('river', r'scenic river|wild and scenic'), ('beach', r'\bbeach\b'), ('lake', r'\blake\b|\blakes\b|reservoir|pond')]


def kinds(t):
    t = str(t or '').lower(); return {k for k, r in _KIND if re.search(r, t)}


_GEN = set('the of and at de la le les du des state provincial national park parc area areas wildlife management natural nature preserve reserve '
           'refuge forest recreation historic site lake lakes reservoir pond river trail biosphere wma nwr sra conservation wetland wetlands '
           'county regional municipal public fishing access game land lands unit tract'.split())


def core(t):
    return {w.rstrip('s') for w in re.findall(r'[a-z0-9]+', str(t or '').lower().replace("'", '')) if w not in _GEN and not w.isdigit() and len(w) > 1}


def unbracket(t):
    """Rule 18 v5 (Brandon, Super Head Bot chat, 7:43 PM CST Nov 3, relayed via Super Head Bot: "Yes"; relayed (paraphrase of the
    question he answered Yes to): bracket qualifiers do not count; one-side compass words in English or French do): a bracketed qualifier ('(Lower Tract)', '(Lewis County)') does not
    count in the name test, so it is taken off both names first (Quality should-fix 2, Nov 4)."""
    return re.sub(r'\s+', ' ', re.sub(r'\([^)]*\)|\[[^\]]*\]', ' ', str(t or ''))).strip()


def _names_it(park, rec):
    park, rec = unbracket(park), unbracket(rec)
    try:
        import kpc_precheck as PC   # the precheck's own name test (rule 18 aware) when it is next to this file
        h = PC.name_how(park, rec, True)
        if h in ('same', 'spelling'): return True
        if h == 'other': return False
    except Exception: pass  # noqa: BLE001
    a, b = core(park), core(rec)
    return bool(a) and a <= b | {w + 's' for w in b} if a else False


def same_land_doubt(park_a, park_b, record):
    """'' = the record names both parks and no kind differs; else a 'not sure' reason (a person decides)."""
    out = []
    for p in (park_a, park_b):
        if not _names_it(p, record): out.append(f"the record '{record}' does not name '{p}'")
    ka, kb, kr = kinds(park_a), kinds(park_b), kinds(record)
    for p, k in ((park_a, ka), (park_b, kb)):
        if k and kr and not (k & kr): out.append(f"'{p}' is a {'/'.join(sorted(k))}, the record a {'/'.join(sorted(kr))}")
    return ('not sure: one record covers two parks (' + '; '.join(out) + '): a person decides') if out else ''


def override_no(path):
    try:
        import kpc_overrides as _KOVR
        d = _KOVR.load(path)
    except Exception:
        try: d = json.load(open(path, encoding='utf-8'))
        except Exception: return {}  # noqa: BLE001
    out = {}
    for ref, o in ((d.get('parks') if isinstance(d, dict) else None) or {}).items():
        no = [x for x in (o or {}).get('no') or [] if x is not None]
        if no: out[ref] = ({str(x) for x in no}, {str(x).strip().lower() for x in no})
    return out


def drop_no(m, no):
    """m = key 'm' rows [id, name, ...]; no = (ids, names) from override_no."""
    if not no: return m
    ids, names = no
    return [x for x in m if not (str(x[0]) in ids or (len(x) > 1 and str(x[1]).strip().lower() in names))]
