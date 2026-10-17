"""Federal campgrounds (Recreation.gov RIDB) for the states around Kentucky — US Trip Planner park cards.
Needs secret RIDB_API_KEY (free key from ridb.recreation.gov, Profile). Writes data/campfed/US-XX.json
{state, updated, camps:[[id, name, lat, lon, agency, reservable(0/1), url, kind c=campground s=picnic shelter/day use]]}. Keeps last week's file if RIDB fails.
The key is never printed or saved."""
import json, os, re, time, urllib.request, urllib.parse, datetime
KEY = os.environ.get('RIDB_API_KEY', '').strip()
STATES = (os.environ.get('STATES') or 'TN IN OH WV VA MO IL AL GA NC MS AR MD DC PA MI WI IA NE KS OK AK AZ CA CO CT DE FL HI ID LA ME MA MN MT NV NH NJ NM NY ND OR RI SD TX UT VT WA WY').split()
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
except Exception as e: note('Nationwide pass FAILED', str(e)[:150])
total = 0
for st in STATES:
    if st not in ok and not BY.get(st): continue
    camps = sorted(BY.get(st, {}).values(), key=lambda c: c[1])
    json.dump({'state': st, 'updated': datetime.date.today().isoformat(), 'camps': camps}, open(f'{OUT}/US-{st}.json', 'w'), separators=(',', ':'))
    total += len(camps)
    if st in ('LA', 'DE', 'TN', 'KY') or len(camps) < 3: note(f'US-{st}', f'{sum(c[7]=="c" for c in camps)} campgrounds + {sum(c[7]=="s" for c in camps)} picnic shelters')
note('Federal campgrounds done', f'{total} campgrounds in {len(STATES)} states')
