#!/usr/bin/env python3
"""ORIGINAL HEADER OF test_near_town_nov23 (setup reused) 23 Nov 2026, owner 6:37 AM ('4 I say yes', ruling W-G6): a 'near a town' point the park's OWN official page gives in words
('2 miles east of Shiocton'; made on the PC from the town lists, park facts page.near, with how far off it may be) is a place
witness. Land reaching its circle is in the right place: with a name that agrees it CONFIRMS ('near a town'). When ALL the
joined land lies far from there (the same name somewhere else) it goes to the check list, the row saying why; never a record
holding POTA's pin, never the far pieces of a park that also has land by the town, never when an id or the agency's own size
speaks for it. A list page or an unofficial site gives nothing. Invented parks and records; this file opens no connection."""
import pathlib, socket, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))


def _no_net(*a, **k): raise RuntimeError('no network in tests')
socket.socket.connect = _no_net
import kpc_match_checks as MC  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


SQ = lambda x0, y0: {'type': 'Polygon', 'coordinates': [[[x0, y0], [x0 + .05, y0], [x0 + .05, y0 + .05], [x0, y0 + .05], [x0, y0]]]}
TABLE = {'sgzza': {'agency': 'state wildlife', 'kind': 'wildlife area'}}
LINK = {'site': 'agency (known)', 'agency': 'ZZ DNR', 'page_kind': 'own page', 'usable': True, 'id_shared_by': 1, 'shared_by': 1,
        'web_name': 'unit 4471', 'name_match': 'none'}
rec = lambda oid, name, x0, y0: {'OBJECTID': oid, 'Unit_Nm': name, 'Mang_Type': 'STAT', 'Mang_Name': 'SFW', 'GIS_Acres': 500, '_g': SQ(x0, y0),
                                 '_bb': [x0, y0, x0 + .05, y0 + .05]}
TOWN = {'lat': 44.50, 'lon': -88.50, 'within_km': 3.0, 'from': '3.2 km E of Otterville (town list)'}


def run(recs, rows, near=(TOWN,), own='own', unofficial=False, sizes=(), name_vs='differs', holds=(), place=False, counties=()):
    parks = {'US-9001': {'n': 'Mud Lake State Wildlife Area', 't': 'State Wildlife Area', 'g': 'official', 'c': [], 'm': [list(r) for r in rows]}}
    f = {'US-9001': {'area': 'US-ZZ', 'name': 'Mud Lake State Wildlife Area', 'type': 'State Wildlife Area', 'pin': [44.9, -89.4], 'link': dict(LINK),
                     'page': {'kind': 'html', 'own_page': own, 'unofficial': unofficial, 'host': 'dnr.zz.example.gov', 'name_vs_pota': name_vs,
                              'name_on_page': '', 'sizes': list(sizes), 'coords': [], 'parts': [], 'inside_of': [], 'near': list(near), 'county_areas': list(counties)}}}
    out = MC.pass_state(parks, recs, f, lambda ref, ids: place, st='ZZ', holds_fn=lambda ref, i: i in holds, layer_table=TABLE)
    p = parks['US-9001']
    return [q[0] for q in p.get('m') or []], [(x[0], x[3]) for x in p.get('c') or []], p.get('match') or {}, out



FAR = rec('sgzza2', 'Mud Lake Wildlife Area', -87.20, 45.10)           # about 120 km from the town: another Mud Lake
ROWH = lambda r, how: [r['OBJECTID'], r['Unit_Nm'], 500, how]
# AUDIT 1 MUST 2: the town (W-G6) and county (W6) rules move only plain name joins
m, c, st, _ = run({'sgzza2': FAR}, [ROWH(FAR, 'same name')])
check('control: a plain name join far from the town goes to check', m == [] and len(c) == 1)
for how in ('reviewed', 'reviewed-sheet'):
    m, c, st, _ = run({'sgzza2': FAR}, [ROWH(FAR, how)])
    check(f"a row a person joined ('{how}') never goes to check for a far town", m == ['sgzza2'] and c == [])
CTY = ({'name': 'Otter', 'lat': 44.5, 'lon': -88.5, 'radius_km': 22.3},)
m, c, st, _ = run({'sgzza2': FAR}, [ROWH(FAR, 'same name')], near=(), counties=CTY)
check('control: a plain name join outside the county the page names goes to check', m == [] and len(c) == 1)
m, c, st, _ = run({'sgzza2': FAR}, [ROWH(FAR, 'reviewed')], near=(), counties=CTY)
check('a row a person joined never goes to check for the county', m == ['sgzza2'] and c == [])
code = (ROOT / '.github/scripts/kpc_match_checks.py').read_text(encoding='utf-8')
check('the map-link rule (W-G10) moves only movable rows', 'rows_ = [q for q in left if movable(q)]' in code and 'and any(movable(q) for q in left)' in code)

# REVIEW of #363 M3: the Canada size counts the same land once
box = {'a': [0, 0, 1, 1], 'b': [0.02, 0.01, 1.0, 0.99], 'c': [0.0, 0.0, 0.98, 1.0], 'd': [5, 5, 6, 6]}
lay = {'a': 'CPCAD', 'b': 'PROV', 'c': 'PROV2', 'd': 'CPCAD'}
p = {}
rows = [['a', 'X', 289], ['b', 'X', 289], ['c', 'X', 283]]
check('three layers holding the same piece count once (289, not 861)', MC.size_once(p, rows, box.get, lay.get) == 289)
check('a second, separate piece still adds', MC.size_once(p, rows + [['d', 'X', 100]], box.get, lay.get) == 389)
check("the key's measured size wins", MC.size_once({'ac': 300}, rows, box.get, lay.get) == 300)
f = {'CA-9001': {'pin': [0.5, 0.5], 'link': {}, 'page': {'kind': 'html', 'own_page': 'own', 'unofficial': False, 'sizes': [
    {'acres': 280, 'witness': 'agency_document', 'total': True, 'clean': True}], 'coords': [], 'parts': [], 'near': []}}}
parks = {'CA-9001': {'n': 'X', 'm': [list(r) + ['same name'] for r in rows], 'c': []}}
out = MC.canada_pass(parks, {}, f, lambda r, i: None, None, size_of=lambda p_, m_: MC.size_once(p_, m_, box.get, lay.get))
check('Canada: the same land in 3 layers agrees with the agency size: kept and confirmed by size',
      len(parks['CA-9001']['m']) == 3 and (parks['CA-9001'].get('match') or {}).get('by') == 'size')
parks = {'CA-9001': {'n': 'X', 'm': [list(r) + ['same name'] for r in rows], 'c': []}}
MC.canada_pass(parks, {}, f, lambda r, i: None, None)
check('the plain outline size no longer adds the 3 rows up either (no vote: kept, not moved)', len(parks['CA-9001']['m']) == 3)
ca = (ROOT / '.github/scripts/kpc_ca_key.py').read_text(encoding='utf-8')
check('the Canada key passes the same-land size', 'size_of=_csize' in ca and 'MC.size_once(' in ca)

# AUDIT 3 S5-S7 (owner 6:02 PM 'Yes')
check("the size vote uses the measured size", MC.outline_size({'ac': 700}, [['a', 'X', 300], ['b', 'X', 300]]) == 700)
check("one row: its own acres", MC.outline_size({}, [['a', 'X', 300]]) == 300)
check("several rows and no measured size: no vote (never added up)", MC.outline_size({}, [['a', 'X', 300], ['b', 'X', 300]]) is None)
check("no vote means no vote", MC.size_vote([(300.0, 'agency', 'agency_document')], None)[0] == 'no vote')
uk = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
check('the union size has a work budget, not a clock', 'if work > 3_000_000: skipped += 1; continue' in uk and 'time.time() - t_ac' not in uk)
import tempfile, gzip, contextlib, io
import kpc_park_facts_read as PFR
with tempfile.TemporaryDirectory() as td:
    bad = pathlib.Path(td) / 'park-facts.json.gz'; bad.write_bytes(b'not gzip')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): got = PFR.load(str(bad))
    check('an unreadable park facts file is said in the log', got == {} and 'unreadable' in buf.getvalue())

# AUDIT 1 MUST 1: importing the US key builder stops before any build
import subprocess, os
idx = ROOT / 'data/us-key/index.json'
t0 = idx.stat().st_mtime if idx.exists() else None
r = subprocess.run([sys.executable, '-c', 'import sys; sys.path.insert(0, ".github/scripts"); import kpc_us_key'], cwd=ROOT,
                   capture_output=True, text=True, timeout=900, env=dict(os.environ, KPC_KEY_OFFLINE='1', STATES='ZZ'))
check('importing kpc_us_key stops with ImportError', r.returncode != 0 and 'ImportError' in r.stderr and 'run it as a script' in r.stderr)
check('and writes no key index', (idx.stat().st_mtime if idx.exists() else None) == t0)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
