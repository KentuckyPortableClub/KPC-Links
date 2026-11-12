/* KPC Virginia birding layer (Nov 8, Brandon: "Yes, layer + list"). OPTIONAL, OFF by default.
   The Virginia Bird & Wildlife Trail (POTA US-9935) has no route line: the park is its official site points
   (Virginia DWR). data/va-birding-sites.json = {pts: [[lon, lat, site_id, name, loop], ...]}, loaded only when the layer is turned on.
   KPCVaBirding(map) returns a Leaflet layer group. */
(function () {
  'use strict';
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  window.KPCVaBirding = function (map) {
    const g = L.layerGroup(); let busy = false, done = false;
    if (!map.getPane('kpcVaBird')) { map.createPane('kpcVaBird'); map.getPane('kpcVaBird').style.zIndex = 395; }
    const pop = p => `<div class="us-pop"><b>${esc(p[3])}</b><div class="meta">Virginia Bird &amp; Wildlife Trail site <b>${esc(p[2])}</b> · ${esc(p[4])}</div>` +
      `<div class="meta" style="margin-top:6px">One of the official trail sites (Virginia DWR). The trail is POTA park <b>US-9935</b>: check its POTA page and the site's own rules and access before you set up.</div>` +
      `<div class="acts" style="margin-top:8px"><a href="https://pota.app/#/park/US-9935" target="_blank" rel="noopener" style="font-weight:800">POTA PAGE ↗</a></div></div>`;
    async function load() {
      if (done || busy || !map.hasLayer(g)) return; busy = true;
      try {
        const u = 'data/va-birding-sites.json';
        const d = await ((window.KPC && KPC.dataUrl) ? KPC.dataUrl(u) : fetch(u)).then(r => r.json());
        (d.pts || []).forEach(p => {
          const m = L.circleMarker([p[1], p[0]], { pane: 'kpcVaBird', radius: 5, color: '#1b1b1b', weight: 1.5, fillColor: '#9be564', fillOpacity: .95 });
          m.bindPopup(pop(p), { maxWidth: 300 }); m.bindTooltip(esc(p[3]) + ' · VA birding trail site'); g.addLayer(m);
        });
        done = true;
      } catch (e) { /* no signal: try again next time it is turned on */ } finally { busy = false; }
    }
    g.on('add', load);
    return g;
  };
})();
