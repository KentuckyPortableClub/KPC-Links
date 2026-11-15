#!/usr/bin/env python3
"""Nov 14: the Europe weather warnings job waits at least 2 s between requests to feeds.meteoalarm.org (kpc_host_pace).

1. Every feed is still read once, in the same order, from the same addresses.
2. On a virtual clock: the first request does not wait, every next one waits 2 s; the added time stays far under the
   10 minute job timeout.
3. The output is the same shape as before (one country per feed, items kept), and a failed feed is still kept as stale.

Offline: urlopen is a fake, time.sleep / time.monotonic are a virtual clock; temp dir only.
"""
import io, json, os, pathlib, sys, tempfile, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
ok = True


def check(cond, msg):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


clock = {'t': 1000.0, 'slept': []}
time.monotonic = lambda: clock['t']
def fake_sleep(s):
    clock['slept'].append(s); clock['t'] += s
time.sleep = fake_sleep

FEED = (b'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:cap="urn:oasis:names:tc:emergency:cap:1.2"><entry>'
        b'<title>Yellow wind warning</title><cap:event>Wind</cap:event><cap:severity>Moderate</cap:severity>'
        b'<cap:areaDesc>Somewhere</cap:areaDesc><cap:expires>2099-01-01T00:00:00+00:00</cap:expires></entry></feed>')
calls = []
def fake_urlopen(req, *a, **k):
    calls.append((req.full_url, clock['t']))
    clock['t'] += 0.1                      # each answer takes 0.1 s
    if req.full_url.endswith('-austria'):
        raise OSError('down')
    return io.BytesIO(FEED)
urllib.request.urlopen = fake_urlopen      # set before import: the pacer wraps it

tmp = pathlib.Path(tempfile.mkdtemp()); os.chdir(tmp)
pathlib.Path('data/alerts').mkdir(parents=True)
pathlib.Path('data/alerts/eu.json').write_text(json.dumps({'countries': {'AT': {'name': 'Austria', 'link': 'x', 'items': []}}}))
import kpc_eu_alerts as eu  # noqa: E402

check(urllib.request.urlopen is not fake_urlopen and getattr(urllib.request.urlopen, '__wrapped__', None) is fake_urlopen,
      'importing the job installs the per-host pacer around urlopen')
eu.main()
want = [eu.FEED + slug for slug in eu.C.values()]
check([u for u, _ in calls] == want, f'all {len(want)} feeds read once, same order, same addresses')
gaps = [b - a for (_, a), (_, b) in zip(calls, calls[1:])]
check(all(g >= 2.0 - 1e-9 for g in gaps), 'at least 2 s between any two requests to feeds.meteoalarm.org')
added = sum(clock['slept'])
check(len(clock['slept']) == len(want) - 1 and added < 120, f'only the first request skips the wait; added {added:.0f} s, far under 600 s')
d = json.loads(pathlib.Path('data/alerts/eu.json').read_text())
c = d['countries']
check(len(c) == len(want) and c['AT'].get('stale') is True and c['AT'].get('failed_runs') == 1, 'failed feed still kept and marked stale')
check(c['DE']['items'] == [{'area': 'Somewhere', 'event': 'Wind', 'level': 'yellow', 'sev': 'Moderate', 'onset': '',
                            'expires': '2099-01-01T00:00:00+00:00'}], 'warnings read as before')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
