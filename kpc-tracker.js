/* KPC PARK TRACKER, EVERYWHERE (Opus Oct 24 2026; Activators Lounge step 2. Brandon: one tracker with a picker, all states,
   Canada and the world; no leaderboards, no club calls; 'my stats … does allow a download csv').
   Where the activations come from:
   - YOUR FILE: pota.app → My Stats → download the CSV (any country), or an ADIF activator log (MY_SIG_INFO / MY_POTA_REF,
     10+ contacts on one UTC day = one activation). Kept on this device only (localStorage kpcTrackActs).
   - KENTUCKY, no file needed: type a call sign and POTA's public records for every KY park are read (KPC.history in kpc-tools.js).
   The park lists: data/parkinfo/index.json (every US park outside KY: [ref, name, state, lat, lon, typeIx, activations]),
   kpc-ky-data.json (KY), data/parkinfo/CA.json (Canada, province in field 10), data/parkinfo/<PFX>.json (64 countries),
   data/pota/index.json (park counts for every POTA program, for the EVERYWHERE totals). All kept fresh by the nightly bots. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const store = { get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  /* Storage plan Step B (Oct 27): data/parkinfo and data/pota now live on KentuckyPortableClub/KPC-Data. */
  const j = (u, ms) => { const c = new AbortController(), t = setTimeout(() => c.abort(), ms || 30000);
    const f = (/^(data\/parkinfo\/|data\/pota\/)/.test(u) && window.KPC && typeof KPC.dataUrl === 'function') ? KPC.dataUrl(u, { signal: c.signal }) : fetch(u, { signal: c.signal });
    return f.then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }).finally(() => clearTimeout(t)); };
  const ST = { AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California', CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', DC: 'District of Columbia', FL: 'Florida', GA: 'Georgia', HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa', KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland', MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri', MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York', NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VT: 'Vermont', VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming' };
  const PROV = { AB: 'Alberta', BC: 'British Columbia', MB: 'Manitoba', NB: 'New Brunswick', NL: 'Newfoundland and Labrador', NS: 'Nova Scotia', NT: 'Northwest Territories', NU: 'Nunavut', ON: 'Ontario', PE: 'Prince Edward Island', QC: 'Quebec', SK: 'Saskatchewan', YT: 'Yukon' };
  let DN = null; try { DN = new Intl.DisplayNames(['en'], { type: 'region' }); } catch (e) {}
  const country = p => { try { const n = DN && DN.of(p); if (n && n !== p) return n; } catch (e) {} return p; };
  const placeName = k => /^US-/.test(k) ? ST[k.slice(3)] || k : /^CA-/.test(k) ? PROV[k.slice(3)] || k : country(k);
  const PARKINFO = ['AG', 'AI', 'AT', 'AU', 'AW', 'BB', 'BE', 'BL', 'BM', 'BQ', 'BS', 'BZ', 'CH', 'CR', 'CU', 'CW', 'CZ', 'DE', 'DK', 'DM', 'DO', 'EE', 'ES', 'FI', 'FR', 'GB', 'GD', 'GL', 'GP', 'GT', 'HN', 'HR', 'HT', 'HU', 'IE', 'IT', 'JM', 'JP', 'KN', 'KY', 'LC', 'LT', 'LU', 'LV', 'MF', 'MQ', 'MS', 'MX', 'NI', 'NL', 'NO', 'PA', 'PL', 'PM', 'PT', 'RO', 'SE', 'SI', 'SK', 'SV', 'SX', 'TC', 'TT', 'VC', 'VG'];

  /* ---------------- my activations ---------------- */
  let ACTS = store.get('kpcTrackActs', {});          /* ref → {n, first, src} */
  let FILEINFO = store.get('kpcTrackFile', null);     /* {name, when, parks} */
  const saveActs = () => store.set('kpcTrackActs', ACTS);
  const REF = /\b(?:[A-Z0-9]{1,3}-\d{4,5}|K-\d{4})\b/g;
  const normRef = r => { r = r.toUpperCase(); if (/^K-\d{4}$/.test(r)) r = 'US-' + r.slice(2); const m = r.match(/^([A-Z0-9]{1,3})-(\d+)$/); return m ? m[1] + '-' + m[2].padStart(4, '0') : r; };
  function cells(line) { const c = []; let cur = '', q = false; for (let i = 0; i < line.length; i++) { const ch = line[i]; if (q) { if (ch === '"') { if (line[i + 1] === '"') { cur += '"'; i++; } else q = false; } else cur += ch; } else if (ch === '"') q = true; else if (ch === ',' || ch === ';' || ch === '\t') { c.push(cur.trim()); cur = ''; } else cur += ch; } c.push(cur.trim()); return c; }
  function parse(txt) {
    const out = {};
    if (/<eor>/i.test(txt)) {      /* ADIF activator log: my park on each contact, 10 on one UTC day = an activation */
      const day = {};
      for (const rec of txt.replace(/^[\s\S]*?<eoh>/i, '').split(/<eor>/i)) {
        const f = {}, re = /<([A-Za-z0-9_]+):(\d+)(?::[^>]*)?>/g; let m;
        while ((m = re.exec(rec))) { f[m[1].toUpperCase()] = rec.substr(re.lastIndex, +m[2]); re.lastIndex += +m[2]; }
        const src = f.MY_POTA_REF || ((f.MY_SIG || '').toUpperCase() === 'POTA' ? f.MY_SIG_INFO : '') || '';
        (String(src).toUpperCase().match(REF) || []).forEach(r => { r = normRef(r); const k = r + '|' + (f.QSO_DATE || ''); day[k] = (day[k] || 0) + 1; });
      }
      Object.entries(day).forEach(([k, n]) => { if (n < 10) return; const [r, d] = k.split('|'); const x = out[r] || (out[r] = { n: 0, first: '' }); x.n++; if (d && (!x.first || d < x.first)) x.first = d; });
      return out;
    }
    const lines = txt.split(/\r?\n/).filter(l => l.trim());
    const head = lines.length ? cells(lines[0]).map(h => h.toLowerCase()) : [];
    const ci = re => head.findIndex(h => re.test(h));
    const cA = ci(/^activations?$|^# ?activations?$/), cF = ci(/first/), cR = ci(/reference|^park$|^ref$/), cL = ci(/^hasc$/) >= 0 ? ci(/^hasc$/) : ci(/^location$/);
    if (cA < 0 && ci(/^qsos$/) >= 0 && ci(/attempts/) < 0 && cR >= 0) return { hunter: true };   /* hunter_parks.csv: no Activations column */
    for (const line of lines.slice(cA >= 0 || cR >= 0 ? 1 : 0)) {
      const c = cells(line), refs = cR >= 0 ? String(c[cR] || '').toUpperCase().match(REF) || [] : line.toUpperCase().match(REF) || [];
      if (!refs.length) continue;
      const n = cA >= 0 ? parseInt(c[cA], 10) : 1;
      if (cA >= 0 && !(n > 0)) continue;                 /* attempts only: not activated */
      refs.slice(0, cR >= 0 ? 9 : 1).forEach(r => { r = normRef(r); const x = out[r] || (out[r] = { n: 0, first: '' }); x.n = Math.max(x.n, isFinite(n) ? n : 1); if (cF >= 0 && c[cF]) x.first = String(c[cF]).slice(0, 10); const lc = cL >= 0 ? String(c[cL] || '').toUpperCase().match(/^(US|CA)-([A-Z]{2})$/) : null; if (lc) x.loc = lc[0]; });
    }
    return out;
  }
  async function takeFile(f) {
    const msg = $('trMsg'); msg.textContent = 'Reading ' + f.name + '…';
    try {
      const out = parse(await f.text());
      if (out.hunter) { msg.textContent = 'That is your HUNTER file (parks you worked). The tracker needs the ACTIVATOR one: activator_parks.csv.'; return; }
      const n = Object.keys(out).length;
      if (!n) { msg.textContent = 'No park numbers (like US-1234) found in that file. Use the CSV from pota.app → My Stats, or an ADIF activator log.'; return; }
      Object.keys(ACTS).forEach(r => { if (ACTS[r].src === 'file') delete ACTS[r]; });
      Object.entries(out).forEach(([r, x]) => { ACTS[r] = Object.assign({}, x, { src: 'file' }); });
      saveActs(); FILEINFO = { name: f.name, when: Date.now(), parks: n }; store.set('kpcTrackFile', FILEINFO);
      msg.textContent = '✅ ' + n.toLocaleString() + ' activated park' + (n > 1 ? 's' : '') + ' read from ' + f.name + '. Saved on this device.';
      draw();
    } catch (e) { msg.textContent = 'Could not read that file (' + e.message + ').'; }
  }
  /* Kentucky with no file: POTA's public records for every KY park (the old tracker's way) */
  async function kyLookup(call) {
    const K = window.KPC; if (!K || !K.history) { $('trMsg').textContent = 'The Kentucky lookup did not load. Refresh and try again.'; return; }
    call = K.base(call); if (!call) return; store.set('kpcMyCall', call);
    $('trMsg').textContent = 'Reading POTA\'s records for every Kentucky park…';
    try {
      const H = (await K.history(K.progressUI($('trProg')))).hist;
      Object.keys(ACTS).forEach(r => { if (ACTS[r].src === 'ky') delete ACTS[r]; });
      let n = 0;
      Object.entries(H).forEach(([r, L]) => { const a = L.filter(x => K.base(x[0]) === call && K.ok(x[2])); if (!a.length) return; n++; if (ACTS[r] && ACTS[r].src === 'file') return; ACTS[r] = { n: a.length, first: a.map(x => x[1]).sort()[0], src: 'ky' }; });
      saveActs(); $('trMsg').textContent = '✅ ' + call + ': ' + n + ' Kentucky park' + (n === 1 ? '' : 's') + ' activated (POTA\'s public records).'; draw();
    } catch (e) { $('trMsg').textContent = 'Could not reach POTA right now. Try again in a minute.'; }
  }

  /* ---------------- park lists ---------------- */
  const LISTS = {};
  async function usIndex() { return LISTS.us || (LISTS.us = j('data/parkinfo/index.json').then(d => d.rows)); }
  async function ky() { return LISTS.ky || (LISTS.ky = j('kpc-ky-data.json').then(d => d.parks.map(p => [p.c, p.n, 'KY', p.la, p.lo, p.t, p.acc]))); }
  async function canada() { return LISTS.ca || (LISTS.ca = j('data/parkinfo/CA.json').then(d => Object.entries(d.parks).map(([r, v]) => [r, v[0], v[10] || '', v[5], v[6], v[2], v[7]]))); }
  async function countryList(p) { return LISTS[p] || (LISTS[p] = j('data/parkinfo/' + p + '.json').then(d => Object.entries(d.parks).map(([r, v]) => [r, v[0], v[10] || '', v[5], v[6], v[2], v[7]]))); }
  /* one place's parks: [ref, name, sub, lat, lon, type, activations by anyone] */
  async function parksOf(k) {
    if (k === 'US-KY') return ky();
    if (/^US-/.test(k)) { const s = k.slice(3); return (await usIndex()).filter(r => r[2] === s); }
    if (/^CA-/.test(k)) { const s = k.slice(3); return (await canada()).filter(r => r[2] === s); }
    if (PARKINFO.includes(k)) return countryList(k);
    return null;
  }

  /* ---------------- the picker ---------------- */
  let PLACE = new URLSearchParams(location.search).get('where') || store.get('kpcTrackPlace', 'US-KY');
  let TOT = null;   /* data/pota/index.json programs counts */
  function fillPicker() {
    const us = Object.keys(ST).map(s => ['US-' + s, ST[s]]).sort((a, b) => a[1].localeCompare(b[1]));
    const ca = Object.keys(PROV).map(s => ['CA-' + s, PROV[s]]).sort((a, b) => a[1].localeCompare(b[1]));
    const w = PARKINFO.map(p => [p, country(p)]).sort((a, b) => a[1].localeCompare(b[1]));
    const o = (L) => L.map(([k, n]) => `<option value="${k}"${k === PLACE ? ' selected' : ''}>${esc(n)}</option>`).join('');
    $('trPlace').innerHTML = `<option value="ALL"${PLACE === 'ALL' ? ' selected' : ''}>🌎 Everywhere (my totals)</option><optgroup label="United States">${o(us)}</optgroup><optgroup label="Canada">${o(ca)}</optgroup><optgroup label="Other countries">${o(w)}</optgroup>`;
  }

  /* ---------------- drawing ---------------- */
  let map = null, layer = null, tab = 'done', page = 1;
  const fmt = d => { d = String(d || '').replace(/-/g, ''); return /^\d{8}$/.test(d) ? new Date(d.slice(0, 4) + '-' + d.slice(4, 6) + '-' + d.slice(6, 8) + 'T12:00:00Z').toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : esc(d); };
  const potaUrl = r => 'https://pota.app/#/park/' + encodeURIComponent(r);
  /* Brandon Oct 24: 'need reminders to update files' — after 30 days the file gets a gold 'time for a fresh one' line */
  const ageDays = () => FILEINFO && FILEINFO.when ? Math.floor((Date.now() - FILEINFO.when) / 86400000) : null;
  function remind() { const a = ageDays(), el = $('trOld'); if (!el) return; el.hidden = !(a != null && a >= 30); if (!el.hidden) el.innerHTML = '⏰ Your POTA file is <b>' + a + ' days old</b>. Parks you activated since then are missing: download a fresh <b>activator_parks.csv</b> (steps above) and pick it again.'; }
  function src() { remind(); const n = Object.keys(ACTS).length; $('trSrc').innerHTML = n ? `<b>${n.toLocaleString()}</b> activated park${n > 1 ? 's' : ''} on this device${FILEINFO ? ' · file: ' + esc(FILEINFO.name) + ' (' + new Date(FILEINFO.when).toLocaleDateString() + ')' : ''} · <button type="button" class="tr-link" id="trClear">clear them</button>` : 'Nothing loaded yet: load your POTA file, or type a call sign for Kentucky.'; const c = $('trClear'); if (c) c.onclick = () => { if (!confirm('Take every activated park off this device?')) return; ACTS = {}; FILEINFO = null; saveActs(); store.set('kpcTrackFile', null); draw(); }; }
  async function draw() {
    src(); store.set('kpcTrackPlace', PLACE);
    const u = new URL(location.href); u.searchParams.set('where', PLACE); history.replaceState(null, '', u);
    $('trKy').hidden = PLACE !== 'US-KY';
    if (PLACE === 'ALL') return drawAll();
    $('trAll').hidden = true; $('trOne').hidden = false;
    $('trStats').innerHTML = '<div class="stat"><b>…</b><span>LOADING</span></div>';
    let L = null; try { L = await parksOf(PLACE); } catch (e) {}
    if (!L) { $('trStats').innerHTML = ''; $('trList').innerHTML = '<p class="muted">We don\'t have the park list for ' + esc(placeName(PLACE)) + ' yet.</p>'; return; }
    const done = L.filter(r => ACTS[r[0]]), need = L.filter(r => !ACTS[r[0]]), atno = need.filter(r => !r[6]).length;
    $('trStats').innerHTML = `<div class="stat"><b>${done.length}</b><span>OF ${L.length.toLocaleString()} PARKS</span></div><div class="stat"><b>${need.length.toLocaleString()}</b><span>STILL TO GO</span></div><div class="stat"><b>${L.length ? Math.round(100 * done.length / L.length) : 0}%</b><span>${esc(placeName(PLACE).toUpperCase())}</span></div><div class="stat"><b>${atno.toLocaleString()}</b><span>NEVER ACTIVATED BY ANYONE</span></div>`;
    $('trBar').style.width = (L.length ? 100 * done.length / L.length : 0) + '%';
    drawMap(L); drawList(L);
  }
  function drawMap(L) {
    if (!window.L) { $('trMap').innerHTML = '<p class="muted" style="padding:16px">The map could not load.</p>'; return; }
    if (!map) { map = window.L.map('trMap', { preferCanvas: true, worldCopyJump: true }); window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18, attribution: '© OpenStreetMap' }).addTo(map); }
    if (layer) layer.remove(); layer = window.L.layerGroup().addTo(map);
    const pts = [];
    L.forEach(r => { if (r[3] == null) return; const d = ACTS[r[0]]; pts.push([r[3], r[4]]);
      window.L.circleMarker([r[3], r[4]], { radius: d ? 6 : 4, weight: 1, color: '#173a28', fillColor: d ? '#1d5a3a' : r[6] ? '#ffffff' : '#d5a63a', fillOpacity: .95 })
        .bindPopup(`<b>${esc(r[1])}</b><br><a href="${potaUrl(r[0])}" target="_blank" rel="noopener">${esc(r[0])}</a><br>${d ? '✅ Activated' + (d.n > 1 ? ' ' + d.n + '×' : '') + (d.first ? ' · first ' + fmt(d.first) : '') : r[6] ? 'Not yet by you · ' + r[6] + ' activations by others' : '⭐ Never activated by anyone'}<br><a href="kpc-kit.html?ref=${encodeURIComponent(r[0])}">Activation Kit ›</a>`).addTo(layer); });
    if (pts.length && map._k !== PLACE) { map.fitBounds(pts, { padding: [16, 16], maxZoom: 9 }); map._k = PLACE; }
    setTimeout(() => map.invalidateSize(), 50);
  }
  function drawList(L) {
    [...$('trTabs').children].forEach(b => b.setAttribute('aria-pressed', b.dataset.t === tab));
    let rows = tab === 'done' ? L.filter(r => ACTS[r[0]]).sort((a, b) => String(ACTS[a[0]].first || '9').localeCompare(String(ACTS[b[0]].first || '9')) || a[0].localeCompare(b[0], undefined, { numeric: true }))
      : L.filter(r => !ACTS[r[0]]).sort((a, b) => ((a[6] || 0) - (b[6] || 0)) || a[0].localeCompare(b[0], undefined, { numeric: true }));
    const shown = rows.slice(0, page * 100);
    $('trList').innerHTML = shown.length ? '<div class="tablewrap"><table class="list"><thead><tr><th>PARK</th><th>' + (tab === 'done' ? 'FIRST' : 'ACTIVATIONS BY ANYONE') + '</th></tr></thead><tbody>' + shown.map(r => `<tr><td><a class="ref" href="${potaUrl(r[0])}" target="_blank" rel="noopener">${esc(r[0])}</a><br>${esc(r[1])}</td><td>${tab === 'done' ? (ACTS[r[0]].first ? fmt(ACTS[r[0]].first) : '✅') : (r[6] ? r[6] : '⭐ none yet')}</td></tr>`).join('') + '</tbody></table></div>' + (rows.length > shown.length ? `<button type="button" class="btn sm alt" id="trMore" style="margin-top:10px">SHOW ${Math.min(100, rows.length - shown.length)} MORE (${(rows.length - shown.length).toLocaleString()} left)</button>` : '')
      : `<p class="muted">${tab === 'done' ? (Object.keys(ACTS).length ? 'None activated here yet.' : 'Load your POTA file above to see the parks you have activated.') : 'Every park here activated. Well done!'}</p>`;
    const m = $('trMore'); if (m) m.onclick = () => { page++; drawList(L); };
    drawList.L = L;
  }
  /* EVERYWHERE: my totals by state / province / country */
  async function drawAll() {
    $('trOne').hidden = true; $('trAll').hidden = false;
    const refs = Object.keys(ACTS);
    if (!refs.length) { $('trAll').innerHTML = '<p class="muted">Load your POTA file above and your totals for every state, province and country show here.</p>'; return; }
    $('trAll').innerHTML = '<p class="muted">Adding it up…</p>';
    const by = {}, add = (k, r) => { (by[k] = by[k] || []).push(r); };
    const needUs = refs.some(r => /^US-/.test(r)), needCa = refs.some(r => /^CA-/.test(r));
    const [U, K, C] = await Promise.all([needUs ? usIndex().catch(() => []) : [], needUs ? ky().catch(() => []) : [], needCa ? canada().catch(() => []) : []]);
    const us = {}; U.concat(K).forEach(r => { us[r[0]] = r[2]; }); const ca = {}; C.forEach(r => { ca[r[0]] = r[2]; });
    const usTot = {}; U.concat(K).forEach(r => { usTot[r[2]] = (usTot[r[2]] || 0) + 1; }); const caTot = {}; C.forEach(r => { caTot[r[2]] = (caTot[r[2]] || 0) + 1; });
    if (!TOT) TOT = await j('data/pota/index.json').then(d => d.programs || {}).catch(() => ({}));
    refs.forEach(r => { const p = r.split('-')[0], lc = ACTS[r].loc; if (lc && lc.slice(0, 2) === p) add(lc, r); else if (p === 'US') add(us[r] ? 'US-' + us[r] : 'US-?', r); else if (p === 'CA') add(ca[r] ? 'CA-' + ca[r] : 'CA-?', r); else add(p, r); });
    const rows = Object.entries(by).map(([k, L]) => { const tot = /^US-/.test(k) ? usTot[k.slice(3)] : /^CA-/.test(k) ? caTot[k.slice(3)] : TOT[k]; return { k, n: L.length, tot: tot || 0 }; }).sort((a, b) => b.n - a.n);
    const places = rows.filter(r => !/\?$/.test(r.k)).length, states = rows.filter(r => /^US-[A-Z]{2}$/.test(r.k)).length, countries = new Set(rows.map(r => r.k.split('-')[0])).size;
    $('trAll').innerHTML = `<div class="stats"><div class="stat"><b>${refs.length.toLocaleString()}</b><span>PARKS ACTIVATED</span></div><div class="stat"><b>${states}</b><span>US STATES</span></div><div class="stat"><b>${countries}</b><span>COUNTRIES</span></div><div class="stat"><b>${places}</b><span>STATES, PROVINCES &amp; COUNTRIES</span></div></div>
      <div class="tablewrap" style="margin-top:14px"><table class="list"><thead><tr><th>WHERE</th><th>ACTIVATED</th><th>OF</th></tr></thead><tbody>${rows.map(r => `<tr><td>${/\?$/.test(r.k) ? esc(r.k.slice(0, 2)) + ' (place not known)' : `<button type="button" class="tr-link" data-go="${esc(r.k)}">${esc(placeName(r.k))}</button>`}</td><td><b>${r.n}</b></td><td>${r.tot ? r.tot.toLocaleString() + ' (' + Math.round(100 * r.n / r.tot) + '%)' : '—'}</td></tr>`).join('')}</tbody></table></div>`;
    $('trAll').querySelectorAll('[data-go]').forEach(b => { b.onclick = () => { PLACE = b.dataset.go; fillPicker(); tab = 'done'; page = 1; draw(); window.scrollTo({ top: $('trPlace').getBoundingClientRect().top + scrollY - 80, behavior: 'smooth' }); }; });
  }

  function init() {
    if (!$('trPlace')) return;
    fillPicker();
    $('trPlace').onchange = () => { PLACE = $('trPlace').value; tab = 'done'; page = 1; draw(); };
    $('trFile').onchange = e => { const f = e.target.files[0]; if (f) takeFile(f); e.target.value = ''; };
    $('trKyF').onsubmit = e => { e.preventDefault(); kyLookup($('trCall').value); };
    $('trCall').value = new URLSearchParams(location.search).get('call') || store.get('kpcMyCall', '') || '';
    $('trTabs').onclick = e => { const b = e.target.closest('[data-t]'); if (!b) return; tab = b.dataset.t; page = 1; if (drawList.L) drawList(drawList.L); };
    draw();
    const c = new URLSearchParams(location.search).get('call'); if (c && PLACE === 'US-KY') kyLookup(c);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
  window.KPCTracker = { parse, ACTS: () => ACTS };
})();
