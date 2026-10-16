/* KPC official public-land layer for Leaflet maps (US Trip Planner).
   Source: USGS PAD-US (Protected Areas Database of the US), The National Map map service, no key.
   The service draws every owner as a solid colour block, which would hide a satellite picture, so each tile is
   repainted here: federal and state land become a bright outline with a light tint, everything else is removed
   (city, county, private, non-profit, tribal, military and easements are not POTA parks). The service's own
   colour for each land manager tells us who runs it (legend checked Oct 16 2026).
   If a browser will not let the page read the picture, the tile is shown faintly as-is instead.
   Use: const pad = KPCPad(map); pad.layer is a Leaflet layer, pad.legend a control. Groups remembered in localStorage kpcPadG. */
(function () {
  'use strict';
  const SRV = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/export';
  const EXT = 20037508.342789244, MINZ = 8;
  /* [legend colour, group]  groups: fed, state, usace, other */
  const CAT = [
    [[134, 198, 108], 'fed'],   // Other Federal (TVA etc.)
    [[242, 220, 145], 'fed'],   // BLM
    [[187, 196, 88], 'other'],  // City
    [[184, 217, 87], 'other'],  // County / regional
    [[128, 62, 57], 'other'],   // Defense (military)
    [[173, 87, 100], 'fed'],    // Fish and Wildlife Service
    [[227, 176, 175], 'other'], // Joint / unknown
    [[230, 71, 71], 'other'],   // Non-profit
    [[112, 161, 112], 'fed'],   // National Park Service
    [[255, 66, 8], 'other'],    // NRCS easements
    [[171, 153, 191], 'state'], // Other state
    [[230, 141, 69], 'other'],  // Private
    [[191, 124, 153], 'state'], // State trust land
    [[163, 146, 222], 'state'], // State fish and wildlife
    [[155, 170, 222], 'state'], // State parks
    [[212, 201, 181], 'other'], // Tribal
    [[99, 221, 255], 'usace'],  // Army Corps of Engineers
    [[0, 92, 230], 'fed'],      // Bureau of Reclamation
    [[137, 189, 42], 'fed'],    // Forest Service
    [[130, 130, 130], 'other']  // anything else
  ];
  const GROUPS = {
    fed: { name: 'Federal land (national forests, parks, refuges, BLM…)', col: [255, 214, 51], on: true },
    state: { name: 'State land (state parks, wildlife areas, forests…)', col: [56, 232, 255], on: true },
    usace: { name: 'Army Corps of Engineers (usually NOT a POTA park)', col: [255, 140, 56], on: true },
    other: { name: 'City, county, private, military (not POTA)', col: [255, 110, 216], on: false }
  };
  const GK = Object.keys(GROUPS);
  const store = {
    get() { try { return JSON.parse(localStorage.getItem('kpcPadG') || 'null'); } catch (e) { return null; } },
    set(v) { try { localStorage.setItem('kpcPadG', JSON.stringify(v)); } catch (e) {} }
  };
  const saved = store.get(); if (saved) GK.forEach(k => { if (k in saved) GROUPS[k].on = !!saved[k]; });
  const css = c => `rgb(${c.join(',')})`;

  function classify(r, g, b) {
    let best = 0, bd = 1e9;
    for (let i = 0; i < CAT.length; i++) { const c = CAT[i][0], d = (r - c[0]) ** 2 + (g - c[1]) ** 2 + (b - c[2]) ** 2; if (d < bd) { bd = d; best = i; } }
    return best + 1;   // 0 = nothing there
  }

  /* Add 'Satellite + Streets + Official Boundaries' to a page's map choices and 'Official boundaries' as a checkbox.
     base / over are the objects handed to L.control.layers. Returns the KPCPad result (or null). */
  const ESRI = 'https://server.arcgisonline.com/ArcGIS/rest/services/';
  window.KPCPadMenu = function (map, base, over, key) {
    if (!window.L || !window.KPCPad) return null;
    const pad = window.KPCPad(map), NAME = 'Satellite + Streets + Official Boundaries';
    base[NAME] = L.layerGroup([L.tileLayer(ESRI + 'World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, attribution: 'Imagery © Esri, Maxar, Earthstar Geographics' }),
      L.tileLayer(ESRI + 'Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, zIndex: 8 }),
      L.tileLayer(ESRI + 'Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, zIndex: 9 })]);
    over['Official boundaries (PAD-US)'] = pad.layer;
    const k = key || 'kpcPadOn'; let on = false; try { on = localStorage.getItem(k) === '1'; } catch (e) {}
    map.whenReady(() => { if (on && !map.hasLayer(pad.layer)) pad.layer.addTo(map); });
    map.on('baselayerchange', e => { if (e.name === NAME && !map.hasLayer(pad.layer)) pad.layer.addTo(map); });
    map.on('overlayadd', e => { if (e.layer === pad.layer) try { localStorage.setItem(k, '1'); } catch (x) {} });
    map.on('overlayremove', e => { if (e.layer === pad.layer) try { localStorage.setItem(k, '0'); } catch (x) {} });
    pad.NAME = NAME; return pad;
  };
  /* opts.skipKY: leave Kentucky out (Park Commander already has Kentucky's own official files).
     Kentucky is cut out of each tile using the county outlines (US Census, kpc-ky-counties-hd.json). */
  let KYC = null;
  const kyReady = () => KYC || (KYC = fetch('kpc-ky-counties-hd.json').then(r => r.json()).then(a => a.map(c => c.r)).catch(() => []));
  function cutKY(x, c, S, rings) {
    const n = 2 ** c.z * S, X = lo => (lo + 180) / 360 * n - c.x * S,
      Y = la => { const r = la * Math.PI / 180; return (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * n - c.y * S; };
    if (X(-82) < 0 || X(-89.6) > S || Y(36.4) < 0 || Y(39.2) > S) return;   /* tile is nowhere near Kentucky */
    x.save(); x.globalAlpha = 1; x.globalCompositeOperation = 'destination-out'; x.beginPath();
    rings.forEach(poly => poly.forEach(ring => ring.forEach(([lo, la], i) => i ? x.lineTo(X(lo), Y(la)) : x.moveTo(X(lo), Y(la)))));
    x.fill('nonzero'); x.lineWidth = 2; x.stroke(); x.restore();
  }
  window.KPCPad = function (map, opts) {
    opts = opts || {};
    let fails = 0, ok = 0, statusEl = null;
    const tellStatus = () => {
      if (!statusEl) return;
      statusEl.textContent = map.getZoom() < MINZ ? 'Zoom in closer (county level) to see the boundaries.'
        : fails > 3 && !ok ? 'The official boundary map is not answering right now. Try again later.' : '';
    };
    const Pad = L.GridLayer.extend({
      createTile(c, done) {
        const S = 512, t = document.createElement('canvas'); t.width = t.height = S;
        if (c.z < MINZ) { setTimeout(() => done(null, t), 0); return t; }
        const n = 2 ** c.z, w = 2 * EXT / n, x0 = -EXT + c.x * w, y1 = EXT - c.y * w;
        const url = `${SRV}?bbox=${x0},${y1 - w},${x0 + w},${y1}&bboxSR=3857&imageSR=3857&size=${S},${S}&dpi=192&format=png32&transparent=true&f=image`;
        const draw = (img, raw) => {
          const x = t.getContext('2d'); x.drawImage(img, 0, 0, S, S);
          if (raw) { if (opts.skipKY) cutKY(x, c, S, kyRings); return; }
          let d; try { d = x.getImageData(0, 0, S, S); } catch (e) { x.clearRect(0, 0, S, S); x.globalAlpha = .45; x.drawImage(img, 0, 0, S, S); return; }
          const p = d.data, cat = new Uint8Array(S * S);
          for (let i = 0, j = 0; j < cat.length; i += 4, j++) {
            if (p[i + 3] < 60) continue;
            const k = classify(p[i], p[i + 1], p[i + 2]); if (GROUPS[CAT[k - 1][1]].on) cat[j] = k;
          }
          /* outline = pixels within R of a change in owner (two quick passes instead of checking a box round every pixel) */
          const R = 3, e = new Uint8Array(S * S);
          for (let y = 0; y < S; y++) for (let xx = 0; xx < S; xx++) {
            const j = y * S + xx;
            if (xx + 1 < S && cat[j] !== cat[j + 1]) { e[j] = 1; e[j + 1] = 1; }
            if (y + 1 < S && cat[j] !== cat[j + S]) { e[j] = 1; e[j + S] = 1; }
          }
          const h = new Uint8Array(S * S);
          for (let y = 0; y < S; y++) { let last = -99; for (let xx = 0; xx < S; xx++) { if (e[y * S + xx]) last = xx; if (xx - last <= R) h[y * S + xx] = 1; } last = 1e9; for (let xx = S - 1; xx >= 0; xx--) { if (e[y * S + xx]) last = xx; if (last - xx <= R) h[y * S + xx] = 1; } }
          const v = new Uint8Array(S * S);
          for (let xx = 0; xx < S; xx++) { let last = -99; for (let y = 0; y < S; y++) { if (h[y * S + xx]) last = y; if (y - last <= R) v[y * S + xx] = 1; } last = 1e9; for (let y = S - 1; y >= 0; y--) { if (h[y * S + xx]) last = y; if (last - y <= R) v[y * S + xx] = 1; } }
          for (let j = 0, i = 0; j < cat.length; j++, i += 4) {
            const k = cat[j]; if (!k) { p[i + 3] = 0; continue; }
            const col = GROUPS[CAT[k - 1][1]].col;
            p[i] = col[0]; p[i + 1] = col[1]; p[i + 2] = col[2]; p[i + 3] = v[j] ? 255 : 46;
          }
          x.putImageData(d, 0, 0);
          if (opts.skipKY) cutKY(x, c, S, kyRings);
        };
        const img = new Image(); img.crossOrigin = 'anonymous';
        img.onload = () => { ok++; draw(img, false); done(null, t); tellStatus(); };
        img.onerror = () => {                       /* no CORS? show the picture faintly instead */
          const im2 = new Image();
          im2.onload = () => { ok++; t.style.opacity = .45; draw(im2, true); done(null, t); tellStatus(); };
          im2.onerror = () => { fails++; done(null, t); tellStatus(); };
          im2.src = url;
        };
        let kyRings = [];
        if (opts.skipKY) kyReady().then(r => { kyRings = r; img.src = url; }); else img.src = url;
        return t;
      }
    });
    const layer = new Pad({ tileSize: 256, maxZoom: 19, zIndex: 6, attribution: 'Official boundaries: USGS PAD-US' });

    const legend = L.control({ position: 'bottomleft' });
    legend.onAdd = () => {
      const d = L.DomUtil.create('div', 'kpc-pad-key');
      d.innerHTML = '<b>OFFICIAL BOUNDARIES (USGS PAD-US)</b>' + GK.map(k => `<label><input type="checkbox" data-g="${k}"${GROUPS[k].on ? ' checked' : ''}><i style="border-color:${css(GROUPS[k].col)};background:${css(GROUPS[k].col)}33"></i>${GROUPS[k].name}</label>`).join('') +
        '<small>Public land from the US government\'s map of protected areas. A park\'s POTA boundary can differ: check the park\'s own map before you set up.</small><small class="kpc-pad-st"></small>';
      statusEl = d.querySelector('.kpc-pad-st'); tellStatus();
      L.DomEvent.disableClickPropagation(d); L.DomEvent.disableScrollPropagation(d);
      d.querySelectorAll('input').forEach(b => b.onchange = () => { GROUPS[b.dataset.g].on = b.checked; const v = {}; GK.forEach(k => v[k] = GROUPS[k].on); store.set(v); layer.redraw(); });
      return d;
    };
    map.on('zoomend', tellStatus);
    if (!document.getElementById('kpc-pad-css')) {
      const s = document.createElement('style'); s.id = 'kpc-pad-css';
      s.textContent = '.kpc-pad-key{background:rgba(10,10,10,.86);color:#f3efe4;padding:8px 10px;border-radius:8px;font:12px/1.35 system-ui,sans-serif;max-width:250px;box-shadow:0 2px 8px rgba(0,0,0,.35)}' +
        '.kpc-pad-key b{display:block;color:#f0c96b;font-size:11px;letter-spacing:.06em;margin-bottom:4px}.kpc-pad-key label{display:flex;gap:6px;align-items:center;margin:3px 0;cursor:pointer}' +
        '.kpc-pad-key i{flex:0 0 14px;height:12px;border:2px solid;border-radius:2px}.kpc-pad-key small{display:block;color:#cfc6b2;margin-top:4px;font-size:10.5px}.kpc-pad-key small:empty{display:none}' +
        '.kpc-pad-key .kpc-pad-st{color:#ffd23f}@media(max-width:600px){.kpc-pad-key{max-width:200px;font-size:11px}.kpc-pad-key small{display:none}.kpc-pad-key .kpc-pad-st{display:block}}';
      document.head.appendChild(s);
    }
    if (opts.legend !== false) { layer.on('add', () => legend.addTo(map)); layer.on('remove', () => legend.remove()); }
    return { layer, legend };
  };
})();
