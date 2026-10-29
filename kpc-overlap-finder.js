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
  /* Oct 28 (HQ: Minnesota's file is gzipped): a region file may be <name>.json or <name>.json.gz; the .gz is unpacked in the browser */
  function jgz(u) { if (typeof DecompressionStream === 'undefined') return Promise.resolve(null);
    return fetch(u, { cache: 'no-cache' }).then(function (r) { if (!r.ok) return null; return new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).json(); }).catch(function () { return null; }); }
  function jz(u) { return j(u).then(function (d) { return d || jgz(u + '.gz'); }); }
  /* Oct 29 (chat 2: Alaska's results file was 135 MB): a spot may keep its big patch shape + park edges + trail zone APART
     (spot.heavy = 'shapes/<region>/<hash>', file <base><heavy>.json.gz = {id, shape, lines, zone}); they are fetched only when a row is opened. */
  var HB = '../KPC-Data/data/fers/';
  function hydrate(x) { if (!x.heavy || x._hy) return Promise.resolve(true);
    return jgz(HB + x.heavy + '.json.gz').then(function (h) { if (!h || h.id !== x.id) return false; ['shape', 'lines', 'zone'].forEach(function (k) { if (h[k]) x[k] = h[k]; }); x._hy = true; return true; }); }
  var SHORT = '⚠️ Parks\' boundaries may overlap here, but we can\'t confirm it. Check both official boundary maps and make your own call before you count it.';   /* Brandon Oct 27 4:23 PM: 'Say this instead' */
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
  var CFG = null, REV = {}, REG = null, ROWS = [], TIGHT = [], WATER = [], MISS = [], WAITN = 0, here = null, F = { big: true, small: true, trail: true, multi: false, near: false };
  function ok3(s) { return Array.isArray(s.passes) && s.passes.length >= 3 && s.passes.every(function (x) { return x === 1; }); }
  function reviewed(s) { return !!(s.reviewed || REV[s.id]); }
  function build(files, missing) {
    var all = [], kids = {};
    files.forEach(function (d) { (d && d.spots || []).forEach(function (s) { s._st = d.st || ''; all.push(s); }); });
    all.forEach(function (s) { var m = /^merged into one row: (.+)$/.exec(s.status || ''); if (m) (kids[m[1]] = kids[m[1]] || []).push(s); });
    var groups = {}; ROWS = []; TIGHT = []; WATER = []; WAITN = 0;
    all.forEach(function (s) {
      if (!ok3(s)) return;
      if (CFG && CFG.hide && CFG.hide[(s.refs || []).slice().sort().join('+')]) return;   // a row chat 8 said to drop (kpc-fers-regions.json 'hide')
      var st = String(s.status || '');
      if (/^very tight/.test(st)) { if (MEMBER) TIGHT.push(s); return; }
      if (/^water only/.test(st)) { if (MEMBER) WATER.push(s); return; }   /* rule 9: water-only spots are listed apart (boat or kayak) */
      if (st !== 'candidate') return;                                    // saved outline only / not sure / dropped / merged
      /* 'same land, two park numbers' = SHOWN with that label everywhere (final ruling, CLAUDE.md) */
      var noAcc = !s.access_pin || !s.access_pin.at;
      if (noAcc && !MEMBER) return;                                      // A9: members only
      var rev = reviewed(s); if (!rev) WAITN++;
      var key = s.refs.slice().sort().join('+');
      var g = groups[key] || (groups[key] = { key: key, refs: s.refs.slice().sort(function (x, y) { return +(/(\d+)$/.exec(x) || [0, 0])[1] - +(/(\d+)$/.exec(y) || [0, 0])[1]; }), names: {}, patches: [], st: s._st, trail: false });
      Object.assign(g.names, s.names || {}); s._kids = (kids[s.id] || []).filter(function (k, i, A) { var sh = (k.shape_sig || JSON.stringify(k.shape || '')); return sh !== (s.shape_sig || JSON.stringify(s.shape || '')) && A.findIndex(function (o) { return (o.shape_sig || JSON.stringify(o.shape || '')) === sh; }) === i; });   /* Brandon Oct 27 6:16 PM ('steps 2 and 3 are the same'): the data listed one stretch twice */ s._rev = rev; s._noAcc = noAcc;
      if (s.kind === 'trail' || s.kind === 'river') g.trail = true; if (s.kind === 'river') g.river = true; g.patches.push(s);   // Oct 28: a water-route row is a LINE (the bank), drawn as its 100-ft band like a trail, never as a polygon
    });
    Object.keys(groups).forEach(function (k) { var g = groups[k];
      g.patches.sort(function (a, b) { return size(b) - size(a); });
      g.n = g.refs.length; g.best = g.patches[0];
      ROWS.push(g); });
    MISS = MEMBER ? ((missing && missing.parks) || []).filter(function (m) { return !REG || !REG.missingSt || m.st === REG.missingSt; }) : [];   // a shared file (missing-midwest) lists several states
  }
  function size(s) { return (s.kind === 'trail' || s.kind === 'river') ? (s.len_m || 0) / 1000 : (s.wide_m || 0); }
  function tierOf(s) { if (s.kind === 'trail' || s.kind === 'river') return 'trail'; var w = (s.wide_m || 0) * YD; return /small/.test(s.small || '') || (w && w < 100) ? 'small' : 'big'; }
  function visiblePatches(g) { var w = $('ovWait') && $('ovWait').checked && MEMBER; return g.patches.filter(function (s) { return s._rev || w; }); }

  /* ---------- the LIST ---------- */
  function tagOf(g) { return g.trail ? '<span class="ov-badge bg-trail">' + (g.river ? 'POSSIBLE RIVER OVERLAP: WITHIN 100 FT OF THE RIVER BANK' : 'POSSIBLE TRAIL OVERLAP: WITHIN 100 FT OF THE TRAIL LINE') + '</span>' : '<span class="ov-badge bg-n">POSSIBLE ' + g.n + '-FER</span>'; }
  function nm(g, r) { return (g.names && g.names[r]) || r; }
  function accLine(s) {
    var a = s.access_pin;
    /* Brandon Oct 27 4:31 PM ('Fort Donelson say no public road for a mile it has a road in the middle of it'): a row the access step never ran on
       (no access_pin at all, e.g. 'same land' rows) is NOT 'no road': only an access_pin that says none is */
    if (!a) return '<p class="ov-note">🅿️ Closest public access not worked out for this one yet: use the official map and the roads on the map.</p>';
    if (!a.at || a.from === 'none') return '<p class="ov-note">🅿️ <b>No public road or parking found within about a mile.</b> Plan your walk on the official map.</p>';
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
      var sz = (s.kind === 'trail' || s.kind === 'river') ? (s.len_m ? 'about ' + Math.round(s.len_m * YD) + (s.kind === 'river' ? ' yards of river bank' : ' yards of trail') + (s.stretches > 1 ? ' in ' + s.stretches + ' stretches' : '') : 'trail stretch') : 'fits a circle about ' + Math.round((s.wide_m || 0) * YD) + ' yards across' + (s.acres ? ' · ' + (+s.acres).toFixed(1) + ' acres' : '');
      return '<li><b>Place ' + (i + 1) + '</b>: ' + sz + (tierOf(s) === 'small' ? ' · <i>small: tight fit</i>' : '') + ' <button type="button" class="ov-pl" data-place="' + esc(g.key) + '|' + i + '">🗺 SHOW</button>' + accLine(s) + '</li>'; }).join('') + '</ol></details>';
  }
  function rowHtml(g, ps) {
    var s = ps[0], small = ps.some(function (x) { return tierOf(x) === 'small'; }), wait = ps.some(function (x) { return !x._rev; });
    return '<div class="ov-row" data-row="' + esc(g.key) + '">' + tagOf(g) + (small ? '<span class="ov-badge bg-small">SMALL OVERLAP: TIGHT FIT, CHECK CAREFULLY</span>' : '') +
      (s.label ? '<span class="ov-badge bg-off">' + esc(s.label.toUpperCase()) + '</span>' : '') +
      '<b class="t" style="margin-top:6px">' + g.refs.map(function (r) { return esc(r) + ' ' + esc(nm(g, r)); }).join(' + ') + '</b>' +
      '<span class="m">' + sizeLine(g, ps) + (here && g._mi != null ? ' · ' + Math.round(g._mi) + ' mi from you' : '') + '</span>' +
      '<p class="ov-note">Last checked ' + niceDate(s.checked || s.found || '') + '</p>' + (ps.length > 1 ? '' : accLine(s)) +
      '<div class="acts"><button type="button" data-open="' + esc(g.key) + '">🗺 SHOW ON THE MAP</button></div>' +
      /* Brandon Oct 27 2:48 PM: 'see more after the last checked date to reveal the other info' */
      '<details class="ov-more"><summary>SEE MORE</summary>' + (ps.length > 1 ? placesHtml(g, ps) : '') +
      (s.note ? '<p class="ov-note">ℹ️ ' + esc(s.note) + '</p>' : '') +
      '<p class="ov-note">Maps used: ' + mapsUsed(s) + '</p>' +
      '<div class="acts">' + (s.maps || []).map(function (m) { return '<a class="b" target="_blank" rel="noopener" href="' + esc(m[1]) + '">OFFICIAL MAP: ' + esc(m[0]) + '</a>'; }).join('') + '</div></details>' +
      '</div>';   /* Brandon Oct 27 3:04 PM: 'No need for a warning on every card' (one SHORT notice heads the list; popups + exports keep theirs) */
  }
  function numKey(g, k) { var n = g.refs.map(function (r) { return +(/(\d+)$/.exec(r) || [0, 0])[1]; }).sort(function (x, y) { return x - y; }); return n[k || 0] || 0; }
  /* Brandon Oct 27 4:30 PM ('I still see mentions of bots … Maps used: … read live from the agency …; official line (trails bot)'): plain words */
  function mapsUsed(s) {
    var md = s.map_dates || {}, k = Object.keys(md); if (!k.length) return 'the official maps (buttons below)';
    return k.map(function (r) { var v = String(md[r] || ''), d = /(\d{4}-\d{2}-\d{2})/.exec(v);
      var w = /official line|trail/i.test(v) ? 'the official trail line' : /agency|official/i.test(v) ? 'the agency\'s official map' : 'the official map';
      return esc(r) + ': ' + w + (d ? ' (' + niceDate(d[1]) + ')' : ''); }).join('; ');
  }
  function niceDate(d) { var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(d || ''); return m ? ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][+m[2] - 1] + ' ' + (+m[3]) + ', ' + m[1] : esc(d || ''); }
  /* plain wording per park (the data's 'why' is a working note); a park without one gets the general sentence */
  var MISS_PLAIN = {
    'US-10102': 'only the open 44 miles, Breaks to US 119, have an official trail line, and spots there are tested in the main list. The planned section has no official line yet (and mostly no trail), so spots there can\'t be checked.'
  };
  function missText(m) {
    var why = m.plain || MISS_PLAIN[m.ref] || 'this park has no official boundary map, so spots where it may overlap another park can\'t be checked. Its map pin sits inside another park\'s official outline.';
    return '<b>' + esc(m.name) + ' (' + esc(m.ref) + ')</b>: ' + esc(why).replace(/&#39;/g, '\'') + ' Not confirmed.' + (m.checked ? ' Last checked ' + niceDate(m.checked) + '.' : '');
  }
  /* the pop-up sheet: one park → its card (one partner) or the list of partner parks (several) */
  var PK = {}, SORT = store('kpcOvSort') === 'az' ? 'az' : 'num', SH = { ref: '', key: '' };
  function countText(e) { var c = {}; e.pairs.forEach(function (x) { var k = x[0].trail ? 'trail' : x[0].n; c[k] = (c[k] || 0) + 1; });
    return Object.keys(c).sort().map(function (k) { var n = c[k]; return k === 'trail' ? n + ' possible trail overlap' + (n > 1 ? 's' : '') : n + ' possible ' + k + '-fer' + (n > 1 ? 's' : ''); }).join(' · '); }
  function sheetEl() {
    var d = $('ovSheet'); if (d) return d;
    d = document.createElement('div'); d.id = 'ovSheet'; d.className = 'ov-sheet'; d.hidden = true; d.setAttribute('role', 'dialog'); d.setAttribute('aria-modal', 'true');
    d.innerHTML = '<div class="ov-sbox"><div class="ov-shd"><button type="button" class="ov-sback" data-sheet="back" hidden>← OTHER PARKS</button><b id="ovShT"></b><button type="button" class="ov-sx" data-sheet="x" aria-label="Close">✕</button></div><div id="ovShB"></div></div>';
    $('ov').appendChild(d); return d;
  }
  function openPark(ref, key) {
    var e = PK[ref]; if (!e) return; var d = sheetEl(); SH.ref = ref; SH.key = key || '';
    if (!key && e.pairs.length === 1) SH.key = e.pairs[0][0].key;
    $('ovShT').textContent = e.ref + ' ' + e.name;
    d.querySelector('[data-sheet=back]').hidden = !(SH.key && e.pairs.length > 1);
    if (SH.key) { var x = e.pairs.filter(function (p) { return p[0].key === SH.key; })[0]; if (!x) return; $('ovShB').innerHTML = '<span class="ov-short">' + SHORT + '</span>' + rowHtml(x[0], x[1]); }
    else $('ovShB').innerHTML = '<p class="ov-note">' + countText(e) + '. Pick the other park:</p><div class="ov-pks">' + e.pairs.map(function (x) {
      var g = x[0], oth = g.refs.filter(function (r) { return r !== ref; });
      return '<button type="button" class="ov-pk" data-pair="' + esc(g.key) + '"><b>' + oth.map(esc).join(' + ') + '</b><span class="nm">' + oth.map(function (r) { return esc(nm(g, r)); }).join(' + ') + '</span><span class="ct">' + (g.trail ? 'possible trail overlap' : 'possible ' + g.n + '-fer') + ' · ' + (g.trail ? 'about ' + (x[1].reduce(function (t, y) { return t + (y.len_m || 0); }, 0) / 1609).toFixed(1) + ' mi of trail' : x[1].length > 1 ? x[1].length + ' places' : 'about ' + Math.round((x[1][0].wide_m || 0) * YD) + ' yards across') + (g._mi != null && F.near ? ' · ' + (g._mi < 10 ? g._mi.toFixed(1) : Math.round(g._mi)) + ' mi' : '') + '</span><span class="go">›</span></button>'; }).join('') + '</div>';
    d.hidden = false; d.querySelector('.ov-sbox').scrollTop = 0; try { d.querySelector('.ov-sx').focus({ preventScroll: true }); } catch (x) {}
  }
  function closeSheet() { var d = $('ovSheet'); if (d) d.hidden = true; SH.ref = ''; SH.key = ''; }
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && $('ovSheet') && !$('ovSheet').hidden) closeSheet(); });
  document.addEventListener('click', function (e) {
    var t = e.target; if (!t.closest) return;
    var a = t.closest('#ov [data-pk]'); if (a) { e.preventDefault(); openPark(a.dataset.pk); return; }
    a = t.closest('#ov [data-pair]'); if (a) { e.preventDefault(); openPark(SH.ref, a.dataset.pair); return; }
    a = t.closest('#ov [data-sheet]'); if (a) { e.preventDefault(); if (a.dataset.sheet === 'back') openPark(SH.ref); else closeSheet(); return; }
    if (t.id === 'ovSheet') { closeSheet(); return; }
    a = t.closest('#ov [data-sort]'); if (a) { e.preventDefault(); SORT = a.dataset.sort; store('kpcOvSort', SORT);
      if (F.near) { F.near = false; var nb = document.querySelector('#ov [data-f=near]'); if (nb) nb.classList.remove('on'); $('ovNearNote').hidden = true; } list(); return; }
    if (t.closest('#ovSheet [data-open], #ovSheet [data-place]')) { var d = $('ovSheet'); if (d) d.hidden = true; }   // the map opens: get the sheet out of the way
  }, true);
  function list() {
    var q = ($('ovQ').value || '').trim().toLowerCase(), out = [];
    ROWS.forEach(function (g) {
      var ps = visiblePatches(g); if (!ps.length) return;
      if (q && (g.refs.join(' ') + ' ' + Object.values(g.names).join(' ') + ' ' + ps.map(function (s) { return (s.access_pin && s.access_pin.name) || ''; }).join(' ')).toLowerCase().indexOf(q) < 0) return;
      if (g.trail ? !F.trail : !F[tierOf(ps[0])]) return; if (F.multi && g.n < 3) return;
      g._mi = here && ps[0].center ? miles(here[0], here[1], ps[0].center[0], ps[0].center[1]) : null;
      out.push([g, ps]);
    });
    /* Brandon Oct 27 5 PM ('if a state has bunch of parks it be really long … just show park number and name sorted by number or a-z,
       click on it a card pops up, or with several 2-fers another list where you pick the other park'): ONE line per park (both sides
       of every pair), sorted BY NUMBER or A–Z (or nearest with NEAR ME); the card opens in a pop-up sheet. */
    var P = {}, qq = q;
    out.forEach(function (x) { x[0].refs.forEach(function (r) { var e = P[r] || (P[r] = { ref: r, name: nm(x[0], r), pairs: [], mi: null }); e.pairs.push(x); if (x[0]._mi != null && (e.mi == null || x[0]._mi < e.mi)) e.mi = x[0]._mi; }); });
    var pk = Object.keys(P).map(function (k) { return P[k]; });
    if (qq) { var own = pk.filter(function (e) { return (e.ref + ' ' + e.name).toLowerCase().indexOf(qq) >= 0; }); if (own.length) pk = own; }
    var refN = function (r) { return +(/(\d+)$/.exec(r) || [0, 0])[1]; };
    pk.sort(F.near && here ? function (a, b) { return a.mi - b.mi; } : SORT === 'az' ? function (a, b) { return a.name.replace(/^the /i, '').localeCompare(b.name.replace(/^the /i, '')) || refN(a.ref) - refN(b.ref); } : function (a, b) { return a.ref.split('-')[0].localeCompare(b.ref.split('-')[0]) || refN(a.ref) - refN(b.ref); });
    PK = P;
    [].forEach.call(document.querySelectorAll('#ov [data-sort]'), function (b) { var on = b.dataset.sort === SORT && !(F.near && here); b.classList.toggle('on', on); b.setAttribute('aria-pressed', String(on)); });
    var empty = '<div class="ov-empty"><b>We are still checking ' + esc(REG ? REG.label : 'these') + '\'s parks.</b> Nothing is listed yet. This does not mean there are no overlaps.</div>';
    $('ovList').innerHTML = pk.length ? '<p class="ov-note">' + pk.length + ' park' + (pk.length > 1 ? 's' : '') + ' with a possible 2-fer in ' + esc(REG.label) + ' (' + out.length + ' pair' + (out.length > 1 ? 's' : '') + '). Tap a park.</p><span class="ov-short" style="margin-bottom:8px">' + SHORT + '</span>' +
      '<div class="ov-pks">' + pk.map(function (e) { return '<button type="button" class="ov-pk" data-pk="' + esc(e.ref) + '"><b>' + esc(e.ref) + '</b><span class="nm">' + esc(e.name) + '</span><span class="ct">' + countText(e) + (e.mi != null && F.near ? ' · ' + (e.mi < 10 ? e.mi.toFixed(1) : Math.round(e.mi)) + ' mi' : '') + '</span><span class="go">›</span></button>'; }).join('') + '</div>'
      : (q ? '<p class="ov-note">Nothing matches that search.</p>' : empty);
    if ($('ovSheet') && !$('ovSheet').hidden && SH.ref && !P[SH.ref]) closeSheet();
    $('ovWaitW').hidden = true;   /* Brandon: no 'not released' talk while only club members can see the page */
    $('ovTightB').hidden = !TIGHT.length; $('ovTight').innerHTML = TIGHT.map(function (s) { return '<div class="ov-row" style="cursor:default"><span class="ov-badge bg-tight">VERY TIGHT: COULD BE MAP ERROR, CHECK BOTH OFFICIAL MAPS ON THE GROUND</span><b class="t">' + s.refs.map(function (r) { return esc(r) + ' ' + esc((s.names || {})[r] || ''); }).join(' + ') + '</b><span class="m">' + (s.kind === 'trail' ? 'trail strip' + (s.len_m ? ' about ' + Math.round(s.len_m * YD) + ' yards long' : '') + ', thinner than 10 yards everywhere' : s.wide_m ? 'about ' + Math.round(s.wide_m * YD) + ' yards across' : '') + '</span>' + accLine(s) + '</div>'; }).join('');
    $('ovWaterB').hidden = !WATER.length; $('ovWater').innerHTML = WATER.map(function (s) { return '<div class="ov-row" style="cursor:default"><span class="ov-badge bg-trail">WATER ONLY: BY BOAT OR KAYAK</span><b class="t">' + s.refs.map(function (r) { return esc(r) + ' ' + esc((s.names || {})[r] || ''); }).join(' + ') + '</b><span class="m">' + (s.wide_m ? 'about ' + Math.round(s.wide_m * YD) + ' yards across, on the water' : 'on the water') + (s.checked ? ' · last checked ' + niceDate(s.checked) : '') + '</span>' + accLine(s) + '</div>'; }).join('');
    /* HQ Oct 27 4:25 PM: plain words, one sentence each: what's missing, why, and what was still tested */
    $('ovMissB').hidden = !MISS.length; $('ovMiss').innerHTML = MISS.map(function (m) { return '<div class="ov-row" style="cursor:default"><span class="ov-badge bg-wld">MISSING BOUNDARY: CHECK THE OFFICIAL MAP</span><p class="ov-note" style="color:#efe9da;font-size:14.5px">' + missText(m) + '</p></div>'; }).join('');
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
    /* Oct 28 (Brandon: the card went behind the zoom + layer buttons): while a card (popup) is open the map's buttons step aside */
    map.on('popupopen', function () { $('ovMap').classList.add('ov-popopen'); var w = $('ovMap').parentNode; if (w) w.classList.add('ov-popopen'); });
    map.on('popupclose', function () { $('ovMap').classList.remove('ov-popopen'); var w = $('ovMap').parentNode; if (w) w.classList.remove('ov-popopen'); });
    map.on('zoomend moveend viewreset', function () { setTimeout(clipTrail, 0); });
    /* RULE SHEET G: zoomed in close anywhere on the map, the parks' pieces on screen are re-read at full detail too */
    var shT = null; map.on('moveend', function () { clearTimeout(shT); shT = setTimeout(function () { if (cur && map.getZoom() >= 13) { var b = map.getBounds().pad(0.2); sharpen(cur, [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()]); } }, 400); });
    if (!window.KPCLayers) base.street.addTo(map); gAll = L.layerGroup().addTo(map);
    if (window.KPCLocate) { try { KPCLocate(map); } catch (e) {} } if (window.KPCFull) { try { KPCFull(map); } catch (e) {} }
    map.on('click', function (e) { if (mode === 'pin') { if (pinM) map.removeLayer(pinM); status([e.latlng.lat, e.latlng.lng], 0, true);
        pinM = L.marker(e.latlng, { icon: L.divIcon({ className: '', html: '<span style="display:block;width:26px;height:26px;border-radius:50% 50% 50% 0;background:#d0312d;border:3px solid #fff;transform:rotate(-45deg);box-shadow:0 2px 6px #0007"></span>', iconSize: [26, 26], iconAnchor: [13, 30] }) }).addTo(map)
          .bindPopup($('ovGps').innerHTML + tripLink(e.latlng.lat, e.latlng.lng), { maxWidth: 280 }).openPopup(); }
      else if (mode === 'measure') { meas.push(e.latlng); if (meas.length > 2) meas = [e.latlng]; draw(); if (meas.length === 2) { var d = map.distance(meas[0], meas[1]); L.popup().setLatLng(meas[1]).setContent('<b>📏 ' + Math.round(d * YD) + ' yards</b> (' + Math.round(d * 3.28084) + ' ft) in a straight line').openOn(map); } } 
      else if (!mode) { L.popup({ maxWidth: 290 }).setLatLng(e.latlng).setContent(landAt(e.latlng.lat, e.latlng.lng)).openOn(map); } });
    return true;
  }
  function setBase(n) { if (!map) return; map.eachLayer(function (l) { if (l instanceof L.TileLayer && !gAll.hasLayer(l)) map.removeLayer(l); }); Object.keys(base).forEach(function (k) { if (map.hasLayer(base[k])) map.removeLayer(base[k]); }); base[n].addTo(map); layerName = n; tools(); }
  /* Oct 28 (Brandon: 'the overlap boundaries still funky'): a trail stretch's patch = its TRUE 2-fer ground from pass 5 ('zone':
     the 100-ft band that is also inside the other park), not the whole band clipped on the screen; the band stays as the line park's look */
  /* HQ Oct 28 8:21 PM (Brandon: 'make sure the overlap lines are drawn correct and match the borders'): an area patch's own shape is
     thinned a little more than the parks' full-detail edges (`lines`, read with the patch), so its corners sat 2-12 m off them. Each
     patch corner is moved onto the nearest edge (within 20 m), and where two corners in a row sit on the SAME edge, the edge's own
     points between them are put in, so the gold line runs exactly along the border. A corner with no edge near it stays as it is. */
  function onEdges(ring, lines) {
    var Ls = []; Object.keys(lines || {}).forEach(function (r) { (lines[r] || []).forEach(function (l) { if (l && l.length > 1) Ls.push(l); }); });
    if (!Ls.length || !ring || ring.length < 3) return ring;
    var k = Math.cos(ring[0][1] * Math.PI / 180) * 111320, m = 110540, XY = function (q, o) { return [(q[0] - o[0]) * k, (q[1] - o[1]) * m]; };
    var snap = function (p) { var best = null; Ls.forEach(function (l, li) { for (var i = 1; i < l.length; i++) { var a = XY(l[i - 1], p), b = XY(l[i], p), dx = b[0] - a[0], dy = b[1] - a[1], t = -(a[0] * dx + a[1] * dy) / ((dx * dx + dy * dy) || 1); t = Math.max(0, Math.min(1, t));
        var d = Math.hypot(a[0] + t * dx, a[1] + t * dy); if (!best || d < best.d) best = { d: d, li: li, s: i - 1 + t, q: [l[i - 1][0] + t * (l[i][0] - l[i - 1][0]), l[i - 1][1] + t * (l[i][1] - l[i - 1][1])] }; } }); return best && best.d <= 20 ? best : null; };
    var closed = ring.length > 3 && ring[0][0] === ring[ring.length - 1][0] && ring[0][1] === ring[ring.length - 1][1], R = closed ? ring.slice(0, -1) : ring.slice();
    var S = R.map(snap), out = [];
    var len = function (pts) { var t = 0; for (var i = 1; i < pts.length; i++) { var a = XY(pts[i - 1], pts[0]), b = XY(pts[i], pts[0]); t += Math.hypot(b[0] - a[0], b[1] - a[1]); } return t; };
    for (var i = 0; i < R.length; i++) {
      var A = S[i], Bn = S[(i + 1) % R.length]; out.push(A ? A.q : R[i]);
      if (A && Bn && A.li === Bn.li && Math.abs(A.s - Bn.s) > 0) {   // both corners on the same edge: walk along it
        var l = Ls[A.li], mid = [], up = Bn.s > A.s;
        if (up) { for (var j = Math.floor(A.s) + 1; j <= Math.floor(Bn.s) && j < l.length; j++) mid.push(l[j]); }
        else { for (var j2 = Math.ceil(A.s) - 1; j2 >= Math.ceil(Bn.s) && j2 >= 0; j2--) mid.push(l[j2]); }
        var direct = len([A.q, Bn.q]), along = len([A.q].concat(mid, [Bn.q]));
        if (mid.length && mid.length < 400 && along <= direct * 3 + 30) mid.forEach(function (q) { out.push(q); });
      }
    }
    out.push(out[0]); return out;
  }
  function patchRings(g) { var out = []; visiblePatches(g).forEach(function (s) { [s].concat(s._kids || []).forEach(function (x) { if (!x.shape || x.shape.length < 2) return;
    if (x.kind === 'trail' || x.kind === 'river') { var band = bandRing(x.shape), z = (x.zone || []).filter(function (r) { return r && r.length > 2; });
      if (z.length) z.forEach(function (r, i) { out.push({ s: x, ring: r, line: x.shape, band: band, zone: true, first: i === 0 }); });
      else out.push({ s: x, ring: band, line: x.shape, band: band, first: true }); }
    else out.push({ s: x, ring: x.lines ? onEdges(x.shape, x.lines) : x.shape, line: null }); }); }); return out; }
  function openRow(key) {   // Oct 29: bring in any apart-stored shapes first (hydrate), then draw
    var g0 = ROWS.filter(function (r) { return r.key === key; })[0], all = [];
    if (g0) g0.patches.forEach(function (p) { all.push(p); (p._kids || []).forEach(function (k) { all.push(k); }); });
    var need = all.filter(function (x) { return x.heavy && !x._hy; });
    if (!need.length) return openRowDraw(key);
    if ($('ovSpot')) $('ovSpot').innerHTML = '<p class="ov-note">Loading the outline…</p>';
    return Promise.all(need.map(hydrate)).then(function (r) { if (r.some(function (x) { return !x; })) toast('Part of this outline could not load. Try again with a signal.'); openRowDraw(key); });
  }
  function openRowDraw(key) {
    if (!window.L && (openRow.tries = (openRow.tries || 0) + 1) < 40) { setTimeout(function () { openRow(key); }, 250); return; }   // the map library is still loading
    var g = ROWS.filter(function (r) { return r.key === key; })[0]; if (!g) return;
    showTab('map'); if (!mkMap()) { $('ovSpot').innerHTML = '<p class="ov-note">The map could not load (no signal?). The list still works.</p>'; return; }
    cur = g; OVON = true; stopGps(); meas = []; lastIn = false; leftUntil = 0; if (pinM) { map.removeLayer(pinM); pinM = null; }
    cur.rings = patchRings(g); parks = g.refs.map(function (r, i) { return { ref: r, n: i + 1, c: COL[i], dash: DASH[i], on: true, fs: null }; });
    spotPanel(); legend(); mapKey(); step = 0; clearTimeout(timer);
    /* Brandon Oct 27 5:59 PM (Pine Mountain trail + Jefferson NF WMA opened zoomed out with the overlap in a corner): fit to the MAIN
       place only (the biggest, first in the list), so it sits zoomed in, in the middle; the other stretches/places are still drawn */
    var main = visiblePatches(g)[0], b = L.latLngBounds([]);
    cur.rings.forEach(function (x) { if (x.s === main) x.ring.forEach(function (p) { b.extend([p[1], p[0]]); }); });
    if (!b.isValid()) cur.rings.forEach(function (x) { x.ring.forEach(function (p) { b.extend([p[1], p[0]]); }); });
    /* the map was hidden in the LIST tab (size 0), so Leaflet fitted to nothing and showed the whole world: size it first, fit again once shown */
    cur.fit = b;
    /* Brandon Oct 27 6:03 PM ('would it be better with several overlaps to show them all'): open on the main one, and a button on the map
       flips to all of them and back */
    var all = L.latLngBounds([]); cur.rings.forEach(function (x) { x.ring.forEach(function (p) { all.extend([p[1], p[0]]); }); }); cur.fitAll = all; cur.wide = false; cur.pi = Math.max(0, cur.rings.findIndex(function (x) { return x.s === main; }));
    zoomBtn();
    var mz = openRow.maxZ || 17; openRow.maxZ = 0;   // Oct 28 (Brandon: 'super zoomed in'): open at 17 at most (16 from the state map)
    if (b.isValid()) { map.invalidateSize(); map.fitBounds(b.pad(0.04), { maxZoom: mz, animate: false }); setTimeout(function () { if (cur === g) { map.invalidateSize(); map.fitBounds(b.pad(0.04), { maxZoom: mz, animate: false }); } }, 120); }
    try { history.replaceState(null, '', '?region=' + encodeURIComponent(REG.id) + '&id=' + encodeURIComponent(key)); } catch (e) {}
    $('ovReport').href = reportUrl(g);
    loadOutlines(g).then(function () { if (cur !== g) return; animate(); sharpen(g); });
    draw();
  }
  /* Brandon Oct 27 6:11 PM: 'add in the same button if it has several overlaps look at next section': ◀ 1 OF 3 ▶ steps through each
     place / stretch (biggest first), 🔭 ALL shows every one. Taps on the bar never reach the map (it used to pop up the land card). */
  function ringB(x) { var b = L.latLngBounds([]); x.ring.forEach(function (p) { b.extend([p[1], p[0]]); }); return b; }
  function zoomBtn() {
    var bt = $('ovZoomAll');
    if (!bt) { bt = document.createElement('div'); bt.id = 'ovZoomAll'; bt.className = 'ov-zall'; $('ovMap').parentNode.appendChild(bt);
      if (window.L && L.DomEvent) { L.DomEvent.disableClickPropagation(bt); L.DomEvent.disableScrollPropagation(bt); }
      ['click', 'pointerdown', 'mousedown', 'touchstart', 'dblclick'].forEach(function (ev) { bt.addEventListener(ev, function (e) { e.stopPropagation(); }); });
      bt.addEventListener('click', function (e) { var b = e.target.closest('[data-z]'); if (!b || !cur || !map) return; e.preventDefault(); var n = cur.rings.length, z = b.dataset.z;
        if (z === 'all') { cur.wide = !cur.wide; map.fitBounds((cur.wide ? cur.fitAll : ringB(cur.rings[cur.pi])).pad(cur.wide ? 0.08 : 0.04), { maxZoom: 18 }); }
        else { cur.wide = false; cur.pi = (cur.pi + (z === 'next' ? 1 : -1) + n) % n; map.fitBounds(ringB(cur.rings[cur.pi]).pad(0.04), { maxZoom: 18 }); }
        zoomBtn(); }); }
    var n = cur ? cur.rings.length : 0; bt.hidden = n < 2; if (n < 2) return;
    var w = cur.trail ? 'STRETCH' : 'PLACE';
    bt.innerHTML = '<button type="button" data-z="prev" aria-label="Previous ' + w.toLowerCase() + '">◀</button><span>' + (cur.wide ? 'ALL ' + n + ' ' + w + 'ES'.slice(cur.trail ? 0 : 1) : w + ' ' + (cur.pi + 1) + ' OF ' + n) + '</span><button type="button" data-z="next" aria-label="Next ' + w.toLowerCase() + '">▶</button><button type="button" data-z="all">' + (cur.wide ? '🎯 ONE' : '🔭 ALL') + '</button>';
  }
  function openPlace(key, i) {
    if (!cur || cur.key !== key) openRow(key); else showTab('map');
    var s = visiblePatches(cur)[i]; if (!s || !map) return;
    var b = L.latLngBounds([]); [s].concat(s._kids || []).forEach(function (x) { (x.shape || []).forEach(function (q) { b.extend([q[1], q[0]]); }); });
    setTimeout(function () { if (b.isValid()) map.fitBounds(b.pad(0.08), { maxZoom: 18 }); }, cur.key === key ? 0 : 400);
    scrollTo({ top: $('ovMap').getBoundingClientRect().top + scrollY - 100, behavior: 'smooth' });
  }
  /* Oct 28 (chat 2, Brandon OK: 'Mammoth Cave x Green River WR looked tangled'): only the pieces of each park's land NEAR the overlap are
     drawn (a polygon whose box touches the overlap's box + a margin); far-off owned-land pieces are left off the map */
  /* HQ + Brandon Oct 29 7:18 AM: close-ups at ~3 m. Once the outlines are drawn, the parks' records near this spot are asked again at
     ~3 m detail for the spot's small box (KPCB.closeUp, 1.5 s limit) and swapped in; nothing waits on it, a slow server = no change */
  function spotBox(g) { var bb = [180, 90, -180, -90]; patchRings(g).forEach(function (x) { x.ring.forEach(function (q) { bb[0] = Math.min(bb[0], q[0]); bb[1] = Math.min(bb[1], q[1]); bb[2] = Math.max(bb[2], q[0]); bb[3] = Math.max(bb[3], q[1]); }); });
    if (bb[0] > bb[2]) return null; var pad = Math.max(0.01, 0.3 * Math.max(bb[2] - bb[0], bb[3] - bb[1])); return [bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad]; }
  function sharpen(g, view) {
    var B = window.KPCB; if (!B || !B.closeUp) return; var box = view || spotBox(g); if (!box) return; var t0 = Date.now();
    Promise.all(parks.map(function (p) { return p.fsAll && p.fsAll.length ? B.closeUp(p.fsAll, box, 1500).then(function (fs) { return [p, fs]; }) : null; })).then(function (r) {
      if (cur !== g) return; var n = 0;
      r.forEach(function (x) { if (!x) return; var sharp = x[1].filter(function (f) { return f._sharp; }).length; if (!sharp) return; n += sharp; x[0].fsAll = x[1]; x[0].fs = near(g, x[1]); });
      SHARP = { n: n, ms: Date.now() - t0 }; if (n) draw();
    }).catch(function () {});
  }
  var SHARP = null;
  function near(g, fs) {
    var bb = [180, 90, -180, -90]; patchRings(g).forEach(function (x) { x.ring.forEach(function (q) { bb[0] = Math.min(bb[0], q[0]); bb[1] = Math.min(bb[1], q[1]); bb[2] = Math.max(bb[2], q[0]); bb[3] = Math.max(bb[3], q[1]); }); });
    if (bb[0] > bb[2]) return fs;
    var pad = Math.max(0.03, 0.75 * Math.max(bb[2] - bb[0], bb[3] - bb[1])), B = [bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad];
    var hits = function (poly) { var x0 = 180, y0 = 90, x1 = -180, y1 = -90; (poly[0] || []).forEach(function (q) { x0 = Math.min(x0, q[0]); y0 = Math.min(y0, q[1]); x1 = Math.max(x1, q[0]); y1 = Math.max(y1, q[1]); }); return !(x1 < B[0] || x0 > B[2] || y1 < B[1] || y0 > B[3]); };
    return fs.map(function (f) { var G = f.geometry;
      if (G.type === 'MultiPolygon') { var k = G.coordinates.filter(hits); return k.length ? Object.assign({}, f, { geometry: { type: 'MultiPolygon', coordinates: k } }) : null; }
      if (G.type === 'Polygon') return hits(G.coordinates) ? f : null;
      return f; }).filter(Boolean);
  }
  function loadOutlines(g) {
    var B = window.KPCB; if (!B) return Promise.resolve();
    return Promise.all(parks.map(function (p) {
      var trailPatch = g.patches.some(function (s) { return s.kind === 'trail' && s.line_source && s.line_source[p.ref]; });
      if (trailPatch) { p.line = true; return null; }   // a line park: its zone is the 100-ft band, drawn from the patch itself
      var ky = /^US-/.test(p.ref) && (g.st === 'KY' || /KY/.test(g.st));
      var pr = ky && B.kyFor ? B.kyFor(p.ref) : /^CA-/.test(p.ref) && B.canada ? B.canada(p.ref) : B.usOutline ? B.usOutline(p.ref, nm(g, p.ref), g.best.center[0], g.best.center[1], [String(g.st || '').replace(/^US-/, '')]).then(function (o) { return o && o.fs; }) : Promise.resolve(null);
      return Promise.resolve(pr).then(function (fs) { p.fsAll = (fs || []).filter(function (f) { return f && f.geometry; }); p.fs = near(g, p.fsAll); }).catch(function () { p.fs = []; p.fsAll = []; });
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
    if (p.line) cur.rings.forEach(function (x) { if (x.line && x.first) rings.push(x.band || x.ring); });
    else (p.fsAll || p.fs || []).forEach(function (f) { try { (B && B.ringsOf ? B.ringsOf(f.geometry) : []).forEach(function (poly) { poly.forEach(function (r) { rings.push(r); }); }); } catch (e) {} });
    if (!rings.length) return null;
    var c = map.getCenter(), box = [[c.lat - 3, c.lng - 4], [c.lat - 3, c.lng + 4], [c.lat + 3, c.lng + 4], [c.lat + 3, c.lng - 4]];
    return L.polygon([box].concat(rings.map(function (r) { return r.map(function (q) { return [q[1], q[0]]; }); })), { stroke: false, fillColor: '#000', fillOpacity: veilOp(), interactive: false, fillRule: 'evenodd' });
  }
  /* Brandon Oct 27 4:00 PM ('one park shaded light one color and the other park another … overlap is clear … I want the overlap to really stand out … let me see some examples'):
     LOOK 1 = grey outside + gold patch (before); 2 = each park tinted its own colour, the overlap CLEAR with a bold white + black dashed border;
     3 = each park tinted, the overlap bright gold with a white glowing border; 4 = grey outside, the overlap clear with a moving gold/black border. */
  var look = +(new URLSearchParams(location.search).get('look') || 4) || 4;   /* Brandon Oct 27 4:06 PM picked LOOK 4 ('4!'): grey outside, the overlap clear with a moving gold/black border */
  function tint(p, f, cls, act) {
    var B = window.KPCB; (B && B.ringsOf ? B.ringsOf(f.geometry) : []).forEach(function (poly) {
      var ll = poly.map(function (r) { return r.map(function (q) { return [q[1], q[0]]; }); });
      if (look === 2) cur.rings.forEach(function (x) { var c = x.s.center ? [x.s.center[1], x.s.center[0]] : x.ring[0], hit = poly[0] && (pip(c[0], c[1], poly[0]) || x.ring.some(function (q) { return pip(q[0], q[1], poly[0]); })); if (hit) ll.push(x.ring.map(function (q) { return [q[1], q[0]]; })); });   /* the overlap punched out of the piece it sits in: it stays clear */
      gAll.addLayer(L.polygon(ll, { color: p.c, weight: 3, dashArray: p.dash, fillColor: p.c, fillOpacity: 0.3, fillRule: 'evenodd', className: cls, interactive: act }).bindPopup(parkPop(p)));
    });
  }
  function liveLines() { var o = []; if (cur) visiblePatches(cur).forEach(function (s) { [s].concat(s._kids || []).forEach(function (x) { if (x.lines && typeof x.lines === 'object') o.push(x.lines); }); }); return o; }
  /* Brandon Oct 27 6:16 PM ('this boundary looks funky like part of 2fer out of bounds'): a trail's 100-ft band was drawn whole, even
     where it leaves the other park. The band (and its gold border) is now CLIPPED to the other park's outline on the map (SVG clip),
     so only ground that is near the trail AND inside the other park shows as the overlap; the other park's line inside the band is
     drawn gold too, so the clipped patch keeps a full gold border. Re-clipped after every zoom/move (Leaflet redraws the paths). */
  function clipTrail() {
    var svg = map && document.querySelector('#ovMap .leaflet-overlay-pane svg'); if (!svg) return;
    if (!cur || !cur.trail) { var og = svg.querySelector('path.ov-edgegold'); if (og) og.remove(); return; }
    var tg = svg.querySelectorAll('path.ov-tclip'), polys = parks.filter(function (p) { return !p.line && p.on && p._g && p._g.length; });
    var defs = svg.querySelector('defs') || svg.insertBefore(document.createElementNS('http://www.w3.org/2000/svg', 'defs'), svg.firstChild);
    var cp = defs.querySelector('#ovClipP'); if (!cp) { cp = document.createElementNS('http://www.w3.org/2000/svg', 'clipPath'); cp.id = 'ovClipP'; cp.setAttribute('clipPathUnits', 'userSpaceOnUse'); defs.appendChild(cp); }
    var cb = defs.querySelector('#ovClipB'); if (!cb) { cb = document.createElementNS('http://www.w3.org/2000/svg', 'clipPath'); cb.id = 'ovClipB'; cb.setAttribute('clipPathUnits', 'userSpaceOnUse'); defs.appendChild(cb); }
    var d = []; polys.forEach(function (p) { p._g.forEach(function (gl) { gl.eachLayer(function (l) { if (l._path) d.push(l._path.getAttribute('d') || ''); }); }); });
    d = d.join(' ').trim();
    if (!d) { [].forEach.call(tg, function (e) { e.removeAttribute('clip-path'); }); return; }
    cp.innerHTML = ''; var pp = document.createElementNS('http://www.w3.org/2000/svg', 'path'); pp.setAttribute('d', d); pp.setAttribute('clip-rule', 'evenodd'); cp.appendChild(pp);
    [].forEach.call(tg, function (e) { e.setAttribute('clip-path', 'url(#ovClipP)'); });
    /* the other park's own edge where it crosses the band: a gold copy clipped to the band */
    var bd = [].map.call(svg.querySelectorAll('path.ov-tclip.ov-band'), function (e) { return e.getAttribute('d') || ''; }).join(' ').trim();
    cb.innerHTML = ''; if (bd) { var bp = document.createElementNS('http://www.w3.org/2000/svg', 'path'); bp.setAttribute('d', bd); cb.appendChild(bp); }
    var gold = svg.querySelector('path.ov-edgegold'); if (step > parks.length && bd && OVON && !cur.rings.some(function (x) { return x.zone; })) {   /* a pass-5 zone is already the exact border: no screen-made gold edge from the saved copy */ if (!gold) { gold = document.createElementNS('http://www.w3.org/2000/svg', 'path'); gold.setAttribute('class', 'ov-edgegold'); svg.querySelector('g').appendChild(gold); }
      gold.setAttribute('d', d); gold.setAttribute('fill', 'none'); gold.setAttribute('stroke', '#ffd34d'); gold.setAttribute('stroke-width', '4'); gold.setAttribute('stroke-dasharray', '14 10'); gold.setAttribute('clip-path', 'url(#ovClipB)'); gold.style.pointerEvents = 'none'; }
    else if (gold) gold.remove();
  }
  function draw() {
    if (!map || !cur) return; gAll.clearLayers();
    var act = !mode;   /* in pin / measure mode the shapes let the tap through to the map */
    var hasLines = liveLines().length > 0;
    if (shade && step > 0 && (look === 1 || look === 4)) parks.forEach(function (p, i) { if (!p.on || i >= step) return; var v = veil(p); if (v) gAll.addLayer(v); });
    parks.forEach(function (p) { p._g = []; });
    parks.forEach(function (p, i) {
      if (!p.on || i >= step) return;
      var cls = fading && i === step - 1 ? 'ov-in' : '';
      (p.fs || []).forEach(function (f) {
        if (look === 2 || look === 3) { tint(p, f, cls, act); return; }
        var gl = L.geoJSON(f, { style: { color: p.c, weight: 3, opacity: hasLines ? 0.35 : 1, dashArray: p.dash, fillColor: p.c, fillOpacity: shade ? 0 : 0.08, className: cls }, interactive: act }).bindPopup(parkPop(p)); gAll.addLayer(gl); p._g.push(gl); });
      /* Brandon Oct 27 5:29 PM ('the overlap lines … do not look like they follow the boundary lines'): the gold border is cut from the agency's
         LIVE full-detail map, the park lines above are our saved copy (a few yards different, up to ~20). When the data carries the live
         edges near the spot (s.lines {ref: [[[lon,lat]…]…]}, chat 2), they are drawn bold and the saved copy goes faint. */
      liveLines().forEach(function (x) { (x[p.ref] || []).forEach(function (ln) { gAll.addLayer(L.polyline(ln.map(function (q) { return [q[1], q[0]]; }), { color: p.c, weight: 3, dashArray: p.dash, className: cls, interactive: false })); }); });
      if (p.line) cur.rings.forEach(function (x) { if (x.line && x.first) { gAll.addLayer(L.polygon((x.band || x.ring).map(function (q) { return [q[1], q[0]]; }), { color: p.c, weight: 1, fillColor: p.c, fillOpacity: 0.18, dashArray: '4 4', className: cls + ' ov-tclip ov-band', interactive: act }).bindPopup(parkPop(p)));
        gAll.addLayer(L.polyline(x.line.map(function (q) { return [q[1], q[0]]; }), { color: p.c, weight: 3, dashArray: p.dash, className: cls })); } });
    });
    if (step > parks.length && OVON) cur.rings.forEach(function (x) {
      var ll = x.ring.map(function (q) { return [q[1], q[0]]; }), fc = (fading ? ' ov-in-patch' : '') + (x.line && !x.zone ? ' ov-tclip' : '');
      if (look === 1) gAll.addLayer(L.polygon(ll, { color: '#b8860b', weight: 2, fillColor: '#ffd34d', fillOpacity: 0.6, className: fc, interactive: act }).bindPopup(patchPop(x.s)));
      else if (look === 2) { gAll.addLayer(L.polygon(ll, { color: '#ffffff', weight: 8, opacity: 0.95, fillOpacity: 0, className: fc, interactive: false })); gAll.addLayer(L.polygon(ll, { color: '#111', weight: 3, dashArray: '10 6', fill: true, fillOpacity: 0, className: fc, interactive: act }).bindPopup(patchPop(x.s))); }
      else if (look === 3) gAll.addLayer(L.polygon(ll, { color: '#ffffff', weight: 5, fillColor: '#ffd34d', fillOpacity: 0.85, className: 'ov-glow' + fc, interactive: act }).bindPopup(patchPop(x.s)));
      else { gAll.addLayer(L.polygon(ll, { color: '#111', weight: 7, opacity: 0.85, fillOpacity: 0, className: fc, interactive: false })); gAll.addLayer(L.polygon(ll, { color: '#ffd34d', weight: 4, dashArray: '14 10', fill: true, fillColor: '#ffd34d', fillOpacity: 0.2, className: 'ov-march' + fc, interactive: act }).bindPopup(patchPop(x.s))); }
    });
    parks.forEach(function (p, i) { if (i >= step || !p.on) return; var c = (p.fs && p.fs[0] && L.geoJSON(p.fs[0]).getBounds().getCenter()) || (cur.rings[0] && L.latLng(cur.rings[0].ring[0][1], cur.rings[0].ring[0][0]));
      if (c) gAll.addLayer(L.marker(c, { interactive: !mode, icon: L.divIcon({ className: '', html: '<span class="ov-plab" style="border-color:' + p.c + '"><span class="ov-num" style="background:' + p.c + '">' + p.n + '</span>' + esc(p.ref) + '</span>', iconSize: null, iconAnchor: [14, 14] }) }).bindPopup(parkPop(p))); });
    var pins = []; visiblePatches(cur).forEach(function (s) { [s.access_pin].concat(s.pins || []).forEach(function (a) { if (a && a.at && pins.length < 3 && !pins.some(function (q) { return q.at[0] === a.at[0] && q.at[1] === a.at[1]; })) pins.push(a); }); });
    pins.forEach(function (a) { gAll.addLayer(L.marker(a.at, { interactive: !mode, icon: L.divIcon({ className: '', html: '<span style="display:inline-grid;place-items:center;width:24px;height:24px;border-radius:5px;background:#1d4d7a;color:#fff;border:2px solid #fff;font:900 14px Arial">P</span>', iconSize: [24, 24], iconAnchor: [12, 12] }) })
      .bindPopup('<b>Closest spot to public access</b><br>' + esc(a.name || '') + ' (' + esc(a.from || '') + '), about ' + Math.round((a.walk_m || 0) * YD) + ' yards from it.<br><small>' + esc(a.note || '') + '</small><br><a target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination=' + a.at[0] + ',' + a.at[1] + '">Directions (to the access, not to the overlap)</a><span class="ov-short">' + SHORT + '</span>')); });
    if (meas.length) { gAll.addLayer(L.polyline(meas, { color: '#d55e00', weight: 3 })); meas.forEach(function (m) { gAll.addLayer(L.circleMarker(m, { radius: 5, color: '#d55e00' })); }); }
    setTimeout(clipTrail, 0);
    if (gps) { gAll.addLayer(L.circle(gps.p, { radius: gps.acc / YD, color: '#1e78ff', weight: 1, fillOpacity: 0.15 })); gAll.addLayer(L.circleMarker(gps.p, { radius: 7, color: '#fff', weight: 3, fillColor: '#1e78ff', fillOpacity: 1 })); }
  }
  /* Brandon Oct 27 3:13 PM ('The private property in a park needs better clarification'): tap any spot on the map = which park
     land it is on by the official outlines. Grey inside a park's outer line = land the park does NOT own or manage (private
     property or another owner): not part of the park, even though it sits inside the park. */
  /* Brandon Oct 27 3:37 PM ('Drop a pin … options to open in KPC Trip Planner'): the US Trip Planner's shared-trip link = the dropped pin */
  function tripLink(lat, lon) {
    var t = 'pin:' + lat.toFixed(5) + ',' + lon.toFixed(5) + ',' + encodeURIComponent('Dropped pin');   /* Brandon 3:41 PM: open with just the dropped pin */
    return '<p style="margin:8px 0 0"><a target="_blank" rel="noopener" href="kpc-planner-us.html?t=' + encodeURIComponent(t) + '">🧭 OPEN IN KPC TRIP PLANNER</a> · <a href="#" onclick="var t=\'' + lat.toFixed(6) + ', ' + lon.toFixed(6) + '\';try{navigator.clipboard.writeText(t);this.textContent=\'COPIED: \'+t}catch(e){prompt(\'Copy the GPS:\',t)}return false">📋 COPY GPS</a> · <a target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination=' + lat.toFixed(5) + ',' + lon.toFixed(5) + '">DIRECTIONS</a></p>';
  }
  function landAt(lat, lon) {
    var B = window.KPCB, ins = parks.map(function (q) { if (q.line) return cur.rings.some(function (x) { return x.line && pip(lon, lat, x.band || x.ring); }); var A = q.fsAll || q.fs; if (!A || !A.length || !B) return null; return A.some(function (f) { return B.inside(lat, lon, f.geometry); }); });
    var inN = parks.filter(function (q, i) { return ins[i]; }), outN = parks.filter(function (q, i) { return ins[i] === false; }), unk = ins.some(function (x) { return x === null; });
    var t = !inN.length ? '<b style="color:#7a1d0e">⛔ Not park land on our maps.</b><br>None of these parks owns or manages this spot: it is private property or another owner\'s land' + (unk ? '' : ', even if it sits inside a park\'s outer line') + '. Do not set up here.'
      : !outN.length ? '<b style="color:#1d5a3a">✅ Inside both outlines by our maps.</b><br>' + inN.map(function (q) { return esc(q.ref); }).join(' + ')
      : '<b style="color:#8a5a00">🟡 Inside ' + inN.map(function (q) { return esc(q.ref); }).join(', ') + ' only.</b><br>Not part of ' + outN.map(function (q) { return esc(q.ref) + ' ' + esc(nm(cur, q.ref)); }).join(', ') + ' here (that park does not own or manage this land).';
    return t + '<br><small>Official outlines can be off by several yards: check the agency map.</small>';
  }
  function parkPop(p) { var s = cur.best, m = (s.maps || []).filter(function (x) { return x[0] === p.ref; })[0];
    return '<span class="ov-num" style="background:' + p.c + ';display:inline-grid;width:22px;height:22px;border-radius:50%;place-items:center;font-weight:900">' + p.n + '</span> <b>' + esc(p.ref) + ' · ' + esc(nm(cur, p.ref)) + '</b>' + (p.line ? '<br>A line park: the band = POTA\'s 100 ft from the line.' : '') +
      '<br>' + (m ? '<a target="_blank" rel="noopener" href="' + esc(m[1]) + '">Official map</a> · ' : '') + '<a target="_blank" rel="noopener" href="https://pota.app/#/park/' + esc(p.ref) + '">POTA page</a>'; }   /* Brandon: the overlap message only on the overlap */
  function patchPop(s) { return '<b>' + (s.kind === 'trail' ? 'Possible trail overlap (100-ft band)' : s.kind === 'river' ? 'Possible river overlap (100 ft from the bank)' : 'Possible overlap') + '</b><br>' + cur.refs.map(function (r) { return '<b>' + esc(r) + '</b> ' + esc(nm(cur, r)); }).join('<br>') + '<br>' + (s.wide_m ? 'Fits a circle about ' + Math.round(s.wide_m * YD) + ' yards across' + (s.acres ? ' · ' + (+s.acres).toFixed(1) + ' acres' : '') + '<br>' : s.len_m ? 'About ' + Math.round(s.len_m * YD) + ' yards of trail<br>' : '') +
    'Last checked ' + esc(s.checked || '') + '<span class="ov-short">' + SHORT + '</span>'; }
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
    var ks = store('kpcOvKey'), open = ks ? ks !== '0' : innerWidth > 700;   /* phones start with the key folded */
    el.innerHTML = '<button type="button" class="ov-kh" data-key>' + (open ? '▾ KEY (HIDE)' : '▸ KEY') + '</button>' + (open ? '<div class="ov-kb">' : '<div class="ov-kb" hidden>') + parks.map(function (p) { return '<div><span class="ov-num" style="background:' + p.c + '">' + p.n + '</span><svg width="26" height="8" aria-hidden="true"><path d="M1 4h24" stroke="' + p.c + '" stroke-width="4" stroke-dasharray="' + p.dash + '"/></svg><b>' + esc(p.ref) + '</b> ' + esc(nm(cur, p.ref)) + (p.line ? ' (100-ft band)' : '') + '</div>'; }).join('') +
      (look === 2 || look === 3 ? parks.map(function (p) { return '<div><span class="ov-sw" style="background:' + p.c + ';opacity:.45"></span>' + esc(p.ref) + ' land</div>'; }).join('') + '<div>no colour = NOT park land (private property or another owner), even inside a park\'s outer line</div><div>👆 Tap any spot to see whose land it is.</div>' : (shade ? '<div><span class="ov-sw" style="background:#000;opacity:.5"></span><b>dark grey = NOT park land</b>: private property or another owner, even inside a park\'s outer line. Don\'t set up there.</div><div><span class="ov-sw" style="background:#000;opacity:.25"></span>light grey = land of one park only</div><div>👆 Tap any spot on the map to see whose land it is.</div>' : '<div><span class="ov-sw" style="background:' + (parks[0] ? parks[0].c : '#999') + ';opacity:.3"></span>light tint in a park\'s colour = inside that park</div>')) +
      (look === 2 ? '<div><span class="ov-sw" style="background:#fff;border:3px dashed #111"></span><b>clear with a black-and-white border = inside both parks: where our maps suggest they may overlap</b></div>' : look === 4 ? '<div><span class="ov-sw" style="background:#fff;border:3px dashed #d5a63a;outline:2px solid #111"></span><b>clear with a moving gold border = inside both parks: where our maps suggest they may overlap</b></div>' : '<div><span class="ov-sw" style="background:#ffd34d;border:2px solid ' + (look === 3 ? '#fff' : '#b8860b') + '"></span><b>gold = inside both parks: where our maps suggest they may overlap</b></div>') + '</div>';
    var kb = el.querySelector('[data-key]'); if (kb) kb.onclick = function (e) { e.preventDefault(); store('kpcOvKey', open ? '0' : '1'); mapKey(); };
  }
  var OVON = true;   // Oct 28 (Brandon): the overlap (moving gold line) can be switched off too, to look at one park's boundary at a time
  function legend() { $('ovLeg').innerHTML = '<li><span class="ov-num" style="background:#ffd34d;color:#111">★</span><svg width="34" height="10" aria-hidden="true"><path d="M2 5h30" stroke="#ffd34d" stroke-width="4" stroke-dasharray="8 5"/></svg><label><input type="checkbox" data-on="ov"' + (OVON ? ' checked' : '') + '> <b>The overlap</b> (moving gold line)</label></li>' + parks.map(function (p, i) { return '<li><span class="ov-num" style="background:' + p.c + '">' + p.n + '</span><svg width="34" height="10" aria-hidden="true"><path d="M2 5h30" stroke="' + p.c + '" stroke-width="4" stroke-dasharray="' + p.dash + '"/></svg><label><input type="checkbox" data-on="' + i + '"' + (p.on ? ' checked' : '') + '> <b>' + esc(p.ref) + '</b> ' + esc(nm(cur, p.ref)) + (p.line ? ' <i>(line: 100-ft band)</i>' : '') + '</label></li>'; }).join(''); }

  /* ---------- GPS walk-in / dropped pin ---------- */
  function status(p, acc, isPin) {
    if (!cur) return; var lat = p[0], lon = p[1], g = $('ovGps'), cls = 'out', t = '', body = '', who = isPin ? 'the pin' : 'you', look = isPin ? ' looks' : ' look';
    var inPatch = null, dPatch = 1e12; cur.rings.forEach(function (x) { var inn = pip(lon, lat, x.ring), d = edgeM(lon, lat, x.ring, true); if (inn && !inPatch) inPatch = x; dPatch = Math.min(dPatch, d); });
    var B = window.KPCB, n = parks.length, ins = parks.map(function (q) { if (q.line) return cur.rings.some(function (x) { return x.line && pip(lon, lat, x.band || x.ring); }); var A = q.fsAll || q.fs; if (!A || !A.length || !B) return null; return A.some(function (f) { return B.inside(lat, lon, f.geometry); }); });
    var known = ins.filter(function (x) { return x !== null; }).length, k = ins.filter(Boolean).length, accM = acc / YD;
    if (inPatch) {
      if (accM > dPatch) { cls = 'edge'; t = '⚠️ TOO CLOSE TO THE EDGE TO TELL'; body = 'GPS is good to about ±' + Math.round(acc) + ' yards and the edge of the lit patch is ' + Math.round(dPatch * YD) + ' yards away. Step farther in; we never guess.'; }
      else { cls = 'in'; t = '✅ By our maps ' + who + look + ' inside ' + (n === 2 ? 'both outlines' : 'all ' + n + ' outlines'); var s = inPatch.s;
        body = 'About ' + Math.round(dPatch * YD) + ' yards to the edge of the lit patch.' + (s.wide_m ? ' Patch ' + Math.round(s.wide_m * YD) + ' yards across.' : '') + ' Last checked ' + esc(s.checked || '') + '.<br><b>Keep your whole station inside the lit patch: radio, antenna, operator.</b>'; }
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
  function tools() { [].forEach.call(document.querySelectorAll('#ovTools [data-t]'), function (b) { var t = b.dataset.t; if (/^(street|sat|topo)$/.test(t)) b.classList.toggle('on', t === layerName); if (t === 'pin' || t === 'measure') b.classList.toggle('on', mode === t); if (t === 'gps') b.classList.toggle('on', watch != null); if (t === 'shade') b.classList.toggle('on', shade); if (/^look/.test(t)) b.classList.toggle('on', t === 'look' + look); }); }
  document.addEventListener('click', function (e) {
    var pl = e.target.closest('#ov [data-place]');
    if (pl) { e.preventDefault(); var kk = pl.dataset.place.split('|'); openPlace(kk[0], +kk[1]); return; }
    var b = e.target.closest('#ov [data-tab], #ov [data-open], #ov [data-t], #ov [data-f], #ov [data-on], #ovAllOn, #ovAllOff, #ov [data-region]'); if (!b) return;
    if (b.matches('[data-on]')) { if (b.dataset.on === 'ov') OVON = b.checked; else parks[+b.dataset.on].on = b.checked; draw(); clipTrail(); return; }
    e.preventDefault();
    if (b.matches('[data-tab]')) { showTab(b.dataset.tab); if (b.dataset.tab === 'map' && !cur && ROWS.length) { var first = ROWS.filter(function (g) { return visiblePatches(g).length; })[0]; if (first) openRow(first.key); else mkMap(); } return; }
    if (b.matches('[data-open]')) { openRow(b.dataset.open);   /* only the SHOW buttons open the map (Brandon: 'See more takes me to map') */ scrollTo({ top: $('ovMap').getBoundingClientRect().top + scrollY - 100, behavior: 'smooth' }); return; }
    if (b.matches('[data-region]')) { loadRegion(b.dataset.region); return; }
    if (b.id === 'ovAllOn' || b.id === 'ovAllOff') { OVON = b.id === 'ovAllOn'; parks.forEach(function (p) { p.on = b.id === 'ovAllOn'; }); legend(); draw(); clipTrail(); return; }
    if (b.matches('[data-f]')) { var f = b.dataset.f;
      if (f === 'near') { if (F.near) { F.near = false; b.classList.remove('on'); $('ovNearNote').hidden = true; list(); return; }
        if (!navigator.geolocation) { toast('This browser cannot give a location.'); return; }
        navigator.geolocation.getCurrentPosition(function (pos) { here = [pos.coords.latitude, pos.coords.longitude]; F.near = true; b.classList.add('on'); $('ovNearNote').hidden = false; list(); }, function () { toast('Location not shared, so the list stays in order.'); }, { timeout: 15000, maximumAge: 300000 }); return; }
      F[f] = !F[f]; b.setAttribute('aria-pressed', String(F[f])); list(); return; }
    var t = b.dataset.t; if (!cur && t !== 'street' && t !== 'sat' && t !== 'topo') { toast('Pick a result first.'); return; }
    if (t === 'replay') { clearTimeout(timer); animate(); }
    else if (t === 'all') { clearTimeout(timer); step = parks.length + 1; draw(); }
    else if (t === 'shade') { shade = !shade; draw(); mapKey(); }
    else if (/^look[1-4]$/.test(t)) { look = +t.slice(4); store('kpcOvLook', String(look)); draw(); mapKey(); }
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
  /* Brandon Oct 27 5 PM: 'might as well have a drop down now for states and provinces': every US state + Canadian province; the ones
     with a checked list come first, the rest say 'not checked yet' (picking one says so plainly, never an empty 'no overlaps') */
  var PLACES = { US: 'AL Alabama|AK Alaska|AZ Arizona|AR Arkansas|CA California|CO Colorado|CT Connecticut|DE Delaware|DC District of Columbia|FL Florida|GA Georgia|HI Hawaii|ID Idaho|IL Illinois|IN Indiana|IA Iowa|KS Kansas|KY Kentucky|LA Louisiana|ME Maine|MD Maryland|MA Massachusetts|MI Michigan|MN Minnesota|MS Mississippi|MO Missouri|MT Montana|NE Nebraska|NV Nevada|NH New Hampshire|NJ New Jersey|NM New Mexico|NY New York|NC North Carolina|ND North Dakota|OH Ohio|OK Oklahoma|OR Oregon|PA Pennsylvania|RI Rhode Island|SC South Carolina|SD South Dakota|TN Tennessee|TX Texas|UT Utah|VT Vermont|VA Virginia|WA Washington|WV West Virginia|WI Wisconsin|WY Wyoming',
    CA: 'AB Alberta|BC British Columbia|MB Manitoba|NB New Brunswick|NL Newfoundland and Labrador|NS Nova Scotia|NT Northwest Territories|NU Nunavut|ON Ontario|PE Prince Edward Island|QC Quebec|SK Saskatchewan|YT Yukon' };
  function regionOf(cc, code) { return CFG.regions.filter(function (r) { return r.id === code && cc === 'US' || (r.files || []).indexOf(cc + '-' + code) >= 0; })[0]; }
  function regionSelect() {
    var done = CFG.regions.map(function (r) { return '<option value="' + esc(r.id) + '">' + esc(r.label) + (r.beta ? ' · BETA' : '') + (r.public ? '' : ' (members)') + '</option>'; }).join('');
    var grp = function (cc, lab) { return '<optgroup label="' + lab + ' (no list yet)">' + PLACES[cc].split('|').map(function (x) { var c = x.slice(0, 2), n = x.slice(3); return regionOf(cc, c) ? '' : '<option value="' + cc + '-' + c + '">' + esc(n) + '</option>'; }).join('') + '</optgroup>'; };
    $('ovRegions').innerHTML = '<label for="ovReg"><b>STATE / PROVINCE</b></label><select id="ovReg"><optgroup label="With a list">' + done + '</optgroup>' + grp('US', 'US states') + grp('CA', 'Canada') + '</select>' +
      '<span class="ov-sort" role="group" aria-label="Sort the parks"><b>SORT</b><button type="button" data-sort="num">BY NUMBER</button><button type="button" data-sort="az">A–Z</button></span>';
    $('ovReg').addEventListener('change', function () { US_PICK = true; loadRegion(this.value); usMark(); });
  }
  /* Oct 28 (Brandon: 'under the hero have a state level clickable map'): every state drawn from kpc-us-states.json; gold = a
     checked list, grey = not checked yet; a tap does what the STATE / PROVINCE box does. Alaska + Hawaii in small boxes. */
  var US_P = null;
  function usMap() {
    var svg = $('ovUsMap'); if (!svg) return;
    (US_P || (US_P = j('kpc-us-states.json'))).then(function (B) {
      if (!B || !B.length) { svg.closest('.ov-us').hidden = true; return; }
      var c38 = Math.cos(38 * Math.PI / 180);
      var proj = function (a) {   // lower 48: a plain lon/lat picture squeezed for latitude; AK + HI moved into boxes bottom-left
        if (a === 'AK') return function (x, y) { return [40 + (x + 172) * 10 * Math.cos(62 * Math.PI / 180), 556 - (y - 51) * 10 * .55]; };
        if (a === 'HI') return function (x, y) { return [270 + (x + 160.5) * 17 * Math.cos(20 * Math.PI / 180), 552 - (y - 18.8) * 17]; };
        return function (x, y) { return [60 + (x + 125) * 18 * c38, 8 + (49.6 - y) * 18 * 1.08]; };
      };
      var html = '';
      B.forEach(function (st) {
        var P = proj(st.a), d = '';
        (st.p || []).forEach(function (poly) { (poly || []).forEach(function (ring) {
          if (st.a === 'AK') ring = ring.filter(function (q) { return q[0] < -129 || q[1] > 54.5; }).map(function (q) { return [q[0] > 0 ? q[0] - 360 : q[0], q[1]]; });
          if (ring.length < 3) return;
          d += 'M' + ring.map(function (q) { var v = P(q[0], q[1]); return v[0].toFixed(1) + ',' + v[1].toFixed(1); }).join('L') + 'Z';
        }); });
        if (!d) return;
        var r = regionOf('US', st.a), id = r ? r.id : 'US-' + st.a;
        html += '<path d="' + d + '" data-r="' + esc(id) + '" class="' + (r ? 'ck' : '') + '" tabindex="0" role="button" aria-label="' + esc(st.n) + (r ? ': has a list' : ': no list yet') + '"><title>' + esc(st.n) + (r ? '' : ' (no list yet)') + '</title></path>';
      });
      svg.innerHTML = html;
      US_VIEW = 'all'; vb(0, 0, 960, 560); var nt = $('ovUsN'); if (nt) nt.textContent = 'Tap a state'; var bk = $('ovUsBack'); if (bk) bk.hidden = true;
      if (!svg._wired) {
        svg._wired = true;
        var go = function (e) {
          if (svg._noTap) return;
          var dt = e.target.closest('.dot');
          if (dt) { openRow.maxZ = 16; openRow(dt.getAttribute('data-k')); var m = $('ovMap'); if (m) setTimeout(function () { scrollTo({ top: m.getBoundingClientRect().top + scrollY - 100, behavior: 'smooth' }); }, 300); return; }
          var t = e.target.closest('path'); if (!t || US_VIEW !== 'all') return;
          US_PICK = true; loadRegion(t.getAttribute('data-r'));
        };
        svg.addEventListener('click', go);
        svg.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(e); } });
        var bk2 = $('ovUsBack'); if (bk2) bk2.addEventListener('click', function () { US_PICK = false; usMap(); });
      }
      usMark();
    });
  }
  /* Oct 28 (Brandon: zoomed in on the page, a tap jumped to a super-zoomed map you could not zoom out of): the state map zooms by
     ITSELF (＋ / － and drag) so nobody needs to pinch the page; a dot opens the result at a normal zoom */
  var VB = [0, 0, 960, 560];
  function vb(x, y, w, h) {
    var svg = $('ovUsMap'); if (!svg) return; w = Math.min(960, Math.max(60, w)); h = w * 560 / 960;
    x = Math.min(960 - w, Math.max(0, x)); y = Math.min(560 - h, Math.max(0, y)); VB = [x, y, w, h];
    svg.setAttribute('viewBox', VB.map(function (v) { return v.toFixed(1); }).join(' '));
    var k = w / 960; [].forEach.call(svg.querySelectorAll('.dot circle'), function (c) { if (!c.dataset.r) c.dataset.r = c.getAttribute('r'); c.setAttribute('r', (+c.dataset.r * Math.max(.35, k)).toFixed(2)); });
    var zz = $('ovUsZ'); if (zz) zz.hidden = US_VIEW !== 'state';
  }
  function vbZoom(f) { var cx = VB[0] + VB[2] / 2, cy = VB[1] + VB[3] / 2, w = VB[2] / f; vb(cx - w / 2, cy - w * 560 / 960 / 2, w, 0); }
  (function () {
    var svg = $('ovUsMap'); if (!svg) return;
    var zz = document.createElement('div'); zz.id = 'ovUsZ'; zz.className = 'ov-usz'; zz.hidden = true;
    zz.innerHTML = '<button type="button" data-uz="in" aria-label="Zoom in">＋</button><button type="button" data-uz="out" aria-label="Zoom out">－</button>';
    svg.parentNode.insertBefore(zz, svg);
    zz.addEventListener('click', function (e) { var b = e.target.closest('[data-uz]'); if (b) vbZoom(b.dataset.uz === 'in' ? 2 : .5); });
    var drag = null;
    svg.addEventListener('pointerdown', function (e) { if (US_VIEW !== 'state' || VB[2] >= 960) return; drag = { x: e.clientX, y: e.clientY, v: VB.slice(), moved: false }; });
    svg.addEventListener('pointermove', function (e) { if (!drag) return; var r = svg.getBoundingClientRect(), k = drag.v[2] / r.width, dx = (e.clientX - drag.x) * k, dy = (e.clientY - drag.y) * k;
      if (Math.abs(dx) + Math.abs(dy) > 2) drag.moved = true; vb(drag.v[0] - dx, drag.v[1] - dy, drag.v[2], 0); });
    var end = function () { if (drag && drag.moved) { svg._noTap = true; setTimeout(function () { svg._noTap = false; }, 50); } drag = null; };
    svg.addEventListener('pointerup', end); svg.addEventListener('pointercancel', end); svg.addEventListener('pointerleave', end);
  })();
  function usMark() {
    var svg = $('ovUsMap'); if (!svg || !REG) return;
    [].forEach.call(svg.querySelectorAll('path'), function (p) { p.classList.toggle('on', p.getAttribute('data-r') === REG.id); });
  }
  /* Oct 28 (Brandon: 'state level shows the selected state with the areas with the overlaps'): a picked state is drawn big with a
     numbered dot at every result in the LIST (same filters); a dot = that result on the MAP below; ALL STATES = back. */
  var US_VIEW = 'all', US_PICK = false;   // the state view only after a person picks a state (the page opens on the whole map)
  function usState() {
    var svg = $('ovUsMap'); if (!svg || !US_P || !REG || !US_PICK) return;
    var sts = ((REG.files || []).map(function (f) { return (/^US-([A-Z]{2})$/.exec(f) || [])[1]; }).filter(Boolean));
    if (!sts.length && /^US-[A-Z]{2}$/.test(REG.id)) sts = [REG.id.slice(3)];
    if (!sts.length) { if (US_VIEW !== 'all') usMap(); return; }
    US_P.then(function (B) {
      var S = (B || []).filter(function (b) { return sts.indexOf(b.a) >= 0; }); if (!S.length) return;
      var x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
      S.forEach(function (st) { (st.p || []).forEach(function (poly) { (poly || []).forEach(function (ring) { ring.forEach(function (q) { x0 = Math.min(x0, q[0]); x1 = Math.max(x1, q[0]); y0 = Math.min(y0, q[1]); y1 = Math.max(y1, q[1]); }); }); }); });
      var k = Math.cos((y0 + y1) / 2 * Math.PI / 180), W = 960, H = 560, pad = 30;
      var sc = Math.min((W - 2 * pad) / ((x1 - x0) * k), (H - 2 * pad) / (y1 - y0));
      var ox = (W - (x1 - x0) * k * sc) / 2, oy = (H - (y1 - y0) * sc) / 2;
      var P = function (lon, lat) { return [ox + (lon - x0) * k * sc, oy + (y1 - lat) * sc]; };
      var html = '';
      S.forEach(function (st) {
        var d = '';
        (st.p || []).forEach(function (poly) { (poly || []).forEach(function (ring) { if (ring.length < 3) return; d += 'M' + ring.map(function (q) { var v = P(q[0], q[1]); return v[0].toFixed(1) + ',' + v[1].toFixed(1); }).join('L') + 'Z'; }); });
        html += '<path class="st' + (REG.none ? '' : ' ck') + '" d="' + d + '"><title>' + esc(st.n) + '</title></path>';
      });
      var n = 0;
      ROWS.forEach(function (g) {
        var ps = visiblePatches(g); if (!ps.length) return;
        if (g.trail ? !F.trail : !F[tierOf(ps[0])]) return; if (F.multi && g.n < 3) return;
        var c = (g.best && g.best.center) || ps[0].center; if (!c) return;
        var v = P(c[1], c[0]); n++;
        html += '<g class="dot" data-k="' + esc(g.key) + '" tabindex="0" role="button" aria-label="' + esc(g.refs.join(' + ')) + '"><title>' + esc(g.refs.join(' + ') + ' · ' + Object.values(g.names || {}).join(' + ')) + '</title><circle cx="' + v[0].toFixed(1) + '" cy="' + v[1].toFixed(1) + '" r="' + (g.n > 2 ? 9 : 7) + '"></circle></g>';
      });
      if (REG.none) html += '<text x="480" y="290" text-anchor="middle" class="nc">no list yet</text>';
      svg.innerHTML = html; US_VIEW = 'state'; vb(0, 0, 960, 560);
      var nt = $('ovUsN'); if (nt) nt.innerHTML = REG.none ? esc(REG.label) + ': no list yet' : '<b>' + esc(REG.label) + '</b>: ' + n + ' place' + (n === 1 ? '' : 's') + ' on this map (tap a dot)';
      var bk = $('ovUsBack'); if (bk) bk.hidden = false;
    });
  }
  function notChecked(id) {
    var m = /^(US|CA)-([A-Z]{2})$/.exec(id || ''); if (!m) return null; var hit = PLACES[m[1]].split('|').filter(function (x) { return x.slice(0, 2) === m[2]; })[0]; return hit ? { id: id, label: hit.slice(3), files: [], none: true } : null;
  }
  function loadRegion(id) {
    REG = CFG.regions.filter(function (r) { return r.id === id; })[0] || notChecked(id) || CFG.regions[0]; cur = null; closeSheet();
    if ($('ovReg')) $('ovReg').value = REG.id;
    if (REG.none) { ROWS = []; TIGHT = []; WATER = []; MISS = []; var nb0 = $('ovRegNote'); if (nb0) nb0.hidden = true; list(); return Promise.resolve(); }
    store('kpcOvRegion', REG.id);
    $('ovList').innerHTML = '<p class="ov-note">Loading ' + esc(REG.label) + '…</p>';
    var base = CFG.base || '../KPC-Data/data/fers/'; HB = base;
    return Promise.all(REG.files.map(function (f) { return jz(base + f + '.json'); }).concat([REG.missing && MEMBER ? j(base + REG.missing + '.json') : null])).then(function (a) {
      var files = a.slice(0, REG.files.length), miss = a[REG.files.length];
      if (files.some(function (x) { return !x; })) {   // offline: a saved copy that has not expired
        var sv = null; try { sv = JSON.parse(localStorage.getItem('kpcOvSave-' + REG.id) || 'null'); } catch (e) {}
        if (sv && sv.until > Date.now() && sv.files) { files = sv.files; toast('Offline: showing your saved copy (good until ' + new Date(sv.until).toDateString() + ').'); }
        else { $('ovList').innerHTML = '<div class="ov-empty"><b>Could not load the overlap list right now.</b> Nothing is shown rather than an old or guessed list. Try again with a signal.</div>'; return; }
      }
      SAVED[REG.id] = files; build(files, miss);
      var nb = $('ovRegNote'); if (!nb) { nb = document.createElement('div'); nb.id = 'ovRegNote'; nb.className = 'ov-empty'; nb.style.margin = '0 0 12px'; $('ovRegions').after(nb); }
      nb.hidden = !REG.note; nb.innerHTML = REG.note ? (REG.beta ? '🧪 ' : '🔄 ') + '<b>' + esc(REG.note) + '</b>' : '';
      if (MEMBER && REG.showWaiting) $('ovWait').checked = true;   // Brandon Oct 27 2:15 PM: 'members only … good with putting KY list on there for now to test it'
      list();
      var q = new URLSearchParams(location.search).get('id'); if (q && ROWS.some(function (r) { return r.key === q; })) { openRow(q); setTimeout(function () { scrollTo({ top: $('ovMap').getBoundingClientRect().top + scrollY - 100, behavior: 'smooth' }); }, 400); }   // a shared link lands on the map
    });
  }
  var list0 = list; list = function () { list0(); usState(); };
  Promise.all([j('kpc-fers-regions.json'), j('kpc-fers-reviewed.json')]).then(function (a) {
    CFG = a[0] || { regions: [] }; REV = (a[1] && a[1].reviewed) || {};
    CFG.regions = (CFG.regions || []).filter(function (r) { return r.public || MEMBER; });
    if (!CFG.regions.length) { $('ovList').innerHTML = '<div class="ov-empty"><b>We are still checking the parks.</b> Nothing is listed yet. This does not mean there are no overlaps.</div>'; return; }
    regionSelect();
    var q = new URLSearchParams(location.search).get('region'), want = q || store('kpcOvRegion');
    loadRegion(CFG.regions.some(function (r) { return r.id === want; }) ? want : CFG.regions[0].id);
    usMap();
  });
  window.KPCOverlap = { rows: function () { return ROWS; }, openRow: openRow, status: status, map: function () { return map; }, rings: function (g) { return patchRings(g); }, sharp: function () { return SHARP; } };
})();
