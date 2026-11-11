"""KPC owner, 2026-11-10: two parks on the same official records are an approximate 2-fer only when both POTA pins are inside the
shared outline AND the pins are within kpc_fers.SAME_RECORDS_NEAR_KM AND the record names both parks with no kind that differs
(kpc_fers_guard.same_land_doubt), unless the pins are on the same spot (SAME_RECORDS_SPOT_KM). Separate units of one big record
(lake recreation-area units, a park and its 'Unit') are held as likely joins to fix, with the reason. Offline; the fixture names,
records and pins are written here (no bot-written data is read)."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, '.github/scripts'))
import kpc_fers as K
FAILS = []
def check(c, msg):
    print(('PASS ' if c else 'FAIL ') + msg)
    if not c: FAILS.append(msg)

# stand-ins for the Nov 10 list (pins rounded; real distances 0.04, 0.48, 1.72 to 9.4 km)
PIN = {'US-C1': ['Chalk Bluff Battlefield Park Recreation Park', 36.4900, -90.1500], 'US-C2': ['Chalk Bluff State Natural Area', 36.4903, -90.1502],
       'US-R1': ['Red Cliffs Archeological Site BLM Historic Area', 37.2240, -113.4050], 'US-R2': ['Red Cliffs Dinosaur Track Site BLM Historic Area', 37.2205, -113.4020],
       'US-J': ['Jackson on Patoka Lake State Recreation Area', 38.4000, -86.6500], 'US-L': ['Lick Fork on Patoka Lake State Recreation Area', 38.4300, -86.6000],
       'US-S1': ['Siloam Springs State Park', 39.8900, -90.9500], 'US-S2': ['Siloam Springs Buckhorn Unit State Park', 39.9500, -91.0000],
       'US-D': ['Dora-New Holland on Salamonie Lake State Recreation Area', 40.7600, -85.6300], 'US-H': ['Mt Hope on Salamonie Lake State Recreation Area', 40.7650, -85.6100],
       'US-K1': ['Chalk Bluff Battlefield Park Recreation Park', 36.4900, -90.1500], 'US-K2': ['Chalk Bluff State Natural Area', 36.4945, -90.1500]}
REC = {'C': 'Chalk Bluff Natural Area', 'R': 'Red Cliffs Recreation Area', 'J': 'Patoka Lake', 'L': 'Patoka Lake', 'S': 'Siloam Springs State Park',
       'D': 'Salamonie Lake', 'H': 'Salamonie Lake', 'K': 'Chalk Bluff Natural Area'}
parks = {r: {'st': 'US-XX', 'm': [['rec1', REC[r[3]], 0, 'name']]} for r in PIN}
check(K.SAME_RECORDS_NEAR_KM == 1.0 and K.SAME_RECORDS_SPOT_KM == 0.1, 'near limit 1 km (between 0.48 km, the farthest real pair, and 1.72 km, the nearest separate units); same spot 0.1 km')
check(K.shared_record_names(parks, ['US-J', 'US-L']) == ['Patoka Lake'], 'the shared record name is read from the key rows')
real = K.pin_in_outline
try:
    K.pin_in_outline = lambda r, P, G: True   # both pins inside the shared outline
    for a, b, want, what in [('US-C1', 'US-C2', 'approx', 'Chalk Bluff (0.04 km, kinds differ but the same spot): approximate'),
                             ('US-R1', 'US-R2', 'approx', 'Red Cliffs (about 0.47 km, the record names both, no kind differs): approximate'),
                             ('US-J', 'US-L', 'held', 'Patoka Lake units (Jackson / Lick Fork): held'), ('US-S1', 'US-S2', 'held', 'Siloam Springs / Buckhorn Unit: held'),
                             ('US-D', 'US-H', 'held', 'Salamonie Lake units at about 1.8 km: held'),
                             ('US-K1', 'US-K2', 'held', 'kinds differ and the pins 0.5 km apart (not the same spot): held by the same-land test')]:
        v = K.same_records_verdict(parks, [a, b], PIN, {})
        check(v and v[0] == want and (want == 'approx' or (len(v) > 3 and v[2] == 'units' and v[1] == sorted([a, b]) and v[3].startswith('not sure:'))),
              f'{what} ({v[:3]}, {K.pin_km(a, b, PIN):.2f} km)')
    v = K.same_records_verdict(parks, ['US-J', 'US-L'], PIN, {})
    check('more than 1 km apart' in v[3] and 'separate units' in v[3], 'the far-pins reason says separate units and the distance rule')
    check('one record covers two parks' in K.same_records_verdict(parks, ['US-K1', 'US-K2'], PIN, {})[3], 'the near-but-doubtful reason is the same-land test reason')
    row = {'refs': ['US-J', 'US-L'], 'status': 'candidate'}
    held = K.same_records_mark(row, v, parks, PIN)
    check(held and row['status'] == v[3] and row.get('person_review') and row.get('join_check') and row.get('separate_units') == ['US-J', 'US-L']
          and 'pin_outside' not in row and row['pin_km']['US-J+US-L'] > 1.0, 'a held separate-units row has the reason, both parks and their pin distance')
    nopin = dict(PIN, **{'US-L': ['Lick Fork on Patoka Lake State Recreation Area', None, None]})
    check(K.same_records_verdict(parks, ['US-J', 'US-L'], nopin, {})[0] == 'held', 'a pin that cannot be measured is never close: held')
    K.pin_in_outline = lambda r, P, G: r != 'US-C2'
    check(K.same_records_verdict(parks, ['US-C1', 'US-C2'], PIN, {}) == ('held', ['US-C2']), 'a pin outside the outline is still held as before, even when close')
finally: K.pin_in_outline = real
src = open(os.path.join(ROOT, '.github/scripts/kpc_fers.py'), encoding='utf-8').read()
import re
check(len(re.findall(r'(?<!def )same_records_verdict\(parks', src)) == 3 and 'FG.same_land_doubt(' in src[src.index('def same_records_doubt'):src.index('def same_records_verdict')],
      'all three call sites use same_records_verdict, which reuses kpc_fers_guard.same_land_doubt')
print('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})')
sys.exit(1 if FAILS else 0)
