#!/usr/bin/env python3
"""KPC owner, 2026-11-13: kpc_fers_store.py (2-fer outlines from the outline store; prep, OFF by default).
Offline: proxy variables dropped, every socket connect refused. A synthetic store (format 1) is built in a temp folder.
Checks: the switch is off by default and install() then changes nothing; the reader verifies checksums; the store gives
download()'s own form (one group per record, rings of 3+ points, use=false records left out and listed, part boxes applied);
a missing park / record / area, a stale area and a WDPA-looking record hold the park (never a download); same_geometry_as;
the real kpc_fers module switched on reads outlines from the store with no network and never loads the national saved copy;
the change list; the rules hashes do not move (the module is not a rule file)."""
import gzip, hashlib, json, os, pathlib, socket, subprocess, sys, tempfile

for k in list(os.environ):
    if 'proxy' in k.lower(): os.environ.pop(k)
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
OPENED = []
class _NoNet(socket.socket):
    def connect(self, a, *k): OPENED.append(a); raise OSError('test: no network')
    def connect_ex(self, a, *k): OPENED.append(a); raise OSError('test: no network')
socket.socket = _NoNet
def _cc(a, *k, **kw): OPENED.append(a); raise OSError('test: no network')
socket.create_connection = _cc

FAILS = []
def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok: FAILS.append(what)

import kpc_fers_store as S  # noqa: E402

# ---------------------------------------------------------------- a synthetic store, format 1
def enc(ring):
    out, px, py = [], 0, 0
    for i, (x, y) in enumerate(ring):
        X, Y = int(round(x * 1e6)), int(round(y * 1e6))
        out += [X, Y] if i == 0 else [X - px, Y - py]; px, py = X, Y
    return out

def sq(x0, y0, d):
    return [[x0, y0], [x0 + d, y0], [x0 + d, y0 + d], [x0, y0 + d], [x0, y0]]

def rec(key, rings, use=True, **kw):
    e = [enc(r) for r in rings]
    return {'key': key, 'layer': kw.pop('layer', 'sgzza'), 'record_id': key, 'record_name': kw.pop('name', key), 'licence': kw.pop('licence', ''),
            'source': 'live', 'use': use, 'q': 6, 'rings': e, 'points': sum(len(x) // 2 for x in e), 'sha256': S.geometry_sha256(e), **kw}

def build(d, area, parks, made='2026-11-13'):
    d.mkdir(parents=True, exist_ok=True)
    fn = f'{area}.kpcstore.json.gz'; raw = bytearray(); idx = {}
    head = gzip.compress(json.dumps({'kpcstore': 1, 'area': area})[:-1].encode() + b', "parks": [', mtime=0)
    raw += head
    for i, p in enumerate(parks):
        b = gzip.compress(((',' if i else '') + json.dumps(p)).encode(), mtime=0)
        fp = hashlib.sha256('|'.join(str(r.get('sha256')) for r in p['records']).encode()).hexdigest()
        idx[p['ref']] = {'file': fn, 'o': len(raw), 'n': len(b), 'grade': p.get('grade', 'official'), 'circle': False,
                         'records': [r['key'] for r in p['records']], 'points': sum(r['points'] for r in p['records']), 'fp': fp, 'date': made}
        raw += b
    raw += gzip.compress(b']}', mtime=0)
    (d / fn).write_bytes(bytes(raw))
    (d / f'index-{area}.json').write_text(json.dumps({'format': 1, 'area': area, 'made': made + 'T00:00:00-06:00', 'parks': idx}), encoding='utf-8')

tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-fers-store-'))
big, small = sq(-80.0, 40.0, 0.01), sq(-79.996, 40.004, 0.002)
P = [{'ref': 'US-9001', 'name': 'Big Test Forest', 'grade': 'official', 'records': [rec("sgzza1", [big, [[-80, 40], [-79.99, 40]]]), rec('901', [sq(-79.97, 40.0, 0.001)], use=False, use_why='easement')]},
     {'ref': 'US-9002', 'name': 'Small Test Park', 'grade': 'official', 'records': [rec('sgzza2', [small]), {**rec('sgzzb2', [small]), 'rings': None, 'same_geometry_as': 'sgzza2'}]},
     {'ref': 'US-9003', 'name': 'Odd Park', 'grade': 'official', 'records': [rec('sgzza3', [sq(-79.9, 40.1, 0.001)], layer_url='https://example.invalid/WDPA_layer/0')]},
     {'ref': 'US-9004', 'name': 'Far Park', 'grade': 'official', 'records': [rec('sgzza4', [sq(-79.0, 41.0, 0.001)])]}]
build(tmp / 'store', 'US-ZZ', P)
# the gzip members must join into one valid JSON document (format 1: the whole area file reads with any gzip + JSON tool)
whole = json.loads(gzip.decompress((tmp / 'store' / 'US-ZZ.kpcstore.json.gz').read_bytes()))
check(whole['kpcstore'] == 1 and [p['ref'] for p in whole['parks']] == ['US-9001', 'US-9002', 'US-9003', 'US-9004'], 'fixture: the synthetic area file is one valid JSON document (format 1)')

# ---------------------------------------------------------------- switch
check(S.mode({}) == 'off' and S.mode({'KPC_FERS_FROM_STORE': 'maybe'}) == 'off' and S.mode({'KPC_FERS_FROM_STORE': ' ON '}) == 'on', 'switch: off by default, only 1 / on / yes / true turn it on')
class Fake: pass
F = Fake(); F.download = 'orig-dl'; F.saved_us = 'orig-su'; F.saved_ca = 'orig-sc'; F.live_load = 'orig-ll'; F.REGION = 'na'
check(S.install(F, env={}) is False and (F.download, F.saved_us, F.saved_ca, F.live_load) == ('orig-dl', 'orig-su', 'orig-sc', 'orig-ll'), 'switch off: install() changes nothing in kpc_fers')
F.REGION = 'world'
check(S.install(F, env={'KPC_FERS_FROM_STORE': 'on'}) is False and F.download == 'orig-dl', 'switch on, world run: refused (world 2-fers wait), nothing changed')
F.REGION = 'ky'
check(S.install(F, env={'KPC_FERS_FROM_STORE': 'on'}) is False and F.download == 'orig-dl', 'switch on, Kentucky run: refused (own files), nothing changed')

# ---------------------------------------------------------------- reader + download form
st = S.Store(tmp / 'store', 45, today='2026-11-14')
g, left, why = st.groups_for('US-9001', 'US-ZZ', ['sgzza1', 901])
check(not why and len(g) == 1 and len(g[0]) == 1 and g[0][0][0] == [-80.0, 40.0] and len(g[0][0]) == 5, 'reader: one group per used record, the 2-point ring dropped (esri_rings), coordinates exact')
check(left and 'easement' in left[0], 'reader: a use=false record is left out and listed (pad_use / LEFT)')
g2, _, why2 = st.groups_for('US-9002', 'US-ZZ', ['sgzza2', 'sgzzb2'])
check(not why2 and len(g2) == 2 and g2[0] == g2[1], 'reader: same_geometry_as gives the earlier record\'s rings')
_, _, w = st.groups_for('US-9002', 'US-ZZ', ['sgzza2', 'sgzzc9'])
check('no record sgzzc9' in w, f'held: the key joins a record the store lacks ({w[:60]})')
_, _, w = st.groups_for('US-9003', 'US-ZZ', ['sgzza3'])
check('WDPA' in w, 'held: a WDPA-looking record is never a 2-fer source')
_, _, w = st.groups_for('US-9999', 'US-ZZ', ['x1'])
check('not in the outline store' in w, 'held: a park the store does not have')
_, _, w = st.groups_for('US-1', 'US-QQ', ['x1'])
check('cannot be read' in w and 'US-QQ' in st.why, 'held: an area with no store at all')
old = S.Store(tmp / 'store', 45, today='2027-02-01')
_, _, w = old.groups_for('US-9001', 'US-ZZ', ['sgzza1'])
check('days old' in w, f'held: a stale area store ({w[:70]})')
clipped, _, _ = st.groups_for('US-9001', 'US-ZZ', ['sgzza1'], clip=lambda rid, rs: [])
check(clipped is None, 'reader: the clip callback is applied (part boxes, rule B12)')
# a moved coordinate never passes
bad = json.loads(json.dumps(P[3])); bad['records'][0]['rings'][0][0] += 1
build(tmp / 'bad', 'US-ZZ', [bad])
_, _, w = S.Store(tmp / 'bad', 45, today='2026-11-14').groups_for('US-9004', 'US-ZZ', ['sgzza4'])
check('failed its check' in w, 'reader: a changed coordinate fails the checksum: held, never used')

# ---------------------------------------------------------------- compact holding + pairs + change list
lz = S.LazyOutlines(lambda r: st.groups_for(r, 'US-ZZ', [x['key'] for x in next(p for p in P if p['ref'] == r)['records'][:1]])[0] or [], ['US-9001', 'US-9002', 'US-9004'], budget=6)
_ = lz['US-9001']; _ = lz['US-9002']; _ = lz['US-9004']; _ = lz['US-9001']
check(len(lz) == 3 and 'US-9002' in lz and 'US-9003' not in lz and lz.unpacks == 4 and len(lz.cache) == 2, 'LazyOutlines: unpacks on use, keeps the point budget (an evicted park is unpacked again)')
check(S.grid_pairs({'a': [0, 0, 1, 1], 'b': [0.9, 0.9, 2, 2], 'c': [5, 5, 6, 6]}) == {('a', 'b')}, 'grid_pairs: only boxes that touch')
now, packed = S.memory_estimate(10_000_000)
check(now == 1_320_000_000 and packed == 90_000_000 + 264_000_000, 'memory estimate: 132 B per point as lists, 9 B packed + the unpacked budget')
o = {'spots': [{'refs': ['US-1', 'US-2'], 'kind': 'area', 'status': 'candidate', 'center': [40.0, -80.0]}, {'refs': ['US-1', 'US-3'], 'kind': 'area', 'status': 'candidate', 'center': [40, -80]},
               {'refs': ['US-1', 'US-4'], 'kind': 'area', 'status': 'dropped in pass 3'}]}
n = {'spots': [{'refs': ['US-2', 'US-1'], 'kind': 'area', 'status': 'very tight: x', 'center': [40.01, -80.0]}, {'refs': ['US-1', 'US-4'], 'kind': 'area', 'status': 'candidate', 'center': [40, -80]}]}
d = S.diff_rows(o, n)
check(d['counts'] == {'same': 1, 'new': 1, 'gone': 1, 'moved': 1, 'status_changed': 1}, f'change list: same / new / gone / moved / status changed ({d["counts"]})')
check('shape' not in json.dumps(d), 'change list: ids, names and statuses only, no shapes')

# ---------------------------------------------------------------- the real 2-fer module, switched on (needs numpy + cv2 like kpc_fers.py)
try:
    import numpy, cv2  # noqa: F401
    have = True
except Exception: have = False  # noqa: BLE001
if not have: print('SKIP real kpc_fers check (numpy / cv2 not installed here)')
else:
    work = tmp / 'run'; work.mkdir()
    cwd = os.getcwd(); os.chdir(work)
    try:
        os.environ['REGION'] = 'na'; os.environ['PASS'] = '2'
        import kpc_fers as KF
        env = {'KPC_FERS_FROM_STORE': 'on', 'KPC_FERS_STORE_DIR': str(tmp / 'store'), 'KPC_FERS_STORE_MAX_DAYS': '100000'}
        orig = KF.download
        check(S.install(KF, env=env) is True and KF.download is not orig, 'switch on: download() is replaced in this process only')
        parks = {'US-9001': {'st': 'US-ZZ', 'ids': ['sgzza1', 901], 'names': {}}, 'US-9002': {'st': 'US-ZZ', 'ids': ['sgzza2'], 'names': {}},
                 'US-9005': {'st': 'US-ZZ', 'ids': ['sgzza5'], 'names': {}}}
        G, badset = KF.download(parks, sorted(parks), 0.0002, 5)
        check(set(G) == {'US-9001', 'US-9002'} and badset == {'US-9005'}, f'switch on: outlines from the store; the missing park is held ({sorted(G)}, {sorted(badset)})')
        check('outline store' in KF.saved_missing_why('US-9005') and 'US-9005' in S.FLAGS, 'switch on: the held park has its reason (listed, flagged for the store filler)')
        check(str(KF.MAPDATE.get('US-9001', '')).startswith('outline store'), 'switch on: the map date says outline store')
        check(KF.saved_us({}) == {} and not KF.SAVED_STR, 'switch on: the national saved key copy is never loaded')
        KF.live_load('zz')
        check(KF.LIVE_FILE is None and KF.LIVE == {}, "switch on: the bot's own saved-live copy is not read or written (one door in)")
        check(not OPENED, f'no network: no connection was attempted ({OPENED[:2]})')
    finally:
        os.chdir(cwd)

# ---------------------------------------------------------------- hashes
import kpc_key_freeze as KFZ  # noqa: E402
check('kpc_fers_store.py' in KFZ.NOT_RULES and not any('kpc_fers_store' in f for v in KFZ.RULE_FILES.values() for f in v), 'kpc_fers_store.py is listed in NOT_RULES and is in no rule list (no rules hash moves)')
want = {'us-key': 'd4ebfafce438', 'ca-key': 'ba480fa34fb6', 'world-key': '158325de87ce', 'fers': 'cef323de4c9a'}
try:
    import kpc_preflight as PF
    want = {k: PF.newest_hash(k) or v for k, v in want.items()}
except Exception: pass  # noqa: BLE001
got = {k: KFZ.rules_hash(k) for k in want}
check(got == want, f'rules hashes are the newest changelog hashes, unchanged by this module ({got})')
src = (ROOT / '.github' / 'scripts' / 'kpc_fers_store.py').read_text(encoding='utf-8')
check('urlopen' not in src and 'requests' not in src and 'http.client' not in src and '://' not in src, 'the module has no network code and names no host')
print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
