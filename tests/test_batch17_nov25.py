#!/usr/bin/env python3
"""25 Nov 2026, batch 17 (the owner's 5:43 PM NY test, parks that lost their outline; invented records only).
  1  a shape too thin to measure against another read is 'can't tell' (US-10040 Old Croton Aqueduct, ~20 m wide): name + size decides
  2  R3b: two name + size fits that are ONE land (proven to each other, boxes 80% the same) are one answer (US-0481 Wertheim NWR)
  3  the two-sources sum counts one source's records on the same ground once (US-2071 Helen L. McNitt State Park)
Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import gzip, json, math, os, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_same_land as SL  # noqa: E402
import kpc_key_rules as KR  # noqa: E402
import kpc_match_checks as MC  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


def strip(x0, y0, dx, dy, n=40):
    """A long thin strip from (x0, y0), n segments, about dy degrees wide."""
    top = [[x0 + dx * i / n, y0 + dy] for i in range(n + 1)]
    bot = [[x0 + dx * i / n, y0] for i in range(n, -1, -1)]
    return [top + bot + [top[0]]]


# ---- 1 ----
old = {'Unit_Nm': 'Old Croton Aqueduct State Historic Park', 'GIS_Acres': 196, '_g': {'rings': strip(-73.9, 41.0, 0.3, 0.0005)}}
new = {'_nm': 'Old Croton Aqueduct State Historic Park', '_ac': 196, '_g': {'rings': strip(-73.9, 41.0003, 0.3, 0.0002)}}
w_old, w_new = SL.mean_width_m(SL.view(old)['rings']), SL.mean_width_m(SL.view(new)['rings'])
check(f'1: a strip {round(w_new)} m wide is too thin to measure: name + size decides ({SL.prove(old, new)})',
      w_new < SL.THIN_M and SL.view(new)['coarse'] and SL.prove(old, new)[0] == 'name_size')
sq = lambda x, y, d: {'rings': [[[x, y], [x + d, y], [x + d, y + d], [x, y + d], [x, y]]]}
check('1: a wide record is still measured (a square kilometre is not thin)', not SL.view({'Unit_Nm': 'X', '_g': sq(-90, 40, 0.012)})['coarse'])
check('1: a thin strip with ANOTHER name is still not proven', SL.prove(old, dict(new, _nm='Croton Gorge Unique Area'))[0] is None)

# ---- 2 ----
a = {'Unit_Nm': 'Wertheim National Wildlife Refuge', 'GIS_Acres': 2671, '_bb': [-72.9, 40.78, -72.85, 40.82]}
b1 = {'_nm': 'Wertheim National Wildlife Refuge', '_ac': 2671, '_bx': [-72.9, 40.78, -72.85, 40.82]}
b2 = {'_nm': 'Wertheim National Wildlife Refuge', '_ac': 2657, '_bx': [-72.9, 40.781, -72.851, 40.82]}
k, lv, note = SL.pick(a, {'5426': b1, '4468': b2}, own='4468')
check(f'2: two fits that are one land (PAD-US holds the refuge twice): the closest size, never the number ({k}, {note})',
      k == '5426' and lv == 'name_size' and 'one land' in note)
b3 = dict(b2, _bx=[-72.875, 40.80, -72.825, 40.84])   # the same name and size, a quarter of the box apart: two lands
check('2: two fits on different boxes stay two fits (not proven)', SL.pick(a, {'5426': b1, '9': b3})[0] is None)

# ---- 3 ----
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
ns = {'os': os, 're': re, 'json': json, 'gzip': gzip, 'math': math, 'KR': KR, 'MC': MC, 'SL': SL, 'notice': lambda *a: None}
exec(src[src.index('def _oid(a)'):src.index('\n', src.index('def _oid(a)'))], ns)
exec(src[src.index('RA_USED = {}'):src.index('\ndef _maiden6')], ns)
ns['_sl_layer'] = lambda i: re.match(r'[a-z]*', str(i)).group(0) or 'padus'
bx = [-74.38, 42.72, -74.36, 42.74]
byid = {'8850': {'Unit_Nm': 'Helen L. Mcnitt', 'Loc_Nm': 'Helen L. McNitt', 'GIS_Acres': 143, '_bb': bx, '_fresh': True},
        '237438': {'Unit_Nm': 'Helen L. McNitt State Park', 'Loc_Nm': '', 'GIS_Acres': 135, '_bb': [-74.3799, 42.7201, -74.3601, 42.7399], '_fresh': True},
        'sgzzb314': {'Unit_Nm': 'Helen L. McNitt', 'Loc_Nm': 'Helen L. McNitt State Park', 'GIS_Acres': 67, '_bb': [-74.38, 42.72, -74.37, 42.73], '_fresh': True},
        'sgzzb315': {'Unit_Nm': 'Helen L. McNitt', 'Loc_Nm': 'Helen L. McNitt State Park', 'GIS_Acres': 59, '_bb': [-74.37, 42.72, -74.36, 42.73], '_fresh': True},
        'sgzzb316': {'Unit_Nm': 'Helen L. McNitt', 'Loc_Nm': 'Helen L. McNitt State Park', 'GIS_Acres': 8, '_bb': [-74.37, 42.73, -74.36, 42.74], '_fresh': True}}
p = {'n': 'Helen L. McNitt State Park', 't': 'State Park', 'm': [[k_, v['Unit_Nm'], v['GIS_Acres'], 'name'] for k_, v in byid.items()]}
r = ns['_name_proofs']('US-9071', p, byid, None, p['n'], p['t'], True)
check(f'3: PAD-US twice on one box (143 and 135) is counted once against NY State Parks 67 + 59 + 8 ({r})',
      r[1] == 'ok' and 'two official sources' in r[0] and '143' in r[0])

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
