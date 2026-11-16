#!/usr/bin/env python3
"""KPC owner, 2026-11-14 (Job 2 item 3): the research inbox gets the store engine's manners and no longer writes data/point-circles.json.
Offline: the network is a stub, the clock is a stub. Run from the KPC-Links root: python3 tests/test_inbox_manners_nov14.py"""
import csv, json, pathlib, socket, sys, tempfile, contextlib, io
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
socket.getaddrinfo = socket.create_connection = lambda *a, **k: (_ for _ in ()).throw(OSError('no network in test'))
import kpc_inbox_manners as MN  # noqa: E402
import kpc_research_inbox as RI  # noqa: E402
import kpc_key_freeze as KF  # noqa: E402
ok = True
def check(c, m):
    global ok; print(('ok   ' if c else 'FAIL ') + m); ok &= bool(c)

class Clock:
    def __init__(self, t=1_800_000_000.0): self.t = t; self.slept = []
    def __call__(self): return self.t
    def sleep(self, s): self.slept.append(s); self.t += s

class Net:
    """answers by url: robots -> (status, body, headers); everything else -> a JSON body"""
    def __init__(self, robots=(404, b'', {}), data=b'{"features": []}', clock=None, step=0.0):
        self.robots, self.data, self.calls, self.clock, self.step = robots, data, [], clock, step
    def __call__(self, url, accept, timeout, follow, cap=0, ua=''):
        self.calls.append((self.clock() if self.clock else 0, url))
        if self.clock and self.step: self.clock.t += self.step
        if url.endswith('/robots.txt') or '/robots' in url:
            r = self.robots(url) if callable(self.robots) else self.robots
            if isinstance(r, Exception): raise r
            st, body, h = r
            return MN.Answer(st, h, body, (h or {}).get('Location', ''))
        return MN.Answer(200, {}, self.data)

def man(tmp, net, clock): return MN.Manners(pathlib.Path(tmp) / MN.COUNTS_NAME, RI.UA, clock=clock, sleep=clock.sleep, opener=net)
U = 'https://gis.example.gov/arcgis/rest/services/p/MapServer/0'

# ---- 1. robots.txt answers
for st, want in ((200, True), (403, True), (404, True), (410, True), (401, True), (429, False), (500, False), (503, False)):
    c = Clock(); n = Net(robots=(st, b'User-agent: *\nDisallow: /private/\n' if st == 200 else b'', {}), clock=c); m = man(tempfile.mkdtemp(), n, c)
    got, why = m.robots_check(U)
    check(got == want, f'robots.txt {st}: {"reads allowed" if want else "no reads from this host this run"} ({why[:70] or "ok"})')
    if not want:
        m.robots_check(U); check(sum(1 for _, u in n.calls if u.endswith('robots.txt')) == 1, f'robots.txt {st}: asked once per host per run, no data read')
        try: m.get(U + '/query?f=json'); check(False, f'{st}: a data read was refused')
        except MN.Skip: check(len(n.calls) == 1, f'robots.txt {st}: the data read is refused with no request')
c = Clock(); n = Net(robots=OSError('unreachable'), clock=c); m = man(tempfile.mkdtemp(), n, c)
check(not m.robots_check(U)[0] and not m.robots_check(U)[0] and len(n.calls) == 1, 'robots.txt unreachable: no reads from that host this run, asked once')
c = Clock(); n = Net(robots=TimeoutError('timed out'), clock=c); m = man(tempfile.mkdtemp(), n, c)
check(not m.robots_check(U)[0], 'robots.txt timeout: no reads from that host this run')
c = Clock(); n = Net(robots=(200, b'User-agent: *\nDisallow: /arcgis/rest/services/p/\n', {}), clock=c); m = man(tempfile.mkdtemp(), n, c)
check(not m.robots_check(U)[0] and m.robots_check('https://gis.example.gov/arcgis/rest/services/q/MapServer/0')[0], 'robots.txt 200: Disallow obeyed, other paths allowed')
# Nov 15: a web page at robots.txt follows the store engine 3.6.2 rule (it was "could not be read" before)
for body, hdr, want, what in ((b'<html>not robots</html>', {}, True, 'an ordinary web page with no robots line = no rules'),
                              (b'<!DOCTYPE html><html><body><h1>Page not found</h1></body></html>', {}, True, 'a "not found" web page = no rules'),
                              (b'<html><body><form action="/login"><input type="password"></form></body></html>', {}, False, 'a sign-in page = no reads this run'),
                              (b'<html><body>Please sign in to continue</body></html>', {}, False, 'a page asking to sign in = no reads this run'),
                              (b'<html><body>Verify you are human</body></html>', {}, False, 'a bot-challenge page = no reads this run'),
                              (b'<html>hello</html>', {'WWW-Authenticate': 'Basic'}, False, 'a page with WWW-Authenticate = no reads this run'),
                              (b'<html><pre>User-agent: *\nDisallow: /arcgis/</pre></html>', {}, False, 'a page holding robots directives is parsed: its Disallow is obeyed')):
    c = Clock(); n = Net(robots=(200, body, hdr), clock=c); m = man(tempfile.mkdtemp(), n, c)
    check(m.robots_check(U)[0] == want, f'robots.txt 200 web page: {what} (engine 3.6.2 rule)')
c = Clock(); n = Net(robots=(200, b'<html><pre>User-agent: *\nDisallow: /private/</pre></html>', {}), clock=c); m = man(tempfile.mkdtemp(), n, c)
check(m.robots_check(U)[0] and not m.robots_check('https://gis.example.gov/private/x')[0], 'a page holding robots directives: other paths allowed')
check(MN.robots_verdict(200, b'<html>x</html>', 'KPC', {}, 'https://other.example.gov/robots.txt', 'https://gis.example.gov/robots.txt')[0] == 'unreadable',
      'a web page that came from another site is never "no rules"')
check(MN.robots_verdict(200, b'Disallow: /\n', 'KPC')[0] == 'unreadable', 'rules with no User-agent group: could not be read (engine 3.6.2)')
c = Clock(); n = Net(robots=(200, b'User-agent: *\nCrawl-delay: 45\n', {}), clock=c); m = man(tempfile.mkdtemp(), n, c)
ok45, why = m.robots_check(U); check(not ok45 and 'skipped this run' in why, 'Crawl-delay over 30 s: host skipped this run')
c = Clock(); n = Net(robots=(429, b'', {'Retry-After': '120'}), clock=c); d = tempfile.mkdtemp(); m = man(d, n, c); m.robots_check(U)
check(abs(MN.Manners(pathlib.Path(d) / MN.COUNTS_NAME, RI.UA, clock=c).not_before.get('gis.example.gov', 0) - (c.t + 120)) < 1, 'a 429 Retry-After is kept for the next run')
# redirects: same host https followed; http refused; another site refused; more than 5 refused
import re  # noqa: E402
def hops(url):
    k = int(re.search(r'/r(\d+)/robots\.txt$', url).group(1)) if re.search(r'/r\d+/robots\.txt$', url) else 0
    return (301, b'', {'Location': f'https://gis.example.gov/r{k + 1}/robots.txt'}) if k < 2 else (200, b'User-agent: *\nDisallow:\n', {})
c = Clock(); n = Net(robots=hops, clock=c); m = man(tempfile.mkdtemp(), n, c)
check(m.robots_check(U)[0] and len(n.calls) == 3, f'robots.txt redirect on the same host followed (2 hops, {len(n.calls)} requests, each counted)')
c = Clock(); n = Net(robots=lambda u: (301, b'', {'Location': 'http://gis.example.gov/robots.txt'}), clock=c); m = man(tempfile.mkdtemp(), n, c)
check(not m.robots_check(U)[0] and len(n.calls) == 1, 'robots.txt redirect to plain http refused (no reads this run)')
c = Clock(); n = Net(robots=lambda u: (302, b'', {'Location': 'https://elsewhere.example.org/robots.txt'}), clock=c); m = man(tempfile.mkdtemp(), n, c)
check(not m.robots_check(U)[0] and len(n.calls) == 1, 'robots.txt redirect to another site refused')
c = Clock(); n = Net(robots=lambda u: (301, b'', {'Location': u.replace('/robots.txt', '/x/robots.txt')}), clock=c); m = man(tempfile.mkdtemp(), n, c)
check(not m.robots_check(U)[0] and len(n.calls) == 6, f'more than 5 robots.txt redirects: not read ({len(n.calls)} requests)')
c = Clock(); n = Net(robots=lambda u: (301, b'', {'Location': 'https://services2.arcgis.com/robots.txt'}), clock=c); m = man(tempfile.mkdtemp(), n, c)
check(not m.robots_check(U)[0] and not any('arcgis.com' in u for _, u in n.calls), 'a redirect to a never-contact host is never followed')
c = Clock(); n = Net(clock=c); m = man(tempfile.mkdtemp(), n, c)
try: m.get('https://services3.arcgis.com/x/FeatureServer/0/query'); check(False, 'never-contact')
except MN.Skip: check(not n.calls, 'never-contact host: no request at all, robots.txt included')

# ---- 2. the 2 s gap on a stubbed clock
c = Clock(); n = Net(clock=c); m = man(tempfile.mkdtemp(), n, c)
for i in range(4): m.get(U + f'/query?i={i}')
ts = [t for t, _ in n.calls]
check(len(ts) == 5 and all(b - a >= 2.0 - 1e-9 for a, b in zip(ts, ts[1:])), f'at least 2 s between requests to one host (robots.txt + 4 reads; gaps {[round(b - a, 2) for a, b in zip(ts, ts[1:])]})')
c = Clock(); n = Net(robots=(200, b'User-agent: *\nCrawl-delay: 7\n', {}), clock=c); m = man(tempfile.mkdtemp(), n, c)
m.get(U + '/query?a'); m.get(U + '/query?b'); ts = [t for t, _ in n.calls]
check(all(b - a >= 7 - 1e-9 for a, b in zip(ts, ts[1:])), 'a Crawl-delay over the 2 s floor wins')
check(MN.SETTINGS['min_seconds_between_requests'] == 2.0 and MN.SETTINGS['per_host_per_hour'] == 200 and MN.SETTINGS['per_host_per_day'] == 1500,
      'the limits come from one constants block (2 s, 200 per hour, 1500 per day)')

class Busy(Net):
    def __call__(self, url, *a, **k):
        r = super().__call__(url, *a, **k)
        return r if url.endswith('robots.txt') else MN.Answer(429, {'Retry-After': '20'})
c = Clock(); n = Busy(clock=c); m = man(tempfile.mkdtemp(), n, c); sk = 0
for i in range(4):
    try: m.get(U + f'/query?{i}')
    except MN.Skip: sk += 1
ts = [t for t, _ in n.calls]
check(sk == 4 and len(n.calls) == 3 and ts[2] - ts[1] >= 20 - 1e-9, f'a data 429: Retry-After waited; after a second one no more reads from the host this run ({len(n.calls)} requests)')

# ---- 3. caps: 200th and 201st in an hour, 1500 a day, counters survive a reload
d = tempfile.mkdtemp(); c = Clock(); n = Net(clock=c); m = man(d, n, c)
for i in range(199): m.get(U + f'/query?i={i}')          # robots.txt + 199 reads = 200 requests
check(len(n.calls) == 200, 'the 200th request in the hour is made (robots.txt counted)')
try: m.get(U + '/query?x'); check(False, '201st')
except MN.Skip as e: check(len(n.calls) == 200 and 'cap reached for host gis.example.gov' in str(e), f'the 201st in the hour is refused, no request ({e})')
check(m.notes == ['cap reached for host gis.example.gov (200 requests per hour)'], 'one plain line in the run notes')
m2 = man(d, n, c)
check(len(m2.times['gis.example.gov']) == 200 and m2.cap_problem('gis.example.gov'), 'the counters survive a reload (next run still capped)')
c.t += 3601; m3 = man(d, n, c); m3.robots['gis.example.gov'] = None
m3.get(U + '/query?later'); check(len(n.calls) == 201, 'an hour later the host may be read again')
d = tempfile.mkdtemp(); c = Clock(); n = Net(clock=c); m = man(d, n, c); got = 0
for hour in range(10):
    m = man(d, n, c); m.robots['gis.example.gov'] = None
    for i in range(200):
        try: m.get(U + f'/query?h{hour}i{i}'); got += 1
        except MN.Skip: break
    c.t += 3600
check(got == 1500, f'1500 per day: {got} reads over 10 hours with a fresh run each hour')
m = man(d, n, c); check('per day' in m.cap_problem('gis.example.gov'), 'the daily cap holds into the next run')
c.t += 2 * 86400; m = man(d, n, c); check(not m.cap_problem('gis.example.gov') and not m.times, 'entries older than 24 hours are pruned')

# ---- 4. a whole inbox run: point-circles.json untouched, the proposal written, a sure row as before
root = pathlib.Path(tempfile.mkdtemp()); ib = root / 'data/research-inbox'; ib.mkdir(parents=True)
pc0 = {'about': 'x', 'parks': {'US-0001': {'kind': 'point-circle-100ft', 'radius_m': 30.48, 'pt': [-84.0, 37.0]}, 'US-0002': {'kind': 'point-circle-100ft', 'radius_m': 30.48, 'pt': [-85.0, 37.0]}}}
(root / 'data/point-circles.json').write_text(json.dumps(pc0, indent=1)); before = (root / 'data/point-circles.json').read_bytes()
LP, LS = 'https://gis.example.gov/arcgis/rest/services/pts/MapServer/0', 'https://gis.example.gov/arcgis/rest/services/poly/MapServer/0'
with open(ib / 'b.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=RI.COLS); w.writeheader()
    w.writerow({'pota_ref': 'US-0003', 'park_name': 'Fort Example State Historic Site', 'layer_url': LP, 'record_id': '5', 'pin_lat': '37.5', 'pin_lon': '-84.5'})
    w.writerow({'pota_ref': 'US-0002', 'park_name': 'Elk Creek State Park', 'layer_url': LS, 'record_id': '7', 'pin_lat': '37.0', 'pin_lon': '-85.0'})
pts = json.dumps({'geometryType': 'esriGeometryPoint', 'features': [{'attributes': {'OBJECTID': 5, 'NAME': 'Fort Example State Historic Site'}, 'geometry': {'x': -84.5005, 'y': 37.5}}]}).encode()
sq = [[[-85.01, 36.99], [-84.99, 36.99], [-84.99, 37.01], [-85.01, 37.01], [-85.01, 36.99]]]
poly = json.dumps({'geometryType': 'esriGeometryPolygon', 'features': [{'attributes': {'OBJECTID': 7, 'NAME': 'Elk Creek State Park'}, 'geometry': {'rings': sq}}]}).encode()
c = Clock(); calls = []
def fake(url, accept, timeout, follow, cap=0, ua=''):
    calls.append(url)
    if url.endswith('/robots.txt'): return MN.Answer(404)
    return MN.Answer(200, {}, pts if '/pts/' in url else poly)
orig = MN.manners_for
MN.manners_for = lambda cd, ua, **k: orig(cd, ua, opener=fake, clock=c, sleep=c.sleep, **k)
out = io.StringIO()
with contextlib.redirect_stdout(out): res = RI.run(RI.inbox_files(root), root=root, kpcdata=root / 'nokpcdata', cache=root / 'cache', offline=False, retry=False, ledger={})
rows = {r['pota_ref']: r for r in res['b']}
check((root / 'data/point-circles.json').read_bytes() == before, 'data/point-circles.json bytes unchanged after a run')
prop = json.loads((ib / 'results' / RI.PC_PROPOSAL).read_text())
check(rows['US-0003']['status'] == 'POINT-CONFIRMED' and prop['parks']['US-0003']['kind'] == 'point-circle-100ft' and prop['parks']['US-0003']['pt'] == [-84.5005, 37.5],
      'the proposal file has the new point circle (same entry as the old write)')
check(rows['US-0002']['status'] == 'SURE' and rows['US-0002']['record_id'] == '7', 'a sure row still behaves as before (SURE, record 7)')
check('US-0002' not in prop['parks'] and 'US-0001' in prop['parks'] and prop['about'] == 'x', 'the proposal = today\'s file + new circles - SURE parks\' circles')
check(sum(u.endswith('robots.txt') for u in calls) == 1 and len(calls) == 3, f'one robots.txt for the host, then the two reads ({len(calls)} requests)')
check((root / 'cache' / MN.COUNTS_NAME).is_file() and len(json.loads((root / 'cache' / MN.COUNTS_NAME).read_text())['hosts']['gis.example.gov']['t']) == 3,
      'the counts file sits next to the saved research outlines and counts the 3 requests')
check(RI.PC_PROPOSAL not in ' '.join(RI.inbox_files(root)), 'the proposal is never read as a research batch')
# a capped host: the park is kept on the retry list, one plain line
MN.manners_for = lambda cd, ua, **k: orig(cd, ua, opener=fake, clock=c, sleep=c.sleep, **k)
cf = root / 'cache' / MN.COUNTS_NAME; j = json.loads(cf.read_text()); j['hosts']['gis.example.gov']['t'] = [c.t - 10] * 200; cf.write_text(json.dumps(j))
for f in (root / 'cache').glob('gis_*'): f.unlink()   # no saved copy: a live read would be needed
calls.clear(); out = io.StringIO()
with contextlib.redirect_stdout(out): res = RI.run(RI.inbox_files(root), root=root, kpcdata=root / 'nokpcdata', cache=root / 'cache', offline=False, retry=False, ledger={})
nal = json.loads((ib / 'needs-another-look.json').read_text())
check(not calls and all(r['status'] == 'NEEDS PERSON' and r.get('retry') == 'next-run' for r in res['b']), 'past the cap: no request, the parks are not read this run')
check({'US-0002', 'US-0003'} <= set(nal['parks']) and nal['parks']['US-0003']['wait_on'] == 'next-run', 'they stay on the retry list for the next run')
check(out.getvalue().count('cap reached for host gis.example.gov') == 1, 'one plain line: cap reached for host gis.example.gov')
check((root / 'data/point-circles.json').read_bytes() == before, 'point-circles.json still untouched')
MN.manners_for = orig

# ---- 5. not a rule file; no rules hash moves
check('kpc_inbox_manners.py' in KF.NOT_RULES and not any('kpc_inbox_manners' in f for v in KF.RULE_FILES.values() for f in v), 'kpc_inbox_manners.py is listed in NOT_RULES')
src = (HERE / '.github/scripts/kpc_research_inbox.py').read_text(encoding='utf-8')
check("open(pc_f, 'w'" not in src, 'the inbox has no write to data/point-circles.json')
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
