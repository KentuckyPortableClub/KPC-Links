#!/usr/bin/env python3
"""Fixes from Sonnet's grade of the whole-US rebuild (HQ 2026-11-18)."""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_key_rules as KR
bad = 0
def ck(c, m):
    global bad; bad += not c; print(('PASS ' if c else 'FAIL ') + m)
ck(KR.contest('Mount Tom State Reservation', {'US-8417': ('Mount Tom State Reserve', 'State Reserve'), 'US-11476': ('Mt. Tom Wildlife Management Area', 'Wildlife Management Area')}) == ('win', 'US-8417'),
   "a 'State Reservation' record goes to the State RESERVE park, not the WMA next door (MA US-8417)")
ck(KR.other_place_word('Charles D. Kelley Wildlife Management Area', 'Charles D. Kelley Autauga County Wildlife Management Area') == '',
   "R-G8: a county named only as where the WMA lies does not make it a county (AL US-3679)")
ck(KR.other_place_word('Elk Lake Wildlife Management Area', 'Elk Lake County Park') == 'county', 'R-G8: a county park is still another kind of place')
ck(KR.other_place_word('Tumalo State Park', 'Tumalo Community School') == 'school', 'R-G8: a school is still another kind of place')
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
ck("'check (trail): the park is its official trail line" in src and "not any(str(x[3]).startswith('reviewed') for x in m)" in src,
   "a trail park with an official line keeps the line; name-joined pieces go to check, a person's join stays (MN US-9386)")
sz = lambda refs: KR.size_pick(6806, {'US-1940': [10632, 6998, 6953], 'US-7850': [1200, 3400]})
ck(KR.contest('CAESAR CREEK', {'US-1940': ('Caesar Creek State Park', 'State Park'), 'US-7850': ('Caesar Creek Lake State Wildlife Area', 'Wildlife Area')}, None, (), None, sz) == ('win', 'US-1940'),
   "a bare-name copy goes to the park that already holds the same land (6,806 ac beside its own 6,953-ac record: Caesar Creek SP)")
ck(KR.size_pick(100, {'a': [100], 'b': [95]}) is None and KR.size_pick(3, {'a': [3]}) is None, 'two parks that fit, or a tiny piece: a person decides')
ck("p['ac'] > 1.1 * _sum" in src, "a park's union acreage is never shown bigger than its records' own acres added up (Savoy Mountain SF)")
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
