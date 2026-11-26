#!/usr/bin/env python3
"""26 Nov 2026 (KPC owner 2:54 PM: 'Fix as in this will not happen anywhere else either'; Fable's review finding 1). The MN test
key put 16 state forests on another forest's land: the website key's row 'sgmnb14' (Northwest Angle) followed the saved copy's
row 14 (Big Fork) to Big Fork's fresh record. An old number never crosses alone now: the row's own name (unnamed: its size) must
fit the fresh record, in the carry AND in the gate, for every layer. Invented records shaped like the real MN rows.
Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import gzip, json, os, pathlib, re, sys

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


src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
ns = {'os': os, 're': re, 'json': json, 'gzip': gzip, 'math': __import__('math'), 'KR': KR, 'MC': MC, 'SL': SL, 'notice': lambda *a: None}
exec(src[src.index('def _oid(a)'):src.index('\n', src.index('def _oid(a)'))], ns)
exec(src[src.index('RA_USED = {}'):src.index('\ndef _maiden6')], ns)
fits, fop = ns['carry_fits'], ns['fresh_old_parks']

big_fork = {'OBJECTID': 'sgmnb6', 'Unit_Nm': 'Big Fork', 'GIS_Acres': 127933, '_fresh': True}
nw_angle = {'OBJECTID': 'sgmnb36', 'Unit_Nm': 'Northwest Angle', 'GIS_Acres': 144415, '_fresh': True}
lost_river = {'OBJECTID': 'sgmnb57', 'Unit_Nm': 'Lost River', 'GIS_Acres': 54755, '_fresh': True}
remer = {'OBJECTID': 'sgmnb42', 'Unit_Nm': 'Remer', 'GIS_Acres': 12851, '_fresh': True}
pad = {'OBJECTID': 207836, 'Unit_Nm': 'Northwest Angle State Forest', 'GIS_Acres': 14158, '_fresh': True}
parcel = {'OBJECTID': 'sgzzz77', 'Unit_Nm': '', 'GIS_Acres': 40.2, '_fresh': True}
hint = {'OBJECTID': 'sgmnb37~old', 'Unit_Nm': 'Big Fork', 'GIS_Acres': 127000, '_hint': True}

check('the row name fits its own record (spelling aside; one name holding the other)',
      fits(['sgmnb36', 'Northwest Angle', 1], nw_angle) and fits([207836, 'NORTHWEST ANGLE STATE FOREST', 1], pad)
      and fits(['x', 'Northwest Angle', 1], pad))
check("another forest's name never fits ('Northwest Angle' on Big Fork, 'Remer' on Lost River)",
      not fits(['sgmnb14', 'Northwest Angle', 143388], big_fork) and not fits(['sgmnb6', 'Remer', 12851], lost_river))
check('an unnamed row fits only by size within 10%; no size = no fit',
      fits(['sgzzz77', '', 40], parcel) and not fits(['sgzzz77', '', 80], parcel) and not fits(['sgzzz77', ''], parcel)
      and not fits(['sgzzz77', 'Unit 3', 0], parcel))
check("short names never fit by one holding the other ('Remer' is not 'Remer Lake Trail')",
      not fits(['a', 'Remer', 1], {'Unit_Nm': 'Remer Lake Trail'}))

recs = [big_fork, nw_angle, lost_river, remer, pad, hint]
old = {'US-4815': {'n': 'Northwest Angle State Forest', 'm': [['sgmnb14', 'Northwest Angle', 143388, 'reviewed'],
                                                              [207836, 'Northwest Angle State Forest', 14158, 'name']]},
       'US-4821': {'n': 'Remer State Forest', 'm': [['sgmnb6', 'Remer', 12851, 'reviewed']]},
       'US-4784': {'n': 'Big Fork State Forest', 'm': [['sgmnb37', 'Big Fork', 127933, 'name']]}}
# the saved copy's own numbers: its row 14 is Big Fork, its row 6 is Lost River (another day's numbering than the website's)
alias = {'sgmnb14': 'sgmnb6', 'sgmnb6': 'sgmnb57', '207836': '207836'}
ns['CARRY_ST'][0] = 'MN'
new = fop(old, alias, recs)
ids = {r: [str(x[0]) for x in v['m']] for r, v in new.items()}
check(f"Northwest Angle's old row never lands on Big Fork; its PAD-US row stays ({ids['US-4815']})",
      'sgmnb6' not in ids['US-4815'] and '207836' in ids['US-4815'])
check(f"Remer's old row never lands on Lost River ({ids['US-4821']})", 'sgmnb57' not in ids['US-4821'])
check(f"an old row with no proven twin still names its hint ({ids['US-4784']})", ids['US-4784'] == ['sgmnb37~old'])
check('every refused row is listed with its state, park, old id and both names',
      sorted((x[0], x[1], x[2], x[4], x[5]) for x in ns['CARRY_REFUSED'])
      == [('MN', 'US-4815', 'sgmnb14', 'sgmnb6', 'Big Fork'), ('MN', 'US-4821', 'sgmnb6', 'sgmnb57', 'Lost River')])

ns['CARRY_REFUSED'].clear()
new2 = fop({'US-4797': {'n': 'Foot Hills State Forest', 'm': [['sgmnb7', 'Foot Hills', 630, 'reviewed']]}},
           {'x1': 'sgmnb36'}, recs + [{'OBJECTID': 'sgmnb7', 'Unit_Nm': 'Birch Lakes', 'GIS_Acres': 630, '_fresh': True}])
check(f"an old number with no proven twin that a fresh record now carries never names it, even with the same size ({new2['US-4797']['m']})",
      new2['US-4797']['m'] == [] and ns['CARRY_REFUSED'][0][2] == 'sgmnb7')
gate = src[src.index('def proven_only_gate') if 'def proven_only_gate' in src else src.index("fresh_on = _kr('KPC_STORE_FRESH')"):]
check('the gate checks every drawn fresh row with the same test, whatever proved the park',
      "elif fresh_on and rec is not None and rec.get('_fresh') and not carry_fits(q, rec):" in src)
check('the PC test gets the refused rows as a list and a count',
      "'KPC_CARRY_LIST'" in src and 'old rows not carried because their name does not fit' in src)
check('two records under one key never share a cached view',
      SL.cached_view('k1', {'Unit_Nm': 'A'})['names'] != SL.cached_view('k1', {'Unit_Nm': 'B'})['names'])

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
