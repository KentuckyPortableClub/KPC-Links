/* Nov 11 2026 (KPC owner): the hand map placer's maths (kpc-map-placer-math.js), in node, no browser, no network.
   - exact recovery of a known similarity from synthetic pairs; residual and leave-one-out numbers;
   - points on a line and bunched points refused; a mirrored fit refused; 2 points refused; pixel <-> lat/lon round trip;
   - every case of the SHARED fixture tests/fixtures/hand-place-cases.json gives the stored numbers. KPC-Data's checker
     (kpc_hand_place.py) is held to the same stored numbers by its own test, so the two languages agree.
   node tests/map_placer_math_nov11.js           (check)
   node tests/map_placer_math_nov11.js --write   (rebuild the fixture's expected numbers from this module; review the diff) */
'use strict';
const fs = require('fs'), path = require('path');
const M = require(path.join(__dirname, '..', 'kpc-map-placer-math.js'));
const FIX = path.join(__dirname, 'fixtures', 'hand-place-cases.json');
let fails = 0; const check = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
const near = (a, b, t) => Math.abs(a - b) <= t;

/* ---- the synthetic park: a known picture -> ground similarity around a pin ---- */
const PIN = [37.65, -84.45];
const Z = { a: 1.5 * Math.cos(15 * Math.PI / 180), b: 1.5 * Math.sin(15 * Math.PI / 180) };
const T0 = { a: Z.a, b: Z.b, tx: 0, ty: 0 };
{ const m = M.applySim(T0, 600, 450); T0.tx = 30 - m[0]; T0.ty = -20 - m[1]; }   // picture pixel (600, 450) sits 30 m east, 20 m south of the pin
const ll = (x, y) => { const g = M.pxToLatLon(T0, PIN, x, y); return [Math.round(g[0] * 1e7) / 1e7, Math.round(g[1] * 1e7) / 1e7]; };
const pair = (x, y, dx, dy, layer) => ({ px: [x, y], ll: ll(x + (dx || 0), y + (dy || 0)), layer: layer || 'usgs-topo' });
const RING = [[420, 300], [780, 280], [860, 520], [700, 690], [430, 640], [380, 470]];
const CASES = {
  exact: { pairs: [pair(150, 120), pair(1050, 160), pair(1000, 800), pair(200, 760), pair(640, 430)], shape: { kind: 'area', px: RING } },
  noisy: { pairs: [pair(150, 120, 3, -2), pair(1050, 160, -2, 1), pair(1000, 800, 1, 3), pair(200, 760, -3, -1), pair(640, 430, 2, 2)], shape: { kind: 'area', px: RING } },
  one_bad: { pairs: [pair(150, 120), pair(1050, 160), pair(1000, 800), pair(200, 760, 90, -60)], shape: { kind: 'area', px: RING } },
  on_a_line: { pairs: [pair(100, 100), pair(400, 104), pair(700, 101), pair(1000, 103)], shape: { kind: 'area', px: RING } },
  bunched: { pairs: [pair(600, 420), pair(640, 430), pair(620, 470), pair(660, 460)], shape: { kind: 'area', px: RING } },
  mirrored: { pairs: [[150, 120], [1050, 160], [1000, 800], [200, 760]].map(p => ({ px: [1200 - p[0], p[1]], ll: ll(p[0], p[1]), layer: 'usgs-topo' })), shape: { kind: 'area', px: RING } },
  two: { pairs: [pair(150, 120), pair(1050, 160)], shape: { kind: 'area', px: RING } },
  osm_point: { pairs: [pair(150, 120), pair(1050, 160), pair(1000, 800), pair(200, 760, 0, 0, 'osm')], shape: { kind: 'area', px: RING } },
  pin_far: { pin: [PIN[0] + 0.03, PIN[1]], pairs: [pair(150, 120), pair(1050, 160), pair(1000, 800), pair(200, 760)], shape: { kind: 'area', px: RING } },   // the POTA pin 3.3 km north of the land
  trail: { pairs: [pair(150, 120), pair(1050, 160), pair(1000, 800), pair(200, 760)], shape: { kind: 'trail', px: [[300, 600], [500, 450], [700, 480], [900, 300]] } }
};
function run(c) {
  const pin = c.pin || PIN, fit = c.pairs.length >= 2 ? M.fitPairs(c.pairs, pin) : null;
  const out = { n: c.pairs.length };
  if (fit) {
    const pl = M.placeShape(fit.T, pin, c.shape.px, c.shape.kind);
    Object.assign(out, { z: [fit.T.a, fit.T.b], t: [fit.T.tx, fit.T.ty], rms: fit.rms, residuals: fit.residuals, loo: fit.loo, loo_rms: fit.loo_rms, loo_max: fit.loo_max,
      scale: fit.scale_m_per_px, rotation_deg: fit.rotation_deg, affine_det_sign: fit.affine ? Math.sign(fit.affine.det) : 0, stretch: fit.affine ? fit.affine.stretch : null, spread: fit.spread,
      lonlat: pl.lonlat, area_acres: pl.area_acres, length_km: pl.length_km, pin_dist_m: pl.pin_dist_m });
  }
  out.gates = M.gates(fit, c.shape, c.pairs.map(q => q.layer), pin).map(g => g.id + ':' + (g.pass ? 'pass' : 'fail'));
  return out;
}

if (process.argv.includes('--write')) {
  const doc = { about: 'Shared fixture of the hand map placer (KPC-Links kpc-map-placer-math.js and KPC-Data kpc_hand_place.py must both give these numbers). ' +
    'Inputs are synthetic: a picture placed on the ground by a known similarity (1.5 m per pixel, turned 15 degrees) around a made-up pin. Built by tests/map_placer_math_nov11.js --write.',
    pin: PIN, limits: M.LIMITS, basemaps: Object.keys(M.BASEMAPS), cases: {} };
  for (const [k, c] of Object.entries(CASES)) doc.cases[k] = { input: c, expected: run(c) };
  fs.writeFileSync(FIX, JSON.stringify(doc, null, 1) + '\n'); console.log('wrote ' + FIX); process.exit(0);
}

/* ---- 1. exact recovery, residuals, leave-one-out ---- */
const ex = M.fitPairs(CASES.exact.pairs, PIN);
check(near(ex.T.a, Z.a, 5e-5) && near(ex.T.b, Z.b, 5e-5) && near(ex.T.tx, T0.tx, 0.02) && near(ex.T.ty, T0.ty, 0.02), 'a known similarity is recovered from 5 exact pairs (lat / lon rounded to 1e-7)');
check(ex.rms < 0.02 && ex.loo_rms < 0.03, 'exact pairs: RMS ' + ex.rms.toFixed(4) + ' m, leave-one-out ' + ex.loo_rms.toFixed(4) + ' m (only the 1e-7 degree rounding)');
check(near(ex.scale_m_per_px, 1.5, 5e-5) && near(ex.rotation_deg, 15, 0.002), 'scale 1.5 m/px and turn 15 degrees read back');
const nz = M.fitPairs(CASES.noisy.pairs, PIN);
const resid = (P, Q, T) => P.map((p, i) => { const m = M.applySim(T, p[0], p[1]); return Math.hypot(m[0] - Q[i][0], m[1] - Q[i][1]); });
check(nz.residuals.every((r, i) => near(r, resid(nz.P, nz.Q, nz.T)[i], 1e-9)) && near(nz.rms, Math.sqrt(nz.residuals.reduce((s, r) => s + r * r, 0) / 5), 1e-12), 'residuals are each pair\'s miss under the fit, RMS their root mean square');
const loo2 = M.fitSimilarity(nz.P.slice(1), nz.Q.slice(1)), m2 = M.applySim(loo2, nz.P[0][0], nz.P[0][1]);
check(near(nz.loo[0], Math.hypot(m2[0] - nz.Q[0][0], m2[1] - nz.Q[0][1]), 1e-9), 'leave-one-out: point 1 measured against a fit of the other 4');
check(nz.rms > 2 && nz.rms < 8 && nz.loo_rms > nz.rms, 'a few pixels of click error: RMS ' + nz.rms.toFixed(2) + ' m, leave-one-out ' + nz.loo_rms.toFixed(2) + ' m (larger, as it should be)');
const bad = M.fitPairs(CASES.one_bad.pairs, PIN);
check(bad.loo_max > 50 && M.gates(bad, CASES.one_bad.shape, ['usgs-topo', 'usgs-topo', 'usgs-topo', 'usgs-topo'], PIN).some(g => g.id === 'leave_one_out_worst' && !g.pass), 'one pair 160 m off: the worst leave-one-out miss (' + bad.loo_max.toFixed(0) + ' m) fails the 50 m gate');

/* ---- 2. refusals ---- */
const G = k => run(CASES[k]).gates;
check(G('exact').every(g => /:pass$/.test(g)), 'the exact case passes every page gate: ' + G('exact').join(' '));
check(G('on_a_line').includes('not_on_a_line:fail'), 'points nearly on one line are refused');
check(G('bunched').includes('points_cover_shape:fail') && G('bunched').includes('no_far_extrapolation:fail'), 'bunched points are refused (they do not span the shape; the shape is far outside them)');
check(G('mirrored').includes('not_mirrored:fail'), 'a mirrored set of pairs is refused (the affine check turns the picture over)');
check(G('two').includes('points:fail') && run(CASES.two).loo === null, '2 points are refused (no leave-one-out possible)');
check(G('osm_point').includes('government_basemap:fail'), 'a point clicked on OpenStreetMap is refused');
check(G('pin_far').includes('pin:fail'), 'a shape 3 km from the POTA pin is refused (pin never moved)');
check(G('trail').every(g => /:pass$/.test(g)) && run(CASES.trail).length_km > 0, 'a trail line passes and has a length');
check(M.fitPairs([CASES.exact.pairs[0]], PIN) === null, 'one point: no fit');

/* ---- 3. round trips ---- */
let worst = 0;
for (const [x, y] of [[0, 0], [1200, 0], [1200, 900], [0, 900], [600, 450]]) { const g = M.pxToLatLon(ex.T, PIN, x, y), p = M.latLonToPx(ex.T, PIN, g[0], g[1]); worst = Math.max(worst, Math.hypot(p[0] - x, p[1] - y)); }
check(worst < 1e-6, 'pixel -> lat / lon -> pixel round trip (worst ' + worst.toExponential(1) + ' px)');
let tw = 0; for (const d of [[0.01, 0.02], [-0.05, 0.03], [0.1, -0.1]]) { const e = M.tmFwd(PIN[0], PIN[1], PIN[0] + d[0], PIN[1] + d[1]), b = M.tmInv(PIN[0], PIN[1], e[0], e[1]); tw = Math.max(tw, Math.abs(b[0] - PIN[0] - d[0]), Math.abs(b[1] - PIN[1] - d[1])); }
check(tw < 1e-11, 'transverse Mercator round trip (worst ' + tw.toExponential(1) + ' degrees)');
const a = M.tmFwd(PIN[0], PIN[1], PIN[0], PIN[1] + 0.001), Nn = 6378137 / Math.sqrt(1 - (1 / 298.257222101) * (2 - 1 / 298.257222101) * Math.sin(PIN[0] * Math.PI / 180) ** 2);
check(near(a[0], Nn * Math.cos(PIN[0] * Math.PI / 180) * 0.001 * Math.PI / 180, 1e-6), 'a small step east is N cos(lat) dlon metres (GRS80)');
check(M.canonical({ b: 1, a: [2, { d: 1, c: 'x' }] }) === '{"a":[2,{"c":"x","d":1}],"b":1}', 'canonical JSON (sorted keys, no spaces) for the click-set fingerprint');

/* ---- 4. the shared fixture ---- */
const doc = JSON.parse(fs.readFileSync(FIX, 'utf8'));
const same = (a, b, t) => { if (a === null || b === null) return a === b; if (Array.isArray(a)) return Array.isArray(b) && a.length === b.length && a.every((v, i) => same(v, b[i], t)); if (typeof a === 'number') return typeof b === 'number' && Math.abs(a - b) <= t; return a === b; };
for (const [k, c] of Object.entries(doc.cases)) {
  const got = run(c.input), exp = c.expected;
  const keys = Object.keys(exp).filter(x => !same(got[x], exp[x], x === 'lonlat' ? 0 : 1e-9));
  check(!keys.length, 'fixture case ' + k + ' gives the stored numbers' + (keys.length ? ' (differs: ' + keys.join(', ') + ')' : ''));
}
check(JSON.stringify(doc.limits) === JSON.stringify(M.LIMITS), 'the fixture records this module\'s gate numbers (KPC-Data compares them with the tracer\'s)');
console.log(fails ? 'SOME FAILED' : 'ALL PASS');
process.exit(fails ? 1 : 0);
