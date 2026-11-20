#!/usr/bin/env python3
"""KPC owner, 2026-11-16 (handoff 'proof of work', items 1 and 2; item 1 alone is tests/test_fers_proof_of_work_nov16.py, from main). Offline, on the made-up store fixture tests/fixtures/fers-store-v4
(made-up squares, made-up refs US-99001..US-99006 under US-RI; nothing real, nothing private).
1 proof of work: a stopped run exits 84 with a receipt that says so; an area of which pass 1 read no outline exits 85, keeps its
  previous file and is never 'measured'; a store run writes one receipt per area (expected, read, held, pairs, rules hash, store
  date, engine, seconds per stage) and 'kpc_fers_receipt.py check' decides done from it (no receipt = red); an area the store
  does not hold is 'store missing', never an answer
2 one program per area in store mode: passes 1, 2, 3, 5 in ONE process (kpc_fers_store.py chain) write byte for byte the same
  2-fer files as four separate processes (the receipt aside: it has times); the 5 m-only switch is off by default, 'count' is
  read only in a store run, and the finer-grid-only spots are listed in the private folder"""
import gzip, json, os, pathlib, shutil, subprocess, sys, tempfile

for k in list(os.environ):
    if 'proxy' in k.lower(): os.environ.pop(k)
ROOT = pathlib.Path(__file__).resolve().parent.parent
SCR = ROOT / '.github' / 'scripts'
FIX = ROOT / 'tests' / 'fixtures' / 'fers-store-v4'
sys.path.insert(0, str(SCR))
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok: FAILS.append(what)


import kpc_fers_receipt as R  # noqa: E402
import kpc_fers_store as ST  # noqa: E402

# ---------------------------------------------------------------- unit: verdicts and the done check
v = R.area_verdicts({'US-RI', 'US-NY', 'US-ZQ'}, {'US-RI': 5, 'US-NY': 3}, {'US-RI': 5}, {'US-ZQ': {'verdict': 'NOT READY', 'why': 'no index-US-ZQ.json'}}, True)
check(v == {'US-RI': 'measured', 'US-NY': 'store empty', 'US-ZQ': 'store missing: no index-US-ZQ.json'}, f'verdicts: measured / store empty / store missing ({v})')
check(R.area_verdicts({'US-RI'}, {'US-RI': 4}, {}, None, False) == {'US-RI': 'measured nothing: 0 of 4 read'}, 'not a store run: 0 of N read is "measured nothing"')
good = {'passes': {str(p): {'areas': {'US-RI': 'measured'}, 'rules_hash': 'abc'} for p in (1, 2, 3, 5)}}
check(R.check(good, [1, 2, 3, 5], 'abc') == [], 'check: every pass measured = done')
check(R.check(None, [1]) and R.check({'passes': {}}, [1]), 'check: no receipt = red')
check(any('pass 5' in x for x in R.check({'passes': {k: v for k, v in good['passes'].items() if k != '5'}}, [1, 2, 3, 5])), 'check: a missing pass = red')
check(any('store empty' in x for x in R.check({'passes': {'1': {'areas': {'US-RI': 'store empty'}}}}, [1])), 'check: store empty = red, never done')
check(any('stopped' in x for x in R.check({'passes': {'1': {'areas': {}, 'stopped': 'x'}}}, [1])), 'check: stopped early = red')
check(any('rules hash' in x for x in R.check(good, [1], 'zzz')), 'check: another rules hash = red')
s = R.Stages(100.0); s.mark('pass 1 saved outlines', 101.5); s.mark('pass 1 downloads (5 parks)', 104.0); s.mark('pass 1 downloads (2 parks)', 105.0)
check(s.table() == {'pass 1 saved outlines': 1.5, 'pass 1 downloads': 3.5}, f'seconds per stage add up by stage ({s.table()})')
src = (SCR / 'kpc_fers.py').read_text()
check(src.count('raise RECEIPT.StoppedEarly(') >= 5 and "notice('2-fer bot', msg); return\n" not in src, 'every early stop of kpc_fers.main() raises StoppedEarly (exit 84), none returns 0')

try:
    import numpy, cv2  # noqa: F401
    HAVE = True
except Exception: HAVE = False  # noqa: BLE001
TMP = pathlib.Path(tempfile.mkdtemp(prefix='kpc-fers-pow-'))
st_fix = ST.Store(FIX, 100000, today='2026-11-15', kind='public')
REC = {'US-99001': 99010, 'US-99002': 99020, 'US-99003': 99030, 'US-99004': 99040}
PINS = {'US-99001': ('Test Forest', 41.63, -71.57, 'National Forest'), 'US-99002': ('Test Inner Park', 41.6275, -71.5725, 'State Park'),
        'US-99003': ('Test Lake Park', 41.67, -71.53, 'State Park'), 'US-99004': ('Test Lake Area', 41.6675, -71.5325, 'Wildlife Management Area'),
        'US-99005': ('Test Trail', 41.6352, -71.57, 'National Recreation Trail'), 'US-99006': ('Test Pin', 41.69, -71.51, 'State Park')}


def layout(t, recs_ok=True, extra_area=None, old=None):
    for d in ('data/parkinfo', 'data/trails', 'data/us-key', 'data/ca-key', 'data/canada-bounds', 'data/fers', 'cache/us', 'cache/ca', 'cache/fers'):
        (t / d).mkdir(parents=True, exist_ok=True)
    (t / 'data/trails/index.json').write_text('[]'); (t / 'data/trails/index-state.json').write_text('[]')
    pins, key, recs = {}, {}, []
    for ref, (nm, la, lo, kind) in PINS.items():
        pins[ref] = [nm, '', kind, '', '', la, lo]
        if ref in REC:
            key[ref] = {'g': 'official', 'm': [[REC[ref], nm, 1, 'name']]}
            g, _, w = st_fix.groups_for(ref, 'US-RI', [REC[ref]])
            recs.append({'OBJECTID': REC[ref], 'Unit_Nm': nm, 'Category': 'Fee', 'Pub_Access': 'OA', 'Own_Type': 'FED', '_r': g[0]})
        else: key[ref] = {'g': 'pin', 'm': []}
    (t / 'data/parkinfo/US-RI.json').write_text(json.dumps({'parks': pins}))
    (t / 'data/us-key/US-RI.json').write_text(json.dumps({'parks': key}))
    with gzip.open(t / 'cache/us/US-RI.json.gz', 'wt') as fh: json.dump({'saved': '2026-11-01', 'recs': recs if recs_ok else []}, fh)
    if extra_area:
        (t / f'data/parkinfo/{extra_area}.json').write_text(json.dumps({'parks': {'US-99101': ['Test Far Park', '', 'State Park', '', '', 39.0, -75.5]}}))
        (t / f'data/us-key/{extra_area}.json').write_text(json.dumps({'parks': {'US-99101': {'g': 'official', 'm': [[99101, 'Test Far Park', 1, 'name']]}}}))
    for a, d in (old or {}).items(): (t / f'data/fers/{a}.json').write_text(json.dumps(d))
    shutil.copytree(FIX, t / 'store-copy' / 'store', ignore=shutil.ignore_patterns('README.md'))


WRAP = """import json, os, runpy, sys, urllib.request
def _audit(ev, args):
    if ev in ('socket.connect', 'socket.getaddrinfo', 'socket.gethostbyname', 'urllib.Request'): raise OSError('test: no network (' + ev + ')')
sys.addaudithook(_audit)
S = sys.argv[1]; sys.path.insert(0, S)
import kpc_http_cache as HC
def _off(url, params, fetch): raise RuntimeError('offline test: no map is read')
HC.cached = _off
if len(sys.argv) > 2 and sys.argv[2] == 'chain':
    sys.argv = [S + '/kpc_fers_store.py', 'chain', sys.argv[3]]
    runpy.run_path(S + '/kpc_fers_store.py', run_name='__main__')
else:
    sys.argv = [S + '/kpc_fers.py']
    runpy.run_path(S + '/kpc_fers.py', run_name='__main__')
"""


def env_for(t, **kw):
    e = {k: v for k, v in os.environ.items() if not k.startswith(('KPC_', 'PASS', 'MINUTES', 'STATES', 'REGION', 'RUN_TAG', 'PARKS', 'GITHUB_', 'WATER_STORE'))}
    e.update({'MINUTES': '60', 'STATES': 'US-RI', 'REGION': 'na', 'RUN_TAG': 'testri', 'KPC_FERS_LIVE_DIR': str(t / 'cache/fers')})
    e.update(kw); return e


def store_env(t, **kw):
    return env_for(t, KPC_FERS_FROM_STORE='on', KPC_FERS_STORE_DIR=str(t / 'store-copy' / 'store'), KPC_FERS_STORE_MAX_DAYS='100000',
                   KPC_FERS_STORE_KIND='public', KPC_FERS_PRIVATE_LOG=str(TMP / ('priv-' + t.name)), **kw)


def go(t, env, args=()):
    (t / 'wrap.py').write_text(WRAP)
    r = subprocess.run([sys.executable, '-B', str(t / 'wrap.py'), str(SCR)] + list(args), cwd=t, env=env, capture_output=True, text=True, timeout=900)
    return r.returncode, r.stdout + r.stderr


def fers_files(t):
    # the receipt has seconds, and the run report has the process's memory (MB now / peak): both differ by nature, nothing else may
    out = {}
    for p in sorted((t / 'data/fers').glob('*')):
        if not p.is_file() or p.name.startswith('receipt-'): continue
        b = p.read_bytes()
        if p.name.startswith('report-'):
            d = json.loads(b)
            for k, v in d.items():
                if isinstance(v, dict): [v.pop(x) for x in [x for x in v if x.startswith('memory')]]
            b = json.dumps(d, sort_keys=True).encode()
        out[p.name] = b
    return out


def receipt(t, tag='testri'):
    f = t / 'data/fers' / f'receipt-{tag}.json'
    return json.loads(f.read_text()) if f.is_file() else None


if not HAVE:
    print('SKIP the end-to-end part: numpy / cv2 not installed')
else:
    # ------------------------------------------------------------ 1 stopped early: exit 84 + a receipt that says so
    t = TMP / 'stopped'; t.mkdir(); layout(t); shutil.rmtree(t / 'data/parkinfo')
    rc, out = go(t, env_for(t, PASS='1'))
    rr = receipt(t)
    check(rc == 84 and rr and 'missing' in rr['passes']['1']['stopped'] and R.check(rr, [1]), f'stopped early (no park list): exit 84, the receipt says why, check is red ({rc})')
    # ------------------------------------------------------------ 1 pass 1 read 0 outlines of an area with official parks: exit 85
    t = TMP / 'empty'; t.mkdir(); layout(t, recs_ok=False, old={'US-RI': {'st': 'US-RI', 'spots': [], 'marker': 'previous file'}})
    rc, out = go(t, env_for(t, PASS='1'))
    rr = receipt(t)
    a = ((rr or {}).get('passes') or {}).get('1', {}).get('areas', {})
    check(rc == 85 and a.get('US-RI', '').startswith('measured nothing') and json.loads((t / 'data/fers/US-RI.json').read_text()).get('marker') == 'previous file',
          f"pass 1 read no outline: exit 85, 'measured nothing', the area keeps its previous file ({rc}, {a})")
    # ------------------------------------------------------------ 1 + 2: separate passes vs one process, the same files
    ts = TMP / 'separate'; ts.mkdir(); layout(ts)
    tc = TMP / 'chain'; tc.mkdir(); layout(tc)
    codes = []
    for p in (1, 2, 3, 5):
        rc, out = go(ts, store_env(ts, PASS=str(p))); codes.append(rc)
        if rc: print(out[-1500:]); break
    rc_c, out_c = go(tc, store_env(tc), ('chain', '1,2,3,5'))
    if rc_c: print(out_c[-2500:])
    fs, fc = fers_files(ts), fers_files(tc)
    diff = sorted(n for n in set(fs) | set(fc) if fs.get(n) != fc.get(n))
    check(codes == [0, 0, 0, 0] and rc_c == 0 and fs and not diff, f'one process (chain 1,2,3,5) writes byte for byte the same 2-fer files as four processes ({codes}, {rc_c}, differ: {diff[:6]})')
    check('pass 5 in the same process' in out_c and out_c.count('outline store::KPC_FERS_FROM_STORE=on') == 1, 'the store is installed once for the four passes')
    rs, rc_ = receipt(ts), receipt(tc)
    ok = bool(rs and rc_) and sorted(rs['passes']) == sorted(rc_['passes']) == ['1', '2', '3', '5']
    for k in ('parks expected', 'parks read', 'parks held', 'pairs tested', 'areas', 'rules_hash', 'store date'):
        ok = ok and all(rs['passes'][p][k] == rc_['passes'][p][k] for p in rs['passes'])
    check(ok, 'the receipts of both ways agree on everything but the seconds')
    n2 = lambda r: str(((r or {}).get('passes', {}).get('2') or {}).get('note') or '')
    check(n2(rc_).startswith('store run: pass 2 not run') and n2(rs) == n2(rc_), "the one process keeps main's pass-2 skip: pass 2 of a store run does nothing and its receipt section says so")
    p1 = (rc_ or {}).get('passes', {}).get('1', {})
    check(p1.get('areas') == {'US-RI': 'measured'} and p1.get('parks expected', {}).get('US-RI') == 4 and p1.get('parks read', {}).get('US-RI') == 4
          and p1.get('store date', {}).get('US-RI') and p1.get('rules_hash') and p1.get('engine', {}).get('files') and p1.get('seconds per stage')
          and p1.get('pairs tested', 0) >= 1, f'the receipt: expected, read, held, pairs, rules hash, store date, engine, seconds per stage ({ {k: p1.get(k) for k in ("parks expected", "parks read", "pairs tested")} })')
    r0 = subprocess.run([sys.executable, str(SCR / 'kpc_fers_receipt.py'), 'check', '--dir', str(tc / 'data/fers'), '--tag', 'testri', '--passes', '1,2,3,5', '--rules', p1.get('rules_hash') or 'x'], capture_output=True, text=True)
    r1 = subprocess.run([sys.executable, str(SCR / 'kpc_fers_receipt.py'), 'check', '--dir', str(tc / 'data/fers'), '--tag', 'nosuch', '--passes', '1'], capture_output=True, text=True)
    check(r0.returncode == 0 and r1.returncode == 2 and 'no receipt' in r1.stdout, f'check: done from the receipt (0), no receipt = red (2) ({r0.returncode}, {r1.returncode})')
    blob = json.dumps(rc_)
    check(not any(n in blob for n, *_ in PINS.values()) and 'US-990' not in blob and 'store-copy' not in blob, 'the receipt holds counts only: no park name, no ref, no store path')
    fo = sorted((TMP / ('priv-' + tc.name)).glob('fine-only-testri-p*.json'))
    # main (Nov 16, store runs: three passes of work): a store run's pass 2 does nothing, so only pass 3 lists them
    check([f.name for f in fo] == ['fine-only-testri-p3.json'] and all(json.loads(f.read_text())['mode'] == 'count' for f in fo),
          f'the finer-grid-only spots are listed for pass 3 in the private folder (pass 2 is skipped in a store run); the switch file is count ({[f.name for f in fo]})')
    # ------------------------------------------------------------ 1 an area the store does not hold: store missing, red
    tm = TMP / 'missing'; tm.mkdir(); layout(tm, extra_area='US-ZQ')
    rc, out = go(tm, store_env(tm, PASS='1', STATES='US-RI US-ZQ'))
    a = ((receipt(tm) or {}).get('passes') or {}).get('1', {}).get('areas', {})
    check(rc == 0 and a.get('US-RI') == 'measured' and a.get('US-ZQ', '').startswith('store missing'), f"an area the store does not hold is 'store missing' (red), the others measured ({a})")
    # ------------------------------------------------------------ 2 the switch: off by default; 'count' only in a store run
    import importlib
    os.environ.pop('KPC_FERS_FINE_ONLY', None)
    os.environ['KPC_FERS_FINE_ONLY'] = 'count'
    os.environ['MINUTES'] = '1'
    KF = importlib.import_module('kpc_fers')
    check(KF.fine_only_mode() == 'off', 'the switch is read only in a store run (a run that downloads keeps its passes as they are)')
    ST.STORE_ON = True; sys.modules['kpc_fers_store'] = ST
    check(KF.fine_only_mode() == 'count', "with the store on, KPC_FERS_FINE_ONLY=count is read")
    os.environ.pop('KPC_FERS_FINE_ONLY')
    check(KF.fine_only_mode() == 'count', 'the switch file is count, so a store run counts a separate piece')
    os.environ['KPC_FERS_FINE_ONLY'] = 'off'
    check(KF.fine_only_mode() == 'off', 'the environment can turn that count off')
    KF.set_pass(3)
    # The made-up spot needs a width and a box. Without them the size test and the box test cannot run (R-2F5).
    d = {'spots': [{'id': 'a', 'refs': ['US-1', 'US-2'], 'kind': 'area', 'passes': [1, 1, 0], 'status': 'pass 2',
                    'wide_m': 80, 'box': [-71.05, 41.00, -71.04, 41.01]}]}
    nk = {'US-1+US-2@area': [{'refs': ['US-1', 'US-2'], 'kind': 'area', 'center': [41.0, -71.0], 'acres': 3.0, 'wide_m': 80, '_used': 1},
                             {'refs': ['US-1', 'US-2'], 'kind': 'area', 'center': [41.2, -71.2], 'acres': 2.0, 'wide_m': 30,
                              'box': [-71.30, 41.20, -71.29, 41.21]}]}
    KF.FINE_ONLY.clear(); add = KF.fine_only_spots(d, nk, '2026-11-16', 'US-RI')
    check(add == [] and len(d['spots']) == 1 and len(KF.FINE_ONLY) == 1 and KF.FINE_ONLY[0]['grid_m'] == 5.0, 'switch off: the 5 m-only spot is listed, no row is added')
    os.environ['KPC_FERS_FINE_ONLY'] = 'count'
    for v in nk.values():
        for n in v: n.pop('_fine', None)
    KF.FINE_ONLY.clear(); add = KF.fine_only_spots(d, nk, '2026-11-16', 'US-RI')
    check(len(add) == 1 and add[0]['fine_only'] == '5 m grid' and add[0]['passes'] == [1, 1, 1] and len(d['spots']) == 2, 'switch count: the spot becomes a row of its own, marked fine_only, decided by pass 3')
    os.environ.pop('KPC_FERS_FINE_ONLY'); ST.STORE_ON = False
    # the separate passes stay for runs whose shapes differ (no chain without the store switch)
    rc, out = go(TMP / 'separate', env_for(TMP / 'separate'), ('chain', '1,2,3,5'))
    check(rc == 2 and 'store runs only' in out, 'the one-process chain refuses a run that is not a store run (the separate passes stay for it)')

print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
