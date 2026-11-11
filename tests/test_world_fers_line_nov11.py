#!/usr/bin/env python3
"""World 2-fer line, KPC-Links side (owner rule, 2026-11-11). Offline: no network. Test only; no rule file is touched.
1 no world (W-*) region of the overlap finder is public (kpc-fers-regions.json): world 2-fers stay beta, members only
2 no world country is on the 2-fer ready list today, and the world key holds no owner / manager data a ready entry could name
3 the world line path: a record on a saved-copy-only host is read from the world saved copy (cache/world/W-XX.json.gz), and with no
  saved copy the park is held 'saved copy missing'; the host is never reached: kpc_net_guard refuses before any name lookup or socket (the test counts both)"""
import gzip, json, os, pathlib, sys, tempfile, types
HERE = pathlib.Path(__file__).resolve().parent.parent
S = HERE / '.github/scripts'
sys.path.insert(0, str(S))
os.chdir(HERE)
os.environ.setdefault('PASS', '2')
os.environ['HTTP_CACHE'] = ''
os.environ['REGION'] = 'world'
try: import cv2  # noqa: F401
except Exception: sys.modules['cv2'] = types.ModuleType('cv2')  # noqa: BLE001
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


# 1 members only
cfg = json.load(open(HERE / 'kpc-fers-regions.json', encoding='utf-8'))
world = [r for r in cfg['regions'] if any(str(f).startswith('W-') for f in r.get('files') or []) or str(r.get('id', '')).startswith('W-')]
check(not [r['id'] for r in world if r.get('public') is not False and r.get('public')], f'no world region is public ({[r["id"] for r in world]} listed; public ones: none)')
check(all(r.get('public') is False and r.get('beta') for r in world), 'every world region that exists is public:false and beta:true')

# 2 ready list
import kpc_fers_ready as FR
rd = FR.load_ready(HERE)
check(not any(FR.area_ready('W-' + c, rd) for c in ('GB', 'AU', 'FR', 'DE', 'JP', 'IE', 'AT')) and FR.area_ready('US-OH', rd) and FR.area_ready('CA-ON', rd),
      'ready list: US and Canada yes; no world country (W-GB W-AU W-FR W-DE W-JP W-IE W-AT) is ready')
keys = set()
for f in (HERE / 'data/world-key').glob('[A-Z][A-Z].json'):
    for p in (json.load(open(f)).get('parks') or {}).values(): keys |= set(p)
OWN = {'owner', 'own', 'manager', 'mang', 'owner_e', 'own_type', 'own_name', 'mang_type', 'mang_name', 'holder'}
check(not ({k.lower() for k in keys} & OWN), f'the world key park rows carry no owner / manager field (fields: {sorted(keys)})')

# 3 saved-copy-only host in the world path
import kpc_fers as K
K.REGION = 'world'
K.HC.DIR = ''
import socket
SOCK = []   # anything that gets as far as a name lookup or a connection: must stay empty (the guard refuses first)
socket.getaddrinfo = lambda *a, **k: SOCK.append(a) or (_ for _ in ()).throw(OSError('no network in this test'))
socket.socket.connect = lambda self, *a, **k: SOCK.append(a) or (_ for _ in ()).throw(OSError('no network in this test'))
CALLS = []   # the finder may still call get(); the shared guard (kpc_net_guard) must refuse before any lookup / socket
_real_get = K.get


def spy_get(url, params, tries=3, timeout=120):
    CALLS.append(url)
    return _real_get(url, params, 1, 1)


K.get = spy_get
K.time.sleep = lambda s: None
src = next(k for k, u in K.LAYERS_W.items() if isinstance(u, str) and not K.HC.kpc_net_guard.host_ok(u)[0] and K.source_of(1, False, k)[0])
RING = [[9.0, 48.0], [9.01, 48.0], [9.01, 48.01], [9.0, 48.01], [9.0, 48.0]]
check(K.saved_only_host(K.source_of(1, False, src)[0]), f'the world layer {src!r} is on a saved-copy-only host')
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    K.CACHE_W = td
    parks = {'W-1': {'st': 'W-DE', 'ids': [1], 'm': [[1, 'Saved Park', src, 'x']], 'names': {'0': 'Saved Park'}},
             'W-2': {'st': 'W-DE', 'ids': [2], 'm': [[2, 'Other Park', src, 'x']], 'names': {'0': 'Other Park'}}}
    PIN = {'W-1': ('Saved Park', 48.005, 9.005, '', 'Park', 'DE'), 'W-2': ('Other Park', 48.005, 9.005, '', 'Park', 'DE')}
    K.pins = lambda: PIN   # the park pins (POTA); never moved
    K.MISSING_SAVED.clear(); CALLS.clear()
    try: got, bad = K.download(parks, ['W-1', 'W-2'], K.DET, K.PREC)
    except AssertionError as e: got, bad = {}, set(); check(False, str(e))
    check(not SOCK and 'W-1' in bad and 'W-2' in bad and K.MISSING_SAVED.get('W-1') and K.MISSING_SAVED.get('W-2'), f'no saved copy at all: no lookup or connection at all (the guard refused), both parks held saved copy missing ({sorted(K.MISSING_SAVED)})')
    with gzip.open(td / 'W-DE.json.gz', 'wt') as fh:
        json.dump({'saved': '2026-11-01', 'recs': [{'id': 1, 'n': 'Saved Park', 'src': src, '_r': [RING]}]}, fh)
    K.MISSING_SAVED.clear(); CALLS.clear()
    try: got, bad = K.download(parks, ['W-1', 'W-2'], K.DET, K.PREC)
    except AssertionError as e: got, bad = {}, set(); check(False, str(e))
    check(not SOCK and got.get('W-1') == [[RING]] and 'W-2' in bad and K.MISSING_SAVED.get('W-2') and 'W-1' not in K.MISSING_SAVED,
          'a saved copy exists for one park: it is used; the other is held; still no lookup or connection')
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
