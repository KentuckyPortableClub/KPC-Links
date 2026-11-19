/* Builds the KPC APP's OFFLINE PARK PACKS (Fable, Oct 22) into app/packs/ (served by GitHub Pages, the app downloads one state at a time).
   Kentucky: every POTA park with its pins, access points and its OUTLINES from the same ky-*.geojson files Park Control uses,
   matched by the website's own kpc-bounds.js (run here in Node), each outline labelled official / approximate (OpenStreetMap outline, unofficial).
   Every other state: parks + pins + kind from data/parkinfo (no outlines yet: the key points at PAD-US tracts that the app can
   fetch when it has signal). Run from the repo root:  bash .github/scripts/kpc_overlay.sh && node .github/scripts/build_app_pack.js   (~1 min; the overlay lays in KPC-Data's parkinfo + access) */
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
  const ky = { state: 'KY', updated: index.updated, note: 'Outlines: official = the agency\'s own map file; approx = an OpenStreetMap outline (unofficial) or the forest\'s outer line. Pins and access points are guides, not confirmed spots.', parks, outlines, kff, summits };
  fs.writeFileSync(path.join(OUT, 'US-KY.json'), JSON.stringify(ky));
  index.states.KY = { parks: parks.length, outlines: nOut, approx: nApprox, bytes: sz(ky) };
  console.log('KY', parks.length, 'parks,', nOut, 'with outlines (' + nApprox + ' approx),', (sz(ky) / 1e6).toFixed(2), 'MB');
  /* ---- Nov 19 2026 (Brandon: WWFF and SOTA as options, per-state packs): every other state's pack also carries the WWFF (KFF) references
     and the SOTA summits in or near the state, from the copies the weekly bots already keep in KPC-Data (data/wwff/KFF.json =
     kpc_wwff_dir.py, data/sota/t/*.json = kpc_sota_dir.py; laid in by kpc_overlay.sh). RULES (listing only, nothing is decided for
     anyone): (1) WWFF = active KFF references; the state is the directory's own state field, else the reference's point inside a
     state outline (kpc-us-states.json). (2) SOTA = valid summits (the bot already drops ended ones) whose point is inside a state
     outline or within ~5 km of its edge (the outlines are coarse, so a summit on a border shows in BOTH states' packs rather than in
     neither). (3) Never paired with a park: the app shows them as their own program, never as a 2-fer. (4) A file missing = that
     part is left out of the packs (the parks still build). */
  const STB = (() => { try { return JSON.parse(fs.readFileSync(path.join(ROOT, 'kpc-us-states.json'), 'utf8')); } catch (e) { return []; } })();
  const STN = {}; STB.forEach(s => { STN[s.n.toUpperCase()] = s.a; STN[s.a] = s.a; });
  const ringIn = (x, y, r) => { let ins = false; for (let i = 0, j = r.length - 1; i < r.length; j = i++) { const xi = r[i][0], yi = r[i][1], xj = r[j][0], yj = r[j][1]; if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) ins = !ins; } return ins; };
  const segD = (x, y, a, b) => { const k = Math.cos(y * Math.PI / 180), ax = a[0] * k, bx = b[0] * k, px = x * k, dx = bx - ax, dy = b[1] - a[1], L = dx * dx + dy * dy || 1e-18, t = Math.max(0, Math.min(1, ((px - ax) * dx + (y - a[1]) * dy) / L)); return Math.hypot(px - (ax + t * dx), y - (a[1] + t * dy)); };
  const BBOX = STB.map(s => { let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9; s.p.forEach(pl => pl.forEach(r => r.forEach(([x, y]) => { x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }))); return { s, x0, x1, y0, y1 }; });
  const statesAt = (la, lo, buf) => { const out = []; for (const b of BBOX) { if (lo < b.x0 - buf * 1.5 || lo > b.x1 + buf * 1.5 || la < b.y0 - buf || la > b.y1 + buf) continue;
    let hit = b.s.p.some(pl => pl.length && ringIn(lo, la, pl[0]) && !pl.slice(1).some(h => ringIn(lo, la, h)));
    if (!hit && buf) hit = b.s.p.some(pl => pl.some(r => r.some((c, i) => i && segD(lo, la, r[i - 1], c) < buf)));
    if (hit) out.push(b.s.a); } return out; };
  const WW = {}, SO = {}; let nWw = 0, nSo = 0;
  try { for (const r of JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'wwff', 'KFF.json'), 'utf8'))) {
    const [ref, name, la, lo, web, st0] = r; if (!ref || !isFinite(la) || !isFinite(lo) || la === null) continue;
    let st = String(st0 || '').toUpperCase().replace(/^US-/, '').trim(); st = STN[st] || ''; if (!st) st = statesAt(la, lo, 0)[0] || ''; if (!st) continue;
    (WW[st] = WW[st] || []).push([ref, name || '', r5(la), r5(lo), web || '']); nWw++; } } catch (e) { console.log('WWFF list not read (' + e.message + '): packs built without it'); }
  try { const td = path.join(ROOT, 'data', 'sota', 't');
    for (const f of fs.readdirSync(td).filter(x => /^-?\d+_-?\d+\.json$/.test(x))) { const [ty, tx] = f.replace('.json', '').split('_').map(Number); if (ty < 17 || ty > 72 || tx < -180 || tx > -64) continue;
      for (const r of JSON.parse(fs.readFileSync(path.join(td, f), 'utf8'))) { const [code, name, ft, , la, lo, pts] = r; if (!code || !isFinite(la) || !isFinite(lo)) continue;
        const sts = statesAt(la, lo, 0.05); if (!sts.length) continue; nSo++; for (const st of sts) (SO[st] = SO[st] || []).push([code, name || '', r5(la), r5(lo), ft || 0, pts || 0]); } } } catch (e) { console.log('SOTA tiles not read (' + e.message + '): packs built without them'); }
  console.log('WWFF', nWw, 'references,', 'SOTA', nSo, 'summits placed by state');
  /* ---- every other state: parks + pins ---- */
  const dir = path.join(ROOT, 'data', 'parkinfo');
  /* Step B (Oct 27): data/parkinfo + data/access live in KPC-Data now: run  bash .github/scripts/kpc_overlay.sh  first (it lays them in) */
  if (!fs.existsSync(dir)) { console.log('data/parkinfo missing: run  bash .github/scripts/kpc_overlay.sh  first (Step B: it lives in KPC-Data). Kentucky pack done, other states skipped.'); }
  /* Oct 25 storage plan (chat 2): parkinfo files no longer carry 'updated'; the change date lives in data/status/kpc_state_links.json {changed:{'data/parkinfo/US-XX.json': 'YYYY-MM-DD'}} */
  let CHG = {}; try { CHG = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'status', 'kpc_state_links.json'), 'utf8')).changed || {}; } catch (e) {}
  for (const f of (fs.existsSync(dir) ? fs.readdirSync(dir) : []).filter(x => /^US-[A-Z]{2}\.json$/.test(x)).sort()) {
    const j = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')), st = j.state;
    if (st === 'KY' || !j.parks) continue;
    /* Oct 25 (HQ hand-off from chat 2): the state agencies' own parking / entrance / gate / trailhead points (data/access/US-XX.json,
       kpc_us_access.py, monthly) go in as each park's 'ap' [[lat, lon, label]] — the same shape Kentucky has — so NEXT PARK's 🧭 directions
       lead to a real lot or gate instead of POTA's pin. At most 12 per park, nearest the pin first. */
    let ACC = {}; try { ACC = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'access', 'US-' + st + '.json'), 'utf8')).parks || {}; } catch (e) {}
    const near = (p, L) => L.map(a => [r5(+a[0]), r5(+a[1]), String(a[2] || '').slice(0, 40)]).filter(a => isFinite(a[0]) && isFinite(a[1])).sort((a, b) => Math.hypot(a[0] - p.la, a[1] - p.lo) - Math.hypot(b[0] - p.la, b[1] - p.lo)).slice(0, 12);
    const P = Object.entries(j.parks).map(([ref, a]) => ({ ref, name: a[0], web: a[1] || '', kind: a[2] || '', act: a[3] || '', acc: a[4] || '', la: a[5], lo: a[6], ap: [] })).filter(p => p.la && p.lo);
    let nAp = 0; P.forEach(p => { if (ACC[p.ref] && ACC[p.ref].length) { p.ap = near(p, ACC[p.ref]); nAp++; } });
    const pack = { state: st, updated: CHG['data/parkinfo/' + f] || j.updated || index.updated, site: j.stateSite || '', note: 'Pins + the agency\'s own parking / entrance points (where it publishes them). No outlines on the phone yet for this state. With signal the app can fetch the official outline (USGS PAD-US) for a park the key knows.', parks: P, outlines: {}, wwff: (WW[st] || []).sort(), sota: (SO[st] || []).sort(), others: 'wwff [ref, name, lat, lon, web] · sota [code, name, lat, lon, feet, points]: their own programs, never a 2-fer' };
    fs.writeFileSync(path.join(OUT, 'US-' + st + '.json'), JSON.stringify(pack));
    index.states[st] = { parks: P.length, outlines: 0, approx: 0, access: nAp, wwff: pack.wwff.length, sota: pack.sota.length, bytes: sz(pack) };
  }
  fs.writeFileSync(path.join(OUT, 'index.json'), JSON.stringify(index));
  console.log(Object.keys(index.states).length, 'states in app/packs/index.json');
})().catch(e => { console.error(e); process.exit(1); });
