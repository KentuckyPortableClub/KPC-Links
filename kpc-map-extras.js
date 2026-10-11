/* KPC map extras — v20261010j
   Shared by KY Park Commander (finder.html) and the Trip Planner (kpc-planner.html):
   • Parking and Entrance markers with their own on/off switches
       official = Kentucky agency GIS (KDFWR, WMA Map Points, Kentucky State Parks) and the KPC park file
       unverified = OpenStreetMap community data
   • Park Overlaps: computed overlap areas from ky-overlaps.geojson
       gold = possible POTA 2-fer (two or more POTA references), purple = other multi-program overlap
   • Hover cards on desktop, tap cards on phones
   Nothing here is proof of legal access or of award eligibility. Cards say so. */
(function () {
'use strict';
if (!window.L) return;
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const KY = 'https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/';
const OFFICIAL = [
 {id:'kdfwr', label:'Kentucky Fish & Wildlife GIS', url:KY+'Ky_Fish_Wildlife_WGS84WM/MapServer/5/query'},
 {id:'wma', label:'KDFWR WMA Map Points', url:'https://services5.arcgis.com/RMHPuOW5MJ6iyTV6/ArcGIS/rest/services/WMA_Map_Points/FeatureServer/0/query'},
 {id:'horse', label:'KDFWR horse trailheads', url:KY+'Ky_Fish_Wildlife_WGS84WM/MapServer/3/query', kind:'trailhead'},
 {id:'boat', label:'KDFWR boat access', url:KY+'Ky_Fish_Wildlife_WGS84WM/MapServer/0/query', kind:'boat'},
 {id:'ksp', label:'Kentucky State Parks GIS', url:KY+'Ky_State_Parks_Features_WGS84WM/MapServer/0/query', kind:'trailhead'}
];
const OVERPASS = ['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter','https://overpass.private.coffee/api/interpreter'];
const KIND = {
 parking:  {g:'P', icon:'🅿️', label:'Parking area'},
 pulloff:  {g:'P', icon:'🚗', label:'Roadside pull-off'},
 entrance: {g:'E', icon:'🚪', label:'Entrance'},
 access:   {g:'E', icon:'🚪', label:'Access point'},
 gate:     {g:'E', icon:'🚧', label:'Gate'},
 trailhead:{g:'E', icon:'🥾', label:'Trailhead'},
 boat:     {g:'E', icon:'⛵', label:'Boat access'}
};
const ZOFF = 11, ZOSM = 13;                      // zoom needed for live official GIS / OpenStreetMap
const potaUrl = r => 'https://pota.app/#/park/' + encodeURIComponent(r);
const sotaUrl = r => 'https://sotl.as/summits/' + encodeURIComponent(r);
const kffUrl = r => 'https://logsearch.wwff.co/directory/' + encodeURIComponent(r);
const dirUrl = (a, b) => `https://www.google.com/maps/dir/?api=1&destination=${a},${b}&travelmode=driving`;
const fine = window.matchMedia ? matchMedia('(hover: hover) and (pointer: fine)').matches : false;
const store = {get(k, d){try{const v = localStorage.getItem(k);return v == null ? d : JSON.parse(v)}catch(e){return d}}, set(k, v){try{localStorage.setItem(k, JSON.stringify(v))}catch(e){}}};

/* ---------- CSS ---------- */
if (!document.getElementById('kx-css')) {
 const st = document.createElement('style'); st.id = 'kx-css';
 st.textContent = `
.kx-ctl{background:#fff;border-radius:8px;box-shadow:0 1px 6px rgba(0,0,0,.35);font:13px/1.35 Arial,Helvetica,sans-serif;max-width:270px;color:#1b1b1b}
.kx-btn{border:0;background:#fff;border-radius:8px;padding:8px 11px;font-weight:900;font-size:12px;letter-spacing:.4px;cursor:pointer;width:100%;text-align:left;color:#1b1b1b;white-space:nowrap}
.kx-btn.on{background:#fff6dc}
.kx-box{padding:2px 11px 10px;max-height:min(62vh,460px);overflow:auto}
.kx-box label{display:flex;align-items:center;gap:8px;padding:5px 0;cursor:pointer;font-weight:700}
.kx-box input{width:18px;height:18px;margin:0;accent-color:#1d5a3a;flex:0 0 auto}
.kx-h{font-size:11px;font-weight:900;letter-spacing:.5px;color:#555;margin:9px 0 3px;text-transform:uppercase}
.kx-lg{display:flex;align-items:center;gap:7px;font-size:12px;color:#333;padding:2px 0}
.kx-sw{display:inline-block;width:16px;height:11px;border-radius:2px;flex:0 0 auto}
.kx-stat{font-size:11.5px;color:#666;margin-top:6px}
.kx-pin{display:flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:50%;background:#fff;font-size:15px;line-height:1;box-shadow:0 1px 4px rgba(0,0,0,.45);box-sizing:border-box}
.kx-pin.off{border:3px solid #1d7a46}
.kx-pin.osm{border:2.5px dashed #6b6b6b;background:#f4f4f4;opacity:.93}
.kx-key{display:inline-flex;width:18px;height:18px;border-radius:50%;background:#fff;box-sizing:border-box;flex:0 0 auto}
.kx-key.off{border:3px solid #1d7a46}.kx-key.osm{border:2.5px dashed #6b6b6b}.kx-key.mine{background:#d5a63a;border:2px solid #111}
.kx-sota{display:flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;background:#7b3fa0;color:#fff;border:2px solid #fff;font-size:11px;box-shadow:0 1px 4px rgba(0,0,0,.5)}
.kx-card{font:13px/1.4 Arial,Helvetica,sans-serif;color:#1b1b1b;min-width:190px}
.kx-card .kx-t{font-weight:900;font-size:14px;margin-bottom:2px}
.kx-card .kx-n{font-weight:700}
.kx-badge{display:inline-block;font-size:11px;font-weight:900;letter-spacing:.3px;border-radius:999px;padding:3px 9px;margin:0 0 6px}
.kx-badge.g{background:#f2c230;color:#111}.kx-badge.p{background:#7b3fa0;color:#fff}
.kx-v{font-size:12px;font-weight:700;margin:5px 0}
.kx-v.off{color:#1d6b3f}.kx-v.osm{color:#8a5a00}
.kx-ll{font-size:12px;color:#444;margin:4px 0;display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.kx-ll button,.kx-acts button,.kx-acts a{font:900 11px Arial,sans-serif;letter-spacing:.3px;border:1px solid #1d5a3a;background:#fff;color:#1d5a3a;border-radius:6px;padding:5px 8px;cursor:pointer;text-decoration:none;display:inline-block}
.kx-acts{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.kx-acts .pri{background:#1d5a3a;color:#fff}
.kx-d{font-size:12px;color:#333;margin:2px 0}
.kx-note{font-size:11.5px;color:#666;margin-top:6px}
.kx-refs{margin:4px 0}.kx-refs div{margin:1px 0}
.kx-refs a{font-weight:900;color:#1d5a3a}
`;
 document.head.appendChild(st);
}

/* ---------- small helpers ---------- */
function json(url, opt, ms){const c = new AbortController(), t = setTimeout(() => c.abort(), ms || 15000);
 return fetch(url, Object.assign({signal:c.signal}, opt || {})).then(r => {if(!r.ok)throw Error('HTTP ' + r.status);return r.json()}).then(j => {if(j && j.error)throw Error(j.error.message || 'GIS error');return j}).finally(() => clearTimeout(t))}
function val(p, keys){for(const k of keys){const f = Object.keys(p).find(x => x.toLowerCase() === k.toLowerCase());if(f && p[f] != null && String(p[f]).trim())return String(p[f]).trim()}return ''}
/* same rules as the KPC Access Finder */
function classify(p, src){
 if (src.kind) return src.kind;
 const type = [val(p,['TYPE','FEATURE','FeatureType','SYMBOL','CATEGORY','PointType','Description','Name','FACILITY','POINT_TYPE','POINTTYPE','FEATURE_TYPE','FEATURETYPE','COMMENTS','LABEL']), val(p,['SUBTYPE','AMENITY','parking','highway','USE','CLASS'])].join(' ').toLowerCase();
 if (/layby|lay-by|pull.?off|turnout|roadside parking/.test(type)) return 'pulloff';
 if (/parking lot|parking area|parking space|parking facility|parking\b|park lot/.test(type)) return 'parking';
 if (/gate|barrier/.test(type)) return 'gate';
 if (/trailhead|trail head/.test(type)) return 'trailhead';
 if (/entrance|access point|entry/.test(type) || src.id === 'kdfwr') return 'entrance';
 return null;                                   // ponds, food plots, etc. are not shown
}
function osmClass(t){
 if (/^(private|no)$/.test(t.access || '')) return null;
 if (t.amenity === 'parking') return t.parking === 'layby' ? 'pulloff' : 'parking';
 if (t.parking === 'layby') return 'pulloff';
 if (t.highway === 'trailhead' || t.information === 'trailhead') return 'trailhead';
 if (t.barrier === 'gate' || t.barrier === 'lift_gate') return 'gate';
 if (t.entrance && t.name) return 'entrance';
 return null;
}
function details(p, osm){
 const out = [];
 if (osm) {
  const L2 = {fee:'Fee', access:'Access', capacity:'Spaces', surface:'Surface', opening_hours:'Hours', operator:'Operator', description:'Note', 'parking':'Parking type'};
  for (const k of Object.keys(L2)) if (p[k] && !(k === 'parking' && p[k] === 'layby')) out.push([L2[k], p[k]]);
 } else {
  for (const k of Object.keys(p)) {
   const v = p[k]; if (v == null || v === '' || typeof v === 'object') continue;
   if (/^(objectid|fid|shape|globalid|x|y|lat|long|lon|latitude|longitude|created|edited|last_|symbol)/i.test(k)) continue;
   if (!/name|type|desc|comment|access|road|lot|area|county|surface|capacity|site|ramp|facility|note|label/i.test(k)) continue;
   const s = String(v).trim(); if (!s || s.length > 70 || /^-?\d+(\.\d+)?$/.test(s) && !/capacity/i.test(k)) continue;
   if (!out.some(x => x[1] === s)) out.push([k.replace(/_/g, ' ').toLowerCase().replace(/^\w/, c => c.toUpperCase()), s]);
   if (out.length >= 5) break;
  }
 }
 return out;
}

/* ---------- hover card on desktop, tap card on phones ---------- */
function hover(layer){
 if (!fine || !layer || layer._kxHover) return; layer._kxHover = true;
 let pinned = false, t = null, over = false;
 const shut = () => {clearTimeout(t); t = setTimeout(() => {if (!pinned && !over && layer.isPopupOpen()) layer.closePopup()}, 380)};
 layer.on('mouseover', () => {clearTimeout(t); if (!layer.isPopupOpen()) {const p = layer.getPopup(); if (p) p.options.autoPan = false; layer._kxH = true; layer.openPopup(); layer._kxH = false}});
 layer.on('mouseout', () => {if (!pinned) shut()});
 layer.on('click', () => {pinned = true; clearTimeout(t); const p = layer.getPopup(); if (p) p.options.autoPan = true; if (!layer.isPopupOpen()) layer.openPopup()});
 layer.on('popupopen', e => {const el = e.popup.getElement(); if (!el) return; el.onmouseenter = () => {over = true; clearTimeout(t)}; el.onmouseleave = () => {over = false; if (!pinned) shut()}; el.onclick = () => {pinned = true}});
 layer.on('popupclose', () => {pinned = false; over = false});
}

/* ---------- overlap data ---------- */
let OVL = null;
function overlapData(){return OVL || (OVL = fetch('ky-overlaps.geojson', {cache:'force-cache'}).then(r => {if(!r.ok)throw Error('HTTP ' + r.status);return r.json()}))}
/* POTA refs → [{kind, other refs, areas}] for cards */
function overlapIndex(){return overlapData().then(gj => {const idx = new Map();
 for (const f of gj.features) {const p = f.properties, refs = p.pota.map(r => r[0]);
  for (const r of refs) {if (!idx.has(r)) idx.set(r, []); idx.get(r).push({kind:p.kind, others:p.pota.filter(x => x[0] !== r), kff:p.kff, sota:p.sota, areas:p.areas, trail:p.trail || ''})}}
 return idx})}

const KINDTXT = {
 '2fer':['g','Possible POTA 2-Fer — Verify Before Activating'],
 pota_wwff:['p','POTA + WWFF overlap'],
 pota_sota:['p','POTA + SOTA: summit inside a park'],
 other:['p','Other multi-program overlap']
};
function refsHtml(p){
 const row = (lab, list, url) => list.length ? `<div><b>${lab}:</b> ${list.map(r => `<a href="${url(r[0])}" target="_blank" rel="noopener">${esc(r[0])}</a> ${esc(r[1] || '')}`).join('<br>')}</div>` : '';
 return `<div class="kx-refs">${row('POTA', p.pota, potaUrl)}${row('WWFF/KFF', p.kff, kffUrl)}${row('SOTA', p.sota, sotaUrl)}</div>`;
}
function overlapCard(p, ll, addStop){
 const k = KINDTXT[p.kind] || KINDTXT.other;
 let why = '';
 if (p.kind === '2fer') why = p.shared ? 'Both POTA references use the same outline in our map data. Check the POTA map for each reference.'
  : p.trail ? `About ${p.miles} miles of the ${esc(p.trail)} run inside this boundary. Being on the trail and inside the park may count for both. Verify each reference first.`
  : 'Two POTA boundaries overlap here. Make sure your exact spot is inside both before you call a 2-fer.';
 else if (p.kind === 'pota_wwff') why = 'One POTA reference plus a separate WWFF/KFF reference. This is <b>not</b> a POTA 2-fer.';
 else if (p.kind === 'pota_sota') why = 'A SOTA summit sits inside this POTA boundary. SOTA needs you in the summit’s activation zone. This is a POTA + SOTA combo, <b>not</b> a POTA 2-fer.';
 else why = 'More than one program is mapped here. This is <b>not</b> a POTA 2-fer.';
 const size = p.acres ? `About ${Number(p.acres).toLocaleString()} acres overlap` : p.miles ? `${p.miles} miles of trail` : p.ft ? `Summit elevation ${Number(p.ft).toLocaleString()} ft` : '';
 return `<div class="kx-card"><span class="kx-badge ${k[0]}">${esc(k[1])}</span>
 <div class="kx-n">${esc(p.areas.join(' + '))}</div>${size ? `<div class="kx-d">${size}</div>` : ''}${refsHtml(p)}
 <div class="kx-d">${why}</div>
 <div class="kx-note">Outlines are approximate. Overlap on a map does not guarantee both references count. Check each program’s rules and official boundary.</div>
 <div class="kx-acts"><a href="${dirUrl(ll.lat.toFixed(5), ll.lng.toFixed(5))}" target="_blank" rel="noopener">DIRECTIONS ↗</a>${addStop ? `<button type="button" class="pri" data-drop="${ll.lat.toFixed(6)},${ll.lng.toFixed(6)}">📍 ADD A SPOT HERE</button>` : ''}</div></div>`;
}

/* ---------- the control ---------- */
function attach(map, opt){
 opt = opt || {};
 const KEY = 'kpcx_' + (opt.key || 'map');
 const st = Object.assign({P:false, E:false, O:false}, store.get(KEY, {}));
 map.createPane('kxov').style.zIndex = 450;
 map.createPane('kxovl').style.zIndex = 455;
 map.createPane('kxpin').style.zIndex = 590;
 const lay = {P:L.layerGroup(), E:L.layerGroup(), O:L.layerGroup()};
 const pts = new Map();                         // key → point
 const cellsOff = new Set(), cellsOsm = new Set(), err = {};
 let statEl = null, legendEl = null, btn = null, box = null, busy = 0, built = false;
 const listeners = [];

 /* official access points that ship with the site (kpc-ky-data.json) */
 function addStatic(parks){(parks || []).forEach(p => (p.ap || []).forEach(a => {
  const la = +a[0], lo = +a[1]; if (!isFinite(la) || !isFinite(lo)) return;
  const kind = /parking|lot\b/i.test(a[2] || '') ? 'parking' : 'access';
  add({la, lo, kind, osm:false, name:a[2] && a[2] !== p.n ? a[2] : p.n + ' access', src:'KPC park file (official agency points)', extra:[['Park', p.n + ' · ' + p.c]], props:{}})}))}
 function near(a, b){return Math.abs(a.la - b.la) < .0003 && Math.abs(a.lo - b.lo) < .0004}
 function add(pt){
  const g = KIND[pt.kind].g, key = g + pt.la.toFixed(4) + ',' + pt.lo.toFixed(4);
  if (pts.has(key)) return;
  if (pt.osm) {for (const q of pts.values()) if (!q.osm && KIND[q.kind].g === g && near(q, pt)) {q.alsoOsm = true; return}}
  else {for (const [k2, q] of pts) if (q.osm && KIND[q.kind].g === g && near(q, pt)) {lay[g].removeLayer(q.m); pts.delete(k2)}}
  pts.set(key, pt);
  const icon = L.divIcon({className:'', html:`<span class="kx-pin ${pt.osm ? 'osm' : 'off'}">${KIND[pt.kind].icon}</span>`, iconSize:[28, 28], iconAnchor:[14, 14], popupAnchor:[0, -12]});
  pt.m = L.marker([pt.la, pt.lo], {icon, pane:'kxpin', title:KIND[pt.kind].label + (pt.name ? ': ' + pt.name : ''), keyboard:true, riseOnHover:true})
   .bindPopup(() => pinCard(pt), {maxWidth:280, minWidth:200, autoPanPadding:[14, 14]});
  hover(pt.m);
  pt.m.addTo(lay[g]);
 }
 function pinCard(pt){
  const k = KIND[pt.kind], ll = pt.la.toFixed(6) + ', ' + pt.lo.toFixed(6);
  const det = (pt.extra || []).concat(details(pt.props || {}, pt.osm));
  return `<div class="kx-card"><div class="kx-t">${k.icon} ${esc(k.label)}</div>${pt.name ? `<div class="kx-n">${esc(pt.name)}</div>` : ''}
  ${pt.osm ? `<div class="kx-v osm">⚠ Unverified: OpenStreetMap community data</div>` : `<div class="kx-v off">✓ Official source: ${esc(pt.src)}</div>`}
  <div class="kx-ll">${ll} <button type="button" data-kxcopy="${ll}">COPY</button></div>
  ${det.map(d => `<div class="kx-d"><b>${esc(d[0])}:</b> ${esc(d[1])}</div>`).join('')}
  ${pt.alsoOsm ? '<div class="kx-d">Also mapped in OpenStreetMap.</div>' : ''}
  ${pt.kind === 'access' ? '<div class="kx-note">Agency access point. It may be a parking area or an entrance.</div>' : ''}
  <div class="kx-note">${pt.osm ? 'Community-mapped. It may be private, closed or gone. Check posted signs on site.' : 'A mapped point is not a promise of legal public parking or access. Check posted signs and the managing agency.'}</div>
  <div class="kx-acts"><a href="${dirUrl(pt.la, pt.lo)}" target="_blank" rel="noopener">DIRECTIONS ↗</a>${opt.addStop ? `<button type="button" class="pri" data-drop="${pt.la},${pt.lo}">📍 ADD AS A STOP</button>` : ''}</div></div>`;
 }

 /* ---------- live loading for the map view ---------- */
 const cellsIn = (b, size) => {const out = [];
  for (let y = Math.floor(b.getSouth() / size); y <= Math.floor(b.getNorth() / size); y++)
   for (let x = Math.floor(b.getWest() / size); x <= Math.floor(b.getEast() / size); x++) out.push(x + ':' + y);
  return out};
 const cellBox = (cells, size) => {let w = 1e9, s = 1e9, e = -1e9, n = -1e9;
  cells.forEach(c => {const [x, y] = c.split(':').map(Number); w = Math.min(w, x * size); s = Math.min(s, y * size); e = Math.max(e, (x + 1) * size); n = Math.max(n, (y + 1) * size)});
  return {w, s, e, n}};
 async function loadOfficial(){
  const SIZE = .2, need = cellsIn(map.getBounds(), SIZE).filter(c => !cellsOff.has(c));
  if (!need.length || need.length > 30) return;
  const bb = cellBox(need, SIZE);
  const qs = new URLSearchParams({where:'1=1', geometry:[bb.w, bb.s, bb.e, bb.n].join(','), geometryType:'esriGeometryEnvelope', inSR:'4326', spatialRel:'esriSpatialRelIntersects', outFields:'*', outSR:'4326', returnGeometry:'true', f:'geojson'});
  let okAll = true;
  await Promise.all(OFFICIAL.map(async src => {
   try {const j = await json(src.url + '?' + qs, null, 14000); delete err[src.label];
    for (const f of j.features || []) {const g = f.geometry || {}, c = g.type === 'Point' ? g.coordinates : null; if (!c) continue;
     const p = f.properties || {}, kind = classify(p, src); if (!kind) continue;
     add({la:+c[1], lo:+c[0], kind, osm:false, name:val(p, ['Name','NAME','SiteName','SITE_NAME','Feature','FACILITY','LABEL']) || '', src:src.label, props:p})}}
   catch (e) {okAll = false; err[src.label] = e.name === 'AbortError' ? 'timed out' : e.message}}));
  if (okAll) need.forEach(c => cellsOff.add(c));
 }
 async function loadOsm(){
  const SIZE = .05, need = cellsIn(map.getBounds(), SIZE).filter(c => !cellsOsm.has(c));
  if (!need.length || need.length > 24) return;
  const bb = cellBox(need, SIZE), box4 = [bb.s, bb.w, bb.n, bb.e].map(n => n.toFixed(5)).join(',');
  const q = `[out:json][timeout:15][bbox:${box4}];(nwr[amenity=parking];nwr[parking=layby];nwr[highway=trailhead];nwr[information=trailhead];node[barrier~"^(gate|lift_gate)$"];node[entrance][name];);out center tags;`;
  let j = null, last = '';
  for (const ep of OVERPASS) {try {j = await json(ep, {method:'POST', body:new URLSearchParams({data:q})}, 17000); if (j.remark && /error|timeout|memory/i.test(j.remark)) throw Error('busy'); break} catch (e) {j = null; last = e.name === 'AbortError' ? 'timed out' : e.message}}
  if (!j) {err.OpenStreetMap = last || 'unavailable'; return}
  delete err.OpenStreetMap;
  for (const el of j.elements || []) {const t = el.tags || {}, kind = osmClass(t), la = el.lat != null ? el.lat : el.center && el.center.lat, lo = el.lon != null ? el.lon : el.center && el.center.lon;
   if (kind && isFinite(la) && isFinite(lo)) add({la:+la, lo:+lo, kind, osm:true, name:t.name || '', src:'OpenStreetMap', props:t})}
  need.forEach(c => cellsOsm.add(c));
 }
 let timer = null;
 function refresh(){clearTimeout(timer); timer = setTimeout(async () => {
  if (!st.P && !st.E) return status();
  const z = map.getZoom(); busy++; status();
  try {if (z >= ZOFF) await loadOfficial(); if (z >= ZOSM) await loadOsm()} finally {busy--; status()}
 }, 450)}
 function status(){
  if (!statEl) return;
  if (!st.P && !st.E) {statEl.textContent = ''; return}
  const z = map.getZoom(), b = map.getBounds();
  let shown = 0; pts.forEach(p => {if (st[KIND[p.kind].g] && b.contains([p.la, p.lo])) shown++});
  const parts = [];
  if (busy) parts.push('Loading parking and entrances…');
  else parts.push(shown + ' shown in this view.');
  if (z < ZOFF) parts.push('Zoom in closer (level ' + ZOFF + '+) to load agency GIS points. Until then only the KPC park file points show.');
  else if (z < ZOSM) parts.push('Zoom in a little more (level ' + ZOSM + '+) to add OpenStreetMap points.');
  const e = Object.keys(err); if (e.length) parts.push('Not reachable right now: ' + e.join(', ') + '.');
  statEl.textContent = parts.join(' ');
 }

 /* ---------- overlaps layer ---------- */
 let ovReady = null;
 function buildOverlaps(){
  return ovReady || (ovReady = overlapData().then(gj => {
   const poly = L.geoJSON({type:'FeatureCollection', features:gj.features.filter(f => /Polygon/.test(f.geometry.type))}, {pane:'kxov',
    style:f => f.properties.kind === '2fer' ? {color:'#a67c00', weight:2, opacity:.95, fillColor:'#f2c230', fillOpacity:.38} : {color:'#5e2d82', weight:2, opacity:.95, fillColor:'#a66bd3', fillOpacity:.32},
    onEachFeature:(f, l) => l.on('click', e => {if (opt.busy && opt.busy()) return; L.popup({maxWidth:300, minWidth:210, autoPanPadding:[14, 14]}).setLatLng(e.latlng).setContent(overlapCard(f.properties, e.latlng, opt.addStop)).openOn(map)})});
   const lines = gj.features.filter(f => f.geometry.type === 'MultiLineString');
   const under = L.geoJSON({type:'FeatureCollection', features:lines}, {pane:'kxovl', interactive:false, style:{color:'#111', weight:10, opacity:.45}});
   const top = L.geoJSON({type:'FeatureCollection', features:lines}, {pane:'kxovl', style:{color:'#f2c230', weight:6, opacity:1, dashArray:'12 7'},
    onEachFeature:(f, l) => l.on('click', e => {if (opt.busy && opt.busy()) return; L.popup({maxWidth:300, minWidth:210}).setLatLng(e.latlng).setContent(overlapCard(f.properties, e.latlng, opt.addStop)).openOn(map)})});
   const pts2 = L.layerGroup(gj.features.filter(f => f.geometry.type === 'Point').map(f => {const c = f.geometry.coordinates, ll = L.latLng(c[1], c[0]);
    const m = L.marker(ll, {pane:'kxpin', icon:L.divIcon({className:'', html:'<span class="kx-sota">▲</span>', iconSize:[22, 22], iconAnchor:[11, 11], popupAnchor:[0, -10]}), title:'SOTA summit inside a POTA park: ' + f.properties.sota[0][0]})
     .bindPopup(() => overlapCard(f.properties, ll, opt.addStop), {maxWidth:300, minWidth:210});
    hover(m); return m}));
   [poly, under, top, pts2].forEach(x => x.addTo(lay.O));
   built = true;
   return gj;
  }).catch(e => {ovReady = null; if (legendEl) legendEl.insertAdjacentHTML('beforeend', '<div class="kx-stat">Overlap file could not load: ' + esc(e.message) + '</div>'); throw e}));
 }

 function apply(){
  ['P', 'E'].forEach(g => st[g] ? lay[g].addTo(map) : map.removeLayer(lay[g]));
  if (st.O) {buildOverlaps().catch(() => {}); lay.O.addTo(map)} else map.removeLayer(lay.O);
  if (legendEl) legendEl.hidden = !st.O;
  if (btn) btn.classList.toggle('on', st.P || st.E || st.O);
  if (box) box.querySelectorAll('input[data-kx]').forEach(i => i.checked = !!st[i.dataset.kx]);
  store.set(KEY, st); status(); refresh();
  listeners.forEach(fn => fn(Object.assign({}, st)));
 }

 const Ctl = L.Control.extend({options:{position:opt.position || 'topright'}, onAdd(){
  const d = L.DomUtil.create('div', 'kx-ctl');
  d.innerHTML = `<button type="button" class="kx-btn" aria-expanded="false">🅿️ Parking &amp; Overlaps ▾</button><div class="kx-box" hidden>
   <label><input type="checkbox" data-kx="P">🅿️ Parking</label>
   <label><input type="checkbox" data-kx="E">🚪 Entrances</label>
   <div class="kx-lg"><span class="kx-key off"></span>Solid green ring = official agency data</div>
   <div class="kx-lg"><span class="kx-key osm"></span>Dashed ring = OpenStreetMap (unverified)</div>
   ${opt.addStop ? '<div class="kx-lg"><span class="kx-key mine"></span>Gold numbered pin = your stop or your spot</div>' : ''}
   <div class="kx-lg">🅿️ parking · 🚗 pull-off · 🚪 entrance · 🚧 gate · 🥾 trailhead · ⛵ boat access</div>
   <div class="kx-stat" data-kxstat></div>
   <div class="kx-h">Park Overlaps</div>
   <label><input type="checkbox" data-kx="O">Show Park Overlaps</label>
   <div data-kxlegend hidden>
    <div class="kx-lg"><span class="kx-sw" style="background:#f2c230;border:2px solid #a67c00"></span>Possible POTA 2-Fer (2+ POTA refs)</div>
    <div class="kx-lg"><span class="kx-sw" style="background:repeating-linear-gradient(90deg,#f2c230 0 7px,transparent 7px 11px);height:5px;border:1px solid #111"></span>Trail inside another POTA park</div>
    <div class="kx-lg"><span class="kx-sw" style="background:#a66bd3;border:2px solid #5e2d82"></span>POTA + WWFF or other combo</div>
    <div class="kx-lg"><span class="kx-sota" style="width:16px;height:16px;font-size:9px">▲</span>SOTA summit inside a POTA park</div>
    <div class="kx-stat">Tap a highlight for details. Verify before activating.</div>
   </div></div>`;
  L.DomEvent.disableClickPropagation(d); L.DomEvent.disableScrollPropagation(d);
  btn = d.querySelector('.kx-btn'); box = d.querySelector('.kx-box'); statEl = d.querySelector('[data-kxstat]'); legendEl = d.querySelector('[data-kxlegend]');
  btn.onclick = () => {box.hidden = !box.hidden; btn.setAttribute('aria-expanded', String(!box.hidden)); status()};
  d.addEventListener('change', e => {const k = e.target.dataset.kx; if (!k) return; st[k] = e.target.checked; apply()});
  return d}});
 new Ctl().addTo(map);
 map.on('moveend', () => {status(); refresh()});
 const fold = () => {if (box && !box.hidden) {box.hidden = true; btn.setAttribute('aria-expanded', 'false')}};
 map.on('click dragstart', fold);   // tapping or dragging the map closes the panel, so it never hides the map on a phone
 document.addEventListener('click', e => {const b = e.target.closest('[data-kxcopy]'); if (!b) return; const v = b.dataset.kxcopy;
  (navigator.clipboard ? navigator.clipboard.writeText(v) : Promise.reject()).then(() => {b.textContent = 'COPIED'}).catch(() => prompt('Copy the GPS coordinates:', v))});
 if (opt.parks) Promise.resolve(opt.parks).then(addStatic).catch(() => {});
 else fetch('kpc-ky-data.json', {cache:'force-cache'}).then(r => r.json()).then(j => addStatic(j.parks)).catch(() => {});
 apply();
 return {
  setOverlaps(v){st.O = !!v; apply()},
  overlapsOn(){return !!st.O},
  set(k, v){st[k] = !!v; apply()},
  state(){return Object.assign({}, st)},
  onChange(fn){listeners.push(fn)},
  points(){return [...pts.values()].map(p => ({la:p.la, lo:p.lo, kind:p.kind, osm:p.osm, name:p.name, src:p.src}))},
  ready(){return buildOverlaps()}
 };
}

window.KPCX = {attach, hover, overlapData, overlapIndex, overlapCard, KINDTXT};
})();
