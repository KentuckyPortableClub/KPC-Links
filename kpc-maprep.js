/* KPC Mapping Representative's Tool Box (kpc-maprep.html) — HIDDEN page (noindex, not linked anywhere).
   Type a park name (and optionally a town and/or state). Finds it in USGS PAD-US (the national public-land database),
   checks it against POTA's park-addition rules (docs.pota.app, "Park Additions and Edits"), shows YES / NO / CHECK
   for each rule, the official links, a boundary map, existing POTA parks nearby, and a ready-to-send note for the Map Rep.
   Uses kpc-bounds.js (KPCB) + kpc-map-tools.js. */
(function () {
  'use strict';
  const B = window.KPCB, $ = id => document.getElementById(id), esc = B.esc;
  const PADUS = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query';
  const RULES_URL = 'https://docs.pota.app/docs/volunteer_reference/park_additions_edits.html';
  const F = 'OBJECTID,Unit_Nm,Loc_Nm,Mang_Type,Mang_Name,Loc_Mang,Own_Type,Own_Name,Loc_Own,Des_Tp,Loc_Ds,Pub_Access,GIS_Acres,State_Nm,Category,Date_Est,Comments';
  const TYPE = { FED: 'Federal', STAT: 'State', LOC: 'Local (county / city)', PVT: 'Private', NGO: 'Non-profit', TRIB: 'Tribal', JNT: 'Joint', DIST: 'Special district', UNK: 'Unknown', TERR: 'Territorial' };
  const AG = { NPS: 'National Park Service', USFS: 'U.S. Forest Service', FWS: 'U.S. Fish & Wildlife Service', BLM: 'Bureau of Land Management', USACE: 'U.S. Army Corps of Engineers', TVA: 'Tennessee Valley Authority', BOR: 'Bureau of Reclamation', DOD: 'Department of Defense', SPR: 'State parks agency', SDNR: 'State natural resources agency', SFW: 'State fish & wildlife agency', SDOF: 'State forestry', SDC: 'State conservation department', SLB: 'State land board', OTHS: 'Other state agency', CITY: 'City', CNTY: 'County', REG: 'Regional agency', NGO: 'Non-profit', PVT: 'Private', UNK: 'Unknown' };
  const ACC = { OA: 'Open to the public', RA: 'Restricted (permit, season or partial)', XA: 'Closed to the public', UK: 'Unknown' };
  const DES = { NP: 'National Park', NM: 'National Monument', NF: 'National Forest', NWR: 'National Wildlife Refuge', NRA: 'National Recreation Area', NCA: 'National Conservation Area', NT: 'National Trail', NSBV: 'National Scenic/Byway', WA: 'Wilderness Area', WSR: 'Wild & Scenic River', SP: 'State Park', SW: 'State Wilderness', SRMA: 'State Resource Mgmt Area', SREC: 'State Recreation Area', SCA: 'State Conservation Area', SHCA: 'State Historic/Cultural Area', SOTH: 'State Other', SF: 'State Forest', PREC: 'Local Park', LP: 'Local Park', LREC: 'Local Recreation Area', LCA: 'Local Conservation Area', HCA: 'Historic/Cultural Area', REC: 'Recreation Area', PROC: 'Proclamation boundary', MPA: 'Marine Protected Area', ACC: 'Access Area', PUB: 'Public land', CONE: 'Conservation easement', AGRE: 'Agricultural easement' };
  const ST = 'AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY PR VI GU AS MP'.split(' ');
  let map = null, lay = null, cur = null;
  const q = (o) => B.jget(PADUS + '?' + new URLSearchParams(Object.assign({ outFields: F, returnGeometry: false, f: 'json' }, o))).then(j => { if (j.error) throw new Error(j.error.message); return (j.features || []).map(f => f.attributes); });
  const words = n => String(n || '').replace(/\b(state|national|park|parks|the|of|and|area|wildlife|management|nature|preserve|natural|recreation|recreational|forest|refuge|site)\b/gi, ' ').replace(/[^A-Za-z0-9' ]/g, ' ').trim().split(/\s+/).filter(w => w.length > 2);
  const like = w => `(Unit_Nm LIKE '%${w.replace(/'/g, "''")}%' OR Loc_Nm LIKE '%${w.replace(/'/g, "''")}%')`;
  const msg = h => { $('mrOut').innerHTML = `<div class="mr-msg">${h}</div>`; };

  $('mrState').innerHTML = '<option value="">Any state</option>' + ST.map(s => `<option>${s}</option>`).join('');

  /* ---------- search ---------- */
  async function search() {
    const name = $('mrName').value.trim(), town = $('mrTown').value.trim(), st = $('mrState').value;
    if (name.length < 3) { msg('Type at least part of the park name.'); return; }
    msg('Searching the national public land database…'); $('mrList').innerHTML = '';
    const w = words(name).slice(0, 3); const W = (w.length ? w : [name]).map(like).join(' AND ');
    let rows = [], where = W, box = null;
    try {
      if (town) {
        const g = await B.jget('https://geocoding-api.open-meteo.com/v1/search?count=10&language=en&format=json&countryCode=US&name=' + encodeURIComponent(town)).catch(() => null);
        let hit = (g && g.results || []).find(r => !st || (r.admin1_code || '').toUpperCase() === st || stateOf(r.admin1) === st) || (g && g.results || [])[0];
        if (hit) box = [hit.longitude - 0.7, hit.latitude - 0.6, hit.longitude + 0.7, hit.latitude + 0.6];
      }
      if (st) where += ` AND State_Nm='${st}'`;
      const o = { where, resultRecordCount: 200, orderByFields: 'GIS_Acres DESC' };
      if (box) Object.assign(o, { geometry: box.join(','), geometryType: 'esriGeometryEnvelope', inSR: 4326, spatialRel: 'esriSpatialRelIntersects' });
      rows = await q(o);
    } catch (e) { msg('The public land database did not answer (' + esc(e.message || 'network') + '). Try again in a minute.'); return; }
    if (!rows.length) { msg(`Nothing named like that in the national public land database${st ? ' in ' + st : ''}${town ? ' near ' + esc(town) : ''}. Try fewer words, or check the spelling. If it's brand new or very small it may not be in the database yet: then use the agency's own map.`); return; }
    const G = new Map(); rows.forEach(r => { const k = (r.Unit_Nm || r.Loc_Nm) + '|' + r.State_Nm; const g = G.get(k) || { name: r.Unit_Nm || r.Loc_Nm, st: r.State_Nm, rows: [], acres: 0 }; g.rows.push(r); g.acres += +r.GIS_Acres || 0; G.set(k, g); });
    const L = [...G.values()].sort((a, b) => (B.sameName(b.name, name) - B.sameName(a.name, name)) || b.acres - a.acres);
    if (L.length === 1) return open(L[0]);
    $('mrOut').innerHTML = '';
    $('mrList').innerHTML = `<p class="mr-help">${L.length} matches. Pick one:</p>` + L.slice(0, 40).map((g, i) => `<button type="button" class="mr-pick" data-i="${i}"><b>${esc(g.name)}</b><span>${esc(g.st)} · ${Math.round(g.acres).toLocaleString()} acres · ${esc(g.rows[0].Loc_Mang || AG[g.rows[0].Mang_Name] || '')}</span></button>`).join('');
    $('mrList').onclick = e => { const b = e.target.closest('[data-i]'); if (b) { $('mrList').innerHTML = ''; open(L[+b.dataset.i]); } };
  }
  const SN = { alabama: 'AL', alaska: 'AK', arizona: 'AZ', arkansas: 'AR', california: 'CA', colorado: 'CO', connecticut: 'CT', delaware: 'DE', florida: 'FL', georgia: 'GA', hawaii: 'HI', idaho: 'ID', illinois: 'IL', indiana: 'IN', iowa: 'IA', kansas: 'KS', kentucky: 'KY', louisiana: 'LA', maine: 'ME', maryland: 'MD', massachusetts: 'MA', michigan: 'MI', minnesota: 'MN', mississippi: 'MS', missouri: 'MO', montana: 'MT', nebraska: 'NE', nevada: 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', ohio: 'OH', oklahoma: 'OK', oregon: 'OR', pennsylvania: 'PA', 'rhode island': 'RI', 'south carolina': 'SC', 'south dakota': 'SD', tennessee: 'TN', texas: 'TX', utah: 'UT', vermont: 'VT', virginia: 'VA', washington: 'WA', 'west virginia': 'WV', wisconsin: 'WI', wyoming: 'WY' };
  const stateOf = n => SN[String(n || '').toLowerCase()] || '';

  /* ---------- one park ---------- */
  async function open(g) {
    msg('Loading the boundary and checking POTA…');
    let fc;
    try {
      const where = `Unit_Nm='${g.name.replace(/'/g, "''")}' AND State_Nm='${g.st}'`;
      const big = g.acres > 50000;
      fc = await B.jget(PADUS + '?' + new URLSearchParams({ where, outFields: F, returnGeometry: true, outSR: 4326, geometryPrecision: 5, maxAllowableOffset: big ? 0.0004 : 0.00005, f: 'geojson' }));
    } catch (e) { msg('Could not load the boundary. Try again.'); return; }
    const feats = (fc.features || []).filter(f => f.geometry);
    if (!feats.length) { msg('No boundary shape came back for that one.'); return; }
    const bb = feats.reduce((a, f) => { const b = B.bbox(f.geometry); return [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])]; }, [180, 90, -180, -90]);
    let la = (bb[1] + bb[3]) / 2, lo = (bb[0] + bb[2]) / 2;
    const inAny = feats.some(f => B.inside(la, lo, f.geometry)); if (!inAny) { const r = B.ringsOf(feats[0].geometry)[0][0]; la = r[0][1]; lo = r[0][0]; }
    const R = feats.map(f => f.properties);
    const fee = R.filter(r => r.Category === 'Fee'), base = fee.length ? fee : R;
    const uniq = k => [...new Set(base.map(r => r[k]).filter(Boolean))];
    cur = { g, feats, la, lo, bb, R };
    // POTA: already a park? nearby parks? sub-park of a bigger park run by the same agency?
    const span = Math.max(0.3, Math.min(1.2, Math.max(bb[2] - bb[0], bb[3] - bb[1])));
    const [near, look, around] = await Promise.all([
      B.potaNear(la, lo, span).catch(() => []),
      B.jget('https://api.pota.app/lookup?search=' + encodeURIComponent(words(g.name).join(' ') || g.name) + '&size=60').catch(() => []),
      q({ geometry: `${lo},${la}`, geometryType: 'esriGeometryPoint', inSR: 4326, spatialRel: 'esriSpatialRelIntersects', where: '1=1' }).catch(() => [])
    ]);
    const inside = near.filter(p => feats.some(f => B.inside(p.la, p.lo, f.geometry)));
    const named = near.filter(p => B.sameName(p.name, g.name)).concat(((look || []).filter(x => x.type === 'park' && B.sameName(x.display.replace(/^\S+\s+/, ''), g.name)).map(x => ({ ref: x.value, name: x.display.replace(/^\S+\s+/, ''), far: true }))));
    const already = [...new Map(named.concat(inside.filter(p => B.sameName(p.name, g.name))).map(p => [p.ref, p])).values()].filter(p => !p.far || /^US-/.test(p.ref));
    const parents = (around || []).filter(r => (r.Unit_Nm || '') !== g.name && (+r.GIS_Acres || 0) > g.acres * 1.5 && r.Category !== 'Easement');
    const parentPota = parents.map(p => ({ p, pota: near.find(x => B.sameName(x.name, p.Unit_Nm)) })).filter(x => x.pota);
    const sameAgency = parentPota.filter(x => x.p.Mang_Name === base[0].Mang_Name && (x.p.Loc_Mang || '') === (base[0].Loc_Mang || ''));
    // ---------- the rules ----------
    const own = uniq('Own_Type'), mng = uniq('Mang_Type'), mngN = uniq('Mang_Name'), locM = uniq('Loc_Mang').join('; '), acc = uniq('Pub_Access'), des = uniq('Des_Tp');
    const top = t => t === 'FED' || t === 'STAT';
    const res = [];
    const add = (v, title, why) => res.push({ v, title, why });
    add(own.every(top) ? 'YES' : own.some(t => t === 'JNT' || t === 'UNK') && !own.some(t => ['LOC', 'PVT', 'NGO', 'TRIB', 'DIST'].includes(t)) ? 'CHECK' : 'NO', 'Owned by the national or state government',
      `Owner: ${base.map(r => (r.Loc_Own || AG[r.Own_Name] || r.Own_Name) + ' (' + (TYPE[r.Own_Type] || r.Own_Type) + ')').filter((x, i, a) => a.indexOf(x) === i).join('; ')}. POTA rule: "All new parks must be owned and operated by the two highest tiers of government" (in the US: federal and state). County, city, private and non-profit land is not added.`);
    add(mng.every(top) && !mngN.includes('USACE') && !mngN.includes('TVA') && !/universit|college/i.test(locM) ? 'YES' : mngN.includes('TVA') || /universit|college/i.test(locM) || mng.some(t => t === 'JNT' || t === 'UNK') ? 'CHECK' : 'NO', 'Run (operated) by the national or state government',
      `Manager: ${esc(locM || mngN.map(m => AG[m] || m).join('; '))} (${mng.map(t => TYPE[t] || t).join(', ')}). ${mngN.includes('USACE') ? 'Run by the Army Corps of Engineers: POTA does not add Corps sites except a very few already confirmed. ' : ''}${mngN.includes('TVA') ? 'TVA land is researched case by case. ' : ''}${/universit|college/i.test(locM) ? 'University land is rarely eligible. ' : ''}${own.includes('FED') && mng.includes('STAT') ? 'Federal land run by a state agency counts as both top tiers (several Kentucky WMAs on Corps land run by Fish & Wildlife are already POTA parks). ' : ''}Parks run by commissions, districts, boards, societies or third parties don't qualify.`);
    add(acc.includes('OA') ? 'YES' : acc.includes('XA') ? 'NO' : 'CHECK', 'Open to the public',
      `Database says: ${acc.map(a => ACC[a] || a).join('; ')}. POTA: "If the National or State agency says that a park is open to the public, then it is eligible." Hard access (hike-in, boat-in) is fine. Confirm on the agency's page.`);
    const exName = /national (historic|recreation(al)?) trail|heritage area|historic landmark|historic place|national register|scenic byway/i.test(g.name);
    const exDes = des.some(d => ['CONE', 'AGRE', 'RECE', 'HCAE', 'OTHE'].includes(d)) || R.every(r => r.Category === 'Easement');
    add(exName || exDes || own.includes('TRIB') || mng.includes('TRIB') || mng.includes('DIST') ? 'NO' : 'YES', 'Not a type POTA won\'t add',
      exName ? 'The name looks like a type POTA excludes (National Recreation Trail, Heritage Area, Historic Place/Landmark, byway).' : exDes ? 'This is an easement (usually private land with a conservation agreement), not a park.' : own.includes('TRIB') || mng.includes('TRIB') ? 'Tribal land is treated as private unless the tribal council says otherwise.' : mng.includes('DIST') ? 'Run by a special district or commission.' : 'Not a Corps site, heritage area, National Recreation Trail, historic landmark, tribal land, commission/district site or commercial trail.');
    add(sameAgency.length ? 'NO' : parentPota.length ? 'YES' : 'YES', 'Not a "sub-park" inside an existing POTA park of the same agency',
      sameAgency.length ? `It sits inside ${sameAgency.map(x => esc(x.p.Unit_Nm) + ' (' + esc(x.pota.ref) + ')').join(', ')}, run by the same agency. POTA: "does not create sub-parks within existing parks if both parks are part of the same government tier or agency."` : parentPota.length ? `It's inside ${parentPota.map(x => esc(x.p.Unit_Nm) + ' (' + esc(x.pota.ref) + ')').join(', ')}, but that is run by a different agency, so it can be its own park (and a 2-fer).` : 'No bigger POTA park run by the same agency surrounds it.');
    add(already.length ? 'NO' : 'YES', 'Not already in POTA',
      already.length ? 'Looks like it is already a POTA park: ' + already.map(p => `<a href="https://pota.app/#/park/${encodeURIComponent(p.ref)}" target="_blank" rel="noopener">${esc(p.ref)} ${esc(p.name)}</a>`).join(', ') + '. No need to request it.' : `No POTA park with this name nearby.${inside.length ? ' (POTA parks with pins inside this boundary: ' + inside.map(p => esc(p.ref + ' ' + p.name)).join(', ') + ' — make sure it isn\'t the same place under another name.)' : ''}`);
    const lakeOnly = /\blake\b|\breservoir\b|\bpond\b/i.test(g.name) && g.acres < 1500;
    add(lakeOnly ? 'CHECK' : 'CHECK', lakeOnly ? 'Not an agency lake surrounded by city, county or private land' : 'Not surrounded by private property',
      lakeOnly ? 'POTA does NOT add agency-owned lakes that are surrounded by city, county or private land. Look at the map: is there state/federal land around the water (shoreline, ramp area) that the public can reach, or is the shore someone else\'s?' : 'Since 2022 POTA deactivates parks surrounded by private property. Check the map for a public road, trail or water route into the land.');
    add('CHECK', 'Has an official government web page with a boundary map',
      `POTA needs the agency's own page (and its boundary map) for the park's POTA listing. If there's no web page, a civil-agency or GIS map can be used. Tourist or commercial sites don't count. Agency: <b>${esc(locM || '')}</b>. Use the search buttons below and paste the official link into your request.`);
    add('INFO', 'Size', `About ${Math.round(g.acres).toLocaleString()} acres. POTA has no size rule, but very small parks may wait if activating would get in the way of the park's main use.`);
    const nNo = res.filter(r => r.v === 'NO').length, nCk = res.filter(r => r.v === 'CHECK').length;
    const verdict = already.length ? ['no', 'ALREADY A POTA PARK'] : nNo ? ['no', 'LIKELY NOT ELIGIBLE'] : nCk ? ['maybe', 'LOOKS POSSIBLE: CONFIRM THE YELLOW ITEMS'] : ['yes', 'LOOKS ELIGIBLE'];
    const gq = s => 'https://www.google.com/search?q=' + encodeURIComponent(s);
    const nm = g.name, stn = g.st;
    const note = [`Park request: ${nm} (${stn})`, '', `Owner: ${base.map(r => r.Loc_Own || AG[r.Own_Name] || r.Own_Name).filter((x, i, a) => a.indexOf(x) === i).join('; ')}`, `Managed by: ${locM}`, `Designation: ${base.map(r => r.Loc_Ds || DES[r.Des_Tp] || r.Des_Tp).filter((x, i, a) => a.indexOf(x) === i).join('; ')}`, `Public access: ${acc.map(a => ACC[a] || a).join('; ')}`, `Size: about ${Math.round(g.acres).toLocaleString()} acres`, `Location: ${la.toFixed(5)}, ${lo.toFixed(5)}`, 'Official web page: (paste the agency link here)', 'Official boundary map: (paste the agency map link here)', `GIS boundary: USGS PAD-US (Unit_Nm "${nm}", ${stn})`, '', 'Rule check (KPC Mapping Rep Tool Box):'].concat(res.filter(r => r.v !== 'INFO').map(r => `- ${r.title}: ${r.v}`)).join('\n');
    $('mrOut').innerHTML = `<section class="mr-res">
<div class="mr-head"><div class="mr-k">${esc(stn)} · PAD-US</div><h2>${esc(nm)}</h2><p>${esc([locM, Math.round(g.acres).toLocaleString() + ' acres', base.map(r => r.Loc_Ds || DES[r.Des_Tp] || '').filter(Boolean).filter((x, i, a) => a.indexOf(x) === i).join(' / ')].filter(Boolean).join(' · '))}</p></div>
<div class="mr-v ${verdict[0]}"><b>${verdict[1]}</b><span>${res.filter(r => r.v === 'YES').length} yes · ${nNo} no · ${nCk} to check yourself</span></div>
<div class="mr-rules">${res.map(r => `<div class="mr-r ${r.v.toLowerCase()}"><i>${r.v === 'INFO' ? 'INFO' : r.v}</i><div><b>${esc(r.title)}</b><p>${r.why}</p></div></div>`).join('')}</div>
<div class="mr-sec"><h3>OFFICIAL WEBSITE &amp; MAP</h3><div class="mr-btns"><a class="gold" href="${gq(`"${nm}" ${stn} site:.gov`)}" target="_blank" rel="noopener">FIND THE OFFICIAL .GOV PAGE ↗</a><a href="${gq(`"${nm}" ${locM} boundary map`)}" target="_blank" rel="noopener">FIND THE AGENCY BOUNDARY MAP ↗</a><a href="${gq(`"${nm}" ${stn} ${locM}`)}" target="_blank" rel="noopener">SEARCH THE AGENCY ↗</a></div><p class="mr-help">These search only for the park by name with its agency. Use the agency's own page, not tourist sites.</p></div>
<div class="mr-sec"><h3>BOUNDARY MAP (USGS PAD-US)</h3><div id="mrMap"></div><p class="mr-help">Gold = this park's land in PAD-US. Blue pins = POTA parks nearby (tap for the number). Tap the map to drop a pin; ⛶ FULL for full screen; layers for satellite, topo and terrain.</p><div class="mr-btns" id="mrFiles"></div></div>
<div class="mr-sec"><h3>NOTE FOR YOUR MAP REP</h3><textarea id="mrNote" rows="13">${esc(note)}</textarea><div class="mr-btns"><a class="gold" href="#" id="mrCopy">COPY THE NOTE</a><a href="${RULES_URL}" target="_blank" rel="noopener">POTA PARK-ADDITION RULES ↗</a></div><p class="mr-help">Send park requests to the Mapping Representative for the state (see the POTA rules page for the Map Rep list; email them from their QRZ page). POTA adds parks at the Map Rep's discretion.</p></div>
</section>`;
    $('mrCopy').onclick = e => { e.preventDefault(); const t = $('mrNote').value; (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(() => e.target.textContent = 'COPIED ✓').catch(() => { $('mrNote').select(); document.execCommand('copy'); e.target.textContent = 'COPIED ✓'; }); };
    draw(feats, near, la, lo);
    window.scrollTo({ top: $('mrOut').offsetTop - 70, behavior: 'smooth' });
  }
  function draw(feats, near, la, lo) {
    if (map) { map.remove(); map = null; }
    map = L.map('mrMap').setView([la, lo], 12);
    if (window.KPCLayers) KPCLayers(map); else L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(map);
    if (window.KPCPin) KPCPin(map); if (window.KPCLocate) KPCLocate(map); if (window.KPCFull) KPCFull(map);
    const fc = { type: 'FeatureCollection', features: feats.map(f => ({ type: 'Feature', properties: { Unit_Nm: f.properties.Unit_Nm }, geometry: f.geometry })) };
    lay = L.geoJSON(fc, { style: f => ({ color: '#ffb000', weight: 3, fillColor: '#ffb000', fillOpacity: .15 }) }).addTo(map);
    try { map.fitBounds(lay.getBounds(), { padding: [16, 16] }); } catch (e) {}
    near.forEach(p => L.circleMarker([p.la, p.lo], { radius: 7, color: '#fff', weight: 2, fillColor: '#1378ff', fillOpacity: 1 }).addTo(map).bindPopup(`<b>${esc(p.ref)}</b> ${esc(p.name)}<br><a href="https://pota.app/#/park/${encodeURIComponent(p.ref)}" target="_blank" rel="noopener">POTA page ↗</a>`));
    const o = { ref: cur.g.name.replace(/\s+/g, '_').slice(0, 40), name: cur.g.name, la, lo };
    $('mrFiles').innerHTML = `<a class="alt" href="#" data-f="kml">SAVE KML · GOOGLE EARTH</a><a class="alt" href="#" data-f="gpx">GPX · GPS UNITS</a><a class="alt" href="#" data-f="geojson">GEOJSON</a>`;
    $('mrFiles').querySelectorAll('[data-f]').forEach(b => b.onclick = e => { e.preventDefault(); B.saveGeo(fc, b.dataset.f, o, b); });
  }
  $('mrForm').addEventListener('submit', e => { e.preventDefault(); search(); });
  const P = new URLSearchParams(location.search);
  if (P.get('name')) { $('mrName').value = P.get('name'); if (P.get('town')) $('mrTown').value = P.get('town'); if (P.get('state')) $('mrState').value = P.get('state').toUpperCase(); search(); }
})();
