#!/usr/bin/env python3
"""R-PP1b (KPC owner, 19 Nov 1:32 PM: "I looked the website up from pota and each one says national park+preserve or etc...no need to
email them"; 1:36 PM: "The Alaska parks was easy clicked on link at pota and read the hero"). A park number KEEPS the national
preserve of its own unit unless POTA numbers that preserve itself. Switch KPC_PRESERVE_WITH_PARK (default ON).
Real cases (PAD-US records in the 19 Nov saved shapes; POTA's numbers):
  keeps the preserve: Denali NP US-0022 (Denali National Preserve 3300, 1,311,169 ac), Gates of the Arctic NP US-0026 (3301,
  945,247), Katmai NP US-0044 (3304, 328,054), Lake Clark NP US-0048 (3305, 1,249,676), Wrangell-St. Elias NP US-0069 (3314,
  4,334,094), Craters of the Moon NM US-0665 (3299, 411,913)
  stays apart (POTA numbers both): Glacier Bay NP US-12607 / Preserve US-0029, Aniakchak NM US-0902 / Preserve US-0003,
  Great Sand Dunes NP US-0033 / Preserve US-8295"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCR = ROOT / '.github' / 'scripts'
sys.path.insert(0, str(SCR))
import kpc_key_rules as KR  # noqa: E402
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok: FAILS.append(what)


AK = {'US-0022': 'Denali National Park', 'US-0026': 'Gates of the Arctic National Park', 'US-0044': 'Katmai National Park',
      'US-0048': 'Lake Clark National Park', 'US-0069': 'Wrangell-St. Elias National Park', 'US-12607': 'Glacier Bay National Park',
      'US-0029': 'Glacier Bay National Preserve', 'US-0902': 'Aniakchak National Monument', 'US-0003': 'Aniakchak National Preserve'}
check(KR.DEFAULTS.get('KPC_PRESERVE_WITH_PARK') == '1', 'switch KPC_PRESERVE_WITH_PARK is ON by default')
for ref, rec in (('US-0022', 'Denali National Preserve'), ('US-0026', 'Gates of the Arctic National Preserve'), ('US-0044', 'Katmai National Preserve'),
                 ('US-0048', 'Lake Clark National Preserve'), ('US-0069', 'Wrangell-St. Elias National Preserve')):
    check(KR.pota_numbers_part(rec, AK, ref) is None, f'{ref} {AK[ref]}: POTA has no number for {rec}: the park number keeps it')
check(KR.pota_numbers_part('Glacier Bay National Preserve', AK, 'US-12607') == 'US-0029', 'Glacier Bay: POTA numbers the preserve (US-0029): apart')
check(KR.pota_numbers_part('Glacier Bay National Park', AK, 'US-0029') == 'US-12607', 'Glacier Bay: the preserve number does not take the park (US-12607)')
check(KR.pota_numbers_part('Aniakchak National Preserve', AK, 'US-0902') == 'US-0003' and KR.pota_numbers_part('Aniakchak National Monument', AK, 'US-0003') == 'US-0902',
      'Aniakchak: monument US-0902 and preserve US-0003 stay apart')
CO = {'US-0033': 'Great Sand Dunes National Park', 'US-8295': 'Great Sand Dunes National Preserve'}
check(KR.pota_numbers_part('Great Sand Dunes National Preserve', CO, 'US-0033') == 'US-8295', 'Great Sand Dunes: apart (US-0033 / US-8295)')
check(KR.pota_numbers_part('Craters of the Moon National Preserve', {'US-0665': 'Craters of the Moon National Monument'}, 'US-0665') is None,
      'Craters of the Moon US-0665 keeps the preserve')

# the build step itself (preserve_apart), cut out of kpc_us_key.py, both switch positions
src = (SCR / 'kpc_us_key.py').read_text(encoding='utf-8')
m = re.search(r"^PRESERVE_HIT = \[\].*?^def preserve_apart\(.*?(?=^NPS_CODE_HIT = \[\])", src, re.S | re.M)
SRC_GEO = ''.join(re.search(rf"^def {fn}\(.*?(?=^def |\Z)", src, re.S | re.M).group(0) for fn in ('rings', 'in_ring', 'inside'))
def run(sw):
    ns = {'KR': KR, '_oid': lambda a: str(a['OBJECTID']), '_kr': (lambda name: True) if sw else (lambda name: name != 'KPC_PRESERVE_WITH_PARK'), 'P_ALL': {}}
    exec(SRC_GEO, ns); exec(m.group(0), ns)
    recs = [{'OBJECTID': 3457, 'Unit_Nm': 'Katmai National Park', 'Mang_Name': 'NPS'}, {'OBJECTID': 3304, 'Unit_Nm': 'Katmai National Preserve', 'Mang_Name': 'NPS'},
            {'OBJECTID': 3419, 'Unit_Nm': 'Glacier Bay National Park', 'Mang_Name': 'NPS'}, {'OBJECTID': 3302, 'Unit_Nm': 'Glacier Bay National Preserve', 'Mang_Name': 'NPS'}]
    parks = {'US-0044': {'n': 'Katmai National Park', 'm': [[3457, 'Katmai National Park', 3624170, 'name'], [3304, 'Katmai National Preserve', 328054, 'name']], 'c': []},
             'US-12607': {'n': 'Glacier Bay National Park', 'm': [[3419, 'Glacier Bay National Park', 3222435, 'name'], [3302, 'Glacier Bay National Preserve', 58406, 'name']], 'c': []},
             'US-0029': {'n': 'Glacier Bay National Preserve', 'm': [[3302, 'Glacier Bay National Preserve', 58406, 'name']], 'c': []}}
    ns['preserve_apart']('AK', parks, recs, on=True, P={})
    return {r: sorted(str(x[0]) for x in p['m']) for r, p in parks.items()}
on, off = run(True), run(False)
check(on['US-0044'] == ['3304', '3457'], 'build, ON: Katmai NP US-0044 keeps its preserve record 3304')
check(on['US-12607'] == ['3419'] and on['US-0029'] == ['3302'], 'build, ON: Glacier Bay NP gives the preserve record to POTA\'s preserve number')
check(off['US-0044'] == ['3457'] and off['US-12607'] == ['3419'], 'build, OFF: R-PP1a as before (Katmai loses the preserve)')
i = src.find("def nps_code_joins"); j = src.find('def _tract_store')
check("KR.pota_numbers_part(nm, {r: q.get('n') or '' for r, q in parks.items()}, owner) is None" in src[i:j] and "_kr('KPC_PRESERVE_WITH_PARK')" in src[i:j],
      'the NPS unit-code step keeps park and preserve apart only where POTA numbers the other part (Denali joins its preserve)')

sc = next((c for c in json.loads((ROOT / '.github/us-key-rule-scope.json').read_text())['changes'] if c.get('id') == '2026-11-19-r-pp1b-preserve-with-park'), {})
check(sc.get('from') == 'c82bdade8675' and {'US-AK', 'US-ID', 'US-CO'} <= set(sc.get('scope', {}).get('states', [])) and 'APPROVED' in str(sc.get('approved')),
      "scope entry 2026-11-19-r-pp1b-preserve-with-park (from main's c82bdade8675, AK ID CO among its states, approved)")
log = (ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
own = next((x for x in log.splitlines() if 'branch prep/preserve-with-park' in x and 'US rules c82bdade8675 -> ' in x), '')
check(bool(own) and 'APPROVED, decided_by KPC owner' in own and 'no need to email them' in own, "this change's changelog line quotes the owner's 1:32 PM words")
print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
