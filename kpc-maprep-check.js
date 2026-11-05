/* Could this be a park? — local check for the Mapping Rep Tool Box.
   Reads the club's published Kentucky layers, answer-key names and overlap file already in this
   repo and answers with point-in-polygon in the browser. No map token, no keyed API, no spoofed
   User-Agent. Newfoundland, Tokyo, Japan A10, South Africa SAPAD and Colorado CNHP outlines are
   never requested and never drawn. */
(function () {
  'use strict';
  const B = () => window.KPCB;
  const $ = id => document.getElementById(id);
  const esc = s => (B() && B().esc) ? B().esc(s) : String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const INFO = 'ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go.';
  const OVERLAP_NOTE = "⚠️ Parks' boundaries may overlap here, but we can't confirm it. Check both official boundary maps and make your own call before you count it.";
  /* ids only — never draw these outlines (data/CREDITS-NC.md) */
  const BLOCKED = /newfoundland|tokyo|\bA10\b|sapad|cnhp|colorado natural heritage/i;

  let pack = null, map = null, drawLayer = null, pinMarker = null, overlayLayers = {}, gen = 0;
  const HOME = {
    'Kentucky State Parks': 'https://parks.ky.gov/',
    'Kentucky Fish & Wildlife': 'https://fw.ky.gov/',
    'Kentucky Office of Nature Preserves': 'https://eec.ky.gov/Nature-Preserves/Pages/default.aspx',
    'National Park Service': 'https://www.nps.gov/',
    'U.S. Fish & Wildlife Service': 'https://www.fws.gov/',
    'U.S. Forest Service': 'https://www.fs.usda.gov/',
    'U.S. Army Corps of Engineers': 'https://www.usace.army.mil/'
  };

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
  function wordsOf(q) {
    return String(q || '').toLowerCase().replace(/&/g, ' and ')
      .replace(/\b(state|national|park|parks|the|of|and|area|resort|wildlife|management|nature|preserve|natural|recreation|recreational|forest|refuge|site|historic|historical)\b/g, ' ')
      .replace(/\b(sp|srp|wma|snp|sna|nwr|nf|nfh|shs|nps)\b/g, ' ')
      .replace(/[^a-z0-9' ]/g, ' ').trim().split(/\s+/).filter(w => w.length > 2);
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
    for (let k = 1; k < 8; k++) {
      const y = bb[1] + (bb[3] - bb[1]) * k / 8;
      if (feats.some(f => b.inside(y, lo0, f.geometry))) return [y, lo0];
    }
    return [la0, lo0];
  }

  async function ready() {
    if (pack) return pack;
    const b = B();
    const [base, counties, ov, corps] = await Promise.all([
      b.ky(),
      b.jget('kpc-ky-counties.json').catch(() => []),
      b.jget('ky-overlaps.geojson').catch(() => ({ features: [] })),
      b.jget('ky-usace.geojson').catch(() => ({ features: [] }))
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
    pack = { feats: feats.filter(f => f.geometry && !blocked(f)), counties: counties || [], overlaps };
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

  function judge(row, parksHere) {
    const f = row.f, t = tierOf(f), acc = accessOf(f), url = urlOf(f), gov = govUrl(url);
    const missing = [];
    if (!url) missing.push('No agency page is stored on this layer.');
    else if (!gov) missing.push('The page on this layer is not a government address, so it cannot be the link you send.');
    if (acc === 'unknown') missing.push('Public access is not stated on this layer.');
    if (!row.acres) missing.push('Acreage is not on this layer.');
    const military = /military reservation|army depot|training area|national guard|air force base|naval base|\bfort\b/i.test(f._nm || '');
    const cred = credits(f);
    let v = 'MAYBE', why = '';
    if (parksHere.length) {
      v = 'ALREADY';
      why = 'POTA already numbers this land (' + parksHere.map(p => p.ref + ' ' + p.name).join('; ') + '). If POTA numbers it, it is a park. Do not add it again.';
    } else if (t === 'osm') {
      v = 'NO';
      why = 'The only outline is an OpenStreetMap sketch. That is background, not evidence. An official government source is still missing.';
      missing.push('An official government map or page.');
    } else if (t === 'line') {
      v = 'NO';
      why = 'This is the forest boundary line. Not all of the land inside that line is public, so the line by itself is not a park.';
    } else if (t === 'other') {
      v = 'NO';
      why = 'The manager looks like a city, county, private owner or non-profit. Those tiers are not added.';
    } else if (acc === 'closed') {
      v = 'NO';
      why = 'The layer says this place is closed to the public. A park has to be open to the public.';
    } else if (t === 'corps') {
      v = 'MAYBE';
      why = 'This is Army Corps of Engineers land. POTA has generally not added Corps sites. Only a few are exceptions, and that call is not made here.';
    } else if (military) {
      v = 'MAYBE';
      why = 'The name looks like military land. A base is not an ordinary park. Someone still has to check whether any public piece of it could qualify.';
    } else if ((f._L || {}).k === 'bwild') {
      v = 'MAYBE';
      why = 'A wild-river corridor is a designation. A designation never qualifies a place by itself. The land still has to pass every rule on its own.';
    } else if (acc === 'restricted') {
      v = 'MAYBE';
      why = 'Access is restricted (permit, appointment or only part of the land). It qualifies only if the agency’s own page says the public may visit without a special permit.';
    } else if (!gov) {
      v = 'MAYBE';
      why = 'It looks like ' + (t === 'fed' ? 'federal' : 'state') + ' land with a boundary, but there is no government page on this layer to send.';
    } else if ((t === 'fed' || t === 'state') && row.acres >= 1) {
      v = 'YES';
      why = 'Published ' + (t === 'fed' ? 'federal' : 'state') + ' land, with a boundary and a government page' + (acc === 'open' ? ', and the layer says it is open to the public.' : '. Confirm that the public can get in without crossing private land.');
    } else if (t === 'fed' || t === 'state') {
      v = 'MAYBE';
      why = 'It looks like public land with a government page, but the outline has no real acreage, so it may be only a dot.';
    } else {
      v = 'MAYBE';
      why = 'The layer does not settle ownership. Read the agency page before you decide.';
    }
    return { v, why, missing, send: (gov ? url : '') || HOME[(f._L || {}).agency] || '', credits: cred, tier: t, access: acc, url };
  }

  function relLine(row) {
    if (row.inn) return 'Your pin is inside this boundary. The nearest edge is about ' + feetOrMi(row.edgeKm) + ' away.';
    return 'Your pin is about ' + feetOrMi(row.edgeKm) + ' outside this boundary.';
  }

  let locP = null;
  async function loadLocations() {
    if (locP) return locP;
    locP = B().jget('locations.json').then(rows => (rows || []).filter(r => r && r[0] === 'POTA')).catch(() => []);
    return locP;
  }

  async function find(q) {
    q = String(q || '').trim();
    if (q.length < 2) return [];
    await ready();
    const b = B(), ref = normRef(q), ws = wordsOf(q);
    const parks = (b.kyData() && b.kyData().parks) || [];
    const hits = [];
    const add = (score, row) => { if (score >= 70) hits.push(Object.assign({ score }, row)); };
    parks.forEach(p => {
      if (BLOCKED.test(p.n || '')) return;
      if (ref && p.c === ref) add(100, { ref: p.c, name: p.n, la: p.la, lo: p.lo, web: p.web, kind: 'pota' });
      else if (b.norm(p.n) === b.norm(q)) add(96, { ref: p.c, name: p.n, la: p.la, lo: p.lo, web: p.web, kind: 'pota' });
      else if (b.sameName(p.n, q) && b.sameKind(p.n, q)) add(88, { ref: p.c, name: p.n, la: p.la, lo: p.lo, web: p.web, kind: 'pota' });
      else if (ws.length && ws.every(w => p.n.toLowerCase().indexOf(w) >= 0)) add(76, { ref: p.c, name: p.n, la: p.la, lo: p.lo, web: p.web, kind: 'pota' });
    });
    pack.feats.forEach(f => {
      if (blocked(f)) return;
      const n = f._nm || '';
      let score = 0;
      if (ref && ((f.properties || {}).ref === ref)) score = 100;
      else if (b.norm(n) === b.norm(q)) score = 94;
      else if (b.sameName(n, q)) score = 84;
      else if (ws.length && ws.every(w => n.toLowerCase().indexOf(w) >= 0)) score = 74;
      if (!score) return;
      if (hits.some(h => h.kind === 'pota' && (b.sameName(h.name, n) || (h.ref && (f.properties || {}).ref === h.ref)))) return;
      add(score, { ref: (f.properties || {}).ref || '', name: n, la: null, lo: null, web: urlOf(f), kind: 'land', f });
    });
    hits.sort((a, c) => c.score - a.score || String(a.ref).localeCompare(String(c.ref)));
    const seen = new Set(), out = [];
    hits.forEach(h => { const k = (h.ref || '') + '|' + b.norm(h.name); if (seen.has(k)) return; seen.add(k); out.push(h); });
    if (out.length) return out.slice(0, 12);
    if (ref || ws.length) {
      const rows = await loadLocations();
      rows.forEach(r => {
        const name = r[2] || '';
        if (BLOCKED.test(name)) return;
        if (ref && r[1] === ref) add(100, { ref: r[1], name, la: +r[3], lo: +r[4], web: r[5] || '', kind: 'list' });
        else if (ws.length >= 2 && ws.every(w => name.toLowerCase().indexOf(w) >= 0)) add(72, { ref: r[1], name, la: +r[3], lo: +r[4], web: r[5] || '', kind: 'list' });
      });
    }
    hits.sort((a, c) => c.score - a.score);
    return hits.filter(h => h.kind === 'list').slice(0, 12);
  }

  function primaryParks(rows) {
    const m = new Map();
    rows.forEach(r => (r.own || []).concat(r.pins || []).forEach(p => { if (p.ref) m.set(p.ref, p); }));
    return [...m.values()];
  }

  function renderSpot(o) {
    const box = $('mrSpot'); if (!box) return;
    const rows = o.inside.concat(o.near);
    const official = o.inside.filter(r => tierOf(r.f) !== 'line');
    const use = official.length ? official : o.inside.length ? o.inside : o.near.slice(0, 1);
    const main = use[0];
    const parks = primaryParks(use.map(r => { const fp = featParks(r.f); r.own = fp.own; r.pins = fp.pins; return r; }));
    const nearParks = o.parkPins || [];
    const ov = o.overlaps || [];
    const place = main ? (main.f._nm || 'Public land') : 'No published public land at this pin';
    const judged = main ? judge(main, main.own && main.own.length ? main.own : parks.filter(p => (main.own || []).some(x => x.ref === p.ref) || (main.pins || []).some(x => x.ref === p.ref))) : null;
    const onLand = !!(main && main.inn && tierOf(main.f) !== 'line' && tierOf(main.f) !== 'osm');
    const vClass = !main ? 'no' : judged.v === 'YES' ? 'yes' : judged.v === 'NO' ? 'no' : judged.v === 'ALREADY' ? 'yes' : 'maybe';
    const vWord = !main ? 'NOT PUBLIC LAND IN THE PUBLISHED LAYERS' : judged.v === 'YES' ? 'LIKELY YES — COULD BE ADDED' : judged.v === 'NO' ? 'LIKELY NO' : judged.v === 'ALREADY' ? 'ALREADY A POTA PARK' : 'MAYBE — A PERSON STILL HAS TO CHECK';

    const kv = (k, v) => `<div class="mr-kv"><dt>${esc(k)}</dt><dd>${v}</dd></div>`;
    let officialHtml = '';
    if (!main) {
      officialHtml = kv('On public land?', '<b>No.</b> This pin is not inside any published Kentucky layer on this site (state parks, wildlife areas, nature preserves, national parks, refuges, Forest Service land or Corps land).')
        + kv('Owning or managing agency', 'None in these layers.')
        + kv('Official layer', 'None.')
        + kv('Acreage', 'None.')
        + kv('Official source', 'None to send.')
        + kv('PAD-US id', 'None at this pin.');
    } else {
      const bits = use.slice(0, 4).map(r => {
        const f = r.f, p = f.properties || {}, L = f._L || {};
        const id = p.PADUS_ID || p.OBJECTID || '';
        const idLink = id ? `<a href="https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query?objectIds=${encodeURIComponent(id)}&outFields=*&returnGeometry=false&f=html" target="_blank" rel="noopener">${esc(id)}</a>` : 'This published layer does not carry a PAD-US id.';
        const src = urlOf(f);
        const cred = credits(f);
        return `<article class="mr-unit"><h4>${esc(f._nm || L.name)}</h4>`
          + kv('On public land?', onLand && r === main ? '<b>Yes.</b> ' + esc(relLine(r)) : '<b>' + (r.inn ? 'Inside this outline.' : 'Not inside.') + '</b> ' + esc(relLine(r)))
          + kv('Owning or managing agency', esc([p.OWNER || p.owner, p.MANAGER, L.agency].filter((x, i, a) => x && a.indexOf(x) === i).join(' · ') || 'Not stated on this layer'))
          + kv('Official layer and designation', esc([L.name, p.TYPE || p.Loc_Ds || ''].filter(Boolean).join(' · ')))
          + kv('Acreage', r.acres ? 'about ' + Math.round(r.acres).toLocaleString() + ' acres' : 'not stated')
          + kv('Official source', src ? `<a href="${esc(src)}" target="_blank" rel="noopener">${esc(src)}</a>` : 'No page stored on this layer.')
          + kv('PAD-US id', idLink)
          + (cred.length ? kv('Credit', esc(cred.join(' · '))) : '')
          + `</article>`;
      }).join('');
      officialHtml = bits;
    }

    const potaList = parks.length ? parks : (main && main.own) || [];
    const potaHtml = kv('Parks at this pin', potaList.length
      ? potaList.map(p => `<a href="https://pota.app/#/park/${encodeURIComponent(p.ref)}" target="_blank" rel="noopener">${esc(p.ref)}</a> ${esc(p.name)}`).join('<br>')
      : 'No POTA park is tied to this outline.')
      + (main ? kv('Distance to the official boundary', esc(relLine(main))) : '')
      + kv('Likely to qualify?', judged ? esc(judged.why) : 'No. Nothing here shows public land that could be added.')
      + kv('What is missing', (judged && judged.missing.length) ? judged.missing.map(esc).join(' ') : (main ? 'Nothing obvious on the published layer. Still confirm the agency page and a way in for the public.' : 'An official layer, the agency, a designation, acreage and a source link.'))
      + kv('Link to send POTA', (judged && judged.send) ? `<a class="mr-send" href="${esc(judged.send)}" target="_blank" rel="noopener">${esc(judged.send)}</a>` : 'No official link is stored. Find the agency’s own page before you send anything.');

    const nearHtml = nearParks.length ? `<p class="mr-help"><b>Nearest POTA pins</b> (the pin, not the boundary): ${nearParks.map(x => `${esc(x.p.c)} ${esc(x.p.n)} · ${esc(feetOrMi(x.km))}`).join('; ')}.</p>` : '';
    const ovHtml = ov.length ? `<div class="mr-ov"><p><b>Overlap file.</b> Our file lists these parks together at this pin: ${ov.map(f => (f.properties.pota || []).map(p => esc(p[0] + ' ' + p[1])).join(', ') || esc((f.properties.areas || []).join(', '))).join('; ')}.</p><p>${esc(OVERLAP_NOTE)}</p></div>` : '';
    const note = (main && main.f._L && main.f._L.note) ? `<p>${esc(main.f._L.note)}</p>` : '';
    const county = o.county ? `<p>County: ${esc(o.county)}. Grid ${esc(grid(o.la, o.lo))}. Pin ${o.la.toFixed(5)}, ${o.lo.toFixed(5)}.</p>` : `<p>Grid ${esc(grid(o.la, o.lo))}. Pin ${o.la.toFixed(5)}, ${o.lo.toFixed(5)}.</p>`;

    box.innerHTML = `<section class="mr-res" data-mr-result="spot">
<div class="mr-head"><div class="mr-k">COULD THIS BE A PARK?</div><h2>${esc(place)}</h2><p>${esc(o.la.toFixed(5))}, ${esc(o.lo.toFixed(5))}${o.county ? ' · ' + esc(o.county + ' County') : ''}</p></div>
<div class="mr-sec mr-official"><h3>1 · Official information</h3>${officialHtml}</div>
<div class="mr-sec"><h3>2 · POTA status</h3><div class="mr-v ${vClass}" data-mr-verdict="${esc(vWord)}"><b>${esc(vWord)}</b></div><div class="mr-dl">${potaHtml}</div>${nearHtml}</div>
<div class="mr-sec"><h3>3 · KPC notes</h3>${note}${county}${ovHtml}<p class="mr-help">${INFO} <a href="kpc-about-info.html">About our information</a></p><p class="mr-help">Street map tiles are © OpenStreetMap contributors, ODbL. Kentucky outlines on this page are the club’s published copies of agency layers.</p></div>
</section>`;
    box.hidden = false;
    drawOnMap(o.la, o.lo, use.map(r => r.f), ov);
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
    if (pinMarker) pinMarker.remove();
    pinMarker = L.marker([la, lo], { draggable: true, title: 'Dropped pin' }).addTo(map);
    pinMarker.on('dragend', () => { const p = pinMarker.getLatLng(); showPoint(p.lat, p.lng); });
    const b = L.latLngBounds([[la, lo]]);
    try { if (fc.features.length) b.extend(L.geoJSON(fc).getBounds()); } catch (e) {}
    map.fitBounds(b.pad(0.3), { maxZoom: 14 });
    setTimeout(() => map.invalidateSize(), 60);
  }

  async function showPoint(la, lo) {
    const my = ++gen;
    const box = $('mrSpot');
    if (box) box.innerHTML = '<p class="mr-msg">Checking the published Kentucky layers at this pin…</p>';
    mount();
    await ready();
    if (my !== gen) return { hit: false };
    const s = scan(la, lo);
    const hit = s.inside.length > 0 || s.near.length > 0;
    const inKy = B().inKY(la, lo);
    renderSpot({
      la, lo, inKy, hit,
      inside: s.inside, near: s.near,
      overlaps: overlapsAt(la, lo),
      county: countyOf(la, lo),
      parkPins: parksNear(la, lo, hit ? 30 : 80)
    });
    const q = $('mrCheckQ'); if (q && document.activeElement !== q) q.value = la.toFixed(5) + ', ' + lo.toFixed(5);
    return { hit, inKy };
  }

  async function showHit(h) {
    await ready();
    mount();
    const b = B();
    let feats = [];
    if (h.ref) { try { feats = (await b.kyFor(h.ref)) || []; } catch (e) { feats = []; } }
    feats = feats.filter(f => !blocked(f));
    if (!feats.length && h.f) feats = [h.f];
    if (!feats.length) {
      pack.feats.forEach(f => { if (!blocked(f) && b.sameName(f._nm, h.name)) feats.push(f); });
    }
    const la = isFinite(h.la) ? h.la : (feats[0] ? pointInside(feats)[0] : 37.5);
    const lo = isFinite(h.lo) ? h.lo : (feats[0] ? pointInside(feats)[1] : -85);
    if (!feats.length) {
      const box = $('mrSpot');
      const outside = h.kind === 'list';
      if (box) box.innerHTML = `<section class="mr-res" data-mr-result="name"><div class="mr-head"><div class="mr-k">COULD THIS BE A PARK?</div><h2>${esc(h.name)}</h2><p>${esc(h.ref || '')}</p></div>
<div class="mr-sec mr-official"><h3>1 · Official information</h3><p>No published Kentucky outline is stored for this park. ${outside ? 'Outlines for Newfoundland and Labrador, Tokyo, Japan A10, South Africa SAPAD and Colorado CNHP are not shown.' : ''}</p>
${h.web ? `<p>Listed page: <a href="${esc(h.web)}" target="_blank" rel="noopener">${esc(h.web)}</a></p>` : ''}</div>
<div class="mr-sec"><h3>2 · POTA status</h3><p>${h.ref ? `<a href="https://pota.app/#/park/${encodeURIComponent(h.ref)}" target="_blank" rel="noopener">${esc(h.ref)}</a> ${esc(h.name)}.` : esc(h.name)} Pin ${isFinite(h.la) ? h.la.toFixed(5) + ', ' + h.lo.toFixed(5) : 'not stored'}.</p></div>
<div class="mr-sec"><h3>3 · KPC notes</h3><p class="mr-help">${INFO} <a href="kpc-about-info.html">About our information</a></p></div></section>`;
      if (isFinite(h.la)) drawOnMap(h.la, h.lo, [], []);
      return { hit: true, inKy: false };
    }
    const s = scan(la, lo);
    const have = s.inside.concat(s.near).filter(r => feats.some(f => f === r.f) || b.sameName(r.f._nm, h.name));
    const rows = have.length ? have : feats.map(f => {
      const inn = b.inside(la, lo, f.geometry);
      const e = b.edge(la, lo, f.geometry);
      return { f, inn, edgeKm: e.km, acres: acresOfFeat(f) };
    });
    renderSpot({
      la, lo, hit: true, inKy: b.inKY(la, lo),
      inside: rows.filter(r => r.inn),
      near: rows.filter(r => !r.inn),
      overlaps: overlapsAt(la, lo),
      county: countyOf(la, lo),
      parkPins: parksNear(la, lo, 40)
    });
    return { hit: true, inKy: b.inKY(la, lo) };
  }

  async function showQuery(q) {
    const my = ++gen;
    const box = $('mrSpot');
    if (box) box.innerHTML = '<p class="mr-msg">Looking up that name in the published layers…</p>';
    const hits = await find(q);
    if (my !== gen) return hits;
    if (!hits.length) {
      if (box) box.innerHTML = `<p class="mr-msg" data-mr-result="none"><b>No park with that name</b> is in the Kentucky file or the park list on this site. Try the GPS pin, or check the spelling. Outlines for Newfoundland and Labrador, Tokyo, Japan A10, South Africa SAPAD and Colorado CNHP are not shown.</p>`;
      return hits;
    }
    if (hits.length === 1 || hits[0].score >= 90 && (!hits[1] || hits[1].score < 80)) {
      await showHit(hits[0]);
      return hits;
    }
    if (box) {
      box.innerHTML = `<div class="mr-res" data-mr-result="list"><div class="mr-head"><div class="mr-k">NAME SEARCH</div><h2>${hits.length} matches</h2><p>Pick one to see official information, then POTA status.</p></div>
<div class="mr-sec">${hits.map((h, i) => `<button type="button" class="mr-pick" data-hit="${i}"><b>${esc(h.name)}</b><span>${esc(h.ref || h.kind)}</span></button>`).join('')}</div></div>`;
      box.querySelectorAll('[data-hit]').forEach(btn => btn.onclick = () => showHit(hits[+btn.dataset.hit]));
    }
    return hits;
  }

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
      const fp = g.feats.map(featParks);
      const own = [];
      fp.forEach(x => (x.own || []).forEach(p => { if (!own.some(o => o.ref === p.ref)) own.push(p); }));
      const fake = { f, inn: true, edgeKm: 0, acres: g.acres, own, pins: [] };
      const j = judge(fake, own);
      const pt = pointInside(g.feats) || [37.5, -85];
      rows.push({ name: g.name, layer: g.layer, agency: g.agency, acres: g.acres, v: j.v, why: j.why, refs: own, la: pt[0], lo: pt[1], send: j.send, id: (f.properties || {}).PADUS_ID || '' });
    });
    const rank = { YES: 0, MAYBE: 1, NO: 2, ALREADY: 3 };
    rows.sort((a, c) => (rank[a.v] - rank[c.v]) || c.acres - a.acres || a.name.localeCompare(c.name));
    return rows;
  }

  async function showAll() {
    const box = $('mrSpot');
    if (box) box.innerHTML = '<p class="mr-msg">Reading every published Kentucky layer…</p>';
    mount();
    await ready();
    const rows = classifyAll();
    const counts = { YES: 0, MAYBE: 0, NO: 0, ALREADY: 0 };
    rows.forEach(r => { counts[r.v] = (counts[r.v] || 0) + 1; });
    const lab = { YES: 'Yes', MAYBE: 'Maybe', NO: 'No', ALREADY: 'Already a park' };
    if (!box) return rows;
    box.innerHTML = `<section class="mr-res" data-mr-result="all"><div class="mr-head"><div class="mr-k">CHECK ALL · KENTUCKY</div><h2>Published layers</h2><p>${rows.length} named places. Yes, no or maybe is about adding a new park. Already means POTA has a number for that land.</p></div>
<div class="mr-sec"><div class="mr-filters" id="mrFilters">${['YES', 'MAYBE', 'NO', 'ALREADY'].map(k => `<button type="button" class="mr-ag${k === 'YES' ? ' on' : ''}" data-f="${k}">${lab[k]} · ${counts[k] || 0}</button>`).join('')}</div>
<p class="mr-help">Other states are not listed here. This page draws Kentucky’s published layers. Newfoundland and Labrador, Tokyo, Japan A10, South Africa SAPAD and Colorado CNHP outlines are not shown.</p>
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
    map = L.map(el, { scrollWheelZoom: true }).setView([37.5, -85.3], 7);
    if (window.KPCLayers) KPCLayers(map, 'Street');
    else L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap contributors, ODbL' }).addTo(map);
    map.on('click', e => {
      const t = e.originalEvent && e.originalEvent.target;
      if (t && t.closest && t.closest('.leaflet-control, .leaflet-popup')) return;
      showPoint(e.latlng.lat, e.latlng.lng);
    });
    setTimeout(() => { if (map) map.invalidateSize(); }, 80);
    buildToggles();
  }

  async function buildToggles() {
    const host = $('mrLayerToggles'); if (!host || host.childElementCount) return;
    await ready();
    const b = B();
    const layers = {};
    pack.feats.forEach(f => {
      const k = (f._L && f._L.k) || 'other';
      (layers[k] = layers[k] || { name: (f._L && f._L.name) || k, agency: (f._L && f._L.agency) || '', feats: [] }).feats.push(f);
    });
    host.innerHTML = Object.keys(layers).map(k => {
      const Lr = layers[k];
      const nc = b.ncLabel ? b.ncLabel('', Lr.agency + ' ' + Lr.name) : '';
      return `<label class="mr-ag"><input type="checkbox" data-ly="${esc(k)}"> ${esc(Lr.name)} <small>${esc(Lr.agency)}${nc ? ' · ' + esc(nc) : ''} · ${Lr.feats.length}</small></label>`;
    }).join('') + '<p class="mr-help">These are Kentucky’s published layers. A WA DBCA outline, if one is ever shown, is labelled CC BY-NC 4.0, DBCA. OpenStreetMap outlines are credited ODbL. CONANP outlines are credited “Fuente: CONANP”. Newfoundland and Labrador, Tokyo, Japan A10, South Africa SAPAD and Colorado CNHP outlines are not on this map.</p>';
    host.querySelectorAll('[data-ly]').forEach(inp => inp.onchange = () => {
      const k = inp.dataset.ly;
      if (overlayLayers[k]) { map.removeLayer(overlayLayers[k]); delete overlayLayers[k]; }
      if (!inp.checked || !map) return;
      const feats = layers[k].feats.filter(f => !blocked(f));
      overlayLayers[k] = L.geoJSON({ type: 'FeatureCollection', features: feats.map(f => ({ type: 'Feature', properties: { name: f._nm }, geometry: f.geometry })) }, {
        style: { color: '#1d5a3a', weight: 1, fillOpacity: 0.08 }
      }).addTo(map);
      overlayLayers[k].eachLayer(layer => { if (layer.feature) layer.bindTooltip(layer.feature.properties.name || '', { sticky: true }); });
    });
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
  }

  wire();
  window.KPCMapCheck = { mount, find, showQuery, showPoint, showAll, ready, map: () => map };
})();
