/* KPC Activation Kit (kpc-kit.html, NOT linked yet: Brandon is trying it first).
   Pick a Kentucky POTA park -> one screen: heads-up reports and tips, weather, boundary map with parking/trailheads,
   2-fers and other programs, where to stay, and a Spot Me button. SAVE FOR OFFLINE keeps it on the phone.
   Uses kpc-bounds.js (window.KPCB). ?ref=US-1234 opens a park. */
(function () {
  'use strict';
  const B = window.KPCB, $ = id => document.getElementById(id), esc = B.esc;
  const APP = 'kpc-finder-v1', TILES = 'kpc-tiles-v1'; /* same caches as Park Commander (kpc-finder-sw.js); never rename */
  const SAVEKEY = 'kpcKitSaved';
  const store = { get: k => { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } }, set: (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  let D = null, CONDS = null, NOTES = null, CAMP = null, map = null, cur = null, geo = null;
  const j = u => fetch(u).then(r => r.ok ? r.json() : null).catch(() => null);
  const name = c => { if (!D) return ''; const x = D.parks.find(p => p.c === c) || D.kff.find(p => p.c === c) || D.summits.find(p => p.c === c); return x ? x.n : ''; };

  if ('serviceWorker' in navigator && window.isSecureContext) navigator.serviceWorker.register('kpc-finder-sw.js').catch(() => {});

  async function load() {
    [D, CONDS, NOTES, CAMP] = await Promise.all([j('kpc-ky-data.json'), j('kpc-conditions.json'), j('kpc-park-notes.json'), j('kpc-campgrounds.json')]);
    if (!D) { $('kitOut').innerHTML = '<p class="kit-msg">Could not load the park list. Check your signal.</p>'; return; }
    $('kitList').innerHTML = D.parks.slice().sort((a, b) => a.n.localeCompare(b.n)).map(p => `<option value="${esc(p.c)}">${esc(p.n)}</option>`).join('');
    const saved = store.get(SAVEKEY) || {};
    const keys = Object.keys(saved);
    $('kitSaved').innerHTML = keys.length ? 'Saved on this phone: ' + keys.map(r => `<a href="?ref=${encodeURIComponent(r)}" data-ref="${esc(r)}">${esc(r)} ${esc(name(r))}</a>`).join(' · ') : '';
    const r0 = new URLSearchParams(location.search).get('ref');
    if (r0) open(r0.toUpperCase());
  }
  function pick(q) {
    q = String(q || '').trim(); if (!q) return;
    const up = q.toUpperCase(), m = up.match(/^(?:US-)?(\d{3,5})$/);
    let p = D.parks.find(x => x.c === up) || (m && D.parks.find(x => x.c === 'US-' + m[1].padStart(4, '0')));
    if (!p) { const l = q.toLowerCase(); const hits = D.parks.filter(x => x.n.toLowerCase().includes(l)); if (hits.length === 1) p = hits[0]; else if (hits.length) { $('kitPick').innerHTML = hits.slice(0, 12).map(x => `<button type="button" data-ref="${x.c}"><b>${esc(x.n)}</b><span>${x.c} ›</span></button>`).join(''); return; } }
    if (!p) { $('kitPick').innerHTML = '<p class="kit-msg">No Kentucky POTA park matches that. Try part of the name or the number.</p>'; return; }
    open(p.c);
  }
  function near() {
    if (!navigator.geolocation) return;
    $('kitPick').innerHTML = '<p class="kit-msg">Getting your location…</p>';
    navigator.geolocation.getCurrentPosition(pos => {
      const la = pos.coords.latitude, lo = pos.coords.longitude;
      const L = D.parks.map(p => ({ p, d: B.km(la, lo, p.la, p.lo) })).sort((a, b) => a.d - b.d).slice(0, 8);
      $('kitPick').innerHTML = L.map(x => `<button type="button" data-ref="${x.p.c}"><b>${esc(x.p.n)}</b><span>${B.dist(x.d)} · ${x.p.c} ›</span></button>`).join('');
    }, () => { $('kitPick').innerHTML = '<p class="kit-msg">Could not get your location. Type the park instead.</p>'; }, { enableHighAccuracy: false, timeout: 15000, maximumAge: 60000 });
  }

  /* ---------- the kit ---------- */
  async function open(ref) {
    const p = D.parks.find(x => x.c === ref); if (!p) return;
    cur = p; $('kitPick').innerHTML = ''; $('kitQ').value = '';
    history.replaceState(null, '', '?ref=' + encodeURIComponent(ref));
    const also = (p.kff || []).concat(p.sota || []), rel = [ref].concat(also);
    const now = Date.now();
    const conds = (CONDS && CONDS.items || []).filter(c => rel.includes(c.ref) && (!c.expires || Date.parse(c.expires) > now));
    const notes = (NOTES && NOTES.notes || []).filter(n => rel.includes(n.ref)).slice(-3).reverse();
    const cg = (CAMP && CAMP.parks || []).find(x => x.pota === ref);
    const saved = (store.get(SAVEKEY) || {})[ref];
    const g = 'https://www.google.com/maps/dir/?api=1&destination=';
    $('kitOut').innerHTML = `
<section class="kit-head"><div class="kit-ref">${esc(p.c)}${also.length ? ' · also ' + also.map(esc).join(' · ') : ''}</div><h2>${esc(p.n)}</h2><p>${esc([p.co ? p.co + ' County' : '', p.t].filter(Boolean).join(' · '))}</p>
<div class="kit-btns"><a class="gold" href="${g}${p.la},${p.lo}" target="_blank" rel="noopener">DIRECTIONS ↗</a>${p.off ? `<a href="${esc(p.off)}" target="_blank" rel="noopener">OFFICIAL MAP ↗</a>` : ''}${p.web && p.web !== p.off ? `<a href="${esc(p.web)}" target="_blank" rel="noopener">WEBSITE ↗</a>` : ''}<a href="https://pota.app/#/park/${esc(p.c)}" target="_blank" rel="noopener">POTA PAGE ↗</a></div></section>
<a class="kit-spot" href="kpc-spot-me.html?pota=${encodeURIComponent(p.c)}${p.kff && p.kff[0] ? '&wwff=' + encodeURIComponent(p.kff[0]) : ''}">📣 SPOT ME AT ${esc(p.c)} ›</a>
<section class="kit-sec"><h3>⚠ HEADS UP</h3>${conds.length ? conds.map(c => `<div class="kit-alert"><b>${esc(c.kind)}</b>${c.details ? ' · ' + esc(c.details) : ''}<span>Reported ${esc(c.seen || '')}${c.call ? ' by ' + esc(c.call) : ''}${c.ref !== ref ? ' (for ' + esc(c.ref) + ')' : ''}</span></div>`).join('') : '<p>No closures or problems reported by members in the last 30 days.</p>'}
${notes.length ? '<h4>Latest member tips</h4>' + notes.map(n => `<div class="kit-note">${esc(n.text)}<span>${esc(n.type || 'Tip')} · ${esc(n.call || '')} · ${esc(n.date || '')}</span></div>`).join('') : ''}
<div class="kit-btns"><a class="alt" href="kpc-park-notes.html?ref=${encodeURIComponent(ref)}">ALL PARK NOTES ›</a>${CAMP && CAMP.closures ? `<a class="alt" href="${esc(CAMP.closures.url)}" target="_blank" rel="noopener">STATE PARK CLOSURES ↗</a>` : ''}</div></section>
<section class="kit-sec"><h3>☁ WEATHER</h3><div id="kitWx">${saved && saved.wx ? '' : 'Loading the forecast…'}</div><div class="kit-btns"><a class="alt" href="kpc-weather.html?ref=${encodeURIComponent(ref)}">FULL FIELD WEATHER ›</a></div></section>
<section class="kit-sec"><h3>🗺 MAP: BOUNDARY, PARKING &amp; TRAILHEADS</h3><div id="kitMap"></div><p class="kit-small" id="kitBnd">Loading the boundary…</p>
<div class="kit-btns"><a class="gold" href="kpc-in-park.html?ref=${encodeURIComponent(ref)}">📍 AM I IN THE PARK? ›</a></div><div class="kit-btns" id="kitFiles"></div></section>
<section class="kit-sec"><h3>➕ MORE REFERENCES HERE</h3>${multi(p)}</section>
<section class="kit-sec"><h3>⛺ WHERE TO STAY</h3>${stay(p, cg)}</section>
<section class="kit-sec kit-off"><h3>📴 SAVE FOR NO SIGNAL</h3><p>Saves this kit, the boundary, the map around the park and today's forecast on this phone, so it opens at the park with no signal. Weather and spots still need signal to update.</p><div class="kit-btns"><button type="button" id="kitSave" class="gold">${saved ? 'UPDATE THE SAVED COPY' : 'SAVE THIS PARK FOR OFFLINE'}</button></div><p class="kit-small" id="kitSaveMsg">${saved ? 'Saved ' + new Date(saved.t).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) + '.' : ''}</p></section>`;
    $('kitSave').onclick = () => saveOffline(p);
    drawMap(p);
    weather(p, saved);
    window.scrollTo({ top: $('kitOut').offsetTop - 70, behavior: 'smooth' });
  }
  function multi(p) {
    const tf = p.tf || [], kff = p.kff || [], so = p.sota || [];
    if (!tf.length && !kff.length && !so.length) return '<p>Just this one park here. No overlapping parks, KFF or summits.</p>';
    return (tf.length ? `<h4>Overlapping boundaries (2-fer)</h4>${tf.map(r => `<div class="kit-row"><b>${esc(r)}</b> ${esc(name(r))}</div>`).join('')}<p class="kit-small">Where the boundaries overlap, one activation counts for each park. Check you're inside every one you log.</p>` : '') +
      (kff.length || so.length ? `<h4>Also here (other programs)</h4>${kff.map(r => `<div class="kit-row"><b>${esc(r)}</b> ${esc(name(r))} <em>WWFF</em></div>`).join('')}${so.map(r => `<div class="kit-row"><b>${esc(r)}</b> ${esc(name(r))} <em>SOTA: only from the summit</em></div>`).join('')}` : '');
  }
  function stay(p, cg) {
    const card = (c, far) => `<div class="kit-row"><b>${esc(c.name)}</b>${far ? ` <em>${esc(far)}</em>` : ''}${c.status === 'closed' ? ' <em class="bad">CLOSED</em>' : ''}<span>${esc([c.sites, c.season, c.notes || c.note].filter(Boolean).join(' · '))}</span><span class="kit-l">${c.url ? `<a href="${esc(c.url)}" target="_blank" rel="noopener">INFO ↗</a>` : ''}${c.reserve ? `<a href="${esc(c.reserve)}" target="_blank" rel="noopener">RESERVE ↗</a>` : ''}</span></div>`;
    if (cg && ((cg.campgrounds || []).length || (cg.lodging || []).length)) return (cg.campgrounds || []).map(c => card(c)).join('') + (cg.lodging || []).map(c => card(c)).join('') + `<div class="kit-btns"><a class="alt" href="kpc-campgrounds.html#${encodeURIComponent(p.c)}">CAMPGROUNDS &amp; CABINS ›</a></div>`;
    const all = []; (CAMP && CAMP.parks || []).forEach(x => (x.campgrounds || []).forEach(c => { if (isFinite(c.la)) all.push({ c, x, d: B.km(p.la, p.lo, c.la, c.lo) }); }));
    const n = all.sort((a, b) => a.d - b.d).slice(0, 2);
    return '<p>No campground or cabins inside this park.' + (CAMP && CAMP.wmaRule && /WMA|Wildlife/.test(p.t + p.n) ? ' ' + esc(CAMP.wmaRule.text) : '') + '</p>' + (n.length ? '<h4>Closest campgrounds in other parks</h4>' + n.map(o => card(o.c, B.dist(o.d) + ' away (' + o.x.pota + ')')).join('') : '') + `<div class="kit-btns"><a class="alt" href="kpc-campgrounds.html">CAMPGROUNDS &amp; CABINS ›</a></div>`;
  }

  /* ---------- map ---------- */
  async function drawMap(p) {
    if (map) { map.remove(); map = null; }
    if (!window.L) { $('kitMap').innerHTML = '<p class="kit-msg">Map unavailable.</p>'; return; }
    map = L.map('kitMap').setView([p.la, p.lo], 13);
    const street = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(map);
    const sat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, attribution: 'Imagery © Esri' });
    L.control.layers({ Street: street, Satellite: sat }).addTo(map);
    L.marker([p.la, p.lo]).addTo(map).bindPopup(esc(p.c + ' ' + p.n) + '<br>POTA pin');
    const ap = p.ap || [];
    ap.forEach(a => L.circleMarker([a[0], a[1]], { radius: 7, color: '#fff', weight: 2, fillColor: '#1d5a3a', fillOpacity: 1 }).addTo(map).bindPopup(`<b>${esc(a[2])}</b><br><a href="https://www.google.com/maps/dir/?api=1&destination=${a[0]},${a[1]}" target="_blank" rel="noopener">Directions ↗</a>`));
    let feats = [];
    try { feats = await B.kyFor(p.c); } catch (e) {}
    const kpc = feats.length && feats.every(f => f._L.kpc), proc = feats.some(f => f._L.proc);
    if (!feats.length) { try { feats = await B.padusByName(p.n, p.la, p.lo); } catch (e) {} }
    const fc = { type: 'FeatureCollection', features: feats.map(f => ({ type: 'Feature', properties: { NAME: f._nm }, geometry: f.geometry })) };
    geo = feats.length ? fc : null;
    if (feats.length) {
      const lay = L.geoJSON(fc, { style: kpc ? { color: '#ffd400', weight: 3, dashArray: '12 5 2 5', fillOpacity: 0 } : { color: '#ffb000', weight: 3, fillColor: '#ffb000', fillOpacity: .12 } }).addTo(map);
      if (!proc) try { map.fitBounds(lay.getBounds(), { padding: [16, 16], maxZoom: 15 }); } catch (e) {}
      $('kitBnd').innerHTML = (kpc ? '<b>Approximate outline drawn by KPC</b> from OpenStreetMap (this park has no official map file). OpenStreetMap is drawn by volunteers, so it can be off; check the park\'s own map.' : proc ? 'Daniel Boone National Forest outer line (it includes private land).' : 'Official boundary' + (feats[0]._L ? ' from ' + [...new Set(feats.map(f => f._L.agency))].map(esc).join(' and ') : ' (USGS PAD-US)') + '.') + (ap.length ? ` Green dots: ${ap.length} parking / trailhead / entrance point${ap.length > 1 ? 's' : ''} (tap for directions).` : '');
      const o = { ref: p.c, name: p.n, la: p.la, lo: p.lo, points: ap };
      $('kitFiles').innerHTML = `<a class="alt" href="#" data-f="kml">KML · GOOGLE EARTH / MAP APPS</a><a class="alt" href="#" data-f="gpx">GPX · GARMIN / GPS UNITS</a>` + B.WHICH;
      $('kitFiles').querySelectorAll('[data-f]').forEach(b => b.onclick = e => { e.preventDefault(); B.saveGeo(fc, b.dataset.f, o, b); });
    } else $('kitBnd').innerHTML = 'No boundary file found for this park. Use the official map.' + (ap.length ? ' Green dots: parking / trailhead points.' : '');
  }

  /* ---------- weather (Open-Meteo + NWS alerts) ---------- */
  const WX = c => c >= 95 ? '⛈ Thunderstorms' : c >= 80 ? '🌦 Showers' : c >= 71 ? '🌨 Snow' : c >= 61 ? '🌧 Rain' : c >= 51 ? '🌦 Drizzle' : c >= 45 ? '🌫 Fog' : c >= 3 ? '☁ Cloudy' : c >= 1 ? '⛅ Partly cloudy' : '☀ Clear';
  async function fetchWx(p) {
    const u = `https://api.open-meteo.com/v1/forecast?latitude=${p.la}&longitude=${p.lo}&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m,wind_gusts_10m&hourly=temperature_2m,precipitation_probability,weather_code,wind_gusts_10m&forecast_hours=12&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=America%2FChicago`;
    const [w, a] = await Promise.all([j(u), fetch(`https://api.weather.gov/alerts/active?point=${p.la.toFixed(4)},${p.lo.toFixed(4)}`, { headers: { Accept: 'application/geo+json' } }).then(r => r.ok ? r.json() : null).catch(() => null)]);
    if (!w || !w.current) return null;
    return { t: Date.now(), w, alerts: a ? (a.features || []).map(f => ({ ev: f.properties.event, sev: f.properties.severity, until: f.properties.ends || f.properties.expires })) : null };
  }
  function showWx(x, old) {
    const c = x.w.current, h = x.w.hourly, rows = h.time.map((t, i) => ({ t, temp: h.temperature_2m[i], pp: h.precipitation_probability[i], wc: h.weather_code[i], g: h.wind_gusts_10m[i] }));
    const storm = rows.some(r => r.wc >= 95), maxPP = Math.max(...rows.map(r => r.pp || 0)), maxG = Math.max(...rows.map(r => r.g || 0));
    const calls = [storm ? '<b class="bad">Storms in the next 12 h: no antennas up near lightning.</b>' : '', maxG >= 25 ? `Gusts to ${Math.round(maxG)} mph: guy your mast.` : '', maxPP >= 50 ? `Rain chance up to ${maxPP}%: bring a tarp.` : ''].filter(Boolean);
    $('kitWx').innerHTML = (old ? `<p class="kit-small">Saved forecast from ${new Date(x.t).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })} (no signal right now).</p>` : '') +
      (x.alerts && x.alerts.length ? x.alerts.map(a => `<div class="kit-alert"><b>${esc(a.ev)}</b><span>${a.until ? 'until ' + new Date(a.until).toLocaleString([], { weekday: 'short', hour: 'numeric', minute: '2-digit' }) : ''}</span></div>`).join('') : x.alerts ? '<p class="kit-small">No weather alerts for this spot.</p>' : '') +
      `<div class="kit-now"><b>${Math.round(c.temperature_2m)}°F</b><span>${WX(c.weather_code)} · feels ${Math.round(c.apparent_temperature)}° · wind ${Math.round(c.wind_speed_10m)} mph, gusts ${Math.round(c.wind_gusts_10m)}</span></div>` +
      (calls.length ? `<p>${calls.join(' ')}</p>` : '<p>Looks fine for the next 12 hours.</p>') +
      `<div class="kit-hours">${rows.filter((r, i) => i % 2 === 0).map(r => `<div><span>${new Date(r.t).toLocaleTimeString([], { hour: 'numeric' })}</span><b>${Math.round(r.temp)}°</b><span>${WX(r.wc).split(' ')[0]} ${r.pp || 0}%</span></div>`).join('')}</div>`;
  }
  async function weather(p, saved) {
    if (saved && saved.wx) showWx(saved.wx, true);
    const x = await fetchWx(p);
    if (x) { showWx(x, false); const S = store.get(SAVEKEY) || {}; if (S[p.c]) { S[p.c].wx = x; S[p.c].t = S[p.c].t || x.t; store.set(SAVEKEY, S); } }
    else if (!saved || !saved.wx) $('kitWx').innerHTML = '<p class="kit-small">No forecast right now (no signal?).</p>';
  }

  /* ---------- save for offline ---------- */
  function tileList(p, bb) {
    const t = [], tx = (lo, z) => Math.floor((lo + 180) / 360 * 2 ** z), ty = (la, z) => { const r = la * Math.PI / 180; return Math.floor((1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * 2 ** z); };
    for (let z = 10; z <= 16; z++) {
      const pad = z <= 12 ? 0.08 : 0.01, x0 = tx(bb[0] - pad, z), x1 = tx(bb[2] + pad, z), y0 = ty(bb[3] + pad, z), y1 = ty(bb[1] - pad, z);
      const n = (x1 - x0 + 1) * (y1 - y0 + 1); if (t.length + n > 900) break;
      for (let x = x0; x <= x1; x++) for (let y = y0; y <= y1; y++) t.push(`https://tile.openstreetmap.org/${z}/${x}/${y}.png`);
    }
    return t;
  }
  async function saveOffline(p) {
    const msg = $('kitSaveMsg'), btn = $('kitSave');
    if (!('caches' in window)) { msg.textContent = 'This browser cannot save pages for offline.'; return; }
    btn.disabled = true; msg.textContent = 'Saving the kit…';
    try {
      const app = await caches.open(APP);
      const scripts = [...document.querySelectorAll('script[src],link[rel=stylesheet][href]')].map(e => e.src || e.href).filter(u => u.startsWith(location.origin) || /unpkg\.com\/leaflet@1\.9\.4/.test(u));
      const files = ['kpc-kit.html', 'kpc-in-park.html', 'kpc-in-park.js', 'kpc-bounds.js', 'kpc-ky-data.json', 'kpc-conditions.json', 'kpc-park-notes.json', 'kpc-campgrounds.json', 'KPC-logo.png'].concat(B.KY.map(L => L.file));
      const urls = [...new Set(files.map(f => new URL(f, location.href).href).concat(scripts).concat(['leaflet.css', 'leaflet.js', 'images/marker-icon.png', 'images/marker-icon-2x.png', 'images/marker-shadow.png', 'images/layers.png'].map(f => 'https://unpkg.com/leaflet@1.9.4/dist/' + f)))];
      let ok = 0;
      for (const u of urls) { try { const r = await fetch(u, { cache: 'reload' }); if (r.ok) { const k = new URL(u); if (k.origin === location.origin) k.search = ''; await app.put(k.href, r); ok++; } } catch (e) {} }
      const bb = geo ? geo.features.reduce((a, f) => { const b = B.bbox(f.geometry); return [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])]; }, [180, 90, -180, -90]) : [p.lo - .03, p.la - .03, p.lo + .03, p.la + .03];
      if (bb[2] - bb[0] > 0.6 || bb[3] - bb[1] > 0.6) { bb[0] = p.lo - .08; bb[2] = p.lo + .08; bb[1] = p.la - .08; bb[3] = p.la + .08; }
      const tiles = tileList(p, bb), tc = await caches.open(TILES); let done = 0;
      for (let i = 0; i < tiles.length; i += 6) {
        await Promise.all(tiles.slice(i, i + 6).map(async u => { try { if (await tc.match(u)) { done++; return; } const r = await fetch(u, { mode: 'cors' }); if (r.ok) { await tc.put(u, r); done++; } } catch (e) {} }));
        msg.textContent = `Saving the map around the park… ${Math.min(100, Math.round((i + 6) / tiles.length * 100))}%`;
      }
      const wx = await fetchWx(p);
      const S = store.get(SAVEKEY) || {}; S[p.c] = { t: Date.now(), wx: wx || (S[p.c] && S[p.c].wx) || null }; store.set(SAVEKEY, S);
      msg.innerHTML = `✓ Saved ${new Date().toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}: the kit, ${done} map pieces and today's forecast. To test it, turn on airplane mode and open this page again.`;
      btn.textContent = 'UPDATE THE SAVED COPY';
    } catch (e) { msg.textContent = 'Saving stopped: ' + (e.message || 'storage full?'); }
    btn.disabled = false;
  }

  /* ---------- start ---------- */
  $('kitForm').addEventListener('submit', e => { e.preventDefault(); pick($('kitQ').value); });
  $('kitNear').addEventListener('click', near);
  document.addEventListener('click', e => { const b = e.target.closest('#kitPick [data-ref], #kitSaved [data-ref]'); if (b) { e.preventDefault(); open(b.dataset.ref); } });
  load();
})();
