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
  (no switch)             RULE 18 TRACT EXCEPTION (Brandon, Nov 2 8:38 PM CST): when an official source (NPS, PAD-US) shows one
                          park as separate TRACTS and POTA lists each tract as its own park, each POTA park gets its own tract
                          of that record, never the whole. Only for parks a person reviewed (TRACT_SPLITS below, or a 'tract'
                          entry a person puts in overrides.json), only when the record really has separate tracts, and only
                          when the park's pin is inside its tract (or within 30 m of it). Everything else stays rule 18 (a pin).
"""
import os, re, unicodedata

DEFAULTS = {'KPC_NO_ALL_PATHS': '1', 'KPC_NO_BY_NAME': '0', 'KPC_ID_JOIN_NAME': '0', 'KPC_REFOUND_NEAR': '0',
            'KPC_SELF_CHECKS': '0', 'KPC_CONF_SORT': '0', 'KPC_PADUS_DEDUPE': '0', 'KPC_PIECE_NAME': '0',
            'KPC_NO_OFFICE_JOIN': '0'}


def setting(name, env=None):
    env = os.environ if env is None else env
    v = str(env.get(name, '') or '').strip()
    return v if v else DEFAULTS.get(name, '0')


def on(name, env=None):
    return setting(name, env).lower() not in ('0', 'off', 'false', 'no', '')


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
        for v in (ov.get('nofp') or {}).values():
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
               'forever', 'wild'}   # batch 1b (Quality): Alabama's 'Forever Wild Tract' is a program name, not a piece (US-12740, US-13081)
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


def piece_words(park_name):
    """The words that name a piece in a POTA name: 'Abo' in 'Salinas Pueblo Missions, Abo Unit National Monument', 'Hilliard'
    in '... Hilliard Tract WMA', '2' in '... Unit 2'. Empty when the name names no piece."""
    w = _plain_words(park_name)
    out = set()
    for i, x in enumerate(w):
        if not re.fullmatch(_PIECE, x) and not (x == 'sub' and i + 1 < len(w) and w[i + 1] == 'unit'): continue
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


def piece_ok(park_name, rec_name, rec_name2=None):
    """(ok, why). ok unless the park names a piece and the record carries none of that piece's own words (a one-letter
    spelling difference in a long word counts: 'Dimmitt' / 'Dimmit')."""
    pw = piece_words(park_name)
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
TRACT_SPLITS = {   # 'label' = the plain label Brandon asked for (8:38 PM CST): POTA's unit name + "tract (NPS boundary piece)"
    'US-11813': dict(_SAPU, tract='Abo', label='Salinas Pueblo Missions NM, Abo tract (NPS boundary piece)'),
    'US-11814': dict(_SAPU, tract='Quarai', label='Salinas Pueblo Missions NM, Quarai tract (NPS boundary piece)'),
    'US-0961': dict(_SAPU, tract='Gran Quivira', label='Salinas Pueblo Missions NM, Gran Quivira tract (NPS boundary piece)'),
}


def tract_label(t):
    """The plain label shown for the tract outline, e.g. 'Salinas Pueblo Missions NM, Gran Quivira tract (NPS boundary piece)'."""
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
