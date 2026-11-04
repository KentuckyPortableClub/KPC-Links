#!/usr/bin/env python3
"""Offline test for links-09 (Nov 4 2026): .github/scripts/kpc_precheck.py ignores bracket qualifiers in its GENERAL rule 18 piece test
and name test; the bad-pin name test still counts them. Rule 18 v5 (Brandon, Super Head Bot chat, 7:43 PM CST Nov 3, relayed via
Super Head Bot: "Yes"; relayed (paraphrase of the question he answered Yes to): bracket qualifiers do not count; one-side compass
words in English or French do). No network, no data."""
import pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
import kpc_precheck as PC  # noqa: E402
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


G = lambda a, b: PC.rule18_differs(a, b, False)   # noqa: E731  the general test (RULE18_PIECE / review pile)
BP = lambda a, b: PC.rule18_differs(a, b, True)   # noqa: E731  the bad-pin name test
check(PC.unbracket('Dunbar Cave (Lower Tract)') == 'Dunbar Cave' and PC.unbracket('Foo [Bar] (Baz) Lake') == 'Foo Lake' and PC.unbracket('(Lower Tract)') == '',
      'unbracket() takes off (...) and [...] qualifiers')
# general test: bracket qualifiers no longer count
for a, b in (('Dunbar Cave (Lower Tract)', 'Dunbar Cave'), ('Dunbar Cave State Natural Area (Lower Tract)', 'Dunbar Cave State Natural Area'),
             ('Bonaventure (South)', 'Bonaventure'), ('Riviere Bonaventure (Ouest)', 'Riviere Bonaventure'), ('Foo Lake (Lewis County)', 'Foo Lake'),
             ('Foo (CNC/Stallman)', 'Foo'), ('Foo Lake (Lewis County)', 'Foo Lake (Qld)'), ('Foo', 'Foo (Unit 2)')):
    check(G(a, b) == '', f"general test: {a!r} vs {b!r} -> '' (a bracket qualifier does not count): {G(a, b)!r}")
# general test: the same words OUTSIDE brackets still count (one-side compass words in English or French, pieces, numbers)
for a, b, want in (('Lower Tract Foo', 'Foo', "piece 'lower'"), ('Bonaventure South', 'Bonaventure', "'south' names only one piece"),
                   ('Riviere Bonaventure Ouest', 'Riviere Bonaventure', "'ouest' names only one piece"), ('North Fork Foo', 'South Fork Foo', "'north' vs 'south'"),
                   ('Foo Unit 2', 'Foo Unit 3', "piece '2'"), ('Foo Unit 2 (Lower Tract)', 'Foo Unit 3', "piece '2'")):
    check(want in G(a, b), f'general test: {a!r} vs {b!r} still flagged outside brackets: {G(a, b)!r}')
# general test (links-11, Quality v2 should-fix 3): a compass word one name has outside brackets and the other ONLY inside its bracket
# ('Langres Nord' vs 'Langres (secteur Nord)') is a review-pile flag that names the bracket, not a silent pass
for a, b, want in (('Marais tufeux du plateau de Langres Nord', 'Marais tufeux du plateau de Langres (secteur Nord)', "'nord'"),
                   ('Papa Westray North Hill', 'Papa Westray (North Hill and Holm)', "'north'"), ('Gerang Gerung South', 'Gerang Gerung (south) F.R', "'south'"),
                   ('Langres (secteur Nord)', 'Langres Nord', "'nord'")):
    check(want in G(a, b) and "only inside the other name's bracket" in G(a, b), f"general test: {a!r} vs {b!r} -> flagged (word only inside the other bracket): {G(a, b)!r}")
# general test: BOTH names carry clashing bracket pieces = different pieces, kept as a flag (not a one-side qualifier)
for a, b, want in (('Foo River (North)', 'Foo River (South)', "'north' vs 'south'"), ('Horseshoe Canyon (South) BLM Wilderness Area', 'Horseshoe Canyon (North)', "'south' vs 'north'"),
                   ('Deep Lead Nature Conservation Reserve (No. 2)', 'Deep Lead Nature Conservation Reserve (No. 1)', 'number 2 vs 1'),
                   ('NTWA Bushland covenant (0130) Reserve', 'NTWA Bushland covenant (0189)', 'number 130 vs 189')):
    check(want in G(a, b) and 'both names carry a different bracketed piece' in G(a, b), f'general test: a clash inside BOTH names\' brackets is still flagged: {a!r} vs {b!r}: {G(a, b)!r}')
# bad-pin test: unchanged, bracket qualifiers still count
for a, b, want in (('Dunbar Cave (Lower Tract)', 'Dunbar Cave', "piece 'lower'"), ('Bonaventure (South)', 'Bonaventure', "'south' names only one piece"),
                   ('Foo (CNC/Stallman)', 'Foo', "qualifier (CNC/Stallman)"), ('Foo Lake (Lewis County)', 'Foo Lake', 'qualifier (Lewis County)')):
    check(want in BP(a, b), f'bad-pin test still counts the bracket: {a!r} vs {b!r}: {BP(a, b)!r}')
check(PC.name_how('Bonaventure (South)', 'Bonaventure', r18=True) == 'other' and PC.name_how('Foo (CNC/Stallman)', 'Foo', r18=True) == 'other',
      "bad-pin name test (name_how r18=True) unchanged: a bracketed qualifier the record lacks = 'other'")
# general name test: the better of the full names and the names without brackets
check(PC.name_how_general('Dunbar Cave (Lower Tract)', 'Dunbar Cave') == 'same' and PC.name_how_general('Foo Lake', 'Bar Hill') == 'other',
      'name_how_general: bracket text never makes a name test worse; an unrelated name is still other')
real = PC.name_how
try:
    PC.name_how = lambda a, b, r18=False: 'same' if '(' not in a + b else 'other'
    check(PC.name_how_general('Foo (Lower Tract)', 'Foo') == 'same', "name_how_general takes the unbracketed answer when it is better ('other' -> 'same')")
    PC.name_how = lambda a, b, r18=False: 'spelling' if '(' not in a + b else 'same'
    check(PC.name_how_general('Foo (Lower Tract)', 'Foo') == 'same', 'name_how_general keeps the full-name answer when that is better')
finally:
    PC.name_how = real
src = (HERE / '.github/scripts/kpc_precheck.py').read_text()
check("name_how_general(p.get('n') or '', x[1])" in src and "rule18_differs(p.get('n') or '', x[1], False)" in src and 'rule18_differs(park, rec, True)' in src
      and "rule18_differs(pota_name or '', x[1], True)" in src, 'wiring: the general test uses brackets off; the bad-pin test (name_how r18 + name_area_backs) keeps brackets=True')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
