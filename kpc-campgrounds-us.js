/* KPC Campgrounds & Cabins: every US state (kpc-campgrounds.html). Kentucky keeps its hand-checked view (kpc-campgrounds.js);
   this file adds the STATE picker and, for any other state, a parks list built from:
   - data/parkinfo/US-XX.json  parks {ref: [name, url, type, …, lat, lon, …]}
   - data/campfed/US-XX.json   federal campgrounds (recreation.gov): camps [[id, name, lat, lon, agency, reservable, url, kind c|s]]
   - data/campstate/US-XX.json state park campgrounds / cabins (built by a bot, official sources; optional, may not exist yet):
                               camps [[id, name, lat, lon, kind c|b|l, potaRef, officialUrl, reserveUrl]]
   - kpc-campground-notes.json member reviews + member-added places (note.st / note.ref when the bot sets them; otherwise the
                               park number in the place text, the GPS, or ", TN" in the town line).
   ?state=TN opens a state; the last pick is remembered (localStorage kpcCgSt). */
(function () {
  'use strict';
  /* Storage plan Step B (Oct 27): bot-rewritten data moved to KPC-Data; KPC.dataUrl (chat 1, every page's head) tries it first, then this site's copy */
  const MOVED = /^(data\/(wwff|world-bounds|pota|names|sota|canada-bounds|parkinfo|world-key|us-key|trails|access|ca-key|sota-land|leaders|campfed|campstate-manual|campstate|nwr|alerts)\/|locations(-ky)?\.json$|data\/(northam|canada|parkinfo-web|boundary-score|boundary-report|state-gis-found|access-layers|state-gis)\.json$)/;
  const dfetch = (u, o) => (MOVED.test(String(u)) && window.KPC && typeof KPC.dataUrl === 'function') ? KPC.dataUrl(u, o) : fetch(u, o);
  var $ = function (id) { return document.getElementById(id); };
  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function ext(href, text, cls) { return href ? '<a class="cg-b' + (cls ? ' ' + cls : '') + '" href="' + esc(href) + '" target="_blank" rel="noopener">' + text + '</a>' : ''; }
  function gps(la, lo) { return 'https://www.google.com/maps/search/?api=1&query=' + la + ',' + lo; }
  function dirs(la, lo) { return 'https://www.google.com/maps/dir/?api=1&destination=' + la + ',' + lo; }
  function wx(la, lo) { return 'https://weather.com/weather/today/l/' + la + ',' + lo; }
  function getJSON(u) { return dfetch(u, { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }); }
  function miles(a, b, c, d) { var R = 3958.8, r = Math.PI / 180, x = Math.sin((c - a) * r / 2), y = Math.sin((d - b) * r / 2); return 2 * R * Math.asin(Math.sqrt(x * x + Math.cos(a * r) * Math.cos(c * r) * y * y)); }
  function norm(s) { return String(s || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim(); }
  function stars(n) { n = Math.round(n * 2) / 2; var s = ''; for (var i = 1; i <= 5; i++) s += n >= i ? '★' : (n >= i - .5 ? '⯪' : '☆'); return s; }
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }

  var ST = { AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California', CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', DC: 'District of Columbia', FL: 'Florida',
    GA: 'Georgia', HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa', KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland', MA: 'Massachusetts',
    MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri', MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York',
    NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee',
    TX: 'Texas', UT: 'Utah', VT: 'Vermont', VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming' };
  var AG = { FS: 'FOREST SERVICE', NPS: 'NATIONAL PARK SERVICE', USACE: 'CORPS OF ENGINEERS', BLM: 'BLM', FWS: 'FISH & WILDLIFE', BOR: 'BUREAU OF RECLAMATION', TVA: 'TVA' };
  var KIND = { c: 'CAMPGROUND', b: 'CABIN', l: 'LODGE' };
  var PAGE = 25;

  var cur = 'KY', S = null, FORM = null, NOTES = null, SHAPES = null, shown = PAGE, Fu = { lodge: false, rev: false };

  function formLink(label, outside) {
    if (!FORM || !FORM.url) return '';
    var q = ['usp=pp_url'];
    if (FORM.kindEntry && (outside ? FORM.kindOutside : FORM.kindInside)) q.push(FORM.kindEntry + '=' + encodeURIComponent(outside ? FORM.kindOutside : FORM.kindInside));
    if (label && FORM.placeEntry && !outside && !/ · $/.test(label)) q.push(FORM.placeEntry + '=' + encodeURIComponent(label));
    var rm = /\b(US-\d{4,5})\b/.exec(label || ''), pe = outside ? FORM.nearEntry : FORM.parkEntry;   // the form's own Park number boxes
    if (rm && pe) q.push(pe + '=' + encodeURIComponent(rm[1]));
    return FORM.url + (FORM.url.indexOf('?') < 0 ? '?' : '&') + q.join('&');
  }

  /* ---- which state a member note belongs to ---- */
  function inPoly(x, y, ring) { var c = false; for (var i = 0, j = ring.length - 1; i < ring.length; j = i++) { var a = ring[i], b = ring[j]; if ((a[1] > y) !== (b[1] > y) && x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]) c = !c; } return c; }
  function stateAt(la, lo) {
    if (!SHAPES) return '';
    for (var i = 0; i < SHAPES.length; i++) { var s = SHAPES[i], P = s.p || []; for (var k = 0; k < P.length; k++) if (inPoly(lo, la, P[k][0] || [])) return s.a; }
    return '';
  }
  function noteGps(n) { var g = n.other && n.other.gps, m = /^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$/.exec(g || ''); return m ? [+m[1], +m[2]] : null; }
  function noteRef(n) { if (n.ref) return n.ref; var m = /\bUS-?0*(\d{1,5})\b/i.exec((n.other && n.other.name) || ''); return m ? 'US-' + ('000' + m[1]).slice(-4) : ''; }
  function noteName(n) { return String((n.other && n.other.name) || '').replace(/\bUS-?\d+\s*[·\-:|]*\s*/i, '').trim(); }
  function noteState(n, parks) {
    if (n.st) return n.st;
    var r = noteRef(n); if (r && parks[r]) return cur;
    var g = noteGps(n); if (g) return stateAt(g[0], g[1]);
    var w = (n.other && n.other.where) || '', m = /,\s*([A-Z]{2})\b/.exec(w); if (m && ST[m[1]]) return m[1];
    for (var k in ST) if (new RegExp('\\b' + ST[k] + '\\b', 'i').test(w)) return k;
    return '';
  }

  /* ---- build the state's rows ---- */
  function build(st, info, fed, sta) {
    var parks = (info && info.parks) || {}, list = [];
    Object.keys(parks).forEach(function (ref) {
      var a = parks[ref]; if (!isFinite(a[5]) || !isFinite(a[6])) return;
      list.push({ ref: ref, n: a[0], url: a[1], type: a[2], la: a[5], lo: a[6], places: [] });
    });
    var places = [];
    ((fed && fed.camps) || []).forEach(function (c) {
      if (c[7] && c[7] !== 'c') return;   // campgrounds only (shelters stay on the trip planner)
      places.push({ id: 'f' + c[0], name: c[1], la: c[2], lo: c[3], kind: 'c', src: 'fed', ag: c[4], book: c[6] });
    });
    ((sta && sta.camps) || []).forEach(function (c) {
      var dup = places.some(function (p) { return p.src === 'fed' && (norm(p.name) === norm(c[1]) || miles(p.la, p.lo, c[2], c[3]) < 0.19); });
      if (!dup) places.push({ id: 's' + c[0], name: c[1], la: c[2], lo: c[3], kind: c[4] || 'c', src: 'state', ref: c[5], web: c[6], book: c[7] });
    });
    /* data/campstate-manual (states with no bot list): ONE entry per PARK from the state's official listing, researched and not
       re-checked park by park: shown as park-level, never as a checked campground. Row [id, name, lat, lon, kind, parkRef, parksPage, reservePage, whatItHas] */
    var man = !(sta && sta.camps && sta.camps.length) && arguments[4];
    ((man && man.camps) || []).forEach(function (c) {
      if (c[9] === 'point') {   // an official GPS point from the state's own map layer (Oct 25, chat 2): a real campground / cabin spot
        var named = c[10] !== 'label only';
        places.push({ id: 'q' + c[0], name: named ? c[1] : (c[4] === 'b' ? 'Cabin' : 'Campground') + ' (official GPS point, name not given)', la: c[2], lo: c[3], kind: c[4] || 'c',
          src: 'statept', ref: c[5], web: c[6], book: c[7], detail: c[8], unnamed: !named, addr: /census geocoder/i.test(c[8] || '') });
        return;
      }
      places.push({ id: 'p' + c[0], name: c[1], la: c[2], lo: c[3], kind: c[4] || 'c', src: 'manual', ref: c[5], web: c[6], book: c[7], what: c[8] });
    });
    var extra = [];
    (NOTES || []).forEach(function (n) {
      if (n.place) return;   // a Kentucky place
      if (noteState(n, parks) !== st) return;
      var r = noteRef(n), g = noteGps(n), nm = noteName(n) || 'Member pick';
      var hit = places.filter(function (p) { return norm(p.name) === norm(nm) || (r && p.ref === r && norm(p.name).indexOf(norm(nm)) >= 0); })[0];
      if (hit) { (hit.rv = hit.rv || []).push(n); return; }
      var ex = extra.filter(function (p) { return norm(p.name) === norm(nm); })[0];
      if (ex) { ex.rv.push(n); return; }
      ex = { id: 'm' + n.id, name: nm, la: g ? g[0] : null, lo: g ? g[1] : null, kind: /cabin|cottage|lodge/i.test((n.other && n.other.type) || '') ? 'b' : 'c', src: 'member', ref: r,
        web: n.other && n.other.web, where: n.other && n.other.where, near: !!n.near, rv: [n] };
      extra.push(ex);
    });
    places = places.concat(extra);
    var AGT = { FS: /National (Forest|Grassland)/i, NPS: /National (Park|Monument|Recreation Area|Seashore|Lakeshore|Historical Park|Preserve|River)/i };
    places.forEach(function (x) {   // a Forest Service / Park Service campground belongs to the nearest forest / park of that kind (pins sit in the middle)
      var re = x.src === 'fed' && AGT[x.ag]; if (!re) return;
      var best = null, bd = 60;
      list.forEach(function (p) { if (!re.test(p.type || '')) return; var d = miles(p.la, p.lo, x.la, x.lo); if (d < bd) { bd = d; best = p; } });
      if (best) x.home = best.ref;
    });
    S = { st: st, parks: list, places: places, byRef: {}, hasState: !!(sta && sta.camps && sta.camps.length), hasManual: !!(man && man.camps && man.camps.length), fedN: ((fed && fed.camps) || []).filter(function (c) { return !c[7] || c[7] === 'c'; }).length };
    list.forEach(function (p) { S.byRef[p.ref] = p; });
  }
  function attach(radius) {
    S.parks.forEach(function (p) { p.places = []; });
    S.loose = [];
    S.places.forEach(function (x) {
      if (x.ref && S.byRef[x.ref]) { var p = S.byRef[x.ref], dd = isFinite(x.la) && x.la !== null ? miles(p.la, p.lo, x.la, x.lo) : NaN; p.places.push({ x: x, d: dd, own: !x.near, near: !!x.near }); return; }
      if (x.la === null || !isFinite(x.la)) { S.loose.push(x); return; }
      var any = false;
      if (x.home && S.byRef[x.home]) { var h = S.byRef[x.home]; h.places.push({ x: x, d: miles(h.la, h.lo, x.la, x.lo), home: true }); any = true; }
      S.parks.forEach(function (p) { if (p.ref === x.home) return; var d = miles(p.la, p.lo, x.la, x.lo); if (d <= radius) { p.places.push({ x: x, d: d }); any = true; } });
      if (!any && x.src === 'member') S.loose.push(x);
    });
    S.parks.forEach(function (p) { p.places.sort(function (a, b) { return ((b.own || b.home) ? 1 : 0) - ((a.own || a.home) ? 1 : 0) || a.d - b.d; }); });
  }

  /* ---- drawing ---- */
  function revHtml(list) {
    if (!list || !list.length) return '';
    var r = list.filter(function (n) { return n.rating; }), avg = r.length ? r.reduce(function (a, n) { return a + n.rating; }, 0) / r.length : 0;
    return '<details class="cg-revs"><summary>' + (avg ? '<span class="cg-stars">' + stars(avg) + '</span> ' + avg.toFixed(1) + ' • ' : '') + list.length + ' REVIEW' + (list.length > 1 ? 'S' : '') + '</summary>' +
      list.map(function (n) {
        return '<div class="cg-rev"><div class="who">' + esc(n.call) + (n.date ? ' • ' + esc(n.date) : '') + (n.rating ? ' • <span class="cg-stars">' + stars(n.rating) + '</span>' : '') + (n.site ? ' • site ' + esc(n.site) : '') + '</div>' +
          ((n.facts || []).length ? '<div class="facts">' + n.facts.map(function (x) { return '<span><b>' + esc(x[0]) + ':</b> ' + esc(x[1]) + '</span>'; }).join('') + '</div>' : '') +
          esc(n.text).replace(/\n/g, '<br>') + (n.photos || []).map(function (p) { return '<img src="' + esc(p) + '" alt="Photo from ' + esc(n.call) + '" loading="lazy">'; }).join('') + '</div>';
      }).join('') + '</details>';
  }
  function srcTag(x) {
    if (x.src === 'fed') return '<span class="cgu-src fed">FEDERAL · ' + esc(AG[x.ag] || x.ag || 'RECREATION.GOV') + '</span>';
    if (x.src === 'state') return '<span class="cgu-src st">STATE PARKS · OFFICIAL</span>';
    if (x.src === 'statept') return x.addr ? '<span class="cgu-src pk">FROM THE PARK’S STREET ADDRESS</span>' : '<span class="cgu-src st">STATE PARKS · OFFICIAL GPS</span>';
    if (x.src === 'manual') return '<span class="cgu-src pk">PARK-LEVEL · FROM THE STATE’S OFFICIAL LISTING</span>';
    return '<span class="cgu-src mem">MEMBER ADDED</span>';
  }
  function placeHtml(o, p) {
    if (o.x.src === 'manual') return manHtml(o, p);
    var x = o.x, lab = (p ? p.ref + ' · ' : '') + x.name, fl = formLink(lab);
    var mi = isFinite(o.d) ? (o.d < 1 ? 'under 1 mi' : Math.round(o.d) + ' mi') + ' from the park pin' : '';
    var dist = !p ? '' : x.src === 'statept' ? 'in this park' + (mi ? ' · ' + mi : '') : o.near ? 'near this park' + (mi ? ' · ' + mi : '') : o.own ? 'at the park' : o.home ? 'in this ' + (/forest|grassland/i.test(p.type || '') ? 'forest' : 'park') + (mi ? ' · ' + mi : '') : mi;
    var nm = x.unnamed ? (x.kind === 'b' ? 'Cabin' : 'Campground') + (o.no ? ' ' + o.no : '') + ' (official GPS point, name not given)' : x.name;
    return '<div class="cg-place"><h3>' + (x.kind !== 'c' ? '<span class="cg-kind">' + KIND[x.kind] + '</span>' : '') + esc(nm) + '</h3>' +
      '<p class="cgu-meta">' + srcTag(x) + (dist ? ' <span>' + esc(dist) + '</span>' : '') + (x.where ? ' <span>' + esc(x.where) + '</span>' : '') + '</p>' +
      (x.src === 'statept' && x.addr ? '<p class="cg-note">Placed from the park’s street address' + (/\(([^)]+)\)/.test(x.detail || '') ? ' (' + esc(/\(([^)]+)\)/.exec(x.detail)[1]) + ')' : '') + ', not a GPS point: the campground itself may be some way in. Check the park’s map.</p>' : '') +
      (x.src === 'statept' && x.unnamed ? '<p class="cg-note">The state’s map marks a ' + (x.kind === 'b' ? 'cabin' : 'campground') + ' here but gives no name: check the state’s page.</p>' : '') +
      '<div class="cg-btns">' + (isFinite(x.la) && x.la !== null ? ext(dirs(x.la, x.lo), 'DIRECTIONS ›', 'gold') : '') + ext(x.web, x.src === 'statept' ? 'STATE PARKS PAGE' : 'OFFICIAL PAGE') + ext(x.book, x.src === 'fed' ? 'RECREATION.GOV ›' : 'RESERVE ›', 'dark') +
      (isFinite(x.la) && x.la !== null ? ext(gps(x.la, x.lo), 'GPS') : '') + (fl ? '<a class="cg-b rev" href="' + esc(fl) + '" target="_blank" rel="noopener">RATE IT ›</a>' : '') + '</div>' +
      revHtml(x.rv) + '</div>';
  }
  function manHtml(o, p) {   // park-level camping line (not a single campground, not checked by us)
    var x = o.x, fl = formLink((p ? p.ref : x.ref) + ' · ' + x.name);
    return '<div class="cg-place cgu-man"><h3>Camping at this park' + (x.what ? ': <span>' + esc(x.what) + '</span>' : '') + '</h3>' +
      '<p class="cgu-meta">' + srcTag(x) + '</p>' +
      '<p class="cg-note">The state lists camping at this park. Not checked site by site: see the state’s page for campgrounds, cabins and open dates before you go.</p>' +
      '<div class="cg-btns">' + ext(x.web, 'STATE PARKS PAGE') + ext(x.book, 'RESERVE ›', 'dark') + (fl ? '<a class="cg-b rev" href="' + esc(fl) + '" target="_blank" rel="noopener">RATE IT ›</a>' : '') + '</div>' +
      revHtml(x.rv) + '</div>';
  }
  function card(p) {
    var add = formLink(p.ref + ' · '), near = formLink(p.ref, true);
    var ms = p.places.filter(function (o) { return o.x.src === 'manual'; }), rest = p.places.filter(function (o) { return o.x.src !== 'manual'; });
    var cs = rest.filter(function (o) { return o.x.kind === 'c'; }), ls = rest.filter(function (o) { return o.x.kind !== 'c'; });
    [cs, ls].forEach(function (L) { var u = L.filter(function (o) { return o.x.unnamed; }); u.forEach(function (o, i) { o.no = u.length > 1 ? i + 1 : 0; }); });
    return '<article class="cg-card" id="park-' + esc(p.ref) + '"><h2>' + esc(p.n) + '</h2><p class="cg-sub">' + esc(p.type || 'Park') + ' • ' + esc(ST[S.st]) + '</p><div data-clos="' + esc(p.ref) + '"></div>' +
      '<div class="cg-prog"><a class="p-pota" href="https://next.pota.app/park/' + esc(p.ref) + '" target="_blank" rel="noopener">POTA ' + esc(p.ref) + '</a></div>' +
      '<div class="cg-btns">' + ext(p.url, 'OFFICIAL PARK PAGE') + '<a class="cg-b" href="kpc-park-notes-us.html?ref=' + esc(p.ref) + '">PARK TIPS ›</a>' + ext(gps(p.la, p.lo), 'PARK GPS') + ext(wx(p.la, p.lo), 'WEATHER') + '</div>' +
      (ms.length ? '<div class="cg-h">STATE PARK CAMPING</div>' + ms.map(function (o) { return placeHtml(o, p); }).join('') : '') +
      (cs.length ? '<div class="cg-h">CAMPGROUNDS (' + cs.length + ')</div>' + cs.map(function (o) { return placeHtml(o, p); }).join('') : '') +
      (ls.length ? '<div class="cg-h">CABINS &amp; LODGES (' + ls.length + ')</div>' + ls.map(function (o) { return placeHtml(o, p); }).join('') : '') +
      (!p.places.length ? '<p class="cg-note">Nothing listed yet within this distance. Try a wider distance, or add one you know.</p>' : '') +
      (add ? '<div class="cg-btns"><a class="cg-b gold" href="' + esc(add) + '" target="_blank" rel="noopener">＋ ADD ONE IN THIS PARK</a>' +
        (near ? '<a class="cg-b gold" href="' + esc(near) + '" target="_blank" rel="noopener">＋ ADD ONE NEAR THIS PARK</a>' : '') + '</div>' : '') + '</article>';
  }
  function match(p) {
    var pk = $('cguPark').value; if (pk) return p.ref === pk;
    if (!p.places.length) return false;
    if (Fu.lodge && !p.places.some(function (o) { return o.x.kind !== 'c'; })) return false;
    if (Fu.rev && !p.places.some(function (o) { return o.x.rv && o.x.rv.length; })) return false;
    var q = $('cgQ').value.trim().toLowerCase();
    if (q) { var hay = [p.ref, p.n, p.type].concat(p.places.map(function (o) { return o.x.name; })).join(' ').toLowerCase(); if (q.split(/\s+/).some(function (w) { return hay.indexOf(w) < 0; })) return false; }
    return true;
  }
  function parkSelect() {
    var sel = $('cguPark'), keep = sel.value, withP = S.parks.filter(function (p) { return p.places.length; }).sort(function (a, b) { return a.n < b.n ? -1 : 1; });
    sel.innerHTML = '<option value="">All ' + withP.length + ' parks with a place to stay</option>' + withP.map(function (p) { return '<option value="' + esc(p.ref) + '">' + esc(p.n) + ' (' + p.places.length + ')</option>'; }).join('');
    if (keep && S.byRef[keep]) { if (!withP.some(function (p) { return p.ref === keep; })) sel.insertAdjacentHTML('beforeend', '<option value="' + esc(keep) + '">' + esc(S.byRef[keep].n) + ' (0)</option>'); sel.value = keep; }
  }
  function draw() {
    if (!S) return;
    var list = S.parks.filter(match).sort(function (a, b) { return a.n < b.n ? -1 : 1; });
    var nPl = {}; list.forEach(function (p) { p.places.forEach(function (o) { nPl[o.x.id] = 1; }); });
    $('cguList').innerHTML = list.slice(0, shown).map(card).join('') +
      (list.length > shown ? '<div class="cg-btns cgu-more"><button type="button" class="cg-b gold" id="cguMore">SHOW ' + Math.min(PAGE, list.length - shown) + ' MORE PARKS (' + (list.length - shown) + ' left)</button></div>' : '');
    $('cguNone').hidden = !!list.length;
    $('cguCount').textContent = list.length + ' PARK' + (list.length === 1 ? '' : 'S') + ' • ' + Object.keys(nPl).length + ' PLACE' + (Object.keys(nPl).length === 1 ? '' : 'S') + ' TO STAY';
    var m = $('cguMore'); if (m) m.onclick = function () { shown += PAGE; draw(); };
    if (window.KPCClos) $('cguList').querySelectorAll('[data-clos]').forEach(function (el) {   // Oct 25 (HQ): the park's current closures (cards only show them when there are some)
      KPCClos.html(el.getAttribute('data-clos'), S.st, { quiet: true }).then(function (h) { el.innerHTML = h; }).catch(function () {}); });
    var lo = S.loose.filter(function (x) { return x.src === 'member'; });
    $('cguLoose').innerHTML = lo.length ? '<h2>Member picks in ' + esc(ST[S.st]) + '</h2><p class="cg-note">Added by members, not tied to a park on this list yet.</p>' + lo.map(function (x) { return placeHtml({ x: x }, null); }).join('') : '';
  }
  /* Oct 30 (HQ 11:12 AM): outside KY say when the camping files were last read (the oldest 'updated' of the files used) */
  function chkDate(files) {
    var d = files.map(function (x) { return x && /^\d{4}-\d{2}-\d{2}/.test(x.updated || '') ? x.updated.slice(0, 10) : ''; }).filter(Boolean).sort()[0];
    if (!d) return '';
    var m = d.split('-'); return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][+m[1] - 1] + ' ' + (+m[2]) + ', ' + m[0];
  }
  function head() {
    var add = formLink('', true), o = SRC[S.st] || {};
    var links = ext(o.parks, 'STATE PARKS ↗', 'gold') + (o.reserve_ok !== false ? ext(o.reserve, 'STATE PARK RESERVATIONS ↗', 'gold') : '');
    $('cguHead').innerHTML = '<b>' + esc(ST[S.st].toUpperCase()) + '</b>' +
      (S.hasState ? 'State park campgrounds and cabins from ' + esc(ST[S.st]) + '’s official data (may not be complete), federal campgrounds from recreation.gov, ' :
        S.hasManual ? 'State park campgrounds from ' + esc(ST[S.st]) + '’s own map points where the state publishes them (tagged OFFICIAL GPS); other parks are listed park by park from the state’s official listing (not checked site by site: confirm on the state’s page). Also federal campgrounds (recreation.gov) ' :
        'State park campgrounds for ' + esc(ST[S.st]) + ' are not listed here yet: use the state’s own pages below. Listed now: federal campgrounds (Forest Service, National Park Service, Corps of Engineers and more, from recreation.gov) ') +
      'and places members have added. Forest Service and Park Service campgrounds sit under their own forest or park; the rest are matched by distance from each park’s map pin.' +
      '<span class="cgu-clos"><b>Camping info last checked ' + esc(S.chk || 'recently') + '.</b> Check the agency’s page before you go.</span>' + (links ? '<div class="cg-btns">' + links + '</div>' : '') +
      (add ? '<div class="cg-btns"><a class="cg-b gold" href="' + esc(add) + '" target="_blank" rel="noopener">＋ ADD A CAMPGROUND OR CABIN WE ARE MISSING</a></div>' : '');
  }

  function closCover() {   // which closure sources we watch for this state (data/alerts/us-parks.json via kpc-closures.js)
    var el = $('cguClosCov'); if (!el || !window.KPCClos) return;
    KPCClos.get('', S.st).then(function (r) {
      el.innerHTML = '<span class="cgu-clos">' + (r.cover.length ? '<b>Closures:</b> we check ' + esc(r.cover.map(function (x) { return x.agency; }).join(', ')) + ' every 6 hours; notices show on the park cards. Other managers are not watched.'
        : '<b>Closures:</b> we do not watch closures in ' + esc(ST[S.st]) + ' yet, so no notice does NOT mean open. Check the state’s page before you go.') + '</span>';
    });
  }
  function setMode(st) {
    cur = st; store('kpcCgSt', st); if ($('cgpName')) $('cgpName').textContent = ST[st] || st; if ($('cgSt') && $('cgSt').value !== st) $('cgSt').value = st;
    var u = new URL(location.href); if (st === 'KY') u.searchParams.delete('state'); else u.searchParams.set('state', st);
    history.replaceState(null, '', u.pathname + u.search + u.hash);
    document.documentElement.classList.toggle('cg-us', st !== 'KY');
    $('cgQ').placeholder = st === 'KY' ? 'Search park, campground, county, US- / KFF- / W4K…' : 'Search park or campground name, or a US- number…';
    if (st === 'KY') return;
    $('cguList').innerHTML = ''; $('cguCount').textContent = 'Loading ' + ST[st] + '…'; $('cguHead').innerHTML = ''; $('cguLoose').innerHTML = '';
    var want = st;
    ready.then(function () {
      var has = IDX && IDX.states && IDX.states[st], hm = !has && MIDX && MIDX.states && MIDX.states[st];
      return Promise.all([getJSON('data/parkinfo/US-' + st + '.json'), getJSON('data/campfed/US-' + st + '.json'), has ? getJSON('data/campstate/US-' + st + '.json') : null, null, hm ? getJSON('data/campstate-manual/US-' + st + '.json') : null]);
    }).then(function (a) {
      if (cur !== want) return;
      build(st, a[0], a[1], a[2], a[4]); S.chk = chkDate([a[1], a[2], a[4]]); shown = PAGE; $('cguPark').value = '';
      attach(+$('cguRad').value); parkSelect(); head(); draw();   /* Oct 30: no closures line outside KY (scope rule) */
    });
  }

  var IDX = null, SRC = {}, MIDX = null;   // + data/campstate-manual/index.json (park-level lists for states the bot has none for)   // data/campstate/index.json (which states have a state-park list) + data/campstate-sources.json (official links)
  var ready = Promise.all([getJSON('kpc-campground-form.json'), getJSON('kpc-campground-notes.json'), getJSON('kpc-us-states.json'), getJSON('data/campstate/index.json'), getJSON('data/campstate-sources.json'), getJSON('data/campstate-manual/index.json')]).then(function (a) {
    FORM = a[0]; NOTES = (a[1] && a[1].notes) || []; SHAPES = a[2]; IDX = a[3] || {}; SRC = (a[4] && a[4].states) || {}; MIDX = a[5] || {};
  });

  /* ---- controls ---- */
  var row = document.querySelector('.cg-row');
  /* Oct 26 (HQ/Brandon: 'the state picker is too hidden; people don't realize they can see other states'): a big 📍 PICK A STATE bar
     right under the hero, a 'Campgrounds & cabins in <state> · change state ▾' heading, and 📍 NEAR ME (the visitor's state from the GPS). */
  /* HQ + Brandon Oct 29 8:38 AM (scope rule, MASTER-PLAN 3.4): campground data outside Kentucky is HIDDEN (files kept). KY_ONLY = true
     shows Kentucky only: no state picker, no NEAR ME, ?state= ignored. Set it to false to bring the other states back. */
  var KY_ONLY = false;   /* Brandon Oct 30 11:05 + 11:10 AM: camping for every US state shown again (camping only; hours / fees / closures outside KY stay hidden) */
  var hero = document.querySelector('main .hero') || document.querySelector('.hero');
  var bar = '<section class="cgp" id="cgPick" data-keep-light aria-label="Pick a state"><div class="cg-wrap">' +
    '<h2 class="cgp-h">Campgrounds &amp; cabins in <b id="cgpName">Kentucky</b> <button type="button" class="cgp-chg" id="cgpChange">· change state ▾</button></h2>' +
    '<div class="cgp-row"><label class="cgp-l" for="cgSt">📍 PICK A STATE</label><select id="cgSt">' + Object.keys(ST).sort(function (a, b) { return ST[a] < ST[b] ? -1 : 1; }).map(function (k) {
      return '<option value="' + k + '">' + esc(ST[k]) + (k === 'KY' ? ' (checked by club members)' : '') + '</option>'; }).join('') + '</select>' +
    '<button type="button" class="cgp-near" id="cgpNear">📍 NEAR ME</button></div><p class="cgp-msg" id="cgpMsg" aria-live="polite">Every US state is here. Kentucky: checked by club members<span id="cgpKyD"></span>; other states come from the agencies’ official lists.</p></div></section>';
    /* Oct 28 (chat 8 / Brandon): say who checked Kentucky and when (kpc-campgrounds.json 'updated') */
    getJSON('kpc-campgrounds.json').then(function (d) { var m = d && /^(\d{4})-(\d{2})-(\d{2})/.exec(d.updated || ''), e = document.getElementById('cgpKyD'); if (m && e) e.textContent = ', last checked ' + ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][+m[2] - 1] + ' ' + (+m[3]) + ', ' + m[1]; });
  if (hero) hero.insertAdjacentHTML('afterend', bar); else row.insertAdjacentHTML('beforebegin', bar);
  if (KY_ONLY) { var pr = document.querySelector('#cgPick .cgp-row'); if (pr) pr.hidden = true; $('cgpChange').hidden = true; $('cgpMsg').innerHTML = 'Kentucky parks: checked by club members<span id="cgpKyD"></span>.'; }
  row.insertAdjacentHTML('beforeend', '<select id="cguPark" aria-label="Park" class="cgu-only"><option value="">All parks</option></select>' +
    '<select id="cguRad" aria-label="How far from the park" class="cgu-only"><option value="2">At the park (2 mi)</option><option value="10" selected>Park + 10 mi around</option><option value="25">Park + 25 mi around</option><option value="50">Park + 50 mi around</option></select>');
  $('cgChips').insertAdjacentHTML('afterend', '<div class="cg-chips cgu-only" id="cguChips"><button class="cg-chip" type="button" data-u="lodge" aria-pressed="false">CABINS &amp; LODGES</button><button class="cg-chip" type="button" data-u="rev" aria-pressed="false">★ HAS REVIEWS</button></div>' +
    '<div class="cg-count cgu-only" id="cguCount" aria-live="polite"></div>');
  $('cgList').parentNode.insertAdjacentHTML('afterend', '<div class="cg-wrap cgu-only"><div class="cg-top cgu-head" id="cguHead"></div><div class="cg-list" id="cguList"></div>' +
    '<p class="cg-none" id="cguNone" hidden>Nothing matches. Try a wider distance, a shorter search, or another park.</p><div id="cguLoose" class="cgu-loose"></div></div>');

  $('cgSt').addEventListener('change', function () { setMode(this.value); $('cgpMsg').textContent = 'Showing ' + ST[this.value] + '. Your pick is remembered on this device.'; });
  $('cgpChange').addEventListener('click', function () { var s2 = $('cgSt'); s2.focus(); try { if (s2.showPicker) s2.showPicker(); } catch (e) {} });
  $('cgpNear').addEventListener('click', function () {
    var m = $('cgpMsg'); if (!navigator.geolocation) { m.textContent = 'This browser can’t share your location: pick your state from the list.'; return; }
    m.textContent = 'Finding your state…';
    navigator.geolocation.getCurrentPosition(function (p) {
      ready.then(function () { var st = stateAt(p.coords.latitude, p.coords.longitude);
        if (!st || !ST[st]) { m.textContent = 'You look to be outside the US states we cover: pick a state from the list.'; return; }
        $('cgSt').value = st; setMode(st); m.textContent = 'You are in ' + ST[st] + '. Showing ' + ST[st] + ' (remembered on this device).'; });
    }, function () { m.textContent = 'Location not shared, so pick your state from the list.'; }, { timeout: 12000, maximumAge: 600000 });
  });
  $('cguPark').addEventListener('change', function () { shown = PAGE; draw(); var c = this.value && document.getElementById('park-' + this.value); if (c) c.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
  $('cguRad').addEventListener('change', function () { if (!S) return; attach(+this.value); parkSelect(); shown = PAGE; draw(); });
  $('cguChips').addEventListener('click', function (e) { var b = e.target.closest('.cg-chip'); if (!b) return; var k = b.dataset.u; Fu[k] = !Fu[k]; b.setAttribute('aria-pressed', String(Fu[k])); shown = PAGE; draw(); });
  $('cgQ').addEventListener('input', function () { if (cur !== 'KY') { shown = PAGE; draw(); } });

  var q = (new URLSearchParams(location.search).get('state') || '').toUpperCase(), first = KY_ONLY ? 'KY' : ST[q] ? q : (ST[store('kpcCgSt')] ? store('kpcCgSt') : 'KY');
  $('cgSt').value = first;
  if (first !== 'KY') setMode(first);
})();
