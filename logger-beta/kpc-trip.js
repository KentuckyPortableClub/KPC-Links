/* KPC app: 🚗 TRIP PLANNER, a tab on MAP (Nov 18 2026; to-do 8; Brandon Nov 17: 'be nice to install some of the features from us trip
   planner on it instead of new page a tab off it'; Nov 18: 'Trip planner as a MAP tab'). MAP gets two tabs: 🗺 CONTACTS (the QSO map) |
   🚗 TRIP PLANNER. Built on the website's park data the app already keeps (the OFFLINE PARK PACKS, kpc-parks.js: the same parks,
   outlines official / approximate / pin, access points, made from the website's US trip planner data and kept up to date about daily),
   so it all works with NO SIGNAL once a state is on the device.
   - FIND: a state on the device, a search (number, name, county), 📍 NEAR ME (GPS, else your grid) = sorted by distance, and
     'not activated by me yet'. Each park: number, name, county, how far, outline (✅ official / ⚠ approximate / pin only), a closure
     warning (KPCAlerts), + ADD.
   - THE TRIP: the stops in order, ↑ ↓ ✕, ⚡ NEAREST-NEXT (re-orders from where you are), how far in a straight line
     (roads are longer), 🧭 DIRECTIONS for the whole trip in the phone's maps app, 🌲 START HERE (that park becomes MY PARK, role
     ACTIVATE, LOG), ⬇ GPX / ⬇ CSV, 📤 SHARE. Kept on the device (localStorage kpcAppTrip).
   - THE MAP: the parks found (dots), the trip (numbered gold pins + a line), you.
   2-fer information is not shown here (beta / members-only on the website; Brandon Nov 17: 'No 2fer info yet'). */
(function (G) {
  'use strict';
  const AP = G.KPCApp, $ = id => document.getElementById(id); if (!AP || !G.KPCMap) return;
  const esc = AP.esc;
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } };
  const SV = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const T = Object.assign({ stops: [], st: '', q: '', near: false, notMine: false, sat: true }, LS('kpcAppTrip', {}));
  if (!Array.isArray(T.stops)) T.stops = [];
  const save = () => SV('kpcAppTrip', T);
  const R = Math.PI / 180;
  const km = (a, b) => { const dLa = (b.la - a.la) * R, dLo = (b.lo - a.lo) * R, h = Math.sin(dLa / 2) ** 2 + Math.cos(a.la * R) * Math.cos(b.la * R) * Math.sin(dLo / 2) ** 2; return 2 * 6371 * Math.asin(Math.min(1, Math.sqrt(h))); };
  const dist = k => AP.dist ? AP.dist(k) : (k * 0.621).toFixed(1) + ' mi';
  const scr = $('scrMap'); if (!scr) return;

  /* ---------------- the two tabs on MAP ---------------- */
  scr.insertAdjacentHTML('afterbegin', '<div class="subtabs" id="mpSub" role="tablist"><button type="button" role="tab" class="on" data-msub="qso">🗺 CONTACTS</button><button type="button" role="tab" data-msub="trip">🚗 TRIP PLANNER</button></div>');
  scr.insertAdjacentHTML('beforeend', `<div class="trbox" id="trBox">
      <div class="trbar"><select id="trSt" aria-label="State"></select><input id="trQ" type="search" placeholder="Search: US-1234, a name, a county" autocomplete="off">
        <button type="button" class="chip" id="trNear">📍 NEAR ME</button><button type="button" class="chip" id="trMine">NOT ACTIVATED BY ME</button><button type="button" class="chip" id="trSat"></button></div>
      <div class="trwrap"><div class="trmap"><canvas id="trCv" aria-label="Map: the parks found and the trip"></canvas></div>
        <div class="trside"><div class="card trtrip" id="trTrip"></div><div class="trfound"><div class="hint" id="trCnt"></div><div class="trlist" id="trList"></div></div></div></div>
    </div>`);
  let SUB = (() => { try { return localStorage.getItem('kpcAppMapSub') || 'qso'; } catch (e) { return 'qso'; } })();
  function sub(w) {
    SUB = w; try { localStorage.setItem('kpcAppMapSub', w); } catch (e) {}
    scr.dataset.sub = w; document.querySelectorAll('#mpSub [data-msub]').forEach(b => { b.classList.toggle('on', b.dataset.msub === w); b.setAttribute('aria-selected', b.dataset.msub === w); });
    if (w === 'trip') open();
  }
  $('mpSub').onclick = e => { const b = e.target.closest('[data-msub]'); if (b) sub(b.dataset.msub); };

  /* ---------------- data: every park on the device ---------------- */
  let PACKS = [], ALL = [], ME = null, MAP = null, PICK = null;
  async function load() {
    PACKS = G.KPCParks ? await KPCParks.loaded() : [];
    ALL = PACKS.flatMap(pk => (pk.parks || []).map(p => ({ p, st: pk.state, ol: (pk.outlines || {})[p.ref] || [] })));
    const sts = PACKS.map(pk => pk.state).sort();
    if (!sts.includes(T.st)) T.st = sts[0] || '';
    $('trSt').innerHTML = sts.length ? sts.map(s => `<option value="${s}"${s === T.st ? ' selected' : ''}>${s}</option>`).join('') + '<option value="*">every state on this device</option>' : '<option value="">no state on this device</option>';
    if (T.st === '*') $('trSt').value = '*';
  }
  const activated = ref => G.KPCLog ? (KPCLog.activated ? KPCLog.activated(ref) : [...KPCLog.all().values()].some(q => !q.d && (q.myrefs || []).includes(ref))) : false;
  const olTxt = x => x.ol.length ? (x.ol.some(o => o.src === 'official') ? '✅ official outline' : '⚠ approximate outline (not official)') : 'pin only';
  function found() {
    const q = T.q.trim().toUpperCase();
    let L = ALL.filter(x => T.st === '*' || x.st === T.st);
    if (q) L = L.filter(x => (x.p.ref + ' ' + x.p.name + ' ' + (x.p.co || '') + ' ' + (x.p.kind || '')).toUpperCase().includes(q));
    if (T.notMine) L = L.filter(x => !activated(x.p.ref));
    if (T.near && ME) { L.forEach(x => { x.km = km(ME, x.p); }); L.sort((a, b) => a.km - b.km); } else L.sort((a, b) => a.p.ref.localeCompare(b.p.ref, undefined, { numeric: true }));
    return L;
  }
  /* ---------------- drawing ---------------- */
  const inTrip = ref => T.stops.some(s => s.ref === ref);
  function drawList() {
    const L = found(), N = 80;
    $('trCnt').textContent = !PACKS.length ? '' : L.length + ' park' + (L.length === 1 ? '' : 's') + (L.length > N ? ' (first ' + N + ' shown: search to narrow)' : '');
    if (!PACKS.length) { $('trList').innerHTML = `<div class="st">No parks on this device yet. Get a state's parks while you have signal; then this works with none.</div><div class="row"><button type="button" class="b gold" id="trGet">🌲 GET MY STATE'S PARKS</button><button type="button" class="b" id="trPk">STATION → PARKS</button></div>`;
      $('trGet').onclick = async () => { if (G.KPCParks) { await KPCParks.myState(true); await load(); redraw(); } };
      $('trPk').onclick = () => { AP.go('station'); const c = $('pkState'); if (c) c.scrollIntoView({ block: 'center' }); }; return; }
    $('trList').innerHTML = L.slice(0, N).map(x => { const cl = G.KPCAlerts && KPCAlerts.closuresFor ? KPCAlerts.closuresFor(x.p.ref) : [];
      return `<div class="trp${PICK === x.p.ref ? ' pick' : ''}" data-trp="${esc(x.p.ref)}"><div><b>${esc(x.p.ref)}</b> ${esc(x.p.name)}<small>${esc(x.p.co || '')}${x.p.co ? ' · ' : ''}${esc(olTxt(x))}${T.near && ME ? ' · ' + dist(x.km) : ''}${activated(x.p.ref) ? ' · ✔ activated by me' : ''}${cl.length ? ' · <span class="bad">⚠ closure notice</span>' : ''}</small></div>
        <button type="button" class="chip sm${inTrip(x.p.ref) ? ' on' : ''}" data-tradd="${esc(x.p.ref)}">${inTrip(x.p.ref) ? '✓ IN TRIP' : '+ ADD'}</button></div>`; }).join('');
  }
  function legs() { const out = []; let tot = 0; for (let i = 1; i < T.stops.length; i++) { const k = km(T.stops[i - 1], T.stops[i]); out.push(k); tot += k; } return { out, tot }; }
  function drawTrip() {
    const S = T.stops, lg = legs();
    $('trTrip').innerHTML = `<h2>🚗 The trip <small class="cxsub">${S.length} stop${S.length === 1 ? '' : 's'}${S.length > 1 ? ' · ' + dist(lg.tot) + ' in a straight line (roads are longer)' : ''}</small></h2>
      ${S.length ? '<ol class="trstops">' + S.map((s, i) => `<li><span class="trn">${i + 1}</span><div><b>${esc(s.ref)}</b> ${esc(s.name)}${i ? '<small>' + dist(lg.out[i - 1]) + ' from the stop before</small>' : ''}</div>
        <span class="trbtn"><button type="button" class="chip sm" data-trup="${i}" aria-label="Move up">↑</button><button type="button" class="chip sm" data-trdn="${i}" aria-label="Move down">↓</button><button type="button" class="chip sm gold" data-trgo="${i}" title="This park becomes MY PARK and the log starts">🌲 START HERE</button><button type="button" class="chip sm" data-trrm="${i}" aria-label="Remove">✕</button></span></li>`).join('') + '</ol>'
      : '<p class="hint">Add parks from the list (+ ADD), or tap a park on the map.</p>'}
      ${S.length ? `<div class="row wrap"><button type="button" class="b sm" id="trOrder">⚡ NEAREST-NEXT ORDER</button><button type="button" class="b sm gold" id="trDir">🧭 DIRECTIONS</button><button type="button" class="b sm" id="trGpx">⬇ GPX</button><button type="button" class="b sm" id="trCsv">⬇ CSV</button><button type="button" class="b sm" id="trShare">📤 SHARE</button><button type="button" class="b sm" id="trClr">CLEAR</button></div>` : ''}`;
    if (!S.length) return;
    $('trOrder').onclick = order; $('trDir').onclick = directions; $('trGpx').onclick = gpx; $('trCsv').onclick = csv; $('trShare').onclick = share;
    $('trClr').onclick = () => { AP.sheet('Clear the trip?', '<div class="row"><button type="button" class="b halt" id="trClrGo">CLEAR ALL STOPS</button></div>'); $('trClrGo').onclick = () => { T.stops = []; save(); AP.shut(); redraw(); }; };
  }
  function drawMap() {
    if (!MAP) {
      MAP = KPCMap.create($('trCv'), { sat: T.sat, draw(ctx, P, z, o) {
        const L = found(), S = T.stops;
        ctx.lineJoin = 'round';
        if (PICK) { const x = ALL.find(y => y.p.ref === PICK); if (x) for (const ol of x.ol) { const g = ol.g, polys = g.type === 'Polygon' ? [g.coordinates] : g.type === 'MultiPolygon' ? g.coordinates : [];
          for (const poly of polys) { ctx.beginPath(); for (const r of poly) r.forEach((c, i) => { const [px, py] = P(c[1], c[0]); if (i) ctx.lineTo(px, py); else ctx.moveTo(px, py); }); ctx.setLineDash(ol.src === 'official' ? [] : [6, 4]); ctx.lineWidth = 2.5; ctx.strokeStyle = '#E8B84A'; ctx.stroke(); ctx.setLineDash([]); } } }
        for (const x of L.slice(0, 1500)) { const [px, py] = P(x.p.la, x.p.lo); if (px < -10 || py < -10 || px > o.w + 10 || py > o.h + 10) continue;
          ctx.fillStyle = inTrip(x.p.ref) ? '#E8B84A' : x.ol.length ? '#3fb950' : '#6DB4F5'; ctx.beginPath(); ctx.arc(px, py, z >= 9 ? 4 : 3, 0, 7); ctx.fill();
          if (z >= 10) { ctx.font = '600 11px system-ui,sans-serif'; ctx.textAlign = 'center'; ctx.fillStyle = o.sat ? '#fff' : (o.dark ? '#E6EAF0' : '#1A1E24'); ctx.fillText(x.p.ref, px, py - 7); } }
        if (S.length > 1) { ctx.beginPath(); S.forEach((s, i) => { const [px, py] = P(s.la, s.lo); if (i) ctx.lineTo(px, py); else ctx.moveTo(px, py); }); ctx.strokeStyle = 'rgba(232,184,74,.9)'; ctx.lineWidth = 3; ctx.setLineDash([8, 6]); ctx.stroke(); ctx.setLineDash([]); }
        S.forEach((s, i) => { const [px, py] = P(s.la, s.lo); ctx.fillStyle = '#E8B84A'; ctx.strokeStyle = '#1a1206'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(px, py, 10, 0, 7); ctx.fill(); ctx.stroke();
          ctx.fillStyle = '#1a1206'; ctx.font = '800 11px system-ui,sans-serif'; ctx.textAlign = 'center'; ctx.fillText(String(i + 1), px, py + 4); });
        if (ME) { const [px, py] = P(ME.la, ME.lo); ctx.fillStyle = '#6DB4F5'; ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(px, py, 6, 0, 7); ctx.fill(); ctx.stroke(); }
      }, tap(la, lo, tx, ty) {
        let hit = null, best = 22; for (const x of found().slice(0, 1500)) { const [px, py] = MAP.P(x.p.la, x.p.lo), d = Math.hypot(px - tx, py - ty); if (d < best) { best = d; hit = x; } }
        if (!hit && G.KPCParks) hit = found().find(x => x.ol.some(ol => KPCParks.inside(la, lo, ol.g)));
        if (hit) { PICK = hit.p.ref; drawList(); MAP.redraw(); const el = document.querySelector(`[data-trp="${hit.p.ref}"]`); if (el) el.scrollIntoView({ block: 'nearest' });
          AP.toast(`<b>${esc(hit.p.ref)}</b> ${esc(hit.p.name)} · ${esc(olTxt(hit))}${inTrip(hit.p.ref) ? '' : ' · <u>tap + ADD in the list</u>'}`, 3500); }
      } });
      fit();
    }
    MAP.redraw();
  }
  /* fit to where most of them are (one stray pin must not zoom the whole map out): the 3rd to 97th percentile */
  function fit() {
    if (!MAP) return; let pts = T.stops.length ? T.stops.map(s => [s.la, s.lo]) : found().map(x => [x.p.la, x.p.lo]); if (ME && T.near) pts.push([ME.la, ME.lo]);
    if (pts.length > 10) { const q = (a, f) => { const b = a.slice().sort((x, y) => x - y); return b[Math.round(f * (b.length - 1))]; }, la = pts.map(p => p[0]), lo = pts.map(p => p[1]); pts = [[q(la, .03), q(lo, .03)], [q(la, .97), q(lo, .97)]]; }
    if (pts.length) MAP.fit(pts);
  }
  function redraw() { drawTrip(); drawList(); if (MAP) MAP.redraw(); $('trNear').classList.toggle('on', T.near); $('trMine').classList.toggle('on', T.notMine); $('trSat').textContent = T.sat ? '🗺 PLAIN' : '🛰 SATELLITE'; }

  /* ---------------- actions ---------------- */
  function add(ref) {
    const x = ALL.find(y => y.p.ref === ref); if (!x) return;
    if (inTrip(ref)) { T.stops = T.stops.filter(s => s.ref !== ref); AP.toast(esc(ref) + ' taken out of the trip.', 1500); }
    else { const ap = x.p.ap && x.p.ap[0]; T.stops.push({ ref, name: x.p.name, la: x.p.la, lo: x.p.lo, go: ap ? [ap[0], ap[1]] : null }); AP.toast('🚗 ' + esc(ref) + ' added: stop ' + T.stops.length + '.', 1500, 'log'); }
    save(); redraw();
  }
  function order() {
    const from = ME || T.stops[0], left = T.stops.slice(), out = []; let at = from;
    while (left.length) { let bi = 0, bd = 1e9; left.forEach((s, i) => { const d = km(at, s); if (d < bd) { bd = d; bi = i; } }); at = left.splice(bi, 1)[0]; out.push(at); }
    T.stops = out; save(); redraw(); fit(); AP.toast('⚡ Re-ordered: nearest next' + (ME ? ', starting from where you are.' : ', starting from stop 1.'), 2500);
  }
  const ll = s => s.go ? s.go[0] + ',' + s.go[1] : s.la + ',' + s.lo;   /* an access point (parking) when the pack has one */
  function directions() {
    const S = T.stops; if (!S.length) return;
    const dest = ll(S[S.length - 1]), way = S.slice(0, -1).slice(0, 9).map(ll).join('|');
    const url = 'https://www.google.com/maps/dir/?api=1' + (ME ? '&origin=' + ME.la + ',' + ME.lo : '') + '&destination=' + dest + (way ? '&waypoints=' + encodeURIComponent(way) : '') + '&travelmode=driving';
    G.open(url, '_blank'); if (S.length > 10) AP.toast('The maps app takes 10 stops at a time: the first 10 are in.', 4000);
  }
  function gpx() {
    const x = s => String(s).replace(/[<&>"]/g, c => ({ '<': '&lt;', '&': '&amp;', '>': '&gt;', '"': '&quot;' }[c]));
    const body = '<?xml version="1.0" encoding="UTF-8"?>\n<gpx version="1.1" creator="KPC app" xmlns="http://www.topografix.com/GPX/1/1">\n' +
      T.stops.map(s => `  <wpt lat="${s.la}" lon="${s.lo}"><name>${x(s.ref)}</name><desc>${x(s.name)}</desc></wpt>`).join('\n') +
      '\n  <rte><name>KPC trip</name>\n' + T.stops.map(s => `    <rtept lat="${s.la}" lon="${s.lo}"><name>${x(s.ref)}</name></rtept>`).join('\n') + '\n  </rte>\n</gpx>\n';
    AP.saveFile(body, 'KPC-trip-' + new Date().toISOString().slice(0, 10) + '.gpx', 'application/gpx+xml');
  }
  function csv() {
    const q = v => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
    const body = 'stop,park,name,lat,lon\n' + T.stops.map((s, i) => [i + 1, s.ref, s.name, s.la, s.lo].map(q).join(',')).join('\n') + '\n';
    AP.saveFile(body, 'KPC-trip-' + new Date().toISOString().slice(0, 10) + '.csv', 'text/csv');
  }
  async function share() {
    const txt = 'My POTA trip (KPC app):\n' + T.stops.map((s, i) => (i + 1) + '. ' + s.ref + ' ' + s.name).join('\n');
    try { if (navigator.share) { await navigator.share({ title: 'KPC trip', text: txt }); return; } } catch (e) { return; }
    try { await navigator.clipboard.writeText(txt); AP.toast('📋 The trip is copied: paste it anywhere.', 2500, 'log'); } catch (e) { AP.toast('Could not share here.', 2500, 'bad'); }
  }
  function startHere(i) {
    const s = T.stops[i]; if (!s) return;
    AP.S.ref = s.ref; AP.S.role = 'act'; AP.save(); const r = $('stRef'); if (r) r.value = s.ref; AP.fire('me');
    AP.toast('🌲 MY PARK = ' + esc(s.ref) + ' (' + esc(s.name) + '). Logging as the activator.' + (T.stops[i + 1] ? ' Next stop: ' + esc(T.stops[i + 1].ref) + '.' : ''), 5000, 'log');
    AP.go('log');
  }
  async function near() {
    if (T.near) { T.near = false; save(); redraw(); return; }
    try { const p = await AP.gps({ maxAge: 60000, ms: 10000 }); ME = { la: p.la, lo: p.lo }; }
    catch (e) { const g = AP.gridLL && AP.gridLL(AP.myGrid()); if (g) { ME = { la: g.la, lo: g.lo }; AP.toast('No GPS here: using the middle of your grid square ' + esc(AP.myGrid()) + '.', 3000); } else { AP.toast('📍 ' + esc(e.message || e), 4000, 'bad'); return; } }
    T.near = true; if (G.KPCParks && ME) { const st = KPCParks.stateNear(ME.la, ME.lo); if (st && PACKS.some(pk => pk.state === st)) T.st = st; $('trSt').value = T.st; }
    save(); redraw(); if (MAP) MAP.view(ME.la, ME.lo, 9);
  }
  $('trBox').addEventListener('click', e => {
    const a = e.target.closest('[data-tradd]'); if (a) { add(a.dataset.tradd); return; }
    const p = e.target.closest('[data-trp]'); if (p && !e.target.closest('button')) { PICK = p.dataset.trp; const x = ALL.find(y => y.p.ref === PICK); drawList(); if (x && MAP) { MAP.view(x.p.la, x.p.lo, 11); } return; }
    const u = e.target.closest('[data-trup]'); if (u) { const i = +u.dataset.trup; if (i > 0) { [T.stops[i - 1], T.stops[i]] = [T.stops[i], T.stops[i - 1]]; save(); redraw(); } return; }
    const d = e.target.closest('[data-trdn]'); if (d) { const i = +d.dataset.trdn; if (i < T.stops.length - 1) { [T.stops[i + 1], T.stops[i]] = [T.stops[i], T.stops[i + 1]]; save(); redraw(); } return; }
    const r = e.target.closest('[data-trrm]'); if (r) { T.stops.splice(+r.dataset.trrm, 1); save(); redraw(); return; }
    const g = e.target.closest('[data-trgo]'); if (g) { startHere(+g.dataset.trgo); return; }
  });
  $('trSt').onchange = () => { T.st = $('trSt').value; save(); redraw(); fit(); };
  let qT = 0; $('trQ').oninput = () => { clearTimeout(qT); qT = setTimeout(() => { T.q = $('trQ').value; save(); drawList(); if (MAP) MAP.redraw(); }, 200); };
  $('trNear').onclick = near;
  $('trMine').onclick = () => { T.notMine = !T.notMine; save(); redraw(); };
  $('trSat').onclick = () => { T.sat = !T.sat; save(); if (MAP) MAP.sat(T.sat); redraw(); };
  let opened = false;
  async function open() { await load(); $('trQ').value = T.q; redraw(); setTimeout(() => { drawMap(); if (!opened) { opened = true; fit(); } }, 30); }

  if (!$('kpcTripCss')) document.head.insertAdjacentHTML('beforeend', `<style id="kpcTripCss">
#mpSub{display:flex;gap:6px;margin:0 0 8px}#mpSub button{flex:1;height:38px;border-radius:12px;border:1px solid var(--line);background:var(--panel2);color:var(--sub);font:800 12px var(--sans);letter-spacing:.12em}
#mpSub button.on{background:linear-gradient(180deg,#f6d58a,#d5a63a);color:var(--onGold);border-color:var(--gold)}
#scrMap[data-sub=trip]>*:not(#mpSub):not(#trBox){display:none!important}#scrMap:not([data-sub=trip]) #trBox{display:none}
.trbar{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:0 0 8px}.trbar select,.trbar input{height:38px;border-radius:10px;border:1px solid var(--line);background:var(--panel2);color:var(--text);padding:0 10px;font:inherit}.trbar input{flex:1 1 180px;min-width:0}
.trwrap{display:grid;gap:10px}.trmap canvas{display:block;width:100%;height:min(46vh,420px);border-radius:12px;border:1px solid var(--line)}
@media (min-width:1000px){.trwrap{grid-template-columns:minmax(0,1fr) 420px}.trmap canvas{height:calc(100vh - 230px)}.trside{max-height:calc(100vh - 230px);overflow:auto}}
.trlist{display:flex;flex-direction:column;gap:4px}.trp{display:flex;align-items:center;gap:8px;justify-content:space-between;padding:8px 10px;border-radius:10px;background:var(--panel);border:1px solid var(--line);cursor:pointer}
.trp.pick{border-color:var(--gold)}.trp small{display:block;color:var(--sub);font-size:11px}.trp .bad{color:var(--red)}
.trstops{list-style:none;margin:0 0 8px;padding:0;display:flex;flex-direction:column;gap:6px}.trstops li{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.trstops li>div{flex:1 1 140px;min-width:0}.trstops small{display:block;color:var(--sub);font-size:11px}
.trn{width:26px;height:26px;border-radius:50%;background:#E8B84A;color:#1a1206;font:800 12px var(--sans);display:flex;align-items:center;justify-content:center;flex:0 0 auto}.trbtn{display:flex;gap:4px;flex-wrap:wrap}
.row.wrap{flex-wrap:wrap}
</style>`);
  sub(SUB === 'trip' ? 'trip' : 'qso');
  AP.on('screen', n => { if (n === 'map' && SUB === 'trip') open(); });
  G.KPCTrip = { T, open, sub, add, order, startHere, legs, found: () => found(), load, _me: v => { ME = v; } };
})(window);
