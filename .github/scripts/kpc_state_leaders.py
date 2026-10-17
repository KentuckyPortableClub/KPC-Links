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
        if d.get('n') == n: return d['a'], False
    except Exception: pass
    a = {}
    for x in get(f'https://api.pota.app/park/activations/{ref}?count=all') or []:
        q = int(x.get('totalQSOs') or 0)
        if q < 10: continue
        c = base(x.get('activeCallsign') or x.get('activatorCallsign') or x.get('callsign'))
        if not c: continue
        v = a.setdefault(c, [0, 0]); v[0] += 1; v[1] += q
    json.dump({'n': n, 'a': a}, open(f, 'w'), separators=(',', ':'))
    return a, True
try: IDX = json.load(open(f'{OUT}/index.json'))
except Exception: IDX = {}
done = []
for st in ST:
    if time.time() - T0 > BUDGET: note('Time', f'stopped before {st} (next run carries on)'); break
    try: L = get(f'https://api.pota.app/location/parks/US-{st}')
    except Exception as e: note(f'US-{st}', f'park list failed: {str(e)[:100]}'); continue
    P = [(p['reference'], int(p.get('activations') or 0)) for p in L if p.get('reference')]
    tot, fetched, bad = {}, 0, 0
    with CF.ThreadPoolExecutor(4) as ex:
        fut = {ex.submit(park, r, n): r for r, n in P if n > 0}
        for f in CF.as_completed(fut):
            try: a, new = f.result()
            except Exception: bad += 1; continue
            fetched += new
            for c, (k, q) in a.items():
                v = tot.setdefault(c, [0, 0, 0]); v[0] += k; v[1] += 1; v[2] += q
    if bad > len(fut) * .2: note(f'US-{st}', f'{bad} parks failed: kept last week'); continue
    rows = [[c] + v for c, v in tot.items()]
    acts = sorted(rows, key=lambda r: (-r[1], -r[2], r[0]))[:50]
    uniq = sorted(rows, key=lambda r: (-r[2], -r[1], r[0]))[:50]
    today = datetime.date.today().isoformat()
    json.dump({'updated': today, 'st': st, 'parks': len(P), 'activated': len(fut), 'activators': len(rows), 'acts': acts, 'uniq': uniq},
              open(f'{OUT}/US-{st}.json', 'w'), separators=(',', ':'))
    IDX[st] = [today, len(P)]; done.append(st)
    note(f'US-{st}', f'{len(P)} parks, {len(rows)} activators; {fetched} parks re-read; top: {acts[0][0] if acts else "-"}')
json.dump(IDX, open(f'{OUT}/index.json', 'w'), separators=(',', ':'), sort_keys=True)
note('State leaders done', f'{len(done)} states in {round((time.time()-T0)/60)} min')
