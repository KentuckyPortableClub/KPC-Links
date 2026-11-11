/* Nov 11 2026 (KPC owner): the overlap finder reads the CURRENT answer key for every region and never lists a bare pin.
   Node, no browser, fake fetch (no network): the real kpc-overlap-finder.js, the real KPC.dataUrl snippet from
   kpc-overlap-finder.html and the real KPCREL block from kpc-gps.js run on a tiny fake page. Run by
   tests/test_overlap_finder_key_nov11.py (or: node tests/overlap_finder_key_nov11.js). */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = path.resolve(__dirname, '..');
let fails = 0; const check = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };

/* ---- fixtures: a key per area (current grades), 2-fer rows, the states map ---- */
const off = n => ({ g: 'official', m: [[1, n, 1, 'name']] }), pin = () => ({ g: 'pin', m: [] }), apx = n => ({ g: 'approximate', m: [[2, n, 1, 'picture trace']] });
const KEYS = {
  'data/us-key/US-OH.json': { parks: { 'US-1': off('A'), 'US-2': off('B'), 'US-3': pin(), 'US-4': apx('D'), 'US-5': Object.assign(pin(), { line: 1 }), 'US-6': pin(), 'US-8': pin() } },
  'data/us-key/US-WV.json': { parks: { 'US-9': pin(), 'US-10': off('J') } },
  'data/ca-key/CA-SK.json': { parks: { 'CA-1': off('K'), 'CA-2': pin(), 'CA-3': apx('M') } }
};
const sp = (refs, kind, extra) => Object.assign({ id: refs.join('+') + '@' + kind, refs, kind, status: 'candidate', passes: [1, 1, 1], reviewed: true, center: [39.5, -82.5], wide_m: 150, access_pin: { at: [39.5, -82.5], from: 'road', name: 'Rd', walk_m: 10 }, names: {} }, extra || {});
const LINE = r => ({ line_source: { [r]: { line: 'data/trails/' + r + '.json' } } });
const FERS = {
  'US-OH': { st: 'US-OH', spots: [
    sp(['US-1', 'US-2'], 'area'),                                         // shown
    sp(['US-1', 'US-3'], 'area'),                                         // hidden: pin
    sp(['US-1', 'US-6'], 'same land'),                                    // hidden: pin
    sp(['US-2', 'US-4'], 'area'),                                         // shown, approximate
    sp(['US-1', 'US-5'], 'trail', Object.assign({ len_m: 400 }, LINE('US-5'))),   // shown: the pin park is the line
    sp(['US-3', 'US-5'], 'trail', Object.assign({ len_m: 400 }, LINE('US-5'))),   // hidden: the AREA park is a pin
    sp(['US-1', 'US-5'], 'river', Object.assign({ len_m: 10, id: 'short' }, LINE('US-5'))),   // hidden: under 25 m
    sp(['US-1', 'US-8'], 'area', { point_circle: ['US-8'], pc_note: { 'US-8': 'point circle' }, tier: 'approximate' }),   // shown: point circle = approximate
    sp(['US-1', 'US-9'], 'area', { center: [40.5, -80.5] }),             // US-9 not in the OH key: graded in WV (pin): hidden
    sp(['US-2', 'US-10'], 'area', { center: [40.5, -80.5] }),            // US-10 graded in WV (official): shown
    sp(['US-1', 'US-3'], 'area', { status: 'very tight: could be map error', id: 'tight-pin' })   // a pin never shows, not even on the tight list
  ] },
  'CA-SK': { st: 'CA-SK', spots: [sp(['CA-1', 'CA-3'], 'area'), sp(['CA-1', 'CA-2'], 'area')] },
  'US-KY': { st: 'US-KY', spots: [sp(['US-1', 'US-3'], 'area')] },     // Kentucky: its own hand-checked list, no key read
  'US-WY': { st: 'US-WY', spots: [sp(['US-1', 'US-2'], 'area')] }      // its key does not load: nothing shown
};
const REGIONS = { base: '../KPC-Data/data/fers/', regions: ['US-OH', 'CA-SK', 'US-KY', 'US-WY'].map(f => ({ id: f.replace(/^US-/, ''), label: f, files: [f], public: false })) };
const STATES = [{ a: 'OH', p: [[[[-85, 38], [-80.6, 38], [-80.6, 42], [-85, 42], [-85, 38]]]] }, { a: 'WV', p: [[[[-80.6, 37], [-77, 37], [-77, 41], [-80.6, 41], [-80.6, 37]]]] }];

/* ---- fake fetch: the KPC-Data site, this site, everything else refused ---- */
const asked = [], everAsked = [];
const DATA = 'https://kentuckyportableclub.github.io/KPC-Data/';
const resp = (o, st) => new Response(o == null ? '' : JSON.stringify(o), { status: st || (o == null ? 404 : 200), headers: { 'content-type': 'application/json' } });
function fakeFetch(u) {
  u = String(u); asked.push(u); everAsked.push(u); const q = u.replace(/\?.*$/, '');
  if (q.startsWith(DATA)) { const p = q.slice(DATA.length); return Promise.resolve(resp(KEYS[p] || null)); }
  if (q === 'kpc-fers-regions.json') return Promise.resolve(resp(REGIONS));
  if (q === 'kpc-fers-reviewed.json') return Promise.resolve(resp({ reviewed: {} }));
  if (q === 'kpc-us-states.json') return Promise.resolve(resp(STATES));
  if (q === 'data/released/RELEASED.json') return Promise.resolve(resp({}));
  if (q === 'data/fers-approx-outlines.json') return Promise.resolve(resp({ parks: {} }));
  const m = /^\.\.\/KPC-Data\/data\/fers\/(.+)\.json$/.exec(q); if (m) return Promise.resolve(resp(FERS[m[1]] || null));
  return Promise.resolve(resp(null));
}

/* ---- a tiny fake page ---- */
function el() {
  const t = { innerHTML: '', textContent: '', value: '', hidden: false, checked: true, style: {}, dataset: {} };
  const noop = () => {}, fn = { addEventListener: noop, removeEventListener: noop, appendChild: noop, after: noop, before: noop, setAttribute: noop, focus: noop, remove: noop,
    getAttribute: () => null, querySelector: () => el(), querySelectorAll: () => [], closest: () => null, getBoundingClientRect: () => ({ top: 0, left: 0, width: 0, height: 0 }) };
  t.classList = { add: noop, remove: noop, toggle: noop, contains: () => false };
  return new Proxy(t, { get: (o, k) => (k in o ? o[k] : k in fn ? fn[k] : typeof k === 'symbol' ? undefined : any()) });
}
/* anything else the page touches: callable, any property, returns another stand-in */
function any() { const f = function () { return el(); }; return new Proxy(f, { get: (o, k) => (k === 'then' || typeof k === 'symbol' ? undefined : k === 'length' ? 0 : any()) }); }
const ids = {}, store = {};
const document = { getElementById: id => ids[id] || (ids[id] = el()), createElement: () => el(), addEventListener: () => {}, querySelectorAll: () => [], querySelector: () => null, documentElement: el(), body: el() };
const window = { document, fetch: fakeFetch, location: { search: '', pathname: '/kpc-overlap-finder.html', origin: 'http://x' }, navigator: {},
  localStorage: { getItem: k => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); }, removeItem: k => { delete store[k]; } },
  scrollTo: () => {}, addEventListener: () => {}, setTimeout, clearTimeout, URLSearchParams, Response, Promise, DecompressionStream, TextDecoder, Blob, Uint8Array, console };
window.window = window; window.scrollY = 0;
const ctx = vm.createContext(window);
const html = fs.readFileSync(path.join(ROOT, 'kpc-overlap-finder.html'), 'utf8');
const du = /<script id="kpc-data-url">([\s\S]*?)<\/script>/.exec(html);
check(!!du, 'kpc-overlap-finder.html has the KPC.dataUrl snippet');
vm.runInContext(du[1], ctx);
const gps = fs.readFileSync(path.join(ROOT, 'kpc-gps.js'), 'utf8');
const rel = /\/\* >>> kpc_released[\s\S]*?\/\* <<< kpc_released \*\//.exec(gps);
check(!!rel, 'kpc-gps.js has the KPCREL block (the map\'s key reader)');
vm.runInContext(rel[0], ctx);
vm.runInContext(fs.readFileSync(path.join(ROOT, 'kpc-overlap-finder.js'), 'utf8'), ctx);

const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  for (let i = 0; i < 50 && !window.KPCOverlap; i++) await sleep(20);
  await sleep(200);
  const O = window.KPCOverlap, ids_ = () => O.rows().map(g => g.patches.map(s => s.id)).flat().sort();
  const pinShown = () => O.rows().some(g => g.patches.some(s => { const lines = Object.keys(s.line_source || {}); const gr = O.grades(); return gr && gr.g && s.refs.some(r => gr.g[r] === 'pin' && lines.indexOf(r) < 0 && (s.point_circle || []).indexOf(r) < 0); }));

  asked.length = 0; await O.load('OH');
  check(everAsked.some(u => u.startsWith(DATA + 'data/us-key/US-OH.json?v=')), 'OH (the first region, read at page load and kept) reads data/us-key/US-OH.json from the KPC-Data site (KPC.dataUrl)');
  check(!everAsked.some(u => /\.\.\/KPC-Data\/data\/(us|ca|world)-key/.test(u)), 'no key read from the old ../KPC-Data/data/ path');
  check(everAsked.some(u => u.startsWith(DATA + 'data/us-key/US-WV.json')), 'a park missing from the OH key is graded in the state its spot lies in (WV key read)');
  const got = ids_();
  check(JSON.stringify(ids_()) === JSON.stringify(['US-1+US-2@area', 'US-1+US-5@trail', 'US-1+US-8@area', 'US-2+US-10@area', 'US-2+US-4@area']), 'OH shows exactly the allowed rows: ' + got.join(', '));
  const H = O.held();
  check(H.pin.length === 5 && H.short.length === 1 && H.unknown.length === 0, `OH held back: ${H.pin.length} pin (area, same land, trail area half, neighbour-state pin, tight list), ${H.short.length} under 25 m`);
  check(!pinShown(), 'OH lists no row with a bare-pin park (the line park of a trail row excepted)');
  const apxRow = O.rows().filter(g => g.key === 'US-2+US-4')[0];
  check(apxRow && apxRow.patches[0]._apx === true && H.apx.indexOf('US-2+US-4@area') >= 0, 'the approximate park\'s row is marked approximate (APPROXIMATE 2-FER + not-official note)');
  check(String(ids['ovList'].innerHTML).indexOf('US-3') < 0, 'the list never names the pin-only park US-3');
  const ol = O.rows().filter(g => g.key === 'US-1+US-2')[0];
  check(ol && !ol.patches[0]._apx, 'an official + official row is not marked approximate');

  asked.length = 0; await O.load('CA-SK');
  check(asked.some(u => u.startsWith(DATA + 'data/ca-key/CA-SK.json?v=')), 'CA-SK reads data/ca-key/CA-SK.json from the KPC-Data site');
  check(JSON.stringify(ids_()) === JSON.stringify(['CA-1+CA-3@area']) && O.rows()[0].patches[0]._apx === true && O.held().pin.length === 1, 'CA-SK: the pin row is hidden, the approximate row shown as approximate');

  asked.length = 0; await O.load('KY');
  check(!asked.some(u => /-key\//.test(u)), 'Kentucky reads no key file (its own hand-checked list)');
  check(ids_().length === 1, 'Kentucky\'s list is shown as it is');

  asked.length = 0; await O.load('WY');
  check(asked.some(u => u.startsWith(DATA + 'data/us-key/US-WY.json')), 'WY asks for its key');
  check(O.rows().length === 0 && /Could not load the park answer key/.test(ids['ovList'].innerHTML), 'a key that does not load: nothing is listed, and the page says why (fail safe)');

  /* every real region in kpc-fers-regions.json maps to a key file (KY excepted) */
  const R = JSON.parse(fs.readFileSync(path.join(ROOT, 'kpc-fers-regions.json'), 'utf8'));
  const miss = R.regions.filter(r => r.files.some(f => !(f === 'US-KY' || /^(US|CA)-[A-Z]{2}$/.test(f) || /^W-[A-Z]{2}$/.test(f))));
  check(miss.length === 0 && R.regions.length > 30, `all ${R.regions.length} real regions have a key file the finder knows (none needs a 'key' field)`);
  const js = fs.readFileSync(path.join(ROOT, 'kpc-overlap-finder.js'), 'utf8');
  check(!/REG\.key\b/.test(js) && !/keyBase/.test(js), 'the old region "key" field / keyBase path is gone');
  console.log(fails ? 'SOME FAILED' : 'ALL PASS'); process.exit(fails ? 1 : 0);
})().catch(e => { console.log('FAIL ' + (e && e.stack || e)); console.log('SOME FAILED'); process.exit(1); });
