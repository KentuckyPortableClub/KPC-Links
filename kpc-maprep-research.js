/* Mapping Rep Tool Box: FIND AND TEST NEW PARKS (Nov 8 2026, Brandon 11:19 AM CST: "the MAIN reason for this tool is for mapping
   reps to research and find new parks to add ... make the tool a tool ... run the checks and provide info").
   For a picked state or province it lists official protected land (USGS PAD-US for a US state, Canada's CPCAD for a province)
   and checks every place by itself:
     - is it already a POTA park? the same official record in our answer key, a park outline from the key over it, a POTA pin
       inside it, or a POTA park with the same name close by (not pins alone)
     - the nearest POTA park and how far, and any overlap with a park outline (part of a park, or a 2-fer)
     - the full official record (name, manager, owner, designation, GAP / IUCN, public access, acres, record id and link)
   and gives a plain verdict (possible candidate / probably already a park / needs a person) with a summary to copy for a submission.
   A rep can also test a place they found themselves (a name, or a tap on the map).
   Requests: only the two official services the Tool Box already reads in the browser (edits.nationalmap.gov PAD-US,
   maps-cartes.ec.gc.ca CPCAD), and this site's own files (answer keys, POTA list). Nothing is written. */
(function () {
  'use strict';
  const W = typeof window !== 'undefined' ? window : globalThis, D = typeof document !== 'undefined' ? document : null;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const PADUS_LAYER = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0';
  const CPCAD_LAYER = 'https://maps-cartes.ec.gc.ca/arcgis/rest/services/CWS_SCF/CPCAD/MapServer/0';
  const BANNED = /ncnhde\.natureserve\.org|services\.arcgis\.com\/33TOOklri9xpic7U/i;
  const PAD_FIELDS = 'OBJECTID,Unit_Nm,Loc_Nm,Mang_Name,Mang_Type,Own_Name,Own_Type,Loc_Own,Loc_Mang,Des_Tp,Loc_Ds,GIS_Acres,Source_PAID,State_Nm,Pub_Access,Category,GAP_Sts,IUCN_Cat,Date_Est,Comments,Agg_Src,GIS_Src,Src_Date';
  const CP_FIELDS = 'OBJECTID,NAME_E,NAME_IND,PA_OECM_DF,IUCN_CAT,STATUS,QUALYEAR,ESTYEAR,BIOME,LOC,O_AREA_HA,PARENT_ID,ZONE_ID,ZONEDESC_E,MECH_E,TYPE_E,OWNER_TYPE,OWNER_E,GOV_TYPE,MGMT_E,JUR_ID';
  const CP_LOC = { AB: 1, BC: 2, MB: 3, NB: 4, NL: 5, NT: 6, NS: 7, NU: 8, ON: 9, PE: 10, QC: 11, SK: 12, YT: 13 };
  const CA_CODES = Object.keys(CP_LOC);
  const MAX_PLACES = 150, NAME_KM = 30, NEAR_PIN_KM = 60;

  /* ---------- pure logic (tested in tests/test_maprep_research_nov8.py with node) ---------- */
  const norm = s => String(s || '').toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '').replace(/&/g, ' and ')
    .replace(/\b(state|national|provincial|park|parks|forest|wildlife|management|area|recreation|recreational|conservation|nature|natural|preserve|reserve|refuge|historic|historical|site|game|lands?|unit|wma|nwr|sp|sf|the|of|and|at|de|du|la|le)\b/g, ' ')
    .replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim();
  const toks = s => [...new Set(norm(s).split(' ').filter(Boolean))];
  const nameKey = s => toks(s).sort().join(' ');
  function sameName(a, b) {   /* the same words (any order), or one name's words all inside the other's (at least half of them) */
    const A = toks(a), B = toks(b); if (!A.length || !B.length) return false;
    const S = A.length <= B.length ? A : B, L = A.length <= B.length ? B : A;
    return S.every(w => L.indexOf(w) >= 0) && S.join('').length > 4 && S.length / L.length >= 0.5;
  }
  function kmBetween(a, b, c, d) { const r = Math.PI / 180, x = (d - b) * r * Math.cos((a + c) / 2 * r), y = (c - a) * r; return Math.sqrt(x * x + y * y) * 6371; }
  function ringsOf(g) { if (!g) return []; if (g.type === 'Polygon') return [g.coordinates]; if (g.type === 'MultiPolygon') return g.coordinates; return []; }
  function inRing(x, y, ring) { let c = false; for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) { const a = ring[i], b = ring[j]; if (((a[1] > y) !== (b[1] > y)) && (x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0])) c = !c; } return c; }
  function inside(la, lo, g) { for (const p of ringsOf(g)) { if (p.length && inRing(lo, la, p[0]) && !p.slice(1).some(h => inRing(lo, la, h))) return true; } return false; }
  function bbox(g) { let a = 180, b = 90, c = -180, d = -90; ringsOf(g).forEach(p => (p[0] || []).forEach(q => { if (q[0] < a) a = q[0]; if (q[0] > c) c = q[0]; if (q[1] < b) b = q[1]; if (q[1] > d) d = q[1]; })); return a <= c ? [a, b, c, d] : null; }
  /* sample points spread over the place (a 9 x 9 grid inside its box, kept when inside the land) */
  function samples(g, n) {
    const bb = bbox(g); if (!bb) return []; n = n || 9; const out = [];
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) { const lo = bb[0] + (bb[2] - bb[0]) * (i + .5) / n, la = bb[1] + (bb[3] - bb[1]) * (j + .5) / n; if (inside(la, lo, g)) out.push([la, lo]); }
    if (!out.length) { const r = ringsOf(g)[0]; if (r && r[0] && r[0][0]) out.push([r[0][0][1], r[0][0][0]]); }
    return out;
  }
  /* share of the place covered by other outlines (0..1) */
  function coverShare(g, others) { const pts = samples(g); if (!pts.length || !others.length) return 0; return pts.filter(p => others.some(o => inside(p[0], p[1], o))).length / pts.length; }
  function nearestKm(g, la, lo) {   /* pin to the nearest corner of the land (0 inside); rough, for "nearest park" */
    if (inside(la, lo, g)) return 0; let best = 1e9;
    ringsOf(g).forEach(p => (p[0] || []).forEach((q, i) => { if (i % 3 === 0) best = Math.min(best, kmBetween(la, lo, q[1], q[0])); })); return best;
  }
  /* one verdict per place. c: {acc, cat, own, same:[refs], cover:[{ref,share}], pinIn:[refs], named:[{ref,km}], nearest:{ref,km}} */
  function verdict(c) {
    const cv = (c.cover || []).slice().sort((a, b) => b.share - a.share), top = cv[0];
    const pct = x => Math.round(x * 100) + '%';
    if ((c.same || []).length) return { v: 'already', label: 'Already a POTA park', why: (c.same.join(', ')) + ' is joined to this same official record in our answer key.' };
    if (top && top.share >= 0.5 && top.same) return { v: 'already', label: 'Already a POTA park', why: top.ref + ' (same name) has an official outline over ' + pct(top.share) + ' of this land.' };
    if (top && top.share >= 0.9) return { v: 'person', label: 'Inside ' + top.ref + ': possible 2-fer', why: 'This land sits inside ' + top.ref + '\u2019s official outline (' + pct(top.share) + '), under its own name and record. A separately designated area inside a park can be a park of its own (a 2-fer). Check that it is designated separately before you submit it.' };
    if (top && top.share >= 0.5) return { v: 'probably', label: 'Probably part of ' + top.ref, why: top.ref + '\u2019s official outline covers ' + pct(top.share) + ' of this land. It is probably part of that park; check the agency map.' };
    if ((c.named || []).length) return { v: 'probably', label: 'Probably already a park (' + c.named[0].ref + ')', why: c.named[0].ref + ' has the same name, ' + c.named[0].km.toFixed(1) + ' km away. Check that it is the same land.' };
    if ((c.pinIn || []).length) return { v: 'probably', label: 'Probably already a park (' + c.pinIn[0] + ')', why: c.pinIn[0] + '\u2019s POTA pin is inside this land, under another name.' };
    const notes = [];
    if (top && top.share >= 0.05) notes.push('Overlaps ' + top.ref + ' (' + pct(top.share) + ' of this land): it may be part of that park, or a 2-fer');
    if (c.acc && c.acc !== 'open') notes.push('Public access is ' + c.acc);
    if (c.cat && /easement/i.test(c.cat)) notes.push('It is an easement, not land the agency owns');
    if (c.own && /private/i.test(c.own)) notes.push('The owner is private');
    if (notes.length) return { v: 'person', label: 'Needs a person', why: notes.join('. ') + '.' };
    return { v: 'new', label: 'Possible candidate', why: 'No POTA park on this official record, no park outline over it, no POTA pin inside it, no park with this name nearby.' + (c.nearest ? ' Nearest POTA park: ' + c.nearest.ref + ', ' + c.nearest.km.toFixed(1) + ' km.' : '') };
  }
  const RANK = { new: 0, person: 1, probably: 2, already: 3 };
  /* group the official records into places (the same name + manager = one place, acres added up) */
  function groupRecords(recs) {
    const m = new Map();
    recs.forEach(r => { const k = norm(r.name) + '|' + (r.manager || ''); const g = m.get(k) || Object.assign({}, r, { ids: [], acres: 0, geoms: [] }); g.ids.push(r.id); g.acres += +r.acres || 0; if (r.geom) g.geoms.push(r.geom); m.set(k, g); });
    return [...m.values()].sort((a, b) => b.acres - a.acres);
  }
  function summaryText(p) {
    const L = [];
    L.push('Proposed park: ' + p.name);
    if (p.place) L.push('Where: ' + p.place + (p.pt ? ' (about ' + p.pt[0].toFixed(5) + ', ' + p.pt[1].toFixed(5) + ')' : ''));
    if (p.designation) L.push('Designation: ' + p.designation);
    L.push('Managed by: ' + (p.manager && !/^unknown$/i.test(p.manager) ? p.manager : 'not stated in the record (ask the owner)'));
    if (p.owner) L.push('Owned by: ' + p.owner);
    if (p.access) L.push('Public access: ' + p.access);
    if (p.protection) L.push('Protection: ' + p.protection);
    if (p.acres) L.push('Size: about ' + Math.round(p.acres).toLocaleString('en-US') + ' acres');
    L.push('Official record: ' + p.source + (p.ids && p.ids.length ? ', id ' + p.ids.join(', ') : ''));
    factRows(p).filter(r => r.vals.some(x => x.src !== p.source) || p.kind === 'state').forEach(r => L.push(r.label + ': ' + r.vals.map(x => x.v + ' (' + x.src + ')').join('; ') + (r.differ ? ' [sources differ]' : '')));
    (p.also || []).forEach(x => L.push('Also in: ' + x.source + (x.name && norm(x.name) !== norm(p.name) ? ' (' + x.name + ')' : '') + (x.link ? ', ' + x.link : '')));
    if (p.link) L.push('Record link: ' + p.link);
    L.push('POTA check: ' + p.verdict.label + '. ' + p.verdict.why);
    L.push('Checked with the KPC Mapping Rep Tool Box. Confirm with the managing agency before you submit.');
    return L.join('\n');
  }
  const pair = (m, k) => { if (!m || k == null) return ''; if (Array.isArray(m)) { const h = m.find(x => x[0] === String(k)); return h ? h[1] : ''; } return m[String(k)] || ''; };

  /* ---------- reading the official records ---------- */
  async function arc(base, params, ms) {
    if (BANNED.test(base)) throw new Error('not an allowed source');
    const c = new AbortController(), t = setTimeout(() => c.abort(), ms || 30000);
    try { const r = await fetch(base + '/query?' + new URLSearchParams(Object.assign({ f: 'geojson', outSR: 4326 }, params)), { signal: c.signal }); if (!r.ok) throw new Error('HTTP ' + r.status); const j = await r.json(); if (j.error) throw new Error(j.error.message || 'query error'); return j; }
    finally { clearTimeout(t); }
  }
  function padRec(f) {
    const a = f.properties || {}, X = (W.KPCMapExtras && W.KPCMapExtras.PAD) || {};
    const acc = { OA: 'open', RA: 'restricted', XA: 'closed', UK: 'unknown' }[a.Pub_Access] || 'unknown';
    return { kind: 'pad', a, id: a.OBJECTID, name: a.Unit_Nm || a.Loc_Nm || 'Public land', manager: [a.Loc_Mang, pair(X.name, a.Mang_Name), a.Mang_Name].find(x => x && String(x).trim() && !/^(unk|unknown)$/i.test(String(x).trim())) || '',
      owner: (a.Loc_Own || pair(X.name, a.Own_Name) || a.Own_Name || '') + (a.Own_Type ? ' (' + (pair(X.type, a.Own_Type) || a.Own_Type) + ')' : ''),
      designation: (a.Loc_Ds && String(a.Loc_Ds).length > 4 ? a.Loc_Ds : pair(X.des, a.Des_Tp) || a.Loc_Ds || a.Des_Tp || ''), acc, cat: a.Category || '', acres: +a.GIS_Acres || 0,
      protection: [a.GAP_Sts ? 'GAP ' + a.GAP_Sts + (pair(X.gap, a.GAP_Sts) ? ' (' + pair(X.gap, a.GAP_Sts) + ')' : '') : '', a.IUCN_Cat && !/^(other|unassigned|n\/?a)/i.test(a.IUCN_Cat) ? 'IUCN ' + a.IUCN_Cat : ''].filter(Boolean).join(', '),
      access: { open: 'open', restricted: 'restricted', closed: 'closed', unknown: 'not stated' }[acc], geom: f.geometry,
      source: 'USGS PAD-US 4.0', link: PADUS_LAYER + '/query?where=OBJECTID%3D' + a.OBJECTID + '&outFields=*&f=html' };
  }
  function caRec(f) {
    const a = f.properties || {}, X = (W.KPCMapExtras && W.KPCMapExtras.CP) || {};
    const own = pair(X.own, a.OWNER_TYPE) || '';
    return { kind: 'ca', a, id: a.OBJECTID, name: a.NAME_E || 'Protected area', manager: a.MGMT_E || '', owner: (a.OWNER_E || '') + (own ? ' (' + own + ')' : ''),
      designation: a.TYPE_E || '', acc: 'unknown', cat: '', acres: (+a.O_AREA_HA || 0) * 2.47105, access: 'not stated in CPCAD (check the agency)',
      protection: a.IUCN_CAT ? 'IUCN ' + (pair(X.iucn, a.IUCN_CAT) || a.IUCN_CAT) : '', geom: f.geometry,
      source: 'CPCAD, December 2025 edition', link: CPCAD_LAYER + '/query?where=OBJECTID%3D' + a.OBJECTID + '&outFields=*&f=html' };
  }
  const PARKLIKE_NOT = /^(MIL|AGRE|FOTH|PROC|ACC|UNK|RECE|HCA|REA)$/i;   /* military, ag easements, "other", proclamation lines, access areas, unknown, recreation easements, habitat easements */
  async function statewide(code, say) {
    if (CP_LOC[code]) {
      say('Reading Canada\u2019s CPCAD for ' + code + '\u2026');
      const j = await arc(CPCAD_LAYER, { where: 'LOC = ' + CP_LOC[code] + ' AND O_AREA_HA >= 8', outFields: CP_FIELDS, orderByFields: 'O_AREA_HA DESC', resultRecordCount: 400, returnGeometry: false }, 40000);
      return (j.features || []).map(caRec);
    }
    say('Reading USGS PAD-US for ' + code + ' (public land, open to the public, 20 acres or more)\u2026');
    const j = await arc(PADUS_LAYER, { where: "State_Nm = '" + code + "' AND Pub_Access = 'OA' AND Category = 'Fee' AND GIS_Acres >= 20", outFields: PAD_FIELDS, orderByFields: 'GIS_Acres DESC', resultRecordCount: 2000, returnGeometry: false }, 45000);
    return (j.features || []).map(padRec).filter(r => !PARKLIKE_NOT.test(String(r.a.Des_Tp || '')));
  }
  async function shapes(code, ids) {
    const out = {}, base = CP_LOC[code] ? CPCAD_LAYER : PADUS_LAYER;
    for (let i = 0; i < ids.length; i += 40) {
      try { const j = await arc(base, { objectIds: ids.slice(i, i + 40).join(','), outFields: 'OBJECTID', returnGeometry: true, maxAllowableOffset: 0.0008, geometryPrecision: 5 }, 40000);
        (j.features || []).forEach(f => { const id = (f.properties || {}).OBJECTID != null ? f.properties.OBJECTID : f.id; if (f.geometry) out[id] = f.geometry; }); } catch (e) {}
    }
    return out;
  }
  async function near(code, la, lo, km) {
    const d = (km || 8) / 111, dx = d / Math.max(0.2, Math.cos(la * Math.PI / 180));
    const env = { geometry: [lo - dx, la - d, lo + dx, la + d].join(','), geometryType: 'esriGeometryEnvelope', inSR: 4326, spatialRel: 'esriSpatialRelIntersects', returnGeometry: true, maxAllowableOffset: 0.0005, geometryPrecision: 5 };
    if (CP_LOC[code]) { const j = await arc(CPCAD_LAYER, Object.assign({ where: '1=1', outFields: CP_FIELDS }, env)); return (j.features || []).map(caRec); }
    const j = await arc(PADUS_LAYER, Object.assign({ where: "Category <> 'Proclamation'", outFields: PAD_FIELDS }, env));
    return (j.features || []).map(padRec);
  }
  async function byName(code, name) {
    const w = norm(name).split(' ').filter(x => x.length > 2).slice(0, 2); if (!w.length) return [];
    const pat = w.map(x => x.charAt(0).toUpperCase() + x.slice(1)).join('%').replace(/'/g, '%');
    if (CP_LOC[code]) { const j = await arc(CPCAD_LAYER, { where: "LOC = " + CP_LOC[code] + " AND NAME_E LIKE '%" + pat + "%'", outFields: CP_FIELDS, returnGeometry: true, maxAllowableOffset: 0.0005, geometryPrecision: 5 }); return (j.features || []).map(caRec); }
    const j = await arc(PADUS_LAYER, { where: "State_Nm = '" + code + "' AND Unit_Nm LIKE '%" + pat + "%'", outFields: PAD_FIELDS, returnGeometry: true, maxAllowableOffset: 0.0005, geometryPrecision: 5 });
    return (j.features || []).map(padRec);
  }

  /* ---------- our own files: answer key and the POTA list ---------- */
  const jget = p => (W.KPCB && W.KPCB.dget ? W.KPCB.dget(p) : fetch(p).then(r => r.ok ? r.json() : null)).catch(() => null);
  const keyP = {};
  function keyFile(code) { const p = CP_LOC[code] ? 'data/ca-key/CA-' + code + '.json' : 'data/us-key/US-' + code + '.json'; return keyP[p] = keyP[p] || jget(p + '?v=' + new Date().toISOString().slice(0, 10)); }
  let pinsP = null;
  function pins() { return pinsP = pinsP || (W.KPCB && W.KPCB.jget ? W.KPCB.jget('locations.json') : fetch('locations.json').then(r => r.json())).then(r => (r || []).filter(x => x && x[0] === 'POTA' && x[3] != null).map(x => ({ ref: x[1], name: x[2], la: +x[3], lo: +x[4] }))).catch(() => []); }
  const outlineP = {};
  /* Nov 8 (Brandon t760u, "Iowa gets stuck on last step"): every wait has a time limit, so one slow server can never hang a step */
  function within(pr, ms, fb) { let t; return Promise.race([Promise.resolve(pr).catch(() => fb), new Promise(r => { t = setTimeout(() => r(fb), ms); })]).finally(() => clearTimeout(t)); }
  const tick = () => new Promise(r => setTimeout(r, 0));   /* let the phone draw between places */
  /* the POTA parks whose key outline is worth comparing with this place (pins near its box, key graded official/approximate) */
  function candRefs(p, ctx) {
    const box = p.geoms.map(bbox).filter(Boolean).reduce((a, b) => a ? [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])] : b, null);
    if (!box || !p.geoms.length) return [];
    const pad = NEAR_PIN_KM / 80;
    return ctx.pins.filter(q => q.la >= box[1] - pad && q.la <= box[3] + pad && q.lo >= box[0] - pad * 1.3 && q.lo <= box[2] + pad * 1.3)
      .filter(q => { const k = ctx.key[q.ref]; return k && k.g && k.g !== 'pin' && (k.m || []).length; }).map(q => q.ref);
  }
  /* Load every key outline the whole search needs up front, in a few batched requests (not one live lookup per park per place).
     A key outline made only of PAD-US records already loaded for this search is used straight from memory. */
  async function prefetchOutlines(places, code, ctx, prog) {
    const refs = [...new Set(places.flatMap(p => p.ids.concat(p.xids || []).some(id => (ctx.rev[String(id)] || []).length) ? [] : candRefs(p, ctx)))].filter(r => !(r in outlineP));
    if (!refs.length) return 0;
    const have = {}; places.forEach(p => p.ids.forEach((id, i) => { if (p.geoms[i]) have[String(id)] = p.geoms[i]; }));
    /* every key record id, grouped by source: PAD-US (plain number) or another agency's layer (prefix + number) */
    const X = (W.KPCB && W.KPCB.usKeyLayers && !CP_LOC[code]) ? await within(W.KPCB.usKeyLayers(), 15000, {}) : {};
    const plain = [], other = [], want = {};
    refs.forEach(r => {
      const ids = (ctx.key[r].m || []).map(x => String(x[0])), pre = id => (id.match(/^[a-z]+/) || [''])[0];
      if (CP_LOC[code] || ids.some(id => pre(id) && !(X[pre(id)] && /^https:/.test(X[pre(id)][0]) && !BANNED.test(X[pre(id)][0]) && !isSavedCopy({ url: X[pre(id)][0] })))) { other.push(r); return; }   /* Nov 11 (job 3): a saved-copy-only host is never asked by id */
      plain.push(r); (ctx.key[r].m || []).forEach(x => { const id = String(x[0]), a = +x[2] || 0, off = a < 20000 ? 0.00004 : a < 200000 ? 0.00015 : a < 1000000 ? 0.0003 : 0.0008;   /* same detail as the map draws (kpc-bounds usKey) */
        if (!have[id]) (want[pre(id) + '|' + off] = want[pre(id) + '|' + off] || new Set()).add(id.slice(pre(id).length)); });
    });
    const jobs = [];
    Object.entries(want).forEach(([pk, set]) => { const list = [...set], pf = pk.split('|')[0], off = +pk.split('|')[1];
      for (let i = 0; i < list.length; i += 40) { const ids = list.slice(i, i + 40);
        const q = () => pf ? within(fetch(X[pf][0] + '?' + new URLSearchParams({ objectIds: ids.join(','), outFields: '*', returnGeometry: true, outSR: 4326, maxAllowableOffset: off, geometryPrecision: 5, f: 'geojson' })).then(r => r.json()), 20000, { features: [] })
          : within(arc(PADUS_LAYER, { objectIds: ids.join(','), outFields: 'OBJECTID', returnGeometry: true, maxAllowableOffset: off, geometryPrecision: 5 }, 20000), 22000, { features: [] });
        jobs.push(() => q().then(j => ((j && j.features) || []).forEach(f => { const a = f.properties || {}, id = [f.id, a.OBJECTID, a.objectid, a.ObjectID, a.OBJECTID_1, a.FID].find(v => v != null); if (f.geometry && id != null) have[pf + id] = f.geometry; })).catch(() => {})); } });
    other.forEach(r => jobs.push(() => outline(r, code)));
    const total = jobs.length; let k = 0, done = 0;
    await within(Promise.all(Array.from({ length: Math.min(4, total) }, async () => { while (k < jobs.length) { const j = jobs[k++]; await j(); done++; if (prog) prog(done, total); } })), 60000, null);
    plain.forEach(r => { const tw = new Set((ctx.key[r].twin || []).map(String)); outlineP[r] = Promise.resolve(ctx.key[r].m.map(x => String(x[0])).filter(id => !tw.has(id)).map(id => have[id]).filter(g => g && /Polygon/.test(g.type))); });
    return refs.length;
  }
  async function outline(ref, code) {
    if (!(ref in outlineP)) outlineP[ref] = within((async () => {
      try {
        if (CP_LOC[code] && W.KPCB && W.KPCB.canada) { const k = await W.KPCB.canada(ref); return ((k && k.fs) || []).map(f => f.geometry).filter(Boolean); }
        if (W.KPCB && W.KPCB.usKey) { const k = await W.KPCB.usKey(ref, [code]); return k && k.state === 'ok' ? (k.fs || []).map(f => f.geometry).filter(g => g && /Polygon/.test(g.type)) : []; }
      } catch (e) {}
      return [];
    })(), 12000, []);
    return outlineP[ref];
  }
  /* ---------- state / province layers next to PAD-US / CPCAD ----------
     data/maprep-state-layers.json (built by hand with .github/scripts/kpc_maprep_state_layers.py) lists the layers the answer keys use for
     each state or province, with only the ones this tool is set up to query live (ok: true). Kentucky is the model:
     every place from every source gets the same checks. Each layer is one query, at most 4 at a time, each with a time limit.
     Hosts that may be used only as a saved copy (services.arcgis.com, services1.arcgis.com, apps.fs.usda.gov) are labelled
     saved copy and are never queried live. */
  const FACT_KEYS = ['owner', 'manager', 'agency', 'designation', 'acres', 'website'];
  let SLP = null;
  function stateLayers(code) { SLP = SLP || within(jget('data/maprep-state-layers.json?v=' + new Date().toISOString().slice(0, 10)), 15000, null).then(j => (j && j.areas) || {});
    return SLP.then(A => (A[code] || [])); }
  const capName = v => { v = String(v || '').replace(/\s+/g, ' ').trim(); return /[a-z]/.test(v) ? v : v.toLowerCase().replace(/(^|[\s\-\/(.])([a-z])/g, (m, a, b) => a + b.toUpperCase()); };
  function geomAcres(g) { let a = 0; ringsOf(g).forEach(p => p.forEach((r, k) => { let s2 = 0; for (let i = 0, j = r.length - 1; i < r.length; j = i++) s2 += (r[j][0] - r[i][0]) * (r[j][1] + r[i][1]);
    const la = r.length ? r[0][1] : 0; const km2 = Math.abs(s2 / 2) * 111.32 * 111.32 * Math.cos(la * Math.PI / 180); a += (k ? -1 : 1) * km2 * 247.105; })); return Math.max(0, a); }
  function slRec(L, f) {
    const a = f.properties || {}, id = [f.id, a.OBJECTID, a.objectid, a.ObjectID, a.OBJECTID_1, a.FID].find(v => v != null);
    /* the layer's own owner / manager / agency / designation / acres / website fields (data/maprep-state-layers.json 'facts') */
    const F = L.facts || {}, facts = {};
    FACT_KEYS.forEach(k => { const fl = F[k], v = fl != null && a[fl] != null ? String(a[fl]).trim() : ''; if (v && !/^(null|none|n\/?a|unknown|unk|-|0)$/i.test(v)) facts[k] = { v, src: L.label, field: fl }; });
    if (!facts.manager && facts.agency) facts.manager = Object.assign({}, facts.agency);
    const ac = facts.acres ? parseFloat(String(facts.acres.v).replace(/,/g, '')) : NaN;
    return { kind: 'state', a, facts, id: L.pre + id, name: capName(a[L.field]) || L.label, manager: facts.manager ? facts.manager.v : L.label, owner: facts.owner ? facts.owner.v : '', designation: facts.designation ? facts.designation.v : '', acc: '', cat: '', acres: ac > 0 ? ac : geomAcres(f.geometry),
      access: 'not stated in this layer (check the agency)', protection: '', geom: f.geometry, source: L.label, layer: L.pre, link: L.url + '?objectIds=' + encodeURIComponent(id) + '&outFields=*&f=html' };
  }
  const SAVED_ONLY_HOSTS = /^(?:www\.)?(?:services\d*\.arcgis\.com|apps\.fs\.usda\.gov)$/i;   /* Nov 11 (job 3): services2..9 too (house rules: services*.arcgis.com) */
  function isSavedCopy(L) {
    if (!L) return false;
    if (L.live === false || L.read === 'saved copy') return true;
    try { return SAVED_ONLY_HOSTS.test(new URL(L.url).hostname); } catch (e) { return false; }
  }
  async function slQuery(L, params, ms) {
    if (isSavedCopy(L) || BANNED.test(L.url) || !/^https:\/\//.test(L.url)) throw new Error('not an allowed source');
    const c = new AbortController(), t = setTimeout(() => c.abort(), ms || 25000);
    try { const r = await fetch(L.url + '?' + new URLSearchParams(Object.assign({ f: 'geojson', outSR: 4326, outFields: '*', returnGeometry: true, maxAllowableOffset: 0.0008, geometryPrecision: 5 }, params)), { signal: c.signal });
      if (!r.ok) throw new Error('HTTP ' + r.status); const j = await r.json(); if (j.error) throw new Error(j.error.message || 'query error');
      return (j.features || []).filter(f => f && f.geometry && /Polygon/.test(f.geometry.type)).map(f => slRec(L, f)).filter(x => x.name && x.name !== L.label); }
    finally { clearTimeout(t); }
  }
  /* follow-up to #94: Kentucky's official layers are the club's own map files (the same ones Check all uses), read from this site */
  const LOCAL = {};
  async function slLocal(L, kind, arg) {
    if (!/^(?:[\w.-]+\/)*[\w.-]+\.geojson$/.test(L.url) || /^(?:https?:|\/\/)/i.test(L.url)) throw new Error('not an allowed source');
    if (!LOCAL[L.url]) LOCAL[L.url] = (async () => {
      const r = await fetch(L.url); if (!r.ok) throw new Error('HTTP ' + r.status); const j = await r.json();
      let own = {}; if (L.owners) { try { const o = await (await fetch(L.owners)).json(); own = (o && o.wmas) || {}; } catch (e) {} }
      const LL = L.owners ? Object.assign({}, L, { facts: Object.assign({ owner: '_owner' }, L.facts || {}) }) : L;
      return (j.features || []).map((f, i) => {
        const a = Object.assign({}, f.properties || {}), w = own[a[L.field]]; if (w && w.says) a._owner = String(w.says).replace(/^owned by\s*/i, '').replace(/\.$/, '');
        const rec = slRec(LL, { id: i, properties: a, geometry: f.geometry }); rec.link = a.URL || L.url; return rec;
      }).filter(x => x.geom && /Polygon/.test(x.geom.type) && x.name && x.name !== L.label);
    })().catch(e => { delete LOCAL[L.url]; throw e; });
    const all = await LOCAL[L.url];
    if (kind === 'state') return all;
    if (kind === 'pin') { const d = 6 / 111, dx = d / Math.max(0.2, Math.cos(arg[0] * Math.PI / 180)), q = [arg[1] - dx, arg[0] - d, arg[1] + dx, arg[0] + d]; return all.filter(x => boxHit(bbox(x.geom), q, 0)); }
    const w = norm(arg).split(' ').filter(x => x.length > 2).slice(0, 2); if (!w.length) return [];
    return all.filter(x => { const n = norm(x.name); return w.every(t => n.includes(t)); });
  }
  /* every ok layer for the place, 4 at a time: [{L, recs, err}] */
  async function slSearch(code, kind, arg) {
    const LS = (await stateLayers(code)).filter(L => L.ok && L.field && !isSavedCopy(L) && !BANNED.test(L.url) && (L.local || /^https:\/\//.test(L.url)));
    const params = L => kind === 'state' ? { where: '1=1', resultRecordCount: 1000 }
      : kind === 'pin' ? (() => { const d = 6 / 111, dx = d / Math.max(0.2, Math.cos(arg[0] * Math.PI / 180)); return { where: '1=1', geometry: [arg[1] - dx, arg[0] - d, arg[1] + dx, arg[0] + d].join(','), geometryType: 'esriGeometryEnvelope', inSR: 4326, spatialRel: 'esriSpatialRelIntersects' }; })()
      : (() => { const w = norm(arg).split(' ').filter(x => x.length > 2).slice(0, 2); return { where: w.length ? 'UPPER(' + L.field + ") LIKE '%" + w.join('%').toUpperCase().replace(/'/g, '%') + "%'" : '1=0' }; })();
    const out = LS.map(L => ({ L, recs: [], err: '' })); let k = 0;
    await Promise.all(Array.from({ length: Math.min(4, LS.length) }, async () => { while (k < out.length) { const o = out[k++];
      try { o.recs = o.L.local ? await slLocal(o.L, kind, arg) : await slQuery(o.L, params(o.L), 25000); } catch (e) { o.err = e && e.name === 'AbortError' ? 'took too long' : String(e && e.message || e); } } }));
    return { all: LS, out, skipped: (await stateLayers(code)).filter(L => !L.ok) };
  }
  const boxOf = gs => gs.map(bbox).filter(Boolean).reduce((a, b) => a ? [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])] : b, null);
  const boxHit = (a, b, pad) => a && b && a[0] - pad <= b[2] && b[0] - pad <= a[2] && a[1] - pad <= b[3] && b[1] - pad <= a[3];
  /* is this state-layer place the same land as that place? same name and close by, or mostly the same outline */
  function samePlace(a, b) {
    const A = a._bb || (a._bb = boxOf(a.geoms)), Bx = b._bb || (b._bb = boxOf(b.geoms)); if (!A || !Bx || !boxHit(A, Bx, 0.05)) return false;
    if (sameName(a.name, b.name)) return true;
    /* different names: only boxes that mostly overlap are worth the outline test (keeps a big state fast on a phone) */
    const ix = Math.max(0, Math.min(A[2], Bx[2]) - Math.max(A[0], Bx[0])) * Math.max(0, Math.min(A[3], Bx[3]) - Math.max(A[1], Bx[1])), ar = x => (x[2] - x[0]) * (x[3] - x[1]) || 1e-9;
    if (ix < 0.5 * Math.max(ar(A), ar(Bx))) return false;
    const ab = Math.max(0, ...a.geoms.map(g => coverShare(g, b.geoms))), ba = Math.max(0, ...b.geoms.map(g => coverShare(g, a.geoms)));
    return ab >= 0.6 && ba >= 0.6;
  }
  /* PAD-US / CPCAD places + state-layer records -> one list; a place in both lists both sources */
  async function mergeSources(places, srec) {
    places.forEach(p => { p.sources = p.sources || [p.source]; p.xids = p.xids || []; });
    const sp = groupRecords(srec.filter(r => r.acres >= 20).map(r => Object.assign({}, r, { manager: r.layer })));   /* grouped per layer + name */
    sp.forEach(x => { x.manager = x.facts && x.facts.manager ? x.facts.manager.v : x.source; x.sources = [x.source]; x.xids = []; });
    const extra = [];
    let n = 0;
    for (const x of sp) {
      if (++n % 25 === 0) await tick();
      const hit = places.find(p => samePlace(x, p)) || extra.find(p => samePlace(x, p));
      if (hit) { if (hit.sources.indexOf(x.source) < 0) hit.sources.push(x.source); hit.xids.push(...x.ids); (hit.also = hit.also || []).push({ source: x.source, name: x.name, ids: x.ids, link: x.link, facts: x.facts || {} });
        if (hit.kind !== 'state' && !hit.owner && x.facts && x.facts.owner) { hit.owner = x.facts.owner.v; hit.ownerFrom = x.source; }   /* PAD-US blank: the state layer's owner is used for the checks */ }
      else extra.push(x);
    }
    return places.concat(extra.sort((a, b) => b.acres - a.acres).slice(0, MAX_PLACES));
  }
  /* all the checks for one place */
  async function checkPlace(p, code, ctx) {
    const pt = (p.geoms[0] && samples(p.geoms[0], 5)[0]) || null;
    const box = p.geoms.map(bbox).filter(Boolean).reduce((a, b) => a ? [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])] : b, null);
    const c = { acc: p.acc, cat: p.cat, own: p.owner, same: [], cover: [], pinIn: [], named: [], nearest: null };
    p.ids.concat(p.xids || []).forEach(id => (ctx.rev[String(id)] || []).forEach(r => { if (c.same.indexOf(r) < 0) c.same.push(r); }));
    const pad = 0.6, close = box ? ctx.pins.filter(q => q.la >= box[1] - pad && q.la <= box[3] + pad && q.lo >= box[0] - pad * 1.3 && q.lo <= box[2] + pad * 1.3) : [];
    close.forEach(q => {
      const inIt = p.geoms.some(g => inside(q.la, q.lo, g));
      const km = Math.min(...p.geoms.map(g => nearestKm(g, q.la, q.lo)).concat([1e9]));
      if (inIt && c.pinIn.indexOf(q.ref) < 0) c.pinIn.push(q.ref);
      if (sameName(q.name, p.name) && km <= NAME_KM) c.named.push({ ref: q.ref, km });
      if (!c.nearest || km < c.nearest.km) c.nearest = { ref: q.ref, km, name: q.name };
    });
    /* the same name anywhere in about 400 km (a long trail or a big forest has its pin far from this piece) */
    if (pt && ctx.byName) (ctx.byName[nameKey(p.name)] || []).forEach(q => { if (!c.named.some(x => x.ref === q.ref)) { const km = kmBetween(pt[0], pt[1], q.la, q.lo); if (km <= 400 || /\btrail\b/i.test(p.name)) c.named.push({ ref: q.ref, km }); } });
    if (!c.same.length && p.geoms.length) {   /* park outlines from our key for the POTA parks close by (not pins alone) */
      const cand = close.filter(q => { const k = ctx.key[q.ref]; return k && k.g && k.g !== 'pin' && (k.m || []).length; })
        .map(q => ({ q, km: Math.min(...p.geoms.map(g => nearestKm(g, q.la, q.lo))) })).filter(x => x.km <= NEAR_PIN_KM).sort((a, b) => a.km - b.km).slice(0, 10);
      for (const x of cand) {
        const gs = await within(outline(x.q.ref, code), 12000, []); if (!gs.length) continue;
        const share = Math.max(...p.geoms.map(g => coverShare(g, gs)));
        if (share > 0) c.cover.push({ ref: x.q.ref, share, same: sameName(x.q.name, p.name) });
      }
    }
    p.checks = c; p.verdict = verdict(c); p.pt = pt; p.place = ctx.placeName;
    return p;
  }

  /* Check all, the Kentucky way, for every other place (kpc-maprep-check.js areaLayers): the place's official list, every place
     checked. Kentucky keeps its own layers. World places (GB, IE, AU, NZ) have no national list wired for this yet. */
  async function classify(code, say) {
    if (!code || code === 'KY') return { unsupported: 'Kentucky uses its own official layers.' };
    const G = W && W.KPCMapLogic, r = G && G.placeByCode ? G.placeByCode(code) : null, region = r ? r.region : (CP_LOC[code] ? 'CA' : /^(GB|IE|AU|NZ)$/.test(code) ? 'world' : 'US');
    if (!/^[A-Z]{2}$/.test(code) || region === 'world' || (region === 'CA' && !CP_LOC[code])) return { unsupported: 'No national list of protected places is wired for this country yet (only its published key below). Use Check a place for one spot.' };
    const ctx = await context(code); ctx.placeName = ctx.placeName || code;
    const recs = await statewide(code, say || (() => {}));
    const SL = slSearch(code, 'state').catch(() => ({ all: [], out: [], skipped: [] }));
    let places = groupRecords(recs).slice(0, MAX_PLACES);
    if (say) say('Getting the boundaries of ' + places.length + ' places\u2026');
    const sh = await shapes(code, places.flatMap(p => p.ids)); places.forEach(p => { if (!p.geoms.length) p.geoms = p.ids.map(id => sh[id]).filter(Boolean); });
    if (say) say('Reading the state and province layers\u2026');
    const S = await SL; places = await mergeSources(places, S.out.flatMap(o => o.recs)); const ST2 = srcStats(places);
    await prefetchOutlines(places, code, ctx);
    let n = 0; for (const p of places) { await within(checkPlace(p, code, ctx), 15000, null); if (!p.verdict) { p.checks = p.checks || { same: [], cover: [], pinIn: [], named: [], nearest: null }; p.verdict = verdict(p.checks); } n++; if (n % 3 === 0) await tick(); if (say && n % 15 === 0) say('Checked ' + n + ' of ' + places.length + '\u2026'); }
    return { places, kind: CP_LOC[code] ? 'ca' : 'pad', source: CP_LOC[code] ? 'CPCAD, December 2025 edition' : 'USGS PAD-US 4.0',
      note: (CP_LOC[code] ? 'The largest protected areas in CPCAD for this province. CPCAD does not say if the public can go in, so access stays unknown until you check.' : 'The largest places of public land open to the public (PAD-US fee land, 20 acres or more).') + ' Also searched: ' + (S.out.length ? S.out.map(o => o.L.label + (o.err ? ' (did not answer, try again later)' : ' (' + (ST2.by[o.L.label] || 0) + ')')).join(', ') : 'no state or province layer is wired for this place') + '. Same land in both: ' + ST2.both + '; only in a state layer: ' + ST2.stateOnly + '.',
      stats: ST2, layers: S.out.map(o => ({ label: o.L.label, recs: o.recs.length, err: o.err })), skipped: S.skipped.map(L => ({ label: L.label })) };
  }
  /* ---------- page ---------- */
  const $ = id => D && D.getElementById(id);
  let rmap = null, rlayer = null, lastPin = null, rows = [], filt = 'new', busy = false;
  const COL = { new: '#1d7a3a', person: '#b7791f', probably: '#8a6516', already: '#7a7a7a' };
  function placeCode() { const s = $('mrRsPlace'); return s ? s.value : ''; }
  function placeName() { const s = $('mrRsPlace'); return s && s.selectedIndex >= 0 ? String(s.options[s.selectedIndex].text || '').replace(/\s*\([A-Z]{2}\)$/, '') : ''; }
  function fillPlaces() {
    const src = $('mrCheckSt'), dst = $('mrRsPlace'); if (!dst || dst.dataset.ready) return;
    const G = W.KPCMapLogic, reg = c => { const r = G && G.placeByCode ? G.placeByCode(c) : null; return r ? r.region : (CA_CODES.indexOf(c) >= 0 ? 'CA' : /^(GB|IE|AU|NZ)$/.test(c) ? 'world' : 'US'); };
    const usca = src ? [...src.options].filter(o => /^[A-Z]{2}$/.test(o.value) && (reg(o.value) === 'US' || reg(o.value) === 'CA')) : [];
    if (!usca.length) return;
    dst.innerHTML = '<option value="">Pick a US state or Canadian province</option>' + usca.map(o => '<option value="' + esc(o.value) + '">' + esc(o.text) + '</option>').join('');
    dst.dataset.ready = '1';
    if (src && src.value && usca.some(o => o.value === src.value)) dst.value = src.value;
  }
  function mountMap() {
    if (rmap || !W.L) return;
    /* Nov 8 (Brandon, t748u): ONE map. The research results draw on the same map as Check a place, pin drop and Street View. */
    const C = W.KPCMapCheck; if (C && C.mount) C.mount();
    rmap = C && C.map ? C.map() : null; shared = !!rmap;
    /* the map's box can change size (layout, phone rotate, folded tools): tell Leaflet so drag and zoom use the real size */
    if (rmap && W.ResizeObserver && !rmap._kpcRO) { const box = rmap.getContainer(); rmap._kpcRO = new ResizeObserver(() => rmap.invalidateSize()); rmap._kpcRO.observe(box); }
    if (!rmap) { const el = $('mrDrop') || $('mrRsMap'); if (!el) return;
      rmap = L.map(el, { scrollWheelZoom: false }).setView([39.8, -90], 4);
      if (W.KPCLayers) W.KPCLayers(rmap, 'Street'); else L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '\u00a9 OpenStreetMap contributors, ODbL' }).addTo(rmap); }
    rlayer = L.featureGroup().addTo(rmap);
    rmap.on('click', e => { const t = e.originalEvent && e.originalEvent.target; if (t && t.closest && t.closest('.leaflet-control, .leaflet-popup')) return; lastPin = [e.latlng.lat, e.latlng.lng]; drawPin(); if (tab !== 'pin') setTab('pin'); say('Pin dropped. Tap SEARCH to check the official land around it.'); });
    setTimeout(() => rmap && rmap.invalidateSize(), 80);
  }
  let pinMk = null, shared = false;
  /* scroll the details panel only (never the page) so the map stays where it is */
  /* Results open in the panel: a desktop panel scrolls by itself and the page stays put. When the panel does not scroll (a phone) the
     page only moves when asked (force: FULL RULES CHECK, Brandon 1:55 PM CST t749u "when you click full rules check it dont jump to it"). */
  function inPanel(el, block, force) {
    if (!el) return; const P = $('mrPanel');
    const own = P && P.contains(el) && getComputedStyle(P).overflowY !== 'visible' && P.scrollHeight > P.clientHeight + 2;
    if (own) { const top = P.scrollTop + el.getBoundingClientRect().top - P.getBoundingClientRect().top - 6; try { P.scrollTo({ top, behavior: 'smooth' }); } catch (e) { P.scrollTop = top; }
      if (force) { const r = P.getBoundingClientRect(); if (r.top < 60 || r.top > innerHeight * 0.5) try { P.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch (e) {} } return; }
    if (force) try { el.scrollIntoView({ behavior: 'smooth', block: block || 'start' }); } catch (e) {}
  }
  /* bring the rules check into view now and again once it has filled in (it loads in steps) */
  function showSpot() { const el = $('mrSpot'); if (!el) return; inPanel(el, 'start', true);
    let n = 0; const mo = new MutationObserver(() => { if (++n > 3) return mo.disconnect(); inPanel(el, 'start', true); }); mo.observe(el, { childList: true }); setTimeout(() => mo.disconnect(), 4000); }
  function drawPin() { if (!rmap || !lastPin || shared) return; if (pinMk) rmap.removeLayer(pinMk); pinMk = L.circleMarker(lastPin, { radius: 7, color: '#111', fillColor: '#f0c96b', fillOpacity: 1, weight: 2 }).addTo(rmap); }
  /* Live status panel (Brandon Nov 8, 1:08 PM CST: "make it feel like it is doing work"): each step with a tick, a bar,
     elapsed time, a note when a source is slow, and a clear error with TRY AGAIN. */
  const ST = { t0: 0, timer: null, steps: [], last: null, slowAt: 0 };
  function stEl() { return $('mrRsStatus'); }
  function stDraw() {
    const el = stEl(); if (!el) return;
    const secs = ST.t0 ? Math.round((Date.now() - ST.t0) / 1000) : 0, cur = ST.steps.filter(x => x.st === 'run').slice(-1)[0];
    const pct = cur && cur.total ? Math.min(100, Math.round(cur.n / cur.total * 100)) : null;
    const slow = cur && !el.classList.contains('done') && !el.classList.contains('err') && Date.now() - cur.at > 20000;
    el.innerHTML = '<div class="mr-rs-st-head"><span class="mr-rs-spin" aria-hidden="true"></span><span>' + esc(ST.title || 'Searching') + '</span><span class="t">' + Math.floor(secs / 60) + ':' + String(secs % 60).padStart(2, '0') + '</span></div>'
      + '<div class="mr-rs-bar' + (pct === null && !el.classList.contains('done') && !el.classList.contains('err') ? ' ind' : '') + '" role="progressbar" aria-valuemin="0" aria-valuemax="100"' + (pct !== null ? ' aria-valuenow="' + pct + '"' : '') + '><i style="' + (el.classList.contains('done') ? 'width:100%' : pct !== null ? 'width:' + pct + '%' : '') + '"></i></div>'
      + '<ol class="mr-rs-steps">' + ST.steps.map(x => '<li class="' + x.st + '">' + esc(x.label) + (x.note ? '<small>' + esc(x.note) + '</small>' : '') + (x.retry && !ST.timer ? ' <button type="button" class="mr-rs-retry1" data-rsretry="1">TRY AGAIN</button>' : '') + '</li>').join('') + '</ol>'
      + (slow ? '<p class="mr-rs-slow">Still waiting on the official server. Big states can take a minute or two; nothing is broken.</p>' : '')
      + (ST.err ? '<p class="mr-rs-err">' + esc(ST.err) + '</p><div class="mr-check-btns"><button type="button" id="mrRsRetry">TRY AGAIN</button></div>' : '');
    const r = $('mrRsRetry'); if (r) r.onclick = () => (ST.kind === 'ids' ? (ST.err = '', stDraw()) : run(ST.kind));
    el.querySelectorAll('[data-rsretry]').forEach(b => b.onclick = () => { if (ST.kind !== 'ids') run(ST.kind); });
  }
  function stBegin(title, kind) {
    const el = stEl(); ST.t0 = Date.now(); ST.steps = []; ST.title = title; ST.err = ''; ST.kind = kind;
    if (el) { el.hidden = false; el.classList.remove('done', 'err'); }
    clearInterval(ST.timer); ST.timer = setInterval(stDraw, 1000); stDraw();
  }
  function stStep(label, total) { ST.steps.forEach(x => { if (x.st === 'run') x.st = 'ok'; }); const x = { label, st: 'run', n: 0, total: total || 0, at: Date.now(), note: '' }; ST.steps.push(x); stDraw(); return x; }
  function stCount(x, n, note) { if (!x) return; x.n = n; x.note = note || (x.total ? n.toLocaleString('en-US') + ' / ' + x.total.toLocaleString('en-US') : ''); stDraw(); }
  /* one line per source: 'Georgia DNR State Parks: 63 places' (a source that failed gets TRY AGAIN; the search goes on) */
  function stLine(label, ok, note) { ST.steps.push({ label, st: ok ? 'ok' : 'bad', n: 0, total: 0, at: Date.now(), note: note || '', retry: !ok, src: true }); stDraw(); }
  function srcStats(places, padSrc) {
    const by = {}; let padOnly = 0, stateOnly = 0, both = 0;
    places.forEach(p => { const ss = p.sources || [p.source]; ss.forEach(x => { by[x] = (by[x] || 0) + 1; });
      const hasPad = p.kind !== 'state', hasSt = p.kind === 'state' || (p.also || []).length > 0; if (hasPad && hasSt) both++; else if (hasPad) padOnly++; else stateOnly++; });
    return { by, padOnly, stateOnly, both };
  }
  function sourceLines(src, padErr, S, places) {
    const padSrc = places.find(p => p.kind !== 'state'), st = srcStats(places), padLabel = padSrc ? padSrc.source : (src === 'CPCAD' ? 'CPCAD, December 2025 edition' : 'USGS PAD-US 4.0');
    stLine(padLabel + ': ' + (padErr ? 'did not answer (' + padErr + ')' : (st.by[padLabel] || 0) + ' places'), !padErr);
    S.out.forEach(o => stLine(o.L.label + ': ' + (o.err ? 'did not answer (' + o.err + ')' : (st.by[o.L.label] || 0) + ' places' + (o.recs.length >= 1000 ? ' (first 1,000 read)' : '')), !o.err));
    /* skipped layers stay silent on the page */
    stLine('Same land in both lists: ' + st.both + ' \u00b7 only in ' + (src === 'CPCAD' ? 'CPCAD' : 'PAD-US') + ': ' + st.padOnly + ' \u00b7 only in a state layer: ' + st.stateOnly, true);
    W.KPCResearch && (W.KPCResearch.lastStats = Object.assign({ layers: S.out.map(o => ({ label: o.L.label, recs: o.recs.length, err: o.err })), skipped: S.skipped.map(L => ({ label: L.label })), padErr }, st));
  }
  function stEnd(ok, msg) {
    const el = stEl(); ST.steps.forEach(x => { if (x.st === 'run') x.st = ok ? 'ok' : 'bad'; }); clearInterval(ST.timer); ST.timer = null;
    if (el) el.classList.add(ok ? 'done' : 'err');
    if (ok) { ST.title = msg || 'Done'; } else ST.err = msg; stDraw();
  }
  function say(t) { const el = $('mrRsMsg'); if (el) el.textContent = t; }
  function draw(list, fit) {
    if (!rmap || !rlayer) return; rlayer.clearLayers();
    list.forEach((p, i) => p.geoms.forEach(g => { try { L.geoJSON({ type: 'Feature', geometry: g }, { style: { color: COL[p.verdict.v], weight: 2, fillOpacity: 0.15 } }).on('click', () => focus(i)).bindTooltip(esc(p.name) + ' \u00b7 ' + esc(p.verdict.label)).addTo(rlayer); } catch (e) {} }));
    if (fit && rlayer.getLayers().length) try { rmap.fitBounds(rlayer.getBounds(), { maxZoom: 13, padding: [16, 16] }); } catch (e) {}
  }
  function focus(i) {
    const p = rows[i]; if (!p) return;
    const el = D.querySelector('[data-rs="' + i + '"]'); if (el) { if (el.tagName === 'DETAILS') el.open = true; inPanel(el, 'start'); }
    if (rmap && p.geoms.length) { const g = L.geoJSON({ type: 'FeatureCollection', features: p.geoms.map(x => ({ type: 'Feature', geometry: x })) }); try { rmap.fitBounds(g.getBounds(), { maxZoom: 14, padding: [20, 20] }); } catch (e) {} }
  }
  /* every fact with its source; PAD-US / CPCAD and a state layer that say different things are both shown, marked 'sources differ' */
  const FACT_LAB = { owner: 'Owner', manager: 'Manager', designation: 'Designation', acres: 'Acres', website: 'Website' };
  function factRows(p) {
    const rows = [], base = p.kind === 'state' ? [] : [{ src: p.source, owner: p.ownerFrom ? '' : p.owner, manager: p.manager, designation: p.designation, acres: p.acres }];
    const st = (p.kind === 'state' ? [{ source: p.source, facts: p.facts || {} }] : (p.also || [])).map(x => Object.assign({ src: x.source }, Object.fromEntries(Object.entries(x.facts || {}).map(([k, v]) => [k, v.v]))));
    const all = base.concat(st), key = v => norm(String(v || '').replace(/\(.*?\)/g, ''));
    ['owner', 'manager', 'designation', 'acres', 'website'].forEach(k => {
      const vals = all.filter(x => x[k] != null && String(x[k]).trim() !== '' && !(k === 'acres' && !(+String(x[k]).replace(/,/g, '') > 0))).map(x => ({ v: k === 'acres' ? Math.round(+String(x[k]).replace(/,/g, '')).toLocaleString('en-US') : String(x[k]).trim(), src: x.src }));
      if (!vals.length) return;
      for (let i = vals.length - 1; i > 0; i--) { const j = vals.findIndex(x => key(x.v) === key(vals[i].v)); if (j < i) { vals[j].src += ' + ' + vals[i].src; vals.splice(i, 1); } }   /* the same value twice: one line, both sources */
      let differ = false;
      if (vals.length > 1) { if (k === 'acres') { const n = vals.map(x => +x.v.replace(/,/g, '')); differ = Math.max(...n) > 1.25 * Math.min(...n); }
        else if (k !== 'website') { const ks = vals.map(x => key(x.v)); differ = ks.some(a => ks.some(b => a && b && a.indexOf(b) < 0 && b.indexOf(a) < 0 && !sameName(a, b))); } }
      rows.push({ k, label: FACT_LAB[k], vals, differ });
    });
    return rows;
  }
  /* the state-layer facts of a place for the full rules check: {owner:{v,src}, manager, designation, website}, plus the facts block */
  function placeFacts(p) {
    const sf = p.kind === 'state' ? Object.assign({}, p.facts || {}) : Object.assign({}, ...((p.also || []).map(x => x.facts || {}).reverse()));
    const facts = {}; ['owner', 'manager', 'designation', 'website'].forEach(k => { if (sf[k]) facts[k] = sf[k]; });
    return { name: p.name, box: boxOf(p.geoms), facts, html: factsHtml(p) };
  }
  function factsHtml(p) {
    const R = factRows(p); if (!R.length || (p.kind !== 'state' && !(p.also || []).length)) return '';   /* PAD-US only: its own record card already shows these */
    return '<div class="mr-rs-checks mr-rs-facts"><b>Official record facts, by source</b><ul>' + R.map(r => '<li>' + esc(r.label) + ': ' + r.vals.map(x => (r.k === 'website' && /^https?:\/\//i.test(x.v) ? '<a href="' + esc(x.v) + '" target="_blank" rel="noopener">' + esc(x.v) + '</a>' : '<b>' + esc(x.v) + '</b>') + ' <small>(' + esc(x.src) + ')</small>').join(' \u00b7 ')
      + (r.differ ? ' <span class="mr-rs-differ">sources differ</span>' : '') + '</li>').join('') + '</ul></div>';
  }
  function card(p, i) {
    const X = W.KPCMapExtras, c = p.checks || {};
    const official = p.kind === 'pad' ? (X && X.padCard ? X.padCard(p.a) : '') : p.kind === 'state' ? '<p class="mr-help mr-rs-src">From the state / province layer: <b>' + esc(p.source) + '</b> (not in ' + (p.source && /CPCAD/.test(p.source) ? 'CPCAD' : 'PAD-US or CPCAD') + ')</p>' : (X && X.caCard ? X.caCard(p.a) : '');
    const also = (p.also || []).length ? '<p class="mr-help mr-rs-src">Also in: ' + p.also.map(x => '<a href="' + esc(x.link) + '" target="_blank" rel="noopener">' + esc(x.source) + (norm(x.name) !== norm(p.name) ? ' (\u201c' + esc(x.name) + '\u201d)' : '') + '</a>').join(' \u00b7 ') + '</p>' : '';
    const lines = [];
    if (c.same.length) lines.push('Same official record as: ' + c.same.join(', '));
    (c.cover || []).forEach(x => lines.push('Park outline over it: ' + x.ref + ' covers ' + Math.round(x.share * 100) + '%'));
    if (c.pinIn.length) lines.push('POTA pin inside it: ' + c.pinIn.join(', '));
    (c.named || []).forEach(x => lines.push('Same name: ' + x.ref + ', ' + x.km.toFixed(1) + ' km'));
    lines.push('Nearest POTA park: ' + (c.nearest ? c.nearest.ref + ' ' + c.nearest.name + ', ' + c.nearest.km.toFixed(1) + ' km' : 'none within about 60 km'));
    return '<details class="mr-rs-card mr-rs-' + p.verdict.v + '" data-rs="' + i + '"><summary><span class="mr-rs-v">' + esc(p.verdict.label) + '</span><b>' + esc(p.name) + '</b><small>'
      + esc([(p.sources || []).length > 1 ? p.sources.length + ' sources' : p.kind === 'state' ? p.source : '', p.designation, p.kind === 'state' ? '' : p.manager].map(x => String(x || '').trim()).concat([ p.acres ? Math.round(p.acres).toLocaleString('en-US') + ' acres' : '']).filter(Boolean).join(' \u00b7 ')) + '</small></summary>'
      + '<p class="mr-rs-why">' + esc(p.verdict.why) + '</p>'
      + '<div class="mr-rs-checks"><b>Checks</b><ul>' + lines.map(l => '<li>' + esc(l) + '</li>').join('') + '</ul></div>'
      + factsHtml(p) + official + also
      + '<p class="mr-rs-links"><a href="' + esc(p.link) + '" target="_blank" rel="noopener">OFFICIAL RECORD \u203a</a> <button type="button" class="mr-ag" data-rscheck="' + i + '">FULL RULES CHECK</button></p>'
      + '<label class="mr-rs-sumlab">Summary for a park submission (copy and edit)</label><textarea class="mr-rs-sum" readonly rows="9" id="mrRsSum' + i + '">' + esc(summaryText(p)) + '</textarea>'
      + '<button type="button" class="mr-ag" data-rscopy="' + i + '">COPY SUMMARY</button></details>';
  }
  function paint() {
    const out = $('mrRsOut'); if (!out) return;
    const n = { new: 0, person: 0, probably: 0, already: 0 }; rows.forEach(p => n[p.verdict.v]++);
    const lab = { new: 'Possible candidate', person: 'Needs a person', probably: 'Probably already a park', already: 'Already a park', all: 'All' };
    const show = rows.map((p, i) => [p, i]).filter(([p]) => filt === 'all' || p.verdict.v === filt);
    out.innerHTML = '<div class="mr-filters" id="mrRsFilters">' + ['new', 'person', 'probably', 'already', 'all'].map(k => '<button type="button" class="mr-ag' + (k === filt ? ' on' : '') + '" data-rsf="' + k + '">' + lab[k] + ' \u00b7 ' + (k === 'all' ? rows.length : n[k]) + '</button>').join('') + '</div>'
      + (show.length ? show.map(([p, i]) => card(p, i)).join('') : '<p class="mr-help">None in this group.</p>');
    out.querySelectorAll('[data-rsf]').forEach(b => b.onclick = () => { filt = b.dataset.rsf; paint(); });
    /* clicking a result (its summary) focuses the one map on it; no separate map button */
    out.querySelectorAll('details[data-rs]').forEach(d => d.addEventListener('toggle', () => { if (d.open) focus(+d.dataset.rs); }));
    out.querySelectorAll('[data-rscopy]').forEach(b => b.onclick = () => { const t = $('mrRsSum' + b.dataset.rscopy); if (!t) return; t.select(); (navigator.clipboard ? navigator.clipboard.writeText(t.value) : Promise.reject()).then(() => { b.textContent = 'COPIED'; }).catch(() => { try { D.execCommand('copy'); b.textContent = 'COPIED'; } catch (e) {} }); });
    out.querySelectorAll('[data-rscheck]').forEach(b => b.onclick = () => {   /* hand the place to "Check a place" (the full rules checklist) */
      const p = rows[+b.dataset.rscheck]; if (!p || !p.pt) return;
      /* Nov 8 (t751u, no repeats): the full check below shows the official record again, so this card folds up */
      const card0 = b.closest('details'); if (card0) card0.open = false;
      const st = $('mrCheckSt'); if (st && [...st.options].some(o => o.value === placeCode())) { st.value = placeCode(); st.dispatchEvent(new Event('change')); }
      if ($('mrCheckQ')) $('mrCheckQ').value = p.name;
      /* follow-up to #94: the full check gets this place's facts from its state / province layers (owner, manager, designation, website) */
      if (W.KPCMapCheck && W.KPCMapCheck.setPlaceFacts) W.KPCMapCheck.setPlaceFacts(placeFacts(p));
      if (W.KPCMapCheck && W.KPCMapCheck.showPoint) W.KPCMapCheck.showPoint(p.pt[0], p.pt[1]);
      showSpot();
    });
    draw(show.map(([p]) => p), false);
  }
  async function context(code) {
    const [key, P] = await Promise.all([within(keyFile(code), 30000, null), within(pins(), 30000, [])]);
    const parks = (key && key.parks) || {}, rev = {};
    Object.entries(parks).forEach(([ref, k]) => { if (k && k.g !== 'pin') (k.m || []).forEach(x => { const id = String(x[0]); (rev[id] = rev[id] || []).indexOf(ref) < 0 && rev[id].push(ref); }); });
    const byName = {}; P.forEach(q => { const k = nameKey(q.name); if (k) (byName[k] = byName[k] || []).push(q); });
    return { key: parks, rev, pins: P, byName, placeName: D ? placeName() : '' };
  }
  /* "Possible new parks" (Check all) hands a row here: the same full checks, by its PAD-US record ids */
  async function testIds(code, ids, name) {
    const sel = $('mrRsPlace'); if (sel && code && [...sel.options].some(o => o.value === code)) sel.value = code;
        if (busy) return; busy = true; mountMap();
    stBegin('Full checks on \u201c' + (name || ids.join(', ')) + '\u201d', 'ids'); let step = null;
    try {
      say('Running the full checks on \u201c' + (name || ids.join(', ')) + '\u201d\u2026'); step = stStep('Loading the answer key, pins and the official record\u2026');
      const ctx = await context(code);
      const j = await arc(CP_LOC[code] ? CPCAD_LAYER : PADUS_LAYER, { objectIds: ids.join(','), outFields: CP_LOC[code] ? CP_FIELDS : PAD_FIELDS, returnGeometry: true, maxAllowableOffset: 0.0005, geometryPrecision: 5 });
      const places = groupRecords((j.features || []).map(CP_LOC[code] ? caRec : padRec));
      for (const p of places) await checkPlace(p, code, ctx);
      rows = places; filt = 'all'; paint(); draw(rows, true);
      say(places.length ? places.map(p => p.name + ': ' + p.verdict.label).join(' \u00b7 ') : 'That record did not come back from the official service.');
      if (places.length) stEnd(true, 'Done: ' + places.map(p => p.name + ': ' + p.verdict.label).join(' \u00b7 ')); else stEnd(false, 'That record did not come back from the official service.');
    } catch (e) { say('The official records did not answer (' + (e && e.message || e) + ').'); stEnd(false, 'The official records did not answer (' + (e && e.message || e) + '). Try again in a minute.'); }
    busy = false;
  }
  /* Nov 8 (Brandon 5:17 / 5:18 PM CST, t768u/t769u): NEAR A SPOT takes an address again (no device GPS). The address is turned into
     GPS with OpenStreetMap Nominatim, the geocoder Check a place uses (kpc-maprep.js), same query; the GPS is shown, the pin goes on
     the one map (the same as a tap) and the search runs from there. Typed GPS numbers work too. Only on SEARCH, at most one request
     a second, results kept. The dropped pin still works. */
  const GEO = {}; let geoAt = 0, locDone = '';
  const gpsNums = t => { const m = String(t).match(/^\s*(-?\d{1,2}(?:\.\d+)?)\s*[, ]\s*(-?\d{1,3}(?:\.\d+)?)\s*$/); if (!m) return null; const a = +m[1], b = +m[2]; return Math.abs(a) <= 90 && Math.abs(b) <= 180 ? [a, b] : null; };
  async function geocode(t) {
    if (GEO[t] !== undefined) return GEO[t];
    const nq = async q2 => { const w = 1100 - (Date.now() - geoAt); if (w > 0) await new Promise(r => setTimeout(r, w)); geoAt = Date.now();
      try { const r = await fetch('https://nominatim.openstreetmap.org/search?' + new URLSearchParams({ q: q2, format: 'jsonv2', countrycodes: 'us,ca', addressdetails: 1, limit: 1 })); return r.ok ? ((await r.json()) || [])[0] || null : null; } catch (e) { return null; } };
    const st0 = placeCode(); let h = await nq(t);
    if (!h && st0 && !new RegExp('\\b' + st0 + '\\b', 'i').test(t)) h = await nq(t + ', ' + st0);
    return (GEO[t] = h ? { la: +h.lat, lo: +h.lon, label: h.display_name, st: String((h.address || {})['ISO3166-2-lvl4'] || '').replace(/^(US|CA)-/, '') } : null);
  }
  function pickPlace(st) { const sel = $('mrRsPlace'); if (st && sel && [...sel.options].some(o => o.value === st) && sel.value !== st) { sel.value = st; sel.dispatchEvent(new Event('change')); } }
  async function stateAt(la, lo) {   /* the same FCC lookup Check a place uses for GPS numbers (US only) */
    try { const r = await fetch(`https://geo.fcc.gov/api/census/area?lat=${la}&lon=${lo}&format=json`); const c = r.ok ? await r.json() : null; return (((c && c.results) || [])[0] || {}).state_code || ''; } catch (e) { return ''; }
  }
  function showAt(t) { const el = $('mrRsLocAt'); if (el) { el.textContent = t || ''; el.hidden = !t; } }
  async function nearFrom(la, lo, label, st) {
    lastPin = [la, lo]; mountMap();
    if (shared && W.KPCMapCheck && W.KPCMapCheck.showPoint) { try { W.KPCMapCheck.showPoint(la, lo); } catch (e) {} }
    else if (rmap) { drawPin(); rmap.setView(lastPin, Math.max(rmap.getZoom(), 11)); }
    showAt('GPS ' + la.toFixed(6) + ', ' + lo.toFixed(6) + (label ? ' \u00b7 ' + label : ''));
    pickPlace(st || await stateAt(la, lo));
    return run('pin', true);
  }
  async function locSearch() {
    const t = ($('mrRsLoc') && $('mrRsLoc').value || '').trim(); if (!t) return false;
    if (t === locDone && lastPin) return false;   /* already placed; SEARCH uses the pin (it may have been moved since) */
    locDone = t; const g = gpsNums(t);
    if (g) { await nearFrom(g[0], g[1], ''); return true; }
    say('Finding that address\u2026'); showAt('');
    const h = await geocode(t);
    if (!h || !isFinite(h.la) || !isFinite(h.lo)) { locDone = ''; say('Could not find that address. Add the town and state, try the road name only, or paste GPS numbers.'); return true; }
    await nearFrom(h.la, h.lo, h.label, h.st); return true;
  }
  async function run(kind, placed) {
    if (kind === 'pin' && !placed && !busy && await locSearch()) return;
    if (busy) return; const code = placeCode();
    if (!code) { say('Pick a US state or a Canadian province first.'); return; }
    if (kind === 'pin' && !lastPin && W.KPCMapCheck && W.KPCMapCheck.pin && W.KPCMapCheck.pin()) { const q = W.KPCMapCheck.pin(); lastPin = Array.isArray(q) ? q : [q.lat != null ? q.lat : q.la, q.lng != null ? q.lng : q.lo]; }
    if (kind === 'pin' && !lastPin) { say('Tap the map to drop a pin first.'); return; }
    const q0 = ($('mrRsQ') && $('mrRsQ').value || '').trim();
    if (kind === 'name' && !q0) { say('Type a place name first.'); return; }
    if (code === 'KY') { /* Kentucky has no published key file; pins and names still work */ }
    busy = true; mountMap();
    const pn = placeName() || code, src = CP_LOC[code] ? 'CPCAD' : 'PAD-US';
    stBegin(kind === 'state' ? 'Searching all of ' + pn : kind === 'pin' ? 'Searching near your pin in ' + pn : 'Searching for \u201c' + q0 + '\u201d in ' + pn, kind);
    let step = null;
    try {
      step = stStep('Loading the answer key and POTA pins for ' + pn + '\u2026');
      const ctx = await context(code); stCount(step, 0, (ctx.pins || []).length.toLocaleString('en-US') + ' pins');
      let recs = [], padErr = '';
      const SL = slSearch(code, kind, kind === 'pin' ? lastPin : q0).catch(() => ({ all: [], out: [], skipped: [] }));   /* state / province layers, in parallel */
      try {
        if (kind === 'state') { step = stStep('Loading ' + src + ' for ' + code + '\u2026'); recs = await statewide(code, say); }
        else if (kind === 'pin') { step = stStep('Loading ' + src + ' around the pin\u2026'); say('Reading official land around the pin\u2026'); recs = await near(code, lastPin[0], lastPin[1], 6); }
        else { step = stStep('Looking for \u201c' + q0 + '\u201d in ' + src + '\u2026'); say('Looking for \u201c' + q0 + '\u201d in the official records\u2026'); recs = await byName(code, q0); if (!recs.length && lastPin) recs = (await near(code, lastPin[0], lastPin[1], 10)).filter(r => sameName(r.name, q0) || norm(r.name).indexOf(norm(q0)) >= 0); }
      } catch (e) { padErr = String(e && e.name === 'AbortError' ? 'took too long' : (e && e.message || e)); }
      let places = groupRecords(recs).slice(0, kind === 'state' ? MAX_PLACES : 40);
      stCount(step, 0, padErr ? 'did not answer' : recs.length.toLocaleString('en-US') + ' records \u00b7 ' + places.length + ' places');
      if (places.some(p => !p.geoms.length)) {
        step = stStep('Getting the boundaries of ' + places.length + ' places\u2026');
        say('Getting the boundaries of ' + places.length + ' places\u2026');
        const sh = await shapes(code, places.flatMap(p => p.ids)); places.forEach(p => { if (!p.geoms.length) p.geoms = p.ids.map(id => sh[id]).filter(Boolean); });
      }
      step = stStep('Reading the state and province layers for ' + pn + '\u2026'); say('Reading the state and province layers\u2026');
      const S = await SL; stCount(step, 0, S.all.length + ' layer' + (S.all.length === 1 ? '' : 's'));
      places = await mergeSources(places, S.out.flatMap(o => o.recs));
      sourceLines(src, padErr, S, places);
      if (!places.length) { rows = []; paint(); const m = padErr && !S.out.some(o => !o.err) ? 'The official records did not answer (' + padErr + '). Try again in a minute.' : 'No official records came back for that. Try another name, drop a pin, or check the spelling.'; say(m); stEnd(false, m); busy = false; return; }
      step = stStep('Loading the key outlines near these places (one batch)\u2026');
      await prefetchOutlines(places, code, ctx, (n, t) => stCount(step, n, n + ' / ' + t + ' batches'));
      step = stStep('Checking against key outlines, pins and names (on this device)\u2026', places.length);
      let done = 0;
      for (const p of places) { await within(checkPlace(p, code, ctx), 15000, null); if (!p.verdict) { p.checks = p.checks || { same: [], cover: [], pinIn: [], named: [], nearest: null }; p.verdict = verdict(p.checks); } done++; if (done % 3 === 0) await tick(); stCount(step, done); if (done % 10 === 0) say('Checked ' + done + ' of ' + places.length + '\u2026'); }
      places.sort((a, b) => (RANK[a.verdict.v] - RANK[b.verdict.v]) || b.acres - a.acres);
      rows = places; filt = rows.some(p => p.verdict.v === 'new') ? 'new' : 'all';
      const n = rows.filter(p => p.verdict.v === 'new').length, c = { person: 0, probably: 0, already: 0 }; rows.forEach(p => { if (p.verdict.v in c) c[p.verdict.v]++; });
      say(rows.length + ' places checked' + (kind === 'state' ? (CP_LOC[code] ? ' (the largest protected areas in CPCAD plus the province layers; CPCAD does not say if the public can go in, so check access)' : ' (the largest PAD-US places open to the public, plus the state and province layers)') : '') + ': ' + n + (n === 1 ? ' is a possible candidate' : ' are possible candidates') + ' (not on POTA yet, by our checks; not newly opened land). Tap one for the checks, the official record and a summary to copy.');
      paint(); draw(rows, true);
      stEnd(true, 'Done: ' + rows.length + ' places checked \u00b7 ' + n + ' possible candidates \u00b7 ' + c.person + ' need a person \u00b7 ' + (c.probably + c.already) + ' already parks');
    } catch (e) { const m = 'The official records did not answer (' + (e && e.message || e) + '). Try again in a minute.'; say(m); stEnd(false, (step ? step.label.replace(/\u2026$/, '') + ' failed. ' : '') + m); }
    busy = false;
  }
  let tab = 'state';
  function setTab(k) {
    tab = k; const root = $('mrResearch'); if (!root) return;
    root.querySelectorAll('[data-rstab]').forEach(t => { const on = t.dataset.rstab === k; t.classList.toggle('on', on); t.setAttribute('aria-selected', on ? 'true' : 'false'); });
    root.querySelectorAll('[data-rspane]').forEach(p => { p.hidden = p.dataset.rspane !== k; });
    if (k === 'name' && $('mrRsQ')) $('mrRsQ').focus();
    say(k === 'state' ? 'Pick a state or province, then SEARCH.' : k === 'pin' ? (lastPin ? 'Pin is down. SEARCH checks the land around it.' : 'Tap the map to drop a pin, then SEARCH.') : 'Type a name, then SEARCH.');
  }
  function wire() {
    const root = $('mrResearch'); if (!root || root.dataset.wired) return; root.dataset.wired = '1';
    const tryFill = () => { fillPlaces(); if (!($('mrRsPlace') || {}).dataset || !$('mrRsPlace').dataset.ready) setTimeout(tryFill, 400); };
    tryFill();
    const b = (id, fn) => { const el = $(id); if (el) el.onclick = fn; };
    b('mrRsFind', () => run('state')); b('mrRsNear', () => run('pin')); b('mrRsTest', () => run('name'));
    root.querySelectorAll('[data-rstab]').forEach(t => t.onclick = () => setTab(t.dataset.rstab));
    const f = $('mrRsForm'); if (f) f.addEventListener('submit', e => { e.preventDefault(); run(tab); });
    b('mrRsPinUse', () => { const q = W.KPCMapCheck && W.KPCMapCheck.pin && W.KPCMapCheck.pin(); if (q) lastPin = Array.isArray(q) ? q : [q.lat != null ? q.lat : q.la, q.lng != null ? q.lng : q.lo];
      if (!lastPin) { say('Tap the map to drop a pin first.'); return; } if ($('mrRsLoc')) $('mrRsLoc').value = ''; locDone = ''; showAt(''); run('pin', true); });
    const det = $('mrResearch'); if (det) { mountMap(); }
    D.addEventListener('click', e => { const t = e.target && e.target.closest && e.target.closest('[data-rstest]'); if (!t) return; e.preventDefault();
      const st = $('mrCheckSt'); testIds((st && st.value) || placeCode(), String(t.dataset.rstest).split(',').filter(Boolean), t.dataset.rsname || ''); });
  }
  if (D) { const go = () => { const app = $('mrApp'); if (app && app.hidden) { setTimeout(go, 300); return; } wire(); }; if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', go); else go(); }
  W.KPCResearch = { placeFacts, factRows, slRec, mergeSources, samePlace, srcStats, slSearch, stateLayers, geomAcres, capName, within, prefetchOutlines, candRefs, verdict, sameName, nameKey, norm, coverShare, samples, inside, bbox, groupRecords, summaryText, nearestKm, padRec, caRec, checkPlace, classify, run, testIds, setTab, PADUS_LAYER, CPCAD_LAYER, CP_LOC };
  if (typeof module !== 'undefined' && module.exports) module.exports = W.KPCResearch;
})();
