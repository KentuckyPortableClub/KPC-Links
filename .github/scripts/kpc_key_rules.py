#!/usr/bin/env python3
"""KEY RULES (Nov 2 2026 review; a local patch, not live until Brandon OKs it). Small, importable helpers shared by the key
builders and BOT A, so every join path asks the SAME questions. Pure Python, no web, no file writes: tested on its own
(kpc_engine/patches/tests/test_key_rules.py).

Every rule has its own switch (an environment variable, set as a repo variable in the workflow). Bug fixes default ON, new
behaviour defaults to what the bots do today (OFF), so applying the patch changes nothing until a switch is turned on.

  KPC_NO_ALL_PATHS     1  a person's NO is checked in EVERY join path (alias_all, Recreation.gov, alias, NAME_JOIN, kept outline);
                          before, alias_all had no check and the others checked the id only. (bug fix)
  KPC_NO_BY_NAME       0  a NO also matches by the NAME + acres saved with it ('nofp', written by BOT A), so a NO survives a
                          PAD-US renumbering. Today a NO matches the id (or an exact name typed into 'no').
  KPC_ID_JOIN_NAME     0  a hand join by id also needs the record's name to look like the park (or the saved fingerprint name);
                          an id that now points at other land goes to 'check' with a reason. Today: the id alone joins.
  KPC_REFOUND_NEAR     0  a kept outline found again under a new PAD-US id must lie within ~0.6 deg of the pin. Today: anywhere.
  KPC_SELF_CHECKS      0  pre-handoff checks on each joined park (acres sanity, layer kind, missing fields, pin inside the state);
                          'report' = note them in the park ('self'), 'hold' = also move the park to check. 0 = off (today).
  KPC_CONF_SORT        0  each park gets a confidence (sure / likely / unsure) and a one-line reason; only 'unsure' parks are
                          listed for chat 11 (data/us-key/review/unsure-US-XX.json). Today every check item goes to chat 11.
  KPC_PADUS_DEDUPE     0  (Nov 2, mapping agent) PAD-US keeps an OLDER copy of the same place from the same data provider
                          (every refuge is there as FWS PAD-US 3.0 AND FWS PAD-US 4.0): the older copy is left out before
                          matching, only when at least 90% of its land lies inside the newer copy (batch 1b). Needs the
                          record's Agg_Src, so only works on a saved copy made after this patch (GEO_CACHE_MODE=refresh once).
                          An id a person joined by hand (after the fingerprint re-find) is never left out. Today: both kept.
  KPC_PIECE_NAME       0  (Nov 2, mapping agent, rule 18) a POTA park that names a piece ('Salinas Pueblo Missions, Abo Unit',
                          'Chattahoochee Fall Line Hilliard Tract', 'Las Palomas, Anacua Unit') only joins a record that
                          carries the piece's own word; the whole area or a sibling unit goes to check. Checked in the name
                          path AND the Recreation.gov path. Compass words count as the same piece ('S.E.' = 'South East'),
                          and Alabama's program name 'Forever Wild Tract' names no piece. OFF until Brandon / chat 11 say ON:
                          turning it ON changes outlines (batch 1b count on the Nov 2 key: see the mapping NOTES).
  KPC_NO_OFFICE_JOIN   0  (Nov 2, mapping agent) a record whose own name (Unit_Nm) is an office ('Eastern Interior Field
                          Office') is not joined by that name. When its second name (Loc_Nm) is a real place (Steese National
                          Conservation Area), the place name is tested instead; a record with no real place name is never
                          joined by name. OFF until Brandon / chat 11 say ON.
  KPC_SAVED_ID_LAND    0  (KPC owner, 2026-11-17, ruling D1: a saved id = the LAND, not the number) a park whose saved record ids
                          are kept through a rules change (the 9 Nov rule) keeps an id only while the record still carries
                          the name it was saved with and acres within 10% (20 acres at least). If an agency renumbered its
                          layer, the same name + acres is looked for in the SAME layer near the pin and the new id is kept;
                          if that fails, the old row is not carried, this run's own match stands, and the record goes to
                          check. OFF until the owner says ON (it changes outlines; count first, one state).
  KPC_ONE_RECORD_ONE_PARK 0  (KPC owner, 2026-11-17, ruling D9: one record, one park) a record joined by name to two or more parks
                          of the same kind stays with the ONE park whose full name is the record's own name; the others give it
                          back and it goes to check (a person may say it is the same land under two numbers). No single
                          winner = left as it is (the tripwire list shows it). A park given its own parts of the record (rule
                          B12 'parts') and hand joins are never moved. OFF until the owner says ON (count first, one state).
  KPC_NO_LEASE_BY_NAME 0  (KPC owner, 2026-11-17, ruling D5) a record whose name says leased / lease / agreement / cooperative area is
                          the easement family: never joined by name alone, it goes to check; a person may say yes for one park.
  KPC_LAKE_ONLY_IF_LAKE 0 (KPC owner, 2026-11-17, ruling D4, rewritten 9:17 AM after the research: WHO OWNS THE WATER decides, not
                          the park's kind). A lake surface joined by name stays only when (a) the park's own TYPE says it is the
                          water (a state fishing lake, a reservoir), or (b) the park has land of its own and the lake sits inside
                          that land (a small lake the park surrounds, or the agency's own outline already holds it). Otherwise it goes to CHECK (a person decides who owns the water; a park on someone else's lake,
                          the Corps', Reclamation's or a utility's, never takes it). A lake over 3 times the park's land never joins
                          by name. OFF until the owner says ON (park-scoped run).
  KPC_DESIGNATION_SPLIT 0 (KPC owner, 2026-11-17 10:00 AM, ruling D3) a national heritage area gets no outline (pin + 'sits on', its
                          records in the park's 'on' list); a federal designation line (FS designated area, BLM monument / NCA,
                          wilderness, study area, a PAD-US Designation record) is drawn only for the park that IS that designation;
                          joined by name to another kind of park it goes to check. Ownership share is a report first. OFF.
  (no switch)             RULE 18 TRACT EXCEPTION (Brandon, Nov 2 8:38 PM CST): when an official source (NPS, PAD-US) shows one
                          park as separate TRACTS and POTA lists each tract as its own park, each POTA park gets its own tract
                          of that record, never the whole. Only for parks a person reviewed (TRACT_SPLITS below, or a 'tract'
                          entry a person puts in overrides.json), only when the record really has separate tracts, and only
                          when the park's pin is inside its tract (or within 30 m of it). Everything else stays rule 18 (a pin).
"""
import os, re, unicodedata

DEFAULTS = {'KPC_NO_ALL_PATHS': '1', 'KPC_NO_BY_NAME': '0', 'KPC_ID_JOIN_NAME': '0', 'KPC_REFOUND_NEAR': '0',
            'KPC_SELF_CHECKS': '0', 'KPC_CONF_SORT': '0', 'KPC_PADUS_DEDUPE': '0', 'KPC_PIECE_NAME': '0',
            'KPC_NO_OFFICE_JOIN': '0', 'KPC_SAVED_ID_LAND': '0', 'KPC_ONE_RECORD_ONE_PARK': '0', 'KPC_NO_LEASE_BY_NAME': '0', 'KPC_LAKE_ONLY_IF_LAKE': '0', 'KPC_DESIGNATION_SPLIT': '0'}


# Reviewer B #7 (KPC owner, 2026-11-17): the switches live in .github/key-switches.json (a US rule file, sliced per area), so a
# switch turned on in GitHub really reaches the build and moves the hash of exactly the areas it is on for. An environment
# variable of the same name still wins (offline proofs, the scorecard).
SWITCH_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'key-switches.json')
_SW = {}


class SwitchFileError(RuntimeError): pass


def switch_file(path=None):
    """{switch: set of areas it is on for} from the switch file. A missing file = every switch at its DEFAULT; a file that cannot
    be read or has the wrong shape raises (the build must stop, never run with every switch silently off)."""
    path = path or SWITCH_FILE
    if path in _SW: return _SW[path]
    import json
    if not os.path.exists(path): _SW[path] = {}; return _SW[path]
    try: d = json.load(open(path, encoding='utf-8'))
    except (OSError, ValueError) as e: raise SwitchFileError(f'{path} cannot be read: {e}')
    sw = d.get('switches') if isinstance(d, dict) else None
    if not isinstance(sw, dict): raise SwitchFileError(f"{path}: no 'switches' object")
    out = {}
    for k, v in sw.items():
        on_ = (v or {}).get('on') if isinstance(v, dict) else None
        if not isinstance(on_, list) or not all(isinstance(a, str) for a in on_): raise SwitchFileError(f"{path}: {k} needs an 'on' list of areas")
        out[k] = set(on_)
    _SW[path] = out
    return out


def setting(name, env=None, area=None, path=None):
    env = os.environ if env is None else env
    v = str(env.get(name, '') or '').strip()
    if v: return v
    areas = switch_file(path).get(name)
    if areas is not None and areas:
        a = str(area or '')
        if '*' in areas or (a and (a in areas or ('US-' + a) in areas)): return '1'
    return DEFAULTS.get(name, '0')


def on(name, env=None, area=None, path=None):
    return setting(name, env, area, path).lower() not in ('0', 'off', 'false', 'no', '')


def areas_on(area, path=None):
    """The switches the file turns on for one area (kpc_area_hash slices the file with this)."""
    a = str(area or '')
    return sorted(k for k, s in switch_file(path).items() if '*' in s or a in s or ('US-' + a) in s)


def nf(t):
    return unicodedata.normalize('NFC', str(t or '')).strip().casefold()


# ------------------------------------------------------------------ a person's NO
def no_ids(ov):
    return {str(x) for x in ((ov or {}).get('no') or [])}


def no_names(ov, by_name=None):
    """Names that are ruled out: an exact name typed into 'no' (today's rule), plus, with KPC_NO_BY_NAME, the names saved
    with each NO in 'nofp' {id: [name, acres]}."""
    ov = ov or {}
    names = {nf(x) for x in (ov.get('no') or []) if not re.fullmatch(r'[a-z]*\d+', str(x))}
    if by_name if by_name is not None else on('KPC_NO_BY_NAME'):
        for v in (ov.get('nofp') or {}).values():
            if v and v[0]: names.add(nf(v[0]))
    return names


def _acres_close(a, b):
    try: a, b = float(a or 0), float(b or 0)
    except (TypeError, ValueError): return True
    if not a or not b: return True
    return abs(a - b) <= max(20, .1 * max(a, b))


def is_no(ov, oid, name=None, acres=None, by_name=None):
    """True when a person ruled this record out for the park: its id is in 'no', its exact name is in 'no', or (KPC_NO_BY_NAME)
    its name + acres match a saved NO fingerprint."""
    ov = ov or {}
    if str(oid) in no_ids(ov): return True
    if name is None: return False
    n = nf(name)
    if n in {nf(x) for x in (ov.get('no') or [])}: return True
    if by_name if by_name is not None else on('KPC_NO_BY_NAME'):
        # Nov 3 step 3 (US-7896 Standing Boy Creek SP: a NO on PAD-US 195158 also knocked out the state's own record sggab59, the
        # one a person joined, because both carry the same name and about the same acres): a NO fingerprint stands for a
        # renumbered copy of the SAME layer's record (the same id family: PAD-US numbers, 'sgga', 'wsa' ...), never another
        # layer's record, and never a record a person joined by its id.
        if str(oid) in {str(x) for x in (ov.get('join') or [])}: return False
        fam = re.match(r'\D*', str(oid)).group()
        for k, v in (ov.get('nofp') or {}).items():
            if re.match(r'\D*', str(k)).group() != fam: continue
            if v and nf(v[0]) == n and _acres_close(acres, v[1] if len(v) > 1 else None): return True
    return False


def drop_no(rows, ov, by_name=None):
    """rows of [id, name, acres, how]; the ones a person ruled out are removed."""
    return [x for x in rows if not is_no(ov, x[0], x[1] if len(x) > 1 else None, x[2] if len(x) > 2 else None, by_name)]


# ------------------------------------------------------------------ a hand join by id: does the record still look like the park?
_STOP = {'state', 'park', 'national', 'forest', 'wildlife', 'management', 'area', 'recreation', 'the', 'of', 'and', 'refuge', 'nature',
         'preserve', 'historic', 'site', 'wma', 'sp', 'sra', 'nwr', 'nf', 'river', 'lake', 'county', 'unit', 'trail', 'memorial'}


def _words(t):
    return {w for w in re.findall(r'[a-z0-9]+', unicodedata.normalize('NFKD', nf(t)).encode('ascii', 'ignore').decode()) if w not in _STOP and len(w) > 1}


def id_join_name_ok(park_name, rec_name, fp_name=None):
    """(ok, why). ok when the record's name shares a real word with the park name or IS the saved fingerprint name."""
    if fp_name and nf(fp_name) == nf(rec_name): return True, 'same name as when the join was approved'
    a, b = _words(park_name), _words(rec_name)
    if a and b and a & b: return True, 'the names share ' + ', '.join(sorted(a & b)[:3])
    return False, f"the approved id now points at '{rec_name}', which does not look like '{park_name}'"


# ------------------------------------------------------------------ pre-handoff self-checks
def self_checks(ref, park, state_box=None, official_acres=None, kind_ok=None):
    """Plain-words problems with one built park before it is handed to chat 11 / the waiting room. park = the key entry
    {'n','t','m','c',...}. state_box = (south, west, north, east) or None; official_acres = the park's own acres or None;
    kind_ok(park_type, record_name) -> bool or None."""
    out = []
    for k in ('n', 'm', 'c'):
        if k not in park: out.append(f'missing field {k}')
    if not str(park.get('n') or '').strip(): out.append('no park name')
    m = park.get('m') or []
    for x in m:
        if not isinstance(x, (list, tuple)) or len(x) < 4: out.append(f'joined row is not [id, name, acres, how]: {str(x)[:60]}'); continue
        if x[0] in (None, ''): out.append(f"joined row with no id ({x[1]})")
    tot = sum(float(x[2] or 0) for x in m if isinstance(x, (list, tuple)) and len(x) > 2 and isinstance(x[2], (int, float)))
    if m and official_acres:
        try: oa = float(official_acres)
        except (TypeError, ValueError): oa = 0
        if oa > 0 and not (.2 * oa <= tot <= 5 * oa):
            out.append(f'acres: joined {tot:,.0f} ac vs the official {oa:,.0f} ac ({tot / oa:.2f}x, outside 0.2x-5x)')
    if m and tot <= 0: out.append('acres: the joined land has 0 acres')
    if m and kind_ok is not None:
        bad = [x[1] for x in m if isinstance(x, (list, tuple)) and len(x) > 1 and kind_ok(park.get('t') or '', x[1]) is False]
        if bad: out.append('layer kind: ' + '; '.join(str(b) for b in bad[:3]) + f" is another kind of place than a {park.get('t') or 'park'}")
    la, lo = park.get('la'), park.get('lo')
    if state_box and la is not None and lo is not None:
        s, w, n, e = state_box
        if not (s - .05 <= la <= n + .05 and w - .05 <= lo <= e + .05): out.append(f'pin {la:.3f},{lo:.3f} is outside the state')
    return out


# ------------------------------------------------------------------ confidence: only unsure parks reach chat 11
SURE_HOW = ('reviewed',)


def confidence(park, problems=()):
    """('sure'|'likely'|'unsure', one-line reason)."""
    m, c = park.get('m') or [], park.get('c') or []
    if problems: return 'unsure', 'self-check: ' + problems[0]
    hows = [str(x[3]) for x in m if isinstance(x, (list, tuple)) and len(x) > 3]
    if m and all(h.startswith(SURE_HOW) for h in hows): return 'sure', 'a person approved this land'
    if m and park.get('far') == 'well outside': return 'unsure', 'the POTA pin is well outside the joined land'
    if m and park.get('kept'): return 'likely', 'last good outline kept: ' + str(park['kept'])[:80]
    if m and any('pin inside' in h or 'same name' in h or h in ('name', 'words') for h in hows): return 'likely', 'same name + kind, pin checks out'
    if m: return 'likely', 'joined by ' + (hows[0] if hows else 'the name test')
    if c:
        why = str(c[0][3]) if isinstance(c[0], (list, tuple)) and len(c[0]) > 3 else 'a candidate'
        return 'unsure', f"not joined: {len(c)} candidate(s), best '{c[0][1]}' ({why})"
    if park.get('a'): return 'sure', 'sits on bigger public land (no outline of its own)'
    return 'sure', 'nothing official found near the pin'


def unsure_list(parks, problems=None):
    """[{ref, name, confidence, why}] for chat 11, unsure first then by ref (only unsure ones)."""
    problems = problems or {}
    out = []
    for ref, p in sorted(parks.items()):
        lvl, why = confidence(p, problems.get(ref) or ())
        if lvl == 'unsure': out.append({'ref': ref, 'name': p.get('n'), 'confidence': lvl, 'why': why})
    return out


# ------------------------------------------------------------------ PAD-US: an older copy of the same place from the same provider
_AGG = re.compile(r'^([A-Za-z]+)_PADUS(\d+)_(\d+)')


def padus_provider(agg_src):
    """('FWS', (4, 0)) for 'FWS_PADUS4_0Fee_FWS_FWSInterest_Simplified'; (None, None) when it is not written that way."""
    m = _AGG.match(str(agg_src or ''))
    return (m.group(1).upper(), (int(m.group(2)), int(m.group(3)))) if m else (None, None)


DEDUPE_OVERLAP = 0.9   # batch 1b (Quality): at least 90% of the older copy's land must lie inside the newer copy


def padus_old_copies(recs, keep=(), overlap=None):
    """OBJECTIDs (as str) of PAD-US records that are an OLDER PAD-US version of another record from the SAME provider with the
    same name, category and designation, about the same acres (within 5%), AND (batch 1b) at least 90% of whose land lies
    inside that newer record: overlap(old, new) -> share 0..1, or None when it cannot be measured (then nothing is dropped).
    Quality's Mohawk River SP (US-8071): NYNHP 2.0 record 232632 and 4.0 record 237555 have the same name and 105 ac but only
    24.5% of the land in common, so it is other land, not a copy. keep = ids a person joined by hand, AFTER the fingerprint
    re-find (kpc_us_key builds it): never returned. A record with no Agg_Src is never returned."""
    keep = {str(x) for x in keep}
    groups = {}
    for a in recs:
        if not isinstance(a.get('OBJECTID'), int): continue
        prov, ver = padus_provider(a.get('Agg_Src'))
        if not prov: continue
        k = (prov, nf(a.get('Unit_Nm') or a.get('Loc_Nm')), a.get('Category') or '', a.get('Des_Tp') or '')
        groups.setdefault(k, []).append((ver, a))
    out = set()
    for rows in groups.values():
        if len({v for v, _ in rows}) < 2: continue
        top = max(v for v, _ in rows)
        new = [a for v, a in rows if v == top]
        for v, a in rows:
            if v == top or str(a['OBJECTID']) in keep: continue
            ac = float(a.get('GIS_Acres') or 0)
            for b in new:
                if not _close5(ac, float(b.get('GIS_Acres') or 0)): continue
                sh = overlap(a, b) if overlap else None
                if sh is not None and sh >= DEDUPE_OVERLAP: out.add(str(a['OBJECTID'])); break
    return out


def _close5(a, b):
    return a > 0 and b > 0 and abs(a - b) <= .05 * max(a, b)


# ------------------------------------------------------------------ rule 18: a park that names a piece of a bigger area
_PIECE = r'(?:sub ?unit|unit|tract|parcel|zone|division)'
_PIECE_SKIP = {'the', 'of', 'a', 'an', 'sub', 'state', 'national', 'wildlife', 'management', 'area', 'park', 'forest', 'refuge',
               'blm', 'recreation', 'special', 'wma',
               'forever', 'wild',
               'use'}   # Nov 3 step 3: 'Public Land USE Zone' (Alberta PLUZ, CA-6125) is a kind of place, not a piece called 'use'   # batch 1b (Quality): Alabama's 'Forever Wild Tract' is a program name, not a piece (US-12740, US-13081)
_COMPASS = {'n': 'north', 's': 'south', 'e': 'east', 'w': 'west', 'ne': 'northeast', 'nw': 'northwest', 'se': 'southeast', 'sw': 'southwest'}
_PIECE_WORD = re.compile(_PIECE)


def _compass(w):
    """batch 1b (Quality: US-13221 'Gordon W. Yeager-S.E. Unit' vs MN DNR 'Gordon W. Yeager WMA: South East Unit'): compass
    words written short or in two words become one word. 'ne' / 'nw' / 'se' / 'sw' always; a single n / s / e / w only right
    before a piece word ('E Unit'), so a middle initial ('Gordon W. Yeager') stays a name."""
    out = []
    for i, x in enumerate(w):
        nxt = w[i + 1] if i + 1 < len(w) else ''
        if len(x) == 2 and x in _COMPASS: x = _COMPASS[x]
        elif len(x) == 1 and x in _COMPASS and _PIECE_WORD.fullmatch(nxt): x = _COMPASS[x]
        if out and out[-1] in ('north', 'south') and x in ('east', 'west'): out[-1] += x; continue   # 'south east' = 'southeast'
        out.append(x)
    return out


def _plain_words(t):
    t = unicodedata.normalize('NFKD', str(t or '')).encode('ascii', 'ignore').decode().lower()
    t = re.sub(r"[\u2019'`.]", '', t).replace('-', ' ')
    return _compass(re.findall(r'[a-z0-9]+', t))


def piece_words(park_name, layer=''):
    """The words that name a piece in a POTA name: 'Abo' in 'Salinas Pueblo Missions, Abo Unit National Monument', 'Hilliard'
    in '... Hilliard Tract WMA', '2' in '... Unit 2'. Empty when the name names no piece.
    Nov 3 step 3 (Quality, CA-6125 Porcupine Hills PLUZ / NV herd areas): `layer` = the record layer's own label ('Public Land
    Use Zones', 'Wildlife Management Units'). A piece word that is part of the layer's own type ('zone' on a land-use-ZONE layer)
    says what KIND of place every record there is, not which piece: it is skipped."""
    w = _plain_words(park_name)
    lw = {x.rstrip('s') for x in _plain_words(layer)} if layer else set()
    out = set()
    for i, x in enumerate(w):
        if not re.fullmatch(_PIECE, x) and not (x == 'sub' and i + 1 < len(w) and w[i + 1] == 'unit'): continue
        if x in lw and i >= 1 and w[i - 1].rstrip('s') in lw: continue   # the layer's own type PHRASE ('land use zone'), not a piece; 'Anacua Unit' on a 'Management Units' layer is still a piece
        if x == 'sub': continue
        j = i - 1
        if j >= 0 and w[j] == 'sub': j -= 1
        if j >= 0 and w[j] not in _PIECE_SKIP: out.add(w[j])
        if i + 1 < len(w) and re.fullmatch(r'\d+|[ivx]+', w[i + 1]): out.add(w[i + 1])
        elif i + 2 < len(w) and w[i + 1] == 'no' and re.fullmatch(r'\d+|[ivx]+', w[i + 2]): out.add(w[i + 2])
    return out


def _ed1(a, b):
    if a == b: return True
    if abs(len(a) - len(b)) > 1 or min(len(a), len(b)) < 5: return False
    if len(a) == len(b): return sum(x != y for x, y in zip(a, b)) == 1
    if len(a) > len(b): a, b = b, a
    return any(a == b[:i] + b[i + 1:] for i in range(len(b)))


def piece_ok(park_name, rec_name, rec_name2=None, layer=''):
    """(ok, why). ok unless the park names a piece and the record carries none of that piece's own words (a one-letter
    spelling difference in a long word counts: 'Dimmitt' / 'Dimmit'). `layer`: see piece_words."""
    pw = piece_words(park_name, layer)
    if not pw: return True, ''
    have = set(_plain_words(rec_name)) | set(_plain_words(rec_name2))
    miss = [p for p in sorted(pw) if p not in have and not (not p.isdigit() and any(_ed1(p, h) for h in have))]
    if not miss: return True, ''
    return False, f"the park is the piece '{' '.join(miss)}' of a bigger area; '{rec_name}' does not name that piece (rule 18)"


# ------------------------------------------------------------------ rule 18 tract exception (Brandon, Nov 2 8:38 PM CST)
# POTA parks that are each ONE TRACT of a single official record, reviewed by a person. ref -> the record's name, the tract's
# name, how many tracts the official source shows, who approved it, when, on which build, and the source. The key re-finds the
# record by its name every run (PAD-US gives records new ids in each version), cuts it into tracts (pieces more than 1 km apart),
# and gives the park only the tract that holds its pin. A person adds a new case here (code review) or as a 'tract' entry in
# overrides.json with the same fields. The POTA name is never changed; 'note' says what the outline is.
_SAPU = {'record': 'Salinas Pueblo Missions National Monument', 'park': 'Salinas Pueblo Missions National Monument', 'of': 3,
         'approved_by': 'Brandon (via Super Head Bot)', 'approved': '2026-11-02 8:38 PM CST',
         'build': 'KPC-Links 635d37f / KPC-Data c12914e7 (batch 1b, re-based); first built on KPC-Links 688c152 / KPC-Data 8fb4237b; Quality research read the key at KPC-Data 8a9d04f7',
         'source': 'NPS Land Resources Division boundary + tracts (SAPU) and USGS PAD-US 4.1 Fee'}
TRACT_SPLITS = {   # 'label' = the plain label Brandon asked for (8:38 PM CST): POTA's unit name + "tract (PAD-US fee piece)" (Quality grade-1b, Nov 3: the outline is the PAD-US 4.1 Fee piece, not the NPS boundary)
    'US-11813': dict(_SAPU, tract='Abo', label='Salinas Pueblo Missions NM, Abo tract (PAD-US fee piece)'),
    'US-11814': dict(_SAPU, tract='Quarai', label='Salinas Pueblo Missions NM, Quarai tract (PAD-US fee piece)'),
    'US-0961': dict(_SAPU, tract='Gran Quivira', label='Salinas Pueblo Missions NM, Gran Quivira tract (PAD-US fee piece)'),
}


def tract_label(t):
    """The plain label shown for the tract outline, e.g. 'Salinas Pueblo Missions NM, Gran Quivira tract (PAD-US fee piece)'."""
    return t.get('label') or f"{t.get('park') or t.get('record')}, {t.get('tract')} tract (official boundary piece)"


def tract_note(t):
    return (f"{tract_label(t)}. One park, {t.get('park') or t.get('record')}, in {t.get('of') or 'several'} tracts "
            f"({t.get('source') or 'official source'}); this outline is the {t.get('tract')} tract only.")


def tract_entry(ref, ov=None):
    """The person-reviewed tract entry for a park (overrides.json 'tract' first, then TRACT_SPLITS), or None."""
    t = (ov or {}).get('tract')
    if isinstance(t, dict) and t.get('record') and t.get('tract') and t.get('approved_by'): return t
    return TRACT_SPLITS.get(ref)


def tracts_of(boxes, gap_km=1.0):
    """Group a record's pieces (their [w, s, e, n] boxes) into tracts: pieces closer than gap_km belong to the same tract.
    Returns a list of lists of piece numbers."""
    import math
    n = len(boxes); grp = list(range(n))
    def find(i):
        while grp[i] != i: grp[i] = grp[grp[i]]; i = grp[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            a, b = boxes[i], boxes[j]
            la = (a[1] + a[3] + b[1] + b[3]) / 4
            dx = max(0, b[0] - a[2], a[0] - b[2]) * 111.32 * math.cos(math.radians(la)); dy = max(0, b[1] - a[3], a[1] - b[3]) * 110.57
            if math.hypot(dx, dy) <= gap_km: grp[find(i)] = find(j)
    out = {}
    for i in range(n): out.setdefault(find(i), []).append(i)
    return sorted(out.values(), key=lambda v: v[0])

def saved_row_ok(row, rec):
    """D1 (KPC owner, 2026-11-17): does a saved join row [id, name, acres, how] still describe record `rec` of this read?
    Same name (accents and case aside) and acres within 10% (at least 20 acres slack); a 0 on either side skips the acres test."""
    nm = rec.get('Unit_Nm') or rec.get('Loc_Nm') or ''
    if nf(nm) != nf(row[1] if len(row) > 1 else ''): return False
    sa, ra = (row[2] if len(row) > 2 else 0) or 0, rec.get('GIS_Acres') or 0
    if not sa or not ra: return True
    return abs(ra - sa) <= max(20, 0.10 * sa)


def _full(t):
    """A full name for D9: case and accents aside, brackets and punctuation out, spaces squeezed."""
    import re as _re
    s = nf(_re.sub(r'\(.*?\)', ' ', str(t or '')))
    return ' '.join(_re.sub(r"[^\w ]+", ' ', s).split())


def d9_winner(record_name, parks):
    """D9 (KPC owner, 2026-11-17): of the parks {ref: park name} sharing one record, the ONE whose full name is the record's own
    name, or None when no park or more than one park carries it."""
    rn = _full(record_name)
    if not rn: return None
    w = [r for r, n in parks.items() if _full(n) == rn]
    return w[0] if len(w) == 1 else None


def lake_inside_land(water_bb, water_acres, land_bbs, land_acres, pad=0.0):
    """D4 (KPC owner, 2026-11-17 9:17 AM): does a lake surface sit inside the park's own land? -> (keep, why).
    water_bb / land_bbs are [x0, y0, x1, y1] boxes (degrees), pad the working copy's slack in degrees. The lake must lie inside the
    box of the park's own land, and (when both sizes are known) be no bigger than that land; a lake over 3 times the land never
    joins by name."""
    lb = [b for b in land_bbs or [] if b]
    if not water_bb or not lb: return False, 'no land outline to hold the lake'
    if water_acres and land_acres and water_acres > 3 * land_acres: return False, 'the lake is over 3 times the park\'s own land'
    x0, y0 = min(b[0] for b in lb) - pad, min(b[1] for b in lb) - pad
    x1, y1 = max(b[2] for b in lb) + pad, max(b[3] for b in lb) + pad
    if not (x0 <= water_bb[0] and y0 <= water_bb[1] and water_bb[2] <= x1 and water_bb[3] <= y1):
        return False, 'the lake reaches past the park\'s own land'
    if water_acres and land_acres and water_acres > land_acres: return False, 'the lake is bigger than the park\'s own land'
    return True, 'the lake sits inside the park\'s own land'


# ---------------------------------------------------------------- THE CONTEST (matching plan section 1; Fable 17 Nov, owner YES)
# A record joined by name to two or more parks goes to the park it fits best; a tie or a bare name goes to a person (never left on
# everyone); a record whose own type words name BOTH parks' kinds ('... State Forest & Wildlife Management Area') stays on both.
# Type words include the short forms agencies write (SP, SF, WA, WMA, SB, SHP, SRA, SNA, DNP, NWR, NF, CA ...): kinds() in the US
# key does not know them, which is why 'Scioto Trail SF' sat on both the State Park and the State Forest.
TYPE_WORDS = [('park', r'state (resort )?park|\bsp\b|\bsrp\b|national park|\bnp\b|\bstate parks?\b'),
              ('forest', r'\bforests?\b|\bsf\b|\bnf\b'),
              ('wildlife', r'wildlife (management )?area|\bwma\b|\bwa\b|\bswa\b|\bfwa\b|game lands?|\bsgl\b|hunting area|game area|fish and wildlife area|wildlife habitat'),
              ('beach', r'\bbeach\b|\bsb\b'),
              ('historic', r'histori|\bshp\b|\bshs\b|\bhs\b|\bnhs\b|\bnhp\b'),
              ('recreation', r'recreation (area|site)|\bsra\b|\bnra\b|\bsrs\b'),
              ('preserve', r'\bpreserve\b|\bdnp\b|\bsnp\b|natural area|\bsna\b|nature reserve'),
              ('wilderness', r'wilderness(?! study)'), ('study', r'study area|\bwsa\b'), ('refuge', r'\brefuge\b|\bnwr\b'),
              ('fishing', r'fishing (lake|area)|\bsfl\b|\bpfl\b|fishing access'), ('monument', r'\bmonument\b'),
              ('conservation', r'conservation area|\bnca\b|\bsca\b'), ('herd', r'\bherd\b|\bhma\b'), ('rma', r'recreation management|\bs?rma\b')]
# a layer's own kind (state-gis 'kind', or the US key's kind tags of a national layer) when the record's name carries no type word
LAYER_TYPE = {'park': 'park', 'sp': 'park', 'wild': 'wildlife', 'wma': 'wildlife', 'forest': 'forest', 'sf': 'forest', 'nf': 'forest',
              'preserve': 'preserve', 'snp': 'preserve', 'nwr': 'refuge', 'hma': 'herd', 'wsa': 'study', 'rma': 'rma', 'nps': 'park'}


def type_words(s):
    """The kinds of place a name's own type words say: {'park', 'forest', ...} (short forms included)."""
    t = re.sub(r'[^a-z ]', ' ', str(s or '').lower())
    return {k for k, rx in TYPE_WORDS if re.search(rx, t)}


def contest(record_name, parks, place=None, layer_kinds=()):
    """parks: {ref: (park name, park type)} of the parks a record is joined to by name. -> ('win', ref) | ('both', None) |
    ('person', why). place(s) = the US key's norm() (place words only), used to break a tie between two parks of the same kind."""
    names = {r: str(v[0] or '') for r, v in parks.items()}
    full = _full(record_name)
    w = [r for r, n in names.items() if _full(n) == full]
    if len(w) == 1: return 'win', w[0]
    if len(w) == len(names) or len({_full(n) for n in names.values()}) == 1:
        return 'both', None   # every sharing park has the same name: POTA lists one place twice ('same land, two park numbers')
    rs = type_words(record_name)
    ps = {r: type_words(v[0]) | type_words(v[1]) for r, v in parks.items()}
    if rs and re.search(r'\band\b|&|/', str(record_name).lower()) and all(ps[r] & rs for r in parks) and len({frozenset(ps[r] & rs) for r in parks}) == len(parks):
        return 'both', None
    if not rs: rs = {LAYER_TYPE[k] for k in layer_kinds if k in LAYER_TYPE}
    if not rs: return 'person', 'a bare name with no type word: which park it belongs to is for a person'
    k = [r for r in parks if ps[r] & rs]
    if len(k) == 1: return 'win', k[0]
    if not k: return 'person', 'the record names a kind of place that none of these parks is'
    if place is not None:
        pr = place(record_name)
        eq = [r for r in k if place(names[r]) == pr]
        if len(eq) == 1: return 'win', eq[0]
    ex = [r for r in k if ps[r] == rs]
    if len(ex) == 1: return 'win', ex[0]
    return 'person', 'the record fits more than one of these parks'
