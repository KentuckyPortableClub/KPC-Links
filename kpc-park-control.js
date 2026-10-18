/* Kentucky Park Control (Brandon Oct 17 2026: 'make a super stripped down us trip planner… Kentucky Park Control… only has info for KY').
   Public page. Data: kpc-ky-data.json (parks / kff / summits / towns), kpc-campgrounds.json (places to stay), kpc-park-notes.json (tip counts).
   Map: Leaflet + kpc-map-tools.js layers / locate / full screen; park outline from KPCB.kyFor (Kentucky's official boundary files).
   Trip list saved on this device (localStorage kpcPcTrip); OPEN IN GOOGLE MAPS makes a multi-stop route. ?ref=US-1234 opens a park. */
(function () {
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const get = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const put = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const iOS = /iPhone|iPad|iPod/.test(navigator.userAgent);
  const dirUrl = (la, lo) => iOS ? `https://maps.apple.com/?daddr=${la},${lo}` : `https://www.google.com/maps/dir/?api=1&destination=${la},${lo}`;
  const COL = { pota: '#2e9e52', kff: '#1aa6a0', sota: '#e07a1c' };
  const SHOW = Object.assign({ pota: true, kff: false, sota: false, trails: true, parking: false }, get('kpcPcShow', {}));
  /* Kentucky trail parks (Brandon Oct 18: 'park control needs the trails'): official lines (Forest Service / State Parks / NPS), Kentucky part only */
  const KYB = [-89.6, 36.45, -81.9, 39.2], inKY = (lo, la) => lo >= KYB[0] && lo <= KYB[2] && la >= KYB[1] && la <= KYB[3];
  const TR = [
    { ref: 'US-11181', f: 'ky-sheltowee.geojson', col: '#6cdb97', by: 'U.S. Forest Service' },
    { ref: 'US-10102', f: 'ky-pine-mountain.geojson', col: '#ffc36b', by: 'Kentucky State Parks' },
    { ref: 'US-1253', f: 'ky-dawkins.geojson', col: '#c7a5ff', by: 'Kentucky State Parks' },
    { ref: 'US-3791', f: 'data/trails/US-3791.json', col: '#ef8a98', by: 'National Park Service' },
    { ref: 'US-4572', f: 'data/trails/US-4572.json', col: '#5bd5ec', by: 'National Park Service', lab: 'route (Ohio River)' },
    { ref: 'US-4572', f: 'ky-lecl-auto.geojson', col: '#2f9fb8', by: 'National Park Service', lab: 'auto tour route (signed roads)', dash: '7 6' }];
  const TL = {}; let TP = {}, trP = null, hi = null;
  let PAD = null; const PCS = { ref: '', html: '' }; let D = null, CG = {}, NOTES = {}, map = null, LAY = {}, outline = null, sel = null, ALL = [], APL = null, APM = [];
  let TRIP = get('kpcPcTrip', []);
  /* Oct 17 (Brandon): guests get 'coming soon' instead of 2-fer / 3-fer information; members see it all */
  const GUEST = !!(window.KPCGate && !window.KPCGate.member()), SOON = '2-fer and 3-fer information coming soon!';
  const isPin = t => /^PIN/.test(t.c);

  /* outline colour by the layer the piece came from (kpc-bounds.js KY list) */
  const PIECE = f => { const k = f._L && f._L.k;
    return k === 'bwma' ? { color: '#4ade80', dashArray: '8 5', who: 'Fish & Wildlife (WMA) land' } : k === 'bsnp' || k === 'bsna' ? { color: '#2dd4bf', who: 'Nature preserve land' }
      : k === 'bnps' ? { color: '#60a5fa', who: 'National Park Service' } : k === 'bfws' ? { color: '#5ab0ff', dashArray: '6 4', who: 'U.S. Fish & Wildlife' }
      : k === 'bdbnf' ? { color: '#a3e635', dashArray: '3 5', who: 'National Forest outer line' } : k === 'bwild' ? { color: '#16b3c0', dashArray: '2 4', who: 'Wild River corridor' }
      : k === 'bwilder' ? { color: '#c6e03a', who: 'Wilderness area' } : k === 'bkpc' ? { color: '#ffd400', dashArray: '12 5 2 5', who: 'approximate (KPC-drawn)' } : { color: '#f0c96b', who: 'State park land' }; };
  function kindOf(x) { return /^US-/.test(x.c) ? 'pota' : /^KFF-/.test(x.c) ? 'kff' : 'sota'; }
  function init() {
    map = L.map('pcMap', { zoomControl: true, preferCanvas: true }).setView([37.75, -85.7], 7);
    if (window.KPCLayers) { KPCLayers(map, null, { padKey: 'kpcPcPad', padOn: true }); PAD = KPCLayers.pad; } else L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(map);
    if (window.KPCLocate) KPCLocate(map); if (window.KPCFull) KPCFull(map);
    /* drop a pin anywhere: street view, directions, copy GPS, add the spot to the trip */
    if (window.KPCPin) KPCPin(map, { on: 'contextmenu', extra: (la, lo) => `<button type="button" data-pctrip="${la},${lo}" style="margin-top:6px;width:100%;padding:8px;border-radius:8px;border:1px solid #d5a63a;background:#fff6dd;font:900 12px Arial;cursor:pointer">+ ADD THIS SPOT TO MY TRIP</button>`,
      onPop: el => el.querySelectorAll('[data-pctrip]').forEach(b => b.onclick = () => { const [la, lo] = b.dataset.pctrip.split(',').map(Number); const nm = prompt('Name this stop (optional):', 'Pin ' + la.toFixed(4) + ', ' + lo.toFixed(4));
        if (nm === null) return; TRIP.push({ c: 'PIN-' + Date.now().toString(36), n: nm || 'Dropped pin', la, lo }); if (TRIP.length > 10) TRIP.shift(); put('kpcPcTrip', TRIP); trip(); b.textContent = '✓ ON MY TRIP'; }) });
    if (window.KPCHere) KPCHere(map, { piece: PIECE, onRef: r => { const y = byRef(r); if (y) pick(y); } });   /* Oct 17 (Brandon: 'drops pins way too easy'): a tap says what land is here; pins = long-press / right-click / DROP A PIN */
    $('pcDrop').onclick = () => { const c = map.getCenter(); map.fire('contextmenu', { latlng: c }); $('pcMap').scrollIntoView({ behavior: 'smooth', block: 'center' }); };
    for (const k of ['pota', 'kff', 'sota', 'trails', 'parking']) { LAY[k] = L.layerGroup(); if (SHOW[k]) LAY[k].addTo(map); }
    if (SHOW.trails) trails();
    for (const x of ALL) { const k = kindOf(x);
      const m = L.circleMarker([x.la, x.lo], { radius: k === 'sota' ? 5 : 6.5, bubblingMouseEvents: false, color: '#fff', weight: 1.4, fillColor: COL[k], fillOpacity: .92 });
      m.bindTooltip(`${x.c} · ${x.n}`); m.on('click', () => pick(x, false)); m.addTo(LAY[k]); x.m = m; }
    count(); chips();
    const lb = $('pcPad'); if (lb) { if (!PAD) lb.hidden = true; else { const sync = () => { const on = map.hasLayer(PAD.layer); lb.classList.toggle('on', on); lb.setAttribute('aria-pressed', on); };
      lb.onclick = () => { const on = !map.hasLayer(PAD.layer); if (on) PAD.layer.addTo(map); else map.removeLayer(PAD.layer); put('kpcPcPad', on ? 1 : 0); sync(); };
      map.on('overlayadd overlayremove layeradd layerremove', sync); map.whenReady(() => setTimeout(sync, 50));
      /* Oct 17 (Brandon: 'all state parks next to CoE land … same color as around US-1271'): the PAD-US pictures colour land by who RUNS it, so Corps
         land run by Kentucky (lake WMAs, some park land) looked like state land. ky-usace.geojson = land the Corps OWNS: always the same orange outline. */
      let CO = null, coP = null; const coSync = () => { const on = map.hasLayer(PAD.layer);
        if (on && !CO && !coP) coP = fetch('ky-usace.geojson').then(r => r.ok ? r.json() : null).then(j => { if (!j) return; map.createPane('pcCorps').style.zIndex = 395;
          CO = L.geoJSON(j, { pane: 'pcCorps', renderer: L.svg({ pane: 'pcCorps' }), style: () => ({ color: '#ff8c38', weight: 2.6, opacity: 1, fill: true, fillOpacity: 0 }),
            onEachFeature: (f, l) => { const p = f.properties || {}; l.bindTooltip(`<b>Army Corps of Engineers land</b><br>${esc(p.NAME || '')}${p.MANAGER ? '<br>Run by: ' + esc(p.MANAGER) : ''}` + (/Dewey Lake|Fishtrap Lake|Yatesville Lake/i.test(p.NAME||'')?'<br><b>This one IS a POTA park</b> (one of the few Corps lakes run by Kentucky that POTA added).':'<br><small>Usually NOT part of a POTA park unless a state agency runs it.</small>'), { sticky: true }); } });
          coSync(); }).catch(() => {}).finally(() => { coP = null; });
        if (CO) { if (on && !map.hasLayer(CO)) CO.addTo(map); if (!on && map.hasLayer(CO)) map.removeLayer(CO); } };
      map.on('layeradd layerremove', e => { if (e.layer === PAD.layer) coSync(); }); map.whenReady(() => setTimeout(coSync, 80)); } }
  }
  function count() { const n = ALL.filter(x => SHOW[kindOf(x)]).length; $('pcCount').textContent = n + ' on the map' + (SHOW.trails ? ' + ' + new Set(TR.map(t => t.ref)).size + ' trails' : ''); }
  /* lines: keep only the stretches inside Kentucky */
  function kyLines(g) { const out = []; const add = l => { let run = []; for (const p of l) { if (inKY(p[0], p[1])) run.push([p[1], p[0]]); else { if (run.length > 1) out.push(run); run = []; } } if (run.length > 1) out.push(run); };
    const geo = gg => { if (!gg) return; if (gg.type === 'LineString') add(gg.coordinates); else if (gg.type === 'MultiLineString') gg.coordinates.forEach(add); else if (gg.type === 'GeometryCollection') gg.geometries.forEach(geo); };
    (g.type === 'FeatureCollection' ? g.features : [g]).forEach(f => geo(f.geometry || f)); return out; }
  function trails() {
    return trP || (trP = Promise.all([fetch('ky-trail-parks.json').then(r => r.json()).catch(() => ({}))].concat(TR.map(t => fetch(t.f).then(r => r.json()).catch(() => null)))).then(([tp, ...G]) => {
      Object.values(tp || {}).forEach(v => { if (v && v.ref) TP[v.ref] = v; });
      G.forEach((g, i) => { const t = TR[i]; if (!g) return; const ls = kyLines(g); if (!ls.length) return; const x = byRef(t.ref), nm = (x ? x.n : t.ref) + (t.lab ? ' · ' + t.lab : '');
        const lay = L.layerGroup([L.polyline(ls, { color: '#111', weight: 7, opacity: .55, interactive: false }), L.polyline(ls, { color: t.col, weight: 4, opacity: .95, dashArray: t.dash || null, bubblingMouseEvents: false })]);
        lay.eachLayer(p => { if (p.options.interactive !== false) { p.bindTooltip(`🥾 ${t.ref} · ${nm}`, { sticky: true }); p.on('click', () => { const y = byRef(t.ref); if (y) pick(y); }); } });
        lay.addTo(LAY.trails); (TL[t.ref] = TL[t.ref] || []).push({ ls, t });
        /* a trail park whose POTA pin is outside Kentucky (Lewis & Clark: Omaha) gets a pin on its Kentucky line */
        if (x && !inKY(x.lo, x.la) && !x.kyPin) { const mid = ls.reduce((a, b) => b.length > a.length ? b : a); const p = mid[Math.floor(mid.length / 2)]; x.la = p[0]; x.lo = p[1]; x.kyPin = 1; if (x.m) x.m.setLatLng(p); } });
      count(); }));
  }
  const tBounds = ref => { const b = L.latLngBounds([]); (TL[ref] || []).forEach(o => o.ls.forEach(l => l.forEach(p => b.extend(p)))); return b; };
  function chips() { document.querySelectorAll('[data-pg]').forEach(b => { const k = b.dataset.pg; b.classList.toggle('on', !!SHOW[k]); b.setAttribute('aria-pressed', SHOW[k] ? 'true' : 'false'); }); }
  document.querySelectorAll('[data-pg]').forEach(b => b.onclick = () => { const k = b.dataset.pg; SHOW[k] = !SHOW[k]; put('kpcPcShow', SHOW); if (map) { if (SHOW[k]) { LAY[k].addTo(map); if (k === 'trails') trails(); } else map.removeLayer(LAY[k]); } chips(); count(); });

  const byRef = c => ALL.find(x => x.c.toUpperCase() === String(c).toUpperCase());
  async function pick(x, fly) {
    sel = x; const k = kindOf(x); if (!SHOW[k]) { SHOW[k] = true; put('kpcPcShow', SHOW); LAY[k].addTo(map); chips(); count(); }
    if (hi) { map.removeLayer(hi); hi = null; }
    if (outline) { map.removeLayer(outline); outline = null; }
    apShow(x);
    if (TR.some(t => t.ref === x.c)) { /* a trail park: light up its line instead of an outline */
      if (!SHOW.trails) { SHOW.trails = true; put('kpcPcShow', SHOW); LAY.trails.addTo(map); chips(); }
      await trails(); if (sel !== x) return; info(x); try { history.replaceState(null, '', '?ref=' + encodeURIComponent(x.c)); } catch (e) {}
      hi = L.layerGroup((TL[x.c] || []).map(o => L.polyline(o.ls, { color: '#f0c96b', weight: 8, opacity: .55, interactive: false }))).addTo(map);
      const b = tBounds(x.c); if (fly !== false && b.isValid()) map.fitBounds(b.pad(.08), { maxZoom: 13 }); return; }
    if (SHOW.trails) trails().then(() => { if (sel === x) info(x); });
    if (fly !== false) map.setView([x.la, x.lo], Math.max(map.getZoom(), k === 'sota' ? 13 : 12));
    info(x); try { history.replaceState(null, '', '?ref=' + encodeURIComponent(x.c)); } catch (e) {}
    if (k !== 'sota' && window.KPCB && KPCB.kyFor) {
      try { const ref = k === 'kff' && x.p ? x.p : x.c, F = await KPCB.kyFor(ref); if (sel !== x || !F || !F.length) return;
        /* Oct 17 (Brandon: Taylorsville Lake 'hard to tell what is what'): each piece in its own colour, by whose land it is */
        outline = L.geoJSON({ type: 'FeatureCollection', features: F }, { style: f => Object.assign({ weight: 3, fill: false }, PIECE(f)), interactive: false }).addTo(map);
        const seen = {}, key = F.map(f => { const P = PIECE(f), nm = (f.properties || {}).NAME || (f._L && f._L.name) || ''; if (seen[nm]) return ''; seen[nm] = 1; return `<li><i style="display:inline-block;width:22px;height:0;border-top:3px ${P.dashArray ? 'dashed' : 'solid'} ${P.color};vertical-align:middle;margin-right:6px"></i>${esc(nm)} <span class="pc-tag">${esc(P.who)}</span></li>`; }).join('');
        PCS.ref = x.c; PCS.html = `<div class="pc-k" style="margin-top:8px">🗺 THE OUTLINE ON THE MAP</div><ul class="pc-list">${key}</ul>${PAD ? '<p class="pc-note">Orange outline = land the Army Corps of Engineers OWNS (USGS PAD-US), even where Kentucky runs it (usually NOT part of a POTA park unless a state agency runs it). Turn it off or on with the 🗺 LAND OWNERS chip.</p>' : ''}`; const box = document.getElementById('pcPieces'); if (box) box.innerHTML = PCS.html;
        if (fly !== false) { const b = outline.getBounds(); if (b.isValid()) map.fitBounds(b.pad(.1), { maxZoom: 14 }); } } catch (e) {} }
  }
  /* Oct 18 (Brandon: 'add the parking spots you gathered tonight in Park Control'): the park's `ap` points as map markers */
  function apIcon(t) {
    const fc = /KPC field check/i.test(t), ic = fc ? '✅' : /trailhead/i.test(t) ? '🥾' : /boat|ramp|fishing|carry-down|bridge/i.test(t) ? '⛵' : /road|enters|end of|closest/i.test(t) ? '🛣' : /kiosk|office|visitor|lodge|museum|info/i.test(t) ? 'ℹ' : 'P';
    const bg = fc ? '#d5a63a' : /road|enters|end of|closest/i.test(t) ? '#6b7280' : '#1d5fbf';
    return L.divIcon({ className: 'pc-ap', html: `<span style="display:flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;background:${bg};color:#fff;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.5);font:800 12px/1 system-ui">${ic}</span>`, iconSize: [24, 24], iconAnchor: [12, 12], popupAnchor: [0, -12] });
  }
  function apShow(x) {
    if (APL) { LAY.parking.removeLayer(APL); APL = null; } APM = [];
    const k = kindOf(x), park = k === 'pota' ? x : k === 'kff' && x.p ? byRef(x.p) : null, ap = (park && park.ap) || [];
    if (!ap.length) return;
    APL = L.layerGroup().addTo(LAY.parking);
    ap.forEach((p, i) => { const m = L.marker([p[0], p[1]], { icon: apIcon(p[2] || ''), bubblingMouseEvents: false, zIndexOffset: 500 })
      .bindPopup(`<b>${esc(p[2] || 'Access point')}</b><br><span style="font-family:ui-monospace,monospace">${(+p[0]).toFixed(5)}, ${(+p[1]).toFixed(5)}</span><br><a href="${dirUrl(p[0], p[1])}" target="_blank" rel="noopener">🚗 DIRECTIONS</a> · <a href="#" data-cpg="${p[0]},${p[1]}">COPY GPS</a>`)
      .addTo(APL); APM[i] = m; });
  }
  document.addEventListener('click', e => { const a = e.target.closest('[data-cpg]'); if (!a) return; e.preventDefault(); const t = a.dataset.cpg; (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(() => { a.textContent = '✓ COPIED'; }).catch(() => prompt('GPS', t)); });
  function info(x) {
    const k = kindOf(x), lab = { pota: 'POTA PARK', kff: 'KFF (WWFF) REFERENCE', sota: 'SOTA SUMMIT' }[k];
    const page = k === 'pota' ? `https://pota.app/#/park/${x.c}` : k === 'kff' ? `https://wwff.co/directory/?showRef=${x.c}` : `https://sotl.as/summits/${x.c}`;
    const park = k === 'pota' ? x : k === 'kff' && x.p ? byRef(x.p) : null;
    const tipsRef = x.c, tips = NOTES[tipsRef] || 0, cg = park && CG[park.c];
    const also = [];
    if (k === 'pota') { if (GUEST) x = Object.assign({}, x, { tf: [] }); (x.kff || []).forEach(r => { const y = byRef(r); also.push([r, y ? y.n : '', 'Also KFF']); }); (x.sota || []).forEach(r => { const y = byRef(r); also.push([r, y ? y.n : '', 'SOTA summit inside (only counts on top)']); }); (x.tf || []).forEach(r => { const y = byRef(typeof r === 'string' ? r : r.c || r[0]); const rr = typeof r === 'string' ? r : r.c || r[0]; also.push([rr, y ? y.n : '', 'Overlapping boundaries (2-fer)']); }); }
    if (k === 'kff' && park) also.push([park.c, park.n, 'Same place: POTA park']);
    if (k === 'pota' && !GUEST) Object.values(TP).forEach(v => { if ((v.parks || []).some(p => (p.refs || []).includes(x.c)) && !also.some(a => a[0] === v.ref)) also.push([v.ref, v.name, 'Trail passes through (possible 2-fer: stand on the trail inside the park)']); });
    const tp = TP[x.c], tline = TL[x.c];
    const trailBox = tline ? `<div class="pc-k" style="margin-top:8px">🥾 TRAIL</div><p class="pc-note" style="margin-top:2px">Shown on the map in Kentucky (line from the ${esc(tline[0].t.by)}${tline.length > 1 ? '; dashed = ' + esc(tline[1].t.lab || '') : ''}). Set up on the trail itself, on public land.</p>` +
      (GUEST ? `<p class="pc-note">${SOON}</p>` : '') + (!GUEST && tp && tp.parks && tp.parks.length ? `<div class="pc-k" style="margin-top:8px">THE TRAIL PASSES THROUGH (POSSIBLE 2-FER / 3-FER: VERIFY)</div><ul class="pc-list">${tp.parks.map(p => `<li>${(p.refs || []).map((r, i) => `<a href="?ref=${encodeURIComponent(r)}" data-ref="${esc(r)}">${esc(r)}</a> ${esc((p.names || [])[i] || '')}`).join(' + ')} <span class="pc-tag">${esc(p.type || '2-fer')}${p.how ? ' · ' + esc(p.how) : ''}</span></li>`).join('')}</ul><p class="pc-note">Stand on the trail inside the other park, and confirm both boundaries on the official maps.</p>` : '') : '';
    const ap = (park && park.ap) || [];
    $('pcInfo').innerHTML = `<div class="pc-k">${lab}</div><h3>${esc(x.n)}</h3>
      <div class="pc-meta"><span class="pc-ref">${esc(x.c)}</span>${x.co ? ' · ' + esc(x.co) + ' County' : ''}${x.t ? ' · ' + esc(x.t) : ''}${x.ft ? ' · ' + Number(x.ft).toLocaleString() + ' ft' + (x.pts ? ' · ' + x.pts + ' pts' : '') : ''}</div>
      <div class="pc-acts"><a class="gold" href="${dirUrl(x.la, x.lo)}" target="_blank" rel="noopener">🚗 DIRECTIONS</a><button type="button" id="pcAdd">${TRIP.some(t => t.c === x.c) ? '✓ ON MY TRIP' : '+ ADD TO MY TRIP'}</button>
      ${park && park.web ? `<a href="${esc(park.web)}" target="_blank" rel="noopener">OFFICIAL WEBSITE ↗</a>` : ''}${park && park.off ? `<a href="${esc(park.off)}" target="_blank" rel="noopener">OFFICIAL MAP ↗</a>` : ''}${park && park.camp ? `<a href="${esc(park.camp)}" target="_blank" rel="noopener">CAMPING ↗</a>` : ''}
      <a href="${page}" target="_blank" rel="noopener">${k === 'pota' ? 'POTA' : k === 'kff' ? 'WWFF' : 'SOTLAS'} PAGE ↗</a>
      <a href="kpc-park-notes.html#${encodeURIComponent(tipsRef)}">📝 PARK TIPS${tips ? ' (' + tips + ')' : ''}</a>${cg ? `<a href="kpc-campgrounds.html#park-${esc(park.c)}">⛺ PLACES TO STAY</a>` : ''}</div>
      ${also.length ? `<div class="pc-k" style="margin-top:8px">ALSO HERE</div><ul class="pc-list">${also.map(a => `<li><a href="?ref=${encodeURIComponent(a[0])}" data-ref="${esc(a[0])}">${esc(a[0])}</a> ${esc(a[1])} <span class="pc-tag">${esc(a[2])}</span></li>`).join('')}</ul>` : ''}
      <div id="pcPieces">${PCS.ref === x.c ? PCS.html : ''}</div>
      ${trailBox}
      ${ap.length ? `<div class="pc-k" style="margin-top:8px">🅿 PARKING &amp; ACCESS POINTS </div><ul class="pc-list">${ap.map((p, i) => `<li><a href="#" data-ap="${i}">📍 ${esc(p[2] || 'Access point')}</a> · <a href="${dirUrl(p[0], p[1])}" target="_blank" rel="noopener">DIRECTIONS</a></li>`).join('')}</ul><p class="pc-note">✅ gold = checked in the field by a KPC member · P / ℹ / 🥾 / ⛵ blue = from the land manager's own maps (KDFWR, State Parks, Forest Service) · 🛣 grey = from the state road map (where a road enters the park): check the satellite view. Turn them on or off with the 🅿 PARKING chip above the map; tapping one turns them on.</p>` : ''}
      <p class="pc-note">GPS ${x.la.toFixed(5)}, ${x.lo.toFixed(5)}${k === 'sota' ? ' · activation zone = within 25 m (82 ft) of the top, no vehicle' : ' · the pin is a guide; the official boundary decides'}</p>`;
    $('pcAdd').onclick = () => { if (!TRIP.some(t => t.c === x.c)) { TRIP.push({ c: x.c, n: x.n, la: x.la, lo: x.lo }); if (TRIP.length > 10) TRIP.shift(); put('kpcPcTrip', TRIP); } trip(); info(x); };
    $('pcInfo').querySelectorAll('[data-ref]').forEach(a => a.onclick = e => { e.preventDefault(); const y = byRef(a.dataset.ref); if (y) pick(y); });
    $('pcInfo').querySelectorAll('[data-ap]').forEach(a => a.onclick = e => { e.preventDefault(); const m = APM[+a.dataset.ap]; if (!m) return; if (!SHOW.parking) { SHOW.parking = true; put('kpcPcShow', SHOW); LAY.parking.addTo(map); chips(); } map.setView(m.getLatLng(), Math.max(map.getZoom(), 16)); m.openPopup(); const el = document.getElementById('pcMap') || map.getContainer(); el.scrollIntoView({ behavior: 'smooth', block: 'center' }); });
    /* Oct 17 (Brandon: the card's name hid under the header): scroll so the card's top sits just below the site header */
    if (matchMedia('(max-width:900px)').matches) { const hd = document.querySelector('header.site-nav'), h = hd ? hd.getBoundingClientRect().height : 0; window.scrollTo({ top: $('pcInfo').getBoundingClientRect().top + window.scrollY - h - 12, behavior: 'smooth' }); }
  }
  function trip() {
    const el = $('pcTripL'); if (!TRIP.length) { el.innerHTML = '<p class="pc-empty">Tap <b>+ ADD TO MY TRIP</b> on a park to start a trip.</p>'; return; }
    const last = TRIP[TRIP.length - 1], way = TRIP.slice(0, -1).map(t => t.la + ',' + t.lo).join('|');
    const g = `https://www.google.com/maps/dir/?api=1&destination=${last.la},${last.lo}${way ? '&waypoints=' + encodeURIComponent(way) : ''}`;
    el.innerHTML = `<ol>${TRIP.map((t, i) => `<li>${isPin(t) ? `<a href="#" data-tr="${i}">📌</a>` : `<a href="?ref=${encodeURIComponent(t.c)}" data-tr="${i}">${esc(t.c)}</a>`} ${esc(t.n)}<button type="button" data-rm="${i}" aria-label="Remove">✕</button></li>`).join('')}</ol>
      <div class="pc-acts"><a class="gold" href="${g}" target="_blank" rel="noopener">🗺 OPEN MY TRIP IN GOOGLE MAPS</a><button type="button" id="pcClr">CLEAR</button></div><p class="pc-note">Google Maps starts from where you are and stops at each park in this order. Up to 10 stops.</p>`;
    el.querySelectorAll('[data-rm]').forEach(b => b.onclick = () => { TRIP.splice(+b.dataset.rm, 1); put('kpcPcTrip', TRIP); trip(); if (sel) info(sel); });
    el.querySelectorAll('[data-tr]').forEach(a => a.onclick = e => { e.preventDefault(); const t = TRIP[+a.dataset.tr], y = byRef(t.c); if (y) pick(y); else { map.setView([t.la, t.lo], 15); map.fire('click', { latlng: L.latLng(t.la, t.lo) }); } });
    $('pcClr').onclick = () => { TRIP = []; put('kpcPcTrip', TRIP); trip(); if (sel) info(sel); };
  }
  /* search: parks / references / summits by name or number, and Kentucky towns */
  const norm = s => String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9/ -]/g, ' ').replace(/\s+/g, ' ').trim();
  let SUG = [], si = -1;
  function suggest() {
    const q = norm($('pcQ').value); const box = $('pcSug'); if (q.length < 2) { box.hidden = true; return; }
    let qq = q; if (/^\d{1,5}$/.test(q)) qq = 'us-' + q.padStart(4, '0');
    const W = q.split(' ');
    const hit = ALL.filter(x => { const c = x.c.toLowerCase(), n = norm(x.n); return c === qq || c.startsWith(qq) || c.includes(q) || W.every(w => n.includes(w)); }).slice(0, 12);
    const towns = (D.towns || []).filter(t => norm(t.n).startsWith(q)).slice(0, 4);
    SUG = hit.map(x => ({ x })).concat(towns.map(t => ({ t }))); si = -1;
    box.innerHTML = SUG.map((s, i) => s.x ? `<button type="button" data-s="${i}"><b>${esc(s.x.c)}</b>${esc(s.x.n)}<small>${esc(s.x.co || '')}</small></button>` : `<button type="button" data-s="${i}">🏘 ${esc(s.t.n)}<small>town · show the parks nearby</small></button>`).join('') || '<div class="pc-empty" style="padding:10px">Nothing in Kentucky by that name or number.</div>';
    box.hidden = false;
  }
  function choose(i) { const s = SUG[i]; if (!s) return; $('pcSug').hidden = true; if (s.x) { $('pcQ').value = s.x.c + ' ' + s.x.n; pick(s.x); } else { $('pcQ').value = s.t.n; near(s.t.la, s.t.lo, s.t.n); } }
  $('pcQ').addEventListener('input', suggest);
  $('pcQ').addEventListener('keydown', e => { const n = SUG.length; if (e.key === 'ArrowDown') { e.preventDefault(); si = Math.min(n - 1, si + 1); } else if (e.key === 'ArrowUp') { e.preventDefault(); si = Math.max(0, si - 1); } else if (e.key === 'Enter') { e.preventDefault(); choose(si < 0 ? 0 : si); return; } else if (e.key === 'Escape') { $('pcSug').hidden = true; return; } else return;
    $('pcSug').querySelectorAll('button').forEach((b, i) => b.classList.toggle('on', i === si)); });
  $('pcSug').addEventListener('click', e => { const b = e.target.closest('[data-s]'); if (b) choose(+b.dataset.s); });
  document.addEventListener('click', e => { if (!e.target.closest('.pc-search')) $('pcSug').hidden = true; });
  const km = (a, b, c, d) => { const R = Math.PI / 180, x = Math.sin((c - a) * R / 2) ** 2 + Math.cos(a * R) * Math.cos(c * R) * Math.sin((d - b) * R / 2) ** 2; return 12742 * Math.asin(Math.sqrt(x)); };
  function near(la, lo, where) {
    map.setView([la, lo], 10);
    const L2 = ALL.filter(x => SHOW[kindOf(x)]).map(x => [x, km(la, lo, x.la, x.lo)]).sort((a, b) => a[1] - b[1]).slice(0, 10);
    $('pcInfo').innerHTML = `<div class="pc-k">CLOSEST TO ${esc(String(where).toUpperCase())}</div><ul class="pc-list">${L2.map(([x, d]) => `<li><a href="?ref=${encodeURIComponent(x.c)}" data-ref="${esc(x.c)}">${esc(x.c)}</a> ${esc(x.n)} <small>${(d * 0.621).toFixed(1)} mi</small></li>`).join('')}</ul><p class="pc-note">Showing what's turned on above (POTA / KFF / SOTA).</p>`;
    $('pcInfo').querySelectorAll('[data-ref]').forEach(a => a.onclick = e => { e.preventDefault(); const y = byRef(a.dataset.ref); if (y) pick(y); });
  }
  $('pcNear').onclick = () => { if (!navigator.geolocation) return; $('pcNear').textContent = '📍 FINDING YOU…';
    navigator.geolocation.getCurrentPosition(p => { $('pcNear').textContent = '📍 NEAR ME'; near(p.coords.latitude, p.coords.longitude, 'you'); }, () => { $('pcNear').textContent = '📍 NEAR ME'; alert('Your location is turned off for this site.'); }, { enableHighAccuracy: true, timeout: 15000 }); };

  Promise.all([fetch('kpc-ky-data.json').then(r => r.json()), fetch('kpc-campgrounds.json').then(r => r.json()).catch(() => null), fetch('kpc-park-notes.json').then(r => r.json()).catch(() => null)]).then(([d, cg, pn]) => {
    D = d; ALL = [].concat(d.parks || [], d.kff || [], d.summits || []).filter(x => isFinite(x.la) && isFinite(x.lo));
    if (cg && cg.parks) cg.parks.forEach(p => { const n = (p.campgrounds || []).length + (p.lodging || []).length; if (p.pota && n) CG[p.pota] = n; });
    if (pn && pn.notes) pn.notes.forEach(n => { NOTES[n.ref] = (NOTES[n.ref] || 0) + 1; });
    const go = () => { if (!window.L) { setTimeout(go, 200); return; } init(); trip();
      const P = new URLSearchParams(location.search), r = P.get('ref') || decodeURIComponent(location.hash.slice(1));
      const x = r && byRef(r.trim()); if (x) pick(x); };
    go();
  }).catch(() => { $('pcInfo').innerHTML = '<p class="pc-empty">The Kentucky park list did not load. Check your signal and reload.</p>'; });
})();
