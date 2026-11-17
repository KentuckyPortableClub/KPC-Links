#!/usr/bin/env python3
"""The contest (matching plan section 1; owner YES 17 Nov): a record shared by two or more parks goes to the park it fits best.
Real cases from hole2-shared-records.csv. Run: python3 tests/test_key_contest_nov17.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import ast, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8'); ns = {'re': re}
for n in ast.parse(src).body:
    if (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {'GEN', 'ABBR', 'NOTNAME'} for t in n.targets)) or (isinstance(n, ast.FunctionDef) and n.name == 'norm'):
        exec(compile(ast.Module([n], []), 'x', 'exec'), ns)
norm = ns['norm']
R = []
def check(ok, what): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + what)
def C(rec, parks, lk=()): return KR.contest(rec, parks, norm, lk)
SP, SF = ('Scioto Trail State Park', 'State Park'), ('Scioto Trail State Forest', 'State Forest')
check(C('Scioto Trail SF', {'US-1990': SP, 'US-5448': SF}) == ('win', 'US-5448'), "'Scioto Trail SF' goes to the State Forest")
check(C('Scioto Trail SP', {'US-1990': SP, 'US-5448': SF}) == ('win', 'US-1990'), "'Scioto Trail SP' goes to the State Park")
check(C('Salt Fork WA', {'US-1989': ('Salt Fork State Park', 'State Park'), 'US-9499': ('Salt Fork State Wildlife Area', 'State Wildlife Area')}) == ('win', 'US-9499'), "'Salt Fork WA' goes to the Wildlife Area")
check(C('Susquehanna Sp', {'US-0335': ('Susquehanna National Wildlife Refuge', 'National Wildlife Refuge'), 'US-1601': ('Susquehanna State Park', 'State Park')}) == ('win', 'US-1601'), "'Susquehanna Sp' leaves the refuge")
check(C('Will Rogers SHP', {'US-3594': ('Will Rogers State Beach', 'State Beach'), 'US-3595': ('Will Rogers State Historical Park', 'State Historical Park')}) == ('win', 'US-3595'), "'Will Rogers SHP' goes to the Historical Park")
check(C('Monterey SB', {'US-3476': ('Monterey State Historical Park', 'State Historical Park'), 'US-3477': ('Monterey State Beach', 'State Beach')}) == ('win', 'US-3477'), "'Monterey SB' goes to the Beach")
check(C('Alexandria SRA', {'US-13536': ('Alexandria Wildlife Management Area', 'Wildlife Management Area'), 'US-5659': ('Alexandria Lakes State Recreation Area', 'State Recreation Area')}) == ('win', 'US-5659'), "'Alexandria SRA' goes to Alexandria LAKES SRA (kind first, not place words)")
check(C('Montague Plains WMA', {'US-11472': ('Montague Plains Wildlife Management Area', 'Wildlife Management Area'), 'US-11473': ('Montague Wildlife Management Area', 'Wildlife Management Area')}) == ('win', 'US-11472'), 'two parks of the same kind: the place words decide')
check(C('White River Marsh Wildlife Area', {'US-11936': ('White River State Fish and Wildlife Area', 'State Fish and Wildlife Area'), 'US-4341': ('White River Marsh State Wildlife Area', 'State Wildlife Area')}) == ('win', 'US-4341'), 'White River Marsh (333 parcels) goes to the Marsh area')
check(C('Prentice Cooper State Forest & Wildlife Management Area', {'US-3971': ('Prentice Cooper Wildlife Management Area', 'Wildlife Management Area'), 'US-5499': ('Prentice Cooper State Forest', 'State Forest')}) == ('both', None), "a record naming both kinds stays on both ('same land, two park numbers')")
check(C('Big Lake', {'US-0163': ('Big Lake National Wildlife Refuge', 'National Wildlife Refuge'), 'US-7265': ('Big Lake Wildlife Management Area', 'Wildlife Management Area')})[0] == 'person', "'Big Lake' (bare name) goes to a person")
check(C('Browns Park', {'US-0223': ('Browns Park National Wildlife Refuge', 'National Wildlife Refuge'), 'US-9625': ('Browns Park State Wildlife Area', 'State Wildlife Area')})[0] == 'person', "'Browns Park' goes to a person")
check(C('Kirkpatrick Basin Wildlife Management Area', {'US-13614': ('Kirkpatrick Basin North Wildlife Management Area', 'Wildlife Management Area'), 'US-13615': ('Kirkpatrick Basin South Wildlife Management Area', 'Wildlife Management Area')})[0] == 'person', 'North or South: a person')
check(C('Blue Rock', {'US-1936': ('Blue Rock State Park', 'State Park'), 'US-5436': ('Blue Rock State Forest', 'State Forest')}, lk=('sf',)) == ('win', 'US-5436'), "a bare name from a state FOREST layer goes to the State Forest (the layer's kind)")
check(C('Mohican State Park', {'US-1977': ('Mohican State Park', 'State Park'), 'US-5444': ('Mohican-Memorial State Forest', 'State Forest')}) == ('win', 'US-1977'), 'full name first (D9)')
check(C('North Platte National Wildlife Refuge', {'US-0445': ('North Platte National Wildlife Refuge', 'National Wildlife Refuge'), 'US-13433': ('North Platte National Wildlife Refuge', 'National Wildlife Refuge')}) == ('both', None), 'two POTA numbers with the same name keep the record (same land, two park numbers; NE proof)')
check(KR.type_words('Cooper Lake SP - Doctors Creek Unit') == {'park'} and KR.type_words('Buffalo Bill Ranch SRA') == {'recreation'}, 'short forms are read')
i0 = src.index('# THE CONTEST (matching plan section 1'); blk = src[i0:i0 + 6000]; pre = src[i0 - 2500:i0]
check("if _kr('KPC_ONE_RECORD_ONE_PARK'):" in pre and 'KR.contest(' in blk and src[src.rfind('\n', 0, i0) + 1:i0] == ' ' * 12, 'the US key runs the contest inside the D9 switch block (same indentation as the D9 body)')
check('a person decides' in blk and "'g'] = 'pin'" in blk, 'a person case leaves every park (a park left with nothing is a pin)')
check('check (exact name)' in blk, 'a record whose full name is ANOTHER park of the state goes back from the park that took it (exact name wins)')
print('ALL PASS' if all(R) else f'{R.count(False)} FAILED'); sys.exit(0 if all(R) else 1)
