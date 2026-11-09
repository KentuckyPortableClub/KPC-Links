"""Nov 4 (Mapping 2-fer review): tests for kpc_fers_guard.py and its use in kpc_fers.py / kpc_fers_line_check.py.
Run: python3 tests/test_fers_guard_nov4.py   (the kpc_fers.py part needs numpy + opencv; it is skipped without them)."""
import json, os, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent / '.github' / 'scripts'
sys.path.insert(0, str(HERE))
import kpc_fers_guard as FG  # noqa: E402

FAIL = []


def ok(c, what):
    print(('PASS ' if c else 'FAIL ') + what)
    if not c: FAIL.append(what)


# 1. bad POTA pins: listed, never moved
ok(FG.pin_problem(0, 0) == '0,0 POTA pin', '0,0 pin is bad')
ok(FG.pin_problem(95.2, -58.1).startswith('impossible'), 'latitude over 90 is bad (no swap guess)')
ok(FG.pin_problem(45, -200).startswith('impossible'), 'longitude past 180 is bad')
ok(FG.pin_problem('x', 1) == 'POTA pin is not a number' and FG.pin_problem(None, 1) == 'POTA pin is not a number', 'not a number is bad')
ok(FG.pin_problem(float('nan'), 1) == 'POTA pin is not a number', 'NaN is bad')
ok(FG.pin_problem(0, 12.5) == '' and FG.pin_problem(45.1, -70.2) == '', 'a real pin (even on the equator) is fine')

# 2. same land from one record
ok(FG.same_land_doubt('White River National Wildlife Refuge', 'Dale Bumpers White River National Wildlife Refuge National Wildlife Area',
                      'Dale Bumpers White River National Wildlife Refuge') == '', 'one refuge record naming both refuge numbers = candidate')
ok(FG.unbracket('Alpha State Park (Lower Tract)') == 'Alpha State Park' and FG.unbracket('Hotel (Lewis County) State Forest') == 'Hotel State Forest', 'bracket qualifiers come off (rule 18 v5)')
ok(FG._names_it('Alpha State Park', 'Alpha State Park (Lower Tract)'), "rule 18 v5: a record's bracket qualifier does not count ('Alpha State Park (Lower Tract)' names 'Alpha State Park')")
ok(FG._names_it('Hotel (Lewis County) State Forest', 'Hotel State Forest'), "rule 18 v5: a POTA bracket qualifier does not count ('Hotel (Lewis County) State Forest' vs 'Hotel State Forest')")
ok(FG.same_land_doubt('Alpha State Park (Upper Tract)', 'Alpha State Park (Lower Tract)', 'Alpha State Park') == '', 'two parks whose names differ only in brackets: the record names both (no bracket-only doubt)')
ok(not FG._names_it('Kirkpatrick Basin North Wildlife Management Area', 'Kirkpatrick Basin Wildlife Management Area'), 'a one-side compass word outside brackets still tells the pieces apart (rule 18)')
ok(FG.same_land_doubt('Fundy Biosphere Reserve', 'Fundy National Park', 'Fundy National Park Of Canada').startswith('not sure'), 'biosphere reserve on a national park record = not sure')
ok(FG.same_land_doubt('Logoly State Park', 'Logoly State Natural Area', 'Logoly State Park').startswith('not sure'), 'natural area on a state park record = not sure (kind differs)')
ok(FG.same_land_doubt('Carpenter Lake WMA', 'Kingfisher Lakes WMA', 'Carpenter Lake WMA').startswith('not sure'), 'one parcel record naming only one of two lakes = not sure')
ok('a person decides' in FG.same_land_doubt('Kirkpatrick Basin North Wildlife Management Area', 'Kirkpatrick Basin South Wildlife Management Area', 'Kirkpatrick Basin Wildlife Management Area')
   or FG.same_land_doubt('Kirkpatrick Basin North Wildlife Management Area', 'Kirkpatrick Basin South Wildlife Management Area', 'Kirkpatrick Basin Wildlife Management Area') == '', 'north / south units: never an error')

# 3. overrides 'no'
with tempfile.TemporaryDirectory() as t:
    p = pathlib.Path(t) / 'o.json'
    p.write_text(json.dumps({'note': 'x', 'parks': {'CA-1': {'no': ['Bad Piece', 77]}, 'CA-2': {'join': ['A']}, 'CA-3': {'none': True}}}))
    no = FG.override_no(p)
    ok(set(no) == {'CA-1'}, "only 'no' lists are read ('join' / 'none' are not a no)")
    m = [[77, 'Other', 'x', 'name'], [5, 'bad piece', 'x', 'name'], [6, 'Good', 'x', 'name']]
    ok(FG.drop_no(m, no['CA-1']) == [[6, 'Good', 'x', 'name']], "a 'no' id or name (any case) is left out")
    ok(FG.drop_no(m, None) == m, 'no override = unchanged')
    ok(FG.override_no(pathlib.Path(t) / 'missing.json') == {}, 'a missing overrides file = no overrides')

# 4. the swap guesses are gone (never move POTA pins)
src = (HERE / 'kpc_fers.py').read_text(); lc = (HERE / 'kpc_fers_line_check.py').read_text()
ok('la_, lo_ = abs(lo_), -abs(la_)' not in src, 'kpc_fers.py: no swap guess for an impossible Canadian pin')
ok('(abs(v[6]), -abs(v[5]))' not in lc, 'kpc_fers_line_check.py: no swap guess either')
ok("if not _wp and l_ref in LN and water_route(l_ref, LN, PINS):" in src and '_dry = []' in src, 'water route with no water/land split: no centre-line test')

# 5. kpc_fers.py pins() + official_parks() on a small fixture (needs numpy + cv2)
try:
    import numpy, cv2  # noqa: F401
    HAVE = True
except Exception:
    HAVE = False
if not HAVE:
    print('SKIP kpc_fers.py fixture test (numpy / opencv not installed)')
else:
    with tempfile.TemporaryDirectory() as t:
        T = pathlib.Path(t)
        (T / 'data/parkinfo').mkdir(parents=True); (T / 'data/us-key').mkdir(parents=True); (T / 'data/ca-key').mkdir(parents=True); (T / 'data/world-key').mkdir(parents=True)
        ca = {'parks': {'CA-0001': ['Good Park', '', 'Provincial Park', 0, 0, 46.0, -71.0, 0, 0, 0, 'QC'],
                        'CA-0002': ['Zero Park', '', 'Provincial Park', 0, 0, 0, 0, 0, 0, 0, 'QC'],
                        'CA-0003': ['Churchill WMA', '', 'WMA', 0, 0, 95.1, -58.7, 0, 0, 0, 'MB'],
                        'CA-0004': ['Said No Park', '', 'Provincial Park', 0, 0, 46.2, -71.2, 0, 0, 0, 'QC'],
                        'CA-0005': ['No Id Park', '', 'Provincial Park', 0, 0, 0, 0, 0, 0, 0, 'QC']}}
        (T / 'data/parkinfo/CA.json').write_text(json.dumps(ca))
        (T / 'data/parkinfo/US-VT.json').write_text(json.dumps({'parks': {'US-0001': ['Vt Park', '', 'State Park', 0, 0, 44.0, -72.0]}}))
        (T / 'data/us-key/US-VT.json').write_text(json.dumps({'parks': {'US-0001': {'m': [[11, 'Vt Park', 'x', 'name']]}}}))
        (T / 'data/ca-key/CA-QC.json').write_text(json.dumps({'parks': {r: {'m': [[f'Quebec layer:{i}', n, 'x', 'name']]} for i, (r, n) in
                                                                         enumerate([('CA-0001', 'Good Park'), ('CA-0002', 'Zero Park'), ('CA-0004', 'Wrong Piece')])}}))
        # Nov 9 PM (Brandon t902u): a bad-pin park joined only by name (no record id) is still left out and listed
        _q = json.loads((T / 'data/ca-key/CA-QC.json').read_text()); _q['parks']['CA-0005'] = {'m': [[None, 'No Id Park', 'x', 'name']]}
        (T / 'data/ca-key/CA-QC.json').write_text(json.dumps(_q))
        (T / 'data/ca-key/CA-MB.json').write_text(json.dumps({'parks': {'CA-0003': {'m': [['Manitoba lay:1', 'Churchill WMA', 'x', 'name']]}}}))
        (T / 'data/ca-key/overrides.json').write_text(json.dumps({'note': 'x', 'parks': {'CA-0004': {'no': ['Wrong Piece']}}}))
        code = ("import sys, json; sys.path.insert(0, %r); import kpc_fers as F; P = F.pins(); parks, skip = F.official_parks(P);"
                "print(json.dumps({'P': sorted(P), 'Pxy': {r: list(v[1:3]) for r, v in P.items()}, 'bad': {r: v[1] for r, v in F.BAD_PIN.items()}, 'parks': sorted(parks), 'skip': skip, 'why': F.SKIPWHY}))") % str(HERE)
        r = subprocess.run([sys.executable, '-c', code], cwd=T, capture_output=True, text=True, env={**os.environ, 'REGION': 'na', 'STATES': ''})
        try: res = json.loads(r.stdout.strip().splitlines()[-1])
        except Exception: res = {}; print(r.stdout[-800:], r.stderr[-1500:])
        ok(res.get('bad') == {'CA-0002': '0,0 POTA pin', 'CA-0003': 'impossible POTA pin 95.1,-58.7', 'CA-0005': '0,0 POTA pin'}, 'pins(): 0,0 and impossible pins listed in BAD_PIN')
        # Nov 9 PM (Brandon t901u/t902u): a bad pin is never used or swapped: the park keeps its name with NO coordinates
        ok(res.get('Pxy', {}).get('CA-0002') == [None, None] and res.get('Pxy', {}).get('CA-0003') == [None, None], 'pins(): bad pins are not used (and never swapped)')
        ok(res.get('parks') == ['CA-0001', 'CA-0002', 'CA-0003', 'US-0001'], 'official_parks(): bad-pin parks with saved record ids are tested by those outlines; the no-ed park is out')
        ok((res.get('skip') or {}).get('bad POTA pin (0,0 / impossible, listed)') == 1 and (res.get('skip') or {}).get('bad POTA pin, tested by its saved record ids (pin not used)') == 2,
           'official_parks(): 1 bad-pin park with no record id left out, 2 tested by their ids')
        ok((res.get('skip') or {}).get('every joined piece is in the overrides no list (key not rebuilt yet)') == 1, "official_parks(): the 'no' park is left out before the key rebuild")
        ok('never moved' in (res.get('why') or {}).get('CA-0005', ''), 'why list says the pin is never moved')

print('ALL PASS' if not FAIL else f'{len(FAIL)} FAILED: {FAIL}')
sys.exit(1 if FAIL else 0)
