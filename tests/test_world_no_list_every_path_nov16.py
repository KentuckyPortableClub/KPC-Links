#!/usr/bin/env python3
"""KPC owner, 2026-11-16 (rule 21: a no means the record never joins that park on any build path). The world builder read a park's
NO list on the name paths only; the later paths joined the same record again because the join was empty (Nov 14 build: the ten
keep-as-pin parks of Nov 2). enforce_no() runs once after every join path."""
import json, pathlib, sys, unicodedata
ROOT = pathlib.Path(__file__).resolve().parents[1]
src = (ROOT / '.github/scripts/kpc_world_key.py').read_text(encoding='utf-8')
ok = True
def check(msg, cond):
    global ok
    ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + msg)
ns = {'unicodedata': unicodedata}
a = src.index('def low(x)'); b = src.index('    return n\n', src.index('def enforce_no')) + len('    return n\n')
exec(src[a:b], ns)
E = ns['enforce_no']
wov = {'BZ-0051': {'no': ['Laughing Bird Caye'], 'join': []}, 'AU-8945': {'no': ['805', 'Godwin Beach']}, 'XX-0001': {'no': ['Other Place']}, 'XX-0003': {'no': ['Big Forest']}}
parks = {
    'BZ-0051': {'n': 'Bird Caye Bird Sanctuary', 'm': [[183, 'Laughing Bird Caye', 'Protected_Areas_Belize_2015', 'pin inside + shared name words'],
                                                    [100, 'Laughing Bird Caye', 'PA_updated_2024', 'pin inside + shared name words']], 'c': []},
    'AU-8945': {'n': 'Scarborough State Beach', 'm': [[805, 'Some Other Name', 'QLD Places', 'the POTA pin is inside it (names are written differently here)']], 'c': []},
    'XX-0001': {'n': 'Right Park', 'm': [[7, 'Right Park', 'L', 'name']], 'c': [[9, 'Near Miss', 'L', 'similar name']]},
    'XX-0002': {'n': 'No List Park', 'm': [[8, 'No List Park', 'L', 'name']], 'c': []},
    'XX-0003': {'n': 'Small Park', 'm': [[1, 'Small Park', 'L', 'name'], [2, 'Big Forest', 'L', 'pin inside + shared name words']], 'c': []}}
before = json.loads(json.dumps(parks))
n = E(parks, wov)
check('three parks change, two do not', n == 3 and parks['XX-0001'] == before['XX-0001'] and parks['XX-0002'] == before['XX-0002'])
check('a record named on the NO list is taken out whatever path joined it: the park is a pin', parks['BZ-0051']['m'] == [])
check('it is listed as a candidate with the reason (never lost, never joined)', len(parks['BZ-0051']['c']) == 2 and all(x[3] == ns['NO_WHY'] for x in parks['BZ-0051']['c']))
check('a NO written as a record id matches too', parks['AU-8945']['m'] == [] and parks['AU-8945']['c'][0][0] == 805)
check('only the NO record goes: the park keeps its other record', parks['XX-0003']['m'] == [[1, 'Small Park', 'L', 'name']])
check('a second run changes nothing', E(parks, wov) == 0)
i = src.index('JPX.apply(cc, parks, P, recs'); j = src.index('_nn = enforce_no(parks, WOV)'); k = src.index('# IS THE BOUNDARY WHERE IT SHOULD BE?')
check('the builder runs it after every join path (after the Japan crosswalk) and before the checks and the saved outlines', i < j < k)
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
