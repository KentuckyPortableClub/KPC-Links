#!/usr/bin/env python3
"""Offline test, Nov 11 2026 (host rules, review package A): blocked hosts are refused BEFORE any request (robots.txt included) and a
blocked source is VISIBLE, never quiet fresh data.
  * owned land (kpc-owned.yml -> kpc_owned_run.py; kpc_owned.py itself, a 2-fer rule file, is untouched and the fers rules hash does
    not move): the Forest Service map (apps.fs.usda.gov) and the Park Service tracts (services1.arcgis.com) get no request of any kind;
    the kept file is byte-for-byte the same; data/status/kpc_owned.json says blocked, STALE since, and carries a needs-download row;
  * US closures: the five services*.arcgis.com feeds are never asked; their last items are kept marked STALE since the last good read;
  * the state GIS scan: a blocked layer is BLOCKED (never 'did not answer'), robots.txt is asked first, hub portals wait 60 s;
  * the discovery bot's fetches go through the host rules, robots.txt and the pacing; its browser refuses blocked hosts too.
Below the guard every HTTP(S) open is stubbed and counted (urllib's do_open) and every socket is refused: both counts must stay 0
for the blocked hosts. Run: python3 -B tests/test_hostguard_pkg_a_nov11.py"""
import contextlib, gzip, io, json, os, pathlib, shutil, socket, subprocess, sys, tempfile, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
S = ROOT / '.github' / 'scripts'
sys.path.insert(0, str(S))
ok = True
OPENS, SOCKS = [], []


def check(a, b):
    """check(condition, message) or check(message, condition)."""
    global ok
    cond, msg = (b, a) if isinstance(a, str) and not isinstance(b, str) else (a, b)
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


def _sock(*a, **k):
    SOCKS.append(a[:1]); raise OSError('no network in this test')


socket.getaddrinfo = socket.create_connection = _sock
socket.socket.connect = lambda self, *a: _sock(*a)


def _do_open(self, http_class, req, **kw):   # below kpc_net_guard's opener check, above http.client: counts what got past the guard
    OPENS.append(req.full_url); raise urllib.error.URLError('stubbed: no network in this test')


urllib.request.AbstractHTTPHandler.do_open = _do_open


def opened(word): return [u for u in OPENS if word in u]


def run(fn, *a):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): r = fn(*a)
    return r, buf.getvalue()


tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-pkg-a-links-'))
os.environ.pop('GITHUB_STEP_SUMMARY', None); os.environ.pop('HTTP_CACHE', None); os.environ.pop('HTTP_OFFLINE', None)
time_sleep = time.sleep; time.sleep = lambda s: None   # no real waits in this test

# ---------------------------------------------------------------- owned land
import kpc_key_freeze as KF  # noqa: E402
fers_before = KF.rules_hash('fers')
import kpc_owned_run as OR  # noqa: E402
import kpc_owned as KO, kpc_net_guard as NG, kpc_http_cache as HC  # noqa: E402,E401
check('owned: importing the runner installs the guard before kpc_owned', NG.installed())
check('owned: the job reads the Forest Service map on apps.fs.usda.gov (a never-contact host)', NG.host_of(OR.JOBS['ky'][2][0][1]) == 'apps.fs.usda.gov')
w = tmp / 'owned'; w.mkdir()
shutil.copy(ROOT / 'ky-dbnf.geojson', w / 'ky-dbnf.geojson')
kept = json.dumps({'type': 'FeatureCollection', 'read': '2026-10-27', 'features': [{'type': 'Feature', 'properties': {'NAME': 'x'}, 'geometry': None}]})
(w / 'ky-dbnf-owned.geojson').write_text(kept)
os.environ['KPC_OWNED_STATUS'] = str(w / 'data' / 'status' / 'kpc_owned.json'); OR.STATUS = pathlib.Path(os.environ['KPC_OWNED_STATUS'])
cwd = os.getcwd(); os.chdir(w)
try:
    rc, out = run(OR.run, 'ky')
finally: os.chdir(cwd)
st = json.load(open(OR.STATUS)) if OR.STATUS.exists() else {}
row = (st.get('jobs') or {}).get('ky') or {}
check(rc == 0 and not OPENS and not SOCKS, f'owned, no saved copy: exit 0 and zero requests of any kind (opens {OPENS[:2]}, sockets {len(SOCKS)})')
check((w / 'ky-dbnf-owned.geojson').read_text() == kept, 'owned: the kept file is byte-for-byte unchanged')
check('::warning' in out and 'BLOCKED' in out and 'STALE since 2026-10-27' in out, 'owned: the log has a warning: BLOCKED, STALE since the kept file was read')
check(row.get('state') == 'blocked' and row.get('stale_since') == '2026-10-27' and row['blocked'][0]['url'] == KO.FSBO, f'owned: data/status/kpc_owned.json says blocked + stale since ({row.get("state")}, {row.get("stale_since")})')
nd = (row.get('needs') or [{}])[0]
check(nd.get('who') == 'person' and nd.get('host') == 'apps.fs.usda.gov' and nd.get('status') == 'open' and set(nd) >= {'id', 'area', 'layer', 'url', 'why', 'source', 'added', 'check'},
      'owned: the note carries a needs-download row (the KPC-Data list schema) for a person')
again = OR.STATUS.read_text(); os.chdir(w)
try: run(OR.run, 'ky')
finally: os.chdir(cwd)
check(OR.STATUS.read_text() == again, 'owned: the same note again = the status file is not rewritten (no extra save)')
# a saved-copy bundle that does not hold the answer: still no request, still stale
(tmp / 'bundle' / 'ab').mkdir(parents=True); (tmp / 'bundle' / 'ab' / 'x.json.gz').write_bytes(gzip.compress(b'{}'))
HC.DIR = str(tmp / 'bundle'); KO.LOG.clear(); KO.FSO.update({'feat': {}, 'tile': {}, 'f': None}); os.chdir(w)
try: rc, out = run(OR.run, 'ky')
finally: os.chdir(cwd); HC.DIR = ''; HC.OFFLINE = False; os.environ.pop('HTTP_OFFLINE', None)
row = json.load(open(OR.STATUS))['jobs']['ky']
check(not OPENS and not SOCKS and row.get('state') == 'blocked' and 'not in the bundle' in (row.get('not_read') or ''),
      f'owned, bundle without the answer: read offline only, zero requests, still marked stale ({row.get("not_read")})')
check((w / 'ky-dbnf-owned.geojson').read_text() == kept, 'owned: the kept file is still unchanged')
# the Park Service tracts (services1.arcgis.com), its robots.txt, and the whole 'nps' read path
for u in (KO.NPSTR + '/query', 'https://services1.arcgis.com/robots.txt'):
    try: KO.get(u, {'f': 'json'}); r = 'answered'
    except NG.NetGuardRefused as e: r = 'refused'
    except Exception as e: r = type(e).__name__  # noqa: BLE001
    check(r == 'refused' and not opened('services1'), f'owned: {u.split("/")[2]}{"/robots.txt" if "robots" in u else " tracts"} refused by the guard before any request ({r})')
try: urllib.request.urlopen('https://services1.arcgis.com/robots.txt', timeout=2); r = 'answered'
except NG.NetGuardRefused: r = 'refused'
check(r == 'refused' and not opened('services1'), 'owned: a plain urlopen of services1 robots.txt is refused too')
padus = KO.PADUS; KO.PADUS = 'https://services9.arcgis.com/x/arcgis/rest/services/PADUS/MapServer/0/query'   # in-test: the fallback is refused too, so nothing goes out
KO.LOG.clear(); KO.OWN_T.clear()
try: res = KO.owned_land('nps', [-86.2, 37.1, -86.1, 37.2], 0.0001, 5)
finally: KO.PADUS = padus
check(res is None and not OPENS and not SOCKS and any('services1.arcgis.com' in x for x in KO.LOG), f'owned: the nps path (Park Service tracts first) is refused before any request ({KO.LOG[:1]})')
check(KF.rules_hash('fers') == fers_before, f'owned: the 2-fer rules hash is the same ({fers_before})')
base = 'origin/main' if subprocess.run(['git', 'rev-parse', '-q', '--verify', 'origin/main'], cwd=ROOT, capture_output=True).returncode == 0 else 'HEAD'
moved = subprocess.run(['git', 'diff', '--name-only', base, '--', *sorted({f for v in KF.RULE_FILES.values() for f in v})], cwd=ROOT, capture_output=True, text=True).stdout.split()
# Declared rule-file changes of the 2-fer batch on top of this package (Pacific area boxes #154, fers aa7561256260 -> 77b31e3427a4,
# awaiting the KPC owner's decision): only the 2-fer hash moves, by its own changelog line; US / CA / world stay put.
DECLARED = {'.github/scripts/kpc_fers.py', '.github/fers-rule-scope.json'}
moved = [f for f in moved if f not in DECLARED]
check(not moved, f'no rule file differs from {base} (so no rules hash moves), past the declared 2-fer batch: {moved}')
wf = (ROOT / '.github' / 'workflows' / 'kpc-owned.yml').read_text(encoding='utf-8')
check('kpc_owned_run.py ky' in wf and 'python3 .github/scripts/kpc_owned.py' not in wf and 'git add data/status/kpc_owned.json' in wf, 'owned: the workflow runs the guarded runner and saves its note')

# ---------------------------------------------------------------- US closures
os.environ['FORCE_RUN'] = '1'
import kpc_us_closures as UC  # noqa: E402
bl = {sid for sid, _st, _w in UC.blocked_states()}
check(bl == {'ca-parks', 'wi-dnr', 'fl-parks', 'mt-fwp', 'nj-parks'}, f'closures: exactly CA, WI, FL, MT, NJ are blocked ({sorted(bl)})')
c = tmp / 'closures'; (c / 'data' / 'alerts').mkdir(parents=True)
item = {'id': 'uc-ca-parks-x-US-0001', 'src': 'ca-parks', 'ref': 'US-0001', 'kind': 'Closure', 'details': 'California State Parks: Closed', 'seen': '2026-10-20', 'expires': '2099-01-01'}
(c / 'data' / 'alerts' / 'us-parks.json').write_text(json.dumps({'sources': {'ca-parks': {'ok': True, 'last_ok': '2026-10-20', 'n': 1}}, 'items': [item]}))
(c / 'kpc-conditions.json').write_text(json.dumps({'items': []}))
def _no_feed(*a, **k): raise RuntimeError('stubbed in this test: no feed is read')
UC.get = _no_feed   # the allowed feeds fail here without a request; the blocked ones must never reach get() at all
os.chdir(c)
try: _, out = run(UC.main)
finally: os.chdir(cwd)
d = json.load(open(c / 'data' / 'alerts' / 'us-parks.json'))
s = d['sources']['ca-parks']; ca = [it for it in d['items'] if it['src'] == 'ca-parks']
check(not opened('arcgis.com') and not SOCKS, f'closures: no request to any services*.arcgis.com feed ({opened("arcgis.com")[:2]})')
check(s.get('blocked') and s.get('ok') is False and s.get('stale_since') == '2026-10-20' and 'STALE since 2026-10-20' in s.get('why', ''), f'closures: CA source says blocked + STALE since its last good read ({s.get("why", "")[:60]})')
check(ca and ca[0].get('stale_since') == '2026-10-20' and '[STALE: not re-read since 2026-10-20' in ca[0]['details'], 'closures: the kept CA item says STALE in its own text (the cards show it)')
cond = json.load(open(c / 'kpc-conditions.json'))
check(any('STALE' in (x.get('details') or '') for x in cond.get('items', [])), 'closures: the STALE words reach kpc-conditions.json too')
check('::warning title=US closures::5 of 11 sources' in out and 'CA (ca-parks) STALE since 2026-10-20' in out, 'closures: the run ends with a warning naming each stale state')
os.environ.pop('FORCE_RUN', None)

# ---------------------------------------------------------------- state GIS scan
import kpc_state_gis as SG  # noqa: E402
n0 = len(OPENS)
try: SG.get('https://services1.arcgis.com/abc/arcgis/rest/services/Parks/FeatureServer/0?f=json'); r = 'asked'
except SG.Blocked: r = 'blocked'
check(r == 'blocked' and len(OPENS) == n0 and any('services1' in k for k in SG.BLOCKED), 'state GIS: a services1 layer is Blocked before any request (robots.txt included) and listed')
check(SG.jget('https://services5.arcgis.com/abc/arcgis/rest/services/X/MapServer/0?f=json') is None and not any('services5' in f for f in SG.FAILED),
      'state GIS: a blocked layer is not counted as "did not answer"')
check(SG.gap_for('www.arcgis.com') == 60 and SG.gap_for('ohiodnr.hub.arcgis.com') == 60 and SG.gap_for('gis-ohiodnr.opendata.arcgis.com') == 60
      and SG.gap_for('gis.sc.gov') == 60 and SG.gap_for('abc.maps.arcgis.com') == 60 and SG.gap_for('gis.ohiodnr.gov') == 2, 'state GIS: 60 s on ArcGIS Online / Hub portals, 2 s elsewhere')
import urllib.robotparser  # noqa: E402
rp = urllib.robotparser.RobotFileParser(); rp.parse(['User-agent: *', 'Disallow: /'])
SG._ROBOTS['https://gis.example.gov'] = rp
try: SG.get('https://gis.example.gov/arcgis/rest/services?f=json'); r = 'asked'
except SG.NotThisRun: r = 'not this run'
check(r == 'not this run' and len(OPENS) == n0, 'state GIS: a robots.txt Disallow stops the read before the request')
# a whole one-state run (Ohio: Kentucky is not in this scan) with robots.txt saying no everywhere: the old layers stay, the blocked one marked BLOCKED
g = tmp / 'sgis'; (g / 'data').mkdir(parents=True)
(g / 'data' / 'state-gis-found.json').write_text(json.dumps({'n': 2, 'layers': [
    {'st': 'OH', 'kind': 'park', 'url': 'https://services1.arcgis.com/abc/arcgis/rest/services/P/FeatureServer/0', 'layer': 'P', 'count': 9, 'nameFields': ['NAME']},
    {'st': 'OH', 'kind': 'wild', 'url': 'https://kygisserver.ky.gov/arcgis/rest/services/W/MapServer/1', 'layer': 'W', 'count': 9, 'nameFields': ['NAME']}]}))
SG.robots_ok = lambda u: False
sys.argv = ['kpc_state_gis.py', 'OH']; os.chdir(g)
try: _, out = run(SG.main)
finally: os.chdir(cwd)
f = json.load(open(g / 'data' / 'state-gis-found.json'))
L = {x['url'].split('/')[2]: x for x in f['layers']}
check(len(OPENS) == n0 and not SOCKS, 'state GIS run: zero requests when robots.txt says no and the hosts are blocked')
check(L.get('services1.arcgis.com', {}).get('blocked') and L.get('kygisserver.ky.gov', {}).get('stale') and not L['kygisserver.ky.gov'].get('blocked'),
      'state GIS run: the old blocked layer is kept marked BLOCKED, the other one kept marked stale (not dropped as not found)')
check('BLOCKED' in out and isinstance(f.get('blocked'), list), 'state GIS run: the log and the file name the blocked addresses')

# ---------------------------------------------------------------- discovery bot (kpc_leadtest's fetch) and stale text
import kpc_leadtest as LT  # noqa: E402
try: LT.get('https://services2.arcgis.com/abc/arcgis/rest/services/X/FeatureServer/0', {'f': 'json'}); r = 'asked'
except LT.NotAsked as e: r = 'blocked' if e.blocked else 'robots'
check(r == 'blocked' and len(OPENS) == n0, 'discovery: a services2 layer is refused before any request (robots.txt included), and said to be BLOCKED')
check(bool(LT.SLOW_RE.search('www.arcgis.com')) and not LT.SLOW_RE.search('gis.ky.gov'), 'discovery: ArcGIS Online / Hub searches wait 60 s')
dsrc = (S / 'kpc_discovery.py').read_text(encoding='utf-8')
check("pg.route('**/*'" in dsrc and 'urllib.request.urlopen(' not in dsrc, 'discovery: every fetch goes through polite_open; the browser refuses blocked hosts')
pe = (S / 'kpc_parking_explorer.py').read_text(encoding='utf-8')
check('isinstance(e, kpc_net_guard.NetGuardRefused)' in pe and 'BLOCKED: never-contact host' in pe, 'parking explorer: a refused server root is logged BLOCKED, not "not listed"')
rh = (S / 'kpc_research_helpers.py').read_text(encoding='utf-8')
check('ArcGIS REST exempt' not in rh, 'research helpers: no stale "ArcGIS REST exempt" text')
check(not OPENS and not SOCKS, f'the whole test: zero requests past the guard ({OPENS[:3]}) and zero sockets ({len(SOCKS)})')
time.sleep = time_sleep
os.chdir(tmp)   # kpc_save writes its 'when each file changed' note at exit, relative to the working folder: keep it out of the repo
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
