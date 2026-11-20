#!/usr/bin/env python3
"""Hand-off 06: the owner's seven answers for 2-fers (R-2F1 to R-2F7). Offline. Made-up parks.
The plain case, the trap and the unsure case of each rule. known-answers rows KA-01 to KA-24."""
import contextlib, csv, io, json, math, os, pathlib, sys, tempfile, types
HERE = pathlib.Path(__file__).resolve().parent.parent
S = HERE / '.github/scripts'
sys.path.insert(0, str(S))
os.environ['PASS'] = '3'
os.environ['REGION'] = 'na'
os.environ['HTTP_CACHE'] = ''
for k in list(os.environ):
    if k.startswith('KPC_FERS_') or 'proxy' in k.lower():
        os.environ.pop(k)
TD = pathlib.Path(tempfile.mkdtemp(prefix='kpc-r2f-'))
os.chdir(TD)
import kpc_fers as K
import kpc_fers_age as AGE
import kpc_fers_store as KS
import kpc_fers_switches as SW
import kpc_fers_key_status as FKS
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg, flush=True)
    ok = ok and bool(c)


src = (S / 'kpc_fers.py').read_text(encoding='utf-8')
store_src = (S / 'kpc_fers_store.py').read_text(encoding='utf-8')
pc_src = (HERE / 'tools/pc-runner/kpc_pc_run.py').read_text(encoding='utf-8')
ar_src = (S / 'kpc_fers_area_run.py').read_text(encoding='utf-8')
LAT0, LON0 = 37.5, -84.0
NOTE = 'Possible 2-fer. We are missing an official boundary here: check both official boundary maps before you count it.'

# --- the switch file (KA-23, KA-24) ---
try:
    SW.load(TD / 'missing.json'); stopped = False
except SystemExit as e:
    stopped = e.code == 4
check(stopped, 'KA-23 a missing switch file stops the bot (exit 4)')
bad = TD / 'broken.json'; bad.write_text('{')
try:
    SW.load(bad); stopped = False
except SystemExit as e:
    stopped = e.code == 4
check(stopped, 'KA-23 a broken switch file stops the bot (exit 4)')
try:
    SW.value('KPC_FERS_NOT_A_SETTING'); stopped = False
except SystemExit as e:
    stopped = e.code == 4
check(stopped, 'KA-23 a setting the code asks for that the file does not hold stops the bot (exit 4)')
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    v, src_of = SW.value('KPC_FERS_NEAR_LINE')
check(v == '1' and src_of == 'file', f'KA-24 the file is in force when the environment is quiet ({v}, {src_of})')
os.environ['KPC_FERS_NEAR_LINE'] = '0'
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    v, src_of = SW.value('KPC_FERS_NEAR_LINE')
check(v == '0' and src_of == 'env' and 'comes from the environment' in buf.getvalue(),
      'KA-24 an environment variable wins and the run prints one notice')
os.environ.pop('KPC_FERS_NEAR_LINE')
os.environ['KPC_FERS_SUMMARY_APPROX'] = '0'
SW._SAID.discard('KPC_FERS_SUMMARY_APPROX')
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    on = K._switch_on('KPC_FERS_SUMMARY_APPROX')
check(on is False and 'comes from the environment' in buf.getvalue(),
      'kpc_fers uses the one switch reader, so the notice is printed whichever path asks')
os.environ.pop('KPC_FERS_SUMMARY_APPROX')
K.write_receipt({'pairs tested': 0}, {}, {}, set(), 'rules')
recs = list((TD / 'data/fers').glob('receipt-*.json')) if (TD / 'data/fers').is_dir() else []
doc = json.loads(recs[0].read_text()) if recs else {}
switches = ((doc.get('passes') or {}).get('3') or {}).get('switches') or []
check(any(s.get('name') == 'KPC_FERS_SUMMARY_APPROX' and s.get('from') == 'file' for s in switches),
      f'KA-24 the receipt records each setting and where it came from ({switches[:1]})')

# --- R-2F3 the band is one cell (KA-01, KA-07) ---
check(not hasattr(K, 'NEAR_LINE_M') and 'KPC_FERS_NEAR_LINE_M' not in src, 'KA-01 no setting takes a number of metres')
check(K.near_line({'kind': 'area', 'wide_m': 22.86}).startswith('near a size line')
      and K.near_line({'kind': 'area', 'wide_m': 45.72}).startswith('near a size line')
      and K.CELL == 5.0, 'KA-01 at pass 3 the band is the 5 m cell, read from CELL')
check(K.near_line({'kind': 'area', 'wide_m': 200}) == '' and K.near_line({'kind': 'river', 'wide_m': 22.86}) == '',
      'KA-07 a 200 m area row and a river row are not touched')
os.environ['KPC_FERS_NEAR_LINE'] = '0'
check(K.near_line({'kind': 'area', 'wide_m': 22.86}) == '', 'KA-06 with the rule off, a width on the line is not NOT SURE')
os.environ.pop('KPC_FERS_NEAR_LINE')

# --- the saved 472-row file (KA-06) ---
rows = list(csv.DictReader(open(HERE / 'tests/fixtures/fers-wl3-near-line-rows.csv', encoding='utf-8')))
y25 = [r for r in rows if r['line'] == '25-yard' and r['status'] != 'water only']
y50 = [r for r in rows if r['line'] == '50-yard' and r['status'] != 'water only']
h25 = [r for r in y25 if K.near_line({'kind': 'area', 'wide_m': float(r['wide_m'])})]
h50 = [r for r in y50 if K.near_line({'kind': 'area', 'wide_m': float(r['wide_m'])})]
check(len(rows) == 472 and len(h25) == 226 and len(y25) == 226 and len(h50) == 154 and len(y50) == 159,
      f'KA-06 226 of 226 at 25 yards and 154 of 159 at 50 yards are NOT SURE ({len(h25)}, {len(h50)})')

# --- the real grid, a few widths (KA-02, KA-03, KA-04, KA-05) ---
try:
    import numpy, cv2  # noqa: F401
    HAVE = True
except Exception:
    HAVE = False
KX, KY = 111320 * math.cos(math.radians(LAT0)), 110574


def rect(x0, y0, x1, y1, ang=0):
    a = math.radians(ang); out = []
    for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]:
        xr, yr = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        out.append([LON0 + xr / KX, LAT0 + yr / KY])
    return [[out]]


def measure(w, ang, off):
    A, B = rect(-2000, -1000, off + w, 1000, ang), rect(off, -1000, 2000, 1000, ang)
    pts = A[0][0] + B[0][0]
    box = [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]
    sp = K.area_spots({'US-9901': A, 'US-9902': B}, ['US-9901', 'US-9902'], box)
    return max(sp, key=lambda s: s['wide_m']) if sp else None


if HAVE:
    under = [measure(w, ang, off) for w in (16, 18, 20, 22) for ang in (0, 17) for off in (0, 2.6)]
    found = [s for s in under if s is not None]
    check(found and all(23 <= s['wide_m'] <= 27 and K.near_line(s).startswith('near a size line') and 'very tight' not in K.near_line(s)
                        for s in found),
          f'KA-02 a true 16 to 22 m overlap that the grid finds reads 23 to 27 m and is NOT SURE ({[(s["wide_m"]) for s in found]})')
    none_small = [measure(w, ang, off) for w in (8, 12, 15) for ang in (0, 45) for off in (0, 3.9)]
    check(all(s is None for s in none_small), 'KA-03 a true 8 to 15 m overlap is found in none of these placements')
    side = []
    for w in (42, 44, 46, 48):
        s = measure(w, 0, 0)
        if s is not None and ((w <= 45 and s['wide_m'] >= 45.72) or (w >= 46 and s['wide_m'] <= 45.72)):
            side.append(s)
    check(side and all(K.near_line(s).startswith('near a size line') and '50-yard' in K.near_line(s) for s in side),
          f'KA-04 a reading on the wrong side of the 50-yard line is NOT SURE ({[s["wide_m"] for s in side]})')
    mid = [measure(w, 0, 0) for w in (30, 31, 32)]
    check(all(s is not None and 31 <= s['wide_m'] <= 37 and K.near_line(s) == '' for s in mid),
          f'KA-05 30 to 32 m reads 31 to 37 m and is not NOT SURE ({[None if s is None else s["wide_m"] for s in mid]})')

    def gap_spots(gap):
        """Two 30 m strips of one pair, `gap` metres apart, on the real grid (shapes, not hand-made boxes)."""
        big = rect(-1500, -1500, 1500, 1500)
        def piece(x0):
            return rect(x0, 0, x0 + 30, 300)
        pts = big[0][0]
        box = [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]
        return K.area_spots({'US-9901': big, 'US-9902': piece(0) + piece(30 + gap)}, ['US-9901', 'US-9902'], box)

    far_g, near_g = gap_spots(1000), gap_spots(120)
    close_g = gap_spots(44)
    check(len(far_g) == 2 and len(near_g) == 2,
          f'KA-13 two 30 m strips on the real grid are two spots at 1 km and at 120 m ({len(far_g)}, {len(near_g)})')
    check(len(close_g) == 1,
          f'KA-13 the same strips 44 m apart are one spot: merge() joins pieces within 0.0005 degrees ({len(close_g)})')
else:
    print('SKIP the live grid readings (numpy / cv2 not installed)')

# --- R-2F2 the forest rule is gone (KA-08) ---
check('fed_neighbours' not in src and 'FED_NEIGHBOUR' not in src and "two agencies" not in src,
      'KA-08 the words "two agencies\' maps disagree" are nowhere in the code')
check('KPC_FERS_FED_NEIGHBOUR' not in pc_src and 'KPC_FERS_NEAR_LINE_M' not in pc_src and 'KPC_FERS_CARRY_MAX' not in pc_src,
      'the PC runner passes none of these settings')
check('KPC_FERS_SUMMARY_APPROX' not in ar_src and 'KPC_FERS_FINE_ONLY' not in ar_src and 'KPC_FERS_STRIP_HELD' not in ar_src,
      'the area runner passes none of these settings')

# --- R-2F1 summary maps, and a key grade of approximate (KA-21, KA-22) ---
K.SUMMARY_SG.clear(); K.SUMMARY_SG.update({'sgmtd': 'compilation', 'sgaki': 'register', '_': ''})
qp = {'US-1': {'ids': ['sgmtd1']}, 'US-2': {'ids': ['mid9']}, 'US-3': {'ids': ['mszp1']},
      'US-4': {'ids': ['sgaki1']}, 'US-5': {'ids': ['sgmtd1', 99]}, 'US-6': {'ids': ['nolabel1']}}
check(K.summary_only('US-1', qp) and K.summary_only('US-2', qp) and K.summary_only('US-3', qp) and K.summary_only('US-4', qp),
      'KA-21 a compilation, a Michigan project line, the Mississippi file and a register are summary maps')
check(not K.summary_only('US-5', qp), 'KA-21 trap: one record of the agency\'s own land is not a summary map')
check(not K.summary_only('US-6', qp), 'KA-21 unsure: a layer with no label is not a summary map')
saved_sg = dict(K.SUMMARY_SG)
K.SUMMARY_SG.clear()
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    K._summary_sg()
check('could not be read' in buf.getvalue() and 'R-2F1' in buf.getvalue(),
      'a missing state-gis.json is said loudly (R-2F1 is not off in silence)')
K.SUMMARY_SG.clear()
K.SUMMARY_SG.update(saved_sg)


@contextlib.contextmanager
def quiet_decide():
    saved = {n: getattr(K, n) for n in ('key_line_match', 'same_records_verdict', 'saved_missing_why', 'is_picture_trace',
                                        'load_key_status', 'pin_inside', 'nearest_access', 'access_pin', 'map_link',
                                        'line_rows', 'how_checked', 'land_check', 'ownership_step')}
    real = FKS.status_for
    K.key_line_match = lambda *a, **k: ''
    K.same_records_verdict = lambda *a, **k: ()
    K.saved_missing_why = lambda r: ''
    K.is_picture_trace = lambda *a: False
    K.load_key_status = lambda *a, **k: None
    K.pin_inside = lambda *a: False
    K.nearest_access = lambda *a, **k: None
    K.access_pin = lambda *a, **k: None
    K.map_link = lambda *a, **k: ''
    K.line_rows = lambda *a, **k: None
    K.how_checked = lambda *a, **k: None
    K.land_check = lambda *a, **k: 'ok'
    try:
        yield
    finally:
        for n, v in saved.items():
            setattr(K, n, v)
        FKS.status_for = real


if HAVE:
    spot = measure(200, 0, 0)
    pin = {'US-9901': ('Grand Canyon National Park', LAT0, LON0, '', '', 'ZZ'),
           'US-9902': ('Kaibab National Forest', LAT0, LON0, '', '', 'ZZ')}
    parks = {'US-9901': {'st': 'US-ZZ', 'ids': ['xx1']}, 'US-9902': {'st': 'US-ZZ', 'ids': ['xx2']}}
    with quiet_decide():
        s = json.loads(json.dumps(spot))
        K.decide(s, parks, {}, {}, pin, '2026-11-19', set(), lambda r: 'US-ZZ')
    check(s.get('status') == 'candidate' and 'not sure' not in s.get('status', ''),
          f'KA-08 Grand Canyon National Park x Kaibab National Forest is decided like any pair ({s.get("status")!r})')
    pin_ol = {'US-9901': ('Olympic National Park', LAT0, LON0, '', '', 'ZZ'),
              'US-9902': ('Olympic National Forest', LAT0, LON0, '', '', 'ZZ')}
    with quiet_decide():
        s = json.loads(json.dumps(spot))
        K.decide(s, parks, {}, {}, pin_ol, '2026-11-19', set(), lambda r: 'US-ZZ')
    check(s.get('status') == 'candidate' and 'not sure' not in s.get('status', ''),
          f'KA-08 Olympic National Park x Olympic National Forest is decided like any pair ({s.get("status")!r})')
    with quiet_decide():
        FKS.status_for = lambda r, a=None: 'approximate'
        s = json.loads(json.dumps(spot))
        K.decide(s, parks, {}, {}, pin, '2026-11-19', set(), lambda r: 'US-ZZ')
    check(s.get('approx') is True and s.get('approx_note'),
          f'KA-22 a park the key grades approximate is an approximate 2-fer (decide _apx) ({s.get("approx_note","")[:40]!r})')
    check("status_for(r, _areas.get(r)) == 'approximate'" in src, 'KA-22 the line is decide() building _apx from the key grade')

# --- R-2F4 the stamp (KA-09 to KA-12, KA-10 every path) ---
root = TD
(root / 'data/us-key').mkdir(parents=True)
key = {'parks': {
    'US-1': {'n': 'One', 'm': [['a', 'One Park', 10, 'name']], 'g': 'official', 'c': [['old check']]},
    'US-2': {'n': 'Two', 'm': [['b', 'Two Park', 12, 'name']], 'g': 'official'},
    'US-3': {'n': 'Three', 'm': [['c', 'Three Park', 8, 'name']], 'g': 'official'},
    'US-4': {'n': 'Four', 'm': [['d', 'Four Park', 9, 'name']], 'g': 'official'},
}}
(root / 'data/us-key/US-ZZ.json').write_text(json.dumps(key))
(root / 'data/us-key/index.json').write_text(json.dumps({'build': 'US-OLD', 'built': '2026-11-01'}))
AGE._INDEX.clear()


def row(refs, **kw):
    r = {'refs': list(refs), 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1], 'center': [LAT0, LON0], 'wide_m': 80, 'acres': 40}
    r.update(kw)
    return r


pair = row(['US-1', 'US-2'])
AGE.stamp(pair, 'US-ZZ', root=str(root))
other = row(['US-3', 'US-4'])
AGE.stamp(other, 'US-ZZ', root=str(root))
(root / 'data/us-key/index.json').write_text(json.dumps({'build': 'US-44600381160', 'built': '2026-11-19 20:25 UTC', 'areas_rebuilt': 0}))
AGE._INDEX.clear()
kept = AGE.keep_fresh([pair, other], 'US-ZZ', root=str(root))
check(kept == [pair, other], 'KA-09 a new key build id, with nothing rebuilt, still copies a stamped row')
key['parks']['US-1']['m'] = [['a', 'One Park', 10, 'name'], ['z', 'Extra', 1, 'name']]
(root / 'data/us-key/US-ZZ.json').write_text(json.dumps(key))
AGE._INDEX.clear()
AGE.NOT_CARRIED.clear()
kept = AGE.keep_fresh([pair, other], 'US-ZZ', root=str(root))
check(kept == [other] and any('US-1' in x['why'] for x in AGE.NOT_CARRIED),
      f'KA-11 one park\'s key entry changes: that pair is not copied, the other pair still is ({[x["why"] for x in AGE.NOT_CARRIED]})')
plain = row(['US-1', 'US-2'])
AGE.NOT_CARRIED.clear()
check(AGE.keep_fresh([plain], 'US-ZZ', root=str(root)) == [], 'KA-10 an unstamped row is not copied by keep_fresh')
check(AGE.NOT_CARRIED and 'not a 2-fer' not in AGE.NOT_CARRIED[0]['why'], 'KA-10 the reason is plain and never says "not a 2-fer"')
n = KS.carry_rows({'st': 'US-ZZ', 'spots': []}, {'st': 'US-ZZ', 'spots': [plain]}, {})
check(n == 0, 'KA-10 carry_rows does not bring an unstamped row back')
old = {'spots': [dict(plain, id='A@1', box=[LON0 - .01, LAT0 - .01, LON0 + .01, LAT0 + .01])]}
new = {'st': 'US-ZZ', 'spots': [dict(plain, id='A@2', status='not sure: closed areas not checked', store_not_checked='closed areas',
                                    box=[LON0 - .01, LAT0 - .01, LON0 + .01, LAT0 + .01], acres=40)]}
KS.keep_old_rows(new, old, '2026-11-19')
check(not new['spots'][0].get('kept'), 'KA-10 keep_old_rows does not put an unstamped row back')
KS.STRIP_HELD = True
KS.withheld_refs = lambda: {'US-2'}
d = {'st': 'US-ZZ', 'spots': []}
KS.carry_held_rows(types.SimpleNamespace(PASS=1, OUT=str(TD / 'data/fers')), d, {'spots': [dict(plain, passes=[1, 1, 1])]})
check(d['spots'] == [], 'KA-17 an unstamped row of a withheld park is dropped and nothing replaces it')
stamped = row(['US-3', 'US-4'], passes=[1, 1, 1], shape=[[LON0, LAT0], [LON0 + .01, LAT0]], lines=[[1, 2]])
AGE.stamp(stamped, 'US-ZZ', root=str(root))
d = {'st': 'US-ZZ', 'spots': []}
KS.withheld_refs = lambda: {'US-4'}
KS.carry_held_rows(types.SimpleNamespace(PASS=1, OUT=str(TD / 'data/fers')), d, {'spots': [stamped]})
x = d['spots'][0] if d['spots'] else {}
check(x and 'shape' not in x and 'lines' not in x and x.get('center') and x.get('acres') == 40 and x.get('status') == 'candidate'
      and x.get('held_outline') == NOTE, 'KA-16 a stamped withheld row keeps the centre and the size and the owner\'s note, and drops the pieces')
pub = TD / 'public.json'
pub.write_text(json.dumps({'spots': d['spots']}))
check('shape' not in pub.read_text() and 'lines' not in pub.read_text(), 'KA-18 the written public file holds no coordinate list from that row')
broken = TD / 'badkey'
(broken / 'data/us-key').mkdir(parents=True)
(broken / 'data/us-key/US-ZZ.json').write_text('{')
AGE._INDEX.clear()
why = AGE.too_old(stamped, 'US-ZZ', root=str(broken))
check(why.startswith('the key file could not be read') or 'not in the key' in why, f'KA-12 an unreadable key is not copied ({why})')
AGE._INDEX.clear()
why = AGE.too_old(row(['US-9', 'US-3']), 'US-ZZ', root=str(root))
# US-9 is not stamped; the unstamped reason comes first. A stamped missing park:
missing = row(['US-9', 'US-3'])
missing['made_on'] = {'US-9': {'key': 'abc', 'outline': ''}, 'US-3': {'key': 'abc', 'outline': ''}}
AGE._INDEX.clear()
why = AGE.too_old(missing, 'US-ZZ', root=str(root))
check('US-9 is not in the key' in why, f'KA-12 a park missing from the key is not copied ({why})')

# store fingerprint
store = TD / 'store'
store.mkdir()
(store / 'index-US-ZZ.json').write_text(json.dumps({'parks': {'US-3': {'fp': 'aaa'}, 'US-4': {'fp': 'bbb'}}}))
KS.STORE_ON = True
KS.STORE = types.SimpleNamespace(dir=store)
KS._FP_CACHE.clear()
fp_row = row(['US-3', 'US-4'])
AGE.stamp(fp_row, 'US-ZZ', root=str(root), store_fp=KS.outline_fps(['US-3', 'US-4']))
check(fp_row['made_on']['US-3']['outline'] == 'aaa', 'the stamp keeps the store index fingerprint and not a date')
check(AGE.keep_fresh([fp_row], 'US-ZZ', root=str(root)) == [fp_row], 'a matching store fingerprint is copied')
(store / 'index-US-ZZ.json').write_text(json.dumps({'parks': {'US-3': {'fp': 'ccc'}, 'US-4': {'fp': 'bbb'}}}))
KS._FP_CACHE.clear()
AGE.NOT_CARRIED.clear()
check(AGE.keep_fresh([fp_row], 'US-ZZ', root=str(root)) == [], 'a changed store fingerprint is not copied')
check('outline fingerprint changed' in AGE.NOT_CARRIED[0]['why'], f'the reason names the outline ({AGE.NOT_CARRIED[0]["why"]})')
(store / 'index-US-ZZ.json').write_text(json.dumps({'parks': {'US-4': {'fp': 'bbb'}}}))
KS._FP_CACHE.clear()
AGE.NOT_CARRIED.clear()
check(AGE.keep_fresh([fp_row], 'US-ZZ', root=str(root)) == [],
      'a stamp that holds a store fingerprint is not copied when today\'s index has none')
check('outline fingerprint changed' in AGE.NOT_CARRIED[0]['why'],
      f'the reason is the outline, not a silent keep ({AGE.NOT_CARRIED[0]["why"]})')
KS.STORE_ON = False
KS.STORE = None

# parts, approx, and a Kentucky tract's acres and how are in the key fingerprint
AGE._INDEX.clear()
s0 = AGE.key_fingerprint('US-3', str(root))[0]
key['parks']['US-3']['parts'] = {'c': [[-84.5, 37.4, -84.4, 37.6]]}
(root / 'data/us-key/US-ZZ.json').write_text(json.dumps(key))
AGE._INDEX.clear()
check(AGE.key_fingerprint('US-3', str(root))[0] != s0, 'parts (a clipped shared record) changes the stamp')
key['parks']['US-3'].pop('parts')
key['parks']['US-3']['approx'] = True
(root / 'data/us-key/US-ZZ.json').write_text(json.dumps(key))
AGE._INDEX.clear()
check(AGE.key_fingerprint('US-3', str(root))[0] != s0, 'approx changes the stamp')
key['parks']['US-3'].pop('approx')
(root / 'data/us-key/US-ZZ.json').write_text(json.dumps(key))
(root / 'data/ky-answer-key.json').write_text(json.dumps({'parks': {'KY-1': {'tracts': [['bstate', 'Sample Park', 10, 'name', 2]]}}}))
AGE._INDEX.clear()
ky0 = AGE.key_fingerprint('KY-1', str(root))[0]
(root / 'data/ky-answer-key.json').write_text(json.dumps({'parks': {'KY-1': {'tracts': [['bstate', 'Sample Park', 11, 'name', 2]]}}}))
AGE._INDEX.clear()
check(AGE.key_fingerprint('KY-1', str(root))[0] != ky0, 'a Kentucky tract\'s acres are in the stamp')
ky_name = AGE.key_fingerprint('KY-1', str(root))[0]
(root / 'data/ky-answer-key.json').write_text(json.dumps({'parks': {'KY-1': {'tracts': [['bstate', 'Sample Park', 11, 'file', 2]]}}}))
AGE._INDEX.clear()
check(AGE.key_fingerprint('KY-1', str(root))[0] != ky_name, 'a Kentucky tract\'s how is in the stamp')
(root / 'data/ky-answer-key.json').write_text(json.dumps({'parks': {'KY-1': {'tracts': [['bstate', 'Sample Park', 11, 'name', 9]]}}}))
AGE._INDEX.clear()
check(AGE.key_fingerprint('KY-1', str(root))[0] == ky_name, 'the fifth tract number is a count and is not in the stamp')

# every status decide() returns carries made_on, and a small batch that does not read the park keeps the row
def plain_spot():
    return {'refs': ['US-1', 'US-2'], 'kind': 'area', 'wide_m': 200, 'acres': 40, 'id': 'US-1+US-2@area',
            'center': [LAT0, LON0], 'box': [LON0 - .01, LAT0 - .01, LON0 + .01, LAT0 + .01],
            'passes': [1, 1, 0], 'status': 'pass 2', 'shape': [[LON0, LAT0], [LON0 + .01, LAT0]]}


rows_settled = []
with quiet_decide():
    s = plain_spot(); K.decide(s, {'US-1': {'st': 'US-ZZ', 'ids': ['a']}, 'US-2': {'st': 'US-ZZ', 'ids': ['b']}}, {}, {},
                               {'US-1': ('One', LAT0, LON0, '', '', 'ZZ'), 'US-2': ('Two', LAT0, LON0, '', '', 'ZZ')},
                               '2026-11-19', set(), lambda r: 'US-ZZ')
    rows_settled.append(s)
    check(s.get('made_on') and s['made_on']['US-1'].get('outline') and s['made_on']['US-1'].get('outline_kind') == 'outline',
          'a plain overlap on a run without the store carries an outline hash, marked outline')
with quiet_decide():
    K.land_check = lambda *a, **k: 'water'
    s = plain_spot(); K.decide(s, {'US-1': {'ids': ['a']}, 'US-2': {'ids': ['b']}}, {}, {},
                               {'US-1': ('One', LAT0, LON0), 'US-2': ('Two', LAT0, LON0)}, '2026-11-19', set(), lambda r: 'US-ZZ')
    rows_settled.append(s)
    check(str(s.get('status')).startswith('water only') and s.get('made_on'), f'a water-only row carries made_on ({s.get("status")!r})')
with quiet_decide():
    K.ownership_step = lambda *a, **k: ('not sure', 'the owner maps disagree')
    s = plain_spot(); K.decide(s, {'US-1': {'ids': ['a']}, 'US-2': {'ids': ['b']}}, {}, {},
                               {'US-1': ('One', LAT0, LON0), 'US-2': ('Two', LAT0, LON0)}, '2026-11-19', set(), lambda r: 'US-ZZ')
    rows_settled.append(s)
    check(str(s.get('status')).startswith('not sure') and s.get('made_on'), f'a not-sure row carries made_on ({s.get("status")!r})')
K.KNOWN_LIVE[('US-1', 'US-2')] = 'the owner activated it in person'
with quiet_decide():
    s = plain_spot(); K.decide(s, {'US-1': {'ids': ['a']}, 'US-2': {'ids': ['b']}}, {}, {},
                               {'US-1': ('One', LAT0, LON0), 'US-2': ('Two', LAT0, LON0)}, '2026-11-19', set(), lambda r: 'US-ZZ')
    rows_settled.append(s)
    check(s.get('status') == 'candidate' and s.get('known') and s.get('made_on'), 'the owner\'s known answer carries made_on')
K.KNOWN_LIVE.pop(('US-1', 'US-2'), None)
dropped = plain_spot()
dropped['status'] = 'dropped in pass 3: the finer official outlines show no shared patch here (the first, coarse look overlapped by drawing error only)'
K._stamp_row(dropped, {}, {}, lambda r: 'US-ZZ')
rows_settled.append(dropped)
check(dropped.get('made_on'), 'a row dropped in pass 3 carries made_on')
K.CURG.clear(); K.CURLN.clear()
AGE.NOT_CARRIED.clear(); AGE.KEY_ONLY.clear()
kept = AGE.keep_fresh(rows_settled, 'US-ZZ', root=str(root))
check(kept == rows_settled and len(AGE.KEY_ONLY) == len(rows_settled),
      f'a later run that does not read those parks keeps every stamped row and counts the key-only check ({len(kept)}, {len(AGE.KEY_ONLY)})')
K.CURG['US-1'] = [[[LON0, LAT0], [LON0 + 1, LAT0], [LON0 + 1, LAT0 + 1], [LON0, LAT0]]]
AGE.NOT_CARRIED.clear()
check(AGE.keep_fresh([rows_settled[0]], 'US-ZZ', root=str(root)) == [],
      'when this run has the park\'s outline and it differs, the row is not copied')
K.CURG.clear()

# the old-file list reads the mark, and only this run's region
markdir = TD / 'marks'; markdir.mkdir()
(markdir / 'US-WA.json').write_text(json.dumps({'st': 'US-WA', 'written_by_rule': 'R-2F4', 'spots': [{'status': 'pass 1'}]}))
(markdir / 'US-OR.json').write_text(json.dumps({'st': 'US-OR', 'spots': [{'status': 'candidate'}]}))
(markdir / 'W-FR.json').write_text(json.dumps({'st': 'W-FR', 'spots': [{'status': 'candidate'}]}))
(markdir / 'report-x.json').write_text('{}')
check(AGE.old_system_areas(markdir, 'na') == ['US-OR'],
      f'the list is the unmarked areas of this region ({AGE.old_system_areas(markdir, "na")})')
check(AGE.old_system_areas(markdir, 'world') == ['W-FR'], 'a world run lists world files only')

# --- R-2F5 a separate piece (KA-13, KA-14, KA-15) ---
check('FINE_GAP_M' not in src and 'KPC_FERS_FINE_100M' not in src and 'FINE_100M' not in src, 'KA-15 no distance in metres between spots')
listed = {'refs': ['US-1', 'US-2'], 'kind': 'area', 'box': [LON0, LAT0, LON0 + .0002, LAT0 + .0002]}
far = {'refs': ['US-1', 'US-2'], 'kind': 'area', 'wide_m': 30, 'box': [LON0 + .02, LAT0, LON0 + .0202, LAT0 + .0002]}
apart = {'refs': ['US-1', 'US-2'], 'kind': 'area', 'wide_m': 30, 'box': [LON0 + .0006, LAT0, LON0 + .0008, LAT0 + .0002]}
touch = {'refs': ['US-1', 'US-2'], 'kind': 'area', 'wide_m': 30, 'box': [LON0 + .0001, LAT0, LON0 + .0004, LAT0 + .0002]}
small = {'refs': ['US-1', 'US-2'], 'kind': 'area', 'wide_m': 15, 'box': [LON0 + .02, LAT0, LON0 + .0202, LAT0 + .0002]}
check(K.fine_own_row(far, [listed]), 'a 30 m piece whose box does not meet a listed spot is its own row')
own, why = K.fine_piece(touch, [listed])
check(not own and 'box meets' in why, f'KA-14 a piece whose box meets a listed spot is not a new row ({why})')
own, why = K.fine_piece(small, [listed])
check(not own and '25 yards' in why, f'KA-14 a 15 m piece is never a row ({why})')
bare = {'refs': ['US-1', 'US-2'], 'kind': 'area', 'center': [LAT0, LON0]}
own, why = K.fine_piece(far, [bare])
check(not own and 'no shape' in why, f'KA-14 a listed row with no shape is not given a new row ({why})')

# --- R-2F7 the paperwork (KA-19, KA-20) ---
check('THIN_SHELF' not in store_src and 'KPC_FERS_SHELF_MIN' not in store_src, 'KA-19 the floor is gone from the code')
scope = json.loads((HERE / '.github/fers-rule-scope.json').read_text())
by_id = {c['id']: c for c in scope['changes']}
check(by_id['2026-11-17-d10-tripwire-not-sure']['approved'].startswith('APPROVED, decided_by KPC owner, 2026-11-19')
      and 'D10 yes' in by_id['2026-11-17-d10-tripwire-not-sure']['approved'], 'KA-19 D10 is approved with the owner\'s 19 Nov words')
check(by_id['2026-11-17-thin-shelf']['approved'].startswith('NOT APPROVED: replaced by 2026-11-19-shelf-no-floor'),
      'KA-19 the thin-shelf entry is kept and marked not approved')
shelf = TD / 'shelf'
shelf.mkdir()
(shelf / 'index-US-ZZ.json').write_text(json.dumps({'coverage': {'parks_on_shelf': 5, 'parks_in_store': 50, 'share': 0.1}}))
line = KS.Store(shelf, max_days=100000, today='2026-11-19').shelf_line('US-ZZ')
check(line == 'US-ZZ: 5 of 50 parks on the shelf; 2-fers are measured only between those.', f'KA-20 the report line is the counts ({line!r})')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
