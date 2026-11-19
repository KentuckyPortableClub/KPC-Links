/* KPC app: OFFLINE PARK PACKS (Fable, Oct 22; Brandon: 'our biggest edge'). STATION → Parks: download a state once
   (Kentucky comes with every park's outline, labelled official or approximate; other states come with pins) and the app
   keeps it on the phone. AM I IN THE PARK then works from GPS with no signal; NEXT PARK lists what is close, with
   directions handed to the phone's maps app. The packs are built on the website side (.github/scripts/build_app_pack.js). */
(function (G) {
  'use strict';
  const $ = id => document.getElementById(id);
  const AP = G.KPCApp, esc = AP.esc;
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const SV = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const URL0 = 'https://kentuckyportableclub.github.io/KPC-Links/app/packs/';
  const STATES = 'AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split(' ');
  const HAVE = LS('kpcPacks', {});                          /* state → {when, parks, outlines, bytes} */
  const PK = {};                                            /* state → the pack, once read */
  let IDB = null;
  function open() { return IDB ? Promise.resolve(IDB) : new Promise(res => { if (!G.indexedDB) { res(null); return; } let r; try { r = indexedDB.open('kpc-parks', 1); } catch (e) { res(null); return; } r.onupgradeneeded = () => { r.result.createObjectStore('pack'); }; r.onsuccess = () => { IDB = r.result; res(IDB); }; r.onerror = () => res(null); }); }
  async function get(st) { if (PK[st]) return PK[st]; const db = await open(); if (!db) return null; return new Promise(res => { try { const rq = db.transaction('pack').objectStore('pack').get(st); rq.onsuccess = () => { if (rq.result) PK[st] = rq.result; res(rq.result || null); }; rq.onerror = () => res(null); } catch (e) { res(null); } }); }
  async function put(st, pack) { const db = await open(); if (!db) return false; PK[st] = pack; return new Promise(res => { try { const tx = db.transaction('pack', 'readwrite'); tx.objectStore('pack').put(pack, st); tx.oncomplete = () => res(true); tx.onerror = () => res(false); } catch (e) { res(false); } }); }
  async function del(st) { const db = await open(); delete PK[st]; delete HAVE[st]; SV('kpcPacks', HAVE); if (!db) return; await new Promise(res => { try { const tx = db.transaction('pack', 'readwrite'); tx.objectStore('pack').delete(st); tx.oncomplete = res; tx.onerror = res; } catch (e) { res(); } }); draw(); }

  /* ---------------- geometry ---------------- */
  function inRing(x, y, r) { let ins = false; for (let i = 0, j = r.length - 1; i < r.length; j = i++) { const xi = r[i][0], yi = r[i][1], xj = r[j][0], yj = r[j][1]; if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi) ins = !ins; } return ins; }
  const polys = g => g.type === 'Polygon' ? [g.coordinates] : g.type === 'MultiPolygon' ? g.coordinates : [];
  function inside(la, lo, g) { for (const p of polys(g)) { if (!p.length || !inRing(lo, la, p[0])) continue; if (p.slice(1).some(h => inRing(lo, la, h))) continue; return true; } return false; }
  function edgeKm(la, lo, g) {
    const sx = 111.195 * Math.cos(la * Math.PI / 180), sy = 111.195; let best = Infinity;
    for (const p of polys(g)) for (const r of p) for (let i = 1; i < r.length; i++) { const a = r[i - 1], b = r[i], dx = (b[0] - a[0]) * sx, dy = (b[1] - a[1]) * sy, x = (lo - a[0]) * sx, y = (la - a[1]) * sy, t = Math.max(0, Math.min(1, (x * dx + y * dy) / ((dx * dx + dy * dy) || 1))), d = Math.hypot(x - t * dx, y - t * dy); if (d < best) best = d; }
    return best;
  }
  const geo = (la1, lo1, la2, lo2) => G.KPCAX25 ? KPCAX25.geo(la1, lo1, la2, lo2) : { km: 111.195 * Math.hypot(la2 - la1, (lo2 - lo1) * Math.cos(la1 * Math.PI / 180)), deg: 0 };
  const dirOf = d => ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][Math.round(d / 45) % 8];

  /* ---------------- what is here ---------------- */
  async function loaded() { const out = []; for (const st of Object.keys(HAVE)) { const p = await get(st); if (p) out.push(p); } return out; }
  async function whereAmI(la, lo) {
    const packs = await loaded(), inside_ = [], near = [];
    for (const pk of packs) {
      for (const p of pk.parks) {
        const g = geo(la, lo, p.la, p.lo), ol = pk.outlines[p.ref] || [];
        let inn = null, edge = Infinity;
        for (const o of ol) { if (inside(la, lo, o.g)) { inn = o; break; } const e = edgeKm(la, lo, o.g); if (e < edge) edge = e; }
        if (inn) inside_.push({ ref: p.ref, name: p.name, src: inn.src, layer: inn.layer, agency: inn.agency, note: inn.note, km: g.km });
        else if (g.km < 80) near.push({ ref: p.ref, name: p.name, km: g.km, deg: g.deg, edge: ol.length ? edge : null, hasOutline: !!ol.length, ap: p.ap || [], la: p.la, lo: p.lo, kind: p.kind });
      }
    }
    near.sort((a, b) => (a.edge != null ? Math.min(a.edge, a.km) : a.km) - (b.edge != null ? Math.min(b.edge, b.km) : b.km));
    return { inside: inside_, near: near.slice(0, 15), packs: packs.map(p => p.state) };
  }
  const worked = ref => G.KPCLog ? (KPCLog.hunted ? KPCLog.hunted(ref) : [...KPCLog.all().values()].some(q => !q.d && (q.refs || []).includes(ref))) : false;   /* + my POTA hunter file */
  const activated = ref => G.KPCLog ? (KPCLog.activated ? KPCLog.activated(ref) : [...KPCLog.all().values()].some(q => !q.d && (q.myrefs || []).includes(ref))) : false;
  async function name(ref) { for (const st of Object.keys(HAVE)) { const p = await get(st); const x = p && p.parks.find(q => q.ref === ref); if (x) return x.name; } return ''; }

  /* ---------------- download ---------------- */
  async function download(st, quiet) {   /* quiet (Nov 18, the app getting your state's pack by itself): no 'Downloading…' and no red line when it fails */
    st = String(st || '').toUpperCase(); if (!STATES.includes(st)) return false;
    if (!quiet) AP.toast('Downloading ' + st + '…', 60000);
    try {
      /* Oct 22 (Brandon: the phone did not download, the PC did): the app's own HTTP first (no browser rules in the way), the page's fetch second */
      const url = URL0 + 'US-' + st + '.json?v=' + Date.now().toString(36).slice(0, 6);
      let txt = '', why = '';
      if (AP.net.canRaw()) { const r = await AP.net.raw(url, { ms: 90000 }); if (r.ok) txt = r.text; else why = r.err || ('HTTP ' + r.status); }
      if (!txt) { try { const r = await AP.net.fetch(url, {}, 90000); if (!r.ok) throw new Error('HTTP ' + r.status); txt = await r.text(); } catch (e) { throw new Error((why ? why + '; then ' : '') + (e.message || e)); } }
      let pack; try { pack = JSON.parse(txt); } catch (e) { throw new Error('the file came down broken (' + txt.length + ' bytes)'); }
      if (!pack || !pack.parks) throw new Error('not a park pack');
      await put(st, pack); HAVE[st] = { when: Date.now(), parks: pack.parks.length, outlines: Object.keys(pack.outlines || {}).length, bytes: JSON.stringify(pack).length }; SV('kpcPacks', HAVE);
      AP.toast('✅ ' + st + ' is on this device: ' + pack.parks.length + ' parks' + (HAVE[st].outlines ? ', ' + HAVE[st].outlines + ' with outlines' : ' (pins only)') + '. Works with no signal now.', 6000, 'log');
      draw(); return true;
    } catch (e) { if (quiet) { console.warn('pack (by itself, will try again later)', st, e && e.message); return false; } AP.toast('Could not download ' + st + ': ' + esc(e.message || e) + (AP.net.online() ? '' : ' (this device says it is offline)'), 8000, 'bad'); console.warn('pack', st, e); return false; }
  }

  /* ---------------- the card ---------------- */
  function draw() {
    const el = $('pkList'); if (!el) return;
    const L = Object.keys(HAVE).sort();
    el.innerHTML = L.length ? L.map(st => `<div class="op"><b>${st}</b> <i>${HAVE[st].parks} parks${HAVE[st].outlines ? ' · ' + HAVE[st].outlines + ' outlines' : ' · pins only'} · ${(HAVE[st].bytes / 1e6).toFixed(1)} MB · ${new Date(HAVE[st].when).toISOString().slice(0, 10)}</i><button type="button" class="ic sm" data-pkdel="${st}">✕</button></div>`).join('')
      : '<p class="hint">Nothing downloaded yet. Pick a state and press DOWNLOAD while you have signal; it stays on this device.</p>';
    el.querySelectorAll('[data-pkdel]').forEach(b => { b.onclick = () => del(b.dataset.pkdel); });
    const sel = $('pkState'); if (sel && !sel.options.length) sel.innerHTML = STATES.map(s => `<option value="${s}"${s === 'KY' ? ' selected' : ''}>${s}${s === 'KY' ? ' (with outlines)' : ''}</option>`).join('');
    ['pkHere', 'pkNext', 'pkMap'].forEach(id => { const b = $(id); if (b) { b.disabled = !L.length; b.title = L.length ? '' : 'Download a state first.'; } });
  }
  /* where am I: the GPS, or on a PC with none, the grid square typed in MY STATION (its centre: rough, and the answer says so) */
  const gridCenter = g => { g = String(g || '').toUpperCase(); if (g.length < 4) return null; const lon = (g.charCodeAt(0) - 65) * 20 - 180 + (+g[2]) * 2 + (g.length >= 6 ? (g.charCodeAt(4) - 65) / 12 + 1 / 24 : 1), lat = (g.charCodeAt(1) - 65) * 10 - 90 + (+g[3]) + (g.length >= 6 ? (g.charCodeAt(5) - 65) / 24 + 1 / 48 : 0.5); return { la: lat, lo: lon, acc: g.length >= 6 ? 3000 : 50000, grid: g }; };
  async function gps() { try { return await AP.gps({ maxAge: 15000 }); } catch (e) { const c = gridCenter(AP.me().grid); if (c && AP.pc) return c; throw e; } }
  async function here() {
    const box = $('pkOut'); box.hidden = false; box.className = 'st'; box.innerHTML = '📍 Finding you…';
    let pos; try { pos = await gps(); } catch (e) { box.className = 'st bad'; box.textContent = '📍 ' + e.message; return; }
    const w = await whereAmI(pos.la, pos.lo);
    const line = p => `<b>${esc(p.ref)}</b> ${esc(p.name)}`;
    if (w.inside.length) {
      box.className = 'st ok';
      box.innerHTML = w.inside.map(p => `✅ You are inside ${line(p)} — ${p.src === 'official' ? 'official outline (' + esc(p.agency || p.layer) + ')' : '<b>approximate</b> outline (' + esc(p.layer) + ')'}${p.note ? ' · ' + esc(p.note) : ''}` + (w.inside.length > 1 ? '' : '')).join('<br>') +
        `<div class="row"><button type="button" class="b gold sm" id="pkUse">USE ${esc(w.inside.map(p => p.ref).join(' '))} AS MY PARK</button></div>` +
        `<small>${pos.grid ? 'From your grid square ' + esc(pos.grid) + ' (rough: no GPS on this computer)' : 'GPS ±' + Math.round(pos.acc || 0) + ' m'} · ${pos.la.toFixed(5)}, ${pos.lo.toFixed(5)}</small>`;
      $('pkUse').onclick = () => { AP.S.ref = w.inside.map(p => p.ref).join(' '); AP.save(); $('stRef').value = AP.S.ref; AP.fire('me'); AP.toast('My park = ' + esc(AP.S.ref), 3000, 'log'); };
      return;
    }
    const n = w.near[0];
    box.className = 'st';
    box.innerHTML = n ? `🚫 Not inside any park on file. Nearest: ${line(n)}, ${n.edge != null ? AP.dist(n.edge) + ' from its line' : AP.dist(n.km) + ' from its pin (no outline on file for this state: approximate)'}, ${dirOf(n.deg)}.` + `<small>GPS ±${Math.round(pos.acc || 0)} m · packs: ${w.packs.join(', ')}</small>`
      : `🚫 No park within 50 miles in the packs you have (${w.packs.join(', ') || 'none'}). Download the state you are in.`;
  }
  async function next() {
    let pos; try { pos = await gps(); } catch (e) { AP.toast('📍 ' + esc(e.message), 6000, 'bad'); return; }
    const w = await whereAmI(pos.la, pos.lo), L = w.near.filter(p => !w.inside.some(i => i.ref === p.ref)).slice(0, 12);
    AP.sheet('Next park', L.length ? `<div class="oplist">${L.map(p => { const ap = p.ap && p.ap[0], dest = ap ? ap[0] + ',' + ap[1] : p.la + ',' + p.lo, cl = G.KPCAlerts ? KPCAlerts.closuresFor(p.ref) : []; return `<div class="op"><b>${esc(p.ref)}</b> <span>${esc(p.name)}</span>${cl.length ? `<em class="bad" title="${esc(cl.map(c => c.details || c.kind).join(' · '))}"> 🚧 ${esc(String(cl[0].details || cl[0].kind || 'notice').slice(0, 70))}</em>` : ''}<i>${AP.dist(p.km)} ${dirOf(p.deg)}${p.edge != null ? ' · ' + AP.dist(p.edge) + ' to the line' : ''}${!activated(p.ref) ? ' · <b>NEW to activate</b>' : ''}${!worked(p.ref) ? ' · new to hunt' : ''}${ap ? ' · ' + esc(ap[2] || 'access point') : ''}</i><a class="ic sm" href="https://www.google.com/maps/dir/?api=1&destination=${dest}" target="_blank" rel="noopener" aria-label="Directions to ${esc(p.name)}">🧭</a></div>`; }).join('')}</div><p class="hint">🧭 opens directions in your maps app (to the access point when one is on file). Distances are straight lines.</p>`
      : '<p class="hint">No other park within 50 miles in the packs you have.</p>');
  }
  /* ---------------- the parks map (Brandon Oct 22: 'off line maps… no way to see them?') ----------------
     Everything downloaded, drawn on the device: outlines (solid = official, dashed = approximate), pins, me. Works with
     no signal; with signal, satellite pictures go underneath (the 🛰 button). Tap a park for what it is. */
  async function mapView() {
    const packs = await loaded();
    if (!packs.length) { AP.toast('Download a state first (DOWNLOAD, while you have signal).', 4000, 'bad'); return; }
    let sat = LS('kpcPkSat', false), me = null, pick = null;
    AP.sheet('Parks on this device', `<div class="pkmap"><canvas id="pkCv" aria-label="Map of the parks on this device"></canvas>
      <div class="pkbar"><button type="button" class="chip" id="pkSat">${sat ? '🗺 PLAIN' : '🛰 SATELLITE + STREETS'}</button><button type="button" class="chip" id="pkMe">📍 ME</button><span class="hint" id="pkCnt"></span></div></div>
      <div class="st" id="pkInfo">Tap a park. Solid line = official outline, dashed = approximate (not official), dot = a park with no outline on file.</div>`);
    const cv = $('pkCv'), all = packs.flatMap(pk => pk.parks.map(pp => ({ p: pp, ol: (pk.outlines || {})[pp.ref] || [] })));
    $('pkCnt').textContent = all.length + ' parks · ' + packs.map(pk => pk.state).join(' ');
    const m = G.KPCMap.create(cv, { sat, draw(ctx, P, z, o) {
      ctx.lineJoin = 'round';
      for (const x of all) for (const ol of x.ol) for (const poly of polys(ol.g)) {
        ctx.beginPath(); for (const r of poly) r.forEach((c, i) => { const [px, py] = P(c[1], c[0]); if (i) ctx.lineTo(px, py); else ctx.moveTo(px, py); });
        const off = ol.src !== 'official', on = pick && pick.p.ref === x.p.ref;
        if (on) { ctx.fillStyle = 'rgba(232,184,74,.22)'; ctx.fill('evenodd'); }   /* Brandon Oct 22: 'remove shading on the maps' — lines only (the picked park is lit) */
        ctx.setLineDash(off ? [6, 4] : []); ctx.lineWidth = on ? 3 : 2; ctx.strokeStyle = on ? '#E8B84A' : off ? '#ffaa3c' : '#3fb950'; ctx.stroke(); ctx.setLineDash([]);
      }
      ctx.font = '600 11px system-ui, sans-serif'; ctx.textAlign = 'center';
      for (const x of all) {
        const [px, py] = P(x.p.la, x.p.lo); if (px < -20 || py < -20 || px > o.w + 20 || py > o.h + 20) continue;
        ctx.fillStyle = x.ol.length ? '#3fb950' : '#6DB4F5'; ctx.beginPath(); ctx.arc(px, py, z >= 9 ? 4 : 3, 0, 7); ctx.fill();
        if (z >= 10) { ctx.fillStyle = o.sat ? '#fff' : (o.dark ? '#E6EAF0' : '#1A1E24'); ctx.fillText(x.p.ref, px, py - 7); }
      }
      if (me) { const [px, py] = P(me.la, me.lo); ctx.fillStyle = '#E8B84A'; ctx.strokeStyle = '#000'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(px, py, 6, 0, 7); ctx.fill(); ctx.stroke(); }
    }, tap(la, lo, tx, ty) {
      let hit = all.find(x => x.ol.some(ol => inside(la, lo, ol.g)));
      if (!hit) { let best = 24; for (const x of all) { const [px, py] = m.P(x.p.la, x.p.lo), d = Math.hypot(px - tx, py - ty); if (d < best) { best = d; hit = x; } } }
      pick = hit || null; m.redraw(); info();
    } });
    function info() {
      const el = $('pkInfo'); if (!el) return;
      if (!pick) { el.textContent = 'Tap a park.'; return; }
      const p = pick.p, ol = pick.ol[0], ap = p.ap && p.ap[0], dest = ap ? ap[0] + ',' + ap[1] : p.la + ',' + p.lo;
      const g = me ? geo(me.la, me.lo, p.la, p.lo) : null;
      el.innerHTML = `<b>${esc(p.ref)}</b> ${esc(p.name)}<br><small>${ol ? (ol.src === 'official' ? '✅ official outline' + (ol.agency ? ' (' + esc(ol.agency) + ')' : '') : '⚠ <b>approximate outline, not official</b>' + (ol.layer ? ' (' + esc(ol.layer) + ')' : '')) : 'no outline on file: the pin is where the program puts it'}${g ? ' · ' + AP.dist(g.km) + ' ' + dirOf(g.deg) : ''}${!activated(p.ref) ? ' · NEW to activate' : ''}${!worked(p.ref) ? ' · new to hunt' : ''}</small>
        <div class="row"><button type="button" class="b gold sm" id="pkMine">USE AS MY PARK</button><a class="b sm" href="https://www.google.com/maps/dir/?api=1&destination=${dest}" target="_blank" rel="noopener">🧭 DIRECTIONS</a></div>`;
      $('pkMine').onclick = () => { AP.S.ref = p.ref; AP.save(); const r = $('stRef'); if (r) r.value = AP.S.ref; AP.fire('me'); AP.toast('My park = ' + esc(p.ref), 3000, 'log'); };
    }
    /* fit to where most parks are (one stray pin must not zoom the whole map out) */
    const q = (a, f) => { const b = a.slice().sort((x, y) => x - y); return b[Math.min(b.length - 1, Math.max(0, Math.round(f * (b.length - 1))))]; };
    const las = all.map(x => x.p.la).filter(isFinite), los = all.map(x => x.p.lo).filter(isFinite);
    m.fit(las.length > 10 ? [[q(las, .03), q(los, .03)], [q(las, .97), q(los, .97)]] : all.map(x => [x.p.la, x.p.lo]));
    $('pkSat').onclick = () => { sat = !m.sat(); m.sat(sat); SV('kpcPkSat', sat); $('pkSat').textContent = sat ? '🗺 PLAIN' : '🛰 SATELLITE + STREETS'; if (sat && !AP.net.online()) AP.toast('No signal: satellite pictures need the internet. The outlines still show.', 4000); };
    $('pkMe').onclick = async () => { try { me = await gps(); m.view(me.la, me.lo, 12); info(); } catch (e) { AP.toast('📍 ' + esc(e.message), 5000, 'bad'); } };
    gps().then(p0 => { me = p0; m.redraw(); }).catch(() => {});
  }
  const b4 = $('pkMap'); if (b4) b4.onclick = mapView;

  /* ---------------- Nov 18 (Brandon: 'does our app update the park list and is it available offline?') ----------------
     KEEP UP TO DATE: about once a day, with signal, each downloaded state is asked again WITHOUT downloading it when it has not
     changed (the website's ETag: '304 not changed' costs a few bytes); a changed state is downloaded again quietly. Everything
     stays on the device for no signal. MY STATE: the first time the app has signal and no state on the device, it downloads
     the state you are in (GPS, else your grid) by itself. */
  const ST_C = { AL: [32.8, -86.8], AK: [61.4, -152.3], AZ: [34.2, -111.7], AR: [34.9, -92.4], CA: [37.2, -119.5], CO: [39.0, -105.5], CT: [41.6, -72.7], DE: [39.0, -75.5], DC: [38.9, -77.0], FL: [28.6, -82.4],
    GA: [32.7, -83.4], HI: [20.8, -156.3], ID: [44.4, -114.6], IL: [40.0, -89.2], IN: [39.9, -86.3], IA: [42.1, -93.5], KS: [38.5, -98.4], KY: [37.5, -85.3], LA: [31.1, -92.0], ME: [45.4, -69.2],
    MD: [39.0, -76.8], MA: [42.3, -71.8], MI: [44.3, -85.4], MN: [46.3, -94.3], MS: [32.7, -89.7], MO: [38.4, -92.5], MT: [47.0, -109.6], NE: [41.5, -99.8], NV: [39.3, -116.6], NH: [43.7, -71.6],
    NJ: [40.2, -74.7], NM: [34.4, -106.1], NY: [42.9, -75.5], NC: [35.6, -79.4], ND: [47.5, -100.5], OH: [40.3, -82.8], OK: [35.6, -97.5], OR: [43.9, -120.6], PA: [40.9, -77.8], RI: [41.7, -71.5],
    SC: [33.9, -80.9], SD: [44.4, -100.2], TN: [35.9, -86.4], TX: [31.5, -99.3], UT: [39.3, -111.7], VT: [44.1, -72.7], VA: [37.5, -78.9], WA: [47.4, -120.5], WV: [38.6, -80.6], WI: [44.6, -89.9], WY: [43.0, -107.6] };
  const stateNear = (la, lo) => { let b = '', bd = 1e9; for (const [k, c] of Object.entries(ST_C)) { const d = (c[0] - la) ** 2 + ((c[1] - lo) * Math.cos(la * Math.PI / 180)) ** 2; if (d < bd) { bd = d; b = k; } } return b; };
  const hdr = (h, k) => { if (!h) return ''; for (const n in h) if (n.toLowerCase() === k) return h[n]; return ''; };
  const RF = LS('kpcPacksRf', { at: 0, etag: {}, auto: '' });
  async function refresh(force) {
    if (!AP.net.online() || !AP.net.canRaw || !AP.net.canRaw()) return { checked: 0, updated: [] };
    if (!force && Date.now() - (RF.at || 0) < 20 * 3600000) return { checked: 0, updated: [] };
    RF.at = Date.now(); SV('kpcPacksRf', RF);
    const out = { checked: 0, updated: [] };
    for (const st of Object.keys(HAVE)) {
      try {
        const url = URL0 + 'US-' + st + '.json', h = RF.etag[st] ? { 'if-none-match': RF.etag[st] } : {};
        const r = await AP.net.raw(url, { ms: 90000, headers: h }); out.checked++;
        if (r.status === 304) continue;
        if (!r.ok) continue;
        const et = hdr(r.headers, 'etag'); let pack = null; try { pack = JSON.parse(r.text); } catch (e) {}
        if (!pack || !pack.parks) continue;
        const old = await get(st);
        if (et) RF.etag[st] = et;
        if (old && old.updated === pack.updated && old.parks.length === pack.parks.length && JSON.stringify(old).length === r.text.length) continue;
        await put(st, pack); HAVE[st] = { when: Date.now(), parks: pack.parks.length, outlines: Object.keys(pack.outlines || {}).length, bytes: r.text.length }; SV('kpcPacks', HAVE); out.updated.push(st);
      } catch (e) {}
    }
    SV('kpcPacksRf', RF); draw();
    if (out.updated.length) AP.toast('🌲 Park list updated from the KPC website: ' + out.updated.join(', ') + '. Works with no signal.', 4000, 'log');
    return out;
  }
  /* Nov 18 (Opus, Fable's start-up find): with no internet the app said 'Getting the parks of KY…' and then a red 'Could not download
     KY: Failed to fetch' at start-up, and never tried again (it marked KY as done before the download). By itself it is now quiet: it
     says something only when the parks are on the device, and tries again when the signal comes back (and once an hour). Pressing
     GET MY STATE'S PARKS (user = true) still says what happened. */
  /* Fable (merge, 0.9.10): (1) a device that started 0.9.9 or older with no signal is still marked done with no pack on it: un-mark it
     once, so it gets its parks by itself after the update; (2) the button says so when the device is offline (it said nothing);
     (3) a failed look for my state never stops the hourly refresh of the packs that are there. */
  if (!RF.fix1) { if (RF.auto && !Object.keys(HAVE).length) RF.auto = ''; RF.fix1 = 1; SV('kpcPacksRf', RF); }
  let MYBUSY = false;
  async function myState(user) {
    if (user && !AP.net.online() && !Object.keys(HAVE).length) { AP.toast('📵 No internet right now. Your state\'s parks come down by themselves as soon as there is a signal.', 6000); return ''; }
    if (Object.keys(HAVE).length || (RF.auto && !user) || !AP.net.online() || MYBUSY) return '';
    MYBUSY = true;
    try {
      let p = null; try { p = await AP.gps({ maxAge: 3600000, ms: 8000 }); } catch (e) { p = gridCenter(AP.me().grid); }
      if (!p) return ''; const st = stateNear(p.la, p.lo); if (!st) return '';
      if (user) AP.toast('🌲 Getting the parks of ' + st + ' for this device (once, so they work with no signal)…', 4000);
      const ok = await download(st, !user);
      if (ok) { RF.auto = st; SV('kpcPacksRf', RF); return st; }
      return '';
    } finally { MYBUSY = false; }
  }
  setTimeout(() => { myState().catch(() => '').then(() => refresh(false)).catch(() => {}); }, 20000);
  G.addEventListener && G.addEventListener('online', () => setTimeout(() => myState().catch(() => {}), 5000));
  setInterval(() => { myState().catch(() => '').then(() => refresh(false)).catch(() => {}); }, 3600000);

  /* 📍 NEAR ME on every MY PARK NUMBER box (Nov 18, Brandon: 'when I go to enter my park number in I can select show near by and
     quickly add it'; 'No 2fer info yet'): the parks around you from the downloaded packs (the one you are inside first), tap = add.
     Works with no signal. A list right under the box, so it also works inside a sheet. */
  function nearBox(inp) {
    if (!inp || inp.dataset.near) return; inp.dataset.near = '1';
    const host = inp.closest('label') || inp;
    host.insertAdjacentHTML('afterend', '<div class="pknear"><button type="button" class="chip sm pknb">📍 NEAR ME</button><div class="pknl" hidden></div></div>');
    const box = host.nextElementSibling, btn = box.querySelector('.pknb'), list = box.querySelector('.pknl');
    btn.onclick = async () => {
      if (!list.hidden) { list.hidden = true; return; }
      list.hidden = false; list.innerHTML = '<span class="hint">📍 Finding you…</span>';
      if (!Object.keys(HAVE).length) { list.innerHTML = '<span class="hint">No parks on this device yet. </span><button type="button" class="chip sm" data-pkget>🌲 GET MY STATE\'S PARKS</button>'; list.querySelector('[data-pkget]').onclick = async () => { const st = await myState(true); if (st) btn.onclick(); }; return; }
      let pos; try { pos = await gps(); } catch (e) { pos = gridCenter(AP.me().grid); if (!pos) { list.innerHTML = '<span class="hint">📍 ' + esc(e.message || e) + ' (or put your grid in STATION → My station)</span>'; return; } }
      const w = await whereAmI(pos.la, pos.lo), L = [...w.inside.map(p => Object.assign({ in: 1 }, p)), ...w.near.filter(p => !w.inside.some(i => i.ref === p.ref))].slice(0, 12);
      if (!L.length) { list.innerHTML = '<span class="hint">No park within 50 miles in the packs on this device (' + esc(w.packs.join(', ')) + ').</span>'; return; }
      list.innerHTML = L.map(p => `<button type="button" class="chip pkn${p.in ? ' on' : ''}" data-pkadd="${esc(p.ref)}" title="${esc(p.name)}"><b>${esc(p.ref)}</b> ${esc(String(p.name || '').slice(0, 28))} · ${p.in ? 'you are here' : AP.dist(p.edge != null ? Math.min(p.edge, p.km) : p.km)}</button>`).join('');
      list.querySelectorAll('[data-pkadd]').forEach(b => { b.onclick = () => {
        const cur = String(inp.value || '').toUpperCase().split(/[\s,]+/).filter(x => /^[A-Z0-9]+-[A-Z0-9]+$/.test(x)), ref = b.dataset.pkadd;
        if (!cur.includes(ref)) cur.push(ref); inp.value = cur.join(' '); inp.dispatchEvent(new Event('input', { bubbles: true })); inp.dispatchEvent(new Event('change', { bubbles: true }));
        b.classList.add('on'); AP.toast('🌲 ' + esc(ref) + ' added.', 1500, 'log'); }; });
    };
  }
  /* 📍 AM I IN THE PARK, on LOG (Nov 18, to-do 5): while you ACTIVATE with a park number set, the phone's GPS is checked against the
     park's outline every 5 minutes: a green 📍 IN US-1234 chip, or an amber 📍 OUTSIDE US-1234 · 0.2 mi from its line (approximate
     outlines say so). Phones only (a PC has no GPS); nothing is sent anywhere. */
  async function parkCheck() {
    const strip = $('lgStrip'); if (!strip || AP.pc || AP.me().hunt || !Object.keys(HAVE).length) { const c = $('lgInPark'); if (c) c.hidden = true; return null; }
    const refs = String(AP.S.ref || '').toUpperCase().split(/[\s,]+/).filter(x => /^[A-Z0-9]+-\d+$/.test(x)); if (!refs.length) return null;
    let pos; try { pos = await AP.gps({ maxAge: 120000, ms: 10000 }); } catch (e) { return null; }
    const w = await whereAmI(pos.la, pos.lo), ins = w.inside.filter(p => refs.includes(p.ref)), near = w.near.find(p => refs.includes(p.ref));
    let c = $('lgInPark'); if (!c) { strip.insertAdjacentHTML('afterbegin', '<span class="kv inpark" id="lgInPark"></span>'); c = $('lgInPark'); }
    c.hidden = false;
    if (ins.length) { c.className = 'kv inpark ok'; c.innerHTML = '<i>📍 IN</i><b>' + esc(ins.map(p => p.ref).join(' ')) + '</b>' + (ins.some(p => p.src !== 'official') ? '<small>approx. line</small>' : ''); }
    else if (near) { c.className = 'kv inpark warn'; c.innerHTML = '<i>📍 OUTSIDE</i><b>' + esc(near.ref) + '</b><small>' + (near.edge != null ? AP.dist(near.edge) + ' from its line' : AP.dist(near.km) + ' from its pin (no outline)') + '</small>'; }
    else { c.className = 'kv inpark'; c.innerHTML = '<i>📍</i><b>' + esc(refs[0]) + '</b><small>not on this device\'s lists</small>'; }
    return { inside: ins.map(p => p.ref), near: near ? near.ref : '' };
  }
  setInterval(() => { parkCheck().catch(() => {}); }, 300000); AP.on('me', () => setTimeout(() => parkCheck().catch(() => {}), 500)); setTimeout(() => parkCheck().catch(() => {}), 8000);
  if (!$('kpcInParkCss')) document.head.insertAdjacentHTML('beforeend', '<style id="kpcInParkCss">.kv.inpark.ok b{color:var(--ok)}.kv.inpark.warn b{color:var(--gold)}.kv.inpark small{display:block;font-size:10px;color:var(--sub)}</style>');
  document.querySelectorAll('input[name="kpc-my-parks"]').forEach(nearBox);
  if (G.MutationObserver) new MutationObserver(() => document.querySelectorAll('input[name="kpc-my-parks"]:not([data-near])').forEach(nearBox)).observe(document.body, { childList: true, subtree: true });
  if (!$('kpcPkCss')) document.head.insertAdjacentHTML('beforeend', '<style id="kpcPkCss">.pknear{margin:4px 0 8px}.pknl{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}.pknl .chip{height:auto;min-height:34px;padding:6px 10px;white-space:normal;text-align:left;font-size:12px}</style>');

  const b1 = $('pkGet'), b2 = $('pkHere'), b3 = $('pkNext');
  if (b1) b1.onclick = () => download($('pkState').value);
  if (b2) b2.onclick = here;
  if (b3) b3.onclick = next;
  draw();
  G.KPCParks = { mapView, download, del, get, loaded, whereAmI, name, inside, edgeKm, have: () => HAVE, STATES, url: URL0, refresh, myState, nearBox, stateNear, parkCheck, _rf: RF };
})(window);
