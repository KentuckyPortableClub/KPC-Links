#!/usr/bin/env python3
"""Q1 (KPC owner, 18 Nov 5:48 AM: 'Yes to 1-3'; .claude/notes/key-quality.md section 11 step 1): a park whose saved answer is
marked approximate ('reviewed-approx': the closest official land, bigger or another shape) is PIN ONLY until a person verifies an
outline with evidence. Its rows go to check with the reason, and the last good outline is never kept for it.
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
check(etna['m'] == [] and etna.get('approx_pin'), 'Mt Etna: no outline, marked pin only')
check(etna['c'] == [['ind5037', 'Salamonie Lake', 10768, KR.APPROX_PIN_WHY]], 'Mt Etna: the Salamonie Lake row goes to check with the Q1 reason')

# Nebraska: Moger, Massie and Smith Lagoon WPAs were all drawn as one 7,011-acre Clay County record
for ref, name in (('US-3486', 'Moger'), ('US-3489', 'Massie'), ('US-3490', 'Smith Lagoon')):
    p = {'n': f'{name} National Waterfowl Production Area', 'm': [[4664, 'Clay County Waterfowl Production Area Of Ne', 7011, 'reviewed-approx']],
         'twin': ['4664']}
    KR.approx_pin(p, {'join': [4664], 'approx': True})
    check(p['m'] == [] and 'twin' not in p and p['c'][0][:3] == [4664, 'Clay County Waterfowl Production Area Of Ne', 7011],
          f'{ref} {name}: no 7,011-acre county record, pin only, the record listed to check')

# rows the rules joined on the same park go too (the ruling is pin only, not 'the rules result')
p = {'m': [[3993, 'Kearney County Waterfowl Production Area', 2891, 'reviewed-approx'], [77, 'Jensen Lagoon', 40, 'name']]}
KR.approx_pin(p, {'approx': True})
check(p['m'] == [] and len(p['c']) == 2, 'Jensen Lagoon: every row of an approximate park goes to check, a name row too')

# what it never touches
p = {'m': [['ind1', 'Salamonie Lake State Forest', 850, 'reviewed']]}
check(KR.approx_pin(p, {'join': ['ind1']}) is False and p['m'], 'a plain reviewed answer (no approx mark) keeps its outline')
check(KR.approx_pin(p, None) is False and p['m'], 'a park with no saved answer keeps its outline')
p = {'m': [['ind5037', 'Salamonie Lake', 10768, 'reviewed-approx']]}
check(KR.approx_pin(p, {'approx': True}, on_=False) is False and p['m'], 'switch off: nothing changes')

# wiring in the builder: after every rule that edits m and before the grade; the keep-last-good guard never brings it back
src = (SCR / 'kpc_us_key.py').read_text(encoding='utf-8')
i = src.find("if KR.approx_pin(p, OVR.get(ref), _kr('KPC_APPROX_PIN')):")
g = src.find("p['g'] = ('pin' if not m else 'approximate'")
h = src.find("held_g.append(f'{ref} ({len(left)})')")
check(0 < h < i < g, 'the Q1 step runs after rule G-1 and before the park is graded (so g = pin)')
k = src.find("if np_.get('approx_pin'): continue")
check(k > 0 and src.rfind('for ref, op in old.items():', 0, k) > g, 'keep-last-good skips a Q1 park (its old outline is not kept)')

# bookkeeping, by this change's own id
sc = next((c for c in json.loads((ROOT / '.github/us-key-rule-scope.json').read_text())['changes'] if c.get('id') == '2026-11-18-q1-approx-pin'), {})
check(sc.get('from') == 'b85537a27b87' and 'US-IN' in sc.get('scope', {}).get('states', []) and 'US-NE' in sc['scope']['states']
      and 'APPROVED' in str(sc.get('approved')), 'scope entry 2026-11-18-q1-approx-pin (from b85537a27b87, IN and NE among its states, approved)')
log = (ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
own = next((x for x in log.splitlines() if 'branch prep/q1-approx-pin' in x and 'US rules b85537a27b87 -> ' in x), '')
check(bool(own) and 'APPROVED' in own, "this change's own changelog line is there and approved by the owner")

print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
