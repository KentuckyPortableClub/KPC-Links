/* place-name labels over satellite (Esri). Oct 16: an iPhone-only CARTO version was tried and taken out again:
   CARTO now answers 'API KEY REQUIRED' (Brandon's iPhone screenshot). Same labels on every device. */
window.kpcPlaceLabels=window.kpcPlaceLabels||function(z){var o={maxZoom:19};if(z)o.zIndex=z;
 return L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',o)};
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
    usace: { name: 'Army Corps of Engineers', col: [255, 140, 56], on: true },
    other: { name: 'City, county, private, military (no park number)', col: [255, 110, 216], on: false }
  };
  const GK = Object.keys(GROUPS);
  const store = {
    get() { try { return JSON.parse(localStorage.getItem('kpcPadG') || 'null'); } catch (e) { return null; } },
    set(v) { try { localStorage.setItem('kpcPadG', JSON.stringify(v)); } catch (e) {} }
  };
  const saved = store.get(); if (saved) GK.forEach(k => { if (k in saved) GROUPS[k].on = !!saved[k]; });
  const css = c => `rgb(${c.join(',')})`;

  const GI = {}; GK.forEach((k, i) => GI[k] = i + 1);
  /* does this browser change pixels read back from a canvas? (checked once) */
  let noisy = null;
  const NOISY = () => {
    if (noisy !== null) return noisy;
    try {
      const c = document.createElement('canvas'); c.width = c.height = 16; const x = c.getContext('2d');
      x.fillStyle = 'rgb(163,146,222)'; x.fillRect(0, 0, 16, 16); x.fillStyle = 'rgb(99,221,255)'; x.fillRect(4, 4, 8, 8);
      const d = x.getImageData(0, 0, 16, 16).data; let bad = 0;
      for (let i = 0; i < d.length; i += 4) { const inn = (i / 4 % 16) >= 4 && (i / 4 % 16) < 12 && Math.floor(i / 64) >= 4 && Math.floor(i / 64) < 12, w = inn ? [99, 221, 255] : [163, 146, 222];
        if (d[i] !== w[0] || d[i + 1] !== w[1] || d[i + 2] !== w[2] || d[i + 3] !== 255) bad++; }
      noisy = bad > 0;
    } catch (e) { noisy = true; }
    return noisy;
  };
  function smooth(cat, S) {
    const o = new Uint8Array(S * S), n = new Uint16Array(GK.length + 1);
    for (let y = 0; y < S; y++) for (let xx = 0; xx < S; xx++) {
      n.fill(0);
      for (let dy = -1; dy <= 1; dy++) { const yy = y + dy; if (yy < 0 || yy >= S) continue;
        for (let dx = -1; dx <= 1; dx++) { const x2 = xx + dx; if (x2 < 0 || x2 >= S) continue; n[cat[yy * S + x2]]++; } }
      let b = 0; for (let k = 1; k < n.length; k++) if (n[k] > n[b]) b = k; o[y * S + xx] = b;
    }
    return o;
  }
  function classify(r, g, b) {
    let best = 0, bd = 1e9;
    for (let i = 0; i < CAT.length; i++) { const c = CAT[i][0], d = (r - c[0]) ** 2 + (g - c[1]) ** 2 + (b - c[2]) ** 2; if (d < bd) { bd = d; best = i; } }
    return best + 1;   // 0 = nothing there
  }

  /* Add 'Satellite + Streets + Official Boundaries' to a page's map choices and 'Official boundaries' as a checkbox.
     base / over are the objects handed to L.control.layers. Returns the KPCPad result (or null). */
  const ESRI = 'https://server.arcgisonline.com/ArcGIS/rest/services/';
  window.KPCPadMenu = function (map, base, over, key, dflt) {   /* dflt (Oct 17): on when this key was never set (Kentucky Park Control) */
    if (!window.L || !window.KPCPad) return null;
    const pad = window.KPCPad(map), NAME = 'Satellite + Streets + Official Boundaries';
    base[NAME] = L.layerGroup([L.tileLayer(ESRI + 'World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, attribution: 'Imagery © Esri, Maxar, Earthstar Geographics' }),
      L.tileLayer(ESRI + 'Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, zIndex: 8 }),
      kpcPlaceLabels(9)]);
    over['Official boundaries (PAD-US)'] = pad.layer;
    const k = key || 'kpcPadOn'; let on = !!dflt; try { const v = localStorage.getItem(k); if (v !== null) on = v === '1'; } catch (e) {}
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
        /* the tile handed to the map is a plain picture (img): some Android browsers draw big canvas tiles on top of
           the map buttons. The repainting happens on an off-screen canvas. */
        const S = 512, t = document.createElement('canvas'); t.width = t.height = S;
        const out = document.createElement('img'); out.alt = ''; out.setAttribute('role', 'presentation');
        if (c.z < MINZ) { setTimeout(() => done(null, out), 0); return out; }
        const finish = () => {
          const give = u => { out.onload = () => { if (u.startsWith('blob:')) setTimeout(() => URL.revokeObjectURL(u), 1000); done(null, out); }; out.onerror = () => done(null, out); out.src = u; };
          try { if (t.toBlob) t.toBlob(b => b ? give(URL.createObjectURL(b)) : done(null, out), 'image/png'); else give(t.toDataURL('image/png')); } catch (e) { done(null, out); }
        };
        const n = 2 ** c.z, w = 2 * EXT / n, x0 = -EXT + c.x * w, y1 = EXT - c.y * w;
        const url = `${SRV}?bbox=${x0},${y1 - w},${x0 + w},${y1}&bboxSR=3857&imageSR=3857&size=${S},${S}&dpi=192&format=png32&transparent=true&f=image`;
        const draw = (img, raw) => {
          const x = t.getContext('2d'); x.drawImage(img, 0, 0, S, S);
          if (raw) { if (opts.skipKY) cutKY(x, c, S, kyRings); return; }
          let d; try { d = x.getImageData(0, 0, S, S); } catch (e) { x.clearRect(0, 0, S, S); x.globalAlpha = .45; x.drawImage(img, 0, 0, S, S); return; }
          const p = d.data; let cat = new Uint8Array(S * S);
          for (let i = 0, j = 0; j < cat.length; i += 4, j++) {
            if (p[i + 3] < 60) continue;
            const k = classify(p[i], p[i + 1], p[i + 2]); if (GROUPS[CAT[k - 1][1]].on) cat[j] = GI[CAT[k - 1][1]];   // compare by group, not by legend colour
          }
          /* Oct 18 (Brandon's phone: whole areas painted solid): some phone browsers add 'privacy noise' to pictures read
             from a canvas, so every pixel looked like an edge. Smooth the groups first (3x3 majority) when the read-back is noisy. */
          if (NOISY()) cat = smooth(cat, S);
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
          /* safety: an outline tile is mostly empty inside. If over half the land pixels came out as 'edge', the picture was
             noisy: draw nothing rather than a solid blob. */
          let land = 0, edge = 0; for (let j = 0; j < cat.length; j++) if (cat[j]) { land++; if (v[j]) edge++; }
          if (land > 3000 && edge > land * .5) { x.clearRect(0, 0, S, S); return; }
          for (let j = 0, i = 0; j < cat.length; j++, i += 4) {
            const k = cat[j]; if (!k) { p[i + 3] = 0; continue; }
            const col = GROUPS[GK[k - 1]].col;
            p[i] = col[0]; p[i + 1] = col[1]; p[i + 2] = col[2]; p[i + 3] = v[j] ? 255 : 0;   // outline only, inside left clear (Brandon Oct 16)
          }
          x.putImageData(d, 0, 0);
          if (opts.skipKY) cutKY(x, c, S, kyRings);
        };
        const img = new Image(); img.crossOrigin = 'anonymous';
        img.onload = () => { ok++; draw(img, false); finish(); tellStatus(); };
        img.onerror = () => {                       /* no CORS? show the picture faintly instead */
          const im2 = new Image();
          im2.onload = () => { ok++; out.style.opacity = .45; out.onload = () => done(null, out); out.src = url; tellStatus(); };   /* can't repaint: show it faintly as it is */
          im2.onerror = () => { fails++; done(null, out); tellStatus(); };
          im2.src = url;
        };
        let kyRings = [];
        if (opts.skipKY) kyReady().then(r => { kyRings = r; img.src = url; }); else img.src = url;
        return out;
      }
    });
    const layer = new Pad({ tileSize: 256, maxZoom: 19, zIndex: 6, attribution: 'Boundaries: USGS PAD-US' });

    const legend = L.control({ position: opts.keyPos || 'topleft' });
    legend.onAdd = () => {
      const d = L.DomUtil.create('div', 'kpc-pad-key');
      /* starts folded as a small button so it never covers the map or its buttons; tap to open (remembered) */
      let open = false; try { open = localStorage.getItem('kpcPadKeyOpen') === '1'; } catch (e) {}
      d.classList.toggle('open', open);
      d.innerHTML = '<button type="button" class="kpc-pad-tg" aria-expanded="' + open + '"><i class="sw"></i>BOUNDARIES <span>' + (open ? '▾' : '▸') + '</span></button><div class="kpc-pad-body"><b>OFFICIAL BOUNDARIES (USGS PAD-US)</b>' + GK.map(k => `<label><input type="checkbox" data-g="${k}"${GROUPS[k].on ? ' checked' : ''}><i style="border-color:${css(GROUPS[k].col)};background:${css(GROUPS[k].col)}33"></i>${GROUPS[k].name}</label>`).join('') +
        '<small>Public land from the US government\'s map of protected areas. A park\'s own map can differ: check it before you set up.</small></div><small class="kpc-pad-st"></small>';
      statusEl = d.querySelector('.kpc-pad-st'); tellStatus();
      const tg = d.querySelector('.kpc-pad-tg');
      tg.onclick = () => { open = !open; d.classList.toggle('open', open); tg.setAttribute('aria-expanded', open); tg.querySelector('span').textContent = open ? '▾' : '▸'; try { localStorage.setItem('kpcPadKeyOpen', open ? '1' : '0'); } catch (e) {} };
      L.DomEvent.disableClickPropagation(d); L.DomEvent.disableScrollPropagation(d);
      d.querySelectorAll('input').forEach(b => b.onchange = () => { GROUPS[b.dataset.g].on = b.checked; const v = {}; GK.forEach(k => v[k] = GROUPS[k].on); store.set(v); layer.redraw(); });
      return d;
    };
    map.on('zoomend', tellStatus);
    if (!document.getElementById('kpc-pad-css')) {
      const s = document.createElement('style'); s.id = 'kpc-pad-css';
      s.textContent = '.kpc-pad-key{background:rgba(10,10,10,.88);color:#f3efe4;border-radius:8px;font:12px/1.35 system-ui,sans-serif;max-width:240px;box-shadow:0 2px 8px rgba(0,0,0,.35)}' +
        '.kpc-pad-tg{all:unset;cursor:pointer;display:flex;gap:6px;align-items:center;padding:6px 9px;font:700 11px/1 system-ui,sans-serif;letter-spacing:.06em;color:#f0c96b}' +
        '.kpc-pad-tg .sw{width:14px;height:10px;border:2px solid #ffd633;border-right-color:#38e8ff;border-bottom-color:#38e8ff;border-radius:2px}' +
        '.kpc-pad-body{display:none;padding:0 10px 8px;max-height:min(46vh,260px);overflow:auto}.kpc-pad-key.open .kpc-pad-body{display:block}' +
        '.kpc-pad-key b{display:block;color:#f0c96b;font-size:10.5px;letter-spacing:.06em;margin-bottom:4px}.kpc-pad-key label{display:flex;gap:6px;align-items:center;margin:3px 0;cursor:pointer}' +
        '.kpc-pad-key i:not(.sw){flex:0 0 14px;height:12px;border:2px solid;border-radius:2px}.kpc-pad-key small{display:block;color:#cfc6b2;margin-top:4px;font-size:10.5px}.kpc-pad-key small:empty{display:none}' +
        '.leaflet-top,.leaflet-bottom{transform:translateZ(0)}.kpc-pad-key .kpc-pad-st{color:#ffd23f;padding:0 9px 6px;margin:0}@media(max-width:600px){.kpc-pad-key{max-width:190px;font-size:11px}}';
      document.head.appendChild(s);
    }
    if (opts.legend !== false) { layer.on('add', () => legend.addTo(map)); layer.on('remove', () => legend.remove()); }
    return { layer, legend };
  };
})();
