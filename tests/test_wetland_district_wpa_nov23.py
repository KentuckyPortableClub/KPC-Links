#!/usr/bin/env python3
"""W12, 23 Nov 2026 (owner 2:12 PM, approving the outside agent's job 9; 4:43 PM "Do it"): 6 of the 22 Wetland Management
Districts get no tract from the FWS realty copy and stay a pin. They now join the Fish and Wildlife Service's own Waterfowl
Production Area records that HOLD POTA's pin or CARRY the district's place name. A pin inside a separate refuge, a production
area only near the pin, a state tag ('... Of Iowa') or another agency's record joins nothing. Invented records; no network."""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


rec = lambda oid, nm, mang='FWS', ac=900: {'OBJECTID': oid, 'Unit_Nm': nm, 'Mang_Name': mang, 'GIS_Acres': ac}
HOLDS = set()
pick = lambda core, recs, pin=(44.0, -97.0), no=(): KR.district_wpa_picks(core, pin[0], pin[1], recs, lambda a: a['OBJECTID'] in HOLDS,
                                                                         lambda a: a['OBJECTID'] in no)
check('the helper exists', hasattr(KR, 'district_wpa_picks'))
got, _ = pick('Heron Slough', [rec('1', 'Heron Slough Waterfowl Production Area'), rec('2', 'Heron Slough Waterfowl Production Area'),
                               rec('fws9', 'Heron Slough Waterfowl Production Area', ac=850)])
check("a production area carrying the district's name joins, ONE record per name (the FWS realty copy first)",
      [a['OBJECTID'] for a in got] == ['fws9'])
HOLDS.add('7')
got, _ = pick('Funk', [rec('7', 'Phelps County Waterfowl Production Area'), rec('8', 'Kearney County Waterfowl Production Area')])
check('a production area that holds the pin joins; one only near the pin does not (it may be another district\'s)',
      [a['OBJECTID'] for a in got] == ['7'])
HOLDS.clear(); HOLDS.add('r1')
got, _ = pick('Iowa', [rec('r1', 'Otter Slough National Wildlife Refuge'), rec('3', 'Clay County Waterfowl Production Area Of Iowa')])
check("a pin inside a separate refuge, and a state tag at the end of a name ('... Of Iowa'), join nothing", got == [])
HOLDS.clear()
got, _ = pick('Willow Lake', [rec('4', 'Willow Lake Waterfowl Production Area', mang='SDGFP'), rec('5', 'Willow Lake State Game Production Area', mang='FWS')])
check("another agency's production area, or a record that is not a production area, joins nothing", got == [])
got, n = pick('Heron Slough', [rec('6', 'Heron Slough Waterfowl Production Area')], no=('6',))
check("a person's no holds, and is counted", got == [] and n == 1)
got, _ = pick('Heron Slough', [rec('fws11', 'Heron Slough WPA')], pin=(None, None))
check('a park with no pin still joins by its name', [a['OBJECTID'] for a in got] == ['fws11'])
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
check('the builder uses it for the districts the realty copy left as a pin', 'KR.district_wpa_picks(core' in src and 'W12: the district' in src)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
