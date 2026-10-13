/* KPC Fox Hunt — bearing map (GPS + phone compass + triangulation) and tape-measure Yagi calculator.
   Bearings are saved on this device only (localStorage "kpcFox"). */
(function () {
'use strict';
const $ = id => document.getElementById(id);
const R = 6371000, rad = d => d * Math.PI / 180, deg = r => r * 180 / Math.PI;
const norm360 = d => ((d % 360) + 360) % 360;

/* ============================================================ geometry */
function dest(la, lo, brg, m) { // great-circle destination
  const d = m / R, b = rad(brg), p1 = rad(la), l1 = rad(lo);
  const p2 = Math.asin(Math.sin(p1) * Math.cos(d) + Math.cos(p1) * Math.sin(d) * Math.cos(b));
  const l2 = l1 + Math.atan2(Math.sin(b) * Math.sin(d) * Math.cos(p1), Math.cos(d) - Math.sin(p1) * Math.sin(p2));
  return [deg(p2), deg(l2)];
}
function dist(a, b) { const dp = rad(b[0] - a[0]), dl = rad(b[1] - a[1]); const h = Math.sin(dp / 2) ** 2 + Math.cos(rad(a[0])) * Math.cos(rad(b[0])) * Math.sin(dl / 2) ** 2; return 2 * R * Math.asin(Math.sqrt(h)); }
function brgTo(a, b) { const p1 = rad(a[0]), p2 = rad(b[0]), dl = rad(b[1] - a[1]); return norm360(deg(Math.atan2(Math.sin(dl) * Math.cos(p2), Math.cos(p1) * Math.sin(p2) - Math.sin(p1) * Math.cos(p2) * Math.cos(dl)))); }
/* Crossing points of every pair of bearing rays (flat-earth is fine at fox-hunt distances) */
function fixes(list, maxM) {
  if (list.length < 2) return [];
  const lat0 = list.reduce((s, b) => s + b.la, 0) / list.length, kx = R * Math.cos(rad(lat0)) * Math.PI / 180, ky = R * Math.PI / 180;
  const P = list.map(b => ({ x: b.lo * kx, y: b.la * ky, dx: Math.sin(rad(b.t)), dy: Math.cos(rad(b.t)) }));
  const out = [];
  for (let i = 0; i < P.length; i++) for (let j = i + 1; j < P.length; j++) {
    const a = P[i], b = P[j];
    const cr = a.dx * b.dy - a.dy * b.dx;
    const ang = Math.abs(deg(Math.asin(Math.max(-1, Math.min(1, cr)))));
    if (ang < 12) continue;                         // nearly parallel: no useful fix
    const qx = b.x - a.x, qy = b.y - a.y;
    const t1 = (qx * b.dy - qy * b.dx) / cr, t2 = (qx * a.dy - qy * a.dx) / cr;
    if (t1 <= 0 || t2 <= 0 || t1 > maxM || t2 > maxM) continue; // must be in front of both hunters
    out.push([(a.y + t1 * a.dy) / ky, (a.x + t1 * a.dx) / kx]);
  }
  return out;
}
function estimate(pts) {
  if (!pts.length) return null;
  const c = [pts.reduce((s, p) => s + p[0], 0) / pts.length, pts.reduce((s, p) => s + p[1], 0) / pts.length];
  const rms = pts.length > 1 ? Math.sqrt(pts.reduce((s, p) => s + dist(c, p) ** 2, 0) / pts.length) : null;
  return { c, rms, n: pts.length };
}
const fmtD = m => { const mi = m / 1609.344; return mi < 0.2 ? Math.round(m * 3.28084) + ' ft' : (mi < 10 ? mi.toFixed(1) : Math.round(mi)) + ' mi'; };

/* ============================================================ bearing map */
let map = null, layer = null, me = null, meMark = null, heading = null, watchId = null, picking = false;
let B = [];
try { B = JSON.parse(localStorage.getItem('kpcFox') || '[]'); } catch (e) { B = []; }
const declEl = () => +($('btDecl') && $('btDecl').value) || 0;
try { const d = localStorage.getItem('kpcFoxDecl'); if (d !== null && $('btDecl')) $('btDecl').value = d; } catch (e) {}
const trueOf = b => norm360(b.kind === 'mag' ? b.raw + declEl() : b.raw);
const saveB = () => { try { localStorage.setItem('kpcFox', JSON.stringify(B)); } catch (e) {} };
const msg = t => { const m = $('btMsg'); if (m) m.textContent = t || ''; };

function draw() {
  if (!map) return;
  layer.clearLayers();
  const rng = (+$('btRange').value || 5) * 1000;
  const list = B.map(b => Object.assign({}, b, { t: trueOf(b) }));
  list.forEach((b, i) => {
    const end = dest(b.la, b.lo, b.t, rng);
    L.polyline([[b.la, b.lo], end], { color: i === list.length - 1 ? '#ffcf5a' : '#d5a63a', weight: 3, opacity: .9, dashArray: b.kind === 'mag' ? null : '6 6' }).addTo(layer);
    L.circleMarker([b.la, b.lo], { radius: 6, color: '#111', weight: 2, fillColor: '#d5a63a', fillOpacity: 1 }).bindTooltip(`#${i + 1}: ${Math.round(b.t)}° true`).addTo(layer);
  });
  const pts = fixes(list, rng), est = estimate(pts);
  pts.forEach(p => L.circleMarker(p, { radius: 3, color: '#7fd39a', weight: 1, fillOpacity: .9 }).addTo(layer));
  const e = $('btEst');
  if (est) {
    const r = Math.max(30, est.rms || 0);
    L.circle(est.c, { radius: r, color: '#2e8b57', weight: 2, fillColor: '#2e8b57', fillOpacity: .15 }).addTo(layer);
    L.marker(est.c, { icon: L.divIcon({ className: 'fox-ico', html: '🦊', iconSize: [30, 30], iconAnchor: [15, 15] }) }).bindTooltip('Best guess').addTo(layer);
    const from = me || [list[list.length - 1].la, list[list.length - 1].lo];
    const d = dist(from, est.c), t = brgTo(from, est.c), mag = norm360(t - declEl());
    e.hidden = false;
    e.innerHTML = `🦊 <b>Best guess: ${fmtD(d)} away</b><br>Head <b>${Math.round(t)}°</b> true (${Math.round(mag)}° on a compass)` +
      `<br><span style="color:#a9d6b6">From ${est.n} crossing${est.n > 1 ? 's' : ''}${est.rms ? ' · spread about ' + fmtD(est.rms) : ''}</span>` +
      `<br><a href="https://www.google.com/maps/dir/?api=1&destination=${est.c[0].toFixed(5)},${est.c[1].toFixed(5)}" target="_blank" rel="noopener" style="color:#ffcf5a;font-weight:800">Directions to this spot ↗</a>`;
  } else {
    e.hidden = !B.length;
    if (B.length) e.innerHTML = B.length === 1 ? 'One bearing so far. Move a good distance <b>sideways</b> and take another.' : 'The lines don\'t cross in front of you yet. Take a bearing from a spot farther to the side.';
  }
  const lst = $('btList');
  lst.innerHTML = list.map((b, i) => `<div><span><b>#${i + 1}</b> ${Math.round(b.t)}° true${b.kind === 'mag' ? ` <small style="color:#8f8a80">(${Math.round(b.raw)}° compass)</small>` : ''}</span><span style="color:#8f8a80">${new Date(b.at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</span></div>`).reverse().join('');
}

function add(la, lo, raw, kind) {
  B.push({ la, lo, raw: norm360(raw), kind, at: Date.now() }); saveB(); draw();
  fit();
}

/* zoom to show every bearing spot and the best guess */
function fit() {
  if (!map || !B.length) return;
  const pts = B.map(b => [b.la, b.lo]);
  const est = estimate(fixes(B.map(b => Object.assign({}, b, { t: trueOf(b) })), (+$('btRange').value || 5) * 1000));
  if (est) pts.push(est.c);
  if (pts.length === 1) map.setView(pts[0], Math.max(map.getZoom(), 14));
  else map.fitBounds(L.latLngBounds(pts).pad(0.35), { maxZoom: 16, animate: false });
}
function showMe(p) {
  me = [p.coords.latitude, p.coords.longitude];
  if (!map) return;
  if (!meMark) { meMark = L.circleMarker(me, { radius: 8, color: '#fff', weight: 3, fillColor: '#2b7cff', fillOpacity: 1 }).addTo(map); map.setView(me, Math.max(map.getZoom(), 14)); }
  else meMark.setLatLng(me);
  if ($('btTake')) $('btTake').disabled = heading === null;
}
function startGPS() {
  if (!navigator.geolocation) { msg('This device has no GPS / location access.'); return; }
  if (watchId !== null) return;
  watchId = navigator.geolocation.watchPosition(showMe, e => msg(e.code === 1 ? 'Location is blocked — allow it for this site to take bearings.' : 'Waiting for a GPS fix…'), { enableHighAccuracy: true, maximumAge: 3000, timeout: 20000 });
}
function onOrient(e) {
  let h = null;
  if (typeof e.webkitCompassHeading === 'number') h = e.webkitCompassHeading;           // iPhone: degrees from magnetic north
  else if (e.absolute && typeof e.alpha === 'number') h = 360 - e.alpha;                // Android: alpha is counter-clockwise
  if (h === null || isNaN(h)) return;
  const so = (screen.orientation && screen.orientation.angle) || window.orientation || 0;
  heading = norm360(h + so);
  $('btHeadV').innerHTML = Math.round(heading) + '°<small>compass (magnetic) · ' + Math.round(norm360(heading + declEl())) + '° true</small>';
  $('btNeedle').style.transform = 'rotate(' + heading + 'deg)';
  if ($('btTake')) $('btTake').disabled = !me;
}
async function startCompass() {
  startGPS();
  try {
    if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
      const r = await DeviceOrientationEvent.requestPermission();
      if (r !== 'granted') { msg('Compass permission was denied. You can still add bearings by hand.'); return; }
    }
    if ('ondeviceorientationabsolute' in window) window.addEventListener('deviceorientationabsolute', onOrient, true);
    else window.addEventListener('deviceorientation', onOrient, true);
    msg('Hold the phone flat, top pointing along the beam. Wave it in a figure-8 once to calibrate.');
    $('btCompass').textContent = '🧭 COMPASS ON';
    setTimeout(() => { if (heading === null) msg('No compass found on this device — add bearings by hand instead.'); }, 4000);
  } catch (e) { msg('Could not start the compass — add bearings by hand instead.'); }
}

function initMap() {
  if (!$('foxMap') || typeof L === 'undefined') { if ($('foxMap')) $('foxMap').innerHTML = '<p style="color:#bbb;padding:20px">The map could not load. Check your connection.</p>'; return; }
  map = L.map('foxMap', { zoomControl: true }).setView([37.7, -85.3], 7);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; OpenStreetMap contributors' }).addTo(map);
  layer = L.layerGroup().addTo(map);
  map.on('click', ev => {
    if (!picking) return;
    picking = false; $('foxMap').style.cursor = '';
    const v = parseFloat($('btDeg').value);
    if (isNaN(v)) { msg('Type the bearing first.'); return; }
    add(ev.latlng.lat, ev.latlng.lng, v, $('btKind').value); msg('Bearing added.'); $('btDeg').value = '';
  });
  draw(); fit();
}

function bindMap() {
  if (!$('foxMap')) return;
  $('btCompass').addEventListener('click', startCompass);
  $('btTake').addEventListener('click', () => {
    if (!me || heading === null) { msg('Waiting for GPS and compass…'); return; }
    add(me[0], me[1], heading, 'mag'); msg(`Bearing ${Math.round(heading)}° saved. Move a good distance sideways for the next one.`);
    if (navigator.vibrate) navigator.vibrate(60);
  });
  $('btPick').addEventListener('click', () => {
    if (isNaN(parseFloat($('btDeg').value))) { msg('Type the bearing first.'); $('btDeg').focus(); return; }
    picking = true; $('foxMap').style.cursor = 'crosshair'; msg('Now tap the map where you took that bearing.');
    $('foxMap').scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
  $('btHere').addEventListener('click', () => {
    const v = parseFloat($('btDeg').value);
    if (isNaN(v)) { msg('Type the bearing first.'); $('btDeg').focus(); return; }
    const go = p => { showMe(p); add(p.coords.latitude, p.coords.longitude, v, $('btKind').value); msg('Bearing added at your location.'); $('btDeg').value = ''; };
    if (!navigator.geolocation) { msg('No location on this device — use TAP MAP.'); return; }
    navigator.geolocation.getCurrentPosition(go, () => msg('Could not get your location — use TAP MAP.'), { enableHighAccuracy: true, timeout: 15000 });
  });
  $('btUndo').addEventListener('click', () => { B.pop(); saveB(); draw(); });
  $('btClear').addEventListener('click', () => { if (!B.length || confirm('Clear all bearings?')) { B = []; saveB(); draw(); } });
  $('btDecl').addEventListener('input', () => { try { localStorage.setItem('kpcFoxDecl', $('btDecl').value); } catch (e) {} draw(); });
  $('btRange').addEventListener('change', draw);
  initMap();
}

/* ============================================================ tape-measure Yagi */
/* WB2HOL 2 m tape-measure Yagi, inches, scaled from 146.565 MHz */
const F0 = 146.565;
const YAGI = [
  ['Reflector (1 piece)', 41.375, 'r'],
  ['Driven element (2 halves, each)', 17.75, 'd'],
  ['Director (1 piece)', 35.125, 'x'],
  ['Boom: reflector → driven (PVC piece)', 7, 'b1'],
  ['Boom: driven → director (PVC piece)', 11.5, 'b2'],
  ['Hairpin match wire', 5, 'h'],
  ['Gap between driven halves (start)', 1, 'g']
];
function inch(v) { // nearest 1/8"
  const e = Math.round(v * 8), w = Math.floor(e / 8), f = e % 8;
  const fr = ['', '⅛', '¼', '⅜', '½', '⅝', '¾', '⅞'][f];
  return (w ? w : (f ? '' : '0')) + (fr ? (w ? ' ' : '') + fr : '') + '"';
}
function yagi() {
  const out = $('ygOut'); if (!out) return;
  let f = parseFloat($('ygF').value); const u = $('ygU').value;
  const warn = $('ygWarn');
  if (!(f >= 50 && f <= 450)) { out.innerHTML = '<tr><td colspan="2">Enter a frequency between 50 and 450 MHz.</td></tr>'; warn.hidden = true; return; }
  const k = F0 / f, val = {};
  out.innerHTML = YAGI.map(([n, v, id]) => {
    const x = id === 'g' ? v : v * k; val[id] = x;   // the feed gap doesn't scale — you tune it
    return `<tr><td>${n}</td><td class="v">${u === 'cm' ? (x * 2.54).toFixed(1) + ' cm' : inch(x)}</td></tr>`;
  }).join('');
  const w = [];
  if (Math.abs(f - F0) > 6) w.push('Scaled from the 2 m design. Tape width and the PVC fittings don\'t scale, so build a little long and trim for the best SWR.');
  if (f < 100) w.push('At this frequency the elements are long and floppy — aluminum tubing works better than tape.');
  if (f > 300) w.push('On 70 cm the elements are short and every ⅛" matters. Consider a smaller boom (⅜" PVC or a wood dowel).');
  warn.hidden = !w.length; warn.innerHTML = w.join('<br>');
  // diagram: element heights scaled to reflector
  const g = $('ygSvg'); if (!g) return;
  const H = 230, sc = H / val.r, cy = 150;
  const xr = 70, xd = 210, xx = 440;
  const el = (x, len, col) => `<rect x="${x - 4}" y="${cy - len / 2}" width="8" height="${len}" rx="3" fill="${col}"/>`;
  const half = val.d * sc;
  g.innerHTML = el(xr, val.r * sc, '#9a9a9a') +
    `<rect x="${xd - 4}" y="${cy - half - 5}" width="8" height="${half}" rx="3" fill="#d5a63a"/><rect x="${xd - 4}" y="${cy + 5}" width="8" height="${half}" rx="3" fill="#d5a63a"/>` +
    `<path d="M${xd + 6} ${cy - 5} h18 v10 h-18" fill="none" stroke="#b5651d" stroke-width="2.5"/>` +
    el(xx, val.x * sc, '#9a9a9a') +
    `<text x="${xr + 10}" y="${cy - val.r * sc / 2 + 12}" font-size="12" font-family="Arial" fill="#333">${$('ygU').value === 'cm' ? (val.r * 2.54).toFixed(1) + ' cm' : inch(val.r)}</text>` +
    `<text x="${xd + 10}" y="${cy - half - 8 + 14}" font-size="12" font-family="Arial" fill="#8a5a12">${$('ygU').value === 'cm' ? (val.d * 2.54).toFixed(1) + ' cm' : inch(val.d)} ×2</text>` +
    `<text x="${xd + 28}" y="${cy + 4}" font-size="11" font-family="Arial" fill="#b5651d">hairpin</text>` +
    `<text x="${xx + 10}" y="${cy - val.x * sc / 2 + 12}" font-size="12" font-family="Arial" fill="#333">${$('ygU').value === 'cm' ? (val.x * 2.54).toFixed(1) + ' cm' : inch(val.x)}</text>`;
}
function bindYagi() {
  if (!$('ygF')) return;
  ['input', 'change'].forEach(t => { $('ygF').addEventListener(t, yagi); $('ygU').addEventListener(t, yagi); });
  document.querySelectorAll('.yg-presets [data-f]').forEach(b => b.addEventListener('click', () => { $('ygF').value = b.dataset.f; yagi(); }));
  yagi();
}

window.KPCFOX = { dest, dist, brgTo, fixes, estimate, inch, get B() { return B; }, add, draw, setMe: (la, lo) => showMe({ coords: { latitude: la, longitude: lo } }), heading: h => onOrient({ webkitCompassHeading: h }) };
function init() { bindMap(); bindYagi(); }
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
