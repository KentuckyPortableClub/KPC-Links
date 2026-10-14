/* KPC Campgrounds & Cabins (kpc-campgrounds.html)
   - kpc-campgrounds.json: campgrounds, cabins and lodges INSIDE Kentucky POTA parks (checked against official pages).
   - kpc-ky-data.json: park names, counties, GPS, KFF and SOTA lists, confirmed 2-fer partners (tf), regions.
   - kpc-campground-notes.json: visitor reviews (written by .github/scripts/kpc_campground_notes.py from the
     KPC Campground Reviews Google Form). place = a campground/lodging id from kpc-campgrounds.json, or null for
     a place outside the parks (then "other" holds its name / where / gps).
   - kpc-campground-form.json: {url, placeEntry}. When url is empty the Review buttons stay hidden. */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function ext(href, text, cls) { return href ? '<a class="cg-b' + (cls ? ' ' + cls : '') + '" href="' + esc(href) + '" target="_blank" rel="noopener">' + text + '</a>' : ''; }
  function gps(la, lo) { return 'https://www.google.com/maps/search/?api=1&query=' + la + ',' + lo; }
  function wx(la, lo) { return 'https://weather.com/weather/today/l/' + la + ',' + lo; }
  function getJSON(u, opt) { return fetch(u, { cache: 'no-cache' }).then(function (r) { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); }).catch(function (e) { if (opt) return null; throw e; }); }
  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function nice(iso) { var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || ''); return m ? MON[+m[2] - 1] + ' ' + (+m[3]) + ', ' + m[1] : ''; }
  function stars(n) { n = Math.round(n * 2) / 2; var s = ''; for (var i = 1; i <= 5; i++) s += n >= i ? '★' : (n >= i - .5 ? '⯪' : '☆'); return s; }

  var D, C, N = [], FORM = null, F = {}, ROWS = [];

  /* kpc-campground-form.json: url, placeEntry (Campground or cabin), and optionally kindEntry + kindInside / kindOutside
     (the two answers of "What are you reviewing") so the form opens on the right section. */
  function formLink(label, outside) {
    if (!FORM || !FORM.url) return '';
    var q = ['usp=pp_url'];
    if (FORM.kindEntry && (outside ? FORM.kindOutside : FORM.kindInside)) q.push(FORM.kindEntry + '=' + encodeURIComponent(outside ? FORM.kindOutside : FORM.kindInside));
    if (label && FORM.placeEntry && !outside) q.push(FORM.placeEntry + '=' + encodeURIComponent(label));
    return FORM.url + (FORM.url.indexOf('?') < 0 ? '?' : '&') + q.join('&');
  }
  function reviewsFor(id) { return N.filter(function (n) { return n.place === id; }); }
  function revHtml(list) {
    if (!list.length) return '';
    var r = list.filter(function (n) { return n.rating; }), avg = r.length ? r.reduce(function (a, n) { return a + n.rating; }, 0) / r.length : 0;
    return '<details class="cg-revs"><summary>' + (avg ? '<span class="cg-stars">' + stars(avg) + '</span> ' + avg.toFixed(1) + ' • ' : '') + list.length + ' REVIEW' + (list.length > 1 ? 'S' : '') + '</summary>' +
      list.map(function (n) {
        return '<div class="cg-rev"><div class="who">' + esc(n.call) + (n.date ? ' • ' + esc(n.date) : '') + (n.rating ? ' • <span class="cg-stars">' + stars(n.rating) + '</span>' : '') + (n.site ? ' • site ' + esc(n.site) : '') + (n.stayed ? ' • stayed ' + esc(n.stayed) : '') + '</div>' +
          ((n.facts || []).length ? '<div class="facts">' + n.facts.map(function (x) { return '<span><b>' + esc(x[0]) + ':</b> ' + esc(x[1]) + '</span>'; }).join('') + '</div>' : '') +
          esc(n.text).replace(/\n/g, '<br>') + (n.photos || []).map(function (p) { return '<img src="' + esc(p) + '" alt="Photo from ' + esc(n.call) + '" loading="lazy">'; }).join('') + '</div>';
      }).join('') + '</details>';
  }

  function placeHtml(x, park, kind) {
    var closed = x.status === 'closed';
    var facts = [];
    if (kind === 'camp') {
      if (x.sites) facts.push('<b>SITES</b> ' + esc(x.sites));
      if (x.hookups) facts.push('<b>HOOKUPS</b> ' + esc(x.hookups));
      if (x.season) facts.push('<b>SEASON</b> ' + esc(x.season));
    } else if (x.units) facts.push('<b>UNITS</b> ' + esc(x.units));
    var label = park.c + ' · ' + x.name;
    var rv = reviewsFor(x.id), fl = formLink(label);
    return '<div class="cg-place" id="' + esc(x.id) + '"><h3>' + (kind === 'lodge' ? '<span class="cg-kind">' + esc(x.kind || 'lodging') + '</span>' : '') + esc(x.name) + (closed ? '<span class="cg-closed">CLOSED</span>' : '') + '</h3>' +
      (facts.length ? '<p>' + facts.join(' • ') + '</p>' : '') +
      (x.extras ? '<p>' + esc(x.extras) + '</p>' : '') +
      (x.notes ? '<p>' + esc(x.notes) + '</p>' : '') +
      (x.note ? '<p>' + esc(x.note) + '</p>' : '') +
      (x.phone ? '<p><b>PHONE</b> <a href="tel:' + esc(String(x.phone).replace(/[^0-9+]/g, '')) + '">' + esc(x.phone) + '</a></p>' : '') +
      '<div class="cg-btns">' + ext(x.url, kind === 'camp' ? 'CAMPGROUND PAGE' : 'PAGE', 'dark') + (closed && x.source && x.source !== x.url ? ext(x.source, 'WHERE IT SAYS CLOSED') : '') + ext(x.map, 'CAMPGROUND MAP', 'gold') + ext(x.reserve, kind === 'camp' ? 'RESERVE' : 'BOOK') +
      (isFinite(x.la) && x.la ? ext(gps(x.la, x.lo), 'GPS') : '') +
      (fl ? '<a class="cg-b rev" href="' + esc(fl) + '" target="_blank" rel="noopener">REVIEW IT ›</a>' : '') + '</div>' +
      revHtml(rv) + '</div>';
  }

  function card(r) {
    var p = r.park, reg = r.reg;
    var prog = '<a class="p-pota" href="https://next.pota.app/park/' + p.c + '" target="_blank" rel="noopener">POTA ' + p.c + '</a>' +
      (p.kff || []).map(function (k) { return '<a class="p-kff" href="https://logsearch.wwff.co/directory/' + k + '" target="_blank" rel="noopener">WWFF ' + k + '</a>'; }).join('') +
      (p.sota || []).map(function (s) { var c = typeof s === 'string' ? s : (s.c || s[0]); return '<a class="p-sota" href="https://sotl.as/summits/' + c + '" target="_blank" rel="noopener">SOTA ' + esc(c) + '</a>'; }).join('') +
      (p.tf || []).map(function (t) { return '<a class="p-2fer" href="kpc-guide-pota.html#s-' + t + '">2-FER ' + t + '</a>'; }).join('');
    var co = String(p.co || ''), coL = /^multiple/i.test(co) ? 'Multiple counties' : /see official/i.test(co) ? co : co + (co.indexOf('/') >= 0 ? ' Counties' : ' County');
    var x = r.x, camp = x.campgrounds || [], lodge = x.lodging || [];
    var links = x.lodging_links || {};
    return '<article class="cg-card" id="park-' + p.c + '"><h2>' + esc(p.n) + '</h2><p class="cg-sub">' + esc(coL) + (reg ? ' • ' + esc(reg) : '') + '</p>' +
      '<div class="cg-prog">' + prog + '</div>' +
      '<div class="cg-btns">' + '<a class="cg-b" href="kpc-guide-pota.html#s-' + p.c + '">PARK GUIDE CARD</a><a class="cg-b" href="kpc-park-notes.html#' + p.c + '">PARK TIPS ›</a>' +
      (isFinite(p.la) ? ext(gps(p.la, p.lo), 'PARK GPS') + ext(wx(p.la, p.lo), 'WEATHER') : '') + '</div>' +
      (camp.length ? '<div class="cg-h">CAMPGROUNDS (' + camp.length + ')</div>' + camp.map(function (c) { return placeHtml(c, p, 'camp'); }).join('') : '') +
      (lodge.length ? '<div class="cg-h">CABINS, COTTAGES &amp; LODGES</div>' + lodge.map(function (c) { return placeHtml(c, p, 'lodge'); }).join('') :
        (links.cabins || links.resort ? '<div class="cg-h">CABINS &amp; LODGES</div><div class="cg-btns">' + ext(links.resort, 'RESORT / LODGE') + ext(links.cabins, 'CABINS') + '</div>' : '')) +
      (x.note ? '<p class="cg-note">' + esc(x.note) + '</p>' : '') +
      '<p class="cg-note">Checked ' + esc(nice((camp[0] || lodge[0] || {}).checked || C.updated)) + ' from the official pages. Call ahead: seasons and closures change.</p></article>';
  }

  function match(r) {
    var p = r.park, x = r.x, camp = x.campgrounds || [], lodge = x.lodging || [];
    if (F.camp && !camp.length) return false;
    if (F.lodge && !lodge.length && !(x.lodging_links && (x.lodging_links.cabins || x.lodging_links.resort))) return false;
    if (F.elec && !camp.some(function (c) { return /\belectric|\d+\s*-?\s*amp\b|full hookup/i.test(c.hookups || ''); })) return false;
    if (F.map && !camp.some(function (c) { return c.map; })) return false;
    if (F.kff && !(p.kff || []).length) return false;
    if (F.sota && !(p.sota || []).length) return false;
    if (F.open && !camp.concat(lodge).some(function (c) { return c.status !== 'closed'; })) return false;
    var reg = $('cgReg').value; if (reg && r.reg !== reg) return false;
    var q = $('cgQ').value.trim().toLowerCase();
    if (q) {
      var hay = [p.c, p.n, p.co, r.reg].concat(p.kff || [], (p.sota || []).map(function (s) { return typeof s === 'string' ? s : (s.c || s[0]); }),
        camp.map(function (c) { return c.name; }), lodge.map(function (c) { return c.name; })).join(' ').toLowerCase();
      if (q.split(/\s+/).some(function (w) { return hay.indexOf(w) < 0; })) return false;
    }
    return true;
  }
  function draw() {
    var list = ROWS.filter(match);
    $('cgList').innerHTML = list.map(card).join('');
    $('cgNone').hidden = !!list.length;
    var nc = list.reduce(function (a, r) { return a + (r.x.campgrounds || []).length; }, 0), nl = list.reduce(function (a, r) { return a + (r.x.lodging || []).length; }, 0);
    $('cgCount').textContent = list.length + ' PARKS • ' + nc + ' CAMPGROUNDS • ' + nl + ' CABIN / LODGE LISTINGS';
  }
  function drawOther() {
    var o = N.filter(function (n) { return !n.place; }), fl = formLink('', true);
    $('cgOtherBtn').innerHTML = fl ? '<a class="cg-b gold" href="' + esc(fl) + '" target="_blank" rel="noopener">REVIEW A PLACE OUTSIDE A PARK ›</a>' : '<p>Reviews open soon.</p>';
    var by = {};
    o.forEach(function (n) { var k = ((n.other && n.other.name) || 'Other').trim(); (by[k] = by[k] || []).push(n); });
    $('cgOther').innerHTML = Object.keys(by).sort().map(function (k) {
      var a = by[k][0].other || {};
      var g = a.gps && /^-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?$/.test(a.gps) ? gps.apply(null, a.gps.split(',').map(function (v) { return v.trim(); })) : '';
      return '<div class="cg-place"><h3 style="color:#fff">' + esc(k) + (a.type ? ' <span class="cg-kind">' + esc(a.type) + '</span>' : '') + '</h3>' + (a.where ? '<p>' + esc(a.where) + '</p>' : '') +
        (g || a.web ? '<div class="cg-btns">' + ext(a.web, 'WEBSITE', 'gold') + ext(g, 'GPS', 'gold') + '</div>' : '') +
        revHtml(by[k]).replace('<details class="cg-revs">', '<details class="cg-revs" open>') + '</div>';
    }).join('');
  }

  Promise.all([getJSON('kpc-ky-data.json'), getJSON('kpc-campgrounds.json'), getJSON('kpc-campground-notes.json', true), getJSON('kpc-campground-form.json', true)])
    .then(function (a) {
      D = a[0]; C = a[1]; N = (a[2] && a[2].notes) || []; FORM = a[3];
      var byC = {}; D.parks.forEach(function (p) { byC[p.c] = p; });
      ROWS = C.parks.filter(function (x) { return byC[x.pota]; }).map(function (x) {
        var p = byC[x.pota];
        return { park: p, x: x, reg: D.regions[String(p.co || '').split('/')[0].trim().toUpperCase()] || '' };
      }).sort(function (a, b) { return a.park.n < b.park.n ? -1 : 1; });
      var regs = {}; ROWS.forEach(function (r) { if (r.reg) regs[r.reg] = (regs[r.reg] || 0) + 1; });
      $('cgReg').innerHTML = '<option value="">All regions (' + ROWS.length + ')</option>' + Object.keys(regs).sort().map(function (k) { return '<option value="' + esc(k) + '">' + esc(k) + ' (' + regs[k] + ')</option>'; }).join('');
      $('cgTop').innerHTML = (C.closures ? '<div><b>CLOSURES &amp; RENOVATIONS</b>Kentucky State Parks lists lodges, cottages and campgrounds that are closed or being renovated on its Improvements page. Check it before you book; we mark what it said on the date shown on each card.<div class="cg-btns">' + ext(C.closures.url, 'STATE PARKS IMPROVEMENTS &amp; CLOSURES ↗', 'gold') + '</div></div>' : '') +
        (C.wmaRule ? '<div class="wma"><b>CAMPING ON WMAs</b>' + esc(C.wmaRule.text) + '<div class="cg-btns">' + ext(C.wmaRule.source, 'KDFWR PUBLIC LANDS RULES ↗') + '</div></div>' : '');
      draw(); drawOther();
      document.documentElement.dataset.ready = '1';
      if (location.hash) { var t = document.getElementById(location.hash.slice(1)); if (t) { var d = t.closest('details'); t.scrollIntoView(); } }
    }).catch(function (e) {
      $('cgErr').hidden = false; $('cgErr').textContent = 'Sorry, the list did not load (' + e.message + '). Try reloading the page.';
      document.documentElement.dataset.ready = '1';
    });
  $('cgQ').addEventListener('input', function () { if (ROWS.length) draw(); });
  $('cgReg').addEventListener('change', draw);
  $('cgChips').addEventListener('click', function (e) {
    var b = e.target.closest('.cg-chip'); if (!b) return;
    var k = b.dataset.f; F[k] = !F[k]; b.setAttribute('aria-pressed', String(!!F[k])); draw();
  });
})();
