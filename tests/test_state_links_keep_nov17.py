#!/usr/bin/env python3
"""kpc_state_links.keep (KPC owner, 2026-11-17): a park-list row from POTA's export carries no website / activations /
attempts / qsos; a field the row does not carry keeps last week's value, a field POTA sends is taken as sent."""
import pathlib, re
src = (pathlib.Path(__file__).resolve().parents[1] / '.github/scripts/kpc_state_links.py').read_text(encoding='utf-8')
ns = {'re': re, 'clean': lambda v: '' if v in (None, 'None', 'null') else str(v).strip()}
exec(src[src.index('def fixurl'):src.index('def pin_of')], ns)
keep = ns['keep']; o = ['Name', 'https://www.nps.gov/cuva/index.htm', 'National Park', '', '', 41.2, -81.5, 1248, 1315, 37626]
cases = [(keep({}, 'website', o, 1) == o[1], 'no website field: last week\'s website kept'),
         (keep({'website': ''}, 'website', o, 1) == '', 'POTA sends an empty website: taken as sent'),
         (keep({'website': 'parks.idaho.gov'}, 'website', o, 1) == 'https://parks.idaho.gov', 'a sent website is fixed up as before'),
         (keep({}, 'activations', o, 7, int) == 1248, 'no activations field: last week\'s count kept'),
         (keep({'activations': 1300}, 'activations', o, 7, int) == 1300, 'a sent count is taken'),
         (keep({}, 'qsos', None, 9, int) is None and keep({}, 'website', None, 1) == '', 'a new park with no fields: blank, as before')]
bad = 0
for ok, msg in cases:
    print(('PASS ' if ok else 'FAIL ') + msg); bad += not ok
print('ALL PASS' if not bad else 'SOME FAILED'); raise SystemExit(1 if bad else 0)
