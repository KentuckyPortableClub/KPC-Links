#!/usr/bin/env python3
"""Nov 14 (KPC owner): the GPS export (kpc-gps.js readFers) keeps only 2-fer rows whose status starts with 'candidate', the same rule
kpc-overlap-finder.js lists by. A 'merged into one row' or 'dropped' row is never a 'Possible 2-fer spot' waypoint.
The three-row pair is shaped like US-2667 + US-4512 in KPC-Data's data/fers/US-NH.json.gz (merged 23 m, candidate 59 m, dropped
in pass 2 20 m), with a lat / lon on each row so the reader can see it. Node only, no network."""
import json, pathlib, shutil, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True
def check(name, cond, extra=''):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name + ('' if cond or not extra else f'  [{str(extra)[:300]}]'))
    ok = ok and bool(cond)

node = shutil.which('node')
if not node: print('SKIP node not installed'); sys.exit(0)
P = ['US-2667', 'US-4512']
def row(i, status, wide, la, lo): return {'id': f'US-2667+US-4512@area@{la:.3f},{lo:.3f}', 'refs': P, 'kind': 'area', 'status': status,
                                          'wide_m': wide, 'center': [la, lo], 'lat': la, 'lon': lo}
DOC = {'spots': [row(0, 'merged into one row: US-2667+US-4512@area@44.272,-71.305', 23, 44.271383, -71.299054),
                 row(1, 'candidate', 59, 44.271383, -71.305452),
                 row(2, 'dropped in pass 2', 20, 44.273623, -71.30109)]}
OTHER = {'spots': [{'refs': ['US-1001', 'US-1002'], 'lat': 35.5, 'lon': -80.5, 'status': s} for s in
                   ('candidate (saved outline only)', 'not sure: water not checked', 'very tight: could be map error', 'water only: boat or kayak', '')]
         + [{'refs': ['US-1001', 'US-1002'], 'lat': 35.6, 'lon': -80.6}], 'old': [['US-1001', 'US-1002', 35.7, -80.7, 'bare row']]}
H = r"""
globalThis.window = globalThis;
const G = require(%(gps)s);
const a = G.readFers(%(doc)s, 'US-2667'), b = G.readFers(%(doc)s), c = G.readFers(%(other)s);
console.log(JSON.stringify({ a: a.map(f => [f.refs, f.lat, f.lon]), b: b.length, c: c.map(f => [f.lat, f.lon]) }));
"""
with tempfile.TemporaryDirectory() as t:
    p = pathlib.Path(t) / 'h.js'
    p.write_text(H % {'gps': json.dumps(str(ROOT / 'kpc-gps.js')), 'doc': json.dumps(DOC), 'other': json.dumps(OTHER)})
    r = subprocess.run([node, str(p)], capture_output=True, text=True, timeout=60)
    try: o = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: o = {'err': (r.stdout + r.stderr)[-400:]}
check('three-row pair: only the 59 m candidate row is exported (the merged 23 m and the dropped 20 m rows are not)',
      o.get('a') == [[P, 44.271383, -71.305452]], o)
check('the whole file gives the same one row', o.get('b') == 1, o)
check("'candidate (saved outline only)' is kept (the finder shows it, with a badge); not sure / very tight / water only / no status / a bare array row are not",
      o.get('c') == [[35.5, -80.5]], o)
check('no console noise', not r.stderr.strip(), r.stderr[-200:])
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
