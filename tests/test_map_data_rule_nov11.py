#!/usr/bin/env python3
"""KPC owner, 2026-11-11 (job 3, the map data rule): public map tools read RELEASED copies only.
The KPCREL block (the same in kpc-bounds.js, kpc-gps.js, kpc-padus-layer.js and kpc-us-planner.js) is run in node with a fake
fetch (no network) for every case:
  released area + file listed      -> the released copy, with its own version
  released area + file NOT listed  -> nothing (never the working copy)
  area never released (world)      -> nothing, unless the owner's switch UNRELEASED_WORKING names it
  RELEASED.json fails (404, bad JSON, offline) -> the last good index this browser kept, else nothing; asked again after a minute
  KPC_WORKING_COPY (Map Rep)       -> the working copy, as before
Plus: kpc-gps.js reads the US key through KPCREL on the wired pages too, and KPCB.jget never asks a blocked host."""
import json, pathlib, re, shutil, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True
def check(name, cond, extra=''):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name + ('' if cond or not extra else f'  [{str(extra)[:300]}]'))
    ok = ok and bool(cond)

NAMES = ['kpc-bounds.js', 'kpc-gps.js', 'kpc-padus-layer.js', 'kpc-us-planner.js']
SRC = {n: (ROOT / n).read_text(encoding='utf-8') for n in NAMES}
blk = lambda s: s[s.index('/* >>> kpc_released'):s.index('/* <<< kpc_released */')] + '/* <<< kpc_released */'
B = blk(SRC['kpc-bounds.js'])
check('the four KPCREL copies are byte-identical', len({blk(s) for s in SRC.values()}) == 1)
check("the owner's switch is in the block and empty by default (the rule)", re.search(r'var UNRELEASED_WORKING = \[\];', B) is not None)
check('the block never turns a failed RELEASED.json into "nothing released" ({})', ".catch(function () { return {}; })" not in B and "r.ok ? r.json() : {}" not in B)

INDEX = {'areas': {'US': {'sha': 'x'}, 'CA': {'sha': 'y'}}, 'files': {
    'us-key/US-FL.json': [['us-key/US-FL.json', 'aaa111']],
    'outlines/US-FL.geojson.gz': [['outlines/US-FL.geojson.gz', 'bbb222']],
    'ca-key/CA-ON.json': [['ca-key/CA-ON.json', 'ccc333']]}}
FILES = {
    'data/released/us-key/US-FL.json': '{"parks":{"US-1":{"g":"official"}}}',
    'data/released/outlines/US-FL.geojson.gz': '{"type":"FeatureCollection","features":[{"id":1}]}',
    'data/released/ca-key/CA-ON.json': '{"parks":{"CA-1":{}}}',
    # working copies (this site and the KPC-Data site): a public page must never get these
    'data/us-key/US-FL.json': '{"parks":{"WORKING":{}}}', 'data/us-key/US-GA.json': '{"parks":{"WORKING":{}}}',
    'data/outlines/US-GA.geojson.gz': '{"features":[{"id":"WORKING"}]}', 'data/world-key/GB.json': '{"parks":{"WORKING":{}}}',
    'data/ca-key/CA-QC.json': '{"parks":{"WORKING":{}}}',
}
HARNESS = r"""
const FILES = %(files)s, MODE = %(mode)s;
globalThis.window = globalThis;
let asked = [], now = 1e12;
const realNow = Date.now; Date.now = () => now;
const store = {}; if (MODE.ls !== 'none') window.localStorage = { getItem: k => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } };
if (MODE.saved) store.kpcReleasedIndex = JSON.stringify(MODE.saved);
let idx = MODE.index;
const res = b => ({ ok: true, status: 200, json: () => Promise.resolve(JSON.parse(b)), arrayBuffer: () => Promise.resolve(new TextEncoder().encode(b).buffer) });
window.fetch = (u, o) => { asked.push([u, (o || {}).cache || '']); const k = String(u).split('?')[0];
  if (k === 'data/released/RELEASED.json') {
    if (idx === 'offline') return Promise.reject(new TypeError('Failed to fetch'));
    if (idx === '404') return Promise.resolve({ ok: false, status: 404 });
    if (idx === 'bad') return Promise.resolve({ ok: true, status: 200, json: () => Promise.reject(new SyntaxError('bad json')) });
    return Promise.resolve(res(JSON.stringify(idx))); }
  const b = FILES[k]; return Promise.resolve(b === undefined ? { ok: false, status: 404 } : res(b)); };
const workingAsked = [];
const working = p => { workingAsked.push(p); const b = FILES[String(p).split('?')[0]]; return Promise.resolve(b === undefined ? { ok: false, status: 404 } : res(b)); };
%(block)s
(async () => {
  const out = {}, P = MODE.paths;
  for (const p of P) { out[p] = { got: await KPCREL.get(p, working), state: await KPCREL.state(p) }; }
  if (MODE.later) { idx = MODE.later; now += 61000; out.later = await KPCREL.get(MODE.laterPath, working); out.laterState = await KPCREL.state(MODE.laterPath); }
  out.asked = asked; out.workingAsked = workingAsked; out.store = store;
  console.log(JSON.stringify(out));
})().catch(e => console.log(JSON.stringify({ err: String(e && e.stack || e) })));
"""
node = shutil.which('node')
def run(mode, block=B):
    with tempfile.TemporaryDirectory() as t:
        p = pathlib.Path(t) / 'h.js'; p.write_text(HARNESS % {'files': json.dumps(FILES), 'mode': json.dumps(mode), 'block': block})
        r = subprocess.run([node, str(p)], capture_output=True, text=True, timeout=60)
        try: return json.loads(r.stdout.strip().splitlines()[-1])
        except Exception: return {'err': (r.stdout + r.stderr)[-400:]}
def notWorking(o):   # nothing outside data/released (and RELEASED.json) was asked, and the caller's working reader was never used
    return not o.get('workingAsked') and all(a[0].startswith('data/released/') for a in o.get('asked', []))

if not node:
    print('SKIP node not installed: the KPCREL runs'); sys.exit(0)

PATHS = ['data/us-key/US-FL.json', 'data/outlines/US-FL.geojson.gz', 'data/ca-key/CA-ON.json', 'data/us-key/US-GA.json',
         'data/outlines/US-GA.geojson.gz', 'data/ca-key/CA-QC.json', 'data/world-key/GB.json']
o = run({'index': INDEX, 'paths': PATHS})
check('released + listed: the key is the released copy', (o.get('data/us-key/US-FL.json') or {}).get('got') == {'parks': {'US-1': {'g': 'official'}}}, o)
check('released + listed: asked as data/released/<file>?v=<its version>, from the cache', ['data/released/us-key/US-FL.json?v=aaa111', 'force-cache'] in o.get('asked', [])
      and ['data/released/outlines/US-FL.geojson.gz?v=bbb222', 'force-cache'] in o.get('asked', []) and ['data/released/ca-key/CA-ON.json?v=ccc333', 'force-cache'] in o.get('asked', []))
check('released + listed: state() says released', (o.get('data/us-key/US-FL.json') or {}).get('state') == 'released')
check('released area, file NOT listed (US-GA key, US-GA outline, CA-QC key): nothing', all((o.get(p) or {}).get('got') is None for p in PATHS[3:6]), o)
check('released area, file NOT listed: state() says not listed', all((o.get(p) or {}).get('state') == 'not listed' for p in PATHS[3:6]))
check('area never released (world-key/GB): nothing, state() says not released', (o.get('data/world-key/GB.json') or {}).get('got') is None
      and (o.get('data/world-key/GB.json') or {}).get('state') == 'not released')
check('no working copy was asked for at all (this site or KPC-Data)', notWorking(o), o.get('workingAsked'))
check('RELEASED.json asked once, never from the cache', [a for a in o.get('asked', []) if 'RELEASED' in a[0]] == [['data/released/RELEASED.json', 'no-cache']])
check('a good RELEASED.json is kept in this browser for a later blip', json.loads((o.get('store') or {}).get('kpcReleasedIndex') or 'null') == INDEX)

# the owner's switch: world named -> world reads its working file until released; US / CA rules unchanged
sw = B.replace('var UNRELEASED_WORKING = [];', "var UNRELEASED_WORKING = ['world'];")
o = run({'index': INDEX, 'paths': ['data/world-key/GB.json', 'data/us-key/US-GA.json']}, sw)
check("switch UNRELEASED_WORKING = ['world']: the world key is read from the working copy", (o.get('data/world-key/GB.json') or {}).get('got') == {'parks': {'WORKING': {}}}
      and o.get('workingAsked') == ['data/world-key/GB.json'], o)
check('switch on: a released area still never falls back (US-GA not listed = nothing)', (o.get('data/us-key/US-GA.json') or {}).get('got') is None)

# RELEASED.json does not load
for how in ('404', 'bad', 'offline'):
    o = run({'index': how, 'paths': ['data/us-key/US-FL.json', 'data/world-key/GB.json']})
    check(f'RELEASED.json {how}, nothing kept: nothing at all, never the working copy', (o.get('data/us-key/US-FL.json') or {}).get('got') is None
          and (o.get('data/world-key/GB.json') or {}).get('got') is None and notWorking(o) and (o.get('data/us-key/US-FL.json') or {}).get('state') == 'no index', o)
o = run({'index': {}, 'paths': ['data/us-key/US-FL.json']})
check('RELEASED.json = {} (no areas): treated as not loaded, never as "read the working copy"', (o.get('data/us-key/US-FL.json') or {}).get('got') is None and notWorking(o))
o = run({'index': 'offline', 'saved': INDEX, 'paths': ['data/us-key/US-FL.json', 'data/us-key/US-GA.json']})
check('RELEASED.json offline, a good one kept: the released copy (last known), still never the working copy',
      (o.get('data/us-key/US-FL.json') or {}).get('got') == {'parks': {'US-1': {'g': 'official'}}} and (o.get('data/us-key/US-GA.json') or {}).get('got') is None and notWorking(o), o)
o = run({'index': 'offline', 'saved': {'bogus': 1}, 'paths': ['data/us-key/US-FL.json']})
check('a kept index that is not a release index is not used', (o.get('data/us-key/US-FL.json') or {}).get('got') is None and notWorking(o))
o = run({'index': 'offline', 'ls': 'none', 'paths': ['data/us-key/US-FL.json']})
check('no localStorage at all (private mode): nothing, no crash', 'err' not in o and (o.get('data/us-key/US-FL.json') or {}).get('got') is None, o)
o = run({'index': '404', 'paths': ['data/us-key/US-FL.json'], 'later': INDEX, 'laterPath': 'data/us-key/US-FL.json'})
check('after a failed RELEASED.json it is asked again a minute later, and the released copy then shows',
      o.get('later') == {'parks': {'US-1': {'g': 'official'}}} and o.get('laterState') == 'released' and len([a for a in o.get('asked', []) if 'RELEASED' in a[0]]) == 2, o)

# Map Rep: KPC_WORKING_COPY keeps the working copy (released area or not, index or not)
rv = 'window.KPC_WORKING_COPY = true;\n' + B
o = run({'index': INDEX, 'paths': ['data/us-key/US-FL.json', 'data/world-key/GB.json']}, rv)
check('KPC_WORKING_COPY (Map Rep): the working copy even for a released, listed file', (o.get('data/us-key/US-FL.json') or {}).get('got') == {'parks': {'WORKING': {}}}
      and (o.get('data/world-key/GB.json') or {}).get('got') == {'parks': {'WORKING': {}}} and (o.get('data/us-key/US-FL.json') or {}).get('state') == 'working', o)
o = run({'index': 'offline', 'paths': ['data/us-key/US-FL.json']}, rv)
check('KPC_WORKING_COPY with RELEASED.json offline: still the working copy', (o.get('data/us-key/US-FL.json') or {}).get('got') == {'parks': {'WORKING': {}}})
for h in ('kpc-maprep.html', 'kpc-maprep-reps.html'):
    hs = (ROOT / h).read_text(encoding='utf-8', errors='replace')
    check(f'{h} still sets KPC_WORKING_COPY before the loaders', 'window.KPC_WORKING_COPY=true' in hs and hs.index('window.KPC_WORKING_COPY=true') < hs.index('kpc-bounds.js'))

# ---- kpc-gps.js: the wired pages (kpc-gps-wire.js gives a page-wide fetch + dataUrl) read the US key through KPCREL too
G = r"""
globalThis.window = globalThis; const asked = [];
const res = b => ({ ok: true, status: 200, json: () => Promise.resolve(JSON.parse(b)), arrayBuffer: () => Promise.resolve(new TextEncoder().encode(b).buffer) });
const F = { 'data/released/RELEASED.json': JSON.stringify(%(index)s), 'data/released/us-key/US-FL.json': '{"parks":{"US-1":{"g":"official","n":"Rel"}}}' };
window.fetch = (u, o) => { asked.push(String(u)); const k = String(u).split('?')[0]; return Promise.resolve(F[k] ? res(F[k]) : { ok: false, status: 404 }); };
window.document = { addEventListener() {}, createElement: () => ({ style: {} }), head: { appendChild() {} }, querySelector: () => null, querySelectorAll: () => [] };
const KPCGPS = require(%(gps)s);
const KD = 'https://kentuckyportableclub.github.io/KPC-Data/';
const kfetch = u => { asked.push('kfetch:' + u); return Promise.resolve(String(u).indexOf(KD) === 0 ? res('{"parks":{"US-1":{"g":"pin","n":"WORKING"}}}') : { ok: false, status: 404 }); };
KPCGPS.config({ dataUrl: p => KD + p, fetch: kfetch, parkInfo: () => ({ ref: 'US-1', name: 'X', lat: 28, lon: -82, area: 'US-FL' }), outline: () => null, trails: () => [] });
(async () => {
  let got = null; try { const P = await KPCGPS.loadPark({ ref: 'US-1', name: 'X', lat: 28, lon: -82, area: 'US-FL' }, {}); got = P && (P.key || P.k || null); } catch (e) { got = 'ERR ' + e; }
  console.log(JSON.stringify({ asked, got }));
})();
"""
with tempfile.TemporaryDirectory() as t:
    p = pathlib.Path(t) / 'g.js'; p.write_text(G % {'index': json.dumps(INDEX), 'gps': json.dumps(str(ROOT / 'kpc-gps.js'))})
    r = subprocess.run([node, str(p)], capture_output=True, text=True, timeout=60)
    try: g = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: g = {'err': (r.stdout + r.stderr)[-400:]}
ga = g.get('asked') or []
check('kpc-gps.js on a wired page: the US key is read from data/released (KPCREL), not the KPC-Data working copy',
      any(a.startswith('data/released/us-key/US-FL.json?v=aaa111') for a in ga) and not any('data/us-key/US-FL.json' in a and 'released' not in a for a in ga), g)
gs = SRC['kpc-gps.js'][SRC['kpc-gps.js'].index('/* <<< kpc_released */'):]
check('kpc-gps.js: only a per-call fetch / dataUrl skips KPCREL (the page-wide config no longer does)', '!cfg.fetch && !cfg.dataUrl' not in gs)

# ---- KPCB.jget: hosts we never contact live are refused before any fetch
J = r"""
globalThis.window = globalThis; const asked = [];
window.fetch = (u, o) => { asked.push(String(u)); return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ features: [] }), arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)) }); };
window.document = { createElement: () => ({ style: {} }), head: { appendChild() {} }, addEventListener() {}, querySelector: () => null, querySelectorAll: () => [] };
window.localStorage = { getItem: () => null, setItem() {} };
require(%(b)s);
(async () => {
  const urls = ['https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWS/FeatureServer/0/query?f=geojson', 'https://services7.arcgis.com/x/arcgis/rest/services/y/FeatureServer/0/query',
    'https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_Wilderness_02/MapServer/0/query', 'https://ncnhde.natureserve.org/x', 'https://gis.example.gov/arcgis/rest/services/33TOOklri9xpic7U/x'];
  const out = {};
  for (const u of urls) { try { await KPCB.jget(u); out[u] = 'fetched'; } catch (e) { out[u] = 'refused'; } }
  try { await KPCB.jget('https://kygisserver.ky.gov/arcgis/rest/services/x/MapServer/0/query'); out.ky = 'fetched'; } catch (e) { out.ky = 'refused ' + e; }
  try { await KPCB.jget('https://www.arcgis.com/sharing/x'); out.www = 'fetched'; } catch (e) { out.www = 'refused'; }
  console.log(JSON.stringify({ asked, out }));
})();
"""
with tempfile.TemporaryDirectory() as t:
    p = pathlib.Path(t) / 'j.js'; p.write_text(J % {'b': json.dumps(str(ROOT / 'kpc-bounds.js'))})
    r = subprocess.run([node, str(p)], capture_output=True, text=True, timeout=60)
    try: jo = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: jo = {'err': (r.stdout + r.stderr)[-400:]}
outs = jo.get('out') or {}
check('KPCB.jget refuses services*.arcgis.com, apps.fs.usda.gov, ncnhde.natureserve.org and the Grant County server, before any fetch',
      len(outs) == 7 and all(v == 'refused' for k, v in outs.items() if k not in ('ky', 'www')) and not any(re.search(r'arcgis\.com|fs\.usda|natureserve|33TOO', a) and 'www.arcgis.com' not in a for a in jo.get('asked', [])), jo)
check('KPCB.jget still asks an allowed host (Kentucky state GIS; www.arcgis.com is not services*)', outs.get('ky') == 'fetched' and outs.get('www') == 'fetched', outs)

# ---- static: the front-end files of this job make no live call to a blocked host
LIVE = re.compile(r"""['"`]https?://(?:[^'"`/]*\.)?(?:services\d*\.arcgis\.com|apps\.fs\.usda\.gov|ncnhde\.natureserve\.org)/""")
for f in ('gis-overlays.js', 'kpc-map-extras.js', 'kpc-live.js', 'kpc-lc-map.js', 'kpc-planner.js', 'kpc-access-finder-classic.html', 'kpc-maprep.js'):
    s = (ROOT / f).read_text(encoding='utf-8', errors='replace')
    if f == 'kpc-maprep.js':   # its two consts stay for the "GIS MAP" links a person clicks (www.arcgis.com map viewer); never queried here
        check(f'{f}: the NPS / FWS map servers are not queried (only the click-to-open GIS MAP links name them)', 'B.jget(NPSQ' not in s and 'B.jget(FWSQ' not in s)
    else:
        check(f'{f}: no live URL on services*.arcgis.com / apps.fs.usda.gov / ncnhde', not LIVE.search(s), (LIVE.search(s) or [''])[0])
go = (ROOT / 'gis-overlays.js').read_text(encoding='utf-8')
check("gis-overlays.js: NPS, Wilderness and FWS boundaries fall back to the same saved file (ky-nps / ky-wilderness / ky-fws), never a live server",
      all(re.search(r"%s:\{[^\n]*file:'%s',live:'%s'" % (k, f, f), go) for k, f in (('bnps', 'ky-nps.geojson'), ('bwilder', 'ky-wilderness.geojson'), ('bfws', 'ky-fws.geojson'))))
check('gis-overlays.js: a trail with no saved copy says so in the status line', 'needs a saved copy on this site' in go)
check('kpc-live.js: state lines come from the saved kpc-us-states.json', "jget('kpc-us-states.json'" in (ROOT / 'kpc-live.js').read_text(encoding='utf-8'))
check('kpc-map-extras.js: the WMA points layer (services5) is marked as needing a saved copy and skipped', "nosave:true" in (ROOT / 'kpc-map-extras.js').read_text(encoding='utf-8'))
mr = (ROOT / 'kpc-maprep-research.js').read_text(encoding='utf-8')
check('kpc-maprep-research.js: every services*.arcgis.com host is saved-copy only (2..9 too), and by-id reads check it', r'services\d*\.arcgis\.com|apps\.fs\.usda\.gov' in mr and "!isSavedCopy({ url: X[pre(id)][0] })" in mr)
tb = (ROOT / 'kpc-maprep-toolbox.js').read_text(encoding='utf-8')
check('kpc-maprep-toolbox.js: the layer tooltip escapes the feature name (agency / OSM text, not HTML)', "bindTooltip(esc(feat.properties.name || '')" in tb and "bindTooltip(feat.properties.name" not in tb)
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
