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
out = []
for s in data:
    try: la, lo = float(s['lat']), float(s['lon'])
    except Exception: continue
    if not (35.0 <= la <= 40.3 and -91.0 <= lo <= -80.0): continue   # Kentucky and the transmitters that reach into it
    out.append({'call': s.get('callsign', ''), 'freq': s.get('freq', ''), 'site': s.get('sitename', ''), 'loc': s.get('siteloc', ''), 'st': s.get('sitestate', ''),
                'status': s.get('status', ''), 'wfo': (s.get('wfo') or '').replace('|', ', '), 'power': s.get('power', ''), 'la': round(la, 4), 'lo': round(lo, 4),
                'same': sorted({c.get('same', '') for c in s.get('counties', []) if c.get('same')})})
out.sort(key=lambda x: x['call'])
if len(out) < 50: notice(f'Only {len(out)} transmitters found; kept the old file.'); sys.exit(0)
new = {'updated': datetime.date.today().isoformat(), 'source': 'https://www.weather.gov/nwr/', 'tx': out}
try: old = json.load(open('kpc-nwr.json'))
except Exception: old = {}
if old.get('tx') != out:
    json.dump(new, open('kpc-nwr.json', 'w'), separators=(',', ':'))
notice(f'{len(out)} transmitters saved ({sum(1 for x in out if x["status"] != "NORMAL")} not normal).')
