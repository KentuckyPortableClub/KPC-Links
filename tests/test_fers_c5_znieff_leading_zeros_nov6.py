#!/usr/bin/env python3
"""Part A Quality v3 should-fix (Nov 6): C5 _R18_NO must not treat ZNIEFF registry numbers or leading-zero
equals as piece clashes. Cases: FR-5453, FR-11445, FR-7968, FR-8493, US-8745, US-8784.
Also: '5 Reserve' strip is AU-only (kpc_number_rules)."""
import json, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
import kpc_precheck as P
import kpc_number_rules as KN

ok = True
def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)

# --- C5 ZNIEFF / leading zeros (real key names where present) ---
fr = json.load(open(HERE / 'data/world-key/FR.json'))['parks']
for ref in ('FR-5453', 'FR-11445', 'FR-7968', 'FR-8493'):
    p = fr[ref]
    for m in p.get('m') or []:
        w = P.rule18_differs(p['n'], m[1], False)
        check(w == '', f'{ref}: no C5 false refusal vs {m[1][:50]!r} (got {w!r})')

us_pa = json.load(open(HERE / 'data/us-key/US-PA.json'))['parks']
for ref, bad_rec in (('US-8745', 'State Game Land #46'), ('US-8784', 'State Game Land #85')):
    p = us_pa[ref]
    w = P.rule18_differs(p['n'], bad_rec, False)
    check(w == '', f'{ref} {p["n"]!r} vs {bad_rec!r}: leading-zero equals pass (got {w!r})')
    # still flags a real one-side No.
check('No.' in (P.rule18_differs('Fish Lake No. 1', 'Fish Lake', False) or KN.why('Fish Lake No. 1', 'Fish Lake') or ''),
      'real one-side No. 1 still refuses')

# --- AU-only '5 Reserve' strip ---
check(KN.one_side('Wellington Discovery Forest 5 Reserve', 'Wellington Discovery Forest', cc='AU') == [],
      "AU: '5 Reserve' strip lets AU-3037-style names pass")
check(KN.one_side('Wellington Discovery Forest 5 Reserve', 'Wellington Discovery Forest', cc='AU-WA') == [],
      "AU-WA: '5 Reserve' strip applies")
# Non-AU: the bare '5' is a piece number (Quality: strip must NOT apply worldwide)
check(KN.one_side('Greenwood 5 Reserve', 'Greenwood Reserve', cc='US') == ['5'] or
      KN.one_side('Greenwood 5 Reserve', 'Greenwood', cc='FR') == ['5'],
      "non-AU: '5 Reserve' is NOT stripped (5 stays a piece)")
check(KN.one_side('Greenwood 5 Reserve', 'Greenwood Reserve', cc=None) == ['5'],
      "cc=None: '5 Reserve' is NOT stripped (safe default)")

print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
