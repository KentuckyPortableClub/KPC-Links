#!/usr/bin/env python3
"""Slim copy of the SOTA summits list, by location, for "Am I in the Park?" and the Activation Kit.
storage.sota.org.uk/summitslist.csv is ~25 MB, too big for a phone, so every week we keep only valid summits,
split into 1 x 1 degree tiles: data/sota/t/<floor lat>_<floor lon>.json = [[code, name, altFt, altM, lat, lon, points], ...].
"""
import csv, io, json, math, pathlib, datetime, urllib.request
UA = 'Mozilla/5.0 (compatible; KPC-Links SOTA summits copy)'
raw = urllib.request.urlopen(urllib.request.Request('https://storage.sota.org.uk/summitslist.csv', headers={'User-Agent': UA}), timeout=180).read().decode('utf-8', 'replace')
lines = raw.splitlines()
if lines and lines[0].startswith('SOTA Summits List'): lines = lines[1:]
today = datetime.date.today(); tiles = {}; n = 0
def date(s):
    try: d, m, y = s.split('/'); return datetime.date(int(y), int(m), int(d))
    except Exception: return None  # noqa: BLE001
for r in csv.DictReader(io.StringIO('\n'.join(lines))):
    vt, vf = date(r.get('ValidTo', '')), date(r.get('ValidFrom', ''))
    if (vt and vt < today) or (vf and vf > today): continue
    try: la, lo = round(float(r['Latitude']), 5), round(float(r['Longitude']), 5)
    except Exception: continue  # noqa: BLE001
    row = [r['SummitCode'].strip(), r['SummitName'].strip(), int(float(r['AltFt'] or 0)), int(float(r['AltM'] or 0)), la, lo, int(float(r['Points'] or 0))]
    tiles.setdefault('%d_%d' % (math.floor(la), math.floor(lo)), []).append(row); n += 1
if n < 50000: raise SystemExit('Only %d summits read; keeping the old copy.' % n)
t = pathlib.Path('data/sota/t'); t.mkdir(parents=True, exist_ok=True); keep = set()
for k, rows in tiles.items():
    rows.sort(); fn = t / (k + '.json'); keep.add(fn.name); s = json.dumps(rows, ensure_ascii=False, separators=(',', ':'))
    if not fn.exists() or fn.read_text(encoding='utf-8') != s: fn.write_text(s, encoding='utf-8')
for fn in t.glob('*.json'):
    if fn.name not in keep: fn.unlink()
print('::notice title=SOTA summits::%d valid summits in %d tiles' % (n, len(tiles)))
