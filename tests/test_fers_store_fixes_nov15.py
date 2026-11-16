#!/usr/bin/env python3
"""KPC owner, 2026-11-15: fixes after the first 2-fer trial on the real outline store (M1, M3 + M2, M4, M5, C1, C2, C7, C8, C9).
Offline; synthetic fixtures only (made-up squares, made-up refs US-99201..US-99231 filed under US-RI, made-up names).
M5  pass-to-pass matcher: a spot is never given to two rows; the best fit goes first (centre in the row's box, then overlap); a
    leftover spot of a pair whose row was dropped becomes a new row in pass 2 and a warning in pass 3
M3 + M2  OWNER RULE 'never worse': on a public store run a withheld park's rows of the previous public file are carried unchanged
    (marked 'not re-checked (outline held privately)', counted per area); no other row or file names the park
M1  a public store run whose neighbours hold many unpublishable parks does not stop in pass 1, and prints no record-id prefix
M4  kpc_fers_expected.py on a public store run leaves withheld parks out (counted only), through the store's redact + guard;
    no readable withheld list = no file
C1 far line parks not listed as held; C2 store wording; C7 the change list goes to the private folder; C8 no float overflow;
C9 the run's total of withheld parks"""
import gzip, hashlib, json, os, pathlib, shutil, subprocess, sys, tempfile, warnings

for k in list(os.environ):
    if 'proxy' in k.lower(): os.environ.pop(k)
ROOT = pathlib.Path(__file__).resolve().parent.parent
SCR = ROOT / '.github' / 'scripts'
sys.path.insert(0, str(SCR))
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok: FAILS.append(what)


import kpc_fers_store as S  # noqa: E402
try:
    import numpy as np, cv2  # noqa: F401
    HAVE = True
except Exception: HAVE = False  # noqa: BLE001
TMP = pathlib.Path(tempfile.mkdtemp(prefix='kpc-fers-fixes-'))

# ---------------------------------------------------------------- M5: the matcher (unit, on the real functions)
if HAVE:
    os.chdir(TMP)
    import kpc_fers as KF
    def row(i, refs, c, box, passes=(1, 0, 0)):
        return {'id': i, 'refs': refs, 'kind': 'area', 'center': list(c), 'box': list(box), 'passes': list(passes), 'status': 'pass 1'}
    def spot(refs, c, box, acres):
        return {'refs': refs, 'kind': 'area', 'center': list(c), 'box': list(box), 'acres': acres}
    P = ['US-99201', 'US-99202']
    # the DE case, made up: row A has a long L-shaped box (3.5 km); row B is small; spot b lies in both boxes (B's spot), spot a is A's own
    A = row('A', P, (39.19, -75.42), (-75.44, 39.18, -75.40, 39.20))
    B = row('B', P, (39.195, -75.405), (-75.407, 39.193, -75.403, 39.197))
    sb_ = spot(P, (39.195, -75.405), (-75.4068, 39.1932, -75.4032, 39.1968), 4.9)
    sa_ = spot(P, (39.1886, -75.4258), (-75.4290, 39.1860, -75.4230, 39.1910), 10.3)
    newk = {KF.key_of(sb_): [dict(sb_), dict(sa_)]}
    got = KF.match_rows([A, B], newk)
    ga, gb = got.get(id(A)), got.get(id(B))
    check(ga is not None and gb is not None and ga['acres'] == 10.3 and gb['acres'] == 4.9,
          f"M5: the row with the long box takes its own spot, the small row the spot in its box (A {ga and ga['acres']}, B {gb and gb['acres']})")
    newk2 = {KF.key_of(sb_): [dict(sb_)]}
    got2 = KF.match_rows([A, B], newk2)
    check(len(got2) == 1 and got2.get(id(B)) is not None, 'M5: one spot, two rows whose boxes touch it: it goes to ONE row (the better fit), never to both')
    main_like = [n for n in newk2[KF.key_of(sb_)] if KF.inter(KF.sbox(A), KF.sbox(n), 0.0005)]
    check(len(main_like) == 1, 'M5: (main gave that one spot to both rows: the row order decided, _used was never read)')
    C = row('C', P, (40.0, -75.0), (-75.01, 39.99, -74.99, 40.01))
    check(KF.match_rows([C], {KF.key_of(sb_): [dict(sb_)]}) == {}, 'M5: a row whose box touches no new spot takes none (dropped as before)')
    # centre first, then overlap
    D = row('D', P, (39.5, -75.5), (-75.52, 39.48, -75.48, 39.52))
    s_in = spot(P, (39.51, -75.51), (-75.512, 39.508, -75.508, 39.512), 1.0)
    s_big = spot(P, (39.53, -75.47), (-75.50, 39.50, -75.44, 39.56), 50.0)   # bigger overlap, centre outside D's box
    g3 = KF.match_rows([D], {KF.key_of(s_in): [dict(s_big), dict(s_in)]})
    check(g3.get(id(D), {}).get('acres') == 1.0, 'M5: the spot whose centre lies in the row\'s box goes first, even against a larger overlap')
    s_in2 = spot(P, (39.505, -75.505), (-75.515, 39.495, -75.495, 39.515), 9.0)
    g4 = KF.match_rows([D], {KF.key_of(s_in): [dict(s_in), dict(s_in2)]})
    check(g4.get(id(D), {}).get('acres') == 9.0, 'M5: of two spots with their centre in the box, the larger share of the boxes wins')
    # leftover spots: pass 2 -> a new row for pass 3; pass 3 -> a new row decided in pass 3 (grade of #204, D5)
    KF.PASS = 2
    d = {'spots': [dict(A, status='dropped in pass 2: x', passes=[1, 0, 0])]}
    nk = {KF.key_of(sa_): [dict(sa_)]}
    added, warned = KF.leftover_spots(d, nk, '2026-11-15')
    new = [x for x in d['spots'] if x['id'] != 'A']
    check(len(added) == 1 and added[0] is new[0] and warned == 0 and new and new[0]['passes'] == [1, 1, 0] and new[0]['status'] == 'pass 2' and not any(k.startswith('_') for k in new[0]),
          f'M5: pass 2: a spot no row took, of a pair whose row was dropped, becomes a new row for pass 3 ({added}, {new and new[0].get("passes")})')
    KF.PASS = 3; KF.LOG.clear()
    d3 = {'spots': [dict(A, status='dropped in pass 3: x', passes=[1, 1, 0])]}
    a3, w3 = KF.leftover_spots(d3, {KF.key_of(sa_): [dict(sa_)]}, '2026-11-15')
    check(len(a3) == 1 and w3 == 0 and len(d3['spots']) == 2 and a3[0]['passes'] == [1, 1, 1] and a3[0]['status'] == 'pass 3',
          'M5: pass 3: such a spot becomes a new row too (passes [1, 1, 1]; the caller decides it in pass 3), never only a warning')
    d3b = {'spots': [dict(A, status='dropped in pass 3: x', passes=[1, 1, 0]), {'id': KF.key_of(sa_) + '@%.3f,%.3f' % tuple(sa_['center']), 'refs': P, 'kind': 'area', 'status': 'dropped: x'}]}
    a3b, w3b = KF.leftover_spots(d3b, {KF.key_of(sa_): [dict(sa_)]}, '2026-11-15')
    check(a3b == [] and w3b == 1 and any('left over' in x for x in KF.LOG), 'M5: a leftover spot whose id is already a row cannot be added: a warning in the report (loud, a person looks)')
    d4 = {'spots': [dict(A, status='pass 3', passes=[1, 1, 1])]}
    check(KF.leftover_spots(d4, {KF.key_of(sa_): [dict(sa_)]}, '2026-11-15') == ([], 0), 'M5: no dropped row of the pair: nothing is added (as before)')
    # D5 (grade of #204): random cases, main's matcher against match_rows + leftover_spots, passes 2 and 3: the spots kept as rows
    import random
    rnd = random.Random(20261115)
    def rbox():
        x, y = rnd.uniform(-75.5, -75.4), rnd.uniform(39.1, 39.2); w, h = rnd.uniform(0.001, 0.05), rnd.uniform(0.001, 0.05)
        return (x, y, x + w, y + h)
    def mk(b): return [(b[1] + b[3]) / 2, (b[0] + b[2]) / 2]
    worse = more = same_n = 0
    for case in range(3000):
        for P_ in (2, 3):
            KF.PASS = P_
            rows = [dict(row(f'r{i}', P, (0, 0), b, passes=(1, 1, 0) if P_ == 3 else (1, 0, 0)), center=mk(b)) for i, b in enumerate(rbox() for _ in range(rnd.randint(1, 4)))]
            sps = [dict(spot(P, (0, 0), b, round(rnd.uniform(1, 50), 1)), center=mk(b)) for b in (rbox() for _ in range(rnd.randint(1, 4)))]
            main_kept = set()
            for r_ in rows:
                m_ = next((j for j, n_ in enumerate(sps) if KF.inter(KF.sbox(r_), KF.sbox(n_), 0.0005)), None)
                if m_ is not None: main_kept.add(m_)
            nk = {KF.key_of(sps[0]): [dict(x, _j=j) for j, x in enumerate(sps)]}
            asg = KF.match_rows(rows, nk)
            for r_ in rows:
                if id(r_) not in asg: r_['status'] = f'dropped in pass {P_}: x'
            dd = {'spots': rows}
            added, _w = KF.leftover_spots(dd, nk, '2026-11-15')
            new_kept = {n_['_j'] for n_ in asg.values()} | {sps.index(next(x for x in sps if x['center'] == g['center'] and x['box'] == g['box'])) for g in added}
            if len(new_kept) < len(main_kept): worse += 1
            elif len(new_kept) > len(main_kept): more += 1
            else: same_n += 1
    check(worse == 0, f'D5: 6,000 random cases (passes 2 and 3): match_rows + leftover_spots keep at least as many spots as main every time (fewer {worse}, more {more}, same {same_n})')
    KF.LOG.clear()
    # C8: the near-pairs distance no longer overflows when a park has no pixel in the frame
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        try:
            v = float((np.minimum(KF.dt(np.ones((5, 5), np.uint8), outside=1), 1e7) * 50.0).min()); ok8 = v > 100
        except Exception: ok8 = False  # noqa: BLE001
    check(ok8 and 'np.minimum(dt(1 - f.area(G[a]), outside=1), 1e7) * f.cell' in (SCR / 'kpc_fers.py').read_text(encoding='utf-8'),
          'C8: the near-pairs distance is clamped before the multiply (no overflow warning; a park with no pixel stays far)')
    os.chdir(ROOT)

# ---------------------------------------------------------------- M3 + M2: carry_held_rows (unit)
class FakeKF: pass
K = FakeKF(); K.PASS = 1; K.OUT = TMP / 'unit-data' / 'fers'
S.PRIVATE_LOG_DIR = TMP / 'unit-priv'; S.PRIVATE_LOG_DIR.mkdir()
S.HELD_PRIVATE.clear(); S.READ_OK.clear(); S.PRIVATE.clear(); S.CARRIED_PUBLIC.clear()
S.HELD_PRIVATE.update({'US-99210', 'US-99213'})
old = {'st': 'US-RI', 'spots': [
    {'id': 'w1', 'refs': ['US-99201', 'US-99210'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1], 'acres': 12.0, 'center': [41.6, -71.6]},
    {'id': 'w2', 'refs': ['US-99210', 'US-99211'], 'kind': 'trail', 'status': 'dropped in pass 3: x', 'passes': [1, 1, 0]},
    {'id': 'p1', 'refs': ['US-99201', 'US-99202'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1]}]}
d1 = {'st': 'US-RI', 'spots': [{'id': 'p1', 'refs': ['US-99201', 'US-99202'], 'kind': 'area', 'status': 'pass 1', 'passes': [1, 0, 0]},
                               {'id': 'x', 'refs': ['US-99213', 'US-99202'], 'kind': 'area', 'status': 'not sure: held: x', 'passes': [0, 0, 0]}]}
n1 = S.carry_held_rows(K, d1, old)
ids = [x['id'] for x in d1['spots']]
w1 = next(x for x in d1['spots'] if x['id'] == 'w1')
check(n1 == 2 and ids == ['p1', 'w1', 'w2'] and S.CARRIED['US-RI'] == 2 and S.CARRIED_LIVE['US-RI'] == 1,
      f'never worse: pass 1 carries every row of the old public file that names a withheld park (2, one live), and drops any other row naming one ({ids})')
check({k: v for k, v in w1.items() if k != 'store_held'} == old['spots'][0] and w1['store_held'] == S.HELD_TAG == 'not re-checked (outline held privately)',
      'never worse: a carried row is the old row unchanged, plus the mark "not re-checked (outline held privately)"')
check(S.CARRIED_PUBLIC == {'US-99210'} and S.withheld_refs() == {'US-99210', 'US-99213'} and S.secret_refs() == {'US-99210', 'US-99213'},
      'never worse: the full withheld set guards every file, and the push-check list is the same whole set, carried parks included (D3)')
check(not S._full_row({'refs': ['US-99201', 'US-99210'], 'kind': 'area', 'status': 'candidate'}) and S._full_row(old['spots'][0]),
      'never worse: only a full row (refs, kind, status, passes) is carried: an old row without passes would stop the passes (KPC-Store store_run test)')
K.PASS = 2
S.HELD_PRIVATE.clear(); S.CARRIED_PUBLIC.clear()   # pass 2 reads fewer parks: the side file keeps the withheld refs
p1file = json.loads(json.dumps(d1))
d2 = json.loads(json.dumps(d1)); next(x for x in d2['spots'] if x['id'] == 'w1')['status'] = 'not sure: changed in memory'
d2['spots'].append({'id': 'y', 'refs': ['US-99210', 'US-99202'], 'kind': 'area', 'status': 'pass 2', 'passes': [1, 1, 0]})
n2 = S.carry_held_rows(K, d2, p1file)
w1b = next(x for x in d2['spots'] if x['id'] == 'w1')
check(n2 == 2 and w1b['status'] == 'candidate' and 'y' not in [x['id'] for x in d2['spots']] and S.CARRIED_PUBLIC == {'US-99210'},
      'never worse: passes 2-5 put back the exact copies pass 1 wrote (a change made in memory is thrown away; a new row naming the park is left out)')
check(S.load_withheld(TMP / 'nothing-here') is None, 'M4: no withheld list in the private folder = None (the caller writes nothing)')
(TMP / 'badlist' / 'store-withheld').mkdir(parents=True); (TMP / 'badlist' / 'store-withheld' / 'x-p1.json').write_text('{')
check(S.load_withheld(TMP / 'badlist') is None, 'M4: a list that cannot be read = None (fail closed)')
# trial 2 (CT): a park pass 1 read from publishable records only (and named) is not withheld by a later pass that only holds its line
S.HELD_PRIVATE.clear(); S.CARRIED_PUBLIC.clear(); S.READ_OK.clear(); S.READ_OK_RUN.clear()
S.HELD_PRIVATE.update({'US-99214', 'US-99213'}); S.READ_OK.add('US-99214')   # pass 1: its outline read (publishable), its line record held
S.save_withheld_list('rok', 1)
S.HELD_PRIVATE.clear(); S.READ_OK.clear(); S.HELD_PRIVATE.update({'US-99214', 'US-99213'})   # pass 5: only the line is looked at
_before = set(S.withheld_refs())
S.READ_OK_RUN.update(S.read_ok_before('rok', 5))
check('US-99214' in _before and S.withheld_refs() == {'US-99213'} and S.read_ok_before('rok', 1) == set(),
      'one answer per park for the run: a park pass 1 read from publishable records only is not withheld in pass 5 (only earlier passes count)')
S.HELD_PRIVATE.clear(); S.CARRIED_PUBLIC.clear(); S.READ_OK_RUN.clear(); S.PRIVATE_LOG_DIR = None

# ---------------------------------------------------------------- C7: the change list is private
oldf, newf = TMP / 'old.json', TMP / 'new.json'
oldf.write_text(json.dumps(old)); newf.write_text(json.dumps(d1))
env = {k: v for k, v in os.environ.items() if not k.startswith('KPC_')}
r = subprocess.run([sys.executable, str(SCR / 'kpc_fers_store.py'), 'diff', '--old', str(oldf), '--new', str(newf), '--out', str(ROOT / 'tmp-change-list')],
                   capture_output=True, text=True, env=env)
check(r.returncode == 2 and not list(ROOT.glob('tmp-change-list*')), 'C7: diff --out inside a git work tree is refused (the list names parks)')
pv = TMP / 'c7-private'
r = subprocess.run([sys.executable, str(SCR / 'kpc_fers_store.py'), 'diff', '--old', str(oldf), '--new', str(newf), '--out', str(ROOT / 'tmp-change-list')],
                   capture_output=True, text=True, env=dict(env, KPC_FERS_PRIVATE_LOG=str(pv)))
check(r.returncode == 0 and (pv / 'tmp-change-list.md').is_file() and (pv / 'tmp-change-list.json').is_file() and not list(ROOT.glob('tmp-change-list*')),
      'C7: with KPC_FERS_PRIVATE_LOG set, the change list (.json + .md) goes to the private folder')


# ---------------------------------------------------------------- end to end: the real kpc_fers.py on a synthetic store
def enc(ring):
    out, px, py = [], 0, 0
    for i, (x, y) in enumerate(ring):
        X, Y = int(round(x * 1e6)), int(round(y * 1e6))
        out += [X, Y] if i == 0 else [X - px, Y - py]; px, py = X, Y
    return out


def sq(x0, y0, d): return [[x0, y0], [x0 + d, y0], [x0 + d, y0 + d], [x0, y0 + d], [x0, y0]]


def rec(key, rings, publishable=True):
    e = [enc(r) for r in rings]
    return {'key': key, 'layer': 'fixlayer', 'record_id': key, 'record_name': key, 'licence_class': 'OPEN' if publishable else 'NO TERMS STATED',
            'publishable': publishable, 'publish_basis': 'verified-row' if publishable else 'none', 'wdpa_derived': False,
            'private_reason': '' if publishable else 'made-up licence hold', 'source': 'live', 'use': True, 'q': 6, 'rings': e,
            'points': sum(len(x) // 2 for x in e), 'sha256': S.geometry_sha256(e)}


def build(d, area, parks, made='2026-11-15'):
    d.mkdir(parents=True, exist_ok=True)
    fn = f'{area}.kpcstore.json.gz'; raw = bytearray(); idx = {}
    raw += gzip.compress(json.dumps({'kpcstore': 1, 'area': area})[:-1].encode() + b', "parks": [', mtime=0)
    for i, p in enumerate(parks):
        b = gzip.compress(((',' if i else '') + json.dumps(p)).encode(), mtime=0)
        fp = hashlib.sha256('|'.join(str(r.get('sha256')) for r in p['records']).encode()).hexdigest()
        idx[p['ref']] = {'file': fn, 'o': len(raw), 'n': len(b), 'grade': 'official', 'circle': False, 'name': p['name'],
                         'records': [r['key'] for r in p['records']], 'points': sum(r['points'] for r in p['records']), 'fp': fp, 'date': made}
        raw += b
    raw += gzip.compress(b']}', mtime=0)
    (d / fn).write_bytes(bytes(raw))
    blob = (d / fn).read_bytes()
    (d / f'index-{area}.json').write_text(json.dumps({'format': 1, 'store_format_version': S.STORE_FORMAT_VERSION, 'area': area, 'made': made + 'T00:00:00-06:00',
                                                      'parks': idx, 'files': {fn: {'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()}}}), encoding='utf-8')


WITHHELD = [f'US-992{i:02d}' for i in range(10, 32)]   # 22 made-up parks whose only record is not publishable
WNAMES = {r: f'Zxq{chr(97 + i)}orra Marsh' for i, r in enumerate(WITHHELD)}
PARKS = {'US-99201': ('Fixture Forest', -71.60, 41.60, 0.01), 'US-99202': ('Fixture Inner Park', -71.597, 41.603, 0.004)}
for i, r in enumerate(WITHHELD): PARKS[r] = (WNAMES[r], -71.30 + 0.02 * i, 41.30, 0.003)
OLD_FILE = {'st': 'US-RI', 'pass3': '2026-11-01', 'spots': [
    {'id': 'old-p', 'refs': ['US-99201', 'US-99202'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1], 'checked': '2026-11-01',
     'center': [41.605, -71.595], 'box': [-71.597, 41.603, -71.593, 41.607], 'acres': 36.0, 'wide_m': 300, 'names': {'US-99201': 'Fixture Forest', 'US-99202': 'Fixture Inner Park'}},
    {'id': 'old-w', 'refs': ['US-99201', 'US-99210'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1], 'checked': '2026-11-01',
     'center': [41.601, -71.599], 'box': [-71.6, 41.6, -71.598, 41.602], 'acres': 8.0, 'wide_m': 120,
     'names': {'US-99201': 'Fixture Forest', 'US-99210': WNAMES['US-99210']}},
    {'id': 'old-d', 'refs': ['US-99211', 'US-99212'], 'kind': 'area', 'status': 'dropped in pass 3: the finer official outlines show no shared patch here', 'passes': [1, 1, 0],
     'center': [41.30, -71.27], 'box': [-71.28, 41.29, -71.26, 41.31]}]}


def layout(t):
    for d in ('data/parkinfo', 'data/trails', 'data/us-key', 'data/ca-key', 'data/canada-bounds', 'data/fers', 'cache/us', 'cache/ca', 'cache/fers'):
        (t / d).mkdir(parents=True, exist_ok=True)
    (t / 'data/trails/index.json').write_text('[]'); (t / 'data/trails/index-state.json').write_text('[]')
    pins, key, sp = {}, {}, []
    for n, (ref, (nm, x, y, w)) in enumerate(sorted(PARKS.items())):
        pins[ref] = [nm, '', 'State Park', '', '', y + w / 2, x + w / 2]
        key[ref] = {'g': 'official', 'm': [[99000 + n, nm, 1, 'name']]}
        sp.append({'ref': ref, 'name': nm, 'grade': 'official', 'records': [rec(str(99000 + n), [sq(x, y, w)], publishable=ref not in WITHHELD)]})
    (t / 'data/parkinfo/US-RI.json').write_text(json.dumps({'parks': pins}))
    (t / 'data/us-key/US-RI.json').write_text(json.dumps({'parks': key}))
    with gzip.open(t / 'cache/us/US-RI.json.gz', 'wt') as fh: json.dump({'saved': '2026-11-01', 'recs': []}, fh)
    (t / 'data/fers/US-RI.json').write_text(json.dumps(OLD_FILE))
    (t / 'data/fers/pota-pairs-US-RI.json').write_text(json.dumps({'pairs': {'US-99201+US-99210': 3, 'US-99201+US-99202': 2, 'US-99213+US-99214': 1}}))
    build(t / 'store', 'US-RI', sp)


WRAP = """import atexit, json, os, runpy, sys
TRIES = []
def _audit(ev, args):
    if ev in ('socket.connect', 'socket.getaddrinfo', 'socket.gethostbyname', 'urllib.Request'):
        TRIES.append(ev); open(os.environ['TRIES_OUT'], 'a').write(ev + '\\n'); raise OSError('test: no network')
sys.addaudithook(_audit)
S = sys.argv[1]; sys.path.insert(0, S)
def _dump():   # what keeper/fers_bot_run.py (KPC-Store) writes for its push check
    m = sys.modules.get('kpc_fers_store')
    if m is not None and m.STORE_ON:
        open(os.environ['EXPORT_OUT'], 'a').write(json.dumps({'pass': os.environ['PASS'], 'secret': sorted(m.secret_refs()), 'withheld': sorted(m.withheld_refs())}) + '\\n')
atexit.register(_dump)
sys.argv = [S + '/kpc_fers.py']
runpy.run_path(S + '/kpc_fers.py', run_name='__main__')
"""

if not HAVE:
    print('SKIP the real kpc_fers.py runs (numpy / cv2 not installed here)')
else:
    t = TMP / 'e2e'; t.mkdir(); layout(t)
    priv = TMP / 'e2e-private'
    (t / 'wrap.py').write_text(WRAP)
    e = {k: v for k, v in os.environ.items() if not k.startswith(('KPC_', 'PASS', 'MINUTES', 'STATES', 'REGION', 'RUN_TAG', 'PARKS', 'GITHUB_', 'WATER_STORE'))}
    e.update({'MINUTES': '5', 'STATES': 'US-RI', 'REGION': 'na', 'RUN_TAG': 'testri', 'KPC_FERS_LIVE_DIR': str(t / 'cache/fers'), 'KPC_FERS_FROM_STORE': 'on',
              'KPC_FERS_STORE_DIR': str(t / 'store'), 'KPC_FERS_STORE_MAX_DAYS': '100000', 'KPC_FERS_STORE_KIND': 'public', 'KPC_FERS_PRIVATE_LOG': str(priv),
              'TRIES_OUT': str(TMP / 'tries.txt'), 'EXPORT_OUT': str(TMP / 'export.jsonl')})
    outs = []
    for p in (1, 2, 3, 5):
        r = subprocess.run([sys.executable, '-B', str(t / 'wrap.py'), str(SCR)], cwd=t, env=dict(e, PASS=str(p)), capture_output=True, text=True, timeout=600)
        outs.append((p, r.returncode, r.stdout + r.stderr))
        if r.returncode: break
        if p == 1:   # the install() call site (D2): pretend pass 1 read US-99213 from publishable records only; later passes must keep that answer
            _l1 = priv / 'store-withheld' / 'testri-p1.json'
            if _l1.is_file(): _d1 = json.loads(_l1.read_text()); _d1['read_ok'] = sorted(set(_d1.get('read_ok') or []) | {'US-99213'}); _l1.write_text(json.dumps(_d1))
    log = '\n'.join(o for _, _, o in outs)
    check([rc for _, rc, _ in outs] == [0, 0, 0, 0] and not (TMP / 'tries.txt').is_file(),
          f'M1: 22 of 24 parks held for licence: passes 1, 2, 3 and 5 run (no "agency map did not answer" stop) with no network ({[(p, rc) for p, rc, _ in outs]})')
    check('id prefixes' not in log and 'outlines not read' not in log, 'M1: no record-id prefix (and no outlines-not-read stop) in the output')
    rep = json.loads((t / 'data/fers/report-testri.json').read_text())
    p1 = rep.get('pass1') or {}
    check(p1.get('parks held: outline not publishable (held privately, not named)') == 22 and 'parks held by the outline store' in p1 and 'parks read from the outline store' in p1
          and 'parks read live (saved for next time)' not in p1, f"C2: store words in the report ({ {k: v for k, v in p1.items() if 'held' in k or 'read' in k} })")
    ri = json.loads((t / 'data/fers/US-RI.json').read_text())
    held_rows = [x for x in ri['spots'] if set(x.get('refs') or []) & set(WITHHELD)]
    olds = {x['id']: x for x in OLD_FILE['spots']}
    check(len(held_rows) == 2 and all(x.get('store_held') == S.HELD_TAG and {k: v for k, v in x.items() if k != 'store_held'} == olds[x['id']] for x in held_rows),
          f"never worse (end to end): the withheld parks' two old public rows (a candidate and a dropped row) are in the new file unchanged, marked ({[x.get('id') for x in held_rows]})")
    pr = next((x for x in ri['spots'] if x.get('refs') == ['US-99201', 'US-99202'] and not str(x.get('status')).startswith('merged')), {})
    check(pr and not pr.get('store_held') and pr.get('passes') == [1, 1, 1], f"the publishable pair is tested again as usual ({pr.get('status')})")
    rx = S._ref_rx(WITHHELD)
    others = {f.name: f.read_text() for f in (t / 'data/fers').glob('*.json') if f.name != 'US-RI.json' and not f.name.startswith('pota-pairs-')}   # pota-pairs: this test's own input
    named = sorted(n for n, txt in others.items() if rx.search(txt) or any(w in txt for w in WNAMES.values()))
    rest = json.dumps([x for x in ri['spots'] if not x.get('store_held')]) + json.dumps({k: v for k, v in ri.items() if k != 'spots'})
    check(named == [] and not rx.search(rest) and not any(w in rest for w in WNAMES.values()),
          f'never worse + M4: no other row of the spot file and no other file names a withheld park, by ref or by name ({named})')
    sm = json.loads((t / 'data/fers/store-missing-testri.json').read_text())
    cr = sm.get('rows carried unchanged (' + S.HELD_TAG + ')') or {}
    check(cr.get('US-RI') == 2 and (sm.get('of them live rows') or {}).get('US-RI') == 1, f'never worse: the store-missing list counts the carried rows per area ({cr})')
    check(sm.get('withheld over the run (all passes so far, not named)') == 22, f"C9: the store-missing list gives the run's total of withheld parks ({sm.get('withheld over the run (all passes so far, not named)')})")
    ex = [json.loads(x) for x in (TMP / 'export.jsonl').read_text().splitlines()]
    check(ex and all(x['secret'] == x['withheld'] for x in ex) and set(ex[0]['secret']) == set(WITHHELD),
          'D3: the push-check list (secret_refs) is the whole withheld set in every pass, the carried parks included')
    check(ex and len(ex) == 4 and 'US-99213' in ex[0]['withheld'] and all('US-99213' not in x['withheld'] for x in ex[1:]),
          'call site (install): passes 2-5 keep pass 1\'s "read from publishable records only" answer (READ_OK_RUN from the private list)')
    lists = sorted(p.name for p in (priv / 'store-withheld').glob('*.json'))
    check(lists == ['testri-p1.json', 'testri-p2.json', 'testri-p3.json', 'testri-p5.json'] and len(json.loads((priv / 'store-withheld/testri-p1.json').read_text())['refs']) == 22,
          f'the full withheld list of each pass is in the private folder ({lists})')
    # M4: the expected-pairs file
    ee = dict(e); ee.pop('PASS', None)
    r = subprocess.run([sys.executable, str(SCR / 'kpc_fers_expected.py')], cwd=t, env=ee, capture_output=True, text=True, timeout=300)
    xf = t / 'data/fers/expected-testri.json'
    xt = xf.read_text() if xf.is_file() else ''
    xd = json.loads(xt) if xt else {}
    # KPC owner, 2026-11-15 23:14 (re-grade R2, 2026-11-16): a pair we LOOKED AT and did not show is no longer named in the
    # pushed file - only counted - and its reason waits for a person in the private folder. A pair in FOUND or NEVER LOOKED AT
    # (neither of which says a pair is not a 2-fer) is still named.
    pub_named = any(x['refs'] == ['US-99201', 'US-99202'] for v in ('FOUND', 'NEVER LOOKED AT') for x in xd.get(v) or [])
    dropped_file = priv / 'not-shown' / 'expected-dropped-testri.json'
    dropped_doc = json.loads(dropped_file.read_text()) if dropped_file.is_file() else {}
    pub_counted = (xd.get('counts') or {}).get('DROPPED', 0) >= 1 and any(
        x.get('refs') == ['US-99201', 'US-99202'] for x in dropped_doc.get('DROPPED') or [])
    check(xt and not rx.search(xt) and not any(w in xt for w in WNAMES.values()) and xd.get('withheld (pairs with a park whose outline is held privately: not named)') == 2
          and (pub_named or pub_counted) and xd.get('DROPPED') == [],
          f"M4: expected-<tag>.json leaves the withheld parks' pairs out (2 counted) and accounts for the public pair ({xd.get('counts')}, named={pub_named}, private={pub_counted})")
    xf.unlink(missing_ok=True)
    r = subprocess.run([sys.executable, str(SCR / 'kpc_fers_expected.py')], cwd=t, env=dict(ee, KPC_FERS_PRIVATE_LOG=str(TMP / 'empty-private')), capture_output=True, text=True, timeout=300)
    check(not xf.is_file() and 'not written' in r.stdout, 'M4: a public store run without a readable withheld list writes no expected file (fail closed)')
    r = subprocess.run([sys.executable, str(SCR / 'kpc_fers_expected.py')], cwd=t, env={k: v for k, v in ee.items() if not k.startswith('KPC_FERS')}, capture_output=True, text=True, timeout=300)
    check(xf.is_file() and 'withheld (pairs' not in xf.read_text(), 'M4: switch off: the expected file is written as before (no store step)')
    # D2: the matcher call sites in kpc_fers.main() (assign = match_rows ..., m = assign.get(id(s)), the leftover_spots call)
    t2 = TMP / 'e2e-m5'; t2.mkdir(); layout(t2)
    e2 = dict(e, KPC_FERS_LIVE_DIR=str(t2 / 'cache/fers'), KPC_FERS_STORE_DIR=str(t2 / 'store'), KPC_FERS_PRIVATE_LOG=str(TMP / 'e2e-m5-private'),
              EXPORT_OUT=str(TMP / 'export-m5.jsonl'))
    def run2(p):
        return subprocess.run([sys.executable, '-B', str(t2 / 'wrap.py'), str(SCR)], cwd=t2, env=dict(e2, PASS=str(p)), capture_output=True, text=True, timeout=600)
    (t2 / 'wrap.py').write_text(WRAP)
    r1 = run2(1)
    f2 = t2 / 'data/fers/US-RI.json'
    p1doc = json.loads(f2.read_text()) if f2.is_file() else {'spots': []}
    PP = ['US-99201', 'US-99202']
    real = [x for x in p1doc['spots'] if x.get('refs') == PP and x.get('kind') == 'area' and x.get('passes') == [1, 0, 0]]
    if r1.returncode or not real:
        check(False, f'D2 setup: pass 1 made a row of the public pair ({r1.returncode}, {len(real)})')
    else:
        # (a) a second row of the same pair over the same spot: main gave both rows that one spot; now exactly one row takes it
        dup = dict(real[0], id=real[0]['id'] + '-twin')
        f2.write_text(json.dumps(dict(p1doc, spots=p1doc['spots'] + [dup])))
        # KPC owner, 2026-11-16: a store run does not run pass 2 (same outlines in every pass); pass 3 takes the pass-1 rows, so the
        # call sites are tested in pass 3
        r2 = run2(3); d2 = json.loads(f2.read_text())
        st2 = sorted(str(x.get('status'))[:17] for x in d2['spots'] if x.get('id') in (real[0]['id'], dup['id']))
        # OWNER RULE 2026-11-15 23:14: the row that did not take the spot is no longer WRITTEN at all (nothing in a 2-fer file
        # ever says a pair is not a 2-fer). Exactly one row of the pair is in the file, and it is the one that took the spot.
        check(r2.returncode == 0 and len(st2) == 1 and not st2[0].startswith(('pass ', 'waiting', 'dropped')),
              f'call site (main): two rows over one spot: one row takes it and is decided, the other is not written, never both ({st2})')
        # (b) + (c) the pair's only row moved far away (its box touches no spot): the real spot becomes a new row of pass 3 and is
        # DECIDED there (D5); it is not lost
        far = dict(real[0], id=real[0]['id'] + '-far', center=[45.0, -70.0], box=[-70.01, 44.99, -69.99, 45.01])
        f2.write_text(json.dumps(dict(p1doc, spots=[x for x in p1doc['spots'] if x is not real[0] and x.get('id') != real[0]['id']] + [far])))
        r4 = run2(3); d4_ = json.loads(f2.read_text())
        m3 = [x for x in d4_['spots'] if x.get('refs') == PP and x.get('kind') == 'area' and 'decided in pass 3' in str(x.get('note'))]
        check(r4.returncode == 0 and len(m3) == 1 and m3[0]['passes'] == [1, 1, 1] and m3[0].get('status') not in ('pass 3', 'waiting for pass 3') and m3[0].get('checked'),
              f"call site (main): pass 3: the spot of a dropped row becomes a new row and is decided in pass 3 ({[(x.get('status'), x.get('passes')) for x in m3]})")
    # C1: a far line park is not listed
    check(S.NEAR_LINE_DEG == 1.0, 'C1: line parks more than about 100 km from the run\'s own pins are not listed as held (counted only)')
    class PK: PINS = {'US-1': ['a', 41.0, -71.0, '', '', 'RI'], 'US-2': ['b', 30.0, -90.0, '', '', 'LA']}
    near = S._near_run(PK, ['US-RI'])
    check(near({'lines': [[[-71.5, 41.5], [-71.4, 41.6]]]}) and not near({'lines': [[[-90.0, 30.0], [-89.9, 30.1]]]}) and near({'lines': [[[-90, 30], [-70.5, 41.2]]]}),
          'C1: a line near the run (or crossing it) counts; a line 2,000 km away does not')

# ---------------------------------------------------------------- the declared hash move (like #138)
import kpc_key_freeze as KFZ  # noqa: E402
import kpc_preflight as PF  # noqa: E402
_log = (ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
# KPC owner, 2026-11-15 (owner rule 12 public view, the next declared move e402c3819224 -> ...): this change's own line, wherever it
# now sits, and any later move starts from it; the newest line on top is checked by test_public_view_readers_nov15.py
_ln = next((x for x in _log.splitlines() if 'fers rules 2fe19a32e5eb -> e402c3819224' in x), '')
_o, _n, _ = PF.changelog_hashes(_ln, 'fers')
_i = _log.splitlines().index(_ln) if _ln else -1
check(_o == '2fe19a32e5eb' and _n == 'e402c3819224' and 'APPROVED, decided_by KPC owner, 2026-11-15' in _ln and _log.splitlines()[_i + 1].startswith('Why:')
      and (_n == KFZ.rules_hash('fers') or f'fers rules {_n} -> ' in _log), f'the store fixes moved the 2-fer hash by their own declared line with its Why line (2fe19a32e5eb -> e402c3819224); any later move starts from it ({KFZ.rules_hash("fers")})')
_sc = next(c for c in json.loads((ROOT / '.github/fers-rule-scope.json').read_text())['changes'] if c.get('id') == '2026-11-15-store-fixes')
check(_sc['id'] == '2026-11-15-store-fixes' and _sc['from'] == '2fe19a32e5eb' and _sc['scope'] == 'none' and _sc.get('approved') == 'APPROVED, decided_by KPC owner, 2026-11-15',
      'scope entry 2026-11-15-store-fixes (from 2fe19a32e5eb, scope none, approved)')
_k = {k: KFZ.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key')}
# KPC owner, 2026-11-16 (handoff item 6): a hash this change did not move is its pinned value OR the newest declared changelog hash
# (a later change may move it in its own declared line); not 'unchanged for ever'
check(all(_k[_x] in ({'us-key': 'd4ebfafce438', 'ca-key': 'ba480fa34fb6', 'world-key': '24cd942eca01'}[_x], __import__('kpc_preflight').newest_hash(_x)) for _x in _k), f'US, CA and world rules hashes do not move, or moved only by a later declared line ({_k})')
shutil.rmtree(TMP, ignore_errors=True)
print('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})')
sys.exit(1 if FAILS else 0)
