/* KPC Activation Kit (kpc-kit.html). Public since Oct 15 2026.
   Any POTA park, WWFF area or SOTA summit, any state -> one screen: weather, boundary map, the other references
   at the same spot, where to stay and a Spot Me button. Kentucky parks also get member reports and tips,
   parking/trailhead points, 2-fers and KPC's campground list. SAVE FOR NO SIGNAL keeps it on the phone.
   Uses kpc-bounds.js (window.KPCB). ?ref=US-1234 / KFF-1234 / W4K/EC-001 opens one. */
(function () {
  'use strict';
  const B = window.KPCB, $ = id => document.getElementById(id), esc = B.esc;
  const APP = 'kpc-finder-v1', TILES = 'kpc-tiles-v1'; /* same caches as Park Commander (kpc-finder-sw.js); never rename */
  const SAVEKEY = 'kpcKitSaved';
  const store = { get: k => { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } }, set: (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  let D = null, CONDS = null, NOTES = null, CAMP = null, map = null, cur = null, geo = null;
  const j = u => fetch(u).then(r => r.ok ? r.json() : null).catch(() => null);
  const name = c => { if (!D) return ''; const x = D.parks.find(p => p.c === c) || D.kff.find(p => p.c === c) || D.summits.find(p => p.c === c); return x ? x.n : ''; };
  const progOf = r => /^[A-Z0-9]{1,4}\/[A-Z0-9]{2}-\d{3}$/.test(r) ? 'SOTA' : /^[A-Z0-9]{1,4}FF-\d{4}$/.test(r) ? 'WWFF' : 'POTA';
  const spotKey = { POTA: 'pota', WWFF: 'wwff', SOTA: 'sota' };

  if ('serviceWorker' in navigator && window.isSecureContext) navigator.serviceWorker.register('kpc-finder-sw.js').catch(() => {});

  async function load() {
    [D, CONDS, NOTES, CAMP] = await Promise.all([j('kpc-ky-data.json'), j('kpc-conditions.json'), j('kpc-park-notes.json'), j('kpc-campgrounds.json')]);
    if (!D) D = { parks: [], kff: [], summits: [] };
    const opt = (c, n, t) => `<option value="${esc(c)}">${esc(n)} (${t})</option>`;
    $('kitList').innerHTML = D.parks.map(p => opt(p.c, p.n, 'POTA')).concat(D.kff.map(p => opt(p.c, p.n, 'WWFF')), D.summits.map(p => opt(p.c, p.n, 'SOTA'))).join('');
    const saved = store.get(SAVEKEY) || {}, keys = Object.keys(saved);
    $('kitSaved').innerHTML = keys.length ? 'Saved on this phone: ' + keys.map(r => `<a href="?ref=${encodeURIComponent(r)}" data-ref="${esc(r)}">${esc(r)} ${esc(saved[r].name || name(r))}</a>`).join(' · ') : '';
    const r0 = new URLSearchParams(location.search).get('ref');
    if (r0) open(r0.toUpperCase());
  }
  const btn = (c, n, extra) => `<button type="button" data-ref="${esc(c)}"><b>${esc(n)}</b><span>${extra ? esc(extra) + ' · ' : ''}${esc(c)} ›</span></button>`;
  async function pick(q) {
    q = String(q || '').trim(); if (!q) return;
    const up = q.toUpperCase().replace(/\s+/g, ''), m = up.match(/^(\d{3,5})$/);
    if (m) return open('US-' + m[1].padStart(4, '0'));
    if (/^[A-Z0-9]{1,4}(\/[A-Z0-9]{2})?-\d{1,5}$/.test(up)) return open(up);
    const l = q.toLowerCase(), local = D.parks.concat(D.kff, D.summits).filter(x => x.n.toLowerCase().includes(l));
    $('kitPick').innerHTML = '<p class="kit-msg">Searching…</p>';
    let far = [];
    try { far = ((await B.jget('https://api.pota.app/lookup?search=' + encodeURIComponent(q) + '&size=60')) || []).filter(x => x.type === 'park' && !local.some(y => y.c === x.value)).slice(0, 15); } catch (e) {}
    if (local.length + far.length === 1) return open((local[0] && local[0].c) || far[0].value);
    $('kitPick').innerHTML = local.length || far.length ? local.slice(0, 12).map(x => btn(x.c, x.n, 'KY ' + progOf(x.c))).join('') + far.map(x => btn(x.value, x.display.replace(/^\S+\s+/, ''), 'POTA')).join('') : '<p class="kit-msg">Nothing matches that. Try part of the name, or a reference like US-1234, KFF-1234 or W4K/EC-001.</p>';
  }
  function near() {
    if (!navigator.geolocation) return;
    $('kitPick').innerHTML = '<p class="kit-msg">Getting your location…</p>';
    navigator.geolocation.getCurrentPosition(pos => listNear(pos.coords.latitude, pos.coords.longitude),
      () => { $('kitPick').innerHTML = '<p class="kit-msg">Could not get your location. Type the park or summit instead.</p>'; }, { enableHighAccuracy: false, timeout: 15000, maximumAge: 60000 });
  }
  /* the 10 closest parks / summits to a spot (your GPS, or a town picked in the box) */
  async function listNear(la, lo, label) {
      if (label) $('kitPick').innerHTML = '<p class="kit-msg">Finding parks and summits near ' + B.esc(label) + '…</p>';
      const out = [];
      D.parks.forEach(p => out.push({ c: p.c, n: p.n, d: B.km(la, lo, p.la, p.lo) }));
      D.summits.forEach(p => out.push({ c: p.c, n: p.n, d: B.km(la, lo, p.la, p.lo) }));
      if (!B.inKY(la, lo)) {
        const [P, S] = await Promise.all([B.potaNear(la, lo, 0.4).catch(() => []), B.sotaNear(la, lo, 40).catch(() => [])]);
        P.forEach(p => out.push({ c: p.ref, n: p.name, d: B.km(la, lo, p.la, p.lo) })); S.forEach(s => out.push({ c: s.ref, n: s.name, d: s.d }));
      }
      if (!B.inKY(la, lo)) { const W = await B.wwffNear(la, lo, 40).catch(() => []); W.forEach(w => out.push({ c: w.ref, n: w.name, d: w.d })); }
      /* parks first: up to 7 POTA / WWFF, then up to 4 SOTA summits (mountain towns would otherwise show only summits) */
      const U = out.filter((x, i, a) => a.findIndex(y => y.c === x.c) === i).sort((a, b) => a.d - b.d);
      const isS = x => /\//.test(x.c), L = U.filter(x => !isS(x)).slice(0, 7).concat(U.filter(isS).slice(0, 4)).sort((a, b) => a.d - b.d);
      $('kitPick').innerHTML = (label ? '<p class="kit-msg">Closest to <b>' + B.esc(label) + '</b>: tap one.</p>' : '') + L.map(x => btn(x.c, x.n, B.dist(x.d) + ' · ' + progOf(x.c))).join('');
  }

  /* ---------- one place, any program: {prog, c, n, la, lo, t, where, web, off, ky, park (KY park data), sota/kff lists, ft} ---------- */
  async function place(ref) {
    const kp = D.parks.find(x => x.c === ref), kk = D.kff.find(x => x.c === ref), ks = D.summits.find(x => x.c === ref);
    if (kp) return { prog: 'POTA', c: kp.c, n: kp.n, la: kp.la, lo: kp.lo, t: kp.t, where: kp.co ? kp.co + ' County, Kentucky' : 'Kentucky', web: kp.web, off: kp.off, ky: true, park: kp };
    if (kk) { const pk = D.parks.find(x => x.c === kk.p); return { prog: 'WWFF', c: kk.c, n: kk.n, la: kk.la, lo: kk.lo, t: 'WWFF area', where: kk.co ? kk.co + ' County, Kentucky' : 'Kentucky', web: pk && pk.web, off: pk && pk.off, ky: true, park: pk || null }; }
    if (ks) return { prog: 'SOTA', c: ks.c, n: ks.n, la: ks.la, lo: ks.lo, t: (ks.ft ? ks.ft.toLocaleString() + ' ft' : '') + (ks.pts != null ? ' · ' + ks.pts + ' points' : ''), ft: ks.ft, where: ks.co ? ks.co + ' County, Kentucky' : 'Kentucky', ky: true, park: null };
    const o = await B.lookup(ref).catch(() => null); if (!o) return null;
    return { prog: o.prog, c: o.ref, n: o.name, short: o.short, la: o.la, lo: o.lo, t: o.type, where: o.where, web: o.web, off: '', ft: o.ft, us: o.us, st: o.st || '', ky: !!o.ky, park: null };
  }
  /* the other references at the same spot */
  async function others(P) {
    const R = new Map(), add = (c, n, why) => { if (c && c !== P.c && !R.has(c)) R.set(c, { c, n: n || name(c), prog: progOf(c), why }); };
    const kp = P.park;
    if (kp) { if (P.prog !== 'POTA') add(kp.c, kp.n, 'park'); (kp.tf || []).forEach(r => add(r, name(r), '2fer')); (kp.kff || []).forEach(r => add(r, name(r), 'same')); (kp.sota || []).forEach(r => add(r, name(r), 'summit')); }
    if (P.ky && P.prog === 'SOTA') { const F = await B.ky().catch(() => []); F.filter(f => !f._L.proc && B.inside(P.la, P.lo, f.geometry)).forEach(f => B.kyRefs(f).forEach(r => add(r.ref, r.name, 'summit-in'))); }
    if (!P.ky) {
      const [W, Po] = await Promise.all([B.wwffNear(P.la, P.lo, 20).catch(() => []), B.potaNear(P.la, P.lo, 0.3).catch(() => [])]);
      const nm = P.short || P.n;
      if (P.prog !== 'SOTA') { W.filter(w => B.sameName(w.name, nm)).forEach(w => add(w.ref, w.name, 'same')); Po.filter(p => B.sameName(p.name, nm)).forEach(p => add(p.ref, p.name, 'same')); }
      if (P.prog === 'SOTA' && P.us) { try { const F = await B.padusArea(P.la, P.lo, 0.004); F.filter(f => B.inside(P.la, P.lo, f.geometry) && f.properties.Category !== 'Easement').forEach(f => { B.refsFor(f, Po).forEach(r => add(r.ref, r.name, 'summit-in')); W.filter(w => B.sameName(w.name, f._nm)).forEach(w => add(w.ref, w.name, 'summit-in')); }); } catch (e) {} }
    }
    return [...R.values()];
  }

  /* ---------- the kit ---------- */
  async function open(ref) {
    $('kitPick').innerHTML = '<p class="kit-msg">Loading ' + esc(ref) + '…</p>';
    const P = await place(ref);
    if (!P) { $('kitPick').innerHTML = '<p class="kit-msg">Could not find ' + esc(ref) + '. Check the number (and your signal).</p>'; return; }
    cur = P; $('kitPick').innerHTML = ''; $('kitQ').value = '';
    history.replaceState(null, '', '?ref=' + encodeURIComponent(P.c));
    const kp = P.park, rel = [P.c].concat(kp ? [kp.c].concat(kp.kff || [], kp.sota || []) : []);
    const now = Date.now();
    const conds = P.ky ? (CONDS && CONDS.items || []).filter(c => rel.includes(c.ref) && (!c.expires || Date.parse(c.expires) > now)) : [];
    const notes = P.ky ? (NOTES && NOTES.notes || []).filter(n => rel.includes(n.ref)).slice(-3).reverse() : [];
    const saved = (store.get(SAVEKEY) || {})[P.c];
    const g = 'https://www.google.com/maps/dir/?api=1&destination=';
    const progLink = P.prog === 'SOTA' ? ['SOTLAS ↗', 'https://sotl.as/summits/' + P.c] : P.prog === 'WWFF' ? ['WWFF ↗', 'https://wwff.co/directory/?showRef=' + P.c] : ['POTA PAGE ↗', 'https://pota.app/#/park/' + P.c];
    $('kitOut').innerHTML = `
<section class="kit-head"><div class="kit-ref"><span class="kit-p">${esc(P.prog)}</span> ${esc(P.c)}</div><h2>${esc(P.n)}</h2><p>${esc([P.t, P.where].filter(Boolean).join(' · '))}</p>
<div class="kit-btns"><a class="gold" href="${g}${P.la},${P.lo}" target="_blank" rel="noopener">DIRECTIONS ↗</a>${P.off ? `<a href="${esc(P.off)}" target="_blank" rel="noopener">OFFICIAL MAP ↗</a>` : ''}${P.web && P.web !== P.off ? `<a href="${esc(P.web)}" target="_blank" rel="noopener">WEBSITE ↗</a>` : ''}<a href="${esc(progLink[1])}" target="_blank" rel="noopener">${progLink[0]}</a>${P.prog !== 'SOTA' ? `<a href="kpc-park-info.html?q=${encodeURIComponent(P.c)}">PARK INFO ›</a>` : ''}</div></section>
 ${!P.ky && P.us ? '<div id="kitUS"></div>' : ''}<a class="kit-spot" id="kitSpot" href="kpc-spot-me.html?${spotKey[P.prog]}=${encodeURIComponent(P.c)}">📣 SPOT ME AT ${esc(P.c)} ›</a>
<section class="kit-sec"><h3>➕ OTHER REFERENCES AT THIS SPOT</h3><div id="kitMulti"><p class="kit-small">Checking POTA, WWFF and SOTA…</p></div></section>
<section class="kit-sec"><h3>⚠ HEADS UP</h3>${P.ky ? (conds.length ? conds.map(c => `<div class="kit-alert"><b>${esc(c.kind)}</b>${c.details ? ' · ' + esc(c.details) : ''}<span>Reported ${esc(c.seen || '')}${c.call ? ' by ' + esc(c.call) : ''}${c.ref !== P.c ? ' (for ' + esc(c.ref) + ')' : ''}</span></div>`).join('') : '<p>No closures or problems reported by members in the last 30 days.</p>') +
 (notes.length ? '<h4>Latest member tips</h4>' + notes.map(n => `<div class="kit-note">${esc(n.text)}<span>${esc(n.type || 'Tip')} · ${esc(n.call || '')} · ${esc(n.date || '')}</span></div>`).join('') : '') +
 `<div class="kit-btns"><a class="alt" href="kpc-park-notes.html?ref=${encodeURIComponent(kp ? kp.c : P.c)}">ALL PARK NOTES ›</a>${CAMP && CAMP.closures ? `<a class="alt" href="${esc(CAMP.closures.url)}" target="_blank" rel="noopener">STATE PARK CLOSURES ↗</a>` : ''}</div>`
 : `<p>Check ${P.web ? '<a href="' + esc(P.web) + '" target="_blank" rel="noopener">the official website</a>' : 'the official website'} for closures, and the ${P.prog} page for recent activations.</p><div id="kitUSNotes"></div><div class="kit-btns"><a class="alt" href="kpc-park-notes-us.html?ref=${encodeURIComponent(P.c)}#find">PARK NOTES (ALL STATES) ›</a></div>`}</section>
<section class="kit-sec"><h3>☁ WEATHER &amp; ☀ BANDS</h3><div id="kitSun"></div><div id="kitWx">${saved && saved.wx ? '' : 'Loading the forecast…'}</div><div class="kit-btns"><a class="alt" href="kpc-weather.html?lat=${P.la}&lon=${P.lo}&name=${encodeURIComponent(P.c + ' ' + P.n)}">FULL FIELD WEATHER ›</a></div></section>
<section class="kit-sec"><h3>🗺 MAP${P.prog === 'SOTA' ? ': SUMMIT' : ': BOUNDARY'}${kp && (kp.ap || []).length ? ', PARKING &amp; TRAILHEADS' : ''}</h3><div id="kitMap"></div><p class="kit-small">👆 Tap the map to drop a pin for Street View or directions. ◎ ME shows where you are (with your GPS numbers), ⛶ FULL opens the map full screen. The layers button has Satellite + streets, Topo, Terrain and Hillshade.</p><p class="kit-small" id="kitBnd">Loading…</p>
<div class="kit-btns"><a class="gold" href="kpc-in-park.html?ref=${encodeURIComponent(P.c)}">📍 ${P.prog === 'SOTA' ? 'AM I IN THE ACTIVATION ZONE?' : 'AM I IN THE PARK?'} ›</a></div><div class="kit-btns" id="kitFiles"></div></section>
<section class="kit-sec"><h3>⛺ WHERE TO STAY</h3>${stay(P)}</section>
<section class="kit-sec kit-off"><h3>📴 SAVE FOR NO SIGNAL</h3><p>Saves this kit, the boundary, the map around it and today's forecast on this phone, so it opens with no signal. Weather and spots still need signal to update.</p><div class="kit-btns"><button type="button" id="kitSave" class="gold">${saved ? 'UPDATE THE SAVED COPY' : 'SAVE THIS FOR OFFLINE'}</button></div><p class="kit-small" id="kitSaveMsg">${saved ? 'Saved ' + new Date(saved.t).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) + '.' : ''}</p></section>`;
    $('kitSave').onclick = () => saveOffline(P);
    drawMap(P);
    weather(P, saved);
    sun(P, saved);
    autoRefresh(P);
    others(P).then(L => drawMulti(P, L)).catch(() => drawMulti(P, []));
    if (!P.ky && P.us) usExtras(P);
    window.scrollTo({ top: $('kitOut').offsetTop - 70, behavior: 'smooth' });
  }
  /* Other states (Oct 16): park type / how to activate / state parks site from data/parkinfo, tips from
     kpc-park-notes-us.json, federal campgrounds + picnic shelters within 10 mi from data/campfed (same data as the US Trip Planner) */
  const jcache = {};
  const jload = u => jcache[u] || (jcache[u] = fetch(u).then(r => r.ok ? r.json() : null).catch(() => null));
  async function usExtras(P) {
    const st = P.st, ACT = { Automobile: 'car', Campground: 'campground', Pedestrian: 'on foot', Boat: 'boat', Bicycle: 'bike' };
    if (st && P.prog === 'POTA') {
      const d = await jload('data/parkinfo/US-' + st + '.json'), p = d && d.parks && d.parks[P.c], el = $('kitUS');
      if (p && el && cur === P) {
        const how = String(p[3] || '').split(',').map(x => ACT[x.trim()] || x.trim().toLowerCase()).filter(Boolean);
        el.innerHTML = `<p class="kit-small" style="margin:6px 0">${esc(p[2] || '')}${how.length ? (p[2] ? ' · ' : '') + 'activate by ' + esc(how.join(', ')) : ''}${p[7] === 0 ? ' · <b>ATNO: never activated!</b>' : p[7] != null && p[7] <= 5 ? ' · <b>RARE: ' + p[7] + ' activation' + (p[7] === 1 ? '' : 's') + '</b>' : ''}</p>` +
          (d.stateSite && /State Park|State Forest|State Recreation/i.test(p[2]) ? `<div class="kit-btns"><a class="alt" href="${esc(d.stateSite)}" target="_blank" rel="noopener">${esc(st)} STATE PARKS SITE ↗</a></div>` : '');
      }
    }
    const N = await jload('kpc-park-notes-us.json'), tips = ((N && N.notes) || []).filter(n => n.ref === P.c).slice(0, 3), te = $('kitUSNotes');
    if (te && cur === P && tips.length) te.innerHTML = '<h4>Latest tips from operators</h4>' + tips.map(n => `<div class="kit-note">${esc(n.text)}<span>${esc(n.type || 'Tip')} · ${esc(n.call || '')} · ${esc(n.date || '')}</span></div>`).join('');
    const fe = $('kitFed'); if (!fe) return;
    const camps = []; if (st) { const c = await jload('data/campfed/US-' + st + '.json'); ((c && c.camps) || []).forEach(x => { const d = B.km(P.la, P.lo, x[2], x[3]); if (d <= 16.1) camps.push({ x, d }); }); }
    camps.sort((a, b) => a.d - b.d);
    const AG = { FS: 'Forest Service', NPS: 'National Park Service', USACE: 'Army Corps', BLM: 'BLM', FWS: 'Fish & Wildlife', BOR: 'Reclamation' };
    const row = o => `<div class="kit-row"><b>${esc(o.x[1])}</b> <em>${esc(B.dist(o.d))} away</em><span>${esc([AG[o.x[4]] || o.x[4], o.x[5] ? 'can reserve' : 'first come'].filter(Boolean).join(' · '))}</span><span class="kit-l"><a href="${esc(o.x[6])}" target="_blank" rel="noopener">RECREATION.GOV ↗</a></span></div>`;
    const cg = camps.filter(o => o.x[7] !== 's').slice(0, 4), sh = camps.filter(o => o.x[7] === 's').slice(0, 3);
    if (cur !== P) return;
    fe.innerHTML = (cg.length ? '<h4>Federal campgrounds within 10 miles</h4>' + cg.map(row).join('') : '<p class="kit-small">No federal campgrounds on Recreation.gov within 10 miles.</p>') + (sh.length && P.prog !== 'SOTA' ? '<h4>Picnic shelters nearby (good for activating)</h4>' + sh.map(row).join('') : '');
  }
  function drawMulti(P, L) {
    if (cur !== P) return;
    const two = L.filter(x => x.why === '2fer'), same = L.filter(x => x.why === 'same' || x.why === 'park'), sum = L.filter(x => x.why === 'summit'), sin = L.filter(x => x.why === 'summit-in');
    const row = (x, note) => `<div class="kit-row"><b>${esc(x.c)}</b> ${esc(x.n)} <em>${esc(x.prog)}${note ? ' · ' + esc(note) : ''}</em></div>`;
    const html = (same.length ? '<h4>Same place, other programs</h4>' + same.map(x => row(x)).join('') : '') +
      (two.length ? '<h4>Overlapping boundaries (2-fer)</h4>' + two.map(x => row(x)).join('') + '<p class="kit-small">Where the boundaries overlap, one activation counts for each park. Check you\'re inside every one you log.</p>' : '') +
      (sum.length ? '<h4>Summits in this park</h4>' + sum.map(x => row(x, 'only from the summit\'s activation zone')).join('') : '') +
      (sin.length ? '<h4>This summit is inside</h4>' + sin.map(x => row(x, 'summit-to-park')).join('') + '<p class="kit-small">From the activation zone you can log the summit and the park together, if the zone is inside the park boundary.</p>' : '');
    $('kitMulti').innerHTML = html || `<p>No other POTA, WWFF or SOTA references found at this spot.</p>`;
    const q = [spotKey[P.prog] + '=' + encodeURIComponent(P.c)], have = new Set([P.prog]);
    same.concat(sin).forEach(x => { if (!have.has(x.prog)) { have.add(x.prog); q.push(spotKey[x.prog] + '=' + encodeURIComponent(x.c)); } });
    const sp = $('kitSpot'); if (sp) sp.href = 'kpc-spot-me.html?' + q.join('&');
  }
  function stay(P) {
    const card = (c, far) => `<div class="kit-row"><b>${esc(c.name)}</b>${far ? ` <em>${esc(far)}</em>` : ''}${c.status === 'closed' ? ' <em class="bad">CLOSED</em>' : ''}<span>${esc([c.sites, c.season, c.notes || c.note].filter(Boolean).join(' · '))}</span><span class="kit-l">${c.url ? `<a href="${esc(c.url)}" target="_blank" rel="noopener">INFO ↗</a>` : ''}${c.reserve ? `<a href="${esc(c.reserve)}" target="_blank" rel="noopener">RESERVE ↗</a>` : ''}</span></div>`;
    const search = `<div class="kit-btns"><a class="alt" href="https://www.google.com/maps/search/campground/@${P.la},${P.lo},11z" target="_blank" rel="noopener">CAMPGROUNDS NEAR HERE ↗</a><a class="alt" href="https://www.recreation.gov/search?q=campground&lat=${P.la}&lng=${P.lo}&radius=25" target="_blank" rel="noopener">RECREATION.GOV ↗</a></div>`;
    if (!P.ky) return '<div id="kitFed"><p class="kit-small">Looking for federal campgrounds and picnic shelters nearby…</p></div><p class="kit-small">State park campgrounds aren\'t in this list: check the park\'s own website. These search near this spot:</p>' + search;
    const cg = P.park && (CAMP && CAMP.parks || []).find(x => x.pota === P.park.c);
    if (cg && ((cg.campgrounds || []).length || (cg.lodging || []).length)) return (cg.campgrounds || []).map(c => card(c)).join('') + (cg.lodging || []).map(c => card(c)).join('') + `<div class="kit-btns"><a class="alt" href="kpc-campgrounds.html">CAMPGROUNDS &amp; CABINS ›</a></div>`;
    const all = []; (CAMP && CAMP.parks || []).forEach(x => (x.campgrounds || []).forEach(c => { if (isFinite(c.la)) all.push({ c, x, d: B.km(P.la, P.lo, c.la, c.lo) }); }));
    const n = all.sort((a, b) => a.d - b.d).slice(0, 2), wma = P.park && /WMA|Wildlife/.test(P.park.t + P.park.n);
    return `<p>No campground or cabins listed ${P.prog === 'SOTA' ? 'at this summit' : 'inside this park'}.${wma && CAMP && CAMP.wmaRule ? ' ' + esc(CAMP.wmaRule.text) : ''}</p>` + (n.length ? '<h4>Closest campgrounds in Kentucky parks</h4>' + n.map(o => card(o.c, B.dist(o.d) + ' away (' + o.x.pota + ')')).join('') : '') + search;
  }

  /* ---------- map ---------- */
  async function drawMap(P) {
    if (map) { map.remove(); map = null; }
    geo = null;
    if (!window.L) { $('kitMap').innerHTML = '<p class="kit-msg">Map unavailable.</p>'; return; }
    map = L.map('kitMap').setView([P.la, P.lo], P.prog === 'SOTA' ? 15 : 13);
    if (window.KPCLayers) KPCLayers(map); else L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(map);
    if (window.KPCPin) KPCPin(map, { on: 'contextmenu' }); if (window.KPCHere) KPCHere(map, { onRef: r => { location.href = 'kpc-kit.html?ref=' + encodeURIComponent(r); } });
    if (window.KPCLocate) KPCLocate(map);
    if (window.KPCFull) KPCFull(map);
    L.marker([P.la, P.lo]).addTo(map).bindPopup(esc(P.c + ' ' + P.n) + '<br>' + esc(P.prog) + (P.prog === 'SOTA' ? ' summit' : ' pin'));
    const ap = (P.park && P.park.ap) || [];
    ap.forEach(a => L.circleMarker([a[0], a[1]], { radius: 7, color: '#fff', weight: 2, fillColor: '#1d5a3a', fillOpacity: 1 }).addTo(map).bindPopup(`<b>${esc(a[2])}</b><br><a href="https://www.google.com/maps/dir/?api=1&destination=${a[0]},${a[1]}" target="_blank" rel="noopener">Directions ↗</a>`));
    const o = { ref: P.c, name: P.n, la: P.la, lo: P.lo, points: ap };
    const files = fc => { $('kitFiles').innerHTML = `<a class="alt" href="#" data-f="kml">KML · GOOGLE EARTH / MAP APPS</a><a class="alt" href="#" data-f="gpx">GPX · GARMIN / GPS UNITS</a>` + B.WHICH; $('kitFiles').querySelectorAll('[data-f]').forEach(b => b.onclick = e => { e.preventDefault(); B.saveGeo(fc, b.dataset.f, o, b); }); };
    if (P.prog === 'SOTA') {
      $('kitBnd').innerHTML = `Summit${P.ft ? ' height ' + P.ft.toLocaleString() + ' ft' : ''}. The activation zone is everything within 82 ft (25 m) of height below the top; SOTLAS shows it drawn on a map. Use <b>Am I in the activation zone?</b> when you get there.`;
      files({ type: 'FeatureCollection', features: [] }); return;
    }
    let feats = [];
    if (P.park) { try { feats = await B.kyFor(P.park.c); } catch (e) {} }
    const kpc = feats.length && feats.every(f => f._L.kpc), proc = feats.some(f => f._L && f._L.proc);
    if (!feats.length && (P.us || P.ky)) { try { feats = await B.padusByName(P.short || (P.park ? P.park.n : P.n), P.la, P.lo); } catch (e) {} }
    let wsrc = '';
    if (!feats.length && !P.us && !P.ky && B.worldByName) { try { feats = await B.worldByName(P.ref || P.c || '', P.prog === 'SOTA' ? '' : (P.short || P.n || ''), P.la, P.lo, { small: P.prog === 'SOTA', type: P.t }); wsrc = feats.length ? feats[0]._src : ''; } catch (e) {} }
    if (cur !== P) return;
    const fc = { type: 'FeatureCollection', features: feats.map(f => ({ type: 'Feature', properties: { NAME: f._nm }, geometry: f.geometry })) };
    geo = feats.length ? fc : null;
    if (feats.length) {
      const lay = L.geoJSON(fc, { style: kpc ? { color: '#ffd400', weight: 3, dashArray: '12 5 2 5', fillOpacity: 0 } : { color: '#ffb000', weight: 3, fillColor: '#ffb000', fillOpacity: 0 } }).addTo(map);
      if (!proc) try { map.fitBounds(lay.getBounds(), { padding: [16, 16], maxZoom: 15 }); } catch (e) {}
      $('kitBnd').innerHTML = (kpc ? '<b>Approximate outline drawn by KPC</b> from OpenStreetMap (this park has no official map file). OpenStreetMap is drawn by volunteers, so it can be off; check the park\'s own map.' : proc ? 'Daniel Boone National Forest outer line (it includes private land).' : (wsrc ? '<b>' + esc(feats[0]._nm) + '</b>' + (feats[0]._info ? ' · ' + esc(feats[0]._info) : '') + '. Official outline from ' + esc(wsrc) + (/^EEA/.test(wsrc) ? ' (matched by name at the POTA pin)' : '') + '.' : 'Official boundary' + (feats[0]._L ? ' from ' + [...new Set(feats.map(f => f._L.agency))].map(esc).join(' and ') : ' (USGS PAD-US)') + '.')) + (ap.length ? ` Green dots: ${ap.length} parking / trailhead / entrance point${ap.length > 1 ? 's' : ''} (tap for directions).` : '');
      files(fc);
    } else $('kitBnd').innerHTML = (P.park && P.park.nob ? esc(P.park.nob) : 'No boundary file found. Use the official map.') + (ap.length ? ' Green dots: parking / trailhead points.' : '');
  }

  /* ---------- weather (Open-Meteo + NWS alerts) ---------- */
  const WX = c => c >= 95 ? '⛈ Thunderstorms' : c >= 80 ? '🌦 Showers' : c >= 71 ? '🌨 Snow' : c >= 61 ? '🌧 Rain' : c >= 51 ? '🌦 Drizzle' : c >= 45 ? '🌫 Fog' : c >= 3 ? '☁ Cloudy' : c >= 1 ? '⛅ Partly cloudy' : '☀ Clear';
  async function fetchWx(p) {
    const u = `https://api.open-meteo.com/v1/forecast?latitude=${p.la}&longitude=${p.lo}&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m,wind_gusts_10m&hourly=temperature_2m,precipitation_probability,weather_code,wind_gusts_10m&daily=sunrise,sunset&forecast_days=1&forecast_hours=12&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=auto`;
    const [w, a] = await Promise.all([j(u), fetch(`https://api.weather.gov/alerts/active?point=${p.la.toFixed(4)},${p.lo.toFixed(4)}`, { headers: { Accept: 'application/geo+json' } }).then(r => r.ok ? r.json() : null).catch(() => null)]);
    if (!w || !w.current) return null;
    return { t: Date.now(), w, alerts: a ? (a.features || []).map(f => ({ ev: f.properties.event, sev: f.properties.severity, until: f.properties.ends || f.properties.expires })) : null };
  }
  function showWx(x, old) {
    const c = x.w.current, h = x.w.hourly, rows = h.time.map((t, i) => ({ t, temp: h.temperature_2m[i], pp: h.precipitation_probability[i], wc: h.weather_code[i], g: h.wind_gusts_10m[i] }));
    const storm = rows.some(r => r.wc >= 95), maxPP = Math.max(...rows.map(r => r.pp || 0)), maxG = Math.max(...rows.map(r => r.g || 0));
    const calls = [storm ? '<b class="bad">Storms in the next 12 h: no antennas up near lightning.</b>' : '', maxG >= 25 ? `Gusts to ${Math.round(maxG)} mph: guy your mast.` : '', maxPP >= 50 ? `Rain chance up to ${maxPP}%: bring a tarp.` : ''].filter(Boolean);
    $('kitWx').innerHTML = (!old ? `<p class="kit-small">Updated ${new Date(x.t).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })} · refreshes every 15 minutes while this page is open</p>` : '') + (old ? `<p class="kit-small">Saved forecast from ${new Date(x.t).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })} (no signal right now).</p>` : '') +
      (x.alerts && x.alerts.length ? x.alerts.map(a => `<div class="kit-alert"><b>${esc(a.ev)}</b><span>${a.until ? 'until ' + new Date(a.until).toLocaleString([], { weekday: 'short', hour: 'numeric', minute: '2-digit' }) : ''}</span></div>`).join('') : x.alerts ? '<p class="kit-small">No weather alerts for this spot.</p>' : '') +
      `<div class="kit-now"><b>${Math.round(c.temperature_2m)}°F</b><span>${WX(c.weather_code)} · feels ${Math.round(c.apparent_temperature)}° · wind ${Math.round(c.wind_speed_10m)} mph, gusts ${Math.round(c.wind_gusts_10m)}</span></div>` +
      (calls.length ? `<p>${calls.join(' ')}</p>` : '<p>Looks fine for the next 12 hours.</p>') +
      (x.w.daily && x.w.daily.sunrise ? `<p class="kit-small">🌅 Sunrise ${new Date(x.w.daily.sunrise[0]).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })} · 🌇 Sunset ${new Date(x.w.daily.sunset[0]).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })} (gray line: the half hour around each is often good for long distance)</p>` : '') +
      `<div class="kit-hours">${rows.filter((r, i) => i % 2 === 0).map(r => `<div><span>${new Date(r.t).toLocaleTimeString([], { hour: 'numeric' })}</span><b>${Math.round(r.temp)}°</b><span>${WX(r.wc).split(' ')[0]} ${r.pp || 0}%</span></div>`).join('')}</div>`;
  }
  async function weather(p, saved) {
    if (saved && saved.wx) showWx(saved.wx, true);
    const x = await fetchWx(p);
    if (x) { showWx(x, false); const S = store.get(SAVEKEY) || {}; if (S[p.c]) { S[p.c].wx = x; S[p.c].t = S[p.c].t || x.t; store.set(SAVEKEY, S); } }
    else if (!saved || !saved.wx) $('kitWx').innerHTML = '<p class="kit-small">No forecast right now (no signal?).</p>';
  }

  /* ---------- solar / band conditions (NOAA SWPC: Kp every 3 hours, solar flux once a day) ---------- */
  async function fetchSun() {
    const [k, f] = await Promise.all([j('https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'), j('https://services.swpc.noaa.gov/products/summary/10cm-flux.json')]);
    let kp = null, sfi = null;
    try { const r = k[k.length - 1]; kp = Number(Array.isArray(r) ? r[1] : r.Kp); } catch (e) {}
    try { sfi = Number((Array.isArray(f) ? f[0] : f).flux); } catch (e) {}
    if (!isFinite(kp) && !isFinite(sfi)) return null;
    return { t: Date.now(), kp: isFinite(kp) ? kp : null, sfi: isFinite(sfi) ? sfi : null };
  }
  function showSun(x, old) {
    const el = $('kitSun'); if (!el) return;
    if (!x) { el.innerHTML = '<p class="kit-small">Solar numbers not available right now.</p>'; return; }
    const kp = x.kp, sfi = x.sfi, hr = new Date().getHours(), day = hr >= 8 && hr < 18;
    const storm = kp != null && kp >= 5, unset = kp != null && kp >= 4;
    const lvl = storm ? ['bad', 'ROUGH'] : sfi == null ? ['', '?'] : sfi >= 150 && !unset ? ['good', 'GREAT'] : sfi >= 100 && !unset ? ['good', 'GOOD'] : sfi >= 80 ? ['ok', 'FAIR'] : ['ok', 'SO-SO'];
    const bands = storm ? 'Geomagnetic storm: high bands are noisy and fade; try 40 m, and expect weaker signals.' : day ? (sfi >= 120 ? 'Daytime: 20, 17, 15 and even 10 m should be open.' : 'Daytime: 20 and 40 m are your best bets.') : (sfi >= 150 ? 'Evening: 20 m may stay open; 40 and 80 m for closer stations.' : 'Evening and night: 40 and 80 m work best.');
    el.innerHTML = `<div class="kit-sun"><span class="kit-sb ${lvl[0]}">HF ${lvl[1]}</span><span>Solar flux <b>${sfi != null ? Math.round(sfi) : '?'}</b> · Kp <b>${kp != null ? kp.toFixed(kp % 1 ? 1 : 0) : '?'}</b> <small>(flux: higher = better high bands · Kp 0-9: lower = calmer)</small></span></div><p class="kit-small">${bands}${old ? ' (saved numbers, no signal right now)' : ''} <a href="kpc-live.html">Live band activity ›</a></p>`;
  }
  async function sun(p, saved) {
    if (saved && saved.sun) showSun(saved.sun, true);
    const x = await fetchSun();
    if (x) { showSun(x, false); const S = store.get(SAVEKEY) || {}; if (S[p.c]) { S[p.c].sun = x; store.set(SAVEKEY, S); } }
    else if (!saved || !saved.sun) showSun(null);
  }
  let timer = null;
  function autoRefresh(P) { clearInterval(timer); timer = setInterval(() => { if (document.hidden || cur !== P) return; weather(P, null); sun(P, null); }, 15 * 60 * 1000); }

  /* ---------- save for offline ---------- */
  function tileList(p, bb) {
    const t = [], tx = (lo, z) => Math.floor((lo + 180) / 360 * 2 ** z), ty = (la, z) => { const r = la * Math.PI / 180; return Math.floor((1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * 2 ** z); };
    for (let z = 10; z <= 16; z++) {
      const pad = z <= 12 ? 0.08 : 0.01, x0 = tx(bb[0] - pad, z), x1 = tx(bb[2] + pad, z), y0 = ty(bb[3] + pad, z), y1 = ty(bb[1] - pad, z);
      const n = (x1 - x0 + 1) * (y1 - y0 + 1); if (t.length + n > 900) break;
      for (let x = x0; x <= x1; x++) for (let y = y0; y <= y1; y++) t.push(`https://tile.openstreetmap.org/${z}/${x}/${y}.png`);
    }
    return t;
  }
  async function saveOffline(p) {
    const msg = $('kitSaveMsg'), btn = $('kitSave');
    if (!('caches' in window)) { msg.textContent = 'This browser cannot save pages for offline.'; return; }
    btn.disabled = true; msg.textContent = 'Saving the kit…';
    try {
      const app = await caches.open(APP);
      const scripts = [...document.querySelectorAll('script[src],link[rel=stylesheet][href]')].map(e => e.src || e.href).filter(u => u.startsWith(location.origin) || /unpkg\.com\/leaflet@1\.9\.4/.test(u));
      const files = ['kpc-kit.html', 'kpc-in-park.html', 'kpc-in-park.js', 'kpc-bounds.js', 'kpc-map-tools.js', 'kpc-padus-layer.js', 'kpc-place-suggest.js', 'kpc-ky-data.json', 'kpc-conditions.json', 'kpc-park-notes.json', 'kpc-campgrounds.json', 'KPC-logo.png'].concat(B.KY.map(L => L.file), B.tilesUsed(), p.prog === 'WWFF' && !p.ky ? ['data/wwff/' + p.c.split('-')[0] + '.json'] : []);
      const urls = [...new Set(files.map(f => new URL(f, location.href).href).concat(scripts).concat(['leaflet.css', 'leaflet.js', 'images/marker-icon.png', 'images/marker-icon-2x.png', 'images/marker-shadow.png', 'images/layers.png'].map(f => 'https://unpkg.com/leaflet@1.9.4/dist/' + f)))];
      let ok = 0;
      for (const u of urls) { try { const r = await fetch(u, { cache: 'reload' }); if (r.ok) { const k = new URL(u); if (k.origin === location.origin) k.search = ''; await app.put(k.href, r); ok++; } } catch (e) {} }
      const bb = geo ? geo.features.reduce((a, f) => { const b = B.bbox(f.geometry); return [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])]; }, [180, 90, -180, -90]) : [p.lo - .03, p.la - .03, p.lo + .03, p.la + .03];
      if (bb[2] - bb[0] > 0.6 || bb[3] - bb[1] > 0.6) { bb[0] = p.lo - .08; bb[2] = p.lo + .08; bb[1] = p.la - .08; bb[3] = p.la + .08; }
      const tiles = tileList(p, bb), tc = await caches.open(TILES); let done = 0;
      for (let i = 0; i < tiles.length; i += 6) {
        await Promise.all(tiles.slice(i, i + 6).map(async u => { try { if (await tc.match(u)) { done++; return; } const r = await fetch(u, { mode: 'cors' }); if (r.ok) { await tc.put(u, r); done++; } } catch (e) {} }));
        msg.textContent = `Saving the map around the park… ${Math.min(100, Math.round((i + 6) / tiles.length * 100))}%`;
      }
      const wx = await fetchWx(p);
      const S = store.get(SAVEKEY) || {}; S[p.c] = { t: Date.now(), name: p.n, wx: wx || (S[p.c] && S[p.c].wx) || null, sun: (await fetchSun()) || (S[p.c] && S[p.c].sun) || null }; store.set(SAVEKEY, S);
      msg.innerHTML = `✓ Saved ${new Date().toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}: the kit, ${done} map pieces and today's forecast. To test it, turn on airplane mode and open this page again.`;
      btn.textContent = 'UPDATE THE SAVED COPY';
    } catch (e) { msg.textContent = 'Saving stopped: ' + (e.message || 'storage full?'); }
    btn.disabled = false;
  }

  /* ---------- start ---------- */
  $('kitForm').addEventListener('submit', e => { e.preventDefault(); pick($('kitQ').value); });
  if (window.KPCTA) KPCTA.attach($('kitQ'), ref => open(ref), { onTown: t => listNear(t.la, t.lo, t.v) });
  $('kitNear').addEventListener('click', near);
  document.addEventListener('click', e => { const b = e.target.closest('#kitPick [data-ref], #kitSaved [data-ref]'); if (b) { e.preventDefault(); open(b.dataset.ref); } });
  load();
})();
