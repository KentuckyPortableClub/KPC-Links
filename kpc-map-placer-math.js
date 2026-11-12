/* KPC MAP PLACER: THE MATHS (Nov 11 2026, KPC owner, 2026-11-11). No DOM: the page (kpc-map-placer.js) and node tests use it, and
   KPC-Data .github/scripts/draft/kpc_hand_place.py does the same sums in Python (the checker never trusts the numbers a page wrote).

   Frames (the same as the picture tracer, kpc_trace_picture.py):
   - picture pixels: x right, y DOWN, in the saved picture's own pixel size;
   - ground metres: a transverse Mercator centred on the POTA pin (GRS80, scale 1), east / north, the tracer's LocalProj frame.
     Here it is the Krueger series to n^6 (Karney 2011); PROJ's tmerc gives the same numbers to well under a millimetre at park sizes.
   - the fit: a SIMILARITY (scale, turn, shift; never mirrored), in the tracer's complex form m = z * p + t with p = x - i*y
     (picture y turned up), exactly like its fit_similarity_c. A full affine is fitted only as a check (mirror and stretch).

   Exported as window.KPCPlaceMath in a page and module.exports in node. */
(function (root) {
  'use strict';
  var VERSION = 'kpc-map-placer-math 1.0 (2026-11-11)';
  /* The gate numbers. The tracer's own (MAX_FIT_M, MIN_POINTS, PIN_MAX_OUTSIDE_M, SIMPLIFY_M, the GeoPDF scale range and skew limit) are
     copied here only so the page can show a preview; the KPC-Data checker imports the real ones from the tracer, and a test compares
     the two lists. The HAND_ ones exist only for hand points (see the checker). */
  var LIMITS = {
    MAX_FIT_M: 50.0, MIN_POINTS: 3, PIN_MAX_OUTSIDE_M: 1000, SIMPLIFY_M: 3.0, SCALE_RANGE: [0.05, 500.0], SKEW_MAX: 0.15,
    HAND_MIN_POINTS: 4, HAND_COLLINEAR_MIN: 0.15, HAND_SPREAD_MIN: 0.5, HAND_EXTRAP_MAX: 0.5, HAND_ROT_FLAG_DEG: 25
  };
  /* The real-map layers a point may be clicked on: government maps the site already shows. Anything else (OpenStreetMap, Esri) is
     for looking only: the tracer's Rule 6 says the fixed points come from a public government basemap, never OpenStreetMap or Google. */
  var BASEMAPS = {
    'usgs-topo': { name: 'USGS The National Map: Topo', url: 'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}' },
    'usgs-imagery-topo': { name: 'USGS The National Map: Imagery Topo', url: 'https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryTopo/MapServer/tile/{z}/{y}/{x}' }
  };
  var ACRE_M2 = 4046.86;   // the tracer's acres divisor

  /* ---------------------------------------------------------------- transverse Mercator (GRS80, k0 = 1, centred on the pin) */
  var A_ = 6378137.0, F_ = 1 / 298.257222101, N_ = F_ / (2 - F_), E_ = Math.sqrt(F_ * (2 - F_));
  var n = N_, n2 = n * n, n3 = n2 * n, n4 = n3 * n, n5 = n4 * n, n6 = n5 * n;
  var AA = A_ / (1 + n) * (1 + n2 / 4 + n4 / 64 + n6 / 256);
  var ALPHA = [0,
    n / 2 - 2 * n2 / 3 + 5 * n3 / 16 + 41 * n4 / 180 - 127 * n5 / 288 + 7891 * n6 / 37800,
    13 * n2 / 48 - 3 * n3 / 5 + 557 * n4 / 1440 + 281 * n5 / 630 - 1983433 * n6 / 1935360,
    61 * n3 / 240 - 103 * n4 / 140 + 15061 * n5 / 26880 + 167603 * n6 / 181440,
    49561 * n4 / 161280 - 179 * n5 / 168 + 6601661 * n6 / 7257600,
    34729 * n5 / 80640 - 3418889 * n6 / 1995840,
    212378941 * n6 / 319334400];
  var BETA = [0,
    n / 2 - 2 * n2 / 3 + 37 * n3 / 96 - n4 / 360 - 81 * n5 / 512 + 96199 * n6 / 604800,
    n2 / 48 + n3 / 15 - 437 * n4 / 1440 + 46 * n5 / 105 - 1118711 * n6 / 3870720,
    17 * n3 / 480 - 37 * n4 / 840 - 209 * n5 / 4480 + 5569 * n6 / 90720,
    4397 * n4 / 161280 - 11 * n5 / 504 - 830251 * n6 / 7257600,
    4583 * n5 / 161280 - 108847 * n6 / 3991680,
    20648693 * n6 / 638668800];
  var D2R = Math.PI / 180;
  function atanh(x) { return 0.5 * Math.log((1 + x) / (1 - x)); }
  function xiEta(lat, dlon) {
    var phi = lat * D2R, lam = dlon * D2R, s = Math.sin(phi);
    var t = Math.sinh(atanh(s) - E_ * atanh(E_ * s));
    var xi1 = Math.atan2(t, Math.cos(lam)), eta1 = atanh(Math.sin(lam) / Math.sqrt(1 + t * t));
    var xi = xi1, eta = eta1;
    for (var j = 1; j <= 6; j++) { xi += ALPHA[j] * Math.sin(2 * j * xi1) * Math.cosh(2 * j * eta1); eta += ALPHA[j] * Math.cos(2 * j * xi1) * Math.sinh(2 * j * eta1); }
    return [xi, eta];
  }
  /** lat, lon (degrees) -> [east, north] metres in the frame centred on (lat0, lon0). */
  function tmFwd(lat0, lon0, lat, lon) {
    var o = xiEta(lat0, 0), p = xiEta(lat, lon - lon0);
    return [AA * p[1], AA * (p[0] - o[0])];
  }
  /** [east, north] metres -> [lat, lon] degrees. */
  function tmInv(lat0, lon0, x, y) {
    var o = xiEta(lat0, 0), xi = y / AA + o[0], eta = x / AA, xi1 = xi, eta1 = eta;
    for (var j = 1; j <= 6; j++) { xi1 -= BETA[j] * Math.sin(2 * j * xi) * Math.cosh(2 * j * eta); eta1 -= BETA[j] * Math.cos(2 * j * xi) * Math.sinh(2 * j * eta); }
    var tau1 = Math.sin(xi1) / Math.sqrt(Math.sinh(eta1) * Math.sinh(eta1) + Math.cos(xi1) * Math.cos(xi1));
    var lam = Math.atan2(Math.sinh(eta1), Math.cos(xi1)), tau = tau1;
    for (var k = 0; k < 8; k++) {   // Newton for tau = tan(phi) from the conformal tau1 (Karney 2011, eqs 7-9)
      var sig = Math.sinh(E_ * atanh(E_ * tau / Math.sqrt(1 + tau * tau)));
      var t1 = tau * Math.sqrt(1 + sig * sig) - sig * Math.sqrt(1 + tau * tau);
      var dt = (tau1 - t1) / Math.sqrt(1 + t1 * t1) * (1 + (1 - E_ * E_) * tau * tau) / ((1 - E_ * E_) * Math.sqrt(1 + tau * tau));
      tau += dt; if (Math.abs(dt) < 1e-15) break;
    }
    return [Math.atan(tau) / D2R, lon0 + lam / D2R];
  }

  /* ---------------------------------------------------------------- the similarity fit (the tracer's fit_similarity_c) */
  /** P: [[x, y] picture px], Q: [[east, north] m]. Returns {a, b, tx, ty} with z = a + ib, t = tx + i ty, or null. */
  function fitSimilarity(P, Q) {
    var k = P.length; if (k < 2 || Q.length !== k) return null;
    var pr = 0, pi = 0, qr = 0, qi = 0, i;
    for (i = 0; i < k; i++) { pr += P[i][0]; pi += -P[i][1]; qr += Q[i][0]; qi += Q[i][1]; }
    pr /= k; pi /= k; qr /= k; qi /= k;
    var den = 0, nr = 0, ni = 0;
    for (i = 0; i < k; i++) {
      var ar = P[i][0] - pr, ai = -P[i][1] - pi, br = Q[i][0] - qr, bi = Q[i][1] - qi;
      den += ar * ar + ai * ai; nr += ar * br + ai * bi; ni += ar * bi - ai * br;   // conj(a) * b
    }
    if (!(den > 0)) return null;
    var a = nr / den, b = ni / den;
    return { a: a, b: b, tx: qr - (a * pr - b * pi), ty: qi - (a * pi + b * pr) };
  }
  function applySim(T, x, y) { var pr = x, pi = -y; return [T.a * pr - T.b * pi + T.tx, T.a * pi + T.b * pr + T.ty]; }
  function invSim(T, e, nn) { var r = e - T.tx, s = nn - T.ty, d = T.a * T.a + T.b * T.b; var pr = (T.a * r + T.b * s) / d, pi = (T.a * s - T.b * r) / d; return [pr, -pi]; }
  function simScale(T) { return Math.hypot(T.a, T.b); }
  /** The picture's 'up' turned this many degrees counter-clockwise from north (west of north); negative = east of north. */
  function simRotDeg(T) { return Math.atan2(T.b, T.a) / D2R; }

  /** Full affine [east, north] = A [x, -y] + c, least squares; only a check (mirror, stretch). Needs 3+ points not on a line. */
  function fitAffine(P, Q) {
    var k = P.length; if (k < 3) return null;
    var mx = 0, my = 0, me = 0, mn = 0, i;
    for (i = 0; i < k; i++) { mx += P[i][0]; my += -P[i][1]; me += Q[i][0]; mn += Q[i][1]; }
    mx /= k; my /= k; me /= k; mn /= k;
    var sxx = 0, sxy = 0, syy = 0, sxe = 0, sye = 0, sxn = 0, syn = 0;
    for (i = 0; i < k; i++) {
      var x = P[i][0] - mx, y = -P[i][1] - my, e = Q[i][0] - me, nn = Q[i][1] - mn;
      sxx += x * x; sxy += x * y; syy += y * y; sxe += x * e; sye += y * e; sxn += x * nn; syn += y * nn;
    }
    var det = sxx * syy - sxy * sxy; if (!(Math.abs(det) > 1e-9 * Math.max(1, sxx * syy))) return null;
    var a11 = (syy * sxe - sxy * sye) / det, a12 = (sxx * sye - sxy * sxe) / det;
    var a21 = (syy * sxn - sxy * syn) / det, a22 = (sxx * syn - sxy * sxn) / det;
    var dA = a11 * a22 - a12 * a21;
    // singular values of [[a11, a12], [a21, a22]]
    var s = a11 * a11 + a12 * a12 + a21 * a21 + a22 * a22, q = Math.sqrt(Math.max(0, s * s - 4 * dA * dA));
    var s1 = Math.sqrt((s + q) / 2), s2 = Math.sqrt(Math.max(0, (s - q) / 2));
    return { A: [[a11, a12], [a21, a22]], det: dA, s1: s1, s2: s2, stretch: s1 > 0 ? (s1 - s2) / s1 : 1 };
  }

  /** Smallest / largest singular value of the centred picture points (the tracer's choose_model flags < 0.08 as 'nearly collinear'). */
  function spreadRatio(P) {
    var k = P.length; if (k < 2) return 0;
    var mx = 0, my = 0, i; for (i = 0; i < k; i++) { mx += P[i][0]; my += P[i][1]; } mx /= k; my /= k;
    var a = 0, b = 0, c = 0; for (i = 0; i < k; i++) { var x = P[i][0] - mx, y = P[i][1] - my; a += x * x; b += x * y; c += y * y; }
    var tr = a + c, q = Math.sqrt(Math.max(0, (a - c) * (a - c) + 4 * b * b)), l1 = (tr + q) / 2, l2 = Math.max(0, (tr - q) / 2);
    return l1 > 0 ? Math.sqrt(l2 / l1) : 0;
  }
  function bbox(P) { var b = [Infinity, Infinity, -Infinity, -Infinity]; P.forEach(function (p) { b[0] = Math.min(b[0], p[0]); b[1] = Math.min(b[1], p[1]); b[2] = Math.max(b[2], p[0]); b[3] = Math.max(b[3], p[1]); }); return b; }
  function bdiag(b) { return Math.hypot(b[2] - b[0], b[3] - b[1]); }
  function distToBox(p, b) { var dx = Math.max(b[0] - p[0], 0, p[0] - b[2]), dy = Math.max(b[1] - p[1], 0, p[1] - b[3]); return Math.hypot(dx, dy); }

  /** Fit + residuals + leave-one-out for point pairs [{px: [x, y], ll: [lat, lon]}] around the pin [lat, lon]. */
  function fitPairs(pairs, pin) {
    var P = pairs.map(function (q) { return [+q.px[0], +q.px[1]]; });
    var Q = pairs.map(function (q) { return tmFwd(pin[0], pin[1], +q.ll[0], +q.ll[1]); });
    var T = fitSimilarity(P, Q); if (!T) return null;
    var res = P.map(function (p, i) { var m = applySim(T, p[0], p[1]); return Math.hypot(m[0] - Q[i][0], m[1] - Q[i][1]); });
    var rms = Math.sqrt(res.reduce(function (s, r) { return s + r * r; }, 0) / res.length);
    var loo = null;
    if (P.length >= 3) {
      loo = P.map(function (p, i) {
        var T2 = fitSimilarity(P.filter(function (_, j) { return j !== i; }), Q.filter(function (_, j) { return j !== i; }));
        if (!T2) return Infinity;
        var m = applySim(T2, p[0], p[1]); return Math.hypot(m[0] - Q[i][0], m[1] - Q[i][1]);
      });
    }
    var looRms = loo ? Math.sqrt(loo.reduce(function (s, r) { return s + r * r; }, 0) / loo.length) : null;
    return { T: T, P: P, Q: Q, residuals: res, rms: rms, loo: loo, loo_rms: looRms, loo_max: loo ? Math.max.apply(null, loo) : null,
      scale_m_per_px: simScale(T), rotation_deg: simRotDeg(T), affine: fitAffine(P, Q), spread: spreadRatio(P) };
  }

  /* ---------------------------------------------------------------- shapes */
  function segX(a, b, c, d) {   // proper or touching crossing of segments ab and cd
    function o(p, q, r) { var v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]); return Math.abs(v) < 1e-12 ? 0 : (v > 0 ? 1 : -1); }
    function on(p, q, r) { return Math.min(p[0], r[0]) - 1e-12 <= q[0] && q[0] <= Math.max(p[0], r[0]) + 1e-12 && Math.min(p[1], r[1]) - 1e-12 <= q[1] && q[1] <= Math.max(p[1], r[1]) + 1e-12; }
    var o1 = o(a, b, c), o2 = o(a, b, d), o3 = o(c, d, a), o4 = o(c, d, b);
    if (o1 !== o2 && o3 !== o4) return true;
    return (o1 === 0 && on(a, c, b)) || (o2 === 0 && on(a, d, b)) || (o3 === 0 && on(c, a, d)) || (o4 === 0 && on(c, b, d));
  }
  /** True when a shape crosses itself. closed: the last vertex joins the first. */
  function selfCrosses(pts, closed) {
    var k = pts.length, m = closed ? k : k - 1;
    for (var i = 0; i < m; i++) for (var j = i + 1; j < m; j++) {
      if (j === i + 1 || (closed && i === 0 && j === m - 1)) continue;   // neighbours share a vertex
      if (segX(pts[i], pts[(i + 1) % k], pts[j], pts[(j + 1) % k])) return true;
    }
    return false;
  }
  /** Douglas-Peucker (tolerance in the points' own units); a closed ring keeps its first vertex. */
  function simplify(pts, tol, closed) {
    var line = closed ? pts.concat([pts[0]]) : pts.slice();
    if (line.length < 3) return pts.slice();
    var keep = new Array(line.length).fill(false); keep[0] = keep[line.length - 1] = true;
    var stack = [[0, line.length - 1]];
    while (stack.length) {
      var s = stack.pop(), a = line[s[0]], b = line[s[1]], best = -1, bi = -1;
      for (var i = s[0] + 1; i < s[1]; i++) { var d = segDist(line[i], a, b); if (d > best) { best = d; bi = i; } }
      if (best > tol) { keep[bi] = true; stack.push([s[0], bi]); stack.push([bi, s[1]]); }
    }
    var out = line.filter(function (_, i) { return keep[i]; });
    if (closed) out.pop();
    return (closed && out.length < 3) || out.length < 2 ? pts.slice() : out;
  }
  function segDist(p, a, b) {
    var dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy, t = L > 0 ? ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L : 0;
    t = Math.max(0, Math.min(1, t)); return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy);
  }
  function inside(p, ring) {
    var c = false; for (var i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      var a = ring[i], b = ring[j];
      if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]) + a[0]) c = !c;
    } return c;
  }
  function shoelace(ring) { var s = 0; for (var i = 0, j = ring.length - 1; i < ring.length; j = i++) s += (ring[j][0] + ring[i][0]) * (ring[j][1] - ring[i][1]); return Math.abs(s) / 2; }
  /** Distance (m) from the pin (0, 0) to the shape: 0 inside an area. */
  function pinDistance(M, closed) {
    if (closed && inside([0, 0], M)) return 0;
    var best = Infinity, k = M.length, m = closed ? k : k - 1;
    for (var i = 0; i < m; i++) best = Math.min(best, segDist([0, 0], M[i], M[(i + 1) % k]));
    return best;
  }
  function round7(v) { return Math.round(v * 1e7) / 1e7; }

  /** Picture shape -> ground: {metres (simplified), lonlat ring / line, area_acres, length_km, pin_dist_m, crosses}. kind 'area' | 'line'. */
  function placeShape(T, pin, shapePx, kind) {
    var closed = kind === 'area';
    var M0 = shapePx.map(function (p) { return applySim(T, +p[0], +p[1]); });
    var M = simplify(M0, LIMITS.SIMPLIFY_M, closed);
    var ll = M.map(function (m) { var g = tmInv(pin[0], pin[1], m[0], m[1]); return [round7(g[1]), round7(g[0])]; });
    if (closed) ll.push(ll[0].slice());
    var len = 0; for (var i = 0; i < M.length - (closed ? 0 : 1); i++) len += Math.hypot(M[(i + 1) % M.length][0] - M[i][0], M[(i + 1) % M.length][1] - M[i][1]);
    return { metres: M, lonlat: ll, area_acres: closed ? shoelace(M) / ACRE_M2 : null, length_km: closed ? null : len / 1000,
      pin_dist_m: pinDistance(M, closed), crosses: selfCrosses(M, closed), n_in: M0.length, n_out: M.length };
  }

  /** Every hand gate the page can judge, in plain words. fit = fitPairs(...); shape = {px: [[x, y]...], kind} or null; layers = the
      base-layer id each real-map point was clicked on. The checker (KPC-Data) repeats these and adds the row, size and edge gates. */
  function gates(fit, shape, layers, pin) {
    var L = LIMITS, out = [], g = function (id, pass, why) { out.push({ id: id, pass: !!pass, why: why }); };
    var nPts = fit ? fit.P.length : 0;
    g('points', nPts >= L.HAND_MIN_POINTS && nPts >= L.MIN_POINTS, nPts + ' point pair(s); hand placements need at least ' + L.HAND_MIN_POINTS);
    if (!fit) return out;
    g('fit', fit.rms < L.MAX_FIT_M, 'fit error (RMS) ' + fit.rms.toFixed(1) + ' m; must be under ' + L.MAX_FIT_M + ' m');
    g('leave_one_out', fit.loo_rms !== null && fit.loo_rms < L.MAX_FIT_M, 'leave-one-out error (RMS) ' + (fit.loo_rms === null ? 'n/a' : fit.loo_rms.toFixed(1) + ' m') + '; must be under ' + L.MAX_FIT_M + ' m');
    g('leave_one_out_worst', fit.loo_max !== null && fit.loo_max < L.MAX_FIT_M, 'worst single point left out misses by ' + (fit.loo_max === null ? 'n/a' : fit.loo_max.toFixed(1) + ' m') + '; must be under ' + L.MAX_FIT_M + ' m');
    g('not_on_a_line', fit.spread >= L.HAND_COLLINEAR_MIN, 'the points spread ' + fit.spread.toFixed(2) + ' across their line (need ' + L.HAND_COLLINEAR_MIN + '): points nearly on one line cannot fix the turn');
    var af = fit.affine;
    g('not_mirrored', !!af && af.det > 0, af ? (af.det > 0 ? 'the points keep the picture the right way round' : 'the points only fit a MIRRORED picture: a pair is swapped or wrong') : 'cannot check: points on a line');
    g('not_stretched', !!af && af.stretch <= L.SKEW_MAX, af ? 'the points stretch the picture ' + (100 * af.stretch).toFixed(1) + '% one way more than the other (limit ' + (100 * L.SKEW_MAX) + '%)' : 'cannot check: points on a line');
    g('scale', fit.scale_m_per_px >= L.SCALE_RANGE[0] && fit.scale_m_per_px <= L.SCALE_RANGE[1], 'scale ' + fit.scale_m_per_px.toFixed(3) + ' m per picture pixel (plausible ' + L.SCALE_RANGE[0] + ' to ' + L.SCALE_RANGE[1] + ')');
    var bad = (layers || []).filter(function (id) { return !BASEMAPS[id]; });
    g('government_basemap', (layers || []).length === nPts && !bad.length, bad.length ? bad.length + ' point(s) were clicked on a map that is not a government basemap' : 'every point was clicked on a USGS map');
    if (shape && shape.px && shape.px.length) {
      var sb = bbox(shape.px), pb = bbox(fit.P), sd = bdiag(sb), pd = bdiag(pb);
      var worst = Math.max.apply(null, shape.px.map(function (p) { return distToBox(p, pb); }));
      g('points_cover_shape', sd > 0 && pd / sd >= L.HAND_SPREAD_MIN, 'the points span ' + (sd > 0 ? (100 * pd / sd).toFixed(0) : '0') + '% of the traced shape’s size (need ' + (100 * L.HAND_SPREAD_MIN) + '%)');
      g('no_far_extrapolation', pd > 0 && worst <= L.HAND_EXTRAP_MAX * pd, 'the shape reaches ' + (pd > 0 ? (100 * worst / pd).toFixed(0) : '∞') + '% of the points’ spread beyond them (limit ' + (100 * L.HAND_EXTRAP_MAX) + '%)');
      var need = shape.kind === 'area' ? 3 : 2, pl = placeShape(fit.T, pin, shape.px, shape.kind);
      g('shape', shape.px.length >= need && !pl.crosses, shape.px.length < need ? 'trace at least ' + need + ' corners' : (pl.crosses ? 'the traced ' + (shape.kind === 'area' ? 'outline' : 'line') + ' crosses itself' : 'traced shape is clean'));
      g('pin', pl.pin_dist_m <= L.PIN_MAX_OUTSIDE_M, pl.pin_dist_m === 0 ? 'the POTA pin is inside the outline' : 'the POTA pin is ' + pl.pin_dist_m.toFixed(0) + ' m from the traced shape (limit ' + L.PIN_MAX_OUTSIDE_M + ' m)');
    }
    return out;
  }

  /** JSON with sorted keys and no spaces: the bytes the click set's sha256 is taken over (the checker does the same). */
  function canonical(v) {
    if (v === null || typeof v !== 'object') return JSON.stringify(v);
    if (Array.isArray(v)) return '[' + v.map(canonical).join(',') + ']';
    return '{' + Object.keys(v).sort().map(function (k) { return JSON.stringify(k) + ':' + canonical(v[k]); }).join(',') + '}';
  }

  var api = { VERSION: VERSION, LIMITS: LIMITS, BASEMAPS: BASEMAPS, tmFwd: tmFwd, tmInv: tmInv, fitSimilarity: fitSimilarity, applySim: applySim,
    invSim: invSim, simScale: simScale, simRotDeg: simRotDeg, fitAffine: fitAffine, spreadRatio: spreadRatio, fitPairs: fitPairs,
    selfCrosses: selfCrosses, simplify: simplify, placeShape: placeShape, pinDistance: pinDistance, gates: gates, canonical: canonical,
    pxToLatLon: function (T, pin, x, y) { var m = applySim(T, x, y); return tmInv(pin[0], pin[1], m[0], m[1]); },
    latLonToPx: function (T, pin, lat, lon) { var m = tmFwd(pin[0], pin[1], lat, lon); return invSim(T, m[0], m[1]); } };
  if (typeof module === 'object' && module.exports) module.exports = api; else root.KPCPlaceMath = api;
})(typeof window !== 'undefined' ? window : this);
