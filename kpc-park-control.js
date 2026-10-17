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
  const SHOW = Object.assign({ pota: true, kff: false, sota: false }, get('kpcPcShow', {}));
  let D = null, CG = {}, NOTES = {}, map = null, LAY = {}, outline = null, sel = null, ALL = [];
  let TRIP = get('kpcPcTrip', []);

  function kindOf(x) { return /^US-/.test(x.c) ? 'pota' : /^KFF-/.test(x.c) ? 'kff' : 'sota'; }
  function init() {
    map = L.map('pcMap', { zoomControl: true, preferCanvas: true }).setView([37.75, -85.7], 7);
    if (window.KPCLayers) KPCLayers(map); else L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(map);
    if (window.KPCLocate) KPCLocate(map); if (window.KPCFull) KPCFull(map);
    for (const k of ['pota', 'kff', 'sota']) { LAY[k] = L.layerGroup(); if (SHOW[k]) LAY[k].addTo(map); }
    for (const x of ALL) { const k = kindOf(x);
      const m = L.circleMarker([x.la, x.lo], { radius: k === 'sota' ? 5 : 6.5, color: '#fff', weight: 1.4, fillColor: COL[k], fillOpacity: .92 });
      m.bindTooltip(`${x.c} · ${x.n}`); m.on('click', () => pick(x, false)); m.addTo(LAY[k]); x.m = m; }
    count(); chips();
  }
  function count() { const n = ALL.filter(x => SHOW[kindOf(x)]).length; $('pcCount').textContent = n + ' on the map'; }
  function chips() { document.querySelectorAll('[data-pg]').forEach(b => { const k = b.dataset.pg; b.classList.toggle('on', !!SHOW[k]); b.setAttribute('aria-pressed', SHOW[k] ? 'true' : 'false'); }); }
  document.querySelectorAll('[data-pg]').forEach(b => b.onclick = () => { const k = b.dataset.pg; SHOW[k] = !SHOW[k]; put('kpcPcShow', SHOW); if (map) { if (SHOW[k]) LAY[k].addTo(map); else map.removeLayer(LAY[k]); } chips(); count(); });

  const byRef = c => ALL.find(x => x.c.toUpperCase() === String(c).toUpperCase());
  async function pick(x, fly) {
    sel = x; const k = kindOf(x); if (!SHOW[k]) { SHOW[k] = true; put('kpcPcShow', SHOW); LAY[k].addTo(map); chips(); count(); }
    if (fly !== false) map.setView([x.la, x.lo], Math.max(map.getZoom(), k === 'sota' ? 13 : 12));
    info(x); try { history.replaceState(null, '', '?ref=' + encodeURIComponent(x.c)); } catch (e) {}
    if (outline) { map.removeLayer(outline); outline = null; }
    if (k !== 'sota' && window.KPCB && KPCB.kyFor) {
      try { const ref = k === 'kff' && x.p ? x.p : x.c, F = await KPCB.kyFor(ref); if (sel !== x || !F || !F.length) return;
        outline = L.geoJSON({ type: 'FeatureCollection', features: F }, { style: { color: '#f0c96b', weight: 2.5, fill: false }, interactive: false }).addTo(map);
        if (fly !== false) { const b = outline.getBounds(); if (b.isValid()) map.fitBounds(b.pad(.1), { maxZoom: 14 }); } } catch (e) {} }
  }
  function info(x) {
    const k = kindOf(x), lab = { pota: 'POTA PARK', kff: 'KFF (WWFF) REFERENCE', sota: 'SOTA SUMMIT' }[k];
    const page = k === 'pota' ? `https://pota.app/#/park/${x.c}` : k === 'kff' ? `https://wwff.co/directory/?showRef=${x.c}` : `https://sotl.as/summits/${x.c}`;
    const park = k === 'pota' ? x : k === 'kff' && x.p ? byRef(x.p) : null;
    const tipsRef = x.c, tips = NOTES[tipsRef] || 0, cg = park && CG[park.c];
    const also = [];
    if (k === 'pota') { (x.kff || []).forEach(r => { const y = byRef(r); also.push([r, y ? y.n : '', 'Also KFF']); }); (x.sota || []).forEach(r => { const y = byRef(r); also.push([r, y ? y.n : '', 'SOTA summit inside (only counts on top)']); }); (x.tf || []).forEach(r => { const y = byRef(typeof r === 'string' ? r : r.c || r[0]); const rr = typeof r === 'string' ? r : r.c || r[0]; also.push([rr, y ? y.n : '', 'Overlapping boundaries (2-fer)']); }); }
    if (k === 'kff' && park) also.push([park.c, park.n, 'Same place: POTA park']);
    const ap = (park && park.ap) || [];
    $('pcInfo').innerHTML = `<div class="pc-k">${lab}</div><h3>${esc(x.n)}</h3>
      <div class="pc-meta"><span class="pc-ref">${esc(x.c)}</span>${x.co ? ' · ' + esc(x.co) + ' County' : ''}${x.t ? ' · ' + esc(x.t) : ''}${x.ft ? ' · ' + Number(x.ft).toLocaleString() + ' ft' + (x.pts ? ' · ' + x.pts + ' pts' : '') : ''}</div>
      <div class="pc-acts"><a class="gold" href="${dirUrl(x.la, x.lo)}" target="_blank" rel="noopener">🚗 DIRECTIONS</a><button type="button" id="pcAdd">${TRIP.some(t => t.c === x.c) ? '✓ ON MY TRIP' : '+ ADD TO MY TRIP'}</button>
      ${park && park.web ? `<a href="${esc(park.web)}" target="_blank" rel="noopener">OFFICIAL WEBSITE ↗</a>` : ''}${park && park.off ? `<a href="${esc(park.off)}" target="_blank" rel="noopener">OFFICIAL MAP ↗</a>` : ''}${park && park.camp ? `<a href="${esc(park.camp)}" target="_blank" rel="noopener">CAMPING ↗</a>` : ''}
      <a href="${page}" target="_blank" rel="noopener">${k === 'pota' ? 'POTA' : k === 'kff' ? 'WWFF' : 'SOTLAS'} PAGE ↗</a>
      <a href="kpc-park-notes.html#${encodeURIComponent(tipsRef)}">📝 PARK TIPS${tips ? ' (' + tips + ')' : ''}</a>${cg ? `<a href="kpc-campgrounds.html#park-${esc(park.c)}">⛺ PLACES TO STAY</a>` : ''}</div>
      ${also.length ? `<div class="pc-k" style="margin-top:8px">ALSO HERE</div><ul class="pc-list">${also.map(a => `<li><a href="?ref=${encodeURIComponent(a[0])}" data-ref="${esc(a[0])}">${esc(a[0])}</a> ${esc(a[1])} <span class="pc-tag">${esc(a[2])}</span></li>`).join('')}</ul>` : ''}
      ${ap.length ? `<div class="pc-k" style="margin-top:8px">🅿 PARKING &amp; ACCESS POINTS (FROM THE LAND MANAGER)</div><ul class="pc-list">${ap.slice(0, 8).map(p => `<li>${esc(p[2] || 'Access point')} · <a href="${dirUrl(p[0], p[1])}" target="_blank" rel="noopener">DIRECTIONS</a></li>`).join('')}</ul>` : ''}
      <p class="pc-note">GPS ${x.la.toFixed(5)}, ${x.lo.toFixed(5)}${k === 'sota' ? ' · activation zone = within 25 m (82 ft) of the top, no vehicle' : ' · the pin is a guide; the official boundary decides'}</p>`;
    $('pcAdd').onclick = () => { if (!TRIP.some(t => t.c === x.c)) { TRIP.push({ c: x.c, n: x.n, la: x.la, lo: x.lo }); if (TRIP.length > 10) TRIP.shift(); put('kpcPcTrip', TRIP); } trip(); info(x); };
    $('pcInfo').querySelectorAll('[data-ref]').forEach(a => a.onclick = e => { e.preventDefault(); const y = byRef(a.dataset.ref); if (y) pick(y); });
    if (matchMedia('(max-width:900px)').matches) $('pcInfo').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  function trip() {
    const el = $('pcTripL'); if (!TRIP.length) { el.innerHTML = '<p class="pc-empty">Tap <b>+ ADD TO MY TRIP</b> on a park to start a trip.</p>'; return; }
    const last = TRIP[TRIP.length - 1], way = TRIP.slice(0, -1).map(t => t.la + ',' + t.lo).join('|');
    const g = `https://www.google.com/maps/dir/?api=1&destination=${last.la},${last.lo}${way ? '&waypoints=' + encodeURIComponent(way) : ''}`;
    el.innerHTML = `<ol>${TRIP.map((t, i) => `<li><a href="?ref=${encodeURIComponent(t.c)}" data-tr="${i}">${esc(t.c)}</a> ${esc(t.n)}<button type="button" data-rm="${i}" aria-label="Remove">✕</button></li>`).join('')}</ol>
      <div class="pc-acts"><a class="gold" href="${g}" target="_blank" rel="noopener">🗺 OPEN MY TRIP IN GOOGLE MAPS</a><button type="button" id="pcClr">CLEAR</button></div><p class="pc-note">Google Maps starts from where you are and stops at each park in this order. Up to 10 stops.</p>`;
    el.querySelectorAll('[data-rm]').forEach(b => b.onclick = () => { TRIP.splice(+b.dataset.rm, 1); put('kpcPcTrip', TRIP); trip(); if (sel) info(sel); });
    el.querySelectorAll('[data-tr]').forEach(a => a.onclick = e => { e.preventDefault(); const y = byRef(TRIP[+a.dataset.tr].c); if (y) pick(y); });
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
