"""KPC park links for states around Kentucky (Brandon Oct 16: 'roll with surrounding states info').
For every POTA park in each state: official website (POTA's park list), park type and how you can activate there
(POTA park page), plus the state's main state-park website (the most common web address among its state parks).
Writes data/parkinfo/US-XX.json  {state, updated, stateSite, parks:{ref:[name, website, type, activation, access, lat, lon, activations, attempts, qsos]}}.
Automatic, NOT checked by KPC (Kentucky stays hand-checked in kpc-ky-data.json / kpc-campgrounds.json).
Park details are fetched once and reused; RECHECK=1 fetches them all again. STATES='TN IN ...' picks states."""
import json, os, re, time, urllib.request, urllib.parse, datetime, collections
STATES = (os.environ.get('STATES') or 'TN IN OH WV VA MO IL AL GA NC MS AR MD DC PA MI WI IA NE KS OK AK AZ CA CO CT DE FL HI ID LA ME MA MN MT NV NH NJ NM NY ND OR RI SD TX UT VT WA WY').split()
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
def fixurl(u):
    """POTA's list has some websites without https:// (e.g. 'parksandrecreation.idaho.gov'), which broke links"""
    u = clean(u)
    if u and not re.match(r'^https?://', u, re.I) and re.match(r'^[\w.-]+\.[a-z]{2,}(/|$)', u, re.I): u = 'https://' + u
    return u if re.match(r'^https?://', u, re.I) else ''
total = 0
COORD = {}
for st in STATES:
    path = f'{OUT}/US-{st}.json'
    try: old = json.load(open(path)).get('parks', {})
    except Exception: old = {}
    try: L = get(f'https://api.pota.app/location/parks/US-{st}')
    except Exception as e: note(f'US-{st} FAILED', e); continue
    parks, fetched = {}, 0
    if L and st == STATES[0]: note('POTA park list fields', ', '.join(sorted(L[0].keys())))
    for p in L:
        ref = p.get('reference', '')
        if not ref.startswith('US-'): continue
        web = fixurl(p.get('website'))
        o = old.get(ref)
        if o and not os.environ.get('RECHECK'): typ, act, acc = o[2], o[3], o[4]
        else:
            try:
                d = get('https://api.pota.app/park/' + urllib.parse.quote(ref)); fetched += 1
                typ, act, acc = clean(d.get('parktypeDesc')), clean(d.get('activationMethods')), clean(d.get('accessMethods'))
                web = web or fixurl(d.get('website'))
            except Exception: typ, act, acc = (o[2], o[3], o[4]) if o else ('', '', '')
            time.sleep(.25)
        try: la, lo = round(float(p.get('latitude')), 5), round(float(p.get('longitude')), 5)
        except Exception: la, lo = (o[5], o[6]) if o and len(o) > 6 else (None, None)
        n_act = p.get('activations'); n_try = p.get('attempts'); n_q = p.get('qsos')
        parks[ref] = [clean(p.get('name')), web, typ, act, acc, la, lo,
                      int(n_act) if str(n_act).isdigit() else None, int(n_try) if str(n_try).isdigit() else None, int(n_q) if str(n_q).isdigit() else None]
    doms = collections.Counter(d for d in (urllib.parse.urlparse(v[1]).netloc.lower().replace('www.', '') for v in parks.values() if v[1] and v[2] == 'State Park') if '.' in d)
    site = ''
    if doms:
        dom, n = doms.most_common(1)[0]
        if n >= 3: site = 'https://' + dom
    data = {'state': st, 'updated': datetime.date.today().isoformat(), 'stateSite': site, 'parks': parks}
    json.dump(data, open(path, 'w'), separators=(',', ':'), ensure_ascii=False)
    withweb = sum(1 for v in parks.values() if v[1])
    note(f'US-{st}', f'{len(parks)} parks, {withweb} with a website, {fetched} details fetched, state park site {site or "(none found)"}')
    total += len(parks)
# Canada + the rest of North America (Brandon Oct 17: 'Canadian cards'): one file per POTA program, data/parkinfo/<PREFIX>.json
# {program, updated, sites:{province:site}, parks:{ref:[same 10 fields, province/state code]}}. Weekly runs do every program;
# a manual run with only 'states' filled skips them; PROGS='CA MX' picks programs.
OKSITE = re.compile(r'(park|parc|parque|\.gov(\.|$)|\.gob\.|\.go\.[a-z]{2}$|\.gc\.ca$|gouv\.qc\.ca$|gov\.[a-z]{2}\.ca$|^gov\.mb\.ca$|sepaq\.com$|^bnt\.bs$|^bvinpt\.org$)')
NA_PROGS = 'CA MX GT BZ SV HN NI CR PA CU JM HT DO BS BB TT AG DM GD KN LC VC AI AW CW SX BQ MF BL GP MQ KY TC VG MS BM GL PM'.split()
PROGS = (os.environ.get('PROGS') or ('' if os.environ.get('STATES') else ' '.join(NA_PROGS))).split()
if PROGS:
    try: LOCS = get('https://api.pota.app/locations')
    except Exception as e: LOCS = []; note('POTA locations FAILED', e)
for pre in PROGS:
    descs = sorted({l['locationDesc'] for l in LOCS if str(l.get('locationDesc', '')).split('-')[0] == pre})
    if not descs: continue
    path = f'{OUT}/{pre}.json'
    try: old = json.load(open(path)).get('parks', {})
    except Exception: old = {}
    parks, fetched, failed, sites = {}, 0, 0, {}
    for desc in descs:
        try: L = get(f'https://api.pota.app/location/parks/{desc}')
        except Exception as e:
            failed += 1; note(f'{desc} FAILED', e)
            parks.update({r: v for r, v in old.items() if len(v) > 10 and v[10] == desc.split('-', 1)[-1]}); continue
        sub = desc.split('-', 1)[-1]
        for p in L:
            ref = p.get('reference', '')
            if not ref or ref in parks: continue
            web = fixurl(p.get('website')); o = old.get(ref)
            if o and not os.environ.get('RECHECK'): typ, act, acc = o[2], o[3], o[4]
            else:
                try:
                    d = get('https://api.pota.app/park/' + urllib.parse.quote(ref)); fetched += 1
                    typ, act, acc = clean(d.get('parktypeDesc')), clean(d.get('activationMethods')), clean(d.get('accessMethods'))
                    web = web or fixurl(d.get('website'))
                except Exception: typ, act, acc = (o[2], o[3], o[4]) if o else ('', '', '')
                time.sleep(.25)
            try: la, lo = round(float(p.get('latitude')), 5), round(float(p.get('longitude')), 5)
            except Exception: la, lo = (o[5], o[6]) if o and len(o) > 6 else (None, None)
            n_act = p.get('activations'); n_try = p.get('attempts'); n_q = p.get('qsos')
            parks[ref] = [clean(p.get('name')), web, typ, act, acc, la, lo,
                          int(n_act) if str(n_act).isdigit() else None, int(n_try) if str(n_try).isdigit() else None, int(n_q) if str(n_q).isdigit() else None, sub]
        doms = collections.Counter(d for d in (urllib.parse.urlparse(v[1]).netloc.lower().replace('www.', '') for v in parks.values() if v[1] and v[10] == sub and re.search(r'Provincial Park|State Park|National Park', v[2] or '')) if '.' in d)
        doms = collections.Counter({d: n for d, n in doms.items() if OKSITE.search(d)})   # only real park / government sites (not Wikipedia, APRS maps, tourism pages)
        if doms:
            dom, n = doms.most_common(1)[0]
            if n >= 3: sites[sub] = 'https://' + dom
    json.dump({'program': pre, 'updated': datetime.date.today().isoformat(), 'sites': sites, 'parks': parks}, open(path, 'w'), separators=(',', ':'), ensure_ascii=False)
    note(f'{pre} parks', f'{len(parks)} parks in {len(descs)} areas, {sum(1 for v in parks.values() if v[1])} with a website, {fetched} details fetched{f", {failed} areas failed" if failed else ""}; park sites {sites}')
# small index for the site search box (kpc-search.js), built from EVERY state file on disk.
# Compact (Oct 16, ~13k parks): {v:2, types:[...], rows:[[ref, name, state, lat, lon, typeIndex, activations]]}; coords fall back to locations.json.
LOC = {}
try:
    for r in json.load(open('locations.json')):
        if r[0] == 'POTA': LOC[r[1]] = (r[3], r[4])
except Exception: pass
types, ti, rows = [], {}, []
for f in sorted(os.listdir(OUT)):
    if not (f.startswith('US-') and f.endswith('.json')): continue
    try: d = json.load(open(f'{OUT}/{f}'))
    except Exception: continue
    for ref, v in d['parks'].items():
        la, lo = (v[5], v[6]) if len(v) > 6 and v[5] is not None else LOC.get(ref, (None, None))
        t = v[2] or ''
        if t not in ti: ti[t] = len(types); types.append(t)
        rows.append([ref, v[0], d['state'], round(la, 3) if la is not None else None, round(lo, 3) if lo is not None else None, ti[t], v[7] if len(v) > 7 else None])
rows.sort(key=lambda r: (r[2], r[1]))
json.dump({'v': 2, 'types': types, 'rows': rows}, open(f'{OUT}/index.json', 'w'), separators=(',', ':'), ensure_ascii=False)
note('Park links done', f'{total} parks in {len(STATES)} states')
