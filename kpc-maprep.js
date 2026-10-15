/* KPC Mapping Representative's Tool Box (kpc-maprep.html) — HIDDEN page (noindex, not linked anywhere).
   Type a park name (and optionally a town and/or state). Finds it in USGS PAD-US (the national public-land database),
   checks it against POTA's park-addition rules (docs.pota.app, "Park Additions and Edits"), shows YES / NO / CHECK
   for each rule, the official links, a boundary map, existing POTA parks nearby, and a copyable park summary (for POTA Mapping Representatives).
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
  let map = null, lay = null, cur = null, lastQ = '';
  const q = (o) => B.jget(PADUS + '?' + new URLSearchParams(Object.assign({ outFields: F, returnGeometry: false, f: 'json' }, o))).then(j => { if (j.error) throw new Error(j.error.message); return (j.features || []).map(f => f.attributes); });
  const words = n => String(n || '').replace(/\b(state|national|park|parks|the|of|and|area|wildlife|management|nature|preserve|natural|recreation|recreational|forest|refuge|site)\b/gi, ' ').replace(/[^A-Za-z0-9' ]/g, ' ').trim().split(/\s+/).filter(w => w.length > 2).map(w => w.length > 4 && /[^s]s$/i.test(w) ? w.slice(0, -1) : w);
  /* The PAD-US server's firewall refuses (403) any where with UPPER(), OR, IN (...), a second LIKE, or anything after a LIKE.
     Safe shape: State_Nm='XX' AND <field> LIKE '%word%word%'. LIKE is case-sensitive, so ask in Title Case (Unit_Nm),
     CAPITALS (Loc_Nm) and as typed, all at once, and merge. Agency picks are filtered here, not in the query. */
  const tc = w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase();
  const pat = (ws, f) => ('%' + ws.map(f).join('%') + '%').replace(/'/g, '%');
  const nameWheres = (ws, pre) => { const seen = new Set(), out = []; [['Unit_Nm', tc], ['Loc_Nm', w => w.toUpperCase()], ['Unit_Nm', w => w]].forEach(([fl, f]) => { const w = `${pre}${fl} LIKE '${pat(ws, f)}'`; if (!seen.has(w)) { seen.add(w); out.push(w); } }); return out; };
  const qName = (ws, st, o) => Promise.all(nameWheres(ws, `State_Nm='${st}' AND `).map(w => q(Object.assign({}, o, { where: w })).catch(() => []))).then(L => { const m = new Map(); L.flat().forEach(r => m.set(r.OBJECTID, r)); return [...m.values()].sort((a, b) => (+b.GIS_Acres || 0) - (+a.GIS_Acres || 0)); });
  let tick = null;
  /* messages; a text ending in … gets a spinning compass and a seconds counter so people can see it's still working */
  const msg = h => {
    clearInterval(tick);
    const busy = /…$/.test(h.replace(/<[^>]+>/g, '').trim());
    $('mrOut').innerHTML = `<div class="mr-msg${busy ? ' busy' : ''}">${busy ? '<span class="mr-spin" aria-hidden="true">🧭</span>' : ''}<div>${h}${busy ? '<small class="mr-sec-n">Still searching… 0 s</small>' : ''}</div></div>`;
    if (busy) { const t0 = Date.now(); tick = setInterval(() => { const e = document.querySelector('.mr-sec-n'); if (!e) { clearInterval(tick); return; } e.textContent = 'Still searching… ' + Math.round((Date.now() - t0) / 1000) + ' s'; }, 1000); }
  };

  $('mrState').innerHTML = '<option value="">Pick a state (required)</option>' + ST.map(s => `<option>${s}</option>`).join('');
  try { const v = localStorage.getItem('kpcMrState'); if (v) $('mrState').value = v; } catch (e) {}
  const NPSQ = 'https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/2/query';
  const FWSQ = 'https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSInterest_Simplified_Authoritative/FeatureServer/0/query';
  const OVER = ['https://overpass-api.de/api/interpreter', 'https://overpass.private.coffee/api/interpreter'];
  let STB = null; const stBox = async st => { if (!STB) STB = await B.jget('kpc-us-states.json').catch(() => []); const x = (STB || []).find(b => b.a === st); if (!x) return null; let a = [180, 90, -180, -90]; x.p.forEach(pl => pl[0].forEach(([X, Y]) => { a = [Math.min(a[0], X), Math.min(a[1], Y), Math.max(a[2], X), Math.max(a[3], Y)]; })); return a; };

  /* ---------- the agencies we search, per state (from PAD-US itself) ---------- */
  let AGL = [], agPick = new Set();
  const agKey = a => a.t + '|' + a.code + '|' + a.loc;
  async function agencies(st) {
    const box = $('mrAg'); AGL = []; agPick = new Set();
    if (!st) { box.innerHTML = ''; return; }
    try { localStorage.setItem('kpcMrState', st); } catch (e) {}
    box.innerHTML = '<p class="mr-help">Loading the federal and state agencies that own land in ' + esc(st) + '…</p>';
    try {
      const agq = () => B.jget(PADUS + '?' + new URLSearchParams({ where: `State_Nm='${st}'`, outFields: 'Mang_Type,Mang_Name,Loc_Mang,Category', returnDistinctValues: true, returnGeometry: false, f: 'json' }), null, 45000);
      let j; try { j = await agq(); } catch (e) { box.innerHTML = '<p class="mr-help">The national database is slow, trying again…</p>'; j = await agq(); }
      const m = new Map();
      (j.features || []).filter(f => /^(FED|STAT)$/.test(f.attributes.Mang_Type) && f.attributes.Category !== 'Easement').forEach(f => { const a = f.attributes, loc = (a.Loc_Mang && !/^unknown$/i.test(a.Loc_Mang)) ? a.Loc_Mang : (AG[a.Mang_Name] || a.Mang_Name); const k = a.Mang_Type + '|' + a.Mang_Name + '|' + loc.toLowerCase(); const o = m.get(k) || { t: a.Mang_Type, code: a.Mang_Name, loc, n: 0 }; o.n += 1; m.set(k, o); });
      AGL = [...m.values()].sort((a, b) => (a.t > b.t ? 1 : a.t < b.t ? -1 : 0) || b.n - a.n);
    } catch (e) { box.innerHTML = '<p class="mr-help">Could not load the agency list right now.</p>'; return; }
    drawAg(st);
  }
  function drawAg(st) {
    const grp = t => AGL.filter(a => a.t === t);
    const chip = a => `<button type="button" class="mr-ag${agPick.has(agKey(a)) ? ' on' : ''}" data-k="${esc(agKey(a))}">${esc(a.loc)}${a.loc !== (AG[a.code] || a.code) && AG[a.code] ? ' <small>' + esc(AG[a.code]) + '</small>' : ''}</button>`;
    $('mrAg').innerHTML = `<details class="mr-agd"${AGL.length && agPick.size ? ' open' : ''}><summary>AGENCIES SEARCHED IN ${esc(st)}: ${grp('FED').length} FEDERAL · ${grp('STAT').length} STATE ${agPick.size ? '· ONLY ' + agPick.size + ' PICKED' : '· ALL'} (TAP TO SEE)</summary>
<p class="mr-help">Every search looks through all of these (from the national public land database), plus the live National Park Service and U.S. Fish &amp; Wildlife Service maps${st === 'KY' ? ', Kentucky\'s own state boundary files' : ''} and, as a backup, OpenStreetMap. Tap agencies to search only those; tap again to undo.</p>
<h4>FEDERAL</h4><div class="mr-ags">${grp('FED').map(chip).join('') || '<span class="mr-help">none listed</span>'}</div><h4>STATE</h4><div class="mr-ags">${grp('STAT').map(chip).join('') || '<span class="mr-help">none listed</span>'}</div></details>`;
    $('mrAg').querySelectorAll('.mr-ag').forEach(b => b.onclick = () => { const k = b.dataset.k; if (agPick.has(k)) agPick.delete(k); else agPick.add(k); drawAg(st); });
  }
  $('mrState').addEventListener('change', e => agencies(e.target.value));

  /* ---------- extra official sources + OpenStreetMap backup, made to look like PAD-US rows ---------- */
  const acresOf = g => { let a = 0; B.ringsOf(g).forEach(poly => poly.forEach((r, n) => { let s2 = 0; for (let i = 0, k = r.length - 1; i < r.length; k = i++) s2 += (r[k][0] + r[i][0]) * (r[k][1] - r[i][1]); const lat = r[0][1] * Math.PI / 180; const m2 = Math.abs(s2 / 2) * 111320 * 111320 * Math.cos(lat); a += n ? -m2 : m2; })); return a / 4046.86; };
  const fake = (f, P) => ({ type: 'Feature', geometry: f.geometry, properties: Object.assign({ Pub_Access: 'UK', Category: 'Fee', Des_Tp: '', Own_Name: '', Mang_Name: '' }, P, { GIS_Acres: P.GIS_Acres || acresOf(f.geometry) }) });
  async function extra(name, st) {
    const w = words(name).slice(0, 3), ws = w.length ? w : [name], box = await stBox(st), out = [];
    const sq = x => x.replace(/'/g, "''");
    const jobs = [
      B.jget(NPSQ + '?' + new URLSearchParams({ where: `STATE='${st}' AND ` + ws.map(x => `UPPER(UNIT_NAME) LIKE '%${sq(x.toUpperCase())}%'`).join(' AND '), outFields: 'UNIT_NAME,UNIT_TYPE,UNIT_CODE', returnGeometry: true, outSR: 4326, geometryPrecision: 5, maxAllowableOffset: 0.0001, f: 'geojson' })).then(j => (j.features || []).forEach(f => out.push({ src: 'National Park Service boundary (live)', f: fake(f, { Unit_Nm: f.properties.UNIT_NAME, Own_Type: 'FED', Own_Name: 'NPS', Loc_Own: 'National Park Service', Mang_Type: 'FED', Mang_Name: 'NPS', Loc_Mang: 'National Park Service', Loc_Ds: f.properties.UNIT_TYPE, State_Nm: st, Web: f.properties.UNIT_CODE ? 'https://www.nps.gov/' + String(f.properties.UNIT_CODE).toLowerCase() + '/' : '' }) }))).catch(() => {}),
      box ? B.jget(FWSQ + '?' + new URLSearchParams({ where: ws.map(x => `ORGNAME LIKE '%${sq(x.toUpperCase())}%'`).join(' AND '), geometry: box.join(','), geometryType: 'esriGeometryEnvelope', inSR: 4326, spatialRel: 'esriSpatialRelIntersects', outFields: 'ORGNAME,RSL_TYPE,INTTYPE1,SUM_GISACRES', returnGeometry: true, outSR: 4326, geometryPrecision: 5, maxAllowableOffset: 0.0001, f: 'geojson' })).then(j => (j.features || []).forEach(f => { const p = f.properties; out.push({ src: 'U.S. Fish & Wildlife Service land (live)', f: fake(f, { Unit_Nm: p.ORGNAME.replace(/\b\w+/g, t => t[0] + t.slice(1).toLowerCase()), Own_Type: 'FED', Own_Name: 'FWS', Loc_Own: 'U.S. Fish & Wildlife Service', Mang_Type: 'FED', Mang_Name: 'FWS', Loc_Mang: 'U.S. Fish & Wildlife Service', Loc_Ds: p.RSL_TYPE, GIS_Acres: p.SUM_GISACRES, Category: p.INTTYPE1 === 'E' ? 'Easement' : 'Fee', State_Nm: st }) }); })).catch(() => {}) : null,
      st === 'KY' ? B.ky().then(F => F.filter(f => B.sameName(f._nm, name) || ws.every(x => f._nm.toLowerCase().includes(x.toLowerCase()))).forEach(f => { const fed = /bnps|bdbnf|bwilder|bfws/.test(f._L.k), kpc = f._L.kpc; out.push({ src: kpc ? 'KPC-drawn outline (approximate)' : 'Kentucky state boundary file (' + f._L.agency + ')', f: fake({ geometry: f.geometry }, { Unit_Nm: f._nm, Own_Type: kpc ? 'UNK' : fed ? 'FED' : 'STAT', Loc_Own: f._L.agency, Mang_Type: kpc ? 'UNK' : fed ? 'FED' : 'STAT', Loc_Mang: f._L.agency, Loc_Ds: (f.properties || {}).TYPE || f._L.name, Pub_Access: /restricted/i.test((f.properties || {}).ACCESS || '') ? 'RA' : /open/i.test((f.properties || {}).ACCESS || '') || /^b(wma|state)$/.test(f._L.k) ? 'OA' : 'UK', State_Nm: 'KY', Web: (f.properties || {}).URL || '' }) }); })).catch(() => {}) : null,
      st === 'KY' ? kyLive(ws).then(L => L.forEach(x => out.push(x))) : null,
      osmFind(ws, st).then(L => L.forEach(x => out.push(x))).catch(() => {})
    ].filter(Boolean);
    await Promise.all(jobs);
    if (st === 'KY') await wmaOwners(out);
    return out;
  }
  /* the agency's own web site, to search for the park's page */
  const agSites = (s, st) => { const o = []; if (/nature preserve/i.test(s)) o.push(st === 'KY' ? 'eec.ky.gov' : ''); if (/fish (&|and) wildlife|kdfwr/i.test(s) && st === 'KY') o.push('fw.ky.gov'); if (/state parks|department of parks/i.test(s) && st === 'KY') o.push('parks.ky.gov'); if (/forestry/i.test(s) && st === 'KY') o.push('eec.ky.gov'); if (/national park service|\bNPS\b/.test(s)) o.push('nps.gov'); if (/fish (&|and) wildlife service|\bFWS\b/.test(s)) o.push('fws.gov'); if (/forest service|USFS/.test(s)) o.push('fs.usda.gov'); return [...new Set(o.filter(Boolean))]; };
  /* Kentucky WMAs: the state map's MANAGER field is the manager, NOT the owner. The real owner is the 'Owned by ...' /
     'privately owned' line on each WMA's Fish & Wildlife page, read weekly into data/ky-wma-owners.json (kpc-new-lands.yml). */
  let WMAO = null;
  const OT = { State: ['STAT', 'Kentucky Fish & Wildlife / state'], Private: ['PVT', 'Private owner'], Corps: ['FED', 'U.S. Army Corps of Engineers', 'USACE'], University: ['UNK', 'University'], Local: ['LOC', 'County / city'], Federal: ['FED', 'Federal agency'] };
  async function wmaOwners(list, onlyKnown) {
    if (!WMAO) WMAO = await B.jget('data/ky-wma-owners.json?v=' + Math.floor(Date.now() / 864e5), null, 15000).then(j => j.wmas || {}).catch(() => ({}));
    list.forEach(x => {
      if (!/Fish & Wildlife/.test(x.src) && !onlyKnown) return;
      const P = x.f.properties, n = P.Unit_Nm;
      const k = Object.keys(WMAO).find(o => B.norm(o) === B.norm(n) && B.sameKind(o, n)) || Object.keys(WMAO).find(o => B.sameName(o, n) && B.sameKind(o, n));
      const o = k && WMAO[k];
      if (o && o.type && OT[o.type]) { const [ty, lab, code] = OT[o.type]; P.Own_Type = ty; P.Loc_Own = lab; if (code) P.Own_Name = code; }
      else if (!onlyKnown) { P.Own_Type = 'UNK'; P.Loc_Own = 'Not stated: check the owner line on the Fish & Wildlife page'; }
      if (o && o.says) P.Says = o.says;
      if (o && o.url && !P.Web) P.Web = o.url;
    });
  }
  /* Kentucky's own live GIS layers (each has its own field names) */
  const KYL = [
    { svc: 'Ky_Public_Hunting_Areas_WGS84WM', id: 1, ag: 'Kentucky Fish & Wildlife', nm: 'AREANAME', web: p => p.DETAIL || (p.KDFWR_ID ? 'https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=' + p.KDFWR_ID : ''), acc: p => /^no/i.test(p.AreaOpen || '') ? 'RA' : 'OA', ds: p => p.WMA === 'Yes' ? 'Wildlife Management Area' : 'Public hunting area' },
    { svc: 'Ky_State_Parks_Features_WGS84WM', id: 8, ag: 'Kentucky State Parks', nm: 'PUBLIC_NAM', full: p => p.PUBLIC_NAM + (/park|site/i.test(p.PUBLIC_NAM) ? '' : /\/historic\//.test(p.HYPERLINK || '') ? ' State Historic Site' : /\/resort\//.test(p.HYPERLINK || '') ? ' State Resort Park' : ' State Park'), web: p => p.HYPERLINK || '', acc: () => 'OA', ds: p => /\/historic\//.test(p.HYPERLINK || '') ? 'State Historic Site' : 'State Park' },
    { svc: 'Ky_KNP_State_Nature_Preserves_WGS84WM', id: 0, ag: 'Office of Kentucky Nature Preserves', nm: 'MANAME', web: p => p.Webpage || '', acc: p => /open/i.test(p.PUB_ACCESS || '') ? 'OA' : p.PUB_ACCESS ? 'RA' : 'UK', ds: p => p.UNIT_TYPE || 'State Nature Preserve', own: p => p.MA_OWNER, mng: p => p.MNG_INST },
    { svc: 'Ky_KNP_Natural_Areas_WGS84WM', id: 0, ag: 'Office of Kentucky Nature Preserves', nm: 'MANAME', web: p => p.Webpage || '', acc: p => /open/i.test(p.PUB_ACCESS || '') ? 'OA' : p.PUB_ACCESS ? 'RA' : 'UK', ds: p => p.UNIT_TYPE || 'State Natural Area', own: p => p.MA_OWNER, mng: p => p.MNG_INST }];
  const kyType = s => /county|fiscal court|city of|town of/i.test(s || '') ? 'LOC' : /universit|college/i.test(s || '') ? 'STAT' : /private|trust|conservancy|foundation|society/i.test(s || '') ? 'NGO' : 'STAT';
  async function kyLive(ws) {
    const sq = x => x.replace(/'/g, "''"), out = [];
    await Promise.all(KYL.map(L => B.jget(`https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/${L.svc}/MapServer/${L.id}/query?` + new URLSearchParams({ where: ws.map(x => `UPPER(${L.nm}) LIKE '%${sq(x.toUpperCase())}%'`).join(' AND '), outFields: '*', returnGeometry: true, outSR: 4326, geometryPrecision: 5, maxAllowableOffset: 0.0001, f: 'geojson' }), null, 20000).then(j => (j.features || []).forEach(f => {
      const P = f.properties || {}; if (!f.geometry || !P[L.nm]) return;
      const own = (L.own && L.own(P)) || L.ag, mg = (L.mng && L.mng(P)) || L.ag;
      out.push({ src: 'Kentucky state GIS (live): ' + L.ag, f: fake(f, { Unit_Nm: L.full ? L.full(P) : P[L.nm], Own_Type: kyType(own), Loc_Own: own, Mang_Type: kyType(mg), Loc_Mang: mg, Loc_Ds: L.ds(P), Pub_Access: L.acc(P), State_Nm: 'KY', Web: L.web(P) }) });
    })).catch(() => {})));
    return out;
  }
  async function osmFind(ws, st) {
    const re = ws.map(x => x.replace(/[^\w ']/g, '')).join('.*');
    const qy = `[out:json][timeout:40];area["ISO3166-2"="US-${st}"]->.s;(nwr["name"~"${re}",i]["leisure"~"^(park|nature_reserve)$"](area.s);nwr["name"~"${re}",i]["boundary"~"^(protected_area|national_park)$"](area.s););out geom 8;`;
    let j = null; for (const u of OVER) { try { j = await B.jget(u, { method: 'POST', body: 'data=' + encodeURIComponent(qy), headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }, 45000); break; } catch (e) {} }
    return (j && j.elements || []).filter(e => e.tags && e.tags.name).map(e => {
      const lines = e.type === 'way' ? [e.geometry] : e.type === 'relation' ? (e.members || []).filter(m => m.type === 'way' && m.role !== 'inner' && m.geometry).map(m => m.geometry) : [];
      if (!lines.length) return null;
      const closed = lines.length === 1 && lines[0].length > 3 && lines[0][0].lat === lines[0][lines[0].length - 1].lat && lines[0][0].lon === lines[0][lines[0].length - 1].lon;
      const geometry = closed ? { type: 'Polygon', coordinates: [lines[0].map(p => [p.lon, p.lat])] } : { type: 'MultiLineString', coordinates: lines.map(l => l.map(p => [p.lon, p.lat])) };
      const t = e.tags, op = t.operator || t.owner || '';
      const fed = /national|u\.?s\.?|united states|forest service|fish and wildlife service|park service|bureau|army corps/i.test(op), stt = /state|commonwealth|department|division|dnr|kdfwr|fish (and|&) wildlife|nature preserves/i.test(op) && !fed;
      return { src: 'OpenStreetMap (NOT official, backup)', osm: true, f: { type: 'Feature', geometry, properties: { Unit_Nm: t.name, Own_Type: 'UNK', Loc_Own: t.owner || op || 'not listed', Mang_Type: fed ? 'FED' : stt ? 'STAT' : 'UNK', Loc_Mang: op || 'not listed', Loc_Ds: t.protection_title || t.leisure || t.boundary || '', Pub_Access: t.access === 'private' || t.access === 'no' ? 'XA' : t.access === 'yes' || t.access === 'permissive' ? 'OA' : 'UK', Category: 'Fee', GIS_Acres: closed ? acresOf(geometry) : 0, State_Nm: st, Mang_Name: '', Own_Name: '', Web: t.website || t['contact:website'] || '', WebOsm: true } } };
    }).filter(Boolean);
  }

  /* a point surely INSIDE the land (for the POTA pin): bbox middle if inside, else the middle of the widest crossing of a mid-latitude line */
  function pinOf(feats, bb) {
    let la = (bb[1] + bb[3]) / 2, lo = (bb[0] + bb[2]) / 2;
    if (feats.some(f => B.inside(la, lo, f.geometry))) return [la, lo];
    let best = null;
    for (let k = 1; k < 10; k++) {
      const y = bb[1] + (bb[3] - bb[1]) * k / 10, xs = [];
      feats.forEach(f => B.ringsOf(f.geometry).forEach(poly => poly.forEach(r => { for (let i = 0, j = r.length - 1; i < r.length; j = i++) { const [x1, y1] = r[j], [x2, y2] = r[i]; if ((y1 > y) !== (y2 > y)) xs.push(x1 + (y - y1) * (x2 - x1) / (y2 - y1)); } })));
      xs.sort((a, b) => a - b);
      for (let i = 0; i + 1 < xs.length; i += 2) { const w = xs[i + 1] - xs[i], m = (xs[i] + xs[i + 1]) / 2; if ((!best || w > best[2]) && feats.some(f => B.inside(y, m, f.geometry))) best = [y, m, w]; }
    }
    if (best) return [best[0], best[1]];
    const ln = B.linesOf(feats[0].geometry)[0] || [[lo, la]]; return [ln[0][1], ln[0][0]];
  }
  function grid(la, lo) { const A = 'ABCDEFGHIJKLMNOPQR', a = 'abcdefghijklmnopqrstuvwx'; let x = lo + 180, y = la + 90; const f1 = A[Math.floor(x / 20)] + A[Math.floor(y / 10)]; x %= 20; y %= 10; const f2 = '' + Math.floor(x / 2) + Math.floor(y); x %= 2; y %= 1; return f1 + f2 + a[Math.floor(x * 12)] + a[Math.floor(y * 24)]; }

  /* ---------- search ---------- */
  async function search() {
    const name = $('mrName').value.trim(), town = $('mrTown').value.trim(), st = $('mrState').value; lastQ = name;
    if (!st) { msg('<b>Pick the state first.</b> Each state has its own agencies, so the search needs to know where to look.'); $('mrState').focus(); return; }
    if (name.length < 3) { msg('Type at least part of the park name.'); return; }
    msg('Searching ' + esc(st) + ': the national public land database (every federal and state agency), the live National Park Service and Fish &amp; Wildlife maps' + (st === 'KY' ? ', Kentucky\'s state files' : '') + ' and OpenStreetMap…'); $('mrList').innerHTML = '';
    const w0 = words(name).slice(0, 3), w = w0.length ? w0 : [name.replace(/[^A-Za-z0-9' ]/g, ' ').trim()];
    let rows = [], box = null;
    const agOK = r => !agPick.size || [...agPick].some(k => { const [t, code] = k.split('|'); const a = AGL.find(x => agKey(x) === k); const loc = (r.Loc_Mang && !/^unknown$/i.test(r.Loc_Mang)) ? r.Loc_Mang : (AG[r.Mang_Name] || r.Mang_Name); return r.Mang_Type === t && r.Mang_Name === code && (!a || a.loc.toLowerCase() === String(loc).toLowerCase()); });
    const xP = agPick.size ? Promise.resolve([]) : extra(name, st);
    try {
      if (town) {
        const g = await B.jget('https://geocoding-api.open-meteo.com/v1/search?count=10&language=en&format=json&countryCode=US&name=' + encodeURIComponent(town)).catch(() => null);
        const hit = (g && g.results || []).find(r => stateOf(r.admin1) === st);
        if (hit) box = [hit.longitude - 0.7, hit.latitude - 0.6, hit.longitude + 0.7, hit.latitude + 0.6];
      }
      const o = { resultRecordCount: 200 };
      if (box) Object.assign(o, { geometry: box.join(','), geometryType: 'esriGeometryEnvelope', inSR: 4326, spatialRel: 'esriSpatialRelIntersects' });
      rows = (await qName(w, st, o)).filter(agOK);
      /* nothing with every word? try again with fewer words (spelling differs: 'Glades' vs 'Glade', extra words) */
      for (let n = w.length - 1; !rows.length && n >= 1; n--) { if (n === 1 && w[0].length < 5) break; rows = (await qName(w.slice(0, n), st, o)).filter(agOK); }
      if (!rows.length && w.length > 1) for (const x of w.filter(x => x.length >= 5)) { rows = (await qName([x], st, o)).filter(agOK); if (rows.length) break; }
    } catch (e) { rows = []; }
    const X = await xP;
    const G = new Map(); rows.forEach(r => { const k = (r.Unit_Nm || r.Loc_Nm) + '|' + r.State_Nm; const g = G.get(k) || { name: r.Unit_Nm || r.Loc_Nm, st: r.State_Nm, rows: [], acres: 0, src: 'USGS PAD-US (national public land database)' }; g.rows.push(r); g.acres += +r.GIS_Acres || 0; G.set(k, g); });
    const L = [...G.values()];
    // extra sources: grouped by name; only added when PAD-US has nothing with that name
    const rank = x => (x.osm ? 2 : 0) + (x.f.properties.Web ? 0 : 1) + (/live/.test(x.src) ? 0 : .5);
    X.sort((a, b) => rank(a) - rank(b));
    const XG = new Map(); X.forEach(x => { const n = x.f.properties.Unit_Nm; if (L.some(g => B.sameName(g.name, n))) return; const k = B.norm(n); const ex = XG.get(k); if (ex && ex.src !== x.src) return; const g = XG.get(k) || { name: n, st, rows: [], acres: 0, src: x.src, osm: x.osm, feats: [] }; g.feats.push(x.f); g.rows.push(x.f.properties); g.acres += +x.f.properties.GIS_Acres || 0; XG.set(k, g); });
    const all = L.concat([...XG.values()].sort((a, b) => (a.osm ? 1 : 0) - (b.osm ? 1 : 0))).sort((a, b) => (B.sameName(b.name, name) - B.sameName(a.name, name)) || ((a.osm ? 1 : 0) - (b.osm ? 1 : 0)) || b.acres - a.acres);
    if (!all.length) return notFound(name, st, town);
    if (all.length === 1) return open(all[0]);
    $('mrOut').innerHTML = '';
    $('mrList').innerHTML = `<p class="mr-help">${all.length} matches in ${esc(st)}. Pick one, or <a href="#" id="mrWeb">research the web for it ›</a></p>` + all.slice(0, 40).map((g, i) => `<button type="button" class="mr-pick${g.osm ? ' osm' : ''}" data-i="${i}"><b>${esc(g.name)}</b><span>${g.acres ? Math.round(g.acres).toLocaleString() + ' acres · ' : ''}${esc((g.rows[0].Loc_Mang && !/^unknown$/i.test(g.rows[0].Loc_Mang) ? g.rows[0].Loc_Mang : '') || AG[g.rows[0].Mang_Name] || g.rows[0].Loc_Own || '')}${['LOC', 'PVT', 'NGO', 'DIST'].includes(g.rows[0].Own_Type) ? ' <em class="mr-no">' + ({ LOC: 'city/county land: not eligible', PVT: 'private: not eligible', NGO: 'non-profit: not eligible', DIST: 'district: not eligible' })[g.rows[0].Own_Type] + '</em>' : ''}<br><small>${esc(g.src)}</small></span></button>`).join('');
    $('mrList').onclick = e => { if (e.target.id === 'mrWeb') { e.preventDefault(); $('mrList').innerHTML = ''; notFound(name, st, town); return; } const b = e.target.closest('[data-i]'); if (b) { $('mrList').innerHTML = ''; open(all[+b.dataset.i]); } };
  }
  /* ---------- nothing official by name: research the web (Wikidata / Wikipedia + OpenStreetMap search),
     then go BACK to the official database with the location we learned (finds it even when the agency spells it differently) ---------- */
  const WD = 'https://www.wikidata.org/w/api.php';
  async function webResearch(name, st, town) {
    const box = await stBox(st), inSt = (la, lo) => !box || (lo >= box[0] - .05 && lo <= box[2] + .05 && la >= box[1] - .05 && la <= box[3] + .05);
    const hits = [];
    const wd = (async () => {
      const s1 = await B.jget(WD + '?' + new URLSearchParams({ action: 'wbsearchentities', search: name, language: 'en', type: 'item', limit: 8, format: 'json', origin: '*' }));
      const ids = (s1.search || []).map(x => x.id); if (!ids.length) return;
      const e = await B.jget(WD + '?' + new URLSearchParams({ action: 'wbgetentities', ids: ids.join('|'), props: 'labels|descriptions|claims|sitelinks', languages: 'en', sitefilter: 'enwiki', format: 'json', origin: '*' }));
      const val = (c, p) => ((c[p] || [])[0] || {}).mainsnak && c[p][0].mainsnak.datavalue ? c[p][0].mainsnak.datavalue.value : null;
      const refIds = new Set(); const items = Object.values(e.entities || {});
      items.forEach(it => { const c = it.claims || {}; ['P137', 'P127', 'P31'].forEach(p => (c[p] || []).forEach(x => { const v = x.mainsnak.datavalue; if (v && v.value && v.value.id) refIds.add(v.value.id); })); });
      let L = {}; if (refIds.size) { const r = await B.jget(WD + '?' + new URLSearchParams({ action: 'wbgetentities', ids: [...refIds].slice(0, 50).join('|'), props: 'labels', languages: 'en', format: 'json', origin: '*' })).catch(() => ({})); Object.values(r.entities || {}).forEach(x => { L[x.id] = x.labels && x.labels.en ? x.labels.en.value : x.id; }); }
      const lab = (c, p) => (c[p] || []).map(x => x.mainsnak.datavalue && x.mainsnak.datavalue.value.id).filter(Boolean).map(id => L[id] || id);
      items.forEach(it => { const c = it.claims || {}, co = val(c, 'P625'); if (!co || !inSt(co.latitude, co.longitude)) return;
        hits.push({ src: 'Wikidata / Wikipedia', name: it.labels && it.labels.en ? it.labels.en.value : name, la: co.latitude, lo: co.longitude, what: it.descriptions && it.descriptions.en ? it.descriptions.en.value : '', type: lab(c, 'P31').join(', '), operator: lab(c, 'P137').join(', '), owner: lab(c, 'P127').join(', '), web: val(c, 'P856') || '', wiki: it.sitelinks && it.sitelinks.enwiki ? 'https://en.wikipedia.org/wiki/' + encodeURIComponent(it.sitelinks.enwiki.title.replace(/ /g, '_')) : '', item: 'https://www.wikidata.org/wiki/' + it.id }); });
    })().catch(() => {});
    const nm = (async () => {
      const j = await B.jget('https://nominatim.openstreetmap.org/search?' + new URLSearchParams({ q: name + (town ? ', ' + town : '') + ', ' + st + ', USA', format: 'jsonv2', countrycodes: 'us', extratags: 1, limit: 6 }));
      (j || []).forEach(x => { const la = +x.lat, lo = +x.lon; if (!inSt(la, lo)) return; const t = x.extratags || {};
        hits.push({ src: 'OpenStreetMap search', name: x.name || x.display_name.split(',')[0], la, lo, what: x.display_name, type: (x.category + ' / ' + x.type).replace(/_/g, ' '), operator: t.operator || '', owner: t.owner || t.ownership || '', web: t.website || t['contact:website'] || t.url || '', access: t.access || '' }); });
    })().catch(() => {});
    await Promise.all([wd, nm]);
    // back to the official database at each place we learned about
    const seen = new Set(), found = [];
    for (const h of hits.slice(0, 8)) {
      const k = h.la.toFixed(3) + ',' + h.lo.toFixed(3); if (seen.has(k)) continue; seen.add(k);
      h.land = await q({ geometry: `${h.lo},${h.la}`, geometryType: 'esriGeometryPoint', inSR: 4326, spatialRel: 'esriSpatialRelIntersects', where: `State_Nm='${st}'` }).catch(() => null);
      if (h.land && !h.land.length) h.land = await q({ geometry: `${h.lo - .004},${h.la - .004},${h.lo + .004},${h.la + .004}`, geometryType: 'esriGeometryEnvelope', inSR: 4326, spatialRel: 'esriSpatialRelIntersects', where: `State_Nm='${st}'` }).then(r => { r.forEach(x => x._near = true); return r; }).catch(() => null);
      (h.land || []).forEach(r => found.push(r));
    }
    return { hits, found };
  }
  async function notFound(name, st, town) {
    const gq = s => 'https://www.google.com/search?q=' + encodeURIComponent(s);
    const list = AGL.filter(a => !/universit|college|guard|transportation|veterans|unknown|division of water/i.test(a.loc)).slice(0, 30);
    msg(`Not in the official databases by that name. Now researching the web (Wikipedia / Wikidata and the OpenStreetMap search) to find where it is, then checking the official land database at that spot…`);
    const R = await webResearch(name, st, town);
    const lands = new Map(); R.found.forEach(r => { const k = (r.Unit_Nm || r.Loc_Nm) + '|' + r.State_Nm; const g = lands.get(k) || { name: r.Unit_Nm || r.Loc_Nm, st: r.State_Nm, rows: [], acres: 0, src: 'USGS PAD-US (found by location)' }; g.rows.push(r); g.acres += +r.GIS_Acres || 0; lands.set(k, g); });
    const LG = [...lands.values()];
    const hitHtml = R.hits.length ? R.hits.slice(0, 6).map(h => {
      const land = h.land == null ? '<span class="mr-w">Could not check the official database at this spot.</span>' : !h.land.length ? '<span class="mr-no">No public land at this spot in the official database: it may be private land, or too new to be listed.</span>' : '<span class="mr-ok">Official database at this spot: ' + [...new Set(h.land.map(r => (r.Unit_Nm || r.Loc_Nm) + ' (' + (TYPE[r.Own_Type] || r.Own_Type) + (r.Loc_Mang ? ', ' + r.Loc_Mang : '') + ')' + (r._near ? ' — next to it' : '')))].map(esc).join('; ') + '</span>';
      const pvt = /private|privately/i.test(h.owner + ' ' + h.access + ' ' + h.operator);
      return `<div class="mr-hit"><b>${esc(h.name)}</b><small>${esc(h.src)}</small><p>${esc([h.what, h.type].filter(Boolean).join(' · '))}</p>${h.operator || h.owner ? `<p>Run by: <b>${esc(h.operator || '?')}</b>${h.owner ? ' · owned by: <b>' + esc(h.owner) + '</b>' : ''}${pvt ? ' <span class="mr-no">says private</span>' : ''}</p>` : ''}${h.access ? `<p>Access tag: ${esc(h.access)}</p>` : ''}<p>${land}</p><div class="mr-btns">${h.web ? `<a class="gold" href="${esc(h.web)}" target="_blank" rel="noopener">WEBSITE LISTED ↗</a>` : ''}${h.wiki ? `<a href="${esc(h.wiki)}" target="_blank" rel="noopener">WIKIPEDIA ↗</a>` : ''}${h.item ? `<a href="${esc(h.item)}" target="_blank" rel="noopener">WIKIDATA ↗</a>` : ''}<a href="https://www.google.com/maps/search/?api=1&query=${h.la},${h.lo}" target="_blank" rel="noopener">MAP ↗</a>${h.operator ? `<a href="${gq(`"${h.name}" "${h.operator}" site:.gov`)}" target="_blank" rel="noopener">SEARCH ${esc(h.operator.toUpperCase().slice(0, 40))} ↗</a>` : ''}</div></div>`;
    }).join('') : '<p>The web search didn\'t find it either.</p>';
    const LOCRE = /\b(city|county|town of|village|municipal|parks? (and|&) rec|metro|township|fiscal court|school|private|church|association|foundation|homeowners|ymca|scouts?|club|llc|inc\.?)\b/i;
    const locHit = R.hits.find(h => LOCRE.test((h.operator || '') + ' ' + (h.owner || '')));
    const noLand = R.hits.length && R.hits.every(h => h.land && !h.land.length);
    const gWho = gq(`"${name}"${town ? ' ' + town : ''} ${st} park owned by`);
    const whoBox = locHit ? `<div class="mr-v no"><b>WEB SOURCES SAY: ${esc((locHit.operator || locHit.owner).toUpperCase())}</b><span>${esc(locHit.name)} (${esc(locHit.src)}) lists it as run${locHit.owner ? ' / owned' : ''} by ${esc(locHit.operator || locHit.owner)}. City, county and private parks are not added to POTA. Confirm with the owner's own page.</span></div>`
      : `<div class="mr-v maybe"><b>${noLand ? 'NO STATE OR FEDERAL LAND WHERE IT IS: PROBABLY A CITY, COUNTY OR PRIVATE PARK' : 'NOT IN ANY STATE OR FEDERAL LIST: PROBABLY A CITY, COUNTY OR PRIVATE PARK'}</b><span>Places missing from every federal and state list are almost always run by a city, county or private group, and POTA doesn't add those. Use WHO OWNS IT? to see who runs it. If the owner turns out to be a state or federal agency, it may still qualify.</span></div>`;
    $('mrOut').innerHTML = `<div class="mr-msg"><b>Not found by name in ${esc(st)}</b> in the official databases${town ? ' near ' + esc(town) : ''}.</div>${whoBox}<div class="mr-rl" style="margin:8px 0 14px"><a class="gold" href="${gWho}" target="_blank" rel="noopener">WHO OWNS IT? (GOOGLE) ↗</a><a href="${gq(`"${name}" ${town || ''} ${st} city parks`)}" target="_blank" rel="noopener">CITY / COUNTY PARK PAGES (GOOGLE) ↗</a></div>
${LG.length ? `<div class="mr-sec mr-found"><h3>FOUND IT BY LOCATION IN THE OFFICIAL DATABASE</h3><p class="mr-help">The web told us where it is, and the official land database has land there under a different name. Pick one to run the rule check:</p>${LG.map((g, i) => `<button type="button" class="mr-pick" data-l="${i}"><b>${esc(g.name)}</b><span>${Math.round(g.acres).toLocaleString()} acres · ${esc(g.rows[0].Loc_Mang || AG[g.rows[0].Mang_Name] || '')}${g.rows.some(r => r._near) ? '<br><small>next to the spot the web gave</small>' : ''}</span></button>`).join('')}</div>` : ''}
<div class="mr-sec"><h3>WHAT THE WEB SAYS (NOT OFFICIAL)</h3><p class="mr-help">From Wikipedia / Wikidata and the OpenStreetMap search. Use it to find the place and the agency's own site; the official answer is still the agency's page.</p>${hitHtml}</div>
<div class="mr-sec"><h3>SEARCH EACH AGENCY'S OWN WEBSITE</h3><p class="mr-help">Brand-new or very small places often show up on the agency's site first. Try fewer words if nothing comes up.</p><div class="mr-btns">${list.map(a => `<a href="${gq(`"${name}" "${a.loc}"`)}" target="_blank" rel="noopener">${esc(a.loc)} ↗</a>`).join('')}<a class="gold" href="${gq(`"${name}" ${st} site:.gov`)}" target="_blank" rel="noopener">ANY .GOV SITE ↗</a></div>
<p class="mr-help">If the agency's own page shows it's federal or state land and open to the public, it may still qualify; use the agency's page and map as the source.</p></div>`;
    $('mrOut').querySelectorAll('[data-l]').forEach(b => b.onclick = () => open(LG[+b.dataset.l]));
  }

  const SN = { alabama: 'AL', alaska: 'AK', arizona: 'AZ', arkansas: 'AR', california: 'CA', colorado: 'CO', connecticut: 'CT', delaware: 'DE', florida: 'FL', georgia: 'GA', hawaii: 'HI', idaho: 'ID', illinois: 'IL', indiana: 'IN', iowa: 'IA', kansas: 'KS', kentucky: 'KY', louisiana: 'LA', maine: 'ME', maryland: 'MD', massachusetts: 'MA', michigan: 'MI', minnesota: 'MN', mississippi: 'MS', missouri: 'MO', montana: 'MT', nebraska: 'NE', nevada: 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', ohio: 'OH', oklahoma: 'OK', oregon: 'OR', pennsylvania: 'PA', 'rhode island': 'RI', 'south carolina': 'SC', 'south dakota': 'SD', tennessee: 'TN', texas: 'TX', utah: 'UT', vermont: 'VT', virginia: 'VA', washington: 'WA', 'west virginia': 'WV', wisconsin: 'WI', wyoming: 'WY' };
  const stateOf = n => SN[String(n || '').toLowerCase()] || '';

  /* ---------- one park ---------- */
  async function open(g) {
    msg('Loading the boundary and checking POTA…');
    let fc;
    if (g.feats) fc = { features: g.feats };
    else try {
      const where = `Unit_Nm='${g.name.replace(/'/g, "''")}' AND State_Nm='${g.st}'`;
      const big = g.acres > 50000;
      fc = await B.jget(PADUS + '?' + new URLSearchParams({ where, outFields: F, returnGeometry: true, outSR: 4326, geometryPrecision: 5, maxAllowableOffset: big ? 0.0004 : 0.00005, f: 'geojson' }));
    } catch (e) { msg('Could not load the boundary. Try again.'); return; }
    const feats = (fc.features || []).filter(f => f.geometry);
    if (!feats.length) { msg('No boundary shape came back for that one.'); return; }
    const bb = feats.reduce((a, f) => { const b = B.bbox(f.geometry); return [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])]; }, [180, 90, -180, -90]);
    let [la, lo] = pinOf(feats, bb);
    const R = feats.map(f => f.properties);
    if (g.st === 'KY' && /\bWMA\b|wildlife management area|wildlife area|hunting/i.test(g.name)) await wmaOwners(R.map(r => ({ src: '', f: { properties: r } })), true);
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
    /* 'already in POTA' only when the name is the SAME (not just close) and it's the same kind of place;
       close names or another kind of place on the same lake/river are listed as 'similar' to check by eye */
    const gKind = B.kindOf(g.name) || B.kindOf(R.map(r => (r.Loc_Ds || '') + ' ' + (DES[r.Des_Tp] || '')).join(' ')) || B.kindOf(lastQ);
    const kindOK = n => { const k = B.kindOf(n); return !k || !gKind || k === gKind; };
    const exact = n => B.norm(n) === B.norm(g.name) && kindOK(n);
    const close = n => B.sameName(n, g.name) || B.norm(n).split(' ').filter(w => w.length > 3 && B.norm(g.name).split(' ').includes(w)).length >= 2;
    const cand = near.concat(((look || []).filter(x => x.type === 'park').map(x => ({ ref: x.value, name: x.display.replace(/^\S+\s+/, ''), far: true })))).filter(p => !p.far || /^US-/.test(p.ref));
    const uniqP = L => [...new Map(L.map(p => [p.ref, p])).values()];
    const already = uniqP(cand.filter(p => exact(p.name)));
    const similar = uniqP(cand.concat(inside).filter(p => !already.some(a => a.ref === p.ref) && close(p.name)));
    const parents = (around || []).filter(r => (r.Unit_Nm || '') !== g.name && (+r.GIS_Acres || 0) > g.acres * 1.5 && r.Category !== 'Easement');
    const parentPota = parents.map(p => ({ p, pota: near.find(x => B.sameName(x.name, p.Unit_Nm)) })).filter(x => x.pota);
    const sameAgency = parentPota.filter(x => x.p.Mang_Name === base[0].Mang_Name && (x.p.Loc_Mang || '') === (base[0].Loc_Mang || ''));
    // ---------- the rules ----------
    const own = uniq('Own_Type'), mng = uniq('Mang_Type'), mngN = uniq('Mang_Name'), locM = (uniq('Loc_Mang').filter(x => x && !/^unknown$/i.test(x)).join('; ') || mngN.map(m => AG[m]).filter(Boolean).join('; ') || uniq('Loc_Own').filter(x => x && !/^unknown$/i.test(x)).join('; ') + ' (owner; the record names no manager)'), acc = uniq('Pub_Access'), des = uniq('Des_Tp');
    const top = t => t === 'FED' || t === 'STAT';
    const corpsOwnEarly = uniq('Own_Name').includes('USACE') || /corps of engineers|\bUSACE\b|\bCOE\b/i.test(uniq('Loc_Own').join(' '));
    const res = [];
    const add = (v, title, why, links) => res.push({ v, title, why, links: links || [] });
    if (g.st === 'KY' && !R.some(r => r.Web)) { try { const F = await B.ky(); const m = F.find(f => f.properties && f.properties.URL && (B.sameName(f._nm, g.name) || B.norm(f._nm) === B.norm(g.name))); if (m) R.push({ Web: m.properties.URL, _ky: true }); } catch (e) {} if (!R.some(r => r.Web)) { try { const L = await kyLive(words(g.name).slice(0, 3)); const m = L.find(x => x.f.properties.Web && (B.sameName(x.f.properties.Unit_Nm, g.name) || B.norm(x.f.properties.Unit_Nm) === B.norm(g.name))) || (L.length === 1 && L[0].f.properties.Web ? L[0] : null); if (m) R.push({ Web: m.f.properties.Web, _ky: true }); } catch (e) {} } }
    const offWeb = [...new Set(R.map(r => !r.WebOsm && r.Web).filter(Boolean))], osmWeb = [...new Set(R.map(r => r.WebOsm && r.Web).filter(Boolean))];
    const LBL = [['Unit_Nm', 'Name'], ['Says', 'Fish & Wildlife page says'], ['Loc_Own', 'Owner'], ['Own_Type', 'Owner type'], ['Loc_Mang', 'Manager'], ['Mang_Type', 'Manager type'], ['Loc_Ds', 'Designation'], ['Pub_Access', 'Public access'], ['GIS_Acres', 'Acres'], ['Category', 'Kind of record'], ['Date_Est', 'Established'], ['Comments', 'Notes'], ['Web', 'Official page']];
    const fmtV = (k, v) => k === 'Own_Type' || k === 'Mang_Type' ? (TYPE[v] || v) : k === 'Pub_Access' ? (ACC[v] || v) : k === 'GIS_Acres' ? Math.round(+v).toLocaleString() : k === 'Category' ? ({ Fee: 'Owned land (fee)', Easement: 'Easement', Designation: 'Designation', Proclamation: 'Proclamation boundary' }[v] || v) : v;
    const recHtml = () => `<details class="mr-rec"><summary>SEE THE RECORD THIS CAME FROM</summary><p class="mr-help">Source: ${esc(g.src || 'USGS PAD-US')}${!g.src || /PAD-US/.test(g.src) ? ' (USGS Protected Areas Database, version 4)' : ''}</p>${base.slice(0, 6).map(r => `<table>${LBL.filter(([k]) => r[k] != null && r[k] !== '' && k !== 'WebOsm').map(([k, l]) => `<tr><th>${l}</th><td>${k === 'Web' ? `<a href="${esc(r[k])}" target="_blank" rel="noopener">${esc(r[k])}</a>` : esc(fmtV(k, r[k]))}</td></tr>`).join('')}</table>`).join('')}</details>`;
    const recL = () => [];
    const gq = s2 => 'https://www.google.com/search?q=' + encodeURIComponent(s2);
    const sat = `https://www.google.com/maps/@${la.toFixed(5)},${lo.toFixed(5)},15z/data=!3m1!1e3`;
    add(own.every(top) ? 'YES' : own.some(t => t === 'JNT' || t === 'UNK') && !own.some(t => ['LOC', 'PVT', 'NGO', 'TRIB', 'DIST'].includes(t)) ? 'CHECK' : 'NO', 'Owned by the national or state government',
      `Owner: ${base.map(r => (r.Loc_Own || AG[r.Own_Name] || r.Own_Name) + ' (' + (TYPE[r.Own_Type] || r.Own_Type) + ')').filter((x, i, a) => a.indexOf(x) === i).join('; ')}. POTA rule: "All new parks must be owned and operated by the two highest tiers of government" (in the US: federal and state). County, city, private and non-profit land is not added.`, recL('OWNER IN THE OFFICIAL RECORD').concat([[`SEARCH ${(locM.replace(/ \(.*$/, '') || 'AGENCY').toUpperCase().slice(0, 40)} (GOOGLE) ↗`, gq(`"${g.name}" "${locM}"`)]]));
    add(mng.every(top) && !mngN.includes('USACE') && !mngN.includes('TVA') && !/universit|college/i.test(locM) ? 'YES' : mngN.includes('TVA') || /universit|college/i.test(locM) || mng.some(t => t === 'JNT' || t === 'UNK') ? 'CHECK' : 'NO', 'Run (operated) by the national or state government',
      `Manager: ${esc(locM || mngN.map(m => AG[m] || m).join('; '))} (${mng.map(t => TYPE[t] || t).join(', ')}). ${mngN.includes('USACE') ? 'Run by the Army Corps of Engineers: POTA does not add Corps sites except a very few already confirmed. ' : ''}${mngN.includes('TVA') ? 'TVA land is researched case by case. ' : ''}${/universit|college/i.test(locM) ? 'University land is rarely eligible. ' : ''}${own.includes('FED') && mng.includes('STAT') ? 'Federal land run by a state agency counts as both top tiers' + (corpsOwnEarly ? ', but this is Corps land: see the Corps rule below. ' : '. ') : ''}Parks run by commissions, districts, boards, societies or third parties don't qualify.`, recL('MANAGER IN THE OFFICIAL RECORD'));
    /* Army Corps of Engineers land (POTA: 'POTA has generally sidestepped USACE sites'; only a few confirmed exceptions) */
    const corpsOwn = uniq('Own_Name').includes('USACE') || /corps of engineers|\bUSACE\b|\bCOE\b/i.test(uniq('Loc_Own').join(' ')), corpsMng = mngN.includes('USACE') || /corps of engineers|\bUSACE\b/i.test(locM);
    add(corpsMng ? 'NO' : corpsOwn ? 'CHECK' : 'YES', 'Not Army Corps of Engineers land',
      corpsMng ? 'The Army Corps of Engineers runs it. POTA\'s rules say Corps sites are 100% Corps owned but mostly run through partnerships with local governments, so POTA has generally sidestepped them, with only a few confirmed exceptions. Treat this as not eligible.'
      : corpsOwn ? `The land belongs to the Army Corps of Engineers and ${esc(locM || 'another agency')} runs it. POTA has generally sidestepped Corps sites; only a few have been confirmed as exceptions. Some state wildlife areas on Corps lakes are POTA parks (in Kentucky, for example, Dewey Lake, Fishtrap Lake and Yatesville Lake WMAs) and many are not. <b>Don't count on it:</b> only the Mapping Representative can say whether this one is an exception.`
      : 'The owner is not the Army Corps of Engineers.', corpsOwn || corpsMng ? [['POTA RULES: CORPS OF ENGINEERS ↗', RULES_URL]] : []);
    const raOnly = !acc.includes('OA') && acc.includes('RA');
    add(acc.includes('OA') ? 'YES' : acc.includes('XA') || raOnly ? 'NO' : 'CHECK', 'Open to the public',
      raOnly ? `Database says: <b>restricted</b> (visits only with a permit, by appointment, in some seasons, or only part of it). POTA adds parks the agency says are open to the public; a place you can only visit with special permission is not open to the public. <b>Only if the agency's own page says anyone may visit</b> (no special permit) could it still qualify; then treat this as YES.${/nature preserve/i.test(locM + ' ' + uniq('Loc_Own').join(' ') + ' ' + g.name) ? ' Many Kentucky state nature preserves are visit-by-permission only.' : ''}`
      : `Database says: ${acc.map(a => ACC[a] || a).join('; ')}. POTA: "If the National or State agency says that a park is open to the public, then it is eligible." Hard access (hike-in, boat-in) is fine. Confirm on the agency's page.`, recL('ACCESS IN THE OFFICIAL RECORD').concat([[`RULES / HOURS (GOOGLE) ↗`, gq(`"${g.name}" ${g.st} hours rules access`)]]));
    const exName = /national (historic|recreation(al)?) trail|heritage area|historic landmark|historic place|national register|scenic byway/i.test(g.name);
    const exDes = des.some(d => ['CONE', 'AGRE', 'RECE', 'HCAE', 'OTHE'].includes(d)) || R.every(r => r.Category === 'Easement');
    add(exName || exDes || own.includes('TRIB') || mng.includes('TRIB') || mng.includes('DIST') ? 'NO' : 'YES', 'Not a type POTA won\'t add',
      exName ? 'The name looks like a type POTA excludes (National Recreation Trail, Heritage Area, Historic Place/Landmark, byway).' : exDes ? 'This is an easement (usually private land with a conservation agreement), not a park.' : own.includes('TRIB') || mng.includes('TRIB') ? 'Tribal land is treated as private unless the tribal council says otherwise.' : mng.includes('DIST') ? 'Run by a special district or commission.' : 'Not a Corps site, heritage area, National Recreation Trail, historic landmark, tribal land, commission/district site or commercial trail.', recL('DESIGNATION IN THE OFFICIAL RECORD'));
    add(sameAgency.length ? 'NO' : parentPota.length ? 'YES' : 'YES', 'Not a "sub-park" inside an existing POTA park of the same agency',
      sameAgency.length ? `It sits inside ${sameAgency.map(x => esc(x.p.Unit_Nm) + ' (' + esc(x.pota.ref) + ')').join(', ')}, run by the same agency. POTA: "does not create sub-parks within existing parks if both parks are part of the same government tier or agency."` : parentPota.length ? `It's inside ${parentPota.map(x => esc(x.p.Unit_Nm) + ' (' + esc(x.pota.ref) + ')').join(', ')}, but that is run by a different agency, so it can be its own park (and a 2-fer).` : 'No bigger POTA park run by the same agency surrounds it.', sameAgency.concat(parentPota).map(x => [x.pota.ref + ' ON POTA ↗', 'https://pota.app/#/park/' + encodeURIComponent(x.pota.ref)]));
    add(already.length ? 'NO' : similar.some(p => inside.some(i => i.ref === p.ref)) ? 'CHECK' : 'YES', 'Not already in POTA',
      already.length ? 'Looks like it is already a POTA park: ' + already.map(p => `<a href="https://pota.app/#/park/${encodeURIComponent(p.ref)}" target="_blank" rel="noopener">${esc(p.ref)} ${esc(p.name)}</a>`).join(', ') + '. No need to add it.' : `No POTA park with this exact name and kind of place.${similar.length ? ' <b>Similar names in POTA (a different kind of place or a close name, so NOT counted as the same park):</b> ' + similar.slice(0, 5).map(p => `<a href="https://pota.app/#/park/${encodeURIComponent(p.ref)}" target="_blank" rel="noopener">${esc(p.ref)} ${esc(p.name)}</a>`).join(', ') + '. Open them and check it isn\'t the same land.' : ''}${inside.length ? ' (POTA parks with pins inside this boundary: ' + inside.map(p => esc(p.ref + ' ' + p.name)).join(', ') + ' — make sure it isn\'t the same place under another name.)' : ''}`, already.concat(similar.slice(0, 3)).map(p => [p.ref + ' ON POTA ↗', 'https://pota.app/#/park/' + encodeURIComponent(p.ref)]).concat([['POTA NAME SEARCH ↗', 'https://api.pota.app/lookup?search=' + encodeURIComponent(words(g.name).join(' ') || g.name) + '&size=60'], ['POTA PARKS AROUND HERE ↗', `https://api.pota.app/park/grids/${(la - .3).toFixed(2)}/${(lo - .3).toFixed(2)}/${(la + .3).toFixed(2)}/${(lo + .3).toFixed(2)}/0`]]));
    const lakeOnly = /\blake\b|\breservoir\b|\bpond\b/i.test(g.name) && g.acres < 1500;
    add(lakeOnly ? 'CHECK' : 'CHECK', lakeOnly ? 'Not an agency lake surrounded by city, county or private land' : 'Has a public way in (road, trail or water)',
      lakeOnly ? 'POTA does NOT add agency-owned lakes that are surrounded by city, county or private land. Look at the map: is there state/federal land around the water (shoreline, ramp area) that the public can reach, or is the shore someone else\'s?' : 'Private land all around is fine as long as the public can get in: a public road, parking lot, trailhead, trail or boat ramp that reaches the land. POTA only turns down (and since 2022 deactivates) land that is cut off by private property, where you would have to cross someone\'s land to get there. The tool looks for public roads, parking, trailheads and ramps inside the boundary.', [['SATELLITE VIEW ↗', sat], ['STREET VIEW AT THE PIN ↗', `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${la.toFixed(5)},${lo.toFixed(5)}`]]);
    add(offWeb.length ? 'YES' : 'CHECK', 'Has an official government web page with a boundary map',
      offWeb.length ? `The official source lists the agency's page for it (below).${offWeb.some(u => /fw\.ky\.gov\/Public_Lands_Search/i.test(u)) ? ' On Kentucky Fish & Wildlife pages the boundary map PDF is linked on that page.' : ' Open it and find the boundary map there.'}` : `POTA needs the agency's own page (and its boundary map) for the park's POTA listing. If there's no web page, a civil-agency or GIS map can be used. Tourist or commercial sites don't count. Agency: <b>${esc(locM || '')}</b>.`,
      offWeb.map(u => ['OFFICIAL PAGE: ' + (u.replace(/^https?:\/\/(www\.)?/, '').split('/')[0]).toUpperCase() + ' ↗', u, 'gold']).concat(osmWeb.map(u => ['WEBSITE (FROM OPENSTREETMAP) ↗', u])).concat(offWeb.length ? [] : agSites(locM + ' ' + uniq('Loc_Own').join(' '), g.st).map(d => [`FIND ITS PAGE ON ${d.toUpperCase()} (GOOGLE) ↗`, gq(`site:${d} "${g.name.replace(/\b(state nature preserve|snp|wma|state park)\b/ig, '').trim()}"`)])).concat([['SEARCH .GOV (GOOGLE) ↗', gq(`"${g.name}" ${g.st} site:.gov`)], ['SEARCH FOR THE MAP (GOOGLE) ↗', gq(`"${g.name}" ${locM} map`)]]));
    add('INFO', 'Size', `About ${Math.round(g.acres).toLocaleString()} acres. POTA has no size rule, but very small parks may wait if activating would get in the way of the park's main use.`);
    if (feats.length > 1) add('INFO', 'Split into pieces', `The land comes in ${feats.length} pieces. POTA: all tracts of one unit share ONE reference number.`);
    if (/wildlife refuge|\bNWR\b/i.test(g.name) || uniq('Own_Name').includes('FWS') && /refuge/i.test(uniq('Loc_Ds').join(' '))) add('INFO', 'National Wildlife Refuge', 'POTA calls refuges its most sensitive US park type: what is fine in other parks may not be fine here. Check with the refuge office before activating.');
    const nNo = res.filter(r => r.v === 'NO').length, nCk = res.filter(r => r.v === 'CHECK').length;
    const verdict = already.length ? ['no', 'ALREADY A POTA PARK'] : nNo ? ['no', 'LIKELY NOT ELIGIBLE'] : corpsOwn ? ['no', 'UNLIKELY: ARMY CORPS OF ENGINEERS LAND (ONLY A FEW ARE EXCEPTIONS)'] : nCk ? ['maybe', 'LOOKS POSSIBLE: CONFIRM THE YELLOW ITEMS'] : ['yes', 'LOOKS ELIGIBLE'];

    const nm = g.name, stn = g.st;
    const note = [`Park: ${nm} (${stn})`, '', `Owner: ${base.map(r => r.Loc_Own || AG[r.Own_Name] || r.Own_Name).filter((x, i, a) => a.indexOf(x) === i).join('; ')}`, `Managed by: ${locM}`, `Designation: ${base.map(r => r.Loc_Ds || DES[r.Des_Tp] || r.Des_Tp).filter((x, i, a) => a.indexOf(x) === i).join('; ')}`, `Public access: ${acc.map(a => ACC[a] || a).join('; ')}`, `Size: about ${Math.round(g.acres).toLocaleString()} acres`, `Suggested POTA pin (inside the boundary): ${la.toFixed(5)}, ${lo.toFixed(5)}`, `Grid square: ${grid(la, lo)}`, 'County: @@COUNTY@@', 'Official web page: ' + (offWeb.join(' ; ') || '(paste the agency link here)'), 'Official boundary map: (paste the agency map link here)', `Boundary source: ${g.src || 'USGS PAD-US'} ("${nm}", ${stn})`, '', 'Rule check:'].concat(res.filter(r => r.v !== 'INFO').map(r => `- ${r.title}: ${r.v}`), ['', 'Links found:', '@@LINKS@@']).join('\n');
    $('mrOut').innerHTML = `<section class="mr-res">
<div class="mr-head"><div class="mr-k">${esc(stn)} · ${esc(g.src || "USGS PAD-US")}</div><h2>${esc(nm)}</h2><p>${esc([locM, Math.round(g.acres).toLocaleString() + ' acres', base.map(r => r.Loc_Ds || DES[r.Des_Tp] || '').filter(Boolean).filter((x, i, a) => a.indexOf(x) === i).join(' / ')].filter(Boolean).join(' · '))}</p></div>
${g.osm ? `<div class="mr-osm"><b>From OpenStreetMap, not an official source.</b> ${esc(B.OSM_NOTE)} Owner and manager come from volunteer tags, so treat every answer below as CHECK until the agency's own page confirms it.</div>` : ""}<div class="mr-v ${verdict[0]}"><b>${verdict[1]}</b><span>${res.filter(r => r.v === 'YES').length} yes · ${nNo} no · ${nCk} to check yourself</span></div>
<div class="mr-rules">${res.map(r => `<div class="mr-r ${r.v.toLowerCase()}"><i>${r.v === 'INFO' ? 'INFO' : r.v}</i><div><b>${esc(r.title)}</b><p>${r.why}</p>${/^Owned/.test(r.title) ? recHtml() : /^(Run|Open|Not a type)/.test(r.title) ? '<p class="mr-help">Record: see SEE THE RECORD THIS CAME FROM in the first rule.</p>' : ''}${r.links.length ? `<div class="mr-rl">${r.links.map(l => `<a class="${l[2] || ''}" href="${esc(l[1])}" target="_blank" rel="noopener">${esc(l[0])}${/↗$/.test(l[0]) ? '' : ' ↗'}</a>`).join('')}</div>` : ''}${/official government web page/.test(r.title) ? '<div class="mr-rl" id="mrWebRule"></div>' : ''}${/surrounded|public way in/.test(r.title) ? '<div id="mrAccess" class="mr-help">Looking for a public road, parking, trailhead or ramp into it…</div><div id="mrAround" class="mr-help">Checking the official land around it…</div>' : ''}${/sub-park/.test(r.title) ? `<details class="mr-rec"><summary>LAND RECORDS AT THE PIN</summary><table>${(around || []).slice(0, 12).map(x => `<tr><th>${esc(x.Unit_Nm || x.Loc_Nm || '?')}</th><td>${esc([x.Loc_Mang, TYPE[x.Own_Type] || x.Own_Type, x.GIS_Acres ? Math.round(+x.GIS_Acres).toLocaleString() + ' acres' : ''].filter(Boolean).join(' · '))}</td></tr>`).join('') || '<tr><td>none in the database</td></tr>'}</table></details>` : ''}</div></div>`).join('')}</div>
<div class="mr-sec"><h3>OFFICIAL WEBSITE &amp; MAP</h3><div class="mr-btns">${offWeb.map(u => `<a class="gold" href="${esc(u)}" target="_blank" rel="noopener">OFFICIAL PAGE ↗</a>`).join("")}<a href="${gq(`"${nm}" ${stn} site:.gov`)}" target="_blank" rel="noopener">SEARCH .GOV (GOOGLE) ↗</a><a href="${gq(`"${nm}" ${locM} boundary map`)}" target="_blank" rel="noopener">SEARCH FOR THE MAP (GOOGLE) ↗</a></div><p class="mr-help">These search only for the park by name with its agency. Use the agency's own page, not tourist sites.</p></div>
<div class="mr-sec"><h3>BOUNDARY MAP (${esc(g.src || 'USGS PAD-US')})</h3><div id="mrMap"></div><p class="mr-help">Gold = this park's land in the source above. Blue dots = POTA parks nearby (tap for the number). Blue P squares = parking (🥾 trailhead, ⛵ boat ramp); green dots = roads or trails into it. Tap the map to drop a pin; ⛶ FULL for full screen; layers for satellite, topo and terrain.</p><div class="mr-btns" id="mrFiles"></div></div>
<div class="mr-sec mr-facts"><h3>📍 FACTS FOR ADDING THE PARK</h3>
<div class="mr-fact"><span>POTA PIN (inside the boundary)</span><b>${la.toFixed(5)}, ${lo.toFixed(5)}</b><div class="mr-btns"><a href="#" data-copy="${la.toFixed(5)}, ${lo.toFixed(5)}">COPY GPS</a><a href="https://www.google.com/maps/search/?api=1&query=${la.toFixed(5)},${lo.toFixed(5)}" target="_blank" rel="noopener">GOOGLE MAPS ↗</a><a href="https://maps.apple.com/?ll=${la.toFixed(5)},${lo.toFixed(5)}&q=${encodeURIComponent(nm)}" target="_blank" rel="noopener">APPLE MAPS ↗</a><a href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${la.toFixed(5)},${lo.toFixed(5)}" target="_blank" rel="noopener">STREET VIEW ↗</a></div></div>
${offWeb.length ? `<div class="mr-fact"><span>OFFICIAL PAGE</span><b>${offWeb.map(u => `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(u)}</a>`).join("<br>")}</b></div>` : ""}<div class="mr-fact"><span>GRID SQUARE</span><b>${grid(la, lo)}</b></div>
<div class="mr-fact"><span>COUNTY</span><b id="mrCounty">looking it up…</b></div>
<div class="mr-fact"><span>PARKING</span><b id="mrFactsPk">looking for parking…</b></div>
<div class="mr-fact"><span>SIZE</span><b>about ${Math.round(g.acres).toLocaleString()} acres</b></div>
<div class="mr-fact"><span>OWNER · MANAGER</span><b>${esc(base.map(r => r.Loc_Own || AG[r.Own_Name] || r.Own_Name).filter((x, i, a) => a.indexOf(x) === i).join('; '))} · ${esc(locM)}</b></div>
<div class="mr-fact"><span>BOUNDARY SOURCE</span><b>${esc(g.src || 'USGS PAD-US')}</b><div class="mr-btns">${g.src && /PAD-US/.test(g.src) || !g.src ? '<a href="https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-data-overview" target="_blank" rel="noopener">ABOUT PAD-US ↗</a>' : ''}<a href="#" data-dl="kml">SAVE BOUNDARY (KML)</a></div></div>
<h4>LINKS FOUND</h4><div id="mrLinks"><p class="mr-help">Searching Wikipedia / Wikidata and OpenStreetMap for this park's links…</p></div>
<p class="mr-help">These came from the web search. The agency's own page and map are the official sources.</p></div>
<div class="mr-sec"><h3>PARK SUMMARY (COPY FOR YOUR RECORDS)</h3><textarea id="mrNote" rows="16">${esc(note)}</textarea><div class="mr-btns"><a class="gold" href="#" id="mrCopy">COPY THE SUMMARY</a><a href="${RULES_URL}" target="_blank" rel="noopener">POTA PARK-ADDITION RULES ↗</a><a href="#" id="mrWeb2">RESEARCH THE WEB FOR MORE ›</a></div><p class="mr-help">Everything above in one block: paste it into your notes or the park record.</p></div>
</section>`;
    $('mrCopy').onclick = e => { e.preventDefault(); const t = $('mrNote').value; (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(() => e.target.textContent = 'COPIED ✓').catch(() => { $('mrNote').select(); document.execCommand('copy'); e.target.textContent = 'COPIED ✓'; }); };
    draw(feats, near, la, lo);
    if (window.KPCSuggest) try { KPCSuggest.park({ g, la, lo, feats, base, own, mng, acc, locM, des: base.map(r => r.Loc_Ds || DES[r.Des_Tp] || r.Des_Tp).filter(Boolean), offWeb, verdict: verdict[1], already, rules: res.map(r => ({ v: r.v, title: r.title })), grid: grid(la, lo) }); } catch (e) {}
    $('mrOut').querySelectorAll('[data-copy]').forEach(b => b.onclick = e => { e.preventDefault(); const v = b.dataset.copy; (navigator.clipboard ? navigator.clipboard.writeText(v) : Promise.reject()).then(() => b.textContent = 'COPIED ✓').catch(() => window.prompt('Copy:', v)); });
    $('mrOut').querySelectorAll('[data-dl]').forEach(b => b.onclick = e => { e.preventDefault(); B.saveGeo({ type: 'FeatureCollection', features: feats.map(f => ({ type: 'Feature', properties: { Unit_Nm: f.properties.Unit_Nm }, geometry: f.geometry })) }, 'kml', { ref: nm.replace(/\s+/g, '_').slice(0, 40), name: nm, la, lo }, b); });
    enrich(g, la, lo);
    $('mrWeb2').onclick = e => { e.preventDefault(); notFound(g.name, g.st, ''); };
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
  /* public way in: OpenStreetMap roads / parking / trailheads / ramps that reach inside the boundary;
     parking, trailheads and ramps up to ~400 m outside are shown too (walk-in), each with a pin button */
  async function accessIn(me) {
    const [w, s, e, n] = cur.bb, pad = .005;
    const bx = `(${(s - pad).toFixed(5)},${(w - pad).toFixed(5)},${(n + pad).toFixed(5)},${(e + pad).toFixed(5)})`;
    const qy = `[out:json][timeout:40];(way[highway~"^(primary|secondary|tertiary|unclassified|residential|service|track|path|footway|bridleway)$"]["access"!~"^(private|no)$"]${bx};nwr[amenity=parking]["access"!~"^(private|no|customers)$"]${bx};node[highway=trailhead]${bx};nwr[leisure=slipway]${bx};);out tags geom 800;`;
    let j = null; for (const u of OVER) { try { j = await B.jget(u, { method: 'POST', body: 'data=' + encodeURIComponent(qy), headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }, 45000); break; } catch (e2) {} }
    if (cur !== me) return; const X = $('mrAccess'); if (!X) return;
    if (!j) throw new Error('osm');
    const inF = (a, b) => cur.feats.some(f => B.inside(a, b, f.geometry));
    const edgeKm = (a, b) => Math.min(...cur.feats.map(f => B.edge(a, b, f.geometry).km));
    const KIND = t => t.leisure === 'slipway' ? 'Boat ramp' : t.highway === 'trailhead' ? 'Trailhead' : t.amenity === 'parking' ? 'Parking' : /^(path|footway|bridleway)$/.test(t.highway) ? 'Trail' : t.highway === 'track' ? 'Dirt / gravel road' : 'Public road';
    const RANK = { 'Parking': 0, 'Trailhead': 1, 'Boat ramp': 2, 'Public road': 3, 'Dirt / gravel road': 4, 'Trail': 5 };
    const SPOT = k => k === 'Parking' || k === 'Trailhead' || k === 'Boat ramp';
    const hits = [];
    (j.elements || []).forEach(el => {
      const t = el.tags || {}; if (/^(private|no)$/.test(t.access || '')) return;
      const k = KIND(t);
      let pts = el.type === 'node' ? [[el.lat, el.lon]] : (el.geometry || []).map(p => [p.lat, p.lon]);
      if (el.type === 'relation' && el.members) el.members.forEach(m => (m.geometry || []).forEach(p => pts.push([p.lat, p.lon])));
      if (!pts.length) return;
      if (SPOT(k)) {   /* one point for a lot: its middle */
        const c = pts.length === 1 ? pts[0] : [pts.reduce((a, p) => a + p[0], 0) / pts.length, pts.reduce((a, p) => a + p[1], 0) / pts.length];
        const ins = inF(c[0], c[1]) || pts.some(p => inF(p[0], p[1])); const d = ins ? 0 : edgeKm(c[0], c[1]);
        if (!ins && d > .4) return;
        hits.push({ k, name: t.name || '', la: c[0], lo: c[1], ins, d, fee: t.fee, surf: t.surface, cap: t.capacity });
      } else { const p = pts.find(q2 => inF(q2[0], q2[1])); if (p) hits.push({ k, name: t.name || t.ref || '', la: p[0], lo: p[1], ins: true, d: 0 }); }
    });
    const seen = new Set(), H = hits.sort((a, b) => RANK[a.k] - RANK[b.k] || a.d - b.d).filter(h => { const key = h.k + '|' + (SPOT(h.k) ? h.la.toFixed(4) + h.lo.toFixed(4) : h.name || h.la.toFixed(3) + h.lo.toFixed(3)); return !seen.has(key) && seen.add(key); });
    const box = X.closest('.mr-r'), lake = box && /agency lake/.test(box.querySelector('b').textContent);
    const inH = H.filter(h => h.ins), spots = H.filter(h => SPOT(h.k));
    const drive = inH.filter(h => /Parking|Boat ramp|road/i.test(h.k)), foot = inH.filter(h => /Trail/.test(h.k)), nextTo = spots.filter(h => !h.ins);
    const ios = /iPhone|iPad|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    const dirU = h => ios ? `https://maps.apple.com/?daddr=${h.la.toFixed(6)},${h.lo.toFixed(6)}` : `https://www.google.com/maps/dir/?api=1&destination=${h.la.toFixed(6)},${h.lo.toFixed(6)}`;
    const where = h => h.ins ? 'inside the boundary' : B.dist(h.d) + ' outside the line (walk in)';
    const extra = h => [h.fee === 'yes' ? 'fee' : '', h.surf ? h.surf : '', h.cap ? h.cap + ' spaces' : ''].filter(Boolean).join(' · ');
    const ICON = { 'Parking': 'P', 'Trailhead': '🥾', 'Boat ramp': '⛵' };
    const spotRow = (h, i) => `<div class="mr-pk"><span class="mr-pki">${ICON[h.k]}</span><div><b>${esc(h.k)}${h.name ? ': ' + esc(h.name) : ''}</b><small>${esc(where(h))}${extra(h) ? ' · ' + esc(extra(h)) : ''}<br>${h.la.toFixed(5)}, ${h.lo.toFixed(5)}</small><div class="mr-rl"><a href="#" data-pk="${i}">📍 PIN IT ON THE MAP</a><a class="gold" href="${dirU(h)}" target="_blank" rel="noopener">DIRECTIONS ↗</a><a href="#" data-cp="${h.la.toFixed(6)}, ${h.lo.toFixed(6)}">COPY GPS</a></div></div></div>`;
    const roads = inH.filter(h => !SPOT(h.k));
    X.innerHTML = (inH.length ? `<p class="mr-help"><b>${drive.length ? 'YES: you can drive in.' : 'Foot access only (trail / trailhead).'}</b> OpenStreetMap shows ${inH.length} public way${inH.length === 1 ? '' : 's'} in that reach inside the boundary (volunteer map: check that it's public and not gated).</p>` : nextTo.length ? `<p class="mr-help"><b>Parking or a trailhead right next to it, but no road inside.</b> Walk-in access may be fine; make sure the walk is on public land or a public trail.</p>` : '<p class="mr-help"><b>No public road, parking, trailhead or ramp found inside the boundary on OpenStreetMap.</b> That does not prove there is none (the map can be missing them). Check the satellite and street view, and the agency\'s page for directions or an access point. If the only way in is across private land, POTA will not add it.</p>')
      + (spots.length ? `<div class="mr-pkbox"><div class="mr-k">PARKING &amp; ACCESS POINTS FOUND (${spots.length})</div>${spots.slice(0, 8).map((h, i) => spotRow(h, i)).join('')}<p class="mr-help">POTA: activating from a roadside pull-off usually puts you OUTSIDE the park. Park, then walk in past the boundary line.</p></div>` : '')
      + (roads.length ? `<details class="mr-rec"><summary>ROADS / TRAILS INTO IT (${roads.length})</summary><table>${roads.slice(0, 10).map(h => `<tr><th>${esc(h.k)}</th><td>${esc(h.name || '(no name)')} · <a href="https://www.google.com/maps/search/?api=1&query=${h.la.toFixed(5)},${h.lo.toFixed(5)}" target="_blank" rel="noopener">${h.la.toFixed(5)}, ${h.lo.toFixed(5)} ↗</a></td></tr>`).join('')}</table></details>` : '');
    const top = spots.slice(0, 8);
    X.querySelectorAll('[data-pk]').forEach(a => a.onclick = ev => { ev.preventDefault(); const h = top[+a.dataset.pk]; if (!map) return; const M = $('mrMap'); if (M) M.scrollIntoView({ behavior: 'smooth', block: 'center' }); map.setView([h.la, h.lo], 17); map.fire('click', { latlng: L.latLng(h.la, h.lo) }); });
    X.querySelectorAll('[data-cp]').forEach(a => a.onclick = ev => { ev.preventDefault(); const v = a.dataset.cp; (navigator.clipboard ? navigator.clipboard.writeText(v) : Promise.reject()).then(() => a.textContent = 'COPIED ✓').catch(() => window.prompt('Copy the GPS:', v)); });
    if (map) {
      top.forEach(h => L.marker([h.la, h.lo], { icon: L.divIcon({ className: 'mr-pkm', html: `<span>${ICON[h.k]}</span>`, iconSize: [26, 26], iconAnchor: [13, 13] }) }).addTo(map).bindPopup(`<b>${esc(h.k)}${h.name ? ': ' + esc(h.name) : ''}</b><br>${esc(where(h))}<br>${h.la.toFixed(5)}, ${h.lo.toFixed(5)}<br><a href="${dirU(h)}" target="_blank" rel="noopener">DIRECTIONS ↗</a> · <a href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${h.la.toFixed(6)},${h.lo.toFixed(6)}" target="_blank" rel="noopener">STREET VIEW ↗</a><br><small>From OpenStreetMap</small>`));
      roads.slice(0, 10).forEach(h => L.circleMarker([h.la, h.lo], { radius: 5, color: '#fff', weight: 2, fillColor: '#18a957', fillOpacity: 1 }).addTo(map).bindPopup(`<b>${esc(h.k)}</b> ${esc(h.name)}<br>Way in (OpenStreetMap)`));
    }
    const T = $('mrNote');
    if (T && spots.length) T.value = T.value.replace('Links found:', 'Parking / access points (OpenStreetMap):\n' + spots.slice(0, 5).map(h => `- ${h.k}${h.name ? ' ' + h.name : ''}: ${h.la.toFixed(5)}, ${h.lo.toFixed(5)} (${where(h)})`).join('\n') + '\nLinks found:');
    if (box && !lake && drive.length + foot.length) {
      box.className = 'mr-r yes'; box.querySelector('i').textContent = 'YES';
      if (T) T.value = T.value.replace('Has a public way in (road, trail or water): CHECK', 'Has a public way in (road, trail or water): YES (OpenStreetMap: ' + inH.slice(0, 3).map(h => h.k + (h.name ? ' ' + h.name : '') + ' at ' + h.la.toFixed(5) + ', ' + h.lo.toFixed(5)).join('; ') + ')');
      const yes = document.querySelectorAll('.mr-r.yes').length, no = document.querySelectorAll('.mr-r.no').length, ck = document.querySelectorAll('.mr-r.check').length;
      const V = document.querySelector('.mr-v'); if (V && !/ALREADY|CORPS/.test(V.textContent)) { V.className = 'mr-v ' + (no ? 'no' : ck ? 'maybe' : 'yes'); V.querySelector('b').textContent = no ? 'LIKELY NOT ELIGIBLE' : ck ? 'LOOKS POSSIBLE: CONFIRM THE YELLOW ITEMS' : 'LOOKS ELIGIBLE'; V.querySelector('span').textContent = `${yes} yes · ${no} no · ${ck} to check yourself`; }
    }
    const FB = $('mrFactsPk'); if (FB) FB.innerHTML = spots.length ? `${esc(spots[0].k)}${spots[0].name ? ' ' + esc(spots[0].name) : ''}: ${spots[0].la.toFixed(5)}, ${spots[0].lo.toFixed(5)} <a href="${dirU(spots[0])}" target="_blank" rel="noopener">directions ↗</a>${spots.length > 1 ? ` (+${spots.length - 1} more under the access rule)` : ''}` : 'none found on OpenStreetMap';
  }
  /* county (FCC census area) + links from the web, filled into the facts box and the note */
  async function enrich(g, la, lo) {
    const me = cur;
    const setNote = (k, v) => { const t = $('mrNote'); if (t) t.value = t.value.replace(k, v); };
    B.jget(`https://geo.fcc.gov/api/census/area?lat=${la}&lon=${lo}&censusYear=2020&format=json`, null, 15000).then(j => { const r = (j.results || [])[0]; const c = r ? r.county_name + ', ' + r.state_code : 'not found'; if (cur !== me) return; $('mrCounty').textContent = c; setNote('@@COUNTY@@', c); }).catch(() => { if (cur === me) { $('mrCounty').textContent = 'could not look it up'; setNote('@@COUNTY@@', '(check)'); } });
    let R = { hits: [] }; try { R = await webResearch(g.name, g.st, ''); } catch (e) {}
    if (cur !== me) return;
    const near = R.hits.filter(h => B.km(h.la, h.lo, la, lo) < 15 && (B.sameName(h.name, g.name) || B.km(h.la, h.lo, la, lo) < 3));
    const links = [];
    near.forEach(h => { if (h.web) links.push(['Website listed (' + h.src + ')', h.web]); if (h.wiki) links.push(['Wikipedia', h.wiki]); if (h.item) links.push(['Wikidata', h.item]); });
    links.push(['OpenStreetMap at the pin', `https://www.openstreetmap.org/?mlat=${la.toFixed(5)}&mlon=${lo.toFixed(5)}#map=15/${la.toFixed(5)}/${lo.toFixed(5)}`]);
    const seen = new Set(), L = links.filter(x => !seen.has(x[1]) && seen.add(x[1]));
    const info = near.filter(h => h.operator || h.owner || h.what).slice(0, 3).map(h => `<p class="mr-help"><b>${esc(h.name)}</b> (${esc(h.src)}): ${esc([h.what, h.operator ? 'run by ' + h.operator : '', h.owner ? 'owned by ' + h.owner : ''].filter(Boolean).join(' · '))}</p>`).join('');
    $('mrLinks').innerHTML = `<div class="mr-links">${L.map(x => `<a href="${esc(x[1])}" target="_blank" rel="noopener"><b>${esc(x[0])}</b><span>${esc(x[1])}</span></a>`).join('')}</div>${info}`;
    setNote('@@LINKS@@', L.map(x => `- ${x[0]}: ${x[1]}`).join('\n'));
    q({ geometry: `${cur.bb[0] - .01},${cur.bb[1] - .01},${cur.bb[2] + .01},${cur.bb[3] + .01}`, geometryType: 'esriGeometryEnvelope', inSR: 4326, spatialRel: 'esriSpatialRelIntersects', where: '1=1', resultRecordCount: 30 }).then(rows => {
      if (cur !== me) return; const A = $('mrAround'); if (!A) return;
      const other = rows.filter(r => !B.sameName(r.Unit_Nm || '', g.name));
      A.innerHTML = `<details class="mr-rec"><summary>OFFICIAL LAND AROUND IT: ${other.length} RECORD${other.length === 1 ? '' : 'S'}</summary><table>${other.map(x => `<tr><th>${esc(x.Unit_Nm || x.Loc_Nm || '?')}</th><td>${esc([x.Loc_Mang, TYPE[x.Own_Type] || x.Own_Type, ACC[x.Pub_Access] || '', x.GIS_Acres ? Math.round(+x.GIS_Acres).toLocaleString() + ' acres' : ''].filter(Boolean).join(' · '))}</td></tr>`).join('') || '<tr><td>No other public land touches it in the database, so the neighbours are probably private. That is fine if a public road, trail or ramp gets you in (see above).</td></tr>'}</table></details>`;
    }).catch(() => { const A = $('mrAround'); if (A) A.textContent = ''; });
    accessIn(me).catch(() => { const X = $('mrAccess'); if (X && cur === me) X.innerHTML = '<p class="mr-help">Could not check OpenStreetMap for a way in right now. Use the satellite and street view buttons.</p>'; });
    const W = $('mrWebRule'); if (W && !W.closest('.mr-r').classList.contains('yes')) {
      const sites = [...new Set(near.map(h => h.web).filter(Boolean))];
      const dom = u => { try { return new URL(u).hostname.replace(/^www\./, ''); } catch (e) { return ''; } };
      const gov = sites.filter(u => /\.(gov|us)$|\.gov\//.test(dom(u)));
      W.innerHTML = sites.length ? sites.map(u => `<a class="${gov.includes(u) ? 'gold' : ''}" href="${esc(u)}" target="_blank" rel="noopener">${gov.includes(u) ? 'OFFICIAL PAGE' : 'WEBSITE LISTED'}: ${esc(dom(u))} ↗</a>`).join('') + [...new Set(sites.map(dom).filter(Boolean))].map(d => `<a href="https://www.google.com/search?q=${encodeURIComponent('site:' + d + ' "' + g.name + '" map')}" target="_blank" rel="noopener">MAPS ON ${esc(d.toUpperCase())} ↗</a>`).join('') : '<span class="mr-help">No website found on the web; use the search buttons.</span>';
    }
  }
  $('mrForm').addEventListener('submit', e => { e.preventDefault(); search(); });
  /* simple password lock (keeps casual visitors out; it is not bank-grade security on a public website) */
  const HASH = 'b36efa5ab2718f715ea105ece66b600d914fb0be36ee52de48363e5727d92b73';
  const sha = async t => { const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(t)); return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join(''); };
  function start() {
    if ($('mrLock')) $('mrLock').hidden = true; $('mrApp').hidden = false;
    if ($('mrState').value) agencies($('mrState').value);
    const P = new URLSearchParams(location.search);
    if (P.get('name')) { $('mrName').value = P.get('name'); if (P.get('town')) $('mrTown').value = P.get('town'); if (P.get('state')) { $('mrState').value = P.get('state').toUpperCase(); agencies($('mrState').value); } search(); }
  }
  let ok = !!$('mrPublic'); /* the public Suggest page uses the same engine with no password */
  if (!ok) try { ok = localStorage.getItem('kpcMrOK') === HASH; } catch (e) {}
  if (ok) start();
  else $('mrLockForm').addEventListener('submit', async e => {
    e.preventDefault();
    const h = await sha('kpc-maprep:' + $('mrPw').value.trim().toLowerCase());
    if (h === HASH) { try { localStorage.setItem('kpcMrOK', HASH); } catch (x) {} start(); }
    else { $('mrPwMsg').textContent = 'That password is not right.'; $('mrPw').select(); }
  });
})();
