/* KPC Kentucky POTA Field Resource — kpc-guide-pota.html  (?order=num or ?order=az)
   Park codes, names, counties, types, coordinates, KFF and SOTA lists come live from kpc-ky-data.json `parks`.
   The card details from the original PDFs (buttons and links, access points, utilities, notes, map region, short names,
   Wild Rivers) and the 2-fer / 3-fer data (synced from .claude/build/fers/fers.json, the single source) are in
   kpc-guide-pota-data.json, built by .claude/build/guides/extract_pota.py. SOTA within 3 mi and Nearby are worked out here.
   "2-FER" is only ever used for POTA + POTA; KFF and SOTA references are shown under ALSO.
   When everything has rendered, <html data-ready="1"> is set for the PDF printer. */
(function () {
  'use strict';
  var REG = [
    ['Bluegrass', 'Bluegrass Region', 'BLUEGRASS'],
    ['Northern Kentucky', 'Northern Kentucky Region', 'NORTHERN'],
    ['Eastern Kentucky', 'Eastern Kentucky (Appalachian / Eastern Coal Field)', 'EASTERN'],
    ['South Central Pennyroyal', 'South Central / Pennyroyal Region', 'S. CENTRAL'],
    ['Western Kentucky', 'Western Kentucky (Western Coal Field)', 'WESTERN'],
    ['Jackson Purchase', 'Jackson Purchase Region', 'PURCHASE']
  ];
  var MAJOR = ['Ashland', 'Covington', 'Frankfort', 'Hopkinsville', 'Louisville', 'Newport', 'Owensboro', 'Paducah',
    'Radcliff', 'Richmond', 'Lexington', 'Bowling Green', 'Jeffersontown'];
  var root = document.documentElement;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function $(id) { return document.getElementById(id); }
  function mi(a, b, c, d) {
    var p = Math.PI / 180, x = Math.pow(Math.sin((c - a) * p / 2), 2) +
      Math.cos(a * p) * Math.cos(c * p) * Math.pow(Math.sin((d - b) * p / 2), 2);
    return 2 * 3958.8 * Math.asin(Math.sqrt(x));
  }
  function f1(d) { return d.toFixed(1); }
  function fN(d) { return d < 10 ? d.toFixed(1) : String(Math.round(d)); }
  function num(n) { return Number(n).toLocaleString('en-US'); }
  function sid(c) { return 's-' + c.replace(/\//g, '-'); }
  function nid(c) { return 'n-' + c.replace(/\//g, '-'); }
  function sotlas(c) { return 'https://sotl.as/summits/' + c; }
  function refUrl(c) { return /^US-/.test(c) ? 'https://next.pota.app/park/' + c : 'https://logsearch.wwff.co/directory/' + c; }
  function ext(href, text, cls) {
    return '<a' + (cls ? ' class="' + cls + '"' : '') + ' href="' + esc(href) + '" target="_blank" rel="noopener">' + text + '</a>';
  }
  function gps(la, lo) { return 'https://www.google.com/maps/search/?api=1&query=' + la + ',' + lo; }
  function osm(la, lo) { return 'https://www.openstreetmap.org/?mlat=' + la + '&mlon=' + lo + '#map=13/' + la + '/' + lo; }
  function wx(la, lo) { return 'https://weather.com/weather/today/l/' + la + ',' + lo; }

  /* ---------- county polygons (kpc-ky-counties-hd.json, US Census 500k simplified: [{n, r:[ring of [lon,lat]]}]) ---------- */
  function pip(x, y, ring) {
    var ins = false;
    for (var i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      var xi = ring[i][0], yi = ring[i][1], xj = ring[j][0], yj = ring[j][1];
      if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) ins = !ins;
    }
    return ins;
  }
  function countyAt(C, la, lo) {
    for (var i = 0; i < C.length; i++) for (var k = 0; k < C[i].r.length; k++) if (pip(lo, la, C[i].r[k])) return C[i].n;
    var best = null, bd = 1e9;
    C.forEach(function (c) {
      c.r.forEach(function (ring) {
        ring.forEach(function (p) { var d = Math.pow(p[0] - lo, 2) + Math.pow(p[1] - la, 2); if (d < bd) { bd = d; best = c.n; } });
      });
    });
    return best;
  }

  /* ---------- regional map (SVG) ---------- */
  function regionMap(regionKey, D, C, pins, opts) {
    opts = opts || {};
    var inReg = C.filter(function (c) { return regionKey ? D.regions[c.n.toUpperCase()] === regionKey : true; });
    var x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    if (opts.bbox) { x0 = opts.bbox[0]; y0 = opts.bbox[1]; x1 = opts.bbox[2]; y1 = opts.bbox[3]; }
    else inReg.forEach(function (c) { c.r.forEach(function (ring) { ring.forEach(function (p) {
      if (p[0] < x0) x0 = p[0]; if (p[0] > x1) x1 = p[0]; if (p[1] < y0) y0 = p[1]; if (p[1] > y1) y1 = p[1];
    }); }); });
    var padX = (x1 - x0) * 0.06, padY = (y1 - y0) * 0.06;
    x0 -= padX; x1 += padX; y0 -= padY; y1 += padY;
    var kx = Math.cos((y0 + y1) / 2 * Math.PI / 180), W = 1000, sc = W / ((x1 - x0) * kx), H = Math.round((y1 - y0) * sc);
    function px(lo) { return ((lo - x0) * kx * sc).toFixed(1); }
    function py(la) { return ((y1 - la) * sc).toFixed(1); }
    function path(c) {
      return c.r.map(function (ring) { return 'M' + ring.map(function (p) { return px(p[0]) + ' ' + py(p[1]); }).join('L') + 'Z'; }).join('');
    }
    function near(c) {
      return c.r.some(function (ring) { return ring.some(function (p) { return p[0] > x0 - .3 && p[0] < x1 + .3 && p[1] > y0 - .3 && p[1] < y1 + .3; }); });
    }
    function centroid(c) {
      var ring = c.r.slice().sort(function (a, b) { return b.length - a.length; })[0], A = 0, cx = 0, cy = 0;
      for (var i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        var f = ring[j][0] * ring[i][1] - ring[i][0] * ring[j][1];
        A += f; cx += (ring[j][0] + ring[i][0]) * f; cy += (ring[j][1] + ring[i][1]) * f;
      }
      return A ? [cx / (3 * A), cy / (3 * A)] : ring[0];
    }
    var s = ['<svg class="g-map" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + esc(regionKey) + ' map">',
      '<rect width="' + W + '" height="' + H + '" fill="#dbe6ee"/>'];
    C.filter(near).forEach(function (c) {
      var r = regionKey ? D.regions[c.n.toUpperCase()] === regionKey : true;
      s.push('<path d="' + path(c) + '" fill="' + (r ? '#ffffff' : '#ece4d1') + '" stroke="' + (r ? '#9db8a6' : '#d9cfb6') + '" stroke-width="' + (r ? 1 : .6) + '" stroke-linejoin="round"/>');
    });
    inReg.filter(near).forEach(function (c) {
      var p = centroid(c);
      s.push('<text x="' + px(p[0]) + '" y="' + py(p[1]) + '" class="m-co">' + esc(c.n) + '</text>');
    });
    (D.towns || []).forEach(function (t) {
      var cn = null;
      for (var i = 0; i < inReg.length && !cn; i++) for (var k = 0; k < inReg[i].r.length; k++) if (pip(t.lo, t.la, inReg[i].r[k])) { cn = inReg[i].n; break; }
      if (!cn) return;
      var big = MAJOR.indexOf(t.n) >= 0;
      s.push('<circle cx="' + px(t.lo) + '" cy="' + py(t.la) + '" r="' + (big ? 4 : 2.4) + '" fill="#161616"/>' +
        '<text x="' + (+px(t.lo) + (big ? 6 : 5)) + '" y="' + (+py(t.la) + 3.5) + '" class="m-t' + (big ? ' big' : '') + '">' + esc(t.n) + '</text>');
    });
    if (opts.extra) s.push(opts.extra(px, py));
    pins.forEach(function (p) {
      s.push('<a href="#' + p.id + '"><title>' + esc(p.title) + '</title><circle cx="' + px(p.lo) + '" cy="' + py(p.la) + '" r="5.5" fill="' + p.color +
        '" stroke="#fff" stroke-width="1.6"/><text x="' + (+px(p.lo) + 8) + '" y="' + (+py(p.la) - 5) + '" class="m-p">' + esc(p.label) + '</text></a>');
    });
    s.push('</svg>');
    return s.join('');
  }
  var CAT = [['State Park', '#e2a52a'], ['WMA', '#1d5a3a'], ['Nature Preserve', '#8cc084'], ['Federal', '#2f5f8f'],
    ['State Forest', '#8a5a2b'], ['Historic / Trail / Other', '#b4442c']];
  var SHORT = [['National Wild and Scenic River', 'WSR'], ['National Forest Wildlife Management Area', 'NF WMA'],
    ['Campground Wildlife Management Area', 'CG WMA'], ['Wildlife Management Area', 'WMA'], ['State Nature Preserve', 'SNP'],
    ['State Historic Site', 'SHS'], ['State Natural Area', 'SNA'], ['State Park', 'SP'], ['State Forest', 'SF'],
    ['National Wildlife Refuge', 'NWR'], ['National Recreation Area', 'NRA'], ['National Historical Park', 'NHP'],
    ['National Historic Trail', 'NHT'], ['National Fish Hatchery', 'NFH'], ['National Battlefield', 'NB'], ['National Monument', 'NM'],
    ['National Park', 'NP'], ['National Forest', 'NF'], ['Wilderness Area', 'WA'], ['Recreation Area', 'RA']];
  var BTNCLS = { 'OFFICIAL MAP': 'b-map', 'AREA MAP': 'b-map', 'BROCHURE': 'b-map', 'GPS': 'b-gps', 'OSM BOUNDARY': 'b-osm',
    'WEBSITE': 'b-web', 'POTA MAP': 'b-web', 'WILD RIVER MAP': 'b-osm', 'ENTRANCE': 'b-gps', 'WEATHER': 'b-wx', 'NEARBY ›': 'b-near',
    'CAMPING ›': 'b-gold', 'RESORT ›': 'b-gold', 'CABINS ›': 'b-gold', 'NPS LEWIS & CLARK': 'b-near' };
  var LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
  function pid(c) { return 's-' + c; }
  function pnid(c) { return 'n-' + c; }
  function pota(c) { return 'https://next.pota.app/park/' + c; }
  function catOf(t) {
    t = String(t || '');
    if (t === 'State Park') return 0;
    if (t === 'WMA') return 1;
    if (/Nature Preserve|Natural Area/.test(t)) return 2;
    if (/^National|River \/ Wilderness|Fish Hatchery/.test(t)) return 3;
    if (t === 'State Forest') return 4;
    return 5;
  }
  function shortName(n) {
    for (var i = 0; i < SHORT.length; i++) {
      var k = SHORT[i][0];
      if (n.slice(-k.length) === k) return n.slice(0, n.length - k.length) + SHORT[i][1];
    }
    return n;
  }
  function inKY(p) { return p.la > 36.45 && p.la < 39.2 && p.lo > -89.6 && p.lo < -81.9; }
  function shortSota(n) { return String(n).replace(/^Unnamed summit \((.+)\)$/, 'Unnamed $1'); }

  var STATE = {};

  function setup(D, G, C, WR) {
    var X = G.parks || {};
    var P = D.parks.slice();
    var byC = {};
    P.forEach(function (p) {
      byC[p.c] = p;
      var x = X[p.c];
      p._x = x || null;
      p._short = (x && x.short) || shortName(p.n);
      if (x && x.mapRegion) p._reg = x.mapRegion;
      else if (!inKY(p)) p._reg = null;           // e.g. a national trail whose reference point is out of state
      else {
        var r = D.regions[String(p.co).split('/')[0].trim().toUpperCase()];
        p._reg = r || D.regions[String(countyAt(C, p.la, p.lo)).toUpperCase()] || null;
      }
    });
    STATE = { D: D, G: G, C: C, WR: WR, P: P, byC: byC };
  }

  /* ---------- 2-fers (fers.json via kpc-guide-pota-data.json) ---------- */
  function fersFor(ref) {
    var F = STATE.G.fers;
    return F.spots.filter(function (d) { return d.refs.indexOf(ref) >= 0; });
  }
  function fersNames() {
    var m = {};
    STATE.G.fers.spots.forEach(function (d) { d.refs.forEach(function (r, i) { m[r] = d.names[i]; }); });
    return m;
  }
  function twoferLine(ref, hadLine) {
    var items = fersFor(ref), NAMES = fersNames();
    if (!items.length) {
      if (!hadLine) return '';
      return '<p class="g-line"><b>2-FER</b> None confirmed in the KPC <a href="#fers">2-Fers &amp; 3-Fers Index</a>. Earlier listed pairs here could not be confirmed from map data; do your own research.</p>';
    }
    var three = items.some(function (d) { return d.type === '3-fer'; });
    var parts = items.map(function (d) {
      var others = d.refs.filter(function (r) { return r !== ref; });
      return (d.type === '3-fer' ? '3-fer with ' : '') + others.map(function (r) {
        return ext(pota(r), esc(r), 'g-ref') + ' ' + esc(NAMES[r] || (STATE.byC[r] ? STATE.byC[r].n : ''));
      }).join(' + ') + esc(d.tag || '');
    });
    return '<p class="g-line g-2fer"><b>' + (three ? '3-FER / 2-FER' : '2-FER') + '</b> ' + parts.join(' • ') +
      ' — GPS points for it are in the <a href="#fers">2-Fers &amp; 3-Fers Index</a> (not exact: they only get you to the area); do your own research.</p>';
  }

  function alsoLine(p) {
    var x = p._x || {}, D = STATE.D, parts = [];
    var note = (x.notes || []).filter(function (n) { return n.k === 'ALSO'; })[0] || {};
    var custom = {};
    (note.links || []).forEach(function (l) { custom[l.label] = l.url; });
    var kff = p.kff || [];
    if (kff.length) parts.push('WWFF: ' + kff.map(function (k) { return ext(custom[k] || 'https://logsearch.wwff.co/directory/' + k, esc(k)); }).join(', '));
    var sota = {};
    D.summits.forEach(function (s) { sota[s.c] = s; });
    var inside = x.sotaInside || [];
    if (inside.length) parts.push('SOTA inside (KY GIS): ' + inside.map(function (c) { return ext(sotlas(c), esc(c)) + ' ' + esc(shortSota(sota[c] ? sota[c].n : '')); }).join(' • '));
    var near = D.summits.map(function (s) { return { s: s, d: mi(p.la, p.lo, s.la, s.lo) }; })
      .filter(function (o) { return o.d <= 3.0 && inside.indexOf(o.s.c) < 0; }).sort(function (a, b) { return a.d - b.d; });
    if (near.length) parts.push('SOTA within 3 mi: ' + near.map(function (o) { return ext(sotlas(o.s.c), esc(o.s.c)) + ' ' + esc(shortSota(o.s.n)) + ' ' + f1(o.d) + ' mi'; }).join(' • '));
    p._q = kff.concat(inside, near.map(function (o) { return o.s.c; })).join(' ');
    return parts.length ? '<p class="g-line"><b>ALSO</b> ' + parts.join(' | ') + '</p>' : '';
  }

  function linkify(t, links) {
    var h = esc(t);
    (links || []).forEach(function (l) {
      var e = esc(l.label);
      if (l.label && h.indexOf(e) >= 0) h = h.replace(e, ext(l.url, e));
    });
    return h;
  }

  function card(p) {
    var x = p._x;
    var btns = x ? x.btns : [['OFFICIAL MAP', p.off], ['GPS', null], ['OSM BOUNDARY', null], ['WEBSITE', p.web], ['WEATHER', null], ['NEARBY ›', null], ['CAMPING ›', p.camp]]
      .filter(function (b) { return b[1] !== undefined && (b[1] || ['GPS', 'OSM BOUNDARY', 'WEATHER', 'NEARBY ›'].indexOf(b[0]) >= 0); });
    var bh = btns.map(function (b) {
      var lab = b[0], cls = 'b ' + (BTNCLS[lab] || 'b-gps');
      if (lab === 'GPS') return ext(gps(p.la, p.lo), 'GPS', cls);
      if (lab === 'OSM BOUNDARY') return ext(osm(p.la, p.lo), 'OSM BOUNDARY', cls);
      if (lab === 'WEATHER') return ext(wx(p.la, p.lo), 'WEATHER', cls);
      if (lab === 'NEARBY ›') return '<a class="' + cls + '" href="#' + pnid(p.c) + '">NEARBY ›</a><a class="b b-near no-print" href="kpc-park-notes.html#' + p.c + '">PARK TIPS ›</a>';
      return ext(b[1], esc(lab), cls);
    }).join('');
    var co = String(p.co || '');
    var coLabel = co === 'See official site' ? 'County: see official site' : co === 'Multiple' ? 'Multiple counties' : co + (co.indexOf('/') >= 0 ? ' Counties' : ' County');
    var type = (x && x.type) || p.t;
    var notes = (x && x.notes) || [{ k: '2-FER' }, { k: 'ALSO' }];
    var had2 = notes.some(function (n) { return n.k === '2-FER'; });
    var lines = '';
    if (!had2) lines += twoferLine(p.c, false);   // fers has a pair the old card had no line for
    notes.forEach(function (n) {
      if (n.k === '2-FER') lines += twoferLine(p.c, !!x);
      else if (n.k === 'ALSO') lines += alsoLine(p);
      else lines += '<p class="g-line"><b>' + esc(n.k) + '</b> ' + linkify(n.t, n.links) + '</p>';
    });
    if (lines.indexOf('<b>ALSO</b>') < 0) lines += alsoLine(p);
    var nameUrl = (x && x.nameUrl) || p.web || pota(p.c);
    var q = [p.c, p.n, co + ' county', type, p._reg || '', p._q || ''].concat(fersFor(p.c).map(function (d) { return d.refs.join(' ') + ' 2-fer ' + d.type; })).join(' ').toLowerCase();
    return '<article class="g-card" id="' + pid(p.c) + '" data-reg="' + esc(p._reg || '') + '" data-q="' + esc(q) + '">' +
      '<div class="g-head">' + ext(pota(p.c), esc(p.c), 'g-code') + '<h3>' + ext(nameUrl, esc(p.n)) + '</h3></div>' +
      '<p class="g-meta">' + esc(coLabel) + ' • ' + esc(type) + '</p><div class="g-btns">' + bh + '</div>' + lines + '</article>';
  }

  function groupsFor(order) {
    var P = STATE.P.slice(), groups = [], gm = {};
    if (order === 'az') {
      P.sort(function (a, b) { var x = a.n.toLowerCase(), y = b.n.toLowerCase(); return x < y ? -1 : x > y ? 1 : 0; });
      LETTERS.forEach(function (L) { gm[L] = { key: L, title: L, list: [] }; groups.push(gm[L]); });
      P.forEach(function (p) { var L = p.n.charAt(0).toUpperCase(); (gm[L] || gm.Z).list.push(p); });
    } else {
      P.sort(function (a, b) { return parseInt(a.c.slice(3), 10) - parseInt(b.c.slice(3), 10); });
      P.forEach(function (p) {
        var t = Math.floor(parseInt(p.c.slice(3), 10) / 1000), key = 'US-' + t + '000s';   // US-0000s, US-1000s ... US-10000s
        if (!gm[key]) { gm[key] = { key: key, title: key, t: t, list: [] }; groups.push(gm[key]); }
        gm[key].list.push(p);
      });
    }
    return { list: P, groups: groups };
  }
  function rangeLabel(g) {
    var a = g.t ? String(g.t * 1000) : '0000', z = g.t ? String(g.t * 1000 + 999) : '0999';
    return 'US-' + a + ' – US-' + z;
  }
  function gkey(k) { return k.replace(/[^A-Za-z0-9-]/g, ''); }

  function renderOrder(order) {
    var R = groupsFor(order), G = R.groups;
    var az = order === 'az';
    document.querySelectorAll('[data-order]').forEach(function (b) {
      var on = b.getAttribute('data-order') === order;
      b.classList.toggle('on', on); b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    $('gOrderK').textContent = az ? 'ALPHABETICAL ORDER • A–Z' : 'NUMERICAL ORDER • US-####';
    $('gKick1').textContent = $('gKick2').textContent = $('gKick3').textContent = 'KENTUCKY POTA FIELD RESOURCE • ' + (az ? 'A–Z' : 'NUMERICAL');
    $('gFindSub').textContent = az ? 'Tap a letter to jump to that section.' : 'Tap a number range to jump to that section.';
    $('gTiles').className = 'g-tiles' + (az ? ' az' : '');
    $('gTiles').innerHTML = G.map(function (g) {
      var n = g.list.length;
      if (az) return n ? '<a class="g-tile" href="#grp-' + gkey(g.key) + '"><b>' + g.key + '</b><small>' + n + (n === 1 ? ' PARK' : ' PARKS') + '</small></a>'
        : '<span class="g-tile none"><b>' + g.key + '</b><small>—</small></span>';
      return '<a class="g-tile" href="#grp-' + gkey(g.key) + '"><b>' + esc(g.key) + '</b><span>' + esc(rangeLabel(g)) + '</span><small>' + n + (n === 1 ? ' PARK' : ' PARKS') + '</small></a>';
    }).join('');
    var full = G.filter(function (g) { return g.list.length; });
    $('gJump').innerHTML = '<a href="#find">FIND</a><a href="#maps">MAPS</a>' +
      full.map(function (g) { return '<a href="#grp-' + gkey(g.key) + '">' + esc(g.key) + '</a>'; }).join('') + '<a href="#fers">2-FERS</a><a href="#wild">WILD RIVERS</a><a href="#nearby">NEARBY</a>';
    $('gCards').innerHTML = full.map(function (g, i) {
      return '<section class="g-grp' + (i ? (az ? '' : ' g-break') : '') + '" id="grp-' + gkey(g.key) + '"><h2 class="g-grp-h">' + esc(g.title) + '</h2>' +
        g.list.map(card).join('') + '</section>';
    }).join('');
    /* nearby */
    var L = R.list;
    $('gNearby').innerHTML = L.map(function (p) {
      var o = STATE.P.filter(function (q) { return q.c !== p.c; }).map(function (q) { return { p: q, d: mi(p.la, p.lo, q.la, q.lo) }; })
        .sort(function (a, b) { return a.d - b.d; });
      var w = o.filter(function (q) { return q.d <= 25; });
      var body = w.length ? '<b>WITHIN 25 MI · NEAREST FIRST</b> ' + w.map(function (q) {
        return '<a href="#' + pid(q.p.c) + '">' + esc(q.p.c) + '</a> ' + esc(q.p._short) + ' ' + fN(q.d) + ' mi';
      }).join(' • ') : (o.length ? '<b>WITHIN 25 MI</b> None in this guide — nearest is <a href="#' + pid(o[0].p.c) + '">' + esc(o[0].p.c) + '</a> ' + fN(o[0].d) + ' mi' : '');
      return '<div class="g-nb g-keep" id="' + pnid(p.c) + '"><div class="g-nb-h"><a href="#' + pid(p.c) + '">' + esc(p.c) + ' ' + esc(p.n) +
        '</a><a class="g-back" href="#' + pid(p.c) + '">‹ CARD</a></div><p>' + body + '</p></div>';
    }).join('');
    STATE.cards = [].slice.call(document.querySelectorAll('#gCards .g-card'));
    STATE.secs = [].slice.call(document.querySelectorAll('#gCards .g-grp'));
    apply();
  }

  function apply() {
    var q = $('gSearch').value.trim().toLowerCase(), reg = $('gRegion').value, n = 0;
    var words = q.split(/\s+/).filter(Boolean);
    STATE.cards.forEach(function (c) {
      var ok = (!reg || c.getAttribute('data-reg') === reg) && words.every(function (w) { return c.getAttribute('data-q').indexOf(w) >= 0; });
      c.classList.toggle('g-off', !ok);
      if (ok) n++;
    });
    STATE.secs.forEach(function (s) { s.classList.toggle('g-off', !s.querySelector('.g-card:not(.g-off)')); });
    $('gCount').textContent = (q || reg) ? 'Showing ' + n + ' of ' + STATE.cards.length + ' parks' : 'All ' + STATE.cards.length + ' parks';
    $('gNone').hidden = n > 0;
  }

  function renderStatic() {
    var D = STATE.D, G = STATE.G, C = STATE.C, P = STATE.P;
    /* 2-fers index */
    var F = G.fers, SP = F.spots, n3 = SP.filter(function (d) { return d.type === '3-fer'; }).length;
    $('gFersLead').textContent = 'All ' + SP.length + ' places in Kentucky where you may work two or three POTA parks at once (' + n3 + ' 3-fers, ' + (SP.length - n3) +
      ' 2-fers), checked against the POTA rules by the Kentucky Portable Club. Park names and numbers match the POTA Kentucky park list. ' +
      'GPS POINTS ARE NOT EXACT: they are guide pins that only get you to the area of the possible 2-fer or 3-fer, not to a confirmed spot. You and your gear must be on public land inside every park; trail and river parks within 100 ft of the trail or water (riverbank pins are approximate and were not checked against the water line); national forests only on Forest Service-owned land. ' +
      'Wickliffe Mounds, Big Bone Lick and Golden Pond are NOT within 100 ft of the river or trail; they rely on the NPS Lewis & Clark visitor center list. Tap a GPS point to open it in Google Maps. More detail, parking, NPS sources and walk-in points are in the KPC 2-Fers & 3-Fers Field Guide in the Members Room.';
    var rows = SP.slice().sort(function (a, b) { return a.sec - b.sec || (a.county < b.county ? -1 : a.county > b.county ? 1 : 0) || (a.refs.join() < b.refs.join() ? -1 : 1); });
    var html = '', cur = -1;
    rows.forEach(function (d) {
      if (d.sec !== cur) {
        if (cur >= 0) html += '</div>';
        cur = d.sec;
        var cnt = SP.filter(function (x) { return x.sec === cur; }).length;
        html += '<h3 class="g-fh">' + esc(F.sections[cur]) + '  (' + cnt + ')</h3><div class="g-frows">';
      }
      html += '<div class="g-frow g-keep"><span class="g-pill' + (d.type === '3-fer' ? ' three' : '') + '">' + esc(d.type.toUpperCase()) + '</span><div class="g-fmain"><div class="g-frefs">' +
        d.refs.map(function (r) { return '<a href="#' + pid(r) + '">' + esc(r) + '</a>'; }).join(' + ') + '</div><div class="g-fnames">' + esc(d.names.join(' + ')) +
        '</div></div><div class="g-fpin"><span>' + esc(d.county) + ' Co.</span>' + ext('https://www.google.com/maps/search/?api=1&query=' + d.pin[0].toFixed(5) + ',' + d.pin[1].toFixed(5),
        d.pin[0].toFixed(5) + ', ' + d.pin[1].toFixed(5) + ' ›', 'g-pinlink') + '<small>not exact • guide pin: ' + esc(String(d.pinWhat || 'general area').replace(/^Set up here$/i, 'Suggested area').replace(/^Target spot/, 'Target area')) + '</small></div></div>';
    });
    html += '</div>';
    $('gFers').innerHTML = html;
    $('gFersTail').innerHTML = '<b>Not counted here (do your own research):</b> ' + esc(F.unconfirmed.map(function (u) { return u[0] + (/^Checked/.test(u[1]) ? ' (checked: NOT a 2-fer)' : ''); }).join('; ')) +
      '. State parks inside the Daniel Boone outer boundary (Cumberland Falls, Natural Bridge, Buckhorn Lake) are state land, not national forest land.';

    /* wild rivers */
    var W = G.wildRivers, WI = G.wildIntro, feats = (STATE.WR && STATE.WR.features) || [];
    var x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9, cents = {};
    feats.forEach(function (f) {
      var ring = f.geometry.type === 'Polygon' ? f.geometry.coordinates[0] : f.geometry.coordinates[0][0], sx = 0, sy = 0;
      ring.forEach(function (p) { sx += p[0]; sy += p[1]; if (p[0] < x0) x0 = p[0]; if (p[0] > x1) x1 = p[0]; if (p[1] < y0) y0 = p[1]; if (p[1] > y1) y1 = p[1]; });
      cents[f.properties.NAME] = [sx / ring.length, sy / ring.length];
    });
    var mapHtml = '';
    if (feats.length) {
      var px0 = (x1 - x0) * .08, py0 = (y1 - y0) * .12;
      mapHtml = regionMap(null, D, C, [], { bbox: [x0 - px0, y0 - py0, x1 + px0, y1 + py0], extra: function (px, py) {
        var s = '';
        feats.forEach(function (f) {
          var polys = f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates;
          polys.forEach(function (pg) { s += '<path d="' + pg.map(function (ring) { return 'M' + ring.map(function (p) { return px(p[0]) + ' ' + py(p[1]); }).join('L') + 'Z'; }).join('') + '" fill="#2a6fb8" stroke="#1d4f86" stroke-width="1.6"/>'; });
        });
        W.forEach(function (r) {
          var c = cents[r.name];
          if (!c) return;
          s += '<a href="#wr-' + r.n + '"><title>' + esc(r.name) + '</title><circle cx="' + (+px(c[0]) + 14) + '" cy="' + (+py(c[1]) - 10) + '" r="11" fill="#13261c" stroke="#e9b13a" stroke-width="2"/><text x="' + (+px(c[0]) + 14) +
            '" y="' + (+py(c[1]) - 6) + '" class="m-n">' + r.n + '</text></a>';
        });
        return s;
      } });
    }
    $('gWildTitle').textContent = WI.mapTitle || 'Kentucky Wild River Corridors';
    $('gWildSub').textContent = WI.mapSub || '';
    $('gWildMap').innerHTML = mapHtml;
    $('gWildDT').textContent = WI.detailsTitle || 'Wild River Details';
    $('gWildDX').textContent = WI.detailsText || '';
    $('gWild').innerHTML = W.map(function (r) {
      var c = cents[r.name], refs = (String(r.xref).match(/US-\d+/g) || []);
      var near = '';
      if (c) { var bd = 1e9; (D.towns || []).forEach(function (t) { var dx = (t.lo - c[0]) * Math.cos(c[1] * Math.PI / 180), dy = t.la - c[1], dd = dx * dx + dy * dy; if (dd < bd) { bd = dd; near = t.n + ' (' + Math.round(Math.sqrt(dd) * 69) + ' mi)'; } }); }
      var pk = null;   // GPS and weather use the same point as the POTA park's card
      refs.some(function (x) { return P.some(function (p) { if (p.c === x && isFinite(p.la)) { pk = p; return true; } }); });
      if (!pk) (String(r.xref).match(/KFF-\d+/g) || []).some(function (x) { return (D.kff || []).some(function (k) { if (k.c === x && isFinite(k.la)) { pk = k; return true; } }); });   // no POTA card: use the WWFF card's point
      var fr = (G.fers && G.fers.spots || []).filter(function (d) { return d.refs.some(function (x) { return refs.indexOf(x) >= 0; }); });
      var xr = esc(r.xref).replace(/(POTA )?(US-\d+)/g, function (m, a, c) { return (a || '') + (P.some(function (p) { return p.c === c; }) ? '<a href="#' + pid(c) + '">' + c + '</a>' : ext(pota(c), c) + ' (not an active POTA park right now; WWFF only)'); })
        .replace(/KFF-\d+/g, function (k) { return ext('https://logsearch.wwff.co/directory/' + k, k); });
      return '<div class="g-wr g-keep" id="wr-' + r.n + '"><div class="g-wr-h"><span class="g-wn">' + r.n + '</span><h3>' + esc(r.name) + '</h3>' + ext(r.official, 'OFFICIAL PAGE →', 'b b-gold') + '</div>' +
        '<p class="g-line"><b>COUNTIES</b> ' + esc(r.counties) + ' • <b>ACRES</b> ' + esc(r.acres) + (near ? ' • <b>NEAREST TOWN</b> ' + esc(near) : '') + '</p>' +
        '<p class="g-line"><b>ACTIVATE AS</b> ' + xr + '</p>' +
        (fr.length ? '<p class="g-line"><b>2-FER / 3-FER</b> ' + fr.length + ' possible spot' + (fr.length > 1 ? 's' : '') + ' with ' + fr.reduce(function (u, d) { d.refs.forEach(function (x) { if (refs.indexOf(x) < 0 && u.indexOf(x) < 0) u.push(x); }); return u; }, []).map(function (x) { return '<a href="#' + pid(x) + '">' + esc(x) + '</a>'; }).join(', ') + ' — see the <a href="#fers">2-Fers &amp; 3-Fers Index</a> (GPS points not exact).</p>' : '') +
        '<div class="g-btns">' + (pk ? ext(gps(pk.la, pk.lo), 'GPS', 'b b-gps') + ext(wx(pk.la, pk.lo), 'WEATHER', 'b b-wx') : '') +
        (refs[0] ? '<a class="b b-near" href="kpc-park-notes.html#' + refs[0] + '">PARK TIPS ›</a>' : '') + '</div></div>';
    }).join('');

    /* regional maps */
    var rc = {};
    P.forEach(function (p) { if (p._reg) rc[p._reg] = (rc[p._reg] || 0) + 1; });
    $('gRegion').innerHTML = '<option value="">All regions (' + P.length + ')</option>' + REG.map(function (r) {
      return '<option value="' + esc(r[0]) + '"' + (rc[r[0]] ? '' : ' disabled') + '>' + esc(r[0]) + ' (' + (rc[r[0]] || 0) + ')</option>';
    }).join('');
    $('gRegChips').innerHTML = REG.map(function (r) { return '<a href="#map-' + r[0].replace(/ /g, '-') + '">' + r[2] + '</a>'; }).join('');
    $('gMaps').innerHTML = REG.map(function (r, i) {
      var list = P.filter(function (p) { return p._reg === r[0]; });
      var pins = list.map(function (p) {
        return { id: pid(p.c), la: p.la, lo: p.lo, color: CAT[catOf(p.t)][1], label: p.c.slice(3), title: p.c + ' ' + p.n };
      });
      return '<div class="g-mapbox g-keep' + (i ? ' g-break' : '') + '" id="map-' + r[0].replace(/ /g, '-') + '"><div class="g-kick">REGIONAL MAP • ' + esc(r[0].toUpperCase()) +
        '</div><h3>' + esc(r[1]) + '</h3><p class="g-sub">' + list.length + (list.length === 1 ? ' park' : ' parks') +
        ' in this region • Tap a pin to open its card • Pins at each reference point (not boundaries)</p>' + regionMap(r[0], D, C, pins) +
        '<p class="g-legend">' + CAT.map(function (c) { return '<span><i style="background:' + c[1] + '"></i>' + esc(c[0]) + '</span>'; }).join('') +
        '<span><i class="town"></i>County seat / major town</span></p>' +
        '<p class="g-foot">Regions follow mapofkentucky.com; counties it does not list are placed with their neighboring region. County lines &amp; towns: Kentucky state GIS.</p></div>';
    }).join('');
    var off = P.filter(function (p) { return !p._reg; });
    $('gOffMap').innerHTML = off.length ? 'Not on a regional map (reference point outside Kentucky): ' + off.map(function (p) { return '<a href="#' + pid(p.c) + '">' + esc(p.c) + '</a> ' + esc(p.n); }).join(' • ') + '.' : '';
    $('gUpdated').textContent = D.updated ? 'Live data updated ' + D.updated + '.' : '';
    $('gTotal').textContent = P.length;
  }

  function getOrder() {
    var m = /[?&]order=(az|num)\b/.exec(location.search);
    return m ? m[1] : 'num';
  }
  function done() {
    var f = document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve();
    f.then(function () { requestAnimationFrame(function () { root.dataset.ready = '1'; }); });
  }
  function getJSON(u, optional) {
    return fetch(u, { cache: 'no-cache' }).then(function (r) { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); })
      .catch(function (e) { if (optional) return null; throw e; });
  }
  Promise.all([getJSON('kpc-ky-data.json'), getJSON('kpc-guide-pota-data.json'), getJSON('kpc-ky-counties-hd.json'), getJSON('ky-wild-rivers.geojson', true)])
    .then(function (a) {
      setup(a[0], a[1], a[2], a[3]);
      renderStatic();
      renderOrder(getOrder());
      $('gSearch').addEventListener('input', apply);
      $('gRegion').addEventListener('change', apply);
      $('gClear').addEventListener('click', function () { $('gSearch').value = ''; $('gRegion').value = ''; apply(); $('gSearch').focus(); });
      document.querySelectorAll('[data-order]').forEach(function (b) {
        b.addEventListener('click', function () {
          var o = b.getAttribute('data-order');
          try { history.replaceState(null, '', location.pathname + '?order=' + o + location.hash); } catch (e) { /* file:// */ }
          renderOrder(o);
        });
      });
      if (location.hash) { var t = document.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView(); }
      done();
    })
    .catch(function (e) {
      var el = $('gErr');
      if (el) { el.hidden = false; el.textContent = 'Sorry, the park list did not load (' + e.message + '). Try reloading the page.'; }
      root.dataset.ready = 'error';
      if (window.console) console.warn(e);
    });
})();
