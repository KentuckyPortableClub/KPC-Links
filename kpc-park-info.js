/* KPC Park & Summit Info Finder (kpc-park-info.html)
   One search box -> only the official info for a POTA park, WWFF reference or SOTA summit anywhere:
   official website, official boundary on a map, and a search of the official site for its maps.
   Sources (all free, no key, readable from a web page):
   - POTA: api.pota.app/lookup?search= (names) and api.pota.app/park/REF (name, pin, type, official website)
   - SOTA: api2.sota.org.uk/api/summits/ASSOC/REGION-NNN
   - WWFF: data/wwff/<PREFIX>.json (weekly copy of the WWFF directory, .github/workflows/kpc-wwff-dir.yml)
   - Official US boundaries: USGS PAD-US (Protected Areas Database), The National Map service
   - Elsewhere / not in PAD-US: OpenStreetMap outline via Overpass (marked unofficial) */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const PADUS = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query';
  const MANG = { NPS: 'National Park Service', USFS: 'U.S. Forest Service', FWS: 'U.S. Fish & Wildlife Service', BLM: 'Bureau of Land Management', USACE: 'U.S. Army Corps of Engineers', TVA: 'Tennessee Valley Authority', BOR: 'Bureau of Reclamation', SPR: 'State parks agency', SDNR: 'State natural resources agency', SFW: 'State fish & wildlife agency', SDOF: 'State forestry agency', CITY: 'City', CNTY: 'County', NGO: 'Nonprofit', PVT: 'Private', SLB: 'State land board', JNT: 'Joint', REG: 'Regional agency', UNK: 'Unknown', DOD: 'Department of Defense', OTHS: 'Other state agency', SDC: 'State department of conservation', SPR2: 'State parks' };
  async function jget(u, opt) { const c = new AbortController(), t = setTimeout(() => c.abort(), 25000); try { const r = await fetch(u, Object.assign({ signal: c.signal }, opt || {})); if (!r.ok) throw new Error('HTTP ' + r.status); return await r.json(); } finally { clearTimeout(t); } }
  const kind = q => { q = q.trim().toUpperCase().replace(/\s+/g, '');
    if (/^[A-Z0-9]{1,4}\/[A-Z0-9]{2}-\d{3}$/.test(q)) return ['sota', q];
    let m = q.match(/^([A-Z0-9]{1,4})-(\d{3,5})$/); if (m) return /FF$/.test(m[1]) ? ['wwff', m[1] + '-' + m[2].padStart(4, '0')] : ['pota', m[1] + '-' + m[2].padStart(4, '0')];
    return ['name', null]; };

  let map = null, layer = null, lastGeo = null;
  function msg(h) { $('piOut').innerHTML = `<div class="pi-msg">${h}</div>`; }
  async function search(q) {
    q = (q || '').trim(); if (!q) return; $('piList').innerHTML = ''; msg('Looking it up…');
    history.replaceState(null, '', '?q=' + encodeURIComponent(q));
    const [k, ref] = kind(q);
    try {
      if (k === 'pota') return showPota(ref);
      if (k === 'sota') return showSota(ref);
      if (k === 'wwff') return showWwff(ref);
      const L = await jget('https://api.pota.app/lookup?search=' + encodeURIComponent(q) + '&size=25');
      const parks = (L || []).filter(x => x.type === 'park');
      if (!parks.length) return msg('No POTA parks match that name. Try fewer words (e.g. <b>Vogel</b>), or type the reference number (US-1234, KFF-1234, W4G/NG-001).');
      if (parks.length === 1) return showPota(parks[0].value);
      $('piOut').innerHTML = '';
      $('piList').innerHTML = `<p class="pi-help">${parks.length} parks match. Pick one:</p>` + parks.map(p => `<button type="button" class="pi-pick" data-ref="${esc(p.value)}"><b>${esc(p.display.replace(/^\S+\s+/, ''))}</b><span>${esc(p.value)} ›</span></button>`).join('');
    } catch (e) { msg('Could not reach the lookup service right now. Check your signal and try again.'); }
  }

  /* ---------- boundaries ---------- */
  const words = n => String(n || '').replace(/\b(state|national|park|parks|forest|wildlife|management|area|recreation|recreational|nature|preserve|refuge|historic|historical|site|reserve|natural|lake|wma|nwr|the|of|and)\b/gi, ' ').replace(/[^A-Za-z0-9' ]/g, ' ').trim().split(/\s+/).filter(w => w.length > 2);
  async function padus(name, la, lo, small) {
    const w = words(name), d = small ? 0.004 : 0.35;
    const env = `${lo - d},${la - d},${lo + d},${la + d}`;
    const base = { geometry: env, geometryType: 'esriGeometryEnvelope', inSR: 4326, spatialRel: 'esriSpatialRelIntersects', outFields: 'Unit_Nm,Loc_Nm,Mang_Name,Loc_Mang,Des_Tp,GIS_Acres,Pub_Access', returnGeometry: true, outSR: 4326, geometryPrecision: 5, maxAllowableOffset: 0.0003, f: 'geojson' };
    if (!small && w.length) base.where = w.slice(0, 2).map(x => `(Unit_Nm LIKE '%${x.replace(/'/g, "''")}%' OR Loc_Nm LIKE '%${x.replace(/'/g, "''")}%')`).join(' AND ');
    else base.where = '1=1';
    const g = await jget(PADUS + '?' + new URLSearchParams(base));
    let fs = (g.features || []).filter(f => f.geometry);
    if (!fs.length) return null;
    if (!small) { // best name match, then the piece the pin is in / nearest
      const nl = String(name).toLowerCase();
      fs.forEach(f => { const u = String(f.properties.Unit_Nm || '').toLowerCase(); f._s = (u.includes(nl) || nl.includes(u) ? 5 : 0) + w.filter(x => u.includes(x.toLowerCase())).length; });
      const top = Math.max(...fs.map(f => f._s)); fs = fs.filter(f => f._s === top);
      const un = fs[0].properties.Unit_Nm; fs = fs.filter(f => f.properties.Unit_Nm === un);
    }
    return { type: 'FeatureCollection', features: fs };
  }
  async function osm(la, lo) {
    const q = `[out:json][timeout:25];is_in(${la},${lo})->.a;(area.a[boundary~"^(protected_area|national_park)$"];area.a[leisure~"^(park|nature_reserve)$"];);out ids tags;`;
    const ep = ['https://overpass-api.de/api/interpreter', 'https://overpass.private.coffee/api/interpreter'];
    let a = null;
    for (const u of ep) { try { a = await jget(u, { method: 'POST', body: 'data=' + encodeURIComponent(q), headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }); break; } catch (e) {} }
    const el = (a && a.elements || []).filter(e => e.tags && e.tags.name); if (!el.length) return null;
    const e = el.sort((x, y) => (x.tags.boundary ? 0 : 1) - (y.tags.boundary ? 0 : 1))[0], id = e.id >= 3600000000 ? ['relation', e.id - 3600000000] : ['way', e.id - 2400000000];
    let g = null;
    for (const u of ep) { try { g = await jget(u, { method: 'POST', body: 'data=' + encodeURIComponent(`[out:json][timeout:40];${id[0]}(${id[1]});out geom;`), headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }); break; } catch (x) {} }
    const o = g && g.elements && g.elements[0]; if (!o) return null;
    const lines = o.type === 'way' ? [o.geometry] : (o.members || []).filter(m => m.type === 'way' && m.role !== 'inner' && m.geometry).map(m => m.geometry);
    return { name: e.tags.name, op: e.tags.operator || '', fc: { type: 'FeatureCollection', features: lines.map(l => ({ type: 'Feature', properties: { name: e.tags.name }, geometry: { type: 'LineString', coordinates: l.map(p => [p.lon, p.lat]) } })) } };
  }

  /* ---------- result card ---------- */
  function domain(u) { try { return new URL(u).hostname.replace(/^www\./, ''); } catch (e) { return ''; } }
  function card(o) {
    const site = o.website, dom = domain(site), g = 'https://www.google.com/search?q=';
    const mapsQ = dom ? g + encodeURIComponent(`site:${dom} ${o.short || o.name} map`) : g + encodeURIComponent(`"${o.name}" ${o.where || ''} official park map`);
    $('piOut').innerHTML = `<section class="pi-res"><div class="pi-head"><div class="pi-ref">${esc(o.ref)} · ${esc(o.prog)}</div><h2>${esc(o.name)}</h2><p>${esc([o.type, o.where].filter(Boolean).join(' · '))}</p></div>
<div class="pi-body"><div class="pi-info">
<div class="pi-sec"><h3>OFFICIAL WEBSITE</h3>${site ? `<div class="pi-btns"><a class="gold" href="${esc(site)}" target="_blank" rel="noopener">${esc(dom || 'OPEN')} ↗</a></div><p>From the ${esc(o.prog)} listing.</p>` : `<p>No official website is listed for this reference. Try the search below.</p>`}</div>
<div class="pi-sec"><h3>BOUNDARY</h3><div class="pi-bnd none" id="piBnd">Looking for the official boundary…</div><div class="pi-btns" style="margin-top:8px" id="piBndBtns"></div></div>
<div class="pi-sec"><h3>THE PARK'S OWN MAPS</h3><div class="pi-btns"><a href="${esc(mapsQ)}" target="_blank" rel="noopener">${dom ? 'SEARCH ' + esc(dom.toUpperCase()) + ' FOR MAPS ↗' : 'SEARCH FOR THE OFFICIAL MAP ↗'}</a></div><p>${dom ? 'Searches only the official site, so you get their trail, campground and boundary maps, not random pages.' : 'No official site listed, so this searches the web for the official map.'}</p></div>
<div class="pi-sec"><h3>MORE</h3><div class="pi-btns">${o.links.map(([t, u]) => `<a class="alt" href="${esc(u)}" target="_blank" rel="noopener">${esc(t)} ↗</a>`).join('')}${isFinite(o.la) ? `<a class="alt" href="https://www.google.com/maps/dir/?api=1&destination=${o.la},${o.lo}" target="_blank" rel="noopener">DIRECTIONS ↗</a>` : ''}</div>${o.note ? `<p>${o.note}</p>` : ''}</div>
<div class="pi-legend"><span><i style="background:#ffb000"></i>Official boundary (PAD-US)</span><span><i style="background:#ff4fd8"></i>OpenStreetMap outline (unofficial)</span><span>📍 ${esc(o.prog)} location</span></div>
</div><div id="piMap" aria-label="Map"></div></div></section>`;
    drawMap(o);
  }
  function drawMap(o) {
    if (map) { map.remove(); map = null; }
    if (!window.L || !isFinite(o.la)) { $('piMap').innerHTML = '<p class="pi-msg">Map unavailable.</p>'; return; }
    map = L.map('piMap', { zoomControl: true }).setView([o.la, o.lo], 13);
    const street = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' });
    const sat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, attribution: 'Imagery © Esri' });
    street.addTo(map); L.control.layers({ Street: street, Satellite: sat }).addTo(map);
    L.marker([o.la, o.lo]).addTo(map).bindPopup(esc(o.ref + ' ' + o.name));
    boundary(o);
  }
  async function boundary(o) {
    const B = $('piBnd'), BB = $('piBndBtns'); lastGeo = null;
    const show = (fc, color, dash, fill) => { if (layer) layer.remove(); layer = L.geoJSON(fc, { style: { color, weight: 3, dashArray: dash, fillOpacity: fill } }).addTo(map); try { map.fitBounds(layer.getBounds(), { padding: [20, 20], maxZoom: 15 }); } catch (e) {} lastGeo = fc; };
    const dl = () => { BB.innerHTML = `<a class="alt" href="#" id="piDl">DOWNLOAD BOUNDARY (GEOJSON)</a>`; $('piDl').onclick = e => { e.preventDefault(); const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(lastGeo)], { type: 'application/geo+json' })); a.download = (o.ref + '-boundary.geojson').replace(/[^\w.-]/g, '_'); a.click(); }; };
    try {
      if (o.us) {
        const fc = await padus(o.prog === 'SOTA' ? '' : (o.short || o.name), o.la, o.lo, o.prog === 'SOTA');
        if (fc && fc.features.length) {
          const p = fc.features[0].properties, names = [...new Set(fc.features.map(f => f.properties.Unit_Nm))];
          show(fc, '#ffb000', null, .12); dl();
          B.className = 'pi-bnd ok';
          B.innerHTML = o.prog === 'SOTA' ? `<b>Public land at this summit:</b> ${names.map(esc).join('; ')}. Official boundary from USGS PAD-US. The SOTA activation zone is the area within 25 m (82 ft) of the summit's height.`
            : `<b>${esc(p.Unit_Nm)}</b> · managed by ${esc(p.Loc_Mang || MANG[p.Mang_Name] || p.Mang_Name || 'unknown')}${p.GIS_Acres ? ' · about ' + Number(p.GIS_Acres).toLocaleString() + ' acres' : ''}. Official boundary from the USGS Protected Areas Database (PAD-US). Check the park's own map for closed areas.`;
          return;
        }
      }
      const os = await osm(o.la, o.lo);
      if (os) { show(os.fc, '#ff4fd8', '8 6', 0); dl(); B.className = 'pi-bnd osm'; B.innerHTML = `<b>${esc(os.name)}</b>${os.op ? ' · ' + esc(os.op) : ''}. Outline from OpenStreetMap: <b>not official</b>, just a guide. Use the park's own map to be sure.`; return; }
      B.className = 'pi-bnd none'; B.innerHTML = 'No boundary found in the official database or OpenStreetMap. The pin shows where ' + esc(o.prog) + ' places it; use the park\'s own map.';
    } catch (e) { B.className = 'pi-bnd none'; B.textContent = 'The boundary service did not answer. Try again in a minute.'; }
  }

  /* ---------- per program ---------- */
  async function showPota(ref) {
    let p; try { p = await jget('https://api.pota.app/park/' + encodeURIComponent(ref)); } catch (e) { return msg('POTA could not be reached. Try again in a minute.'); }
    if (!p || !p.reference) return msg(`No POTA park ${esc(ref)}. Check the number.`);
    const ky = /^US-KY/.test(p.locationDesc || '');
    card({ ref: p.reference, prog: 'POTA', name: p.name + (p.parktypeDesc && !new RegExp(p.parktypeDesc, 'i').test(p.name) ? ' ' + p.parktypeDesc : ''), short: p.name, type: p.parktypeDesc, where: p.locationName || p.locationDesc, la: +p.latitude, lo: +p.longitude, website: p.website, us: /^US-/.test(p.locationDesc || ''),
      links: [['POTA PAGE', 'https://pota.app/#/park/' + p.reference]].concat(ky ? [['KPC PARK NOTES', 'kpc-park-notes.html?ref=' + p.reference], ['KPC PARK COMMANDER', 'finder.html']] : []),
      note: ky ? 'Kentucky park: the KPC Park Commander has its official boundary, entrances, parking and any overlapping parks.' : '' });
  }
  async function showSota(ref) {
    const [a, r] = ref.split('/'); let s;
    try { s = await jget(`https://api2.sota.org.uk/api/summits/${encodeURIComponent(a)}/${encodeURIComponent(r)}`); } catch (e) { return msg('SOTA could not be reached (or no such summit). Check the reference, like W4G/NG-001.'); }
    if (!s || !s.summitCode) return msg('No SOTA summit ' + esc(ref) + '.');
    card({ ref: s.summitCode, prog: 'SOTA', name: s.name, type: `${s.altFt ? s.altFt.toLocaleString() + ' ft' : ''}${s.points != null ? ' · ' + s.points + ' points' : ''}${s.valid === false ? ' · NOT VALID NOW' : ''}`, where: s.associationName + (s.regionName ? ' · ' + s.regionName : ''), la: +s.latitude, lo: +s.longitude, website: '', us: /^USA/.test(s.associationName || ''),
      links: [['SOTA SUMMIT PAGE', 'https://www.sotadata.org.uk/en/summit/' + s.summitCode], ['SOTLAS MAP', 'https://sotlas.org/summits/' + s.summitCode]],
      note: 'Summits have no official website. SOTLAS shows the activation zone, trails and recent activations.' });
  }
  async function showWwff(ref) {
    const pre = ref.split('-')[0]; let rows;
    try { rows = await jget('data/wwff/' + encodeURIComponent(pre) + '.json'); } catch (e) { return msg('No WWFF program ' + esc(pre) + ' in our copy of the WWFF directory.'); }
    const x = rows.find(r => r[0] === ref); if (!x) return msg('No active WWFF reference ' + esc(ref) + '.');
    card({ ref: x[0], prog: 'WWFF', name: x[1], type: 'WWFF reference', where: [x[6], x[5]].filter(Boolean).join(', '), la: x[2], lo: x[3], website: /^https?:\/\//.test(x[4]) ? x[4] : '', us: pre === 'KFF',
      links: [['WWFF SPOTS & AGENDA', 'https://spots.wwff.co/']], note: 'From the WWFF directory (copied weekly). In the US, WWFF (KFF) areas usually match a POTA park; search its name too.' });
  }

  $('piForm').addEventListener('submit', e => { e.preventDefault(); search($('piQ').value); });
  document.querySelector('.pi-ex').addEventListener('click', e => { const b = e.target.closest('[data-q]'); if (b) { $('piQ').value = b.dataset.q; search(b.dataset.q); } });
  $('piList').addEventListener('click', e => { const b = e.target.closest('[data-ref]'); if (b) { $('piList').innerHTML = ''; showPota(b.dataset.ref); } });
  const q0 = new URLSearchParams(location.search).get('q'); if (q0) { $('piQ').value = q0; search(q0); }
})();
