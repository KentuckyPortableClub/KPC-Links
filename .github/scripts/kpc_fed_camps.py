"""Federal campgrounds (Recreation.gov RIDB) for the states around Kentucky — US Trip Planner park cards.
Needs secret RIDB_API_KEY (free key from ridb.recreation.gov, Profile). Writes data/campfed/US-XX.json
{state, updated, camps:[[id, name, lat, lon, agency, reservable(0/1), url]]}. Keeps last week's file if RIDB fails.
The key is never printed or saved."""
import json, os, re, time, urllib.request, urllib.parse, datetime
KEY = os.environ.get('RIDB_API_KEY', '').strip()
STATES = (os.environ.get('STATES') or 'TN IN OH WV VA MO IL').split()
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
total = 0
for st in STATES:
    try:
        camps, off = [], 0
        while True:
            j = get('facilities', {'state': st, 'limit': 50, 'offset': off}); R = j.get('RECDATA', [])
            for f in R:
                if 'campground' not in (f.get('FacilityTypeDescription') or '').lower(): continue
                if f.get('Enabled') is False: continue
                la, lo = f.get('FacilityLatitude'), f.get('FacilityLongitude')
                try: la, lo = round(float(la), 5), round(float(lo), 5)
                except Exception: continue
                if not la or not lo: continue
                nm = re.sub(r'\s+', ' ', (f.get('FacilityName') or '').strip())
                if re.search(r'picnic|pavilion|day use|shelter', nm, re.I) and not re.search(r'camp', nm, re.I): continue
                if nm.isupper(): nm = re.sub(r"'S\b", "'s", nm.title())
                nm = re.sub(r'\b(Ky|Tn|Va|Wv|Oh|Mo|Il|In)\b(?=\W*$)', lambda m: m.group(1).upper(), nm)
                fid = str(f.get('FacilityID'))
                camps.append([fid, nm, la, lo,
                              ORG.get(f.get('ParentOrgID'), ''), 1 if f.get('Reservable') else 0,
                              'https://www.recreation.gov/camping/campgrounds/' + fid])
            off += len(R)
            if not R or off >= int(j.get('METADATA', {}).get('RESULTS', {}).get('TOTAL_COUNT', 0)): break
            time.sleep(.3)
        camps.sort(key=lambda c: c[1])
        json.dump({'state': st, 'updated': datetime.date.today().isoformat(), 'camps': camps},
                  open(f'{OUT}/US-{st}.json', 'w'), separators=(',', ':'))
        total += len(camps)
        note(f'US-{st}', f'{len(camps)} federal campgrounds ({sum(c[5] for c in camps)} reservable), agencies: ' + ', '.join(sorted({c[4] for c in camps if c[4]})))
    except Exception as e: note(f'US-{st} FAILED', f'{e}; kept the old file')
note('Federal campgrounds done', f'{total} campgrounds in {len(STATES)} states')
