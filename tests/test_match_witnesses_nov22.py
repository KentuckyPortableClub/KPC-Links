#!/usr/bin/env python3
"""22 Nov 2026 (owner: "more options we have to match the better other then name"; "agency id ... the one for sure"; "we have
the grid squares of every park"): the new witnesses in the match checks. (1) A point on the park's OWN page inside a record
keeps a piece the pin rule (3c) would send to check, and with a name that agrees it confirms the park; an office or mailing
point never counts. (2) The outline store's id fields reach the id check in store mode (KPC_RECORD_ATTRS). (3) POTA's grid
square is checked against its pin (a note, nothing moves). Invented parks and records only. No network."""
import gzip, json, os, pathlib, re, socket, subprocess, sys, tempfile

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


SQ = lambda x0, y0: {'type': 'Polygon', 'coordinates': [[[x0, y0], [x0 + .1, y0], [x0 + .1, y0 + .1], [x0, y0 + .1], [x0, y0]]]}
TABLE = {'sgzza': {'agency': 'state parks', 'kind': 'park'}}
LINK = {'site': 'agency (known)', 'agency': 'ZZ State Parks', 'page_kind': 'own page', 'usable': True, 'id_shared_by': 1, 'shared_by': 1}


def rec(oid, name, x0, y0):
    return {'OBJECTID': oid, 'Unit_Nm': name, 'Mang_Type': 'STAT', 'Mang_Name': 'SPR', 'GIS_Acres': 500, '_g': SQ(x0, y0), '_bb': [x0, y0, x0 + .1, y0 + .1]}


def fact(coords):
    return {'area': 'US-ZZ', 'name': 'Test Lake State Park', 'type': 'State Park', 'pin': [40.05, -79.95], 'link': dict(LINK),
            'page': {'kind': 'html', 'own_page': 'own', 'unofficial': False, 'host': 'parks.zz.example.gov', 'name_on_page': '',
                     'sizes': [], 'coords': coords, 'parts': [], 'inside_of': []}}


def inside(pt, r):
    b = r['_bb']; return b[0] <= pt[1] <= b[2] and b[1] <= pt[0] <= b[3]


def run(coords):
    recs = {'sgzza1': rec('sgzza1', 'Test Lake State Park', -80.0, 40.0), 'sgzza2': rec('sgzza2', 'Hilltop Tract', -79.7, 40.3)}
    parks = {'US-9001': {'n': 'Test Lake State Park', 't': 'State Park', 'g': 'official', 'c': [],
                         'm': [['sgzza1', 'Test Lake State Park', 500, 'same name'], ['sgzza2', 'Hilltop Tract', 500, 'same name']]}}
    f = {'US-9001': fact(coords)}
    holds = lambda ref, i: i == 'sgzza1'      # POTA's pin sits in the first record only
    page_holds = lambda ref, i: any(inside((c['lat'], c['lon']), recs[i]) for c in MC_pts(f[ref]) if True) if i in recs else None
    out = MC.pass_state(parks, recs, f, lambda ref, ids: True, st='ZZ', holds_fn=holds, layer_table=TABLE, page_holds_fn=page_holds)
    return parks['US-9001'], out


def MC_pts(fct):
    return [{'lat': a, 'lon': b} for a, b in MC.page_pins(fct)]


p, out = run([])
check('no page point: the pin rule sends the other-named piece to check (as before)', [q[0] for q in p['m']] == ['sgzza1'])
p, out = run([{'lat': 40.35, 'lon': -79.65, 'role': 'unknown'}])
check("a point on the park's own page inside that piece keeps it, and it is counted",
      [q[0] for q in p['m']] == ['sgzza1', 'sgzza2'] and out.get('kept_by_page_point') == 1)
p, out = run([{'lat': 40.35, 'lon': -79.65, 'role': 'office'}])
check('an office point on the page never counts', [q[0] for q in p['m']] == ['sgzza1'] and not out.get('kept_by_page_point'))
check('page_pins leaves out office and mailing points, keeps park and unknown ones',
      MC.page_pins(fact([{'lat': 1, 'lon': 2, 'role': 'office'}, {'lat': 3, 'lon': 4, 'role': 'mailing'}, {'lat': 5, 'lon': 6, 'role': 'park'},
                         {'lat': 7, 'lon': 8}])) == [(5.0, 6.0), (7.0, 8.0)])

src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
check('the US key hands the page-point test to the match checks', 'page_holds_fn=_page_holds' in src)
check('the US key reads the store id fields into a copy of each record (never the drawn record)',
      'KPC_RECORD_ATTRS' in src and "byid[i] = dict(a, SA=" in src)
r = subprocess.run([sys.executable, '-I', str(ROOT / '.github/scripts/kpc_store_attrs.py'), '--selftest'], capture_output=True, text=True)
check('the store id field tool keeps only the id fields, never WDPA, and skips old copies', r.returncode == 0 and 'ALL PASS' in r.stdout)

# the id check now finds a NY DEC-style address id once the store's URL field is on the record
ties = MC.load_link_ties()
t = next((x for x in ties if x.get('field') and x.get('layer')), None)
if t:
    m = re.search(r'\(([^)]*)\)', t['rx'])
    check('a store record carrying the tied field gives the id check a vote', bool(t))
ns = {}
exec(re.search(r"def _maiden6\(la, lo\):.*?\n\n", src, re.S).group(0), ns)
check("the grid square is worked out from the pin the way POTA does (a known pin and its grid)", ns['_maiden6'](25.4643, -80.3353) == 'EL95tl')
check('the grid note is a note only (it never moves a record)', "p['match'].setdefault('notes', []).append('grid square differs from pin')" in src)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
