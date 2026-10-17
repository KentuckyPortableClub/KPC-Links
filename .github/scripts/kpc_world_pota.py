"""POTA parks for the whole world, outside the US and Canada, as 1-degree tiles for the KPC US Trip Planner
(Brandon Oct 17: 'drop pins for all three programs for the world'). WWFF and SOTA world tiles already exist
(data/wwff/t, data/sota/t, built Sundays); this adds data/pota/t/<floor lat>_<floor lon>.json = [[ref, name, lat, lon], ...]
plus data/pota/index.json {updated, parks, tiles, programs:{prefix: count}}.
Source: api.pota.app/locations, then /location/parks/<locationDesc> for every location. A location that fails keeps
last month's rows (read back from the old tiles)."""
import json, os, glob, math, time, datetime, urllib.request

UA = {'User-Agent': 'KPC world POTA pins (kentuckyportableclub.github.io)'}
OUT = 'data/pota/t'


def note(t, m):
    print(f'::notice title={t}::{m}', flush=True)


def get(u):
    err = None
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as f:
                return json.loads(f.read().decode('utf-8', 'replace'))
        except Exception as e:
            err = e; time.sleep(3 + 4 * i)
    raise err


old = {}
for f in glob.glob(OUT + '/*.json'):
    try:
        for r in json.load(open(f)):
            old[r[0]] = r
    except Exception:
        pass

locs = get('https://api.pota.app/locations')
want = sorted({l['locationDesc'] for l in locs if l.get('locationDesc') and not str(l['locationDesc']).startswith(('US-', 'CA-'))})
note('Locations', f'{len(want)} POTA locations outside the US and Canada')
rows, failed, byp = {}, [], {}
t0 = time.time()
for i, desc in enumerate(want):
    try:
        for p in get(f'https://api.pota.app/location/parks/{desc}') or []:
            ref = str(p.get('reference') or '').upper()
            try:
                la, lo = round(float(p['latitude']), 5), round(float(p['longitude']), 5)
            except Exception:
                continue
            if not ref or (la == 0 and lo == 0) or abs(la) > 90 or abs(lo) > 180:
                continue
            rows[ref] = [ref, (p.get('name') or '').strip(), la, lo]
    except Exception as e:
        failed.append(desc)
    time.sleep(.25)
    if time.time() - t0 > 100 * 60:
        note('Time', f'stopped after {i + 1} locations (time limit); the rest keep last month'); failed += want[i + 1:]; break
pre = lambda r: r.split('-')[0]
fset = {d.split('-')[0] for d in failed}
for ref, r in old.items():
    if ref not in rows and pre(ref) in fset:
        rows[ref] = r
if len(rows) < 0.8 * len(old):
    note('Refused', f'only {len(rows)} parks this time vs {len(old)} last time: kept the old files'); raise SystemExit(0)
tiles = {}
for r in rows.values():
    tiles.setdefault(f'{math.floor(r[2])}_{math.floor(r[3])}', []).append(r)
    byp[pre(r[0])] = byp.get(pre(r[0]), 0) + 1
os.makedirs(OUT, exist_ok=True)
for f in glob.glob(OUT + '/*.json'):
    os.remove(f)
for k, L in tiles.items():
    json.dump(sorted(L), open(f'{OUT}/{k}.json', 'w'), separators=(',', ':'), ensure_ascii=False)
json.dump({'updated': datetime.date.today().isoformat(), 'parks': len(rows), 'tiles': len(tiles), 'programs': dict(sorted(byp.items()))},
          open('data/pota/index.json', 'w'), separators=(',', ':'))
note('World POTA pins', f'{len(rows):,} parks in {len(tiles):,} tiles, {len(byp)} programs; {len(failed)} locations failed')
