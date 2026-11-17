#!/usr/bin/env python3
"""Handoff 9 (the KPC owner's 2-fer fix list, 2026-11-17): the eight bugs and the owner-question settings. Offline, no network.
Every check below FAILS on main 36dc58cf (the fix is not there) and passes with it.
 1a a crash in the US water / closed-area check is NOT SURE ('water/closed-area check failed'), never a candidate
 1b the PAD-US closed-area map gives no answer -> the row is NOT SURE ('closed areas not checked'); an answer of 'nothing closed' still passes
 1c a pair test that crashes is counted, listed in the private folder, and its area's receipt says 'not finished' (red), never 'measured'
 1d a park whose outline could not be read makes its area's receipt say 'not finished' and names the count
 2  owner ruling N3 / Q3: KPC_FERS_NEAR_LINE_M (OFF = 0): a measured width within the band of the 25-yard or 50-yard line is NOT SURE;
    the real 5 m grid on made-up squares (Handoff 6 WL3 script) and the 472 old rows near a line (WL3 CSV) are the proof
 3  D10 on the PC runner: the runner and the area runner point the bot at KPC-Data's not-sure list; a missing list prints a warning
 4  Q4: KPC_FERS_CARRY_MAX=key (OFF): a carried row from an older key build is not carried (stamp, or checked before the build date)
 5  the public report keeps the problem COUNT; the full list goes to the private folder
 6  world designation layers (UK national parks ...) get the 'May contain private land' rule like US designation lines
 8  KNOWN_LIVE / KY_DROP / SAME_LAND_PAIRS / MAPFIX come from .github/fers-rulings.json, unchanged, each with a date and who ruled
 Q1 KPC_FERS_SUMMARY_APPROX (OFF): a summary-map-only outline is approximate; Q2 KPC_FERS_FED_NEIGHBOUR (OFF): park/refuge x
    national forest is NOT SURE unless one is a designation; Q5 the 100 m rule for fine-grid rows; Q6 KPC_FERS_STRIP_HELD (OFF)"""
import argparse, contextlib, csv, io, json, math, os, pathlib, sys, tempfile, types
HERE = pathlib.Path(__file__).resolve().parent.parent
S = HERE / '.github/scripts'
sys.path.insert(0, str(S)); sys.path.insert(0, str(HERE / 'tools/pc-runner'))
os.environ['PASS'] = '3'
os.environ['HTTP_CACHE'] = ''
for k in ('KPC_FERS_NOT_SURE', 'KPC_FERS_NEAR_LINE_M', 'KPC_FERS_CARRY_MAX', 'KPC_FERS_SUMMARY_APPROX', 'KPC_FERS_FED_NEIGHBOUR',
          'KPC_FERS_STRIP_HELD', 'KPC_FERS_NOT_SHOWN_DIR', 'KPC_FERS_PRIVATE_OUT', 'KPC_FERS_PRIVATE_LOG', 'KPC_FERS_FROM_STORE'):
    os.environ.pop(k, None)
try:
    import numpy  # noqa: F401
    import cv2  # noqa: F401
    HAVE = True
except Exception:  # noqa: BLE001
    HAVE = False
if not HAVE:
    print('SKIP numpy / cv2 not installed here (the rules check installs them)'); sys.exit(0)
TD = pathlib.Path(tempfile.mkdtemp(prefix='kpc-h9-'))
PRIV = pathlib.Path(tempfile.mkdtemp(prefix='kpc-h9-private-'))
os.chdir(TD)
import kpc_fers as K
import kpc_fers_age as AGE
import kpc_fers_key_status as FKS
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg, flush=True); ok = ok and bool(c)


src = (S / 'kpc_fers.py').read_text(encoding='utf-8')
LAT0, LON0 = 37.5, -84.0
KX, KY = 111320 * math.cos(math.radians(LAT0)), 110574


def rect(x0, y0, x1, y1, ang=0):
    a = math.radians(ang); out = []
    for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]:
        xr, yr = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        out.append([LON0 + xr / KX, LAT0 + yr / KY])
    return [[out]]


def two_parks(w, ang=0, off=0.0, a='US-9901', b='US-9902'):
    """Handoff 6's WL3 grid test: park A ends w metres inside park B (an overlap w metres wide, 2 km long)."""
    A, B = rect(-2000, -1000, off + w, 1000, ang), rect(off, -1000, 2000, 1000, ang)
    pts = A[0][0] + B[0][0]
    return {a: A, b: B}, [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]


PIN = {'US-9901': ('Test Park A', LAT0, LON0, '', '', 'ZZ'), 'US-9902': ('Test Park B', LAT0, LON0 + .01, '', '', 'ZZ')}
PARKS = {'US-9901': {'st': 'US-ZZ', 'ids': ['sgzza1'], 'names': {}}, 'US-9902': {'st': 'US-ZZ', 'ids': ['sgzzb1'], 'names': {}}}
st_of = lambda r: (PARKS.get(r) or {}).get('st', '')


@contextlib.contextmanager
def offline_decide():
    """decide() with every outside lookup it makes before / after the checks under test answered offline."""
    saved = {n: getattr(K, n) for n in ('key_line_match', 'same_records_verdict', 'saved_missing_why', 'is_picture_trace', 'load_key_status',
                                        'pin_inside', 'nearest_access', 'access_pin', 'map_link', 'line_rows', 'how_checked', 'nhd_water', 'pad_closed')}
    sf = FKS.status_for
    K.key_line_match = lambda *a, **k: ''; K.same_records_verdict = lambda *a, **k: (); K.saved_missing_why = lambda r: ''
    K.is_picture_trace = lambda *a: False; K.load_key_status = lambda *a, **k: None; K.pin_inside = lambda *a: False
    K.nearest_access = lambda *a, **k: None; K.access_pin = lambda *a, **k: None; K.map_link = lambda *a, **k: ''
    K.line_rows = lambda *a, **k: None; K.how_checked = lambda *a, **k: None
    K.nhd_water = lambda box, live=True: []          # the water map answered: no water here
    K.pad_closed = lambda box: []                    # the closed-area map answered: nothing closed
    FKS.status_for = lambda r, a=None: 'official'
    try: yield
    finally:
        for n, v in saved.items(): setattr(K, n, v)
        FKS.status_for = sf


def spot(w=200.0, ang=0, off=0.0):
    G, box = two_parks(w, ang, off)
    sp = K.area_spots(G, ['US-9901', 'US-9902'], box)
    s = max(sp, key=lambda x: x['wide_m']) if sp else None
    if s is not None: s.setdefault('id', 'US-9901+US-9902@test')
    return G, s


def decided(s, G):
    K.decide(s, PARKS, G, {}, PIN, '2026-11-17', set(), st_of)
    return str(s.get('status') or '')


# ------------------------------------------------------------------ 1a / 1b
with offline_decide():
    G, s0 = spot(200)
    check(s0 is not None and s0['wide_m'] > 150, f'a 200 m overlap of two made-up parks is found by the real 5 m grid ({s0 and s0["wide_m"]} m)')
    s = json.loads(json.dumps(s0)); st = decided(s, G)
    check(st == 'candidate', f'control: both maps answer, nothing closed, no water -> candidate ({st!r})')
    real_lc = K.land_check
    def boom(*a, **k): raise RuntimeError('made-up crash in the water / closed-area check')
    K.land_check = boom
    s = json.loads(json.dumps(s0)); st = decided(s, G)
    K.land_check = real_lc
    check(st.startswith('not sure: water/closed-area check failed (RuntimeError)'), f'1a a crash in the US land check is NOT SURE, never a candidate ({st!r})')
    def no_answer(box): raise TimeoutError('PAD-US did not answer')
    K.pad_closed = no_answer
    s = json.loads(json.dumps(s0)); st = decided(s, G)
    check(st.startswith('not sure: closed areas not checked (the PAD-US closed-area map did not answer'), f'1b the closed-area map gave no answer -> NOT SURE ({st!r})')
    check('_closed_fail' not in s, '1b the inside mark never reaches a written row')
    K.pad_closed = lambda box: []
    check('s.pop(\'_closed_fail\', None)   # PAD-US is a US map' in src, '1b Canada keeps its own closed-area handling (the mark is dropped, as before)')

# ------------------------------------------------------------------ 1c a crashed pair
os.environ['KPC_FERS_PRIVATE_LOG'] = str(PRIV)
K.ONLY.clear(); K.ONLY.add('US-ZZ'); K.RUN_TAG = 'h9'
G, _ = two_parks(200)
counts = {'pairs tested': 0}
real_as = K.area_spots
def crash(*a, **k): raise ValueError('made-up crash in the pair test')
K.area_spots = crash
K.CRASHED_PAIRS.clear(); K.UNREAD_PARKS.clear(); K.TESTED.clear()
got = K.find_spots(G, {}, {('US-9901', 'US-9902')}, counts)
K.area_spots = real_as
check(got == [] and ('US-9901', 'US-9902') in K.CRASHED_PAIRS, f'1c the crashed pair is remembered ({K.CRASHED_PAIRS})')
check(counts.get('pair tests that crashed (not finished; listed in the private folder)') == 1, f'1c it is counted in the report ({counts})')
check(('US-9901', 'US-9902') not in K.TESTED, '1c pass 2-3: its rows wait for the next run (not tested = never "dropped in pass 3")')
K._ST_OF = st_of
K.write_receipt(counts, PARKS, G, set(), 'h9rules')
rc = json.loads((TD / 'data/fers/receipt-h9.json').read_text())
v = ((rc.get('passes') or {}).get('3') or {}).get('areas', {}).get('US-ZZ', '')
check(v.startswith('not finished: 1 pair test(s) crashed'), f'1c the area receipt says not finished ({v!r})')
check(K.RECEIPT.check(rc, ['3']) != [], '1c so the receipt check is red (exit 2), never "every pass measured"')
pf, pn = K.save_problems(['US-9901 + US-9902: made-up crash'])
doc = json.loads(pf.read_text()) if pf else {}
check(pf is not None and str(pf).startswith(str(PRIV)) and doc.get('pair tests that crashed') == [['US-9901', 'US-9902', 'ValueError: made-up crash in the pair test']],
      f'1c the crashed pair is listed in the private folder ({pf})')
# ------------------------------------------------------------------ 1d an unread park
K.CRASHED_PAIRS.clear(); K.UNREAD_PARKS.clear(); K.UNREAD_PARKS['US-9902'] = 'US-ZZ'
K.write_receipt(counts, PARKS, G, {'US-9902'}, 'h9rules')
rc = json.loads((TD / 'data/fers/receipt-h9.json').read_text())
v = ((rc.get('passes') or {}).get('3') or {}).get('areas', {}).get('US-ZZ', '')
check(v == 'not finished: 1 park outline(s) could not be read (listed for a person in the private folder)', f'1d one unread park: the receipt says so with the count ({v!r})')
check("UNREAD_PARKS.update({r: (parks.get(r) or {}).get('st') or '' for r in _open})" in src and src.count('UNREAD_PARKS.update(') == 2,
      '1d pass 1 (under the 20-park stop line) and passes 2-3 both record every unread park')
K.UNREAD_PARKS.clear()
check("_tp = {tuple(sorted(p_)) for p_ in TIMED_PAIRS} | {tuple(sorted(p_)) for p_ in CRASHED_PAIRS}" in src,
      '1c pass 1 carries a crashed pair\'s old rows like a pair skipped for time (never lost)')

# ------------------------------------------------------------------ 2 the size-line band (N3)
check(K.NEAR_LINE_M == 0 and K.near_line({'kind': 'area', 'wide_m': 25}) == '', '2 setting OFF by default: nothing changes (today\'s rows)')
slips, read45 = [], None
for w in (16, 18, 20):
    for ang in (0, 17, 45):
        for off in (0, 1.3, 2.6):
            _, s = spot(w, ang, off)
            if s is not None: slips.append((w, ang, off, s['wide_m'], K.near_line(s, 8)))
_, s46 = spot(46, 0, 0)
check(slips and all(n.startswith('near a size line') and 'the 25-yard line' in n for *_, n in slips),
      f'2 every 16-20 m overlap the 5 m grid lets past the 25-yard floor is NOT SURE with an 8 m band ({[(w, m) for w, _, _, m, _ in slips]})')
check(s46 is not None and K.near_line(s46, 8).startswith('near a size line') and 'the 50-yard line' in K.near_line(s46, 8),
      f'2 a true 46 m overlap read as {s46 and s46["wide_m"]} m is NOT SURE near the 50-yard line')
check(K.near_line({'kind': 'area', 'wide_m': 200}, 8) == '' and K.near_line({'kind': 'river', 'len_m': 25}, 8) == '', '2 a wide area row and a line row are not touched')
rows = list(csv.DictReader(open(HERE / 'tests/fixtures/fers-wl3-near-line-rows.csv', encoding='utf-8')))
area_rows = [r for r in rows if r['line'] in ('25-yard', '50-yard') and r['status'] != 'water only']
hit = [r for r in area_rows if K.near_line({'kind': 'area', 'wide_m': float(r['wide_m'])}, 8)]
check(len(rows) == 472 and len(hit) == len(area_rows), f'2 the old rows near the 25 / 50-yard lines all fall in the 8 m band ({len(hit)} of {len(area_rows)}; 472 in the CSV)')
check(not [r for r in area_rows if K.near_line({'kind': 'area', 'wide_m': float(r['wide_m'])}, 0)], '2 band 0 (off): none of them changes')
with offline_decide():
    _, s = spot(18, 17, 1.3)
    if s is None: _, s = spot(20, 0, 0)
    K.NEAR_LINE_M = 8.0
    st = decided(s, two_parks(18, 17, 1.3)[0])
    K.NEAR_LINE_M = 0.0
    check(st.startswith('not sure: near a size line'), f'2 with the setting on, decide() makes it NOT SURE ({st!r})')

# ------------------------------------------------------------------ 3 D10 on the PC runner
import kpc_pc_run as PC
kd = TD / 'kpcdata-elsewhere'
check(PC.tripwire_list(kd) is None, '3 no list in the KPC-Data checkout -> None (the runner prints a WARNING line)')
(kd / 'data/waiting/tripwires').mkdir(parents=True)
(kd / 'data/waiting/tripwires/not-sure.json').write_text(json.dumps({'parks': {'US-9901': ['T1']}}))
check(PC.tripwire_list(kd) == (kd / 'data/waiting/tripwires/not-sure.json').resolve(), '3 the runner finds the list in the KPC-Data checkout')
pcs = (HERE / 'tools/pc-runner/kpc_pc_run.py').read_text(encoding='utf-8')
check("env['KPC_FERS_NOT_SURE'] = str(nsl)" in pcs and 'WARNING: D10 is OFF for this run' in pcs, '3 the runner passes it to the bot (KPC_FERS_NOT_SURE) or warns')
import kpc_fers_area_run as AR
r = AR.Run(argparse.Namespace(links=str(TD), kpcdata=str(kd), python=None, tag='t', states='US-ZZ', region='na', store='off', dry_run=True))
check(r.env().get('KPC_FERS_NOT_SURE') == str(kd.resolve() / 'data/waiting/tripwires/not-sure.json'), '3 the area runner passes the list from a KPC-Data checkout anywhere')
K._TRIPWIRE.clear()
buf = io.StringIO()
with contextlib.redirect_stdout(buf): got = K.tripwire_parks(); K.tripwire_parks()
check(got == {} and buf.getvalue().count('D10 is off for this run') == 1, f'3 the bot warns once when no list is found ({buf.getvalue()[:90]!r})')
os.environ['KPC_FERS_NOT_SURE'] = str(kd / 'data/waiting/tripwires/not-sure.json'); K._TRIPWIRE.clear()
check(K.tripwire_parks() == {'US-9901': ['T1']}, '3 with the list passed, D10 reads it')
os.environ.pop('KPC_FERS_NOT_SURE'); K._TRIPWIRE.clear()

# ------------------------------------------------------------------ 4 never past a key rebuild
(TD / 'data/us-key').mkdir(parents=True, exist_ok=True)
(TD / 'data/us-key/index.json').write_text(json.dumps({'build': 'US-200', 'built': '2026-10-30 18:00 UTC'}))
AGE._BUILT.clear(); AGE.NOT_CARRIED.clear()
old_row = {'refs': ['US-9901', 'US-9902'], 'kind': 'area', 'status': 'candidate', 'checked': '2026-10-29', 'passes': [1, 1, 1]}
new_row = dict(old_row, checked='2026-11-02')
check(AGE.keep_fresh([old_row, new_row], 'US-ZZ') == [old_row, new_row], '4 setting OFF: every old row is carried as before')
os.environ['KPC_FERS_CARRY_MAX'] = 'key'
kept = AGE.keep_fresh([old_row, new_row, dict(old_row, key_build='US-199'), dict(old_row, key_build='US-200')], 'US-ZZ')
check(kept == [new_row, dict(old_row, key_build='US-200')], f'4 key: a row made before the Oct 30 build (or stamped with build US-199) is not carried ({len(kept)} of 4 kept)')
check(len(AGE.NOT_CARRIED) == 2 and 'before the key was rebuilt on 2026-10-30' in AGE.NOT_CARRIED[0]['why'], f'4 each one is listed with the reason ({AGE.NOT_CARRIED[:1]})')
x = {}; AGE.stamp(x, 'US-ZZ')
check(x == {'key_build': 'US-200'}, '4 a row decided while the setting is on carries its key build')
check(AGE.too_old(old_row, 'CA-ZZ').startswith('the CA-ZZ key build date could not be read'), '4 a key with no build date: not carried (fail closed)')
import kpc_fers_store as KS
new = {'st': 'US-ZZ', 'spots': []}
n = KS.carry_rows(new, {'st': 'US-ZZ', 'pass1': '2026-10-29', 'spots': [old_row]}, {})
check(n == 0, f'4 the store\'s carry_rows does not bring back a row from before the rebuild ({n})')
os.environ.pop('KPC_FERS_CARRY_MAX'); AGE.NOT_CARRIED.clear()
n = KS.carry_rows({'st': 'US-ZZ', 'spots': []}, {'st': 'US-ZZ', 'pass1': '2026-10-29', 'spots': [old_row]}, {})
check(n == 1, f'4 setting OFF: carry_rows brings it back as before ({n})')

# ------------------------------------------------------------------ 5 problems: count in public, list in private
check("problems=len(LOG))" in src and 'problems=LOG[:40]' not in src, '5 the public report keeps the problem count only')
check(doc.get('problems') == ['US-9901 + US-9902: made-up crash'] and pn == 1, '5 the full problem list is in the private folder')
os.environ.pop('KPC_FERS_PRIVATE_LOG')
check(K.private_file('problems') is None, '5 no private folder given -> nothing is written anywhere (only the count)')
os.environ['KPC_FERS_PRIVATE_LOG'] = str(HERE)   # inside a git work tree: refused
check(K.private_file('problems') is None, '5 a folder inside a git work tree is refused (it could be pushed)')
os.environ.pop('KPC_FERS_PRIVATE_LOG')

# ------------------------------------------------------------------ 6 world designation layers
reg = K.REGION; K.REGION = 'world'
wp = {'GB-0003': {'ids': [1], 'm': [[1, 'North York Moors', 'Natural England National Parks', 'name']]},
      'GB-0099': {'ids': [7], 'm': [[7, 'Howardian Hills', 'Natural England National Landscapes', 'name']]},
      'GB-0001': {'ids': [754], 'm': [[754, 'Cassop Vale SSSI', 'Natural England SSSI', 'pin inside']]}}
check(K.designation_only('GB-0003', wp) and K.designation_only('GB-0099', wp), '6 a UK national park and a national landscape are designation lines (the private-land note)')
check(not K.designation_only('GB-0001', wp), '6 a nature reserve layer is not')
K.REGION = reg
check('Natural England National Parks' in K.WORLD_DESIG and 'NRW Wales National Parks' in K.WORLD_DESIG, '6 the world layer kinds come from .github/fers-rulings.json')

# ------------------------------------------------------------------ 8 the rulings file
OLD = {'KNOWN_LIVE': {('US-0050', 'US-10105'): 'Mammoth Cave x Green River Wild River: Brandon activates it in person (ruling Oct 28 8:35 PM)'},
       'KY_DROP': {('US-1277', 'US-4484'): 'Cumberland Falls is state land beside Forest Service land (ruling Oct 27)',
                   ('US-1286', 'US-4484'): 'Natural Bridge is state land beside Forest Service land (ruling Oct 27)',
                   ('US-0686', 'US-4484'): 'Big South Fork is Park Service land beside Forest Service land (ruling Oct 27)',
                   ('US-3799', 'US-4484'): 'Burchell-Beech is KDFWR-owned (ruling Oct 27)',
                   ('US-4484', 'US-7964'): 'W.H. Martin is state nature preserve land (ruling Oct 27)',
                   ('US-12083', 'US-4484'): 'University of the Cumberlands WMA is private (ruling Oct 27)'},
       'SAME_LAND_PAIRS': [(('US-0703', 'US-3790'), 'Fort Heiman tract', 'Fort Heiman (Fort Donelson National Battlefield tract)')],
       'MAPFIX': {'US-0703': 'https://www.nps.gov/fodo/planyourvisit/maps.htm'}}
for name, val in OLD.items():
    check(getattr(K, name) == val, f'8 {name} is exactly what kpc_fers.py had in code (nothing a run makes changes)')
check(all(e.get('date') and e.get('ruled_by') for k in ('known_live', 'ky_drop', 'same_land_pairs', 'map_fix') for e in K.RULINGS[k]), '8 every entry has a date and who ruled')
check("KY_DROP = {('US-1277'" not in src and "KNOWN_LIVE = {('US-0050'" not in src, '8 the pairs are no longer written in the code')
bad = TD / 'rulings-broken.json'; bad.write_text('{"known_live": [{"pair": ["a", "b"], "why": "x"}]}')
try: K.load_rulings(bad); stopped = False
except SystemExit as e: stopped = e.code == 4
check(stopped, '8 a broken rulings file (an entry with no date / who) stops the bot loudly (exit 4)')
try: K.load_rulings(TD / 'missing.json'); stopped = False
except SystemExit as e: stopped = e.code == 4
check(stopped, '8 a missing rulings file stops the bot loudly (exit 4)')
import kpc_key_freeze as KFZ
check('.github/fers-rulings.json' in KFZ.RULE_FILES['fers'] and '.github/scripts/kpc_fers_age.py' in KFZ.RULE_FILES['fers'], '8 the rulings file and the age check are 2-fer rule files (a change moves the fers hash)')

# ------------------------------------------------------------------ Q1 summary-map outlines
K.SUMMARY_SG.clear(); K.SUMMARY_SG.update({'sgmtd': 'compilation', 'sgaki': 'register', '_': ''})
qp = {'US-4502': {'ids': ['sgmtd744']}, 'US-6823': {'ids': ['mid17']}, 'US-0822': {'ids': ['sgaki3']}, 'US-0030': {'ids': [12345, 'sgmtd1']}}
check(K.summary_only('US-4502', qp) and K.summary_only('US-6823', qp) and K.summary_only('US-0822', qp), 'Q1 compilation / Michigan project / register-only outlines are summary maps')
check(not K.summary_only('US-0030', qp), 'Q1 a park with one record of its agency\'s own land is not')
check(K.SUMMARY_APPROX is False and 'if SUMMARY_APPROX:' in src, 'Q1 setting KPC_FERS_SUMMARY_APPROX is OFF by default')
# ------------------------------------------------------------------ Q2 park / refuge x national forest
fp = {'US-0030': ('Grand Canyon National Park',), 'US-4430': ('Kaibab National Forest',), 'US-0056': ('Olympic National Park',),
      'US-4532': ('Olympic National Forest',), 'US-0046': ('Yosemite National Park',), 'US-1999': ('Merced Wild and Scenic River',),
      'US-8004': ('Swan River National Wildlife Refuge',), 'US-4502': ('Flathead National Forest',), 'US-1000': ('Some State Park',)}
nop = {r: {'ids': ['sgzz1']} for r in fp}
check(K.fed_neighbours(['US-0030', 'US-4430'], nop, fp) == 'Grand Canyon National Park x Kaibab National Forest', 'Q2 Grand Canyon NP x Kaibab NF is flagged')
check(K.fed_neighbours(['US-0056', 'US-4532'], nop, fp) and K.fed_neighbours(['US-8004', 'US-4502'], nop, fp), 'Q2 Olympic NP x NF and a refuge x forest are flagged')
check(K.fed_neighbours(['US-0046', 'US-1999'], nop, fp) == '' and K.fed_neighbours(['US-1000', 'US-4502'], nop, fp) == '', 'Q2 a designation laid on a park, and a state park, are not')
check(K.FED_NEIGHBOUR is False, 'Q2 setting KPC_FERS_FED_NEIGHBOUR is OFF by default')
# ------------------------------------------------------------------ Q5 the 100 m rule
row = {'refs': ['US-9901', 'US-9902'], 'center': [LAT0, LON0]}
far = {'refs': ['US-9901', 'US-9902'], 'kind': 'area', 'wide_m': 30, 'center': [LAT0 + .009, LON0]}   # about 1 km north
near = dict(far, center=[LAT0 + .0004, LON0])                                                     # about 44 m north
small = dict(far, wide_m=15)
check(K.fine_own_row(far, [row]) and not K.fine_own_row(near, [row]) and not K.fine_own_row(small, [row]),
      'Q5 a 30 m patch 1 km away is its own row; one 44 m away or under 25 yards across stays with its row')
check(K.fine_only_mode() == 'off' and K.FINE_100M is False and 'if FINE_100M and not fine_own_row(n, d.get(\'spots\', [])): continue' in src,
      'Q5 KPC_FERS_FINE_ONLY and KPC_FERS_FINE_100M are both OFF by default; with both on, the 100 m rule picks the rows')
# ------------------------------------------------------------------ Q6 strip a held park's outline from carried rows
KS.withheld_refs = lambda: {'US-9902'}
KF = types.SimpleNamespace(PASS=1, OUT=str(TD / 'data/fers'))
held_row = {'refs': ['US-9901', 'US-9902'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1], 'center': [LAT0, LON0],
            'acres': 50, 'shape': [[LON0, LAT0], [LON0 + .001, LAT0]], 'lines': [[1, 2]]}
d = {'st': 'US-ZZ', 'spots': []}; KS.carry_held_rows(KF, d, {'spots': [held_row]})
check(d['spots'] and 'shape' in d['spots'][0], 'Q6 setting OFF: the carried row is an exact copy, as before')
KS.STRIP_HELD = True
d = {'st': 'US-ZZ', 'spots': []}; KS.carry_held_rows(KF, d, {'spots': [held_row]})
x = d['spots'][0] if d['spots'] else {}
check(x and 'shape' not in x and 'lines' not in x and x.get('center') and x.get('acres') == 50 and x.get('held_outline', '').startswith('there may be a 2-fer here'),
      'Q6 KPC_FERS_STRIP_HELD=1: the withheld park\'s pieces leave the row; "there may be a 2-fer here" stays')
KS.STRIP_HELD = False
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
