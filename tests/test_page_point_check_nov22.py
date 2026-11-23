#!/usr/bin/env python3
"""22 Nov 2026 (owner 8:55 PM, ruling W-G3 "Check list"): a pin-only park whose own official page gives a point inside a
piece of land gets that piece on its check list, never drawn; an office point, a piece a person said no to, or a piece
already listed is not added. Invented parks and records only. Fails before the change (no _page_point_checks)."""
import ast, math, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = (ROOT / '.github' / 'scripts' / 'kpc_us_key.py').read_text(encoding='utf-8')
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_match_checks as MC  # noqa: E402
bad = []


def check(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok: bad.append(name)


tree = ast.parse(SRC)
want = {'_page_point_checks', 'near', 'inside', 'in_ring', 'rings'}
got = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in want}
check('the US key has the page-point check for pin-only parks', set(got) == want)
if set(got) == want:
    ns = {'MC': MC, 'math': math, 'OVR': {'US-9002': {'no': ['sgzza2']}}}
    for n in want: exec(compile(ast.Module([got[n]], []), 'k', 'exec'), ns)
    sq = lambda x0, y0: {'rings': [[[x0, y0], [x0 + .1, y0], [x0 + .1, y0 + .1], [x0, y0 + .1], [x0, y0]]]}
    rec = lambda oid, x0, y0: {'OBJECTID': oid, 'Unit_Nm': 'Test Land', 'GIS_Acres': 10, '_g': sq(x0, y0), '_bb': [x0, y0, x0 + .1, y0 + .1]}
    byid = {'sgzza1': rec('sgzza1', -80.0, 40.0), 'sgzza2': rec('sgzza2', -79.0, 41.0)}
    page = lambda pts: {'page': {'own_page': 'own', 'unofficial': False, 'coords': pts}}
    parks = {'US-9001': {'m': [], 'c': []}, 'US-9002': {'m': [], 'c': []}, 'US-9003': {'m': [['sgzza1', 'x', 1, 'same name']], 'c': []},
             'US-9004': {'m': [], 'c': []}, 'US-9005': {'m': [], 'c': [['sgzza1', 'Test Land', 10, 'check (similar name)']]}}
    facts = {'US-9001': page([{'lat': 40.05, 'lon': -79.95, 'role': 'unknown'}]),
             'US-9002': page([{'lat': 41.05, 'lon': -78.95, 'role': 'park'}]),
             'US-9003': page([{'lat': 40.05, 'lon': -79.95, 'role': 'park'}]),
             'US-9004': page([{'lat': 40.05, 'lon': -79.95, 'role': 'office'}]),
             'US-9005': page([{'lat': 40.05, 'lon': -79.95, 'role': 'park'}])}
    res = {}
    ns['_page_point_checks']('ZZ', parks, byid, facts, res)
    check('a pin-only park gets the land its page point is in as a CHECK row, not an outline',
          parks['US-9001']['m'] == [] and [c[0] for c in parks['US-9001']['c']] == ['sgzza1'] and 'page point' in parks['US-9001']['c'][0][3])
    check("a piece a person said no to is never added", parks['US-9002']['c'] == [])
    check('a park that already has an outline is left alone', parks['US-9003']['c'] == [])
    check('an office point on the page does not count', parks['US-9004']['c'] == [])
    check('a piece already on the check list is not added twice', len(parks['US-9005']['c']) == 1)
    check('it is counted', res.get('page_point_checks') == 1)
print('ALL PASS' if not bad else f'{len(bad)} FAIL')
sys.exit(1 if bad else 0)
