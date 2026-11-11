/* >>> kpc_released (KPC owner, 2026-11-11): the same block is in kpc-bounds.js, kpc-padus-layer.js, kpc-us-planner.js and kpc-gps.js (a test keeps them equal).
   The public map reads RELEASED files only: data/released/RELEASED.json (asked for fresh every page load) lists, per working file name,
   its released file(s) and each one's own version, so a changed file shows at once and an unchanged one stays cached.
   KPCREL.get('data/outlines/US-FL.geojson.gz') -> the parsed file (parts put together), or null when it is not released.
   An area that was never released (no entry in RELEASED.json) reads the working file as before.
   The Map Rep pages set window.KPC_WORKING_COPY = true before this file: they always read the working copy (the key being reviewed).
   Nov 11 (job 2): ONE part scheme for released and working files (kpc_release.split): a file over 1 MB is part 1 under its own name
   plus <stem>.p2<ext> ... ; part 1 carries kpc_part = [1, N, tag]. The working-copy path reads part 1, then parts 2..N, and puts them
   together with the same join; parts of two different saves (another tag) or a missing part = nothing, never half a file.
   An outline too big for one part is in pieces (kpc_piece = [k, M], same properties): the join puts its polygons back together. */
(function (w) {
  if (!w || w.KPCREL || typeof w.fetch !== 'function') return;
  var P = null, AREA = [[/^(outlines\/US-|us-key\/)/, 'US'], [/^ca-key\//, 'CA'], [/^world-key\//, 'world']];
  function index() { return P || (P = w.fetch('data/released/RELEASED.json', { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : {}; }).catch(function () { return {}; })); }
  function parse(r) {
    if (!r || !r.ok) return null;
    return r.arrayBuffer().then(function (ab) {
      var u8 = new Uint8Array(ab);
      if (u8.length >= 2 && u8[0] === 0x1f && u8[1] === 0x8b) {
        if (typeof DecompressionStream !== 'function') throw new Error('gzip');
        return new Response(new Blob([ab]).stream().pipeThrough(new DecompressionStream('gzip'))).text().then(JSON.parse);
      }
      return JSON.parse(new TextDecoder().decode(ab));
    });
  }
  function pieces(fs) {   /* Nov 11: the pieces of one big outline (kpc_piece = [k, M]) become one MultiPolygon again, in order */
    var by = {}, out = [], ok = true;
    fs.forEach(function (f) {
      var k = f && f.kpc_piece; if (!k) { out.push(f); return; }
      var r = (f.properties || {}).ref, g = by[r];
      if (!g) { g = by[r] = { f: Object.assign({}, f, { geometry: { type: 'MultiPolygon', coordinates: [] } }), n: k[1], got: 0 }; delete g.f.kpc_piece; out.push(g.f); }
      if (k[0] !== g.got + 1 || k[1] !== g.n) ok = false;
      g.f.geometry.coordinates = g.f.geometry.coordinates.concat((f.geometry || {}).coordinates || []); g.got++;
    });
    return ok && Object.keys(by).every(function (r) { return by[r].got === by[r].n; }) ? out : null;
  }
  function join(docs) {
    if (docs.some(function (d) { return !d; })) return null;            /* a missing part = not released (never half a file) */
    var k0 = docs[0].kpc_part;                                          /* Nov 11: parts must all be of the same save (same N and tag) */
    if (k0 && (docs.length !== k0[1] || docs.some(function (d, i) { var k = d.kpc_part || []; return k[0] !== i + 1 || k[1] !== k0[1] || k[2] !== k0[2]; }))) return null;
    if (docs.length === 1) return docs[0];
    var out = Object.assign({}, docs[0]); delete out.kpc_part;
    if (Array.isArray(out.features)) { out.features = pieces([].concat.apply([], docs.map(function (d) { return d.features || []; }))); if (!out.features) return null; }
    if (out.parks && !Array.isArray(out.parks)) out.parks = Object.assign.apply(null, [{}].concat(docs.map(function (d) { return d.parks || {}; })));
    return out;
  }
  function partName(path, i) { return i < 2 ? path : String(path).replace(/(\.geojson\.gz|\.json)$/, '.p' + i + '$1'); }
  function more(path, d, one) {   /* Nov 11: a working file in parts: part 1 says how many (kpc_part), parts 2..N are read the same way */
    var k = d && d.kpc_part, list = [Promise.resolve(d)];
    if (!k || !(k[1] > 1)) return Promise.resolve(d);
    for (var i = 2; i <= k[1]; i++) list.push(one(partName(path, i)));
    return Promise.all(list).then(join);
  }
  function urls(path) {
    var rel = String(path).replace(/^data\//, '').replace(/\?.*$/, '');
    return index().then(function (d) {
      var a = AREA.filter(function (x) { return x[0].test(rel); })[0];
      if (w.KPC_WORKING_COPY === true || !a || !(d.areas || {})[a[1]]) return null;   /* a review page (Map Rep sets KPC_WORKING_COPY) or an area not released yet: the working file */
      return ((d.files || {})[rel] || []).map(function (f) { return 'data/released/' + f[0] + '?v=' + f[1]; });
    });
  }
  function get(path, working) {
    return urls(path).then(function (list) {
      /* nothing released for it: the working file, read exactly as before this block existed (the caller's own fetch and r.json(); only an outline .gz is unpacked) */
      if (list === null) {
        if (working) { var wk = function (p) { return working(p).then(function (r) { return r && r.ok ? r.json() : null; }); }; return wk(path).then(function (d) { return more(path, d, wk); }); }
        var day = new Date().toISOString().slice(0, 10), rd = function (c) { return function (p) { return w.fetch(p + '?v=' + day, { cache: c }).then(parse); }; };
        return rd('force-cache')(path).then(function (d) {   /* parts of two saves in the browser cache: read them all once more, fresh */
          return more(path, d, rd('force-cache')).then(function (j) { return j || !(d && d.kpc_part) ? j : rd('reload')(path).then(function (d2) { return more(path, d2, rd('reload')); }); });
        });
      }
      if (!list.length) return null;
      return Promise.all(list.map(function (u) { return w.fetch(u, { cache: 'force-cache' }).then(parse); })).then(join);
    }).catch(function () { return null; });
  }
  w.KPCREL = { get: get, urls: urls, index: index };
})(typeof window !== 'undefined' ? window : null);
/* <<< kpc_released */
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
  window.KPCPadMenu = function (map, base, over, key, dflt) {   /* dflt (Oct 17): on when this key was never set (Kentucky Park Map) */
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


  window.kpcKeyOutlines = window.kpcKeyOutlines || (function () {
    const cache = {}, caCache = {}, wCache = {};
    const day = () => new Date().toISOString().slice(0, 10);
    const dfetch = (u, opt) => (window.KPC && KPC.dataUrl) ? KPC.dataUrl(u, opt) : fetch(u, opt);
    function getJson(url) {
      return dfetch(url, { cache: 'force-cache' }).then(r => r.ok ? r.json() : Promise.reject())
        .catch(() => fetch(url, { cache: 'reload' }).then(r => r.ok ? r.json() : null))
        .catch(() => null);
    }
    async function gunzipJson(res) {
      const ab = await res.arrayBuffer(), u8 = new Uint8Array(ab);
      let text;
      if (u8.length >= 2 && u8[0] === 0x1f && u8[1] === 0x8b) {
        if (typeof DecompressionStream !== 'function') throw new Error('gzip');
        text = await new Response(new Blob([ab]).stream().pipeThrough(new DecompressionStream('gzip'))).text();
      } else text = new TextDecoder().decode(ab);
      return JSON.parse(text);
    }
    function load(st) {
      st = String(st || '').replace(/^US-/i, '').toUpperCase();
      if (!st || st === 'KY') return Promise.resolve(null);
      if (!cache[st]) {
        cache[st] = (window.KPCREL ? KPCREL.get('data/outlines/US-' + st + '.geojson.gz')   /* Nov 11: the released file(s), each with its own version */
          : fetch('data/outlines/US-' + st + '.geojson.gz?v=' + day(), { cache: 'force-cache' }).then(r => r.ok ? gunzipJson(r) : null))
          .then(j => {
            if (!j || !Array.isArray(j.features)) return null;
            const by = {};
            j.features.forEach(f => { const r = (f.properties || {}).ref; if (r) by[r] = f; });
            return { features: j.features, by, area: (j.kpc && j.kpc.area) || ('US-' + st) };
          })
          .catch(() => null);
      }
      return cache[st];
    }
    /* Published per-park Canada outlines already on the site (data/canada-bounds/<REF>.json). No new files. */
    function loadCanada(ref) {
      ref = String(ref || '').toUpperCase();
      if (!/^CA-\d/.test(ref)) return Promise.resolve(null);
      if (!caCache[ref]) {
        const url = 'data/canada-bounds/' + encodeURIComponent(ref) + '.json?v=' + day();
        caCache[ref] = getJson(url).then(j => {
          if (!j) return null;
          const fs = (j.type === 'FeatureCollection' ? (j.features || []) : [j]).filter(f => f && f.geometry);
          if (!fs.length) return null;
          fs.forEach(f => {
            const p = f.properties || (f.properties = {});
            if (!p.ref) p.ref = ref;
            if (!p.name) p.name = p.cpcad || ref;
            if (!p.g) p.g = p.approx ? 'approximate' : 'official';
          });
          return { features: fs, area: ref };
        }).catch(() => null);
      }
      return caCache[ref];
    }
    function worldToFeat(ref, b) {
      if (!b || !b.r || !b.r.length) return null;
      return { type: 'Feature', properties: { ref, name: b.n || ref, g: 'official', src: b.s || '' },
        geometry: { type: 'MultiPolygon', coordinates: b.r.map(r => [r]) } };
    }
    /* Saved world shards (data/world-bounds/CC/n.json, 100 parks each) already published on KPC-Data
       and the world-bounds branch. World-key JSON has joins but no geometry; do not live-fetch agency maps. */
    function loadWorldShard(cc, n) {
      cc = String(cc || '').toUpperCase(); n = +n;
      if (!/^[A-Z]{2}$/.test(cc) || cc === 'US' || cc === 'CA' || !isFinite(n) || n < 0) return Promise.resolve(null);
      const key = cc + '/' + n;
      if (!wCache[key]) {
        const rel = 'data/world-bounds/' + cc + '/' + n + '.json?v=' + day();
        const raw = 'https://raw.githubusercontent.com/KentuckyPortableClub/KPC-Links/world-bounds/data/world-bounds/' + cc + '/' + n + '.json';
        wCache[key] = getJson(rel)
          .then(j => j || fetch(raw).then(r => r.ok ? r.json() : null).catch(() => null))
          .then(j => {
            if (!j || typeof j !== 'object') return null;
            const features = [];
            Object.keys(j).forEach(ref => { const f = worldToFeat(ref, j[ref]); if (f) features.push(f); });
            return features.length ? { features, area: key } : null;
          })
          .catch(() => null);
      }
      return wCache[key];
    }
    function loadWorldRef(ref) {
      ref = String(ref || '').toUpperCase();
      const m = /^([A-Z]{2})-(\d+)$/.exec(ref);
      if (!m || m[1] === 'US' || m[1] === 'CA') return Promise.resolve(null);
      return loadWorldShard(m[1], Math.floor(parseInt(m[2], 10) / 100));
    }
    let caRows = null, caRowsP = null;
    function canadaRows() {
      if (caRows) return Promise.resolve(caRows);
      return caRowsP || (caRowsP = getJson('data/canada.json?v=' + day()).then(j => {
        const rows = (j && j.rows) || [];
        caRows = rows.filter(r => r && r[0] === 'POTA' && /^CA-/.test(r[1]) && isFinite(r[3]) && isFinite(r[4]))
          .map(r => ({ ref: r[1], la: r[3], lo: r[4] }));
        return caRows;
      }).catch(() => (caRows = [])));
    }
    return { load, loadCanada, loadWorldShard, loadWorldRef, canadaRows };
  })();

  window.KPCPad = function (map, opts) {
    opts = opts || {}; if (opts.kyOfficial || opts.usOfficial) opts.skipKY = true; const MINZ_ = opts.minz || MINZ;   /* Oct 30: a page may ask for outlines sooner (US Trip Planner = 7) */
    let fails = 0, ok = 0, statusEl = null, missingNames = [];
    const tellStatus = () => {
      if (!statusEl) return;
      if (opts.usOfficial) {
        statusEl.textContent = map.getZoom() < MINZ_ ? 'Zoom in closer (county level) to see official outlines.'
          : (missingNames.length ? ('No saved outline yet for ' + missingNames.join(', ') + '.') : '');
        return;
      }
      statusEl.textContent = map.getZoom() < MINZ_ ? 'Zoom in closer (county level) to see the boundaries.'
        : fails > 3 && !ok ? 'The official boundary map is not answering right now. Try again later.' : '';
    };
    const Pad = L.GridLayer.extend({
      createTile(c, done) {
        /* the tile handed to the map is a plain picture (img): some Android browsers draw big canvas tiles on top of
           the map buttons. The repainting happens on an off-screen canvas. */
        const S = 512, t = document.createElement('canvas'); t.width = t.height = S;
        const out = document.createElement('img'); out.alt = ''; out.setAttribute('role', 'presentation');
        if (c.z < MINZ_) { setTimeout(() => done(null, out), 0); return out; }
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
    const layer = opts.usOfficial
      ? L.layerGroup([], { attribution: 'Boundaries: saved US, Canada, and world key outlines' })
      : new Pad({ tileSize: 256, maxZoom: 19, zIndex: 6, attribution: 'Boundaries: USGS PAD-US' });

    const legend = L.control({ position: opts.keyPos || 'topleft' });
    legend.onAdd = () => {
      const d = L.DomUtil.create('div', 'kpc-pad-key');
      /* starts folded as a small button so it never covers the map or its buttons; tap to open (remembered) */
      let open = false; try { open = localStorage.getItem('kpcPadKeyOpen') === '1'; } catch (e) {}
      d.classList.toggle('open', open);
      d.innerHTML = opts.usOfficial
        ? ('<button type="button" class="kpc-pad-tg" aria-expanded="' + open + '"><i class="sw"></i>BOUNDARIES <span>' + (open ? '▾' : '▸') + '</span></button><div class="kpc-pad-body"><b>OFFICIAL OUTLINES (SAVED KEY FILES)</b>' +
          '<small>Thin official POTA park outlines from the US key\'s saved files, loaded for the states on screen. A park\'s own map can differ: check it before you set up.' +
          (opts.kyOfficial ? ' In Kentucky, official outlines are the same saved state and federal files Park Commander uses.' : '') +
          ' If a state has no saved file yet, a note appears instead of a background map.</small></div><small class="kpc-pad-st"></small>')
        : ('<button type="button" class="kpc-pad-tg" aria-expanded="' + open + '"><i class="sw"></i>BOUNDARIES <span>' + (open ? '▾' : '▸') + '</span></button><div class="kpc-pad-body"><b>OFFICIAL BOUNDARIES (USGS PAD-US)</b>' + GK.map(k => `<label><input type="checkbox" data-g="${k}"${GROUPS[k].on ? ' checked' : ''}><i style="border-color:${css(GROUPS[k].col)};background:${css(GROUPS[k].col)}33"></i>${GROUPS[k].name}</label>`).join('') +
        '<small>Public land from the US government\'s map of protected areas. A park\'s own map can differ: check it before you set up.' + (opts.kyOfficial ? ' In Kentucky, official outlines are the same saved state and federal files Park Commander uses, drawn as thin lines.' : '') + '</small></div><small class="kpc-pad-st"></small>');
      statusEl = d.querySelector('.kpc-pad-st'); tellStatus();
      const tg = d.querySelector('.kpc-pad-tg');
      tg.onclick = () => { open = !open; d.classList.toggle('open', open); tg.setAttribute('aria-expanded', open); tg.querySelector('span').textContent = open ? '▾' : '▸'; try { localStorage.setItem('kpcPadKeyOpen', open ? '1' : '0'); } catch (e) {} };
      L.DomEvent.disableClickPropagation(d); L.DomEvent.disableScrollPropagation(d);
      d.querySelectorAll('input').forEach(b => b.onchange = () => { GROUPS[b.dataset.g].on = b.checked; const v = {}; GK.forEach(k => v[k] = GROUPS[k].on); store.set(v); if (layer.redraw) layer.redraw(); });
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
    if (opts.usOfficial) attachUsOfficial(map, layer, { minz: MINZ_, parksInView: opts.parksInView, onMissing: names => { missingNames = names || []; tellStatus(); } });
    if (opts.kyOfficial) attachKyOfficial(map, layer);
    return { layer, legend };
  };

  /* Nov 10: the US Trip Planner was drawing official boundaries from a PAD-US raster export.
     That paints state land as a thick, blocky cyan outline, clips at tile edges, and misses
     parks the saved Kentucky files already have (Green River SNA, Barren River Lake State
     Resort Park, Brigadoon SNP, Marrowbone WMA, and others). When kyOfficial is on, Kentucky
     is cut out of the raster (skipKY) and those saved vector files are drawn as thin SVG,
     the same outlines as Park Commander. No new services*.arcgis.com calls. */
  const KY_OFFICIAL = {
    bstate:{name:'State parks',file:'ky-state-parks.geojson',color:'#2fa84f'},
    bwma:{name:'WMAs & public hunting areas',file:'ky-hunting-areas.geojson',color:'#f08a1c'},
    bsnp:{name:'State nature preserves',file:'ky-nature-preserves.geojson',color:'#a25ee0'},
    bsna:{name:'State natural areas',file:'ky-natural-areas.geojson',color:'#e2559f'},
    bdbnfo:{name:'Daniel Boone NF (Forest Service land)',file:'ky-dbnf-owned.geojson',color:'#2f7fd6',own:true},
    bdbnf:{name:'Forest boundary line (Daniel Boone)',file:'ky-dbnf.geojson',color:'#2f7fd6',proc:true},
    bnps:{name:'National Park Service',file:'ky-nps.geojson',color:'#9b6a3c'},
    bwild:{name:'Wild river corridors',file:'ky-wild-rivers.geojson',color:'#16b3c0'},
    bwilder:{name:'Wilderness areas',file:'ky-wilderness.geojson',color:'#c6e03a'},
    bfws:{name:'Wildlife refuges & fish hatcheries',file:'ky-fws.geojson',color:'#5ab0ff'},
    busace:{name:'Army Corps of Engineers land',file:'ky-usace.geojson',color:'#ff8c38',corps:true},
    bpad:{name:'More official park outlines',file:'ky-padus-parks.geojson',color:'#e8b04a'},
    bkpc:{name:'OpenStreetMap outlines (unofficial)',file:'ky-kpc-drawn.geojson',color:'#ffd400',kpc:true}
  };
  function attachKyOfficial(map, host) {
    if (!window.L || !map || !map.createPane) return;
    if (!map.getPane('kyoff')) {
      const p = map.createPane('kyoff');
      p.style.zIndex = 450;
    }
    const rend = L.svg({ pane: 'kyoff', padding: 0.5 });
    const group = L.layerGroup();
    const ownRef = f => { const r = (f && f.properties || {}).ref; return typeof r === 'string' && /^[A-Z0-9]{1,4}-\d{4,5}$/.test(r.trim()) ? r.trim() : ''; };
    const nm = f => (window.kpcAnswerKey && kpcAnswerKey.outlineName(f)) || ((f.properties || {}).NAME || '');
    const joined = f => !!(ownRef(f) || (window.kpcAnswerKey && kpcAnswerKey.keyJoin(f).length));
    const W = 2;   /* thin, crisp SVG stroke — the PAD-US raster outline was many pixels wide */
    function restyle() {
      group.eachLayer(l => {
        if (l.setStyle && l.options && l.options.style) l.setStyle(l.options.style);
        if (l.eachLayer) l.eachLayer(x => { if (x.setStyle && x.options && x.options.style) x.setStyle(x.options.style); });
      });
    }
    if (window.kpcAnswerKey) kpcAnswerKey.loadKey(restyle);
    Object.keys(KY_OFFICIAL).forEach(k => {
      const s = KY_OFFICIAL[k];
      const url = s.file + '?v=20261110us';
      const load = () => fetch(url, { cache: 'force-cache' }).then(r => r.ok ? r.json() : Promise.reject())
        .catch(() => fetch(url, { cache: 'reload' }).then(r => r.ok ? r.json() : null));
      load().then(j => {
        if (!j || !Array.isArray(j.features)) return;
        (j.features || []).forEach(f => { f._lk = k; });
        const st = f => {
          if (s.proc) return { color: s.color, weight: 1.6, opacity: 0.75, fill: false, dashArray: '6 8', className: 'kpc-kyoff' };
          if (s.corps) return { color: s.color, weight: 2.6, opacity: 1, fill: true, fillOpacity: 0, className: 'kpc-kyoff' };
          if (s.kpc) return { color: s.color, weight: 3, opacity: 1, fill: true, fillOpacity: 0, dashArray: '12 5 2 5', className: 'kpc-kyoff' };
          const has = s.own || joined(f);
          /* Same idea as Park Commander: a joined official park is a solid, clearly visible line
             (WMA orange especially), not a 2 px nearly-empty stroke on satellite. */
          return has
            ? { color: s.color, weight: 3.5, opacity: 1, fillColor: s.color, fillOpacity: 0.22, dashArray: null, className: 'kpc-kyoff' }
            : { color: '#ff2a2a', weight: 2.5, opacity: 1, fill: true, fillOpacity: 0, dashArray: '2 6', className: 'kpc-kyoff' };
        };
        const lay = L.geoJSON(j, { pane: 'kyoff', renderer: rend, style: st, className: 'kpc-kyoff',
          onEachFeature: (f, l) => l.bindPopup(() => `<b>${(nm(f) || s.name).replace(/[<>]/g, '')}</b><div style="font-size:12px;color:#555">${s.name}</div>`, { maxWidth: 260 })
        });
        group.addLayer(lay);
      }).catch(() => {});
    });
    const sync = () => { if (map.hasLayer(host)) { if (!map.hasLayer(group)) group.addTo(map); } else if (map.hasLayer(group)) map.removeLayer(group); };
    host.on('add', sync); host.on('remove', sync);
    map.whenReady(sync);
    if (map.hasLayer(host)) group.addTo(map);
  }

  /* Nov 10: official outlines outside Kentucky come from published saved files only,
     drawn as thin SVG, never the PAD-US raster, and no new outline files are generated.
     US: data/outlines/US-XX.geojson.gz (states in view). Canada: data/canada-bounds/<REF>.json
     for parks in view. World: data/world-bounds/CC/n.json shards where those files exist
     (currently a subset of countries). A missing file is "no saved outline yet". */
  function attachUsOfficial(map, host, cfg) {
    if (!window.L || !map || !map.createPane) return;
    cfg = cfg || {};
    const MINZ = cfg.minz || 7;
    if (!map.getPane('usoff')) {
      const p = map.createPane('usoff');
      p.style.zIndex = 440;
    }
    const rend = L.svg({ pane: 'usoff', padding: 0.5 });
    /* when usOfficial, host is an empty LayerGroup used as the on/off overlay */
    const useHost = !!(host && host.addLayer && host.eachLayer && !host.redraw);
    const group = useHost ? host : L.layerGroup();
    const loaded = {};
    const W = 2;
    const style = f => {
      const g = (f.properties || {}).g;
      if (g && g !== 'official') return { color: '#c47a12', weight: W, opacity: 0.9, fill: false, dashArray: '6 6', className: 'kpc-usoff' };
      return { color: '#c9a227', weight: W, opacity: 0.95, fillColor: '#c9a227', fillOpacity: 0, className: 'kpc-usoff' };
    };
    const nm = f => ((f.properties || {}).name || (f.properties || {}).ref || '');
    let borders = null;
    const bordersP = fetch('kpc-us-states.json').then(r => r.ok ? r.json() : []).then(a => (borders = a || [])).catch(() => (borders = []));
    function hitsBox(p, box) {
      /* True shape test: a state's overall bbox can cover a neighbor (New York's
         rectangle reaches into Vermont). Use vertices, view corners, and edges. */
      const [x0, y0, x1, y1] = box;
      const inRect = (x, y) => x >= x0 && x <= x1 && y >= y0 && y <= y1;
      const inRing = (x, y, r) => {
        let ins = false;
        for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
          const xi = r[i][0], yi = r[i][1], xj = r[j][0], yj = r[j][1];
          if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi) ins = !ins;
        }
        return ins;
      };
      const crosses = (ax, ay, bx, by, cx, cy, dx, dy) => {
        const den = (ax - bx) * (cy - dy) - (ay - by) * (cx - dx);
        if (!den) return false;
        const t = ((ax - cx) * (cy - dy) - (ay - cy) * (cx - dx)) / den;
        const u = -((ax - bx) * (ay - cy) - (ay - by) * (ax - cx)) / den;
        return t >= 0 && t <= 1 && u >= 0 && u <= 1;
      };
      const edges = [[x0, y0, x1, y0], [x1, y0, x1, y1], [x1, y1, x0, y1], [x0, y1, x0, y0]];
      const corners = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]];
      const ringHits = r => {
        if (!r || r.length < 2) return false;
        for (let i = 0; i < r.length; i++) if (inRect(r[i][0], r[i][1])) return true;
        for (let i = 0; i < corners.length; i++) if (inRing(corners[i][0], corners[i][1], r)) return true;
        for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
          const a = r[j], b = r[i];
          for (let k = 0; k < edges.length; k++) {
            const e = edges[k];
            if (crosses(a[0], a[1], b[0], b[1], e[0], e[1], e[2], e[3])) return true;
          }
        }
        return false;
      };
      const walkRings = o => {
        if (!Array.isArray(o) || !o.length) return false;
        if (typeof o[0][0] === 'number') return ringHits(o);
        for (let i = 0; i < o.length; i++) if (walkRings(o[i])) return true;
        return false;
      };
      return walkRings(p);
    }
    function statesInView() {
      if (!borders || !borders.length || !map.getBounds) return [];
      const b = map.getBounds(), box = [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()];
      return borders.filter(s => s && s.a && s.a !== 'KY' && hitsBox(s.p, box)).map(s => s);
    }
    let req = 0;
    function refresh() {
      if (!hostOn()) {
        if (!useHost && map.hasLayer(group)) map.removeLayer(group);
        return;
      }
      if (!useHost && !map.hasLayer(group)) group.addTo(map);
      if (map.getZoom() < MINZ) {
        if (cfg.onMissing) cfg.onMissing([]);
        return;
      }
      const id = ++req;
      Promise.resolve(borders || bordersP).then(() => {
        if (id !== req) return;
        const sts = statesInView();
        const missing = [];
        function addPack(key, pack) {
          if (!pack || loaded[key]) return;
          const feats = (pack.features || []).filter(f => f && f.geometry && (f.properties || {}).g !== 'pin');
          if (!feats.length) return false;
          const fc = { type: 'FeatureCollection', features: feats };
          const lay = L.geoJSON(fc, { pane: 'usoff', renderer: rend, style, className: 'kpc-usoff',
            onEachFeature: (f, l) => l.bindPopup(() => {
              const p = f.properties || {};
              const ref = (p.ref || '').replace(/[<>]/g, '');
              return '<b>' + nm(f).replace(/[<>]/g, '') + '</b>' + (ref ? '<div style="font-size:12px;color:#555">' + ref + '</div>' : '');
            }, { maxWidth: 260 })
          });
          group.addLayer(lay);
          loaded[key] = true;
          return true;
        }
        const KO = window.kpcKeyOutlines;
        const jobs = sts.map(s => (KO ? KO.load(s.a) : Promise.resolve(null)).then(pack => {
          if (!pack) { missing.push(s.n || s.a); return; }
          if (addPack(s.a, pack) === false) missing.push(s.n || s.a);
        }).catch(() => { missing.push(s.n || s.a); }));
        /* Canada: saved per-park files for POTA pins in the viewport (cap so a phone is not asked for thousands). */
        const b = map.getBounds(), c = map.getCenter();
        const CA_CAP = 80;
        const near = (la, lo) => (la - c.lat) * (la - c.lat) + (lo - c.lng) * (lo - c.lng);
        const pins = typeof cfg.parksInView === 'function' ? (cfg.parksInView() || []) : [];
        jobs.push((KO && KO.canadaRows ? KO.canadaRows() : Promise.resolve([])).then(rows => {
          let hits = (rows || []).filter(r => b.contains([r.la, r.lo]));
          pins.forEach(p => { if (p && /^CA-/.test(p.ref) && isFinite(p.la) && isFinite(p.lo) && b.contains([p.la, p.lo]) && !hits.some(h => h.ref === p.ref)) hits.push(p); });
          hits.sort((a, x) => near(a.la, a.lo) - near(x.la, x.lo));
          hits = hits.filter(h => !loaded[h.ref]).slice(0, CA_CAP);
          let i = 0;
          const worker = () => {
            if (i >= hits.length) return Promise.resolve();
            const h = hits[i++];
            return (KO.loadCanada(h.ref)).then(pack => { addPack(h.ref, pack); }).catch(() => {}).then(worker);
          };
          return Promise.all([0, 1, 2, 3, 4, 5, 6, 7].map(() => worker()));
        }));
        /* World: only where a saved world-bounds shard already exists. Pins already on the page (does not add parks). */
        const wSeen = {};
        pins.forEach(p => {
          const ref = p && p.ref && String(p.ref).toUpperCase();
          const m = ref && /^([A-Z]{2})-(\d+)$/.exec(ref);
          if (!m || m[1] === 'US' || m[1] === 'CA') return;
          if (!isFinite(p.la) || !isFinite(p.lo) || !b.contains([p.la, p.lo])) return;
          const key = 'W:' + m[1] + '/' + Math.floor(parseInt(m[2], 10) / 100);
          if (loaded[key] || wSeen[key] || !KO || !KO.loadWorldRef) return;
          wSeen[key] = true;
          jobs.push(KO.loadWorldRef(ref).then(pack => addPack(key, pack)).catch(() => {}));
        });
        Promise.all(jobs).then(() => { if (id === req && cfg.onMissing) cfg.onMissing(missing); });
      });
    }
    const hostOn = () => map.hasLayer(host) || (useHost === false && map.hasLayer(group));
    const sync = () => {
      if (hostOn()) {
        if (!useHost && !map.hasLayer(group)) group.addTo(map);
        refresh();
      } else if (!useHost && map.hasLayer(group)) map.removeLayer(group);
    };
    host.on && host.on('add', sync);
    host.on && host.on('remove', () => { if (!useHost && map.hasLayer(group)) map.removeLayer(group); });
    map.on('moveend', () => { if (hostOn()) refresh(); });
    map.on('zoomend', () => { if (hostOn()) refresh(); });
    map.whenReady(sync);
    if (hostOn()) refresh();
  }

})();
