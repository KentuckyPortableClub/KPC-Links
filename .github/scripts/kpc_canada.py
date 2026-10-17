"""Canadian pins for the KPC US Trip Planner (Brandon Oct 16: 'Canada you can go ahead and drop the pins, we work on
boundaries later'). Writes data/canada.json in the same row format as locations.json:
  ['POTA', 'CA-0001', name, lat, lon, url]   from api.pota.app (all Canadian POTA parks, by province)
  ['WWFF', 'VEFF-0001', name, lat, lon, url] from our weekly WWFF copy (data/wwff/VEFF.json)
  ['SOTA', 'VE7/..', name, lat, lon, url, altM, points] from our weekly SOTA tiles (VE/VA/VY/VO associations)
Keeps last week's POTA rows if POTA can't be reached."""
import json, os, glob, time, urllib.request, datetime
UA = {'User-Agent': 'KPC Canada pins (kentuckyportableclub.github.io)'}
def note(t, m): print(f'::notice title={t}::{m}')
def get(u):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as f: return json.loads(f.read().decode('utf-8', 'replace'))
        except Exception as e: err = e; time.sleep(3 + 4 * i)
    raise err
try: old = json.load(open('data/canada.json'))
except Exception: old = {'rows': []}
pota, prov = {}, {}
for pv in 'AB BC MB NB NL NS NT NU ON PE QC SK YT'.split():
    try:
        L = get(f'https://api.pota.app/location/parks/CA-{pv}')
        for p in L:
            ref = p.get('reference', '')
            try: la, lo = round(float(p['latitude']), 5), round(float(p['longitude']), 5)
            except Exception: continue
            if ref.startswith('CA-') and ref not in pota:
                pota[ref] = ['POTA', ref, (p.get('name') or '').strip(), la, lo, 'https://pota.app/#/park/' + ref]; prov[pv] = prov.get(pv, 0) + 1
        time.sleep(.5)
    except Exception as e: note(f'CA-{pv}', f'failed: {str(e)[:100]}')
if not pota:
    pota = {r[1]: r for r in old.get('rows', []) if r[0] == 'POTA'}; note('POTA', 'no answer: kept last copy')
rows = sorted(pota.values(), key=lambda r: r[1])
try:
    for x in json.load(open('data/wwff/VEFF.json')):
        try: rows.append(['WWFF', x[0], x[1], round(float(x[2]), 5), round(float(x[3]), 5), 'https://wwff.co/directory/?showRef=' + x[0]])
        except Exception: pass
except Exception as e: note('WWFF', str(e)[:100])
seen = set()
for f in glob.glob('data/sota/t/*.json'):
    for r in json.load(open(f)):
        a = r[0].split('/')[0]
        if a[:2] in ('VE', 'VA', 'VY', 'VO') and r[0] not in seen:
            seen.add(r[0]); rows.append(['SOTA', r[0], r[1], r[4], r[5], 'https://sotl.as/summits/' + r[0], r[3], r[6]])
json.dump({'updated': datetime.date.today().isoformat(), 'rows': rows}, open('data/canada.json', 'w'), separators=(',', ':'), ensure_ascii=False)
note('Canada pins', f"{len(pota)} POTA parks ({', '.join(f'{k} {v}' for k, v in sorted(prov.items()))}), {sum(1 for r in rows if r[0]=='WWFF')} WWFF, {len(seen)} SOTA")
