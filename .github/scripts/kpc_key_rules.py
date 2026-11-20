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
  KPC_SELF_CHECKS      0  pre-handoff checks on each joined park (acres sanity, layer kind, missing fields, pin inside the state).
                          'report' (the switch file's 'on' list) notes them in the park ('self'). 'hold' (the switch file's
                          'hold' list, per state) moves the park to check for the SIZE line only: the measured outline ('ac')
                          against the official size, 0.33x to 3x. Layer kind and a pin outside the state are noted and do not
                          hold. A park with no official size is not held. 0 = off (today; the hold list is empty).
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
                          The same switch covers a person's own rows in overrides.json (17 Nov, HQ): a 'join' id with a saved
                          'fp' whose record now holds other land moves to the same name + acres in the same layer, or goes to
                          check (the join stays until a person answers); a 'no' id with a saved 'nofp' moves the same way (the NO is the land), and stays where it is
                          when the land is not found again (a person looks).
  KPC_ONE_RECORD_ONE_PARK 0  (KPC owner, 2026-11-17, ruling D9: one record, one park) a record joined by name to two or more parks
                          of the same kind stays with the ONE park whose full name is the record's own name; the others give it
                          back and it goes to check (a person may say it is the same land under two numbers). No single
                          winner = left as it is (the tripwire list shows it). A park given its own parts of the record (rule
                          B12 'parts') and hand joins are never moved. OFF until the owner says ON (count first, one state).
  KPC_HOLD_ON_PASS_ERROR 0  (outside review finding F10, 2026-11-19; reviewer's go 19 Nov 2026) an error
                          inside the US key's one-record-two-parks pass (the kind pass, D9, the contest) HOLDS the state: run() fails
                          for it like any other error of a state, no key file is written and its saved copy on main is kept
                          (pass_error below). OFF = today: the notice 'one-record-two-parks pass skipped', and the state is saved.
                          No error = no change either way.
  KPC_SAVED_ANSWERS_SAY 0 (outside review finding F5, 2026-11-19; reviewer's first slice, step S6b; the owner's word of 19 Nov 2026)
                          the US key's saved joins say what they could not do: a join not found in the read (no record with
                          that id, none of that name near the pin, the fingerprint finds none), a fingerprint that fits two
                          or more records (refind_saved 'two': the first one still joins, as before, and the park is named for a
                          grader; Fable + owner, 20 Nov), and one record under both 'join' and 'no' of a park (join_and_no; which wins is not changed).
                          Said in the build's notice and in the state's counts (saved_join_not_found / _two_fits / _join_and_no),
                          never as a check row. Bare-name joins are not changed. OFF = today.
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
  KPC_NPS_UNIT_CODE    0  (Handoff 8 fix 1, matching plan section 3) a POTA park whose website is nps.gov/<4-letter code> joins the Park
                          Service record(s) carrying the same unit code (PAD-US NPS records keep it in Loc_Nm; the NPS boundary layer in
                          UNIT_CODE), at any distance, with no name test. A unit that two or more POTA parks of the state use (by website or
                          by a name join: park + preserve) is settled by NAME inside the unit: a record goes to the one park whose full name
                          is the record's own name, the other gives it back (to check). A person's NO and hand joins always stand. OFF.
  KPC_FS_RIVER_NAMES   0  (Handoff 8 fix 2, reviewer A #6) a Forest Service wild and scenic river record is named 'Manistee, Michigan
                          National Wild and Scenic River' / 'Sturgeon, Michigan (Hiawatha NF) ...': the ', <State>' and the '(<forest> NF)'
                          are dropped before the name test (a park that names its forest, 'Sturgeon (Hiawatha)', only takes that forest's
                          record). Also the record's SECOND name field is tested on its own kind words when it has none ('Cumberland
                          Trail' / 'Ozone Falls' joins Ozone Falls State Natural Area), only near the pin. Study areas are not rivers. OFF.
  KPC_G8_OTHER_PLACE   0  (Handoff 8 fix 3, reviewer A #7) in rule R-G8, a shared-words record whose name says it is a school, college,
                          city, county, town, cemetery, church or airport is 'another kind of place' (to check), unless the park's own
                          name has that word or the record holds the park's full name ('Watkins Lake State Park and County Preserve').
                          Before: 'Tumalo Community School' and 'Ontario High School' were drawn into the state parks. OFF.
  KPC_WORLD_NEAR_NAME  0  (matching plan section 6; owner YES 17 Nov, grey area 3) world key: a park with no join whose pin is inside ONE
                          area of a kind that does not disagree, with a nearly identical name (near_name: one or two letters off, or
                          the same word stems with other endings), joins it as APPROXIMATE and goes on a person's list. OFF.
  KPC_STATE_COPY       0  (D7, KPC owner 17 Nov 6:06 AM) a record from a state layer D11 labels 'compilation' (a state's copy of other
                          agencies' units) is not the managing agency's own record: beside the agency's own joined record it goes to
                          check; alone it stays and the park is graded approximate. A person's join is never moved. OFF.
  KPC_AGENCY_TIE       0  (matching plan section 2, the agency leg; HQ 17 Nov) in the contest, a record that would go to a person
                          (a bare name, or it fits more than one park) goes to the ONE park whose POTA website's agency keeps its land
                          in that record's manager: .github/key-agency-table.json, learned from the person-reviewed joins (website host
                          -> managers, counted per park). Only when exactly one park's host has the manager on 2+ parks and every other
                          park's host is in the table with 0. Unknown host = no evidence = a person, as today. OFF.
  KPC_MEASURED_ACRES   0  (Handoff 8 fix 4, reviewer A #9) a joined park with no union acreage ('ac') whose records include one with no
                          acres on file (0) gets 'ac' measured from the saved shapes (records with acres on file count their own acres),
                          and 'ac_how' = 'measured' says so. The join rows are not changed. Plain Python, no shapely. OFF.
  KPC_CA_NONE_KEPT     0  (Handoff 8 fix 5, reviewer B #4; Canada) a park a person marked 'none' in data/ca-key/overrides.json (a different
                          place, no outline of its own) takes no NAME join until a person clears the 'none'. Before, 'none' only emptied
                          the check list, so a layer added later with the same name joined anyway (9 parks: Trout Brook PP, Cedar Creek
                          CA, Ministers Island NHS ...). A person's own join or alias still stands. OFF.
  KPC_CA_SAVED_ID_LAND 0  (Handoff 8 fix 6, reviewer B3; Canada) a hand join saved as a bare record id keeps the LAND it stood for:
                          name + hectares + the source's own stable id (CPCAD ZONE_ID = the tract row's 'sid'), from overrides 'fp' or the
                          published tract row. If the id now points at a record with another name, the land is found again by that id
                          (or same layer + name + hectares within 10%); if not, nothing joins by the id and the park goes to a person
                          (check B3). Today all 81 saved ids with a tract row still point at the right names (no change). OFF.
  KPC_JP_A10_NAMES     0  (Handoff 8 fix 7; Japan, kpc_world_key.py pull_a10n) the MLIT v3 codelist names a park by its bare name
                          ('102 | 網走', no 公園), so only 5 areas of the national A10-10 file were kept. ON takes the name cell next
                          to the code and adds the kind from A10_003 (網走 -> 網走国定公園; prefectural -> 自然公園). OFF.
  KPC_MK_LAYER_93      0  (Handoff 8 fix 8; North Macedonia, kpc_world_key.py) the sheet layer MapServer/94 has the monuments and
                          natural rarities but no national park; ON also reads MapServer/93 of the same service (the areas layer:
                          Galichica, Mavrovo, Pelister), code only, no data file. A record whose own Prot_Stat says 'proposed' never
                          gives official land: it leaves 'm' and is listed for a person in 'c'. OFF.
  KPC_APPROX_PIN       1  (Q1, KPC owner 18 Nov 5:48 AM: 'Yes to 1-3'; reading 1:45 PM; key-quality.md sections 11 step 1 and 14)
                          the rows that rest on an approximate saved answer ('reviewed-approx': the closest official land, bigger
                          or another shape) go to check until a person verifies an outline with evidence; every other row stays.
                          A park left with nothing is pin only and its last outline is never kept. ON for the US key (default).
  KPC_PRESERVE_APART   1  (R-PP1, Fable 19 Nov, key-quality.md section 19 items 4 + 10) a park number does NOT cover the national
                          preserve beside it unless POTA's own name for that number says so ('... and Preserve'). A Park Service
                          record named Preserve that the NAME rules joined to a park whose POTA name has no 'Preserve' (or a
                          park / monument record joined to a preserve-only number) goes to check. A person's join stands; a
                          combined 'Park & Preserve' record or park is both. ON for the US key (default).
  KPC_FAR_JOIN         1  (R-FJ1, KPC owner 19 Nov 11:49 AM: 'yes pins are only references they are not always right'; key-quality.md
                          section 19 items 26-27) a person's saved join may reach a record FAR from POTA's pin (past the 0.6 degree
                          box) when the answer names that record by its exact id in BOTH 'join' and 'far', carries decided_by and
                          evidence (who, source, saw, date), and the record read today still fits the saved fingerprint (same name,
                          acres within 10% or 20 ac). Never by name, never for a re-found id, never for an 'approx' answer, never
                          past a NO. A far id that no longer fits goes to check; a 'far' with no evidence is ignored (warning).
                          ON for the US key (default).
  KPC_PRESERVE_WITH_PARK 1 (R-PP1b, KPC owner 19 Nov 1:32 PM: 'I looked the website up from pota and each one says national park+
                          preserve or etc...no need to email them') a park number KEEPS the national preserve of its own unit (POTA's
                          website for the number is the combined 'Park & Preserve' unit) unless POTA numbers that preserve itself:
                          park and preserve are kept apart (R-PP1, the NPS unit-code step) only where another POTA park of the state
                          carries the record's own full name (Glacier Bay US-12607 / US-0029, Aniakchak US-0902 / US-0003, Great Sand
                          Dunes US-0033 / US-8295). Denali, Gates of the Arctic, Katmai, Lake Clark, Wrangell-St. Elias and Craters of
                          the Moon keep their preserve. OFF = R-PP1a as before. ON for the US key (default).
  (no switch)             RULE 18 TRACT EXCEPTION (Brandon, Nov 2 8:38 PM CST): when an official source (NPS, PAD-US) shows one
                          park as separate TRACTS and POTA lists each tract as its own park, each POTA park gets its own tract
                          of that record, never the whole. Only for parks a person reviewed (TRACT_SPLITS below, or a 'tract'
                          entry a person puts in overrides.json), only when the record really has separate tracts, and only
                          when the park's pin is inside its tract (or within 30 m of it). Everything else stays rule 18 (a pin).
"""
import json, os, re, unicodedata

DEFAULTS = {'KPC_NO_ALL_PATHS': '1', 'KPC_NO_BY_NAME': '0', 'KPC_ID_JOIN_NAME': '0', 'KPC_REFOUND_NEAR': '0',
            'KPC_SELF_CHECKS': '0', 'KPC_CONF_SORT': '0', 'KPC_PADUS_DEDUPE': '0', 'KPC_PIECE_NAME': '0',
            'KPC_NO_OFFICE_JOIN': '0', 'KPC_SAVED_ID_LAND': '0', 'KPC_ONE_RECORD_ONE_PARK': '0', 'KPC_NO_LEASE_BY_NAME': '0', 'KPC_LAKE_ONLY_IF_LAKE': '0', 'KPC_DESIGNATION_SPLIT': '0',
            'KPC_NPS_UNIT_CODE': '0', 'KPC_FS_RIVER_NAMES': '0', 'KPC_G8_OTHER_PLACE': '0',
            'KPC_MEASURED_ACRES': '0', 'KPC_CA_NONE_KEPT': '0', 'KPC_CA_SAVED_ID_LAND': '0', 'KPC_JP_A10_NAMES': '0', 'KPC_MK_LAYER_93': '0', 'KPC_AGENCY_TIE': '0', 'KPC_STATE_COPY': '0', 'KPC_WORLD_NEAR_NAME': '0', 'KPC_HOLD_ON_PASS_ERROR': '0', 'KPC_SAVED_ANSWERS_SAY': '0',
            'KPC_APPROX_PIN': '1', 'KPC_PRESERVE_APART': '1', 'KPC_FAR_JOIN': '1', 'KPC_PRESERVE_WITH_PARK': '1'}


# Reviewer B #7 (KPC owner, 2026-11-17): the switches live in .github/key-switches.json (a US rule file, sliced per area), so a
# switch turned on in GitHub really reaches the build and moves the hash of exactly the areas it is on for. An environment
# variable of the same name still wins (offline proofs, the scorecard).
SWITCH_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'key-switches.json')
_SW = {}
_HOLD = {}   # path -> {switch: set of areas whose mode is hold} (the size check; other switches ignore it)


class SwitchFileError(RuntimeError): pass


APPROX_PIN_WHY = 'check (Q1): an approximate saved answer is pin only until a person verifies the outline'


def approx_pin(p, ov, on_=True):
    """Q1 (KPC owner, 18 Nov 5:48 AM: 'Yes to 1-3'; reading ruled 18 Nov 1:45 PM: 'Go with what you think is best'; key-quality.md
    sections 11 step 1 and 14). The rows that rest on an APPROXIMATE saved answer (tagged 'reviewed-approx': the closest official
    land, bigger or another shape) give no outline until a person verifies one with evidence: those rows move to check with the
    reason. Every other row stays (an answer that loses its power does not erase what the rules joined alone: Walton WMA's own
    records, Bluestone's NPS unit code, Gran Quivira's official tract). The park is marked pin only when nothing is left.
    Returns True when a row moved. A park without the mark, or the switch off, is not touched."""
    if not on_ or not (ov or {}).get('approx'): return False
    _m = p.get('m') or []
    _ap = [x for x in _m if str(x[3] if len(x) > 3 else '').startswith('reviewed-approx')]
    if not _ap: return False
    p['c'] = list(p.get('c') or []) + [[x[0], x[1], x[2], APPROX_PIN_WHY] for x in _ap]
    p['m'] = [x for x in _m if x not in _ap]
    if p.get('twin'):
        _left = {str(x[0]) for x in p['m']}
        p['twin'] = [t for t in p['twin'] if t in _left]
        if not p['twin']: p.pop('twin')
    if not p['m']: p['approx_pin'] = 'Q1: approximate saved answer, pin only until verified'
    return True


def _area_hit(areas, area):
    """True when `area` (a state code or 'US-XX') is in the list, or the list is '*'."""
    if not areas: return False
    a = str(area or '')
    return '*' in areas or (a and (a in areas or ('US-' + a) in areas))


def switch_file(path=None):
    """{switch: set of areas it is on for} from the switch file. A 'hold' list counts as on (the size check reads it as hold).
    A missing file = every switch at its DEFAULT; a file that cannot be read or has the wrong shape raises (the build must stop,
    never run with every switch silently off)."""
    path = path or SWITCH_FILE
    if path in _SW: return _SW[path]
    import json
    if not os.path.exists(path): _SW[path] = {}; _HOLD[path] = {}; return _SW[path]
    try: d = json.load(open(path, encoding='utf-8'))
    except (OSError, ValueError) as e: raise SwitchFileError(f'{path} cannot be read: {e}')
    sw = d.get('switches') if isinstance(d, dict) else None
    if not isinstance(sw, dict): raise SwitchFileError(f"{path}: no 'switches' object")
    out, hold = {}, {}
    for k, v in sw.items():
        on_ = (v or {}).get('on') if isinstance(v, dict) else None
        if not isinstance(on_, list) or not all(isinstance(a, str) for a in on_): raise SwitchFileError(f"{path}: {k} needs an 'on' list of areas")
        h_ = (v or {}).get('hold', []) if isinstance(v, dict) else []
        if not isinstance(h_, list) or not all(isinstance(a, str) for a in h_): raise SwitchFileError(f"{path}: {k} needs a 'hold' list of areas")
        out[k] = set(on_) | set(h_)
        hold[k] = set(h_)
    _SW[path] = out
    _HOLD[path] = hold
    return out


def setting(name, env=None, area=None, path=None):
    env = os.environ if env is None else env
    v = str(env.get(name, '') or '').strip()
    if v: return v
    path = path or SWITCH_FILE
    areas = switch_file(path).get(name)
    if _area_hit((_HOLD.get(path) or {}).get(name), area): return 'hold'
    if _area_hit(areas, area): return '1'
    return DEFAULTS.get(name, '0')


def on(name, env=None, area=None, path=None):
    return setting(name, env, area, path).lower() not in ('0', 'off', 'false', 'no', '')


def areas_on(area, path=None):
    """The switches the file turns on for one area (kpc_area_hash slices the file with this)."""
    a = str(area or '')
    return sorted(k for k, s in switch_file(path).items() if '*' in s or a in s or ('US-' + a) in s)


class PassError(RuntimeError): pass


def pass_error(area, err, hold):
    """2026-11-19 (outside review finding F10; reviewer's go 19 Nov; switch KPC_HOLD_ON_PASS_ERROR, OFF): the US key's
    one-record-two-parks pass stopped with error `err` for `area`. hold False (today): returns `err` unchanged, so the caller's
    notice 'one-record-two-parks pass skipped: <error>' reads word for word as before and the state carries on. hold True:
    raises PassError naming the area, so run() fails for that state the way every other error of a state does (the builder
    says FAILED, writes no key file for it, and the state keeps its saved copy on main: held, fail closed)."""
    if hold: raise PassError(f'{area}: one-record-two-parks pass stopped with an error, so {area} is held (its saved copy is kept): {type(err).__name__}: {err}') from err
    return err


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
# Owner 20 Nov 2026, 4:52 AM ("hold parks that dont pass"); the band is the one counted on the sample (0.33x-3x).
SIZE_LO, SIZE_HI = 0.33, 3.0


def measured_acres(park):
    """The park's own outline, the key's 'ac' field (measured while KPC_MEASURED_ACRES is on). None when it was not measured.
    The sum of the joined rows is not the size: the same land from two layers would count twice."""
    ac = (park or {}).get('ac')
    if isinstance(ac, bool) or not isinstance(ac, (int, float)): return None
    return float(ac)


def self_checks(ref, park, state_box=None, official_acres=None, kind_ok=None):
    """Plain-words problems with one built park before it is handed to chat 11 / the waiting room. park = the key entry
    {'n','t','m','c',...}. state_box = (south, west, north, east) or None; official_acres = the park's own acres or None;
    kind_ok(park_type, record_name) -> bool or None. The size line uses the measured outline, not the sum of the rows, and
    only when an official size is known. A park with no official size is not a size failure."""
    out = []
    for k in ('n', 'm', 'c'):
        if k not in park: out.append(f'missing field {k}')
    if not str(park.get('n') or '').strip(): out.append('no park name')
    m = park.get('m') or []
    for x in m:
        if not isinstance(x, (list, tuple)) or len(x) < 4: out.append(f'joined row is not [id, name, acres, how]: {str(x)[:60]}'); continue
        if x[0] in (None, ''): out.append(f"joined row with no id ({x[1]})")
    tot = sum(float(x[2] or 0) for x in m if isinstance(x, (list, tuple)) and len(x) > 2 and isinstance(x[2], (int, float)) and not isinstance(x[2], bool))
    measured = measured_acres(park)
    if m and official_acres and measured is not None:
        try: oa = float(official_acres)
        except (TypeError, ValueError): oa = 0
        if oa > 0 and not (SIZE_LO * oa <= measured <= SIZE_HI * oa):
            out.append(f'acres: measured outline {measured:,.0f} ac vs the official {oa:,.0f} ac ({measured / oa:.2f}x, outside 0.33x-3x). '
                       'The official size was matched to this park by name and kind from an agency list')
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

def rec_names(rec):
    """Every name a record goes by: its name, its second name (Ohio: Unit_Nm is a code like 'CaesarCrkSP' and Loc_Nm the readable
    'CAESAR CREEK'), and the key's shown form 'second (first)' (scorecard 17 Nov: the code alone failed 164 Ohio hand joins)."""
    u, l = str(rec.get('Unit_Nm') or '').strip(), str(rec.get('Loc_Nm') or '').strip()
    out = [x for x in (u, l) if x]
    if u and l: out += [f'{l} ({u})', f'{u} ({l})']
    return out


def refind_saved(fp_name, fp_acres, family, cands):
    """KPC_SAVED_ANSWERS_SAY (2026-11-19, outside review finding F5; reviewer's first slice, step S6b): a saved join id gone from
    the read is looked for again by its fingerprint, the builder's own test: the same name (nf), the same id family (the
    letters before the number: PAD-US numbers, 'sgmta', 'wsa' ...) and acres within 10% (at least 20). cands = [(id, name,
    acres)] of the records near the pin (the caller tests the distance). -> ('one', id) / ('none', None) / ('two', [ids]).
    'two' = two or more different records fit: the builder still joins the first, as before the switch, and names the park
    in the notice so a grader can say which one is right (Fable + owner, 20 Nov 2026: nothing new for a person to pick)."""
    hits = []
    for i, n, a in cands or []:
        i = str(i)
        if (nf(n) == nf(fp_name) and re.match(r'\D*', i).group() == family
                and abs((a or 0) - (fp_acres or 0)) <= max(20, .1 * (fp_acres or 0)) and i not in hits): hits.append(i)
    if not hits: return 'none', None
    return ('one', hits[0]) if len(hits) == 1 else ('two', hits)


def join_not_found(want, ids, near_names):
    """KPC_SAVED_ANSWERS_SAY (F5): True when a saved join `want` (an id, or a bare name) finds nothing in the read: no record has
    that id (ids = every record id read) and no record near the pin has that name (near_names, nf-normalised; both may be lazy)."""
    return str(want) not in (ids or ()) and nf(want) not in near_names


def join_and_no(ov):
    """KPC_SAVED_ANSWERS_SAY (F5): the ids one park's saved answer holds under both 'join' and 'no', sorted. Said only: which of
    the two wins is not changed."""
    o = ov or {}
    return sorted({str(x) for x in o.get('join') or []} & {str(x) for x in o.get('no') or []})


FAR_EVIDENCE = ('who', 'source', 'saw', 'date')


def far_join_ok(ov, rid, rec):
    """R-FJ1 (KPC owner, 2026-11-19 11:49 AM: 'yes pins are only references they are not always right'): may the saved answer `ov`
    join record `rec` (id `rid`) although it lies far from POTA's pin? -> (status, why):
      'ok'          the id is in both 'join' and 'far', the answer has decided_by + evidence, the record fits its fingerprint
      'nofit'       asked for, but the record read today has another name or acres more than 10% (20 ac) off: check, no join
      'noevidence'  asked for, but no decided_by, no evidence (who, source, saw, date) or no fingerprint: ignored, warning
      'approx'      asked for on an 'approx' answer (Q1 keeps those a pin): ignored
      None          not asked for (the id is not in 'far', or not in 'join')."""
    rid = str(rid)
    if rid not in {str(x) for x in (ov or {}).get('far') or []} or rid not in {str(x) for x in (ov or {}).get('join') or []}: return None, ''
    if ov.get('approx'): return 'approx', "R-FJ1: 'far' on an approximate answer is ignored (Q1 keeps it a pin)"
    ev = ov.get('evidence') if isinstance(ov.get('evidence'), dict) else {}
    fp = (ov.get('fp') or {}).get(rid)
    if not str(ov.get('decided_by') or '').strip() or not all(str(ev.get(k) or '').strip() for k in FAR_EVIDENCE) or not fp:
        return 'noevidence', "R-FJ1: 'far' needs decided_by, evidence (who, source, saw, date) and the record's fingerprint: ignored"
    fn, fa = (list(fp) + [None, None])[:2]
    names = {nf(x) for x in rec_names(rec or {})}
    try: ra, fa_ = float((rec or {}).get('GIS_Acres') or 0), float(fa or 0)
    except (TypeError, ValueError): ra, fa_ = 0.0, 0.0
    if nf(fn) not in names: return 'nofit', f"check (R-FJ1): the far record no longer fits its saved name ('{fn}')"
    if abs(ra - fa_) > max(20.0, .1 * fa_): return 'nofit', f"check (R-FJ1): the far record no longer fits its saved acres ({round(fa_):,} saved, {round(ra):,} now)"
    return 'ok', 'R-FJ1: a person\'s evidence names this exact record'


def saved_row_ok(row, rec):
    """D1 (KPC owner, 2026-11-17): does a saved join row [id, name, acres, how] still describe record `rec` of this read?
    Same name (accents and case aside; any of the record's names, see rec_names) and acres within 10% (at least 20 acres
    slack); a 0 on either side skips the acres test."""
    if nf(row[1] if len(row) > 1 else '') not in {nf(n) for n in rec_names(rec) or ['']}: return False
    sa, ra = (row[2] if len(row) > 2 else 0) or 0, rec.get('GIS_Acres') or 0
    if not sa or not ra: return True
    return abs(ra - sa) <= max(20, 0.10 * sa)


def saved_land_moves(ov, by_id, refind):
    """D1 on a person's own rows (KPC owner, 2026-11-17: 'a saved id = the land; a NO likewise'). ov = one park's overrides;
    by_id = {record id: record} of this read; refind(old_id, name, acres) -> records of the SAME layer near the pin with that
    name + acres (the caller filters). Returns (new_ov, notes); new_ov is a copy, ov is not touched; notes are
    (kind, old id, new id or None, saved name, saved acres) with kind 'join moved' / 'join check' / 'no moved' / 'no kept'.
    Either of the record's names (Unit_Nm or Loc_Nm) may carry the saved name.
    A row is only looked at when its record IS in this read and no longer fits; a gone id keeps today's re-find path."""
    ov = dict(ov or {})
    notes = []
    fp, nofp = dict(ov.get('fp') or {}), dict(ov.get('nofp') or {})
    join, no = list(ov.get('join') or []), list(ov.get('no') or [])
    for k, saved, rows in (('join', fp, join), ('no', nofp, no)):
        for old in list(rows):
            sv = saved.get(str(old))
            rec = by_id.get(str(old))
            if not sv or not sv[0] or rec is None: continue
            row = [old, sv[0], sv[1] if len(sv) > 1 else 0]
            if saved_row_ok(row, rec): continue
            hits = [a for a in refind(str(old), sv[0], row[2]) if str(a.get('OBJECTID')) != str(old) and saved_row_ok(row, a)]
            if k == 'join' and hits and any(is_no(ov, a.get('OBJECTID'), a.get('Unit_Nm') or a.get('Loc_Nm'), a.get('GIS_Acres'), by_name=True) for a in hits[:1]):
                hits = []
            if len(hits) == 1:
                new = str(hits[0].get('OBJECTID'))
                rows[rows.index(old)] = hits[0].get('OBJECTID')
                saved[new] = saved.pop(str(old))
                notes.append((k + ' moved', str(old), new, sv[0], row[2]))
            elif k == 'join':   # not found again: the person's join STAYS (never worse) and the record goes to check
                notes.append(('join check', str(old), None, sv[0], row[2]))
            else:
                notes.append(('no kept', str(old), None, sv[0], row[2]))
    if fp or 'fp' in ov: ov['fp'] = fp
    if nofp or 'nofp' in ov: ov['nofp'] = nofp
    if 'join' in ov or join: ov['join'] = join
    if 'no' in ov or no: ov['no'] = no
    return ov, notes


def brackets(t):
    """The words in a name's brackets, as one lower-case string ('Horseshoe Canyon (North) BLM Wilderness Area' -> 'north');
    '' when there are none. Fable's review of #271: a bracket word that tells two parks apart is part of the name."""
    import re as _re
    return ' '.join(' '.join(_re.sub(r"[^\w ]+", ' ', nf(x)).split()) for x in _re.findall(r'\((.*?)\)', str(t or '')))


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


# ------------------------------------------------------------------ Handoff 8 fix 1: Park Service unit codes before names
_NPS_SITE = re.compile(r'(?:^|[/.])nps\.gov/([a-z]{4})(?=[/?#.]|$)', re.I)


def nps_code_from_site(url):
    """The 4-letter Park Service unit code in a POTA website ('https://www.nps.gov/guis/index.htm' -> 'GUIS'), or None.
    Only the unit folder counts: nps.gov/articles/..., nps.gov/places/..., nps.gov/nr/... name no unit."""
    m = _NPS_SITE.search(str(url or '').strip())
    return m.group(1).upper() if m else None


def nps_record_code(rec):
    """The unit code a record carries: the NPS boundary layer's UNIT_CODE, or a PAD-US Park Service record's Loc_Nm when that is a
    4-letter code (PAD-US writes 'GUIS', 'GRSA' there). None for any other record."""
    sa = (rec or {}).get('SA') or {}
    v = sa.get('UNIT_CODE') or sa.get('unit_code') or (rec or {}).get('UNIT_CODE')
    if v and re.fullmatch(r'[A-Za-z]{4}', str(v).strip()): return str(v).strip().upper()
    if str((rec or {}).get('Mang_Name') or '') == 'NPS':
        v = str((rec or {}).get('Loc_Nm') or '').strip()
        if re.fullmatch(r'[A-Z]{4}', v): return v
    return None


# ------------------------------------------------------------------ Handoff 8 fix 2: Forest Service wild and scenic river names
_FSR_STATE = re.compile(r',\s*(?:' + '|'.join(sorted({w.replace('_', ' ') for w in (
    'Alabama Alaska Arizona Arkansas California Colorado Connecticut Delaware Florida Georgia Hawaii Idaho Illinois Indiana Iowa Kansas '
    'Kentucky Louisiana Maine Maryland Massachusetts Michigan Minnesota Mississippi Missouri Montana Nebraska Nevada New_Hampshire New_Jersey '
    'New_Mexico New_York North_Carolina North_Dakota Ohio Oklahoma Oregon Pennsylvania Rhode_Island South_Carolina South_Dakota Tennessee '
    'Texas Utah Vermont Virginia Washington West_Virginia Wisconsin Wyoming').split()}, key=len, reverse=True)) + r')\b', re.I)
_FSR_FOREST = re.compile(r'\(([^)]*?)\s*(?:NF|N\.F\.|National Forests?)\s*\)', re.I)


def fs_river_record(name, layer=''):
    """A Forest Service wild and scenic river record (not a study area): its name says Wild and Scenic River and its layer is the
    Forest Service's (FS river corridors 'fwsr', FS designated areas 'fsod', or a Forest Service layer name)."""
    n = str(name or '')
    if not re.search(r'wild\s*(and|&)\s*scenic river', n, re.I) or re.search(r'study area', n, re.I): return False
    return bool(re.match(r'(fwsr|fsod)\d', str(layer or ''), re.I) or re.search(r'forest service', str(layer or ''), re.I))


def fs_river_name(name):
    """(clean name, forest) for a Forest Service river record: 'Sturgeon, Michigan (Hiawatha NF) National Wild and Scenic River' ->
    ('Sturgeon National Wild and Scenic River', 'hiawatha'); 'Manistee, Michigan National Wild and Scenic River' -> ('Manistee National
    Wild and Scenic River', '')."""
    n = str(name or '')
    m = _FSR_FOREST.search(n)
    forest = nf(m.group(1)) if m else ''
    n = _FSR_FOREST.sub(' ', n)
    n = _FSR_STATE.sub(' ', n)
    return ' '.join(n.split()), forest


def fs_river_forest_ok(park_name, forest):
    """A park that names its forest in brackets ('Sturgeon (Hiawatha) National Wild and Scenic River') takes only that forest's
    record; a record with no forest, or a park with no bracket, is not refused here."""
    pb = re.findall(r'\(([^)]*)\)', str(park_name or ''))
    if not pb or not forest: return True
    fw = set(re.findall(r'\w+', forest))
    return any(fw & set(re.findall(r'\w+', nf(b))) for b in pb)
# ------------------------------------------------------------------ Handoff 8 fix 3: schools, cities and counties are another kind of place
OTHER_PLACE = {'school': 'school', 'schools': 'school', 'college': 'college', 'colleges': 'college', 'city': 'city', 'cities': 'city',
               'county': 'county', 'counties': 'county', 'town': 'town', 'towns': 'town', 'cemetery': 'cemetery', 'cemeteries': 'cemetery',
               'church': 'church', 'churches': 'church', 'airport': 'airport', 'airports': 'airport'}


def other_place_word(park_name, rec_name):
    """R-G8 (Handoff 8 fix 3): the word that makes record `rec_name` another kind of place than the park ('school' for 'Tumalo
    Community School' vs Tumalo State Park), or '' when it may stand: no such word, the park's own name has the same word, or the
    record holds the park's full name ('Watkins Lake State Park and County Preserve' holds 'Watkins Lake State Park')."""
    rw = [OTHER_PLACE[w] for w in _full(rec_name).split() if w in OTHER_PLACE]
    if not rw: return ''
    pf = _full(park_name)
    if pf and (' ' + pf + ' ') in (' ' + _full(rec_name) + ' '): return ''
    # Sonnet's grade 18 Nov: 'Charles D. Kelley Autauga County Wildlife Management Area' IS Charles D. Kelley WMA (the county is only
    # where it lies): the record holds every word of the park's own name (type words aside) and names the same kind of place.
    tw = type_words(park_name)
    pc = _full(re.sub('|'.join(rx for _k, rx in TYPE_WORDS), ' ', str(park_name or '').lower()))
    rf = ' ' + _full(rec_name) + ' '
    if pc and all((' ' + w + ' ') in rf for w in pc.split()) and tw and (tw & type_words(rec_name)): return ''
    pw = {OTHER_PLACE[w] for w in pf.split() if w in OTHER_PLACE}
    left = [w for w in rw if w not in pw]
    return left[0] if left else ''


# ------------------------------------------------------------------ Handoff 8 fix 4: measured acres
def ring_acres(rings):
    """Acres of a record's rings (lon / lat degrees): the shoelace on a local equal-area scale (x times cos latitude), signed, so a
    hole (the other winding) subtracts; the absolute total. Plain Python."""
    import math
    tot = 0.0
    for r in rings or []:
        if len(r) < 3: continue
        lat0 = math.radians(sum(q[1] for q in r) / len(r)); kx, ky = 111320.0 * math.cos(lat0), 110574.0
        a = 0.0
        for i in range(len(r)):
            x1, y1 = r[i - 1][0] * kx, r[i - 1][1] * ky; x2, y2 = r[i][0] * kx, r[i][1] * ky
            a += x1 * y2 - x2 * y1
        tot += a / 2.0
    return abs(tot) / 4046.8564224


def measured_ac(rows, rings_of, parts=None):
    """Handoff 8 fix 4: (acres, n measured) for a park's joined rows [id, name, acres, how] when at least one has no acres on file:
    rows with acres count their own acres, rows without are measured from their saved shape (rings_of(id) -> rings; only the
    rings inside the park's own part boxes when the park has 'parts'). None when no row lacks acres or a 0-acre row has no shape."""
    zero = [x for x in rows or [] if not (x[2] if len(x) > 2 else 0)]
    if not zero: return None
    tot, n = sum(float(x[2] or 0) for x in rows if len(x) > 2 and x[2]), 0
    for x in zero:
        rr = [r for r in (rings_of(str(x[0])) or []) if len(r) > 3]
        boxes = (parts or {}).get(str(x[0]))
        if boxes:
            rr = [r for r in rr if any(b[0] - .01 <= (min(q[0] for q in r) + max(q[0] for q in r)) / 2 <= b[2] + .01
                                     and b[1] - .01 <= (min(q[1] for q in r) + max(q[1] for q in r)) / 2 <= b[3] + .01 for b in boxes)]
        if not rr: return None
        tot += ring_acres(rr); n += 1
    return round(tot), n

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
              ('reserve', r'\breservation\b|\bstate reserve\b|\bcoastal reserve\b'),   # 18 Nov held states: NC's 'Buxton Woods Coastal Reserve' = Buxton Woods State Reserve   # Sonnet 18 Nov: Mount Tom State RESERVE = the 'Mount Tom State Reservation' records
              ('wilderness', r'wilderness(?! study)'), ('study', r'study area|\bwsa\b'), ('refuge', r'\brefuge\b|\bnwr\b'),
              ('fishing', r'fishing (lake|area)|\bsfl\b|\bpfl\b|fishing access'), ('monument', r'\bmonument\b'),
              ('conservation', r'conservation area|\bnca\b|\bsca\b'), ('herd', r'\bherd\b|\bhma\b'), ('rma', r'recreation management|\bs?rma\b')]
# a layer's own kind (state-gis 'kind', or the US key's kind tags of a national layer) when the record's name carries no type word.
# Fable's review of #271 (18 Nov): the US kind tag 'wild' is WILDERNESS (the two federal wilderness layers); a state layer of kind
# 'wild' (wildlife) arrives as 'wma' through the US key's SGK table. Before, bare wilderness names were typed 'wildlife'.
LAYER_TYPE = {'park': 'park', 'sp': 'park', 'wild': 'wilderness', 'wma': 'wildlife', 'forest': 'forest', 'sf': 'forest', 'nf': 'forest',
              'preserve': 'preserve', 'snp': 'preserve', 'nwr': 'refuge', 'hma': 'herd', 'wsa': 'study', 'rma': 'rma', 'nps': 'park'}


# Held states, 18 Nov (key-quality.md section 11 step 2 (a), causes B + C): A RECORD'S LAYER SAYS WHAT KIND IT IS. A record whose own
# name has no type word ('Gold Butte' in the BLM monuments / NCAs layer, 'Mount Irish' in the ACEC layer) takes its kind from the
# title of the layer it comes from. Not for a layer that gathers many kinds of land from many owners (D11 'compilation' or
# 'register'): its title says nothing about one record. 'acec' is a layer kind only (no park name carries it as a type word here).
LAYER_TYPE_WORDS = TYPE_WORDS + [('acec', r'critical environmental concern|\bacec\b'), ('conservation', r'\bnca\b|national conservation')]


LAYER_KINDS = {k for k, _ in LAYER_TYPE_WORDS}
SAME_LAND = 'same land, two park numbers'


def layer_type_words(title, what=''):
    """The kinds of place a LAYER's own title says it holds ('BLM national monuments / conservation areas' -> {'monument',
    'conservation'}; 'ACEC Designated Polygons' -> {'acec'}). Plurals count ('monuments', 'NCAs'). A compilation or register
    layer (D11) -> set(): its title is about many kinds of land."""
    if str(what or '') in ('compilation', 'register'): return set()
    # the '(<kind>, state GIS table)' tail is the coarse state-gis kind of the whole layer, not its title (Alaska's legislatively
    # designated areas carry 'preserve' and hold special management areas, refuges, habitat areas: Kenai River US-12708)
    t = re.sub(r'\([a-z ]+, state gis table\)', ' ', str(title or '').lower())
    t = re.sub(r'(national )?(forest|park) service|fish and wildlife service|department of (fish and )?wildlife|wildlife resources', ' ', t)   # an agency's name is not a kind
    t = re.sub(r'[^a-z ]', ' ', t)
    t = re.sub(r'\b(\w{2,}[^s\W])s\b', r'\1', t)   # monuments -> monument, areas -> area, ncas -> nca (wilderness keeps its ss)
    return {k for k, rx in LAYER_TYPE_WORDS if re.search(rx, t)}


def type_words(s):
    """The kinds of place a name's own type words say: {'park', 'forest', ...} (short forms included)."""
    t = re.sub(r'[^a-z ]', ' ', str(s or '').lower())
    return {k for k, rx in TYPE_WORDS if re.search(rx, t)}


AGENCY_TABLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'key-agency-table.json')
_AGT = {}


def agency_table(path=None):
    """{host: {manager: parks, '_parks': n}} from .github/key-agency-table.json; {} when missing (no evidence, nothing decided)."""
    path = path or AGENCY_TABLE
    if path not in _AGT:
        try:
            with open(path, encoding='utf-8') as f: _AGT[path] = (json.load(f) or {}).get('hosts') or {}
        except (OSError, ValueError): _AGT[path] = {}
    return _AGT[path]


def web_host(u):
    """The host of a POTA website ('https://www.fws.gov/refuge/x' -> 'fws.gov'), as kpc_agency_table.py counts it."""
    import urllib.parse
    h = urllib.parse.urlparse(str(u or '')).netloc.lower().split(':')[0]
    return h[4:] if h.startswith('www.') else h


def _lev(a, b, cap=3):
    """Edit distance between a and b, stopping at cap."""
    if abs(len(a) - len(b)) >= cap: return cap
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1): cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        if min(cur) >= cap: return cap
        prev = cur
    return min(prev[-1], cap)


def near_name(a, b):
    """World near names (Fable's rule sheet): two cleaned names that are NOT equal but nearly the same: one or two letters off
    (both at least 6 letters; a number never differs), or the same words with other endings (each word pair shares its first
    5 letters and differs only in its last 3). A name inside a longer name is not near."""
    a, b = ' '.join(str(a or '').split()), ' '.join(str(b or '').split())
    if not a or not b or a == b: return False
    if re.findall(r'\d+', a) != re.findall(r'\d+', b): return False
    if min(len(a), len(b)) >= 6 and _lev(a, b) <= 2: return True
    wa, wb = a.split(), b.split()
    if len(wa) != len(wb): return False
    def st(x, y):
        n = 0
        while n < min(len(x), len(y)) and x[n] == y[n]: n += 1
        return x == y or (n >= 5 and max(len(x), len(y)) - n <= 3)
    return all(st(x, y) for x, y in zip(wa, wb))


def pota_numbers_part(record_name, parks, ref):
    """R-PP1b (KPC owner, 19 Nov 1:32 PM): does POTA number this part itself? The other POTA park of the state whose full name is
    the record's own name (D9), or None. parks = {ref: park name} of the state; `ref` (the park being built) is left out."""
    return d9_winner(record_name, {r: n for r, n in (parks or {}).items() if r != ref})


def nps_part_clash(park_name, record_name):
    """Fable's last look (19 Nov; the outside agent's second look): one NPS unit code can hold a PARK and a PRESERVE (DENA = Denali
    National Park and Denali National Preserve, which POTA numbers apart). A unit-code join never puts a Preserve record on a park
    that is not a preserve, nor the other way round. True = the two disagree (the record goes to check)."""
    def part(t):
        t = str(t or '').lower()
        if not re.search(r'\bpreserve\b', t): return 'other'
        return 'both' if re.search(r'\b(park|monument)\b', t) else 'preserve'   # 'Wrangell-St. Elias National Park & Preserve' is both; R-PP1: so is 'Oregon Caves National Monument and Preserve' (one record)
    return {part(park_name), part(record_name)} == {'preserve', 'other'}


def box_overlap(b1, b2):
    """Share of the smaller of two boxes [minx, miny, maxx, maxy] that the other covers (0 when either is missing)."""
    if not b1 or not b2: return 0.0
    w = max(0.0, min(b1[2], b2[2]) - max(b1[0], b2[0])); h = max(0.0, min(b1[3], b2[3]) - max(b1[1], b2[1]))
    s = min((b1[2] - b1[0]) * (b1[3] - b1[1]), (b2[2] - b2[0]) * (b2[3] - b2[1])) or 1e-12
    return w * h / s


def size_pick(acres, held, tol=0.10, floor=5.0):
    """The one ref in held = {ref: [acres of the OTHER records it already holds]} with a record within tol of `acres` (a copy of
    the same land in another layer), or None: no acres, two parks fit, or none."""
    try: a = float(acres or 0)
    except (TypeError, ValueError): return None
    if a < floor: return None
    w = [r for r, xs in held.items() if any(abs(float(x or 0) - a) <= tol * a for x in xs)]
    return w[0] if len(w) == 1 else None


def agency_pick(manager, hosts, table, min_parks=2):
    """KPC_AGENCY_TIE: hosts = {ref: website host}. The one ref whose host has `manager` on min_parks+ parks while every other
    ref's host is in the table with none of it; else None (unknown host, two hosts that fit, no manager)."""
    if not manager or not hosts: return None
    fit, known = {}, True
    for r, h in hosts.items():
        t = table.get(h) if h else None
        if t is None: known = False; continue
        fit[r] = int(t.get(str(manager)) or 0)
    w = [r for r, n in fit.items() if n >= min_parks]
    if len(w) != 1 or not known: return None
    if len({hosts[r] for r in hosts}) < 2: return None    # one agency on every side: the website cannot tell them apart
    if any(n > 0 for r, n in fit.items() if r != w[0]): return None
    return w[0]


def contest(record_name, parks, place=None, layer_kinds=(), agency=None, size=None):
    """parks: {ref: (park name, park type)} of the parks a record is joined to by name. -> ('win', ref) | ('both', None) |
    ('person', why). place(s) = the US key's norm() (place words only), used to break a tie between two parks of the same kind.
    agency(refs) -> ref or None (KPC_AGENCY_TIE: the record's manager vs the parks' websites) is asked before a 'person' answer.
    size(refs) -> ref or None (Sonnet's grade 18 Nov: Ohio's bare 'CAESAR CREEK' copy of 6,806 ac goes to the park that already holds
    its own 6,953-ac record, Caesar Creek SP, not the wildlife area) is asked first: a copy of land one park already holds."""
    names = {r: str(v[0] or '') for r, v in parks.items()}
    full = _full(record_name)
    w = [r for r, n in names.items() if _full(n) == full]
    if len(w) == 1: return 'win', w[0]
    # Fable's review of #271 (18 Nov; Horseshoe Canyon (North) US-5833 / (South) US-5846): a bracket word that differs between the
    # sharing parks is part of the name. Those parks are never 'the same name' nor 'the same place'; a record carrying one park's
    # bracket word goes to that park.
    bw = {r: brackets(n) for r, n in names.items()}
    split = len(set(bw.values())) > 1
    if split:
        rb = brackets(record_name)
        hit = [r for r in parks if rb and bw[r] == rb]
        if len(hit) == 1: return 'win', hit[0]
    if not split and (len(w) == len(names) or len({_full(n) for n in names.values()}) == 1):
        return 'both', None   # every sharing park has the same name: POTA lists one place twice ('same land, two park numbers')
    rs = type_words(record_name)
    ps = {r: type_words(v[0]) | type_words(v[1]) for r, v in parks.items()}
    if rs and re.search(r'\band\b|&|/', str(record_name).lower()) and all(ps[r] & rs for r in parks) and len({frozenset(ps[r] & rs) for r in parks}) == len(parks):
        return 'both', None
    from_layer = False
    if not rs:
        rs = {LAYER_TYPE.get(k, k) for k in layer_kinds} & LAYER_KINDS   # (a) 18 Nov: a bare name's kind is its layer's
        from_layer = bool(rs)
    k = [r for r in parks if ps[r] & rs] if rs else []
    if not rs or (from_layer and not k):
        # a bare name, or a layer kind that fits none of the parks (Fable's review of #271: a title is weaker evidence than land
        # a park already holds): the bare-name path, size first, then agency, then a person
        g = (size(list(parks)) if size else None) or (agency(list(parks)) if agency else None)
        if g: return 'win', g
        return 'person', 'a bare name with no type word: which park it belongs to is for a person'
    if len(k) == 1: return 'win', k[0]
    if not k: return 'person', 'the record names a kind of place that none of these parks is'
    if place is not None:
        pr = place(record_name)
        eq = [r for r in k if place(names[r]) == pr]
        if len(eq) == 1: return 'win', eq[0]
    ex = [r for r in k if ps[r] == rs]
    if len(ex) == 1: return 'win', ex[0]
    g = (size(k) if size else None) or (agency(k) if agency else None)
    if g: return 'win', g
    # (b) 'same land, two park numbers' by place name was taken out (Fable's last look, 19 Nov: Seven Sisters US-12918 is a 7.8-acre
    # fishing access site beside the 1,554-acre WMA US-12646). A pair is the same land only when a person recorded it with evidence.
    return 'person', 'the record fits more than one of these parks'
