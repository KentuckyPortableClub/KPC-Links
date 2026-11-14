#!/usr/bin/env python3
"""Problem solver says WHY (Nov 10): every unjoined park gets exactly one code, a plain why and a next step; the host check
fails closed. Tiny synthetic rows, a temp folder, offline, nothing written to the repo."""
import json, os, pathlib, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_problem_solver as S

ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)

def park(n='Test Park', t='State Park', **kw):
    p = {'n': n, 't': t, 'm': [], 'g': 'pin', 'c': [], 'bk': [None, None, '', '-', 'nocand']}; p.update(kw); return p

CASES = [
 ('HELD_CHECK', park(c=[['a1', 'Test Park', 5, 'held: far']], held={'why': 'the nearest part is 40 km from the pin', 'ids': ['a1']}), {}),
 ('PERSON_NO', park(c=[['a1', 'Test Park', 5, 'a person said NO to this record (overrides.json no: x)']]), {}),
 ('PERSON_NO', park(), {'override': {'none': True}}),
 ('BORDER', park(), {'states': ['US-KY', 'US-TN'], 'state': 'US-KY'}),
 ('BORDER', park(), {'states': ['US-KY'], 'state': 'US-KY', 'joined_in': {'US-TN'}}),
 ('SHARED_RECORD', park(c=[['a1', 'Other Park', 5, 'record also joined to US-1 whose kind it names']]), {}),
 ('PIN_FAR_SAME_NAME', park(c=[['a1', 'Test Park', 5, 'same name far from the pin, no join at the pin']]), {}),
 ('NAME_ALIAS', park(c=[['a1', 'Testing Area', 5, 'similar name']]), {}),
 ('NAME_ALIAS', park(a=[['a1', 'Big Pine Preserve', 5, 'the POTA pin is inside it (different name)']]), {'wwff_name': 'Big Pine'}),
 ('LINEAR', park(n='Long Path', t='National Scenic Trail'), {}),
 ('LINEAR', park(n='Red River Byway'), {}),
 ('POINT_FEATURE', park(n='Old Mill Historic Site'), {}),
 ('POINT_FEATURE', park(n='Salt Lighthouse', t='State Park'), {}),
 ('SUB_UNIT_OF_BROADER', park(a=[['a1', 'Big Forest', 900, 'the POTA pin is inside it (different name)']]), {}),
 ('LAYER_GAP', park(), {'has_layer': False}),
 ('LAYER_GAP', park(), {'has_layer': True, 'saved_n': 150, 'expected_n': 1000}),
 ('LAYER_GAP', park(bk=['x1', None, '', '-', 'noshape']), {}),
 ('UNKNOWN', park(c=[['a1', 'Elsewhere', 5, 'same name, different kind of place']]), {}),
]
for want, p, ctx in CASES:
    code, why, nxt = S.why_code('US-1', p, ctx)
    check(code == want and len(why) > 10 and len(nxt) > 10 and '\n' not in why, f'{want}: {why[:70]}')
# order: first match wins (held beats a person's NO and a border listing)
c, _, _ = S.why_code('US-1', park(held={'why': 'x'}, c=[['a', 'T', 1, 'a person said NO to this record']]), {'states': ['US-KY', 'US-TN'], 'state': 'US-KY'})
check(c == 'HELD_CHECK', 'held beats NO and border')
c, _, _ = S.why_code('US-1', park(n='Old Trail Historic Site'), {})
check(c == 'LINEAR', 'linear is tested before point feature')
c, w, _ = S.why_code('US-1', park(n='X'), {'has_layer': False})
check('no agency layer' in w, 'LAYER_GAP names the true cause (no layer listed)')
# the WWFF evidence is named in the why, and an alias is only suggested
c, w, n = S.why_code('US-1', park(c=[['a1', 'Big Pine Preserve', 5, 'similar name']]), {'wwff_name': 'Big Pine'})
check(c == 'NAME_ALIAS' and 'WWFF' in w and 'approve' in n and 'automatically' in n, 'NAME_ALIAS cites the WWFF name and only suggests')
# a joined park gets no row; a grade-pin park does
files = {'KY': {'US-1': park(m=[['a', 'Test Park', 5, 'name']], g='official'), 'US-2': park(m=[['a', 'Test Park', 5, 'name']], g='pin'), 'US-3': park()}}
rows = S.why_rows(files, {}, ROOT, {'DATA': '/nonexistent'}, None)
check(sorted(r['ref'] for r in rows) == ['US-2', 'US-3'] and all(set(r) == {'ref', 'state', 'name', 'code', 'why', 'next_step'} for r in rows), 'one row per unjoined park (no joined ones), the six fields')
# the output file keeps every old field and gains why / why_counts; it writes only where OUT says
tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-why-'))
(tmp / 'data/us-key').mkdir(parents=True)
json.dump({'parks': {'US-9': park(held={'why': 'far', 'ids': ['a1']}, c=[['a1', 'Test Park', 5, 'held: far']]), 'US-8': park()}}, open(tmp / 'data/us-key/US-KY.json', 'w'))
S.run({'OUT': str(tmp / 'o'), 'DATA': '/nonexistent', 'PARKINFO': str(tmp / 'none')}, root=tmp)
d = json.load(open(tmp / 'o.json'))
check({'about', 'counts', 'parks', 'why', 'why_counts'} <= set(d) and d['why_counts'] == {'HELD_CHECK': 1, 'LAYER_GAP': 1}, f"json keeps about / counts / parks and adds why: {d['why_counts']}")
check('Count by code' in (tmp / 'o.md').read_text(encoding='utf-8'), 'the text report has the count-by-code line')
# host check: the guard decides; a missing guard fails closed
check(S.host_allowed('https://example.org/x')[0] and not S.host_allowed('https://services1.arcgis.com/a')[0] and not S.host_allowed('https://ncnhde.natureserve.org/a')[0]
      and S.host_allowed('https://apps.fs.usda.gov/a')[0],   # KPC owner, 2026-11-13: apps.fs.usda.gov allowed (slow host)
      'host_allowed follows kpc_net_guard')
real = sys.modules.pop('kpc_net_guard', None); sys.modules['kpc_net_guard'] = None   # makes the import fail
check(S.host_allowed('https://example.org/x')[0] is False, 'guard missing -> not allowed (fail closed)')
sys.modules.pop('kpc_net_guard', None)
if real: sys.modules['kpc_net_guard'] = real
check('HOLD_HOST' not in open(S.__file__, encoding='utf-8').read(), 'the short own host list is gone')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
