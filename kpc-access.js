/* KPC Parking & Access Finder, rebuilt Oct 26 2026 (chat 3; Brandon Oct 25: 'it only uses open source, how do we improve it').
   OFFICIAL POINTS FIRST:
   - Kentucky: kpc-ky-data.json parks[].ap [[lat, lon, label]] (KDFWR, Kentucky State Parks, NPS, Forest Service… points),
     official-park-access.json (state park trailheads from the park pages), kpc-ky-facilities.json trailheads with parking.
   - Other states: data/access/US-XX.json {parks: {ref: [[lat, lon, label]]}} (chat 2's US access bot, agency parking /
     entrance / gate / ramp points; the agency is in the label's brackets).
   - OpenStreetMap ONLY when asked (＋ FILL IN), tagged VOLUNTEER MAP.
   Each point: who it came from, inside the park line or N mi outside it (kpc-bounds.js outline: KY layers / US key /
   PAD-US), DIRECTIONS. Closures beside it (kpc-closures.js). Coverage line per state from the data.
   ?ref=US-1234 opens a park; ?state=TN picks a state (remembered: localStorage kpcAfSt). */
(function () {
  'use strict';
  /* Storage plan Step B (Oct 27): bot-rewritten data moved to KPC-Data; KPC.dataUrl (chat 1, every page's head) tries it first, then this site's copy */
  const MOVED = /^(data\/(wwff|world-bounds|pota|names|sota|canada-bounds|parkinfo|world-key|us-key|trails|access|ca-key|sota-land|leaders|campfed|campstate-manual|campstate|nwr|alerts)\/|locations(-ky)?\.json$|data\/(northam|canada|parkinfo-web|boundary-score|boundary-report|state-gis-found|access-layers|state-gis)\.json$)/;
  const dfetch = (u, o) => (MOVED.test(String(u)) && window.KPC && typeof KPC.dataUrl === 'function') ? KPC.dataUrl(u, o) : fetch(u, o);
  const $ = id => document.getElementById(id), B = () => window.KPCB;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const j = u => dfetch(u, { cache: 'no-cache' }).then(r => r.ok ? r.json() : null).catch(() => null);
  const mi = (a, b, c, d) => { const r = Math.PI / 180, x = Math.sin((c - a) * r / 2), y = Math.sin((d - b) * r / 2); return 2 * 3958.8 * Math.asin(Math.sqrt(x * x + Math.cos(a * r) * Math.cos(c * r) * y * y)); };
  const dir = (la, lo) => 'https://www.google.com/maps/dir/?api=1&destination=' + la + ',' + lo;
  const store = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } };
  const ST = { AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California', CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', DC: 'District of Columbia', FL: 'Florida',
    GA: 'Georgia', HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa', KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland', MA: 'Massachusetts',
    MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri', MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York',
    NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee',
    TX: 'Texas', UT: 'Utah', VT: 'Vermont', VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming' };
  /* Oct 27 (HQ: 'US + CANADA · KENTUCKY MOST COMPLETE'): Canada's provinces too, keyed CA-XX (California stays CA):
     parks from data/parkinfo/CA.json (province in field 10), official points from data/access/CA-XX.json. */
  const PROV = { AB: 'Alberta', BC: 'British Columbia', MB: 'Manitoba', NB: 'New Brunswick', NL: 'Newfoundland and Labrador', NS: 'Nova Scotia', NT: 'Northwest Territories', NU: 'Nunavut', ON: 'Ontario', PE: 'Prince Edward Island', QC: 'Quebec', SK: 'Saskatchewan', YT: 'Yukon' };
  Object.keys(PROV).forEach(k => { ST['CA-' + k] = PROV[k]; });
  const isCA = st => /^CA-/.test(st || '');
  const accUrl = st => 'data/access/' + (isCA(st) ? st : 'US-' + st) + '.json';
  let CAJ = null; const caInfo = () => CAJ || (CAJ = j('data/parkinfo/CA.json'));
  const KINDS = [['parking', '🅿', 'Parking', /parking|\blot\b|pull-?off|lay-?by/i], ['entrance', '🚪', 'Entrances', /entrance|entry|\baccess point\b/i], ['gate', '🚧', 'Gates', /\bgate/i],
    ['trailhead', '🥾', 'Trailheads', /trail/i], ['ramp', '🛶', 'Boat ramps', /boat|ramp|launch|carry|canoe|kayak|slipway|paddl/i], ['other', '📍', 'Other', /./]];
  const kindOf = t => (KINDS.find(k => k[3].test(t || '')) || KINDS[5])[0];
  const KI = Object.fromEntries(KINDS.map(k => [k[0], k]));
  /* HQ Oct 27 5:33 PM: chat 2's points carry HOW they were tied to the park (4th field 'name' = the agency's layer names the park,
     'place' = it only sits on/near the park's land). A place-only point is 'Nearby public access, not the park's own', never a park entrance. */
  const NEARTXT = 'Nearby public access, not the park\u2019s own';
  const nearLab = l => NEARTXT + ': ' + String(l || 'access point').replace(/\b(park\s+)?entrances?\b/ig, 'access').replace(/^\w/, c => c.toLowerCase());
  /* who the point came from: '(Tennessee Wildlife Resources Agency)' / '(TWRA; all managers)' / 'KDFWR boat ramp: …' / 'NPS parking lot' */
  function srcOf(label, ky) {
    const m = /\(([^()]+)\)\s*$/.exec(label || ''), part = m ? m[1].split(';')[0].replace(/\s+(asset (inventory|management data)|EGIS.*|GIS Bureau|Facilities Parking Area)$/i, '').trim() : '';
    if (part && !/^(\d+\s*m\b|n\/a|work in progress|pavement|field data|\d{4}|approx|outside|inside|statewide|one \d)/i.test(part)) return part;
    const a = /^(KDFWR|NPS|USFS|Forest Service|USACE|Corps|TVA|FWS|USFWS|BLM|Kentucky State Parks|KSP|KY State Parks|State Parks|KNP|OSM)\b/i.exec(label || '');
    if (a) return { KSP: 'Kentucky State Parks', 'KY STATE PARKS': 'Kentucky State Parks', USFS: 'Forest Service', CORPS: 'Corps of Engineers', USACE: 'Corps of Engineers', FWS: 'Fish & Wildlife Service', USFWS: 'Fish & Wildlife Service', KNP: 'Kentucky Nature Preserves' }[a[1].toUpperCase()] || a[1];
    return ky ? 'Kentucky official map' : (ST[cur && cur.st] || 'State') + ' official map';
  }
  const clean = l => String(l || '').replace(/\s*\(([^()]+)\)\s*$/, m => /outside the line|\d+ m\)/.test(m) ? '' : '').replace(/^(KDFWR|NPS)\s+/, '').replace(/^\w/, c => c.toUpperCase()) || 'Access point';

  let D = null, KYX = null, KYF = null, LIST = [], cur = null, map = null, gOut = null, gPts = null, OFF = {};
  const ACC = {};   // data/access/US-XX.json cache

  /* ---------- state + park lists ---------- */
  async function loadState(st) {
    store('kpcAfSt', st);
    $('afPk').innerHTML = '<option value="">Loading parks…</option>'; $('afCov').textContent = '';
    if (st === 'KY') {
      D = D || await j('kpc-ky-data.json');
      LIST = ((D && D.parks) || []).map(p => ({ ref: p.c, n: p.n, la: p.la, lo: p.lo, n_ap: (p.ap || []).length, st: 'KY' }));
    } else {
      const [I, A] = await Promise.all([isCA(st) ? caInfo() : j('data/parkinfo/US-' + st + '.json'), ACC[st] || (ACC[st] = j(accUrl(st)))]);
      const ap = (A && A.parks) || {};
      LIST = Object.entries((I && I.parks) || {}).filter(([ref, a]) => !isCA(st) || a[10] === st.slice(3)).map(([ref, a]) => ({ ref, n: a[0], web: a[1], type: a[2], la: a[5], lo: a[6], n_ap: (ap[ref] || []).length, st }));
    }
    LIST.sort((a, b) => a.n < b.n ? -1 : 1);
    const withP = LIST.filter(p => p.n_ap), name = ST[st];
    $('afCov').innerHTML = st === 'KY'
      ? '<b>Kentucky:</b> official parking or access points for ' + withP.length + ' of ' + LIST.length + ' parks.'
      : withP.length ? '<b>' + esc(name) + ':</b> official parking for ' + withP.length + ' of ' + LIST.length + ' parks; the rest use the volunteer map.'
        : '<b>' + esc(name) + ':</b> no official parking points yet; use the volunteer map (＋ FILL IN after you pick a park).';
    $('afPk').innerHTML = '<option value="">Pick a park (' + LIST.length + ')</option>' +
      (withP.length ? '<optgroup label="With official points">' + withP.map(p => '<option value="' + esc(p.ref) + '">' + esc(p.n) + ' (' + p.n_ap + ')</option>').join('') + '</optgroup>' : '') +
      (LIST.length > withP.length ? '<optgroup label="Volunteer map only">' + LIST.filter(p => !p.n_ap).map(p => '<option value="' + esc(p.ref) + '">' + esc(p.n) + '</option>').join('') + '</optgroup>' : '');
  }

  /* ---------- official points for one park ---------- */
  async function officialPoints(p) {
    const out = [], add = (la, lo, label, src, kind, how) => { if (!isFinite(la) || !isFinite(lo)) return; if (out.some(x => mi(x.la, x.lo, la, lo) < 0.02)) return; let k = kind || kindOf(label); const near = how === 'place'; if (near && k === 'entrance') k = 'other'; out.push({ la: +la, lo: +lo, label: near ? nearLab(label) : label, src, kind: k, near, osm: false }); };
    if (p.st === 'KY') {
      D = D || await j('kpc-ky-data.json'); KYX = KYX || await j('official-park-access.json'); KYF = KYF || await j('kpc-ky-facilities.json');
      const k = ((D && D.parks) || []).find(x => x.c === p.ref);
      ((k && k.ap) || []).forEach(a => add(a[0], a[1], clean(a[2]), srcOf(a[2], true)));
      const x = KYX && KYX[p.ref]; ((x && x.trailheads) || []).forEach(t => add(t.lat, t.lon, 'Trailhead: ' + t.name, 'Kentucky State Parks', 'trailhead'));
      const f = KYF && KYF.parks && KYF.parks[p.ref]; ((f && f.th) || []).filter(t => t[4]).forEach(t => add(t[0], t[1], 'Trailhead: ' + (t[3] || t[2]) + (t[5] ? ' (restrooms)' : ''), 'Kentucky State Parks', 'trailhead'));
    } else {
      const A = await (ACC[p.st] || (ACC[p.st] = j(accUrl(p.st))));
      ((A && A.parks && A.parks[p.ref]) || []).forEach(a => add(a[0], a[1], clean(a[2]), srcOf(a[2], false), null, a[3]));
    }
    return out;
  }

  /* ---------- outline + inside / outside ---------- */
  async function outline(p) {
    const b = B(); if (!b) return { fs: [], label: 'none' };
    try {
      if (p.st === 'KY') { const fs = await b.kyFor(p.ref); if (fs && fs.length) return { fs, label: 'official', src: 'Kentucky official maps' }; }
      if (isCA(p.st) || /^CA-\d/.test(p.ref)) { const fs = b.canada ? await b.canada(p.ref) : []; return fs.length ? { fs, label: fs.some(f => f._approx) ? 'approx' : 'official', why: (fs.find(f => f._why) || {})._why || '', src: [...new Set(fs.map(f => f._src))].join(' + ') } : { fs: [], label: 'none' }; }
      if (b.usOutline) return await b.usOutline(p.ref, p.short || p.n, p.la, p.lo, [p.st].filter(Boolean));
    } catch (e) {}
    return { fs: [], label: 'none' };
  }
  function where(pt, fs) {
    const b = B(); if (!b || !fs.length) return { t: '', km: null };
    if (fs.some(f => f.geometry && b.inside(pt.la, pt.lo, f.geometry))) return { t: 'inside the park line', km: 0 };
    let best = Infinity; fs.forEach(f => { if (f.geometry) { const e = b.edge(pt.la, pt.lo, f.geometry); if (e.km < best) best = e.km; } });
    const m = best * 0.621371;
    return isFinite(m) ? { t: m < 0.1 ? 'right at the park line' : (m < 1 ? m.toFixed(1) : Math.round(m)) + ' mi outside the park line', km: best } : { t: '', km: null };
  }

  /* ---------- open a park ---------- */
  async function open(ref, from) {
    $('afMsg').textContent = 'Loading ' + ref + '…'; $('afNearL').innerHTML = '';
    let p = LIST.find(x => x.ref === ref);
    if (!p || from === 'search') {
      let o = null; try { o = B() && await B().lookup(ref); } catch (e) {}
      if (!o && !p) { $('afMsg').textContent = 'Could not find ' + ref + '. Check the number (the lookup needs a signal).'; return; }
      if (o) {
        let cst = '';
        if (o.prog === 'POTA' && /^CA-\d/.test(o.ref)) { const C = await caInfo(), c = C && C.parks && C.parks[o.ref]; if (c && c[10]) cst = 'CA-' + c[10]; }
        if (o.prog !== 'POTA' || (!o.us && !cst)) { $('afMsg').textContent = 'This finder covers US and Canada parks for now. Try the Activation Kit for ' + o.ref + '.'; return; }
        const st = cst || (/^(US|K)-/.test(o.ref) && (o.ky || o.st === 'KY') ? 'KY' : (o.st || (p && p.st) || ''));
        p = Object.assign({}, p || {}, { ref: o.ref, n: o.name, short: o.short, la: o.la, lo: o.lo, web: o.web || (p && p.web), type: o.type, st });
        if (st && ST[st] && $('afSt').value !== st) { $('afSt').value = st; await loadState(st); }
      }
    }
    cur = p; history.replaceState(null, '', '?ref=' + encodeURIComponent(p.ref));
    $('afPk').value = LIST.some(x => x.ref === p.ref) ? p.ref : '';
    $('afOut').hidden = false; $('afName').textContent = p.n; $('afMeta').textContent = [p.ref, p.type, ST[p.st]].filter(Boolean).join(' · ');
    $('afBtns').innerHTML = (isFinite(p.la) ? '<a class="ln" style="color:#f0c96b;font-weight:700;margin-right:14px" href="' + dir(p.la, p.lo) + '" target="_blank" rel="noopener">🧭 DIRECTIONS TO THE PARK PIN</a>' : '') +
      '<a style="color:#f0c96b;font-weight:700;margin-right:14px" href="kpc-kit.html?ref=' + encodeURIComponent(p.ref) + '">🧰 ACTIVATION KIT</a><a style="color:#f0c96b;font-weight:700" href="kpc-in-park.html?ref=' + encodeURIComponent(p.ref) + '">📍 AM I IN THE PARK?</a>';
    $('afBnd').textContent = 'Checking the park line…'; $('afList').innerHTML = ''; $('afClos').innerHTML = '';
    if (window.KPCClos) KPCClos.html(p.ref, p.st).then(h => { if (cur === p) $('afClos').innerHTML = h; }).catch(() => {});
    const [pts, o] = await Promise.all([officialPoints(p), outline(p)]);
    if (cur !== p) return;
    p.pts = pts; p.fs = o.fs || [];
    $('afBnd').textContent = (p.fs.length ? (o.label === 'official' ? 'Official outline' + (o.src ? ' (' + o.src + ')' : '') + '.' : 'Approximate outline, not official' + (o.why ? ' (' + o.why + ')' : '') + '. Check the park’s own map.')
      : 'Pin only (no official outline yet), so points are not checked against the line. Check the park’s own map.');   /* RULE SHEET G wording */
    pts.forEach(x => Object.assign(x, { w: where(x, p.fs) }));
    $('afMsg').textContent = '';
    draw(); mapDraw(true);
    $('afOut').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  /* ---------- list + map ---------- */
  function shown() { return (cur && cur.pts || []).filter(x => !OFF[x.kind]); }
  function draw() {
    const all = cur.pts || [], L = shown().slice().sort((a, b) => (a.osm ? 1 : 0) - (b.osm ? 1 : 0) || (a.w.km == null ? 9 : a.w.km) - (b.w.km == null ? 9 : b.w.km));
    const nOff = all.filter(x => !x.osm).length, nOsm = all.length - nOff;
    $('afCount').textContent = nOff + ' OFFICIAL POINT' + (nOff === 1 ? '' : 'S') + (nOsm ? ' + ' + nOsm + ' FROM THE VOLUNTEER MAP' : '');
    const have = new Set(all.map(x => x.kind));
    $('afFlt').innerHTML = KINDS.filter(k => have.has(k[0])).map(k => '<button type="button" data-k="' + k[0] + '" aria-pressed="' + !OFF[k[0]] + '">' + k[1] + ' ' + k[2].toUpperCase() + ' (' + all.filter(x => x.kind === k[0]).length + ')</button>').join('');
    $('afList').innerHTML = L.length ? L.map((x, i) => '<div class="af-pt" data-i="' + all.indexOf(x) + '"><b>' + KI[x.kind][1] + ' ' + esc(x.label) + '</b><span class="src' + (x.osm ? ' osm' : '') + '">' + (x.osm ? 'VOLUNTEER MAP' : esc(x.src.toUpperCase())) + '</span>' +
      (x.w.t ? '<span class="in">' + esc(x.w.t) + '</span>' : '') + '<div><a href="' + dir(x.la, x.lo) + '" target="_blank" rel="noopener">DIRECTIONS ›</a><a href="#" data-zoom="' + all.indexOf(x) + '">SHOW ON MAP</a></div></div>').join('')
      : '<p class="af-msg">' + (all.length ? 'All points are filtered out.' : 'No official parking or access points for this park yet. Tap ＋ FILL IN FROM THE VOLUNTEER MAP, and check the park’s own map.') + '</p>';
  }
  function icon(x) { return L.divIcon({ className: 'pin' + (x.osm ? ' osm' : ''), html: '<span>' + KI[x.kind][1] + '</span>', iconSize: [28, 28], iconAnchor: [14, 14] }); }
  let sharpStop = null;
  function mapDraw(fit) {
    if (!window.L) return;
    if (!map) { map = L.map('afMap', { zoomControl: true }); if (window.KPCLayers) KPCLayers(map, 'Satellite + streets'); else L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(map); gOut = L.layerGroup().addTo(map); gPts = L.layerGroup().addTo(map); }
    gOut.clearLayers(); gPts.clearLayers();
    /* RULE SHEET G: one outline layer; zoomed in, the agency's full-detail copy of the part on screen (KPCB.sharpLayer) */
    if (sharpStop) { sharpStop(); sharpStop = null; }
    const fsOk = (cur.fs || []).filter(f => f && f.geometry); const outL = L.geoJSON({ type: 'FeatureCollection', features: fsOk.map(f => ({ type: 'Feature', properties: {}, geometry: f.geometry })) }, { style: { color: '#f0c96b', weight: 3, fillOpacity: .06 } }).addTo(gOut);
    if (B() && B().sharpLayer && fsOk.length) sharpStop = B().sharpLayer(map, outL, fsOk, { map: f => ({ type: 'Feature', properties: {}, geometry: f.geometry }) });
    const all = cur.pts || [];
    shown().forEach(x => L.marker([x.la, x.lo], { icon: icon(x) }).bindPopup('<b>' + esc(x.label) + '</b><br>' + (x.osm ? 'Volunteer map (OpenStreetMap)' : esc(x.src)) + (x.w.t ? '<br>' + esc(x.w.t) : '') + '<br><a href="' + dir(x.la, x.lo) + '" target="_blank" rel="noopener">Directions ›</a>').addTo(gPts));
    if (isFinite(cur.la)) L.circleMarker([cur.la, cur.lo], { radius: 6, color: '#fff', weight: 2, fillColor: '#c0392b', fillOpacity: 1 }).bindPopup('POTA park pin').addTo(gPts);
    map.invalidateSize();
    if (fit) {
      let b = null; try { const g = L.featureGroup([].concat(gOut.getLayers(), gPts.getLayers())); if (g.getLayers().length) b = g.getBounds(); } catch (e) {}
      if (b && b.isValid()) map.fitBounds(b.pad(.08), { maxZoom: 15 }); else if (isFinite(cur.la)) map.setView([cur.la, cur.lo], 13);
    }
    setTimeout(() => map.invalidateSize(), 60);
  }

  /* ---------- volunteer map (OpenStreetMap), only when asked ---------- */
  const OVER = ['https://overpass-api.de/api/interpreter', 'https://overpass.private.coffee/api/interpreter', 'https://overpass.kumi.systems/api/interpreter'];
  async function fillOsm() {
    if (!cur) return; const btn = $('afOsm'); btn.disabled = true; btn.textContent = 'LOOKING AT THE VOLUNTEER MAP…';
    let bb = null;
    if (cur.fs.length && B()) { const a = [180, 90, -180, -90]; cur.fs.forEach(f => { const x = B().bbox(f.geometry); a[0] = Math.min(a[0], x[0]); a[1] = Math.min(a[1], x[1]); a[2] = Math.max(a[2], x[2]); a[3] = Math.max(a[3], x[3]); }); bb = a; }
    else if (isFinite(cur.la)) bb = [cur.lo - .04, cur.la - .03, cur.lo + .04, cur.la + .03];
    if (!bb) { btn.textContent = 'NO PLACE TO LOOK'; return; }
    if ((bb[2] - bb[0]) * (bb[3] - bb[1]) > 1.2) { const c = [(bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2]; bb = [c[0] - .5, c[1] - .5, c[0] + .5, c[1] + .5]; }   // very big parks: the middle only
    const box = [bb[1] - .01, bb[0] - .01, bb[3] + .01, bb[2] + .01].map(v => v.toFixed(5)).join(',');
    const q = '[out:json][timeout:40];(nwr["amenity"="parking"]["access"!~"private|customers|no"](' + box + ');node["highway"="trailhead"](' + box + ');nwr["leisure"="slipway"](' + box + ');node["barrier"="gate"]["access"!~"private|no"](' + box + ');node["entrance"](' + box + '););out center tags 400;';
    let r = null; for (const u of OVER) { try { r = await fetch(u, { method: 'POST', body: 'data=' + encodeURIComponent(q), headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }).then(x => x.ok ? x.json() : null); if (r) break; } catch (e) {} }
    if (!r) { btn.disabled = false; btn.textContent = '＋ FILL IN FROM THE VOLUNTEER MAP (try again)'; return; }
    let n = 0;
    (r.elements || []).forEach(e => {
      const la = e.lat != null ? e.lat : e.center && e.center.lat, lo = e.lon != null ? e.lon : e.center && e.center.lon, t = e.tags || {}; if (!isFinite(la)) return;
      if (cur.pts.some(x => mi(x.la, x.lo, la, lo) < 0.03)) return;
      const kind = t.amenity === 'parking' ? 'parking' : t.highway === 'trailhead' ? 'trailhead' : t.leisure === 'slipway' ? 'ramp' : t.barrier === 'gate' ? 'gate' : 'entrance';
      const x = { la, lo, kind, osm: true, src: 'Volunteer map', label: (t.name || KI[kind][2].replace(/s$/, '')) + (t.fee === 'yes' ? ' (fee)' : '') };
      x.w = where(x, cur.fs); if (x.w.km != null && x.w.km > 1.6) return;   // over a mile outside the line: not this park's
      cur.pts.push(x); n++;
    });
    btn.textContent = n ? '✓ ' + n + ' ADDED FROM THE VOLUNTEER MAP' : 'THE VOLUNTEER MAP HAS NOTHING MORE HERE';
    draw(); mapDraw(false);
  }

  /* ---------- near me ---------- */
  function nearMe() {
    if (!navigator.geolocation) { $('afMsg').textContent = 'This browser cannot give a location.'; return; }
    $('afMsg').textContent = 'Finding where you are…';
    navigator.geolocation.getCurrentPosition(pos => {
      const la = pos.coords.latitude, lo = pos.coords.longitude;
      const L2 = LIST.filter(p => isFinite(p.la)).map(p => Object.assign({ d: mi(la, lo, p.la, p.lo) }, p)).sort((a, b) => a.d - b.d).slice(0, 8);
      $('afMsg').textContent = L2.length && L2[0].d > 150 ? 'These are the closest in ' + ST[$('afSt').value] + '; pick your own state above if you are somewhere else.' : '';
      $('afNearL').innerHTML = L2.map(p => '<button type="button" data-ref="' + esc(p.ref) + '">' + esc(p.n) + ' <small>· ' + Math.round(p.d) + ' mi · ' + (p.n_ap ? p.n_ap + ' official point' + (p.n_ap > 1 ? 's' : '') : 'volunteer map only') + '</small></button>').join('');
    }, e => { $('afMsg').textContent = e.code === 1 ? 'Location is blocked for this page. Pick a park instead.' : 'Could not get your location.'; }, { timeout: 15000, maximumAge: 300000 });
  }

  /* ---------- wiring ---------- */
  const opt = k => '<option value="' + k + '">' + ST[k] + '</option>', byName = (a, b) => ST[a] < ST[b] ? -1 : 1;
  $('afSt').innerHTML = '<optgroup label="United States">' + Object.keys(ST).filter(k => !isCA(k)).sort(byName).map(opt).join('') + '</optgroup><optgroup label="Canada">' + Object.keys(ST).filter(isCA).sort(byName).map(opt).join('') + '</optgroup>';
  $('afSt').addEventListener('change', () => loadState($('afSt').value));
  $('afPk').addEventListener('change', () => { if ($('afPk').value) open($('afPk').value); });
  $('afNear').addEventListener('click', nearMe);
  $('afNearL').addEventListener('click', e => { const b = e.target.closest('[data-ref]'); if (b) open(b.dataset.ref); });
  $('afOsm').addEventListener('click', fillOsm);
  $('afFlt').addEventListener('click', e => { const b = e.target.closest('[data-k]'); if (!b) return; OFF[b.dataset.k] = !OFF[b.dataset.k]; draw(); mapDraw(false); });
  $('afList').addEventListener('click', e => { const z = e.target.closest('[data-zoom]'); if (!z) return; e.preventDefault(); const x = cur.pts[+z.dataset.zoom]; if (map && x) { map.setView([x.la, x.lo], 17); $('afMap').scrollIntoView({ behavior: 'smooth', block: 'center' }); } });
  if (window.KPCTA) KPCTA.attach($('afQ'), ref => open(ref, 'search'));
  const qs = new URLSearchParams(location.search), qst = (qs.get('state') || '').toUpperCase(), qref = (qs.get('ref') || '').toUpperCase();
  const first = ST[qst] ? qst : ST[store('kpcAfSt')] ? store('kpcAfSt') : 'KY';
  $('afSt').value = first;
  loadState(first).then(() => { if (qref) open(qref, LIST.some(p => p.ref === qref) ? '' : 'search'); });
})();
