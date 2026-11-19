#!/usr/bin/env python3
"""R-PP1 (Fable 19 Nov; .claude/notes/key-quality.md section 19 items 4 and 10): a park number does NOT cover the national preserve
beside it unless POTA's own name for that number says so. POTA numbers park and preserve apart where it wants them (Glacier Bay
US-12607 + US-0029, Aniakchak US-0902 + US-0003, Great Sand Dunes US-0033 + US-8295). Switch KPC_PRESERVE_APART (default ON).
Permanent cases with the real names and acres (PAD-US records in the 19 Nov saved shapes; Kit B, the outside agent):
  Wrangell-St. Elias NP US-0069 took 'Wrangell-St. Elias National Preserve' (3314, 4,334,094 ac) by name
  Katmai NP US-0044 took 'Katmai National Preserve' (3304, 328,054 ac)
  Lake Clark NP US-0048 took 'Lake Clark National Preserve' (3305, 1,249,676 ac)
  Gates of the Arctic NP US-0026 took 'Gates of the Arctic National Preserve' (3301, 945,247 ac)
  Craters of the Moon NM US-0665 took 'Craters of the Moon National Preserve' (3299, 411,913 ac)
Each keeps its own park / monument record. Oregon Caves NM US-0953 keeps its ONE record 'Oregon Caves National Monument and
Preserve' (3395, 4,531 ac): a combined name is both. A person's join ('reviewed...') stands.
R-PP1a (Fable 19 Nov, owner 8:13 AM '1 yes for now'): a row whose record holds POTA's OWN PIN for that number stays and is named
as a person's question: Wrangell-St. Elias US-0069 and Craters of the Moon US-0665 keep the preserve until POTA answers. Also: this change's own scope entry
and changelog line, found by their id."""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCR = ROOT / '.github' / 'scripts'
sys.path.insert(0, str(SCR))
import kpc_key_rules as KR  # noqa: E402
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok: FAILS.append(what)


# 1. the name test (shared with the unit-code join of #276)
check(KR.DEFAULTS.get('KPC_PRESERVE_APART') == '1', 'switch KPC_PRESERVE_APART is ON by default')
check(KR.nps_part_clash('Craters of the Moon National Monument', 'Craters of the Moon National Preserve'), 'a monument number does not take the preserve record')
check(not KR.nps_part_clash('Oregon Caves National Monument', 'Oregon Caves National Monument and Preserve'), "a combined 'Monument and Preserve' record is both (Oregon Caves keeps it)")
check(not KR.nps_part_clash('Wrangell-St. Elias National Park & Preserve', 'Wrangell-St. Elias National Preserve'), "a combined 'Park & Preserve' park takes both parts")
check(KR.nps_part_clash('Glacier Bay National Preserve', 'Glacier Bay National Park'), 'a preserve-only number (Glacier Bay US-0029) does not take the park record')

# 2. the build step itself, run on the real rows (its source is cut out of kpc_us_key.py and run with small stand-ins)
src = (SCR / 'kpc_us_key.py').read_text(encoding='utf-8')
m = re.search(r"^PRESERVE_HIT = \[\].*?^def preserve_apart\(.*?(?=^NPS_CODE_HIT = \[\])", src, re.S | re.M)
check(bool(m), 'preserve_apart() is in kpc_us_key.py, before the NPS unit-code join')
SRC_GEO = ''.join(re.search(rf"^def {fn}\(.*?(?=^def |\Z)", src, re.S | re.M).group(0) for fn in ('rings', 'in_ring', 'inside'))
ns = {'KR': KR, '_oid': lambda a: str(a['OBJECTID']), '_kr': lambda name: True, 'P_ALL': {}}
exec(SRC_GEO, ns)
exec(m.group(0) if m else 'def preserve_apart(*a, **k): return 0', ns)
recs = [{'OBJECTID': 3480, 'Unit_Nm': 'Wrangell-St. Elias National Park', 'Mang_Name': 'NPS', 'Loc_Nm': 'WRST'},
        {'OBJECTID': 3314, 'Unit_Nm': 'Wrangell-St. Elias National Preserve', 'Mang_Name': 'NPS', 'Loc_Nm': 'WRST'},
        {'OBJECTID': 3358, 'Unit_Nm': 'Craters of the Moon National Monument', 'Mang_Name': 'NPS', 'Loc_Nm': 'CRMO'},
        {'OBJECTID': 3299, 'Unit_Nm': 'Craters of the Moon National Preserve', 'Mang_Name': 'NPS', 'Loc_Nm': 'CRMO'},
        {'OBJECTID': 3395, 'Unit_Nm': 'Oregon Caves National Monument and Preserve', 'Mang_Name': 'NPS', 'Loc_Nm': 'ORCA'},
        {'OBJECTID': 3304, 'Unit_Nm': 'Katmai National Preserve', 'Mang_Name': 'NPS', 'Loc_Nm': 'KATM'},
        {'OBJECTID': 'sgalb8', 'Unit_Nm': 'Turkey Creek Tract', 'Mang_Name': 'ADCNR'}]
parks = {'US-0069': {'n': 'Wrangell-St. Elias National Park', 'm': [[3480, 'Wrangell-St. Elias National Park', 7950157, 'name'], [3314, 'Wrangell-St. Elias National Preserve', 4334094, 'name']], 'c': []},
         'US-0665': {'n': 'Craters of the Moon National Monument', 'm': [[3299, 'Craters of the Moon National Preserve', 411913, 'name'], [3358, 'Craters of the Moon National Monument', 54164, 'name']], 'c': []},
         'US-0953': {'n': 'Oregon Caves National Monument', 'm': [[3395, 'Oregon Caves National Monument and Preserve', 4531, 'words']], 'c': []},
         'US-0044': {'n': 'Katmai National Park', 'm': [[3304, 'Katmai National Preserve', 328054, 'reviewed']], 'c': []},
         'US-3709': {'n': 'Turkey Creek Nature Preserve State Conservation Area', 'm': [['sgalb8', 'Turkey Creek Tract', 462, 'name']], 'c': []}}
n = ns['preserve_apart']('AK', parks, recs, on=True)
ids = lambda r: [str(x[0]) for x in parks[r]['m']]
check(n == 2, f'two rows go to check (got {n})')
check(ids('US-0069') == ['3480'] and any(str(x[0]) == '3314' and 'R-PP1' in x[3] for x in parks['US-0069']['c']),
      'Wrangell-St. Elias NP US-0069 keeps its park record (7,950,157 ac); the 4,334,094-acre preserve goes to check')
check(ids('US-0665') == ['3358'], 'Craters of the Moon NM US-0665 keeps the 54,164-acre monument; the 411,913-acre preserve goes to check')
check(ids('US-0953') == ['3395'], "Oregon Caves NM US-0953 keeps its one 'Monument and Preserve' record (4,531 ac)")
check(ids('US-0044') == ['3304'], "a person's join ('reviewed') stands")
check(ids('US-3709') == ['sgalb8'], 'a state nature preserve on a state layer is not touched (Park Service records only)')
check(ns['preserve_apart']('AK', {'US-0069': {'n': 'Wrangell-St. Elias National Park', 'm': [[3314, 'Wrangell-St. Elias National Preserve', 4334094, 'name']]}}, recs, on=False) == 0,
      'switch OFF: nothing moves')

# 2b. R-PP1a (Fable 19 Nov, owner 8:13 AM '1 yes for now'): a row whose record holds POTA's OWN PIN stays and is a person's question.
# Real pins (KPC-Data parkinfo) and squares round the real result on the 19 Nov saved shapes: Wrangell-St. Elias's pin
# (61.5124, -142.835) and Craters of the Moon's (43.1036, -113.646) are inside the preserve; Katmai's (58.5572, -155.778) is not.
def sq(la, lo, d=0.05): return {'rings': [[[lo - d, la - d], [lo + d, la - d], [lo + d, la + d], [lo - d, la + d], [lo - d, la - d]]]}
recs2 = [dict(r) for r in recs]
for r in recs2:
    r['_g'] = {'3314': sq(61.5124, -142.835), '3299': sq(43.1036, -113.646), '3304': sq(58.0, -155.0)}.get(str(r['OBJECTID']), sq(0.0, 0.0))
pins = {'US-0069': ['Wrangell-St. Elias National Park', '', '', '', '', 61.5124, -142.835],
        'US-0665': ['Craters of the Moon National Monument', '', '', '', '', 43.1036, -113.646],
        'US-0044': ['Katmai National Park', '', '', '', '', 58.5572, -155.778]}
parks2 = {'US-0069': {'n': 'Wrangell-St. Elias National Park', 'm': [[3480, 'Wrangell-St. Elias National Park', 7950157, 'name'], [3314, 'Wrangell-St. Elias National Preserve', 4334094, 'name']], 'c': []},
          'US-0665': {'n': 'Craters of the Moon National Monument', 'm': [[3299, 'Craters of the Moon National Preserve', 411913, 'name'], [3358, 'Craters of the Moon National Monument', 54164, 'name']], 'c': []},
          'US-0044': {'n': 'Katmai National Park', 'm': [[3304, 'Katmai National Preserve', 328054, 'name']], 'c': []}}
ns['PRESERVE_ASK'].clear()
n2 = ns['preserve_apart']('AK', parks2, recs2, on=True, P=pins)
ids2 = lambda r: sorted(str(x[0]) for x in parks2[r]['m'])
check(n2 == 1 and ids2('US-0044') == [], f"R-PP1a: Katmai's pin is not in the preserve: the preserve goes to check (moved {n2})")
check(ids2('US-0069') == ['3314', '3480'] and ids2('US-0665') == ['3299', '3358'],
      "R-PP1a: POTA's own pin inside the preserve record: Wrangell-St. Elias US-0069 and Craters of the Moon US-0665 keep it")
check(sorted(h[1] for h in ns['PRESERVE_ASK']) == ['US-0069', 'US-0665'], "R-PP1a: the two kept rows are listed as a person's question")
check(ns['preserve_apart']('AK', {'US-0069': {'n': 'Wrangell-St. Elias National Park', 'm': [[3314, 'Wrangell-St. Elias National Preserve', 4334094, 'name']]}},
                           recs2, on=True, P={'US-0069': ['x', '', '', '', '', 0, 0]}) == 1, 'a 0,0 POTA pin is no pin: the rule acts')
src_i = src.find('_pa = preserve_apart(st, parks, recs, P=P)')
check(src_i > 0 and "R-PP1a park and preserve, a person's question" in src, "the build passes POTA's pins and names the kept rows once in the run's notice")

i = src.find('_pa = preserve_apart(st, parks, recs, P=P)'); j = src.find("if _kr('KPC_NPS_UNIT_CODE'):   # Handoff 8 fix 1")
check(0 < i < j, 'the build calls preserve_apart() before the NPS unit-code join')

# 3. scope entry + changelog line
sc = next((c for c in json.loads((ROOT / '.github/us-key-rule-scope.json').read_text())['changes'] if c.get('id') == '2026-11-19-r-pp1-park-preserve'), {})
check(sc.get('from') == '7c6e01e1bc2b' and {'US-AK', 'US-ID', 'US-OR'} <= set(sc.get('scope', {}).get('states', [])) and sc.get('scope', {}).get('saved_ids') is True
      and 'APPROVED' in str(sc.get('approved')), "scope entry 2026-11-19-r-pp1-park-preserve (from main's 7c6e01e1bc2b, AK ID OR among its states, saved ids, approved)")
log = (ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
own = next((x for x in log.splitlines() if 'branch prep/r-pp1-park-preserve' in x and 'US rules 7c6e01e1bc2b -> ' in x), '')
check(bool(own) and 'APPROVED, decided_by KPC owner' in own and 'R-PP1a' in own, "this change's own changelog line is there, approved by the owner (R-PP1a)")

print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
