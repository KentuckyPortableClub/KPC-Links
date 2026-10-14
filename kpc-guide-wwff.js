/* KPC Kentucky WWFF (KFF) Field Resource — kpc-guide-wwff.html
   Reference codes, names, counties, GPS and the paired POTA park come live from kpc-ky-data.json.
   The extra card details from the PDF (park type, official map / website / entrance / camping links, access points,
   notes, SOTA inside, map region) come from kpc-guide-wwff-data.json (built by .claude/build/guides/extract_wwff.py).
   SOTA within 3 mi and nearby parks are worked out here with the PDF's rules (checked by check_guides.py).
   A KFF reference that is in kpc-ky-data.json but not yet in the PDF still gets a card, using its POTA park's links.
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

  /* ---------- county polygons (kpc-ky-counties.json: [{n, r:[ring of [lon,lat]]}]) ---------- */
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
  function regionMap(regionKey, D, C, pins) {
    var inReg = C.filter(function (c) { return D.regions[c.n.toUpperCase()] === regionKey; });
    var x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    inReg.forEach(function (c) { c.r.forEach(function (ring) { ring.forEach(function (p) {
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
      var r = D.regions[c.n.toUpperCase()] === regionKey;
      s.push('<path d="' + path(c) + '" fill="' + (r ? '#ffffff' : '#ece4d1') + '" stroke="' + (r ? '#7e9c88' : '#cbbfa4') + '" stroke-width="' + (r ? 1.1 : .7) + '"/>');
    });
    inReg.forEach(function (c) {
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
    pins.forEach(function (p) {
      s.push('<a href="#' + p.id + '"><title>' + esc(p.title) + '</title><circle cx="' + px(p.lo) + '" cy="' + py(p.la) + '" r="6.5" fill="' + p.color +
        '" stroke="#fff" stroke-width="1.6"/><text x="' + (+px(p.lo) + 8) + '" y="' + (+py(p.la) - 5) + '" class="m-p">' + esc(p.label) + '</text></a>');
    });
    s.push('</svg>');
    return s.join('');
  }

  var POTA_COLOR = '#e2a52a', ONLY_COLOR = '#b4442c';
  var BTN = { map: 'OFFICIAL MAP', areamap: 'AREA MAP', brochure: 'BROCHURE', web: 'WEBSITE', entrance: 'ENTRANCE',
    camp: 'CAMPING ›', resort: 'RESORT ›', cabins: 'CABINS ›' };
  var NOTE_ORDER = ['PARKING (official page)', 'ACCESS POINTS', 'ACCESS ADVISORY', 'TRAIL', 'ALSO', 'NOTES'];
  function kid(c) { return 's-' + c; }
  function knid(c) { return 'n-' + c; }
  function logsearch(c) { return 'https://logsearch.wwff.co/directory/' + c; }
  function shortSota(n) { return String(n).replace(/^Unnamed summit \((.+)\)$/, 'Unnamed $1'); }

  function render(D, G, C) {
    var X = G.refs || {};
    var K = D.kff.slice().sort(function (a, b) { return a.c < b.c ? -1 : 1; });
    var parks = {};
    D.parks.forEach(function (p) { parks[p.c] = p; });
    var sota = {};
    D.summits.forEach(function (s) { sota[s.c] = s; });
    function regionOf(k) {
      var x = X[k.c];
      if (x && x.mapRegion) return x.mapRegion;
      var r = D.regions[String(k.co).split('/')[0].trim().toUpperCase()];
      return r || D.regions[String(countyAt(C, k.la, k.lo)).toUpperCase()] || 'Eastern Kentucky';
    }

    /* groups by thousands */
    var groups = [], gmap = {};
    K.forEach(function (k) {
      var n = parseInt(k.c.slice(4), 10), t = Math.floor(n / 1000), key = 'KFF-' + t + '000s';
      if (!gmap[key]) { gmap[key] = { key: key, t: t, list: [] }; groups.push(gmap[key]); }
      gmap[key].list.push(k);
      k._reg = regionOf(k);
    });
    $('gTiles').innerHTML = groups.map(function (g) {
      var a = 'KFF-' + g.t + '000', z = g.t + '999';
      return '<a class="g-tile" href="#grp-' + g.key + '"><b>' + esc(g.key) + '</b><span>' + esc(a) + ' – ' + esc(z) + '</span><small>' +
        g.list.length + (g.list.length === 1 ? ' PARK' : ' PARKS') + '</small></a>';
    }).join('');
    $('gRegChips').innerHTML = REG.map(function (r) { return '<a href="#map-' + r[0].replace(/ /g, '-') + '">' + r[2] + '</a>'; }).join('');
    var rc = {};
    K.forEach(function (k) { rc[k._reg] = (rc[k._reg] || 0) + 1; });
    $('gRegion').innerHTML = '<option value="">All regions (' + K.length + ')</option>' + REG.map(function (r) {
      return '<option value="' + esc(r[0]) + '"' + (rc[r[0]] ? '' : ' disabled') + '>' + esc(r[0]) + ' (' + (rc[r[0]] || 0) + ')</option>';
    }).join('');
    $('gJump').innerHTML = '<a href="#find">FIND</a><a href="#maps">MAPS</a>' +
      groups.map(function (g) { return '<a href="#grp-' + g.key + '">' + esc(g.key) + '</a>'; }).join('') + '<a href="#nearby">NEARBY</a>';

    /* regional maps */
    $('gMaps').innerHTML = REG.map(function (r, i) {
      var list = K.filter(function (k) { return k._reg === r[0]; });
      var pins = list.map(function (k) {
        return { id: kid(k.c), la: k.la, lo: k.lo, color: k.p ? POTA_COLOR : ONLY_COLOR, label: k.c.slice(4), title: k.c + ' ' + k.n + (k.p ? ' (POTA ' + k.p + ')' : ' (KFF only)') };
      });
      return '<div class="g-mapbox g-keep' + (i ? ' g-break' : '') + '" id="map-' + r[0].replace(/ /g, '-') + '"><div class="g-kick">REGIONAL MAP • ' + esc(r[0].toUpperCase()) +
        '</div><h3>' + esc(r[1]) + '</h3><p class="g-sub">' + list.length + (list.length === 1 ? ' reference' : ' references') +
        ' in this region • Tap a pin to open its card • Pins at each reference point (not boundaries)</p>' + regionMap(r[0], D, C, pins) +
        '<p class="g-legend"><span><i style="background:' + POTA_COLOR + '"></i>KFF with POTA match</span><span><i style="background:' + ONLY_COLOR +
        '"></i>KFF only</span><span><i class="town"></i>County seat / major town</span></p>' +
        '<p class="g-foot">Regions follow mapofkentucky.com; counties it does not list are placed with their neighboring region. County lines &amp; towns: Kentucky state GIS.</p></div>';
    }).join('');

    function linkify(t, links) {
      var h = esc(t);
      (links || []).forEach(function (l) { h = h.replace(esc(l.label), ext(l.url, esc(l.label))); });
      return h;
    }
    function sotaLink(c) { return ext(sotlas(c), esc(c)); }

    /* cards */
    $('gCards').innerHTML = groups.map(function (g, gi) {
      return '<section class="g-grp' + (gi ? ' g-break' : '') + '" id="grp-' + g.key + '"><h2 class="g-grp-h">' + esc(g.key) + '</h2>' + g.list.map(function (k) {
        var x = X[k.c], park = k.p ? parks[k.p] : null;
        var links = x ? (x.links || []) : [];
        if (!x && park) {  // not in the PDF yet: borrow the paired POTA park's links
          if (park.off) links.push({ k: 'map', url: park.off });
          if (park.web) links.push({ k: 'web', url: park.web });
          if (park.camp) links.push({ k: 'camp', url: park.camp });
        }
        function L(keys, cls) {
          return links.filter(function (l) { return keys.indexOf(l.k) >= 0; }).map(function (l) { return ext(l.url, BTN[l.k], 'b ' + cls); }).join('');
        }
        var potaName = park ? park.n : (x && x.potaName) || '';
        var co = String(k.co), coLabel = /[()]/.test(co) ? co : co + (co.indexOf('/') >= 0 ? ' Counties' : ' County');
        var type = x ? x.type : (park && park.t) || '';
        var meta = [coLabel, type, k.p ? 'POTA: ' + potaName : ''].filter(Boolean).join(' • ');
        var btns = L(['map', 'areamap', 'brochure'], 'b-map') + ext(gps(k.la, k.lo), 'GPS', 'b b-gps') + ext(osm(k.la, k.lo), 'OSM BOUNDARY', 'b b-osm') +
          L(['web'], 'b-web') + (k.p ? ext('https://next.pota.app/park/' + k.p, 'POTA ' + esc(k.p), 'b b-pota') : '') + L(['entrance'], 'b-gps') +
          ext(wx(k.la, k.lo), 'WEATHER', 'b b-wx') + '<a class="b b-near" href="#' + knid(k.c) + '">NEARBY ›</a>' + L(['camp', 'resort', 'cabins'], 'b-gold');
        /* notes, in the PDF's order */
        var notes = {};
        ((x && x.notes) || []).forEach(function (n) { notes[n.k] = n; });
        var inside = (x && x.also && x.also.inside) || [];
        var nearS = D.summits.map(function (s) { return { s: s, d: mi(k.la, k.lo, s.la, s.lo) }; })
          .filter(function (o) { return o.d <= 3.0 && inside.indexOf(o.s.c) < 0; }).sort(function (a, b) { return a.d - b.d; });
        var also = [];
        if (inside.length) also.push('SOTA inside (KY GIS): ' + inside.map(function (c) { return sotaLink(c) + ' ' + esc(shortSota(sota[c] ? sota[c].n : '')); }).join(' • '));
        if (nearS.length) also.push('SOTA within 3 mi: ' + nearS.map(function (o) { return sotaLink(o.s.c) + ' ' + esc(shortSota(o.s.n)) + ' ' + f1(o.d) + ' mi'; }).join(' • '));
        var lines = NOTE_ORDER.map(function (key) {
          if (key === 'ALSO') return also.length ? '<p class="g-line"><b>ALSO</b> ' + also.join(' | ') + '</p>' : '';
          var n = notes[key];
          return n ? '<p class="g-line"><b>' + esc(key) + '</b> ' + linkify(n.t, n.links) + '</p>' : '';
        }).join('');
        var q = [k.c, k.n, co + ' county', type, k.p || '', potaName, k._reg].concat(nearS.map(function (o) { return o.s.c; }), inside).join(' ').toLowerCase();
        var nameUrl = (x && x.nameUrl) || (park && park.web) || logsearch(k.c);
        return '<article class="g-card" id="' + kid(k.c) + '" data-reg="' + esc(k._reg) + '" data-q="' + esc(q) + '">' +
          '<div class="g-head">' + ext(logsearch(k.c), esc(k.c), 'g-code') + '<h3>' + ext(nameUrl, esc(k.n)) + '</h3></div>' +
          '<p class="g-meta">' + esc(meta) + '</p><div class="g-btns">' + btns + '</div>' + lines + '</article>';
      }).join('') + '</section>';
    }).join('');

    /* nearby parks */
    $('gNearby').innerHTML = K.map(function (k) {
      var L = K.filter(function (o) { return o.c !== k.c; }).map(function (o) { return { k: o, d: mi(k.la, k.lo, o.la, o.lo) }; })
        .sort(function (a, b) { return a.d - b.d; });
      var w = L.filter(function (o) { return o.d <= 25; });
      var body = w.length ? '<b>WITHIN 25 MI · NEAREST FIRST</b> ' + w.map(function (o) {
        return '<a href="#' + kid(o.k.c) + '">' + esc(o.k.c) + '</a> ' + esc(o.k.n) + ' ' + fN(o.d) + ' mi';
      }).join(' • ') : (L.length ? '<b>WITHIN 25 MI</b> None in this guide — nearest is <a href="#' + kid(L[0].k.c) + '">' + esc(L[0].k.c) + '</a> ' + fN(L[0].d) + ' mi' : '');
      return '<div class="g-nb g-keep" id="' + knid(k.c) + '"><div class="g-nb-h"><a href="#' + kid(k.c) + '">' + esc(k.c) + ' ' + esc(k.n) +
        '</a><a class="g-back" href="#' + kid(k.c) + '">‹ CARD</a></div><p>' + body + '</p></div>';
    }).join('');

    $('gUpdated').textContent = D.updated ? 'Live data updated ' + D.updated + '.' : '';
    $('gTotal').textContent = K.length;

    var cards = [].slice.call(document.querySelectorAll('#gCards .g-card'));
    var secs = [].slice.call(document.querySelectorAll('#gCards .g-grp'));
    function apply() {
      var q = $('gSearch').value.trim().toLowerCase(), reg = $('gRegion').value, n = 0;
      var words = q.split(/\s+/).filter(Boolean);
      cards.forEach(function (c) {
        var ok = (!reg || c.getAttribute('data-reg') === reg) && words.every(function (w) { return c.getAttribute('data-q').indexOf(w) >= 0; });
        c.classList.toggle('g-off', !ok);
        if (ok) n++;
      });
      secs.forEach(function (s) { s.classList.toggle('g-off', !s.querySelector('.g-card:not(.g-off)')); });
      $('gCount').textContent = (q || reg) ? 'Showing ' + n + ' of ' + cards.length + ' references' : 'All ' + cards.length + ' references';
      $('gNone').hidden = n > 0;
    }
    $('gSearch').addEventListener('input', apply);
    $('gRegion').addEventListener('change', apply);
    $('gClear').addEventListener('click', function () { $('gSearch').value = ''; $('gRegion').value = ''; apply(); $('gSearch').focus(); });
    apply();
    if (location.hash) { var t = document.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView(); }
  }

  function done() {
    var f = document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve();
    f.then(function () { requestAnimationFrame(function () { root.dataset.ready = '1'; }); });
  }
  function getJSON(u) {
    return fetch(u, { cache: 'no-cache' }).then(function (r) { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
  }
  Promise.all([getJSON('kpc-ky-data.json'), getJSON('kpc-guide-wwff-data.json'), getJSON('kpc-ky-counties.json')])
    .then(function (a) { render(a[0], a[1], a[2]); done(); })
    .catch(function (e) {
      var el = $('gErr');
      if (el) { el.hidden = false; el.textContent = 'Sorry, the KFF list did not load (' + e.message + '). Try reloading, or open the PDF.'; }
      root.dataset.ready = 'error';
      if (window.console) console.warn(e);
    });
})();
