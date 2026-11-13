/* KPC MAP PLACER (Nov 11 2026, KPC owner, 2026-11-11). Members only, beta, not linked from any menu.
   Place a park's saved PICTURE map by hand: click the same spot on the picture (left) and on a USGS map (right), pair after pair;
   the page fits the picture onto the ground (similarity: scale, turn, shift), shows each pair's error, the leave-one-out error and
   every gate in plain words, then the person traces the boundary or trail on the picture and the page shows it on the real map.
   SAVE gives one "click set" JSON. Nothing is sent anywhere: the KPC-Data checker (.github/scripts/draft/kpc_hand_place.py)
   re-computes it all and writes the approximate trace. The maths is kpc-map-placer-math.js (no DOM). Pins never move. */
(function () {
  'use strict';
  var VERSION = 'kpc-map-placer.js 1.0 (2026-11-11)';
  var M = window.KPCPlaceMath, $ = function (id) { return document.getElementById(id); };
  var RAW = 'https://raw.githubusercontent.com/KentuckyPortableClub/KPC-Data/picture-maps/';
  var LOOK_ONLY = { osm: { name: 'OpenStreetMap (look only: points cannot be placed on it)', url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png', attr: '&copy; OpenStreetMap contributors' } };
  var ST = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'];
  var PROV = ['AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT'];
  var S = { ref: null, park: null, row: null, pic: null, pairs: [], pending: null, mode: 'pairs', shape: { kind: 'area', px: [] }, fit: null, gates: [], base: 'usgs-topo' };
  var pmap = null, rmap = null, picLayer = null, baseLayers = {}, gP = null, gR = null, ghost = null, INDEX = null;

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function say(t, bad) { var e = $('mpSay'); if (e) { e.textContent = t; e.className = 'mp-say' + (bad ? ' bad' : ''); } }
  function r2(v) { return Math.round(v * 100) / 100; }
  function r7(v) { return Math.round(v * 1e7) / 1e7; }
  function j(u) { return fetch(u, { cache: 'no-cache' }).then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status + ' for ' + u); return r.json(); }); }
  function dj(p) { return (window.KPC && KPC.dataUrl ? KPC.dataUrl(p) : fetch(p)).then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }); }
  function today() { var d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
  function hex(buf) { return Array.prototype.map.call(new Uint8Array(buf), function (x) { return x.toString(16).padStart(2, '0'); }).join(''); }

  /* ------------------------------------------------------------ park list: picture-maps index x POTA park list of the state */
  function index() { return INDEX || (INDEX = j(RAW + 'index.json').then(function (d) { return (d && d.maps) || d || []; })); }
  function parksOf(st) {
    if (st === 'KY') return j('kpc-ky-data.json').then(function (d) { var o = {}; ((d && d.parks) || []).forEach(function (p) { o[p.c] = { name: p.n, type: p.t || '', pin: [+p.la, +p.lo], src: 'kpc-ky-data.json' }; }); return o; });
    var ca = /^CA-/.test(st), f = ca ? 'data/parkinfo/CA.json' : 'data/parkinfo/US-' + st + '.json';
    return dj(f).then(function (d) { var o = {}; Object.keys((d && d.parks) || {}).forEach(function (r) { var a = d.parks[r]; if (ca && a[10] !== st.slice(3)) return; o[r] = { name: a[0], type: a[2] || '', pin: [+a[5], +a[6]], src: f }; }); return o; });
  }
  function fillStates() {
    var s = $('mpSt'); if (!s) return;
    s.innerHTML = '<option value="">State or province</option>' + ST.map(function (x) { return '<option value="' + x + '">' + x + '</option>'; }).join('') + PROV.map(function (x) { return '<option value="CA-' + x + '">Canada ' + x + '</option>'; }).join('');
  }
  function listParks() {
    var st = $('mpSt').value, sel = $('mpPark'); if (!st) return Promise.resolve();
    sel.innerHTML = '<option>Loading…</option>';
    return Promise.all([index(), parksOf(st)]).then(function (a) {
      var rows = a[0], parks = a[1], seen = {};
      var list = rows.filter(function (r) { if (!parks[r.ref] || seen[r.ref] || !(r.files || []).length) return false; seen[r.ref] = 1; return true; });
      S._parks = parks; S._rows = {}; list.forEach(function (r) { S._rows[r.ref] = r; });
      sel.innerHTML = list.length ? '<option value="">' + list.length + ' park(s) with a saved picture map</option>' + list.map(function (r) { return '<option value="' + esc(r.ref) + '">' + esc(r.ref + ' ' + (parks[r.ref].name || r.name || '')) + '</option>'; }).join('')
        : '<option value="">No saved picture map for a park here</option>';
    }).catch(function (e) { sel.innerHTML = '<option value="">Could not load the list</option>'; say('Could not load the park list: ' + e.message, true); });
  }

  /* ------------------------------------------------------------ the picture (saved copy on the picture-maps branch, or a dropped file) */
  function pickPark(ref) {
    var row = S._rows && S._rows[ref], park = S._parks && S._parks[ref]; if (!row || !park) return Promise.resolve();
    var pg = Array.isArray(row.page) ? row.page[0] : (row.page || 1), file = row.files[0];
    resetWork(); S.ref = ref; S.park = park; S.row = { source_url: row.source_url || '', page: pg, file: file, boundary_px: row.boundary_px || null };
    say('Loading the saved picture for ' + ref + '…');
    return fetch(RAW + file.split('/').map(encodeURIComponent).join('/'), { cache: 'no-cache' }).then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.arrayBuffer(); })
      .then(function (buf) { return showPicture(buf, RAW + file); })
      .catch(function (e) { say('Could not load the saved picture (' + e.message + '). You can drop the same file on the page instead.', true); });
  }
  function dropFile(f) {
    if (!f || !S.ref) { say('Pick the park first, then drop its picture file.', true); return Promise.resolve(); }
    return f.arrayBuffer().then(function (buf) { return showPicture(buf, 'dropped file: ' + f.name); });
  }
  function showPicture(buf, from) {
    return crypto.subtle.digest('SHA-256', buf).then(function (h) {
      var url = URL.createObjectURL(new Blob([buf], { type: 'image/jpeg' }));
      return new Promise(function (ok, bad) { var im = new Image(); im.onload = function () { ok({ url: url, w: im.naturalWidth, h: im.naturalHeight, sha: hex(h) }); }; im.onerror = function () { bad(new Error('not a picture')); }; im.src = url; });
    }).then(function (p) {
      S.pic = { file: S.row.file, source_url: S.row.source_url, page: S.row.page, sha256: p.sha, width: p.w, height: p.h, loaded_from: from, url: p.url };
      if (picLayer) pmap.removeLayer(picLayer);
      var b = [[-p.h, 0], [0, p.w]];
      picLayer = L.imageOverlay(p.url, b).addTo(pmap); pmap.fitBounds(b);
      rmap.setView(S.park.pin, 15);
      if (gR) gR.clearLayers();
      redraw();
      $('mpRing').hidden = !(S.row.boundary_px && S.row.boundary_px.length > 2);
      say(S.ref + ' ' + (S.park.name || '') + ': picture ' + p.w + ' x ' + p.h + ' px. Click a spot on the PICTURE, then the same spot on the MAP.');
    });
  }

  /* ------------------------------------------------------------ clicks */
  function picXY(ll) { return [r2(ll.lng), r2(-ll.lat)]; }
  function onPic(e) {
    if (!S.pic) return;
    var p = picXY(e.latlng);
    if (p[0] < 0 || p[1] < 0 || p[0] > S.pic.width || p[1] > S.pic.height) { say('That is off the picture.', true); return; }
    if (S.mode === 'shape') { S.shape.px.push(p); refit(); return; }
    S.pending = { px: p }; redraw();
    say('Point ' + (S.pairs.length + 1) + ' on the picture. Now click the SAME spot on the map (a USGS layer).');
  }
  function onMap(e) {
    if (!S.pic || S.mode !== 'pairs') return;
    if (!S.pending) { say('Click the spot on the PICTURE first, then here.', true); return; }
    if (!M.BASEMAPS[S.base]) { say('Points can only be placed on a USGS map (government basemap). Switch the map layer first.', true); return; }
    S.pairs.push({ px: S.pending.px, ll: [r7(e.latlng.lat), r7(e.latlng.lng)], layer: S.base, zoom: rmap.getZoom() });
    S.pending = null; refit();
    say('Pair ' + S.pairs.length + ' placed.' + (S.pairs.length < M.LIMITS.HAND_MIN_POINTS ? ' At least ' + M.LIMITS.HAND_MIN_POINTS + ' pairs, spread around the park.' : ''));
  }
  function delPair(i) { S.pairs.splice(i, 1); refit(); }
  function movePic(i, ll) { S.pairs[i].px = picXY(ll); refit(); }
  function moveMap(i, ll) { S.pairs[i].ll = [r7(ll.lat), r7(ll.lng)]; S.pairs[i].layer = S.base; S.pairs[i].zoom = rmap.getZoom(); refit(); }

  /* ------------------------------------------------------------ fit + drawing */
  function refit() {
    S.fit = S.pairs.length >= 3 ? M.fitPairs(S.pairs, S.park.pin) : null;
    var sh = S.shape.px.length ? { px: S.shape.px, kind: S.shape.kind } : null;
    S.gates = S.fit ? M.gates(S.fit, sh, S.pairs.map(function (q) { return q.layer; }), S.park.pin) : [];
    redraw(); table();
  }
  function num(i) { return L.divIcon({ className: 'mp-num', html: '<span>' + i + '</span>', iconSize: [24, 24], iconAnchor: [12, 12] }); }
  function redraw() {
    if (!gP) return; gP.clearLayers(); gR.clearLayers();
    S.pairs.forEach(function (q, i) {
      var a = L.marker([-q.px[1], q.px[0]], { icon: num(i + 1), draggable: true }).addTo(gP);
      a.on('dragend', function () { movePic(i, a.getLatLng()); });
      var b = L.marker(q.ll, { icon: num(i + 1), draggable: true }).addTo(gR);
      b.on('dragend', function () { moveMap(i, b.getLatLng()); });
    });
    if (S.pending) L.marker([-S.pending.px[1], S.pending.px[0]], { icon: num('?') }).addTo(gP);
    if (S.park) L.circleMarker(S.park.pin, { radius: 7, color: '#c00', weight: 3, fillOpacity: 0.9, interactive: false }).addTo(gR).bindTooltip('POTA pin (never moved)');
    var sp = S.shape.px.map(function (p) { return [-p[1], p[0]]; });
    if (sp.length) (S.shape.kind === 'area' && sp.length > 2 ? L.polygon(sp, { color: '#e000e0', weight: 2, fillOpacity: 0.08 }) : L.polyline(sp, { color: '#e000e0', weight: 2 })).addTo(gP);
    if (S.fit) {
      var T = S.fit.T, w = S.pic.width, h = S.pic.height;
      var c = [[0, 0], [w, 0], [w, h], [0, h]].map(function (p) { return M.pxToLatLon(T, S.park.pin, p[0], p[1]); });
      L.polygon(c, { color: '#555', weight: 1, dashArray: '4 4', fill: false, interactive: false }).addTo(gR);
      if (S.shape.px.length > (S.shape.kind === 'area' ? 2 : 1)) {
        var pl = M.placeShape(T, S.park.pin, S.shape.px, S.shape.kind), ll = pl.lonlat.map(function (q) { return [q[1], q[0]]; });
        (S.shape.kind === 'area' ? L.polygon(ll, { color: '#e000e0', weight: 3, fillOpacity: 0.12 }) : L.polyline(ll, { color: '#e000e0', weight: 3 })).addTo(gR)
          .bindTooltip('Approximate: not the official boundary');
      }
      var pp = M.latLonToPx(T, S.park.pin, S.park.pin[0], S.park.pin[1]);
      L.circleMarker([-pp[1], pp[0]], { radius: 6, color: '#c00', weight: 3, interactive: false }).addTo(gP);
    }
    placeGhost();
  }
  /* The ghosted picture on the real map: an <img> in the overlay pane, CSS-transformed so three corners land on their fitted places. */
  function placeGhost() {
    if (!rmap) return;
    if (!S.fit || !S.pic) { if (ghost) ghost.style.display = 'none'; return; }
    if (!ghost) { ghost = document.createElement('img'); ghost.className = 'mp-ghost'; ghost.alt = ''; rmap.getPanes().overlayPane.appendChild(ghost); }
    var w = S.pic.width, h = S.pic.height, T = S.fit.T, pin = S.park.pin;
    var p = [[0, 0], [w, 0], [0, h]].map(function (q) { var g = M.pxToLatLon(T, pin, q[0], q[1]); return rmap.latLngToLayerPoint(L.latLng(g[0], g[1])); });
    var a = (p[1].x - p[0].x) / w, b = (p[1].y - p[0].y) / w, c = (p[2].x - p[0].x) / h, d = (p[2].y - p[0].y) / h;
    ghost.src = S.pic.url; ghost.style.display = ''; ghost.style.width = w + 'px'; ghost.style.height = h + 'px';
    ghost.style.opacity = String(($('mpOp') ? +$('mpOp').value : 50) / 100);
    ghost.style.transform = 'matrix(' + [a, b, c, d, p[0].x, p[0].y].map(function (v) { return v.toFixed(6); }).join(',') + ')';
  }
  function table() {
    var t = $('mpPairs'), f = S.fit;
    if (t) t.innerHTML = S.pairs.length ? '<table><tr><th>#</th><th>picture x, y</th><th>map lat, lon</th><th>map</th><th>error</th><th>left out</th><th></th></tr>' + S.pairs.map(function (q, i) {
      return '<tr><td>' + (i + 1) + '</td><td>' + q.px[0].toFixed(1) + ', ' + q.px[1].toFixed(1) + '</td><td>' + q.ll[0].toFixed(6) + ', ' + q.ll[1].toFixed(6) + '</td><td>' + esc(M.BASEMAPS[q.layer] ? 'USGS' : q.layer) +
        '</td><td>' + (f ? f.residuals[i].toFixed(1) + ' m' : '') + '</td><td>' + (f && f.loo ? f.loo[i].toFixed(1) + ' m' : '') + '</td><td><button type="button" data-del="' + i + '" aria-label="Delete pair ' + (i + 1) + '">✕</button></td></tr>';
    }).join('') + '</table>' : '<p class="mp-note">No pairs yet.</p>';
    if (t) Array.prototype.forEach.call(t.querySelectorAll('[data-del]'), function (b) { b.onclick = function () { delPair(+b.getAttribute('data-del')); }; });
    var s = $('mpFit');
    if (s) s.innerHTML = f ? 'Fit error <b>' + f.rms.toFixed(1) + ' m</b> · leave-one-out <b>' + (f.loo_rms === null ? 'n/a' : f.loo_rms.toFixed(1) + ' m') + '</b> (worst ' + (f.loo_max === null ? 'n/a' : f.loo_max.toFixed(1) + ' m') +
      ') · ' + f.scale_m_per_px.toFixed(3) + ' m per picture pixel · picture turned ' + f.rotation_deg.toFixed(1) + '°' : 'The fit starts after 3 pairs.';
    var g = $('mpGates');
    if (g) g.innerHTML = S.gates.map(function (x) { return '<li class="' + (x.pass ? 'ok' : 'no') + '">' + (x.pass ? '✓ PASS ' : '✗ FAIL ') + esc(x.why) + '</li>'; }).join('') +
      (S.gates.length ? '<li class="later">… CHECKED LATER by the KPC-Data checker: the index row (agency, source, banned map sites), the picture file’s fingerprint, the size for the park type, a clipped map edge, and the line agreement when the tracer’s saved basemap is there.</li>' : '');
    var a = $('mpAcres');
    if (a) { var pl = f && S.shape.px.length > (S.shape.kind === 'area' ? 2 : 1) ? M.placeShape(f.T, S.park.pin, S.shape.px, S.shape.kind) : null; a.textContent = pl ? (pl.area_acres !== null ? 'Traced area about ' + pl.area_acres.toFixed(1) + ' acres' : 'Traced line about ' + pl.length_km.toFixed(2) + ' km') + ' (the checker judges the size for a ' + (S.park.type || 'park') + ').' : ''; }
    var sv = $('mpSave'); if (sv) sv.disabled = !(f && S.shape.px.length);
  }

  /* ------------------------------------------------------------ the click set */
  function clickSet() {
    var f = S.fit;
    return {
      format: 'kpc-click-set 1', tool: VERSION + ' / ' + M.VERSION, ref: S.ref,
      park: { name: S.park.name || '', type: S.park.type || '', pin: S.park.pin, pin_source: S.park.src },
      picture: { file: S.pic.file, source_url: S.pic.source_url, page: S.pic.page, sha256: S.pic.sha256, width: S.pic.width, height: S.pic.height, loaded_from: S.pic.loaded_from },
      pairs: S.pairs.map(function (q, i) { return { n: i + 1, px: q.px, ll: q.ll, layer: q.layer, zoom: q.zoom }; }),
      shape: { kind: S.shape.kind, px: S.shape.px, from: S.shape.from || 'hand' },
      fit: { model: 'similarity', z: [f.T.a, f.T.b], t: [f.T.tx, f.T.ty], scale_m_per_px: f.scale_m_per_px, rotation_deg: f.rotation_deg,
        residuals_m: f.residuals, rms_m: f.rms, loo_m: f.loo, loo_rms_m: f.loo_rms, loo_max_m: f.loo_max },
      gates: S.gates, date: today(), by: (($('mpBy') && $('mpBy').value) || '').trim().slice(0, 40) || 'anonymous'
    };
  }
  function save() {
    if (!S.fit || !S.shape.px.length) { say('Place at least 3 pairs and trace the shape first.', true); return null; }
    var cs = clickSet(), txt = JSON.stringify(cs, null, 1) + '\n';
    var a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([txt], { type: 'application/json' })); a.download = S.ref + '.clicks.json';
    document.body.appendChild(a); a.click(); a.remove();
    var bad = S.gates.filter(function (x) { return !x.pass; }).length;
    say('Saved ' + S.ref + '.clicks.json' + (bad ? ' (' + bad + ' gate(s) still fail: the checker will refuse it until they pass)' : '') + '. Hand it in as the page says below.', !!bad);
    window.KPCPlacerLast = cs;
    return cs;
  }

  /* ------------------------------------------------------------ set-up */
  function resetWork() { S.pairs = []; S.pending = null; S.shape = { kind: $('mpKind') ? $('mpKind').value : 'area', px: [] }; S.fit = null; S.gates = []; redraw(); table(); }
  function setMode(m) { S.mode = m; ['mpModePairs', 'mpModeShape'].forEach(function (id) { var b = $(id); if (b) b.setAttribute('aria-pressed', String((id === 'mpModeShape') === (m === 'shape'))); }); S.pending = null; redraw();
    say(m === 'shape' ? 'Tracing: click around the ' + (S.shape.kind === 'area' ? 'boundary' : 'trail') + ' on the PICTURE, corner by corner.' : 'Pairs: click a spot on the picture, then the same spot on the map.'); }
  function setBase(id) {
    var all = Object.assign({}, M.BASEMAPS, LOOK_ONLY), def = all[id]; if (!def) return;
    Object.keys(baseLayers).forEach(function (k) { if (rmap.hasLayer(baseLayers[k])) rmap.removeLayer(baseLayers[k]); });
    baseLayers[id] = baseLayers[id] || L.tileLayer(def.url, { maxZoom: 19, maxNativeZoom: M.BASEMAPS[id] ? 16 : 19, attribution: def.attr || 'USGS The National Map' });
    baseLayers[id].addTo(rmap); S.base = id;
  }
  function init() {
    if (!M || !window.L || !$('mpPic')) return;
    if (window.KPCGate && !KPCGate.member()) return;   // members only: the door covers the page anyway
    pmap = L.map('mpPic', { crs: L.CRS.Simple, minZoom: -5, maxZoom: 4, zoomSnap: 0.25, attributionControl: false });
    pmap.setView([0, 0], 0);
    rmap = L.map('mpMap', { zoomSnap: 0.5 }); rmap.setView([37.8, -85.0], 7);
    gP = L.layerGroup().addTo(pmap); gR = L.layerGroup().addTo(rmap);
    setBase('usgs-topo');
    pmap.on('click', onPic); rmap.on('click', onMap);
    rmap.on('zoomend', placeGhost); rmap.on('moveend', placeGhost); rmap.on('viewreset', placeGhost);
    fillStates();
    $('mpSt').onchange = listParks;
    $('mpPark').onchange = function () { pickPark($('mpPark').value); };
    $('mpFile').onchange = function () { dropFile(this.files && this.files[0]); };
    $('mpBase').onchange = function () { setBase(this.value); };
    $('mpModePairs').onclick = function () { setMode('pairs'); };
    $('mpModeShape').onclick = function () { setMode('shape'); };
    $('mpKind').onchange = function () { S.shape.kind = this.value; refit(); };
    $('mpUndo').onclick = function () { S.shape.px.pop(); refit(); };
    $('mpClear').onclick = function () { S.shape.px = []; S.shape.from = 'hand'; refit(); };
    $('mpRing').onclick = function () { S.shape = { kind: 'area', px: S.row.boundary_px.map(function (p) { return [r2(+p[0]), r2(+p[1])]; }), from: 'tracer boundary step' }; $('mpKind').value = 'area'; refit(); };
    $('mpOp').oninput = placeGhost;
    $('mpSave').onclick = save;
    var q = new URLSearchParams(location.search), st = q.get('st'), ref = q.get('ref');
    if (st) { $('mpSt').value = st; listParks().then(function () { if (ref) { $('mpPark').value = ref; pickPark(ref); } }); }
    table();
  }
  window.KPCPlacer = { state: function () { return S; }, clickSet: function () { return S.fit ? clickSet() : null; }, save: save, pick: pickPark, list: listParks, setMode: setMode, setBase: setBase, VERSION: VERSION };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
