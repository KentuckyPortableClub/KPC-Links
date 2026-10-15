#!/usr/bin/env python3
"""Slim copy of the WWFF directory for the Park Info Finder (kpc-park-info.html).
wwff.co's directory CSV can't be read by a web page (no CORS), so every week we save the active references,
split by program prefix: data/wwff/<PREFIX>.json = [[ref, name, lat, lon, website, state, county], ...].
"""
import csv, io, json, pathlib, sys, urllib.request
UA = 'Mozilla/5.0 (compatible; KPC-Links WWFF directory copy)'
raw = urllib.request.urlopen(urllib.request.Request('https://wwff.co/wwff-data/wwff_directory.csv', headers={'User-Agent': UA}), timeout=120).read().decode('utf-8', 'replace')
out = {}
for r in csv.DictReader(io.StringIO(raw)):
    if (r.get('status') or '').lower() != 'active':
        continue
    ref = (r.get('reference') or '').strip().upper()
    if '-' not in ref:
        continue
    def f(k):
        v = (r.get(k) or '').strip()
        return '' if v in ('-', 'n/a', 'N/A') else v
    try:
        la, lo = round(float(r['latitude']), 5), round(float(r['longitude']), 5)
    except Exception:  # noqa: BLE001
        la = lo = None
    out.setdefault(ref.split('-')[0], []).append([ref, f('name'), la, lo, f('website'), f('state'), f('county')])
d = pathlib.Path('data/wwff'); d.mkdir(parents=True, exist_ok=True)
keep = set()
for p, rows in out.items():
    rows.sort()
    fn = d / (p + '.json'); keep.add(fn.name)
    s = json.dumps(rows, ensure_ascii=False, separators=(',', ':'))
    if not fn.exists() or fn.read_text(encoding='utf-8') != s:
        fn.write_text(s, encoding='utf-8')
for fn in d.glob('*.json'):
    if fn.name not in keep and fn.name != 'index.json':
        fn.unlink()
# location tiles (1 x 1 degree, by the floor of lat/lon) for "what's near me" lookups: data/wwff/t/<lat>_<lon>.json = [[ref, name, lat, lon], ...]
import math
t = d / 't'; t.mkdir(exist_ok=True); tiles = {}
for rows in out.values():
    for r in rows:
        if r[2] is None or r[3] is None: continue
        tiles.setdefault('%d_%d' % (math.floor(r[2]), math.floor(r[3])), []).append(r[:4])
tk = set()
for k, rows in tiles.items():
    rows.sort(); fn = t / (k + '.json'); tk.add(fn.name); s2 = json.dumps(rows, ensure_ascii=False, separators=(',', ':'))
    if not fn.exists() or fn.read_text(encoding='utf-8') != s2: fn.write_text(s2, encoding='utf-8')
for fn in t.glob('*.json'):
    if fn.name not in tk: fn.unlink()
(d / 'index.json').write_text(json.dumps(sorted(out), separators=(',', ':')), encoding='utf-8')
print('::notice title=WWFF directory::%d programs, %d active refs, KFF %d' % (len(out), sum(len(v) for v in out.values()), len(out.get('KFF', []))))
