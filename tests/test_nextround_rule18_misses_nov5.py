#!/usr/bin/env python3
"""Next round C5 (Nov 5; Brandon's yes relayed via Super; Quality's r18 probe in the fix-bundle-2 grade): three rule-18 misses in
kpc_precheck.rule18_differs: a bracketed '(No.2)' was dropped (CA-3900), 'No. 1' on one side only passed, two different Natura/FFH
site codes passed. Each is now a review-pile flag (never a hold). kpc_precheck.py is not a rule file: no rules hash moves.
Run: python3 -B tests/test_nextround_rule18_misses_nov5.py"""
import pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
import kpc_precheck as P, kpc_key_freeze as KF
ok = True
def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)
FLAG = [("Nisga'a Memorial Lava Bed Corridor Protected Area", "NISGA'A MEMORIAL LAVA BED CORRIDOR PROTECTED AREA (No.2)", 'No. 2'),
        ('Fish Lake No. 1', 'Fish Lake', 'No. 1'), ('Fish Lake', 'Fish Lake (No. 3)', 'No. 3'), ('Lac Vert nº 4', 'Lac Vert', 'No. 4'),
        ('Rhinau Natura 2000 FR4201797', 'Rhinau Natura 2000 FR4211810', 'FR4201797 vs FR4211810'),
        ('DE-0095 FFH 5131-301', 'FFH 5131-302', '5131-301 vs 5131-302'),
        ('Fish Lake No. 1 State Forest', 'Fish Lake No. 2 State Forest', 'number 1 vs 2')]
PASSES = [('Banks Island No. 1 Migratory Bird Sanctuary', 'Banks Island No. 1 Migratory Bird Sanctuary'), ('Rhinau FR4201797', 'Rhinau'),
          ('Tiefer-Wald Natura 2000', 'Tiefer-Wald'), ('9 Mile Canyon', 'Nine Mile Canyon'), ('Area #3', 'Area 3'), ('Lake No Name', 'Lake No Name'),
          ('Rhinau FR4201797', 'Rhinau Natura 2000 FR4201797'), ('Lewis Creek (Lewis County)', 'Lewis Creek'),
          ('Terril de la cite n9 d’Annequin Biological Reserve', 'Terril de la cité n°9 d’Annequin')]   # v3: FR-5508, 'n9' = 'n°9'
for a, b, want in FLAG:
    for br in (False, True):
        w = P.rule18_differs(a, b, br)
        # v2 re-cut: stacked with v2 C10 (kpc_key_rules.piece_ok, one-side number) the same pair is flagged first by C10's wording
        check((w.startswith('rule 18') and want in w) or ('in one name only' in w and w.endswith('(rule 18)')), f'{a!r} vs {b!r} (brackets={br}): flagged ({w})')
for a, b in PASSES:
    check(P.rule18_differs(a, b, False) == '', f'{a!r} vs {b!r}: still passes')
w = P.rule18_differs('Deep Lead Nature Conservation Reserve (No. 2)', 'Deep Lead Nature Conservation Reserve (No. 1)', False)
check('both names carry a different bracketed piece' in w, f'both-bracket clash keeps its own wording ({w})')
check(P.rule18_differs('Langres Nord', 'Langres (secteur Nord)', False).startswith('rule 18'), 'links-11 bracket case unchanged')
check('kpc_precheck.py' not in ' '.join(sum(KF.RULE_FILES.values(), [])) if isinstance(next(iter(KF.RULE_FILES.values())), list) else 'kpc_precheck.py' not in str(KF.RULE_FILES), 'kpc_precheck.py is not a rule file')
# kpc_precheck.py is in no key's rule files, so this patch moves no rules hash (checked by file, not by value: next round C7, a
# separate patch, moves the world hash on purpose)
# v2 re-cut (Nov 5): by file only, no pinned values, so the test also holds when another patch in the stack (v2 C10, the
# one-side-number rule in kpc_key_rules.py) moves the US hash on purpose
check(not any('kpc_precheck' in f for fs in KF.RULE_FILES.values() for f in fs) and 'kpc_precheck.py' not in str(getattr(KF, 'FACTS', '')),
      'no rules hash moves (kpc_precheck.py is not a rule file)')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
