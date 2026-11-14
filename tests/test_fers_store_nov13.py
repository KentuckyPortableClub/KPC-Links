#!/usr/bin/env python3
"""KPC owner, 2026-11-13: kpc_fers_store.py (2-fer outlines from the outline store; prep, OFF by default).
Offline: proxy variables dropped, every socket connect refused. Synthetic stores (format 1) are built in a temp folder.
Covers: switch off = nothing changes; the reader's checks; download()'s form; every kind of damage HOLDS (never a crash);
no half parks; WDPA anywhere in a record or park; licences (public store holds unpublishable parks, private store tags rows
club-room only); lazy holding (nothing unpacked at download, a points budget, a store changed mid-run is loud); the area gate
(missing / stale area stops before anything is saved: exit 87); the memory gate (exit 88, one row per area); no live pair
vanishes (carried rows); the join-review rule; corridors only from the saved copy; the change list; the real kpc_fers module
switched on; the rules hashes do not move."""
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
            'publishable': kw.pop('publishable', True), 'source': 'live', 'use': use, 'q': 6, 'rings': e, 'points': sum(len(x) // 2 for x in e), 'sha256': S.geometry_sha256(e), **kw}

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
    doc = {'format': 1, 'area': area, 'made': made + 'T00:00:00-06:00', 'parks': idx}
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
     {'ref': 'US-9009', 'name': 'Private Park', 'grade': 'official', 'records': [rec('sgzza9', [sq(-79.995, 40.005, 0.001)], publishable=False, licence_class='NO TERMS STATED')]}]
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
check(not w and info['private'] == {'sgzza9': 'NO TERMS STATED'}, 'licence: on the private store the park is used and its unpublishable records are named')
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
        base = {'KPC_FERS_FROM_STORE': 'on', 'KPC_FERS_STORE_DIR': str(tmp / 'store'), 'KPC_FERS_STORE_MAX_DAYS': '100000', 'KPC_FERS_STORE_KIND': 'private'}
        orig = {k: getattr(KF, k) for k in ('download', 'saved_us', 'saved_ca', 'live_load', 'pc_tag')}
        KF.ONLY = {'US-QQ'}
        try: S.install(KF, env=base); code = None
        except SystemExit as e: code = e.code
        rowsf = work / 'data' / 'fers' / f'store-missing-{KF.area_name()}.json'
        rows = json.loads(rowsf.read_text())
        check(code == 87 and rows['areas']['US-QQ']['verdict'] == 'NOT READY' and KF.download is orig['download'], 'area gate: a missing area store exits 87 before pass 1 (nothing replaced, nothing to save), its row written')
        KF.ONLY = {'US-ZZ'}; S.AREA_ROWS.clear()
        try: S.install(KF, env={**base, 'KPC_FERS_STORE_MAX_DAYS': '0'}); code = None
        except SystemExit as e: code = e.code
        check(code == 87 and KF.download is orig['download'], 'area gate: a stale area store exits 87 too')
        S.AREA_ROWS.clear()
        try: S.install(KF, env={**base, 'KPC_FERS_STORE_LIMIT_MB': '100'}); code = None
        except SystemExit as e: code = e.code
        rows = json.loads((work / 'data' / 'fers' / f'store-missing-{KF.area_name()}.json').read_text())
        check(code == 88 and rows['areas']['US-ZZ']['verdict'] == 'WILL NOT FIT' and KF.download is orig['download'], 'memory gate: install exits 88 with the area row when the run will not fit')
        S.AREA_ROWS.clear()
        check(S.install(KF, env=base) is True and KF.download is not orig['download'] and S.STORE_ON, 'switch on: download() is replaced in this process only')
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
        (work / 'data' / 'fers' / 'US-ZZ.json').write_text(json.dumps({'st': 'US-ZZ', 'pass3': '2026-10-29', 'spots': [
            {'refs': ['US-9001', 'US-9005'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1], 'id': 'a'},
            {'refs': ['US-9001', 'US-9009'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 1, 1], 'id': 'b'}]}))
        d = KF.pc_tag({'st': 'US-ZZ', 'spots': [{'refs': ['US-9001', 'US-9009'], 'kind': 'area', 'status': 'candidate', 'passes': [1, 0, 0]}]})
        byp = {tuple(x['refs']): x for x in d['spots']}
        check(byp[('US-9001', 'US-9005')]['status'].startswith('not sure: held: US-9005') and byp[('US-9001', 'US-9009')].get('club_room_only'),
              'switch on: the save path carries the held pair as a "not sure: held" row and tags the private-outline row club_room_only')
        check(not OPENED, f'no network: no connection was attempted ({OPENED[:2]})')
    finally:
        os.chdir(cwd)
prog = tmp / 'exit.py'
prog.write_text('import sys; sys.path.insert(0, %r)\nimport kpc_fers_store as S\nclass K: pass\nk = K(); k.REGION = "na"; k.OUT = %r; k.ONLY = {"US-ZZ"}; k.pc_tag = lambda d: d; k.area_name = lambda: "zz"\n'
                'print(S.install(k, env={"KPC_FERS_FROM_STORE": "on", "KPC_FERS_STORE_DIR": %r, "KPC_FERS_STORE_MAX_DAYS": "100000"}))\n' % (str(ROOT / '.github/scripts'), str(tmp / 'out'), str(tmp / 'store')))
r = subprocess.run([sys.executable, str(prog)], capture_output=True, text=True)
fl2 = tmp / 'out' / 'store-missing-zz.json'
check(r.stdout.strip().endswith('True') and fl2.is_file() and json.loads(fl2.read_text())['parks'] == {} and json.loads(fl2.read_text())['areas']['US-ZZ']['verdict'] == 'READY',
      'the store-missing list is written at exit even with nothing held')

# ---------------------------------------------------------------- change list
o = {'spots': [{'refs': ['US-1', 'US-2'], 'kind': 'area', 'status': 'candidate', 'center': [40.0, -80.0]}, {'refs': ['US-1', 'US-3'], 'kind': 'area', 'status': 'candidate', 'center': [40, -80]},
               {'refs': ['US-1', 'US-4'], 'kind': 'area', 'status': 'dropped in pass 3'}]}
nn = {'spots': [{'refs': ['US-2', 'US-1'], 'kind': 'area', 'status': 'very tight: x', 'center': [40.01, -80.0]}, {'refs': ['US-1', 'US-4'], 'kind': 'area', 'status': 'candidate', 'center': [40, -80]}]}
dd = S.diff_rows(o, nn)
check(dd['counts'] == {'same': 1, 'new': 1, 'gone': 1, 'moved': 1, 'status_changed': 1} and 'shape' not in json.dumps(dd), f'change list: same / new / gone / moved / status changed, no shapes ({dd["counts"]})')
check(S.grid_pairs({'a': [0, 0, 1, 1], 'b': [0.9, 0.9, 2, 2], 'c': [5, 5, 6, 6]}) == {('a', 'b')}, 'grid_pairs: only boxes that touch')

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
