/* KPC Kentucky SOTA (W4K) Field Resource — kpc-guide-sota.html
   Summit codes, names, counties, elevation, points and GPS come live from kpc-ky-data.json.
   The extra card lines from the PDF (KY GIS public land, map region) come from kpc-guide-sota-data.json
   (built by .claude/build/guides/extract_sota.py). Parks within 3 mi and nearby summits are worked out here,
   with the same rules the PDF used (checked by .claude/build/guides/check_guides.py).
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
  var PTS = [[10, '#b4442c'], [8, '#8a5a2b'], [6, '#e2a52a'], [4, '#1d5a3a'], [2, '#7db36a'], [1, '#9a9a9a']];
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

  function render(D, G, C) {
    var X = G.summits || {};
    var S = D.summits.slice().sort(function (a, b) { return a.c < b.c ? -1 : 1; });
    var P = D.parks.concat(D.kff);
    var byCode = {};
    S.forEach(function (s) { byCode[s.c] = s; });
    function regionOf(s) {
      var x = X[s.c];
      if (x && x.mapRegion) return x.mapRegion;
      var r = D.regions[String(s.co).split('/')[0].trim().toUpperCase()];
      return r || D.regions[String(countyAt(C, s.la, s.lo)).toUpperCase()] || 'Eastern Kentucky';
    }
    function ptsColor(p) { for (var i = 0; i < PTS.length; i++) if (p >= PTS[i][0]) return PTS[i][1]; return PTS[PTS.length - 1][1]; }

    /* groups: EC in blocks of 50, then KA, PR ... */
    var groups = [], gmap = {};
    S.forEach(function (s) {
      var m = /^W4K\/([A-Z]{2})-(\d{3})$/.exec(s.c), key, title;
      if (!m) { key = 'other'; title = 'Other'; }
      else if (m[1] === 'EC') {
        var b = Math.floor((+m[2] - 1) / 50) * 50 + 1, bs = ('00' + b).slice(-3);
        key = 'EC-' + bs; title = 'EC-' + bs + '+';
      } else { key = m[1]; title = m[1]; }
      if (!gmap[key]) { gmap[key] = { key: key, title: title, list: [] }; groups.push(gmap[key]); }
      gmap[key].list.push(s);
      s._g = key; s._reg = regionOf(s);
    });

    /* index tiles */
    $('gTiles').innerHTML = groups.map(function (g) {
      var a = g.list[0].c.replace('W4K/', ''), z = g.list[g.list.length - 1].c.replace('W4K/', '');
      var big = 'W4K/' + g.key;
      return '<a class="g-tile" href="#grp-' + g.key + '"><b>' + esc(big) + '</b><span>' + esc(a) + ' – ' + esc(z) + '</span><small>' +
        g.list.length + (g.list.length === 1 ? ' SUMMIT' : ' SUMMITS') + '</small></a>';
    }).join('');
    $('gRegChips').innerHTML = REG.map(function (r) { return '<a href="#map-' + r[0].replace(/ /g, '-') + '">' + r[2] + '</a>'; }).join('');

    /* region filter */
    var rc = {};
    S.forEach(function (s) { rc[s._reg] = (rc[s._reg] || 0) + 1; });
    $('gRegion').innerHTML = '<option value="">All regions (' + S.length + ')</option>' + REG.map(function (r) {
      return '<option value="' + esc(r[0]) + '"' + (rc[r[0]] ? '' : ' disabled') + '>' + esc(r[0]) + ' (' + (rc[r[0]] || 0) + ')</option>';
    }).join('');
    $('gJump').innerHTML = '<a href="#find">FIND</a><a href="#maps">MAPS</a><a href="#county">BY COUNTY</a>' +
      groups.map(function (g) { return '<a href="#grp-' + g.key + '">' + esc(g.title) + '</a>'; }).join('') + '<a href="#nearby">NEARBY</a>';

    /* regional maps */
    $('gMaps').innerHTML = REG.map(function (r, i) {
      var list = S.filter(function (s) { return s._reg === r[0]; });
      var pins = list.map(function (s) {
        return { id: sid(s.c), la: s.la, lo: s.lo, color: ptsColor(s.pts), label: s.c.replace('W4K/', ''), title: s.c + ' ' + s.n + ' (' + s.pts + ' pt)' };
      });
      return '<div class="g-mapbox g-keep' + (i ? ' g-break' : '') + '" id="map-' + r[0].replace(/ /g, '-') + '"><div class="g-kick">REGIONAL MAP • ' + esc(r[0].toUpperCase()) +
        '</div><h3>' + esc(r[1]) + '</h3><p class="g-sub">' + list.length + (list.length === 1 ? ' summit' : ' summits') +
        ' in this region • Tap a pin to open its card • Pins at each reference point (not boundaries)</p>' + regionMap(r[0], D, C, pins) +
        '<p class="g-legend">' + PTS.map(function (p) { return '<span><i style="background:' + p[1] + '"></i>' + p[0] + ' pt</span>'; }).join('') +
        '<span><i class="town"></i>County seat / major town</span></p>' +
        '<p class="g-foot">Regions follow mapofkentucky.com; counties it does not list are placed with their neighboring region. County lines &amp; towns: Kentucky state GIS.</p></div>';
    }).join('');

    /* county index */
    var byCo = {};
    S.forEach(function (s) { (byCo[s.co] = byCo[s.co] || []).push(s); });
    var cos = Object.keys(byCo).sort();
    $('gCountyHead').textContent = cos.length + ' counties • ' + S.length + ' summits. County from the Kentucky state GIS county map. Tap a summit to jump to its card.';
    $('gCounty').innerHTML = cos.map(function (co) {
      var L = byCo[co];
      return '<div class="g-co g-keep"><div class="g-co-h"><h3>' + esc(co) + ' County</h3><span>' + L.length + (L.length === 1 ? ' SUMMIT' : ' SUMMITS') + '</span></div><p>' +
        L.map(function (s) { return '<a href="#' + sid(s.c) + '"><b>' + esc(s.c.replace('W4K/', '')) + '</b> ' + esc(s.n) + '</a>'; }).join(' • ') + '</p></div>';
    }).join('');

    /* cards */
    var nearPark = {};
    $('gCards').innerHTML = groups.map(function (g, gi) {
      return '<section class="g-grp' + (gi ? ' g-break' : '') + '" id="grp-' + g.key + '"><h2 class="g-grp-h">' + esc(g.title) + '</h2>' + g.list.map(function (s) {
        var x = X[s.c] || {};
        var inside = {};
        (x.landLinks || []).forEach(function (l) { inside[l.label] = 1; });
        var near = P.map(function (p) { return { c: p.c, n: p.n, d: mi(s.la, s.lo, p.la, p.lo) }; })
          .filter(function (p) { return p.d <= 3.0 && !inside[p.c]; })
          .sort(function (a, b) { return a.d - b.d; });
        nearPark[s.c] = near;
        var land = '';
        if (x.land) {
          var t = esc(x.land);
          (x.landLinks || []).forEach(function (l) { t = t.replace(esc(l.label), ext(l.url, esc(l.label))); });
          land = '<p class="g-line"><b>INSIDE PUBLIC LAND (KY GIS)</b> ' + t + ' <span class="g-dim">(official KY public-land polygons; confirm before claiming)</span></p>';
        }
        var nl = near.length ? '<p class="g-line"><b>POTA / KFF WITHIN 3 MI</b> ' + near.map(function (p) {
          return ext(refUrl(p.c), esc(p.c), 'g-ref') + ' ' + esc(p.n) + ' ' + f1(p.d) + ' mi';
        }).join(' • ') + ' <span class="g-dim">(to the park’s reference point — check boundaries)</span></p>' : '';
        var q = [s.c, s.n, s.co + ' county', s._reg, x.land || ''].concat(near.map(function (p) { return p.c + ' ' + p.n; })).join(' ').toLowerCase();
        return '<article class="g-card" id="' + sid(s.c) + '" data-reg="' + esc(s._reg) + '" data-q="' + esc(q) + '">' +
          '<div class="g-head">' + ext(sotlas(s.c), esc(s.c), 'g-code') + '<h3>' + ext(sotlas(s.c), esc(s.n)) + '</h3></div>' +
          '<p class="g-meta">' + esc(s.co) + ' County • Region ' + esc(s.c.slice(4, 6)) + ' • ' + num(Math.round(s.ft * 0.3048)) + ' m / ' + num(s.ft) + ' ft • ' +
          s.pts + (s.pts === 1 ? ' point' : ' points') + '</p>' +
          '<div class="g-btns">' + ext(gps(s.la, s.lo), 'GPS', 'b b-gps') + ext(osm(s.la, s.lo), 'OSM MAP', 'b b-osm') + ext(wx(s.la, s.lo), 'WEATHER', 'b b-wx') +
          '<a class="b b-near" href="#' + nid(s.c) + '">NEARBY ›</a></div>' + land + nl + '</article>';
      }).join('') + '</section>';
    }).join('');

    /* nearby summits */
    $('gNearby').innerHTML = S.map(function (s) {
      var L = S.filter(function (o) { return o.c !== s.c; }).map(function (o) { return { s: o, d: mi(s.la, s.lo, o.la, o.lo) }; })
        .sort(function (a, b) { return a.d - b.d; });
      var w = L.filter(function (o) { return o.d <= 10; });
      var body = w.length ? '<b>WITHIN 10 MI · NEAREST FIRST</b> ' + w.map(function (o) {
        return '<a href="#' + sid(o.s.c) + '">' + esc(o.s.c) + '</a> ' + esc(o.s.n) + ' ' + f1(o.d) + ' mi';
      }).join(' • ') : (L.length ? '<b>WITHIN 10 MI</b> None in this guide — nearest is <a href="#' + sid(L[0].s.c) + '">' + esc(L[0].s.c) + '</a> ' + fN(L[0].d) + ' mi' : '');
      return '<div class="g-nb g-keep" id="' + nid(s.c) + '"><div class="g-nb-h"><a href="#' + sid(s.c) + '">' + esc(s.c) + ' ' + esc(s.n) +
        '</a><a class="g-back" href="#' + sid(s.c) + '">‹ CARD</a></div><p>' + body + '</p></div>';
    }).join('');

    $('gUpdated').textContent = D.updated ? 'Live data updated ' + D.updated + '.' : '';
    $('gTotal').textContent = S.length;

    /* search + region filter (screen only; print always shows every card) */
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
      $('gCount').textContent = (q || reg) ? 'Showing ' + n + ' of ' + cards.length + ' summits' : 'All ' + cards.length + ' summits';
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
  Promise.all([getJSON('kpc-ky-data.json'), getJSON('kpc-guide-sota-data.json'), getJSON('kpc-ky-counties.json')])
    .then(function (a) { render(a[0], a[1], a[2]); done(); })
    .catch(function (e) {
      var el = $('gErr');
      if (el) { el.hidden = false; el.textContent = 'Sorry, the summit list did not load (' + e.message + '). Try reloading, or use the PDF download.'; }
      root.dataset.ready = 'error';
      if (window.console) console.warn(e);
    });
})();
