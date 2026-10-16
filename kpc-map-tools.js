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
    map.on('click', e => {
      if (opts && opts.skip && opts.skip(e)) return;
      const la = e.latlng.lat.toFixed(6), lo = e.latlng.lng.toFixed(6);
      if (m) m.remove();
      const dir = ios ? `https://maps.apple.com/?daddr=${la},${lo}` : `https://www.google.com/maps/dir/?api=1&destination=${la},${lo}`;
      const html = `<div class="kpin-pop"><b>Dropped pin</b>${la}, ${lo}<a class="g" href="${dir}" target="_blank" rel="noopener">DIRECTIONS (MAP APP) ↗</a><a href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${la},${lo}" target="_blank" rel="noopener">STREET VIEW ↗</a>${ios ? `<a href="https://www.google.com/maps/dir/?api=1&destination=${la},${lo}" target="_blank" rel="noopener">GOOGLE MAPS ↗</a>` : ''}<button type="button" data-copy="${la}, ${lo}">COPY GPS</button><button type="button" data-rm="1">REMOVE PIN</button></div>`;
      m = L.marker(e.latlng, { draggable: true }).addTo(map).bindPopup(html).openPopup();
      m.on('dragend', () => { const p = m.getLatLng(); m.remove(); m = null; map.fire('click', { latlng: p }); });
    });
    map.on('popupopen', ev => {
      const el = ev.popup.getElement(); if (!el) return;
      el.querySelectorAll('[data-copy]').forEach(b => b.onclick = () => { const v = b.dataset.copy; (navigator.clipboard ? navigator.clipboard.writeText(v) : Promise.reject()).then(() => b.textContent = 'COPIED ✓').catch(() => { window.prompt('Copy the GPS:', v); }); });
      el.querySelectorAll('[data-rm]').forEach(b => b.onclick = () => { if (m) { m.remove(); m = null; } });
    });
  }
  /* base maps + terrain: Street, Satellite, USGS Topo (US), Terrain (OpenTopoMap, worldwide), plus a Hillshade overlay */
  function layers(map, first) {
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
    const pad = window.KPCPadMenu ? KPCPadMenu(map, B, O) : null;   /* official PAD-US boundaries (kpc-padus-layer.js) */
    let pick = 'Street'; try { const v = localStorage.getItem('kpcMapBase'); if (B[v]) pick = v; } catch (e) {}
    if (first && B[first]) pick = first;
    B[pick].addTo(map); if (pad && pick === pad.NAME) pad.layer.addTo(map);
    L.control.layers(B, O, { collapsed: true }).addTo(map);
    map.on('baselayerchange', e => { try { localStorage.setItem('kpcMapBase', e.name); } catch (x) {} });
    return B[pick];
  }
  /* "where am I" button: blue dot + accuracy circle + your GPS numbers (tap again to refresh) */
  function locate(map) {
    let dot = null, ring = null;
    const C = L.Control.extend({ options: { position: 'topleft' }, onAdd() {
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
    const C = L.Control.extend({ options: { position: 'topleft' }, onAdd() {
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
  window.KPCTA = { attach }; window.KPCPin = pin; window.KPCLayers = layers; window.KPCLocate = locate; window.KPCFull = full;
})();
