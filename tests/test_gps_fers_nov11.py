#!/usr/bin/env python3
"""KPC owner, 2026-11-11 (M2): the GPS tool's 2-fer file (kpc-gps.js loadPark, opts.fers).
World areas (W-XX) are skipped: not one request for data/fers/W-*. An area stored only as <area>.json.gz (US-NC, US-ID) is read
and unpacked the way kpc-overlap-finder.js jz() does (.json first, then .json.gz, DecompressionStream), with the same result as the
same content served as .json. One answer per area. No file at all = no 2-fer spots, no throw. Node, fake fetch, no network."""
import gzip, json, pathlib, re, shutil, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True
def check(name, cond, extra=''):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name + ('' if cond or not extra else f'  [{str(extra)[:300]}]'))
    ok = ok and bool(cond)

node = shutil.which('node')
if not node: print('SKIP node not installed'); sys.exit(0)
ROWS = {'spots': [{'refs': ['US-1001', 'US-1002'], 'center': [35.5, -80.5], 'lat': 35.5, 'lon': -80.5, 'note': 'x'}]}
H = r"""
globalThis.window = globalThis; const asked = [];
const FILES = %(files)s, GZ = %(gz)s;
window.fetch = (u, o) => { u = String(u); asked.push(u); const k = u.split('?')[0];
  if (GZ[k]) return Promise.resolve(new Response(Buffer.from(GZ[k], 'base64'), { status: 200 }));
  if (FILES[k] !== undefined) return Promise.resolve(new Response(FILES[k], { status: 200, headers: { 'content-type': 'application/json' } }));
  return Promise.resolve(new Response('', { status: 404 })); };
%(nodz)s
const KPCGPS = require(%(gps)s);
KPCGPS.config({ parkInfo: () => null, outline: () => null, trails: () => [] });
(async () => {
  const out = {};
  for (const [ref, area] of [['US-1001', 'US-OH'], ['US-1001', 'US-NC'], ['US-1001', 'US-ZZ'], ['GB-0001', 'W-GB'], ['US-1002', 'US-NC'], ['GB-0002', 'W-GB']]) {
    try { const p = await KPCGPS.loadPark({ ref, name: 'P', lat: 35.5, lon: -80.5, area }, { fers: true }); out[ref + '@' + area] = (p.fers || []).map(f => [f.refs, f.lat, f.lon]); }
    catch (e) { out[ref + '@' + area] = 'THROW ' + e; }
  }
  out.asked = asked; console.log(JSON.stringify(out));
})();
"""
def run(nodz=False):
    gzb = __import__('base64').b64encode(gzip.compress(json.dumps(ROWS).encode())).decode()
    files = {'data/fers/US-OH.json': json.dumps(ROWS)}
    with tempfile.TemporaryDirectory() as t:
        p = pathlib.Path(t) / 'h.js'
        p.write_text(H % {'files': json.dumps(files), 'gz': json.dumps({'data/fers/US-NC.json.gz': gzb}), 'gps': json.dumps(str(ROOT / 'kpc-gps.js')),
                          'nodz': 'delete globalThis.DecompressionStream;' if nodz else ''})
        r = subprocess.run([node, str(p)], capture_output=True, text=True, timeout=60)
        try: return json.loads(r.stdout.strip().splitlines()[-1]), r.stderr
        except Exception: return {'err': (r.stdout + r.stderr)[-400:]}, r.stderr

o, err = run()
a = o.get('asked') or []
check('W-area park: zero requests containing data/fers/W-', not any('data/fers/W-' in u for u in a) and 'asked' in o, o)
check('W-area park: no 2-fer spots, no throw (the no-file state)', o.get('GB-0001@W-GB') == [] and o.get('GB-0002@W-GB') == [], o)
check('an area with .json: read as before', bool(o.get('US-1001@US-OH')) and any(u.startswith('data/fers/US-OH.json') for u in a))
check('an area with only .json.gz: read and unpacked, the same result as the same content as .json',
      o.get('US-1001@US-NC') and [x[1:] for x in o['US-1001@US-NC']] == [x[1:] for x in o['US-1001@US-OH']] and any(u.startswith('data/fers/US-NC.json.gz') for u in a), o)
check('.json is tried first, then .json.gz (the order of kpc-overlap-finder.js jz())',
      [u.split('?')[0] for u in a if 'fers/US-NC' in u][:2] == ['data/fers/US-NC.json', 'data/fers/US-NC.json.gz'], a)
check('one answer per area: a second NC park asks nothing more', len([u for u in a if 'fers/US-NC' in u]) == 2, a)
check('neither file: no 2-fer spots, no throw, asked once each', o.get('US-1001@US-ZZ') == [] and [u.split('?')[0] for u in a if 'US-ZZ' in u and 'fers' in u] == ['data/fers/US-ZZ.json', 'data/fers/US-ZZ.json.gz'], a)
check('no console noise', not err.strip(), err[-200:])
o2, _ = run(nodz=True)
check('a browser without DecompressionStream: stops at .json (as the finder), empty, no throw',
      o2.get('US-1001@US-NC') == [] and not any('.json.gz' in u for u in o2.get('asked') or []) and o2.get('US-1001@US-OH'), o2)
pages = {p.name: p.read_text(encoding='utf-8', errors='replace') for p in ROOT.glob('*.html')}
vs = {m for h in pages.values() for m in re.findall(r'kpc-gps\.js\?v=(\w+)', h)}
check(f'kpc-gps.js has one bumped ?v= on every page: {sorted(vs)}', vs == {'20261111m2'})
srcs = [p for p in list(ROOT.glob('*.js')) + list(ROOT.glob('*.html')) if 'data/fers/W-' in p.read_text(encoding='utf-8', errors='replace')]
check('no root script or page names data/fers/W-', not srcs, srcs)
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
