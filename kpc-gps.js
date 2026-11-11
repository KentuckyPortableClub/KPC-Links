/* >>> kpc_released (KPC owner, 2026-11-11): the same block is in kpc-bounds.js, kpc-padus-layer.js, kpc-us-planner.js and kpc-gps.js (a test keeps them equal).
   The public map reads RELEASED files only: data/released/RELEASED.json (asked for fresh every page load) lists, per working file name,
   its released file(s) and each one's own version, so a changed file shows at once and an unchanged one stays cached.
   KPCREL.get('data/outlines/US-FL.geojson.gz') -> the parsed file (parts put together), or null when it is not released.
   An area that was never released (no entry in RELEASED.json) reads the working file as before.
   The Map Rep pages set window.KPC_WORKING_COPY = true before this file: they always read the working copy (the key being reviewed).
   Nov 11 (job 2): ONE part scheme for released and working files (kpc_release.split): a file over 1 MB is part 1 under its own name
   plus <stem>.p2<ext> ... ; part 1 carries kpc_part = [1, N, tag]. The working-copy path reads part 1, then parts 2..N, and puts them
   together with the same join; parts of two different saves (another tag) or a missing part = nothing, never half a file.
   An outline too big for one part is in pieces (kpc_piece = [k, M], same properties): the join puts its polygons back together. */
(function (w) {
  if (!w || w.KPCREL || typeof w.fetch !== 'function') return;
  var P = null, AREA = [[/^(outlines\/US-|us-key\/)/, 'US'], [/^ca-key\//, 'CA'], [/^world-key\//, 'world']];
  function index() { return P || (P = w.fetch('data/released/RELEASED.json', { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : {}; }).catch(function () { return {}; })); }
  function parse(r) {
    if (!r || !r.ok) return null;
    return r.arrayBuffer().then(function (ab) {
      var u8 = new Uint8Array(ab);
      if (u8.length >= 2 && u8[0] === 0x1f && u8[1] === 0x8b) {
        if (typeof DecompressionStream !== 'function') throw new Error('gzip');
        return new Response(new Blob([ab]).stream().pipeThrough(new DecompressionStream('gzip'))).text().then(JSON.parse);
      }
      return JSON.parse(new TextDecoder().decode(ab));
    });
  }
  function pieces(fs) {   /* Nov 11: the pieces of one big outline (kpc_piece = [k, M]) become one MultiPolygon again, in order */
    var by = {}, out = [], ok = true;
    fs.forEach(function (f) {
      var k = f && f.kpc_piece; if (!k) { out.push(f); return; }
      var r = (f.properties || {}).ref, g = by[r];
      if (!g) { g = by[r] = { f: Object.assign({}, f, { geometry: { type: 'MultiPolygon', coordinates: [] } }), n: k[1], got: 0 }; delete g.f.kpc_piece; out.push(g.f); }
      if (k[0] !== g.got + 1 || k[1] !== g.n) ok = false;
      g.f.geometry.coordinates = g.f.geometry.coordinates.concat((f.geometry || {}).coordinates || []); g.got++;
    });
    return ok && Object.keys(by).every(function (r) { return by[r].got === by[r].n; }) ? out : null;
  }
  function join(docs) {
    if (docs.some(function (d) { return !d; })) return null;            /* a missing part = not released (never half a file) */
    var k0 = docs[0].kpc_part;                                          /* Nov 11: parts must all be of the same save (same N and tag) */
    if (k0 && (docs.length !== k0[1] || docs.some(function (d, i) { var k = d.kpc_part || []; return k[0] !== i + 1 || k[1] !== k0[1] || k[2] !== k0[2]; }))) return null;
    if (docs.length === 1) return docs[0];
    var out = Object.assign({}, docs[0]); delete out.kpc_part;
    if (Array.isArray(out.features)) { out.features = pieces([].concat.apply([], docs.map(function (d) { return d.features || []; }))); if (!out.features) return null; }
    if (out.parks && !Array.isArray(out.parks)) out.parks = Object.assign.apply(null, [{}].concat(docs.map(function (d) { return d.parks || {}; })));
    return out;
  }
  function partName(path, i) { return i < 2 ? path : String(path).replace(/(\.geojson\.gz|\.json)$/, '.p' + i + '$1'); }
  function more(path, d, one) {   /* Nov 11: a working file in parts: part 1 says how many (kpc_part), parts 2..N are read the same way */
    var k = d && d.kpc_part, list = [Promise.resolve(d)];
    if (!k || !(k[1] > 1)) return Promise.resolve(d);
    for (var i = 2; i <= k[1]; i++) list.push(one(partName(path, i)));
    return Promise.all(list).then(join);
  }
  function urls(path) {
    var rel = String(path).replace(/^data\//, '').replace(/\?.*$/, '');
    return index().then(function (d) {
      var a = AREA.filter(function (x) { return x[0].test(rel); })[0];
      if (w.KPC_WORKING_COPY === true || !a || !(d.areas || {})[a[1]]) return null;   /* a review page (Map Rep sets KPC_WORKING_COPY) or an area not released yet: the working file */
      return ((d.files || {})[rel] || []).map(function (f) { return 'data/released/' + f[0] + '?v=' + f[1]; });
    });
  }
  function get(path, working) {
    return urls(path).then(function (list) {
      /* nothing released for it: the working file, read exactly as before this block existed (the caller's own fetch and r.json(); only an outline .gz is unpacked) */
      if (list === null) {
        if (working) { var wk = function (p) { return working(p).then(function (r) { return r && r.ok ? r.json() : null; }); }; return wk(path).then(function (d) { return more(path, d, wk); }); }
        var day = new Date().toISOString().slice(0, 10), rd = function (c) { return function (p) { return w.fetch(p + '?v=' + day, { cache: c }).then(parse); }; };
        return rd('force-cache')(path).then(function (d) {   /* parts of two saves in the browser cache: read them all once more, fresh */
          return more(path, d, rd('force-cache')).then(function (j) { return j || !(d && d.kpc_part) ? j : rd('reload')(path).then(function (d2) { return more(path, d2, rd('reload')); }); });
        });
      }
      if (!list.length) return null;
      return Promise.all(list.map(function (u) { return w.fetch(u, { cache: 'force-cache' }).then(parse); })).then(join);
    }).catch(function () { return null; });
  }
  w.KPCREL = { get: get, urls: urls, index: index };
})(typeof window !== 'undefined' ? window : null);
/* <<< kpc_released */
/* kpc-gps.js - the ONE place KPC GPS files are made (GPX 1.1, KML 2.2, GeoJSON).
 * Kentucky Portable Club. Browser, no dependencies, no server. Also loads in plain node (for tests).
 *
 *   KPCGPS.park(ref, opts)      -> Promise<{gpx, kml, geojson, files}>   one park
 *   KPCGPS.trip(stops, opts)    -> Promise<{gpx, kml, geojson, files}>   planner stops, in order (<rte>)
 *   KPCGPS.download(text, filename, mime)                                save / share a file
 *   KPCGPS.button(target, opts) -> <button> "⬇ GPS" + its chooser       UI helper
 *   KPCGPS.buildPark(park, opts) / KPCGPS.buildTrip(parks, opts)          same output from data you already hold (sync)
 *   KPCGPS.config({...})        adapters: dataUrl, outline (KPCB), parkInfo, trails, fetch, siteUrl, builtDate
 *
 * The data shapes it reads are ASSUMED (no site code / KPC-Data access when written); see README.md.
 * Never reads OpenStreetMap or Google data: everything comes from the club's own files through the adapters.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.KPCGPS = factory();
}(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // ---- the exact texts (spec "The data that goes in"); do not reword ----
  var NOTICE = "\u2139\ufe0f Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go.";
  var SITE_URL = "https://kentuckyportableclub.github.io/KPC-Links/";   // default site link (ruled Oct 31 2026); config({siteUrl}) overrides
  var PARKING_NO_AGENCY = "Parking (from an official access list; check the agency\u2019s map before you go)";   // ruled Oct 31 2026
  var FER_NOTICE = "\u26a0\ufe0f Parks' boundaries may overlap here, but we can't confirm it. Check both official boundary maps and make your own call before you count it.";
  var PIN_LABEL = "POTA pin (activations happen inside the boundary, not at the pin)";
  var NEARBY_LABEL = "Nearby public access, not the park's own";
  var PULLOFF_LABEL = "Possible pull-off (aerial photo, not official)";
  var NO_OUTLINE = "No official outline yet";
  var ROUTE_LABEL = "Trip stops in the planner's order (stops only, no turn-by-turn)";
  var SYM = { pin: "Flag, Green", parking: "Parking Area", trailhead: "Trail Head", boat: "Boat Ramp", entrance: "Information", pulloff: "Parking Area", other: "Information" };
  var MAX_PTS = 2000;                       // per outline in the GPX copy
  var TOLS = [5, 10, 15, 20, 30, 50, 75, 100, 150, 200, 300, 500, 750, 1000, 1500, 2000, 3000, 5000];
  var MIME = { gpx: "application/gpx+xml", kml: "application/vnd.google-earth.kml+xml", geojson: "application/geo+json" };

  var cfg = {
    siteUrl: null,        // default: SITE_URL (https://kentuckyportableclub.github.io/KPC-Links/)
    builtDate: null,      // date the data was built (YYYY-MM-DD); default: today
    siteBase: "",         // prefix for the site's own copy of data files (e.g. "/")
    dataUrl: null,        // function(path) -> url | [urls]; default window.KPC.dataUrl
    outline: null,        // function(ref, park) -> {status, agency, why, geojson} | Promise
    parkInfo: null,       // function(ref, opts) -> {ref, name, lat, lon, area} | Promise
    trails: null,         // function(ref, park) -> [{name, agency, geojson}] | Promise
    fetch: null           // function(url) -> Promise<Response-like>; default global fetch
  };
  function config(o) { for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) cfg[k] = o[k]; return cfg; }
  function g() { return typeof window !== "undefined" ? window : (typeof globalThis !== "undefined" ? globalThis : {}); }

  // ---------------- small helpers ----------------
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function today() { var d = new Date(); return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()); }
  function siteUrl(o) {
    if (o && o.siteUrl) return o.siteUrl;
    if (cfg.siteUrl) return cfg.siteUrl;
    return SITE_URL;
  }
  function xesc(s) {
    return String(s == null ? "" : s).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\uFFFE\uFFFF]/g, "")
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function num(v) { var n = typeof v === "string" ? parseFloat(v) : v; return (typeof n === "number" && isFinite(n)) ? n : null; }
  function okLL(lat, lon) { return lat != null && lon != null && Math.abs(lat) <= 90 && Math.abs(lon) <= 180 && !(lat === 0 && lon === 0); }
  function f7(x) { return (Math.round(x * 1e7) / 1e7).toString(); }
  function cut(s, n) { s = String(s).trim(); if (s.length <= n) return s; var c = s.slice(0, n), i = c.lastIndexOf(" "); return (i >= n - 8 ? c.slice(0, i) : c).trim(); }
  function shortName(name) {
    var s = String(name || "park").normalize ? String(name || "park").normalize("NFD").replace(/[\u0300-\u036f]/g, "") : String(name || "park");
    s = s.replace(/&/g, " and ").replace(/[^A-Za-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    if (s.length > 40) { s = s.slice(0, 40); if (s.lastIndexOf("-") > 20) s = s.slice(0, s.lastIndexOf("-")); }
    return s || "park";
  }
  function fileName(kind, ext, x, date) {
    date = date || today();
    if (kind === "park") return "KPC_" + x.ref + "_" + shortName(x.name) + "_" + date + "." + ext;
    if (kind === "trip") return "KPC_trip_" + date + "." + ext;
    return "KPC_" + x + "_parks_" + date + "." + ext;     // state pack
  }

  // ---------------- geometry: rings, simplification (same algorithm as kpc_gpspacks.py only when no tracts are passed; with tracts it differs) ----------------
  function closeRing(r) {
    var out = [];
    for (var i = 0; i < r.length; i++) {
      var p = r[i]; if (!p || num(p[0]) == null || num(p[1]) == null) continue;
      var q = [num(p[0]), num(p[1])];
      if (out.length && out[out.length - 1][0] === q[0] && out[out.length - 1][1] === q[1]) continue;
      out.push(q);
    }
    if (out.length && (out[0][0] !== out[out.length - 1][0] || out[0][1] !== out[out.length - 1][1])) out.push([out[0][0], out[0][1]]);
    return out.length >= 4 ? out : null;
  }
  // GeoJSON geometry -> list of polygons, each a list of closed rings [[lon,lat],...]
  function polygonsOf(geom) {
    if (!geom) return [];
    if (geom.type === "FeatureCollection") { var all = []; (geom.features || []).forEach(function (f) { all = all.concat(polygonsOf(f)); }); return all; }
    if (geom.type === "Feature") return polygonsOf(geom.geometry);
    if (geom.type === "GeometryCollection") { var a2 = []; (geom.geometries || []).forEach(function (x) { a2 = a2.concat(polygonsOf(x)); }); return a2; }
    var polys = geom.type === "Polygon" ? [geom.coordinates] : geom.type === "MultiPolygon" ? geom.coordinates : [];
    var res = [];
    (polys || []).forEach(function (rings) {
      var rr = (rings || []).map(closeRing).filter(Boolean);
      if (rr.length) res.push(rr);
    });
    return res;
  }
  // Nov 7: the tract id of each polygon polygonsOf() returns, when every feature carries properties.tract (tract switch on); else null
  function polyTracts(geom, n) {
    if (!geom || geom.type !== "FeatureCollection") return null;
    var out = [], any = false;
    (geom.features || []).forEach(function (f) { var t = f && f.properties && f.properties.tract; if (t) any = true; polygonsOf(f).forEach(function () { out.push(t || ""); }); });
    return any && out.length === n ? out : null;
  }
  function linesOf(geom) {
    if (!geom) return [];
    if (geom.type === "FeatureCollection") { var all = []; (geom.features || []).forEach(function (f) { all = all.concat(linesOf(f)); }); return all; }
    if (geom.type === "Feature") return linesOf(geom.geometry);
    var ls = geom.type === "LineString" ? [geom.coordinates] : geom.type === "MultiLineString" ? geom.coordinates : [];
    return (ls || []).map(function (l) {
      return (l || []).filter(function (p) { return p && num(p[0]) != null && num(p[1]) != null; }).map(function (p) { return [num(p[0]), num(p[1])]; });
    }).filter(function (l) { return l.length >= 2; });
  }
  function proj(pts) {          // local metres (equirectangular around the mean latitude)
    var lat0 = 0; pts.forEach(function (p) { lat0 += p[1]; }); lat0 = lat0 / pts.length * Math.PI / 180;
    var kx = 111320 * Math.cos(lat0), ky = 110540;
    return pts.map(function (p) { return [p[0] * kx, p[1] * ky]; });
  }
  function segDist(p, a, b) {
    var dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy, t = 0;
    if (L > 0) { t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L; t = t < 0 ? 0 : t > 1 ? 1 : t; }
    var x = a[0] + t * dx - p[0], y = a[1] + t * dy - p[1]; return Math.sqrt(x * x + y * y);
  }
  function dpIdx(xy, i0, i1, tol, keep) {      // Douglas-Peucker, iterative
    var stack = [[i0, i1]];
    while (stack.length) {
      var s = stack.pop(), a = s[0], b = s[1], dmax = -1, k = -1;
      for (var i = a + 1; i < b; i++) { var d = segDist(xy[i], xy[a], xy[b]); if (d > dmax) { dmax = d; k = i; } }
      if (k > 0 && dmax > tol) { keep[k] = 1; stack.push([a, k]); stack.push([k, b]); }
    }
  }
  function simplifyLine(pts, tol) {
    if (pts.length <= 2) return pts.slice();
    var xy = proj(pts), keep = new Uint8Array(pts.length); keep[0] = 1; keep[pts.length - 1] = 1;
    dpIdx(xy, 0, pts.length - 1, tol, keep);
    return pts.filter(function (_, i) { return keep[i]; });
  }
  function simplifyRing(ring, tol) {           // ring is closed; result stays closed, >= 4 points
    if (ring.length <= 4) return ring.slice();
    var xy = proj(ring), n = ring.length, k = 1, dmax = -1;
    for (var i = 1; i < n - 1; i++) { var dx = xy[i][0] - xy[0][0], dy = xy[i][1] - xy[0][1], d = dx * dx + dy * dy; if (d > dmax) { dmax = d; k = i; } }
    var keep = new Uint8Array(n); keep[0] = 1; keep[k] = 1; keep[n - 1] = 1;
    dpIdx(xy, 0, k, tol, keep); dpIdx(xy, k, n - 1, tol, keep);
    var out = ring.filter(function (_, i) { return keep[i]; });
    if (out.length < 4) {                      // keep a triangle: add the point farthest from the 0-k line
      var m = -1, dm = -1;
      for (var j = 1; j < n - 1; j++) { if (j === k) continue; var dd = segDist(xy[j], xy[0], xy[k]); if (dd > dm) { dm = dd; m = j; } }
      if (m < 0) return ring.slice();
      var idx = [0, k, m].sort(function (a, b) { return a - b; });
      out = [ring[idx[0]], ring[idx[1]], ring[idx[2]], ring[0]];
    }
    return out;
  }
  function countPts(polys) { var c = 0; polys.forEach(function (p) { p.forEach(function (r) { c += r.length; }); }); return c; }
  function ringArea(r) { var xy = proj(r), a = 0; for (var i = 0; i < xy.length - 1; i++) a += xy[i][0] * xy[i + 1][1] - xy[i + 1][0] * xy[i][1]; return Math.abs(a / 2); }
  // simplify a whole outline to <= maxPts points: 5 m first, then coarser. -> {polys, tol, dropped, points}
  // Nov 7 (tracts, hidden): `tracts` = the tract id of each polygon (only when the outline was read with the tract switch on). Then
  // every tract keeps its biggest outer ring before the size trim, so a small tract is never left out whole. Without it: as before.
  function simplifyOutline(polys, maxPts, tracts) {
    maxPts = maxPts || MAX_PTS;
    var res = null, tol = TOLS[0];
    for (var t = 0; t < TOLS.length; t++) {
      tol = TOLS[t];
      res = polys.map(function (p) { return p.map(function (r) { return simplifyRing(r, tol); }); });
      if (countPts(res) <= maxPts) return { polys: res, tol: tol, dropped: 0, points: countPts(res) };
    }
    // still too many (thousands of small pieces): leave out the smallest pieces until it fits
    var pieces = [];
    res.forEach(function (p, pi) { p.forEach(function (r, ri) { pieces.push({ pi: pi, ri: ri, a: ringArea(r), n: r.length }); }); });
    pieces.sort(function (a, b) { return b.a - a.a; });
    var total = 0, keepSet = {}, dropped = 0;
    if (tracts && tracts.length === res.length) {
      var firstOf = {};
      pieces.forEach(function (x) { var t = String(tracts[x.pi]); if (x.ri === 0 && !(t in firstOf)) firstOf[t] = x; });
      Object.keys(firstOf).forEach(function (t) { var x = firstOf[t]; total += x.n; keepSet[x.pi + ":" + x.ri] = 1; });
      pieces = pieces.filter(function (x) { return !keepSet[x.pi + ":" + x.ri]; });
    }
    pieces.forEach(function (x) { if (total + x.n <= maxPts) { total += x.n; keepSet[x.pi + ":" + x.ri] = 1; } else dropped++; });
    var out = [];
    res.forEach(function (p, pi) {
      if (!keepSet[pi + ":0"]) { dropped += 0; return; }           // outer ring gone -> its holes go too
      out.push(p.filter(function (_, ri) { return keepSet[pi + ":" + ri]; }));
    });
    return { polys: out, tol: tol, dropped: dropped, points: countPts(out) };
  }
  function simplifyLines(lines, maxPts) {
    maxPts = maxPts || MAX_PTS; var res = lines, tol = TOLS[0];
    for (var t = 0; t < TOLS.length; t++) {
      tol = TOLS[t]; res = lines.map(function (l) { return simplifyLine(l, tol); });
      var c = 0; res.forEach(function (l) { c += l.length; }); if (c <= maxPts) break;
    }
    var n = 0; res.forEach(function (l) { n += l.length; });
    return { lines: res, tol: tol, points: n };
  }

  // ---------------- tolerant readers for the club files (shapes assumed; see README) ----------------
  var REF_RE = /^[A-Z0-9]{1,4}-\d{1,6}$/;
  function accessKind(label) {
    var s = String(label || ""), i = s.indexOf(":"), text = (i >= 0 ? s.slice(i + 1) : s).trim(), l = text.toLowerCase();
    if (/pull-?off|candidate/.test(l)) return { kind: "pulloff", text: text };
    if (/boat|ramp|launch/.test(l)) return { kind: "boat", text: text };
    if (/trail ?head/.test(l)) return { kind: "trailhead", text: text };
    if (/entrance|entry|gate/.test(l)) return { kind: "entrance", text: text };
    if (/parking|lot\b/.test(l)) return { kind: "parking", text: text };
    return { kind: "other", text: text || "Access point" };
  }
  function outsideFlag(o) {
    if (!o || typeof o !== "object") return false;
    if (o.outside === true || o.out === true || o.nearby === true || o.inside === false || o.own === false) return true;
    var w = String(o.where || o.side || o.position || "").toLowerCase();
    return w === "outside" || w === "out" || w === "nearby";
  }
  // returns {ref: [{lat, lon, label, agency, outside, grade, source_url, read_date}]}
  function readAccess(obj, area) {
    var out = {};
    function add(ref, p) { if (!ref) return; (out[ref] = out[ref] || []).push(p); }
    function walk(o, ref, depth) {
      if (depth > 10 || o == null) return;
      if (Array.isArray(o)) {
        if (o.length >= 2 && typeof o[0] === "number" && typeof o[1] === "number") {
          var a = o[0], b = o[1], lat, lon;
          if (Math.abs(a) <= 90 && (Math.abs(b) > 90 || (a > 0 && b < 0))) { lat = a; lon = b; } else { lon = a; lat = b; }
          var strs = o.slice(2).filter(function (v) { return typeof v === "string"; });
          var lab = strs.filter(function (v) { return !/^(outside|out|nearby|inside)$/i.test(v); })[0] || "";
          var objx = o.slice(2).filter(function (v) { return v && typeof v === "object" && !Array.isArray(v); })[0] || {};
          var outside = strs.some(function (v) { return /^(outside|out|nearby)$/i.test(v); }) || outsideFlag(objx);
          if (okLL(lat, lon)) add(ref, { lat: lat, lon: lon, label: lab, agency: objx.agency || null, outside: outside, grade: objx.grade || objx.answer || null, source_url: objx.source_url || null, read_date: objx.read_date || null });
          return;
        }
        o.forEach(function (v) { walk(v, ref, depth + 1); });
        return;
      }
      if (typeof o === "object") {
        if (o.type === "FeatureCollection") { (o.features || []).forEach(function (f) { walk(f, ref, depth + 1); }); return; }
        if (o.type === "Feature" && o.geometry && o.geometry.type === "Point") {
          var pr = o.properties || {}, c = o.geometry.coordinates || [];
          if (okLL(num(c[1]), num(c[0]))) add(pr.ref || pr.park || ref, { lat: num(c[1]), lon: num(c[0]), label: pr.label || pr.name || pr.kind || pr.type || "", agency: pr.agency || null, outside: outsideFlag(pr), grade: pr.grade || pr.answer || null, source_url: pr.source_url || null, read_date: pr.read_date || null });
          return;
        }
        var la = num(o.lat != null ? o.lat : o.latitude), lo = num(o.lon != null ? o.lon : (o.lng != null ? o.lng : o.longitude));
        if (okLL(la, lo)) {
          add(o.ref || o.park || ref, { lat: la, lon: lo, label: o.label || o.name || o.kind || o.type || "", agency: o.agency || null, outside: outsideFlag(o), grade: o.grade || o.answer || null, source_url: o.source_url || null, read_date: o.read_date || null });
          return;
        }
        Object.keys(o).forEach(function (k) {
          var v = o[k]; if (v && typeof v === "object") walk(v, REF_RE.test(k) ? k : ref, depth + 1);
        });
      }
    }
    // Kentucky's kpc-ky-data.json keeps the access points under "ap"
    walk(obj && obj.ap && !obj.parks ? obj.ap : obj, null, 0);
    return out;
  }
  // data/parkinfo/US-XX.json {"parks": {ref: [name, website, type, access, access2, lat, lon, ...]}}
  function readParkInfo(obj, ref) {
    var parks = obj && (obj.parks || obj), row = parks && parks[ref];
    if (!row && Array.isArray(parks)) row = parks.filter(function (r) { return r && (r[0] === ref || r.ref === ref); })[0];
    if (!row) return null;
    if (Array.isArray(row)) {
      if (row[0] === ref) return { ref: ref, name: row[1], lat: num(row[2]), lon: num(row[3]) };   // world rows [ref, name, lat, lon]
      return { ref: ref, name: row[0], website: row[1], type: row[2], lat: num(row[5]), lon: num(row[6]) };
    }
    return { ref: ref, name: row.name || row.n, lat: num(row.lat), lon: num(row.lon != null ? row.lon : row.lng) };
  }
  // data/fers/US-XX.json rows (shape unknown here: any row naming two refs and a lat/lon)
  function readFers(obj, ref) {
    var out = [];
    function refsOf(o) {
      var r = [];
      ["a", "b", "ref", "ref_a", "ref_b", "park", "other", "with"].forEach(function (k) { if (typeof o[k] === "string" && REF_RE.test(o[k])) r.push(o[k]); });
      ["refs", "parks", "pair"].forEach(function (k) { if (Array.isArray(o[k])) o[k].forEach(function (x) { if (typeof x === "string" && REF_RE.test(x)) r.push(x); }); });
      return r.filter(function (x, i) { return r.indexOf(x) === i; });
    }
    function walk(o, key, depth) {
      if (depth > 8 || o == null || typeof o !== "object") return;
      if (Array.isArray(o)) {
        if (o.length >= 4 && typeof o[0] === "string" && typeof o[1] === "string" && REF_RE.test(o[0]) && REF_RE.test(o[1])) {
          var la0 = num(o[2]), lo0 = num(o[3]);
          if (okLL(la0, lo0)) out.push({ refs: [o[0], o[1]], lat: la0, lon: lo0, note: typeof o[4] === "string" ? o[4] : "" });
          return;
        }
        o.forEach(function (v) { walk(v, key, depth + 1); }); return;
      }
      var la = num(o.lat), lo = num(o.lon != null ? o.lon : o.lng);
      if (o.type === "Feature" && o.geometry && o.geometry.type === "Point") { la = num(o.geometry.coordinates[1]); lo = num(o.geometry.coordinates[0]); o = Object.assign({}, o.properties || {}, { _lat: la }); }
      var rs = refsOf(o); if (key && REF_RE.test(key) && rs.indexOf(key) < 0) rs.unshift(key);
      if (okLL(la, lo) && rs.length >= 2) { out.push({ refs: rs, lat: la, lon: lo, note: o.note || o.name || "", source_url: o.source_url || null, read_date: o.read_date || null }); return; }
      Object.keys(o).forEach(function (k) { walk(o[k], REF_RE.test(k) ? k : key, depth + 1); });
    }
    walk(obj, null, 0);
    return ref ? out.filter(function (f) { return f.refs.indexOf(ref) >= 0; }) : out;
  }

  // ---------------- the model: one park -> labelled items ----------------
  // agency named once for a whole access file (ASSUMED keys: agency, meta.agency, source.agency)
  function fileAgency(j) { return j ? agencyText(j.agency) || agencyText(j.meta && j.meta.agency) || agencyText(j.source && j.source.agency) : null; }
  function agencyText(a) { return (a && String(a).trim()) || null; }
  function outlineLabel(st, agency, why) {
    if (st === "official") return "Official boundary (" + (agencyText(agency) || "the managing agency") + ")";
    if (st === "approximate") return "Approximate outline (" + (why || "no official file yet") + ")";
    return NO_OUTLINE;
  }
  function normStatus(s) {
    s = String(s || "").toLowerCase();
    if (/^off/.test(s)) return "official";
    if (/^appr|^trace|picture/.test(s)) return "approximate";
    return "pin";
  }
  // park = {ref, name, lat, lon, outline:{status, agency, why, geojson|polys}, access:[...], trails:[{name, agency, geojson|lines}], fers:[...]}
  function model(park, opts) {
    opts = opts || {};
    var ref = park.ref, name = park.name || ref, o = park.outline || {};
    var st = normStatus(o.status || o.g || park.g);
    var polys = st === "pin" ? [] : (o.polys || polygonsOf(o.geojson || o.geometry || o));
    var m = { ref: ref, name: name, lat: num(park.lat), lon: num(park.lon), status: st, agency: o.agency || null, why: o.why || null, area: park.area || null };
    m.outlineLabel = outlineLabel(st, m.agency, m.why);
    m.polys = polys;
    m.polyTracts = st === "pin" || o.polys ? null : polyTracts(o.geojson || o.geometry || o, polys.length);   // Nov 7: null unless tract-labelled
    m.outlineMissing = st !== "pin" && !polys.length;
    m.access = []; var counts = {};
    (park.access || []).forEach(function (a) {
      var k = accessKind(a.label);
      if (k.kind === "pulloff") {
        if (!opts.pulloffs || String(a.grade || "").toUpperCase() !== "YES") return;   // only club-graded YES, only when asked
      }
      var label;
      if (k.kind === "parking") {
        var ag = agencyText(a.agency) || agencyText(park.accessAgency);   // access data's own agency only, never the outline's (ruled Oct 31 2026 9:41 PM CT)
        label = /^parking\s*\(from .+\)$/i.test(k.text) ? k.text : ag ? "Parking (from " + ag + ")" : PARKING_NO_AGENCY;   // no agency: ruled Oct 31 2026
      }
      else if (k.kind === "entrance") label = "Entrance";
      else if (k.kind === "boat") label = "Boat ramp";
      else if (k.kind === "trailhead") label = "Trailhead";
      else if (k.kind === "pulloff") label = PULLOFF_LABEL;
      else label = k.text;
      var short = { parking: "Parking", entrance: "Entrance", boat: "Boat ramp", trailhead: "Trailhead", pulloff: "Pull-off?", other: cut(k.text, 14) }[k.kind];
      if (a.outside) short = "Nearby " + short.toLowerCase();
      counts[short] = (counts[short] || 0) + 1;
      m.access.push({ lat: a.lat, lon: a.lon, kind: k.kind, label: label, outside: !!a.outside, sym: SYM[k.kind], short: short, n: counts[short],
        source_url: a.source_url || park.accessSource || null, read_date: a.read_date || park.accessRead || null });
    });
    m.access.forEach(function (a) { if (counts[a.short] < 2) a.n = 0; });
    m.trails = [];
    if (opts.trails !== false) (park.trails || []).forEach(function (t) {
      var lines = t.lines || linesOf(t.geojson || t.geometry || t);
      if (lines.length) m.trails.push({ name: t.name || "Trail", agency: t.agency || null, lines: lines, label: (t.name || "Trail") + " (official line, " + (agencyText(t.agency) || "the managing agency") + ")", source_url: t.source_url || null });
    });
    m.fers = (opts.fers || park.fersGiven) ? (park.fers || []).map(function (f) { return { lat: f.lat, lon: f.lon, refs: f.refs, note: f.note || "", source_url: f.source_url || null }; }) : [];
    return m;
  }
  function wname(m, a) { return cut(m.ref + " " + a.short + (a.n ? " " + a.n : ""), 30); }
  function pinDesc(m) {
    var d = m.ref + " " + m.name + ". " + PIN_LABEL + ".";
    var pc = m.status === "pin" && window.KPCB && KPCB.pcSync && KPCB.pcSync(m.ref);   /* Nov 9 2026: the exported file says it too */
    d += m.status === "pin" ? " " + NO_OUTLINE + "." + (pc ? " " + KPCB.pcNote(pc) : "") : m.outlineMissing ? " Outline: " + m.outlineLabel + ", not in this file (see the park card)." : " Outline: " + m.outlineLabel + ".";
    return d;
  }
  function fileDesc(o, anyFers) {
    var d = NOTICE + "\nData built: " + (o.builtDate || cfg.builtDate || today()) + "\nSite: " + siteUrl(o);
    if (anyFers) d += "\n" + FER_NOTICE;
    return d;
  }

  // ---------------- writers ----------------
  function gpxDoc(ms, o, route) {
    var anyFers = ms.some(function (m) { return m.fers.length; });
    var L = [], pts = [];
    ms.forEach(function (m) {
      if (okLL(m.lat, m.lon)) pts.push([m.lat, m.lon]);
      m.access.forEach(function (a) { pts.push([a.lat, a.lon]); });
    });
    L.push('<?xml version="1.0" encoding="UTF-8"?>');
    L.push('<gpx version="1.1" creator="KPC kpc-gps.js" xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">');
    L.push("<metadata><name>" + xesc(o.title) + "</name><desc>" + xesc(fileDesc(o, anyFers)) + "</desc>");
    var su = siteUrl(o); if (/^https?:\/\//.test(su)) L.push('<link href="' + xesc(su) + '"><text>Kentucky Portable Club</text></link>');
    L.push("<time>" + new Date().toISOString().replace(/\.\d+Z$/, "Z") + "</time>");
    if (pts.length) {
      var la = pts.map(function (p) { return p[0]; }), lo = pts.map(function (p) { return p[1]; });
      L.push('<bounds minlat="' + f7(Math.min.apply(null, la)) + '" minlon="' + f7(Math.min.apply(null, lo)) + '" maxlat="' + f7(Math.max.apply(null, la)) + '" maxlon="' + f7(Math.max.apply(null, lo)) + '"/>');
    }
    L.push("</metadata>");
    function wpt(lat, lon, name, desc, src, sym, type) {
      L.push('<wpt lat="' + f7(lat) + '" lon="' + f7(lon) + '"><name>' + xesc(cut(name, 30)) + "</name><desc>" + xesc(desc) + "</desc>" +
        (src ? "<src>" + xesc(src) + "</src>" : "") + (sym ? "<sym>" + xesc(sym) + "</sym>" : "") + (type ? "<type>" + xesc(type) + "</type>" : "") + "</wpt>");
    }
    ms.forEach(function (m) {
      if (okLL(m.lat, m.lon)) wpt(m.lat, m.lon, m.ref + " " + m.name, pinDesc(m), "POTA park pin (data/parkinfo)", SYM.pin, "POTA pin");
      m.access.forEach(function (a) {
        var desc = (a.outside ? NEARBY_LABEL + ": " + a.label : a.label) + ". " + m.ref + " " + m.name + ".";
        wpt(a.lat, a.lon, wname(m, a), desc, a.source_url || "KPC access file (data/access)", a.sym, a.outside ? "Nearby access" : a.kind === "pulloff" ? "Possible pull-off" : "Official access");
      });
      m.fers.forEach(function (f, i) {
        wpt(f.lat, f.lon, "2-fer " + f.refs.join("+"), FER_NOTICE + " Possible 2-fer spot: " + f.refs.join(" + ") + (f.note ? ". " + f.note : "") + ".", f.source_url || "KPC 2-fer rows (data/fers)", null, "2-fer spot");
      });
    });
    if (route && route.length) {
      L.push("<rte><name>" + xesc(cut(o.title, 30)) + "</name><desc>" + xesc(ROUTE_LABEL) + "</desc>");
      route.forEach(function (s, i) {
        L.push('<rtept lat="' + f7(s.lat) + '" lon="' + f7(s.lon) + '"><name>' + xesc(cut((i + 1) + " " + (s.ref ? s.ref + " " : "") + (s.name || ""), 30)) + "</name><desc>" +
          xesc("Stop " + (i + 1) + ": " + (s.ref ? s.ref + " " : "") + (s.name || "") + (s.ref ? ". " + PIN_LABEL + "." : "")) + "</desc><sym>" + SYM.pin + "</sym></rtept>");
      });
      L.push("</rte>");
    }
    ms.forEach(function (m) {
      if (m.polys.length && o.outlines !== false) {
        var s = simplifyOutline(m.polys, o.maxPoints, m.polyTracts);
        L.push("<trk><name>" + xesc(m.ref + " boundary (" + (m.status === "official" ? "Official" : "Approximate") + ")") + "</name><desc>" +
          xesc(m.outlineLabel + ". " + m.ref + " " + m.name + ". Simplified to ~" + s.tol + " m for GPS units (" + s.points + " points)" + (s.dropped ? "; " + s.dropped + " small pieces left out" : "") + ".") +
          "</desc><type>" + (m.status === "official" ? "Official boundary" : "Approximate outline") + "</type>");
        s.polys.forEach(function (p) { p.forEach(function (r) {
          L.push("<trkseg>" + r.map(function (c) { return '<trkpt lat="' + f7(c[1]) + '" lon="' + f7(c[0]) + '"/>'; }).join("") + "</trkseg>");
        }); });
        L.push("</trk>");
      }
      m.trails.forEach(function (t) {
        var s = simplifyLines(t.lines, o.maxPoints);
        L.push("<trk><name>" + xesc(cut(t.name, 30)) + "</name><desc>" + xesc(t.label + ". " + m.ref + " " + m.name + ". Simplified to ~" + s.tol + " m for GPS units (" + s.points + " points).") + "</desc><type>Trail</type>");
        s.lines.forEach(function (l) { L.push("<trkseg>" + l.map(function (c) { return '<trkpt lat="' + f7(c[1]) + '" lon="' + f7(c[0]) + '"/>'; }).join("") + "</trkseg>"); });
        L.push("</trk>");
      });
    });
    L.push("</gpx>");
    return L.join("\n") + "\n";
  }

  // KML colours are aabbggrr
  var KSTYLE = {
    pin: '<Style id="pin"><IconStyle><color>ff00c000</color><scale>1.3</scale></IconStyle><LabelStyle><scale>0.9</scale></LabelStyle></Style>',
    parking: '<Style id="parking"><IconStyle><color>ffff6600</color><scale>1.0</scale></IconStyle></Style>',
    entrance: '<Style id="entrance"><IconStyle><color>ffffffff</color><scale>1.0</scale></IconStyle></Style>',
    boat: '<Style id="boat"><IconStyle><color>ffffff00</color><scale>1.0</scale></IconStyle></Style>',
    trailhead: '<Style id="trailhead"><IconStyle><color>ff2f6b8b</color><scale>1.0</scale></IconStyle></Style>',
    other: '<Style id="other"><IconStyle><color>ffcccccc</color><scale>0.9</scale></IconStyle></Style>',
    nearby: '<Style id="nearby"><IconStyle><color>ff888888</color><scale>0.8</scale></IconStyle></Style>',
    pulloff: '<Style id="pulloff"><IconStyle><color>ff0080ff</color><scale>0.8</scale></IconStyle></Style>',
    fer: '<Style id="fer"><IconStyle><color>ffff00ff</color><scale>1.0</scale></IconStyle></Style>',
    official: '<Style id="official"><LineStyle><color>ff00ffff</color><width>3</width></LineStyle><PolyStyle><color>3300ffff</color><outline>1</outline></PolyStyle></Style>',
    approxfill: '<Style id="approxfill"><LineStyle><color>0000ffff</color><width>0</width></LineStyle><PolyStyle><color>2200ffff</color><outline>0</outline></PolyStyle></Style>',
    dash: '<Style id="dash"><LineStyle><color>ff00ffff</color><width>3</width></LineStyle></Style>',
    trail: '<Style id="trail"><LineStyle><color>ff1e3cdc</color><width>3</width></LineStyle></Style>',
    route: '<Style id="route"><LineStyle><color>ffff00aa</color><width>2</width></LineStyle></Style>'
  };
  function kc(r) { return r.map(function (c) { return f7(c[0]) + "," + f7(c[1]); }).join(" "); }
  function dashes(ring) {   // KML has no dashed line style, so the approximate outline is drawn as short dashes
    var xy = proj(ring), per = 0, i;
    for (i = 0; i < xy.length - 1; i++) per += Math.hypot(xy[i + 1][0] - xy[i][0], xy[i + 1][1] - xy[i][1]);
    var dash = Math.max(15, Math.min(400, per / 120)), out = [], cur = [ring[0]], on = true, left = dash;
    for (i = 0; i < xy.length - 1; i++) {
      var a = ring[i], b = ring[i + 1], segL = Math.hypot(xy[i + 1][0] - xy[i][0], xy[i + 1][1] - xy[i][1]), pos = 0;
      while (segL - pos > left) {
        pos += left; var t = pos / segL, p = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
        if (on) { cur.push(p); out.push(cur); cur = []; } else cur = [p];
        on = !on; left = dash;
      }
      left -= segL - pos; if (on) cur.push(b);
    }
    if (on && cur.length >= 2) out.push(cur);
    return out.filter(function (d) { return d.length >= 2; });
  }
  function kmlDoc(ms, o, route) {
    var anyFers = ms.some(function (m) { return m.fers.length; });
    var single = ms.length === 1 && !(route && route.length), L = [];
    L.push('<?xml version="1.0" encoding="UTF-8"?>');
    L.push('<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>' + xesc(o.title) + "</name><open>1</open><description>" + xesc(fileDesc(o, anyFers)) + "</description>");
    Object.keys(KSTYLE).forEach(function (k) { L.push(KSTYLE[k]); });
    function pm(name, desc, style, geom) { L.push("<Placemark><name>" + xesc(name) + "</name><description>" + xesc(desc) + "</description><styleUrl>#" + style + "</styleUrl>" + geom + "</Placemark>"); }
    function pt(lat, lon) { return "<Point><coordinates>" + f7(lon) + "," + f7(lat) + "</coordinates></Point>"; }
    if (!single) L.push("<Folder><name>Park pins</name>");
    ms.forEach(function (m) { if (okLL(m.lat, m.lon)) pm(m.ref + " " + m.name, pinDesc(m), "pin", pt(m.lat, m.lon)); });
    if (route && route.length) {
      pm("Trip route", ROUTE_LABEL + ": " + route.map(function (s, i) { return (i + 1) + ". " + (s.ref || "") + " " + (s.name || ""); }).join("; "), "route",
        "<LineString><tessellate>1</tessellate><coordinates>" + route.map(function (s) { return f7(s.lon) + "," + f7(s.lat); }).join(" ") + "</coordinates></LineString>");
    }
    if (!single) L.push("</Folder>");
    L.push("<Folder><name>Parking</name><description>Official parking and access points from the club's access files. Grey points: " + xesc(NEARBY_LABEL) + ".</description>");
    ms.forEach(function (m) { m.access.forEach(function (a) {
      pm(a.outside ? NEARBY_LABEL : a.label, (a.outside ? NEARBY_LABEL + ": " + a.label : a.label) + ". " + m.ref + " " + m.name + ".", a.outside ? "nearby" : a.kind, pt(a.lat, a.lon));
    }); });
    L.push("</Folder><Folder><name>Trails</name>");
    ms.forEach(function (m) { m.trails.forEach(function (t) {
      pm(t.name, t.label + ". " + m.ref + " " + m.name + ".", "trail", "<MultiGeometry>" + t.lines.map(function (l) { return "<LineString><tessellate>1</tessellate><coordinates>" + kc(l) + "</coordinates></LineString>"; }).join("") + "</MultiGeometry>");
    }); });
    L.push("</Folder><Folder><name>Outline</name>");
    ms.forEach(function (m) {
      if (!m.polys.length || o.outlines === false) {
        if (m.status === "pin") L.push("<Placemark><name>" + xesc(m.ref + ": " + NO_OUTLINE) + "</name><description>" + xesc(m.ref + " " + m.name + ". " + NO_OUTLINE + ". No outline is drawn.") + "</description></Placemark>");
        return;
      }
      var polys = m.polys, extra = "";
      if (o.kmlSimplify) { var s = simplifyOutline(m.polys, o.maxPoints, m.polyTracts); polys = s.polys; extra = " Simplified to ~" + s.tol + " m (" + s.points + " points)" + (s.dropped ? "; " + s.dropped + " small pieces left out" : "") + "."; }
      var pg = polys.map(function (p) {
        return "<Polygon><tessellate>1</tessellate><outerBoundaryIs><LinearRing><coordinates>" + kc(p[0]) + "</coordinates></LinearRing></outerBoundaryIs>" +
          p.slice(1).map(function (r) { return "<innerBoundaryIs><LinearRing><coordinates>" + kc(r) + "</coordinates></LinearRing></innerBoundaryIs>"; }).join("") + "</Polygon>";
      }).join("");
      var desc = m.outlineLabel + ". " + m.ref + " " + m.name + "." + extra;
      var nm = m.ref + " boundary (" + (m.status === "official" ? "Official" : "Approximate") + ")";
      if (m.status === "official") pm(nm, desc, "official", "<MultiGeometry>" + pg + "</MultiGeometry>");
      else {
        var ds = []; polys.forEach(function (p) { p.forEach(function (r) { ds = ds.concat(dashes(r)); }); });
        pm(nm, desc + " Dashed line: approximate.", "approxfill", "<MultiGeometry>" + pg + "</MultiGeometry>");
        pm(nm + " line", desc + " Dashed line: approximate.", "dash", "<MultiGeometry>" + ds.map(function (d) { return "<LineString><tessellate>1</tessellate><coordinates>" + kc(d) + "</coordinates></LineString>"; }).join("") + "</MultiGeometry>");
      }
    });
    L.push("</Folder>");
    if (anyFers) {
      L.push("<Folder><name>2-fers</name><description>" + xesc(FER_NOTICE) + "</description>");
      ms.forEach(function (m) { m.fers.forEach(function (f) { pm("2-fer " + f.refs.join(" + "), FER_NOTICE + " Possible 2-fer spot: " + f.refs.join(" + ") + (f.note ? ". " + f.note : "") + ".", "fer", pt(f.lat, f.lon)); }); });
      L.push("</Folder>");
    }
    L.push("</Document></kml>");
    return L.join("\n") + "\n";
  }
  function geojsonDoc(ms, o, route) {
    var anyFers = ms.some(function (m) { return m.fers.length; }), F = [];
    var rd = o.builtDate || cfg.builtDate || today();
    function feat(geom, props) { F.push({ type: "Feature", geometry: geom, properties: props }); }
    ms.forEach(function (m) {
      if (okLL(m.lat, m.lon)) feat({ type: "Point", coordinates: [m.lon, m.lat] }, { kpc: "pin", ref: m.ref, name: m.ref + " " + m.name, label: PIN_LABEL, outline: m.outlineLabel, desc: pinDesc(m), no_outline: m.status === "pin" ? NO_OUTLINE : undefined, sym: SYM.pin, source_url: "data/parkinfo", read_date: rd, why: "POTA park pin" });
      m.access.forEach(function (a) {
        feat({ type: "Point", coordinates: [a.lon, a.lat] }, { kpc: a.outside ? "nearby_access" : a.kind === "pulloff" ? "possible_pulloff" : "access", ref: m.ref, name: wname(m, a), label: a.outside ? NEARBY_LABEL : a.label, access_label: a.label, own: !a.outside, sym: a.sym, source_url: a.source_url || "data/access", read_date: a.read_date || rd, why: a.outside ? NEARBY_LABEL : "official access point from the club's access file" });
      });
      if (m.polys.length && o.outlines !== false) feat({ type: m.polys.length === 1 ? "Polygon" : "MultiPolygon", coordinates: m.polys.length === 1 ? m.polys[0] : m.polys },
        { kpc: "outline", ref: m.ref, name: m.ref + " boundary (" + (m.status === "official" ? "Official" : "Approximate") + ")", label: m.outlineLabel, status: m.status, agency: m.agency, line: m.status === "official" ? "solid yellow" : "dashed", detail: "full detail (not simplified)", source_url: "KPCB outline", read_date: rd, why: m.outlineLabel });
      m.trails.forEach(function (t) { feat({ type: "MultiLineString", coordinates: t.lines }, { kpc: "trail", ref: m.ref, name: t.name, label: t.label, source_url: t.source_url || "KPC trail layer", read_date: rd, why: "official trail line" }); });
      m.fers.forEach(function (f) { feat({ type: "Point", coordinates: [f.lon, f.lat] }, { kpc: "2fer", ref: m.ref, refs: f.refs, name: "2-fer " + f.refs.join("+"), label: FER_NOTICE, note: f.note, source_url: f.source_url || "data/fers", read_date: rd, why: "possible 2-fer spot" }); });
    });
    if (route && route.length) feat({ type: "LineString", coordinates: route.map(function (s) { return [s.lon, s.lat]; }) }, { kpc: "route", label: ROUTE_LABEL, stops: route.map(function (s) { return s.ref || s.name; }) });
    var head = { notice: NOTICE, built: rd, site: siteUrl(o), title: o.title };
    if (anyFers) head.fer_notice = FER_NOTICE;
    return JSON.stringify({ type: "FeatureCollection", kpc: head, description: fileDesc(o, anyFers), features: F }, null, 1) + "\n";
  }

  // ---------------- public builders ----------------
  function buildPark(park, opts) {
    opts = Object.assign({}, opts || {});
    var m = model(park, opts), date = opts.fileDate || today();
    var o = Object.assign({ title: "KPC " + m.ref + " " + m.name }, opts);
    return { gpx: gpxDoc([m], o), kml: kmlDoc([m], o), geojson: geojsonDoc([m], o),
      files: { gpx: fileName("park", "gpx", m, date), kml: fileName("park", "kml", m, date), geojson: fileName("park", "geojson", m, date) } };
  }
  // parks: in stop order; a stop without a ref (a plain point) is {name, lat, lon}
  function buildTrip(parks, opts) {
    opts = Object.assign({ outlines: true }, opts || {});
    var date = opts.fileDate || today(), ms = [], route = [];
    parks.forEach(function (p) {
      if (p.ref) { var m = model(p, opts); ms.push(m); if (okLL(m.lat, m.lon)) route.push({ ref: m.ref, name: m.name, lat: m.lat, lon: m.lon }); }
      else if (okLL(num(p.lat), num(p.lon))) route.push({ name: p.name || "Stop", lat: num(p.lat), lon: num(p.lon) });
    });
    var seen = {};                              // a 2-fer spot shared by two stops goes in once
    ms.forEach(function (m) { m.fers = m.fers.filter(function (f) { var k = f.refs.slice().sort().join("+") + "@" + f7(f.lat) + "," + f7(f.lon); if (seen[k]) return false; seen[k] = 1; return true; }); });
    var o = Object.assign({ title: "KPC trip " + date }, opts);
    return { gpx: gpxDoc(ms, o, route), kml: kmlDoc(ms, o, route), geojson: geojsonDoc(ms, o, route),
      files: { gpx: fileName("trip", "gpx", null, date), kml: fileName("trip", "kml", null, date), geojson: fileName("trip", "geojson", null, date) } };
  }

  // ---------------- data loading through the adapters (all assumed; see README) ----------------
  var cache = {};
  function candidates(path, opts) {
    var w = g(), list = [], du = (opts && opts.dataUrl) || cfg.dataUrl || (w.KPC && typeof w.KPC.dataUrl === "function" ? function (p) { return w.KPC.dataUrl(p); } : null);
    if (du) { var u = du(path); (Array.isArray(u) ? u : [u]).forEach(function (x) { if (x) list.push(x); }); }
    var site = ((opts && opts.siteBase) || cfg.siteBase || "") + path;
    if (list.indexOf(site) < 0) list.push(site);                   // the site's own copy, last
    return list;
  }
  function getJSON(path, opts) {
    var key = path; if (cache[key]) return cache[key];
    var f = (opts && opts.fetch) || cfg.fetch || (typeof fetch === "function" ? fetch : null);
    if (!f) return Promise.resolve(null);
    var urls = candidates(path, opts);
    // Nov 11 (KPC owner): a US key file comes from data/released (KPCREL) unless the caller gave its own fetch or data source
    var W = g();
    if (W.KPCREL && /^data\/us-key\/US-[A-Z]{2}\.json$/.test(path) && !(opts && (opts.fetch || opts.dataUrl)) && !cfg.fetch && !cfg.dataUrl) {
      var rp = W.KPCREL.get(path, function (q) { return W.KPC && typeof W.KPC.dataUrl === "function" ? W.KPC.dataUrl(q) : W.fetch(q); }).then(function (j) { return j ? { url: "data/released/" + path.slice(5), json: j } : null; });
      cache[key] = rp; rp.then(function (x) { if (!x) delete cache[key]; });
      return rp;
    }
    var p = urls.reduce(function (prev, url) {
      return prev.then(function (got) {
        if (got) return got;
        return Promise.resolve().then(function () { return f(url); }).then(function (r) { return r && r.ok ? r.json() : null; }).then(function (j) { return j ? { url: url, json: j } : null; }).catch(function () { return null; });
      });
    }, Promise.resolve(null));
    cache[key] = p; p.then(function (x) { if (!x) delete cache[key]; });
    return p;
  }
  function call(fn, a, b) { try { return Promise.resolve(fn ? fn(a, b) : null).catch(function () { return null; }); } catch (e) { return Promise.resolve(null); } }
  function defaultOutline(ref) {          // KPCB's API is not known here: try the likely names
    var K = g().KPCB; if (!K) return null;
    var fns = ["gpsOutline", "outline", "get", "geojson", "feature", "lookup"];
    for (var i = 0; i < fns.length; i++) if (typeof K[fns[i]] === "function") return K[fns[i]](ref);
    return K[ref] || (K.parks && K.parks[ref]) || null;
  }
  function normOutline(x, key) {
    var o = x || {};
    var geo = o.geojson || o.geometry || o.feature || ((o.type === "Feature" || o.type === "Polygon" || o.type === "MultiPolygon" || o.type === "FeatureCollection") ? o : null);
    var props = (o.type === "Feature" && o.properties) || o.properties || {};
    var st = o.status || o.g || props.status || props.g || (key && key.g) || (geo ? "official" : "pin");
    var agency = o.agency || props.agency || (key && key.src && key.src[0] && (key.src[0].agency || (typeof key.src[0] === "string" ? key.src[0] : null))) || null;
    var why = o.why || props.why || (key && key.m && key.m[0] && key.m[0][3]) || (/trace|picture/i.test(String(st)) ? "traced from the agency's picture map" : null);
    return { status: normStatus(st), agency: agency, why: why, geojson: geo };
  }
  function loadPark(stop, opts) {
    opts = opts || {};
    var ref = typeof stop === "string" ? stop : stop.ref, given = typeof stop === "object" ? stop : {};
    var area = given.area || opts.area || (g().KPC && g().KPC.area) || null;
    var infoP = given.lat != null && given.name ? Promise.resolve(given)
      : call(opts.parkInfo || cfg.parkInfo, ref, opts).then(function (x) {
        if (x) return x;
        return area ? getJSON("data/parkinfo/" + area + ".json", opts).then(function (r) { return r ? readParkInfo(r.json, ref) : null; }) : null;
      });
    var keyP = area ? getJSON("data/us-key/" + area + ".json", opts).then(function (r) { return r && r.json && r.json.parks ? r.json.parks[ref] : null; }) : Promise.resolve(null);
    var accP = area ? getJSON("data/access/" + area + ".json", opts).then(function (r) {
      if (r) return { pts: readAccess(r.json)[ref] || [], url: r.url, agency: fileAgency(r.json) };
      if (area === "US-KY") return getJSON("kpc-ky-data.json", Object.assign({}, opts, { dataUrl: function () { return null; } })).then(function (k) { return k ? { pts: readAccess(k.json.ap ? { ap: k.json.ap } : k.json)[ref] || [], url: k.url } : { pts: [] }; });
      return { pts: [] };
    }) : Promise.resolve({ pts: given.access || [] });
    var ferP = Array.isArray(given.fers) ? Promise.resolve(given.fers) : opts.fers && area && !opts.noFers ? getJSON("data/fers/" + area + ".json", opts).then(function (r) { return r ? readFers(r.json, ref) : []; }) : Promise.resolve(given.fers || []);
    return Promise.all([infoP, keyP, accP, ferP]).then(function (v) {
      var info = v[0] || {}, key = v[1];
      var park = Object.assign({}, given, info, { ref: ref, area: area });
      park.access = given.access || v[2].pts; park.accessSource = v[2].url || null;
      if (!park.accessAgency) park.accessAgency = v[2].agency || null;
      park.fers = v[3]; park.fersGiven = Array.isArray(given.fers);   // spots handed over by the page (Overlap Finder) always go in
      var oP = given.outline ? Promise.resolve(given.outline) : call(opts.outline || cfg.outline || defaultOutline, ref, park);
      var tP = given.trails ? Promise.resolve(given.trails) : call(opts.trailsAdapter || cfg.trails || function (r) { var K = g().KPCB; return K && typeof K.trails === "function" ? K.trails(r) : null; }, ref, park);
      return Promise.all([oP, tP]).then(function (w) {
        park.outline = normOutline(w[0], key);
        park.trails = Array.isArray(w[1]) ? w[1] : [];
        return park;
      });
    });
  }
  function park(ref, opts) { return loadPark(ref, opts).then(function (p) { return buildPark(p, opts); }); }
  function trip(stops, opts) {
    return Promise.resolve(stops).then(function (stops) { return Promise.all((stops || []).map(function (s) {
      if (typeof s === "object" && !s.ref) return s;                // plain point stop
      return loadPark(s, opts);
    })); }).then(function (ps) { return buildTrip(ps, opts); });   // KPC site (chat 3): stops may be a Promise (areas looked up first)
  }

  // ---------------- download ----------------
  function download(text, filename, mime) {
    var w = g(), nav = w.navigator || {};
    mime = mime || (/\.gpx$/i.test(filename) ? MIME.gpx : /\.kml$/i.test(filename) ? MIME.kml : MIME.geojson);
    var blob = new Blob([text], { type: mime });
    var iOS = /iP(hone|ad|od)/.test(nav.userAgent || "") || (nav.platform === "MacIntel" && nav.maxTouchPoints > 1);
    if (iOS && typeof File === "function" && nav.canShare) {
      try {
        var file = new File([blob], filename, { type: mime });
        if (nav.canShare({ files: [file] })) return nav.share({ files: [file], title: filename }).then(function () { return "shared"; }, function (e) { return e && e.name === "AbortError" ? "cancelled" : anchor(); });
      } catch (e) { /* fall through to a normal download */ }
    }
    function anchor() {
      var url = URL.createObjectURL(blob), a = w.document.createElement("a");
      a.href = url; a.download = filename; a.rel = "noopener"; a.style.display = "none";
      w.document.body.appendChild(a); a.click();
      setTimeout(function () { URL.revokeObjectURL(url); a.remove(); }, 30000);
      return "downloaded";
    }
    return Promise.resolve(anchor());
  }

  // ---------------- the "⬇ GPS" button + chooser ----------------
  var CSS = ".kpcgps{display:inline-block;max-width:100%;box-sizing:border-box;font:inherit}" +
    ".kpcgps *{box-sizing:border-box}" +
    ".kpcgps-btn{font:inherit;font-size:15px;min-height:40px;padding:6px 12px;border:1px solid #2c5e2e;border-radius:8px;background:#fff;color:#2c5e2e;cursor:pointer}" +
    ".kpcgps-panel{display:none;margin-top:6px;padding:8px;border:1px solid #bbb;border-radius:8px;background:#fff;color:#222;max-width:100%;width:340px}" +
    ".kpcgps.open .kpcgps-panel{display:block}" +
    ".kpcgps-fmts{display:flex;flex-wrap:wrap;gap:6px}" +
    ".kpcgps-fmts button{flex:1 1 96px;min-width:0;min-height:44px;font:inherit;font-size:14px;padding:6px 8px;border:1px solid #2c5e2e;border-radius:6px;background:#eef6ee;color:#173a18;cursor:pointer;white-space:normal}" +
    ".kpcgps-fmts button:first-child{background:#2c5e2e;color:#fff}" +
    ".kpcgps-panel label{display:flex;align-items:center;gap:8px;margin-top:8px;font-size:14px;min-height:32px}" +
    ".kpcgps-panel input{width:20px;height:20px;flex:none}" +
    ".kpcgps-note{font-size:12px;color:#555;margin-top:6px;overflow-wrap:anywhere}" +
    ".kpcgps-msg{font-size:13px;margin-top:4px;min-height:1em;overflow-wrap:anywhere}";
  function css(doc) { if (doc.getElementById("kpcgps-css")) return; var s = doc.createElement("style"); s.id = "kpcgps-css"; s.textContent = CSS; doc.head.appendChild(s); }
  // target: element to append to. opts: {ref} for one park, or {stops: fn|array} for a trip; plus park()/trip() options.
  function button(target, opts) {
    opts = opts || {}; var doc = g().document; css(doc);
    var box = doc.createElement("div"); box.className = "kpcgps";
    var isTrip = !!opts.stops;
    box.innerHTML = '<button type="button" class="kpcgps-btn" aria-expanded="false">\u2b07 GPS</button>' +
      '<div class="kpcgps-panel" role="group" aria-label="Download for GPS"><div class="kpcgps-fmts">' +
      '<button type="button" data-f="gpx">GPX (Garmin / phone)</button><button type="button" data-f="kml">KML (Google Earth)</button><button type="button" data-f="geojson">GeoJSON</button></div>' +
      (opts.noFers ? "" : '<label><input type="checkbox" class="kpcgps-fers"> include 2-fer spots</label>') +   // KPC site: the raw 2-fer box only where asked
      (isTrip ? '<label><input type="checkbox" class="kpcgps-outl" checked> include park outlines</label>' : "") +
      '<div class="kpcgps-note">' + xesc(NOTICE) + '</div><div class="kpcgps-msg" aria-live="polite"></div></div>';
    var btn = box.querySelector(".kpcgps-btn"), msg = box.querySelector(".kpcgps-msg");
    btn.addEventListener("click", function () { var o = box.classList.toggle("open"); btn.setAttribute("aria-expanded", o ? "true" : "false"); });
    Array.prototype.forEach.call(box.querySelectorAll("[data-f]"), function (b) {
      b.addEventListener("click", function () {
        var f = b.getAttribute("data-f"), fb = box.querySelector(".kpcgps-fers"), o = Object.assign({}, opts, { fers: fb ? fb.checked : false });
        if (isTrip) o.outlines = box.querySelector(".kpcgps-outl").checked;
        msg.textContent = "Making the file\u2026";
        var job = isTrip ? trip(typeof opts.stops === "function" ? opts.stops() : opts.stops, o) : park(typeof opts.ref === "function" ? opts.ref() : opts.ref, o);
        job.then(function (r) { return download(r[f], r.files[f], MIME[f]).then(function (how) { msg.textContent = how === "cancelled" ? "" : "Saved " + r.files[f]; }); })
          .catch(function (e) { msg.textContent = "Sorry, the file could not be made (" + (e && e.message || e) + ")."; });
      });
    });
    if (target) target.appendChild(box);
    return box;
  }

  return {
    version: "0.1.0", NOTICE: NOTICE, FER_NOTICE: FER_NOTICE, PIN_LABEL: PIN_LABEL, NEARBY_LABEL: NEARBY_LABEL, PULLOFF_LABEL: PULLOFF_LABEL, NO_OUTLINE: NO_OUTLINE, SITE_URL: SITE_URL, PARKING_NO_AGENCY: PARKING_NO_AGENCY, SYM: SYM, MIME: MIME,
    config: config, park: park, trip: trip, download: download, button: button,
    buildPark: buildPark, buildTrip: buildTrip, loadPark: loadPark,
    readAccess: readAccess, readParkInfo: readParkInfo, readFers: readFers, polygonsOf: polygonsOf,
    simplifyOutline: simplifyOutline, simplifyRing: simplifyRing, shortName: shortName, fileName: fileName,
    _clearCache: function () { cache = {}; }
  };
}));
