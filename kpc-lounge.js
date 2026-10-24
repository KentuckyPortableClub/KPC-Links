/* KPC ACTIVATORS LOUNGE (kpc-activators-lounge.html, Opus Oct 24 2026; Brandon: 'it is go … keep it hidden for now').
   The front door for activators, every program, anywhere: ONE search box (park, WWFF area or summit: name, number or NEAR ME)
   → a short card with the right buttons into the tools we already have, plus today's HF conditions and every activator tool
   tagged with the programs it works for (POTA / WWFF / SOTA) and where (anywhere / US / Kentucky).
   Data: KPCB.lookup (any reference, any country), api.pota.app/lookup (park names, any country), locations.json (US SOTA +
   WWFF names, loaded only for a name search), data/pota|wwff|sota/t tiles (NEAR ME, worldwide), NOAA SWPC (conditions). */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const store = { get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  async function j(u, ms) { const c = new AbortController(), t = setTimeout(() => c.abort(), ms || 15000); try { const r = await fetch(u, { signal: c.signal }); if (!r.ok) throw new Error('HTTP ' + r.status); return await r.json(); } finally { clearTimeout(t); } }
  const km = (a, b, c, d) => { const r = Math.PI / 180, x = Math.sin((c - a) * r / 2) ** 2 + Math.cos(a * r) * Math.cos(c * r) * Math.sin((d - b) * r / 2) ** 2; return 12742 * Math.asin(Math.sqrt(x)); };
  const mi = k => { const m = k / 1.609344; return m < 10 ? m.toFixed(1) + ' mi' : Math.round(m) + ' mi'; };
  const progOf = r => /\//.test(r) ? 'SOTA' : /^[A-Z0-9]{1,4}FF-/.test(r) ? 'WWFF' : 'POTA';
  const kind = q => { q = q.trim().toUpperCase().replace(/\s+/g, '');
    let m = q.match(/^([A-Z0-9]{1,4}\/[A-Z0-9]{2})-(\d{1,3})$/); if (m) return m[1] + '-' + m[2].padStart(3, '0');
    m = q.match(/^([A-Z0-9]{1,4})-(\d{1,5})$/); if (m) return m[1] + '-' + m[2].padStart(4, '0');
    if (/^\d{1,5}$/.test(q)) return 'US-' + q.padStart(4, '0');   /* a bare number = a US park */
    return null; };
  const B = () => window.KPCB;

  /* ---------------- the search ---------------- */
  function msg(h) { $('lgPick').innerHTML = '<p class="lg-msg">' + h + '</p>'; }
  async function search(q) {
    q = (q || '').trim(); if (!q) return; $('lgOut').innerHTML = '';
    history.replaceState(null, '', '?q=' + encodeURIComponent(q));
    const ref = kind(q);
    if (ref) { msg('Looking up ' + esc(ref) + '…'); return open(ref); }
    msg('Searching…');
    const out = [];
    try { const L = await j('https://api.pota.app/lookup?search=' + encodeURIComponent(q) + '&size=60'); (L || []).filter(x => x.type === 'park').forEach(x => out.push({ prog: 'POTA', ref: x.value, name: String(x.display || '').replace(/^\S+\s+/, '') })); } catch (e) {}
    try {
      if (!search.loc) search.loc = j('locations.json', 30000).catch(() => []);
      const L = await search.loc, w = q.toLowerCase().split(/\s+/).filter(Boolean);
      L.filter(r => r[0] !== 'POTA' && w.every(x => String(r[2]).toLowerCase().includes(x))).slice(0, 40).forEach(r => out.push({ prog: r[0], ref: r[1], name: r[2] }));
    } catch (e) {}
    if (!out.length) return msg('Nothing matches <b>' + esc(q) + '</b>. Try fewer words, or type the number (US-1234, GFF-0001, W4K/EC-001).');
    if (out.length === 1) return open(out[0].ref);
    out.sort((a, b) => (/^US-/.test(b.ref) - /^US-/.test(a.ref)) || a.ref.localeCompare(b.ref, undefined, { numeric: true }));
    $('lgPick').innerHTML = `<p class="lg-help">${out.length > 60 ? 'The first 60 of ' + out.length : out.length} matches. Pick one:</p>` + out.slice(0, 60).map(pickBtn).join('');
  }
  const SEEN = new Map();   /* the last list: a fallback for the card when the lookup service does not answer (no signal) */
  const pickBtn = p => { SEEN.set(p.ref, p); return `<button type="button" class="lg-pk" data-ref="${esc(p.ref)}"><span class="lg-tag ${p.prog.toLowerCase()}">${p.prog}</span><b>${esc(p.name)}</b><span class="lg-r">${esc(p.ref)}${p.d != null ? ' · ' + mi(p.d) : ''} ›</span></button>`; };

  /* NEAR ME: our own worldwide copies (1-degree tiles), no outside service needed */
  async function near() {
    if (!navigator.geolocation) return msg('This browser cannot give a location. Type a name or number instead.');
    msg('Finding where you are…');
    navigator.geolocation.getCurrentPosition(async pos => {
      const la = pos.coords.latitude, lo = pos.coords.longitude, R = 40;
      const tiles = (dir) => { const K = new Set(), dla = R / 111, dlo = R / (111 * Math.cos(la * Math.PI / 180)); for (const a of [la - dla, la, la + dla]) for (const o of [lo - dlo, lo, lo + dlo]) K.add(Math.floor(a) + '_' + Math.floor(o)); return Promise.all([...K].map(k => fetch(dir + k + '.json').then(r => r.ok ? r.json() : []).catch(() => []))).then(x => x.flat()); };
      /* POTA tiles skip the US + Canada (those parks are in the state lists): ask POTA's own map for them, and with no
         signal fall back to our US search list */
      const usca = () => (B() && B().potaNear ? B().potaNear(la, lo, 0.4).then(L => L.map(p => [p.ref, p.name, p.la, p.lo])) : Promise.reject()).catch(() => (search.loc || (search.loc = j('locations.json', 30000).catch(() => []))).then(L => L.filter(r => r[0] === 'POTA' && Math.abs(r[3] - la) < 0.5 && Math.abs(r[4] - lo) < 0.7).map(r => [r[1], r[2], r[3], r[4]])));
      const [P0, P1, W, S] = await Promise.all([tiles('data/pota/t/'), usca(), tiles('data/wwff/t/'), tiles('data/sota/t/')]);
      const P = P0.concat(P1.filter(r => !P0.some(x => x[0] === r[0])));
      const all = [].concat(P.map(r => ({ prog: 'POTA', ref: r[0], name: r[1], la: r[2], lo: r[3] })), W.map(r => ({ prog: 'WWFF', ref: r[0], name: r[1], la: r[2], lo: r[3] })),
        S.map(r => ({ prog: 'SOTA', ref: r[0], name: r[1] && r[1] !== r[0] ? r[1] : 'Unnamed summit', la: r[4], lo: r[5] })));
      all.forEach(p => { p.d = km(la, lo, p.la, p.lo); });
      const L = all.filter(p => p.d <= R).sort((a, b) => a.d - b.d).slice(0, 25);
      $('lgPick').innerHTML = L.length ? `<p class="lg-help">Closest to you (straight-line miles):</p>` + L.map(pickBtn).join('') : '<p class="lg-msg">No park, WWFF area or summit within 25 miles that we know of.</p>';
    }, e => msg(e.code === 1 ? 'Location is blocked for this page. Allow it in the browser settings, or type a name.' : 'Could not get your location. Type a name or number instead.'), { enableHighAccuracy: false, timeout: 15000, maximumAge: 300000 });
  }

  /* ---------------- one place: a short card with the right doors ---------------- */
  async function open(ref) {
    let o = null;
    try { if (B()) o = await B().lookup(ref); } catch (e) {}
    if (!o && SEEN.has(ref)) { const x = SEEN.get(ref), us = /^US-|^KFF-|^W\d|^K\d|^N\d/.test(ref); o = { prog: x.prog, ref, name: x.name, la: x.la, lo: x.lo, us, ky: /^W4K\//.test(ref) || (/^(US|KFF)-/.test(ref) && B() && B().inKY && B().inKY(x.la, x.lo)), st: '', where: '', type: '' }; if (o.ky && o.prog === 'WWFF') o.st = 'KY'; }
    if (!o) return msg('Could not find <b>' + esc(ref) + '</b>. Check the number, or search by name (the lookup needs a signal).');
    $('lgPick').innerHTML = '';
    store.set('kpcLgLast', { ref: o.ref, name: o.name, prog: o.prog });
    history.replaceState(null, '', '?q=' + encodeURIComponent(o.ref));
    const P = o.prog, R = encodeURIComponent(o.ref), here = o.la != null ? o.la + ',' + o.lo : '';
    const ky = !!o.ky || (P === 'SOTA' && /^W4K\//.test(o.ref)) || (P === 'WWFF' && o.us && o.st === 'KY');
    const prog = { POTA: ['POTA PAGE', 'https://pota.app/#/park/' + R], WWFF: ['WWFF PAGE', 'https://wwff.co/directory/?showRef=' + R], SOTA: ['SOTLAS PAGE', 'https://sotl.as/summits/' + R] }[P];
    const b = [];
    b.push(['🧰 ACTIVATION KIT', 'kpc-kit.html?ref=' + R, 'gold']);
    if (P === 'SOTA') b.push(['⛰ ACTIVATION ZONE', 'kpc-sota-az.html#' + o.ref]);
    else b.push(['📍 AM I IN THE PARK?', 'kpc-in-park.html?ref=' + R]);
    if (here) b.push(['🧭 DIRECTIONS', 'https://www.google.com/maps/dir/?api=1&destination=' + here, '', 1]);
    if (here) b.push(['🌦 WEATHER', 'kpc-weather.html?lat=' + o.la + '&lon=' + o.lo + '&name=' + encodeURIComponent(o.name)]);
    if (P === 'POTA' && o.us) b.push(['🖨 PRINT A PARK SHEET', 'kpc-park-sheet.html?ref=' + R]);
    if (ky) b.push(['📝 PARK NOTES', 'kpc-park-notes.html#' + R]); else if (o.us) b.push(['📝 PARK NOTES', 'kpc-park-notes-us.html?ref=' + R]);
    if (o.us) b.push(['🚗 TRIP PLANNER', 'kpc-planner-us.html?q=' + R]);
    b.push(['🔎 OFFICIAL INFO', 'kpc-park-info.html?q=' + R]);
    if (o.web) b.push(['🌐 OFFICIAL WEBSITE', o.web, '', 1]);
    b.push([prog[0] + ' ↗', prog[1], '', 1]);
    $('lgOut').innerHTML = `<section class="lg-card">
      <div class="lg-ch"><span class="lg-tag ${P.toLowerCase()}">${P}</span> <span class="lg-ref">${esc(o.ref)}</span></div>
      <h2>${esc(o.name)}</h2>
      <p class="lg-where">${esc([o.type, o.where].filter(Boolean).join(' · '))}</p>
      <div class="lg-btns">${b.map(x => `<a class="${x[2] || ''}" href="${esc(x[1])}"${x[3] ? ' target="_blank" rel="noopener"' : ''}>${esc(x[0])}</a>`).join('')}</div>
      <p class="lg-small">${ky ? 'Kentucky: the Activation Kit adds member reports, parking, trailheads and places to stay.' : o.us ? 'Outside Kentucky some tools have less: boundaries come from the national map, and Park Notes only has what members sent in.' : 'Outside the US: the Kit, Am I in the Park and the weather forecast work; boundaries are approximate and marked so.'}</p>
    </section>`;
    $('lgOut').scrollIntoView({ block: 'start', behavior: 'smooth' });
  }

  /* ---------------- today's HF conditions (NOAA SWPC; same reading as the Activation Kit) ---------------- */
  async function sun() {
    const el = $('lgSun'); if (!el) return;
    let kp = null, sfi = null;
    try { const [k, f] = await Promise.all([j('https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'), j('https://services.swpc.noaa.gov/products/summary/10cm-flux.json')]);
      try { const r = k[k.length - 1]; kp = Number(Array.isArray(r) ? r[1] : r.Kp); } catch (e) {}
      try { sfi = Number((Array.isArray(f) ? f[0] : f).flux); } catch (e) {} } catch (e) {}
    if (!isFinite(kp)) kp = null; if (!isFinite(sfi)) sfi = null;
    if (kp == null && sfi == null) { el.innerHTML = '<span class="lg-sb">HF ?</span><span>The solar numbers did not load. <a href="kpc-space-weather.html">Radio Conditions ›</a></span>'; return; }
    const hr = new Date().getHours(), day = hr >= 8 && hr < 18, storm = kp != null && kp >= 5, unset = kp != null && kp >= 4;
    const lvl = storm ? ['bad', 'ROUGH'] : sfi == null ? ['', '?'] : sfi >= 150 && !unset ? ['good', 'GREAT'] : sfi >= 100 && !unset ? ['good', 'GOOD'] : sfi >= 80 ? ['ok', 'FAIR'] : ['ok', 'SO-SO'];
    const tip = storm ? 'Geomagnetic storm: high bands are noisy; try 40 m.' : day ? (sfi >= 120 ? 'Daytime: 20, 17, 15 and 10 m should be open.' : 'Daytime: 20 and 40 m are your best bets.') : (sfi >= 150 ? 'Evening: 20 m may stay open; 40 and 80 m for closer stations.' : 'Evening and night: 40 and 80 m work best.');
    el.innerHTML = `<span class="lg-sb ${lvl[0]}">HF ${lvl[1]}</span><span>Solar flux <b>${sfi != null ? Math.round(sfi) : '?'}</b> · Kp <b>${kp != null ? kp.toFixed(kp % 1 ? 1 : 0) : '?'}</b> · ${tip} <a href="kpc-space-weather.html">Radio Conditions ›</a></span>`;
  }

  function init() {
    $('lgForm').addEventListener('submit', e => { e.preventDefault(); search($('lgQ').value); });
    $('lgNear').addEventListener('click', near);
    $('lgPick').addEventListener('click', e => { const b = e.target.closest('[data-ref]'); if (b) { $('lgQ').value = b.dataset.ref; open(b.dataset.ref); } });
    const last = store.get('kpcLgLast', null);
    if (last && last.ref) $('lgLast').innerHTML = 'Last one: <button type="button" class="lg-link" data-last="1">' + esc(last.ref + ' ' + (last.name || '')) + '</button>';
    $('lgLast').addEventListener('click', e => { if (e.target.closest('[data-last]')) { $('lgQ').value = last.ref; open(last.ref); } });
    const q = new URLSearchParams(location.search).get('q'); if (q) { $('lgQ').value = q; search(q); }
    sun(); setInterval(() => { if (!document.hidden) sun(); }, 15 * 60 * 1000);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
