/* KPC SOTA Activation Zone checker.
   Summit heights: SOTA (Kentucky from kpc-ky-data.json; other states from locations.json, loaded only on request).
   Ground heights: Copernicus DEM GLO-90 through the free Open-Meteo elevation API.
   The zone is judged DEM-to-DEM (your spot vs the top of the same model), so the model's bias mostly cancels out.
   Saved zones (localStorage "kpcAZ:<ref>") let it work with no signal on the summit. */
(function () {
'use strict';
const $ = id => document.getElementById(id);
const R = 6371000, rad = d => d * Math.PI / 180, deg = r => r * 180 / Math.PI;
const AZ = 25;               // metres
const STEP = 60, N = 4;      // grid: 9 x 9 points, 60 m apart (±240 m) + the summit point = 82 lookups in one request
const ELEV = 'https://api.open-meteo.com/v1/elevation';
const ft = m => Math.round(m * 3.28084);
const dist = (a, b) => { const dp = rad(b[0] - a[0]), dl = rad(b[1] - a[1]); const h = Math.sin(dp / 2) ** 2 + Math.cos(rad(a[0])) * Math.cos(rad(b[0])) * Math.sin(dl / 2) ** 2; return 2 * R * Math.asin(Math.sqrt(h)); };
const brg = (a, b) => { const p1 = rad(a[0]), p2 = rad(b[0]), dl = rad(b[1] - a[1]); return (deg(Math.atan2(Math.sin(dl) * Math.cos(p2), Math.cos(p1) * Math.sin(p2) - Math.sin(p1) * Math.cos(p2) * Math.cos(dl))) + 360) % 360; };
const DIRS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
const fmtD = m => m < 300 ? ft(m) + ' ft' : (m / 1609.344).toFixed(m < 16000 ? 1 : 0) + ' mi';
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const msg = t => { $('azMsg').textContent = t || ''; };

/* ---------------- summits ---------------- */
let SUM = [], allLoaded = false;            // {c, n, m (metres), la, lo}
const ky = fetch('kpc-ky-data.json').then(r => r.json()).then(d => {
  SUM = (d.summits || []).filter(s => s.c && s.la).map(s => ({ c: s.c, n: s.n, m: s.ft ? s.ft / 3.28084 : null, la: s.la, lo: s.lo, pts: s.pts }));
}).catch(() => { msg('Could not load the Kentucky summit list.'); });
async function loadAll() {
  if (allLoaded) return;
  msg('Loading every U.S. summit… (one time, about 5 MB)');
  try {
    const rows = await (await fetch('locations.json')).json();
    const have = new Set(SUM.map(s => s.c));
    rows.forEach(r => { if (r[0] === 'SOTA' && !have.has(r[1])) SUM.push({ c: r[1], n: r[2], la: r[3], lo: r[4], m: r[6] ? +r[6] : null, pts: r[7] ? +String(r[7]).replace(/\D/g, '') || null : null }); });
    allLoaded = true; msg(`${SUM.length.toLocaleString()} summits ready.`); $('azAll').hidden = true;
  } catch (e) { msg('Could not load the full summit list — check your connection.'); }
}

/* ---------------- elevation ---------------- */
async function elevations(pts) {
  const out = [];
  for (let i = 0; i < pts.length; i += 100) {
    const chunk = pts.slice(i, i + 100);
    const u = `${ELEV}?latitude=${chunk.map(p => p[0].toFixed(5)).join(',')}&longitude=${chunk.map(p => p[1].toFixed(5)).join(',')}`;
    const r = await fetch(u); if (!r.ok) throw new Error('elevation ' + r.status);
    const j = await r.json(); if (!j || !Array.isArray(j.elevation)) throw new Error('bad elevation');
    out.push(...j.elevation);
  }
  return out;
}
function gridPts(s) {
  const dLa = STEP / 111320, dLo = STEP / (111320 * Math.cos(rad(s.la))), pts = [];
  for (let i = -N; i <= N; i++) for (let j = -N; j <= N; j++) pts.push([s.la + i * dLa, s.lo + j * dLo]);
  return { pts, dLa, dLo };
}
/* zone record: top = highest model height on the summit, grid for offline lookups */
async function buildZone(s) {
  const g = gridPts(s);
  const ev = await elevations(g.pts.concat([[s.la, s.lo]]));
  const sumE = ev[ev.length - 1], grid = ev.slice(0, -1);
  // top of the hill in the model: the summit point or any grid point within ~90 m of it
  let top = sumE;
  g.pts.forEach((p, k) => { if (dist(p, [s.la, s.lo]) <= 90 && grid[k] > top) top = grid[k]; });
  const z = { c: s.c, n: s.n, m: s.m, la: s.la, lo: s.lo, top, sumE, grid, dLa: g.dLa, dLo: g.dLo, at: Date.now() };
  try { localStorage.setItem('kpcAZ:' + s.c, JSON.stringify(z)); } catch (e) {}
  return z;
}
function savedZone(c) { try { return JSON.parse(localStorage.getItem('kpcAZ:' + c) || 'null'); } catch (e) { return null; } }
/* height from the saved grid (bilinear); null if outside it */
function gridHeight(z, la, lo) {
  const fi = (la - z.la) / z.dLa + N, fj = (lo - z.lo) / z.dLo + N, M = 2 * N + 1;
  if (fi < 0 || fj < 0 || fi > M - 1 || fj > M - 1) return null;
  const i0 = Math.min(M - 2, Math.floor(fi)), j0 = Math.min(M - 2, Math.floor(fj)), ti = fi - i0, tj = fj - j0;
  const v = (i, j) => z.grid[i * M + j];
  return v(i0, j0) * (1 - ti) * (1 - tj) + v(i0, j0 + 1) * (1 - ti) * tj + v(i0 + 1, j0) * ti * (1 - tj) + v(i0 + 1, j0 + 1) * ti * tj;
}

/* ---------------- map ---------------- */
let map = null, zLayer = null, meMark = null, link = null, cur = null, zone = null;
function initMap() {
  if (typeof L === 'undefined') { $('azMap').innerHTML = '<p style="color:#bbb;padding:20px">The map could not load. The checker still works.</p>'; return; }
  map = L.map('azMap').setView([37.5, -84.5], 7);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; OpenStreetMap contributors' }).addTo(map);
  zLayer = L.layerGroup().addTo(map);
  map.on('click', e => { if (cur) check(e.latlng.lat, e.latlng.lng, null, 'tap'); });
}
function drawZone() {
  if (!map) return;
  zLayer.clearLayers();
  if (!cur) return;
  let edge = false;
  if (zone) {
    const M = 2 * N + 1;
    for (let i = 0; i < M; i++) for (let j = 0; j < M; j++) {
      const la = zone.la + (i - N) * zone.dLa, lo = zone.lo + (j - N) * zone.dLo, h = zone.grid[i * M + j];
      const inside = zone.top - h <= AZ;
      if (inside && (i === 0 || j === 0 || i === M - 1 || j === M - 1)) edge = true;
      L.rectangle([[la - zone.dLa / 2, lo - zone.dLo / 2], [la + zone.dLa / 2, lo + zone.dLo / 2]],
        { weight: 0.5, color: inside ? '#2e8b57' : '#777', fillColor: inside ? '#2e8b57' : '#787878', fillOpacity: inside ? 0.45 : 0.18 })
        .bindTooltip(`${ft(zone.top - h)} ft below the top`).addTo(zLayer);
    }
  }
  const e = $('azEdge'); if (e) e.hidden = !edge;
  L.circleMarker([cur.la, cur.lo], { radius: 8, color: '#111', weight: 2, fillColor: '#d5a63a', fillOpacity: 1 }).bindTooltip(`${cur.c} ${cur.n}`).addTo(zLayer);
}

/* ---------------- choosing a summit ---------------- */
function showSummit(s) {
  cur = s; zone = savedZone(s.c);
  const h = s.m ? `${Math.round(s.m)} m / ${ft(s.m).toLocaleString()} ft` : 'height unknown';
  $('azSum').hidden = false;
  $('azSum').innerHTML = `<b>${esc(s.n)}</b><span>${esc(s.c)} · ${h}${s.pts ? ' · ' + s.pts + ' pts' : ''}</span><br><span style="color:${zone ? '#7fd39a' : '#cfc6b2'}">${zone ? '✓ Zone saved on this phone' : 'Zone not saved yet'}</span>` +
    ` · <a href="https://sotl.as/summits/${encodeURI(s.c)}" target="_blank" rel="noopener" style="color:var(--gold-light)">summit info ↗</a>`;
  $('azSave').disabled = false; $('azSave').textContent = zone ? '↻ UPDATE SAVED ZONE' : '⬇ SAVE ZONE FOR OFFLINE';
  $('azGps').disabled = false;
  $('azStatus').hidden = true;
  if (map) map.setView([s.la, s.lo], 16);
  drawZone();
  if (!zone && navigator.onLine !== false) prepare(true);
}
async function prepare(quiet) {
  if (!cur) return;
  $('azSave').disabled = true; if (!quiet) msg('Saving the zone…');
  try { zone = await buildZone(cur); msg(quiet ? '' : 'Zone saved — it will work here with no signal.'); showSummit(cur); }
  catch (e) { msg('Could not get elevation data (no signal?). You can still check with GPS altitude.'); $('azSave').disabled = false; }
}
function list(items) {
  const box = $('azList');
  if (!items.length) { box.hidden = true; return; }
  box.innerHTML = items.slice(0, 30).map((s, k) => `<button type="button" data-k="${k}"><span><b>${esc(s.c)}</b> ${esc(s.n)}</span><small>${s.d != null ? fmtD(s.d) : (s.m ? ft(s.m).toLocaleString() + ' ft' : '')}</small></button>`).join('');
  box.hidden = false;
  box.querySelectorAll('button').forEach(b => b.addEventListener('click', () => { box.hidden = true; $('azQ').value = ''; showSummit(items[+b.dataset.k]); }));
}
function search(q) {
  q = q.trim().toLowerCase(); if (q.length < 2) { list([]); return; }
  const hits = SUM.filter(s => s.c.toLowerCase().includes(q) || (s.n || '').toLowerCase().includes(q));
  hits.sort((a, b) => (a.c.toLowerCase().startsWith(q) ? 0 : 1) - (b.c.toLowerCase().startsWith(q) ? 0 : 1));
  list(hits.map(s => Object.assign({}, s, { d: null })));
  if (!hits.length && !allLoaded) msg('Not in Kentucky? Tap "Load all U.S. summits".');
}
function locate() {
  return new Promise((ok, no) => {
    if (!navigator.geolocation) return no(new Error('no gps'));
    navigator.geolocation.getCurrentPosition(ok, no, { enableHighAccuracy: true, timeout: 20000, maximumAge: 5000 });
  });
}
async function nearest() {
  msg('Finding you…');
  try {
    await ky;
    const p = await locate(), me = [p.coords.latitude, p.coords.longitude];
    let near = SUM.map(s => Object.assign({}, s, { d: dist(me, [s.la, s.lo]) })).sort((a, b) => a.d - b.d);
    if ((!near.length || near[0].d > 40000) && !allLoaded) { await loadAll(); near = SUM.map(s => Object.assign({}, s, { d: dist(me, [s.la, s.lo]) })).sort((a, b) => a.d - b.d); }
    msg('');
    if (near.length && near[0].d < 400) showSummit(near[0]); else list(near.slice(0, 10));
  } catch (e) { msg('Could not get your location. Search for the summit instead.'); }
}

/* ---------------- the check ---------------- */
let lastQ = 0;
async function check(la, lo, gps, how) {
  if (!cur) return;
  const me = [la, lo], d = dist(me, [cur.la, cur.lo]), b = brg(me, [cur.la, cur.lo]);
  if (map) {
    if (!meMark) meMark = L.circleMarker(me, { radius: 8, color: '#fff', weight: 3, fillColor: '#2b7cff', fillOpacity: 1 }).addTo(map); else meMark.setLatLng(me);
    if (link) link.remove(); link = L.polyline([me, [cur.la, cur.lo]], { color: '#2b7cff', weight: 2, dashArray: '4 6' }).addTo(map);
  }
  const st = $('azStatus'); st.hidden = false;
  const toward = `Summit is ${fmtD(d)} ${DIRS[Math.round(b / 45) % 8]} (${Math.round(b)}°).`;
  if (d > 3000) { st.className = 'az-status far'; st.innerHTML = `<span class="big">NOT ON THE SUMMIT YET</span>${toward}`; return; }
  // your ground height: live lookup when online, else the saved grid
  let h = null, src = '';
  if (navigator.onLine !== false && Date.now() - lastQ > 3000) {
    lastQ = Date.now();
    try { h = (await elevations([me]))[0]; src = 'elevation data'; } catch (e) { h = null; }
  }
  if (h === null && zone) { h = gridHeight(zone, la, lo); if (h !== null) src = 'saved zone'; }
  const top = zone ? zone.top : null;
  let line2 = '';
  if (gps && gps.altitude != null && cur.m) {
    const below = cur.m - gps.altitude;
    line2 = `<br><small>Phone GPS altitude says ${below >= 0 ? ft(below) + ' ft below' : ft(-below) + ' ft above'} the listed summit height (±${ft(gps.altitudeAccuracy || 15)} ft).</small>`;
  }
  if (h === null || top === null) {
    if (gps && gps.altitude != null && cur.m) {
      const below = cur.m - gps.altitude, inside = below <= AZ;
      st.className = 'az-status ' + (inside ? 'in' : 'out');
      st.innerHTML = `<span class="big">${inside ? 'PROBABLY IN THE ZONE' : 'PROBABLY BELOW THE ZONE'}</span>By phone GPS only: about ${ft(Math.max(0, below))} ft below the summit (limit 82 ft). GPS altitude can be off — save the zone ahead of time for a better answer.<br>${toward}`;
    } else { st.className = 'az-status far'; st.innerHTML = `<span class="big">NO ELEVATION DATA</span>Save the zone while you have signal, then check again.<br>${toward}`; }
    return;
  }
  const below = Math.max(0, top - h), inside = below <= AZ;
  st.className = 'az-status ' + (inside ? 'in' : 'out');
  st.innerHTML = inside
    ? `<span class="big">✓ IN THE ZONE</span>About <b>${ft(below)} ft</b> below the top — the limit is 82 ft${below > AZ - 6 ? '. You\'re close to the edge — move a little higher to be safe' : ''}.<br>${d < 40 ? 'You\'re right on top.' : toward}${line2}<br><small>From ${src}${how === 'tap' ? ' (map spot)' : ''}.</small>`
    : `<span class="big">NOT YET — CLIMB ${ft(below - AZ)} FT MORE</span>You're about <b>${ft(below)} ft</b> below the top; the zone starts at 82 ft below.<br>${toward}${line2}<br><small>From ${src}${how === 'tap' ? ' (map spot)' : ''}.</small>`;
}
async function gpsCheck() {
  msg('Getting a GPS fix…');
  try { const p = await locate(); msg(p.coords.accuracy > 50 ? `GPS accuracy is only about ${ft(p.coords.accuracy)} ft — give it a minute in the open.` : ''); await check(p.coords.latitude, p.coords.longitude, p.coords, 'gps'); if (map) map.setView([p.coords.latitude, p.coords.longitude], Math.max(map.getZoom(), 16)); }
  catch (e) { msg('Could not get your location — allow location for this site, or tap the map.'); }
}

function init() {
  if (!$('azMap')) return;
  initMap();
  $('azNear').addEventListener('click', nearest);
  $('azAll').addEventListener('click', loadAll);
  $('azQ').addEventListener('input', e => { ky.then(() => search(e.target.value)); });
  $('azSave').addEventListener('click', () => prepare(false));
  $('azGps').addEventListener('click', gpsCheck);
  const ref = (location.hash.match(/#([A-Z0-9]+\/[A-Z]{2}-\d{3})/i) || [])[1];
  if (ref) ky.then(async () => { let s = SUM.find(x => x.c.toUpperCase() === ref.toUpperCase()); if (!s) { await loadAll(); s = SUM.find(x => x.c.toUpperCase() === ref.toUpperCase()); } if (s) showSummit(s); });
}
window.KPCAZ = { gridPts, gridHeight, buildZone, check, showSummit, get zone() { return zone; }, get SUM() { return SUM; }, ky };
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
