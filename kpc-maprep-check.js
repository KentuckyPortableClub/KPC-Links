/* Could this be a park? — check for the Mapping Rep Tool Box.
   Outlines come from that place's published key (US, Canada, or the world key for
   GB, Ireland, Australia and New Zealand). A US place also uses PAD-US.
   A name with no place searches every loaded region. It does not assume one state.
   No map token, no keyed API, no spoofed User-Agent. Newfoundland, Tokyo, Japan A10,
   South Africa SAPAD and Colorado CNHP outlines are never requested and never drawn. */
(function () {
  'use strict';
  const B = () => window.KPCB;
  const $ = id => document.getElementById(id);
  const esc = s => (B() && B().esc) ? B().esc(s) : String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const INFO = 'ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go.';
  const OVERLAP_NOTE = "⚠️ Parks' boundaries may overlap here, but we can't confirm it. Check both official boundary maps and make your own call before you count it.";
  /* ids only — never draw these outlines (data/CREDITS-NC.md) */
  const BLOCKED = /newfoundland|tokyo|\bA10\b|sapad|cnhp|colorado natural heritage/i;

  let pack = null, map = null, drawLayer = null, pinMarker = null, pinCtl = null, overlayLayers = {}, gen = 0, lastPin = null;
  /* Which country this check runs, and which states have outlines saved on the site. */
  const REGION = {
    us: { enabled: true, source: 'PAD-US', local: ['KY'] },
    ca: { enabled: false, source: 'CPCAD' }
  };
  const GAP_WORD = {
    '1': 'GAP 1, managed for biodiversity',
    '2': 'GAP 2, managed for biodiversity, some disturbance suppressed',
    '3': 'GAP 3, multiple use',
    '4': 'GAP 4, no known biodiversity mandate'
  };
  const isLocal = code => REGION.us.local.indexOf(code) >= 0;
  let statesP = null, keyCache = {};
  function agTable() { return window.KPCMapAg || {}; }
  async function loadStates() {
    if (statesP) return statesP;
    statesP = B().jget('kpc-us-states.json').then(rows => (rows || []).map(b => {
      let x0 = 180, y0 = 90, x1 = -180, y1 = -90;
      (b.p || []).forEach(pl => (pl[0] || []).forEach(([x, y]) => { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }));
      return { a: b.a, n: b.n, p: b.p, bb: [x0, y0, x1, y1] };
    })).catch(() => []);
    return statesP;
  }
  function stateAt(la, lo, rows) {
    const b = B();
    for (const s of rows || []) {
      const bb = s.bb;
      if (!bb || lo < bb[0] || lo > bb[2] || la < bb[1] || la > bb[3]) continue;
      for (const pl of s.p || []) {
        const ring = pl[0];
        if (ring && ring.length > 2 && b.inside(la, lo, { type: 'Polygon', coordinates: [ring] })) return { code: s.a, name: s.n, local: isLocal(s.a) };
      }
    }
    return null;
  }
  function parseState(q, rows) {
    const s = String(q || '').trim();
    const byCode = new Map(rows.map(r => [r.a, r]));
    let m = s.match(/^(.*?)[,\s]+([A-Za-z]{2})$/);
    if (m && byCode.has(m[2].toUpperCase()) && m[1].trim().length > 2) {
      const row = byCode.get(m[2].toUpperCase());
      return { q: m[1].trim(), code: row.a, name: row.n, local: isLocal(row.a) };
    }
    const low = s.toLowerCase();
    for (const row of rows) {
      const name = String(row.n || '').toLowerCase();
      if (!name) continue;
      if (low.endsWith(', ' + name) || low.endsWith(' ' + name)) {
        return { q: s.slice(0, s.length - row.n.length).replace(/[,\s]+$/, ''), code: row.a, name: row.n, local: isLocal(row.a) };
      }
    }
    return null;
  }
  function placeList() {
    const G = window.KPCMapLogic;
    return (G && G.placeRows) ? G.placeRows() : [];
  }
  function keyFile(code) {
    const row = placeList().find(r => r.code === code);
    const region = row ? row.region : 'US';
    if (region === 'CA') return 'data/ca-key/CA-' + code + '.json';
    if (region === 'world') return 'data/world-key/' + code + '.json';
    return 'data/us-key/US-' + code + '.json';
  }
  async function chosenState(q) {
    const rows = await loadStates();
    const places = placeList();
    const sel = $('mrCheckSt');
    const picked = sel && sel.value;
    if (picked) {
      const row = places.find(r => r.code === picked) || rows.find(r => r.a === picked);
      if (row) return { q: String(q || '').trim(), code: row.code || row.a, name: row.name || row.n, local: isLocal(row.code || row.a), region: row.region || 'US', picked: true };
    }
    const parsed = parseState(q, places.length ? places.map(r => ({ a: r.code, n: r.name })) : rows);
    if (parsed) return parsed;
    if (lastPin) {
      const at = stateAt(lastPin.la, lastPin.lo, rows);
      if (at) return { q: String(q || '').trim(), code: at.code, name: at.name, local: at.local, region: 'US', fromPin: true };
    }
    return { q: String(q || '').trim(), code: '', name: '', local: false, region: '', all: true };
  }
  async function stateKey(code) {
    if (!code) return null;
    if (!keyCache[code]) keyCache[code] = B().jget(keyFile(code)).catch(() => null);
    return keyCache[code];
  }
  function homesFor(code) {
    const rows = ((agTable().SA || {})[code]) || [];
    return rows.map(([label, host]) => [label, /^https?:/i.test(host) ? host : 'https://' + host.replace(/^\/\//, '')]);
  }
  let agP = null;
  function ensureAgencies() {
    if (window.KPCMapLogic && KPCMapLogic.agenciesReady && KPCMapLogic.agenciesReady()) return Promise.resolve();
    if (!agP) {
      const get = (window.KPCB && KPCB.jget) ? (p => KPCB.jget(p)) : (p => fetch(p).then(r => { if (!r.ok) throw new Error('agencies'); return r.json(); }));
      agP = get('data/maprep/agencies.json').then(j => { if (window.KPCMapLogic && j) KPCMapLogic.loadAgencies(j); return j; }).catch(() => null);
    }
    return agP;
  }
  function slotLink(label, slot) {
    if (!slot || !slot.url) return '';
    const tag = slot.verified ? '' : ' (unverified)';
    return `<a class="k-off" href="${esc(slot.url)}" target="_blank" rel="noopener"><b>${esc(label + tag)}</b><span>${esc(slot.url)}</span></a>`;
  }
  function directoryBlock(code, blob) {
    const G = window.KPCMapLogic;
    if (!G || !G.agencyMatches) return '';
    const rows = G.agencyMatches(code || '', blob || '');
    if (!rows.length) return '<p class="mr-help">No agency directory row is stored for this place.</p>';
    const head = rows[0].matched ? 'Matching agencies' : 'Land agencies for this place';
    const note = rows[0].matched ? 'Picked from the directory by this place and the designation, even when the layer has no page of its own.' : 'The designation did not name an agency, so every land agency stored for this place is listed.';
    return `<h4 style="margin:12px 0 6px">${head}</h4><p class="mr-help">${note}</p>` + rows.map(a => {
      const links = [slotLink(a.name + ' — home', a.home), slotLink(a.name + ' — finder', a.finder), slotLink(a.name + ' — GIS', a.gis)].filter(Boolean).join('');
      return links ? `<div class="mr-links">${links}</div>` : `<p class="mr-help">${esc(a.name)}: no URL stored.</p>`;
    }).join('');
  }
  function paintPlaceButton() {
    const btn = $('mrCheckAll'); if (!btn) return;
    const sel = $('mrCheckSt');
    const code = sel && sel.value;
    const row = placeList().find(r => r.code === code);
    btn.textContent = row ? ('CHECK ALL IN ' + row.name.toUpperCase()) : 'CHECK ALL IN THIS PLACE';
  }
  function fillStateMenu() {
    const sel = $('mrCheckSt'); if (!sel || sel.dataset.ready) return;
    const rows = placeList();
    if (!rows.length) return;
    sel.dataset.ready = '1';
    rows.forEach(r => {
      const o = document.createElement('option');
      o.value = r.code;
      o.textContent = r.name + ' (' + r.code + ')';
      sel.appendChild(o);
    });
    sel.value = '';
    sel.onchange = () => { paintPlaceButton(); if (window.KPCMapDesk && KPCMapDesk.syncPlace) KPCMapDesk.syncPlace(sel.value); buildToggles(); };
    paintPlaceButton();
  }
  function syncPlace(code) {
    const sel = $('mrCheckSt');
    if (sel && sel.dataset.ready && [...sel.options].some(o => o.value === code)) sel.value = code || '';
    paintPlaceButton();
    buildToggles();
  }

  function acresOf(g) {
    const b = B(); let a = 0;
    b.ringsOf(g).forEach(poly => poly.forEach((r, n) => {
      let s2 = 0;
      for (let i = 0, k = r.length - 1; i < r.length; k = i++) s2 += (r[k][0] + r[i][0]) * (r[k][1] - r[i][1]);
      const lat = (r[0] ? r[0][1] : 0) * Math.PI / 180;
      const m2 = Math.abs(s2 / 2) * 111320 * 111320 * Math.cos(lat);
      a += n ? -m2 : m2;
    }));
    return Math.abs(a) / 4046.86;
  }
  function feetOrMi(km) {
    if (km == null || !isFinite(km)) return '';
    const ft = km * 3280.84;
    if (ft < 30) return 'at this pin';
    if (ft < 1000) return Math.round(ft) + ' ft';
    const mi = km * 0.621371;
    return (mi < 10 ? mi.toFixed(1) : Math.round(mi)) + ' mi';
  }
  function govUrl(u) {
    try {
      const h = new URL(u).hostname.replace(/^www\./, '').toLowerCase();
      return /\.(gov|mil)$/.test(h) || /(^|\.)(gc|gov)\.ca$/.test(h);
    } catch (e) { return false; }
  }
  function grid(la, lo) {
    const A = 'ABCDEFGHIJKLMNOPQR', a = 'abcdefghijklmnopqrstuvwx';
    let x = lo + 180, y = la + 90;
    const f1 = A[Math.floor(x / 20)] + A[Math.floor(y / 10)];
    x %= 20; y %= 10;
    const f2 = '' + Math.floor(x / 2) + Math.floor(y);
    x %= 2; y %= 1;
    return f1 + f2 + a[Math.floor(x * 12)] + a[Math.floor(y * 24)];
  }
  function normRef(q) {
    let s = String(q || '').toUpperCase().replace(/[^A-Z0-9-]/g, '');
    if (/^\d{1,5}$/.test(s)) s = 'US-' + s.padStart(4, '0');
    const m = s.match(/^([A-Z]{2})-(\d{1,5})$/);
    if (m) s = m[1] + '-' + m[2].padStart(4, '0');
    return /^(US|CA|MX)-\d{4,5}$/.test(s) ? s : '';
  }
  /* W.M.A. / WMA / Wildlife Management Area, SP / State Park, SNP / State Nature Preserve, and the same for case and punctuation. */
  function canon(s) {
    if (window.KPCMapLogic) return KPCMapLogic.canon(s);
    let t = String(s || '').toLowerCase().replace(/&/g, ' and ');
    t = t.replace(/w\s*\.\s*m\s*\.\s*a\.?/g, ' wma ');
    t = t.replace(/\bwma\b/g, ' wildlife management area ');
    t = t.replace(/s\s*\.\s*n\s*\.\s*p\.?/g, ' snp ');
    t = t.replace(/\bsnp\b/g, ' state nature preserve ');
    t = t.replace(/s\s*\.\s*n\s*\.\s*a\.?/g, ' sna ');
    t = t.replace(/\bsna\b/g, ' state natural area ');
    t = t.replace(/s\s*\.\s*p\.?/g, ' sp ');
    t = t.replace(/\bsp\b/g, ' state park ');
    t = t.replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim();
    const core = t.replace(/\b(wildlife|management|area|state|national|park|parks|nature|preserve|natural|forest|refuge|the|of|and|site|historic|historical|recreational|recreation|resort)\b/g, ' ').replace(/\s+/g, ' ').trim();
    return { full: t, core: core || t };
  }
  function tokens(s) { return String(s || '').split(' ').filter(w => w.length > 2); }
  function dice(a, b) {
    if (a === b) return 1;
    if (!a || !b || a.length < 2 || b.length < 2) return 0;
    const bg = s => { const m = new Map(); for (let i = 0; i < s.length - 1; i++) { const k = s.slice(i, i + 2); m.set(k, (m.get(k) || 0) + 1); } return m; };
    const A = bg(a), B = bg(b); let inter = 0, na = 0, nb = 0;
    A.forEach(n => { na += n; }); B.forEach(n => { nb += n; });
    A.forEach((n, k) => { if (B.has(k)) inter += Math.min(n, B.get(k)); });
    return (2 * inter) / (na + nb || 1);
  }
  function nameScore(query, candidate) {
    if (window.KPCMapLogic) return KPCMapLogic.nameScore(query, candidate);
    const q = canon(query), c = canon(candidate);
    if (!q.core || !c.core) return 0;
    if (q.core === c.core || q.full === c.full) return 96;
    const qt = tokens(q.core), ct = tokens(c.core);
    if (qt.length && qt.every(w => ct.indexOf(w) >= 0)) return ct.length === qt.length ? 92 : 84;
    const d = dice(q.core, c.core);
    const generic = { creek: 1, lake: 1, river: 1, fork: 1, branch: 1, ridge: 1, county: 1, hunting: 1, public: 1, north: 1, south: 1, east: 1, west: 1 };
    const shared = qt.filter(w => ct.indexOf(w) >= 0 && !generic[w] && w.length >= 4);
    if (d >= 0.8 && shared.length) return 70;
    if (d >= 0.72 && shared.length) return 58;
    if (shared.some(w => w.length >= 6) && d >= 0.45) return 52;
    return 0;
  }
  function hiddenBlob(f) {
    const p = f.properties || {}, L = f._L || {};
    return [L.name, L.agency, L.note, p.SOURCE, p.src, p.NAME, p.MANAGER].filter(Boolean).join(' ');
  }
  function blocked(f) { return BLOCKED.test(hiddenBlob(f)); }
  function credits(f) {
    const out = [], blob = hiddenBlob(f), L = f._L || {};
    if (L.kpc || /openstreetmap/i.test(blob)) out.push('© OpenStreetMap contributors, ODbL');
    if (/CONANP/i.test(blob)) out.push('Fuente: CONANP');
    const nc = (B() && B().ncLabel) ? B().ncLabel('', L.agency || blob) : '';
    if (nc && out.indexOf(nc) < 0) out.push(nc);
    return out;
  }
  function urlOf(f) {
    const p = f.properties || {};
    const u = p.URL || p.Web || p.url || p.HYPERLINK || '';
    return /^https?:\/\//i.test(u) ? u : '';
  }
  function acresOfFeat(f) {
    const p = f.properties || {};
    const n = +p.ACRES || +p.GIS_Acres || +p.acres;
    if (n > 0) return n;
    try { return acresOf(f.geometry); } catch (e) { return 0; }
  }
  function tierOf(f) {
    const L = f._L || {}, p = f.properties || {};
    const who = [p.MANAGER, p.OWNER, p.owner, L.agency].filter(Boolean).join(' ');
    if (L.k === 'bkpc' || L.kpc) return 'osm';
    if (L.k === 'bdbnf' || L.proc) return 'line';
    if (L.k === 'busace' || /corps of engineers/i.test(who)) return 'corps';
    if (/non-profit|audubon|private|county|city of|town of/i.test(who)) return 'other';
    if (['bnps', 'bfws', 'bwilder', 'bdbnfo'].indexOf(L.k) >= 0 || /park service|fish & wildlife service|forest service|federal/i.test(who)) return 'fed';
    return 'state';
  }
  function accessOf(f) {
    const a = String((f.properties || {}).ACCESS || (f.properties || {}).Pub_Access || '');
    if (/^(xa|closed|no)$/i.test(a) || /closed to the public/i.test(a)) return 'closed';
    if (/restrict|permit|appointment|limited/i.test(a) || a === 'RA') return 'restricted';
    if (/open|yes|public/i.test(a) || a === 'OA') return 'open';
    const k = (f._L || {}).k;
    if (k === 'bstate' || k === 'bnps' || k === 'bwma' || k === 'bfws') return 'open';
    return 'unknown';
  }
  function pointInside(feats) {
    const b = B();
    if (!feats.length) return null;
    let bb = [180, 90, -180, -90];
    feats.forEach(f => { const x = f._bb || b.bbox(f.geometry); bb = [Math.min(bb[0], x[0]), Math.min(bb[1], x[1]), Math.max(bb[2], x[2]), Math.max(bb[3], x[3])]; });
    const la0 = (bb[1] + bb[3]) / 2, lo0 = (bb[0] + bb[2]) / 2;
    if (feats.some(f => b.inside(la0, lo0, f.geometry))) return [la0, lo0];
    for (let i = 1; i <= 6; i++) for (let j = 1; j <= 6; j++) {
      const la = bb[1] + (bb[3] - bb[1]) * i / 7, lo = bb[0] + (bb[2] - bb[0]) * j / 7;
      if (feats.some(f => b.inside(la, lo, f.geometry))) return [la, lo];
    }
    const line = b.linesOf(feats[0].geometry)[0] || [];
    if (line[0]) return [line[0][1], line[0][0]];
    return [la0, lo0];
  }

  async function ready() {
    if (pack) return pack;
    const b = B();
    const [base, counties, ov, corps, owners] = await Promise.all([
      b.ky(),
      b.jget('kpc-ky-counties.json').catch(() => []),
      b.jget('ky-overlaps.geojson').catch(() => ({ features: [] })),
      b.jget('ky-usace.geojson').catch(() => ({ features: [] })),
      b.jget('data/ky-wma-owners.json').catch(() => null)
    ]);
    const feats = (base || []).slice();
    (corps.features || []).forEach(f => {
      if (!f.geometry || !b.ringsOf(f.geometry).length) return;
      f._L = { k: 'busace', name: 'Army Corps of Engineers land', agency: 'U.S. Army Corps of Engineers', note: 'Corps land is generally not added. Only a few sites are exceptions.' };
      f._bb = b.bbox(f.geometry);
      f._nm = (f.properties || {}).NAME || 'Army Corps land';
      feats.push(f);
    });
    const overlaps = (ov.features || []).filter(f => f.geometry && b.ringsOf(f.geometry).length).map(f => { f._bb = b.bbox(f.geometry); return f; });
    pack = { feats: feats.filter(f => f.geometry && !blocked(f)), counties: counties || [], overlaps, owners: (owners && owners.wmas) || {} };
    return pack;
  }

  function countyOf(la, lo) {
    const b = B();
    for (const c of (pack && pack.counties) || []) {
      for (const ring of c.r || []) {
        if (ring && ring.length > 2 && b.inside(la, lo, { type: 'Polygon', coordinates: [ring] })) return c.n;
      }
    }
    return '';
  }
  function overlapsAt(la, lo) {
    const b = B(), out = [];
    for (const f of (pack && pack.overlaps) || []) {
      const bb = f._bb;
      if (lo < bb[0] || lo > bb[2] || la < bb[1] || la > bb[3]) continue;
      if (b.inside(la, lo, f.geometry)) out.push(f);
    }
    return out;
  }
  function scan(la, lo) {
    const b = B(), inside = [], near = [];
    for (const f of pack.feats) {
      const bb = f._bb;
      if (!bb || lo < bb[0] - 0.02 || lo > bb[2] + 0.02 || la < bb[1] - 0.02 || la > bb[3] + 0.02) continue;
      const inn = b.inside(la, lo, f.geometry);
      const e = b.edge(la, lo, f.geometry);
      const row = { f, inn, edgeKm: e.km, acres: acresOfFeat(f) };
      if (inn) inside.push(row);
      else if (e.km < 1.6) near.push(row);
    }
    const area = r => { const x = r.f._bb; return (x[2] - x[0]) * (x[3] - x[1]); };
    inside.sort((a, c) => area(a) - area(c));
    near.sort((a, c) => a.edgeKm - c.edgeKm);
    return { inside, near: near.slice(0, 5) };
  }
  function parksNear(la, lo, kmMax) {
    const b = B(), P = (b.kyData() && b.kyData().parks) || [];
    return P.map(p => ({ p, km: b.km(la, lo, p.la, p.lo) })).filter(x => x.km <= kmMax).sort((a, c) => a.km - c.km).slice(0, 6);
  }
  function featParks(f) {
    try {
      const info = B().landInfo(f);
      const own = (info.own || []).map(r => ({ ref: r.ref, name: r.name }));
      const pins = (info.pins || []).map(r => ({ ref: r.ref, name: r.name }));
      return { own, pins, info };
    } catch (e) { return { own: [], pins: [], info: null }; }
  }

  let locP = null;
  async function loadLocations() {
    if (locP) return locP;
    locP = B().jget('locations.json').then(rows => (rows || []).filter(r => r && r[0] === 'POTA')).catch(() => []);
    return locP;
  }

  const PADUS = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query';
  const PAD_FIELDS = 'OBJECTID,Unit_Nm,Loc_Nm,Mang_Name,Mang_Type,Own_Name,Own_Type,Loc_Own,Loc_Mang,Des_Tp,GIS_Acres,Source_PAID,State_Nm,Pub_Access,Category,GAP_Sts';
  const KDFWR_SEARCH = 'https://app.fw.ky.gov/Public_Lands_Search/default.aspx';
  const TIER_WORD = { FED: 'federal', STAT: 'state', LOC: 'county or city', PVT: 'private', NGO: 'non-profit', TRIB: 'tribal', JNT: 'joint', DIST: 'district', UNK: 'not stated', TERR: 'territorial' };

  function ownerRec(name) {
    const b = B(), bag = pack.owners || {}, keys = Object.keys(bag);
    const hit = keys.find(k => b.norm(k) === b.norm(name)) || keys.find(k => nameScore(name, k) >= 92);
    return hit ? bag[hit] : null;
  }
  function partiesFrom(says) {
    const text = String(says || '');
    const found = [];
    const add = (name, tier) => { if (name && !found.some(f => f.name === name)) found.push({ name, tier }); };
    if (/kentucky department of fish (?:and|&) wildlife|\bkdfwr\b/i.test(text)) add('Kentucky Department of Fish and Wildlife Resources', 'state');
    if (/division of forestry/i.test(text)) add('Kentucky Division of Forestry', 'state');
    if (/nature preserves/i.test(text)) add('Kentucky State Nature Preserves Commission', 'state');
    if (/kentucky state parks|state parks/i.test(text)) add('Kentucky State Parks', 'state');
    if (/forest service/i.test(text)) add('U.S. Forest Service', 'federal');
    if (/national park service/i.test(text)) add('National Park Service', 'federal');
    if (/fish (?:and|&) wildlife service/i.test(text)) add('U.S. Fish and Wildlife Service', 'federal');
    if (/corps of engineers/i.test(text)) add('U.S. Army Corps of Engineers', 'corps');
    (text.match(/[A-Z][A-Za-z.]+(?: [A-Z][A-Za-z.]+)? County Fiscal Court/g) || []).forEach(c => add(c, 'county'));
    if (/\b(LLC|LLLP|L\.L\.C\.|Inc\.)\b/.test(text)) add('a private company named in the sentence', 'private');
    return found;
  }
  function rule(v, title, field, evidence) { return { v, title, field, evidence }; }
  function ownRule(label, parties, field, evidence) {
    if (!evidence) return rule('unknown', label, field, 'No sentence or code is stored in ' + field + '.');
    if (!parties.length) return rule('unknown', label, field, 'The text is stored, but it does not name an owner this checker recognizes. Text: ' + evidence);
    const qual = parties.filter(p => p.tier === 'state' || p.tier === 'federal');
    const other = parties.filter(p => p.tier === 'county' || p.tier === 'city' || p.tier === 'private');
    const corps = parties.filter(p => p.tier === 'corps');
    const list = parties.map(p => p.name + ' (' + p.tier + ')').join('; ');
    if (other.length && qual.length) return rule('unknown', label, field, evidence + ' Named: ' + list + '. A qualifying agency and a county, city or private party are both named. Joint ownership is not a pass and not a fail in the written rule, so it stays unknown.');
    if (other.length) return rule('fail', label, field, evidence + ' Named: ' + list + '. County, city and private owners are not a qualifying tier.');
    if (corps.length && qual.length) return rule('unknown', label, field, evidence + ' Named: ' + list + '. The Corps is named along with another agency. Corps land is not treated as an ordinary yes.');
    if (corps.length) return rule('unknown', label, field, evidence + ' Named: ' + list + '. The Corps is the owner on this sentence. That is not recorded as a pass.');
    if (qual.length) return rule('pass', label, field, evidence + ' Named: ' + list + '.');
    return rule('unknown', label, field, evidence);
  }
  function codeRule(label, code, field) {
    const c = String(code || '').toUpperCase();
    if (!c) return rule('unknown', label, field, field + ' is blank.');
    if (c === 'FED' || c === 'STAT') return rule('pass', label, field, field + ' = ' + c + ' (' + (TIER_WORD[c] || c) + ').');
    if (c === 'JNT') return rule('unknown', label, field, field + ' = JNT (joint). The record does not say which governments, so this is not a pass or a fail.');
    if (c === 'UNK' || c === 'TERR') return rule('unknown', label, field, field + ' = ' + c + '.');
    return rule('fail', label, field, field + ' = ' + c + ' (' + (TIER_WORD[c] || c) + '). That tier is not federal or state.');
  }
  function accessRule(raw, field) {
    const a = String(raw || '');
    if (!a) return rule('unknown', 'Open to the public', field, field + ' is not on this record.');
    if (/^(OA|open|yes|public)$/i.test(a)) return rule('pass', 'Open to the public', field, field + ' = ' + a + '.');
    if (/^(XA|closed|no)$/i.test(a) || /closed to the public/i.test(a)) return rule('fail', 'Open to the public', field, field + ' = ' + a + '.');
    if (/restrict|permit|appointment|limited|^RA$/i.test(a)) return rule('unknown', 'Open to the public', field, field + ' = ' + a + '. Restricted access still needs the agency page. It is not marked fail or pass from this code alone.');
    return rule('unknown', 'Open to the public', field, field + ' = ' + a + '.');
  }
  /* One checklist. Every line cites the field it used. Nothing here is filled in by assumption. */
  function rulesFor(ctx) {
    const f = ctx.f, p = (f && f.properties) || {}, L = (f && f._L) || {};
    const own = ctx.owner;
    const pad = ctx.padExact || null;
    const says = (own && own.says) || '';
    const parties = partiesFrom(says);
    const rules = [];
    if (says) rules.push(ownRule('Owned by the federal or state government', parties, 'ky-wma-owners says', says));
    else if (p.OWNER || p.owner || p.Loc_Own) rules.push(ownRule('Owned by the federal or state government', partiesFrom(p.OWNER || p.owner || p.Loc_Own), 'owner field on the layer', p.OWNER || p.owner || p.Loc_Own));
    else if (pad && (pad.Own_Type || pad.Own_Name || pad.Loc_Own)) {
      const extra = [pad.Own_Name, pad.Loc_Own].filter(Boolean).join(' · ');
      const named = partiesFrom(extra);
      if (String(pad.Own_Type || '').toUpperCase() === 'JNT') {
        if (named.length && named.every(x => x.tier === 'state' || x.tier === 'federal')) rules.push(rule('pass', 'Owned by the federal or state government', 'PAD-US Own_Type and Loc_Own', 'Own_Type = JNT. Loc_Own / Own_Name names only state or federal agencies: ' + named.map(x => x.name).join('; ') + '.'));
        else rules.push(rule('unknown', 'Owned by the federal or state government', 'PAD-US Own_Type and Loc_Own', 'Own_Type = JNT. Loc_Own / Own_Name: ' + (extra || 'blank') + '. Joint ownership stays unknown unless every named party is federal or state.'));
      } else {
        const base = codeRule('Owned by the federal or state government', pad.Own_Type, 'PAD-US Own_Type');
        if (extra && /county|city of|fiscal court/i.test(extra) && base.v === 'pass') rules.push(rule('unknown', base.title, 'PAD-US Own_Type and Loc_Own', 'Own_Type = ' + pad.Own_Type + ', but Loc_Own / Own_Name also says: ' + extra + '.'));
        else rules.push(Object.assign(base, { evidence: base.evidence + (extra ? ' Own_Name / Loc_Own: ' + extra + '.' : '') }));
      }
    } else rules.push(rule('unknown', 'Owned by the federal or state government', 'owner sentence / PAD-US Own_Type', 'No owner sentence and no PAD-US owner code for this place.'));

    const mgrBits = [p.MANAGER, p.Loc_Mang, L.agency].filter(Boolean);
    if (p.MANAGER || p.Loc_Mang) {
      const m = p.MANAGER || p.Loc_Mang;
      if (/^(kdfwr|state)$/i.test(m) || /fish & wildlife|state parks|nature preserves|park service|forest service|fish & wildlife service/i.test(m)) rules.push(rule('pass', 'Managed by the federal or state government', 'MANAGER', 'MANAGER = ' + m + '.'));
      else if (/county|city|private|non-profit/i.test(m)) rules.push(rule('fail', 'Managed by the federal or state government', 'MANAGER', 'MANAGER = ' + m + '.'));
      else rules.push(rule('unknown', 'Managed by the federal or state government', 'MANAGER', 'MANAGER = ' + m + '. That word is not a federal or state agency name by itself.'));
    } else if (pad && pad.Mang_Type) rules.push(codeRule('Managed by the federal or state government', pad.Mang_Type, 'PAD-US Mang_Type').v ? Object.assign(codeRule('Managed by the federal or state government', pad.Mang_Type, 'PAD-US Mang_Type'), { evidence: 'Mang_Type = ' + (pad.Mang_Type || '') + '. Mang_Name = ' + (pad.Mang_Name || 'blank') + '. Loc_Mang = ' + (pad.Loc_Mang || 'blank') + '.' }) : rule('unknown', 'Managed by the federal or state government', 'MANAGER', 'No manager field.'));
    else if (L.agency && f) rules.push(rule('unknown', 'Managed by the federal or state government', 'layer agency', 'The outline comes from the ' + L.agency + ' layer (' + (L.name || '') + '). That says who published the layer, not who manages this tract, so management stays unknown.'));
    else rules.push(rule('unknown', 'Managed by the federal or state government', 'MANAGER', 'No manager field.'));

    if (/military reservation|army depot|national guard/i.test((f && f._nm) || (pad && pad.Unit_Nm) || '')) rules.push(rule('fail', 'Not named as a military base', 'name', 'The name says military reservation, army depot or national guard.'));
    else rules.push(rule('pass', 'Not named as a military base', 'name', 'The name does not say military reservation, army depot or national guard. The word Fort alone is not treated as a base.'));

    const accField = p.ACCESS ? 'ACCESS' : (p.Pub_Access ? 'Pub_Access' : (pad && pad.Pub_Access ? 'PAD-US Pub_Access' : ''));
    const accVal = p.ACCESS || p.Pub_Access || (pad && pad.Pub_Access) || '';
    rules.push(accessRule(accVal, accField || 'ACCESS / Pub_Access'));

    const des = p.TYPE || p.Loc_Ds || (pad && pad.Des_Tp) || '';
    const desField = p.TYPE ? 'TYPE' : (p.Loc_Ds ? 'Loc_Ds' : (pad && pad.Des_Tp ? 'PAD-US Des_Tp' : 'TYPE'));
    if (des) rules.push(rule('pass', 'Has a designated name and purpose', desField, desField + ' = ' + des + '.'));
    else rules.push(rule('unknown', 'Has a designated name and purpose', 'TYPE / Des_Tp', 'No designation field is stored.'));

    if (f && f.geometry && L.k !== 'bkpc' && !L.kpc && !L.proc && !/proclamation/i.test((pad && pad.Category) || '')) rules.push(rule('pass', 'Has an official boundary', (L.name || 'published layer'), 'The outline is the published ' + (L.name || 'layer') + '.'));
    else if (f && L.proc) rules.push(rule('fail', 'Has an official boundary', L.name || 'boundary line', 'This is the forest boundary line. Land inside that line is not all public.'));
    else if (f && (L.kpc || L.k === 'bkpc')) rules.push(rule('fail', 'Has an official boundary', 'OpenStreetMap outline', 'The only line is an OpenStreetMap sketch (ODbL). That is not an official boundary.'));
    else if (pad && pad.OBJECTID && /proclamation/i.test(pad.Category || '')) rules.push(rule('fail', 'Has an official boundary', 'PAD-US Category', 'Category = Proclamation. OBJECTID ' + pad.OBJECTID + '. That line is the administrative boundary. Land inside it is not all public.'));
    else if (pad && pad.OBJECTID) rules.push(rule('pass', 'Has an official boundary', 'PAD-US OBJECTID ' + pad.OBJECTID, 'PAD-US has a record. The boundary download link is the PAD-US geometry for that id.'));
    else rules.push(rule('unknown', 'Has an official boundary', 'layer geometry', 'No outline in the saved state layers and no PAD-US record id.'));

    const page = urlOf(f || { properties: {} }) || (own && own.url) || '';
    if (page && govUrl(page)) rules.push(rule('pass', 'Has an official government web page', 'URL', page));
    else if (page) rules.push(rule('unknown', 'Has an official government web page', 'URL', page + ' is stored, and it is not a .gov address.'));
    else rules.push(rule('unknown', 'Has an official government web page', 'URL', 'No page is stored on the layer or in the owner file.'));

    const pota = ctx.pota || [];
    const listName = (ctx.state && ctx.state.name) ? ctx.state.name + ' and the POTA list' : 'the POTA list';
    if (pota.length) rules.push(rule('fail', 'Not already a POTA park', listName, pota.map(x => x.ref + ' ' + x.name).join('; ') + '.'));
    else rules.push(rule('unknown', 'Not already a POTA park', listName, 'No park in the list we checked uses this name. The list can lag behind POTA, so this is not a pass.'));

    let summary = 'MAYBE';
    if (pota.length) summary = 'ALREADY';
    else if (rules.some(r => r.v === 'fail' && r.title !== 'Not already a POTA park')) summary = 'NO';
    else if (rules.some(r => r.v === 'unknown')) summary = 'MAYBE';
    else summary = 'YES';
    return { rules, summary, parties, says, page, mgr: mgrBits.join(' · ') };
  }

  function padWhere(words, code) {
    const st = String(code || 'KY').replace(/[^A-Z]/g, '');
    const tc = w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase();
    const clean = words.map(w => w.replace(/'/g, '')).filter(w => w.length > 2).slice(0, 3);
    if (!clean.length || !st) return [];
    return [
      "State_Nm='" + st + "' AND Unit_Nm LIKE '%" + clean.map(tc).join('%') + "%'",
      "State_Nm='" + st + "' AND Loc_Nm LIKE '%" + clean.map(w => w.toUpperCase()).join('%') + "%'"
    ];
  }
  async function padusQuery(where) {
    const j = await B().jget(PADUS + '?' + new URLSearchParams({ where, outFields: PAD_FIELDS, returnGeometry: false, f: 'json', resultRecordCount: '20' }), null, 12000).catch(() => null);
    return ((j && j.features) || []).map(f => f.attributes).filter(Boolean);
  }
  async function padusByName(q, code) {
    const core = tokens(canon(q).core);
    const words = core.length ? core : tokens(canon(q).full);
    const wheres = padWhere(words, code);
    if (words.length > 1) wheres.push.apply(wheres, padWhere(words.slice(0, 1), code));
    const seen = new Set(), rows = [];
    for (const w of wheres) {
      const got = await padusQuery(w);
      got.forEach(a => { if (!seen.has(a.OBJECTID)) { seen.add(a.OBJECTID); a._score = Math.max(nameScore(q, a.Unit_Nm || ''), nameScore(q, a.Loc_Nm || '')); rows.push(a); } });
    }
    return rows.sort((a, b) => b._score - a._score);
  }
  async function padusAt(la, lo) {
    if (!Number.isFinite(la)) return [];
    const j = await B().jget(PADUS + '?' + new URLSearchParams({
      geometry: lo + ',' + la, geometryType: 'esriGeometryPoint', inSR: '4326', spatialRel: 'esriSpatialRelIntersects',
      where: '1=1', outFields: PAD_FIELDS, returnGeometry: false, f: 'json', resultRecordCount: '8'
    }), null, 12000).catch(() => null);
    const rows = ((j && j.features) || []).map(f => f.attributes).filter(a => a && !/^Easement$/i.test(a.Category || ''));
    const rank = a => {
      const own = String(a.Own_Type || '').toUpperCase();
      return [/proclamation/i.test(a.Category || '') ? 1 : 0, (own === 'FED' || own === 'STAT' || own === 'JNT') ? 0 : 1, +a.GIS_Acres || 0];
    };
    rows.sort((a, b) => { const A = rank(a), B = rank(b); return A[0] - B[0] || A[1] - B[1] || A[2] - B[2]; });
    return rows;
  }
  async function padGeom(id, name) {
    const j = await B().jget(PADUS + '?' + new URLSearchParams({ objectIds: String(id), outFields: 'Unit_Nm,Category', returnGeometry: 'true', outSR: '4326', f: 'geojson', geometryPrecision: '5', maxAllowableOffset: '0.0004' }), null, 15000).catch(() => null);
    const f = j && j.features && j.features[0];
    if (!f || !f.geometry || blocked(f)) return null;
    f._nm = name || (f.properties && f.properties.Unit_Nm) || '';
    f._L = { k: 'padus', name: 'PAD-US outline', agency: 'USGS PAD-US', proc: /proclamation/i.test((f.properties && f.properties.Category) || '') };
    f._bb = B().bbox(f.geometry);
    return f;
  }
  function padLink(a) {
    if (a && a.OBJECTID) return PADUS + '?objectIds=' + encodeURIComponent(a.OBJECTID) + '&outFields=*&f=html';
    return '';
  }
  function padGeo(a) {
    if (a && a.OBJECTID) return PADUS + '?objectIds=' + encodeURIComponent(a.OBJECTID) + '&outFields=Unit_Nm,Source_PAID&returnGeometry=true&outSR=4326&f=geojson';
    return '';
  }

  async function locNear(la, lo, kmMax) {
    const rows = await loadLocations();
    const b = B(), out = [];
    rows.forEach(r => {
      const name = r[2] || '';
      if (BLOCKED.test(name)) return;
      const km = b.km(la, lo, +r[3], +r[4]);
      if (km <= kmMax) out.push({ ref: r[1], name, la: +r[3], lo: +r[4], web: r[5] || '', km });
    });
    out.sort((a, c) => a.km - c.km);
    return out.slice(0, 8);
  }
  async function find(q, state) {
    q = String(q || '').trim();
    if (q.length < 2) return [];
    await ready();
    const b = B(), ref = normRef(q);
    const st = state || await chosenState(q);
    const name = st.q || q;
    const hits = [];
    const useLocal = st.code === 'KY';
    if (!st.code) {
      const rows = await loadLocations();
      rows.forEach(r => {
        const nm = r[2] || '';
        if (BLOCKED.test(nm)) return;
        const score = ref && r[1] === ref ? 100 : nameScore(name, nm);
        if (score < 52) return;
        hits.push({ score, ref: r[1], name: nm, la: +r[3], lo: +r[4], web: r[5] || '', kind: 'pota', state: String(r[1] || '').split('-')[0] });
      });
    }
    if (useLocal) {
      const parks = (b.kyData() && b.kyData().parks) || [];
      parks.forEach(p => {
        if (BLOCKED.test(p.n || '')) return;
        const score = ref && p.c === ref ? 100 : nameScore(name, p.n);
        if (score >= 52) hits.push({ score, ref: p.c, name: p.n, la: p.la, lo: p.lo, web: p.web, kind: 'pota', state: 'KY' });
      });
      pack.feats.forEach(f => {
        if (blocked(f)) return;
        const n = f._nm || '';
        const score = ref && (f.properties || {}).ref === ref ? 100 : nameScore(name, n);
        if (score < 52) return;
        if (hits.some(h => h.kind === 'pota' && h.score >= 80 && (b.sameName(h.name, n) || nameScore(h.name, n) >= 84))) return;
        hits.push({ score, ref: (f.properties || {}).ref || '', name: n, la: null, lo: null, web: urlOf(f), kind: 'land', f, state: 'KY' });
      });
    }
    if (st.code && st.code !== 'KY') {
      const key = await stateKey(st.code);
      const parks = (key && key.parks) || {};
      const idx = await loadLocations().then(rows => { const m = new Map(); rows.forEach(r => m.set(r[1], r)); return m; });
      Object.keys(parks).forEach(id => {
        const p = parks[id];
        if (!p || BLOCKED.test(p.n || '')) return;
        const score = ref && id === ref ? 100 : nameScore(name, p.n || '');
        if (score < 52) return;
        const row = idx.get(id);
        hits.push({ score, ref: id, name: p.n, la: row ? +row[3] : null, lo: row ? +row[4] : null, web: row ? (row[5] || '') : '', kind: 'key', state: st.code });
      });
    }
    if (window.KPCMapLogic && st.code === 'KY') {
      KPCMapLogic.watchHits(name).forEach(w => {
        if (hits.some(h => nameScore(h.name, w.name) >= 90)) return;
        hits.push({ score: nameScore(name, w.name), ref: '', name: w.name, la: null, lo: null, web: w.url, kind: 'watch', state: 'KY' });
      });
    }
    if (ref && ref.indexOf('US-') === 0 && !hits.some(h => h.ref === ref && h.score >= 100)) {
      const rows = await loadLocations();
      const row = rows.find(r => r[1] === ref);
      if (row && !BLOCKED.test(row[2] || '')) {
        const at = stateAt(+row[3], +row[4], await loadStates());
        if (at && !at.local) {
          const key = await stateKey(at.code);
          const named = key && key.parks && key.parks[ref];
          hits.push({ score: 100, ref, name: (named && named.n) || row[2], la: +row[3], lo: +row[4], web: row[5] || '', kind: named ? 'key' : 'pota', state: at.code });
        }
      }
    }
    hits.sort((a, c) => c.score - a.score || String(a.name).localeCompare(String(c.name)));
    const seen = new Set();
    return hits.filter(h => { const k = (h.ref || '') + '|' + canon(h.name).core; if (seen.has(k)) return false; seen.add(k); return true; }).slice(0, 12);
  }

  async function elsewhere(q) {
    const rows = await loadLocations();
    const out = [];
    rows.forEach(r => {
      const name = r[2] || '';
      if (BLOCKED.test(name)) return;
      const score = nameScore(q, name);
      if (score >= 80) out.push({ score, ref: r[1], name, la: +r[3], lo: +r[4], web: r[5] || '' });
    });
    out.sort((a, c) => c.score - a.score);
    const seen = new Set();
    return out.filter(h => { if (seen.has(h.ref)) return false; seen.add(h.ref); return true; }).slice(0, 5);
  }

  function primaryParks(rows) {
    const m = new Map();
    rows.forEach(r => (r.own || []).concat(r.pins || []).forEach(p => { if (p.ref) m.set(p.ref, p); }));
    return [...m.values()];
  }

  function agencyLinks(f, owner, state, pad) {
    const L = (f && f._L) || {}, p = (f && f.properties) || {};
    const out = [];
    const add = (label, url) => { if (url && !out.some(x => x[1] === url)) out.push([label, url]); };
    const page = urlOf(f || { properties: {} }) || (owner && owner.url) || '';
    if (page) add('Agency page for this place', page);
    const code = (state && state.code) || 'KY';
    const blob = [p.MANAGER, L.agency, L.k, p.TYPE, pad && pad.Mang_Name, pad && pad.Loc_Mang, pad && pad.Own_Name, pad && pad.Des_Tp, pad && pad.Unit_Nm].filter(Boolean).join(' ');
    if (!state || state.local || state.assumed || code === 'KY') {
      if (/kdfwr|fish & wildlife|bwma|hunting/i.test(blob)) add('Kentucky Fish & Wildlife', 'https://fw.ky.gov/');
      if (/kdfwr|fish & wildlife|bwma|wildlife management/i.test(blob)) add('KDFWR public-lands search', KDFWR_SEARCH);
      if (/state park|bstate/i.test(blob)) add('Kentucky State Parks', 'https://parks.ky.gov/');
      if (/nature preserve|bsnp|bsna/i.test(blob)) add('Office of Kentucky Nature Preserves', 'https://eec.ky.gov/Nature-Preserves/Pages/default.aspx');
      if (/park service|bnps/i.test(blob)) add('National Park Service', 'https://www.nps.gov/');
      if (/fish & wildlife service|bfws/i.test(blob)) add('U.S. Fish & Wildlife Service', 'https://www.fws.gov/');
      if (/forest service|bdbnf|national forest/i.test(blob)) add('U.S. Forest Service', 'https://www.fs.usda.gov/');
      if (/corps|busace/i.test(blob)) add('U.S. Army Corps of Engineers', 'https://www.usace.army.mil/');
    }
    if (state && !state.local) homesFor(code).forEach(([label, url]) => add(label, url));
    ((agTable().FEDA) || []).forEach(([label, host, re]) => { if (re && re.test(blob)) add(label, 'https://' + host + '/'); });
    return out;
  }
  const PAD_LOOK = '<p class="mr-padlook">On the PAD-US record, look at who owns the land, who manages it, the designation, the acres, and public access.</p>';
  function padTable(a) {
    if (!a) return '';
    const gap = a.GAP_Sts == null || a.GAP_Sts === '' ? 'blank' : (GAP_WORD[String(a.GAP_Sts)] || ('GAP ' + a.GAP_Sts));
    const rows = [['Unit_Nm', a.Unit_Nm], ['Mang_Name', a.Mang_Name], ['Own_Name', a.Own_Name], ['Loc_Own', a.Loc_Own], ['Loc_Mang', a.Loc_Mang], ['Des_Tp', a.Des_Tp], ['GAP_Sts', gap], ['GIS acres', a.GIS_Acres], ['Source_PAID', a.Source_PAID], ['Pub_Access', a.Pub_Access], ['State_Nm', a.State_Nm], ['OBJECTID', a.OBJECTID]];
    return PAD_LOOK + `<table class="mr-recbox">${rows.map(([k, v]) => `<tr><th>${esc(k)}</th><td>${esc(v == null || v === '' ? 'blank' : v)}</td></tr>`).join('')}</table>`
      + `<p class="mr-help"><a href="${esc(padLink(a))}" target="_blank" rel="noopener">PAD-US record ↗</a>`
      + (padGeo(a) ? ` · <a href="${esc(padGeo(a))}" target="_blank" rel="noopener">Boundary download (GeoJSON) ↗</a>` : '') + '</p>';
  }
  function rulesHtml(R) {
    const cls = { pass: 'yes', fail: 'no', unknown: 'check' };
    const word = { pass: 'PASS', fail: 'FAIL', unknown: 'UNKNOWN' };
    return R.rules.map(r => `<div class="mr-r ${cls[r.v] || 'check'}"><i>${word[r.v] || 'UNKNOWN'}</i><div><b>${esc(r.title)}</b><p>${esc(r.evidence)}</p><p class="mr-help">Evidence field: ${esc(r.field)}</p></div></div>`).join('');
  }
  function summaryWord(s) {
    return s === 'YES' ? 'LIKELY YES — COULD BE ADDED' : s === 'NO' ? 'LIKELY NO' : s === 'ALREADY' ? 'ALREADY A POTA PARK' : 'MAYBE — A RULE IS STILL UNKNOWN';
  }
  function drawOnMap(la, lo, feats, overlaps) {
    if (!map) return;
    if (drawLayer) { map.removeLayer(drawLayer); drawLayer = null; }
    const fc = { type: 'FeatureCollection', features: (feats || []).filter(f => f && f.geometry && !blocked(f)).map(f => ({ type: 'Feature', properties: { name: f._nm || '' }, geometry: f.geometry })) };
    const ov = { type: 'FeatureCollection', features: (overlaps || []).map(f => ({ type: 'Feature', properties: {}, geometry: f.geometry })) };
    drawLayer = L.layerGroup();
    if (fc.features.length) L.geoJSON(fc, { style: { color: '#8a5a00', weight: 3, fillColor: '#d5a63a', fillOpacity: 0.18 } }).addTo(drawLayer);
    if (ov.features.length) L.geoJSON(ov, { style: { color: '#6b4a10', weight: 2, dashArray: '6 4', fillOpacity: 0 } }).addTo(drawLayer);
    drawLayer.addTo(map);
    const b = L.latLngBounds([[la, lo]]);
    try { if (fc.features.length) b.extend(L.geoJSON(fc).getBounds()); } catch (e) {}
    map.fitBounds(b.pad(0.3), { maxZoom: 14 });
    const dropPin = () => {
      if (pinCtl) { pinCtl.drop(L.latLng(la, lo)); return; }
      if (pinMarker) pinMarker.remove();
      pinMarker = L.marker([la, lo], { draggable: true, title: 'Dropped pin' }).addTo(map);
      pinMarker.on('dragend', () => { const p = pinMarker.getLatLng(); showPoint(p.lat, p.lng); });
    };
    dropPin();
    setTimeout(() => { if (map) { map.invalidateSize(); dropPin(); } }, 80);
  }

  function renderContext(ctx) {
    const box = $('mrSpot'); if (!box) return;
    const f = ctx.f, p = (f && f.properties) || {}, L = (f && f._L) || {};
    const R = rulesFor(ctx);
    const acres = ctx.acres || (f ? acresOfFeat(f) : 0) || (ctx.padExact && +ctx.padExact.GIS_Acres) || 0;
    const st = ctx.state || { code: '', name: '', local: false };
    const place = st.name || 'this place';
    const title = (f && f._nm) || (ctx.padExact && ctx.padExact.Unit_Nm) || ctx.title || ('No published ' + place + ' layer for this name');
    const kv = (k, v) => `<div class="mr-kv"><dt>${esc(k)}</dt><dd>${v}</dd></div>`;
    const links = agencyLinks(f, ctx.owner, st, ctx.padExact);
    if (!f && st.code === 'KY') {
      links.push(['Kentucky Fish & Wildlife', 'https://fw.ky.gov/']);
      links.push(['KDFWR public-lands search', KDFWR_SEARCH]);
      links.push(['Kentucky State Parks', 'https://parks.ky.gov/']);
    }
    if (!f && st.code !== 'KY') homesFor(st.code).forEach(pair => { if (!links.some(x => x[1] === pair[1])) links.push(pair); });
    const q = ctx.query || title;
    const nameQ = "State_Nm='" + st.code + "' AND Unit_Nm LIKE '%" + tokens(canon(q).core).slice(0, 2).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join('%') + "%'";
    const padSearch = PADUS + '?' + new URLSearchParams({ where: nameQ, outFields: PAD_FIELDS, returnGeometry: 'false', f: 'html' }).toString();
    const pota = ctx.pota || [];
    const say = `<div class="mr-say"><b>Before you click an official link.</b> This is a helper, not the final word. Open every link and research the land yourself before you submit a park. We match published government outlines (PAD-US and our state layers), then ownership, manager, designation and public access, and compare that with POTA’s published rules. We can miss a new tract, a joint owner, an easement, a private inholding or a name change. The agency page and the PAD-US record always win over this summary.</div>`;
    const linkBlock = say + `<div class="mr-links">${links.map(([lab, url]) => `<a class="k-off" href="${esc(url)}" target="_blank" rel="noopener"><b>${esc(lab)}</b><span>${esc(url)}</span></a>`).join('')}`
      + (pota.length ? pota.map(x => `<a class="k-pota" href="https://pota.app/#/park/${encodeURIComponent(x.ref)}" target="_blank" rel="noopener"><b>POTA park page ${esc(x.ref)}</b><span>https://pota.app/#/park/${esc(x.ref)}</span></a>`).join('') : `<a class="k-pota" href="https://pota.app/" target="_blank" rel="noopener"><b>POTA park page</b><span>No park in the ${esc(place)} list uses this name, so there is no park-page link yet.</span></a>`)
      + (ctx.padExact ? `<a class="k-off" href="${esc(padLink(ctx.padExact))}" target="_blank" rel="noopener"><b>PAD-US record</b><span>${esc(padLink(ctx.padExact))}</span></a>` : `<a class="k-off" href="${esc(padSearch)}" target="_blank" rel="noopener"><b>PAD-US name search for ${esc(place)}</b><span>${esc(padSearch)}</span></a>`)
      + (f ? `<a href="#" data-dl="1"><b>Download this boundary (GeoJSON)</b><span>The outline from the published layer, saved from this page.</span></a>` : '')
      + `</div>`;
    const miss = !f ? `<div class="mr-miss"><b>Not in our ${esc(place)} layers yet.</b> ${st.local ? 'The published files on this site do not have this name.' : 'This state has no outlines saved on this site. Its answer key was loaded for this search.'} PAD-US was queried for ${esc(place)}${ctx.pin ? ' and at this pin' : ''}. Nothing was scraped.</div>` : '';
    const ownLine = ctx.owner && ctx.owner.says ? ctx.owner.says : (ctx.says || '');
    const official = miss
      + kv('Managing agency', esc((p.MANAGER && p.MANAGER + (L.agency ? ' · layer: ' + L.agency : '')) || L.agency || (ctx.padExact && (ctx.padExact.Mang_Name || ctx.padExact.Loc_Mang)) || ('Not in the ' + place + ' layers.')))
      + kv('Designation', esc(p.TYPE || p.Loc_Ds || (ctx.padExact && ctx.padExact.Des_Tp) || 'Not stated on a layer here.'))
      + kv('Ownership', ownLine ? esc(ownLine) : (ctx.padExact ? esc(['Own_Name ' + (ctx.padExact.Own_Name || 'blank'), 'Loc_Own ' + (ctx.padExact.Loc_Own || 'blank'), 'Own_Type ' + (ctx.padExact.Own_Type || 'blank')].join(' · ')) : 'No owner sentence is stored for this name.'))
      + (ctx.padExact && ctx.padExact.GAP_Sts != null && ctx.padExact.GAP_Sts !== '' ? kv('GAP status', esc(GAP_WORD[String(ctx.padExact.GAP_Sts)] || ('GAP ' + ctx.padExact.GAP_Sts))) : '')
      + kv('Acres', acres ? 'about ' + Math.round(acres).toLocaleString() : 'Not stated.')
      + (ctx.edgeNote ? kv('Pin and the boundary', esc(ctx.edgeNote)) : '')
      + `<h4 style="margin:12px 0 6px">Links</h4>${linkBlock}`
      + (ctx.padExact ? `<h4 style="margin:12px 0 6px">PAD-US record</h4>${padTable(ctx.padExact)}` : `<h4 style="margin:12px 0 6px">PAD-US</h4>${PAD_LOOK}<p class="mr-help">No PAD-US record in ${esc(place)} matched this name${ctx.pin ? ' or this pin' : ''}. The search link above opens the same query.</p>`)
      + (ctx.padNear && ctx.padNear.length ? `<p class="mr-help"><b>Other PAD-US names (not an exact hit):</b> ${ctx.padNear.slice(0, 5).map(a => `<a href="${esc(padLink(a))}" target="_blank" rel="noopener">${esc(a.Unit_Nm)}</a>`).join(', ')}.</p>` : '')
      + directoryBlock(st.code, [title, p.TYPE, p.Loc_Ds, p.MANAGER, L.agency, L.name, L.k, ctx.padExact && ctx.padExact.Des_Tp, ctx.padExact && ctx.padExact.Mang_Name, ctx.padExact && ctx.padExact.Unit_Nm].filter(Boolean).join(' '));
    const vClass = R.summary === 'YES' || R.summary === 'ALREADY' ? 'yes' : R.summary === 'NO' ? 'no' : 'maybe';
    const potaBody = pota.length
      ? pota.map(x => `<a href="https://pota.app/#/park/${encodeURIComponent(x.ref)}" target="_blank" rel="noopener">${esc(x.ref)}</a> ${esc(x.name)}`).join('<br>')
      : ('No park in the ' + place + ' list uses this name.');
    const elseHtml = (ctx.elsewhere || []).length ? `<p class="mr-help"><b>Similar names in the park list (other places, not this one):</b> ${ctx.elsewhere.map(x => `<a href="https://pota.app/#/park/${encodeURIComponent(x.ref)}" target="_blank" rel="noopener">${esc(x.ref)}</a> ${esc(x.name)}`).join('; ')}.</p>` : '';
    const where = Number.isFinite(ctx.la) ? `${ctx.la.toFixed(5)}, ${ctx.lo.toFixed(5)}` : 'no pin yet';
    box.innerHTML = `<section class="mr-res" data-mr-result="spot">
<div class="mr-head"><div class="mr-k">COULD THIS BE A PARK?</div><h2>${esc(title)}</h2><p>${esc(where)}${ctx.county ? ' · ' + esc(ctx.county + ' County') : ''}</p></div>
<div class="mr-sec mr-official"><h3>1 · Official information</h3>${official}</div>
<div class="mr-sec"><h3>2 · POTA status</h3><div class="mr-v ${vClass}" data-mr-verdict="${esc(summaryWord(R.summary))}"><b>${esc(summaryWord(R.summary))}</b></div><div class="mr-dl">${kv('Parks with this name', potaBody)}${elseHtml}</div></div>
<div class="mr-sec"><h3>3 · Rules checklist</h3><p class="mr-help">Pass, fail or unknown. Each line names the field it used. A blank field stays unknown. Nothing here is filled in by assumption.</p>${directoryBlock(st.code, [title, p.TYPE, p.Loc_Ds, p.MANAGER, L.agency, L.name, ctx.padExact && ctx.padExact.Des_Tp].filter(Boolean).join(' '))}${rulesHtml(R)}</div>
<div class="mr-sec"><h3>4 · KPC notes</h3>${L.note ? `<p>${esc(L.note)}</p>` : ''}${ctx.county ? `<p>County: ${esc(ctx.county)}. ` : '<p>'}${Number.isFinite(ctx.la) ? `Grid ${esc(grid(ctx.la, ctx.lo))}.` : ''}</p>
${ctx.overlapHtml || ''}<p class="mr-help">${INFO} <a href="kpc-about-info.html">About our information</a></p><p class="mr-help">Street map tiles are © OpenStreetMap contributors, ODbL. Outlines come from this place’s published key. A US place also uses PAD-US.</p></div>
</section>`;
    box.hidden = false;
    const dl = box.querySelector('[data-dl]');
    if (dl && f) dl.onclick = e => {
      e.preventDefault();
      const fc = { type: 'FeatureCollection', features: (ctx.feats || [f]).filter(x => x && x.geometry).map(x => ({ type: 'Feature', properties: { name: x._nm || title }, geometry: x.geometry })) };
      const blob = new Blob([JSON.stringify(fc)], { type: 'application/geo+json' });
      const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = title.replace(/[^A-Za-z0-9]+/g, '_').slice(0, 40) + '.geojson'; a.click();
    };
    if (f && Number.isFinite(ctx.la)) drawOnMap(ctx.la, ctx.lo, ctx.feats || [f], ctx.overlaps || []);
  }

  async function contextFromFeature(f, extra) {
    extra = extra || {};
    const b = B();
    const pt = Number.isFinite(extra.la) ? [extra.la, extra.lo] : (pointInside([f]) || [null, null]);
    const la = pt[0], lo = pt[1];
    const inn = Number.isFinite(la) && b.inside(la, lo, f.geometry);
    const edge = Number.isFinite(la) ? b.edge(la, lo, f.geometry) : { km: null };
    const fp = featParks(f);
    const owner = ownerRec(f._nm);
    let pad = extra.pad || [];
    if (!pad.length && (f._nm || Number.isFinite(la))) {
      const code = extra.state && extra.state.code;
      const [byName, at] = await Promise.all([f._nm ? padusByName(f._nm, code) : Promise.resolve([]), Number.isFinite(la) ? padusAt(la, lo) : Promise.resolve([])]);
      pad = byName.map(a => Object.assign({ _score: a._score || nameScore(f._nm, a.Unit_Nm || '') }, a));
      at.forEach(a => { if (!pad.some(x => x.OBJECTID === a.OBJECTID)) pad.push(Object.assign({ _score: 100 }, a)); });
    }
    const exact = pad.filter(a => (a._score || 0) >= 80);
    const near = pad.filter(a => (a._score || 0) < 80);
    const pinExact = pad.filter(a => a._score === 100 && !(a.Unit_Nm));
    const feeExact = exact.filter(a => !/proclamation/i.test(a.Category || ''));
    const padExact = feeExact[0] || exact[0] || pad.find(a => a._score === 100 && !/proclamation/i.test(a.Category || '')) || pad.find(a => a._score === 100) || null;
    return {
      f, feats: [f], la, lo, county: Number.isFinite(la) && (!extra.state || extra.state.local) ? countyOf(la, lo) : '',
      owner, pota: (extra.pota && extra.pota.length) ? extra.pota : (fp.own || []),
      state: extra.state || null,
      padExact: (exact[0] || null),
      padNear: near.filter(a => (a._score || 0) >= 52).slice(0, 5),
      acres: acresOfFeat(f),
      edgeNote: Number.isFinite(edge.km) ? (inn ? 'A point on this check is inside the boundary. The nearest edge is about ' + feetOrMi(edge.km) + ' away.' : 'The point used here is about ' + feetOrMi(edge.km) + ' outside the boundary.') : '',
      overlaps: Number.isFinite(la) ? overlapsAt(la, lo) : [],
      query: extra.query || f._nm,
      title: f._nm
    };
  }

  async function stateObj(code) {
    const rows = await loadStates();
    const row = rows.find(r => r.a === code);
    const known = placeList().find(r => r.code === code);
    return row ? { code: row.a, name: row.n, local: isLocal(row.a), region: 'US' } : (known || { code: code || '', name: code || '', local: false, region: '' });
  }
  function canadaHtml() {
    const names = agTable().PROVN || {};
    const list = Object.keys(names).length ? Object.keys(names).map(k => names[k] + ' (' + k + ')').join(', ') : 'Alberta (AB), British Columbia (BC), Manitoba (MB), New Brunswick (NB), Newfoundland and Labrador (NL), Northwest Territories (NT), Nova Scotia (NS), Nunavut (NU), Ontario (ON), Prince Edward Island (PE), Quebec (QC), Saskatchewan (SK), Yukon (YT)';
    return `<section class="mr-res" data-mr-result="canada"><div class="mr-head"><div class="mr-k">OUTSIDE THE UNITED STATES</div><h2>This pin is not in a US state</h2></div><div class="mr-sec"><p>This pin is not inside a US state, so this check does not guess a province. Provinces and territories: ${esc(list)}.</p><p class="mr-help">Pick the province in the Mapping desk to query CPCAD and the provincial layers that are marked ok. Newfoundland and Labrador outlines, Tokyo, Japan A10, South Africa SAPAD and Colorado CNHP outlines are not fetched.</p></div></section>`;
  }
  async function showPoint(la, lo) {
    await ensureAgencies();
    lastPin = { la: la, lo: lo };
    const my = ++gen;
    const box = $('mrSpot');
    if (box) box.innerHTML = '<p class="mr-msg">Finding which state this pin is in…</p>';
    mount();
    const st = stateAt(la, lo, await loadStates());
    if (st && $('mrCheckSt')) { $('mrCheckSt').value = st.code; paintPlaceButton(); if (window.KPCMapDesk && KPCMapDesk.syncPlace) KPCMapDesk.syncPlace(st.code); buildToggles(); }
    if (!st) {
      if (box) box.innerHTML = canadaHtml();
      const q0 = $('mrCheckQ'); if (q0 && document.activeElement !== q0) q0.value = la.toFixed(5) + ', ' + lo.toFixed(5);
      return { hit: false, region: 'off' };
    }
    if (box) box.innerHTML = '<p class="mr-msg">Checking ' + esc(st.name) + ' and PAD-US at this pin…</p>';
    await ready();
    if (my !== gen) return { hit: false, region: 'US', state: st.code };
    const pad = await padusAt(la, lo);
    if (my !== gen) return { hit: false, region: 'US', state: st.code };
    if (st.local) {
      const s = scan(la, lo);
      const row = (s.inside.filter(r => (r.f._L || {}).k !== 'bdbnf')[0]) || s.inside[0] || s.near[0];
      if (!row && !pad.length) {
        renderContext({ title: 'No published public land at this pin', la, lo, county: countyOf(la, lo), f: null, pota: [], padExact: null, padNear: [], pin: true, state: st, query: la.toFixed(4) + ', ' + lo.toFixed(4), edgeNote: 'This pin is not inside a published ' + st.name + ' layer.' });
      } else if (row) {
        const ctx = await contextFromFeature(row.f, { la, lo, state: st, pad: pad.map(a => Object.assign({ _score: 100 }, a)) });
        ctx.edgeNote = row.inn ? 'Your pin is inside this boundary. The nearest edge is about ' + feetOrMi(row.edgeKm) + ' away.' : 'Your pin is about ' + feetOrMi(row.edgeKm) + ' outside this boundary.';
        ctx.pin = true;
        ctx.state = st;
        const ov = overlapsAt(la, lo);
        if (ov.length) ctx.overlapHtml = `<div class="mr-ov"><p><b>Overlap file.</b> Our file lists these parks together at this pin: ${ov.map(g => (g.properties.pota || []).map(x => esc(x[0] + ' ' + x[1])).join(', ') || esc((g.properties.areas || []).join(', '))).join('; ')}.</p><p>${esc(OVERLAP_NOTE)}</p></div>`;
        renderContext(ctx);
      } else {
        renderContext({ title: pad[0].Unit_Nm, la, lo, county: countyOf(la, lo), f: null, pota: [], padExact: pad[0], padNear: pad.slice(1, 5), pin: true, state: st, query: pad[0].Unit_Nm, edgeNote: 'PAD-US has a record at this pin in ' + st.name + '. It is not in the saved ' + st.name + ' layers.' });
      }
      const q = $('mrCheckQ'); if (q && document.activeElement !== q) q.value = la.toFixed(5) + ', ' + lo.toFixed(5);
      return { hit: !!(row || pad.length), region: 'US', state: st.code, inKy: true };
    }
    const best = pad[0] || null;
    let f = null;
    if (best) { try { f = await padGeom(best.OBJECTID, best.Unit_Nm); } catch (e) { f = null; } }
    const nearP = await locNear(la, lo, 40);
    const pota = nearP.filter(p => (f && B().inside(p.la, p.lo, f.geometry)) || (best && nameScore(best.Unit_Nm || '', p.name) >= 92)).map(p => ({ ref: p.ref, name: p.name }));
    if (f) {
      const ctx = await contextFromFeature(f, { la, lo, state: st, pota, query: best.Unit_Nm, pad: pad.map(a => Object.assign({ _score: a.OBJECTID === best.OBJECTID ? 100 : 60 }, a)) });
      ctx.state = st;
      ctx.pin = true;
      const edge = B().edge(la, lo, f.geometry);
      const insideLine = B().inside(la, lo, f.geometry);
      ctx.edgeNote = (/proclamation/i.test(best.Category || '') ? 'PAD-US Category is Proclamation for this record. The line is the administrative boundary. Land inside it is not all public. ' : '') + (insideLine ? 'Your pin is inside this outline. The nearest edge is about ' + feetOrMi(edge.km) + ' away.' : 'Your pin is about ' + feetOrMi(edge.km) + ' from this outline.') + ' No name was required.';
      renderContext(ctx);
    } else if (best) {
      renderContext({ title: best.Unit_Nm, la, lo, f: null, pota, padExact: best, padNear: pad.slice(1, 5), pin: true, state: st, query: best.Unit_Nm, edgeNote: 'PAD-US has a record at this pin in ' + st.name + '.' });
    } else {
      renderContext({ title: 'No published public land at this pin', la, lo, f: null, pota: [], padExact: null, padNear: [], pin: true, state: st, query: la.toFixed(4) + ', ' + lo.toFixed(4), edgeNote: 'This pin is in ' + st.name + '. It is not inside a PAD-US fee record, and this state has no outlines saved on this site.' });
    }
    const q = $('mrCheckQ'); if (q && document.activeElement !== q) q.value = la.toFixed(5) + ', ' + lo.toFixed(5);
    return { hit: !!(f || best), region: 'US', state: st.code, inKy: false };
  }

  async function showHit(h) {
    await ensureAgencies();
    await ready();
    mount();
    const b = B();
    if ((h.kind === 'key' || (h.state && !isLocal(h.state))) && h.ref && B().usOutline) {
      const st = await stateObj(h.state);
      let drawn = null, outline = null;
      try { outline = await b.usOutline(h.ref, h.name, h.la || 0, h.lo || 0, [h.state]); } catch (e) { outline = null; }
      if (outline && !BLOCKED.test((outline.src || '') + ' ' + (outline.why || ''))) {
        const cand = (outline.fs || []).filter(x => x && x.geometry && !blocked(x));
        const la = h.la != null && Number.isFinite(+h.la) ? +h.la : null;
        const lo = h.lo != null && Number.isFinite(+h.lo) ? +h.lo : null;
        const scored = cand.map(f => ({ f, inn: la != null && b.inside(la, lo, f.geometry), acres: acresOfFeat(f), score: nameScore(h.name || '', f._nm || '') }));
        const inside = scored.filter(x => x.inn);
        const pool = inside.length ? inside : scored;
        pool.sort((a, c) => {
          if (inside.length) return (c.acres - a.acres) || (c.score - a.score);
          const ak = la == null ? 0 : b.edge(la, lo, a.f.geometry).km;
          const ck = la == null ? 0 : b.edge(la, lo, c.f.geometry).km;
          return ak - ck || c.score - a.score;
        });
        drawn = (pool[0] && pool[0].f) || null;
      }
      if (drawn) {
        const layerName = drawn._nm || '';
        drawn._L = { k: 'uskey', name: drawn._src || 'published key layer', agency: drawn._src || '', note: outline.label === 'approx' ? (outline.why || 'The answer key calls this outline approximate.') : (outline.note || '') };
        if (h.name) {
          if (layerName && nameScore(h.name, layerName) < 80) drawn._L.note = ((drawn._L.note ? drawn._L.note + ' ' : '') + 'The layer’s own name is ' + layerName + '.');
          drawn._nm = h.name;
        } else drawn._nm = layerName;
        drawn._bb = drawn._bb || b.bbox(drawn.geometry);
        const ctx = await contextFromFeature(drawn, { la: h.la != null && Number.isFinite(+h.la) ? +h.la : undefined, lo: h.lo != null && Number.isFinite(+h.lo) ? +h.lo : undefined, query: h.name, state: st, pota: [{ ref: h.ref, name: h.name }] });
        ctx.state = st;
        if (h.ref && !ctx.pota.some(p => p.ref === h.ref)) ctx.pota = [{ ref: h.ref, name: h.name }].concat(ctx.pota);
        renderContext(ctx);
        return { hit: true, region: 'US', state: st.code };
      }
    }
    let feats = [];
    if (h.f) feats = [h.f];
    if (h.ref) { try { const more = (await b.kyFor(h.ref)) || []; more.forEach(f => { if (!blocked(f) && feats.indexOf(f) < 0) feats.push(f); }); } catch (e) {} }
    if (!feats.length) pack.feats.forEach(f => { if (!blocked(f) && nameScore(h.name, f._nm) >= 84) feats.push(f); });
    if (feats.length > 1) {
      const qFull = canon(h.name || '').full;
      const rank = f => {
        let s = nameScore(h.name || f._nm, f._nm);
        if (h.la != null && Number.isFinite(+h.lo) && B().inside(+h.la, +h.lo, f.geometry)) s += 25;
        const full = canon(f._nm).full;
        if (/\bstate park\b/.test(qFull) && /\bnature preserve\b/.test(full) && !/\bnature preserve\b/.test(qFull)) s -= 20;
        return s;
      };
      feats.sort((a, b) => rank(b) - rank(a));
    }
    if (!feats.length) {
      const st = h.state ? await stateObj(h.state) : await chosenState(h.name);
      const pad = await padusByName(h.name, st.code);
      const exact = pad.filter(a => a._score >= 80);
      const elseNames = await elsewhere(h.name);
      renderContext({
        title: h.name, f: null, la: h.la != null && Number.isFinite(+h.la) ? +h.la : null, lo: h.lo != null && Number.isFinite(+h.lo) ? +h.lo : null,
        pota: h.ref ? [{ ref: h.ref, name: h.name }] : [],
        padExact: exact[0] || null, padNear: pad.filter(a => a._score < 80 && a._score >= 52).slice(0, 5),
        elsewhere: elseNames.filter(x => x.ref !== h.ref), query: h.name, state: st
      });
      if (h.la != null && Number.isFinite(+h.la)) drawOnMap(+h.la, +h.lo, [], []);
      return { hit: false };
    }
    const stHit = h.state ? await stateObj(h.state) : await chosenState(h.name);
    const ctx = await contextFromFeature(feats[0], { la: h.la != null && Number.isFinite(+h.la) ? +h.la : undefined, lo: h.lo != null && Number.isFinite(+h.lo) ? +h.lo : undefined, query: h.name, state: stHit });
    ctx.state = stHit;
    ctx.feats = feats;
    if (h.ref && !ctx.pota.some(p => p.ref === h.ref)) ctx.pota = [{ ref: h.ref, name: h.name }].concat(ctx.pota);
    renderContext(ctx);
    return { hit: true, inKy: Number.isFinite(ctx.la) ? b.inKY(ctx.la, ctx.lo) : false };
  }

  async function showQuery(q) {
    await ensureAgencies();
    const my = ++gen;
    const box = $('mrSpot');
    const st = await chosenState(q);
    const name = st.q || q;
    if (box) box.innerHTML = '<p class="mr-msg">Searching ' + esc(st.name) + (st.local ? ' layers' : '’s published key') + ', then PAD-US…</p>';
    const hits = await find(name, st);
    if (my !== gen) return hits;
    const exact = hits.filter(h => h.score >= 80);
    const near = hits.filter(h => h.score < 80);
    if (exact.length === 1 || (exact[0] && exact[0].score >= 90 && (!exact[1] || exact[1].score < 80))) {
      await showHit(exact[0]);
      return hits;
    }
    if (exact.length) {
      if (box) {
        box.innerHTML = `<div class="mr-res" data-mr-result="list"><div class="mr-head"><div class="mr-k">NAME SEARCH</div><h2>${exact.length} matches</h2><p>These names match in ${esc(st.name)}. Pick one.</p></div>
<div class="mr-sec">${exact.map((h, i) => `<button type="button" class="mr-pick" data-hit="${i}"><b>${esc(h.name)}</b><span>${esc(h.ref || (st.local ? 'saved layer' : 'answer key'))} · ${h.score}</span></button>`).join('')}</div></div>`;
        box.querySelectorAll('[data-hit]').forEach(btn => btn.onclick = () => showHit(exact[+btn.dataset.hit]));
      }
      return hits;
    }
    const pad = await padusByName(name, st.code);
    if (my !== gen) return hits;
    const padExact = pad.filter(a => a._score >= 80);
    const padNear = pad.filter(a => a._score < 80 && a._score >= 52);
    const elseNames = near.length ? [] : await elsewhere(q);
    if (padExact.length === 1 && !near.length) {
      renderContext({ title: padExact[0].Unit_Nm, f: null, pota: [], padExact: padExact[0], padNear: padNear.slice(0, 5), elsewhere: elseNames, query: name, state: st });
      return hits;
    }
    const nearBtns = near.map((h, i) => `<button type="button" class="mr-pick" data-near="${i}"><b>${esc(h.name)}</b><span>Near match · ${esc(h.ref || st.name)}</span></button>`).join('');
    const padBtns = padExact.concat(padNear).slice(0, 8).map(a => `<p class="mr-help"><a href="${esc(padLink(a))}" target="_blank" rel="noopener">${esc(a.Unit_Nm)}</a> · ${esc(a.Mang_Name || '')} · ${esc(a.Own_Name || '')} · ${a.GIS_Acres || 0} acres · Source_PAID ${esc(a.Source_PAID || 'blank')}</p>`).join('');
    if (box) box.innerHTML = `<section class="mr-res" data-mr-result="none"><div class="mr-head"><div class="mr-k">COULD THIS BE A PARK?</div><h2>${esc(q)}</h2></div>
<div class="mr-sec mr-official"><h3>1 · Official information</h3>
<div class="mr-miss"><b>Not an exact name in our ${esc(st.name)} layers.</b> ${near.length ? 'Near matches are listed below.' : (st.local ? 'Nothing in the published files is close to this name.' : 'The answer key for this state does not have this name.')} PAD-US was queried for ${esc(st.name)}. No page was scraped.</div>
${kvSafe('Managing agency', 'Not in the layers. Use the agency links below.')}
<div class="mr-say"><b>Before you click an official link.</b> This is a helper, not the final word. Open every link and research the land yourself before you submit a park. The agency page and the PAD-US record always win over this summary.</div>
<p class="mr-help">${(st.code === 'KY' ? [['Kentucky Fish & Wildlife', 'https://fw.ky.gov/'], ['KDFWR public-lands search', KDFWR_SEARCH], ['Kentucky State Parks', 'https://parks.ky.gov/']] : homesFor(st.code)).map(([lab, url]) => `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(lab)} ↗</a>`).join(' · ') || 'No agency home is stored for this state. Use the PAD-US link.'}</p>
<p class="mr-help"><a href="${esc(PADUS + '?' + new URLSearchParams({ where: "State_Nm='" + st.code + "' AND Unit_Nm LIKE '%" + tokens(canon(name).core).slice(0, 2).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join('%') + "%'", outFields: PAD_FIELDS, returnGeometry: 'false', f: 'html' }).toString())}" target="_blank" rel="noopener">PAD-US name search for ${esc(st.name)} ↗</a></p>
${PAD_LOOK}
${padExact.length ? '<h4>PAD-US records with this name</h4>' + padBtns : (padNear.length ? '<h4>PAD-US names that are only partly the same</h4>' + padBtns : '<p class="mr-help">PAD-US returned no ' + esc(st.name) + ' record for this name.</p>')}
${nearBtns ? '<h4>Near matches in our layers</h4>' + nearBtns : ''}
</div>
<div class="mr-sec"><h3>2 · POTA status</h3><p>${elseNames.length ? 'Similar names elsewhere, not this place: ' + elseNames.map(x => esc(x.ref + ' ' + x.name)).join('; ') : 'No similar park in the list was close enough to call a match.'}</p></div>
<div class="mr-sec"><h3>3 · Rules checklist</h3>${directoryBlock(st.code, name)}${rulesHtml(rulesFor({ f: null, pota: [], state: st, padExact: padExact.length === 1 ? padExact[0] : null }))}</div>
<div class="mr-sec"><h3>4 · KPC notes</h3><p class="mr-help">${INFO} <a href="kpc-about-info.html">About our information</a></p></div>
</section>`;
    if (box) box.querySelectorAll('[data-near]').forEach(btn => btn.onclick = () => showHit(near[+btn.dataset.near]));
    return hits;
  }
  function kvSafe(k, v) { return `<div class="mr-kv"><dt>${esc(k)}</dt><dd>${v}</dd></div>`; }

  function classifyAll() {
    const b = B();
    const groups = new Map();
    pack.feats.forEach(f => {
      if (blocked(f) || !f._nm) return;
      const key = (f._L && f._L.k) + '|' + b.norm(f._nm);
      const g = groups.get(key) || { name: f._nm, layer: (f._L && f._L.name) || '', agency: (f._L && f._L.agency) || '', feats: [], acres: 0 };
      g.feats.push(f); g.acres += acresOfFeat(f); groups.set(key, g);
    });
    const rows = [];
    groups.forEach(g => {
      const f = g.feats[0];
      const fp = featParks(f);
      const R = rulesFor({ f, owner: ownerRec(f._nm), pota: fp.own || [] });
      const pt = pointInside(g.feats) || [37.5, -85];
      rows.push({ name: g.name, layer: g.layer, agency: g.agency, acres: g.acres, v: R.summary, refs: fp.own || [], la: pt[0], lo: pt[1] });
    });
    const rank = { YES: 0, MAYBE: 1, NO: 2, ALREADY: 3 };
    rows.sort((a, c) => (rank[a.v] - rank[c.v]) || c.acres - a.acres || a.name.localeCompare(c.name));
    return rows;
  }
  async function showAll() {
    await ensureAgencies();
    const box = $('mrSpot');
    const stAll = await chosenState('');
    if (!stAll.code) { if (box) box.innerHTML = '<p class="mr-msg">Pick a state, province, or country. Check all reads that place’s published key. A name with no place searches every loaded region.</p>'; return []; }
    if (stAll.code !== 'KY') {
      if (box) box.innerHTML = '<p class="mr-msg">Reading the published key for ' + esc(stAll.name) + '…</p>';
      const key = await stateKey(stAll.code);
      const parks = (key && key.parks) || {};
      const ids = Object.keys(parks);
      const shown = ids.slice(0, 400);
      if (box) box.innerHTML = `<section class="mr-res" data-mr-result="all"><div class="mr-head"><div class="mr-k">CHECK ALL · ${esc(stAll.name.toUpperCase())}</div><h2>Published key</h2><p>${ids.length} parks in the ${esc(stAll.region === 'world' ? 'world' : stAll.region === 'CA' ? 'Canada' : 'US')} key. ${stAll.region === 'US' || !stAll.region ? 'PAD-US is the other official set for a US place.' : ''}</p></div><div class="mr-sec"><p class="mr-help">Outlines for this list come from that place’s published key. ${shown.length < ids.length ? 'The first ' + shown.length + ' names are listed.' : ''}</p>${shown.map(id => `<p><b>${esc((parks[id] && parks[id].n) || id)}</b> · ${esc(id)}</p>`).join('') || '<p>No published key for this place is on the site yet.</p>'}</div></section>`;
      return ids;
    }
    if (box) box.innerHTML = '<p class="mr-msg">Reading the published outlines for ' + esc(stAll.name) + '…</p>';
    mount();
    await ready();
    const rows = classifyAll();
    const counts = { YES: 0, MAYBE: 0, NO: 0, ALREADY: 0 };
    rows.forEach(r => { counts[r.v] = (counts[r.v] || 0) + 1; });
    const lab = { YES: 'Yes', MAYBE: 'Maybe', NO: 'No', ALREADY: 'Already a park' };
    if (!box) return rows;
    box.innerHTML = `<section class="mr-res" data-mr-result="all"><div class="mr-head"><div class="mr-k">CHECK ALL · ${esc(stAll.name.toUpperCase())}</div><h2>Published layers</h2><p>${rows.length} named places. Yes, no or maybe is about adding a new park. Already means POTA has a number for that land.</p></div>
<div class="mr-sec"><div class="mr-filters" id="mrFilters">${['YES', 'MAYBE', 'NO', 'ALREADY'].map(k => `<button type="button" class="mr-ag${k === 'YES' ? ' on' : ''}" data-f="${k}">${lab[k]} · ${counts[k] || 0}</button>`).join('')}</div>
<p class="mr-help">These outlines are the published copy saved for this place. Other places use their own published key, and a US place also uses PAD-US. Newfoundland and Labrador, Tokyo, Japan A10, South Africa SAPAD and Colorado CNHP outlines are not shown.</p>
<div id="mrAllRows"></div></div></section>`;
    const paint = (which) => {
      const host = $('mrAllRows'); if (!host) return;
      host.innerHTML = rows.filter(r => r.v === which).map(r => `<button type="button" class="mr-pick" data-la="${r.la}" data-lo="${r.lo}"><b>${esc(r.name)}</b><span>${esc(lab[r.v])}${r.refs.length ? ' · ' + esc(r.refs.map(p => p.ref).join(', ')) : ''} · ${r.acres ? Math.round(r.acres).toLocaleString() + ' acres · ' : ''}${esc(r.agency)}${r.id ? ' · PAD-US ' + esc(String(r.id)) : ''}</span></button>`).join('') || '<p class="mr-help">None in this group.</p>';
      host.querySelectorAll('.mr-pick').forEach(btn => btn.onclick = () => showPoint(+btn.dataset.la, +btn.dataset.lo));
    };
    paint('YES');
    $('mrFilters').querySelectorAll('[data-f]').forEach(btn => btn.onclick = () => {
      $('mrFilters').querySelectorAll('.mr-ag').forEach(x => x.classList.remove('on'));
      btn.classList.add('on'); paint(btn.dataset.f);
    });
    return rows;
  }

  function mount() {
    const el = $('mrDrop'); if (!el || map || !window.L) return;
    map = L.map(el, { scrollWheelZoom: true }).setView([39.8, -96.5], 4);
    if (window.KPCLayers) KPCLayers(map, 'Street');
    else L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap contributors, ODbL' }).addTo(map);
    if (window.KPCPin) {
      pinCtl = KPCPin(map, {
        skip: e => { const t = e.originalEvent && e.originalEvent.target; return !!(t && t.closest && t.closest('.leaflet-control, .leaflet-popup')); },
        onDrop: (la, lo) => showPoint(la, lo)
      });
    } else {
      map.on('click', e => {
        const t = e.originalEvent && e.originalEvent.target;
        if (t && t.closest && t.closest('.leaflet-control, .leaflet-popup')) return;
        showPoint(e.latlng.lat, e.latlng.lng);
      });
    }
    setTimeout(() => { if (map) map.invalidateSize(); }, 80);
    buildToggles();
    fillStateMenu();
  }

  async function buildToggles() {
    const host = $('mrLayerToggles'); if (!host) return;
    const summary = host.parentElement && host.parentElement.querySelector ? host.parentElement.querySelector('summary') : null;
    const code = (($('mrCheckSt') && $('mrCheckSt').value) || ($('mrDeskPlace') && $('mrDeskPlace').value) || '');
    const row = placeList().find(r => r.code === code);
    if (summary) summary.textContent = row ? ('LAYERS YOU CAN TURN ON · ' + row.name.toUpperCase()) : 'LAYERS YOU CAN TURN ON';
    if (!code) { host.innerHTML = '<p class="mr-help">Pick a state, province, or country. This list is that place’s live layers.</p>'; return; }
    let cat = null;
    try { cat = await fetch('data/maprep/catalog.json').then(r => r.ok ? r.json() : null); } catch (e) { cat = null; }
    const live = ((cat && cat.sources) || []).filter(s => s.place === code && s.live && s.enabled !== false && s.rest && !/services\d*\.arcgis\.com/i.test(s.rest) && !/33TOOklri9xpic7U/i.test(s.rest));
    if (!live.length) { host.innerHTML = '<p class="mr-help">No live layer is stored for ' + esc(code) + '.</p>'; return; }
    host.innerHTML = live.map(s => `<label class="mr-ag"><input type="checkbox" data-rest="${esc(s.rest)}" data-title="${esc(s.title)}"> ${esc(s.title)} <small>${esc(s.agency || '')}${s.credit ? ' · ' + esc(s.credit) : ''}</small></label>`).join('') + '<p class="mr-help">These are the live layers stored for this place. Search or pin vs this queries the ones you leave on. OpenStreetMap outlines are credited ODbL.</p>';
  }

  function wire() {
    const form = $('mrCheckForm'); if (!form) return;
    form.addEventListener('submit', e => {
      e.preventDefault();
      const q = ($('mrCheckQ').value || '').trim();
      const P = window.KPCparseLoc ? window.KPCparseLoc(q) : null;
      if (P) showPoint(P[0], P[1]);
      else showQuery(q);
    });
    const gps = $('mrCheckGps');
    if (gps) gps.onclick = () => {
      if (!navigator.geolocation) { const box = $('mrSpot'); if (box) box.innerHTML = '<p class="mr-msg">This device has no GPS. Type coordinates instead.</p>'; return; }
      const box = $('mrSpot'); if (box) box.innerHTML = '<p class="mr-msg">Getting a GPS fix…</p>';
      navigator.geolocation.getCurrentPosition(p => showPoint(p.coords.latitude, p.coords.longitude),
        err => { if (box) box.innerHTML = '<p class="mr-msg">Could not read GPS (' + esc(err.message) + '). Type the coordinates or drop a pin.</p>'; },
        { enableHighAccuracy: true, timeout: 20000, maximumAge: 15000 });
    };
    const all = $('mrCheckAll'); if (all) all.onclick = () => showAll();
    fillStateMenu();
  }

  wire();
  window.KPCMapCheck = { mount, find, showQuery, showPoint, showAll, ready, syncPlace, map: () => map, pin: () => lastPin };
})();
