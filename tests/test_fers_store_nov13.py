#!/usr/bin/env python3
"""KPC owner, 2026-11-13: kpc_fers_store.py (2-fer outlines from the outline store; prep, OFF by default).
Offline: proxy variables dropped, every socket connect refused. Synthetic stores (format 1) are built in a temp folder.
Covers: switch off = nothing changes; the reader's checks; download()'s form; every kind of damage HOLDS (never a crash);
no half parks; WDPA anywhere in a record or park; licences (public store holds unpublishable parks, private store tags rows
club-room only); lazy holding (nothing unpacked at download, a points budget, a store changed mid-run is loud); the area gate
(missing / stale area stops before anything is saved: exit 87); the memory gate (exit 88, one row per area); no live pair
vanishes (carried rows); the join-review rule; corridors only from the saved copy; the change list; the real kpc_fers module
switched on; the rules hashes do not move.
2026-11-14 (review must-fixes): the write guard (club-room-only / private / world / never-released rows never reach a public file,
the run fails instead; a private run writes only into its private folder; kpc_fers_publish refuses them too); the writer trace;
the shut door (pad_closed asks nothing, zero network requests from the finder's pieces, sockets refused and counted); the R12 text
matches missing_list(); one row per pair (a merged narrow patch is never read as the pair's width). Store format 4: /3 and /4
read, /5 refused; area records only make outlines (lines, pins, unknown kinds left out and counted); line parks on today's
100-ft line rule (a trail across a park pairs, a trail 40 m outside does not; a wide river pairs from its bank tile, never from
its centre line); water tiles from the store; the river centre-line fallback switch, both settings."""
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

# ---------------------------------------------------------------- synthetic store, format 1
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
    return {'key': key, 'layer': kw.pop('layer', 'sgzza'), 'record_id': key, 'record_name': kw.pop('name', key), 'licence_class': kw.pop('licence_class', 'OPEN'),
            'publishable': kw.pop('publishable', True), 'publish_basis': kw.pop('publish_basis', 'verified-row'), 'wdpa_derived': kw.pop('wdpa_derived', False),
            'private_reason': kw.pop('private_reason', ''), 'source': 'live', 'use': use, 'q': 6, 'rings': e, 'points': sum(len(x) // 2 for x in e), 'sha256': S.geometry_sha256(e), **kw}

def build(d, area, parks, made='2026-11-13', member=None, index_edit=None):
    d.mkdir(parents=True, exist_ok=True)
    fn = f'{area}.kpcstore.json.gz'; raw = bytearray(); idx = {}
    raw += gzip.compress(json.dumps({'kpcstore': 1, 'area': area})[:-1].encode() + b', "parks": [', mtime=0)
    for i, p in enumerate(parks):
        b = gzip.compress(((',' if i else '') + json.dumps(p)).encode(), mtime=0)
        if member: b = member(p['ref'], b)
        fp = hashlib.sha256('|'.join(str(r.get('sha256')) for r in p['records']).encode()).hexdigest()
        idx[p['ref']] = {'file': fn, 'o': len(raw), 'n': len(b), 'grade': p.get('grade', 'official'), 'circle': False,
                         'records': [r['key'] for r in p['records']], 'points': sum(r['points'] for r in p['records']), 'fp': fp, 'date': made}
        raw += b
    raw += gzip.compress(b']}', mtime=0)
    (d / fn).write_bytes(bytes(raw))
    blob = (d / fn).read_bytes()
    doc = {'format': 1, 'store_format_version': S.STORE_FORMAT_VERSION, 'area': area, 'made': made + 'T00:00:00-06:00', 'parks': idx,
           'files': {fn: {'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()}}}
    if index_edit: doc = index_edit(doc)
    (d / f'index-{area}.json').write_text(json.dumps(doc), encoding='utf-8')
    return d

tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-fers-store-'))
big, small = sq(-80.0, 40.0, 0.01), sq(-79.996, 40.004, 0.002)
P = [{'ref': 'US-9001', 'name': 'Big Test Forest', 'grade': 'official', 'records': [rec('sgzza1', [big, [[-80, 40], [-79.99, 40]]]), rec('901', [sq(-79.97, 40.0, 0.001)], use=False, use_why='easement')]},
     {'ref': 'US-9002', 'name': 'Small Test Park', 'grade': 'official', 'records': [rec('sgzza2', [small]), {**rec('sgzzb2', [small]), 'rings': None, 'same_geometry_as': 'sgzza2'}]},
     {'ref': 'US-9003', 'name': 'Odd Park', 'grade': 'official', 'records': [rec('sgzza3', [sq(-79.9, 40.1, 0.001)], layer_url='https://example.invalid/WDPA_layer/0')]},
     {'ref': 'US-9004', 'name': 'Far Park', 'grade': 'official', 'records': [rec('sgzza4', [sq(-79.0, 41.0, 0.001)])]},
     {'ref': 'US-9006', 'name': 'Half Park', 'grade': 'official', 'records': [rec('sgzza6', [sq(-78.0, 41.0, 0.001)]), rec('sgzzb6', [[[-78, 41], [-78.001, 41]]])]},
     {'ref': 'US-9007', 'name': 'Hidden Words', 'grade': 'official', 'records': [rec('sgzza7', [sq(-78.5, 41.0, 0.001)], attributes={'SRC': 'from Protected Planet'})]},
     {'ref': 'US-9008', 'name': 'Park Note', 'grade': 'official', 'note': 'copied from wdpa', 'records': [rec('sgzza8', [sq(-78.6, 41.0, 0.001)])]},
     {'ref': 'US-9009', 'name': 'Private Park', 'grade': 'official', 'records': [rec('sgzza9', [sq(-79.995, 40.005, 0.001)], publishable=False, licence_class='NO TERMS STATED', publish_basis='none', private_reason='licence not read yet')]}]
build(tmp / 'store', 'US-ZZ', P)
whole = json.loads(gzip.decompress((tmp / 'store' / 'US-ZZ.kpcstore.json.gz').read_bytes()))
check(whole['kpcstore'] == 1 and len(whole['parks']) == len(P), 'fixture: the synthetic area file is one valid JSON document (format 1)')

# ---------------------------------------------------------------- switch
check(S.mode({}) == 'off' and S.mode({'KPC_FERS_FROM_STORE': 'maybe'}) == 'off' and S.mode({'KPC_FERS_FROM_STORE': ' ON '}) == 'on', 'switch: off by default, only 1 / on / yes / true turn it on')
class Fake: pass
F = Fake(); F.download = 'orig-dl'; F.saved_us = 'orig-su'; F.saved_ca = 'orig-sc'; F.live_load = 'orig-ll'; F.pc_tag = 'orig-pt'; F.REGION = 'na'
check(S.install(F, env={}) is False and (F.download, F.saved_us, F.saved_ca, F.live_load, F.pc_tag) == ('orig-dl', 'orig-su', 'orig-sc', 'orig-ll', 'orig-pt'), 'switch off: install() changes nothing in kpc_fers')
for reg in ('world', 'ky'):
    F.REGION = reg
    check(S.install(F, env={'KPC_FERS_FROM_STORE': 'on'}) is False and F.download == 'orig-dl', f'switch on, {reg} run: the store is not used and the bot runs as today (nothing replaced)')
r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_fers_store.py'), 'run'], capture_output=True, text=True, env={k: v for k, v in os.environ.items() if k != 'KPC_FERS_FROM_STORE'}, cwd=tmp)
check(r.returncode == 2 and 'is not on' in r.stdout, "the 'run' command refuses when the switch is off (it never runs the bot with downloads)")

# ---------------------------------------------------------------- reader + download form (private store: every park readable)
st = S.Store(tmp / 'store', 45, today='2026-11-14', kind='private')
g, left, why = st.groups_for('US-9001', 'US-ZZ', ['sgzza1', 901])
check(not why and len(g) == 1 and len(g[0]) == 1 and g[0][0][0] == [-80.0, 40.0] and len(g[0][0]) == 5, 'reader: one group per used record, the 2-point ring dropped, coordinates exact')
check(left and 'easement' in left[0], 'reader: a use=false record is left out and listed (pad_use / LEFT)')
g2, _, why2 = st.groups_for('US-9002', 'US-ZZ', ['sgzza2', 'sgzzb2'])
check(not why2 and len(g2) == 2 and g2[0] == g2[1], "reader: same_geometry_as gives the earlier record's rings")
def held(store, ref, ids, area='US-ZZ'): return store.groups_for(ref, area, ids)[2]
def _inside_dir(p, root):
    try: pathlib.Path(p).resolve().relative_to(pathlib.Path(root).resolve()); return True
    except ValueError: return False
check('no record sgzzc9' in held(st, 'US-9002', ['sgzza2', 'sgzzc9']), 'held: the key joins a record the store lacks')
check('half a park' in held(st, 'US-9006', ['sgzza6', 'sgzzb6']), 'held: a joined record with no usable ring holds the WHOLE park (never half a park)')
check('WDPA' in held(st, 'US-9003', ['sgzza3']), 'held: WDPA words in the layer address')
check('WDPA' in held(st, 'US-9007', ['sgzza7']), 'held: WDPA words hidden in the record attributes')
check('WDPA' in held(st, 'US-9008', ['sgzza8']), 'held: WDPA words at park level')
check('not in the outline store' in held(st, 'US-9999', ['x1']), 'held: a park the store does not have')
check('cannot be read' in held(st, 'US-1', ['x1'], 'US-QQ'), 'held: an area with no store at all')
check('days old' in held(S.Store(tmp / 'store', 45, today='2027-02-01', kind='private'), 'US-9001', ['sgzza1']), 'held: a stale area store')
check(st.groups_for('US-9001', 'US-ZZ', ['sgzza1'], clip=lambda rid, rs: [])[0] is None, 'reader: the clip callback is applied (part boxes, rule B12)')

# every kind of damage HOLDS with a reason (no exception escapes)
def corrupt(name, member=None, index_edit=None):
    d = build(tmp / ('d-' + name), 'US-ZZ', [P[3], P[1]], member=member, index_edit=index_edit)
    s = S.Store(d, 45, today='2026-11-14', kind='private')
    try: return held(s, 'US-9004', ['sgzza4']) or 'NOT HELD'
    except Exception as e: return f'CRASH {type(e).__name__}'  # noqa: BLE001
bad_gzip = lambda ref, b: (b[:10] + b'\x00\xff' * 8 + b[26:]) if ref == 'US-9004' else b
cut_json = lambda ref, b: gzip.compress(gzip.decompress(b)[:-7], mtime=0) if ref == 'US-9004' else b
no_trailer = lambda ref, b: b[:-8] if ref == 'US-9004' else b
def _drop_o(d): d['parks']['US-9004'].pop('o'); return d
def _not_obj(d): d['parks']['US-9004'] = 7; return d
cases = {'bad gzip piece': corrupt('gz', member=bad_gzip), 'cut-off JSON piece': corrupt('cut', member=cut_json), 'missing gzip trailer': corrupt('tr', member=no_trailer),
         'index is a list': corrupt('list', index_edit=lambda d: [d]), 'index entry without offset': corrupt('noo', index_edit=_drop_o),
         'index entry not an object': corrupt('nob', index_edit=_not_obj), 'store format 2': corrupt('fmt', index_edit=lambda d: {**d, 'format': 2})}
bad4 = json.loads(json.dumps(P[3])); bad4['records'][0]['rings'][0][0] += 1
build(tmp / 'd-coord', 'US-ZZ', [bad4]); cases['changed coordinate'] = held(S.Store(tmp / 'd-coord', 45, today='2026-11-14', kind='private'), 'US-9004', ['sgzza4'])
for k, v in cases.items():
    check(v != 'NOT HELD' and not v.startswith('CRASH'), f'damage held, never a crash: {k} ({v[:70]})')
check(not held(S.Store(tmp / 'd-noo', 45, today='2026-11-14', kind='private'), 'US-9002', ['sgzza2']), 'damage: one bad index entry holds only that park; the others are read')

# ---------------------------------------------------------------- licences
pub = S.Store(tmp / 'store', 45, today='2026-11-14', kind='public')
check('needs the private store' in held(pub, 'US-9009', ['sgzza9']), 'licence: on a PUBLIC store a park with a record not marked publishable is held "needs the private store"')
check(not held(pub, 'US-9001', ['sgzza1', 901]), 'licence: on a public store a publishable park is read')
_, _, w, info = st.examine('US-9009', 'US-ZZ', ['sgzza9'])
check(not w and info['private']['sgzza9']['licence_class'] == 'NO TERMS STATED' and info['private']['sgzza9']['private_reason'] == 'licence not read yet', 'licence: on the private store the park is used and its unpublishable records are named')
doc = {'spots': [{'refs': ['US-9001', 'US-9009'], 'kind': 'area', 'status': 'candidate'}, {'refs': ['US-9001', 'US-9002'], 'kind': 'area', 'status': 'candidate'}]}
check(S.tag_club_room(doc, {'US-9009': info['private']}) == 1 and doc['spots'][0]['club_room_only'] and 'club_room_only' not in doc['spots'][1], 'licence: a row that used an unpublishable outline is tagged club_room_only')

# ---------------------------------------------------------------- rows: carried, never vanished
old = {'pass3': '2026-10-29', 'spots': [{'refs': ['US-1', 'US-2'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1], 'center': [40, -80]},
                                        {'refs': ['US-1', 'US-3'], 'kind': 'area', 'status': 'very tight: x', 'passes': [1, 1, 1]},
                                        {'refs': ['US-1', 'US-4'], 'kind': 'trail', 'status': 'candidate', 'passes': [1, 1, 1]},
                                        {'refs': ['US-1', 'US-5'], 'kind': 'area', 'status': 'dropped in pass 3', 'passes': [1, 1, 0]}]}
new = {'spots': [{'refs': ['US-2', 'US-1'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 0, 0]}]}
n = S.carry_rows(new, old, {'US-3': 'US-3 is not in the outline store for US-ZZ'})
rows = {tuple(x['refs']): x for x in new['spots']}
check(n == 2 and rows[('US-1', 'US-3')]['status'].startswith('not sure: held: US-3') and rows[('US-1', 'US-3')]['passes'] == [0, 0, 0], 'rows: a live pair touching a held park comes back as "not sure: held: <why>" (no later pass retests it)')
check(rows[('US-1', 'US-4')]['status'].startswith('dropped: not found again') and ('US-1', 'US-5') not in rows, 'rows: a live pair not made again comes back as a dropped row; an old dropped row is not carried')
check(S.carry_rows(new, old, {}) == 0, 'rows: carrying twice adds nothing')
live_old = {S._pk(s) for s in old['spots'] if S._live(s)}
check(live_old <= {S._pk(s) for s in new['spots']}, 'rows: every live pair of the last file has a row in the new file (the post-line check sees none vanish)')

# ---------------------------------------------------------------- join review (proposal; not wired)
fl = {'US-0450': 'bigger-park-record', 'US-4953': 'bigger-park-record'}
r1 = {'refs': ['US-0450', 'US-2679'], 'kind': 'area', 'status': 'candidate'}; r2 = {'refs': ['US-4952', 'US-4953'], 'kind': 'same land', 'status': 'candidate'}
v1 = S.join_review(r1, fl, {'US-0450': {'5355', 'a'}, 'US-2679': {'b'}}); v2 = S.join_review(r2, fl, {'US-4952': {'57014', 'x'}, 'US-4953': {'57014'}})
check(v1 == 'tagged' and r1['status'] == 'candidate' and 'join under review' in r1['join_note'], 'join review: a flagged park with no shared record is KEPT and tagged "join under review"')
check(v2 == 'held' and r2['status'].startswith('not sure: join under review') and '57014' in r2['status'], "join review: held only when the two parks share a joined record (one was given the other's outline)")
check(S.join_review({'refs': ['US-1', 'US-2']}, fl, {}) == 'kept', 'join review: rows with no flagged park are untouched')

# ---------------------------------------------------------------- memory gate
check(S.estimate_mb(7_800_000, 25_000, 750_000, lazy=True) < S.estimate_mb(7_800_000, 25_000, 750_000, lazy=False), 'memory gate: the lazy estimate is below the all-unpacked one')
ok, rows = S.fit_check(st, ['US-ZZ'], limit_mb=3000)
check(ok and rows['US-ZZ']['verdict'] == 'READY' and rows['US-ZZ']['points'] > 0, f'memory gate: a small area is READY ({rows["US-ZZ"].get("estimate_mb")} MB)')
ok, rows = S.fit_check(st, ['US-ZZ'], limit_mb=100)
check(not ok and rows['US-ZZ']['verdict'] == 'WILL NOT FIT' and 'cut the area smaller' in rows['US-ZZ']['why'], 'memory gate: over the limit -> WILL NOT FIT with a plain reason')
ok, rows = S.fit_check(st, ['US-ZZ', 'US-QQ'], limit_mb=3000)
check(not ok and rows['US-QQ']['verdict'] == 'NOT READY' and rows['US-ZZ']['verdict'] == 'READY', 'area gate: one row per area; a missing area is NOT READY')
r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_fers_store.py'), 'fit', str(tmp / 'store'), 'US-ZZ'], capture_output=True, text=True, env={**os.environ, 'KPC_FERS_STORE_LIMIT_MB': '100'})
check(r.returncode == 88 and 'WILL NOT FIT' in r.stdout, f'fit command: exit 88 when it will not fit ({r.stdout.strip()[:60]})')

# ---------------------------------------------------------------- the real 2-fer module, switched on (needs numpy + cv2 like kpc_fers.py)
try:
    import numpy, cv2  # noqa: F401
    have = True
except Exception: have = False  # noqa: BLE001
if not have: print('SKIP real kpc_fers checks (numpy / cv2 not installed here)')
else:
    work = tmp / 'run'; work.mkdir()
    cwd = os.getcwd(); os.chdir(work)
    try:
        os.environ['REGION'] = 'na'; os.environ['PASS'] = '2'
        import kpc_fers as KF
        def inst(K, env):
            try: return S.install(K, env=env)
            finally: S.unsilence()   # a private store run sends the process's own prints to its private log: the test prints again
        priv = tmp / 'private'
        base = {'KPC_FERS_FROM_STORE': 'on', 'KPC_FERS_STORE_DIR': str(tmp / 'store'), 'KPC_FERS_STORE_MAX_DAYS': '100000', 'KPC_FERS_STORE_KIND': 'private', 'KPC_FERS_PRIVATE_OUT': str(priv)}
        orig = {k: getattr(KF, k) for k in ('download', 'saved_us', 'saved_ca', 'live_load', 'pc_tag')}
        KF.ONLY = {'US-QQ'}
        for bad_env, what in (({k: v for k, v in base.items() if k != 'KPC_FERS_PRIVATE_OUT'}, 'not set'), ({**base, 'KPC_FERS_PRIVATE_OUT': str(ROOT / 'never-made-private')}, 'inside a git work tree'),
                              ({**base, 'KPC_FERS_PRIVATE_OUT': str(work / 'p')}, 'inside the working folder')):
            try: inst(KF, env=bad_env); code = None
            except SystemExit as e: code = e.code
            check(code == 89 and KF.download is orig['download'] and S.PRIVATE_OUT is None and not (ROOT / 'never-made-private').exists(),
                  f'private store run: refused (exit 89) before anything is read when the private folder is {what}')
        try: inst(KF, env=base); code = None
        except SystemExit as e: code = e.code
        rowsf = priv / f'store-missing-{KF.area_name()}.json'
        rows = json.loads(rowsf.read_text())
        check(code == 87 and rows['areas']['US-QQ']['verdict'] == 'NOT READY' and KF.download is orig['download'], 'area gate: a missing area store exits 87 before pass 1 (nothing replaced, nothing to save), its row written')
        KF.ONLY = {'US-ZZ'}; S.AREA_ROWS.clear()
        try: inst(KF, env={**base, 'KPC_FERS_STORE_MAX_DAYS': '0'}); code = None
        except SystemExit as e: code = e.code
        check(code == 87 and KF.download is orig['download'], 'area gate: a stale area store exits 87 too')
        S.AREA_ROWS.clear()
        try: inst(KF, env={**base, 'KPC_FERS_STORE_LIMIT_MB': '100'}); code = None
        except SystemExit as e: code = e.code
        rows = json.loads((priv / f'store-missing-{KF.area_name()}.json').read_text())
        check(code == 88 and rows['areas']['US-ZZ']['verdict'] == 'WILL NOT FIT' and KF.download is orig['download'], 'memory gate: install exits 88 with the area row when the run will not fit')
        S.AREA_ROWS.clear()
        check(inst(KF, env=base) is True and KF.download is not orig['download'] and S.STORE_ON, 'switch on: download() is replaced in this process only')
        parks = {'US-9001': {'st': 'US-ZZ', 'ids': ['sgzza1', 901], 'names': {}}, 'US-9002': {'st': 'US-ZZ', 'ids': ['sgzza2'], 'names': {}},
                 'US-9005': {'st': 'US-ZZ', 'ids': ['sgzza5'], 'names': {}}, 'US-9006': {'st': 'US-ZZ', 'ids': ['sgzza6', 'sgzzb6'], 'names': {}},
                 'US-9009': {'st': 'US-ZZ', 'ids': ['sgzza9'], 'names': {}}}
        G, badset = KF.download(parks, sorted(parks), 0.0002, 5)
        check(isinstance(G, S.LazyOutlines) and G.unpacks == 0 and not G.cache, 'lazy: download() returns LazyOutlines and unpacks nothing')
        check(set(G) == {'US-9001', 'US-9002', 'US-9009'} and badset == {'US-9005', 'US-9006'}, f'switch on: store outlines; missing and half parks held ({sorted(G)}, {sorted(badset)})')
        check(G['US-9001'][0][0][0] == [-80.0, 40.0] and G.unpacks == 1 and G.box('US-9002') is not None, 'lazy: a park is unpacked on use only; its box is known without unpacking')
        G.budget = 1; _ = G['US-9002']; _ = G['US-9009']; _ = G['US-9001']
        check(len(G.cache) == 2 and G.unpacks == 4, 'lazy: the points budget evicts the oldest unpacked park (an evicted park is unpacked again)')
        check('outline store' in KF.saved_missing_why('US-9005') and 'US-9006' in S.FLAGS and 'US-9009' in S.PRIVATE, 'switch on: held parks carry their reason; private parks are remembered for the club-room tag')
        check(str(KF.MAPDATE.get('US-9001', '')).startswith('outline store'), 'switch on: the map date says outline store')
        cache = work / 'cache'; cache.mkdir()
        with gzip.open(cache / 'US-ZZ.json.gz', 'wt', encoding='utf-8') as fh:
            json.dump({'recs': [{'OBJECTID': 'wsrc7', 'Unit_Nm': 'Test Wild River', '_r': [sq(-80, 40, 0.01)]}, {'OBJECTID': 5300, '_r': [sq(-81, 40, 0.01)]}, {'OBJECTID': 'sgzza1', '_r': [big]}]}, fh)
        KF.CACHE_US = cache; KF.SAVED_STR.clear()
        check(KF.saved_us({}) == {} and set(KF.SAVED_STR) == {'wsrc7'}, 'switch on: saved_us() keeps only the Wild and Scenic corridor records (not the national copy)')
        Gc, bc = KF.download({'US-9010': {'st': 'US-ZZ', 'ids': ['wsrc7'], 'names': {}}}, ['US-9010'], 0, 0)
        check('US-9010' in Gc and not bc and Gc['US-9010'], 'switch on: a corridor park is read from that saved copy (until the store holds the corridors)')
        KF.live_load('zz')
        check(KF.LIVE_FILE is None and KF.LIVE == {}, "switch on: the bot's own saved-live copy is not read or written (one door in)")
        f = tmp / 'store' / 'US-ZZ.kpcstore.json.gz'; keep = f.read_bytes()
        G2, _ = KF.download(parks, ['US-9002'], 0, 0)
        e2 = json.loads((tmp / 'store' / 'index-US-ZZ.json').read_text())['parks']['US-9002']; o2 = e2['o'] + 12
        f.write_bytes(keep[:o2] + b'\x00' * 20 + keep[o2 + 20:])
        try: _ = G2['US-9002']; loud = False
        except S.StoreChanged: loud = True
        f.write_bytes(keep)
        check(loud and not issubclass(S.StoreChanged, Exception), 'lazy: a store damaged during the run raises StoreChanged (not an Exception, so no pair test can swallow it)')
        (priv / 'US-ZZ.json').write_text(json.dumps({'st': 'US-ZZ', 'pass3': '2026-10-29', 'spots': [
            {'refs': ['US-9001', 'US-9005'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1], 'id': 'a'},
            {'refs': ['US-9001', 'US-9009'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1], 'id': 'b'}]}))
        d = KF.pc_tag({'st': 'US-ZZ', 'spots': [{'refs': ['US-9001', 'US-9009'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 0, 0]}]})
        byp = {tuple(x['refs']): x for x in d['spots']}
        check(byp[('US-9001', 'US-9005')]['status'].startswith('not sure: held: US-9005') and byp[('US-9001', 'US-9009')].get('club_room_only'),
              'switch on: the save path carries the held pair as a "not sure: held" row and tags the private-outline row club_room_only')
        check(not OPENED, f'no network: no connection was attempted ({OPENED[:2]})')

        # ---- must-fix 2: the store is the only door. The finder makes no network request at all.
        import urllib.request
        S.NET_TRIES.clear(); S.ASKED.clear()
        try: urllib.request.urlopen('http://example.invalid/x', timeout=1); ctl = False
        except OSError: ctl = True
        check(ctl and len(S.NET_TRIES) == 1, f'shut door: a direct connection is refused and counted, so a zero count below means none was tried ({S.NET_TRIES})')
        S.NET_TRIES.clear()
        try: KF.pad_closed([-80.0, 40.0, -79.99, 40.01]); pcr = False
        except S.NoDownload: pcr = True
        check(pcr and not S.ASKED and not S.NET_TRIES, 'no download: pad_closed() (the live PAD-US closed-area read) asks for nothing in a store run')
        spot = {'refs': ['US-9001', 'US-9002'], 'kind': 'area', 'id': 'US-9001+US-9002@area@t', 'box': [-79.9962, 40.0038, -79.9938, 40.0062]}
        lc = KF.land_check(spot, G)
        check(lc == 'not checked' and 'rule 10' in spot.get('closed_check', '') and not S.NET_TRIES and not any('PAD' in a for a in S.ASKED),
              f'no download: an area spot whose closed-area check cannot run is "not checked" (NOT SURE), never confirmed ({lc}, asked {S.ASKED})')
        d2 = {'spots': [dict(spot, status='not sure: water not checked (the USGS water map did not answer): run pass 5')]}
        check(S.closed_status(d2) == 1 and d2['spots'][0]['status'].startswith('not sure: closed areas not checked'), 'no download: that row says why (closed areas not checked), not a water reason')
        refused = 0
        for fn, args in ((KF.get, (KF.PADUS, {'f': 'json'})), (KF.KO.get, (KF.KO.PADUS, {'f': 'json'})), (KF._get, (KF.PADUS, {}))):
            try: fn(*args)
            except S.NoDownload: refused += 1
        check(refused == 3 and not S.NET_TRIES, 'no download: every fetch of kpc_fers.py, kpc_owned.py and the answer cache is refused before it is sent')
        check(KF.nhd_water([-80.0, 40.0, -79.99, 40.01]) is None and not S.NET_TRIES, 'no download: water with no saved tile = None (NOT SURE), no live try goes out')
        check(KF.KO.owned_land('nps', [-80.0, 40.0, -79.99, 40.01], 0.0001, 6) is None and not S.NET_TRIES, 'no download: ownership tiles are not read live (the map did not answer = NOT SURE)')
        Gz, _ = KF.download(parks, sorted(parks), 0.0002, 5); _ = [Gz[r] for r in Gz]; KF.saved_us({}); KF.saved_ca(parks); KF.live_load('zz'); KF.live_save('2026-11-14')
        check(not S.NET_TRIES and not OPENED, f'zero network requests: download, saved_us, saved_ca, live_load / live_save, pad_closed, land_check, water and ownership made no connection ({S.NET_TRIES[:2]})')

        # ---- format 4 (store tool 3.5): area / line / pin records; lines on the existing 100-ft line rule; water tiles from the store
        import math as _m
        def lrec(key, paths, **kw):
            r = rec(key, [], **kw); e = [enc(x) for x in paths]
            r.update(geometry_kind='line', lines=e, line_points=sum(len(x) // 2 for x in e), line_sha256=S.geometry_sha256(e)); return r
        def prec(key, pt, **kw):
            r = rec(key, [], **kw); r.update(geometry_kind='pin', pin_point=pt, pin_source='test official point'); return r
        park4 = sq(-77.50, 41.50, 0.01)
        out40 = 41.50 - 40 / 110574.0
        bank_n = 41.50 - 10 / 110574.0
        P4 = [{'ref': 'US-9401', 'name': 'Area Park', 'records': [rec('a1', [park4]), lrec('l1', [[[-77.5, 41.505], [-77.49, 41.505]]]), prec('p1', [-77.495, 41.505])]},
              {'ref': 'US-9402', 'name': 'Crossing Trail', 'records': [lrec('l2', [[[-77.51, 41.505], [-77.495, 41.505], [-77.48, 41.506]]], boundary_rule='trail_100ft')]},
              {'ref': 'US-9403', 'name': 'Pin Only', 'records': [prec('p3', [-77.4, 41.4])]},
              {'ref': 'US-9404', 'name': 'Odd Kind', 'records': [{**rec('b4', [sq(-77.3, 41.3, 0.01)]), 'geometry_kind': 'blob'}]},
              {'ref': 'US-9405', 'name': 'Outside Trail', 'records': [lrec('l5', [[[-77.51, out40], [-77.48, out40]]])]},
              {'ref': 'US-9406', 'name': 'Test Water', 'records': [lrec('l6', [[[-77.498, 41.4977], [-77.492, 41.4977]]], record_name='Test Water', boundary_rule='river_100ft_from_bank', river_class='water_trail', bank_status='covered')]},
              {'ref': 'US-9412', 'name': 'Mississippi River Trail', 'records': [lrec('l12', [[[-77.2, 41.2], [-77.19, 41.2]]], record_name='Mississippi River Trail', boundary_rule='trail_100ft')]},
              {'ref': 'US-9413', 'name': 'Kentucky Water Trail', 'records': [lrec('l13', [[[-77.2, 41.21], [-77.19, 41.21]]], record_name='Kentucky Water Trail', boundary_rule='river_100ft_from_bank', river_class='water_trail', bank_status='covered')]},
              {'ref': 'US-9414', 'name': 'Corridor River', 'records': [lrec('l14', [[[-77.2, 41.22], [-77.19, 41.22]]], boundary_rule='designated_corridor_area', river_class='designated_corridor')]},
              {'ref': 'US-9415', 'name': 'By Name River', 'records': [lrec('l15', [[[-77.498, 41.4999], [-77.492, 41.4999]]], boundary_rule='river_100ft_from_bank', river_class='water_trail', bank_status='covered', source='nhd-by-name', line_extent='the park may be a stretch only')]},
              {'ref': 'US-9416', 'name': 'Old Route', 'records': [lrec('l16', [[[-77.2, 41.24], [-77.19, 41.24]]], boundary_rule='river_100ft_from_bank', river_class='historic_route', bank_status='route line too coarse for a bank test')]},
              {'ref': 'US-9417', 'name': 'No Line', 'records': [lrec('l17', [[[-77.2, 41.25], [-77.19, 41.25]]], boundary_rule='river_100ft_from_bank', river_class='water_trail', bank_status='line_missing')]},
              {'ref': 'US-9418', 'name': 'Unsorted', 'records': [lrec('l18', [[[-77.2, 41.26], [-77.19, 41.26]]], boundary_rule='unclear_river_class', river_class='unclear')]},
              {'ref': 'US-9419', 'name': 'Bankless', 'records': [lrec('l19', [[[-77.498, 41.4977], [-77.492, 41.4977]], [[-77.498, 41.51 + 11 / 110574.0], [-77.492, 41.51 + 11 / 110574.0]]], boundary_rule='river_100ft_from_bank', river_class='water_trail', bank_status='bank_missing', bank_missing=True)]},
              {'ref': 'US-9420', 'name': 'Ruleless', 'records': [lrec('l20', [[[-77.2, 41.27], [-77.19, 41.27]]])]},
              {'ref': 'US-9421', 'name': 'NPS Water Route', 'records': [lrec('l21', [[[-77.2, 41.28], [-77.19, 41.28]]], boundary_rule='river_100ft_from_bank', river_class='historic_route', bank_status='route line too coarse for a bank test')]}]
        def _k4(d):
            d['store_format_version'] = 'kpc-outline-store-index/4'; d['geometry_kinds'] = ['area', 'line', 'pin']
            for p in P4:
                ks = [S.kind_of(r) for r in p['records']]
                d['parks'][p['ref']]['geometry_kind'] = 'area' if 'area' in ks or not ks else ('line' if 'line' in ks else 'pin' if 'pin' in ks else 'blob')
            return d
        build(tmp / 's4', 'US-ZY', P4, made='2026-11-14', index_edit=_k4)
        st4 = S.Store(tmp / 's4', 100000, today='2026-11-14', kind='private')
        g41, _, w41, i41 = st4.examine('US-9401', 'US-ZY', ['a1', 'l1', 'p1'], keep=True)
        check(not w41 and len(g41) == 1 and g41[0][0] == park4 and i41['skipped'] == {'line': 1, 'pin': 1}, f'format 4: only AREA records make the outline; the line and pin records are left out and counted ({i41.get("skipped")})')
        check('no area record' in held(st4, 'US-9403', ['p3'], 'US-ZY') and 'pin is never a boundary' in held(st4, 'US-9403', ['p3'], 'US-ZY'), 'format 4: a pin-only park is never an outline (held: a pin is never a boundary)')
        check('no area record' in held(st4, 'US-9404', ['b4'], 'US-ZY'), 'format 4: an unknown geometry_kind is not an area (left out, never read as one)')
        base = {'US-9405': {'lines': [[[-77.51, out40], [-77.48, out40]]], 'kind': 'trail', 'by': 'Test agency (data/trails)', 'type': 'NRT'},
                'US-9499': {'lines': [[[-77.2, 41.2], [-77.1, 41.2]]], 'kind': 'trail', 'by': 'x', 'type': 'NRT'},
                'US-9421': {'lines': [[[-77.3, 41.3], [-77.25, 41.31]]], 'kind': 'trail', 'by': 'National Park Service', 'type': 'NHT', 'water_parts': [0]}}
        S.FLAGS.clear(); S.STORE_LINES.clear()
        LN4 = S.store_lines(KF, st4, ['US-ZY'], base)
        check(LN4.get('US-9421') == base['US-9421'] and 'US-9421' not in S.STORE_LINES and 'US-9421' not in S.LINE_SKIPPED and 'US-9421' not in S.FLAGS,
              'M4 (owner ruling): a coarse NPS water route (US-4572, US-3791, US-4567, US-4581) is NOT skipped: its data/trails line and rule exactly as on main')
        LN4.pop('US-9421', None)
        check(set(LN4) == {'US-9402', 'US-9405', 'US-9406', 'US-9412', 'US-9413', 'US-9419'} and LN4['US-9402']['lines'][0][0] == [-77.51, 41.505] and LN4['US-9402']['lines'][0][-1] == [-77.48, 41.506]
              and LN4['US-9402']['lines'][0][0] != LN4['US-9402']['lines'][0][-1], 'format 4: line parks get their line from the store, open and exact (never closed, never buffered into an area)')
        check(LN4['US-9405']['by'] == 'Test agency (data/trails)' and LN4['US-9405']['type'] == 'NRT' and LN4['US-9405']['kind'] == 'trail' and LN4['US-9406']['kind'] == 'river' and LN4['US-9402']['kind'] == 'trail',
              "format 4: trail or river comes from the record's boundary_rule (data/trails only when a record has none); who drew it and its type from data/trails")
        check(LN4['US-9412']['kind'] == 'trail' and LN4['US-9413']['kind'] == 'river', 'M5: kind from boundary_rule, never the name: "Mississippi River Trail" (trail_100ft) is a trail, "Kentucky Water Trail" (river_100ft_from_bank) a river')
        check('designated-corridor' in S.FLAGS.get('US-9414', '') and 'line is missing' in S.FLAGS.get('US-9417', '') and 'not sorted' in S.FLAGS.get('US-9418', '') and 'no boundary rule' in S.FLAGS.get('US-9420', '')
              and not {'US-9414', 'US-9417', 'US-9418', 'US-9420'} & set(LN4),
              'M4: a designated-corridor river is an AREA park (its line is never the boundary); line_missing, unclear class and no boundary rule are held')
        check('found on USGS NHD by name' in S.LINE_SKIPPED.get('US-9415', '') and 'too coarse' in S.LINE_SKIPPED.get('US-9416', '') and LN4['US-9419'].get('bank_missing') and not LN4['US-9406'].get('bank_missing'),
              'M4 (owner ruling): a by-name river line and a coarse route line are SKIPPED and counted (no 2-fer from them); bank_missing is read from the record')
        _n_todo = len(S.RIVER_TODO)
        _rows4 = {'st': 'US-ZY', 'spots': [{'refs': ['US-9401', 'US-9419'], 'kind': 'river', 'status': 'candidate', 'id': 'r19', 'center': [41.4977, -77.495], 'len_m': 400},
                                         {'refs': ['US-9401', 'US-9419'], 'kind': 'river', 'status': 'candidate', 'bank_ok': True, 'id': 'r19b'},
                                         {'refs': ['US-9401', 'US-9406'], 'kind': 'river', 'status': 'candidate', 'id': 'r6'}, {'refs': ['US-9401', 'US-9402'], 'kind': 'trail', 'status': 'candidate', 'id': 't2'}]}
        S.line_status(KF, _rows4); _x4 = _rows4['spots']
        check([x['status'] for x in _x4] == ['candidate'] * 4 and _x4[0].get('river_bank') == S.BANK_EST and not any(x.get('river_bank') for x in _x4[1:])
              and len(S.RIVER_TODO) == _n_todo + 1 and S.RIVER_TODO[-1]['river'] == 'US-9419' and S.RIVER_TODO[-1]['park'] == 'US-9401',
              'M4 (owner ruling): a bank_missing water trail is still decided by the existing centre-line rule, the row marked as an estimate and its stretch put on the river bank to-do; covered rivers and trails unchanged')
        check('US-9401' not in LN4 and 'not in the outline store' in S.FLAGS.get('US-9499', ''), 'format 4: an area park is tested as an area; a data/trails line the store lacks is HELD (one door in)')
        parks4 = {'US-9401': {'st': 'US-ZY', 'ids': ['a1', 'l1', 'p1'], 'names': {}}, 'US-9402': {'st': 'US-ZY', 'ids': ['l2'], 'names': {}}, 'US-9403': {'st': 'US-ZY', 'ids': ['p3'], 'names': {}}}
        G4, bad4 = S.store_download(KF, st4, parks4, sorted(parks4))
        check(set(G4) == {'US-9401'} and bad4 == {'US-9403'} and 'US-9402' not in KF.MISSING_SAVED, f'format 4: the line park is not held as a missing outline (tested by its line), the pin park is held ({sorted(G4)}, {sorted(bad4)})')
        g9401 = G4['US-9401']; bx = [-77.52, 41.49, -77.47, 41.52]
        cross = KF.line_spots('US-9402', LN4['US-9402']['lines'], 'US-9401', g9401, False, bx, 'trail')
        check(cross and all(x['kind'] == 'trail' for x in cross) and max(x['len_m'] for x in cross) > 500, f'line rule: a trail that crosses the park is a pair (100 ft rule, {[x["len_m"] for x in cross]} m)')
        check(KF.line_spots('US-9405', LN4['US-9405']['lines'], 'US-9401', g9401, False, bx, 'trail') == [], 'line rule: a trail 40 m outside the park is no pair (30.48 m from the line since Nov 14, station 5 m inside)')
        wpoly = [[[-77.51, 41.4955], [-77.47, 41.4955], [-77.47, bank_n], [-77.51, bank_n], [-77.51, 41.4955]]]
        wdir = tmp / 's4' / 'water' / 'us-nhdplus-hr'; wdir.mkdir(parents=True, exist_ok=True); widx = {'sources': {'us-nhdplus-hr': {'publishable': True, 'licence_class': 'PUBLIC DOMAIN'}}, 'tiles': {'us-nhdplus-hr': {}}}
        for i in range(int(_m.floor(-77.9 / .1)), int(_m.floor(-77.1 / .1)) + 1):
            for jt in range(int(_m.floor(41.1 / .1)), int(_m.floor(41.9 / .1)) + 1):
                raw_t = gzip.compress(json.dumps({'d': 'us-nhdplus-hr 2026-11-01', 'f': [['area', wpoly]]}).encode(), mtime=0)
                (wdir / f'{i}_{jt}.json.gz').write_bytes(raw_t); widx['tiles']['us-nhdplus-hr'][f'{i}_{jt}.json.gz'] = {'sha256': hashlib.sha256(raw_t).hexdigest(), 'date': '2026-11-01'}
        (tmp / 's4' / 'water' / 'index.json').write_text(json.dumps(widx))
        keep_wl = KF._wload; KF.NHDC.clear(); KF.WATER_UNCHECKED.clear()
        KF._wload = lambda i, jt: None   # no tile anywhere: the river's centre line only
        S.NET_TRIES.clear()
        cen = KF.line_spots('US-9406', LN4['US-9406']['lines'], 'US-9401', g9401, False, bx, 'river')
        check(cen == [] and ('US-9406', 'US-9401') in KF.WATER_UNCHECKED and not S.NET_TRIES,
              'river, centre line only (no water tile): no pair from the centre line of a wide river, and the pair is marked water-unchecked (NOT SURE), no live call')
        KF.NHDC.clear(); KF.WATER_UNCHECKED.clear(); KF.WATER_MARK.clear()
        KF._wload = S.water_reader(st4, ['US-ZY'], None)
        bnk = KF.line_spots('US-9406', LN4['US-9406']['lines'], 'US-9401', g9401, False, bx, 'river')
        check(bnk and not KF.WATER_UNCHECKED and S.WATER_READ['store'] > 0 and '2026-11-01' in KF.WATER_MARK and not S.NET_TRIES,
              f'river with its bank (water tile from the store): the park 10 m from the bank is a pair, 100 ft from the bank; the row is dated from the tile ({[x["len_m"] for x in bnk]} m)')
        # S1: the spec's water section: store/water/<source id>/, checked against water/index.json, the area's own source only
        t0 = S.store_water(st4, ['US-ZY'], -775, 414)
        check(isinstance(t0, dict) and t0['d'] == '2026-11-01' and t0['f'], 'water: a tile is read from store/water/us-nhdplus-hr/<i>_<j>.json.gz, checked against water/index.json; its row date is the tile date')
        _calls = []
        _wr = S.water_reader(st4, ['US-ZY'], lambda i, jt: _calls.append((i, jt)) or {'d': 'other copy', 'f': []})
        tf = wdir / '-775_414.json.gz'; keep_t = tf.read_bytes(); tf.write_bytes(keep_t[:-3] + b'xyz')
        check(S.store_water(st4, ['US-ZY'], -775, 414) is S.WATER_DAMAGED and _wr(-775, 414) is None and not _calls,
              'water: a damaged tile (sha256 differs from water/index.json) is NOT SURE and never falls through to another copy')
        tf.write_bytes(keep_t)
        check(_wr(-700, 300) == {'d': 'other copy', 'f': []} and _calls == [(-700, 300)], "water: a tile the store does not hold falls back to the bot's own last good copy, as today")
        (tmp / 's4' / 'water' / 'on-ohn').mkdir(exist_ok=True); (tmp / 's4' / 'water' / 'on-ohn' / '-760_400.json.gz').write_bytes(gzip.compress(b'{"d": "on-ohn 2026-11-01", "f": []}'))
        check(S.store_water(st4, ['US-ZY'], -776, 415)['d'] == '2026-11-01' and S.store_water(st4, ['US-ZY'], -760, 400) is None,
              'water: a border tile is read from the source mapped to the area (us-nhdplus-hr); another source (on-ohn) never decides alone')
        _wi = json.loads((tmp / 's4' / 'water' / 'index.json').read_text()); _wi['sources']['us-nhdplus-hr']['publishable'] = False; (tmp / 's4' / 'water' / 'index.json').write_text(json.dumps(_wi))
        check(S.store_water(S.Store(tmp / 's4', 100000, today='2026-11-14', kind='public'), ['US-ZY'], -775, 414) is S.WATER_DAMAGED
              and isinstance(S.store_water(S.Store(tmp / 's4', 100000, today='2026-11-14', kind='private'), ['US-ZY'], -775, 414), dict),
              'water: a source marked publishable false is not read on a public store run (NOT SURE); a private run reads it')
        _wi['sources']['us-nhdplus-hr']['publishable'] = True; (tmp / 's4' / 'water' / 'index.json').write_text(json.dumps(_wi))
        check(S.store_water(st4, ['CA-ON'], -775, 414) is None, "water: Canadian areas are not read from the store (no bank source wired in the bot): today's behaviour")
        KF.NHDC.clear(); _keep_wl2 = KF._wload; KF._wload = S.water_reader(st4, ['US-ZY'], None)
        b19 = KF.line_spots('US-9419', LN4['US-9419']['lines'], 'US-9401', g9401, False, bx, 'river')
        KF._wload = _keep_wl2
        check(any(x.get('bank_ok') for x in b19) and any(not x.get('bank_ok') for x in b19), f'M4: a bank_missing river: the stretch in mapped water was measured from the bank (bank_ok), the stretch off the water was not ({[(x["len_m"], bool(x.get("bank_ok"))) for x in b19]})')
        # the river rule with NO bank data, behind one switch (KPC_FERS_RIVER_NO_BANK): default centreline = today; tiers = PROVISIONAL
        def rl(m_from_edge): y = 41.50 - m_from_edge / 110574.0; return [[[-77.498, y], [-77.492, y]]]
        check(S.river_mode({}) == 'centreline' and S.river_mode({'KPC_FERS_RIVER_NO_BANK': 'tiers'}) == 'tiers' and S.river_mode({'KPC_FERS_RIVER_NO_BANK': 'maybe'}) == 'centreline'
              and S.RIVER_NO_BANK['catch_m'] == 250.0, 'river switch: default centreline (today); only "tiers" turns the provisional tiers on; catch distance 250 m')
        keep_ls = KF.line_spots
        KF._wload = S.water_reader(st4, ['US-ZY'], None)
        KF.NHDC.clear(); c1 = KF.line_spots('US-9407', narrow := [[[-77.498, 41.51 + 11 / 110574.0], [-77.492, 41.51 + 11 / 110574.0]]], 'US-9401', g9401, False, bx, 'river')
        check(c1 and not any('river_tier' in x for x in c1), f'river switch, default: no bank data = measured from the centre line exactly as today, no tier label ({[x["len_m"] for x in c1]} m)')
        S.river_bank_guard(KF, 'tiers'); S.RIVER_TIERS.clear(); S.RIVER_TODO.clear()
        KF.NHDC.clear(); t1 = KF.line_spots('US-9406', LN4['US-9406']['lines'], 'US-9401', g9401, False, bx, 'river')
        check(t1 and all(x['river_tier'] == S.TIER_BANK for x in t1), 'tier 1 bank: a wide river with its bank tile, the park ending at the bank: solid, 30.48 m from the bank as today')
        KF._wload = lambda i, jt: None   # no bank tiles from here on
        KF.NHDC.clear(); t2 = KF.line_spots('US-9408', rl(-33), 'US-9401', g9401, False, bx, 'river')
        check(t2 and all(x['river_tier'] == S.TIER_CENTRE for x in t2), 'tier 2: no bank data, the park reaches past the river centre line: counts ("park reaches the river centre line")')
        KF.NHDC.clear(); t3 = KF.line_spots('US-9409', rl(120), 'US-9401', g9401, False, bx, 'river')
        check(len(t3) == 1 and t3[0]['river_tier'] == S.TIER_ALONG and t3[0]['river_candidate']['centre_line_m'] in range(110, 131) and any('along the river' in g for g in t3[0]['river_candidate']['signs']),
              f'tier 3: a wide river (no bank tile), the park ending at the bank 120 m from the centre line: a CANDIDATE with the bank-assumed sign, never a 2-fer ({t3[0].get("river_candidate") if t3 else None})')
        KF.NHDC.clear(); t4 = KF.line_spots('US-9410', rl(200), 'US-9401', g9401, False, bx, 'river')
        check(len(t4) == 1 and t4[0]['river_tier'] == S.TIER_LINE and not t4[0]['river_candidate']['signs'], 'tier 4: a park set back 200 m (behind a road) is no tier 3; within the 250 m catch it is a centre-line candidate')
        KF.NHDC.clear(); t5 = KF.line_spots('US-9411', rl(300), 'US-9401', g9401, False, bx, 'river')
        check(t5 == [], 'tiers: a park 300 m from the centre line (beyond the catch distance) is not caught')
        dt_ = KF.pc_tag({'st': 'US-ZY', 'spots': [dict(x, status='candidate', id=f't{i}') for i, x in enumerate(t1 + t2 + t3 + t4)]})
        stt = [x['status'] for x in dt_['spots']]
        check(stt[:len(t1) + len(t2)] == ['candidate'] * (len(t1) + len(t2)) and all(x.startswith('river candidate: needs bank shape') for x in stt[len(t1) + len(t2):]),
              'tiers: only tiers 1 and 2 stay 2-fers; tier 3 / 4 rows say "river candidate: needs bank shape" with the distance and signs')
        check(len(S.RIVER_TODO) == 2 and {x['river'] for x in S.RIVER_TODO} == {'US-9409', 'US-9410'} and not any('shape' in x or 'lines' in x for x in S.RIVER_TODO) and S.store_counts()['river bank to-do (stretches)'] == 2,
              f'tiers: every caught candidate goes on the bank store to-do list (ids, distance, signs, a box; no shape) ({S.RIVER_TODO})')
        import csv as _csv
        check(S.write_todo_csv() and [r for r in _csv.reader(open(priv / 'river-bank-todo.csv'))][0] == ['park ref', 'other park ref', 'lat', 'lon', 'radius m']
              and len(list(_csv.reader(open(priv / 'river-bank-todo.csv')))) == 3 and S.PRIVATE_LOG_DIR == S.PRIVATE_OUT,
              "S3: the river bank to-do is the spec's river-bank-todo.csv (park ref, other park ref, lat, lon, radius m), written in the PRIVATE folder only")
        check(S.write_candidates_csv() and 'river candidate: needs a look' in (priv / 'river-candidates-needs-a-look.csv').read_text() and 'US-9415' in (priv / 'river-candidates-needs-a-look.csv').read_text(),
              'M4 (owner ruling): the skipped lines are listed as "river candidate: needs a look" in the PRIVATE folder only')
        S.RIVER_NO_BANK['mode'] = 'centreline'; KF.line_spots = keep_ls
        check(not S.NET_TRIES, 'tiers: no network request')
        KF._wload = keep_wl; KF.NHDC.clear(); KF.WATER_MARK.clear()
        d4 = KF.pc_tag({'st': 'US-ZY', 'spots': [dict(cross[0], status='candidate', id='t1'), {'refs': ['US-9401', 'US-1'], 'kind': 'area', 'status': 'candidate', 'id': 't2'}]})
        cnt = S.store_counts()
        check(S.LINE_ROWS.get('US-ZY') == 1 and cnt['line parks read from the store'] == 6 and cnt['line parks skipped (by-name / coarse / no bank status)'] == 2 and cnt['records left out of area outlines (not area)'].get('pin', 0) >= 1,
              f'format 4: the run report counts the left-out records, the store line parks and the pairs that depend on the 100-ft line rule ({cnt})')

        # ---- must-fix 1: a private store run writes only into its private folder (club room only)
        pub_f = work / 'data' / 'fers' / 'US-ZZ.json'
        try: KF.save_json(pub_f, {'st': 'US-ZZ', 'spots': []}); g1 = False
        except S.LeakRefused as e: g1 = e.code == 89
        check(g1 and not pub_f.exists(), 'write guard: a private store run cannot write a file into the working folder (exit 89, nothing written)')
        KF.save_json(KF.file_of('US-ZZ'), KF.pc_tag({'st': 'US-ZZ', 'spots': [{'refs': ['US-9001', 'US-9009'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 0, 0], 'id': 'b2', 'wide_m': 30, 'center': [40.0, -80.0]}]}), indent=None)
        got_p = json.loads((priv / 'US-ZZ.json').read_text())
        check(_inside_dir(KF.file_of('US-ZZ'), priv) and any(x.get('club_room_only') for x in got_p['spots']) and not pub_f.exists(),
              "write guard: a private store run's spot file (club-room rows included) lands in the private folder only")
        import kpc_save as _KS
        check(not any(str(priv) in k for k in _KS._changed), "write guard: kpc_save's exit-time status file (data/status/<bot>.json) does not list the private files")
    finally:
        os.chdir(cwd)
prog = tmp / 'exit.py'
prog.write_text('import sys; sys.path.insert(0, %r)\nimport kpc_fers_store as S\nclass K: pass\nk = K(); k.REGION = "na"; k.OUT = %r; k.ONLY = {"US-ZZ"}; k.pc_tag = lambda d: d; k.area_name = lambda: "zz"\n'
                'print(S.install(k, env={"KPC_FERS_FROM_STORE": "on", "KPC_FERS_STORE_DIR": %r, "KPC_FERS_STORE_MAX_DAYS": "100000"}))\n' % (str(ROOT / '.github/scripts'), str(tmp / 'out'), str(tmp / 'store')))
r = subprocess.run([sys.executable, str(prog)], capture_output=True, text=True)
fl2 = tmp / 'out' / 'store-missing-zz.json'
check(r.stdout.strip().endswith('True') and fl2.is_file() and json.loads(fl2.read_text())['parks'] == {} and json.loads(fl2.read_text())['areas']['US-ZZ']['verdict'] == 'READY',
      'the store-missing list is written at exit even with nothing held')

# ---------------------------------------------------------------- must-fix 1: the write guard on a PUBLIC store run (fresh process per case)
if have:
    guard_prog = tmp / 'guard.py'
    guard_prog.write_text(r"""import json, os, sys
os.environ['REGION'] = 'na'; os.environ['PASS'] = '3'
sys.path.insert(0, %r)
import kpc_fers as KF, kpc_fers_store as S
KF.ONLY = {'US-ZZ'}
_env = {'KPC_FERS_FROM_STORE': 'on', 'KPC_FERS_STORE_DIR': %r, 'KPC_FERS_STORE_MAX_DAYS': '100000', 'KPC_FERS_STORE_KIND': 'public'}
if len(sys.argv) > 2: _env['KPC_FERS_PRIVATE_LOG'] = sys.argv[2]
assert S.install(KF, env=_env)
case = sys.argv[1]; f = KF.file_of('US-ZZ')
row = {'refs': ['US-9001', 'US-9002'], 'kind': 'area', 'status': 'candidate', 'id': 'US-9001+US-9002@area@x', 'wide_m': 30, 'acres': 1.0, 'center': [40.0, -80.0], 'shape': [[-80, 40], [-79.99, 40], [-79.99, 40.01]]}
priv = {'sgzza9': {'licence_class': 'NO TERMS STATED'}}
if case == 'clean': KF.save_json(f, KF.pc_tag({'st': 'US-ZZ', 'spots': [row]}))
if case == 'tagged': KF.save_json(f, {'st': 'US-ZZ', 'spots': [dict(row, club_room_only=True)]})
if case == 'tagged_no_geometry': KF.save_json(f, {'st': 'US-ZZ', 'spots': [{'refs': row['refs'], 'kind': 'area', 'status': 'candidate', 'club_room_only': True}]})
if case == 'tagged_by_pc_tag': S.PRIVATE['US-9009'] = priv; KF.save_json(f, KF.pc_tag({'st': 'US-ZZ', 'spots': [dict(row, refs=['US-9001', 'US-9009'])]}))
if case == 'private_untagged': S.PRIVATE['US-9009'] = priv; KF.save_json(f, {'st': 'US-ZZ', 'spots': [dict(row, refs=['US-9001', 'US-9009'])]})
if case == 'private_id_only': S.PRIVATE['US-9009'] = priv; KF.save_json(KF.OUT / 'looked-US-ZZ.json', {'unread': ['US-9009'], 'boxes': {}})
if case == 'world': KF.save_json(f, {'st': 'US-ZZ', 'spots': [dict(row, refs=['US-9001', 'GB-0001'])]})
if case == 'blocked': KF.save_json(KF.OUT / 'report.json', {'build': 'US-42797939226'})
if case == 'log_line': S.PRIVATE['US-9009'] = priv; KF.save_json(KF.OUT / 'report.json', {'problems': ['us-9009 lower case', 'pairUS-9009', 'area-US-9009', 'fine line'], 'x': {'US-9009': 1}})
if case == 'print_secret': print('progress: now US-9001+US-9003, us-9008 and US-9009 at the end', flush=True)
if case == 'store_list_blocked': S.FLAGS['US-9001'] = 'built from US-42797939226'; sys.exit(0)
if case == 'swallowed':
    try: KF.save_json(f, {'st': 'US-ZZ', 'spots': [dict(row, club_room_only=True)]})
    except Exception: pass
print('WROTE')
""" % (str(ROOT / '.github/scripts'), str(tmp / 'store')))
    def guard_case(case, plog=None):
        d = tmp / ('g-' + case + ('-log' if plog else '')); d.mkdir(exist_ok=True)
        r = subprocess.run([sys.executable, str(guard_prog), case] + ([str(plog)] if plog else []), capture_output=True, text=True, cwd=d)
        return r.returncode, (d / 'data' / 'fers').glob('*') and sorted(p.name for p in (d / 'data' / 'fers').glob('*')), r.stdout + r.stderr
    rc, files, out = guard_case('clean')
    check(rc == 0 and 'US-ZZ.json' in files and 'WROTE' in out, f'write guard: a clean public row is written as before ({rc}, {files})')
    import re as _rx
    REFS_OUT = _rx.compile(r'(?i)US-9\d{3}|GB-0001|sgzza\d|NO TERMS')
    for case, what in (('tagged', 'a row marked club_room_only, with its shape, width, centre and area'), ('tagged_no_geometry', 'a row marked club_room_only, with no geometry at all'),
                       ('world', 'a world 2-fer row'), ('blocked', 'the never-released build US-42797939226'), ('swallowed', "a refusal inside kpc_fers.py's own 'except Exception'")):
        rc, files, out = guard_case(case)
        check(rc == 89 and 'US-ZZ.json' not in files and 'report.json' not in files and 'WROTE' not in out and 'write refused' in out,
              f'write guard: the run FAILS (exit 89, nothing written) rather than write {what} to a public file ({rc}, {files})')
        check(not REFS_OUT.search(out) and 'problem(s)' in out, f'M2: the refusal prints a count and a generic reason only: no park, record or licence in stdout / stderr ({REFS_OUT.findall(out)[:3]})')
    for case, what, fname in (('tagged_by_pc_tag', 'a row the save path tags club_room_only', 'US-ZZ.json'), ('private_untagged', 'a row with a private park whose tag was never set', 'US-ZZ.json'),
                              ('private_id_only', 'a private park id alone (the looked list), no geometry', 'looked-US-ZZ.json'), ('log_line', 'log lines naming it in lower case or glued to other text', 'report.json')):
        rc, files, out = guard_case(case)
        body = (tmp / ('g-' + case) / 'data' / 'fers' / fname).read_text() if fname in files else ''
        sm = (tmp / ('g-' + case) / 'data' / 'fers' / 'store-missing-US-ZZ.json').read_text() if 'store-missing-US-ZZ.json' in files else ''
        check(rc == 0 and fname in files and body and not _rx.search(r'(?i)US-9009|US-900[378]|sgzza9|NO TERMS', body + sm) and 'fine line' in (body if case == 'log_line' else 'fine line')
              and not REFS_OUT.search(out), f'M1: {what}: the park is left out of the public file (and store-missing, stdout), never named ({rc}, {files})')
    smj = json.loads((tmp / 'g-clean' / 'data' / 'fers' / 'store-missing-US-ZZ.json').read_text())
    check(smj['withheld (parks held or used for unpublishable / WDPA records: not named)'] >= 4 and not _rx.search(r'(?i)US-900[3789]|sgzza[3789]|NO TERMS|wdpa_derived', json.dumps(smj['parks'])),
          f"M1: store-missing names no park held for licence or WDPA records (filled from the store index for ALL parks of the area, read or not): only a count ({smj['withheld (parks held or used for unpublishable / WDPA records: not named)']})")
    rc, files, out = guard_case('print_secret')
    check(rc == 0 and 'US-9003' not in out and 'US-9009' not in out and 'us-9008' not in out.lower().replace('[withheld]', '') and 'US-9001' in out,
          f'M1 / M3: a public run prints no park held for licence or WDPA records (a line naming one has it replaced by [withheld]) ({out.strip()[-120:]})')
    plog = tmp / 'plog-tagged'
    rc, files, out = guard_case('tagged', plog)
    pl = (plog / 'private-log.txt').read_text() if (plog / 'private-log.txt').is_file() else ''
    check(rc == 89 and 'US-9001+US-9002' in pl and 'US-9001' not in out and 'details are only in the private log' in out,
          'M2: with a private log folder the details of a refusal go there, and only there')
    rc, files, out = guard_case('store_list_blocked')
    check(rc == 89 and 'store-missing-US-ZZ.json' not in files, f'write guard: the store-missing list (written at exit) passes the guard too ({rc}, {files})')

# ---------------------------------------------------------------- the guard itself, hardened (S5), and small fixes (S2, S7)
_po = S.PRIVATE_OUT; S.PRIVATE_OUT = None
def _refused(doc, secret=()):
    try: S.guard_write('data/fers/x.json', doc, secret); return False
    except S.LeakRefused: return True
_deep = {'a': 1}
for _ in range(20): _deep = {'n': [_deep]}
_deep_flag = json.loads(json.dumps(_deep).replace('{"a": 1}', '{"club_room_only": true}'))
check(_refused(_deep_flag) and _refused({'pairs': ['US-1+GB-0001']}) and _refused({'x': [{'refs': ['US-1', 'W-5']}]}) and _refused({'build': 42797939226})
      and _refused({'p': ['area-US-9009']}, {'US-9009'}) and _refused({'p': 'pairUS-9009'}, {'US-9009'}) and _refused({'p': 'us-9009'}, {'US-9009'})
      and not _refused({'p': 'US-90091', 'refs': ['US-1', 'CA-2']}, {'US-9009'}),
      'S5: the guard sees a club-room flag 20 levels deep, world refs in any row shape (pairs, refs without kind), the blocked build as a number, and a private ref in any case or glued to other text')
S.PRIVATE_OUT = _po
check(S.env_float({'X': 'nan'}, 'X', 250.0) == 250.0 and S.env_float({'X': 'inf'}, 'X', 250.0) == 250.0 and S.env_float({'X': '-3'}, 'X', 250.0) == 250.0
      and S.env_float({'X': '0'}, 'X', 250.0) == 250.0 and S.env_float({'X': '300'}, 'X', 250.0) == 300.0, 'S7: nan, inf, zero and negative settings are refused (the default stays)')
class _LC:
    pad_closed = None
    def land_check(self_or_s, *a, **k): raise RuntimeError('boom')
_lc = _LC(); _lc.land_check = lambda s_, G_, live=True: (_ for _ in ()).throw(RuntimeError('boom'))
S.shut_door(_lc)
_sp = {'refs': ['US-1', 'US-2'], 'kind': 'area'}
_lcr = _lc.land_check(_sp, {})
_d2 = {'spots': [dict(_sp, status='not sure: water not checked (the USGS water map did not answer): run pass 5')]}
S.closed_status(_d2)
check(_lcr == 'not checked' and _d2['spots'][0]['status'].startswith('not sure: the land check stopped with an error'), 'S2: any error inside the land check on a store run is NOT SURE, never ok')

# ---------------------------------------------------------------- S6 / M1 / M3: kpc_fers.main() end to end on a synthetic store, every socket shut
if have:
    e2e = tmp / 'e2e'
    def e2e_world(name):
        b = e2e / name; w = b / 'w'
        for d in ('data/parkinfo', 'data/trails', 'data/us-key', 'data/fers'): (w / d).mkdir(parents=True, exist_ok=True)
        EP = [('US-9601', 'Big Forest', sq(-71.6, 41.6, 0.02), {}), ('US-9602', 'Inner Park', sq(-71.59, 41.61, 0.005), {}),
              ('US-9603', 'Secret Park', sq(-71.585, 41.605, 0.004), {'publishable': False, 'licence_class': 'NO TERMS STATED', 'publish_basis': 'none'}),
              ('US-9604', 'Wdpa Park', sq(-71.595, 41.615, 0.004), {'wdpa_derived': True})]
        build(b / 'store', 'US-RI', [{'ref': r, 'name': n, 'records': [rec(str(int(r[-4:]) * 10), [g], **kw)]} for r, n, g, kw in EP], made='2026-11-14')
        pins = {r: [n, 'State Park', '', '', '', g[0][1] + 0.001, g[0][0] + 0.001] for r, n, g, kw in EP}
        pins['US-9605'] = ['Held Park', 'State Park', '', '', '', 41.615, -71.58]
        (w / 'data/parkinfo/US-RI.json').write_text(json.dumps({'parks': pins}))
        key = {r: {'m': [[int(r[-4:]) * 10, n, 0.01, 'name']], 'g': 'official'} for r, n, g, kw in EP}
        key['US-9605'] = {'m': [[96059, 'Held Park', 0.01, 'name']], 'g': 'official'}
        (w / 'data/us-key/US-RI.json').write_text(json.dumps({'parks': key}))
        (w / 'data/trails/index.json').write_text('[]'); (w / 'data/trails/index-state.json').write_text('[]')
        (w / 'data/fers/US-RI.json').write_text(json.dumps({'st': 'US-RI', 'pass3': '2026-10-29', 'spots': [
            {'refs': ['US-9601', 'US-9603'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1], 'id': 'old1', 'names': {'US-9603': 'Secret Park'}}]}))
        runner = b / 'runner.py'
        runner.write_text('import socket, sys, os, json, atexit\nTRIES = []\n'
                          'def no(*a, **k): TRIES.append(str(a[:2])[:80]); raise OSError("no network")\n'
                          'socket.socket.connect = lambda self, *a, **k: no(*a); socket.socket.connect_ex = lambda self, *a, **k: no(*a)\n'
                          'socket.create_connection = no; socket.getaddrinfo = no\n'
                          'atexit.register(lambda: open(os.environ["TRIES_OUT"], "w").write(json.dumps(TRIES)))\n'
                          f'sys.path.insert(0, {str(ROOT / ".github/scripts")!r})\nimport kpc_fers_store as S\nsys.exit(S.main(["run"]))\n')
        return b, w, runner
    def e2e_run(name, **extra):
        b, w, runner = e2e_world(name)
        env = {k: v for k, v in os.environ.items() if 'proxy' not in k.lower() and k not in ('GITHUB_ACTIONS', 'KPC_FERS_PRIVATE_RUNNER')}
        env.update(KPC_FERS_FROM_STORE='on', KPC_FERS_STORE_DIR=str(b / 'store'), KPC_FERS_STORE_MAX_DAYS='100000', STATES='US-RI', PASS='1', REGION='na', MINUTES='5',
                   TRIES_OUT=str(b / 'tries.json'), **extra)
        r = subprocess.run([sys.executable, str(runner)], cwd=w, capture_output=True, text=True, env=env, timeout=900)
        tries = json.loads((b / 'tries.json').read_text()) if (b / 'tries.json').is_file() else None
        return r, b, w, tries
    SECRET = _rx.compile(r'(?i)US-960[34]|Secret Park|Wdpa Park|9603\d|9604\d|NO TERMS')
    r, b, w, tries = e2e_run('public', KPC_FERS_PRIVATE_LOG=str(e2e / 'public-plog'))
    pub_files = {f.name: f.read_text() for f in (w / 'data/fers').glob('*.json')}
    spots = json.loads(pub_files.get('US-RI.json', '{}')).get('spots') or []
    miss = json.loads(pub_files.get('missing-na.json', '{}')).get('parks') or []
    check(r.returncode == 0 and tries == [] and 'store-missing-US-RI.json' in pub_files and any(set(x['refs']) == {'US-9601', 'US-9602'} for x in spots),
          f'S6: kpc_fers.main() runs end to end on a store with every socket shut: zero connection attempts, the files written ({r.returncode}, {tries}, {sorted(pub_files)})')
    # KPC owner, 2026-11-15 (owner rule never worse, R12): the old public row of the withheld park (old1) is carried UNCHANGED, with
    # only the mark 'not re-checked (outline held privately)'; that exact copy is the one place the park may appear
    _old1 = {'refs': ['US-9601', 'US-9603'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1], 'id': 'old1', 'names': {'US-9603': 'Secret Park'}}
    _car = [x for x in spots if x.get('store_held')]
    _rest = dict(json.loads(pub_files.get('US-RI.json', '{}')), spots=[x for x in spots if not x.get('store_held')])
    _other = {k: v for k, v in pub_files.items() if k != 'US-RI.json'}
    check(_car == [dict(_old1, store_held=S.HELD_TAG)] and not SECRET.search(json.dumps(_rest)) and not any(SECRET.search(t) for t in _other.values())
          and not SECRET.search(r.stdout + r.stderr),
          'M1: a public run names no park held for licence / WDPA records in ANY file (looked, missing, store-missing, report, any other row) nor in stdout / stderr; its old public row is carried unchanged (never worse)')
    m5 = [x for x in miss if x.get('ref') == 'US-9605']
    check(m5 and m5[0]['why'].startswith('held by the outline store') and 'no official boundary' not in m5[0]['why'],
          f'M1: a park the store held is on the Missing boundary list with the reason the store gave, never "no official boundary" ({[x.get("why") for x in m5]})')
    import time as _time
    check(isinstance(S._StoreTime(_time).monotonic(), float) and (lambda t0: (S._StoreTime(_time).sleep(60), _time.time() - t0)[1] < 1)(_time.time()),
          "store run: pass 1's one-minute wait for a slow agency server is skipped (the second try only reads the store again)")
    r, b, w, tries = e2e_run('private', KPC_FERS_STORE_KIND='private', KPC_FERS_PRIVATE_OUT=str(e2e / 'private-out'))
    pf = sorted(f.name for f in (e2e / 'private-out').glob('*'))
    check(r.returncode == 0 and tries == [] and 'run-log.txt' in pf and 'US-RI.json' in pf and json.loads((w / 'data/fers/US-RI.json').read_text())['spots'][0]['id'] == 'old1'
          and not _rx.search(r'US-96\d\d|Big Forest|Inner Park', r.stdout + r.stderr) and 'every detail is in the private folder' in r.stdout,
          f'M3: a private run writes only into its private folder and prints counts only: no park in stdout / stderr ({_rx.findall(r"US-96..", r.stdout + r.stderr)[:3]})')
    r, b, w, tries = e2e_run('actions', KPC_FERS_STORE_KIND='private', KPC_FERS_PRIVATE_OUT=str(e2e / 'actions-out'), GITHUB_ACTIONS='true')
    check(r.returncode == 89 and not (e2e / 'actions-out' / 'US-RI.json').exists() and 'KPC_FERS_PRIVATE_RUNNER' in r.stdout, 'M3: a private store run under GitHub Actions is refused (exit 89, nothing read) unless the private-runner switch is set')
    r, b, w, tries = e2e_run('runner', KPC_FERS_STORE_KIND='private', KPC_FERS_PRIVATE_OUT=str(e2e / 'runner-out'), GITHUB_ACTIONS='true', KPC_FERS_PRIVATE_RUNNER='1')
    check(r.returncode == 0 and (e2e / 'runner-out' / 'US-RI.json').is_file() and not _rx.search(r'US-96\d\d', r.stdout + r.stderr),
          'M3: with KPC_FERS_PRIVATE_RUNNER=1 it runs, and still prints no park')

# writer trace: every file kpc_fers.py writes goes through save_json -> _save_json_raw (the guarded write step), except the two
# direct writers the shut door turns off in a store run (live_save: the saved-live copy; _wsave: a live water tile) and, from the
# privacy grade of 2026-11-16 (F2), save_not_shown: the per-pair reasons for the pairs we stopped looking at. That one writes ONLY
# into a private folder named by KPC_FERS_NOT_SHOWN_DIR / KPC_FERS_PRIVATE_OUT / KPC_FERS_PRIVATE_LOG, refuses any folder inside a
# git work tree and writes nowhere when there is none (not_shown_file; tests/test_partial_boundary_nov15.py proves it).
import re as _re  # noqa: E402
_src = (ROOT / '.github/scripts/kpc_fers.py').read_text(encoding='utf-8')
_defs = [(m.start(), m.group(1)) for m in _re.finditer(r'^def (\w+)', _src, _re.M)]
def _owner(pos): return max((d for d in _defs if d[0] <= pos), default=(0, '?'))[1]
_direct = sorted({_owner(m.start()) for m in _re.finditer(r"\.write_text\(|\.write_bytes\(|gzip\.open\([^\n]*'w|[^.\w]open\([^\n]*['\"][wa]b?['\"]|json\.dump\(", _src)})
check(_direct == ['_wsave', 'live_save', 'save_not_shown'] and _src.count('def save_json') == 1
      and 'return _save_json_raw(p, no_denials(p, FCOUNT.apply(p, d)), *a, **k)' in _src
      and 'def not_shown_file' in _src and 'if _in_git_tree(' in _src,
      f'writer trace: kpc_fers.py writes files only through save_json -> _save_json_raw, plus live_save / _wsave (turned off in a store run) and save_not_shown (a private folder outside every git tree) ({_direct})')
_ss = (ROOT / '.github/scripts/kpc_fers_store.py').read_text(encoding='utf-8')
# KPC owner, 2026-11-15 (store trial fixes): + 2 private side files (store-held refs between passes, the store-withheld lists), both in the private folder
check(len(_re.findall(r'\.write_text\(', _ss)) == 6 and 'guard_write(p, doc)' in _ss and "if hasattr(KF, name): setattr(KF, name, lambda *a, **k: None)" in _ss,
      'writer trace: the store module writes the store-missing list (guarded), the diff command output (ids, names, statuses only; private folder) and the between-pass side files and withheld lists (private folder, Nov 15)')
try:
    import kpc_release as _REL
    check(S.BLOCKED_BUILDS == _REL.BLOCKED_BUILDS, 'the never-released list is the release tool\'s own (US-42797939226)')
except Exception as e: check(False, f'kpc_release import: {e}')  # noqa: BLE001
check('never released' in held(build(tmp / 'blk', 'US-ZZ', [P[3]], index_edit=lambda d: {**d, 'pack_commit': 'key build US-42797939226'}) and S.Store(tmp / 'blk', 45, today='2026-11-14'), 'US-9004', ['sgzza4']),
      'an area store whose index names the never-released build is NOT READY')

# the public-site door for 2-fers (kpc_fers_publish.py): a club-room / world / blocked row is never published, whatever the review
import kpc_fers_publish as PUB  # noqa: E402
okrow = {'id': 'a', 'refs': ['US-1', 'US-2'], 'kind': 'area', 'status': 'candidate'}
check(PUB.not_public_why(okrow) == '' and 'club_room_only' in PUB.not_public_why(dict(okrow, club_room_only=True)) and 'outside the US' in PUB.not_public_why(dict(okrow, refs=['US-1', 'GB-0001']))
      and 'never released' in PUB.not_public_why(dict(okrow, note='US-42797939226')), 'publish: club_room_only, world and never-released rows are refused')
pr = tmp / 'pubrepo'; pd = tmp / 'pubdata' / 'data' / 'fers'; pr.mkdir(); pd.mkdir(parents=True)
(pr / 'kpc-fers-reviewed.json').write_text(json.dumps({'reviewed': {'a': 'ok'}}))
(pd / 'US-KY.json').write_text(json.dumps({'spots': [dict(okrow, club_room_only=True, shape=[[-84, 37], [-84.01, 37], [-84.01, 37.01]], acres=1)]}))
r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_fers_publish.py'), 'layer', '--repo', str(pr), '--data', str(tmp / 'pubdata')], capture_output=True, text=True, env={**os.environ, 'KPC_FERS_LAYER': 'preview'})
check(r.returncode == 1 and 'club_room_only' in r.stdout and not (pr / 'preview' / 'ky-overlaps.geojson').exists(), f'publish: a reviewed club_room_only row stops the publish (exit 1, no file) ({r.returncode})')

# must-fix 4: one pair, several patches. The bot keeps ONE row per pair (the widest patch); the others say 'merged into one row'.
# Ids sort the narrow patch first, so a reader that takes the first row of the pair reports the narrow patch's width.
mx = {'spots': [{'id': 'US-2+US-1@area@44.271,-71.299', 'refs': ['US-1', 'US-2'], 'kind': 'area', 'wide_m': 23, 'status': 'merged into one row: US-2+US-1@area@44.272,-71.305', 'center': [44.271, -71.299]},
                {'id': 'US-2+US-1@area@44.272,-71.305', 'refs': ['US-1', 'US-2'], 'kind': 'area', 'wide_m': 59, 'status': 'candidate', 'center': [44.272, -71.305]}]}
rw = S._rows(mx)[(('US-1', 'US-2'), 'area')]
check(len(rw) == 1 and rw[0]['wide_m'] == 59, 'widths: the store module reads the pair row (59 m), never the merged patch (23 m) that sorts first')
nn2 = {'spots': []}; S.carry_rows(nn2, mx, {})
check([x['wide_m'] for x in nn2['spots']] == [59], 'widths: a carried pair keeps its pair row (59 m); the merged patch is not carried as a second row')

# ---------------------------------------------------------------- a real v3 store (made by the outline store tool full 3, synthetic squares)
import shutil  # noqa: E402
V3 = ROOT / 'tests' / 'fixtures' / 'fers-store-v3'
def v3(kind='private', edit=None, files=None):
    d = tmp / f'v3-{len(list(tmp.glob("v3-*")))}'; d.mkdir()
    for f in (files or [p.name for p in V3.iterdir() if p.name != 'README.md']): shutil.copy(V3 / f, d / f)
    if edit: edit(d)
    return S.Store(d, 100000, today='2026-11-14', kind=kind)
s3 = v3()
a3 = s3.area('US-ZA')
check(a3 is not None and s3.area('US-ZB') is not None and a3.idx['store_format_version'] == 'kpc-outline-store-index/3', 'v3: both area indexes open; the contract version is the one this reader reads')
g3, _, w3 = s3.groups_for('US-9150', 'US-ZA', ['sgzz50a', 'sgzz50b'])
check(not w3 and len(g3) == 2, f'v3: a park with tracts in two area files is assembled whole ({w3 or len(g3)} groups)')
check(sorted(json.load(open(V3 / 'index.json'))['parks']['US-9150']['records']) == ['sgzz50b'], "v3: (the tool's combined index.json keeps only one area's entry for that park: it is not read)")
check('index-US-ZA.json' in held(v3(files=['index.json', 'US-ZA.kpcstore.json.gz', 'US-ZB.kpcstore.json.gz']), 'US-9101', ['sgzz1'], 'US-ZA'), 'v3: only a combined index.json -> the area is refused with a plain reason')
def _ver(d):
    j = json.loads((d / 'index-US-ZA.json').read_text()); j['store_format_version'] = 'kpc-outline-store-index/5'; (d / 'index-US-ZA.json').write_text(json.dumps(j))
check('this reader reads' in held(v3(edit=_ver), 'US-9101', ['sgzz1'], 'US-ZA'), 'v3: an unknown store_format_version (/5) is refused (area held with the reason): fails closed')
def _ver4(d):
    j = json.loads((d / 'index-US-ZA.json').read_text()); j['store_format_version'] = 'kpc-outline-store-index/4'; (d / 'index-US-ZA.json').write_text(json.dumps(j))
_g3 = s3.groups_for('US-9101', 'US-ZA', ['sgzz1'])
check(not _g3[2] and _g3[0] == v3(edit=_ver4).groups_for('US-9101', 'US-ZA', ['sgzz1'])[0], 'v3: the format-3 store reads unchanged; the same index marked /4 reads the same (a record with no geometry_kind is an area)')
def _flip(d):
    f = d / 'US-ZA.kpcstore.json.gz'; b = bytearray(f.read_bytes()); b[-3] ^= 1; f.write_bytes(bytes(b))
check('sha256' in held(v3(edit=_flip), 'US-9101', ['sgzz1'], 'US-ZA'), 'v3: an area file that does not match its sha256 in the index is refused before use')
check('marked WDPA derived' in held(s3, 'US-9103', ['sgzz3'], 'US-ZA'), 'v3: wdpa_derived true holds the park (the store flag, with no WDPA words in any value)')
pub3 = v3('public')
check('needs the private store' in held(pub3, 'US-9102', ['sgzz2']) and not held(pub3, 'US-9101', ['sgzz1'], 'US-ZA'), 'v3: public store: publishable false is held, publishable true is read')
_, _, w9, i9 = s3.examine('US-9102', 'US-ZA', ['sgzz2'])
check(not w9 and i9['private']['sgzz2'] == {'licence_class': 'NO TERMS STATED', 'publish_basis': 'none', 'private_reason': 'licence not read yet'}, 'v3: private store: the record is used and its licence class, basis and private reason are kept for the club-room tag')
ok3, rows3 = S.fit_check(s3, ['US-ZA', 'US-ZB'], 3000)
check(ok3 and rows3['US-ZA']['verdict'] == rows3['US-ZB']['verdict'] == 'READY', 'v3: the memory gate reads the v3 indexes')
pb = build(tmp / 'basis', 'US-ZZ', [{'ref': 'US-9301', 'name': 'x', 'records': [rec('b1', [sq(-80, 40, 0.01)], publishable=True, publish_basis='none')]}])
check('needs the private store' in held(S.Store(pb, 45, today='2026-11-14', kind='public'), 'US-9301', ['b1']), 'v3: publishable true without a verified-row / owner-confirmed basis is not trusted')

# ---------------------------------------------------------------- change list
o = {'spots': [{'refs': ['US-1', 'US-2'], 'kind': 'area', 'status': 'candidate', 'center': [40.0, -80.0]}, {'refs': ['US-1', 'US-3'], 'kind': 'area', 'status': 'candidate', 'center': [40, -80]},
               {'refs': ['US-1', 'US-4'], 'kind': 'area', 'status': 'dropped in pass 3'}]}
nn = {'spots': [{'refs': ['US-2', 'US-1'], 'kind': 'area', 'status': 'very tight: x', 'center': [40.01, -80.0]}, {'refs': ['US-1', 'US-4'], 'kind': 'area', 'status': 'candidate', 'center': [40, -80]}]}
dd = S.diff_rows(o, nn)
check(dd['counts'] == {'same': 1, 'new': 1, 'gone': 1, 'moved': 1, 'status_changed': 1} and 'shape' not in json.dumps(dd), f'change list: same / new / gone / moved / status changed, no shapes ({dd["counts"]})')
check(S.grid_pairs({'a': [0, 0, 1, 1], 'b': [0.9, 0.9, 2, 2], 'c': [5, 5, 6, 6]}) == {('a', 'b')}, 'grid_pairs: only boxes that touch')

# ---------------------------------------------------------------- must-fix 3: the R12 text says what the code does (no rule change)
_ml = _src[_src.index('def missing_list'):_src.index('# ------------------------------------------------------------------ rasters')]
_rn = (ROOT / '.claude/RULES-NOW.md').read_text(encoding='utf-8')
_r12 = _rn[_rn.index('(12) MISSING BOUNDARY'):_rn.index('(13) KEEP IT CURRENT')]
check(all(x in _ml for x in ('(ref in G)', 'pip_groups(G[r], lo, la)', 'ref in KY_NOT_SURE or ref in PARTIAL', 'RET = retired()', 'if la is None or lo is None: continue',
                             '(ref in LN and ref not in PARTIAL)', "'Missing boundary: check the official map'"))
      and "if PARKS: raise RuntimeError('small batch: the missing-boundary list is kept as it was')" in _src and "lst = 'Approximate 2-fer: not the official boundary; needs more research'" in _src
      and all(x in _r12 for x in ('NO outline', 'pin sits inside another park', 'US-10102', 'line park tested by its official line', 'retired', 'bad POTA pin', 'Approximate 2-fer: not the official boundary', 'PARKS=', 'missing-<run>.json'))
      and 'a pair where one park has no official boundary' not in _r12 and _r12 in (ROOT / '.claude/notes/mapping.md').read_text(encoding='utf-8'),
      'R12: RULES-NOW.md (word for word from mapping.md) says what missing_list() does: per park with no outline, pin inside another outline or held by name; approximate / circle parks are tested')

# ---------------------------------------------------------------- hashes
import kpc_key_freeze as KFZ  # noqa: E402
# Nov 15 (KPC owner, 2026-11-15; the switch-over): kpc_fers.main() calls this module, so it left NOT_RULES for the 2-fer RULE_FILES (one declared move)
check('kpc_fers_store.py' not in KFZ.NOT_RULES and '.github/scripts/kpc_fers_store.py' in KFZ.RULE_FILES['fers'] and '.github/fers-store-areas.json' in KFZ.RULE_FILES['fers']
      and not any('kpc_fers_store' in f for k, v in KFZ.RULE_FILES.items() if k != 'fers' for f in v), 'kpc_fers_store.py and its area list are 2-fer rule files only (not in NOT_RULES, in no key rule list)')
want = {'us-key': 'd4ebfafce438', 'ca-key': 'ba480fa34fb6', 'world-key': '158325de87ce', 'fers': 'cef323de4c9a'}
try:
    import kpc_preflight as PF
    want = {k: PF.newest_hash(k) or v for k, v in want.items()}
except Exception: pass  # noqa: BLE001
got = {k: KFZ.rules_hash(k) for k in want}
check(got == want, f'rules hashes are the newest changelog hashes ({got})')
src = (ROOT / '.github' / 'scripts' / 'kpc_fers_store.py').read_text(encoding='utf-8')
check('urlopen' not in src and 'requests' not in src and 'http.client' not in src and '://' not in src, 'the module has no network code and names no host')
print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
