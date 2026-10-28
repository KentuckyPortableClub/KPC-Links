"""Federal campgrounds (Recreation.gov RIDB), EVERY state incl. Kentucky + DC (Oct 26, HQ: 'all states, not just around KY') — US Trip Planner park cards.
Needs secret RIDB_API_KEY (free key from ridb.recreation.gov, Profile). Writes data/campfed/US-XX.json
{state, updated, camps:[[id, name, lat, lon, agency, reservable(0/1), url, kind c=campground s=picnic shelter/day use]]}. Keeps last week's file if RIDB fails.
The key is never printed or saved."""
import json, os, re, time, urllib.request, urllib.parse, datetime
KEY = os.environ.get('RIDB_API_KEY', '').strip()
STATES = (os.environ.get('STATES') or 'KY TN IN OH WV VA MO IL AL GA NC MS AR MD DC PA MI WI IA NE KS OK AK AZ CA CO CT DE FL HI ID LA ME MA MN MT NV NH NJ NM NY ND OR RI SD SC TX UT VT WA WY').split()
OUT = 'data/campfed'; os.makedirs(OUT, exist_ok=True)
def note(t, m): print(f'::notice title={t}::{m}')
if not KEY: note('RIDB_API_KEY missing', 'Add the secret RIDB_API_KEY (GitHub Settings > Secrets and variables > Actions).'); raise SystemExit(0)
API = 'https://ridb.recreation.gov/api/v1/'
def get(path, q):
    u = API + path + '?' + urllib.parse.urlencode(q)
    err = None
    for i in range(4):
        try:
            r = urllib.request.Request(u, headers={'apikey': KEY, 'accept': 'application/json', 'User-Agent': 'KPC trip planner (kentuckyportableclub.github.io)'})
            with urllib.request.urlopen(r, timeout=60) as f: return json.loads(f.read().decode('utf-8', 'replace'))
        except urllib.error.HTTPError as e:
            err = f'HTTP {e.code}'
            if e.code in (401, 403): break
            time.sleep(3 + i * 5)
        except Exception as e: err = str(e)[:120]; time.sleep(3 + i * 5)
    raise RuntimeError(err)
# agency names
ORG = {}
try:
    off = 0
    while True:
        j = get('organizations', {'limit': 50, 'offset': off}); R = j.get('RECDATA', [])
        for o in R: ORG[o.get('OrgID')] = o.get('OrgAbbrevName') or o.get('OrgName') or ''
        off += len(R)
        if not R or off >= int(j.get('METADATA', {}).get('RESULTS', {}).get('TOTAL_COUNT', 0)): break
except Exception as e:
    note('RIDB FAILED', f'{e} (401/403 = the key is wrong or not active yet)'); raise SystemExit(0)
def row(f):
    if 'campground' not in (f.get('FacilityTypeDescription') or '').lower() or f.get('Enabled') is False: return None
    la, lo = f.get('FacilityLatitude'), f.get('FacilityLongitude')
    try: la, lo = round(float(la), 5), round(float(lo), 5)
    except Exception: return None
    if not la or not lo: return None
    nm = re.sub(r'\s+', ' ', (f.get('FacilityName') or '').strip())
    kind = 's' if re.search(r'picnic|pavilion|day use|shelter', nm, re.I) and not re.search(r'camp', nm, re.I) else 'c'
    if nm.isupper(): nm = re.sub(r"'S\b", "'s", nm.title())
    nm = re.sub(r'\b(Ky|Tn|Va|Wv|Oh|Mo|Il|In)\b(?=\W*$)', lambda m: m.group(1).upper(), nm)
    fid = str(f.get('FacilityID'))
    return [fid, nm, la, lo, ORG.get(f.get('ParentOrgID'), ''), 1 if f.get('Reservable') else 0, 'https://www.recreation.gov/camping/campgrounds/' + fid, kind]
def pages(q):
    off = 0
    while True:
        j = get('facilities', dict(q, limit=50, offset=off)); R = j.get('RECDATA', [])
        for f in R: yield f
        off += len(R)
        if not R or off >= int(j.get('METADATA', {}).get('RESULTS', {}).get('TOTAL_COUNT', 0)): break
        time.sleep(.3)
BY, ok = {}, set()
for st in STATES:
    try:
        BY[st] = {r[0]: r for r in (row(f) for f in pages({'state': st})) if r}; ok.add(st)
    except Exception as e: note(f'US-{st} FAILED', f'{e}; kept the old file')
# Oct 16: some states (Louisiana, Delaware) came back empty by state name, so also read EVERY facility once and
# put each campground in the state its pin is in (kpc-us-states.json outlines).
def inside(x, y, ring):
    c = False; j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]; xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi: c = not c
        j = i
    return c
try:
    SHAPES = [(b['a'], [pl[0] for pl in b['p']]) for b in json.load(open('kpc-us-states.json'))]
    def state_of(la, lo):
        for a, rings in SHAPES:
            if a in BY and any(inside(lo, la, r) for r in rings): return a
        return ''
    added = 0
    for f in pages({}):
        r = row(f)
        if not r: continue
        a = state_of(r[2], r[3])
        if a and r[0] not in BY[a]: BY[a][r[0]] = r; added += 1
    note('Nationwide pass', f'{added} campgrounds added that the state search missed')
    # Oct 28 (tune pass): RIDB's state search goes by the OFFICE address, so 196 rows sat in the wrong state file (Hartwell Lake's
    # South Carolina campgrounds listed under Georgia, 132 in two files). The pin decides: a row whose pin is inside another
    # state's outline moves there (or leaves, when that state is not in this run); a pin inside no outline (coast) stays.
    def pin_state(la, lo):
        for a, rings in SHAPES:
            if any(inside(lo, la, r) for r in rings): return a
        return ''
    OWN = dict(SHAPES)
    def near_own(st, la, lo):     # about 3 miles of slack: the state outlines are simplified along the borders
        return any(inside(lo + dx, la + dy, r) for dx, dy in ((0, 0), (.05, 0), (-.05, 0), (0, .05), (0, -.05)) for r in OWN.get(st, []))
    moved = 0
    for st in list(BY):
        for fid, r in list(BY[st].items()):
            if near_own(st, r[2], r[3]): continue
            a = pin_state(r[2], r[3])
            if a and a != st:
                del BY[st][fid]; moved += 1
                if a in BY: BY[a].setdefault(fid, r)
    seen = {}
    for st in BY:
        for fid in BY[st]: seen.setdefault(fid, []).append(st)
    for fid, sts in seen.items():          # one campground, one state file (the planner reads the states nearby anyway)
        if len(sts) < 2: continue
        r = BY[sts[0]][fid]; home = pin_state(r[2], r[3])
        for st in sts:
            if st != (home if home in sts else sts[0]): del BY[st][fid]; moved += 1
    note('Pin check', f'{moved} campgrounds moved to the state their pin is in (or listed once instead of twice)')
except Exception as e: note('Nationwide pass FAILED', str(e)[:150])
# SELF-GRADE GATE (Oct 28, HQ): Kentucky's federal campgrounds in the hand-checked kpc-campgrounds.json (Recreation.gov ones
# with a pin) must be in the KY list, same name within 2 km (the hand pins sit at the entrance, RIDB's at the middle: Zilpo
# is 1.5 km apart). A FAIL keeps last month's Kentucky file and says so.
def hav_m(a, b, c, d):
    import math
    p = math.pi / 180
    h = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742000 * math.asin(math.sqrt(h))
def nw(s): return {w for w in re.sub(r'[^a-z0-9 ]', ' ', s.lower()).split() if w not in ('campground', 'camp', 'the', 'ky', 'tn', 'daniel', 'boone', 'nat', 'for')}
GATE = None
if 'KY' in BY:
    try:
        want = [g for p in json.load(open('kpc-campgrounds.json'))['parks'] for g in p.get('campgrounds', [])
                if 'recreation.gov' in (g.get('reserve', '') + g.get('source', '')) and g.get('la') and g.get('lo')]
        want = list({g['name']: g for g in want}.values())
        pool = list(BY['KY'].values()) + list(BY.get('TN', {}).values())
        miss = [g['name'] for g in want if not any(nw(g['name']) & nw(r[1]) and hav_m(g['la'], g['lo'], r[2], r[3]) <= 2000 for r in pool)]
        GATE = {'result': 'FAIL' if (miss or not want) else 'PASS', 'checked': len(want), 'missing': miss, 'date': datetime.date.today().isoformat()}
        note('Federal camps GATE ' + GATE['result'], f"{len(want) - len(miss)} of {len(want)} known Kentucky federal campgrounds found within 2 km" + (f"; missing: {', '.join(miss)}" if miss else '')
             + f" · grade me: federal campgrounds {GATE['result']}")
    except Exception as e: note('Federal camps GATE', f'not run: {str(e)[:120]}')
total = kept = 0
for st in STATES:
    if st not in ok and not BY.get(st): continue
    camps = sorted(BY.get(st, {}).values(), key=lambda c: c[1])
    fn = f'{OUT}/US-{st}.json'
    try: old = json.load(open(fn)).get('camps') or []
    except Exception: old = []
    # a state that came back with less than half of last month's list (RIDB timed out part way) keeps last month's file
    if (len(old) >= 10 and len(camps) < len(old) / 2) or (st == 'KY' and GATE and GATE['result'] == 'FAIL'):
        note(f'US-{st} kept', f'{len(camps)} read vs {len(old)} last time: last month\'s file kept'); kept += 1; continue
    out = {'state': st, 'updated': datetime.date.today().isoformat(), 'camps': camps}
    if st == 'KY' and GATE: out['gate'] = GATE
    json.dump(out, open(fn, 'w'), separators=(',', ':'))
    total += len(camps)
    if st in ('LA', 'DE', 'TN', 'KY') or len(camps) < 3: print(f'US-{st}: {sum(c[7]=="c" for c in camps)} campgrounds + {sum(c[7]=="s" for c in camps)} picnic shelters')
note('Federal campgrounds done', f'{total} campgrounds in {len(STATES)} states' + (f'; {kept} state file(s) kept from last time' if kept else ''))
