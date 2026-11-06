/* Mapping Rep Tool Box helpers. No network. Safe to run under Node (node kpc-maprep-logic.js).
   The page loads the full abbreviation table from data/maprep/abbreviations.json.
   A short core list is built in so WMA / SNP / SNA / SP still match before that file arrives.
   This file does not read or write answer keys. */
(function (root, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.KPCMapLogic = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const CORE = [
    ['wma', 'wildlife management area'],
    ['snp', 'state nature preserve'],
    ['sna', 'state natural area'],
    ['sp', 'state park'],
    ['nwr', 'national wildlife refuge'],
    ['nf', 'national forest'],
    ['nra', 'national recreation area'],
    ['sga', 'state game area'],
    ['swa', 'state wildlife area'],
    ['srp', 'state resort park'],
    ['zec', 'zone d exploitation controlee']
  ];
  /* The desk covers the United States, Canada, and the English-speaking countries.
     Tract notes stay in this file. The page shows them only when tractsOn() is true. */
  const US_PLACES = [['AL','Alabama'],['AK','Alaska'],['AZ','Arizona'],['AR','Arkansas'],['CA','California'],['CO','Colorado'],['CT','Connecticut'],['DE','Delaware'],['DC','District of Columbia'],['FL','Florida'],['GA','Georgia'],['HI','Hawaii'],['ID','Idaho'],['IL','Illinois'],['IN','Indiana'],['IA','Iowa'],['KS','Kansas'],['KY','Kentucky'],['LA','Louisiana'],['ME','Maine'],['MD','Maryland'],['MA','Massachusetts'],['MI','Michigan'],['MN','Minnesota'],['MS','Mississippi'],['MO','Missouri'],['MT','Montana'],['NE','Nebraska'],['NV','Nevada'],['NH','New Hampshire'],['NJ','New Jersey'],['NM','New Mexico'],['NY','New York'],['NC','North Carolina'],['ND','North Dakota'],['OH','Ohio'],['OK','Oklahoma'],['OR','Oregon'],['PA','Pennsylvania'],['RI','Rhode Island'],['SC','South Carolina'],['SD','South Dakota'],['TN','Tennessee'],['TX','Texas'],['UT','Utah'],['VT','Vermont'],['VA','Virginia'],['WA','Washington'],['WV','West Virginia'],['WI','Wisconsin'],['WY','Wyoming']];
  const CA_PLACES = [['AB','Alberta'],['BC','British Columbia'],['MB','Manitoba'],['NB','New Brunswick'],['NL','Newfoundland and Labrador'],['NT','Northwest Territories'],['NS','Nova Scotia'],['NU','Nunavut'],['ON','Ontario'],['PE','Prince Edward Island'],['QC','Quebec'],['SK','Saskatchewan'],['YT','Yukon']];
  const WORLD_PLACES = [['GB','United Kingdom'],['IE','Ireland'],['AU','Australia'],['NZ','New Zealand']];
  function places() { return { us: US_PLACES, ca: CA_PLACES, world: WORLD_PLACES }; }
  function placeRows() {
    const out = [];
    US_PLACES.forEach(([code, name]) => out.push({ code: code, name: name, region: 'US' }));
    CA_PLACES.forEach(([code, name]) => out.push({ code: code, name: name, region: 'CA' }));
    WORLD_PLACES.forEach(([code, name]) => out.push({ code: code, name: name, region: 'world' }));
    return out;
  }
  function placeByCode(code) {
    return placeRows().find(r => r.code === String(code || '').toUpperCase()) || null;
  }
  /* Hidden. Default off. ?tracts=1 or localStorage kpcMapTracts=1 turns the tract box on. */
  function tractsOn() {
    try {
      if (typeof location !== 'undefined' && location && /(?:\?|&)tracts=1(?:&|$)/.test(String(location.search || ''))) return true;
      if (typeof localStorage !== 'undefined' && localStorage && localStorage.getItem('kpcMapTracts') === '1') return true;
    } catch (e) {}
    return false;
  }
  /* Names the club is watching. Muddygut is not in the saved state file yet (KDFWR id 9729). */
  const WATCH = [
    { name: 'Blackford Oaks WMA', state: 'KY', id: '9719', url: 'https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=9719' },
    { name: 'Muddygut WMA', state: 'KY', id: '9729', url: 'https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=9729' },
    { name: 'Crow Creek WMA', state: 'KY', id: '9731', url: 'https://app.fw.ky.gov/Public_Lands_Search/detail.aspx?Kdfwr_id=9731' }
  ];
  const BANNED = [/33TOOklri9xpic7U/i, /Grant_County_Interactive_Parcel_Map/i, /ncnhde\.natureserve\.org/i];
  const BLOCKED_PLACES = { CO: 1, TN: 1 };
  const PRIVATE_FIELD = /(owner|own_nm|^name$|mail|addr|street|grantee|taxpayer|^city$|^zip|^account|^deed|address)/i;
  const STOP = /\b(the|of|and|at|state|national|natural|nature|historic|historical|site|park|parks|wildlife|management|area|areas|wma|preserve|forest|recreation|recreational|refuge|sanctuary|center|fee|tract|unit|ky|resort|fishing|public|hunting|commission|corps|engineers|us)\b/g;
  const GOV_TYPES = /^(FED|STAT|DESG)$/i;
  const PUBLIC_WORDS = /\b(city|county|counties|fiscal court|state|commonwealth|kentucky|united states|national|federal|department|dept|division|office|district|university|college|authority|board|parks?|recreation|commission|corps|service|government|town|conservancy|land trust|foundation|society|association|nature|audubon|wildlife|resources|forestry|cabinet)\b/i;

  let compiled = [];
  let AGENCIES = null;
  const ROLE_RULES = [
    ['wildlife', /wildlife|fish|game|\bwma\b|hunting|refuge|waterfowl/i],
    ['parks', /state park|\bparks\b|historic site|recreation/i],
    ['preserves', /nature preserve|natural area|natural heritage|\bpreserve\b/i],
    ['forestry', /forest/i],
    ['heritage', /heritage|historic/i],
    ['lands', /trust land|state land|land board|land office/i]
  ];
  function loadAgencies(doc) {
    AGENCIES = doc && doc.places ? doc : { places: (doc && doc.places) || {} };
    return true;
  }
  function agenciesReady() { return !!(AGENCIES && AGENCIES.places); }
  /* Links for this state, chosen by the designation. If the designation names no agency, every agency for the place is returned. */
  function agencyMatches(code, text) {
    if (!agenciesReady()) return [];
    const place = AGENCIES.places[code];
    if (!place) return [];
    const roles = ROLE_RULES.filter(([, re]) => re.test(String(text || ''))).map(([r]) => r);
    const all = place.agencies || [];
    let rows = all.filter(a => (a.roles || [a.role]).some(r => roles.indexOf(r) >= 0));
    const matched = rows.length > 0;
    if (!matched) rows = all.slice();
    return rows.map(a => ({ name: a.name, role: a.role, roles: a.roles || [a.role], home: a.home || {}, finder: a.finder || {}, gis: a.gis || {}, matched: matched }));
  }

  function compile(rows) {
    const map = new Map();
    const add = (token, expansion) => {
      const list = map.get(token) || [];
      if (list.indexOf(expansion) < 0) list.push(expansion);
      map.set(token, list);
    };
    /* CORE is the existing Tool Box list. A later row is added beside it and never replaces it. */
    CORE.forEach(([t, e]) => add(t, e));
    (rows || []).forEach(r => {
      /* Name forms and spelling pairs are stored with their source. They are not expansions. */
      if (r.expand === false) return;
      const token = String(r.token || '').toLowerCase().replace(/\./g, '');
      const expansion = String(r.expansion || '').toLowerCase().replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim();
      if (token.length >= 2 && expansion) add(token, expansion);
    });
    compiled = [...map.entries()].sort((a, b) => b[0].length - a[0].length);
  }
  compile([]);

  function loadRows(rows) { compile(rows); return compiled.length; }

  function expandVariants(s) {
    let t = String(s || '').toLowerCase().replace(/&/g, ' and ');
    t = t.replace(/\b([a-z](?:\.[a-z]){1,6})\.?\b/g, m => m.replace(/\./g, ''));
    let outs = [t];
    compiled.forEach(([tok, exps]) => {
      const list = exps && exps.length ? exps : [];
      const re = new RegExp('(?<![a-z0-9])' + tok.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '(?![a-z0-9])', 'g');
      const next = [];
      outs.forEach(cur => {
        re.lastIndex = 0;
        if (!re.test(cur)) { next.push(cur); return; }
        list.forEach(exp => {
          re.lastIndex = 0;
          next.push(cur.replace(re, ' ' + exp + ' '));
        });
      });
      outs = next.slice(0, 8);
    });
    return outs.map(x => x.replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim());
  }
  /* The first expansion is the one the Tool Box already had. Later meanings are extra choices. */
  function expandName(s) {
    const v = expandVariants(s);
    return v.length ? v[0] : '';
  }

  function canonFrom(full) {
    const core = full.replace(/\b(wildlife|management|area|state|national|park|parks|nature|preserve|natural|forest|refuge|the|of|and|site|historic|historical|recreational|recreation|resort)\b/g, ' ').replace(/\s+/g, ' ').trim();
    return { full: full, core: core || full };
  }
  function canon(s) {
    return canonFrom(expandName(s));
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
  function normName(s) {
    return expandName(s).replace(STOP, ' ').replace(/\s+/g, ' ').trim();
  }
  /* Shorter name of at least two words is a whole-word prefix or suffix of the longer one. */
  function fuzzySame(a, b) {
    const n = normName(a), m = normName(b);
    if (!n || !m || n.length < 4 || m.length < 4) return false;
    if (n === m) return true;
    const w = n.split(' '), x = m.split(' ');
    const sh = w.length <= x.length ? w : x;
    const lo = w.length <= x.length ? x : w;
    if (sh.length < 2) return false;
    const S = sh.join(' ');
    return lo.slice(0, sh.length).join(' ') === S || lo.slice(-sh.length).join(' ') === S;
  }
  function scoreCanon(q, c, query, candidate) {
    if (!q.core || !c.core) return 0;
    if (q.core === c.core || q.full === c.full) return 96;
    const qt = tokens(q.core), ct = tokens(c.core);
    if (qt.length && qt.every(w => ct.indexOf(w) >= 0)) return ct.length === qt.length ? 92 : 84;
    if (fuzzySame(query, candidate)) return 88;
    const d = dice(q.core, c.core);
    const generic = { creek: 1, lake: 1, river: 1, fork: 1, branch: 1, ridge: 1, county: 1, hunting: 1, public: 1, north: 1, south: 1, east: 1, west: 1 };
    const shared = qt.filter(w => ct.indexOf(w) >= 0 && !generic[w] && w.length >= 4);
    if (d >= 0.8 && shared.length) return 70;
    if (d >= 0.72 && shared.length) return 58;
    if (shared.some(w => w.length >= 6) && d >= 0.45) return 52;
    return 0;
  }
  function nameScore(query, candidate) {
    const qs = expandVariants(query).map(canonFrom);
    const cs = expandVariants(candidate).map(canonFrom);
    let best = 0;
    for (let i = 0; i < qs.length; i++) {
      for (let j = 0; j < cs.length; j++) {
        const s = scoreCanon(qs[i], cs[j], query, candidate);
        if (s > best) best = s;
        if (best === 96) return 96;
      }
    }
    return best;
  }
  function searchNames(query, list) {
    return (list || []).map(item => {
      const name = typeof item === 'string' ? item : item.name;
      const score = nameScore(query, name);
      const base = typeof item === 'string' ? { name: item } : Object.assign({}, item);
      return Object.assign(base, { score: score });
    }).filter(x => x.score >= 52).sort((a, b) => b.score - a.score || String(a.name).localeCompare(String(b.name)));
  }
  function watchHits(query) { return searchNames(query, WATCH); }

  function ringsOf(g) {
    if (!g) return [];
    if (g.type === 'Polygon') return g.coordinates || [];
    if (g.type === 'MultiPolygon') { const out = []; (g.coordinates || []).forEach(p => (p || []).forEach(r => out.push(r))); return out; }
    return [];
  }
  function insideRing(lon, lat, ring) {
    let ins = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const xi = ring[i][0], yi = ring[i][1], xj = ring[j][0], yj = ring[j][1];
      const dy = (yj - yi) || 1e-15;
      if ((yi > lat) !== (yj > lat) && lon < (xj - xi) * (lat - yi) / dy + xi) ins = !ins;
    }
    return ins;
  }
  function insideGeom(lat, lon, g) {
    let n = 0;
    ringsOf(g).forEach(r => { if (r && r.length > 2 && insideRing(lon, lat, r)) n++; });
    return n % 2 === 1;
  }
  /* Metres from the pin to the nearest outline edge. No name is required. */
  function pinDistance(lat, lon, g) {
    const sx = 111195 * Math.cos(lat * Math.PI / 180), sy = 110946;
    let best = Infinity;
    ringsOf(g).forEach(pts => {
      for (let i = 1; i < pts.length; i++) {
        const a = pts[i - 1], b = pts[i];
        const dx = (b[0] - a[0]) * sx, dy = (b[1] - a[1]) * sy;
        const x = (lon - a[0]) * sx, y = (lat - a[1]) * sy;
        const den = dx * dx + dy * dy || 1;
        const t = Math.max(0, Math.min(1, (x * dx + y * dy) / den));
        const d = Math.hypot(x - t * dx, y - t * dy);
        if (d < best) best = d;
      }
    });
    const meters = Number.isFinite(best) ? best : null;
    return { inside: insideGeom(lat, lon, g), meters: meters, miles: meters == null ? null : meters / 1609.344 };
  }
  function formatDistance(d) {
    if (!d || d.meters == null) return '';
    if (d.meters < 30 && d.inside) return 'at this pin';
    const ft = d.meters * 3.28084;
    const how = d.inside ? 'inside, nearest edge ' : 'outside, nearest edge ';
    if (ft < 1000) return how + Math.round(ft) + ' ft';
    const mi = d.miles;
    return how + (mi < 10 ? mi.toFixed(1) : Math.round(mi)) + ' mi';
  }

  function isBanned(url) { return BANNED.some(r => r.test(String(url || ''))); }
  function isParcel(src) {
    if (!src) return false;
    return src.group === 'ky_parcels' || /pva|parcel/i.test((src.rest || '') + ' ' + (src.title || '') + ' ' + (src.kind || ''));
  }
  function blockedPlace(code) { return !!BLOCKED_PLACES[String(code || '').toUpperCase()]; }
  function hostOf(url) {
    const m = String(url || '').match(/^https?:\/\/([^/]+)/i);
    return m ? m[1].toLowerCase() : '';
  }
  function servicesHost(url) { return /^services\d*\.arcgis\.com$/i.test(hostOf(url)); }

  function publicFields(props, parcel) {
    const out = {};
    Object.keys(props || {}).forEach(k => {
      if (parcel && PRIVATE_FIELD.test(k)) return;
      if (/^(shape|globalid|objectid)/i.test(k)) return;
      out[k] = props[k];
    });
    return out;
  }
  function scrubOwner(txt, ownType) {
    if (!txt) return '';
    if (GOV_TYPES.test(String(ownType || ''))) return String(txt);
    const parts = String(txt).split(/\s*[&;]\s*/).map(x => x.trim()).filter(Boolean);
    const out = parts.map(x => PUBLIC_WORDS.test(x) ? x : 'private party (withheld)');
    return out.filter((v, i, a) => a.indexOf(v) === i).join(' & ');
  }

  /* Could this be a park? One plain report. Joint state-and-county ownership stays "maybe". */
  function rulesCheck(ctx) {
    ctx = ctx || {};
    const pota = ctx.pota || [];
    const missing = [];
    if (!ctx.owner) missing.push('owner');
    if (!ctx.agency) missing.push('managing agency');
    if (!ctx.designation) missing.push('designation');
    if (!ctx.website) missing.push('official website');
    if (!ctx.boundaryUrl && !ctx.padusUrl) missing.push('official boundary link');
    if (ctx.access == null || ctx.access === '' || ctx.access === 'unknown') missing.push('public access');
    let likely = 'maybe';
    if (pota.length) likely = 'already';
    else if (ctx.publicLand === false || ctx.ownerTier === 'private' || ctx.access === 'closed') likely = 'no';
    else if (ctx.joint || ctx.ownerTier === 'joint' || ctx.ownerTier === 'local') likely = 'maybe';
    else if (ctx.publicLand === true && (ctx.ownerTier === 'state' || ctx.ownerTier === 'federal') && (ctx.boundaryUrl || ctx.padusUrl) && ctx.access !== 'closed') likely = 'yes';
    const send = ctx.boundaryUrl || ctx.padusUrl || ctx.website || '';
    return {
      publicLand: ctx.publicLand == null ? null : !!ctx.publicLand,
      agency: ctx.agency || '',
      layer: ctx.layer || '',
      overlap: pota.map(p => ({ ref: p.ref, name: p.name })),
      likely: likely,
      missing: missing,
      sendLink: send,
      joint: !!(ctx.joint || ctx.ownerTier === 'joint')
    };
  }

  function alreadyPark(geom, pins, miles) {
    const limit = miles == null ? 0.25 : miles;
    for (const p of pins || []) {
      const d = pinDistance(+p.lat, +p.lon, geom);
      if (d.inside || (d.miles != null && d.miles <= limit)) return p;
    }
    return null;
  }
  function filterCandidates(rows, opt) {
    opt = opt || {};
    const showClosed = !!opt.closed, showPriv = !!opt.priv, showSmall = opt.small !== false, showLocal = opt.local !== false, hideNamed = !!opt.hideNamed;
    return (rows || []).filter(c => (showClosed || c.access !== 'closed') && (showPriv || !c.private) && (showSmall || c.acres >= 5) && (showLocal || !c.local) && (!hideNamed || !c.nameMatch));
  }
  function exportLeads(rows) {
    return (rows || []).map(r => ({
      name: r.name || '',
      agency: r.agency || '',
      layer: r.layer || '',
      acres: r.acres || 0,
      access: r.access || '',
      owner: scrubOwner(r.owner || '', r.ownerType || ''),
      website: r.website || '',
      boundaryLink: r.boundaryLink || '',
      pin: r.pin || null,
      note: 'Research lead, not a park and not a boundary.'
    }));
  }
  function servicesDiff(known, liveNames) {
    const k = new Set(known || []), n = new Set(liveNames || []);
    return {
      added: [...n].filter(x => !k.has(x)).sort(),
      missing: [...k].filter(x => !n.has(x)).sort()
    };
  }
  function tractLinks(doc, ref) {
    doc = doc || {};
    const parks = doc.parks || {};
    const tracts = parks[ref] || [];
    const nested = doc.nested || [];
    const same = doc.same_area || [];
    return {
      ref: ref,
      tracts: tracts.map(t => ({
        name: t.name || '',
        src: t.src || '',
        layer: t.layer || '',
        sid: t.sid || '',
        acres: t.ac,
        measured: t.ac_measured,
        pieces: t.pieces,
        owner: t.own || '',
        parentId: t.parent || '',
        access: t.access || ''
      })),
      parents: nested.filter(x => x.child === ref),
      children: nested.filter(x => x.parent === ref),
      sameArea: same.filter(x => x.park === ref || x.other === ref)
    };
  }
  function layerWords(query) {
    return tokens(canon(query).core).slice(0, 3);
  }
  /* KY fishing-lake shore outlines. Report data only. The hidden tract switch is the
     existing off-by-default gate, so these are not drawn and do not replace a key outline. */
  function shoreOverlays(doc) {
    if (!tractsOn()) return [];
    return ((doc && doc.overlays) || []).filter(f => f && f.geometry && f.properties && f.properties.role === 'shore-outline');
  }

  function selftest() {
    const fails = [];
    const ok = (c, m) => { if (!c) fails.push(m); };
    if (typeof require !== 'undefined') {
      const fs = require('fs'), path = require('path');
      const dir = path.join(__dirname, 'data', 'maprep');
      const ab = JSON.parse(fs.readFileSync(path.join(dir, 'abbreviations.json'), 'utf8'));
      loadRows(ab.rows);
      ok(places().us.length === 51 && places().ca.length === 13 && places().world.map(x => x[0]).join() === 'GB,IE,AU,NZ', 'place list is the US, Canada, and GB IE AU NZ');
      ok(tractsOn() === false, 'tract notes are off unless the hidden switch is on');
      ok(nameScore('Foo SPA', 'Foo Special Protection Area') === 96, 'Foo SPA vs Foo Special Protection Area scores 96');
      ok(nameScore('Foo SPA', 'Foo State Preservation Area') === 96, 'Louisiana SPA is kept beside Special Protection Area');
      const cat = JSON.parse(fs.readFileSync(path.join(dir, 'catalog.json'), 'utf8'));
      ok(ab.rows.length >= 60, 'abbreviation table is thin');
      cat.sources.forEach(s => {
        ok(!isBanned(s.rest) && !isBanned(s.download), 'banned url in catalog ' + s.id);
        if (s.live) {
          ok(!servicesHost(s.rest), 'live services*.arcgis.com ' + s.id);
          ok(!blockedPlace(s.place), 'live blocked state ' + s.id);
          ok(s.enabled !== false, 'live while region off ' + s.id);
          ok(!isParcel(s), 'live parcel ' + s.id);
        }
      });
      ok(cat.regions && cat.regions.US && cat.regions.US.enabled && cat.regions.CA && cat.regions.CA.enabled, 'US and Canada on');
      ok(cat.regions.AU && cat.regions.AU.enabled === false, 'Australia stays off');
      ok((cat.sources.filter(s => s.live && s.region === 'CA').length) >= 1, 'a Canada layer is live');
      ok(cat.sources.some(s => s.origin === 'camp-layers' && s.place === 'IA'), 'Iowa camp-style layer');
      ok(cat.sources.some(s => s.origin === 'camp-layers' && s.place === 'MN'), 'Minnesota camp-style layer');
      ok(cat.sources.some(s => s.origin === 'camp-layers' && s.place === 'WI'), 'Wisconsin camp-style layer');
      const shore = JSON.parse(fs.readFileSync(path.join(__dirname, 'data', 'research-sources', 'ky-fishing-shore.json'), 'utf8'));
      const blob = JSON.stringify(shore);
      ok(shore.source_label === 'county tax parcel, KDFWR owner, not a survey', 'shore source label');
      ok(shore.report_only === true && shore.applied_to_key === false && shore.shared_outline === false, 'shore overlay stays off the key');
      ok(!blob.includes('33TOOklri9xpic7U'), 'shore file does not use the banned server');
      ok(shoreOverlays(shore).length === 0, 'shore overlays stay off unless the hidden switch is on');
      const outlines = (shore.overlays || []).filter(f => f.properties && f.properties.role === 'shore-outline');
      ok(outlines.map(f => f.properties.ref).join() === 'US-13599,US-13600', 'Kingfisher and Carpenter are separate shore outlines');
      const pieces = (shore.overlays || []).filter(f => f.properties && f.properties.role === 'parcel-piece');
      ok(pieces.length === 3 && new Set(pieces.map(f => f.properties.ref)).size === 2, 'three parcel pieces, not one shared outline');
    }
    ok(nameScore('Blackford Oaks W.M.A.', 'Blackford Oaks WMA') >= 90, 'Blackford Oaks W.M.A.');
    ok(nameScore('Blackford Oaks WMA', 'Blackford Oaks Wildlife Management Area') >= 90, 'Blackford Oaks WMA words');
    const muddy = searchNames('Muddygut WMA', WATCH.concat([{ name: 'Muddygut Wildlife Management Area' }]));
    ok(muddy.some(h => /muddygut/i.test(h.name)), 'Muddygut WMA');
    ok(fuzzySame('Dale Hollow Lake WMA', 'Dale Hollow State Park'), 'Dale Hollow prefix');
    ok(!fuzzySame('Island Park', 'Jefferson Memorial Forest'), 'short names do not fuzzy-match');
    ok(/state nature preserve/.test(canon('Natural Bridge SNP').full) && canon('Natural Bridge SNP').core.indexOf('bridge') >= 0, 'SNP expands');
    const joint = rulesCheck({ publicLand: true, owner: 'Kentucky and Adair County', ownerTier: 'joint', joint: true, agency: 'KDFWR', designation: 'WMA', website: 'https://fw.ky.gov/', boundaryUrl: 'https://fw.ky.gov/map', access: 'open', layer: 'KDFWR' });
    ok(joint.likely === 'maybe' && joint.joint, 'joint ownership stays maybe');
    const priv = rulesCheck({ publicLand: false, ownerTier: 'private', owner: 'a person', agency: '', access: 'closed' });
    ok(priv.likely === 'no' && priv.publicLand === false, 'private land is no');
    const yes = rulesCheck({ publicLand: true, ownerTier: 'state', owner: 'Kentucky', agency: 'Kentucky State Parks', designation: 'State Park', website: 'https://parks.ky.gov/x', boundaryUrl: 'https://parks.ky.gov/map', access: 'open', layer: 'State parks' });
    ok(yes.likely === 'yes' && yes.sendLink.indexOf('parks.ky.gov/map') >= 0, 'state park can be yes');
    const already = rulesCheck({ publicLand: true, ownerTier: 'federal', owner: 'NPS', agency: 'NPS', designation: 'National Park', pota: [{ ref: 'US-0001', name: 'Example' }], boundaryUrl: 'https://www.nps.gov/' });
    ok(already.likely === 'already' && already.overlap.length === 1, 'overlap is already a park');
    const square = { type: 'Polygon', coordinates: [[[-0.001, -0.001], [0.001, -0.001], [0.001, 0.001], [-0.001, 0.001], [-0.001, -0.001]]] };
    const inn = pinDistance(0, 0, square);
    ok(inn.inside && inn.meters > 50, 'pin in the middle is inside');
    const out = pinDistance(0.002, 0, square);
    ok(!out.inside && out.meters > 80 && out.meters < 160, 'pin north of the square is about 111 m out, got ' + (out.meters && out.meters.toFixed(1)));
    const hit = alreadyPark(square, [{ ref: 'US-1', name: 'In', lat: 0, lon: 0 }]);
    ok(hit && hit.ref === 'US-1', 'pin inside counts as already a park');
    const leads = exportLeads([{ name: 'X', agency: 'A', geometry: { type: 'Polygon' }, pin: [1, 2], owner: 'Smith Family', ownerType: '' }]);
    ok(leads.length === 1 && !leads[0].geometry && leads[0].owner === 'private party (withheld)' && leads[0].note.indexOf('not a boundary') >= 0, 'export is a lead list');
    const diff = servicesDiff(['Ky_A', 'Ky_B'], ['Ky_B', 'Ky_C']);
    ok(diff.added.join() === 'Ky_C' && diff.missing.join() === 'Ky_A', 'KY service diff');
    const fields = publicFields({ OWNER: 'secret', NAME: 'also secret', ACRES: 10, UNIT: 'Park' }, true);
    ok(fields.OWNER == null && fields.NAME == null && fields.ACRES === 10 && fields.UNIT === 'Park', 'parcel privacy');
    ok(isBanned('https://services.arcgis.com/33TOOklri9xpic7U/arcgis/rest/services/Parcels/FeatureServer/0'), 'grant county filter');
    const doc = { parks: { 'US-1': [{ name: 'Piece', src: 'padus', pieces: 2, ac: 10, parent: 'P', own: 'State' }] }, nested: [{ child: 'US-1', parent: 'US-2', share: 1, how: 'geometry' }], same_area: [{ park: 'US-1', other: 'US-3', via: 'parent id' }] };
    const links = tractLinks(doc, 'US-1');
    ok(links.tracts.length === 1 && links.tracts[0].pieces === 2 && links.parents[0].parent === 'US-2' && links.sameArea.length === 1, 'tract parent and child');
    const kept = filterCandidates([
      { name: 'Open', access: 'open', acres: 20, private: false, local: false },
      { name: 'Shut', access: 'closed', acres: 20, private: false, local: false },
      { name: 'Tiny', access: 'open', acres: 1, private: false, local: false }
    ], { closed: false, small: false });
    ok(kept.length === 1 && kept[0].name === 'Open', 'find-new filters');
    if (typeof require !== 'undefined') {
      const fs2 = require('fs'), path2 = require('path');
      const ag = JSON.parse(fs2.readFileSync(path2.join(__dirname, 'data', 'maprep', 'agencies.json'), 'utf8'));
      loadAgencies(ag);
      const need = 'AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY AB BC MB NB NL NT NS NU ON PE QC SK YT'.split(' ');
      need.forEach(code => ok(ag.places[code] && ag.places[code].agencies && ag.places[code].agencies.length > 0, 'agency row for ' + code));
      const ky = agencyMatches('KY', 'Blackford Oaks Wildlife Management Area');
      ok(ky.some(a => a.matched && a.role === 'wildlife' && a.finder && a.finder.url), 'KY WMA uses the wildlife directory');
      ok(!JSON.stringify(ag).includes('33TOOklri9xpic7U'), 'directory has no banned server');
    }
    if (fails.length) {
      console.log(fails.join('\n'));
      console.log('SOME FAILED');
      return 1;
    }
    console.log('PASS maprep toolbox selftest');
    return 0;
  }

  return {
    CORE: CORE, WATCH: WATCH, loadRows: loadRows, expandName: expandName, canon: canon, normName: normName,
    fuzzySame: fuzzySame, nameScore: nameScore, searchNames: searchNames, watchHits: watchHits,
    pinDistance: pinDistance, formatDistance: formatDistance, isBanned: isBanned, isParcel: isParcel,
    blockedPlace: blockedPlace, servicesHost: servicesHost, publicFields: publicFields, scrubOwner: scrubOwner,
    rulesCheck: rulesCheck, alreadyPark: alreadyPark, filterCandidates: filterCandidates, exportLeads: exportLeads,
    servicesDiff: servicesDiff, tractLinks: tractLinks, layerWords: layerWords,
    places: places, placeRows: placeRows, placeByCode: placeByCode, tractsOn: tractsOn, shoreOverlays: shoreOverlays,
    loadAgencies: loadAgencies, agenciesReady: agenciesReady, agencyMatches: agencyMatches, selftest: selftest
  };
});

if (typeof require !== 'undefined' && require.main === module) {
  process.exit(module.exports.selftest());
}
