#!/usr/bin/env python3
"""KPC owner, 2026-11-16 (handoff 'proof of work', item 4): ONE record lookup for key, store and bot (kpc_record_key.store_key).
Contract test: one tiny store sample of each kind (US, Canada, world) in the REAL store format (index contract
kpc-outline-store-index/4, a gzip-member .kpcstore.json.gz), made up here (made-up squares, made-up refs and record ids; nothing
real, nothing private, nothing WDPA). A key join in each key's own row format is turned into the store key by the one function,
and the real store reader (kpc_fers_store.Store) must find the record by it. A change of either format fails here, not in a run.
Also: the committed US fixture (tests/fixtures/fers-store-v4) is read the same way, and kpc_fers_store.store_ids is this function."""
import gzip, hashlib, json, os, pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCR = ROOT / '.github' / 'scripts'
sys.path.insert(0, str(SCR))
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok: FAILS.append(what)


import kpc_record_key as RK  # noqa: E402
import kpc_fers_store as ST  # noqa: E402

# ---------------------------------------------------------------- the function
check(RK.store_key('US-RI', [57154, 'Test Park', 1, 'name']) == 57154, 'US: a key join -> the record id as it is')
check(RK.store_key('CA-AB', ['abc1', 'Test Park', 0.9, 'name']) == 'abc1', 'Canada: a key join -> the record id as it is')
check(RK.store_key('W-BE', [352, 'Test Site', 'EEA Natura 2000']) == 'W-BE:EEA Natura 2000:352', "world: '<area>:<layer>:<id>' (the case #216 fixed)")
check(RK.store_key('W-BE', ['275', 'x', 'BE: Réserves naturelles domaniales (approved layer 2)']) == 'W-BE:BE: Réserves naturelles domaniales (approved layer 2):275',
      'world: a layer name with a colon in it is kept whole')
check(RK.split_key('W-BE:BE: Réserves (layer 2):275') == ('W-BE', 'BE: Réserves (layer 2)', '275') and RK.split_key(57154) == ('', '', '57154'), 'split_key reads a world key back')
for bad in (('W-BE', [352, 'x']), ('XX-1', [1])):
    try: RK.store_key(*bad); ok = False
    except ValueError: ok = True
    check(ok, f'a join that cannot be a store key fails loudly ({bad})')
check(ST.store_ids({'st': 'W-BE', 'ids': [352], 'm': [[352, 'x', 'EEA Natura 2000']]}) == ['W-BE:EEA Natura 2000:352'] and ST.store_ids({'st': 'US-RI', 'ids': [1, 2]}) == [1, 2],
      'kpc_fers_store.store_ids is this function (the bot and the store read through it)')
src = (SCR / 'kpc_fers_store.py').read_text()
check('kpc_record_key.park_keys(p)' in src and src.count('f"{p[\'st\']}:{x[2]}:{x[0]}"') == 0, 'no second copy of the world key format in the store reader')

# ---------------------------------------------------------------- tiny real-format store samples, one per kind
def enc(ring):
    o, px, py = [], 0, 0
    for i, (x, y) in enumerate(ring):
        X, Y = int(round(x * 1e6)), int(round(y * 1e6)); o += [X, Y] if i == 0 else [X - px, Y - py]; px, py = X, Y
    return o


def sq(x0, y0, d): return [[x0, y0], [x0 + d, y0], [x0 + d, y0 + d], [x0, y0 + d], [x0, y0]]


def rec(key, layer, rid, ring):
    e = [enc(ring)]
    return {'key': str(key), 'layer': layer, 'record_id': str(rid), 'record_name': 'made-up record', 'licence_class': 'PUBLIC DOMAIN', 'publishable': True,
            'publish_basis': 'verified-row', 'credit_line': 'made-up test record', 'wdpa_derived': False, 'private_reason': '', 'source': 'live', 'use': True,
            'q': 6, 'boundary_kind': 'official', 'geometry_kind': 'area', 'rings': e, 'points': sum(len(x) // 2 for x in e), 'sha256': ST.geometry_sha256(e)}


def make_store(d, area, parks):
    fn = f'{area}.kpcstore.json.gz'
    raw = bytearray(gzip.compress(('{"kpcstore": 1, "area": "%s", "parks": [' % area).encode(), mtime=0)); idx = {}
    for i, p in enumerate(parks):
        bb = gzip.compress(((',' if i else '') + json.dumps(p)).encode(), mtime=0)
        idx[p['ref']] = {'file': fn, 'o': len(raw), 'n': len(bb), 'grade': 'official', 'circle': False, 'records': [r['key'] for r in p['records']], 'points': 5,
                         'date': '2026-11-16', 'geometry_kind': 'area', 'fp': hashlib.sha256('|'.join(r['sha256'] for r in p['records']).encode()).hexdigest()}
        raw += bb
    raw += gzip.compress(b']}', mtime=0); (d / fn).write_bytes(bytes(raw))
    (d / f'index-{area}.json').write_text(json.dumps({'format': 1, 'store_format_version': 'kpc-outline-store-index/4', 'geometry_kinds': ['area', 'line', 'pin'],
                                                      'area': area, 'made': '2026-11-16', 'parks': idx,
                                                      'files': {fn: {'bytes': len(raw), 'sha256': hashlib.sha256(bytes(raw)).hexdigest()}}}))


TMP = pathlib.Path(tempfile.mkdtemp(prefix='kpc-record-key-'))
# each sample: (area, ref, the key's join row in that key's format, layer as the store files it, record id)
SAMPLES = [('US-ZQ', 'US-99901', [99901, 'Test Us Park', 1, 'name'], 'padus', 99901),
           ('CA-ZQ', 'CA-99902', ['zq2', 'Test Ca Park', 0.9, 'name'], 'cpcad', 'zq2'),
           ('W-ZQ', 'ZQ-0903', [903, 'Test World Park', 'test layer: two'], 'test layer: two', 903)]
for area, ref, join, layer, rid in SAMPLES:
    key = RK.store_key(area, join)
    make_store(TMP, area, [{'ref': ref, 'name': join[1], 'records': [rec(key, layer, rid, sq(-71.5, 41.5, 0.01))]}])
st = ST.Store(TMP, 100000, today='2026-11-16', kind='private')
for area, ref, join, layer, rid in SAMPLES:
    p = {'st': area, 'ids': [join[0]], 'names': {}}
    if area.startswith('W-'): p['m'] = [join]
    ids = ST.store_ids(p)
    try: g, left, why = st.groups_for(ref, area, ids)
    except Exception as e: g, left, why = None, [], f'{type(e).__name__}: {e}'  # noqa: BLE001
    check(bool(g) and not why and abs(g[0][0][0][0] + 71.5) < 1e-6, f'{area}: the key join {join[:1] + join[2:3]} finds its store record by {ids} ({why or "read"})')
    if area.startswith('W-'):   # the bare key id (the #216 bug) must NOT find it: the formats really differ
        g2, _, why2 = st.groups_for(ref, area, [join[0]])
        check(not g2 and why2, 'world: the bare key id does not find the record (so the shared function is the only way)')

# ---------------------------------------------------------------- the committed US fixture, by the key's own join rows
FIX = ROOT / 'tests' / 'fixtures' / 'fers-store-v4'
sf = ST.Store(FIX, 100000, today='2026-11-15', kind='public')
for ref, rid in (('US-99001', 99010), ('US-99002', 99020)):
    g, _, why = sf.groups_for(ref, 'US-RI', ST.store_ids({'st': 'US-RI', 'ids': [RK.store_key('US-RI', [rid, 'x', 1, 'name'])]}))
    check(bool(g) and not why, f'the committed US fixture is read by the key join of {ref} ({why or "read"})')

print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
