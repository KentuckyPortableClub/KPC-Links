/* Mapping Rep Tool Box: FIND AND TEST NEW PARKS (Nov 8 2026, Brandon 11:19 AM CST: "the MAIN reason for this tool is for mapping
   reps to research and find new parks to add ... make the tool a tool ... run the checks and provide info").
   For a picked state or province it lists official protected land (USGS PAD-US for a US state, Canada's CPCAD for a province)
   and checks every place by itself:
     - is it already a POTA park? the same official record in our answer key, a park outline from the key over it, a POTA pin
       inside it, or a POTA park with the same name close by (not pins alone)
     - the nearest POTA park and how far, and any overlap with a park outline (part of a park, or a 2-fer)
     - the full official record (name, manager, owner, designation, GAP / IUCN, public access, acres, record id and link)
   and gives a plain verdict (looks new / probably already a park / needs a person) with a summary to copy for a submission.
   A rep can also test a place they found themselves (a name, or a tap on the map).
   Requests: only the two official services the Tool Box already reads in the browser (edits.nationalmap.gov PAD-US,
   maps-cartes.ec.gc.ca CPCAD; robots.txt allows both), and this site's own files (answer keys, POTA list). Nothing is written. */
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
    return { v: 'new', label: 'Looks new', why: 'No POTA park on this official record, no park outline over it, no POTA pin inside it, no park with this name nearby.' + (c.nearest ? ' Nearest POTA park: ' + c.nearest.ref + ', ' + c.nearest.km.toFixed(1) + ' km.' : '') };
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
  async function outline(ref, code) {
    if (!(ref in outlineP)) outlineP[ref] = (async () => {
      try {
        if (CP_LOC[code] && W.KPCB && W.KPCB.canada) { const k = await W.KPCB.canada(ref); return ((k && k.fs) || []).map(f => f.geometry).filter(Boolean); }
        if (W.KPCB && W.KPCB.usKey) { const k = await W.KPCB.usKey(ref, [code]); return k && k.state === 'ok' ? (k.fs || []).map(f => f.geometry).filter(g => g && /Polygon/.test(g.type)) : []; }
      } catch (e) {}
      return [];
    })();
    return outlineP[ref];
  }
  /* all the checks for one place */
  async function checkPlace(p, code, ctx) {
    const pt = (p.geoms[0] && samples(p.geoms[0], 5)[0]) || null;
    const box = p.geoms.map(bbox).filter(Boolean).reduce((a, b) => a ? [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])] : b, null);
    const c = { acc: p.acc, cat: p.cat, own: p.owner, same: [], cover: [], pinIn: [], named: [], nearest: null };
    p.ids.forEach(id => (ctx.rev[String(id)] || []).forEach(r => { if (c.same.indexOf(r) < 0) c.same.push(r); }));
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
        const gs = await outline(x.q.ref, code); if (!gs.length) continue;
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
    const places = groupRecords(recs).slice(0, MAX_PLACES);
    if (say) say('Getting the boundaries of ' + places.length + ' places\u2026');
    const sh = await shapes(code, places.flatMap(p => p.ids)); places.forEach(p => { if (!p.geoms.length) p.geoms = p.ids.map(id => sh[id]).filter(Boolean); });
    let n = 0; for (const p of places) { await checkPlace(p, code, ctx); n++; if (say && n % 15 === 0) say('Checked ' + n + ' of ' + places.length + '\u2026'); }
    return { places, kind: CP_LOC[code] ? 'ca' : 'pad', source: CP_LOC[code] ? 'CPCAD, December 2025 edition' : 'USGS PAD-US 4.0',
      note: CP_LOC[code] ? 'The largest ' + places.length + ' protected areas in CPCAD for this province. CPCAD does not say if the public can go in, so access stays unknown until you check.' : 'The largest ' + places.length + ' places of public land open to the public (PAD-US fee land, 20 acres or more).' };
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
    if (!rmap) { const el = $('mrDrop') || $('mrRsMap'); if (!el) return;
      rmap = L.map(el, { scrollWheelZoom: false }).setView([39.8, -90], 4);
      if (W.KPCLayers) W.KPCLayers(rmap, 'Street'); else L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '\u00a9 OpenStreetMap contributors, ODbL' }).addTo(rmap); }
    rlayer = L.featureGroup().addTo(rmap);
    rmap.on('click', e => { const t = e.originalEvent && e.originalEvent.target; if (t && t.closest && t.closest('.leaflet-control, .leaflet-popup')) return; lastPin = [e.latlng.lat, e.latlng.lng]; drawPin(); if (tab !== 'pin') setTab('pin'); say('Pin dropped. Tap SEARCH to check the official land around it.'); });
    setTimeout(() => rmap && rmap.invalidateSize(), 80);
  }
  let pinMk = null, shared = false;
  /* scroll the details panel only (never the page) so the map stays where it is */
  function inPanel(el, block) { if (!el) return; const P = $('mrPanel'); if (P && P.contains(el) && P.scrollHeight > P.clientHeight + 2) { P.scrollTop += el.getBoundingClientRect().top - P.getBoundingClientRect().top - (block === 'center' ? Math.max(0, (P.clientHeight - el.offsetHeight) / 2) : 0); return; } if (!P) try { el.scrollIntoView({ behavior: 'smooth', block: block || 'start' }); } catch (e) {} }
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
      + '<ol class="mr-rs-steps">' + ST.steps.map(x => '<li class="' + x.st + '">' + esc(x.label) + (x.note ? '<small>' + esc(x.note) + '</small>' : '') + '</li>').join('') + '</ol>'
      + (slow ? '<p class="mr-rs-slow">Still waiting on the official server. Big states can take a minute or two; nothing is broken.</p>' : '')
      + (ST.err ? '<p class="mr-rs-err">' + esc(ST.err) + '</p><div class="mr-check-btns"><button type="button" id="mrRsRetry">TRY AGAIN</button></div>' : '');
    const r = $('mrRsRetry'); if (r) r.onclick = () => (ST.kind === 'ids' ? (ST.err = '', stDraw()) : run(ST.kind));
  }
  function stBegin(title, kind) {
    const el = stEl(); ST.t0 = Date.now(); ST.steps = []; ST.title = title; ST.err = ''; ST.kind = kind;
    if (el) { el.hidden = false; el.classList.remove('done', 'err'); }
    clearInterval(ST.timer); ST.timer = setInterval(stDraw, 1000); stDraw();
  }
  function stStep(label, total) { ST.steps.forEach(x => { if (x.st === 'run') x.st = 'ok'; }); const x = { label, st: 'run', n: 0, total: total || 0, at: Date.now(), note: '' }; ST.steps.push(x); stDraw(); return x; }
  function stCount(x, n, note) { if (!x) return; x.n = n; x.note = note || (x.total ? n.toLocaleString('en-US') + ' / ' + x.total.toLocaleString('en-US') : ''); stDraw(); }
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
  function card(p, i) {
    const X = W.KPCMapExtras, c = p.checks || {};
    const official = p.kind === 'pad' ? (X && X.padCard ? X.padCard(p.a) : '') : (X && X.caCard ? X.caCard(p.a) : '');
    const lines = [];
    if (c.same.length) lines.push('Same official record as: ' + c.same.join(', '));
    (c.cover || []).forEach(x => lines.push('Park outline over it: ' + x.ref + ' covers ' + Math.round(x.share * 100) + '%'));
    if (c.pinIn.length) lines.push('POTA pin inside it: ' + c.pinIn.join(', '));
    (c.named || []).forEach(x => lines.push('Same name: ' + x.ref + ', ' + x.km.toFixed(1) + ' km'));
    lines.push('Nearest POTA park: ' + (c.nearest ? c.nearest.ref + ' ' + c.nearest.name + ', ' + c.nearest.km.toFixed(1) + ' km' : 'none within about 60 km'));
    return '<details class="mr-rs-card mr-rs-' + p.verdict.v + '" data-rs="' + i + '"><summary><span class="mr-rs-v">' + esc(p.verdict.label) + '</span><b>' + esc(p.name) + '</b><small>'
      + esc([p.designation, p.manager].map(x => String(x || '').trim()).concat([ p.acres ? Math.round(p.acres).toLocaleString('en-US') + ' acres' : '']).filter(Boolean).join(' \u00b7 ')) + '</small></summary>'
      + '<p class="mr-rs-why">' + esc(p.verdict.why) + '</p>'
      + '<div class="mr-rs-checks"><b>Checks</b><ul>' + lines.map(l => '<li>' + esc(l) + '</li>').join('') + '</ul></div>'
      + official
      + '<p class="mr-rs-links"><a href="' + esc(p.link) + '" target="_blank" rel="noopener">OFFICIAL RECORD \u203a</a> <button type="button" class="mr-ag" data-rscheck="' + i + '">FULL RULES CHECK</button></p>'
      + '<label class="mr-rs-sumlab">Summary for a park submission (copy and edit)</label><textarea class="mr-rs-sum" readonly rows="9" id="mrRsSum' + i + '">' + esc(summaryText(p)) + '</textarea>'
      + '<button type="button" class="mr-ag" data-rscopy="' + i + '">COPY SUMMARY</button></details>';
  }
  function paint() {
    const out = $('mrRsOut'); if (!out) return;
    const n = { new: 0, person: 0, probably: 0, already: 0 }; rows.forEach(p => n[p.verdict.v]++);
    const lab = { new: 'Looks new', person: 'Needs a person', probably: 'Probably already a park', already: 'Already a park', all: 'All' };
    const show = rows.map((p, i) => [p, i]).filter(([p]) => filt === 'all' || p.verdict.v === filt);
    out.innerHTML = '<div class="mr-filters" id="mrRsFilters">' + ['new', 'person', 'probably', 'already', 'all'].map(k => '<button type="button" class="mr-ag' + (k === filt ? ' on' : '') + '" data-rsf="' + k + '">' + lab[k] + ' \u00b7 ' + (k === 'all' ? rows.length : n[k]) + '</button>').join('') + '</div>'
      + (show.length ? show.map(([p, i]) => card(p, i)).join('') : '<p class="mr-help">None in this group.</p>');
    out.querySelectorAll('[data-rsf]').forEach(b => b.onclick = () => { filt = b.dataset.rsf; paint(); });
    /* clicking a result (its summary) focuses the one map on it; no separate map button */
    out.querySelectorAll('details[data-rs]').forEach(d => d.addEventListener('toggle', () => { if (d.open) focus(+d.dataset.rs); }));
    out.querySelectorAll('[data-rscopy]').forEach(b => b.onclick = () => { const t = $('mrRsSum' + b.dataset.rscopy); if (!t) return; t.select(); (navigator.clipboard ? navigator.clipboard.writeText(t.value) : Promise.reject()).then(() => { b.textContent = 'COPIED'; }).catch(() => { try { D.execCommand('copy'); b.textContent = 'COPIED'; } catch (e) {} }); });
    out.querySelectorAll('[data-rscheck]').forEach(b => b.onclick = () => {   /* hand the place to "Check a place" (the full rules checklist) */
      const p = rows[+b.dataset.rscheck]; if (!p || !p.pt) return;
      const st = $('mrCheckSt'); if (st && [...st.options].some(o => o.value === placeCode())) { st.value = placeCode(); st.dispatchEvent(new Event('change')); }
      if ($('mrCheckQ')) $('mrCheckQ').value = p.name;
      if (W.KPCMapCheck && W.KPCMapCheck.showPoint) W.KPCMapCheck.showPoint(p.pt[0], p.pt[1]);
      inPanel($('mrSpot'), 'start');
    });
    draw(show.map(([p]) => p), false);
  }
  async function context(code) {
    const [key, P] = await Promise.all([keyFile(code), pins()]);
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
  async function run(kind) {
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
      let recs = [];
      if (kind === 'state') { step = stStep('Loading ' + src + ' for ' + code + '\u2026'); recs = await statewide(code, say); }
      else if (kind === 'pin') { step = stStep('Loading ' + src + ' around the pin\u2026'); say('Reading official land around the pin\u2026'); recs = await near(code, lastPin[0], lastPin[1], 6); }
      else { step = stStep('Looking for \u201c' + q0 + '\u201d in ' + src + '\u2026'); say('Looking for \u201c' + q0 + '\u201d in the official records\u2026'); recs = await byName(code, q0); if (!recs.length && lastPin) recs = (await near(code, lastPin[0], lastPin[1], 10)).filter(r => sameName(r.name, q0) || norm(r.name).indexOf(norm(q0)) >= 0); }
      let places = groupRecords(recs).slice(0, kind === 'state' ? MAX_PLACES : 40);
      stCount(step, 0, recs.length.toLocaleString('en-US') + ' records \u00b7 ' + places.length + ' places');
      if (!places.length) { rows = []; paint(); say('No official records came back for that. Try another name, drop a pin, or check the spelling.'); stEnd(false, 'No official records came back for that. Try another name, drop a pin, or check the spelling.'); busy = false; return; }
      if (places.some(p => !p.geoms.length)) {
        step = stStep('Getting the boundaries of ' + places.length + ' places\u2026');
        say('Getting the boundaries of ' + places.length + ' places\u2026');
        const sh = await shapes(code, places.flatMap(p => p.ids)); places.forEach(p => { if (!p.geoms.length) p.geoms = p.ids.map(id => sh[id]).filter(Boolean); });
      }
      step = stStep('Checking against key outlines, pins and names\u2026', places.length);
      let done = 0;
      for (const p of places) { await checkPlace(p, code, ctx); done++; stCount(step, done); if (done % 10 === 0) say('Checked ' + done + ' of ' + places.length + '\u2026'); }
      places.sort((a, b) => (RANK[a.verdict.v] - RANK[b.verdict.v]) || b.acres - a.acres);
      rows = places; filt = rows.some(p => p.verdict.v === 'new') ? 'new' : 'all';
      const n = rows.filter(p => p.verdict.v === 'new').length, c = { person: 0, probably: 0, already: 0 }; rows.forEach(p => { if (p.verdict.v in c) c[p.verdict.v]++; });
      say(rows.length + ' places checked' + (kind === 'state' ? (CP_LOC[code] ? ' (the largest ' + rows.length + ' protected areas in CPCAD; CPCAD does not say if the public can go in, so check access)' : ' (the largest ' + rows.length + ' that are open to the public)') : '') + ': ' + n + ' look new. Tap one for the checks, the official record and a summary to copy.');
      paint(); draw(rows, true);
      stEnd(true, 'Done: ' + rows.length + ' places checked \u00b7 ' + n + ' look new \u00b7 ' + c.person + ' need a person \u00b7 ' + (c.probably + c.already) + ' already parks');
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
    const det = $('mrResearch'); if (det) { mountMap(); }
    D.addEventListener('click', e => { const t = e.target && e.target.closest && e.target.closest('[data-rstest]'); if (!t) return; e.preventDefault();
      const st = $('mrCheckSt'); testIds((st && st.value) || placeCode(), String(t.dataset.rstest).split(',').filter(Boolean), t.dataset.rsname || ''); });
  }
  if (D) { const go = () => { const app = $('mrApp'); if (app && app.hidden) { setTimeout(go, 300); return; } wire(); }; if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', go); else go(); }
  W.KPCResearch = { verdict, sameName, nameKey, norm, coverShare, samples, inside, bbox, groupRecords, summaryText, nearestKm, padRec, caRec, checkPlace, classify, run, testIds, setTab, PADUS_LAYER, CPCAD_LAYER, CP_LOC };
  if (typeof module !== 'undefined' && module.exports) module.exports = W.KPCResearch;
})();
