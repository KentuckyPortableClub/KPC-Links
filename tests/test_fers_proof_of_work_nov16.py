#!/usr/bin/env python3
"""KPC owner, 2026-11-16 (handoff 'proof of work', item 1; round 1). Offline, on the made-up store fixture tests/fixtures/fers-store-v4
(made-up squares, made-up refs US-99001..US-99006 under US-RI; nothing real, nothing private).
1 proof of work: a stopped run exits 84 with a receipt that says so; an area of which pass 1 read no outline exits 85, keeps its
  previous file and is never 'measured'; a store run writes one receipt per area (expected, read, held, pairs, rules hash, store
  date, engine, seconds per stage) and 'kpc_fers_receipt.py check' decides done from it (no receipt = red); an area the store
  does not hold is 'store missing', never an answer"""
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
check(R.tag_from_env({'REGION': 'ky'}) == 'ky' and R.tag_from_env({'STATES': 'US-RI us-ny'}) == 'US-NY-US-RI' and R.tag_from_env({'RUN_TAG': 'NE-1', 'REGION': 'ky'}) == 'ne-1',
      'check finds the receipt by the same tag the bot uses (RUN_TAG, ky, or the states)')
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
    # ------------------------------------------------------------ 1 a store run: one receipt section per pass, check decides done
    tc = TMP / 'store'; tc.mkdir(); layout(tc)
    codes = []
    for p in (1, 2, 3, 5):
        rc, out = go(tc, store_env(tc, PASS=str(p))); codes.append(rc)
        if rc: print(out[-1500:]); break
    rc_ = receipt(tc)
    check(codes == [0, 0, 0, 0] and bool(rc_) and sorted(rc_['passes']) == ['1', '2', '3', '5'], f'a store run: every pass exits 0 and adds its section to the receipt ({codes})')
    p1 = (rc_ or {}).get('passes', {}).get('1', {})
    check(p1.get('areas') == {'US-RI': 'measured'} and p1.get('parks expected', {}).get('US-RI') == 4 and p1.get('parks read', {}).get('US-RI') == 4
          and p1.get('store date', {}).get('US-RI') and p1.get('rules_hash') and p1.get('engine', {}).get('files') and p1.get('seconds per stage')
          and p1.get('pairs tested', 0) >= 1, f'the receipt: expected, read, held, pairs, rules hash, store date, engine, seconds per stage ({ {k: p1.get(k) for k in ("parks expected", "parks read", "pairs tested")} })')
    r0 = subprocess.run([sys.executable, str(SCR / 'kpc_fers_receipt.py'), 'check', '--dir', str(tc / 'data/fers'), '--tag', 'testri', '--passes', '1,2,3,5', '--rules', p1.get('rules_hash') or 'x'], capture_output=True, text=True)
    r1 = subprocess.run([sys.executable, str(SCR / 'kpc_fers_receipt.py'), 'check', '--dir', str(tc / 'data/fers'), '--tag', 'nosuch', '--passes', '1'], capture_output=True, text=True)
    r2 = subprocess.run([sys.executable, str(SCR / 'kpc_fers_receipt.py'), 'check', '--dir', str(tc / 'data/fers'), '--passes', '1,2,3,5'], capture_output=True, text=True,
                        env={**os.environ, 'RUN_TAG': 'testri'})
    check(r0.returncode == 0 and r1.returncode == 2 and 'no receipt' in r1.stdout and r2.returncode == 0,
          f'check: done from the receipt (0), no receipt = red (2), the tag from the environment ({r0.returncode}, {r1.returncode}, {r2.returncode})')
    blob = json.dumps(rc_)
    check(not any(n in blob for n, *_ in PINS.values()) and 'US-990' not in blob and 'store-copy' not in blob, 'the receipt holds counts only: no park name, no ref, no store path')
    # ------------------------------------------------------------ 1 an area the store does not hold: store missing, red
    tm = TMP / 'missing'; tm.mkdir(); layout(tm, extra_area='US-ZQ')
    rc, out = go(tm, store_env(tm, PASS='1', STATES='US-RI US-ZQ'))
    a = ((receipt(tm) or {}).get('passes') or {}).get('1', {}).get('areas', {})
    check(rc == 0 and a.get('US-RI') == 'measured' and a.get('US-ZQ', '').startswith('store missing'), f"an area the store does not hold is 'store missing' (red), the others measured ({a})")

print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
