/* KPC trails layer: national trails + (Oct 16) state trails, National Recreation Trails and rail-trail parks from data/trails/index-state.json.
   Was: KPC national trails layer (US Trip Planner + Park Commander). National Scenic / Historic Trails that are POTA parks,
   official routes from data/trails (refreshed monthly by .github/workflows/kpc-us-trails.yml). Only trails crossing the
   map view are loaded. Own SVG pane under the park dots so a tap on a dot still opens the dot.
   KPCTrails(map, {skipKY:true}) leaves out the parts inside Kentucky (Park Commander has Kentucky's own trail layers). */
(function () {
  'use strict';
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  let KY = null;
  const kyP = () => KY || (KY = fetch('kpc-ky-counties-hd.json').then(r => r.json()).then(a => a.map(c => { const r = c.r[0] || []; let x0 = 180, y0 = 90, x1 = -180, y1 = -90; c.r.forEach(rg => rg.forEach(([x, y]) => { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; })); return { r: c.r, bb: [x0, y0, x1, y1] }; })).catch(() => []));
  const inRing = (x, y, r) => { let ins = false; for (let i = 0, j = r.length - 1; i < r.length; j = i++) { const xi = r[i][0], yi = r[i][1], xj = r[j][0], yj = r[j][1]; if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) ins = !ins; } return ins; };
  const inKY = (C, x, y) => x > -89.6 && x < -81.9 && y > 36.4 && y < 39.2 && C.some(c => x >= c.bb[0] && x <= c.bb[2] && y >= c.bb[1] && y <= c.bb[3] && c.r.some(rg => inRing(x, y, rg)));
  /* cut every line where it enters Kentucky, keep the outside pieces */
  function dropKY(f, C) {
    const out = [];
    (f.geometry.coordinates || []).forEach(line => { let cur = []; line.forEach(p => { if (inKY(C, p[0], p[1])) { if (cur.length > 1) out.push(cur); cur = []; } else cur.push(p); }); if (cur.length > 1) out.push(cur); });
    return { type: 'Feature', properties: f.properties, geometry: { type: 'MultiLineString', coordinates: out } };
  }
  window.KPCTrails = function (map, opts) {
    opts = opts || {};
    const g = L.layerGroup(), done = {}; let IDX = null, busy = false;
    if (!map.getPane('kpcTrails')) { map.createPane('kpcTrails'); map.getPane('kpcTrails').style.zIndex = 390; }
    const rend = L.svg({ pane: 'kpcTrails', padding: .5 });
    const KIND = { NST: ['National Scenic Trail', '#ff5fa2', null], NHT: ['National Historic Trail', '#ffb347', '9 6'], ST: ['State Trail', '#3ddc84', null], NRT: ['National Recreation Trail', '#b388ff', '4 5'], TP: ['Trail park', '#3ddc84', null] };
    const pop = t => { const k = KIND[t.kind] || KIND.ST; return `<div class="us-pop"><b>${esc(t.name)}</b><div class="meta">POTA <b>${esc(t.ref)}</b> · ${esc(t.type || k[0])}${t.km ? ' · about ' + t.km + ' km of trail drawn' : ''}</div>` +
      `<div class="meta" style="margin-top:6px">${t.official === false ? 'Line from <b>OpenStreetMap</b> (a volunteer map, usually close but <b>not official</b>).' : 'Official route from the ' + esc(t.by) + '.'} A trail is one POTA park along its whole length: check the trail's POTA page for where you can set up.</div>` +
      `<div class="acts" style="margin-top:8px"><a href="https://pota.app/#/park/${encodeURIComponent(t.ref)}" target="_blank" rel="noopener" style="font-weight:800">POTA PAGE ↗</a></div></div>`; };
    async function load() {
      if (!map.hasLayer(g) || busy) return; busy = true;
      try {
        if (!IDX) IDX = [].concat(...await Promise.all(['data/trails/index.json', 'data/trails/index-state.json'].map(u => fetch(u).then(r => r.ok ? r.json() : []).catch(() => []))));   /* national + state / recreation trails */
        const C = opts.skipKY ? await kyP() : null;
        const b = map.getBounds().pad(.3), W = b.getWest(), S = b.getSouth(), E = b.getEast(), N = b.getNorth();
        for (const t of IDX) {
          if (done[t.ref] || t.bbox[0] > E || t.bbox[2] < W || t.bbox[1] > N || t.bbox[3] < S) continue; done[t.ref] = 1;
          fetch('data/trails/' + t.ref + '.json').then(r => r.json()).then(f => {
            if (C && C.length) f = dropKY(f, C);
            if (!f.geometry.coordinates.length) return;
            const casing = L.geoJSON(f, { renderer: rend, interactive: false, style: { color: '#1b1b1b', weight: 6, opacity: .55 } });
            const k = KIND[t.kind] || KIND.ST, line = L.geoJSON(f, { renderer: rend, style: { color: k[1], weight: 3, opacity: .95, dashArray: k[2] } });
            line.bindPopup(pop(t), { maxWidth: 300 }); line.bindTooltip(t.name, { sticky: true });
            g.addLayer(casing); g.addLayer(line);
          }).catch(() => { delete done[t.ref]; });
        }
      } finally { busy = false; }
    }
    g.on('add', load); map.on('moveend', load);
    return g;
  };
})();
