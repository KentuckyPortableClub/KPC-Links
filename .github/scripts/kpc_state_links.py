"""KPC park links for states around Kentucky (Brandon Oct 16: 'roll with surrounding states info').
For every POTA park in each state: official website (POTA's park list), park type and how you can activate there
(POTA park page), plus the state's main state-park website (the most common web address among its state parks).
Writes data/parkinfo/US-XX.json  {state, updated, stateSite, parks:{ref:[name, website, type, activation, access]}}.
Automatic, NOT checked by KPC (Kentucky stays hand-checked in kpc-ky-data.json / kpc-campgrounds.json).
Park details are fetched once and reused; RECHECK=1 fetches them all again. STATES='TN IN ...' picks states."""
import json, os, time, urllib.request, urllib.parse, datetime, collections
STATES = (os.environ.get('STATES') or 'TN IN OH WV VA MO IL').split()
UA = {'User-Agent': 'KPC park links (kentuckyportableclub.github.io)'}
OUT = 'data/parkinfo'; os.makedirs(OUT, exist_ok=True)
def get(u):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40) as f: return json.loads(f.read().decode('utf-8', 'replace'))
        except Exception as e: err = e; time.sleep(2 + i * 3)
    raise err
def note(t, m): print(f'::notice title={t}::{m}')
clean = lambda v: '' if v in (None, 'None', 'null') else str(v).strip()
total = 0
for st in STATES:
    path = f'{OUT}/US-{st}.json'
    try: old = json.load(open(path)).get('parks', {})
    except Exception: old = {}
    try: L = get(f'https://api.pota.app/location/parks/US-{st}')
    except Exception as e: note(f'US-{st} FAILED', e); continue
    parks, fetched = {}, 0
    for p in L:
        ref = p.get('reference', '')
        if not ref.startswith('US-'): continue
        web = clean(p.get('website'))
        o = old.get(ref)
        if o and not os.environ.get('RECHECK'): typ, act, acc = o[2], o[3], o[4]
        else:
            try:
                d = get('https://api.pota.app/park/' + urllib.parse.quote(ref)); fetched += 1
                typ, act, acc = clean(d.get('parktypeDesc')), clean(d.get('activationMethods')), clean(d.get('accessMethods'))
                web = web or clean(d.get('website'))
            except Exception: typ, act, acc = (o[2], o[3], o[4]) if o else ('', '', '')
            time.sleep(.25)
        parks[ref] = [clean(p.get('name')), web, typ, act, acc]
    doms = collections.Counter(urllib.parse.urlparse(v[1]).netloc.lower().replace('www.', '') for v in parks.values() if v[1] and v[2] == 'State Park')
    site = ''
    if doms:
        dom, n = doms.most_common(1)[0]
        if n >= 3: site = 'https://' + dom
    data = {'state': st, 'updated': datetime.date.today().isoformat(), 'stateSite': site, 'parks': parks}
    json.dump(data, open(path, 'w'), separators=(',', ':'), ensure_ascii=False)
    withweb = sum(1 for v in parks.values() if v[1])
    note(f'US-{st}', f'{len(parks)} parks, {withweb} with a website, {fetched} details fetched, state park site {site or "(none found)"}')
    total += len(parks)
note('Park links done', f'{total} parks in {len(STATES)} states')
