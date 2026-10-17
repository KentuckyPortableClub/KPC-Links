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
  const refsOf = s => [...new Set(String(s || '').toUpperCase().split(/[\s,;+&]+/).map(nref).filter(r => REF.test(r) && !/FF-/.test(r)))];   /* POTA only */
  const sotaN = r => { const m = String(r || '').trim().toUpperCase().match(/^([A-Z0-9]{1,4}\/[A-Z0-9]{2})-(\d{1,3})$/); return m ? m[1] + '-' + m[2].padStart(3, '0') : ''; };
  const wwffN = r => { const m = String(r || '').trim().toUpperCase().match(/^([A-Z0-9]{1,3}FF)-(\d{1,4})$/); return m ? m[1] + '-' + m[2].padStart(4, '0') : ''; };
  const progOf = r => sotaN(r) ? 'SOTA' : wwffN(r) ? 'WWFF' : 'POTA';
  /* any program's numbers (their P2P park, KFF, summit): POTA US-1234, WWFF KFF-1234, SOTA W4K/EC-001 */
  const anyRefs = s => [...new Set(String(s || '').toUpperCase().split(/[\s,;+&]+/).filter(Boolean).map(t => sotaN(t) || wwffN(t) || nref(t)).filter(r => sotaN(r) || wwffN(r) || REF.test(r)))];
  const byProg = s => { const A = anyRefs(s); return { pota: A.filter(r => progOf(r) === 'POTA'), wwff: A.filter(r => progOf(r) === 'WWFF'), sota: A.filter(r => progOf(r) === 'SOTA') }; };
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
  const SET = Object.assign({ call: get('kpcMyCall', '') || '', park: '', grid: '', pwr: '', stamp: false, carry: false, notes: '', act: 0, pinfo: {}, me: null, ops: '', op: '', share: false, wf: '', so: '', role: 'act', prev: false }, get('kpcLgSet', {}));
  const saveSet = () => put('kpcLgSet', SET);
  /* one box for every park number now (Brandon Oct 16): fold old separate WWFF / SOTA boxes into it once */
  if (SET.wf || SET.so) { const have = String(SET.park || ''); [SET.wf, SET.so].forEach(r => { if (r && !have.toUpperCase().includes(String(r).toUpperCase())) SET.park = [SET.park, r].filter(Boolean).join(', '); }); SET.wf = ''; SET.so = ''; saveSet(); }
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
  const myParks = () => isHunt() ? [] : refsOf(SET.park);
  const isHunt = () => SET.role === 'hunt';
  const myWwff = () => isHunt() ? '' : (byProg(SET.park).wwff[0] || '');
  const mySota = () => isHunt() ? '' : (byProg(SET.park).sota[0] || '');
  const myRefsTxt = () => [myParks().join(' + '), myWwff(), mySota()].filter(Boolean).join(' · ');
  const myCall = () => String(SET.call || '').toUpperCase().trim();
  /* operators (Brandon Oct 16: 'add several people to log with'): my call + the other calls typed in. Each operator logs
     under their own call (own POTA file + credit) unless 'one station call' is ticked. */
  const opsList = () => [...new Set([myCall(), ...String(SET.ops || '').toUpperCase().split(/[\s,;]+/).filter(okCall)].filter(Boolean))];
  const curOp = () => { const L0 = opsList(); return L0.includes(SET.op) ? SET.op : (L0[0] || myCall()); };
  const stationCall = () => SET.share ? myCall() : curOp();
  const multi = () => opsList().length > 1;
  function inAct(q) {
    const P = myParks().join(','), W = myWwff(), So = mySota(), today = ymd(new Date()), team = opsList();
    if (isHunt()) return q.role === 'hunt' && (team.includes(q.my) || team.includes(q.op)) && q.d === today && (!SET.act || q.t >= SET.act);
    if (q.role === 'hunt') return false;
    const same = P ? q.pk === P : W ? q.wf === W : So ? q.so === So : !q.pk && !q.wf && !q.so;
    return same && (team.includes(q.my) || team.includes(q.op)) && q.d === today && (!SET.act || q.t >= SET.act);
  }
  const actList = () => L.q.filter(inAct).sort((a, b) => a.t - b.t);
  function meLL() {
    const p = myParks()[0], pi = p && SET.pinfo[p];
    if (pi && pi.la != null) return [pi.la, pi.lo];
    if (SET.me) return SET.me;
    return fromGrid(SET.grid);
  }
  let pT, KYD = null;
  /* the one park box: POTA, WWFF and SOTA numbers together; adding WWFF / SOTA later also marks this activation's contacts */
  /* tap the park box: offer the other programs at the same place (KFF for a KY park, summits inside it); nothing is added by itself */
  async function parkSug() {
    const box = $('myParkSug'), P = refsOf(SET.park), have = anyRefs(SET.park), out = [];
    try { KYD = KYD || await fetch('kpc-ky-data.json').then(r => r.json()); } catch (e) {}
    if (KYD) P.forEach(r => { const kp = (KYD.parks || []).find(x => x.c === r); if (!kp) return;
      (kp.kff || []).forEach(k => { if (!have.includes(k)) out.push(`<button type="button" data-sug="${esc(k)}">+ ${esc(k)} <small>WWFF / KFF, same park</small></button>`); });
      (kp.sota || []).forEach(k => { if (!have.includes(k)) out.push(`<button type="button" data-sug="${esc(k)}">+ ${esc(k)} <small>SOTA summit here (only if you're on top)</small></button>`); }); });
    box.innerHTML = out.length ? '<span>Also here (tap to add):</span>' + out.join('') : ''; box.hidden = !out.length;
  }
  function setRefs(v, typing) {
    const before = actList(), W0 = myWwff(), S0 = mySota();
    SET.park = String(v || '').toUpperCase().replace(/^[\s,]+/, ''); if (!typing || $('myPark').value.toUpperCase() !== SET.park) $('myPark').value = SET.park;
    const W = myWwff(), So = mySota(); let ch = 0;
    if (W && W !== W0) before.forEach(q => { if (!q.wf) { q.wf = W; ch++; } }); if (So && So !== S0) before.forEach(q => { if (!q.so) { q.so = So; ch++; } });
    saveSet(); if (ch) save(); drawAll(); if (document.activeElement === $('myPark')) { clearTimeout(setRefs.t); setRefs.t = setTimeout(parkSug, 800); }
  }
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
    /* a Kentucky park that is also a KFF reference fills in the WWFF box (never the SOTA box: you must be on the summit) */

    const p0 = SET.pinfo[P[0]];
    if (p0 && p0.g && !SET.grid) { SET.grid = p0.g; $('myGrid').value = p0.g; saveSet(); }
    $('myParkInfo').innerHTML = out.join(' &nbsp;·&nbsp; ') + (P.length > 1 ? ' <span class="lg-mu">· a ' + P.length + '-fer: every contact counts for each park</span>' : '');
    drawAll();
  }
  function stationInit() {
    $('myCall').value = SET.call; $('myPark').value = SET.park; $('myGrid').value = SET.grid; $('myPwr').value = SET.pwr;
    $('myCall').oninput = e => { SET.call = e.target.value.toUpperCase().trim(); e.target.value = SET.call; put('kpcMyCall', base(SET.call)); saveSet(); drawAll(); };
    $('myPark').oninput = e => { const W0 = myWwff(); setRefs(e.target.value, true); if (W0 && !myWwff()) SET.noKff = true; saveSet(); clearTimeout(pT); pT = setTimeout(parkInfo, 700); };
    $('myPark').addEventListener('focus', parkSug);
    $('myParkSug').onclick = e => { const b = e.target.closest('[data-sug]'); if (!b) return; setRefs([SET.park, b.dataset.sug].filter(x => String(x || '').trim()).join(', ')); parkSug(); toast('✓ ' + b.dataset.sug + ' added.'); };
    $('myGrid').oninput = e => { SET.grid = e.target.value.trim(); SET.me = null; saveSet(); drawMap(); opBar(); };
    $('myPwr').oninput = e => { SET.pwr = e.target.value.trim(); saveSet(); opBar(); };
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
  function dupeOf(call, band, mode, ref) { const b = base(call), me = stationCall(); return actList().filter(q => q.my === me && base(q.call) === b && (!band || q.band === band) && (!mode || q.mode === mode) && (!isHunt() || (q.ref || '') === (ref || ''))); }
  async function who() {
    const call = $('eCall').value.toUpperCase().trim(), n = ++lkN;
    if (!okCall(call)) { $('eWho').innerHTML = ''; WHO = null; return; }
    const band = $('eBand').value, mode = $('eMode').value;
    const d = dupeOf(call, band, mode, anyRefs($('eRef').value).join(',')), before = L.q.filter(q => base(q.call) === base(call)).length;
    const dTxt = d.length ? `<span class="t">⚠ ALREADY IN YOUR LOG ${isHunt() ? 'TODAY' : 'THIS ACTIVATION'} ON ${esc(band || 'THIS BAND')} ${esc(mode)} AT ${fT(d[d.length - 1].tm)}Z</span>` : '';
    const prev = L.q.filter(q => base(q.call) === base(call) && !inAct(q)).sort((a, b) => b.t - a.t), lp = prev[0];
    const bTxt = prev.length ? `<span class="lg-prev">🔁 worked ${prev.length}× before · last ${esc(fD(lp.d))} at ${esc([lp.pk, lp.wf, lp.so].filter(Boolean).join(' ') || 'a park')} (${esc(lp.band)} ${esc(lp.mode)})${lp.name ? ' · ' + esc(lp.name) : ''}</span>` : (L.q.length && !before ? '<span class="lg-prev new">🆕 first time in your log</span>' : '');
    $('eWho').innerHTML = `<div class="w ${d.length ? 'dupe' : 'none'}"><b>${esc(call)}</b>${dTxt}${bTxt}<span class="lg-mu">looking up…</span></div>`;
    const r = await look(call); if (n !== lkN) return; WHO = r ? Object.assign({ call: base(call) }, r) : null;
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
  /* AUTO FREQUENCY (Brandon Oct 17: 'FT8 FT4 FT2 select the band and the freq is automatic… if any mode changes the freq goes
     to somewhere in the right freq area'): FT8/FT4/FT2/JS8/PSK31 = the standard dial frequency; CW, phone, AM, FM = a common
     spot in that part of the band, only when the frequency is empty, on another band or outside that mode's part of the band */
  const DIAL = {
    FT8: { '160m': 1840, '80m': 3573, '60m': 5357, '40m': 7074, '30m': 10136, '20m': 14074, '17m': 18100, '15m': 21074, '12m': 24915, '10m': 28074, '6m': 50313, '2m': 144174 },
    FT4: { '80m': 3575, '40m': 7047.5, '30m': 10140, '20m': 14080, '17m': 18104, '15m': 21140, '12m': 24919, '10m': 28180, '6m': 50318, '2m': 144170 },
    FT2: { '40m': 7052, '20m': 14084 },   /* new mode (2025-26): only these two are published so far; check your FT2 program */
    JS8: { '160m': 1842, '80m': 3578, '40m': 7078, '30m': 10130, '20m': 14078, '17m': 18104, '15m': 21078, '12m': 24922, '10m': 28078, '6m': 50318 },
    PSK31: { '80m': 3580, '40m': 7070, '30m': 10142, '20m': 14070, '17m': 18100, '15m': 21070, '12m': 24920, '10m': 28120, '6m': 50290 },
    RTTY: { '80m': 3580, '40m': 7080, '30m': 10140, '20m': 14080, '17m': 18100, '15m': 21080, '12m': 24920, '10m': 28080 },
    CW: { '160m': 1820, '80m': 3530, '60m': 5332, '40m': 7030, '30m': 10110, '20m': 14040, '17m': 18080, '15m': 21040, '12m': 24900, '10m': 28040, '6m': 50090, '2m': 144050, '70cm': 432100 },
    SSB: { '160m': 1900, '80m': 3850, '60m': 5330.5, '40m': 7200, '20m': 14250, '17m': 18130, '15m': 21300, '12m': 24950, '10m': 28400, '6m': 50150, '2m': 144200, '1.25m': 222100, '70cm': 432100 },
    AM: { '160m': 1885, '80m': 3885, '40m': 7290, '20m': 14286, '15m': 21425, '10m': 29000, '6m': 50400, '2m': 144400 },
    FM: { '10m': 29600, '6m': 52525, '2m': 146520, '1.25m': 223500, '70cm': 446000 },
  };
  /* the part of each band where a mode belongs (kHz from the band's bottom edge up to the top) */
  const AREA = { CW: { '160m': [1800, 1840], '80m': [3500, 3600], '40m': [7000, 7125], '30m': [10100, 10150], '20m': [14000, 14150], '17m': [18068, 18110], '15m': [21000, 21200], '12m': [24890, 24930], '10m': [28000, 28300], '6m': [50000, 50100] },
    SSB: { '160m': [1843, 2000], '80m': [3600, 4000], '60m': [5330, 5410], '40m': [7125, 7300], '20m': [14150, 14350], '17m': [18110, 18168], '15m': [21200, 21450], '12m': [24930, 24990], '10m': [28300, 29700], '6m': [50100, 54000], '2m': [144100, 148000], '1.25m': [222000, 225000], '70cm': [420000, 450000] } };
  AREA.AM = AREA.SSB;
  function autoFreq(why) {
    const m = $('eMode').value, b = $('eBand').value, k = kHzOf($('eFreq').value); if (!b) return;
    const D = DIAL[m] || {}, fixed = ['FT8', 'FT4', 'FT2', 'JS8', 'PSK31', 'RTTY'].includes(m);
    let f = null;
    if (fixed) { if (D[b]) f = D[b]; else if (why === 'band' || bandOf(k) !== b) { toast(`No standard ${m} frequency on ${b}: type the one you are on.`); return; } }
    else { const A = (AREA[m] || {})[b]; const okNow = k && bandOf(k) === b && (!A || (k >= A[0] && k <= A[1])); if (!okNow && D[b]) f = D[b]; }
    if (f == null || Math.abs(f - k) < 0.01) return;
    $('eFreq').value = mhz(f); put('kpcLgRadio', { f: $('eFreq').value, m }); try { radioTxt(); } catch (e) {}
  }
  /* reports are filled in (59 phone, 599 CW) unless you change them (Brandon Oct 16: 'everyone is 59 unless we change it') */
  function modeSet() { const m = $('eMode').value, d = rstDef(m);
    ['eRs', 'eRr'].forEach(i => { const el = $(i); el.placeholder = d || '–'; if (!el.value || el.value === el.dataset.def) el.value = d; el.dataset.def = d; }); }
  function clearForm(keepRadio) {
    ['eCall', 'eRef', 'eName', 'eSt', 'eNote', 'eRs', 'eRr'].forEach(i => $(i).value = '');
    if (!keepRadio) { $('eFreq').value = ''; $('eBand').value = ''; }
    modeSet();
    $('eWho').innerHTML = ''; WHO = null; SPOTLL = null; lkN++; clearTimeout(lkT); if (EDIT) drawer(false); EDIT = null; $('eLog').textContent = '⬆'; $('eLog').setAttribute('aria-label', 'Log it'); $('eDel').hidden = true; $('dEdit').hidden = true;
    if ($('eManual').checked) { $('eManual').checked = false; $('eWhen').hidden = true; $('eTime').textContent = 'Time: now (UTC)'; }
  }
  function entryInit() {
    const lastF = get('kpcLgRadio', null); if (lastF) { $('eFreq').value = lastF.f || ''; $('eMode').value = lastF.m || 'SSB'; }
    bandSet(); modeSet();
    $('eCall').oninput = e => { const p = e.target.selectionStart; e.target.value = e.target.value.toUpperCase().replace(/\s/g, ''); try { e.target.setSelectionRange(p, p); } catch (x) {} clearTimeout(lkT); lkT = setTimeout(who, 450); };
    $('eFreq').oninput = () => { bandSet(); put('kpcLgRadio', { f: $('eFreq').value, m: $('eMode').value }); };
    $('eMode').onchange = () => { modeSet(); autoFreq('mode'); put('kpcLgRadio', { f: $('eFreq').value, m: $('eMode').value }); who(); };
    $('eBand').onchange = () => { autoFreq('band'); if (!$('eBand').value) return; if (bandOf(kHzOf($('eFreq').value)) !== $('eBand').value) { const D = DIAL[$('eMode').value] || DIAL.SSB; const f = D[$('eBand').value] || (BANDS.find(x => x[0] === $('eBand').value) || [0, 0])[1]; if (f) $('eFreq').value = mhz(f); } put('kpcLgRadio', { f: $('eFreq').value, m: $('eMode').value }); try { radioTxt(); } catch (e) {} };
    $('eRef').onblur = e => { e.target.value = anyRefs(e.target.value).join(', ') || e.target.value.toUpperCase(); };
    $('eSt').oninput = e => { e.target.value = e.target.value.toUpperCase(); };
    $('eClear').onclick = () => { clearForm(true); $('eCall').focus(); };
    $('eManual').onchange = e => { $('eWhen').hidden = !e.target.checked; if (e.target.checked && !$('eWhen').value) $('eWhen').value = iso(new Date()).slice(0, 16); $('eTime').textContent = e.target.checked ? 'Time: typed by hand (UTC)' : 'Time: now (UTC)'; };
    $('eForm').onsubmit = e => { e.preventDefault(); logIt(); };
    ['eCall', 'eRs', 'eRr', 'eSt', 'eRef', 'eName', 'eFreq', 'eNote'].forEach(i => $(i).addEventListener('keydown', e => { if ((e.key === 'Enter' || e.keyCode === 13) && !e.isComposing) { e.preventDefault(); logIt(); } }));
  }
  function logIt() {
    const call = $('eCall').value.toUpperCase().trim();
    if (!okCall(call)) { toast('Type their call sign first.'); $('eCall').focus(); return; }
    if (!myCall()) { toast('Put YOUR call in ⚙ STATION first.'); stationOpen(true); $('myCall').focus(); return; }
    if (!isHunt() && !myParks().length && !myWwff() && !mySota()) { toast('Put your park number in ⚙ STATION first (or switch to 🎯 HUNTING).'); stationOpen(true); $('myPark').focus(); return; }
    const k = kHzOf($('eFreq').value), band = bandOf(k);
    if (!k || !band) { toast('Type the frequency (like 14.285 or 14285).'); drawer(true); $('eFreq').focus(); return; }
    const mode = $('eMode').value;
    let when = new Date();
    if ($('eManual').checked && $('eWhen').value) { const w = new Date($('eWhen').value + ':00Z'); if (!isNaN(w)) when = w; }
    if (!EDIT) { const d = dupeOf(call, band, mode, anyRefs($('eRef').value).join(',')); if (d.length && !confirm(`${call} is already in your log ${isHunt() ? 'today' : 'this activation'} on ${band} ${mode}. Log it again anyway?`)) return; }
    const note = $('eNote').value.trim().slice(0, 600), cn = SET.carry || SET.prev ? notesTxt() : '';
    const r = WHO && WHO.call === base(call) ? WHO : {}, there = r.la != null ? [r.la, r.lo] : SPOTLL || fromGrid(r.g);
    const q = { id: EDIT ? EDIT.id : 'q' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6), call, d: ymd(when), tm: iso(when).slice(11, 16).replace(':', ''), t: EDIT ? EDIT.t : Date.now(),
      f: mhz(k), band, mode, rs: $('eRs').value.trim() || rstDef(mode), rr: $('eRr').value.trim() || rstDef(mode), ref: anyRefs($('eRef').value).join(','), name: $('eName').value.trim() || (r.name || '').split(' ')[0], st: ($('eSt').value.trim() || r.st || '').toUpperCase(),
      qth: r.qth || (EDIT && EDIT.qth) || '', g: r.g || (EDIT && EDIT.g) || '', la: there ? there[0] : (EDIT ? EDIT.la : null), lo: there ? there[1] : (EDIT ? EDIT.lo : null), note, cn: EDIT ? (EDIT.cn || '') : cn, role: EDIT ? (EDIT.role || 'act') : (isHunt() ? 'hunt' : 'act'),
      my: EDIT ? EDIT.my : stationCall(), op: EDIT ? (EDIT.op || EDIT.my) : curOp(), pk: EDIT ? EDIT.pk : (isHunt() ? '' : myParks().join(',')), wf: EDIT ? (EDIT.wf || '') : myWwff(), so: EDIT ? (EDIT.so || '') : mySota(), mg: EDIT ? EDIT.mg : SET.grid, pw: EDIT ? EDIT.pw : SET.pwr, x: 0 };
    if (EDIT) { const i = L.q.findIndex(x => x.id === EDIT.id); if (i >= 0) L.q[i] = q; toast('✓ Contact updated.'); }
    else { L.q.push(q); const n = actList().filter(x => x.my === q.my).length; toast(isHunt() ? `✓ ${call}${q.ref ? ' at ' + q.ref.split(',')[0] : ''} logged (${n} today)` : `✓ ${call} logged${multi() ? ' by ' + q.op : ''} (${n} this activation${multi() && !SET.share ? ' for ' + q.my : ''})${n === 10 ? ': 🎉 that makes it a valid activation!' : ''}`, () => { L.q = L.q.filter(x => x.id !== q.id); save(); drawAll(); }); NEWID = q.id;
      /* the effect flares only for a milestone (every 50 contacts in my log) or DX outside North America (Brandon Oct 17) */
      const tot = L.q.length, dx = isDX(call); if (tot % 50 === 0 || dx) { const fx = $('cEntry'); fx.classList.remove('pop'); void fx.offsetWidth; fx.classList.add('pop'); setTimeout(() => fx.classList.remove('pop'), 3200); const fm = dx ? `🌍 DX! ${call} is outside North America` : `🎉 ${tot} contacts in your log!`; if (window.KPCFx && !document.getElementById('lg').hasAttribute('data-night')) KPCFx(SET.fx, fm); else toast(fm); } }
    save(); clearForm(true); drawAll(); radioTxt(); $('eCall').focus();
    /* the look-up hadn't come back yet (typed fast): fill name / state / town / map spot in when it does */
    if (!r.call) look(call).then(x => { if (!x) return; const z = L.q.find(y => y.id === q.id); if (!z) return;
      if (!z.name) z.name = (x.name || '').split(' ')[0]; if (!z.st && x.st) z.st = String(x.st).toUpperCase(); if (!z.qth) z.qth = x.qth || ''; if (!z.g) z.g = x.g || '';
      if (z.la == null) { const ll = x.la != null ? [x.la, x.lo] : fromGrid(x.g); if (ll) { z.la = ll[0]; z.lo = ll[1]; } } save(); drawAll(); }).catch(() => {});
  }
  let NEWID = null;

  /* ---------------- log table ---------------- */
  let LV = 'act';
  const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function drawLog() {
    const s = $('lSearch').value.trim().toUpperCase();
    let R = (LV === 'act' ? actList() : L.q.slice()).sort((a, b) => tsOf(a) - tsOf(b) || a.t - b.t);
    if (s) R = R.filter(q => [q.call, q.ref, q.name, q.st, q.qth, q.pk, q.band, q.mode].join(' ').toUpperCase().includes(s));
    $('lCount').textContent = `${R.length} shown · ${L.q.length} in all`;
    $('tN').textContent = actList().length;
    if (!R.length) { $('lList').innerHTML = `<div class="lg-empty">${LV === 'act' ? (isHunt() ? 'No hunting contacts today yet. Tap a spot to fill in the call, frequency and park.' : myParks().length || myWwff() || mySota() ? 'No contacts in this activation yet. Tap a spot or type a call below.' : 'Put your park number in ⚙ STATION, then log away.') : 'Nothing logged yet.'}</div>`; return; }
    R = R.slice(-800); const out = []; let day = '';
    const byDay = {}; R.forEach(q => { byDay[q.d] = byDay[q.d] || []; byDay[q.d].push(q); });
    R.forEach(q => {
      if (q.d !== day) { day = q.d; const D = byDay[day], sts = new Set(D.map(x => x.st).filter(v => /^[A-Z]{2}$/.test(v))).size, refs = new Set(D.map(x => [x.pk, x.wf, x.so].filter(Boolean).join(' '))).size;
        out.push(`<div class="lg-day"><b>${MON[+day.slice(4, 6) - 1]} ${+day.slice(6, 8)}</b><span>${D.length} QSO${D.length > 1 ? 's' : ''}</span><i>${sts ? '🗺 ' + sts + ' states' : ''}${LV === 'all' ? ' · ' + esc([...new Set(D.map(x => x.pk || x.wf || x.so))].join(', ')) : ''}</i></div>`); }
      const f = String(q.f || ''), fi = f.split('.'), fk = fi.length > 1 ? `${fi[0]}.${(fi[1] + '000').slice(0, 3)}<small>.${(fi[1] + '0000').slice(3, 4)}</small>` : esc(f);
      out.push(`<div class="lr${q.id === NEWID ? ' new' : ''}${EDIT && EDIT.id === q.id ? ' ed' : ''}" data-ed="${q.id}" role="button" tabindex="0"><span class="t">${fT(q.tm)}z</span><span class="f">${fk}</span><span class="c">${esc(q.call)}${multi() || (q.op && q.op !== q.my) ? `<small>${esc(q.op || q.my)}</small>` : ''}</span><span class="s">${esc(q.st)}</span><span class="n">${esc(q.name)}</span><span class="p" title="${esc(q.ref)}">${q.ref ? '🌲' : ''}${q.note || q.cn ? '📝' : ''}</span><span class="r">${esc(q.rs)}</span><span class="r">${esc(q.rr)}</span></div>`);
    });
    $('lList').innerHTML = out.join('');
    if (!s) $('lList').scrollTop = $('lList').scrollHeight;
    NEWID = null;
  }
  function editStart(q) {
    EDIT = q;
    $('eCall').value = q.call; $('eFreq').value = q.f; $('eMode').value = q.mode; $('eRs').value = q.rs; $('eRr').value = q.rr; $('eRef').value = anyRefs(q.ref).join(', '); $('eName').value = q.name; $('eSt').value = q.st; $('eNote').value = q.note || '';
    $('eManual').checked = true; $('eWhen').hidden = false; $('eWhen').value = fD(q.d) + 'T' + fT(q.tm); $('eTime').textContent = 'Editing a saved contact';
    bandSet(); radioTxt(); $('eLog').textContent = '💾'; $('eLog').setAttribute('aria-label', 'Save changes'); $('eDel').hidden = false; $('dEdit').hidden = false; drawer(true); drawLog(); who(); $('eCall').focus();
  }
  function logInit() {
    document.querySelectorAll('[data-lv]').forEach(b => b.onclick = () => { LV = b.dataset.lv; document.querySelectorAll('[data-lv]').forEach(x => x.classList.toggle('on', x === b)); drawLog(); });
    $('lSearch').oninput = drawLog;
    const pick = e => { const r = e.target.closest('[data-ed]'); if (!r) return; const q = L.q.find(x => x.id === r.dataset.ed); if (q) editStart(q); };
    $('lList').onclick = pick; $('lList').onkeydown = e => { if (e.key === 'Enter') pick(e); };
    /* are you sure? before deleting (Brandon Oct 16) */
    $('eDel').onclick = () => {
      if (!EDIT) return; const i = L.q.findIndex(q => q.id === EDIT.id); if (i < 0) return; const dq = L.q[i];
      if (!confirm(`Are you sure? Delete ${dq.call} (${fT(dq.tm)}Z ${dq.band} ${dq.mode}) from your log?`)) return;
      const [gone] = L.q.splice(i, 1); clearForm(true); save(); drawAll(); toast(`🗑 ${gone.call} deleted.`, () => { L.q.push(gone); save(); drawAll(); });
    };
  }

  /* ---------------- the docked entry: radio chip, More drawer, tabs ---------------- */
  function radioTxt() { const k = kHzOf($('eFreq').value), b = bandOf(k); $('dRadioT').textContent = tabMode() ? `${b ? mhz(k) : 'Band???'} ${$('eMode').value}` : `${b ? mhz(k) + ' · ' + b : 'Band???'} · ${$('eMode').value}`; $('dRadio').classList.toggle('bad', !b); }
  /* phones: the radio row, More and ⚙ Station are pop-up menus over the log, one at a time (Brandon Oct 16) */
  function popOnly(w) { if (!tabMode()) return; if (w !== 'more' && !$('eMore').hidden) drawer(false); if (w !== 'radio' && document.getElementById('lg').hasAttribute('data-radio')) radioRow(false); if (w !== 'sta' && !$('cOp').hidden) stationOpen(false); }
  function drawer(open) { if (open) popOnly('more'); $('eMore').hidden = !open; $('dMoreB').classList.toggle('on', open); dockSize(); }
  function radioRow(open) { if (open) popOnly('radio'); const m = document.getElementById('lg'); m.toggleAttribute('data-radio', open); $('dRadio').setAttribute('aria-expanded', open); $('dRadio').classList.toggle('on', open); dockSize(); }
  const tabMode = () => matchMedia('(max-width:1099px)').matches;
  function rtab(t) { const m = document.getElementById('lg'); m.dataset.rt = t; put('kpcLgRt', t); document.querySelectorAll('[data-rt]').forEach(b => b.classList.toggle('on', b.dataset.rt === t)); if (t === 'map' && MAP) setTimeout(() => { MAP.invalidateSize(); drawMap(true); }, 60); }
  function tab(t, quiet) {
    const m = document.getElementById('lg'); m.dataset.tab = t; put('kpcLgTab', t);
    document.querySelectorAll('[data-tab]').forEach(b => b.classList.toggle('on', b.dataset.tab === t));
    if (t === 'map' && MAP) setTimeout(() => { MAP.invalidateSize(); drawMap(true); }, 60);
    if (t === 'log') setTimeout(drawLog, 30);
    if (tabMode()) scrollTo(0, 0);
  }
  const hdrH = () => { const h = document.querySelector('header.site-nav, header'); return h ? Math.max(0, h.getBoundingClientRect().bottom) : 0; };
  function dockSize() { const m = document.getElementById('lg'); m.style.setProperty('--dock', $('cEntry').offsetHeight + 'px'); m.style.setProperty('--hdr', hdrH() + 'px'); }
  /* phones: when the keyboard is up, give the log the room (Brandon Oct 17 picture): fit the app to the visible part of the
     screen, hide the extras, newest contacts right above the entry line */
  let VVMAX = 0;
  function vvFit() {
    const vv = window.visualViewport, m = document.getElementById('lg'); if (!vv) return;
    if (!tabMode()) { m.removeAttribute('data-kb'); return; }
    VVMAX = Math.max(VVMAX, vv.height); const ae = document.activeElement, typing = ae && /^(INPUT|SELECT|TEXTAREA)$/.test(ae.tagName) && ae.type !== 'checkbox';
    const kb = typing && vv.height < VVMAX - 120, was = m.hasAttribute('data-kb'); m.toggleAttribute('data-kb', kb);
    m.style.setProperty('--vvh', Math.round(vv.height) + 'px'); m.style.setProperty('--vvt', Math.round(vv.offsetTop) + 'px');
    m.style.setProperty('--kbb', Math.max(0, Math.round(innerHeight - vv.height - vv.offsetTop)) + 'px');
    dockSize(); if (kb && !was) { const l = document.querySelector('#cLog .lg-list'); if (l) setTimeout(() => { l.scrollTop = l.scrollHeight; }, 60); }
  }
  if (window.visualViewport) { visualViewport.addEventListener('resize', vvFit); visualViewport.addEventListener('scroll', vvFit); addEventListener('orientationchange', () => { VVMAX = 0; setTimeout(vvFit, 400); }); document.addEventListener('focusin', () => setTimeout(vvFit, 350)); document.addEventListener('focusout', () => setTimeout(vvFit, 350)); }
  function dockInit() {
    $('dRadio').onclick = () => { radioRow(!document.getElementById('lg').hasAttribute('data-radio')); if (document.getElementById('lg').hasAttribute('data-radio')) $('eFreq').focus(); };
    $('dMoreB').onclick = () => drawer($('eMore').hidden);
    document.querySelectorAll('[data-rt]').forEach(b => b.onclick = () => rtab(b.dataset.rt)); rtab(get('kpcLgRt', 'spots'));
    $('dSta').onclick = () => { stationOpen($('cOp').hidden); return; if (tabMode()) scrollTo({ top: $('cOp').getBoundingClientRect().top + scrollY - hdrH() - 8, behavior: 'smooth' }); else $('cOp').scrollIntoView({ behavior: 'smooth' }); };
    document.querySelectorAll('[data-tab]').forEach(b => b.onclick = () => tab(b.dataset.tab));
    tab(({ stats: 'info', notes: 'log', station: 'log' })[get('kpcLgTab', 'log')] || get('kpcLgTab', 'log'), true);
    ['eFreq', 'eMode'].forEach(i => $(i).addEventListener('input', radioTxt)); $('eMode').addEventListener('change', radioTxt); radioTxt();
    if (!kHzOf($('eFreq').value) && !tabMode()) radioRow(true);
    document.addEventListener('click', e => { const x = e.target.closest('[data-popx]'); if (x) { if (x.dataset.popx === 'radio') radioRow(false); else drawer(false); return; }
      if (tabMode() && !e.target.closest('#cEntry') && !e.target.closest('.lg-toast')) popOnly(''); });
    $('dRole').onclick = () => { role(isHunt() ? 'act' : 'hunt'); toast(isHunt() ? '🎯 Hunting: no park number needed. Tap a spot, log it, and the park goes with the contact.' : '🏕 Activating: your park number goes on every contact.'); };
    if (window.ResizeObserver) new ResizeObserver(dockSize).observe($('cEntry')); addEventListener('resize', dockSize); setTimeout(dockSize, 100);
  }

  /* ---------------- ADIF / CSV ---------------- */
  const enc = new TextEncoder();
  const af = (k, v) => { v = String(v == null ? '' : v).replace(/[<>]/g, ''); return v === '' ? '' : `<${k}:${enc.encode(v).length}>${v} `; };
  function adMode(m) { m = String(m || '').toUpperCase(); if (m === 'FT4') return ['MFSK', 'FT4']; if (m === 'FT2') return ['MFSK', 'FT2']; if (m === 'JS8') return ['MFSK', 'JS8']; if (m === 'PSK31') return ['PSK', 'PSK31']; if (m === 'OTHER') return ['', '']; return [m, '']; }
  function adif(Q, onePark, prog) {
    let o = `KPC Activator Logger\n${af('ADIF_VER', '3.1.4')}${af('PROGRAMID', 'KPC Activator Logger')}${af('CREATED_TIMESTAMP', iso(new Date()).replace(/[-:]/g, '').replace('T', ' ').slice(0, 15))}<EOH>\n`;
    Q.forEach(q => {
      const [md, sm] = adMode(q.mode), T = byProg(q.ref), their = T.pota, mine = onePark ? [onePark] : refsOf(q.pk), p0 = prog === 'WWFF' ? '' : (mine[0] || ''), pi = SET.pinfo[mine[0]] || {};
      const mySig = prog === 'WWFF' ? ['WWFF', q.wf] : p0 ? ['POTA', p0] : q.wf ? ['WWFF', q.wf] : ['', ''];
      const thSig = prog === 'WWFF' ? (T.wwff[0] ? ['WWFF', T.wwff[0]] : ['', '']) : their[0] ? ['POTA', their[0]] : T.wwff[0] ? ['WWFF', T.wwff[0]] : ['', ''];
      const myst = (String(pi.st || '').match(/^US-([A-Z]{2})$/) || [])[1] || '';
      o += af('CALL', q.call) + af('QSO_DATE', q.d) + af('TIME_ON', q.tm) + af('BAND', q.band) + af('FREQ', q.f) + af('MODE', md) + af('SUBMODE', sm) + af('RST_SENT', q.rs) + af('RST_RCVD', q.rr)
        + af('STATION_CALLSIGN', q.my) + af('OPERATOR', base(q.op || q.my)) + af('MY_SIG', mySig[0]) + af('MY_SIG_INFO', mySig[1]) + af('MY_POTA_REF', prog === 'WWFF' ? '' : mine.join(',')) + af('MY_WWFF_REF', q.wf) + af('MY_SOTA_REF', q.so) + af('MY_GRIDSQUARE', q.mg) + af('MY_STATE', myst) + af('TX_PWR', q.pw)
        + af('SIG', thSig[0]) + af('SIG_INFO', thSig[1]) + af('POTA_REF', their.join(',')) + af('WWFF_REF', T.wwff[0] || '') + af('SOTA_REF', T.sota[0] || '')
        + af('NAME', q.name) + af('QTH', q.qth) + af('STATE', /^[A-Z]{2}$/.test(q.st) ? q.st : '') + af('GRIDSQUARE', q.g)
        + af('COMMENT', [anyRefs(q.ref).length ? 'P2P ' + anyRefs(q.ref).join(' ') : '', q.name].filter(Boolean).join(' ').slice(0, 120)) + af('NOTES', [q.note, q.cn].filter(Boolean).join(' · ')) + '<EOR>\n';
    });
    return o;
  }
  /* SOTA activator CSV for sotadata.org.uk: V2,my call,my summit,dd/mm/yy,HHMM,frequency,mode,their call,their summit,notes */
  function sotaCsv(Q, so, c) {
    return Q.map(q => { const ts = byProg(q.ref).sota[0] || '', dt = q.d.slice(6, 8) + '/' + q.d.slice(4, 6) + '/' + q.d.slice(2, 4);
      return ['V2', c, so, dt, q.tm, q.f + 'MHz', String(q.mode || '').replace(/^OTHER$/, 'Other'), q.call, ts, String([q.note, q.cn].filter(Boolean).join(' · ')).replace(/[,\n\r]/g, ' ').slice(0, 120)].join(','); }).join('\r\n') + '\r\n';
  }
  function parseAdif(t) {
    const out = []; t = String(t || ''); const h = t.search(/<eoh>/i); if (h >= 0) t = t.slice(h + 5);
    t.split(/<eor>/i).forEach(rec => {
      const r = {}; const re = /<(\w+):(\d+)(?::\w)?>/g; let m;
      while ((m = re.exec(rec))) { r[m[1].toUpperCase()] = rec.substr(re.lastIndex, +m[2]); re.lastIndex += +m[2]; }
      if (!r.CALL || !r.QSO_DATE || !r.TIME_ON) return;
      const k = kHzOf(r.FREQ), g = r.GRIDSQUARE || '', ll = fromGrid(g);
      out.push({ id: 'i' + Math.random().toString(36).slice(2, 10), call: r.CALL.toUpperCase(), d: r.QSO_DATE, tm: String(r.TIME_ON).slice(0, 4), t: 0, f: k ? mhz(k) : '', band: (r.BAND || bandOf(k)).toLowerCase(), mode: r.SUBMODE || r.MODE || '',
        rs: r.RST_SENT || '', rr: r.RST_RCVD || '', ref: anyRefs([r.POTA_REF, r.WWFF_REF, r.SOTA_REF, /^(POTA|WWFF)$/.test(r.SIG || '') ? r.SIG_INFO : ''].filter(Boolean).join(',')).join(','), wf: wwffN(r.MY_WWFF_REF || (r.MY_SIG === 'WWFF' ? r.MY_SIG_INFO : '')), so: sotaN(r.MY_SOTA_REF || ''), name: r.NAME || '', st: r.STATE || '', qth: r.QTH || '', g, la: ll ? ll[0] : null, lo: ll ? ll[1] : null,
        note: r.NOTES || '', my: (r.STATION_CALLSIGN || r.OPERATOR || myCall()).toUpperCase(), pk: refsOf(r.MY_POTA_REF || (r.MY_SIG === 'POTA' || !r.MY_SIG ? r.MY_SIG_INFO : '')).join(','), mg: r.MY_GRIDSQUARE || '', pw: r.TX_PWR || '', x: 1 });
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
    $('xPota').onclick = async () => { const F = buildFiles(); if (!F) return; const ok = await files(F.list); if (ok !== false) { F.A.forEach(q => q.x = 1); save(); toast(F.msg); } };
    $('xMail').onclick = async () => {
      const F = buildFiles(); if (!F) return;
      const subj = `${isHunt() ? 'Hunting log' : 'POTA log'} ${stationCall() || myCall()} ${myRefsTxt()} ${fD(F.A[0].d)}`.replace(/\s+/g, ' ').trim();
      const body = `${subj}\n${F.A.length} contacts.\nFiles: ${F.list.map(f => f[0]).join(', ')}\n\nMade with the KPC Logger (Kentucky Portable Club).`;
      try { const FF = F.list.map(([n, t, ty]) => new File([t], n, { type: ty || 'text/plain' })); if (navigator.canShare && navigator.canShare({ files: FF })) { await navigator.share({ files: FF, title: subj, text: body }); F.A.forEach(q => q.x = 1); save(); return; } } catch (e) { if (e && e.name === 'AbortError') return; }
      await dl(F.list); F.A.forEach(q => q.x = 1); save();
      setTimeout(() => { location.href = 'mailto:?subject=' + encodeURIComponent(subj) + '&body=' + encodeURIComponent(body + '\n\n(The files just downloaded: attach them to this email.)'); }, 900);
      toast('⬇ Files downloaded. Your email opens next: attach the files from your Downloads folder.');
    };
    function buildFiles() {
      const A = actList(); if (!A.length) { toast(isHunt() ? 'No hunting contacts today yet.' : 'No contacts in this activation yet.'); return null; }
      if (isHunt()) { const d = A[0].d, fc = (stationCall() || myCall() || 'mine').replace(/\//g, '-');
        return { A, list: [[`${fc}-hunting-${d}.adi`, adif(A)]], msg: `⬇ Your hunting log for today (${A.length} contacts). Upload it to QRZ, LoTW or your logging program. POTA gives hunters credit from the activators' logs.` }; }
      const P = myParks(), W = myWwff(), So = mySota(); if (!P.length && !W && !So) { toast('Put your park number in ⚙ STATION first.'); return null; }
      const d = A[0].d, calls = [...new Set(A.map(q => q.my))], F = [], short = [];
      calls.forEach(c => { const Q = A.filter(q => q.my === c), fc = c.replace(/\//g, '-');
        if (P.length && Q.length < 10) short.push(`${c} POTA ${Q.length}/10`); if (W && Q.length < 44) short.push(`${c} WWFF ${Q.length}/44`);
        P.forEach(p => F.push([`${fc}@${p}-${d}.adi`, adif(Q, p)]));                                   /* POTA: one file per park, CALL@PARK-YYYYMMDD.adi */
        if (W) F.push([`${fc}@${W} ${d}.adi`, adif(Q, null, 'WWFF')]);                                 /* WWFF: CALL@REF YYYYMMDD.adi, for your WWFF log manager */
        if (So) F.push([`${fc}-${So.replace('/', '_')}-${d}.csv`, sotaCsv(Q, So, c), 'text/csv']); /* SOTA: sotadata.org.uk activator CSV (V2) */ });
      return { A, list: F, msg: `⬇ ${F.length} file${F.length > 1 ? 's' : ''} (${A.length} contacts)${short.length ? '. Not enough yet: ' + short.join(', ') : ''}.` };
    }
    /* ☁ SEND TO QRZ at the end (Brandon Oct 17), one contact at a time; kpcQrz key shared with the Hunters Lounge */
    if ($('xQz') && window.KPCQrz) {
      const qm = h => { $('xQzMsg').innerHTML = h; };
      const one = q => { const a = adif([q]); return a.slice(a.indexOf('<EOH>') + 5).trim(); };
      const showKey = () => { const Z = KPCQrz.get(); $('xQzKey').value = Z.key || ''; const n = L.q.filter(q => !q.qz).length; qm(Z.key ? `Key saved. ${n ? n + ' contact' + (n === 1 ? '' : 's') + ' not sent to QRZ yet.' : 'Everything has been sent.'}` : 'No QRZ key saved on this device yet.'); };
      $('xQzSave').onclick = () => { const k = $('xQzKey').value.trim(); if (!/^[A-Z0-9-]{8,}$/i.test(k)) { qm('That doesn\'t look like a QRZ logbook key.'); return; } KPCQrz.set({ key: k }); showKey(); };
      $('xQzForget').onclick = () => { if (!confirm('Forget your QRZ key on this device?')) return; KPCQrz.set({ key: '', on: false }); showKey(); };
      async function qzSend(list) {
        if (!KPCQrz.get().key) { qm('Paste your QRZ logbook key and tap SAVE KEY first.'); return; }
        if (!list.length) { qm('Nothing to send.'); return; }
        if (list.some(q => q.qz) && !confirm(`${list.filter(q => q.qz).length} of these were sent before. Send them again? (QRZ will call them duplicates.)`)) list = list.filter(q => !q.qz);
        let ok = 0, bad = 0, last = '';
        for (let i = 0; i < list.length; i++) { qm(`Sending ${i + 1} of ${list.length}…`); const r = await KPCQrz.send(one(list[i])); if (r.ok) { ok++; list[i].qz = r.sure ? 2 : 1; } else { bad++; last = r.msg; } await new Promise(z => setTimeout(z, 350)); }
        save(); qm(`☁ Sent ${ok} contact${ok === 1 ? '' : 's'} to QRZ${bad ? ` · ${bad} did not go (${last})` : ''}.` + (await KPCQrz.relay() ? '' : ' QRZ doesn\'t let a web page see its reply, so tap <b>🔎 SEE QRZ\'S ANSWER</b> once (OK or duplicate = it worked) or check your QRZ logbook.'));
      }
      $('xQzAct').onclick = () => qzSend(L.q.filter(inAct).sort((a, b) => a.t - b.t));
      $('xQzNew').onclick = () => qzSend(L.q.filter(q => !q.qz).sort((a, b) => a.t - b.t));
      $('xQzSee').onclick = () => { if (!KPCQrz.get().key) { qm('Save your QRZ key first.'); return; } const q = L.q.slice().sort((a, b) => b.t - a.t)[0]; if (!q) { qm('Nothing logged yet.'); return; }
        KPCQrz.showAnswer('INSERT', one(q)); qm(`A new tab opened with QRZ's own answer for <b>${q.call}</b>: <b>OK</b> = it's in, <b>duplicate</b> = it was already there, <b>FAIL</b> = the REASON says why (often the key is for a different logbook than the call you were on).`); };
      showKey();
    }
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
      if (SET.notes && confirm('Clear the notes too?')) { SET.notes = ''; $('nText').value = ''; }
      saveSet(); drawAll(); toast('🏁 New activation started. Change your park number if you moved.'); $('myPark').focus();
    };
  }

  /* North America by call prefix (US, Canada, Mexico, Central America, Caribbean, Greenland); anything else counts as DX */
  const NAPRE = /^(A[A-L]|[KNW]|V[A-GOY]|C[F-KYZ]|X[A-O]|4[A-C]|6[D-J]|C[LMO]|T[GI]|H[O-RI]|YN|YS|V[23P]|J[3678]|8P|6Y|ZF|C6|FG|FM|FS|PJ|P4|HH|OX|XP|TO|FP|ZB)/;
  const isDX = c => { c = String(c || '').toUpperCase().split('/').reduce((a, b) => b.length > a.length ? b : a, ''); return c.length > 2 && !NAPRE.test(c); };
  /* ---------------- POTA spots ---------------- */
  let SP = [], SPP = [], SPS = [], SPW = [], SPD = [], wwAt = 0, spT = null, spAt = 0;
  const PICON = { POTA: '🌲', WWFF: '🌳', SOTA: '⛰', DX: '🌐' };
  async function spots() {
    /* POTA + SOTA every minute, WWFF (from Spothole, about 1 MB) every 3 minutes; all turned into the POTA spot shape (Brandon Oct 17) */
    const jg = (u, ms) => { const c = new AbortController(), t = setTimeout(() => c.abort(), ms); return fetch(u, { cache: 'no-store', signal: c.signal }).then(r => r.ok ? r.json() : Promise.reject(r.status)).finally(() => clearTimeout(t)); };
    const kh = f => { f = Number(f); return !isFinite(f) || f <= 0 ? 0 : f < 1000 ? f * 1000 : f < 1e6 ? f : f / 1000; };
    const ms = v => { if (v == null) return Date.now(); if (typeof v === 'number') return v < 1e12 ? v * 1000 : v; const s = String(v); const d = Date.parse(/[zZ]|[+-]\d\d:?\d\d$/.test(s) ? s : s + 'Z'); return isFinite(d) ? d : Date.now(); };
    const P = jg('https://api.pota.app/spot/activator', 25000).then(j => { SPP = (Array.isArray(j) ? j : []).map(x => Object.assign(x, { prog: 'POTA', _t: ms(x.spotTime), frequency: kh(x.frequency) })); return 1; }).catch(() => 0);
    const S = jg('https://api2.sota.org.uk/api/spots/50/all', 25000).then(j => { SPS = (j || []).map(x => ({ spotId: 'S' + (x.id || x.timeStamp + x.activatorCallsign), prog: 'SOTA', activator: String(x.activatorCallsign || '').toUpperCase(), frequency: kh(x.frequency), mode: x.mode || '', reference: ((x.associationCode || '') + '/' + (x.summitCode || '')).toUpperCase(), name: x.summitDetails || '', locationDesc: x.associationCode || '', _t: ms(x.timeStamp), comments: x.comments || '', spotter: x.callsign || '', source: '' })).filter(x => x.frequency && x.activator); return 1; }).catch(() => 0);
    let W = Promise.resolve(1);
    if (Date.now() - wwAt > 175000) W = jg('https://spothole.app/api/v1/spots?max_age=2700', 60000).then(j => { const L = Array.isArray(j) ? j : (j && j.spots) || []; wwAt = Date.now();
      SPW = L.filter(x => /WWFF/i.test(x.sig || '') && !/RBN|SKIM/i.test(x.source || '')).map((x, i) => { const rr = x.sig_refs || []; const r0 = (Array.isArray(rr) ? rr : [rr]).map(v => typeof v === 'string' ? { id: v } : v)[0] || {};
        return { spotId: 'W' + (x.id || i + '-' + x.time), prog: 'WWFF', activator: String(x.dx_call || '').toUpperCase(), frequency: kh(x.freq != null ? x.freq : x.frequency), mode: x.mode || '', reference: String(r0.id || r0.ref || '').toUpperCase(), name: r0.name || '', locationDesc: x.dx_state ? 'US-' + x.dx_state : (x.dx_country || ''), _t: ms(x.time), comments: x.comment || '', spotter: x.de_call || '', source: '', latitude: x.dx_latitude, longitude: x.dx_longitude }; })
        .filter(x => x.frequency && x.activator && x.reference);
      /* DX cluster (Brandon Oct 17: 'add dx cluster option to spots on loggers'): every other Spothole spot with no program, skimmers / RBN / PSK Reporter left out */
      SPD = L.filter(x => !x.sig && !/RBN|SKIM|PSK|WSPR|REVERSE/i.test(x.source || '') && !/-#$/.test(x.de_call || '')).map((x, i) => ({ spotId: 'D' + (x.id || i + '-' + x.time), prog: 'DX', activator: String(x.dx_call || '').toUpperCase(), frequency: kh(x.freq != null ? x.freq : x.frequency), mode: x.mode || '', reference: '', name: x.dx_country || '', locationDesc: x.dx_state ? 'US-' + x.dx_state : '', _t: ms(x.time), comments: x.comment || '', spotter: x.de_call || '', source: x.source || '', latitude: x.dx_latitude, longitude: x.dx_longitude }))
        .filter(x => x.frequency && x.activator); return 1; }).catch(() => 0);
    const ok = await Promise.all([P, S, W]); SP = SPP.concat(SPW, SPS, SPD); if (ok.some(Boolean)) spAt = Date.now();
    if (!SP.length && !ok.some(Boolean)) $('pList').innerHTML = '<div class="lg-empty">The spot sites are not answering right now (or no signal). Trying again in a minute.</div>';
    drawSpots(); clearTimeout(spT); spT = setTimeout(spots, 60000);
  }
  const spMode = s => { const m = String(s.mode || '').toUpperCase(); return /^(USB|LSB|SSB|PHONE)$/.test(m) ? 'SSB' : m; };
  const isRbn = s => /RBN/i.test(s.source || '') || /-#$/.test(s.spotter || '');
  function drawSpots() {
    const b = $('pBand').value, m = $('pMode').value, nr = $('pNoRbn').checked, nw = $('pNoWk').checked, s = $('pSearch').value.trim().toUpperCase();
    const pg = { POTA: $('pPota').checked, WWFF: $('pWwff').checked, SOTA: $('pSota').checked, DX: $('pDx').checked };
    const nOn = [!!b, !!m, nw, !pg.POTA, !pg.WWFF, !pg.SOTA, pg.DX, !!s].filter(Boolean).length; $('pfN').textContent = nOn ? nOn + ' ON' : '';
    const worked = new Set(actList().map(q => base(q.call) + '|' + q.band));
    let R = SP.filter(x => { const k = +x.frequency, md = spMode(x);
      if (!pg[x.prog || 'POTA']) return false; if (nr && isRbn(x)) return false; if (nw && worked.has(base(x.activator) + '|' + bandOf(k))) return false; if (b && bandOf(k) !== b) return false;
      if (m && !(m === 'DATA' ? DIGI.test(md) || /DATA|RTTY|PSK/.test(md) : md === m)) return false;
      if (s && ![x.activator, x.reference, x.name, x.locationDesc, x.comments].join(' ').toUpperCase().includes(s)) return false; return true; });
    const BO = BANDS.map(b => b[0]); R.sort((a, c) => BO.indexOf(bandOf(+a.frequency)) - BO.indexOf(bandOf(+c.frequency)) || (+a.frequency) - (+c.frequency));
    $('pAge').textContent = spAt ? `${R.length} shown · updated ${new Date(spAt).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}` : '';
    /* TABLE like the Hunters Lounge (Brandon Oct 17: 'make it like the hunters lounge table view… and the sort by features'):
       tap a heading to sort (tap again to flip); saved in kpcLgSpSort; tap a row = fill the log */
    const AGE = x => Math.max(0, Math.round((Date.now() - (x._t || Date.parse(x.spotTime + 'Z'))) / 6e4));
    const SO = SPSORT.k, dir = SPSORT.d;
    const key = { when: x => AGE(x), call: x => base(x.activator), freq: x => +x.frequency, mode: x => spMode(x), park: x => String(x.reference || '') }[SO] || (x => +x.frequency);
    R.sort((a, c) => { const A = key(a), C = key(c); return (A < C ? -1 : A > C ? 1 : 0) * dir || (+a.frequency) - (+c.frequency); });
    const th = (k, n, c) => `<th class="srt${SO === k ? ' on' : ''}${c ? ' ' + c : ''}" data-srt="${k}" title="Sort by this">${n}${SO === k ? (dir > 0 ? ' ▴' : ' ▾') : ''}</th>`;
    $('pList').innerHTML = R.length ? `<table class="lg-st"><thead><tr>${th('when', 'WHEN', 'hs')}${th('call', 'CALL')}${th('freq', 'MHz')}${th('mode', 'MODE', 'hs')}${th('park', 'PARK / REF / WHERE')}<th></th></tr></thead><tbody>` + R.slice(0, 200).map(x => {
      const k = +x.frequency, w = worked.has(base(x.activator) + '|' + bandOf(k)), ago = AGE(x);
      const st = x.locationDesc ? String(x.locationDesc).split(',')[0].replace(/^US-/, '') : '';
      return `<tr class="sp${w ? ' wk' : ''}" data-sp="${x.spotId}"><td class="t hs">${ago < 60 ? ago + 'm' : Math.floor(ago / 60) + 'h'}</td><td class="c">${esc(x.activator)}${w ? ' <i>✓</i>' : ''}</td><td class="f">${(k / 1000).toFixed(3)}<small>${esc(bandOf(k))}</small></td><td class="hs">${esc(spMode(x) || '?')}</td><td class="r"><b>${PICON[x.prog] || '🌲'} ${esc(x.reference || (x.prog === 'DX' ? 'DX' : ''))}</b><small>${esc(x.name || '')}${st ? ' · ' + esc(st) : ''}</small>${x.comments && !isRbn(x) ? `<small class="x">${esc(String(x.comments).slice(0, 70))}</small>` : ''}</td><td class="a">${(x.prog || 'POTA') === 'POTA' ? `<span class="rs" data-respot="${x.spotId}" role="button" tabindex="0" title="Respot them on POTA">📣</span>` : ''}</td></tr>`; }).join('') + '</tbody></table>'
      : `<div class="lg-empty">${SP.length ? 'No spots match these choices.' : 'Loading spots…'}</div>`;
  }
  let SPSORT = Object.assign({ k: 'freq', d: 1 }, get('kpcLgSpSort', {}));
  document.addEventListener('click', e => { const h = e.target.closest('#pList th[data-srt]'); if (!h) return; const k = h.dataset.srt;
    SPSORT = SPSORT.k === k ? { k, d: -SPSORT.d } : { k, d: k === 'when' ? 1 : 1 }; put('kpcLgSpSort', SPSORT); drawSpots(); });
  function spotsInit() {
    $('pBand').innerHTML = '<option value="">All bands</option>' + BANDS.slice(0, 11).map(b => `<option>${b[0]}</option>`).join('');
    ['pBand', 'pMode', 'pNoRbn', 'pNoWk', 'pPota', 'pWwff', 'pSota', 'pDx'].forEach(i => $(i).onchange = () => { put('kpcLgSpF', { b: $('pBand').value, m: $('pMode').value, r: $('pNoRbn').checked, w: $('pNoWk').checked, pp: $('pPota').checked, pw: $('pWwff').checked, ps: $('pSota').checked, pd: $('pDx').checked }); if (i === 'pDx' && $('pDx').checked) wwAt = 0, spots(); drawSpots(); });
    const f = get('kpcLgSpF', null); if (f) { $('pBand').value = f.b || ''; $('pMode').value = f.m || ''; $('pNoRbn').checked = f.r !== false; $('pNoWk').checked = !!f.w; $('pPota').checked = f.pp !== false; $('pWwff').checked = f.pw !== false; $('pSota').checked = f.ps !== false; $('pDx').checked = !!f.pd; }
    $('pSearch').oninput = drawSpots;
    $('pList').onclick = e => {
      const btn = e.target.closest('[data-sp]'); if (!btn) return; const x = SP.find(s => String(s.spotId) === btn.dataset.sp); if (!x) return;
      /* an FT8 / FT4 station: tab over to the FT8 screen (Brandon Oct 17) */
      if (/^(FT8|FT4)$/.test(spMode(x)) && window.KPCFT8UI) { window.KPCFT8UI.go({ call: String(x.activator || '').toUpperCase(), khz: +x.frequency, mode: spMode(x), ref: x.reference || '', prog: x.prog }); return; }
      clearForm(false); EDIT = null;
      $('eCall').value = String(x.activator || '').toUpperCase(); $('eFreq').value = mhz(+x.frequency);
      const md = spMode(x); $('eMode').value = [...$('eMode').options].some(o => o.value === md) ? md : 'OTHER';
      $('eRef').value = x.reference || ''; bandSet(); modeSet(); put('kpcLgRadio', { f: $('eFreq').value, m: $('eMode').value });
      SPOTLL = x.latitude != null ? [+x.latitude, +x.longitude] : null;
      radioTxt(); who(); catTune(true); if (tabMode()) tab('log'); if ($('eRadio').offsetParent === null && tabMode()) { /* phone: radio row folded */ }
      setTimeout(() => $('eRs').focus(), 350);
    };
    spots();
    document.addEventListener('visibilitychange', () => { if (!document.hidden && Date.now() - spAt > 60000) spots(); });
  }

  /* ---------------- self spot ---------------- */
  function rlCheck(kind) { const t = Date.now(), Q = (get('kpcSpotMeSent', []) || []).filter(x => t - x < 36e5);
    if (kind === 'qrt') { if (Q.length && t - Q[Q.length - 1] < 6e4) return 'Wait a minute after your last spot.'; if (Q.length >= 6) return 'Too many spots this hour.'; return ''; }
    if (Q.length && t - Q[Q.length - 1] < 3e5) return 'Please wait ' + Math.ceil((3e5 - (t - Q[Q.length - 1])) / 6e4) + ' more minute(s): one POTA spot every 5 minutes.';
    if (Q.length >= 4) return 'That\'s 4 POTA spots this hour. Try again in ' + Math.ceil((36e5 - (t - Q[0])) / 6e4) + ' minute(s).'; return ''; }
  function rlNote() { const Q = (get('kpcSpotMeSent', []) || []).filter(x => Date.now() - x < 36e5); Q.push(Date.now()); put('kpcSpotMeSent', Q); }
  function spotInit() {
    const msg = (t, c) => { $('sMsg').className = 'lg-msg ' + (c || ''); $('sMsg').textContent = t; toast(t); };
    $('sQrt').onclick = () => sendSpot('qrt'); $('sQsy').onclick = () => sendSpot('qsy');
    $('sSend').onclick = () => sendSpot('');
    $('dSpot').onclick = () => sendSpot('');
    $('pList').addEventListener('click', e => { const b = e.target.closest('[data-respot]'); if (!b) return; e.stopPropagation(); const x = SP.find(s => String(s.spotId) === b.dataset.respot); if (x) respot(x); }, true);
    /* hunters: spot the activator in the call box (the POTA way to say thanks) */
    async function spotThem() {
      const them = $('eCall').value.toUpperCase().trim(), ref = byProg($('eRef').value).pota[0], k = kHzOf($('eFreq').value), mode = $('eMode').value === 'OTHER' ? '' : $('eMode').value;
      if (!okCall(them) || !ref) { msg('Type (or tap a spot for) the activator\'s call and park first.', 'bad'); return; }
      if (!k || !bandOf(k)) { msg('Set the frequency first.', 'bad'); drawer(true); return; }
      if (!myCall()) { msg('Put your call in ⚙ STATION first.', 'bad'); stationOpen(true); return; }
      const wait = rlCheck(); if (wait) { msg(wait, 'bad'); return; }
      const cm = ($('sCm').value.trim() || 'Thanks!').slice(0, 60);
      if (!confirm(`Spot ${them} at ${ref} on ${mhz(k)} MHz ${mode} on POTA, from ${myCall()}?\n${cm}`)) return;
      try { const r = await fetch('https://api.pota.app/spot/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ activator: them, spotter: base(myCall()), frequency: String(Math.round(k * 10) / 10), reference: ref, mode, source: 'KPC Logger', comments: cm }) });
        const body = await r.text().catch(() => ''); if (r.ok) { rlNote(); msg(`✓ Spotted ${them} at ${ref}.`, 'ok'); setTimeout(spots, 8000); } else msg('✗ POTA turned it down: ' + (String(body).replace(/^"|"$/g, '') || 'error ' + r.status), 'bad'); }
      catch (e) { msg('✗ POTA could not be reached. Check your signal.', 'bad'); }
    }
    /* RESPOT a station from the spots list (hunters and activators alike): same frequency, mode and park, me as the spotter */
    async function respot(x) {
      const k = +x.frequency, mode = spMode(x), ref = x.reference;
      if (!myCall()) { msg('Put your call in ⚙ first.', 'bad'); stationOpen(true); return; }
      const wait = rlCheck(); if (wait) { msg(wait, 'bad'); return; }
      const c0 = prompt(`Respot ${x.activator} at ${ref} on ${mhz(k)} ${mode}?\nComment (optional):`, $('sCm').value.trim() || 'Thanks!'); if (c0 === null) return; const cm = c0.slice(0, 60);
      try { const r = await fetch('https://api.pota.app/spot/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ activator: x.activator, spotter: base(myCall()), frequency: String(k), reference: ref, mode, source: 'KPC Logger', comments: cm }) });
        const body = await r.text().catch(() => ''); if (r.ok) { rlNote(); msg(`✓ Respotted ${x.activator} at ${ref}.`, 'ok'); setTimeout(spots, 8000); } else msg('✗ POTA turned it down: ' + (String(body).replace(/^"|"$/g, '') || 'error ' + r.status), 'bad'); }
      catch (e) { msg('✗ POTA could not be reached. Check your signal.', 'bad'); }
    }
    async function sendSpot(kind) {
      if (isHunt()) { msg('Hunting: use RESPOT on a spot in the SPOTS list to spot an activator.', 'bad'); return; }
      const call = stationCall(), P = myParks(), k = kHzOf($('eFreq').value), mode = $('eMode').value === 'OTHER' ? '' : $('eMode').value;
      if (!call) { msg('Put your call in ⚙ STATION first.', 'bad'); stationOpen(true); return; }
      if (!P.length) { msg('Put your park number in ⚙ STATION first.', 'bad'); stationOpen(true); return; }
      if (!k || !bandOf(k)) { msg('Type the frequency you are on (like 14.285).', 'bad'); drawer(true); return; }
      const wait = rlCheck(kind); if (wait) { msg(wait, 'bad'); return; }
      let cm = kind === 'qrt' ? 'QRT · thanks all, 73!' : kind === 'qsy' ? ('QSY · now on ' + mhz(k) + ' ' + $('sCm').value.trim()).trim() : $('sCm').value.trim();
      if (kind !== 'qrt' && P.length > 1 && !/fer|US-|\d{4}/i.test(cm)) cm = (P.length + '-fer: ' + P.slice(1).join(' ') + ' ' + cm).trim();
      if (!confirm(`This posts a real, public spot on POTA:\n\n${call} at ${P[0]} on ${mhz(k)} MHz ${mode}${cm ? '\n' + cm : ''}\n\nOnly send it when you're on the air. Send it?`)) return;
      msg('Sending…');
      try {
        const r = await fetch('https://api.pota.app/spot/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ activator: call, spotter: base(call), frequency: String(Math.round(k * 10) / 10), reference: P[0], mode, source: 'KPC Logger', comments: cm }) });
        const body = await r.text().catch(() => '');
        if (r.ok) { rlNote(); msg(`✓ Spot sent: ${call} at ${P[0]} on ${mhz(k)} ${mode}. It shows on pota.app within a minute. Next spot can go in 5 minutes.`, 'ok'); setTimeout(spots, 8000); }
        else msg('✗ POTA turned it down: ' + (String(body).replace(/^"|"$/g, '') || 'error ' + r.status) + '. Nothing was sent.', 'bad');
      } catch (e) { msg('✗ POTA could not be reached. Check your signal and try again.', 'bad'); }
    }
  }

  /* ---------------- notes (small box on top: tick to add them to new QSOs and / or the ones already logged) ---------------- */
  const notesTxt = () => String(SET.notes || '').trim().replace(/\s*\n\s*/g, ' · ').slice(0, 300);
  function notesPrev() { if (!SET.prev) return; const t = notesTxt(); let ch = 0; actList().forEach(q => { if ((q.cn || '') !== t) { q.cn = t; q.x = 0; ch++; } }); if (ch) { save(); drawLog(); } return ch; }
  function notesInit() {
    $('nText').value = SET.notes || ''; $('nCarry').checked = !!SET.carry; $('nPrev').checked = !!SET.prev;
    let nt; $('nText').oninput = () => { clearTimeout(nt); nt = setTimeout(() => { SET.notes = $('nText').value; saveSet(); notesPrev(); }, 500); };
    $('nCarry').onchange = e => { SET.carry = e.target.checked; saveSet(); toast(SET.carry ? '✓ Your notes go into every new QSO.' : 'New QSOs won\'t get your notes.'); };
    $('nPrev').onchange = e => { SET.prev = e.target.checked; saveSet(); if (SET.prev) { if (!notesTxt()) { toast('Type your notes first.'); return; } const n = notesPrev(); toast(`✓ Notes added to ${n || 'all'} QSO${n === 1 ? '' : 's'} already in ${isHunt() ? 'today\'s log' : 'this activation'} (and they follow your changes).`); } };
  }

  /* ---------------- map ---------------- */
  let MAP = null, ML = null, MV = 'act';
  function mapInit() {
    document.querySelectorAll('[data-mv]').forEach(b => b.onclick = () => { MV = b.dataset.mv; document.querySelectorAll('[data-mv]').forEach(x => x.classList.toggle('on', x === b)); drawMap(true); });
    if (!window.L) { $('mMap').innerHTML = '<div class="lg-empty">The map could not load (no signal?).</div>'; return; }
    MAP = window.L.map('mMap', { worldCopyJump: true, zoomControl: true }).setView([37.8, -85.7], 5);
    const SAT = window.L.layerGroup([window.L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 18, attribution: 'Imagery © Esri, Maxar, Earthstar Geographics' }),
      window.L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', { maxZoom: 18 })]);
    const STR = window.L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' });
    const base = b => { [SAT, STR].forEach(l => MAP.removeLayer(l)); (b === 'street' ? STR : SAT).addTo(MAP); document.querySelectorAll('[data-mb]').forEach(x => x.classList.toggle('on', x.dataset.mb === b)); };
    document.querySelectorAll('[data-mb]').forEach(x => x.onclick = () => { put('kpcLgBase', x.dataset.mb); base(x.dataset.mb); });
    base(navigator.onLine === false ? 'street' : get('kpcLgBase', 'sat'));
    window.addEventListener('offline', () => base('street'));
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
    $('sAct').textContent = n; $('sRate').textContent = r10; $('sHr').textContent = hr; $('sTot').textContent = L.q.length.toLocaleString(); opBar(n);
    $('dN').textContent = n; $('dRate').textContent = r10; $('tN').textContent = n;
    const sp = T.length ? (now - T[0]) / 6e4 : 0; $('dSpan').textContent = sp >= 1440 ? Math.floor(sp / 1440) + 'd ' + Math.floor(sp % 1440 / 60) + 'h' : sp >= 60 ? Math.floor(sp / 60) + 'h ' + Math.round(sp % 60) + 'm' : Math.round(sp) + 'm';
    if (multi() && !SET.share) { $('sOps').innerHTML = opsList().map(c => { const k2 = A.filter(q => q.my === c).length; return `<span class="${k2 >= 10 ? 'ok' : ''}">${esc(c)} ${k2 >= 10 ? '✓ ' + k2 : k2 + '/10'}</span>`; }).join(''); }
    else if (multi()) { $('sOps').innerHTML = opsList().map(c => `<span>${esc(c)} ${A.filter(q => (q.op || q.my) === c).length} logged</span>`).join(''); }
    else $('sOps').innerHTML = '';
    const W = myWwff(), So = mySota(), pg = [];
    if (W) pg.push(`<span class="${n >= 44 ? 'ok' : ''}">WWFF ${esc(W)} ${n >= 44 ? '✓ ' + n : n + '/44'}</span>`);
    if (So) pg.push(`<span class="${n >= 4 ? 'ok' : ''}">SOTA ${esc(So)} ${n >= 4 ? '✓ ' + n + ' (points count)' : n + '/4'}</span>`);
    $('sProg').innerHTML = pg.join('');
    drawOps();
    const g = Math.min(n, 10); $('sGoalBar').style.width = g * 10 + '%';
    const P = myParks();
    $('sGoal').parentElement.classList.toggle('done', n >= 10);
    if (isHunt()) { $('sGoal').textContent = `🎯 Hunting today: ${n} contact${n === 1 ? '' : 's'}, ${new Set(A.map(q => q.ref).filter(Boolean)).size} parks`; $('sGoalBar').style.width = '100%'; }
    else $('sGoal').textContent = !P.length ? (myWwff() || mySota() ? 'POTA: no park number set (WWFF / SOTA below)' : 'Add your park number in ⚙ STATION to start an activation') : n >= 10 ? `✓ Valid activation at ${P.join(' + ')} (${n} contacts). Keep going!` : `${n} of 10 contacts for a valid POTA activation at ${P.join(' + ')}`;
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

  /* ---------------- the operation bar on top of the log card (PoLo style) ---------------- */
  function opBar(n) {
    const P = myParks(), sc = stationCall();
    $('oCall').textContent = sc || 'YOUR CALL'; $('oAt').textContent = isHunt() ? '·' : '@'; $('oPark').textContent = isHunt() ? '🎯 HUNTING' : (myRefsTxt() || 'NO PARK YET');
    if (isHunt()) { const A = actList(); $('oSub').textContent = !sc ? 'Tap ⚙ STATION to set your call' : `${A.length} contacts today · ${new Set(A.map(q => q.ref).filter(Boolean)).size} parks`; $('oN').textContent = A.length; $('lMini').innerHTML = `<b>${esc(sc || 'YOUR CALL')}</b> · 🎯 HUNTING`; return; }
    const nm = P.map(r => SET.pinfo[r] && SET.pinfo[r].n).filter(Boolean).join(' + ');
    $('oSub').textContent = !sc || !myRefsTxt() ? 'Tap ⚙ STATION to set your call and park' : [nm, SET.grid, SET.pwr ? SET.pwr + ' W' : '', multi() ? opsList().length + ' operators' : ''].filter(Boolean).join(' · ');
    $('oN').textContent = n == null ? actList().length : n;
    $('lMini').innerHTML = `<b>${esc(sc || 'YOUR CALL')}</b> ${isHunt() ? '· 🎯 HUNTING' : '@ <i>' + esc(myRefsTxt() || 'NO PARK YET') + '</i>'}`;
  }
  /* ⚙ = the station menu, folded above the entry (Brandon Oct 16) */
  /* Download & files + Install fold into bars (Brandon Oct 17) */
  ['cFiles', 'cApp'].forEach(id => { const c = document.getElementById(id); if (!c) return; c.classList.add('lg-fold'); const h = c.querySelector('h2'); h.setAttribute('role', 'button'); h.tabIndex = 0;
    const tg = () => { c.classList.toggle('open'); h.setAttribute('aria-expanded', c.classList.contains('open')); }; h.onclick = tg; h.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); tg(); } }; });
  document.addEventListener('click', e => { const a = e.target.closest('a[href="#cApp"],a[href="#cFiles"]'); if (!a) return; const c = document.getElementById(a.getAttribute('href').slice(1)); if (c) c.classList.add('open'); });
  function stationOpen(open) { if (open) popOnly('sta'); $('cOp').hidden = !open; $('dSta').classList.toggle('on', open); $('dSta').setAttribute('aria-expanded', open); dockSize(); if (open) { const t = !myCall() ? $('myCall') : null; if (t) setTimeout(() => t.focus({ preventScroll: true }), 50); } }
  function night(on) { document.getElementById('lg').toggleAttribute('data-night', on); $('oNight').textContent = on ? '☀ DAY' : '🌙 NIGHT'; put('kpcLgNight', on); }
  function role(r) {
    SET.role = r === 'hunt' ? 'hunt' : 'act'; saveSet();
    document.querySelectorAll('[data-role]').forEach(b => b.classList.toggle('on', b.dataset.role === SET.role));
    document.getElementById('lg').dataset.role = SET.role;
    $('dSpot').hidden = isHunt(); $('dRole').textContent = tabMode() ? (isHunt() ? '🎯 HUNT' : '🏕 ACT') : (isHunt() ? '🎯 HUNTING' : '🏕 ACTIVATING'); $('dRole').classList.toggle('hunt', isHunt()); $('lvAct').textContent = isHunt() ? 'TODAY' : 'THIS ACTIVATION';
    $('xPota').textContent = isHunt() ? '⬇ MY HUNTING LOG (TODAY, ADIF)' : '⬇ FILES FOR THIS ACTIVATION (POTA · WWFF · SOTA)';
    $('myParkL').firstChild.textContent = isHunt() ? 'My park numbers (only when you activate)' : 'My park numbers';
    drawAll();
  }
  function opBarInit() {
    document.querySelectorAll('[data-role]').forEach(b => b.onclick = () => { role(b.dataset.role); toast(isHunt() ? '🎯 Hunting: no park number needed. Tap a spot, log it, and the park goes with the contact.' : '🏕 Activating: your park number goes on every contact.'); });
    role(SET.role);
    const FXL = { flames: '🔥 FLAMES', fireworks: '🎆 FIREWORKS', stars: '🌠 STARS', off: '🚫 PLAIN' };
    const fxSet = f => { SET.fx = FXL[f] ? f : 'flames'; saveSet(); $('cEntry').dataset.fx = SET.fx; $('oFx').textContent = FXL[SET.fx]; };
    const LKL = { classic: '🏕 CLASSIC', lodge: '🔥 CABIN LODGE', night: '🌌 NIGHT SKY', dark: '🌑 DARK' }, LKN = { classic: 'lodge', lodge: 'night', night: 'dark', dark: 'classic' };
    const lookSet = l => { SET.look = LKL[l] ? l : 'lodge'; saveSet(); document.getElementById('lg').dataset.look = SET.look; $('oLook').textContent = LKL[SET.look]; document.querySelectorAll('[data-look]').forEach(b => b.classList.toggle('on', b.dataset.look === SET.look)); };
    lookSet(SET.look || 'lodge'); $('oLook').onclick = () => lookSet(LKN[SET.look]); document.querySelectorAll('[data-look]').forEach(b => b.onclick = () => lookSet(b.dataset.look));
    fxSet(SET.fx || 'flames'); $('oFx').onclick = () => fxSet(({ flames: 'fireworks', fireworks: 'stars', stars: 'off', off: 'flames' })[SET.fx]);
    night(!!get('kpcLgNight', false)); $('oNight').onclick = () => night(!document.getElementById('lg').hasAttribute('data-night'));
    $('oEdit').onclick = () => stationOpen(false);
    stationOpen(!myCall() || (!isHunt() && !myParks().length && !myWwff() && !mySota()));
  }

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
        $('myNear').innerHTML = R.map(([p, d]) => `<div class="np"><div><b>${esc(p[0])}</b> <span>${esc(p[1])}</span> <em>${esc(p[2].slice(3))} · ${d < 0.2 ? 'you are here or very close' : d.toFixed(1) + ' mi'}</em></div><button type="button" class="lg-btn ${myParks().includes(p[0]) ? 'line' : 'gold'} sm" data-add="${esc(p[0])}">${myParks().includes(p[0]) ? '✓ ADDED' : '+ ADD'}</button></div>`).join('') + '<div class="lg-row"><button type="button" class="lg-btn line sm" data-nclose="1">DONE</button><span class="lg-mu" style="margin:0">Tap + ADD on a second park for a 2-fer (it adds the comma for you). The park pin is not the boundary: check you\'re inside.</span></div>';
        drawMap(true);
      }, e => { $('myGpsMsg').textContent = 'Could not get your location (' + (e.message || 'blocked') + ').'; }, { enableHighAccuracy: true, timeout: 20000 });
    };
    $('myNear').onclick = e => {
      if (e.target.closest('[data-nclose]')) { $('myNear').hidden = true; return; }
      const a = e.target.closest('[data-add]'); if (!a) return;
      const ref = a.dataset.add, p = (PK || []).find(x => x[0] === ref); if (myParks().includes(ref)) return;
      if (p && !SET.pinfo[ref]) SET.pinfo[ref] = { n: p[1], st: p[2], la: p[3], lo: p[4], g: toGrid(p[3], p[4]), t: Date.now() - 6 * 864e5 };
      if (isHunt()) role('act');
      setRefs([SET.park, ref].filter(x => String(x || '').trim()).join(', ')); parkInfo();
      a.textContent = '✓ ADDED'; a.className = 'lg-btn line sm'; toast(`✓ ${ref} added: your park numbers are ${SET.park}.`);
    };
  }

  function tileList(bb, z) { const n = 2 ** z, X = lo => Math.floor((lo + 180) / 360 * n), Y = la => { const r = la * Math.PI / 180; return Math.floor((1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * n); };
    const out = []; const x0 = Math.max(0, X(bb[0])), x1 = Math.min(n - 1, X(bb[2])), y0 = Math.max(0, Y(bb[3])), y1 = Math.min(n - 1, Y(bb[1]));
    for (let x = x0; x <= x1; x++) for (let y = y0; y <= y1; y++) out.push(`https://tile.openstreetmap.org/${z}/${x}/${y}.png`); return out; }
  async function saveTiles(m) {
    const me = meLL(); if (!me) return 0; const [la, lo] = me;
    let T = tileList([-180, -70, 180, 75], 2).concat(tileList([-130, 15, -60, 55], 3), tileList([-128, 22, -64, 51], 4), tileList([lo - 12, la - 7, lo + 12, la + 7], 5), tileList([lo - 6, la - 3.5, lo + 6, la + 3.5], 6));
    [[7, 1.5], [8, .8], [9, .4], [10, .2], [11, .1], [12, .05], [13, .03]].forEach(([z, d]) => { T = T.concat(tileList([lo - d * 1.4, la - d, lo + d * 1.4, la + d], z)); });
    T = [...new Set(T)].slice(0, 1200);
    const c = await caches.open('kpc-tiles-v1'); let done = 0;
    for (let i = 0; i < T.length; i += 6) {
      await Promise.all(T.slice(i, i + 6).map(async u => { try { if (await c.match(u)) { done++; return; } const r = await fetch(u, { mode: 'cors' }); if (r.ok) { await c.put(u, r); done++; } } catch (e) {} }));
      m.textContent = `Saving the map around you… ${Math.min(100, Math.round((i + 6) / T.length * 100))}%`;
    }
    return done;
  }

  /* ---------------- 📸 share my activation (a picture for Facebook / Discord / texts) ---------------- */
  const img = src => new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = no; i.src = src; });
  let STATES = null;
  async function sharePic() {
    const A = actList(); if (!A.length) { toast('Log some contacts first.'); return; }
    const W = 1080, H = 1350, cv = document.createElement('canvas'); cv.width = W; cv.height = H; const x = cv.getContext('2d');
    x.fillStyle = '#050b0f'; x.fillRect(0, 0, W, H);
    try { const h = await img('hero-founders.jpg'); x.drawImage(h, 0, 0, W, W * h.height / h.width); } catch (e) {}
    const g = x.createLinearGradient(0, 230, 0, 420); g.addColorStop(0, 'rgba(5,11,15,0)'); g.addColorStop(1, 'rgba(5,11,15,1)'); x.fillStyle = g; x.fillRect(0, 230, W, 200);
    x.fillStyle = '#45e08f'; x.font = '900 26px Arial'; x.fillText(isHunt() ? 'KPC LOGGER · HUNTING REPORT' : 'KPC LOGGER · ACTIVATION REPORT', 50, 440);
    x.fillStyle = '#fff'; x.font = '900 64px Menlo, Consolas, monospace'; x.fillText(stationCall() || myCall(), 50, 515);
    x.fillStyle = '#ffd27a'; x.font = '900 46px Menlo, Consolas, monospace'; x.fillText(isHunt() ? new Set(A.map(q => q.ref).filter(Boolean)).size + ' parks hunted' : myRefsTxt().slice(0, 36), 50, 575);
    const nm = myParks().map(r => SET.pinfo[r] && SET.pinfo[r].n).filter(Boolean).join(' + ');
    x.fillStyle = '#dbe3dd'; x.font = '30px Arial'; x.fillText((nm || '').slice(0, 52), 50, 620); x.fillText(fD(A[0].d) + ' · ' + fT(A[0].tm) + '–' + fT(A[A.length - 1].tm) + ' UTC', 50, 660);
    const me = meLL(), sts = new Set(A.map(q => q.st).filter(s => /^[A-Z]{2}$/.test(s))).size, p2p = A.filter(q => q.ref).length, bands = [...new Set(A.map(q => q.band))];
    let far = 0; A.forEach(q => { if (me && q.la != null) far = Math.max(far, miles(me, [q.la, q.lo])); });
    const tiles = [[A.length, 'CONTACTS'], [sts, 'STATES'], [p2p, 'PARK-TO-PARK'], [far ? Math.round(far).toLocaleString() : '-', 'MILES, FARTHEST']];
    tiles.forEach(([v, l], i) => { const tx = 50 + i * 248; x.fillStyle = 'rgba(255,255,255,.07)'; x.fillRect(tx, 690, 228, 130); x.strokeStyle = 'rgba(226,176,74,.5)'; x.strokeRect(tx, 690, 228, 130);
      x.fillStyle = i ? '#fff' : '#45e08f'; x.font = '900 54px Menlo, Consolas, monospace'; x.fillText(String(v), tx + 18, 760); x.fillStyle = '#9fb0ad'; x.font = '900 18px Arial'; x.fillText(l, tx + 18, 800); });
    /* little map: states + lines from you */
    const mx = 50, my = 850, mw = 980, mh = 400;
    x.fillStyle = '#08131a'; x.fillRect(mx, my, mw, mh);
    const pts = A.filter(q => q.la != null).map(q => [q.la, q.lo, q.band]); const all = pts.map(p => [p[0], p[1]]).concat(me ? [me] : []);
    if (all.length) {
      let la0 = Math.min(...all.map(p => p[0])), la1 = Math.max(...all.map(p => p[0])), lo0 = Math.min(...all.map(p => p[1])), lo1 = Math.max(...all.map(p => p[1]));
      const pad = Math.max(2, (la1 - la0) * .12); la0 -= pad; la1 += pad; lo0 -= pad * 1.3; lo1 += pad * 1.3;
      const sc = Math.min(mw / (lo1 - lo0) / Math.cos((la0 + la1) / 2 * Math.PI / 180), mh / (la1 - la0)), kx = sc * Math.cos((la0 + la1) / 2 * Math.PI / 180);
      const cx = mx + (mw - (lo1 - lo0) * kx) / 2, cy = my + (mh - (la1 - la0) * sc) / 2, P = (la, lo) => [cx + (lo - lo0) * kx, cy + (la1 - la) * sc];
      x.save(); x.beginPath(); x.rect(mx, my, mw, mh); x.clip();
      try { STATES = STATES || await fetch('kpc-us-states.json').then(r => r.json()); x.strokeStyle = 'rgba(226,176,74,.35)'; x.lineWidth = 1.2;
        STATES.forEach(s => (s.p || []).forEach(poly => poly.forEach(ring => { x.beginPath(); ring.forEach(([lo, la], i) => { const [a, b] = P(la, lo); i ? x.lineTo(a, b) : x.moveTo(a, b); }); x.closePath(); x.stroke(); }))); } catch (e) {}
      pts.forEach(([la, lo, b]) => { const c = BCOL[b] || '#ddd'; if (me) { const [a1, b1] = P(me[0], me[1]), [a2, b2] = P(la, lo); x.strokeStyle = c; x.globalAlpha = .7; x.lineWidth = 2; x.beginPath(); x.moveTo(a1, b1); x.lineTo(a2, b2); x.stroke(); x.globalAlpha = 1; } });
      pts.forEach(([la, lo, b]) => { const [a, bb] = P(la, lo); x.fillStyle = BCOL[b] || '#ddd'; x.beginPath(); x.arc(a, bb, 8, 0, 6.283); x.fill(); x.strokeStyle = '#fff'; x.lineWidth = 2; x.stroke(); });
      if (me) { const [a, b] = P(me[0], me[1]); x.fillStyle = '#ffd27a'; x.font = '44px Arial'; x.textAlign = 'center'; x.fillText('⭐', a, b + 15); x.textAlign = 'left'; }
      x.restore();
    }
    x.fillStyle = '#9fb0ad'; x.font = '22px Arial'; x.fillText(bands.join(' · ') + '  ·  Kentucky Portable Club', 50, 1300);
    const blob = await new Promise(r => cv.toBlob(r, 'image/png'));
    $('rShareOut').innerHTML = `<img src="${URL.createObjectURL(blob)}" alt="Activation report picture">`;
    files([[`KPC-${(stationCall() || 'activation').replace(/\//g, '-')}-${(myParks()[0] || myWwff() || mySota() || 'park').replace('/', '_')}-${A[0].d}.png`, blob, 'image/png']]);
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
      let tl = 0; try { tl = await saveTiles(m); } catch (e) {}
      m.className = 'lg-msg ' + (bad && !ok ? 'bad' : 'ok'); m.textContent = ok ? `✓ Saved (${ok} files${tl ? ' and ' + tl + ' map pieces around ' + (myParks()[0] || 'you') : ''}). The logger now opens and works with no signal on this device.${bad ? ' ' + bad + ' extra file(s) could not be saved.' : ''}` : 'Could not save (no signal?). Try again with signal.';
      put('kpcLgSaved', Date.now());
    };
    const t = get('kpcLgSaved', 0); if (t && !$('aMsg').textContent) { $('aMsg').className = 'lg-msg ok'; $('aMsg').textContent = '✓ Saved for no signal on ' + new Date(t).toLocaleDateString([], { month: 'short', day: 'numeric' }) + '. Tap again to refresh it.'; }
  }

  /* ---------------- radio control (CAT), like the Hunters Lounge (Brandon Oct 17: 'build cat control… for ssb, cw etc
     also change bands modes frequency'). Uses kpc-cat.js (Web Serial: Chrome / Edge on a computer). Settings shared with the
     Lounge (localStorage kpcCat); the two ticks live in SET.catT / SET.catF. ---------------- */
  let catBusy = false, catT = null;
  const catOk = () => !!(window.KPCCat && KPCCat.get().on && KPCCat.connected());
  function catDraw() {
    if (!window.KPCCat) return; const on = catOk(), C = KPCCat.get();
    $('catSt').textContent = on ? '✓ connected' : C.on ? 'not connected' : 'off'; $('catSt').className = on ? 'ok' : '';
    $('catGo').textContent = on ? '⏏ DISCONNECT' : '🔌 CONNECT MY RADIO';
    $('dCat').hidden = !C.on; $('dCat').classList.toggle('bad', !on); $('dCat').classList.toggle('on', on);
  }
  /* send the dock's frequency + mode to the radio (not when the change came from the radio itself) */
  function catTune(now) {
    if (catBusy || !catOk() || SET.catT === false) return;
    clearTimeout(catT); catT = setTimeout(() => { const k = kHzOf($('eFreq').value); if (k && bandOf(k)) KPCCat.tune(k, $('eMode').value === 'OTHER' ? 'USB' : $('eMode').value); }, now ? 0 : 350);
  }
  function catFromRadio(r) {
    if (!r || !r.khz || SET.catF === false) return; catBusy = true;
    try {
      const cur = $('eMode').value, rm = String(r.mode || '').toUpperCase();
      const m = /USB|LSB/.test(rm) ? (DIGI.test(cur) && false ? cur : 'SSB') : rm === 'CW' ? 'CW' : rm === 'FM' ? 'FM' : rm === 'AM' ? 'AM' : rm === 'DATA' ? (DIGI.test(cur) || /RTTY|PSK|FT2/.test(cur) ? cur : 'FT8') : cur;
      /* a digital mode on plain USB: keep the digital mode the dock already has */
      const mode = (rm === 'USB' && /^(FT8|FT4|FT2|JS8|PSK31|RTTY)$/.test(cur)) ? cur : m;
      if (Math.abs(kHzOf($('eFreq').value) - r.khz) > 0.05 || mode !== cur) {
        $('eFreq').value = mhz(Math.round(r.khz * 10) / 10); if ([...$('eMode').options].some(o => o.value === mode)) $('eMode').value = mode;
        bandSet(); modeSet(); put('kpcLgRadio', { f: $('eFreq').value, m: $('eMode').value }); radioTxt();
      }
    } finally { setTimeout(() => { catBusy = false; }, 50); }
  }
  function catInit() {
    if (!window.KPCCat) { $('myCat').hidden = true; return; }
    KPCCat.fillSelect($('catRadio')); const C = KPCCat.get(); $('catRadio').value = C.radio || '';
    $('catTune').checked = SET.catT !== false; $('catFollow').checked = SET.catF !== false;
    $('catTune').onchange = () => { SET.catT = $('catTune').checked; saveSet(); };
    $('catFollow').onchange = () => { SET.catF = $('catFollow').checked; saveSet(); KPCCat.set({ follow: SET.catF }); };
    $('catRadio').onchange = () => { const r = KPCCat.pickRadio($('catRadio').value); if (!r) { $('catMsg').textContent = 'Set the speed and radio type on the VIP Lounge CAT & QRZ tab.'; return; }
      $('catMsg').textContent = 'Settings filled in for your ' + r.label + '. Now press CONNECT MY RADIO.' + (/yaesu/.test(r.proto) ? ' Set the radio\'s CAT RATE menu to ' + r.baud + '.' : r.proto === 'icom' ? ' The radio\'s CI-V address should be ' + r.civ + ' (CI-V USB echo off).' : ''); };
    if (!KPCCat.supported()) { $('catGo').disabled = true; $('catMsg').textContent = 'This browser can\'t talk to a radio. Use Chrome or Edge on a computer, or Chrome on an Android phone (newer versions, with a USB-C cable). iPhones can\'t do this yet.'; }
    $('catGo').onclick = async () => {
      if (catOk()) { await KPCCat.disconnect(); KPCCat.set({ on: false }); catDraw(); return; }
      if (!KPCCat.get().proto || !$('catRadio').value && !KPCCat.get().radio) { $('catMsg').textContent = 'Pick your radio first.'; return; }
      KPCCat.set({ on: true, follow: SET.catF !== false }); const ok = await KPCCat.connect(true); catDraw();
      if (ok) { $('catMsg').textContent = '✓ Radio connected. Tap a spot or change the band and the radio follows; turn the radio\'s dial and the log follows.'; if (SET.catF !== false) KPCCat.read().then(catFromRadio); }
    };
    $('dCat').onclick = () => { if (catOk()) { KPCCat.read().then(r => { catFromRadio(r); toast(r ? '📻 Radio: ' + mhz(r.khz) + ' ' + (r.mode || '') : 'The radio did not answer.'); }); } else { stationOpen(true); setTimeout(() => $('myCat').scrollIntoView({ block: 'center' }), 80); } };
    KPCCat.onStatus(t => { $('catMsg').textContent = t; catDraw(); });
    ['eFreq', 'eMode', 'eBand'].forEach(i => $(i).addEventListener('change', () => catTune()));
    $('eFreq').addEventListener('keydown', e => { if (e.key === 'Enter') catTune(true); });
    KPCCat.follow(r => catFromRadio(r));
    if (C.on && SET.catF !== false) KPCCat.set({ follow: true });
    if (C.on) KPCCat.connect(false).then(catDraw); catDraw();
  }

  /* ---------------- no cell signal: APSPOT text message (Brandon Oct 17: 'ap spots style… getting spotted… no cell signal') ---------------- */
  function apInit() {
    $('sAp').onclick = () => {
      const call = stationCall(), k = kHzOf($('eFreq').value), mode = $('eMode').value === 'OTHER' ? '' : $('eMode').value;
      if (isHunt()) { toast('Hunting: TEXT MY SPOT is for spotting yourself at a park.'); return; }
      if (!call) { toast('Put your call in ⚙ STATION first.'); stationOpen(true); return; }
      const R = [].concat(myParks().slice(0, 1).map(r => ['POTA', r]), myWwff() ? [['WWFF', myWwff()]] : [], mySota() ? [['SOTA', mySota()]] : []);
      if (!R.length) { toast('Put your park number in ⚙ STATION first.'); stationOpen(true); return; }
      if (!k || !bandOf(k)) { toast('Type the frequency you are on first (like 14.285).'); drawer(true); return; }
      const cm = $('sCm').value.trim().slice(0, 40), M = R.map(r => `! ${r[0]} ${r[1]} ${(k / 1000).toFixed(3)} ${mode}${cm ? ' ' + cm : ''}`);
      const box = $('sMsg'); box.className = 'lg-msg';
      box.innerHTML = `<b>📵 Spot yourself by text message (APSPOT)</b><br>A text message often gets out when the internet won't. Tap TEXT IT, pick your saved <b>APSPOT</b> contact (its number is on <a href="https://apspot.radio" target="_blank" rel="noopener">apspot.radio</a>; save it before you leave home) and send. APSPOT puts the spot on POTA${R.length > 1 ? ', WWFF and SOTA (one message each)' : ''} for you. No signal at all? Leave it as a draft: it sends when one bar shows up.` +
        M.map((m, i) => `<div class="lg-ap"><code>${esc(m)}</code><a class="lg-btn gold sm" href="sms:?&body=${encodeURIComponent(m)}">📱 TEXT IT${M.length > 1 ? ' (' + R[i][0] + ')' : ''}</a></div>`).join('');
    };
  }

  /* ---------------- for the FT8 tab (kpc-logger-ft8.js) ---------------- */
  function quickLog(o) {
    const call = String(o.call || '').toUpperCase().trim();
    if (!okCall(call)) return { msg: 'That call sign does not look right.' };
    if (!myCall()) return { msg: 'Put YOUR call in ⚙ STATION first.' };
    if (!isHunt() && !myParks().length && !myWwff() && !mySota()) return { msg: 'Put your park number in ⚙ STATION first (or switch to 🎯 HUNTING).' };
    const k = +o.khz, band = bandOf(k); if (!band) return { msg: 'The frequency is not on a ham band.' };
    const when = new Date(), ll = fromGrid(o.g || '');
    const q = { id: 'q' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6), call, d: ymd(when), tm: iso(when).slice(11, 16).replace(':', ''), t: Date.now(),
      f: mhz(k), band, mode: o.mode || 'FT8', rs: o.rs || '', rr: o.rr || '', ref: anyRefs(o.ref || '').join(','), name: '', st: '', qth: '', g: String(o.g || '').toUpperCase(), la: ll ? ll[0] : null, lo: ll ? ll[1] : null,
      note: '', cn: SET.carry || SET.prev ? notesTxt() : '', role: isHunt() ? 'hunt' : 'act', my: stationCall(), op: curOp(), pk: isHunt() ? '' : myParks().join(','), wf: myWwff(), so: mySota(), mg: SET.grid, pw: SET.pwr, x: 0, ft: 1 };
    L.q.push(q); NEWID = q.id; save(); drawAll(); try { radioTxt(); } catch (e) {}
    look(call).then(x => { if (!x) return; const z = L.q.find(y => y.id === q.id); if (!z) return;
      if (!z.name) z.name = (x.name || '').split(' ')[0]; if (!z.st && x.st) z.st = String(x.st).toUpperCase(); if (!z.qth) z.qth = x.qth || ''; if (!z.g) z.g = x.g || '';
      if (z.la == null) { const l2 = x.la != null ? [x.la, x.lo] : fromGrid(x.g); if (l2) { z.la = l2[0]; z.lo = l2[1]; } } save(); drawAll(); }).catch(() => {});
    return { ok: true, q, n: actList().filter(x => x.my === q.my).length };
  }
  window.KPCLog = {
    me: () => ({ call: myCall(), station: stationCall(), grid: String(SET.grid || '').toUpperCase(), hunt: isHunt(), pota: myParks(), wwff: myWwff(), sota: mySota() }),
    add: quickLog, band: bandOf, toast,
    dupe: (call, band, mode) => dupeOf(call, band, mode, '').length > 0,
    worked: call => { const b = base(call); return L.q.some(q => base(q.call) === b); },
    qs: () => L.q,
    freq: () => kHzOf($('eFreq').value),
    spots: () => SP, station: () => stationOpen(true),
    tab: t => { if (tabMode()) tab(t); else rtab(t); }
  };

  async function start() {
    const parts = [() => { $('rShare').onclick = sharePic; $('hShare').onclick = sharePic; }, stationInit, opBarInit, opsInit, nearInit, entryInit, dockInit, logInit, expInit, spotsInit, spotInit, notesInit, appInit, mapInit, catInit, apInit];
    parts.forEach(f => { try { f(); } catch (e) { console.error(f.name, e); } });
    try { const o = await idbGet('log'); IDBok = true; if (o && Array.isArray(o.q) && ((o.u || 0) > (L.u || 0) || o.q.length > L.q.length)) { L = o; put(LK, L); } } catch (e) {}
    if (navigator.storage && navigator.storage.persisted) { try { PERSIST = await navigator.storage.persisted(); } catch (e) {} }
    drawAll(); safe();
    setInterval(() => { const u = iso(new Date()).slice(11, 19); $('sUtc').textContent = u; $('dClk').textContent = (tabMode() ? '' : '🕒 ') + u + 'z'; }, 1000);
    setInterval(rates, 30000);
    window.addEventListener('storage', e => { if (e.key === LK) { L = get(LK, L); drawAll(); } });
  }
  start();
})();
