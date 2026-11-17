#!/usr/bin/env python3
"""Handoff 8 fix 3 (switch KPC_G8_OTHER_PLACE): in rule R-G8 a school, college, city, county, town, cemetery, church or airport is
another kind of place, unless the park's own name has the word or the record holds the park's full name. Real park and record
names from the offline runs of Oregon, California and Michigan (Nov 17). The offline before / after is in the pull request.
Run:  python3 tests/test_h8_other_place_nov17.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)
for ref, park, rec, word in (('US-2859', 'Tumalo State Park', 'Tumalo Community School', 'school'),
                             ('US-9149', 'Ontario State Recreation Area', 'Ontario High School', 'school'),
                             ('US-3445', 'Huntington State Beach', 'Huntington City Beach', 'city')):
    check(KR.other_place_word(park, rec) == word, f'MUST lose: {ref} {park} / {rec!r} = another kind of place (a {word})')
for ref, park, rec in (('US-3332', 'Watkins Lake State Park', 'Watkins Lake State Park and County Preserve'),
                       ('-', 'Cass County State Forest', 'Cass County Forest'),
                       ('-', 'Church Hill State Park', 'Church Hill'),
                       ('-', 'Tumalo State Park', 'Tumalo'),
                       ('-', 'Townsend State Park', 'Townsend')):
    check(KR.other_place_word(park, rec) == '', f'must NOT: {ref} {park} keeps {rec!r}')
check(KR.other_place_word('Oak Grove State Park', 'Oak Grove Cemetery') == 'cemetery' and KR.other_place_word('Fairport Harbor State Park', 'Fairport Harbor Beach') == '',
      "whole words only ('Fairport' is not 'airport')")
check(not KR.on('KPC_G8_OTHER_PLACE', {}), 'the switch is OFF unless set')
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
check("KR.other_place_word(p.get('n') or '', x[1]) if _kr('KPC_G8_OTHER_PLACE')" in src, 'R-G8 in kpc_us_key.py asks this rule, behind its switch')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
