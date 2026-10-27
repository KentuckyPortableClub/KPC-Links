/* PARK OVERLAP FINDER: PREVIEW (chat 3, Oct 27; HQ/Brandon: 'build a PREVIEW … so Brandon can see how it will work').
   MADE-UP DATA ONLY (rule sheet C in .claude/notes/logger-lounge-digi.md): fake parks XX-0001…, fake names '(example)', on a
   made-up map in metres (no real places or coordinates). Shows the design in new-chat-starters.md ('PARK OVERLAP FINDER
   DESIGN' + 'N-FERS UP TO 9'): outlines draw in one park at a time and the lit patch narrows, 9 colours + 9 line patterns +
   number badges, on/off per park, rings where fewer parks overlap, line trails as the 100-ft band, sizes / acres / tiers worked
   out from the shapes, a GPS walk-in card (accuracy circle, 'too close to the edge to tell'), drop a pin, measure, the list
   with filters, confidence + proof badges, access + walking time, offline save that expires, report a mistake (dummy).
   Real data (data/fers/<ST>.json) plugs in later, after Brandon's GO and the rule sheet A rulings. */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var NS = 'http://www.w3.org/2000/svg', YD = 1.09361, FT = 3.28084, BAND = 30.48;   // POTA's 100 ft from a line = 30.48 m
  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  var SHORT = '⚠️ Possible POTA overlap only. We think these POTA parks\' boundaries may overlap here, but we can\'t confirm it. Check both official boundary maps and make your own call before you count it.';
  var COL = ['#E69F00', '#56B4E9', '#009E73', '#F0E442', '#0072B2', '#D55E00', '#CC79A7', '#9A9A9A', '#8E6CEF'];   // colour-blind safe set
  var DASH = ['', '16 7', '4 6', '16 6 3 6', '2 8', '22 6 4 6 4 6', '10 4', '1 5 9 5', '26 9'];
  var CONF = { off: ['bg-off', 'OFFICIAL MAPS BOTH'], nat: ['bg-nat', 'ONE FROM A NATIONAL DATABASE'], wld: ['bg-wld', 'UNOFFICIAL OR WORLD DATA (trusted less)'] };
  var SRCW = { off: 'the agency\'s official boundary (example)', nat: 'a national protected-area database (example)', wld: 'world / unofficial data (example)' };
  function circ(cx, cy, r, n, sq) { var p = []; n = n || 28; for (var i = 0; i < n; i++) { var a = i / n * Math.PI * 2; p.push([Math.round(cx + Math.cos(a) * r * (sq || 1)), Math.round(cy + Math.sin(a) * r)]); } return p; }

  /* ---------- the made-up spots ---------- */
  var S = [
    { id: 'S1', town: 'Pine Hollow (example)', st: 'Example State A', mi: 4, checked: '2026-10-20', maps: 'agency maps dated 2026-03 and 2025-11 (example)',
      parks: [{ ref: 'XX-0001', name: 'Pine Hollow State Forest (example)', ag: 'State Forestry (example)', src: 'off', pts: [[80, 120], [700, 80], [760, 420], [520, 700], [120, 640]] },
        { ref: 'XX-0002', name: 'Cedar Run Wildlife Area (example)', ag: 'State Wildlife Agency (example)', src: 'off', pts: [[480, 300], [1100, 240], [1130, 700], [600, 740], [450, 520]] }],
      roads: [[[0, 770], [400, 760], [800, 775], [1200, 765]], [[620, 770], [640, 640]]], access: [{ name: 'Cedar Run gravel lot (example)', x: 640, y: 640, trail: true }],
      proof: 6, note: 'Hunting season Nov 14-30 (example): wear blaze orange. Gate closed at dark (example).' },
    { id: 'S2', town: 'Twin Creeks (example)', st: 'Example State A', mi: 11, checked: '2026-10-18', maps: 'agency map 2026-01; national database 2025-09 (example)',
      parks: [{ ref: 'XX-0003', name: 'Twin Creeks State Park (example)', ag: 'State Parks (example)', src: 'off', pts: [[100, 100], [640, 100], [640, 700], [100, 700]] },
        { ref: 'XX-0004', name: 'Upper Twin Creek Preserve (example)', ag: 'Land Trust (example)', src: 'nat', pts: [[580, 150], [1100, 150], [1100, 650], [580, 650]] }],
      roads: [[[0, 760], [1200, 740]], [[610, 750], [610, 690]]], access: [{ name: 'Twin Creeks boat ramp lot (example)', x: 610, y: 690, trail: false }], proof: 0 },
    { id: 'S3', town: 'Three Forks (example)', st: 'Example State A', mi: 23, checked: '2026-10-21', maps: 'agency maps 2026-02, 2025-12, 2026-04 (example)',
      parks: [{ ref: 'XX-0005', name: 'Three Forks National Forest (example)', ag: 'Forest agency (example)', src: 'off', pts: circ(470, 360, 300, 28, 1.1) },
        { ref: 'XX-0006', name: 'Fork Ridge Wilderness (example)', ag: 'Forest agency (example)', src: 'off', pts: circ(720, 370, 290, 28, 1.05) },
        { ref: 'XX-0007', name: 'Lower Fork State Natural Area (example)', ag: 'State Nature Preserves (example)', src: 'off', pts: circ(600, 570, 260, 28, 1.2) }],
      roads: [[[0, 790], [600, 780], [1200, 790]], [[600, 785], [595, 720]]], access: [{ name: 'Lower Fork trailhead (example)', x: 595, y: 720, trail: true }], proof: 2 },
    { id: 'S4', town: 'Ridgeback (example)', st: 'Example State B', mi: 38, checked: '2026-10-19', maps: 'trail line 2025-08; agency map 2026-05 (example)',
      parks: [{ ref: 'XX-0008', name: 'Ridgeback National Scenic Trail (example)', ag: 'Trail agency (example)', src: 'off', line: [[40, 600], [300, 520], [520, 430], [760, 380], [1150, 200]] },
        { ref: 'XX-0009', name: 'Ridgeback Wildlife Area (example)', ag: 'State Wildlife Agency (example)', src: 'off', pts: [[350, 150], [900, 120], [950, 650], [380, 700]] }],
      roads: [[[0, 760], [1200, 770]], [[470, 765], [470, 520]]], access: [{ name: 'Ridgeback road crossing (example)', x: 470, y: 520, trail: true }], proof: 3 },
    { id: 'S5', town: 'Blue Lake (example)', st: 'Example State B', mi: 46, checked: '2026-10-15', maps: 'agency maps 2026-02 (example)',
      parks: [{ ref: 'XX-0010', name: 'Blue Lake Recreation Area (example)', ag: 'Corps of Engineers (example)', src: 'off', pts: [[100, 100], [700, 100], [700, 500], [100, 500]] },
        { ref: 'XX-0011', name: 'Blue Lake Waterfowl Refuge (example)', ag: 'Wildlife Refuge agency (example)', src: 'off', pts: [[450, 300], [1100, 300], [1100, 750], [450, 750]] }],
      lake: [[400, 250], [770, 235], [800, 560], [420, 585]], roads: [[[0, 780], [1200, 780]], [[350, 778], [360, 600]]], access: [{ name: 'Blue Lake boat ramp (example)', x: 380, y: 590, trail: false }], proof: 1 },
    { id: 'S6', town: 'Six Corners (example)', st: 'Example State B', mi: 61, checked: '2026-10-22', maps: 'six agency maps 2025-10 to 2026-06 (example)',
      parks: [0, 1, 2, 3, 4, 5].map(function (k) { var a = k / 6 * Math.PI * 2; return { ref: 'XX-00' + (12 + k), name: ['Six Corners State Forest', 'Corners Creek Wildlife Area', 'Old Mill Natural Area', 'Hawk Ridge Wilderness', 'Corners Lake Recreation Area', 'Six Corners Heritage Trail Area'][k] + ' (example)', ag: ['State Forestry', 'State Wildlife Agency', 'Nature Preserves', 'Forest agency', 'Corps of Engineers', 'State Parks'][k] + ' (example)', src: k === 4 ? 'nat' : 'off', pts: circ(600 + Math.cos(a) * 120, 400 + Math.sin(a) * 105, 250, 26, 1.15) }; }),
      roads: [[[0, 785], [1200, 790]], [[600, 790], [600, 600]]], access: [{ name: 'Six Corners trailhead (example)', x: 600, y: 600, trail: true }], proof: 0 },
    { id: 'S7', town: 'Narrow Gap (example)', st: 'Example State A', mi: 17, checked: '2026-10-23', maps: 'agency maps 2026-01 (example)', members: true,
      parks: [{ ref: 'XX-0018', name: 'Narrow Gap State Park (example)', ag: 'State Parks (example)', src: 'off', pts: [[100, 100], [630, 100], [630, 700], [100, 700]] },
        { ref: 'XX-0019', name: 'Gap Run Wildlife Area (example)', ag: 'State Wildlife Agency (example)', src: 'off', pts: [[597, 120], [1100, 120], [1100, 680], [597, 680]] }],
      roads: [[[0, 760], [1200, 760]], [[615, 760], [615, 690]]], access: [{ name: 'Narrow Gap pull-off (example)', x: 615, y: 690, trail: false }], proof: 0 },
    { id: 'S8', town: 'Bald Knob (example)', st: 'Example State B', mi: 74, checked: '2026-10-12', maps: 'agency maps 2025-07 (example)',
      parks: [{ ref: 'XX-0020', name: 'Bald Knob Wilderness (example)', ag: 'Forest agency (example)', src: 'off', pts: circ(480, 400, 330, 26, 1.1) },
        { ref: 'XX-0021', name: 'Knob Fork Wild River corridor (example)', ag: 'Forest agency (example)', src: 'wld', pts: [[560, 0], [760, 0], [740, 800], [540, 800]] }],
      roads: [], access: [], proof: 0 }
  ];
  var MISS = [{ refs: 'XX-0030 + XX-0031', names: 'Hollow Spring Wildlife Area + Hollow Spring Fish Hatchery (examples)', why: 'XX-0031 has no official boundary: only a map pin. Check the official map before you count it.' },
    { refs: 'XX-0032 + XX-0033', names: 'Long Ridge State Forest + Long Ridge Scenic Byway (examples)', why: 'XX-0033 has no official line or corridor yet. Not confirmed.' }];

  /* ---------- geometry ---------- */
  function band(line, w) {   // the 100-ft zone around a line = a polygon (left side + right side back)
    var L = [], R = [];
    for (var i = 0; i < line.length; i++) {
      var p = line[i], a = line[Math.max(0, i - 1)], b = line[Math.min(line.length - 1, i + 1)], dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1, nx = -dy / l, ny = dx / l;
      L.push([p[0] + nx * w, p[1] + ny * w]); R.unshift([p[0] - nx * w, p[1] - ny * w]);
    }
    return L.concat(R);
  }
  function pip(p, poly) { var c = false; for (var i = 0, j = poly.length - 1; i < poly.length; j = i++) { var a = poly[i], b = poly[j]; if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]) + a[0]) c = !c; } return c; }
  function dseg(p, a, b) { var dx = b[0] - a[0], dy = b[1] - a[1], t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy || 1); t = Math.max(0, Math.min(1, t)); return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy); }
  function dedge(p, poly) { var m = 1e9; for (var i = 0, j = poly.length - 1; i < poly.length; j = i++) m = Math.min(m, dseg(p, poly[i], poly[j])); return m; }
  S.forEach(function (s, si) {
    s.parks.forEach(function (k, i) { if (k.line) k.pts = band(k.line, BAND); k.c = COL[i]; k.dash = DASH[i]; k.n = i + 1; k.on = true;
      var cx = 0, cy = 0; k.pts.forEach(function (q) { cx += q[0]; cy += q[1]; }); k.lab = k.line ? k.line[0] : [cx / k.pts.length, cy / k.pts.length]; });
    s.n = s.parks.length;
    /* work it out from the shapes, like the real tool: sample every 4 m */
    var st = 4, all = 0, best = null, bestD = -1, cnt = {}, lakeAll = true, inLake = 0;
    for (var x = 0; x <= 1200; x += st) for (var y = 0; y <= 800; y += st) {
      var p = [x, y], k = 0; s.parks.forEach(function (q) { if (pip(p, q.pts)) k++; });
      if (k >= 2) cnt[k] = (cnt[k] || 0) + 1;
      if (k === s.n) { all++; var d = 1e9; s.parks.forEach(function (q) { d = Math.min(d, dedge(p, q.pts)); }); if (d > bestD) { bestD = d; best = p; }
        if (s.lake) { if (pip(p, s.lake)) inLake++; else lakeAll = false; } }
    }
    s.acres = all * st * st / 4046.86; s.across = 2 * bestD * YD; s.best = best; s.rings = cnt;
    s.water = !!(s.lake && lakeAll && inLake > 0);
    s.tier = s.across >= 100 ? 'big' : s.across >= 50 ? 'small' : s.across >= 25 ? 'tight' : 'none';
    s.conf = s.parks.some(function (q) { return q.src === 'wld'; }) ? 'wld' : s.parks.some(function (q) { return q.src === 'nat'; }) ? 'nat' : 'off';   // the WEAKEST park's
    if (s.access.length && best) { var a = s.access[0], m = 1e9, bp = null;
      for (var x2 = 0; x2 <= 1200; x2 += 8) for (var y2 = 0; y2 <= 800; y2 += 8) { var q2 = [x2, y2]; if (s.parks.every(function (q) { return pip(q2, q.pts); })) { var dd = Math.hypot(q2[0] - a.x, q2[1] - a.y); if (dd < m) { m = dd; bp = q2; } } }
      s.walk = { m: m, to: bp, min: Math.max(1, Math.round(m / 1.34 / 60)) }; }
  });

  /* ---------- page state ---------- */
  var leftUntil = 0, cur = null, step = 0, timer = null, style = 'street', vb = { x: 0, y: 0, w: 1200, h: 800 }, mode = '', meas = [], pin = null, gps = null, walkT = null, lastIn = false;
  var svg = $('ovMap');
  function tag(n, a, kids) { var e = document.createElementNS(NS, n); for (var k in a) e.setAttribute(k, a[k]); (kids || []).forEach(function (c) { e.appendChild(c); }); return e; }
  function path(pts, close) { return 'M' + pts.map(function (p) { return p[0].toFixed(1) + ' ' + p[1].toFixed(1); }).join('L') + (close ? 'Z' : ''); }
  function nfer(n) { return n + '-FER'; }
  function yd(m) { return Math.round(m * YD); }
  function toast(t) { var e = $('ovToast'); e.textContent = t; e.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(function () { e.hidden = true; }, 4200); }

  function setView() { svg.setAttribute('viewBox', vb.x + ' ' + vb.y + ' ' + vb.w + ' ' + vb.h); }
  function draw() {
    var s = cur; if (!s) return; while (svg.firstChild) svg.removeChild(svg.firstChild);
    var defs = tag('defs', {}); svg.appendChild(defs);
    var bg = { street: '#efece4', sat: '#33432b', topo: '#f3eedc' }[style];
    svg.appendChild(tag('rect', { x: -2000, y: -2000, width: 5200, height: 4800, fill: bg }));
    if (style === 'sat') { defs.appendChild(tag('pattern', { id: 'ovSat', width: 40, height: 40, patternUnits: 'userSpaceOnUse' }, [tag('circle', { cx: 8, cy: 9, r: 7, fill: '#2a3823' }), tag('circle', { cx: 28, cy: 26, r: 9, fill: '#3b4d31' }), tag('circle', { cx: 30, cy: 6, r: 4, fill: '#253020' })]));
      svg.appendChild(tag('rect', { x: -2000, y: -2000, width: 5200, height: 4800, fill: 'url(#ovSat)' })); }
    if (style === 'topo') for (var r = 60; r < 900; r += 60) svg.appendChild(tag('ellipse', { cx: 520, cy: 380, rx: r * 1.3, ry: r, fill: 'none', stroke: '#c9a97a', 'stroke-width': r % 300 ? 0.8 : 1.8, 'vector-effect': 'non-scaling-stroke' }));
    if (s.lake) svg.appendChild(tag('path', { d: path(s.lake, true), fill: style === 'sat' ? '#1d3a52' : '#a9cfe8' }));
    s.roads.forEach(function (rd) { if (style !== 'sat') svg.appendChild(tag('path', { d: path(rd), fill: 'none', stroke: style === 'topo' ? '#d0663a' : '#c9c2b0', 'stroke-width': style === 'topo' ? 3 : 14, 'stroke-linecap': 'round' }));
      svg.appendChild(tag('path', { d: path(rd), fill: 'none', stroke: style === 'sat' ? '#bcb6a8' : style === 'topo' ? '#d0663a' : '#ffffff', 'stroke-width': style === 'topo' ? 2 : 10, 'stroke-linecap': 'round' })); });
    var u = vb.w / Math.max(200, svg.clientWidth || 600);   // metres per screen pixel: markers keep their screen size
    var on = s.parks.filter(function (k, i) { return k.on && i < step; });
    /* paler rings: each park's own fill adds up where more of them overlap */
    on.forEach(function (k) { svg.appendChild(tag('path', { d: path(k.pts, true), fill: '#f0c96b', 'fill-opacity': 0.09 })); });
    /* the lit patch = where ALL the parks switched on overlap: one clip inside the next */
    if (on.length >= 2) {
      on.forEach(function (k, i) { defs.appendChild(tag('clipPath', { id: 'ovC' + i }, [tag('path', { d: path(k.pts, true) })])); });
      var g = tag('rect', { x: -2000, y: -2000, width: 5200, height: 4800, fill: '#ffd34d', 'fill-opacity': 0.72, 'data-patch': '1', class: 'ov-patch' });
      for (var i = on.length - 1; i >= 0; i--) g = tag('g', { 'clip-path': 'url(#ovC' + i + ')' }, [g]);
      g.style.cursor = 'pointer'; g.setAttribute('data-patch', '1'); g.style.animation = 'ovGlow 2.4s ease-in-out infinite'; svg.appendChild(g);
    }
    s.parks.forEach(function (k, i) {
      if (!k.on || i >= step) return;
      var newest = i === step - 1 && timer;
      var o = tag('path', { d: path(k.pts, true), fill: 'none', stroke: k.c, 'stroke-width': 4, 'stroke-dasharray': k.dash, 'vector-effect': 'non-scaling-stroke', 'data-park': i, 'stroke-linejoin': 'round' });
      o.style.cursor = 'pointer'; svg.appendChild(o);
      if (newest) { o.style.opacity = 0; requestAnimationFrame(function () { o.style.transition = 'opacity .9s'; o.style.opacity = 1; }); }
      if (k.line) svg.appendChild(tag('path', { d: path(k.line), fill: 'none', stroke: k.c, 'stroke-width': 2, 'stroke-dasharray': '2 3', 'vector-effect': 'non-scaling-stroke', 'pointer-events': 'none' }));
      var b = tag('g', { 'data-park': i }, [tag('circle', { cx: k.lab[0], cy: k.lab[1], r: 12 * u, fill: k.c, stroke: '#fff', 'stroke-width': 2.5 * u }), tag('text', { x: k.lab[0], y: k.lab[1] + 4.6 * u, 'text-anchor': 'middle', 'font-size': 13 * u, 'font-weight': 900, fill: '#111', 'font-family': 'Arial' })]);
      b.lastChild.textContent = k.n; b.style.cursor = 'pointer'; svg.appendChild(b);
    });
    s.access.forEach(function (a) { var g = tag('g', {}, [tag('rect', { x: a.x - 11 * u, y: a.y - 11 * u, width: 22 * u, height: 22 * u, rx: 4 * u, fill: '#1d4d7a', stroke: '#fff', 'stroke-width': 2 * u }), tag('text', { x: a.x, y: a.y + 5.5 * u, 'text-anchor': 'middle', 'font-size': 15 * u, 'font-weight': 900, fill: '#fff', 'font-family': 'Arial' })]); g.lastChild.textContent = 'P'; svg.appendChild(g); });
    if (s.walk && s.walk.to && step >= s.n) svg.appendChild(tag('path', { d: path([[s.access[0].x, s.access[0].y], s.walk.to]), stroke: '#1d4d7a', 'stroke-width': 3, 'stroke-dasharray': '6 5', fill: 'none', 'vector-effect': 'non-scaling-stroke', 'pointer-events': 'none' }));
    if (s.best && step >= s.n) { var st2 = tag('g', { 'pointer-events': 'none' }, [tag('circle', { cx: s.best[0], cy: s.best[1], r: 6 * u, fill: '#7a1d0e', stroke: '#fff', 'stroke-width': 2 * u })]); svg.appendChild(st2); }
    /* scale bar (100 yards) */
    var sx = vb.x + vb.w * 0.04, sy = vb.y + vb.h * 0.94, L = 100 / YD;
    svg.appendChild(tag('path', { d: 'M' + sx + ' ' + sy + 'h' + L, stroke: style === 'sat' ? '#fff' : '#222', 'stroke-width': 3, 'vector-effect': 'non-scaling-stroke' }));
    var tx = tag('text', { x: sx, y: sy - vb.h * 0.015, 'font-size': 12 * u, fill: style === 'sat' ? '#fff' : '#222', 'font-family': 'Arial', 'font-weight': 700 }); tx.textContent = '100 yards'; svg.appendChild(tx);
    if (meas.length) { svg.appendChild(tag('path', { d: path(meas), stroke: '#d55e00', 'stroke-width': 3, fill: 'none', 'vector-effect': 'non-scaling-stroke' }));
      meas.forEach(function (p) { svg.appendChild(tag('circle', { cx: p[0], cy: p[1], r: 5 * u, fill: '#d55e00' })); }); }
    if (pin) svg.appendChild(tag('path', { d: 'M' + pin[0] + ' ' + pin[1] + 'l' + (-9 * u) + ' ' + (-22 * u) + 'a' + (10 * u) + ' ' + (10 * u) + ' 0 1 1 ' + (18 * u) + ' 0z', fill: '#d0312d', stroke: '#fff', 'stroke-width': 2 * u }));
    if (gps) { svg.appendChild(tag('circle', { cx: gps.p[0], cy: gps.p[1], r: gps.acc / YD, fill: 'rgba(30,120,255,.18)', stroke: 'rgba(30,120,255,.7)', 'stroke-width': 2, 'vector-effect': 'non-scaling-stroke' }));
      svg.appendChild(tag('circle', { cx: gps.p[0], cy: gps.p[1], r: 7 * u, fill: '#1e78ff', stroke: '#fff', 'stroke-width': 2.5 * u })); }
  }
  var css = document.createElement('style'); css.textContent = '@keyframes ovGlow{0%,100%{opacity:.85}50%{opacity:1}}'; document.head.appendChild(css);

  /* ---------- the side panels ---------- */
  function badges(s) {
    var t = [];
    t.push('<span class="ov-badge bg-n">' + (s.n === 2 ? 'POSSIBLE 2-FER' : 'POSSIBLE ' + nfer(s.n)) + '</span>');
    if (s.tier === 'small') t.push('<span class="ov-badge bg-small">SMALL OVERLAP: TIGHT FIT, CHECK CAREFULLY</span>');
    if (s.tier === 'tight') t.push('<span class="ov-badge bg-tight">VERY TIGHT: COULD BE MAP ERROR, CHECK BOTH OFFICIAL MAPS ON THE GROUND</span><span class="ov-badge bg-mem">MEMBERS ONLY</span>');
    if (s.water) t.push('<span class="ov-badge bg-water">🚤 WATER ONLY: BOAT OR KAYAK</span>');
    t.push('<span class="ov-badge ' + CONF[s.conf][0] + '">' + CONF[s.conf][1] + '</span>');
    return t.join('');
  }
  function proof(s) { return '<p class="ov-note">🏅 ' + (s.proof ? 'Activated as a 2-fer ' + s.proof + ' times (example)' : 'No 2-fer activations yet (example)') + '. People sometimes log a spot as a 2-fer that isn\'t one: a hint, not proof.</p>'; }
  function rings(s) { if (s.n < 3) return ''; var ks = Object.keys(s.rings).map(Number).sort(function (a, b) { return b - a; });
    return '<p class="ov-note">Where they overlap: ' + ks.map(function (k) { return k + ' of ' + s.n + ': ' + (s.rings[k] * 16 / 4046.86).toFixed(1) + ' acres'; }).join(' · ') + '. The bright patch is where all ' + s.n + ' overlap; paler rings = fewer. Best spot (red dot) = where all ' + s.n + ' meet farthest from every edge.</p>'; }
  function spotPanel() {
    var s = cur; if (!s) return;
    var acc = s.access[0];
    $('ovSpot').innerHTML = '<h2>' + esc(s.town) + '</h2>' + badges(s) +
      '<p style="margin:8px 0 0">' + s.parks.map(function (k) { return '<b>' + esc(k.ref) + '</b> ' + esc(k.name); }).join('<br>') + '</p>' +
      '<p class="ov-note">Size: the spot fits a circle about <b>' + Math.round(s.across) + ' yards</b> across · about <b>' + s.acres.toFixed(1) + ' acres</b>' + (s.parks.some(function (k) { return k.line; }) ? ' (the trail is a line: its 100-ft band is the zone)' : '') + '</p>' + rings(s) +
      (acc && s.walk ? '<p class="ov-note">🅿️ Nearest official access: <b>' + esc(acc.name) + '</b>: about ' + yd(s.walk.m) + ' yards to the patch, ~' + s.walk.min + ' min walk' + (acc.trail ? ', on a trail' : ', <b>no trail</b>: cross-country') + '. <a class="b" style="min-height:30px;padding:3px 10px;font-size:11px" href="#" data-t="dirs">DIRECTIONS</a></p>'
        : '<p class="ov-note">🅿️ <b>No public road or parking found within about a mile.</b> Plan your walk on the official map.</p>') +
      (s.note ? '<p class="ov-note">🚧 ' + esc(s.note) + '</p>' : '') + proof(s) +
      '<p class="ov-note">Last checked ' + s.checked + ' · ' + esc(s.maps) + '</p><p class="ov-note">One log per park (POTA): upload a log for each park number.</p>' +
      '<span class="ov-short">' + SHORT + '</span>';
    $('ovLeg').innerHTML = s.parks.map(function (k, i) {
      return '<li><span class="ov-num" style="background:' + k.c + '">' + k.n + '</span><svg width="34" height="10" aria-hidden="true"><path d="M2 5h30" stroke="' + k.c + '" stroke-width="4" stroke-dasharray="' + (k.dash || '') + '"/></svg>' +
        '<label><input type="checkbox" data-on="' + i + '"' + (k.on ? ' checked' : '') + '> <b>' + esc(k.ref) + '</b> ' + esc(k.name) + (k.line ? ' <i>(line: 100-ft band)</i>' : '') + '</label></li>';
    }).join('');
  }
  function legOn(i, v) { cur.parks[i].on = v; draw(); }

  /* ---------- GPS / pin status card ---------- */
  function status(p, acc, isPin) {
    var s = cur, ins = s.parks.map(function (k) { return pip(p, k.pts); }), k = ins.filter(Boolean).length, n = s.n, g = $('ovGps'), cls = 'out', t = '', body = '';
    var dIn = 1e9, dOut = 1e9;
    s.parks.forEach(function (q, i) { var d = dedge(p, q.pts); if (ins[i]) dIn = Math.min(dIn, d); else dOut = Math.min(dOut, d); });
    var edge = k === n ? dIn : dOut, accM = acc / YD, who = isPin ? 'the pin' : 'you';
    if (k === n) {
      if (accM > edge) { cls = 'edge'; t = '⚠️ TOO CLOSE TO THE EDGE TO TELL'; body = 'GPS is good to about ±' + Math.round(acc) + ' yards and the edge is ' + yd(edge) + ' yards away. Step farther in; we never guess.'; }
      else { cls = 'in'; t = '✅ By our maps ' + who + (isPin ? ' looks' : ' look') + ' inside ' + (n === 2 ? 'both outlines' : 'all ' + n + ' outlines');
        body = 'About ' + yd(edge) + ' yards to the nearest edge. Spot ' + Math.round(s.across) + ' yards across, ' + s.acres.toFixed(1) + ' acres · ' + CONF[s.conf][1].toLowerCase() + ' · last checked ' + s.checked + '.' + (s.water ? ' 🚤 Water only: by boat or kayak.' : '') +
          '<br><b>Keep your whole station inside the lit patch: radio, antenna, operator.</b> POTA decides, not KPC.'; }
      lastIn = !isPin; leftUntil = 0;
    } else {
      if (!isPin && Date.now() < leftUntil) { cls = 'left'; t = '🚨 You left the overlap'; body = 'By our maps you are outside ' + (n - k) + ' of the outlines now. Step back into the lit patch.'; }
      else if (lastIn && !isPin) { leftUntil = Date.now() + 3500; cls = 'left'; t = '🚨 You left the overlap'; body = 'By our maps you are now outside ' + (n - k) + ' of the outlines. Step back into the lit patch.'; try { navigator.vibrate && navigator.vibrate([200, 100, 200]); } catch (e) {} lastIn = false; }
      else if (k > 0 && accM > edge) { cls = 'edge'; t = '⚠️ TOO CLOSE TO THE EDGE TO TELL'; body = 'GPS ±' + Math.round(acc) + ' yards, the next outline is ' + yd(edge) + ' yards away.'; }
      else if (k === 0) { t = '📍 Outside ' + (n === 2 ? 'both outlines' : 'all ' + n + ' outlines'); body = 'About ' + yd(dOut) + ' yards to the nearest park line.' + (s.access[0] ? ' Nearest official access: ' + esc(s.access[0].name) + '.' : ''); }
      else { cls = 'one'; var inN = s.parks.filter(function (q, i) { return ins[i]; }), outN = s.parks.filter(function (q, i) { return !ins[i]; });
        var bp = s.best, brg = bp ? Math.round((Math.atan2(bp[0] - p[0], -(bp[1] - p[1])) * 180 / Math.PI + 360) % 360) : null, dir = brg == null ? '' : ['north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west', 'north-west'][Math.round(brg / 45) % 8];
        t = n === 2 ? '🟡 By our maps ' + who + (isPin ? ' looks' : ' look') + ' inside: ' + esc(inN[0].ref) : '🟡 By our maps ' + who + (isPin ? ' looks' : ' look') + ' inside ' + k + ' of ' + n + ' outlines';
        body = (n === 2 ? 'About ' + yd(dOut) + ' yards to ' + esc(outN[0].ref) + '.' : 'Missing: ' + outN.map(function (q) { return esc(q.ref); }).join(', ') + '.') + (dir ? ' The full patch is ' + dir + ', about ' + yd(Math.hypot(bp[0] - p[0], bp[1] - p[1])) + ' yards.' : ''); }
    }
    g.className = 'ov-gps ' + cls; g.innerHTML = '<b class="st">' + t + '</b><span>' + body + '</span><span class="ov-short">' + SHORT + '</span>' + (isPin ? '' : '<p class="ov-note">Simulated GPS · ±' + Math.round(acc) + ' yards</p>');
  }
  function walk() {
    var s = cur; stopWalk(); if (!s.best) return;
    var a = s.access[0] ? [s.access[0].x, s.access[0].y] : [60, 760], b = s.best, ex = [b[0] + (b[0] - a[0]) * 1.4, b[1] + (b[1] - a[1]) * 1.4], N = 60, i = 0; lastIn = false; pin = null;
    walkT = setInterval(function () {
      var f = i / N, p = f <= 1 ? [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f] : [b[0] + (ex[0] - b[0]) * (f - 1), b[1] + (ex[1] - b[1]) * (f - 1)];
      var acc = f < 0.3 ? 30 - f * 40 : f < 0.62 ? 26 : f < 1.0 ? 7 : 9;   // a weak fix near the edge shows 'too close to tell'
      gps = { p: p, acc: acc }; draw(); status(p, acc, false);
      if (++i > N * 1.7) { stopWalk(); toast('Walk-in finished. Tap 🚶 again to replay it.'); }
    }, 220);
    $('ovGps').scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }
  function stopWalk() { if (walkT) clearInterval(walkT); walkT = null; }

  /* ---------- open a spot (animate the parks in) ---------- */
  function open(id, instant) {
    var s = S.filter(function (x) { return x.id === id; })[0] || S[0]; cur = s; stopWalk(); gps = null; pin = null; meas = []; mode = ''; lastIn = false;
    s.parks.forEach(function (k) { k.on = true; }); vb = { x: -60, y: -40, w: 1320, h: 880 }; setView(); spotPanel(); $('ovPop').hidden = true;
    $('ovGps').className = 'ov-gps out'; $('ovGps').innerHTML = '<b class="st">📍 GPS walk-in</b><span>Tap 🚶 SIMULATE A GPS WALK-IN to see how the card changes as you walk in, or 📌 DROP A PIN and tap the map.</span>';
    tools(); clearTimeout(timer); timer = null;
    if (instant) { step = s.n; draw(); return; }
    step = 1; draw();
    (function next() { timer = setTimeout(function () { step++; draw(); if (step < s.n) next(); else { timer = null; setTimeout(function () { vb = zoomTo(s); setView(); draw(); }, 600); } }, 1500); })();
    try { history.replaceState(null, '', '#s=' + s.id); } catch (e) {}
  }
  function zoomTo(s) { var xs = [], ys = []; s.parks.forEach(function (k) { k.pts.forEach(function (p) { xs.push(p[0]); ys.push(p[1]); }); });
    var x0 = Math.min.apply(0, xs), x1 = Math.max.apply(0, xs), y0 = Math.min.apply(0, ys), y1 = Math.max.apply(0, ys), w = (x1 - x0) * 1.08, h = (y1 - y0) * 1.08;
    var r = svg.clientWidth / Math.max(1, svg.clientHeight); if (w / h < r) w = h * r; else h = w / r; return { x: (x0 + x1) / 2 - w / 2, y: (y0 + y1) / 2 - h / 2, w: w, h: h }; }
  function tools() { [].forEach.call(document.querySelectorAll('#ovTools [data-t]'), function (b) { var t = b.dataset.t; if (/^(street|sat|topo)$/.test(t)) b.classList.toggle('on', t === style); if (t === 'pin' || t === 'measure') b.classList.toggle('on', mode === t); if (t === 'walk') b.classList.toggle('on', !!walkT); }); }
  function pt(e) { var p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY; var q = p.matrixTransform(svg.getScreenCTM().inverse()); return [q.x, q.y]; }
  function pop(html) { var e = $('ovPop'); e.innerHTML = '<button type="button" class="x" data-x>✕</button>' + html; e.hidden = false; }

  /* ---------- map events: drag to pan, tap outline / patch / pin / measure ---------- */
  var drag = null, moved = false;
  svg.addEventListener('pointerdown', function (e) { drag = { x: e.clientX, y: e.clientY, vb: Object.assign({}, vb) }; moved = false; });
  svg.addEventListener('pointermove', function (e) { if (!drag) return; var dx = e.clientX - drag.x, dy = e.clientY - drag.y; if (Math.abs(dx) + Math.abs(dy) > 6) moved = true; if (!moved) return;
    var k = vb.w / svg.clientWidth; vb.x = drag.vb.x - dx * k; vb.y = drag.vb.y - dy * k; setView(); });
  addEventListener('pointerup', function (e) {
    if (!drag) return; var wasMoved = moved; drag = null; if (wasMoved || !e.target.closest || !e.target.closest('#ovMap')) return;
    var p = pt(e), s = cur;
    if (mode === 'pin') { pin = p; stopWalk(); gps = null; draw(); status(p, 0, true); return; }
    if (mode === 'measure') { if (meas.length >= 2) meas = []; meas.push(p); draw(); if (meas.length === 2) { var d = Math.hypot(meas[1][0] - meas[0][0], meas[1][1] - meas[0][1]); pop('<b>📏 ' + yd(d) + ' yards</b> (' + Math.round(d * FT) + ' ft, ' + Math.round(d) + ' m) in a straight line. Tap twice more to measure again.'); } return; }
    var pk = e.target.closest('[data-park]'), pa = e.target.closest('[data-patch]');
    if (pa && !pk) { pop('<b>' + (s.n === 2 ? 'Possible 2-fer' : 'Possible ' + s.n + '-fer') + ' patch</b><br>Fits a circle about <b>' + Math.round(s.across) + ' yards</b> across · <b>' + s.acres.toFixed(1) + ' acres</b><br>Confidence: ' + CONF[s.conf][1].toLowerCase() + '<br>Last checked ' + s.checked + ' · ' + esc(s.maps) + '<span class="ov-short">' + SHORT + '</span>'); return; }
    if (pk) { var k = s.parks[+pk.getAttribute('data-park')]; pop('<span class="ov-num" style="background:' + k.c + ';display:inline-grid;width:22px;height:22px;border-radius:50%;place-items:center;font-weight:900">' + k.n + '</span> <b>' + esc(k.ref) + ' · ' + esc(k.name) + '</b><br>Managed by ' + esc(k.ag) + '<br>Outline from ' + SRCW[k.src] + (k.line ? '<br>A trail that is only a line: the light band = POTA\'s 100 ft from it.' : '') +
      '<br><a href="#" data-fake>Official map (example)</a> · <a href="#" data-fake>POTA page (example)</a><span class="ov-short">' + SHORT + '</span>'); return; }
    $('ovPop').hidden = true;
  });
  svg.addEventListener('wheel', function (e) { e.preventDefault(); zoom(e.deltaY < 0 ? 0.85 : 1.18, pt(e)); }, { passive: false });
  function zoom(f, c) { c = c || [vb.x + vb.w / 2, vb.y + vb.h / 2]; vb = { x: c[0] - (c[0] - vb.x) * f, y: c[1] - (c[1] - vb.y) * f, w: vb.w * f, h: vb.h * f }; setView(); draw(); }

  document.addEventListener('click', function (e) {
    var b = e.target.closest('#ov [data-t], #ov [data-x], #ov [data-fake], #ov [data-on], #ovAllOn, #ovAllOff, #ov [data-tab], #ov [data-open], #ov [data-f], #ov [data-send]');
    if (!b) return;
    if (b.matches('[data-on]')) { legOn(+b.dataset.on, b.checked); return; }
    e.preventDefault();
    if (b.matches('[data-x]')) { $('ovPop').hidden = true; return; }
    if (b.matches('[data-fake]')) { toast('In the real tool this opens the agency\'s official map or the POTA park page.'); return; }
    if (b.id === 'ovAllOn' || b.id === 'ovAllOff') { cur.parks.forEach(function (k) { k.on = b.id === 'ovAllOn'; }); spotPanel(); draw(); return; }
    if (b.matches('[data-tab]')) { var m = b.dataset.tab === 'map'; $('ovMapTab').hidden = !m; $('ovListTab').hidden = m; [].forEach.call(document.querySelectorAll('#ov [data-tab]'), function (x) { x.classList.toggle('on', x === b); x.setAttribute('aria-selected', String(x === b)); }); if (m) { vb = zoomTo(cur); setView(); draw(); } else list(); return; }
    if (b.matches('[data-open]')) { $('ov').querySelector('[data-tab=map]').click(); open(b.dataset.open); window.scrollTo({ top: $('ovMapW').getBoundingClientRect().top + scrollY - 90, behavior: 'smooth' }); return; }
    if (b.matches('[data-f]')) { var f = b.dataset.f; if (f === 'near') { F.near = !F.near; b.classList.toggle('on', F.near); } else { F[f] = !F[f]; b.setAttribute('aria-pressed', String(F[f])); } list(); return; }
    if (b.matches('[data-send]')) { $('ovPop').hidden = true; toast('Preview: nothing was sent. In the real tool your report goes to the KPC staff room, is read weekly, and fixes show in a short "recent corrections" list.'); return; }
    var t = b.dataset.t;
    if (t === 'replay') open(cur.id); else if (t === 'all') { clearTimeout(timer); timer = null; step = cur.n; vb = zoomTo(cur); setView(); draw(); }
    else if (/^(street|sat|topo)$/.test(t)) { style = t; draw(); }
    else if (t === 'zin') zoom(0.75); else if (t === 'zout') zoom(1.33);
    else if (t === 'pin' || t === 'measure') { mode = mode === t ? '' : t; meas = []; draw(); toast(mode === 'pin' ? 'Tap the map to drop a pin.' : mode === 'measure' ? 'Tap two places on the map.' : 'Done.'); }
    else if (t === 'walk') { if (walkT) { stopWalk(); } else walk(); }
    else if (t === 'sv') toast('In the real tool: Google Street View opens at the spot (made-up map here).');
    else if (t === 'share') { var u = location.origin + location.pathname + '#s=' + cur.id; try { navigator.clipboard.writeText(u); } catch (x) {} toast('Link copied: ' + u); }
    else if (t === 'gpx') toast('In the real tool: download the spot as GPX or KML for your GPS. The made-up spots have no real coordinates.');
    else if (t === 'dirs') toast('In the real tool: driving directions to the official access point open in your maps app.');
    else if (t === 'save') { var until = new Date(Date.now() + 30 * 864e5); try { localStorage.setItem('kpcOvPreviewSave', JSON.stringify({ id: cur.id, until: until.toISOString() })); } catch (x) {} toast('Saved for offline until ' + until.toDateString() + '. It refreshes when you are back online and expires after 30 days, so old boundaries are never used.'); }
    else if (t === 'report') pop('<b>⚑ Report a mistake: ' + esc(cur.town) + '</b><br>What looks wrong? (wrong line, closed gate, private land, the spot is under water…)<textarea aria-label="What looks wrong"></textarea><button type="button" class="b" data-send style="margin-top:6px;color:#5a3a00;border-color:#b08a3a">SEND (PREVIEW: NOTHING IS SENT)</button>');
    tools();
  });

  /* ---------- the LIST tab ---------- */
  var F = { near: false, big: true, small: true, tight: true, water: true, multi: false, off: false };
  function list() {
    var q = ($('ovQ').value || '').trim().toLowerCase();
    var L = S.filter(function (s) {
      if (q && (s.town + ' ' + s.parks.map(function (k) { return k.ref + ' ' + k.name; }).join(' ')).toLowerCase().indexOf(q) < 0) return false;
      if (s.water) return F.water; if (!F[s.tier]) return false; if (F.multi && s.n < 3) return false; if (F.off && s.conf !== 'off') return false; return true;
    });
    L.sort(F.near ? function (a, b) { return a.mi - b.mi; } : function (a, b) { return (a.st < b.st ? -1 : a.st > b.st ? 1 : 0) || b.n - a.n || b.across - a.across; });
    var html = '', lastSt = '';
    if (F.near) html += '<p class="ov-note">📍 Sorted by distance from a pretend location (preview).</p>';
    L.forEach(function (s) {
      if (!F.near && s.st !== lastSt) { html += '<p class="ov-st">' + esc(s.st.toUpperCase()) + '</p>'; lastSt = s.st; }
      html += '<div class="ov-row' + (cur && cur.id === s.id ? ' sel' : '') + '" data-open="' + s.id + '"><b class="t">' + (s.n === 2 ? '2-fer' : s.n + '-fer') + ' · ' + s.parks.map(function (k) { return esc(k.ref); }).join(', ') + '</b>' +
        '<span class="m">' + esc(s.town) + (F.near ? ' · ' + s.mi + ' mi (pretend)' : '') + ' · ' + Math.round(s.across) + ' yards across · ' + s.acres.toFixed(1) + ' acres</span><br>' + badges(s) + '<span class="ov-short">' + SHORT + '</span></div>';
    });
    $('ovList').innerHTML = html || '<p class="ov-note">Nothing matches. Try another search or turn a filter back on.</p>';
    $('ovMiss').innerHTML = MISS.map(function (m) { return '<div class="ov-row" style="cursor:default"><b class="t">' + esc(m.refs) + '</b><span class="m">' + esc(m.names) + '</span><br><span class="ov-badge bg-mem">MEMBERS FIRST</span><span class="ov-badge bg-wld">MISSING BOUNDARY: CHECK THE OFFICIAL MAP</span><p class="ov-note">' + esc(m.why) + '</p></div>'; }).join('');
  }
  $('ovQ').addEventListener('input', function () { if ($('ovListTab').hidden) $('ov').querySelector('[data-tab=list]').click(); else list(); });

  var h = /#s=(S\d)/.exec(location.hash);
  open(h ? h[1] : 'S1');
  addEventListener('resize', function () { if (!timer) { vb = zoomTo(cur); setView(); draw(); } });
  window.KPCOverlapPreview = { S: S, open: open, status: status };
})();
