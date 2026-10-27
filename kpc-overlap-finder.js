/* PARK OVERLAP FINDER (chat 3, Oct 27; HQ/Brandon: 'build the REAL Park Overlap Finder now on Kentucky's final 2-fer data …
   new regions plug in as their own lists'). Rules = Sheet A + chat 8's accepted recommendations (notes/logger-lounge-digi.md,
   .claude/build/research/KPC_RuleSheet_Finder_desk.md) and mapping.md's 2-FER RULES 1-14 (the bot applies those).
   DATA: KPC-Data data/fers/<file>.json per region (kpc-fers-regions.json). SHOWN = status 'candidate' + passes [1,1,1] +
   REVIEWED (spot.reviewed, or kpc-fers-reviewed.json written by HQ). Members may tick 'waiting for review'. Hidden: saved outline
   only, not sure, dropped, merged stretches (same land, two park numbers = shown with that label) (drawn under their row). Members only:
   very tight list, missing-boundary list, rows with no public access within ~1 mile, 'how we checked'. Non-members never see a
   region whose public flag is false. Wording: 'POSSIBLE 2-FER' / 'POSSIBLE TRAIL OVERLAP', never 'is a 2-fer' / 'shared';
   GPS card 'By our maps you look inside both outlines', never 'you are in both parks'. FULL notice on the page, SHORT on every
   row, popup, GPS card and exported file. */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function j(u) { return fetch(u, { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }); }
  var SHORT = '⚠️ Possible POTA overlap only. We think these POTA parks\' boundaries may overlap here, but we can\'t confirm it. Check both official boundary maps and make your own call before you count it.';
  var YD = 1.09361, BAND = 30.48, COL = ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#56B4E9', '#8E6CEF', '#9A9A9A', '#F0E442', '#E69F00'];   /* Brandon Oct 27 3:04 PM: no gold/orange for the first parks: gold is the overlap */
  var DASH = ['', '12 6', '3 6', '12 6 3 6', '2 8', '18 6 4 6 4 6', '8 4', '1 5 9 5', '22 8'];
  var MEMBER = !window.KPCGate || KPCGate.member();
  function toast(t) { var e = $('ovToast'); e.textContent = t; e.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(function () { e.hidden = true; }, 4500); }
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }

  /* ---------- small geometry on [lon, lat] rings, in metres around a point ---------- */
  function mxy(lat0) { var kx = 111320 * Math.cos(lat0 * Math.PI / 180), ky = 110540; return { f: function (p) { return [p[0] * kx, p[1] * ky]; }, b: function (q) { return [q[0] / kx, q[1] / ky]; } }; }
  function pip(lon, lat, ring) { var c = false; for (var i = 0, k = ring.length - 1; i < ring.length; k = i++) { var a = ring[i], b = ring[k]; if ((a[1] > lat) !== (b[1] > lat) && lon < (b[0] - a[0]) * (lat - a[1]) / (b[1] - a[1]) + a[0]) c = !c; } return c; }
  function dseg(p, a, b) { var dx = b[0] - a[0], dy = b[1] - a[1], t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy || 1); t = Math.max(0, Math.min(1, t)); return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy); }
  function edgeM(lon, lat, pts, closed) { var P = mxy(lat), p = P.f([lon, lat]), m = 1e12; for (var i = 0; i < pts.length - 1 + (closed ? 1 : 0); i++) { var a = P.f(pts[i]), b = P.f(pts[(i + 1) % pts.length]); m = Math.min(m, dseg(p, a, b)); } return m; }
  function bandRing(line) {   /* the 100-ft zone along a line, as a ring */
    var P = mxy(line[0][1]), L = [], R = [], pts = line.map(P.f);
    for (var i = 0; i < pts.length; i++) { var a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)], dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1, nx = -dy / l, ny = dx / l;
      L.push(P.b([pts[i][0] + nx * BAND, pts[i][1] + ny * BAND])); R.unshift(P.b([pts[i][0] - nx * BAND, pts[i][1] - ny * BAND])); }
    return L.concat(R);
  }
  function miles(a, b, c, d) { var r = Math.PI / 180, x = Math.sin((c - a) * r / 2), y = Math.sin((d - b) * r / 2); return 2 * 3958.8 * Math.asin(Math.sqrt(x * x + Math.cos(a * r) * Math.cos(c * r) * y * y)); }

  /* ---------- data: regions → rows ---------- */
  var CFG = null, REV = {}, REG = null, ROWS = [], TIGHT = [], MISS = [], WAITN = 0, here = null, F = { big: true, small: true, trail: true, multi: false, near: false };
  function ok3(s) { return Array.isArray(s.passes) && s.passes.length >= 3 && s.passes.every(function (x) { return x === 1; }); }
  function reviewed(s) { return !!(s.reviewed || REV[s.id]); }
  function build(files, missing) {
    var all = [], kids = {};
    files.forEach(function (d) { (d && d.spots || []).forEach(function (s) { s._st = d.st || ''; all.push(s); }); });
    all.forEach(function (s) { var m = /^merged into one row: (.+)$/.exec(s.status || ''); if (m) (kids[m[1]] = kids[m[1]] || []).push(s); });
    var groups = {}; ROWS = []; TIGHT = []; WAITN = 0;
    all.forEach(function (s) {
      if (!ok3(s)) return;
      var st = String(s.status || '');
      if (/^very tight/.test(st)) { if (MEMBER) TIGHT.push(s); return; }
      if (st !== 'candidate') return;                                    // saved outline only / not sure / dropped / merged
      /* 'same land, two park numbers' = SHOWN with that label everywhere (final ruling, CLAUDE.md) */
      var noAcc = !s.access_pin || !s.access_pin.at;
      if (noAcc && !MEMBER) return;                                      // A9: members only
      var rev = reviewed(s); if (!rev) WAITN++;
      var key = s.refs.slice().sort().join('+');
      var g = groups[key] || (groups[key] = { key: key, refs: s.refs.slice().sort(function (x, y) { return +(/(\d+)$/.exec(x) || [0, 0])[1] - +(/(\d+)$/.exec(y) || [0, 0])[1]; }), names: {}, patches: [], st: s._st, trail: false });
      Object.assign(g.names, s.names || {}); s._kids = kids[s.id] || []; s._rev = rev; s._noAcc = noAcc;
      if (s.kind === 'trail') g.trail = true; g.patches.push(s);
    });
    Object.keys(groups).forEach(function (k) { var g = groups[k];
      g.patches.sort(function (a, b) { return size(b) - size(a); });
      g.n = g.refs.length; g.best = g.patches[0];
      ROWS.push(g); });
    MISS = MEMBER ? ((missing && missing.parks) || []) : [];
  }
  function size(s) { return s.kind === 'trail' ? (s.len_m || 0) / 1000 : (s.wide_m || 0); }
  function tierOf(s) { if (s.kind === 'trail') return 'trail'; var w = (s.wide_m || 0) * YD; return /small/.test(s.small || '') || (w && w < 100) ? 'small' : 'big'; }
  function visiblePatches(g) { var w = $('ovWait') && $('ovWait').checked && MEMBER; return g.patches.filter(function (s) { return s._rev || w; }); }

  /* ---------- the LIST ---------- */
  function tagOf(g) { return g.trail ? '<span class="ov-badge bg-trail">POSSIBLE TRAIL OVERLAP: WITHIN 100 FT OF THE TRAIL LINE</span>' : '<span class="ov-badge bg-n">POSSIBLE ' + g.n + '-FER</span>'; }
  function nm(g, r) { return (g.names && g.names[r]) || r; }
  function accLine(s) {
    var a = s.access_pin; if (!a || !a.at) return '<p class="ov-note">🅿️ <b>No public road or parking found within about a mile.</b> Plan your walk on the official map (members only until a person has looked at it).</p>';
    var acc = s.access && s.access.name ? ' Nearest official access point: ' + esc(s.access.name) + '.' : '';
    var generic = !a.name || /^public (road|path)$/i.test(a.name), yd = Math.round((a.walk_m || 0) * YD), what = a.from === 'road' ? (generic ? 'an unnamed public road' : esc(a.name) + ' (public road)') : a.from === 'path' ? (generic ? 'a public path' : esc(a.name) + ' (public path)') : esc(a.name || a.from) + ' (' + esc(a.from) + ')';
    return '<p class="ov-note">📍 Closest spot to public access: ' + (yd < 15 ? 'right beside <b>' + what + '</b>.' : 'about ' + yd + ' yards from <b>' + what + '</b>.') + acc +
      ' <a class="b" style="min-height:30px;padding:3px 10px;font-size:11px" target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination=' + a.at[0] + ',' + a.at[1] + '">DIRECTIONS TO THE CLOSEST PUBLIC ACCESS (NOT TO THE OVERLAP)</a></p>';
  }
  function sizeLine(g, ps) {
    var s = ps[0];
    if (g.trail) { var n = ps.reduce(function (t, x) { return t + (+x.stretches || 1); }, 0), km = ps.reduce(function (t, x) { return t + (x.len_m || 0); }, 0); return n + ' stretch' + (n > 1 ? 'es' : '') + ' of trail inside the park, about ' + (km / 1609).toFixed(1) + ' mi in all (the 100-ft band along the line is the zone)'; }
    return (ps.length > 1 ? ps.length + ' places, biggest first: ' : '') + 'fits a circle about <b>' + Math.round((s.wide_m || 0) * YD) + ' yards</b> across' + (s.acres ? ' · about ' + (+s.acres).toFixed(1) + ' acres' : '');
  }
  /* Brandon Oct 27 2:37 PM ('info says 6 places but only lists 1'): every place listed, biggest first, each with its size, access and a SHOW button */
  function placesHtml(g, ps) {
    return '<details class="ov-places"' + (ps.length <= 3 ? ' open' : '') + '><summary>▸ THE ' + ps.length + ' PLACES</summary><ol>' + ps.map(function (s, i) {
      var sz = s.kind === 'trail' ? (s.len_m ? 'about ' + Math.round(s.len_m * YD) + ' yards of trail' + (s.stretches > 1 ? ' in ' + s.stretches + ' stretches' : '') : 'trail stretch') : 'fits a circle about ' + Math.round((s.wide_m || 0) * YD) + ' yards across' + (s.acres ? ' · ' + (+s.acres).toFixed(1) + ' acres' : '');
      return '<li><b>Place ' + (i + 1) + '</b>: ' + sz + (tierOf(s) === 'small' ? ' · <i>small: tight fit</i>' : '') + (s._rev ? '' : ' · <i>waiting for review</i>') + ' <button type="button" class="ov-pl" data-place="' + esc(g.key) + '|' + i + '">🗺 SHOW</button>' + accLine(s) + '</li>'; }).join('') + '</ol></details>';
  }
  function rowHtml(g, ps) {
    var s = ps[0], small = ps.some(function (x) { return tierOf(x) === 'small'; }), wait = ps.some(function (x) { return !x._rev; });
    return '<div class="ov-row" data-row="' + esc(g.key) + '">' + tagOf(g) + (small ? '<span class="ov-badge bg-small">SMALL OVERLAP: TIGHT FIT, CHECK CAREFULLY</span>' : '') + (wait ? '<span class="ov-badge bg-wait">WAITING FOR REVIEW</span>' : '') +
      (s.label ? '<span class="ov-badge bg-off">' + esc(s.label.toUpperCase()) + '</span>' : '') +
      '<b class="t" style="margin-top:6px">' + g.refs.map(function (r) { return esc(r) + ' ' + esc(nm(g, r)); }).join(' + ') + '</b>' +
      '<span class="m">' + sizeLine(g, ps) + (here && g._mi != null ? ' · ' + Math.round(g._mi) + ' mi from you' : '') + '</span>' +
      '<p class="ov-note">Last checked ' + esc(s.checked || s.found || '') + '</p>' +
      '<div class="acts"><button type="button" data-open="' + esc(g.key) + '">🗺 SHOW ON THE MAP</button></div>' +
      /* Brandon Oct 27 2:48 PM: 'see more after the last checked date to reveal the other info' */
      '<details class="ov-more"><summary>▸ SEE MORE</summary>' + (ps.length > 1 ? placesHtml(g, ps) : accLine(s)) +
      (s.note ? '<p class="ov-note">ℹ️ ' + esc(s.note) + '</p>' : '') +
      '<p class="ov-note">Maps used: ' + esc(Object.keys(s.map_dates || {}).map(function (r) { return r + ' ' + s.map_dates[r]; }).join('; ') || 'see the official maps') + '</p>' +
      (MEMBER && (s.how_checked || s.ownership) ? '<p class="ov-how2">How we checked (members): ' + esc([s.how_checked, s.ownership, s.owner_here ? 'owner: ' + s.owner_here : ''].filter(Boolean).join(' · ')) + '</p>' : '') +
      '<div class="acts">' + (s.maps || []).map(function (m) { return '<a class="b" target="_blank" rel="noopener" href="' + esc(m[1]) + '">OFFICIAL MAP: ' + esc(m[0]) + '</a>'; }).join('') + '</div></details>' +
      '</div>';   /* Brandon Oct 27 3:04 PM: 'No need for a warning on every card' (one SHORT notice heads the list; popups + exports keep theirs) */
  }
  function numKey(g, k) { var n = g.refs.map(function (r) { return +(/(\d+)$/.exec(r) || [0, 0])[1]; }).sort(function (x, y) { return x - y; }); return n[k || 0] || 0; }
  function list() {
    var q = ($('ovQ').value || '').trim().toLowerCase(), out = [];
    ROWS.forEach(function (g) {
      var ps = visiblePatches(g); if (!ps.length) return;
      if (q && (g.refs.join(' ') + ' ' + Object.values(g.names).join(' ') + ' ' + ps.map(function (s) { return (s.access_pin && s.access_pin.name) || ''; }).join(' ')).toLowerCase().indexOf(q) < 0) return;
      if (g.trail ? !F.trail : !F[tierOf(ps[0])]) return; if (F.multi && g.n < 3) return;
      g._mi = here && ps[0].center ? miles(here[0], here[1], ps[0].center[0], ps[0].center[1]) : null;
      out.push([g, ps]);
    });
    /* Brandon Oct 27 2:48 PM: 'have list in order numerically' = by the lowest park number in each row (then the next one) */
    out.sort(F.near && here ? function (a, b) { return a[0]._mi - b[0]._mi; } : function (a, b) { return (a[0].st < b[0].st ? -1 : a[0].st > b[0].st ? 1 : 0) || numKey(a[0]) - numKey(b[0]) || numKey(a[0], 1) - numKey(b[0], 1); });
    var empty = '<div class="ov-empty"><b>We are still checking ' + esc(REG ? REG.label : 'these') + '\'s parks.</b> Nothing is listed yet. This does not mean there are no overlaps.' + (MEMBER && WAITN && !$('ovWait').checked ? '<br><br>Members: ' + WAITN + ' result' + (WAITN > 1 ? 's are' : ' is') + ' waiting for review. Tick the box below to see them (marked WAITING FOR REVIEW).' : '') + '</div>';
    $('ovList').innerHTML = out.length ? '<p class="ov-note">' + out.length + ' result' + (out.length > 1 ? 's' : '') + ' in ' + esc(REG.label) + '.</p><span class="ov-short" style="margin-bottom:8px">' + SHORT + '</span>' + out.map(function (x) { return rowHtml(x[0], x[1]); }).join('') : (q ? '<p class="ov-note">Nothing matches that search.</p>' : empty);
    $('ovWaitW').hidden = !(MEMBER && WAITN);
    $('ovTightB').hidden = !TIGHT.length; $('ovTight').innerHTML = TIGHT.map(function (s) { return '<div class="ov-row" style="cursor:default"><span class="ov-badge bg-tight">VERY TIGHT: COULD BE MAP ERROR, CHECK BOTH OFFICIAL MAPS ON THE GROUND</span><span class="ov-badge bg-mem">MEMBERS ONLY</span><b class="t">' + s.refs.map(function (r) { return esc(r) + ' ' + esc((s.names || {})[r] || ''); }).join(' + ') + '</b><span class="m">' + (s.wide_m ? 'about ' + Math.round(s.wide_m * YD) + ' yards across' : '') + '</span>' + accLine(s) + '</div>'; }).join('');
    $('ovMissB').hidden = !MISS.length; $('ovMiss').innerHTML = MISS.map(function (m) { return '<div class="ov-row" style="cursor:default"><span class="ov-badge bg-mem">MEMBERS FIRST</span><span class="ov-badge bg-wld">' + esc((m.note || 'Missing boundary: check the official map').toUpperCase()) + '</span><b class="t">' + esc(m.ref) + ' ' + esc(m.name) + '</b><p class="ov-note">' + esc(m.why || '') + (m.checked ? ' · checked ' + esc(m.checked) : '') + '</p></div>'; }).join('');
  }

  /* ---------- the MAP ---------- */
  var map = null, base = {}, gAll = null, cur = null, parks = [], step = 0, timer = null, gps = null, watch = null, lastIn = false, leftUntil = 0, mode = '', meas = [], pinM = null, layerName = 'street';
  function mkMap() {
    if (map || !window.L) return !!map;
    map = L.map('ovMap', { zoomControl: true }).setView([37.5, -85.3], 7);
    /* Oct 27 (Brandon: 'add the map layers'): the site's usual layer menu (Street, Satellite, Satellite + streets, USGS Topo, Terrain,
       Hillshade, official PAD-US boundaries) from kpc-map-tools.js, top right of the map; the STREET / SATELLITE / TOPO buttons stay as shortcuts */
    if (window.KPCLayers) { try { KPCLayers(map, 'Satellite + streets'); } catch (e) {} }   /* Brandon: default = satellite + streets */
    base.street = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' });
    base.sat = L.layerGroup([L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, attribution: 'Imagery © Esri' }), L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19 }), L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19 })]);
    base.topo = L.tileLayer('https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}', { maxZoom: 16, attribution: 'USGS The National Map' });
    map.on('baselayerchange', function (e) { baseNow = e.name || ''; draw(); });
    if (!window.KPCLayers) base.street.addTo(map); gAll = L.layerGroup().addTo(map);
    if (window.KPCLocate) { try { KPCLocate(map); } catch (e) {} } if (window.KPCFull) { try { KPCFull(map); } catch (e) {} }
    map.on('click', function (e) { if (mode === 'pin') { if (pinM) map.removeLayer(pinM); status([e.latlng.lat, e.latlng.lng], 0, true);
        pinM = L.marker(e.latlng, { icon: L.divIcon({ className: '', html: '<span style="display:block;width:26px;height:26px;border-radius:50% 50% 50% 0;background:#d0312d;border:3px solid #fff;transform:rotate(-45deg);box-shadow:0 2px 6px #0007"></span>', iconSize: [26, 26], iconAnchor: [13, 30] }) }).addTo(map)
          .bindPopup($('ovGps').innerHTML, { maxWidth: 280 }).openPopup(); }
      else if (mode === 'measure') { meas.push(e.latlng); if (meas.length > 2) meas = [e.latlng]; draw(); if (meas.length === 2) { var d = map.distance(meas[0], meas[1]); L.popup().setLatLng(meas[1]).setContent('<b>📏 ' + Math.round(d * YD) + ' yards</b> (' + Math.round(d * 3.28084) + ' ft) in a straight line').openOn(map); } } });
    return true;
  }
  function setBase(n) { if (!map) return; map.eachLayer(function (l) { if (l instanceof L.TileLayer && !gAll.hasLayer(l)) map.removeLayer(l); }); Object.keys(base).forEach(function (k) { if (map.hasLayer(base[k])) map.removeLayer(base[k]); }); base[n].addTo(map); layerName = n; tools(); }
  function patchRings(g) { var out = []; visiblePatches(g).forEach(function (s) { [s].concat(s._kids || []).forEach(function (x) { if (x.shape && x.shape.length > 1) out.push({ s: x, ring: x.kind === 'trail' ? bandRing(x.shape) : x.shape, line: x.kind === 'trail' ? x.shape : null }); }); }); return out; }
  function openRow(key) {
    var g = ROWS.filter(function (r) { return r.key === key; })[0]; if (!g) return;
    showTab('map'); if (!mkMap()) { $('ovSpot').innerHTML = '<p class="ov-note">The map could not load (no signal?). The list still works.</p>'; return; }
    cur = g; stopGps(); meas = []; lastIn = false; leftUntil = 0; if (pinM) { map.removeLayer(pinM); pinM = null; }
    cur.rings = patchRings(g); parks = g.refs.map(function (r, i) { return { ref: r, n: i + 1, c: COL[i], dash: DASH[i], on: true, fs: null }; });
    spotPanel(); legend(); mapKey(); step = 0; clearTimeout(timer);
    var b = L.latLngBounds([]); cur.rings.forEach(function (x) { x.ring.forEach(function (p) { b.extend([p[1], p[0]]); }); });
    /* the map was hidden in the LIST tab (size 0), so Leaflet fitted to nothing and showed the whole world: size it first, fit again once shown */
    cur.fit = b;
    if (b.isValid()) { map.invalidateSize(); map.fitBounds(b.pad(0.25), { maxZoom: 17, animate: false }); setTimeout(function () { if (cur === g) { map.invalidateSize(); map.fitBounds(b.pad(0.25), { maxZoom: 17, animate: false }); } }, 120); }
    try { history.replaceState(null, '', '?region=' + encodeURIComponent(REG.id) + '&id=' + encodeURIComponent(key)); } catch (e) {}
    $('ovReport').href = reportUrl(g);
    loadOutlines(g).then(function () { if (cur !== g) return; animate(); });
    draw();
  }
  function openPlace(key, i) {
    if (!cur || cur.key !== key) openRow(key); else showTab('map');
    var s = visiblePatches(cur)[i]; if (!s || !map) return;
    var b = L.latLngBounds([]); [s].concat(s._kids || []).forEach(function (x) { (x.shape || []).forEach(function (q) { b.extend([q[1], q[0]]); }); });
    setTimeout(function () { if (b.isValid()) map.fitBounds(b.pad(0.4), { maxZoom: 17 }); }, cur.key === key ? 0 : 400);
    scrollTo({ top: $('ovMap').getBoundingClientRect().top + scrollY - 100, behavior: 'smooth' });
  }
  function loadOutlines(g) {
    var B = window.KPCB; if (!B) return Promise.resolve();
    return Promise.all(parks.map(function (p) {
      var trailPatch = g.patches.some(function (s) { return s.kind === 'trail' && s.line_source && s.line_source[p.ref]; });
      if (trailPatch) { p.line = true; return null; }   // a line park: its zone is the 100-ft band, drawn from the patch itself
      var ky = /^US-/.test(p.ref) && (g.st === 'KY' || /KY/.test(g.st));
      var pr = ky && B.kyFor ? B.kyFor(p.ref) : B.usOutline ? B.usOutline(p.ref, nm(g, p.ref), g.best.center[0], g.best.center[1], [String(g.st || '').replace(/^US-/, '')]).then(function (o) { return o && o.fs; }) : Promise.resolve(null);
      return Promise.resolve(pr).then(function (fs) { p.fs = (fs || []).filter(function (f) { return f && f.geometry; }); }).catch(function () { p.fs = []; });
    }));
  }
  /* Brandon Oct 27 2:22 PM: 'slow down the animation': each park fades in over ~1.6 s, 3 s apart, then the overlap patch fades in */
  var fading = false;
  function animate() { step = 0; draw(); (function next() { timer = setTimeout(function () { step++; fading = true; draw(); setTimeout(function () { fading = false; }, 2000); if (step <= parks.length) next(); }, step ? 3000 : 900); })(); }
  /* Brandon Oct 27 2:37 PM ('Daniel Boone forest hard to tell the boundaries … lightly shade out private land, land not a park'): one light grey
     veil per park over everything that is NOT that park (holes = the park's own land, inholdings stay grey). Outside both = darker,
     inside one park = lighter, inside both = clear (+ gold). Daniel Boone's outline is Forest Service-OWNED land, so private land shows grey. */
  var shade = true;
  /* Brandon Oct 27 2:48 PM ('shading good on open source but no private shading on other layers'): stronger on satellite / topo */
  var baseNow = 'Satellite + streets';
  function veilOp() { return /satellite|topo|terrain/i.test(baseNow) ? 0.38 : 0.2; }
  function veil(p) {
    var B = window.KPCB, rings = [];
    if (p.line) cur.rings.forEach(function (x) { if (x.line) rings.push(x.ring); });
    else (p.fs || []).forEach(function (f) { try { (B && B.ringsOf ? B.ringsOf(f.geometry) : []).forEach(function (poly) { poly.forEach(function (r) { rings.push(r); }); }); } catch (e) {} });
    if (!rings.length) return null;
    var c = map.getCenter(), box = [[c.lat - 3, c.lng - 4], [c.lat - 3, c.lng + 4], [c.lat + 3, c.lng + 4], [c.lat + 3, c.lng - 4]];
    return L.polygon([box].concat(rings.map(function (r) { return r.map(function (q) { return [q[1], q[0]]; }); })), { stroke: false, fillColor: '#000', fillOpacity: veilOp(), interactive: false, fillRule: 'evenodd' });
  }
  function draw() {
    if (!map || !cur) return; gAll.clearLayers();
    var act = !mode;   /* in pin / measure mode the shapes let the tap through to the map */
    if (shade && step > 0) parks.forEach(function (p, i) { if (!p.on || i >= step) return; var v = veil(p); if (v) gAll.addLayer(v); });
    parks.forEach(function (p, i) {
      if (!p.on || i >= step) return;
      var cls = fading && i === step - 1 ? 'ov-in' : '';
      (p.fs || []).forEach(function (f) { gAll.addLayer(L.geoJSON(f, { style: { color: p.c, weight: 3, dashArray: p.dash, fillColor: p.c, fillOpacity: shade ? 0 : 0.08, className: cls }, interactive: act }).bindPopup(parkPop(p))); });
      if (p.line) cur.rings.forEach(function (x) { if (x.line) { gAll.addLayer(L.polygon(x.ring.map(function (q) { return [q[1], q[0]]; }), { color: p.c, weight: 1, fillColor: p.c, fillOpacity: 0.18, dashArray: '4 4', className: cls, interactive: act }).bindPopup(parkPop(p)));
        gAll.addLayer(L.polyline(x.line.map(function (q) { return [q[1], q[0]]; }), { color: p.c, weight: 3, dashArray: p.dash, className: cls })); } });
    });
    if (step > parks.length) cur.rings.forEach(function (x) {
      gAll.addLayer(L.polygon(x.ring.map(function (q) { return [q[1], q[0]]; }), { color: '#b8860b', weight: 2, fillColor: '#ffd34d', fillOpacity: 0.6, className: fading ? 'ov-in-patch' : '', interactive: act }).bindPopup(patchPop(x.s)));
    });
    parks.forEach(function (p, i) { if (i >= step || !p.on) return; var c = (p.fs && p.fs[0] && L.geoJSON(p.fs[0]).getBounds().getCenter()) || (cur.rings[0] && L.latLng(cur.rings[0].ring[0][1], cur.rings[0].ring[0][0]));
      if (c) gAll.addLayer(L.marker(c, { icon: L.divIcon({ className: '', html: '<span class="ov-plab" style="border-color:' + p.c + '"><span class="ov-num" style="background:' + p.c + '">' + p.n + '</span>' + esc(p.ref) + '</span>', iconSize: null, iconAnchor: [14, 14] }) }).bindPopup(parkPop(p))); });
    var pins = []; visiblePatches(cur).forEach(function (s) { [s.access_pin].concat(s.pins || []).forEach(function (a) { if (a && a.at && pins.length < 3 && !pins.some(function (q) { return q.at[0] === a.at[0] && q.at[1] === a.at[1]; })) pins.push(a); }); });
    pins.forEach(function (a) { gAll.addLayer(L.marker(a.at, { icon: L.divIcon({ className: '', html: '<span style="display:inline-grid;place-items:center;width:24px;height:24px;border-radius:5px;background:#1d4d7a;color:#fff;border:2px solid #fff;font:900 14px Arial">P</span>', iconSize: [24, 24], iconAnchor: [12, 12] }) })
      .bindPopup('<b>Closest spot to public access</b><br>' + esc(a.name || '') + ' (' + esc(a.from || '') + '), about ' + Math.round((a.walk_m || 0) * YD) + ' yards from it.<br><small>' + esc(a.note || '') + '</small><br><a target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination=' + a.at[0] + ',' + a.at[1] + '">Directions (to the access, not to the overlap)</a><span class="ov-short">' + SHORT + '</span>')); });
    if (meas.length) { gAll.addLayer(L.polyline(meas, { color: '#d55e00', weight: 3 })); meas.forEach(function (m) { gAll.addLayer(L.circleMarker(m, { radius: 5, color: '#d55e00' })); }); }
    if (gps) { gAll.addLayer(L.circle(gps.p, { radius: gps.acc / YD, color: '#1e78ff', weight: 1, fillOpacity: 0.15 })); gAll.addLayer(L.circleMarker(gps.p, { radius: 7, color: '#fff', weight: 3, fillColor: '#1e78ff', fillOpacity: 1 })); }
  }
  function parkPop(p) { var s = cur.best, m = (s.maps || []).filter(function (x) { return x[0] === p.ref; })[0];
    return '<span class="ov-num" style="background:' + p.c + ';display:inline-grid;width:22px;height:22px;border-radius:50%;place-items:center;font-weight:900">' + p.n + '</span> <b>' + esc(p.ref) + ' · ' + esc(nm(cur, p.ref)) + '</b>' + (p.line ? '<br>A line park: the band = POTA\'s 100 ft from the line.' : '') +
      '<br>' + (m ? '<a target="_blank" rel="noopener" href="' + esc(m[1]) + '">Official map</a> · ' : '') + '<a target="_blank" rel="noopener" href="https://pota.app/#/park/' + esc(p.ref) + '">POTA page</a><span class="ov-short">' + SHORT + '</span>'; }
  function patchPop(s) { return '<b>' + (s.kind === 'trail' ? 'Possible trail overlap (100-ft band)' : 'Possible overlap patch') + '</b><br>' + (s.wide_m ? 'Fits a circle about ' + Math.round(s.wide_m * YD) + ' yards across' + (s.acres ? ' · ' + (+s.acres).toFixed(1) + ' acres' : '') + '<br>' : s.len_m ? 'About ' + Math.round(s.len_m * YD) + ' yards of trail<br>' : '') +
    'Last checked ' + esc(s.checked || '') + (s._rev ? '' : '<br><b style="color:#a3271a">WAITING FOR REVIEW</b>') + '<span class="ov-short">' + SHORT + '</span>'; }
  function spotPanel() {
    var g = cur, ps = visiblePatches(g); $('ovSpot').innerHTML = rowHtml(g, ps).replace('class="ov-row"', 'class="ov-row" style="cursor:default;border:0;padding:0"').replace(/<button type="button" data-open="[^"]*">[^<]*<\/button>/, '') + '<p class="ov-note">One log per park (POTA): upload a log for each park number.</p>';
  }
  /* Brandon Oct 27 2:26 PM ('show park number layer 1 and other park 2 … is the shading only the overlap?'): a key ON the map:
     each park's number badge + park number + its line style, and what the shading means */
  var keyCtl = null;
  function mapKey() {
    if (!map || !L.Control) return;
    if (!keyCtl) { var K = L.Control.extend({ options: { position: 'bottomleft' }, onAdd: function () { var d = L.DomUtil.create('div', 'ov-mkey'); L.DomEvent.disableClickPropagation(d); return d; } }); keyCtl = new K(); keyCtl.addTo(map); }
    var el = keyCtl.getContainer(); if (!el) return;
    var open = store('kpcOvKey') !== '0';
    el.innerHTML = '<button type="button" class="ov-kh" data-key>' + (open ? '▾ KEY (HIDE)' : '▸ KEY') + '</button>' + (open ? '<div class="ov-kb">' : '<div class="ov-kb" hidden>') + parks.map(function (p) { return '<div><span class="ov-num" style="background:' + p.c + '">' + p.n + '</span><svg width="26" height="8" aria-hidden="true"><path d="M1 4h24" stroke="' + p.c + '" stroke-width="4" stroke-dasharray="' + p.dash + '"/></svg><b>' + esc(p.ref) + '</b> ' + esc(nm(cur, p.ref)) + (p.line ? ' (100-ft band)' : '') + '</div>'; }).join('') +
      (shade ? '<div><span class="ov-sw" style="background:#2b2b2b;opacity:.45"></span>darker grey = in neither park (private or other land)</div><div><span class="ov-sw" style="background:#2b2b2b;opacity:.22"></span>light grey = inside only one park</div>' : '<div><span class="ov-sw" style="background:' + (parks[0] ? parks[0].c : '#999') + ';opacity:.3"></span>light tint in a park\'s colour = inside that park</div>') +
      '<div><span class="ov-sw" style="background:#ffd34d;border:2px solid #b8860b"></span><b>gold = inside both parks: where our maps suggest they may overlap</b></div></div>';
    var kb = el.querySelector('[data-key]'); if (kb) kb.onclick = function (e) { e.preventDefault(); store('kpcOvKey', open ? '0' : '1'); mapKey(); };
  }
  function legend() { $('ovLeg').innerHTML = parks.map(function (p, i) { return '<li><span class="ov-num" style="background:' + p.c + '">' + p.n + '</span><svg width="34" height="10" aria-hidden="true"><path d="M2 5h30" stroke="' + p.c + '" stroke-width="4" stroke-dasharray="' + p.dash + '"/></svg><label><input type="checkbox" data-on="' + i + '"' + (p.on ? ' checked' : '') + '> <b>' + esc(p.ref) + '</b> ' + esc(nm(cur, p.ref)) + (p.line ? ' <i>(line: 100-ft band)</i>' : '') + '</label></li>'; }).join(''); }

  /* ---------- GPS walk-in / dropped pin ---------- */
  function status(p, acc, isPin) {
    if (!cur) return; var lat = p[0], lon = p[1], g = $('ovGps'), cls = 'out', t = '', body = '', who = isPin ? 'the pin' : 'you', look = isPin ? ' looks' : ' look';
    var inPatch = null, dPatch = 1e12; cur.rings.forEach(function (x) { var inn = pip(lon, lat, x.ring), d = edgeM(lon, lat, x.ring, true); if (inn && !inPatch) inPatch = x; dPatch = Math.min(dPatch, d); });
    var B = window.KPCB, n = parks.length, ins = parks.map(function (q) { if (q.line) return cur.rings.some(function (x) { return x.line && pip(lon, lat, x.ring); }); if (!q.fs || !q.fs.length || !B) return null; return q.fs.some(function (f) { return B.inside(lat, lon, f.geometry); }); });
    var known = ins.filter(function (x) { return x !== null; }).length, k = ins.filter(Boolean).length, accM = acc / YD;
    if (inPatch) {
      if (accM > dPatch) { cls = 'edge'; t = '⚠️ TOO CLOSE TO THE EDGE TO TELL'; body = 'GPS is good to about ±' + Math.round(acc) + ' yards and the edge of the lit patch is ' + Math.round(dPatch * YD) + ' yards away. Step farther in; we never guess.'; }
      else { cls = 'in'; t = '✅ By our maps ' + who + look + ' inside ' + (n === 2 ? 'both outlines' : 'all ' + n + ' outlines'); var s = inPatch.s;
        body = 'About ' + Math.round(dPatch * YD) + ' yards to the edge of the lit patch.' + (s.wide_m ? ' Patch ' + Math.round(s.wide_m * YD) + ' yards across.' : '') + ' Last checked ' + esc(s.checked || '') + '.<br><b>Keep your whole station inside the lit patch: radio, antenna, operator.</b> POTA decides, not KPC.'; }
      if (!isPin) { lastIn = true; leftUntil = 0; }
    } else {
      if (!isPin && (lastIn || Date.now() < leftUntil)) { if (lastIn) { leftUntil = Date.now() + 4000; try { navigator.vibrate && navigator.vibrate([200, 100, 200]); } catch (e) {} } lastIn = false; cls = 'left'; t = '🚨 You left the overlap'; body = 'By our maps you are outside the lit patch now (about ' + Math.round(dPatch * YD) + ' yards from it). Step back in.'; }
      else if (accM > dPatch && dPatch < 200) { cls = 'edge'; t = '⚠️ TOO CLOSE TO THE EDGE TO TELL'; body = 'GPS ±' + Math.round(acc) + ' yards, the lit patch is ' + Math.round(dPatch * YD) + ' yards away.'; }
      else if (known && k > 0) { cls = 'one'; var inN = parks.filter(function (q, i) { return ins[i]; }), outN = parks.filter(function (q, i) { return ins[i] === false; });
        t = '🟡 By our maps ' + who + look + ' inside ' + (n === 2 ? inN.map(function (q) { return esc(q.ref); }).join('') : k + ' of ' + n + ' outlines'); body = (outN.length ? 'Not inside: ' + outN.map(function (q) { return esc(q.ref); }).join(', ') + '. ' : '') + 'The lit patch is about ' + Math.round(dPatch * YD) + ' yards away.'; }
      else { t = '📍 Outside ' + (n === 2 ? 'both outlines' : 'the outlines') + (known < n ? ' (as far as our maps show)' : ''); body = 'The lit patch is about ' + Math.round(dPatch * YD) + ' yards away. Use the closest public access (P on the map).'; }
    }
    g.className = 'ov-gps ' + cls; g.innerHTML = '<b class="st">' + t + '</b><span>' + body + '</span><span class="ov-short">' + SHORT + '</span>' + (isPin ? '' : '<p class="ov-note">GPS ±' + Math.round(acc) + ' yards · your location stays on this device</p>');
  }
  function startGps() {
    if (!navigator.geolocation) { toast('This browser cannot give a location.'); return; }
    stopGps(); watch = navigator.geolocation.watchPosition(function (pos) { gps = { p: [pos.coords.latitude, pos.coords.longitude], acc: (pos.coords.accuracy || 50) * YD }; draw(); status(gps.p, gps.acc, false); },
      function (e) { toast(e.code === 1 ? 'Location is blocked for this page.' : 'Could not get your location.'); stopGps(); }, { enableHighAccuracy: true, maximumAge: 2000, timeout: 30000 });
    tools();
  }
  function stopGps() { if (watch != null && navigator.geolocation) navigator.geolocation.clearWatch(watch); watch = null; gps = null; tools(); }

  /* ---------- export, share, offline, report ---------- */
  function fileOut(kind) {
    var g = cur; if (!g) return; var nmx = g.refs.join('+'), desc = esc(g.refs.map(function (r) { return r + ' ' + nm(g, r); }).join(' + ')) + ' · ' + esc(SHORT);
    var s = '';
    if (kind === 'gpx') { s = '<?xml version="1.0" encoding="UTF-8"?>\n<gpx version="1.1" creator="KPC Park Overlap Finder" xmlns="http://www.topografix.com/GPX/1/1">\n<metadata><name>' + esc(nmx) + '</name><desc>' + desc + '</desc></metadata>\n' +
      g.rings.map(function (x, i) { return '<trk><name>' + esc(nmx) + ' patch ' + (i + 1) + '</name><desc>' + desc + '</desc><trkseg>' + x.ring.concat([x.ring[0]]).map(function (p) { return '<trkpt lat="' + p[1] + '" lon="' + p[0] + '"/>'; }).join('') + '</trkseg></trk>'; }).join('\n') +
      visiblePatches(g).filter(function (x) { return x.access_pin && x.access_pin.at; }).map(function (x) { return '\n<wpt lat="' + x.access_pin.at[0] + '" lon="' + x.access_pin.at[1] + '"><name>Closest spot to public access</name><desc>' + desc + '</desc></wpt>'; }).join('') + '\n</gpx>\n'; }
    else { s = '<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>' + esc(nmx) + '</name><description>' + desc + '</description>\n' +
      g.rings.map(function (x, i) { return '<Placemark><name>' + esc(nmx) + ' patch ' + (i + 1) + '</name><description>' + desc + '</description><Polygon><outerBoundaryIs><LinearRing><coordinates>' + x.ring.concat([x.ring[0]]).map(function (p) { return p[0] + ',' + p[1]; }).join(' ') + '</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>'; }).join('\n') + '\n</Document></kml>\n'; }
    var a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([s], { type: kind === 'gpx' ? 'application/gpx+xml' : 'application/vnd.google-earth.kml+xml' })); a.download = 'KPC-overlap-' + nmx + '.' + kind; document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }
  function reportUrl(g) {
    var u = 'https://docs.google.com/forms/d/e/1FAIpQLScnnwJnLgdhqRb1k-Z4efvMDUNHmVjGWzIDgR8eWyJKxBPDJQ/viewform';
    return u + '?usp=pp_url&entry.1939220235=' + encodeURIComponent('Report a problem') + '&entry.1238884486=' + encodeURIComponent(g.refs.join(' + ') + ' (Park Overlap Finder)');
  }

  /* ---------- tabs, tools, wiring ---------- */
  function showTab(t) { var m = t === 'map'; $('ovMapTab').hidden = !m; $('ovListTab').hidden = m; [].forEach.call(document.querySelectorAll('#ov [data-tab]'), function (x) { var on = x.dataset.tab === t; x.classList.toggle('on', on); x.setAttribute('aria-selected', String(on)); }); if (m && map) setTimeout(function () { map.invalidateSize(); }, 50); }
  function tools() { [].forEach.call(document.querySelectorAll('#ovTools [data-t]'), function (b) { var t = b.dataset.t; if (/^(street|sat|topo)$/.test(t)) b.classList.toggle('on', t === layerName); if (t === 'pin' || t === 'measure') b.classList.toggle('on', mode === t); if (t === 'gps') b.classList.toggle('on', watch != null); if (t === 'shade') b.classList.toggle('on', shade); }); }
  document.addEventListener('click', function (e) {
    var pl = e.target.closest('#ov [data-place]');
    if (pl) { e.preventDefault(); var kk = pl.dataset.place.split('|'); openPlace(kk[0], +kk[1]); return; }
    var b = e.target.closest('#ov [data-tab], #ov [data-open], #ov [data-row], #ov [data-t], #ov [data-f], #ov [data-on], #ovAllOn, #ovAllOff, #ov [data-region]'); if (!b) return;
    if (b.matches('[data-on]')) { parks[+b.dataset.on].on = b.checked; draw(); return; }
    if (b.matches('[data-row]') && e.target.closest('a,button')) return;
    e.preventDefault();
    if (b.matches('[data-tab]')) { showTab(b.dataset.tab); if (b.dataset.tab === 'map' && !cur && ROWS.length) { var first = ROWS.filter(function (g) { return visiblePatches(g).length; })[0]; if (first) openRow(first.key); else mkMap(); } return; }
    if (b.matches('[data-open]') || b.matches('[data-row]')) { openRow(b.dataset.open || b.dataset.row); scrollTo({ top: $('ovMap').getBoundingClientRect().top + scrollY - 100, behavior: 'smooth' }); return; }
    if (b.matches('[data-region]')) { loadRegion(b.dataset.region); return; }
    if (b.id === 'ovAllOn' || b.id === 'ovAllOff') { parks.forEach(function (p) { p.on = b.id === 'ovAllOn'; }); legend(); draw(); return; }
    if (b.matches('[data-f]')) { var f = b.dataset.f;
      if (f === 'near') { if (F.near) { F.near = false; b.classList.remove('on'); $('ovNearNote').hidden = true; list(); return; }
        if (!navigator.geolocation) { toast('This browser cannot give a location.'); return; }
        navigator.geolocation.getCurrentPosition(function (pos) { here = [pos.coords.latitude, pos.coords.longitude]; F.near = true; b.classList.add('on'); $('ovNearNote').hidden = false; list(); }, function () { toast('Location not shared, so the list stays by state.'); }, { timeout: 15000, maximumAge: 300000 }); return; }
      F[f] = !F[f]; b.setAttribute('aria-pressed', String(F[f])); list(); return; }
    var t = b.dataset.t; if (!cur && t !== 'street' && t !== 'sat' && t !== 'topo') { toast('Pick a result first.'); return; }
    if (t === 'replay') { clearTimeout(timer); animate(); }
    else if (t === 'all') { clearTimeout(timer); step = parks.length + 1; draw(); }
    else if (t === 'shade') { shade = !shade; draw(); mapKey(); }
    else if (t === 'gps') { if (watch != null) stopGps(); else startGps(); }
    else if (t === 'pin' || t === 'measure') { mode = mode === t ? '' : t; meas = []; draw(); toast(mode === 'pin' ? 'Tap the map to drop a pin.' : mode === 'measure' ? 'Tap two places on the map.' : 'Done.'); }
    else if (t === 'sv') { var c = cur.best.access_pin && cur.best.access_pin.at || cur.best.center; window.open('https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=' + c[0] + ',' + c[1], '_blank', 'noopener'); }
    else if (t === 'share') { var u = location.origin + location.pathname + '?region=' + encodeURIComponent(REG.id) + '&id=' + encodeURIComponent(cur.key); try { navigator.clipboard.writeText(u + '\n' + SHORT); } catch (x) {} toast('Link copied (with the overlap notice).'); }
    else if (t === 'gpx' || t === 'kml') fileOut(t);
    else if (t === 'save') { var until = Date.now() + 30 * 864e5; try { localStorage.setItem('kpcOvSave-' + REG.id, JSON.stringify({ until: until, files: SAVED[REG.id] })); toast('Saved for offline until ' + new Date(until).toDateString() + '. It refreshes when you are back online and expires after 30 days, so old boundaries are never used.'); } catch (x) { toast('This phone has no room to save it.'); } }
    tools();
  });
  $('ovQ').addEventListener('input', function () { showTab('list'); list(); });
  $('ovWait').addEventListener('change', list);

  var SAVED = {};
  function loadRegion(id) {
    REG = CFG.regions.filter(function (r) { return r.id === id; })[0] || CFG.regions[0]; store('kpcOvRegion', REG.id); cur = null;
    [].forEach.call(document.querySelectorAll('#ov [data-region]'), function (x) { x.classList.toggle('on', x.dataset.region === REG.id); });
    $('ovList').innerHTML = '<p class="ov-note">Loading ' + esc(REG.label) + '…</p>';
    var base = CFG.base || '../KPC-Data/data/fers/';
    return Promise.all(REG.files.map(function (f) { return j(base + f + '.json'); }).concat([REG.missing && MEMBER ? j(base + REG.missing + '.json') : null])).then(function (a) {
      var files = a.slice(0, REG.files.length), miss = a[REG.files.length];
      if (files.some(function (x) { return !x; })) {   // offline: a saved copy that has not expired
        var sv = null; try { sv = JSON.parse(localStorage.getItem('kpcOvSave-' + REG.id) || 'null'); } catch (e) {}
        if (sv && sv.until > Date.now() && sv.files) { files = sv.files; toast('Offline: showing your saved copy (good until ' + new Date(sv.until).toDateString() + ').'); }
        else { $('ovList').innerHTML = '<div class="ov-empty"><b>Could not load the overlap list right now.</b> Nothing is shown rather than an old or guessed list. Try again with a signal.</div>'; return; }
      }
      SAVED[REG.id] = files; build(files, miss);
      if (MEMBER && REG.showWaiting) $('ovWait').checked = true;   // Brandon Oct 27 2:15 PM: 'members only … good with putting KY list on there for now to test it'
      list();
      var q = new URLSearchParams(location.search).get('id'); if (q && ROWS.some(function (r) { return r.key === q; })) openRow(q);
    });
  }
  Promise.all([j('kpc-fers-regions.json'), j('kpc-fers-reviewed.json')]).then(function (a) {
    CFG = a[0] || { regions: [] }; REV = (a[1] && a[1].reviewed) || {};
    CFG.regions = (CFG.regions || []).filter(function (r) { return r.public || MEMBER; });
    if (!CFG.regions.length) { $('ovList').innerHTML = '<div class="ov-empty"><b>We are still checking the parks.</b> Nothing is listed yet. This does not mean there are no overlaps.</div>'; return; }
    $('ovRegions').innerHTML = CFG.regions.length > 1 ? '<b>REGION</b>' + CFG.regions.map(function (r) { return '<button type="button" data-region="' + esc(r.id) + '">' + esc(r.label) + (r.public ? '' : ' 🔒') + '</button>'; }).join('') : '<b>REGION: ' + esc(CFG.regions[0].label.toUpperCase()) + (CFG.regions[0].public ? '' : ' 🔒 MEMBERS ONLY') + '</b>';
    var q = new URLSearchParams(location.search).get('region'), want = q || store('kpcOvRegion');
    loadRegion(CFG.regions.some(function (r) { return r.id === want; }) ? want : CFG.regions[0].id);
  });
  window.KPCOverlap = { rows: function () { return ROWS; }, openRow: openRow, status: status };
})();
