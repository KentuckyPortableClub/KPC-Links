"""Top activators in each US state, for the KPC Hunters Lounge (Brandon Oct 16: 'see who top 20 activators in that state is').
POTA has no state leaderboard we can read (location/* stats need a sign-in), so this adds it up from POTA's public
activation list for every park in the state (api.pota.app/park/activations/<ref>?count=all). An activation counts when it
has 10+ QSOs (POTA's rule). Calls like KZ4CP/P count as KZ4CP. A park is only re-read when its activation count changed
(cache .cache/leaders, kept between runs with actions/cache).
Writes data/leaders/US-XX.json {updated, st, parks, activated, acts:[[call, activations, parks, qsos]] (top 50 by
activations), uniq:[...] (top 50 by different parks)} and data/leaders/index.json {st: [updated, parks]}."""
import json, os, time, datetime, urllib.request, concurrent.futures as CF
ST = (os.environ.get('STATES') or 'AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY').split()
C, OUT = '.cache/leaders', 'data/leaders'; os.makedirs(C, exist_ok=True); os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'KPC state leaders (kentuckyportableclub.github.io)'}
YEAR = str(datetime.date.today().year)
T0 = time.time(); BUDGET = float(os.environ.get('BUDGET_MIN', '300')) * 60
def note(t, m): print(f'::notice title={t}::{m}', flush=True)
def get(u):
    err = None
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as f: return json.loads(f.read().decode('utf-8', 'replace'))
        except Exception as e: err = e; time.sleep(2 + 5 * i)
    raise err
def base(c): return max(str(c or '').upper().strip().split('/'), key=len)
def park(ref, n):
    f = f'{C}/{ref}.json'
    try:
        d = json.load(open(f))
        if d.get('n') == n and d.get('v') == 2: return d['a'], d['h'], False
    except Exception: pass
    a, h = {}, {}
    # hunters: POTA only shares each park's top 10 hunters (park/leaderboard caps at 10)
    try:
        for x in (get(f'https://api.pota.app/park/leaderboard/{ref}?count=10') or {}).get('hunter_qsos') or []:
            c = base(x.get('callsign'))
            if c: h[c] = h.get(c, 0) + int(x.get('count') or 0)
    except Exception: pass
    for x in get(f'https://api.pota.app/park/activations/{ref}?count=all') or []:
        q = int(x.get('totalQSOs') or 0)
        if q < 10: continue
        c = base(x.get('activeCallsign') or x.get('activatorCallsign') or x.get('callsign'))
        if not c: continue
        d = str(x.get('qso_date') or '')[:8]
        v = a.setdefault(c, [0, 0, d, d, {}]); v[0] += 1; v[1] += q
        if d and (not v[2] or d < v[2]): v[2] = d
        if d and d > v[3]: v[3] = d
        y = v[4].setdefault(d[:4] or '?', [0, 0]); y[0] += 1; y[1] += q
    json.dump({'v': 2, 'n': n, 'a': a, 'h': h}, open(f, 'w'), separators=(',', ':'))
    return a, h, True
try: IDX = json.load(open(f'{OUT}/index.json'))
except Exception: IDX = {}
done = []
for st in ST:
    if time.time() - T0 > BUDGET: note('Time', f'stopped before {st} (next run carries on)'); break
    try: L = get(f'https://api.pota.app/location/parks/US-{st}')
    except Exception as e: note(f'US-{st}', f'park list failed: {str(e)[:100]}'); continue
    P = [(p['reference'], int(p.get('activations') or 0)) for p in L if p.get('reference')]
    tot, hun, fetched, bad, calls = {}, {}, 0, 0, {}
    with CF.ThreadPoolExecutor(4) as ex:
        fut = {ex.submit(park, r, n): r for r, n in P if n > 0}
        for f in CF.as_completed(fut):
            try: a, h, new = f.result()
            except Exception: bad += 1; continue
            fetched += new
            for c in a: calls.setdefault(c, []).append(fut[f])
            for c, (k, q, d1, d2, yy) in a.items():
                v = tot.setdefault(c, [0, 0, 0, '', '', 0, 0, 0]); v[0] += k; v[1] += 1; v[2] += q
                if d1 and (not v[3] or d1 < v[3]): v[3] = d1
                if d2 and d2 > v[4]: v[4] = d2
                y = yy.get(YEAR)
                if y: v[5] += y[0]; v[6] += 1; v[7] += y[1]
            for c, q in h.items():
                v = hun.setdefault(c, [0, 0]); v[0] += q; v[1] += 1
    if bad > len(fut) * .2: note(f'US-{st}', f'{bad} parks failed: kept last week'); continue
    rows = [[c] + v for c, v in tot.items()]
    # row = [call, activations, parks, qsos, first date, last date, activations this year, parks this year, qsos this year]
    acts = sorted(rows, key=lambda r: (-r[1], -r[2], r[0]))[:50]
    uniq = sorted(rows, key=lambda r: (-r[2], -r[1], r[0]))[:50]
    qsos = sorted(rows, key=lambda r: (-r[3], -r[1], r[0]))[:50]
    yacts = sorted([r for r in rows if r[6]], key=lambda r: (-r[6], -r[7], r[0]))[:50]
    yuniq = sorted([r for r in rows if r[7]], key=lambda r: (-r[7], -r[6], r[0]))[:50]
    yqsos = sorted([r for r in rows if r[8]], key=lambda r: (-r[8], -r[6], r[0]))[:50]
    today = datetime.date.today().isoformat()
    hr = [[c] + v for c, v in hun.items()]
    hunt = sorted(hr, key=lambda r: (-r[1], -r[2], r[0]))[:50]
    huntp = sorted(hr, key=lambda r: (-r[2], -r[1], r[0]))[:50]
    json.dump({'v': 2, 'updated': today, 'year': YEAR, 'st': st, 'parks': len(P), 'activated': len(fut), 'activators': len(rows), 'yactivators': sum(1 for r in rows if r[6]),
               'acts': acts, 'uniq': uniq, 'qsos': qsos, 'yacts': yacts, 'yuniq': yuniq, 'yqsos': yqsos, 'hunt': hunt, 'huntp': huntp},
              open(f'{OUT}/US-{st}.json', 'w'), separators=(',', ':'))
    if st == 'KY':
        # Oct 22 (Brandon: 'teach it to look up peoples calls'): which Kentucky parks each call has activated (10+ QSOs),
        # so the Discord helper can answer 'how many parks does K4XYZ still need'. POTA's own public activation lists.
        json.dump({'updated': today, 'parks': [r for r, n in P], 'calls': {c: sorted(set(v)) for c, v in sorted(calls.items())}},
                  open(f'{OUT}/KY-calls.json', 'w'), separators=(',', ':'))
    IDX[st] = [today, len(P)]; done.append(st)
    note(f'US-{st}', f'{len(P)} parks, {len(rows)} activators; {fetched} parks re-read; top: {acts[0][0] if acts else "-"}')
json.dump(IDX, open(f'{OUT}/index.json', 'w'), separators=(',', ':'), sort_keys=True)
note('State leaders done', f'{len(done)} states in {round((time.time()-T0)/60)} min')
