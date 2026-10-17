/* KPC Activator Logger (kpc-logger.html, members room). Oct 16 2026.
   Log a POTA activation in the browser: tap a live POTA spot to fill the form, call sign lookup (callook.info for US calls,
   HamDB for the rest; both public FCC/agency data, CORS *), QSO map, rates per hour, notes that can ride on every contact,
   a self-spot to api.pota.app (same spam guard as Spot Me: kpcSpotMeSent), and POTA's one-file-per-park ADIF export.
   The log is saved on every change to localStorage kpcLogger AND IndexedDB kpc-logger/kv/'log' (newer wins on load). */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const get = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const put = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } };
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const BANDS = [['160m', 1800, 2000], ['80m', 3500, 4000], ['60m', 5330, 5410], ['40m', 7000, 7300], ['30m', 10100, 10150], ['20m', 14000, 14350], ['17m', 18068, 18168], ['15m', 21000, 21450], ['12m', 24890, 24990], ['10m', 28000, 29700], ['6m', 50000, 54000], ['2m', 144000, 148000], ['1.25m', 222000, 225000], ['70cm', 420000, 450000]];
  const BCOL = { '160m': '#a78bfa', '80m': '#f472b6', '60m': '#fb7185', '40m': '#f59e0b', '30m': '#facc15', '20m': '#45e08f', '17m': '#2dd4bf', '15m': '#38bdf8', '12m': '#60a5fa', '10m': '#818cf8', '6m': '#e879f9', '2m': '#f97316', '1.25m': '#fbbf24', '70cm': '#ef4444' };
  const bandOf = k => { for (const [b, a, z] of BANDS) if (k >= a && k <= z) return b; return ''; };
  const kHzOf = v => { v = parseFloat(String(v || '').replace(',', '.')); if (!v) return 0; return v > 1000 ? v : v * 1000; };
  const mhz = k => k ? (k / 1000).toFixed(k % 1 ? 4 : 3).replace(/0+$/, '').replace(/\.$/, '') : '';
  const PHONE = /^(SSB|USB|LSB|FM|AM)$/, CWISH = /^(CW|RTTY|PSK31)$/, DIGI = /^(FT8|FT4|JS8)$/;
  const rstDef = m => PHONE.test(m) ? '59' : CWISH.test(m) ? '599' : '';
  const REF = /^[A-Z0-9]{1,4}-\d{4,5}$/;
  const nref = r => { r = String(r || '').trim().toUpperCase().replace(/^K-/, 'US-'); if (/^\d{3,5}$/.test(r)) r = 'US-' + r; const m = r.match(/^([A-Z0-9]{1,4})-(\d{1,5})$/); return m ? m[1] + '-' + m[2].padStart(4, '0') : r; };
  const refsOf = s => [...new Set(String(s || '').toUpperCase().split(/[\s,;+&]+/).map(nref).filter(r => REF.test(r)))];
  const base = c => { c = String(c || '').toUpperCase().trim(); const p = c.split('/'); return p.length > 1 ? p.reduce((a, b) => (b.length > a.length ? b : a)) : c; };
  const okCall = c => /^[A-Z0-9/]{3,14}$/.test(c) && /\d/.test(c) && /[A-Z]/.test(c);
  const iso = d => d.toISOString();
  const ymd = d => iso(d).slice(0, 10).replace(/-/g, '');
  const fD = d => d ? d.slice(0, 4) + '-' + d.slice(4, 6) + '-' + d.slice(6, 8) : '';
  const fT = t => t ? t.slice(0, 2) + ':' + t.slice(2, 4) : '';
  const tsOf = q => Date.UTC(+q.d.slice(0, 4), +q.d.slice(4, 6) - 1, +q.d.slice(6, 8), +q.tm.slice(0, 2), +q.tm.slice(2, 4));
  let tT;
  function toast(msg, undo) {
    const t = $('lgToast'); t.innerHTML = esc(msg) + (undo ? '<button type="button">UNDO</button>' : ''); t.hidden = false;
    if (undo) t.querySelector('button').onclick = () => { undo(); t.hidden = true; };
    clearTimeout(tT); tT = setTimeout(() => { t.hidden = true; }, undo ? 7000 : 3500);
  }
  /* grid squares */
  function toGrid(la, lo) {
    lo += 180; la += 90; const A = 'ABCDEFGHIJKLMNOPQRSTUVWX';
    return A[Math.floor(lo / 20)] + A[Math.floor(la / 10)] + Math.floor(lo % 20 / 2) + Math.floor(la % 10) + A[Math.floor(lo % 2 * 12)].toLowerCase() + A[Math.floor(la % 1 * 24)].toLowerCase();
  }
  function fromGrid(g) {
    g = String(g || '').trim(); if (!/^[A-R]{2}\d{2}([A-X]{2})?/i.test(g)) return null; g = g.toUpperCase();
    let lo = (g.charCodeAt(0) - 65) * 20 - 180 + (+g[2]) * 2, la = (g.charCodeAt(1) - 65) * 10 - 90 + (+g[3]);
    if (g.length >= 6) { lo += (g.charCodeAt(4) - 65) / 12 + 1 / 24; la += (g.charCodeAt(5) - 65) / 24 + 1 / 48; } else { lo += 1; la += .5; }
    return [la, lo];
  }
  const miles = (a, b) => { const R = 3958.8, r = Math.PI / 180, dl = (b[0] - a[0]) * r, dn = (b[1] - a[1]) * r, x = Math.sin(dl / 2) ** 2 + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dn / 2) ** 2; return 2 * R * Math.asin(Math.sqrt(x)); };

  /* ---------------- settings + log storage ---------------- */
  const SET = Object.assign({ call: get('kpcMyCall', '') || '', park: '', grid: '', pwr: '', stamp: false, carry: false, notes: '', act: 0, pinfo: {}, me: null, ops: '', op: '', share: false }, get('kpcLgSet', {}));
  const saveSet = () => put('kpcLgSet', SET);
  const LK = 'kpcLogger';
  let L = get(LK, null); if (!L || !Array.isArray(L.q)) L = { v: 1, u: 0, q: [] };
  let IDB = null, IDBok = false, PERSIST = null;
  const idb = () => IDB || (IDB = new Promise((res, rej) => { try { const r = indexedDB.open('kpc-logger', 1); r.onupgradeneeded = () => r.result.createObjectStore('kv'); r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); } catch (e) { rej(e); } }));
  const idbGet = k => idb().then(db => new Promise((res, rej) => { const t = db.transaction('kv').objectStore('kv').get(k); t.onsuccess = () => res(t.result); t.onerror = () => rej(t.error); }));
  const idbPut = (k, v) => idb().then(db => new Promise((res, rej) => { const t = db.transaction('kv', 'readwrite'); t.objectStore('kv').put(v, k); t.oncomplete = () => res(); t.onerror = () => rej(t.error); }));
  async function save() {
    L.u = Date.now(); const okLS = put(LK, L);
    try { await idbPut('log', JSON.parse(JSON.stringify(L))); IDBok = true; } catch (e) { IDBok = false; }
    if (PERSIST === null && navigator.storage && navigator.storage.persist) { try { PERSIST = await navigator.storage.persist(); } catch (e) { PERSIST = false; } }
    safe(okLS);
  }
  function safe(okLS) {
    const n = L.q.length, nx = L.q.filter(q => !q.x).length, c = [];
    if (!n) { $('lSafe').innerHTML = ''; return; }
    c.push(okLS === false ? '<span class="warn">⚠ this browser would not save the first copy</span>' : `✓ ${n} contact${n === 1 ? '' : 's'} saved on this device`);
    if (IDBok) c.push('✓ second copy kept');
    c.push(PERSIST ? '✓ browser told to keep it' : '<span class="warn">download a copy now and then (some browsers clear site data when space runs low)</span>');
    if (nx) c.push(`<span class="warn">${nx} not downloaded yet</span>`);
    $('lSafe').innerHTML = c.join(' · ');
  }

  /* ---------------- my station ---------------- */
  const myParks = () => refsOf(SET.park);
  const myCall = () => String(SET.call || '').toUpperCase().trim();
  /* operators (Brandon Oct 16: 'add several people to log with'): my call + the other calls typed in. Each operator logs
     under their own call (own POTA file + credit) unless 'one station call' is ticked. */
  const opsList = () => [...new Set([myCall(), ...String(SET.ops || '').toUpperCase().split(/[\s,;]+/).filter(okCall)].filter(Boolean))];
  const curOp = () => { const L0 = opsList(); return L0.includes(SET.op) ? SET.op : (L0[0] || myCall()); };
  const stationCall = () => SET.share ? myCall() : curOp();
  const multi = () => opsList().length > 1;
  function inAct(q) {
    const P = myParks().join(','), today = ymd(new Date()), team = opsList();
    return q.pk === P && (team.includes(q.my) || team.includes(q.op)) && q.d === today && (!SET.act || q.t >= SET.act);
  }
  const actList = () => L.q.filter(inAct).sort((a, b) => a.t - b.t);
  function meLL() {
    const p = myParks()[0], pi = p && SET.pinfo[p];
    if (pi && pi.la != null) return [pi.la, pi.lo];
    if (SET.me) return SET.me;
    return fromGrid(SET.grid);
  }
  let pT;
  async function parkInfo() {
    const P = myParks(), out = [];
    if (!P.length) { $('myParkInfo').innerHTML = SET.park ? '<span class="bad">Type a park number like US-1234.</span>' : ''; drawAll(); return; }
    $('myParkInfo').innerHTML = 'Looking up ' + esc(P.join(', ')) + '…';
    for (const r of P) {
      let pi = SET.pinfo[r];
      if (!pi || Date.now() - (pi.t || 0) > 7 * 864e5) {
        try {
          const j = await fetch('https://api.pota.app/park/' + encodeURIComponent(r)).then(x => x.ok ? x.json() : null);
          if (j && j.reference) { pi = { n: j.name, st: String(j.locationDesc || '').split(',')[0], la: +j.latitude, lo: +j.longitude, g: j.grid6 || j.grid4 || '', t: Date.now() }; SET.pinfo[r] = pi; saveSet(); }
        } catch (e) {}
      }
      out.push(pi ? `<b>${esc(r)}</b> ${esc(pi.n)} <span class="lg-mu">(${esc(pi.st)}${pi.g ? ' · ' + esc(pi.g) : ''})</span>` : `<b>${esc(r)}</b> <span class="bad">POTA didn't know this number (or no signal)</span>`);
    }
    const p0 = SET.pinfo[P[0]];
    if (p0 && p0.g && !SET.grid) { SET.grid = p0.g; $('myGrid').value = p0.g; saveSet(); }
    $('myParkInfo').innerHTML = out.join(' &nbsp;·&nbsp; ') + (P.length > 1 ? ' <span class="lg-mu">· a ' + P.length + '-fer: every contact counts for each park</span>' : '');
    drawAll();
  }
  function stationInit() {
    $('myCall').value = SET.call; $('myPark').value = SET.park; $('myGrid').value = SET.grid; $('myPwr').value = SET.pwr;
    $('myCall').oninput = e => { SET.call = e.target.value.toUpperCase().trim(); e.target.value = SET.call; put('kpcMyCall', base(SET.call)); saveSet(); drawAll(); };
    $('myPark').oninput = e => { SET.park = e.target.value.toUpperCase(); e.target.value = SET.park; saveSet(); clearTimeout(pT); pT = setTimeout(parkInfo, 700); };
    $('myGrid').oninput = e => { SET.grid = e.target.value.trim(); SET.me = null; saveSet(); drawMap(); };
    $('myPwr').oninput = e => { SET.pwr = e.target.value.trim(); saveSet(); };
    $('myGps').onclick = () => {
      if (!navigator.geolocation) { $('myGpsMsg').textContent = 'This browser has no GPS.'; return; }
      $('myGpsMsg').textContent = 'Finding you…';
      navigator.geolocation.getCurrentPosition(p => { const la = p.coords.latitude, lo = p.coords.longitude; SET.me = [la, lo]; SET.grid = toGrid(la, lo); $('myGrid').value = SET.grid; saveSet(); $('myGpsMsg').textContent = `✓ ${SET.grid} (${la.toFixed(5)}, ${lo.toFixed(5)})`; drawMap(); },
        e => { $('myGpsMsg').textContent = 'Could not get your location (' + (e.message || 'blocked') + ').'; }, { enableHighAccuracy: true, timeout: 20000 });
    };
    if (SET.park) parkInfo();
  }

  /* ---------------- call sign lookup ---------------- */
  const CACHE = get('kpcLgCache', {});
  async function look(call) {
    const b = base(call); if (!okCall(b)) return null;
    const c = CACHE[b]; if (c && Date.now() - c.t < 30 * 864e5) return c;
    let r = null;
    const us = /^(A[A-L]|[KNW])[0-9A-Z]*\d/.test(b);
    const callook = async () => { const j = await fetch('https://callook.info/' + encodeURIComponent(b) + '/json').then(x => x.ok ? x.json() : null); if (!j || j.status !== 'VALID') return null;
      const l2 = String((j.address && j.address.line2) || ''), m = l2.match(/^(.*?),\s*([A-Z]{2})\s+\d/);
      return { name: j.name || '', qth: m ? titleCase(m[1]) : titleCase(l2), st: m ? m[2] : '', g: (j.location && j.location.gridsquare) || '', la: j.location ? +j.location.latitude : null, lo: j.location ? +j.location.longitude : null, cl: (j.current && j.current.operClass) || (j.type === 'CLUB' ? 'CLUB' : ''), cty: 'United States', src: 'FCC (callook.info)' }; };
    const hamdb = async () => { const j = await fetch('https://api.hamdb.org/v1/' + encodeURIComponent(b) + '/json/kpclogger').then(x => x.ok ? x.json() : null); const h = j && j.hamdb, s = h && h.callsign;
      if (!s || (h.messages && /NOT_FOUND/i.test(h.messages.status || '')) || !s.call || s.call === 'NOT_FOUND') return null;
      const nm = [s.fname, s.mi, s.name].filter(Boolean).join(' ');
      return { name: nm, qth: titleCase(s.addr2 || ''), st: s.state || '', g: s.grid || '', la: s.lat ? +s.lat : null, lo: s.lon ? +s.lon : null, cl: s.class || '', cty: s.country || '', src: 'HamDB' }; };
    try { r = us ? (await callook().catch(() => null)) || (await hamdb().catch(() => null)) : (await hamdb().catch(() => null)); } catch (e) { r = null; }
    if (r) { r.t = Date.now(); r.name = titleCase(r.name); CACHE[b] = r; const k = Object.keys(CACHE); if (k.length > 600) k.sort((x, y) => CACHE[x].t - CACHE[y].t).slice(0, 100).forEach(x => delete CACHE[x]); put('kpcLgCache', CACHE); }
    return r;
  }
  function titleCase(s) { s = String(s || '').trim(); if (!s || /[a-z]/.test(s)) return s; return s.toLowerCase().replace(/\b([a-z])/g, m => m.toUpperCase()).replace(/\b(Ii|Iii|Iv)\b/g, m => m.toUpperCase()); }
  let lkT, lkN = 0, WHO = null, SPOTLL = null;
  function dupeOf(call, band, mode) { const b = base(call), me = stationCall(); return actList().filter(q => q.my === me && base(q.call) === b && (!band || q.band === band) && (!mode || q.mode === mode)); }
  async function who() {
    const call = $('eCall').value.toUpperCase().trim(), n = ++lkN;
    if (!okCall(call)) { $('eWho').innerHTML = ''; WHO = null; return; }
    const band = $('eBand').value, mode = $('eMode').value;
    const d = dupeOf(call, band, mode), before = L.q.filter(q => base(q.call) === base(call)).length;
    const dTxt = d.length ? `<span class="t">⚠ ALREADY IN THIS ACTIVATION ON ${esc(band || 'THIS BAND')} ${esc(mode)} AT ${fT(d[d.length - 1].tm)}Z</span>` : '';
    const bTxt = before ? `<span class="lg-mu">worked ${before}× before in your log</span>` : '';
    $('eWho').innerHTML = `<div class="w ${d.length ? 'dupe' : 'none'}"><b>${esc(call)}</b>${dTxt}${bTxt}<span class="lg-mu">looking up…</span></div>`;
    const r = await look(call); if (n !== lkN) return; WHO = r;
    const link = `<a href="https://www.qrz.com/db/${encodeURIComponent(base(call))}" target="_blank" rel="noopener">QRZ ›</a>`;
    if (!r) { $('eWho').innerHTML = `<div class="w ${d.length ? 'dupe' : 'none'}"><b>${esc(call)}</b>${dTxt}${bTxt}<span class="lg-mu">no public record found (could be outside the US/Canada, a new call, or no signal)</span>${link}</div>`; return; }
    const here = meLL(), there = r.la != null && r.lo != null ? [r.la, r.lo] : fromGrid(r.g), mi = here && there ? Math.round(miles(here, there)) : null;
    $('eWho').innerHTML = `<div class="w ${d.length ? 'dupe' : ''}"><b>${esc(r.name || call)}</b><span>${esc([r.qth, r.st].filter(Boolean).join(', '))}${r.cty && r.cty !== 'United States' ? ' · ' + esc(r.cty) : ''}</span>${r.g ? `<span class="lg-mu">${esc(r.g)}</span>` : ''}${r.cl ? `<span class="t">${esc(String(r.cl).toUpperCase())}</span>` : ''}${mi != null ? `<span class="lg-mu">${mi.toLocaleString()} mi</span>` : ''}${dTxt}${bTxt}${link}</div>`;
    if (!$('eName').value) $('eName').value = (r.name || '').split(' ')[0];
    if (!$('eSt').value && r.st) $('eSt').value = r.st;
  }

  /* ---------------- entry form ---------------- */
  let EDIT = null;
  function bandSet() { const k = kHzOf($('eFreq').value); $('eBand').value = bandOf(k); }
  function modeSet() { const m = $('eMode').value, d = rstDef(m); $('eRs').placeholder = d || 'report'; $('eRr').placeholder = d || 'report'; }
  function clearForm(keepRadio) {
    ['eCall', 'eRef', 'eName', 'eSt', 'eNote', 'eRs', 'eRr'].forEach(i => $(i).value = '');
    if (!keepRadio) { $('eFreq').value = ''; $('eBand').value = ''; }
    $('eWho').innerHTML = ''; WHO = null; SPOTLL = null; EDIT = null; $('eLog').innerHTML = '✓ LOG IT <small>(Enter)</small>';
  }
  function entryInit() {
    const lastF = get('kpcLgRadio', null); if (lastF) { $('eFreq').value = lastF.f || ''; $('eMode').value = lastF.m || 'SSB'; }
    bandSet(); modeSet();
    $('eCall').oninput = e => { const p = e.target.selectionStart; e.target.value = e.target.value.toUpperCase().replace(/\s/g, ''); try { e.target.setSelectionRange(p, p); } catch (x) {} clearTimeout(lkT); lkT = setTimeout(who, 450); };
    $('eFreq').oninput = () => { bandSet(); put('kpcLgRadio', { f: $('eFreq').value, m: $('eMode').value }); };
    $('eMode').onchange = () => { modeSet(); put('kpcLgRadio', { f: $('eFreq').value, m: $('eMode').value }); who(); };
    $('eRef').onblur = e => { e.target.value = refsOf(e.target.value).join(', ') || e.target.value.toUpperCase(); };
    $('eSt').oninput = e => { e.target.value = e.target.value.toUpperCase(); };
    $('eClear').onclick = () => { clearForm(true); $('eCall').focus(); };
    $('eManual').onchange = e => { $('eWhen').hidden = !e.target.checked; if (e.target.checked && !$('eWhen').value) $('eWhen').value = iso(new Date()).slice(0, 16); $('eTime').textContent = e.target.checked ? 'time: typed by hand (UTC)' : 'time: now (UTC)'; };
    $('eForm').onsubmit = e => { e.preventDefault(); logIt(); };
  }
  function logIt() {
    const call = $('eCall').value.toUpperCase().trim();
    if (!okCall(call)) { toast('Type their call sign first.'); $('eCall').focus(); return; }
    if (!myCall()) { toast('Put YOUR call in "My station" first.'); $('myCall').focus(); return; }
    const k = kHzOf($('eFreq').value), band = bandOf(k);
    if (!k || !band) { toast('Type the frequency (like 14.285 or 14285).'); $('eFreq').focus(); return; }
    const mode = $('eMode').value;
    let when = new Date();
    if ($('eManual').checked && $('eWhen').value) { const w = new Date($('eWhen').value + ':00Z'); if (!isNaN(w)) when = w; }
    if (!EDIT) { const d = dupeOf(call, band, mode); if (d.length && !confirm(`${call} is already in this activation on ${band} ${mode}. Log it again anyway?`)) return; }
    const note = [$('eNote').value.trim(), SET.carry && SET.notes.trim() ? SET.notes.trim().replace(/\s*\n\s*/g, ' · ') : ''].filter(Boolean).join(' · ').slice(0, 600);
    const r = WHO || {}, there = r.la != null ? [r.la, r.lo] : SPOTLL || fromGrid(r.g);
    const q = { id: EDIT ? EDIT.id : 'q' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6), call, d: ymd(when), tm: iso(when).slice(11, 16).replace(':', ''), t: EDIT ? EDIT.t : Date.now(),
      f: mhz(k), band, mode, rs: $('eRs').value.trim() || rstDef(mode), rr: $('eRr').value.trim() || rstDef(mode), ref: refsOf($('eRef').value).join(','), name: $('eName').value.trim(), st: $('eSt').value.trim().toUpperCase(),
      qth: r.qth || (EDIT && EDIT.qth) || '', g: r.g || (EDIT && EDIT.g) || '', la: there ? there[0] : (EDIT ? EDIT.la : null), lo: there ? there[1] : (EDIT ? EDIT.lo : null), note: EDIT ? $('eNote').value.trim() : note,
      my: EDIT ? EDIT.my : stationCall(), op: EDIT ? (EDIT.op || EDIT.my) : curOp(), pk: EDIT ? EDIT.pk : myParks().join(','), mg: EDIT ? EDIT.mg : SET.grid, pw: EDIT ? EDIT.pw : SET.pwr, x: 0 };
    if (EDIT) { const i = L.q.findIndex(x => x.id === EDIT.id); if (i >= 0) L.q[i] = q; toast('✓ Contact updated.'); }
    else { L.q.push(q); const n = actList().filter(x => x.my === q.my).length; toast(`✓ ${call} logged${multi() ? ' by ' + q.op : ''} (${n} this activation${multi() && !SET.share ? ' for ' + q.my : ''})${n === 10 ? ': 🎉 that makes it a valid activation!' : ''}`, () => { L.q = L.q.filter(x => x.id !== q.id); save(); drawAll(); }); NEWID = q.id; }
    save(); clearForm(true); drawAll(); $('eCall').focus();
  }
  let NEWID = null;

  /* ---------------- log table ---------------- */
  let LV = 'act';
  function drawLog() {
    const s = $('lSearch').value.trim().toUpperCase();
    let R = (LV === 'act' ? actList() : L.q.slice()).sort((a, b) => b.t - a.t);
    if (s) R = R.filter(q => [q.call, q.ref, q.name, q.st, q.qth, q.pk, q.band, q.mode].join(' ').toUpperCase().includes(s));
    $('lCount').textContent = `${R.length} shown · ${L.q.length} in all`;
    $('lBody').innerHTML = R.length ? R.slice(0, 500).map(q => `<tr data-id="${q.id}"${q.id === NEWID ? ' class="new"' : ''}><td class="m">${LV === 'all' ? esc(fD(q.d).slice(5)) + ' ' : ''}${fT(q.tm)}</td><td class="c">${esc(q.call)}${multi() || (q.op && q.op !== q.my) ? `<div class="lg-mu" style="margin:0;font:11px Arial">by ${esc(q.op || q.my)}</div>` : ''}</td><td class="m">${esc(q.f)}</td><td class="hs">${esc(q.mode)}</td><td class="hs m">${esc(q.rs)} / ${esc(q.rr)}</td><td>${q.ref ? `<span class="p2p">${esc(q.ref)}</span>` : ''}${LV === 'all' ? `<div class="lg-mu" style="margin:0">at ${esc(q.pk)}</div>` : ''}</td><td class="hs">${esc([q.name, q.st].filter(Boolean).join(' · '))}</td><td><button type="button" data-ed="${q.id}" aria-label="Edit">✏️</button><button type="button" data-del="${q.id}" aria-label="Delete">🗑</button></td></tr>`).join('')
      : `<tr><td colspan="8"><div class="lg-empty">${LV === 'act' ? (myParks().length ? 'No contacts in this activation yet. Tap a spot or type a call above.' : 'Put your park number in "My station", then log away.') : 'Nothing logged yet.'}</div></td></tr>`;
    NEWID = null;
  }
  function logInit() {
    document.querySelectorAll('[data-lv]').forEach(b => b.onclick = () => { LV = b.dataset.lv; document.querySelectorAll('[data-lv]').forEach(x => x.classList.toggle('on', x === b)); drawLog(); });
    $('lSearch').oninput = drawLog;
    $('lBody').onclick = e => {
      const ed = e.target.closest('[data-ed]'), del = e.target.closest('[data-del]');
      if (del) { const i = L.q.findIndex(q => q.id === del.dataset.del); if (i < 0) return; const [gone] = L.q.splice(i, 1); save(); drawAll(); toast(`🗑 ${gone.call} deleted.`, () => { L.q.push(gone); save(); drawAll(); }); }
      if (ed) { const q = L.q.find(x => x.id === ed.dataset.ed); if (!q) return; EDIT = q;
        $('eCall').value = q.call; $('eFreq').value = q.f; $('eMode').value = q.mode; $('eRs').value = q.rs; $('eRr').value = q.rr; $('eRef').value = q.ref; $('eName').value = q.name; $('eSt').value = q.st; $('eNote').value = q.note || '';
        $('eManual').checked = true; $('eWhen').hidden = false; $('eWhen').value = fD(q.d) + 'T' + fT(q.tm); $('eTime').textContent = 'editing a saved contact';
        bandSet(); $('eLog').innerHTML = '💾 SAVE CHANGES'; $('cEntry').scrollIntoView({ behavior: 'smooth', block: 'start' }); who(); }
    };
  }

  /* ---------------- ADIF / CSV ---------------- */
  const enc = new TextEncoder();
  const af = (k, v) => { v = String(v == null ? '' : v).replace(/[<>]/g, ''); return v === '' ? '' : `<${k}:${enc.encode(v).length}>${v} `; };
  function adMode(m) { m = String(m || '').toUpperCase(); if (m === 'FT4') return ['MFSK', 'FT4']; if (m === 'JS8') return ['MFSK', 'JS8']; if (m === 'PSK31') return ['PSK', 'PSK31']; if (m === 'OTHER') return ['', '']; return [m, '']; }
  function adif(Q, onePark) {
    let o = `KPC Activator Logger\n${af('ADIF_VER', '3.1.4')}${af('PROGRAMID', 'KPC Activator Logger')}${af('CREATED_TIMESTAMP', iso(new Date()).replace(/[-:]/g, '').replace('T', ' ').slice(0, 15))}<EOH>\n`;
    Q.forEach(q => {
      const [md, sm] = adMode(q.mode), their = refsOf(q.ref), mine = onePark ? [onePark] : refsOf(q.pk), p0 = mine[0] || '', pi = SET.pinfo[p0] || {};
      const myst = (String(pi.st || '').match(/^US-([A-Z]{2})$/) || [])[1] || '';
      o += af('CALL', q.call) + af('QSO_DATE', q.d) + af('TIME_ON', q.tm) + af('BAND', q.band) + af('FREQ', q.f) + af('MODE', md) + af('SUBMODE', sm) + af('RST_SENT', q.rs) + af('RST_RCVD', q.rr)
        + af('STATION_CALLSIGN', q.my) + af('OPERATOR', base(q.op || q.my)) + af('MY_SIG', p0 ? 'POTA' : '') + af('MY_SIG_INFO', p0) + af('MY_POTA_REF', mine.join(',')) + af('MY_GRIDSQUARE', q.mg) + af('MY_STATE', myst) + af('TX_PWR', q.pw)
        + (their.length ? af('SIG', 'POTA') + af('SIG_INFO', their[0]) + af('POTA_REF', their.join(',')) : '')
        + af('NAME', q.name) + af('QTH', q.qth) + af('STATE', /^[A-Z]{2}$/.test(q.st) ? q.st : '') + af('GRIDSQUARE', q.g)
        + af('COMMENT', [their.length ? 'P2P ' + their.join(' ') : '', q.name].filter(Boolean).join(' ').slice(0, 120)) + af('NOTES', q.note) + '<EOR>\n';
    });
    return o;
  }
  function parseAdif(t) {
    const out = []; t = String(t || ''); const h = t.search(/<eoh>/i); if (h >= 0) t = t.slice(h + 5);
    t.split(/<eor>/i).forEach(rec => {
      const r = {}; const re = /<(\w+):(\d+)(?::\w)?>/g; let m;
      while ((m = re.exec(rec))) { r[m[1].toUpperCase()] = rec.substr(re.lastIndex, +m[2]); re.lastIndex += +m[2]; }
      if (!r.CALL || !r.QSO_DATE || !r.TIME_ON) return;
      const k = kHzOf(r.FREQ), g = r.GRIDSQUARE || '', ll = fromGrid(g);
      out.push({ id: 'i' + Math.random().toString(36).slice(2, 10), call: r.CALL.toUpperCase(), d: r.QSO_DATE, tm: String(r.TIME_ON).slice(0, 4), t: 0, f: k ? mhz(k) : '', band: (r.BAND || bandOf(k)).toLowerCase(), mode: r.SUBMODE || r.MODE || '',
        rs: r.RST_SENT || '', rr: r.RST_RCVD || '', ref: refsOf(r.POTA_REF || (r.SIG === 'POTA' ? r.SIG_INFO : '')).join(','), name: r.NAME || '', st: r.STATE || '', qth: r.QTH || '', g, la: ll ? ll[0] : null, lo: ll ? ll[1] : null,
        note: r.NOTES || '', my: (r.STATION_CALLSIGN || r.OPERATOR || myCall()).toUpperCase(), pk: refsOf(r.MY_POTA_REF || r.MY_SIG_INFO).join(','), mg: r.MY_GRIDSQUARE || '', pw: r.TX_PWR || '', x: 1 });
    });
    out.forEach(q => q.t = tsOf(q));
    return out;
  }
  function files(list) {
    const touch = matchMedia('(pointer:coarse)').matches;
    if (touch && navigator.canShare) {
      try { const F = list.map(([n, t, ty]) => new File([t], n, { type: ty || 'text/plain' })); if (navigator.canShare({ files: F })) return navigator.share({ files: F, title: list.length > 1 ? 'POTA logs' : list[0][0] }).then(() => true).catch(e => e && e.name === 'AbortError' ? false : dl(list)); } catch (e) {}
    }
    return dl(list);
  }
  function dl(list) {
    list.forEach(([n, t, ty], i) => setTimeout(() => { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([t], { type: ty || 'text/plain' })); a.download = n; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 2000); }, i * 600));
    return Promise.resolve(true);
  }
  function expInit() {
    $('xPota').onclick = async () => {
      const A = actList(); if (!A.length) { toast('No contacts in this activation yet.'); return; }
      const P = myParks(); if (!P.length) { toast('Put your park number in "My station" first.'); return; }
      const d = A[0].d, calls = [...new Set(A.map(q => q.my))], F = [], short = [];
      calls.forEach(c => { const Q = A.filter(q => q.my === c); if (Q.length < 10) short.push(c + ' ' + Q.length); P.forEach(p => F.push([`${c.replace(/\//g, '-')}@${p}-${d}.adi`, adif(Q, p)])); });
      const ok = await files(F);
      if (ok !== false) { A.forEach(q => q.x = 1); save(); toast(`⬇ ${F.length} POTA file${F.length > 1 ? 's' : ''} (${A.length} contacts)${short.length ? '. Under 10 so far: ' + short.join(', ') : ''}.`); }
    };
    $('xAll').onclick = async () => { if (!L.q.length) { toast('Nothing logged yet.'); return; } const Q = L.q.slice().sort((a, b) => a.t - b.t); const ok = await files([[`KPC-activator-log-${myCall().replace(/\//g, '-') || 'mine'}-${ymd(new Date())}.adi`, adif(Q)]]); if (ok !== false) { Q.forEach(q => q.x = 1); save(); } };
    $('xCsv').onclick = () => { const h = 'date_utc,time_utc,call,freq_mhz,band,mode,rst_sent,rst_rcvd,their_park,name,qth,state,grid,my_call,my_park,note\n';
      files([[`KPC-activator-log-${myCall().replace(/\//g, '-') || 'mine'}.csv`, h + L.q.slice().sort((a, b) => a.t - b.t).map(q => [fD(q.d), fT(q.tm), q.call, q.f, q.band, q.mode, q.rs, q.rr, q.ref, q.name, q.qth, q.st, q.g, q.my, q.pk, q.note].map(v => '"' + String(v || '').replace(/"/g, '""') + '"').join(',')).join('\n'), 'text/csv']]); };
    $('xLoad').onchange = async e => {
      const f = e.target.files[0]; if (!f) return; const got = parseAdif(await f.text()); e.target.value = '';
      const have = new Set(L.q.map(q => base(q.call) + q.d + q.tm + q.band)); const add = got.filter(q => !have.has(base(q.call) + q.d + q.tm + q.band));
      L.q.push(...add); save(); drawAll(); toast(add.length ? `⬆ ${add.length} contact${add.length > 1 ? 's' : ''} added from ${f.name}${got.length > add.length ? ` (${got.length - add.length} were already here)` : ''}.` : 'Nothing new in that file.');
    };
    $('xNew').onclick = () => {
      const A = actList(), nx = A.filter(q => !q.x).length;
      if (nx && !confirm(`${nx} contact${nx > 1 ? 's' : ''} in this activation ${nx > 1 ? 'have' : 'has'} not been downloaded yet. Start a new activation anyway? (They stay in "Everything".)`)) return;
      SET.act = Date.now();
      if (SET.notes && confirm('Clear the activation notes too?')) { SET.notes = ''; $('nText').value = ''; if (SET.stamp) stampOn(); }
      saveSet(); drawAll(); toast('🏁 New activation started. Change your park number if you moved.'); $('myPark').focus();
    };
  }

  /* ---------------- POTA spots ---------------- */
  let SP = [], spT = null, spAt = 0;
  async function spots() {
    try { const j = await fetch('https://api.pota.app/spot/activator', { cache: 'no-store' }).then(r => r.ok ? r.json() : Promise.reject(r.status)); SP = Array.isArray(j) ? j : []; spAt = Date.now(); }
    catch (e) { if (!SP.length) $('pList').innerHTML = '<div class="lg-empty">POTA spots are not answering right now (or no signal). Trying again in a minute.</div>'; }
    drawSpots(); clearTimeout(spT); spT = setTimeout(spots, 60000);
  }
  const spMode = s => { const m = String(s.mode || '').toUpperCase(); return /^(USB|LSB|SSB|PHONE)$/.test(m) ? 'SSB' : m; };
  const isRbn = s => /RBN/i.test(s.source || '') || /-#$/.test(s.spotter || '');
  function drawSpots() {
    const b = $('pBand').value, m = $('pMode').value, nr = $('pNoRbn').checked, nw = $('pNoWk').checked, s = $('pSearch').value.trim().toUpperCase();
    const worked = new Set(actList().map(q => base(q.call) + '|' + q.band));
    let R = SP.filter(x => { const k = +x.frequency, md = spMode(x);
      if (nr && isRbn(x)) return false; if (nw && worked.has(base(x.activator) + '|' + bandOf(k))) return false; if (b && bandOf(k) !== b) return false;
      if (m && !(m === 'DATA' ? DIGI.test(md) || /DATA|RTTY|PSK/.test(md) : md === m)) return false;
      if (s && ![x.activator, x.reference, x.name, x.locationDesc, x.comments].join(' ').toUpperCase().includes(s)) return false; return true; });
    R.sort((a, c) => String(c.spotTime).localeCompare(String(a.spotTime)));
    $('pAge').textContent = spAt ? `${R.length} shown · updated ${new Date(spAt).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}` : '';
    $('pList').innerHTML = R.length ? R.slice(0, 120).map(x => { const k = +x.frequency, w = worked.has(base(x.activator) + '|' + bandOf(k)), ago = Math.max(0, Math.round((Date.now() - Date.parse(x.spotTime + 'Z')) / 6e4));
      return `<button type="button" class="lg-sp${w ? ' wk' : ''}" data-sp="${x.spotId}"><span class="c">${esc(x.activator)}</span><span class="md">${esc(spMode(x) || '?')} · ${esc(bandOf(k))}</span><span class="f">${esc(mhz(k))}</span><span class="n">${esc(x.reference)} ${esc(x.name || '')} · ${esc(String(x.locationDesc || '').split(',')[0])}</span><span class="x">${ago} min ago${x.comments ? ' · ' + esc(String(x.comments).slice(0, 80)) : ''}</span></button>`; }).join('')
      : `<div class="lg-empty">${SP.length ? 'No spots match these choices.' : 'Loading spots…'}</div>`;
  }
  function spotsInit() {
    $('pBand').innerHTML = '<option value="">All bands</option>' + BANDS.slice(0, 11).map(b => `<option>${b[0]}</option>`).join('');
    ['pBand', 'pMode', 'pNoRbn', 'pNoWk'].forEach(i => $(i).onchange = () => { put('kpcLgSpF', { b: $('pBand').value, m: $('pMode').value, r: $('pNoRbn').checked, w: $('pNoWk').checked }); drawSpots(); });
    const f = get('kpcLgSpF', null); if (f) { $('pBand').value = f.b || ''; $('pMode').value = f.m || ''; $('pNoRbn').checked = f.r !== false; $('pNoWk').checked = !!f.w; }
    $('pSearch').oninput = drawSpots;
    $('pList').onclick = e => {
      const btn = e.target.closest('[data-sp]'); if (!btn) return; const x = SP.find(s => String(s.spotId) === btn.dataset.sp); if (!x) return;
      clearForm(false); EDIT = null;
      $('eCall').value = String(x.activator || '').toUpperCase(); $('eFreq').value = mhz(+x.frequency);
      const md = spMode(x); $('eMode').value = [...$('eMode').options].some(o => o.value === md) ? md : 'OTHER';
      $('eRef').value = x.reference || ''; bandSet(); modeSet(); put('kpcLgRadio', { f: $('eFreq').value, m: $('eMode').value });
      SPOTLL = x.latitude != null ? [+x.latitude, +x.longitude] : null;
      who(); if (matchMedia('(max-width:1099px)').matches) $('cEntry').scrollIntoView({ behavior: 'smooth', block: 'start' });
      setTimeout(() => $('eRs').focus(), 350);
    };
    spots();
    document.addEventListener('visibilitychange', () => { if (!document.hidden && Date.now() - spAt > 60000) spots(); });
  }

  /* ---------------- self spot ---------------- */
  function rlCheck() { const t = Date.now(), Q = (get('kpcSpotMeSent', []) || []).filter(x => t - x < 36e5);
    if (Q.length && t - Q[Q.length - 1] < 3e5) return 'Please wait ' + Math.ceil((3e5 - (t - Q[Q.length - 1])) / 6e4) + ' more minute(s): one POTA spot every 5 minutes.';
    if (Q.length >= 4) return 'That\'s 4 POTA spots this hour. Try again in ' + Math.ceil((36e5 - (t - Q[0])) / 6e4) + ' minute(s).'; return ''; }
  function rlNote() { const Q = (get('kpcSpotMeSent', []) || []).filter(x => Date.now() - x < 36e5); Q.push(Date.now()); put('kpcSpotMeSent', Q); }
  function spotInit() {
    const msg = (t, c) => { $('sMsg').className = 'lg-msg ' + (c || ''); $('sMsg').textContent = t; };
    $('sCopy').onclick = () => { $('sFreq').value = $('eFreq').value; const m = $('eMode').value; if ([...$('sMode').options].some(o => o.value === m)) $('sMode').value = m; };
    if (!$('sFreq').value) $('sFreq').value = $('eFreq').value;
    $('sSend').onclick = async () => {
      const call = stationCall(), P = myParks(), k = kHzOf($('sFreq').value), mode = $('sMode').value;
      if (!call) { msg('Put your call in "My station" first.', 'bad'); return; }
      if (!P.length) { msg('Put your park number in "My station" first.', 'bad'); return; }
      if (!k || !bandOf(k)) { msg('Type the frequency you are on (like 14.285).', 'bad'); return; }
      const wait = rlCheck(); if (wait) { msg(wait, 'bad'); return; }
      let cm = $('sCm').value.trim(); if (P.length > 1 && !/fer|US-|\d{4}/i.test(cm)) cm = (P.length + '-fer: ' + P.slice(1).join(' ') + ' ' + cm).trim();
      if (!confirm(`This posts a real, public spot on POTA:\n\n${call} at ${P[0]} on ${mhz(k)} MHz ${mode}${cm ? '\n' + cm : ''}\n\nOnly send it when you're on the air. Send it?`)) return;
      msg('Sending…');
      try {
        const r = await fetch('https://api.pota.app/spot/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ activator: call, spotter: base(call), frequency: String(Math.round(k * 10) / 10), reference: P[0], mode, source: 'KPC Logger', comments: cm }) });
        const body = await r.text().catch(() => '');
        if (r.ok) { rlNote(); msg(`✓ Spot sent: ${call} at ${P[0]} on ${mhz(k)} ${mode}. It shows on pota.app within a minute. Next spot can go in 5 minutes.`, 'ok'); setTimeout(spots, 8000); }
        else msg('✗ POTA turned it down: ' + (String(body).replace(/^"|"$/g, '') || 'error ' + r.status) + '. Nothing was sent.', 'bad');
      } catch (e) { msg('✗ POTA could not be reached. Check your signal and try again.', 'bad'); }
    };
  }

  /* ---------------- notes ---------------- */
  const stampLine = () => `${myParks().join(' + ') || 'US-????'} · ${fD(ymd(new Date()))} UTC`;
  function stampOn() { const t = $('nText').value, line = stampLine(); if (!t.startsWith(line)) { $('nText').value = line + '\n' + t.replace(/^[A-Z0-9 +-]*\d{4,5}[^\n]*UTC\n?/, ''); SET.notes = $('nText').value; saveSet(); } }
  function notesInit() {
    $('nText').value = SET.notes || ''; $('nStamp').checked = !!SET.stamp; $('nCarry').checked = !!SET.carry;
    let nt; $('nText').oninput = () => { clearTimeout(nt); nt = setTimeout(() => { SET.notes = $('nText').value; saveSet(); $('nSaved').textContent = '✓ Saved on this device ' + new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }) + '.' + (SET.carry ? ' These notes go into every new contact.' : ''); }, 400); };
    $('nStamp').onchange = e => { SET.stamp = e.target.checked; if (SET.stamp) stampOn(); else { $('nText').value = $('nText').value.replace(/^[A-Z0-9 +?-]*· \d{4}-\d{2}-\d{2} UTC\n?/, ''); SET.notes = $('nText').value; } saveSet(); };
    $('nCarry').onchange = e => { SET.carry = e.target.checked; saveSet(); toast(SET.carry ? '✓ Your notes will go into every new contact.' : 'Notes will stay on this page only.'); };
    $('myPark').addEventListener('change', () => { if (SET.stamp) stampOn(); });
  }

  /* ---------------- map ---------------- */
  let MAP = null, ML = null, MV = 'act';
  function mapInit() {
    document.querySelectorAll('[data-mv]').forEach(b => b.onclick = () => { MV = b.dataset.mv; document.querySelectorAll('[data-mv]').forEach(x => x.classList.toggle('on', x === b)); drawMap(true); });
    if (!window.L) { $('mMap').innerHTML = '<div class="lg-empty">The map could not load (no signal?).</div>'; return; }
    MAP = window.L.map('mMap', { worldCopyJump: true, zoomControl: true }).setView([37.8, -85.7], 5);
    window.L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 18, attribution: 'Imagery © Esri, Maxar, Earthstar Geographics' }).addTo(MAP);
    window.L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', { maxZoom: 18 }).addTo(MAP);
    ML = window.L.layerGroup().addTo(MAP);
  }
  let lastFit = '';
  function drawMap(refit) {
    if (!MAP) return; ML.clearLayers();
    const Q = (MV === 'act' ? actList() : L.q).filter(q => q.la != null && q.lo != null), me = meLL(), used = {};
    if (me) window.L.marker(me, { icon: window.L.divIcon({ className: '', html: '<div class="lg-me">⭐</div>', iconSize: [26, 26], iconAnchor: [13, 13] }), zIndexOffset: 1000 }).bindPopup(`<b>${esc(myCall() || 'You')}</b><br>${esc(myParks().join(', '))}<br>${esc(SET.grid)}`).addTo(ML);
    Q.forEach(q => {
      const c = BCOL[q.band] || '#ddd'; used[q.band] = c; const ll = [q.la, q.lo];
      if (me) window.L.polyline([me, ll], { color: c, weight: 1.6, opacity: .6 }).addTo(ML);
      const mi = me ? Math.round(miles(me, ll)) : null;
      window.L.circleMarker(ll, { radius: 6, color: '#fff', weight: 2, fillColor: c, fillOpacity: 1 }).bindPopup(`<b>${esc(q.call)}</b> ${esc(q.name)}<br>${esc([q.qth, q.st].filter(Boolean).join(', '))}${q.ref ? '<br>Park: ' + esc(q.ref) : ''}<br>${esc(q.band)} ${esc(q.mode)} · ${fT(q.tm)}Z ${esc(fD(q.d))}${mi != null ? '<br>' + mi.toLocaleString() + ' mi' : ''}`).addTo(ML);
    });
    const noLoc = (MV === 'act' ? actList() : L.q).length - Q.length;
    $('mInfo').textContent = Q.length ? `${Q.length} on the map${noLoc ? ` · ${noLoc} with no location` : ''}` : '';
    $('mKey').innerHTML = Object.entries(used).map(([b, c]) => `<span><i style="background:${c}"></i>${esc(b)}</span>`).join('');
    const key = MV + Q.length + (me || []).join();
    if (refit || key !== lastFit) { lastFit = key; const pts = Q.map(q => [q.la, q.lo]).concat(me ? [me] : []); if (pts.length > 1) MAP.fitBounds(pts, { padding: [30, 30], maxZoom: 8 }); else if (pts.length) MAP.setView(pts[0], 7); }
  }

  /* ---------------- rates ---------------- */
  function rates() {
    const A = actList(), now = Date.now(), T = A.map(tsOf).sort((a, b) => a - b), n = A.length;
    const last10 = T.slice(-10), r10 = last10.length > 1 ? Math.round((last10.length - 1) / Math.max((last10[last10.length - 1] - last10[0]) / 36e5, 1 / 60)) : 0;
    const hr = T.filter(t => now - t <= 36e5).length;
    $('sAct').textContent = n; $('sRate').textContent = r10; $('sHr').textContent = hr;
    if (multi() && !SET.share) { $('sOps').innerHTML = opsList().map(c => { const k2 = A.filter(q => q.my === c).length; return `<span class="${k2 >= 10 ? 'ok' : ''}">${esc(c)} ${k2 >= 10 ? '✓ ' + k2 : k2 + '/10'}</span>`; }).join(''); }
    else if (multi()) { $('sOps').innerHTML = opsList().map(c => `<span>${esc(c)} ${A.filter(q => (q.op || q.my) === c).length} logged</span>`).join(''); }
    else $('sOps').innerHTML = '';
    drawOps();
    const g = Math.min(n, 10); $('sGoalBar').style.width = g * 10 + '%';
    const P = myParks();
    $('sGoal').parentElement.classList.toggle('done', n >= 10);
    $('sGoal').textContent = !P.length ? 'Add your park number in "My station" to start an activation' : n >= 10 ? `✓ Valid activation at ${P.join(' + ')} (${n} contacts). Keep going!` : `${n} of 10 contacts for a valid POTA activation at ${P.join(' + ')}`;
    const calls = new Set(A.map(q => base(q.call))).size, p2p = A.filter(q => q.ref).length, sts = new Set(A.map(q => q.st).filter(s => /^[A-Z]{2}$/.test(s))).size;
    const me = meLL(); let far = null; A.forEach(q => { if (me && q.la != null) { const m = miles(me, [q.la, q.lo]); if (!far || m > far[0]) far = [m, q.call]; } });
    const span = T.length > 1 ? (T[T.length - 1] - T[0]) / 36e5 : 0, avg = span > 0.05 ? Math.round((n - 1) / span) : 0;
    const H = {}; T.forEach(t => { const h = new Date(t).getUTCHours(); H[h] = (H[h] || 0) + 1; });
    const best = Math.max(0, ...Object.values(H));
    $('rTiles').innerHTML = [[n, 'contacts'], [calls, 'different calls'], [r10, 'rate, last 10 /h'], [avg, 'average /h'], [hr, 'last 60 min'], [best, 'best hour'], [p2p, 'park-to-park'], [sts, 'states'], [far ? Math.round(far[0]).toLocaleString() : '-', far ? 'mi, farthest (' + esc(far[1]) + ')' : 'farthest']]
      .map(([v, l]) => `<div><b>${v}</b><span>${l}</span></div>`).join('');
    if (!T.length) { $('rHours').innerHTML = '<div class="lg-empty" style="width:100%">The hours fill in as you log.</div>'; $('rBm').innerHTML = ''; return; }
    const h0 = Math.floor(T[0] / 36e5), h1 = Math.max(Math.floor(T[T.length - 1] / 36e5), Math.floor(now / 36e5) <= h0 + 23 ? Math.floor(now / 36e5) : h0), cols = [];
    for (let h = h0; h <= h1 && cols.length < 24; h++) { const c = T.filter(t => Math.floor(t / 36e5) === h).length, hh = String(new Date(h * 36e5).getUTCHours()).padStart(2, '0');
      cols.push(`<div class="h${c && c === best ? ' best' : ''}" title="${c} contacts at ${hh}00Z"><b>${c || ''}</b><i style="height:${best ? Math.max(2, c / best * 100) : 2}%"></i><span>${hh}z</span></div>`); }
    $('rHours').innerHTML = cols.join('');
    const B = {}, M = {}; A.forEach(q => { B[q.band] = (B[q.band] || 0) + 1; M[q.mode] = (M[q.mode] || 0) + 1; });
    $('rBm').innerHTML = Object.entries(B).sort((a, b) => b[1] - a[1]).map(([k, v]) => `<span><i style="display:inline-block;width:9px;height:9px;border-radius:50%;background:${BCOL[k] || '#ddd'};margin-right:5px"></i>${esc(k)} <b>${v}</b></span>`).join('') + Object.entries(M).sort((a, b) => b[1] - a[1]).map(([k, v]) => `<span>${esc(k)} <b>${v}</b></span>`).join('');
  }

  function drawAll() { drawLog(); rates(); drawMap(); drawSpots(); }

  /* ---------------- operators ---------------- */
  function drawOps() {
    const L0 = opsList(), A = actList();
    $('myShareL').hidden = L0.length < 2; $('eOps').hidden = L0.length < 2;
    if (L0.length < 2) return;
    const cur = curOp();
    $('eOps').innerHTML = '<b>ON THE RADIO NOW:</b>' + L0.map(c => `<button type="button" data-op="${esc(c)}" class="${c === cur ? 'on' : ''}">${esc(c)}<small>${A.filter(q => (q.op || q.my) === c).length}</small></button>`).join('');
  }
  function opsInit() {
    $('myOps').value = SET.ops || ''; $('myShare').checked = !!SET.share;
    $('myOps').oninput = e => { e.target.value = e.target.value.toUpperCase(); SET.ops = e.target.value; saveSet(); drawAll(); };
    $('myShare').onchange = e => { SET.share = e.target.checked; saveSet(); drawAll(); toast(SET.share ? 'Everyone logs under ' + (myCall() || 'my call') + ' (one POTA file per park).' : 'Each operator logs under their own call (their own POTA files).'); };
    $('eOps').onclick = e => { const b = e.target.closest('[data-op]'); if (!b) return; SET.op = b.dataset.op; saveSet(); drawOps(); who(); toast('🎙 ' + SET.op + ' is on the radio.'); $('eCall').focus(); };
  }

  /* ---------------- parks near me (GPS; works with no signal once saved) ---------------- */
  let PK = null;
  async function parkList() {
    if (PK) return PK; const out = [];
    try { const ix = await fetch('data/parkinfo/index.json').then(r => r.json()); (ix.rows || []).forEach(r => { if (r[3] != null) out.push([r[0], r[1], 'US-' + r[2], +r[3], +r[4]]); }); } catch (e) {}
    try { const ky = await fetch('kpc-ky-data.json').then(r => r.json()); (ky.parks || []).forEach(p => { if (p.la != null) out.push([p.c, p.n, 'US-KY', +p.la, +p.lo]); }); } catch (e) {}
    if (out.length) PK = out; return out;
  }
  function nearInit() {
    $('myNearB').onclick = () => {
      if (!navigator.geolocation) { $('myGpsMsg').textContent = 'This browser has no GPS.'; return; }
      $('myGpsMsg').textContent = 'Finding you…';
      navigator.geolocation.getCurrentPosition(async pos => {
        const me = [pos.coords.latitude, pos.coords.longitude]; SET.me = me; SET.grid = toGrid(me[0], me[1]); $('myGrid').value = SET.grid; saveSet();
        const all = await parkList();
        if (!all.length) { $('myGpsMsg').textContent = 'The park list could not load (no signal, and it was not saved yet).'; return; }
        const R = all.map(p => [p, miles(me, [p[3], p[4]])]).sort((a, b) => a[1] - b[1]).slice(0, 8);
        $('myGpsMsg').textContent = `✓ You're at ${SET.grid}. Nearest parks:`;
        $('myNear').hidden = false;
        $('myNear').innerHTML = R.map(([p, d]) => `<div class="np"><div><b>${esc(p[0])}</b> <span>${esc(p[1])}</span> <em>${esc(p[2].slice(3))} · ${d < 0.2 ? 'you are here or very close' : d.toFixed(1) + ' mi'}</em></div><button type="button" class="lg-btn gold sm" data-use="${esc(p[0])}">USE THIS PARK</button><button type="button" class="lg-btn line sm" data-add="${esc(p[0])}">+ ADD (2-FER)</button></div>`).join('') + '<p class="lg-mu">The park pin is not the boundary: make sure you are inside the park (Am I in the Park? checks the official line).</p>';
        drawMap(true);
      }, e => { $('myGpsMsg').textContent = 'Could not get your location (' + (e.message || 'blocked') + ').'; }, { enableHighAccuracy: true, timeout: 20000 });
    };
    $('myNear').onclick = e => {
      const u = e.target.closest('[data-use]'), a = e.target.closest('[data-add]'); if (!u && !a) return;
      const ref = (u || a).dataset.use || (u || a).dataset.add, p = (PK || []).find(x => x[0] === ref);
      if (p && !SET.pinfo[ref]) SET.pinfo[ref] = { n: p[1], st: p[2], la: p[3], lo: p[4], g: toGrid(p[3], p[4]), t: Date.now() - 6 * 864e5 };
      const cur = myParks(); SET.park = u ? ref : [...new Set(cur.concat(ref))].join(', ');
      $('myPark').value = SET.park; saveSet(); parkInfo(); if (SET.stamp) stampOn();
      $('myNear').hidden = true; toast(`✓ ${SET.park} is your park now. Every contact you log gets it.`);
    };
  }

  /* ---------------- notes onto contacts already logged ---------------- */
  function notesAllInit() {
    $('nAll').onclick = () => {
      const t = ($('nText').value || '').trim().replace(/\s*\n\s*/g, ' · '); if (!t) { toast('Type some notes first.'); return; }
      const A = actList(); if (!A.length) { toast('No contacts in this activation yet.'); return; }
      let n = 0; A.forEach(q => { if (!(q.note || '').includes(t)) { q.note = [q.note, t].filter(Boolean).join(' · ').slice(0, 900); q.x = 0; n++; } });
      save(); drawAll(); toast(n ? `✓ Notes added to ${n} contact${n > 1 ? 's' : ''}.` : 'Those contacts already have these notes.');
    };
  }

  /* ---------------- install + no signal ---------------- */
  let PROMPT = null;
  function appInit() {
    const sw = () => { try { if ('serviceWorker' in navigator && window.isSecureContext) return navigator.serviceWorker.register('kpc-finder-sw.js'); } catch (e) {} return Promise.resolve(null); };
    sw();
    window.addEventListener('beforeinstallprompt', e => { e.preventDefault(); PROMPT = e; $('aInstall').hidden = false; });
    window.addEventListener('appinstalled', () => { $('aInstall').hidden = true; $('aMsg').className = 'lg-msg ok'; $('aMsg').textContent = '✓ Installed. Open it from your home screen or apps.'; });
    if (matchMedia('(display-mode: standalone)').matches || navigator.standalone) { $('aMsg').className = 'lg-msg ok'; $('aMsg').textContent = '✓ Running as an installed app.'; }
    $('aInstall').onclick = async () => { if (!PROMPT) return; PROMPT.prompt(); try { await PROMPT.userChoice; } catch (e) {} PROMPT = null; $('aInstall').hidden = true; };
    $('aSave').onclick = async () => {
      const m = $('aMsg'); m.className = 'lg-msg'; m.textContent = 'Saving…';
      if (!window.caches) { m.className = 'lg-msg bad'; m.textContent = 'This browser can’t save pages for offline use.'; return; }
      try { await sw(); } catch (e) {}
      const strip = u => { const x = new URL(u, location.href); x.search = ''; x.hash = ''; return x.href; };
      const urls = new Set([location.href, 'kpc-logger.html', 'kpc-logger.webmanifest', 'data/parkinfo/index.json', 'kpc-ky-data.json', 'kpc-icon-192.png', 'kpc-icon-512.png', 'kpc-icon-180.png', 'bg-group.jpg', 'bg-group-mobile.jpg', 'KPC26-Group-Photo.jpg', 'KPC26-Group-Photo-web.jpg',
        'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css', 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js']);
      try { performance.getEntriesByType('resource').forEach(r => { const u = new URL(r.name); if (u.origin === location.origin) urls.add(r.name); }); } catch (e) {}
      const c = await caches.open('kpc-finder-v1'); let ok = 0, bad = 0;
      for (const u of urls) { try { const abs = new URL(u, location.href); const r = await fetch(abs.href, { cache: 'no-cache' }); if (r.ok) { await c.put(abs.origin === location.origin ? strip(abs.href) : abs.href, r.clone()); ok++; } else bad++; } catch (e) { bad++; } }
      PK = null; parkList();
      m.className = 'lg-msg ' + (bad && !ok ? 'bad' : 'ok'); m.textContent = ok ? `✓ Saved (${ok} files). The logger now opens and works with no signal on this device.${bad ? ' ' + bad + ' extra file(s) could not be saved.' : ''}` : 'Could not save (no signal?). Try again with signal.';
      put('kpcLgSaved', Date.now());
    };
    const t = get('kpcLgSaved', 0); if (t && !$('aMsg').textContent) { $('aMsg').className = 'lg-msg ok'; $('aMsg').textContent = '✓ Saved for no signal on ' + new Date(t).toLocaleDateString([], { month: 'short', day: 'numeric' }) + '. Tap again to refresh it.'; }
  }

  async function start() {
    const parts = [stationInit, opsInit, nearInit, entryInit, logInit, expInit, spotsInit, spotInit, notesInit, notesAllInit, appInit, mapInit];
    parts.forEach(f => { try { f(); } catch (e) { console.error(f.name, e); } });
    try { const o = await idbGet('log'); IDBok = true; if (o && Array.isArray(o.q) && ((o.u || 0) > (L.u || 0) || o.q.length > L.q.length)) { L = o; put(LK, L); } } catch (e) {}
    if (navigator.storage && navigator.storage.persisted) { try { PERSIST = await navigator.storage.persisted(); } catch (e) {} }
    drawAll(); safe();
    setInterval(() => { $('sUtc').textContent = iso(new Date()).slice(11, 19); }, 1000);
    setInterval(rates, 30000);
    window.addEventListener('storage', e => { if (e.key === LK) { L = get(LK, L); drawAll(); } });
  }
  start();
})();
