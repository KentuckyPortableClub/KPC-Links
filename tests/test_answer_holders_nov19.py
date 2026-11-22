#!/usr/bin/env python3
"""KPC_ANSWER_HOLDERS (finding F2; decided 22 Nov 2026). A record a person joined to one park
(reviewed / chat / hand / answer row) and joined by name to another: the D9 full-name winner test
decides (kpc_key_rules.answer_holder_moves). Ties hold. A short form is not a full name, so nothing
moves. A name-only join never takes the record. A person's row is never moved. Switch OFF unless set.
Invented parks only. Run: python3 tests/test_answer_holders_nov19.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import pathlib, re, sys, textwrap
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

LAKE, WMA = 'Cedar Lake Wildlife Management Area', 'Cedar Wildlife Management Area'
A, B = 'US-99011', 'US-99012'
check(not KR.on('KPC_ANSWER_HOLDERS', {}) and KR.DEFAULTS.get('KPC_ANSWER_HOLDERS') == '0', 'the switch KPC_ANSWER_HOLDERS is OFF unless set')

v = KR.answer_holder_moves(LAKE, {A: (LAKE, True), B: (WMA, False)})
check(v == ('moved', A, [B]), f'the person joined the record to the park it names: the other park gives its row back {v}')
v = KR.answer_holder_moves(WMA, {A: (LAKE, False), B: (WMA, True)})
check(v == ('moved', B, [A]), f'... and the other way round {v}')
v = KR.answer_holder_moves(WMA, {A: (LAKE, True), B: (WMA, False)})
check(v == ('disagree', B, [B, A]), f'the record names the by-name park, a person said the other: they disagree, nothing moves {v}')
v = KR.answer_holder_moves('Cedar WMA', {A: (LAKE, False), B: (WMA, True)})
check(v == ('no-winner', None, []), 'a short-form record name is not a full name, so there is no winner and nothing moves')
v = KR.answer_holder_moves('Pine Hill State Forest', {'A': ('Pine Hill (Cattaraugus County) State Forest', True), 'B': ('Pine Hill (Delaware County) State Forest', False)})
check(v == ('no-winner', None, []), f'two parks that both carry the name: no single winner, nothing moves {v}')
v = KR.answer_holder_moves(WMA, {B: (WMA, True), A: (LAKE, True), 'X': ('Cedar Dam', False)})
check(v == ('people', None, []), f'two parks hold it by a person\'s row: nothing moves {v}')
check(KR.answer_holder_moves(WMA, {B: (WMA, False), A: (LAKE, False)})[0] == 'skip'
      and KR.answer_holder_moves(WMA, {B: (WMA, True), A: (LAKE, True)})[0] == 'skip',
      'a record with no person\'s row (D9 and the contest decide it, as today), or only people\'s rows, is not this step\'s')
bad = [h for h in ({'P': (WMA, True), 'Q': (LAKE, False)}, {'P': (LAKE, True), 'Q': (WMA, False)}, {'P': (WMA, True), 'Q': (WMA, False)})
       if 'P' in KR.answer_holder_moves(WMA, h)[2] and KR.answer_holder_moves(WMA, h)[0] == 'moved']
check(not bad, "a person's park is never in the list of parks that give a row back")

src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
m = re.search(r"^        if _kr\('KPC_ANSWER_HOLDERS'\):\n.*?(?=^    \S)", src, re.S | re.M)
check(bool(m) and src[m.end():].lstrip(' ').startswith(('except Exception as _e:', '# 2026-11-19 (outside review finding F10')),
      'the US key runs the step, behind its own switch, at the end of the one-record-two-parks pass (inside its try)')
def build(sw, parks):
    said = []
    ns = {'KR': KR, 're': re, 'st': 'ZZ', 'parks': parks, '_kr': lambda name: sw and name == 'KPC_ANSWER_HOLDERS', 'notice': lambda t, x: said.append(x)}
    exec(textwrap.dedent(m.group(0)), ns)
    return said
def key():
    return {A: {'n': LAKE, 'g': 'official', 'm': [[255408, LAKE, 2095, 'reviewed'], [255698, WMA, 19860, 'name']], 'c': []},
            B: {'n': WMA, 'g': 'official', 'm': [[255698, WMA, 19860, 'reviewed'], [255408, LAKE, 2095, 'name']], 'c': []},
            'US-99001': {'n': 'Lone Park', 'g': 'official', 'm': [['trl9', 'Cedar Trail', 0, 'name']], 'c': []}}
k = key(); said = build(True, k)
check([str(x[0]) for x in k[A]['m']] == ['255408'] and [str(x[0]) for x in k[B]['m']] == ['255698'],
      'ON: each park ends with only the record that names it')
check(k[A]['m'][0][3] == 'reviewed' and k[B]['m'][0][3] == 'reviewed', "ON: the person's rows stay where the person put them")
check(k[B]['c'] == [[255408, LAKE, 2095, "check (D9, saved answer): this record is US-99011's own (its full name) and a person joined it there; one record, one park unless a person says same land"]],
      'ON: the row given back goes to check with the reason')
check(k[A]['g'] == k[B]['g'] == 'official' and len(said) == 1 and '2 park(s) gave back' in said[0], 'ON: both keep land (official), one notice')
k = key(); build(False, k)
check(k == key(), 'OFF: nothing changes')
k = {A: {'n': LAKE, 'g': 'official', 'm': [[255698, WMA, 19860, 'name']], 'c': []},
     B: {'n': WMA, 'g': 'official', 'm': [[255698, WMA, 19860, 'reviewed']], 'c': []}}
build(True, k)
check(k[A]['m'] == [] and k[A]['g'] == 'pin', 'ON: a park left with no joined record is a pin (owner rule, 2026-11-10)')
k = {A: {'n': LAKE, 'g': 'official', 'm': [[255698, WMA, 19860, 'reviewed']], 'c': []},
     B: {'n': WMA, 'g': 'official', 'm': [[255698, WMA, 19860, 'name']], 'c': []}}
k0 = {r: dict(p, m=[list(x) for x in p['m']]) for r, p in k.items()}; said = build(True, k)
check(k == k0 and len(said) == 1 and 'disagree' in said[0] and A in said[0] and B in said[0],
      'ON, they disagree: nothing moves and no check row is added; the notice names both parks')
k = {A: {'n': LAKE, 'g': 'official', 'm': [['sgzz23', 'Cedar WMA', 19769, 'name']], 'c': []},
     B: {'n': WMA, 'g': 'official', 'm': [['sgzz23', 'Cedar WMA', 19769, 'reviewed']], 'c': []}}
k0 = {r: dict(p, m=[list(x) for x in p['m']]) for r, p in k.items()}; said = build(True, k)
check(k == k0 and not said, 'ON, no winner (a short-form record): nothing moves, no notice')
k = {A: {'n': LAKE, 'g': 'official', 'm': [[255408, LAKE, 2095, 'reviewed']], 'c': []},
     B: {'n': WMA, 'g': 'official', 'm': [[255408, LAKE, 2095, 'name']], 'c': [], 'parts': {'255408': [[0, 0, 1, 1]]}}}
k0 = {r: dict(p, m=[list(x) for x in p['m']]) for r, p in k.items()}; build(True, k)
check(k == k0, 'ON: a park given only its own parts of the record (B12) is not a holder')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
