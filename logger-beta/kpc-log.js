/* KPC app: the LOG screen. The entry dock (PoLo style: chips, one line, round gold button), the list of contacts,
   the ADIF file, and the little API the FT8 screen logs through (KPCLog.add), like the website logger.

   THE LOG STORE (Fable, Oct 22 — the decision is in kpc-links notes/ft8-app.md 'LOG STORAGE + SYNC'):
   one record per contact, the same on phone and PC:
     id (stable, never changes)  v (edit count)  u (last changed, ms)  d (1 = taken out: a tombstone, so the other device learns too)
     t call khz band mode rs rr st g name note   refs[] (their parks)  myrefs[] (my parks)   station op ctl (Part 97.119)   src (device)
   Lives in IndexedDB 'kpc-log' (store 'qso', key id), all in memory while the app runs. Merge rule: by id, higher v wins,
   tie → later u wins. KPCLog.changes(since) + KPCLog.merge(records) are what the remote link and the .kpclog file use. */
(function (G) {
  'use strict';
  const $ = id => document.getElementById(id);
  const AP = G.KPCApp, esc = AP.esc;
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const SV = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const pad = n => String(n).padStart(2, '0');
  const YEAR = 366 * 86400000;

  /* ---------------- ids ---------------- */
  const rnd = n => { let s = ''; const A = 'abcdefghijkmnpqrstuvwxyz23456789'; const u = new Uint8Array(n); (G.crypto && crypto.getRandomValues) ? crypto.getRandomValues(u) : u.forEach((_, i) => { u[i] = Math.random() * 256; }); for (let i = 0; i < n; i++) s += A[u[i] % A.length]; return s; };
  const newId = t => (t || Date.now()).toString(36) + '-' + rnd(8);
  function fnv(s) { let h = 0x811c9dc5; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; } return h.toString(16).padStart(8, '0'); }
  /* the same old contact on two devices → the same id (station, their call, the minute, band, mode) */
  const hashId = q => 'h' + fnv([q.station || q.my || '', q.call, Math.floor((+q.t || 0) / 60000), q.band || '', q.mode || ''].join('|')) + fnv(String(q.call) + '#' + Math.floor((+q.t || 0) / 60000));
  const DEV = LS('kpcDev', '') || (() => { const d = rnd(6); SV('kpcDev', d); return d; })();

  /* ---------------- the store ---------------- */
  const ALL = new Map();                                   /* id → record, tombstones included */
  let Q = [];                                              /* what the screen shows: live records of the current operator, oldest first */
  let IDB = null, ready = false, idbOk = false;
  function idbOpen() {
    return new Promise(res => {
      if (!G.indexedDB) { res(null); return; }
      let r; try { r = indexedDB.open('kpc-log', 1); } catch (e) { res(null); return; }
      r.onupgradeneeded = () => { const db = r.result; if (!db.objectStoreNames.contains('qso')) db.createObjectStore('qso', { keyPath: 'id' }); };
      r.onsuccess = () => res(r.result); r.onerror = () => res(null); r.onblocked = () => res(null);
    });
  }
  function idbAll(db) { return new Promise(res => { try { const rq = db.transaction('qso').objectStore('qso').getAll(); rq.onsuccess = () => res(rq.result || []); rq.onerror = () => res([]); } catch (e) { res([]); } }); }
  function idbPut(recs) {   /* → true when the database really took them (Nov 18 full review L3: the answer is checked now) */
    if (!IDB || !recs.length) return Promise.resolve(true);
    return new Promise(res => { try { const tx = IDB.transaction('qso', 'readwrite'), st = tx.objectStore('qso'); recs.forEach(r => st.put(r)); tx.oncomplete = () => res(true); tx.onerror = () => res(false); tx.onabort = () => res(false); } catch (e) { res(false); } });
  }
  function idbClear() { if (!IDB) return Promise.resolve(); return new Promise(res => { try { const tx = IDB.transaction('qso', 'readwrite'); tx.objectStore('qso').clear(); tx.oncomplete = () => res(); tx.onerror = () => res(); } catch (e) { res(); } }); }
  /* localStorage is the fallback when IndexedDB is missing (and a safety copy of the last 2,000 while it works) */
  /* Nov 18 full review (L15): the safety copy is the 2,000 most recently CHANGED records (an edit to an old contact is in it too),
     not the 2,000 added last. → false when localStorage refused it (full). */
  function lsSave() {
    try { let live = [...ALL.values()]; if (idbOk && live.length > 2000) live = live.sort((a, b) => (+a.u || 0) - (+b.u || 0)).slice(-2000);
      localStorage.setItem('kpcAppQso2', JSON.stringify(live)); return true; } catch (e) { return false; }
  }
  /* Nov 18 full review (L3): a contact that could not be stored is never lost in silence: a red NOT SAVED bar on the LOG screen, a retry,
     and a button for the KPC log file (which holds everything that is in memory right now). */
  let UNSAVED = 0;
  async function persist(recs) {   /* Oct 24: the safety copy first (sync), so a contact survives the app being closed a moment after logging */
    const lsOk = lsSave();
    let ok = await idbPut(recs);
    if (IDB && !ok) { await new Promise(r => setTimeout(r, 800)); ok = await idbPut(recs); }
    const bad = IDB ? !ok && !lsOk || !ok && ALL.size > 2000 : !lsOk;
    if (bad) { UNSAVED += recs.length; notSaved(IDB ? 'this device\'s storage refused the write (full?)' : 'this device\'s storage is full'); }
    else if (UNSAVED && ok && (IDB || lsOk)) { UNSAVED = 0; notSaved(''); }
    return !bad;
  }
  function notSaved(why) {
    let b = $('lgNotSaved');
    if (!why) { if (b) b.hidden = true; return; }
    if (!b) { const st = $('lgStrip'); if (!st) return; st.insertAdjacentHTML('beforebegin', '<div class="st bad" id="lgNotSaved" role="alert" style="font-weight:700"></div>'); b = $('lgNotSaved'); }
    b.hidden = false;
    b.innerHTML = '⚠ NOT SAVED: ' + esc(why) + '. ' + UNSAVED + ' change' + (UNSAVED === 1 ? '' : 's') + ' are only in memory. <button type="button" class="b gold" id="lgNsSave">💾 SAVE THE KPC LOG FILE NOW</button> <button type="button" class="b" id="lgNsTry">TRY AGAIN</button>';
    $('lgNsSave').onclick = () => saveFile(fileText(), fname('.kpclog'), 'application/json');
    $('lgNsTry').onclick = () => persist([...ALL.values()]);
    if (!notSaved.said || Date.now() - notSaved.said > 60000) { notSaved.said = Date.now(); AP.toast('⚠ A contact could NOT be saved on this device (' + esc(why) + '). Save the KPC log file now (LOG screen).', 9000, 'bad'); }
  }

  function upgrade(o, old) {                               /* an old-style contact (no id) → a record */
    const q = Object.assign({}, o);
    q.station = String(q.station || q.my || '').toUpperCase(); q.op = String(q.op || q.my || q.station || '').toUpperCase(); delete q.my;
    q.refs = Array.isArray(q.refs) ? q.refs : (q.ref ? [String(q.ref).toUpperCase()] : []);
    q.myrefs = Array.isArray(q.myrefs) ? q.myrefs : (q.myref ? [String(q.myref).toUpperCase()] : []);
    delete q.myref; q.ref = q.refs[0] || '';
    q.id = q.id || hashId(q); q.v = +q.v || 1; q.u = +q.u || +q.t || Date.now(); q.d = q.d ? 1 : 0; q.src = q.src || (old ? 'old' : DEV);
    q.t = +q.t || Date.now(); q.call = String(q.call || '').toUpperCase();
    ['mode', 'band'].forEach(k => { if (q[k] != null && typeof q[k] !== 'string') q[k] = typeof q[k] === 'number' ? String(q[k]) : ''; });   /* 0.9.7: a hand-edited log file with an odd type here must not break the screens that read it */
    return q;
  }
  /* Nov 18 full review (L2, L9): the log is filtered by operator ONLY when OPERATORS are set up (STATION → 👤 ME). Before, a new call sign
     (vanity, upgrade, a typo fixed) hid every older contact, and a club / Field Day file with other OPERATORs showed nothing. With
     operators set up, the home station still sees what it logged under any call this device has had (MYC). */
  const MYC = new Set(LS('kpcAppMyCalls', []));
  function myCallsAdd() { const c = String(AP.S.call || '').toUpperCase(); if (c && !MYC.has(c)) { MYC.add(c); SV('kpcAppMyCalls', [...MYC].slice(-20)); } }
  function view() {
    myCallsAdd();
    const op = AP.me().op, opsOn = !!((AP.S.ops || []).length || AP.S.op), home = !AP.S.op;
    Q = [...ALL.values()].filter(q => !q.d && (!opsOn || !op || !q.op || q.op === op || (home && MYC.has(q.op)))).sort((a, b) => a.t - b.t || (a.id < b.id ? -1 : 1));
    V = CUR ? Q.filter(q => opOf(q) === CUR) : Q;
  }
  let FIND = '', SEL = null;   /* Nov 19: 🔍 FIND text and the ☑ FIX SEVERAL picks (declared up here: draw() reads them) */
  let V = [];   /* Oct 25: the contacts of the log that is open (CUR), or all of them */
  async function load() {
    IDB = await idbOpen(); idbOk = !!IDB;
    let recs = IDB ? await idbAll(IDB) : [];
    recs.forEach(r => ALL.set(r.id, upgrade(r)));
    /* Oct 24: the safety copy can be newer (the app closed before the database finished writing): newer records from it win */
    const missed = [];
    for (const r of LS('kpcAppQso2', [])) { if (!r || !r.id) continue; const h = ALL.get(r.id), u = upgrade(r); if (!h || (+u.v || 0) > (+h.v || 0) || ((+u.v || 0) === (+h.v || 0) && (+u.u || 0) > (+h.u || 0))) { ALL.set(u.id, u); missed.push(u); } }
    if (missed.length && IDB) idbPut(missed).catch(() => {});
    const old = LS('kpcAppQso', null);                     /* the list from 0.3.x: moved over once, then the key goes */
    if (old && old.length) {
      const up = old.map(o => upgrade(o, true)).filter(q => !ALL.has(q.id));
      up.forEach(q => ALL.set(q.id, q)); await persist(up);
      try { localStorage.removeItem('kpcAppQso'); } catch (e) {}
    }
    /* tombstones older than a year go */
    const cut = Date.now() - YEAR; [...ALL.values()].forEach(q => { if (q.d && q.u < cut) ALL.delete(q.id); });
    ready = true; view(); draw(); undoChip(); AP.fire('log', { why: 'load', n: ALL.size });
  }

  /* the merge rule: by id, higher v wins, tie → later u wins. Returns the records that changed here. */
  function merge(recs, why) {
    const changed = [];
    (recs || []).forEach(r => {
      if (!r || !r.call) return;
      let q = upgrade(r); const old = ALL.get(q.id);
      /* Nov 18 full review (L10, L19): the link merges FIELD BY FIELD — each edit stamps the fields it changed (fu), so a report fixed on the
         PC and a name added on the phone both survive, and an upload mark never wipes a call-sign fix made on the other device */
      if (old && why === 'merge' && !old.d && !q.d && (old.fu || q.fu)) { const m = fieldMerge(old, q); if (JSON.stringify(m) === JSON.stringify(old)) return; q = m; }
      else if (old && (old.v > q.v || (old.v === q.v && old.u >= q.u))) return;
      if (why === 'file' || why === 'adif') q.u = Math.max(+q.u || 0, Date.now());   /* Nov 18 (L11): new HERE now, so the catch-up sync sends it on */
      ALL.set(q.id, q); changed.push(q);
    });
    if (changed.length) { persist(changed); view(); draw(); AP.fire('log', { why: why || 'merge', recs: changed }); }
    return changed;
  }
  const NOF = { id: 1, v: 1, u: 1, d: 1, src: 1, fu: 1, ref: 1 };
  const ftime = (q, k) => (q.fu && +q.fu[k]) || 0;
  function fieldMerge(a, b) {
    const win = a.v > b.v || (a.v === b.v && a.u >= b.u) ? a : b, lose = win === a ? b : a;
    const out = Object.assign({}, win, { fu: Object.assign({}, win.fu || {}) }); let took = false;
    new Set([...Object.keys(a), ...Object.keys(b)]).forEach(k => {
      if (NOF[k]) return;
      if (ftime(lose, k) > ftime(win, k) && JSON.stringify(lose[k]) !== JSON.stringify(win[k])) { out[k] = lose[k]; out.fu[k] = ftime(lose, k); took = true; }
    });
    if (took) { out.v = Math.max(+a.v || 1, +b.v || 1) + 1; out.u = Math.max(+a.u || 0, +b.u || 0); }
    out.ref = (out.refs || [])[0] || '';
    return out;
  }
  const changes = since => [...ALL.values()].filter(q => q.u > (+since || 0)).sort((a, b) => a.u - b.u);
  function touch(q) { q.v = (+q.v || 1) + 1; q.u = Date.now(); q.src = DEV; }
  function remove(id) { const q = ALL.get(id); if (!q || q.d) return null; q.d = 1; touch(q); persist([q]); view(); draw(); AP.fire('log', { why: 'del', recs: [q] }); return q; }
  function edit(id, patch) { const q = ALL.get(id); if (!q) return null; const now = Date.now(); q.fu = Object.assign({}, q.fu || {}); Object.keys(patch || {}).forEach(k => { if (JSON.stringify(q[k]) !== JSON.stringify(patch[k])) q.fu[k] = now; }); Object.assign(q, patch); q.ref = (q.refs || [])[0] || ''; touch(q); persist([q]); view(); draw(); AP.fire('log', { why: 'edit', recs: [q] }); return q; }

  const D = Object.assign({ khz: 14074, mode: 'FT8' }, LS('kpcAppDock', {}));
  const saveD = () => SV('kpcAppDock', D);

  /* Oct 25 (Brandon: 'make sure log works for any band and any mode'): every band in the ADIF list (kHz), 2190 m to 1 mm, not 160 m–70 cm */
  const BANDS = [['2190m', 135.7, 137.8], ['630m', 472, 479], ['560m', 501, 504], ['160m', 1800, 2000], ['80m', 3500, 4000], ['60m', 5060, 5450], ['40m', 7000, 7300], ['30m', 10100, 10150], ['20m', 14000, 14350],
    ['17m', 18068, 18168], ['15m', 21000, 21450], ['12m', 24890, 24990], ['10m', 28000, 29700], ['8m', 40000, 45000], ['6m', 50000, 54000], ['5m', 54000.001, 69900], ['4m', 70000, 71000], ['2m', 144000, 148000], ['1.25m', 222000, 225000],
    ['70cm', 420000, 450000], ['33cm', 902000, 928000], ['23cm', 1240000, 1300000], ['13cm', 2300000, 2450000], ['9cm', 3300000, 3500000], ['6cm', 5650000, 5925000], ['3cm', 10000000, 10500000],
    ['1.25cm', 24000000, 24250000], ['6mm', 47000000, 47200000], ['4mm', 75500000, 81000000], ['2.5mm', 119980000, 123000000], ['2mm', 134000000, 149000000], ['1mm', 241000000, 250000000], ['submm', 300000000, 7500000000]];
  /* a frequency in each band to start from when only the band is known (PoLo's '20m' command, the BAND box) — phone / data / CW by mode */
  const BANDKHZ = { '2190m': [136, 136, 136], '630m': [475, 474, 475], '560m': [502, 502, 502], '160m': [1900, 1840, 1810], '80m': [3850, 3573, 3530], '60m': [5357, 5357, 5332], '40m': [7200, 7074, 7030], '30m': [10136, 10136, 10110], '20m': [14250, 14074, 14060],
    '17m': [18140, 18100, 18080], '15m': [21300, 21074, 21060], '12m': [24950, 24915, 24910], '10m': [28400, 28074, 28060], '8m': [40680, 40680, 40680], '6m': [50125, 50313, 50090], '5m': [60000, 60000, 60000], '4m': [70200, 70200, 70100], '2m': [146520, 144174, 144050], '1.25m': [223500, 222100, 222100],
    '70cm': [446000, 432174, 432100], '33cm': [927500, 903100, 903100], '23cm': [1294500, 1296174, 1296100] };
  const bandKhz = (b, m) => { const r = BANDKHZ[b]; const i = /CW/.test(m || '') ? 2 : isData(m) ? 1 : 0; if (r) return r[i]; const B = BANDS.find(x => x[0] === b); return B ? Math.round((B[1] + B[2]) / 2) : 0; };
  /* every mode, grouped the way people think of them; 'Other' takes anything typed (kept as typed, in ADIF too) */
  const MODES = [['Voice', ['SSB', 'USB', 'LSB', 'AM', 'FM', 'DSTAR', 'DMR', 'C4FM', 'FREEDV', 'M17']], ['CW', ['CW']],
    ['Digital', ['FT8', 'FT4', 'JS8', 'FST4', 'Q65', 'JT65', 'JT9', 'MSK144', 'RTTY', 'PSK31', 'PSK63', 'PSK125', 'OLIVIA', 'CONTESTIA', 'MFSK16', 'THOR', 'DOMINO', 'MT63', 'HELL', 'SSTV', 'PKT', 'APRS', 'VARA', 'ARDOP', 'WSPR', 'FT2', 'ATV']]];
  const ALLMODES = MODES.flatMap(g => g[1]);
  const isData = m => MODES[2][1].includes(String(m || '').toUpperCase()) || /^(DATA|DIG)/.test(String(m || '').toUpperCase());
  function modeSel(id, cur) {
    cur = String(cur || '').toUpperCase(); const other = cur && !ALLMODES.includes(cur);
    return `<select id="${id}" data-modesel="1">${MODES.map(([g, L]) => `<optgroup label="${g}">${L.map(m => `<option${m === cur ? ' selected' : ''}>${m}</option>`).join('')}</optgroup>`).join('')}<optgroup label="Other"><option value="__other"${other ? ' selected' : ''}>Other… (type it)</option></optgroup></select><input id="${id}O" class="modeo" placeholder="the mode, as ADIF writes it" autocapitalize="characters" spellcheck="false" value="${other ? esc(cur) : ''}"${other ? '' : ' hidden'}>`;
  }
  function modeWire(id) { const s = $(id), o = $(id + 'O'); if (!s || !o) return; s.onchange = () => { o.hidden = s.value !== '__other'; if (!o.hidden) o.focus(); }; }
  const modeVal = id => { const s = $(id), o = $(id + 'O'); if (!s) return ''; return s.value === '__other' ? String(o.value || '').trim().toUpperCase().replace(/[^A-Z0-9 _-]/g, '') : s.value; };
  function bandSel(id, cur) { return `<select id="${id}"><option value="">(from the frequency)</option>${BANDS.map(b => `<option${b[0] === cur ? ' selected' : ''}>${b[0]}</option>`).join('')}</select>`; }
  const bandOf = k => { const b = BANDS.find(r => k >= r[1] && k <= r[2]); return b ? b[0] : ''; };
  const isFT = m => /^FT[428]$/.test(m);
  const modeGroupL = m => { m = String(m || '').toUpperCase(); return /^(SSB|USB|LSB|AM|FM|DV|FREEDV|DIGITALVOICE)$/.test(m) ? 'PH' : /^CW/.test(m) ? 'CW' : 'DG'; };   /* POTA's three modes */
  const rstDef = m => isFT(m) || /^(FT|JS8|FST4|Q65|JT|MSK|WSPR)/.test(m) ? '' : m === 'CW' || isData(m) ? (m === 'SSTV' ? '595' : '599') : '59';
  /* Nov 10: a hand-typed FT8 / FT4 (or other WSJT-type) contact with the boxes empty logs -10 / -10; WSPR has no QSO. Old contacts / the edit sheet / ADIF import keep their blanks. */
  const typedRst = m => /^(FT|JS8|FST4|Q65|JT|MSK)/.test(m) ? '-10' : rstDef(m);
  const base = c => { const P = String(c || '').toUpperCase().split('/').filter(Boolean); if (P.length < 2) return P[0] || ''; return P.filter(x => /\d/.test(x) && /[A-Z]/.test(x)).sort((a, b) => b.length - a.length)[0] || P.sort((a, b) => b.length - a.length)[0]; };   /* Nov 10: 'Q4SPB/P' → Q4SPB (the old pattern gave 'P') */
  const dayOf = ms => new Date(ms).toISOString().slice(0, 10);
  const refList = s => String(s || '').toUpperCase().split(/[\s,;+]+/).map(x => x.trim().replace(/@.*$/, '').replace(/^([A-Z0-9]+)-(\d{1,3})$/, (m, a, b) => a + '-' + b.padStart(4, '0'))).filter(x => /^[A-Z0-9]+-[A-Z0-9]+$/.test(x)).filter((x, i, a) => a.indexOf(x) === i);
  const myRefs = () => refList(AP.S.ref);

  /* ================= MY LOGS (Brandon Oct 25: 'look at PoLo and HAMRS … they start out with a page with a list of your logs and you can
     start new logs from there, let us do that too') =================
     An OPERATION = one log: an activation, a hunting day, an event. Kept in localStorage kpcAppOps {id: {id, name, kind, t0, stops:[{t, refs, grid}],
     notes:[{t, text}]}}; CUR = the open one ('' = every contact). Each contact carries opn (the operation's id). Contacts from before
     this have no opn: they are grouped by UTC day + my park(s), the same way on every device ('d:2026-10-25:US-0050').
     BREAK / 🚗 NEXT PARK (PoLo's BREAK): one log for the day, a new stop with its own park(s) + grid; every contact keeps its own
     myrefs + mg, so SAVE ADIF gives one file per park and the full log in one. */
  const MHZ = k => { const t = Math.round(k * 10) / 10; return (t / 1000).toFixed(t % 1 ? 4 : 3); };   /* 7191.5 → 7.1915 (Oct 26) */
  const OPS = LS('kpcAppOps', {}); let CUR = LS('kpcAppCur', '');
  const opsSave = () => { SV('kpcAppOps', OPS); SV('kpcAppCur', CUR); };
  const autoKey = q => 'd:' + dayOf(q.t) + ':' + ((q.myrefs || []).join('+') || 'hunt');
  const opOf = q => q.opn || autoKey(q);
  function opMeta(id) {
    if (OPS[id]) return OPS[id];
    const m = /^d:(\d{4}-\d{2}-\d{2}):(.*)$/.exec(id || ''); if (!m) return { id, name: 'A log', kind: 'act', t0: 0, stops: [], notes: [] };
    const hunt = m[2] === 'hunt'; return { id, name: (hunt ? '🎯 Hunting ' : '🌲 ' + m[2].replace(/\+/g, ' + ') + ' · ') + m[1], kind: hunt ? 'hunt' : 'act', t0: Date.parse(m[1]), stops: [], notes: [], auto: true };
  }
  function opList() {
    const by = {}; for (const q of Q) { const k = opOf(q); (by[k] = by[k] || []).push(q); }
    Object.keys(OPS).forEach(k => { by[k] = by[k] || []; });
    return Object.entries(by).map(([k, L]) => { const m = opMeta(k); return { id: k, m, n: L.length, t0: m.t0 || (L[0] && L[0].t) || 0, t1: L.length ? L[L.length - 1].t : (m.t0 || 0), parks: [...new Set(L.flatMap(q => q.myrefs || []).concat((m.stops || []).flatMap(x => x.refs || [])))] }; }).sort((a, b) => b.t1 - a.t1);
  }
  function opNew(kind, name, refs, fixedId) {   /* Nov 5: fixedId = the same log on every device (a contest: 'cx-arrl-fd-2026') */
    const id = fixedId || ('o' + Date.now().toString(36) + rnd(3)), t = Date.now(), me = AP.me();
    refs = refs || (kind === 'act' ? myRefs() : []);
    OPS[id] = { id, kind, name: name || (kind === 'hunt' ? '🎯 Hunting ' + dayOf(t) : kind === 'event' ? '🎪 Event ' + dayOf(t) : '🌲 ' + (refs.join(' + ') || 'Activation') + ' · ' + dayOf(t)), t0: t, stops: kind === 'act' ? [{ t, refs, grid: me.grid || '' }] : [], notes: [] };
    if (kind === 'hunt' || kind === 'act') { AP.S.role = kind; AP.save(); const r = $('stRole'); if (r) r.value = kind; }
    CUR = id; opsSave(); view(); draw(); dockChips(); counts(); return id;
  }
  function opOpen(id) { CUR = id || ''; opsSave(); const m = opMeta(id); if (id && m.kind && (m.kind === 'hunt' || m.kind === 'act')) { AP.S.role = m.kind; const st = (m.stops || []).slice(-1)[0]; if (m.kind === 'act' && st && st.refs && st.refs.length) AP.S.ref = st.refs.join(' '); AP.save(); AP.fire('me'); } view(); draw(); dockChips(); counts(); }
  /* BREAK: the next park in the same log */
  function opBreak(refs, grid) {
    if (!CUR || !OPS[CUR]) { const old = CUR; opNew('act', '', myRefs()); if (old) { /* an auto log becomes a real one: its contacts move in */ } }
    const m = OPS[CUR], t = Date.now(); refs = refList((refs || []).join ? refs.join(' ') : refs);
    m.stops = (m.stops || []).concat([{ t, refs, grid: grid || AP.me().grid || '' }]); if (m.kind !== 'act') m.kind = 'act';
    AP.S.ref = refs.join(' '); AP.S.role = 'act'; if (grid) AP.S.grid = grid; AP.save(); const e = $('stRef'); if (e) e.value = AP.S.ref;
    opsSave(); AP.fire('me'); view(); draw(); dockChips(); counts();
    AP.toast('🚗 BREAK: now at ' + esc(refs.join(' + ') || 'a new spot') + '. The count starts again for this park; SAVE ADIF gives a file per park.', 5000, 'log');
  }
  function breakSheet() {
    const near = (breakSheet.near || []).slice(0, 8);
    AP.sheet('🚗 Next park (BREAK)', `<p class="hint">Done here? Keep the same log and start the next park. Every contact keeps the park it was made at; SAVE ADIF then gives one file per park, plus the whole day in one.</p>
      <label class="e wide">THE NEXT PARK NUMBER(S)<input id="bkRefs" name="kpc-my-parks" autocomplete="off" autocapitalize="characters" spellcheck="false" placeholder="US-1234 (two with a space = a 2-fer)"></label>
      <label class="e">MY GRID THERE<input id="bkGrid" autocapitalize="characters" maxlength="6" value="${esc(AP.me().grid || '')}"></label>
      ${near.length ? '<div class="chips wrap">' + near.map(p => `<button type="button" class="chip" data-bkp="${esc(p.ref)}">${esc(p.ref)} ${esc(String(p.name || '').slice(0, 24))}</button>`).join('') + '</div>' : ''}
      <div class="row"><button type="button" class="b" id="bkGps">📍 MY GRID FROM GPS</button><button type="button" class="b gold" id="bkGo">🚗 START THE NEXT PARK</button></div>`);
    parkBox($('bkRefs'));
    document.querySelectorAll('[data-bkp]').forEach(b => { b.onclick = () => { $('bkRefs').value = b.dataset.bkp; }; });
    $('bkGps').onclick = async () => { try { const p = await AP.gps(); if (p) $('bkGrid').value = AP.toGrid(p.la, p.lo); } catch (e) { AP.toast(esc(e.message || e), 5000, 'bad'); } };
    $('bkGo').onclick = () => { const r = refList($('bkRefs').value); if (!r.length) { AP.toast('Type the next park number first.', 3000, 'bad'); return; } AP.shut(); opBreak(r, String($('bkGrid').value || '').trim().toUpperCase()); };
  }
  function opNote(text) {
    text = String(text || '').trim(); if (!text) return;
    if (!CUR || !OPS[CUR]) opNew(AP.me().hunt ? 'hunt' : 'act');
    OPS[CUR].notes = (OPS[CUR].notes || []).concat([{ t: D.hold || Date.now(), text: text.slice(0, 300) }]); opsSave(); draw();
  }
  /* the MY LOGS page (Oct 26, Brandon: 'my logs should be a separate page not on the log screen … longer intro then to my logs page'):
     its own screen ('logs'), opened after the opening at each fresh start, from the 📒 bar at the very top of the LOG screen, or LOGS in the CALL box.
     logsCard(false) = back to the logger. */
  const KIND = { act: ['🌲', 'Activation'], hunt: ['🎯', 'Hunting'], event: ['🎪', 'Event'] };
  function logsCard(show) {
    const el = $('lgOps'); if (!el) return;
    if (show === false) { if (document.body.dataset.screen === 'logs') AP.go('log'); return; }
    const L = opList().slice(0, 40), cur = CUR, today = dayOf(Date.now());
    const card = o => { const k = KIND[o.m.kind] || KIND.act, d = o.t0 ? new Date(o.t0).toISOString().slice(0, 10) : '';
      return `<button type="button" class="opr k-${esc(o.m.kind || 'act')}${o.id === cur ? ' on' : ''}" data-op="${esc(o.id)}"><span class="ki">${k[0]}</span><span class="n">${esc(String(o.m.name).replace(/^[🌲🎯🎪]\s*/u, ''))}</span><span class="d">${esc(k[1])}${d ? ' · ' + (d === today ? 'today' : esc(d)) : ''}${o.parks.length ? ' · ' + esc(o.parks.join(', ')) : ''}${o.m.stops && o.m.stops.length > 1 ? ' · ' + o.m.stops.length + ' parks' : ''}</span><b>${o.n}<small>QSO${o.n === 1 ? '' : 's'}</small></b>${o.id === cur ? '<em>OPEN</em>' : ''}</button>`; };
    el.innerHTML = `<div class="opsh"><div><h2>📒 My logs</h2><p>Start a new log, open an old one, or go straight to the logger with every contact.</p></div>
        <button type="button" class="b gold opgo" data-opx="close">✍ ${cur ? 'BACK TO THIS LOG' : 'GO TO THE LOGGER'} ›</button></div>
      <div class="opsnew"><button type="button" class="opn act" data-opnew="act"><span>🌲</span><b>NEW ACTIVATION</b><i>At a park (or a summit). BREAK moves on to the next park in the same log.</i></button>
        <button type="button" class="opn" data-opnew="hunt"><span>🎯</span><b>NEW HUNTING LOG</b><i>From home or the car: the parks you work go in their own log.</i></button>
        <button type="button" class="opn" data-opnew="event"><span>🎪</span><b>NEW EVENT</b><i>Field Day, a special event, a contest, a club night.</i></button></div>
      <button type="button" class="opr every${!cur ? ' on' : ''}" data-op=""><span class="ki">📚</span><span class="n">Every contact · the regular logger</span><span class="d">all logs together, nothing split</span><b>${Q.length}<small>QSO${Q.length === 1 ? '' : 's'}</small></b>${!cur ? '<em>OPEN</em>' : ''}</button>
      <div class="opsl">${L.length ? '<h3>RECENT LOGS</h3>' + L.map(card).join('') : '<div class="empty">No logs yet. Start one above, or just use the logger: every contact lands in today\'s log by itself.</div>'}</div>`;
    AP.go('logs');
  }
  document.addEventListener('click', e => {
    const n = e.target.closest('[data-opnew]'); if (n) { const k = n.dataset.opnew; if (k === 'act' && !myRefs().length) { AP.sheet('🌲 New activation', `<label class="e wide">MY PARK NUMBER(S)<input id="onRefs" name="kpc-my-parks" autocomplete="off" autocapitalize="characters" spellcheck="false" placeholder="US-0050"></label><div class="row"><button type="button" class="b gold" id="onGo">START THE LOG</button></div>`); parkBox($('onRefs')); $('onGo').onclick = () => { const r = refList($('onRefs').value); AP.S.ref = r.join(' '); AP.save(); AP.shut(); opNew('act', '', r); logsCard(false); AP.fire('me'); }; return; } opNew(k); logsCard(false); AP.toast('📒 New log started: ' + esc(OPS[CUR].name), 3000, 'log'); return; }
    const o = e.target.closest('[data-op]'); if (o) { opOpen(o.dataset.op); logsCard(false); AP.toast('📒 ' + esc(o.dataset.op ? opMeta(o.dataset.op).name : 'Every contact') + ' is open.', 2200, 'log'); return; }
    if (e.target.closest('[data-opx]')) logsCard(false);
  });
  /* ================= THE CLOCK HOLD (PoLo, for paper logs; Brandon Oct 24: 'be able to pause the clock and change clock time') =================
     D.hold = the time the next typed-in contact gets (ms); each logged contact steps it on 1 minute. FT8 / digital contacts always use the real clock. */
  function holdSet(t) { D.hold = t ? Math.round(t / 1000) * 1000 : 0; saveD(); dockChips(); }
  function holdChip() {
    let c = $('dkHold'); if (!c) { $('dkFreq').insertAdjacentHTML('afterend', '<button type="button" class="chip hold" id="dkHold" hidden title="The clock is held: tap to go back to now"></button>'); c = $('dkHold'); c.onclick = () => holdSheet(); }
    c.hidden = !D.hold; if (D.hold) c.textContent = '⏸ CLOCK HELD ' + new Date(D.hold).toISOString().slice(5, 10).replace('-', '/') + ' ' + new Date(D.hold).toISOString().slice(11, 16) + 'z';
  }
  function holdSheet() {
    const t = D.hold || Date.now();
    AP.sheet('⏸ The log clock', `<p class="hint">For putting a paper log in: hold the clock at the time of the first contact; each contact you log moves it on a minute. FT8 and the other digital modes always use the real clock.</p>
      <div class="grid2"><label class="e">DATE (UTC)<input id="hdD" type="date" value="${isoD(t)}"></label><label class="e">TIME (UTC)<input id="hdT" inputmode="numeric" value="${isoT(t).slice(0, 5)}"></label></div>
      <div class="row"><button type="button" class="b gold" id="hdGo">⏸ HOLD AT THIS TIME</button>${D.hold ? '<button type="button" class="b" id="hdNow">▶ BACK TO NOW</button>' : ''}</div>
      <p class="hint">In the CALL box: <b>14:30</b> holds the clock, <b>05-09</b> sets the date, <b>+3m</b> / <b>-1h</b> / <b>+1d</b> moves it, <b>NOW</b> lets go.</p>`);
    $('hdGo').onclick = () => { holdSet(whenOf($('hdD').value, $('hdT').value, t)); AP.shut(); };
    if ($('hdNow')) $('hdNow').onclick = () => { holdSet(0); AP.shut(); AP.toast('▶ The log clock is back to now.', 2000); };
  }
  /* ================= COMMANDS IN THE CALL BOX (PoLo's list; Brandon Oct 24: 'polo has a lot of commands … lets use some of them') =================
     Typed in CALL, then the gold button (or Enter). Returns true when the text was a command (then nothing is logged). */
  function command(raw) {
    const x = String(raw || '').trim().toUpperCase(); if (!x) return false;
    const done = (t, bad) => { AP.toast(t, 3500, bad ? 'bad' : 'log'); return true; };
    const BN = BANDS.map(b => b[0].toUpperCase()), AL = { '2200M': '2190M', '1.25CM': '1.25CM', '220': '1.25M', '440': '70CM', '222': '1.25M', '900': '33CM' };
    if (AL[x] && BN.includes(AL[x])) return command(AL[x]);
    if (BN.includes(x)) { const b = BANDS[BN.indexOf(x)][0]; D.khz = bandKhz(b, D.mode); saveD(); dockChips(); return done('📻 ' + b + ' · ' + (D.khz / 1000).toFixed(3) + ' ' + D.mode); }
    if (ALLMODES.includes(x) || x === 'PHONE' || x === 'SSB') { D.mode = x === 'PHONE' ? 'SSB' : x; saveD(); dockChips(); return done('Mode ' + D.mode); }
    let m;
    if ((m = /^(\d{1,3})(?:\.(\d{1,6}))$/.exec(x)) && +m[1] < 1000) { const mhz = parseFloat(x); D.khz = Math.round(mhz * 1000 * 1000) / 1000; saveD(); dockChips(); return done('📻 ' + mhz.toFixed(3) + ' MHz' + (bandOf(D.khz) ? ' · ' + bandOf(D.khz) : '')); }
    if ((m = /^(\d{3,7})(?:\.(\d{1,3}))?$/.exec(x)) && +m[1] >= 130 && bandOf(parseFloat(x))) { D.khz = parseFloat(x); saveD(); dockChips(); return done('📻 ' + MHZ(D.khz) + ' MHz · ' + bandOf(D.khz)); }
    if ((m = /^\.(\d{1,3})$/.exec(x))) { const k = Math.floor(D.khz / 1000) * 1000 + +m[1].padEnd(3, '0'); D.khz = k; saveD(); dockChips(); return done('📻 ' + (k / 1000).toFixed(3) + ' MHz'); }
    if ((m = /^(\d{1,4})W$/.exec(x))) { AP.S.pwr = m[1]; AP.save(); const e = $('stPwr'); if (e) e.value = m[1]; return done('Power ' + m[1] + ' W (goes on each contact)'); }
    if ((m = /^(\d{1,2}):(\d{2})(?::(\d{2}))?$/.exec(x))) { const b = new Date(D.hold || Date.now()); const t = Date.UTC(b.getUTCFullYear(), b.getUTCMonth(), b.getUTCDate(), +m[1], +m[2], +(m[3] || 0)); holdSet(t); return done('⏸ Clock held at ' + x + 'z. Each contact moves it on a minute. NOW lets go.'); }
    if ((m = /^(?:(\d{4})-)?(\d{1,2})-(\d{1,2})$/.exec(x))) { const b = new Date(D.hold || Date.now()); const t = Date.UTC(m[1] ? +m[1] : b.getUTCFullYear(), +m[2] - 1, +m[3], b.getUTCHours(), b.getUTCMinutes()); if (!isFinite(t)) return false; holdSet(t); return done('⏸ Date set: ' + isoD(t) + ' (clock held).'); }
    if ((m = /^([+-])(\d{1,3})([SMHDW])$/.exec(x))) { const k = { S: 1e3, M: 6e4, H: 36e5, D: 864e5, W: 6048e5 }[m[3]], t = (D.hold || Date.now()) + (m[1] === '-' ? -1 : 1) * +m[2] * k; holdSet(t); return done('⏸ Clock now ' + isoD(t) + ' ' + isoT(t).slice(0, 5) + 'z.'); }
    if (x === 'NOW') { holdSet(0); return done('▶ The log clock is back to now.'); }
    if ((m = /^OP(?:ER)?\/([A-Z0-9/]{3,})$/.exec(x))) { AP.S.op = m[1] === (AP.S.call || '').toUpperCase() ? '' : m[1]; if (AP.S.op && !(AP.S.ops || []).some(o => o.call === m[1])) AP.S.ops = (AP.S.ops || []).concat([{ call: m[1], grid: '', name: '' }]); AP.save(); AP.fire('me'); return done('👤 Operator now ' + m[1] + '.'); }
    if (x === 'BREAK' || x === 'NEXT') { breakSheet(); return true; }
    if (x === 'LOGS') { logsCard(); return true; }
    if ((m = /^NOTE\s+(.+)$/i.exec(String(raw).trim()))) { opNote(m[1]); return done('📝 Note saved in this log.'); }
    if (x === 'SOLAR') { solarNote(); return true; }
    if (x === 'WEATHER' || x === 'WX') { wxNote(); return true; }
    if (/^(QRV|QSY|QRT|SPOTME|SPME)$/.test(x)) { if (G.KPCSpotMe) KPCSpotMe.sheet(x === 'SPOTME' || x === 'SPME' ? '' : x); else done('Spotting is not ready here.', true); return true; }
    if (x === 'HELP' || x === '?') { cmdHelp(); return true; }
    /* Nov 19 2026 (Brandon, PoLo's list + ours): SPME/comment, NOTE alone, CQ, UNDO, GRID, 25WPM, ADIF, the pile-up stack (// or ..)
       and call lists (..NAME). None of these logs a contact. CQ only starts what the voice keyer / the CW screen's F1 already send. */
    if ((m = /^(?:SPOTME|SPME)\/\s*(.{1,60})$/.exec(x))) { if (G.KPCSpotMe) KPCSpotMe.sheet(String(raw).trim().replace(/^\S+?\/\s*/, '').slice(0, 60)); else done('Spotting is not ready here.', true); return true; }
    if (x === 'NOTE') { noteAsk(); return true; }
    if (x === 'BIG') { bigSet(!document.body.classList.contains('biglog')); return done('🔠 Big log line ' + (document.body.classList.contains('biglog') ? 'ON' : 'OFF') + '.'); }
    if (x === 'CQ') return cqCmd(done);
    if (x === 'UNDO') { undoAsk(); return true; }
    if (x === 'ADIF') { saveAdifList(V.length ? V : Q, CUR && OPS[CUR] ? 'this log' : 'your log'); return true; }
    if (x === 'GRID') { const b = $('stGps'); if (b) b.click(); else done('No GPS button here: type GRID EM77.', true); return true; }
    if ((m = /^GRID\s*([A-R]{2}\d{2}(?:[A-X]{2})?)$/.exec(x))) { const g = m[1].slice(0, 4) + m[1].slice(4).toLowerCase(); AP.S.grid = g; AP.save(); const e = $('stGrid'); if (e) e.value = g; AP.fire('me'); return done('📍 My grid is ' + g + ' now (FT8, the log and the map use it).'); }
    if ((m = /^(\d{1,2})WPM$/.exec(x))) return wpmCmd(+m[1], done);
    if ((m = /^(?:\.\.|\/\/)([A-Z0-9]+)$/.exec(x))) { const L = callLists(), k = m[1]; if (!L[k]) return done('No call list called ' + esc(k) + '. Make one: tap ⌨ on the log line → MY CALL LISTS.', true); FILL = L[k].join(', '); return done('📋 ' + esc(k) + ': ' + L[k].length + ' calls in the box. Press ⬆ again to log one contact each.'); }
    if (/[A-Z0-9](\/\/|\.\.)[A-Z0-9]/.test(x)) { const f = x.split(/\/\/+|\.\.+/).map(c => c.replace(/\./g, '/')).filter(Boolean); FILL = f.shift(); STACK = f.concat(STACK); drawStack(); return done('🥞 ' + (f.length + 1) + ' calls stacked. Fix this one, log it, the next comes up by itself.'); }
    /* not a command and not a call sign (a call has a letter AND a digit): say so instead of logging it */
    if (!/,/.test(x) && !(/[A-Z]/.test(x) && /\d/.test(x) && /^[A-Z0-9/.]+$/.test(x)) || /^\d+(\.\d+)?M$/.test(x)) return done('“' + esc(String(raw).trim()) + '” is not a call sign or a command. Type HELP for the list.', true);
    return false;
  }
  /* Nov 19 2026 (Brandon: 'add a way people can find the shortcuts easily'): ⌨ on the log line, HELP in CALL, and a hint under CALL
     while a command is being typed all open / show this list; a tap on a gold word puts it in CALL. */
  const CMDS = [
    ['On the air', [['CQ', 'send my CQ: voice memory 1, or F1 on the CW screen'], ['SPOTME', 'spot me on POTA'], ['SPME/QRV 20 CW', 'spot me with my own comment'], ['QRV', 'spot me: QRV (also QSY, QRT)'], ['25WPM', 'CW speed: the app\'s keyer and the radio']]],
    ['Band, mode, frequency', [['20m', 'the band (40m, 2m…)'], ['CW', 'the mode (SSB, FT8, FM…)'], ['14.070', 'the frequency (or 14070)'], ['.247', 'only the kHz: 14.245 → 14.247'], ['5W', 'my power']]],
    ['Time (paper logs)', [['14:30', 'hold the clock at 14:30z'], ['05-09', 'the date'], ['+3m', 'move the clock (-1h, +1d…)'], ['NOW', 'back to the real time']]],
    ['Pile-ups and groups', [['K4AB//W1XY', 'stack calls: log one, the next comes up'], ['..CLUB', 'one of MY CALL LISTS (below)'], ['K4AB,W1XY', 'one contact each, same reports'], ['K4AB.P', 'a dot is a slash: K4AB/P']]],
    ['My log', [['UNDO', 'take out the last contact (asks first)'], ['NOTE', 'a note in this log (or NOTE text…)'], ['BREAK', 'next park, same log'], ['LOGS', 'my logs'], ['ADIF', 'save this log\'s ADIF file'], ['WEATHER', 'the weather, saved as a note'], ['SOLAR', 'flux + Kp, saved as a note']]],
    ['Me', [['GRID', 'my grid from the GPS (or GRID EM77)'], ['OP/K4XYZ', 'who is at the key'], ['BIG', 'big log line on / off (gloves, sunlight)']]]];
  /* what a tap puts in CALL: an example that needs more typing gives only its start */
  const STEM = { 'SPME/QRV 20 CW': 'SPME/', 'OP/K4XYZ': 'OP/', '..CLUB': '..', 'K4AB//W1XY': '', 'K4AB,W1XY': '', 'K4AB.P': '' };
  const stemOf = k => k in STEM ? STEM[k] : k;
  function cmdHelp() {
    const L = callLists();
    AP.sheet('⌨ Shortcuts for the CALL box', `<p class="hint">Type one in CALL and press the gold ⬆. Nothing is logged. Tap a gold word to put it in CALL.</p><div class="cmdl">` +
      CMDS.map(([h, a]) => `<h3 class="sh">${esc(h)}</h3>` + a.map(([k, d]) => `<p><button type="button" class="chip sm gold" data-cmdx="${esc(k)}">${esc(k)}</button> ${esc(d)}</p>`).join('')).join('') +
      `<h3 class="sh">📋 MY CALL LISTS</h3><p class="hint">One list per line: a name, a colon, the calls. Then ..NAME in CALL fills them in (press ⬆ again to log one contact each).</p>
      <textarea id="cmdLists" rows="4" style="width:100%" spellcheck="false" autocapitalize="characters" placeholder="CLUB: K4AB, W1XY, N4KPC">${esc(Object.keys(L).map(k => k + ': ' + L[k].join(', ')).join('\n'))}</textarea>
      <div class="row"><button type="button" class="b gold" id="cmdListsOk">💾 SAVE MY LISTS</button></div></div>`);
    document.querySelectorAll('[data-cmdx]').forEach(b => { b.onclick = () => { AP.shut(); AP.go('log'); const e = $('eCall'); e.value = stemOf(b.dataset.cmdx); e.focus(); lookUp(); }; });
    $('cmdListsOk').onclick = () => {
      const o = {}; for (const ln of $('cmdLists').value.toUpperCase().split(/\n/)) { const m = /^\s*([A-Z0-9]{1,12})\s*[:=]\s*(.+)$/.exec(ln); if (!m) continue; const c = m[2].split(/[\s,;]+/).map(x => x.replace(/\./g, '/')).filter(x => /[A-Z]/.test(x) && /\d/.test(x)); if (c.length) o[m[1]] = c.slice(0, 50); }
      try { localStorage.setItem('kpcAppLists', JSON.stringify(o)); } catch (e) {}
      AP.toast('📋 ' + Object.keys(o).length + ' call list' + (Object.keys(o).length === 1 ? '' : 's') + ' saved' + (Object.keys(o).length ? ': ' + esc(Object.keys(o).map(k => '..' + k).join(' ')) : '') + '.', 4000, 'log');
    };
  }
  const callLists = () => { const o = LS('kpcAppLists', {}); return o && typeof o === 'object' ? o : {}; };
  /* the hint under CALL while a command is being typed (a call sign has a digit, so it never gets one) */
  function cmdHints(v) {
    const x = String(v || '').toUpperCase().trim(); if (!x) return '';
    if (/^(\.\.|\/\/)/.test(x)) { const L = Object.keys(callLists()); return '📋 ' + (L.length ? 'My call lists: ' + L.map(k => `<button type="button" class="chip sm gold" data-cmdh="..${esc(k)}">..${esc(k)}</button>`).join(' ') : 'No call lists yet: <button type="button" class="chip sm" data-cmdh="?">⌨ MAKE ONE</button>'); }
    if (/[A-Z0-9](\/\/|\.\.)/.test(x)) return '🥞 Pile-up stack: press ⬆ and the first call comes up to fix and log; the rest wait in line.';
    if (/\d/.test(x) || x.length < 2) return '';
    const hit = CMDS.flatMap(g => g[1]).filter(([k]) => !/^(\d|\.|K4AB)/.test(k) && k.replace(/[\/ ].*$/, '').startsWith(x));
    if (!hit.length) return '';
    return '⌨ ' + hit.slice(0, 4).map(([k, d]) => `<button type="button" class="chip sm gold" data-cmdh="${esc(k)}">${esc(k)}</button> <small>${esc(d)}</small>`).join(' · ') + ' · <button type="button" class="chip sm" data-cmdh="?">ALL</button>';
  }
  $('eLook').addEventListener('click', e => { const b = e.target.closest('[data-cmdh]'); if (!b) return; const k = b.dataset.cmdh; if (k === '?') { cmdHelp(); return; } $('eCall').value = stemOf(k); $('eCall').focus(); lookUp(); });
  if ($('dkCmd')) $('dkCmd').onclick = () => cmdHelp();

  /* ================= Nov 19 2026 LOG ROUND (Brandon: '2,3,5,6': one-tap reports, their park looked up, a tidier log line, fix several
     contacts at once + search). Nothing here touches the radio. ================= */

  /* 2. ONE-TAP REPORTS: shown while a call is in CALL; tap = that report in SENT or RCVD (empty still means 59 / 599 / -10) */
  $('lgForm').insertAdjacentHTML('afterend', '<div class="rstq" id="eRstQ" hidden></div>');
  const rstSet = () => { const m = String(D.mode || '').toUpperCase(); return isFT(m) ? ['-05', '-10', '-15'] : /^(SSB|USB|LSB|AM|FM|PHONE|DSTAR|DMR|C4FM|FREEDV|M17)$/.test(m) ? (innerWidth < 520 ? ['59', '57', '55'] : ['59', '57', '55', '53']) : ['599', '579', '559']; };   /* a phone gets three a side so both fit */
  function drawRst() {
    const el = $('eRstQ'); if (!el) return;
    const on = !!$('eCall').value.trim() && !document.body.classList.contains('cx-on') && !/^(NOTE|SPME|SPOTME|GRID|\.\.|\/\/)/i.test($('eCall').value.trim());
    el.hidden = !on; if (!on) return;
    const L = rstSet(), s = $('eRs').value.trim(), r = $('eRr').value.trim();
    el.innerHTML = '<span class="rl">SENT</span>' + L.map(x => `<button type="button" class="chip sm${s === x ? ' on' : ''}" data-rq="s" data-v="${x}">${x}</button>`).join('') +
      '<span class="rl">RCVD</span>' + L.map(x => `<button type="button" class="chip sm${r === x ? ' on' : ''}" data-rq="r" data-v="${x}">${x}</button>`).join('');
  }
  $('eRstQ').addEventListener('click', e => { const b = e.target.closest('[data-rq]'); if (!b) return; const box = $(b.dataset.rq === 's' ? 'eRs' : 'eRr'); box.value = box.value === b.dataset.v ? '' : b.dataset.v; drawRst(); $('eCall').focus(); });
  ['eCall', 'eRs', 'eRr'].forEach(i => $(i).addEventListener('input', () => setTimeout(drawRst, 0)));
  $('lgForm').addEventListener('submit', () => setTimeout(drawRst, 0));
  $('eClr').addEventListener('click', () => setTimeout(drawRst, 0));
  AP.on('dial', () => setTimeout(drawRst, 0));

  /* 3. THEIR PARK LOOKED UP: name, state and grid from a downloaded park pack, else POTA's park page (api.pota.app, the same
     server the spots come from), else the name a spot carried. Kept 90 days in kpcParkInfo. Fills THEIR STATE / GRID when empty. */
  const PI = LS('kpcParkInfo', {});
  async function parkInfo(ref) {
    ref = String(ref || '').toUpperCase(); if (!/^[A-Z0-9]+-\d{3,5}$/.test(ref)) return null;
    if (PI[ref] && Date.now() - PI[ref].at < 90 * 864e5) return PI[ref];
    let r = null;
    try { if (G.KPCParks && KPCParks.have) for (const st of Object.keys(KPCParks.have() || {})) { const pk = await KPCParks.get(st), x = pk && (pk.parks || []).find(q => q.ref === ref);
      if (x) { r = { name: x.name || '', g: isFinite(x.la) && AP.toGrid ? AP.toGrid(x.la, x.lo) : '', st: /^US-[A-Z]{2}$/.test(st) ? st.slice(3) : '', src: 'pack' }; break; } } } catch (e) {}
    if (!r) try { const a = await AP.net.raw('https://api.pota.app/park/' + encodeURIComponent(ref), { ms: 8000 }), j = JSON.parse(a && a.text || 'null');
      if (j && j.name) { const loc = String(j.locationDesc || ''); r = { name: String(j.name).slice(0, 80), g: String(j.grid6 || j.grid4 || '').slice(0, 6), st: /^(US|CA)-[A-Z]{2}$/.test(loc) ? loc.slice(3) : '', loc, src: 'pota' }; } } catch (e) {}
    if (!r && G.KPCParkNames && KPCParkNames[ref]) return { name: KPCParkNames[ref], g: '', st: '', src: 'spot' };
    if (r) { r.at = Date.now(); PI[ref] = r; const ks = Object.keys(PI); if (ks.length > 3000) ks.sort((a, b) => PI[a].at - PI[b].at).slice(0, ks.length - 3000).forEach(k => delete PI[k]); SV('kpcParkInfo', PI); }
    return r;
  }
  const parkTxt = (ref, r) => r ? `🌲 <b>${esc(ref)}</b> ${esc(r.name)}${r.st ? ' · ' + esc(r.st) : r.loc ? ' · ' + esc(r.loc) : ''}${r.g ? ' · ' + esc(r.g) : ''}` : `❓ <b>${esc(ref)}</b>: no park found yet (check the number; with no signal only downloaded states are known)`;
  /* the line under a park box while typing */
  function parkLook(inp) {
    if (!inp || inp.dataset.pl) return; inp.dataset.pl = '1';
    inp.insertAdjacentHTML('afterend', '<div class="look parklk" aria-live="polite"></div>'); const out = inp.nextElementSibling;
    let t = null, n = 0;
    const go = () => { clearTimeout(t); t = setTimeout(async () => { const my = ++n, refs = refList(inp.value).filter(r => /-\d{4,5}$/.test(r)).slice(0, 8); if (!refs.length) { out.innerHTML = ''; return; }
      const L = await Promise.all(refs.map(parkInfo)); if (my !== n) return; out.innerHTML = refs.map((r, i) => parkTxt(r, L[i])).join('<br>'); }, 350); };
    inp.addEventListener('input', go); go();
  }
  /* after the P2P / More sheet: THEIR STATE + GRID from the park (only boxes left empty; a 2-fer in two states fills no state) */
  async function parkFill() {
    const refs = MORE.refs || []; if (!refs.length) return;
    const L = (await Promise.all(refs.map(parkInfo))).filter(Boolean), sts = [...new Set(L.map(x => x.st).filter(Boolean))];
    let n = 0; const A = parkFill.a || (parkFill.a = {});   /* what WE filled last time: a new park replaces it, a hand-typed one stays */
    const stOk = (!MORE.st || MORE.st === A.st) && (!$('eSt').value || $('eSt').value === A.st), gOk = !MORE.g || String(MORE.g).toUpperCase() === String(A.g || '').toUpperCase();
    if (stOk) { const ns = sts.length === 1 ? sts[0] : ''; if (ns || A.st) { MORE.st = ns; $('eSt').value = ns; A.st = ns; n++; } }
    if (gOk && L[0] && L[0].g) { MORE.g = L[0].g; A.g = L[0].g; n++; }
    if (n) { moreChip(); AP.toast(parkTxt(refs[0], L[0]) + (refs.length > 1 ? ' + ' + (refs.length - 1) + ' more' : ''), 3500, 'log'); }
  }
  setTimeout(() => { const p2p0 = $('dkP2p').onclick, more0 = $('dkMore').onclick;   /* after the whole file: those two handlers are set further down */
    $('dkP2p').onclick = () => { p2p0(); parkLook($('shPall')); };
    $('dkMore').onclick = () => { more0(); parkLook($('shQref')); }; }, 0);   /* both sheets call moreChip() when they close: it starts parkFill() when their park changed */

  /* 5. A TIDIER LOG LINE: the dock's chips in two rows on a phone (CSS), and 🔠 BIG LOG LINE (gloves / sunlight): STATION → 📋 LOG or BIG in CALL */
  const bigSet = on => { document.body.classList.toggle('biglog', !!on); try { localStorage.setItem('kpcBigLog', on ? '1' : ''); } catch (e) {} const b = $('stBig'); if (b) b.textContent = '🔠 BIG LOG LINE: ' + (on ? 'ON' : 'OFF'); };
  if ($('stCols') && !$('stBig')) { $('stCols').insertAdjacentHTML('afterend', '<button type="button" class="b" id="stBig" title="Bigger CALL box, report buttons and gold button: for gloves and sunlight"></button>'); $('stBig').onclick = () => bigSet(!document.body.classList.contains('biglog')); }
  bigSet((() => { try { return localStorage.getItem('kpcBigLog') === '1'; } catch (e) { return false; } })());

  /* the dock's chips: row 1 = frequency / mode / my park + ACT-HUNT; row 2 = everything else in ONE row that slides sideways on a phone
     (it was three rows, 220 px of a phone screen). Chips other files add later land in row 2 by themselves. */
  { const ch = document.querySelector('#lgDock .chips'); if (ch && !$('dk2')) { ch.insertAdjacentHTML('beforeend', '<div class="dk2" id="dk2"></div>'); const r2 = $('dk2'), keep = new Set(['dkFreq', 'dkRole', 'dkHold', 'dk2']);
    const mv = () => [...ch.children].forEach(el => { if (!keep.has(el.id)) r2.appendChild(el); }); mv(); new MutationObserver(mv).observe(ch, { childList: true });
    const fade = () => r2.classList.toggle('more', r2.scrollWidth - r2.clientWidth - r2.scrollLeft > 4); r2.addEventListener('scroll', fade, { passive: true }); addEventListener('resize', fade); new MutationObserver(() => setTimeout(fade, 0)).observe(r2, { childList: true, subtree: true }); setTimeout(fade, 300); } }   /* a soft fade on the right edge while more chips sit off screen */
  /* 6. FIND + FIX SEVERAL: 🔍 filters the list (call, park, name, state, note, band, mode); ☑ FIX SEVERAL picks rows, then one sheet
     changes band / frequency, mode, my park(s) or their park(s) on all of them at once */
  const FINDT = {};
  { const st = $('lgStrip'); if (st && !$('lgFind')) { st.insertAdjacentHTML('beforeend', '<button type="button" class="chip" id="lgFind" title="Find a call, park or note in this log">🔍 FIND</button><button type="button" class="chip" id="lgSel" title="Pick several contacts and fix their band, mode or park at once">☑ FIX MANY</button>');
    st.insertAdjacentHTML('afterend', '<div class="lgfind" id="lgFindW" hidden><input id="lgFindT" type="search" autocomplete="off" autocapitalize="characters" spellcheck="false" placeholder="call, park, name, note…" aria-label="Find in this log"><button type="button" class="chip" id="lgFindX" aria-label="Stop finding">✕</button></div><div class="lgselbar" id="lgSelBar" hidden></div>'); } }
  const hits = q => { if (!FIND) return true; const f = FIND; return [q.call, (q.refs || []).join(' '), (q.myrefs || []).join(' '), q.name, q.st, q.note, q.band || bandOf(q.khz), q.mode, q.g].some(x => String(x || '').toUpperCase().includes(f)); };
  $('lgFind').onclick = () => { const w = $('lgFindW'); w.hidden = !w.hidden; if (!w.hidden) $('lgFindT').focus(); else { FIND = ''; $('lgFindT').value = ''; draw(); } };
  $('lgFindX').onclick = () => { FIND = ''; $('lgFindT').value = ''; $('lgFindW').hidden = true; draw(); };
  $('lgFindT').addEventListener('input', () => { FIND = $('lgFindT').value.trim().toUpperCase(); clearTimeout(FINDT.t); FINDT.t = setTimeout(draw, 150); });
  function selBar() {
    const b = $('lgSelBar'); document.body.classList.toggle('lgsel', !!SEL); b.hidden = !SEL; if (!SEL) return;
    b.innerHTML = `<b>☑ ${SEL.size} picked</b><button type="button" class="chip" id="lgSelAll">ALL SHOWN</button><button type="button" class="chip gold" id="lgSelFix"${SEL.size ? '' : ' disabled'}>🔧 FIX THEM</button><button type="button" class="chip" id="lgSelX">✕ DONE</button>`;
    $('lgSelAll').onclick = () => { shownRows().forEach(q => SEL.add(q.id)); selBar(); draw(); };
    $('lgSelX').onclick = () => { SEL = null; selBar(); draw(); };
    $('lgSelFix').onclick = fixSheet;
  }
  const shownRows = () => { const L = V.filter(hits); return L.length > SHOWN ? L.slice(-SHOWN) : L; };
  $('lgSel').onclick = () => { SEL = SEL ? null : new Set(); selBar(); draw(); if (SEL) AP.toast('Tap the contacts to fix, then 🔧 FIX THEM.', 3000); };
  function fixSheet() {
    const ids = [...SEL].filter(id => { const q = ALL.get(id); return q && !q.d; }); if (!ids.length) return;
    AP.sheet('🔧 Fix ' + ids.length + ' contact' + (ids.length > 1 ? 's' : ''), `<p class="hint">Leave a box as it is to keep what each contact has. Only what you change is changed, on all ${ids.length}.</p>
      <div class="grid2"><label class="e">BAND<select id="fxBand"><option value="">(keep)</option>${BANDS.map(b => `<option>${b[0]}</option>`).join('')}</select></label>
      <label class="e">FREQUENCY (kHz)<input id="fxKhz" inputmode="decimal" placeholder="(keep)"></label>
      <label class="e">MODE<select id="fxMode"><option value="">(keep)</option>${MODES.map(([g, L]) => `<optgroup label="${esc(g)}">${L.map(m => `<option>${esc(m)}</option>`).join('')}</optgroup>`).join('')}</select></label>
      <label class="e wide">MY PARK(S)<input id="fxMy" autocomplete="off" autocapitalize="characters" spellcheck="false" placeholder="(keep)"></label>
      <label class="e wide">THEIR PARK(S)<input id="fxTheir" autocomplete="off" autocapitalize="characters" spellcheck="false" placeholder="(keep)"></label></div>
      <label class="ck"><input type="checkbox" id="fxTheirX"> take THEIR park off these (not park to park)</label>
      <div class="row"><button type="button" class="b gold" id="fxOk">🔧 FIX ${ids.length}</button><button type="button" class="b" id="fxNo">CANCEL</button></div>`);
    parkBox($('fxMy')); parkBox($('fxTheir')); parkLook($('fxTheir'));
    $('fxNo').onclick = () => AP.shut();
    $('fxOk').onclick = () => {
      const band = $('fxBand').value, kRaw = $('fxKhz').value.trim(), mode = $('fxMode').value, my = refList($('fxMy').value), th = refList($('fxTheir').value), thX = $('fxTheirX').checked;
      let khz = kRaw ? parseFloat(kRaw) : NaN; if (kRaw && khz < 1000 && khz > 0) khz = Math.round(khz * 1000 * 1000) / 1000;   /* 14.074 typed as MHz */
      if (kRaw && !bandOf(khz)) { AP.toast('That frequency is not in a ham band.', 3000, 'bad'); return; }
      if (!band && !kRaw && !mode && !my.length && !th.length && !thX) { AP.toast('Nothing to change: pick a band, mode or park first.', 3000, 'bad'); return; }
      const recs = [];
      for (const id of ids) { const q = ALL.get(id); if (!q) continue; const pt = {};
        if (kRaw) { pt.khz = khz; pt.band = bandOf(khz); } else if (band && band !== (q.band || bandOf(q.khz))) { pt.band = band; if (!(q.khz && bandOf(q.khz) === band)) pt.khz = 0; }   /* a frequency outside the new band goes: the band alone is a valid ADIF contact */
        if (mode) pt.mode = mode; if (my.length) pt.myrefs = my; if (th.length) pt.refs = th; else if (thX) pt.refs = [];
        const now = Date.now(); q.fu = Object.assign({}, q.fu || {}); let ch = false; Object.keys(pt).forEach(k => { if (JSON.stringify(q[k]) !== JSON.stringify(pt[k])) { q.fu[k] = now; ch = true; } });
        if (!ch) continue; Object.assign(q, pt); q.ref = (q.refs || [])[0] || ''; touch(q); recs.push(q); }
      AP.shut();
      if (!recs.length) { AP.toast('They already had that: nothing changed.', 3000); return; }
      persist(recs); view(); SEL = null; selBar(); draw(); AP.fire('log', { why: 'edit', recs });
      AP.toast('🔧 Fixed ' + recs.length + ' contact' + (recs.length > 1 ? 's' : '') + '.', 3000, 'log');
    };
  }
  let FILL = '', STACK = [], LASTIDS = [];
  function drawStack() {
    let el = $('eStack'); if (!el) { $('eLook').insertAdjacentHTML('beforebegin', '<div class="look" id="eStack" hidden></div>'); el = $('eStack'); }
    el.hidden = !STACK.length;
    el.innerHTML = STACK.length ? '🥞 Next: ' + STACK.map((c, i) => `<button type="button" class="chip sm" data-stk="${i}">${esc(c)}</button>`).join(' ') + ' <button type="button" class="chip sm" data-stk="x" aria-label="Clear the stack">✕</button>' : '';
  }
  document.addEventListener('click', e => { const b = e.target.closest('[data-stk]'); if (!b) return; if (b.dataset.stk === 'x') { STACK = []; drawStack(); return; }
    const i = +b.dataset.stk, cur = $('eCall').value.trim().toUpperCase(); const c = STACK[i]; if (cur) STACK[i] = cur; else STACK.splice(i, 1); $('eCall').value = c; drawStack(); $('eCall').focus(); lookUp(); });
  function noteAsk() {
    AP.sheet('📝 A note in this log', '<label class="e wide">NOTE<textarea id="noteT" rows="3" maxlength="300" style="width:100%"></textarea></label><div class="row"><button type="button" class="b gold" id="noteOk">💾 SAVE THE NOTE</button></div>');
    setTimeout(() => { const t = $('noteT'); if (t) t.focus(); }, 50);
    $('noteOk').onclick = () => { const t = $('noteT').value.trim(); if (!t) { AP.toast('Type the note first.', 2500, 'bad'); return; } AP.shut(); opNote(t); AP.toast('📝 Note saved in this log.', 2500, 'log'); };
  }
  function cqCmd(done) {
    const md = String(D.mode || '').toUpperCase(), act = G.KPCModes && KPCModes.active && KPCModes.active();
    if (md === 'CW') {
      if (act && act.id === 'CW') { KPCModes.op('mac', { i: 0 }); return done('📡 CW F1 (CQ) going out. STOP or Esc stops it.'); }
      return done('CW CQ goes from the CW screen: DIGI → CW, then CQ here or F1 there.', true);
    }
    if (/^(SSB|USB|LSB|AM|FM|PHONE)$/.test(md)) { if (!G.KPCVoice) return done('The voice keyer is not in this app.', true); KPCVoice.play(0); return true; }   /* play() says itself why it cannot (practice call, empty memory, already sending) */
    return done(isFT(md) ? 'FT8 / FT4: use the CQ button on the DIGI screen.' : 'CQ from here works in SSB / AM / FM (voice memory 1) and CW (F1 on the CW screen).', true);
  }
  function wpmCmd(w, done) {
    if (w < 5 || w > 60) return done('CW speed 5 to 60 WPM.', true);
    const out = [];
    if (G.KPCModes5 && KPCModes5.S) { KPCModes5.S.cw.wpm = Math.max(8, Math.min(45, w)); KPCModes5.save(); out.push('the app\'s keyer ' + KPCModes5.S.cw.wpm); }
    const K = G.KPCCat;
    if (K && K.connected && K.connected() && K.extras && K.extras().includes('keyspd') && G.KPCRigX) { KPCRigX.X.keyspd = w; KPCRigX.save(); KPCRigX.go('keyspd', w).then(ok => { if (ok) AP.toast('⏩ The radio\'s keyer: ' + w + ' WPM.', 2500, 'log'); try { KPCRigX.draw(); } catch (e) {} }); out.push('the radio (sending)'); }
    return done(out.length ? '⏩ CW ' + w + ' WPM: ' + out.join(', ') + '.' : 'No CW keyer here to set.', !out.length);
  }
  function undoAsk() {
    let ids = LASTIDS.filter(id => { const q = ALL.get(id); return q && !q.d; });
    if (!ids.length) { const live = V.filter(q => !q.d); const q = live.slice().sort((a, b) => (+b.u || 0) - (+a.u || 0))[0]; if (q) ids = [q.id]; }
    if (!ids.length) { AP.toast('Nothing to take out.', 2500, 'bad'); return; }
    const qs = ids.map(id => ALL.get(id));
    AP.sheet('↩ Take out the last contact?', `<p>${qs.map(q => `<b>${esc(q.call)}</b> · ${esc(q.band || bandOf(q.khz) || '')} ${esc(q.mode)} · ${esc(isoT(q.t).slice(0, 5))}z`).join('<br>')}</p><div class="row"><button type="button" class="b halt" id="undoOk">✕ TAKE ${qs.length > 1 ? 'THEM' : 'IT'} OUT</button><button type="button" class="b" id="undoNo">KEEP</button></div>`);
    $('undoNo').onclick = () => AP.shut();
    $('undoOk').onclick = () => { AP.shut(); qs.forEach(q => remove(q.id)); LASTIDS = []; AP.toast('↩ Taken out: ' + esc(qs.map(q => q.call).join(', ')) + '.', 3000, 'log'); };
  }
  async function solarNote() {
    try { const p = G.KPCProp && KPCProp.solar ? await KPCProp.solar(true) : null; if (p && (p.sfi != null || p.kp != null)) { opNote('☀ Solar: flux ' + (p.sfi != null ? p.sfi : '?') + ', Kp ' + (p.kp != null ? p.kp : '?')); AP.toast('☀ Saved in the log: flux ' + (p.sfi != null ? p.sfi : '?') + ', Kp ' + (p.kp != null ? p.kp : '?'), 4000, 'log'); return; } } catch (e) {}
    AP.toast('No solar numbers right now (no signal?).', 3000, 'bad');
  }
  async function wxNote() {
    const g = AP.gridLL ? AP.gridLL(AP.me().grid || '') : null; let p = null; if (AP.native) { try { p = await AP.gps(); } catch (e) {} }
    const la = p ? p.la : g && g.la, lo = p ? p.lo : g && g.lo; if (!isFinite(la)) { AP.toast('Weather needs your grid (STATION → My station) or the GPS.', 4000, 'bad'); return; }
    try { const r = await AP.net.raw('https://api.open-meteo.com/v1/forecast?latitude=' + la.toFixed(3) + '&longitude=' + lo.toFixed(3) + '&current=temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m&temperature_unit=fahrenheit&wind_speed_unit=mph', { ms: 10000 });
      const j = JSON.parse(r.text || '{}').current; if (!j) throw new Error('no answer');
      const W = { 0: 'clear', 1: 'mostly clear', 2: 'partly cloudy', 3: 'cloudy', 45: 'fog', 48: 'fog', 51: 'drizzle', 53: 'drizzle', 55: 'drizzle', 61: 'rain', 63: 'rain', 65: 'heavy rain', 71: 'snow', 73: 'snow', 75: 'heavy snow', 80: 'showers', 81: 'showers', 82: 'heavy showers', 95: 'thunderstorm', 96: 'thunderstorm', 99: 'thunderstorm' };
      const t = Math.round(j.temperature_2m) + '°F, ' + (W[j.weather_code] || 'weather code ' + j.weather_code) + ', wind ' + Math.round(j.wind_speed_10m) + ' mph, ' + j.relative_humidity_2m + '% humidity';
      opNote('🌦 Weather: ' + t); AP.toast('🌦 Saved in the log: ' + esc(t), 4500, 'log');
    } catch (e) { AP.toast('The weather did not come (no signal?).', 3000, 'bad'); }
  }

  /* ---------------- counts + list ---------------- */
  function counts() {
    const today = dayOf(Date.now());
    /* Oct 25: in an activation log the count is for THIS park (since the last BREAK), so the 10 for the activation is easy to see */
    const m = CUR ? opMeta(CUR) : null, st = m && m.kind === 'act' && (m.stops || []).length ? m.stops[m.stops.length - 1] : null;
    /* Nov 18 full review (L13): the count POTA uses — this UTC day only, each call once per band and mode — and a warning at 0000z */
    const d0 = Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth(), new Date().getUTCDate());
    const uniq = L => new Set(L.map(q => base(q.call) + '|' + (q.band || bandOf(q.khz)) + '|' + modeGroupL(q.mode))).size;
    const n = st ? uniq(V.filter(q => q.t >= Math.max(st.t, d0))) : uniq(Q.filter(q => dayOf(q.t) === today));
    const nl = $('lgN') && $('lgN').previousElementSibling; if (nl) nl.textContent = st ? 'THIS PARK · TODAY UTC' : 'TODAY (UTC)';
    if (st && counts.day && counts.day !== today && V.some(q => q.t >= st.t && q.t < d0)) AP.toast('🕛 New UTC day: the activation count starts again at 0 (POTA counts each UTC day on its own).', 9000, 'bad');
    counts.day = today;
    $('lgN').textContent = n; $('lgAll').textContent = CUR ? V.length : Q.length; const al = $('lgAll').previousElementSibling; if (al) al.textContent = CUR ? 'THIS LOG' : 'ALL';
    const g = AP.me().goal;
    $('lgGoalW').hidden = !g; if (g) $('lgGoal').textContent = n + '/' + g;
    const last = V[V.length - 1];
    $('lgLast').textContent = last ? last.call : '—';
  }
  /* Oct 24 (Brandon: 'add a few more columns … yes to both we need to give users plenty of options'): extra columns on the
     log lines and extra ADIF fields, picked in STATION → Log files → 🧩 COLUMNS & ADIF (localStorage kpcLogOpts) */
  const LO = (() => { try { return Object.assign({ cols: [], ad: { pwr: 1, rig: 1, app: 1, note: 1, auto: 1, cnty: 1 } }, JSON.parse(localStorage.getItem('kpcLogOpts') || '{}')); } catch (e) { return { cols: [], ad: { pwr: 1, rig: 1, app: 1, note: 1 } }; } })();
  if (LO.ad.auto === undefined) LO.ad.auto = 1; if (LO.ad.cnty === undefined) LO.ad.cnty = 1;   /* Oct 24: on for logs saved before these existed */
  const loSave = () => { try { localStorage.setItem('kpcLogOpts', JSON.stringify(LO)); } catch (e) {} };
  const XCOL = { name: ['Name', q => q.name], g: ['Their grid', q => q.g], mine: ['My park', q => (q.myrefs || []).join('+')], note: ['Notes', q => q.note], op: ['Operator', q => q.op], pw: ['Power', q => q.pw ? q.pw + ' W' : ''], mg: ['My grid', q => q.mg], mc: ['My county', q => cty(q.mc)], cn: ['Their county', q => cty(q.cn)] };
  const cty = v => v ? String(v).split(',').reverse().join(', ') : '';
  const xcols = q => LO.cols.filter(k => XCOL[k]).map(k => { const v = XCOL[k][1](q); return v ? `<em class="xc" title="${esc(XCOL[k][0])}">${esc(String(v).slice(0, 40))}</em>` : ''; }).join('');
  function colSheet() {
    const ck = (id, on, t) => `<label class="ck" style="display:flex;margin:7px 0"><input type="checkbox" data-lo="${id}"${on ? ' checked' : ''}> <span>${t}</span></label>`;
    AP.sheet('Columns & ADIF', '<h3 class="sh">Show on each log line</h3>' + Object.entries(XCOL).map(([k, v]) => ck('c:' + k, LO.cols.includes(k), v[0])).join('') +
      '<h3 class="sh">Put in the ADIF file</h3>' + ck('a:pwr', LO.ad.pwr, 'My power (TX_PWR)') + ck('a:rig', LO.ad.rig, 'My rig and antenna (MY_RIG, MY_ANTENNA)') + ck('a:note', LO.ad.note, 'Notes (COMMENT)') + ck('a:auto', LO.ad.auto, 'Automatic comment that shows on QRZ: “POTA activation at US-0050 · Hopkins County, KY” (+ the operator when you run a club call)') + ck('a:cnty', LO.ad.cnty, 'Counties (MY_CNTY, CNTY): mine from GPS / grid, theirs from their park or 6-letter grid') + ck('a:app', LO.ad.app, 'The app\'s own fields (APP_KPC_…: lets the app merge the file back without doubles)') +
      '<p class="hint">Call, date, time, band, frequency, mode, reports, state, grid, name, parks (POTA / SIG) and my grid always go in. Set MY POWER, MY RIG and MY ANTENNA in STATION → My station.</p>',
      () => { LO.cols = Object.keys(XCOL).filter(k => document.querySelector(`[data-lo="c:${k}"]`).checked); ['pwr', 'rig', 'note', 'app', 'auto', 'cnty'].forEach(k => { LO.ad[k] = document.querySelector(`[data-lo="a:${k}"]`).checked ? 1 : 0; }); loSave(); draw(); });
  }
  if ($('stCols')) $('stCols').onclick = colSheet;
  /* Oct 24 (Brandon: 'is on qrz see no cloud'): ☁ = it went up to QRZ / eQSL / Wavelog, ⚠ = an upload failed (tap the line for why) */
  function upMark(q) {
    const u = q.up || {}, ks = Object.keys(u).filter(k => !/T$/.test(k)); if (!ks.length) return '';
    const ok = ks.filter(k => u[k] === 'ok'), bad = ks.filter(k => /^fail/.test(String(u[k])));
    const name = { qrz: 'QRZ', eqsl: 'eQSL', wavelog: 'Wavelog' };
    return ok.length ? ` <i class="upok" title="Uploaded to ${esc(ok.map(k => name[k] || k).join(', '))}">☁</i>` : bad.length ? ` <i class="upbad" title="${esc(bad.map(k => (name[k] || k) + ': ' + u[k]).join(' · '))}">⚠</i>` : '';
  }
  /* Brandon Oct 22: 'call then state under it same with band and signal takes up to much space' — ONE line per contact */
  function row(q) {
    const refs = (q.refs || []).join('+');
    return `<div class="qrow one${SEL && SEL.has(q.id) ? ' pick' : ''}" data-q="${esc(q.id)}" role="row"${SEL ? ' aria-selected="' + SEL.has(q.id) + '"' : ''}>
      <span class="t">${AP.utc(q.t)}</span>
      <span class="c"><b>${esc(q.call)}</b>${q.st ? `<em>${esc(q.st)}</em>` : ''}${refs ? `<u>🌲${esc(refs)}</u>` : ''}${xcols(q)}</span>
      <span class="m"><s>${esc(q.band || bandOf(q.khz) || '')}</s> ${q.khz ? MHZ(q.khz) : ''} <b>${esc(q.mode)}</b></span>
      <span class="r">${esc([q.rs, q.rr].filter(Boolean).join('/'))}${upMark(q)}</span>
      <span class="x"><button type="button" data-del="${esc(q.id)}" aria-label="Take ${esc(q.call)} out of the log">✕</button></span></div>`;
  }
  let SHOWN = 300;
  document.addEventListener('click', e => { if (e.target.closest && e.target.closest('[data-lgmore]')) { SHOWN += 500; draw(); } });
  function draw() {
    const el = $('lgList');
    /* the open log: its contacts, with the BREAK lines (🚗 next park) and the notes (NOTE / WEATHER / SOLAR) in their places */
    /* Nov 18 review (L18): only the newest SHOWN rows are drawn (300, + 500 per SHOW MORE): with 10,000 contacts every ENTER redrew them all */
    if (draw.cur !== CUR) { draw.cur = CUR; SHOWN = 300; }
    const m = CUR ? opMeta(CUR) : null, VF = FIND ? V.filter(hits) : V, V2 = VF.length > SHOWN ? VF.slice(-SHOWN) : VF, t0 = V2.length ? V2[0].t : 0, items = V2.map(q => ({ t: q.t, h: row(q) }));   /* Nov 19: 🔍 FIND shows only matching contacts */
    if (m && !(FIND)) { (m.stops || []).slice(1).forEach(st => items.push({ t: st.t, h: `<div class="qsep brk">🚗 ${esc(AP.utc(st.t))} · BREAK → <b>${esc((st.refs || []).join(' + ') || 'a new spot')}</b>${st.grid ? ' · ' + esc(st.grid) : ''}</div>` }));
      (m.notes || []).forEach(nt => items.push({ t: nt.t, h: `<div class="qsep note">📝 ${esc(AP.utc(nt.t))} · ${esc(nt.text)}</div>` })); }
    if (V.length > SHOWN) for (let i = items.length - 1; i >= 0; i--) if (items[i].t < t0) items.splice(i, 1);
    items.sort((a, b) => a.t - b.t);
    const more = V.length > SHOWN ? `<div class="qsep"><button type="button" class="b sm" data-lgmore="1">⬇ SHOW ${Math.min(500, V.length - SHOWN)} OLDER (${V.length - SHOWN} not drawn)</button></div>` : '';
    const head = ''; if ($('lgBarN')) { $('lgBarN').textContent = m ? m.name : 'Every contact (the regular logger)'; $('lgBarC').textContent = V.length + ' contact' + (V.length === 1 ? '' : 's'); $('lgBar').classList.toggle('every', !m); }
    el.innerHTML = head + (items.length ? items.map(x => x.h).reverse().join('') + more
      : FIND ? '<div class="empty">Nothing in this log matches “' + esc(FIND) + '”.</div>' : '<div class="empty">' + (ready ? 'No contacts yet. Type a call sign below and press the gold button — or work someone on the FT8 screen and it lands here by itself. Type <b>HELP</b> in the CALL box for the commands.' : 'Opening the log…') + '</div>');
    counts();
  }
  document.addEventListener('click', e => { if (e.target.closest('[data-oplist]')) logsCard(); });
  AP.on('log', () => { if (document.body.dataset.screen === 'logs') setTimeout(() => logsCard(), 0); });
  $('lgList').addEventListener('click', e => {
    if (SEL) { const r0 = e.target.closest('[data-q]'); if (r0) { const id = r0.dataset.q; if (SEL.has(id)) SEL.delete(id); else SEL.add(id); r0.classList.toggle('pick', SEL.has(id)); selBar(); } return; }   /* Nov 19: ☑ FIX SEVERAL picks rows */
    const d = e.target.closest('[data-del]');
    if (d) {   /* Brandon Oct 22: 'if deleting a qso needs are you sure? question' */
      const q0 = ALL.get(d.dataset.del); if (!q0) return;
      AP.sheet('Take this contact out?', `<p><b>${esc(q0.call)}</b> · ${esc(q0.band || bandOf(q0.khz))} ${esc(q0.mode)} · ${esc(AP.utc(q0.t, true))} UTC</p>
        <div class="row"><button type="button" class="b halt" id="dlYes">YES, TAKE IT OUT</button><button type="button" class="b" id="dlNo">KEEP IT</button></div>`);
      $('dlYes').onclick = () => { AP.shut(); const q = remove(q0.id); if (q) AP.toast('Took ' + esc(q.call) + ' out of the log.', 3000); };
      $('dlNo').onclick = () => AP.shut();
      return;
    }
    const r = e.target.closest('[data-q]'); if (r) editSheet(r.dataset.q);
  });
  /* tap a line: fix it (the fix syncs like a new contact). Oct 25 (Brandon: 'go back in and correct or add'): the sheet now also fixes the
     DATE, TIME (UTC), FREQUENCY, BAND and any MODE, and the same sheet opens EMPTY for a contact you missed (＋ ADD AN EARLIER CONTACT):
     you give its time and it lands in its place in the list. */
  const isoD = t => new Date(t).toISOString().slice(0, 10), isoT = t => new Date(t).toISOString().slice(11, 19);
  function whenOf(dv, tv, fb) {
    const d = String(dv || '').trim(), tt = String(tv || '').trim().replace(/[^\d:]/g, '');
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(d), n = /^(\d{1,2}):?(\d{2})(?::?(\d{2}))?$/.exec(tt.length === 4 && !/:/.test(tt) ? tt.slice(0, 2) + ':' + tt.slice(2) : tt);
    if (!m || !n) return fb;
    const t = Date.UTC(+m[1], +m[2] - 1, +m[3], +n[1], +n[2], +(n[3] || 0)); return isFinite(t) && +n[1] < 24 && +n[2] < 60 ? t : fb;
  }
  function editSheet(id) {
    const q = id ? ALL.get(id) : null; if (id && !q) return;
    const t0 = q ? q.t : (D.hold || Date.now()) - 60000, nq = q || { call: '', mode: D.mode, khz: D.khz, band: bandOf(D.khz), rs: rstDef(D.mode), rr: rstDef(D.mode), st: '', g: '', refs: [], myrefs: myRefs(), name: '', note: '', mc: '', cn: '' };
    AP.sheet(q ? 'Fix this contact' : '＋ Add an earlier contact', `
      <div class="grid2">
        <label class="e">CALL<input id="edCall" autocapitalize="characters" spellcheck="false" value="${esc(nq.call)}"></label>
        <label class="e">MODE${modeSel('edMode', nq.mode)}</label>
        <label class="e">DATE (UTC)<input id="edDate" type="date" value="${isoD(t0)}"></label>
        <label class="e">TIME (UTC)<input id="edTime" inputmode="numeric" value="${isoT(t0)}" placeholder="14:30"></label>
        <label class="e">FREQUENCY (kHz)<input id="edKhz" inputmode="decimal" value="${nq.khz || ''}" placeholder="14250 (or blank)"></label>
        <label class="e">BAND${bandSel('edBand', nq.khz && bandOf(nq.khz) === nq.band ? '' : nq.band)}</label>
        <label class="e">SENT<input id="edRs" value="${esc(nq.rs)}"></label>
        <label class="e">RCVD<input id="edRr" value="${esc(nq.rr)}"></label>
        <label class="e">THEIR STATE<input id="edSt" autocapitalize="characters" maxlength="2" value="${esc(nq.st)}"></label>
        <label class="e">THEIR GRID<input id="edG" autocapitalize="characters" maxlength="6" value="${esc(nq.g)}"></label>
        <label class="e wide">THEIR PARK(S)<input id="edRefs" name="kpc-their-parks" autocomplete="off" autocapitalize="characters" spellcheck="false" value="${esc((nq.refs || []).join(' '))}" placeholder="US-1234 US-5678"></label>
        <label class="e wide">MY PARK(S)<input id="edMy" name="kpc-my-parks" autocomplete="off" autocapitalize="characters" spellcheck="false" value="${esc((nq.myrefs || []).join(' '))}"></label>
        <label class="e">THEIR NAME<input id="edName" value="${esc(nq.name)}"></label>
        <label class="e">NOTE<input id="edNote" value="${esc(nq.note)}"></label>
        <label class="e">MY COUNTY<input id="edMc" value="${esc(nq.mc || '')}" placeholder="KY,Hopkins"></label>
        <label class="e">THEIR COUNTY<input id="edCn" value="${esc(nq.cn || '')}" placeholder="KY,Warren"></label>
      </div>
      <p class="hint">${q ? 'Station ' + esc(q.station || '?') + ' · operator ' + esc(q.op || '?') + (q.ctl ? ' · control op ' + esc(q.ctl) : '') + '. ' : ''}Times are UTC. The band follows the frequency; pick one only when there is no frequency. Two park numbers with a space = a 2-fer.</p>`,
      () => {
        const call = v('edCall', true).replace(/[<>\s]/g, ''); if (!call || call.length < 3) { AP.toast((q ? 'Not changed' : 'Not added') + ': that call sign is too short.', 3000, 'bad'); return; }
        const kz0 = parseFloat(String(v('edKhz')).replace(',', '.')), kz = isFinite(kz0) && kz0 > 0 && kz0 < 1000 ? kz0 * 1000 : kz0, khz = isFinite(kz) && kz > 100 ? Math.round(kz * 1000) / 1000 : 0, bpick = v('edBand');   /* Nov 18 (L6): '14.250' is MHz = 14250 kHz */
        const band = khz ? (bandOf(khz) || bpick) : bpick, t = whenOf(v('edDate'), v('edTime'), t0), mode = modeVal('edMode') || nq.mode;
        if (!khz && !band) { AP.toast((q ? 'Not changed' : 'Not added') + ': it needs a frequency (kHz or MHz) or a band.', 4000, 'bad'); return false; }
        const patch = { call, mode, t, khz, band, rs: v('edRs'), rr: v('edRr'), st: v('edSt', true), g: v('edG', true), refs: refList(v('edRefs')), myrefs: refList(v('edMy')), name: v('edName'), note: v('edNote'), mc: v('edMc'), cn: v('edCn') };
        if (q) { edit(id, patch); AP.toast('✅ ' + esc(call) + ' fixed.', 2500, 'log'); }
        else { const r = add(Object.assign({}, patch, { opn: CUR || '' })); AP.toast(r.ok ? '✅ ' + esc(call) + ' added at ' + esc(AP.utc(t)) + ' UTC.' : 'Not added: ' + esc(r.msg), 3000, r.ok ? 'log' : 'bad'); }
      });
    modeWire('edMode'); parkBox($('edRefs')); parkBox($('edMy'));
    if (!q) setTimeout(() => { const e = $('edCall'); if (e) e.focus(); }, 60);
  }

  /* ---------------- the dock ---------------- */
  function dockChips() {
    const me = AP.me(), need = me.hunt ? false : !me.ref;
    const f = $('dkFreq');
    f.textContent = MHZ(D.khz) + ' ' + D.mode + (me.ref ? ' · MY PARK ' + myRefs().join('+') : need ? ' · MY PARK?' : '');   /* Brandon Oct 22: it read as THEIR park */
    f.classList.toggle('bad', need);
    $('dkRole').textContent = me.hunt ? '🎯 HUNT' : '🏕 ACT';
    $('eRs').placeholder = rstDef(D.mode) || '-10'; $('eRr').placeholder = rstDef(D.mode) || '-10';
    /* Brandon Oct 22: THEIR STATE always on the line for phone / CW contacts (FT8 fills it from the look-up later) */
    $('eStW').hidden = isFT(D.mode);
    /* 🌲 P2P: only while activating */
    holdChip();
    let bk = $('dkBrk'); if (!bk) { $('dkP2p').insertAdjacentHTML('afterend', '<button type="button" class="chip" id="dkBrk" title="Done at this park? Start the next one in the same log (BREAK)">🚗 NEXT PARK</button>'); bk = $('dkBrk'); bk.onclick = () => breakSheet(); }
    bk.hidden = me.hunt;
    const p = $('dkP2p'); p.hidden = me.hunt;
    p.textContent = MORE.refs && MORE.refs.length ? '🌲 ' + MORE.refs.join('+') : '🌲 P2P'; p.classList.toggle('on', !!(MORE.refs && MORE.refs.length));
  }
  $('dkRole').onclick = () => { AP.S.role = AP.me().hunt ? 'act' : 'hunt'; AP.save(); $('stRole').value = AP.S.role; dockChips(); counts(); };
  $('dkSet').onclick = () => AP.go('station');
  $('dkFreq').onclick = () => {
    AP.sheet('Band, mode and park', `
      <div class="grid2">
        <label class="e">FREQUENCY (kHz)<input id="shKhz" inputmode="decimal" value="${D.khz}"></label>
        <label class="e">MODE${modeSel('shMode', D.mode)}</label>
        <label class="e">BAND${bandSel('shBand', '')}</label>
        <label class="e wide">MY PARK NUMBER(S)<input id="shRef" name="kpc-my-parks" autocomplete="off" autocapitalize="characters" spellcheck="false" value="${esc(AP.S.ref || '')}" placeholder="US-0785 US-1234"></label>
      </div>
      <p class="hint">This is what goes in the log for contacts you type in by hand. Picking a BAND puts the usual frequency for that band and mode. Two park numbers with a space = a 2-fer (every contact counts for both). The FT8 screen uses its own band and mode. You can also type <b>20m</b>, <b>CW</b>, <b>14.070</b> or <b>.247</b> in the CALL box and press the gold button.</p>`,
      () => {
        if ($('shMode')) D.mode = modeVal('shMode') || D.mode;
        const k0 = parseFloat(String($('shKhz') && $('shKhz').value).replace(',', '.')), k = k0 > 0 && k0 < 1000 ? k0 * 1000 : k0, bp = $('shBand') && $('shBand').value;   /* Nov 18 (L6): MHz typed = fine */
        if (bp && (!isFinite(k) || bandOf(k) !== bp)) D.khz = bandKhz(bp, D.mode); else if (isFinite(k) && k > 100) D.khz = Math.round(k * 1000) / 1000;
        if ($('shRef')) { AP.S.ref = refList($('shRef').value).join(' '); AP.save(); $('stRef').value = AP.S.ref; }
        saveD(); dockChips();
      });
    parkBox($('shRef')); modeWire('shMode');
  };
  $('dkMore').onclick = () => {
    MORE.st = v('eSt', true) || MORE.st || '';
    AP.sheet('More for this contact', `
      <div class="grid2">
        <label class="e wide">THEIR PARK NUMBER(S)<input id="shQref" name="kpc-their-parks" autocomplete="off" autocapitalize="characters" spellcheck="false" value="${esc((MORE.refs || []).join(' '))}" placeholder="US-1234 US-5678"></label>
        <label class="e">THEIR NAME<input id="shName" value="${esc(MORE.name || '')}"></label>
        <label class="e">THEIR STATE<input id="shSt" autocapitalize="characters" spellcheck="false" maxlength="2" value="${esc(MORE.st || '')}"></label>
        <label class="e">THEIR GRID<input id="shGrid" autocapitalize="characters" spellcheck="false" maxlength="6" value="${esc(MORE.g || '')}"></label>
        <label class="e">NOTE<input id="shNote" value="${esc(MORE.note || '')}"></label>
      </div>
      <p class="hint">These go with the next contact you log, then clear themselves. Park-to-park contacts need their park number; two with a space = their 2-fer.</p>`,
      () => { MORE = { refs: refList(v('shQref')), name: v('shName'), st: v('shSt', true), g: v('shGrid', true), note: v('shNote') }; $('eSt').value = MORE.st; moreChip(); dockChips(); });
    parkBox($('shQref'));
  };
  /* 🌲 P2P (Brandon Oct 22): their park number in two taps — the prefix is ready, type the digits */
  /* Brandon Oct 22: 'prefix list not right or complete' — POTA's references now use the country's two-letter code (US-, CA-,
     GB-, DE-…); this is every prefix in POTA's park list (Oct 22), the usual ones first */
  const PFX = ['US', 'CA', 'MX'].concat('AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HN HR HU ID IE IL IM IN IQ IR IS IT JE JM JO JP KE KG KH KM KN KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PR PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TK TL TN TO TR TT TW TZ UA UG UM US UY VC VE VG VI VN VU WS YE YT ZA ZM ZW'.split(' ').filter(x => !['US', 'CA', 'MX'].includes(x)));
  /* 🌲 P2P (Brandon Oct 22: 'make it all one box and space bar adds a coma automatically' — he has had 7-fers): ONE box,
     the prefix is already typed, SPACE = a comma and the same prefix again, as many parks as they have */
  $('dkP2p').onclick = () => {
    const mine = (String(myRefs()[0] || '').match(/^([A-Z0-9]+)-/) || [])[1] || 'US';
    const cur = (MORE.refs || []).join(', ');
    AP.sheet('Their park(s) — park to park', `
      <label class="e wide">THEIR PARK NUMBER(S)<input id="shPall" name="kpc-p2p" autocomplete="off" autocapitalize="characters" spellcheck="false" value="${esc(cur || mine + '-')}" enterkeyhint="done"></label>
      <div class="row pfxrow"><span class="hint" style="margin:0 6px 0 0">COUNTRY:</span>${['US', 'CA', 'MX', 'GB', 'DE', 'FR'].map(x => `<button type="button" class="b sm" data-pfx="${x}">${x}</button>`).join('')}<select id="shPfx" class="selc" aria-label="Other country prefix"><option value="">more…</option>${PFX.slice(3).filter((x, i, a) => a.indexOf(x) === i).sort().map(x => `<option>${x}</option>`).join('')}</select></div>
      <div class="row"><button type="button" class="b gold" id="shPok">✓ USE IT</button>${cur ? '<button type="button" class="b" id="shPno">✕ NOT P2P</button>' : ''}</div>
      <p class="hint">Type the number. SPACE starts the next park (a comma and the same prefix go in by themselves) — a 2-fer, a 7-fer, as many as they have. Another country? Tap its COUNTRY button (or type over the prefix). Goes with the next contact you log, then clears itself.</p>`,
      () => { MORE.refs = refList(v('shPall')); const odd = MORE.refs.filter(r => !PFX.includes(r.split('-')[0]) && !/FF$/.test(r.split('-')[0])); if (odd.length) AP.toast('Check ' + esc(odd.join(', ')) + ': that prefix is not one of POTA\'s.', 5000, 'bad'); moreChip(); dockChips(); });
    const inp = $('shPall'); parkBox(inp, mine);
    /* Oct 24 (Brandon: 'their p2p starts out with us … cant change it'): COUNTRY buttons swap the prefix of the park being typed */
    const setPfx = x => { if (!x) return; const parts = inp.value.split(/,\s*/); const last = parts.pop() || ''; parts.push(x + '-' + (last.replace(/^[A-Z0-9]*-?/i, '') || '')); inp.value = parts.join(', '); inp.focus(); try { inp.setSelectionRange(inp.value.length, inp.value.length); } catch (e) {} };
    document.querySelectorAll('[data-pfx]').forEach(b => { b.onclick = () => setPfx(b.dataset.pfx); });
    $('shPfx').onchange = () => { setPfx($('shPfx').value); $('shPfx').value = ''; };
    setTimeout(() => { try { inp.focus(); inp.setSelectionRange(inp.value.length, inp.value.length); } catch (e) {} }, 60);
    inp.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); AP.shut(); } });
    $('shPok').onclick = () => AP.shut();
    if ($('shPno')) $('shPno').onclick = () => { inp.value = ''; AP.shut(); };
  };
  /* any park box: SPACE (or a typed comma) → ', ' + the last prefix, so several parks need no punctuation */
  function parkBox(inp, dflt) {
    if (!inp || inp.dataset.pk) return; inp.dataset.pk = '1';
    const fix = () => {
      const s = inp.value, at = inp.selectionStart == null ? s.length : inp.selectionStart;
      if (!/[ ,]$/.test(s.slice(0, at)) || /,\s?$/.test(s.slice(0, at - 1))) return;
      const before = s.slice(0, at - 1).replace(/[\s,]+$/, ''), pf = ((before.match(/([A-Z0-9]+)-[A-Z0-9]*$/i) || [])[1] || dflt || 'US').toUpperCase();
      if (!before || /-$/.test(before)) { inp.value = s.slice(0, at - 1) + s.slice(at); try { inp.setSelectionRange(at - 1, at - 1); } catch (e) {} return; }   /* nothing typed yet for this park: no new one */
      const nv = before + ', ' + pf + '-'; inp.value = nv + s.slice(at); try { inp.setSelectionRange(nv.length, nv.length); } catch (e) {}
    };
    inp.addEventListener('input', fix);
  }
  const v = (id, up) => { const e = $(id); let x = e ? e.value.trim() : ''; return up ? x.toUpperCase() : x; };
  let MORE = {};
  function moreChip() { const n = Object.values(MORE).filter(x => Array.isArray(x) ? x.length : x).length; $('dkMore').textContent = n ? '✏️ ' + n : '✏️'; const k = (MORE.refs || []).join(); if (k !== moreChip.k) { moreChip.k = k; if (k && G.KPCLog) setTimeout(() => parkFill(), 50); } }

  /* ---------------- call book (Brandon Oct 24: 'the auto look up is not working … the world will be able to use it') ----------------
     QRZ XML when the ham has a QRZ XML subscription (worldwide, STATION → Log files → 📖 CALL LOOK-UP), else free:
     callook.info (FCC) for US calls, HamDB for the rest. Answers kept 30 days in localStorage kpcAppLkC. */
  const LK = (() => { try { const o = JSON.parse(localStorage.getItem('kpcAppLk') || '{}'); return G.KPCSec ? KPCSec.openObj(o, ['pass']) : o; } catch (e) { return {}; } })();   /* Nov 18 (SEC-2): the QRZ password sealed at rest */
  const LKC = (() => { try { return JSON.parse(localStorage.getItem('kpcAppLkC') || '{}'); } catch (e) { return {}; } })();
  const lkSave = () => { try { localStorage.setItem('kpcAppLk', JSON.stringify(G.KPCSec ? KPCSec.sealObj(LK, ['pass']) : LK)); } catch (e) {} };
  const tc = x => { x = String(x || '').trim(); return !x || /[a-z]/.test(x) ? x : x.toLowerCase().replace(/\b([a-z])/g, m => m.toUpperCase()); };
  const okCall = c => /^[A-Z0-9]{1,3}[0-9][A-Z0-9]{0,3}[A-Z]$/.test(c) && /\d/.test(c);
  const jget = async url => { const r = await AP.net.raw(url, { ms: 9000 }); if (!r.ok) throw new Error(r.err || 'HTTP ' + r.status); return r.text; };
  let QK = '';
  async function qrzXml(b) {
    const tag = (x, t) => { const m = x.match(new RegExp('<' + t + '>([^<]*)</' + t + '>', 'i')); return m ? m[1].replace(/&amp;/g, '&') : ''; };
    for (let i = 0; i < 2; i++) {
      if (!QK) { const x = await jget('https://xmldata.qrz.com/xml/current/?username=' + encodeURIComponent(LK.user) + ';password=' + encodeURIComponent(LK.pass) + ';agent=KPCapp'); QK = tag(x, 'Key'); if (!QK) { LK.err = tag(x, 'Error') || 'QRZ did not sign in'; lkSave(); return null; } LK.err = ''; lkSave(); }
      const x = await jget('https://xmldata.qrz.com/xml/current/?s=' + QK + ';callsign=' + encodeURIComponent(b));
      const er = tag(x, 'Error'); if (/session|invalid/i.test(er) && !/not found/i.test(er)) { QK = ''; continue; }
      if (!tag(x, 'call')) return null;
      const st = tag(x, 'state'), cn = tag(x, 'county');
      return { name: tc([tag(x, 'fname'), tag(x, 'name')].filter(Boolean).join(' ')), qth: tc(tag(x, 'addr2')), st, g: tag(x, 'grid').toUpperCase(), la: +tag(x, 'lat') || null, lo: +tag(x, 'lon') || null, cty: tag(x, 'country'), cn: st && cn ? st + ',' + cn : '', src: 'QRZ' };
    }
    return null;
  }
  async function callook(b) { const j = JSON.parse(await jget('https://callook.info/' + encodeURIComponent(b) + '/json')); if (!j || j.status !== 'VALID') return null;
    const l2 = String((j.address && j.address.line2) || ''), m = l2.match(/^(.*?),\s*([A-Z]{2})\s+\d/);
    return { name: tc(j.name), qth: tc(m ? m[1] : l2), st: m ? m[2] : '', g: String((j.location && j.location.gridsquare) || '').toUpperCase(), la: j.location ? +j.location.latitude : null, lo: j.location ? +j.location.longitude : null, cty: 'United States', src: 'FCC' }; }
  async function hamdb(b) { const j = JSON.parse(await jget('https://api.hamdb.org/v1/' + encodeURIComponent(b) + '/json/kpcapp')); const h = j && j.hamdb, x = h && h.callsign;
    if (!x || !x.call || x.call === 'NOT_FOUND') return null;
    return { name: tc([x.fname, x.mi, x.name].filter(Boolean).join(' ')), qth: tc(x.addr2), st: x.state || '', g: String(x.grid || '').toUpperCase(), la: +x.lat || null, lo: +x.lon || null, cty: x.country || '', src: 'HamDB' }; }
  async function callBook(call) {
    const b = base(call); if (!okCall(b)) return null;
    const c = LKC[b]; if (c && Date.now() - c.t < 30 * 864e5) return c;
    if (LK.off) return null;
    const us = /^(A[A-L]|[KNW])[0-9A-Z]*\d/.test(b);
    let r = null;
    if (LK.user && LK.pass) r = await qrzXml(b).catch(() => null);
    if (!r && us) r = await callook(b).catch(() => null);
    if (!r) r = await hamdb(b).catch(() => null);
    if (r) { r.t = Date.now(); LKC[b] = r; const k = Object.keys(LKC); if (k.length > 800) k.sort((x, y) => LKC[x].t - LKC[y].t).slice(0, 100).forEach(x => delete LKC[x]); try { localStorage.setItem('kpcAppLkC', JSON.stringify(LKC)); } catch (e) {} }
    return r;
  }
  function lkSheet() {
    AP.sheet('📖 Call look-up', `<p class="hint">Type a call on the LOG line and the app fills in their name, state and grid (only boxes you have left empty). Free for everyone: the FCC (US calls) and HamDB. With a <b>QRZ XML subscription</b> it uses QRZ first, which covers the whole world and gives the county too.</p>
      <label class="ck" style="display:flex;margin:8px 0"><input type="checkbox" id="lkOn"${LK.off ? '' : ' checked'}> <span>Look up calls as I type them</span></label>
      <label class="e">QRZ USER NAME (OPTIONAL)<input id="lkU" autocomplete="off" autocapitalize="characters" value="${esc(LK.user || '')}"></label>
      <label class="e">QRZ PASSWORD<input id="lkP" type="password" autocomplete="off" value="${esc(LK.pass || '')}"></label>
      <p class="hint">${LK.err ? '⚠ QRZ said: ' + esc(LK.err) + '. Without a QRZ XML subscription the free look-ups still work.' : 'Kept on this device only.'}</p>`,
      () => { LK.off = !$('lkOn').checked; const u = $('lkU').value.trim(), p = $('lkP').value; if (u !== LK.user || p !== LK.pass) { QK = ''; LK.err = ''; } LK.user = u; LK.pass = p; lkSave(); lookUp(); });
  }
  if ($('stLook')) $('stLook').onclick = lkSheet;
  /* ---------------- my POTA files (Brandon Oct 24: 'note about the hunter and activators csv file for the logger app') ----------------
     pota.app → My Stats → hunted parks / activated parks → ⬇ EXPORT CSV gives hunter_parks.csv and activator_parks.csv.
     Kept in localStorage kpcAppPotaF {h:{refs,t,file}, a:{refs,t,file}}; the log's own contacts count too. */
  const PF = (() => { try { return JSON.parse(localStorage.getItem('kpcAppPotaF') || '{}'); } catch (e) { return {}; } })();
  const pfSave = () => { try { localStorage.setItem('kpcAppPotaF', JSON.stringify(PF)); } catch (e) {} };
  const pfSet = k => new Set((PF[k] && PF[k].refs) || []);
  let PFH = pfSet('h'), PFA = pfSet('a');
  function csvRows(t) { const out = []; String(t).split(/\r?\n/).forEach(line => { if (!line.trim()) return; const r = []; let cur = '', q = false; for (let i = 0; i < line.length; i++) { const ch = line[i]; if (q) { if (ch === '"' && line[i + 1] === '"') { cur += '"'; i++; } else if (ch === '"') q = false; else cur += ch; } else if (ch === '"') q = true; else if (ch === ',') { r.push(cur); cur = ''; } else cur += ch; } r.push(cur); out.push(r); }); return out; }
  function potaFile(text, name) {
    const rows = csvRows(text), hd = (rows[0] || []).map(x => x.trim().toLowerCase()), ri = hd.indexOf('reference'), ai = hd.indexOf('activations');
    const act = ai >= 0 || /activator/i.test(name || ''), kind = act ? 'a' : 'h', refs = new Set();
    if (ri >= 0) rows.slice(1).forEach(r => { const ref = String(r[ri] || '').trim().toUpperCase(); if (!/^[A-Z0-9]{1,4}-\d{4,6}$/.test(ref)) return; if (act && ai >= 0 && !(+r[ai] > 0)) return; refs.add(ref); });
    else (String(text).toUpperCase().match(/\b[A-Z0-9]{1,4}-\d{4,6}\b/g) || []).forEach(x => refs.add(x));
    if (!refs.size) return { ok: false, msg: 'No park numbers in ' + (name || 'that file') + '. Is it hunter_parks.csv or activator_parks.csv from pota.app → My Stats?' };
    PF[kind] = { refs: [...refs], t: Date.now(), file: name || '' }; pfSave(); PFH = pfSet('h'); PFA = pfSet('a'); AP.fire('potafile', kind);
    return { ok: true, kind, n: refs.size };
  }
  /* Oct 30: the POTA sign-in (kpc-pota.js) hands over the same two lists straight from pota.app */
  function potaSet(kind, refs, label) { if (!refs || !refs.length) return; PF[kind] = { refs: [...new Set(refs)], t: Date.now(), file: label || 'pota.app' }; pfSave(); PFH = pfSet('h'); PFA = pfSet('a'); LH = LA = null; AP.fire('potafile', kind); }
  /* a park counts as hunted / activated when the POTA file says so OR a contact in this log does */
  let LH = null, LA = null;   /* parks in this log, rebuilt after any change */
  AP.on('log', () => { LH = LA = null; });
  const logSets = () => { if (!LH) { LH = new Set(); LA = new Set(); for (const q of ALL.values()) if (!q.d) { (q.refs || []).forEach(r => LH.add(r)); (q.myrefs || []).forEach(r => LA.add(r)); } } };
  const huntedRef = r => { logSets(); return PFH.has(r) || LH.has(r); };
  const activatedRef = r => { logSets(); return PFA.has(r) || LA.has(r); };
  function pfSheet() {
    const st = k => { const x = PF[k]; if (!x) return 'not loaded'; const d = Math.round((Date.now() - x.t) / 864e5); return `<b>${x.refs.length}</b> parks from ${esc(x.file || 'a file')}, ${d ? d + ' day' + (d > 1 ? 's' : '') + ' ago' : 'today'}${d > 30 ? ' — <b style="color:var(--bad)">over a month old: get a fresh copy</b>' : ''}`; };
    AP.sheet('📄 My POTA files', `<p class="hint">Load the two files POTA makes for you, so the app knows which parks are <b>new to you</b>: SPOTS can show only new-to-you parks, the 'park you still need' alert uses them, and NEXT PARK marks the ones you have never activated.</p>
      <h3 class="sh">Where to get them</h3>
      <ol class="hint" style="margin:0 0 10px 18px;padding:0"><li>Sign in at <b>pota.app</b> (a browser on the phone or PC).</li><li>Tap your call (top right) → <b>My Stats</b>.</li><li>Open <b>Hunted parks</b> → <b>⬇ EXPORT CSV</b> = <b>hunter_parks.csv</b>.</li><li>Open <b>Activated parks</b> → <b>⬇ EXPORT CSV</b> = <b>activator_parks.csv</b>.</li><li>Come back here and pick each file (they land in Downloads).</li></ol>
      <p>🎯 Hunter file: ${st('h')}</p><p>🌲 Activator file: ${st('a')}</p>
      <input type="file" id="pfIn" accept=".csv,text/csv,text/plain" multiple hidden>
      <div class="row"><button type="button" class="b gold" id="pfPick">📄 PICK A FILE (either one)</button>${PF.h || PF.a ? '<button type="button" class="b" id="pfClr">FORGET THEM</button>' : ''}</div>
      <p class="hint">Get fresh copies now and then (once a month is fine); contacts you log in the app count by themselves in between.</p>`);
    $('pfPick').onclick = () => $('pfIn').click();
    $('pfIn').onchange = async e => { const msgs = []; for (const f of e.target.files) { const r = potaFile(await f.text(), f.name); msgs.push(r.ok ? (r.kind === 'a' ? '🌲 ' + r.n + ' activated parks' : '🎯 ' + r.n + ' hunted parks') : r.msg); } AP.toast(esc(msgs.join(' · ')), 6000, msgs.some(m => /No park/.test(m)) ? 'bad' : 'log'); AP.shut(); pfSheet(); draw(); };
    if ($('pfClr')) $('pfClr').onclick = () => { delete PF.h; delete PF.a; pfSave(); PFH = pfSet('h'); PFA = pfSet('a'); AP.shut(); pfSheet(); };
  }
  if ($('stPota')) $('stPota').onclick = pfSheet;
  /* a gentle reminder once a month */
  setTimeout(() => { const old = ['h', 'a'].filter(k => PF[k] && Date.now() - PF[k].t > 31 * 864e5); if (old.length && Date.now() - (+localStorage.getItem('kpcAppPotaR') || 0) > 7 * 864e5) { try { localStorage.setItem('kpcAppPotaR', Date.now()); } catch (e) {} AP.toast('📄 Your POTA ' + (old.length > 1 ? 'files are' : old[0] === 'h' ? 'hunter file is' : 'activator file is') + ' over a month old: STATION → Log files → MY POTA FILES.', 7000); } }, 20000);
  /* who is this? (my own log, then the call book) */
  let lkN = 0, LKHIT = null;
  function lookUp() {
    const c = base($('eCall').value);
    const el = $('eLook'), n = ++lkN; LKHIT = null;
    { const h = cmdHints($('eCall').value); if (h) { el.innerHTML = h; return; } }   /* Nov 19: typing a shortcut shows what it does */
    if (!c || c.length < 3) { el.innerHTML = ''; return; }
    const hit = Q.filter(q => base(q.call) === c);
    const last = hit[hit.length - 1];
    /* Nov 18 full review (L20): a real DUPE (same call, band, mode and UTC day — and my same park) says so in red */
    const dB = bandOf(D.khz), dM = modeGroupL(D.mode), dDay = dayOf(Date.now()), myp = myRefs().join('+');
    const dupe = hit.some(q => dayOf(q.t) === dDay && (q.band || bandOf(q.khz)) === dB && modeGroupL(q.mode) === dM && (q.myrefs || []).join('+') === myp);
    { const gb = $('eGo') || document.querySelector('#scrLog .go'); if (gb) gb.classList.toggle('dupe', dupe); }   /* the gold LOG button turns red-edged on a dupe too */
    const dTag = dupe ? '<span class="st bad" id="eDupe" style="display:inline-block;padding:2px 8px;font-weight:700">DUPE: ' + esc(dB) + ' ' + esc(D.mode) + ' today (UTC)</span> ' : '';
    const mine = dTag + (!hit.length ? '<span class="nw">🆕 First time with this call.</span>' : `🔁 Worked ${hit.length} time${hit.length > 1 ? 's' : ''} · last <b>${esc(last.band || bandOf(last.khz))} ${esc(last.mode)}</b> on ${esc(new Date(last.t).toISOString().slice(0, 10))}${last.refs && last.refs.length ? ' · <b>' + esc(last.refs.join('+')) + '</b>' : ''}`);
    el.innerHTML = mine;
    if (!okCall(c) || LK.off) return;
    clearTimeout(lookUp.t); lookUp.t = setTimeout(async () => {
      const r = await callBook(c); if (n !== lkN || !r) return;
      LKHIT = Object.assign({ call: c }, r);
      const where = [r.qth, r.st && r.st !== r.qth ? r.st : '', r.cty && !/^United States/.test(r.cty) ? r.cty : ''].filter(Boolean).join(', ');
      el.innerHTML = `📖 <b>${esc(r.name || '?')}</b>${where ? ' · ' + esc(where) : ''}${r.g ? ' · ' + esc(r.g) : ''} <small style="opacity:.6">(${esc(r.src)})</small><br>` + mine;
      if (!isFT(D.mode) && $('eSt') && !$('eSt').value && r.st && /^[A-Z]{2}$/.test(r.st)) $('eSt').value = r.st;
    }, 450);
  }
  $('eCall').oninput = () => { let x = $('eCall').value.toUpperCase(); const free = /^(NOTE\b|SPME\/|SPOTME\/|GRID\b)/.test(x); if (!free) x = x.replace(/\s/g, ''); if (!free) x = x.replace(/(.)(?:[.\/]{2,})/g, (a, c) => c + '//');   /* Nov 19: a pile-up stack (.. or //, after the dot-to-slash below has turned one dot into a slash) */ if (!free && /[A-Z]\d*\.[A-Z0-9]*$/.test(x) && /[A-Z]/.test(x.split('.')[0])) x = x.replace(/\./g, '/'); $('eCall').value = x; clearTimeout(lkT); lkT = setTimeout(lookUp, 150); };
  let lkT = null;
  $('eSt').oninput = () => { $('eSt').value = $('eSt').value.toUpperCase().replace(/[^A-Z]/g, ''); };
  $('eClr').onclick = () => { ['eCall', 'eRs', 'eRr', 'eSt'].forEach(i => { $(i).value = ''; }); $('eLook').innerHTML = ''; $('eCall').focus(); };

  /* ---------------- logging ---------------- */
  /* their county (Oct 24): from their park's pin (offline park pack) or a 6-letter grid; my county if it was not known yet.
     Filled a moment after logging (needs signal the first time a spot is looked up; answers are kept on the device). */
  async function cntyFill(q) {
    try {
      const up = {};
      if (!q.mc && AP.me().cnty) up.mc = AP.me().cnty;
      const bk = await callBook(q.call).catch(() => null);   /* name / state / grid for contacts logged from FT8 or the remote */
      /* Nov 18 full review (L12): a station at a park, /P /M /MM, or with a prefix (VE3/K4ABC) is NOT at its call-book home: state and grid
         come from the park's pin (below), never from the home address */
      const away = (q.refs || []).length > 0 || /\/(P|M|MM|AM|QRP|PM)$/.test(q.call) || /^[A-Z0-9]{1,4}\/[A-Z0-9]/.test(q.call);
      if (bk) { if (!q.name && bk.name) up.name = bk.name; if (!away && !q.st && /^[A-Z]{2}$/.test(bk.st || '')) up.st = bk.st; if (!away && !q.g && bk.g) up.g = bk.g; if (!q.cn && bk.cn && !away) up.cn = bk.cn; }
      if (away && (!q.g || !q.st) && q.ref && G.KPCParks && KPCParks.loaded) {
        for (const pk of await KPCParks.loaded()) { const x = (pk.parks || []).find(z => z.ref === q.ref); if (x && isFinite(x.la)) { if (!q.g && AP.toGrid) up.g = AP.toGrid(x.la, x.lo); if (!q.st && /^[A-Z]{2}$/.test(x.st || '')) up.st = x.st; break; } }
      }
      if (!q.cn && AP.county) {
        let p = null;
        if (q.ref && G.KPCParks && KPCParks.loaded) { for (const pk of await KPCParks.loaded()) { const x = (pk.parks || []).find(z => z.ref === q.ref); if (x && isFinite(x.la)) { p = { la: x.la, lo: x.lo }; break; } } }
        const g6 = up.g || q.g || '';
        if (!p && !up.cn && bk && isFinite(bk.la) && bk.la && !away) p = { la: bk.la, lo: bk.lo };   /* at home: the call book's address */
        if (!p && !up.cn && /^[A-R]{2}\d{2}[A-X]{2}$/i.test(g6)) p = AP.gridLL(g6);
        if (p && !up.cn) { const v = await AP.county(p.la, p.lo); if (v) { up.cn = v.st + ',' + v.c; if (!q.st && v.st) up.st = v.st; } }
      }
      const cur = ALL.get(q.id); if (cur && !cur.d && Object.keys(up).length) edit(q.id, up);
    } catch (e) {}
  }
  function add(o) {
    const call = String(o.call || '').toUpperCase().replace(/[<>\s]/g, '');
    if (!call || call.length < 3) return { ok: false, msg: 'that call sign is too short' };
    const khz = 'khz' in o && o.band && !+o.khz ? 0 : (+o.khz || D.khz), mode = (o.mode || D.mode || 'FT8').toUpperCase(), me = AP.me(), t = +o.t || Math.round(AP.now ? AP.now() : Date.now());   /* Nov 18 (L23): the CALIBRATEd clock */
    const refs = Array.isArray(o.refs) ? refList(o.refs.join(' ')) : refList(o.ref);
    const q = {
      id: newId(t), v: 1, u: Date.now(), d: 0, src: DEV,
      t, call, khz, band: (khz && bandOf(khz)) || String(o.band || '').toLowerCase() || bandOf(khz), mode, opn: o.opn != null ? String(o.opn) : (CUR || ''),
      rs: String(o.rs || '').trim(), rr: String(o.rr || '').trim(),
      st: String(o.st || '').toUpperCase(), g: String(o.g || '').toUpperCase(),
      refs, ref: refs[0] || '', myrefs: Array.isArray(o.myrefs) ? refList(o.myrefs.join(' ')) : myRefs(),
      station: String(o.my || o.station || me.call || '').toUpperCase(), op: String(o.op || me.op || '').toUpperCase(), ctl: String(o.ctl || me.ctl || '').toUpperCase(),
      mg: String(o.mg || me.grid || '').toUpperCase(),
      pw: String(o.pw || AP.S.pwr || ''), rig: String(o.rig || AP.S.rig || ''), ant: String(o.ant || AP.S.ant || ''),   /* Oct 24: power / rig / antenna at that moment */   /* Oct 23 (Brandon: 'qrz does not seem to want to change grids from your home grid'): MY grid on each contact, so a park's grid sticks to that day's contacts */
      name: o.name || '', note: o.note || '',
      mc: String(o.mc || me.cnty || ''), cn: String(o.cn || '')   /* Oct 24: counties, ADIF style 'KY,Hopkins' */
    };
    if (o.cx && typeof o.cx === 'object') q.cx = o.cx;   /* Nov 5: a contest contact's exchange {k, c, s, r, g} (kpc-contest.js) */
    if (q.ctl === q.op) q.ctl = '';
    ALL.set(q.id, q); persist([q]); view(); draw(); AP.fire('log', { why: 'add', recs: [q] });
    const el = $('lgList').firstElementChild; if (el) el.classList.add('new');
    const n = Q.filter(x => dayOf(x.t) === dayOf(q.t)).length;
    cntyFill(q);
    return { ok: true, n, q };
  }
  $('lgForm').onsubmit = e => {
    e.preventDefault();
    const raw = $('eCall').value.trim();
    if (!raw) { AP.toast('Type a call sign first (or HELP for the commands).', 2500, 'bad'); $('eCall').focus(); return; }
    if (command(raw)) { $('eCall').value = FILL; FILL = ''; $('eLook').innerHTML = ''; if ($('eCall').value) lookUp(); return; }
    /* Oct 25 (PoLo): several calls with commas = one contact each, same reports */
    const calls = raw.split(/[\s,;]+/).map(c => c.replace(/\./g, '/')).filter(Boolean);
    const st = (!isFT(D.mode) && v('eSt', true)) || MORE.st;
    let r = null, n = 0; const ids = [];
    for (const call of calls) {
      const lh = calls.length === 1 && LKHIT && LKHIT.call === base(call) ? LKHIT : null;
      const t = D.hold && !isFT(D.mode) ? D.hold : 0;
      r = add({ call, t, khz: D.khz, mode: D.mode, rs: $('eRs').value.trim() || typedRst(D.mode), rr: $('eRr').value.trim() || typedRst(D.mode), st: calls.length === 1 ? (st || (lh && /^[A-Z]{2}$/.test(lh.st) ? lh.st : '')) : '', refs: MORE.refs, g: calls.length === 1 ? (MORE.g || (lh ? lh.g : '')) : '', name: calls.length === 1 ? (MORE.name || (lh ? lh.name : '')) : '', note: MORE.note, cx: G.KPCContest ? KPCContest.entryCx() : null });
      if (!r.ok) { AP.toast('Not logged: ' + esc(r.msg) + (calls.length > 1 ? ' (' + esc(call) + ')' : ''), 4000, 'bad'); return; }
      n++; ids.push(r.q.id); if (D.hold) { D.hold += 60000; saveD(); }
    }
    MORE = {}; moreChip(); dockChips();
    const cnt = $('lgN') ? $('lgN').textContent : r.n;
    AP.toast('✅ ' + (n > 1 ? n + ' contacts' : esc(r.q.call)) + ' logged · ' + esc(r.q.band) + ' ' + esc(r.q.mode) + ' · ' + cnt + (AP.me().hunt ? ' today' : ' at this park') + (D.hold ? ' · ⏸ clock now ' + isoT(D.hold).slice(0, 5) + 'z' : ''), 2600, 'log');
    LASTIDS = ids;
    $('eClr').onclick();
    if (STACK.length) { $('eCall').value = STACK.shift(); drawStack(); lookUp(); }   /* the pile-up stack: the next call comes up by itself */
  };

  /* ---------------- the ADIF file ----------------
     One ADIF line PER MY PARK (a 2-fer on my side = two lines, POTA wants a log per park). Their 2-fer: the first park in
     SIG_INFO / POTA_REF, the rest in APP_KPC_REFS and the comment. Station / operator / control op kept apart (Part 97.119). */
  /* ADIF modes the way QRZ, LoTW and POTA read them (Brandon Oct 22: 'qrz does not have ft8 mode so in the adif make it the
     mode qrz accepts'): FT8 is its own ADIF mode; FT4, JS8, FT2 are MFSK sub-modes; PSK31 = PSK/PSK31 (same as the website logger) */
  /* Oct 25: the whole ADIF 3.1.4 mode / submode table for the modes in the list (Feld Hell is plain HELL, not FMHELL) */
  const ADM = { FT4: ['MFSK', 'FT4'], FT2: ['MFSK', 'FT2'], JS8: ['MFSK', 'JS8'], FST4: ['MFSK', 'FST4'], FST4W: ['MFSK', 'FST4W'], Q65: ['MFSK', 'Q65'], MFSK16: ['MFSK', 'MFSK16'], MFSK8: ['MFSK', 'MFSK8'],
    PSK31: ['PSK', 'PSK31'], PSK63: ['PSK', 'PSK63'], PSK125: ['PSK', 'PSK125'], BPSK31: ['PSK', 'PSK31'], USB: ['SSB', 'USB'], LSB: ['SSB', 'LSB'], CONTESTIA: ['CONTESTI', ''],
    DSTAR: ['DIGITALVOICE', 'DSTAR'], DMR: ['DIGITALVOICE', 'DMR'], C4FM: ['DIGITALVOICE', 'C4FM'], FREEDV: ['DIGITALVOICE', 'FREEDV'], M17: ['DIGITALVOICE', 'M17'], FMHELL: ['HELL', 'FMHELL'],
    APRS: ['PKT', ''], VARA: ['DYNAMIC', 'VARA HF'], 'VARA HF': ['DYNAMIC', 'VARA HF'] };
  function adMode(m) { m = String(m || '').toUpperCase(); return ADM[m] || [m, '']; }
  const sigOf = r => /^[A-Z0-9]*FF-/.test(r) ? 'WWFF' : /^[A-Z0-9]+\/[A-Z]{2}-\d{3}$/.test(r) ? 'SOTA' : 'POTA';
  /* the comment QRZ shows (Brandon Oct 24: 'activation at us-0050 so they see it on qrz' + the county + the operator of a club call) */
  function autoNote(q, my) {
    const out = [], mine = q.myrefs || [];
    if (my) out.push(sigOf(my) + (mine.length > 1 ? ' ' + mine.length + '-fer' : '') + ' activation at ' + mine.join(' + '));
    if (q.mc) out.push(cty(q.mc).replace(/^([^,]+),/, '$1 County,'));
    const op = q.op || '', st = q.station || '';
    if (op && st && op !== st) out.push('op ' + op);
    return out.join(' - ');
  }
  /* Nov 18 full review:
     L4  a contact with a 2-fer / 3-fer activator = ONE LINE PER THEIR PARK (each with its own SIG_INFO), as POTA's P2P rules want;
         o.one (QRZ / eQSL / Wavelog uploads) keeps one line per contact, the other parks in the comment.
     L7  no FREQ tag when the frequency isn't known (a band-only contact), never FREQ 0.000000.
     L14 ADI is ASCII: the comment joins with ' - ', accented letters go plain in the file (the app keeps the real ones). */
  const asc7 = v => String(v).normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[ßæøÆØ]/g, c => ({ 'ß': 'ss', 'æ': 'ae', 'ø': 'o', 'Æ': 'AE', 'Ø': 'O' })[c]).replace(/[^\x20-\x7e\n]/g, '');
  function adif(list, onlyMy, o) {
    o = o || {};
    const me = AP.me(), f = (k, v2) => { if (!v2 && v2 !== 0) return ''; v2 = asc7(v2); return v2 ? '<' + k + ':' + v2.length + '>' + v2 + ' ' : ''; };
    list = list || Q;
    let out = 'KPC app log (' + list.length + ' contacts' + (onlyMy ? ', park ' + onlyMy : '') + ')\n<ADIF_VER:5>3.1.4 <PROGRAMID:3>KPC <PROGRAMVERSION:' + AP.VER.length + '>' + AP.VER + '\n<EOH>\n';
    for (const q of list) {
      const d = new Date(q.t), day = d.getUTCFullYear() + pad(d.getUTCMonth() + 1) + pad(d.getUTCDate()), tm = pad(d.getUTCHours()) + pad(d.getUTCMinutes()) + pad(d.getUTCSeconds());
      const refs = q.refs || [];
      const mine = (q.myrefs && q.myrefs.length ? q.myrefs : ['']).filter(m => !onlyMy || m === onlyMy);
      const theirs = o.one || refs.length < 2 ? [refs[0] || ''] : refs;
      for (const my of mine) for (const r0 of theirs) {
        const more = o.one ? refs.slice(1) : [];
        out += f('CALL', q.call) + f('QSO_DATE', day) + f('TIME_ON', tm) + f('BAND', q.band || bandOf(q.khz)) + (+q.khz > 0 ? f('FREQ', (q.khz / 1000).toFixed(6)) : '') +
          f('MODE', adMode(q.mode)[0]) + f('SUBMODE', adMode(q.mode)[1]) +
          f('RST_SENT', q.rs) + f('RST_RCVD', q.rr) + f('STATE', q.st) + f('GRIDSQUARE', q.g) + f('NAME', q.name) +
          f('STATION_CALLSIGN', q.station || me.call) + f('OPERATOR', q.op || q.station || me.call) + f('APP_KPC_CONTROL_OP', q.ctl) + f('MY_GRIDSQUARE', q.mg || me.grid) +
          f('MY_SIG', my ? sigOf(my) : '') + f('MY_SIG_INFO', my) + (my && sigOf(my) === 'POTA' ? f('MY_POTA_REF', my) : '') +
          f('SIG', r0 ? sigOf(r0) : '') + f('SIG_INFO', r0) + (r0 && sigOf(r0) === 'POTA' ? f('POTA_REF', r0) : '') +
          (LO.ad.app ? f('APP_KPC_REFS', refs.join(',')) + f('APP_KPC_ID', q.id) : '') +
          (LO.ad.pwr ? f('TX_PWR', String(q.pw || '').replace(/[^0-9.]/g, '')) : '') + (LO.ad.rig ? f('MY_RIG', q.rig) + f('MY_ANTENNA', q.ant) : '') +
          (LO.ad.cnty ? f('MY_CNTY', q.mc) + f('MY_STATE', String(q.mc || '').split(',')[0].length === 2 ? String(q.mc).split(',')[0] : '') + f('CNTY', q.cn) : '') +
          (q.cx && G.KPCContest ? KPCContest.adifTags(q) : '') +
          f('COMMENT', (() => { const an = LO.ad.auto ? autoNote(q, my) : '', nt = LO.ad.note ? String(q.note || '') : ''; return [an && !nt.replace(/ · /g, ' - ').includes(an) ? an : '', nt, more.length ? 'also ' + more.join(' ') : ''].filter(Boolean).join(' - '); })())   /* Nov 18: an imported ADIF already has the automatic comment: not twice */ + '<EOR>\n';
      }
    }
    return out;
  }
  /* Nov 18 review (L25): the file carries the date of its first contact (the activation's date), not today's */
  function fname(ext, park, list) { const L = list || (park ? Q.filter(q => (q.myrefs || []).includes(park)) : V.length ? V : Q), t = L.length ? Math.min(...L.map(q => +q.t || Date.now())) : Date.now(); return 'KPC-' + (AP.me().call || 'log').replace(/[^A-Z0-9]/gi, '') + (park ? '-' + park : '') + '-' + new Date(t).toISOString().slice(0, 10) + (ext || '.adi'); }
  const saveFile = (txt, name, mime) => AP.saveFile(txt, name, mime);   /* Oct 22: Android needs the plugin (see kpc-app.js) */
  $('stAdif').onclick = () => saveAdifList(Q, 'the log');
  /* Nov 19 2026: the ADIF save, for SAVE ADIF FILE (every contact) and the ADIF shortcut in CALL (the open log) */
  function saveAdifList(list, what) {
    list = (list || []).filter(q => !q.d);
    if (!list.length) { AP.toast('Nothing in ' + esc(what || 'the log') + ' yet.', 3000, 'bad'); return; }
    const parks = [...new Set(list.flatMap(q => q.myrefs || []))];
    if (parks.length > 1) {                                /* more than one of my parks in the log: one file per park */
      AP.sheet('Which park?', '<p class="hint">Your log has contacts from more than one park. POTA wants one file per park.</p><div class="row">' +
        parks.map(p => `<button type="button" class="b gold" data-park="${esc(p)}">${esc(p)}</button>`).join('') + '<button type="button" class="b" data-park="*">EVERYTHING IN ONE FILE</button></div><p class="hint">⚠ EVERYTHING IN ONE FILE is for your own records or QRZ: <b>don\'t upload it to POTA</b> (POTA wants one file per park).</p>');
      document.querySelectorAll('[data-park]').forEach(b => { b.onclick = () => { AP.shut(); const p = b.dataset.park === '*' ? '' : b.dataset.park; const txt = adif(p ? list.filter(q => (q.myrefs || []).includes(p)) : list, p); saveFile(txt, fname('.adi', p, p ? list.filter(q => (q.myrefs || []).includes(p)) : list)); show(txt); }; });
      return;
    }
    const txt = adif(list);
    saveFile(txt, fname('.adi', '', list));
    show(txt);
  }
  function show(txt) { const t = $('stAdifT'); t.hidden = false; t.value = txt; }
  $('stCopy').onclick = async () => {
    if (!Q.length) { AP.toast('Nothing in the log yet.', 3000, 'bad'); return; }
    const txt = adif(); show(txt);
    try { await navigator.clipboard.writeText(txt); AP.toast('The whole log is copied. Paste it into an email or a file to upload.', 5000, 'log'); }
    catch (e) { $('stAdifT').select(); AP.toast('Copy did not work here: the log is in the box below, hold to select and copy it.', 6000); }
  };
  $('stClear').onclick = () => {
    if (!Q.length) return;
    AP.sheet('Clear the log?', `<p class="hint">This takes all ${Q.length} of ${esc(AP.me().op || 'your')} contacts out of this device. Save the ADIF or KPC log file first if you still need them. A phone or PC that syncs with this one learns they are gone too.</p>
      <div class="row"><button type="button" class="b halt" id="shYes">YES, CLEAR IT</button><button type="button" class="b" id="shNo">KEEP MY LOG</button></div>`);
    $('shYes').onclick = () => { const gone = Q.map(q => { q.d = 1; touch(q); return q; }); persist(gone); view(); draw(); AP.shut(); AP.fire('log', { why: 'clear', recs: gone }); SV('kpcAppLastClear', { at: Date.now(), ids: gone.map(q => q.id) }); undoChip(); AP.toast('The log is empty now. ↩ UNDO CLEAR on the LOG screen brings it back (30 days).', 5000); };
    $('shNo').onclick = () => AP.shut();
  };

  /* Nov 18 review (L22): ↩ UNDO CLEAR for 30 days after a CLEAR (the cleared contacts are tombstones: they come back, and to the other device too) */
  function undoChip() {
    const lc = LS('kpcAppLastClear', null), st = $('lgStrip'); if (!st) return;
    let b = $('lgUndo'); const ok = lc && lc.ids && lc.ids.length && Date.now() - lc.at < 30 * 864e5 && lc.ids.some(id => { const q = ALL.get(id); return q && q.d; });
    if (!ok) { if (b) b.remove(); return; }
    if (!b) { st.insertAdjacentHTML('beforeend', '<button type="button" class="chip" id="lgUndo"></button>'); b = $('lgUndo'); }
    b.textContent = '↩ UNDO CLEAR (' + lc.ids.length + ')';
    b.onclick = () => { const k = revive(lc.ids.map(id => ALL.get(id)).filter(q => q && q.d)); try { localStorage.removeItem('kpcAppLastClear'); } catch (e) {} undoChip(); AP.toast('↩ ' + k + ' contact' + (k === 1 ? '' : 's') + ' back in the log.', 4000, 'log'); };
  }
  /* ---------------- the KPC log file (.kpclog): every record as JSON, for moving a log between devices with no link ---------------- */
  function fileText() { return JSON.stringify({ kpclog: 1, ver: AP.VER, dev: DEV, when: Date.now(), n: ALL.size, qso: [...ALL.values()] }); }
  function importText(txt) {
    let j; try { j = JSON.parse(txt); } catch (e) { j = null; }
    if (j && Array.isArray(j.qso)) return restoreRecs(j.qso, 'file');
    if (/<EOR>/i.test(txt)) { const recs = adifParse(txt), r = restoreRecs(recs, 'adif'); r.skipped = adifParse.skipped || 0; return r; }
    return { ok: false, msg: 'that is not a KPC log file or an ADIF file' };
  }
  /* Nov 18 full review (L1): a RESTORE could never bring back what was deleted or CLEARed here: the delete has the higher edit count, so
     the merge kept it deleted. Now the file is merged as before, and contacts that are live in the file but deleted here are counted
     and offered back ('Bring back N deleted contacts?'). Nothing comes back without the yes. */
  function deadIn(recs) {
    const out = [];
    (recs || []).forEach(r => { if (!r || !r.call || r.d) return; const q = upgrade(r), h = ALL.get(q.id); if (h && h.d) out.push(q); });
    return out;
  }
  function revive(list) {
    const back = [];
    (list || []).forEach(q => { const h = ALL.get(q.id); if (!h || !h.d) return; const n = Object.assign({}, q, { d: 0, v: Math.max(+h.v || 1, +q.v || 1) + 1, u: Date.now(), src: DEV }); ALL.set(n.id, n); back.push(n); });
    if (back.length) { persist(back); view(); draw(); AP.fire('log', { why: 'edit', recs: back }); }
    return back.length;
  }
  function restoreRecs(recs, why) {
    /* Nov 18 (L16): an ADIF line with no APP_KPC_ID that is a contact already here (same call, minute, band, mode) takes that contact's id,
       so re-importing your own file never doubles the log */
    if (why === 'adif') {
      const key = q => [q.call, Math.floor((+q.t || 0) / 60000), String(q.band || '').toLowerCase(), String(q.mode || '').toUpperCase()].join('|'), have = new Map();
      ALL.forEach(q => { const k = key(q); if (!have.has(k) || !q.d) have.set(k, q.id); });
      (recs || []).forEach(r => { if (r && !r.id) { const id = have.get(key(r)); if (id) r.id = id; } });
    }
    const dead = deadIn(recs), n = merge(recs, why).length;
    if (dead.length) setTimeout(() => {
      AP.sheet('Bring back deleted contacts?', `<p>${dead.length} contact${dead.length > 1 ? 's' : ''} in this file ${dead.length > 1 ? 'were' : 'was'} deleted or CLEARed on this device${dead.length > 1 ? '' : ''}. Bring ${dead.length > 1 ? 'them' : 'it'} back?</p>
        <p class="hint">A phone or PC that syncs with this one gets them back too.</p>
        <div class="row"><button type="button" class="b gold" id="shRevive">↩ BRING BACK ${dead.length}</button><button type="button" class="b" id="shNoRev">LEAVE THEM DELETED</button></div>`);
      $('shRevive').onclick = () => { const k = revive(dead); AP.shut(); AP.toast('↩ ' + k + ' contact' + (k === 1 ? '' : 's') + ' back in the log.', 4000, 'log'); };
      $('shNoRev').onclick = () => AP.shut();
    }, 50);
    return { ok: true, n, of: (recs || []).length, dead: dead.length };
  }
  function adifParse(txt) {
    const body = txt.replace(/^[\s\S]*?<EOH>/i, ''), out = [];
    adifParse.skipped = 0;
    body.split(/<EOR>/i).forEach(rec => {
      const F = {}; rec.replace(/<([A-Z0-9_]+):(\d+)(?::[^>]*)?>/gi, (m, k, n, off) => { F[k.toUpperCase()] = rec.substr(off + m.length, +n); return m; });
      if (!F.CALL || !F.QSO_DATE) return;
      const tm = (F.TIME_ON || '0000').trim().padEnd(6, '0'), d = F.QSO_DATE.trim();
      const t = Date.UTC(+d.slice(0, 4), +d.slice(4, 6) - 1, +d.slice(6, 8), +tm.slice(0, 2), +tm.slice(2, 4), +tm.slice(4, 6));
      /* Nov 18 public-release review (0.9.7): a line from a damaged file whose call sign or date cannot be read is counted and left out.
         Before, a bad date was logged as a contact made NOW, and a wrong field length put the next tags inside the call sign. */
      F.CALL = F.CALL.trim();
      if (!/^[^\s<>]{3,20}$/.test(F.CALL) || !/^\d{8}$/.test(d) || !/^\d{6}/.test(tm) || !isFinite(t) || +d.slice(4, 6) < 1 || +d.slice(4, 6) > 12 || +d.slice(6, 8) < 1 || +d.slice(6, 8) > 31 || +tm.slice(0, 2) > 23 || +tm.slice(2, 4) > 59) { adifParse.skipped++; return; }
      const khz = F.FREQ ? Math.round(parseFloat(F.FREQ) * 1e6) / 1000 : 0, sub = (F.SUBMODE || '').toUpperCase(), mo = (F.MODE || '').toUpperCase(), mode = sub && sub !== 'USB' && sub !== 'LSB' ? (sub === 'VARA HF' ? 'VARA' : sub) : sub || mo;   /* any mode is kept as written; USB/LSB stay USB/LSB */
      const refs = refList([F.APP_KPC_REFS || '', F.SIG_INFO || '', F.POTA_REF || ''].join(' '));   /* Nov 18 (L21): PoLo / HAMRS park LISTS in POTA_REF / MY_POTA_REF are read whole */
      out.push({ id: F.APP_KPC_ID || '', t, call: F.CALL.toUpperCase(), khz, band: (F.BAND || bandOf(khz)).toLowerCase(), mode, rs: F.RST_SENT || '', rr: F.RST_RCVD || '', st: F.STATE || '', g: F.GRIDSQUARE || '', name: F.NAME || '', note: F.COMMENT || '',
        refs, myrefs: refList((F.MY_SIG_INFO || '') + ' ' + (F.MY_POTA_REF || '')), station: F.STATION_CALLSIGN || '', mg: F.MY_GRIDSQUARE || '', mc: F.MY_CNTY || '', cn: F.CNTY || '', op: F.OPERATOR || F.STATION_CALLSIGN || '', ctl: F.APP_KPC_CONTROL_OP || '', pw: F.TX_PWR || '', rig: F.MY_RIG || '', ant: F.MY_ANTENNA || '', v: 1, u: t, src: 'adif' });
    });
    /* Nov 18 full review (L5): a 2-fer is written one line per park (mine and theirs): lines of the SAME contact (same APP_KPC_ID, or with
       no id the same call, minute, band and mode) are joined back into one contact with all the parks */
    const by = new Map(), joined = [];
    for (const r of out) {
      const k = r.id ? 'i' + r.id : 'k' + [r.call, Math.floor(r.t / 60000), r.band, r.mode, r.station].join('|');
      const h = by.get(k);
      if (!h) { by.set(k, r); joined.push(r); continue; }
      r.refs.forEach(x => { if (!h.refs.includes(x)) h.refs.push(x); }); r.myrefs.forEach(x => { if (!h.myrefs.includes(x)) h.myrefs.push(x); });
    }
    return joined;
  }
  const bSave = $('stKpcSave'), bAdd = $('stKpcAdd'), fIn = $('stKpcFile');
  if (bSave) bSave.onclick = () => { if (!ALL.size) { AP.toast('Nothing in the log yet.', 3000, 'bad'); return; } saveFile(fileText(), fname('.kpclog'), 'application/json'); };
  if (bAdd && fIn) { bAdd.onclick = () => fIn.click(); fIn.onchange = async () => { const f = fIn.files && fIn.files[0]; fIn.value = ''; if (!f) return; const r = importText(await f.text()); AP.toast(r.ok ? '✅ ' + r.n + ' of ' + r.of + ' contacts were new or newer and went into the log.' + (r.skipped ? ' ⚠ ' + r.skipped + ' line' + (r.skipped === 1 ? ' was' : 's were') + ' left out: no readable call sign or date.' : '') : 'Not added: ' + esc(r.msg), r.ok && r.skipped ? 9000 : 5000, r.ok ? 'log' : 'bad'); }; }

  /* ---------------- hide what can't work yet ---------------- */
  AP.on('me', () => { view(); draw(); dockChips(); counts(); });
  /* Nov 18 full review (L8): the dock follows the radio's MODE too, not only its dial. USB / LSB → SSB, CW → CW, AM, FM; a DATA mode keeps
     the dock's digital mode. FT8 on the dock with the radio in plain USB/LSB/CW and the FT8 screen NOT running = an SSB / CW operator on a
     fresh install: the dock becomes SSB / CW on the radio's dial. */
  const radioMode = m => { m = String(m || '').toUpperCase(); return /^(USB|LSB)$/.test(m) ? 'SSB' : /^CW/.test(m) ? 'CW' : m === 'AM' ? 'AM' : /^FM|^NFM|^WFM/.test(m) ? 'FM' : ''; };
  AP.on('dial', r => {
    if (!r || !r.khz || !r.mode) return;
    const rm = radioMode(r.mode), digiOn = G.KPCDigi && KPCDigi.running && KPCDigi.running();
    /* Nov 18 public-release review (0.9.7): an FT8 / FT4 dock is only kept while the radio really sits on the FT8 / FT4 frequency (within
       3 kHz of the FT8 screen's dial, or of the band's usual FT8 spot). Before, the sound simply being on kept it: after some FT8 the
       operator turned the radio to 14.250 USB, and every voice contact typed on LOG went in as FT8 on 14.074. */
    const near = (a, b2) => a > 0 && b2 > 0 && Math.abs(a - b2) <= 3;
    const ftHere = !!digiOn && (near(r.khz, KPCDigi.dialKhz ? KPCDigi.dialKhz() : 0) || near(r.khz, bandKhz(bandOf(r.khz), 'FT8')));
    const keep = isFT(D.mode) ? ftHere : (rm === 'SSB' && /^(JS8|RTTY|PSK|SSTV|FREEDV|DV)/.test(D.mode) && digiOn);
    if (rm && rm !== D.mode && !keep) {
      const was = D.mode; D.mode = rm; if (isFT(was)) D.khz = r.khz; saveD(); dockChips();
    }
  });
  AP.on('dial', r => { if (r && r.khz && !isFT(D.mode)) { const off = (G.KPCModes5 && KPCModes5.cwOff && document.body.dataset.screen === 'digi') ? KPCModes5.cwOff(r) : 0; D.khz = r.khz + off; saveD(); dockChips(); } });   /* tone CW parks the dial one tone low: log the CW frequency */

  draw(); dockChips(); moreChip(); parkBox($('stRef'));
  setInterval(() => { try { if (ready) counts(); } catch (e) {} }, 60000);   /* Nov 18 (L13): the 0000z turn shows without a new contact */
  load().then(() => { const L = opList(), last = L[0]; if (G.KPC_FRESH || (!navigator.webdriver && !/[?&](headless|fake)=1/.test(location.search) && (!last || Date.now() - last.t1 > 6 * 36e5))) logsCard(); });
  /* ＋ a contact missed earlier: on the LOG strip */
  { const st = $('lgStrip'); if (st && !$('lgAdd')) { st.insertAdjacentHTML('beforeend', '<button type="button" class="chip" id="lgAdd" title="Add a contact you missed, with its own time">＋ EARLIER CONTACT</button>'); $('lgAdd').onclick = () => editSheet(null); } }
  /* NEXT PARK suggestions for the BREAK sheet: the nearest parks from the downloaded packs (the GPS fix the app last had) */
  AP.on('me', () => { breakSheet.near = []; try { const pos = AP.S.pos; if (pos && G.KPCParks && KPCParks.loaded) KPCParks.loaded().then(ps => { const L = []; ps.forEach(pk => (pk.parks || []).forEach(x => { if (isFinite(x.la)) { const d = Math.hypot((x.la - pos.la) * 111, (x.lo - pos.lo) * 111 * Math.cos(pos.la * Math.PI / 180)); L.push({ ref: x.ref, name: x.name, d }); } })); breakSheet.near = L.sort((a, b) => a.d - b.d).slice(0, 8); }).catch(() => {}); } catch (e) {} });

  /* the same little API the website logger has, so the FT8 screen can log the same way */
  /* a spot was tapped (the spot frame): the line is ready to log */
  function prefill(o) {
    if (o.khz > 100 && !isFT(String(o.mode || '').toUpperCase())) { D.khz = +o.khz; D.mode = String(o.mode || D.mode).toUpperCase(); saveD(); }
    else if (o.mode) { D.mode = String(o.mode).toUpperCase(); saveD(); }
    MORE = Object.assign({}, MORE, { refs: refList((o.refs || []).join(' ')), g: String(o.g || '').toUpperCase() });
    $('eCall').value = String(o.call || '').toUpperCase(); moreChip(); dockChips();
    const st1 = String(o.st || '').split('/')[0]; if (st1 && $('eSt') && /^[A-Z]{2}$/.test(st1)) $('eSt').value = st1;   /* Oct 26: the spot's state fills the STATE box */
    lookUp();
  }
  G.KPCLog = {
    add, qs: () => Q, prefill, all: () => ALL, me: AP.me, band: bandOf, toast: AP.toast, adif, dock: D, saveDock: saveD,
    worked: call => { const b = base(call); return Q.some(q => base(q.call) === b); },
    count: () => Q.length, spots: () => [], newPark: () => false,
    merge, changes, remove, edit, get: id => ALL.get(id), fileText, importText, adifParse, restoreRecs, revive, deadIn, _persist: persist, _unsaved: () => UNSAVED, _fname: fname, _undoChip: undoChip, ready: () => ready, dev: DEV, refList,
    hunted: r => huntedRef(r), activated: r => activatedRef(r), potaFile, potaSet, potaFiles: () => PF, potaSheet: () => pfSheet(),
    /* Nov 19 2026 (to-do 3): a 'new to me' choice with no POTA file loaded yet takes the member to MY POTA FILES and says why (one tap,
       no empty list with no word). k = 'h' (hunted: SPOTS) or 'a' (activated: TRIP PLANNER). true = the file is there. */
    needFile: (k, what) => { if (PF[k] && PF[k].refs && PF[k].refs.length) return true; AP.toast('📄 To show ' + what + ', the app needs your POTA ' + (k === 'a' ? 'activator' : 'hunter') + ' file (pota.app → My Stats → EXPORT CSV). Load it here; until then it only knows the contacts in this app.', 9000, 'log'); setTimeout(pfSheet, 300); return false; },
    command, ops: () => opList(), opNew, opOpen, opBreak, opNote, cur: () => CUR, shown: () => V, hold: () => D.hold || 0, holdSet, logsCard, editSheet, bands: BANDS, modes: ALLMODES, adMode, bandKhz
  };
})(window);
