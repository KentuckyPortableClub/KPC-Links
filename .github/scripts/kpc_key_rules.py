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
"""
import os, re, unicodedata

DEFAULTS = {'KPC_NO_ALL_PATHS': '1', 'KPC_NO_BY_NAME': '0', 'KPC_ID_JOIN_NAME': '0', 'KPC_REFOUND_NEAR': '0',
            'KPC_SELF_CHECKS': '0', 'KPC_CONF_SORT': '0'}


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
