/* Nov 11 (site review S): the service worker (kpc-finder-sw.js) run in a fake worker: no browser, no network.
   Prints PASS / FAIL lines. Run: node tests/sw_sim_nov11.js [path-to-sw]   (called by tests/test_sw_offline_nov11.py) */
const vm = require('vm'), fs = require('fs'), path = require('path');
const SW = process.argv[2] || path.join(__dirname, '..', 'kpc-finder-sw.js');
const SRC = fs.readFileSync(SW, 'utf8');
const ORIGIN = 'https://site.test', BASE = ORIGIN + '/KPC-Links/';
let bad = 0;
const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) bad++; };

function env(opts = {}) {
  const stores = new Map(), L = {}; let rnd = opts.rnd == null ? 0.5 : opts.rnd;
  const mk = n => { if (!stores.has(n)) stores.set(n, new Map()); const m = stores.get(n);
    return {
      match: async k => { const e = m.get(typeof k === 'string' ? k : k.url); return e ? new Response(e.b, { status: e.s, headers: e.h }) : undefined; },
      put: async (k, r) => { if (r.status === 206) throw new TypeError('put 206'); const b = await r.arrayBuffer(); m.set(typeof k === 'string' ? k : k.url, { b, s: r.status, h: [...r.headers] }); },
      keys: async () => [...m.keys()].map(u => ({ url: u })),
      delete: async k => m.delete(typeof k === 'string' ? k : k.url) }; };
  const caches = { open: async n => mk(n), keys: async () => [...stores.keys()], delete: async n => stores.delete(n) };
  const M = Object.create(Math); M.random = () => rnd;
  const sb = { URL, Response, Request, Promise, setTimeout, clearTimeout, console, Math: M, caches, fetch: req => sb.fetchImpl(req) };
  sb.fetchImpl = async () => { throw new TypeError('offline'); };
  sb.self = { location: { origin: ORIGIN }, addEventListener: (t, f) => { L[t] = f; }, skipWaiting: () => Promise.resolve(), clients: { claim: () => Promise.resolve() } };
  vm.createContext(sb); vm.runInContext(SRC, sb);
  const e = {
    stores, caches, set rnd(v) { rnd = v; }, set net(f) { sb.fetchImpl = f; },
    async activate() { let p; L.activate({ waitUntil: x => { p = x; } }); await p; },
    async fire(url, o = {}) { const req = { url, method: o.method || 'GET', mode: o.mode || 'cors', headers: new Map() }; let p = null; L.fetch({ request: req, respondWith: x => { p = x; } }); return p ? { handled: true, res: await p } : { handled: false }; },
    async keys(n) { return (await (await caches.open(n)).keys()).map(k => k.url); },
    async seed(n, url, body = 'x', status = 200) { await (await caches.open(n)).put(url, new Response(body, { status })); },
    async text(r) { return r.res && r.res.text ? r.res.text() : ''; } };
  return e;
}
const ok200 = (body, extra) => new Response(body, Object.assign({ status: 200 }, extra));
(async () => {
  /* ---- cache names ---- */
  ok(/const APP = 'kpc-finder-v1';/.test(SRC) && /const TILES = 'kpc-tiles-v1';/.test(SRC), 'cache names kpc-finder-v1 and kpc-tiles-v1 unchanged in the worker');
  { const e = env(); await e.seed('kpc-finder-v1', BASE + 'a.js', 'A'); await e.seed('kpc-tiles-v1', 'https://tile.openstreetmap.org/1/1/1.png', 'T'); await e.seed('kpc-other', BASE + 'z', 'Z'); await e.seed('unrelated', BASE + 'z', 'Z');
    await e.activate(); const k = [...e.stores.keys()].sort();
    ok(k.includes('kpc-finder-v1') && k.includes('kpc-tiles-v1'), 'activate keeps both saved-map caches (phones keep their offline maps)');
    ok((await e.keys('kpc-finder-v1')).length === 1 && (await e.keys('kpc-tiles-v1')).length === 1, 'activate leaves the entries inside both caches alone'); }

  /* ---- what is handled ---- */
  { const e = env(); e.net = async () => ok200('n');
    ok(!(await e.fire(BASE + 'x.json', { method: 'POST' })).handled, 'POST is never handled (goes straight to the network)');
    ok(!(await e.fire('https://api.pota.app/spot/activator')).handled, 'api.pota.app live data is not handled or saved');
    ok(!(await e.fire('wss://broker.example/mqtt')).handled, 'mqtt / websocket traffic is not handled');
    ok(!(await e.fire('https://example.org/x.js')).handled, 'other cross-origin hosts are not handled');
    ok(!(await e.fire('https://services1.arcgis.com/x/query')).handled && !(await e.fire('https://apps.fs.usda.gov/x')).handled, 'the blocked GIS hosts are never fetched or saved by the worker (not handled)');
    ok(!(await e.fire('https://unpkg.com/mqtt/dist/mqtt.min.js')).handled, 'mqtt / other unpkg libraries are not handled (only Leaflet 1.9.4)');
    ok((await e.fire('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js')).handled, 'Leaflet 1.9.4 from unpkg is handled'); }

  /* ---- stale data: network first, a changed file shows at once ---- */
  { const e = env(); let body = 'V1'; e.net = async () => ok200(body);
    let r = await e.fire(BASE + 'finder.js'); ok(await e.text(r) === 'V1', 'first load of finder.js: V1');
    await new Promise(r => setTimeout(r, 20)); body = 'V2';
    r = await e.fire(BASE + 'finder.js?v=20261111'); ok(await e.text(r) === 'V2', 'finder.js changed on the site: the next load is V2 (not the saved V1)');
    await new Promise(r => setTimeout(r, 20)); e.net = async () => { throw new TypeError('offline'); };
    r = await e.fire(BASE + 'finder.js'); ok(await e.text(r) === 'V2', 'no signal: finder.js answers with the newest saved copy (V2)');
    const nav = await e.fire(BASE + 'kpc-planner.html', { mode: 'navigate' });
    const navT = await e.text(nav);
    ok(nav.res.status === 503 && /No signal/.test(navT), 'no signal, page never saved: an honest "No signal" page, not a browser error');
    ok(/Save my trip for no signal/.test(navT) && /Save for offline/.test(navT), 'that page names the right save button for the planners as well as Park Commander');
    const sub = await e.fire(BASE + 'nothing-saved.js'); ok(sub.handled && sub.res.type === 'error', 'no signal, script never saved: a clean network error (no hang, no crash)'); }

  /* ---- site errors ---- */
  { const e = env(); e.net = async () => ok200('GOOD'); await e.fire(BASE + 'finder.js'); await new Promise(r => setTimeout(r, 20));
    e.net = async () => new Response('down', { status: 503 });
    let r = await e.fire(BASE + 'finder.js'); ok(await e.text(r) === 'GOOD', 'site answers 503 but a saved copy exists: the saved copy is used (listed file)');
    r = await e.fire(BASE + 'kpc-notlisted.js'); ok(r.res.status === 503, 'site answers 503, nothing saved: the 503 is passed on honestly');
    e.net = async () => ok200('OTHER'); await e.fire(BASE + 'kpc-planner.html', { mode: 'navigate' });   /* not in the list: not saved by the worker */
    e.net = async () => new Response('gone', { status: 404 });
    r = await e.fire(BASE + 'finder.js'); ok(r.res.status === 404, 'a 404 is passed on (a removed file is not served from the old copy forever)'); }
  { const e = env(); e.net = async () => new Response('nope', { status: 404 }); await e.fire(BASE + 'finder.js'); await new Promise(r => setTimeout(r, 20));
    ok((await e.keys('kpc-finder-v1')).length === 0, 'a 404 answer is not saved as a good copy');
    e.net = async () => new Response('part', { status: 206 }); await e.fire(BASE + 'finder.js'); await new Promise(r => setTimeout(r, 20));
    ok((await e.keys('kpc-finder-v1')).length === 0, 'a 206 partial answer is not saved');
    e.net = async () => new Response(null, { status: 204 }); await e.fire(BASE + 'finder.js'); await new Promise(r => setTimeout(r, 20));
    ok((await e.keys('kpc-finder-v1')).length === 0, 'a 204 empty answer is not saved'); }

  /* ---- released files: the ?v= is the version ---- */
  { const e = env(); const R = BASE + 'data/released/';
    e.net = async req => ok200(req.url.includes('?v=B') ? 'FILE-B' : 'FILE-A');
    await e.fire(R + 'us-key/US-WI.json?v=A'); await e.fire(R + 'RELEASED.json'); await new Promise(r => setTimeout(r, 20));
    const ks = await e.keys('kpc-finder-v1');
    ok(ks.length === 0, 'released files are fetched from the network every time and are not saved by the worker itself');
    await e.seed('kpc-finder-v1', R + 'us-key/US-WI.json?v=A', 'FILE-A'); await e.seed('kpc-finder-v1', R + 'RELEASED.json', 'INDEX');
    e.net = async () => { throw new TypeError('offline'); };
    let r = await e.fire(R + 'us-key/US-WI.json?v=A'); ok(await e.text(r) === 'FILE-A', 'no signal: the released file saved for ?v=A is served for ?v=A');
    r = await e.fire(R + 'us-key/US-WI.json?v=B'); ok(r.res.type === 'error', 'no signal: a NEW index asking ?v=B is not answered with the copy saved for ?v=A (no new-index / old-file pair)');
    r = await e.fire(R + 'RELEASED.json'); ok(await e.text(r) === 'INDEX', 'no signal: the saved index is served'); }
  { const e = env(); const R = BASE + 'data/released/'; await e.seed('kpc-finder-v1', R + 'us-key/US-OH.json', 'OLD-SAVE');   /* the old packers saved it without the ?v= */
    e.net = async () => { throw new TypeError('offline'); };
    const r = await e.fire(R + 'us-key/US-OH.json?v=Z'); ok(r.res.type === 'error', 'no signal: a copy saved without its ?v= is not passed off as the version the index names'); }

  /* ---- tiles ---- */
  { const e = env({ rnd: 0 }); const T = 'https://tile.openstreetmap.org/'; const c = await e.caches.open('kpc-tiles-v1');
    for (let i = 0; i < 2600; i++) await c.put(T + '9/' + i + '/1.png', new Response('t'));
    e.net = async () => ok200('png');
    for (let i = 0; i < 5; i++) await e.fire('https://a.tile.openstreetmap.org/12/' + i + '/7.png');   /* a short session: far fewer than 40 tiles */
    await new Promise(r => setTimeout(r, 100));
    const n = (await e.keys('kpc-tiles-v1')).length; ok(n <= 2500, 'tile cache is trimmed to the 2500 limit in a short worker lifetime (was ' + n + ')'); }
  { const e = env(); e.net = async () => ok200('png'); await e.fire('https://b.tile.openstreetmap.org/12/1/7.png'); await new Promise(r => setTimeout(r, 30));
    const k = await e.keys('kpc-tiles-v1'); ok(k.length === 1 && k[0] === 'https://tile.openstreetmap.org/12/1/7.png', 'a./b./c. tile hosts share one saved copy');
    e.net = async () => { throw new TypeError('offline'); };
    const r = await e.fire('https://c.tile.openstreetmap.org/12/1/7.png'); ok(await e.text(r) === 'png', 'no signal: a saved tile is served for any of a./b./c.'); }
  { const e = env(); e.net = async () => ({ ok: false, status: 0, type: 'opaque', clone() { return this; } });
    await e.fire('https://a.tile.openstreetmap.org/3/1/1.png'); await new Promise(r => setTimeout(r, 30));
    ok((await e.keys('kpc-tiles-v1')).length === 0, 'an opaque (no-cors) tile answer is not saved (it could count for megabytes)'); }
  /* Nov 11 (owner): the worker only keeps tiles the page asked for; it never fetches on its own */
  { const e = env(); const seen = []; e.net = async req => { seen.push(req.url); return ok200('png'); };
    await e.fire('https://a.tile.openstreetmap.org/12/100/200.png'); await new Promise(r => setTimeout(r, 60));
    ok(seen.length === 1 && /12\/100\/200/.test(seen[0]), 'a viewed tile causes exactly one request: no neighbours, no refresh, no prefetch (' + seen.length + ')');
    await new Promise(r => setTimeout(r, 200)); ok(seen.length === 1, 'and nothing is requested later on its own');
    e.net = async () => { throw new TypeError('offline'); };
    const hit = await e.fire('https://tile.openstreetmap.org/12/100/200.png'); ok(await e.text(hit) === 'png', 'offline: the tile the member viewed online is served from the cache');
    const miss = await e.fire('https://tile.openstreetmap.org/12/101/200.png'); ok(miss.res.type === 'error', 'offline: a tile never viewed is a plain network error (the map shows its empty tile)'); }
  console.log(bad ? bad + ' FAILED' : 'ALL PASSED'); process.exit(bad ? 1 : 0);
})().catch(e => { console.log('FAIL worker test crashed: ' + e.stack); process.exit(1); });
