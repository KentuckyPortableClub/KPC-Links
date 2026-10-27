/* KPC RARELY ACTIVATED PARKS, EVERYWHERE (Opus Oct 24 2026; Activators Lounge step 3).
   Kentucky: POTA's public records read live (KPC.history in kpc-tools.js: activations with 10+ QSOs, QSOs, last date), as before.
   Every other US state, Canadian province and 64 countries: the activation counts the nightly bots keep
   (data/parkinfo/index.json field 6, CA.json / <PFX>.json field 7). Colours: never / 1-5 / 6-20 / 21-75 / 76+.
   HIDE MY PARKS uses the file loaded in the Park Tracker (localStorage kpcTrackActs). NEAR ME sorts by distance. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const store = { get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  /* Storage plan Step B (Oct 27): data/parkinfo now lives on KentuckyPortableClub/KPC-Data. */
  const j = u => ((window.KPC && KPC.dataUrl) ? KPC.dataUrl(u) : fetch(u)).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
  const ST = { AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California', CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', DC: 'District of Columbia', FL: 'Florida', GA: 'Georgia', HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa', KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland', MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri', MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York', NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VT: 'Vermont', VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming' };
  const PROV = { AB: 'Alberta', BC: 'British Columbia', MB: 'Manitoba', NB: 'New Brunswick', NL: 'Newfoundland and Labrador', NS: 'Nova Scotia', NT: 'Northwest Territories', NU: 'Nunavut', ON: 'Ontario', PE: 'Prince Edward Island', QC: 'Quebec', SK: 'Saskatchewan', YT: 'Yukon' };
  const PARKINFO = ['AG', 'AI', 'AT', 'AU', 'AW', 'BB', 'BE', 'BL', 'BM', 'BQ', 'BS', 'BZ', 'CH', 'CR', 'CU', 'CW', 'CZ', 'DE', 'DK', 'DM', 'DO', 'EE', 'ES', 'FI', 'FR', 'GB', 'GD', 'GL', 'GP', 'GT', 'HN', 'HR', 'HT', 'HU', 'IE', 'IT', 'JM', 'JP', 'KN', 'KY', 'LC', 'LT', 'LU', 'LV', 'MF', 'MQ', 'MS', 'MX', 'NI', 'NL', 'NO', 'PA', 'PL', 'PM', 'PT', 'RO', 'SE', 'SI', 'SK', 'SV', 'SX', 'TC', 'TT', 'VC', 'VG'];
  let DN = null; try { DN = new Intl.DisplayNames(['en'], { type: 'region' }); } catch (e) {}
  const country = p => { try { const n = DN && DN.of(p); if (n && n !== p) return n; } catch (e) {} return p; };
  const placeName = k => /^US-/.test(k) ? ST[k.slice(3)] || k : /^CA-/.test(k) ? PROV[k.slice(3)] || k : country(k);
  const col = n => n == null ? '#9a948a' : n === 0 ? '#b5452b' : n <= 5 ? '#e08a2c' : n <= 20 ? '#d5a63a' : n <= 75 ? '#7fb069' : '#1d5a3a';
  const km = (a, b, c, d) => { const r = Math.PI / 180, x = Math.sin((c - a) * r / 2) ** 2 + Math.cos(a * r) * Math.cos(c * r) * Math.sin((d - b) * r / 2) ** 2; return 12742 * Math.asin(Math.sqrt(x)); };
  const potaUrl = r => 'https://pota.app/#/park/' + encodeURIComponent(r);
  const K = () => window.KPC;

  let PLACE = new URLSearchParams(location.search).get('where') || store.get('kpcRarePlace', 'US-KY');
  let P = [], f = '25', reg = '', map = null, layer = null, ME = null, HIDE = store.get('kpcRareHide', false);
  const mine = () => store.get('kpcTrackActs', {});

  const LISTS = {};
  const usIndex = () => LISTS.us || (LISTS.us = j('data/parkinfo/index.json').then(d => d.rows));
  const canada = () => LISTS.ca || (LISTS.ca = j('data/parkinfo/CA.json').then(d => Object.entries(d.parks).map(([r, v]) => ({ c: r, n: v[0], sub: v[10] || '', la: v[5], lo: v[6], t: v[2], acts: v[7] }))));
  /* one place → [{c, n, la, lo, t, acts, q?, last?, reg?}] */
  async function load(force) {
    const pr = $('prog'), sm = pr.querySelector('small');
    if (PLACE === 'US-KY') {
      const D = await K().data(); let H;
      try { H = (await K().history(K().progressUI(pr), force)).hist; } catch (e) { sm.textContent = 'Could not reach POTA right now: try again in a minute.'; throw e; }
      $('reg').innerHTML = '<option value="">All Kentucky</option>'; Object.values(D.regions).filter((v, i, a) => a.indexOf(v) === i).sort().forEach(r => $('reg').add(new Option(r, r)));
      return D.parks.map(p => { const a = H[p.c] || []; return { c: p.c, n: p.n, la: p.la, lo: p.lo, t: p.t, co: p.co, off: p.off, acts: a.filter(x => K().ok(x[2])).length, q: a.reduce((s, x) => s + x[2], 0), last: a.map(x => x[1]).sort().pop() || '', reg: D.regions[String(p.co || '').split('/')[0].trim().toUpperCase()] || '' }; });
    }
    pr.classList.add('on'); sm.textContent = 'Loading ' + placeName(PLACE) + '…';
    let L = [];
    if (/^US-/.test(PLACE)) { const s = PLACE.slice(3); L = (await usIndex()).filter(r => r[2] === s).map(r => ({ c: r[0], n: r[1], la: r[3], lo: r[4], acts: r[6] })); }
    else if (/^CA-/.test(PLACE)) { const s = PLACE.slice(3); L = (await canada()).filter(r => r.sub === s); }
    else L = Object.entries((await j('data/parkinfo/' + PLACE + '.json')).parks).map(([r, v]) => ({ c: r, n: v[0], la: v[5], lo: v[6], t: v[2], acts: v[7] }));
    pr.classList.remove('on'); sm.textContent = '';
    return L;
  }
  async function go(force) {
    store.set('kpcRarePlace', PLACE);
    const u = new URL(location.href); u.searchParams.set('where', PLACE); history.replaceState(null, '', u);
    const ky = PLACE === 'US-KY';
    $('regW').hidden = !ky; $('refresh').hidden = !ky; $('qsoH').hidden = !ky; reg = '';
    $('srcNote').textContent = ky ? 'Kentucky: POTA\'s public records read live (activations with 10+ QSOs; "Last" = the most recent activation of any kind), saved in your browser for 12 hours.' : placeName(PLACE) + ': activation counts from POTA, refreshed every night by the club\'s bots.';
    $('stats').innerHTML = '<div class="stat"><b>…</b><span>LOADING</span></div>'; $('tbody').innerHTML = '';
    try { P = await load(force); } catch (e) { $('stats').innerHTML = ''; $('tbody').innerHTML = '<tr><td colspan="4" class="muted">Could not load the park list for ' + esc(placeName(PLACE)) + '.</td></tr>'; return; }
    const known = P.filter(p => p.acts != null), never = known.filter(p => p.acts === 0).length, u5 = known.filter(p => p.acts <= 5).length, tot = known.reduce((s, p) => s + p.acts, 0);
    $('stats').innerHTML = `<div class="stat"><b>${never.toLocaleString()}</b><span>NEVER ACTIVATED</span></div><div class="stat"><b>${u5.toLocaleString()}</b><span>5 OR FEWER</span></div><div class="stat"><b>${P.length.toLocaleString()}</b><span>PARKS IN ${esc(placeName(PLACE).toUpperCase())}</span></div><div class="stat"><b>${tot.toLocaleString()}</b><span>ACTIVATIONS IN ALL</span></div>`;
    if (map) map._k = '';
    draw();
  }
  function draw() {
    const M = mine(), hasMine = Object.keys(M).length;
    $('hideW').hidden = !hasMine; $('hide').checked = HIDE && hasMine;
    let L = P.filter(p => (!reg || p.reg === reg) && !(HIDE && hasMine && M[p.c]));
    if (ME) L.forEach(p => { p.d = p.la != null ? km(ME[0], ME[1], p.la, p.lo) : 1e9; });
    L.sort(f === 'near' ? (a, b) => a.d - b.d : (a, b) => ((a.acts == null ? 1e9 : a.acts) - (b.acts == null ? 1e9 : b.acts)) || ((a.q || 0) - (b.q || 0)) || a.c.localeCompare(b.c, undefined, { numeric: true }));
    const show = f === 'all' ? L : f === '0' ? L.filter(p => p.acts === 0) : f === 'near' ? L.filter(p => p.d < 160).slice(0, 40) : L.slice(0, 25);
    const big = new Set(show.map(p => p.c));
    if (window.L) {
      if (!map) { map = window.L.map('map', { preferCanvas: true, worldCopyJump: true }); window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18, attribution: '© OpenStreetMap' }).addTo(map); }
      if (layer) layer.remove(); layer = window.L.layerGroup().addTo(map);
      const pts = [];
      L.forEach(p => { if (p.la == null) return; pts.push([p.la, p.lo]); const on = big.has(p.c);
        window.L.circleMarker([p.la, p.lo], { radius: on ? 8 : 4, weight: 1, color: '#222', fillColor: col(p.acts), fillOpacity: on ? .95 : .45 })
          .bindPopup(`<b>${esc(p.n)}</b><br><a class="ref" href="${potaUrl(p.c)}" target="_blank" rel="noopener">${esc(p.c)}</a>${p.co ? ' · ' + esc(p.co) + ' Co.' : ''}<br><b>${p.acts == null ? '?' : p.acts}</b> activations${p.q != null ? ' · ' + p.q + ' QSOs' : ''}${p.last ? '<br>Last: ' + esc(K() && K().fmtDate ? K().fmtDate(p.last) : p.last) : ''}${M[p.c] ? '<br>✅ You activated it' : ''}<br><a href="https://www.google.com/maps/dir/?api=1&destination=${p.la},${p.lo}" target="_blank" rel="noopener">Directions</a> · <a href="kpc-kit.html?ref=${encodeURIComponent(p.c)}">Activation Kit</a>`).addTo(layer); });
      if (ME && f === 'near') window.L.circleMarker(ME, { radius: 7, color: '#1a5fb4', fillColor: '#3584e4', fillOpacity: 1 }).bindPopup('You').addTo(layer);
      const fit = f === 'near' && show.length ? show.map(p => [p.la, p.lo]).concat([ME]) : pts;
      if (fit.length && map._k !== PLACE + f) { map.fitBounds(fit, { padding: [16, 16], maxZoom: 10 }); map._k = PLACE + f; }
    }
    $('tbody').innerHTML = show.map(p => `<tr><td><a class="ref" href="${potaUrl(p.c)}" target="_blank" rel="noopener">${esc(p.c)}</a> ${p.acts === 0 ? '<span class="tag r">NEVER</span>' : ''}${M[p.c] ? ' <span class="tag gr">MINE</span>' : ''}<br>${esc(p.n)}${p.t || p.co ? `<br><span class="muted" style="font-size:12px">${esc([p.co ? p.co + ' Co.' : '', p.t].filter(Boolean).join(' • '))}</span>` : ''}</td><td><b>${p.acts == null ? '?' : p.acts}</b></td><td class="hide-m"${PLACE === 'US-KY' ? '' : ' hidden'}>${p.q != null ? p.q : ''}</td><td style="font-size:12px">${f === 'near' && p.d < 1e8 ? Math.round(p.d / 1.609) + ' mi' : p.last ? esc(K() && K().fmtDate ? K().fmtDate(p.last) : p.last) : '—'}</td></tr>`).join('') || `<tr><td colspan="4" class="muted">${f === 'near' ? 'No parks here within 100 miles of you. Pick the state you are in.' : 'No parks match.'}</td></tr>`;
    $('lastH').textContent = f === 'near' ? 'DISTANCE' : 'LAST';
  }
  function fillPicker() {
    const us = Object.keys(ST).map(s => ['US-' + s, ST[s]]).sort((a, b) => a[1].localeCompare(b[1]));
    const ca = Object.keys(PROV).map(s => ['CA-' + s, PROV[s]]).sort((a, b) => a[1].localeCompare(b[1]));
    const w = PARKINFO.map(p => [p, country(p)]).sort((a, b) => a[1].localeCompare(b[1]));
    const o = L => L.map(([k, n]) => `<option value="${k}"${k === PLACE ? ' selected' : ''}>${esc(n)}</option>`).join('');
    $('place').innerHTML = `<optgroup label="United States">${o(us)}</optgroup><optgroup label="Canada">${o(ca)}</optgroup><optgroup label="Other countries">${o(w)}</optgroup>`;
  }
  function near() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(pos => { ME = [pos.coords.latitude, pos.coords.longitude]; f = 'near'; [...$('flt').children].forEach(x => x.setAttribute('aria-pressed', x.dataset.f === 'near')); draw(); },
      () => { $('prog').classList.add('on'); $('prog').querySelector('small').textContent = 'Could not get your location (allow it in the browser settings).'; }, { timeout: 15000, maximumAge: 300000 });
  }
  function init() {
    if (!$('place')) return;
    fillPicker();
    $('place').onchange = () => { PLACE = $('place').value; f = f === 'near' ? 'near' : f; go(); };
    $('flt').onclick = e => { const b = e.target.closest('button'); if (!b) return; if (b.dataset.f === 'near') return near(); f = b.dataset.f; [...$('flt').children].forEach(x => x.setAttribute('aria-pressed', x === b)); draw(); };
    $('reg').onchange = e => { reg = e.target.value; draw(); };
    $('refresh').onclick = () => go(true);
    $('hide').onchange = () => { HIDE = $('hide').checked; store.set('kpcRareHide', HIDE); draw(); };
    go();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
