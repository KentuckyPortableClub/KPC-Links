#!/usr/bin/env python3
"""KPC owner, 2026-11-13: gis.blm.gov and apps.fs.usda.gov are not robots-blocked.

robots.txt answers seen on 2026-11-13: gis.blm.gov 404 (no file), apps.fs.usda.gov 403 (no rules file served). A 4xx robots answer
states no rule (RFC 9309, 2.3.1.3), so neither host is a never-contact or saved-copy-only host. apps.fs.usda.gov is a SLOW host:
at least 10 s between requests, one at a time, Retry-After honoured, refused for the rest of the run after a 403 / 429 burst.
Unchanged: every services*.arcgis.com host, ncnhde.natureserve.org, the Grant County NM org (33TOOklri9xpic7U), and the one BLM
Nevada service that needs a sign-in (KPC-Data registry blocked.csv).

Offline: proxy variables are dropped, every socket is refused, and the slow-host requests go to a stub opener, never the network.
"""
import email.utils, io, json, os, pathlib, socket, subprocess, sys, time, urllib.error, urllib.request

for _k in ('HTTPS_PROXY', 'HTTP_PROXY', 'https_proxy', 'http_proxy', 'ALL_PROXY', 'all_proxy', 'KPC_SAVED_ONLY_HOSTS'):
    os.environ.pop(_k, None)
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
ok = True


def check(cond, msg):
    global ok
    ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + msg)


SOCKS = []
def _no_socket(*a, **k):
    SOCKS.append(a); raise OSError('this test makes no network calls')
socket.create_connection = _no_socket
socket.socket.connect = lambda self, *a, **k: _no_socket(*a)

import kpc_net_guard as NG  # noqa: E402
import kpc_master as M  # noqa: E402
import kpc_host_pace as HP  # noqa: E402
import kpc_problem_solver as PS  # noqa: E402
import kpc_key_freeze as KF  # noqa: E402

BLM = ['https://gis.blm.gov/arcgis/rest/services/range/BLM_Natl_WHB/MapServer/0/query',
       'https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_WLD_WSA/MapServer', 'https://gis.blm.gov/robots.txt',
       'https://gis.blm.gov/idarcgis/rest/services/recreation/BLM_ID_Recreation_Area_Poly/MapServer/0']
FS = ['https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_Wilderness_02/MapServer/0/query',
      'https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_WildScenicRiver_01/MapServer/0', 'https://APPS.fs.usda.gov:443/robots.txt']
STILL = ['https://services.arcgis.com/x/arcgis/rest/services/y/FeatureServer/0', 'https://services1.arcgis.com/x/FeatureServer/0',
         'https://services2.arcgis.com/x', 'https://services5.arcgis.com/robots.txt', 'https://services9.arcgis.com/x',
         'https://services-eu1.arcgis.com/x', 'https://ncnhde.natureserve.org/system/files/marea.zip', 'http://ncnhde.natureserve.org/robots.txt',
         'https://services.arcgis.com/33TOOklri9xpic7U/arcgis/rest/services/Parcels/FeatureServer/0']

# ---- 1. gis.blm.gov is allowed on every bot path
for u in BLM:
    check(NG.host_ok(u)[0] and M.live_ok(u)[0] and PS.host_allowed(u)[0] and M.who_for(u)[0] == 'bot', f'gis.blm.gov allowed: {u[8:70]}')
check(NG.min_gap('gis.blm.gov') == 0.0 and M.host_delay('gis.blm.gov') == M.HOST_DELAY, 'gis.blm.gov keeps the ordinary 2 s gap')

# ---- 2. the Nevada sign-in-only service stays blocked as sign-in only (KPC-Data registry blocked.csv)
NV = 'https://gis.blm.gov/nvarcgis/rest/services/BLM_Nevada_SNPLMA_Disposal_Boundary?f=json'
data = pathlib.Path(os.environ.get('DATA') or ROOT.parent / 'KPC-Data')
bc = data / '.github/scripts/draft/tools/kpc_engine/registry/blocked.csv'
if bc.exists():
    import csv
    rows = [r for r in csv.DictReader(open(bc, encoding='utf-8')) if r.get('domain') == 'gis.blm.gov']
    check(len(rows) == 1 and rows[0]['url'] == NV and 'sign-in' in rows[0]['reason'] and 'robots' not in rows[0]['reason'].lower(),
          f'KPC-Data blocked.csv keeps ONE gis.blm.gov row: the Nevada SNPLMA service, sign-in only, not a robots block ({len(rows)} rows)')
else:
    print(f'NOTE KPC-Data checkout not found at {data} (set DATA=): the blocked.csv row is checked by the KPC-Data test')
doc = (ROOT / 'docs' / 'round3-left-out.md').read_text(encoding='utf-8')
check('BLM_Nevada_SNPLMA_Disposal_Boundary' in doc and 'stays blocked as sign-in only' in doc, 'the dated note keeps the Nevada service sign-in only')

# ---- 3. apps.fs.usda.gov is allowed, as a slow host
for u in FS:
    check(NG.host_ok(u)[0] and M.live_ok(u)[0] and PS.host_allowed(u)[0], f'apps.fs.usda.gov allowed: {u[8:70]}')
check('apps.fs.usda.gov' not in NG.NEVER and 'apps.fs.usda.gov' not in M.SAVED_ONLY_HOSTS and 'apps.fs.usda.gov' not in PS.NEVER_HOST,
      'apps.fs.usda.gov is off the never-contact and saved-copy-only defaults')
check(NG.min_gap('apps.fs.usda.gov') >= 10 and NG.min_gap('APPS.FS.USDA.GOV:443') >= 10 and M.host_delay('apps.fs.usda.gov') >= 10,
      'apps.fs.usda.gov: at least 10 s between requests (guard, master pacer)')
r = subprocess.run([sys.executable, '-B', '-c', "import sys; sys.path.insert(0, '.github/scripts'); import kpc_research_inbox as RI; "
                    "print('apps.fs.usda.gov' in RI.HOLD, 'services1.arcgis.com' in RI.HOLD)"], cwd=ROOT, capture_output=True, text=True, timeout=120,
                   env={k: v for k, v in os.environ.items() if k != 'KPC_SAVED_ONLY_HOSTS'})
check(r.stdout.split() == ['False', 'True'], f'research inbox: apps.fs.usda.gov is not held, services1 is ({r.stdout.strip() or r.stderr[-160:]})')

# the env list can still ADD the host back (owner-side variable)
r = subprocess.run([sys.executable, '-B', '-c', "import sys; sys.path.insert(0, '.github/scripts'); import kpc_master as M, kpc_net_guard as G; "
                    "print(M.live_ok('https://apps.fs.usda.gov/x')[0], G.host_ok('https://apps.fs.usda.gov/x')[0])"], cwd=ROOT, capture_output=True,
                   text=True, timeout=120, env=dict(os.environ, KPC_SAVED_ONLY_HOSTS='apps.fs.usda.gov'))
check(r.stdout.split() == ['False', 'False'], f'KPC_SAVED_ONLY_HOSTS=apps.fs.usda.gov still blocks it (the variable only adds) ({r.stdout.strip() or r.stderr[-160:]})')

# master Pacer with a fake clock: 10 s between two requests to the Forest Service host, 2 s to BLM
now = [100.0]; slept = []
def _sleep(s): slept.append(s); now[0] += s
P = M.Pacer(clock=lambda: now[0], sleep=_sleep)
P.wait('apps.fs.usda.gov'); now[0] += 1.0; P.wait('apps.fs.usda.gov')
check(slept and abs(slept[-1] - 9.0) < 1e-6, f'master Pacer waits 10 s between two Forest Service requests ({slept})')
slept.clear(); P.wait('gis.blm.gov'); now[0] += 1.0; P.wait('gis.blm.gov')
check(slept and abs(slept[-1] - 1.0) < 1e-6, f'master Pacer keeps 2 s for gis.blm.gov ({slept})')

# kpc_host_pace.wait: the per-host floor (real clock, sleep stubbed)
_real_sleep = time.sleep; HS = []
HP.time.sleep = lambda s: HS.append(s)
try:
    HP._last.pop('apps.fs.usda.gov', None); HP.wait('apps.fs.usda.gov'); HP.wait('apps.fs.usda.gov')
finally: HP.time.sleep = _real_sleep
check(HS and HS[-1] > 9.5, f'kpc_host_pace.wait: about 10 s before the second Forest Service request ({[round(x, 2) for x in HS]})')


# The guard itself, on every urllib request: stub opener, fake clock
class Resp(io.BytesIO):
    status = code = 200
    msg = 'OK'
    def info(self): return {}
    def geturl(self): return 'stub'


ANS = []          # what the stub answers next: 200 or (code, headers)
OPENED = []
class Stub(urllib.request.BaseHandler):
    handler_order = 100   # before the real HTTPS handler: nothing reaches the network
    def https_open(self, req):
        OPENED.append((now[0], req.full_url))
        a = ANS.pop(0) if ANS else 200
        if a == 200: return Resp(b'{}')
        code, hdr = a
        raise urllib.error.HTTPError(req.full_url, code, 'stub', hdr, io.BytesIO(b''))


NG.install()
NG.time.monotonic = lambda: now[0]
NG.time.sleep = _sleep
op = urllib.request.build_opener(Stub)
NG._SLOW.clear(); slept.clear(); OPENED.clear(); now[0] = 1000.0
for i in range(3):
    with op.open(FS[0] + f'?n={i}', timeout=5) as resp: resp.read()
gaps = [b[0] - a[0] for a, b in zip(OPENED, OPENED[1:])]
check(len(OPENED) == 3 and all(g >= 10 - 1e-6 for g in gaps), f'guard: 3 Forest Service requests, each at least 10 s apart ({gaps})')

# one at a time: a second request while the first answer is still open is refused, not sent alongside it
NG._SLOW.clear(); OPENED.clear()
first = op.open(FS[0] + '?open=1', timeout=5)
import threading
res = []
NG.SLOW_LOCK_WAIT = 0.2   # a short wait in this test (900 s in a run)
def _second():
    try: op.open(FS[0] + '?second=1', timeout=5); res.append('sent')
    except NG.NetGuardRefused: res.append('refused')
t = threading.Thread(target=_second); t.start(); t.join(10)
check(res == ['refused'] and len(OPENED) == 1, f'guard: one connection at a time (a second request while one is open: {res})')
first.close()
NG.SLOW_LOCK_WAIT = 900.0
with op.open(FS[0] + '?after=1', timeout=5) as resp: resp.read()
check(len(OPENED) == 2, 'guard: after the first answer is closed the next request goes out')

# Retry-After is waited out (seconds and HTTP date)
NG._SLOW.clear(); OPENED.clear(); slept.clear(); now[0] = 5000.0
ANS[:] = [(429, {'Retry-After': '45'})]
try: op.open(FS[0] + '?ra=1', timeout=5)
except urllib.error.HTTPError: pass
with op.open(FS[0] + '?ra=2', timeout=5) as resp: resp.read()
check(len(OPENED) == 2 and OPENED[1][0] - OPENED[0][0] >= 45 - 1e-6, f'guard: Retry-After 45 s honoured ({OPENED[1][0] - OPENED[0][0]:.0f} s)')
check(abs(NG._retry_after({'Retry-After': email.utils.formatdate(time.time() + 120, usegmt=True)}) - 120) < 5, 'guard: a Retry-After HTTP date is read')
NG._SLOW.clear(); ANS[:] = [(503, {'Retry-After': '3600'})]
try: op.open(FS[0] + '?long=1', timeout=5)
except urllib.error.HTTPError: pass
try: op.open(FS[0] + '?long=2', timeout=5); r2 = 'sent'
except NG.NetGuardRefused: r2 = 'refused'
check(r2 == 'refused', 'guard: a Retry-After over 10 minutes stops the host for the run')

# a 403 / 429 burst stops the host for the rest of the run
NG._SLOW.clear(); OPENED.clear(); ANS[:] = [(403, {}), (429, {}), (403, {})]
for i in range(3):
    try: op.open(FS[0] + f'?b={i}', timeout=5)
    except urllib.error.HTTPError: pass
try: op.open(FS[0] + '?b=4', timeout=5); r3 = 'sent'
except NG.NetGuardRefused: r3 = 'refused'
check(r3 == 'refused' and len(OPENED) == 3, f'guard: 3 answers of 403 / 429 in a row = no more requests to the host this run ({len(OPENED)} sent)')
NG._SLOW.clear(); OPENED.clear(); ANS[:] = [(403, {}), 200, (403, {}), 200, (429, {}), 200, (403, {}), 200, (403, {})]
for i in range(9):
    try:
        with op.open(FS[0] + f'?t={i}', timeout=5) as resp: resp.read()
    except urllib.error.HTTPError: pass
try: op.open(FS[0] + '?t=9', timeout=5); r4 = 'sent'
except NG.NetGuardRefused: r4 = 'refused'
check(r4 == 'refused' and len(OPENED) == 9, 'guard: 5 answers of 403 / 429 in one run stop the host too')
# BLM is not slowed by the guard
NG._SLOW.clear(); OPENED.clear(); now[0] = 9000.0; slept.clear()
for i in range(2):
    with op.open(BLM[0] + f'?n={i}', timeout=5) as resp: resp.read()
check(len(OPENED) == 2 and not slept and 'gis.blm.gov' not in NG._SLOW, 'guard: gis.blm.gov requests are not held by the slow-host rule')
ua = (ROOT / '.github/scripts/kpc_master.py').read_text(encoding='utf-8')
check("UA = 'KPC (kentuckyportableclub.github.io)'" in ua, 'the honest club User-Agent is unchanged')

# ---- 4. still blocked: every services*.arcgis.com host, ncnhde.natureserve.org, the Grant County org
for u in STILL:
    check(not NG.host_ok(u)[0] and not M.live_ok(u)[0] and not PS.host_allowed(u)[0], f'still blocked: {u[8:75]}')
check(M.who_for(STILL[-1])[0] == 'never' and M.who_for(STILL[6])[0] == 'never', 'Grant County and ncnhde stay never-contact')
check(('services.arcgis.com', '/33TOOklri9xpic7U') in M.NEVER_CONTACT and ('ncnhde.natureserve.org', '') in M.NEVER_CONTACT and 'ncnhde.natureserve.org' in NG.NEVER,
      'the never-contact lists still hold Grant County and ncnhde')
for u in ('https://services1.arcgis.com/robots.txt', 'https://ncnhde.natureserve.org/robots.txt'):
    try: op.open(u, timeout=5); r5 = 'sent'
    except NG.NetGuardRefused: r5 = 'refused'
    check(r5 == 'refused', f'guard refuses {u} before any request')

# ---- no rules hash moves: no rule file differs from origin/main
base = 'origin/main' if subprocess.run(['git', 'rev-parse', '-q', '--verify', 'origin/main'], cwd=ROOT, capture_output=True).returncode == 0 else 'HEAD'
moved = subprocess.run(['git', 'diff', '--name-only', base, '--', *sorted({f for v in KF.RULE_FILES.values() for f in v})], cwd=ROOT,
                       capture_output=True, text=True).stdout.split()
check(not moved, f'no rule file changed by this PR, so no US / CA / world / 2-fer rules hash moves ({moved})')
check(not SOCKS, f'no socket was opened ({len(SOCKS)})')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
