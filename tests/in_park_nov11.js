/* Nov 11 2026 (KPC owner): "Am I in the Park?" (kpc-in-park.js) answers for the spot you are at NOW, says when a reference
   is not found, drops a slow answer for a reference you already replaced, and never calls an approximate outline official.
   Node, no browser, no network: the real kpc-in-park.js runs on a tiny fake page with a fake KPCB (boundaries) and a fake L.
   Run by tests/test_in_park_nov11.py (or: node tests/in_park_nov11.js). */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = path.resolve(__dirname, '..');
const SRC = fs.readFileSync(path.join(ROOT, 'kpc-in-park.js'), 'utf8');
let fails = 0; const check = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
const tick = (ms) => new Promise(r => setTimeout(r, ms || 0));

/* a square outline around a spot, about 2 km across */
const square = (la, lo, d) => ({ type: 'Polygon', coordinates: [[[lo - d, la - d], [lo + d, la - d], [lo + d, la + d], [lo - d, la + d], [lo - d, la - d]]] });
const bbOf = g => { const c = g.coordinates[0]; return [Math.min(...c.map(p => p[0])), Math.min(...c.map(p => p[1])), Math.max(...c.map(p => p[0])), Math.max(...c.map(p => p[1]))]; };
const km = (a, b, c, d) => { const R = Math.PI / 180, x = Math.sin((c - a) * R / 2) ** 2 + Math.cos(a * R) * Math.cos(c * R) * Math.sin((d - b) * R / 2) ** 2; return 12742 * Math.asin(Math.sqrt(x)); };

function page(search, kpcb) {
  const listeners = {}, els = {};
  function el(id) {
    const e = { id, innerHTML: '', textContent: '', className: '', value: '', style: {}, dataset: {}, onclick: null,
      classList: { add() {}, remove() {}, toggle() {}, contains: () => false },
      addEventListener(t, f) { (listeners[id + ':' + t] = listeners[id + ':' + t] || []).push(f); },
      insertAdjacentHTML(w, h) { e.innerHTML += h; }, scrollIntoView() {}, remove() {} };
    return e;
  }
  const document = { getElementById: id => els[id] || (els[id] = el(id)), createElement: () => el('x'), addEventListener() {}, querySelector: () => null, querySelectorAll: () => [] };
  let mapClick = null, layersOn = 0;
  const layer = (gj) => { const o = { addTo() { if (gj === 1) layersOn++; o.on = true; return o; }, remove() { if (o.on && gj === 1) layersOn--; o.on = false; return o; }, bindTooltip() { return o; }, setStyle() { return o; }, getBounds() { return {}; } }; return o; };
  const map = { on(t, f) { if (t === 'click') mapClick = f; return map; }, setView() { return map; }, getZoom: () => 14, fitBounds() { return map; } };
  const L = { map: () => map, tileLayer: () => layer(), geoJSON: () => layer(1), layerGroup: () => layer(), circle: () => layer(), circleMarker: () => layer(), polyline: () => layer() };
  const unhandled = [];
  const window = { document, L, KPCB: kpcb, location: { search }, navigator: { onLine: false }, URLSearchParams, setTimeout, clearTimeout, Promise, console, Date, Math, Map, Set, JSON, Object, Array, String, Number, isFinite };
  window.window = window;
  const ctx = vm.createContext(window);
  const onRej = e => unhandled.push(String(e && e.message || e));
  process.on('unhandledRejection', onRej);
  vm.runInContext(SRC, ctx);
  return { els, $: id => document.getElementById(id), listeners, click: (la, lo) => mapClick({ latlng: { lat: la, lng: lo } }), unhandled, layersOn: () => layersOn, done: () => process.off('unhandledRejection', onRej) };
}

/* fake KPCB: PAD-US answers come back when the test lets them (deferred), one area per spot */
function fakeB(opts) {
  opts = opts || {};
  const B = {
    asked: [], waiting: [],
    esc: s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])),
    inKY: () => false, km, dist: k => k.toFixed(2) + ' km', dir: () => 'north', isLine: () => false,
    inside: (la, lo, g) => { const b = bbOf(g); return lo > b[0] && lo < b[2] && la > b[1] && la < b[3]; },
    edge: (la, lo, g) => { const b = bbOf(g), d = Math.min(Math.abs(lo - b[0]), Math.abs(lo - b[2])) * 88, e = Math.min(Math.abs(la - b[1]), Math.abs(la - b[3])) * 111; return { km: Math.min(d, e), lat: la, lon: lo }; },
    sameName: (a, b) => !!a && !!b && String(a).toLowerCase() === String(b).toLowerCase(),
    refsFor: (f, near) => near.filter(p => B.inside(p.la, p.lo, f.geometry)),
    kyRefs: () => [], kyData: () => ({ parks: [], kff: [], summits: [] }), ky: () => Promise.resolve([]), kyFor: () => Promise.resolve([]),
    ACCESS: {}, OSM_NOTE: '', osmAt: () => Promise.resolve([]), elevation: () => Promise.resolve(null),
    wwffNear: () => Promise.resolve([]), sotaNear: () => Promise.resolve([]),
    potaNear: (la, lo) => Promise.resolve((opts.parks || []).filter(p => km(la, lo, p.la, p.lo) < 30)),
    padusArea: (la, lo) => { B.asked.push([la, lo]); const f = { type: 'Feature', properties: { Unit_Nm: 'Land ' + la, GIS_Acres: 500 }, geometry: square(la, lo, 0.01) }; f._nm = f.properties.Unit_Nm; f._bb = bbOf(f.geometry);
      if (!opts.deferPadus) return Promise.resolve([f]); return new Promise(r => B.waiting.push(() => r([f]))); },
    lookup: q => opts.lookup ? opts.lookup(q) : Promise.resolve(null),
    usOutline: (...a) => opts.usOutline ? opts.usOutline(...a) : Promise.resolve({ fs: [] }),
    retired: () => Promise.resolve(null)
  };
  return B;
}

(async () => {
  /* 1. the spot moved while the first area was still loading: the answer is for the NEW spot, not judged against the old area */
  {
    const B = fakeB({ deferPadus: true, parks: [{ ref: 'US-1', name: 'Alpha', la: 37.0, lo: -100.0 }, { ref: 'US-2', name: 'Bravo', la: 40.0, lo: -90.0 }] });
    const P = page('', B);
    P.click(37.0, -100.0); await tick(5);
    P.click(40.0, -90.0); await tick(5);
    check(B.asked.length === 1, 'while one area loads, a second far tap does not start a second load at once');
    B.waiting.shift()(); await tick(20);
    check(B.asked.length === 2 && B.asked[1][0] === 40.0, 'when the first area lands, the newest spot gets its own boundaries');
    if (B.waiting.length) B.waiting.shift()(); await tick(20);
    const v = P.els.ipV.innerHTML;
    check(/US-2/.test(v) && /INSIDE/.test(v) && !/NOT INSIDE/.test(v), 'the answer is for the spot you are at now (inside US-2), not the old area: ' + v.replace(/<[^>]+>/g, ' ').slice(0, 90));
    P.done();
  }
  /* 2. a reference nobody knows: a plain "could not find" (was a script error and 'Loading…' forever) */
  {
    const B = fakeB({});
    const P = page('?ref=US-99999', B);
    await tick(30);
    check(/Could not find US-99999/.test(P.els.ipTgt.innerHTML), 'an unknown reference says "Could not find US-99999": ' + P.els.ipTgt.innerHTML.replace(/<[^>]+>/g, '').slice(0, 80));
    check(!P.unhandled.length, 'no unhandled promise rejection (' + P.unhandled.join('|') + ')');
    P.done();
  }
  /* 3. an approximate US outline: the answer names it approximate, never "Official" */
  {
    const fs3 = [{ type: 'Feature', properties: {}, geometry: square(41.0, -82.0, 0.02) }]; fs3[0]._nm = 'Five Lakes'; fs3[0]._bb = bbOf(fs3[0].geometry);
    const B = fakeB({ lookup: () => Promise.resolve({ prog: 'POTA', ref: 'US-5', name: 'Five Lakes', la: 41.0, lo: -82.0, us: true, ky: false, st: 'OH' }),
      usOutline: () => Promise.resolve({ fs: fs3, label: 'approx', why: 'the names only partly match' }) });
    const P = page('?ref=US-5', B);
    await tick(30);
    check(/approximate outline, not official/i.test(P.els.ipTgt.innerHTML), 'the reference line says approximate');
    P.click(41.0, -82.0); await tick(30);
    const v = P.els.ipV.innerHTML;
    check(/INSIDE/.test(v) && /Approximate outline, not official/.test(v) && !/Official \(USGS PAD-US\)/.test(v), 'inside an approximate outline the answer says "Approximate outline, not official": ' + v.replace(/<[^>]+>/g, ' ').slice(0, 120));
    P.done();
  }
  /* 4. a slow answer for an older reference never replaces the newer one; the old outline leaves the map */
  {
    let slow = null;
    const out = ref => ({ fs: [Object.assign({ type: 'Feature', properties: {}, geometry: square(41, -82, 0.02) }, { _nm: ref, _bb: bbOf(square(41, -82, 0.02)) })], label: 'official' });
    const B = fakeB({ lookup: q => q === 'US-7' ? new Promise(r => { slow = () => r({ prog: 'POTA', ref: 'US-7', name: 'Seven', la: 41, lo: -82, us: true, st: 'OH' }); })
      : Promise.resolve({ prog: 'POTA', ref: q, name: 'Eight', la: 41, lo: -82, us: true, st: 'OH' }), usOutline: r => Promise.resolve(out(r)) });
    const P = page('', B);
    const submit = v => { P.$('ipRef').value = v; (P.listeners['ipRefForm:submit'] || []).forEach(f => f({ preventDefault() {} })); };
    submit('US-7'); await tick(5);
    submit('US-8'); await tick(30);
    check(/US-8/.test(P.els.ipTgt.innerHTML), 'the newer reference is shown');
    slow(); await tick(30);
    check(/US-8/.test(P.els.ipTgt.innerHTML) && !/US-7/.test(P.els.ipTgt.innerHTML), 'the slow older answer (US-7) is dropped: ' + P.els.ipTgt.innerHTML.replace(/<[^>]+>/g, '').slice(0, 60));
    check(P.layersOn() <= 1, 'one park outline on the map at most (' + P.layersOn() + ')');
    P.done();
  }
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.log('FAIL the test itself stopped: ' + (e && e.stack || e)); console.log('SOME FAILED'); process.exit(1); });
