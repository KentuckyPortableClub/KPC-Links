#!/usr/bin/env python3
"""Split locations.json (5.4 MB, every page that needs a park list loaded all of it) by program.
Usage: python3 split_locations.py locations.json OUTDIR
Writes OUTDIR/locations-pota.json, locations-sota.json, locations-wwff.json (same row shape, same order).
OUTDIR = the KPC-Data repo ROOT (KPC.dataUrl asks KPC-Data first). Pages fall back to filtering locations.json if a split file is missing.
Run it again whenever locations.json is rebuilt (kpc_new_refs.py etc.)."""
import json, sys, pathlib
src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
rows = json.loads(src.read_text(encoding='utf-8'))
rows = rows.get('rows', rows) if isinstance(rows, dict) else rows
by = {'POTA': [], 'SOTA': [], 'WWFF': []}
other = 0
for r in rows:
    if r[0] in by: by[r[0]].append(r)
    else: other += 1
for k, v in by.items():
    p = out / f'locations-{k.lower()}.json'
    new = json.dumps(v, ensure_ascii=False, separators=(',', ':'))
    if not p.exists() or p.read_text(encoding='utf-8') != new:
        p.write_text(new, encoding='utf-8')
    print(k, len(v), 'rows', len(new) // 1024, 'KB')
assert sum(len(v) for v in by.values()) + other == len(rows)
print('rows with another program (not written):', other)
