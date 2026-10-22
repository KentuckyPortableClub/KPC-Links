/* Builds the KPC APP's OFFLINE PARK PACKS (Fable, Oct 22) into app/packs/ (served by GitHub Pages, the app downloads one state at a time).
   Kentucky: every POTA park with its pins, access points and its OUTLINES from the same ky-*.geojson files Park Control uses,
   matched by the website's own kpc-bounds.js (run here in Node), each outline labelled official / approximate (KPC-drawn).
   Every other state: parks + pins + kind from data/parkinfo (no outlines yet: the key points at PAD-US tracts that the app can
   fetch when it has signal). Run from the repo root:  node .github/scripts/build_app_pack.js        (~1 min) */
const fs = require('fs'), path = require('path');
const ROOT = process.cwd(), OUT = path.join(ROOT, 'app', 'packs');
fs.mkdirSync(OUT, { recursive: true });

/* kpc-bounds.js wants a browser: give it just enough (fetch = read a file next to the page, window = here) */
global.window = global; global.navigator = { userAgent: 'node' }; global.document = { createElement: () => ({ style: {} }), body: { appendChild() {} } };
global.matchMedia = () => ({ matches: false }); global.URL = global.URL || {};
global.fetch = async (u, o) => { const f = path.join(ROOT, String(u).split('?')[0]); if (!fs.existsSync(f)) return { ok: false, status: 404, json: async () => ({}), text: async () => '' }; const txt = fs.readFileSync(f, 'utf8'); return { ok: true, status: 200, json: async () => JSON.parse(txt), text: async () => txt }; };
require(path.join(ROOT, 'kpc-bounds.js'));
const B = global.KPCB;

/* Douglas-Peucker in degrees: 0.00003° ≈ 3 m, keeps the shape and halves the bytes */
function rdp(pts, eps) {
  if (pts.length < 3) return pts;
  const [ax, ay] = pts[0], [bx, by] = pts[pts.length - 1]; let idx = 0, dmax = 0;
  const dx = bx - ax, dy = by - ay, L = dx * dx + dy * dy || 1e-18;
  for (let i = 1; i < pts.length - 1; i++) { const [px, py] = pts[i], t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / L)), d = Math.hypot(px - (ax + t * dx), py - (ay + t * dy)); if (d > dmax) { dmax = d; idx = i; } }
  if (dmax > eps) { const a = rdp(pts.slice(0, idx + 1), eps), b = rdp(pts.slice(idx), eps); return a.slice(0, -1).concat(b); }
  return [pts[0], pts[pts.length - 1]];
}
const r5 = v => Math.round(v * 1e5) / 1e5;
function simplify(g) {
  const ring = r => { const s = rdp(r, 0.00003).map(([x, y]) => [r5(x), r5(y)]); return s.length >= 4 ? s : null; };
  if (g.type === 'Polygon') { const rs = g.coordinates.map(ring).filter(Boolean); return rs.length ? { type: 'Polygon', coordinates: rs } : null; }
  if (g.type === 'MultiPolygon') { const ps = g.coordinates.map(p => p.map(ring).filter(Boolean)).filter(p => p.length); return ps.length ? { type: 'MultiPolygon', coordinates: ps } : null; }
  return null;
}
const sz = o => Buffer.byteLength(JSON.stringify(o));

(async () => {
  const index = { updated: new Date().toISOString().slice(0, 10), states: {} };
  /* ---- Kentucky, with outlines ---- */
  const KYD = JSON.parse(fs.readFileSync(path.join(ROOT, 'kpc-ky-data.json'), 'utf8'));
  await B.ky();
  const parks = [], outlines = {}; let nOut = 0, nApprox = 0;
  for (const p of KYD.parks) {
    parks.push({ ref: p.c, name: p.n, la: p.la, lo: p.lo, kind: p.t || '', co: p.co || '', web: p.web || '', off: p.off || '', camp: p.camp || '', ap: (p.ap || []).map(a => [r5(a[0]), r5(a[1]), a[2] || '']), kff: p.kff || [], sota: p.sota || [] });
    const feats = await B.kyFor(p.c);
    const list = [];
    for (const f of feats) { const g = simplify(f.geometry); if (!g) continue; const approx = !!(f._L.kpc || f._L.proc); list.push({ g, src: approx ? 'approx' : 'official', layer: f._L.name, agency: f._L.agency, note: f._L.note || '' }); if (approx) nApprox++; }
    if (list.length) { outlines[p.c] = list; nOut++; }
  }
  const kff = (KYD.kff || []).map(k => ({ ref: k.c, name: k.n, la: k.la, lo: k.lo, p: k.p || '' })), summits = (KYD.summits || []).map(x => ({ ref: x.c, name: x.n, la: x.la, lo: x.lo, ft: x.ft || 0 }));
  const ky = { state: 'KY', updated: index.updated, note: 'Outlines: official = the agency\'s own map file; approx = drawn by KPC from OpenStreetMap or the forest\'s outer line. Pins and access points are guides, not confirmed spots.', parks, outlines, kff, summits };
  fs.writeFileSync(path.join(OUT, 'US-KY.json'), JSON.stringify(ky));
  index.states.KY = { parks: parks.length, outlines: nOut, approx: nApprox, bytes: sz(ky) };
  console.log('KY', parks.length, 'parks,', nOut, 'with outlines (' + nApprox + ' approx),', (sz(ky) / 1e6).toFixed(2), 'MB');
  /* ---- every other state: parks + pins ---- */
  const dir = path.join(ROOT, 'data', 'parkinfo');
  for (const f of fs.readdirSync(dir).filter(x => /^US-[A-Z]{2}\.json$/.test(x)).sort()) {
    const j = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')), st = j.state;
    if (st === 'KY' || !j.parks) continue;
    const P = Object.entries(j.parks).map(([ref, a]) => ({ ref, name: a[0], web: a[1] || '', kind: a[2] || '', act: a[3] || '', acc: a[4] || '', la: a[5], lo: a[6], ap: [] })).filter(p => p.la && p.lo);
    const pack = { state: st, updated: j.updated || index.updated, site: j.stateSite || '', note: 'Pins only: no outlines on the phone yet for this state. With signal the app can fetch the official outline (USGS PAD-US) for a park the key knows.', parks: P, outlines: {} };
    fs.writeFileSync(path.join(OUT, 'US-' + st + '.json'), JSON.stringify(pack));
    index.states[st] = { parks: P.length, outlines: 0, approx: 0, bytes: sz(pack) };
  }
  fs.writeFileSync(path.join(OUT, 'index.json'), JSON.stringify(index));
  console.log(Object.keys(index.states).length, 'states in app/packs/index.json');
})().catch(e => { console.error(e); process.exit(1); });
