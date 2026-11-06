/* Mapping desk on kpc-maprep.html. US first. Canada is on. Other countries stay in the catalog and are not queried.
   No drawing tools. Exports are a candidate list, not boundaries.
   Live queries are user-started, one place at a time, and only layers the catalog marks live. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const Lgc = () => window.KPCMapLogic;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  let catalog = null, leads = [], drawLayer = null, pinsP = null, busy = false;

  function out(html) {
    const el = $('mrDeskOut');
    if (el) el.innerHTML = html;
  }
  function placeCode() {
    const sel = $('mrDeskPlace');
    return sel && sel.value ? sel.value : 'KY';
  }
  function regionOf(code) {
    if (!catalog) return 'US';
    const s = catalog.sources.find(x => x.place === code);
    return s ? s.region : (code === 'CA' ? 'CA' : 'US');
  }
  function layersFor(code, liveOnly) {
    if (!catalog) return [];
    const reg = regionOf(code);
    return catalog.sources.filter(s => {
      if (s.place !== code && !(code !== 'CA' && reg === 'CA' && s.place === 'CA' && s.id === 'ca-cpcad')) return false;
      if (liveOnly && !s.live) return false;
      return s.enabled !== false;
    });
  }
  async function loadCatalog() {
    if (catalog) return catalog;
    const r = await fetch('data/maprep/catalog.json');
    if (!r.ok) throw new Error('catalog');
    catalog = await r.json();
    try {
      const ag = await fetch('data/maprep/agencies.json');
      if (ag.ok && Lgc()) Lgc().loadAgencies(await ag.json());
    } catch (e) {}
    try {
      const a = await fetch('data/maprep/abbreviations.json');
      if (a.ok) { const j = await a.json(); if (Lgc()) Lgc().loadRows(j.rows || []); }
    } catch (e) {}
    return catalog;
  }
  function fillPlaces() {
    const sel = $('mrDeskPlace');
    if (!sel || !catalog || sel.dataset.ready) return;
    sel.dataset.ready = '1';
    const places = [];
    const seen = new Set();
    catalog.sources.forEach(s => {
      if (!s.enabled || seen.has(s.place)) return;
      seen.add(s.place);
      places.push(s.place);
    });
    places.sort((a, b) => a.localeCompare(b));
    if (!seen.has('KY')) places.unshift('KY');
    sel.innerHTML = places.map(p => `<option value="${esc(p)}">${esc(p)}${p === 'CA' ? ' · Canada national' : ''}</option>`).join('');
    sel.value = seen.has('KY') ? 'KY' : places[0];
    sel.onchange = paintDirectory;
    paintDirectory();
  }
  function paintDirectory() {
    const host = $('mrDeskDir');
    const G = Lgc();
    if (!host || !G || !G.agencyMatches) return;
    const code = placeCode();
    const rows = G.agencyMatches(code, '');
    host.innerHTML = '<details class="mr-agd" open><summary>AGENCY DIRECTORY · ' + esc(code) + '</summary>' + (rows.length ? rows.map(a => {
      const one = (label, slot) => (slot && slot.url) ? `<a href="${esc(slot.url)}" target="_blank" rel="noopener">${esc(label)}${slot.verified ? '' : ' (unverified)'}</a>` : `<span>${esc(label)}: not stored</span>`;
      return `<p class="mr-help"><b>${esc(a.name)}</b><br>${one('Home', a.home)} · ${one('Finder', a.finder)} · ${one('GIS', a.gis)}</p>`;
    }).join('') : '<p class="mr-help">No directory row for this place.</p>') + '</details>';
  }
  function featName(src, props) {
    const keys = [src.nameField, 'NAME', 'Name', 'Unit_Nm', 'AREANAME', 'PUBLIC_NAM', 'MANAME', 'PROP_NAME', 'NAME_E'].filter(Boolean);
    for (const k of keys) if (props && props[k]) return String(props[k]);
    return src.title;
  }
  function acresOf(src, props, geom) {
    const keys = [src.acresField, 'GIS_Acres', 'ACRES_CAL', 'ACRES', 'ABSOLUTE_ACREAGE'].filter(Boolean);
    for (const k of keys) {
      const n = +((props || {})[k]);
      if (n > 0) return src.acresField === 'O_AREA_HA' || /hectare/i.test(src.acresField || '') ? n * 2.47105 : n;
    }
    return 0;
  }
  function webOf(props) {
    const keys = ['URL', 'Web', 'Webpage', 'HYPERLINK', 'DETAIL', 'website'];
    for (const k of keys) {
      const v = props && props[k];
      if (typeof v === 'string' && /^https?:/i.test(v)) return v;
    }
    return '';
  }
  function accessOf(props) {
    const v = (props && (props.Pub_Access || props.PUB_ACCESS || props.AreaOpen || props.ACCESS)) || '';
    const s = String(v).trim().toUpperCase();
    if (!s) return 'unknown';
    if (s === 'OA' || /^(YES|OPEN)/.test(s)) return 'open';
    if (s === 'XA' || /^(NO|CLOSED)/.test(s)) return 'closed';
    if (s === 'RA' || /RESTRICT|PERMIT|LIMIT/.test(s)) return 'restricted';
    return 'unknown';
  }
  async function arcQuery(src, params) {
    const G = Lgc();
    if (!src || !src.rest) return { skipped: 'no url' };
    if (!src.live) return { skipped: src.whyNotLive || 'not queried' };
    if (G && (G.isBanned(src.rest) || G.servicesHost(src.rest) || G.blockedPlace(src.place) || G.isParcel(src))) return { skipped: 'blocked' };
    const u = src.rest.replace(/\/$/, '') + '/query?' + new URLSearchParams(Object.assign({
      f: 'geojson', where: '1=1', outFields: '*', returnGeometry: 'true', outSR: '4326',
      geometryPrecision: '5', resultRecordCount: '40'
    }, params));
    const r = await fetch(u);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const j = await r.json();
    if (j.error) throw new Error(j.error.message || 'query failed');
    return j;
  }
  async function pool(items, n, job) {
    const out = new Array(items.length);
    let i = 0;
    async function worker() {
      while (i < items.length) {
        const k = i++;
        try { out[k] = await job(items[k], k); }
        catch (e) { out[k] = { error: e.message || String(e) }; }
      }
    }
    await Promise.all(Array.from({ length: Math.min(n, items.length) }, worker));
    return out;
  }
  function mapObj() { return window.KPCMapCheck && KPCMapCheck.map && KPCMapCheck.map(); }
  function clearDraw() {
    const map = mapObj();
    if (drawLayer && map) map.removeLayer(drawLayer);
    drawLayer = null;
  }
  function showShapes(rows) {
    const map = mapObj();
    if (!map || !window.L) return;
    clearDraw();
    if (!$('mrDeskBounds') || !$('mrDeskBounds').checked) return;
    const feats = rows.filter(r => r.f && r.f.geometry).map(r => ({
      type: 'Feature',
      properties: { name: r.name, credit: r.credit, layer: r.layer, parcel: r.parcel ? 1 : 0, props: r.props || {} },
      geometry: r.f.geometry
    }));
    if (!feats.length) return;
    drawLayer = L.geoJSON({ type: 'FeatureCollection', features: feats }, {
      style: { color: '#1d5a3a', weight: 2, fillOpacity: 0.12 },
      onEachFeature: (feat, layer) => {
        layer.bindTooltip(feat.properties.name || '', { sticky: true });
        layer.on('click', e => {
          if (window.L && L.DomEvent) L.DomEvent.stopPropagation(e);
          const G = Lgc();
          const clean = G ? G.publicFields(feat.properties.props, !!feat.properties.parcel) : {};
          const bits = Object.keys(clean).slice(0, 8).map(k => esc(k) + ': ' + esc(clean[k])).join('<br>');
          layer.bindPopup('<b>' + esc(feat.properties.name) + '</b><br>' + esc(feat.properties.layer) + '<br><small>' + esc(feat.properties.credit) + '</small>' + (bits ? '<br>' + bits : '')).openPopup();
        });
      }
    }).addTo(map);
  }
  async function potaPins() {
    if (pinsP) return pinsP;
    pinsP = (async () => {
      const jget = window.KPCB && KPCB.jget;
      if (!jget) return [];
      const rows = await jget('locations.json').catch(() => []);
      return (rows || []).filter(r => r && r[0] === 'POTA' && r[3] != null).map(r => ({ ref: r[1], name: r[2], lat: +r[3], lon: +r[4] }));
    })();
    return pinsP;
  }
  function ruleCard(name, src, extra) {
    const G = Lgc();
    if (!G) return '';
    const owner = (extra && extra.owner) || src.agency || '';
    const tier = /county|city/i.test(owner) ? 'local' : /private/i.test(owner) ? 'private' : 'state';
    const dir = (G.agencyMatches ? G.agencyMatches(src.place || placeCode(), [name, src.kind, src.agency, src.title].join(' ')) : []).map(a => {
      const one = (label, slot) => (slot && slot.url) ? `<a href="${esc(slot.url)}" target="_blank" rel="noopener">${esc(label)}${slot.verified ? '' : ' (unverified)'}</a>` : '';
      return `<p class="mr-help"><b>${esc(a.name)}</b> · ${[one('home', a.home), one('finder', a.finder), one('GIS', a.gis)].filter(Boolean).join(' · ') || 'no URL stored'}</p>`;
    }).join('');
    const rep = G.rulesCheck({
      publicLand: tier !== 'private',
      owner: owner,
      ownerTier: extra && extra.joint ? 'joint' : tier,
      joint: !!(extra && extra.joint),
      agency: src.agency,
      designation: src.kind || '',
      layer: src.title,
      website: (extra && extra.website) || '',
      boundaryUrl: src.rest || '',
      access: (extra && extra.access) || 'unknown',
      pota: (extra && extra.pota) || []
    });
    const word = { yes: 'Likely qualifies', no: 'Likely does not qualify', maybe: 'Maybe — something is still missing', already: 'Already a POTA park' }[rep.likely];
    return `<div class="mr-miss"><b>${esc(word)}.</b> ${rep.publicLand ? 'Public land' : 'Not shown as public land'} · ${esc(rep.agency || 'agency not named')} · ${esc(rep.layer)}. `
      + (rep.overlap.length ? 'Overlaps ' + rep.overlap.map(p => esc(p.ref + ' ' + p.name)).join('; ') + '. ' : 'No POTA park from this check sits on it. ')
      + (rep.missing.length ? 'Missing: ' + esc(rep.missing.join(', ')) + '. ' : '')
      + (rep.sendLink ? 'Link to send with a POTA note: <a href="' + esc(rep.sendLink) + '" target="_blank" rel="noopener">' + esc(rep.sendLink) + '</a>.' : '')
      + '</div>' + dir;
  }

  async function searchAll() {
    if (busy) return;
    const q = ($('mrDeskQ') && $('mrDeskQ').value || '').trim();
    if (q.length < 2) { out('<p class="mr-msg">Type a place name. Abbreviations such as W.M.A. and SNP are fine.</p>'); return; }
    busy = true;
    const code = placeCode();
    out('<p class="mr-msg">Searching ' + esc(code) + '…</p>');
    try {
      await loadCatalog();
      const G = Lgc();
      const local = [];
      (G ? G.watchHits(q) : []).forEach(h => local.push(h));
      if (window.KPCMapCheck && KPCMapCheck.find) {
        const saved = await KPCMapCheck.find(q, { q: q, code: code === 'CA' ? '' : code, local: code === 'KY', name: code }).catch(() => []);
        (saved || []).forEach(h => { if (!local.some(x => x.name === h.name && x.ref === h.ref)) local.push(h); });
      }
      const words = G ? G.layerWords(q) : [];
      const layers = layersFor(code, false);
      const live = layers.filter(s => s.live);
      const quiet = layers.filter(s => !s.live);
      const got = await pool(live, 4, async src => {
        if (!src.nameField || !words.length) return { src, status: 'skipped', why: src.nameField ? 'need a longer name' : 'no name field on this layer' };
        const where = words.map(w => 'UPPER(' + src.nameField + ") LIKE '%" + w.replace(/'/g, "''").toUpperCase() + "%'").join(' AND ');
        const j = await arcQuery(src, { where: where, returnGeometry: 'false' });
        if (j.skipped) return { src, status: 'skipped', why: j.skipped };
        const feats = (j.features || []).map(f => ({ name: featName(src, f.properties || {}), props: G.publicFields(f.properties || {}, G.isParcel(src)) }))
          .filter(f => G.nameScore(q, f.name) >= 52 || G.fuzzySame(q, f.name));
        return { src, status: feats.length ? 'match' : 'none', feats: feats };
      });
      const matches = got.filter(x => x && x.status === 'match');
      let html = '<section class="mr-res"><div class="mr-head"><div class="mr-k">SEARCH ALL LAYERS</div><h2>' + esc(q) + '</h2><p>' + esc(code) + ' · ' + live.length + ' live layers, ' + quiet.length + ' listed but not queried.</p></div><div class="mr-sec">';
      if (local.length) {
        html += '<h3>Names on this site</h3>' + local.slice(0, 8).map(h => '<p><b>' + esc(h.name) + '</b>' + (h.ref ? ' · ' + esc(h.ref) : '') + (h.url ? ' · <a href="' + esc(h.url) + '" target="_blank" rel="noopener">official page</a>' : '') + '</p>').join('');
      }
      html += '<h3>Which layers matched</h3><ul class="mr-help">';
      got.forEach(row => {
        if (!row || !row.src) return;
        const why = row.status === 'match' ? (row.feats || []).map(f => f.name).slice(0, 4).join(', ') : (row.why || row.error || 'no name in this layer');
        html += '<li><b>' + esc(row.src.title) + '</b> — ' + esc(row.status) + (why ? ': ' + esc(why) : '') + '<br><small>' + esc(row.src.credit || '') + '</small></li>';
      });
      quiet.forEach(s => { html += '<li><b>' + esc(s.title) + '</b> — not queried. ' + esc(s.whyNotLive || 'link only') + (s.download ? ' · <a href="' + esc(s.download) + '" target="_blank" rel="noopener">download</a>' : '') + '</li>'; });
      html += '</ul>';
      if (matches[0] && matches[0].feats[0]) html += ruleCard(matches[0].feats[0].name, matches[0].src, {});
      html += '<p class="mr-help">Official information wins: the agency page and the PAD-US record, then this summary. Outlines drawn from here are view-only.</p></div></section>';
      out(html);
    } catch (e) {
      out('<p class="mr-msg">Search stopped: ' + esc(e.message || e) + '</p>');
    }
    busy = false;
  }

  function envParams(la, lo) {
    const d = 0.12;
    return {
      geometry: [lo - d, la - d, lo + d, la + d].join(','),
      geometryType: 'esriGeometryEnvelope',
      spatialRel: 'esriSpatialRelIntersects',
      where: '1=1'
    };
  }
  async function pinVs() {
    const pin = window.KPCMapCheck && KPCMapCheck.pin && KPCMapCheck.pin();
    if (!pin) { out('<p class="mr-msg">Drop a pin on the map. Pin vs this does not need a name.</p>'); return; }
    if (window.KPCMapCheck && KPCMapCheck.showPoint) KPCMapCheck.showPoint(pin.la, pin.lo);
    if (busy) return;
    busy = true;
    out('<p class="mr-msg">Measuring the pin against official outlines…</p>');
    try {
      await loadCatalog();
      const G = Lgc();
      const code = placeCode();
      const live = layersFor(code, true).filter(s => s.findNew).slice(0, 8);
      const got = await pool(live, 3, async src => {
        const j = await arcQuery(src, envParams(pin.la, pin.lo));
        if (j.skipped || j.error) return { src, error: j.skipped || j.error, rows: [] };
        const rows = [];
        (j.features || []).forEach(f => {
          if (!f.geometry || !G) return;
          const d = G.pinDistance(pin.la, pin.lo, f.geometry);
          if (d.meters == null || d.meters > 8000) return;
          rows.push({ name: featName(src, f.properties || {}), d: d, f: f, credit: src.credit, layer: src.title, parcel: G.isParcel(src), props: f.properties || {} });
        });
        return { src, rows: rows };
      });
      const rows = got.flatMap(x => (x && x.rows) || []).sort((a, b) => a.d.meters - b.d.meters).slice(0, 8);
      showShapes(rows.map(r => ({ f: r.f, name: r.name, credit: r.credit, layer: r.layer, parcel: r.parcel, props: r.props })));
      let html = '<section class="mr-res"><div class="mr-head"><div class="mr-k">PIN VS THIS</div><h2>' + pin.la.toFixed(5) + ', ' + pin.lo.toFixed(5) + '</h2><p>Distance from the pin to the nearest official outline. No name search.</p></div><div class="mr-sec">';
      if (!rows.length) html += '<p>No outline from the live layers for ' + esc(code) + ' came back within about 5 miles. The check above still used the saved state file and PAD-US.</p>';
      rows.forEach(r => {
        html += '<p><b>' + esc(r.name) + '</b> · ' + esc(G.formatDistance(r.d)) + '<br><small>' + esc(r.layer) + ' · ' + esc(r.credit) + '</small></p>';
      });
      html += '</div></section>';
      out(html);
    } catch (e) { out('<p class="mr-msg">' + esc(e.message || e) + '</p>'); }
    busy = false;
  }

  function opts() {
    return {
      closed: !!($('mrFClosed') && $('mrFClosed').checked),
      priv: !!($('mrFPriv') && $('mrFPriv').checked),
      small: !!($('mrFSmall') && $('mrFSmall').checked),
      local: !!($('mrFLocal') && $('mrFLocal').checked),
      hideNamed: !!($('mrFNamed') && $('mrFNamed').checked)
    };
  }
  async function findNew() {
    const pin = window.KPCMapCheck && KPCMapCheck.pin && KPCMapCheck.pin();
    if (!pin) { out('<p class="mr-msg">Drop a pin, then ask for parks you could add near here.</p>'); return; }
    if (busy) return;
    busy = true;
    const code = placeCode();
    out('<p class="mr-msg" id="mrDeskWait">Looking for public land near the pin…</p>');
    try {
      await loadCatalog();
      const waiting = layersFor(code, true).filter(s => s.findNew).slice(0, 8);
      const note0 = $('mrDeskWait');
      if (note0) note0.textContent = 'Looking for public land near the pin… waiting on ' + waiting.length + ' sources.';
      const G = Lgc();
      const allPins = await potaPins();
      const nearPins = allPins.filter(p => Math.abs(p.lat - pin.la) < 0.4 && Math.abs(p.lon - pin.lo) < 0.4);
      const live = layersFor(code, true).filter(s => s.findNew).slice(0, 8);
      let left = live.length;
      const got = await pool(live, 3, async src => {
        const j = await arcQuery(src, envParams(pin.la, pin.lo));
        left -= 1;
        const note = $('mrDeskWait');
        if (note) note.textContent = 'Waiting on ' + left + ' of ' + live.length + ' sources.';
        if (j.skipped || j.error) return { src, err: j.skipped || j.error, rows: [] };
        const rows = [];
        (j.features || []).forEach(f => {
          if (!f.geometry) return;
          const props = f.properties || {};
          const name = featName(src, props);
          const covered = G.alreadyPark(f.geometry, nearPins, 0.25);
          if (covered) return;
          const owner = String(props[src.ownerField] || props.Loc_Own || props.Own_Name || src.agency || '');
          const ownType = String(props.Own_Type || '');
          const priv = /^PVT$/i.test(ownType);
          const local = /^(LOC|DIST)$/i.test(ownType);
          let pinPt = [pin.la, pin.lo];
          try {
            const bb = window.KPCB && KPCB.bbox && KPCB.bbox(f.geometry);
            if (bb) pinPt = [((bb[1] + bb[3]) / 2), ((bb[0] + bb[2]) / 2)];
          } catch (e) {}
          rows.push({
            name: name, agency: src.agency, layer: src.title, credit: src.credit, acres: Math.round(acresOf(src, props)),
            access: accessOf(props), private: priv, local: local, owner: G.scrubOwner(owner, ownType), ownerType: ownType,
            website: webOf(props), boundaryLink: src.rest, pin: pinPt,
            nameMatch: G.fuzzySame(name, (nearPins.find(p => G.fuzzySame(name, p.name)) || {}).name || ''),
            f: f, props: props, parcel: false, src: src
          });
        });
        return { src, rows: rows };
      });
      const raw = got.flatMap(x => (x && x.rows) || []);
      const errs = got.filter(x => x && x.err);
      leads = G.filterCandidates(raw, opts());
      showShapes(leads);
      let html = '<section class="mr-res"><div class="mr-head"><div class="mr-k">PARKS YOU COULD ADD</div><h2>' + leads.length + ' lead' + (leads.length === 1 ? '' : 's') + ' near the pin</h2><p>Public land with no POTA pin inside it or within 0.25 mile. These are leads, not parks.</p></div><div class="mr-sec" id="mrLeadList">';
      html += '<p class="mr-help" id="mrDeskWait">' + raw.length + ' shapes before filters. ' + (raw.length - leads.length) + ' hidden by the filters.</p>';
      errs.forEach(e => { html += '<p class="mr-help">' + esc(e.src.title) + ' did not answer (' + esc(e.err) + ').</p>'; });
      if (!leads.length) html += '<p>Nothing new in this view, or the layers did not answer.</p>';
      leads.slice(0, 40).forEach((c, i) => {
        html += '<div class="mr-hit"><b>' + esc(c.name) + '</b><small>' + esc(c.layer) + ' · ' + (c.acres ? c.acres + ' acres · ' : '') + esc(c.access) + '</small>';
        html += '<p>' + esc(c.owner || c.agency) + (c.nameMatch ? ' Name is close to a park already on the list. Check before you treat it as new.' : '') + '</p>';
        html += '<div class="mr-rl"><button type="button" class="mr-ag" data-pincheck="' + i + '">PIN + CHECK</button></div>';
        html += ruleCard(c.name, c.src, { owner: c.owner, access: c.access, website: c.website });
        html += '<p class="mr-help">' + esc(c.credit) + '</p></div>';
      });
      html += '</div></section>';
      out(html);
      const box = $('mrDeskOut');
      if (box) box.querySelectorAll('[data-pincheck]').forEach(btn => btn.onclick = () => pinCheck(leads[+btn.dataset.pincheck]));
    } catch (e) { out('<p class="mr-msg">' + esc(e.message || e) + '</p>'); }
    busy = false;
  }
  function pinCheck(c) {
    if (!c) return;
    showShapes([c]);
    const b = c.f && c.f.geometry && window.KPCB && KPCB.bbox ? KPCB.bbox(c.f.geometry) : null;
    const la = b ? (b[1] + b[3]) / 2 : (c.pin ? c.pin[0] : null);
    const lo = b ? (b[0] + b[2]) / 2 : (c.pin ? c.pin[1] : null);
    if (la != null && window.KPCMapCheck && KPCMapCheck.showPoint) KPCMapCheck.showPoint(la, lo);
    if ($('mrCheckQ')) $('mrCheckQ').value = c.name;
  }
  function exportLeads() {
    const G = Lgc();
    const rows = G ? G.exportLeads(leads) : [];
    if (!rows.length) { out('<p class="mr-msg">Find leads first. The file is a candidate list, not boundaries.</p>'); return; }
    const blob = new Blob([JSON.stringify({ note: 'Research leads. Not park boundaries.', leads: rows }, null, 1)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'maprep-leads.json';
    a.click();
  }
  async function kyUpdate() {
    await loadCatalog();
    const known = (catalog.kyServices && catalog.kyServices.services) || [];
    const folder = catalog.kyServices && catalog.kyServices.folder;
    if (!folder) { out('<p class="mr-msg">No Kentucky folder is stored.</p>'); return; }
    out('<p class="mr-msg">Asking the Kentucky GIS folder which services it has…</p>');
    try {
      const r = await fetch(folder + '?f=json');
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const j = await r.json();
      const names = (j.services || []).map(s => s.name).filter(Boolean);
      const diff = Lgc().servicesDiff(known, names);
      let html = '<section class="mr-res"><div class="mr-head"><div class="mr-k">KENTUCKY GIS UPDATES</div><h2>' + names.length + ' services in the folder</h2><p>Compared with the ' + known.length + ' services this page already reads. Nothing is added by itself.</p></div><div class="mr-sec">';
      html += '<p><b>New since our list:</b> ' + (diff.added.length ? esc(diff.added.join(', ')) : 'none') + '</p>';
      html += '<p><b>On our list but not in the folder:</b> ' + (diff.missing.length ? esc(diff.missing.join(', ')) : 'none') + '</p>';
      html += '<p class="mr-help">Credit: Kentucky Geography Network, kygisserver.ky.gov. This check reads the folder list only.</p></div></section>';
      out(html);
    } catch (e) { out('<p class="mr-msg">The Kentucky folder did not answer (' + esc(e.message || e) + ').</p>'); }
  }
  async function showTracts() {
    const ref = ($('mrDeskRef') && $('mrDeskRef').value || '').trim().toUpperCase();
    const code = placeCode();
    if (!/^([A-Z]{2})-\d{1,5}$/.test(ref)) { out('<p class="mr-msg">Type a park number such as US-7958, and pick that park’s state.</p>'); return; }
    const path = regionOf(code) === 'CA' ? 'data/ca-key/tracts/CA-' + code + '.json' : 'data/us-key/tracts/US-' + code + '.json';
    out('<p class="mr-msg">Reading tract notes for ' + esc(code) + '…</p>');
    try {
      const get = window.KPCB && KPCB.jget;
      const doc = get ? await get(path).catch(() => null) : await fetch(path).then(r => r.ok ? r.json() : null).catch(() => null);
      if (!doc) { out('<p class="mr-msg">No tract file for ' + esc(code) + ' is on this site yet. The page is ready for it: pieces, parent, and child.</p>'); return; }
      const box = Lgc().tractLinks(doc, ref);
      let html = '<section class="mr-res"><div class="mr-head"><div class="mr-k">TRACTS</div><h2>' + esc(ref) + '</h2><p>Pieces of the official records, and parks inside parks. The answer key itself is unchanged.</p></div><div class="mr-sec">';
      if (!box.tracts.length && !box.parents.length && !box.children.length) html += '<p>This number is not in the ' + esc(code) + ' tract file.</p>';
      box.tracts.forEach(t => {
        html += '<p><b>' + esc(t.name || t.layer || t.src) + '</b><br><small>' + esc(t.src) + ' · ' + esc(t.layer) + (t.sid ? ' · id ' + esc(t.sid) : '') + (t.acres != null ? ' · ' + t.acres + ' acres official' : '') + (t.measured != null ? ' · ' + t.measured + ' acres measured' : '') + ' · pieces ' + esc(t.pieces == null ? 'not split' : t.pieces) + (t.parentId ? ' · parent id ' + esc(t.parentId) : '') + (t.owner ? ' · ' + esc(t.owner) : '') + '</small></p>';
      });
      if (box.parents.length) html += '<p><b>Inside:</b> ' + box.parents.map(p => esc(p.parent + ' (' + p.how + ')')).join(', ') + '</p>';
      if (box.children.length) html += '<p><b>Contains:</b> ' + box.children.map(p => esc(p.child + ' (' + p.how + ')')).join(', ') + '</p>';
      if (box.sameArea.length) html += '<p><b>Same official area:</b> ' + box.sameArea.map(p => esc((p.park === ref ? p.other : p.park) + ' · ' + (p.via || ''))).join('; ') + '</p>';
      html += '</div></section>';
      out(html);
    } catch (e) { out('<p class="mr-msg">' + esc(e.message || e) + '</p>'); }
  }

  function wire() {
    const root = $('mrDesk');
    if (!root || root.dataset.wired) return;
    root.dataset.wired = '1';
    loadCatalog().then(fillPlaces).catch(() => { const el = $('mrDeskOut'); if (el) el.innerHTML = '<p class="mr-msg">The layer catalog did not load.</p>'; });
    const q = $('mrDeskForm');
    if (q) q.addEventListener('submit', e => { e.preventDefault(); searchAll(); });
    const b = (id, fn) => { const el = $(id); if (el) el.onclick = fn; };
    b('mrDeskPin', pinVs);
    b('mrDeskNew', findNew);
    b('mrDeskExport', exportLeads);
    b('mrDeskKy', kyUpdate);
    b('mrDeskTracts', showTracts);
  }
  function mount() { wire(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', wire);
  else wire();
  window.KPCMapDesk = { mount: mount, searchAll: searchAll, pinVs: pinVs, findNew: findNew };
})();
