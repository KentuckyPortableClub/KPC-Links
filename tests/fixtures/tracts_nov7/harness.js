/* Node harness for tests/test_tracts_nov7.py (Nov 7, tracts Part 1). Loads the site's own browser scripts into node vm contexts with
   stubbed fetch / DOM / KPCGate, from two folders: the CURRENT tree and the origin/main copies (old), and prints one JSON answer.
   No network: every fetch is answered from local files or from the fixture file. Writes nothing.
   node harness.js <job.json>  ->  stdout JSON */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const JOB = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const NEW = JOB.root, OLD = JOB.old, DATA = JOB.data, FX = JOB.fixture || {};

function readJson(p) { try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch (e) { try { return JSON.parse(require('zlib').gunzipSync(fs.readFileSync(p + '.gz')).toString('utf8')); } catch (e2) { return null; } } }
/* deterministic fake geometry for a record id: a box (from the side file when known) with a hole for every third id and a second
   piece for records with pieces > 1, so the exports see holes and multipolygons */
function hash(s) { let h = 7; for (const c of String(s)) h = (h * 31 + c.charCodeAt(0)) >>> 0; return h; }
function rect(w, s, e, n) { return [[w, s], [e, s], [e, n], [w, n], [w, s]]; }
function fakeGeom(rid, rec) {
  let b = rec && rec.box;
  if (!b || !(b[2] > b[0]) || !(b[3] > b[1])) { const h = hash(rid), x = -90 + (h % 1000) / 100, y = 35 + ((h >> 10) % 500) / 100; b = [x, y, x + 0.02, y + 0.015]; }
  const [w, s, e, n] = b, dx = e - w, dy = n - s, h = hash(rid);
  const outer = rect(w, s, e, n);
  const poly = h % 3 === 0 ? [outer, rect(w + dx * 0.4, s + dy * 0.4, w + dx * 0.6, s + dy * 0.6).reverse()] : [outer];
  if (rec && +rec.pieces > 1) return { type: 'MultiPolygon', coordinates: [poly, [rect(e + 0.05, s, e + 0.05 + dx / 3, s + dy / 3)]] };
  return { type: 'Polygon', coordinates: poly };
}

const T0 = Date.parse('2026-11-07T18:00:00Z');
class FixedDate extends Date { constructor(...a) { if (a.length) super(...a); else super(T0); } static now() { return T0; } }
function makeCtx(dir, opt) {
  opt = opt || {};
  const FXT = opt.fx || FX;
  const els = {};
  const el = id => els[id] || (els[id] = { id, innerHTML: '', value: '', textContent: '', dataset: {}, style: {}, options: [], classList: { add() {}, remove() {} },
    querySelectorAll: () => [], querySelector: () => null, addEventListener() {}, appendChild() {}, remove() {}, click() {}, closest: () => null });
  const blobs = [];
  const sb = {
    console, URLSearchParams, AbortController, TextEncoder, setTimeout: (f) => 0, clearTimeout() {},
    Date: FixedDate,   /* one clock for old and new runs (the GPS files write a <time>) */
    location: { search: opt.search || '', href: 'https://x/kpc-test.html' + (opt.search || ''), pathname: '/kpc-test.html' },
    localStorage: { getItem: k => (opt.ls && k in opt.ls ? opt.ls[k] : null), setItem() {}, removeItem() {} },
    navigator: {}, matchMedia: () => ({ matches: false }),
    Blob: class { constructor(parts, o) { this.text = parts.join(''); this.type = (o || {}).type; blobs.push(this); } },
    URL: { createObjectURL: () => 'blob:x', revokeObjectURL() {} },
    MutationObserver: class { observe() {} },
    document: { readyState: 'complete', getElementById: el, createElement: () => el('_new' + Object.keys(els).length), querySelectorAll: () => [], querySelector: () => null,
      addEventListener() {}, body: { appendChild() {} }, head: { appendChild() {} }, documentElement: {} },
    _els: els, _blobs: blobs
  };
  if (opt.member !== undefined) sb.KPCGate = { member: () => !!opt.member };
  sb.window = sb;
  sb.fetch = async (u) => {
    const url = String(u), bare = url.split('?')[0];
    const ok = j => ({ ok: true, status: 200, json: async () => JSON.parse(JSON.stringify(j)), text: async () => JSON.stringify(j) });
    const no = () => ({ ok: false, status: 404, json: async () => { throw new Error('404'); }, text: async () => '' });
    if (bare === 'data/tract-switch.json') return opt.switchDoc ? ok(opt.switchDoc) : no();
    if (/objectIds=/.test(url)) {   /* any ArcGIS layer asked by id: the fixture's shapes, else fake shapes from the side file */
      const q = new URLSearchParams(url.split('?')[1] || ''), ids = (q.get('objectIds') || '').split(',').filter(Boolean);
      const feats = ids.map(id => {
        const g = (FXT.geom || {})[bare + '|' + id] || (FXT.geom || {})['*|' + id];
        const rec = (opt.recs || {})[id];
        const geometry = g || (opt.fake === false ? null : fakeGeom(id, rec));
        return geometry ? { type: 'Feature', id: isNaN(+id) ? id : +id, properties: { OBJECTID: isNaN(+id) ? id : +id, NAME: (rec && rec.name) || ('Record ' + id) }, geometry } : null;
      }).filter(Boolean);
      return ok({ type: 'FeatureCollection', features: feats });
    }
    if (/raw\.githubusercontent\.com\/.*\/data\/world-bounds\//.test(bare)) { const rel = bare.replace(/^.*?\/(data\/world-bounds\/.*)$/, '$1'); const j = (FXT.files || {})[rel] || readJson(path.join(DATA, rel)); return j ? ok(j) : no(); }
    const fx = (FXT.files || {})[bare]; if (fx) return ok(fx);
    if (FXT.only) return no();
    if (/^https?:/.test(bare)) return no();
    for (const base of [DATA, NEW]) { const j = readJson(path.join(base, bare)); if (j) return ok(j); }
    return no();
  };
  vm.createContext(sb);
  for (const f of opt.scripts || []) vm.runInContext(fs.readFileSync(path.join(dir, f), 'utf8'), sb, { filename: f });
  return sb;
}
const strip = x => JSON.parse(JSON.stringify(x));
async function saveAll(K, fc, o, ctx) {   /* KPCB.saveGeo for kml / gpx / geojson, the file text captured from the Blob */
  const out = {};
  for (const fmt of ['kml', 'gpx', 'geojson']) { ctx._blobs.length = 0; await K.saveGeo(fc, fmt, o, null); out[fmt] = ctx._blobs.length ? ctx._blobs[0].text : null; }
  return out;
}
async function gpsFiles(ctx, ref, park) {   /* kpc-gps-wire outline() -> kpc-gps buildPark(): the GPX / KML / GeoJSON the ⬇ GPS button makes */
  const W = ctx.KPCGPSW; if (!W) return null;
  const ol = await W.outline(ref, park);
  const b = ctx.KPCGPS.buildPark(Object.assign({ ref, name: park.name, lat: park.lat, lon: park.lon, outline: ol }), { fileDate: '2026-11-07', builtDate: '2026-11-07' });
  return { outline: strip(ol), gpx: b.gpx, kml: b.kml, geojson: b.geojson };
}

const PAGE_SCRIPTS = ['kpc-bounds.js', 'kpc-gps.js', 'kpc-gps-wire.js'];
const TOOL_SCRIPTS = ['kpc-bounds.js', 'kpc-maprep-logic.js', 'kpc-maprep-candidates.js', 'kpc-maprep-check.js'];

/* ---- OFF: one place's parks through usOutline + the three exports + the GPS files; same stubs for old and new ---- */
async function usPlace(dir, st, opt) {
  const FXT = (opt && opt.fx) || {};
  const side = (FXT.files || {})['data/us-key/tracts/US-' + st + '.json'] || readJson(path.join(DATA, 'data/us-key/tracts/US-' + st + '.json')) || {};
  const recs = {}; Object.values(side.parks || {}).forEach(ts => ts.forEach(t => { const id = String(t.rid).replace(/^[a-z]+/i, ''); if (!recs[id]) recs[id] = t; }));
  const ctx = makeCtx(dir, Object.assign({ scripts: PAGE_SCRIPTS, recs }, opt));
  ctx.KPCB.lookup = async ref => ({ prog: 'POTA', ref, name: 'Park ' + ref, short: 'Park ' + ref, la: 37, lo: -86, us: true, st, ky: false });
  const key = (FXT.files || {})['data/us-key/US-' + st + '.json'] || readJson(path.join(DATA, 'data/us-key/US-' + st + '.json')) || readJson(path.join(NEW, 'data/us-key/US-' + st + '.json'));
  const out = {};
  for (const ref of Object.keys(key.parks).sort()) {
    const u = await ctx.KPCB.usOutline(ref, key.parks[ref].n, 37, -86, [st]);
    const o = { ref, name: key.parks[ref].n || ref, la: 37, lo: -86, points: [[37.01, -86.01, 'Parking']] };
    const fc = { type: 'FeatureCollection', features: (u.fs || []) };
    out[ref] = { u: strip(u), files: u.fs && u.fs.length ? await saveAll(ctx.KPCB, fc, o, ctx) : null, gps: await gpsFiles(ctx, ref, { name: o.name, lat: 37, lon: -86 }) };
  }
  return out;
}
async function worldPlace(dir, cc, refs, opt) {
  const ctx = makeCtx(dir, Object.assign({ scripts: PAGE_SCRIPTS, fake: false }, opt));
  const out = {};
  for (const ref of refs) {
    const w = await ctx.KPCB.worldKey(ref);
    out[ref] = { w: strip(w), files: w && w.fs && w.fs.length ? await saveAll(ctx.KPCB, { type: 'FeatureCollection', features: w.fs }, { ref, name: ref, la: 52, lo: -1 }, ctx) : null,
      inHole: w && w.fs && (opt.holePoints || {})[ref] ? opt.holePoints[ref].map(p => w.fs.some(f => ctx.KPCB.inside(p[0], p[1], f.geometry))) : null };
  }
  return out;
}
/* ---- the Tool Box "Check all" output for a place ---- */
async function toolbox(dir, code, opt) {
  const ctx = makeCtx(dir, Object.assign({ scripts: TOOL_SCRIPTS }, opt));
  ctx._els.mrCheckSt = Object.assign(ctx.document.getElementById('mrCheckSt'), { value: code });
  const L = ctx.KPCMapLogic; L.loadRows(readJson(path.join(NEW, 'data/maprep/abbreviations.json')).rows);
  const ids = await ctx.KPCMapCheck.showAll();
  let html = ctx._els.mrSpot ? ctx._els.mrSpot.innerHTML : '';
  const rows = ctx._els.mrAllKeyRows ? ctx._els.mrAllKeyRows.innerHTML : null;
  const more = ctx._els.mrAllKeyMore ? ctx._els.mrAllKeyMore.innerHTML : null;
  let rows2 = null;
  const btn = ctx._els.mrAllKeyMoreBtn; if (btn && typeof btn.onclick === 'function') { btn.onclick(); rows2 = ctx._els.mrAllKeyRows.innerHTML; }
  return { n: (ids || []).length, html, rows, more, rows2, tractsOn: L.tractsOn() };
}

(async () => {
  const res = {};
  for (const t of JOB.tasks || []) {
    const dir = t.old ? OLD : NEW;
    try {
      if (t.kind === 'us') res[t.id] = await usPlace(dir, t.st, t.opt);
      else if (t.kind === 'world') res[t.id] = await worldPlace(dir, t.cc, t.refs, t.opt);
      else if (t.kind === 'toolbox') res[t.id] = await toolbox(dir, t.code, t.opt);
      else if (t.kind === 'switch') {
        const ctx = makeCtx(dir, Object.assign({ scripts: ['kpc-bounds.js', 'kpc-maprep-logic.js'] }, t.opt));
        const ready = await ctx.KPCB.tractsReady();
        res[t.id] = { ready, on: ctx.KPCB.tractsOn(), logic: ctx.KPCMapLogic.tractsOn(), mode: ctx.KPCB.tractMode(), count: ctx.KPCB.countMode(),
          fetchedSwitch: ctx.KPCB.tractsOn !== undefined };
      } else if (t.kind === 'simplify') {
        const ctx = makeCtx(dir, { scripts: ['kpc-gps.js'] });
        const G = ctx.KPCGPS, polys = t.polys;
        res[t.id] = { off: strip(G.simplifyOutline(polys, t.max)), on: strip(G.simplifyOutline(polys, t.max, t.tracts)),
          park: (() => { const fc = { type: 'FeatureCollection', features: t.features }; const b = G.buildPark({ ref: 'US-9100', name: 'Fixture', lat: 37, lon: -86, outline: { status: 'official', agency: 'Fixture', geojson: fc } }, { fileDate: '2026-11-07', maxPoints: t.max }); return { gpx: b.gpx }; })() };
      } else if (t.kind === 'logic') {
        const ctx = makeCtx(dir, Object.assign({ scripts: ['kpc-bounds.js', 'kpc-maprep-logic.js', 'kpc-maprep-candidates.js'] }, t.opt));
        await ctx.KPCB.tractsReady();
        const L = ctx.KPCMapLogic, C = ctx.KPCMapCands;
        res[t.id] = { on: L.tractsOn(), inOverlap: L.pinDistance(t.pt[0], t.pt[1], t.geom).inside, insideAny: L.insideAny ? L.insideAny(t.pt[0], t.pt[1], t.geom) : null,
          kpcbInside: ctx.KPCB.inside(t.pt[0], t.pt[1], t.geom), parks: L.alreadyParks ? L.alreadyParks(t.geom, t.pins).map(p => p.ref) : null,
          first: (L.alreadyPark(t.geom, t.pins) || {}).ref, pinCheck: strip(C.pinCheck([t.geom], t.pins)) };
      }
    } catch (e) { res[t.id] = { error: String(e && e.stack || e) }; }
  }
  process.stdout.write(JSON.stringify(res));
})();
