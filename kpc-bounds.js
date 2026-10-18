/* KPC shared boundary helpers (kpc-in-park.html "Am I in the Park?" and kpc-kit.html Activation Kit).
   - Kentucky: the official boundary files KPC keeps (same ones Park Commander uses), plus KPC-drawn outlines.
   - Anywhere in the US: USGS PAD-US (Protected Areas Database), The National Map (CORS ok, no key).
   - Nearby POTA parks: api.pota.app/park/grids (CORS *).
   - Last resort: OpenStreetMap via Overpass (volunteer map, NOT official).
   window.KPCB */
(function () {
  'use strict';
  const PADUS = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query';
  const OVER = ['https://overpass-api.de/api/interpreter', 'https://overpass.private.coffee/api/interpreter'];
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  async function jget(u, opt, ms) { const c = new AbortController(), t = setTimeout(() => c.abort(), ms || 25000); try { const r = await fetch(u, Object.assign({ signal: c.signal }, opt || {})); if (!r.ok) throw new Error('HTTP ' + r.status); return await r.json(); } finally { clearTimeout(t); } }

  /* ---------- geometry ---------- */
  function ringsOf(g) { if (!g) return []; if (g.type === 'Polygon') return [g.coordinates]; if (g.type === 'MultiPolygon') return g.coordinates; return []; }
  function linesOf(g) { if (!g) return []; if (g.type === 'LineString') return [g.coordinates]; if (g.type === 'MultiLineString') return g.coordinates; const o = []; ringsOf(g).forEach(p => p.forEach(r => o.push(r))); return o; }
  function inRing(x, y, r) { let ins = false; for (let i = 0, j = r.length - 1; i < r.length; j = i++) { const xi = r[i][0], yi = r[i][1], xj = r[j][0], yj = r[j][1]; if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi) ins = !ins; } return ins; }
  function inside(lat, lon, g) { for (const poly of ringsOf(g)) { if (!poly.length || !inRing(lon, lat, poly[0])) continue; if (poly.slice(1).some(h => inRing(lon, lat, h))) continue; return true; } return false; }
  /* nearest point on the outline: {km, lat, lon} */
  function edge(lat, lon, g) {
    const sx = 111.195 * Math.cos(lat * Math.PI / 180), sy = 111.195; let best = { km: Infinity, lat, lon };
    for (const pts of linesOf(g)) for (let i = 1; i < pts.length; i++) {
      const a = pts[i - 1], b = pts[i], dx = (b[0] - a[0]) * sx, dy = (b[1] - a[1]) * sy, x = (lon - a[0]) * sx, y = (lat - a[1]) * sy;
      const t = Math.max(0, Math.min(1, (x * dx + y * dy) / ((dx * dx + dy * dy) || 1))), d = Math.hypot(x - t * dx, y - t * dy);
      if (d < best.km) best = { km: d, lon: a[0] + t * (b[0] - a[0]), lat: a[1] + t * (b[1] - a[1]) };
    }
    return best;
  }
  function bbox(g) { let a = [180, 90, -180, -90]; for (const l of linesOf(g)) for (const [x, y] of l) { if (x < a[0]) a[0] = x; if (y < a[1]) a[1] = y; if (x > a[2]) a[2] = x; if (y > a[3]) a[3] = y; } return a; }
  const km = (la1, lo1, la2, lo2) => { const r = Math.PI / 180, a = Math.sin((la2 - la1) * r / 2) ** 2 + Math.cos(la1 * r) * Math.cos(la2 * r) * Math.sin((lo2 - lo1) * r / 2) ** 2; return 12742 * Math.asin(Math.sqrt(a)); };
  function dir(la1, lo1, la2, lo2) { const r = Math.PI / 180, y = Math.sin((lo2 - lo1) * r) * Math.cos(la2 * r), x = Math.cos(la1 * r) * Math.sin(la2 * r) - Math.sin(la1 * r) * Math.cos(la2 * r) * Math.cos((lo2 - lo1) * r); const b = (Math.atan2(y, x) / r + 360) % 360; return ['north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west', 'north-west'][Math.round(b / 45) % 8]; }
  const dist = k => { const ft = k * 3280.84; return ft < 1000 ? Math.round(ft / 10) * 10 + ' ft' : (k * 0.621371).toFixed(k * 0.621371 < 10 ? 1 : 0) + ' mi'; };

  /* ---------- names ---------- */
  const norm = s => String(s || '').toLowerCase().replace(/&/g, ' and ').replace(/wildlife management area|state nature preserve|state natural area|state resort park|state historic site|state recreation area|national wildlife refuge|national recreation area|national historical park|national historic site|national park|national forest|state park|state forest|wma|nwr|the |[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim();
  /* what kind of place a name describes; two names of different kinds (a WMA and a state park on the same lake) are NOT the same place */
  const kindOf = s => { s = String(s || '').toLowerCase(); return /wildlife management area|\bwma\b|wildlife area|hunting area|game (land|area)/.test(s) ? 'wma' : /nature preserve|natural area|\bsnp\b|\bsna\b/.test(s) ? 'snp' : /historic site|historical park|historic park|\bshs\b/.test(s) ? 'hist' : /state (resort )?park|\bsrp\b|recreation(al)? area/.test(s) ? 'sp' : /national forest/.test(s) ? 'nf' : /state forest/.test(s) ? 'sf' : /wildlife refuge|\bnwr\b/.test(s) ? 'nwr' : /hatchery|\bnfh\b/.test(s) ? 'nfh' : /national (park|monument|preserve|seashore|lakeshore|battlefield|river)/.test(s) ? 'nps' : ''; };
  /* every kind a name names ('X State Forest and WMA' = forest AND wma), so a combined name matches either park (Oct 18: Marrowbone SF) */
  const KINDS = [['wma', /wildlife management area|\bwma\b|wildlife area|hunting area|game (land|area)/], ['snp', /nature preserve|natural area|\bsnp\b|\bsna\b/], ['hist', /historic site|historical park|historic park|\bshs\b/], ['sp', /state (resort )?park|\bsrp\b|recreation(al)? area/], ['nf', /national forest/], ['sf', /state forest/], ['nwr', /wildlife refuge|\bnwr\b/], ['nfh', /hatchery|\bnfh\b/], ['nps', /national (park|monument|preserve|seashore|lakeshore|battlefield|river)/]];
  const kindsOf = s => { s = String(s || '').toLowerCase(); return KINDS.filter(([, r]) => r.test(s)).map(([k]) => k); };
  const sameKind = (a, b) => { const x = kindsOf(a), y = kindsOf(b); return !x.length || !y.length || x.some(k => y.includes(k)); };
  function sameName(a, b) { a = norm(a); b = norm(b); if (!a || !b) return false; if (a === b) return true; const s = a.length < b.length ? a : b, l = a.length < b.length ? b : a; return s.length > 5 && l.startsWith(s) && s.length / l.length >= 0.6; }

  /* ---------- Kentucky official layers (same files as Park Commander) ---------- */
  const KY = [
    ['bstate', 'State Parks', 'Kentucky State Parks', 'ky-state-parks.geojson'],
    ['bwma', 'WMAs & Public Hunting Areas', 'Kentucky Fish & Wildlife', 'ky-hunting-areas.geojson'],
    ['bsnp', 'State Nature Preserves', 'Kentucky Office of Nature Preserves', 'ky-nature-preserves.geojson'],
    ['bsna', 'State Natural Areas', 'Kentucky Office of Nature Preserves', 'ky-natural-areas.geojson'],
    ['bdbnf', 'Daniel Boone National Forest', 'U.S. Forest Service', 'ky-dbnf.geojson', 'This is the forest’s outer (proclamation) line. It includes private land and towns, so it does not prove the spot is Forest Service land.'],
    ['bnps', 'National Park Service', 'National Park Service', 'ky-nps.geojson'],
    ['bwild', 'Wild River Corridors', 'Kentucky Office of Nature Preserves', 'ky-wild-rivers.geojson'],
    ['bwilder', 'Wilderness Areas', 'U.S. Forest Service', 'ky-wilderness.geojson', 'Federal wilderness: no motorized equipment (generators), group size limits.'],
    ['bfws', 'Wildlife Refuges & Fish Hatcheries', 'U.S. Fish & Wildlife Service', 'ky-fws.geojson', 'Some refuge areas close by season. Check the refuge page.'],
    ['bpad', 'Official outline (USGS PAD-US)', 'USGS PAD-US (official land records)', 'ky-padus-parks.geojson'],
    ['bkpc', 'KPC-drawn outline', 'Kentucky Portable Club (from OpenStreetMap)', 'ky-kpc-drawn.geojson', 'Approximate outline drawn by KPC from OpenStreetMap because this park has no official map file. Not official.']
  ].map(([k, name, agency, file, note]) => ({ k, name, agency, file, note, kpc: k === 'bkpc', proc: k === 'bdbnf' }));
  const ALIAS = {"Ohio River Islands National Wildlife Refuge": ["US-0608"], "Livingston County Wildlife Management Area and State Nature Preserve (Bissell Bluff SNP)": ["US-3823"], "Livingston County Wildlife Management Area and State Nature Preserve (Newman's Bluff SNP)": ["US-3823"], "Blue Licks State Park State Nature Preserve": ["US-1274"], "Knobs State Forest and WMA": ["US-4690"], "Little South Fork State Natural Area (Steele Hollow SNA)": ["US-7962"], "Clifty Wilderness": ["US-3801"], "Big South Fork National River and Recreation Area": ["US-0686"], "Bad Branch Wild River": ["US-10112"], "Big South Fork Wild River": ["US-10107"], "Cumberland River Wild River": ["US-10103"], "Green River Wild River": ["US-10105"], "Rock Creek Wild River": ["US-10111"], "Red River Wild River": ["US-10104"], "Rockcastle River Wild River": ["US-10106"], "Mammoth Cave National Park": ["US-0050"], "Abraham Lincoln Birthplace National Historical Park": ["US-0724"], "Camp Nelson National Monument": ["US-7950"], "Mill Springs Battlefield National Monument": ["US-7708"], "Cumberland Gap National Historical Park": ["US-0019"], "Fort Donelson National Battlefield": ["US-0703", "US-3790"], "Jefferson National Forest": ["US-4526", "US-10139"], "Pine Mountain State Scenic Trail": ["US-10102"], "Clay WMA": ["US-10124"], "Horsemill Branch WMA": ["US-11274"], "Little Sexton Creek WMA": ["US-12079"], "General Burnside Island State Park": ["US-1257"], "Green River State Natural Area (Rush Island Bottoms)": ["US-12752"], "Green River State Natural Area (Davis Bend)": ["US-12752"], "Dale Hollow Lake State Resort Park": ["US-1278"], "Big Rivers WMA and State Forest": ["US-3796"], "Marion County WMA and State Forest": ["US-3824"], "Miller Welch-Central Kentucky WMA": ["US-3825"], "Vernon-Douglas State Nature Preserve": ["US-7957"], "Dr. William H. Martin State Natural Area": ["US-7964"], "Otter Creek Outdoor Recreation Area": ["US-8144"], "Kentucky Ridge Forest WMA": ["US-10141"], "Tom Dorman State Nature Preserve": ["US-7958"]};
  const inKY = (la, lo) => la > 36.45 && la < 39.2 && lo > -89.6 && lo < -81.9;
  let kyFeat = null, kyData = null;
  async function ky() {
    if (!kyData) kyData = await jget('kpc-ky-data.json').catch(() => ({ parks: [], kff: [], summits: [] }));
    if (kyFeat) return kyFeat;
    const out = [];
    await Promise.all(KY.map(async L => { try { const j = await jget(L.file + '?v=20261018q', { cache: 'force-cache' }); (j.features || []).forEach(f => { if (!ringsOf(f.geometry).length) return; f._L = L; f._bb = bbox(f.geometry); f._nm = (f.properties || {}).NAME || L.name; out.push(f); }); } catch (e) {} }));
    kyFeat = out; byName = null; return out;
  }
  /* which POTA refs a KY boundary belongs to: by name (or KPC's alias list) first; "the park's pin is inside it" only
     for parks that have no boundary matched by name (so a river corridor around a state park doesn't count as the state park) */
  let byName = null;
  function nameIndex() {
    if (byName) return byName; byName = new Map();
    const P = kyData && kyData.parks || [];
    for (const f of kyFeat || []) {
      const p = f.properties || {}, b = f._bb, m = new Set();
      if (p.ref) m.add(p.ref);
      (ALIAS[f._nm] || []).forEach(r => m.add(r));
      /* Oct 17 (Brandon: Yatesville Lake SP was taking Yatesville Lake WMA; Little South Fork SNA took the Wild River): a name match also needs the same KIND
         of place, and a Wild River corridor only matches a wild / scenic river park */
      for (const x of P) if (sameName(x.n, f._nm) && (sameKind(x.n, f._nm) || /state (resort )?park state nature preserve/i.test(f._nm)) && (f._L.k !== 'bwild' || /wild|scenic river/i.test(x.n)) && x.lo >= b[0] - .5 && x.lo <= b[2] + .5 && x.la >= b[1] - .5 && x.la <= b[3] + .5) m.add(x.c);
      f._names = m; m.forEach(r => byName.set(r, (byName.get(r) || []).concat(f)));
    }
    return byName;
  }
  function kyRefs(f) {
    const N = nameIndex(), P = kyData && kyData.parks || [], out = new Map(), b = f._bb;
    (f._names || []).forEach(r => { const x = P.find(q => q.c === r); if (x) out.set(r, x); });
    if (!f._L.proc && f._L.k !== 'bwilder') for (const x of P) {
      if (out.has(x.c) || N.has(x.c)) continue;
      if (x.lo >= b[0] - .02 && x.lo <= b[2] + .02 && x.la >= b[1] - .02 && x.la <= b[3] + .02 && inside(x.la, x.lo, f.geometry)) out.set(x.c, x);
    }
    return [...out.values()].map(x => ({ ref: x.c, name: x.n, la: x.la, lo: x.lo }));
  }

  /* Oct 17 (Brandon: 'click a boundary … tell you the name, WMA tract etc.'; the SHARED 'no park number' check for every tool):
     landInfo(f) = what one KY outline is for all three programs; landAt(lat, lon) = every KY outline at a spot (inside, or within ~25 m of its line) */
  function landInfo(f) {
    nameIndex(); const D = kyData || {}, P = D.parks || [], b = f._bb;
    const own = [...(f._names || [])].map(r => P.find(q => q.c === r)).filter(Boolean).map(x => ({ ref: x.c, name: x.n }));
    const pins = own.length ? [] : kyRefs(f).filter(r => !own.some(o => o.ref === r.ref));
    const inB = (la, lo) => lo >= b[0] && lo <= b[2] && la >= b[1] && la <= b[3] && inside(la, lo, f.geometry);
    const kff = [], kffIn = [], sota = [];
    (D.kff || []).forEach(k => { if (!k.p && sameName(k.n, f._nm)) kff.push({ ref: k.c, name: k.n }); else if (inB(k.la, k.lo)) kffIn.push({ ref: k.c, name: k.n, p: k.p }); });
    (D.summits || []).forEach(x => { if (inB(x.la, x.lo)) sota.push({ ref: x.c, name: x.n, ft: x.ft }); });
    return { name: f._nm, layer: f._L.name, k: f._L.k, own, pins, kff, kffIn, sota, numbered: own.length > 0 || kff.length > 0, props: f.properties || {} };
  }
  async function landAt(lat, lon) {
    const F = await ky(), out = [];
    for (const f of F) { const b = f._bb; if (lon < b[0] - .001 || lon > b[2] + .001 || lat < b[1] - .001 || lat > b[3] + .001) continue;
      const inn = inside(lat, lon, f.geometry), e = inn ? null : edge(lat, lon, f.geometry);
      if (inn || (e && e.km < .025)) out.push(Object.assign(landInfo(f), { f, onLine: !inn })); }
    const area = x => (x.f._bb[2] - x.f._bb[0]) * (x.f._bb[3] - x.f._bb[1]);
    return out.sort((a, b) => area(a) - area(b));
  }
  /* KY features that belong to one POTA ref */
  async function kyFor(ref) { const F = await ky(); const N = nameIndex(); return N.has(ref) ? N.get(ref) : F.filter(f => kyRefs(f).some(r => r.ref === ref)); }

  /* ---------- PAD-US ---------- */
  const ACCESS = { OA: 'open to the public', RA: 'restricted access (permit or season)', XA: 'CLOSED to the public', UK: 'access unknown' };
  async function padus(params) { const q = Object.assign({ where: '1=1', inSR: 4326, spatialRel: 'esriSpatialRelIntersects', outFields: 'OBJECTID,Unit_Nm,Loc_Nm,Mang_Name,Loc_Mang,Des_Tp,Pub_Access,GIS_Acres,Category', outSR: 4326, f: 'geojson' }, params); return jget(PADUS + '?' + new URLSearchParams(q)); }
  /* public land around a point (box of +-d degrees), geometry simplified by size */
  async function padusArea(la, lo, d) {
    const meta = await padus({ geometry: `${lo - d},${la - d},${lo + d},${la + d}`, geometryType: 'esriGeometryEnvelope', returnGeometry: false });
    const fs = (meta.features || []).map(f => f.properties || {}).filter(p => p.Category !== 'Proclamation');
    if (!fs.length) return [];
    const A = p => +p.GIS_Acres || 0, env = `${lo - d},${la - d},${lo + d},${la + d}`;
    const tiers = [[fs.filter(p => A(p) < 20000), 0.00004, false], [fs.filter(p => A(p) >= 20000 && A(p) < 200000), 0.00015, true], [fs.filter(p => A(p) >= 200000), 0.0003, true]];
    const parts = await Promise.all(tiers.map(([list, off, box]) => list.length ? padus(Object.assign({ objectIds: list.map(p => p.OBJECTID).join(','), returnGeometry: true, geometryPrecision: 5, maxAllowableOffset: off }, box ? { geometry: env, geometryType: 'esriGeometryEnvelope' } : {})).then(j => j.features || []) : []));
    return parts.flat().filter(f => f.geometry).map(f => { f._nm = f.properties.Unit_Nm || f.properties.Loc_Nm || 'Public land'; f._bb = bbox(f.geometry); return f; });
  }
  const words = n => String(n || '').replace(/\b(state|national|park|parks|forest|wildlife|management|area|recreation|recreational|nature|preserve|refuge|historic|historical|site|reserve|natural|lake|wma|nwr|the|of|and)\b/gi, ' ').replace(/[^A-Za-z0-9' ]/g, ' ').trim().split(/\s+/).filter(w => w.length > 2);
  async function padusByName(name, la, lo) {
    const w = words(name), d = 0.35; if (!w.length) return [];
    /* PAD-US firewall: one plain LIKE only (no UPPER/OR/AND), so ask Title Case, CAPITALS and as typed, then merge */
    const ws = w.slice(0, 2), pat = f => ('%' + ws.map(f).join('%') + '%').replace(/'/g, '%');
    const wh = [...new Set([`Unit_Nm LIKE '${pat(x => x.charAt(0).toUpperCase() + x.slice(1).toLowerCase())}'`, `Loc_Nm LIKE '${pat(x => x.toUpperCase())}'`, `Unit_Nm LIKE '${pat(x => x)}'`])];
    const gs = await Promise.all(wh.map(where => padus({ where, geometry: `${lo - d},${la - d},${lo + d},${la + d}`, geometryType: 'esriGeometryEnvelope', returnGeometry: true, geometryPrecision: 5, maxAllowableOffset: 0.0001 }).catch(() => ({ features: [] }))));
    const seen = new Set(); const g = { features: gs.flatMap(x => x.features || []).filter(f => { const k = f.id != null ? f.id : (f.properties || {}).OBJECTID; if (k != null && seen.has(k)) return false; seen.add(k); return true; }) };
    let fs = (g.features || []).filter(f => f.geometry && f.properties.Category !== 'Proclamation'); if (!fs.length) return [];
    const nl = String(name).toLowerCase();
    fs.forEach(f => { const u = String(f.properties.Unit_Nm || '').toLowerCase(); f._s = (u.includes(nl) || nl.includes(u) ? 5 : 0) + w.filter(x => u.includes(x.toLowerCase())).length; });
    const top = Math.max(...fs.map(f => f._s)); fs = fs.filter(f => f._s === top); const un = fs[0].properties.Unit_Nm;
    return fs.filter(f => f.properties.Unit_Nm === un).map(f => { f._nm = un; f._bb = bbox(f.geometry); return f; });
  }
  /* ---------- Europe (Brandon Oct 17: 'europe next'): official outlines asked live from the European Environment Agency
     (EEA, CORS ok for our site, checked Oct 17): Natura 2000 sites (EU Habitats + Birds directives) and the Nationally
     designated areas inventory (NatDA, ex-CDDA: national parks, nature parks, reserves… for 38 countries; NOT the UK).
     Point query at the pin (then ~1 km around it), best NAME match only (never a different place), outline by OBJECTID. ---------- */
  const EEA = 'https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/';
  const EUL = { n2k: EEA + 'Natura2000Sites/MapServer/2/query', nat: EEA + 'CDDA_Dyna_WM/MapServer/4/query' };
  const inEurope = (la, lo) => la > 34 && la < 72 && lo > -32 && lo < 45;
  const EUGEN = /\b(national|nationalpark|national park|nature|natural|naturale|natura|naturpark|naturschutzgebiet|landschaftsschutzgebiet|nsg|lsg|ffh|spa|sac|sci|park|parks|parc|parco|parque|park krajobrazowy|krajobrazowy|rezerwat|obszar|chronionego|krajobrazu|regional|régional|regionale|nazionale|nacional|national|reserve|réserve|riserva|reserva|naturreservat|nationalpark|area|site|zone|zona|sito|historic|historical|biological|recreation|protected|landscape|heritage|world|conservation|marine|other|monument|trail|the|of|and|de|del|della|di|du|des|la|le|les|der|die|das|von|im|am|en|et|y|e|i|och|og|san|saint|sankt|st)\b/g;
  const deacc = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const euWords = s => deacc(s).replace(/["'„“”«»]/g, ' ').replace(/[^a-z0-9 ]/g, ' ').replace(/\b[a-z]{2}\d{4,}\b|\b\d+\b/g, ' ').replace(EUGEN, ' ').split(/\s+/).filter(w => w.length > 2);
  const euSim = (a, b) => { const A = euWords(a), B = new Set(euWords(b)); if (!A.length || !B.size) return 0; const hit = A.filter(w => B.has(w) || [...B].some(x => x.length > 4 && w.length > 4 && (x.startsWith(w.slice(0, 5)) || w.startsWith(x.slice(0, 5))))).length; return hit / Math.max(A.length, B.size); };
  async function euAt(url, la, lo, d, fields) {
    const q = d ? { geometry: `${lo - d},${la - d},${lo + d},${la + d}`, geometryType: 'esriGeometryEnvelope' } : { geometry: `${lo},${la}`, geometryType: 'esriGeometryPoint' };
    const j = await jget(url + '?' + new URLSearchParams(Object.assign(q, { inSR: 4326, spatialRel: 'esriSpatialRelIntersects', outFields: fields, returnGeometry: false, f: 'json' })), null, 25000).catch(() => null);
    return (j && j.features || []).map(f => f.attributes);
  }
  async function euro(name, la, lo, o) {
    o = o || {}; if (!inEurope(la, lo)) return [];
    const N2F = 'OBJECTID,SITECODE,SITENAME,SITETYPE,Area_ha,MS', NAF = 'OBJECTID,siteName,designationTypeCode,iucnCategory,siteArea,countryCode,nationalId';
    let C = [];
    for (const d of [0, 0.01]) {
      const [a, b] = await Promise.all([euAt(EUL.n2k, la, lo, d, N2F), euAt(EUL.nat, la, lo, d, NAF)]);
      C = C.concat(a.map(x => ({ d, L: 'n2k', id: x.OBJECTID, nm: x.SITENAME, ha: +x.Area_ha || 0, code: x.SITECODE, info: 'Natura 2000 site ' + x.SITECODE + ' (' + ({ A: 'EU Birds Directive', B: 'EU Habitats Directive', C: 'EU Birds + Habitats Directives' }[x.SITETYPE] || 'EU nature network') + ')' }))
        .concat(b.map(x => ({ d, L: 'nat', id: x.OBJECTID, nm: String(x.siteName || '').replace(/^(LSG|NSG|FFH)\s+/i, '').replace(/^"|"$/g, ''), ha: +x.siteArea || 0, code: x.nationalId, info: 'Nationally designated area' + (x.iucnCategory && !/notApplicable|notReported/i.test(x.iucnCategory) ? ' · IUCN category ' + x.iucnCategory : '') + (x.countryCode ? ' · ' + x.countryCode : '') }))));
      if (o.small && C.length) break;
      if (C.some(c => euSim(name, c.nm) >= .5 || (c.d === 0 && euWords(c.nm).length && euWords(c.nm).every(w => euWords(name).includes(w))))) break;
    }
    if (!C.length) return [];
    let pick;
    if (o.small) pick = C.sort((x, y) => (x.ha || 1e12) - (y.ha || 1e12))[0];   /* a summit: the smallest protected area it sits in */
    else {
      const wantN2k = /natura\s*2000/i.test(o.type || '');
      const PW = new Set(euWords(name));
      C.forEach(c => { const mw = euWords(c.nm); let s = euSim(name, c.nm); if (c.d === 0 && mw.length && mw.some(w => w.length > 4) && mw.every(w => PW.has(w))) s = Math.max(s, .6); c.s = s + (wantN2k === (c.L === 'n2k') ? .05 : 0); });
      C.sort((x, y) => y.s - x.s || (x.ha || 1e12) - (y.ha || 1e12)); pick = C[0]; if (pick.s < .5) return [];
    }
    const off = pick.ha < 2000 ? 0.00005 : pick.ha < 50000 ? 0.0002 : 0.0005;
    const g = await jget(EUL[pick.L] + '?' + new URLSearchParams({ objectIds: pick.id, outFields: 'OBJECTID', returnGeometry: true, outSR: 4326, maxAllowableOffset: off, geometryPrecision: 5, f: 'geojson' }), null, 30000).catch(() => null);
    const fs = (g && g.features || []).filter(f => f.geometry);
    return fs.map(f => { f._nm = pick.nm; f._bb = bbox(f.geometry); f._src = pick.L === 'n2k' ? 'EEA Natura 2000' : 'EEA Nationally designated areas'; f._info = pick.info; f._ha = pick.ha; f.properties = Object.assign(f.properties || {}, { NAME: pick.nm, SOURCE: f._src, CODE: pick.code }); return f; });
  }
  /* Canada: the official outline saved by kpc-canada-bounds.yml (CPCAD or the province's map) */
  async function canada(ref) {
    if (!/^CA-\d/.test(ref || '')) return [];
    const j = await jget('data/canada-bounds/' + encodeURIComponent(ref) + '.json', null, 20000).catch(() => null); if (!j) return [];
    const fs = (j.type === 'FeatureCollection' ? j.features : [j]).filter(f => f && f.geometry);
    return fs.map(f => { const p = f.properties || {}; f._nm = p.cpcad || p.name || ref; f._bb = bbox(f.geometry); f._src = p.srcShort || 'CPCAD (Environment and Climate Change Canada)'; f._info = [p.type, p.manager].filter(Boolean).join(' · '); return f; });
  }
  /* any non-US official outline we know how to get: Canada file, then Europe */
  async function worldByName(ref, name, la, lo, o) { const c = await canada(ref); if (c.length) return c; return euro(name, la, lo, o); }
  /* POTA parks near a point */
  async function potaNear(la, lo, d) {
    const j = await jget(`https://api.pota.app/park/grids/${(la - d).toFixed(3)}/${(lo - d).toFixed(3)}/${(la + d).toFixed(3)}/${(lo + d).toFixed(3)}/0`, null, 15000);
    return (j.features || []).map(f => ({ ref: f.properties.reference, name: f.properties.name, lo: f.geometry.coordinates[0], la: f.geometry.coordinates[1] })).filter(p => km(la, lo, p.la, p.lo) < 60);
  }
  function refsFor(f, near) { return near.filter(p => sameName(p.name, f._nm) || (inside(p.la, p.lo, f.geometry) && f.properties.Category !== 'Easement')); }

  /* ---------- WWFF and SOTA near a spot (weekly copies in data/wwff/t and data/sota/t, 1x1 degree tiles) ---------- */
  const tileCache = {};
  function tilesAround(la, lo, kmR) {
    const dla = kmR / 111, dlo = kmR / (111 * Math.cos(la * Math.PI / 180)), K = new Set();
    for (const a of [la - dla, la + dla]) for (const o of [lo - dlo, lo + dlo]) K.add(Math.floor(a) + '_' + Math.floor(o));
    K.add(Math.floor(la) + '_' + Math.floor(lo)); return [...K];
  }
  async function tileRows(dir, la, lo, kmR) {
    const rows = await Promise.all(tilesAround(la, lo, kmR).map(k => { const u = dir + k + '.json'; return tileCache[u] || (tileCache[u] = fetch(u).then(r => r.ok ? r.json() : []).catch(() => [])); }));
    return rows.flat();
  }
  async function wwffNear(la, lo, kmR) { return (await tileRows('data/wwff/t/', la, lo, kmR)).map(r => ({ ref: r[0], name: r[1], la: r[2], lo: r[3], d: km(la, lo, r[2], r[3]) })).filter(x => x.d <= kmR).sort((a, b) => a.d - b.d); }
  async function sotaNear(la, lo, kmR) { return (await tileRows('data/sota/t/', la, lo, kmR)).map(r => ({ ref: r[0], name: r[1], ft: r[2], m: r[3], la: r[4], lo: r[5], pts: r[6], d: km(la, lo, r[4], r[5]) })).filter(x => x.d <= kmR).sort((a, b) => a.d - b.d); }
  /* ground height in meters: USGS (US, about 1 m) then Open-Meteo (worldwide, about 90 m grid) */
  async function elevation(la, lo) {
    try { const j = await jget(`https://epqs.nationalmap.gov/v1/json?x=${lo}&y=${la}&units=Meters&wkid=4326`, null, 12000); const v = +j.value; if (isFinite(v) && v > -500) return { m: v, src: 'USGS' }; } catch (e) {}
    try { const j = await jget(`https://api.open-meteo.com/v1/elevation?latitude=${la}&longitude=${lo}`, null, 12000); const v = +(j.elevation || [])[0]; if (isFinite(v)) return { m: v, src: 'Open-Meteo' }; } catch (e) {}
    return null;
  }
  /* any reference -> {prog, ref, name, la, lo, type, where, web, off} */
  async function lookup(q) {
    q = String(q || '').trim().toUpperCase().replace(/\s+/g, '');
    let m = q.match(/^([A-Z0-9]{1,4}\/[A-Z0-9]{2})-(\d{1,3})$/);
    if (m) { const ref = m[1] + '-' + m[2].padStart(3, '0'); const [a, r] = ref.split('/'); const s = await jget(`https://api2.sota.org.uk/api/summits/${encodeURIComponent(a)}/${encodeURIComponent(r)}`); if (!s || !s.summitCode) return null; return { prog: 'SOTA', ref: s.summitCode, name: s.name, la: +s.latitude, lo: +s.longitude, ft: s.altFt, mAlt: s.altM, pts: s.points, type: (s.altFt ? s.altFt.toLocaleString() + ' ft · ' : '') + (s.points != null ? s.points + ' points' : ''), where: s.associationName + (s.regionName ? ' · ' + s.regionName : ''), us: /^USA/.test(s.associationName || '') }; }
    m = q.match(/^([A-Z0-9]{1,4})-(\d{1,5})$/); if (!m) return null;
    if (/FF$/.test(m[1])) { const ref = m[1] + '-' + m[2].padStart(4, '0'); const rows = await jget('data/wwff/' + m[1] + '.json').catch(() => []); const x = rows.find(r => r[0] === ref); if (!x) return null; return { prog: 'WWFF', ref, name: x[1], la: x[2], lo: x[3], web: /^https?:/.test(x[4]) ? x[4] : '', type: 'WWFF reference', where: [...new Set([x[6], x[5]].filter(Boolean))].join(', '), st: String(x[5] || '').replace(/^K-/, ''), us: m[1] === 'KFF' }; }
    const ref = m[1] + '-' + m[2].padStart(4, '0'); const p = await jget('https://api.pota.app/park/' + encodeURIComponent(ref)); if (!p || !p.reference) return null;
    return { prog: 'POTA', ref, name: p.name + (p.parktypeDesc && !new RegExp(p.parktypeDesc, 'i').test(p.name) ? ' ' + p.parktypeDesc : ''), short: p.name, la: +p.latitude, lo: +p.longitude, web: p.website || '', type: p.parktypeDesc, where: p.locationName || p.locationDesc, st: String(p.locationDesc || '').split(',')[0].replace(/^US-/, ''), us: /^US-/.test(p.locationDesc || ''), ky: /^US-KY/.test(p.locationDesc || '') };
  }

  /* ---------- OpenStreetMap (volunteer map, not official) ---------- */
  const post = (u, q, ms) => jget(u, { method: 'POST', body: 'data=' + encodeURIComponent(q), headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }, ms);
  async function osmAt(la, lo) {
    const q = `[out:json][timeout:25];is_in(${la},${lo})->.a;(area.a[boundary~"^(protected_area|national_park)$"];area.a[leisure~"^(park|nature_reserve)$"];);out ids tags;`;
    let a = null; for (const u of OVER) { try { a = await post(u, q, 30000); break; } catch (e) {} }
    const el = (a && a.elements || []).filter(e => e.tags && e.tags.name); if (!el.length) return [];
    const e = el.sort((x, y) => (x.tags.boundary ? 0 : 1) - (y.tags.boundary ? 0 : 1))[0], id = e.id >= 3600000000 ? ['relation', e.id - 3600000000] : ['way', e.id - 2400000000];
    let g = null; for (const u of OVER) { try { g = await post(u, `[out:json][timeout:40];${id[0]}(${id[1]});out geom;`, 45000); break; } catch (x) {} }
    const o = g && g.elements && g.elements[0];
    const lines = !o ? [] : o.type === 'way' ? [o.geometry] : (o.members || []).filter(m => m.type === 'way' && m.role !== 'inner' && m.geometry).map(m => m.geometry);
    const geom = { type: 'MultiLineString', coordinates: lines.map(l => l.map(p => [p.lon, p.lat])) };
    return [{ _nm: e.tags.name, _osm: true, _op: e.tags.operator || '', others: el.slice(1).map(x => x.tags.name), geometry: geom, properties: { name: e.tags.name } }];
  }

  /* ---------- save a boundary as a map file (phones: share menu) ---------- */
  const xe = t => String(t == null ? '' : t).replace(/[<>&"']/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;' }[c]));
  function toKml(fc, o) {
    const pm = fc.features.map(f => ringsOf(f.geometry).map(poly => `<Placemark><name>${xe((f.properties && (f.properties.Unit_Nm || f.properties.NAME || f.properties.name)) || o.name)}</name><styleUrl>#b</styleUrl><Polygon>` + poly.map((r, n) => `<${n ? 'innerBoundaryIs' : 'outerBoundaryIs'}><LinearRing><coordinates>${r.map(c => (+c[0]).toFixed(6) + ',' + (+c[1]).toFixed(6)).join(' ')}</coordinates></LinearRing></${n ? 'innerBoundaryIs' : 'outerBoundaryIs'}>`).join('') + `</Polygon></Placemark>`).join('')).join('');
    const pts = (o.points || []).map(p => `<Placemark><name>${xe(p[2])}</name><Point><coordinates>${p[1]},${p[0]}</coordinates></Point></Placemark>`).join('');
    return `<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>${xe(o.ref + ' ' + o.name)}</name><Style id="b"><LineStyle><color>ff00b0ff</color><width>3</width></LineStyle><PolyStyle><color>3300b0ff</color></PolyStyle></Style><Placemark><name>${xe(o.ref)}</name><Point><coordinates>${o.lo},${o.la}</coordinates></Point></Placemark>${pts}${pm}</Document></kml>`;
  }
  function toGpx(fc, o) {
    let n = 0; const tr = fc.features.map(f => ringsOf(f.geometry).map(poly => `<trk><name>${xe(o.ref + ' boundary ' + (++n))}</name><trkseg>${poly[0].map(c => `<trkpt lat="${(+c[1]).toFixed(6)}" lon="${(+c[0]).toFixed(6)}"/>`).join('')}</trkseg></trk>`).join('')).join('');
    const pts = (o.points || []).map(p => `<wpt lat="${p[0]}" lon="${p[1]}"><name>${xe(p[2])}</name></wpt>`).join('');
    return `<?xml version="1.0" encoding="UTF-8"?>\n<gpx version="1.1" creator="Kentucky Portable Club" xmlns="http://www.topografix.com/GPX/1/1"><wpt lat="${o.la}" lon="${o.lo}"><name>${xe(o.ref + ' ' + o.name)}</name></wpt>${pts}${tr}</gpx>`;
  }
  async function saveGeo(fc, fmt, o, btn) {
    const T = { kml: ['application/vnd.google-earth.kml+xml', toKml], gpx: ['application/gpx+xml', toGpx], geojson: ['application/geo+json', f => JSON.stringify(f)] }[fmt];
    const name = (o.ref + '-boundary.' + fmt).replace(/[^\w.-]/g, '_'), blob = new Blob([T[1](fc, o)], { type: T[0] });
    if (matchMedia('(pointer:coarse)').matches && navigator.canShare) { try { const file = new File([blob], name, { type: T[0] }); if (navigator.canShare({ files: [file] })) { await navigator.share({ files: [file], title: o.ref + ' boundary' }); return; } } catch (e) { if (e && e.name === 'AbortError') return; } }
    const url = URL.createObjectURL(blob), a = document.createElement('a'); a.href = url; a.download = name; a.style.display = 'none'; document.body.appendChild(a); a.click(); setTimeout(() => { a.remove(); URL.revokeObjectURL(url); }, 60000);
    if (btn) { const w = btn.textContent; btn.textContent = 'SAVED ✓ (CHECK DOWNLOADS)'; setTimeout(() => btn.textContent = w, 3000); }
  }
  const WHICH = `<details class="kb-which"><summary>WHICH FILE DO I NEED? (TAP HERE)</summary><ul><li><b>iPhone or iPad:</b> tap <b>KML</b>, then pick <b>Google Earth</b> (free app) or <b>Save to Files</b>. Gaia GPS, onX and CalTopo open it too (in the app: Import).</li><li><b>Android phone:</b> tap <b>KML</b> and pick <b>Google Earth</b>, or save it and import it in Gaia GPS, onX or Google My Maps.</li><li><b>Garmin or other handheld GPS:</b> use <b>GPX</b>. Copy it into the GPS's <b>GPX</b> folder from a computer (or Garmin BaseCamp / Explore).</li><li><b>Computer:</b> <b>KML</b> opens in Google Earth, or at <b>mymaps.google.com</b> → Create a new map → Import.</li><li><b>Not sure?</b> Pick <b>KML</b>.</li></ul></details>`;
  const OSM_NOTE = 'OpenStreetMap is a free map drawn by volunteers. Its park outlines are often close, but they can be off, out of date, or missing land, and they are not official. POTA goes by the park’s official boundary, so check the park’s own map or signs, and when in doubt, set up well inside.';

  window.KPCB = { landInfo, landAt, kindOf, sameKind, tilesUsed: () => Object.keys(tileCache), wwffNear, sotaNear, elevation, lookup, esc, jget, ringsOf, linesOf, inside, edge, bbox, km, dir, dist, norm, sameName, KY, inKY, ky, kyRefs, kyFor, kyData: () => kyData, ACCESS, padusArea, padusByName, euro, canada, worldByName, inEurope, potaNear, refsFor, osmAt, saveGeo, WHICH, OSM_NOTE };
})();
