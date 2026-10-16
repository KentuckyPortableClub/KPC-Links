"""Saves the NOAA Weather Radio transmitters around Kentucky (from the NWS station data used by
weather.gov/nwr) into kpc-nwr.json for the Weather page: call sign, frequency, site, status, location
and the counties each one covers (SAME codes). Run monthly by kpc-nwr.yml."""
import json, re, sys, urllib.request, datetime
U = 'https://www.weather.gov/source/nwr/JS/ccl-data.js'
def notice(m): print('::notice title=NOAA Weather Radio::' + m)
try:
    t = urllib.request.urlopen(urllib.request.Request(U, headers={'User-Agent': 'KPC-Links (kentuckyportableclub.github.io)'}), timeout=90).read().decode('utf-8', 'replace')
    data = json.loads(t[t.index('['):t.rindex(']') + 1])
except Exception as e:
    notice(f'Could not read the NWS transmitter list ({e}); kept the old file.'); sys.exit(0)
out = []; bystate = {}
FIPS = {'01':'AL','02':'AK','04':'AZ','05':'AR','06':'CA','08':'CO','09':'CT','10':'DE','11':'DC','12':'FL','13':'GA','15':'HI','16':'ID','17':'IL','18':'IN','19':'IA','20':'KS','21':'KY','22':'LA','23':'ME','24':'MD','25':'MA','26':'MI','27':'MN','28':'MS','29':'MO','30':'MT','31':'NE','32':'NV','33':'NH','34':'NJ','35':'NM','36':'NY','37':'NC','38':'ND','39':'OH','40':'OK','41':'OR','42':'PA','44':'RI','45':'SC','46':'SD','47':'TN','48':'TX','49':'UT','50':'VT','51':'VA','53':'WA','54':'WV','55':'WI','56':'WY','72':'PR'}
def row(s, la, lo):
    return {'call': s.get('callsign', ''), 'freq': s.get('freq', ''), 'site': s.get('sitename', ''), 'loc': s.get('siteloc', ''), 'st': s.get('sitestate', ''),
            'status': s.get('status', ''), 'wfo': (s.get('wfo') or '').replace('|', ', '), 'power': s.get('power', ''), 'la': round(la, 4), 'lo': round(lo, 4),
            'same': sorted({c.get('same', '') for c in s.get('counties', []) if c.get('same')})}
for s in data:
    try: la, lo = float(s['lat']), float(s['lon'])
    except Exception: continue
    r = row(s, la, lo)
    # every state this transmitter covers (SAME code = 0 + state FIPS + county), plus its own state (Oct 16: nationwide, data/nwr/XX.json)
    for st in {FIPS.get(c[1:3]) for c in r['same'] if len(c) == 6} | {r['st']}:
        if st: bystate.setdefault(st, []).append(r)
    if not (35.0 <= la <= 40.3 and -91.0 <= lo <= -80.0): continue   # Kentucky and the transmitters that reach into it
    out.append(r)
out.sort(key=lambda x: x['call'])
if len(out) < 50: notice(f'Only {len(out)} transmitters found; kept the old file.'); sys.exit(0)
new = {'updated': datetime.date.today().isoformat(), 'source': 'https://www.weather.gov/nwr/', 'tx': out}
try: old = json.load(open('kpc-nwr.json'))
except Exception: old = {}
if old.get('tx') != out:
    json.dump(new, open('kpc-nwr.json', 'w'), separators=(',', ':'))
import os
os.makedirs('data/nwr', exist_ok=True)
for st, L in bystate.items():
    L.sort(key=lambda x: x['call'])
    p = f'data/nwr/{st}.json'
    try: o = json.load(open(p)).get('tx')
    except Exception: o = None
    if o != L: json.dump({'updated': datetime.date.today().isoformat(), 'source': 'https://www.weather.gov/nwr/', 'tx': L}, open(p, 'w'), separators=(',', ':'))
notice(f'{len(bystate)} state files in data/nwr ({sum(len(v) for v in bystate.values())} transmitter listings).')
notice(f'{len(out)} transmitters saved ({sum(1 for x in out if x["status"] != "NORMAL")} not normal).')
