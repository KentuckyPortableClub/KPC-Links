/* KPC shared boundary helpers (kpc-in-park.html "Am I in the Park?" and kpc-kit.html Activation Kit).
   - Kentucky: the official boundary files KPC keeps (same ones Park Commander uses), plus OpenStreetMap outlines (unofficial).
   - Anywhere in the US: USGS PAD-US (Protected Areas Database), The National Map (CORS ok, no key).
   - Nearby POTA parks: api.pota.app/park/grids (CORS *).
   - Last resort: OpenStreetMap via Overpass (volunteer map, NOT official).
   window.KPCB */
(function () {
  'use strict';
  const PADUS = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query';
  const OVER = ['https://overpass-api.de/api/interpreter', 'https://overpass.private.coffee/api/interpreter'];
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  async function jget(u, opt, ms) { const c = new AbortController(), t = setTimeout(() => c.abort(), ms || 25000); try { const r = await fetch(u, Object.assign({ signal: c.signal }, opt || {})); if (!r.ok) throw new Error('HTTP ' + r.status); const j = await r.json(); if (j && Array.isArray(j.features) && /maxAllowableOffset=/.test(u)) j.features.forEach(f => { if (f && !f._url) { f._url = u; f._pk = JSON.stringify(f.properties || {}); } }); return j; } finally { clearTimeout(t); } }
  /* Storage plan Step B (Oct 27): the answer-key / outline folders below live on KentuckyPortableClub/KPC-Data now.
     dfetch/dget try that address first and fall back to this site's own copy, same as window.KPC.dataUrl (used
     directly where we only need the Response; dget adds jget's abort-timeout + JSON parsing on top of it). */
  function dfetch(u, opt) { return (window.KPC && KPC.dataUrl) ? KPC.dataUrl(u, opt) : fetch(u, opt); }
  async function dget(u, opt, ms) { const c = new AbortController(), t = setTimeout(() => c.abort(), ms || 25000); try { const r = await dfetch(u, Object.assign({ signal: c.signal }, opt || {})); if (!r.ok) throw new Error('HTTP ' + r.status); return await r.json(); } finally { clearTimeout(t); } }

  /* ---------- geometry ---------- */
  function ringsOf(g) { if (!g) return []; if (g.type === 'Polygon') return [g.coordinates]; if (g.type === 'MultiPolygon') return g.coordinates; return []; }
  function linesOf(g) { if (!g) return []; if (g.type === 'LineString') return [g.coordinates]; if (g.type === 'MultiLineString') return g.coordinates; const o = []; ringsOf(g).forEach(p => p.forEach(r => o.push(r))); return o; }
  function inRing(x, y, r) { let ins = false; for (let i = 0, j = r.length - 1; i < r.length; j = i++) { const xi = r[i][0], yi = r[i][1], xj = r[j][0], yj = r[j][1]; if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi) ins = !ins; } return ins; }
  /* Oct 30 (Brandon: trail lines = option A): a LINE park (official trail line) counts within POTA's 100 ft of the line, never an inside test */
  const isLine = g => !!g && (g.type === 'LineString' || g.type === 'MultiLineString');
  function inside(lat, lon, g) { if (isLine(g)) return edge(lat, lon, g).km <= 0.03048; for (const poly of ringsOf(g)) { if (!poly.length || !inRing(lon, lat, poly[0])) continue; if (poly.slice(1).some(h => inRing(lon, lat, h))) continue; return true; } return false; }
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
    ['bdbnfo', 'Daniel Boone National Forest (Forest Service land)', 'U.S. Forest Service', 'ky-dbnf-owned.geojson', 'Forest Service-owned land from its ownership map (2015 data): land bought since may be missing, so check the official map.'],
    ['bdbnf', 'Forest boundary line', 'U.S. Forest Service', 'ky-dbnf.geojson', 'Forest boundary line: not all land inside is public. Only the shaded Forest Service land is the park.'],
    ['bnps', 'National Park Service', 'National Park Service', 'ky-nps.geojson'],
    ['bwild', 'Wild River Corridors', 'Kentucky Office of Nature Preserves', 'ky-wild-rivers.geojson'],
    ['bwilder', 'Wilderness Areas', 'U.S. Forest Service', 'ky-wilderness.geojson', 'Federal wilderness: no motorized equipment (generators), group size limits.'],
    ['bfws', 'Wildlife Refuges & Fish Hatcheries', 'U.S. Fish & Wildlife Service', 'ky-fws.geojson', 'Some refuge areas close by season. Check the refuge page.'],
    ['bpad', 'Official outline (USGS PAD-US)', 'USGS PAD-US (official land records)', 'ky-padus-parks.geojson'],
    ['bkpc', 'OpenStreetMap outline (unofficial)', 'OpenStreetMap (traced, not official)', 'ky-kpc-drawn.geojson', 'Outline traced from OpenStreetMap because this park has no official map file. Not official.']
  ].map(([k, name, agency, file, note]) => ({ k, name, agency, file, note, kpc: k === 'bkpc', proc: k === 'bdbnf', own: k === 'bdbnfo' }));
  /* Oct 27 (MAP DATA RULE SHEET B1 + B-G1, Fable's boundary review #1): for an agency-land park the park is the land the agency
     OWNS (shaded); its outer line is only a faint dashed 'Forest boundary line: not all land inside is public' and never says 'inside'. */
  const ALIAS = {"Ohio River Islands National Wildlife Refuge": ["US-0608"], "Livingston County Wildlife Management Area and State Nature Preserve (Bissell Bluff SNP)": ["US-3823"], "Livingston County Wildlife Management Area and State Nature Preserve (Newman's Bluff SNP)": ["US-3823"], "Blue Licks State Park State Nature Preserve": ["US-1274"], "Knobs State Forest and WMA": ["US-4690"], "Little South Fork State Natural Area (Steele Hollow SNA)": ["US-7962"], "Clifty Wilderness": ["US-3801"], "Big South Fork National River and Recreation Area": ["US-0686"], "Bad Branch Wild River": ["US-10112"], "Big South Fork Wild River": ["US-10107"], "Cumberland River Wild River": ["US-10103"], "Green River Wild River": ["US-10105"], "Rock Creek Wild River": ["US-10111"], "Red River Wild River": ["US-10104"], "Rockcastle River Wild River": ["US-10106"], "Mammoth Cave National Park": ["US-0050"], "Abraham Lincoln Birthplace National Historical Park": ["US-0724"], "Camp Nelson National Monument": ["US-7950"], "Mill Springs Battlefield National Monument": ["US-7708"], "Cumberland Gap National Historical Park": ["US-0019"], "Fort Donelson National Battlefield": ["US-0703"], "Fort Heiman (Fort Donelson National Battlefield tract)": ["US-3790"], "Jefferson National Forest": ["US-4526", "US-10139"], "Pine Mountain State Scenic Trail": ["US-10102"], "Clay WMA": ["US-10124"], "Horsemill Branch WMA": ["US-11274"], "Little Sexton Creek WMA": ["US-12079"], "General Burnside Island State Park": ["US-1257"], "Green River State Natural Area (Rush Island Bottoms)": ["US-12752"], "Green River State Natural Area (Davis Bend)": ["US-12752"], "Dale Hollow Lake State Resort Park": ["US-1278"], "Big Rivers WMA and State Forest": ["US-3796"], "Marion County WMA and State Forest": ["US-3824"], "Miller Welch-Central Kentucky WMA": ["US-3825"], "Vernon-Douglas State Nature Preserve": ["US-7957"], "Dr. William H. Martin State Natural Area": ["US-7964"], "Otter Creek Outdoor Recreation Area": ["US-8144"], "Kentucky Ridge Forest WMA": ["US-10141"], "Tom Dorman State Nature Preserve": ["US-7958"]};
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
      if (f._L.own) { f._names = m; m.forEach(r => byName.set(r, (byName.get(r) || []).concat(f))); continue; }   // owned parcels carry their park number
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
    if (!f._L.proc && !f._L.own && f._L.k !== 'bwilder') for (const x of P) {
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
  /* HQ + Brandon Oct 29 7:18 AM: CLOSE-UPS at ~3 m. Outlines read live are thinned by the map server (maxAllowableOffset 0.0001-0.0002 deg
     = 11-22 m). closeUp(fs, box) asks the SAME server again for the same records, only those touching the small box [w, s, e, n],
     at maxAllowableOffset 0.00003 deg (~3 m), geometryPrecision 6, and returns fs with those records swapped for the sharp copies.
     Records with no remembered query (Kentucky's saved files) and very big records (box over ~0.6 sq deg, e.g. a whole national
     forest: too heavy to load sharp) stay as they are; the 2-fer data's own full-detail 'lines' cover those near a spot.
     ms = time limit (default 1.5 s): a slow server just means the normal outline stays. */
  async function closeUp(fs, box, ms) {
    fs = fs || []; if (!box) return fs;
    const big = f => { const b = f._bb || bbox(f.geometry); return (b[2] - b[0]) * (b[3] - b[1]) > 0.6; };
    const groups = {}; fs.forEach(f => { if (f && f._url && !big(f)) (groups[f._url] = groups[f._url] || []).push(f); });
    const urls = Object.keys(groups); if (!urls.length) return fs;
    const env = box.map(v => (+v).toFixed(6)).join(',');
    const sharp = await Promise.all(urls.map(u => { const q = new URL(u); const P = q.searchParams;
      P.set('maxAllowableOffset', '0.00003'); P.set('geometryPrecision', '6'); P.set('geometry', env); P.set('geometryType', 'esriGeometryEnvelope'); P.set('spatialRel', 'esriSpatialRelIntersects'); P.set('inSR', '4326');
      return jget(q.toString(), null, ms || 1500).then(j => (j && j.features) || []).catch(() => null); }));
    const swap = new Map(); sharp.forEach((list, i) => { if (!list) return; list.forEach(n => { if (n && n.geometry) swap.set(urls[i] + '|' + JSON.stringify(n.properties || {}), n); }); });
    if (!swap.size) return fs;
    return fs.map(f => { const n = f && f._url && swap.get(f._url + '|' + f._pk); if (!n) return f;
      const g = Object.assign({}, f, { geometry: n.geometry, _sharp: true }); g._bb = bbox(n.geometry); return g; });
  }
  /* RULE SHEET G (Oct 29, chat 2 step 3): what a card says about the outline. o = {label: 'official'|'approx'|'none', pinOff} */
  function gradeText(o) {
    o = o || {}; const t = o.line && o.label !== 'approx' ? 'Official trail line' : o.label === 'official' ? 'Official outline' : o.label === 'approx' ? 'Approximate outline' : 'Pin only (no official outline yet)';
    return t + (o.pinOff ? '. POTA’s pin may be off for this park' : '');
  }
  /* RULE SHEET G: zoomed in close (zoom >= 13), a drawn outline is swapped for the agency's own ~3 m copy of the part on screen
     (closeUp, no second rounding); zoomed out, the lighter copy comes back. layer = the L.geoJSON drawn from fs (its own style
     function stays). Nothing waits: a slow server = the normal outline stays. Returns a stop() function. */
  function sharpLayer(map, layer, fs, opts) {
    opts = opts || {}; const minZ = opts.minZoom || 13; let t = null, sharpOn = false, gen = 0;
    const put = list => { try { layer.clearLayers(); layer.addData({ type: 'FeatureCollection', features: list.map(opts.map || (f => f.type === 'Feature' ? f : Object.assign({ type: 'Feature', properties: {} }, f))) }); } catch (e) {} };
    const go = () => { const my = ++gen;
      if (!map || map.getZoom() < minZ) { if (sharpOn) { sharpOn = false; put(fs); } return; }
      const b = map.getBounds().pad(0.2), box = [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()];
      closeUp(fs, box, 2500).then(list => { if (my !== gen || !list.some(f => f._sharp)) return; sharpOn = true; put(list); if (opts.onSharp) opts.onSharp(list); }).catch(() => {}); };
    const on = () => { clearTimeout(t); t = setTimeout(go, 350); };
    map.on('moveend zoomend', on); setTimeout(go, 0);
    return () => { map.off('moveend zoomend', on); clearTimeout(t); gen++; };
  }
  /* KY features that belong to one POTA ref */
  async function kyFor0(ref) { const F = await ky(); const N = nameIndex(); return N.has(ref) ? N.get(ref) : F.filter(f => kyRefs(f).some(r => r.ref === ref)); }
  /* Oct 31 (chat 2 / Brandon option A): a Kentucky TRAIL park with no outline in the KY files (Trail of Tears, Lewis and Clark,
     Sheltowee Trace) is drawn as its official trail line (data/trails/<ref>.json, every line in the file), counted within 100 ft. */
  let TIDX = null;
  const trailIdx = () => TIDX || (TIDX = Promise.all(['data/trails/index.json', 'data/trails/index-state.json'].map(u => dfetch(u).then(r => r.ok ? r.json() : []).catch(() => [])))
    .then(a => { const m = {}; [].concat(...a).forEach(t => { if (t && t.ref) m[t.ref] = t; }); return m; }));
  async function trailLine(ref) {
    const t = (await trailIdx())[ref]; if (!t) return [];
    const j = await dfetch('data/trails/' + ref + '.json').then(r => r.ok ? r.json() : null).catch(() => null); if (!j) return [];
    return (j.type === 'FeatureCollection' ? j.features || [] : [j]).filter(f => f && f.geometry && isLine(f.geometry))
      .map(f => (f._src = t.by || 'National Park Service', f._line = true, f._nm = t.name || (f.properties || {}).name || ref, f._L = { name: 'Official trail line', agency: f._src, k: 'btrail' }, f._bb = bbox(f.geometry), f));   /* _L: the shape the KY tools expect */
  }
  async function kyFor(ref) { const fs = await kyFor0(ref); if (fs && fs.length) return fs; try { return await trailLine(ref); } catch (e) { return []; } }

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
  /* US answer key (Oct 18, Brandon: 'use the checked outlines'): data/us-key/US-XX.json lists, per park, the PAD-US
     (or USFWS 'fws<oid>') records that match it by NAME and KIND. Returns {state:'none'} when the key knows the park but
     nothing is joined (unsure ones wait on the check list), null when no key file has the park. */
  const FWSQ = 'https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSInterest_Simplified_Authoritative/FeatureServer/0/query';
  /* answer-key id prefix -> [query url, name field, source label] (other agencies' own maps, Oct 18) */
  const XMAP = { fws: [FWSQ, 'ORGNAME', 'U.S. Fish & Wildlife Service'],
    wld: ['https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_Wilderness_02/MapServer/0/query', 'wildernessname', 'National Wilderness Preservation System'],
    hma: ['https://gis.blm.gov/arcgis/rest/services/range/BLM_Natl_WHB/MapServer/0/query', 'HMA_NAME', 'Bureau of Land Management'],
    rma: ['https://gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recreation/MapServer/9/query', 'FET_NAME', 'Bureau of Land Management'],
    rst: ['https://gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recs_poly/MapServer/0/query', 'FET_NAME', 'Bureau of Land Management'],
    nca: ['https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_NM_NCA_poly/MapServer/0/query', 'NCA_NAME', 'Bureau of Land Management'],
    wsa: ['https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_WLD_WSA/MapServer/1/query', 'NLCS_NAME', 'Bureau of Land Management'],
    wbl: ['https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_NLCS_WLD_WSA/MapServer/0/query', 'NLCS_NAME', 'Bureau of Land Management'],
    odw: ['https://services1.arcgis.com/jRf8jjFwxedITdFe/arcgis/rest/services/Public_WMA_Boundaries/FeatureServer/1/query', 'WMANAME', 'Oklahoma Dept. of Wildlife Conservation'] };
  const keyCache = {};
  /* Oct 18: state agency layers the bot found at run time (data/us-key/layers.json = {prefix: [query url, name field, label]}) */
  let LAYP = null;
  const layers = () => LAYP || (LAYP = dfetch('data/us-key/layers.json?v=' + new Date().toISOString().slice(0, 10)).then(r => r.ok ? r.json() : {}).catch(() => ({}))
    .then(L => { Object.entries(L || {}).forEach(([k, v]) => { if (!XMAP[k] && Array.isArray(v) && v[0]) XMAP[k] = v; }); return XMAP; }));
  /* Oct 23 (Brandon: 'add a note to the card that the park is retired until the monthly update'): parks POTA took off
     its list, written every night by the pin bots (data/retired-refs.json). retired(ref) -> {n, d, src} or null */
  let retP = null;
  function retired(ref) {
    if (!retP) retP = fetch('data/retired-refs.json?v=' + new Date().toISOString().slice(0, 10)).then(r => r.ok ? r.json() : {}).then(j => (j && j.refs) || {}).catch(() => ({}));
    return retP.then(R => R[String(ref || '').toUpperCase()] || null);
  }
  function retiredHtml(r) {
    const d = r && r.d ? new Date(r.d + 'T12:00:00').toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : '';
    return '<b style="font-size:14px">Retired by POTA.</b> This park is no longer on the official list' + (d ? ' (we noticed on ' + esc(d) + ')' : '') + ', so a new activation will not count. Contacts already made still count.';
  }
  async function usKey(ref, states) {
    await layers();
    let hit = null, known = false, site = null, note = '', grade = '', pinOff = false;
    for (const st of states || []) {
      if (!(st in keyCache)) keyCache[st] = dfetch('data/us-key/US-' + st + '.json?v=' + new Date().toISOString().slice(0, 10)).then(r => r.ok ? r.json() : null).catch(() => null);
      const k = await keyCache[st]; const p = k && k.parks && k.parks[ref];
      if (p) { known = true; if (p.note) note = p.note; if (p.g && !grade) grade = String(p.g); if (p.pin_may_be_wrong) pinOff = true; if (p.m && p.m.length) { hit = hit || { n: p.n, m: [], twin: new Set() }; (p.twin || []).forEach(t => hit.twin.add(String(t))); hit.m.push(...p.m); hit.far = hit.far || p.far; if (p.read && (!hit.read || p.read < hit.read)) hit.read = p.read; } if (p.a && p.a.length) site = p.a; }
    }
    /* RULE SHEET G (Oct 29): the key's own grade decides: 'official' / 'approximate' / 'pin' (= no outline, whatever matched) */
    if (grade === 'pin') return { state: 'none', site, grade, pinOff };
    if (!hit) return known ? { state: 'none', site, grade, pinOff } : null;
    const seen = new Set(), m = hit.m.filter(x => !seen.has(String(x[0])) && seen.add(String(x[0])) && !(hit.twin && hit.twin.has(String(x[0]))));   /* Oct 30 (chat 2): 'twin' ids = the same land as another joined record: not drawn twice */
    const off = a => a < 20000 ? 0.00004 : a < 200000 ? 0.00015 : a < 1000000 ? 0.0003 : 0.0008;
    const groups = {};
    m.forEach(x => { const s = String(x[0]), pre = (s.match(/^[a-z]+/) || [''])[0], id = s.slice(pre.length), o = off(+x[2] || 0), g = pre + o; (groups[g] = groups[g] || { pre, o, ids: [] }).ids.push(id); });
    const jobs = [];
    Object.values(groups).forEach(g => { for (let i = 0; i < g.ids.length; i += 40) { const ids = g.ids.slice(i, i + 40).join(','), X = XMAP[g.pre];
      if (X && String(X[0]).startsWith('file:') && String(X[0]).indexOf('{n}') >= 0) {   /* Oct 30: one file per record (official trail lines) */
        g.ids.slice(i, i + 40).forEach(n => jobs.push(dfetch(X[0].slice(5).replace('{n}', n) + '?v=' + new Date().toISOString().slice(0, 10)).then(r => r.ok ? r.json() : null)
          .then(j => (!j ? [] : j.type === 'FeatureCollection' ? (j.features || []) : [j]).map(f => (f._src = X[2] || 'National Park Service', f._line = true, f))).catch(() => [])));
        continue;
      }
      if (X && String(X[0]).startsWith('file:')) {   /* Oct 28: a zipped-shapefile layer (Mississippi): the key's own simplified copy */
        const want = new Set(g.ids.slice(i, i + 40).map(n => g.pre + n));
        jobs.push(dfetch(X[0].slice(5) + '?v=' + new Date().toISOString().slice(0, 10)).then(r => r.ok ? r.json() : { features: [] })
          .then(j => (j.features || []).filter(f => want.has(String((f.properties || {}).OBJECTID))).map(f => (f._src = X[2], f))).catch(() => []));
        continue;
      }
      jobs.push(X ? jget(X[0] + '?' + new URLSearchParams({ objectIds: ids, outFields: X[1], returnGeometry: true, outSR: 4326, maxAllowableOffset: g.o, geometryPrecision: 5, f: 'geojson' }), null, 30000).then(j => (j.features || []).map(f => { f._src = X[2]; const p = f.properties || {}; f.properties = Object.assign({ Unit_Nm: p[X[1]] }, p); return f; })).catch(() => [])
        : padus({ objectIds: ids, returnGeometry: true, geometryPrecision: 5, maxAllowableOffset: g.o }).then(j => (j.features || []).map(f => (f._src = 'USGS PAD-US', f))).catch(() => [])); } });
    const fs = (await Promise.all(jobs)).flat().filter(f => f.geometry);
    if (!fs.length) return { state: 'error', n: hit.n, m };
    fs.forEach(f => { const p = f.properties || {}; f._nm = p.Unit_Nm || p.ORGNAME || hit.n; f._bb = bbox(f.geometry); });
    /* Oct 22 (Brandon: 'note boundaries that we dont know for sure so they clearly know this is not offical'): an outline is
       APPROXIMATE when the names only partly match AND the park's map pin is outside the land. A pin alone is not enough:
       POTA's pins can be miles off (Kodiak Refuge, Vega State Park) while the name is exact. A person's review
       (overrides.json) always counts as sure. */
    const how = new Set(m.map(x => String(x[3] || ''))), reviewed = how.has('reviewed'), named = [...how].some(h => h.startsWith('name'));
    const handApprox = how.has('reviewed-approx') && !reviewed;   /* Oct 22: checked by hand, the closest official land is bigger / shaped differently */
    /* Oct 25: a state's lake-surface map (Idaho, Washington, Arkansas) draws the water, not the agency's lake property around it */
    const water = !reviewed && [...how].every(h => h.indexOf('water outline only') >= 0);
    const approx = grade ? grade === 'approximate' : (handApprox || water || (!reviewed && !named && !!hit.far));
    const why = handApprox ? 'this is the closest official land, but it is bigger than the park or shaped differently' : water ? 'this is the lake\u2019s shoreline from the state\u2019s water map; the park is the agency\u2019s lake property around it, so check the agency\u2019s map for the land' : approx ? 'the names only partly match and the park\u2019s map pin is ' + (hit.far === 'well outside' ? 'well outside this land' : 'just outside this land') : '';
    const line = fs.every(f => isLine(f.geometry));   /* a trail park drawn as its official line */
    return { state: 'ok', n: hit.n, m, fs, approx, why, note, water, read: hit.read || '', grade, pinOff, line };
  }
  /* Oct 22 (Brandon: 'note boundaries that we dont know for sure'): ONE answer for every tool that draws a US park.
     {fs, label: 'official' | 'approx' | 'none', why, src, site}. Checked list first; a park it doesn't know falls back to a
     live name search, which is labelled approximate because nobody has checked it. */
  async function usOutline(ref, name, la, lo, states) {
    let k = null; try { k = await usKey(ref, states); } catch (e) {}
    if (k && k.state === 'ok') return { fs: k.fs, label: k.approx ? 'approx' : 'official', line: !!k.line, pinOff: !!k.pinOff, water: !!k.water, read: k.read || '', old: !!k.read && (Date.now() - Date.parse(k.read + 'T12:00:00')) > 365 * 864e5, why: k.why || '', note: k.note || '', src: [...new Set(k.fs.map(f => f._src))].join(' + ') };
    if (k && k.state === 'none') return { fs: [], label: 'none', why: '', src: '', site: k.site, pinOff: !!k.pinOff };
    let fs = []; try { fs = await padusByName(name, la, lo); } catch (e) {}
    return fs.length ? { fs, label: 'approx', why: 'found by a name search and not checked yet', src: 'USGS PAD-US' } : { fs: [], label: 'none', why: '', src: '' };
  }
  /* Oct 18 (Brandon: review the US data… tappable land): what official land is at a spot, and which POTA parks the answer key joined to it */
  const revCache = {};
  async function keyRev(st) {
    if (!(st in revCache)) revCache[st] = (keyCache[st] = keyCache[st] || dfetch('data/us-key/US-' + st + '.json?v=' + new Date().toISOString().slice(0, 10)).then(r => r.ok ? r.json() : null).catch(() => null))
      .then(k => { const m = {}; Object.entries((k && k.parks) || {}).forEach(([ref, p]) => (p.m || []).forEach(x => (m[String(x[0])] = m[String(x[0])] || []).push({ ref, n: p.n }))); return m; });
    return revCache[st];
  }
  const ACC = { OA: 'open to the public', RA: 'restricted access', XA: 'closed to the public', UK: 'access unknown' };
  async function usLandAt(la, lo, states) {
    const pt = { geometry: `${lo},${la}`, geometryType: 'esriGeometryPoint' };
    const meta = await padus(Object.assign({ returnGeometry: false }, pt)).catch(() => ({ features: [] }));
    let fs = (meta.features || []).map(f => f.properties || {}).filter(p => p.Category !== 'Proclamation');
    const seen = new Set(); fs = fs.filter(p => { const k = (p.Unit_Nm || '') + '|' + (p.Loc_Mang || p.Mang_Name || ''); if (seen.has(k)) return false; seen.add(k); return true; })
      .sort((a, b) => (+a.GIS_Acres || 0) - (+b.GIS_Acres || 0)).slice(0, 5);
    if (!fs.length) return [];
    const rev = Object.assign({}, ...(await Promise.all((states || []).map(keyRev))));
    const geo = await padus({ objectIds: fs.map(p => p.OBJECTID).join(','), returnGeometry: true, geometryPrecision: 5, maxAllowableOffset: 0.0002,
      geometry: `${lo - 0.15},${la - 0.15},${lo + 0.15},${la + 0.15}`, geometryType: 'esriGeometryEnvelope' }).catch(() => ({ features: [] }));
    const G = {}; (geo.features || []).forEach(f => { G[(f.properties || {}).OBJECTID] = f; });
    return fs.map(p => ({ id: p.OBJECTID, name: p.Unit_Nm || p.Loc_Nm || 'Public land', by: p.Loc_Mang || p.Mang_Name || '', kind: p.Des_Tp || '',
      access: ACC[p.Pub_Access] || '', acres: Math.round(+p.GIS_Acres || 0), parks: rev[String(p.OBJECTID)] || [], f: G[p.OBJECTID] || null }));
  }
  const words = n => String(n || '').replace(/\b(state|national|park|parks|forest|wildlife|management|area|recreation|recreational|nature|preserve|refuge|historic|historical|site|reserve|natural|lake|wma|nwr|the|of|and)\b/gi, ' ').replace(/[^A-Za-z0-9' ]/g, ' ').trim().split(/\s+/).filter(w => w.length > 2);
  async function padusByName(name, la, lo) {
    const w = words(name), d = 0.35; if (!w.length) return [];
    /* PAD-US firewall: one plain LIKE only (no UPPER/OR/AND), so ask Title Case, CAPITALS and as typed, then merge */
    const ws = w.slice(0, 2), pat = f => ('%' + ws.map(f).join('%') + '%').replace(/'/g, '%');
    const wh = [...new Set([`Unit_Nm LIKE '${pat(x => x.charAt(0).toUpperCase() + x.slice(1).toLowerCase())}'`, `Loc_Nm LIKE '${pat(x => x.toUpperCase())}'`, `Unit_Nm LIKE '${pat(x => x)}'`])];
    const gs = await Promise.all(wh.map(where => padus({ where, geometry: `${lo - d},${la - d},${lo + d},${la + d}`, geometryType: 'esriGeometryEnvelope', returnGeometry: true, geometryPrecision: 5, maxAllowableOffset: 0.0001 }).catch(() => ({ features: [] }))));
    const seen = new Set(); const g = { features: gs.flatMap(x => x.features || []).filter(f => { const k = f.id != null ? f.id : (f.properties || {}).OBJECTID; if (k != null && seen.has(k)) return false; seen.add(k); return true; }) };
    let fs = (g.features || []).filter(f => f.geometry && !/^(Proclamation|Easement)$/.test(f.properties.Category || '')); if (!fs.length) return [];   /* Oct 27 (boundary review #9): an easement or a proclamation line is never park land */
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
  /* Canada: the official outline saved by kpc-canada-bounds.yml (CPCAD or the province's map); when there is no saved
     file, the Canada ANSWER KEY (data/ca-key, Oct 24, Brandon: 'hook the Canada and world answer keys into the planner,
     Info Finder and the Kit') says which official areas the checking bot joined, and they are fetched by id */
  const caCache = {}; let CAREF = null, CALAY = null;
  async function caKey(ref) {
    CAREF = CAREF || dfetch('data/ca-key/refs.json?v=' + new Date().toISOString().slice(0, 10)).then(r => r.ok ? r.json() : {}).catch(() => ({}));
    CALAY = CALAY || dfetch('data/ca-key/layers.json?v=' + new Date().toISOString().slice(0, 10)).then(r => r.ok ? r.json() : {}).catch(() => ({}));
    const pv = (await CAREF)[ref]; if (!pv) return null;   /* (+ RULE SHEET G grade below) */
    if (!(pv in caCache)) caCache[pv] = dfetch('data/ca-key/CA-' + pv + '.json?v=' + new Date().toISOString().slice(0, 10)).then(r => r.ok ? r.json() : null).catch(() => null);
    const k = await caCache[pv], p = k && k.parks && k.parks[ref]; if (!p) return null;
    const m = p.m || []; if (!m.length || p.g === 'pin') return { state: 'none', site: p.a || null, pinOff: !!p.pin_may_be_wrong };
    const L = await CALAY, by = {};
    m.forEach(x => { const s = String(x[0]), i = s.lastIndexOf(':'), pre = i < 0 ? 'cpcad' : s.slice(0, i), id = i < 0 ? s : s.slice(i + 1); (L[pre] || []).forEach(u => (by[u] = by[u] || []).push(id)); });
    const want = new Set(m.map(x => String(x[1] || '').toLowerCase().replace(/\s+/g, ' ').trim()));
    const fs = (await Promise.all(Object.entries(by).map(([u, ids]) => jget(u + '/query?' + new URLSearchParams({ objectIds: ids.slice(0, 40).join(','), outFields: '*', returnGeometry: true, outSR: 4326, maxAllowableOffset: 0.0002, geometryPrecision: 5, f: 'geojson' }), null, 30000)
      .then(j => (j.features || []).filter(f => { const P = f.properties || {}; const names = Object.keys(P).filter(k => /name|nom|toponym|title/i.test(k) && !/file|url|link|code|id$/i.test(k)).map(k => String(P[k] || '').toLowerCase().replace(/\s+/g, ' ').trim()); return !names.length || names.some(n => want.has(n)); })   /* two layers can share an id prefix: keep the record whose NAME is the joined one */
        .map(f => (f._src = u.indexOf('maps-cartes.ec.gc.ca') >= 0 ? 'CPCAD (Environment and Climate Change Canada)' : 'the province\u2019s own map', f))).catch(() => [])))).flat().filter(f => f.geometry);
    if (!fs.length) return { state: 'error' };
    const how = m.map(x => String(x[3] || '')), reviewed = how.some(h => h === 'reviewed'), named = how.some(h => /^(name|same name|exact name|reviewed)/.test(h));
    const approx = p.g ? p.g === 'approximate' : (how.some(h => h === 'reviewed-approx') || (!reviewed && (!named || p.far === 'well outside')));
    const why = how.some(h => h === 'reviewed-approx') ? 'this is the closest official land, but it is bigger than the park or shaped differently' : approx ? 'the names only partly match or the park\u2019s map pin sits well outside this land' : '';
    const nm = m[0][1];
    fs.forEach(f => { f._nm = f._nm || nm; f._bb = bbox(f.geometry); f._approx = approx; f._why = why; f._info = ''; f.properties = Object.assign(f.properties || {}, { NAME: f._nm, SOURCE: f._src }); });
    return { state: 'ok', fs, approx, why, pinOff: !!p.pin_may_be_wrong };
  }
  async function canada(ref) {
    if (!/^CA-\d/.test(ref || '')) return [];
    const j = await dget('data/canada-bounds/' + encodeURIComponent(ref) + '.json', null, 20000).catch(() => null);
    if (!j) { let k = null; try { k = await caKey(ref); } catch (e) {} return k && k.state === 'ok' ? k.fs : []; }
    const fs = (j.type === 'FeatureCollection' ? j.features : [j]).filter(f => f && f.geometry);
    return fs.map(f => { const p = f.properties || {}; f._nm = p.cpcad || p.name || ref; f._bb = bbox(f.geometry); f._src = p.srcShort || 'CPCAD (Environment and Climate Change Canada)'; f._info = [p.type, p.manager].filter(Boolean).join(' · '); if (p.approx) { f._approx = true; f._why = 'this is the closest official land, but it is bigger than the park or shaped differently'; } return f; });
  }
  /* Oct 22 (Brandon's schedule: 'hook the world key into KPCB like usKey'): data/world-key/XX.json lists, per park, the
     official areas the checking bot joined (by name, or by the pin when names are written differently). The outline comes
     straight from that agency's map by id. A join made on the pin alone is labelled approximate. */
  const wkCache = {}; let WLAY = null;
  const wlayers = () => WLAY || (WLAY = dfetch('data/world-key/layers.json?v=' + new Date().toISOString().slice(0, 10)).then(r => r.ok ? r.json() : {}).catch(() => ({})));
  async function worldKey(ref) {
    const cc = String(ref || '').split('-')[0]; if (!/^[A-Z]{2}$/.test(cc) || cc === 'US' || cc === 'CA') return null;
    if (!(cc in wkCache)) wkCache[cc] = dfetch('data/world-key/' + cc + '.json?v=' + new Date().toISOString().slice(0, 10)).then(r => r.ok ? r.json() : null).catch(() => null);
    const k = await wkCache[cc], p = k && k.parks && k.parks[ref]; if (!p) return null;
    const m = p.m || []; if (!m.length) return { state: 'none' };
    const L = await wlayers(), by = {};
    m.forEach(x => { if (L[x[2]] && x[0] !== null && x[0] !== undefined) (by[x[2]] = by[x[2]] || []).push(x[0]); });
    const fs = (await Promise.all(Object.entries(by).map(([src, ids]) => jget(L[src] + '/query?' + new URLSearchParams({ objectIds: ids.slice(0, 40).join(','), outFields: '*', returnGeometry: true, outSR: 4326, maxAllowableOffset: 0.0002, geometryPrecision: 5, f: 'geojson' }), null, 30000)
      .then(j => (j.features || []).map(f => (f._src = src, f))).catch(() => [])))).flat().filter(f => f.geometry);
    /* Oct 22: an outline from a map a web page cannot ask by id (IGN, BfN, NatureScot, Wales, BAFU, Japan A10) is saved
       by the world bot in data/world-bounds/CC/<n>.json, 100 parks to a file */
    if (!fs.length) {
      const num = parseInt(String(ref).split('-')[1], 10), sh = await dget('data/world-bounds/' + cc + '/' + Math.floor(num / 100) + '.json', null, 20000).catch(() => null), b = sh && sh[ref];
      if (b && b.r && b.r.length) fs.push({ type: 'Feature', properties: {}, geometry: { type: 'MultiPolygon', coordinates: b.r.map(r => [r]) }, _src: b.s + ' (saved by KPC)' });
    }
    if (!fs.length) return { state: 'error' };
    const nm = (m.find(x => L[x[2]]) || m[0])[1], how = m.map(x => String(x[3] || ''));
    const approx = !how.some(h => /^(name|same name|exact name)/.test(h)), why = approx ? 'the official name is written differently, so this was matched by where the park\u2019s pin sits' : '';
    fs.forEach(f => { f._nm = f._nm || nm; f._bb = bbox(f.geometry); f._approx = approx; f._why = why; f._info = f._info || ''; f.properties = Object.assign(f.properties || {}, { NAME: f._nm, SOURCE: f._src }); });
    return { state: 'ok', fs, approx, why };
  }
  /* any non-US official outline we know how to get: Canada file, then the checked world list, then a live Europe guess
     (labelled approximate when the checked list knows the park but found nothing sure) */
  async function worldByName(ref, name, la, lo, o) {
    const c = await canada(ref); if (c.length) return c;
    let k = null; try { k = await worldKey(ref); } catch (e) {}
    if (k && k.state === 'ok') return k.fs;
    const e = await euro(name, la, lo, o);
    if (k && k.state === 'none') e.forEach(f => { f._approx = true; f._why = 'our maps did not find a sure match; this is a live guess by name'; });
    return e;
  }
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
    const rows = await Promise.all(tilesAround(la, lo, kmR).map(k => { const u = dir + k + '.json'; return tileCache[u] || (tileCache[u] = dfetch(u).then(r => r.ok ? r.json() : []).catch(() => [])); }));
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
    if (/FF$/.test(m[1])) { const ref = m[1] + '-' + m[2].padStart(4, '0'); const rows = await dget('data/wwff/' + m[1] + '.json').catch(() => []); const x = rows.find(r => r[0] === ref); if (!x) return null; return { prog: 'WWFF', ref, name: x[1], la: x[2], lo: x[3], web: /^https?:/.test(x[4]) ? x[4] : '', type: 'WWFF reference', where: [...new Set([x[6], x[5]].filter(Boolean))].join(', '), st: String(x[5] || '').replace(/^K-/, ''), us: m[1] === 'KFF' }; }
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

  window.KPCB = { trailLine, closeUp, gradeText, sharpLayer, landInfo, landAt, kindOf, sameKind, tilesUsed: () => Object.keys(tileCache), wwffNear, sotaNear, elevation, lookup, esc, jget, dget, ringsOf, linesOf, inside, edge, bbox, km, dir, dist, norm, sameName, KY, inKY, ky, kyRefs, kyFor, kyData: () => kyData, ACCESS, padusArea, padusByName, usKey, usOutline, usLandAt, retired, retiredHtml, euro, canada, caKey, worldKey, worldByName, inEurope, potaNear, refsFor, osmAt, saveGeo, WHICH, OSM_NOTE };
})();
