#!/usr/bin/env python3
"""Q1 (KPC owner, 18 Nov 5:48 AM: 'Yes to 1-3'; reading ruled 1:45 PM: 'Go with what you think is best'; .claude/notes/
key-quality.md sections 11 step 1 and 14): the rows of an approximate saved answer ('reviewed-approx': the closest official land,
bigger or another shape) go to check until a person verifies an outline with evidence. Rows the rules joined alone stay
(Walton WMA, Bluestone, Gran Quivira: Fable's review of #270). A park left with nothing is pin only, and its last good outline is
never kept.
Permanent cases with the real names and acres (key-quality.md section 1 (6)): Mt Etna on all of Salamonie Lake, and the
Nebraska waterfowl areas on county-wide records (three parks on one 7,011-acre record). Also: this change's own scope entry
and changelog line, found by their id."""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCR = ROOT / '.github' / 'scripts'
sys.path.insert(0, str(SCR))
import kpc_key_rules as KR  # noqa: E402
import kpc_key_freeze as KF  # noqa: E402
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok: FAILS.append(what)


# the switch: ON by default for the US key, off when an offline proof says so
check(KR.DEFAULTS.get('KPC_APPROX_PIN') == '1', 'KPC_APPROX_PIN is ON by default (Q1 is an approved ruling)')
check(KR.on('KPC_APPROX_PIN', env={'KPC_APPROX_PIN': '0'}) is False, 'an environment value of 0 turns it off (offline proofs)')

# Mt Etna (US-4179): a small state recreation area joined to the whole 10,768-acre Salamonie Lake property
etna = {'n': 'Mt Etna on Salamonie Lake State Recreation Area', 'g': 'approximate',
        'm': [['ind5037', 'Salamonie Lake', 10768, 'reviewed-approx']], 'c': []}
check(KR.approx_pin(etna, {'join': ['ind5037'], 'approx': True}) is True, 'Mt Etna: an approximate saved answer acts')
check(etna['m'] == [] and etna.get('approx_pin'), 'Mt Etna: nothing left, marked pin only')
check(etna['c'] == [['ind5037', 'Salamonie Lake', 10768, KR.APPROX_PIN_WHY]], 'Mt Etna: the Salamonie Lake row goes to check with the Q1 reason')

# Nebraska: Moger, Massie and Smith Lagoon WPAs were all drawn as one 7,011-acre Clay County record
for ref, name in (('US-3486', 'Moger'), ('US-3489', 'Massie'), ('US-3490', 'Smith Lagoon')):
    p = {'n': f'{name} National Waterfowl Production Area', 'm': [[4664, 'Clay County Waterfowl Production Area Of Ne', 7011, 'reviewed-approx']],
         'twin': ['4664']}   # (twin kept in m by the builder; it goes with its row)
    KR.approx_pin(p, {'join': [4664], 'approx': True})
    check(p['m'] == [] and 'twin' not in p and p['c'][0][:3] == [4664, 'Clay County Waterfowl Production Area Of Ne', 7011],
          f'{ref} {name}: no 7,011-acre county record, pin only, the record listed to check')

# rows the rules joined alone STAY (Fable's review of #270, real rows from the 18 Nov offline build)
walton = {'n': 'Walton Wildlife Management Area', 'm': [[195119, 'Walton Public Dove Field & Hatchery', 248, 'reviewed-approx'],
          ['sggaa28', 'WALTON WMA', 246, 'reviewed-approx'], ['sggac763', 'WALTON WMA', 246, 'name']]}
check(KR.approx_pin(walton, {'approx': True}) is True and walton['m'] == [['sggac763', 'WALTON WMA', 246, 'name']] and 'approx_pin' not in walton,
      "Walton WMA (US-7902): the dove field (248 ac) and the row the answer named go to check; its own 'WALTON WMA' name row stays, no pin mark")
check([x[0] for x in walton['c']] == [195119, 'sggaa28'], 'Walton WMA: exactly the two reviewed-approx rows are on the check list')
blue = {'n': 'Bluestone National Wild and Scenic River', 'm': [['wsrc22', 'Bluestone Wild and Scenic River', 4336, 'name'],
        [3555, 'Bluestone National Scenic River', 3035, 'NPS unit code BLUE (POTA website nps.gov/blue)']]}
check(KR.approx_pin(blue, {'approx': True}) is False and len(blue['m']) == 2 and not blue.get('c'),
      'Bluestone WSR (US-0697): marked approximate but no approximate row: the NPS unit code join and the corridor stay')
gq = {'n': 'Salinas Pueblo Missions, Gran Quivira Unit, National Monument', 'm': [[3403, 'Salinas Pueblo Missions NM, Gran Quivira tract (PAD-US fee piece)', 611,
      'reviewed (official tract: Gran Quivira of Salinas Pueblo Missions National Monument; rule 18 tract exception)']]}
check(KR.approx_pin(gq, {'approx': True}) is False and len(gq['m']) == 1, 'Gran Quivira (US-0961): the rule-18 official tract (611 ac) stays')

# what it never touches
p = {'m': [['ind5037', 'Salamonie Lake', 10768, 'reviewed-approx']]}
check(KR.approx_pin(p, {'approx': True}, on_=False) is False and p['m'], 'switch off: nothing changes')
p = {'m': [['ind5037', 'Salamonie Lake', 10768, 'reviewed']]}
check(KR.approx_pin(p, {'join': ['ind5037']}) is False and p['m'], 'a plain reviewed answer (no approx mark) keeps its outline')
check(KR.approx_pin(p, None) is False and p['m'], 'a park with no saved answer keeps its outline')

# wiring in the builder: after every rule that edits m and before the grade; the keep-last-good guard never brings it back
src = (SCR / 'kpc_us_key.py').read_text(encoding='utf-8')
i = src.find("if KR.approx_pin(p, OVR.get(ref), _kr('KPC_APPROX_PIN')):")
g = src.find("p['g'] = ('pin' if not m else 'approximate'")
h = src.find("held_g.append(f'{ref} ({len(left)})')")
check(0 < h < i < g, 'the Q1 step runs after rule G-1 and before the park is graded')
check("if _p.get('m'): _p.pop('approx_pin', None)" in src, 'the pin-only mark stays only on a park that ended with no outline (a trail park may get its line)')
k = src.find("if (OVR.get(ref) or {}).get('approx') and _kr('KPC_APPROX_PIN'):\n                # Q1 (Fable's round 2")
check(k > 0 and src.rfind('for ref, op in old.items():', 0, k) > g and src.find("np_['c'] = _q1c; np_['kept']", k) > k
      and src.find("np_['c'] = _q1c; np_['refound']", k) > k and src.find("np_['c'] = _q1c\n", k) > k,
      'keep-last-good (kept, refound and transferred) takes the reviewed-approx rows out first and lists them to check')
check("if np_.get('approx_pin'): continue" not in src, 'the guard no longer hangs on the pin-only mark')
# Split Rock (US-6157, WY; Fable's round 2): its approximate WSA record was not in the read, so keep-last-good met its old rows
sr_old = [['wsa29617', 'Split Rock', 0, 'reviewed-approx']]
q = {'m': list(sr_old), 'c': []}
check(KR.approx_pin(q, {'approx': True}) is True and q['m'] == [] and q['c'][0][:2] == ['wsa29617', 'Split Rock'],
      'Split Rock: its old approximate row (wsa29617) is not kept; it goes to check, and the park is pin only')

# bookkeeping, by this change's own id
sc = next((c for c in json.loads((ROOT / '.github/us-key-rule-scope.json').read_text())['changes'] if c.get('id') == '2026-11-18-q1-approx-pin'), {})
check(sc.get('from') == 'b85537a27b87' and 'US-IN' in sc.get('scope', {}).get('states', []) and 'US-NE' in sc['scope']['states']
      and 'APPROVED' in str(sc.get('approved')), 'scope entry 2026-11-18-q1-approx-pin (from b85537a27b87, IN and NE among its states, approved)')
log = (ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
own = next((x for x in log.splitlines() if 'branch prep/q1-approx-pin' in x and 'US rules b85537a27b87 -> ' in x), '')
check(bool(own) and 'APPROVED' in own, "this change's own changelog line is there and approved by the owner")

print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
