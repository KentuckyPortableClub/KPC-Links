/* place-name labels over satellite (Esri). Oct 16: an iPhone-only CARTO version was tried and taken out again:
   CARTO now answers 'API KEY REQUIRED' (Brandon's iPhone screenshot). Same labels on every device. */
window.kpcPlaceLabels=window.kpcPlaceLabels||function(z){var o={maxZoom:19};if(z)o.zIndex=z;
 return L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',o)};
/* KPC small shared helpers for the Park Info Finder and the Activation Kit.
   KPCTA.attach(input, onPick): suggestions as you type (Kentucky POTA / WWFF / SOTA from kpc-ky-data.json right away,
   POTA parks anywhere from api.pota.app/lookup, and a typed reference number). Solid panel that covers the page.
   KPCPin(map): tap the map to drop a pin with STREET VIEW, DIRECTIONS (opens the phone's map app) and COPY GPS. */
(function () {
  'use strict';
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const css = document.createElement('style');
  css.textContent = `.kta-wrap{position:relative;flex:1 1 260px;min-width:0;display:flex}.kta-wrap>input{flex:1;min-width:0;width:100%}
.kta{position:absolute;left:0;right:0;top:calc(100% + 4px);z-index:1500;background:#fff;border:1px solid #cbbf9f;border-radius:10px;box-shadow:0 14px 30px rgba(0,0,0,.28);max-height:min(60vh,420px);overflow:auto;display:none;text-align:left}
.kta.on{display:block}.kta button{display:flex;gap:10px;justify-content:space-between;align-items:center;width:100%;padding:11px 14px;border:0;border-bottom:1px solid #eee3cc;background:#fff;color:#171717;font:15px Arial,sans-serif;text-align:left;cursor:pointer}
.kta button:last-child{border-bottom:0}.kta button:hover,.kta button.sel{background:#f6efdc}.kta b{font-family:Georgia,serif;font-weight:700}.kta span{font:900 11px Arial,sans-serif;letter-spacing:.8px;color:#1d5a3a;white-space:nowrap}
.kta .kta-h{padding:7px 14px;font:900 10px Arial,sans-serif;letter-spacing:1.4px;color:#68635a;background:#f6f2ea}
.kpin-pop{font:14px Arial,sans-serif;min-width:190px}.kpin-pop b{display:block;margin-bottom:6px}.kpin-pop a,.kpin-pop button{display:block;width:100%;box-sizing:border-box;margin:5px 0;padding:8px 10px;border-radius:7px;border:1.5px solid #171717;background:#fff;color:#171717!important;font:900 11.5px Arial,sans-serif;letter-spacing:.8px;text-align:center;text-decoration:none;cursor:pointer}
.kpin-pop a.g{background:#d5a63a;border-color:#d5a63a}.kloc-b{min-height:36px;padding:6px 10px;border:2px solid rgba(0,0,0,.25);border-radius:6px;background:#fff;color:#1378ff;font:900 12px Arial,sans-serif;letter-spacing:.6px;cursor:pointer}
.kmap-full{position:fixed!important;inset:0!important;width:100vw!important;height:100vh!important;height:100dvh!important;max-height:none!important;min-height:0!important;margin:0!important;border-radius:0!important;z-index:5000!important}
html.kmap-lock,html.kmap-lock body{overflow:hidden!important}
.kfull-b{display:block;margin-top:6px!important}
.kpin-hint{font-size:12.5px;color:#5b5648;margin:6px 0 0}`;
  document.head.appendChild(css);

  let KY = null;
  const kyP = fetch('kpc-ky-data.json').then(r => r.json()).then(d => { KY = [].concat((d.parks || []).map(p => [p.c, p.n, 'POTA · KY']), (d.kff || []).map(p => [p.c, p.n, 'WWFF · KY']), (d.summits || []).map(p => [p.c, p.n, 'SOTA · KY'])); }).catch(() => { KY = []; });
  const isRef = q => /^[A-Z0-9]{1,4}(\/[A-Z0-9]{2})?-\d{1,5}$/.test(q);
  const prog = r => /\//.test(r) ? 'SOTA' : /FF-/.test(r) ? 'WWFF' : 'POTA';
  const padRef = r => { if (/^\d{3,5}$/.test(r)) r = 'US-' + r;   /* a bare number = a POTA park */
    const m = r.match(/^([A-Z0-9]{1,4}\/[A-Z0-9]{2})-(\d{1,3})$/); if (m) return m[1] + '-' + m[2].padStart(3, '0');
    const k = r.match(/^([A-Z0-9]{1,4})-(\d{1,5})$/); return k ? k[1] + '-' + k[2].padStart(4, '0') : r; };
  /* the real name of a typed number from anywhere (POTA from api.pota.app, WWFF from our weekly copy) */
  const nameCache = {};
  async function refName(r) {
    if (r in nameCache) return nameCache[r];
    let out = null;
    try {
      if (/\//.test(r)) { const [a, b] = r.split('/'); const j = await fetch('https://api2.sota.org.uk/api/summits/' + encodeURIComponent(a) + '/' + encodeURIComponent(b)).then(x => x.ok ? x.json() : null); if (j && j.name) out = [r, j.name, 'SOTA']; }
      else if (/FF-/.test(r)) { const rows = await fetch('data/wwff/' + r.split('-')[0] + '.json').then(x => x.ok ? x.json() : []); const x = rows.find(y => y[0] === r); if (x) out = [r, x[1], 'WWFF' + (x[5] ? ' · ' + x[5] : '')]; }
      else { const j = await fetch('https://api.pota.app/park/' + encodeURIComponent(r)).then(x => x.ok ? x.json() : null); if (j && j.name) out = [r, j.name + (j.parktypeDesc && !new RegExp(j.parktypeDesc, 'i').test(j.name) ? ' ' + j.parktypeDesc : ''), 'POTA' + (j.locationDesc ? ' · ' + String(j.locationDesc).replace(/^US-/, '').split(',')[0] : '')]; }
    } catch (e) {}
    return (nameCache[r] = out);
  }

  function attach(input, onPick, opts) {
    opts = opts || {};
    const wrap = document.createElement('div'); wrap.className = 'kta-wrap';
    input.parentNode.insertBefore(wrap, input); wrap.appendChild(input);
    input.removeAttribute('list'); input.setAttribute('autocomplete', 'off');
    const box = document.createElement('div'); box.className = 'kta'; box.setAttribute('role', 'listbox'); wrap.appendChild(box);
    let t = null, seq = 0, items = [], sel = -1;
    const close = () => { box.classList.remove('on'); sel = -1; };
    const draw = (local, far, q, towns) => {
      towns = towns || [];
      items = []; let h = '';
      const up = padRef(q.toUpperCase().replace(/\s+/g, ''));
      const lookRow = isRef(up) && !local.some(x => x[0] === up) && !far.some(x => x[0] === up);
      if (lookRow) { items.push([up, 'Look up ' + up, prog(up)]); }
      if (local.length) { items.push(...local); }
      if (far.length) items.push(...far);
      if (towns.length) items.push(...towns);
      if (!items.length) { close(); return; }
      let i = 0;
      const row = x => `<button type="button" data-i="${i++}" role="option"><b>${esc(x[1])}</b><span>${esc(x[2])}${x[0] ? ' · ' + esc(x[0]) : ''}</span></button>`;
      const nRef = lookRow ? 1 : 0;
      h += items.slice(0, nRef).map(row).join('');
      if (local.length) h += '<div class="kta-h">KENTUCKY</div>' + local.map(row).join('');
      if (far.length) h += '<div class="kta-h">' + (isRef(up) ? 'FOUND' : 'POTA PARKS EVERYWHERE') + '</div>' + far.map(row).join('');
      if (towns.length) h += '<div class="kta-h">TOWNS: SHOW WHAT\'S NEARBY</div>' + towns.map(row).join('');
      box.innerHTML = h; box.classList.add('on'); sel = -1;
    };
    async function suggest() {
      const q = input.value.trim(), my = ++seq; if (q.length < 2) { close(); return; }
      await kyP;
      const l = q.toLowerCase(), up = padRef(q.toUpperCase().replace(/\s+/g, ''));
      const local = (KY || []).filter(x => x[1].toLowerCase().includes(l) || x[0].startsWith(up)).sort((a, b) => (b[1].toLowerCase().startsWith(l) - a[1].toLowerCase().startsWith(l)) || a[1].localeCompare(b[1])).slice(0, 8);
      draw(local, [], q);
      if (isRef(up)) {                              /* a typed number: show its real name */
        if (local.some(x => x[0] === up)) return;
        const hit = await refName(up); if (my !== seq || !hit) return;
        draw(local, [hit], q); return;
      }
      if (q.length < 3) return;
      /* towns anywhere in the US (kpc-place-suggest.js), when the page asks for them */
      const twP = opts.onTown && window.KPCPlace ? KPCPlace.towns(q).then(a => a.slice(0, 5).map(t => ['', t.v, t.k, { town: 1, la: t.la, lo: t.lo, v: t.v }])).catch(() => []) : Promise.resolve([]);
      let far = [];
      try {
        const c = new AbortController(), tm = setTimeout(() => c.abort(), 8000);
        const L = await fetch('https://api.pota.app/lookup?search=' + encodeURIComponent(q) + '&size=60', { signal: c.signal }).then(r => r.json()); clearTimeout(tm);
        if (my !== seq) return;
        far = (L || []).filter(x => x.type === 'park' && !local.some(y => y[0] === x.value)).sort((a, b) => (/^US-/.test(b.value) - /^US-/.test(a.value))).slice(0, 10).map(x => [x.value, x.display.replace(/^\S+\s+/, ''), 'POTA']);
      } catch (e) {}
      const towns = await twP; if (my !== seq) return;
      draw(local, far, q, towns);
    }
    input.addEventListener('input', () => { clearTimeout(t); t = setTimeout(suggest, 180); });
    input.addEventListener('focus', () => { if (input.value.trim().length >= 2) suggest(); });
    input.addEventListener('keydown', e => {
      const b = box.querySelectorAll('button'); if (!box.classList.contains('on') || !b.length) return;
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); sel = (sel + (e.key === 'ArrowDown' ? 1 : -1) + b.length) % b.length; b.forEach((x, k) => x.classList.toggle('sel', k === sel)); b[sel].scrollIntoView({ block: 'nearest' }); }
      else if (e.key === 'Enter' && sel >= 0) { e.preventDefault(); b[sel].click(); }
      else if (e.key === 'Escape') close();
    });
    box.addEventListener('mousedown', e => e.preventDefault());
    box.addEventListener('click', e => { const b = e.target.closest('button[data-i]'); if (!b) return; const x = items[+b.dataset.i]; close(); input.blur(); if (x[3] && x[3].town) { input.value = x[1]; opts.onTown(x[3]); return; } input.value = x[0]; onPick(x[0], x); });
    document.addEventListener('click', e => { if (!wrap.contains(e.target)) close(); });
    return { close };
  }

  function pin(map, opts) {
    let m = null;
    const ios = /iPhone|iPad|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    const EV = (opts && opts.on) || 'click';   /* Oct 17: Park Control drops pins on long-press / right-click only ('contextmenu') */
    map.on(EV, e => {
      if (opts && opts.skip && opts.skip(e)) return;
      const la = e.latlng.lat.toFixed(6), lo = e.latlng.lng.toFixed(6);
      if (m) m.remove();
      const dir = ios ? `https://maps.apple.com/?daddr=${la},${lo}` : `https://www.google.com/maps/dir/?api=1&destination=${la},${lo}`;
      const html = `<div class="kpin-pop"><b>Dropped pin</b>${la}, ${lo}<a class="g" href="${dir}" target="_blank" rel="noopener">DIRECTIONS (MAP APP) ↗</a><a href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${la},${lo}" target="_blank" rel="noopener">STREET VIEW ↗</a>${ios ? `<a href="https://www.google.com/maps/dir/?api=1&destination=${la},${lo}" target="_blank" rel="noopener">GOOGLE MAPS ↗</a>` : ''}<button type="button" data-copy="${la}, ${lo}">COPY GPS</button><button type="button" data-rm="1">REMOVE PIN</button></div>`;
      m = L.marker(e.latlng, { draggable: true }).addTo(map).bindPopup(opts && opts.extra ? html.replace(/<\/div>$/, opts.extra(la, lo) + '</div>') : html).openPopup();
      m.on('dragend', () => { const p = m.getLatLng(); m.remove(); m = null; map.fire(EV, { latlng: p }); });
    });
    map.on('popupopen', ev => {
      const el = ev.popup.getElement(); if (!el) return;
      el.querySelectorAll('[data-copy]').forEach(b => b.onclick = () => { const v = b.dataset.copy; (navigator.clipboard ? navigator.clipboard.writeText(v) : Promise.reject()).then(() => b.textContent = 'COPIED ✓').catch(() => { window.prompt('Copy the GPS:', v); }); });
      el.querySelectorAll('[data-rm]').forEach(b => b.onclick = () => { if (m) { m.remove(); m = null; } });
      if (opts && opts.onPop) opts.onPop(el, m);
    });
  }
  /* base maps + terrain: Street, Satellite, USGS Topo (US), Terrain (OpenTopoMap, worldwide), plus a Hillshade overlay */
  function layers(map, first, lo) {   /* lo (Oct 17): {padKey, padOn} = its own PAD-US on/off memory + default */
    const B = {
      Street: L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }),
      Satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, attribution: 'Imagery © Esri' }),
      'Satellite + streets': L.layerGroup([
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, attribution: 'Imagery © Esri' }),
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19 }),
        kpcPlaceLabels()]),
      'Topo (USGS, US only)': L.tileLayer('https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}', { maxZoom: 16, attribution: 'USGS The National Map' }),
      'Terrain (OpenTopoMap)': L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', { maxZoom: 17, subdomains: 'abc', attribution: '© OpenStreetMap, SRTM · OpenTopoMap (CC-BY-SA)' })
    };
    const O = { 'Hillshade (terrain shading)': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Elevation/World_Hillshade/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, opacity: .45, attribution: 'Hillshade © Esri' }) };
    const pad = window.KPCPadMenu ? KPCPadMenu(map, B, O, lo && lo.padKey, lo && lo.padOn) : null;   /* official PAD-US boundaries (kpc-padus-layer.js) */
    if (pad && pad.legend && pad.legend.setPosition) pad.legend.setPosition('bottomleft');   /* key at the bottom (Brandon Oct 16) */
    let pick = 'Street'; try { const v = localStorage.getItem('kpcMapBase'); if (B[v]) pick = v; } catch (e) {}
    if (first && B[first]) pick = first;
    B[pick].addTo(map); if (pad && pick === pad.NAME) pad.layer.addTo(map);
    L.control.layers(B, O, { collapsed: true }).addTo(map);
    map.on('baselayerchange', e => { try { localStorage.setItem('kpcMapBase', e.name); } catch (x) {} });
    layers.pad = pad; return B[pick];
  }
  /* "where am I" button: blue dot + accuracy circle + your GPS numbers (tap again to refresh) */
  function locate(map) {
    let dot = null, ring = null;
    const C = L.Control.extend({ options: { position: 'bottomright' }, onAdd() {
      const b = L.DomUtil.create('button', 'kloc-b'); b.type = 'button'; b.title = 'Show where I am'; b.innerHTML = '◎ ME';
      L.DomEvent.disableClickPropagation(b);
      b.onclick = () => {
        if (!navigator.geolocation) { alert('This browser has no GPS.'); return; }
        b.textContent = '…';
        navigator.geolocation.getCurrentPosition(p => {
          b.innerHTML = '◎ ME'; const ll = [p.coords.latitude, p.coords.longitude], acc = Math.round(p.coords.accuracy || 0);
          if (dot) dot.remove(); if (ring) ring.remove();
          if (acc) ring = L.circle(ll, { radius: acc, color: '#1378ff', weight: 1, fillOpacity: .1, interactive: false }).addTo(map);
          const la = ll[0].toFixed(6), lo = ll[1].toFixed(6), ft = Math.round(acc * 3.28084);
          dot = L.circleMarker(ll, { radius: 9, color: '#fff', weight: 3, fillColor: '#1378ff', fillOpacity: 1 }).addTo(map)
            .bindPopup(`<div class="kpin-pop"><b>You are here</b>${la}, ${lo}${acc ? '<br>GPS good to about ±' + (ft < 1000 ? ft + ' ft' : (acc / 1609).toFixed(1) + ' mi') : ''}<button type="button" data-copy="${la}, ${lo}">COPY GPS</button></div>`).openPopup();
          map.setView(ll, Math.max(map.getZoom(), 15));
        }, e => { b.innerHTML = '◎ ME'; alert(e.code === 1 ? 'Location is turned off for this site. Allow it in your browser settings.' : 'Could not get a GPS fix. Try again outside.'); }, { enableHighAccuracy: true, timeout: 20000, maximumAge: 5000 });
      };
      return b; } });
    new C().addTo(map);
  }
  /* full-screen map (works on iPhone too: the map box is stretched over the whole screen) */
  function full(map) {
    const box = map.getContainer(); let on = false, ph = null;
    const C = L.Control.extend({ options: { position: 'bottomright' }, onAdd() {
      const b = L.DomUtil.create('button', 'kloc-b kfull-b'); b.type = 'button'; b.title = 'Full screen map'; b.innerHTML = '⛶ FULL';
      L.DomEvent.disableClickPropagation(b);
      const set = v => {
        on = v; box.classList.toggle('kmap-full', on); document.documentElement.classList.toggle('kmap-lock', on);
        b.innerHTML = on ? '✕ EXIT' : '⛶ FULL'; b.title = on ? 'Exit full screen' : 'Full screen map';
        if (on) { ph = window.scrollY; } else if (ph != null) { window.scrollTo(0, ph); }
        setTimeout(() => map.invalidateSize(), 60);
      };
      b.onclick = () => set(!on);
      document.addEventListener('keydown', e => { if (on && e.key === 'Escape') set(false); });
      return b; } });
    new C().addTo(map);
  }
  /* Oct 17: KPCPin(map, {extra(la, lo) → more popup html, onPop(el, marker)}) (Kentucky Park Control: + ADD THIS SPOT TO MY TRIP) */
  /* ---- Oct 17: KPCHere(map, {piece, onRef}) = tap an outline (zoom 10+) → 'What land is here?' (KY: KPCB.landAt + Army Corps land) ---- */
  /* Oct 17 (Brandon: 'click on a boundary… tell you Name here WMA tract etc.'): tap the map = every outline at that spot, for all three programs */
  let corpsF = null;
  const corps = () => corpsF ? Promise.resolve(corpsF) : fetch('ky-usace.geojson').then(r => r.ok ? r.json() : { features: [] }).then(j => (corpsF = (j.features || []).map(f => (f._bb = KPCB.bbox(f.geometry), f)))).catch(() => (corpsF = []));
  const HCSS = '.pc-here .pc-note{font-size:12.5px;color:#6b6252;margin:6px 0 0}.pc-here .pc-list{margin:4px 0 0;padding:0;list-style:none;font-size:13px}.pc-here .pc-list li{padding:3px 0}.pc-here .pc-list a{color:#7a5410;font-weight:700}.pc-here .pc-tag{display:inline-block;padding:1px 6px;border-radius:999px;font:900 10px Arial;background:#e9f5ec;color:#1f6b3a;border:1px solid #a9d3b4}.pc-here .pc-acts button{margin-top:8px;padding:7px 10px;border-radius:999px;border:1px solid #c9b48a;background:#fff;font:900 11.5px Arial;cursor:pointer}';
  function here(map, opts) { if (!document.getElementById('kpc-here-css')) { const s = document.createElement('style'); s.id = 'kpc-here-css'; s.textContent = HCSS; document.head.appendChild(s); } opts = opts || {}; let tapL = null; const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const PIECE = opts.piece || (() => ({ color: '#f0c96b' }));
    map.on('click', async e => { const t = e.originalEvent && e.originalEvent.target; if (t && (!t.isConnected || (t.closest && t.closest('.leaflet-popup')))) return; const ll = e.latlng;
    /* Oct 17 (Brandon: 'a little too easy to pull up'): only when zoomed in to county level or closer, only on an outline (empty land = nothing),
       a one-line label first ('name · status · more ›'), the full box only on 'more'; real park numbers listed first */
    if (!window.KPCB || !KPCB.landAt || map.getZoom() < 10) return;
    const [A0, C] = await Promise.all([KPCB.landAt(ll.lat, ll.lng), corps()]);
    const co = C.filter(f => { const b = f._bb; return ll.lng >= b[0] && ll.lng <= b[2] && ll.lat >= b[1] && ll.lat <= b[3] && KPCB.inside(ll.lat, ll.lng, f.geometry); });
    if (tapL) { map.removeLayer(tapL); tapL = null; }
    if (!A0.length && !co.length) return;
    const A = A0.filter(a => a.numbered).concat(A0.filter(a => !a.numbered)).slice(0, 5);
    tapL = L.geoJSON({ type: 'FeatureCollection', features: A.map(a => a.f) }, { interactive: false,
      style: f => { const a = A.find(x => x.f === f); return a && a.numbered ? Object.assign({ weight: 4, fill: true, fillOpacity: .08 }, PIECE(f)) : { color: '#ff2a2a', weight: 3, dashArray: '2 6', fill: false }; } }).addTo(map);
    const st = a => a.own.length ? a.own.map(r => r.ref).join(', ') : a.kff.length ? a.kff.map(r => r.ref).join(', ') + ' (KFF only)' : 'no park number';
    const top = A[0];
    const label = top ? `<b>${esc(top.name)}</b> · <span style="color:${top.numbered ? '#1f6b3a' : '#a01818'};font-weight:800">${esc(st(top))}</span>${A.length > 1 ? ` · +${A.length - 1} more here` : ''}`
      : `<b>Army Corps of Engineers land</b>`;
    const li = (a, i) => a.slice(0, 6).map(r => `<li><a href="?ref=${encodeURIComponent(r.ref)}" data-pcref="${esc(r.ref)}">${esc(r.ref)}</a> ${esc(r.name || '')}${i ? ' <span class="pc-tag">' + esc(i(r)) + '</span>' : ''}</li>`).join('');
    const box = a => {
      let h = `<div style="margin:8px 0 2px;font:700 15px/1.25 Georgia,serif">${esc(a.name)}</div><div class="pc-note" style="margin:0">${esc(a.layer)}${a.onLine ? ' · you tapped right on its line' : ''}</div>`;
      if (a.own.length) h += `<ul class="pc-list"><li><b>🌲 POTA:</b></li>${li(a.own)}</ul>`;
      else if (a.kff.length) h += `<p class="pc-note" style="color:#0d5a55;font-weight:800">🌳 KFF (WWFF) reference, no POTA number:</p><ul class="pc-list">${li(a.kff)}</ul>`;
      else h += `<p class="pc-note" style="color:#a01818;font-weight:800;margin:4px 0">🚫 Government land · no park number (may not be open to the public).</p>` + (a.pins.length ? `<div class="pc-note">POTA park pin inside it (only that park’s own land counts):</div><ul class="pc-list">${li(a.pins)}</ul>` : '');
      const kin = a.kffIn.filter(k => !a.kff.some(x => x.ref === k.ref));
      if (kin.length && a.numbered) h += `<div class="pc-note"><b>🌳 KFF here:</b></div><ul class="pc-list">${li(kin)}</ul>`;
      if (a.sota.length) h += `<div class="pc-note"><b>⛰ SOTA summits on this land</b> (SOTA goes by the summit, so these count):</div><ul class="pc-list">${li(a.sota, r => r.ft ? Number(r.ft).toLocaleString() + ' ft' : '')}</ul>`;
      return h; };
    const full = () => '<div style="font:900 11px Arial;letter-spacing:1.4px;color:#7a5410">WHAT LAND IS HERE?</div>' + A.map(box).join('<hr style="border:0;border-top:1px dashed #e2d6bb;margin:8px 0">') +
      co.map(f => { const p = f.properties || {}; return `<p class="pc-note" style="border-left:4px solid #ff8c38;padding-left:6px"><b>Army Corps of Engineers land</b>${p.MANAGER ? ', run by ' + esc(p.MANAGER) : ''}.</p>`; }).join('') +
      `<div class="pc-acts"><button type="button" data-pcpin="1">📌 DROP A PIN HERE</button></div><p class="pc-note" style="margin:2px 0 0">Outlines are guides. The official map decides.</p>`;
    const pop = L.popup({ maxWidth: 300, maxHeight: 300, className: 'pc-here' }).setLatLng(ll)
      .setContent(`<div style="font:13px/1.35 Arial">${label} <a href="#" data-pcmore="1" style="font-weight:800;color:#7a5410;white-space:nowrap">more ›</a></div>`).openOn(map);
    const wire = () => { const el = pop.getElement(); if (!el) return;
      const mo = el.querySelector('[data-pcmore]'); if (mo) mo.onclick = e => { e.preventDefault(); e.stopPropagation(); setTimeout(() => { pop.setContent(full()); wire(); }, 0); };
      el.querySelectorAll('[data-pcref]').forEach(a => a.onclick = e => { e.preventDefault(); map.closePopup(); if (opts.onRef) opts.onRef(a.dataset.pcref); else location.href = '?ref=' + encodeURIComponent(a.dataset.pcref); });
      const pb = el.querySelector('[data-pcpin]'); if (pb) pb.onclick = () => { map.closePopup(); map.fire('contextmenu', { latlng: ll }); }; };
    wire();
    map.once('popupclose', () => { if (tapL) { map.removeLayer(tapL); tapL = null; } });
    });
  }
  window.KPCTA = { attach }; window.KPCPin = pin; window.KPCHere = here; window.KPCLayers = layers; window.KPCLocate = locate; window.KPCFull = full;
})();
