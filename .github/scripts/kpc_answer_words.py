#!/usr/bin/env python3
"""KPC shared answer words (Nov 3, Mapping; Quality grade-answer-sheet R1/R2 + bot-review R5): ONE list of words a person writes,
used by every reader (the key builders' answer-sheet reader, the answer-sheet checker, the pre-check stage).

A person only ever writes: YES / NO / PIN / FIXED / NOT SURE.
  YES       the record is this park's land (on the answer sheet it joins, with a person's sign-off and a date)
  NO        it is not (the row is not used; the person also adds the id to overrides 'no', which always wins)
  PIN       the POTA pin is wrong, not the record (the row is NOT SURE until it is re-checked)
  FIXED     a person changed something and it needs a fresh check (NOT SURE until re-checked)
  NOT SURE  a person must look again (old spellings CAN'T TELL / CANT_TELL / STALE mean this)
Internal states (written by bots, never by a person): PROPOSED (a bot's suggestion, not used) and APPROVED (old word for YES).
Any other word, or a typo, reads as NOT SURE: never as "ignore", so a park never falls back to a guess because of a typo.
This file is identical in KPC-Links and KPC-Data .github/scripts/ (tests check the copy: same sha256 in the NOTES).
"""
import datetime, json, re

WORDS = ('YES', 'NO', 'PIN', 'FIXED', 'NOT SURE')
SAME = {'APPROVED': 'YES', 'CANT_TELL': 'NOT SURE', "CAN'T TELL": 'NOT SURE', 'CANT TELL': 'NOT SURE', 'CAN’T TELL': 'NOT SURE',
        'STALE': 'NOT SURE', 'NOT_SURE': 'NOT SURE', 'NOTSURE': 'NOT SURE', 'UNSURE': 'NOT SURE'}
INTERNAL = ('PROPOSED', '')


def word(w):
    """-> (shared word or 'PROPOSED', known?)  Unknown words -> ('NOT SURE', False)."""
    w = ' '.join(str(w or '').replace('\u2019', "'").strip().upper().split())
    if w in INTERNAL: return 'PROPOSED', True
    if w in WORDS: return w, True
    if w in SAME: return SAME[w], True
    return 'NOT SURE', False


def use(w):
    """What a sheet row in status w does: 'join' (YES), 'ignore' (NO: overrides 'no' carries it), 'not sure' (PIN / FIXED /
    NOT SURE / any unknown word: a question for a person, never a guess), 'proposed' (not used yet)."""
    s, _ = word(w)
    return {'YES': 'join', 'NO': 'ignore', 'PROPOSED': 'proposed'}.get(s, 'not sure')


def persons(env_value, default='Brandon,KZ4CP'):
    return {p.strip().lower() for p in (env_value or default).split(',') if p.strip()}


def signed_off(approved_by, approved_date, who, today=None):
    """R2: a person's sign-off = one of the comma / semicolon / plus / ampersand separated names in approved_by is EXACTLY a
    listed person (case-insensitive), AND approved_date is a real date (YYYY-MM-DD) that is not in the future.
    'not Brandon', 'waiting for Brandon' and 'Brandon (TEST ROW, not real)' are not sign-offs."""
    names = {n.strip().lower() for n in re.split(r'[,;+&]|\band\b', str(approved_by or '')) if n.strip()}
    if not names & set(who): return False
    try: d = datetime.date.fromisoformat(str(approved_date or '').strip()[:10])
    except ValueError: return False
    return d <= (today or datetime.date.today())


def fp_cell(txt):
    """R3: the fp cell -> (name, acres float or None), or None when the cell is not a [name, acres] list (that row is NOT SURE)."""
    try: v = json.loads(txt) if str(txt or '').strip() else None
    except ValueError: return None
    if v is None: return ('', None)
    if not isinstance(v, list) or not v or not isinstance(v[0], str): return None
    a = v[1] if len(v) > 1 else None
    if a in (None, ''): return (v[0], None)
    try: a = float(str(a).replace(',', ''))
    except ValueError: return None
    return (v[0], a)
