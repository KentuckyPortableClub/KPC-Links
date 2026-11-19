#!/usr/bin/env python3
"""Fable's last look (19 Nov; .claude/notes/key-quality.md section 15): one NPS unit code can hold a PARK and a PRESERVE (DENA =
Denali National Park and Denali National Preserve, which POTA numbers apart). The unit-code join (KPC_NPS_UNIT_CODE) never puts a
Preserve record on a park that is not a preserve, nor the other way round; a combined 'Park & Preserve' unit is both.
Permanent case with the real name and acres: Denali National Park US-0022 took the 1,311,169-acre 'Denali National Preserve'
(PAD-US 3300) in the 18 Nov offline build of main's rules (the outside agent's second look; NPS: Park 4,740,091 acres, Preserve
1,334,118 acres). Also: this change's own scope entry and changelog line, found by their id."""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCR = ROOT / '.github' / 'scripts'
sys.path.insert(0, str(SCR))
import kpc_key_rules as KR  # noqa: E402
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok: FAILS.append(what)


check(KR.nps_part_clash('Denali National Park', 'Denali National Preserve'), "Denali NP US-0022 does not take 'Denali National Preserve' (3300, 1,311,169 ac) by the code DENA")
check(KR.nps_part_clash('Denali National Preserve', 'Denali National Park'), '... nor the preserve the park record')
check(not KR.nps_part_clash('Denali National Park', 'Denali National Park'), "the park's own record still joins by the code (4,680,746 ac)")
check(not KR.nps_part_clash('Wrangell-St. Elias National Park & Preserve', 'Wrangell - St Elias National Preserve'), "a combined 'Park & Preserve' park takes both parts")
check(not KR.nps_part_clash('Big Cypress National Preserve', 'Big Cypress National Preserve'), 'a preserve takes its own preserve record')
check(KR.nps_part_clash('Great Sand Dunes National Park', 'Great Sand Dunes National Preserve'), 'Great Sand Dunes: park and preserve kept apart')

src = (SCR / 'kpc_us_key.py').read_text(encoding='utf-8')
i = src.find('if KR.nps_part_clash(p.get(\'n\') or \'\', nm):')
j = src.find("p['m'] = sorted(list(p.get('m') or []) + [[a['OBJECTID'], nm, round(a.get('GIS_Acres') or 0), tag]]")
check(0 < i < j, 'nps_code_joins tests park / preserve before it joins a record by the code')

sc = next((c for c in json.loads((ROOT / '.github/us-key-rule-scope.json').read_text())['changes'] if c.get('id') == '2026-11-19-nps-park-preserve'), {})
check(sc.get('from') == '99e1aa58edd9' and 'US-AK' in sc.get('scope', {}).get('states', []) and 'APPROVED' in str(sc.get('approved')),
      'scope entry 2026-11-19-nps-park-preserve (from #271\'s 99e1aa58edd9, Alaska among its states, approved)')
log = (ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
own = next((x for x in log.splitlines() if 'branch prep/nps-unit-code-preserve' in x and 'US rules 99e1aa58edd9 -> ' in x), '')
check(bool(own) and 'APPROVED' in own, "this change's own changelog line is there and approved by the owner")

print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
